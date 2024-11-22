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
    __init__()                                   -- Initializes TestCase class

    generate_sensitive_data()                    -- Generate an EICAR file

    init_tc()                                    -- Initial configuration for the testcase

    run_data_curation()                          -- Runs the data curation job on the client

    core_validation()                            -- Verifies that the delete anomaly option deletes the core

    cleanup()                                    -- Runs cleanup

    run()                                        -- Run function for this testcase
"""
import datetime
import os

import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.utils.activateutils import ActivateUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.GovernanceAppsPages.UnusualFileActivity import \
    UnusualFileActivity
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVWebAutomationException
from Web.Common.page_object import TestStep, handle_testcase_exception

from cvpysdk.client import Client
from cvpysdk.index_server import IndexServer
from cvpysdk.job import Job
from Web.AdminConsole.Components.table import Rtable, Table
from Web.AdminConsole.Components.panel import DropDown, PanelInfo, ModalPanel, RDropDown, RPanelInfo


class TestCase(CVTestCase):
    """Class for executing delete anomaly option"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Check the license usage"
        self.tcinputs = {
            
        }
        # Testcase constants
        self.browser = None
        self.admin_console = None
        self.test_case_error = None
    
    def navigate_to_license_summary(self):
        """
            Navigates to the license summary report
        """
        self.navigator.navigate_to_license()
        
        table = Table(self.admin_console, title="Data Insights Licenses")
        title_xpath = "//*[contains(text(),'Data Insights Licenses')]"
        self.admin_console.scroll_into_view(title_xpath)
        table.expand_grid()
        table.access_link_by_column("Sensitive Data For Files", "Sensitive Data For Files")
        self.admin_console.wait_for_completion()
        dropdown = DropDown(self.admin_console)
        dropdown.select_drop_down_values(values = ["Threat Scan For Files"], drop_down_label= "Activate Licence Type")

        threat_scan_usage_table = Rtable(self.admin_console, title = "Data insights usage per client - current details")
        num_clients = threat_scan_usage_table.get_total_rows_count()
        if num_clients == self.analyzed_servers:
            self.log.info("License count matched")
        else:
            raise CVTestStepFailure("License count unmatched")


    def init_tc(self):
        """ Initial configuration for the test case"""
        try:
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']

         
            self.activateutils = ActivateUtils()           
            
            
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=username, password=password)
            self.navigator = self.admin_console.navigator
            self.file_activity = UnusualFileActivity(self.admin_console)
            self.gdpr_obj = GDPR(self.admin_console, self.commcell)
            
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

   
    @test_step
    def count_analyzed_servers(self):
        """Count TS servers analyzed"""


        # Navigate to unusual file activity
        self.navigator.navigate_to_unusual_file_activity()
        table = Rtable(self.admin_console, title = "Unusual file activity")
        self.analyzed_servers = table.get_total_rows_count()
       
    
    def run(self):
        try:
            self.init_tc()
            self.count_analyzed_servers()
            self.navigate_to_license_summary()
            
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
