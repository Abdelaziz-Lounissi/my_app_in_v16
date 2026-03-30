# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models, tools, _
from math import ceil

# TODO : move to hm_base_setup
class HmWorksCategory(models.Model):
    _name = "hm.works.category"
    _description = "Works Category"

    hm_name = fields.Char(string="HM Name", copy=True, store=True, index=False, translate=False)
    name = fields.Char(string="Name", copy=True, store=True, index=False, translate=True)
    hm_access_to_the_necessary_profession_id = fields.Many2one("hm.access.profession",
                                                               string="Accès à la profession nécessaire",
                                                               ondelete="set null", store=True, copy=True, index=False)
    hm_works_category_parent_id = fields.Many2one("hm.works.category.parent", string="Catégorie de travaux parent",
                                                  ondelete="set null", store=True, copy=True, index=False)
    hm_intervention_type = fields.Selection([("Travaux", "Travaux"), ("Maintenance", "Maintenance")], store=True,
                                            copy=True, index=False, string="Type d'intervention")
    hm_works_category_count = fields.Integer(string="Catégorie de travaux count",
                                             store=False, copy=False, index=False,
                                             compute='_compute_works_category_count')
    hm_so_manager_theoretical_workload_in_minutes = fields.Integer('Charge de gestion estimée en minutes',
                                                                   required=True, default=0)
    hm_so_manager_workload_points = fields.Integer('Points de gestion', required=True, compute='calculate_point_gestion')
    create_icr_automatically = fields.Boolean(string='Create ICR from Technician Report', default=False, help="If this box is checked, the intervention will be automatically approved upon receipt of the technician report. An ICR linked to the lead will be automatically created based on the same technician report")


    @api.depends('hm_so_manager_theoretical_workload_in_minutes')
    def calculate_point_gestion(self):
        """
            la valeur du champ 'Points de gestion' hm_so_manager_workload_points est automatiquement calculée
            quand je modifie la valeur du champ 'Charge de gestion estimée en minutes'
            formule: hm_so_manager_workload_points = hm_so_manager_theoretical_workload_in_minutes / hm_so_manager_workload_ratio
            la valeur est arrondie à l'unité supérieure si >= .5
        """
        for work in self:
            if work.hm_so_manager_theoretical_workload_in_minutes < 0:
                raise ValidationError(
                    'la valeur du Charge de gestion estimée en minutes doit être supérieure ou égale à 0')
            params = self.env['ir.config_parameter'].sudo()
            hm_so_manager_workload_ratio = int(params.get_param('hm_sale_crm.hm_so_manager_workload_ratio', default=0))
            if hm_so_manager_workload_ratio != 0:
                number_splited = str(
                    work.hm_so_manager_theoretical_workload_in_minutes / hm_so_manager_workload_ratio).split('.')
                if number_splited[1].startswith("5"):
                    work.hm_so_manager_workload_points = ceil(
                        work.hm_so_manager_theoretical_workload_in_minutes / hm_so_manager_workload_ratio)
                else:
                    work.hm_so_manager_workload_points = round(
                        work.hm_so_manager_theoretical_workload_in_minutes / hm_so_manager_workload_ratio)
            else:
                work.hm_so_manager_workload_points = 0

    def _compute_works_category_count(self):
        results = self.env['sale.order.template'].read_group([('hm_work_category', 'in', self.ids)],
                                                             ['hm_work_category'], 'hm_work_category')
        dic = {}
        for x in results:
            dic[x['hm_work_category'][0]] = x['x_studio_catgorie_de_travaux_count']
        for record in self:
            record['hm_works_category_count'] = dic.get(record.id, 0)


class HmWorksCategoryParent(models.Model):
    _name = "hm.works.category.parent"
    _description = "Works Category"

    hm_name = fields.Char(string="HM Name", copy=False, store=True, index=False, translate=False)
    name = fields.Char(string="Name", copy=False, store=True, index=False, translate=True)
    hm_sales_teams = fields.Many2one("crm.team", string="Equipes de vente", store=True, copy=False,
                                     ondelete="set null", index=False)
    hm_is_maintenance_work = fields.Boolean(string="Is Maintenance Work", store=True, copy=False, index=False)
    hm_nameplate_to_be_registered = fields.Boolean(string="Plaquette signalétique à enregistrer",
                                                   store=True, copy=False, index=False)
    do_not_display_icr_at_customer = fields.Boolean(string="Ne pas afficher l'IRC chez le client")

