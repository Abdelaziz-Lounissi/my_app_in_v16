# -*- coding: utf-8 -*-
{
    'name': 'HeatMe : Facq Integration',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'API',
    'summary': 'API Facq Integration',
    'website': 'https://netskill.be/',
    'depends': ['base', 'mail', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/hm_product_facq_view.xml',
        'views/hm_facq_log_view.xml',
        'views/res_company.xml',
        'views/hm_facq_menu.xml',
        'data/ir_cron.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
