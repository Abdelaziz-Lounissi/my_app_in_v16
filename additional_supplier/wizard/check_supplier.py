# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CheckSupplier(models.TransientModel):
    _name = "check.supplier"
    _description = "Check Supplier"

    po_lines = fields.One2many('purchase.order.line', 'order_id', string='PO Lines')

    @api.model
    def _create_update_po_line(self, purchase_id, po_line, type):
        if type == 'new':
            # Update the supplier of the new PO to the selected one
            purchase_id.partner_id = po_line.supplier_choice.partner_id

        product_id = po_line.supplier_choice.product_tmpl_id.product_variant_id
        if product_id:
            po_line.product_id = product_id
            if type == 'update':
                # Link the PO line to the found PO
                purchase_id.order_line |= po_line
            else:
                purchase_id.order_line = [(6, 0, [po_line.id])]

            product_qty = po_line.product_qty
            po_line.onchange_product_id()
            po_line.product_qty = product_qty

    def check_supplier(self):
        purchase_obj = self.env['purchase.order']
        po_id = purchase_obj.browse(self._context.get('purchase_id'))
        for po_line in self.po_lines:
            if po_line.supplier_choice and po_id.hm_so_lie:
                purchase_id = purchase_obj.search([('id', '!=', po_id.id), ('state', '=', 'draft'),
                     ('partner_id', '=', po_line.supplier_choice.partner_id.id),
                     ('hm_so_lie', '=', po_id.hm_so_lie.id)], limit=1)
                if purchase_id:
                    # We found a matching PO, so we're going to link the PO line.
                    self._create_update_po_line(purchase_id=purchase_id, po_line=po_line, type='update')
                else:
                    # No matching PO found, therefore, we'll duplicate the original PO and link the PO line
                    purchase_id = po_id.copy()
                    self._create_update_po_line(purchase_id=purchase_id, po_line=po_line, type='new')

        if not po_id.order_line:
            po_id.button_cancel()

    def check_supplier_cancel(self):
        for po_line in self.po_lines:
            if po_line.supplier_choice:
                po_line.supplier_choice = False
        return {'type': 'ir.actions.act_window_close'}