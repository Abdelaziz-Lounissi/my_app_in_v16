# -*- coding: utf-8 -*-
from odoo import _, api, exceptions, fields, models

# todo: review this class: do we still using it ? teh emport po?

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    potential_match_line = fields.Many2many('purchase.order.line', compute='_compute_potential_matched_line')
    potential_match_line_count = fields.Integer(compute='_compute_potential_matched_line',
                                                string='Number of potential duplicates')
    is_po_emport = fields.Boolean(related='order_id.is_po_emport', related_sudo=True)

    @api.depends('product_id', 'order_id.hm_so_lie', 'order_id.is_po_emport')
    def _compute_potential_matched_line(self):
        for rec in self:
            if rec.order_id.hm_so_lie and rec.order_id.is_po_emport:
                params = {'sale_order_id': rec.order_id.hm_so_lie.id}
                query = '''
                SELECT id
                FROM purchase_order_line
                WHERE sale_order_id = %(sale_order_id)s
                '''
                if rec.product_id:
                    query += ' AND product_id = %(product_id)s'
                    params['product_id'] = rec.product_id.id

                self._cr.execute(query, params)
                lines = [i[0] for i in self._cr.fetchall()]
                matched = list(filter(lambda val: val != rec.id, lines))
                rec.potential_match_line = [(6, 0, matched)]
                rec.potential_match_line_count = len(matched)
            else:
                rec.potential_match_line = [(6, 0, [])]
                rec.potential_match_line_count = 0

    # TODO: delete me after tests
    # def _prepare_sale_order_line_values(self):
    #     last_sequence = self.order_id.hm_so_lie.order_line and max(
    #         self.order_id.hm_so_lie.order_line.mapped("sequence")) or 1
    #     return {
    #         'name': '[%s] %s' % (self.product_id.default_code, self.name)
    #         if self.product_id.default_code
    #         else self.name,
    #         'product_uom_qty': self.qty_received,
    #         'product_uom': self.product_uom.id,
    #         'product_id': self.product_id.id,
    #         'price_unit': self.price_unit,
    #         'purchase_line_ids': [(4, self.id)],
    #         'order_id': self.order_id.hm_so_lie.id,
    #         'is_po_emport': True,
    #         'qty_delivered_manual': self.qty_received,
    #         'qty_delivered_method': 'manual',
    #         'qty_delivered': self.qty_received,
    #         'sequence': last_sequence + 1,
    #     }

    def write(self, values):
        res = super(PurchaseOrderLine, self).write(values)
        if values.get('product_qty'):
            for line in self:
                if line.is_po_emport and line.sale_line_id:
                    line.sale_line_id.write(
                        {'product_uom_qty': line.product_uom_qty, 'product_uom': line.product_uom.id})
        return res

    def action_open_potential_duplicate(self):
        wzrd_linked_po_obj = self.env['linked.purchase.order.lines']

        wzrd_linked_po_obj.search([('line_id', '=', self.id), ('create_uid', '=', self._uid)]).unlink()
        linked_po_ids = self.env['linked.purchase.order.lines']
        for line in self.potential_match_line:
            linked_po_ids += wzrd_linked_po_obj.create(
                {
                    'line_id': self.id,
                    'po_line_id': line.id,
                    'new_product_uom_qty': self.product_uom_qty,
                    'new_product_id': self.product_id.id,
                    'new_name': self.name,
                }
            )

        return {
            'name': _('Existing lines found on other Purchase Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'linked.purchase.order.lines',
            'view_mode': 'tree',
            'domain': [('id', 'in', linked_po_ids.ids)],
        }

    # TODO: delete me after tests
    # def action_link_to_sale_order(self):
    #     so_line_obj = self.env['sale.order.line']
    #     for line in self:
    #         if (not line.sale_line_id and line.order_id.hm_so_lie and line.is_po_emport):
    #             values = line._prepare_sale_order_line_values()
    #             so_line = so_line_obj.new(values)
    #             so_line.product_id_change()
    #             so_line.product_uom_change()
    #             so_line._onchange_discount()
    #             new_values = so_line._convert_to_write(so_line._cache)
    #             so_line_id = so_line_obj.create(new_values)
    #             line.write({'sale_line_id': so_line_id.id})
    #             for picking in line.order_id.picking_ids:
    #                 for move_line in picking.move_ids_without_package:
    #                     if move_line.product_id.id == line.product_id.id:
    #                         picking.write({'sale_id': line.order_id.hm_so_lie.id})
    #             self._action_launch_stock_rule(so_line_id)

    # TODO: delete me after tests
    # def _action_launch_stock_rule(self, so_line_id):
    #     procurements = []
    #     group_id = so_line_id._get_procurement_group()
    #     procurement_group_obj = self.env['procurement.group']
    #     if not group_id:
    #         group_id = procurement_group_obj.create(so_line_id._prepare_procurement_group_vals())
    #         so_line_id.order_id.procurement_group_id = group_id
    #     else:
    #         # In case the procurement group is already created and the order was
    #         # cancelled, we need to update certain values of the group.
    #         updated_vals = {}
    #         if group_id.partner_id != so_line_id.order_id.partner_shipping_id:
    #             updated_vals.update({'partner_id': so_line_id.order_id.partner_shipping_id.id})
    #         if group_id.move_type != so_line_id.order_id.picking_policy:
    #             updated_vals.update({'move_type': so_line_id.order_id.picking_policy})
    #         if updated_vals:
    #             group_id.write(updated_vals)
    #
    #     qty = so_line_id._get_qty_procurement(False)
    #     values = so_line_id._prepare_procurement_values(group_id=group_id)
    #     product_qty = so_line_id.product_uom_qty - qty
    #
    #     line_uom = so_line_id.product_uom
    #     quant_uom = so_line_id.product_id.uom_id
    #     product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
    #     procurements.append(
    #         procurement_group_obj.Procurement(
    #             so_line_id.product_id,
    #             product_qty,
    #             procurement_uom,
    #             so_line_id.order_id.partner_shipping_id.property_stock_customer,
    #             so_line_id.name,
    #             so_line_id.order_id.name,
    #             so_line_id.order_id.company_id,
    #             values
    #         )
    #     )
    #     if procurements:
    #         procurement_group_obj.run(procurements)

    def action_unlink_from_sale_order(self):
        for line in self:
            if (line.is_po_emport and line.sale_line_id and line.sale_line_id.is_po_emport and len(line.order_id.invoice_ids) == 0):
                try:
                    immediate_return_line_ids = []
                    location_id = False
                    move_id = False
                    stock_picking = self.env['stock.picking'].search(
                        [('origin', '=', line.order_id.name), ('picking_type_id.code', '=', 'incoming'),
                         ('state', '=', 'done')])[-1]
                    if stock_picking:
                        for return_line in stock_picking.move_line_ids_without_package.filtered(
                                lambda x: x.product_id.id == line.product_id.id):
                            move_id = self.env['stock.move'].sudo().search([('reference','=',stock_picking.name),('product_id','=',return_line.product_id.id)]).id

                            location_id = return_line.location_dest_id.id
                            immediate_return_line_ids.append([0, False, {
                                'product_id': return_line.product_id.id,
                                'quantity': line.product_qty,
                                'uom_id': return_line.product_uom_id,
                                'move_id': move_id,
                                'to_refund': True
                            }])
                        exist_retour = self.env['stock.return.picking'].search([('picking_id','=',stock_picking.id)])
                        if exist_retour:
                            immediate_return_line_ids.append([0, False,  {
                                'product_id': exist_retour.product_return_moves.product_id.id,
                                'quantity': exist_retour.product_return_moves.quantity,
                                'uom_id': exist_retour.product_return_moves.uom_id,
                                'move_id': move_id,
                                'to_refund': True
                            }])
                            self.env['stock.return.picking'].create({
                                'picking_id': stock_picking.id,
                                'product_return_moves': immediate_return_line_ids,
                                'location_id': stock_picking.location_id.id
                            }).create_returns()
                        else:
                            self.env['stock.return.picking'].create({
                                'picking_id': stock_picking.id,
                                'product_return_moves': immediate_return_line_ids,
                                'location_id': stock_picking.location_id.id
                            }).create_returns()
                    pickings = self.env['stock.picking'].search([('origin', 'like', stock_picking.name)],limit=1)
                    sale_delivery = self.env['stock.immediate.transfer'].create({
                        'pick_ids': [(4, pickings.id)],
                    })
                    sale_delivery.with_context(button_validate_picking_ids=sale_delivery.pick_ids.ids).process()
                    params = {'line_id': line.id}
                    query = '''
                                delete
                                FROM purchase_order_line
                                WHERE  id = %(line_id)s 
                                '''
                    self._cr.execute(query, params)
                    line.price_unit = 0.0
                    line.taxes_id = False
                    sale_to_delete = self.env['sale.order.line'].search([('id', '=', line.sale_line_id.id)])

                    params_sale_order = {'sale_line_id': sale_to_delete.id}
                    query_sale_order = '''
                                delete
                                FROM sale_order_line
                                WHERE  id = %(sale_line_id)s 
                                '''
                    self._cr.execute(query_sale_order, params_sale_order)
                except exceptions.UserError:
                    line.sale_line_id.write({'product_uom_qty': 0.0})

    # TODO: delete me after tests
    # def action_transfer_lines_to_saleorder(self):
    #     line_to_process = self.env['purchase.order.line']
    #     for line in self:
    #         if line.qty_received > 0:
    #             line_to_process += line
    #
    #     if len(self) != len(line_to_process):
    #         raise exceptions.UserError(
    #             _(
    #                 'Some of the lines selected does not fulfill the criteria required.\n'
    #                 'Please check quantity delivered and make sure the line is not linked to sale order yet'
    #             )
    #         )
    #
    #     line_to_process.action_link_to_sale_order()
    #     return True

    @api.onchange('hm_budget')
    def onchange_budget(self):
        if self.sale_line_id:
            self.sale_line_id.purchase_price = self.hm_budget