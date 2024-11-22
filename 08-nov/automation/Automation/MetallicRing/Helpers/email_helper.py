# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for sending email post Metallic Ring configuration

    EmailHelper:

        __init__()                              --  Initializes email Helper

        send_init_failure_mail                  --  Sends the initialization failure mail containing
                                                    the information of the exception

        send_welcome_mail                       --  Sends the welcome mail containing the information
                                                    to track the ring progress

        is_mail_sent                            --  Check if a mail is already sent to a given user for a given ring

        send_next_steps_mail                    --  Sends the next steps to be carried out post the
                                                    ring configuration is complete

        send_status_mail                        --  Sends the information about the ring configuration to the end users

        send_pr_mail                            --  Sends mail to list of users to approve the PR created in azure portal

        __get_html_info                         --  Reads the data from Metallic Ring DB and gets the needed HTML
                                                    table rows for rendering

        __send_mail                             --  Sends mail with the given subject, body, mailserver, from,
                                                    to, and cc addresses

"""

import smtplib
import time
from AutomationUtils import logger
from AutomationUtils.config import get_config
from MetallicRing.Core.sqlite_db_helper import SQLiteDBQueryHelper
from MetallicRing.DBQueries import Constants as db_cs
from MetallicRing.Utils import Constants as cs
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_MAIL_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.mailing_info
_RING_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class EmailHelper:
    """helper class for sending email post Metallic Ring configuration"""

    def __init__(self, ring_id, commcell_name):
        self.ring_id = ring_id
        self.commcell_name = commcell_name
        self.log = logger.get_log()
        self.db_obj = SQLiteDBQueryHelper()

    def send_init_failure_mail(self, exception, from_addr=_MAIL_CONFIG.from_addr, to_addr=_MAIL_CONFIG.to_addr,
                               cc_addr=_MAIL_CONFIG.sre_team_cc_email):
        """
        Sends the initialization failure mail containing the information of the exception
        Args:
            from_addr       -   From address of the mail to be sent
            to_addr         -   To address of the mail to be sent
            cc_addr         -   CC address of the mail to be sent
        """
        self.log.info(f"Sending init failure mail")
        subject = f"SaaS Ring [{self.ring_id}] Configuration has failed to start"
        html = cs.EMAIL_INIT_FAILURE_CONSTANT
        html = html.replace("<<<RING_NAME>>>", self.ring_id)
        html = html.replace("<<<EXCEPTION>>>", exception)
        self.__send_mail(subject, from_addr, to_addr, cc_addr, html)
        self.log.info("Metallic ring status mail sent successfully")

    def send_welcome_mail(self, from_addr=_MAIL_CONFIG.from_addr, to_addr=_MAIL_CONFIG.to_addr,
                          cc_addr=_MAIL_CONFIG.sre_team_cc_email):
        """
        Sends the welcome mail containing the information to track the ring progress
        Args:
            from_addr       -   From address of the mail to be sent
            to_addr         -   To address of the mail to be sent
            cc_addr         -   CC address of the mail to be sent
        """
        self.log.info(f"Sending welcome mail")
        if self.is_mail_sent(self.ring_id, to_addr):
            self.log.info("Welcome Mail is already sent. Not sending again")
            return
        ring_status_url = _RING_CONFIG.status_url % (self.ring_id.lower(), self.commcell_name)
        subject = f"SaaS Ring [{self.ring_id}] Configuration has started"
        html = cs.EMAIL_WELCOME_TRACK_CONSTANT
        html = html.replace("<<<RING_NAME>>>", self.ring_id)
        html = html.replace("<<<COMMCELL_NAME>>>", self.commcell_name)
        html = html.replace("<<<STATUS_URL>>>", ring_status_url)
        self.__send_mail(subject, from_addr, to_addr, cc_addr, html)
        self.db_obj.execute_query(db_cs.INSERT_WELCOME_MAIL_QUERY % (self.ring_id, '%s', to_addr))
        self.log.info("Metallic ring status mail sent successfully")

    def is_mail_sent(self, ring_id, sent_to):
        """
        Check if a mail is already sent to a given user for a given ring
        Args:
            ring_id(str)        --  Name of the ring
            sent_to(str)        --  Email to which the mail is sent to
        Returns:
            bool                -- true if mail is sent else false
        """
        self.log.info(f"Checking if mail is sent for ring [{ring_id}] to user(s) [{sent_to}]")
        query = db_cs.SELECT_WELCOME_MAIL_QUERY % (ring_id, sent_to)
        result = self.db_obj.execute_query(query)
        self.log.info(f"Query returned - [{result.rows}]")
        if len(result.rows) != 0:
            self.log.info("Mail sent already. Returning true")
            return True
        self.log.info("Mail is not sent. Returning false")
        return False

    def send_next_steps_mail(self, from_addr=_MAIL_CONFIG.from_addr, to_addr=_MAIL_CONFIG.to_addr,
                             cc_addr=_MAIL_CONFIG.sre_team_cc_email):
        """
        Sends the next steps to be carried out post the ring configuration is complete
        Args:
            from_addr       -   From address of the mail to be sent
            to_addr         -   To address of the mail to be sent
            cc_addr         -   CC address of the mail to be sent
        """
        self.log.info(f"Sending final mail with configuration status complete")
        subject = f"SaaS Ring [{self.ring_id}] Configuration Complete"
        html = cs.EMAIL_NEXT_STEPS_CONSTANT
        html = html.replace("<<<RING_NAME>>>", self.ring_id)
        html = html.replace("<<<COMMCELL_NAME>>>", self.commcell_name)
        html = html.replace("<<<OWNER>>>", to_addr)
        html = html.replace("<<<COMPANY_NAME>>>", f"{cs.CMP_NAME}{self.ring_id}")
        html = html.replace("<<<USERNAME>>>", cs.CMP_USER_NAME)
        self.__send_mail(subject, from_addr, to_addr, cc_addr, html)
        self.log.info("Metallic ring status mail sent successfully")

    def send_status_mail(self, from_addr=_MAIL_CONFIG.from_addr, to_addr=_MAIL_CONFIG.to_addr,
                         cc_addr=_MAIL_CONFIG.sre_team_cc_email):
        """
        Sends the information about the ring configuration to the end users
        Args:
            from_addr       -   From address of the mail to be sent
            to_addr         -   To address of the mail to be sent
            cc_addr         -   CC address of the mail to be sent
        """
        self.log.info(f"Sending Ring Status Mail")
        subject = f"SaaS Ring [{self.ring_id}] Configuration Status Report"
        html = cs.EMAIL_HTML_CONSTANT
        table_rows = self.__get_html_info()
        html = html.replace("<<<TABLE_DATA>>>", table_rows)
        html = html.replace("<<<RING_NAME>>>", self.ring_id)
        html = html.replace("<<<COMMCELL_NAME>>>", self.commcell_name)
        self.__send_mail(subject, from_addr, to_addr, cc_addr, html)
        self.log.info("Metallic ring status mail sent successfully")

    def send_pr_mail(self, from_addr=_MAIL_CONFIG.from_addr, to_addr=_MAIL_CONFIG.sre_team_to_mail,
                     cc_addr=_MAIL_CONFIG.sre_team_cc_email):
        """
        Sends mail to list of users to approve the PR created in azure portal
        Args:
            from_addr       -   From address of the mail to be sent
            to_addr         -   To address of the mail to be sent
            cc_addr         -   CC Mail addresses
        """
        self.log.info(f"Sending mail for PR request approval")
        subject = f"Pull request received for {self.ring_id}. Waiting on approval"
        html = cs.EMAIL_PR_HTML_CONSTANT
        html = html.replace("<<<RING_NAME>>>", self.ring_id)
        html = html.replace("<<<COMMCELL_NAME>>>", self.commcell_name)
        self.__send_mail(subject, from_addr, to_addr, cc_addr, html)
        self.log.info(f"Mail sent successfully")

    def __send_mail(self, subject, from_addr, to_addr, cc_addr, body, email_server=_MAIL_CONFIG.smtp_server):
        """
        Sends mail with the given subject, body, mailserver, from, to, and cc addresses
        Args:
            subject         -   Subject of the mail
            from_addr       -   From address of the mail to be sent
            to_addr         -   To address of the mail to be sent
            cc_addr         -   CC Mail addresses
            body            -   Content of the mail
            email_server    -   Name of the email server
        """
        self.log.info(f"Initializing mail with to [{to_addr}], from [{from_addr}] and SMTP Server - [{email_server}]")

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['CC'] = cc_addr
        msg['To'] = to_addr
        message_html = MIMEText(body, 'html')
        self.log.info(f"HTML Message formed - [{message_html}]")
        msg.attach(message_html)
        mail_server = smtplib.SMTP(email_server)
        to_addr = f"{to_addr}, {cc_addr}"
        mail_server.sendmail(from_addr, to_addr.split(","), msg.as_string())
        self.log.info("Mail sent successfully")
        mail_server.quit()

    def __get_html_info(self):
        """
        Reads the data from Metallic Ring DB and gets the needed HTML table rows for rendering
        """
        self.log.info("Forming the HTML table rows needed for sending email")
        query = db_cs.SELECT_RING_EMAIL_QUERY % self.ring_id.lower()
        result = self.db_obj.execute_query(query)
        state_dict = {0: "Started", 1: "Completed", 2: "Pending", -1: "Failed"}
        table_rows = ""
        for index, row in enumerate(result.rows):
            state = state_dict.get(row[1], "Unavailable")
            table_row = f"<tr>" \
                        f"<td>{index + 1}</td>" \
                        f"<td>{row[0]}</td>" \
                        f"<td>{state}</td>" \
                        f"<td>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row[2]))}</td>" \
                        f"<td>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row[3]))}</td>" \
                        f"<td><span class='text'>{row[4]}</span></td>" \
                        f"</tr>"
            table_rows += table_row
        self.log.info(f"Table row formed is [{table_rows}]")
        return table_rows
