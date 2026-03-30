# -*- encoding: utf-8 -*-

from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
import operator as py_operator
import pytz
from werkzeug.urls import url_encode
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


class TechnicianInterventionProposal(models.Model):
    _name = "hm.technician.intervention.proposal"
    _description = "Technician Intervention Proposal"

    STATUS_SELECTION = [
        ('shortlisted', 'Shortlisted'),
        ('sent', 'Proposal sent'),
        ('interested', 'Interested'),
        ('accepted', 'Proposal accepted'),
        ('declined', 'Proposal declined'),
        ('canceled', 'Canceled'),
    ]
    name = fields.Char(compute='_get_name')
    active = fields.Boolean(default=True)
    state = fields.Selection(selection=STATUS_SELECTION, default='shortlisted', string='Status')
    proposal_datetime = fields.Datetime(string='Proposal Date')
    tech_answer_deadline_datetime = fields.Datetime(string='Technician Answer Deadline')
    tech_first_answer_datetime = fields.Datetime(string="First technician's response",
                                                 help="Date à laquelle le technicien a décliné ou renseigné ses disponibilités pour la première fois")
    interested_datetime = fields.Datetime(string='Interested Date')
    availability_last_updated = fields.Datetime(string='Availability Last Updated',
                                                help="Date à laquelle les disponibilités du technicien ont été mises à jour pour la dernière fois")
    declined_datetime = fields.Datetime(string='Declined Date',
                                        help="Date à laquelle le technicien a refusé la proposition")
    accepted_datetime = fields.Datetime(string='Accepted Date')
    canceled_datetime = fields.Datetime(string='Canceled Date')
    sale_order_id = fields.Many2one('sale.order')
    partner_id = fields.Many2one('res.partner', string='Technician', required=True)
    technician_availability_ids = fields.One2many('hm.resource.availability.calendar', 'tech_availability_id',
                                                  'Technician Availability')
    hm_customer_availability_id = fields.Many2one('hm.customer.availability',
                                                  related='sale_order_id.customer_availability_id',
                                                  string='Customer Availability')

    hm_so_manager_id = fields.Many2one('res.users', string='SO Manager', search='_for_hm_so_manager',
                                       compute='get_so_datas')
    hm_so_manager_phone = fields.Char(string='Numéro de téléphone gestionnaire SO', readonly=False,
                                      search='_for_hm_so_manager', compute='get_so_datas')
    property_id = fields.Many2one("hm.property", string="Property", search='_for_property_id', compute='get_so_datas')
    property_address_without_street = fields.Char(string="Property address without street",
                                                  search='_for_property_address_without_street',
                                                  compute='_compute_property_address_without_street', compute_sudo=True)

    work_type = fields.Many2one('hm.work.type', string='Work type', search='_for_work_type', compute='get_so_datas')
    hm_work_object = fields.Char(string='Object', search='_for_hm_work_object', compute='get_so_datas', translate=True)
    urgency_level = fields.Char(string='Emergency degrees', search='_for_urgency_level', compute='get_so_datas')

    sent_by_id = fields.Many2one('res.users', string='Sent by')
    accepted_by_id = fields.Many2one('res.users', string='Accepted by')
    canceled_by_id = fields.Many2one('res.users', string='Cancelled by')
    sequence = fields.Integer('Sequence', default=1, help="Used to order proposal")
    allow_availabilities_outside_prefs = fields.Boolean(
        string='Allow Technician to Enter Availabilities Outside Client Preferences',
        search='_for_allow_availabilities_outside_prefs', compute='get_so_datas',
        help="If I have client availability, I will retrieve that value; otherwise, I will return True.")
    currency_id = fields.Many2one(related='create_uid.currency_id')
    urgency_fee = fields.Monetary(
        string="Urgency fee for intervention within 24 hours",
        search='_for_urgency_fee', compute='get_so_datas')
    intervention_deadline_date = fields.Datetime(
        string="Date limite d'intervention",
        search='_for_intervention_deadline_date', compute='get_so_datas')
    show_confirm_proposal_button = fields.Boolean(
        string="Technical field, used to hide/show the confirm button based on customer availability",
        help="Technical field",
        index=True,
        search='_for_show_confirm_proposal_button',
        compute='compute_show_confirm_proposal_button'
    )

    def _for_intervention_deadline_date(self, operator, value):
        ids = []
        for proposal in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](proposal['intervention_deadline_date'], value):
                ids.append(proposal.id)
        return [('id', 'in', ids)]

    def _for_urgency_fee(self, operator, value):
        ids = []
        for proposal in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](proposal['urgency_fee'], value):
                ids.append(proposal.id)
        return [('id', 'in', ids)]

    def _for_allow_availabilities_outside_prefs(self, operator, value):
        ids = []
        for proposal in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](proposal['allow_availabilities_outside_prefs'], value):
                ids.append(proposal.id)
        return [('id', 'in', ids)]

    def _for_property_address_without_street(self, operator, value):
        ids = []
        for product in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](product['property_address_without_street'], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def compute_show_confirm_proposal_button(self):
        for proposal in self:
            show_confirm_proposal_button = False
            if proposal.state == 'interested':
                show_confirm_proposal_button = True
            proposal.show_confirm_proposal_button = show_confirm_proposal_button

    def _compute_property_address_without_street(self):
        for proposal in self:
            property_address_without_street = ""
            parent_property_address_without_street = ""
            property = proposal.property_id
            if property:
                property_address_without_street += str(property.zip)
                if property.city:
                    property_address_without_street += ' ' + str(property.city)
                if property.country_id:
                    property_address_without_street += ', ' + str(
                        property.country_id and property.country_id.name
                    )

                if property.have_a_parent_property:
                    property = property.parent_id

                    parent_property_address_without_street += str(property.zip)
                    if property.city:
                        parent_property_address_without_street += ' ' + str(property.city)
                    if property.country_id:
                        parent_property_address_without_street += ', ' + str(
                            property.country_id and property.country_id.name
                        )

            # debug parent_property_address_without_street
            # proposal.parent_property_address_without_street = parent_property_address_without_street
            proposal.property_address_without_street = property_address_without_street

    def _for_property_address_without_street(self, operator, value):
        ids = []
        for product in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](product['property_address_without_street'], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def _for_hm_work_object(self, operator, value):
        ids = []
        for proposal in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](proposal['hm_work_object'], value):
                ids.append(proposal.id)
        return [('id', 'in', ids)]

    def _for_work_type(self, operator, value):
        ids = []
        for proposal in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](proposal['work_type'], value):
                ids.append(proposal.id)
        return [('id', 'in', ids)]

    def _for_property_id(self, operator, value):
        ids = []
        for proposal in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](proposal['property_id'], value):
                ids.append(proposal.id)
        return [('id', 'in', ids)]

    def _for_hm_so_manager_phone(self, operator, value):
        ids = []
        for proposal in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](proposal['hm_so_manager_phone'], value):
                ids.append(proposal.id)
        return [('id', 'in', ids)]

    def _for_hm_so_manager(self, operator, value):
        ids = []
        for proposal in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](proposal['hm_so_manager_id'], value):
                ids.append(proposal.id)
        return [('id', 'in', ids)]

    def _for_urgency_level(self, operator, value):
        ids = []
        for proposal in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](proposal['urgency_level'], value):
                ids.append(proposal.id)
        return [('id', 'in', ids)]

    def get_so_datas(self):
        for rec in self.sudo():
            sale_order_id = rec.sudo().sale_order_id

            rec.hm_so_manager_id = sale_order_id.hm_so_manager_id
            rec.hm_so_manager_phone = sale_order_id.hm_so_manager_phone
            rec.property_id = sale_order_id.property_id
            rec.work_type = sale_order_id.work_type
            rec.hm_work_object = sale_order_id.hm_work_object

            emergency_degrees_id = sale_order_id.emergency_degrees_id
            rec.urgency_level = emergency_degrees_id.technical_value if emergency_degrees_id else ""
            rec.urgency_fee = emergency_degrees_id.urgency_fee if emergency_degrees_id else 0

            rec.intervention_deadline_date = sale_order_id.intervention_deadline_date or False

            customer_availability_id = sale_order_id.customer_availability_id
            rec.allow_availabilities_outside_prefs = customer_availability_id.allow_availabilities_outside_prefs if customer_availability_id else True

    @api.model
    def _get_name(self):
        for rec in self.sudo():
            rec.name = 'Proposal/' + str(rec.sudo().sale_order_id.name) + '/' + str(rec.partner_id.name)

    def get_msg_by_lang(self, msg, lang):
        translated_msg = ''
        if lang == 'nl_BE':
            if msg == 'Confirmation RDV':
                translated_msg = 'Afspraak bevestigd'
            elif msg == 'Modification RDV':
                translated_msg = 'Wijziging afspraak'
            elif msg == 'Nouvelle proposition':
                translated_msg = 'Nieuw voorstel'
            elif msg == 'Proposition annulée':
                translated_msg = 'Voorstel geannuleerd'
            elif msg == 'Intervention annulée':
                translated_msg = 'Interventie geannuleerd'
            elif msg == "L'intervention":
                translated_msg = 'De geplande interventie'
            elif msg == "prévue le":
                translated_msg = 'op'
            elif msg == "a été annulée":
                translated_msg = 'is geannuleerd'
            elif msg == "Urgence avec supplément":
                translated_msg = 'Dringend met toeslag'
        elif lang == 'en_US':
            if msg == 'Confirmation RDV':
                translated_msg = 'Appointment Confirmation'
            elif msg == 'Modification RDV':
                translated_msg = 'Change in Appointment'
            elif msg == 'Nouvelle proposition':
                translated_msg = 'New proposal'
            elif msg == 'Proposition annulée':
                translated_msg = 'Cancelled proposal'
            elif msg == 'Intervention annulée':
                translated_msg = 'Cancelled intervention'
            elif msg == "L'intervention":
                translated_msg = 'The scheduled intervention'
            elif msg == "prévue le":
                translated_msg = 'on'
            elif msg == "a été annulée":
                translated_msg = 'has been canceled'
            elif msg == "Urgence avec supplément":
                translated_msg = 'Urgent with supplement'
        if not translated_msg:
            translated_msg = msg
        return translated_msg

    def run_proposal_notification(self, notification_type):
        notification_obj = self.env['hm.mobile.notification']
        token_obj = self.env['hm.mobile.token']
        context = self.env.context

        if context.get('notif_from_so', False):
            so_id = context.get('so_id', False)
            so_rec = self.env['sale.order'].browse(so_id)
            if context.get('hm_imputed_technician_id', False):
                hm_imputed_technician_id = context.get('hm_imputed_technician_id', False)
                partner_id = self.env['res.partner'].browse(hm_imputed_technician_id)
            else:
                partner_id = so_rec.hm_imputed_technician_id
        else:
            so_id = self.sale_order_id.id
            so_rec = self.sale_order_id
            partner_id = self.partner_id

        commitment_date = so_rec.commitment_date
        commitment_date_str = ""
        if commitment_date:
            tz = pytz.timezone('Europe/Brussels')
            commitment_date_str = pytz.utc.localize(commitment_date).astimezone(tz).strftime('%d/%m/%Y à %H:%M')

        commitment_date_when_intervention_canceled = False
        commitment_date_when_intervention_canceled_str = ''
        if context.get('commitment_date_when_intervention_canceled', False):
            commitment_date_when_intervention_canceled = context.get('commitment_date_when_intervention_canceled', False)
            tz = pytz.timezone('Europe/Brussels')
            commitment_date_when_intervention_canceled_str = pytz.utc.localize(commitment_date_when_intervention_canceled).astimezone(tz).strftime('%d/%m/%Y à %H:%M')

        hm_work_object = so_rec.hm_work_object or ""
        city = so_rec.property_id and so_rec.property_id.city or ""
        zip_code = so_rec.property_id and so_rec.property_id.zip or ""
        so_number = so_rec.name

        technician_name = ""
        if self.partner_id:
            technician_name = self.partner_id.name
        else:
            technician_name = so_rec.hm_imputed_technician_id.name

        if notification_type == "new":
            message = f"{hm_work_object} ({so_number})\n{zip_code} {city}"

            if so_rec.emergency_degrees_id and so_rec.emergency_degrees_id.urgency_fee > 0:
                urgency_fee = so_rec.emergency_degrees_id.urgency_fee
                if urgency_fee % 1 == 0:
                    urgency_fee = int(urgency_fee)
                else:
                    urgency_fee = float(urgency_fee)
                    urgency_fee = str(urgency_fee).rstrip('0').rstrip('.')
                urgency_fee_msg = f"%s {urgency_fee}€ 🚨"%(self.get_msg_by_lang('Urgence avec supplément', partner_id.lang))

                message = urgency_fee_msg +'\n'+ message

            notification_data = {
                "new": {
                    "title": "🤝 %s"%(self.get_msg_by_lang('Nouvelle proposition', partner_id.lang)),
                    "message": message,
                    "data": {"proposal_id": self.id}
                },
            }

        elif notification_type == "canceled":
            message = f"{hm_work_object} ({so_number})\n{zip_code} {city}"

            notification_data = {
                "canceled": {
                    "title": "❌ %s"%(self.get_msg_by_lang('Proposition annulée', partner_id.lang)),
                    "message": message,
                    "data": {"proposal_id": self.id}
                },
            }
        elif notification_type == "intervention_canceled":
            msg1 = self.get_msg_by_lang("L'intervention", partner_id.lang)
            msg2 = self.get_msg_by_lang('prévue le', partner_id.lang)
            msg3 = self.get_msg_by_lang('a été annulée', partner_id.lang)
            message = f"{msg1} {so_number} {msg2} {commitment_date_when_intervention_canceled_str} {msg3}."

            notification_data = {
                "intervention_canceled": {
                    "title": "❌ %s"%(self.get_msg_by_lang('Intervention annulée', partner_id.lang)),
                    "message": message,
                    "data": {}
                },
            }

        elif notification_type == "confirmed" or notification_type == "updated":
            message = f"{commitment_date_str}\n{hm_work_object} ({so_number})\n{zip_code} {city}"

            if notification_type == "confirmed":
                title = "📅 %s"%(self.get_msg_by_lang('Confirmation RDV', partner_id.lang))
            else:
                title = "📅 %s"%(self.get_msg_by_lang('Modification RDV', partner_id.lang))

            notification_data = {
                notification_type: {
                    "title": title,
                    "message": message,
                    "data": {"intervention_id": so_rec.id}
                },
            }

        notification_info = notification_data.get(notification_type)
        # Notify the technicians if their status is "actif_app"
        if partner_id.hm_status == "actif_app":
            if notification_info:
                tokens = token_obj.search([('user_id.partner_id', '=', partner_id.id)])
                if tokens:
                    notification_rec = notification_obj.create({
                        "title": notification_info["title"],
                        "technician_id": partner_id.id,
                        "message": notification_info["message"],
                        "datas": notification_info["data"],
                        "token_ids": [(6, 0, tokens.ids)]
                    })
                    _logger.info("--- Create notification ID: %s" % notification_rec.id)
                    notification_rec.with_context(so_id=so_id).action_send_notification()
                    self.env.cr.commit()
                else:
                    fail_message = "' " + notification_info["title"] + " ' \n" + "Aucun appareil n'a été enregistré par {technicien}, il ne recevra donc pas de notification.\nNote : soit le technicien n'a pas installé l'application, soit il n'a pas activé les notifications."
                    fail_message = fail_message.format(technicien=technician_name)
                    _logger.warning("⚠️ Attention - No token found: %s" % fail_message)
                    raise ValidationError(fail_message)
        else:
            msg_chatter = "' " + notification_info["title"] + " ' \n" + "n'a pas pu être envoyée à {technicien}, car son statut n'est pas 'Actif - App'."
            msg_chatter = msg_chatter.format(technicien=technician_name)
            so_rec.message_post(
                body=msg_chatter,
                author_id=self.env.ref('base.partner_root').id
            )

    def show_warning_message(self):
        warning_message = "Vous n'êtes pas le gestionnaire du SO. Envoyer la proposition quand même?"
        view = self.env.ref('hm_sales_technicien_info.hm_proposal_warning_wizard_form_view')
        context = self.env.context
        proposal_ids = context.get('proposal_ids', self.ids)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hm.proposal.warning.wizard',
            'name': 'Warning',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_warning_message': warning_message,
                'proposal_ids': proposal_ids,
            }
        }

    def check_so_manager(self):
        sale_order_id = self.sale_order_id
        context = self.env.context
        proposal_ids = context.get('proposal_ids', self.ids)
        if not sale_order_id.hm_so_manager_id:
            sale_order_id.write({"hm_so_manager_id": self.env.user.id})
        elif sale_order_id.hm_so_manager_id and sale_order_id.hm_so_manager_id != self.env.user:
            return self.with_context(proposal_ids=proposal_ids).show_warning_message()
        return True

    def send_proposal(self):
        context = self.env.context
        res = True
        if self.sale_order_id.state != 'sale':
            raise UserError(_("Veuillez confirmer le devis avant d'envoyer les propositions."))
        else:
            if not context.get('force_send_proposal', False):
                res = self.check_so_manager()

            if res and type(res) == bool:
                self.state = 'sent'
                self.proposal_datetime = datetime.now()
                self.sent_by_id = self.env.user.id
                self.run_proposal_notification(notification_type="new")
                self.sale_order_id.last_proposal_sent = datetime.now()

            else:
                return res

    def send_whatsapp(self):
        if self.partner_id and self.partner_id.hm_surnom_heat_me:
            phone_number = str(self.partner_id.phone).replace(" ", "")
            hm_so_manager_name = str(self.sale_order_id.hm_so_manager_id.name) or "Heat Me"
            surnom_tech = self.partner_id.hm_surnom_heat_me or self.partner_id.name or ""
            encodedtext = "Hello "+str(surnom_tech)+", as-tu vu ma proposition pour " +str(self.sale_order_id.name) + " ?"+ "%0A"+ hm_so_manager_name
            whatsapp_url = f"https://wa.me/{phone_number}?text={encodedtext}"
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': whatsapp_url,
            }
        return False

    def run_confirm_process(self, commitment_date):
        if self.sale_order_id:
            self.state = 'accepted'
            self.accepted_datetime = datetime.now()
            self.accepted_by_id = self.env.user.id
            proposal_ids = self.search([('id', '!=', self.id), ('sale_order_id', '=', self.sale_order_id.id)])
            for proposal in proposal_ids:
                proposal.action_cancel_proposal()
            self.sudo().sale_order_id.write(
                {"commitment_date": commitment_date, "state2": "planned",
                 "hm_imputed_technician_id": self.partner_id.id})

    def action_confirm_proposal(self):
        if self.technician_availability_ids:
            if len(self.technician_availability_ids) == 1:
                self.run_confirm_process(commitment_date=self.technician_availability_ids[0].format_date())
            else:
                view_id = self.env.ref('hm_sales_technicien_info.hm_resource_availability_popup_form_view')
                return {
                    'name': ('Disponibilités technicien'),
                    'res_model': 'hm.resource.availability.calendar',
                    'res_id': self.id,
                    'view_id': view_id.id,
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'tree',
                    'target': 'new',
                    'nodestroy': True,
                    'domain': [('tech_availability_id', '=', self.id)],
                }

    def action_cancel_proposal(self):
        if self.state in ('sent', 'interested', 'accepted'):
            notification_type = "canceled"
            if self.state == 'accepted':
                notification_type = 'intervention_canceled'
            self.run_proposal_notification(notification_type=notification_type)
            self.state = 'canceled'
            self.canceled_datetime = datetime.now()
            self.canceled_by_id = self.env.user.id
        elif self.state == "shortlisted":
            self.unlink()

    def action_unlink_proposal(self):
        self.unlink()

    def write(self, vals):
        res = super(TechnicianInterventionProposal, self).write(vals)
        for record in self:
            if 'technician_availability_ids' in vals and record.state in ('shortlisted', 'sent'):
                record.state = 'interested'
                record.notify_so_manager(notification_type='interested', technician_name=record.sudo().partner_id.name)

            if not record.env.context.get('force_skip_write', False):
                if record.state == 'declined':
                    record.with_context(force_skip_write=True).declined_datetime = datetime.now()
                    record.notify_so_manager(notification_type='canceled', technician_name=record.sudo().partner_id.name)
                    if record.tech_first_answer_datetime:
                        record.with_context(force_skip_write=True).availability_last_updated = datetime.now()
                    else:
                        record.with_context(force_skip_write=True).tech_first_answer_datetime = datetime.now()
                elif record.state == 'canceled':
                    record.with_context(force_skip_write=True).canceled_datetime = datetime.now()
                    record.with_context(force_skip_write=True).canceled_by_id = self.env.user.id
        return res

    def unlink(self):
        for proposal in self:
            if proposal.state != 'shortlisted':
                raise UserError(_("You cannot delete a proposal that is not in 'Proposal to send' status."))
        return super(TechnicianInterventionProposal, self).unlink()

    def notify_so_manager(self, notification_type, technician_name):
        if self.sale_order_id and self.sudo().sale_order_id.hm_so_manager_id:
            model_name = "sale.order"
            url_params = {
                'id': self.sale_order_id.id,
                'model': model_name,
                'view_type': 'form'
            }
            notification_data = {
                "interested": {
                    "message": f"✅ Technicien intéressé - '{technician_name}' est disponible.</a>",
                },
                "updated": {
                    "message": f"✅ Technicien intéressé - '{technician_name}' a modifié ses disponibilités.</a>",
                },
                "canceled": {
                    "message": f"❌ Proposition déclinée par '{technician_name}'.</a>",
                }
            }
            notification_info = notification_data.get(notification_type)
            self.sudo().sale_order_id.message_post(
                partner_ids=[self.sudo().sale_order_id.hm_so_manager_id.partner_id.id],
                body=notification_info["message"],
                author_id=self.env.ref('base.partner_root').id,
            )


    def delete_archived_proposals(self):
        self.search([('active', '=', False)]).unlink()