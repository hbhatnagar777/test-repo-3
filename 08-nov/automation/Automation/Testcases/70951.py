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

from Application.Office365.Office365Plan import Office365Plan
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.constants import OFFICE_365_PLAN_CI
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange
    Content Indexing without preview"""

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

                exmbclient_object      (object)    --  Object of ExchangeMailbox class

        """
        super(TestCase, self).__init__()
        self._client = None
        self._subclient = None
        self.name = ("Basic acceptance test of Exchange Content"
                     " Indexing without preview generation")
        self.show_to_user = True
        self.smtp_list = []
        self.mailboxes_list = []
        self.exmbclient_object = None
        self.tcinputs = {
            "SubclientName": None,
            "BackupsetName": None,
            "IndexServer": None,
            "ServerPlanName": None,
            "DomainName": None,
            "ProxyServers": None,
            "azureAppKeyID": None,
            "azureAppKeySecret": None,
            "azureTenantName": None,
            "EnvironmentType": None
        }
        self.o365_plan = None
        self.testdata = None

    def setup(self):
        """Setup function of this test case"""
        self.exmbclient_object = ExchangeMailbox(self)
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )

        self.testdata = TestData(self.exmbclient_object)

        self.mailboxes_list = self.testdata.create_online_mailbox()

        self.smtp_list = [f"{x}@{self.tcinputs['DomainName']}" for x in self.mailboxes_list]

        self.exmbclient_object.exchange_lib.send_email(
            mailbox_list=self.smtp_list)

        self.log.info("Mailbox List: %s" % self.mailboxes_list)
        self.log.info("SMTP List: %s" % self.smtp_list)

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info("Client creation successful")
        self._subclient = self.exmbclient_object.cvoperations.subclient
        ci_plan_name = f"{OFFICE_365_PLAN_CI}" % self.id
        self.o365_plan = Office365Plan(self.exmbclient_object.commcell, ci_plan_name)
        self.log.info(f"Created Plan : {self.o365_plan.plan_name}")
        self.o365_plan.enable_content_indexing()
        self.log.info("Enabled CI on plan")

    def run(self):
        """Run function of this test case"""
        try:

            subclient_content = {
                'mailboxNames': self.mailboxes_list,
                'plan_name': self.o365_plan.plan_name,
                'plan_id': self.o365_plan.plan_id
            }

            self.log.info(
                "--------------------------CREATE USER ASSOCAITION"
                "-----------------------------------"
            )
            active_directory = self.exmbclient_object.active_directory

            active_directory.set_user_assocaitions(subclient_content, False)

            self.log.info(
                "--------------------------RUNNING BACKUP"
                "-----------------------------------"
            )

            self.exmbclient_object.cvoperations.run_backup()
            self.log.info(
                "--------------------------CREATING SOLR OBJECT--------------------------"
            )
            solr = SolrHelper(self.exmbclient_object)
            select_dict = {"ContentIndexingStatus": [0, 1], "DocumentType": 2,
                           solr.keyword_for_client_id: solr.client_id}
            if solr.index_details[0]['server_type'] != 1:
                select_dict = {"ContentIndexingStatus": [0, 1], "DocumentType": 2,
                               solr.keyword_for_client_id: solr.client_id}
            self.log.info(
                "-------------------Getting items eligible for CI from Solr----------------------"
            )

            items_eligible_for_ci = solr.get_count_from_json(solr.create_url_and_get_response(select_dict).content)
            self.log.info(
                "-----------Getting job details of automatic CI job-----------"
            )
            ci_job = self.exmbclient_object.cvoperations.get_automatic_ci_job()
            ci_item_cnt = ci_job.details["jobDetail"]["generalInfo"]["totalNumOfFiles"]
            self.log.info(f"Total items content indexed by job: {ci_job.job_id} = {ci_item_cnt}")
            if int(items_eligible_for_ci) != int(ci_item_cnt):
                raise Exception(f'Total number of items content indexed by job = {ci_item_cnt}'
                                f'is not equal to the total number of items eligible for ci: {items_eligible_for_ci}')
            if not solr.is_content_indexed(ci_item_cnt):
                raise Exception("Solr not updated. Content indexing failed")

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function for the Test Case"""
        self.testdata.delete_online_mailboxes(mailboxes_list=self.smtp_list)
