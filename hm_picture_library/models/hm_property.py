# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.osv import expression


class HmProperty(models.Model):
    _inherit = 'hm.property'

    total_pictures = fields.Integer(compute='_compute_total_pictures')

    def _compute_total_pictures(self):
        for property in self:
            lead_ids = property.sale_order_ids.mapped('opportunity_id')
            domain = expression.OR([[('sale_order_ids', 'in', property.sale_order_ids.ids)], [('lead_ids', 'in', lead_ids.ids)]])
            res_domain = expression.AND([domain, [('is_client_signature', '=', False)]])
            res_ids = self.env['hm.picture.library'].search(res_domain)
            property.total_pictures = len(res_ids)

    def action_view_property_pictures(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hm_picture_library.hm_picture_library_action")
        lead_ids = self.sale_order_ids.mapped('opportunity_id')
        domain = expression.OR([[('sale_order_ids', 'in', self.sale_order_ids.ids)], [('lead_ids', 'in', lead_ids.ids)]])
        res_domain = expression.AND([domain, [('is_client_signature', '=', False)]])
        res_ids = self.env['hm.picture.library'].search(res_domain)
        action['domain'] = [('id', 'in', res_ids.ids)]
        return action
