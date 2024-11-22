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
    __init__()                                          -- initialize TestCase class
    init_tc()                                           -- initialize pre-requisites
    run_send_log()                                      -- To run sendLogs job
    all_received__send_log_bundle()                     -- checking all received send log
                                                           chunck size
    verify_data_collected_from_all_send_log_bundle()    -- checking whether extracted file
                                                           contain data from
    run()                                               -- run function of this test case

Input Example:

    "testCases":
            {
                "60765":
                        {
                            "GatewayClientName": " gateway client name"
                        }
            }

"""
import os
import re
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception
from cvpysdk.internetoptions import InternetOptions
from cvpysdk.client import Clients
from Reports.SendLog.utils import SendLogUtils

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Sendlogs: sendlogs job with proxy client"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.browser = None
        self.admin_console = None
        self.send_log = None
        self.job_id = None
        self.commcell_id = None
        self.path = None
        self.commcell_name = None
        self.navigator = None
        self.send_log_utils = None
        self.commserv_client = None
        self.internet = None
        self.download_directory = None
        self.directory = None
        self.gateway_client = None
        self.tcinputs = {
            "GatewayClientName": None
        }
        self.name = " sendlogs job with proxy client"
        self.controller_machine = None
        self.gateway_machine = None

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.commcell_name = self.commcell.commserv_name
            self.commserv_client = self.commcell.commserv_client
            self.controller_machine = Machine()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.internet = InternetOptions(self.commcell)
            self.gateway_client = Clients(self.commcell).get(self.tcinputs["GatewayClientName"])
            self.gateway_machine = Machine(self.gateway_client)
            self.internet.set_gateway_for_sendlogs(self.gateway_client.client_name)
            self.send_log_utils = SendLogUtils(self, self.controller_machine)
            self.download_directory = self.send_log_utils.create_directory_for_given_path \
                ("TC60765")
            navigator = self.admin_console.navigator
            navigator.navigate_to_commcell()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_send_log(self):
        """Running SendLog job"""
        comm_cell = Commcell(self.admin_console)
        comm_cell.access_sendlogs()
        send_log = SendLogs(self.admin_console)
        info_list = send_log.Informationlist
        advanced_list = send_log.Advancedlist
        send_log.deselect_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        send_log.deselect_information(information_list=[info_list.OS_LOGS, info_list.MACHINE_CONFIG,
                                                        info_list.ALL_USERS_PROFILE])
        self.job_id = send_log.submit()
        job_obj = self.commcell.job_controller.get(self.job_id)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.job_id}] failed"
            )

    @test_step
    def verify_gateway_log(self):
        """Verifying that gateway is used for sendlogs job"""

        commvault_log_path = self.gateway_client.log_directory
        cvd_log = os.path.join(commvault_log_path, "cvd.log")
        file_content = self.gateway_machine.read_file(cvd_log)
        sendlog_file_pattern = "sendLogFiles_(.*)" + self.job_id + ".7z.001] uploaded successfully"
        sendlog_job_text_exists = re.findall(sendlog_file_pattern, file_content)
        if sendlog_job_text_exists:
            self.log.info(
                "gateway cvd.log has sendlog job details ")
        else:
            raise CVTestStepFailure(
                f"Send log job id [{self.job_id}] is not found in the cvd.log on "
                f"[{self.gateway_client.client_name}] gateway client"
            )

    def run(self):
        try:
            self.init_tc()
            self.run_send_log()
            self.verify_gateway_log()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.internet.set_no_gateway()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
