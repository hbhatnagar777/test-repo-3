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

Input:
    "testCases": {
        "58296": {
          "ClientName": "",
          "AgentName": "",
          "BackupsetName": "",
          "PlanName": "",
          "RestorePath": ""
        }
    }
"""
import glob
import os
import time
from pathlib import Path

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient, FsAgent
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """ Command center: Testcase to verify preview of files
                        through command center.
    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Verify preview/download feature of file from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.machine = None
        self.file_server = None
        self.fs_agent = None
        self.fs_sub_client = None
        self.sub_client_details = None
        self.download_path = None
        self.fs_helper = None
        self.os_name = None
        self.restore_file_path = ""
        self.sub_client_name = 'Test_58296'
        self.content = []
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "BackupsetName": None,
            "PlanName": None,
            "RestorePath": None
        }

    @test_step
    def navigate_to_client_page(self):
        """ Navigates to the input client page """
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_file_servers()
        self.refresh()
        self.file_server.access_server(self.client.display_name)
        self.refresh()

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
        self.restore_file_path = self.tcinputs['RestorePath']
        if self.os_name == 'Windows':
            directory_path = self.machine.join_path(self.client.job_results_directory, 'Test')
        else:
            directory_path = '/opt/58296'
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
        self.fs_sub_client.add_fs_subclient(backup_set=self.tcinputs['BackupsetName'],
                                            subclient_name=self.sub_client_name,
                                            plan=self.tcinputs['PlanName'],
                                            define_own_content=True,
                                            backup_data=self.content,
                                            file_system=self.os_name,
                                            remove_plan_content=True)
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
        job = self.fs_sub_client.backup_subclient(backupset_name=self.tcinputs['BackupsetName'],
                                                  subclient_name=self.sub_client_name,
                                                  backup_type=backup_type)
        self.wait_for_job_completion(job)
        return job

    @test_step
    def delete_sub_client(self):
        """ Verifies whether subclient exists or not and then deletes the subclient """
        if self.fs_sub_client.is_subclient_exists(self.sub_client_name):
            self.log.info("%s Deletes subclient %s", "*" * 8, "*" * 8)
            self.fs_sub_client.delete_subclient(self.tcinputs['BackupsetName'],
                                                self.sub_client_name)
            self.admin_console.wait_for_completion()

    def define_modify_file(self, file_path):
        """ Sets the modify file
                Args:
                    file_path (str): location of the file.
                Returns :
                     file_content_before_change : path of modified file
        """
        file_content_before_change = self.machine.read_file(file_path)
        self.machine.modify_content_of_file(file_path=file_path,
                                            content="New line is added")
        return file_content_before_change

    def get_download_folder(self, file_type):
        """ Gets the download folder
                file_type(str): extension type of the file.
        """
        newest_file_type = max(
            glob.iglob(os.path.join(self.download_path, '*.{0}'.format(file_type))),
            key=os.path.getctime)
        return newest_file_type

    def preview_file(self, file_path):
        """ Views the selected file
                Args:
                    file_path (str): Path of the file to be selected.
        """
        self.fs_sub_client.preview_selected_items(backupset_name=self.tcinputs["BackupsetName"],
                                                  subclient_name=self.sub_client_name,
                                                  preview_file_path=file_path)

    @test_step
    def check_preview_text_file(self):
        """ Verifies the preview of the text file"""
        file_path = self.machine.join_path(self.subclient.content[0], 'textfile.txt')
        self.machine.create_file(file_path=file_path, content='New text file is created')
        self.backup_job(Backup.BackupType.FULL)
        self.refresh()
        self.preview_file(file_path)
        self.fs_helper.validate_preview_file(
            log_directory=self.commcell.commserv_client.log_directory,
            file_type='text')
        self.navigate_to_client_page()

    @test_step
    def check_preview_audio_file(self):
        """ Verifies the preview of the audio file"""
        file_path = self.machine.join_path(self.subclient.content[0], 'audiofile.wav')
        self.machine.create_file(file_path=file_path, content='new audio file created')
        self.backup_job(Backup.BackupType.INCR)
        self.preview_file(file_path)
        self.refresh()
        self.fs_helper.validate_preview_file(
            log_directory=self.commcell.commserv_client.log_directory,
            file_type='audio')
        self.navigate_to_client_page()

    @test_step
    def check_preview_video_file(self):
        """ Verifies the preview of the video file"""
        file_path = self.machine.join_path(self.subclient.content[0], 'videofile.mp3')
        self.machine.create_file(file_path=file_path, content='new video file created')
        self.backup_job(Backup.BackupType.INCR)
        self.preview_file(file_path)
        self.refresh()
        self.fs_helper.validate_preview_file(
            log_directory=self.commcell.commserv_client.log_directory,
            file_type='video')
        self.navigate_to_client_page()

    @test_step
    def check_download_large_file(self):
        """ Verifies the download file feature for large file"""
        file_path = self.machine.join_path(self.subclient.content[0], "File.css")
        file_size = int(1024 * 1024 * 1024 * 1.1)  # 1.1GB file_size
        self.machine.create_file(file_path=file_path, content="Large File", file_size=file_size - 1)
        self.backup_job(Backup.BackupType.INCR)
        if self.machine.check_directory_exists(self.restore_file_path):
            self.machine.remove_directory(self.restore_file_path)
        self.machine.create_directory(directory_name=self.restore_file_path)

        if self.os_name == "Windows":
            des_path = self.restore_file_path.replace("\\", "/")
        else:
            des_path = self.restore_file_path[1:]
        self.refresh()
        self.fs_sub_client.download_selected_items(backupset_name=self.tcinputs['BackupsetName'],
                                                   subclient_name=self.sub_client_name,
                                                   download_files=[file_path],
                                                   file_system=self.os_name,
                                                   dest_client=self.client.display_name,
                                                   restore_path=des_path,
                                                   files_size=int(self.machine.get_file_size(file_path)))
        self.admin_console.wait_for_completion()
        self.navigate_to_client_page()
        self.fs_helper.validate_restore_for_selected_files(backup_files=[file_path],
                                                           restore_path=self.restore_file_path)

    @test_step
    def check_download_particular_file_version(self):
        """Downloads particular version of file"""
        if self.os_name.lower() == 'windows':
            file_path = 'C:\\file2.txt'
        else:
            file_path = '/opt/file2.txt'
        file_content = 'New file is created'
        self.machine.create_file(file_path, file_content)
        self.fs_sub_client.access_subclient(self.tcinputs['BackupsetName'], self.sub_client_name)
        self.sub_client_details.edit_content(browse_and_select_data=False,
                                             backup_data=[file_path],
                                             file_system=self.os_name)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()
        self.backup_job(Backup.BackupType.INCR)
        data = self.define_modify_file(file_path)
        data = data.rstrip()
        self.backup_job(Backup.BackupType.INCR)
        self.fs_sub_client.download_selected_items(backupset_name=self.tcinputs['BackupsetName'],
                                                   subclient_name=self.sub_client_name,
                                                   download_files=[file_path],
                                                   file_system=self.os_name,
                                                   version_nums=['1'])
        self.admin_console.wait_for_completion()
        self.navigate_to_client_page()
        path = self.get_download_folder('txt')
        self.fs_helper.validate_download_files(
            backup_files={os.path.basename(file_path): data},
            download_path=path)

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

        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        if self.tcinputs.get("isMetallic"):
            # TODO : IMPORT HUB AND USE ADVANCE OPTION TO OPNE CONSOLE
            self.log.info("\n\n%s RUNNING TESTCASE FOR METALLIC %s\n", "-" * 5, "-" * 5)
            self.admin_console.login(enable_sso="False")
        self.fs_agent = FsAgent(self.admin_console)

        self.file_server = FileServers(self.admin_console)
        self.fs_sub_client = FsSubclient(self.admin_console)
        self.sub_client_details = FsSubclientDetails(self.admin_console)
        self.machine = Machine(self.client)
        self.os_name = self.client._properties['client']['osInfo']['Type']

    def run(self):
        """Main function for test case execution"""
        try:
            self.define_content()
            self.navigate_to_client_page()
            self.add_sub_client()
            self.check_preview_text_file()
            self.check_preview_audio_file()
            self.check_preview_video_file()
            self.check_download_large_file()
            self.check_download_particular_file_version()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        if self.cleanup_run:
            self.log.info("Performing cleanup")
            self.delete_sub_client()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
