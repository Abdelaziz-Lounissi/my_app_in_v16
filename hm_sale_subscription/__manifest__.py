# -*- coding: utf-8 -*-

{
    'name': "HeatMe : Subscriptions",
    'version': '16.0.1.0.0',
    'category': 'Sales/Subscriptions',
    'summary': 'Subscriptions Management',
    'author': 'Aziz, Netskill Group(NSG)',
    'website': 'https://netskill.be/',
    'depends': [
        'sale_subscription',
        'hm_property',
        'crm',
    ],
    'data': [
        'views/crm_lead_views.xml',
        'views/res_partner_views.xml',
        'views/hm_property_views.xml',
        'views/sale_order_views.xml',
    ],
    'application': True,
    'license': 'LGPL-3',

}
