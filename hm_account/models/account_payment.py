# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    sender_bank_account = fields.Char(string="Sender bank account", compute="_compute_sender_bank_account")

    def _compute_sender_bank_account(self):
        for payment in self:
            bank_account = False
            for move_line in payment.move_line_ids:
                if move_line.statement_line_id and move_line.statement_line_id.account_number:
                    bank_account = move_line.statement_line_id.account_number
                    break
            payment.sender_bank_account = bank_account

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id and self.partner_id.customer_payment_mode_id.payment_type == 'inbound':
            self.payment_type = 'inbound'
        elif self.partner_id and self.partner_id.supplier_payment_mode_id.payment_type == 'outbound':
            self.payment_type = 'outbound'
        else:
            self.payment_type = 'outbound'