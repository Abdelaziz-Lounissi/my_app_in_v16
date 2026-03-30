# -*- coding: utf-8 -*-


from odoo import api, fields, models
import operator as py_operator
from odoo.exceptions import ValidationError



class ResPartner(models.Model):
    _inherit = 'res.partner'

    subscription_count = fields.Integer(string='Subscriptions', compute='_subscription_count')

    def _subscription_count(self):
        for partner in self:
            all_partners = self.with_context(active_test=False).search([('id', 'child_of', partner.ids)])
            all_partners.read(['parent_id'])

            subscription_data = self.env['sale.order'].search_count([
                ('is_subscription', '=', True),
                '|', '|',
                ('partner_id', 'in', all_partners.ids),
                ('partner_onsite_id', 'in', partner.ids),
                ('partner_invoice_id', 'in', partner.ids)
            ],
            )

            partner.subscription_count = subscription_data
