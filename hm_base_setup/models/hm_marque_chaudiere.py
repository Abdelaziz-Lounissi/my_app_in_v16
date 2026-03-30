# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HmBoilerBrand(models.Model):
    _name = "hm.marque.chaudiere"
    _description = "Marque chaudière"

    name = fields.Char(string="Name", copy=False, store=True, index=False, translate=False)
