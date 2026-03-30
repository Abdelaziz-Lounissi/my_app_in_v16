# -*- encoding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    agreement_id = fields.Many2one('hm.agreement', string='Agreement')

    @api.onchange('agreement_id')
    def onchange_agreement(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_id.agreement_id = self.agreement_id and self.agreement_id.id or False

    def update_product_agreement(self):
        template_obj = self.env['product.template']
        product_template_ids = template_obj.search([('tmpl_variant_count', '=', 1), ('agreement_id', '!=', False)])
        for product_template_id in product_template_ids:
            product_template_id.product_variant_id.agreement_id = product_template_id.agreement_id and product_template_id.agreement_id.id or False


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model_create_multi
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        if res.product_tmpl_id.agreement_id and res.product_tmpl_id.product_variant_count == 1:
            res.agreement_id = res.product_tmpl_id.agreement_id.id
        return res

    agreement_id = fields.Many2one('hm.agreement', string='Agreement')