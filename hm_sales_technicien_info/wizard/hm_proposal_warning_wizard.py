# -*- encoding: utf-8 -*-

from odoo import fields, models, api, _


class HmProposalWarningWizard(models.TransientModel):
    _name = 'hm.proposal.warning.wizard'
    _description = 'Proposal Warning Wizard'

    warning_message = fields.Text(string='Warning Message', readonly=True)

    def confirm_action(self):
        context = self.env.context
        proposal_ids = context.get('proposal_ids', False)
        proposal_ids = self.env['hm.technician.intervention.proposal'].browse(proposal_ids)
        for proposal in proposal_ids.filtered(lambda x: x.state == 'shortlisted'):
            proposal.with_context(force_send_proposal=True).send_proposal()
        return {'type': 'ir.actions.act_window_close'}

    def cancel_action(self):
        return {'type': 'ir.actions.act_window_close'}
