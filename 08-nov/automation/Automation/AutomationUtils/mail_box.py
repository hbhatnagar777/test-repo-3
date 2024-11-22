# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
File to connect to mail server and download emails.

MailBox
=======

Connect()        -- Connect to the Mail server

Disconnect()     -- Disconnect to the Mail server

download_mails() -- download the e-mails

EmailSearchFilter
=================
__init__()        --  initializes search filter with mail subject

use corresponding setter methods to add more filters to search emails

"""
import imaplib
import os
from email import message_from_string
from email.utils import parseaddr
import string
import mimetypes
from time import sleep
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup

from random import randint
from AutomationUtils import (
    logger,
    config
)

_CONF = config.get_config()
_EMAIL_CONSTANTS = _CONF.email


class MailBox:
    """
    Module to connect to mail server to download e-mails.
    default values of mail server credentials and smtp server name are taken from config json.
    for defining search filter refer to EmailSearchFilter class

    > Example Usage:

        from AutomationUtils.mail_box import MailBox,EmailSearchFilter
        mail_box = MailBox()
        mail_box.connect()
        search_query = EmailSearchFilter('test_mail_subject')
        mail_box.download_mails(search_query, download_dir='c:\\downloads')
        mail_box.disconnect()

    > for setting download directory from testcase use the below method to create a testcase
    directory inside temp directory of automation

        from Reports.utils import TestCaseUtils
        self.utils = TestCaseUtils(self)
        self.utils.reset_temp_dir()
        download_directory = self.utils.get_temp_dir()

    """
    def __init__(self, mail_server=_EMAIL_CONSTANTS.server, username=_EMAIL_CONSTANTS.username,
                 password=_EMAIL_CONSTANTS.password):
        """
        Args:
            mail_server (str): name of the mail server

            username    (str): username of the mailbox

            password    (str): password of the mailbox

        """
        self.mail_server = mail_server
        self.username = username
        self.password = password
        self.mail_box = None
        self.default_folder = 'INBOX'
        self.log = logger.get_log()
        self.local_dir_mail_download = None
        self._mail = None

    def _mark_mail_as_read(self, uid):
        """
        Mail the mail as read

        Args:
            uid (int): unique id of the mail

        """
        try:
            self.mail_box.store(uid, '+FLAGS', '\Seen')
            return True
        except Exception as excep:
            raise Exception('Failed to mark mail as read') from excep

    def _get_mail_uid_list(self, search_filter, mail_folder='INBOX'):
        """
            Returns a list of Unique IDs for the mails on the mailbox.
            If a search_query is passed, the mails are filtered using the IMAP Search Command.
        """
        self._select_folder(mail_folder)
        search_filter = search_filter.return_search_query_string()
        self.log.info(
            'Searching for mails with the following search query: %s', search_filter
        )
        result, data = self.mail_box.search(None, search_filter)
        if result != 'OK':
            raise Exception(
                'Searching for emails failed, Mailbox returned [%s] for the search query: [%s].'
                % (result, str(search_filter))
            )
        unique_ids = data[0].split()
        self.log.info('Search returned [%s] mails', len(unique_ids))
        return unique_ids

    def _parse_mails(self, mail_uid):
        """
        Parse the mail and extract the data.

        Args:
            mail_uid (int) : unique id of the mail

        """
        # self.log.info('Processing mail with UID: ' + mail_uid)
        result, data = self.mail_box.fetch(mail_uid, '(RFC822)')
        if result != 'OK':
            raise Exception(u'Failed to fetch Mail with reason: [%s]', result)
        # The Body is in [0][1]
        email_message = message_from_string(data[0][1].decode("utf-8"))
        mail = dict((x, y) for x, y in email_message.items())
        from_addresses_raw = []
        to_addresses_raw = []
        # process individual addresses for the 'From' mail header field
        if email_message['From'] is not None:
            from_addresses_raw = email_message['From'].split(',')
        from_address = []
        for email_address in from_addresses_raw:
            parsed_email = parseaddr(email_address)
            from_address.append(parsed_email[1])
        mail['From'] = from_address

        if email_message['To'] is not None:
            to_addresses_raw = email_message['To'].split(',')
        to_address = []
        for email_address in to_addresses_raw:
            parsed_email = parseaddr(email_address)
            to_address.append(parsed_email[1])
        mail['To'] = to_address
        mail['Body'] = self._get_text_blocks(email_message)
        mail['Attachments'] = self._get_attachments(email_message)
        mail['uid'] = mail_uid
        # self.log.info('Processed mail with UID: ' + mail_uid)
        return mail

    def check_if_mail_body_contains(self, mail_uid, pattern_list):
        """Parses through the body of the mail with given uid and checks the existence
            of the values in the mail body

            Args:
                mail_uid    (int)  -  UID of the fetched mail
                pattern_list (list) - List of values to be matched in the mail body

            Returns:
                bool - True if pattern matches else False

            NOTE : It is on the tester on what all values he wants to check for in the Mail Body. The function
            performs a hard match
        """
        mail = self._parse_mails(mail_uid=mail_uid)
        body = mail.get("Body", None)[0].decode('utf-8')

        pattern_match = True
        for match_criteria in pattern_list:
            if not bool(re.search(match_criteria, body)):
                pattern_match = False
                break

        return pattern_match

    @staticmethod
    def format_filename(file_name):
        """
        formats the file name with only allowed characters
        Args:
            file_name (str): file name

        Returns: valid filename for the given string

        """
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in file_name if c in valid_chars)
        return filename

    @classmethod
    def _get_text_blocks(cls, email_message_instance):
        """
            Get a list of the text blocks in the mail.
            Currently includes the attachments which are of type text/html and text/plain
        """
        if email_message_instance.is_multipart():
            text_blocks = []
            for part in email_message_instance.walk():
                if part.get_content_maintype() == 'text' and part.get_filename(False) is False:
                    content = part.get_payload(decode=True)
                    if content is not None:
                        text_blocks.append(content)
            return text_blocks
        else:
            content = email_message_instance.get_payload(decode=True)
            if content is not None:
                return [content]

    def _get_attachments(self, email_message_instance):
        """
            Get a list of the text blocks in the mail.
            Currently includes the attachments which are of type text/html and text/plain
        """
        attachments = {}
        if email_message_instance.is_multipart():

            for part in email_message_instance.walk():
                if part.get_filename(False) is not False:
                    self.log.info('Attachment MIME type:' + mimetypes.guess_extension(
                        part.get_content_type()))
                    content = part.get_payload(decode=True)
                    if content is not None:
                        attachments[part.get_filename()] = content
        return attachments

    def _write_mail_to_disk(self, mail, save_attachments):
        """
        Write the mails to the local directory which can be configured during class initialization.
        """
        if not os.path.isdir(self.local_dir_mail_download):
            self.log.info('Creating the directory for downloading the mails.')
            os.mkdir(self.local_dir_mail_download)

        # Find type of mail(ex: text/plain) and save it to a filename appropriate for the type
        # Default to HTML. (Mails come with mixed mode which would work best saved as HTML)

        if 'Content-Type' not in mail:
            mail_type = 'html'
        else:
            mail_type = mail['Content-Type'].split(';')[0].split('/')[1]

        if 'Subject' in mail:
            subject = mail['Subject']
        else:
            subject = 'Subject Not Found'
        if mail_type == 'plain':
            file_name = self.format_filename(subject.strip() + '.txt')
        else:
            file_name = self.format_filename(subject.strip() + '.html')
        file_path = os.path.join(self.local_dir_mail_download,
                                 mail['uid'] + '-' + file_name)
        # worst case, if a file name is repeated, attach a random number to the file name
        if os.path.isfile(file_path):
            file_path = os.path.join(self.local_dir_mail_download,
                                     str(randint(0, 1000)) + '-' +
                                     mail['uid'] + '-' + file_name)
        file_obj = open(file_path, 'w+', encoding="utf-8")
        if 'Body' in mail and mail['Body']:
            file_obj.write(mail['Body'][0].decode("utf-8"))
            file_obj.close()
        # save the attachments
        if save_attachments is True and len(mail['Attachments']) != 0:
            self.log.info(
                "Processing [%s] Attachments for email with UID [%s]", len(mail['Attachments']),
                mail['uid']
            )
            attachments_dir_path = os.path.join(self.local_dir_mail_download,
                                                'Attachment-' +
                                                mail['uid'] + '-' + self.format_filename(
                                                    subject.strip()))
            if not os.path.isdir(attachments_dir_path):
                os.mkdir(attachments_dir_path)
            # 'filename' : content
            for file_name in mail['Attachments']:
                file_obj = open(
                    os.path.join(attachments_dir_path, self.format_filename(file_name)),
                    'wb'
                )
                file_obj.write(mail['Attachments'][file_name])
                file_obj.close()
        return True

    def connect(self):
        """Connects to the IMAP server

        Raises:
            Exception:
                if there is a connection failure
        """
        for retry in range(1, 11):
            try:
                # Due to security settings non ssl connection may fail hence imap4_ssl is used
                self.mail_box = imaplib.IMAP4_SSL(self.mail_server)
                if isinstance(self.username, str) and isinstance(self.password, str):
                    self.mail_box.login(self.username, self.password)
                else:
                    self.mail_box = None
                    raise Exception(
                        'Invalid username or password for mail server %s', self.mail_server)
                self.log.info('Connected to mail server %s', self.mail_server)
                return
            except Exception as excep:
                if retry > 9:
                    self.log.exception("Failed to connect to mail server with [%s] "
                                       "exception", str(excep))
                    self.mail_box = None
                    raise Exception("Couldn't connect to Mail server %s with error [%s]" %
                                    (self.mail_server, excep))
                self.log.info("connect to mail server failed, wait for 60 seconds before retry")
                sleep(60)
                self.log.info("[%s] Retrying to connect to mail server [%s]", str(retry),
                              self.mail_server)

    def disconnect(self):
        """ Close the connection created to the IMAP server """
        if self.mail_box is not None:
            self._select_folder('INBOX') # close will fail if no folders selected
            self.mail_box.close()
            self.mail_box.logout()
            self.log.info('Disconnected to mail server %s', self.mail_server)

    def _select_folder(self, folder_name):
        """
        Select a particular folder on the mailbox

        Raises:
            Exception:
                when the folder name is invalid
        """
        result, message = self.mail_box.select(folder_name)
        if result != 'OK':
            raise Exception(
                'Selecting folder [%s] on mailbox failed with reason [%s]' % (folder_name, message)
            )
        self.log.info('Mailbox folder changed to [%s]', folder_name)

    def download_mails(self, search_filter, download_dir, mail_folder='INBOX',
                       save_attachments=True):
        """ Downloads the mails that match the given search filter and marks the mail as read.

        Args:
            search_filter (EmailSearchFilter): filter object of search filter class

            download_dir                (str): directory path to download mails

            mail_folder                 (str): Folder to search default is 'INBOX'

            save_attachments           (bool): True downloads the attachments in a sub folder

        Raises:
            Exception:
                when no e-mails found for the given search filter
                when mail folder is invalid
        """
        self.local_dir_mail_download = download_dir
        unique_ids = self._get_mail_uid_list(search_filter, mail_folder)
        if unique_ids:
            if search_filter.get_recent_only() is True:   # parse and download latest mail alone.
                unique_ids = [max(unique_ids)]
            count = 0
            for each_id in unique_ids:
                mail = self._parse_mails(each_id.decode("utf-8"))
                if mail:
                    self._write_mail_to_disk(mail, save_attachments)
                    self._mark_mail_as_read(each_id.decode("utf-8"))
                    count += 1
            self.log.info(
                "Downloaded %s of %s mails returned by the search", count, len(unique_ids)
            )
            return True
        else:
            raise Exception('No emails found for search filter [%s]', str(search_filter))

    def get_mail_otp(self, search_query,user_name):
        """ Returns OTP from mail body
        
        Args:
             search_query (EmailSearchFilter): object of search filter to search in inbox
             user_name (str): user name for the account for which we are fetching otp

        Returns:
            otp (int): 6 digit integer otp value
        """
        uids = self._get_mail_uid_list(search_query)
        for uid in uids:
            mail = self._parse_mails(uid)
            mail_body = mail['Body'][0].decode()
            if user_name in mail_body:
                return re.findall("<br>{0}<br>".format("\d"*6), mail_body)[0].strip("<br>")

    def get_mail_links(self, search_query):
        """ Returns links from the mail body

        Args:
             search_query (EmailSearchFilter): object of search filter to search in inbox

        Returns:
            links (list): list of all the links in a mail
        """
        if not self._mail:
            uid = self._get_mail_uid_list(search_query)
            mail = self._parse_mails(uid[0])
            self._mail = mail

        mail_body = self._mail['Body'][0].decode()
        mail_doc = BeautifulSoup(mail_body, 'html.parser')
        links = {}
        for link in mail_doc.find_all('a'):
            text = link.text
            url = link["href"]
            links[text] = url

        return links

    def get_mail(self, search_query):
        """ Returns the mail """
        if not self._mail:
            uid = self._get_mail_uid_list(search_query)
            mail = self._parse_mails(uid[0])
            self._mail = mail

        return self._mail


class EmailSearchFilter:
    """
    This is used to define the search filter fields in a mail header
    By default sets the filter with unread and recent only mails that are sent from yesterday.
    use corresponding setter methods to change the filter
    """

    def __init__(self, subject):
        """
        Args:
            subject: part of the text to search for in e-mail subject
        """
        self.unread = True  # Get unread mails only
        self.subject = subject
        self.to_address = None   # e-Mail Address of the receiver of the mail.
        self.sender_name = None  # sender name
        self.recent_only = True  # Get mails which has the \Recent flag set.
        self.mail_sent_on_date = None  # Date on which the mail was sent.
        self.mail_sent_from_date = datetime.today() - timedelta(1)
        self.log = logger.get_log()

    def set_sender_name(self, sender_name):
        """sets sender name in search filter"""
        self.sender_name = sender_name

    def set_to_address(self, email_address):
        """sets to address in search filter"""
        self.to_address = email_address

    def set_subject(self, subject):
        """sets subject in search filter"""
        self.subject = subject

    def set_recent_only(self, val):
        """set latest only flag"""
        if isinstance(val, bool):
            self.recent_only = val

    def set_unread_only(self, val):
        """sets unread only flag in search filter"""
        self.unread = val

    def set_mail_sent_on(self, date, month, year):
        """
        set date on search filter to search on particular date

        Raises:
            ValueError:
                when invalid date/month/year is passed

        """
        try:
            date = datetime(int(year), int(month), int(date))
            self.mail_sent_on_date = date
        except ValueError:
            raise ValueError(
                'Invalid date given: Date: %d, Month: %d, Year: %d' % (date, month, year)
            )

    def set_mail_sent_from_date(self, date, month, year):
        """
        set date on search filter to search from particular date

        Raises:
            ValueError:
                when invalid date/month/year is passed

        """
        try:
            _date = datetime(int(year), int(month), int(date))
            self.mail_sent_from_date = _date
        except ValueError:
            raise ValueError(
                'Invalid date given: Date: %d, Month: %d, Year: %d' % (date, month, year)
            )

    def get_sender_name(self):
        """gets sender name set in search filter"""
        return self.sender_name

    def get_to_address(self):
        """gets to address set in search filter"""
        return self.to_address

    def get_subject(self):
        """gets subject set in search filter"""
        return self.subject

    def get_recent_only(self):
        """gets recent only flag value set in search filter"""
        return self.recent_only

    def get_mail_sent_on(self):
        """gets mail sent on date set in search filter"""
        return self.mail_sent_on_date

    def get_mail_sent_from_date(self):
        """gets mail sent from date set in search filter"""
        return self.mail_sent_from_date

    def get_unread_only(self):
        """gets unread only flag set in search filter"""
        return self.unread

    def return_search_query_string(self):
        """returns the search query string in required format to search emails"""
        self.log.info('Generating Search query for mails')
        search_filter = dict()
        search_string_list = []
        if self.sender_name is not None:
            search_filter['FROM'] = self.sender_name
        if self.to_address is not None:
            search_filter['TO'] = self.to_address
        if self.subject is not None:
            search_filter['SUBJECT'] = self.subject
        if self.unread is True:
            search_filter['NOT'] = 'SEEN'
        if isinstance(self.mail_sent_on_date, datetime):
            search_filter['ON'] = self.mail_sent_on_date.strftime("%d-%b-%Y")
        elif isinstance(self.mail_sent_from_date, datetime):
            search_filter['SINCE'] = self.mail_sent_from_date.strftime("%d-%b-%Y")
        elif self.recent_only is True:
            search_filter['NOT'] = 'OLD'

        for key, value in search_filter.items():
            search_string_list.append(str(key) + ' "' + str(value) + '"')
        search_string = "(" + " ".join(search_string_list) + ")"
        self.log.info('Search query created: ' + search_string)
        return search_string
