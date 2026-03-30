# -*- coding: utf-8 -*-
# Merge module hm_base

from odoo import api, fields, models, _


class Region(models.Model):
    _name = "region.code"
    _description = "Region code"

    name = fields.Char(string="Region", required=True)


class CountryState(models.Model):
    _inherit = 'res.country.state'

    region = fields.Many2one(comodel_name='region.code', string="Region")
