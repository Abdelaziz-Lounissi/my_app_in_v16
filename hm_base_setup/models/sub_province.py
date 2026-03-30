# -*- coding: utf-8 -*-
# Merge module hm_base

from odoo import api, fields, models, _


class SubProvince(models.Model):
    _name = "sub.province"
    _description = "Sub province"

    name = fields.Char(string="Sous province")
