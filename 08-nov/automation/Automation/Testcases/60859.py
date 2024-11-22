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
    setup()                     --  Initialize TestCase attributes
    create_subclient_objects()  --  Creates subclient objects to run backups on
    run_subclient_backups()     --  Run backup jobs for passed subclient list
    create_client_group()       --  Create client group to run FSO Job on
    create_fso_client_group()   --  Create FSO client group
    create_inventory()          --  Creates Activate Inventory
    create_plan()               --  Creates FSO DC Plan
    create_fso_client()         --  Add new FSO Server
    perform_cleanup()           --  Perform cleanup related tasks
    run()                       --  Run function of this test case
    tear_down()                 --  Tear Down tasks
"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils.activateutils import ActivateUtils
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.Helper.FSOHelper import FSOServerGroupHelper
from Server.JobManager.jobmanager_helper import JobManager
from Web.AdminConsole.AdminConsolePages.server_groups import ServerGroups
import dynamicindex.utils.constants as cs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class TestCase(CVTestCase):
    """Class for executing basic acceptance test of FSO Server Group"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Add FSO Server Group and verify data source dashboards"
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "IndexServerName": None,
            "StoragePolicy": None,
            "NameServerAsset": None
        }
        # Test Case constants
        self.fso_server_group_name = None
        self.inventory_name = None
        self.plan_name = None
        self.server_group_clients = None
        self.sg_subclient_content_list = None
        self.sg_sqlitedb_path_list = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.server_group = None
        self.activate_utils = None
        self.fso_sg_helper = None
        self.job_manager = None
        self.navigator = None
        self.wait_time = 60
        self.error_dict = {}

    def setup(self):
        """Testcase Setup Method"""
        try:
            self.inventory_name = f"{self.id}_inventory_fso"
            self.plan_name = f"{self.id}_plan_fso"
            self.fso_server_group_name = f"{self.id}_fso_server_group"
            self.country_name = cs.USA_COUNTRY_NAME
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.tcinputs['UserName'],
                                              password=self.tcinputs['Password'])
            self.admin_console.login(username=self.tcinputs['UserName'],
                                     password=self.tcinputs['Password'])
            self.navigator = self.admin_console.navigator
            self.server_group = ServerGroups(self.admin_console)
            self.activate_utils = ActivateUtils(commcell=self.commcell)
            self.job_manager = JobManager(commcell=self.commcell)
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.gdpr_obj.data_source_name = self.fso_server_group_name
            self.fso_sg_helper = FSOServerGroupHelper(self.admin_console, self.commcell, self.csdb)
            self.server_group_clients = self.fso_sg_helper.config_mapping['CLIENT_LIST']
            self.sg_subclient_content_list = self.fso_sg_helper.config_mapping[
                'SUBCLIENT_CONTENT_LIST']
            self.sg_sqlitedb_path_list = self.fso_sg_helper.config_mapping['SQLITE_DB_LIST']
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def create_subclient_objects(self):
        """
        Create FS Subclient objects for respective clients.
        Return:
            List[(Object)] : Subclient object list
        """
        return self.activate_utils.create_fs_subclient_for_clients(
            self.id, self.server_group_clients,
            self.sg_subclient_content_list,
            self.tcinputs['StoragePolicy'],
            cs.FSO_SUBCLIENT_PROPS
        )

    def run_subclient_backups(self, subclient_obj_list):
        """
        Run backup jobs for passed subclient list
        Args:
            subclient_obj_list (list) : Subclient Object list to run backup jobs
        """
        self.activate_utils.run_backup(subclient_obj_list, backup_level='Full')

    @test_step
    def create_client_group(self):
        """Create server group used by FSO server group"""
        self.navigator.navigate_to_server_groups()
        self.fso_sg_helper.add_client_group(
            self.fso_server_group_name,
            self.server_group_clients
        )

    @test_step
    def create_fso_client_group(self):
        """Create FSO Client Group"""
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_sg_helper.fso_obj.add_fso_server_group()
        self.fso_sg_helper.file_server_lookup.add_fso_server_group_datasource(
            self.fso_server_group_name, cs.SERVER_GROUP_NAME, self.country_name,
            inventory_name=self.inventory_name)

    @test_step
    def create_inventory(self):
        """
        Create Inventory With Given Name server Asset
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.tcinputs['IndexServerName'])
        self.gdpr_obj.inventory_details_obj.add_asset_name_server(
            self.tcinputs['NameServerAsset'])
        if not self.gdpr_obj.inventory_details_obj.wait_for_asset_status_completion(
                self.tcinputs['NameServerAsset']):
            raise CVTestStepFailure("Could not complete Asset Scan for Inventory")

    @test_step
    def create_plan(self):
        """
        Create Data Classification Plan
        """
        self.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.tcinputs['IndexServerName'],
            content_search=False, content_analysis=False, target_app='fso')

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.fso_sg_helper.fso_cleanup(
            self.server_group_clients[0], self.fso_server_group_name)
        self.fso_sg_helper.remove_client_group(self.fso_server_group_name)
        self.gdpr_obj.cleanup(inventory_name=self.inventory_name, plan_name=self.plan_name)

    def run(self):
        """Run function for test case execution"""
        try:
            self.run_subclient_backups(self.create_subclient_objects())
            self.perform_cleanup()
            self.create_client_group()
            self.create_inventory()
            self.create_plan()
            self.create_fso_client_group()
            self.fso_sg_helper.fso_server_group_details.select_server_details_action(self.server_group_clients[0])
            self.fso_sg_helper.fso_client_details.select_details_action(self.fso_server_group_name)

            if not self.fso_sg_helper.file_server_lookup.wait_for_data_source_status_completion(
                    self.fso_server_group_name):
                raise Exception(f"Could not complete Data source scan for {self.fso_server_group_name}")
            self.log.info("Sleeping for: '%d' seconds" % self.wait_time)
            time.sleep(self.wait_time)
            self.navigator.navigate_to_governance_apps()
            self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
            self.fso_sg_helper.fso_obj.select_fso_grid_tab()
            self.fso_sg_helper.analyze_server_group_details(self.fso_server_group_name)

            for index, client in enumerate(self.server_group_clients):
                self.fso_sg_helper.backup_file_path = self.sg_subclient_content_list[index]
                self.fso_sg_helper.create_sqlite_db_connection(self.sg_sqlitedb_path_list[index])
                self.navigator.navigate_to_governance_apps()
                self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
                self.fso_sg_helper.fso_obj.select_fso_grid_tab()
                self.fso_sg_helper.fso_obj.select_details_action(self.fso_server_group_name)
                try:
                    self.fso_sg_helper.analyze_client_details(
                        client,
                        self.fso_server_group_name,
                        self.fso_sg_helper.get_fso_file_count_db(),
                        self.plan_name,
                        is_backed_up=True,
                        server_group_client=True
                    )
                except Exception as error_status:
                    self.error_dict[f'Client {client}: Analyze client details page'] = \
                        str(error_status)
                    self.status = constants.FAILED

                self.fso_sg_helper.fso_client_details.select_datasource(self.fso_server_group_name)
                self.gdpr_obj.verify_data_source_name()

                try:
                    self.fso_sg_helper.review_size_distribution_dashboard(crawl_type='Backup')
                except Exception as exp:
                    self.error_dict[f'Client {client}: Size Distribution Dashboard'] = str(exp)
                    self.status = constants.FAILED

                try:
                    self.fso_sg_helper.review_file_duplicates_dashboard()
                except Exception as exp:
                    self.error_dict[f'Client {client}: Duplicates Dashboard'] = str(exp)
                    self.status = constants.FAILED

                try:
                    self.fso_sg_helper.verify_fso_time_data()
                except Exception as exp:
                    self.error_dict[f'Client {client}: Access/Modified/Created Time Match Failed'] = \
                        str(exp)
                    self.status = constants.FAILED

                self.fso_sg_helper.close_existing_connections()

            if self.status == constants.FAILED:
                raise CVTestStepFailure(str(self.error_dict))

        except Exception as exp:
            if len(self.error_dict) > 0:
                self.log.info("************Following Error Occurred in Automation************")
                for key, value in self.error_dict.items():
                    self.log.info("%s %s" % (key, value))
                self.log.info("**************************************************************")
            handle_testcase_exception(self, exp)

    def tear_down(self):
        try:
            if self.status != constants.FAILED:
                self.perform_cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
