# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_label_section = fields.Char(
        compute='_compute_line_section', store=True, string='Section',
    )
    is_po_emport = fields.Boolean(string='PO Emport', default=False)
    amount_budget = fields.Float(
        compute='_compute_amount_budget', string='Budget Marchandise'
    )
    amount_labor = fields.Float(
        compute='_compute_amount_budget', string='Budget MO'
    )

    @api.depends('is_po_emport', 'product_id.label_section')
    def _compute_line_section(self):
        for line in self:
            section = [line.product_id.label_section or '']
            if line.is_po_emport:
                section.append('PO Emport')

            if line.is_po_emport and 'Budget' in line.product_id.label_section:
                section.append('PO Emport Budget')

            line.line_label_section = ', '.join(section)

    @api.depends('product_id.bom_count','product_id.is_product_budget','product_id.is_labor_budget','purchase_price','product_uom_qty')
    def _compute_amount_budget(self):
        for line in self:
            total_budget = 0.0
            total_labor_budget = 0.0

            if line.product_id.bom_count > 0:
                total_budget += (
                    line.product_uom_qty * line.product_id.budget_price
                )
                total_labor_budget += (
                    line.product_uom_qty * line.product_id.budget_labor
                )
            elif line.product_id.is_product_budget:
                total_budget += line.purchase_price * line.product_uom_qty
            elif line.product_id.is_labor_budget:
                total_labor_budget += (
                    line.purchase_price * line.product_uom_qty
                )

            line.amount_budget = total_budget
            line.amount_labor = total_labor_budget
