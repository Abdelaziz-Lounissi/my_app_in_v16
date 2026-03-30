# -*- coding: utf-8 -*-
import pytz
from odoo import api, fields, models, _
from datetime import datetime
from datetime import date
from datetime import timedelta

from odoo.http import request


class hm_property_popup(models.TransientModel):
    _name = "hm.property.popup"
    _description = "Hm property popup"

    property_id = fields.Integer(string="Property", readonly=True)
    tanent = fields.Many2one('res.partner', string="zzz")
    landlord = fields.Many2one('res.partner', string="Properdddty")
    tanent_address = fields.Boolean(string="Adresse du Locataire", default=True)
    landlord_address = fields.Boolean(string="Adresse du Propriétaire", default=True)

    def action_change_address(self):

        property = self.env['hm.property'].search([('id','=',self.property_id)])
        address = []
        if property:
            address = {
                    'street': property.street,
                    'street2': property.street2 or False,
                    'city': property.city,
                    'state_id': property.state_id.id or False,
                    'zip': property.zip,
                    'country_id': property.country_id.id or False,
                }


            if self.tanent_address:
                property.tenant_id.write(address)
            if self.landlord_address:
                property.landlord_id.write(address)
            address['name'] = property.name
            property.partner_id.write(address)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'}
