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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.activateapps.constants import EdiscoveryConstants as edisconstant
from dynamicindex.CollectionPruning.fso_pruning_helper import FSOPruningHelper
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
        self.name = "Collection Pruning integration test case for FSO live crawl - validate create and delete " \
                    "of plan and inventory, create and prune of orphan datasource, validate the audit trail logs"
        self.tcinputs = {
            "ClientName": None,
            "LocalPath": None,
            "IndexServer": None
        }
        # Test Case constants
        self.fso_pruning_helper = None
        self.fso_plan_name = None
        self.fso_inventory = None
        self.fso_ds_name = None
        self.fso_client_name = None
        self.index_server = None
        self.path = None

    def setup(self):
        """Initial Configuration For Testcase"""
        try:
            self.fso_pruning_helper = FSOPruningHelper(self.commcell)
            self.fso_plan_name = f"{self.id}_fso_plan"
            self.fso_inventory = f"{self.id}_fso_inventory"
            self.fso_ds_name = f"{self.id}_fso_ds"
            self.fso_client_name = self.tcinputs['ClientName']
            self.index_server = self.tcinputs['IndexServer']
            self.path = self.tcinputs['LocalPath']
        except Exception as exception:
            self.status = constants.FAILED
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run Function For Test Case Execution"""
        try:
            self.log.info("Starting test case run")
            self.fso_pruning_helper.initialize_fso(self.fso_plan_name, self.fso_inventory, self.index_server,
                                                   fso_client=self.fso_client_name, ds_name=self.fso_ds_name)
            datasource = self.fso_pruning_helper.add_fso_server(edisconstant.SourceType.SOURCE, self.path)
            self.fso_pruning_helper.validate_fso_server(edisconstant.SourceType.SOURCE, self.path)
            if self.fso_pruning_helper.prune_orphan_datasources(datasource):
                raise Exception("Datasource is deleted even when the backupset association exists")
            self.log.info("Datasource is present. Proceeding with pruning of datasource")
            self.fso_pruning_helper.delete_unc_backupset(self.client)
            if not self.fso_pruning_helper.prune_orphan_datasources(datasource):
                raise Exception("Datasource deletion failed even after the backupset associated to it is deleted.")
            self.fso_pruning_helper.validate_audit_pruning()
            self.log.info("Datasource pruned successfully. Audit information is validated")
        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status != constants.FAILED:
                self.fso_pruning_helper.cleanup()
                self.log.info("Test case execution completed successfully")
        except Exception as exp:
            self.status = constants.FAILED
            self.log.info("Test case execution failed")
            handle_testcase_exception(self, exp)
