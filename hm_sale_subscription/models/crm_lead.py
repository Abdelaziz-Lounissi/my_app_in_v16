# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = "crm.lead"

    subscription_count = fields.Integer(string='Subscriptions', compute='_subscription_count')


    def _subscription_count(self):
        for rec in self:
            subscription_data = 0
            if self.property_id:
                subscription_data = self.env['sale.order'].search_count([('is_subscription','=', True), ('property_id', '=', self.property_id.id)])
            rec.subscription_count=subscription_data


    def action_crm_sale_subscription(self):
        action = self.env.ref('sale_subscription.sale_subscription_action').read()[0]
        if self.property_id:
            action['context'] = {
                'default_property_id': self.property_id.id,
            }
        action['domain'] = [('is_subscription','=', True), ('property_id','=', self.property_id.id)]
        res_id = self.env['sale.order'].search([('is_subscription','=', True), ('property_id', '=', self.property_id.id)])
        if len(res_id) == 1:
            action['res_id'] = res_id and res_id.id or False
        return action
