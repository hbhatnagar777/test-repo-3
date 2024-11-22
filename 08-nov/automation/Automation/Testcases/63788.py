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

    verify_dashboard_details()    --  Verify the dashboard details of the self service user

    verify_restore_details()      --  Verify restore job details

    verify_export_job_details()   -- Verify export file job details

    verify_preview_of_mails_for_self_service_user()   --  Verify the preview of the mails

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_Exchange Self Service User Case:
    Basic Validation for Metallic Exchange Self Service User
    """
    TestStep = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic Office 365 Exchange Self Service User Case"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.app_type = None
        self.app_name = None
        self.saml_obj = None
        self.export_job_details = None
        self.utils = TestCaseUtils(self)

    @TestStep
    def verify_dashboard_details(self, dashboard_details) -> None:
        """Verifies the dashboard details with the client page details"""
        self.log.info("VERIFYING THE DETAILS ON BOTH PAGES")
        for entry in dashboard_details["ClientDetailsInfo"]:
            if entry["AgentName"].split()[0] == O365AppTypes.exchange.value:
                client_detail = self.office365_obj.get_self_service_user_details_by_client(entry["App name"])
                self.admin_console.driver.back()
                self.admin_console.wait_for_completion()
                if dashboard_details["User"] == client_detail["Email address"]:
                    self.log.info("User email is matching with the value shown on the self service dashboard")
                else:
                    raise Exception("User email is showing different on both pages. Please check")
                if entry["Backup size"] == client_detail["Active backup size"]:
                    self.log.info(
                        "The backed up size is also showing equal on Self Service Dashboard as well as Client Details Page")
                elif entry["Backup size"] == 'Not available' and client_detail["Active backup size"] == '0 B':
                    self.log.info(
                        "The backed up size is also showing equal on Self Service Dashboard as well as Client Details Page")
                else:
                    raise Exception("Backed up size is different on both pages. Please check.")
                if entry["Items backed up"] == client_detail["Active items backed up"]:
                    self.log.info(
                        "Number of items backed up on both self service dashboard and client details is Equal")
                elif entry["Items backed up"] == 'Not available' and client_detail["Active items backed up"] == '0':
                    self.log.info(
                        "Number of items backed up on both self service dashboard and client details is Equal")
                else:
                    raise Exception("Backed up items count is different on both pages. Please check.")
                if entry["Last backup"] == client_detail["Last backup time"]:
                    self.log.info(
                        "Last backup time is matching with the self service dashboard of the client")
                else:
                    raise Exception("Backup time is different on both pages. Please check.")

        self.log.info("SUCCESSFULLY VERIFIED THE DETAILS ON BOTH PAGES")

    @TestStep
    def verify_restore_details(self, restore_job_detail) -> None:
        """Verify the restore job details"""
        if restore_job_detail["Status"] == "Completed":
            self.log.info("Job Completed successfully")
        else:
            raise Exception("Job did not complete successfully. Please check")
        if self.tcinputs["SAML user name"] in restore_job_detail["Job started by"].lower():
            self.log.info("Verified the job invocation by self service user")
        else:
            raise Exception("Job was not invoked by self service user")
        if int(restore_job_detail["Successful messages"]) > 0:
            self.log.info("Restore count is greater than 0")
        else:
            raise Exception("Restore count is not greater than 0")

    @TestStep
    def verify_export_job_details(self) -> None:
        """Verifies the exported file details on the view exports"""
        if self.export_job_details["Status"] == "Completed":
            self.log.info("Job Completed successfully")
        else:
            raise Exception("Job did not complete successfully. Please check")
        if self.tcinputs["SAML user name"] in self.export_job_details["Job started by"].lower():
            self.log.info("Verified the job invocation by self service user")
        else:
            raise Exception("Job was not invoked by self service user")
        if int(self.export_job_details["No. of successes"]) > 0:
            self.log.info("Restore count is greater than 0")
        else:
            raise Exception("Restore count is not greater than 0")
        if int(self.export_job_details["Total no. of files to be restored"]) == int(self.export_job_details["No of files restored"]):
            self.log.info("All files were restored successfully")
        else:
            raise Exception("No of files restored is not equal to files which were submitted for restore. Please check")
        self.navigator.navigate_to_office365(access_tab=False)
        self.office365_obj.verify_export_file_details_for_self_service_user(
            client_name=self.tcinputs["Name"],
            export_job_details=self.export_job_details,
            verify_download=True
        )

    @TestStep
    def verify_preview_of_mails_for_self_service_user(self) -> None:
        """Verifies the preview of the mails for the self service user"""
        mails = self.office365_obj.fetch_preview_of_mails_for_self_service_user()
        for mail in mails:
            if mail["Preview"] == "" or len(mail["Preview"]) == 0:
                raise Exception("Preview was not fetched for the subject {}".format(mail["Subject"]))

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.tcinputs["SAML user name"],
                                 password=self.tcinputs["SAML user pwd"],
                                 saml=True)
        self.service = HubServices.office365
        self.app_type = O365AppTypes.exchange
        self.navigator = self.admin_console.navigator
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type)

    def run(self):
        """Main function for test case execution"""
        try:
            dashboard_details = self.office365_obj.get_self_service_user_dashboard_details()
            self.verify_dashboard_details(dashboard_details)
            restore_job_details = self.office365_obj.perform_operations_on_self_user_client(
                client_name=self.tcinputs["Name"],
                operation="Restore")
            self.verify_restore_details(restore_job_details)
            self.navigator.navigate_to_office365(access_tab=False)
            self.export_job_details = self.office365_obj.perform_operations_on_self_user_client(
                client_name=self.tcinputs["Name"],
                operation="Export",
                export_as="PST"
            )
            self.verify_export_job_details()
            self.navigator.navigate_to_office365(access_tab=False)
            self.export_job_details = self.office365_obj.perform_operations_on_self_user_client(
                client_name=self.tcinputs["Name"],
                operation="Export",
                export_as="CAB"
            )
            self.verify_export_job_details()
            self.navigator.navigate_to_office365(access_tab=False)
            self.office365_obj.perform_operations_on_self_user_client(
                client_name=self.tcinputs["Name"],
                operation="Download"
            )
            self.verify_preview_of_mails_for_self_service_user()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)