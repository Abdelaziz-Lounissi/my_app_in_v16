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
import logging
import operator as py_operator
import re
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.base.models.res_partner import ADDRESS_FIELDS
from dateutil.relativedelta import relativedelta

STREET_FIELDS = ['street_name', 'street_number', 'street_number2']

from lxml import etree
import logging
_logger = logging.getLogger(__name__)

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne,
}


class HmProperty(models.Model):
    _name = 'hm.property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property'
    _parent_store = True
    _rec_name = 'display_name'


    def get_default_landlord(self):
        if not self.env.user.has_group('realty_property.group_multi_landlord'):
            return self.env.user.company_id.partner_id

    partner_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True)
    active = fields.Boolean(default=True)
    name = fields.Char(
        string='Property Name',
        compute='_compute_display_name',
        default='New',
        readonly=True,
        required=True,
        compute_sudo=True,
        tracking=True
    )
    parent_id = fields.Many2one('hm.property', 'Parent Property', ondelete='restrict')
    manager_id = fields.Many2one('res.partner', string='Manager', tracking=True)
    landlord_id = fields.Many2one('res.partner', 'Landlord', tracking=True)
    acp_id = fields.Many2one('res.partner', 'Landlord ACP', default=get_default_landlord)
    parent_path = fields.Char(index=True, unaccent=False)
    main_property_id = fields.Many2one(
        'hm.property',
        'Main Parent Property',
        index=True,
        compute='_get_main_property',
        store=True,
    )

    display_name = fields.Char('Complete Name', compute='_compute_display_name', store=True, tracking=True, compute_sudo=True)
    street_name = fields.Char(
        'Street Name',
        compute='_split_street',
        inverse='_set_street',
        store=True,
        tracking=True
    )
    street_number = fields.Char(
        'House',
        compute='_split_street',
        help='House Number',
        inverse='_set_street',
        store=True,
        tracking=True
    )
    street_number2 = fields.Char(
        'Door',
        compute='_split_street',
        help='Door Number',
        inverse='_set_street',
        store=True,
        tracking=True
    )
    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)
    zip = fields.Char(change_default=True, tracking=True)
    city = fields.Char(tracking=True)
    state_id = fields.Many2one('res.country.state', string='State', ondelete='restrict', required=True, tracking=True)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', tracking=True)
    property_type_id = fields.Many2one('hm.property.type', string='Type', ondelete='restrict')
    surface = fields.Float('Surface')
    child_ids = fields.One2many('hm.property', 'parent_id', 'Child Properties')
    child_count = fields.Integer('Nbr Lots', compute='_child_count')
    state = fields.Selection(
        [
            ('project', 'New'),
            ('open', 'Started'),
            ('closed', 'Closed'),
            ('sold', 'Sold'),
        ],
        'Status',
    )
    build_date = fields.Integer('Construction Date')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        index=True,
        default=lambda self: self.env.user.company_id.id,
    )
    company_currency = fields.Many2one(
        string='Currency',
        related='company_id.currency_id',
        readonly=True, related_sudo=True,
    )
    doc_count = fields.Integer(
        compute='_compute_attached_docs_count',
        string='Number of documents attached',
    )
    city_id = fields.Many2one('res.city', 'City of Address', tracking=True)
    surface = fields.Float('Surface')
    quotity = fields.Integer('Quotity')
    smoke_alarms = fields.Integer('Smoke Detectors')
    peb_certificate = fields.Char('PEB Certificate nbr')
    peb_category = fields.Char('PEB Category')
    peb_certificator_id = fields.Many2one('res.partner', string='PEB certificator')
    peb_expiration_date = fields.Date('Expiration Date')
    peb_conso = fields.Float('PEB Consumption/m2')

    tenant_id = fields.Many2one('res.partner', string='Tenant', tracking=True)
    syndic_id = fields.Many2one('res.partner', string='Syndic')
    technician_default_id = fields.Many2one('res.partner', string='Technician', tracking=True)
    work_billing_id = fields.Many2one('res.partner', string='Work billing')
    maintenance_billing_id = fields.Many2one('res.partner', string='Maintenance billing')
    build_year = fields.Date(
        string='Build year',
        default=fields.Date.today().replace(year=1900, month=1, day=1),
    )
    # TODO a verfifier!!!!!!!!!!!!!!!!!!!
    qr_code = fields.Char(string='QR Code', copy=False)
    have_a_parent_property = fields.Boolean(string='A une propriété parent?', default=False)
    for_rent = fields.Boolean(string='For Rent?')
    batiment_age = fields.Integer(
        compute='_compute_batiment_age',
        string='Age',
        readonly=True,
    )
    is_residential = fields.Boolean(string='Is residential?')
    is_parent = fields.Boolean(string='is a parent', default=False)

    # sales
    sale_order_ids = fields.One2many(comodel_name='sale.order', inverse_name='property_id', string='Sales',)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count')

    # x_studio_plaquette_signaltique_chaudire
    hm_boiler_nameplate = fields.Html(string="Plaquette signalétique chaudière", store=True,
                                                          index=False, copy=False, translate=False)
    # x_studio_type_need_a_parent
    hm_type_need_a_parent = fields.Boolean(string="Type need a parent", store=True, readonly=True, copy=False,
                                                 index=False, related="property_type_id.have_a_parent_property")

    check_tenant_address = fields.Boolean('Check tenant Address', store=True, default=False)
    check_landlord_address = fields.Boolean('Check landlord Address', store=True, default=False)
    customer_reference = fields.Char(string='Référence client')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []
        property_ids = []
        results = super(HmProperty, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)
        property_ids = list(results)
        if name and operator in ['=', 'ilike']:
            property_ids = self._search(
                [
                    '|',
                    ('landlord_id', 'ilike', name),
                    '|',
                    ('tenant_id', 'ilike', name),
                    ('display_name', 'ilike', name),
                ]
                + args,
                limit=limit,
            )
        if not property_ids:
            property_ids = self._search(
                [
                    ('display_name', operator, name),
                ]
                + args,
                limit=limit,
                access_rights_uid=name_get_uid,
                )
        return property_ids

    @api.depends('name', 'zip', 'street', 'street2', 'state_id', 'country_id', 'city')
    def _compute_display_name(self):
        for property in self:
            if property.have_a_parent_property:
                name = (
                    str(property.street)
                    + ' '
                    + str(property.street2)
                    + ','
                    + str(property.zip)
                )
                if property.city:
                    name += ' ' + str(property.city)
                if property.country_id:
                    name += ', ' + str(
                        property.country_id and property.country_id.name
                    )
            else:
                name = str(property.street)
                if property.zip:
                    name += ' ' + str(property.zip)
                if property.city:
                    name += ' ' + str(property.city)
                if property.country_id:
                    name += ', ' + str(
                        property.country_id
                        and property.country_id.name
                        or False
                    )

            property.name = name
            property.display_name = name

    @api.depends('parent_path')
    def _get_main_property(self):
        for property in self:
            ancestor_id = property.parent_path.split('/')[0]
            property.main_property_id = self.env['hm.property'].search(
                [('id', '=', ancestor_id)]
            )

    def _for_rent_search(self, operator, value):
        ids = []
        for property in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](property['for_rent'], value):
                ids.append(property.id)
        return [('id', 'in', ids)]

    def _compute_attached_docs_count(self):
        Attachment = self.env['ir.attachment']
        for task in self:
            task.doc_count = Attachment.search_count(
                [('res_model', '=', 'hm.tenancy'), ('res_id', '=', task.id)]
            )

    def _compute_batiment_age(self):
        for property in self:
            property.batiment_age = relativedelta(datetime.now(), property.build_year).years

    def _child_count(self):
        self.child_count = len(self.child_ids)


    # On/Off the edit mode for delivery address based on user profil
    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HmProperty, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            for node in doc.xpath("//field[@name='partner_id']"):
                if self.env.user.has_group('hm_property.group_property_admin'):
                    node.set('options', "{'no_open': False}")
                else:
                    node.set('options', "{'no_open': True}")
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(rec.sale_order_ids)



    def get_street_fields(self):
        """Returns the fields that can be used in a street format.
        Overwrite this function if you want to add your own fields."""
        return STREET_FIELDS

    def _set_street(self):
        """Updates the street field.
        Writes the `street` field on the partners when one of the sub-fields in STREET_FIELDS
        has been touched"""
        street_fields = self.get_street_fields()
        for properti in self:
            street_format = ( '%(street_number)s/%(street_number2)s %(street_name)s'
            )
            previous_field = None
            previous_pos = 0
            street_value = ''
            separator = ''
            # iter on fields in street_format, detected as '%(<field_name>)s'
            for re_match in re.finditer(r'%\(\w+\)s', street_format):
                # [2:-2] is used to remove the extra chars '%(' and ')s'
                field_name = re_match.group()[2:-2]
                field_pos = re_match.start()
                if field_name not in street_fields:
                    raise UserError(
                        _('Unrecognized field %s in street format.')
                        % field_name
                    )
                if not previous_field:
                    # first iteration: add heading chars in street_format
                    if properti[field_name]:
                        street_value += (
                            street_format[0:field_pos] + properti[field_name]
                        )
                else:
                    # get the substring between 2 fields, to be used as separator
                    separator = street_format[previous_pos:field_pos]
                    if street_value and properti[field_name]:
                        street_value += separator
                    if properti[field_name]:
                        street_value += properti[field_name]
                previous_field = field_name
                previous_pos = re_match.end()

            # add trailing chars in street_format
            street_value += street_format[previous_pos:]
            if not properti.have_a_parent_property:
                properti.street = street_value

    @api.model
    def _split_street_with_params(self, street_raw, street_format=False):
        regex = r'((\d+\w* ?(-|\/) ?\d*\w*)|(\d+\w*))'

        street_name = street_raw
        street_number = ''
        street_number2 = ''

        # Try to find number at beginning
        start_regex = re.compile('^' + regex)
        matches = re.search(start_regex, street_raw)
        if matches and matches.group(0):
            street_number = matches.group(0)
            street_name = re.sub(start_regex, '', street_raw, 1)
        else:
            # Try to find number at end
            end_regex = re.compile(regex + '$')
            matches = re.search(end_regex, street_raw)
            if matches and matches.group(0):
                street_number = matches.group(0)
                street_name = re.sub(end_regex, '', street_raw, 1)

        if street_number:
            street_number_split = street_number.split('/')
            if len(street_number_split) > 1:
                street_number2 = street_number_split.pop(-1)
                street_number = '/'.join(street_number_split)

        return {
            'street_name': street_name.strip(),
            'street_number': street_number.strip(),
            'street_number2': street_number2.strip(),
        }

    @api.depends('street')
    def _split_street(self):
        """Splits street value into sub-fields.
        Recomputes the fields of STREET_FIELDS when `street` of a partner is updated"""
        street_fields = self.get_street_fields()
        for properti in self:
            if not properti.street:
                for field in street_fields:
                    properti[field] = None
                continue

            street_format = ( '%(street_number)s/%(street_number2)s %(street_name)s'
            )
            street_raw = properti.street
            vals = self._split_street_with_params(street_raw, street_format)
            # assign the values to the fields
            for k, v in vals.items():
                properti[k] = v
            for k in set(street_fields) - set(vals):
                properti[k] = None

    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)

    def _formatting_address_fields(self):
        """Returns the list of address fields usable to format addresses."""
        return self._address_fields() + self.get_street_fields()

    @api.constrains('display_name')
    def _check_name(self):
        for property in self:
            domain = [
                ('display_name', '=', property.display_name),
                ('id', '!=', property.id),
            ]
            if self.search(domain):
                raise UserError(_('le nom du bien doit être unique.'))

    def action_open_documents(self):
        self.ensure_one()
        domain = [
            ('res_model', '=', 'hm.property'),
            ('res_id', 'in', self.ids),
        ]
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _(
                """<p class="oe_view_nocontent_create">
                        Documents are attached to your property.</p><p>
                        Send messages or log internal notes with attachments to link
                        documents to your project.
                    </p>"""
            ),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}"
            % (self._name, self.id),
        }

    @api.onchange('street2')
    def onchange_street2(self):
        if self.street2:
            parent_id = self.env.context.get('default_parent_id', False)
            if not parent_id and self.parent_id:
                parent_id = self.parent_id.id
            if parent_id:
                parent_id = self.browse(parent_id)
                child_ids = self.search(
                    [
                        ('parent_id', '=', parent_id.id),
                        ('street2', '=', self.street2),
                    ]
                )
                if len(child_ids):
                    raise UserError('Rue 2 existe déjà!')

    @api.onchange('property_type_id')
    def onchange_property_type_id(self):
        if self.property_type_id:
            self.have_a_parent_property = self.property_type_id.have_a_parent_property
            self.is_residential = self.property_type_id.is_residential
            self.is_parent = self.property_type_id.is_parent
        else:
            self.have_a_parent_property = False
            self.is_residential = False
            self.is_parent = False
        res = {'domain': {'parent_id': []}}
        if self.property_type_id.have_a_parent_property:
            res = {'domain': {'parent_id': [('is_parent', '=', True)]}}
        return res

    @api.onchange('city')
    def onchange_city(self):
        state_id = False
        if self.city:
            state_id = self.env['zip.code'].search(
                [
                    ('commune_principale', '=', self.city.upper()),
                ], limit= 1
            )
        self.state_id = state_id and state_id.state_id.id or False

    @api.onchange('state_id', 'zip')
    def onchange_zip(self):
        zip_code_id = False
        if self.zip:
            zip_code_id = self.env['zip.code'].search(
                [
                    ('zip', '=', self.zip),
                    ], limit=1
            )
        self.state_id = zip_code_id and zip_code_id.state_id.id or False
        self.city = zip_code_id and zip_code_id.commune_principale or False

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        if self.parent_id:
            self.street = self.parent_id.street
            self.street2 = self.parent_id.street2
            self.zip = self.parent_id.zip
            self.city = self.parent_id.city
            self.state_id = (
                self.parent_id.state_id and self.parent_id.state_id.id or False
            )
            self.country_id = (
                self.parent_id.country_id
                and self.parent_id.country_id.id
                or False
            )
            if not self.syndic_id:
                self.syndic_id = (
                    self.parent_id.syndic_id
                    and self.parent_id.syndic_id.id
                    or False
                )
            if not self.landlord_id:
                self.landlord_id = (
                    self.parent_id.landlord_id
                    and self.parent_id.landlord_id.id
                    or False
                )
            if not self.technician_default_id:
                self.technician_default_id = (
                    self.parent_id.technician_default_id
                    and self.parent_id.technician_default_id.id
                    or False
                )
            if not self.work_billing_id:
                self.work_billing_id = (
                    self.parent_id.work_billing_id
                    and self.parent_id.work_billing_id.id
                    or False
                )
            if not self.maintenance_billing_id:
                self.maintenance_billing_id = (
                    self.parent_id.maintenance_billing_id
                    and self.parent_id.maintenance_billing_id.id
                    or False
                )
            self.build_year = self.parent_id.build_year
            self.qr_code = self.parent_id.qr_code

    @api.onchange('tenant_id')
    def onchange_tenant_id(self):
        tenant_invoice_address = False
        partner_invoice_address = False
        maintenance_billing_address = False
        if self.tenant_id and self.tenant_id.child_ids:
            if len(self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')) > 1:
                self.check_tenant_address = True
                self.check_landlord_address = False
            else:
                self.check_tenant_address = False

        if self.tenant_id:
            if self.tenant_id.child_ids:
                if len(self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice'))>1:
                    tenant_invoice_address = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')[0]
                else:
                    tenant_invoice_address = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')
            elif tenant_invoice_address:
                self.maintenance_billing_id = tenant_invoice_address.id
            else:
                self.maintenance_billing_id = self.tenant_id.id
        if self.tenant_id and not self.landlord_id:

            if self.tenant_id.child_ids:
                if len(self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice'))>1:
                    tenant_invoice_address = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')[0]
                else:
                    tenant_invoice_address = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')

            if tenant_invoice_address:
                self.maintenance_billing_id = tenant_invoice_address.id
                self.work_billing_id = tenant_invoice_address.id
            else:
                self.maintenance_billing_id = self.tenant_id.id
                self.work_billing_id = self.tenant_id.id
        else:
            if self.landlord_id.child_ids:
                if len(self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice'))>1:

                    partner_invoice_address = self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice')[0]
                else:
                    partner_invoice_address = self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice')
            if self.tenant_id and not partner_invoice_address:
                if self.tenant_id.child_ids:
                    if len(self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')) > 1:

                        tenant_invoice_address = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')[0]
                    else:
                        tenant_invoice_address = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')
                    self.maintenance_billing_id = tenant_invoice_address.id
                    self.work_billing_id = self.landlord_id.id
                else:
                    self.maintenance_billing_id = self.tenant_id.id
                    self.work_billing_id = self.landlord_id.id
            if partner_invoice_address:
                if self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice') :
                    if len(self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice'))>1:
                        self.maintenance_billing_id = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')[0]
                    else:
                        self.maintenance_billing_id = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')
                else :
                    self.maintenance_billing_id= self.tenant_id.id
                self.work_billing_id = partner_invoice_address.id

            else:
                self.maintenance_billing_id = self.tenant_id.id
                self.work_billing_id = self.landlord_id.id

    @api.onchange('for_rent')
    def onchange_for_rent(self):
        self.tenant_id = False

    @api.onchange('syndic_id')
    def onchange_parent_syndic(self):
        if self.syndic_id and self.is_parent:
            self.work_billing_id = self.syndic_id.id
            self.maintenance_billing_id = self.syndic_id.id
            self.manager_id = self.syndic_id.id

    @api.onchange('landlord_id')
    def onchange_landlord(self):
        partner_invoice_address = False
        if self.landlord_id and self.is_parent:
            if not self.landlord_id.landlord_manager_id:
                self.manager_id = (self.landlord_id and self.landlord_id.id or False)
            else:
                self.manager_id = (self.landlord_id.landlord_manager_id and self.landlord_id.landlord_manager_id.id or False)
            if self.landlord_id.child_ids:
                if len(self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice'))>1:
                    partner_invoice_address = self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice')[0]
                else:
                    partner_invoice_address = self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice')

            if partner_invoice_address:
                self.maintenance_billing_id = partner_invoice_address.id
                self.work_billing_id = partner_invoice_address.id
            else:
                self.work_billing_id = self.landlord_id.id
                self.maintenance_billing_id = self.landlord_id.id
            self.tenant_id = self.landlord_id.id
        if self.landlord_id and not self.tenant_id:
            if self.landlord_id.child_ids:
                if len(self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice'))>1:

                    partner_invoice_address = self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice')[0]
                else:
                    partner_invoice_address = self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice')
            if partner_invoice_address:
                self.maintenance_billing_id = partner_invoice_address.id
                self.work_billing_id = partner_invoice_address.id
            else:
                self.maintenance_billing_id = self.landlord_id.id
                self.work_billing_id = self.landlord_id.id
        else:
            if self.landlord_id.child_ids:
                if len(self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice'))>1:
                    self.check_landlord_address = True
                    self.check_tenant_address = False
                    partner_invoice_address = self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice')[0]
                else:
                    partner_invoice_address = self.landlord_id.child_ids.filtered(lambda c: c.type == 'invoice')
                    self.check_landlord_address = False
            if partner_invoice_address:
                if self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice'):
                    if len(self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice'))>1:
                        self.maintenance_billing_id = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')[0]
                    else:
                        self.maintenance_billing_id = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')
                else:
                     self.tenant_id.id
                self.work_billing_id = partner_invoice_address.id
            else:
                if self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice'):
                    if len(self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')) > 1:
                        self.maintenance_billing_id = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')[
                            0]
                    else:
                        self.maintenance_billing_id = self.tenant_id.child_ids.filtered(lambda c: c.type == 'invoice')
                else:
                    self.maintenance_billing_id = self.tenant_id.id
                self.work_billing_id = self.landlord_id.id

    @api.onchange('is_parent')
    def onchange_parent(self):
        if self.syndic_id and self.is_parent:
            self.work_billing_id = self.syndic_id.id
            self.maintenance_billing_id = self.syndic_id.id

        if self.landlord_id and self.for_rent:
            self.work_billing_id = self.landlord_id.id

    @api.model_create_multi
    def create(self, vals_list):
        res = super(HmProperty, self).create(vals_list)

        for record, values in zip(res, vals_list):
            record._split_street()
            partner_vals = {
                'name': record.name,
                'street': record.street,
                'street_name': record.street_name or (record.parent_id and record.parent_id.street_name) or '',
                'street_number': record.street_number,
                'street2': record.street2 or False,
                'city': record.city,
                'state_id': record.state_id.id or False,
                'zip': record.zip,
                'country_id': record.country_id.id or False,
                'type': 'delivery',
                'from_property': True,
                'active': False,
            }
            partner = self.env['res.partner'].create(partner_vals)
            subtype = partner._track_subtype({'active': partner.active})
            partner.message_post(subtype_id=subtype.id, body=subtype.description)

            record.write({
                'partner_id': partner.id,
                'check_tenant_address': False,
                'check_landlord_address': False
            })

            if "zip" in values:
                zip_code_id = self.env['zip.code'].search([('zip', '=', record.zip)], limit=1)
                record.state_id = zip_code_id.state_id.id if zip_code_id else False

        return res

    def write(self, vals):
        res = super(HmProperty, self).write(vals)
        if 'country_id' in vals and 'street' not in vals:
            self._set_street()
        address_fields = self._formatting_address_fields()
        if self.check_tenant_address == True:
            self.check_tenant_address = False
        if self.check_landlord_address == True:
            self.check_landlord_address = False
        if any(f in vals for f in address_fields):
            if self.partner_id:
                partner_vals = {
                    'name': self.name,
                    'street': self.street,
                    'street_name': self.street_name,
                    'street_number': self.street_number,
                    'street2': self.street2 or False,
                    'city': self.city,
                    'state_id': self.state_id.id or False,
                    'zip': self.zip,
                    'country_id': self.country_id.id or False,
                    'type': 'delivery',
                }
                self.partner_id.write(partner_vals)
        if "zip" in vals:
            zip_code_id = self.env['zip.code'].search([('zip', '=', self.zip)], limit=1)
            self.state_id = zip_code_id and zip_code_id.state_id.id or False
        return res

    @api.model
    def cron_create_partner(self):
        property_ids = self.search([('partner_id', '=', False)], limit=40)
        partner_obj = self.env['res.partner']
        if property_ids:
            for property in property_ids:
                partner_vals = [
                    {
                        'name': property.name,
                        'street': property.street,
                        'street2': property.street2 or False,
                        'city': property.city,
                        'state_id': property.state_id.id or False,
                        'zip': property.zip,
                        'country_id': property.country_id.id or False,
                        'type': 'delivery',
                    }
                ]
                partner = partner_obj.create(partner_vals)
                property.write({'partner_id': partner.id})

    @api.onchange('display_name')
    def onchange_show_child_type(self):
        filter_type_by = self.env.context.get('filter_type_by', False)
        if filter_type_by:
            is_parent = True
            have_a_parent_property = False
            if filter_type_by == 'child':
                is_parent = False
                have_a_parent_property = True
            return {'domain': {'property_type_id': [('is_parent', '=', is_parent), ('have_a_parent_property', '=', have_a_parent_property)]}}

    @api.onchange('build_year')
    def onchange_build_year(self):
        if self.child_ids:
            child_ids = self.browse(self.child_ids.ids)
            for child in child_ids:
                child.write({'build_year': self.build_year})

    @api.model
    def update_partner(self):
        property_ids = self.search([])
        for property in property_ids:
            property.partner_id.write({'from_property': True})

    @api.model
    def update_properties_build_year(self):
        property_ids = self.search([('child_ids', '!=', False)])
        for property in property_ids:
            for child in property.child_ids:
                child.write({'build_year': property.build_year})
