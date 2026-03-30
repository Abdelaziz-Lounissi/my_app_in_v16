# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HmCategoryCompetence(models.Model):
    _name = "hm.category.competence"
    _description = "Category competence"

    name = fields.Char(string="Name", copy=False, store=True, index=False, translate=False)
