# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Statistical estimation of stockable products',
    'version': '0.2',
    'author': 'Codeback Software',
    'summary': 'Storage, Forecast, Stock rules, Scheduler',
    'description' : """
TBD
    """,
    'website': 'http://codeback.es',
    'images': [],
    'depends': ['stock'],
    'category': 'Warehouse Management',
    'sequence': 23,
    'demo': [],
    'data': [
        'stock_estimation_manager.xml',
        'stock_estimation_manager_view.xml',
    ],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'css': [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
