# -*- coding: utf-8 -*-
from odoo import models


class HmProperty(models.Model):
    _name = 'hm.property'
    _inherit = ['hm.property', 'google.places.mixin']

    def _get_mapping_odoo_fields(self):
        res = super(HmProperty, self)._get_mapping_odoo_fields()
        res.update({'lat': 'property_latitude', 'lng': 'property_longitude'})
        return res
