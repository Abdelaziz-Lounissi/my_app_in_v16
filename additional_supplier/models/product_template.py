# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    updated = fields.Boolean('Updated', default=False)
    prime_supplier_id = fields.Many2one('res.partner', 'Prime supplier', compute='_compute_prime_supplier')
    first_supplier_info_id = fields.Many2one('product.supplierinfo', 'First supplier info', compute='_compute_first_supplier_info', store=True)
    archive = fields.Boolean('Archive', default=False)
    archived = fields.Boolean('Archive after merge', default=False)
    is_flagged = fields.Boolean('Is flagged', default=False)
    active = fields.Boolean(default=True, tracking=True)

    @api.depends('seller_ids')
    def _compute_first_supplier_info(self):
        for product in self:
            if product.seller_ids:
                product.first_supplier_info_id = product.seller_ids[0].id
            else:
                product.first_supplier_info_id = False

    @api.depends('seller_ids')
    def _compute_prime_supplier(self):
        for product in self.sudo():
            products = self.env['product.product'].search([('barcode', '=', product.barcode)])
            if product.seller_ids:
                prime_supplier_id = product.seller_ids[0]
                source = prime_supplier_id.source
                created_date = prime_supplier_id.created_date
                updated_date = prime_supplier_id.updated_date
                product.prime_supplier_id = prime_supplier_id.partner_id.id
                # check if the product supplier info is created form merge or not.
                # if yes => run the update base on supplier info.
                # if no =>  block the update, keeps the data as it is.
                if source == False and created_date == False and updated_date == False:
                    product.list_price = product.list_price
                    if not products:
                        product.barcode = product.barcode
                    product.hm_supplier_category = product.hm_supplier_category
                    product.sku = product.sku
                    product.standard_price = product.standard_price
                elif source or created_date or updated_date:
                    product.list_price = prime_supplier_id.gross_price
                    products_code_ean = self.env['product.product'].search([('barcode', '=', prime_supplier_id.code_ean)])
                    # if not products_code_ean:
                    #     product.barcode = prime_supplier_id.code_ean
                    product.hm_supplier_category = prime_supplier_id.parent_category
                    product.sku = prime_supplier_id.product_code
                    product.standard_price = prime_supplier_id.price
            else:
                product.prime_supplier_id = False
                if product.product_variant_count > 1:
                    product.list_price = 0

    @api.model
    def set_prime_supplier(self):
        settings_partner = self.env['res.config.settings'].get_values()
        partner = settings_partner['partner_id']
        if len(self.seller_ids) > 1:
            prime_supplier_ids = self.seller_ids.filtered(lambda x: x.partner_id.id == partner)
            for prime_supplier_id in prime_supplier_ids:
                prime_supplier_id.sequence = 0

            supplier_info_ids = self.seller_ids.filtered(lambda x: x.partner_id.id != partner)
            sequence = 1
            for supplier_info_id in supplier_info_ids:
                supplier_info_id.sequence = sequence
                sequence += 1
            self.env.cr.commit()
