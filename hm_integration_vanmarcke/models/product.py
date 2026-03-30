# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging

_logger = logging.getLogger(__name__)


class SupplierInfo(models.Model):
    _name = 'product.supplierinfo'
    _inherit = ['product.supplierinfo', 'mail.thread', 'mail.activity.mixin']

    long_name_nl = fields.Text(string='Long Name NL')
    long_name_fr = fields.Text(string='Long Name FR')
    description_nl = fields.Text(string='Description NL')
    description_fr = fields.Text(string='Description FR')
    image_url_2 = fields.Char(string='Image Url 2')
    image_url_3 = fields.Char(string='Image Url 3')
    category = fields.Char(string='Category')
    parent_category = fields.Char(string='Parent category')


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # todo, fix check based on gross price
    @api.model
    def van_merge_products(self):
        facq_obj = self.env['hm.product.facq']
        vm_obj = self.env['hm.product.vanmarcke']
        hm_product_vanmarcke_ids = self.env['hm.product.vanmarcke'].search(
            [('executed', '=', False), '|', ('mark_as_created', '=', True), ('mark_as_updated', '=', True)], limit=500)
        partner_vanmarcke = self.env['res.partner'].search([('id', '=', 108)], limit=1)
        product_template_obj = self.env['product.template']
        product_supplierinfo_obj = self.env['product.supplierinfo']
        vm_id = self.env['hm.product.vanmarcke.import'].search([('import_state', '=', 'import_in_progress')])

        _logger.info("--************************* Start of 'Van Marcke - Update Heat Me Catalog with Van Marcke Catalog' *******************************")
        if hm_product_vanmarcke_ids:
            # Create a new category "TO BE MOVED" for new products if it does not exist.
            product_category_to_be_moved = self.env['product.category'].search([('name', '=', 'TO BE MOVED')], limit=1)
            if not product_category_to_be_moved:
                product_category_to_be_moved = self.env['product.category'].create({'name': "TO BE MOVED"})

            for hm_product_vanmarcke_id in hm_product_vanmarcke_ids:
                _logger.info('--** For hm.product.vanmarcke with ID = %s ' % hm_product_vanmarcke_id.id)

                # search with PSS key
                product_supplierinfo_ids = product_supplierinfo_obj.search(
                    [('product_code', '=', hm_product_vanmarcke_id.supplier_code), ('partner_id', '=', partner_vanmarcke.id)])
                _logger.info('-- Search matching product.supplierinfo for PSS key = %s-%s' % (partner_vanmarcke.name, hm_product_vanmarcke_id.supplier_code))

                if product_supplierinfo_ids:
                    _logger.info('-- Search with PSS key : OK ')

                    for product_supplierinfo_id in product_supplierinfo_ids:
                        _logger.info('-- Updated product.supplierinfo with ID = %s' % product_supplierinfo_id.id)
                        price = float(hm_product_vanmarcke_id.net_price)
                        if float(hm_product_vanmarcke_id.net_price) > 0 and float(
                                product_supplierinfo_id.hm_special_price) > 0:
                            price = min(float(hm_product_vanmarcke_id.net_price),
                                        float(product_supplierinfo_id.hm_special_price))
                        product_supplierinfo_id.write({'price':price or 0,
                                                       'gross_price': hm_product_vanmarcke_id.gross_price or 0})
                        product_supplierinfo_id['hm_imported_price'] = hm_product_vanmarcke_id.net_price or 0
                        product_supplierinfo_id['updated_date'] = fields.Datetime.now()
                        product_supplierinfo_id['code_ean'] = hm_product_vanmarcke_id.code_ean or ''
                        product_supplierinfo_id['parent_category'] = hm_product_vanmarcke_id.parent_category or ''
                        if not product_supplierinfo_id['source']:
                            product_supplierinfo_id['source'] = "van marcke catalog"
                        product_supplierinfo_id['name_nl'] = hm_product_vanmarcke_id.name_nl or ''
                        product_supplierinfo_id['product_name'] = hm_product_vanmarcke_id.name_fr or ''
                        product_supplierinfo_id['description_fr'] = hm_product_vanmarcke_id.description_fr or ''
                        product_supplierinfo_id['description_nl'] = hm_product_vanmarcke_id.description_nl or ''
                        product_supplierinfo_id['long_name_nl'] = hm_product_vanmarcke_id.long_name_nl or ''
                        product_supplierinfo_id['long_name_fr'] = hm_product_vanmarcke_id.long_name_fr or ''
                        # product_supplierinfo_id['fiche_nl'] = hm_product_vanmarcke_id.fiche_nl or ''
                        product_supplierinfo_id['fiche_fr'] = hm_product_vanmarcke_id.fiche_fr or ''
                        product_supplierinfo_id['image_url_1'] = hm_product_vanmarcke_id.image_url_1 or ''
                        product_supplierinfo_id['image_url_2'] = hm_product_vanmarcke_id.image_url_2 or ''
                        product_supplierinfo_id['image_url_3'] = hm_product_vanmarcke_id.image_url_3 or ''
                        product_supplierinfo_id['category'] = hm_product_vanmarcke_id.category or ''

                        product_supplierinfo_id.product_tmpl_id._compute_prime_supplier()

                else:
                    _logger.info('--    No active product.supplierinfo found')

                    if hm_product_vanmarcke_id.fabricant and hm_product_vanmarcke_id.manufacturer_code:
                        # search wih SMMC key
                        # manufacturer(supplierinfo) = brand_name(facq) = fabricant(vm)
                        _logger.info('-- Search matching product.supplierinfo for SMMC key = Facq-%s-%s' %(hm_product_vanmarcke_id.fabricant, hm_product_vanmarcke_id.manufacturer_code))
                        _logger.info('-- Search matching hm.product.facq for MMC key = %s-%s' %(hm_product_vanmarcke_id.fabricant, hm_product_vanmarcke_id.manufacturer_code))
                        _logger.info('-- Search matching hm.product.vanmarcke for MMC key = %s-%s' %(hm_product_vanmarcke_id.fabricant, hm_product_vanmarcke_id.manufacturer_code))

                        product_supplierinfo_facq_smmc_key_list = product_supplierinfo_obj.search(
                            [('manufacturer_code', '=', hm_product_vanmarcke_id.manufacturer_code),
                             ('manufacturer', '=', hm_product_vanmarcke_id.fabricant),
                             ('partner_id', '=', 175)])
                        _logger.info('--    product_supplierinfo_facq_smmc_key_list : %s ' % product_supplierinfo_facq_smmc_key_list)

                        hm_product_facq_mmc_key_list = facq_obj.search(
                            [('producer_id', '=', hm_product_vanmarcke_id.manufacturer_code),
                             ('brand_name', '=', hm_product_vanmarcke_id.fabricant)])
                        _logger.info('--    hm_product_facq_mmc_key_list : %s ' % hm_product_facq_mmc_key_list)

                        # search in VM, because VM record not created/merged in supplier info yet.
                        hm_product_van_marcke_mmc_key_list = vm_obj.search(
                            [('manufacturer_code', '=', hm_product_vanmarcke_id.manufacturer_code),
                             ('fabricant', '=', hm_product_vanmarcke_id.fabricant)])
                        _logger.info('--    hm_product_van_marcke_mmc_key_list : %s ' % hm_product_van_marcke_mmc_key_list)

                        # VM smmc key is unique!
                        create_product_template_and_product_supplierinfo = True
                        if len(hm_product_van_marcke_mmc_key_list) == 1 and len(product_supplierinfo_facq_smmc_key_list) == 1 and len(
                                hm_product_facq_mmc_key_list) == 1:
                            _logger.info('-- product.supplierinfo exists and SMMC key is unique for Facq + MMC key is unique in Facq and Van Marcke catalogs')

                            create_product_template_and_product_supplierinfo = False
                            _logger.info('-- Check if price difference <= 50% ')
                            diff_gross_price = abs((product_supplierinfo_facq_smmc_key_list.gross_price * 50) / 100)
                            check_diff_sale_price = abs(product_supplierinfo_facq_smmc_key_list.gross_price - hm_product_vanmarcke_id.gross_price) <= diff_gross_price
                            _logger.info('--    Facq supplierinfo price : %s' % product_supplierinfo_facq_smmc_key_list.gross_price)
                            _logger.info('--    VM price : %s' % hm_product_vanmarcke_id.gross_price)
                            _logger.info('--    Price difference = %s' % diff_gross_price)

                            if check_diff_sale_price:
                                _logger.info('--    Price difference <= 50% : OK')
                                _logger.info('-- Van Marcke and Facq can share the same product')
                                # check if gross_price with diff <= 50%
                                # diff gross_price < 50 %
                                # Create a new Vendor Pricelists for this article
                                _logger.info('-- Create new product.supplierinfo')
                                new_supplierinfo_id = product_supplierinfo_obj.create({
                                    'partner_id': partner_vanmarcke.id,
                                    'product_tmpl_id': product_supplierinfo_facq_smmc_key_list.product_tmpl_id.id,
                                    'product_name': hm_product_vanmarcke_id.name_fr or '',
                                    'product_code': hm_product_vanmarcke_id.supplier_code or '',
                                    'source': "van marcke catalog",
                                    'created_date': fields.Datetime.now(),
                                    'manufacturer_code': hm_product_vanmarcke_id.manufacturer_code or '',
                                    'code_ean': hm_product_vanmarcke_id.code_ean or '',
                                    'name_nl': hm_product_vanmarcke_id.name_nl or '',
                                    'long_name_nl': hm_product_vanmarcke_id.long_name_nl or '',
                                    'long_name_fr': hm_product_vanmarcke_id.long_name_fr or '',
                                    'manufacturer': hm_product_vanmarcke_id.fabricant or '',
                                    'fabricant': hm_product_vanmarcke_id.fabricant or '',
                                    'model': hm_product_vanmarcke_id.model or '',
                                    'description_nl': hm_product_vanmarcke_id.description_nl or '',
                                    'description_fr': hm_product_vanmarcke_id.description_fr or '',
                                    'image_url_1': hm_product_vanmarcke_id.image_url_1 or '',
                                    'image_url_2': hm_product_vanmarcke_id.image_url_2 or '',
                                    'image_url_3': hm_product_vanmarcke_id.image_url_3 or '',
                                    'fiche_fr': hm_product_vanmarcke_id.fiche_fr or '',
                                    'gross_price': hm_product_vanmarcke_id.gross_price or 0,
                                    'price': hm_product_vanmarcke_id.net_price or 0,
                                    'hm_imported_price': hm_product_vanmarcke_id.net_price or 0,
                                    'category': hm_product_vanmarcke_id.category or '',
                                    'parent_category': hm_product_vanmarcke_id.parent_category or '',
                                })
                                _logger.info('-- Created product.supplierinfo with ID = %s' % new_supplierinfo_id.id)
                                product_supplierinfo_facq_smmc_key_list.product_tmpl_id.set_prime_supplier()
                                product_supplierinfo_facq_smmc_key_list.product_tmpl_id._compute_prime_supplier()
                            else:
                                _logger.info('--    Price difference <= 50% : NON OK')
                                create_product_template_and_product_supplierinfo = True
                    else:
                        _logger.info('-- Manufacturer and Manufacturer Code : Undefined (False)')

                        create_product_template_and_product_supplierinfo = True

                    if create_product_template_and_product_supplierinfo:
                        # create a new article
                        _logger.info('-- Create new product.template')
                        new_product_template = product_template_obj.create({'name': hm_product_vanmarcke_id.name_fr,
                                                                            'description_sale': hm_product_vanmarcke_id.long_name_fr,
                                                                            'description': hm_product_vanmarcke_id.description_fr,
                                                                            'categ_id': product_category_to_be_moved.id,
                                                                            'type': 'consu',
                                                                            'hm_manufacturer_reference': hm_product_vanmarcke_id.manufacturer_code,
                                                                            'list_price': hm_product_vanmarcke_id.gross_price,
                                                                            'standard_price': hm_product_vanmarcke_id.net_price,
                                                                            'sku': hm_product_vanmarcke_id.supplier_code,
                                                                            'hm_image_url': hm_product_vanmarcke_id.image_url_1,
                                                                            'hm_image_url_2': hm_product_vanmarcke_id.image_url_2,
                                                                            'hm_image_url_3': hm_product_vanmarcke_id.image_url_3,
                                                                            'hm_technical_sheet_1': hm_product_vanmarcke_id.fiche_fr,
                                                                            'hm_supplier_category': hm_product_vanmarcke_id.parent_category,
                                                                            'origin': 'vam',
                                                                            })
                        _logger.info('-- Created product.template with ID = %s' % new_product_template.id)

                        # self.env.cr.execute(
                        #     "SELECT barcode FROM product_product WHERE barcode = '%s'" % hm_product_vanmarcke_id.code_ean)
                        # if len(self.env.cr.fetchall()) == 0:
                        #     new_product_template['barcode'] = hm_product_vanmarcke_id.code_ean

                        # Create a new Vendor Pricelists for this article
                        _logger.info('-- Create new product.supplierinfo')
                        new_supplierinfo_id = product_supplierinfo_obj.create({
                            'partner_id': partner_vanmarcke.id,
                            'product_tmpl_id': new_product_template.id,
                            'product_name': hm_product_vanmarcke_id.name_fr or '',
                            'product_code': hm_product_vanmarcke_id.supplier_code or '',
                            'source': "van marcke catalog",
                            'created_date': fields.Datetime.now(),
                            'manufacturer_code': hm_product_vanmarcke_id.manufacturer_code or '',
                            'code_ean': hm_product_vanmarcke_id.code_ean or '',
                            'name_nl': hm_product_vanmarcke_id.name_nl or '',
                            'long_name_nl': hm_product_vanmarcke_id.long_name_nl or '',
                            'long_name_fr': hm_product_vanmarcke_id.long_name_fr or '',
                            'manufacturer': hm_product_vanmarcke_id.fabricant or '',
                            'fabricant': hm_product_vanmarcke_id.fabricant or '',
                            'model': hm_product_vanmarcke_id.model or '',
                            'description_nl': hm_product_vanmarcke_id.description_nl or '',
                            'description_fr': hm_product_vanmarcke_id.description_fr or '',
                            'image_url_1': hm_product_vanmarcke_id.image_url_1 or '',
                            'image_url_2': hm_product_vanmarcke_id.image_url_2 or '',
                            'image_url_3': hm_product_vanmarcke_id.image_url_3 or '',
                            'fiche_fr': hm_product_vanmarcke_id.fiche_fr or '',
                            'gross_price': hm_product_vanmarcke_id.gross_price or 0,
                            'price': hm_product_vanmarcke_id.net_price or 0,
                            'hm_imported_price': hm_product_vanmarcke_id.net_price or 0,
                            'category': hm_product_vanmarcke_id.category or '',
                            'parent_category': hm_product_vanmarcke_id.parent_category or '',
                        })
                        _logger.info('-- Created product.supplierinfo with ID = %s' % new_supplierinfo_id.id)

                hm_product_vanmarcke_id.executed = True
                self.env.cr.commit()

            vm_id.import_state = "done"
            vm_id.message_post(
                body=f"""<div class="o_thread_message_content">
                            <span>Van Marcke - Step 2: Done</span>
                        </div>"""
            )
        else:
            _logger.info("-- *** There is no update in Van Marcke's catalog ***")
        _logger.info("--************************* End of 'Van Marcke - Update Heat Me Catalog with Van Marcke Catalog' ******************************")