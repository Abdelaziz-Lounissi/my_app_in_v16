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


class ResPartner(models.Model):
    _inherit = "res.partner"

    def check_emails_to_ignore(self, email, emails_to_ignore):
        for email_ignore in emails_to_ignore:
            if email_ignore.lower() in email.lower():
                return True
        return False

    @api.model_create_multi
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        for values in vals:
            context = self.env.context
            if context.get('emails_to_ignore_check', False):
                emails_to_ignore = self.env["ir.config_parameter"].sudo().get_param("emails_to_ignore", default=[])
                email = context.get('crm_email', False)
                check_emails_to_ignore = False
                if emails_to_ignore and email:
                    emails_to_ignore = list(emails_to_ignore.split(';'))
                    check_emails_to_ignore = self.check_emails_to_ignore(email=email, emails_to_ignore=emails_to_ignore)
                    if not check_emails_to_ignore:
                        res['email'] = email
                if not check_emails_to_ignore and 'phone' not in values and context.get('crm_phone', False):
                    res['phone'] = context.get('crm_phone', '')

        return res

    def write(self, vals):
        context = self.env.context
        if context.get('emails_to_ignore_check', False):
            emails_to_ignore = self.env["ir.config_parameter"].sudo().get_param("emails_to_ignore", default=[])
            email = vals.get('email', False)
            if emails_to_ignore and email:
                check_email = True
                emails_to_ignore = list(emails_to_ignore.split(';'))
                check_email = self.check_emails_to_ignore(email=email, emails_to_ignore=emails_to_ignore)
                if not check_email:
                    vals['email'] = email
        res = super(ResPartner, self).write(vals)
        return res

    @api.model
    def default_get(self, fields):
        res = super(ResPartner, self).default_get(fields)
        context = self.env.context
        auto_addresse_locataire = context.get('auto_addresse_locataire', False)
        if not context.get('default_for_rent', True):
            res['street'] = context.get('street', '')
            res['street2'] = context.get('street2', '')
            res['city'] = context.get('city', '')
            res['state_id'] = context.get('state_id', False)
            res['country_id'] = context.get('country_id', False)
            res['zip'] = context.get('zip', '')

        if auto_addresse_locataire:
            res['street'] = context.get('default_street', '')
            res['street2'] = context.get('default_street2', '')
            res['city'] = context.get('default_city', '')
            res['state_id'] = context.get('default_state_id', False)
            res['country_id'] = context.get('default_country_id', False)
            res['zip'] = context.get('default_zip', '')

        if context.get('emails_to_ignore_check', False):
            emails_to_ignore = self.env["ir.config_parameter"].sudo().get_param("emails_to_ignore", default=[])
            email = context.get('crm_email', False)
            check_emails_to_ignore = False
            if emails_to_ignore and email:
                emails_to_ignore = list(emails_to_ignore.split(';'))
                check_emails_to_ignore = self.check_emails_to_ignore(email=email, emails_to_ignore=emails_to_ignore)
                if not check_emails_to_ignore:
                    res['email'] = email
            if not check_emails_to_ignore:
                res['phone'] = context.get('crm_phone', '')

        return res

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id:
            self.city = self.city_id.name
            self.zip = self.city_id.zipcode
            self.state_id = self.city_id.state_id

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'active' in init_values and self.active == True:
            return self.env.ref('hm_property.mt_partner_unarchived')
        elif 'active' in init_values and self.active == False:
            return self.env.ref('hm_property.mt_partner_archived')
        return super(ResPartner, self)._track_subtype(init_values)

