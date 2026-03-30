# -*- coding: utf-8 -*-

from odoo import api, fields, models
import base64


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    account_key = fields.Binary(string='Account Key')

    @api.model
    def get_values(self):
        res = super().get_values()
        account_key = self.env['ir.config_parameter'].sudo().get_param('account_key')
        res.update({
            'account_key': account_key,
        })
        return res

    def set_values(self):
        super().set_values()

        # Encode the binary data as a base64-encoded string
        encoded_data = base64.b64encode(self.account_key or b'').decode('utf-8')

        # Set the value of the 'account_key' parameter
        self.env['ir.config_parameter'].sudo().set_param('account_key', encoded_data)

    def update_init_firebase_manually(self):
        self.ensure_one()
        if self.account_key:
            encoded_data = base64.b64encode(self.account_key or b'').decode('utf-8')
            self.env['hm.mobile.notification'].with_context(
                    check_account_key_from_file=True,
                    account_key=encoded_data
                ).init_firebase()