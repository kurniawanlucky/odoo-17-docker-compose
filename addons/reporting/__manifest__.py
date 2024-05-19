# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Reports',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': [
        'product',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'data/master_period_data.xml',
        'data/product_data.xml',
        'security/reporting_security.xml',
        'security/ir.model.access.csv',
        'views/period_views.xml',
        'views/report_views.xml',
        'views/report_menus.xml',  # Last because referencing actions defined in previous files
    ],
    'demo': [],
    'installable': True,
    'license': 'LGPL-3',
}
