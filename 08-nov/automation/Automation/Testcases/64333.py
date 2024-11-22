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

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Server.Network.networkhelper import NetworkHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.AdminConsolePages.server_group_details import *
from Web.AdminConsole.AdminConsolePages.server_groups import *
import os

class TestCase(CVTestCase):
    """Command Center - Network options - Enable network gateway and force incoming ssl"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center - Network options - Enable network gateway and force incoming ssl"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.client1 = None
        self.client2 = None
        self.servergroup = None
        self.server_group_name = "TESTCASE_CG_64333"
        self.servergroupobject = None
        self.clients = [self.client1, self.client2]
        self.force_ssl_label = "Force SSL encryption in incoming tunnels"
        self.enable_gateway_label = "Enable network gateway"
    
    def open_servergroup_configuration(self):
        """Open the server group configuration page"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.set_downloads_dir(os.getcwd())
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                 password=self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_server_groups()
        self.servergroup = ServerGroupConfiguration(self.admin_console)
        
        self.servergroup.access_configuration_tab(self.server_group_name)

    def setup(self):
        """Setup function of this test case"""
        # Add clients from tcinputs
        self._network = NetworkHelper(self)
        self.client1 = self.tcinputs.get('client1')
        self.client2 = self.tcinputs.get('client2')

        # Create the server group with the pre defined servergroup name
        clientgrps = self._network.entities.create_client_groups([self.server_group_name])
        clientgrps[self.server_group_name]["object"].add_clients([self.client1, self.client2])
        self.open_servergroup_configuration()
    
    @test_step
    def validate_step1(self):
        """STEP1 Validate the network gateway option in command center"""
        # Apply network settings
        settings = {
            'enable_gateway': {'value': True, 'delete': False}
        }
        self.servergroup.apply_network_settings(settings)

        self._network.validate_other_settings(self.client1, "proxy", "1")
        self._network.validate_other_settings(self.client2, "proxy", "1")

    @test_step
    def validate_step2(self):
        """STEP2 Validate the force incoming ssl option in command center"""        
        # Apply network settings
        settings = {
            'force_ssl': {'value': True, 'delete': False}
        }
        self.servergroup.apply_network_settings(settings)

        self._network.validate_other_settings(self.client1, "force_incoming_https", "1")
        self._network.validate_other_settings(self.client2, "force_incoming_https", "1")

        added_setting = self.servergroup.get_network_settings()
        self._network.validate_settings_display(added_setting, self.force_ssl_label, "Yes")
        self._network.validate_settings_display(added_setting, self.enable_gateway_label, "Yes")

    @test_step
    def validate_step3(self):
        """STEP3 Remove both settings and validate"""        
        # Apply network settings to remove configurations
        settings = {
            'enable_gateway': {'value': False, 'delete': True},
            'force_ssl': {'value': False, 'delete': True}
        }
        self.servergroup.apply_network_settings(settings)

        self._network.validate_other_settings(self.client1, "proxy", "0")
        self._network.validate_other_settings(self.client2, "proxy", "0")
        self._network.validate_other_settings(self.client1, "force_incoming_https", "0")
        self._network.validate_other_settings(self.client2, "force_incoming_https", "0")

    def run(self):
        """Main function for test case execution"""
        try:
            self.validate_step1()
            self.validate_step2()
            self.validate_step3()
        except Exception as excp:
            handle_testcase_exception(self, excp)
        finally:
            self.browser.close()
            self.browser = None
            self._network.cleanup_network()
            self._network.entities.cleanup()
            if self.commcell.client_groups.has_clientgroup(self.server_group_name):
                self.commcell.client_groups.delete(self.server_group_name)