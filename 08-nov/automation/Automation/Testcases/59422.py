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

    verify_operations() -- Verifies if tenant admin can perform operations on company servers

    verify_subclient_operations() -- Verifies if tenant admin can backup subclient

    verify_subclient_modification() -- Verifies if tenant admin can create and modify subclient

    tear_down()     --  tear down function of this test case

"""

import time
import os

from cvpysdk.commcell import Commcell

from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.config = get_config()
        self.name = "MSP cases for File Servers page"
        self.tcinputs = {
            "BackupsetName": "",
            "SubclientName": "",
            "username": ""
        }

    def setup(self):
        self.log.info("Initializing pre-requisites")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs['username'],
                                 self.config.MSPCompany.tenant_password)
        self.navigator = self.admin_console.navigator
        self.file_servers = FileServers(self.admin_console)
        self.fssubclient = FsSubclient(self.admin_console)
        self.__subclient = FsSubclientDetails(self.admin_console)
        self.commcell = Commcell(webconsole_hostname=self.commcell.webconsole_hostname,
                                 commcell_username=self.tcinputs['username'],
                                 commcell_password=self.config.MSPCompany.tenant_password)

        all_clients = list(self.commcell.clients.all_clients.keys())
        self.client = None
        for client in all_clients:
            if self.commcell.clients.get(client).is_ready:
                self.client = self.commcell.clients.get(client)
                break

    @test_step
    def verify_operations(self):
        """Verifies if tenant admin can perform operations on company servers"""
        self.navigator.navigate_to_file_servers()
        self.log.info('Checking for readiness of client')
        self.file_servers.run_check_readiness(client_name=self.client.name)
        self.navigator.navigate_to_file_servers()
        self.log.info('Performing restore from servers page')
        self.file_servers.restore_subclient(client_name=self.client.name,
                                            subclient_name=self.tcinputs['SubclientName'])

    @test_step
    def verify_subclient_operations(self):
        """Verifies if tenant admin can backup subclient"""
        self.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.client.name)
        self.log.info('Performing backup from subclient details page')
        self.file_servers.backup_subclient('default', 'full')

    @test_step
    def verify_subclient_modification(self):
        """Verifies if tenant admin can create and modify subclient"""
        self.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.client.name)
        self.log.info('Creating a subclient')
        self.fssubclient.add_fs_subclient(self.tcinputs['BackupsetName'],
                                          'Test_59422',
                                          self.config.MSPCompany.company.plans[0],
                                          define_own_content=True,
                                          backup_data=self.config.MSPCompany.backup_loc)
        self.fssubclient.access_subclient(self.tcinputs['BackupsetName'], 'Test_59422')
        self.log.info('Changing backup content for created subclient')
        self.__subclient.edit_content(browse_and_select_data=True, backup_data=self.config.MSPCompany.backup_loc,
                                      del_content=self.config.MSPCompany.backup_loc)
        self.log.info('Deleting created subclient')
        self.__subclient.delete_subclient()

    def run(self):
        """Run function of this test case"""
        try:
            self.verify_operations()

            self.verify_subclient_operations()

            self.verify_subclient_modification()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
