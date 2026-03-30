# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    hm_is_real_picture = fields.Boolean('Real picture?', default=False, help="A real picture?")
