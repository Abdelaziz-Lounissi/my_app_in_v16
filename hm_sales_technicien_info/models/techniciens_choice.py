# -*- encoding: utf-8 -*-


from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class techniciens_choice(models.Model):
    _name = "techniciens.choice"
    _description = "Techniciens choice"

    sale_order_id = fields.Many2one('sale.order', string='sale order', ondelete="cascade", )
    sale_id = fields.Many2one('sale.order', string='Ref sale order', ondelete="cascade", )
    partner_id = fields.Many2one('res.partner', string='Technician', required=True)
    zip = fields.Char(related='partner_id.zip', string='zip')
    city = fields.Char(related='partner_id.city', string='Ville')

    work_type_ids_tech = fields.Many2many('hm.work.type', string='Work type', readonly=False)
    agremeent_ids_tech = fields.Many2many('hm.agreement', string='Agremeents', readonly=False)

    status = fields.Selection(
        [('traiter', 'A traiter'), ('propose_client', 'Proposé technicien'), ('accepte', 'Accepté'),
         ('refuser', 'Refusé'), ('annuler', 'Annulé')],
        string='Status', default='traiter', required=True)
    old_status = fields.Selection(
        [('traiter', 'A traiter'), ('propose_client', 'Proposé technicien'), ('accepte', 'Accepté'),
         ('refuser', 'Refusé'), ('annuler', 'Annulé')],
        string='Status Old', default='traiter')
    sequence = fields.Integer(string='Sequence', default=10)
    hm_availablity = fields.Many2one("technician.availability", related="partner_id.hm_technician_availability_id", readonly=True,
                                      store=True, string="Availability", copy=False, index=False)
    hm_availablity_1 = fields.Many2one("technician.availability", related="partner_id.hm_technician_availability_id", readonly=True,
                                        store=True, copy=False, string="HM Availability", index=False)

    def action_add_technician(self):
        intervention_proposal_obj = self.env['hm.technician.intervention.proposal']
        intervention_proposal_obj.create({
            'partner_id': self.partner_id.id,
            'sale_order_id': self.sale_order_id.id,
        })
        self.sale_order_id.selected_tech_choice_ids = False
        # If we add a new proposal, and we have already notified the SO manager that all proposals have been sent,
        # we need to notify the SO manager again after the automatic sending for this new proposal.
        self.sale_order_id.notify_so_manager_byproposals = False
        if (self.sale_order_id.proposal_lines or self.sale_order_id.send_proposals == 'in_batches') and not self.sale_order_id.hm_so_manager_id:
            self.sale_order_id.hm_so_manager_id = self.env.user.id

    @api.onchange('partner_id')
    def on_change_partner_id(self):
        if self.partner_id:
            self.work_type_ids_tech = self.partner_id and self.partner_id.work_type_ids or False
            list_agremeent_reg_ids = self.partner_id.agremeent_reg_ids.mapped('agreement_id').ids
            self.agremeent_ids_tech = [(6, 0, list_agremeent_reg_ids)]

    @api.onchange('status')
    def onchange_status(self):
        if self.status and self.status == 'accepte':
            self.old_status = self._origin.status

    def delete_unused_technicians_choices(self):
        rec_ids = self.env['techniciens.choice'].search([
            '|',
            ('sale_order_id.state2', 'in', ['report_sent', 'to_invoice', 'invoiced']),
            ('sale_order_id.state', '=', 'cancel')
        ])
        for rec in rec_ids:
            _logger.info('--** Unlink Tech. choice ID: %s ' % rec.id)
            rec.sudo().unlink()
