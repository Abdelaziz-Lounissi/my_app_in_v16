# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _default_picking_type_emport(self):
        if self._context.get('purchase_order_emport'):
            picking_type_id = (
                self.env['stock.picking.type']
                .with_context(lang='en_US')
                .search([('code', '=', 'incoming'), ('name', '=', 'Dropship')])
            )
            if picking_type_id:
                return picking_type_id

        res = self._default_picking_type()
        return res

    picking_type_id = fields.Many2one(default=_default_picking_type_emport)
    # new fields
    is_po_emport = fields.Boolean(default=False, string='Is Purchase Order Emport?')
    sale_order_total_budget = fields.Monetary(string='Total budget', compute='_compute_total_budget')
    total_used_budget = fields.Monetary(string='Total budget used', compute='_compute_total_budget',)
    total_budget_left = fields.Monetary(string='Remaining budget', compute='_compute_total_budget',)
    is_emport_sale_order_readonly = fields.Boolean(compute='_compute_is_emport_sale_order_readonly')

    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrder, self).default_get(fields)
        if self.env.context.get('purchase_order_emport'):
            res['is_po_emport'] = True
        return res

    @api.depends('order_line.sale_line_id')
    def _compute_is_emport_sale_order_readonly(self):
        for rec in self:
            rec.is_emport_sale_order_readonly = (
                True
                if rec.order_line.filtered(lambda l: l.sale_line_id)
                else False
            )

    @api.onchange('hm_so_lie')
    def _onchange_hm_so_lie(self):
        self.order_line.sale_order_id = self.hm_so_lie and self.hm_so_lie.id or False
        if self.is_po_emport:
            self.origin = (self.hm_so_lie and self.hm_so_lie.name or '')

    @api.depends('hm_so_lie', 'is_po_emport', 'order_line.sale_line_id')
    def _compute_total_budget(self):
        po_obj = self.env['purchase.order']
        for purchase_order in self:
            purchase_order.sale_order_total_budget = (purchase_order.hm_so_lie.amount_budget)
            total_used_budget = sum(
                ln.price_subtotal
                for ln in purchase_order.order_line
                if not ln.sale_line_id
            )
            purchase_order.total_used_budget = total_used_budget
            if purchase_order.hm_so_lie:
                other_po_ids = po_obj.search([('hm_so_lie', '=', purchase_order.hm_so_lie.id),
                                              ('state', 'not in', ('draft', 'cancel', 'sent', 'to approve')),
                                              ('is_po_emport', '=', True)])
                consumed_budget = 0.0
                for other_po in other_po_ids.filtered(lambda other_po: other_po.id != purchase_order.id):
                    for other_po_line in other_po.order_line:
                        if not other_po_line.sale_line_id:
                            consumed_budget += other_po_line.price_subtotal

                total_budget_left = (purchase_order.hm_so_lie.amount_budget - (consumed_budget + total_used_budget))
                purchase_order.total_budget_left = total_budget_left
            else:
                purchase_order.total_budget_left = 0.0

    # TODO: delete me after tests
    # def action_add_lines_to_saleorder(self):
    #     self.ensure_one()
    #     for line in self.order_line:
    #         if not line.sale_order_id and line.qty_received > 0:
    #             line.action_link_to_sale_order()

    def action_open_other_po_emport(self):
        self.ensure_one()
        other_po_ids = self.env[self._name].search(
            [('hm_so_lie', '=', self.hm_so_lie.id), ('state', 'not in', ('draft', 'cancel', 'sent', 'to approve')),
             ('is_po_emport', '=', True)])
        tree_view_id = self.env.ref('hm_purchase_sale_budget.view_purchase_order_tree_other_pos_budget')
        view_form_id = self.env.ref('hm_purchase_sale_budget.hm_purchase_budget_form_view')
        return {
            'name': _('Purchase order related'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'tree,form',
            'views': [(tree_view_id.id, 'tree'), (view_form_id.id, 'form')],
            'domain': [('id', 'in', other_po_ids.ids)],
        }
