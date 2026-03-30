# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PoStage(models.Model):
    _name = "purchase.stage"
    _description = "Purchase Stages"
    _rec_name = 'name'
    _order = "sequence, name, id"

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages.")
    po_type = fields.Selection(
        selection=[("po_marchandise", "PO Marchandise"), ("po_emport_marchandise", "PO Emport Marchandise"), ("po_technicien", "PO Technicien"), ("po_frais_generaux", "PO Frais Généraux"), ('po_commission', 'PO Commission')],
        string="PO Type", ondelete='set null', help='Specific purchase that uses this stage. Other purchases will not be able to see or use this stage.')