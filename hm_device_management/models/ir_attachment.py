# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    hm_document_type = fields.Selection(
        selection_add=[
            ('device_nameplate', _('Device nameplate')),
        ]
    )
