# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
import base64
from bs4 import BeautifulSoup
import base64
import requests
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HmWorkReport(models.Model):
    _name = 'hm.work.report'
    _description = "Hm Work Report"

    name = fields.Char(compute='_compute_name')
    body_text = fields.Text(string="Request", copy=True)
    hm_related_so_id = fields.Many2one('sale.order', string="SO liee", copy=True)

    picture_lib_ids = fields.Many2many('hm.picture.library', 'hm_wk_id', string="Extra Media", copy=True)
    picture_wr_info_ids = fields.One2many('hm.picture.wr.info', 'wk_id', string="Info", copy=True)

    def _compute_name(self):
        for rec in self:
            if rec.hm_related_so_id:
                rec.name = 'WR' + '/' + str(rec.hm_related_so_id.id)
            else:
                rec.name = '/'

    @api.model
    def default_get(self, fields):
        res = super(HmWorkReport, self).default_get(fields)
        if res.get('hm_related_so_id', False):
            hm_related_so_id = self.env['sale.order'].browse(res.get('hm_related_so_id'))
            picture_ids = self.env['hm.picture.library'].search([('sale_order_ids', 'in', hm_related_so_id.id), ('is_technicien_report_picture', '=', True), ('is_client_signature', '=', False)])
            if picture_ids:
                res.update({'picture_lib_ids': [(6, 0, picture_ids.ids)]})
            body_text = ""
            if hm_related_so_id.hm_tech_report_summary:
                body_text += """%s\n """ % hm_related_so_id.hm_tech_report_summary.strip()
            if hm_related_so_id.hm_tech_report_improvement_suggestions:
                body_text += """%s\n """ % hm_related_so_id.hm_tech_report_improvement_suggestions.strip()
            if len(body_text):
                res.update({'body_text': body_text})
        return res

    @api.constrains('hm_related_so_id')
    def validate_unique_work_report_for_so(self):
        for wk in self:
            if  wk.hm_related_so_id and wk.search([('hm_related_so_id', '=', wk.hm_related_so_id.id), ('id', '!=', wk.id)]):
                raise UserError(_('You cannot have two Work Reports for the same SO!'))

    @api.onchange('picture_lib_ids')
    def _onchange_picture(self):
        info_ids = []
        for picture in self.picture_lib_ids:
            if self.hm_related_so_id.id not in picture.sale_order_ids.ids:
                picture._origin.write({"sale_order_ids": [(4, self.hm_related_so_id and self.hm_related_so_id.id)]})
            picture_info = picture.mapped('library_pic_so_info_ids').filtered(
                lambda x: x.hm_so_id == self.hm_related_so_id)
            picture_id = self.picture_wr_info_ids.filtered(
                lambda x: x.hm_picture_library_id == picture_info.hm_picture_library_id)
            if not picture_id:
                info_ids.append((0, 0, {
                    'name': picture_info.name or picture.name,
                    'caption': picture_info.caption,
                    'hm_picture_library_id': picture._origin.id,
                    'hm_so_id': self.hm_related_so_id.id,
                }))

        for picture_info in self.picture_wr_info_ids:
            picture_info_ids = self.picture_lib_ids.mapped('library_pic_so_info_ids').filtered(
                lambda x: x.hm_so_id == self.hm_related_so_id)
            if picture_info.hm_picture_library_id.id not in picture_info_ids.mapped('hm_picture_library_id').ids:
                info_ids.append((3, picture_info.id))

        self.picture_wr_info_ids = info_ids

    @api.onchange('picture_wr_info_ids')
    def _onchange_picture_wr_info_ids(self):
        if self.picture_wr_info_ids:
            self.picture_lib_ids = [(6, 0, self.picture_wr_info_ids.mapped('hm_picture_library_id').ids)]

