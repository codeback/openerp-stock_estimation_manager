from openerp.osv import fields,osv
from openerp.tools.translate import _

import pdb

class stock_estimation_manager(osv.osv):   
    _name = "stock.estimation.manager"
    
    _columns = {
        'product_id': fields.char('Product ID', size=125),
        'date': fields.char('Date', size=125),
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
        
        # Eliminar todos los objetos actuales
        args = []
        ids = self.search(cr, uid, args)
        self.unlink(cr, uid, ids)

        # Obtener las localizaciones de tipo cliente
        stock_locations = self.get_objects(cr, uid, 'stock.location')     
        stock_locations_customer = [sl for sl in stock_locations if sl.usage=='customer']

        # Obtener todos los movimientos cuyo destino final sea una localizacion de
        # tipo cliente        
        stock_moves = self.get_objects(cr, uid, 'stock.move')        
                
        stock_moves_customer = [sm for slc in stock_locations_customer for sm in stock_moves 
                                if sm.location_dest_id==slc]

        # Agrupar los movimientos por producto y fecha
        """
        pdb.set_trace() 
        res={}
        default_key = {}
        for smc in stock_moves_customer:
            product_id = smc.product_id
            date = smc.date.split(" ")[0]
            res.setdefault(product_id, default_key)

            res[product_id].setdefault(date, 0.0)
            res[product_id][date] += smc.product_qty
        """   
        res=[]
        for smc in stock_moves_customer:            
            obj = {
                    'product_id': smc.product_id.id,
                    'date': smc.date.split(" ")[0],
                    'product_qty': smc.product_qty 
                }
            res.append(obj)
            self.create(cr, uid, obj, context=None)
            self._columns['product_id'] = smc.product_id.id
            self._columns['date'] = smc.date
            self._columns['product_qty'] = smc.product_qty
       
        return res

stock_estimation_manager()