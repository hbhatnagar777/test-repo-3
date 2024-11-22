# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Class:
Cleanup - Class for validating Cleanup Operation with various cleanup policies having different
message rules

Cleanup:

    __init__                            --- initializes Cleanup object

    compare_mailbox_prop_cleanup        --- Method to call validation functions based on
    'Create Stubs' or 'Delete Messages' selection

    create_config_file                  --- Creates log file for storing and comparing item roles

    validate_cleanup_delete             --- Validate if message has been deleted based on Cleanup
    Policy rule

    validate_source_pruning             --- Validate if message has been pruned from source based
    on Cleanup Policy rule

    validate_cleanup                    --- Validate if message has been stubbed based on Cleanup
    Policy rule

    check_cleanup_validity              --- Check if a message is eligible for cleanup

    get_policy_values                   --- Get values from Cleanup Policy

    check_cleanup_source_prunning_eligibility   --- Check if message is eligible to be pruned

"""

from collections import OrderedDict
import os
import logging
import base64
from xmltodict import parse
from cvpysdk.commcell import Commcell
from bs4 import BeautifulSoup
from . import utils
from . import constants as CONSTANT


class Cleanup():
    """Class for performing Cleanup related operations."""

    def __init__(self, ex_object):
        """
            Initializes the Cleanup object.

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
        if self.exchange_type == 'O365':
            self.admin_user = ex_object.exchange_online_user
            self.admin_pwd = ex_object.exchange_online_password
        else:
            self.admin_user = ex_object.service_account_user
            self.admin_pwd = ex_object.service_account_password
        self.mailbox_prop = {}
        self.tcinputs = self.tc_object.tcinputs
        self.recall_service = self.tcinputs['RecallService']
        utils.create_config_file(self.tc_object.id)

    def compare_mailbox_prop_cleanup(
            self,
            before_cleanup,
            after_cleanup,
            delete=False):
        """
            Compares mailbox properties after cleanup operation.

            Args:
                before_cleanup: Exchangelib object before backup

                after_cleanup: ExchangeLib object after cleanup

                delete: if delete = False, then calls validate_cleanup()
                        else, calls validate_cleanup_delete()

            Raises:
                Exception:
                    If an error was returned while validating mailbox properties

        """

        try:
            if not delete:
                # Call validate_cleanup()
                if not self.validate_cleanup(before_cleanup, after_cleanup):
                    raise Exception("Cleanup Validation failed for mailbox.")

            else:
                # Call validate_cleanup_delete()
                if not self.validate_cleanup_delete(before_cleanup, after_cleanup):
                    raise Exception("Cleanup Validation failed for mailbox.")

        except Exception as excp:
            self.log.exception(
                'Exception while comparing mailbox properties after Cleanup'
            )
            raise excp

    def validate_cleanup_delete(self, before_cleanup, after_cleanup):
        """
            Validate if messages are deleted during cleanup job

            Args:
                before_cleanup --  Object of Exchangelib before cleanup

                after_cleanup --  Object of ExchangeLib after cleanup

            Returns:
                True on success

        """
        try:
            self.log.info("Mailboxes before cleanup: ")
            self.log.info(before_cleanup)
            for (key_before_cleanup, value_before_cleanup), (
                    key_after_cleanup, value_after_cleanup) in \
                    zip(before_cleanup.items(), after_cleanup.items()):
                mailbox_name = key_before_cleanup
                before_cleanup = value_before_cleanup
                after_cleanup = value_after_cleanup
                self.log.info("Validating mailbox properties for: %s", str(mailbox_name))
                logging.info("Validation of Mailbox: %s", mailbox_name)
                # Fetching Cleanup Policy values
                policy_dict = self.get_policy_values(mailbox_name)
                logging.info("Policy values in policy_dict: ")
                logging.info(policy_dict)

                folders_list = []

                # Fetch folders before cleanup
                all_folders_before_cleanup = before_cleanup.folders
                for folder1 in all_folders_before_cleanup:
                    if hasattr(folder1, 'sub_folder'):
                        all_folders_before_cleanup.extend(folder1.sub_folder)
                logging.info("Folders before Cleanup Job:")
                logging.info(all_folders_before_cleanup)

                # Getting list of all folders after cleanup
                all_folders_after_cleanup = after_cleanup.folders
                for folder1 in all_folders_after_cleanup:
                    if hasattr(folder1, 'sub_folder'):
                        all_folders_after_cleanup.extend(folder1.sub_folder)
                        folders_list.append(folder1.folder_name)
                logging.info("Folders after Cleanup job:")
                logging.info(all_folders_after_cleanup)

                # Traversing through each folder present in the list of folders before Cleanup
                for folder in all_folders_before_cleanup:
                    logging.info('\n')
                    logging.info("################################################")
                    logging.info("Folder name: %s", folder.folder_name)

                    # Skip validation of these folders as they are present under "Recoverable
                    # Items" or "Drafts" folder
                    if folder.folder_name.lower() in [
                            "calendar logging", "deletions", "purges", "versions", "drafts"]:
                        logging.info(
                            "Skipping this folder as it is under Recoverable Items or Drafts")
                        continue

                    # Getting all messages in the folder before cleanup
                    msg2 = folder.messages

                    # Check if this folder is present even after Cleanup
                    try:
                        index1 = folders_list.index(folder.folder_name)
                    except BaseException:
                        self.log.error("%s Folder does not exist", str(folder.folder_name))
                        logging.error("%s Folder does not exist", str(folder.folder_name))
                        return False

                    # Getting all messages in the folder after cleanup
                    msg1 = all_folders_after_cleanup[index1].messages

                    # Storing search keys of all messages before cleanup
                    search_key_list = []
                    for index_range in range(0, len(msg2)):
                        search_key_list.append(msg2[index_range].search_key)

                    # In case of Delete Messages option enabled in cleanup policy,
                    # see if message are eligible for cleanup

                    logging.info('\n')
                    logging.info("Delete Messages Enabled")
                    search_key_list_after_cleanup = []

                    # Storing search keys of mailbox after cleanup, if any
                    if msg1:
                        for range1 in range(0, len(msg1)):
                            search_key_list_after_cleanup.append(msg1[range1].search_key)
                            logging.info("Search key that is being added into list: %s"
                                         "", str(msg1[range1].search_key))

                    for msg in msg2:
                        logging.info('\n')
                        logging.info("Subject: %s", str(msg.subject.encode('utf8')))
                        logging.info("Search Key: %s", str(msg.search_key))
                        if policy_dict['CreateStubs'] == '0':
                            # Check if message is eligible for cleanup
                            if self.check_cleanup_validity(msg, policy_dict):
                                if msg.search_key in search_key_list_after_cleanup:

                                    self.log.info(
                                        "This mail has not been deleted although Delete Message is "
                                        "enabled in cleanup policy")
                                    logging.info(
                                        "This mail has not been deleted although Delete Message is "
                                        "enabled in cleanup policy")
                                    return False

                                logging.info("ELIGIBLE: Validated the message")
                            else:
                                if msg.search_key not in search_key_list_after_cleanup:
                                    logging.info("This mail has been deleted although "
                                                 "it is not eligible for cleanup")
                                    self.log.info("This mail has been deleted although "
                                                  "it is not eligible for cleanup")
                                    return False

                                logging.info("NOT ELIGIBLE: Validated the message")
                        else:
                            logging.info("Delete Messages option not selected in Cleanup Policy")
                            return False
            return True
        except Exception as excp:
            self.log.exception('Exception during validation of mailboxes after Cleanup')
            raise excp

    def validate_source_pruning(self, before_cleanup_dict, after_cleanup_dict):
        """
            Validate source pruning after clenaup job

            Args:
                before_cleanup_dict --  Exchangelib before cleanup object

                after_cleanup_dict --  ExchangeLib after cleanup object

            Returns:
                True on success

        """
        for mailbox_name in before_cleanup_dict:
            policy_dict = self.get_policy_values(mailbox_name)
            before_cleanup = before_cleanup_dict[mailbox_name]
            after_cleanup = after_cleanup_dict[mailbox_name]
            folders_list = []
            all_folders_before_cleanup = before_cleanup.folders
            for folder in all_folders_before_cleanup:
                if hasattr(folder, 'sub_folder'):
                    all_folders_before_cleanup.extend(folder.sub_folder)

            # Getting list of all folders after cleanup
            all_folders_after_cleanup = after_cleanup.folders
            for folder in all_folders_after_cleanup:
                if hasattr(folder, 'sub_folder'):
                    all_folders_after_cleanup.extend(folder.sub_folder)
                    folders_list.append(folder.folder_name)

            # Traversing through each folder present in all_folders_before_cleanup
            for folder in all_folders_before_cleanup:
                self.log.info('\n')
                self.log.info("################################################")
                self.log.debug("FOLDER NAME: %s", folder.folder_name)

                # Getting all messages in the folder before cleanup
                before_cleanup_msg = folder.messages
                try:
                    index1 = folders_list.index(folder.folder_name)
                except Exception:
                    self.log.error("Folder: %s does not exist", str(folder.folder_name))
                    return False

                # Getting all messages in the folder after cleanup
                after_cleanup_msg = all_folders_after_cleanup[index1].messages

                # Storing search keys of all messages before cleanup
                search_key_list = []
                for msg in range(0, len(before_cleanup_msg)):
                    search_key_list.append(before_cleanup_msg[msg].search_key)
                    self.log.info("Search key that is being added into list: '{0}'".format(
                        str(before_cleanup_msg[msg].search_key)))

                search_key_list_after_cleanup = []

                # Storing search keys of mailbox after cleanup, if any
                if after_cleanup_msg:
                    for msg in range(0, len(after_cleanup_msg)):
                        search_key_list_after_cleanup.append(after_cleanup_msg[msg].search_key)
                        self.log.info("Search key that is being added into list: '{0}'"
                                      "".format(str(after_cleanup_msg[msg].search_key)))

                for msg in before_cleanup_msg:
                    if self.check_cleanup_source_prunning_eligibility(msg, policy_dict):
                        self.log.info("Subject: %s", str(msg.subject.encode('utf8')))
                        self.log.info("Search Key: %s", str(msg.search_key))

                        if msg.search_key in search_key_list_after_cleanup:
                            self.log.error(
                                "This mail has not been pruned although Delete Message is "
                                "enabled in cleanup policy")
                            return False

                        self.log.info("ELIGIBLE: Validated the message")
                    else:
                        if msg.search_key not in search_key_list_after_cleanup:
                            logging.error("This mail has been pruned although it is not "
                                          "eligible for cleanup")
                            self.log.error("This mail has been pruned although it is not "
                                           "eligible for cleanup")
                            return False

                        logging.info("NOT ELIGIBLE: Validated the message")

        return True

    def validate_cleanup(self, before_cleanup, after_cleanup):
        """
            Validate if messages are Stubbed after cleanup job

            Args:
                before_cleanup --  Object of Exchangelib before cleanup

                after_cleanup --  Object of ExchangeLib after cleanup

            Returns:
                True on success

            Raises:
                Exception:
                    If an error occurred during validation

        """
        try:
            v11_cv_stub_parameter = 'V="12"'

            # File to store the message body
            _body_file = os.path.join(CONSTANT.RETRIEVED_FILES_PATH, "MessageBody.txt")

            # Fetching the mailbox name
            self.log.info("Mailboxes before cleanup: ")
            self.log.info(before_cleanup)
            self.log.info("Mailboxes after cleanup: ")
            self.log.info(after_cleanup)

            # for mailbox_name in before_cleanup:
            for (key_before_cleanup, value_before_cleanup), \
                (key_after_cleanup, value_after_cleanup) \
                    in zip(before_cleanup.items(), after_cleanup.items()):
                logging.info('\n')
                policy_dict = None
                mailbox_name = key_before_cleanup
                self.log.info("Validating mailbox properties for: %s", mailbox_name)
                folders_list = []

                # Getting mailbox property objects before and after cleanup
                before_cleanup = value_before_cleanup
                after_cleanup = value_after_cleanup

                # Fetching Cleanup Policy values
                policy_dict = self.get_policy_values(mailbox_name)
                logging.info("Policy values in policy_dict: ")
                logging.info(policy_dict)

                # Getting list of all folders before cleanup
                all_folders_before_cleanup = before_cleanup.folders
                for folder1 in all_folders_before_cleanup:
                    if hasattr(folder1, 'sub_folder'):
                        all_folders_before_cleanup.extend(folder1.sub_folder)

                # Getting list of all folders after cleanup
                all_folders_after_cleanup = after_cleanup.folders
                for folder1 in all_folders_after_cleanup:
                    if hasattr(folder1, 'sub_folder'):
                        all_folders_after_cleanup.extend(folder1.sub_folder)
                        folders_list.append(folder1.folder_name)

                # Traversing through each folder present in all_folders_before_cleanup
                for folder in all_folders_before_cleanup:
                    logging.info('\n')
                    logging.info(
                        "##################################################################")
                    logging.debug("FOLDER NAME: %s", folder.folder_name)

                    # Skip validation of these folders as they are present under "Recoverable
                    # Items" or "Drafts" folder
                    if folder.folder_name.lower() in [
                            "calendar logging", "deletions", "purges", "versions", "drafts"]:
                        logging.info(
                            "Skipping this folder as it is under Recoverable Items or Drafts")
                        continue

                    # Getting all messages in the folder before cleanup
                    msg2 = folder.messages
                    try:
                        index1 = folders_list.index(folder.folder_name)
                    except Exception:
                        self.log.error("%s - This Folder does not exist", str(folder.folder_name))
                        logging.error("%s - This Folder does not exist", str(folder.folder_name))
                        return False

                    # Getting all messages in the folder after cleanup
                    msg1 = all_folders_after_cleanup[index1].messages

                    # Storing search keys of all messages before cleanup
                    search_key_list = []
                    for index1 in range(0, len(msg2)):
                        search_key_list.append(msg2[index1].search_key)

                    for index2 in range(0, len(msg1)):
                        logging.info('\n')
                        logging.info("Search key after cleanup: %s", msg1[index2].search_key)

                        try:
                            index2 = search_key_list.index(msg1[index2].search_key)
                        except BaseException:
                            self.log.info("%s : Mail is not present", str(msg1[index2].subject))
                            logging.info("%s : Mail is not present", str(msg1[index2].subject))
                            return False

                        logging.info(
                            "Search key before cleanup: %s",
                            msg2[index2].search_key)
                        logging.info("MESSAGE SUBJECT: %s", msg1[index2].subject)
                        logging.info("SUBJECT BEFORE CLEANUP: %s", msg2[index2].subject)
                        logging.info("Entry ID: %s", str(msg1[index2].entry_id))
                        logging.info("Message Class before Cleanup: %s",
                                     str(msg2[index2].message_class))
                        logging.info("Message Class after Cleanup: %s",
                                     str(msg1[index2].message_class))

                        if msg2[index2].message_class == "IPM.Note" and \
                                self.check_cleanup_validity(msg2[index2], policy_dict):
                            """Only the mails that are of IPM.Note message class and
                             eligible for cleanup based on cleanup policy will be stubbed"""

                            logging.debug("**** ELIGIBLE FOR CLEANUP ****")

                            # Fetching the User GUID
                            logging.info("Fetching User Guid from the embedded recall link")
                            var1 = msg1[index2].cv_stub.split('mg=')
                            var2 = var1[1].split('&amp')

                            _recall_link_user_guid = base64.b64decode(var2[0])
                            _recall_link_user_guid = _recall_link_user_guid.decode()

                            logging.info("CV Stub value: %s", str(msg1[index2].cv_stub))
                            logging.info("CV Dataheader value: %s",
                                         str(msg1[index2].cv_dataheader))
                            logging.info("User GUID retrieved from CS DB: %s",
                                         str(policy_dict['userGuid']))
                            logging.info(
                                "_recall_link_user_guid retrieved from CVStub: %s",
                                _recall_link_user_guid)
                            logging.info("Message Class before Cleanup: %s",
                                         str(msg2[index2].message_class))
                            logging.info("Message Class after Cleanup: %s",
                                         str(msg1[index2].message_class))

                            # Write message body into file present in _body_file path
                            logging.info(
                                "Writing message body into file present in"
                                "<Commvault Folder>/Automation/Application/"
                                "Exchange/ExchangeMailbox/"
                                "RetrievedFiles/MessageBody.txt")

                            bodyfile = open(_body_file, "w")
                            bodyfile.write(msg1[index2].body)
                            bodyfile.close()

                            # Read body from the file saved in above step
                            logging.info("Reading the body...")
                            with open(_body_file, 'r') as content_file:
                                msg_body = content_file.read()

                            # Fetch the recall link
                            logging.info("Fetching the recall link")
                            htmlvar = msg_body
                            htmlvar = htmlvar.split('<a href=')
                            htmlvar = htmlvar[1].split('style')
                            htmlvar = htmlvar[0].split('/webconsole')
                            htmlvar = htmlvar[0].split('"')
                            embedded_recall_link = htmlvar[1]

                            logging.info('Recall Link given by user: %s',
                                         str(self.recall_service))
                            logging.info(
                                'Recall link retrieved from stub: %s',
                                str(embedded_recall_link))

                            if msg2[index2].message_class == "IPM.Note":
                                if msg1[index2].message_class != "IPM.Note.CommVault.Galaxy.Stub" \
                                        or msg1[index2].cv_stub.find(v11_cv_stub_parameter) < 0\
                                        or msg1[index2].cv_dataheader is None\
                                        or str(_recall_link_user_guid) \
                                        != str(policy_dict['userGuid'])\
                                        or str(self.recall_service) != str(embedded_recall_link):
                                    logging.info(
                                        "*Error* Eligible for Cleanup: But Message not Stubbed")
                                    return False  # Discontinue Validation

                                logging.info("Eligible for cleanup: Message got stubbed."
                                             "Validated the message")
                                # Continue Validation
                        else:
                            logging.debug("***********NOT ELIGIBLE FOR CLEANUP*****")
                            if msg2[index2].message_class == "IPM.Note":
                                if msg1[index2].message_class == "IPM.Note.CommVault.Galaxy.Stub"\
                                        or msg1[index2].cv_stub is not None\
                                        or msg1[index2].cv_dataheader is not None:
                                    logging.info(
                                        "*Error* Not Eligible for Cleanup:"
                                        " Message has been wrongly stubbed")
                                    logging.info("Message class after cleanup: %s",
                                                 str(msg1[index2].message_class))
                                    logging.info("CV Stub value after cleanup: %s",
                                                 str(msg1[index2].cv_stub))
                                    logging.info("CV Dataheader after cleanup: %s",
                                                 str(msg1[index2].cv_dataheader))
                                    return False  # Discontinue Validation

                                logging.info("Not Eligible for Cleanup:Message did not "
                                             "get stubbed.Validated the message")
                                # Continue Validation

                            logging.info("Message class is not IPM.Note This is"
                                         " not eligible for cleanup")
                            # Continue Validation
            return True

        except Exception as excp:
            self.log.exception('Exception during validation of mailboxes after Cleanup')
            raise excp

    def add_users_with_end_users_role(self, mailbox_smtp):
        """Adding Users under Security with EndUser role
            Args:
                mailbox_smtp --  Users STMP address
        """

        name = mailbox_smtp.split('@')[0]
        domain = mailbox_smtp.split('@')[1]
        domain1 = domain.split('.')[0]
        login_name = f'{domain1}\\{name}'

        mailbox_password = base64.b64decode(CONSTANT.DEFAULT_WEBCONSOLE)
        # Delete user from Users tab under Securitybuilder
        try:
            ret = self.tc_object.commcell.users.delete(login_name, "admin")
            self.log.info(ret)
            self.log.info("Deleted User from Security")
        except Exception:
            self.log.exception("User could not be deleted")

        # Adding Users under Security

        security_dict = {
            'assoc1':
                {
                    'clientName': [self.client_name],
                    'role': ['End Users']
                }
        }
        user_obj = self.tc_object.commcell.users.add(
            name, name, mailbox_smtp, domain=domain1,
            password=mailbox_password, entity_dictionary=security_dict)
        self.log.info(user_obj)
        self.log.info("Added the user to security")

    def validate_recall(self, before_cleanup, after_cleanup):
        """
            Validate if messages are recall link after cleanup job

            Args:
                before_cleanup --  Object of Exchangelib before cleanup

                after_cleanup --  Object of ExchangeLib after cleanup

            Raises:
                Exception:
                    If an error occurred during validation
        """
        try:

            # File to store the message body
            _body_file = os.path.join(CONSTANT.RETRIEVED_FILES_PATH, "MessageBody.txt")

            # Fetching the mailbox name
            self.log.info("Mailboxes before cleanup: ")
            self.log.info(before_cleanup)
            self.log.info("Mailboxes after cleanup: ")
            self.log.info(after_cleanup)

            # for mailbox_name in before_cleanup:
            for (key_before_cleanup, value_before_cleanup), (
                    key_after_cleanup, value_after_cleanup) in \
                    zip(before_cleanup.items(), after_cleanup.items()):
                logging.info('\n')
                mailbox_name = key_before_cleanup
                self.log.info("Validating mailbox properties for: %s", mailbox_name)
                folders_list = []
                mailbox_password = base64.b64decode(CONSTANT.DEFAULT_WEBCONSOLE)

                name = mailbox_name.split('@')[0]
                domain = mailbox_name.split('@')[1]
                domain1 = domain.split('.')[0]
                login_name = f'{domain1}\\{name}'

                # Getting mailbox property objects before and after cleanup
                before_cleanup = value_before_cleanup
                after_cleanup = value_after_cleanup

                # Fetching Cleanup Policy values
                policy_dict = self.get_policy_values(mailbox_name)
                logging.info("Policy values in policy_dict: ")
                logging.info(policy_dict)

                # Delete user from Users tab under Securitybuilder
                try:
                    ret = self.tc_object.commcell.users.delete(login_name, "admin")
                    self.log.info(ret)
                    self.log.info("Deleted User from Security")
                except Exception:
                    self.log.exception("User could not be deleted")

                # Adding Users under Security

                security_dict = {
                    'assoc1':
                        {
                            'clientName': [self.client_name],
                            'role': ['End Users']
                        }
                }
                user_obj = self.tc_object.commcell.users.add(
                    name, name, mailbox_name, domain=domain1,
                    password=mailbox_password, entity_dictionary=security_dict)
                self.log.info(user_obj)
                self.log.info("Added the user to security")

                # Getting list of all folders before cleanup
                all_folders_before_cleanup = before_cleanup.folders
                for folder1 in all_folders_before_cleanup:
                    if hasattr(folder1, 'sub_folder'):
                        all_folders_before_cleanup.extend(folder1.sub_folder)

                # Getting list of all folders after cleanup
                all_folders_after_cleanup = after_cleanup.folders
                for folder1 in all_folders_after_cleanup:
                    if hasattr(folder1, 'sub_folder'):
                        all_folders_after_cleanup.extend(folder1.sub_folder)
                        folders_list.append(folder1.folder_name)

                # Traversing through each folder present in all_folders_before_cleanup
                for folder in all_folders_before_cleanup:
                    logging.info('\n')
                    logging.info(
                        "##################################################################")
                    logging.debug("FOLDER NAME: %s", folder.folder_name)

                    # Getting all messages in the folder before cleanup
                    msg2 = folder.messages
                    try:
                        index1 = folders_list.index(folder.folder_name)
                    except Exception:
                        self.log.error("%s - This Folder does not exist", str(folder.folder_name))
                        logging.error("%s - This Folder does not exist", str(folder.folder_name))
                        return False

                    # Getting all messages in the folder after cleanup
                    msg1 = all_folders_after_cleanup[index1].messages

                    # Storing search keys of all messages before cleanup
                    search_key_list = []
                    for index1 in range(0, len(msg2)):
                        search_key_list.append(msg2[index1].search_key)

                    for index2 in range(0, len(msg1)):
                        logging.info('\n')
                        logging.info("Search key after cleanup: %s", msg1[index2].search_key)

                        try:
                            index2 = search_key_list.index(msg1[index2].search_key)
                        except Exception:
                            self.log.info("%s : Mail is not present", str(msg1[index2].subject))
                            logging.info("%s : Mail is not present", str(msg1[index2].subject))
                            return False

                        logging.info(
                            "Search key before cleanup: %s",
                            msg2[index2].search_key)
                        logging.info("MESSAGE SUBJECT: %s", msg1[index2].subject)
                        logging.info("SUBJECT BEFORE CLEANUP: %s", msg2[index2].subject)
                        logging.info("Entry ID: %s", str(msg1[index2].entry_id))
                        logging.info("Message class before cleanup: %s",
                                     str(msg2[index2].message_class))

                        if (msg2[index2].message_class == "IPM.Note" and
                                self.check_cleanup_validity(msg2[index2], policy_dict)):
                            # Only the mails that are of IPM.Note message class and
                            # eligible for cleanup based on cleanup policy will be stubbed

                            logging.debug("**** ELIGIBLE FOR CLEANUP ****")

                            # Fetching the User GUID
                            logging.info("Fetching User Guid from the embedded recall link")
                            var1 = msg1[index2].cv_stub.split('mg=')
                            var2 = var1[1].split('&amp')

                            _recall_link_user_guid = base64.b64decode(var2[0])
                            _recall_link_user_guid = _recall_link_user_guid.decode()

                            logging.info("CV Stub value: %s", str(msg1[index2].cv_stub))
                            logging.info("CV Dataheader value: %s",
                                         str(msg1[index2].cv_dataheader))
                            logging.info("User GUID retrieved from CS DB: %s",
                                         str(policy_dict['userGuid']))
                            logging.info(
                                "_recall_link_user_guid retrieved from CVStub: %s",
                                _recall_link_user_guid)
                            logging.info("Message Class before Cleanup: %s",
                                         str(msg2[index2].message_class))
                            logging.info("Message Class after Cleanup: %s",
                                         str(msg1[index2].message_class))

                            # Write message body into file present in _body_file path
                            logging.info(
                                "Writing message body into file present in"
                                "<Commvault Folder>/Automation/Application/"
                                "Exchange/ExchangeMailbox/"
                                "RetrievedFiles/MessageBody.txt")

                            bodyfile = open(_body_file, "w", encoding="utf-8")
                            bodyfile.write(msg1[index2].body)
                            bodyfile.close()

                            # Read body from the file saved in above step
                            logging.info("Reading the body...")
                            with open(_body_file, 'r', encoding="utf-8") as content_file:
                                msg_body = content_file.read()

                            # Fetch the recall link
                            logging.info("Fetching the recall link")
                            htmlvar = msg_body
                            htmlvar = htmlvar.split('<a href=')
                            htmlvar = htmlvar[1].split('style')
                            htmlvar = htmlvar[0].split('/webconsole')
                            htmlvar = htmlvar[0].split('"')
                            embedded_recall_link = htmlvar[1]

                            # Fetch the cs param value
                            html_var = msg_body
                            cs_param_value = html_var.split('mg')[0].split('cs=')[
                                1].split('&amp;amp;')[0]
                            cs_param_value = cs_param_value.replace('&amp;', '')
                            logging.info("The csParamValue is: %s", str(cs_param_value))

                            logging.info('Recall Link given by user: %s',
                                         str(self.recall_service))
                            logging.info(
                                'Recall link retrieved from stub: %s',
                                str(embedded_recall_link))

                            if msg2[index2].message_class == "IPM.Note":
                                if (msg1[index2].message_class != "IPM.Note.CommVault.Galaxy.Stub"
                                        or msg1[index2].cv_stub.find(CONSTANT.CV_STUB_PARAMETER) < 0
                                        or msg1[index2].cv_dataheader is None
                                        or str(_recall_link_user_guid)
                                        != str(policy_dict['userGuid'])
                                        or str(self.recall_service) != str(embedded_recall_link)):
                                    logging.info(
                                        "*Error* Eligible for Cleanup: But Message not Stubbed")
                                    raise Exception(
                                        'Eligible for Cleanup: But Message not Stubbed')
                                    # Discontinue Validation
                                else:
                                    # Add code for recall link validation here
                                    preview_json = self.get_preview(_recall_link_user_guid,
                                                                    str(cs_param_value),
                                                                    mailbox_name, mailbox_password)
                                    if not preview_json:
                                        logging.info("Failure in getting preview")
                                        raise Exception("Failure in getting preview")
                                    logging.info("Preview JSON obtained is: ")
                                    logging.info(preview_json)
                                    self.compare_preview_and_mapi(preview_json, msg1[index2])

                        else:
                            logging.debug("***********NOT ELIGIBLE FOR CLEANUP*****")
                            if msg2[index2].message_class == "IPM.Note":
                                if (msg1[index2].message_class == "IPM.Note.CommVault.Galaxy.Stub"
                                        or msg1[index2].cv_stub is not None
                                        or msg1[index2].cv_dataheader is not None):
                                    logging.info("*Error* Not Eligible for Cleanup: "
                                                 "Message has been wrongly stubbed")
                                    logging.info("Message class after cleanup: %s",
                                                 str(msg1[index2].message_class))
                                    logging.info("CV Stub value after cleanup: %s",
                                                 str(msg1[index2].cv_stub))
                                    logging.info("CV Dataheader after cleanup: %s",
                                                 str(msg1[index2].cv_dataheader))
                                    raise Exception("Not eligible for clenaup")
                                    # Discontinue Validation
                                else:
                                    logging.info("Not Eligible for Cleanup: "
                                                 "Message did not get stubbed "
                                                 "Validated the message")
                                    # Continue Validation
                            else:
                                logging.info("Message class is not IPM.Note."
                                             "This is not eligible for cleanup")
                                # Continue Validation

        except Exception as excp:
            self.log.exception('Exception during validation of mailboxes after Cleanup')
            raise excp

    def compare_preview_and_mapi(self, preview_json, mapi_msg):
        """
            Compare preview Json and Mapi properties

            Args:
                preview_json --  Preview Api Json

                mapi_msg --  Mapi properties from ExchangeLib

            Raises:
                Exception:
                    If an error occurred during validation
        """

        # Fetch from , to and cc addresses from json returned by
        # preview API

        from_add = preview_json['from']
        to_add = preview_json['to']
        cc_flag = 0
        try:
            cc_add = preview_json['cc']
        except Exception:
            cc_flag = 1
            logging.info("No Cc addresses")
        from_addresses_recall = []
        to_addresses_recall = []
        cc_addresses_recall = []

        # Subject attained using preview API
        msg_subject = preview_json['subject'].strip().encode('utf8')
        logging.info("Subject obtained using API: %s", msg_subject)

        # Store all the display names of from, to and cc addresses
        # obtained from preview API in respective lists
        for address in from_add:
            from_addresses_recall.append(
                str(address['displayName'].strip()))

        if cc_flag == 0:
            for address in cc_add:
                cc_addresses_recall.append(
                    str(address['displayName'].strip()))

        for address in to_add:
            to_addresses_recall.append(
                str(address['displayName'].strip()))

        # Subject attained using Exchange lib
        mapi_subject = mapi_msg.subject.encode('utf8')
        logging.info(
            "Subject obtained from MAPI: %s", mapi_subject)

        # Lists to store from, to, cc addresses
        mapi_from_addresses = []
        mapi_to_addresses = []
        mapi_cc_addresses = []

        # Fetch from, to, cc addresses using Exchange Library
        mapi_from = mapi_msg.from_address
        mapi_to = mapi_msg.to_address
        mapi_cc = mapi_msg.cc_address

        # Append from, to, cc addresses in lists obtained using
        # Exchange Library
        for key in mapi_from:
            mapi_from_addresses.append(key)

        for key in mapi_to:
            mapi_to_addresses.append(key)

        for key in mapi_cc:
            mapi_cc_addresses.append(key)

        # Get message body from recall api
        logging.info("Getting message body from recall api")
        recall_body_location = os.path.join(CONSTANT.RETRIEVED_FILES_PATH,
                                            "recall_msg_body.txt")
        msg_body = preview_json['body'].encode('utf8')
        body_file = open(recall_body_location, "wb")
        body_file.write(msg_body)
        body_file.close()

        # Get message body from exchange lib
        logging.info("Getting message body from exchange lib")
        mapi_body_location = os.path.join(CONSTANT.RETRIEVED_FILES_PATH,
                                          "mapi_msg_body.txt")
        mapi_body = mapi_msg.txt_body
        mapi_body = mapi_body.encode('utf8')
        body_file = open(mapi_body_location, "wb")
        body_file.write(mapi_body)
        body_file.close()

        # Validate from addresses
        if from_addresses_recall.sort() != mapi_from_addresses.sort():
            self.log.info("From addresses do not match. Check logging "
                          "file for more details")
            logging.info("From addresses are not same")
            logging.info("From addresses obtained from Preview API:")
            logging.info(from_addresses_recall)
            logging.info("From addresses obtained from Exchange:")
            logging.info(mapi_from_addresses)
            raise Exception("From addresses do not match")

        # Validate to addresses
        if to_addresses_recall.sort() != mapi_to_addresses.sort():
            self.log.info("To addresses do not match. Check logging "
                          "file for more details")
            logging.info("To addresses are not same")
            logging.info("To addresses obtained from Preview API:")
            logging.info(to_addresses_recall)
            logging.info("To addresses obtained from Exchange:")
            logging.info(mapi_to_addresses)
            raise Exception("To addresses do not match")

        # Validate cc addresses
        if cc_addresses_recall.sort() != mapi_cc_addresses.sort():
            self.log.info("Cc addresses do not match. "
                          "Check logging file for more details")
            logging.info("Cc addresses are not same")
            logging.info("Cc addresses obtained from Preview API:")
            logging.info(cc_addresses_recall)
            logging.info("Cc addresses obtained from Exchange:")
            logging.info(mapi_cc_addresses)
            raise Exception("Cc addresses do not match")

        # Validate subjects
        if msg_subject != mapi_subject:
            self.log.info("Subject does not match."
                          " Check logging file for more details")
            logging.info("Subject are not same")
            logging.info("Subject obtained from Preview API: %s", msg_subject)
            logging.info("Subject obtained from Exchange: %s", mapi_subject)
            raise Exception("Subject does not match")

        # Validate message bodies
        ret = self.validate_msg_bodies(
            recall_body_location, mapi_body_location)
        if not ret:
            raise Exception("Message bodies do not match")
        logging.info(
            "Eligible for cleanup:"
            " Message got stubbed. Validated the message")
        # Continue Validation

    def check_cleanup_validity(self, obj_before, policy_dict):
        """
            Method to check if a message is eligible for Cleanup job based
            on the message rules of the Cleanup Policy.

            Args:
                obj_before --  Object of Exchangelib before backup

                policy_dict --  Dict containing the values of Cleanup Policy

            Returns:
                True if message is eligible for cleanup

        """

        try:
            logging.debug("*****Checking if this item is "
                          "eligible for cleanup*****")
            logging.debug(policy_dict)

            logging.debug('Cleanup Rule - Enable Message Rules: '
                          '%s', str(policy_dict['EnableMsgRules']))
            if policy_dict['EnableMsgRules'] != "1":
                logging.info("Message rules not enabled")
                return False

            logging.debug('Cleanup Rule - Collect Message with Attachment: '
                          '%s', str(policy_dict['MsgsWithAttachment']))
            if policy_dict['MsgsWithAttachment'] == "1":
                if not obj_before.attachment_details:
                    logging.info(
                        "Attachments not Present in this mail, so not eligible for cleanup")
                    return False

            logging.debug('Cleanup rule - Skip Unread Messages: %s',
                          str(policy_dict['SkipUnread']))
            logging.debug('Is mail read?: %s', str(obj_before.is_read))
            if policy_dict['SkipUnread'] == "1":
                if not obj_before.is_read:
                    logging.info("Message is unread, so not eligible")
                    return False

            logging.debug("Cleanup rule - Cleanup Messages Larger Than: %s",
                          str(int(policy_dict['MsgsLargerThan']) * 1024))
            logging.debug("Message Size: %s", str(obj_before.message_size))
            if (int(policy_dict['MsgsLargerThan']) * 1024) > int(obj_before.message_size):
                logging.debug("Message size is lesser, so not eligible for cleanup")
                return False

            # Fetching time and converting GMT to local time
            no_of_days = utils.calculate_duration(obj_before.received_time)

            logging.debug("Number of days: %s", str(no_of_days))
            logging.debug("Include messages older than: %s",
                          str(policy_dict['CollectDaysAfter']))
            if int(policy_dict['CollectDaysAfter']) > int(no_of_days):
                logging.debug(
                    "Number of days is lesser than message rule,"
                    " so not eligible for Cleanup")
                return False

            logging.info("Message is qualified for Cleanup job")
            return True

        except Exception as excp:
            self.log.exception("Exception occurred while checking"
                               "if the message is valid for cleanup")
            raise excp

    def get_policy_values(self, mailbox_name):
        """
            Method to get values of cleanup policy associated to mailbox

            Args:
                mailbox_name  (str)  --  Mailbox name associated to subclient

                Returns:
                    policy_dict (dict) -- Dict of policy values

        """

        # Fetch Client ID
        client_id = self.tc_object.commcell.clients.all_clients[self.client_name.lower()]['id']

        # Fetch User GUID
        _user_guid_query = "select userGuid from APP_EmailConfigPolicyAssoc where " \
            "smtpAdrress = '%s' and clientId = '%s'" % (mailbox_name, client_id)
        self.csdb.execute(_user_guid_query)
        _user_guid_results = self.csdb.fetch_one_row()
        user_guid = _user_guid_results[0]

        # Fetch Policy ID
        _query1 = "select policyId from APP_EmailConfigPolicies where " \
                  "policyType = 2 and componentNameId " \
                  "IN (select assocId from APP_EmailConfigPolicyAssoc where clientId = '%s' " \
                  "and smtpAdrress = '%s' and modified = 0 )" % (client_id, mailbox_name)
        self.csdb.execute(_query1)
        _results1 = self.csdb.fetch_one_row()

        # Fetch Policy details of Exchange Configuration Policy
        _query2 = ("select policyDetails from APP_ConfigurationPolicyDetails"
                   " where  modified = 0 and componentNameId ='%s' " % _results1[0])
        self.csdb.execute(_query2)
        _results2 = self.csdb.fetch_one_row()

        policy_xml = _results2[0]
        policy_dict = {}

        policy_dict['userGuid'] = user_guid

        # Getting the message rules based on the Policy XML retrieved from the CS DB
        # Converting XML into Dict
        dict_of_base_xml = OrderedDict(parse(policy_xml, process_namespaces=True))
        add_recall_link = dict_of_base_xml['emailPolicy'][
            'cleanupPolicy']['@addRecallLink']
        policy_dict['RecallLink'] = str(add_recall_link)

        collect_msgs_days_after = dict_of_base_xml['emailPolicy'][
            'cleanupPolicy']['@collectMsgsDaysAfter']
        policy_dict['CollectDaysAfter'] = str(collect_msgs_days_after)

        collect_msgs_larger_than = dict_of_base_xml['emailPolicy'][
            'cleanupPolicy']['@collectMsgsLargerThan']
        policy_dict['MsgsLargerThan'] = str(collect_msgs_larger_than)

        collect_msg_with_attach = dict_of_base_xml['emailPolicy'][
            'cleanupPolicy']['@collectMsgWithAttach']
        policy_dict['MsgsWithAttachment'] = str(collect_msg_with_attach)

        skip_unread_msgs = dict_of_base_xml['emailPolicy'][
            'cleanupPolicy']['@skipUnreadMsgs']
        policy_dict['SkipUnread'] = str(skip_unread_msgs)

        enable_message_rules = dict_of_base_xml['emailPolicy'][
            'cleanupPolicy']['@enableMessageRules']
        policy_dict['EnableMsgRules'] = str(enable_message_rules)

        leave_msg_body = dict_of_base_xml['emailPolicy'][
            'cleanupPolicy']['@leaveMsgBody']
        policy_dict['LeaveMsgBody'] = str(leave_msg_body)

        create_stubs = dict_of_base_xml['emailPolicy'][
            'cleanupPolicy']['@createStubs']
        policy_dict['CreateStubs'] = str(create_stubs)

        prune_msgs = dict_of_base_xml['emailPolicy'][
            'cleanupPolicy']['@pruneMsgs']

        policy_dict['PruneMsgs'] = str(prune_msgs)

        prune_stubs = dict_of_base_xml['emailPolicy'][
            'cleanupPolicy']['@pruneStubs']

        policy_dict['PruneStubs'] = str(prune_stubs)

        pruning_days = dict_of_base_xml['emailPolicy'][
            'cleanupPolicy']['@numOfDaysForSourcePruning']

        policy_dict['PrunningDays'] = str(pruning_days)

        return policy_dict

    def check_cleanup_source_prunning_eligibility(self, message, policy_dict):
        """
            Method to check if a message is eligible for source pruning  based on the message rules
            of the Cleanup Policy If any of the rule fails, the module returns false

             Args:
                    Message (CVMessage) --  Message properties object

                    policy_dict (dict)  --  Dict of policy values

            Returns:
                    True on success

        """

        try:
            logging.info('\n')
            logging.debug("*****Checking Validation*****")

            logging.debug("PruneMsgs: %s", str(policy_dict['PruneMsgs']))
            logging.debug("PruneStubs: %s", str(policy_dict['PruneStubs']))
            if policy_dict['PruneMsgs'] != "1" and policy_dict['PruneStubs'] != "1":
                logging.info("Source prunning is not enabled")
                return False

            logging.debug("collectMsgWithAttach: %s", str(policy_dict['PruneStubs']))
            if policy_dict['PruneMsgs'] == "1":
                if not message.message_class == "IPM.Note":
                    logging.info("Attachments not Present in this mail, so not "
                                 "eligible for cleanup")
                    return False

            logging.debug("skipUnreadMsgs: %s", str(policy_dict['PruneStubs']))
            logging.debug("Is mail read?: %s", str(message.is_read))
            if policy_dict['PruneStubs'] == "1":
                if not message.message_class == "IPM.Note.CommVault.Galaxy.Stub":
                    logging.info("Attachments not Present in this mail, so not "
                                 "eligible for cleanup")
                    return False
            no_of_days = utils.calculate_duration(message.received_time)
            logging.debug("Number of days: %s", str(no_of_days))
            logging.debug("PrunningDays %s", str(policy_dict['PrunningDays']))
            if int(policy_dict['PrunningDays']) > int(no_of_days):
                logging.debug("Number of days is lesser than Pruning Days, so not "
                              "eligible for source prunning")
                return False
            return True

        except Exception as excp:
            self.log.exception('An error occurred while checking source prunning validaty ')
            raise excp

    @staticmethod
    def split_by_length(cs_val, max_length):
        """
            Method to split CS value from recall link to get docId

            Args:
                cs_val --  cs value in recall link

                max_length --  max length to split the value

            Returns:
                List containing values that are split based on max_length value

        """
        index = 0
        ret_list = []
        while index < len(cs_val):
            val = cs_val[index:index + min(max_length, len(cs_val) - index)]
            ret_list.append(str(val))
            index += max_length
        return ret_list

    def extract_turboguid(self, cs_param_value):
        """Method to get the turbo guid based on cs value in recall link
            Args:
                cs_val --  cs value in recall link

            Returns:
                Turbo GUID"""
        turboguid = ""
        max_length = 8

        logging.info("In extract_turboguid()")

        cs_param_value = cs_param_value + "="
        cs_param_value = base64.b64decode(cs_param_value).decode('UTF-8')
        logging.info("cs_param_value: %s", cs_param_value)

        index = 0
        components = self.split_by_length(cs_param_value, max_length)
        for component in components:
            index += 1
            if (index % 2) != 0:
                turboguid += str(component)
        logging.info("Turboguid: %s", turboguid)
        return turboguid

    def get_preview(self, recall_link_user_guid, cs_param_value, smtp_address, password):
        """Method to get the preview from recall link guid
            Args:
                recall_link_user_guid --  UserGuid associated to email

                cs_param_value        --  cs value in recall link

                smtp_address          --  email of the user

                password              --  password of the user to be

            Returns:
                json        -   preview json of an email"""
        try:
            logging.info("In get_preview()")

            if not self.tc_object.subclient.subclient_id:
                raise Exception("Subclient ID could not be fetched")
            doc_id = self.extract_turboguid(str(cs_param_value))
            logging.info("docID: %s", doc_id)

            # request() in commcell.py of pysdk
            preview_url = CONSTANT.SERVICES_DICT_TEMPLATE['PREVIEW_URL'] % (
                doc_id,
                self.tc_object.subclient.subclient_id,
                recall_link_user_guid
            )
            # preview_url = ("/Email/message/Preview?docId=" + str(doc_id) + r"&appId="
            #                + str(subclient_id) + r"&commcellId=2&guid=" +
            #                str(recall_link_user_guid))
            logging.info("URL to get the preview: %s", str(preview_url))
            preview_url = str(preview_url)

            # Login to webconsole and get auth token
            commcell_preview_obj = Commcell(self.tc_object.commcell.commserv_hostname,
                                            smtp_address, password.decode("utf-8"))

            # GET request to get the preview
            preview_response = commcell_preview_obj.request("GET", preview_url)

            logging.info("Returned token from get_preview:")
            logging.info(preview_response)
            final_json = preview_response.json()
            return final_json

        except Exception as excp:
            self.log.exception('Exception while getting the preview of a mail')
            raise excp

    def validate_msg_bodies(self, recall_body_location, mapi_body_location):
        """This function divides the contents of paragraph tags in recall body and
        actual body into lists of individual words
            Args:

                recall_body_location    --  body obtained from recall api

                mapi_body_location      --  body obtained from exchange"""
        try:
            logging.info("In get_message_bodies_lists")
            final_content_recall = []
            final_content_mapi = []

            # Divide message body obtained from recall API

            # read the body
            with open(recall_body_location, 'r', encoding='utf-8') as myfile:
                data = myfile.read()
            myfile.close()

            soup = BeautifulSoup(data, 'lxml')
            p_tags = soup.find_all('p')

            # Write the text between <p> tags into same file
            body_file = open(recall_body_location, "wb")
            for i in range(0, len(p_tags)):
                body_file.write(p_tags[i].getText().encode('utf8'))
            body_file.close()

            with open(recall_body_location, encoding='utf-8') as file:
                content = file.readlines()
            content = [content_line.strip() for content_line in content]
            content = [content_line.split() for content_line in content]

            for list1 in content:
                final_content_recall = final_content_recall + list1

            # Divide message body obtained from Exchange

            # read the body
            with open(mapi_body_location, encoding='utf-8') as file:
                content1 = file.readlines()
            content1 = [content_line.strip() for content_line in content1]
            content1 = [content_line.replace('\xa0', '') for content_line in content1]
            content1 = [content_line.split() for content_line in content1]

            for list2 in content1:
                final_content_mapi = final_content_mapi + list2

            for i in range(0, 3):
                final_content_mapi.pop(0)

            flag1 = 0

            for recall_body in final_content_recall:
                if recall_body not in final_content_mapi:
                    flag1 += 1
                    logging.info("Failed words: %s", recall_body)

            if flag1 > 30:
                raise Exception("Too many differences in message bodies obtained from recall link and exchange. "
                                "Please check logging file- 51449_helper.log for the differences")

        except Exception as excp:
            self.log.exception("Exception in get_message_bodies_list(): %s", excp)
            raise excp

    def validate_journal_delete(self, before_cleanup_dict, after_cleanup_dict):
        """Validate message are deleted during clenaup job
            Args:
                before_cleanup_dict --  Exchangelib before backup object
                after_cleanup_dict  --  ExchangeLib after backup object"""

        for mailbox_name in before_cleanup_dict:
            before_cleanup = before_cleanup_dict[mailbox_name]
            after_cleanup = after_cleanup_dict[mailbox_name]
            folders_list = []
            all_folders_before_cleanup = before_cleanup.folders
            for folder in all_folders_before_cleanup:
                if hasattr(folder, 'sub_folder'):
                    all_folders_before_cleanup.extend(folder.sub_folder)
            # Getting list of all folders after cleanup
            all_folders_after_cleanup = after_cleanup.folders
            for folder in all_folders_after_cleanup:
                if hasattr(folder, 'sub_folder'):
                    all_folders_after_cleanup.extend(folder.sub_folder)
                    folders_list.append(folder.folder_name)
            # Traversing through each folder present in all_folders_before_cleanup
            for folder in all_folders_before_cleanup:
                self.log.info("\n################################################")
                self.log.debug("FOLDER NAME: " + folder.folder_name)
                # log.info("Folder name:"+folder.folder_name)

                # Getting all messages in the folder before cleanup
                msg2 = folder.messages
                try:
                    index1 = folders_list.index(folder.folder_name)
                except BaseException:
                    self.log.error(str(folder.folder_name) + "Folder does not exist")
                    raise Exception("Unable to validate journal mailbix cleanup")

                # Getting all messages in the folder after cleanup
                msg1 = all_folders_after_cleanup[index1].messages

                # Storing search keys of all messages before cleanup
                search_key_list = []
                for msg, value in enumerate(msg2):
                    search_key_list.append(msg2[msg].search_key)

                # In case of Delete Messages option checkedin in cleanup policy,
                    # see if message is eligible for cleanup

                self.log.info("\nDelete Messages Enabled")
                search_key_list_after_cleanup = []

                # Storing search keys of mailbox after cleanup, if any
                if msg1:
                    for msg, value in enumerate(msg1):
                        search_key_list_after_cleanup.append(msg1[msg].search_key)
                        self.log.info("Search key that is being added into list: '{0}'"
                                      "".format(str(msg1[msg].search_key)))

                for msg in msg2:

                    self.log.info("\nSubject: " + str(msg.subject.encode('utf8')))
                    self.log.info("Search Key: " + str(msg.search_key))

                    if msg.search_key in search_key_list_after_cleanup:
                        self.log.info(
                            "This mail has not been deleted although Delete Message is "
                            "enabled in cleanup policy")
                        raise Exception("Unable to validate journal mailbix cleanup")
                    else:
                        self.log.info("ELIGIBLE: Validated the message")
