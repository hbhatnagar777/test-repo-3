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

    setup()         --  setup function of this test case

    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
from datetime import datetime
from AutomationUtils import logger, config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Server import serverutils
from Server.Monitoring.monitoringhelper import MonitoringHelper
from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.WebConsole.LogMonitoring.home import Home
from Web.WebConsole.webconsole import WebConsole
from Reports.utils import TestCaseUtils

_CONFIG = config.get_config()
_MONITORING_CONFIG = serverutils.get_logmonitoring_config()


class TestCase(CVTestCase):
    """Class for executing Commvault logs for Windows clients of Log Monitoring"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Log Monitoring test case for CommVault Logs Template for Windows clients"
        self.feature = self.features_list.NOTAPPLICABLE
        self.product = self.products_list.LOGMONITORING
        self.tcinputs = {
            "Index_Server": None
        }
        self.utils = TestCaseUtils(self)

    def setup(self):
        """Setup function for the test case execution"""
        self.log = logger.get_log()
        self.utility = OptionsSelector(self.commcell)
        self.monitoring = MonitoringHelper(self.commcell)

        self.log.info("Checking for a valid tc input")
        if self.tcinputs["Index_Server"] in ("", "None"):
            raise Exception("Invalid test case input")

        self.log.info("Initializing the variable names for the test case")

        clients_obj = self.commcell.clients

        self.log.info("Checking for the source file on the client")
        self.mobj = Machine(self.commcell.commserv_name, self.commcell)
        self.file_path = self.mobj.join_path(
            clients_obj.get(self.tcinputs["ClientName"]).log_directory,
            _MONITORING_CONFIG.CVD_PATH)
        if self.mobj.check_file_exists(self.file_path) == False:
            raise Exception("The source file doesnt exist on the client")

        now = datetime.now()
        self.policy = "policy{0}".format(now)
        self.machine_name = self.commcell.commserv_hostname
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.web_console = WebConsole(self.browser, self.machine_name)
        self.lmhome = Home(self.web_console)

    def run(self):
        """Main function for test case execution"""

        try:
            self.monitoring.create_monitoring_policy(
                self.policy, _MONITORING_CONFIG.Templates.commvault_logs,
                self.tcinputs["Index_Server"],
                self.tcinputs["ClientName"], self.file_path)

            self.log.info(
                "Adding a delay of 100 seconds for pushing the indexed data to webconsole")
            self.utility.sleep_time(100)

            self.web_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                   self.inputJSONnode['commcell']['commcellPassword'])
            self.web_console.wait_till_load_complete()
            self.web_console.goto_log_monitoring()

            count = self.lmhome.get_count_policy(self.policy)
            if count != "0":
                self.log.info("Windows CommVault Logs indexed successfully")

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.web_console)
            Browser.close_silently(self.browser)
            self.monitoring.cleanup_policies()
