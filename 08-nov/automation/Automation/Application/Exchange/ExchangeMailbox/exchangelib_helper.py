# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main Module for invoking Exchange LIbrary APIs.

CVMailbox, CVFolder, CVMessage, ExchangeLib are the classes defined in this file.

CVMailbox: Class for all Exchange Mailbox Info.

CVFolder: Class for all Exchange Folder Info.

CVMessage: Class for all Exchange message properties Info.

ExchangeLib: Class for performing all Exchange Third party library operations.

"""
import os
import time
from functools import wraps
from requests.exceptions import ConnectionError, ChunkedEncodingError
import requests
from exchangelib import (IMPERSONATION, Account, Credentials, Configuration,
                         CalendarItem, Message, Task, Contact, Mailbox, FileAttachment, Folder,Version,Build)
from exchangelib.errors import ErrorServerBusy, ErrorTimeoutExpired, ErrorInternalServerError
from exchangelib.items import MeetingRequest
from exchangelib import extended_properties
from exchangelib import Configuration, OAuth2Credentials, OAUTH2, Identity
from oauthlib.oauth2 import OAuth2Token
from AutomationUtils import logger
from . import constants
from ...Office365.o365_data_gen import O365DataGenerator


class IsHidden(extended_properties.ExtendedProperty):
    """Class for IsHidden extended property"""
    property_tag = 0x10f4  # hex integer (e.g. 0x8000) or string ('0x8000')
    property_type = 'Boolean'


class SearchKey(extended_properties.ExtendedProperty):
    """Class for SearchKey extended property"""
    property_tag = 0x300B  # hex integer (e.g. 0x8000) or string ('0x8000')
    property_type = 'Binary'


class MessageClass(extended_properties.ExtendedProperty):
    """Class for MessageClass extended property"""
    property_tag = 0x001A  # hex integer (e.g. 0x8000) or string ('0x8000')
    property_type = 'String'


class CVDataHeader(extended_properties.ExtendedProperty):
    """Class for CVDataHeader extended property"""
    distinguished_property_set_id = 'PublicStrings'
    property_name = 'CVDataHeader'
    property_type = 'String'


class CVStub(extended_properties.ExtendedProperty):
    """Class for CVStub extended property"""
    distinguished_property_set_id = 'PublicStrings'
    property_name = 'CVStub'
    property_type = 'String'


class MessageSize(extended_properties.ExtendedProperty):
    """Class for MessageSize extended property"""
    property_tag = 0x0E08  # hex integer (e.g. 0x8000) or string ('0x8000')
    property_type = 'Integer'


class EntryID(extended_properties.ExtendedProperty):
    """Class for EntryID extended property"""
    # property_tag = 0x0fff  # hex integer (e.g. 0x8000) or string ('0x8000')
    property_tag = 4095
    property_type = 'Binary'


class CVMailbox(object):
    """Class for Mailbox Detail """

    def __init__(self):
        """Initializes the CVMailbox object."""
        self.folders = []
        self.mailbox_type = ""
        self.logger_location = ""


class CVFolder(object):
    """Class for Folder Detail """

    def __init__(self):
        """Initializes the CVFolder object."""
        self.folder_name = ""
        self.folder_id = ""
        self.sub_folder = []
        self.messages = []


class CVMessage(object):
    """Class for CVMessage Detail """

    def __init__(self):
        self.from_address = {}
        self.to_address = {}
        self.cc_address = {}
        self.bcc_address = {}
        self.subject = ""
        self.body = ""
        self.txt_body = ""
        self.lastmodified_time = ""
        self.lastmodified_name = ""
        self.received_time = ""
        self.importance = ""
        self.is_read = ""
        self.has_attachment = ""
        self.message_id = ""
        self.message_class = ""
        self.folder = ""
        self.attachment_details = []
        self.contact_info = []
        self.unquie_id = ""
        self.changeKey = ""
        self.cv_stub = ""
        self.search_key = ""
        self.cv_dataheader = ""
        self.message_size = ""
        self.entry_id = ""


class CVAttachment(object):
    """Class for Attachments Detail"""

    def __init__(self):
        """Initializes the CVAttachment object."""
        self.attachment_id = ""
        self.content_id = ""
        self.content_type = ""
        self.content = ""
        self.is_inline = ""
        self.name = ""
        self.size = ""
        self.lastmodified_time = ""
        self.content_location = ""
        self.is_contactphoto = ""
        self.msg_deatils = ""


class CVContact(object):
    """Class for Contacts Detail """

    def __init__(self):
        """Initializes the CVContact object."""
        self.contact_displayname = ""
        self.contact_emailaddress = ""
        self.company = ""
        self.department = ""
        self.jobtittle = ""
        self.givenname = ""


class EXMBOnlineAPICallDecorator:
    """Class for handling timeout of Salesforce API connection"""

    def __init__(self):
        """
        Constructor function for the class

        Args:

        """

        self.log = logger.get_log()
        self._max_retries = 3

    def __call__(self):
        """
        Wrapper method that checks if EWS connection has timed out or there is any EWS specific error
        and re- attempts the operation

        Returns:
            function: The wrapped function
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                for i in range(self._max_retries):
                    try:
                        return_val = func(*args, **kwargs)
                        break
                    except (ConnectionError, ChunkedEncodingError, ErrorInternalServerError) as exp:
                        self.__exp = exp
                        self.log.error(f"{exp}")
                        time.sleep(45)
                        self.log.info(f"Tried {i + 1} times out of {self._max_retries}. Retrying....")

                    except (ErrorTimeoutExpired, ErrorServerBusy) as excp:
                        self.__exp = excp
                        self.log.error(f"EWS Exception: {excp}")
                        time.sleep(45)
                        self.log.info(f"Tried {i + 1} times out of {self._max_retries}. Retrying....")
                else:
                    raise Exception(f"Exchange Lib timeout error. Tried {self._max_retries} times and failed.") \
                        from self.__exp
                return return_val

            return wrapper

        return decorator


class ExchangeLib(object):
    """Class for using Third party ExchangeLib related operations."""

    ews_api_call = EXMBOnlineAPICallDecorator()

    def __init__(self, ex_object):
        """Initializes the ExchangeLib object.

                Args:
                    ex_object  (Object)  --  instance of ExchangeMailbox module


                Returns:
                    object  --  instance of ExchangeLib class
        """
        self.tc_object = ex_object.tc_object
        self.log = self.tc_object.log
        self.app_name = self.__class__.__name__
        self.mail_users = ex_object.users
        self.server_name = ex_object.exchange_server
        self.cas_server = ex_object.exchange_cas_server

        self.exchange_type = ex_object.exchange_type
        self.mailbox_type = ex_object.mailbox_type

        if (self.exchange_type == constants.environment_types.EXCHANGE_ONPREMISE.value
                or self.mailbox_type == constants.mailbox_type.JOURNAL.name):
            self.admin_user = ex_object.service_account_user
            self.admin_pwd = ex_object.service_account_password
            from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
            BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
            user_name = self.admin_user.split("\\")
            uname = str(user_name[0] + "\\" + user_name[1])
            credentials = Credentials(username=uname, password=self.admin_pwd)
            self.config = Configuration(credentials=credentials,
                                        server=self.cas_server)
        elif self.exchange_type == constants.environment_types.EXCHANGE_ONLINE.value:
            self.admin_user = ex_object.exchange_online_user
            self.admin_pwd = ex_object.exchange_online_password
            self.client_id = ex_object.azure_app_id
            self.client_secret = ex_object.azure_app_key_secret
            self.azure_tenant_name = ex_object.azure_tenant_name
            credentials = OAuth2Credentials(client_id=self.client_id, client_secret=self.client_secret,
                                            tenant_id=self.azure_tenant_name,
                                            identity=Identity(primary_smtp_address=self.admin_user))

            self.config = Configuration(credentials=credentials, auth_type=OAUTH2,version=Version(Build(15,1,2,3)),
                                        service_endpoint='https://outlook.office365.com/EWS/exchange.asmx')

        else:
            self.admin_user = ex_object.exchange_online_user
            self.admin_pwd = ex_object.exchange_online_password
            credentials = Credentials(
                username=self.admin_user,
                password=self.admin_pwd)
            self.config = Configuration(
                credentials=credentials,
                service_endpoint='https://outlook.office365.com/EWS/exchange.asmx')
            # For Hybrid Env

        self.mailbox_prop = {}

    @ews_api_call()
    def get_mailbox_properties(self, mailbox_name, **kwargs):
        """Get properties of mailbox
            Args:
                mailbox_name(str)       --  Mailbox smtp

            Returns:
                cvmailbox (CVMailbox)   --  returns mailbox properties object

        """

        try:
            count = kwargs.get('count', 100)
            exclude_folder = kwargs.get('exclude_folder', None)
            cvmailbox = CVMailbox()
            cvmailbox.mailbox_type = self.mailbox_type
            processed_folder_list = set()
            if exclude_folder:
                processed_folder_list.update(exclude_folder)
            account = Account(
                primary_smtp_address=mailbox_name,
                config=self.config,
                access_type=IMPERSONATION)

            # Deregister the properties in case any of them are still registered
            items = [Task, Contact, Message, CalendarItem, MeetingRequest]
            fields = ['PidTagSearchKey', 'CVDataHeader', 'CVStub', 'entry_id']

            for item in items:
                for field in fields:
                    try:
                        item.deregister(field) if item.get_field_by_fieldname(field) else None
                    except:
                        pass

            Task.register('PidTagSearchKey', SearchKey)
            Task.register('CVDataHeader', CVDataHeader)
            Task.register('CVStub', CVStub)
            Task.register('entry_id', EntryID)

            Contact.register('PidTagSearchKey', SearchKey)
            Contact.register('CVDataHeader', CVDataHeader)
            Contact.register('CVStub', CVStub)
            Contact.register('entry_id', EntryID)

            Message.register('PidTagSearchKey', SearchKey)
            Message.register('CVDataHeader', CVDataHeader)
            Message.register('CVStub', CVStub)
            Message.register('entry_id', EntryID)

            CalendarItem.register('PidTagSearchKey', SearchKey)
            CalendarItem.register('CVDataHeader', CVDataHeader)
            CalendarItem.register('CVStub', CVStub)
            CalendarItem.register('entry_id', EntryID)

            MeetingRequest.register('PidTagSearchKey', SearchKey)
            MeetingRequest.register('CVDataHeader', CVDataHeader)
            MeetingRequest.register('CVStub', CVStub)
            MeetingRequest.register('entry_id', EntryID)

            folders = account.root.tois.children
            for folder in folders:
                if str(folder.absolute) in processed_folder_list:
                    continue

                cv_folder = CVFolder()
                processed_folder_list.add(str(folder.absolute))
                cv_folder.folder_name = folder.name
                if folder.all().exists():
                    try:
                        messages = folder.all().order_by('-datetime_received')[:count]
                        for message in messages:
                            cvmessage = self.collect_message_properties(message)
                            if not cvmessage:
                                continue
                            cv_folder.messages.append(cvmessage)
                    except AttributeError:
                        self.log.info("Folder {} has no messages".format(folder.name))
                    cvmailbox.folders.append(cv_folder)
                    self.log.info(
                        "Collected {} messages from {} folder".format(len(cv_folder.messages), (cv_folder.folder_name)))

            Task.deregister('PidTagSearchKey')
            Task.deregister('CVDataHeader')
            Task.deregister('CVStub')
            Task.deregister('entry_id')

            Contact.deregister('PidTagSearchKey')
            Contact.deregister('CVDataHeader')
            Contact.deregister('CVStub')
            Contact.deregister('entry_id')

            Message.deregister('PidTagSearchKey')
            Message.deregister('CVDataHeader')
            Message.deregister('CVStub')
            Message.deregister('entry_id')

            CalendarItem.deregister('PidTagSearchKey')
            CalendarItem.deregister('CVDataHeader')
            CalendarItem.deregister('CVStub')
            CalendarItem.deregister('entry_id')

            MeetingRequest.deregister('PidTagSearchKey')
            MeetingRequest.deregister('CVDataHeader')
            MeetingRequest.deregister('CVStub')
            MeetingRequest.deregister('entry_id')
            processed_folder_list.clear()
            return cvmailbox

        except Exception as excp:
            self.log.exception(
                'An error occurred while mailbox property for mailbox "{}" '.format(mailbox_name))
            raise excp

    def get_message_properties_helper(
            self, root, processed_folder_list, msg_cnt=10):
        """Helper method for get_message_properties consolidated
            Args:
                root (CVFolder)             -- CVFolder object

                processed_folder_list(set)  -- Folders processed

                msg_cnt(int)                --  Number of emails required per folder

            Returns:
                List of subfolder and its hierarchy

        """
        sub_folders = []
        if root:
            folders = root.walk()
            for folder in folders:
                if str(folder.absolute) in processed_folder_list:
                    continue
                cvfolder = CVFolder()
                processed_folder_list.add(str(folder.absolute))
                cvfolder.folder_name = folder.name
                if folder.children:
                    fldr_list = self.get_message_properties_helper(
                        folder, processed_folder_list)
                    for sub_folder in fldr_list:
                        cvfolder.sub_folder.append(sub_folder)
                self.log.info(folder)
                if folder.name == "Audits":
                    continue

                if folder.name == "Purges":
                    continue
                if folder.all().exists():
                    try:
                        for message in folder.all().order_by('-datetime_received')[:msg_cnt]:
                            cvmessage = self.collect_message_properties(message)
                            if cvmessage is None:
                                continue
                            cvfolder.messages.append(cvmessage)
                    except AttributeError:
                        print(folder.folder_name)
                self.log.info("Found: {} messages for folder: {}".format(len(cvfolder.messages), folder.name))
                sub_folders.append(cvfolder)
        return sub_folders

    def collect_message_properties(self, message):
        """Get properties of each message
            Returns:
                cvmessage (CVMessage) -- returns message properties object
        """
        if message.ELEMENT_NAME not in ['CalendarItem', 'Message', 'Contact', 'Task']:
            return None

        try:

            cvmessage = CVMessage()
            if message.ELEMENT_NAME == "Message":

                # cvmessage.message_id = message.message_id
                # self.log.info(message.id)
                # sender = {}

                cvmessage.message_id = message.id if hasattr(message, "id") else ""

                cvmessage.unquie_id = message.message_id
                if message.sender is not None:
                    # sender[message.sender.name] ={message.sender.email_address}
                    cvmessage.from_address[message.sender.name] = message.sender.email_address

                if message.to_recipients is not None:
                    for to in message.to_recipients:
                        # to_address = {}
                        # to_address[to.name] ={to.email_address}
                        cvmessage.to_address[to.name] = to.email_address

                if message.cc_recipients is not None:
                    for cc in message.cc_recipients:
                        # cc_address = {}
                        # cc_address[cc.name] ={cc.email_address}
                        cvmessage.cc_address[cc.name] = cc.email_address
                if message.bcc_recipients is not None:
                    for bcc in message.bcc_recipients:
                        # bcc_address = {}
                        # bcc_address[bcc.name] ={bcc.email_address}
                        cvmessage.bcc_address[bcc.name] = bcc.email_address

                cvmessage.is_read = message.is_read

            elif message.ELEMENT_NAME == "Contact":
                # log.info("It is a contact.. Getting the properties of contact")
                contact = CVContact()

                contact.contact_emailaddress = message.email_addresses
                contact.contact_displayname = message.display_name
                contact.company = message.company_name
                contact.givenname = message.given_name
                contact.department = message.department
                contact.jobtittle = message.job_title

                cvmessage.contact_info.append(contact)

            # itemid = message.item_id
            pid = message.PidTagSearchKey
            search_key_hex = ""
            if pid is not None:
                search_key_hex = ''.join('{:02X}'.format(b) for b in pid)

            # cvmessage.search_key = message.PidTagSearchKey
            cvmessage.search_key = search_key_hex
            cvmessage.cv_stub = message.CVStub
            cvmessage.cv_dataheader = message.CVDataHeader
            cvmessage.message_class = message.item_class
            # message.MessageClass
            cvmessage.message_size = message.size
            # message.MessageSize
            # decoded_entry_id = base64.b64decode(message.entry_id)
            # hex_val = decoded_entry_id.encode('hex').upper()
            final_entry_id = ""
            if message.entry_id is not None:
                final_entry_id = ''.join('{:02X}'.format(b)
                                         for b in message.entry_id)
            # # final_entry_id = ''.join([ "%02X" % ord(x) for x in message.entry_id]).strip()
            # entry_id = message.entry_id
            # final_entry_id = binascii.hexlify(entry_id.encode('utf8'))
            cvmessage.entry_id = final_entry_id
            # cvmessage.entry_id = message.EntryID

            # cvmessage.message_id = message.item_id
            cvmessage.txt_body = message.text_body

            cvmessage.lastmodified_time = message.last_modified_time
            cvmessage.received_time = message.datetime_received

            # cvmessage.has_attachment =message.has_attach
            cvmessage.subject = message.subject
            cvmessage.body = message.body
            cvmessage.importance = message.importance

            cvmessage.changeKey = message.changekey
            cvmessage.lastmodified_name = message.last_modified_name
            # if message.has_attachments:
            for attachment in message.attachments:
                att = CVAttachment()
                att.attachment_id = attachment.content_id
                att.content_type = attachment.content_type

                att.is_inline = attachment.is_inline
                # att.name
                # attachment.name
                # att.size
                # attachment.size
                att.lastmodified_time = attachment.last_modified_time
                att.content_location = attachment.content_location

                if attachment.ELEMENT_NAME == 'FileAttachment':
                    # if attachment.content:
                    #     att.content = attachment.content
                    # else:
                    #     log.error("Cannot open attachment")
                    att.is_contactphoto = attachment.is_contact_photo
                else:
                    msg_details = self.collect_message_properties(
                        attachment.item)
                    att.msg_deatils = msg_details
                cvmessage.attachment_details.append(att)

            return cvmessage

        except Exception as excp:
            self.log.exception(
                'An error occurred while message property for message "{}" '.format(message))
            raise excp

    def get_mailbox_prop(self, exclude_folder=None):
        """Set properties of mailboxes to dictonary assocaited to subclient
                Args:
                    exclude_folder (list)        -- List of strings of folder names to exclude
        """
        try:
            if not isinstance(self.mail_users, list):
                raise Exception("Invalid Mail Users type. Please provide List")
            for user in self.mail_users:
                success = False
                while not success:
                    try:
                        self.log.info(
                            'Getiing property for Mailbox "{0}" '.format(user))
                        cvmailbox_object = self.get_mailbox_properties(user, exclude_folder=exclude_folder)
                        self.mailbox_prop[user] = cvmailbox_object
                        success = True
                    except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as excp:
                        self.log.info("Fetching properties failed with the following exception: {}".format(excp))
                        time.sleep(60)

                    except (ErrorTimeoutExpired, ErrorServerBusy) as excp:
                        self.log.info(
                            f"Fetching properties failed as server refused connection with the following exception:"
                            f" {excp}")
                        time.sleep(45)

        except Exception as excp:
            self.log.exception(
                'An error occurred while mailbox property for mailbox')
            raise excp

    @ews_api_call()
    def delete_mailbox_content(self, mailbox_name):
        """Deletes the inbox content for mail user.
            Args:
                mailbox_name  (str)  --  Smtp address of mail user
        """
        try:
            account = Account(
                primary_smtp_address=mailbox_name,
                config=self.config,
                access_type=IMPERSONATION)

            inbox = account.inbox
            if inbox.all().exists():
                for message in inbox.all().order_by('-datetime_received')[:100]:
                    message.soft_delete()

        except Exception as excp:
            self.log.exception('An error occurred while deleting the mailbox content')
            raise excp

    def delete_item_recoverable_folder(self, mailbox_name):
        """Deletes the items from recoverable folder.
            Args:
                mailbox_name  (str)  --  Smtp address of mail user
        """
        try:
            account = Account(
                primary_smtp_address=mailbox_name,
                config=self.config,
                access_type=IMPERSONATION)
            folder = account.recoverable_items_deletions
            if folder.all().exists():
                for message in folder.all().order_by('-datetime_received')[:100]:
                    message.delete()

        except Exception as excp:
            self.log.exception('An error occurred while deleting the mailbox '
                               'content from recoverable folder')
            raise excp

    @ews_api_call()
    def modify_subject(self, mailbox_name):
        """Modify the subject of messages in inbox for mail user.
            Args:
                mailbox_name  (str)  --  Smtp address of mail user
        """
        try:
            account = Account(
                primary_smtp_address=mailbox_name,
                config=self.config,
                access_type=IMPERSONATION)
            inbox = account.inbox
            if inbox.all().exists():
                for message in inbox.all().order_by('-datetime_received')[:100]:
                    message.subject = "Test Version"
                    # message.save()
                    message.save(update_fields=['subject'])

        except Exception as excp:
            self.log.exception('An error occurred while modifying the mailbox content')
            raise excp

    def delete_items_from_cv_well_known_folders(self, mailbox_list, message_count=100):
        """Helper method to delete messages from mailbox
            Args:
                mailbox_list(dictionary)         --  Dictionary containing mailbox properties

                message_count(int)               --  Number of messages to delete

            Returns:
                true_up_entry_id(dictionary)       -- This contains the list of message entry id's
                                                    deleted

        """

        try:
            true_up_entry_id = {}
            if not isinstance(mailbox_list, list):
                raise Exception("mailboxes are not list type. Please provide list")
            for mailbox in mailbox_list:
                self.log.info('Processing Mailbox: %s' % mailbox)
                true_up_entry_id[mailbox] = []
                account = Account(
                    primary_smtp_address=mailbox,
                    config=self.config,
                    access_type=IMPERSONATION)
                mailbox_properties = self.get_mailbox_properties(mailbox, count=message_count)
                folders = mailbox_properties.folders
                for folder in folders:
                    if folder.folder_name == "Top of Information Store":
                        folders = folder.sub_folder
                for folder in folders:
                    self.log.info('Processing Folder: %s' % folder.folder_name)
                    if folder.folder_name.lower() in constants.CV_WELL_KNOWN_FOLDER_NAMES:
                        current_folder = getattr(account, folder.folder_name.lower())
                        folder_messages = folder.messages
                        for current_message in folder_messages[:message_count]:
                            message = current_folder.get(message_id=current_message.unquie_id)
                            true_up_entry_id[mailbox].append(current_message.entry_id)
                            self.log.info('Deleting Message: %s' % current_message.entry_id)
                            message.delete()
            time.sleep(30)
            return true_up_entry_id
        except Exception as excp:
            self.log.exception('An error occurred while deleting the mailbox content')
            raise excp

    @ews_api_call()
    def send_email(self, mailbox_list, primary_smtp_user=""):
        """
        Sends 10 emails to each of the email address in the mailbox list
        Arguments:
            mailbox_list    (list)  -   List of SMTP address, to be populated
                    Example: ['user1@example.com','user2@example.com']
            primary_smtp_user   (str)   - Domain Admin user email address

        NOTE:
            The function requires that the PoowerCDO folder be present on the
            Automation Controller

        """
        ROOT_PATH = constants.SEND_SCRIPT_PATH
        import random

        def get_body():
            body_dir = os.path.join(ROOT_PATH, 'Body')
            body_file = random.choice([os.path.join(body_dir, x) for x in os.listdir(
                body_dir) if os.path.isfile(os.path.join(body_dir, x))])
            print(body_file)
            file_handler = open(body_file, "r", encoding="utf-8")
            body_content = file_handler.read()
            return body_content

        def get_subject():
            subject_file = os.path.join(ROOT_PATH, "subjects.txt")
            sub_file = open(subject_file, "r", encoding="utf-8")
            subject = random.choice(sub_file.read().splitlines())
            return subject

        def get_attachments():
            attachment_dir = os.path.join(ROOT_PATH, 'Attach')
            attach_files = [
                x for x in os.listdir(attachment_dir) if os.path.isfile(
                    os.path.join(
                        attachment_dir, x))]
            attach_count = random.randint(0, len(attach_files) // 2)
            attach = list()
            for _ in range(attach_count):
                attach.append(
                    attach_files[random.randint(0, len(attach_files) - 1)])
            print(attach)
            return attach

        if primary_smtp_user == "":
            primary_smtp_user = self.admin_user

        account = Account(
            primary_smtp_address=primary_smtp_user,
            config=self.config,
            access_type=IMPERSONATION)

        ex_mailbox_list = list()
        for i in mailbox_list:
            mailbox = Mailbox(email_address=i)
            ex_mailbox_list.append(mailbox)
        for _ in range(10):
            mail_body = get_body()
            mail_subject = get_subject()

            message = Message(account=account,
                              subject=mail_subject,
                              body=mail_body,
                              to_recipients=ex_mailbox_list
                              )
            mail_attachment = get_attachments()
            for attachment in mail_attachment:
                print(attachment)
                attach_file = open(
                    os.path.join(
                        ROOT_PATH,
                        "Attach",
                        attachment),
                    "rb")
                mail_attach = FileAttachment(
                    name=attachment, content=attach_file.read())

                message.attach(mail_attach)

            message.send_and_save()
        time.sleep(60)

    @ews_api_call()
    def public_folder_item_count(
            self, public_folder_name, parent_folder_path=None, depth="shallow"):
        """
            This function returns the count of the emails in the public folder.

            Arguments:
                public_folder_name      (str)-- The name of the Public Folder
                parent_folder_path      (str)-- / separated parent folders
                depth                   (str)-- Shallow or Deep
                    Shallow: returns item counts in the folder only
                    Deep: Recursive item count in sub- folders also

            Returns:
                count                   (int)-- Number of items in the public folder

        """
        account = Account(
            primary_smtp_address=self.admin_user,
            config=self.config,
            access_type=IMPERSONATION,
            autodiscover=True)

        if parent_folder_path is None:
            public_folder = account.public_folders_root / public_folder_name
        else:
            public_folder = parent_folder_path / public_folder_name

        count = len(public_folder.all())

        if depth == "Shallow":
            return count

        child_folders = public_folder.children

        for child_folder in child_folders:
            child_name = child_folder.name
            res = self.public_folder_item_count(
                public_folder_name=child_name,
                parent_folder_path=public_folder,
                depth="Deep")
            count += res

        return count

    @ews_api_call()
    def _generate_and_send_email(self, mailbox_list, primary_smtp_user=""):
        """
        Sends 10 emails to each of the email address in the mailbox list
        Arguments:
            mailbox_list    (list)  -   List of SMTP address, to be populated
                    Example: ['user1@example.com','user2@example.com']
            primary_smtp_user   (str)   - Domain Admin user email address
        NOTE:
            The function requires that the PoowerCDO folder be present on the
            Automation Controller
        """
        import random
        o365_data_gen = O365DataGenerator(self.log)
        def get_body():
            return o365_data_gen.generate_email_message(unicode=True)["body"]
        def get_subject():
            return o365_data_gen.generate_email_message(unicode=True)["subject"]
        def get_attachments():
            attachment_dir = os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                'Attach')
            o365_data_gen.gen_file(no_of_docs=random.randint(1, 5), doc_path=attachment_dir)
            attach_files = [
                x for x in os.listdir(attachment_dir) if os.path.isfile(
                    os.path.join(
                        attachment_dir, x))]
            attach_count = random.randint(0, len(attach_files) // 2)
            attach = list()
            for _ in range(attach_count):
                attach.append(
                    attach_files[random.randint(0, len(attach_files) - 1)])
            print(attach)
            return attach
        if primary_smtp_user == "":
            primary_smtp_user = self.admin_user
        account = Account(
            primary_smtp_address=primary_smtp_user,
            config=self.config,
            access_type=IMPERSONATION)
        ex_mailbox_list = list()
        for i in mailbox_list:
            mailbox = Mailbox(email_address=i)
            ex_mailbox_list.append(mailbox)
        mail_attachment = get_attachments()
        attachment_dir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'Attach')
        for _ in range(10):
            mail_body = get_body()
            mail_subject = get_subject()
            message = Message(account=account,
                              subject=mail_subject,
                              body=mail_body,
                              to_recipients=ex_mailbox_list
                              )
            for attachment in mail_attachment:
                attach_file = open(
                    os.path.join(
                        attachment_dir,
                        attachment),
                    "rb")
                mail_attach = FileAttachment(
                    name=attachment, content=attach_file.read())
                message.attach(mail_attach)
            message.send_and_save()
        time.sleep(60)

    @ews_api_call()
    def cleanup_mailboxes(self, mailbox_list):
        """
            Helper method to cleanup contents from all the folders in the mailbox

            Args:
                mailbox_list(list)--        List of SMTP Addresses to cleanup contents of

        """
        try:
            if not isinstance(mailbox_list, list):
                raise Exception("mailboxes are not list type. Please provide list")

            for mailbox in mailbox_list:
                self.log.info('Processing Mailbox: %s' % mailbox)
                account = Account(
                    primary_smtp_address=mailbox,
                    config=self.config,
                    access_type=IMPERSONATION)
                success = False
                while not success:
                    try:
                        mailbox_properties = self.get_mailbox_properties(mailbox)
                        folders = mailbox_properties.folders
                        folders_to_be_processed = list()
                        # for folder in folders:
                        #     if folder.folder_name == "Top of Information Store":
                        #         folders_to_be_processed.extend(folder.sub_folder)
                        for folder in folders:
                            if not hasattr(account, folder.folder_name.lower()):
                                continue
                            current_folder = getattr(account, folder.folder_name.lower())
                            self.log.info("Wiping Folder: {}".format(folder.folder_name))
                            current_folder.wipe()
                        account.recoverable_items_deletions.empty()
                        success = True

                    except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as excp:
                            self.log.info("Fetching properties failed with the following exception: {}".format(excp))
                            time.sleep(60)

                    except (ErrorTimeoutExpired, ErrorServerBusy) as excp:
                        self.log.info(
                            "Fetching properties failed as server refused connection with the following exception: {}".format(
                                excp))
                        time.sleep(45)
            time.sleep(150)
        except Exception as excp:
            self.log.exception('An error occurred while performing mailbox cleanup')
            raise excp

    @ews_api_call()
    def create_mailbox_folder(self, mailbox_smtp, folder_name=None):
        """
        The following function creates a folder in the TOIS(Top of Information Store)

            mailbox_smtp(str) :- SMTP address of the mailbox in which you want to create the folder

            folder_name(str)  :- Folder name (Optional)
        """
        account = Account(
            primary_smtp_address=mailbox_smtp,
            config=self.config,
            access_type=IMPERSONATION
        )
        if folder_name is None:
            folder_name = constants.MAILBOX_FOLDER % self.tc_object.id
        self.log.info("Creating folder with the name {0} ".format(folder_name))
        TOISFolder = account.root.tois
        for folder in TOISFolder.children:
            if folder.name.lower() == folder_name.lower():
                self.log.info("Mailbox Folder exists deleting it.")
                folder.delete()
                break
        folder = Folder(parent=TOISFolder, name=folder_name)
        folder.save()

        return folder_name
