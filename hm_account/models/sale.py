# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # TODO: not clean: forcing ids
    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        res = super(SaleOrder, self)._get_invoiced()
        for order in self:
            invoices = self.env['account.move'].search(
                [('sale_order_id', '=', order.id), ('move_type', 'in', ['out_invoice', 'out_refund'])])
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)
        return res
