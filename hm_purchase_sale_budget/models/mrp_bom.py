# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # TODO: debug if still need it
    budget_standard_price = fields.Float(
        compute='_compute_amount_budget', string='Budget Cost',
    )
    labor_standard_price = fields.Float(
        compute='_compute_amount_budget', string='Labor Cost',
    )

    @api.depends('bom_line_ids.amount_labor', 'bom_line_ids.amount_budget')
    def _compute_amount_budget(self):
        for bom in self:
            product = bom.product_id or bom.product_tmpl_id
            bom.budget_standard_price = sum(
                line.amount_budget
                for line in bom.bom_line_ids
                if not line._skip_bom_line(product)
            )
            bom.labor_standard_price = sum(
                line.amount_labor
                for line in bom.bom_line_ids
                if not line._skip_bom_line(product)
            )

    def _update_is_product_budget(self):
        for bom in self:
            if bom.product_id:
                bom.product_id.write(
                    {'is_product_budget': False, 'is_labor_budget': False}
                )
            elif bom.product_tmpl_id:
                bom.product_tmpl_id.write(
                    {'is_product_budget': False, 'is_labor_budget': False}
                )

    @api.model_create_multi
    def create(self, values):
        res = super(MrpBom, self).create(values)
        res._update_is_product_budget()
        return res

    def write(self, values):
        res = super(MrpBom, self).write(values)
        self._update_is_product_budget()

        return res
