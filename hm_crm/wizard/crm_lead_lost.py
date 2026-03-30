# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    def action_lost_reason_apply(self):
        super(CrmLeadLost, self).action_lost_reason_apply()
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        leads.write({'probability': 0, 'active': False})
        return leads
