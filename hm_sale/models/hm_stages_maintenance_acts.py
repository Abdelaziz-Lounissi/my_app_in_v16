# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HmStagesMaintenanceActs(models.Model):
    _name = "hm.stages.maintenance.acts"
    _description = "Stages Maintenance Acts"

    name = fields.Char(string="Name", copy=False, store=True, index=False, translate=False)
