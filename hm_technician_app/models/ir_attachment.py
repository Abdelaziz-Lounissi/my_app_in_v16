# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from bs4 import BeautifulSoup
import logging
import base64
import requests
_logger = logging.getLogger(__name__)


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    hm_document_type = fields.Selection([
        ('boiler_certificate', 'Boiler certificate'),
    ], string='Document type', copy=False, index=True, tracking=True)
