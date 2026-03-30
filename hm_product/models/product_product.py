# -*- coding: utf-8 -*-
# Merge module sale_custom

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = "product.product"

    external_id = fields.Char('External ID', compute='_get_external_id')
    active = fields.Boolean(default=True, tracking=True)
    executed = fields.Boolean('Executed', default=False)
    equivalent_product_ids = fields.Many2many('product.template', related='product_tmpl_id.equivalent_product_ids', string='Equivalent Products', related_sudo=True)

    def open_equivalent_product(self):
        """ In case if the user want to update the equivalent,
         Redirect to the related product.template,
         equivalent are based on product.template object"""
        self.ensure_one()
        return {'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'view_mode': 'form',
                'res_id': self.product_tmpl_id.id,
                'target': 'current',
                }

    def _get_external_id(self):
        res = self.get_external_id()
        for record in self:
            record['external_id'] = res.get(record.id)

    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """
        # description=''
        # name = self.display_name.replace('[%s]' % self.code, '')

        attribute = self.product_template_attribute_value_ids or ''
        name = ''
        if attribute:
            name = "[" + str(attribute[0].name) + "]"
        if self.description_sale:
            name += " " + self.description_sale
        if name == '':
            name = ' '
        return name

    @api.onchange('description_sale')
    def onchange_description_sale_sale(self):
        if self.description_sale and self.product_variant_id:
            sale_order_lines = self.env['sale.order.template.line'].search(
                [('product_id', '=', self.product_variant_id.id)])
            description = self.description_sale
            for line in sale_order_lines:
                line.write({'name': description})

    # Adapter la recherche d'article par nom/fabricant/supplier code
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []
        results = super(ProductProduct, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)
        all_product_ids = set(results)
        if name:
            search_domain = ['|', ('hm_manufacturer_reference', '=', name), ('seller_ids.product_code', '=', name)]
            new_product_ids = self.sudo().search(search_domain, limit=limit)
            all_product_ids.update(new_product_ids.ids)
        return list(all_product_ids)

    @api.model
    def track_products_fields_standard_price(self):
        for record in self:
            currency_symbol = record.currency_id.symbol
            new_standard_price = "%.2f" % record.standard_price

            if record._context.get('old_values'):
                old_vals = record._context['old_values'].get(record.id, {})

                # No variant Track process
                if 'standard_price' in old_vals:
                    old_standard_price = "%.2f" % old_vals['standard_price']

                    if old_standard_price != new_standard_price and record.product_tmpl_id.product_variant_count == 1:
                        record.product_tmpl_id.message_post(body=_("""<div class="o_thread_message_content">
                                                                        <ul class="o_mail_thread_message_tracking">
                                                                            <li> Cost:
                                                                                <span> %.2f %s </span>
                                                                                    <span class="fa fa-long-arrow-right" role="img" aria-label="Changed" title="Changed"></span>
                                                                                        <span> %s %s </span>
                                                                            </li>
                                                                        </ul>
                                                                    </div>""")
                                                                 % (old_vals['standard_price'],
                                                                    currency_symbol,
                                                                    new_standard_price,
                                                                    currency_symbol
                                                            ))
                        record.message_post(body=_("""<div class="o_thread_message_content">
                                                        <ul class="o_mail_thread_message_tracking">
                                                            <li> Cost:
                                                                <span> %.2f %s </span>
                                                                    <span class="fa fa-long-arrow-right" role="img" aria-label="Changed" title="Changed"></span>
                                                                        <span> %s %s </span>
                                                            </li>
                                                        </ul>
                                                    </div>""")
                                                 % (old_vals['standard_price'],
                                                    currency_symbol,
                                                    new_standard_price,
                                                    currency_symbol
                                            ))

                    # Multi variant Track process
                    if record.product_tmpl_id.product_variant_count > 1 and old_standard_price != new_standard_price:
                        record.message_post(body=_("""<div class="o_thread_message_content">
                                                        <ul class="o_mail_thread_message_tracking">
                                                            <li> Cost:
                                                                <span> %.2f %s </span>
                                                                    <span class="fa fa-long-arrow-right" role="img" aria-label="Changed" title="Changed"></span>
                                                                        <span> %s %s </span>
                                                            </li>
                                                        </ul>
                                                    </div>""")
                                                 % (old_vals['standard_price'],
                                                    currency_symbol,
                                                    new_standard_price,
                                                    currency_symbol
                                            ))

    def update_bom_template_cost_sale_price(self):
        bom_line_obj = self.env['mrp.bom.line']

        context = self.env.context
        if context.get('upt_from_product', False):
            for variant in self:
                lines = bom_line_obj.search([('product_id', '=', variant.id)])
                for bom in lines.mapped('bom_id'):
                    tot_price = 0
                    for line in bom.bom_line_ids:
                        if line._skip_bom_line(variant):
                            continue
                        lst_price = line.product_id.lst_price
                        tot_price += lst_price * line.product_qty

                    product_tmpl_id = bom.product_tmpl_id
                    if len(product_tmpl_id.product_variant_ids) > 1:
                        product_tmpl_id.with_context(product_tmpl_id=product_tmpl_id).update_product_variants_cost_price_extra()
                    else:
                        # update template sale price
                        bom.product_tmpl_id.write({'list_price': tot_price})
                        # Actually update the standard price.
                        product_tmpl_id.action_bom_cost()

        elif context.get('upt_from_bom_line', False):
            for variant in self:
                tot_price = 0
                product_tmpl_id = variant.product_tmpl_id
                for line in product_tmpl_id.bom_ids.bom_line_ids:
                    if line._skip_bom_line(variant):
                        continue
                    lst_price = line.product_id.lst_price
                    tot_price += lst_price * line.product_qty

                # update template sale price
                product_tmpl_id.write({'list_price': tot_price})
                # Actually update the standard price.
                product_tmpl_id.action_bom_cost()

    def update_product_sale_description(self):
        template_line_ids = self.env['sale.order.template.line'].search([('product_id', '=', self.id)])
        langs = ['nl_BE', 'en_US', 'fr_FR']

        for template_line in template_line_ids:
            template_line.write({'name': self.description_sale})
            for lang in [x for x in langs if x != self.env.user.lang]:
                template_line.with_context(lang=lang).write(
                    {'name': self.with_context(lang=lang).description_sale})

