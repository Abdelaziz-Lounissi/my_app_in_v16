# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    hm_image_sales_team = fields.Binary(string="Image Sales team", copy=False, store=True, index=False)
    hm_real_works = fields.Boolean(string="Real Works", copy=False, store=True, index=False)
    hm_update_opportunity_status = fields.Boolean(string='Update opportunity status automatically', default=False,
                                                  help="Cochez cette case pour que le statut des opportunités soit automatiquement mis à jour sur base du statut des devis liés")

