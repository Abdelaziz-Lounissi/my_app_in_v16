# -*- coding: utf-8 -*-


from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('property_id')
    def onchange_property_for_subscription(self):
        if self.property_id:
            subscription_stage_in_progress = self.env["sale.order"].search([
                ('is_subscription', '=', True),
                ('property_id', '=', self.property_id.id),
                ('stage_id', '=', self.env.ref("sale_subscription.sale_subscription_stage_in_progress").id)
            ])
            subscription_names=""
            for rec in subscription_stage_in_progress:
                subscription_names += '-' + rec.sale_order_template_id.name + '\n'
            if subscription_names:
                return {
                    'warning': {
                        'title': "Attention",
                        'message': f"⚠️ Il y a un ou plusieurs abonnement(s) en cours à cette adresse :\n{subscription_names}\n\n"
                                   f"Veuillez sélectionner la liste de prix correspondante.",
                    }
                }


