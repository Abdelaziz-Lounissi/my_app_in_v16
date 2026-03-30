# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class HmSoPrimeLine(models.Model):
    _name = "hm.so.primes.line"
    _description = "HeatMe : SO Primes Line"

    sequence = fields.Integer('Sequence')
    name = fields.Char('Name')
    hm_prime_id = fields.Many2one('hm.primes', 'Prime', required=True)
    hm_qty_prime = fields.Float('Quantity',default=1.0)
    hm_unit_price_prime = fields.Float('Unit Price')
    hm_currency_id = fields.Many2one("res.currency", string="Currency", store=True, copy=False, index=False,
                                     ondelete="set null")
    hm_subtotal_prime = fields.Monetary(compute='_compute_hm_prime_total', string='Total des primes disponibles', readonly=True, store=False,
                                       currency_field='hm_currency_id')
    sale_order_id = fields.Many2one('sale.order')
    country_id = fields.Many2one('region.code', string='Region', related="sale_order_id.property_id.state_id.region", ondelete='restrict', related_sudo=True)

    @api.depends('hm_qty_prime', 'hm_unit_price_prime')
    def _compute_hm_prime_total(self):
        for line in self:
            line.hm_subtotal_prime = line.hm_qty_prime * line.hm_unit_price_prime

    def action_view_prime(self):
        view = self.env.ref('hm_primes.hm_primes_view_form')
        return {
            'name': _('View prime'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hm.primes',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': self.hm_prime_id.id,
            'target': 'current',
        }

    @api.onchange('hm_prime_id')
    def onchange_prime(self):
        values = None
        filter_prime_ids = [data.hm_prime_id.id for data in self.sale_order_id.hm_premium_ids]
        if values is None:
            values = {}
        values['domain'] = {'hm_prime_id': [('id', 'not in', filter_prime_ids)]}
        self.hm_unit_price_prime = self.hm_prime_id.hm_basic_amount_of_the_premium
        return values
