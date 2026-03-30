# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SMSTemplate(models.Model):
    _inherit = "sms.template"

    number_field_name = fields.Char(string='Champ contenant le numéro de téléphone du destinataire')
