# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib
import email
import logging
import re
import socket
from email.message import Message
from odoo import api, models, tools
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def get_references_x_odoo_objects(self, message, save_original):
        if isinstance(message, xmlrpclib.Binary):
            message = bytes(message.data)
        if isinstance(message, str):
            message = message.encode('utf-8')
        message = email.message_from_bytes(message, policy=email.policy.SMTP)
        # parse the message, verify we are not in a loop by checking message_id is not duplicated
        msg_dict = self.message_parse(message, save_original=save_original)
        references = msg_dict['references']
        x_odoo_objects = tools.decode_message_header(message=message, header='X-Odoo-Objects')
        mail_from = tools.decode_message_header(message=message, header='From', )
        # Use regular expressions to extract the domain
        pattern = r'@(\S+)\s*>'
        match = re.search(pattern, mail_from)
        mail_domain_name = ""
        if match:
            domain = match.group(1)
            mail_domain_name = domain
            return references, x_odoo_objects, mail_domain_name
        return False, False, False

    def store_references_by_x_odoo_objects(self, references, x_odoo_objects, lead_id, mail_domain_name):
        mail_references_obj = self.env['hm.mail.references']
        references_id = mail_references_obj.search([
            ('x_odoo_objects', '=', x_odoo_objects),
            ('mail_domain_name', '=', mail_domain_name)
        ])
        if not references_id:
            mail_references_obj.create({
                "name": "Reference-Lead/%s" % lead_id,
                "lead_id": lead_id,
                "references": references,
                "x_odoo_objects": x_odoo_objects,
                "mail_domain_name": mail_domain_name
            })

    def search_references_by_x_odoo_objects(self, message):
        x_odoo_objects = tools.decode_message_header(message=message, header='X-Odoo-Objects')
        mail_from = tools.decode_message_header(message=message, header='From')
        references_id = False
        # Use regular expressions to extract the domain
        pattern = r'@(\S+)\s*>'
        match = re.search(pattern, mail_from)
        if match:
            domain = match.group(1)
            mail_domain_name = domain
            domain_id = self.env['hm.mail.domain'].search([('name', '=', mail_domain_name)])
            if not domain_id:
                return False
            references_id = self.env['hm.mail.references'].search([
                ('x_odoo_objects', '=', x_odoo_objects),
                ('mail_domain_name', '=', mail_domain_name)
            ])
        return references_id

    @api.model
    def message_process(self, model, message, custom_values=None, save_original=False, strip_attachments=False, thread_id=None):
        """
        Custom processing to store mail references and x_odoo_objects
        when incoming messages are related to CRM Leads.

        Overrides the standard message_process to extract additional metadata
        (references, objects, domain) for 'crm.lead' messages and store them
        in a custom references table.
        """

        original_encoded_message = message

        result_thread_id = super(MailThread, self).message_process( model, message, custom_values=custom_values,
            save_original=save_original, strip_attachments=strip_attachments, thread_id=thread_id)

        # Decode the message again for further custom parsing
        if isinstance(message, xmlrpclib.Binary):
            message = bytes(message.data)
        if isinstance(message, str):
            message = message.encode('utf-8')
        message = email.message_from_bytes(message, policy=email.policy.SMTP)

        msg_dict = self.message_parse(message, save_original=save_original)
        routes = self.message_route(message, msg_dict, model, thread_id, custom_values)

        # Apply custom reference logic only if the message is for a CRM Lead
        if routes and isinstance(routes[0], (list, tuple)) and routes[0][0] == 'crm.lead':
            references, x_odoo_objects, mail_domain_name = self.get_references_x_odoo_objects(original_encoded_message,
                                                                                              save_original)
            domain_id = self.env['hm.mail.domain'].search([('name', '=', mail_domain_name)])

            # Store extracted metadata only if all required components are available
            if references and x_odoo_objects and mail_domain_name and domain_id:
                self.store_references_by_x_odoo_objects(
                    references=references,
                    lead_id=result_thread_id,
                    x_odoo_objects=x_odoo_objects,
                    mail_domain_name=mail_domain_name
                )

        return result_thread_id

    @api.model
    def _routing_check_route(self, message, message_dict, route, raise_exception=True):
        """
        Custom override to enforce message routing to an existing CRM Lead
        if a reference is found in the custom references table.
        """

        result = super(MailThread, self)._routing_check_route(message, message_dict, route, raise_exception)

        # Ensure the route is valid and concerns a CRM Lead
        if route and isinstance(route[0], str) and route[0] == 'crm.lead':
            # Try to find a lead based on custom reference logic
            references_id = self.search_references_by_x_odoo_objects(message=message)
            if references_id:
                # Force assign the message to the identified lead thread
                force_thread_id = references_id.lead_id.id
                result = (result[0], force_thread_id, result[2], result[3], result[4])

        return result
