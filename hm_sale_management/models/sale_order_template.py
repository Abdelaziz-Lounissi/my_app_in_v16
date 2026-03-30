# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _, SUPERUSER_ID
from math import ceil
from odoo.exceptions import UserError


class SaleOrderTemplate(models.Model):
    _name = 'sale.order.template'
    _inherit = ['sale.order.template', 'mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char('Quotation Template', required=True, translate=False)
    hm_work_category = fields.Many2one("hm.works.category", string="Catégorie de travaux", store=True,
                                       copy=True, index=False, ondelete="set null")
    hm_access_to_the_necessary_profession_id = fields.Many2one("hm.access.profession",
                                                               string="Acces à la profession nécessaire",
                                                               related="hm_work_category.hm_access_to_the_necessary_profession_id",
                                                               readonly=True, store=True, copy=False,
                                                               ondelete="set null",
                                                               index=False)
    hm_status = fields.Selection(
        [("draft", "En construction"), ("to_validate", "A valider"), ("active", "Actif")],
        string="Statut", store=True, copy=True, index=False, default="draft")
    hm_display_proprio_on_work_order = fields.Boolean(string="Afficher proprio sur bon de travail", store=True, copy=True, index=False)
    hm_work_type = fields.Char(string="HM Work Type", related="work_type.display_name", readonly=True, copy=True,
                               index=False, translate=False, store=False)
    hm_forced_fiscal_position_for_model = fields.Many2one("account.fiscal.position",
                                                          string="Position fiscale forcée pour modéle",
                                                          store=True, copy=True, ondelete="set null",
                                                          index=False)
    hm_work_object = fields.Text(string='Objet des travaux pour le SO',
                                 help="Ce texte est copié dans l'objet des travaux du SO lorsque ce modèle de devis est sélectionné", copy=True, translate=True)
    # TODO: debug if still need it
    product_ids = fields.Many2many('product.product', 'product_sale_order_template', 'order_template_id', 'product_id', string='Work type product')
    hm_so_manager_theoretical_workload_in_minutes = fields.Integer('Charge de gestion estimée en minutes', default=0)
    hm_so_manager_workload_points = fields.Integer('Points de gestion', compute='calculate_point_gestion')
    ask_qr_code = fields.Boolean(string="Demander au technicien de coller un QR code sur l'appareil", default=False)

    @api.onchange('work_type')
    def onchange_work_type(self):
        if self.work_type:
            self.hm_work_object = self.work_type.name
        else:
            self.hm_work_object = False

    @api.depends('hm_so_manager_theoretical_workload_in_minutes')
    def calculate_point_gestion(self):
        """
            la valeur du champ 'Points de gestion' hm_so_manager_workload_points est automatiquement calculée
            quand je modifie la valeur du champ 'Charge de gestion estimée en minutes'
            formule: hm_so_manager_workload_points = hm_so_manager_theoretical_workload_in_minutes / hm_so_manager_workload_ratio
            la valeur est arrondie à l'unité supérieure si >= .5
        """
        for work in self:
            if work.hm_so_manager_theoretical_workload_in_minutes < 0:
                raise ValidationError('la valeur du Charge de gestion estimée en minutes doit être supérieure ou égale à 0')
            params = self.env['ir.config_parameter'].sudo()
            hm_so_manager_workload_ratio = int(params.get_param('hm_sale_crm.hm_so_manager_workload_ratio', default=0))
            if hm_so_manager_workload_ratio != 0:
                number_splited = str(work.hm_so_manager_theoretical_workload_in_minutes / hm_so_manager_workload_ratio).split('.')
                if number_splited[1].startswith("5"):
                    work.hm_so_manager_workload_points = ceil(work.hm_so_manager_theoretical_workload_in_minutes / hm_so_manager_workload_ratio)
                else:
                    work.hm_so_manager_workload_points = round(work.hm_so_manager_theoretical_workload_in_minutes / hm_so_manager_workload_ratio)
            else:
                work.hm_so_manager_workload_points = 0

    @api.onchange('sale_order_template_line_ids')
    def onchange_order_template_line(self):
        if self.sale_order_template_line_ids:
            list_product_ids = self.sale_order_template_line_ids.mapped('product_id')
            self.product_ids = [(6, 0, list_product_ids.ids)]
        else:
            self.product_ids = [(6, 0, [])]

    @api.model
    def update_order_template_line_product(self):
        for order in self.search([]):
            if order.sale_order_template_line_ids:
                list_product_ids = order.sale_order_template_line_ids.mapped('product_id')
                order.product_ids = [(6, 0, list_product_ids.ids)]
            else:
                order.product_ids = [(6, 0, [])]


class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    hm_sol_state = fields.Selection(
        [("normal", "Normal"), ("option", "Option"), ("variant", "Variant")],
        string="Status", default='normal', store=True, copy=False, index=False)

    spec = fields.Text(string='Spec')
    computed_image_art = fields.Html(string="Art", compute="_compute_image_art", store=True)
    product_uom_qty = fields.Float(
        string='Quantity',
        required=True,
        digits='Product Unit of Measure',
        default=1)

    @api.onchange('hm_sol_state')
    def onchange_hm_sol_state(self):
        if self.hm_sol_state == 'option':
            self.product_uom_qty = 0
        elif self.hm_sol_state == 'variant':
            self.product_uom_qty = 0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.ensure_one()
        if self.product_id:
            attribute = self.product_id.product_template_attribute_value_ids or ''
            name = ''
            if attribute:
                name = "[" + str(attribute[0].name) + "]"
            if self.product_id.description_sale:
                name += " " + self.product_id.description_sale
            self.name = name
            # no price in v16
            # self.price_unit = self.product_id.lst_price
            self.product_uom_id = self.product_id.uom_id.id
            domain = {'product_uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
            return {'domain': domain}

    @api.depends('product_id')
    def _compute_image_art(self):
        for line in self:
            if line.product_id:
                parts = ["<div class='d-flex flex-column align-items-center text-center'>"]
                sku_text = line.product_id.sku or "No Reference"
                parts.append(f"<span class='border-bottom pb-1 mb-1'>{sku_text}</span>")
                supplier = line.product_id.prime_supplier_id
                if supplier and supplier.image_1920 and supplier.hm_is_real_picture:
                    supplier_img_url = f'/web/image/res.partner/{supplier.id}/image_1920/35x35'
                    parts.append(f"<img style='padding:20px!important' src='{supplier_img_url}' alt='Supplier Image'/>")
                product_img_url = f'/web/image/product.product/{line.product_id.id}/image_1024/48x48'
                parts.append(f"<img src='{product_img_url}' alt='Product Image'/>")

                parts.append("</div>")
                line.computed_image_art = ''.join(parts)
            else:
                line.computed_image_art = "<span class='text-muted border-bottom pb-1 mb-1'>No Product</span>"

    @api.model
    def assign_product_state(self, record_id=False):
        context = self.env.context
        record = self
        if context.get("record_id") :
            record_id = context.get("record_id")
            record = self.browse(record_id)
        if context.get("assign_opt") and record:
            record.hm_sol_state = 'option'
            record.product_uom_qty = 0
        elif context.get("assign_vrt") and record:
            record.hm_sol_state = 'variant'
            record.product_uom_qty = 0
        return True


    def write(self, vals):

        can_edit_sot = self.env.user.has_group('hm_sale_management.group_can_edit_sale_order_template')
        if not can_edit_sot:
            raise UserError("Vous n'êtes pas autorisé à modifier les modèles de devis.")

        shared_dict = {}
        fnames = (
            'name', 'product_uom_qty'
        )
        origin = self._origin.read(fnames)[0]
        template_id = self.env['sale.order.template.line']
        for i in origin:
            if (i in vals) and (origin[i] != vals[i]):
                new_value = vals[i]
                if type(vals[i]) is int and i != 'name':
                    new_value = float("{:.2f}".format(vals[i]))
                shared_dict[i] = new_value
        if shared_dict:
            self.sale_order_template_id.message_post(body=self._format_message(shared_dict, origin))
        return super(SaleOrderTemplateLine, self).write(vals)

    def _format_message(self, shared_dict, origin):
        mess = "<ul>"
        mess += """Line : %s %s""" %(self.product_id.name,self.name)

        for fname, value in shared_dict.items():
            mess += """
                              <li>{label}: {old_value} -> {new_value}</li>
                              """.format(
                label=self._fields[fname].string,
                old_value=origin[fname] if fname == 'name' else origin[fname],
                new_value=shared_dict[fname],
            )
        mess += "<ul>"
        return mess

    def _format_unlink_msg(self, shared_dict):
        mess = "<ul>"
        mess += """
                          <li>{label}: {old_value} -> {new_value}</li>
                          """.format(
            label="Template line",
            old_value=shared_dict,
            new_value='ligne supprimée',
        )
        mess += "<ul>"
        return mess

    def unlink(self):
        for rec in self:
            self.sale_order_template_id.message_post(body=self._format_unlink_msg(rec.product_id.name))
        return super(SaleOrderTemplateLine, self).unlink()

    def _format_create_msg(self, shared_dict):
        mess = "<ul>"
        mess += """
                          <li>{label}: {new_value}</li>
                          """.format(
            label="ligne ajoutée ",
            new_value=shared_dict,
        )
        mess += "<ul>"
        return mess

    @api.model_create_multi
    def create(self, vals):
        res = super(SaleOrderTemplateLine, self).create(vals)
        for i in vals:
            self.env['sale.order.template'].search([('id','=',i['sale_order_template_id'])]).message_post(body=self._format_create_msg(self.env['product.product'].search([('id','=',i['product_id'])]).name))
        return res

    @api.onchange('product_id', 'spec')
    def _onchange_spec(self):
        self.ensure_one()
        if self.product_id:
            if self.spec or self.spec == "":
                self.name = ">> " + self.spec + "\n" + self.name

    def run_variant_process(self):
        self.product_uom_qty = 0;
        self.hm_sol_state = 'variant'

    def run_option_process(self):
        self.product_uom_qty = 0;
        self.hm_sol_state = 'option'
