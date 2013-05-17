from openerp.osv import fields,osv
from openerp.tools.translate import _

from datetime import datetime, timedelta
import pdb

class stock_estimation_manager(osv.osv):   
    _name = "stock.estimation.manager"
    
    _columns = {
        'product_id': fields.char('Product ID', size=125),
        'date': fields.date('Date'),
        'product_qty':fields.float('Quantity'),
        }  

    def run_scheduler(self, cr, uid, context=None):
        self.get_sales(cr, uid)
        return True   

    def view_init(cr, uid, fields_list, context=None):
        
        res = super(stock_estimation_manager, self).view_init(cr, uid, fields_list, context=context)
        self.get_sales(cr, uid)

        return res

    def get_objects(self, cr, uid, name, args=[], ids=None):                       

        obj = self.pool.get(name)
        if not ids:
            ids = obj.search(cr, uid, args)
        return obj.browse(cr, uid, ids)

    def get_sales(self, cr, uid):        
        
        CALCULATION_WINDOW_DAYS = 2

        # Eliminar todos los objetos actuales
        args = []
        ids = self.search(cr, uid, args)
        self.unlink(cr, uid, ids)

        # Obtener las localizaciones de tipo cliente
        stock_locations = self.get_objects(cr, uid, 'stock.location')     
        stock_locations_customer = [sl for sl in stock_locations if sl.usage=='customer']

        # Obtener todos los movimientos cuyo destino final sea una localizacion de
        # tipo cliente y esten dentro de los días de la ventana de cálculo

        calculation_date = datetime.today() - timedelta(days=CALCULATION_WINDOW_DAYS)
        str_calculation_date = datetime.strftime(calculation_date, "%Y-%m-%d") + " 00:00:00"

        args = [('create_date', '>=', str_calculation_date)]
        stock_moves = self.get_objects(cr, uid, 'stock.move', args)        
                
        stock_moves_customer = [sm for slc in stock_locations_customer for sm in stock_moves 
                                if sm.location_dest_id==slc]

        # Agrupar los movimientos por producto y fecha
        res={}
        for smc in stock_moves_customer:
            product_id = smc.product_id.id
            date = datetime.strptime(smc.create_date, "%Y-%m-%d %H:%M:%S").date()
            res.setdefault(product_id, {})
            res[product_id].setdefault(date, 0.0)
            res[product_id][date] += smc.product_qty

        for product in res.keys():
            for date in res[product].keys():
                obj = {
                    'product_id': product,
                    'date': date,
                    'product_qty': res[product][date]
                }
                self.create(cr, uid, obj, context=None)

        """
        for smc in stock_moves_customer:            
            date = datetime.strptime(smc.date, "%Y-%m-%d %H:%M:%S").date()
            obj = {
                    'product_id': smc.product_id,
                    'date': date,
                    'product_qty': smc.product_qty 
                }
            self.create(cr, uid, obj, context=None)
        """

stock_estimation_manager()