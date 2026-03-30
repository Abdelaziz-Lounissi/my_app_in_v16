# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ProductProduct(models.Model):
    _inherit = "product.product"

    def write(self, values):
        res = super(ProductProduct, self).write(values)
        if 'description_sale' in values:
            if self.product_variant_id:
                sale_order_lines = self.env['sale.order.template.line'].search([('product_id', '=', self.product_variant_id.id)])
                description = values['description_sale']
                for line in sale_order_lines:
                    if line.spec or line.spec == "":
                        line.write({'name': ">> " + line.spec + "\n" + description})
        return res