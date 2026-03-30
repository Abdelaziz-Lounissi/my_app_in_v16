# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    so_picture_id = fields.Many2one('hm.picture.library', string="Picture library")
    total_pictures = fields.Integer(compute='_compute_total_pictures')
    selected_picture_info_ids = fields.One2many('hm.picture.so.info', compute='_compute_selected_picture_info', inverse='_inverse_selected_picture_info', string="Info")

    def _compute_selected_picture_info(self):
        pic_info_obj = self.env['hm.picture.so.info']
        for so in self:
            res_ids = pic_info_obj.search([('hm_so_id', '=', so.id), ('hm_picture_library_id.is_client_signature', '=', False)])
            so.selected_picture_info_ids = [(6, 0, res_ids.ids or [])]

    @api.depends('selected_picture_info_ids')
    def _inverse_selected_picture_info(self):
        pic_info_obj = self.env['hm.picture.so.info']
        for so in self:
            for res in so.selected_picture_info_ids:
                res_id = pic_info_obj.search([('id', '=', res.id), ('hm_picture_library_id.is_client_signature', '=', False)])
                res_id.caption = res.caption

    def _compute_total_pictures(self):
        for order in self:
            res_ids = self.env['hm.picture.library'].search([('sale_order_ids', 'in', order.id), ('is_client_signature', '=', False)])
            order.total_pictures = len(res_ids.ids)

    @api.model_create_multi
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        opportunity_id =False
        for val in vals:
            opportunity_id = val.get('opportunity_id', False)
        if not self.env.context.get('default_icr_id', False) and opportunity_id:
            icr_id = self.env['hm.icr'].search([('hm_related_lead_id', '=', opportunity_id)], limit=1)
            res.icr_id = icr_id and icr_id.id or False
        return res
