# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ask_device_nameplate = fields.Boolean(
        related="sale_order_template_id.ask_device_nameplate",
        string="Demander au technicien de prendre une photo de la plaquette signalétique"
    )
    hm_device_sale_order_id = fields.Many2one('hm.device', string="Device")
    selected_device_ids = fields.One2many('hm.so.device.select', 'sale_order_id', compute='_compute_property_for_devices', string='Devices')
    warranty_display = fields.Char(compute='_compute_warranty_display', precompute=False)
    has_selected_devices = fields.Boolean(
        compute='_compute_has_selected_devices',
        store=True,
        index=True,
    )

    @api.depends('selected_device_ids')
    def _compute_has_selected_devices(self):
        for rec in self:
            rec.has_selected_devices = bool(rec.selected_device_ids)

    @api.depends("hm_device_sale_order_id.warranty_start_date", "hm_device_sale_order_id.warranty_end_date", "property_id")
    def _compute_warranty_display(self):
        device_obj = self.env['hm.device']
        for record in self:
            warranty_display = ""
            if record.property_id:
                device_counter = device_obj.search_count([("property_id", '=', record.property_id.id), ("is_under_warranty", '=', True)])
                if device_counter:
                    if device_counter == 1 :
                        warranty_display = f"{device_counter} GARANTIE"
                    else:
                        warranty_display = f"{device_counter} GARANTIES"

            record.warranty_display = warranty_display

    @api.depends("property_id")
    def _compute_property_for_devices(self):
        device_obj = self.env['hm.device']
        select_device_obj = self.env['hm.so.device.select']
        for rec in self:
            if not rec.property_id:
                rec.selected_device_ids = [(5, 0, 0)]
                continue
            devices =device_obj.search([('property_id', '=', rec.property_id.id)])
            select_devices = []
            for device in devices:
                select_device_id = select_device_obj.search([('sale_order_id', '=', rec.id), ('property_id', '=', rec.property_id.id), ('device_id', '=', device.id)], limit=1)
                if not select_device_id:
                    select_device_id = select_device_obj.create({
                        'sale_order_id': rec.id,
                        'property_id': rec.property_id.id,
                        'device_id': device.id
                    })
                select_devices.append(select_device_id.id)
            rec.selected_device_ids = [(6, 0, select_devices)]
