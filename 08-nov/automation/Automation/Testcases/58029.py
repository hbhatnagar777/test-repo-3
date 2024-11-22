# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  Initial configuration for the test case

    verify_client_existence         -- Check if IBMi client entity present

    navigate_to_file_server_tab     -- Navigates to file server tab of Protect--> File Servers

    navigate_to_client_subclient_tab-- Navigates to the subclient page for IBMi clients

    create_ibmi_client()            --  Create new IBMi client machine.

    retire()            --  Retire the IBMi client

    create_user_defined_backupset()	--  Create a new backupset

    verify_auto_created_subclients()--  Verify Auto-Created subclients of a backupSet

    delete_user_defined_backupset()	--  Delete the specified backupset

    run()                           --  run function of this test case

Input Example:

    "testCases":
            {
                "58029":
                        {
                            "PlanName":"Test-Auto",
                            "ClientName": "Existing-client",
                            "AccessNode": ["proxy1", "proxy2"],
                            "HostName": "IBMi-host-name",
                            "TestPath": "/QSYS.LIB"
                        }
            }

"""

import random
import string
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validate IBMi client creation from command center"
        self.browser = None
        self.admin_console = None
        self.client_obj = None
        self.display_name = None
        self.navigator = None
        self.new_client_name = None
        self.helper = None
        self.browser = None
        self.hostname = None
        self.username = None
        self.password = None
        self.RfsSubclient = None
        self.backupset_name = None
        self.Rfile_servers = None
        self.tcinputs = {
            "AgentName": None,
            "ClientName": None,
            "PlanName": None,
            "TestPath": None,
            "HostName": None
        }

    def setup(self):
        """ Initial configuration for the test case. """

        try:
            # Initialize test case inputs
            self.log.info("***TESTCASE: %s***", self.name)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.Rfile_servers = FileServers(self.admin_console)
            self.RfsSubclient = Subclient(self.admin_console)
            self.display_name = self.commcell.clients.get(self.tcinputs['ClientName']).display_name
            self.backupset_name = "CCAUTOMATION"
            self.new_client_name = "IBMi-CCAUTOMATION"

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def verify_client_existence(self):
        """Check if IBMi client entity present"""
        self.Rfile_servers.navigate_to_file_server_tab()
        return self.Rfile_servers.is_client_exists(server_name=self.new_client_name)

    @test_step
    def navigate_to_client_subclient_tab(self):
        """Navigates to the subclient page for IBMi clients"""
        self.Rfile_servers.navigate_to_file_server_tab()
        self.Rfile_servers.access_server(self.display_name)
        self.admin_console.access_tab("Subclients")
        self.admin_console.wait_for_completion()

    @test_step
    def create_ibmi_client(self):
        """ Create new IBMi client """
        self.Rfile_servers.navigate_to_file_server_tab()
        notification = self.Rfile_servers.add_ibmi_client(server_name=self.new_client_name,
                                                          file_server_host_name=self.new_client_name,
                                                          username=self.tcinputs['UserName'],
                                                          password=self.generate_strong_password(),
                                                          access_node=self.tcinputs['AccessNode'],
                                                          data_path="/var/commvault",
                                                          port=0,
                                                          plan=self.tcinputs['PlanName'],
                                                          subsystem_description="QSYS/QCTL",
                                                          job_queue="QSYS/QCTL",
                                                          create_jobq=True,
                                                          job_priority=6,
                                                          run_priority=59
                                                          )
        if 'created successfully' not in notification:
            raise CVTestStepFailure(notification)
        self.admin_console.refresh_page()

    @test_step
    def retire(self):
        """ Retire the IBMi client"""
        self.Rfile_servers.navigate_to_file_server_tab()
        notification = self.Rfile_servers.retire_ibmi_client(server_name=self.new_client_name)
        if 'retired successfully' not in notification:
            raise CVTestStepFailure(notification)
        # An email has been sent to the administrator
        self.admin_console.refresh_page()

    @test_step
    def create_user_defined_backupset(self, backupset_name):
        """ Create a new backupset
        Args:
            backupset_name (str): name of the BackupSet
        """
        self.navigate_to_client_subclient_tab()
        if not self.RfsSubclient.is_backupset_exists(backupset_name=backupset_name):
            self.RfsSubclient.add_ibmi_backupset(backupset_name=backupset_name,
                                                 plan_name=self.tcinputs['PlanName'])
            self.admin_console.refresh_page()

    @test_step
    def verify_auto_created_subclients(self, backupset_name):
        """ Verify Auto-Created subclients of a backupSet
        Args:
            backupset_name (str): name of the BackupSet
        """
        self.navigate_to_client_subclient_tab()
        status = self.RfsSubclient.is_ibmi_subclient_exists(backupset_name=backupset_name,
                                                            subclient_name='ALL')
        if not status:
            raise CVTestStepFailure("expected subclients not found "
                                    "under the backupset:{0}".format(backupset_name))

    @test_step
    def delete_user_defined_backupset(self):
        """ Delete the specified backupset if exists """
        self.navigate_to_client_subclient_tab()
        status = self.RfsSubclient.is_backupset_exists(backupset_name=self.backupset_name)
        if status:
            self.log.info("BackupSet:{0} exists under the IBMi "
                          "client. Deleting it...".format(self.backupset_name))
            self.RfsSubclient.delete_backup_set(self.backupset_name)

    @test_step
    def generate_strong_password(self):
        """ generate random and strong password """
        password = ''.join(random.choice(string.ascii_uppercase +
                                         string.digits +
                                         string.ascii_lowercase +
                                         string.punctuation) for _ in range(10))
        return password

    def run(self):
        try:
            if self.verify_client_existence():
                self.retire()
            self.create_ibmi_client()
            self.commcell.clients.refresh()
            self.client_obj = self.commcell.clients.get(self.new_client_name)
            self.display_name = self.client_obj.display_name
            self.admin_console.refresh_page()
            self.create_user_defined_backupset(backupset_name=self.backupset_name)
            self.verify_auto_created_subclients(backupset_name="defaultBackupSet")
            self.verify_auto_created_subclients(backupset_name=self.backupset_name)
            self.delete_user_defined_backupset()
            self.retire()

        except Exception as exception:
            handle_testcase_exception(self, exception)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
