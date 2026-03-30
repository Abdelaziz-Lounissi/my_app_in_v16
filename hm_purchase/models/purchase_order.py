# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError, AccessError
from odoo import _, api, exceptions, fields, models
from dateutil.relativedelta import relativedelta
import datetime
from lxml import etree
from datetime import datetime, timedelta
import logging
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    hm_so_lie = fields.Many2one('sale.order', string='Sale Order', compute='_compute_hm_so_lie', inverse='_inverse_hm_so_lie',store=True)
    hm_po_deleted_from_portal = fields.Boolean(string="PO supprimé du portail", store=True, copy=False, index=False)

    # TODO: task id:
    hm_delivery_address_id = fields.Many2one("res.partner", string="Shipping address", ondelete='set null',
                                             store=True, copy=False, index=False,
                                             related="hm_person_who_will_do_the_kidnapping_id.hm_vam_privileged_technics_store", related_sudo=True)
    hm_delivery_address = fields.Many2one("res.partner", string="Adresse de livraison choisie", ondelete='set null',
                                          store=True, copy=False, index=False)
    hm_intervention_property_address = fields.Many2one("hm.property", string="Intervention address", readonly=True,
                                                       ondelete="set null", related="hm_so_lie.property_id",
                                                       store=True, index=False, copy=False, related_sudo=True)
    hm_interv_address_name = fields.Char(string="Adresse interv",
                                         related="dest_address_id.display_name",
                                         store=True, copy=False, translate=False, index=False, related_sudo=True)
    hm_delivery_date = fields.Datetime(string="Delivery Date", store=True, copy=False, index=False)
    hm_intervention_datetime = fields.Datetime(string="Date intervention",
                                               help="C'est la date de livraison promise au client. Si elle est définie, le bon de livraison se basera sur cette date plutôt que celle définié grâce au délai indiqué sur l'article.",
                                               related="order_line.sale_line_id.order_id.commitment_date", store=True,
                                               copy=False, index=False, readonly=False, related_sudo=True)
    hm_intervention_address_name = fields.Char(string="Nom d'adresse d'intervention",
                                               related="dest_address_id.name",
                                               copy=False,
                                               store=True, index=False, related_sudo=True)
    hm_technician = fields.Boolean(string="Technician", copy=False, store=True, index=False)

    # TODO rename :hm_person_who_will_do_the_kidnapping_id  => picking_responsible_id
    hm_person_who_will_do_the_kidnapping_id = fields.Many2one("res.partner", string="Personne qui fera l'enlèvement",
                                                              ondelete="set null",
                                                              copy=False, store=True, index=False)
    hm_imputed_technician_id = fields.Many2one("res.partner", string="Technicien", readonly=True,
                                               related="hm_so_lie.hm_imputed_technician_id",
                                               ondelete="set null", tracking=True, copy=False, store=True, index=True)
    po_type = fields.Selection(
        selection=[("po_marchandise", "PO Marchandise"), ("po_emport_marchandise", "PO Emport Marchandise"),
                   ("po_technicien", "PO Technicien"), ("po_frais_generaux", "PO Frais Généraux"),
                   ('po_commission', 'PO Commission')], string="PO Type", default="po_emport_marchandise")

    stage2_id = fields.Many2one('purchase.stage', string='State2 PO', ondelete='restrict', tracking=True, index=True,
                                copy=False,
                                group_expand='_read_group_stage_ids')
    groupby_stage2_name =  fields.Char(string='Used for State2 PO - Group by', compute='_compute_groupby_stage2_name',
                                        store=True, precompute=True, index=True, readonly=True)

    credit_note_claim_reason = fields.Text(string="Motif réclamation NC")
    hm_date_state2_update_deadline = fields.Datetime('Date limite de changement de statut', tracking=True)
    hm_state2_update_overdue = fields.Boolean('Est en retard de gestion', compute="compute_has_overdue_activity",
                                             store=True)
    # TODO: clean me
    so_manager = fields.Many2one('res.partner', related='hm_so_lie.hm_so_manager_id.partner_id', string='Manager SO')
    so_manager_1 = fields.Many2one('res.users', related='hm_so_lie.hm_so_manager_id', string='Gestionnaire du so')
    state2 = fields.Selection(related="hm_so_lie.state2", readonly=True, string='State2 SO')

    # TODO: waiting for decision
    show_supplier_encoded_button = fields.Boolean(compute="compute_visibility_supplier_encoded_button", store=True, index=True)
    date_confirm = fields.Datetime(string='Approved by the supplier', readonly=True, copy=False)

    has_group_sale_manager = fields.Boolean(compute='_has_group_sale_manager', string='Has group sale manager')
    block_auto_send_to_technician = fields.Boolean(string="Bloquer les envois auto au technicien")

    @api.depends('stage2_id.name', 'stage2_id')
    def _compute_groupby_stage2_name(self):
        for rec in self:
            rec.groupby_stage2_name = rec.stage2_id.name

    def _inverse_hm_so_lie(self):
        for po in self:
            if po.hm_so_lie:
                for line in po.order_line:
                    line.sale_order_id = po.hm_so_lie.id
                    line.is_po_emport = po.po_type == 'po_emport_marchandise'
            else:
                for line in po.order_line:
                    line.sale_order_id = False
                    line.is_po_emport = False

    @api.depends('hm_so_lie', 'order_line.sale_order_id', 'po_type')
    def _compute_hm_so_lie(self):
        for po in self:
            sale_obj = self.env['sale.order']
            if po.hm_so_lie and po.po_type == 'po_emport_marchandise':
                po.order_line.sale_order_id = po.hm_so_lie and po.hm_so_lie.id or False
                po.order_line.is_po_emport = True
            else:
                if po.hm_so_lie:
                    po.order_line.sale_order_id = po.hm_so_lie and po.hm_so_lie.id or False
                else:
                    orders = []
                    for ln in po.order_line:
                        if ln.sale_order_id:
                            orders = ln.sale_order_id
                    po.hm_so_lie = orders and orders[0] or sale_obj
                    po.order_line.is_po_emport = False

    @api.depends('state', 'stage2_id')
    def compute_visibility_supplier_encoded_button(self):
        for po in self:
            if po.state == 'purchase' and po.stage2_id.id in [self.env.ref("hm_purchase.purchase_stage1_po_marchandise").id ,self.env.ref("hm_purchase.purchase_stage1_po_emport_marchandise").id
                ,self.env.ref("hm_purchase.purchase_stage1_po_technicien").id , self.env.ref("hm_purchase.purchase_stage1_po_commission").id ,self.env.ref("hm_purchase.purchase_stage2_po_marchandise").id]:
                po.show_supplier_encoded_button = True
            else:
                po.show_supplier_encoded_button = False

    @api.model
    def cron_state2_po_deadline(self):
        canceled_state2_po_1 = self.env.ref('hm_purchase.purchase_stage3_po_technicien').id
        canceled_state2_po_2 = self.env.ref('hm_purchase.purchase_stage6_po_marchandise').id
        canceled_state2_po_3 = self.env.ref('hm_purchase.purchase_stage3_po_emport_marchandise').id
        canceled_state2_po_4 = self.env.ref('hm_purchase.purchase_stage3_po_commission').id
        canceled_state2_po_5 = self.env.ref('hm_purchase.purchase_stage5_po_frais').id

        purchase_ids = self.search([
            ('po_type', '=', 'po_marchandise'),
            ('stage2_id', 'not in', (
                canceled_state2_po_1,
                canceled_state2_po_2,
                canceled_state2_po_3,
                canceled_state2_po_4,
                canceled_state2_po_5
            )),
            '|',
            ('hm_date_state2_update_deadline', '=', False),
            ('hm_date_state2_update_deadline', '<', datetime.now())
        ])

        for purchase in purchase_ids:
            _logger.info('**** Purchase  %s ' % purchase.id)
            activity_summary = False
            activity_type_id = False

            if purchase.stage2_id == self.env.ref('hm_purchase.purchase_stage1_po_marchandise'):
                activity_summary = 'Commander ou annuler le PO?'
                activity_type_id = self.env.ref('hm_purchase.hm_purchase_activity_order_or_cancel')

            elif purchase.stage2_id == self.env.ref('hm_purchase.purchase_stage2_po_marchandise'):
                activity_summary = 'Vérifier si PO a été encodé par le fournisseur'
                activity_type_id = self.env.ref('hm_purchase.hm_purchase_activity_supplier_po_encoding_check')

            elif purchase.stage2_id == self.env.ref('hm_purchase.purchase_stage3_po_marchandise'):
                activity_summary = 'Vérifier quantités, SKU, disponibilité, date et adresse de livraison'
                activity_type_id = self.env.ref('hm_purchase.hm_purchase_activity_po_check_qty_sku_delivery')

            if activity_summary and activity_type_id and activity_type_id not in purchase.activity_ids.mapped('activity_type_id'):
                vals = {
                    'summary': activity_summary,
                    'note': activity_summary,
                    'activity_type_id': activity_type_id.id,
                    'user_id': purchase.hm_so_lie.hm_so_manager_id.id
                }
                purchase.activity_schedule(**vals)

    @api.onchange('state', 'stage2_id', 'hm_intervention_datetime')
    def _onchange_state2_po_deadline(self):
        res = False
        date_now = datetime.now()
        brussels_timezone = pytz.timezone('Europe/Brussels')
        date_now = date_now.astimezone(pytz.timezone(brussels_timezone.zone))

        sale_order = self.hm_so_lie

        if not sale_order.check_date_by_working_hours(date_now):
            date_now = date_now + timedelta(days=1)

            while sale_order.check_date_weekend_or_holidays(date_now):
                date_now += timedelta(days=1)

            tech_today_calendar_id = sale_order.get_date_by_tech_calendar(date_now)
            tech_today_from_hour = tech_today_calendar_id['tech_from_hour']
            tech_today_from_min = tech_today_calendar_id['tech_from_min']

            next_date = date_now.replace(hour=tech_today_from_hour, minute=tech_today_from_min)
            date_now = next_date

        if self.po_type == 'po_marchandise' and self.stage2_id == self.env.ref('hm_purchase.purchase_stage2_po_marchandise') and sale_order.commitment_date:
            commitment_date = sale_order.commitment_date.astimezone(pytz.timezone(brussels_timezone.zone))

            working_hours_18 = sale_order.get_date_by_working_hours(date_now, 18)
            working_hours_36 = sale_order.get_date_by_working_hours(date_now, 36)

            # si l'intervention est programmée dans les prochaines 16h ouvrables: Now + 4h ouvrables
            if commitment_date <= working_hours_18:
                _logger.info('**** PO / Case 1 : OK ')
                _logger.info('**** commitment_date : %s' % commitment_date)
                _logger.info('**** working_hours_18 : %s ' % working_hours_18)

                res = sale_order.compute_po_deadline(days=0.5, date_now=date_now)

            # si l'intervention est programmée au-délà de 16h ouvrables: Now + 8h ouvrables
            elif (working_hours_18 < commitment_date) and (working_hours_36 > commitment_date):
                _logger.info('**** PO / Case 2 : OK ')
                _logger.info('**** commitment_date : %s' % commitment_date)
                _logger.info('**** working_hours_18 : %s ' % working_hours_18)
                _logger.info('**** working_hours_36 : %s ' % working_hours_36)

                res = sale_order.compute_po_deadline(days=1, date_now=date_now)

            # si l'intervention est programmée au-délà de 32h ouvrables: Now + 16h ouvrables
            elif working_hours_18 <= commitment_date:
                _logger.info('**** PO / Case 3 : OK ')
                _logger.info('**** commitment_date : %s' % commitment_date)
                _logger.info('**** working_hours_18 : %s ' % working_hours_18)

                res = sale_order.compute_po_deadline(days=2, date_now=date_now)

        if self.po_type == 'po_marchandise' and self.stage2_id == self.env.ref( 'hm_purchase.purchase_stage3_po_marchandise'):
            _logger.info('**** PO / Case 4 : OK ')
            _logger.info('**** date_now + 30 min ')

            res = date_now + timedelta(minutes=30)

        if self.po_type == 'po_marchandise' and self.stage2_id not in [self.env.ref( 'hm_purchase.purchase_stage1_po_marchandise'), self.env.ref( 'hm_purchase.purchase_stage2_po_marchandise'), self.env.ref( 'hm_purchase.purchase_stage3_po_marchandise')]:
            res = False
            _logger.info('**** PO / Case 5 : OK ')
            _logger.info('**** date_now => False ')

        if res:
            res = res.astimezone(pytz.timezone('UTC')).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        self.hm_date_state2_update_deadline = res

    @api.depends('hm_date_state2_update_deadline')
    def compute_has_overdue_activity(self):
        for order in self:
            if order.hm_date_state2_update_deadline and order.hm_date_state2_update_deadline < datetime.now():
                order.hm_state2_update_overdue = True
            else:
                order.hm_state2_update_overdue = False

    def get_return_to_do_action_view(self):
        move_ids = self.env['stock.move']
        if self.po_type == 'po_technicien':
            po_so_ids = self.search(
                [('hm_so_lie', '=', self.hm_so_lie.id),
                 ('po_type', 'in', ['po_marchandise', 'po_emport_marchandise'])])

            domain = lambda x: x.state in ['draft', 'assigned'] and x.is_returned_picking == True
            move_ids = po_so_ids.mapped('picking_ids').filtered(domain).mapped('move_ids_without_package')

        view_id = self.env.ref('hm_purchase.view_move_tree_receipt_picking_inherit')

        return {
            'name': 'Return to Do',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(view_id.id, 'tree')],
            'res_model': 'stock.move',
            'domain': [('id', 'in', move_ids.ids)],
            'type': 'ir.actions.act_window',
        }

    def _set_hm_delivery_address(self):
        if self.hm_delivery_address:
            self.hm_delivery_address = self.hm_delivery_address.id
        elif self.hm_delivery_address_id:
            self.hm_delivery_address = self.hm_delivery_address_id.id

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        result = super(PurchaseOrder, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                       orderby=orderby, lazy=lazy)
        state1 = []
        state2 = []
        state3 = []
        state4 = []
        state5 = []
        state6 = []
        state7 = []
        res = result
        for rec in res:
            if rec.get('groupby_stage2_name') and rec['groupby_stage2_name'] == 'À traiter':
                state1.append(rec)
            elif rec.get('groupby_stage2_name') and rec['groupby_stage2_name'] == 'Envoyé au fournisseur':
                state2.append(rec)
            elif rec.get('groupby_stage2_name') and rec['groupby_stage2_name'] == 'Encodé par fournisseur':
                state3.append(rec)
            elif rec.get('groupby_stage2_name') and rec['groupby_stage2_name'] == 'Réceptionné':
                state4.append(rec)
            elif rec.get('groupby_stage2_name') and rec['groupby_stage2_name'] == 'Clôturé':
                state5.append(rec)
            elif rec.get('groupby_stage2_name') and rec['groupby_stage2_name'] == 'Annulé':
                state6.append(rec)
            else:
                state7.append(rec)
        result_byorder = state1 + state2 + state3 + state4 + state5 + state6 + state7
        if result_byorder:
            result = result_byorder
        return result

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return stages.search([], order=order)

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.stage2_id == self.env.ref('hm_purchase.purchase_stage2_po_marchandise'):
            return self.env.ref('hm_purchase.mt_rfq_sent_to_supplier')
        elif 'state' in init_values and self.stage2_id == self.env.ref('hm_purchase.purchase_stage3_po_marchandise'):
            return self.env.ref('hm_purchase.mt_rfq_confirmed2')
        return super(PurchaseOrder, self)._track_subtype(init_values)

    def action_rfq_send(self):
        res = super(PurchaseOrder, self).action_rfq_send()
        if 're_sent_to_supplier' in self.env.context:
            if self.po_type not in ['po_technicien', 'po_frais_generaux']:
                if (not self.hm_delivery_address or not self.hm_delivery_date):
                    raise exceptions.UserError(
                        _(
                            'Please define the following two fields:\n'
                            '- Delivery Address\n'
                            '- Delivery Date'
                        )
                    )
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if 're_sent_to_supplier' in self.env.context:
            self.write({'stage2_id': self.env.ref('hm_purchase.purchase_stage2_po_marchandise').id})
        return super(PurchaseOrder, self).message_post(**kwargs)

    def update_po_lines(self):
        if self.partner_id:
            for line in self.order_line:
                supplier_info = line.product_id.seller_ids.filtered(lambda l: l.partner_id == self.partner_id)
                if supplier_info:
                    price = supplier_info.price
                    line.price_unit = price

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        res = super(PurchaseOrder, self).onchange_partner_id()
        if not self.is_po_emport:
            if self.partner_id:
                if self.partner_id.hm_technician:
                    self.po_type = 'po_technicien'
                else:
                    self.po_type = 'po_marchandise'
            else:
                self.po_type = False
        self.update_po_lines()
        return res

    @api.onchange('po_type')
    def onchange_po_type(self):
        if self.state != 'purchase':
            stage2_id = self.env['purchase.stage'].search([('po_type', '=', self.po_type)], limit=1, order='sequence')
            self.stage2_id = stage2_id and stage2_id.id or False
        if self.po_type != 'po_emport_marchandise':
            self.is_po_emport = False
            self.env.context = dict(self.env.context)
            self.env.context.update({'purchase_order_emport': False})
            self.env.context.update({'default_is_po_emport': False})
        if self.po_type == 'po_emport_marchandise':
            self.is_po_emport = True
            self.env.context = dict(self.env.context)
            self.env.context.update({'purchase_order_emport': True})
            self.env.context.update({'default_is_po_emport': True})

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            # skip add supplier to product
            # order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.company.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    @api.depends('state', 'stage2_id')
    def _has_group_sale_manager(self):
        validated_state2_po_marchandise = self.env.ref('hm_purchase.purchase_stage5_po_marchandise').id
        validated_state2_po_emport_marchandise = self.env.ref('hm_purchase.purchase_stage2_po_emport_marchandise').id
        validated_state2_po_technicien = self.env.ref('hm_purchase.purchase_stage2_po_technicien').id
        validated_state2_po_commission = self.env.ref('hm_purchase.purchase_stage2_po_commission').id
        for po in self:
            po.has_group_sale_manager = True
            if po.state in ['done', 'cancel']:
                po.has_group_sale_manager = False
            elif po.stage2_id.id in [validated_state2_po_marchandise, validated_state2_po_emport_marchandise, validated_state2_po_technicien, validated_state2_po_commission]:
                po.has_group_sale_manager = False

    @api.onchange('state', 'stage2_id')
    def _onchange_stage2_id(self):
        if self.state2 in ('invoiced', 'to_invoice'):
            raise UserError(
                _("Ce PO ne peut plus être modifié car le SO lié est au statut validé. Pour débloquer cela adressez vous au manager pour qu'il change le status du SO"))
        if self.state2 == 'cancel' or self.stage2_id.id in (self.env.ref('hm_purchase.purchase_stage6_po_marchandise').id,
                                                            self.env.ref(
                                                                'hm_purchase.purchase_stage3_po_emport_marchandise').id,
                                                            self.env.ref('hm_purchase.purchase_stage3_po_technicien').id,
                                                            self.env.ref('hm_purchase.purchase_stage3_po_commission').id,
                                                            self.env.ref('hm_purchase.purchase_stage5_po_frais').id):
            self._origin.sudo().write({'state': 'cancel'})

    @api.constrains('state')
    def _check_state(self):
        for record in self:
            if record.state2 == 'invoiced':
                raise UserError(
                    _("Ce PO ne peut plus être modifié car le SO lié est au statut validé. Pour débloquer cela adressez vous au manager pour qu'il change le status du SO"))
            if record.hm_so_lie.state == 'cancel' and record.state != 'cancel':
                raise UserError(
                    _("Ce PO ne peut plus être modifié car le SO lié est Annulé. Pour débloquer cela adressez vous au manager pour qu'il change le status du SO."))

    @api.constrains('stage2_id')
    def _check_stage2_id(self):
        for record in self:
            canceled_state2_po_1 = self.env.ref('hm_purchase.purchase_stage3_po_technicien').id
            canceled_state2_po_2 = self.env.ref('hm_purchase.purchase_stage6_po_marchandise').id
            canceled_state2_po_3 = self.env.ref('hm_purchase.purchase_stage3_po_emport_marchandise').id
            canceled_state2_po_4 = self.env.ref('hm_purchase.purchase_stage3_po_commission').id
            canceled_state2_po_5 = self.env.ref('hm_purchase.purchase_stage5_po_frais').id

            if record.state == 'cancel' and record.stage2_id.id not in (canceled_state2_po_1, canceled_state2_po_2, canceled_state2_po_3, canceled_state2_po_4, canceled_state2_po_5):
                raise UserError(_("Ce PO ne peut plus être modifié car le PO est au statut Annulé."))

            validated_state2_po_marchandise = self.env.ref('hm_purchase.purchase_stage5_po_marchandise').id
            validated_state2_po_emport_marchandise = self.env.ref(
                'hm_purchase.purchase_stage2_po_emport_marchandise').id
            validated_state2_po_technicien = self.env.ref('hm_purchase.purchase_stage2_po_technicien').id
            validated_state2_po_commission = self.env.ref('hm_purchase.purchase_stage2_po_commission').id
            if record.hm_so_lie and record.hm_so_lie.id == 3002 and record.stage2_id.id in (validated_state2_po_marchandise, validated_state2_po_emport_marchandise, validated_state2_po_technicien, validated_state2_po_commission) and not self.env.user.has_group('purchase.group_purchase_manager'):
                raise AccessError(_("Seuls les membres du groupe Achats > Administrateur peuvent passer un PO lié au %s en statut 'Clôturé'.")%record.hm_so_lie.name)

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PurchaseOrder, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        view_id = self.env.ref('hm_purchase.hm_so_purchase_order_tree_view').id
        doc = etree.XML(res['arch'])
        sale_order_id = self._context.get('active_id')
        if not sale_order_id or self._context.get('active_model') != 'sale.order':
            return res
        if view_id and view_type == 'tree':
            sale_order = self.env['sale.order'].browse(sale_order_id)
            if (sale_order.state == 'sale' and sale_order.state2 in ('to_invoice', 'invoiced')) or sale_order.state in ('draft', 'sent', 'cancel'):
                doc.set('create', 'false')
                doc.set('edit', 'false')
            else:
                return res
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        # if 'hm_imputed_technician_id' not in res:
        #     res['hm_imputed_technician_id'] = self.hm_imputed_technician_id and self.hm_imputed_technician_id.id or False
        if 'sale_id' not in res:
            res['sale_id'] = self.hm_so_lie and self.hm_so_lie.id or False
        # if 'hm_responsible_return_goods' not in res:
        #     res['hm_responsible_return_goods'] = self.hm_person_who_will_do_the_kidnapping_id and self.hm_person_who_will_do_the_kidnapping_id.id or False
        return res

    @api.constrains('hm_so_lie')
    def _check_hm_so_lie(self):
        for record in self:
            if record.po_type == 'po_frais_generaux' and record.hm_so_lie:
                raise UserError(
                    _("Ce PO ne peut pas avoir le type PO frais généraux car le SO lié est défini."))

    def action_credit_note_send(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']

        template_id = self.env['mail.template'].with_context(lang='fr_BE').search([
            '|',
            ('name', 'ilike', 'Réclamation note de crédit'),
            ('name', 'ilike', 'Réclamation NC')
        ], limit=1).id

        if not template_id:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'active_model': 'purchase.order',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.model_create_multi
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        for values in vals:
            if 'hm_so_lie' in values:
                sale_order = self.env['sale.order'].search([('id', '=', values['hm_so_lie'])])
                if sale_order.state2 in ('to_invoice', 'invoiced'):
                    raise UserError(_("Vous ne pouvez pas ajouter un autre bon de commande lorsque state2 est %s.") % (sale_order.state2))
                if not res.hm_so_lie:
                    res.hm_so_lie = sale_order
            stage2_id = self.env['purchase.stage'].search([('po_type', '=', res.po_type)], limit=1, order='sequence')
            res.stage2_id = stage2_id and stage2_id.id or False
            self.onchange_po_type()
            for order_line in res.order_line:
                order_line.onchange_product()
        return res

    def write(self, vals):
        old_partner_id = self.partner_id
        super(PurchaseOrder, self).write(vals)
        if vals.get('order_line'):
            order_line_id = vals.get('order_line')[0]
            if order_line_id and order_line_id[1]:
                if 'virtual_' in str(order_line_id[1]):
                    product_id = self.env['product.product'].browse(order_line_id[2]['product_id'])
                    if product_id.property_account_expense_id:
                        property_account_expense_code = product_id.property_account_expense_id.code
                        if property_account_expense_code in ('613100', '613040'):
                            self.po_type = 'po_commission'
                else:
                    sale_order_line_id = self.env['purchase.order.line'].browse(order_line_id[1])
                    if sale_order_line_id.product_id.property_account_expense_id:
                        property_account_expense_code = sale_order_line_id.product_id.property_account_expense_id.code
                        if property_account_expense_code in ('613100', '613040'):
                            self.po_type = 'po_commission'
        if 'partner_id' in vals:
            default, _, external = self.env['mail.message.subtype'].default_subtypes('purchase.order')
            partner_ids = self.partner_id.ids
            customer_ids = (
                self.env['res.partner'].sudo().search([('id', 'in', partner_ids), ('partner_share', '=', True)]).ids)
            partner_subtypes = dict(
                (pid, external.ids if pid in customer_ids else default.ids)
                for pid in partner_ids)

            fol_id = self.env['mail.followers'].sudo().create(
                {
                    'partner_id': self.partner_id.id,
                    'res_model': 'purchase.order',
                    'subtype_ids': [(6, 0, partner_subtypes[self.partner_id.id])],
                }
            )
            old_fol = self.env['mail.followers'].search(
                [
                    ('partner_id', '=', old_partner_id.id),
                    ('res_model', '=', 'purchase.order'),
                    ('res_id', '=', self.id),
                ]
            )
            old_fol.sudo().unlink()
            message_follower_ids = [(4, fol_id.id)]
            self.sudo().write({'message_follower_ids': message_follower_ids})
        if 'state' in vals:
            if self.state == 'cancel':
                if self.po_type == 'po_technicien':
                    canceled_state2_po = self.env.ref('hm_purchase.purchase_stage3_po_technicien').id

                elif self.po_type == 'po_marchandise':
                    canceled_state2_po = self.env.ref('hm_purchase.purchase_stage6_po_marchandise').id

                elif self.po_type == 'po_emport_marchandise':
                    canceled_state2_po = self.env.ref('hm_purchase.purchase_stage3_po_emport_marchandise').id

                elif self.po_type == 'po_commission':
                    canceled_state2_po = self.env.ref('hm_purchase.purchase_stage3_po_commission').id

                elif self.po_type == 'po_frais_generaux':
                    canceled_state2_po = self.env.ref('hm_purchase.purchase_stage5_po_frais').id

                self.stage2_id = canceled_state2_po
            else:
                stage2_id = self.env['purchase.stage'].search([('po_type', '=', self.po_type)], limit=1, order='sequence')
                self.stage2_id = stage2_id and stage2_id.id or False
        if 'stage2_id' in vals:
            self.groupby_stage2_name = self.stage2_id and self.stage2_id.name or ''
        if 'partner_ref' in vals and self.stage2_id and self.stage2_id.id in [self.env.ref('hm_purchase.purchase_stage1_po_marchandise').id,
                                                        self.env.ref('hm_purchase.purchase_stage1_po_emport_marchandise').id,
                                                        self.env.ref('hm_purchase.purchase_stage1_po_technicien').id,
                                                        self.env.ref('hm_purchase.purchase_stage1_po_commission').id,
                                                        self.env.ref('hm_purchase.purchase_stage1_po_frais').id,
                                                        self.env.ref('hm_purchase.purchase_stage2_po_marchandise').id,
                                                        self.env.ref('hm_purchase.purchase_stage2_po_frais').id]:
            self.stage2_id = self.env.ref('hm_purchase.purchase_stage3_po_marchandise').id
            self.date_confirm = fields.Datetime.now()
        if 'stage2_id' in vals and vals.get('stage2_id', False) in [self.env.ref('hm_purchase.purchase_stage3_po_marchandise').id, self.env.ref('hm_purchase.purchase_stage3_po_frais').id]:
            self.date_confirm = fields.Datetime.now()

    def button_cancel(self):
        if self.mapped("invoice_ids"):
            raise UserError( _("⚠️ Annulation impossible : ce bon de commande est associé à des factures fournisseurs."))
        else:
            result = super(PurchaseOrder, self).button_cancel()
            return result