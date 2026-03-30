# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    def write(self, vals):
        res = super(MrpBom, self).write(vals)
        self.bom_line_ids.update_product_cost_sale_price()
        return res

    @api.model_create_multi
    def create(self, vals):
        res = super(MrpBom, self).create(vals)
        res.bom_line_ids.update_product_cost_sale_price()
        return res


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    # update variant cost/sale price based on Bom Line create/update
    @api.model
    def update_product_cost_sale_price(self):
        # calcul and update the variant extra price(prix de vente)
        product_tmpl_id = self.bom_id.product_tmpl_id
        if len(product_tmpl_id.product_variant_ids) > 1:
            product_tmpl_id.with_context(product_tmpl_id=product_tmpl_id).update_product_variants_cost_price_extra()
        else:
            # calcul and update template sale & cost price
            product_tmpl_id.product_variant_ids.with_context(upt_from_bom_line=True).update_bom_template_cost_sale_price()
