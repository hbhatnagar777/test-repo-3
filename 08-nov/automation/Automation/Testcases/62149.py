# -*- coding: utf-8 -*

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
    setup()                             --  Initialize TestCase attributes
    create_inventory()                  --  Creates Activate Inventory
    create_plan()                       --  Creates FSO DC Plan
    create_fso_client()                 --  Add new FSO Server
    perform_cleanup()                   --  Perform cleanup related tasks
    create_tagset()                     --  Add new tagset
    delete_tagset()                     --  Delete a tagset  
    add_tags()                          --  Add a tag to tagset
    setup_tags()                        --  Setting up a Tag set and applying tags  
    review_tag_files_action_fso()       --  Perform Tag Files review action for FSO  
    verify_tag_files_action_fso()       --  Verify Tag Files review action for FSO
    run()                               --  Run function of this test case
    tear_down()                         --  Tear Down tasks
"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.GovernanceAppsPages.FileStorageOptimization import FileStorageOptimization
from dynamicindex.utils.activateutils import ActivateUtils
import dynamicindex.utils.constants as cs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Tags import Tags
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class TestCase(CVTestCase):
    """Basic acceptance test case for Tag manager feature in Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Apply Tag Action for a single file in Review Page of a FSO Datasource"
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "IndexServerName": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "UserName": None,
            "Password": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "TestDataSQLiteDBPath": None,
            "AccessNode": None
        }
        # Test Case constants
        self.file_server_display_name = None
        self.inventory_name = None
        self.plan_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.fso_obj = None
        self.fso_helper = None
        self.navigator = None
        self.test_case_error = None
        self.wait_time = 60
        self.error_dict = {}
        self.tags_obj = None

    def setup(self):
        """Initial Configuration for testcase"""
        try:
            self.file_server_display_name = f"{self.id}_test_file_server_fso"
            self.inventory_name = f"{self.id}_inventory_fso"
            self.plan_name = f"{self.id}_plan_fso"
            self.tagset_name = f"{self.id} Tagset"
            self.tag_name = f"{self.id} Tag"
            self.tagset_desc = "Sample Tagset to Validate Tags Functionality"
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.tcinputs['UserName'],
                                              password=self.tcinputs['Password'])
            self.admin_console.login(username=self.tcinputs['UserName'],
                                     password=self.tcinputs['Password'])
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.fso_obj = FileStorageOptimization(self.admin_console)
            self.tags_obj = Tags(self.admin_console)
            self.country_name = cs.USA_COUNTRY_NAME
            self.gdpr_obj.data_source_name = self.file_server_display_name
            self.fso_helper = FSO(self.admin_console, self.commcell)
            self.fso_helper.data_source_name = self.file_server_display_name
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_inventory(self):
        """
        Create Inventory With Given Nameserver
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.tcinputs['IndexServerName'])

        self.gdpr_obj.inventory_details_obj.add_asset_name_server(
            self.tcinputs['NameServerAsset'])
        if not self.gdpr_obj.inventory_details_obj.wait_for_asset_status_completion(
                self.tcinputs['NameServerAsset']):
            raise CVTestStepFailure("Could not complete Asset Scan")

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
    def create_fso_client(self):
        """Create FSO client """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_obj.add_client(
            self.inventory_name, self.plan_name
        )

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.fso_helper.fso_cleanup(
            self.file_server_display_name,
            self.file_server_display_name,
            pseudo_client_name=self.file_server_display_name)
        self.gdpr_obj.cleanup(inventory_name=self.inventory_name,
                              plan_name=self.plan_name)
        self.delete_tagset()
    
    @test_step    
    def create_tagset(self):
        """
        Create a Tag set
        """
        self.navigator.navigate_to_tags()
        self.tags_obj.create_tagset(self.tagset_name, self.tagset_desc)   

    @test_step    
    def delete_tagset(self):
        """
        Delete a Tag set
        """
        self.navigator.navigate_to_tags()
        if self.tags_obj._check_if_tagset_exists(self.tagset_name):
            self.tags_obj.action_delete_tagset(self.tagset_name)
    
    @test_step            
    def add_tags(self):
        """
        Adding tag to a Tag set
        """
        self.navigator.navigate_to_tags()
        self.tags_obj.action_add_tag(self.tagset_name, self.tag_name)
    
    @test_step    
    def setup_tags(self):    
        """
        Setting up a Tag set and applying tags
        """
        self.create_tagset()
        self.add_tags()
       
    @test_step
    def review_tag_files_action_fso(self, filepath):
        """
        Performing Tag Files review action for FSO
        Args:
            filepath (str): path of the file
        """
        tag_action_status = None
        filename = filepath[filepath.rindex('\\') + 1:]
        try:
            tag_action_status = self.gdpr_obj.data_source_review_obj.review_tag_files_action(
                filename,
                self.tag_name,
                is_fso=True,
                data_source_type=cs.FILE_SYSTEM,
                all_items_in_page=False
            )
            if not tag_action_status:
                raise CVWebAutomationException("Failed to apply tag on the given file")
        except CVWebAutomationException as error:
            self.error_dict[f'Tag File Action Failure: {filepath}'] = str(error)
            self.test_case_error = str(error)
            self.gdpr_obj.data_source_review_obj.close_action_modal()
            
    @test_step
    def verify_tag_files_action_fso(self, tag_name, filepath):
        """
        Verify Tag Files review action for FSO
        Args:
            filepath (str): path of the file
            tag_name (str): name of the tag to be applied
        """
        filename = filepath[filepath.rindex('\\') + 1:]
        self.log.info("Name of the file retrieved from filepath: %s" % filename)
        
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        
        self.fso_obj.select_details_action(self.file_server_display_name)
        self.fso_helper.fso_client_details.select_datasource(self.file_server_display_name)
        self.fso_helper.fso_data_source_discover.select_fso_review_tab()
        
        tagged_file = self.gdpr_obj.data_source_review_obj.get_tagged_file_names(tag_name)
        self.log.info("Name of the file retrieved from tag filter: %s" % tagged_file[0])
        
        if tagged_file[0] == filename:
            self.log.info("Successfully verified the file name for the applied tag: %s" % tag_name)
        else:
            raise CVTestStepFailure("Validation of the file name failed for the tag: %s" % tag_name)    
        
    def run(self):
        """Main function for test case execution"""
        try:
            self.perform_cleanup()
            self.create_inventory()
            self.create_plan()
            self.create_fso_client()
             
            self.fso_helper.create_sqlite_db_connection(self.tcinputs['TestDataSQLiteDBPath'])
            self.fso_helper.test_data_path = self.tcinputs['FileServerDirectoryPath']
                  
            self.gdpr_obj.file_server_lookup_obj.add_file_server(
                self.tcinputs['HostNameToAnalyze'], 'Host name',
                self.file_server_display_name, self.country_name,
                self.tcinputs['FileServerDirectoryPath'],
                username = self.tcinputs['FileServerUserName'],
                password = self.tcinputs['FileServerPassword'],
                access_node=self.tcinputs['AccessNode'])
                       
            self.fso_helper.fso_obj.select_details_action(
                self.file_server_display_name
            )
            self.fso_helper.fso_client_details.select_details_action(
                self.file_server_display_name
            )
                       
            if not self.fso_helper.file_server_lookup.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise Exception("Could not complete Datasource scan.")
            self.log.info("Sleeping for: '%d' seconds" % self.wait_time)
            time.sleep(self.wait_time)
                       
            self.navigator.navigate_to_governance_apps()
            self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
            self.fso_helper.analyze_client_expanded_view(self.file_server_display_name)
            try:
                self.fso_helper.analyze_client_details(
                    self.file_server_display_name,
                    self.file_server_display_name,
                    self.fso_helper.get_fso_file_count_db(),
                    self.plan_name
                )
            except Exception as err_status:
                self.error_dict["Analyze Client Details Page"] = str(err_status)
                self.test_case_error = str(err_status)    
                      
            self.setup_tags()
            
            self.navigator.navigate_to_governance_apps()
            self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
            self.fso_obj.select_details_action(self.file_server_display_name)
            self.fso_helper.fso_client_details.select_datasource(self.file_server_display_name)
            self.fso_helper.fso_data_source_discover.select_fso_review_tab()
 
            files_list = self.fso_helper.fetch_fso_files_db(2)
            self.review_tag_files_action_fso(files_list[1])
            self.verify_tag_files_action_fso(self.tag_name, files_list[1])
             
            if self.test_case_error is not None:
                raise CVTestStepFailure(str(self.error_dict))
             
        except Exception as exp:
            if len(self.error_dict.keys()) > 0:
                self.log.info("**Following Error Occurred in the Automation Test case**")
                for key, value in self.error_dict.items():
                    self.log.info("%s %s" % (key, value))
            handle_testcase_exception(self, exp)
            self.status = constants.FAILED
                        
    def tear_down(self):
        try:
            if self.status != constants.FAILED:
                self.perform_cleanup()
        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
