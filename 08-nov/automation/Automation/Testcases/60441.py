# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                                   --  initialize TestCase class

    init_tc()                                    --  Initial configuration for the testcase

    configure_machine_inputs()                   --  Configure Inputs for machine according to machines configuration

    create_index_server()                        --  Create an Index Server

    validate_index_server_overview()             --  Validates Index Server Overview

    delete_index_server()                        --  Delete an Index Server

    run()                                        --  run function of this test case
"""
import time
from random import randint
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.AdminConsole.AdminConsolePages.Index_Server import IndexServer
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.utils.constants import FILE_STORAGE_OPTIMIZATION


class TestCase(CVTestCase):
    """Class for executing this Testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Overview an index Server and match attributes with the user input"
        self.tcinputs = {
            "IndexServerNodeNames": None,
            "Roles": None
        }
        # Testcase Constants
        self.index_server_name = None
        self.index_directory = []
        self.ports = []
        self.memory = []
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.machine_obj = None
        self.index_servers_obj = None

    def init_tc(self):
        """ Initial configuration for the test case"""
        try:
            self.index_server_name = f'{self.id}_IS'
            if isinstance(self.tcinputs['IndexServerNodeNames'], str):
                self.tcinputs['IndexServerNodeNames'] = self.tcinputs['IndexServerNodeNames'].split(",")
            if isinstance(self.tcinputs['Roles'], str):
                self.tcinputs['Roles'] = self.tcinputs['Roles'].split(",")
            self.configure_machine_inputs(self.tcinputs['IndexServerNodeNames'])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.index_servers_obj = IndexServer(self.admin_console)

        except Exception:
            raise Exception("init tc failed")

    def configure_machine_inputs(self, node_names):
        """
        Configure Inputs for machine according to machines configuration.

        Args:
             node_names (list):  name of the machine/node.
        """
        for node in node_names:
            self.log.info(f'Forming index directory on the node {node}')
            self.index_directory.append(IndexServerHelper.get_new_index_directory(
                self.commcell, node, int(time.time())))
            self.machine_obj = Machine(node, self.commcell)
            total_memory = int(self.machine_obj.get_hardware_info()['RAM'][: -2]) * 1024
            self.memory.append(randint(4097, min(total_memory, 32768)))
            self.ports.append(randint(20000, 20010))

    @test_step
    def create_index_server(self):
        """
            create an index server
        """

        self.navigator.navigate_to_index_servers()
        self.log.info('Deleting Index Server if already exists')
        index_server_exist = self.index_servers_obj.is_index_server_exists(self.index_server_name)
        if index_server_exist:
            self.delete_index_server()
        self.index_servers_obj.create_index_server(
            index_server_name=self.index_server_name,
            index_directory=self.index_directory,
            port_number=self.ports,
            memory=self.memory,
            solutions=[FILE_STORAGE_OPTIMIZATION],
            index_server_roles=self.tcinputs['Roles'],
            index_server_node_names=self.tcinputs['IndexServerNodeNames'])

    @test_step
    def validate_index_server_overview(self):
        """
        Validates Index Server Overview
        """
        self.navigator.navigate_to_index_servers()
        self.index_servers_obj.validate_index_server_overview(
            self.index_server_name, self.tcinputs['IndexServerNodeNames'],
            self.index_directory, self.ports, self.tcinputs['Roles'], self.memory)

    @test_step
    def delete_index_server(self):
        """
            Delete an Index Server
        """
        self.navigator.navigate_to_index_servers()
        self.index_servers_obj.delete_index_server(index_server_name=self.index_server_name)
        index = 0
        for node in self.tcinputs['IndexServerNodeNames']:
            self.machine_obj = Machine(node, self.commcell)
            self.log.info(f'Removing Index directory for node {node}')
            self.machine_obj.remove_directory(self.index_directory[index])
            index += 1

    def run(self):
        try:
            self.init_tc()
            self.create_index_server()
            self.validate_index_server_overview()
            self.delete_index_server()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
