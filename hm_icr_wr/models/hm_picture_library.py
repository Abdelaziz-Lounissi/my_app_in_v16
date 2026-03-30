# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import requests
import base64


class HmPictureLibrary(models.Model):
    _inherit = 'hm.picture.library'

    hm_icr_id = fields.Many2one('hm.icr', string="Template")
    hm_wk_id = fields.Many2one('hm.work.report', string="Template")

    library_pic_wk_info_ids = fields.Many2many('hm.picture.wr.info', compute='_compute_wk_picture_info', string="Work report")
    library_pic_icr_info_ids = fields.Many2many('hm.picture.icr.info', compute='_compute_icr_picture_info',  string="Icr")

    def _compute_wk_picture_info(self):
        for picture in self:
            res_ids = self.env['hm.picture.wr.info'].search([('hm_picture_library_id', '=', picture.id)])
            picture.library_pic_wk_info_ids = [(6, 0, res_ids.ids or [])]

    def _compute_icr_picture_info(self):
        for picture in self:
            res_ids = self.env['hm.picture.icr.info'].search([('hm_picture_library_id', '=', picture.id)])
            picture.library_pic_icr_info_ids = [(6, 0, res_ids.ids or [])]

    def unlink(self):
        for picture in self:
            wr_res_ids = self.env['hm.picture.wr.info'].search([('hm_picture_library_id', '=', picture.id)])
            wr_res_ids.unlink()
            icr_res_ids = self.env['hm.picture.icr.info'].search([('hm_picture_library_id', '=', picture.id)])
            icr_res_ids.unlink()
        return super(HmPictureLibrary, self).unlink()

    def get_external_image_base64(self):
        """Return the external image as base64 for PDF display"""
        self.ensure_one()
        if not self.external_image_url:
            return False
        url = self.get_external_image_direct_url()
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
        except Exception:
            return False
        return False
