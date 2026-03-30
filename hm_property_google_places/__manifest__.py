# -*- coding: utf-8 -*-
{
    'name': 'Property Google Places',
    'version': '16.0.1.0.2',
    'author': 'Aziz, Netskill Group(NSG)',
    'license': 'AGPL-3',
    'website': 'https://netskill.be/',
    'category': 'Extra Tools',
    'summary': 'Property Google Places',
    'description': """
Property Google Places
======================

Add Additional information to your Property.
This module using Google Places as a source data, so the information you would get should be reliable.

You can create a new contact within Google maps by:
1. Click place on Google Maps.
2. By search. You can do search by address, name, or type of place.
""",
    'depends': [
        'base_google_places',
        'hm_property_google_map',
    ],
    'website': 'https://github.com/mithnusa',
    'data': ['views/hm_property.xml'],
    'assets': {
        'web.assets_backend': [
            'hm_property_google_places/static/src/views/**/*',
        ]
    },
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
