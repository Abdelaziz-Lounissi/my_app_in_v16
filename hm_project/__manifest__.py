# -*- coding: utf-8 -*-
{
    'name': 'HeatMe : Project',
    'version': '16.0.1.0.0',
    'author': 'Aziz, Netskill Group(NSG)',
    'category': 'Project',
    'summary': 'Operations/Project',
    'website': 'https://netskill.be/',
    "depends": ["project"],
    "data": [
        "security/ir.model.access.csv",
        "views/project_version_view.xml",
        "views/project_views.xml",
        "views/task_view.xml",
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
