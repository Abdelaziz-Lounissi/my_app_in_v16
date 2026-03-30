# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    supplier_reference = fields.Char(required=True, string="Référence fournisseur")
