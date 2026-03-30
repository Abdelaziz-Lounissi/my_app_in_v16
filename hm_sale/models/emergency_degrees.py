# -*- coding: utf-8 -*-

from odoo import api, fields, models


class EmergencyDegrees(models.Model):
    _name = "order.emergency.degrees"
    _description = "Emergency Degrees"
    _rec_name = 'name'
    _order = "sequence, name, id"

    name = fields.Char('Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages.")
    technical_value = fields.Char('Valeur technique')

    currency_id = fields.Many2one(related='create_uid.currency_id', related_sudo=True)
    delay_to_plan_intervention = fields.Integer(
        string="Delay to schedule the intervention (days)",
        default=15,
        help="Maximum number of days to schedule the intervention from the date the service order manager will organize their intervention"
    )
    urgency_fee = fields.Monetary(
        string="Urgency fee for intervention within 24 hours",
        default=0,
        help="Emergency fee charged to the customer if the intervention takes place on the same day before 9 PM for an order placed before 10 AM, otherwise before 5 PM the next day"
    )
    product_ids = fields.Many2many(
        "product.product",
        string="Produits liés",
        help="Lorsque le produit est ajouté à un devis/bon de commande, le délai d'intervention est automatiquement mis à jour"

    )
    sequence = fields.Integer('Sequence')

    @api.onchange('urgency_fee')
    def onchange_urgency_fee(self):
        if self.urgency_fee > 0:
            self.delay_to_plan_intervention = 0
