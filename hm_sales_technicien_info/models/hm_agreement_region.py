# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models


class HmAgreementRegion(models.Model):
    _name = 'hm.agreement.region'
    _description = 'Agreement Region'

    agreement_id = fields.Many2one('hm.agreement', string='Agreement')
    region = fields.Many2one('region.code', string='Région')
    partner_id = fields.Many2one('res.partner')
    name = fields.Char(string='Nom', compute='_compute_name_complete', store=True)
    hm_category_competence_id = fields.Many2one("hm.category.competence", string="Catégorie de compétence", copy=False,
                                                store=True, ondelete="set null", index=False)
    hm_access_profession_id = fields.Many2one("hm.access.profession", string="Accès à la profession", copy=False,
                                              store=True, index=False, ondelete="set null")

    @api.depends('region.name', 'agreement_id.name')
    def _compute_name_complete(self):
        for rec in self:
            names = []
            if rec.region:
                names.append(rec.region.name)
            if rec.agreement_id:
                names.append(rec.agreement_id.name)
            rec.name = ' / '.join(names)

    @api.constrains('region', 'agreement_id')
    def _check_region_agreement(self):
        for rec in self:
            check_count = self.search_count(
                [
                    ('region', '=', rec.region.id),
                    ('agreement_id', '=', rec.agreement_id.id),
                ]
            )
            if check_count > 1:
                raise exceptions.ValidationError(_('Region and Agreement must be unique!'))
