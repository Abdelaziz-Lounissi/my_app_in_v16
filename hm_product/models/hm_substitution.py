# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class HmSubstitution(models.Model):
    _name = "hm.substitution"
    _description = "Hm Substitution"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    display_name = fields.Char('Display Name', compute="_compute_display_name")
    old_product = fields.Many2one('product.product', string='Article à substituer')
    new_product = fields.Many2one('product.product', string='Article remplaçant')
    log = fields.Text('Log')
    substitution_date = fields.Datetime(string="Date de substitution")
    archive = fields.Boolean(default=False, string="Archiver l'article à substituer")

    @api.depends('old_product', 'new_product')
    def _compute_display_name(self):
        for prod in self:
            prod.display_name = prod.old_product.name + ' --> ' + prod.new_product.name

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, substitution_date=False, log=False)
        return super(HmSubstitution, self).copy(default)

    def action_substitution(self):
        bom_line_obj = self.env['mrp.bom.line']
        sale_order_line_obj = self.env['sale.order.template.line']
        sale_order_template_option_obj = self.env['sale.order.template.option']
        product_obj = self.env['product.product']
        log = ''
        if not self.new_product.equivalent_product_ids:
            if self.archive:
                self.old_product.active = False
            if self.old_product.default_code:
                if not self.new_product.default_code:
                    default_code = self.old_product.default_code
                    self.new_product.write({'default_code': default_code})
                self.old_product.update({'default_code': False})
            bom_lines = bom_line_obj.search([('product_id', '=', self.old_product.id)])
            if bom_lines:
                log += 'BOMs : ' + '\n'
                for bom_line in bom_lines:
                    bom_line.product_id = self.new_product.id
                    log += bom_line.bom_id.product_tmpl_id.name + '\n'
            sale_order_lines = sale_order_line_obj.search([('product_id', '=', self.old_product.id)])
            if sale_order_lines:
                log += '==========================\n'
                log += 'Modèle de devis : ' + '\n'
                for sale_order_line in sale_order_lines:
                    sale_order_line.product_id = self.new_product.id
                    sale_order_line._onchange_product_id()
                    log += sale_order_line.sale_order_template_id.name + '\n'
            sale_order_template_options = sale_order_template_option_obj.search([('product_id', '=', self.old_product.id)])
            if sale_order_template_options:
                log += '==========================\n'
                log += 'Option modèle de devis : ' + '\n'
                for sale_order_template_option in sale_order_template_options:
                    sale_order_template_option.product_id = self.new_product.id
                    sale_order_template_option._onchange_product_id()
                    log += sale_order_template_option.sale_order_template_id.name + '\n'
            old_product_template_id = self.old_product.product_tmpl_id.id
            optional_products = product_obj.search([('optional_product_ids.id', '=', old_product_template_id)])
            if optional_products:
                log += '==========================\n'
                log += 'Articles optionnels : ' + '\n'
                for product in optional_products:
                    for optional_product_id in product.optional_product_ids.filtered(lambda opt: opt.id == old_product_template_id):
                        product['optional_product_ids'] = [(3, optional_product_id.id), (4, self.new_product.product_tmpl_id.id)]
                    log += product.name + '\n'

            if self.old_product.equivalent_id:
                log += '==========================\n'
                log += 'Articles équivalents : ' + '\n'
                for product in self.old_product.equivalent_product_ids:
                    log += product.name + '\n'

                self.new_product.product_tmpl_id.equivalent_id = self.old_product.product_tmpl_id.equivalent_id.id
                self.old_product.product_tmpl_id.equivalent_id = False
                self.new_product.product_tmpl_id._compute_other_equivalent_product()
                self.old_product.product_tmpl_id._compute_other_equivalent_product()

            self.log = log
            if not self.log:
                raise UserError(_('Aucun article à substituer.'))
            self.substitution_date = fields.Datetime.now()
        else:
            raise UserError(_("Erreur, L'article remplaçant à des articles équivalents!"))


