# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _, SUPERUSER_ID
from math import ceil
from odoo.exceptions import UserError


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    ask_device_nameplate = fields.Boolean(string="Demander au technicien de prendre une photo de la plaquette signalétique", default=False)
