# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Pexego Sistemas Informáticos (<http://www.pexego.es>). All Rights Reserved
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

from osv import fields, osv
from tools.translate import _
import pdb
import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime

class stock_estimation_order_line(osv.TransientModel):

    _name = "stock.estimation.order.line"
    _rec_name = 'product_id'
    _columns = {
        'product_id' : fields.many2one('product.product', string="Product", required=True, ondelete='CASCADE'),
        'product_name': fields.char('Product', size=128, required=True),
        'quantity' : fields.float("Quantity", required=True),
        'wizard_id' : fields.many2one('stock.estimation.order.wizard', string="Wizard", ondelete='CASCADE'),
    }

class stock_estimation_order_wizard (osv.osv_memory):
    """stock.estimation.order.wizard"""

    _name = 'stock.estimation.order.wizard'
    _columns = {       
        'order_lines_ids' : fields.one2many('stock.estimation.order.line', 'wizard_id', 'Order lines'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(stock_estimation_order_wizard, self).default_get(cr, uid, fields, context=context)
        stock_est_ids = context.get('active_ids', [])
        
        if not stock_est_ids or len(stock_est_ids) == 0:
            return res

        stock_est_objs = self.pool.get('stock.estimation').browse(cr, uid, stock_est_ids, context=context)

        order_lines = []
        for stock_est_obj in stock_est_objs:
            order_line = {
                'product_id': stock_est_obj.product_id.id,
                'product_name': stock_est_obj.product_name,
                'quantity': stock_est_obj.required_qty,
            }
            order_lines.append(order_line)
            
        res.update(order_lines_ids=order_lines)
        return res

    def generate_order(self, cr, uid, ids, context=None):
        
        wf_service = netsvc.LocalService("workflow")
        proc_obj = self.pool.get('procurement.order')
        #stock_est = self.pool.get('stock.estimation')
        order = self.browse(cr, uid, ids[0], context=context)
        # stock_est_objs = stock_est.browse(cr, uid, context['active_ids'], context=context)

        for order_line in order.order_lines_ids:
            product = order_line.product_id

            if product.orderpoint_ids and product.orderpoint_ids[0]:
                warehouse = product.orderpoint_ids[0].warehouse_id
            
                proc_id = proc_obj.create(cr, uid,
                                self._prepare_procurement(cr, uid, product, warehouse, order_line.quantity, context=context),
                                context=context)
                
                wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
                wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_check', cr)
                '''
                proc_obj.signal_workflow(cr, uid, [proc_id], 'button_confirm', context=context)
                proc_obj.signal_workflow(cr, uid, [proc_id], 'button_check', context=context)
                '''

    def _prepare_procurement(self, cr, uid, product, warehouse, product_qty, context=None):
        return {'name': _('Stock Estimation Automatic OP: %s') % (product.name,),
            'origin': _('Stock Estimation Module'),
            'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'product_id': product.id,
            'product_qty': product_qty,
            'product_uom': product.uom_id.id,
            'location_id': warehouse.lot_input_id.id,
            'company_id': warehouse.company_id.id,
            'procure_method': 'make_to_order',}

stock_estimation_order_wizard ()
