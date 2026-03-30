# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HmProductVanmarcke(models.Model):
    _name = "hm.product.vanmarcke"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Hm Product Van Marcke"

    supplier_code = fields.Char(string='Supplier code')
    manufacturer_code = fields.Char(string='Manufacturer code')
    code_ean = fields.Char(string='EAN code')
    name_nl = fields.Char(string='Name NL')
    name_fr = fields.Char(string='Name FR')
    long_name_nl = fields.Text(string='Long Name NL')
    long_name_fr = fields.Text(string='Long Name FR')
    fabricant = fields.Char(string='Manufacturer')
    model = fields.Char(string='Model')
    description_nl = fields.Text(string='Description NL')
    description_fr = fields.Text(string='Description FR')
    image_url_1 = fields.Char(string='Image Url 1')
    image_url_2 = fields.Char(string='Image Url 2')
    image_url_3 = fields.Char(string='Image Url 3')
    category = fields.Char(string='Category')
    fiche_nl = fields.Char(string='Fiche NL')
    fiche_fr = fields.Char(string='Fiche FR')
    gross_price = fields.Float(string='Gross price', tracking=True)
    price_code = fields.Char(string='Price code')
    minimum_quantity = fields.Char(string='Minimum quantity')
    vat_code = fields.Char(string='VAT code')
    parent_category = fields.Char(string='Parent category')
    net_price = fields.Float(string='Net Price', tracking=True)
    display_name = fields.Char('Display Name', compute="_compute_display_name")
    executed = fields.Boolean('Executed', default=False)
    updated = fields.Boolean('Updated', default=False)
    check_import = fields.Boolean('Check Import', default=False)
    mark_as_created = fields.Boolean('Product supplier info to be created')
    mark_as_updated = fields.Boolean('Product supplier info to be updated')

    def _compute_display_name(self):
        for prod in self:
            prod_name = ''
            if prod.name_fr:
                prod_name = str(prod.name_fr)
            prod.display_name = prod_name