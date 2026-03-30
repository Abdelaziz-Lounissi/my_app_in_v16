# -*- encoding: utf-8 -*-

from odoo import fields, models, api


class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    work_type = fields.Many2one('hm.work.type', string='Work type', required=True)

    automate_proposals_creation = fields.Boolean(string="Créer automatiquement les propositions")
    send_proposals = fields.Selection(
        selection=[
            ('one_shot', 'One-shot'),
            ('in_batches', 'In batches'),
        ],
        string='Send proposals',
        default='one_shot',
    )

    batch_size = fields.Selection(
        selection=[
            ('1', '1 technician at a time'),
            ('2', '2 technicians at a time'),
            ('3', '3 technicians at a time'),
        ], string='Suggest the intervention to', default='1')

    frequency_proposals = fields.Selection(
        selection=[
            ('10_min', 'Every 10 minutes'),
            ('30_min', 'Every 30 minutes'),
            ('60_min', 'Every hour'),
            ('240_min', 'Every 4 hours'),
            ('1440_min', 'Every 24 hours'),
        ],
        string='Frequency of proposals',
        default='60_min',
    )
