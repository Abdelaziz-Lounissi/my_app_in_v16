# -*- coding: utf-8 -*-

from odoo import models


class IrActionsServer(models.Model):
    _name = 'ir.actions.server'
    _inherit = ['mail.thread','ir.actions.server']
