# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TechnicianAvailability(models.Model):
    _name = "technician.availability"
    _description = "Technician Availability"
    _order = "name"

    name = fields.Char('Technician Availability Name', required=True, translate=True)
