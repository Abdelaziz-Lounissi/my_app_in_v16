from odoo import fields, models, api, _
import firebase_admin
from firebase_admin import messaging
from odoo.exceptions import ValidationError
import base64
import json
from datetime import datetime
from firebase_admin import get_app, initialize_app, credentials
from werkzeug.urls import url_encode
import ast
import logging

_logger = logging.getLogger(__name__)

class MobileNotification(models.Model):
    _name = 'hm.mobile.notification'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Mobile Notification'
    _order = "sent_date desc"

    name = fields.Char(compute='_compute_name', string="Name", store=True)
    title = fields.Char(string="Title", required=True)
    message = fields.Text(string="Message", required=True)
    datas = fields.Text(string="Datas", required=False)
    token_ids = fields.Many2many(
        comodel_name="hm.mobile.token",
        string="Tokens",
        required=True,
        relation="hm_mobile_notification_token_rel",
        column1="notification_id",
        column2="token_id"
    )

    user_id = fields.Many2one("res.users", string="User")
    technician_id = fields.Many2one("res.partner", string="Technician")
    sent_date = fields.Datetime(string="Sent Date")
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('fail', 'Fail'),
            ('success', 'Success')
        ],
        'Status',
        readonly=True,
        default='draft'
    )

    @api.depends('state')
    def _compute_name(self):
        for notification in self:
            name = '/'
            if notification.state != 'draft':
                name = f"Notification/{notification.id}"
            notification.name = name

    def init_firebase(self, force_reinitialize=False):
        # Initialize the Firebase application
        params = self.env['ir.config_parameter'].sudo()
        account_key_file = params.get_param('account_key', default=False)

        if self.env.context.get('check_account_key_from_file', False):
            account_key_file = self.env.context.get('account_key', False)

        if not self.env.context.get('check_account_key_from_file', False) and not account_key_file:
            raise ValidationError('Impossible de se connecter à Firebase - fichier de clé privée manquant!')

        try:
            if not force_reinitialize:
                # Check if the Firebase app is already initialized
                app = get_app()
            else:
                # Delete and reinitialize the app
                app = get_app()
                firebase_admin.delete_app(app)
                raise ValueError  # Force to reinitialize after deletion

        except ValueError:
            # The app was not initialized or was explicitly deleted, so initialize it now
            try:
                account_key_data = base64.b64decode(base64.b64decode(account_key_file))
                account_key_dict = json.loads(account_key_data)

                # Initialize the Firebase app with the parsed file contents
                cred = credentials.Certificate(account_key_dict)
                initialize_app(cred)
                _logger.info("Firebase SDK initialized successfully.")

            except Exception as e:
                _logger.error(f'Failed to initialize Firebase SDK: {e}')
                raise ValidationError('Impossible de se connecter à Firebase - fichier de clé privée incorrect!')

    def send_token_push(self, title, body, tokens, datas):
        _logger.info("Sending notification ID: %s to Firebase" % self.id)

        params = self.env['ir.config_parameter'].sudo()
        account_key_file = params.get_param('account_key', default=False)
        apns = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound="default")
            )
        )
        if not account_key_file:
            self.init_firebase()
        try:
            # Retrieve the app instance
            get_app()
        except ValueError:
            # App is not initialized, so reinitialize it
            self.init_firebase()

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                tokens=tokens,
                data=datas,
                apns=apns
            )
            messaging.send_each_for_multicast(message)
            _logger.info("--- Sending notification ID: %s to Firebase" % self.id)
        except Exception as e:
            _logger.error(f'Error sending notification: {e}')
            # If sending fails due to SDK expiration or invalid state, try reinitializing the Firebase app and retry
            try:
                _logger.info("Reinitializing Firebase SDK due to error.")
                self.init_firebase(force_reinitialize=True)
                # Retry sending the message
                messaging.send_each_for_multicast(message)
                _logger.info("--- Retried and sent notification ID: %s to Firebase" % self.id)
            except Exception as retry_exception:
                _logger.error(f'Retry failed: {retry_exception}')
                raise ValidationError(f"Failed to send notification after retry: {retry_exception}")

    def send_email(self, error_message, type):
        model_name = self._name
        record_id = self.id

        url_params = {
            'id': record_id,
            'model': model_name,
            'view_type': 'form'
        }

        encoded_record_url = url_encode(url_params)
        record_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/web?#' + encoded_record_url

        if type == "failure":
            mail_template = self.env.ref('hm_firebase_integration.mail_template_notification_failure')
            body_html = (
                "<p>An error occurred while sending the notification:</p>"
                f"<p>{error_message}</p>"
                f"<p>Record URL: <a href='{record_url}'>{record_url}</a></p>"
            )
            subject = 'Notification Failure'
        else:
            mail_template = self.env.ref('hm_firebase_integration.mail_template_delete_notification')
            body_html = (
                f"<p>Record URL: <a href='{record_url}'>{record_url}</a></p>"
            )
            subject = 'Deleting Notification'

        mail_template.send_mail(
            self.id,
            force_send=True,
            raise_exception=False,
            email_values={
                'subject': subject,
                'body_html': body_html,
                'body': body_html,
                'email_to': """ "Jérôme [Heat Me]" <jerome@heat-me.be>""",
                'email_cc': """ "Aziz" <abdelaziz@yourent.immo>""",
                'email_from': self.env.ref('base.user_root').email_formatted,
                'author_id': self.env.ref('base.partner_root').id
            }
        )

    def action_send_notification(self):
        tokens = self.token_ids.mapped('firebase_registration_token')
        tokens_users = ', '.join(self.token_ids.mapped('user_id').mapped('name'))
        title = self.title
        body = self.message
        datas_str = {}
        datas = False
        context = self.env.context

        if not title or not body or not tokens:
            self.state = 'fail'
            error_message = "Some mandatory fields are missing. Please check the record."
            self.message_post(
                body=f"""<div class="o_thread_message_content">
                        <span>Erreur: {error_message}</span>
                    </div>"""
            )
            # Send email to Jerome and Aziz
            self.send_email(error_message=error_message,  type="failure")
            return

        if self.datas:
            datas = ast.literal_eval(self.datas)
            datas_str = {str(key): str(value) for key, value in datas.items()}

        try:
            self.send_token_push(title=title, body=body, tokens=tokens, datas=datas_str)
            self.state = 'success'
            self.sent_date = datetime.now()
            self.message_post(
                body=_(
                    """<div class="o_thread_message_content">
                    <ul class="o_mail_thread_message_tracking">
                        <li> Destinataires:
                            <span> %s </span>
                        </li> 
                        <li> Title:
                            <span> %s </span>
                        </li>    
                        <li> Message:
                            <span> %s </span>
                        </li>
                    </ul>
                    </div>"""
                ) % (tokens_users, title, body)
            )

            if context and context.get('so_id', False):
                so_id = context.get('so_id', False)
                so_rec = self.env['sale.order'].browse(so_id)
                so_rec.message_post(
                    body=_(
                        """<div class="o_thread_message_content">
                         %s - %s envoyé à %s
                        </div>"""
                    ) % (title, body, tokens_users)
                )

        except Exception as e:
            self.state = 'fail'
            self.message_post(
                body=f"""<div class="o_thread_message_content">
                        <span>Erreur: {e}</span>
                    </div>"""
            )
            # Send email to Jerome and Aziz
            self.send_email(error_message=e, type= "failure")

    def unlink(self):
        for notification in self:
            notification.send_email(error_message="", type="unlink")
        return super(MobileNotification, self).unlink()

