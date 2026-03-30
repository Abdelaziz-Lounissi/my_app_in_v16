# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import logging

_logger = logging.getLogger(__name__)


class HmProperty(models.Model):
    _inherit = 'hm.property'

    device_count = fields.Integer(compute='_compute_device_count', string='Device Count')
    executed = fields.Boolean('Executed', default=False)
    warranty_display = fields.Char(compute='_compute_warranty_display', precompute=False)


    def _compute_warranty_display(self):
        device_obj = self.env['hm.device']
        for record in self:
            warranty_display = ""
            device_counter = device_obj.search_count([("property_id", '=', record.id), ("is_under_warranty", '=', True)])
            if device_counter:
                if device_counter == 1 :
                    warranty_display = f"{device_counter} GARANTIE"
                else:
                    warranty_display = f"{device_counter} GARANTIES"

            record.warranty_display = warranty_display

    def _compute_device_count(self):
        device_obj = self.env['hm.device']
        for record in self:
            device_count = device_obj.search_count([('property_id', '=', record.id)])
            record.device_count = device_count

    # TODO: One time action
    def _set_device_for_properties(self):
        rec_ids = self.search([('executed', '=', False)], limit=200)
        device_obj = self.env['hm.device']
        _logger.info(f"*** Processing {len(rec_ids.ids)} properties.")
        product_tmpl_id = 301984
        for rec in rec_ids:
            html_content = rec.hm_boiler_nameplate
            rec.executed = True
            if not html_content or html_content.strip() == "<p><br></p>":
                _logger.info(
                    f"Skipping record {rec.id} ('{rec.name}') because the HTML field is empty or contains only <p><br></p>")
                continue

            _logger.info(f"*** Process property {rec.id}.")
            partner_id = rec.landlord_id.id or rec.work_billing_id.id or rec.manager_id.id
            if not device_obj.search([("property_id", '=', rec.id)]) and partner_id:

                device_id = device_obj.create({"property_id": rec.id,
                                               "product_tmpl_id": product_tmpl_id,
                                               })
                _logger.info(f"*** Create new device :{device_id.id}.")
                _logger.info(f"*** Create new product template : {product_tmpl_id}.")
