# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    lead_picture_id = fields.Many2one('hm.picture.library', string="Picture library")
    total_pictures = fields.Integer(compute='_compute_total_pictures')
    selected_picture_info_ids = fields.One2many('hm.picture.lead.info', compute='_compute_selected_picture_info', inverse='_inverse_selected_picture_info', string="Info")

    def _compute_selected_picture_info(self):
        for lead in self:
            res_ids = self.env['hm.picture.lead.info'].search([('hm_lead_id', '=', lead.id)])
            lead.selected_picture_info_ids = [(6, 0, res_ids.ids or [])]

    @api.depends('selected_picture_info_ids')
    def _inverse_selected_picture_info(self):
        for lead in self:
            for res in lead.selected_picture_info_ids:
                res_id = self.env['hm.picture.lead.info'].search([('id', '=', res.id)])
                res_id.caption = res.caption

    def _compute_total_pictures(self):
        for lead in self:
            res_ids = self.env['hm.picture.library'].search([('lead_ids', 'in', lead.ids)])
            lead.total_pictures = len(res_ids.ids)
