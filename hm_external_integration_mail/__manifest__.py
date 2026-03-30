# -*- coding: utf-8 -*-

{
    'name': 'HeatMe : External integration mail',
    'summary': '',
    'description': 'External integration mail',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'mail',
    'license': 'AGPL-3',
    'website': 'http://netskill.be',
    'version': '13.0.1.0.0',
    'installable': True,
    'auto_install': False,
    'depends': ['mail', 'crm'],
    'data': [
            'views/hm_mail_domain_views.xml',
            'views/hm_mail_references_views.xml',
            'views/menu_views.xml',
            'security/ir.model.access.csv',
    ],
}
