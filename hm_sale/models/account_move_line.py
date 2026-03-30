# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    spec = fields.Text(string='Spec', compute='_compute_spec')

    @api.depends('sale_line_ids.spec')
    def _compute_spec(self):
        for rec in self:
            spec_lines = []
            for line in rec.sale_line_ids.filtered(lambda l: l.spec):
                spec_lines.append('>> ' + str(line.spec))
            rec.spec = '\n'.join(spec_lines)
