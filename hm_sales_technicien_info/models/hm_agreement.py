# -*- coding: utf-8 -*-
# ############################################################################
from odoo import _, fields, models


class HmAgreement(models.Model):
    _name = 'hm.agreement'
    _description = 'Agreement'

    name = fields.Char(string='Name')

    _sql_constraint = [
        ('name_unique', 'UNIQUE(name)', _('Name must be unique!'))
    ]
