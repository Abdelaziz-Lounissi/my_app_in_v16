# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class HmPictureIcrInfo(models.Model):
    _name = 'hm.picture.icr.info'
    _description = "Hm Picture ICR Info"

    name = fields.Char("Name")
    caption = fields.Text("Caption")
    hm_picture_library_id = fields.Many2one('hm.picture.library', string="Picture")
    hm_lead_id = fields.Many2one('crm.lead', string="Lead")
    icr_id = fields.Many2one('hm.icr', string="ICR")

    image_256 = fields.Image(related="hm_picture_library_id.image_256", attachment=False, max_width=256, max_height=256, store=False, related_sudo=True)
    image_1920 = fields.Image(related="hm_picture_library_id.original_image", attachment=False, max_width=1920, max_height=1920, store=False, related_sudo=True)
    image_1024 = fields.Image("Image 1024", attachment=False, related="image_1920", max_width=1024, max_height=1024, store=False, related_sudo=True)

    sequence = fields.Integer('Sequence', default=1, help="Used to order picture")
    external_image_url = fields.Char(related="hm_picture_library_id.external_image_url", string="Lien externe", readonly=True)
    external_image_preview_html = fields.Html(related="hm_picture_library_id.external_image_preview_html", string="Aperçu depuis G.Drive", readonly=True)

class HmPictureWrInfo(models.Model):
    _name = 'hm.picture.wr.info'
    _description = "Hm Picture Work Report Info"

    name = fields.Char("Name")
    caption = fields.Text("Caption")
    hm_picture_library_id = fields.Many2one('hm.picture.library', string="Picture")
    hm_so_id = fields.Many2one('sale.order', string="Lead")
    wk_id = fields.Many2one('hm.work.report', string="Work Report")

    image_256 = fields.Image(related="hm_picture_library_id.image_256", attachment=False, max_width=256, max_height=256, store=False, related_sudo=True)
    image_1920 = fields.Image(related="hm_picture_library_id.original_image", attachment=False, max_width=1920, max_height=1920, store=False, related_sudo=True)
    image_1024 = fields.Image("Image 1024", attachment=False, related="image_1920", max_width=1024, max_height=1024, store=False, related_sudo=True)

    sequence = fields.Integer('Sequence', default=1, help="Used to order picture")
    external_image_url = fields.Char(related="hm_picture_library_id.external_image_url", string="Lien externe", readonly=True)
    external_image_preview_html = fields.Html(related="hm_picture_library_id.external_image_preview_html", string="Aperçu depuis G.Drive", readonly=True)
