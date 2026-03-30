# -*- encoding: utf-8 -*-
# ############################################################################
#
#    Copyright Mars & Moore sprl
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import timedelta

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    emails_to_ignore = fields.Char(string="E-mails à ignorer", help="Les e-mails listés dans ce champ ne seront pas copiés depuis le lead au moment de la création du propriétaire et/ou du locataire",config_parameter='emails_to_ignore')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        emails_to_ignore = params.get_param('emails_to_ignore', default=[])
        res.update(
            emails_to_ignore=emails_to_ignore,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("emails_to_ignore", self.emails_to_ignore)
