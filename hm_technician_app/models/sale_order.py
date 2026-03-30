# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import json
import ast


class SaleOrder(models.Model):
    _inherit = "sale.order"

    hm_tech_sync_id = fields.Many2one("hm.technician.app.sync", string="Tech sync", readonly=True, copy=False)
    hm_tech_report_summary = fields.Text(string="Résumé de l'intervention", readonly=True, copy=False)
    hm_tech_report_improvement_suggestions = fields.Text(string="Suggestions d'amélioration", readonly=True, copy=False)
    hm_tech_report_arrival = fields.Datetime(string="Début de l'intervention", readonly=True, copy=False)
    hm_tech_report_departure = fields.Datetime(string="Fin de l'intervention", readonly=True, copy=False)
    hm_tech_report_intervention_status = fields.Text(string="Statut intervention technicien", readonly=True, copy=False)
    hm_tech_report_start_stop_log = fields.Text(string="Start / Stop log", readonly=True, copy=False)
    hm_tech_intervention_duration_in_s = fields.Integer(string="Heures facturables en secondes", readonly=True, copy=False)
    hm_tech_intervention_billable_h = fields.Float(string="Heures facturables", readonly=True, copy=False)
    hm_tech_report_internal_notes = fields.Text(string="Notes internes technicien", readonly=True, copy=False)
    technicien_report_picture_info_ids = fields.Many2many('hm.picture.so.info', compute='_compute_technicien_report_picture_info', compute_sudo=True, string="Tech. pictures")
    ask_qr_code = fields.Boolean(string="Demander au technicien de coller un QR code sur l'appareil", compute='_compute_ask_qr_code', compute_sudo=True)
    hm_tech_report_qr_code = fields.Char(string="Tech. report QR code", readonly=True, copy=False)

    def _compute_ask_qr_code(self):
        for sale in self:
            ask_qr_code = False
            if not sale.property_id.qr_code and sale.sale_order_template_id.ask_qr_code:
                ask_qr_code = True
            sale.ask_qr_code = ask_qr_code

    @api.depends()
    def _compute_technicien_report_picture_info(self):
        for sale in self:
            res_ids = self.env['hm.picture.so.info'].search([('hm_so_id', '=', sale.id), ('hm_picture_library_id.is_technicien_report_picture', '=', True), ('hm_picture_library_id.is_client_signature', '=', False)])
            sale.technicien_report_picture_info_ids = [(6, 0, res_ids.ids or [])]

    def write(self, vals):
        current_technician_id = self.hm_imputed_technician_id
        super(SaleOrder, self).write(vals)

        # Check if 'hm_imputed_technician_id' is in vals and has a non-False value
        if 'hm_imputed_technician_id' in vals:
            res_id = self.id
            model_name = 'sale.order'

            # Add current technician ID to the search domain if it exists
            if current_technician_id:
                # Search for the existing technician sync record
                sync_record = self.env['hm.technician.app.sync'].search([('tech_uid', '=', current_technician_id.id),
                                                                         ('res_id', '=', self.id),
                                                                         ('model_name', '=', model_name)])

                # Deactivate existing sync record if found
                if sync_record:
                    sync_record.write({'active': False})

            new_technician_id = vals['hm_imputed_technician_id']
            if new_technician_id:
                # Create a new sync record with the correct res_id (self.id)
                sync_id = self.env['hm.technician.app.sync'].create({
                    'res_id': res_id,
                    'model_name': model_name,
                    'tech_uid': new_technician_id,
                    'active': True,
                })

                # Update the sale order with the new sync ID
                if sync_id:
                    self.hm_tech_sync_id = sync_id.id

        # If context key `force_sale_order_confirm` is True and state is set to 'sale',
        # the order(s) will be confirmed automatically.
        if 'state' in vals and vals['state'] == 'sale' and self.env.context.get("force_sale_order_confirm",  False):
            for order in self.with_context(force_sale_order_confirm=False):
                order.action_confirm()

    @api.model_create_multi
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        for values in vals:
            if 'sale_order_template_id' in values and self.env.context.get('force_onchange_sale_order_template', False):
                res.onchange_property_id_params()
                res._onchange_sale_order_template_id()
                res._update_work_type_and_object_from_template()
                res.onchange_work_type_params()
                res.on_change_product_template_id()
                res.onchange_agremeent_ids_params()
                res.onchange_property_id_params()
                res._compute_tech_choice_ids()
                res.onchange_template_for_proposals()
                res.run_automated_technician_proposal_creation()

        return res