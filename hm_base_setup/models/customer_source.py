# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CustomerSource(models.Model):
    _name = "customer.source"
    _description = "Customer Source"
    _order = "name"

    name = fields.Char(string='Customer Source Name', required=True, translate=True)
