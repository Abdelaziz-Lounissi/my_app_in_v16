# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'HeatMe : Purchase requisition',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Purchase',
    'description': """
""",
    'depends': ['purchase_requisition', 'sale_management'],
    'demo': ['data/purchase_requisition_demo.xml'],
    'data': [
        'views/purchase_requisition_views.xml',
        'views/sale_order_template_views.xml'
    ],
    'license': 'LGPL-3',
}
