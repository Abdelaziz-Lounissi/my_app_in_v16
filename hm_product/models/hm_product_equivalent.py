# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HmProductEquivalent(models.Model):
    _name = "hm.product.equivalent"
    _description = "Product Equivalent"

    name = fields.Char(string='Equivalent')
