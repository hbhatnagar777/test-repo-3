# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                              - initialize TestCase class
    setup()                                 - Setup
    cc_login()                              - Login to command center
    navigate_to_page()                      - Navigate to specific page
    cleanup()                               - Cleanup the resources on IBMi client
    run()                                   - run function of this test case

Input Example:

    "testCases":
            {
                "70523":
                        {
                            "AgentName": "File System",
                            "PlanName":"Test-Auto",
                            "AgentName": "File System",
                            "ClientName": "Existing-client",
                            "TestPath": "/QSYS.LIB",
                            "UserName": <client_user>,
                            "Password": <client_password>
                        }
            }

"""
import datetime
import time

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Overview
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Validation of check readiness for IBMi client from command center."
        self.helper = None
        self.browser = None
        self.display_name = None
        self.fsAgent = None
        self.fsSubclient = None
        self.admin_console = None
        self.client_machine = None
        self.navigator = None
        self.Rfile_servers = None
        self.table = None
        self.page = None
        self.overview = None
        self.script_location = None
        self.duration = None
        self.tcinputs = {
            "AgentName": None,
            "ClientName": None,
            "PlanName": None,
            "TestPath": None,
            "HostName": None,
            "UserName": None,
            "Password": None
        }

    def setup(self):
        """ Initial configuration for the test case. """

        try:
            # Initialize test case inputs
            self.log.info("***TESTCASE: %s***", self.name)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.display_name = self.commcell.clients.get(self.tcinputs['ClientName']).display_name
            self.script_location = "/tmp/cv_automation_tc.sh"
            self.duration = 450

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def cc_login(self):
        """Login to command center"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                 password=self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.Rfile_servers = FileServers(self.admin_console)
        self.table = Rtable(self.admin_console)
        self.page = PageContainer(self.admin_console)
        self.overview = Overview(self.admin_console)

    @test_step
    def navigate_to_page(self, page=None):
        """Navigates to requested page"""
        if page:
            self.log.info("Navigating to {0}".format(page))
        else:
            self.log.info("Navigating to File servers tab")
        self.Rfile_servers.navigate_to_file_server_tab()
        if page == "Check_readiness_from_file_servers":
            self.table.access_action_item(self.display_name,
                                          self.admin_console.props['label.readinessCheck'])
            self.admin_console.wait_for_completion()

        if page == "client_overview_page":
            self.Rfile_servers.access_server(self.display_name)

    @test_step
    def cleanup(self):
        """Cleanup the data generated on IBMi client"""
        self.client_machine.reconnect()
        self.client_machine.run_ibmi_command(command="rm -rf {0}".format(self.script_location))

    def run(self):
        try:
            self.cc_login()
            self.log.info("Check-readiness test is running from Manage--> File servers page. and "
                          "Client details page")

            self.log.info("# # # # # # # # # CHECK READINESS TEST CYCLE #1 # # # # # # # # #")
            self.log.info("# # # # # # # # # BEFORE ENDING CLIENT SERVICES # # # # # # # # #")
            self.log.info("# # # # # # # # # SERVICES EXPECTED TO BE READY # # # # # # # # #")

            self.navigate_to_page("Check_readiness_from_file_servers")
            self.log.info("# # # # # # # # # VALIDATE FROM FILE SERVER PAGE # # # # # # # #")
            if not self.overview.is_ibmi_client_status_ready_under_check_readiness_page():
                raise CVTestStepFailure("IBMi client is expected to be in Ready state.")

            self.navigate_to_page("client_overview_page")
            self.log.info("# # # # # # # # # VALIDATE FROM OVERVIEW PAGE # # # # # # # #")
            if not self.overview.is_ibmi_client_status_ready_under_overview_page():
                raise CVTestStepFailure("IBMi client is expected to be in Ready state in overview page.")

            self.log.info("# # # # # # # # # VALIDATE FROM IBMi CLIENT PAGE # # # # # # # #")
            self.page.access_page_action(self.admin_console.props['label.readinessCheck'])
            if not self.overview.is_ibmi_client_status_ready_under_check_readiness_page():
                raise CVTestStepFailure("IBMi client is expected to be in Ready state.")

            self.log.info("Client services and SSH will be ending now")
            self.client_machine.halt_ssh_and_cv_services(duration=self.duration,
                                                         script_path=self.script_location)
            services_ended_time = datetime.datetime.now()
            self.log.info("SSH & CV services ended IBMi client @ {0}".format(services_ended_time))
            time.sleep(10)
            self.log.info("# # # # # # # # # CHECK READINESS TEST CYCLE #2 # # # # # # # # #")
            self.log.info("# # # # # # # # # AFTER ENDING CLIENT SERVICES  # # # # # # # # #")
            self.log.info("# # # # # # # # # SERVICES EXPECTED TO BE NOT READY # # # # # # #")

            self.navigate_to_page("Check_readiness_from_file_servers")
            self.log.info("# # # # # # # # # VALIDATE FROM FILE SERVER PAGE # # # # # # # #")
            if self.overview.is_ibmi_client_status_ready_under_check_readiness_page():
                raise CVTestStepFailure("IBMi client is expected to be in Not-Ready state.")

            self.navigate_to_page("client_overview_page")
            self.log.info("# # # # # # # # # VALIDATE FROM OVERVIEW PAGE # # # # # # # #")
            if self.overview.is_ibmi_client_status_ready_under_overview_page():
                raise CVTestStepFailure("IBMi client is expected to be in Not-Ready state in overview page.")

            self.log.info("# # # # # # # # # VALIDATE FROM IBMi CLIENT PAGE # # # # # # # #")
            self.page.access_page_action(self.admin_console.props['label.readinessCheck'])
            if self.overview.is_ibmi_client_status_ready_under_check_readiness_page():
                raise CVTestStepFailure("IBMi client is expected to be in Not-Ready state.")

            while True:
                if datetime.datetime.now().timestamp() - services_ended_time.timestamp() < self.duration:
                    time.sleep(self.duration/5)
                else:
                    self.log.info("Client service stopped at : time is {0}".format(services_ended_time))
                    self.log.info("Client service should be started by now time is {0}".format(datetime.datetime.now()))
                    time.sleep(10)  # wait for a minute before trying next check-readiness
                    self.client_machine.reconnect()
                    break
            self.log.info("# # # # # # # # # CHECK READINESS TEST CYCLE #3 # # # # # # # # #")
            self.log.info("# # # # # # # # # AFTER STARTING CLIENT SERVICES  # # # # # # # #")
            self.log.info("# # # # # # # # # SERVICES EXPECTED TO BE READY # # # # # # # # #")

            self.navigate_to_page("Check_readiness_from_file_servers")
            self.log.info("# # # # # # # # # VALIDATE FROM FILE SERVER PAGE # # # # # # # #")
            if not self.overview.is_ibmi_client_status_ready_under_check_readiness_page():
                raise CVTestStepFailure("IBMi client is expected to be in Ready state.")

            self.navigate_to_page("client_overview_page")
            self.log.info("# # # # # # # # # VALIDATE FROM OVERVIEW PAGE # # # # # # # #")
            if not self.overview.is_ibmi_client_status_ready_under_overview_page():
                raise CVTestStepFailure("IBMi client is expected to be in Ready state in overview page.")

            self.log.info("# # # # # # # # # VALIDATE FROM IBMi CLIENT PAGE # # # # # # # #")
            self.page.access_page_action(self.admin_console.props['label.readinessCheck'])
            if not self.overview.is_ibmi_client_status_ready_under_check_readiness_page():
                raise CVTestStepFailure("IBMi client is expected to be in Ready state.")

            self.log.info("Final check-readiness test by clicking check-readiness button from check-readiness page")
            self.admin_console.click_button("Check readiness")
            self.log.info("# # # # # # # # # VALIDATE FROM REDO OF CHECK-READINESS PAGE # # # # # # # #")
            if not self.overview.is_ibmi_client_status_ready_under_check_readiness_page():
                raise CVTestStepFailure("IBMi client is expected to be in Ready state.")

            self.log.info("* * * * CHECK-READINESS VALIDATION FROM FILE SERVERS PAGE AND "
                          "FROM IBMi CLIENT OVERVIEW PAGE IS COMPLETED * * * *")
            self.cleanup()
            self.log.info("**IBMi - Check readiness validation from Command center has completed successfully **")
            self.log.info("******TEST CASE COMPLETED SUCCESSFULLY AND PASSED******")

        except Exception as exception:
            handle_testcase_exception(self, exception)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.log.info("Logout from command center completed successfully")
