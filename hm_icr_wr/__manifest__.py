# -*- coding: utf-8 -*-
{
    'name': 'HeatMe : ICR & Work Report',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'ICR/WR',
    'summary': 'ICR & Work Report Management',
    'website': 'https://netskill.be/',
    'depends': ['base', 'hm_picture_library', 'hm_sale', 'hm_sale_crm'],
    'data': [
        'security/ir.model.access.csv',

        'views/hm_picture_library_view.xml',
        'views/crm_lead.xml',
        'views/hm_icr_view.xml',
        'views/hm_wr_view.xml',
        'views/menu_view.xml',
        'views/purchase_order_view.xml',
        'views/sale_order_view.xml',
        'views/intervention_proposal_view.xml',
    ],
    # 'qweb': [
    #     'static/src/xml/hm_create_kanban.xml',
    #     'static/src/xml/base.xml',
    # ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
