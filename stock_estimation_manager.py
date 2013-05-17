from openerp.osv import fields,osv
from openerp.tools.translate import _

from datetime import datetime, timedelta
from decimal import Decimal
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
        self.get_sales(cr, uid)
        return True   

    def view_init(cr, uid, fields_list, context=None):
        
        outgoings = super(stock_estimation_manager, self).view_init(cr, uid, fields_list, context=context)
        self.get_sales(cr, uid)

        return outgoings

    def get_objects(self, cr, uid, name, args=[], ids=None):                       

        obj = self.pool.get(name)
        if not ids:
            ids = obj.search(cr, uid, args)
        return obj.browse(cr, uid, ids)

    def get_sales(self, cr, uid):        
        
        CALCULATION_WINDOW_DAYS = 5
        SECURITY_DAYS = 2
        STOCK_VIRTUAL = 0

        # Eliminar todos los objetos actuales
        args = []
        ids = self.search(cr, uid, args)
        self.unlink(cr, uid, ids)

        # Obtener las localizaciones de tipo cliente
        stock_locations = self.get_objects(cr, uid, 'stock.location')     
        stock_locations_customer = [sl for sl in stock_locations if sl.usage=='customer']

        # Obtener todos los movimientos cuyo destino final sea una localizacion de
        # tipo cliente y esten dentro de los dias de la ventana de calculo
        calculation_date = datetime.today() - timedelta(days=CALCULATION_WINDOW_DAYS)
        str_calculation_date = datetime.strftime(calculation_date, "%Y-%m-%d") + " 00:00:00"

        args = [('create_date', '>=', str_calculation_date)]
        stock_moves = self.get_objects(cr, uid, 'stock.move', args)        

        stock_moves_customer = [sm for slc in stock_locations_customer for sm in stock_moves 
                                if sm.location_dest_id==slc]

        # Agrupar los movimientos por producto y fecha
        outgoings={}
        for smc in stock_moves_customer:
            product_id = smc.product_id
            date = datetime.strptime(smc.create_date, "%Y-%m-%d %H:%M:%S").date()
            outgoings.setdefault(product_id, {})
            outgoings[product_id].setdefault(date, 0.0)
            outgoings[product_id][date] += smc.product_qty

        # Halla la media para cada producto
        for product in outgoings.keys():
            outgoing_qties = outgoings[product].values()
            mean = Decimal(sum(outgoing_qties))/CALCULATION_WINDOW_DAYS
            
            outgoings_per_day = mean
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

stock_estimation_manager()