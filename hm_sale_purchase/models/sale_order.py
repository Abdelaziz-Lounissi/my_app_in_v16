# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

# TODO: move to hm_sale
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    hm_imputed_technician_id = fields.Many2one('res.partner', string='Technicien', store=True, copy=False,
                                               index=False, ondelete='set null', tracking=True)
    hm_so_manager_id = fields.Many2one('res.users', string='SO Manager', store=True, copy=False, index=False,
                                       ondelete='set null')
    hm_so_manager_phone = fields.Char(string='Numéro de téléphone gestionnaire SO', readonly=True, store=True, related_sudo=True,
                                           index=False, related='hm_so_manager_id.phone')
    state2 = fields.Selection(selection=[
        ('deposit_to_receive', 'Acompte à recevoir'),
        ('to_organize', 'À organiser'),
        ('planned', 'Planifié'),
        ('tech_on_the_way', 'En route'),
        ('in_progress', 'En cours'),
        ('paused', 'En pause'),
        ('report_to_send', 'En attente rapport'),
        ('report_sent', 'A clôturer'),
        ('to_invoice', 'A facturer'),
        # ('closed', 'Clôturé'),
        ('invoiced', 'Facturé'),
        # ('validated', 'Approuvé'),
    ], string='State2 SO', copy=False, index=True, tracking=True, default='to_organize')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    hm_technical_info = fields.Text(string='Infos tech', store=True, copy=True, translate=False, index=False)
