# -*- coding: utf-8 -*-
{
    'name': 'HeatMe : Picture Library',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'Documents/Pictures',
    'summary': 'Picture Library Management',
    'website': 'https://netskill.be/',
    'depends': ['base', 'crm', 'sale', 'base_automation', 'account', 'hm_property'],
    'data': [
        'data/config_parameter.xml',
        'data/ir_actions_server.xml',
        'data/base_automation.xml',
        'data/cron_update_mime.xml',
        'security/ir.model.access.csv',
        'views/hm_picture_library_view.xml',
        'views/sale_order_view.xml',
        'views/crm_lead.xml',
        'views/menu_view.xml',
        'views/hm_property_view.xml',
        'wizard/hm_picture_library_wizard_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hm_picture_library/static/src/js/external_image_zoom.js',
            'hm_picture_library/static/src/css/style.css'
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
