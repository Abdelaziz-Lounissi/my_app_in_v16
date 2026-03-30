# -*- coding: utf-8 -*-
from odoo import fields, models


class LinkedPurchaseOrderLines(models.TransientModel):
    _name = 'linked.purchase.order.lines'
    _description = 'Linked Purchase order line'
    _inherits = {
        'purchase.order.line': 'po_line_id',
    }
    # ID of existing PO
    po_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        required=True,
        string='Purchase Order line',
    )
    # ID of new PO created or purposed
    line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        required=True,
        string='New Purchase Order line',
    )
    qty_delivered = fields.Float(
        related='po_line_id.sale_line_id.qty_delivered',
        string='Delivered Qty', related_sudo=True,
    )
    # new data
    new_product_uom_qty = fields.Float(string='Proposed Qty')
    new_product_id = fields.Many2one(
        comodel_name='product.product', string='Product New',
    )
    new_name = fields.Char(string='Proposed Description')

    def action_open_po(self):
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action.pop('view_id', None)
        action.pop('views', None)
        action.update(
            {
                'view_mode': 'form',
                'domain': [('id', '=', self.po_line_id.order_id.id)],
                'res_id': self.po_line_id.order_id.id,
            }
        )
        return action
