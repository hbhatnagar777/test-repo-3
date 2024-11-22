# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                                   --  initialize TestCase class

    setup()                                      --  Initial configuration for the testcase

    create_subclient_obj()                       --  Create FS Subclient objects for respective clients

    run_subclient_backups()                      --  Run backup jobs for passed subclient list

    create_plan()                                --  Creates a plan

    create_fso_client()                          --  Creates FSO client

    create_fso_datasource()                      --  Create FSO data source and start crawl job

    download_csv()                               --  Downloads the CSV from the passed dashboard & returns the csv_path

    cleanup()                                    --  Runs cleanup

    run()                                        --  run function of this test case

    tear_down()                                  --  Tear Down tasks
"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.utils.constants import USA_COUNTRY_NAME, CLIENT_NAME, FSO_SUBCLIENT_PROPS, DUPLICATES_DASHBOARD


class TestCase(CVTestCase):
    """Class for executing this Testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Validation of Export to CSV for Duplicates dashboard (Backed up datasource)"
        self.tcinputs = {
            "IndexServer": None,
            "HostNameToAnalyze": None,
            "FileServerLocalTestDataPath": None,
            "StoragePolicy": None
        }
        # Testcase Constants
        self.index_server_name = None
        self.plan_name = None
        self.file_server_display_name = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.gdpr_base = None
        self.fso_helper = None
        self.explict_wait = 120
        self.machine_obj = None
        self.activate_utils = None
        self.utils = None
        self.duplicate_files = None
        self.datasource_helper = None
        self.downloads_directory = None

    def setup(self):
        """ Initial configuration for the test case"""

        try:
            self.index_server_name = self.tcinputs['IndexServer']
            self.file_server_display_name = f"{self.id}_Automation_DS"
            self.plan_name = f'{self.id}_plan'
            self.utils = TestCaseUtils(self)
            self.machine_obj = Machine()
            self.downloads_directory = self.utils.get_temp_dir()
            self.machine_obj.clear_folder_content(self.downloads_directory)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.downloads_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.activate_utils = ActivateUtils(commcell=self.commcell)
            self.gdpr_base = GDPR(self.admin_console, self.commcell, self.csdb)
            self.gdpr_base.data_source_name = self.file_server_display_name
            self.fso_helper = FSO(self.admin_console, self.commcell)
            self.datasource_helper = DataSourceHelper(self.commcell)
            self.fso_helper.data_source_name = self.file_server_display_name
            self.fso_helper.backup_file_path = self.tcinputs['FileServerLocalTestDataPath']

        except Exception:
            raise Exception("init tc failed")

    def create_subclient_obj(self):
        """
        Create FS Subclient objects for respective clients.
        Return:
            List[(Object)] : Subclient object list
        """
        return self.activate_utils.create_fs_subclient_for_clients(
            self.id, [self.tcinputs['HostNameToAnalyze']],
            [self.tcinputs['FileServerLocalTestDataPath']],
            self.tcinputs['StoragePolicy'], FSO_SUBCLIENT_PROPS
        )

    def run_subclient_backups(self, subclient_obj_list):
        """
        Run backup jobs for passed subclient list
        Args:
            subclient_obj_list (list) : Subclient Object list to run backup jobs
        """
        self.activate_utils.run_backup(subclient_obj_list, backup_level='Full')

    @test_step
    def create_plan(self):
        """
            Creates a plan
        """

        self.navigator.navigate_to_plan()
        self.gdpr_base.plans_obj.create_data_classification_plan(self.plan_name, self.index_server_name,
                                                                 content_search=False, content_analysis=False,
                                                                 target_app='fso')

    @test_step
    def create_fso_client(self):
        """Create FSO client """

        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.add_client(plan_name=self.plan_name, inventory_name=None)

    @test_step
    def create_fso_datasource(self):
        """Create FSO data source and start crawl job"""

        try:
            self.fso_helper.file_server_lookup.add_file_server(
                self.tcinputs["HostNameToAnalyze"], CLIENT_NAME,
                self.file_server_display_name, USA_COUNTRY_NAME,
                agent_installed=True, backup_data_import=True,
                fso_server=True, crawl_type='Quick')
            if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise CVTestStepFailure("Could not complete the Datasource scan.")
            self.log.info(f"Sleeping for: {self.explict_wait} seconds")
            time.sleep(self.explict_wait)
            self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['HostNameToAnalyze'])

        except Exception as exp:
            handle_testcase_exception(self, exp)

    @test_step
    def download_csv(self):
        """
            Downloads the CSV from the passed dashboard & returns the csv_path
        """
        try:
            self.fso_helper.navigate_to_datasource_details(self.tcinputs['HostNameToAnalyze'],
                                                           self.file_server_display_name)
            self.fso_helper.fso_data_source_discover.select_fso_dashboard(
                self.admin_console.props['reports.fileDuplicate'])
            self.duplicate_files = int(self.fso_helper.fso_data_source_discover.fso_dashboard_entity_count(
                "Total Duplicate Files"))
            self.admin_console.click_button_using_text("Export to CSV")
            self.log.info("Wait 3 minutes for CSV Download")
            time.sleep(180)
            csv_path = self.fso_helper.get_csv_file_from_machine(self.downloads_directory)
            return csv_path
        except Exception as err:
            handle_testcase_exception(self, err)

    @test_step
    def cleanup(self):
        """
            Cleans up the environment
        """

        self.fso_helper.fso_cleanup(self.tcinputs['HostNameToAnalyze'], self.file_server_display_name)
        self.gdpr_base.cleanup(self.plan_name)

    def run(self):
        try:
            self.run_subclient_backups(self.create_subclient_obj())
            self.cleanup()
            self.create_plan()
            self.create_fso_client()
            self.create_fso_datasource()
            csv_path = self.download_csv()
            attributes = {"AccessTime", "Url", "OwnerName", "Size", "FileName"}
            total_documents = self.datasource_helper.get_doc_counts_from_solr(self.tcinputs['HostNameToAnalyze'],
                                                                              self.file_server_display_name)
            parameters = {"start": 0, "rows": total_documents}
            solr_json_response = self.datasource_helper.get_data_from_solr(self.tcinputs['HostNameToAnalyze'],
                                                                           self.file_server_display_name, attributes,
                                                                           parameters, document_type="FILES",
                                                                           is_backedup=True)
            self.datasource_helper.validate_csv_data_with_solr(csv_path, solr_json_response,
                                                               dashboard=DUPLICATES_DASHBOARD,
                                                               **{'duplicate_files': self.duplicate_files})
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            self.cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
