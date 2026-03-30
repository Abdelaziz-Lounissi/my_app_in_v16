# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # x_studio_budget
    hm_budget = fields.Float(string="Budget", related="purchase_line_id.hm_budget", readonly=True,
                             store=True, copy=False, index=False, related_sudo=True)

    # x_studio_technicien
    hm_technician = fields.Boolean(string="Technician", related="partner_id.hm_technician", readonly=True,
                                   store=True, copy=False, index=False, related_sudo=True)

    computed_image_art = fields.Html(string="Art", compute="_compute_image_art")

    @api.depends('product_id')
    def _compute_image_art(self):
        for line in self:
            line.computed_image_art = ""
            if line.product_id:
                res = "<div class='d-flex flex-column align-items-center text-center'>"
                supplier_info_id = False
                for supplier in line.product_id.seller_ids:
                    if line.purchase_line_id.order_id.partner_id.id == supplier.partner_id.id:
                        supplier_info_id = supplier
                if supplier_info_id and supplier_info_id.product_code:
                    res += "<span class='border-bottom pb-1 mb-1'>%s</span>" % supplier_info_id.product_code
                else:
                    res += "<span class='text-muted border-bottom pb-1 mb-1'>No Reference</span>"
                image_url = '/web/image/%s/%s/%s/%s' % ('product.product', line.product_id.id, 'image_1024', '48x48')
                res += "<img src='%s' alt='Product Image'/>" % image_url
                res += "</div>"
                line.computed_image_art = res
