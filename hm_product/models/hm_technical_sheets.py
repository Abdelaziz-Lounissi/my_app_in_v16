# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HmTechnicalSheets(models.Model):
    _name = "hm.technical.sheets"
    _description = "Technical Sheets"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", copy=True, store=True, index=False, translate=False)
    hm_stage_id = fields.Many2one("hm.technical.sheets.stages", store=True, index=False, copy=False, string="Stage",
                                  ondelete="set null")
    hm_technical_sheet_category = fields.Selection(
        [("Reglementation", "Reglementation"), ("Régulation", "Régulation"), ("Primes", "Primes"),
         ("Matériel chauffage", "Matériel chauffage"), ("Matériel sanitaire", "Matériel sanitaire"),
         ("Dimensionnement", "Dimensionnement"), ("Commercial", "Commercial")], string="Catégorie fiche technique",
        copy=False, store=True, index=False)
    hm_doc_1 = fields.Binary(string="Doc 1", copy=False, store=True, index=False)
    hm_doc_1_filename = fields.Char(string="Filename for hm_doc_1", copy=False, store=True, index=False,
                                    translate=False)
    hm_doc_2_pdf = fields.Binary(string="Doc 2 (PDF)", copy=False, store=True, index=False)
    hm_doc_2_filename = fields.Char(string="Filename for hm_doc_2_pdf", copy=False, store=True, index=False,
                                    translate=False)
    hm_doc_3_pdf = fields.Binary(string="Doc 3 (PDF)", copy=False, store=True, index=False)
    hm_doc_3_filename = fields.Char(string="Filename for hm_doc_3_pdf", copy=False, store=True, index=False,
                                    translate=False)
    hm_text_technical_info = fields.Html(string="Texte info technique", store=True, copy=True,
                                         translate=False, index=False)


class HmTechnicalSheetsStages(models.Model):
    _name = "hm.technical.sheets.stages"
    _description = "Technical Sheets Stages"

    name = fields.Char(string="Name", copy=False, store=True, index=False, translate=False)
