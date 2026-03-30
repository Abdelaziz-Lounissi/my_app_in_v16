# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    priority = fields.Selection(selection_add=[
        ("0", "Lowest"), ("1", "Low"), ("2", "Medium"), ("3", "High")
    ], default='0', index=True, string="Priority", tracking=True)
    version_id = fields.Many2one("project.version", string="Version")
    nsg_task_id = fields.Integer(string="NSG Task ID")