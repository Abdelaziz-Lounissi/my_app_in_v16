# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
import re
import requests
import datetime
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import base64

_logger = logging.getLogger(__name__)


class HmDevice(models.Model):
    _name = "hm.device"
    _description = "Devices"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    state = fields.Selection([('to_install', 'To install'), ('installed', 'Installed'), ('uninstalled', 'Uninstalled')])

    # Général
    name = fields.Char("Name", compute="compute_device_name")
    property_id = fields.Many2one("hm.property", required=True, string="Real Estate")
    for_rent = fields.Boolean(related="property_id.for_rent", string='For Rent?')
    landlord_id = fields.Many2one(related="property_id.landlord_id", string='Landlord')
    tenant_id = fields.Many2one(related="property_id.tenant_id", string='Tenant')

    product_tmpl_id = fields.Many2one("product.template", required=True, string="Product")
    hm_brand = fields.Char(related="product_tmpl_id.hm_brand", string="Manufacturer")
    device_type_id = fields.Many2one(related="product_tmpl_id.categ_id", string="Device Type")

    # Détails de l'installation
    installed_by_heat_me = fields.Selection(
        selection=[('yes', 'Yes'), ('no', 'No')],
        string="Installed by Heat Me",
    )
    qr_code = fields.Char(string="Heat Me QR Code")

    installation_date = fields.Date(string="Installation Date")
    serial_number = fields.Char(string="Device Serial Number")
    device_model_id = fields.Many2one("hm.device.model", string="Device model")
    construction_date = fields.Date(string="Device Construction Date")

    # Garantie
    warranty_duration_in_month = fields.Integer(string="Warranty duration in month", default=0)
    warranty_start_date = fields.Date(string="Warranty start date")
    warranty_end_date = fields.Date(string="Warranty end date", compute="_compute_warranty_end_date", store=True)
    registration_date = fields.Date(string="Date of registration with the manufacturer")
    is_under_warranty = fields.Boolean(compute='_compute_is_under_warranty', store=True)

    # Interventions
    registration_reference = fields.Char(string="Manufacturer Registration Reference")
    last_intervention_date = fields.Date(string="Last Intervention Date", compute="_compute_last_intervention_date")
    next_intervention_date = fields.Date(string="Next Intervention Date", compute="_compute_next_intervention_date")

    # technical
    executed = fields.Boolean('Executed', default=False)
    sale_order_ids = fields.Many2many('sale.order', compute="_compute_sale_order_ids", string="Sales Info")
    sale_order_id = fields.Many2one('sale.order', string="Sale order")

    @api.depends("warranty_start_date", "warranty_duration_in_month")
    def _compute_is_under_warranty(self):
        today = fields.Date.today()
        for record in self:
            if record.warranty_start_date and record.warranty_end_date:
                record.is_under_warranty = (
                        record.warranty_start_date <= today <= record.warranty_end_date
                )
            else:
                record.is_under_warranty = False

    @api.depends("property_id", "device_model_id")
    def compute_device_name(self):
        for rec in self:
            rec.name = f"{rec.property_id.id}-{rec.device_model_id.name}" if rec.property_id and rec.device_model_id else ""

    def _compute_sale_order_ids(self):
        select_sale_order_obj = self.env['hm.so.device.select']
        for rec in self:
            selected_sale_order_ids = select_sale_order_obj.search(
                [('property_id', '=', rec.property_id.id), ('is_selected', '=', True), ('device_id', '=', rec.id)])
            sale_order_ids = selected_sale_order_ids.mapped("sale_order_id")
            rec.sale_order_ids = [(6, 0, sale_order_ids.ids)]

    @api.depends("warranty_start_date", "warranty_duration_in_month")
    def _compute_warranty_end_date(self):
        for rec in self:
            if rec.warranty_start_date:
                rec.warranty_end_date = rec.warranty_start_date + relativedelta(months=rec.warranty_duration_in_month)
            else:
                rec.warranty_end_date = False

    def _compute_last_intervention_date(self):
        sale_obj = self.env["sale.order"]
        select_sale_order_obj = self.env['hm.so.device.select']
        today = datetime.datetime.now().date()
        for rec in self:
            selected_sale_order_ids = select_sale_order_obj.search(
                [('property_id', '=', rec.property_id.id), ('is_selected', '=', True), ('device_id', '=', rec.id)])
            sale_order_ids = selected_sale_order_ids.mapped("sale_order_id")
            order_id = sale_obj.search([('commitment_date', '<', today), ('id', 'in', sale_order_ids.ids)],
                                       order='commitment_date DESC', limit=1)
            rec.last_intervention_date = order_id.commitment_date

    def _compute_next_intervention_date(self):
        sale_obj = self.env["sale.order"]
        select_sale_order_obj = self.env['hm.so.device.select']
        today = datetime.datetime.now().date()
        for rec in self:
            selected_sale_order_ids = select_sale_order_obj.search(
                [('property_id', '=', rec.property_id.id), ('is_selected', '=', True), ('device_id', '=', rec.id)])
            sale_order_ids = selected_sale_order_ids.mapped("sale_order_id")
            order_id = sale_obj.search([('commitment_date', '>=', today), ('id', 'in', sale_order_ids.ids)],
                                       order='commitment_date ASC', limit=1)
            rec.next_intervention_date = order_id.commitment_date

    @api.onchange("installed_by_heat_me")
    def _onchange_installed_by_heat_me(self):
        if self.installed_by_heat_me == "yes":
            self.warranty_duration_in_month = 24

    def _migrate_field_hm_boiler_nameplate_2_attachments(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        rec_ids = self.search([('property_id', '!=', False), ('executed', '=', False),], limit=200)

        for record in rec_ids:
            record.executed = True
            if not record.property_id.hm_boiler_nameplate:
                continue

            soup = BeautifulSoup(record.property_id.hm_boiler_nameplate, 'html.parser')
            attachments = []
            text_content = soup.get_text(separator="\n").strip()

            html_content = str(soup)
            img_pattern = re.compile(r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>')
            image_matches = img_pattern.findall(html_content)

            images_data = []

            if image_matches:
                _logger.info(f"Found {len(image_matches)} images in the HTML content for record {record.id}")

                for img_src in image_matches:
                    img_binary = None
                    img_filename = None

                    if img_src.startswith('data:image/'):  # Gestion des images en base64
                        img_type_match = re.match(r'data:image/(.*?);base64,(.*)', img_src)
                        if img_type_match:
                            img_type, img_data = img_type_match.groups()
                            img_binary = base64.b64decode(img_data)
                            img_filename = f"image_{image_matches.index(img_src) + 1}.{img_type}"
                    else:
                        full_img_url = img_src if img_src.startswith('http') else f'{base_url}{img_src}'
                        try:
                            response = requests.get(full_img_url, timeout=5)
                            if response.status_code == 200:
                                img_binary = response.content
                                img_filename = img_src.split('/')[-1].split('?')[0] or f"image_{image_matches.index(img_src) + 1}.jpg"
                        except requests.RequestException as e:
                            _logger.error(f"Failed to download image {full_img_url}: {e}")

                    if img_binary and img_filename:
                        images_data.append((img_binary, img_filename))

            counter = 1
            for img_binary, img_filename in images_data:
                attachment = self.env['ir.attachment'].create({
                    'name': "plaquette_signalétique_%s" % (counter),
                    'type': 'binary',
                    'datas': base64.b64encode(img_binary),
                    'res_model': self._name,
                    'res_id': record.id,
                    'hm_document_type': 'device_nameplate'
                })
                attachments.append(attachment.id)
                counter += 1

            if text_content:
                record.message_post(
                    body=text_content,
                )


class HmDeviceModel(models.Model):
    _name = "hm.device.model"
    _description = "Devices Model"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(compute='_compute_name')
    product_tmpl_id = fields.Many2one("product.template", required=True, string="Product")
    model_name = fields.Char(string="Model")

    @api.depends('model_name')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.model_name

    @api.constrains('product_tmpl_id', 'model_name')
    def _check_product_model_unique(self):
        for record in self:
            if record.product_tmpl_id and record.model_name:
                domain = [
                    ('product_tmpl_id', '=', record.product_tmpl_id.id),
                    ('model_name', '=', record.model_name),
                    ('id', '!=', record.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError('Le couple Produit-Modèle doit être unique!')

    @api.model
    def name_create(self, name):
        new_record = self.create({"model_name": name})
        return new_record.name_get()[0]

    @api.model
    def default_get(self, fields):
        res = super(HmDeviceModel, self).default_get(fields)
        if self.env.context.get('default_name'):
            res['model_name'] = self.env.context["default_name"]
        return res


class MmSoSelectDevice(models.Model):
    _name = "hm.so.device.select"
    _description = "Selected devices"

    name = fields.Char(compute='_compute_name', string="Name")
    sale_order_id = fields.Many2one('sale.order', string="Sale order")
    device_id = fields.Many2one('hm.device', string="Device")
    property_id = fields.Many2one("hm.property", required=True, string="Real Estate")
    device_model_id = fields.Many2one(related="device_id.device_model_id", string="Device model")
    product_tmpl_id = fields.Many2one(related="device_id.product_tmpl_id")
    state = fields.Selection(related="device_id.state", )
    is_selected = fields.Boolean('Is selected?', default=False)

    @api.depends('device_id', 'sale_order_id')
    def _compute_name(self):
        for rec in self:
            rec.name = str(rec.sale_order_id.name) + str(rec.device_id.name)
