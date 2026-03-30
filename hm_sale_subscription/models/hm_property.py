# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class HmProperty(models.Model):
    _inherit = 'hm.property'


    subscription_count = fields.Integer(string='Subscriptions', compute='_subscription_count')


    def _subscription_count(self):
        for rec in self:
            subscription_data = self.env['sale.order'].search_count([('is_subscription','=', True), ('property_id', '=', self.id)])
            rec.subscription_count=subscription_data
