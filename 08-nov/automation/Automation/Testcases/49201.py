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
import socket
from datetime import datetime
from AutomationUtils import logger, config, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Server import serverutils
from Server.Monitoring.monitoringhelper import MonitoringHelper
from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep
from Web.WebConsole.LogMonitoring.home import Home
from Web.WebConsole.LogMonitoring.navigator import Navigator
from Web.WebConsole.LogMonitoring.upload import Upload
from Web.WebConsole.webconsole import WebConsole
from Reports.utils import TestCaseUtils

_CONFIG = config.get_config()
_MONITORING_CONFIG = serverutils.get_logmonitoring_config()

class TestCase(CVTestCase):
    """Uploading a text file against an on demand policy in web console"""


    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Uploading a text file against an on demand policy in web console"
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
        self.machine_name = self.commcell.commserv_hostname

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.web_console = WebConsole(self.browser, self.machine_name)

        self.lmhome = Home(self.web_console)
        self.lmupload = Upload(self.web_console)
        self._nav = Navigator(self.web_console)

        self.mobj = Machine(socket.gethostname())
        if self.mobj.check_directory_exists(constants.TEMP_DIR):
            self.mobj.remove_directory(constants.TEMP_DIR)
        self.mobj.create_directory(constants.TEMP_DIR)

        self.path = self.mobj.join_path(constants.TEMP_DIR, _MONITORING_CONFIG.PATH)
        self.log.info("Creating a text file for monitoring policy content")
        if self.mobj.check_directory_exists(self.path):
            self.mobj.remove_directory(self.path)
        self.mobj.create_file(self.path, _MONITORING_CONFIG.CONTENT * 28)

        self.csobj = Machine(self.commcell.commserv_name, self.commcell)
        self.staging = self.csobj.join_path(self.csobj.client_object.install_directory,
                                            _MONITORING_CONFIG.TEMP,
                                            _MONITORING_CONFIG.STAGING_AREA)
        self.log.info("Creating a staging area for on demand policy")
        if self.csobj.check_directory_exists(self.staging):
            self.csobj.remove_directory(self.staging)
        self.csobj.create_directory(self.staging)

    @TestStep()
    def start_step1(self):
        """Creating an on demand monitoring policy"""
        self.monitoring.create_monitoring_policy(
            self.policy, _MONITORING_CONFIG.Templates.on_demand,
            self.tcinputs["Index_Server"],
            self.tcinputs["ClientName"], self.staging, run=False)

    @TestStep()
    def start_step2(self):
        """Uploading the text file in log monitoring application in web console"""
        self.web_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                               self.inputJSONnode['commcell']['commcellPassword'])
        self.web_console.wait_till_load_complete()
        self.web_console.goto_log_monitoring()
        self._nav.go_to_upload()
        self.lmupload.upload(self.path, self.policy)

        self.log.info("Adding a delay of 15 seconds for completion of upload operation")
        self.utility.sleep_time(15)

    @TestStep()
    def start_step3(self):
        """Validation upload and indexing of the text file"""
        status = self.lmupload.get_upload_status()
        if status == "Successfully Indexed":
            self.log.info("Successfully uploaded and indexed the file")
        else:
            raise Exception("Failed to upload/index the file")

        self._nav.go_to_lm_homepage()
        if not self.lmhome.is_exists_policy(self.policy):
            raise Exception("Failed to find the policy on home page")
        if not self.lmhome.is_exists_tagname(_MONITORING_CONFIG.TAG_NAME):
            raise Exception("Failed to find the tag name on home page")

    @TestStep()
    def start_step4(self):
        """Checking whether the staging area is cleared or not"""
        if self.csobj.get_folder_size(self.staging) == 0:
            self.log.info("The staging area is cleared successfully")
        else:
            raise Exception("Failed to clear the staging area")

    def run(self):
        try:
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.start_step3()
            self.start_step4()
        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.web_console)
            Browser.close_silently(self.browser)
            self.log.info("Deleting the content file")
            if self.mobj.check_directory_exists(constants.TEMP_DIR):
                self.mobj.remove_directory(constants.TEMP_DIR)
            self.log.info("Deleting the staging area file")
            if self.csobj.check_directory_exists(self.staging):
                self.csobj.remove_directory(self.staging)
            self.monitoring.cleanup_policies()
