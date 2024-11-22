# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Class:
TrueUp - Class for running true up job and validating whether message deleted on the mailboxes
are masked in the solr index

TrueUp:

    __init__                            --- initializes TrueUp object

    validate_true_up                    --- Method to validate messages deleted from mailboxes
                                            are masked in the solr index

    validate_deletion_time_based_retention  --- Method to validate received time and deletion time
                                                based retention

    is_sync_process_running             --- Checks for sync process

    wait_for_sync_process_to_exit       --- waits till sync process exits gracefully

"""

import time
from datetime import datetime, timedelta, timezone
from AutomationUtils.machine import Machine
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.ExchangeMailbox.retention_options import Retention
from .constants import SolrDocumentType, SolrDocumentCIState
from . import constants


class TrueUp:
    """Class for performing TrueUp related operations."""

    def __init__(self, ex_object):
        """
            Initializes the TrueUp object.

            Args:
                ex_object  (Object)  --  instance of ExchangeMailbox module

            Returns:
                object  --  instance of TrueUp class

        """
        self.tc_object = ex_object.tc_object
        self.ex_object = ex_object
        self.log = self.tc_object.log
        self.app_name = self.__class__.__name__
        self.mail_users = ex_object.users
        self.csdb = ex_object.csdb
        self.retention = Retention(ex_object)

    def validate_true_up(self, true_up_object):
        """ This method verifies messages deleted from mailboxes are masked in the solr index
            Args:
                true_up_object(dictionary)         --  Number of messages to delete

            Raises exception if validation fails

        """
        try:
            # Initialize solr
            solr = SolrHelper(self.ex_object)
            is_solr_standalone = solr.is_solr_standalone()
            fl = ('objectEntryId' if is_solr_standalone else 'ObjectEntryId')

            # Check for deleted messages on all mailbox
            for mailbox_name in true_up_object:
                true_up_list = true_up_object[mailbox_name]
                self.log.info('Validating MAILBOX: %s', mailbox_name)
                is_delete_retention_policy = self.retention.is_delete_retention_policy_assigned(
                    mailbox_name)
                self.log.info("Is delete retention policy assigned : %s"
                              % is_delete_retention_policy)
                mailbox_user_guid = self.retention.get_mailbox_user_guid(mailbox_name)
                mailbox_user_guid = mailbox_user_guid.lower()
                self.log.info("mailbox user guid: %s" % mailbox_user_guid)

                # Query solr
                keyword = ['IsVisible', 'DocumentType', 'ItemState', 'OwnerId']
                if is_solr_standalone:
                    keyword = ['visible', 'datatype', 'cistate', 'cvowner']
                s_dict = {solr.keyword_for_client_id: solr.client_id,
                          keyword[0]: True,
                          keyword[1]: constants.SolrDocumentType.MESSAGE.value,
                          keyword[2]: constants.SolrDocumentCIState.TRUE_UP.value,
                          keyword[3]: mailbox_user_guid}
                self.log.info(s_dict)
                output = solr.get_result_of_custom_query(s_dict, [fl])
                num_found = output["total_records"]

                # Validate based on retention policy type
                if is_delete_retention_policy:
                    # Validating count
                    if num_found != len(true_up_list):
                        self.log.info("Total records with TrueUp status in solr: %s" % num_found)
                        self.log.info("Total records in TrueUp list: %s" % len(true_up_list))
                        raise Exception("TrueUp list count doesn't match with solr index count")

                    # Validating messages
                    results = output["result"]
                    for result in results.values():
                        if result[fl] not in true_up_list:
                            self.log.exception("EntryId: %s not found in TrueUp list" % result[fl])
                            raise Exception("EntryId: %s not found in TrueUp list" % result[fl])
                else:
                    if num_found != 0:
                        self.log.info("Found records in solr with TrueUp Status: %s" % num_found)
                        raise Exception("TrueUp job masked few messages")

        except Exception as excp:
            self.log.exception('An error occurred while validating true up')
            raise excp

    def validate_deletion_time_based_retention(self, true_up_object):
        """Helper method to validate retention
            Args:
                true_up_object(dictionary)         --  Number of messages to delete

            Raises:
                Exception if retention validation fails
        """
        try:
            before_retention = {}

            # Initialize solr
            solr = SolrHelper(self.ex_object)
            is_solr_standalone = solr.is_solr_standalone()

            # Check for deleted messages on all mailbox
            for mailbox_name in true_up_object:
                self.log.info('Validating MAILBOX: %s', mailbox_name)
                is_delete_retention_policy = self.retention.is_delete_retention_policy_assigned(
                    mailbox_name)
                self.log.info("Is delete retention policy assigned : %s"
                              % is_delete_retention_policy)
                days_for_media_pruning = self.retention.get_number_of_days_for_media_pruning(
                    mailbox_name)
                days_for_media_pruning = int(days_for_media_pruning)
                self.log.info("Number of days for media pruning : %s"
                              % days_for_media_pruning)
                mailbox_user_guid = self.retention.get_mailbox_user_guid(mailbox_name)
                mailbox_user_guid = mailbox_user_guid.lower()

                # Validate based on retention policy type
                if is_delete_retention_policy:
                    keyword = ['DateDeleted', 'IsVisible', 'DocumentType', 'ItemState', 'OwnerId']
                    if is_solr_standalone:
                        keyword = ['datedeleted', 'visible', 'datatype', 'cistate', 'cvowner']
                    valid_time = datetime.now(tz=timezone.utc) - timedelta(
                        days=days_for_media_pruning)
                    date_deleted_valid = (
                        f'{valid_time.year}-{valid_time.month}-{valid_time.day}T{valid_time.hour}'
                        f':{valid_time.minute}:{valid_time.second}Z')
                    s_dict = {solr.keyword_for_client_id: solr.client_id,
                              keyword[0]: f'[* TO {date_deleted_valid}]',
                              keyword[1]: True,
                              keyword[2]: constants.SolrDocumentType.MESSAGE.value,
                              keyword[3]: constants.SolrDocumentCIState.TRUE_UP.value,
                              keyword[4]: mailbox_user_guid}
                    response = solr.create_url_and_get_response(
                        s_dict, None, {"rows": 0})
                    item_count = solr.get_count_from_json(response.content)
                    self.log.info("Total number of items eligible for deleted: %d" % item_count)

                    # Collect
                    before_retention[mailbox_user_guid] = item_count
                else:
                    keyword = ['ReceivedTime', 'IsVisible', 'DocumentType', 'OwnerId']
                    if solr.is_solr_standalone():
                        keyword = ['mtm', 'visible', 'datatype', 'cvowner']
                    valid_time = datetime.now(
                        tz=timezone.utc) - timedelta(days=days_for_media_pruning + 1)
                    mtm_valid = (
                        f'{valid_time.year}-{valid_time.month}-{valid_time.day}T{valid_time.hour}'
                        f':{valid_time.minute}:{valid_time.second}Z')
                    s_dict = {solr.keyword_for_client_id: solr.client_id,
                              keyword[0]: f'[* TO {mtm_valid}]',
                              keyword[1]: True,
                              keyword[2]: 2,
                              keyword[3]: mailbox_user_guid}
                    response = solr.create_url_and_get_response(s_dict, None, {"rows": 0})
                    item_count = solr.get_count_from_json(response.content)
                    self.log.info("Total number of items eligible for deleted: %d" % item_count)

                    # Collect
                    before_retention[mailbox_user_guid] = item_count

            # Run retention
            self.ex_object.cvoperations.run_retention()
            time.sleep(120)

            # After running retention compare with actual numbers
            for mailbox_user_guid in before_retention:
                keyword = ['IsVisible', 'DocumentType', 'OwnerId']
                if solr.is_solr_standalone():
                    keyword = ['visible', 'datatype', 'cvowner']
                s_dict = {solr.keyword_for_client_id: solr.client_id,
                          keyword[0]: False,
                          keyword[1]: 2,
                          keyword[2]: mailbox_user_guid}
                response = solr.create_url_and_get_response(s_dict, None, {"rows": 0})
                json_num = solr.get_count_from_json(response.content)
                self.log.info("Total number of items after applying retention: %d" % json_num)

                if before_retention[mailbox_user_guid] != json_num:
                    self.log.exception("Expected with retention: %d"
                                       % before_retention[mailbox_user_guid])
                    self.log.exception("Actual after running retention: %d " % json_num)
                    raise Exception("Exception occured while validating retention")

        except Exception as excp:
            self.log.exception("Exception occured while validating retention")
            raise excp

    def is_sync_process_running(self):
        """ Method to check if sync process is running
            Raises:
                Exception:
                    If sync process doesn't get launched within stipulated  time

        """
        try:
            machine = Machine(self.ex_object.proxies[0], self.ex_object.commcell)
            result = machine.is_process_running(constants.TRUE_UP_PROCESS_EXE,
                                                constants.SYNC_PROCESS_WAIT_TIME,
                                                constants.SYNC_PROCESS_POLL_INTERVAL)
            if not result:
                self.log.exception("Sync process didn't initiated within time: %d secs"
                                   % constants.SYNC_PROCESS_WAIT_TIME)
                raise Exception("Sync process didn't initiated within time: %d secs"
                                % constants.SYNC_PROCESS_WAIT_TIME)
        except Exception as excp:
            self.log.exception("An error occurred while checking is sync process running")
            raise excp

    def wait_for_sync_process_to_exit(self):
        """ Method will wait for the process to exit gracefully
            Raises:
                Exception:
                    If sync process doesn't exit gracefully with in stipulated time

        """
        try:
            machine = Machine(self.ex_object.proxies[0], self.ex_object.commcell)
            result = machine.wait_for_process_to_exit(constants.TRUE_UP_PROCESS_EXE,
                                                      constants.SYNC_PROCESS_WAIT_TIME,
                                                      constants.SYNC_PROCESS_POLL_INTERVAL)
            if not result:
                self.log.exception("Sync process didn't exited within: %d sec"
                                   % constants.SYNC_PROCESS_WAIT_TIME)
                raise Exception("Sync process didn't exited within: %d secs"
                                % constants.SYNC_PROCESS_WAIT_TIME)
        except Exception as excp:
            self.log.exception("An error occurred while waiting for sync process to exit")
            raise excp
