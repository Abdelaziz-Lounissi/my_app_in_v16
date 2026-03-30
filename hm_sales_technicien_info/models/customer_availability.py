# -*- encoding: utf-8 -*-

from datetime import datetime
from odoo import fields, models, api, _
import pytz
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)



class CustomerAvailability(models.Model):
    _name = "hm.customer.availability"
    _description = "Customer Availability"

    name = fields.Char()
    display_name = fields.Char('Display Name', compute="_compute_display_name")
    sale_order_id = fields.Many2one('sale.order', string='SO')
    allow_availabilities_outside_prefs = fields.Boolean(string='Allow Technician to Enter Availabilities Outside Client Preferences', default=True, copy=False)
    cust_availability_ids = fields.One2many('hm.resource.availability.calendar', 'customer_availability_id',
                                            'Customer availability')

    def _compute_display_name(self):
        for rec in self:
            count_cust_availability = len(rec.cust_availability_ids.ids)
            msg = f"📅({count_cust_availability})" if count_cust_availability else "❓"
            sale_order_name = rec.sale_order_id.name
            display_text = f"Disponibilités du client {sale_order_name} {msg}"
            rec.display_name = display_text
            rec.name = display_text

    @api.constrains('sale_order_id')
    def _check_customer_availability(self):
        for availability in self:
            domain = [
                ('sale_order_id', '=', availability.sale_order_id.id),
                ('id', '!=', availability.id),
            ]
            duplicate_availability = self.search(domain)
            if duplicate_availability:
                raise ValidationError('Vous ne pouvez pas créer plus d\'une disponibilité pour un client par commande de vente (Sale Order).')

    def write(self, vals):
        res = super(CustomerAvailability, self).write(vals)
        # recompute fields
        sale_order_id = self.sudo().sale_order_id
        sale_order_id.proposal_lines.technician_availability_ids._compute_availability_color()
        sale_order_id.set_intervention_deadline_date()
        return res

    def save_and_close(self):
        return True

class ResourceAvailabilityCalendar(models.Model):
    _name = "hm.resource.availability.calendar"
    _description = "Resource Availability Calendar"
    _order = 'date_from'
    _rec_name = 'name'

    name = fields.Char(compute='compute_date_format', compute_sudo=True, store=False)
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', compute='compute_date_format', index=True, store=True)
    date = fields.Date(string='Date', required=True)

    hour_from = fields.Float(string='Work from', required=True)
    hour_to = fields.Float(string='Work to', required=True)

    date_from = fields.Datetime(string='Date from', compute='compute_date_format', store=True)
    date_to = fields.Datetime(string='Date to', compute='compute_date_format', store=True)
    customer_availability_id = fields.Many2one('hm.customer.availability', 'Customer Availability')
    tech_availability_id = fields.Many2one('hm.technician.intervention.proposal', 'Technician Availability')
    availability = fields.Selection(
        [('custom', 'Custom'), ('unavailable', 'Unavailable'), ('daytime', 'During the day'), ('morning', 'In the morning'),
         ('afternoon', 'In the afternoon'), ('evening', 'In the evening'), ('afternoon_evening', 'In the afternoon and in the evening'), ('all_day', 'During the day and evening')],
        string='Availability', default='daytime')
    availability_color = fields.Selection([('green', 'Green'), ('blue', 'Blue'), ('red', 'Red')], compute="_compute_availability_color" , string='Availability color')
    my_color = fields.Integer(string='Color Index')

    @api.depends('tech_availability_id', 'date', 'hour_from', 'hour_to')
    def _compute_availability_color(self):
        for record in self:
            my_color = 4
            availability_color = 'blue'

            sale_order_id = record.tech_availability_id.sale_order_id

            customer_availability = sale_order_id.customer_availability_id
            customer_availability_ids = customer_availability.cust_availability_ids
            allow_availabilities_outside_prefs = customer_availability.allow_availabilities_outside_prefs

            intervention_deadline_date = sale_order_id.intervention_deadline_date
            emergency_degrees_id = sale_order_id.emergency_degrees_id
            check_intervention_deadline_date = False

            if customer_availability_ids:

                if intervention_deadline_date:
                    check_intervention_deadline_date = any(
                        availability.date_to < intervention_deadline_date
                        for availability in customer_availability_ids.filtered(
                            lambda x: x.availability != "unavailable"
                        )
                    )

                domain = [
                    ('date', '=', record.date),
                    ('hour_from', '<=', record.hour_from),
                    ('hour_to', '>=', record.hour_to)
                ]

                matching_availability = customer_availability_ids.filtered_domain(domain)
                matching_availability = matching_availability and matching_availability[0] or []

                if matching_availability and matching_availability.availability != 'unavailable':
                    availability_color = 'green'
                    my_color = 10
                elif matching_availability and matching_availability.availability != 'unavailable' and allow_availabilities_outside_prefs and ((intervention_deadline_date and check_intervention_deadline_date) or (not intervention_deadline_date)):
                    availability_color = 'blue'
                    my_color = 4
                elif (not matching_availability) and allow_availabilities_outside_prefs and ((intervention_deadline_date and check_intervention_deadline_date) or (not intervention_deadline_date)):
                    availability_color = 'blue'
                    my_color = 4
                else:
                    my_color = 9
                    availability_color = 'red'
            elif not customer_availability and intervention_deadline_date and record.date_to:
                check_intervention_deadline_date = bool(record.date_to < intervention_deadline_date)
                if check_intervention_deadline_date:
                    my_color = 4
                    availability_color = 'blue'
            elif not customer_availability and not emergency_degrees_id and not intervention_deadline_date:
                my_color = 4
                availability_color = 'blue'

            record.my_color = my_color
            record.availability_color = availability_color

    @api.onchange('availability')
    def _onchange_hours(self):
        hour_ranges = {
            'unavailable': (8.00, 21.00),
            'daytime': (8.00, 17.00),
            'morning': (8.00, 12.00),
            'afternoon': (12.00, 17.00),
            'evening': (17.00, 20.00),
            'afternoon_evening': (12.00, 20.00),
            'all_day': (8.00, 20.00),
        }
        if self.availability in hour_ranges:
            self.hour_from, self.hour_to = hour_ranges[self.availability]

    @api.depends('date', 'hour_from', 'hour_to')
    def compute_date_format(self):
        tz = pytz.timezone('Europe/Brussels')

        for rec in self.sudo():
            if rec.date:
                hour_from_minutes = round((rec.hour_from - int(rec.hour_from)) * 60)
                hour_from_str = f"{int(rec.hour_from):02d}:{hour_from_minutes:02d}"
                hour_from_dt = datetime.strptime(hour_from_str, "%H:%M")

                hour_to_minutes = round((rec.hour_to - int(rec.hour_to)) * 60)
                hour_to_str = f"{int(rec.hour_to):02d}:{hour_to_minutes:02d}"
                hour_to_dt = datetime.strptime(hour_to_str, "%H:%M")

                date_from = datetime.strptime(str(rec.date), '%Y-%m-%d')
                date_to = datetime.strptime(str(rec.date), '%Y-%m-%d')

                rec.date_from = tz.localize(datetime.combine(date_from.date(), hour_from_dt.time()),
                                            is_dst=None).astimezone(pytz.utc).replace(tzinfo=None)
                rec.date_to = tz.localize(datetime.combine(date_to.date(), hour_to_dt.time()), is_dst=None).astimezone(
                    pytz.utc).replace(tzinfo=None)

                rec.name = str(rec.date.strftime('%d/%m')) + ' ' + str(hour_from_dt.strftime('%H:%M')) + '-' + str(hour_to_dt.strftime('%H:%M'))
                dayofweek = datetime.strptime(str(rec.date), '%Y-%m-%d').weekday()
                rec.dayofweek = str(dayofweek)

            else:
                rec.name = ''
                rec.date_from = False
                rec.date_to = False

    def unlink(self):
        for proposal in self:
            proposal.sudo().customer_availability_id.sale_order_id.proposal_lines.technician_availability_ids._compute_availability_color()
        return super(ResourceAvailabilityCalendar, self).unlink()

    def write(self, vals):
        res = super(ResourceAvailabilityCalendar, self).write(vals)
        if any(field in vals for field in ['date', 'hour_from', 'hour_to']):
            # notification_type = 'updated'
            if self.tech_availability_id.tech_first_answer_datetime:
                self.tech_availability_id.availability_last_updated = datetime.now()
            if self.tech_availability_id.state in ('shortlisted', 'sent'):
                self.tech_availability_id.state = 'interested'
                notification_type = 'interested'
                self.tech_availability_id.notify_so_manager(notification_type=notification_type,
                                                            technician_name=self.tech_availability_id.sudo().partner_id.name)
            elif self.tech_availability_id.state == 'interested':
                self.tech_availability_id.notify_so_manager(notification_type='updated',
                                                            technician_name=self.tech_availability_id.sudo().partner_id.name)
            self.sudo()._auto_confirm_technician_availability()

        # recompute fields
        sale_order_id = self.sudo().customer_availability_id.sale_order_id
        sale_order_id.proposal_lines.technician_availability_ids._compute_availability_color()
        sale_order_id.set_intervention_deadline_date()

        return res

    @api.model_create_multi
    def create(self, vals):
        res = super(ResourceAvailabilityCalendar, self).create(vals)
        # notification_type = 'updated'
        if not res.tech_availability_id.tech_first_answer_datetime:
            res.tech_availability_id.tech_first_answer_datetime = datetime.now()
        else:
            res.tech_availability_id.availability_last_updated = datetime.now()
        if res.tech_availability_id.state in ('shortlisted', 'sent'):
            res.tech_availability_id.state = 'interested'
            notification_type = 'interested'
            res.tech_availability_id.notify_so_manager(notification_type=notification_type,
                                                        technician_name=res.tech_availability_id.sudo().partner_id.name)
        elif res.tech_availability_id.state == 'interested':
            res.tech_availability_id.notify_so_manager(notification_type='updated',
                                                        technician_name=res.tech_availability_id.sudo().partner_id.name)
        res.sudo()._compute_availability_color()
        res.sudo()._auto_confirm_technician_availability()
        return res

    def format_date(self):
        tz = pytz.timezone('Europe/Brussels')
        # Convert fractional hours to hours and minutes
        hour_from_minutes = round((self.hour_from - int(self.hour_from)) * 60)
        # Format the time as a string with leading zeros for single digits
        hour_from_str = f"{int(self.hour_from):02d}:{hour_from_minutes:02d}"
        # Combine the date and time strings into a single string
        full_date_str = f"{self.date} {hour_from_str}"
        date_from = datetime.strptime(full_date_str, "%Y-%m-%d %H:%M")
        date_from = tz.localize(date_from, is_dst=None).astimezone(pytz.utc).replace(tzinfo=None)
        return date_from

    def select_tech_availability(self):
        commitment_date = self.format_date()
        self.tech_availability_id.run_confirm_process(commitment_date=commitment_date)


    def _auto_confirm_technician_availability(self):
        """
        Automatically confirm availability for green status records.
        Updates the sale order with commitment date and technician info when
        availability state is 'interested' and color code is green (10).
        """
        for availability in self:
            # Check if availability is green (10) and technician is interested
            if availability.my_color == 10 and availability.tech_availability_id.state == 'interested':
                # Default commitment date from current availability
                commitment_date = availability.format_date()
                today = datetime.today()

                # Find earliest availabilities for the same technician to adjust commitment date
                earlier_availabilities = self.search([
                    ("tech_availability_id", "=", availability.tech_availability_id.id),
                    ("date_from", "<", availability.date_from),
                    ("date_from", ">=", today),
                    ("my_color", "=", 10)
                ], order="date_from asc", limit=1)

                # If an earlier availability exists, use its date as commitment date
                if earlier_availabilities:
                    commitment_date = earlier_availabilities.format_date()

                _logger.info('**** commitment_date : %s ' % commitment_date)
                _logger.info('**** today : %s ' % today)

                if commitment_date.date() >= today.date():
                    # Update the related sale order with commitment date and technician info
                    availability.tech_availability_id.sudo().sale_order_id.write({
                        "commitment_date": commitment_date,
                        "state2": "planned",
                        "hm_imputed_technician_id": availability.tech_availability_id.partner_id.id
                    })