# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import operator as py_operator

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne,
    'ilike': py_operator.contains,
}


class ResUsers(models.Model):
    _inherit = "res.users"

    hm_is_internal_user = fields.Boolean(compute='_compute_is_internal_user', search='_for_is_internal_user', index=True)

    def _compute_is_internal_user(self):
        for user in self:
            hm_is_internal_user = False
            if user.has_group('base.group_user'):
                hm_is_internal_user = True
            user.hm_is_internal_user = hm_is_internal_user

    def _for_is_internal_user(self, operator, value):
        user_ids = []
        for user in self.with_context(prefetch_fields=False).search([]):
            if operator == 'not ilike' :
                if value not in user['hm_is_internal_user']:
                    user_ids.append(user.id)
            elif OPERATORS[operator](user['hm_is_internal_user'], value):
                user_ids.append(user.id)
        return [('id', 'in', user_ids)]
