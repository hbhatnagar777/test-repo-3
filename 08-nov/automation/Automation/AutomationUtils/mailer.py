# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ---------------------------------------------------------------------------

"""Helper file for sending Automation Report emails.

Mailer is the only class defined in this file.

Mailer: Class that makes a request to the server to send email report to specified users.

Mailer:
    __init__()                  --  initialize objects of Mailer class

    _parse_template_config()     --  checks for valid json file and correcponding keys

    _parse_receiver()            -- checks for receivers and replaces the delimiters in the
                                   mail addresses by ','.

    _send_email_via_smtp         --    Sends the mail notification via SMTPlib

    mail()                      --  Sends the email to specified receivers

"""

import json
import os.path
import re
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP, SMTPException
from email.mime.text import MIMEText

from AutomationUtils import logger
from AutomationUtils.constants import AUTOMATION_EMAIL
from AutomationUtils.constants import CONFIG_FILE_PATH


class Mailer:
    """Class that makes a request to the server to send email report to specified users."""

    RECEIVERS = None

    def __init__(self, mailing_inputs=None, commcell_object=None):
        """Initialize required attributes of the mailer object.

        Args:
            mailing_inputs      (dict)    --  required inputs to send an email
                    default: None

                    Example:
                        {
                            "receiver": "user1@test.com,user2@test.com"

                        }

            commcell_object     (object)  --  object reference to this commcell
                    default: None

        **Note:**  If mailing_inputs is not defined we pick the mailing inputs from
                    static attribute (Mailer.RECEIVERS)

        """
        self._log = logger.get_log()
        self._commcell = commcell_object or self._log.error("Commcell object is not initialized.")
        self._receiver = self._parse_receiver(mailing_inputs)
        self.config_data = self._parse_config()

    def mail(self, subject, body, sender=None, attachments=None):
        """ Sends the mail notification to specified recipients via REST API if commcell
            object is initialized or via SMTPlib when commcell object is not initialized

        Args:
                subject   (str)     --  subject of the mail to be sent

                body      (str)     --  content to be sent in the mail

                sender    (str)     --  address of the email to be sent as.

                    default: None       It sends using the automation mail ID

                attachments (list)  --  list of local filepaths to send

                    default: None       No attachments in the mail reports
        """
        if sender or attachments:
            self._send_email_via_smtp(sender, subject, body, attachments)

        else:
            self._log.info("Sending email via REST API to: %s", self._receiver)
            try:
                self._commcell.send_mail(self._receiver, subject, body, self.config_data.get('copySender', True))
            except Exception as exp:
                self._log.warning("Failed to send mail with error: %s", exp)
                self._send_email_via_smtp(AUTOMATION_EMAIL, subject, body)

    def _send_email_via_smtp(self, from_, subject, body, attachments=None):
        """ Sends the mail notification via SMTPlib

        Args:
                from_    (str)     --  address of the email to be sent as

                subject   (str)     --  subject of the mail to be sent

                body      (str)     --  content to be sent in the mail

                attachments (list)  --  list of local filepaths to send as attachments

        """
        server = self.config_data.get('server')
        if not server:
            error_message = ("Email server details are not specified in configuration file.\n"
                             "Please configure email server details.")
            self._log.error(error_message)
            raise Exception(error_message)

        message = MIMEMultipart()
        message['Subject'] = subject
        message['To'] = ",".join(self._receiver)
        message.attach(MIMEText(body, 'html'))

        if attachments:
            for filepath in attachments:
                try:
                    with open(filepath, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())

                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {os.path.basename(filepath)}",
                    )
                    message.attach(part)
                except Exception as e:
                    self._log.error(f"Failed to attach file {filepath}: {e}")
                    continue

        self._log.info("Sending email via SMTP to: %s", self._receiver)
        try:
            with SMTP(server) as mail:
                if self.config_data.get('username') and self.config_data.get('password'):
                    self._log.info("Logging in the email server with the user %s", self.config_data['username'])
                    try:
                        mail.login(self.config_data['username'], self.config_data['password'])
                    except SMTPException:
                        self._log.info("Login failed. Proceeding to try relay server call")
                        context = ssl._create_unverified_context(protocol=ssl.PROTOCOL_TLS_CLIENT)
                        mail.ehlo()
                        mail.starttls(context=context)
                        mail.ehlo()
                    message['From'] = self.config_data['email_id']
                else:
                    message['From'] = from_ or AUTOMATION_EMAIL
                mail.sendmail(message['From'], self._receiver, message.as_string())
        except Exception as exp:
            error_msg = "Failed to send mail"
            self._log.error(error_msg)
            raise Exception(error_msg) from exp

    def _parse_config(self):
        """ Checks whether the path to the template_config.json is valid  and parses
            the template_config.json to get the values of server, username and password.

        Raises:
            Exception:
                     When the json file does not exist.
                     Permission is not granted on the requested file,
                     Missing key in the json.

        """
        try:
            with open(CONFIG_FILE_PATH, 'r') as config_file:
                return json.load(config_file)["email"]
        except Exception as error:
            error_message = ("Failed to read email configuration from file.\n"
                             "Either the user doesn’t have permission or key is missing in the configuration file.\n"
                             "Skip sending email via SMTP.")
            self._log.error(error_message)
            raise Exception(error_message) from error

    def _parse_receiver(self, mailing_inputs):
        """ checks for list of receiver email and also replaces the delimiters ':' and ';'
            with ','.

        Args:
                mailing_inputs   (dict)     --  email_addresses to which email has to be sent.

        Raises:
                Exception: When the email receiver list is empty.

        """
        try:
            return re.split('[;,:]', mailing_inputs.get("receiver", Mailer.RECEIVERS))
        except Exception as excp:
            error_message = "Error in parsing receivers."
            self._log.error(error_message)
            raise Exception(error_message) from excp
