# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class BaseAutomation(models.Model):
    _name = 'base.automation'
    _inherit = ['mail.thread', 'base.automation']

    _tracked_fields = [
        "name", "model_name", "type", "active", "trigger", "trigger_field_ids", "filter_pre_domain",
        "filter_domain", "state", "template_id", "mail_post_method", "activity_type_id",
        "activity_summary", "activity_note", "activity_date_deadline_range", "activity_user_type",
        "activity_user_id", "activity_user_field_name", "sms_template_id", "sms_method", "code","trg_date_range", "trg_date_range_type",

    ]

    description = fields.Text(
        string="Automation Description",
        help="Detailed description of this automation rule's purpose, conditions, and expected behavior",
        tracking=True
    )

    @api.model
    def _setup_base(self):
        """Setup tracking on specified fields"""
        super()._setup_base()
        for field_name in self._tracked_fields:
            if field_name in self._fields:
                field = self._fields[field_name]
                field.tracking = True

    def write(self, vals):
        if self.env.context.get('skip_automation_notification') or not vals:
            return super(BaseAutomation, self).write(vals)
        skip_fields = {'write_date', 'write_uid', '__last_update', 'message_ids', 'message_follower_ids', 'last_run'}
        if set(vals.keys()).issubset(skip_fields):
            return super(BaseAutomation, self).write(vals)
        old_fields_map = {rec.id: rec.trigger_field_ids for rec in self}
        res = super(BaseAutomation, self).write(vals)
        try:
            emails = [
                "jerome@heat-me.be",
                "abdelaziz@yourent.immo",
                "developer@heat-me.be"
            ]
            partners = self.env['res.partner']
            for email in emails:
                user = self.env['res.users'].search([('email', '=', email)], limit=1)
                if user:
                    partners |= user.partner_id

            if not partners:
                return res

            mentions = " ".join(
                f'<a href="#" data-oe-model="res.partner" data-oe-id="{p.id}">@{p.name}</a>'
                for p in partners
            )
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

            for record in self:
                record_url = f"{base_url}/web#id={record.id}&model=base.automation&view_type=form"

                if 'trigger_field_ids' in vals:
                    old_fields = old_fields_map.get(record.id, self.env['ir.model.fields'])
                    new_fields = record.trigger_field_ids
                    added = new_fields - old_fields
                    removed = old_fields - new_fields
                    record._notify_trigger_field_changes(added, removed)

                message_body = f"""
                    <p>Bonjour {mentions},</p>
                    <p>Une action automatisée a été <b>modifiée</b> :</p>
                    <ul>
                        <li><b>Nom :</b> {record.name}</li>
                        <li><b>Date :</b> {fields.Datetime.to_string(record.write_date) if record.write_date else 'N/A'}</li>
                        <li><b>Modifié par :</b> {self.env.user.name}</li>
                    </ul>
                    <p><a href="{record_url}" target="_blank">🔗 Ouvrir cette action automatisée</a></p>
                """

                record.message_post(
                    body=message_body,
                    subject=_("Modification d'une action automatisée"),
                    partner_ids=partners.ids,
                    email_layout_xmlid='mail.mail_notification_layout',
                )

        except Exception as e:
            _logger.error("Notification failed: %s", e)

        return res

    def _notify_trigger_field_changes(self, added, removed):
        lines = ["<p><b>Champs de déclenchement modifiés :</b></p>"]  # Titre ajouté

        if added:
            added_list = "".join(f"<li>✅ {f.name} ({f.model_id.model})</li>" for f in added)
            lines.append(f"<ul>{added_list}</ul>")

        if removed:
            removed_list = "".join(f"<li>❌ {f.name} ({f.model_id.model})</li>" for f in removed)
            lines.append(f"<ul>{removed_list}</ul>")

        if lines:
            self.message_post(
                body="<br/>".join(lines),
                subtype_xmlid="mail.mt_note",
                message_type="notification",
            )
