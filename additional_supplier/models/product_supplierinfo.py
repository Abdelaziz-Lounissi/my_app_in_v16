# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging
from odoo.tools.float_utils import float_compare, float_round, float_is_zero

_logger = logging.getLogger(__name__)

class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    equivalent = fields.Boolean(string='Equivalent')
    source = fields.Char(string="Source")
    created_date = fields.Datetime(string='Create Date', readonly=True)
    updated_date = fields.Datetime(string='Update Date', readonly=True)
    manufacturer_code = fields.Char(string='Manufacturer code')
    code_ean = fields.Char(string='EAN code')
    name_nl = fields.Char(string='Name NL')
    fabricant = fields.Char(string='Manufacturer')
    manufacturer = fields.Char(string='Manufacturer')
    model = fields.Char(string='Model')
    image_url_1 = fields.Char(string='Image Url 1')
    fiche_fr = fields.Char(string='Fiche FR')
    fiche_nl = fields.Char(string='Fiche NL')
    gross_price = fields.Float(string='Gross price', tracking=True)
    price = fields.Float(string='Price', default=0.0, digits='Product Price', tracking=True, required=True, help="The price to purchase a product")
    hm_special_price = fields.Float(string='Prix spécial contrat cadre', tracking=True)
    hm_special_price_contract = fields.Text(string='Référence contrat cadre', tracking=True)
    hm_imported_price = fields.Float(string='Prix net importé', readonly=True)
    active = fields.Boolean(default=True, tracking=True)

    hm_calculated_discount = fields.Float('Discount calculated (%)', compute='_get_calculated_discount', store=True, tracking=True)
    copy_calculated_discount = fields.Boolean('Copy calculated discount', default=False)
    hm_calc_disc_vs_max_obt_disc = fields.Float('Calculated discount (%) vs Maximum obtained discount (%)', compute='_get_hm_calculated_discount_vs_max_obtained_discount')

    @api.depends("hm_calculated_discount", "hm_max_obtained_discount")
    def _get_hm_calculated_discount_vs_max_obtained_discount(self):
        for record in self:
            record['hm_calc_disc_vs_max_obt_disc'] = record.hm_calculated_discount - record.hm_max_obtained_discount

    @api.depends("gross_price", "price")
    def _get_calculated_discount(self):
        for record in self:
            hm_calculated_discount = 0
            if record.gross_price != 0:
                hm_calculated_discount = 100 * (1 - (record.price / record.gross_price))
            record['hm_calculated_discount'] = hm_calculated_discount

    def write(self, vals):
        for product in self:
            price = product.price
            gross_price = product.gross_price
            hm_calculated_discount = 0
            res = super(SupplierInfo, product).write(vals)
            if product.gross_price != 0:
                hm_calculated_discount = 100 * (1 - (product.price / product.gross_price))
            if vals.get('gross_price', False):
                if ((float_is_zero(product.hm_special_price, precision_digits=2) or not product.hm_special_price) and gross_price != vals['gross_price']):
                    if hm_calculated_discount > product.hm_max_obtained_discount:
                        product.hm_max_obtained_discount = hm_calculated_discount
            elif vals.get('price', False) and price != vals['price']:
                if hm_calculated_discount > product.hm_max_obtained_discount:
                    product.hm_max_obtained_discount = hm_calculated_discount
        return res

    @api.onchange('hm_special_price', 'hm_imported_price')
    def _onchange_price_and_hm_special_price(self):
        price = 0
        if self.hm_imported_price != 0.0 and self.hm_special_price != 0.0:
            price = min(self.hm_imported_price, self.hm_special_price)
        else:
            price = max(self.hm_imported_price, self.hm_special_price)
        if self.price != 0.0:
            price = min(self.price, price)
        self.price = price


    def name_get(self):
        res_names = super(SupplierInfo, self).name_get()
        if self._context.get('active_model') != 'purchase.order' and not self._context.get('is_supplier_choice'):
            return res_names
        result = []
        for res in self:
            name = '%s / %s' % (res.partner_id.display_name, res.price)
            result.append((res.id, name))
        return result
