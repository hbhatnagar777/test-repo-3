# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main Module for invoking ContentStore MailServer operations.

CvEML, ContentStore are the classes defined in this file.

CvEML: Class for all EMLS properties.

ContentStore: Class for performing all ContentStore related operations.

"""
import os
import sqlite3
import re
import glob
import random
import calendar
import time
import email
import sys
import shutil
import smtplib
from base64 import b64decode
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from pathlib import Path
import xmltodict
import eml_parser
from dicttoxml import dicttoxml
from AutomationUtils import machine, windows_machine
from Application.Exchange.ExchangeMailbox import constants
from .constants import CSSendEmailHelper
from .exchangelib_helper import CVMailbox
from .exchangelib_helper import CVFolder
from . import utils


class CvEML():
    """Class for CvEML Detail """

    def __init__(self):
        """Initializes the CvEML object."""
        self.eml_file_name = ""
        self.eml_from_address = ""
        self.exch_from_address = ""
        self.eml_to_address = []
        self.eml_cc_address = []
        self.exch_to_address = []
        self.exch_cc_address = []
        self.bcc_address = {}
        self.eml_subject = ""
        self.exch_subject = ""
        self.eml_received_time = ""
        self.exch_received_time = ""
        self.eml_message_id = ""
        self.exch_message_id = ""
        self.exch_description = ""
        self.exch_content_type = ""
        self.eml_received = ""
        self.exch_received = ""
        self.eml_mime_version = ""
        self.exch_mime_version = ""
        self.exch_original_arrival_time = ""
        self.exch_return_path = ""
        self.eml_sender = ""
        self.eml_return_path = ""
        self.eml_mime_version = ""
        self.eml_content_type = ""


class ContentStore():
    """Class for ContentStore Mail Server related operations."""

    def __init__(self, ex_object):
        """Initializes the ContentStore object.
            Args:
                ex_object  (Object)  --  instance of ExchangeMailbox module
            Returns:
                object  --  instance of ContentStore class"""
        self.tc_object = ex_object.tc_object
        self.log = self.tc_object.log
        self.ex_object = ex_object
        self.mail_users = ex_object.users
        self.server_name = ex_object.content_store_mail_server
        self.mailbox_type = ex_object.mailbox_type
        self.csdb = ex_object.csdb
        self.admin_user = ex_object.service_account_user
        self.admin_pwd = ex_object.service_account_password
        self.domain_username = ex_object.domain_username
        self.domain_password = ex_object.domain_userpassword
        self.domain_name = ex_object.domain_name
        self.host_machine = machine.Machine(
            ex_object.server_name, self.ex_object.commcell)
        self.imap_server = os.path.join(
            self.host_machine.client_object.install_directory,
            "ImapServer")
        self.mailbox_folder_dict = {}
        self.contentstore_mailbox_path = os.path.join(
            self.ex_object.smtp_mailbox_path, "Mailboxes")
        self.restore_path = ex_object.tc_object.tcinputs.\
            get('RestorePath', None)
        self.get_folder_paths()
        self.mailbox_prop = {}
        self.status = {}
        self.localmachine = windows_machine.WindowsMachine()

    def get_eml_properties_smtp_gateway(self, folder_path):
        """Return properties of EMLs in folder path
            Args:
                folder_path  (str)  --  folder path having EMLs
            Returns:
                output   (str)  -- output of command executed, which contains eml properties
                """
        command = (f'{self.imap_server}\\SMTPGateway.exe -dump '
                   f'-srcdir \"{folder_path}\" ')
        output = self.host_machine.execute_command(command)
        return output._output

    def read_eml_properties_from_file(self, output):
        """Read eml properties from file and stores in CvEML object
            Args:
                output (str) -- eml properties as text
            Returns:
                eml_messages (List) -- returns list of CvEML
                 properties object"""
        try:
            eml_messages = []
            output_list = output.split("* File :")
            for i in range(1, len(output_list)):

                string = output_list[i].split('Attachment :')
                if len(string) == 1:
                    contentstore = string[0]
                    exchange = ""
                else:
                    contentstore = string[0]
                    exchange = string[1]
                eachline = exchange.split('\n')
                eml_message = CvEML()
                for p in enumerate(eachline):
                    j = p[1]
                    if (j.lstrip().find("Description :") == 0 and
                            "Description :" in j):
                        eml_message.exch_description = j.lstrip().split(
                            "Description :", 1)[1]
                    elif (j.lstrip().find("ContentType :") == 0
                          and "ContentType :" in j):
                        eml_message.exch_content_type = j.lstrip().split(
                            "ContentType :", 1)[1]
                    elif (j.lstrip().find("Received :") == 0 and
                          "Received :" in j):
                        eml_message.exch_received = j.lstrip().split(
                            "Received :", 1)[1]
                    elif (j.lstrip().find("MIME-Version :") == 0 and
                          "MIME-Version :" in j):
                        eml_message.eml_mime_version = \
                            j.lstrip().split("MIME-Version :", 1)[1]
                    elif (j.lstrip().find("From :") == 0 and
                          "From :" in j):
                        eml_message.exch_from_address = \
                            j.lstrip().split("From :", 1)[1]
                    elif (j.lstrip().find("To :") == 0 and
                          "To :" in j):
                        eml_message.exch_to_address.append(
                            j.lstrip().split("To :", 1)[1])
                    elif j.lstrip().find("CC :") == 0 and \
                            "CC :" in j:
                        eml_message.exch_cc_address.append(
                            j.lstrip().split("CC :", 1)[1])
                    elif j.lstrip().find("Date :") == 0 and \
                            "Date :" in j:
                        eml_message.exch_received_time = \
                            j.lstrip().split("Date :", 1)[1]
                    elif j.lstrip().find("Subject :") == 0 and \
                            "Subject :" in j:
                        eml_message.exch_subject = \
                            j.lstrip().split("Subject :", 1)[1]
                    elif (j.lstrip().find("Message-ID :") == 0 and
                          "Message-ID :" in j):
                        eml_message.exch_message_id = j.lstrip().split(
                            "Message-ID :", 1)[1]
                    elif (j.lstrip().find("Return-Path :") == 0 and
                          "Return-Path :" in j):
                        eml_message.exch_return_path = \
                            j.lstrip().split("Return-Path :", 1)[1]
                    elif (j.lstrip().find(
                            "X-MS-Exchange-Organization-OriginalArrivalTime :") == 0
                          and "X-MS-Exchange-Organization-OriginalArrivalTime :"
                          in j):
                        eml_message.exch_original_arrival_time = \
                            j.lstrip().split("X-MS-Exchange-"
                                                       "Organization-OriginalArrivalTime :", 1)[1]

                eachline = contentstore.split('\n')
                eml_message.eml_file_name = eachline[0].split('\\')[-1]
                for p in enumerate(eachline):
                    j = p[1]
                    if j.find("Subject :") == 0 and \
                            "Subject :" in j:
                        eml_message.eml_subject = \
                            j.split("Subject :", 1)[1]
                    elif j.find("Date :") == 0 and \
                            "Date :" in j:
                        eml_message.eml_received_time = \
                            j.split("Date :", 1)[1]
                    elif j.find("From :") == 0 and \
                            "From :" in j:
                        eml_message.eml_from_address = \
                            j.split("From :", 1)[1]
                    elif j.find("To :") == 0 and \
                            "To :" in j:
                        eml_message.eml_to_address.append(
                            j.split("To :", 1)[1])
                    elif j.find("Cc :") == 0 and \
                            "Cc :" in j:
                        eml_message.eml_cc_address.append(
                            j.split("Cc :", 1)[1])
                    elif (j.find("- Return-Path :") == 0 and
                          "- Return-Path :" in j):
                        eml_message.eml_return_path = \
                            j.split("- Return-Path :", 1)[1]
                    elif j.find("- Received :") == 0 and \
                            "- Received :" in j:
                        eml_message.eml_received = \
                            j.split("- Received :", 1)[1]
                    elif j.find("- Content-Type :") == 0 and \
                            "Date :" in j:
                        eml_message.eml_content_type =\
                            j.split("- Content-Type :", 1)[1]
                    elif j.find("- Sender :") == 0 and \
                            "- Content-Type :" in j:
                        eml_message.eml_sender = \
                            j.split("- Sender :", 1)[1]
                    elif (j.find("- Message-ID :") == 0 and
                          "- Message-ID :" in j):
                        eml_message.eml_message_id = \
                            j.split("- Message-ID :", 1)[1]

                eml_messages.append(eml_message)
            return eml_messages

        except Exception as excp:
            self.log.exception("Exception in "
                               "read_eml_properties_from_file(): " + str(excp))
            raise excp

    def get_folder_properties(self, folder_path):
        """Get properties of EMLs and stores in CVFolder object
            Args:
                folder_path  (str)  --  folder path having EMLs
            Returns:
                cvfolder (CVFolder) -- returns CVFolder object"""
        folder_name = folder_path.split("\\")[-1]
        cvfolder = CVFolder()
        cvfolder.foldername = folder_name

        output = self.get_eml_properties_smtp_gateway(folder_path)
        eml_messages = self.read_eml_properties_from_file(output)
        cvfolder.messages = eml_messages
        return cvfolder

    def get_mailbox_properties(self, eml_folder_path=None):
        """Get properties of mailboxes assocaited to subclient
            Args:
                folder_path  (str)  --  if folder path
                is given read properties
                of EMls from folder_path

            Returns:
                tuple [folder_count , message_count]
                """
        cvmailbox_object = None
        if not eml_folder_path:
            for user, folders_path in self.mailbox_folder_dict.items():
                cvmailbox_object = CVMailbox()
                for folder_path in folders_path:
                    cvmailbox_object.folders.append(
                        self.get_folder_properties(folder_path))
                self.mailbox_prop[user] = cvmailbox_object
        else:
            cvmailbox_object = CVMailbox()
            cvmailbox_object.folders.append(
                self.get_folder_properties(eml_folder_path))
            self.mailbox_prop["restore_path"] = cvmailbox_object

        folders_count = len(cvmailbox_object.folders)
        messages_count = 0

        for folder in cvmailbox_object.folders:
            messages_count = messages_count + len(folder.messages)

        return [folders_count, messages_count]

    def get_folder_paths(self):
        """Get folder path in mailbox and save it in self.mailbox_folder_dict"""
        for user in self.mail_users:
            path = os.path.join(self.contentstore_mailbox_path, str(user))
            output = self.host_machine.\
                get_files_and_directory_path(path)
            output = output.split("\r\n\r\n")
            folder_list = []
            for line in output:
                name = line.strip().split("\n")
                if any(".eml" in x for x in name):
                    if name[0].strip().split(":", 1)[1] \
                            not in folder_list:
                        folder_list.append(name[0].strip().split(":", 1)[1])
            self.mailbox_folder_dict[user] = folder_list

    def delete_restore_data(self):
        """Deletes the data in restore path from
        previous jobs"""
        if 'RestorePath' not in self.tc_object.tcinputs:
            raise Exception("Please provide restore to "
                            "disk path in Input Json File")
        self.host_machine.remove_directory(
            self.tc_object.tcinputs['RestorePath'])

    def get_folder_status(self):
        """Get status from _master.db3 file"""
        try:
            for user, folders_path in self.mailbox_folder_dict.items():
                self.log.info("Getting folder status "
                              "from master db for mailbox %s", user)
                master_db_path = os.path.dirname(folders_path[0]).strip().split('\\')
                drive = master_db_path[0].split(":")[0]
                path = '\\'.join((master_db_path[1:]))
                master_db_path = (f'\\\\{self.host_machine.client_object.client_name}\\'
                                  f'{drive}$\\{path}')
                master_dat_file = os.path.join(master_db_path, "_master.db3")
                conn = sqlite3.connect(master_dat_file)
                cursor = conn.cursor()
                query = "select subfoldername, status from Info"
                master_result = cursor.execute(query)
                for row in master_result:
                    self.status[row[0]] = row[1]
        except Exception as excp:
            self.log.exception("Exception in get_folder_status(): %s", excp)
            raise excp

    def get_email_count_cache(self):
        """ Get count of emails from all _MessagesInfo.db3 files """
        emailcount = 0
        try:
            master_db_path = self.get_SMTPCacheRemotePath()

            self.localmachine.mount_network_path(str(self.master_drive),
                                                 str(self.domain_name) + "\\\\" +
                                                 str(self.domain_username),
                                                 str(self.domain_password))
            self.log.info("Connection established")
            self.log.info("Accessing Remote SMTPCache location:%s", master_db_path)
            os.chdir(master_db_path)
            messageinfo_fileslist = []
            for file in Path(master_db_path).glob("**/_MessagesInfo.db3"):
                messageinfo_fileslist.append(str(file.absolute()))
            for msginfo_file in messageinfo_fileslist:
                conn = sqlite3.connect(msginfo_file)
                cursor = conn.cursor()
                query = "select count(ID) from MessagesInfo"
                master_result = cursor.execute(query)
                for row in master_result:
                    emailcount = emailcount + int(row[0])
                    break
            return emailcount
        except Exception as excp:
            self.log.exception("Exception in get_email_count_cache(): %s", excp)
            raise excp

    def verify_datfile(self):
        """Verify _MessagesInfo.db3  dat file after content store archive job
            Returns:
                tuple : [folders_backeup, messages_backedup]
            Raises:
                Exception:
                    If verification of _MessagesInfo.db3 was not successful"""
        messages = []
        try:
            self.log.info("Verifying .dat file after archive job")
            folders_backedup = 0
            messages_backedup = 0
            for user, folders_path in self.mailbox_folder_dict.items():
                self.log.info("Validating _MessagesInfo.db3 dat files for mailbox : %s", user)
                mailbox_guid = utils.get_mailbox_guid(
                    user, self.ex_object.tc_object.subclient.subclient_id, self.csdb)
                for folder in folders_path:
                    self.log.info("Checking folder : " + folder)
                    folder_split = folder.strip().split("\\")
                    for prop_folder in self.mailbox_prop[user].folders:
                        if prop_folder.foldername == folder_split[-1]:
                            messages = prop_folder.messages
                    drive = folder_split[0].split(":")[0]
                    path = '\\'.join(folder_split[1:])
                    temp = (f'\\\\{self.host_machine.client_object.client_name}\\'
                            f'{drive}$\\{path}')
                    dat_file = os.path.join(temp, "_MessagesInfo.db3")
                    self.log.info("Verifiying post archive status of db- %s", dat_file)
                    conn = sqlite3.connect(dat_file)
                    cursor = conn.cursor()
                    query = "select id, size, backedup ,internetmessageid from MessagesInfo"
                    result = cursor.execute(query)
                    status = self.status[folder.split("\\")[-1]]
                    messages_backedup = messages_backedup + len(messages)
                    for row in result:
                        for message in messages:
                            if row[0] in message.eml_file_name:
                                intrenet_id = str(mailbox_guid) + message.eml_message_id.strip()

                                if row[2] == "true" and status == "Dump":
                                    self.log.error(
                                        "Message is backed up from current folder %s ", row[0])
                                    raise Exception("Message is backed up from current folder")
                                if row[3] != intrenet_id:
                                    self.log.error("Intranet id not saved properly.")
                                    raise Exception("Intranet id not saved properly")
                                if row[2] != "true" and status == "Archive":
                                    self.log.error("Message not backed up %s", row[0])
                                    raise Exception("Message not backed up")

                folders_backedup = folders_backedup + len(folders_path)
            return [folders_backedup, messages_backedup]

        except Exception as excp:
            self.log.exception("Exception in verify_datfile(): %s", excp)
            raise excp

    def verify_after_cleanup(self):
        """Verify folders are deleted after cleanup job
            Returns:
               Number of folders cleanedup
            Raises:
                Exception:
                    If cleanup of mailbox folder is not successful"""
        try:
            folders_cleanedup = 0
            for user, folders_path in self.mailbox_folder_dict.items():
                self.log.info("################################################")
                for folder in folders_path:
                    self.log.debug(" Checking for folder path: %s", folder)
                    status = self.status[folder.split("\\")[-1]]
                    if status.lower() == "cleanup":
                        if self.host_machine.check_directory_exists(folder):
                            self.log.error('Cleanup was not successful of folder : %s,'
                                           ' Mailbox %s', folder, user)
                            raise Exception("Cleanup Validation failed for mailbox.")
                        folders_cleanedup = folders_cleanedup + 1
            return folders_cleanedup
        except Exception as excp:
            self.log.exception("Exception in verify_after_cleanup(): %s", excp)
            raise excp

    def getEmailBody(self, texttype=None, sizetype=None):
        """Get Body of EML File
            Args:
                texttype (CSSendEmailHelper): type of text that should be inserted in the body
                                Possible values: Unicode, English
                                None- English

                sizetype (CSSendEmailHelper): Large- for 40 MB emails
                                None- small emails by default

            Returns:
                Random text as Email body : String"""
        try:
            if texttype == CSSendEmailHelper.UNICODE:
                samplespath = os.path.join(constants.SEND_SCRIPT_PATH, "Unicode_Body")
            elif sizetype == CSSendEmailHelper.LARGE:
                samplespath = os.path.join(constants.SEND_SCRIPT_PATH, "Large_Body")
            else:
                samplespath = os.path.join(constants.SEND_SCRIPT_PATH, "Body")

            random_file = random.choice(os.listdir(samplespath))
            random_file_body = samplespath + "\\" + random_file
            random_file = open(random_file_body, 'rb')
            content = random_file.read()
            random_file.close()
            return content.decode('utf-8', 'ignore')
        except Exception as excp:
            self.log.info("Error getting email body from sample dataset")
            raise excp

    def getEmailSubject(self, email_unique_id, texttype=None):
        """Get Subject of EML File
            Args:
                email_unique_id  (str): Unique ID generated while sending email
                texttype (CSSendEmailHelper): type of text that should be inserted in the subject
                                Possible values: Unicode, English
                                None- English
            Returns:
                 Random text as Email Subject : String"""
        try:
            if texttype == CSSendEmailHelper.UNICODE:
                samplespath = os.path.join(constants.SEND_SCRIPT_PATH, "Unicode_subjects.txt")
            else:
                samplespath = os.path.join(constants.SEND_SCRIPT_PATH, "subjects.txt")
            unicode_file = open(samplespath, 'rb')
            content = unicode_file.read().splitlines()
            unicode_file.close()
            rand_sub = random.choice(content).decode('utf-8', 'ignore')
            subj = rand_sub + "_" + email_unique_id
            return subj
        except Exception as excp:
            self.log.info("Error getting email subject from sample dataset."
                          " Unique_id is :" + email_unique_id)
            raise excp

    def getAttachmentLists(self, filecount, texttype=None, sizetype=None):

        """Get Attachments List for EML File
            Args:
                filecount  (int): Number of files to be attached to the email
                texttype (CSSendEmailHelper): type of text that should be inserted in the subject
                                Possible values: Unicode, English
                                None- English
                sizetype (CSSendEmailHelper): Large for 40 MB emails
                                None- small emails by default

                supported combinations of values:
                texttype: None/English and sizetype: None/Small/Large
                texttype: None/Unicode and sizetype: None/Small

            Returns:
                Random files list as Email attachments : List"""
        try:

            if texttype == CSSendEmailHelper.UNICODE:
                samplespath = os.path.join(constants.SEND_SCRIPT_PATH, "Unicode_AttachMetadata")
                sizetype = None

            else:
                samplespath = os.path.join(constants.SEND_SCRIPT_PATH, "AttachMetadata")

            if sizetype == "Large":
                samplespath = os.path.join(constants.SEND_SCRIPT_PATH, "Attach")

            loop = 0
            att_list = []
            size = 0
            while loop < filecount:
                att = random.choice(os.listdir(samplespath))
                attpath = samplespath + "\\" + att
                att_list.append(attpath)
                size = size + os.path.getsize(attpath)
                loop = loop + 1

            self.log.info("Total attachments size is %s", size)
            return att_list

        except Exception as excp:
            self.log.info("Error getting attachments list from sample dataset.")
            raise excp

    def send_email(self, mailcount, sizetype=None, texttype=None):

        """Send Emails as per the given mailcount

        Args:
                mailcount  (int): Number of emails to be generated
                sizetype (CSSendEmailHelper): Large- for 40 MB emails
                                                None- small emails by default
                texttype (CSSendEmailHelper): Unicode- for unicode text in the emails
                                                None- English text in the emails

        """

        try:
            count = 1

            while count <= mailcount:
                self.log.info('Sending email number: %s', str(count))

                xml = XMLWriter()

                self.log.info('DataSet path is %s', constants.SEND_SCRIPT_PATH)

                current_milli_time = calendar.timegm(time.gmtime())
                unique_id = str(current_milli_time)
                xml.uniqueid = unique_id

                # Getting recipients from userlist.txt file in the above path
                recipient_list = []
                userlistpath = os.path.join(constants.SEND_SCRIPT_PATH, "userlist.txt")
                userslist_file = open(userlistpath, 'r')
                for smtpaddress in userslist_file:
                    smtpaddress = smtpaddress.strip()
                    recipient_list.append(smtpaddress.lower())
                userslist_file.close()

                # setting sender,smtpserver details
                sender_smtp = constants.ADMIN_USER
                sender_smtp_password = b64decode(constants.ADMIN_PWD.encode()).decode()
                xml.from_smtp = sender_smtp.lower()

                O365_mailserver = constants.SMTP_SERVER

                # setting random text for email body, subject and attachments
                email_body = self.getEmailBody(texttype, sizetype)
                xml.body = email_body

                email_subject = self.getEmailSubject(unique_id, texttype)
                xml.subject = email_subject

                max_attachments = 10

                attcount = random.randint(1, max_attachments)
                # number of attachments to be attached to the email

                if sizetype == CSSendEmailHelper.LARGE:
                    attcount = 4

                xml.attachmentscount = attcount

                email_attachments = self.getAttachmentLists(
                    attcount, texttype, sizetype)

                # Create message container
                msg = MIMEMultipart('alternative')
                msg['From'] = sender_smtp
                to_address_list = []
                cc_address_list = []
                bcc_address_list = []

                to_address_list.append(random.choice(recipient_list))
                # multiple To address
                to_address_list.append(random.choice(recipient_list))

                cc_address_list.append(random.choice(recipient_list))
                bcc_address_list.append(random.choice(recipient_list))

                msg['To'] = ', '.join(to_address_list)
                msg['Cc'] = ', '.join(cc_address_list)
                msg['Bcc'] = ', '.join(bcc_address_list)

                xml.to_smtp = to_address_list
                xml.cc_smtp = cc_address_list
                xml.bcc_smtp = bcc_address_list

                msg['Subject'] = email_subject

                body_text = email_body
                body_html = "<p>" + email_body + "</p>"

                # Create the body of the message (a plain-text and
                # an HTML version).
                # Record the MIME types of both parts - text/plain
                # and text/html.
                part1 = MIMEText(body_text, 'plain')
                part2 = MIMEText(body_html, 'html')

                # Attach parts into message container.
                msg.attach(part1)
                msg.attach(part2)

                attachmentnames = []

                for attachment in email_attachments:
                    # open the file to be sent
                    index_filename = attachment.rfind('\\') + 1
                    att_filename = attachment[index_filename:]

                    attachmentnames.append(att_filename)

                    att = open(attachment, 'rb')
                    # instance of MIMEBase and named as p
                    part = MIMEBase('application', 'octet-stream')
                    # To change the payload into encoded form

                    part.set_payload(att.read())

                    # encode into base64
                    encoders.encode_base64(part)

                    fname = os.path.basename(attachment)

                    part.add_header('Content-Disposition', 'attachment',
                                    filename=(Header(fname, 'utf-8').
                                              encode()))

                    # attach the instance 'p' to instance 'msg'
                    msg.attach(part)

                xml.attachmentslist = attachmentnames

                # Send the message via O365 SMTP server.
                mail = smtplib.SMTP(O365_mailserver, 587, timeout=40)

                # mail.set_debuglevel(1)

                # if tls = True
                mail.starttls()

                mail.login(sender_smtp, sender_smtp_password)

                mail.ehlo()

                # sending email
                mail.sendmail(sender_smtp, to_address_list,
                              msg.as_string())

                # terminating the session
                mail.quit()

                folderpath = constants.LOCAL_WORKING_DIR + "\\O365Emails"

                xml.write_xmltofile(folderpath)

                count = count + 1

        except Exception as excp:
            self.log.info("Error sending emails --")
            self.log.error('Error %s on line %s. Error %s', type(excp).__name__,
                           sys.exc_info()[-1].tb_lineno, excp)
            raise excp

    def get_emailproperties_from_smtpcache(self):

        """Read properties of Emails in the SMTPCache Folder """

        try:

            master_db_path = self.get_SMTPCacheRemotePath()
            self.localmachine.mount_network_path(str(self.master_drive),
                                                 str(self.domain_name) + "\\\\" +
                                                 str(self.domain_username),
                                                 str(self.domain_password))

            self.log.info("Connection established")

            self.log.info("Accessing Remote SMTPCache location:%s",
                          master_db_path)
            dirpath = master_db_path + "\\Inbox"

            for file in glob.glob(dirpath + "\\*\\*.eml"):
                eml_filepath = file
                self.log.info("Reading properties of eml file: %s",
                              eml_filepath)

                eml_f = open(eml_filepath, "r", encoding="utf-8")
                content = eml_f.read()
                all_eml_properties = content.splitlines()

                bcc_value = None

                for prop in all_eml_properties:
                    if 'BCC:' in prop:
                        bcc_value = prop.split(':')[1]

                bcc_value = bcc_value[bcc_value.find('<') +
                                      1:bcc_value.find('>')]

                """
                EML_Parser 3rd party library is used to 
                parse the eml file.
                Attachment body parsing code has been commented, 
                as parser fails to work with unicode body.
                Attachment name with/ without unicode characters is 
                retrieved along with other metadata.
                """
                dic = eml_parser.eml_parser.decode_email(eml_filepath,
                                                         include_raw_body=True)

                number_attachments = 0
                xml = XMLWriter()

                # getting metadata from eml msg : subject, from,
                # to[list], cc[list], bcc [list] ,attachment [list], body

                subject = dic['header']['subject']
                xml.subject = subject

                from_smtp = dic['header']['from']
                xml.from_smtp = from_smtp

                # getting recipient information

                if 'to' in dic['header']:
                    xml.to_smtp = dic['header']['to']
                if 'cc' in dic['header']:
                    xml.cc_smtp = dic['header']['cc']

                xml.bcc_smtp = bcc_value.split(',')

                attname_list = []

                # getting all attachment names and
                # storing them in the list

                if 'attachment' in dic:
                    for att in dic['attachment']:
                        attname = att['filename']
                        if attname not in ("part-000"):
                            attname_list.append(attname)
                            number_attachments = \
                                number_attachments + 1
                    xml.attachmentslist = attname_list
                    xml.attachmentscount = number_attachments

                # getting message body

                eml_file = open(eml_filepath, 'rb')
                content = eml_file.read()
                eml_file.close()
                msg = email.message_from_bytes(content)
                body_parts = eml_parser.eml_parser.get_raw_body_text(msg)
                xml.body = body_parts[1][1]

                unique_id_indx = subject.rfind('_') + 1
                xml.uniqueid = subject[unique_id_indx:]

                folderpath = constants.LOCAL_WORKING_DIR + "\\SMTPCacheEmails"

                self.log.info("Eml file %s has email generated with unique_id %s",
                              eml_filepath, xml.uniqueid)

                xml.write_xmltofile(folderpath)

        except Exception as excp:
            self.log.info('Error on line %s', format(sys.exc_info()[-1].tb_lineno),
                          type(excp).__name__, excp)
            self.log.info("Error getting eml file properties.", )
            raise excp

    def get_SMTPCacheRemotePath(self):

        """Get SMTPCache location on remote machine"""

        try:
            for user in self.mail_users:
                path = os.path.join(self.contentstore_mailbox_path,
                                    str(user))

                master_db_path = path.strip().split('\\')
                drive = master_db_path[0].split(":")[0]
                master_drive = f'\\\\{self.host_machine.client_object.client_name}' \
                               f'\\'f'{drive}$'
                self.master_drive = master_drive
                path = '\\'.join((master_db_path[1:]))
                master_db_path = (f'\\\\{self.host_machine.client_object.client_name}\\'
                                  f'{drive}$\\{path}')
                self.log.info("SMTP Cache location is : %s", master_db_path)

                return master_db_path

        except Exception as excp:
            self.log.info('Error on line %s', format(sys.exc_info()[-1].tb_lineno),
                          type(excp).__name__, excp)
            self.log.info("Error getting remote SMTP Cache location.", )
            raise excp

    def cleanup_SMTPCache(self):

        """Cleanup SMTPCache location on remote machine"""

        try:
            master_db_path = self.get_SMTPCacheRemotePath()
            self.localmachine.mount_network_path(str(self.master_drive),
                                                 str(self.domain_name) + "\\\\" +
                                                 str(self.domain_username),
                                                 str(self.domain_password))
            self.log.info("Connection established")
            self.log.info("Accessing Remote SMTPCache location:%s", master_db_path)
            self.log.info("Cleaning up SMTPCache")
            dirpath = master_db_path + "\\Inbox"
            if os.path.exists(dirpath) and os.path.isdir(dirpath):
                shutil.rmtree(dirpath)

        except Exception as excp:
            self.log.info('Error on line %s', format(sys.exc_info()[-1].tb_lineno),
                          type(excp).__name__, excp)
            self.log.info("Error cleaning remote SMTP Cache", )
            raise excp

    def cleanup_AutomationTemp(self):
        """ Cleanup Automation data location """
        try:
            self.log.info("Cleaning up Automation Temporary Directory")
            dirpath = constants.LOCAL_WORKING_DIR + "\\O365Emails"
            if os.path.exists(dirpath):
                shutil.rmtree(dirpath)
            dirpath = constants.LOCAL_WORKING_DIR + "\\SMTPCacheEmails"
            if os.path.exists(dirpath):
                shutil.rmtree(dirpath)

        except Exception as excp:
            self.log.info('Error on line %s', format(sys.exc_info()[-1].tb_lineno),
                          type(excp).__name__, excp)
            self.log.info("Error cleaning Automation Temporary Directory", )
            raise excp

class XMLWriter:
    """Class for write EML to XML """
    def __init__(self):
        self.uniqueid = None
        self.subject = None
        self.from_smtp = None
        self.to_smtp = None
        self.cc_smtp = None
        self.bcc_smtp = None
        self.attachmentscount = None
        self.attachmentslist = None
        self.body = None

    def write_xmltofile(self, folderpath):
        """
        Write metadata to XML files
        Args:
            folderpath: (str): Windows Path to save XML files
        """
        try:
            xml = dicttoxml(self.__dict__)
            xml = xml.decode()

            try:
                os.stat(folderpath)
            except:
                os.mkdir(folderpath)
            filename = folderpath + "\\" + str(self.uniqueid) + ".xml"
            xmlfile = open(filename, "w", encoding="utf-8")
            xml = re.sub(r"[\n\t\s]*", "", xml)  # remove all white spaces,
            # new lines, tabs
            xmlfile.write(xml)
            xmlfile.close()
        except Exception as excp:
            raise excp

    def comparexmlfiles(self, xml_path_O365, xml_path_smtp):

        """Compare xml files at SMTPCache location with automation
        generated xml files

        Args:
                xml_path_O365  (str): Windows Path of XML files
                generated while sending emails via Office365 Server

                xml_path_smtp  (str): Windows Path of XML files
                generated after reading metadata of SMTPCache emails
        Returns:
            Difference between xml files: Dict"""

        try:
            o365file = open(xml_path_O365, "r", encoding="utf-8")
            text1 = o365file.read()
            o365_val = set((xmltodict.parse(text1)).items())
            smtpfile = open(xml_path_smtp, "r", encoding="utf-8")
            text2 = smtpfile.read()
            smtp_val = set((xmltodict.parse(text2)).items())
            res = o365_val ^ smtp_val
            if res:
                return res
        except Exception as excp:
            raise excp
