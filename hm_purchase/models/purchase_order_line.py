# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError, AccessError
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    hm_budget = fields.Float(string="Budget", related="sale_line_id.purchase_price", readonly=True, store=True,
                             copy=False, index=False, related_sudo=True)
    hm_description_from_so = fields.Text(string="Description from SO", related="sale_line_id.name",
                                         readonly=True, store=True, copy=False, index=False, translate=False, related_sudo=True)
    hm_technical_info = fields.Text(string="Infos tech", store=True, copy=False, index=False, translate=False,
                                    related="sale_line_id.hm_technical_info", related_sudo=True)

    # TODO: clean me; still need it?
    hm_product_qty_credit = fields.Float(string="credited Quantity", readonly=True, store=False, index=False, copy=False,
                                        compute='_compute_credit_qty_total')
    hm_total_credit = fields.Float(string="credited Total", readonly=True, store=False, index=False, copy=False,
                                        compute='_compute_credit_qty_total')

    hm_motif_retour = fields.Char(string="Motif du retour")
    partner_ref = fields.Char('Vendor Reference', related="order_id.partner_ref", related_sudo=True)
    # TODO: clean me; name; related??
    hm_so_lie = fields.Many2one('sale.order', string='SO lié', related='order_id.hm_so_lie', related_sudo=True)

    # TODO: clean me; still need it?
    product_name = fields.Char(related='product_id.name', string="Product name", store=True, index=True, related_sudo=True)
    product_categ_name = fields.Char(related='product_id.categ_id.name', string="Category name",store=True, index=True, related_sudo=True)
    product_categ_display_name = fields.Char(related='product_id.categ_id.display_name', string="Category name",store=True, index=True, related_sudo=True)

    stage2_id = fields.Many2one('purchase.stage',  related="order_id.stage2_id", store=True)

    computed_image_art = fields.Html(string="Art", compute="_compute_image_art")
    sku = fields.Char("SKU", compute="_compute_image_art")
    used_in_bom_count = fields.Integer(related="product_id.used_in_bom_count")
    state2 = fields.Selection(related="order_id.state2",store=True, string='State2 SO')
    po_type = fields.Selection(related="order_id.po_type", store=True, string='PO Type')


    @api.depends('qty_invoiced','qty_received','price_unit')
    def _compute_credit_qty_total(self):
        for rec in self:
            rec.hm_product_qty_credit = rec.qty_invoiced - rec.qty_received
            rec.hm_total_credit = rec.hm_product_qty_credit * rec.price_unit

    @api.depends('product_id')
    def _compute_image_art(self):
        for line in self:
            line.computed_image_art = ""
            line.sku = ""
            if line.product_id:
                res = "<div class='d-flex flex-column align-items-center text-center'>"
                supplier_info_id = False
                for supplier in line.product_id.seller_ids:
                    if line.order_id.partner_id.id == supplier.partner_id.id:
                        supplier_info_id = supplier
                if supplier_info_id and supplier_info_id.product_code:
                    res += "<span class='border-bottom pb-1 mb-1'>%s</span>" % supplier_info_id.product_code
                    line.sku = supplier_info_id.product_code
                else:
                    res += "<span class='text-muted border-bottom pb-1 mb-1'>No Reference</span>"
                    line.sku = ""

                if line.order_id.partner_id and line.order_id.partner_id.image_1920 and line.order_id.partner_id.hm_is_real_picture == True:
                    image_url = '/web/image/%s/%s/%s/%s' % ('res.partner', line.order_id.partner_id.id, 'image_1920', '35x35')
                    res += "<img style='padding:20px!important' src='%s' alt='Supplier Image'/>" % image_url

                image_url = '/web/image/%s/%s/%s/%s' % ('product.product', line.product_id.id, 'image_1024', '48x48')
                res += "<img src='%s' alt='Product Image'/>" % image_url
                res += "</div>"
                line.computed_image_art = res

    def _get_product_purchase_description(self, product_lang):
        name = super(PurchaseOrderLine, self)._get_product_purchase_description(product_lang)
        name = product_lang.name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        return name

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            first_line = self.order_id.order_line[0] and self.order_id.order_line[0]._origin.id
            first_line_id = self.env['purchase.order.line'].browse(first_line)
            if first_line_id != False and first_line_id.product_id.property_account_expense_id:
                property_account_expense_code = first_line_id.product_id.property_account_expense_id.code
                if property_account_expense_code in ('613100', '613040'):
                    self.order_id.po_type = 'po_commission'

    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values, po):
        res = super()._prepare_purchase_order_line_from_procurement(product_id, product_qty, product_uom, company_id, values, po)
        if values.get('sale_line_id'):
            sale_line_id = values.get('sale_line_id')
            order_lines = self.env['sale.order.line'].search([('id', '=', sale_line_id)])
            # If the 1st article of the PO is an article whose expense account is 613100 or 613040
            # ->The standard PO is automatically pre-encoded as PO Commission
            if order_lines and order_lines.product_id.property_account_expense_id:
                property_account_expense_code = order_lines.product_id.property_account_expense_id.code
                if property_account_expense_code in ('613100', '613040'):
                    po.po_type = 'po_commission'

            if order_lines and order_lines.spec and product_id.hm_maintain_SO_desc_and_cost_on_PO and po.state == 'draft':
                name = order_lines.spec
                price_unit = order_lines.purchase_price
                res['name'] = name
                res['price_unit'] = price_unit
            else:
                partner = values['supplier'].partner_id
                product_lang = product_id.with_prefetch().with_context(lang=partner.lang, partner_id=partner.id)
                name = product_lang.name
                if product_lang.description_purchase:
                    name += '\n' + product_lang.description_purchase
                res['name'] = name

        return res

    def create_so_line_from_po_line(self):
        order = self.hm_so_lie
        if order:
            if order.state2 =="invoiced":
                raise UserError("Vous ne pouvez pas ajouter cette ligne au SO car son statut d'intervention est 'Facturé.")

            sale_order_line = self.env['sale.order.line'].with_context(skip_procurement=True).create([
                {
                    'display_type': False,
                    'name': self.name,
                    'product_template_id': self.product_tmpl_id.id,
                    'product_id': self.product_id.id,
                    'product_uom': self.product_uom.id,
                    'product_uom_qty': self.product_qty,
                    'order_id': order.id,
                    'is_po_emport': True,
                }
            ])
            self.sale_line_id = sale_order_line.id
            sale_order_line._compute_price_unit()
            sale_order_line._compute_amount()
