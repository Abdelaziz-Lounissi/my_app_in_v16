# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    total_icr = fields.Integer(compute='_compute_total_icr')

    def _compute_total_icr(self):
        icr_obj = self.env['hm.icr']
        for lead in self:
            res_ids = icr_obj.search([('hm_related_lead_id', 'in', lead.ids)])
            lead.total_icr = len(res_ids.ids)

    def action_view_icr(self):
        icr_obj = self.env['hm.icr']
        action = self.env.ref('hm_icr_wr.action_icr_for_crm_lead').read()[0]
        action['context'] = {
            'default_hm_related_lead_id': self.id,
        }
        action['domain'] = [('hm_related_lead_id', '=', self.id)]
        icr_ids = icr_obj.search([('hm_related_lead_id', '=', self.id)])
        if len(icr_ids) <= 1:
            action['views'] = [(self.env.ref('hm_icr_wr.hm_icr_form_view').id, 'form')]
            action['res_id'] = icr_ids and icr_ids.id or False
        return action
