# -*- encoding: utf-8 -*-
# ############################################################################
#
#    Copyright Mars & Moore sprl
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, api

import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True, index=True,
                                 domain="[]",
                                 help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")
    property_id = fields.Many2one("hm.property", string="Property")
    partner_onsite_id = fields.Many2one("res.partner", string="Contact sur place", domain="[('from_property', '=', False)]")
    partner_ids_domain = fields.Many2many('res.partner', compute_sudo=True, compute='_compute_partner_ids_domain',
        help="This field dynamically stores the list of partner IDs based on the selected property, including tenant, landlord, manager, and syndic."
    )

    @api.depends('property_id')
    def _compute_partner_ids_domain(self):
        for lead in self:
            partner_ids = []
            if lead.property_id:
                if lead.property_id.tenant_id:
                    partner_ids.append(lead.property_id.tenant_id.id)
                if lead.property_id.landlord_id:
                    partner_ids.append(lead.property_id.landlord_id.id)
                if lead.property_id.manager_id:
                    partner_ids.append(lead.property_id.manager_id.id)
                if lead.property_id.syndic_id:
                    partner_ids.append(lead.property_id.syndic_id.id)
            else:
                partner_ids = self.env['res.partner'].search([])
            lead.partner_ids_domain = partner_ids

    @api.onchange('property_id')
    def onchange_property_id(self):
        if self.property_id:
            fiscal_obj = self.env['account.fiscal.position']
            partner_onsite_id = False
            if self.property_id.work_billing_id:
                self.web_partner_invoice_id = self.property_id.work_billing_id.id
                self.web_partner_shipping_id = self.property_id.work_billing_id.id

            # self.web_partner_shipping_id = self.property_id.tenant_id and self.property_id.tenant_id.id or False
            if self.property_id.tenant_id:
                partner_onsite_id = self.property_id.tenant_id.id
            else:
                partner_onsite_id = self.property_id.landlord_id.id

            self.partner_onsite_id = partner_onsite_id

            if self.property_id.tenant_id == self.property_id.landlord_id == self.property_id.manager_id:
                self.partner_id = self.property_id.landlord_id and self.property_id.landlord_id.id or False
            else:
                partner_ids = []
                if self.property_id.tenant_id:
                    partner_ids.append(self.property_id.tenant_id.id)
                if self.property_id.landlord_id:
                    partner_ids.append(self.property_id.landlord_id.id)
                if self.property_id.manager_id:
                    partner_ids.append(self.property_id.manager_id.id)
                if self.property_id.syndic_id:
                    partner_ids.append(self.property_id.syndic_id.id)
                self.partner_id = partner_ids[0]

                self.partner_ids_domain = partner_ids

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.web_partner_invoice_id = self.partner_id
        else:
            self.web_partner_invoice_id = False
