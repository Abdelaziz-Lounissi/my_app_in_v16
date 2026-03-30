# -*- coding: utf-8 -*-
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
from datetime import datetime

from odoo import api, fields, models
from lxml import etree
# import simplejson
import operator as py_operator
from odoo.exceptions import ValidationError
from odoo.addons.sale.models.sale_order import READONLY_FIELD_STATES

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne,
}



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True,
        change_default=True,
        index=True,
        tracking=True,
        domain="['&', '|', ('company_id', '=', False), ('company_id', '=', company_id), '&', ('from_property', '=', False), ('id', 'in', partner_ids_domain)]"
    )

    property_id = fields.Many2one(
        'hm.property', string='Property',
        states=READONLY_FIELD_STATES,

    )
    partner_onsite_id = fields.Many2one(
        'res.partner',
        string='Partner on site',
        domain="[('from_property', '=', False)]",
    )
    manager_id = fields.Many2one(
        'res.partner',
        string='Manager',
        domain="[('from_property', '=', False)]",
    )
    origin_crm = fields.Boolean(string='origin_crm', default=False)
    parent_property_address = fields.Char(string="Parent property address", search='_for_parent_property_address', compute='_compute_parent_property_address', compute_sudo=True)
    partner_ids_domain = fields.Many2many('res.partner', compute_sudo=True, compute='_compute_partner_ids_domain',
        help="This field dynamically stores the list of partner IDs based on the selected property, including tenant, landlord, manager, and syndic."
    )

    @api.depends('property_id')
    def _compute_partner_ids_domain(self):
        for order in self:
            partner_ids = []
            if order.property_id:
                if order.property_id.tenant_id:
                    partner_ids.append(order.property_id.tenant_id.id)
                if order.property_id.landlord_id:
                    partner_ids.append(order.property_id.landlord_id.id)
                if order.property_id.manager_id:
                    partner_ids.append(order.property_id.manager_id.id)
                if order.property_id.syndic_id:
                    partner_ids.append(order.property_id.syndic_id.id)
            else:
                partner_ids = self.env['res.partner'].search([])
            order.partner_ids_domain = partner_ids

    def _for_parent_property_address(self, operator, value):
        ids = []
        for product in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](product['parent_property_address'], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def _compute_parent_property_address(self):
        for order in self:
            parent_property_address = ""
            property = order.property_id
            if property and property.parent_id:
                parent_property_address = property.parent_id.display_name
            order.parent_property_address = parent_property_address

    @api.onchange('sale_order_template_id')
    def onchange_partner_sale_order_template(self):
        # if self.sale_order_template_id.hm_forced_fiscal_position_for_model:
        #     self.fiscal_position_id = self.sale_order_template_id.hm_forced_fiscal_position_for_model

        work_category = self.sale_order_template_id.hm_work_category
        if work_category.hm_intervention_type == 'Maintenance':
            self.partner_invoice_id = (
                self.property_id.maintenance_billing_id
                and self.property_id.maintenance_billing_id.id
                or False
            )
        elif work_category.hm_intervention_type == 'Travaux':
            self.partner_invoice_id = (
                self.property_id.work_billing_id
                and self.property_id.work_billing_id.id
                or False
            )
        # self.partner_invoice_id = self.property_id.partner_id and self.property_id.partner_id.id or False

    @api.onchange('partner_shipping_id', 'partner_id')
    def onchange_partner_shipping_id(self):
        """
        Trigger the change of fiscal position when the shipping address is modified.
        """

        return {}

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """

        values = {
            'payment_term_id': self.partner_id.property_payment_term_id
            and self.partner_id.property_payment_term_id.id
            or False,
            'user_id': self.partner_id.user_id.id
            or self.partner_id.commercial_partner_id.user_id.id
            or self.env.uid,
        }
        if (
            self.env['ir.config_parameter']
            .sudo()
            .get_param('sale.use_sale_note')
            and self.env.user.company_id.sale_note
        ):
            values['note'] = self.with_context(
                lang=self.partner_id.lang
            ).env.user.company_id.sale_note

        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id

        if self.partner_id:
            values['pricelist_id'] = (
                self.partner_id.property_product_pricelist
                and self.partner_id.property_product_pricelist
                or False
            )

        self.update(values)

    @api.depends('partner_id')
    def _compute_partner_shipping_id(self):
        for order in self:
            if order.property_id:
                order.partner_shipping_id = self.property_id.partner_id.id
            else:
                order.partner_shipping_id = order.partner_id.address_get(['delivery'])['delivery'] if order.partner_id else False

    @api.onchange('property_id')
    def onchange_property_id(self):
        if self.property_id:
            self.partner_id = False
            self.onchange_partner_sale_order_template()
            if self.property_id.tenant_id:
                partner_onsite_id = self.property_id.tenant_id.id
                # partner_shipping_id = self.property_id.tenant_id.id
            else:
                partner_onsite_id = self.property_id.landlord_id.id
                # partner_shipping_id = self.property_id.partner.id

            if not self.origin_crm:
                self.partner_onsite_id = partner_onsite_id
            self.partner_shipping_id = self.property_id.partner_id.id
            self.manager_id = (
                self.property_id.manager_id
                and self.property_id.manager_id.id
                or False
            )

            if (
                self.property_id.tenant_id
                == self.property_id.landlord_id
                == self.property_id.manager_id
            ):
                self.partner_id = (
                    self.property_id.landlord_id
                    and self.property_id.landlord_id.id
                    or False
                )
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

                self.partner_ids_domain = partner_ids

        else:
            self.partner_id = False

    @api.onchange('partner_invoice_id')
    def onchange_partner_invoice(self):
        if self.partner_invoice_id and self.partner_onsite_id:
            if self.partner_invoice_id.id == self.partner_onsite_id.id:
                self.partner_id = self.partner_invoice_id
        if self.partner_invoice_id and self.property_id:
            work_category = self.sale_order_template_id.hm_work_category
            if work_category.hm_intervention_type == 'Maintenance':
                if not self.property_id.maintenance_billing_id:
                    self.property_id.write(
                        {'maintenance_billing_id': self.partner_invoice_id.id}
                    )
            elif work_category.hm_intervention_type == 'Travaux':
                if not self.property_id.work_billing_id:
                    self.property_id.write(
                        {'work_billing_id': self.partner_invoice_id.id}
                    )
            self._compute_fiscal_position_id()

    @api.depends('partner_shipping_id', 'partner_id', 'company_id', 'sale_order_template_id', 'property_id')
    def _compute_fiscal_position_id(self):
        for order in self:
            if order.property_id or order.sale_order_template_id:
                fiscal_position_id = order._compute_fiscal_position_by_property_and_order_template()
                order.fiscal_position_id = fiscal_position_id.id

                # Recalculer toutes les taxes en fonction de cette position fiscale
                order._recompute_taxes()
            else:
                # Otherwise, run the std
                super(SaleOrder, self)._compute_fiscal_position_id()


    def _compute_fiscal_position_by_property_and_order_template(self):
        fiscal_obj = self.env['account.fiscal.position']
        fiscal_position_id = False
        if self.sale_order_template_id and self.sale_order_template_id.hm_forced_fiscal_position_for_model:
            fiscal_position_id = self.sale_order_template_id.hm_forced_fiscal_position_for_model

        elif self.partner_invoice_id.vat:
            if str(self.partner_invoice_id.vat).startswith('BE'):
                fiscal_position_id = fiscal_obj.with_context(lang='fr_BE').search([('name', 'like', 'Cocontractant')],  limit=1)
            else:
                fiscal_position_id = fiscal_obj.with_context(lang='fr_BE').search([('name', 'like', 'Intra-Communautaire')], limit=1)

        elif not self.partner_invoice_id.vat:
            if self.property_id.property_type_id.is_residential and self.property_id.batiment_age >= 10 :
                fiscal_position_id = fiscal_obj.search([('name', 'like', 'de plus de 10')], limit=1)

        if not fiscal_position_id:
            fiscal_position_id = fiscal_obj.with_context(lang='fr_BE').search([('name', 'like', 'National (21%)')], limit=1)

        return fiscal_position_id


    @api.onchange('partner_onsite_id')
    def onchange_partner_onsite_id(self):
        if self.partner_invoice_id and self.partner_onsite_id:
            if self.partner_invoice_id.id == self.partner_onsite_id.id:
                self.partner_id = self.partner_invoice_id
