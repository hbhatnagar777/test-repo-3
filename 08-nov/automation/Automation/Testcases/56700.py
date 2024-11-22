# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""

Test case to enable Ransomware Protection on existing Storage Pool of Hyperscale setup
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Basic idea of the test case :
To have Admin Console basic health check for hyperscale setup.

prerequisites:
1. HyperScale setup

input json file arguments required:

"56700": {
          "username": "",
          "password": "",
          "ClientName": "",
          "Storage_Pool_Name": "",
          "ControlNodes": {
            "MA1": "",
            "MA2": "",
            "MA3": ""
          }
        }
"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain


class TestCase(CVTestCase):
    """ Hyperscale Testcase for health check """

    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Admin Console - Basic Disk Configuration Case"
        self.browser = None
        self.admin_console = None
        self.mas = []
        self.storagepool_name = None
        self.control_nodes = None
        self.ma1 = None
        self.ma2 = None
        self.ma3 = None
        self.mas = []
        self.username = None
        self.password = None
        self.driver = None
        self.storage_helper = None
        self.tcinputs = {
            "Storage_Pool_Name": None,
            "username": None,
            "password": None,
            "ControlNodes": {
                "MA1": None,
                "MA2": None,
                "MA3": None,
            },
        }

    def init_tc(self):
        """Initial configuration for the test case"""

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.driver = self.admin_console.driver
            self.admin_console.login(self.tcinputs.get("username"),
                                     self.tcinputs.get("password"))
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def setup(self):
        """Initializes test case variables"""

        self.init_tc()
        self.storage_helper = StorageMain(self.admin_console)
        self.username = self.tcinputs.get("username")
        self.password = self.tcinputs.get("password")
        self.control_nodes = self.tcinputs.get("ControlNodes")
        self.ma1 = self.control_nodes.get('MA1')
        self.ma2 = self.control_nodes.get('MA2')
        self.ma3 = self.control_nodes.get('MA3')
        self.mas.extend((self.ma1, self.ma2, self.ma3))
        self.storagepool_name = self.tcinputs.get("Storage_Pool_Name")

    def run(self):
        """Main function for test case execution"""
        try:
            # creating storagepool
            self.storage_helper.hyperscale_add_storagepool(self.storagepool_name, self.mas)
            time.sleep(300)
            self.driver.refresh()

            # checking storagepool status
            if self.storage_helper.hyperscale_storagepool_health_status(self.storagepool_name)\
                    == 'Online':
                self.log.info(f"{self.storagepool_name} Status is online")
            else:
                raise CVTestStepFailure(f"{self.storagepool_name} Status is not online")

            # getting library details
            library_details = self.storage_helper.hyperscale_library_info(self.storagepool_name)
            self.log.info("Library Details : ")
            for item in library_details:
                self.log.info(f"{item} : {library_details[item]}")

            # checking nodes health status
            nodes_list = self.storage_helper.hyperscale_list_nodes(self.storagepool_name)
            for node in self.mas:
                if node not in nodes_list:
                    raise CVTestStepFailure(f"{node} is not present in Admin Console")
                if self.storage_helper.hyperscale_node_health_status(self.storagepool_name, node)\
                        == 'Online':
                    self.log.info(f"{node} Status is online")
                else:
                    raise CVTestStepFailure(f"{node} Status is not online")

            # checking brick health status and brick info in each node
            for node in nodes_list:
                bricks_details = self.storage_helper.hyperscale_node_disks_info\
                    (self.storagepool_name, node)
                self.log.info("Bricks Details : ")
                for item in bricks_details:
                    self.log.info(f"{item} : {bricks_details[item]}")
                bricks_list = self.storage_helper.hyperscale_list_bricks\
                    (self.storagepool_name, node)
                for brick in bricks_list:
                    if self.storage_helper.hyperscale_brick_health_status\
                                (self.storagepool_name, node,brick) == 'Ready':
                        self.log.info(f"{brick} Status is ready")
                    else:
                        raise CVTestStepFailure(f"{brick} Status is not ready")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function for this test case"""
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)
