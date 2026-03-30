# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
import base64
from odoo.exceptions import UserError, Warning
import logging
from PIL import Image
import io
_logger = logging.getLogger(__name__)
from odoo.tools import image_process
from odoo.tools.mimetypes import guess_mimetype
import mimetypes
import re

suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


def image_size(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


class HmPictureLibrary(models.Model):
    _name = 'hm.picture.library'
    _description = "Hm Picture Library"
    _order = 'sequence, id'

    def _get_name(self):
        name = "Image"
        for rec in self:
            rec.name = name + '/' + str(rec.id)

    # name = fields.Char("Name", default=_get_default_name, required=True)
    name = fields.Char("Name", readonly=True, compute=_get_name)
    sequence = fields.Integer(default=10, index=True)

    # original_image = fields.Binary(index=True)
    original_image = fields.Image("Image 1920", max_width=1920, max_height=1920, store=True)
    image_256 = fields.Image("Image 256", related="original_image", max_width=256, max_height=256, store=True)
    file_size_bin = fields.Integer()

    sale_order_ids = fields.Many2many('sale.order', 'so_picture_id', string="Sale order", copy=False)
    lead_ids = fields.Many2many('crm.lead', 'lead_picture_id', string="Leads", copy=False)

    library_pic_lead_info_ids = fields.One2many('hm.picture.lead.info', 'hm_picture_library_id', string="Leads Info", copy=False)
    library_pic_so_info_ids = fields.One2many('hm.picture.so.info', 'hm_picture_library_id', string="Sales Info", copy=False)
    active = fields.Boolean("Active", default=True)
    file_size = fields.Char('File size', readonly=True)
    success = fields.Boolean(compute="compute_file_flag")
    warning = fields.Boolean(compute="compute_file_flag")
    danger = fields.Boolean(compute="compute_file_flag")
    sequence = fields.Integer()
    is_technicien_report_picture = fields.Boolean(string="Rapport technicien", help="Photo envoyée par le technicien via l'application mobile")
    is_client_signature = fields.Boolean(string="Is client signature", help="Is client signature")
    is_resized = fields.Boolean()
    mime_type = fields.Char(
        string="MIME Type",
        index=True,
        help="Detected MIME type of the image"
    )
    file_extension = fields.Char(
        string="File Extension",
        index=True,
        help="Detected file extension"
    )
    external_image_url = fields.Char(string="Lien externe")
    external_image_preview_html = fields.Html(
        string="Aperçu depuis G.Drive", compute="_compute_external_image_preview_html", sanitize=False
    )

    @api.depends('external_image_url')
    def _compute_external_image_preview_html(self):
        """Generate HTML preview for external images with hover zoom."""
        for rec in self:
            if not rec.external_image_url:
                rec.external_image_preview_html = False
                continue

            url = rec.external_image_url.strip()

            # Extract Google Drive file ID
            patterns = [
                r'drive\.google\.com/file/d/([^/]+)',
                r'drive\.google\.com/open\?id=([^&]+)',
                r'drive\.google\.com/uc\?.*id=([^&]+)'
            ]
            file_id = None
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    file_id = match.group(1)
                    break

            if file_id:
                preview_url = f'https://drive.google.com/thumbnail?id={file_id}&sz=w1920'
            else:
                preview_url = url

            rec.external_image_preview_html = f'''
           
            <div class="external_image_container">
                <img src="{preview_url}" class="external_image_zoomable"
                     alt="Aperçu de l'image" loading="eager"/>
            </div>
            '''

    def get_external_image_direct_url(self):
        """Convert Google Drive share URL to direct image URL for display."""
        self.ensure_one()
        if not self.external_image_url:
            return False

        url = self.external_image_url.strip()

        # Pattern to extract file ID from Google Drive URLs
        patterns = [
            r'drive\.google\.com/file/d/([^/]+)',
            r'drive\.google\.com/open\?id=([^&]+)',
            r'drive\.google\.com/uc\?.*id=([^&]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                file_id = match.group(1)
                # Use thumbnail URL which is more reliable for previews
                return f'https://drive.google.com/thumbnail?id={file_id}&sz=w1000'


    def compute_file_flag(self):
        for rec in self:
            if rec.file_size_bin < 100000:
                rec.success = True
                rec.warning = False
                rec.danger = False
            elif rec.file_size_bin > 100000 and rec.file_size_bin < 1000000:
                rec.warning = True
                rec.success = False
                rec.danger = False
            else:
                rec.danger = True
                rec.warning = False
                rec.success = False

    def compute_file_size(self, original_image):
        file_size = ''
        file_size_bin = 0
        if original_image:
            # Decode base64 string
            binary_data = base64.b64decode(original_image)

            # Update computed file size
            file_size_bin = len(binary_data)
            file_size = image_size(len(binary_data))
        return file_size, file_size_bin

    def _check_is_heic_picture(self, original_image):
        if original_image:
            binary_data = base64.b64decode(original_image)
            file_header = binary_data[:12]
            heic_header_signature = b'ftypheic'
            is_heic = heic_header_signature in file_header
            if is_heic:
                if not self.env.context.get('skip_raise', False):
                    raise ValidationError("Format de fichier non pris en charge .heic : Veuillez charger une autre image dans un format différent.")
        return False

    def _compute_mime_and_extension_from_binary(self, binary_data):
        """Compute MIME type and file extension from binary data."""
        mimetype = guess_mimetype(binary_data) or 'application/octet-stream'
        extension = mimetypes.guess_extension(mimetype)
        if extension:
            extension = extension.lstrip('.')
        return mimetype, extension or ''

    def write(self, vals):
        if 'original_image' in vals:
            self._check_is_heic_picture(vals['original_image'])
            computed_file_size, computed_file_size_bin = self.compute_file_size(vals['original_image'])
            vals['file_size'] = computed_file_size
            vals['file_size_bin'] = computed_file_size_bin
            try:
                binary_data = base64.b64decode(vals['original_image'])
                mimetype, extension = self._compute_mime_and_extension_from_binary(binary_data)
                vals['mime_type'] = mimetype
                vals['file_extension'] = extension
            except Exception as e:
                _logger.warning(f"**** Warning computing MIME type on write for record ID {self.id}: {e}")

        return super(HmPictureLibrary, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'original_image' in vals:
                self._check_is_heic_picture(vals['original_image'])
                computed_file_size, computed_file_size_bin = self.compute_file_size(vals['original_image'])
                vals['file_size'] = computed_file_size
                vals['file_size_bin'] = computed_file_size_bin
                try:
                    binary_data = base64.b64decode(vals['original_image'])
                    mimetype, extension = self._compute_mime_and_extension_from_binary(binary_data)
                    vals['mime_type'] = mimetype
                    vals['file_extension'] = extension
                except Exception as e:
                    _logger.warning(f"**** Warning computing MIME type on create : {e}")

        return super(HmPictureLibrary, self).create(vals_list)

    @api.model
    def _reset_picture_info(self):

        so_ids = self.sale_order_ids
        lead_ids = self.lead_ids
        info_so_ids = self.library_pic_so_info_ids.mapped('hm_so_id').ids
        info_lead_ids = self.library_pic_lead_info_ids.mapped('hm_lead_id').ids

        new_lead_info_ids = []
        new_so_info_ids = []
        for x in so_ids:
            if x.id not in info_so_ids:
                name = 'SO/%s/image/%s' % (x.id, x.name)
                new_so_info_ids.append((0, 0, {'name': name, 'hm_picture_library_id': self.id, 'hm_so_id': x.id}))

        for x in lead_ids:
            if x.id not in info_lead_ids:
                name = 'Lead/%s/image/%s' % (x.id, x.name)
                new_lead_info_ids.append((0, 0, {'name': name, 'hm_picture_library_id': self.id, 'hm_lead_id': x.id}))
        if new_lead_info_ids:
            self.write({'library_pic_lead_info_ids': new_lead_info_ids})
        if new_so_info_ids:
            self.write({'library_pic_so_info_ids': new_so_info_ids})

    def attach_picture_for_lead(self):
        lead_id = self.env.context.get('lead_id')
        if lead_id :
            record_lead_id = self.env['crm.lead'].search([('id','=',lead_id)],limit=1)
            if record_lead_id :
                for rec in self :
                    rec.lead_ids = [(4, record_lead_id.id)]
                return record_lead_id.id
            else:
                return False
        else:
            return False

    def attach_so_picture(self):
        sale_id = self.env.context.get('sale_id')
        if sale_id :
            record_lead_id = self.env['sale.order'].search([('id','=',sale_id)],limit=1)
            if record_lead_id :
                for rec in self :
                    rec.sale_order_ids = [(4, record_lead_id.id)]
                return record_lead_id.id
            else:
                return False
        else:
            return False

    def resize_image_process(self, record):
        record_ids = record
        if not record_ids:
            record_ids = self.search([ ('is_resized', '=', False), ('file_size_bin', '>', 1000000), ('original_image', '!=', False)], limit=1000)
        for rec in record_ids:
            if rec.original_image:
                _logger.info('**** Start process : %s ' % rec.id)
                try:
                    original_image = base64.b64decode(rec.original_image)
                    resized_image_in_1920 =  base64.b64encode(image_process(original_image,size=(1920, 1920), verify_resolution=True,) or b'') or False
                    rec.sudo().write({'original_image': resized_image_in_1920, 'is_resized': True})
                except Exception as e:
                    _logger.error(f"Error decoding image for record {rec.id}: {str(e)}")
                    rec.sudo().write({'is_resized': True})
                    continue

    # TODO: delete after deploy prod
    def calculate_file_size(self):
        _logger.info('***** BEGIN calculate_file_size *****')

        picture_ids = self.env['hm.picture.library'].search([('file_size_bin', '=', 0)], limit=500)
        _logger.info('Total records to process: %s', len(picture_ids))

        for pic in picture_ids:
            _logger.info('Processing picture ID: %s', pic.id)

            if not pic.with_context(skip_raise=True)._check_is_heic_picture(pic.original_image):
                computed_file_size, computed_file_size_bin = pic.compute_file_size(pic.original_image)

                _logger.info('Old file_size : %s ' % pic.file_size)
                _logger.info('Old file_size_bin : %s ' % pic.file_size_bin)

                pic.write({
                    'file_size': computed_file_size,
                    'file_size_bin': computed_file_size_bin
                })

                _logger.info('Updated file_size : %s ' % pic.file_size)
                _logger.info('Updated file_size_bin : %s ' % pic.file_size_bin)

    def batch_update_mime_and_extension(self, batch_size):
        """Update mime_type and file_extension for a batch of images that are missing them."""
        records = self.search([
            ('original_image', '!=', False),
            '|', ('mime_type', '=', False), ('file_extension', '=', False)
        ], limit=batch_size)

        processed_count = 0
        _logger.info(f"Batch MIME/Extension. Records to process: {len(records)}")

        for rec in records:
            try:
                binary_data = base64.b64decode(rec.original_image)
                mimetype, extension = self._compute_mime_and_extension_from_binary(binary_data)
                rec.write({
                    'mime_type': mimetype,
                    'file_extension': extension
                })
                processed_count += 1
            except Exception as e:
                _logger.error(f"Error updating record {rec.id}: {e}")

        _logger.info(f"Batch MIME/Extension update finished. Records processed: {processed_count}")
        return processed_count