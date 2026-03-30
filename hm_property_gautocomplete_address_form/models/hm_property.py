# -*- coding: utf-8 -*-
from odoo import api, models


class HmProperty(models.Model):
    _inherit = 'hm.property'

    @api.onchange('street', 'zip', 'city', 'state_id', 'country_id')
    def _delete_coordinates(self):
        """An overwrite method to prevent the deletion of the coordinates"""
        pass
