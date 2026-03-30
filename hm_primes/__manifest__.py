# -*- coding: utf-8 -*-
{
    'name': 'HeatMe : Primes',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'Documents/Pictures',
    'summary': 'Primes Management',
    'website': 'https://netskill.be/',
    # TODO: fix depends
    'depends': [
        'base',
        'hm_sales_technicien_info'
    ],
    'data': [
        'security/primes_security.xml',
        'security/ir.model.access.csv',
        'views/primes_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
