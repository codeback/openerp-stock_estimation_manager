# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2013 Codeback Software S.L. (www.codeback.es). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields,osv
from openerp.tools.translate import _

from datetime import datetime, timedelta
from decimal import Decimal
from scipy.stats import norm
import math
import pdb

class stock_estimation(osv.osv):   
    _name = "stock.estimation"
    _columns = {
        'stock_status': fields.selection([('level1','Danger'),('level2','Warning'), ('level3','Caution'),('level4','Available')],'Stock status'),
        'product_name': fields.char('Product', size=128, required=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'outgoings_per_day': fields.float('Outgoings per day'),
        'expected_per_day': fields.float('Expected per day'),
        'security_stock': fields.float('Security Stock'),
        'security_days': fields.float('Security Days'),
        'required_qty': fields.float('Required quantity'),
        'stock_min': fields.float('Min. stock'),
        'stock_max': fields.float('Max. stock'),        
        'stock_virtual': fields.float('Virtual stock'),
        'stock_real': fields.float('Real stock'),
        'supplier_delay': fields.float('Lead time'),
        'supplier_name': fields.char('Supplier', size=64),
        }  

    def run_scheduler(self, cr, uid, context=None):
        """ Estimate stock from scheduler"""   
        self.estimate_stock(cr, uid)
        return True     

    def estimate_stock(self, cr, uid):              
        
        # Eliminar todos los objetos actuales
        self._clear_objects(cr, uid)
                
        # Leer datos de configutacion
        config = self._get_config_data(cr,uid)              
        
        # Obtener las localizaciones objetivo (de tipo cliente y opcionalmente
        # los materiales utilizados en la fabricacion
        stock_locations = self._get_locations(cr, uid, 'customer')
        if config['include_bom']:
            stock_locations_production = self._get_locations(cr, uid, 'production')
            stock_locations.extend(stock_locations_production)
        
        # Obtener todos los movimientos cuyo destino final sea una localizacion
        # objetivo y esten dentro de los dias de la ventana de calculo
        stock_moves = self._get_moves_in_window(cr, uid, stock_locations, config['window_days'])
        
        # Agrupar los movimientos por producto y fecha
        outgoings = self._group_by_product_and_date(stock_moves)
        
        for product in outgoings.keys():
            
            if self._is_valid_product(product):
                
                outgoing_qties = self._get_qties_per_day(
                    outgoings[product].values(), config['window_days'])
                
                # Eliminar outliers
                outgoing_qties = self._remove_outliers(outgoing_qties, config['sigma_factor'])
                
                stock_real = Decimal(product.qty_available)
                stock_virtual = Decimal(product.virtual_available)
                qos = config['qos']
                
                # 3 niveles de estimación
                ALERT_OFFSET = 0.05
                estimation = self._estimate_product(product, outgoing_qties, qos)                
                
                if estimation['security_stock'] < 0:
                    
                    # Producto con estimación Danger 
                    stock_status = 'level1'    
                    
                    stock_min = estimation['stock_min']                                              
                    
                    required_qty = estimation['required_qty']
                    
                    stock_max = required_qty + stock_virtual          
                    
                else:                    
                    
                    estimation2 = self._estimate_product(product, outgoing_qties, qos+ALERT_OFFSET) 
                    
                    if estimation2['security_stock'] < 0:
                        
                        # Producto con estimación Warning 
                        stock_status = 'level2'                        
                        stock_min = estimation2['stock_min']                
                        required_qty = estimation2['required_qty']
                        stock_max = required_qty + stock_virtual 
                    else:
                        
                        stock_status = 'level4'
                        stock_min = 0
                        stock_max = 0
                        required_qty = 0

                        if qos+2*ALERT_OFFSET <= 1:
                            estimation3 = self._estimate_product(product, outgoing_qties, qos+2*ALERT_OFFSET) 

                            if estimation3['security_stock'] < 0:
                                # Producto con estimación Caution 
                                stock_status = 'level3'
                                required_qty = estimation3['required_qty']
                
                record = {
                    'stock_status': stock_status,
                    'product_name': product.code or product.name,
                    'product_id': product.id,
                    'security_stock': estimation['security_stock'],
                    'security_days': estimation['security_days'],
                    'required_qty': required_qty,
                    'outgoings_per_day': estimation['outgoings_per_day'],
                    'expected_per_day': estimation['expected_per_day'],
                    'stock_min': stock_min,
                    'stock_max': stock_max,
                    'stock_virtual': stock_virtual,
                    'stock_real': stock_real,
                    'supplier_delay': product.seller_delay,
                    'supplier_name': product.seller_id.name
                }
                
                self.create(cr, uid, record)
                
                # Actualizar Qmin y Qmax del punto de pedido
                if product.stock_estimation_mode == 'a':
                    
                    self._update_orderpoint(cr, uid, product.orderpoint_ids, record['stock_min'], record['stock_max'])

        return True

    def _estimate_product(self, product, outgoing_qties, qos):

        # Calculo de la cdf inversa usando QoS
        mean, expected_outgoings = self._calculate_inverse_cdf(outgoing_qties, qos)
                        
        # Calcular resultados
        outgoings_per_day = Decimal(mean)
        expected_per_day = Decimal(expected_outgoings)
        stock_real = Decimal(product.qty_available)
        stock_virtual = Decimal(product.virtual_available)
        supplier_delay = Decimal(product.seller_delay)
        stock_min = Decimal(expected_per_day * supplier_delay)            
        security_stock = Decimal(stock_virtual-stock_min)
        security_days = Decimal(stock_virtual / expected_per_day)
        required_qty = Decimal(2.0) * (stock_min - stock_virtual)
        
        # Comprobar que la cantidad requerida es al menos 1 unidad de la cantidad mínima
        required_qty = self._get_uom_qty(required_qty, product.uom_id.rounding)
        if required_qty < product.uom_id.rounding:
            security_stock = 0            

        return {                       
            'security_stock': security_stock,
            'security_days': security_days,            
            'outgoings_per_day': outgoings_per_day,
            'expected_per_day': expected_per_day,
            'stock_min': stock_min,
            'required_qty': required_qty            
        }

    def _get_uom_qty(self, required_qty, precision, count=0):
        if precision >= 1:
            return Decimal(round(required_qty,count))
        else:
            count=count+1
            return self._get_uom_qty(required_qty, precision*10, count=count)

    def _get_objects(self, cr, uid, name, args=[], ids=None):   
        """
        Obtiene los objetos del modelo 'name'
        """                  
        obj = self.pool.get(name)
        if not ids:
            ids = obj.search(cr, uid, args)
        return obj.browse(cr, uid, ids)

    def _clear_objects(self, cr, uid, args=[], ids=None):
        """
        Elimina los objetos de forma permanente
        """
        if not ids:
            ids = self.search(cr, uid, args)
        self.unlink(cr, uid, ids)

    def _get_locations(self, cr, uid, location_type):
        """
        Obtiene las localizaciones de un determinado tipo
        """
        stock_locations = self._get_objects(cr, uid, 'stock.location')     
        return [sl for sl in stock_locations if sl.usage==location_type]

    def _get_moves_in_window(self, cr, uid, stock_locations, window_days):
        """
        Obtiene todos los movimientos cuyo destino final sea una localizacion
        objetivo y esten dentro de los dias de la ventana de calculo
        """
        calculation_date = datetime.today() - timedelta(days=window_days)
        str_calculation_date = datetime.strftime(calculation_date, "%Y-%m-%d") + " 00:00:00"

        args = [('create_date', '>=', str_calculation_date)]
        stock_moves = self._get_objects(cr, uid, 'stock.move', args)        

        return [sm for sl in stock_locations for sm in stock_moves if sm.location_dest_id==sl and sm.state != 'cancel']

    def _group_by_product_and_date(self, stock_moves):
        """
        Agrupa los movimientos por porducto y fecha (dia)
        """
        outgoings = {}
        for smc in stock_moves:
            product_id = smc.product_id
            date = datetime.strptime(smc.create_date, "%Y-%m-%d %H:%M:%S").date()
            outgoings.setdefault(product_id, {})
            outgoings[product_id].setdefault(date, 0.0)
            outgoings[product_id][date] += smc.product_qty
        return outgoings

    def _get_qties_per_day(self, values, window_days):
        """
        Devuelve las cantidades de salida por dia. Si hay algun dia que 
        no ha habido salidas agrega un cero
        """        
        if window_days - len(values) > 0:
            n = window_days - len(values)
            days_of_zeros = [0.0] * int(n)
            values.extend(days_of_zeros)

        return values

    def _calculate_mean_and_std(self, outgoing_qties):
        """
        Halla la media y la desviacion tipica
        """
        mean = sum(outgoing_qties)/len(outgoing_qties)        
        variance = map(lambda x: (x - mean)**2, outgoing_qties)
        standard_deviation = math.sqrt(sum(variance)/len(outgoing_qties))

        return (mean, standard_deviation)

    def _calculate_inverse_cdf(self, outgoing_qties, qos):
        """
        Halla la media y la desv. tipica para cada producto y se calcula la 
        cdf inversa utilizando la QoS deseada para cada producto
        """
        mean, standard_deviation = self._calculate_mean_and_std(outgoing_qties)
        return (mean, norm(mean, standard_deviation).ppf(qos))

    def _remove_outliers(self, outgoing_qties, sigma_factor):
        """
        Calcula la media y la std y establece al valor medio 
        aquellos valores que superen sigma_factor veces la std
        """
        mean, standard_deviation = self._calculate_mean_and_std(outgoing_qties)

        results = []
        for outgoing_qty in outgoing_qties:
            if outgoing_qty > mean + sigma_factor*standard_deviation:
                outgoing_qty = mean
            results.append(outgoing_qty)
        
        return results

    def _update_orderpoint(self, cr, uid, ids, stock_min, stock_max):
        if ids and ids[0]:
            id_op = ids[0].id
            orderpoint = self.pool.get('stock.warehouse.orderpoint') 
            values = {
                'product_min_qty': stock_min,
                'product_max_qty': stock_max
            }
            orderpoint.write(cr, uid, [id_op], values)

    def _get_config_data(self, cr, uid):
        """
        Lee los datos de configutacion
        """

        model_conf = self.pool.get('stock.estimation.config.settings')        
        ids = model_conf.search(cr, uid, [])
        config = model_conf.browse(cr, uid, ids)

        if config and config[0]:
            config_data = config[0]
        else:
            obj_id = model_conf.create(cr, uid, {})
            config = model_conf.browse(cr, uid, [obj_id])
            config_data = config[0]

        return {
            'window_days': config_data.default_window_days,
            'qos': config_data.default_qos,
            'include_bom': config_data.default_include_bom,
            'sigma_factor': config_data.default_sigma_factor
        }

    def _is_valid_product(self, product):
        if product.active \
        and self._is_stockable(product) \
        and self._is_module_activated(product) \
        and self._is_buyable(product) \
        and self._is_state_normal(product):
            return True
        return False

    def _is_stockable(self, product):
        return product.type and product.type == 'product'

    def _is_module_activated(self, product):
        return product.stock_estimation_mode and product.stock_estimation_mode != 'd'

    def _is_buyable(self, product):
        return product.supply_method and product.supply_method == 'buy'

    def _is_state_normal(self, product):
        return not product.state or product.state == 'sellable'

stock_estimation()

class stock_estimation_settings(osv.osv):  
    _name = "stock.estimation.settings"
    
    _columns = {
        'window_days': fields.integer('Window days'),
        'qos': fields.float('Quality of Service'),
        'include_bom': fields.boolean('Include BoM'),
        'sigma_factor': fields.float('Sigma Factor'),    
    } 

    def create(self, cr, uid, values, context=None):
        ids = self.search(cr, uid, [])
        if ids and ids[0]:
            id=ids[len(ids)-1]
            self.write(cr, uid, [id], values, context)
        else:
            id = super(stock_estimation_settings,self).create(cr, uid, values, context)
        return id

    def run_stock_estimation(self, cr, uid, ids, context=None):
        """ Estimate stock from wizard"""    

        obj = self.pool.get('stock.estimation')
        obj.estimate_stock(cr, uid)
        
        menu_mod = self.pool.get('ir.ui.menu')        
        args = [('name', '=', 'Stock estimation manager')]
        menu_ids = menu_mod.search(cr, uid, args)
        
        return {
            'name': 'Stock Estimation',
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'menu_id': menu_ids[0]},
        }      

stock_estimation_settings()