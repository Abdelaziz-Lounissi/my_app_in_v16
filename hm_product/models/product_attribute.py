# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import re

class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    @api.model
    def track_products_fields_extra_price(self):
        for record in self:
            if record._context.get('old_values'):
                old_vals = record._context['old_values'].get(record.id, {})

                # Multi Variant Track process
                if 'price_extra' in old_vals:
                    for variant in self.ptav_product_variant_ids:
                        currency_symbol = variant.currency_id.symbol
                        new_price_extra = "%.2f" % record.price_extra
                        old_price_extra = "%.2f" % old_vals['price_extra']
                        if old_price_extra != new_price_extra:
                            variant.message_post(body=_("""<div class="o_thread_message_content">
                                                            <ul class="o_mail_thread_message_tracking">
                                                                <li> Sales Price:
                                                                    <span> %.2f %s </span>
                                                                        <span class="fa fa-long-arrow-right" role="img" aria-label="Changed" title="Changed"></span>
                                                                            <span> %.2f %s </span>
                                                                </li>
                                                            </ul>
                                                        </div>""")
                                                     % (old_vals['price_extra'] + variant.list_price,
                                                        currency_symbol,
                                                        record.price_extra + variant.list_price,
                                                        currency_symbol
                                        ))
