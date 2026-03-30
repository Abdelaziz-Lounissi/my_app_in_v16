# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HmPurchaseOrderLineStage(models.Model):
    _name = "hm.purchase.order.line.stage"
    _description = "Purchase order line stage"

    name = fields.Char(string="Name", copy=False, store=True, index=False, translate=False)
