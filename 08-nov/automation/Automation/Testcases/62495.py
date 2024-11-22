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
    __init__()                          --  initialize TestCase class

    setup()                             --  sets up the variables required for running the testcase

    run()                               --  run function of this test case

    tear_down()                         --  tears down the activate created entities for running the testcase

"""
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.CollectionPruning.exchange_pruning_helper import ExchangePruningHelper
from dynamicindex.utils import constants as cs
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVTestCaseInitFailure


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Collection Pruning integration test case for Exchange backed up client - validate create, run " \
                    "backup, delete client. Validate pruning of exchange datasource collections and audit trail logs"
        self.tcinputs = {
            "AgentName": None,
            "BackupsetName": None,
            "SubclientName": None,
            "ServiceAccountDetails": None,
            "JobResultDirectory": None,
            "IndexServer": None,
            "DomainName": None,
            "ExchangeCASServer": None,
            "ExchangeServerName": None,
            "ProxyServers": None,
            "RecallService": None,
            "ServerPlanName": None,
            "PSTPath": None,
            "EnvironmentType": None,
            "MailId": None,
            "MailboxName": None,
            "IndexServerClient": None
        }
        # Test Case constants
        self.exchange_pruning_helper = None
        self.exch_mb_object = None
        self.backupset = None
        self.backupset_guid = None
        self.datasource_name = None
        self.index_server = None
        self.ex_mb_object = None
        self.email_id = None
        self.mailbox_name = None

    def setup(self):
        """Initial Configuration For Testcase"""
        try:
            self.index_server = self.tcinputs['IndexServerClient']
            self.email_id = self.tcinputs['MailId']
            self.mailbox_name = self.tcinputs['MailboxName']
            self.ex_mb_object = ExchangeMailbox(self)
            self.exchange_pruning_helper = ExchangePruningHelper(self.commcell, self.ex_mb_object,
                                                                 self.email_id, self.mailbox_name)
        except Exception as exception:
            self.status = constants.FAILED
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run Function For Test Case Execution"""
        try:
            self.log.info("Starting test case run")
            self.exch_mb_object = self.exchange_pruning_helper.initialize_exchange_onprem()
            self.client = self.exchange_pruning_helper.create_exchange_client()
            self.subclient = self.exchange_pruning_helper.configure_exchange_subclient(self.id)
            self.backupset = self.exch_mb_object.cvoperations.backupset
            self.backupset_guid = self.backupset.properties.get("backupSetEntity", {}).get("backupsetGUID", "")
            self.datasource_name = f"{cs.EXCHANGE_INDEX}{self.backupset_guid}"
            self.exchange_pruning_helper.exchange_run_backup()
            core_name, datasource_actual_name = \
                self.exchange_pruning_helper.ds_helper.get_datasource_collection_name(self.datasource_name)
            if self.exchange_pruning_helper.prune_orphan_datasources(datasource_actual_name):
                raise Exception("Datasource is deleted even when the client association exists")
            self.log.info("Datasource is present. Proceeding with pruning of datasource")
            self.exchange_pruning_helper.exchange_delete_client(self.index_server)
            if not self.exchange_pruning_helper.prune_orphan_datasources(datasource_actual_name):
                raise Exception("Datasource deletion failed even after the client associated to it is deleted.")
            if not self.exchange_pruning_helper.is_pruning_audited(datasource_actual_name, core_name):
                raise Exception("Audit for datasource pruning failed")
            self.log.info("Datasource pruned successfully. Audit information is validated")
        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status != constants.FAILED:
                self.log.info("Test case execution completed successfully")
        except Exception as exp:
            self.status = constants.FAILED
            self.log.info("Test case execution failed")
            handle_testcase_exception(self, exp)
