# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Override the 'total_invoiced' field to include the group 'hm_group_invoicing_readonly',
    # allowing users in this group to view the total invoiced in the form view.
    total_invoiced = fields.Monetary(compute='_invoice_total', string="Total Invoiced",
        groups='account.group_account_invoice,account.group_account_readonly,hm_account.hm_group_invoicing_readonly')