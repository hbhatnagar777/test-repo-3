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
from Web.WebConsole.LogMonitoring.search import Search
from Web.WebConsole.webconsole import WebConsole
from Reports.utils import TestCaseUtils

_CONFIG = config.get_config()
_MONITORING_CONFIG = serverutils.get_logmonitoring_config()

class TestCase(CVTestCase):
    """Deleting and erasing data from a search in Log Monitoring Application"""


    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Deleting and erasing data from a search in Log Monitoring"
        self.feature = self.features_list.NOTAPPLICABLE
        self.product = self.products_list.LOGMONITORING
        self.tcinputs = {
            "Index_Server": None
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

        self.log.info("Initializing the variable names for the test case")
        now = datetime.now()
        self.policy = "policy{0}".format(now)
        self.search = "search{0}".format(now)
        self.machine_name = self.commcell.commserv_hostname

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.web_console = WebConsole(self.browser, self.machine_name)
        self.lmhome = Home(self.web_console)
        self.lmsearch = Search(self.web_console)
        self.lmactions = Actions(self.web_console)
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
        """Performing the search and erase operations on data in webconsole"""
        self.web_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                               self.inputJSONnode['commcell']['commcellPassword'])
        self.web_console.wait_till_load_complete()
        self.web_console.goto_log_monitoring()
        self.lmhome.click_policy(self.policy)
        self.lmsearch.save_search(self.search)
        self.lmactions.delete_search()
        self.lmactions.erase_data()

    @TestStep()
    def start_step3(self):
        """Verifying whether the data is successfully erased"""
        count_log_lines = self.lmsearch.get_log_lines_count()
        if count_log_lines == 0:
            self.log.info("Search data erased successfully")
        else:
            raise Exception("Search data erase failed : log lines still seen in results")

    def run(self):
        try:
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.start_step3()
        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.web_console)
            Browser.close_silently(self.browser)
            self.log.info("Deleting the content file")
            if self.mobj.check_directory_exists(self.path):
                self.mobj.remove_directory(self.path)
            self.monitoring.cleanup_policies()
