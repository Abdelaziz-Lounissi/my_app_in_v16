# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def open_action_check_supplier(self):
        self.ensure_one()
        view = self.env.ref('additional_supplier.check_supplier_form_view')
        return {
            'name': _('Check Supplier'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'check.supplier',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': {'purchase_id': self.id},
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id', related_sudo=True)
    supplier_choice = fields.Many2one('product.supplierinfo', string='Supplier Choice', domain="['|', ('product_tmpl_id', 'in', equivalent_product_ids), ('product_tmpl_id', '=', product_tmpl_id)]")
    equivalent_product_ids = fields.Many2many('product.template', related='product_tmpl_id.equivalent_product_ids', string='Equivalent Products', related_sudo=True)
