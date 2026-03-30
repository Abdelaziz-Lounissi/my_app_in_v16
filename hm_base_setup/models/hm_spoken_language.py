# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HmSpokenLanguage(models.Model):
    _name = "hm.spoken.language"
    _description = "Spoken Language"

    name = fields.Char(string="Name", copy=False, store=True, index=False, translate=False)
