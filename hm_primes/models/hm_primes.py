# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.osv import expression
from lxml import etree


class HmPrimes(models.Model):
    _name = "hm.primes"
    _description = "Primes"

    active = fields.Boolean('Active', default=True)
    hm_region = fields.Many2one("region.code", string="Region", copy=True, store=True, index=False, ondelete="set null")
    hm_region_name = fields.Char(string="HM region",compute='_compute_region_name', copy=True, store=True, index=False, translate=False)
    name = fields.Char(string="Name", copy=True, store=True, index=False, translate=False)
    hm_conditions_prime = fields.Html(string="Conditions prime", copy=True, store=True, index=False, translate=False)
    hm_description_of_the_premium_for_the_customer = fields.Text(string="Descriptif de la prime pour le client",
                                                                 copy=True, store=True, index=False, translate=False)
    hm_document_to_be_completed_by_hm = fields.Binary(string="Document à compléter par Heat Me", copy=True, store=True,
                                                      index=False)
    hm_document_to_be_completed_by_hm_filename = fields.Char(string="Nom du document à compléter par Heat Me", copy=True,
                                                             store=True, index=False, translate=False)
    hm_document_to_be_completed_by_the_customer = fields.Binary(string="Document à compléter par le client", copy=True,
                                                                store=True, index=False)
    hm_document_to_be_completed_by_the_customer_filename = fields.Char(string="Nom du document à compléter par le client",
        copy=True, store=True, index=False, translate=False)
    hm_web_link_infos = fields.Char(string="Lien web infos", copy=True, store=True, index=False, translate=False)
    hm_basic_amount_of_the_premium = fields.Float(string="Prime unitaire", copy=True, store=True, index=False)
    hm_procedure_text_to_send_to_the_customer = fields.Text(string="Texte procédure à envoyer au client", copy=True,
                                                            store=True, index=False, translate=False)
    hm_currency_id = fields.Many2one("res.currency", string="Currency", store=True, copy=True, index=False,
                                     ondelete="set null")
    hm_qty_premium = fields.Float(string='Quantity', default=1.0, copy=True)

    hm_premium_total = fields.Monetary(compute='_compute_hm_premium_total', string='Total', readonly=True, store=True,
                                       currency_field='hm_currency_id')

    @api.depends('hm_qty_premium', 'hm_basic_amount_of_the_premium')
    def _compute_hm_premium_total(self):
        for line in self:
            line.hm_premium_total = line.hm_qty_premium * line.hm_basic_amount_of_the_premium

    # to display in Tree default_order
    def _compute_region_name(self):
        for line in self:
            line.hm_region_name = line.hm_region.name

    # TODO: clean me
    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HmPrimes, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        view_id = self.env.ref('hm_primes.hm_primes_view_search').id
        doc = etree.XML(res['arch'])
        if view_id and view_type == 'search':
            for node in doc.xpath("//filter[@name='state']"):
                if self._context.get('default_hm_region'):
                    state = self.env['region.code'].browse(self._context['default_hm_region'])
                    context = dict(self._context)
                    del context['search_default_state']
                    self = self.with_context(context)
                    state_filter = "['|', ('hm_region', '=', " + str(
                        context.get('default_hm_region')) + "), ('hm_region', '=', False)]"
                    node.set('domain', state_filter)
                    node.set('string', "Région est égal à " + state.display_name + " ou Région n’est pas défini")
                else:
                    return res
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name=_("%s (copy)") % (self.name))
        return super(HmPrimes, self).copy(default)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        prime_ids = []
        if self._context.get('state_property') and self._context.get('default_hm_region'):
            if not name:
                domain = ['|', ('hm_region', '=', self._context.get('default_hm_region')), ('hm_region', '=', False)]
                prime_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
            else:
                domain = ['&', '|', ('hm_region', '=', self._context.get('default_hm_region')), ('hm_region', '=', False), ('name', operator, name)]
                prime_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return prime_ids
