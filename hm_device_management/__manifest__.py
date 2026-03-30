# -*- coding: utf-8 -*-
{
    'name': 'HeatMe : Device Management',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'Device Management',
    'summary': 'Device Management',
    'website': 'https://netskill.be/',
    "depends": ["base", "hm_sale", "hm_property", "hm_technician_app"],
    "data": [
        "security/ir.model.access.csv",

        "views/hm_device_views.xml",
        "views/hm_device_model_views.xml",
        "views/hm_device_menu_views.xml",
        "views/product_views.xml",
        "views/sale_views.xml",
        "views/sale_order_template_views.xml",
        "views/hm_property_views.xml",
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
