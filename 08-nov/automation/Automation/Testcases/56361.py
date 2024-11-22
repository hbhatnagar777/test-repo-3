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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""
import zipfile
import time
from selenium.common.exceptions import StaleElementReferenceException

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.database_helper import MSSQL
from Web.AdminConsole.GovernanceAppsPages.ComplianceSearch import ComplianceSearch
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of 'Export To CAB'
    operation for selected items in Compliance Search from adminconsole"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Basic acceptance Test of 'Export To CAB' operation " \
                    "for selected items in Compliance Search from adminconsole"
        self.test_individual_failure_message = ""
        self.browser = None
        self.indexservercloud = None
        self.accessnodes = None
        self.globaladmin = None
        self.password = None
        self.tcinputs = {
            "IndexServer": None
        }
        # Test Case constants
        self.browser = None
        self.app_name = None
        self.search_keyword = None
        self.count_compliance_search = -1
        self.test_case_error = None
        self.gov_app = None
        self.app = None
        self.navigator = None
        self.admin_console = None
        self.selected_item_count = None
        self.export_jobid = None
        self.utils = TestCaseUtils(self)
        self.export_item_count = None
        self.local_machine = None
        self.owner_field_list = None
        self.sqlobj = None
        self.exportset_name = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            # Test Case constants
            self.app_name = str(self.id) + "_app"
            self.indexservercloud = self.tcinputs['IndexServer']
            self.search_keyword_eml_export = self.tcinputs['SearchKeywordEML']
            self.search_keyword_msg_export = self.tcinputs['SearchKeywordMSG']
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.inputJSONnode['commcell']['webconsole_url'], enable_ssl=True)
            self.admin_console.login(self.inputJSONnode['commcell']['loginUsername'],
                                     self.inputJSONnode['commcell']['loginPassword'])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()
            self.app = ComplianceSearch(self.admin_console)
            self.gov_app = GovernanceApps(self.admin_console)
            self.gov_app.select_compliance_search()

            self.selected_item_count = 15
            self.local_machine = Machine()
            self.owner_field_list = self.tcinputs['Custodian_Users']
            server_name = self.tcinputs['SQLServerName']
            sqluser = self.tcinputs['sqluser']
            sqlpassword = self.tcinputs['sqlpassword']
            self.sqlobj = MSSQL(server_name,
                                sqluser,
                                sqlpassword,
                                "DM2",
                                use_pyodbc=False)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def cleanup(self):
        """
        Reset temp dir and restore DB status of emails
        """
        self.utils.reset_temp_dir()
        _query = "update dmresultset set RestoreStatus=0,DestinationPath='' " \
                 "where RestoreStatus=4"
        self.sqlobj.execute(_query)

    @test_step
    def compliancesearch_keyword_search(self, keyword):
        """
            Search for Keyword in Compliance Search UI
            Args:
                keyword: text on which search has to be performed
        """
        self.count_compliance_search = self.app.search_for_keyword_get_results(
            self.indexservercloud, keyword)
        self.log.info(
            "Compliance Search returns %s items",
            self.count_compliance_search)
        if self.count_compliance_search == -1:
            raise CVTestStepFailure(f"Error getting Compliance Search results")

    @test_step
    def perform_export_to_cab_selected_items(self, file_format):
        """
            Perform 'Export To CAB' operation on given set of results
            Args:
                file_format: Format of the emails to be exported to
        """
        millis = int(round(time.time() * 1000))
        downloadsetname = str(millis) + "_downloadset"
        self.exportset_name = str(millis) + "_exportset"
        self.export_item_count = self.selected_item_count
        if not self.app.do_export_to("CAB", self.selected_item_count,
                                     downloadsetname, self.exportset_name, file_format):
            exp = "Export job didn't get submitted successfully"
            raise CVTestStepFailure(exp)

    @test_step
    def verify_job_completion(self):
        """
            Verify that 'Export To' job completed successfully
        """
        self.navigator.navigate_to_jobs()
        export_job_id, job_details = self.app.get_export_job_details()
        self.export_jobid = export_job_id
        if not job_details['Status'] == 'Completed':
            exp = "Export job {0} is not completed successfully"\
                .format(export_job_id)
            raise CVTestStepFailure(exp)

    @test_step
    def verify_download(self):
        """
            Verify that download completes successfully
        """
        self.navigator.navigate_to_governance_apps()
        self.gov_app.select_compliance_search()
        self.app.perfom_download(self.export_jobid, self.exportset_name)

    @test_step
    def validate_cab_results(self):
        """
            Verify that downloaded set has required number of files
        """
        self.utils.wait_for_file_to_download("zip", timeout_period=300)
        download_directory = self.utils.get_temp_dir()
        files = self.local_machine.get_files_in_path(
            download_directory)  # to extract Zip files
        for file in files:
            with zipfile.ZipFile(file, 'r') as zip_file:
                zip_file.extractall(download_directory)

        extracted_files = self.local_machine.get_files_in_path(
            download_directory)
        extracted_file_count = len(extracted_files) - 1
        if extracted_file_count == self.export_item_count:
            self.log.info("Zip file has %s files", extracted_file_count)
            self.app.delete_exportset(self.exportset_name)
        else:
            self.log.info(
                "Actual file count is %s and Expected file count is %s",
                extracted_file_count,
                self.export_item_count)
            raise CVTestStepFailure(
                "Count of extracted and exported "
                "files are not same for jobid: [{0}]".format(
                    self.export_jobid))

    @test_step
    def perform_export(self, file_format):
        """
        Perform Export and verify
        """
        try:
            self.perform_export_to_cab_selected_items(file_format)
            self.verify_job_completion()
        except:
            self.log.info("Verifying whether the export set already exists")
            self.export_jobid= 'Not available'

        self.verify_download()
        self.validate_cab_results()

    def run(self):
        try:

            self.init_tc()
            self.cleanup()
            # Export as EML Files
            self.compliancesearch_keyword_search(
                self.search_keyword_eml_export)
            self.perform_export("EML")
            time.sleep(30)
            # Export as MSG Files
            self.cleanup()
            self.compliancesearch_keyword_search(
                self.search_keyword_msg_export)
            self.perform_export("MSG")
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
