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

class stock_estimation_config_settings(osv.osv_memory):   
    _name = "stock.estimation.config.settings"
    _inherit = 'res.config.settings'
    
    _columns = {
        'default_window_days': fields.integer('Window days', default_model='stock.estimation.settings', required=True),
        'default_qos': fields.float('Quality of Service', default_model='stock.estimation.settings', required=True),
        'default_include_bom': fields.boolean('Include BoM', default_model='stock.estimation.settings'),
        'default_sigma_factor': fields.float('Sigma Factor', default_model='stock.estimation.settings', required=True),
    } 

    _defaults = {
        'default_window_days': 30,
        'default_qos' : 0.7,
        'default_include_bom' : True,
        'default_sigma_factor' : 2,
    }  

    def create(self, cr, uid, values, context=None):
        ids = self.search(cr, uid, [])
        if ids and ids[0]:
            id=ids[0]
            self.write(cr, uid, [id], values, context)
        else:
            id = super(stock_estimation_config_settings, self).create(cr, uid, values, context)
        return id

stock_estimation_config_settings()