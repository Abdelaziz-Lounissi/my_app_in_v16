# -*- coding: utf-8 -*-
{
    'name': 'HeatMe : Purchase',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'Purchases',
    'summary': 'Purchases Management',
    'website': 'https://netskill.be/',
    "depends": ["hm_sale_purchase", "sale_margin", "stock", "hm_property"],
    "data": [
        "data/mail_template.xml",
        "data/ir_actions_server.xml",
        "data/ir_cron.xml",
        "data/base_automation.xml",
        "data/purchase_data.xml",
        "data/purchase_stage_data.xml",
        "data/activity_type_view.xml",

        "security/ir.model.access.csv",

        "views/purchase_order_view.xml",
        "views/purchase_order_line_stage_view.xml",
        'views/nc_receivable.xml',
        'views/purchase_order_line_view.xml',
        'views/res_partner_view.xml',
        'views/stock_move_view.xml',
        'views/purchase_order_portal_templates.xml',

        # reports
        "views/purchase_report.xml",
        "views/report_purchase_order.xml",
        "views/report_technician_billing_order.xml",
        "views/report_purchase_order_without_price.xml",

    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
