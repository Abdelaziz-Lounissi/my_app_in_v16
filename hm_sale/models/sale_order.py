# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
from datetime import timedelta, time
import logging
import base64
# import pyperclip

_logger = logging.getLogger(__name__)
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_compare

import pytz
import dateutil.relativedelta as relativedelta
from odoo.osv import expression
import requests


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _check_group_edit_deadline_dates_so(self):
        return not self.user.has_group('hm_sale.group_modifier_dates_limites_organisation_cloture_so')

    commitment_date = fields.Datetime('Intervention date',
                                      states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                      copy=False, readonly=True,
                                      help="This is the delivery date promised to the customer. "
                                           "If set, the delivery order will be scheduled based on "
                                           "this date rather than product lead times.")
    hm_display_po = fields.Boolean(string='Display PO', store=True, copy=False, index=False)
    hm_block_auto_mail = fields.Boolean(string='Bloquer mail auto', store=True, copy=False, index=False)
    hm_briefing_necessary_tech = fields.Boolean(string='Briefing tech nécessaire', store=True, copy=False,
                                                index=False)
    hm_partner_id = fields.Char(string='adresse de livr', store=True, copy=False, index=False,
                                related='partner_shipping_id.display_name', translate=False, related_sudo=True)

    hm_debrief_difficulties = fields.Text(string='Difficultés rencontrées', store=True, copy=False, index=False,
                                          translate=False)
    hm_is_debrief_done = fields.Boolean(string='Débriefing réalisé', store=True, copy=False, index=False)
    hm_sales_teams_valid_for_analysis = fields.Many2one('crm.team',
                                                        string='Equipes de vente > VALIDE (pour analyse)',
                                                        store=True, copy=False, index=False,
                                                        ondelete='set null')
    hm_related_field = fields.Char(string='New Champ lié', store=True, copy=False, index=False, translate=False,
                                   related='order_line.hm_technician.hm_surnom_heat_me')
    hm_order_line_technician_name = fields.Char(string='New Champ lié POL Tech.', store=True, copy=False, index=False,
                                                translate=False,
                                                related='order_line.hm_technician.name')
    hm_delivery_datetime = fields.Datetime(string='Delivery date', store=True, copy=False, index=False)
    hm_property_manager_name = fields.Char(string='New Champ lié Prop. manager', store=True, copy=False, index=False,
                                           translate=False,
                                           related='partner_shipping_id.hm_property_manager_id.name')
    hm_partner_do_not_ask_customer_opinions = fields.Boolean(string='Validated', readonly=True, store=True, copy=False,
                                                             index=False,
                                                             related='partner_id.hm_do_not_ask_customer_opinions')
    hm_work_object = fields.Char(string='Object', store=True, copy=True, index=False, translate=False)
    hm_technician_po_id = fields.Many2one('purchase.order', string='PO Technician', store=True, copy=False,
                                          index=False, ondelete='set null',
                                          related='order_line.purchase_line_ids.order_id')
    hm_initial_margin_forecast = fields.Monetary(string='Prévision marge initiale', store=True, copy=False,
                                                 index=False)
    can_edit_initial_margin_forecast = fields.Boolean(compute='_compute_can_edit_initial_margin_forecast', store=False)

    hm_street_delivery_address = fields.Char(string='Rue adresse de livraison', readonly=True, store=True,
                                             copy=False, index=False, translate=False,
                                             related='partner_shipping_id.street')
    hm_sales_team_from_opportunity_crm_id = fields.Many2one('crm.team', string='Sales team from opportunity CRM',
                                                            readonly=True, store=True, copy=False, index=False,
                                                            tracking=True, ondelete='set null',
                                                            related='opportunity_id.team_id',
                                                            help='When sending mails, the default email address is taken from the Sales Team.')
    hm_customer_source_id = fields.Many2one('customer.source', string='Source client', readonly=True, store=True,
                                            copy=False,
                                            index=False, related='partner_id.hm_customer_source_id')
    hm_so_customer_source_invoicing = fields.Many2one('customer.source', string='Source client SO (facturation)',
                                                      readonly=True,
                                                      store=True, copy=False, index=False,
                                                      related='partner_invoice_id.hm_customer_source_id')
    hm_technician = fields.Char(string='HM Technician', readonly=True, store=True, copy=False, index=False,
                                related='hm_imputed_technician_id.display_name', translate=False)
    hm_tel_partner = fields.Char(string='Tel client', store=True, copy=False, index=False, translate=False,
                                 related='partner_id.phone')
    hm_phone_contact_on_site = fields.Char(string='Tel contact sur place', readonly=False, store=True, copy=False,
                                           index=False, translate=False, related='partner_onsite_id.phone')
    hm_type = fields.Char(string='Type', store=True, copy=False, index=False, translate=False,
                          related='sale_order_template_id.name')
    hm_type_1 = fields.Char(string='Type 1', store=True, copy=False, index=False, translate=False,
                            related='sale_order_template_id.name')
    hm_city_intervention = fields.Char(string='City (intervention)', readonly=True, store=True, copy=False,
                                       index=False, translate=False, related='partner_shipping_id.city')
    hm_commande_lie_count = fields.Integer(string='Commande Liée count', store=False,
                                           copy=False, index=False,
                                           compute='_compute_commande_lie_count')
    hm_po_lines_count = fields.Integer(string='PO lines', store=False, copy=False, index=False,
                                       compute='_compute_po_lines_count')
    hm_primes_ids = fields.Many2many('hm.primes', 'x_sale_order_x_primes_rel', 'sale_order_id', 'x_primes_id',
                                     string='Primes', store=True, copy=True, index=False)
    hm_premium_ids = fields.One2many('hm.so.primes.line', 'sale_order_id', copy=True)
    customer_availability = fields.Text(string='Info disponibilités client')
    hm_so_manager_theoretical_workload_in_minutes = fields.Integer('Charge de gestion estimée en minutes',
                                                                   readonly=False)
    hm_so_manager_workload_points = fields.Integer('Points de gestion', readonly=False,
                                                   tracking=True)
    hm_responsible_id = fields.Many2one("res.users", compute="_calcul_hm_responsible", index=True, store=True,
                                        string="Responsable SO")
    hm_validity_date_state2 = fields.Date('Validity date')
    is_greater = fields.Boolean(compute='_get_greater', string='Greater than')
    has_group_sale_manager = fields.Boolean(compute='_has_group_sale_manager', string='Has group sale manager')
    has_group_sale_manager_for_point_of_management = fields.Boolean(
        compute='_has_group_sale_manager_for_point_of_management',
        string='Has group sale manager for point of management')
    amount_untaxed_at_signature = fields.Monetary(string='Untaxed Amount at signature', tracking=True, readonly=True)
    hm_so_invoiced_date = fields.Date(string="Date de passage du SO en statut d'intervention 'Facturé' ", store=True, copy=False, index=True)

    hm_organization_deadline_date = fields.Date(string="A organiser au plus tard le", store=True, copy=False, index=True, tracking=True, readonly=_check_group_edit_deadline_dates_so)
    hm_closing_deadline_date = fields.Date(string="A clôturer au plus tard le", store=True, copy=False, index=True, tracking=True, readonly=_check_group_edit_deadline_dates_so)

    hm_sum_premium_total = fields.Monetary(string='Total des primes disponibles', store=True, readonly=True,
                                           compute='_compute_hm_sum_premium_total', compute_sudo=True)

    hm_amount_total_with_premium = fields.Monetary(string='Total net primes déduites', store=True, readonly=True,
                                                   compute='_compute_hm_amount_total_with_premium')
    hm_amount_total_line_premium = fields.Monetary(string='Total prime SO', default=0.0, store=False, readonly=True,
                                                   compute='_compute_hm_sum_premium_total', compute_sudo=True)

    margin_rate = fields.Float(string='Margin Rate', compute='_compute_margin_rate')
    so_invoice_count = fields.Integer(string='SO Invoice Count', compute='_get_so_invoice_count', readonly=True,
                                      index=True, store=True)
    purchase_ids = fields.One2many("purchase.order", "hm_so_lie", string="purchases")
    check_purchase_ids = fields.Boolean(compute='_compute_check_purchase_ids')
    emergency_degrees_id = fields.Many2one("order.emergency.degrees", string='Emergency degrees')
    intervention_deadline_date = fields.Datetime(string="Date limite d'intervention")
    hm_calculated_margin = fields.Float(string='Calculated margin', compute="_compute_calculated_margin", digits=(3, 2))
    work_report_sent_to_client = fields.Boolean(
        string='Work Report Sent to Client',
        default=False,
        copy=False,
        help="Indicates if the work report has been sent to the client."
    )
    allow_closing_without_report = fields.Boolean(string="Autoriser la clôture sans rapport d'intervention", default=False, copy=False, index=True, help="Autoriser la clôture sans rapport d'intervention.", tracking=True)


    sent_on = fields.Datetime(string="Date d'envoi du devis", store=True, copy=False, index=True, help="Date à laquelle le devis a été envoyé.")
    deposit_received_on = fields.Datetime(string="Acompte reçu le", store=True, copy=False, index=True)
    tech_on_the_way_since = fields.Datetime(string="Technicien en route le", store=True, copy=False, index=True, help="Indicates that the technician is en route since.")
    intervention_planned_on = fields.Datetime(string="Intervention planifiée le", store=True, copy=False, index=True)
    intervention_started_on = fields.Datetime(string="Intervention démarrée le", store=True, copy=False, index=True)
    intervention_finished_on = fields.Datetime(string="Intervention terminée le", store=True, copy=False, index=True)
    intervention_report_received_on = fields.Datetime(string="Rapport d'intervention reçu le", store=True, copy=False)
    intervention_closed_on = fields.Datetime(string="Intervention clôturée le", store=True, copy=False, index=True)
    intervention_invoiced_on = fields.Datetime(string="Intervention facturée le", store=True, copy=False)

    amount_total_invoiced = fields.Monetary(
        compute='_compute_amount_total_invoiced', store=True, precompute=False, string='Total facturé',compute_sudo=True
    )
    amount_total_remaining_to_invoice = fields.Monetary(
        compute='_compute_amount_total_remaining_to_invoice', store=True, precompute=False, string='Reste à facturer',compute_sudo=True
    )

    @api.depends('invoice_ids.amount_total','invoice_ids.state', 'order_line.invoice_lines')
    def _compute_amount_total_invoiced(self):
        for sale in self:
            sale.amount_total_invoiced = sum(
                - inv.amount_total if inv.move_type == 'out_refund' else inv.amount_total for inv in sale.mapped('invoice_ids').filtered(lambda inv: inv.state == 'posted')
            )

    @api.depends('amount_total','order_line.price_subtotal', 'order_line.price_total','amount_total_invoiced','invoice_ids.amount_total','invoice_ids.state', 'order_line.invoice_lines')
    def _compute_amount_total_remaining_to_invoice(self):
        for sale in self:
            sale.amount_total_remaining_to_invoice = sale.amount_total  - sale.amount_total_invoiced

    @api.depends('user_id')
    def _compute_can_edit_initial_margin_forecast(self):
        margin_group = False
        if self.env.user.has_group('hm_sale.group_initial_margin_user'):
            margin_group = True
        for record in self:
            record.can_edit_initial_margin_forecast = margin_group

    @api.onchange('state2')
    def onchange_validity_date(self):
        if self.state2 and self.state2 == "invoiced":
            self.hm_validity_date_state2 = datetime.datetime.today()

    # TODO: debug if still need this method
    def request_review_google_rating(self):
        mail_mail_obj = self.env['mail.mail']
        template_id = self.env.ref('hm_sale.hm_mail_template_request_review_on_google_after_execution')
        check_date_validity = datetime.datetime.today() + relativedelta.relativedelta(days=-2)
        check_six_month_date = datetime.datetime.today() + relativedelta.relativedelta(days=-180)
        so_ids = self.env['sale.order'].search([("state2", "=", "invoiced"), ("hm_validity_date_state2", "=", check_date_validity)])
        # TODO
        # The sender is the current user ??
        sender_partner_id = self.env.user.partner_id
        for so_id in so_ids:
            if so_id.partner_id.email and ((not so_id.partner_id.hm_last_customer_review_request_on) or (
                    so_id.partner_id.hm_last_customer_review_request_on < check_six_month_date)):
                # Compose email
                values = template_id.generate_email(so_id.id, fields=None)
                values['email_to'] = so_id.partner_id.email
                values['email_from'] = sender_partner_id.email
                values['res_id'] = so_id.id
                if not values['email_to'] and not values['email_from']:
                    pass
                msg_id = mail_mail_obj.create(values)
                if msg_id:
                    mail_mail_obj.send(msg_id)
                    # Update last customer review request on
                    so_id.partner_id.hm_last_customer_review_request_on = datetime.datetime.now()
                    self.env.cr.commit()

    def generate_work_report(self):
        attachment = False
        if self.wr_id:
            report_xml_id = 'hm_sale.hm_action_work_report'
            pdf = self.env['ir.actions.report']._render_qweb_pdf(report_xml_id, self.id)[0]
            # pdf = base64.b64encode(pdf).decode()
            attachment = self.env['ir.attachment'].create({
                'name': "Rapport d'intervention %s.pdf" % self.name,
                'datas': base64.b64encode(pdf),
                'type': 'binary',
                'res_model': self._name,
                'res_id': self.id,
            })
        return attachment

    @api.depends("hm_so_manager_id", "user_id")
    def _calcul_hm_responsible(self):
        for rec in self:
            hm_responsible_id = False
            if rec.hm_so_manager_id:
                hm_responsible_id = rec.hm_so_manager_id.id
            elif rec.user_id:
                hm_responsible_id = rec.user_id.id
            rec.hm_responsible_id = hm_responsible_id

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.hm_so_manager_theoretical_workload_in_minutes < 0:
                raise ValidationError(
                    'la valeur du Charge de gestion estimée en minutes doit être supérieure ou égale à 0')
            else:
                if order.sale_order_template_id and order.sale_order_template_id.hm_so_manager_theoretical_workload_in_minutes != 0:
                    order.hm_so_manager_theoretical_workload_in_minutes = order.sale_order_template_id.hm_so_manager_theoretical_workload_in_minutes
                    order.hm_so_manager_workload_points = order.sale_order_template_id.hm_so_manager_workload_points
                else:
                    order.hm_so_manager_theoretical_workload_in_minutes = order.hm_work_category.hm_so_manager_theoretical_workload_in_minutes
                    order.hm_so_manager_workload_points = order.hm_work_category.hm_so_manager_workload_points
        return res

    def generate_intervention_proposal(self):
        icr_text = ''
        proposal = False
        emergency_degrees = ''
        customer_availability_text = ''
        customer_availability = ''
        if self.icr_id:
            icr_text = """- Détail: """
            if self.icr_id.body_text:
                icr_text += """%s\n""" % (self.icr_id.body_text)

            for picture in self.icr_id.picture_icr_info_ids.filtered(lambda x: x.caption):
                icr_text += """%s\n""" % picture.caption

        if self.emergency_degrees_id and self.emergency_degrees_id.name:
            emergency_degrees = """- Délai d'intervention: %s \n""" % (self.emergency_degrees_id.name)

        if self.customer_availability_id:

            # Lundi 24/04 entre 08:00 et 14:00
            dayofweek = {
                '0': 'Lundi',
                '1': 'Mardi',
                '2': 'Mercredi',
                '3': 'Jeudi',
                '4': 'Vendredi',
                '5': 'Samedi',
                '6': 'Dimanche'
            }
            for availability in self.customer_availability_id.cust_availability_ids:
                hour_from_minutes = round((availability.hour_from - int(availability.hour_from)) * 60)
                hour_from_str = f"{int(availability.hour_from):02d}:{hour_from_minutes:02d}"
                hour_from_dt = datetime.datetime.strptime(hour_from_str, "%H:%M")

                hour_to_minutes = round((availability.hour_to - int(availability.hour_to)) * 60)
                hour_to_str = f"{int(availability.hour_to):02d}:{hour_to_minutes:02d}"
                hour_to_dt = datetime.datetime.strptime(hour_to_str, "%H:%M")

                customer_availability_text += """%s %s entre %s et %s\n""" % (
                dayofweek[availability.dayofweek], availability.date.strftime('%d/%m'), hour_from_dt.strftime('%H:%M'),
                hour_to_dt.strftime('%H:%M'))

            customer_availability = """- Disponibilités du client:\n%s\n""" % (customer_availability_text)

        proposal = """🆕 👷‍♀️ Nouvelle demande d'intervention HeatMe 🆕👷‍♀️:%s \n \n- %s \n- Lieu: %s \n""" % (self.name,
                                                                                                             self.hm_work_object or '',
                                                                                                             self.partner_shipping_id and self.partner_shipping_id.zip + ' ' + self.partner_shipping_id.city or '')
        proposal += emergency_degrees
        proposal += customer_availability
        proposal += icr_text

        proposal += """\nPeux-tu prendre en charge cette intervention? Si oui, merci de me proposer une date et heure estimative. 👍 """
        # pyperclip.copy(proposal)

        return proposal

    @api.depends('hm_premium_ids.hm_subtotal_prime')
    def _compute_hm_sum_premium_total(self):
        for order in self:
            sum_premium_total = 0.0
            for line in order.hm_premium_ids:
                sum_premium_total += line.hm_subtotal_prime
            order.hm_sum_premium_total = sum_premium_total
            order.hm_amount_total_line_premium = sum_premium_total

    @api.depends('hm_sum_premium_total', 'amount_total')
    def _compute_hm_amount_total_with_premium(self):
        for order in self:
            amount_total = order.amount_total or 0.0
            hm_sum_premium_total = order.hm_sum_premium_total or 0.0
            if amount_total >= hm_sum_premium_total:
                order.hm_amount_total_with_premium = amount_total - hm_sum_premium_total
            else:
                order.hm_amount_total_with_premium = 0.0

    def _compute_commande_lie_count(self):
        results = self.env['purchase.order'].read_group([('hm_so_lie', 'in', self.ids)], ['hm_so_lie'], 'hm_so_lie')
        dic = {}
        for x in results:
            dic[x['hm_so_lie'][0]] = x['hm_so_lie_count']
        for record in self:
            record['hm_commande_lie_count'] = dic.get(record.id, 0)

    def _compute_po_lines_count(self):
        results = self.env['purchase.order.line'].read_group([('sale_order_id', 'in', self.ids)], ['sale_order_id'],
                                                             'sale_order_id')
        dic = {}
        for x in results:
            dic[x['sale_order_id'][0]] = x['sale_order_id_count']
        for record in self:
            record['hm_po_lines_count'] = dic.get(record.id, 0)

    def _compute_margin_rate(self):
        for sale in self:
            if sale.margin and sale.amount_untaxed:
                sale.margin_rate = sale.margin / sale.amount_untaxed
            else:
                sale.margin_rate = 0

    def _compute_check_purchase_ids(self):
        for order in self:
            purchases = self.env['purchase.order'].search(
                [('hm_so_lie', '=', order.id), ('partner_id.hm_technician', '=', False),
                 ('partner_id.name', 'not ilike', 'emport'), ('state', '!=', 'draft')])
            if purchases:
                order.check_purchase_ids = True
            else:
                order.check_purchase_ids = False

    def set_intervention_deadline_date(self):
        for record in self:
            res = False
            delay_to_plan_intervention = record.emergency_degrees_id.delay_to_plan_intervention
            brussels_timezone = pytz.timezone('Europe/Brussels')
            utc_timezone = pytz.timezone('UTC')
            if record.emergency_degrees_id:
                if delay_to_plan_intervention > 0:
                    today_with_xdelay = datetime.datetime.now() + timedelta(days=delay_to_plan_intervention)
                    if record.customer_availability_id.cust_availability_ids:
                        max_customer_availability = max(
                            record.customer_availability_id.cust_availability_ids.mapped('date_to'))
                        if max_customer_availability.date() > today_with_xdelay.date():
                            res = max_customer_availability
                        else:
                            res = today_with_xdelay
                    else:
                        res = today_with_xdelay
                    res = brussels_timezone.localize(res)  # Assuming res is in Brussels timezone
                    res = res.replace(hour=17, minute=0, second=0, microsecond=0)  # Set hour to 17:00

                if delay_to_plan_intervention == 0:
                    date_order = self.date_order
                    if date_order:
                        signed_on_brussels = date_order.astimezone(brussels_timezone)
                        signed_on_time = signed_on_brussels.time()
                        if signed_on_time < time(10, 0) and date_order.date() == datetime.datetime.now().date():
                            res = signed_on_brussels.replace(hour=21, minute=0, second=0, microsecond=0)

                        else:
                            tomorrow_with_xdelay = datetime.datetime.now() + timedelta(days=1)
                            res = brussels_timezone.localize(
                                tomorrow_with_xdelay)  # Assuming res is in Brussels timezone
                            res = res.replace(hour=17, minute=0, second=0, microsecond=0)  # Set hour to 17:00

                if res:
                    res = res.astimezone(utc_timezone)  # Convert to UTC timezone
                    res = res.replace(tzinfo=None)
            else:
                if record.customer_availability_id and record.customer_availability_id.cust_availability_ids:
                    res = max(record.customer_availability_id.cust_availability_ids.mapped('date_to'))
            record.intervention_deadline_date = res

    @api.depends('invoice_count')
    def _get_so_invoice_count(self):
        for rec in self:
            rec.so_invoice_count = rec.invoice_count

    @api.model
    def update_so_invoice_count(self):
        sale_ids = self.search([])
        sale_ids._get_so_invoice_count()

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
        action = self.env.ref('calendar.action_calendar_event').read()[0]
        partner_ids = self.env.user.partner_id.ids
        location = str(self.lieu_valide(self.property_id.street)) + str(
            self.lieu_valide(self.property_id.city)) + str(self.lieu_valide(self.property_id.zip)) + str(
            self.lieu_valide(self.property_id.country_id.name))
        if self.partner_id:
            partner_ids.append(self.partner_id.id)

        name = self.name + ' - Visite technicien HeatMe @'
        if self.property_id and self.property_id.street:
            name += self.property_id.street
        if self.property_id and self.property_id.street2:
            name += ' ' + self.property_id.street2

        action['context'] = {
            'default_partner_id': self.partner_id and self.partner_id.id or False,
            'default_partner_ids': partner_ids,
            'default_contact_lieu': self.partner_onsite_id and self.partner_onsite_id.id or False,
            'default_location': location,
            'default_street2': self.property_id and self.property_id.street2 or '',
            'default_team_id': self.team_id and self.team_id.id or False,
            'default_name': name,
            'default_sale_order_id': self.id,
        }
        action['domain'] = [('sale_order_id', '=', self.id)]
        return action

    # Set the current user as the default user
    @api.model
    def default_get(self, fields):
        res = super(SaleOrder, self).default_get(fields)
        res['user_id'] = self.env.user
        return res

    # TODO : delete not used!
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            # 'partner_invoice_id': addr['invoice'],
            # 'partner_shipping_id': addr['delivery'],
            # 'user_id': self.env.user
        }
        if not self.user_id:
            values['user_id'] = self.env.user

        if self.env['ir.config_parameter'].sudo().get_param(
                'sale.use_sale_note') and self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note
        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id

        if self.env.context.get("default_partner_id") and not self.partner_id:
            partner_id = self.env['res.partner'].browse(self.env.context.get("default_partner_id"))
            values['partner_id'] = partner_id.id
            values[
                'payment_term_id'] = partner_id.property_payment_term_id and partner_id.property_payment_term_id.id or False
        self.update(values)

    @api.onchange('partner_invoice_id')
    def onchange_partner_invoice_id(self):
        values = {
            'pricelist_id': self.partner_invoice_id.property_product_pricelist and self.partner_invoice_id.property_product_pricelist.id or False,
        }
        self.update(values)

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if res:
            res.update({
                'sale_order_id': self.id,
                'partner_shipping_id': self.property_id.partner_id and self.property_id.partner_id.id or self.partner_shipping_id.id,
            })
        return res

    # TODO: check if still need it
    def _activity_cancel_on_purchase(self):
        """ If some SO are cancelled, we need to put an activity on their generated purchase. If sale lines of
            differents sale orders impact different purchase, we only want one activity to be attached.
        """
        purchase_to_notify_map = {}  # map PO -> recordset of SOL as {purchase.order: set(sale.orde.liner)}
        purchase_order_lines = self.env['purchase.order.line'].search(
            [('sale_line_id', 'in', self.mapped('order_line').ids), ('state', '!=', 'cancel')])
        for purchase_line in purchase_order_lines:
            purchase_to_notify_map.setdefault(purchase_line.order_id, self.env['sale.order.line'])
            purchase_to_notify_map[purchase_line.order_id] |= purchase_line.sale_line_id
        for purchase_order, sale_order_lines in purchase_to_notify_map.items():
            user_id = purchase_order.user_id.partner_id.id or self.env.uid,
            author_id = user_id
            model = purchase_order._name
            res_id = purchase_order.id
            message_type = 'notification'
            date = datetime.date.today()
            render_context = {
                'sale_orders': sale_order_lines.mapped('order_id'),
                'sale_order_lines': sale_order_lines,
            }
            Body = self.env.ref('sale_purchase.exception_purchase_on_sale_cancellation',
                                raise_if_not_found=False).render(render_context, engine='ir.qweb',
                                                                 minimal_qcontext=True)
            vals = {'author_id': author_id, 'model': model, 'res_id': res_id, 'message_type': message_type,
                    'date': date, 'body': Body}
            message_object = self.env['mail.message'].create(vals)


    def run_create_icr_automatically(self):
        body_parts = [self.hm_tech_report_summary, self.hm_tech_report_improvement_suggestions,
                      self.hm_tech_report_internal_notes]
        body_text = '\n'.join(part for part in body_parts if part)
        res_ids = self.env['hm.picture.so.info'].search(
            [('hm_so_id', '=', self.id), ('hm_picture_library_id.is_technicien_report_picture', '=', True)])

        icr_id = self.env['hm.icr'].create({
            "body_text": body_text,
            "hm_related_lead_id": self.opportunity_id.id,
        })
        for res in res_ids:
            if res.hm_picture_library_id.is_client_signature:
                continue
            else:
                self.env['hm.picture.icr.info'].create({
                    "hm_picture_library_id": res.hm_picture_library_id.id,
                    "caption": res.caption,
                    "icr_id": icr_id.id
                })
        return icr_id or False

    def create_downpayment(self):
        # acompte_product = self.env.ref('__export__.product_product_35_77a6329a')
        acompte_product = self.env['product.product'].browse(35)
        has_downpayment_invoice = False
        has_downpayment_invoice = any(
            line.product_id == acompte_product and line.quantity > 0 for line in self.invoice_ids.invoice_line_ids)
        if self.amount_total >= self.partner_id.min_amount_to_ask_deposit and not has_downpayment_invoice:
            # TODO : Factures clients with id 1(no ref)
            context = {
                'active_model': 'sale.order',
                'active_ids': [self._origin.id],
                'active_id': self._origin.id,
                'default_journal_id': 1,
            }
            downpayment = self.env['sale.advance.payment.inv'].with_context(context).create({
                'advance_payment_method': 'percentage',
                'amount': 40,
            })

            action_invoice = downpayment.with_context(open_invoices=True).create_invoices()
            invoice_id = action_invoice['res_id']
            if not invoice_id:
                posted_invoice_res_ids = self.invoice_ids.filtered(lambda inv: inv.state == 'posted')
                invoice_id = self.env['account.move'].search(expression.AND([action_invoice['domain'], [('id', 'not in', posted_invoice_res_ids.ids)]]), order="id desc", limit=1).id
            downpayment_invoice = self.env['account.move'].browse(invoice_id)
            # 3 jours (acomptes) = id 19
            downpayment_invoice.invoice_payment_term_id = 19
            downpayment_invoice.action_post()
            context = {
                'active_model': 'account.move',
                'active_ids': [invoice_id],
                'active_id': invoice_id,
            }
            # debug later template downpayment_invoice
            template = self.env.ref('account.email_template_edi_invoice', False)
            email_downpayment = self.env['account.invoice.send'].with_context(context).create({
                "is_email": True,
                "snailmail_is_letter": False,
                "model": 'account.move',
                "res_id": invoice_id,
                "composition_mode": 'comment',
                "template_id": template and template.id,
                "invoice_ids": [(6, 0, [invoice_id])]})
            email_downpayment.onchange_is_email()
            email_downpayment.onchange_template_id()
            email_downpayment.send_and_print_action()

            # Add the salesperson and sales order manager as followers to the invoice
            vendor_id = self.user_id
            hm_so_manager_id = self.hm_so_manager_id
            if vendor_id:
                downpayment_invoice.message_subscribe(partner_ids=[(vendor_id.partner_id.id)])
            if hm_so_manager_id:
                downpayment_invoice.message_subscribe(partner_ids=[(hm_so_manager_id.partner_id.id)])
            self.state2 = 'deposit_to_receive'
        else:
            self.state2 = 'to_organize'

    def has_boiler_certificate(self):
        boiler_certificate_ids = self.env['ir.attachment'].search([
            ('res_id', '=', self.id),
            ('res_model', '=', 'sale.order'),
            ('hm_document_type', '=', 'boiler_certificate')
        ])
        return bool(boiler_certificate_ids)

    def decode_base64_attachments(self, data):
        updated_data = []
        for title, b64_data in data:
            decoded_data = base64.b64decode(b64_data)
            updated_data.append((title, decoded_data))
        return updated_data

    # TODO: v18, no need for this custom dev; we can call multi attachments for 1 mail template
    def generate_and_send_work_report_with_boiler_certificate_by_email(self):
        mail_template = self.env.ref('hm_sale.hm_mail_template_intervention_report')
        boiler_certificate = self.env['ir.attachment'].search([
            ('res_id', '=', self.id),
            ('res_model', '=', 'sale.order'),
            ('hm_document_type', '=', 'boiler_certificate')
        ])

        email_fields = ['subject', 'body_html', 'email_from', 'email_to', 'partner_to',
                        'email_cc', 'reply_to', 'attachment_ids', 'mail_server_id']
        email_values = mail_template.generate_email(self.id, fields=email_fields)

        partner_ids = email_values.get('partner_ids', [])
        author_id = self.env.user.partner_id.id

        if self.hm_so_manager_id:
            partner_ids += self.hm_so_manager_id.partner_id.ids
            author_id = self.hm_so_manager_id.partner_id.id

        try:
            self.message_post(
                body=email_values['body_html'],
                email_from=email_values['email_from'],
                email_to=email_values['email_to'],
                email_cc=email_values['email_cc'],
                reply_to=email_values['reply_to'],
                subject=email_values['subject'],
                partner_ids=partner_ids,
                message_type='comment',
                attachments=self.decode_base64_attachments(email_values.get('attachments', [])),
                attachment_ids=boiler_certificate.ids,
                subtype_id=self.env.ref('mail.mt_comment').id,
                subtype_xmlid='mail.mt_comment',
                author_id=author_id
            )
            self.work_report_sent_to_client = True
        except Exception as e:
            _logger.error(f"Error sending work report email: {e}")

    # ******************************************* Write ***************************************************

    def write(self, vals):
        # Capture the current context and initial states
        context = self.env.context
        is_state2_update = 'state2' in vals
        new_state2 = vals.get('state2')
        new_state = vals.get('state')
        current_state2 = self.state2

        # Call the super method to apply `vals`
        res = super(SaleOrder, self).write(vals)

        # Handle `state2` status changes and report requirements
        if is_state2_update and current_state2 == 'report_sent' and new_state2 in ['to_invoice', 'invoiced']:
            self._check_and_handle_intervention_report(context)

        # Handle fiscal_position_id changes and force line updates
        if 'fiscal_position_id' in vals:
            self.action_update_taxes()

        # Process changes based on `state2` status
        if new_state2:
            self._handle_state2_changes(new_state2, current_state2)

        # Handle `state` changes and related updates
        if new_state:
            self._handle_state_changes(new_state)

        # Update technician-related fields if relevant
        if 'hm_imputed_technician_id' in vals:
            self._update_purchase_orders(vals['hm_imputed_technician_id'])

        # Update SO followers if manager changes
        if 'hm_so_manager_id' in vals:
            self._update_so_followers()

        # Set intervention deadline if certain fields are updated
        if any(key in vals for key in ['emergency_degrees_id', 'customer_availability_id']) or new_state == 'sale':
            self.set_intervention_deadline_date()

        # Update emergency_degrees_id if an emergency degree exists for the product
        product_ids = self.order_line.filtered(lambda line: line.product_uom_qty > 0).mapped('product_id.id')
        emergency_degree_from_product_lines_id = self.env['order.emergency.degrees'].search([('product_ids', 'in', product_ids)], order='sequence',limit=1)
        if emergency_degree_from_product_lines_id:
            if not self.emergency_degrees_id or bool(emergency_degree_from_product_lines_id.sequence < self.emergency_degrees_id.sequence):
                self.emergency_degrees_id = emergency_degree_from_product_lines_id.id

        return res

    def _check_and_handle_intervention_report(self, context):
        """Ensure intervention report requirements are met before changing `state2`."""
        if not self.work_report_sent_to_client:
            if self.wr_id:
                self.generate_and_send_work_report_with_boiler_certificate_by_email()
            else:
                boiler_certificates_ids = self.env['ir.attachment'].search([
                    ('res_id', '=', self.id),
                    ('res_model', '=', 'sale.order'),
                    ('hm_document_type', '=', 'boiler_certificate')
                ])
                if boiler_certificates_ids:
                    raise UserError(_("Une ou plusieurs attestations ont été associées à cette commande.\n👉 Veuillez compléter le rapport d'intervention afin de pouvoir clôturer la commande."))
                elif not self.allow_closing_without_report:
                    raise UserError(_("Veuillez compléter le rapport d'intervention ou cocher le champ 'Autoriser la clôture sans rapport d'intervention' afin de pouvoir clôturer cette commande."))

    def _handle_state2_changes(self, new_state2, current_state2):
        """Processes additional actions based on `state2` changes."""
        date_now = datetime.datetime.now()
        if self.state2 == 'report_sent' and self.sale_order_template_id.hm_work_category.create_icr_automatically:
            self.icr_id = self.run_create_icr_automatically()
            self.state2 = 'invoiced'

        if new_state2 == 'invoiced' and not self.hm_so_invoiced_date:
            self.hm_so_invoiced_date = datetime.date.today()

        if current_state2 =='deposit_to_receive' and new_state2 == 'to_organize' and not self.deposit_received_on:
            self.deposit_received_on = date_now
        elif new_state2 == 'planned' and not self.intervention_planned_on:
            self.intervention_planned_on = date_now
        elif current_state2 =='planned' and new_state2 == 'tech_on_the_way' and not self.tech_on_the_way_since:
            self.tech_on_the_way_since = date_now
        elif new_state2 == 'in_progress' and not self.intervention_started_on:
            self.intervention_started_on = date_now
        elif new_state2 == 'report_to_send':
            self.intervention_finished_on = date_now
        elif current_state2 in ['planned', 'tech_on_the_way', 'in_progress', 'paused', 'report_to_send'] and new_state2 == 'report_sent':
            self.intervention_report_received_on = date_now
        elif new_state2 == 'to_invoice' and not self.intervention_closed_on:
            self.intervention_closed_on = date_now
        elif new_state2 == 'invoiced' and not self.intervention_invoiced_on:
            self.intervention_invoiced_on = date_now

    def _handle_state_changes(self, new_state):
        """Manages updates for `state` changes."""
        if new_state == 'sent':
            self._handle_opportunity_updates('crm.stage_lead3', 'activity_as_complete_opportunity_sent')
            self.sent_on = datetime.datetime.now()

        if new_state in ['sale', 'cancel']:
            if self.opportunity_id.sale_amount_total > 0.0:
                self._evaluate_and_update_opportunity_stage()

            self._complete_offer_activity('activity_as_complete_opportunity_won_lost')

        if new_state == 'sale':
            self.amount_untaxed_at_signature = self.amount_untaxed

    def _evaluate_and_update_opportunity_stage(self):
        """Evaluates whether to move the opportunity to a 'won' stage."""
        confirmed_order = self.opportunity_id.order_ids.filtered(lambda o: o.state == 'sale')
        if confirmed_order:
            check_so = all(
                order.state not in ['draft', 'sent'] or order.amount_untaxed == 0.0
                for order in self.opportunity_id.order_ids
                if order.state != 'sale'
            )

            if check_so:
                self.opportunity_id.stage_id = self.env.ref('crm.stage_lead4').id

    def _handle_opportunity_updates(self, stage_ref, activity_type_xmlid):
        """Updates the opportunity stage and completes relevant activities."""
        if self._can_update_opportunity():
            if stage_ref == 'crm.stage_lead3' and self.opportunity_id.stage_id.id not in [self.env.ref('crm.stage_lead3').id, self.env.ref('crm.stage_lead4').id]:
                self.opportunity_id.stage_id = self.env.ref(stage_ref)
            self._complete_offer_activity(activity_type_xmlid)

    def _complete_offer_activity(self, activity_type_xmlid):
        """Completes specified activities for the opportunity."""
        activity_ids = self.env['mail.activity.type'].search([(activity_type_xmlid, '=', True)])
        if activity_ids:
            self.opportunity_id.activity_ids.filtered(
                lambda msg: msg.activity_type_id in activity_ids).action_feedback()

    def _can_update_opportunity(self):
        """Determines if the opportunity can be updated based on team settings."""
        return (
                self.opportunity_id and
                self.opportunity_id.team_id and
                self.opportunity_id.team_id.hm_update_opportunity_status
        )

    def _update_purchase_orders(self, technician_id):
        """Updates related purchase orders with the specified technician."""
        if technician_id:
            technician_purchases = self.env['purchase.order'].search([
                ('po_type', '=', 'po_technicien'),
                ('hm_so_lie', '=', self.id),
                ('state', '!=', 'purchase')
            ])
            for purchase in technician_purchases:
                if purchase.order_line.filtered(lambda line: line.product_id.seller_ids and line.product_id.seller_ids[0].partner_id.name == "Technicien à imputer"):
                    purchase.write({'partner_id': technician_id})
                    purchase.onchange_partner_id()

    # **********************************************************************************************

    def _has_group_sale_manager_for_point_of_management(self):
        is_sale_manager = self.env.user.has_group('hm_sale.group_show_workload_points_in_minutes')
        for so in self:
            so.has_group_sale_manager_for_point_of_management = False
            if is_sale_manager:
                so.has_group_sale_manager_for_point_of_management = True

    @api.depends('state', 'state2')
    def _has_group_sale_manager(self):
        is_sale_manager = self.env.user.has_group('sales_team.group_sale_manager')
        for so in self:
            so.has_group_sale_manager = True
            if so.state in ['done', 'cancel']:
                so.has_group_sale_manager = False
            elif so.state2 == 'invoiced':
                so.has_group_sale_manager = False
            elif is_sale_manager and so.state2 == 'to_invoice':
                so.has_group_sale_manager = True
            elif not is_sale_manager and so.state2 == 'to_invoice':
                so.has_group_sale_manager = False

    @api.depends('state2', 'amount_total_invoiced', 'amount_total')
    def _get_greater(self):
        for so in self:
            if (so.state2 and so.state2 == 'to_invoice') and (so.amount_total_invoiced >= so.amount_total):
                so.is_greater = True
            else:
                so.is_greater = False

    # ************************************************************************************

    def is_holiday(self, date):
        tech_calendar_id = self.env['resource.calendar'].browse(5)
        tech_today_calendar_id = tech_calendar_id.global_holiday_ids.filtered(lambda x: x.holiday_date == date.date())
        if tech_today_calendar_id:
            return True
        else:
            return False

    def compute_po_deadline(self, days, date_now=None):

        if days == 0.5:
            hours = 4
        elif days == 1:
            hours = 9
        elif days == 2:
            hours = 18

        # *** Get technician calendar
        tech_today_calendar_id = self.get_date_by_tech_calendar(date_now)
        tech_today_hour_to = tech_today_calendar_id['tech_to_hour']
        tech_today_min_to = tech_today_calendar_id['tech_to_min']

        tech_today_hour_to = date_now.replace(hour=int(tech_today_hour_to), minute=tech_today_min_to)

        # check if the technician still working now(based on calendar)
        if date_now > tech_today_hour_to:

            next_date_day = date_now + timedelta(days=1)

            while self.check_date_weekend_or_holidays(next_date_day):
                next_date_day += timedelta(days=1)

            tech_today_calendar_id = self.get_date_by_tech_calendar(next_date_day)
            tech_nextday_hour_from = tech_today_calendar_id['tech_from_hour']
            tech_nextday_min_from = tech_today_calendar_id['tech_from_min']

            next_date_day = next_date_day.replace(hour=tech_nextday_hour_from, minute=tech_nextday_min_from)
            new_mints = 0
            new_hours = hours
            po_date_deadline = next_date_day + timedelta(hours=new_hours, minutes=new_mints)

        else:
            # calcul the days/hours diff between two dates and added to today
            po_date_deadline = self.get_date_by_working_hours(date_now, hours)

        return po_date_deadline

    def check_date_by_working_hours(self, date_now):
        tech_calendar_id = self.env['resource.calendar'].browse(5)
        now_weekday = date_now.weekday()
        tech_today_calendar_id = tech_calendar_id.attendance_ids.filtered(lambda x: x.dayofweek == str(now_weekday))

        tech_today_from_hour = int(str(tech_today_calendar_id.hour_from).split('.')[0])
        tech_today_from_min = int(float('0.' + str(tech_today_calendar_id.hour_from).split('.')[1]) * 60)

        tech_today_hour_to = int(str(tech_today_calendar_id.hour_to).split('.')[0])
        tech_today_min_to = int(float('0.' + str(tech_today_calendar_id.hour_to).split('.')[1]) * 60)

        tech_today_from = date_now.replace(hour=int(tech_today_from_hour), minute=tech_today_from_min, second=0)
        tech_today_to = date_now.replace(hour=int(tech_today_hour_to), minute=tech_today_min_to, second=0)

        if tech_today_calendar_id and tech_today_from <= date_now and date_now <= tech_today_to:
            return True
        else:
            return False

    def check_date_weekend_or_holidays(self, date_now):
        if self.is_holiday(date_now) or date_now.weekday() in (5, 6):
            return True
        else:
            return False

    def get_date_by_tech_calendar(self, date_now):
        tech_calendar_id = self.env['resource.calendar'].browse(5)
        tech_today_calendar_id = tech_calendar_id.attendance_ids.filtered(
            lambda x: x.dayofweek == str(date_now.weekday()))

        tech_from_hour = int(str(tech_today_calendar_id.hour_from).split('.')[0])
        tech_from_min = int(float('0.' + str(tech_today_calendar_id.hour_from).split('.')[1]) * 60)

        tech_to_hour = int(str(tech_today_calendar_id.hour_to).split('.')[0])
        tech_to_min = int(float('0.' + str(tech_today_calendar_id.hour_to).split('.')[1]) * 60)

        res = {
            'tech_from_hour': tech_from_hour,
            'tech_from_min': tech_from_min,
            'tech_to_hour': tech_to_hour,
            'tech_to_min': tech_to_min
        }
        return res

    def get_date_by_working_hours(self, date_now, working_hours):

        tech_today_calendar_id = self.get_date_by_tech_calendar(date_now)
        tech_today_hour_to = tech_today_calendar_id['tech_to_hour']
        tech_today_min_to = tech_today_calendar_id['tech_to_min']

        tech_today_hour_to = date_now.replace(hour=int(tech_today_hour_to), minute=tech_today_min_to)

        hours_to_add = 0
        minutes_to_add = 0
        working_hour_still_for_today = tech_today_hour_to.hour - date_now.hour

        if working_hour_still_for_today >= 0 and working_hour_still_for_today < working_hours:
            next_date_day = date_now + timedelta(days=1)

            while self.check_date_weekend_or_holidays(next_date_day):
                next_date_day += timedelta(days=1)

            working_hour_for_nextday = working_hours - working_hour_still_for_today

            if tech_today_hour_to.minute != date_now.minute and tech_today_hour_to.minute:
                working_hour_for_nextday = working_hour_for_nextday - 1
                minutes_to_add = 60 - tech_today_hour_to.minute

            while working_hour_for_nextday > 0:
                if working_hour_for_nextday - 9 >= 0:
                    working_hour_for_nextday = working_hour_for_nextday - 9
                    next_date_day = next_date_day + timedelta(days=1)
                    while self.check_date_weekend_or_holidays(next_date_day):
                        next_date_day += timedelta(days=1)
                else:
                    hours_to_add = working_hour_for_nextday
                    working_hour_for_nextday = working_hour_for_nextday - 9

            tech_today_calendar_id = self.get_date_by_tech_calendar(next_date_day)
            next_date_day_hour_from = tech_today_calendar_id['tech_from_hour']

            if hours_to_add > 0:
                date_now = next_date_day.replace(hour=next_date_day_hour_from)
                date_now = date_now + timedelta(hours=hours_to_add, minutes=minutes_to_add)
            else:
                date_now = next_date_day

        else:
            hours_to_add = working_hours
            date_now = date_now + timedelta(hours=hours_to_add)

        return date_now

    def get_previous_date_by_working_hours(self, date_now, working_hours):

        tech_today_calendar_id = self.get_date_by_tech_calendar(date_now)
        tech_today_hour_from = tech_today_calendar_id['tech_from_hour']
        tech_today_min_from = tech_today_calendar_id['tech_from_min']

        tech_today_hour_from = date_now.replace(hour=int(tech_today_hour_from), minute=tech_today_min_from)

        hours_to_cut = 0
        minutes_to_cut = 0

        working_hours_for_today = tech_today_hour_from.hour - date_now.hour

        working_hour_for_previous_day = working_hours + working_hours_for_today
        if abs(working_hours_for_today) < working_hours:
            previous_date_day = date_now - timedelta(days=1)

        if working_hours_for_today == 0:
            previous_date_day = date_now - timedelta(days=1)
            working_hour_for_previous_day = working_hour_for_previous_day - 9
            while self.check_date_weekend_or_holidays(previous_date_day):
                previous_date_day = previous_date_day - timedelta(days=1)

        while self.check_date_weekend_or_holidays(previous_date_day):
            previous_date_day = previous_date_day - timedelta(days=1)

        while working_hour_for_previous_day > 0:
            if working_hour_for_previous_day - 9 >= 0:
                working_hour_for_previous_day = working_hour_for_previous_day - 9
                previous_date_day = previous_date_day - timedelta(days=1)
                while self.check_date_weekend_or_holidays(previous_date_day):
                    previous_date_day = previous_date_day - timedelta(days=1)
            else:
                hours_to_cut = working_hour_for_previous_day
                working_hour_for_previous_day = working_hour_for_previous_day - 9

        date_now = previous_date_day
        return date_now

    def update_po_deadline(self, date_now=False):
        brussels_timezone = pytz.timezone('Europe/Brussels')

        # TODO delete after test
        # date_now = datetime.datetime.strptime('2022-10-21 14:00:00', '%Y-%m-%d %H:%M:%S')
        # date_now = brussels_timezone.localize(date_now)

        for rec in self.purchase_ids.sudo():
            res = False
            if rec.hm_so_lie and rec.hm_so_lie.state2 == "planned" and rec.hm_so_lie.commitment_date:

                commitment_date = rec.hm_so_lie.commitment_date.astimezone(pytz.timezone(brussels_timezone.zone))

                if not date_now:
                    date_now = datetime.datetime.now()
                    date_now = date_now.astimezone(pytz.timezone(brussels_timezone.zone))

                # Heures ouvrables
                if not self.check_date_by_working_hours(date_now):
                    date_now = date_now + timedelta(days=1)

                    while self.check_date_weekend_or_holidays(date_now):
                        date_now += timedelta(days=1)

                    tech_today_calendar_id = self.get_date_by_tech_calendar(date_now)
                    tech_today_from_hour = tech_today_calendar_id['tech_from_hour']
                    tech_today_from_min = tech_today_calendar_id['tech_from_min']

                    next_date = date_now.replace(hour=tech_today_from_hour, minute=tech_today_from_min)
                    date_now = next_date

                working_hours_18 = self.get_date_by_working_hours(date_now, 18)
                working_hours_36 = self.get_date_by_working_hours(date_now, 36)

                # # si l'intervention est programmée (= date de livraison sur le SO) dans les prochaines 18h ouvrables: Now + 4h ouvrables
                if commitment_date <= working_hours_18:
                    _logger.info('**** SO / Case 1 : OK')
                    _logger.info('**** commitment_date : %s ' % commitment_date)
                    _logger.info('**** working_hours_18 : %s ' % working_hours_18)

                    res = self.compute_po_deadline(days=0.5, date_now=date_now)

                # # # si l'intervention est programmée au-délà de 18h ouvrables: Latest(Now + 4h ouvrables, Date et heure d'intervention - 18h ouvrables)
                elif (working_hours_18 < commitment_date) and (working_hours_36 > commitment_date):
                    _logger.info('**** SO / Case 2 : OK ')
                    _logger.info('**** commitment_date : %s' % commitment_date)
                    _logger.info('**** working_hours_18 : %s ' % working_hours_18)
                    _logger.info('**** working_hours_36 : %s ' % working_hours_36)

                    po_date_deadline_by_4_working_hours = self.compute_po_deadline(days=0.5, date_now=date_now)
                    previous_po_date_deadline_by_18_working_hours = self.get_previous_date_by_working_hours(
                        commitment_date, 18)
                    res = max(previous_po_date_deadline_by_18_working_hours, po_date_deadline_by_4_working_hours)


                # # # si l'intervention est programmée au-délà de 36h ouvrables: Now + 18h ouvrables
                elif working_hours_36 <= commitment_date:
                    _logger.info('**** SO / Case 3 : OK ')
                    _logger.info('**** commitment_date : %s' % commitment_date)
                    _logger.info('**** working_hours_36 : %s ' % working_hours_36)

                    res = self.compute_po_deadline(days=2, date_now=date_now)

                purchase = rec.browse(rec._origin.id)
                purchase.hm_date_state2_update_deadline = res.astimezone(pytz.timezone('UTC')).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)
                _logger.info('**** result : %s ' % res)
                _logger.info('**** result with format : %s ' % purchase.hm_date_state2_update_deadline)

    # TODO : debug
    @api.onchange('state2', 'commitment_date')
    def onchange_update_related_po_deadline(self):
        if self.state2 == 'planned':
            self.update_po_deadline()

    # ************************************************************************************

    @api.constrains('state2')
    def _check_state2(self):
        state2_po_marchandise = self.env.ref('hm_purchase.purchase_stage5_po_marchandise').id
        state2_po_emport_marchandise = self.env.ref('hm_purchase.purchase_stage2_po_emport_marchandise').id
        state2_po_technicien = self.env.ref('hm_purchase.purchase_stage2_po_technicien').id
        state2_po_commission = self.env.ref('hm_purchase.purchase_stage2_po_commission').id
        for record in self:
            if record.state2 == 'planned':
                if not self.hm_imputed_technician_id or not self.commitment_date:
                    raise UserError(
                        _("Impossible de planifier le devis tant que la date d'intervention et le technicien ne sont pas définis."))
            elif record.state2 == 'to_invoice':
                for po in record.purchase_ids:
                    if po.state not in ['purchase', 'cancel']:
                        raise UserError(
                            _("Impossible de clôturer la commande tant que les PO liés ne sont pas validés ou alors annulés."))
                    elif po.state == 'purchase' and po.stage2_id.id not in [state2_po_marchandise,
                                                                            state2_po_emport_marchandise,
                                                                            state2_po_technicien, state2_po_commission]:
                        raise UserError(
                            _("Impossible de clôturer la commande tant que le statut 2 des PO liés n'est pas validée."))
            elif record.state2 == 'invoiced':
                if record.amount_total_invoiced < record.amount_total:
                    raise UserError(_("❌ Impossible de marquer le bon de commande comme 'Facturé' car le total est supérieur au montant facturé.\n👉 Diminuez le total ou facturez le solde du bon de commande."))
                else:
                    for po in record.purchase_ids:
                        if po.state not in ['purchase', 'cancel']:
                            raise UserError(
                                _("Impossible de valider le devis tant que les PO liés ne sont pas validés ou alors annulés."))
                        elif po.state == 'purchase' and po.stage2_id.id not in [state2_po_marchandise,
                                                                                state2_po_emport_marchandise,
                                                                                state2_po_technicien,
                                                                                state2_po_commission]:
                            raise UserError(
                                _("Impossible de valider le devis tant que le statut 2 des PO liés n'est pas validée."))

    def action_cancel(self):
        state1_po_marchandise = self.env.ref('hm_purchase.purchase_stage1_po_marchandise').id
        state1_po_emport_marchandise = self.env.ref('hm_purchase.purchase_stage1_po_emport_marchandise').id
        state1_po_technicien = self.env.ref('hm_purchase.purchase_stage1_po_technicien').id
        state1_po_commission = self.env.ref('hm_purchase.purchase_stage1_po_commission').id
        state2_po_marchandise = self.env.ref('hm_purchase.purchase_stage6_po_marchandise').id
        state2_po_emport_marchandise = self.env.ref('hm_purchase.purchase_stage3_po_emport_marchandise').id
        state2_po_technicien = self.env.ref('hm_purchase.purchase_stage3_po_technicien').id
        state2_po_commission = self.env.ref('hm_purchase.purchase_stage3_po_commission').id
        for po in self.purchase_ids:
            if po.state not in ['draft', 'cancel']:
                raise UserError(
                    _("Impossible d'annuler le devis tant que les PO liés ne sont pas brouillons ou alors annulés."))
            elif po.stage2_id.id not in [state2_po_marchandise, state2_po_emport_marchandise, state2_po_technicien,
                                         state2_po_commission, state1_po_marchandise, state1_po_emport_marchandise,
                                         state1_po_technicien, state1_po_commission]:
                raise UserError(
                    _("Impossible d'annuler le devis tant que les PO liés ne sont pas brouillons ou alors annulés."))
            else:
                po.button_cancel()

        invoice_ids = self.invoice_ids.filtered(lambda inv: inv.state == 'posted' and (inv.move_type in ['out_invoice', 'out_refund']))
        prec = self.env['decimal.precision'].precision_get('Account')
        if (invoice_ids != [] and float_compare(sum(invoice_ids.mapped('amount_total_signed')), 0.0, precision_digits=prec) != 0):
            raise UserError(
                _("❌ Vous ne pouvez pas annuler ce bon de commande car la somme de ses factures et notes de crédit comptabilisées n'est pas nulle.")
            )

        result = super(SaleOrder, self).action_cancel()
        return result

    @api.model
    def update_state2(self):
        rec_ids = self.search([('state2', '=', 'planned'), ('commitment_date', '<', datetime.datetime.today())])
        for rec in rec_ids:
            rec.write({'state2': 'in_progress'})
        return True

    @api.onchange('sale_order_template_id')
    def onchange_so_template(self):
        for line in self.order_line:
            if line.product_id and line.product_id.product_tmpl_id:
                product_template = line.product_id.product_tmpl_id
                if len(product_template.product_variant_ids) > 1:
                    line.is_variant = True
                else:
                    line.is_variant = False

    @api.onchange('commitment_date')
    def _onchange_commitment_date(self):
        """ Warn if the commitment dates is sooner than the expected date """
        res = super(SaleOrder, self)._onchange_commitment_date()
        if not self.commitment_date:
            self.hm_imputed_technician_id = False
        return res

    @api.model_create_multi
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        for values in vals:
            if 'hm_so_manager_id' in values and values['hm_so_manager_id'] != False:
                res.with_context(new_manager_id=self.hm_so_manager_id.partner_id)._update_so_followers()
            if 'emergency_degrees_id' in values or 'customer_availability_id' in values:
                res.set_intervention_deadline_date()
        return res

    def _update_so_followers(self):
        ctx = self.env.context
        new_manager_id = ctx.get('new_manager_id', False)
        if new_manager_id:
            exist_follower = self.env['mail.followers'].search(
                [
                    ('partner_id', '=', new_manager_id.id),
                    ('res_model', '=', 'sale.order'),
                    ('res_id', '=', self.id),
                ]
            )
            if not exist_follower:
                self.env['mail.followers'].sudo().create(
                    {'partner_id': new_manager_id.id,
                     'res_model': 'sale.order',
                     'res_id': self.id,
                     'subtype_ids': [(6, 0, self.env.ref('mail.mt_comment').ids)]
                     }
                )

    def action_purchase_order_line_view(self):
        action = self.env.ref('hm_purchase.hm_purchase_line_action').read()[0]
        return action

    @api.depends('state2', 'amount_untaxed', 'purchase_ids')
    def _compute_calculated_margin(self):
        for rec in self:
            amount_purchase = 0.0

            for purchase in rec.purchase_ids:
                if purchase.po_type in (
                        'po_marchandise', 'po_emport_marchandise', 'po_technicien') and purchase.state2 == 'invoiced':
                    amount_purchase += purchase.amount_untaxed

            if rec.amount_untaxed > 0:
                rec.hm_calculated_margin = (1 - amount_purchase / rec.amount_untaxed)
            else:
                rec.hm_calculated_margin = 0

    @api.onchange('state2')
    def onchange_check_fields_commitment_date_imputed_technician(self):
        if self.state == 'sale' and self.state2 not in ('deposit_to_receive', 'to_organize'):
            msg = "Veuillez compléter le ou les champ(s) suivant(s) avant de modifier le statut de l'intervention :\n"
            if not self.hm_imputed_technician_id:
                msg += "- Technicien\n"
            if not self.commitment_date:
                msg += "- Date d'intervention\n"
            if msg != "Veuillez compléter le ou les champ(s) suivant(s) avant de modifier le statut de l'intervention :\n":
                raise UserError(_(msg))

    @api.depends('partner_id')
    def _compute_partner_invoice_id(self):
        for order in self:
            if not order.partner_invoice_id:
                order.partner_invoice_id = order.partner_id.address_get(['invoice'])[
                    'invoice'] if order.partner_id else False
            else:
                order.partner_invoice_id = order.partner_invoice_id

    @api.depends('partner_id')
    def _compute_user_id(self):
        for order in self:
            # force the user to always be the current user
            order.user_id = self.env.user

    def action_quotation_send(self):
        self.ensure_one()

        product_without_supplier_ids = self.order_line.mapped('product_id').filtered(
            lambda product: self.env.ref('purchase_stock.route_warehouse0_buy').id in product.route_ids.ids and product.bom_count == 0 and not product.seller_ids
        )
        if product_without_supplier_ids:
            msg_product_names = "\n".join(f"- {product.name}" for product in product_without_supplier_ids)
            msg = _("❌ Vous ne pouvez pas envoyer ce devis car les produits suivants n'ont pas de prix fournisseur :\n\n")
            message = msg + msg_product_names + "\n\n Allez sur la fiche produit et complétez la liste des fournisseurs ou supprimez la ligne du devis."
            raise ValidationError(message)

        return super().action_quotation_send()

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


    def action_update_taxes(self):
        if self.state2 == "invoiced":
            raise ValidationError("⚠️ Vous ne pouvez pas modifier la position fiscale d'un bon de commande dont le statut d'intervention est 'Facturé'.")
        super(SaleOrder, self).action_update_taxes()
