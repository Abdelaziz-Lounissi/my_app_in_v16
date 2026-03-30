# -*- coding: utf-8 -*-
# Merge module hm_account_custom


from odoo import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == 'percentage':
            amount = float(40)
            return {'value': {'amount': amount}}
        return {}
