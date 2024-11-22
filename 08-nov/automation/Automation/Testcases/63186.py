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
    __init__()                                            --  initialize TestCase class
    init_tc()                                             --  Initialize pre-requisites
    run_send_log_on_cluster_client()                      --  run sendlogs on cluster client
    verify_logs()                                         --  verify the logs from the cluster client
    run()                                                 --  run function of this test case

Input Example:

    "testCases":
            {
                "63186":
                        {
                         "ClientName" : "C1",
                         "ActiveClusterClientName" : "A1"
                        }
            }


"""

import os
import time
from AutomationUtils.config import get_config
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Reports.SendLog.utils import SendLogUtils
from AutomationUtils.machine import Machine

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """send logs by JobID"""
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
        self.sjob_id = None
        self.machine = None
        self.path = None
        self.job = None
        self.commcell_name = None
        self.navigator = None
        self.send_log_utils = None
        self.file_server = None
        self.send_log = None
        self.client_name = None
        self.active_client_name = None
        self.name = "Sendlogs Validation on Clustered Setup"
        self.tcinputs = {}

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.commcell_name = self.commcell.commserv_name
            self.machine = Machine()
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.client_name = self.client.client_name
            self.active_client_name = self.tcinputs['ActiveClusterClientName']
            self.send_log = SendLogs(self.admin_console)
            self.file_server = FileServers(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_send_log_on_cluster_client(self):
        """Run sendlogs operation on cluster client"""
        self.admin_console.navigator.navigate_to_file_servers()
        self.admin_console.wait_for_completion()
        self.file_server.action_sendlogs(self.client_name)
        info_list = self.send_log.Informationlist
        self.send_log.deselect_information(information_list=[info_list.OS_LOGS, info_list.MACHINE_CONFIG,
                                                             info_list.ALL_USERS_PROFILE])
        self.send_log.disable_self_email_notification()
        self.sjob_id = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.sjob_id)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.sjob_id}] failed"
            )

    @test_step
    def verify_logs(self):
        """ Verify the logs from cluster client """
        self.path = os.path.join(self.path, self.active_client_name)
        entities_dict = {'cvd.log': False, 'cvfwd.log': False}
        file_list = self.machine.get_files_in_path(self.path, recurse=False)
        self.send_log_utils.verify_entities(file_list, entities_dict, self.path)

    def run(self):
        try:
            self.init_tc()
            self.run_send_log_on_cluster_client()
            self.log.info(f'Waiting for 15 minutes to check file present at network location for '
                          f'send log job id {self.sjob_id}')
            time.sleep(900)
            self.path = self.send_log_utils.get_uncompressed_path(self.sjob_id)
            self.verify_logs()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
