# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
import logging
from bs4 import BeautifulSoup
import base64
import requests
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


class HmIcr(models.Model):
    _name = 'hm.icr'
    _description = "Hm Icr"

    name = fields.Char(compute='_compute_name')
    sequence = fields.Integer()
    body_text = fields.Text(string="Request", copy=True)
    hm_related_lead_id = fields.Many2one('crm.lead', string="Lead liee", copy=True)
    picture_lib_ids = fields.Many2many('hm.picture.library', 'hm_icr_id', string="Extra Media", copy=True)
    picture_icr_info_ids = fields.One2many('hm.picture.icr.info', 'icr_id', string="Info", copy=True)
    active = fields.Boolean(default=True)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='Sale Order Count')
    search_pictures_ids = fields.Many2many(
        comodel_name='hm.picture.library',
        relation='hm_icr_hm_picture_library_search_rel',
        column1='icr_id',
        column2='picture_id',
        compute='_compute_search_pictures_ids',
        string='Technical fields for searched pictures'
    )

    # lead_description = fields.Html(string='Lead description', related='hm_related_lead_id.hm_html_description', copy=True)

    @api.depends('hm_related_lead_id')
    def _compute_search_pictures_ids(self):
        picture_lib_obj = self.env['hm.picture.library']
        sale_obj = self.env['sale.order']

        for icr in self:
            sale_order_ids = sale_obj.search([('opportunity_id', '=', icr.hm_related_lead_id.id)]).ids
            search_pictures1_ids = picture_lib_obj.search([
                ('sale_order_ids', 'in', sale_order_ids),
                ('is_client_signature', '=', False)

            ]).ids
            search_pictures2_ids = picture_lib_obj.search([
                ('lead_ids', 'in', icr.hm_related_lead_id.ids),
                ('is_client_signature', '=', False)
            ]).ids
            icr.search_pictures_ids = [(6, 0, search_pictures1_ids + search_pictures2_ids)]


    def _compute_sale_order_count(self):
        sale_obj = self.env['sale.order']
        for icr in self:
            sale_order_ids = sale_obj.search([('icr_id', '=', icr.id)])
            sale_order_count = len(sale_order_ids)
            icr.sale_order_count = sale_order_count

    def _compute_name(self):
        for rec in self:
            if rec.hm_related_lead_id:
                rec.name = 'ICR' + '/' + str(rec.hm_related_lead_id.id) + '-' + str(rec.sequence)
            else:
                rec.name = '/'

    @api.model
    def default_get(self, fields):
        res = super(HmIcr, self).default_get(fields)
        if res.get('hm_related_lead_id', False):
            picture_ids = self.env['hm.picture.library'].search([('lead_ids', 'in', res['hm_related_lead_id'])])
            if picture_ids:
                res.update({'picture_lib_ids': [(6, 0, picture_ids.ids)]})
        return res

    @api.model_create_multi
    def create(self, vals):
        sequence = 1
        picture_lib_ids = []
        for values in vals:
            if values.get('hm_related_lead_id', False):
                icr_ids = self.search(
                    [('hm_related_lead_id', '=', values['hm_related_lead_id']), ('active', 'in', (True, False))])
                sequence = (len(icr_ids) + 1) or 1
            values['sequence'] = sequence
        res = super(HmIcr, self).create(vals)
        return res

    def action_view_sale_order(self):
        opportunity = self.hm_related_lead_id
        sale_obj = self.env['sale.order']
        action = self.env.ref('sale.action_orders').read()[0]
        action['context'] = {
            'default_partner_id': opportunity.partner_id.id,
            'default_opportunity_id': opportunity.id,
        }
        action['domain'] = [('icr_id', '=', self.id)]
        orders = sale_obj.search([('icr_id', '=', self.id)])
        if len(orders) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = orders.id
        return action

    def action_new_quotation(self):
        action = self.env.ref("sale_crm.sale_action_quotations_new").read()[0]

        opportunity = self.hm_related_lead_id

        action['context'] = {
            'search_default_opportunity_id': opportunity.id,
            'default_opportunity_id': opportunity.id,
            'default_opportunity_id': opportunity.id,
            'search_default_partner_id': opportunity.partner_id.id,
            'default_partner_id': opportunity.partner_id.id,
            'default_campaign_id': opportunity.campaign_id.id,
            'default_medium_id': opportunity.medium_id.id,
            'default_origin': opportunity.name,
            'default_source_id': opportunity.source_id.id,
            'default_company_id': opportunity.company_id.id or self.env.company.id,
            'default_tag_ids': opportunity.tag_ids.ids,
            'default_property_id': opportunity.property_id and opportunity.property_id.id or False,
            'default_icr_id': self.id or False,
        }
        if opportunity.user_id:
            action['context']['default_user_id'] = opportunity.user_id.id
        return action

    @api.onchange('picture_lib_ids')
    def _onchange_picture(self):
        info_ids = []
        for picture in self.picture_lib_ids:
            if self.hm_related_lead_id.id not in picture.lead_ids.ids:
                picture._origin.write({"lead_ids": [(4, self.hm_related_lead_id and self.hm_related_lead_id.id)]})
            picture_info = picture.mapped('library_pic_lead_info_ids').filtered(
                lambda x: x.hm_lead_id == self.hm_related_lead_id)
            picture_id = self.picture_icr_info_ids.filtered(
                lambda x: x.hm_picture_library_id == picture_info.hm_picture_library_id)
            if not picture_id:
                info_ids.append((0, 0, {
                    'name': picture_info.name or picture.name,
                    'caption': picture_info.caption,
                    'hm_picture_library_id': picture._origin.id,
                    'hm_lead_id': self.hm_related_lead_id.id,
                }))

        for picture_info in self.picture_icr_info_ids:
            picture_info_ids = self.picture_lib_ids.mapped('library_pic_lead_info_ids').filtered(
                lambda x: x.hm_lead_id == self.hm_related_lead_id)
            if picture_info.hm_picture_library_id.id not in picture_info_ids.mapped('hm_picture_library_id').ids:
                info_ids.append((3, picture_info.id))

        self.picture_icr_info_ids = info_ids

    @api.onchange('picture_icr_info_ids')
    def _onchange_picture_icr_info_ids(self):
        if self.picture_icr_info_ids:
            self.picture_lib_ids = [(6, 0, self.picture_icr_info_ids.mapped('hm_picture_library_id').ids)]

    def copy_lead_description(self):
        if self.hm_related_lead_id.hm_html_description:
            hm_html_description = html2plaintext(self.hm_related_lead_id.hm_html_description).strip().replace('*', '')
            body_text = hm_html_description
            if self.body_text:
                body_text = self.body_text + '\n' + hm_html_description
            self.body_text = body_text
