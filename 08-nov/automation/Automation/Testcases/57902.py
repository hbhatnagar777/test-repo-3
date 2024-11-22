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
    __init__()                   --  initialize TestCase class

    install_file_server_client() --  Install file server client method for test case

    wait_for_job_completion()   --  Waits for completion of job and gets the object
                                    once job completes

    run()                       --  run function of this test case

Input Example:

    "testCases":
            {
                "57902":
                        {
                            "OSType":"Unix",
                            "AgentName": "File System",
                            "NewClientName": "cc-automation",
                            "NewBackupsetName":"Test-automation",
                            "SubclientName":"Test1",
                            "PlanName":"Test-Auto",
                            "TestPath": "/var/log/commvault",
                        }
            }

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient, FsAgent
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.AdminConsole.Components.panel import Backup
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from time import sleep


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File Server installation from command center"
        self.tcinputs = {
            "OSType": None,
            "AgentName": None,
            "NewClientName": None,
            "NewBackupsetName": None,
            "SubclientName": None,
            "PlanName": None,
            "TestPath": None
        }

    def init_tc(self):
        """ Initial configuration for the test case. """

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.driver = self.browser.driver
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.file_servers = FileServers(self.admin_console)
            self.fs_agent_obj = FsAgent(self.admin_console)
            self.fssubclient_obj = FsSubclient(self.admin_console)
            self.fssubclient_details_obj = FsSubclientDetails(self.admin_console)
            self.backup_type = Backup(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def wait_for_job_completion(self, job_id):
        job_obj = self.commcell.job_controller.get(job_id)
        job_status = job_obj.wait_for_completion()
        self.log.info(job_status)
        if job_status == 'False':
            raise CVTestStepFailure("Job %s didn't complete successfully", job_id)

    @test_step
    def install_file_server_client(self):
        """ Install new file server client """

        if self.commcell.clients.has_client(self.tcinputs['NewClientName']):
            self.log.info("Client already exists. Retiring client")
            self.file_servers.retire_server(self.tcinputs['NewClientName'])
            sleep(400)
            self.log.info("Client Retired")
            self.commcell.clients.refresh()
            self.admin_console.refresh_page()
        if self.commcell.clients.has_client(self.tcinputs['NewClientName']):
            self.log.info("Client already exists. Deleting client")
            self.file_servers.delete_client(self.tcinputs['NewClientName'])
            sleep(400)
            self.log.info("Client Deleted")
            self.commcell.clients.refresh()
            self.admin_console.refresh_page()
        job_id = self.file_servers.install_windows_unix_client(self.tcinputs['NewClientName'],
                                                      self.tcinputs['ClientUsername'], self.tcinputs['ClientPassword'],
                                                      os_type=self.tcinputs['OSType'])
        self.wait_for_job_completion(job_id)

    @test_step
    def create_user_defined_backupset(self):
        """ Create a new backupset """
        if self.fssubclient_obj.is_backupset_exists(self,self.tcinputs['NewBackupsetName']) is False :
            self.fs_agent_obj.add_backupset(self.tcinputs['NewBackupsetName'],
                                            self.tcinputs['PlanName'],
                                            file_system=self.tcinputs['OSType'])

    @test_step
    def create_user_defined_subclient(self):
        """ Create a new subclient """
        testpath = self.tcinputs['TestPath']
        if  self.fssubclient_obj.is_subclient_exists(self.tcinputs['SubclientName']) is False:
            self.fssubclient_obj.add_fs_subclient(self.tcinputs['NewBackupsetName'],
                                                self.tcinputs['SubclientName'],
                                                self.tcinputs['PlanName'], define_own_content=True,
                                                browse_and_select_data=False, backup_data=[testpath],
                                                file_system='Unix', remove_plan_content=True)

    @test_step
    def navigate_to_user_defined_subclient(self):
        """ Navigate to subclient page """
        self.admin_console.refresh_page()
        self.fssubclient_obj.access_subclient(self.tcinputs['NewBackupsetName'],
                                              self.tcinputs['SubclientName'])

    @test_step
    def backup_job(self, backup_type):
        """ Run a filesystem backup job """
        jobid = self.fssubclient_details_obj.backup(backup_type, drop_down=True)
        self.wait_for_job_completion(jobid)

    @test_step
    def delete_user_defined_subclient(self):
        """ Delete the specified subclient """
        self.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.display_name)
        self.fssubclient_obj.delete_subclient(self.tcinputs['NewBackupsetName'],
                                              self.tcinputs['SubclientName'])

    @test_step
    def delete_user_defined_backupset(self):
        """ Delete the specified backpset """
        if self.tcinputs["NewBackupsetName"] == "defaultBackupSet":
            self.log.info("Default Backupset provided. Skipping delete")
        self.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.display_name)
        self.fssubclient_obj.delete_backup_set(self.tcinputs['NewBackupsetName'])

    def run(self):
        try:
            self.init_tc()
            self.navigator.navigate_to_file_servers()
            self.install_file_server_client()
            sleep(30)
            self.commcell.clients.refresh()
            self.client_obj = self.commcell.clients.get(self.tcinputs['NewClientName'])
            self.display_name = self.client_obj.display_name
            self.admin_console.refresh_page()
            self.log.info(self.client_obj)
            self.log.info(self.display_name)
            self.admin_console.refresh_page()
            self.file_servers.access_server(self.display_name)
            self.create_user_defined_backupset()
            self.create_user_defined_subclient()
            self.admin_console.refresh_page()
            self.navigate_to_user_defined_subclient()
            self.backup_job(Backup.BackupType.FULL)
            self.delete_user_defined_subclient()
            self.delete_user_defined_backupset()
            self.navigator.navigate_to_file_servers()
            self.file_servers.retire_server(self.display_name)
            #TODO check is software is unistalled or not on client
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
