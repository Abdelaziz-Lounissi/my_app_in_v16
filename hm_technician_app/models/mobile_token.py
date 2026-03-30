from odoo import fields, models, api
from odoo.exceptions import ValidationError


class MobileToken(models.Model):
    _name = 'hm.mobile.token'
    _description = 'Mobile token'

    name = fields.Char()
    display_name = fields.Char('Display Name', compute="_compute_display_name")
    firebase_registration_token = fields.Char(string="Firebase registration token")
    user_id = fields.Many2one("res.users", string="User")
    last_app_call = fields.Datetime(string="Last app call")
    app_version = fields.Char('App version')

    @api.depends('name', 'user_id')
    def _compute_display_name(self):
        for token in self:
            name_parts = token.user_id.name.split(' ')
            if len(name_parts) >= 3:
                truncated_name = ' '.join(name_parts[:2])
            elif len(name_parts) == 2:
                truncated_name = name_parts[0]
            else:
                truncated_name = token.user_id.name
            token_name = token.name if token.name else ''
            token.display_name = truncated_name + '/' + token_name

    @api.constrains('firebase_registration_token')
    def _constrains_firebase_registration_token_unique(self):
        for record in self:
            if record.firebase_registration_token:
                token_count = self.search_count([('firebase_registration_token', '=', record.firebase_registration_token)])
                if token_count > 1:
                    raise ValidationError('Firebase registration token must be unique!')
