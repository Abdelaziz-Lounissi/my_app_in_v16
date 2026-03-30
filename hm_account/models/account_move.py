# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_id = fields.Many2one('sale.order', string='Origin Order')

    # x_studio_bien_immobilier
    hm_property_id = fields.Many2one("hm.property", string="Property",
                                     related="sale_order_id.property_id", ondelete="set null", readonly=True,
                                     store=True, copy=False, index=False, related_sudo=True)
    # x_studio_catgorie_de_travaux
    hm_work_category = fields.Many2one("hm.works.category", string="Catégorie de travaux",
                                       related="sale_order_id.hm_work_category", readonly=True,
                                       ondelete="set null", copy=False, store=True, index=False, related_sudo=True)
    # x_studio_catgorie_de_travaux_parent
    hm_parent_work_category = fields.Many2one("hm.works.category.parent",
                                              string="Catégorie de travaux parent",
                                              related="sale_order_id.hm_parent_work_category",
                                              readonly=True, ondelete="set null", store=True, copy=False,
                                              index=False, related_sudo=True)
    # x_studio_date_dintervention
    hm_intervention_date = fields.Datetime(string="Intervention date",
                                           help="This is the delivery date promised to the customer. If set, the delivery order will be scheduled based on this date rather than product lead times.",
                                           store=True,
                                           related="invoice_line_ids.sale_line_ids.order_id.commitment_date",
                                           copy=False, index=False, related_sudo=True)
    # x_studio_gestionnaire_1
    hm_manager1 = fields.Many2one("res.partner", string="Manager", related="sale_order_id.manager_id",
                                  readonly=True, ondelete="set null", copy=False, store=True, index=False,
                                  related_sudo=True)
    # x_studio_numero_tva
    hm_vat_number = fields.Char(string="VAT Number", related="partner_id.vat", readonly=True, store=True,
                                copy=False,
                                help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.",
                                index=False, translate=False)
    # x_studio_obligation_de_retenue_1
    hm_withholding_obligation = fields.Binary(string="Withholding obligation", store=True, copy=False,
                                              index=False)

    # x_studio_technicien
    hm_technician = fields.Boolean(string="Technician", related="partner_id.hm_technician", readonly=True, store=True, copy=False, index=False)

    hm_so_manager_id = fields.Many2one('res.users', related='sale_order_id.hm_so_manager_id', string='Gestionnaire SO',
                                       related_sudo=True)
    total_ticket = fields.Integer(compute='_compute_total_ticket')

    def _compute_total_ticket(self):
        helpdesk_obj = self.env['helpdesk.ticket']
        for move in self:
            res_count = 0
            if move.sale_order_id:
                res_count= helpdesk_obj.search_count([('sale_order_id', '=', move.sale_order_id.id)])
            move.total_ticket = res_count

    def action_view_ticket(self):
        helpdesk_obj = self.env['helpdesk.ticket']
        action = self.env.ref('helpdesk.helpdesk_ticket_action_main_my').read()[0]
        if self.sale_order_id:
            action['context'] = {
                'default_sale_order_id': self.sale_order_id.id,
            }
            action['domain'] = [('sale_order_id', '=', self.sale_order_id.id)]
            ticket_ids = helpdesk_obj.search([('sale_order_id', '=', self.sale_order_id.id)])
            if len(ticket_ids) <= 1:
                action['views'] = [(self.env.ref('helpdesk.helpdesk_ticket_view_form').id, 'form')]
                action['res_id'] = ticket_ids and ticket_ids.id or False
        return action

    # TODO: clean : product_is_lettre; product_is_print; product_is_email
    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('account.email_template_edi_invoice', False)
        compose_form = self.env.ref('account.account_invoice_send_wizard_form', False)

        product_is_email = self.partner_id.is_email_partner
        product_is_print = self.partner_id.is_print_partner
        product_is_lettre = self.partner_id.is_letter

        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            default_is_email=product_is_email,
            default_is_print=product_is_print,
            default_snailmail_is_letter=product_is_lettre,
            custom_layout="mail.mail_notification_paynow",
            force_email=True
        )
        return {
            'name': 'Send Invoice',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'is_email': False,
            'context': ctx,
        }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        # OVERRIDE
        # Cancel Recompute 'partner_shipping_id' based on 'partner_id'.
        partner_shipping_id = self.partner_shipping_id
        res = super(AccountMove, self)._onchange_partner_id()
        self.partner_shipping_id = partner_shipping_id and partner_shipping_id.id or False
        return res

    # TODO: replace 5 by 2 and 6 by 3 in template + methods
    def get_report_template(self):
        sale_order_id = self.sale_order_id
        acompte_product = self.env['product.product'].browse(35)
        template_number = False
        # 1: la facture à envoyer provient d'un SO
        # 5: la facture à envoyer est une facture d'acompte
        # 6: la facture à envoyer est une note de crédit
        if self.move_type == 'out_invoice':
            # Check if any line contains the 'acompte_product' for template number 5
            if any(line.product_id == acompte_product and line.quantity > 0 for line in self.invoice_line_ids):
                template_number = 5
            else:
                template_number = 1
        elif self.move_type == 'out_refund':
            template_number = 6

        return template_number

    # TODO: replace 5 by 2 and 6 by 3 in template + methods
    def get_template_subject(self):
        report_number = self.get_report_template()
        lang = self.sale_order_id.partner_id.lang
        template_subject_datas = {
            'fr_FR': {
                1: "{company_name} - Facture (Référence {so_number})",
                5: "{company_name} - Facture d'acompte (Référence {so_number})",
                6: "{company_name} - Note de crédit (Référence {so_number})",
            },
            'en_US': {
                1: "{company_name} - Invoice (Reference {so_number})",
                5: "{company_name} - Deposit Invoice (Reference {so_number})",
                6: "{company_name} - Credit Note (Reference {so_number})",
            },
            'nl_BE': {
                1: "{company_name} - Factuur (Referentie {so_number})",
                5: "{company_name} - Aanbetalingsfactuur (Referentie {so_number})",
                6: "{company_name} - Kredietnota (Referentie {so_number})",
            }
        }

        template_subject_data = template_subject_datas.get(lang, template_subject_datas['fr_FR']).get(report_number)

        if template_subject_data:
            template_subject_data = template_subject_data.format(
                company_name=self.company_id.name or self.env.company.name, so_number=self.sale_order_id.name or "/")
        else:
            template_subject_data = "{company_name} Facture (Ref {invoice_number})"
            template_subject_data = template_subject_data.format(
                company_name=self.company_id.name or self.env.company.name, invoice_number=self.name or 'n/a')
        return template_subject_data

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        sale_order = self.sale_order_id
        if sale_order:
            # TODO: debug invoice check when SO is invoiced
            # if (
            #         self.move_type == 'out_invoice'
            #         and sale_order.state2 == 'invoiced'
            #         and 'qr_code_method' not in vals
            # ):
            #     raise ValidationError("⚠️ Vous ne pouvez pas modifier une facture liée à un bon de commande en statut 'Facturé'.")

            sale_order._compute_amount_total_invoiced()
            invoiced_total = sale_order.amount_total_invoiced
            order_total = sale_order.amount_total
            currency_rounding = self.currency_id.rounding
            if (
                    float_compare(invoiced_total, order_total, precision_rounding=currency_rounding) == 0
                    and sale_order.state2 == 'to_invoice'
            ):
                sale_order.state2 = 'invoiced'

        return res

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        result = super(AccountMove, self).create(vals_list)
        for record in result:
            sale_order = record.sale_order_id
            if sale_order:
                # TODO: debug invoice check when SO is invoiced
                # if record.move_type == 'out_invoice' and sale_order.state2 == 'invoiced':
                #     raise ValidationError("⚠️ Vous ne pouvez pas créer une facture liée à un bon de commande en statut 'Facturé'.")

                sale_order._compute_amount_total_invoiced()
                invoiced_total = sale_order.amount_total_invoiced
                order_total = sale_order.amount_total
                currency_rounding = record.currency_id.rounding
                if (
                        float_compare(invoiced_total, order_total, precision_rounding=currency_rounding) == 0
                        and sale_order.state2 == 'to_invoice'
                ):
                    sale_order.state2 = 'invoiced'

        return result

    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        partner_id = self.partner_id
        res = super(AccountMove, self)._onchange_purchase_auto_complete()
        if partner_id:
            self.partner_id = partner_id
        # custom: disable the: Compute ref, Compute payment_reference
        if self.payment_reference or self.ref:
            self.payment_reference = ''
            self.ref = ''
        return res

    def js_assign_outstanding_line(self, line_id):
        res = super(AccountMove, self).js_assign_outstanding_line(line_id)
        lines = self.env['account.move.line'].browse(line_id)
        move_name = lines.ref or lines.name or ''
        self.with_context(action='assign').compute_payment_reference(move_name=move_name)
        return res

    def js_remove_outstanding_partial(self, partial_id):
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        move_id = partial.credit_move_id.move_id
        move_id.with_context(action='remove').compute_payment_reference(move_name=partial.credit_move_id.ref)
        move_id.with_context(action='remove').compute_payment_reference(move_name=partial.debit_move_id.ref)
        res = super(AccountMove, self).js_remove_outstanding_partial(partial_id)
        return res

    def compute_payment_reference(self, move_name):
        context = self.env.context
        action_type = context.get('action', False)
        payment_reference = self.payment_reference or ''

        if self.move_type in ['in_invoice', 'in_refund']:

            if action_type == 'remove' and payment_reference:
                if move_name and move_name in payment_reference:
                    payment_reference_list = [ref.strip() for ref in payment_reference.split(',') if
                                              ref.strip() != move_name]
                    payment_reference = ', '.join(payment_reference_list)

            elif action_type == 'assign':
                payment_reference_list = [ref.strip() for ref in payment_reference.split(',')] if payment_reference else []
                if move_name not in payment_reference_list:
                    payment_reference_list.append(move_name)
                payment_reference = ', '.join(payment_reference_list)

            if self.ref:
                if self.ref not in payment_reference:
                    payment_reference_list = [ref.strip() for ref in
                                              payment_reference.split(',')] if payment_reference else []
                    if self.ref not in payment_reference_list:
                        payment_reference_list.append(self.ref)
                    payment_reference = ', '.join(payment_reference_list)

        self.payment_reference = payment_reference

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self.filtered(lambda x: x.ref):
            move.payment_reference = move.ref

        # TODO: Activate the error message. Currently, there is a bug related to this method when confirming payment.
        # else:
        #     raise ValidationError("La référence de facture est obligatoire pour confirmer cette facture/note de crédit.")
        check_withholding_obligation = self.filtered(lambda mv: mv.hm_technician and mv.move_type != 'out_invoice' and not mv.hm_withholding_obligation)
        if check_withholding_obligation:
            raise ValidationError("⚠️ Impossible de comptabiliser la facture. Le champ 'Obligation de retenue' doit être rempli avant de pouvoir confirmer cette facture ou note de crédit.")

        return res



    def action_reverse(self):
        if self.move_type == 'out_invoice' and self.sale_order_id.state2 =='invoiced':
            raise ValidationError(
                "⚠️ Vous ne pouvez pas créditer une facture liée à un bon de commande en statut 'Facturé'."
            )
        return super().action_reverse()


    def action_reset_so_to_invoice(self):
        for rec in self:
            sale_order = rec.sale_order_id
            if sale_order and sale_order.state2 == "invoiced":
                sale_order.state2 = 'to_invoice'

