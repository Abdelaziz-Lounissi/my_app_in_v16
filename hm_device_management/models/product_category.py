# -*- coding: utf-8 -*-

from odoo import api, fields, models
import ast


class ProductCategory(models.Model):
    _inherit = 'product.category'

    def _check_group_update_technical_value(self):
        return not self.user.has_group('base.group_system')

    technical_value = fields.Char("Technical value", readonly=_check_group_update_technical_value)
