# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings']

    hm_so_manager_workload_ratio = fields.Integer(default=0, config_parameter='hm_sale_crm.hm_so_manager_workload_ratio')


    @api.constrains('hm_so_manager_workload_ratio')
    def constrains_workload_ratio(self):
        for rec in self:
            if rec.hm_so_manager_workload_ratio < 0:
                raise ValidationError('la valeur du  Ratio charge de gestion doit être supérieure ou égale à 0')


