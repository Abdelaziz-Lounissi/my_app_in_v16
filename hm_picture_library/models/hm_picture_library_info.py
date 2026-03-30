# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
import base64


class HmPictureLeadInfo(models.Model):
    _name = 'hm.picture.lead.info'
    _description = "Hm Picture Lead Info"

    name = fields.Char("Name", required=True)
    caption = fields.Char("Caption")
    hm_picture_library_id = fields.Many2one('hm.picture.library', string="Picture")
    hm_lead_id = fields.Many2one('crm.lead', string="Lead")
    image_256 = fields.Image(related="hm_picture_library_id.image_256", attachment=False, max_width=256, max_height=256, store=False)
    image_1920 = fields.Image(related="hm_picture_library_id.original_image", attachment=False, max_width=1920, max_height=1920, store=False)
    external_image_url = fields.Char(related="hm_picture_library_id.external_image_url", string="Lien externe", readonly=True)
    external_image_preview_html = fields.Html(related="hm_picture_library_id.external_image_preview_html", string="Aperçu depuis G.Drive", readonly=True)


class HmPictureSoInfo(models.Model):
    _name = 'hm.picture.so.info'
    _description = "Hm Picture So Info"

    name = fields.Char("Name", required=True)
    caption = fields.Char("Caption")
    hm_picture_library_id = fields.Many2one('hm.picture.library', string="Picture")
    hm_so_id = fields.Many2one('sale.order', string="SO")
    image_256 = fields.Image(related="hm_picture_library_id.image_256", attachment=False, max_width=256, max_height=256, store=False)
    image_1920 = fields.Image(related="hm_picture_library_id.original_image", attachment=False, max_width=1920, max_height=1920, store=False)
    external_image_url = fields.Char(related="hm_picture_library_id.external_image_url", string="Lien externe", readonly=True)
    external_image_preview_html = fields.Html(related="hm_picture_library_id.external_image_preview_html", string="Aperçu depuis G.Drive", readonly=True)
