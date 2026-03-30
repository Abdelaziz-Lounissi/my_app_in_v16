# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from bs4 import BeautifulSoup
import logging
import base64
import requests
_logger = logging.getLogger(__name__)


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    migration_done = fields.Boolean(default=False)
