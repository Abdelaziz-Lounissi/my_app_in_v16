# -*- coding: utf-8 -*-

from odoo import models, fields,api
from odoo.tools import float_compare


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    has_negative_po_balance = fields.Boolean(
        string="Solde de BC négatif",
        compute="_compute_has_negative_po_balance",
        store=True,
        help="Indique si le fournisseur/technicien a un solde négatif sur les bons de commande non facturés"
    )

    @api.depends('partner_id')
    def _compute_has_negative_po_balance(self):
        """
        Vérifie si le fournisseur/technicien a un solde négatif sur les bons de commande
        non facturés, ce qui nécessiterait de traiter d'abord les notes de crédit.
        """
        purchase_order_obj = self.env['purchase.order']
        for record in self:
            record.has_negative_po_balance = False
            if not record.partner_id:
                continue

            technician_id = record.partner_id
            domain = [
                ('partner_id', '=', technician_id.id),
                ('po_type', 'in', ('po_technicien', 'po_emport_marchandise')),
                ('stage2_id', 'in', (
                    record.env.ref('hm_purchase.purchase_stage2_po_technicien').id,
                    record.env.ref('hm_purchase.purchase_stage2_po_emport_marchandise').id
                )),
                ('state', '=', 'purchase'),
                ('invoice_status', '!=', 'invoiced'),
                ('hm_po_deleted_from_portal', '=', False)
            ]

            relevant_pos = purchase_order_obj.search(domain)
            total_po_amount = sum(po.amount_total for po in relevant_pos)

            if float_compare(total_po_amount, 0.0, precision_rounding=record.currency_id.rounding) < 0:
                record.has_negative_po_balance = True


    @api.depends('available_journal_ids')
    def _compute_journal_id(self):
        for wizard in self:
            # custom : get the journal from the payment methode from the current supplier
            if wizard.partner_id and wizard.partner_id.supplier_payment_mode_id and wizard.partner_id.supplier_payment_mode_id.fixed_journal_id:
                fixed_journal_id = wizard.partner_id.supplier_payment_mode_id.fixed_journal_id
                wizard.journal_id = fixed_journal_id

            # else keep executing the standard workflow
            elif wizard.can_edit_wizard:
                batch = wizard._get_batches()[0]
                wizard.journal_id = wizard._get_batch_journal(batch)
            else:
                wizard.journal_id = self.env['account.journal'].search([
                    ('type', 'in', ('bank', 'cash')),
                    ('company_id', '=', wizard.company_id.id),
                    ('id', 'in', self.available_journal_ids.ids)
                ], limit=1)

    @api.depends('payment_type', 'journal_id')
    def _compute_payment_method_line_id(self):
        for wizard in self:
            # custom : get the payment methode from the current supplier
            payment_method_line_id = False
            if wizard.partner_id and wizard.partner_id.supplier_payment_mode_id and wizard.partner_id.supplier_payment_mode_id.fixed_journal_id:
                supplier_payment_method_id = wizard.partner_id.supplier_payment_mode_id.payment_method_id
                payment_method_line_id = wizard.journal_id.outbound_payment_method_line_ids.filtered(lambda x: x.payment_method_id == supplier_payment_method_id)

            if payment_method_line_id:
                wizard.payment_method_line_id = payment_method_line_id and payment_method_line_id.id or False
            # else keep executing the standard workflow
            else:
                if wizard.journal_id:
                    available_payment_method_lines = wizard.journal_id._get_available_payment_method_lines(wizard.payment_type)
                else:
                    available_payment_method_lines = False

                # Select the first available one by default.
                if available_payment_method_lines:
                    wizard.payment_method_line_id = available_payment_method_lines[0]._origin
                else:
                    wizard.payment_method_line_id = False

