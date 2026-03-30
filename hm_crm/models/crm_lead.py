# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import datetime
from odoo.osv import expression
import operator as py_operator
import logging
import requests

_logger = logging.getLogger(__name__)

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne,
    'ilike': py_operator.contains,
}


class CrmLead(models.Model):
    _inherit = "crm.lead"

    hm_boiler_replacement = fields.Boolean(string="Remplacement de chaudière?", copy=False, store=True,
                                           index=False)
    hm_boiler_power = fields.Text(string="Puissance chaudière?", copy=False, store=True, translate=False,
                                  index=False)
    hm_boiler_type_ecs = fields.Text(string="Type ECS chaudière?", copy=False, store=True, translate=False,
                                     index=False)
    hm_regulation = fields.Text(string="Régulation?", copy=False, store=True, index=False, translate=False)
    hm_boiler_model = fields.Text(string="Modèle de chaudière?", copy=False, store=True, index=False,
                                  translate=False)
    hm_heating_circuit_type = fields.Text(string="Type circuit chauffage?", store=True, copy=False, index=False,
                                          translate=False)
    hm_chimney = fields.Text(string="Cheminée", copy=False, store=True, index=False, translate=False)
    hm_hair_intake = fields.Text(string="Prise d'air", copy=False, store=True, translate=False, index=False)
    hm_motivation_and_deadlines = fields.Text(string="Motivation et délais", copy=False, store=True, translate=False,
                                              index=False)
    hm_boiler_energy_source = fields.Text(string="Source énergie chaudière", store=True, copy=False,
                                          index=False, translate=False)
    hm_condensate_evacuation = fields.Text(string="Évacuation condensats?", copy=False, store=True, index=False,
                                           translate=False)
    hm_boiler_brands_affinity = fields.Text(string="Affinité marques chaudière?", copy=False, store=True,
                                            index=False, translate=False)
    hm_image_sales_team = fields.Binary(string="Image sales team", related="team_id.hm_image_sales_team",
                                        readonly=True, store=True, copy=False, index=False, related_sudo=True)
    hm_sales_team_leader_id = fields.Many2one(comodel_name="res.users", string="Sales team leader", ondelete="set null",
                                              readonly=True, related="team_id.user_id", copy=False, index=False, related_sudo=True)
    hm_elements_to_be_replaced = fields.Text(string="Elements à remplacer?", copy=False, store=True, index=False,
                                             translate=False)
    hm_customer_source_2 = fields.Many2one(comodel_name="customer.source", related="partner_id.hm_customer_source_id",
                                           readonly=True,
                                           store=True,
                                           copy=False, index=False, string="HM Source client", related_sudo=True)
    hm_lead_transmis_id = fields.Many2one(comodel_name="res.users", string="Lead forwarded by", ondelete="set null",
                                          readonly=False, copy=False, store=True, index=False,
                                          domain = "['|', '|', ('partner_id.hm_status', 'ilike', 'Actif'), ('hm_is_internal_user', '=', True), ('id', 'in', [104])]"
                                          )
    hm_wc_lead_id = fields.Integer(string="WhatConverts Lead Id", default=0, tracking=True)
    hm_searchable_phone = fields.Char(string='Partner Searchable Phone', compute='_reset_phone_format',
                                      search='_for_hm_searchable_phone', store=False, index=True, readonly=True)

    # TODO: to be reviewed
    web_partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address')
    web_partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address')

    explicatif = fields.Text(string='Explicatif')
    descriptions = fields.Text(string='Description')
    cas_urgence = fields.Text(string='Urgence')
    je_souhaite = fields.Char(string='Je souhaite')
    hm_html_description = fields.Html(string="Description html", copy=False, store=True, index=False,
                                      translate=False)
    authorize_reminder_action = fields.Boolean(related="stage_id.authorize_reminder_action",
                                               string="Authorize Reminder", related_sudo=True)


    def _for_hm_searchable_phone(self, operator, value):
        leads_ids = []
        for lead in self.with_context(prefetch_fields=False).search([]):
            if operator == 'not ilike' :
                if value not in lead['hm_searchable_phone']:
                    leads_ids.append(lead.id)
            elif OPERATORS[operator](lead['hm_searchable_phone'], value):
                leads_ids.append(lead.id)
        return [('id', 'in', leads_ids)]

    @api.depends('partner_id.phone', 'phone')
    def _reset_phone_format(self):
        for rec in self:
            phone = rec.partner_id.phone or ""
            if not phone:
                phone = rec.phone or ""
            phone = phone.replace(" ", "")
            rec.hm_searchable_phone = phone

    @api.model
    def lieu_valide(self, lieu):
        if not lieu:
            lieu = ''
        else:
            lieu = lieu + ' '
        return lieu

    def action_schedule_meeting(self):
        """ Open meeting's calendar view to schedule meeting on current opportunity.
            :return dict: dictionary value for created Meeting view
        """
        self.ensure_one()

        location = str(self.lieu_valide(self.property_id.street)) + str(
            self.lieu_valide(self.property_id.city)) + str(self.lieu_valide(self.property_id.zip)) + str(
            self.lieu_valide(self.property_id.country_id.name))

        action = self.env.ref('calendar.action_calendar_event').read()[0]
        partner_ids = self.env.user.partner_id.ids
        if self.partner_id:
            partner_ids.append(self.partner_id.id)
        action['context'] = {
            'default_opportunity_id': self.id if self.type == 'opportunity' else False,
            'default_partner_id': self.partner_id.id,
            'default_partner_ids': partner_ids,
            'default_location': location,
            'default_team_id': self.team_id.id,
            'default_contact_lieu': self.partner_onsite_id and self.partner_onsite_id.id or False,
            'default_name': self.name,
        }
        action['domain'] = [('opportunity_id', '=', self.id)]
        return action

    def action_new_quotation(self):
        results = super(CrmLead, self).action_new_quotation()
        results['context'].update({
            'search_default_opportunity_id': self.id,
            'default_opportunity_id': self.id,
            'default_name': self.name,
            'default_company_id': self.company_id.id or self.env.company.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_team_id': self.team_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_property_id': self.property_id.id,
            'default_partner_invoice_id': self.web_partner_invoice_id.id,
            'default_partner_shipping_id': self.web_partner_shipping_id.id,
            'default_partner_onsite_id': self.partner_onsite_id.id,
            'default_origin_crm': True
        })
        return results

    def action_send_email_rappel(self):
        self.ensure_one()
        lang = self.partner_id.lang or 'fr_BE'
        mail_template_rappel = self.env.ref('hm_crm.mail_template_rappel').with_context(lang=lang)
        if not self.partner_id.email:
            raise UserError(_("Unable to post message, please check the partner email."))
        self.message_post_with_template(mail_template_rappel.id, message_type='comment')

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id != self.env.user and not self.hm_lead_transmis_id:
            self.hm_lead_transmis_id = self.env.user.id

    @api.depends('user_id', 'type')
    def _compute_team_id(self):
        for lead in self:
            if (not lead.team_id) and lead.user_id and lead.user_id.team_id :
                lead.team_id = lead.user_id.team_id

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s  %s" % (record.id, record.name)))
        return result

    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = list(args or [])
        all_lead_ids = super(CrmLead, self)._name_search(name, args=args, operator=operator, limit=limit,
                                                         name_get_uid=name_get_uid)
        if name:
            domain = expression.AND([args, [('id', '=ilike', name)]])
            new_lead_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
            all_lead_ids = list(set(all_lead_ids) | set(new_lead_ids))
        return all_lead_ids

    def write(self, vals):
        result = super(CrmLead, self).write(vals)
        if any(key in vals for key in ["probability", "active"]) and self.won_status != "pending":
            offer_activity_ids = self.env['mail.activity.type'].search([
                ('activity_as_complete_opportunity_won_lost', '=', True)
            ])
            if offer_activity_ids:
                activities_to_update = self.activity_ids.filtered(
                    lambda activity: activity.activity_type_id in offer_activity_ids
                )
                if activities_to_update:
                    activities_to_update.action_feedback()
        if "zip" in vals:
            zip_code_id = self.env['zip.code'].search([('zip', '=', self.zip)], limit=1)
            self.state_id = zip_code_id and zip_code_id.state_id.id or False
        return result

    @api.model_create_multi
    def create(self, vals):
        res = super(CrmLead, self).create(vals)
        for values in vals:
            if "zip" in values:
                zip_code_id = self.env['zip.code'].search([('zip', '=', res.zip)], limit=1)
                res.state_id = zip_code_id and zip_code_id.state_id.id or False
        return res

    @api.model
    def send_http_post_request(self, url, payload):
        if not url or not payload:
            raise ValidationError(_("Both URL and payload are required."))
        try:
            # Send the POST request
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return {
                "status_code": response.status_code,
                "response_text": response.text,
            }
        except requests.RequestException as e:
            raise UserError(_("Error while sending the request: %s") % str(e))
