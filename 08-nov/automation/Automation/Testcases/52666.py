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
from Web.Common.page_object import TestStep
from Web.WebConsole.LogMonitoring.actions import Actions
from Web.WebConsole.LogMonitoring.home import Home
from Web.WebConsole.LogMonitoring.manage import Manage
from Web.WebConsole.LogMonitoring.navigator import Navigator
from Web.WebConsole.LogMonitoring.search import Search
from Web.WebConsole.webconsole import WebConsole
from Reports.utils import TestCaseUtils

_CONFIG = config.get_config()
_MONITORING_CONFIG = serverutils.get_logmonitoring_config()


class TestCase(CVTestCase):
    """Class for executing Basic Test of Log Monitoring in WebConsole"""


    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Test of Log Monitoring"
        self.feature = self.features_list.NOTAPPLICABLE
        self.product = self.products_list.LOGMONITORING
        self.tcinputs = {
            "Index_Server":None,
            }
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """Initializing the variables for the test case"""
        self.log = logger.get_log()
        self.utility = OptionsSelector(self.commcell)
        self.monitoring = MonitoringHelper(self.commcell)

        self.log.info("Checking for a valid tc input")
        if self.tcinputs["Index_Server"] in ("", "None"):
            raise Exception("Invalid test case input")

        now = datetime.now()
        self.policy = "policy{0}".format(now)
        self.search = "search{0}".format(now)
        self.alert = "alert{0}".format(now)
        self.schedule = "schedule{0}".format(now)
        self.machine_name = self.commcell.commserv_hostname

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.web_console = WebConsole(self.browser, self.machine_name)

        self.lmhome = Home(self.web_console)
        self.lmsearch = Search(self.web_console)
        self.lmactions = Actions(self.web_console)
        self.lmmanage = Manage(self.web_console)
        self._nav = Navigator(self.web_console)
        self.mobj = Machine(self.commcell.commserv_name, self.commcell)
        self.path = self.mobj.join_path(self.mobj.client_object.install_directory,
                                        _MONITORING_CONFIG.TEMP, _MONITORING_CONFIG.PATH)
        self.log.info("Creating a text file for monitoring policy content")
        if self.mobj.check_directory_exists(self.path):
            self.mobj.remove_directory(self.path)
        self.mobj.create_file(self.path, _MONITORING_CONFIG.CONTENT * 28)

    @TestStep()
    def start_step1(self):
        """Creating and running a monitoring policy"""
        self.monitoring.create_monitoring_policy(
            self.policy, _MONITORING_CONFIG.Templates.simple_text,
            self.tcinputs["Index_Server"],
            self.tcinputs["ClientName"], self.path)

        self.log.info("Adding a delay of 100 seconds for pushing the indexed data to webconsole")
        self.utility.sleep_time(100)

    @TestStep()
    def start_step2(self):
        """Validating the number of log lines indexed and search in webconsole"""
        self.web_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                               self.inputJSONnode['commcell']['commcellPassword'])
        self.web_console.wait_till_load_complete()
        self.web_console.goto_log_monitoring()

        count = self.lmhome.get_count_policy(self.policy)
        if count == _MONITORING_CONFIG.COUNT_LOG_LINES:
            self.log.info("Number of lines indexed validated successfully")
        else:
            raise Exception("Indexing Validation Failed : Number of lines "
                            "indexed do not match the actual data content")

        self.lmhome.click_policy(self.policy)
        self.lmsearch.make_search(_MONITORING_CONFIG.SEARCH_STRING)
        count_log_lines = self.lmsearch.get_log_lines_count()

        if count_log_lines == _MONITORING_CONFIG.SEARCH_LINES:
            self.log.info("Number of log lines are %d", count_log_lines)
            self.log.info("Search validated successfully")
        else:
            raise Exception("Search Validation Failed")
        self.web_console.wait_till_load_complete()

    @TestStep()
    def start_step3(self):
        """Creating an alert, schedule and saving the search to default dashboard"""
        self.lmactions.save_to_dashboard(self.search)
        self.lmactions.create_schedule(self.schedule, _MONITORING_CONFIG.EMAIL)
        self.lmactions.create_alert(self.alert, _MONITORING_CONFIG.EMAIL)

    @TestStep()
    def start_step4(self):
        """Verifying the creation of alert and schedule"""
        self.lmmanage.click_schedules()
        if not self.lmmanage.is_exists_schedule(self.schedule):
            raise Exception("Failed to validate schedule creation")
        self.lmmanage.click_alerts()
        if not self.lmmanage.is_exists_alert(self.alert):
            raise Exception("Failed to validate alert creation")

    @TestStep()
    def start_step5(self):
        """Deleting the search"""
        self._nav.go_to_search()
        self.lmactions.delete_search()

    def run(self):
        try:
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.start_step3()
            self.start_step4()
            self.start_step5()
        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.web_console)
            Browser.close_silently(self.browser)
            self.log.info("Deleting the content file")
            if self.mobj.check_directory_exists(self.path):
                self.mobj.remove_directory(self.path)
            self.monitoring.cleanup_policies()
