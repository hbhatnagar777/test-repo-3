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
from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.CollectionPruning.sharepoint_pruning_heper import SharepointPruningHelper
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
        self.name = "Collection Pruning integration test case for Sharepoint Online v2 client - validate create, " \
                    "run backup, index server switch and delete client. Validate pruning of migrated sharepoint " \
                    "datasource collections and validate audit trail logs"
        self.tcinputs = {
            "PseudoClientName": None,
            "ServerPlanName": None,
            "IndexServer": None,
            "AccessNodes": None,
            "TenantUrl": None,
            "Username": None,
            "Password": None,
            "AzureAppId": None,
            "AzureAppKeyValue": None,
            "AzureDirectoryId": None,
            "AzureUserName": None,
            "AzureSecret": None,
            "SiteUrl": None,
            "Office365Plan": None,
            "IsModernAuthEnabled": None,
            "NewIndexServer": None
        }
        # Test Case constants
        self.sharepoint_pruning_helper = None
        self.sp_object = None
        self.backupset = None
        self.backupset_guid = None
        self.datasource_name = None
        self.new_index_server = None
        self.sp_online_object = None
        self.site_url = None
        self.o365_plan = None

    def setup(self):
        """Initial Configuration For Testcase"""
        try:
            if isinstance(self.tcinputs["AccessNodes"], str):
                self.tcinputs["AccessNodes"] = self.tcinputs["AccessNodes"].split(",")
            self.sp_online_object = SharePointOnline(self)
            self.o365_plan = self.tcinputs['Office365Plan']
            self.site_url = self.tcinputs["SiteUrl"]
            self.new_index_server = self.tcinputs["NewIndexServer"]
            self.sharepoint_pruning_helper = SharepointPruningHelper(self.commcell, self.sp_online_object,
                                                                     self.o365_plan, self.site_url)
        except Exception as exception:
            self.status = constants.FAILED
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run Function For Test Case Execution"""
        try:
            self.log.info("Starting test case run")
            self.sp_object = self.sharepoint_pruning_helper.create_sharepoint_o365()
            self.backupset = self.sp_object.cvoperations.backupset
            self.backupset_guid = self.backupset.properties.get("backupSetEntity", {}).get("backupsetGUID", "")
            self.datasource_name = f"{cs.SHAREPOINT_INDEX}{self.backupset_guid}"
            self.sharepoint_pruning_helper.sharepoint_run_backup()
            core_name, datasource_actual_name = \
                self.sharepoint_pruning_helper.ds_helper.get_datasource_collection_name(self.datasource_name)
            self.sharepoint_pruning_helper.sharepoint_switch_index_server(self.new_index_server)
            self.sharepoint_pruning_helper.sharepoint_run_backup()
            if not self.sharepoint_pruning_helper.ds_helper.check_datasource_exists(datasource_actual_name):
                raise Exception(f"Old Datasource [{datasource_actual_name}] doesn't exist. "
                                f"Deleted even before the pruning API is called")
            self.log.info("Old Datasource is present. Proceeding with pruning of datasource")
            self.sharepoint_pruning_helper.prune_migrated_index_datasource(datasource_actual_name, self.datasource_name)
            if not self.sharepoint_pruning_helper.is_pruning_audited(datasource_actual_name, core_name):
                raise Exception("Audit for datasource pruning failed")
            self.log.info("Datasource pruned successfully. Audit information is validated")
        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status != constants.FAILED:
                self.sharepoint_pruning_helper.sharepoint_delete_client()
                self.log.info("Test case execution completed successfully")
        except Exception as exp:
            self.status = constants.FAILED
            self.log.info("Test case execution failed")
            handle_testcase_exception(self, exp)
