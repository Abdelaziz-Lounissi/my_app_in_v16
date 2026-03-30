# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.product_id', 'order_line.purchase_price', 'order_line.product_uom_qty', 'order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total', 'order_line.purchase_line_ids.price_subtotal')
    def _compute_amount_total(self):
        po_obj = self.env['purchase.order']
        for so in self:
            total_budget = 0.0
            total_labor_budget = 0.0
            for ln in so.order_line:
                total_budget += ln.amount_budget
                total_labor_budget += ln.amount_labor

            total_budget_used = 0.0
            for po in po_obj.search(
                    [('hm_so_lie', '=', so.id), ('state', 'not in', ('draft', 'cancel', 'sent', 'to approve')),
                     ('is_po_emport', '=', True)]):
                total_budget_used += po.total_used_budget

            so.amount_budget = total_budget
            so.amount_budget_remaining = total_budget - total_budget_used
            so.amount_labor_budget = total_labor_budget

    amount_budget = fields.Monetary(compute='_compute_amount_total', string='Total budget', store = True,compute_sudo=True)
    amount_budget_remaining = fields.Monetary(compute='_compute_amount_total', string='Total budget remaining',compute_sudo=True)
    amount_labor_budget = fields.Monetary(compute='_compute_amount_total', string='Total labor budget', store = True,compute_sudo=True)

    def name_get(self):
        if self._context.get('purchase_order_classique_emport'):
            res = []
            for order in self:
                name = ' / '.join(filter(None, [order.name, order.hm_work_object, order.partner_id.display_name,
                                                 order.property_id.display_name]))
                res.append((order.id, name))
            return res
        return super().name_get()

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not self._context.get('purchase_order_classique_emport'):
            res = super(SaleOrder, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
            return res

        args = args or []
        domain = []
        if name:
            domain = [
                '|',
                '|',
                '|',
                ('partner_id', 'ilike', name),
                ('name', operator, name),
                ('property_id', 'ilike', name),
                ('hm_imputed_technician_id', 'ilike', name)
            ]
        account_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return account_ids

    def action_open_lines(self):
        self.ensure_one()
        actions = self.env.ref('hm_purchase_sale_budget.action_order_line_sections').read()[0]
        actions['domain'] = [('id', 'in', self.order_line.filtered(lambda ln: not ln.display_type).ids)]
        return actions
