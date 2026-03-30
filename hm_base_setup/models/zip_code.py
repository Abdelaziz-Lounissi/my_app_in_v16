# -*- coding: utf-8 -*-
# Merge module hm_base

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ZipCode(models.Model):
    _name = 'zip.code'
    _description = 'Zip Code'
    _rec_name = 'name'

    @api.depends('local', 'zip')
    def _compute_name_complete(self):
        for rec in self:
            rec.name = '{} : {}'.format(rec.local and rec.local.upper() or '', rec.zip)

    name = fields.Char(compute='_compute_name_complete', string='Complete name', store=True)
    zip = fields.Char(string='Zip', required=True)
    local = fields.Char(string='Localité', required=True)
    sous_commune = fields.Boolean('Sous-Commune')
    commune_principale = fields.Char('Commune Principale')
    state_id = fields.Many2one(comodel_name='res.country.state', string='Province', required=True)
    code_pays = fields.Many2one(comodel_name='res.country', string='Country', related='state_id.country_id', readonly=False,
                                required=True)
    sous_province = fields.Many2one(comodel_name='sub.province', string='Sous province')

    _sql_constraints = [
        (
            'zip_zip_code_unique',
            'CHECK(1 > 0)',
            'Le code postal doit étre unique !',
        )
    ]

    @api.constrains('zip', 'local')
    def _constrains_zip_code_unique(self):
        zip_code_count = self.search_count([('zip', '=', self.zip), ('local', '=', self.local)])
        if zip_code_count > 1:
            raise ValidationError(_('Le couple code postal , localité doit étre unique !'))

    @api.onchange('zip')
    def onchange_zip(self):
        if self.zip:
            if not self.zip.isnumeric():
                raise UserError(_('Le code postale doit étre un entier'))
            if int(self.zip) < 0:
                raise UserError(_('Le code postale doit étre positif'))
