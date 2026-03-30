# -*- coding: utf-8 -*-
{
    'name': 'HeatMe: Automation Tracking & Notifications',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group (NSG)',
    'category': 'Automation/Technical',
    'summary': 'Advanced tracking and notifications for automation rule changes',
    'website': 'https://netskill.be/',
    "depends": ["base", "mail", "base_automation"],
    "data": [
        "views/ir_act_server_views.xml",
        "views/base_automation_views.xml",
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
