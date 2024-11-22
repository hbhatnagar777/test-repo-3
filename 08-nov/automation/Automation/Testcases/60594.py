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

    delete_index_server()                        --  Delete an Index server

    run()                                        --  run function of this test case
"""

import time
from AutomationUtils.cvtestcase import CVTestCase
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
        self.name = "Create an index Server with already existing name & verify error message"
        self.tcinputs = {
            "IndexServerNodeNames": None
        }
        # Testcase Constants
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.index_directory = []
        self.test_case_error = None
        self.index_server_name = None
        self.index_servers_obj = None

    def init_tc(self):
        """ Initial configuration for the test case """
        try:
            self.index_server_name = f'{self.id}_IS'
            self.configure_machine_inputs(self.tcinputs['IndexServerNodeNames'])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.index_servers_obj = IndexServer(self.admin_console)

        except Exception:
            raise Exception("Testcase initialization failed")

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
            index_directory=[self.index_directory[0]],
            index_server_node_names=[self.tcinputs['IndexServerNodeNames'][0]],
            solutions=[FILE_STORAGE_OPTIMIZATION])

        try:
            self.index_servers_obj.create_index_server(
                index_server_name=self.index_server_name,
                index_directory=[self.index_directory[1]],
                index_server_node_names=[self.tcinputs['IndexServerNodeNames'][1]],
                solutions=[FILE_STORAGE_OPTIMIZATION])
        except Exception as err:
            if f"Server with same name already exists" not in str(err):
                self.log.info('Testcase Failed')
                self.test_case_error = err
            else:
                self.log.info('Testcase Passed')

    @test_step
    def delete_index_server(self):
        """
            delete an index server and remove index directories
        """
        self.navigator.navigate_to_index_servers()
        self.index_servers_obj.delete_index_server(self.index_server_name)

    def run(self):
        try:
            self.init_tc()
            self.create_index_server()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
