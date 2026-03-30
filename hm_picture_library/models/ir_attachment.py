# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    picture_id = fields.Many2one('hm.picture.library', string="Picture library")

    def _check_picture_is_ignored(self):
        file_size_min = self.env["ir.config_parameter"].sudo().get_param("hm_picture_library_file_size_min")
        res = int(file_size_min) < self.file_size
        return bool(res)

    # create new picture.library if the attachment is Image in Sale order or Crm lead
    def _create_picture_library_from_attachments(self):
        if self._check_picture_is_ignored() and self.res_model in ('crm.lead', 'sale.order') and self.res_id and self.mimetype.startswith('image') and self.name != 'signature':
            record_id = self.env[self.res_model].browse(self.res_id)
            if self.res_model == 'crm.lead':
                datas = {"original_image": self.datas, "lead_ids": [(4, record_id.id)]}
            else:
                datas = {"original_image": self.datas, "sale_order_ids": [(4, record_id.id)]}
            picture_id = self.env['hm.picture.library'].create(datas)
            self.picture_id=picture_id.id

    # update new picture.library if the attachment is Image in Sale order or Crm lead
    def _update_picture_library_from_attachments(self):
        if self._check_picture_is_ignored() and self.res_model in ('crm.lead', 'sale.order') and self.res_id and self.mimetype.startswith('image') and self.name != 'signature' and not self.picture_id:
            record_id = self.env[self.res_model].browse(self.res_id)
            if self.res_model == 'crm.lead':
                datas = {"original_image": self.datas, "lead_ids": [(4, record_id.id)]}
            else:
                datas = {"original_image": self.datas, "sale_order_ids": [(4, record_id.id)]}
            picture_id = self.env['hm.picture.library'].create(datas)
            self.picture_id = picture_id.id
