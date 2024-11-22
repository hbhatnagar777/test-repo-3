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
    """Class for executing Unix sys logs test of Log Monitoring"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Log Monitoring test case for Unix Sys Logs Template"
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

        self.unix_clients, _num = self.utility.get_ready_clients(
            self.commcell.clients.all_clients, num=1, validate=False, os_type="Unix")

        if not self.unix_clients:
            raise Exception("No Unix client with successfull connectivity to commcell exists")

        now = datetime.now()
        self.log.info("Initializing the variable names for the test case")

        self.policy = "policy{0}".format(now)
        self.machine_name = self.commcell.commserv_hostname

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.web_console = WebConsole(self.browser, self.machine_name)
        self.lmhome = Home(self.web_console)

        self.mobj = Machine(self.unix_clients[0], self.commcell)

        if self.mobj.check_file_exists(_MONITORING_CONFIG.CRON_PATH) == False:
            raise Exception("The source file doesnt exist on the client")

    def run(self):
        """Main function for test case execution"""

        try:
            self.monitoring.create_monitoring_policy(
                self.policy, _MONITORING_CONFIG.Templates.sys_log,
                self.tcinputs["Index_Server"],
                self.unix_clients[0], _MONITORING_CONFIG.CRON_PATH)

            self.log.info(
                "Adding a delay of 100 seconds for pushing the indexed data to webconsole")
            self.utility.sleep_time(100)

            self.web_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                   self.inputJSONnode['commcell']['commcellPassword'])
            self.web_console.wait_till_load_complete()
            self.web_console.goto_log_monitoring()

            count = self.lmhome.get_count_policy(self.policy)
            if count != "0":
                self.log.info("Unix sys logs indexed successfully")

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.web_console)
            Browser.close_silently(self.browser)
            self.monitoring.cleanup_policies()
