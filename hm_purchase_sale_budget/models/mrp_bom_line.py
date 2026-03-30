# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.depends(
        'product_id.is_labor_budget',
        'product_id.is_product_budget',
        'product_id.bom_count',
        'product_id.standard_price',
        'product_id.uom_id',
        'product_uom_id',
        'product_qty',
    )
    def _compute_amount_budget(self):
        for rec in self:
            total_budget = 0
            total_labor = 0
            if rec.product_id.bom_count > 0:
                bom_price = (
                    rec.product_id.uom_id._compute_price(
                        rec.product_id.budget_price, rec.product_uom_id
                    )
                    * rec.product_qty
                )
                total_budget += bom_price
                total_labor += bom_price
            elif rec.product_id.is_product_budget:
                total_budget += (
                    rec.product_id.uom_id._compute_price(
                        rec.product_id.standard_price, rec.product_uom_id
                    )
                    * rec.product_qty
                )
            elif rec.product_id.is_labor_budget:
                total_labor += (
                    rec.product_id.uom_id._compute_price(
                        rec.product_id.standard_price, rec.product_uom_id
                    )
                    * rec.product_qty
                )

            rec.amount_budget = total_budget
            rec.amount_labor = total_labor

    # x_studio_prix_de_vente
    hm_lst_price = fields.Float(related='product_id.lst_price', related_sudo=True)
    # x_studio_cout_unit
    hm_standard_price = fields.Float(related='product_id.standard_price', related_sudo=True)
    amount_budget = fields.Float(
        compute='_compute_amount_budget', string='Amount Budget'
    )
    amount_labor = fields.Float(
        compute='_compute_amount_budget', string='Amount Labor'
    )
