# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, modules, tools


class MailActivityType(models.Model):
    _inherit = "mail.activity.type"

    # show_message = fields.Boolean(default=True, String="Do not Show in Messages")
    activity_as_complete_opportunity_sent = fields.Boolean('Mark the activity as complete once the quote has been sent',
                                                           default=False,
                                                           help="Cochez cette case pour que l'activité soit automatiquement marquée comme terminée une fois le statut de l'opportunité passé à Devis final envoyé")
    activity_as_complete_opportunity_won_lost = fields.Boolean('Mark activity as complete once opportunity won',
                                                               default=False,
                                                               help="Cochez cette case pour que l'activité soit automatiquement marquée comme terminée une fois le statut de l'opportunité passé à Gagné ou Perdu")
