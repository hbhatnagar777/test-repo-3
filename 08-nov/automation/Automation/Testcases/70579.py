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
from random import choice

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.dashboard import RDashboard
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
        self.name = "[Global CC]: Validate Dashboard Functionality"
        self.browser = None
        self.admin_console = None
        self.config = None
        self.exp = None

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
        self.navigator.navigate_to_dashboard()
        self.global_url = self.admin_console.current_url()
        self.metrics_url = self.global_url.split("//")[1].split("/")[0]
        self.service_commmcell_list = [item[1] for item in self.admin_console.navigator.service_commcells_displayed()]
        self.service_commmcell_list.pop(0)

    def run(self):
        """Run function of this test case"""
        try:

            retry_count = 5
            while retry_count:
                try:
                    if retry_count < 5:
                        self.setup()

                    # Verify if count in individual commcell is same shown in global
                    self.global_dashboard_data = RDashboard(self.admin_console).get_pane_and_entity_titles(True, True)

                    for commcell in self.service_commmcell_list:
                        self.navigator.switch_service_commcell(commcell)
                        self.admin_console.close_warning_dialog()
                        self.navigator.navigate_to_dashboard()
                        dashboard_data = (
                            RDashboard(self.admin_console).get_pane_and_entity_titles(get_count=True))

                        self.verify_dashboard_count_commcell(commcell, dashboard_data)

                        self.admin_console.navigate(self.global_url)
                        self.admin_console.wait_for_completion()
                        self.admin_console.close_warning_dialog()

                    self.verify_dashboard_redirection(self.global_dashboard_data)

                except Exception as exp:
                    if retry_count == 1:
                        raise exp

                    self.log.info(traceback.format_exc())

                    # teardown here
                    self.tear_down()

                    retry_count -= 1
                    self.log.info("TC Failed, trying again")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def verify_dashboard_count_commcell(self, commcell_name, dashboard_data):
        """ Method to verify if data from local service commcell and obtained from global matches """
        # Need to remove this node, since we don't have this on global dashboard
        if "CWE/CWW" in dashboard_data:
            dashboard_data.pop("CWE/CWW")

        for container in dashboard_data.keys():
            if dashboard_data[container]:
                for kpi in dashboard_data[container].keys():
                    self.compare(self.global_dashboard_data[container][kpi].get(commcell_name),
                                 dashboard_data[container][kpi], kpi)

    def compare(self, global_data, local_data, tile):
        """ Method to compare global and local data for a tile and raise errors if the count doesn't match"""
        if not global_data:
            global_data = '0'

        global_data = int(global_data.replace(',', ''))
        local_data = int(local_data.replace(',', ''))

        if global_data != local_data:
            self.log.info(global_data)
            self.log.info(local_data)
            raise CVTestStepFailure(f"Count shown in global dashboard and local for {tile} does not match")

        self.log.info(f"Count matches for tile {tile}: {local_data}")

    def verify_dashboard_redirection(self, global_dashboard_data):
        """ Method to verify if on clicking dashboard tile of a service commcell user is redirected """
        for container in global_dashboard_data.keys():
            kpis = global_dashboard_data[container].keys()
            kpi = choice(kpis)

            for commcell in global_dashboard_data[container].get(kpi):
                RDashboard(self.admin_console).click_on_commcell_from_callout(commcell, container, kpi)
                self.admin_console.wait_for_completion()
                self.admin_console.close_warning_dialog()

                if self.metrics_url in self.admin_console.current_url():
                    raise CVTestStepFailure(f"Clicking on {container} > {kpi} > {commcell} did not redirect")

                # Hacky way to go back to global dashboard
                self.browser.switch_to_first_tab()
                # This is to make sure even if page doesn't redirect to new tab we are going back
                if self.metrics_url not in self.admin_console.current_url():
                    self.admin_console.navigate(self.global_url)
                    self.navigator.navigate_to_dashboard()

