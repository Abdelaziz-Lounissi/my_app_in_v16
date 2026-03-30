# -*- coding: utf-8 -*-
{
    'name': 'HeatMe : Van Marcke Integration',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'API',
    'summary': 'API Van Marcke Integration',
    'website': 'https://netskill.be/',
    'depends': ['base', 'mail', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/hm_product_vanmarcke.xml',
        'views/hm_product_vanmarcke_import.xml',
        'views/hm_vanmarcke_menu.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
