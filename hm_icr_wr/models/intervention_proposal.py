# -*- encoding: utf-8 -*-

from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class TechnicianInterventionProposal(models.Model):
    _inherit = "hm.technician.intervention.proposal"

    hm_icr_id = fields.Many2one('hm.icr', related='sale_order_id.icr_id', string="ICR", related_sudo=True)
