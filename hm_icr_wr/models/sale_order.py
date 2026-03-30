# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # so_gallery_id = fields.Many2one('hm.picture.library', string="Gallery")
    total_wr = fields.Integer(compute='_compute_total_wr')
    icr_id = fields.Many2one("hm.icr", "ICR")
    wr_id = fields.Many2one('hm.work.report', compute='_get_w_report', string="Work report")

    def _get_w_report(self):
        wr_obj = self.env['hm.work.report']
        for order in self:
            wr_id = wr_obj.search([('hm_related_so_id', '=', order.id)], limit=1)
            order.wr_id = wr_id and wr_id.id or False

    def _compute_total_wr(self):
        wr_obj = self.env['hm.work.report']
        for order in self:
            res_ids = wr_obj.search([('hm_related_so_id', '=', order.id)])
            order.total_wr = len(res_ids.ids)

    def action_wr_for_sale_order(self):
        wk_ids = []
        wk_ids = self.env['hm.work.report'].search([('hm_related_so_id', '=', self.id)])
        if len(wk_ids) > 1:
            views = [(self.env.ref('hm_icr_wr.hm_wr_tree_view').id, 'tree'),
                     (self.env.ref('hm_icr_wr.hm_wr_form_view').id, 'form')]
            return {
                'name': 'Work Report',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'hm.work.report',
                'views': views,
                'domain': [('id', 'in', wk_ids.ids)],
                'type': 'ir.actions.act_window',
                'context': {'default_hm_related_so_id': self.id},
            }

        else:
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hm.work.report',
                'res_id': wk_ids.id or False,
                'type': 'ir.actions.act_window',
                'target': 'popup',
                'context': {'default_hm_related_so_id': self.id},

            }
