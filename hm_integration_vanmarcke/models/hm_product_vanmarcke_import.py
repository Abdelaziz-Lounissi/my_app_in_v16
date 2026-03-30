# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import io
import logging
import csv
from dbfread import DBF
import os
import base64
from pathlib import Path
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HmProductVanmarckeImport(models.Model):
    _name = "hm.product.vanmarcke.import"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Hm Product Van Marcke Import"

    name = fields.Char('name', compute='_compute_name')
    name_csv = fields.Char('File name', tracking=True)
    file_csv = fields.Binary('File CSV')
    name_dbf = fields.Char('File name', tracking=True)
    file_dbf = fields.Binary('File DBF')
    note_import_product_vanmarcke = fields.Text('Log', tracking=True)
    import_date = fields.Datetime('', default=lambda self: fields.datetime.now(), tracking=True)
    count_line_csv = fields.Integer('Total File Line')
    count_updated_price_csv = fields.Integer('Total updated price in csv file')
    count_updated_line_csv = fields.Integer('Total updated in csv file')
    count_created_line_csv = fields.Integer('Total created in csv file')
    count_line_dbf = fields.Integer('Total File Line')
    count_updated_price_dbf = fields.Integer('Total updated price in dbf file')
    count_updated_line_dbf = fields.Integer('Total updated in dbf file')
    count_created_line_dbf = fields.Integer('Total created in dbf file')
    check_empty_files = fields.Boolean(default=False)
    import_csv_done = fields.Boolean(default=False)
    import_dbf_done = fields.Boolean(default=False)
    import_state = fields.Selection(
        selection=[("new", "new"), ("import_in_progress", "Import in progress"), ("done", "Done"), ('fail', 'Fail')],
        string="State", tracking=True, default="new")

    def _compute_name(self):
        for record in self:
            name = '/'
            if record.import_date:
                name = "Import %s" % record.import_date.strftime('%d/%m/%Y')
            record.name = name

    @api.onchange('name_csv', 'name_dbf')
    def check_csv_dbf_extension(self):
        if self.name_csv:
            if ".csv" not in str(self.name_csv):
                raise ValidationError(_('The file has no requested extension, please check your file which must be (*.csv)'))
        if self.name_dbf:
            if ".dbf" not in str(self.name_dbf):
                raise ValidationError(_('The file has no requested extension, please check your file which must be (*.dbf)'))

    @api.constrains('check_empty_files')
    def check_required_fields(self):
        if (not self.name_csv) or (not self.name_dbf):
            raise ValidationError(_('Please select the 2 Van Marcke files (*.csv and *.dbf)'))

    def import_vm_csv(self):
        if not self.file_csv:
            raise ValidationError("File not found. Please make sure to upload a file.")

        if self.import_state == "new":
            self.import_state = 'import_in_progress'
            self.env.cr.commit()
        note_import_product_vanmarcke = ''
        HmProductVanmarcke = self.env['hm.product.vanmarcke']
        total_success_import_record = 0
        total_failed_record = 0
        list_of_failed_record = ''

        data = base64.b64decode(self.file_csv).decode('latin-1')
        csvfile = io.StringIO(data)
        parsed_csv = list(csv.reader(csvfile, delimiter=';'))

        if len(parsed_csv) == 0:
            self.message_post(
                body=f"""<div class="o_thread_message_content">
                        <span>Erreur: Le fichier CSV est vide .</span>
                    </div>"""
            )
        else:
            count = 0
            count_created = 0
            count_updated = 0
            count_price_update = 0
            list_to_create = []

            for row in parsed_csv:
                count += 1
                try:
                    row_dict = {i: value for i, value in enumerate(row)}
                    supplier_code = str(row_dict.get(0, ''))
                    if supplier_code:
                        product_exist_id = HmProductVanmarcke.sudo().search([('supplier_code', '=', supplier_code)],
                                                                            limit=1)
                        product_vals = {
                            'supplier_code': str(row_dict.get(0, '')),
                            'manufacturer_code': str(row_dict.get(1, '')),
                            'code_ean': str(row_dict.get(2, '')),
                            'name_nl': str(row_dict.get(3, '')),
                            'name_fr': str(row_dict.get(4, '')),
                            'long_name_nl': str(row_dict.get(5, '')),
                            'long_name_fr': str(row_dict.get(6, '')),
                            'fabricant': str(row_dict.get(7, '')),
                            'model': str(row_dict.get(8, '')),
                            'description_nl': str(row_dict.get(9, '')),
                            'description_fr': str(row_dict.get(10, '')),
                            'image_url_1': str(row_dict.get(11, '')),
                            'image_url_2': str(row_dict.get(12, '')),
                            'image_url_3': str(row_dict.get(13, '')),
                            'category': str(row_dict.get(14, '')),
                            'fiche_nl': str(row_dict.get(15, '')),
                            'fiche_fr': str(row_dict.get(16, '')),
                            'gross_price': float(row_dict.get(17, 0.0)),
                            'price_code': str(row_dict.get(18, '')),
                            'minimum_quantity': str(row_dict.get(19, '')),
                            'vat_code': str(row_dict.get(20, '')),
                            'parent_category': str(row_dict.get(21, '')),
                            'net_price': float(row_dict.get(22, 0.0)),
                            'check_import': True,
                            'executed': False,
                        }
                        if product_exist_id:
                            # Update product: Update (Gross Price, Net Price)
                            if (product_exist_id.gross_price != product_vals['gross_price'] or
                                    product_exist_id.net_price != product_vals['net_price']):
                                count_price_update += 1

                            if (product_exist_id.gross_price != product_vals['gross_price'] or
                                    product_exist_id.net_price != product_vals['net_price'] or
                                    product_exist_id.name_nl != product_vals['name_nl'] or
                                    product_exist_id.name_fr != product_vals['name_fr'] or
                                    product_exist_id.long_name_nl != product_vals['long_name_nl'] or
                                    product_exist_id.long_name_fr != product_vals['long_name_fr'] or
                                    product_exist_id.description_nl != product_vals['description_nl'] or
                                    product_exist_id.description_fr != product_vals['description_fr'] or
                                    product_exist_id.image_url_1 != product_vals['image_url_1'] or
                                    product_exist_id.image_url_2 != product_vals['image_url_2'] or
                                    product_exist_id.image_url_3 != product_vals['image_url_3'] or
                                    product_exist_id.category != product_vals['category'] or
                                    product_exist_id.fiche_nl != product_vals['fiche_nl'] or
                                    product_exist_id.fiche_fr != product_vals['fiche_fr']):
                                product_vals['mark_as_updated'] = True
                                product_vals['mark_as_created'] = False
                                product_exist_id.write(product_vals)
                                count_updated += 1
                                _logger.info('Update hm.product.vanmarcke: %s.' % product_vals['name_fr'])
                        else:
                            product_vals['mark_as_created'] = True
                            list_to_create.append(product_vals)
                            _logger.info('Create hm.product.vanmarcke: %s.' % product_vals['name_fr'])
                            count_created += 1
                except Exception as e:
                    total_failed_record += 1
                    list_of_failed_record += ', '.join(row)
                    _logger.error("Error: %s" % e)
                    _logger.error("Error at %s" % str(row))

            self.count_line_csv = count
            self.count_created_line_csv = count_created
            self.count_updated_line_csv = count_updated
            self.count_updated_price_csv = count_price_update

            if list_to_create:
                HmProductVanmarcke.create(list_to_create)
                total_success_import_record += 1

        self.import_csv_done = True

        self.message_post(
            body=f"""<div class="o_thread_message_content">
                        <span>Van Marcke - Step 1-1: Done</span>
                    </div>"""
        )

    def convert_dbf_csv(self):
        repertoire = '/tmp/dbf_file/'
        csv_fn = str((self.name_dbf).rsplit('.', 1)[0]) + ".csv"

        try:
            os.makedirs(repertoire, exist_ok=True)
        except OSError:
            raise ValidationError(_('Repository not found'))

        file_path = os.path.join(repertoire, self.name_dbf)
        file_csv_path = os.path.join(repertoire, csv_fn)

        with open(file_path, 'wb') as f:
            f.write(base64.decodebytes(self.file_dbf))

        table = DBF(file_path, encoding='iso-8859-1')

        with open(file_csv_path, 'w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(table.field_names)
            for record in table:
                writer.writerow(list(record.values()))
        self.import_dbf_done = True
        self.message_post(
            body=f"""<div class="o_thread_message_content">
                        <span>Van Marcke - Step 1-2: Done</span>
                    </div>"""
        )

    def import_vm_dbf_csv(self):
        if self.import_state == "new":
            self.import_state = 'import_in_progress'
            self.env.cr.commit()

        if not self.import_dbf_done:
            self.convert_dbf_csv()
        note_import_product_vanmarcke = ''
        HmProductVanmarcke = self.env['hm.product.vanmarcke']
        total_success_import_record = 0
        list_to_create = []
        repertoire = '/tmp/dbf_file/'
        csv_fn = str((self.name_dbf).rsplit('.', 1)[0]) + ".csv"
        file_csv_path = os.path.join(repertoire, csv_fn)

        with open(file_csv_path, 'r') as csv_fl:
            rows = csv.reader(csv_fl, quotechar="'", delimiter=';')
            next(rows)
            count = 0
            count_updated = 0
            count_created = 0
            count_price_update = 0

            for row in rows:
                count += 1
                row_dict = {i: value for i, value in enumerate(row)}
                supplier_code = str(row_dict.get(0, ''))
                name_fr = str(row_dict.get(1, ''))
                gross_price = float(row_dict.get(2, 0.0))
                net_price = float(row_dict.get(3, 0.0))
                vat_code = str(row_dict.get(4, ''))
                price_code = str(row_dict.get(5, ''))
                if supplier_code:
                    product_exist_id = HmProductVanmarcke.sudo().search([('supplier_code', '=', supplier_code)],
                                                                        limit=1)

                    product_vals = {
                        'supplier_code': supplier_code,
                        'name_fr': name_fr,
                        'gross_price': gross_price,
                        'price_code': price_code,
                        'vat_code': vat_code,
                        'net_price': net_price,
                        'check_import': False,
                    }

                    if product_exist_id:
                        # Update product: Update (Gross Price, Net Price)
                        if product_exist_id.gross_price != gross_price:
                            count_price_update += 1

                        if (product_exist_id.gross_price != gross_price or
                                product_exist_id.name_fr != name_fr):
                            product_vals['mark_as_updated'] = True
                            product_vals['mark_as_created'] = False
                            product_vals['executed'] = False
                            product_exist_id.write(product_vals)
                            _logger.info('Update product: %s.' % name_fr)
                            count_updated += 1

                    else:
                        count_created += 1
                        product_vals['mark_as_created'] = True
                        product_vals['executed'] = False
                        list_to_create.append(product_vals)
                        _logger.info('Append product: %s.' % name_fr)

            self.count_line_dbf = count
            self.count_updated_line_dbf = count_updated
            self.count_created_line_dbf = count_created
            self.count_updated_price_dbf = count_price_update

            if list_to_create:
                HmProductVanmarcke.create(list_to_create)
                total_success_import_record += 1

    def import_vm_catalog_csv(self):
        try:
            vm_id = self.search([('import_state', 'in', ('new', 'import_in_progress'))])
            if len(vm_id) > 1:
                raise ValidationError(
                    "Multiple imports were found with the 'New' status. Please ensure that only one import exists.")
            if not vm_id.import_csv_done:
                vm_id.import_vm_csv()
        except Exception as e:
            vm_id.import_state = 'fail'
            vm_id.message_post(
                body=f"""<div class="o_thread_message_content">
                            <span>Erreur: {e}</span>
                        </div>"""
            )

    def import_vm_catalog_dbf(self):
        try:
            vm_id = self.search([('import_state', '=', 'import_in_progress')])
            if len(vm_id) > 1:
                raise ValidationError(
                    "Multiple imports were found with the 'Import in progress' status. Please ensure that only one import exists.")

            if not vm_id.import_csv_done:
                raise ValidationError("Il faut lancer la cron Van Marcke - Step 1-1: Import catalog CSV")
            else:
                vm_id.import_vm_dbf_csv()
        except Exception as e:
            vm_id.import_state = 'fail'
            vm_id.message_post(
                body=f"""<div class="o_thread_message_content">
                        <span>Erreur: {e}</span>
                    </div>"""
            )

    def import_file(self):
        return True
