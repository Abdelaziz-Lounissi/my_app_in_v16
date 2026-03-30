# -*- coding: utf-8 -*-
# Merge module hm_sale_purchase_custom

import logging
from odoo import models

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_purchase_order(self, company_id, origins, values):
        res = super(StockRule, self)._prepare_purchase_order(company_id, origins, values)

        values = values[0]
        partner_id = values['supplier'].partner_id
        group = values['group_id']

        if partner_id.name == "Technicien à imputer" and group.sale_id.hm_imputed_technician_id:
            partner_id = group.sale_id.hm_imputed_technician_id

        if group.sale_id.sale_order_template_id.requisition_id and partner_id == group.sale_id.sale_order_template_id.requisition_id.vendor_id:
            res['requisition_id'] = group.sale_id.sale_order_template_id.requisition_id.id
            res['partner_ref'] = group.sale_id.sale_order_template_id.requisition_id.supplier_reference

        return res
