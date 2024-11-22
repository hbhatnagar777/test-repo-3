# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

import sys
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants

from Application.Exchange.ExchangeMailbox.case_manager import CaseManager
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.ExchangeMailbox.constants import (
    CASE_CLIENT_BK_NAME,
    CASE_CLIENT_CI_NAME,
    CASE_CLIENT_EE_NAME
)


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Email archiving Case Manager
     Jobs Validation"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case

                show_to_user    (bool)      --  test case flag to determine if the test case is
                                                    to be shown to user or not

                    Accept:
                        True    -   test case will be shown to user from commcell gui

                        False   -   test case will not be shown to user

                    default: False

                tcinputs    (dict)      --  dict of test case inputs with input name as dict key
                                                and value as input type

                        Ex: {

                             "MY_INPUT_NAME": None

                        }

        """
        super(TestCase, self).__init__()
        self.name = "Basic acceptance test of Email archiving Case Manager Jobs Validation"
        self.show_to_user = True
        self.smtp_list = []
        self.mailboxes_list = []
        self.case_object = None
        self.tcinputs = {
            "SubclientName": None,
            "BackupsetName": None,
            "IndexServer": None,
            "ExchangeClient": None,
            "DCPlan": None,
            "ServerPlan": None,
            "BackedupMailboxes": None,
            "CIMailboxes": None,
            "EEMailboxes": None,
            "CaseIndexServer": None,
            "HoldType": None,
            "GroupSMTP": None,
            "EmailFilters": None
        }

    def run(self):
        """Run function of this test case"""
        try:
            source_ex_object = ExchangeMailbox(self)
            source_ex_object.client_name = self.tcinputs['ExchangeClient']
            self.client = self.commcell.clients.get(source_ex_object.client_name)
            source_ex_object.cvoperations.client = self.client
            source_subclient = source_ex_object.cvoperations.subclient
            self.log.info("***************CASE1 BACKED UP SOURCE***************")
            self.case_object = CaseManager(self)
            self.log.info("Getting Backuped users assocaited")
            custodian_info_list, guids = self.case_object.get_custodian_list(
                source_subclient, self.tcinputs['BackedupMailboxes'])
            self.log.info(custodian_info_list)
            source_solr = SolrHelper(source_ex_object)
            self.case_object.client_name = CASE_CLIENT_BK_NAME % (self.id)
            self.case_object.add_case_and_definition(custodian_info_list)
            self.log.info(
                "--------------------------RUNNING INDEX COPY"
                "-----------------------------------"
            )
            self.case_object.cvoperations.index_copy()
            destination = SolrHelper(self.case_object)
            self.case_object.validate_index_copy(source_solr, destination, guids)
            self.log.info(
                "--------------------------RUNNING DATA COPY"
                "-----------------------------------"
            )
            job = self.case_object.cvoperations.data_copy()
            self.case_object.validate_data_copy(destination, job.job_id)
            select_dict = {"ContentIndexingStatus": 0, "CAState": 0, "datatype": 2,
                           destination.keyword_for_client_id: destination.client_id}
            items_eligible_for_ci = destination.create_url_and_get_response(
                select_dict, None, None)
            items_eligible_for_ci = destination.get_count_from_json(items_eligible_for_ci.content)
            self.log.info(
                "--------------------------RUNNING CONTENT INDEXING"
                "-----------------------------------"
            )
            job = self.case_object.cvoperations.run_content_indexing()
            ci_item_cnt = job.details["jobDetail"]["generalInfo"]["totalNumOfFiles"]
            if int(items_eligible_for_ci) != int(ci_item_cnt):
                raise Exception(f'Total number of items content indexed by job {job.job_id} '
                                f'is not equal to the total number of items eligible for ci')
            destination.is_content_indexed(ci_item_cnt)

            self.log.info("**************CASE2 CONTENT INDEXED******************")

            self.case_object = CaseManager(self)
            self.log.info("Getting Backuped users assocaited")
            custodian_info_list, guids = self.case_object.get_custodian_list(
                source_subclient, self.tcinputs['CIMailboxes'])
            self.log.info(custodian_info_list)
            source_solr = SolrHelper(source_ex_object)

            self.case_object.client_name = CASE_CLIENT_CI_NAME % (self.id)
            self.case_object.add_case_and_definition(custodian_info_list)
            self.case_object.cvoperations.index_copy()
            destination = SolrHelper(self.case_object)
            self.case_object.validate_index_copy(source_solr, destination, guids)

            self.log.info("*************CASE3 ENTITY EXTARCTED SOURCE***************")

            self.case_object = CaseManager(self)
            self.log.info("Getting Backuped users assocaited")
            custodian_info_list, guids = self.case_object.get_custodian_list(
                source_subclient, self.tcinputs['EEMailboxes'])
            self.log.info(custodian_info_list)
            source_solr = SolrHelper(source_ex_object)
            self.case_object.client_name = CASE_CLIENT_EE_NAME % (self.id)
            self.case_object.add_case_and_definition(custodian_info_list)
            self.case_object.cvoperations.index_copy()
            destination = SolrHelper(self.case_object)
            self.case_object.validate_index_copy(source_solr, destination, guids)

            self.log.info("*************CASE4 GROUP IN CUSTODIAN LIST***************")

            self.case_object = CaseManager(self)
            self.log.info("Getting Backuped users assocaited")
            custodian_info_list = self.case_object.get_custodian_list_with_smtp(
                self.tcinputs['GroupSMTP'])
            self.log.info(custodian_info_list)
            self.case_object.client_name = CASE_CLIENT_EE_NAME % (self.id)
            self.case_object.add_case_and_definition(custodian_info_list)
            self.case_object.cvoperations.index_copy()

            self.log.info("*************CASE5 EMAIL FILTERS***************")
            self.case_object = CaseManager(self)
            self.log.info("Getting Backuped users assocaited")
            source_solr = SolrHelper(source_ex_object)
            self.case_object.client_name = CASE_CLIENT_EE_NAME % (self.id)
            self.case_object.add_case_and_definition(
                custodian_info_list=[], email_filters=self.tcinputs['EmailFilters'])
            self.case_object.cvoperations.index_copy()
            destination_solr = SolrHelper(self.case_object)
            self.case_object.validate_filters(
                source_solr, destination_solr, self.tcinputs['EmailFilters'])

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
