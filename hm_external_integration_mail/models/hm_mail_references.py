# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HmMailReferences(models.Model):
    _name = "hm.mail.references"
    _description = "Hm Mail References"

    name = fields.Char(string='Name')
    references = fields.Text(string='References')
    x_odoo_objects = fields.Char(string='X-Odoo-Objects')
    lead_id = fields.Many2one(comodel_name="crm.lead", string='Lead')
    mail_domain_name = fields.Char(string='Domain name')
