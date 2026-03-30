# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CrmLead(models.Model):
    _inherit = "crm.lead"

    # TODO: Remove after deploy
    # x_studio_description_html
    hm_html_description = fields.Html(string="Description html", copy=False, store=True, index=False,
                                      translate=False)

# class SaleOrder(models.Model):
#     _inherit = "sale.order"
#
#     hm_lead_transmis_id = fields.Many2one(string="Lead forwarded by", related='opportunity_id.hm_lead_transmis_id', store=True, precompute=True)
