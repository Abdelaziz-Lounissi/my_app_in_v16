# -*- coding: utf-8 -*-
{
    'name': 'HeatMe: WhatsApp',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'WhatsApp',
    'summary': 'WhatsApp Text Messaging',
    'website': 'https://netskill.be/',
    'depends': ['sms', 'web', 'mail'],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            'hm_whatsapp/static/src/components/*/*',
        ],
    },
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
