# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main module for executing the test case.

This module defines the TestCase class, which handles the execution of a test case
validating command center actions like viewing and pushing network configurations
on Servers and Server Groups pages.

TestCase:
    __init__()      --  Initializes the TestCase class.
    setup()         --  Sets up the necessary components for the test case.
    validate_test_step1()  --  Validates the network summary of Command Center.
    validate_test_step2()  --  Verifies the push network configuration from Command Center.
    validate_test_step3()  --  Adds server groups and verifies push network configurations.
    run()           --  Executes the test case.
    cleanup()       --  Cleans up after the test case execution.

Inputs:
    SourceClient1: A client computer.
    SourceClient2: Another client computer.
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Server.Network.networkhelper import NetworkHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.AdminConsolePages.server_groups import *
from Web.AdminConsole.AdminConsolePages.Servers import Servers


class TestCase(CVTestCase):
    """Class for Command Center - Network Options test case.

    This test case verifies the viewing and pushing of network configurations
    on Command Center's Servers and Server Groups pages.
    """

    test_step = TestStep()

    def __init__(self):
        """Initializes the TestCase class object."""
        super(TestCase, self).__init__()
        self.name = "Command Center - Network Options - Verify the view and push network configurations"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.servers = None
        self.test_servergroupname = "TEST_GROUP1_64330"
        self.test_servergroupname2 = "TEST_GROUP2_64330"
        self.server_input1 = None
        self.server_input2 = None
        self.server_object1 = None
        self.server_object2 = None
        self.network_helper = None
        self.topology = "TEST_ONW_64330"

    def setup(self):
        """Sets up the necessary components for the test case."""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                 password=self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_servers()
        self.servers = Servers(self.admin_console)
        self.server_input1 = self.tcinputs['SourceClient1']
        self.server_input2 = self.tcinputs['SourceClient2']
        self.server_object1 = self.commcell.clients.get(self.server_input1)
        self.server_object2 = self.commcell.clients.get(self.server_input2)
        self.network_helper = NetworkHelper(self)
        self.cleanup()

    def validate_test_step1(self):
        """Validates the network summary of Command Center.
        Compares the network summary from the Command Center with the summary from the client object.
        """
        import re

        def clean_string(s):
            # Remove all whitespace characters (space, tab, newline)
            return re.sub(r'\s+', '', s)

        summary = self.servers.action_view_network_summary(self.commcell.commserv_name)
        summary_from_client_object = self.commcell.clients.get(self.commcell.commserv_name).get_network_summary()

        cleaned_summary = clean_string(summary)
        cleaned_summary_from_client_object = clean_string(summary_from_client_object)

        if cleaned_summary != cleaned_summary_from_client_object:
            print("Summaries do not match. Differences:")
            print("UI Summary:", summary)
            print("Client Object Summary:", summary_from_client_object)
            assert False, "Summary from client object is not the same as summary from command center"
        else:
            print("Summaries match successfully")

    def __validate_workqueue_token(self, client_id):
        """Validates the work queue token for a given client ID.

        Args:
            client_id (int): The client ID to validate the work queue token for.
        """
        self.csdb.execute(
            "SELECT clientId, workToken from APP_WorkQueueRequest where workToken = 5 AND clientId = {}".format(
                client_id))
        result = self.csdb.fetch_all_rows()
        self.log.info("Result : {}".format(result))
        try:
            assert result[0][0] == client_id, "Client ID is not same as expected"
            assert result[0][1] == '5', "Work Token is not same as expected"
        except Exception as e:
            self.log.error("Exception in validate_workqueue_token : {}".format(e))
            raise CVTestStepFailure("Work Queue Token is not same as expected")

    def validate_test_step2(self):
        """Verifies the push network configuration from Command Center."""
        try:
            self.servers.action_push_network_configuration(self.server_input1)
            self.__validate_workqueue_token(self.server_object1.client_id)
        except Exception as e:
            self.log.error("Exception in validate_test_step2 : {}".format(e))
            raise CVTestStepFailure("Push network configuration failed ")

    def validate_test_step3(self):
        """Adds server groups and verifies push network configurations.

        Adds server groups and verifies the push network configuration of the same.
        """
        try:
            self.commcell.client_groups.add(self.test_servergroupname, [self.server_input1])
            self.commcell.client_groups.add(self.test_servergroupname2, [self.server_input2])
            self.navigator.navigate_to_server_groups()
            server_group = ServerGroups(self.admin_console)
            server_group.action_push_network_configuration(self.test_servergroupname)
            self.__validate_workqueue_token(self.server_object1.client_id)

            server_group.action_push_network_configuration(self.test_servergroupname2)
            self.__validate_workqueue_token(self.server_object2.client_id)

            # Push configuration for one way topology
            self.network_helper.one_way_topology(self.test_servergroupname, self.test_servergroupname2, self.topology)
            server_group.action_push_network_configuration(self.test_servergroupname)
            server_group.action_push_network_configuration(self.test_servergroupname2)
            #self.network_helper.validate_fwconfig_file(2, self.server_input1, self.server_input2)
        except Exception as e:
            raise CVTestStepFailure("Exception in validate_test_step3 : {}".format(e))

    def run(self):
        """Executes the test case."""
        try:
            self.validate_test_step1()
            self.validate_test_step2()
            self.validate_test_step3()
        except Exception as e:
            self.log.error("Exception in test case : {}".format(e))
            raise e
        finally:
            self.cleanup()
            self.browser.close()

    def cleanup(self):
        """Cleans up after the test case execution."""
        try:
            self.commcell.client_groups.delete(self.test_servergroupname)
            self.commcell.client_groups.delete(self.test_servergroupname2)
            self.network_helper.delete_topology(self.topology)
        except Exception as e:
            self.log.error("Exception in cleanup : {}".format(e))
