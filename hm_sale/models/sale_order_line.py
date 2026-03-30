# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    hm_product_barcode = fields.Char(string='HM Art', help='International Article Number used for product identification.',
                                     store=True, copy=False, translate=False, index=False, related='product_id.barcode', related_sudo=True)
    hm_product_description_sale = fields.Text(string='ART desc',
                                              help='A description of the Product that you want to communicate to your customers. This description will be copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note.',
                                              store=True, copy=False, translate=True, index=False,
                                              related='product_id.description_sale')
    hm_product_name = fields.Char(string='Product Name', store=True, copy=False, index=False, translate=True,
                                  related='product_id.name')
    hm_intervention_date = fields.Datetime(string='Intervention date',
                                           help='This is the delivery date promised to the customer. If set, the delivery order will be scheduled based on this date rather than product lead times.',
                                           readonly=True, store=True, copy=False, index=False,
                                           related='order_id.commitment_date')
    hm_so_invoice_status = fields.Selection(string='État de la facture SO', readonly=True, store=True,
                                            copy=False, index=False, related='order_id.invoice_status')
    hm_sale_order_id = fields.Many2one('sale.order', string='Validated', store=True, copy=False, index=False,
                                       ondelete='set null', related='purchase_line_ids.sale_order_id')
    hm_purchase_line_order_id = fields.Many2one('purchase.order', string='Validé', store=True, copy=False, index=False,
                                                ondelete='set null', related='purchase_line_ids.order_id')
    hm_purchase_line = fields.Integer(string='New Champ lié POL HM', store=True, copy=False, index=False,
                                      related='purchase_line_ids.id')
    hm_nr_po = fields.Integer(string='Nr PO', store=True, copy=False, index=False,
                              related='purchase_line_ids.order_id.id')
    hm_radiator_power = fields.Float(string='Puissance radiateur', readonly=True, index=False, copy=False,
                                     related='product_id.hm_radiator_power_kw')
    hm_technician = fields.Many2one('res.partner', string='Technician', store=True, copy=False, index=False,
                                    ondelete='set null', related='purchase_line_ids.order_id.partner_id',
                                    help='You can find a vendor by its Name, TIN, Email or Internal Reference.')
    spec = fields.Text(string='Spec')
    bom_count = fields.Integer(related="product_id.bom_count")
    is_variant = fields.Boolean(string="Copied Variant", default=False, copy=True)
    computed_image_art = fields.Html(string="Art", compute="_compute_image_art")
    hm_product_qty = fields.Char(string='HM Quantity', compute='_compute_hm_product_qty')

    @api.onchange('product_id')
    def _compute_image_art(self):
        for line in self:
            line.computed_image_art = ""
            if line.product_id:
                res = "<div class='d-flex flex-column align-items-center text-center'>"
                if line.product_id.product_tmpl_id.sku:
                    res += "<span class='border-bottom pb-1 mb-1'>%s</span>" % line.product_id.product_tmpl_id.sku
                else:
                    res += "<span class='text-muted border-bottom pb-1 mb-1'>No Reference</span>"
                prime_supplier_id = line.product_id.seller_ids and line.product_id.seller_ids[0] or False
                if prime_supplier_id and prime_supplier_id.partner_id.image_1920 and prime_supplier_id.partner_id.hm_is_real_picture == True:
                    image_url = '/web/image/%s/%s/%s/%s' % ('res.partner', prime_supplier_id.partner_id.id, 'image_1920', '35x35')
                    res += "<img style='padding:20px!important' src='%s' alt='Supplier Image'/>" % image_url
                image_url = '/web/image/%s/%s/%s/%s' % ('product.product', line.product_id.id, 'image_1024', '48x48')
                res += "<img src='%s' alt='Product Image'/>" % image_url
                res += "</div>"
                line.computed_image_art = res

    @api.onchange('product_custom_attribute_value_ids')
    def onchange_pproduct_custom_attribute_value_ids(self):
        self.is_variant = False

    @api.onchange('product_uom_qty')
    def _compute_hm_product_qty(self):
        for line in self:
            product_uom_qty = line.product_uom_qty
            str_product_uom_qty = str(product_uom_qty).split('.')
            if str_product_uom_qty and int(str_product_uom_qty[1]) == 0:
                decimal_product_uom_qty = round(product_uom_qty)
            else:
                decimal_product_uom_qty = round(product_uom_qty, 2)
            line.hm_product_qty = decimal_product_uom_qty
