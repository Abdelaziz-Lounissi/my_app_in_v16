# -*- encoding: utf-8 -*-

from odoo import fields, models, api, _


class HmWorkType(models.Model):
    _name = 'hm.work.type'
    _description = 'Work type'

    name = fields.Char(string="Name", translate=True)
    hm_access_profession_id = fields.Many2one("hm.access.profession", string="Accès à la profession", store=True,
                                              copy=False, ondelete="set null", index=False)
