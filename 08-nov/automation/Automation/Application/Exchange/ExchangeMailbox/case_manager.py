# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main Module for setting input variables and creating objects of all other modules.
This module is imported in any test case.
You need to create an object of this module in the test case.

CaseManager: Class for initializing input variables and other module objects.

"""

from __future__ import unicode_literals
from AutomationUtils.cvtestcase import CVTestCase
from .operations import CvOperation
from . import constants


class CaseManager():
    """Class for initializing input variables and object creation from different modules"""

    def __init__(self, tc_object):
        """Initializes the input variables,logging and creates object from other modules.

            Args:
                tc_object   --  instance of testcase class

            Returns:
                object  --  instance of CaseManager class

        """
        self.tc_object = tc_object
        self.log = self.tc_object.log
        self.log.info('logger initialized for CaseManger')
        self.app_name = self.__class__.__name__
        self._users = None
        self._active_directory = None
        self._exchange_lib = None
        self.csdb = self.tc_object.csdb
        self.populate_tc_inputs(tc_object)

        self._cvoperations = None

    def __repr__(self):
        """Representation string for the instance of CaseManger class."""

        return 'CaseManager class instance for Commcell'

    def populate_tc_inputs(self, tc_object):
        """Initializes all the test case inputs after validation

        Args:
            tc_object (obj)    --    Object of CVTestCase
        Returns:
            None
        Raises:
            Exception:
                if a valid CVTestCase object is not passed.
                if CVTestCase object doesn't have agent initialized"""
        if not isinstance(tc_object, CVTestCase):
            raise Exception(
                "Valid test case object must be passed as argument"
            )
        self.tc_inputs = tc_object.tcinputs
        self.client_name = constants.CASE_CLIENT_NAME % (tc_object.id)
        self.commcell = tc_object.commcell
        self.subclient_name = tc_object.tcinputs.get('SubclientName')
        self.backupset_name = tc_object.tcinputs.get('BackupsetName')
        self.index_server = tc_object.tcinputs.get('CaseIndexServer')

        self.server_plan = tc_object.tcinputs.get("ServerPlan")
        self.dc_plan = tc_object.tcinputs.get("DCPlan")
        self.hold_type = tc_object.tcinputs.get("HoldType")

    @property
    def cvoperations(self):
        """Returns the instance of the CvOperation class."""
        if self._cvoperations:
            return self._cvoperations
        self._cvoperations = CvOperation(self)
        return self._cvoperations

    def get_custodian_list(self, ex_subclient_object, mailboxes):
        """Get custodian list
            Args:
                ex_subclient_object  (subclient)  --  Exchange Subclient object

                mailboxes            (list)       --   list of mailboxes

            Returns:
                custodian_info_list, guids (tuple) -- returns custodian_info list

        """
        custodian_info_list = []
        guids = []
        self.log.info("Getting Custodians")
        for user in ex_subclient_object.users:
            if user['display_name'] in mailboxes:
                guids.append(user['user_guid'].lower())
                guid = user['user_guid'].replace("X", '-').lower()
                custodian_info = {
                    "smtp": user['smtp_address'],
                    "name": user['display_name'],
                    "guid": guid
                }
                custodian_info_list.append(custodian_info)

        self.log.info(custodian_info_list)
        return custodian_info_list, guids

    def get_custodian_list_with_smtp(self, mailboxes):
        """Get users from mailbox smtp

            Args:
                mailboxes        (list)        --  list of mailboxes

            Returns:

                custodian_info_list (list)     --  returns custodian_info list"""
        custodian_info_list = []
        self.log.info("Getting Custodians")
        for user in mailboxes:
            custodian_info = {
                "smtp": user,
                "name": "",
                "guid": ""
            }
            custodian_info_list.append(custodian_info)

        self.log.info(custodian_info_list)
        return custodian_info_list

    def add_case_and_definition(self, custodian_info_list, email_filters=None):
        """Create case and add defination to the case

            Args:
                custodian_info_list  (list)  --  list of custodians

        """
        self.log.info("-------------------CREATING CASE-----------------")
        self.client = self.cvoperations.add_case_client()
        self.subclient = self.cvoperations.subclient
        self.log.info("------------------ADDING DEFINITION--------------")
        self.subclient.add_definition(
            constants.DEFINITION_NAME,
            custodian_info_list,
            email_filters)
        self.log.info("Definition added")

    def validate_index_copy(self, source_solr, destination_solr, guids):
        """Validate Index Copy Job
            Args:
                source_solr       (dict) --  user guid as key and index records as value

                destination_solr  (dict) --  user guid as key and index records as value

                guids             (str)  --  mailbox guids

        """

        source_results = source_solr.get_items_for_users(guids)
        destination_results = destination_solr.get_items_for_users(guids)
        standalone_solr = False
        if source_solr.type == constants.SOLR_TYPE_DICT[1]:
            standalone_solr = True
        self.log.info("Source is standalone %s", standalone_solr)
        self.compare_solr_results(source_results, destination_results, standalone_solr)

    def validate_data_copy(self, destination_solr, job_id):
        """Validate data copy job
            Args:
                destination_solr   --  destination solr object

                job_id             --  data copy job id

        """
        try:

            facet_fields = {
                'facet.field': 'AchiveFileId',
                'facet': 'on'
            }
            solr_results = destination_solr.get_result_of_custom_query(
                {'DocumentType': 2}, op_params=facet_fields)
            self.log.info("Getting number of items in job %s from database" % job_id)
            query_string = "select id from archFile Where name = 'Not Named' and jobId=%s" % job_id
            self.csdb.execute(query_string)
            result = self.csdb.fetch_all_rows()
            for key in solr_results['results'].keys():
                email = solr_results['results'][key]
                if email['AchiveFileId'] not in result:
                    self.log.error("ContentId: %s archivefid is not correct in solr", key)
                    raise Exception("Failed to validate data copy job")

        except Exception as excp:
            self.log.exception("Error in getting job details from database. %s" % str(excp))
            raise excp

    def validate_journal_index_copy(self, source_solr, destination_solr, smtp_list):
        """Validate Index Copy Job for journal/Contentstore mailbox
            Args:
                source_solr       --  Source Solr Object

                destination_solr  --  Destination Solr object

                smtp_list         --  List of custodain

        """

        standalone_solr = False
        if source_solr.type == constants.SOLR_TYPE_DICT[1]:
            standalone_solr = True
        self.log.info("Source is standalone %s", standalone_solr)
        if standalone_solr:
            rc_list_dict = {}
            for user in smtp_list:
                rc_list_dict['rclst'] = user
        else:
            rc_list_dict = {}
            for user in smtp_list:
                rc_list_dict['RecipientList'] = user
        source = source_solr.get_result_of_custom_query(rc_list_dict)
        rc_list_dict = {}
        for user in smtp_list:
            rc_list_dict['RecipientList'] = user
        destination = destination_solr.get_result_of_custom_query(rc_list_dict)
        for source_user in source:
            if source['total_records'] != destination['total_records']:
                self.log.error("Total records for user %s", source_user)
                raise Exception("Failed to validate index copy job")
            source_result = source['result']
            destination_result = destination['result']
            for key in source_result.keys():
                source_email = source_result[key]
                destination_email = destination_result[key]
                if not standalone_solr:
                    if source_result[key] != destination_email:
                        self.log.error("Email properties of source and destination "
                                       "did not match for content id %s", key)
                        raise Exception("Failed to validate index copy job")

                else:
                    for item in source_email.keys():
                        self.log.info(item)
                        if (item in constants.SOLR_KEYWORDS_MAPPING and
                                not source_email.get(item) == destination_email.get(
                                    constants.SOLR_KEYWORDS_MAPPING[item])):
                            self.log.error("%s properties are not same for email "
                                           "with contentid %s", item, key)
                            raise Exception("Failed to validate index copy job")

    def validate_filters(self, source_solr, destination_solr, email_filters):
        """Validate email filters in index copy job
            Args:
                source_solr       --  Source Solr Object

                destination_solr  --  Destination Solr object

                email_filters     --  Filters for solr query

        """
        standalone_solr = False
        if source_solr.type == constants.SOLR_TYPE_DICT[1]:
            standalone_solr = True
        source_query_dict = {}
        if standalone_solr:
            for filter in email_filters['filters']:
                source_query_dict[constants.CASE_FILTER_AND_SOLR_MAPPING[
                    filter['field']]] = filter['values'][0]
        else:
            for filter in email_filters['filters']:
                source_query_dict[constants.SOLR_KEYWORDS_MAPPING[
                    constants.CASE_FILTER_AND_SOLR_MAPPING[
                        filter['field']]]] = filter['values'][0]
        source_results = source_solr.get_result_of_custom_query(source_query_dict)

        destination_query_dict = {}
        for filter in email_filters['filters']:
            destination_query_dict[constants.SOLR_KEYWORDS_MAPPING[
                constants.CASE_FILTER_AND_SOLR_MAPPING[filter['field']]]] = filter['values'][0]
        destination_results = destination_solr.get_result_of_custom_query(destination_query_dict)
        self.compare_solr_results(source_results, destination_results, standalone_solr)

    def compare_solr_results(self, source, destination, standalone_solr):
        """Compare source and destination solr results
            Args:
                source             --  source solr results

                destination        --  Destination solr results

                standalone_solr    --  True if source is standalone

        """

        for source_user in source:
            destination_user = destination[source_user]
            if source[source_user]['total_records'] != destination_user['total_records']:
                self.log.error("Total records for user %s", source_user)
                raise Exception("Failed to validate index copy job")
            source_result = source[source_user]['result']
            destination_result = destination[source_user]['result']
            for key in source_result.keys():
                source_email = source_result[key]
                destination_email = destination_result[source_user + "!" + key]
                if not standalone_solr:
                    if source_result[key] != destination_email:
                        self.log.error("Email properties of source and destination "
                                       "did not match for content id %s", key)
                        raise Exception("Failed to validate index copy job")
                else:
                    for item in source_email.keys():
                        if (item in constants.SOLR_KEYWORDS_MAPPING and
                                not source_email.get(item) == destination_email.get(
                                    constants.SOLR_KEYWORDS_MAPPING[item])):
                            self.log.error("%s properties are not same for email with "
                                           "contentid %s", item, key)
                            raise Exception("Failed to validate index copy job")
