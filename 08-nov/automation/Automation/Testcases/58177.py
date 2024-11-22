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

Input Example:

     "testCases": {
            "58177": {
              "ClientName": "",
              "AgentName": "",
              "BackupsetName": "",
              "PlanName": "",
            }
     }
"""
import os
import time
import glob
from pathlib import Path
from Web.AdminConsole.Hub.constants import FileObjectTypes, HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """ Command center: Testcase to verify download files/folder
                        through command center.
    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Verify download files/folder from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.machine = None
        self.file_server = None
        self.fs_sub_client = None
        self.fs_helper = None
        self.os_name = None
        self.delimiter = None
        self.sub_client_name = "Test_58177"
        self.config = get_config()
        self.download_list = []
        self.download_path = ''
        self.modified_file = None
        self.content = []
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "BackupsetName": None,
            "PlanName": None
        }

    def navigate_to_client_page(self):
        """ Navigates to the input client page """
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.file_server.access_server(self.client.display_name)
        self.admin_console.wait_for_completion()
        self.admin_console.access_tab("Subclients")
        self.admin_console.wait_for_completion()

    def refresh(self):
        """ Refreshes the current page """
        self.log.info("%s Refreshes browser %s", "*" * 8, "*" * 8)
        time.sleep(60)
        self.admin_console.refresh_page()

    def wait_for_job_completion(self, job_id):
        """ Function to wait till job completes
                Args:
                    job_id (str): Entity which checks the job completion status
        """
        self.log.info("%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = self.commcell.job_controller.get(job_id)
        return job_obj.wait_for_completion()

    @test_step
    def define_content(self):
        """ Define the subclient content """
        if self.os_name == "Windows":
            self.delimiter = "\\"
            directory_path = self.client.job_results_directory + self.delimiter + 'Testing'
        else:
            self.delimiter = "/"
            directory_path = '/opt/58177'
        self.content.append(directory_path)
        self.fs_helper.generate_testdata(['.html', '.css', '.xls'], directory_path, 2)

    @test_step
    def add_sub_client(self):
        """ Creates new sub_client
                Raises:
                    Exception:
                        -- if fails to add entity
        """
        self.delete_sub_client()
        self.fs_sub_client.add_subclient(subclient_name=self.sub_client_name,
                                         backupset_name=self.tcinputs['BackupsetName'],
                                         plan_name=self.tcinputs['PlanName'],
                                         contentpaths=self.content,
                                         define_own_content=True,
                                         remove_plan_content=True
                                         )
        self.backupset.subclients.refresh()
        self.subclient = self.backupset.subclients.get(self.sub_client_name)

    def backup_job(self, backup_type):
        """ Function to run a backup job
            Args:
                backup_type (BackupType) : Type of backup (FULL, INCR, DIFFERENTIAL, SYN_FULL)
            Raises:
                Exception :
                 -- if fails to run the backup
        """
        self.log.info("%s Starts Backup job %s for subclient %s", backup_type,
                      "*" * 8, "*" * 8)
        job = self.fs_sub_client.backup_subclient(subclient_name=self.sub_client_name,
                                                  backupset_name=self.tcinputs['BackupsetName'],
                                                  backup_type=backup_type)
        self.wait_for_job_completion(job)
        return job

    def download_files(self, download_list):
        """download the selected files/folders"""

        self.fs_sub_client.download_selected_items(parent_dir=self.subclient.content[0],
                                                   backupset_name=self.tcinputs['BackupsetName'],
                                                   subclient_name=self.sub_client_name,
                                                   download_files=download_list)
        self.admin_console.wait_for_completion()

        #Adding sleep condition as download files may take long time
        time.sleep(300)

        self.navigate_to_client_page()

    def get_download_folder(self, file_type):
        """ Gets the download folder
                file_type(str): extension type of the file.
        """
        newest_file_type = max(
            glob.iglob(os.path.join(self.download_path, '*.{0}'.format(file_type))),
            key=os.path.getctime)
        return newest_file_type

    @test_step
    def check_download_single_file(self):
        """ Downloads single file """
        file_path = self.subclient.content[0] + self.delimiter + 'newfile.txt'
        file_content = 'New text file is created'
        self.machine.create_file(file_path, file_content)
        self.backup_job(Backup.BackupType.FULL)
        self.refresh()
        self.download_files(download_list=["newfile.txt"])
        path = self.get_download_folder('txt')
        self.fs_helper.validate_download_files(
            backup_files={os.path.basename(file_path): file_content},
            download_path=path)

    @test_step
    def check_download_multiple_file(self):
        """ Downloads multiple files"""
        file_path = self.subclient.content[0] + self.delimiter + 'newfile.doc'
        file_content = 'New doc file is created'
        self.machine.create_file(file_path, file_content)
        file_path1 = self.subclient.content[0] + self.delimiter + 'textfile.docx'
        self.machine.create_file(file_path1, file_content)
        self.backup_job(Backup.BackupType.INCR)
        self.refresh()
        self.download_files(download_list=["newfile.doc", "textfile.docx"])
        path = self.get_download_folder('zip')
        self.fs_helper.validate_download_files(
            backup_files={os.path.basename(file_path): file_content,
                          os.path.basename(file_path1): file_content},
            download_path=path)

    @test_step
    def check_download_folder_plus_file(self):
        """ Downloads folder + file """
        directory_path = self.subclient.content[0] + self.delimiter + 'Test'
        if self.machine.check_directory_exists(directory_path):
            self.machine.remove_directory(directory_path)
        self.machine.create_directory(directory_path)
        file_path = directory_path + self.delimiter + 'textfile.txt'
        file_content = 'New file is created'
        self.machine.create_file(file_path, file_content)
        file_path1 = directory_path + self.delimiter + 'textfile.doc'
        self.machine.create_file(file_path1, file_content)
        file_path2 = self.subclient.content[0] + self.delimiter + 'filetext.docx'
        file_content1 = 'New doc file is created'
        self.machine.create_file(file_path2, file_content1)
        self.backup_job(Backup.BackupType.INCR)
        self.refresh()
        self.download_files(download_list=["Test", "filetext.docx"])
        path = self.get_download_folder('zip')
        self.fs_helper.validate_download_files(
            backup_files={os.path.basename(file_path): file_content,
                          os.path.basename(file_path1): file_content,
                          os.path.basename(file_path2): file_content1},
            download_path=path)

    @test_step
    def delete_sub_client(self):
        """ Verifies whether sub_client exists or not and then deletes the subclient """
        if self.fs_sub_client.is_subclient_exists(subclient_name=self.sub_client_name,
                                                  backupset_name=self.tcinputs['BackupsetName']):
            self.log.info("%s Deletes sub_client %s", "*" * 8, "*" * 8)
            self.fs_sub_client.delete_subclient(subclient_name=self.sub_client_name,
                                                backupset_name=self.tcinputs['BackupsetName'])
            self.admin_console.wait_for_completion()

    def setup(self):
        """ Pre-requisites for this test case """
        self.log.info("Initializing pre-requisites")
        self.browser = BrowserFactory().create_browser_object()
        self.download_path = str(os.path.join(Path.home(), "Downloads"))
        self.browser.set_downloads_dir(self.download_path)
        self.browser.open()
        self.fs_helper = FSHelper(self)
        self.fs_helper.populate_tc_inputs(self, mandatory=False)

        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)

        #Updated login method to use paramters from config.json
        #Added this so that cases can be handled from autocenter
        self.admin_console.login(username=self.config.ADMIN_USERNAME,
                                 password=self.config.ADMIN_PASSWORD)

        self.hub_dashboard = Dashboard(
            self.admin_console,
            HubServices.file_system,
            app_type=FileObjectTypes.file_server
        )

        try:
            self.admin_console.click_button("OK, got it")
        except BaseException:
            self.log.info("No Popup seen")

        self.file_server = FileServers(self.admin_console)
        self.fs_sub_client = Subclient(self.admin_console)
        self.machine = Machine(self.client)
        self.os_name = self.client._properties['client']['osInfo']['Type']

    def run(self):
        """Main function for test case execution"""
        try:
            self.define_content()
            self.navigate_to_client_page()
            self.add_sub_client()
            self.check_download_single_file()
            self.check_download_multiple_file()
            self.check_download_folder_plus_file()

        except Exception as exp:
            handle_testcase_exception(self, exp)


    def tear_down(self):
        if self.cleanup_run:
            self.log.info("Performing cleanup")
            self.delete_sub_client()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
