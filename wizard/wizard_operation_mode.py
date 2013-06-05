from openerp.osv import fields,osv
from openerp.tools.translate import _
import pdb

class stock_estimation_mode_wizard (osv.osv_memory):
    """stock.estimation.mode.wizard"""

    _name = 'stock.estimation.mode.wizard'
    _columns = {      
        'operation_mode': fields.selection([('d','Disabled'),('a','Auto'),('m','Manual')],'Operation mode', required=True, select=1),      
    }

    def apply_mode(self, cr, uid, ids, context=None):
        
        prod_model = self.pool.get('product.product')
        stock_est_model = self.pool.get('stock.estimation')
        stock_est_objs = stock_est_model.browse(cr, uid, context['active_ids'], context=context)

        prod_ids = [se.product_id.id for se in stock_est_objs]

        objs = self.browse(cr, uid, ids, context=context)
        values = {
            'stock_estimation_mode': objs[0].operation_mode
        }
        prod_model.write(cr, uid, prod_ids, values)

        return True

stock_estimation_mode_wizard ()
