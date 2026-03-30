# -*- coding: utf-8 -*-

from odoo import models, api


class AccountFollowupReport(models.AbstractModel):
    _inherit = 'account.followup.report'


    @api.model
    def _get_sms_body(self, options):
        lang = self.env.user.lang
        if options.get('partner_id'):
            partner = self.env['res.partner'].browse(options.get('partner_id'))
            lang = partner.lang

        if options.get('sms_template'):
            options['sms_template'] = options['sms_template'].with_context(lang=lang)

        return super(AccountFollowupReport, self.with_context(lang=lang))._get_sms_body(options)