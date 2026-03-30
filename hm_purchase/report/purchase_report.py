# -*- coding: utf-8 -*-
# Merge module hm_sale_purchase_custom

from odoo import _, fields, models


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    state = fields.Selection(
        selection_add=[
            ('sent_to_supplier', _('Sent to Supplier')),
            ('confirmed', _('Confirmed')),
        ]
    )
