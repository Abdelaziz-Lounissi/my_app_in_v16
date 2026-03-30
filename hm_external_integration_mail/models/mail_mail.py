# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import datetime
import logging
import psycopg2
import smtplib
import threading
import re

from collections import defaultdict

from odoo import _, api, fields, models
from odoo import tools
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def get_mail_references(self, model, res_id):
        references = False
        lead_id = False
        mail_references_obj = self.env['hm.mail.references']
        if model == 'crm.lead':
            lead_id = res_id
        elif model == 'sale.order':
            sale_order_id = self.env['sale.order'].browse(res_id)
            lead_id = sale_order_id.opportunity_id and sale_order_id.opportunity_id.id
        elif model == 'account.move':
            move_id = self.env['account.move'].browse(res_id)
            lead_id = move_id.sale_order_id.opportunity_id and move_id.sale_order_id.opportunity_id.id
        if lead_id:
            references = mail_references_obj.search([('lead_id', '=', lead_id)])
        return references

    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None):

        # Update the email reference before sending it
        for mail_id in self.ids:
            mail = self.browse(mail_id)
            references_id = self.get_mail_references(mail.model, mail.res_id)
            if references_id:
                mail.write({
                    'references': references_id.references,
                    'email_to': "catchall@"+ str(references_id.mail_domain_name)
                })
        result = super(MailMail, self)._send(auto_commit, raise_exception, smtp_session)
        return result
