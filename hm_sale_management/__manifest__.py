# -*- coding: utf-8 -*-

{
    'name': 'HeatMe : Sale Management',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'Sales',
    'summary': 'Sales Management',
    'website': 'https://netskill.be/',
    'depends': [
        'hm_base_setup',
        'hm_sale_crm',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/sale_order_template_views.xml',
        'views/sale_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
