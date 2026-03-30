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
from odoo import fields, models, api

import logging

_logger = logging.getLogger(__name__)


class HmPropertyTenant(models.Model):
    _inherit = 'res.partner'

    birthdate = fields.Date('Birthdate')
    birthplace = fields.Char('Place of birth')
    idnbr = fields.Char('ID Number')
    nationalnbr = fields.Char('National Number')
    nationality = fields.Char('Nationality')

    is_copro = fields.Boolean('Is copro?')
    is_landlord = fields.Boolean('Is landlord?')
    is_tenant = fields.Boolean('Is tenant?')
    is_manager = fields.Boolean('Is manager?')
    is_syndic = fields.Boolean('Is Syndic?')

    landlord_manager_id = fields.Many2one('res.partner','Landlord Manger')
