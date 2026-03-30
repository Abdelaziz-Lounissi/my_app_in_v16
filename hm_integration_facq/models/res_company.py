# -*- coding: utf-8 -*-
# © 2018 Net Skill Group

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    user_id = fields.Char('UserID', default='567419', required=True)
    login = fields.Char('Login', default='fkb310', required=True)
    password = fields.Char('Password', default='qvb692', required=True)
    culture_id = fields.Char('CultureID', default='FR', required=True)
    facq_path = fields.Char('File Path')
