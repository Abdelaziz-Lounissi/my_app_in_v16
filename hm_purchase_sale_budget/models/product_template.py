# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_product_budget = fields.Boolean(default=False, string='Article budget?')
    budget_price = fields.Float(
        string='Budget BOM', compute='_compute_budget_price'
    )
    is_labor_budget = fields.Boolean(default=False, string='Labor Budget?')
    budget_labor = fields.Float(
        string='Budget labor', compute='_compute_budget_price'
    )
    label_section = fields.Char(compute='_compute_label_section', store=True)

    @api.depends('is_product_budget', 'is_labor_budget', 'bom_count')
    def _compute_budget_price(self):
        for product in self:
            if product.bom_count > 0:
                product.budget_price = sum(
                    bom.budget_standard_price for bom in product.bom_ids
                )
                product.budget_labor = sum(
                    bom.labor_standard_price for bom in product.bom_ids
                )
            else:
                product.budget_price = 0.0
                product.budget_labor = 0.0

    @api.depends('is_product_budget', 'is_labor_budget')
    def _compute_label_section(self):
        for product in self:
            labels = []
            if product.is_product_budget:
                labels.append('Budget')
            if product.is_labor_budget:
                labels.append('Labor')

            product.label_section = ', '.join(labels)

    @api.onchange('is_product_budget')
    def onchange_template_is_product_budget(self):
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
