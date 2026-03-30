# -*- coding: utf-8 -*-
{
    'name': 'Property Google Map',
    'summary': '''
        Show your Properties in Google maps view
    ''',
    'description': '''
        A new view 'Google maps' added on Property, gives you
        an ability to show your Property location in Google maps
    ''',
    'license': 'AGPL-3',
    'author': 'Aziz, Netskill Group(NSG)',
    'website': 'https://netskill.be/',
    'category': 'Extra Tools',
    'version': '16.0.2.1.3',
    'depends': [
        'base_geolocalize',
        'hm_property',
        'web_view_google_map',
    ],
    'data': ['views/hm_property.xml'],
    'assets': {
        'web.assets_backend': [
            'hm_property_google_map/static/src/views/**/*',
        ]
    },
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
