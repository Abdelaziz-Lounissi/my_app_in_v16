# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import json
import ast

class TechnicianAppSync(models.Model):
    _name = "hm.technician.app.sync"
    _description = "Technician app sync"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", compute='_compute_name')
    res_id = fields.Integer("Ressource ID")
    model_name = fields.Char("Model", required=True)
    request_value = fields.Text("Request", tracking=True)
    tech_uid = fields.Integer("Technician ID", required=True)
    active = fields.Boolean(default=True, tracking=True)

    state = fields.Selection([
        ('new', 'New'),
        ('to_sync', 'To sync'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ], string='State', copy=False, index=True, tracking=True, default='new')

    def _compute_name(self):
        for rec in self:
            try:
                rec.name = self.env[rec.model_name].browse(int(rec.res_id)).display_name
            except Exception as e:
                rec.name = '/'

    def get_datas(self, request_value):
        datas = {}
        res = ast.literal_eval(request_value)
        return res


    @api.model
    def sync_technician_app(self):
        if self.model_name == 'sale.order':
            so_obj = self.env['sale.order']
            if self.res_id and self.tech_uid and self.request_value:
                try:
                    so_id = so_obj.search([('id', '=', self.res_id), ('hm_imputed_technician_id', '=', self.tech_uid)])
                    if so_id:
                        datas = self.get_datas(self.request_value)
                        tech_uid = self.env.ref('hm_technician_app.technician_user')

                        # Calculer la durée de l'intervention en heures décimales
                        if datas.get('hm_tech_intervention_duration_in_s', False):
                            hm_tech_intervention_duration = datas['hm_tech_intervention_duration_in_s']
                            decimal_hours = hm_tech_intervention_duration / 3600.0
                            duration_in_decimal = round(decimal_hours, 2)
                            datas.update({'hm_tech_intervention_billable_h': duration_in_decimal})

                        if datas.get('hm_tech_report_qr_code', False) and so_id.property_id and not so_id.property_id.qr_code:
                            so_id.with_env(self.env(user=tech_uid)).property_id.write({'qr_code': datas['hm_tech_report_qr_code']})

                        so_id.with_env(self.env(user=tech_uid)).write(datas)
                        self.state = 'synced'
                        return True
                    else:
                        self.state = 'failed'
                except Exception as error_message:
                    self.state = 'failed'
                    self.message_post(
                        body=f"""<div class="o_thread_message_content">
                                <span>Erreur: {error_message}</span>
                            </div>"""
                    )
        else:
            return False
