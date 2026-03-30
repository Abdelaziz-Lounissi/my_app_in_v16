# -*- coding: utf-8 -*-
{
    'name': "HeatMe : Additional Supplier",
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'Purchase',
    'summary': 'Multi Supplier Management',
    'website': 'https://netskill.be/',
    'depends': ['base', 'hm_purchase', 'hm_product', 'hm_integration_facq', 'hm_integration_vanmarcke'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/purchase_views.xml',
        'wizard/check_supplier.xml',
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
