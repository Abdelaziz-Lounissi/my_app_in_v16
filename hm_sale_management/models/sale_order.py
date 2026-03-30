# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"


    hm_work_category = fields.Many2one('hm.works.category', string='Catégorie de travaux', store=True,
                                       copy=False, index=False, readonly=True, ondelete='set null',
                                       related='sale_order_template_id.hm_work_category')

    hm_parent_work_category = fields.Many2one('hm.works.category.parent',
                                              string='Catégorie de travaux parent', store=True, copy=False,
                                              index=False, readonly=True, ondelete='set null',
                                              related='hm_work_category.hm_works_category_parent_id')

    hm_fiscal_position_template_forced_id = fields.Many2one('account.fiscal.position',
                                                            string='Fiscal Position template forced', store=True,
                                                            copy=False, index=False, readonly=True,
                                                            ondelete='set null',
                                                            related='sale_order_template_id.hm_forced_fiscal_position_for_model')

    # TOD: debug => used in many base auto
    hm_sales_team_from_quotation_template_id = fields.Many2one('crm.team',
                                                               string='Sales team from quotation template',
                                                               readonly=True, store=True, copy=False, index=False,
                                                               ondelete='set null',
                                                               related='sale_order_template_id.hm_work_category.hm_works_category_parent_id.hm_sales_teams')

    @api.onchange('sale_order_template_id')
    def _onchange_sale_order_template_id(self):
        data = []
        cpt = 0
        if self.sale_order_template_id:
            for line in self.sale_order_template_id.sale_order_template_line_ids:
                data.append({
                    'hm_sol_state': line.hm_sol_state,
                    'spec': line.spec,
                })
        ret = super(SaleOrder, self)._onchange_sale_order_template_id()
        if self.sale_order_template_id:
            for line in self.order_line:
                line.hm_sol_state = data[cpt]['hm_sol_state']
                line.spec = data[cpt]['spec']
                cpt += 1
                if line.name == '':
                    line.name = ' '
                if line.hm_sol_state != 'normal':
                    line.product_uom_qty = 0
                if line.product_id.product_tmpl_id:
                    product_template = line.product_id.product_tmpl_id
                    if len(product_template.product_variant_ids) > 1:
                        line.is_variant = True
                    else:
                        line.is_variant = False
        return ret


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    hm_sol_state = fields.Selection(
        [("normal", "Normal"), ("option", "Option"), ("variant", "Variant")],
        string="Status", default='normal', copy=True, index=False)

    def write(self, vals):
        # Ensure 'hm_sol_state' is set to 'normal' only if 'product_uom_qty' is explicitly provided and non-zero
        if 'product_uom_qty' in vals and vals['product_uom_qty'] != 0:
            vals['hm_sol_state'] = 'normal'

        return super(SaleOrderLine, self).write(vals)

    @api.onchange('product_uom_qty')
    def onchange_product_uom_qty_sol(self):
        if self.product_uom_qty and self.product_uom_qty != 0:
            self.hm_sol_state = 'normal'

    def run_variant_process(self):
        self.product_uom_qty = 0;
        self.hm_sol_state = 'variant'

    def run_option_process(self):
        self.product_uom_qty = 0;
        self.hm_sol_state = 'option'

class SaleOrderOption(models.Model):
    _inherit = "sale.order.option"

    # update SO Agreement when adding new SOL based on SO option
    def button_add_to_order(self):
        super(SaleOrderOption, self).button_add_to_order()
        self.order_id.on_change_product_template_id()
        self.order_id.onchange_agremeent_ids_params()
        self.order_id._compute_tech_choice_ids()
