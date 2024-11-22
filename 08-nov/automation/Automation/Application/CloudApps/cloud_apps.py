# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main Module for invoking cloud APIs.

GAdmin, GMail, GDrive are the classes defined in this file.

GAdmin: Class for performing GSuite Admin operations like getting user list,
        modifying user properties etc.

GMail: Class for performing all gmail related operations.

GDrive: Class for performing all GDrive related operations.

GAdmin:
        __init__(cloud_object)  --  Initializes the GAdmin object

        __repr__()  --  Representation string for the instance of the GAdmin class

        __get_users()   --  Gets the list of users by calling GSuite Directory API

Attributes
==========

        **users**   --  Returns the user smtp address list from GSuite account

GMail:
        __init__(cloud_object)  --  Initializes the GMail object

        __repr__()  --  Representation string for the instance of GMail class

        _get_messages_prop()    --  Gets the message property of all the messages in the mailbox of a user

        get_labels()    --  Fetches the list of labels for a GMail user

        get_messages_prop() --  Gets message properties for user mailbox and stores it in TinyDB file

        delete_messages()   --  Deletes specific messages inside user's mailbox

        append_message()    --  Appends a message into the user's mailbox based on mail_insertion_type setting

        _create_message()   --  Creates a MIME message by fetching a random page from wikipedia

        _select_random_sender() --  Selects the random sender from available Google users

         compare_msg_props()    --  Compares message properties

GDrive:
        __init__(cloud_object)  --  Initializes the GDrive object

        __repr__()  --  Representation string for the instance of GDrive class

        create_files()  --  This method creates and upload files on user's GDrive

        files_op()  --  Method to perform various operations on user's GDRive

"""


from __future__ import unicode_literals
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from email.header import Header
import mimetypes
import base64
from random import randrange
import io
import hashlib
import uuid
import re
import time
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from AutomationUtils.machine import Machine
from . import constants
from .wiki import Wiki
from .exception import CVCloudException


class GAdmin(object):
    """Class for performing admin level operation for GSuite account."""

    def __init__(self, cc_object):
        """Initializes the GAdmin object.

                Args:

                    cc_object  (Object)  --  instance of CloudConnector class

                Returns:

                    object  --  instance of GAdmin class
        """

        self.log = cc_object.log
        self.api_name = self.__class__.__name__
        self.admin_api = 'GAdmin'

        self.log.info('auth object assigned')
        self.auth_object = cc_object.auth

        self.log.info('got mail users in constructor')
        self._mail_users = self.__get_users()

    def __repr__(self):
        """Representation string for the instance of the GAdmin class."""

        return 'Google Admin class instance for GSuite Admin API version: %s' % \
               constants.GOOGLE_API_DICT.get(self.admin_api)[1]

    def __get_users(self, domain_search=True):
        """Gets the list of users by calling GSuite Directory API.

                Returns:

                    list    --  A list containing email id of all users
        """
        try:

            self.admin_service = self.auth_object.build_service(self.admin_api)
            result = self.admin_service.users().get(
                userKey=constants.ADMIN_EMAIL).execute()
            user_list = []
            # if 'customerId' in result:
            if not domain_search:
                self.log.info(
                    'customerId of the GSuite account: %s', result['customerId'])
                customer_id = result['customerId']
                results = self.admin_service.users().list(
                    customer=customer_id,
                    maxResults=constants.USER_SEARCH_MAX_COUNT).execute()
                for user in results['users']:
                    user_list.append(user['primaryEmail'])

                while 'nextPageToken' in results:
                    page_token = results['nextPageToken']
                    results = self.admin_service.users().list(
                        customer=customer_id,
                        pageToken=page_token,
                        maxResults=constants.USER_SEARCH_MAX_COUNT).execute()
                    for user in results['users']:
                        user_list.append(user['primaryEmail'])
            else:
                self.log.info(
                    'Customer ID not found. Will do a domain search on domain: %s',
                    constants.ADMIN_EMAIL.split('@')[1])
                results = self.admin_service.users().list(
                    domain=constants.ADMIN_EMAIL.split('@')[1],
                    maxResults=constants.USER_SEARCH_MAX_COUNT).execute()
                for user in results['users']:
                    user_list.append(user['primaryEmail'])
                while 'nextPageToken' in results:
                    page_token = results['nextPageToken']
                    results = self.admin_service.users().list(
                        domain=constants.ADMIN_EMAIL.split('@')[1],
                        pageToken=page_token,
                        maxResults=constants.USER_SEARCH_MAX_COUNT).execute()
                    for user in results['users']:
                        user_list.append(user['primaryEmail'])

            if not user_list:
                raise CVCloudException(self.admin_api, '101')

        except Exception as excp:
            self.log.exception(
                'Exception while fetching user list from Google')
            raise CVCloudException(self.admin_api, '102', str(excp))
        self.log.info('Total no of users found: %s', len(user_list))
        return user_list

    @property
    def users(self):
        """Returns the user smtp address list from GSuite account"""
        return self._mail_users


class GMail(object):
    """Class for performing GMail related operations."""

    def __init__(self, cc_object):
        """Initializes the GMail object.

                Args:

                    cc_object  (Object)  --  instance of cloud_connector module

                Returns:

                    object  --  instance of GMail class
        """
        self.tc_object = cc_object.tc_object
        self.log = self.tc_object.log
        self.api_name = self.__class__.__name__
        self.auth_object = cc_object.auth
        self.dbo = cc_object.dbo
        self.wiki = Wiki(self.log)
        self.mail_users = cc_object.gadmin.users

    def __repr__(self):
        """Representation string for the instance of GMail class."""
        return 'GMail operation class instance for GMail API version: %s' % \
               constants.GOOGLE_API_DICT.get(self.api_name)[1]

    def _get_messages_prop(
            self,
            after_restore=False,
            label_list=None,
            google_resp_format='raw',
            oop_type=None
    ):
        """Gets the message property of all the messages in the mailbox of a user

                Args:

                    after_restore  (boolean)  --  True if properties are fetched after restore job

                    label_list (list)  -- List of labels to fetch messages from user mailbox.

                    google_resp_format (str) -- The format to return the message in

                                                  Allowed values

                                                    - full -

                                                    - metadata -

                                                    - minimal -

                                                    - raw - With this parameter entire message payload is returned as
                                                          base64 encoded string.

                    oop_type  (str)  --  Specifies source or destination for out of place restore



                Returns:

                    Dict    --   A dict of following form:
                            {'user_id': [{message1 property dict},
                                        {message2 property dict},
                                        {message3 property dict}
                                        ]
                            }

                            Message property dict format    --   A list containing dicts for
                                                                 message properties.
                                                                 One dict per message.

                       e.g.:    [
                                    {'To':'some address','From':'some address',
                                    'Message-ID':'someid'},
                                     {'To':'some address','From':'some address',
                                     'Message-ID':'someid'},
                                      {'To':'some address','From':'some address',
                                      'Message-ID':'someid'}
                                  ]

        """
        self.log.info('Fetching message properties for the users')
        sc_content = self.tc_object.subclient.content

        table_type = constants.MESSAGES_TABLE
        if after_restore:
            table_type = constants.MESSAGES_AFTER_RES_TABLE
        if oop_type == 'source':
            table_type = constants.MESSAGES_AFTER_OOP_SOURCE
        if oop_type == 'destination':
            table_type = constants.MESSAGES_AFTER_OOP_DESTINATION

        for content in sc_content:
            user_id = content.get('SMTPAddress')

            try:
                gmail_service = self.auth_object.build_service(
                    self.api_name, delegated_user=user_id)
                response = gmail_service.users().messages().list(
                    userId=user_id, labelIds=label_list, includeSpamTrash=True).execute()

                messages = []
                archived_mails_count = 0

                if 'messages' in response:
                    messages.extend(response['messages'])
                while 'nextPageToken' in response:
                    page_token = response['nextPageToken']
                    response = gmail_service.users().messages().list(
                        userId=user_id,
                        labelIds=label_list,
                        pageToken=page_token,
                        includeSpamTrash=True).execute()
                    messages.extend(response['messages'])
                for ids in messages:

                    prop_dict = {}
                    msg = gmail_service.users().messages().get(
                        userId=user_id, id=ids['id'], format=google_resp_format).execute()

                    label_id_list = msg.get('labelIds')
                    self.log.info('Label id list: %s', label_id_list)
                    if label_id_list is None:
                        self.log.info('There is no label associated to the mail. '
                                      'This can be archived mail')
                        archived_mails_count += 1

                    elif 'SPAM' in label_id_list:
                        self.log.info('SPAM found. Skipping the message.')
                        continue
                    else:
                        matched = False
                        for label in label_id_list:
                            if label in constants.VALID_LABEL_IDS or re.match("Label_*", label):
                                matched = True
                                break
                        if not matched:
                            self.log.info('This is an archived mail')
                            archived_mails_count += 1

                    if google_resp_format == 'full':
                        headers = msg.get('payload').get('headers')
                        prop_dict['id'] = ids['id']
                        prop_dict['labelIds'] = msg.get('labelIds')
                        prop_dict['Size'] = msg.get('sizeEstimate')
                        for element in headers:
                            if element.get('name') in [
                                    'Subject', 'From', 'To', 'Date', 'Message-ID']:
                                prop_dict[
                                    element.get('name')] = element.get('value')
                        self.log.info('Saving message properties in json db')
                        self.dbo.save_into_table(user_id, prop_dict, table_type)

                    elif google_resp_format == 'raw':

                        raw_msg = base64.urlsafe_b64decode(
                            msg.get('raw')).decode('utf-8', 'ignore')
                        self.log.info('Removing illegal content from raw mail content')
                        raw_msg = raw_msg.replace('\r\t', ' ')
                        raw_msg = raw_msg.replace('\r\n\t', ' ').replace(
                            '\r\n', '\r').replace('\n', '\r')
                        raw_msg = base64.urlsafe_b64encode(raw_msg.encode('utf-8')).decode('utf-8')
                        self.log.info('Generating hash for base64 raw mail content')
                        msg_hash = hashlib.md5(raw_msg.encode('utf-8')).hexdigest()
                        self.log.info('message hash: %s', msg_hash)
                        msg['raw'] = msg_hash
                        self.log.info('Saving message properties in json db')
                        self.dbo.save_into_table(user_id, msg, table_type)
                    else:
                        self.log.exception(
                            'Google response format provided is invalid: %s', google_resp_format)
                        raise CVCloudException(self.api_name, '107')

                self.log.info(
                    'message properties got for user: "%s". '
                    'Total number of mails for Label ids: %s (excluding SPAM): "%s"',
                    user_id, label_list, self.dbo.get_length(f'{user_id}_messages'))
                if not after_restore:
                    self.log.info(
                        'Fetching label list for the user with number of messages in each label')
                    final_label_dict = self.get_labels(
                        user_id, gmail_service=gmail_service)
                    archived_mails_dict = {'name': '~ArchivedMail', 'messagesTotal': archived_mails_count}
                    final_label_dict[user_id].append(archived_mails_dict)
                    self.log.info('Archived mails count: %s', archived_mails_count)
                    self.log.info('Saving label list to json db')

                    self.dbo.save_into_table(
                        user_id, final_label_dict[user_id], constants.LABELS_TABLE)

            except Exception as google_exception:
                self.log.exception(
                    'An error occurred while fetching messages for user')
                raise google_exception

    def get_labels(self, user_id, gmail_service=None):
        """Fetches the list of labels for a GMail user

                Args:

                    user_id (str)  --  SMTP address of the user

                    gmail_service (object)  --  GMail Resource service object

                Returns:

                    A dict containing label details

        """
        if not gmail_service:
            gmail_service = self.auth_object.build_service(
                self.api_name, delegated_user=user_id)
        label_response = gmail_service.users().labels().list(userId=user_id).execute()

        label_id_list = []
        final_label_dict = {}
        for label in label_response.get('labels'):
            label_id = label.get('id')
            if label_id in constants.LABEL_IDS_TO_SKIP:
                continue
            else:
                label_get = gmail_service.users().labels().get(
                    userId=user_id, id=label_id).execute()
                label_id_list.append(label_get.copy())
        final_label_dict[user_id] = label_id_list
        self.log.info('final label dict: %s', final_label_dict)
        return final_label_dict

    def get_messages_prop(self,
                          after_restore=False,
                          label_list=None,
                          google_resp_format='raw',
                          oop=False):
        """Gets message properties for user mailbox and stores it in TinyDB file.

                Args:

                    after_restore  (boolean)  --  True if properties are fetched after restore job

                    label_list  (list)  --  List of labels to fetch from user mailbox

                    google_resp_format (str) -- The format to return the message in

                                                  Allowed values

                                                    - full -

                                                    - metadata -

                                                    - minimal -

                                                    - raw - With this parameter entire message payload is returned
                                                            as base64 encoded string.

                    oop  (boolean)  --  True if out of place restore

        """
        if oop:
            job_list = self.dbo.get_content('joblist')[0]['job_list']
            self.log.info('Job list got from db: %s', job_list)
            if len(job_list) != 3:
                self.log.exception('Invalid job list: %s', job_list)
                raise CVCloudException(self.api_name, '401')

            destination = job_list[2]
            source = job_list[1][0]

            user_id_dict = [{'SMTPAddress': source.split('\\')[2]}]
            label_list = [source.split('\\')[3]]
            self.log.info('user id dict: %s', user_id_dict)
            self.log.info('label list: %s', label_list)
            self._get_messages_prop(
                after_restore=False, label_list=label_list, oop_type='source')
            dest_user = destination.split('/')[0]
            self.log.info('destination user id: %s', dest_user)
            self.log.info('destination label list: %s',
                          [destination.split('/')[1] + '/' + label_list[0]])
            label_dict = self.get_labels(user_id=dest_user)
            label_list_temp = label_dict.get(dest_user)
            for dict1 in label_list_temp:
                if dict1.get('name') == destination.split(
                        '/')[1] + '/' + label_list[0]:
                    label_id = dict1.get('id')
            self.log.info('destination label id: %s', label_id)
            self._get_messages_prop(
                after_restore=False,
                label_list=[label_id],
                oop_type='destination',
                google_resp_format=google_resp_format)
        else:
            self._get_messages_prop(
                after_restore=after_restore,
                label_list=label_list,
                google_resp_format=google_resp_format)

    def delete_messages(self):
        """Deletes specific messages inside user's mailbox."""

        id_dict = {}
        sc_content = self.tc_object.subclient.content
        if sc_content:
            for content in sc_content:
                user_id = content.get('SMTPAddress')
                idlist = self.dbo.get_message_id_list(user_id)
                msg_list = self.dbo.get_content(
                    f'{user_id} {constants.MESSAGES_AFTER_OOP_DESTINATION}')
                if msg_list:
                    for msg in msg_list:
                        idlist.append(msg['id'])
                id_dict['user_id'] = user_id
                id_dict['ids'] = idlist

                self.log.info(
                    'following messages will be deleted: %s', id_dict)
                if not id_dict['ids']:
                    self.log.info('there is nothing to delete.')
                else:
                    try:
                        gmail_service = self.auth_object.build_service(
                            self.api_name, delegated_user=user_id)
                        gmail_service.users().messages().batchDelete(
                            userId=user_id, body=id_dict).execute()

                        self.log.info(
                            'specified messages have been deleted '
                            'from user mailbox: %s', user_id)
                    except Exception as excp:
                        self.log.exception(
                            'Exception while deleting messages from GMail')
                        raise CVCloudException(self.api_name, '201', str(excp))

    def append_message(
            self,
            unicode_data=False,
            no_of_mails=constants.NO_OF_MAILS_TO_CREATE,
            mail_insertion_type='APPEND'
    ):
        """Appends a message into the user's mailbox based on mail_insertion_type setting.
           Message body is created by fetching random wiki page.
           Please refer to Args for more details

                Args:

                    sc_content (list) -- Subclient content list. This can be obtained by
                    get_sc_content method of commvault class

                    unicode_data (Boolean) -- If True, unicode mails will be created.

                    no_of_mails (int) -- Number of mails to create in each mail account.

                    mail_insertion_type (str): Whether to import or append message.

                        Allowed values:

                            APPEND: Directly inserts a message into only this user's mailbox similar to IMAP APPEND,
                                    bypassing most scanning and classification. Does not send a message.

                            IMPORT: Imports a message into only this user's mailbox, with standard email delivery
                                    scanning and classification similar to receiving via SMTP. Does not send a message

                            SEND: Sends the message to random sender

        """
        sc_content = self.tc_object.subclient.content
        self.log.info('subclient content: %s', sc_content)
        if sc_content:
            for content in sc_content:
                user_id = content.get('SMTPAddress')
                try:

                    self.log.info('Creating documents for attachment')
                    self.wiki.create_docx(
                        unicode_data=unicode_data,
                        pdf=True,
                        google_docs=True,
                        ca_type='gmail')
                    self.log.info(
                        'inserting message into user mailbox: "%s"', user_id)

                    gmail_service = self.auth_object.build_service(
                        self.api_name, delegated_user=user_id)
                    for i in range(no_of_mails):
                        sender = self._select_random_sender()
                        if sender.lower() == user_id.lower():
                            sender = self._select_random_sender()
                        self.log.info(
                            'mail insertion type: %s', mail_insertion_type)

                        if mail_insertion_type.upper() == 'APPEND':
                            message = self._create_message(
                                sender, user_id, unicode_data, mail_insertion_type)

                            imported_message = gmail_service.users().messages().insert(
                                userId='me', body=message).execute()
                        elif mail_insertion_type.upper() == 'IMPORT':
                            message = self._create_message(
                                sender, user_id, unicode_data, mail_insertion_type)
                            self.log.info('base64 encoded: %s', message)
                            imported_message = gmail_service.users().messages().import_(
                                userId='me', body=message).execute()
                        elif mail_insertion_type.upper() == 'SEND':
                            message = self._create_message(
                                user_id, sender, unicode_data, mail_insertion_type)
                            imported_message = gmail_service.users().messages().send(
                                userId='me', body=message).execute()
                        else:
                            self.log.info(
                                'mail insertion type: %s', mail_insertion_type)
                            self.log.exception(
                                'Invalid mail insertion type provided.')
                            raise CVCloudException(self.api_name, '108')
                        self.log.info(
                            u'Following message has been appended into user mailbox: %s', user_id)
                        self.log.info(u'%s', imported_message)
                except Exception as excp:
                    self.log.exception(
                        'Exception while inserting message into user mailbox')
                    raise CVCloudException(self.api_name, '102', str(excp))
        else:
            raise CVCloudException(self.api_name, '101')

    def _create_message(self, sender, to, unicode_data, mail_insertion_type):
        """Creates a MIME message by fetching a random page from wikipedia

                Args:

                    sender (str) -- sender's email id

                    to (str) -- recipient's email id

                    unicode_data (boolean) -- set it true to create mails with unicode data

                    mail_insertion_type (str)  --  Type of mail insertion to Google

                                                    Allowed Values:
                                                        - APPEND
                                                        - IMPORT
                                                        - SEND

                Returns:

                    dict of following form: {'raw': base64 encoded MIME message, 'labelIds': [labels to apply]}

        """
        try:
            self.log.info('Fetching random message from wiki')
            wiki = Wiki(self.log)
            wiki_message = wiki.create_message_from_wiki(unicode_data)
            self.log.info(
                'message content got from wiki. Creating MIME object now.')

            message = MIMEMultipart()
            message['To'] = to
            message['From'] = sender
            message['Subject'] = Header(wiki_message['subject'], 'UTF-8')

            body = MIMEText(wiki_message['body'], 'plain', 'UTF-8')

            message.attach(body)
            # Creating attachments for GMail
            if os.path.exists(constants.GMAIL_DOCUMENT_DIRECTORY):
                self.log.info('attachment directory exists for GMail. Uploading attachments')

                for filename in os.listdir(constants.GMAIL_DOCUMENT_DIRECTORY):
                    path = os.path.join(constants.GMAIL_DOCUMENT_DIRECTORY, filename)
                    if not os.path.isfile(path):
                        continue

                    # Guess the content type based on the file's extension.  Encoding
                    # will be ignored, although we should check for simple things like
                    # gzip'd or compressed files.

                    content_type, encoding = mimetypes.guess_type(path)
                    if content_type is None or encoding is not None:
                        content_type = 'application/octet-stream'
                    main_type, sub_type = content_type.split('/', 1)

                    if main_type == 'text':
                        fp = open(path, 'r', encoding="utf8")
                        msg = MIMEText(fp.read(), _subtype=sub_type)
                        fp.close()
                    elif main_type == 'image':
                        fp = open(path, 'rb')
                        msg = MIMEImage(fp.read(), _subtype=sub_type)
                        fp.close()
                    elif main_type == 'audio':
                        fp = open(path, 'rb')
                        msg = MIMEAudio(fp.read(), _subtype=sub_type)
                        fp.close()
                    else:
                        fp = open(path, 'rb')
                        msg = MIMEBase(main_type, sub_type)
                        msg.set_payload(fp.read())
                        fp.close()

                    encoders.encode_base64(msg)
                    msg.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=filename)

                    message.attach(msg)
            raw = base64.urlsafe_b64encode(message.as_bytes())
            raw = raw.decode()
            self.log.info('MIME object created successfully')

            if mail_insertion_type == 'APPEND' or mail_insertion_type == 'IMPORT':
                return {
                    'raw': raw,
                    'labelIds': [
                        'INBOX',
                        'UNREAD']}
            elif mail_insertion_type == 'SEND':
                return {
                    'raw': raw
                }
            else:
                self.log.exception('Invalid mail insertion type')
                raise CVCloudException(self.api_name, '108')

        except Exception as excp:
            self.log.exception('Exception while creating MIME object')
            raise CVCloudException(self.api_name, '103', str(excp))

    def _select_random_sender(self):
        """Selects the random sender from available Google users to be added in From field while creating a MIME mail

                Returns:

                    Str  --  A random user's SMTP Address

        """
        random_number = randrange(len(self.mail_users))
        self.log.info(
            'setting sender mail id: %s', self.mail_users[random_number])
        return self.mail_users[random_number]

    def compare_msg_props(
            self,
            oop=False):
        """Compares message properties.

                Args:

                    oop  (boolean)  -- True if the restore is out of place restore

                                        Default: False

                Returns:

                    True on success

        """
        self.log.info('Comparing message properties after restore')

        key_match = True
        len_match = True
        sc_content = self.tc_object.subclient.content
        if sc_content:
            for content in sc_content:
                user_id = content.get('SMTPAddress')
                table1_size = self.dbo.get_length(f'{user_id}{constants.MESSAGES_TABLE}')
                table2_size = self.dbo.get_length(f'{user_id}{constants.MESSAGES_AFTER_RES_TABLE}')
                self.log.info(
                    'Length of first table: %s and Length of second table: %s: ',
                    table1_size, table2_size)
                if table1_size != table2_size:
                    len_match = False
                    break
                else:
                    if oop:
                        table1 = f'{user_id}{constants.MESSAGES_AFTER_OOP_SOURCE}'
                        table2 = f'{user_id}{constants.MESSAGES_AFTER_OOP_DESTINATION}'
                    else:
                        table1 = f'{user_id}{constants.MESSAGES_TABLE}'
                        table2 = f'{user_id}{constants.MESSAGES_AFTER_RES_TABLE}'
                    msg_list = self.dbo.get_content(table1)
                    msg_list_after_res = self.dbo.get_content(table2)
                    self.log.info('msg list: %s', msg_list)
                    self.log.info('msg list after restore : %s', msg_list_after_res)

                    for msg1 in msg_list:
                        matched = False

                        for msg2 in msg_list_after_res:
                            self.log.info(
                                'raw of msg1: %s, type %s',
                                msg1.get('raw'), type(msg1.get('raw')))
                            self.log.info(
                                'raw of msg2: %s, type %s',
                                msg2.get('raw'), type(msg2.get('raw')))

                            if msg1.get('raw') == msg2.get('raw'):
                                if msg1.get('sizeEstimate') == msg2.get(
                                        'sizeEstimate'):
                                    self.log.info('sizeEstimate match successful')
                                else:
                                    self.log.warning(
                                        'Size is not matching but this can be becasue of removing illegal characters from the mail.')
                                if oop:
                                    self.log.info(
                                        'This is oop restore so skipping label id match.')
                                    matched = True
                                    break
                                else:
                                    if msg1.get('labelIds') == msg2.get(
                                            'labelIds'):
                                        self.log.info('labelIds match successful')
                                        matched = True
                                        break
                                    else:
                                        self.log.exception(
                                            'labelIds are not matching: %s and %s',
                                            msg1.get('labelIds'), msg2.get('labelIds'))
                                        raise CVCloudException(
                                            self.api_name, '104')

                        if not matched:
                            self.log.exception(
                                'Message property comparison failed for raw format for restored message: %s', msg2)
                            raise CVCloudException(self.api_name, '104')
        if not key_match:
            self.log.exception('email id is not present in restore dict')
            raise CVCloudException(self.api_name, '105')

        elif not len_match:
            self.log.exception(
                'Number of messages in the mailbox are different after restore. '
                'Before backup number of messages: %s and after restore number of messages: %s for user mailbox: %s',
                table1_size, table2_size, user_id)
            raise CVCloudException(self.api_name, '301')
        self.log.info(
            'raw properties, size estimates and label Ids are matching.')


class GDrive(object):
    """Class for performing GDrive related operations."""

    def __init__(self, cc_object):
        """Initializes the GDrive object.

                Args:

                    cc_object  (Object)  --  instance of cloud_connector module


                Returns:

                    object  --  instance of GDrive class

        """

        self.tc_object = cc_object.tc_object
        self.log = self.tc_object.log
        self.api_name = self.__class__.__name__
        self.auth_object = cc_object.auth
        self.mail_users = cc_object.gadmin.users
        self.dbo = cc_object.dbo
        self.wiki = Wiki(self.log)
        self.machine = Machine()

    def __repr__(self):
        """Representation string for the instance of GDrive class."""
        return 'GDrive operation class instance for GDrive API version: %s' % \
            constants.GOOGLE_API_DICT.get(self.api_name)[1]

    def create_files(
            self,
            unicode_data=False,
            no_of_docs=constants.NO_OF_DOCS_TO_CREATE,
            pdf=False,
            google_docs=False,
            new_folder=True,
            attempt=''):
        """This method creates and upload files on user's GDrive

                Args:

                    unicode_data  (boolean)  --  True if unicode data files have to be created

                    no_of_docs  (int)  --  Number of files to create and upload

                    pdf  (boolean)  --  True if pdf files have to be created

                    google_docs  (boolean)  --  True if Google Docs have to be created

                    new_folder  (boolean)  --  True if a new folder has to be created on user's GDrive

                    attempt (str)   --  Attempt to document creation

        """
        sc_content = self.tc_object.subclient.content
        if sc_content:
            for content in sc_content:
                user_id = content.get('SMTPAddress')
                self.wiki.create_docx(
                    no_of_docs=no_of_docs,
                    unicode_data=unicode_data,
                    pdf=pdf,
                    google_docs=google_docs,
                    ca_type='gdrive')
                try:
                    self.log.info(
                        'creating documents into users GDrive: "%s"', user_id)

                    gdrive_service = self.auth_object.build_service(
                        self.api_name, delegated_user=user_id)

                    if not new_folder:
                        self.log.info('Files will be uploaded to existing folder')

                        request = gdrive_service.files().list(
                            q=f"name = '{constants.GDRIVE_FOLDER}' and mimeType = 'application/vnd.google-apps.folder'").execute()
                        folder = {'id': request.get('files')[0]['id']}

                    else:

                        self.log.info('Creating a new folder on GDrive')
                        folder_CVID = str(uuid.uuid4())
                        file_metadata = {
                            'name': constants.GDRIVE_FOLDER,
                            'mimeType': 'application/vnd.google-apps.folder',
                            'properties': {'CVID': folder_CVID}
                        }
                        folder = gdrive_service.files().create(body=file_metadata).execute()

                        self.log.info('folder created on GDrive: %s', folder)
                    self.log.info('Now creating files inside the folder')

                    count = 0

                    # Walk the tree.
                    for root, directories, files in os.walk(
                            str(constants.GDRIVE_DOCUMENT_DIRECTORY)):
                        for filename in files:
                            # Join the two strings in order to form the full filepath.
                            file_path = os.path.join(root, filename)
                            self.log.info('uploading file: %s', file_path)
                            file_name = file_path.split('\\')[-1]
                            self.log.info('filename: %s', file_name)

                            media_body = MediaFileUpload(file_path, resumable=True)

                            body = {
                                'name': file_name,
                                'description': 'Uploaded by script',
                                'parents': [
                                    folder.get('id')
                                ]
                            }
                            try:
                                if file_name.split('.')[1] == 'txt':
                                    file_name = file_name.split('.')[0]
                                    body['name'] = file_name.split('.')[0]
                                    body['mimeType'] = 'application/vnd.google-apps.document'
                            except BaseException:
                                continue
                            time_out = 0
                            request = {}
                            while time_out <= 3:
                                try:
                                    request = gdrive_service.files().create(
                                        body=body, media_body=media_body,
                                        fields='name,parents,id,properties,md5Checksum,mimeType').execute()
                                    self.log.info('File uploaded successfully')
                                    count += 1
                                    break
                                except HttpError as err:
                                    # If the error is a rate limit, connection error or backend error,
                                    # wait and try again.
                                    time_out += 1

                                    if err.resp.status in [400, 403, 429, 500, 502]:
                                        self.log.info(
                                            'HTTPError %s got from Google Server. '
                                            'Waiting for few seconds before checking the status', err.resp.status)
                                        time.sleep(time_out * 10)
                                        # This is backend error from Google so we need the check whether the entity exists
                                        # If the entity exists, get the details and save into local db.
                                        # Retry if the entity doesn't exist
                                        request_file = gdrive_service.files().list(
                                            q=f"name = '{body['name']}' and '{folder['id']}' in parents").execute()
                                        if not request_file['files']:
                                            self.log.info(
                                                'file was not found on Gdrive. Uploading again. '
                                                'This is attempt: %s', time_out)
                                            if time_out == 3:
                                                self.log.info(
                                                    'Time out attempt exceeded (3 times) for this file. '
                                                    'Uploading next file.')
                                            continue
                                        else:
                                            self.log.info(
                                                'file was uploaded. '
                                                'Fetching the details and storing in local db')
                                            request = gdrive_service.files().get(
                                                fileId=request_file['files'][0]['id'],
                                                fields='name,parents,id,properties,md5Checksum,mimeType').execute()
                                            count += 1
                                            break
                                    else:
                                        raise
                            del media_body

                        data = {'no_of_docs': count, 'attempt': attempt}

                        self.dbo.save_into_table(
                            user_id, data, data_type=constants.GDRIVE_CREATED_TABLE)

                except Exception as excp:
                    self.log.exception(
                        'Exception while creating files in user GDrive')
                    raise CVCloudException(self.api_name, '101', str(excp))

    def delete_folder(self):
        """
        Method to delete the folder on GDrive which was created via Automation
        Folder id is fetched from local DB file.

        """
        sc_content = self.tc_object.subclient.content
        try:
            for content in sc_content:
                user_id = content.get('SMTPAddress')

                self.delete_single_folder(user_id)

        except Exception as excp:
            self.log.exception('Exception in delete_folder operation on GDrive')
            raise CVCloudException(self.api_name, '107', str(excp))

    def delete_single_folder(self, user_id):
        """Method to delete automation folder from specified user's GDrive

                Args:

                    user_id  (str)  --  SMTP address of the user

        """
        try:
            db_content = self.dbo.get_content(f'{user_id}{constants.GDRIVE_TABLE}')
            if db_content:
                folder_id = db_content[0]['parents'][0]
            else:
                folder_id = ''
            self.log.info('folder id: %s', folder_id)

            gdrive_service = self.auth_object.build_service(
                self.api_name, delegated_user=user_id)
            self.log.info('Deleting the folder: %s', folder_id)
            try:
                gdrive_service.files().delete(fileId=folder_id).execute()
                self.log.info('GDrive folder deleted successfully')
            except HttpError as err:
                if err.resp.status == 404:
                    self.log.info('Folder not found on GDrive')
        except Exception as excp:
            self.log.exception('Exception while deleting single folder from user GDrive')
            raise CVCloudException(self.api_name, '107', str(excp))

    def download_files(self, user=None):
        """
        Method to download all the files from GDrive Automation folder.
        Folder id is fetched from local DB file.

            Args:

                user    (str)   --  SMTP Address of the user

        """
        if user:
            sc_content = [{'SMTPAddress': user}]
        else:
            sc_content = self.tc_object.subclient.content
        try:
            for content in sc_content:
                user_id = content.get('SMTPAddress')

                db_content = self.dbo.get_content(f'{user_id}{constants.GDRIVE_TABLE}')
                if db_content:
                    folder_id = db_content[0]['parents'][0]
                else:
                    folder_id = ''
                self.log.info('folder id: %s', folder_id)

                gdrive_service = self.auth_object.build_service(
                    self.api_name, delegated_user=user_id)
                download_directory = os.path.join(constants.DOWNLOAD_DIRECTORY, user_id)
                if not os.path.exists(download_directory):
                    os.makedirs(download_directory)
                self.log.info('Downloading the files')

                for files in db_content:
                    self.log.info('file: %s', files)
                    self.download_single_file(
                        gdrive_service=gdrive_service,
                        file_id=files.get('id'),
                        file_name=files.get('name'),
                        mime_type=files['mimeType'],
                        download_directory=download_directory
                    )

        except Exception as excp:
            self.log.exception('Exception in download_files operation on GDrive')
            raise CVCloudException(self.api_name, '108', str(excp))

    def compare_file_properties(self, oop=False, to_disk=False):
        """
        Method to compare file properties before backup and after restore.

            Args:

                oop (bool)  --  True if restore is out of place

                to_disk (bool)  --  True if restore is to disk
                Note: This paramether works only if oop is set to True

        """
        sc_content = self.tc_object.subclient.content
        try:
            if not oop:
                for content in sc_content:
                    user_id = content.get('SMTPAddress')

                    self._compare_files(user_id=user_id)
            else:
                if to_disk:
                    # This is OOP restore to disk
                    job_list = self.dbo.get_content('job_list_disk')[0]['job_list']
                    user_id = job_list[3]
                    self.download_files(user=user_id)
                    source_path = os.path.join(constants.DOWNLOAD_DIRECTORY, user_id)
                    destination_path = constants.DESTINATION_TO_DISK_AFTER_RESTORE % (
                        constants.DESTINATION_TO_DISK,
                        user_id,
                        constants.GDRIVE_FOLDER)
                    self.log.info('destination path on proxy client: %s', destination_path)
                    proxy_client = Machine(
                        self.tc_object.instance.proxy_client,
                        self.tc_object.commcell)

                    diff = self.machine.compare_folders(destination_machine=proxy_client,
                                                        source_path=source_path,
                                                        destination_path=destination_path)

                    if diff:
                        self.log.error(
                            'Following files are not matching after restore, '
                            'These are google docs files so skipping for now: %s', diff)

                        # raise CVCloudException(self.api_name, '114')
                    self.log.info('File hashes are matching after disk restore')
                    proxy_client.remove_directory(destination_path)
                else:
                    # This is OOP to other user account
                    job_list = self.dbo.get_content('job_list_oop')[0]['job_list']
                    user_id = job_list[2]
                    self.get_file_properties(user=user_id)
                    self._compare_files(user_id=user_id)

        except Exception as excp:
            self.log.exception('Exception in compare_files operation on GDrive')
            raise CVCloudException(self.api_name, '109', str(excp))

    def get_file_properties(self, user=None):
        """
        Method to fetch file properties from GDrive Automation folder and store them to local DB

            Args:

                user    (str)   --  SMTP Address of the user

        """

        if user:
            sc_content = [{'SMTPAddress': user}]
        else:
            sc_content = self.tc_object.subclient.content

        try:
            for content in sc_content:
                user_id = content.get('SMTPAddress')

                db_content = self.dbo.get_content(f'{user_id}{constants.GDRIVE_TABLE}')
                if db_content:
                    folder_id = db_content[0]['parents'][0]
                else:
                    folder_id = ''
                self.log.info('folder id: %s', folder_id)

                gdrive_service = self.auth_object.build_service(
                    self.api_name, delegated_user=user_id)

                self.log.info('purging the table before fetching current properties')
                self.dbo.dbo.purge_table(f'{user_id}{constants.GDRIVE_TABLE}')
                request = gdrive_service.files().list(
                    q=f"name = '{constants.GDRIVE_FOLDER}' and mimeType = 'application/vnd.google-apps.folder'").execute()
                self.log.info('request json: %s', request)
                parent_id = request.get('files')[0]['id']

                request = gdrive_service.files().list(
                    q=f"'{parent_id}' in parents").execute()
                files_list = request['files']
                while 'nextPageToken' in request:
                    page_token = request['nextPageToken']
                    request = gdrive_service.files().list(
                        q=f"'{parent_id}' in parents", pageToken=page_token).execute()
                    files_list.extend(request['files'])
                for file_metadata in files_list:
                    file_json = gdrive_service.files().get(
                        fileId=file_metadata['id'],
                        fields='name,parents,id,properties,md5Checksum,mimeType').execute()
                    # if mime type is google docs, get the hash value here and store it in local db
                    if re.match(
                            "application/vnd.google-apps.*",
                            file_metadata['mimeType']):
                        hsh = self.download_single_file(gdrive_service=gdrive_service,
                                                        file_id=file_metadata['id'],
                                                        file_name=file_metadata['name'],
                                                        mime_type=file_metadata['mimeType'],
                                                        get_hash=True)

                        file_json['md5Checksum'] = hsh
                    self.log.info('saving file json to db: %s', file_json)
                    self.dbo.save_into_table(
                        user_id, file_json, data_type=constants.GDRIVE_TABLE)
        except Exception as excp:
            self.log.exception('Exception in get_file_properties operation on GDrive')
            raise CVCloudException(self.api_name, '110', str(excp))

    def delete_files(self):
        """
        Method to delete all the files inside Automation folder

        """

        sc_content = self.tc_object.subclient.content
        try:
            for content in sc_content:
                user_id = content.get('SMTPAddress')

                db_content = self.dbo.get_content(f'{user_id}{constants.GDRIVE_TABLE}')
                if db_content:
                    folder_id = db_content[0]['parents'][0]
                else:
                    folder_id = ''
                self.log.info('folder id: %s', folder_id)

                gdrive_service = self.auth_object.build_service(
                    self.api_name, delegated_user=user_id)

                self.log.info('deleting files inside the folder')
                try:
                    request = gdrive_service.files().list(
                        q=f"'{folder_id}' in parents").execute()
                    files_list = request['files']

                    while 'nextPageToken' in request:
                        page_token = request['nextPageToken']
                        request = gdrive_service.files().list(
                            q=f"'{folder_id}' in parents", pageToken=page_token).execute()
                        files_list.extend(request['files'])
                    if not files_list:
                        self.log.error(
                            'There is no file in the folder for user: %s', user_id)
                        continue
                    for file_metadata in files_list:
                        self.log.info('deleting individual file')
                        gdrive_service.files().delete(fileId=file_metadata['id']).execute()
                        self.log.info(
                            'fileId deleted from GDrive folder: %s', file_metadata['id'])
                except HttpError as err:
                    if err.resp.status == 404:
                        self.log.info('Folder not found on GDrive')
                        continue
        except Exception as excp:
            self.log.exception('Exception in delete_files operation on GDrive')
            raise CVCloudException(self.api_name, '111', str(excp))

    def download_single_file(self, gdrive_service, file_id, file_name, mime_type,
                             download_directory=constants.DOWNLOAD_DIRECTORY, get_hash=False):
        """Method to download a single file from GDrive based on the file ID.
        File is downloaded in download folder defined in constants file.

                Args:

                    gdrive_service (object)  --  Instance of GDrive API Resource

                    file_id (str)  --  Google assigned ID of the file

                    file_name (str)  -- Name of the file to be downloaded

                    mime_type (str)  --  MIME type of the file

                    download_directory (str)  --  Directory name to download files into

                    get_hash (bool)  --  If true, MD5 hash is returned for the file.
                    File is deleted immediately after creating hash.

        """
        try:
            if re.match(
                    "application/vnd.google-apps.*",
                    mime_type) and mime_type != 'application/vnd.google-apps.script':
                file_request = gdrive_service.files().export_media(fileId=file_id,
                                                                   mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            elif mime_type == 'application/vnd.google-apps.script':
                file_request = gdrive_service.files().export_media(
                    fileId=file_id, mimeType='application/vnd.google-apps.script+json')
            else:
                file_request = gdrive_service.files().get_media(fileId=file_id)
            if not os.path.exists(download_directory):
                os.makedirs(download_directory)
            file_path = os.path.join(download_directory, file_name)
            self.log.info('file name on disk: %s', file_name)
            self.log.info('file path: %s', file_path)
            bytes_handle = io.BytesIO()
            downloader = MediaIoBaseDownload(bytes_handle, file_request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                self.log.info("Download %d%%.", int(status.progress() * 100))
            with open(file_path, 'wb') as file_handle:
                file_handle.write(bytes_handle.getvalue())

            if get_hash:
                # generate hash and return the value.
                # Hash matching has issues for Google docs files
                # So matching the file size in case of Google docs files

                # hsh = self.machine.get_file_hash(file_path)

                size = self.machine.get_file_size(file_path)

                try:
                    os.remove(file_path)
                except OSError:
                    pass
                return size

        except Exception as excp:
            self.log.exception('Exception occured while downloading single file')
            raise CVCloudException(self.api_name, '112', str(excp))

    def get_folder_id(self, user_id):
        """Method to get the folder id for GDrive automation folder

                Args:

                    user_id (str)  --  SMTP address of the user

                Returns:

                    folder ID (str)  --  ID of the automation folder
        """
        try:
            gdrive_service = self.auth_object.build_service(
                self.api_name, delegated_user=user_id)

            request = gdrive_service.files().list(
                q=f"name = '{constants.GDRIVE_FOLDER}' and mimeType = 'application/vnd.google-apps.folder'"
            ).execute()
            self.log.info('request json: %s', request)
            parent_id = request.get('files')[0]['id']
            return parent_id
        except Exception as excp:
            self.log.exception('Error during get folder id')
            raise CVCloudException(self.api_name, '113', str(excp))

    def _compare_files(self, user_id):
        """Method to compare files on GDrive with file metadata in local db

                Args:
                    user_id  (str)   --  SMTP address of the user

                Raises exception on comparison failure

        """

        db_content = self.dbo.get_content(f'{user_id}{constants.GDRIVE_TABLE}')
        if db_content:
            folder_id = db_content[0]['parents'][0]
        else:
            folder_id = ''
        self.log.info('folder id: %s', folder_id)

        gdrive_service = self.auth_object.build_service(
            self.api_name, delegated_user=user_id)

        request = gdrive_service.files().list(
            q=f"name = '{constants.GDRIVE_FOLDER}' and mimeType = 'application/vnd.google-apps.folder'"
        ).execute()
        self.log.info('request json: %s', request)
        parent_id = request.get('files')[0]['id']

        request = gdrive_service.files().list(
            q=f"'{parent_id}' in parents").execute()
        files_list = request['files']
        while 'nextPageToken' in request:
            page_token = request['nextPageToken']
            request = gdrive_service.files().list(
                q=f"'{parent_id}' in parents", pageToken=page_token).execute()
            files_list.extend(request['files'])
        self.log.info('compare json: %s', request)
        self.log.info('Parent ID: %s', parent_id)
        self.log.info('Number of Backed up documents: %s', len(db_content))
        self.log.info('Number of restored documents: %s', len(files_list))

        if len(db_content) != len(files_list):
            self.log.error(
                'Number of restored documents is different than the number of backed up documents.')
            raise CVCloudException(self.api_name, '106')

        for file_metadata in files_list:
            request_checksum_json = gdrive_service.files().get(
                fileId=file_metadata['id'], fields='name,md5Checksum,properties,parents').execute()

            # if mimetype is google docs, download the file and then generate hash here.
            # match it against the already stored hash in local db
            if re.match(
                    "application/vnd.google-apps.*",
                    file_metadata['mimeType']):
                hsh = self.download_single_file(gdrive_service=gdrive_service,
                                                file_id=file_metadata['id'],
                                                file_name=file_metadata['name'],
                                                mime_type=file_metadata['mimeType'],
                                                get_hash=True)

                #request_checksum_json['md5Checksum'] = hsh
                if hsh <= 0:
                    self.log.error('Something wrong with google docs file.')
                    raise CVCloudException(self.api_name, '115')
            self.log.info('md5Checksum json: %s', request_checksum_json)

            if 'md5Checksum' in request_checksum_json:
                if self.dbo.search_md5checksum(
                        request_checksum_json.get('md5Checksum'), user_id):
                    self.log.info('After restore checksum of file is matching')
                else:
                    self.log.info('Checksum did not match after restore:')
                    self.log.info('After restore: %s', request_checksum_json)
                    raise CVCloudException(self.api_name, '104')
