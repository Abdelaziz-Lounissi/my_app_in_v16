# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import json
import xmltodict, json
import logging
import requests
from odoo.exceptions import UserError
import base64
import datetime
from xml.etree import ElementTree as et

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _name = 'ir.attachment'
    _inherit = ['ir.attachment', 'mail.thread', 'mail.activity.mixin']

    count_line = fields.Integer('Total File Line')
    count_updated_line = fields.Integer('Total updated')
    count_created_line = fields.Integer('Total created')
    count_price_update = fields.Integer('Total updated prices')
    import_start_date = fields.Datetime('Import start date')
    import_end_date = fields.Datetime('Import end date')
    import_state = fields.Selection(
        selection=[("download_done", "Download done"), ("import_in_progress", "Import in progress"), ("done", "Done"), ('fail', 'Fail')], string="State", tracking=True)
    log_text = fields.Text('Logs')


class HmProductFacq(models.Model):
    _name = "hm.product.facq"
    _description = "Hm Product Facq"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(compute='_compute_name', string='Name')
    product_id = fields.Char(string='Facq Product ID')
    label_fr = fields.Char(string="Label FR", translate=False)
    label_nl = fields.Char(string='Label NL')
    provider_id = fields.Char(string='Provider ID')
    provider_name = fields.Char(string="Manufacturer name and category Facq", translate=False)
    brand_name = fields.Char(string="Manufacturer name", translate=False)
    producer_id = fields.Char(string="Producer ID", translate=False)
    public_price_tax_excluded = fields.Float(string="Public Price Tax Excluded", translate=False, tracking=True)
    net_price_tax_excluded = fields.Float(string="Net Price Tax Excluded", translate=False, tracking=True)
    unit = fields.Char(string="Unit", translate=False)
    image_url = fields.Char(string="Image Url", translate=False)
    technical_sheet = fields.Char(string="Technical Sheet", translate=False)
    log_id = fields.Many2one('hm.facq.log', string="Logs")
    executed = fields.Boolean('Executed', default=False)
    updated = fields.Boolean('Updated', default=False)
    mark_as_created = fields.Boolean('Product supplier info to be created')
    mark_as_updated = fields.Boolean('Product supplier info to be updated')
    pvcheck_is_done = fields.Boolean(default=False)

    def _compute_name(self):
        for catalog in self:
            catalog.name = catalog.label_fr

    def _create_log(self, note, date, state):
        log_vals = {
            'note': note,
            'date': date,
            'state': state
        }
        log = self.env['hm.facq.log'].create(log_vals)
        return log

    @api.model
    def create_facq_connection(self, xml_full_path):
        try:
            _logger.info('Start connection with Facq')
            url = "https://extranet.facq.be/addin/facq/soap/FacqSoap.asmx"
            headers = {"Content-Type": "text/xml; charset=utf-8"}
            company = self.env.company
            UserID = company.user_id
            Login = company.login
            Password = company.password
            CultureID = company.culture_id
            body = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><GetCatalog xmlns="https://extranet.facq.be/addin/facq/soap"><request><UserID>%s</UserID><Login>%s</Login><Password>%s</Password><CultureID>%s</CultureID></request></GetCatalog></soap:Body></soap:Envelope>""" % (
                UserID, Login, Password, CultureID)
            headers.update({"Content-Length": str(len(body))})
            response = requests.post(url, data=body, headers=headers, allow_redirects=True)
            f = open(xml_full_path, "wb")
            f.write(response.content)
            f.close()
            self._create_log("Successfully Connected with Facq Api.", fields.Datetime.now(), 'success')
            return True
        except Exception as e:
            self._create_log(str(e), fields.Datetime.now(), 'fail')
            return False

    @api.model
    def get_facq_catalog(self):
        _logger.info("--************************* Start of 'Facq - Step 1: Get Heat Me Catalog ' *******************************")

        facq_full_path = self.env.company.facq_path
        log_text = ''
        if not facq_full_path:
            raise UserError('Facq PATH, is not set yet!.')
        try:
            xml_full_path = facq_full_path + '/facq_catalog.xml'
            connection = self.create_facq_connection(xml_full_path)
            if connection:
                # convert the xmlfile to a new Json file & read from the new file.json
                json_full_path = facq_full_path + '/data.json'
                with open(xml_full_path) as xml_file:
                    data_dict = xmltodict.parse(xml_file.read())
                    xml_file.close()

                    # generate the object using json.dumps()
                    # corresponding to json data
                    json_data = json.dumps(data_dict)

                    # Write the json data to output to a json file
                    with open(json_full_path, "w") as json_file:
                        json_file.write(json_data)
                        json_file.close()
                import_state = 'download_done'

        except Exception as e:
            import_state = 'fail'
            log_text = str(e)

        # create attachment for fileXML
        with open(xml_full_path, 'rb') as fileXML:
            current_date = str(fields.Datetime.now() + datetime.timedelta(hours=1))
            date_format = datetime.datetime.strptime(str(current_date), '%Y-%m-%d %H:%M:%S').strftime(
                '%Y%m%dT%H%M%S')
            vals = {
                'datas': base64.b64encode(fileXML.read()),
                'name': "facq_catalog " + str(date_format) + '.xml',
                'mimetype': 'application/xml',
                "res_model": 'hm_product_facq',
                "import_state": import_state,
                "import_start_date": fields.Datetime.now(),
                "log_text": log_text,
            }
            self.env['ir.attachment'].create(vals)

        _logger.info("--************************* End of 'Facq - Step 1: Get Heat Me Catalog ' *******************************")

    @api.model
    def facq_pvcheck_update(self):
        """ Cron job: PVCheck update in batches """
        _logger.info("--******** Start PVCheck Update ********--")

        company = self.env.company
        facq_login = company.login
        facq_password = company.password
        facq_user_id = company.user_id
        culture_id = company.culture_id

        batch_size = 1000
        products_to_process = self.sudo().search(
            [('pvcheck_is_done', '=', False)],
            limit=batch_size
        )
        if not products_to_process:
            _logger.info("Aucun produit à traiter pour PVCheck.")
            products_to_reset = self.sudo().search([
                ('public_price_tax_excluded', '>', 0),
                ('net_price_tax_excluded', '>', 0)
            ])
            products_to_reset.write({'pvcheck_is_done': False})
            return

        count_all_product = 0
        count_product_update = 0
        count_price_update = 0

        for product in products_to_process:
            count_all_product += 1
            product_id = product.product_id

            xml_body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                   xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <PVCheck xmlns="https://extranet.facq.be/addin/facq/soap">
          <request>
            <UserID>{facq_user_id}</UserID>
            <Login>{facq_login}</Login>
            <Password>{facq_password}</Password>
            <CultureID>{culture_id}</CultureID>
            <ListPVCheckRequestProduct>
              <PVCheckRequestProduct>
                <ProductID>{product_id}</ProductID>
              </PVCheckRequestProduct>
            </ListPVCheckRequestProduct>
          </request>
        </PVCheck>
      </soap:Body>
    </soap:Envelope>"""

            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'https://extranet.facq.be/addin/facq/soap/PVCheck',
            }

            try:
                response = requests.post(
                    'https://extranet.facq.be/addin/facq/soap/FacqSoap.asmx',
                    data=xml_body.encode('utf-8'),
                    headers=headers,
                    timeout=60
                )
                response.raise_for_status()

                root = et.fromstring(response.content)
                ns = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                      'facq': 'https://extranet.facq.be/addin/facq/soap'}

                product_node = root.find('.//facq:Product', ns)
                if not product_node:
                    _logger.warning(f"Aucun détail PVCheck pour {product_id}")
                    continue

                public_price = float(product_node.findtext('facq:PublicPriceTaxExcluded', '0', ns))
                net_price = float(product_node.findtext('facq:NetPriceTaxExcluded', '0', ns))
                label_fr = product_node.findtext('facq:LabelFR', '', ns)
                label_nl = product_node.findtext('facq:LabelNL', '', ns)
                image_url = product_node.findtext('facq:ImageUrl', '', ns)
                technical_sheet = product_node.findtext('facq:TechnicalSheet', '', ns)

                price_changed = (product.public_price_tax_excluded != public_price or
                                 product.net_price_tax_excluded != net_price)
                other_fields_changed = (product.label_fr != label_fr or
                                        product.label_nl != label_nl or
                                        product.image_url != image_url or
                                        product.technical_sheet != technical_sheet)

                vals = {'pvcheck_is_done': True}

                if price_changed or other_fields_changed:
                    vals.update({
                        'public_price_tax_excluded': public_price,
                        'net_price_tax_excluded': net_price,
                        'label_fr': label_fr,
                        'label_nl': label_nl,
                        'image_url': image_url,
                        'technical_sheet': technical_sheet,
                        'mark_as_updated': True,
                        'executed': False,
                    })
                    count_product_update += 1
                    if price_changed:
                        count_price_update += 1
                    _logger.info(f"Produit mis à jour : {label_fr}")

                product.write(vals)

                if count_all_product % 100 == 0:
                    self.env.cr.commit()

            except Exception as e:
                _logger.error(f"Erreur PVCheck pour {product_id}: {e}", exc_info=True)

        self._create_log(
            f"PVCheck terminé: {count_all_product} produits traités, "
            f"{count_product_update} mis à jour, {count_price_update} prix modifiés.",
            fields.Datetime.now(),
            'success'
        )

        _logger.info(f"-- PVCheck terminé: {count_all_product} produits traités, "
                     f"{count_product_update} mis à jour, {count_price_update} prix modifiés --")

    # Using SOAP 1.1
    @api.model
    def import_facq_catalog(self):
        _logger.info("--************************* Start of 'Facq - Step 2: Import Heat Me Catalog ' *******************************")

        facq_full_path = self.env.company.facq_path
        if not facq_full_path:
            raise UserError('Facq PATH, is not set yet!.')

        json_full_path = f"{facq_full_path}/data.json"

        try:
            with open(json_full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            facq_catalog_attachment = self.env['ir.attachment'].search([('import_state', '=', 'download_done')],
                                                                       limit=1)
            if not facq_catalog_attachment:
                raise UserError(_("Aucun fichier à importer avec l'état 'download_done'."))

            facq_catalog_attachment.import_state = 'import_in_progress'
            self.env.cr.commit()

            products = data.get('soap:Envelope', {}).get('soap:Body', {}).get('GetCatalogResponse', {}).get(
                'GetCatalogResult', {}).get('ListProduct', {}).get('Product', [])
            if not products:
                raise UserError(_("Le fichier JSON ne contient aucun produit."))

            existing_products = {p.product_id: p for p in self.sudo().search([])}

            count_all_product = 0
            count_product_created = 0
            count_product_update = 0
            count_price_update = 0
            list_to_create = []

            for item in products:
                count_all_product += 1
                product_id = item.get('ProductID')
                vals = {
                    'product_id': product_id,
                    'label_fr': item.get('LabelFR'),
                    'label_nl': item.get('LabelNL'),
                    'provider_id': item.get('ProviderID'),
                    'provider_name': item.get('ProviderName'),
                    'brand_name': item.get('BrandName'),
                    'producer_id': item.get('ProducerID'),
                    'public_price_tax_excluded': float(item.get('PublicPriceTaxExcluded', 0)),
                    'net_price_tax_excluded': float(item.get('NetPriceTaxExcluded', 0)),
                    'unit': item.get('Unit'),
                    'image_url': item.get('ImageUrl'),
                    'technical_sheet': item.get('TechnicalSheet'),
                    'executed': False,
                }

                existing_product = existing_products.get(product_id)

                if existing_product:
                    price_changed = (existing_product.public_price_tax_excluded != vals['public_price_tax_excluded'] or
                                     existing_product.net_price_tax_excluded != vals['net_price_tax_excluded'])

                    other_fields_changed = (existing_product.label_fr != vals['label_fr'] or
                                            existing_product.label_nl != vals['label_nl'] or
                                            existing_product.image_url != vals['image_url'] or
                                            existing_product.technical_sheet != vals['technical_sheet'])

                    if price_changed:
                        count_price_update += 1

                    if price_changed or other_fields_changed:
                        vals.update({
                            'mark_as_updated': True,
                            'mark_as_created': False,
                            'executed': False,
                        })
                        existing_product.write(vals)
                        count_product_update += 1
                        _logger.info(f"Mise à jour du produit : {item['LabelFR']}")
                else:
                    vals['mark_as_created'] = True
                    list_to_create.append(vals)
                    count_product_created += 1
                    _logger.info(f"Append product : {item['LabelFR']}")

            # Create all product in list
            if list_to_create:
                self.create(list_to_create)

            facq_catalog_attachment.write({
                'count_line': count_all_product,
                'count_updated_line': count_product_update,
                'count_created_line': count_product_created,
                'count_price_update': count_price_update,
                'import_state': 'done',
                'import_end_date': fields.Datetime.now(),
            })

            _logger.info( "--************************* End of 'Facq - Step 2: Import Heat Me Catalog ' *******************************")

        except Exception as e:
            _logger.error(f"Erreur lors de l'import du catalogue Facq: {e}", exc_info=True)
            self._create_log(_("Échec de la création des articles"), fields.Datetime.now(), 'fail')
            if facq_catalog_attachment:
                facq_catalog_attachment.write({
                    'import_state': 'fail',
                    'log_text': str(e),
                })
            self.env.cr.commit()

