# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from datetime import date
from datetime import timedelta


class HmPictureWizard(models.TransientModel):
    _name = "hm.picture.library.wizard"
    _description = "Hm Picture Library Wizard"

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', copy=False, required=True, ondelete='cascade')

    hm_so_id = fields.Many2one('sale.order', string="SO")
    hm_lead_id = fields.Many2one('crm.lead', string="Lead")

    def action_save(self):
        action = {}
        action = self.env.ref('hm_picture_library.hm_picture_library_action').read()[0]
        for rec in self.attachment_ids:
            picture_id = self.env['hm.picture.library'].create({"original_image": rec.datas})
            if picture_id and self.hm_lead_id:
                picture_id.write({"lead_ids": [(4, self.hm_lead_id and self.hm_lead_id.id)]})
                action = {'type': 'ir.actions.act_window', 'res_model': 'crm.lead', 'res_id': self.hm_lead_id.id,
                          'view_mode': 'form'}
            if picture_id and self.hm_so_id:
                action = {'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'res_id': self.hm_so_id.id,
                          'view_mode': 'form'}
                picture_id.write({"sale_order_ids": [(4, self.hm_so_id and self.hm_so_id.id)]})
        return action
