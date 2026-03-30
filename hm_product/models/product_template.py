# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import operator as py_operator
import logging
import requests
from io import BytesIO
import base64

_logger = logging.getLogger(__name__)
import operator as py_operator
from odoo.osv import expression

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne,
}


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _order = "default_code,name"

    # TODO: debug, do we still need it?
    # x_studio_categorie_fournisseur
    hm_supplier_category = fields.Char(string='Catégorie Fournisseur', store=True, translate=False,
                                       index=False, copy=False)

    # TODO: debug, for later; task id 13388
    # x_studio_fiche_technique
    hm_technical_sheet = fields.Html(string='Fiche technique', store=True, copy=False, index=False,
                                     translate=False)
    hm_technical_sheet_1 = fields.Char(string='Fiche technique 1', store=True, copy=False, index=False,
                                       translate=False)
    hm_technical_sheet_2 = fields.Char(string='Fiche technique 2', store=True, index=False, copy=False,
                                       translate=False)
    hm_technical_sheets_ids = fields.Many2many('hm.technical.sheets', 'product_template_fiches_techniques',
                                               'template_id', 'fiche_techniques_id',
                                               string='Fiches techniques',
                                               store=True, index=False, copy=False)
    hm_image_url = fields.Char(string='Image URL 1', store=True, copy=False, index=False, translate=False)
    hm_image_url_2 = fields.Char(string='Image URL 2', store=True, copy=False, index=False, translate=False)
    hm_image_url_3 = fields.Char(string='Image URL 3', store=True, copy=False, index=False, translate=False)
    hm_brand = fields.Char(string='Marque', store=True, copy=False, index=False, translate=False)
    hm_modified_price = fields.Char(string='Prix modifié', store=True, copy=False, index=False, translate=False)
    hm_radiator_power_kw = fields.Float(string='Puissance radiateur (W)', store=True, index=False,
                                        copy=False)
    hm_manufacturer_reference = fields.Char(string='Référence fabricant', store=True, copy=False, index=False,
                                            translate=False)

    equivalent_product_ids = fields.Many2many('product.template', compute="_compute_other_equivalent_product", string='Equivalent Products')
    equivalent_id = fields.Many2one('hm.product.equivalent', copy=False, string='Equivalent')
    hm_is_real_picture = fields.Boolean('Real picture?', default=False, help="A real picture?")
    origin = fields.Selection([("facq", "Facq"), ("vam", "VAM"), ("buderus", "Buderus")], string='Origin', store=True, copy=False, index=False, translate=False)
    supplier_count = fields.Integer(compute="_compute_supplier_count", string='Has more than one supplier',  search='_for_supplier_count', store=False, copy=False, index=False, translate=False)
    external_id = fields.Char('External ID', compute='_get_external_id')
    executed = fields.Boolean('Executed', default=False)
    can_remove_equivalent = fields.Boolean(compute="_compute_can_remove_equivalent", string='Remove Equivalent', copy=False, search='_for_remove_equivalent_search', index=True, translate=False)
    can_add_equivalent = fields.Boolean(compute="_compute_can_add_equivalent", string='Add Equivalent', copy=False,  search='_for_add_equivalent_search',  index=True, translate=False)
    equivalent_filter = fields.Boolean(compute="_compute_equivalent_filter", search='_for_equivalent_filter', string='Equivalent filter')
    equivalent_green_color = fields.Boolean(compute="_compute_equivalent_color", string='Green', copy=False,   index=True, translate=False)
    facq_vm_filter = fields.Boolean(compute="_compute_facq_vm_filter", search='_for_facq_vm_filter', string='Facq VM', copy=False, index=False, default=False)
    can_image_1024_be_zoomed = fields.Boolean("Can Image 1024 be zoomed", compute='_compute_can_image_1024_be_zoomed', store=True)
    sale_order_confirmed_count = fields.Integer(compute='_compute_sale_order_confirmed')
    purchase_order_confirmed_count = fields.Integer(compute='_compute_purchase_order_confirmed')
    hm_maintain_SO_desc_and_cost_on_PO = fields.Boolean('Maintenir la description et le coût du SO sur le PO', default=False)
    sku = fields.Char("SKU")
    hm_current_discount = fields.Float(string='Current discount', readonly=True,
                                       compute='_compute_current_discount',
                                       copy=False, index=False, store=False)

    def _compute_sale_order_confirmed(self):
        for rec in self:
            sale_ids = []
            product_variant_ids = self.product_variant_ids.ids
            if product_variant_ids:
                sale_line_ids = self.env['sale.order.line'].search(
                    [('product_id', 'in', product_variant_ids), ('state', '=', 'sale')])

                sale_ids = sale_line_ids.mapped('order_id').ids
            rec.sale_order_confirmed_count = len(sale_ids)

    def _compute_purchase_order_confirmed(self):
        for rec in self:
            po_ids = []
            product_variant_ids = self.product_variant_ids.ids
            canceled_state2_pos = [
                self.env.ref('hm_purchase.purchase_stage3_po_technicien').id,
                self.env.ref('hm_purchase.purchase_stage6_po_marchandise').id,
                self.env.ref('hm_purchase.purchase_stage3_po_emport_marchandise').id,
                self.env.ref('hm_purchase.purchase_stage3_po_commission').id,
                self.env.ref('hm_purchase.purchase_stage5_po_frais').id
            ]

            if product_variant_ids:
                po_line_ids = self.env['purchase.order.line'].search(
                    [('product_id', 'in', product_variant_ids), ('order_id.state', '=', 'purchase'),
                     ('order_id.stage2_id', 'not in', canceled_state2_pos)])
                po_ids = po_line_ids.mapped('order_id').ids
            rec.purchase_order_confirmed_count = len(po_ids)

    @api.depends('image_1920', 'image_1024')
    def _compute_can_image_1024_be_zoomed(self):
        for template in self:
            try:
                template.can_image_1024_be_zoomed = template.image_1920 and tools.is_image_size_above(template.image_1920, template.image_1024)
            except Exception:
                template.can_image_1024_be_zoomed = False

    def _for_facq_vm_filter(self, operator, value):
        ids = []
        for product in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](product['facq_vm_filter'], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def _for_equivalent_filter(self, operator, value):
        ids = []
        for product in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](product['equivalent_filter'], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def _for_supplier_count(self, operator, value):
        ids = []
        for product in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](product['supplier_count'], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def _for_add_equivalent_search(self, operator, value):
        ids = []
        for product in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](product['can_add_equivalent'], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def _for_remove_equivalent_search(self, operator, value):
        ids = []
        for product in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](product['can_remove_equivalent'], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def _get_external_id(self):
        res = self.get_external_id()
        for record in self:
            record['external_id'] = res.get(record.id)

    @api.depends('can_add_equivalent', 'can_remove_equivalent', 'equivalent_id')
    def _compute_equivalent_filter(self):
        for product in self:
            product.equivalent_filter = True
            if not product.can_remove_equivalent and not product.can_add_equivalent:
                product.equivalent_filter = False

    def _compute_can_add_equivalent(self):
        for product in self:
            product.can_add_equivalent = False
            active_id = product.env.context.get('active_id')
            product_id = product.browse(active_id)
            if product_id.equivalent_id and not product.equivalent_id:
                product.can_add_equivalent = True
            elif not product_id.equivalent_id:
                product.can_add_equivalent = True

    def _compute_can_remove_equivalent(self):
        for product in self:
            product.can_remove_equivalent = False
            active_id = product.env.context.get('active_id')
            product_id = product.browse(active_id)
            if product_id.equivalent_id and product.equivalent_id and product_id.equivalent_id.id == product.equivalent_id.id:
                product.can_remove_equivalent = True

    def _compute_equivalent_color(self):
        for product in self:
            equivalent_green_color = False
            if product.can_add_equivalent is not False or (product.can_add_equivalent is False and product.can_remove_equivalent is not False):
                active_id = product.env.context.get('active_id')
                product_id = product.browse(active_id)
                if product_id.equivalent_id and product.equivalent_id and product_id.equivalent_id.id == product.equivalent_id.id:
                    equivalent_green_color = True
                else:
                    equivalent_green_color = False
            product.equivalent_green_color = equivalent_green_color

    @api.depends('seller_ids')
    def _compute_supplier_count(self):
        for product in self:
            product.supplier_count = len(product.seller_ids.ids) or 0

    @api.depends('seller_ids', 'seller_ids.partner_id', 'seller_ids.sequence')
    def _compute_facq_vm_filter(self):
        for product in self:
            product.facq_vm_filter = False
            if len(product.seller_ids.ids) == 2:
                seller_ids = product.seller_ids.mapped('partner_id').ids
                if 108 in seller_ids and 175 in seller_ids:
                    product.facq_vm_filter = True

    def open_equivalent_product(self):
        view_id = self.env.ref('hm_product.hm_product_select_equivalent_tree_view')
        return {
            'name': ('Equivalent'),
            'res_model': 'product.template',
            'res_id': self.id,
            'view_id': view_id.id,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'target': 'new',
            'nodestroy': True,
            'domain': [('id', '!=', self.id)],
            'context': {'search_default_equivalent_product': 1}
        }

    def add_equivalent_product(self):
        active_product = self.env.context.get('active_id', False)
        if active_product:
            main_product = self.browse(active_product)
            if self.equivalent_id:
                main_product.equivalent_id = self.equivalent_id.id
            elif main_product.equivalent_id:
                self.equivalent_id = main_product.equivalent_id and main_product.equivalent_id.id or False
            else:
                equivalent_id = self.env['hm.product.equivalent'].create({'name':'EQV'})
                equivalent_id.name = 'EQV' + str(equivalent_id.id)
                main_product.equivalent_id = equivalent_id.id
                self.equivalent_id = equivalent_id.id

    def remove_equivalent_product(self):
        active_product = self.env.context.get('active_id', False)
        if active_product:
            main_product = self.browse(active_product)
            if len(main_product.equivalent_product_ids) == 1:
                main_product.equivalent_id = False
        self.equivalent_id = False

    @api.depends('equivalent_id')
    def _compute_other_equivalent_product(self):
        for product in self:
            equivalents = []
            if product.equivalent_id:
                equivalents = self.search([('equivalent_id', '=', product.equivalent_id.id), ('id', '!=', product.id)]).ids
            product.equivalent_product_ids = [(6, 0, equivalents)]

    @api.onchange('description_sale')
    def onchange_description_sale_sale(self):
        if self.description_sale and self.product_variant_id:
            sale_order_lines = self.env['sale.order.template.line'].search(
                [('product_id', '=', self.product_variant_id.id)])
            description = self.description_sale
            for line in sale_order_lines:
                line.write({'name': description})

    # update the variants extra prices based on template BOM.
    # with this feature Odoo will consider that each variant own a price (not based on template).
    @api.model
    # def update_product_extra_cost(self):
    def update_product_variants_cost_price_extra(self):
        context = self.env.context
        templates = context.get('product_tmpl_id', False)
        if not templates:
            templates = self.env['product.template'].search([('bom_ids', '!=', False)])
        bom_obj = self.env['mrp.bom']
        for template in templates:
            bom = bom_obj.search([('product_tmpl_id', '=', template.id)], limit=1)
            for variant in template.product_variant_ids:
                shared_products = 0
                for line in bom.bom_line_ids.filtered(lambda x: not x.bom_product_template_attribute_value_ids):
                    shared_products += line.product_qty * line.hm_lst_price

                for attribute in variant.product_template_attribute_value_ids:
                    total_by_attribute = 0
                    for line in bom.bom_line_ids:
                        if attribute in line.bom_product_template_attribute_value_ids:
                            total_by_attribute += line.product_qty * line.hm_lst_price
                    attribute.price_extra = shared_products + total_by_attribute

                # Set template sale price to 0
                template.write({'list_price': 0})

                # Actually update the standard price.
                variant._set_price_from_bom()

    def get_image_from_url(self, url_final):
        try:
            response = requests.get(url_final)
            image_base64 = base64.b64encode(BytesIO(response.content).getvalue())
            return image_base64
        except:
            return False
            _logger.warning("Product ID: %s > (Bad Image)" % self.id)

    # ----------------------------------------------------------------------------------------------------------
    # TODO:
    def run_update_bom_template_cost_sale_price(self):
        for product_tmpl_id in self:
            product_tmpl_id.product_variant_ids.with_context(upt_from_product=True).update_bom_template_cost_sale_price()

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if ('list_price' in vals and vals.get('list_price') != 0) or 'standard_price' in vals:
            self.run_update_bom_template_cost_sale_price()
        if not vals.get('image_1920'):
            image_base64 = False
            if vals.get('hm_image_url'):
                image_base64 = self.get_image_from_url(vals.get('hm_image_url'))
            elif vals.get('hm_image_url_2') and not self.hm_image_url:
                image_base64 = self.get_image_from_url(vals.get('hm_image_url_2'))
            elif vals.get('hm_image_url_3') and not self.hm_image_url_2:
                image_base64 = self.get_image_from_url(vals.get('hm_image_url_3'))
            if image_base64:
                try:
                    self.image_1920 = image_base64
                except:
                    pass
        return res

    @api.model_create_multi
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        for values in vals:
            if not values.get('image_1920'):
                image_base64 = False
                if values.get('hm_image_url') :
                    image_base64 = self.get_image_from_url(values.get('hm_image_url'))
                elif values.get('hm_image_url_2') and not self.hm_image_url:
                    image_base64 = self.get_image_from_url(values.get('hm_image_url_2'))
                elif values.get('hm_image_url_3') and not self.hm_image_url_2:
                    image_base64 = self.get_image_from_url(values.get('hm_image_url_3'))
                if image_base64:
                    try:
                        res.image_1920 = image_base64
                    except:
                        pass
        return res


    @api.depends('list_price', 'standard_price')
    def _compute_current_discount(self):
        for record in self:
            if record.list_price != 0:
                record['hm_current_discount'] = (1 - (record.standard_price / record.list_price)) * 100
            else:
                record['hm_current_discount'] = 0

    @api.model
    def track_products_fields_list_price(self):
        for record in self:
            currency_symbol = record.currency_id.symbol
            new_list_price = "%.2f" % record.list_price
            if record._context.get('old_values'):
                old_vals = record._context['old_values'].get(record.id, {})

                # No variant Track process
                if 'list_price' in old_vals:
                    old_list_price = "%.2f" % old_vals['list_price']
                    if old_list_price != new_list_price and record.product_variant_count == 1:
                        record.product_variant_ids[0].message_post(body=_("""<div class="o_thread_message_content">
                                                                                <ul class="o_mail_thread_message_tracking">
                                                                                    <li> Sales Price:
                                                                                        <span> %.2f %s </span>
                                                                                            <span class="fa fa-long-arrow-right" role="img" aria-label="Changed" title="Changed"></span>
                                                                                                <span> %s %s </span>
                                                                                    </li>
                                                                                </ul>
                                                                            </div>""")
                                                                             % (old_vals['list_price'],
                                                                                currency_symbol,
                                                                                new_list_price,
                                                                                currency_symbol
                                                                    ))
                        record.message_post(body=_("""<div class="o_thread_message_content">
                                                        <ul class="o_mail_thread_message_tracking">
                                                            <li> Sales Price:
                                                                <span> %.2f %s </span>
                                                                    <span class="fa fa-long-arrow-right" role="img" aria-label="Changed" title="Changed"></span>
                                                                        <span> %s %s </span>
                                                            </li>
                                                        </ul>
                                                    </div>""")
                                                     % (old_vals['list_price'],
                                                        currency_symbol,
                                                        new_list_price,
                                                        currency_symbol
                                            ))

    @api.onchange('hm_maintain_SO_desc_and_cost_on_PO')
    def _onchange_hm_maintain_SO_desc_and_cost_on_PO(self):
        for variant in self.product_variant_ids:
            if self.hm_maintain_SO_desc_and_cost_on_PO:
                variant.hm_maintain_SO_desc_and_cost_on_PO = self.hm_maintain_SO_desc_and_cost_on_PO

    def action_view_sale_order_confirmed(self):
        product_variant_ids = self.product_variant_ids.ids
        sale_line_ids = self.env['sale.order.line'].search([
            ('product_id', 'in', product_variant_ids),
            ('state', '=', 'sale')
        ])

        if sale_line_ids:
            sale_orders = sale_line_ids.mapped('order_id')

            action = self.env.ref('sale.action_orders').read()[0]
            action['domain'] = [('id', 'in', sale_orders.ids)]
            if len(sale_orders) == 1:
                action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
                action['res_id'] = sale_orders[0].id
            return action

    def action_view_purchase_order_confirmed(self):
        canceled_stage_ids = [
            self.env.ref('hm_purchase.purchase_stage3_po_technicien').id,
            self.env.ref('hm_purchase.purchase_stage6_po_marchandise').id,
            self.env.ref('hm_purchase.purchase_stage3_po_emport_marchandise').id,
            self.env.ref('hm_purchase.purchase_stage3_po_commission').id,
            self.env.ref('hm_purchase.purchase_stage5_po_frais').id
        ]
        product_variant_ids = self.product_variant_ids.ids
        po_line_ids = self.env['purchase.order.line'].search([
            ('product_id', 'in', product_variant_ids),
            ('order_id.state', '=', 'purchase'),
            ('order_id.stage2_id', 'not in', canceled_stage_ids)
        ])
        if po_line_ids:
            po_ids = po_line_ids.mapped('order_id').ids
            action = self.env.ref('purchase.purchase_form_action').read()[0]
            action['domain'] = [('id', 'in', po_ids)]
            if len(po_ids) == 1:
                action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
                action['res_id'] = po_ids[0]
            return action

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        results = super(ProductTemplate, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)
        old_product_ids = set(results)
        domain = expression.OR([
            [('sku', '=', name)],
            [('default_code', operator, name)],
            [('name', operator, name)],
            [('hm_manufacturer_reference', '=', name)],
            [('seller_ids.product_code', '=', name)]
        ])
        combined_domain = expression.AND([domain, args or []])
        product_ids = self._search(combined_domain, limit=limit, access_rights_uid=name_get_uid)
        if product_ids:
            all_product_ids = old_product_ids.union(product_ids)
        else:
            all_product_ids = old_product_ids
        return list(all_product_ids)

    def update_product_tmpl_sale_description(self):
        for product in self.product_variant_ids:
            product.update_product_sale_description()
