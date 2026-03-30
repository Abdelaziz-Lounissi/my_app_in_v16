# -*- coding: utf-8 -*-
{
    'name': 'HeatMe : Technician App',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'Technician App',
    'summary': 'Technician App Management',
    'website': 'https://netskill.be/',
    "depends": ["base", "sale", "hm_picture_library"],
    "data": [
        "data/data.xml",
        "data/ir_cron.xml",
        "views/technician_app_sync_views.xml",
        "views/technician_app_picture_sync_views.xml",
        "views/technician_app_document_sync_views.xml",
        "views/sale_views.xml",
        "views/mobile_token_views.xml",
        "views/attachment_views.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
