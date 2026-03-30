# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HmFacqLog(models.Model):
    _name = "hm.facq.log"
    _description = "Hm Facq Log"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date desc"

    name = fields.Char(compute='_compute_name', string="Name")
    note = fields.Char(string="Note")
    date = fields.Datetime(string="Date")
    state = fields.Selection([('fail', 'Fail'), ('success', 'Success')], 'Status', readonly=True, default='success')

    def _compute_name(self):
        for log in self:
            log.name = str(log.state) + ' ' + "update price"
