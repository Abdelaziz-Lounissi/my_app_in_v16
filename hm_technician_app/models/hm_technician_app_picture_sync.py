# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
import json
import ast
import logging

_logger = logging.getLogger(__name__)


class TechnicianAppPictureSync(models.Model):
    _name = "hm.technician.app.picture.sync"
    _description = "Technician app picture sync"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", compute='_compute_name')
    res_id = fields.Integer("Ressource ID")
    model_name = fields.Char("Model", required=True)
    request_value = fields.Text("Request", tracking=True)
    original_image = fields.Image("Image", max_width=1920, max_height=1920)
    tech_uid = fields.Integer("Technician ID", required=True)
    active = fields.Boolean(default=True, tracking=True)
    pic_library_id = fields.Many2one("hm.picture.library", string="Picture ID")

    state = fields.Selection([
        ('to_sync', 'To sync'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ], string='State', copy=False, index=True, tracking=True, default='to_sync')

    def _compute_name(self):
        for rec in self:
            try:
                rec.name = self.env[rec.model_name].browse(int(rec.res_id)).display_name
            except Exception as e:
                rec.name = '/'

    def get_datas(self, request_value):
        datas = {}
        res = ast.literal_eval(request_value)
        return res

    @api.model
    def sync_technician_app_picture(self):
        skip_sync_technician_app_picture = self.env.context.get('skip_sync_technician_app_picture', False)
        if self.model_name == 'sale.order' and not skip_sync_technician_app_picture:
            if self.res_id and self.tech_uid and self.request_value:
                try:
                    datas = self.get_datas(self.request_value)

                    library_obj = self.env['hm.picture.library']
                    library_so_info_obj = self.env['hm.picture.so.info']
                    original_image = self.original_image
                    caption = datas.get('caption', '')
                    is_client_signature = bool(datas.get('is_client_signature', False))

                    pic_library_id = self.pic_library_id
                    if not self.pic_library_id and original_image:
                        pic_library_id = library_obj.create({
                            'original_image': original_image,
                            'sale_order_ids': [(6, 0, [self.res_id])],
                            'is_technicien_report_picture':True,
                            'is_client_signature':is_client_signature
                        })

                    if caption:
                        pic_library_info_id = library_so_info_obj.search(
                            [('hm_picture_library_id', '=', pic_library_id.id), ('hm_so_id', '=', self.res_id)])
                        if pic_library_info_id:
                            pic_library_info_id.write({'caption':caption})

                    self.pic_library_id = pic_library_id.id
                    self.state = 'synced'
                    return pic_library_id.id
                except Exception as e:
                    self.state = 'failed'


    @api.model
    def delete_picture(self, value_list):
        """Delete picture from Tech App JSON request."""
        picture_sync_id = value_list.get('picture_sync_id')
        tech_uid = value_list.get('tech_uid')

        if not (picture_sync_id and tech_uid):
            # return False, "This record does not exist or was deleted"
            return False

        picture_sync_rec = self.with_context(skip_sync_technician_app_picture=True).search([('id', '=', picture_sync_id)])

        if not picture_sync_rec:
            # return False, "Record not found"
            return False

        if not (picture_sync_rec.tech_uid and picture_sync_rec.tech_uid == tech_uid):
            picture_sync_rec.message_post(body="""<div class="o_thread_message_content">
                                          <span>User unauthorized to delete this image : %s</span>
                                      </div>""" % (tech_uid))
            # return False, "User unauthorized to delete this image"
            return False

        picture_id = picture_sync_rec.pic_library_id

        if picture_id:
            check_lead = picture_id.lead_ids
            check_icr = self.env['hm.picture.icr.info'].search([('hm_picture_library_id', '=', picture_id.id)])
            check_work_report = self.env['hm.picture.wr.info'].search([('hm_picture_library_id', '=', picture_id.id)])
            so_id = self.env[picture_sync_rec.model_name].search([('id', '=', picture_sync_rec.res_id)])

            if check_lead or check_icr or check_work_report:
                picture_sync_rec.message_post(body="""<div class="o_thread_message_content">
                                              <span>L'image ne peut pas être supprimée car elle est liée à d'autres documents que le %s:</span>
                                              <ul class="o_mail_thread_message_tracking">
                                                  <li>Lead(s):<span>%s</span></li>
                                                  <li>ICR(s):<span>%s</span></li>
                                                  <li>Work report(s):<span>%s</span></li>
                                              </ul>
                                          </div>""" % (
                so_id.name, check_lead.ids, check_icr.ids, check_work_report and check_work_report.wk_id.ids or []))
                # return False, "The image cannot be deleted because it is linked to other Leads, ICRs, work reports."
                return False
            else:
                picture_sync_rec.original_image = False
                picture_id.unlink()
                picture_sync_rec.active = False
                # return True, "Ok"
                return True
        else:
            # return False, "Image already deleted"
            return False

    def write(self, values):
        if values and 'original_image' in values and values['original_image']:
            if self.pic_library_id and not self.pic_library_id.is_client_signature:
                del values['original_image']
            else:
                self.pic_library_id.write({"original_image":values['original_image'] })
        res = super(TechnicianAppPictureSync, self).write(values)
        return res

    @api.model
    def cleanup_synced_images(self):
        rec_ids = self.env['ir.attachment'].search([('res_model', '=', 'hm.technician.app.picture.sync'), ('res_field', '=', 'original_image')], limit=1000)
        picture_sync_obj = self.env['hm.technician.app.picture.sync']
        sale_order_obj = self.env['sale.order']
        for rec in rec_ids:
          picture_sync = picture_sync_obj.browse(rec.res_id)
          if picture_sync and picture_sync.state == 'synced' and picture_sync.res_id and picture_sync.model_name=='sale.order':
              sale_order = sale_order_obj.browse(picture_sync.res_id)
              if sale_order.state2 in ('to_invoice', 'report_sent', 'invoiced'):
                  rec.unlink()

