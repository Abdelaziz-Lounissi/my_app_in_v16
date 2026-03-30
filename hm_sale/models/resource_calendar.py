# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models


class ResourceCalendarHoliday(models.Model):
    _name = "resource.calendar.holiday"
    _description = "Holidays"
    _order = "holiday_date"

    name = fields.Char('Name')
    calendar_id = fields.Many2one('resource.calendar', 'Working Hours')
    holiday_date = fields.Date('Date', required=True)
    days = fields.Integer('Days', default=1, required=True)


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    global_holiday_ids = fields.One2many(
        'resource.calendar.holiday', 'calendar_id', 'Holidays',copy=False,
        )