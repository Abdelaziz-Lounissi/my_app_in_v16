# -*- coding: utf-8 -*-

from odoo import models


class IrCron(models.Model):
    _name = 'ir.cron'
    _inherit = ['mail.thread','ir.cron']
