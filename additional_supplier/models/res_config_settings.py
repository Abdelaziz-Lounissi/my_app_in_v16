# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    partner_id = fields.Many2one('res.partner', string='Default supplier', domain="[('supplier_rank', '>', 0)]")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        partner = params.get_param('partner_id', default=108)
        res.update(
            partner_id=int(partner),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("partner_id", self.partner_id.id)
