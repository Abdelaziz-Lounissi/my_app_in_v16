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


class RealtyPropertyType(models.Model):
    _name = 'hm.property.type'
    _description = 'Realty Type'
    _order = 'sequence'

    name = fields.Char(string='Realty Type Name', translate=True)
    sequence = fields.Integer(string='Sequence')
    is_residential = fields.Boolean(string='Is residential?')
    have_a_parent_property = fields.Boolean(string="A une propriété parent?", default=False)
    is_parent = fields.Boolean(string="is a parent", default=False)
