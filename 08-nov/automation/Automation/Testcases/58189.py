# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Testcase for verifying if Adminconsole comes up when tomcat process is stopped.

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  Initialize TestCase class

    run()           --  Run function of this testcase

"""

import time
from cvpysdk.commcell import Commcell
from selenium.common.exceptions import WebDriverException
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.anomalies.webserver_anomaly import WebserverAnomaly
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory


class TestCase(CVTestCase):
    """Testcase for verifying if Adminconsole comes up when Tomcat service is stopped."""

    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.tcinputs = {
            "WebserverACClient": None
        }
        self.name = "Negative Automation: Verify if adminconsole comes up after stopping tomcat service."

    def run(self):
        """ Main function for testcase execution. Tries AC login when Tomcat is in stopped state."""
        webconsole_hostname = self.inputJSONnode['commcell']['webconsoleHostname']
        commcell_username = self.inputJSONnode['commcell']['commcellUsername']
        commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        client_name = self.tcinputs["WebserverACClient"]
        log = logger.get_log()
        log.info("Started executing %s testcase", self.id)
        try:
            commcell = Commcell(
                webconsole_hostname=webconsole_hostname,
                commcell_username=commcell_username,
                commcell_password=commcell_password)
            wc = WebserverAnomaly(commcell_object=commcell, client_name=client_name)
            self.log.info("Starting Tomcat service before beginning the next steps.")
            wc.start_tomcat()
            self.log.info("Sleeping for a minute.")
            time.sleep(60)
            browser = BrowserFactory().create_browser_object()
            browser.open()
            admin_console = AdminConsole(browser, client_name)
            self.log.info("Stopping Tomcat service.")
            wc.stop_tomcat()
            self.log.info("Sleeping for a minute.")
            time.sleep(60)
            try:
                admin_console.login()
            except WebDriverException:
                self.log.info("Adminconsole login is failing as IIS is in stopped state.")
            self.log.info("Starting Tomcat service.")
            wc.start_tomcat()
            browser.close()
        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception occurred while executing this test case.")
            raise exp
