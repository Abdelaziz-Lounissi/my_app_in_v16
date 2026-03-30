# -*- coding: utf-8 -*-
# Merge module hm_sale_purchase_custom

import logging
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_get_domain(self, company_id, values, partner):
        gpo = self.group_propagation_option
        group = (gpo == 'fixed' and self.group_id) or \
                (gpo == 'propagate' and 'group_id' in values and values['group_id']) or False
        if group and partner.name == "Technicien à imputer" and group.sale_id.hm_imputed_technician_id:
            partner = group.sale_id.hm_imputed_technician_id.id
        else:
            partner = partner.id

        domain = (
            ('partner_id', '=', partner),
            ('state', '=', 'draft'),
            ('picking_type_id', '=', self.picking_type_id.id),
            ('company_id', '=', company_id.id),
        )
        if group:
            domain += (('group_id', '=', group.id),)
        return domain

    @api.model
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, po):
        res = super(StockRule, self)._prepare_purchase_order_line(product_id, product_qty, product_uom, company_id, values, po)
        if values.get('sale_line_id'):
            sale_line_id = values.get('sale_line_id')
            order_line_id = self.env['sale.order.line'].search([('id', '=', sale_line_id)])
            # If the 1st article of the PO is an article whose expense account is 613100 or 613040
            # ->The standard PO is automatically pre-encoded as PO Commission
            if order_line_id and order_line_id.product_id.property_account_expense_id:
                property_account_expense_code = order_line_id.product_id.property_account_expense_id.code
                if property_account_expense_code in ('613100', '613040'):
                    po.po_type = 'po_commission'

            if order_line_id and product_id.hm_maintain_SO_desc_and_cost_on_PO and po.state == 'draft':
                name = order_line_id.spec or order_line_id.name or " "
                price_unit = order_line_id.purchase_price
                res['name'] = name
                res['price_unit'] = price_unit
            else:
                partner = values['supplier'].partner_id.name
                product_lang = product_id.with_prefetch().with_context(lang=partner.lang, partner_id=partner.id)
                name = product_lang.name
                if product_lang.description_purchase:
                    name += '\n' + product_lang.description_purchase
                res['name'] = name
        return res

    def _prepare_purchase_order(self, company_id, origins, values):
        res = super(StockRule, self)._prepare_purchase_order(company_id, origins, values)

        values = values[0]
        partner_id = values['supplier'].partner_id
        group = values['group_id']

        po_type = 'po_marchandise'
        if partner_id.hm_technician:
            po_type = 'po_technicien'

        if partner_id.name == "Technicien à imputer" and group.sale_id.hm_imputed_technician_id:
            partner_id = group.sale_id.hm_imputed_technician_id

        res['po_type'] = po_type
        res['stage2_id'] = False
        res['partner_id'] = partner_id.id

        return res
