# -*- coding: utf-8 -*-

from odoo import api, fields, models
import ast


class TechnicianAppDocumentSync(models.Model):
    _name = "hm.technician.app.document.sync"
    _description = "Technician app document sync"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", compute='_compute_name')
    res_id = fields.Integer("Ressource ID")
    model_name = fields.Char("Model", required=True)
    request_value = fields.Text("Request", tracking=True)
    document = fields.Binary("Document")
    tech_uid = fields.Integer("Technician ID", required=True)
    active = fields.Boolean(default=True, tracking=True)
    attachment_id = fields.Many2one("ir.attachment", string="Attachment")

    state = fields.Selection([
        ('to_sync', 'To sync'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ], string='State', copy=False, index=True, tracking=True, default='to_sync')
    doc_type = fields.Selection([
        ('boiler_certificate', 'Boiler certificate'),
    ], string='Type', copy=False, index=True, tracking=True)

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
    def sync_technician_app_document(self):
        if self.res_id and self.tech_uid and self.request_value:
            try:
                record = self.env[self.model_name].browse(int(self.res_id))

                if self.env.user.id == record.hm_imputed_technician_id.user_ids[0].id:
                    datas = self.get_datas(self.request_value)
                    attachment_obj = self.env['ir.attachment']
                    document = self.document
                    doc_type = datas.get('type', False)
                    doc_name = datas.get('doc_name', '')

                    attachment_id = attachment_obj.sudo().create({
                        'datas': document,
                        'name': doc_name,
                        'res_model': self.model_name,
                        'res_id': self.res_id,
                        'hm_document_type': doc_type,

                    })

                    self.doc_type = doc_type
                    self.attachment_id = attachment_id.id
                    self.state = 'synced'
                    return self.id
                else:
                    self.message_post(body="""<div class="o_thread_message_content">
                                                  <span>User unauthorized to add this document : %s</span>
                                              </div>""" % (self.env.user.id))
                    self.state = 'failed'
                    return False
            except Exception as e:
                self.state = 'failed'
                self.message_post(body="""<div class="o_thread_message_content">
                                                  <span>Erreur : %s</span>
                                              </div>""" % (str(e)))

    @api.model
    def delete_document(self, value_list):
        """Delete document from Tech App JSON request."""
        document_sync_id = value_list.get('document_sync_id')
        tech_uid = value_list.get('tech_uid')

        if not (document_sync_id and tech_uid):
            # return False, "This record does not exist or was deleted"
            return False

        document_sync_rec = self.search([('id', '=', document_sync_id)])

        if not document_sync_rec:
            # return False, "Record not found"
            return False

        if not (document_sync_rec.tech_uid and document_sync_rec.tech_uid == tech_uid):
            document_sync_rec.message_post(body="""<div class="o_thread_message_content">
                                          <span>User unauthorized to delete this document : %s</span>
                                      </div>""" % (tech_uid))
            # return False, "User unauthorized to delete this document"
            return False

        document_id = document_sync_rec.attachment_id

        if document_id:
            document_id.sudo().unlink()
            document_sync_rec.sudo().unlink()
            # return True, "Ok"
            return True
        else:
            # return False, "document already deleted"
            return False
