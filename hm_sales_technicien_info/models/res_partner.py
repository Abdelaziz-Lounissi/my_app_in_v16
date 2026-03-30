# -*- encoding: utf-8 -*-
# ############################################################################
#

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    agremeent_reg_ids = fields.Many2many('hm.agreement.region', string='HM Agreements')
    work_type_ids = fields.Many2many('hm.work.type', 'hm_work_type_res_partner_rel', 'res_partner_id',
                                     'hm_work_type_id', string='Work type')
    agremeent_ids_tech = fields.Many2many('hm.agreement', string='Agremeents')
    region_tech = fields.Many2many('region.code', string='Sous-région')
    proposal_lines = fields.One2many('hm.technician.intervention.proposal', 'partner_id', string='Proposals')

    @api.onchange('agremeent_reg_ids')
    def onchange_agremeent_reg_ids(self):
        if self.agremeent_reg_ids:
            list_agremeent_reg_ids = self.agremeent_reg_ids.mapped('agreement_id').ids
            list_region_tech = self.agremeent_reg_ids.mapped('region').ids
            self.agremeent_ids_tech = [(6, 0, list_agremeent_reg_ids)]
            self.region_tech = [(6, 0, list_region_tech)]
        else:
            self.agremeent_ids_tech = [(6, 0, [])]
            self.region_tech = [(6, 0, [])]

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.context.get('technicien_agremeent_region_search', False):
            new_domain = []
            agremeent_names = []
            for dom in domain:
                if type(dom) == list and dom[0] == 'agremeent_reg_ids':
                    agremeent_names.append(dom)
                else:
                    new_domain.append(dom)

            if agremeent_names:
                dict_agremeent_names = agremeent_names[0][2]
                if type(dict_agremeent_names) == list:
                    for operator_list in range(1, len(dict_agremeent_names)):
                        new_domain.append('|')

                    for agremeent_name in dict_agremeent_names:
                        new_domain.append(['agremeent_reg_ids', 'ilike', agremeent_name])

                    domain = new_domain
        return super(ResPartner, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                   order=order)
