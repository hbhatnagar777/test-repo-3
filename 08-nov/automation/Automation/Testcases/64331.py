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
    """Command Center - Network Options - Verify the Override Tunnel Port and Keep Alive Interval at ServerGroup"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center - Network Options - Verify the Override Tunnel Port and Keep Alive Interval at ServerGroup"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.client1 = None
        self.client2 = None
        self.servergroup = None
        self.server_group_name = "TESTCASE_CG_64331"
        self.servergroupobject = None
        self.clients = [self.client1, self.client2]
    
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
        #self._network = NetworkHelper(self)

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
        """Validate the network settings"""
        # To DO - PRe validate the settings with default values
        settings = self.servergroup.get_network_settings()

        self.servergroup.apply_network_settings({'tunnel_port': {'value':"9403"}})

        # verify the settings from network helper
        self._network.validate_tunnel_port([{'clientName': self.client1}], "9403")
        self._network.validate_tunnel_port([{'clientName': self.client2}], "9403")
        self._network.validate_settings_display(self.servergroup.get_network_settings(), "Tunnel port","9403")
    
    @test_step
    def validate_step2(self):
        """Validate the removal of a tunnel port and addition of keepalive"""
        client1_port = self.commcell.clients.get(self.client1).network.tunnel_connection_port
        client2_port = self.commcell.clients.get(self.client2).network.tunnel_connection_port

        self.servergroup.apply_network_settings({'tunnel_port': {"value":"", "delete": True}, "keepalive_interval": {"value":"150"}})

        self._network.validate_tunnel_port([{'clientName': self.client1}], client1_port)

        self._network.validate_settings_display(self.servergroup.get_network_settings(), "Tunnel port", 8403)
        self._network.validate_tunnel_port([{'clientName': self.client2}], client2_port)
        
        
        self._network.validate_settings_display(self.servergroup.get_network_settings(), "Keep-alive interval in seconds","150")
        self._network.validate_keep_alive([{'clientName': self.client1}], "150")

        self._network.validate_keep_alive([{'clientName': self.client2}], "150")
    
    @test_step
    def validate_step3(self):
        """Validate the keepalive setting of a group reverted back"""
        self.servergroup.apply_network_settings({'keepalive_interval': {"value": "180"}})
        self._network.validate_settings_display(self.servergroup.get_network_settings(), "Keep-alive interval in seconds","180")
        self._network.validate_keep_alive([{'clientName': self.client1}], "180")
        self._network.validate_keep_alive([{'clientName': self.client2}], "180")
    
    @test_step
    def run(self):
        """Run testcase"""
        try:
            self.validate_step1()
            self.validate_step2()
            self.validate_step3()
        except Exception as e:
            handle_testcase_exception(self, e)
        finally:
            self.teardown()

    def teardown(self):
        """Teardown function of this test case"""
        self.browser.close()
        self.browser = None
        self._network.cleanup_network()
        self._network.entities.cleanup()
        if self.commcell.client_groups.has_clientgroup(self.server_group_name):
            self.commcell.client_groups.delete(self.server_group_name)
