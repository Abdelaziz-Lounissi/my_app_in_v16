# -*- encoding: utf-8 -*-

from odoo import fields, models, api


class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    requisition_id = fields.Many2one('purchase.requisition', string='Contrat-cadre')
