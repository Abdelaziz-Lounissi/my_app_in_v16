# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    hm_last_customer_review_request_on = fields.Datetime("Last customer review request")
    min_amount_to_ask_deposit = fields.Monetary(string='Montant TVAC à partir duquel exiger un acompte', tracking=True, default=400)

    prevent_auto_email = fields.Boolean(
        string="Empêcher l'envoi d'e-mail automatique",
        default=False
    )
    b2b_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='B2B Partner'
    )

    @api.onchange("b2b_partner_id")
    def onchange_b2b_partner(self):
        prevent_auto_email = False
        if self.b2b_partner_id:
            prevent_auto_email = True
        self.prevent_auto_email = prevent_auto_email
