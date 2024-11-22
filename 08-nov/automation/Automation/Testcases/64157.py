# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Mainfile for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                            --  initialize TestCase class
    init_tc()                                             --  Initialize pre-requisites
    run()                                                 --  run function of this test case
    validate_lower_client_sp()                            -- validates that the client is in lower sp
    run_sendlog()                                         -- runs the sendlogs on a client
    verify_client_logs()                                  -- verifies the logs on a client

Input Example:

    "testCases":
            {
                "64157":
                        {
                          "ClientName": ""
                        }
            }

"""

import os
import time
from AutomationUtils.machine import Machine
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Reports.utils import TestCaseUtils
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from cvpysdk.license import LicenseDetails
from Reports.SendLog.utils import SendLogUtils

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """This test case verifies basic sendlogfiles feature"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.browser = None
        self.admin_console = None
        self.send_log = None
        self.info_list = None
        self.file_server = None
        self.commcell_id = None
        self.commcell_name = None
        self.commserv_machine = None
        self.machine = None
        self.utils: TestCaseUtils = None
        self.client = None
        self.commserv_client = None
        self.local_machine = None
        self.base_path = None
        self.curr_path = None
        self.send_log_utils = None
        self.sjobid = None
        self.jobid_list = []
        self.path = None
        self.comm_cell = None
        self.name = "Sendlogs Backward Compatibility"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.utils = TestCaseUtils(self,
                                       username=self.inputJSONnode["commcell"]["commcellUsername"],
                                       password=self.inputJSONnode["commcell"]["commcellPassword"])
            self.commserv_client = self.commcell.commserv_client
            self.commserv_machine = Machine(self.commserv_client)
            self.machine = Machine()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.admin_console.navigator.navigate_to_servers()
            self.admin_console.wait_for_completion()
            time.sleep(5)
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.file_server = FileServers(self.admin_console)
            licence = LicenseDetails(self.commcell)
            self.commcell_id = licence.commcell_id_hex
            self.commcell_name = self.commcell.commserv_name
            self.comm_cell = Commcell(self.admin_console)
            self.local_machine = Machine()
            self.send_log = SendLogs(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def validate_lower_client_sp(self):
        """Validating if the client's version is lower than CS's version"""
        cs_sp = self.commcell.commserv_client.service_pack
        client_sp = self.client.service_pack
        if client_sp == cs_sp:
            raise CVTestStepFailure(
                f"Both client and CS are in same SP : {cs_sp}"
            )
        elif client_sp > cs_sp:
            raise CVTestStepFailure(
                f"Client SP is higher than CS SP. This is a bug"
            )
        else:
            self.log.info(f"Client is in lower SP, proceed to validate sendlogs.")
            self.log.info(f"CS SP : {cs_sp}     Client SP: {client_sp}")

    @test_step
    def run_sendlog(self):
        """Running the sendlog on a client"""
        self.file_server.action_sendlogs(self.tcinputs["ClientName"])
        info_list = self.send_log.Informationlist
        self.send_log.deselect_information(information_list=[info_list.OS_LOGS, info_list.MACHINE_CONFIG,
                                                             info_list.ALL_USERS_PROFILE])
        self.send_log.disable_email_notification()
        self.sjobid = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.sjobid)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.sjobid}] failed"
            )

    @test_step
    def verify_client_logs(self):
        """Verifying the logs collected from the client side"""
        self.path = os.path.join(self.path, self.tcinputs["ClientName"])
        entities_dict = {'cvd.log': False, 'cvfwd.log': False}
        file_list = self.local_machine.get_files_in_path(self.path)
        self.send_log_utils.verify_entities(file_list, entities_dict, self.path)

    def run(self):
        """Run function of this test case"""
        try:
            self.init_tc()
            self.validate_lower_client_sp()
            self.run_sendlog()
            self.log.info('Waiting for 20 mins to check file present at location ' +
                          _STORE_CONFIG.Reports.uncompressed_logs_path
                          + ' for send log job id ' + self.sjobid)
            time.sleep(1200)
            self.path = self.send_log_utils.get_uncompressed_path(self.sjobid, self.jobid_list)
            self.verify_client_logs()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
