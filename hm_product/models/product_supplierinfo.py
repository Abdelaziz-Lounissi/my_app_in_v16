# -*- coding: utf-8 -*-

from odoo import fields, models


class SupplierInfo(models.Model):
    _name = 'product.supplierinfo'
    _inherit = ['product.supplierinfo', 'mail.thread', 'mail.activity.mixin']

    # hm_negotiated_discount
    # TODO: debug, do we still need it?
    hm_max_obtained_discount = fields.Float(string='Maximum obtained discount(%)', index=False, copy=False, tracking=True)

    def open_supplier_info(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.supplierinfo',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'views': [[self.env.ref('product.product_supplierinfo_form_view').id, 'form']],
        }
