# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"


    @api.model
    def facq_merge_products(self):
        facq_obj = self.env['hm.product.facq']
        vm_obj = self.env['hm.product.vanmarcke']
        hm_product_facq_ids = facq_obj.search(
            [('executed', '=', False), '|', ('mark_as_created', '=', True), ('mark_as_updated', '=', True)], limit=500)
        partner_facq = self.env['res.partner'].search([('id', '=', 175)], limit=1)
        product_template_obj = self.env['product.template']
        product_supplierinfo_obj = self.env['product.supplierinfo']
        _logger.info("--************************* Start of 'Facq - Step 3: Update Heat Me Catalog with Facq Catalog' *******************************")
        if hm_product_facq_ids:

            # Create a new category "TO BE MOVED" for new products if it does not exist.
            product_category_to_be_moved = self.env['product.category'].search([('name', '=', 'TO BE MOVED')], limit=1)
            if not product_category_to_be_moved:
                product_category_to_be_moved = self.env['product.category'].create({'name': "TO BE MOVED"})

            for hm_product_facq_id in hm_product_facq_ids:
                _logger.info('--** For hm.product.facq with ID = %s ' % hm_product_facq_id.id)

                # search wih PSS key
                _logger.info('-- Search matching product.supplierinfo for PSS key = %s-%s' % (partner_facq.name, hm_product_facq_id.product_id))
                product_supplierinfo_ids = product_supplierinfo_obj.search(
                    [('product_code', '=', hm_product_facq_id.product_id), ('partner_id', '=', partner_facq.id)])

                if product_supplierinfo_ids:
                    _logger.info('-- Search with PSS key : OK ')

                    for product_supplierinfo_id in product_supplierinfo_ids:
                        _logger.info('-- Updated product.supplierinfo with ID = %s' % product_supplierinfo_id.id)

                        price = float(hm_product_facq_id.net_price_tax_excluded)
                        if float(hm_product_facq_id.net_price_tax_excluded) > 0 and float(product_supplierinfo_id.hm_special_price) > 0:
                            price = min(float(hm_product_facq_id.net_price_tax_excluded), float(product_supplierinfo_id.hm_special_price))
                        product_supplierinfo_id['hm_imported_price'] = hm_product_facq_id.net_price_tax_excluded or 0
                        product_supplierinfo_id.write({'price':price, 'gross_price': hm_product_facq_id.public_price_tax_excluded or 0})
                        product_supplierinfo_id['updated_date'] = fields.Datetime.now()
                        if not product_supplierinfo_id['source']:
                            product_supplierinfo_id['source'] = "facq catalog"
                        product_supplierinfo_id['product_name'] = hm_product_facq_id.label_fr or ''
                        product_supplierinfo_id['name_nl'] = hm_product_facq_id.label_nl or ''
                        product_supplierinfo_id['image_url_1'] = hm_product_facq_id.image_url or ''
                        product_supplierinfo_id['fiche_fr'] = hm_product_facq_id.technical_sheet or ''

                        product_supplierinfo_id.product_tmpl_id._compute_prime_supplier()

                else:
                    _logger.info('--    No active product.supplierinfo found')

                    if hm_product_facq_id.brand_name and hm_product_facq_id.producer_id:
                        # search with SMMC & MMC key
                        _logger.info('-- Search matching product.supplierinfo for SMMC key = Van Marcke-%s-%s' %(hm_product_facq_id.brand_name, hm_product_facq_id.producer_id))
                        _logger.info('-- Search matching hm.product.facq for MMC key = %s-%s' %(hm_product_facq_id.brand_name, hm_product_facq_id.producer_id))
                        _logger.info('-- Search matching hm.product.vm for MMC key = %s-%s' %(hm_product_facq_id.brand_name, hm_product_facq_id.producer_id))

                        # 1.search in supplier info for VM matched SMMC.
                        # 2.get product id from the VM matched MMC, to make the merge for the new created supplier info
                        # manufacturer(supplierinfo) = brand_name(facq) = fabricant(vm)
                        product_supplierinfo_vanmarcke_smmc_key_list = product_supplierinfo_obj.search(
                            [('manufacturer_code', '=', hm_product_facq_id.producer_id),
                             ('manufacturer', '=', hm_product_facq_id.brand_name),
                             ('partner_id', '=', 108)])
                        _logger.info('--    product_supplierinfo_vanmarcke_smmc_key_list : %s ' % product_supplierinfo_vanmarcke_smmc_key_list)

                        hm_product_vanmarcke_mmc_key_list = vm_obj.search(
                            [('manufacturer_code', '=', hm_product_facq_id.producer_id),
                             ('fabricant', '=', hm_product_facq_id.brand_name)])
                        _logger.info('--    hm_product_vanmarcke_mmc_key_list : %s ' % hm_product_vanmarcke_mmc_key_list)

                        # search in facq, because facq record not created/merged in supplier info yet.
                        hm_product_facq_mmc_key_list = facq_obj.search(
                            [('producer_id', '=', hm_product_facq_id.producer_id),
                             ('brand_name', '=', hm_product_facq_id.brand_name)])
                        _logger.info('--    hm_product_facq_mmc_key_list : %s ' % hm_product_facq_mmc_key_list)

                        # Facq smmc key is unique!
                        create_product_template_and_product_supplierinfo = True
                        if len(hm_product_facq_mmc_key_list) == 1 and len(product_supplierinfo_vanmarcke_smmc_key_list) == 1 and len(hm_product_vanmarcke_mmc_key_list) == 1:
                            _logger.info('-- product.supplierinfo exists and SMMC key is unique for Van Marcke + MMC key is unique in Facq and Van Marcke catalogs')
                            create_product_template_and_product_supplierinfo = False
                            _logger.info('-- Check if price difference <= 50%')

                            public_price_tax_excluded = float(hm_product_facq_id.public_price_tax_excluded)
                            diff_gross_price = (product_supplierinfo_vanmarcke_smmc_key_list.gross_price * 50) / 100
                            check_diff_sale_price = abs(product_supplierinfo_vanmarcke_smmc_key_list.gross_price - public_price_tax_excluded) <= (diff_gross_price)
                            _logger.info('--    VM supplier info price : %s' % product_supplierinfo_vanmarcke_smmc_key_list.gross_price)
                            _logger.info('--    Facq price : %s' % public_price_tax_excluded)
                            _logger.info('--    Price difference : %s' % diff_gross_price)

                            if check_diff_sale_price:
                                _logger.info('--    Price difference <= 50% : OK')
                                _logger.info('-- Facq and Van Marcke can share the same product')

                                # check if gross_price with diff <= 50%
                                # diff gross_price < 50 %
                                # Create a new Vendor Pricelists for this article
                                _logger.info('-- Create new product.supplierinfo')
                                new_supplierinfo_id = product_supplierinfo_obj.create(
                                    {'partner_id': partner_facq.id,
                                     'product_tmpl_id': product_supplierinfo_vanmarcke_smmc_key_list.product_tmpl_id.id,
                                     'product_name': hm_product_facq_id.label_fr or '',
                                     'product_code': hm_product_facq_id.product_id or '',
                                     'source': "facq catalog",
                                     'created_date': fields.Datetime.now(),
                                     'manufacturer_code': hm_product_facq_id.producer_id or '',
                                     'name_nl': hm_product_facq_id.label_nl or '',
                                     'manufacturer': hm_product_facq_id.brand_name or '',
                                     'fabricant': hm_product_facq_id.brand_name or '',
                                     'image_url_1': hm_product_facq_id.image_url or '',
                                     'fiche_fr': hm_product_facq_id.technical_sheet or '',
                                     'gross_price': hm_product_facq_id.public_price_tax_excluded or 0,
                                     'hm_imported_price': hm_product_facq_id.net_price_tax_excluded or 0,
                                     'price': hm_product_facq_id.net_price_tax_excluded or 0,
                                     })
                                _logger.info('-- Created product.supplierinfo with ID = %s' % new_supplierinfo_id.id)

                                product_supplierinfo_vanmarcke_smmc_key_list.product_tmpl_id.set_prime_supplier()
                                product_supplierinfo_vanmarcke_smmc_key_list.product_tmpl_id._compute_prime_supplier()
                            else:
                                _logger.info('--    Price difference <= 50% : NON OK')
                                create_product_template_and_product_supplierinfo = True
                    else:
                        create_product_template_and_product_supplierinfo = True

                    if create_product_template_and_product_supplierinfo:
                        # create a new article
                        _logger.info('-- Create new product.template')

                        route_dropshipping = self.env.ref('stock_dropshipping.route_drop_shipping')
                        route_make_to_order = self.env.ref('stock.route_warehouse0_mto')
                        route_buy = self.env.ref('purchase_stock.route_warehouse0_buy')

                        new_product_template = product_template_obj.create({'name': hm_product_facq_id.label_fr,
                                                                            'categ_id': product_category_to_be_moved.id,
                                                                            'type': 'consu',
                                                                            'hm_manufacturer_reference': hm_product_facq_id.producer_id,
                                                                            'list_price': hm_product_facq_id.public_price_tax_excluded,
                                                                            'standard_price': hm_product_facq_id.net_price_tax_excluded,
                                                                            'sku': hm_product_facq_id.product_id,
                                                                            'hm_image_url': hm_product_facq_id.image_url,
                                                                            'hm_technical_sheet_1': hm_product_facq_id.technical_sheet,
                                                                            'origin': 'facq',
                                                                            'route_ids':  [(6, 0, [route_dropshipping.id, route_make_to_order.id, route_buy.id])],
                                                                            })

                        _logger.info('-- Created product.template with ID = %s' % new_product_template.id)

                        # Create a new Vendor Pricelists for this article
                        _logger.info('-- Create new product.supplierinfo')
                        new_supplierinfo_id = product_supplierinfo_obj.create(
                            {'partner_id': partner_facq.id,
                             'product_tmpl_id': new_product_template.id,
                             'product_name': hm_product_facq_id.label_fr or '',
                             'product_code': hm_product_facq_id.product_id or '',
                             'source': "facq catalog",
                             'created_date': fields.Datetime.now(),
                             'manufacturer_code': hm_product_facq_id.producer_id or '',
                             'name_nl': hm_product_facq_id.label_nl or '',
                             'manufacturer': hm_product_facq_id.brand_name or '',
                             'fabricant': hm_product_facq_id.brand_name or '',
                             'image_url_1': hm_product_facq_id.image_url or '',
                             'fiche_fr': hm_product_facq_id.technical_sheet or '',
                             'gross_price': hm_product_facq_id.public_price_tax_excluded or 0,
                             'hm_imported_price': hm_product_facq_id.net_price_tax_excluded or 0,
                             'price': hm_product_facq_id.net_price_tax_excluded or 0,
                             })
                        _logger.info('-- Created product.supplierinfo with ID = %s' % new_supplierinfo_id.id)

                hm_product_facq_id.executed = True
                self.env.cr.commit()
        else:
            _logger.info("-- *** There is no update in Facq's catalog ***")
        _logger.info("-- ************************ End of 'Facq - Step 3: Update Heat Me Catalog with Facq Catalog' **********************************")

