# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('is_product_budget')
    def onchange_variant_is_product_budget(self):
        route_buy_id = self.env.ref(
            'purchase_stock.route_warehouse0_buy', raise_if_not_found=False
        )
        route_mto_id = self.env.ref(
            'stock.route_warehouse0_mto', raise_if_not_found=False
        )
        new_routes = []
        if self.is_product_budget:
            if route_buy_id:
                new_routes.append((3, route_buy_id.id))
            if route_mto_id:
                new_routes.append((3, route_mto_id.id))

        else:
            if route_buy_id:
                new_routes.append((4, route_buy_id.id))
            if route_mto_id:
                new_routes.append((4, route_mto_id.id))

        if new_routes:
            self.route_ids = new_routes

    @api.depends('is_product_budget', 'is_labor_budget')
    def _compute_label_section(self):
        for product in self:
            labels = []
            if product.is_product_budget:
                labels.append('Budget')
            if product.is_labor_budget:
                labels.append('Labor')

            product.label_section = ', '.join(labels)

    @api.depends('is_product_budget', 'is_labor_budget', 'bom_count')
    def _compute_budget_price(self):
        for product in self:
            if product.bom_count > 0:
                total_amount_budget = 0
                total_labor_standard_price = 0
                if product.product_template_attribute_value_ids:
                    for attribute in product.product_template_attribute_value_ids:
                        for bom in product.bom_ids:
                            for line in bom.bom_line_ids:
                                if not line.bom_product_template_attribute_value_ids or attribute in line.bom_product_template_attribute_value_ids and not line._skip_bom_line(product):
                                    total_amount_budget += line.amount_budget
                                    total_labor_standard_price += line.amount_labor
                else:
                    for bom in product.bom_ids:
                        for line in bom.bom_line_ids:
                            if not line._skip_bom_line(product):
                                total_amount_budget += line.amount_budget
                                total_labor_standard_price += line.amount_labor

                product.budget_price = total_amount_budget
                product.budget_labor = total_labor_standard_price
            else:
                product.budget_price = 0.0
                product.budget_labor = 0.0

    budget_labor = fields.Float(
        string='Budget labor', compute='_compute_budget_price'
    )
    budget_price = fields.Float(
        string='Budget BOM', compute='_compute_budget_price'
    )
    label_section = fields.Char(compute='_compute_label_section', store=True)

