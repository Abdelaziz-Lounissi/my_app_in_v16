# -*- coding: utf-8 -*-
{
    'name': 'HeatMe : Firebase Integration',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'Mobile App',
    'summary': 'Firebase integration with mobile App',
    'website': 'https://netskill.be/',
    'depends': ['base', 'hm_technician_app'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'views/res_config_settings_views.xml',
        'views/mobile_notification_views.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
