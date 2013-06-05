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

{
    'name': 'Statistical estimation of stockable products',
    'version': '0.2',
    'author': 'Codeback Software',
    'summary': 'Storage, Forecast, Stock rules, Scheduler',
    'description' : 'Advanced estimation of stockable products based on configurable settings. Automatically or manually generates purchase orders based on expected needs',
    'website': 'http://codeback.es',
    'images': [],
    'depends': ['stock', 'procurement'],
    'category': 'Warehouse Management',
    'sequence': 23,
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'stock_estimation_view.xml',
        'stock_estimation_data.xml',        
        'product_view.xml',
        'wizard/wizard_order.xml',
        'wizard/wizard_operation_mode.xml',
    ],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'css': [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
