# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ServerActions(models.Model):
    _inherit = 'ir.actions.server'

    def _run_action_sms_multi(self, eval_context=None):
        # TDE CLEANME: when going to new api with server action, remove action
        if not self.sms_template_id or self._is_recompute():
            return False

        records = eval_context.get('records') or eval_context.get('record')
        if not records:
            return False

        composer = self.env['sms.composer'].with_context(
            default_res_model=records._name,
            default_res_ids=records.ids,
            default_composition_mode='comment' if self.sms_method == 'comment' else 'mass',
            default_template_id=self.sms_template_id.id,
            default_mass_keep_log=self.sms_method == 'note',
            default_number_field_name=self.sms_template_id.number_field_name or False,
        ).create({})
        composer.action_send_sms()
        return False
