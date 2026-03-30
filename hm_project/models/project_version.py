# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ProjectVersion(models.Model):
    _name = 'project.version'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'project_id, name'
    _description = 'Project Version'

    name = fields.Char("Name", required=True)
    project_id = fields.Many2one("project.project", string="Project", required=False)
    task_ids = fields.One2many("project.task", "version_id", string="Tasks")
    task_count = fields.Integer(compute='_compute_task_count', string="Nbr Tasks")
    date_target = fields.Date("Target Date")
    date_release = fields.Date("Release Date")
    sequence = fields.Integer(string='Sequence')
    description = fields.Html('Description')
    state = fields.Selection([('future', 'Future'), ('current', 'Current'), ('closed', 'Closed'), ('support', 'Support')],
                             string='Status', copy=False, index=True, tracking=True, default='future')

    @api.constrains('name', 'project_id')
    def _check_description(self):
        for record in self:
            if len(self.env['project.version'].search([('name', '=', record.name), ('project_id', '=', record.project_id.id)])) > 1:
                raise ValidationError("The name of the version must be unique by project")

    def _compute_task_count(self):
        for version in self:
            version.task_count = len(version.task_ids)

    def action_open_tasks(self):
        self.ensure_one()
        action = self.env.ref('project.act_project_project_2_project_task_all').read()[0]
        action['domain'] = [('id', 'in', self.task_ids.ids)]
        action['context'] = {'default_search_project_id': self.project_id.id, 'default_search_version_id': self.id}
        return action
