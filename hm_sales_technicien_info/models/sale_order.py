# -*- encoding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, timedelta
from werkzeug.urls import url_encode
import pytz
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the Earth (Haversine formula)."""
    # Earth radius in km
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # Distance in km
    return R * c

class sale_order(models.Model):
    _inherit = "sale.order"

    def default_zip_code(self):
        zip_obj = self.env['zip.code']
        if self.property_id and self.property_id.zip:
            zip_id = zip_obj.search([('zip', '=', self.property_id.zip)])
            return zip_id

    def default_techniciens_domain(self):
        return [
            ('partner_id.hm_technician_availability_id', '!=', self.env.ref('hm_base_setup.currently_unavailable').id)]

    work_type = fields.Many2one('hm.work.type', string='Work type')
    search_work_type = fields.Many2one('hm.work.type', string='Find Work type', copy=True)
    search_zip_code = fields.Many2one('zip.code', string='Code postale', default=default_zip_code, copy=True)
    agremeent_ids = fields.Many2many('hm.agreement', 'hm_agreement_sale_order_rel', 'sale_order_id', 'hm_agreement_id',
                                     string='Agremeents')
    search_agremeent_ids = fields.Many2many('hm.agreement.region', string='Agreements')
    tech_choice_ids = fields.One2many('techniciens.choice', 'sale_order_id', string='Technicians Selected',
                                      compute="_compute_tech_choice_ids", domain=default_techniciens_domain)
    selected_tech_choice_ids = fields.Char(string='Selected Technicians')
    # TODO: clean name => technician_id
    technicien = fields.Many2one('res.partner', string='Technicians')
    customer_availability_id = fields.Many2one('hm.customer.availability', string='Disponibilités du client',
                                               copy=False)

    proposal_lines = fields.One2many('hm.technician.intervention.proposal', 'sale_order_id',
                                     string='Intervention proposal to the technician')
    send_proposals = fields.Selection(
        selection=[
            ('one_shot', 'One-shot'),
            ('in_batches', 'In batches'),
        ],
        string='Send proposals',
        default='one_shot',
    )
    batch_size = fields.Selection(
        selection=[
            ('1', '1 technician at a time'),
            ('2', '2 technicians at a time'),
            ('3', '3 technicians at a time'),
        ], string='Suggest the intervention to', default='1')
    frequency_proposals = fields.Selection(
        selection=[
            ('10_min', 'Every 10 minutes'),
            ('30_min', 'Every 30 minutes'),
            ('60_min', 'Every hour'),
            ('240_min', 'Every 4 hours'),
            ('1440_min', 'Every 24 hours'),
        ],
        string='Frequency of proposals',
        default='60_min',
    )
    last_proposal_sent = fields.Datetime()
    notify_so_manager_byproposals = fields.Boolean(
        default=False,
        string="Is SO Manager Notified By Proposals",
        help="Technical field used to define if the sales order manager is notified when all proposals are sent."
    )

    @api.onchange('sale_order_template_id')
    def _update_work_type_and_object_from_template(self):
        if self.sale_order_template_id.work_type:
            self.work_type = self.with_context(lang=self.partner_id.lang).sale_order_template_id.work_type
        else:
            self.work_type = False
            
        if self.sale_order_template_id.hm_work_object:
            self.hm_work_object = self.with_context(lang=self.partner_id.lang).sale_order_template_id.hm_work_object

        elif self.sale_order_template_id.work_type and self.sale_order_template_id.work_type.name:
            self.hm_work_object = self.with_context(lang=self.partner_id.lang).sale_order_template_id.work_type.name
        else:
            self.hm_work_object = False

    @api.onchange('order_line', 'sale_order_option_ids')
    def on_change_product_template_id(self):
        order_line_ids = self.order_line.filtered(lambda x: x.product_id.agreement_id and x.product_uom_qty > 0)
        agreement_ids = []
        for line in order_line_ids:
            agreement_ids.append(line.product_id.agreement_id.id)
        self.agremeent_ids = [(6, 0, list(agreement_ids))]
        if not order_line_ids:
            self.agremeent_ids = False

    def default_domain_for_partner_id(self, sale_id):
        domain = []
        search_domain = []
        order = self.env['sale.order'].search([('id', '=', sale_id)], limit=1)
        if order:
            zip = order.property_id and order.property_id.zip or False
            work_type_id = order.work_type.ids
            if work_type_id:
                search_domain += [('work_type_ids', 'in', work_type_id)]
            agremeent_ids = order.agremeent_ids
            agreemets = self.env['hm.agreement.region'].search([('agreement_id', 'in', agremeent_ids.ids)])
            list_partner = []
            for partner in agreemets:
                list_partner.append(partner.partner_id.id)
            if list_partner:
                search_domain += [('id', 'in', list_partner)]
            partner_ids = self.env['res.partner'].search(search_domain)
            listchild = []
            for child_id in partner_ids:
                for child_id_zip_code in child_id.zip_code:
                    if child_id_zip_code.zip == zip:
                        listchild.append(child_id.id)
            domain = [('partner_id', 'in', listchild)]
        return domain

    def techniciens_choice(self):
        # domain = self.default_domain_for_partner_id(self.id)
        domain = [('sale_order_id', '=', self.id)]
        return {
            'name': 'Techniciens',
            'domain': domain,
            'res_model': 'techniciens.choice',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'list',
            'view_type': 'tree',
            'target': 'current',
        }

    def action_import_tech(self):
        tech_choice_obj = self.env['techniciens.choice']
        if not self.ids:
            raise UserError(_("Merci de sélectionner aux moins une ligne !"))
        else:
            for technicien in self.ids:
                technicien_id = tech_choice_obj.browse(technicien)
                sale_order_id = technicien_id.sale_order_id
                # technicien_id.is_selected = True
                tech_choice_obj.create({
                    'sale_id': sale_order_id.id,
                    'partner_id': technicien_id.partner_id.id,
                    'work_type_ids_tech': [(6, 0, technicien_id.work_type_ids_tech.ids)],
                    'agremeent_ids_tech': [(6, 0, technicien_id.agremeent_ids_tech.ids)],
                })

    # add_tech_selection_ids list ids for selected_tech_choice_ids
    @api.model
    def add_tech_selection_ids(self):
        if self.env.context.get('tech_selection_ids') and self.env.context.get('href'):
            sale_id = False
            href = self.env.context.get('href')
            href_list = href.split('id=')
            if len(href_list) > 2:
                href_val = href_list[1].split('&')
                if len(href_val) > 0:
                    sale_id = href_val[0]
                else:
                    sale_id = href_list[1]
                if sale_id:
                    sale_id = self.env['sale.order'].search([('id', '=', int(sale_id))])
                    if sale_id:
                        sale_id.selected_tech_choice_ids = self.env.context.get('tech_selection_ids')

    @api.onchange('work_type')
    def onchange_work_type_params(self):
        if self.work_type:
            self.search_work_type = self.work_type.id

    @api.onchange('agremeent_ids')
    def onchange_agremeent_ids_params(self):
        res = [(6, 0, [])]
        if self.agremeent_ids:
            zip_id = self.env['zip.code'].search([('zip', '=', self.property_id.zip)], limit=1)
            agremeent_reg_ids = self.env['hm.agreement.region'].search(
                ['&', ('agreement_id', 'in', self.agremeent_ids.ids), '|',
                 ('region', '=', zip_id.state_id.region.id),
                 ('region', '=', False)])
            res = [(6, 0, agremeent_reg_ids.ids)]
        self.search_agremeent_ids = res

    @api.onchange('property_id')
    def onchange_property_id_params(self):
        if self.property_id:
            zip_id = self.env['zip.code'].search([('zip', '=', self.property_id.zip)], limit=1)
            if zip_id.sous_commune:
                zip_id = self.env['zip.code'].search(
                    [('commune_principale', '=', zip_id.commune_principale), ('sous_commune', '=', False)], limit=1)
            self.search_zip_code = zip_id and zip_id.id or False

    def _is_technician_available(self, partner, today):
        start_date = partner.tech_unavailability_start_date
        end_date = partner.tech_unavailability_end_date

        if start_date and not end_date:
            # Case 1: Date start defined, end date not defined
            return start_date > today

        if not start_date and end_date:
            # Case 2: Start date not defined, end date defined
            return end_date < today

        if start_date and end_date:
            # Case 3: Both start and end dates defined
            if start_date > today:
                return True
            if end_date < today:
                return True
            if start_date <= today <= end_date:
                return False

        # Default case when neither start nor end date is defined
        return True

    @api.depends('search_agremeent_ids', 'search_work_type', 'search_zip_code', 'state2', 'state')
    def _compute_tech_choice_ids(self):
        for rec in self:
            rec.tech_choice_ids = [(6, 0, [])]

            if rec.state2 in ['report_sent', 'to_invoice', 'invoiced'] or rec.state == 'cancel':
                continue

            domain = [('show_technician_in_search', '=', True)]
            if rec.search_agremeent_ids:
                domain.append(('agremeent_reg_ids', 'in', rec.search_agremeent_ids.ids))
            if rec.search_work_type:
                domain.append(('work_type_ids', 'in', rec.search_work_type.ids))
            if rec.search_zip_code:
                domain.append(('zip_code', 'in', rec.search_zip_code.ids))

            partner_ids = self.env['res.partner'].search(domain)

            if partner_ids and rec.proposal_lines:
                existing_partners = rec.proposal_lines.mapped('partner_id').ids
                partner_ids = partner_ids.filtered(lambda p: p.id not in existing_partners)

            if rec.search_agremeent_ids:
                search_ids = set(rec.search_agremeent_ids.ids)
                partner_ids = partner_ids.filtered(
                    lambda p: search_ids.issubset(set(p.agremeent_reg_ids.ids))
                )

            partner_ids = partner_ids.filtered_domain([
                ('hm_status', 'ilike', '%Actif%'),
                ('hm_technician_availability_id', '!=', self.env.ref('hm_base_setup.currently_unavailable').id)
            ])

            today = date.today()
            available_technicians = partner_ids.filtered(lambda p: self._is_technician_available(p, today))

            # Get Property Location
            property_lat = rec.property_id.partner_id.partner_latitude
            property_lon = rec.property_id.partner_id.partner_longitude

            # Compute Distance for Each Technician
            technician_distances = []
            for tech in available_technicians:
                if tech.partner_latitude and tech.partner_longitude and property_lat and property_lon:
                    distance = haversine_distance(property_lat, property_lon, tech.partner_latitude,
                                                  tech.partner_longitude)
                else:
                    distance = float('inf')
                technician_distances.append((tech, distance))

            # Sort Technicians by Distance
            # Sort by proximity
            technician_distances.sort(key=lambda x: x[1])

            # Categorizing ⭐ and 🚀
            star_techs = [t[0] for t in technician_distances if '⭐' in t[0].name]
            rocket_techs = [t[0] for t in technician_distances if '🚀' in t[0].name and '⭐' not in t[0].name]
            other_techs = [t[0] for t in technician_distances if '⭐' not in t[0].name and '🚀' not in t[0].name]

            sorted_techs = star_techs + rocket_techs + other_techs

            tech_choice_liste = []
            tech_choice_obj = self.env['techniciens.choice']
            for partner in sorted_techs:
                tech_id = tech_choice_obj.search([('sale_order_id', '=', rec.id), ('partner_id', '=', partner.id)],
                                                 limit=1)
                if not tech_id:
                    tech_choice_vals = {
                        'sale_order_id': rec.id,
                        'partner_id': partner.id,
                        'work_type_ids_tech': [(6, 0, partner.work_type_ids.ids)],
                        'agremeent_ids_tech': [(6, 0, partner.agremeent_reg_ids.mapped('agreement_id').ids)],
                    }
                    tech_choice = tech_choice_obj.create(tech_choice_vals)
                else:
                    tech_choice = tech_id
                tech_choice_liste.append(tech_choice.id)

            rec.tech_choice_ids = [(6, 0, tech_choice_liste)]

    # **********************************************


    # TODO: old process for hm_imputed_technician_id
    def write(self, vals):
        res = super(sale_order, self).write(vals)
        proposal_obj = self.env['hm.technician.intervention.proposal']
        old_hm_imputed_technician_id = self.hm_imputed_technician_id
        old_commitment_date = self.commitment_date
        if (vals.get("hm_imputed_technician_id") and vals.get("commitment_date")) or (self.commitment_date and vals.get("hm_imputed_technician_id")) or (self.hm_imputed_technician_id and vals.get("commitment_date")) :
            self.state2  = 'planned'

            # Send notification to technician if the intervention date is already set and there is a new value
            if self.commitment_date and vals.get("commitment_date") and not vals.get("hm_imputed_technician_id"):
                proposal = self.proposal_lines.filtered(
                    lambda p: p.state == "accepted" and p.partner_id == self.hm_imputed_technician_id)
                if proposal:
                    proposal.run_proposal_notification(notification_type="updated")
                else:
                    proposal_obj.with_context(notif_from_so=True, so_id=self.id).run_proposal_notification(notification_type="updated")

            if vals.get("hm_imputed_technician_id") or (vals.get("hm_imputed_technician_id") and vals.get("commitment_date")):
                proposal_obj.with_context(notif_from_so=True, so_id=self.id).run_proposal_notification(notification_type="confirmed")
                if old_hm_imputed_technician_id and old_hm_imputed_technician_id.id != vals.get("hm_imputed_technician_id") and old_hm_imputed_technician_id.id not in self.proposal_lines.mapped('partner_id').ids:
                    proposal_obj.with_context(notif_from_so=True, so_id=self.id, hm_imputed_technician_id=old_hm_imputed_technician_id.id, commitment_date_when_intervention_canceled=old_commitment_date).run_proposal_notification(notification_type="intervention_canceled")

                for proposal in self.proposal_lines:
                    if proposal.partner_id.id == vals.get("hm_imputed_technician_id"):
                        proposal.state = 'accepted'
                        proposal.accepted_datetime = datetime.now()
                        proposal.accepted_by_id = self.env.user.id
                    elif proposal.state == "shortlisted":
                        proposal.with_context(force_skip_write=True).active = False
                    else:
                        proposal.with_context(commitment_date_when_intervention_canceled=old_commitment_date).action_cancel_proposal()

        self.proposal_lines.technician_availability_ids._compute_availability_color()
        if "sale_order_template_id" in vals:
            self.run_automated_technician_proposal_creation()
        return res


    @api.model_create_multi
    def create(self, vals):
        res = super(sale_order, self).create(vals)
        for values in vals:
            if 'sale_order_template_id' in values and not self.env.context.get('force_onchange_sale_order_template', False):
                res.onchange_template_for_proposals()
                res.run_automated_technician_proposal_creation()
        return res


    def action_cancel(self):
        result = super(sale_order, self).action_cancel()
        for proposal in self.proposal_lines:
            proposal.action_cancel_proposal()
        return result

    def action_send_proposals(self):
        if self.proposal_lines:
            res = self.proposal_lines[0].with_context(proposal_ids=self.proposal_lines.ids).check_so_manager()
            if res and type(res) == dict:
                return res
        for proposal in self.proposal_lines.filtered(lambda x: x.state == 'shortlisted'):
            proposal.with_context(force_send_proposal=True).send_proposal()

    def generate_url(self):
        model_name = "sale.order"
        url_params = {
            'id': self.id,
            'model': model_name,
            'view_type': 'form'
        }
        encoded_record_url = url_encode(url_params)
        record_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url') + '/web?#' + encoded_record_url
        return record_url

    def schedule_proposal_sending(self):
        # Search for sale orders in the 'to_organize' state and with 'in_batches' option for sending proposals
        so_ids = self.search([('state', '=', 'sale'), ('state2', '=', 'to_organize'), ('send_proposals', '=', 'in_batches')])
        time_now = datetime.now()

        # Define the start and end time for sending proposals
        brussels_tz = pytz.timezone('Europe/Brussels')
        time_now_with_tz = datetime.now(brussels_tz)

        start_time = datetime.now(brussels_tz).replace(hour=7, minute=0, second=0, microsecond=0)
        end_time = datetime.now(brussels_tz).replace(hour=21, minute=0, second=0, microsecond=0)
        if start_time <= time_now_with_tz <= end_time:

            # Define mapping of frequency options to time deltas
            frequency_options = {
                '10_min': timedelta(minutes=10),
                '30_min': timedelta(minutes=30),
                '60_min': timedelta(hours=1),
                '240_min': timedelta(hours=4),
                '1440_min': timedelta(days=1),
            }

            for so in so_ids:
                batch_size = int(so.batch_size)
                shortlisted_proposals = so.proposal_lines.filtered(lambda x: x.state == 'shortlisted')
                proposal_lines_to_send = shortlisted_proposals.sorted(key=lambda x: x.sequence)

                # Check if we have proposal to send
                if proposal_lines_to_send :

                    # Check if last frequency call exists
                    send_proposals = False

                    if so.last_proposal_sent:
                        proposals_tosend_by_frequency = time_now - so.last_proposal_sent

                        # Get time delta for selected frequency option
                        frequency_delta = frequency_options.get(so.frequency_proposals)

                        # Send proposals if enough time has elapsed since last frequency call
                        if frequency_delta and proposals_tosend_by_frequency >= frequency_delta:
                            send_proposals = True
                        else:
                            # When there are proposals marked as shortlisted but none are in the 'Sent' or 'Technician Interested' status,
                            # the next batch is sent immediately.
                            proposal_lines_sent = so.proposal_lines.filtered(lambda x: x.state == 'sent')
                            proposal_lines_interested = so.proposal_lines.filtered(lambda x: x.state == 'interested')
                            proposal_lines_shortlisted = so.proposal_lines.filtered(lambda x: x.state == 'shortlisted')

                            if proposal_lines_shortlisted and not proposal_lines_interested and not proposal_lines_sent:
                                send_proposals = True
                    else:
                        send_proposals = True

                    # check it's the time to send proposal based on SO frequency datas
                    if send_proposals:
                        num_proposals_to_send = min(batch_size, len(proposal_lines_to_send))
                        for proposal in proposal_lines_to_send[:num_proposals_to_send]:
                            proposal.with_context(force_send_proposal=True).send_proposal()

                    proposal_lines_shortlisted = so.proposal_lines.filtered(lambda x: x.state == 'shortlisted')
                    if so.proposal_lines and (not proposal_lines_shortlisted) and not so.notify_so_manager_byproposals:
                        record_url = so.generate_url()
                        message = f"Toutes les propositions ont été envoyées, souhaitez-vous en créer d'autres?, URL : <a href='{record_url}'>{record_url}</a>"
                        so.sudo().message_post(
                            partner_ids=[so.sudo().hm_so_manager_id.partner_id.id],
                            body=message,
                            author_id=self.env.ref('base.partner_root').id
                        )
                        so.notify_so_manager_byproposals = True

    def create_update_customer_availability(self):
        view_id = self.env.ref('hm_sales_technicien_info.customer_availability_view_form_wizard')
        customer_availability_id = self.customer_availability_id
        if not customer_availability_id:
            customer_availability_id = self.customer_availability_id.create({'sale_order_id': self.id})
            self.customer_availability_id = customer_availability_id.id
        return {
            'name': _('Customer availability'),
            'res_model': 'hm.customer.availability',
            'view_id': view_id.id,
            'type': 'ir.actions.act_window',
            'res_id': customer_availability_id.id or False,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.onchange('sale_order_template_id')
    def onchange_template_for_proposals(self):
        send_proposals = 'one_shot'
        batch_size = '1'
        frequency_proposals = '60_min'
        template_id = self.sale_order_template_id
        if template_id:
            send_proposals = template_id.send_proposals
            batch_size = template_id.batch_size
            frequency_proposals = template_id.frequency_proposals

        self.send_proposals = send_proposals
        self.batch_size = batch_size
        self.frequency_proposals = frequency_proposals

    def run_automated_technician_proposal_creation(self):
        """
        Automatically creates proposals for technicians based on template settings.
        Computes eligible technicians and creates proposals for up to 10 candidates.
        """
        for record in self:
            if record.sale_order_template_id.automate_proposals_creation:
                record._compute_tech_choice_ids()
                for technician in record.tech_choice_ids[:10]:
                    technician.action_add_technician()
