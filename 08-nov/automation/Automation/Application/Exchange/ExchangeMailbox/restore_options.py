# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
main file for validating all the options for restores

Class:
Restore - class defined for validating  all restores options
"""

import pickle
import logging
from collections import OrderedDict
from xmltodict import parse
from AutomationUtils.machine import Machine
from .constants import OpType, MBX_JOURNAL, TOP_OF_INFO_STORE
from . import utils


class Restore(object):
    """Class for performing Restore related operations."""

    def __init__(self, ex_object):
        """Initializes the Restore object.
            Args:
                ex_object  (Object)  --  instance of ExchangeMailbox module

            Returns:
                object  --  instance of ExchangeLib class
        """
        self.tc_object = ex_object.tc_object
        self.log = self.tc_object.log
        self.app_name = self.__class__.__name__
        self.mail_users = ex_object.users
        self.client_name = ex_object.client_name
        self.mailbox_type = ex_object.mailbox_type
        self.csdb = ex_object.csdb
        self.server_name = ex_object.exchange_server
        self.exchange_type = ex_object.exchange_type
        if self.exchange_type == 1:
            self.admin_user = ex_object.service_account_user
            self.admin_pwd = ex_object.service_account_password
        else:
            self.admin_user = ex_object.exchange_online_user
            self.admin_pwd = ex_object.exchange_online_password

        self.mailbox_prop = {}
        self.valid_folders = set()
        utils.create_config_file(self.tc_object.id)

    def compare_mailbox_prop(self, op_type, before_backup, after_restore,
                             destination_mailbox_name=None, restore_as_stub=None, destination_mailbox_folder=None):
        """Compare mailbox properties
            Args:
                op_type (str)                   --  set it OVERWRITE or SKIP

                before_backup (dict)            --  ExchangeLib before backup object

                after_restore (dict)            --  ExchangeLib after backup object

                destination_mailbox_name(str)   --  Mailbox Name where restored
                    Default(None)

                restore_as_stub (dict)          --  stubbing rules

                destination_mailbox_folder(str) -- Folder in which you have restored the mailboxes
                    Default(None)

            Raises:
                Exception:
                    If comparision fails
        """
        mbx_name = None
        try:
            logging.info(
                "*********************************************************************")
            if op_type in (OpType.OVERWRITE, OpType.OOPOVERWRITE):
                self.log.info("Validating restore with %s option" % str(op_type))
                for mailbox_name in before_backup:
                    mbx_name = mailbox_name
                    logging.info('Validating MAILBOX: %s\n', mailbox_name)
                    policy_dict = None
                    self.log.info("Validating mailbox properties for : %s", mailbox_name)
                    before_backup_folder = before_backup[mailbox_name]
                    # we dont need to get policy value for journal mailbox
                    if self.mailbox_type != MBX_JOURNAL:
                        policy_dict = self.get_policy_values(mailbox_name)
                    if op_type == OpType.OOPOVERWRITE:
                        # Setting property of after restore object
                        after_restore_folder = None
                        after_re = None
                        for folder in after_restore[destination_mailbox_name].folders:
                            if folder.folder_name.lower() == TOP_OF_INFO_STORE:
                                after_re = folder.sub_folder
                                break

                        if destination_mailbox_folder:
                            for folder in after_re:
                                if destination_mailbox_folder.lower() == folder.folder_name.lower():
                                    after_re = folder.sub_folder
                                    break

                        for sub_folder in after_re:
                            if mailbox_name.lower() == sub_folder.folder_name.lower():
                                after_restore_folder = sub_folder
                                break
                        if not after_restore_folder:
                            raise Exception("Mailbox %s was not restored" % mailbox_name)

                        # Setting property of before restore object
                        for folder in before_backup_folder.folders:
                            if folder.folder_name.lower() == TOP_OF_INFO_STORE:
                                before_backup_folder = folder
                                break

                        if restore_as_stub:
                            self.validate_restore_as_stub(
                                before_backup_folder.sub_folder,
                                after_restore_folder.sub_folder,
                                restore_as_stub,
                                mailbox_name,
                                1)
                            self.log.info("Validated mailbox %s ", mailbox_name)
                        else:
                            self.validate_restores(before_backup_folder.sub_folder,
                                                   after_restore_folder.sub_folder,
                                                   policy_dict, mailbox_name)
                            self.log.info("Validated mailbox %s ", mailbox_name)
                    else:
                        after_restore_folder = after_restore[mailbox_name]
                        if restore_as_stub:
                            self.validate_restore_as_stub(
                                before_backup_folder.folders,
                                after_restore_folder.folders,
                                restore_as_stub, mailbox_name)
                        else:
                            self.validate_restores(
                                before_backup_folder.folders,
                                after_restore_folder.folders,
                                policy_dict, mailbox_name)
            elif op_type == OpType.SKIP:
                serialized_obj = pickle.dumps(before_backup, -1)
                serialized_obj1 = pickle.dumps(after_restore, -1)

                if serialized_obj != serialized_obj1:
                    raise Exception("Restore with skip option was not successful")
            else:
                raise Exception("Invalid option selected")

        except Exception as excp:
            self.log.exception(
                'An error occurred while mailbox property for mailbox %s ', mbx_name)
            raise excp

    def validate_delted_item_retention(self, before_backup, after_restore):
        """Compare mailbox properties in recoverable folder before backup and after restore to
        validate deleted item retention
            Args:
                before_backup (dict) --  ExchangeLib before backup object

                after_restore (dict) --  ExchangeLib after backup object

            Raises:
                Exception:
                    If validation was unsuccessful
        """
        for mailbox_name in before_backup:
            self.log.info("Validating mailbox properties for : %s", mailbox_name)
            mb1 = before_backup[mailbox_name]
            mb2 = after_restore[mailbox_name]
            policy_dict = self.get_policy_values(mailbox_name)
            m1foldermessages = {}
            m2foldermessages = {}
            for m1folder in mb1.folders:
                if 'Recoverable Items' in m1folder.folder_name:
                    for sub_folder in m1folder.sub_folder:
                        m1foldermessages[sub_folder.folder_name] = sub_folder.messages
            for m2folder in mb2.folders:
                if '~Recoverable Items' in m2folder.folder_name:
                    for sub_folder in m2folder.sub_folder:
                        m2foldermessages[sub_folder.folder_name] = sub_folder.messages

            for key in m1foldermessages:
                for key1 in m2foldermessages:
                    if key == key1:
                        m1messages = m1foldermessages[key]
                        m2messages = m2foldermessages[key1]
                        if len(m1messages) != len(m2messages):
                            self.log.error(
                                'Message before backup and after restore  are not '
                                'same in folder %(folder) in mailbox %(mailbox) ',
                                {
                                    'folder': key,
                                    'message': mailbox_name
                                }
                            )
                            raise Exception("Deleted item retention validation failed")

                        for m1message in m1messages:
                            for m2message in m2messages:
                                if m1message.search_key == m2message.search_key:
                                    validity_check = self.check_archive_validity(
                                        m1message, policy_dict)
                                    if validity_check:
                                        if not self.validate_messages(m1message, m2message):
                                            self.log.error('Message with subject %s was not '
                                                           'restored', m1message.subject)
                                            raise Exception("Deleted item retention validation "
                                                            "failed")

    def validate_restores(self, before_backup_folders, after_restore_folders, policy_dict,
                          mailbox_name):
        """Validate in place, oop and pst restores
            Args:
                before_backup_folders (CVFolder)    --  Folders list in mailbox before backup

                after_restore_folders (CVFolder)    --  Folders list in mailbox after restore

                policy_dict (dict)                  --  policy dict

                mailbox_name (str)                  --  mailbox name

            Raises:
                Exception:
                    If validation was unsuccessful or not
        """
        try:
            m1_folder_list = {}
            m2_folder_list = {}
            skip_folders = ("purges", "versions", "calendar logging", "deletions",
                            "recoverable items", "~recoverable items")
            # check if all folders are there before and after restore
            for folder in before_backup_folders:
                if folder.folder_name.lower() not in skip_folders:
                    m1_folder_list[str(folder.folder_name)] = folder
            for folder in after_restore_folders:
                if folder.folder_name.lower() not in skip_folders:
                    m2_folder_list[str(folder.folder_name)] = folder

            # check if all folder names are same
            self.log.info("Checking folders before backup and after restore matches ")
            self.log.info("Before backup")
            self.log.info(m1_folder_list.keys())
            self.log.info("After restore")
            self.log.info(m2_folder_list.keys())
            # messages in folder validation
            for key in m1_folder_list:
                if key in m2_folder_list:
                    # ------- Skip validation of folders in "Recoverable Items" folder
                    m1subfolder = m1_folder_list[key].sub_folder
                    m2subfolder = m2_folder_list[key].sub_folder
                    if m1subfolder:
                        self.log.info('----------------------------------------'
                                      'Validating messages in subfolders of folder %s', key)
                        self.validate_restores(m1subfolder, m2subfolder, policy_dict,
                                               mailbox_name)
                        self.log.info("----------------------------------------")
                    self.log.info("Validating message contents in folder: %s", key)
                    m1_folder_messages = m1_folder_list[key].messages
                    m2_folder_messages = m2_folder_list[key].messages

                    # validating message contents
                    for m1message in m1_folder_messages:
                        check_validity = True
                        res = False
                        if MBX_JOURNAL != self.mailbox_type:
                            check_validity = self.check_archive_validity(m1message, policy_dict)
                        if check_validity:
                            for m2message in m2_folder_messages:
                                if m1message.search_key == m2message.search_key:
                                    res = self.validate_messages(m1message, m2message)
                                    break
                            if not res:
                                raise Exception("Message with subject %s not restored when it"
                                                " should have been" % str(m1message.subject))
                else:
                    if self.check_if_folder_eligible(m1_folder_list[key], policy_dict):
                        raise Exception("Folder: %s not found in restored mailbox, should have "
                                        "been present" % str(key))
        except Exception as excp:
            self.log.exception('An error occurred while mailbox property for '
                               'mailbox %s', mailbox_name)
            raise excp

    def validate_restore_as_stub(
            self,
            before_backup_folders,
            after_restore_folders,
            policy_dict,
            mailbox_name,
            oop=0):
        """Validate in place, oop and pst restores of messages as stubs
            Args:
                before_backup_folders (CVFolder)    --  Folders list in mailbox before backup

                after_restore_folders (CVFolder)    --  Folders list in mailbox after restore

                policy_dict (dict)                  --  policy dict

                mailbox_name (str)                  --  mailbox name

                oop(int)                           --  if it is an oop restore(2 if pst, else 1)
                    Default: 0

            Raises:
                Exception:
                    If validation was unsuccessful or not
        """
        try:
            m1_folder_list = {}
            m2_folder_list = {}
            # check if all folders are there before and after restore
            for folder in before_backup_folders:
                m1_folder_list[str(folder.folder_name)] = folder
            for folder in after_restore_folders:
                m2_folder_list[str(folder.folder_name)] = folder
            if oop == 2:
                m2_folder_list = {}
                for m2folder in after_restore_folders:
                    if m2folder.messages:
                        m2_folder_list[str(m2folder.folder_name)] = m2folder
            elif oop == 1:
                attach = False
                m2_folder_list = {}
                for folder in after_restore_folders:
                    if folder.folder_name == mailbox_name:
                        attach = True
                    if attach and str(folder.folder_name) not in m2_folder_list:
                        m2_folder_list[str(folder.folder_name)] = folder

            # check if all folder names are same
            self.log.info("Checking folders before backup and after restore matches ")
            self.log.info("Before backup")
            self.log.info(m1_folder_list.keys())
            self.log.info("After restore")
            self.log.info(m2_folder_list.keys())
            # messages in folder validation
            for key in m1_folder_list:
                if key in m2_folder_list:
                    # ------- Skip validation of folders in "Recoverable Items"
                    # folders and Non-IPM folders
                    if key.lower() in {"purges", "versions", "calendar logging", "deletions",
                                       "calendar", "contacts", "tasks", "notes",
                                       "recoverable items"}:
                        self.log.info("Skipping folder: %s ", key)
                        if True:
                            continue
                    m1subfolder = m1_folder_list[key].sub_folder
                    m2subfolder = m2_folder_list[key].sub_folder
                    if not oop and m1subfolder:
                        self.log.info('Validating messages in sub folders of folder %s', key)
                        self.validate_restore_as_stub(
                            m1subfolder, m2subfolder, policy_dict, mailbox_name, oop)
                        self.log.info("----------------------------------------")
                    self.log.info("Validating message contents in folder: %s", key)
                    m1_folder_messages = m1_folder_list[key].messages
                    m2_folder_messages = m2_folder_list[key].messages

                    if not oop and len(m1_folder_messages) != len(m2_folder_messages):
                        raise Exception('Message before backup and after restore are not '
                                        'same in folder: %s in mailbox %s' % (key, mailbox_name))
                    # validating message contents
                    for m1message in m1_folder_messages:
                        check_validity = True
                        res = False
                        if MBX_JOURNAL != self.mailbox_type:
                            check_validity = self.check_restore_as_stub_validity(
                                m1message, policy_dict)
                        if check_validity:
                            for m2message in m2_folder_messages:
                                if m1message.search_key == m2message.search_key:
                                    res = self.validate_stub(m1message, m2message)
                                    break
                            if not res:
                                raise Exception(
                                    "Message with subject %s not restored as stub when it"
                                    " should have been" % str(
                                        m1message.subject))
                        else:
                            for m2message in m2_folder_messages:
                                if m1message.search_key == m2message.search_key:
                                    res = self.validate_messages(m1message, m2message)
                                    break
                            if not res:
                                raise Exception("Message with subject %s not restored when it"
                                                " should have been" % str(m1message.subject))

                else:
                    if self.check_if_folder_eligible(m1_folder_list[key], policy_dict):
                        raise Exception("Folder: %s not found in restored mailbox, should have "
                                        "been present" % str(key))
        except Exception as excp:
            self.log.exception('An error occurred while mailbox property for '
                               'mailbox %s', mailbox_name)
            raise excp

    def check_restore_as_stub_validity(self, obj_before, restore_as_stub_dict):
        """Method to check if a message is eligible for restore as stub based
        on the rules on restore job.
             Args:
                    obj_before (CVMessage) --  Message properties object

                    restore_as_stub_dict (dict)     --  Dict of stub rules

            Returns:
                True on success
        """
        try:
            logging.debug("*****Checking Validation*****")

            logging.debug('Messages with attachments: %s ',
                          str(restore_as_stub_dict['collect_msg_with_attach']))
            if restore_as_stub_dict['collect_msg_with_attach']:
                if not obj_before.attachment_details:
                    logging.info(
                        "Attachments not Present in this mail, "
                        "so restore data version instead of stub")
                    return False

            logging.debug("Include messages larger than: %s",
                          str(int(restore_as_stub_dict['collect_msgs_larger_than']) * 1024))
            logging.debug("Message Size: %s", str(obj_before.message_size))
            if (int(restore_as_stub_dict['collect_msgs_larger_than'])
                * 1024) > int(obj_before.message_size):
                logging.debug("Message size is lesser, so restore data version instead of stub")
                return False

            no_of_days = utils.calculate_duration(obj_before.received_time)

            logging.debug("Number of days: %s", str(no_of_days))
            logging.debug("Include messages older than: %s", str(
                restore_as_stub_dict['collect_msgs_days_after']))
            if int(restore_as_stub_dict['collect_msgs_days_after']) > int(no_of_days):
                logging.debug(
                    "Number of days is lesser than message rule, "
                    "so restore data version instead of stub")
                return False

            logging.info("Message is qualified, Restore stub version")
            return True

        except Exception as excp:
            self.log.exception('An error occurred while checking restore as stub validity')
            raise excp

    def check_archive_validity(self, obj_before, policy_dict):
        """Method to check if a message is eligible for archive job based
        on the message rules of the Archive Policy
             Args:
                    obj_before (CVMessage) --  Message properties object

                    policy_dict (dict)     --  Dict of policy values

            Returns:
                True on success
        """
        try:
            logging.debug("*****Checking Validation*****")

            logging.debug('Archive messages with attachments: %s ',
                          str(policy_dict['OnlyMsgsWithAttachemts']))
            if policy_dict['OnlyMsgsWithAttachemts'] == "1":
                if not obj_before.attachment_details:
                    logging.info(
                        "Attachments not Present in this mail, so not eligible for Archive")
                    return False

            logging.debug("Include messages larger than: %s",
                          str(int(policy_dict['MsgsLargerThan']) * 1024))
            logging.debug("Message Size: %s", str(obj_before.message_size))
            if (int(policy_dict['MsgsLargerThan']) * 1024) > int(obj_before.message_size):
                logging.debug("Message size is lesser, so not eligible for Archive")
                return False

            no_of_days = utils.calculate_duration(obj_before.received_time)

            logging.debug("Number of days: %s", str(no_of_days))
            logging.debug("Include messages older than: %s", str(policy_dict['MsgsOlderThan']))
            if int(policy_dict['MsgsOlderThan']) > int(no_of_days):
                logging.debug(
                    "Number of days is lesser than message rule, so not eligible for archive")
                return False

            logging.info("Message is qualified for Archive job")
            return True

        except Exception as excp:
            self.log.exception('An error occurred while checking archive validity')
            raise excp

    def get_policy_values(self, mailbox_name):
        """Method to get values of policy associated to mailbox
            Args:
                mailbox_name  (str)  --  Mailbox name associated to subclient

            Returns:
                policy_dict (dict) -- Dict of policy values
        """
        _query = "select id from APP_Client where name = '%s'" % self.client_name
        self.csdb.execute(_query)
        _results = self.csdb.fetch_one_row()

        _query1 = ("select policyId from APP_EmailConfigPolicies where policyType = 1 and "
                   "componentNameId IN (select assocId from APP_EmailConfigPolicyAssoc "
                   "where clientId = '%s' and smtpAdrress = '%s' and modified = 0 )" %
                   (_results[0], mailbox_name))
        self.csdb.execute(_query1)
        _results1 = self.csdb.fetch_one_row()

        _query2 = ("select policyDetails from APP_ConfigurationPolicyDetails where  "
                   "modified = 0 and componentNameId ='%s' " % _results1[0])
        self.csdb.execute(_query2)
        _results2 = self.csdb.fetch_one_row()

        policy_xml = _results2[0]
        policy_dict = {}

        policy_xml = "<root>" + policy_xml + "</root>"
        #   adding a root XML element to decode policy XMl for O365 Plans
        # Getting the message rules based on the Policy XML retrieved from the CS DB
        dict_of_base_xml = OrderedDict(
            parse(
                policy_xml,
                process_namespaces=True))  # Converting XML into Dict

        dict_of_base_xml = dict_of_base_xml["root"]
        #   remove the extra root XML

        include_msgs_older_than = dict_of_base_xml['emailPolicy'][
            'archivePolicy']['@includeMsgsOlderThan']
        policy_dict['MsgsOlderThan'] = str(include_msgs_older_than)
        logging.info(
            "includeMsgsOlderThan rule of Archive Policy: %s",
            str(include_msgs_older_than))

        include_msgs_larger_than = dict_of_base_xml['emailPolicy'][
            'archivePolicy']['@includeMsgsLargerThan']

        policy_dict['MsgsLargerThan'] = str(include_msgs_larger_than)
        logging.info(
            "includeMsgsLargerThan rule of Archive Policy: %s",
            str(include_msgs_larger_than))

        include_only_msgs_with_attachemts = dict_of_base_xml[
            'emailPolicy']['archivePolicy']['@includeOnlyMsgsWithAttachemts']
        policy_dict['OnlyMsgsWithAttachemts'] = str(include_only_msgs_with_attachemts)

        logging.info(
            "includeOnlyMsgsWithAttachemts rule of Archive Policy: %s",
            str(include_only_msgs_with_attachemts))

        return policy_dict

    def validate_messages(self, m1message, m2message):
        """compare messages properties
            Args:
                m1message(CVMessage)  --  cvmessage object

                m2message(CVMessage)  --  cvmessage object

            Returns:
                True on success
        """
        if m1message.lastmodified_time == m2message.lastmodified_time:
            self.log.error('Message is not modified. Restore was not done for the message with '
                           'subject %s although it was eligible for backup.', m1message.subject)
            return False

        self.log.info(
            "Validating message properties of email with subject %s ", m1message.subject)

        if (m1message.txt_body != m2message.txt_body and
                m1message.received_time != m2message.received_time
                and m1message.is_read != m2message.is_read and
                m1message.has_attachment != m2message.has_attachment
                and m1message.importance != m2message.importance):
            self.log.error('Message details like body subject, received time etc. are '
                           'incorrectly restored for message with subject %s',
                           m1message.subject)
            return False

        if not m1message.contact_info:
            if m1message.subject != m2message.subject:
                return False

        if m1message.attachment_details:
            self.log.info("Attachments validation for message")
            if len(m1message.attachment_details) != len(
                    m2message.attachment_details):
                self.log.error("Attachments count does not match")
                return False

            for m1att in m1message.attachment_details:
                for m2att in m2message.attachment_details:
                    if m1att.attachment_id == m2att.attachment_id:
                        if (m1att.content != m2att.content and m1att.name != m2att.name
                                and m1att.size != m2att.size and
                                m1att.content_type != m2att.content_type
                                and m1att.is_inline != m2att.is_inline and
                                m1att.lastmodified_time != m2att.lastmodified_time
                                and m1att.content_location != m2att.content_location
                                and m1att.is_contactphoto != m2att.is_contactphoto):
                            self.log.error("Attachments details does not match ")
                            return False

        if m1message.contact_info:
            self.log.info("This is a contact. Validation of contact item")
            for m1contact in m1message.contact_info:
                for m2contact in m2message.contact_info:
                    if (m1contact.contact_displayname != m2contact.contact_displayname
                            and m1contact.contact_emailaddress !=
                            m2contact.contact_emailaddress
                            and m1contact.company != m2contact.company
                            and m1contact.department != m2contact.department
                            and m1contact.jobtittle != m2contact.jobtittle
                            and m1message.givenname != m2contact.givenname):
                        self.log.error("Contact details does not match ")
                        return False

        return True

    def validate_stub(self, m1message, m2message):
        """compare stub properties
            Args:
                m1message(CVMessage)  --  cvmessage object

                m2message(CVMessage)  --  cvmessage object

            Returns:
                True on success
        """

        # Condition 1: Compare subject
        self.log.info("Validating message subject: %s ", m1message.subject)
        if not m1message.contact_info:
            if m1message.subject != m2message.subject:
                self.log.error(
                    'Message subject: %s is modified during stubbing.',
                    m1message.subject)
                return False

        # Condition 2: Compare last modified time(LMT)
        self.log.info(
            "Validating message last modified time(LMT) of email with subject %s ",
            m1message.subject)
        if m1message.lastmodified_time == m2message.lastmodified_time:
            self.log.error('Message LMT did not change subject: %s ', m1message.subject)
            return False

        # Condition 3: Compare message class
        self.log.info("Validating message class of email with subject %s ", m1message.subject)
        if m1message.message_class == m2message.message_class:
            self.log.error(
                'Message class not modified after stubbing for message: %s',
                m1message.subject)
            return False

        return True

    def validate_contentstore_restore_to_disk(self, before_backup, after_restore):
        """Compare mailbox properties to validate restores
            Args:
                before_backup (dict) --  Mailbox properties before backup

                after_restore (dict) --  Mailbox properties after restore

            Raises:
                Exception:
                    If an error was returned while validating restore to disk
        """
        try:
            self.log.info("Validating restore to disk for ContentStore Mailbox Backupset ")
            for mailbox_name in before_backup:

                m1folders = before_backup[mailbox_name].folders
                m2folders = after_restore['restore_path'].folders
                m1foldermessages = []
                m2foldermessages = []
                for m1folder in m1folders:
                    for message in m1folder.messages:
                        m1foldermessages.append(message)
                for m2folder in m2folders:
                    for message in m2folder.messages:
                        m2foldermessages.append(message)
                for m1messgae in m1foldermessages:
                    for m2message in m2foldermessages:
                        if m1messgae.exch_message_id == m2message.eml_message_id:
                            if (m1messgae.eml_subject != m2message.eml_subject and
                                    m1messgae.eml_received_time != m2message.eml_received_time
                                    and m1messgae.exch_return_path != m2message.eml_return_path):
                                raise Exception("Not able to validate eml properties for "
                                                "mailbox %(mailbox) and subject %(subject) ",
                                                {
                                                    'mailbox': mailbox_name,
                                                    'subject': m1messgae.eml_subject
                                                }
                                                )

        except Exception as excp:
            self.log.exception(
                'An error occurred while mailbox property for mailbox %s', excp)
            raise excp

    def compare_restore_disk(self, before_backup, destination_client, destination_dir):
        """Compare mailbox properties for disk restores
            Args:
                before_backup (dict)        --  Mailbox properties before backup

                destination_client (str)    --  Client name where the mailboxes were restored

                destination_dir(str)        --  Path where mailboxes were restored

            Raises:
                Exception:
                    If comparision fails
        """
        mbx_name = ""
        try:
            remote_machine = Machine(destination_client, self.tc_object.commcell)
            if not remote_machine.check_directory_exists(destination_dir):
                raise Exception("The directory does not exist")

            for mailbox_name in before_backup:
                mbx_name = mailbox_name
                self.log.info("\n--------------- Validating disk restore for "
                              "%s---------------\n", mailbox_name)
                policy_dict = None
                if self.mailbox_type != MBX_JOURNAL:
                    policy_dict = self.get_policy_values(mailbox_name)
                before_backup_obj = None
                for folder in before_backup[mailbox_name].folders:
                    if folder.folder_name.lower() == TOP_OF_INFO_STORE:
                        before_backup_obj = folder

                remote_machine = Machine(destination_client, self.tc_object.commcell)
                contents = remote_machine.scan_directory(f'{destination_dir}\\{mailbox_name}')
                after_restore = self.restore_disk_helper(f'{destination_dir}\\{mailbox_name}',
                                                         contents)
                self.validate_restores_disk(before_backup_obj, policy_dict, after_restore)
                self.log.info("\n-------------- Mailbox %s successfully verified----------\n",
                              mailbox_name)

        except Exception as excp:
            self.log.exception('An error occurred while mailbox property for mailbox %s', mbx_name)
            raise excp

    def compare_restore_pst(self, before_backup, after_restore, restore_mbx_name):
        """Compare mailbox properties for pst restores
            Args:
                before_backup (dict)     --  Mailbox properties before backup

                after_restore (dict)     --  Mailbox properties after restore

                restore_mbx_name(str)    --  Name of mailbox where data was restored

            Raises:
                Exception:
                    If comparision fails
        """
        mbx_name = None
        try:
            after_restore = after_restore[restore_mbx_name]
            for folder in after_restore.folders:
                if folder.folder_name.lower() == TOP_OF_INFO_STORE:
                    after_restore = folder
                    break
            for mailbox_name in before_backup:
                self.log.info("Validating restore for %s", mailbox_name)
                mbx_name = mailbox_name
                before_backup_folder = before_backup[mailbox_name]
                for folder in before_backup_folder.folders:
                    if folder.folder_name.lower() == TOP_OF_INFO_STORE:
                        before_backup_folder = folder
                        break
                policy_dict = None
                if self.mailbox_type != MBX_JOURNAL:
                    policy_dict = self.get_policy_values(mailbox_name)

                self.validate_restores(
                    before_backup_folder.sub_folder,
                    after_restore.sub_folder,
                    policy_dict, mbx_name)
        except Exception as excp:
            self.log.exception("Error in validating PST Restores for mailbox %s" % str(mbx_name))
            raise excp

    def check_if_folder_eligible(self, folder, policy_dict):
        """Validate if folder is eligible for backup
            Args:
                folder(CVFolder)       --  CVFolder object of folder to verify

                policy_dict (dict)     --  policy dict

            Returns:
                True on success
        """
        try:
            val = 0
            res = False
            if folder.messages:
                for msg in folder.messages:
                    if self.check_archive_validity(msg, policy_dict):
                        val = val + 1
            if folder.sub_folder:
                for sub_folder in folder.sub_folder:
                    if self.check_if_folder_eligible(sub_folder, policy_dict):
                        res = True
            if val > 1 or res:
                self.valid_folders.add(folder.folder_name)
                res = True
            else:
                res = False
            return res
        except Exception as excp:
            self.log.exception("Exception occurred while testing eligibility of folder %s",
                               folder.folder_name)
            raise excp

    def restore_disk_helper(self, root_dir, contents):
        """Helper function to validate disk restores.
        Gets the count of immediate folders and files within a folder
            Args:
                root_dir(str)           --  Path of directory to scan

                contents(dict)          --  Dictionary with list of files in folder

            Returns:
               dictionary with number of messages, sub folders, and sub folder names in
               root_dir
        """
        try:
            folder_details, sub_folder_list = {}, {}
            root_dir += "\\"
            folder_cnt, message_cnt = 0, 0
            for item in contents:
                path = item['path'].split(root_dir)
                if path and len(path) > 1:
                    paths = path[1].split("\\")
                    if len(paths) == 1:
                        if item['type'] == 'file':
                            message_cnt += 1
                        else:
                            folder_cnt += 1
                            sub_folder = self.restore_disk_helper(
                                f'{root_dir}{paths[0]}', contents)
                            sub_folder_list[paths[0]] = sub_folder

            folder_details["msg_length"] = message_cnt
            folder_details["sub_folder_length"] = folder_cnt
            folder_details["sub_folder_list"] = sub_folder_list
            return folder_details

        except Exception as excp:
            self.log.exception("Exception occurred while getting list of files and folders"
                               " under %s", root_dir)
            raise excp

    def validate_restores_disk(self, before_backup, policy_dict, after_restore):
        """Validate restores to disk
            Args:
                before_backup (CVFolder)  --  Exchange CVFolder Object

                policy_dict (dict)        --  Policy Dictionary

                after_restore (dict)      --  Dictionary from restore_disk_helper

            Raises:
                Exception:
                    if validation is unsuccessful
        """
        try:
            self.log.info("Validating restore of folder: %s", before_backup.folder_name)
            msg_cnt, folder_cnt = 0, 0
            for msg in before_backup.messages:
                check_validity = True
                if MBX_JOURNAL != self.mailbox_type:
                    check_validity = self.check_archive_validity(msg, policy_dict)
                if check_validity:
                    msg_cnt += 1
            if msg_cnt != after_restore["msg_length"]:
                raise Exception("Total number of messages before backup and after restore"
                                " to disk in folder %s are not same" %
                                str(before_backup.folder_name))

            for sub_folder in before_backup.sub_folder:
                if self.check_if_folder_eligible(sub_folder, policy_dict):
                    if sub_folder.folder_name not in after_restore["sub_folder_list"]:
                        raise Exception("Folder %s not found in restored folders." %
                                        str(sub_folder.folder_name))
                    folder_cnt += 1
                    self.validate_restores_disk(sub_folder, policy_dict,
                                                after_restore["sub_folder_list"][
                                                    sub_folder.folder_name])

            if folder_cnt != after_restore["sub_folder_length"]:
                raise Exception("Total number of sub folders before backup and after restore "
                                "to disk in folder %s are not same" %
                                str(before_backup.folder_name))

        except Exception as excp:
            self.log.exception("Error occurred while validating disk restores.")
            raise excp

    def compare_mailbox_for_pst_ingestion(self, before_backup_folder, after_restore_folder):
        """Compare mailbox properties for pst ingestion
            Args:
                before_backup_folder (dict)     --  ExchangeLib before backup object

                after_restore_folder (dict)     --  ExchangeLib after restore object

            Raises:
                Exception:
                    If comparision fails

        """
        for folder in after_restore_folder:
            if folder.folder_name.lower() == TOP_OF_INFO_STORE:
                after_restore_folder = folder.sub_folder
                break
        for mailbox, props in before_backup_folder.items():
            before_backup_obj = None
            policy_dict = None
            after_restore_obj = None
            for folder in props.folders:
                if folder.folder_name.lower() == TOP_OF_INFO_STORE:
                    before_backup_obj = folder.sub_folder
            if self.mailbox_type != MBX_JOURNAL:
                policy_dict = self.get_policy_values(mailbox)
            for folder in after_restore_folder:
                if folder.folder_name == mailbox:
                    after_restore_obj = folder.sub_folder
                    break
            if not after_restore_obj:
                raise Exception("Mailbox %s not found in after restore object " % mailbox)
            self.validate_restores_pst_ingestion(before_backup_obj, after_restore_obj, policy_dict,
                                                 mailbox)

    def validate_restores_pst_ingestion(self, before_backup_folders, after_restore_folders,
                                        policy_dict, mailbox):
        """Validate in place, oop and pst restores
            Args:
                before_backup_folders (CVFolder)    --  Folders list in mailbox before backup

                after_restore_folders (CVFolder)    --  Folders list in mailbox after restore

                policy_dict (dict)                  --  policy dict

                mailbox (str)                       --  mailbox name

            Raises:
                Exception:
                    If validation was unsuccessful
        """
        try:
            m1_folder_list = {}
            m2_folder_list = {}
            for folder in before_backup_folders:
                m1_folder_list[str(folder.folder_name)] = folder
            for folder in after_restore_folders:
                m2_folder_list[str(folder.folder_name)] = folder

            self.log.info("Checking folders before backup and after restore matches ")
            self.log.info("Before backup")
            self.log.info(m1_folder_list.keys())
            self.log.info("After restore")
            self.log.info(m2_folder_list.keys())

            for key in m1_folder_list:
                if key in m2_folder_list:
                    # ------- Skip validation of folders in "Recoverable Items" folder
                    if key.lower() in {"purges", "versions", "calendar logging", "deletions"}:
                        self.log.info("Skipping folder %s as it is in Recoverable Items", key)
                        if True:
                            continue
                    m1subfolder = m1_folder_list[key].sub_folder
                    m2subfolder = m2_folder_list[key].sub_folder
                    if m1subfolder:
                        self.log.info('----------------------------------------'
                                      'Validating messages in subfolders of folder %s', key)
                        self.validate_restores_pst_ingestion(m1subfolder, m2subfolder, policy_dict,
                                                             mailbox)
                        self.log.info("----------------------------------------")
                    self.log.info("Validating message contents in folder: %s", key)
                    m1_folder_messages = m1_folder_list[key].messages
                    m2_folder_messages = m2_folder_list[key].messages

                    for m1message in m1_folder_messages:
                        check_validity = True
                        res = False
                        if MBX_JOURNAL != self.mailbox_type:
                            check_validity = self.check_archive_validity(m1message, policy_dict)
                        if check_validity:
                            for m2message in m2_folder_messages:
                                if m1message.search_key == m2message.search_key:
                                    res = self.validate_messages(m1message, m2message)
                                    break
                            if not res:
                                raise Exception("Message with subject %s not restored when it"
                                                " should have been" % str(m1message.subject))
                else:
                    if self.check_if_folder_eligible(m1_folder_list[key], policy_dict):
                        raise Exception("Folder: %s not found in restored mailbox, should have"
                                        " been present" % str(key))
        except Exception as excp:
            self.log.exception('An error occurred while mailbox property for '
                               'mailbox %s', mailbox)
            raise excp
