# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # todo: clean name => is_technician
    hm_technician = fields.Boolean(string="Technician")
    hm_surnom_heat_me = fields.Char(string="Surnom Heat Me", store=True, index=False, copy=False, translate=False)
    hm_start_activity = fields.Date(string="Début d'activité", copy=False, index=False, store=True)
    hm_work_at_2 = fields.Boolean(string="Travaille à 2", store=True, index=False, copy=False)
    hm_know_how_to_find_a_colleague = fields.Boolean(string="Sais trouver un collègue", store=True, index=False,
                                                     copy=False)
    hm_assurance_policy = fields.Binary(string="Police assurance", store=True, index=False, copy=False)
    hm_connected_testo = fields.Boolean(string="Testo connecté", store=True, index=False, copy=False)
    hm_to_an_intern = fields.Boolean(string="A un stagiaire", copy=False, store=True, index=False)

    hm_remarks = fields.Text(string="Remarques", store=True, copy=False, index=False, translate=False)

    hm_currently_unavailable = fields.Boolean(string="Actuellement indisponible", copy=False, store=True,
                                              index=False)
    hm_assurance_rc = fields.Selection([("Pas assuré", "Pas assuré"), ("Assuré, pas reçu", "Assuré,pas reçu"),
                                        ("Assuré, reçu police", "Assuré, reçu police")], string="Assurance RC",
                                       copy=False, store=True, index=False)
    hm_carte_facq = fields.Selection(
        selection=[("Pas fait", "Pas fait"), ("Demandé carte", "Demandé carte"), ("Carte opérationnelle", "Carte opérationnelle"),
         ("Carte bloquée", "Carte bloquée")], string="Carte Facq", copy=False, store=True, index=False)
    hm_carte_vam = fields.Selection(
        selection=[("Pas fait", "Pas fait"), ("Demandé carte", "Demandé carte"), ("Carté opérationnelle", "Carté opérationnelle"),
         ("Carte bloquée", "Carte bloquée")], string="Carte VAM", copy=False, store=True, index=False)
    hm_commercial_delegate_id = fields.Many2one(comodel_name="res.partner", string="Délégué commercial", ondelete="set null",
                                                copy=False, store=True, index=False)
    hm_technician_availability_id = fields.Many2one(comodel_name="technician.availability", string="Disponibilité technicien",  copy=False, store=True, index=False)
    hm_manager_mail = fields.Char(string="HM Email Manager",
                                  related="hm_property_manager_id.email", copy=False, store=True,
                                  translate=False, index=False)
    hm_property_manager_mail = fields.Char(string="Email Manager", copy=False,
                                           related="hm_property_manager_id.email", translate=False,
                                           store=True, index=False)
    hm_technician_colleague_ids = fields.Many2many(comodel_name="res.partner", relation="x_res_partner_res_partner_rel", column1="id1", column2="id2",
                                                   string="Collègue technicien", copy=False, store=True, index=False)
    hm_2sYmL_file_name = fields.Char(string="Nom du fichier pour x_studio_field_2sYmL", copy=False,
                                     index=False, store=True, translate=False)
    hm_privileged_boiler_brand = fields.Many2many(comodel_name="hm.marque.chaudiere", relation="x_res_partner_x_marque_chaudiere_rel",
                                                  column1="res_partner_id", column2="x_marque_chaudiere_id",
                                                  string="Marque chaudière privilégiée", copy=False, index=False,
                                                  store=True)
    hm_boiler_registration_with_manufacturer = fields.Date(string="Enregistrement chaudière chez fabricant (garantie)",
                                                           copy=False,
                                                           store=True, index=False)
    hm_boiler_brand_ids = fields.Many2many(comodel_name="hm.marque.chaudiere", relation="x_res_partner_x_marque_chaudiere_rel",
                                           column1="res_partner_id", column2="x_marque_chaudiere_id", copy=False,
                                           string="Marque chaudière", store=True, index=False)
    hm_parent_phone = fields.Char(string="New Champ lié phone", related="parent_id.phone", copy=False, store=True,
                                  translate=False, index=False)
    hm_contact_id = fields.Many2one(comodel_name="res.partner", ondelete="set null", copy=False, store=True, string="HM Contact",
                                    index=False)
    hm_HMUpT_file_name = fields.Char(string="Nom du fichier pour x_studio_field_HMUpT", copy=False,
                                     store=True, translate=False, index=False)
    hm_availablity = fields.Selection(selection=[("Soir", "Soir"), ("Samedi", "Samedi"), ("Dimanche", "Dimanche")],
                                      string="Availability", copy=False, store=True, index=False)
    hm_mastered_boiler_brand = fields.Many2many(comodel_name="hm.marque.chaudiere", relation="x_res_partner_x_marque_chaudiere_rel",
                                                column1="res_partner_id", column2="x_marque_chaudiere_id",
                                                string="Marque chaudière maitrisée", copy=False, store=True,
                                                index=False)
    hm_languages = fields.Many2many(comodel_name="res.lang", relation="x_res_lang_res_partner_rel", column1="res_partner_id", column2="res_lang_id",
                                    string="Languages", copy=False, store=True, index=False)
    hm_hHnMQ_file_name = fields.Char(string="Nom du fichier pour x_studio_field_hHnMQ", copy=False,
                                     store=True, index=False, translate=False)
    hm_privileged_technics_store_ids = fields.Many2many(comodel_name="res.partner", relation="x_res_partner_res_partner_rel", column1="id1", column2="id2",
                                                        string="Magasin Technics privilegié many", copy=False,
                                                        index=False,
                                                        store=True)
    hm_spoken_language_ids = fields.Many2many(comodel_name="hm.spoken.language", relation="x_res_partner_x_langue_parle_rel",
                                              column1="res_partner_id",
                                              column2="x_langue_parle_id", string="Langue parlée", copy=False, store=True,
                                              index=False)
    hm_access_to_the_profession_ids = fields.Many2many(comodel_name="hm.access.profession", relation="res_partner_hm_access_profession_rel",
                                                       column1="res_partner_id",
                                                       column2="hm_access_profession_id", string="Access to the profession", copy=False,
                                                       index=False,
                                                       store=True)
    hm_property_manager_id = fields.Many2one(comodel_name="res.partner", string="HM Manager", ondelete="set null",
                                             copy=False, store=True, index=False)
    hm_info_next_maintenance = fields.Text(string="Infos prochain entretien", copy=False, store=True,
                                           translate=False, index=False)
    hm_privileged_sanicenter_store_facq = fields.Many2one(comodel_name="res.partner",
                                                          string="Magasin SaniCenter privilégié Facq",
                                                          ondelete="set null", copy=False, store=True,
                                                          index=False)
    hm_vam_privileged_technics_store = fields.Many2one(comodel_name="res.partner", string="Magasin Technics privilégié VAM",
                                                       copy=False, index=False, store=True, ondelete="set null")
    hm_do_not_send_reminder_before_intervention = fields.Boolean(
        string="Ne pas envoyer de rappel avant intervention", copy=False, store=True, index=False)
    hm_do_not_ask_customer_opinions = fields.Boolean(string="Ne plus demander avis client", copy=False,
                                                     store=True, index=False)
    hm_assurance_policy_file_name = fields.Char(string="Nom du fichier pour hm_assurance_policy", store=True,
                                                translate=False, copy=False, index=False)
    hm_heating_curve_adjustment = fields.Float(string="Réglage coube de chauffe", store=True, index=False,
                                               copy=False, tracking=True)
    hm_customer_source_id = fields.Many2one(comodel_name="customer.source", ondelete="set null", store=True, index=False, copy=True, string="Source client")
    hm_mobile_payment_terminal = fields.Boolean(string="Terminal paiement mobile", store=True, copy=False,
                                                index=False)
    hm_third_party_payer_id = fields.Many2one(comodel_name="res.partner", string="Tiers payeur", store=True, index=False, copy=False,
                                              ondelete="set null")

    hm_check_profession_access = fields.Boolean(string="Vérifié accès profession", store=True, index=False, copy=False)

    hm_status = fields.Selection(
        selection=[('actif_app', 'Actif - App'),
                   ('Actif', "Actif - N'utilise pas l'application"),
                   ('Entreprise autonome (Vincotte,..)', 'Entreprise autonome (Vincotte,..)'),
                   ('Intéressé', 'Inactif - Activation en attente'),
                   ('A relancer prochainement', 'Inactif - A réactiver prochainement'),
                   ('Recallé', "Inactif - Heat Me a décidé d'ârreter"),
                   ("A décidé d'arrêter", "Inactif - Le technicien a décidé d'arrêter"),
         ], string="HM Status", copy=False, store=True, index=False)

    tech_unavailability_start_date = fields.Date(string="Date début indisponibilité")
    tech_unavailability_end_date = fields.Date(string="Date fin indisponibilité")

    is_print_partner = fields.Boolean(string='Imprimer', default=False)
    is_letter = fields.Boolean(string='Envoyé par la poste', default=False)
    is_email_partner = fields.Boolean(string='IS EMAIL PARTNER', default=True)

    from_property = fields.Boolean(string="Adresse des Biens", default=False)
    numero_carte_facq = fields.Text(string='Numéro carte Facq')
    numero_carte_vam = fields.Text(string='Numéro carte VAM')
    active = fields.Boolean(default=True, tracking=True)
    zip_code = fields.Many2many(
        'zip.code',
        'zip_code_res_partner_rel',
        'res_partner_id',
        'zip_code_id',
        string="zones d'intervention",
    )
    show_technician_in_search = fields.Boolean(
        string="Afficher le technicien dans la liste 'Rechercher des techniciens'",
        default=True,
        help="Si cette case est cochée, le technicien sera visible dans la liste 'Rechercher des techniciens' lors de l'organisation d'une intervention."
    )

    @api.constrains('tech_unavailability_start_date', 'tech_unavailability_end_date')
    def _check_unavailability_dates(self):
        for record in self:
            if record.tech_unavailability_end_date and record.tech_unavailability_start_date:
                if record.tech_unavailability_end_date < record.tech_unavailability_start_date:
                    raise ValidationError("Date fin indisponibilité ne peut pas être antérieure à Date début indisponibilité.")

    @api.constrains('type')
    def check_second_billing_address(self):
        for rec in self:
            if rec.parent_id and len(rec.parent_id.child_ids.filtered(lambda c: c.type == 'invoice')) > 1:
                raise UserError(_("This Company %r already have billing address") %(rec.parent_id.name))

    @api.onchange('zip', 'country_id')
    def onchange_zip_code(self):
        if self.zip and self.country_id:
            res_country_id = self.env['res.country'].search([('code', '=', self.country_id.code)], limit=1)
            if res_country_id:
                zip_code_id = self.env['zip.code'].search(
                    [('zip', '=', self.zip), ('code_pays', '=', res_country_id.id)], limit=1)
                if zip_code_id:
                    self.state_id = zip_code_id.state_id.id

    @api.onchange('hm_technician')
    def onchange_technician(self):
        property_account_position_id = False
        if self.hm_technician:
            property_account_position_id = self.env.ref('l10n_be.1_fiscal_position_template_4')
        self.property_account_position_id = property_account_position_id and property_account_position_id.id or False

    def action_view_sale_order(self):
        super(ResPartner, self).action_view_sale_order()
        action = self.env['ir.actions.act_window']._for_xml_id('sale.action_quotations_with_onboarding')
        all_child = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        action["domain"] = [("partner_id", "in", all_child.ids)]
        return action

    def write(self, values):
        special_fields = (
            'tech_unavailability_end_date',
            'tech_unavailability_start_date',
            'hm_technician_availability_id',
            'hm_currently_unavailable',
        )
        if any(field in values for field in special_fields):
            if self.env.user.has_group('base.group_user'):
                return super(ResPartner, self.sudo()).write(values)

        if values.get('hm_status') == 'actif_app':
            for partner in self:
                token_count = self.env['hm.mobile.token'].search_count([('user_id.partner_id', '=', partner.id)])
                if token_count == 0:
                    raise UserError(_("[Mobile Token] Le technicien doit avoir installé l'application, s'être connecté et activé les notifications."))

        return super(ResPartner, self).write(values)