# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HmMailDomain(models.Model):
    _name = "hm.mail.domain"
    _description = "Hm Mail Domain"

    name = fields.Char(string='Domain name')
