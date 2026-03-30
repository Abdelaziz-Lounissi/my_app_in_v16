# -*- coding: utf-8 -*-

from odoo import fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    hm_lead_transmis_id = fields.Many2one(string="Lead forwarded by", related='opportunity_id.hm_lead_transmis_id', store=True, precompute=True)
