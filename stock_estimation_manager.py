from openerp.osv import fields,osv
from openerp.tools.translate import _

from datetime import datetime, timedelta
from decimal import Decimal
from scipy.stats import norm
import math
import pdb

class stock_estimation_manager(osv.osv):   
    _name = "stock.estimation.manager"
    
    _columns = {
        'procurement_need': fields.boolean('Procurement need'),
        'product_name': fields.char('Product', size=128, required=True),
        'outgoings_per_day': fields.float('Outgoings per day'),
        'security_stock': fields.float('Security Stock'),
        'stock_min': fields.float('Stock min'),
        'stock_max': fields.float('Stock max'),        
        'stock_virtual': fields.float('Stock virtual'),
        'stock_real': fields.float('Stock real'),
        'suplier_delay': fields.float('Supplier lead time')
        }  

    def run_scheduler(self, cr, uid, context=None):
        self.estimate_stock(cr, uid)
        return True   

    def estimate_stock(self, cr, uid):        
        
        # Leer datos de configutacion
        CALCULATION_WINDOW_DAYS = int(10)
        SECURITY_DAYS = 0
        QOS = 0.7
        MANUFACTURING_MATERIALS = False

        # Eliminar todos los objetos actuales
        self._clear_objects(cr, uid)

        # Obtener las localizaciones objetivo (de tipo cliente y opcionalmente
        # los materiales utilizados en la fabricacion
        stock_locations = self._get_locations(cr, uid, 'customer')
        if MANUFACTURING_MATERIALS:
            stock_locations_production = self._get_locations(cr, uid, 'production')
            stock_locations.extend(stock_locations_production)

        # Obtener todos los movimientos cuyo destino final sea una localizacion
        # objetivo y esten dentro de los dias de la ventana de calculo
        stock_moves = self._get_moves_in_window(cr, uid, stock_locations, CALCULATION_WINDOW_DAYS)

        # Agrupar los movimientos por producto y fecha
        outgoings = self._group_by_product_and_date(stock_moves)
        
        for product in outgoings.keys():

            outgoing_qties = self._get_qties_per_day(
                outgoings[product].values(), CALCULATION_WINDOW_DAYS)
 
            # Calculo de la cdf inversa usando QoS
            estimated_outgoings = self._calculate_inverse_cdf(outgoing_qties, QOS)
            
            # Guardar resultados
            outgoings_per_day = Decimal(estimated_outgoings)
            stock_real = Decimal(product.qty_available)
            stock_virtual = Decimal(product.virtual_available)
            suplier_delay = Decimal(product.seller_delay)
            stock_min = Decimal(outgoings_per_day * (suplier_delay + SECURITY_DAYS))            
            security_stock = stock_virtual-stock_min
            
            if security_stock < 0:
                procurement_need = True
                stock_max = Decimal(2.0) * stock_min - stock_virtual
            else:
                procurement_need = False
                stock_max = 0

            record = {
                'procurement_need': procurement_need,
                'product_name': product.name,
                'security_stock': security_stock,
                'outgoings_per_day': outgoings_per_day,
                'stock_min': stock_min,
                'stock_max': stock_max,
                'stock_virtual': stock_virtual,
                'stock_real': stock_real,
                'suplier_delay': suplier_delay
            }
            self.create(cr, uid, record)

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

        return [sm for sl in stock_locations for sm in stock_moves if sm.location_dest_id==sl]

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

    def _calculate_inverse_cdf(self, outgoing_qties, qos):
        """
        Halla la media y la desv. tipica para cada producto y se calcula la 
        cdf inversa utilizando la QoS deseada para cada producto
        """
        mean = sum(outgoing_qties)/len(outgoing_qties)        
        variance = map(lambda x: (x - mean)**2, outgoing_qties)
        standard_deviation = math.sqrt(sum(variance)/len(outgoing_qties))
        return norm(mean, standard_deviation).ppf(qos)

stock_estimation_manager()