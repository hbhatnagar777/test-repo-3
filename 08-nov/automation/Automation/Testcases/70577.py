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
    __init__()      --  initialize TestCase class
    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case
"""


import traceback

from AutomationUtils.config import get_config

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[Global CC]: Validate Switcher and Single Sign-On (SSO) Functionality"
        self.browser = None
        self.admin_console = None
        self.config = None
        self.exp = None
        self.tcinputs = {}
        self.sc_to_ignore = self.tcinputs.get("SCToIgnore", [])

    def setup(self):
        """Setup function of this test case"""
        self.config = get_config()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator

        # switch to global view
        self.log.info("Switching to Global view...")
        self.navigator.switch_service_commcell('Global')
        self.global_url = self.admin_console.current_url()
        self.metrics_url = self.global_url.split("//")[1].split("/")[0]

        # This gets commcell names from the commcell switcher and removes global/router commcell name
        self.service_commmcell_list = [item[1] if not item[0] else None for item in self.navigator.service_commcells_displayed()]
        self.service_commmcell_list.remove(None)
        self.service_commmcell_list.pop(0)

    def run(self):
        """Run function of this test case"""
        try:

            retry_count = 5
            while retry_count:
                try:
                    for service_commcell in self.service_commmcell_list:
                        if service_commcell in self.sc_to_ignore:
                            self.log.info(f"Ignoring service commcell {service_commcell} as told explicitly")
                        else:
                            self.navigator.switch_service_commcell(service_commcell)
                            if self.metrics_url in self.admin_console.current_url():
                                self.log.info(f"Current Page: {self.admin_console.current_url()}")
                                raise CVTestStepFailure(
                                    f"Clicking on {service_commcell} from commcell switcher did not redirect; "
                                    f"Current page {self.admin_console.current_url()}")

                            self.admin_console.navigate(self.global_url)
                            self.admin_console.wait_for_completion()

                    break
                except Exception as exp:
                    if retry_count == 1:
                        raise exp

                    self.log.info(traceback.format_exc())
                    self.tear_down()
                    retry_count -= 1
                    self.log.info("TC Failed, trying again")
                    self.setup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
