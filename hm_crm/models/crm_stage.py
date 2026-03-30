# -*- coding: utf-8 -*-
# Merge module crm_module

from odoo import api, fields, models


class CrmStage(models.Model):
    _inherit = "crm.stage"

    authorize_reminder_action = fields.Boolean("Authorize Reminder", default=False)
