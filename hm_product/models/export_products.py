# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
from io import BytesIO
import base64
import xlsxwriter
import xlrd

class ProductTemplateExport(models.Model):
    _name = "product.template.export"
    _description = "Product Template Export"

    file = fields.Binary()
    type = fields.Selection(selection=[("is_used", "Is used"), ("not_used", "is not used")], default='is_used',
                            string="Product")
    list = fields.Selection(
        selection=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6"), ("7", "7"), ("8", "8"),
                   ("9", "9"), ("10", "10"), ("11", "11"), ("12", "12"), ("13", "13"),("14", "14"),("15", "15"),("16", "16"),("17", "17"),("18", "18"),("19", "19"),("20", "20")], default='1', required='1', string="List")

    def archive_process(self):
        if self.file:
            file_data = base64.b64decode(self.file)
            wb = xlrd.open_workbook(file_contents=file_data)
            _logger.info('**** Start process : %s ' % self.type)

            for sheet in wb.sheets():
                for row in range(sheet.nrows):
                    if row == 0:
                        continue
                    for col in range(sheet.ncols):
                        value = sheet.cell(row, col).value
                        if self.type == 'is_used':
                            _logger.info('**** Product ID %s ' % int(value))
                            # => archiver product.supplierinfo facq
                            record = self.env['product.product'].browse(int(value))
                            facq_id = record.seller_ids.filtered(lambda x: x.name.id == 175)
                            facq_id.write({'active': False})
                        else:
                            # => archiver product.template
                            # => archiver product.product
                            # => archiver product.supplierinfo facq & VM
                            _logger.info('**** Product ID %s ' % int(value))
                            record = self.env['product.product'].browse(int(value))
                            record.write({'active': False})
                            record.product_tmpl_id.write({'active': False})
                            record.product_tmpl_id.seller_ids.write({'active': False})

    def generate_export_product_product_excel(self):
        file_name = _('export_product_variants.xlsx')
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        rw = 1
        cl = 0
        k = 0
        heading_format = workbook.add_format({'align': 'center',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 12})
        text_format = workbook.add_format({'align': 'right'})
        worksheet = workbook.add_worksheet('products export')
        width = len("Prise en charge et déplacement technicien solaire")
        products = self.env['product.product'].search([])

        if self.list == '1':
            products = products[0:7000]
        elif self.list == '2':
            products = products[7001:14000]
        elif self.list == '3':
            products = products[14001:21000]
        elif self.list == '4':
            products = products[21001:28000]
        elif self.list == '5':
            products = products[28001:35000]
        elif self.list == '6':
            products = products[35001:42000]
        elif self.list == '7':
            products = products[42001:49000]
        elif self.list == '8':
            products = products[49001:56000]
        elif self.list == '9':
            products = products[56001:63000]
        elif self.list == '10':
            products = products[63001:70000]
        elif self.list == '11':
            products = products[70001:77000]
        elif self.list == '12':
            products = products[77001:84000]
        elif self.list == '13':
            products = products[84001:91000]
        elif self.list == '14':
            products = products[91001:98000]
        elif self.list == '15':
            products = products[98001:105000]
        elif self.list == '16':
            products = products[105001:112000]
        elif self.list == '17':
            products = products[112001:119000]
        elif self.list == '18':
            products = products[119001:126000]
        elif self.list == '19':
            products = products[126001:133000]
        elif self.list == '20':
            products = products[133001:140000]

        max_list = str(int(self.list) +1)
        if max_list == 20:
            max_list = 1
        self.list = max_list
        title = ['Variant External ID', 'Template External ID', 'ID', 'Article', 'Référence interne', 'Nom',
                 'SKU', 'FIXED SKU', 'Référence fabricant', 'Code-barres', 'Coût', 'Unité de mesure', 'Prix',
                 'Prix de vente', 'Prix public', 'Prix modifié', 'Prix spécial contrat cadre', 'Prime supplier', 'Is equivalent']
        col = 0
        j = 0
        for j, t in enumerate(title):
            worksheet.write(0, col + j, t, heading_format)
            worksheet.set_column(0, col + j, width)
            j += 1
        count = 0
        for product in products:
            list_variant = []
            count += 1
            worksheet.write(rw + k, cl, str(product.external_id))
            worksheet.write(rw + k, 1, str(product.product_tmpl_id.external_id))
            worksheet.write(rw + k, 2, product.id)
            worksheet.write(rw + k, 3, str(product.product_variant_id.display_name))
            worksheet.write(rw + k, 4, str(product.default_code) if product.default_code else '')
            worksheet.write(rw + k, 5, str(product.display_name))
            worksheet.write(rw + k, 6, str(product.sku) if product.sku else '')
            worksheet.write(rw + k, 7, str(product.sku) if product.sku else '')
            worksheet.write(rw + k, 8,
                            str(product.hm_manufacturer_reference) if product.hm_manufacturer_reference else '')
            worksheet.write(rw + k, 9, str(product.barcode) if product.barcode else '')
            worksheet.write(rw + k, 10, str('{0:.2f}'.format(product.standard_price)).replace('.', ','), text_format)
            worksheet.write(rw + k, 11, str(product.uom_id.display_name))
            worksheet.write(rw + k, 12, str('{0:.2f}'.format(product.price)).replace('.', ','), text_format)
            worksheet.write(rw + k, 13, str('{0:.2f}'.format(product.list_price)).replace('.', ','), text_format)
            worksheet.write(rw + k, 14, str('{0:.2f}'.format(product.lst_price)).replace('.', ','), text_format)
            worksheet.write(rw + k, 15, str(product.hm_modified_price) if product.hm_modified_price else 0.00,
                            text_format)
            worksheet.write(rw + k, 16, str('{0:.2f}'.format(product.seller_ids[0].hm_special_price)).replace('.', ',')
            if product.seller_ids else 0.0, text_format)
            worksheet.write(rw + k, 17, str(product.seller_ids[0].name.name) if product.seller_ids else '')
            is_equivalent = 'N'
            if product.equivalent_id:
                is_equivalent = 'Y'
            worksheet.write(rw + k, 18, is_equivalent)
            k += 1
        workbook.close()
        file_download = base64.b64encode(fp.getvalue())
        fp.close()
        attach_id = self.env['report.excel'].create({
            'name': file_name,
            'file_download': file_download,
        })
        return {
            'name': file_name,
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=report.excel&id=" + str(
                attach_id.id) + "&filename_field=file_name&field=file_download&download=true&filename=" + file_name,
            'target': 'new'
        }

    def generate_export_product_supplier_info_excel(self):
        file_name = _('export_supplier_info.xlsx')
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        rw = 1
        cl = 0
        k = 0
        heading_format = workbook.add_format({'align': 'center',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 12})
        text_format = workbook.add_format({'align': 'right'})
        worksheet = workbook.add_worksheet('products supplier info export')
        width = len("Prise en charge et déplacement technicien solaire")
        product_supplierinfo_ids = self.env['product.supplierinfo'].search([('active', '=', True)])
        title = ['External ID', 'Supplier', 'Product Template', "Product Variant", 'SKU', 'fabricant', "code fabricant",
                 "Prix importé", "gross price", "Prix spécial contrat cadre", "Prix"]
        col = 0
        j = 0
        for j, t in enumerate(title):
            worksheet.write(0, col + j, t, heading_format)
            worksheet.set_column(0, col + j, width)
            j += 1
        count = 0
        for product_supplierinfo in product_supplierinfo_ids:
            count += 1
            worksheet.write(rw + k, cl, str(product_supplierinfo.external_id))
            worksheet.write(rw + k, 1, str(product_supplierinfo.name.name))
            worksheet.write(rw + k, 2,
                            str(product_supplierinfo.product_tmpl_id.external_id) if product_supplierinfo.product_tmpl_id else '')
            worksheet.write(rw + k, 3,
                            str(product_supplierinfo.product_id.external_id) if product_supplierinfo.product_id else '')
            worksheet.write(rw + k, 4, str(product_supplierinfo.product_code) or '')
            worksheet.write(rw + k, 5, str(product_supplierinfo.manufacturer) or '')
            worksheet.write(rw + k, 6, str(product_supplierinfo.manufacturer_code) or '')
            worksheet.write(rw + k, 7, str(product_supplierinfo.hm_imported_price) or '')
            worksheet.write(rw + k, 8, str(product_supplierinfo.gross_price) or '')
            worksheet.write(rw + k, 9, str(product_supplierinfo.hm_special_price) or '')
            worksheet.write(rw + k, 10, str(product_supplierinfo.price) or '')

            k += 1
        workbook.close()
        file_download = base64.b64encode(fp.getvalue())
        fp.close()
        attach_id = self.env['report.excel'].create({
            'name': file_name,
            'file_download': file_download,
        })

        return {
            'name': file_name,
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=report.excel&id=" + str(
                attach_id.id) + "&filename_field=file_name&field=file_download&download=true&filename=" + file_name,
            'target': 'new'
        }


class ReportExcel(models.TransientModel):
    _name = 'report.excel'
    _description = "Report Excel"

    name = fields.Char('File Name', size=256, readonly=True)
    file_download = fields.Binary('Download report', readonly=True)
