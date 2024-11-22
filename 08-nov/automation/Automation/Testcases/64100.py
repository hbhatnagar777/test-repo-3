# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies backup networks UI access based on user permissions 

between a client and a media agent from command center.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case


"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Server.Network.networkhelper import NetworkHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVWebAutomationException
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.AdminConsolePages.NetworkPage import NetworkPage, BackupNetworks
import os
import re

class TestCase(CVTestCase):
    """[Network - Command Center] - Negative Test Case for the DIPs Screen access"""
    
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center - Backup Networks - Negatives testcases for react DIPs screen"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            "tenantAdminUsername": "",
            "tenantAdminPassword": "",
            "commcellUsername": "",
            "commcellPassword": "",
            "tenantUsername": "",
            "tenantPassword": ""
            
        }
    
    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.commserve = self.commcell.commserv_name
            self._network = NetworkHelper(self)
            self.option = OptionsSelector(self.commcell)
            self.browser = BrowserFactory().create_browser_object(browser_type=Browser.Types.EDGE)
            self.browser.set_downloads_dir(os.getcwd())

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)
    
    def __open_browser_with_user(self, username, password):
        self.browser = BrowserFactory().create_browser_object(browser_type=Browser.Types.EDGE)
        self.browser.set_downloads_dir(os.getcwd())
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=username, password=password)
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_network()

        # Click tile topologies in adminpage
        self.networkpage = NetworkPage(self.admin_console)
        self.backupnetworks = BackupNetworks(self.admin_console)
        self.networkpage.click_dips()

    @test_step
    def verify_mspadmin_access(self):
        """Open browser and login as msp admin other than 'admin' and validate that he is able to access"""
        try:
            self.__open_browser_with_user(self.inputJSONnode['commcell']['commcellUsername'], 
                                          self.inputJSONnode['commcell']['commcellPassword'])
            self.browser.close()
            self.log.info("MSP ADMIN is able to access the page correctly")
        except Exception as e:
            raise Exception(e)
        
    def verify_tenant_admin_access(self):
        """Verify that tenant admin is not able to access the page"""
        try:
            self.__open_browser_with_user(self.tcinputs.get("tenantAdminUsername"), self.tcinputs.get("tenantAdminPassword"))
        except Exception as e:
            self.log.info("Tenant Admin is unable to access backup networks")
            self.browser.close()
            return

        raise Exception("Tenant admin is able to access the backupnetworks page")

    def verify_tenant_user_access(self):
        """Verify that tenant user is not able to access the page"""
        try:
            self.__open_browser_with_user(self.tcinputs.get("tenantUsername"), self.tcinputs.get("tenantPassword"))
        except Exception as e:
            self.log.info("Passed: Tenant User is unable to access backupnetworks page")
            self.browser.close()
            return
    
        raise Exception("Tenant User is able to view backup networks page")
    
    def verify_commcell_user_access(self):
        """Verify that commcell user has no access to the page"""
        try:
            self.__open_browser_with_user(self.tcinputs.get("commcellUsername"), self.tcinputs.get("commcellPassword"))
        except Exception as e:
            self.browser.close()
            self.log.info("Passed: Commcell user has no access to the backupnetworks page")
            return

        raise Exception("Commcell user is able to access backupnetworks page")

    def run(self):
        self.init_tc()
        self.verify_mspadmin_access()
        self.verify_tenant_user_access()
        self.verify_tenant_admin_access()
        self.verify_commcell_user_access()