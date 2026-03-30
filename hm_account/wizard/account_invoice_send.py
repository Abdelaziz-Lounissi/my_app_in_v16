# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _


class AccountInvoiceSend(models.TransientModel):
    _name = 'account.invoice.send'
    _inherit = 'account.invoice.send'

    def send_and_print_action(self):
        res = super(AccountInvoiceSend, self).send_and_print_action()

        # Add SO manager on invoice chatter
        res_ids = self._context.get('active_ids')
        invoices = self.env['account.move'].browse(res_ids).filtered(lambda move: move.is_invoice(include_receipts=True))
        for inv in invoices:
            inv.message_subscribe(partner_ids=[(inv.sale_order_id.hm_so_manager_id.partner_id.id)])
        return res

