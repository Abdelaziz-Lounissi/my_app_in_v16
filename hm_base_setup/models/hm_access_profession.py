# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HmAccessProfession(models.Model):
    _name = "hm.access.profession"
    _description = "Access To The Profession"

    name = fields.Char(string="Name", copy=False, store=True, index=False, translate=True)
