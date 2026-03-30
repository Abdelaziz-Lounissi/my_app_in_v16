# -*- coding: utf-8 -*-
{
    'name': 'Property Google Autocomplete Address form extended',
    'summary': '''
        Extended version of Property Google Autocomplete Address form
    ''',
    'description': '''
        Extended version of Property Google Autocomplete Address form
        Added some more info (Google Address, Place ID, Place URL, Opening Hours, Types, Global Code, Compound Code, Plus code URL, Vicinity) of a place from Google place into Odoo
    ''',
    'license': 'AGPL-3',
    'author': 'Aziz, Netskill Group(NSG)',
    'website': 'https://netskill.be/',
    'category': 'Extra Tools',
    'version': '16.0.1.0.0',
    'depends': [
        'hm_property_gautocomplete_address_form',
        'web_widget_google_places',
        'hm_property_google_places',
    ],
    'data': ['views/hm_property.xml'],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
