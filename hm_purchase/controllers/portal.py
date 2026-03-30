# -*- coding: utf-8 -*-

import base64
try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO
from collections import OrderedDict
from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.web.controllers.main import Binary
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools import image_process


def get_records_pager_my_purchase_orders(ids, current):
    path = request.httprequest.path
    res = {}

    if current.id in ids and (hasattr(current, 'website_url') or hasattr(current, 'access_url')):
        attr_name = 'access_url' if hasattr(current, 'access_url') else 'website_url'
        idx = ids.index(current.id)
        res = {
            'prev_record': idx != 0 and getattr(current.browse(ids[idx - 1]), attr_name),
            'next_record': idx < len(ids) - 1 and getattr(current.browse(ids[idx + 1]), attr_name),
        }

    if '/my/purchase_orders/' in path:
        res['prev_record'] = idx != 0 and str(res['prev_record']).replace('/my/purchase', '/my/purchase_orders')
        res['next_record'] = idx < len(ids) - 1 and str(res['next_record']).replace('/my/purchase', '/my/purchase_orders')

    return res


class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        PurchaseOrder = request.env['purchase.order']
        if 'rfq_count' in counters:
            values['rfq_count'] = PurchaseOrder.search_count([
                ('state', 'in', ['sent'])
            ]) if PurchaseOrder.check_access_rights('read', raise_exception=False) else 0
        if 'purchase_count' in counters:
            values['purchase_count'] = PurchaseOrder.search_count([
                ('state', 'in', ['purchase', 'done', 'cancel'])
            ]) if PurchaseOrder.check_access_rights('read', raise_exception=False) else 0
        return values

    def _prepare_home_portal_values(self):
        values = super(CustomerPortal, self)._prepare_home_portal_values()
        partner = request.env.user.partner_id
        purchase_order_count = request.env['purchase.order'].search_count(
            [('partner_id', '=', partner.id), ("po_type", "in", ("po_technicien", "po_emport_marchandise")),
            ('stage2_id', 'in', (request.env.ref('hm_purchase.purchase_stage2_po_technicien').id, request.env.ref('hm_purchase.purchase_stage2_po_emport_marchandise').id)),
             ('state', '=', 'purchase'),
             ('hm_po_deleted_from_portal', '=', False)]) if request.env['purchase.order'].check_access_rights('read', raise_exception=False) else 0
        values['purchase_order_count'] = purchase_order_count

        # Quotations and Sales Orders

        SaleOrder = request.env['sale.order']
        quotation_count = SaleOrder.search_count([
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['sent', 'cancel']),
            ('hm_imputed_technician_id', '!=', partner.id)
        ]) if SaleOrder.check_access_rights('read', raise_exception=False) else 0
        order_count = SaleOrder.search_count([
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['sale', 'done']),
            ('hm_imputed_technician_id', '!=', partner.id)
        ]) if SaleOrder.check_access_rights('read', raise_exception=False) else 0

        values.update({
            'quotation_count': quotation_count,
            'order_count': order_count,
        })

        return values

    def _purchase_orders_get_page_view_values(self, purchase_order_technicien, access_token, **kwargs):

        def resize_to_48(source):
            if not source:
                source = request.env['ir.binary']._placeholder()
            else:
                source = base64.b64decode(source)
            return base64.b64encode(image_process(source, size=(48, 48)))

        values = {
            'page_name': 'purchase_order_technicien',
            'purchase_order_technicien': purchase_order_technicien,
            'resize_to_48': resize_to_48,
        }
        return self._get_page_view_values(purchase_order_technicien, access_token, values, 'my_purchase_orders_history', True, **kwargs)

    @http.route(['/my/purchase', '/my/purchase/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_purchase_orders_technicien(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):

        values = self._prepare_portal_layout_values()
        user = request.env.user
        partner = user.partner_id

        PurchaseOrder = request.env['purchase.order']

        domain = [('partner_id', '=', partner.id),
                  ("po_type", "in", ("po_technicien", "po_emport_marchandise")),
                  ('stage2_id', 'in', (request.env.ref('hm_purchase.purchase_stage2_po_technicien').id,
                                       request.env.ref('hm_purchase.purchase_stage2_po_emport_marchandise').id)),
                  ('state', '=', 'purchase'),
                  ('amount_untaxed', '!=', 0),
                  ('hm_po_deleted_from_portal', '=', False)]

        searchbar_sortings = {
            'date': {'label': _('Le plus récent'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Nom'), 'order': 'name asc, id asc'},
            'amount_total': {'label': _('Total'), 'order': 'amount_total desc, id desc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('purchase.order', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_filters = {
            'facturable': {'label': _('Facturable'), 'domain': [('invoice_status', '=', 'to invoice')]},
            'facture': {'label': _('Facturé'), 'domain': [('invoice_status', '=', 'invoiced')]},
            'tous': {'label': _('Tous'), 'domain': [('invoice_status', '!=', 'no')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'facturable'

        domain += searchbar_filters[filterby]['domain']

        # count for pager
        purchase_order_count = PurchaseOrder.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/purchase",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=purchase_order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        purchase_orders = PurchaseOrder.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_purchase_orders_history'] = purchase_orders.ids[:100]

        values.update({
            'date': date_begin,
            'purchase_orders': purchase_orders.sudo(),
            'page_name': 'purchase_order_technicien',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/purchase',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })

        return request.render("hm_purchase.portal_my_purchase_orders_technicien", values)

    @http.route(['/my/purchase/<int:purchase_order_id>'], type='http', auth="public", website=True)
    def portal_purchase_order_page(self, purchase_order_id, access_token=None, **kw):
        user = request.env.user
        technicien_po = request.env['purchase.order'].sudo().search([('partner_id', '=', user.partner_id.id),
                                                                     ("po_type", "in", ("po_technicien", "po_emport_marchandise")),
                                                                     ('stage2_id', 'in', (request.env.ref('hm_purchase.purchase_stage2_po_technicien').id, request.env.ref('hm_purchase.purchase_stage2_po_emport_marchandise').id)),
                                                                     ('state', '=', 'purchase'),
                                                                     ('hm_po_deleted_from_portal', '=', False)
                                                                     ])
        purchase_order_technicien = request.env['purchase.order'].sudo().browse(purchase_order_id)

        try:
            purchase_order_sudo = self._document_check_access('purchase.order', purchase_order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._purchase_orders_get_page_view_values(purchase_order_sudo, access_token, **kw)
        if purchase_order_sudo.company_id:
            values['res_company'] = purchase_order_sudo.company_id

        if purchase_order_technicien.id not in technicien_po.ids:
            return request.redirect('/my')
        else:
            history = request.session.get('my_purchase_orders_history', [])
            values.update(get_records_pager_my_purchase_orders(history, purchase_order_sudo))
            return request.render("hm_purchase.portal_purchase_order_page", values)

    @http.route(['/my/purchase/generate_pdf/<int:purchase_order_id>'], type='http', auth="public", website=True)
    def generate_pdf(self, purchase_order_id=None, access_token=None, **kw):
        user = request.env.user
        technicien_po = request.env['purchase.order'].sudo().search([('partner_id', '=', user.partner_id.id),
                                                                     ("po_type", "in", ("po_technicien", "po_emport_marchandise")),
                                                                     ('stage2_id', 'in', (request.env.ref('hm_purchase.purchase_stage2_po_technicien').id, request.env.ref('hm_purchase.purchase_stage2_po_emport_marchandise').id)),
                                                                     ('state', 'in', ['purchase']),
                                                                     ('hm_po_deleted_from_portal', '=', False)
                                                                     ])

        if purchase_order_id not in technicien_po.ids:
            return request.redirect('/my')
        else:
            pdf = request.env.ref('purchase.action_report_purchase_order').sudo().render_qweb_pdf([purchase_order_id])[0]
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf)),
            ]
            return request.make_response(pdf, headers=pdfhttpheaders)
