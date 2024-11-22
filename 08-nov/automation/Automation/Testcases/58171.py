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
        "58171": {
          "ClientName": "",
          "AgentName": "",
          "BackupsetName": "",
          "PlanName": "",
          "RestoreMachine": "",
          "RestorePath": "",
          "RestorePathForCrossMachine": ""
        }
    }
"""
from http import client
import time
from Web.AdminConsole.Hub.dashboard import Dashboard
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from cvpysdk.constants import AppIDAType
from Web.AdminConsole.Hub.constants import HubServices, FileObjectTypes


class TestCase(CVTestCase):
    """ Command center: Testcase verifies all types backup/restore and
                        verify them through command center.
    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Verifies all types of backups/restores from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.jobs = None
        self.machine = None
        self.dest_machine = None
        self.file_server = None
        self.fs_sub_client = None
        self.fs_helper = None
        self.os_name = None
        self.delimiter = None
        self.config = get_config()
        self.restore_file_path = ''
        self.sub_client_name = 'Test_58171'
        self.content = []
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "BackupsetName": None,
            "PlanName": None,
            "RestoreMachine": None,
            "RestorePath": None,
            "RestorePathForCrossMachine": None
        }

    def navigate_to_client_page(self):
        """ Navigates to the input client page """
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.file_server.access_server(self.client.display_name)
        self.admin_console.wait_for_completion()
        self.admin_console.access_tab("Subclients")
        self.admin_console.wait_for_completion()
        self.refresh()

    def refresh(self, wait_time=180):
        """ Refreshes the current page """
        self.log.info("%s Refreshes browser %s", "*" * 8, "*" * 8)
        time.sleep(wait_time)
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
    def init_pre_req(self):
        """ Initialize tc inputs"""
        self.os_name = self.client._properties['client']['osInfo']['Type']
        self.restore_file_path = self.tcinputs['RestorePath']
        if self.os_name == "Windows":
            self.delimiter = "\\"
            # setting appTypeId for DB query
            self.appTypeId = AppIDAType.WINDOWS_FILE_SYSTEM.value
        else:
            self.delimiter = "/"
            # setting appTypeId for DB query
            self.appTypeId = AppIDAType.LINUX_FILE_SYSTEM.value
        self.navigate_to_client_page()
        val = self.fs_sub_client.is_subclient_exists(subclient_name=self.sub_client_name,
                                                     backupset_name=self.tcinputs['BackupsetName'])
        if not val:
            self.add_subclient()
        else:
            self.subclient = self.backupset.subclients.get(self.sub_client_name)

    def define_content(self):
        """ Define the subclient content, exclusions and exceptions """
        if self.os_name == "Windows":
            path = self.client.job_results_directory + self.delimiter + 'Test58171'
        else:
            path = '/opt/Test58171'
        self.fs_helper.generate_testdata(['.html', '.py'], path, 6)
        self.content.append(path)

    def get_content_hash(self, content):
        """Returns set of files and their MD5 hash values present on the input path
                Args:
                     content      (list)  --  list of folders paths to get hash values of.
                Returns:
                    list     -   list of folder paths and their hash value

        """
        self.log.info("%s Gets hash_value of a folder %s", "*" * 8, "*" * 8)
        hash_list = []
        for path in content:
            hash_list.append(self.machine._get_folder_hash(directory_path=path))
        return hash_list

    def add_subclient(self):
        """ Creates new subclient
                Raises:
                    Exception:
                        -- if fails to add entity
        """
        self.define_content()
        self.delete_sub_client()
        # toggle_own_content should be true only when plan has predefined contents
        self.fs_sub_client.add_subclient(subclient_name=self.sub_client_name,
                                         plan_name=self.tcinputs['PlanName'],
                                         contentpaths=self.content,
                                         backupset_name=self.tcinputs['BackupsetName'],   
                                         define_own_content=True,
                                         remove_plan_content=True)
        
        self.backupset.subclients.refresh()
        self.subclient = self.backupset.subclients.get(self.sub_client_name)
        self.refresh()

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
        self.navigate_to_client_page()
        job = self.fs_sub_client.backup_subclient(backupset_name=self.tcinputs['BackupsetName'],
                                                  subclient_name=self.sub_client_name, 
                                                  backup_type=backup_type)
        self.wait_for_job_completion(job)
        return job

    def restore_in_place(self):
        """ Restores the subclient
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        self.log.info("%s Starts inplace restore for subclient %s", "*" * 8, "*" * 8)
        self.navigate_to_client_page()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            subclient_name=self.sub_client_name,
            backupset_name=self.tcinputs['BackupsetName'],
            dest_client=self.client.display_name,
            unconditional_overwrite=True)
        self.wait_for_job_completion(restore_job)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()

    def validate_inplace_restore(self, content_paths, content_hash_values):
        """ Validates backup files are backedup or not
                Args:
                    content_paths   list(paths): list of paths that are restored
                    content_hash_values     list(hash_values): list of hash_values before restore
        """
        self.log.info("%s Validates inplace restore %s", "*" * 8, "*" * 8)
        restore_hash = self.get_content_hash(content_paths)
        flag = True
        for idx, key in enumerate(content_hash_values):
            diff = key - restore_hash[idx]
            if bool(diff):
                flag = False
                break

        if not flag:
            raise Exception("Files are not backed up")

    def restore_out_of_place(self):
        """ Restores the subclient
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        self.log.info("%s Starts out_of_place restore for subclient %s", "*" * 8, "*" * 8)
        
        if self.machine.check_directory_exists(self.restore_file_path):
            self.machine.remove_directory(self.restore_file_path)
        self.machine.create_directory(self.restore_file_path, False)
        self.navigate_to_client_page()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            subclient_name=self.sub_client_name,
            backupset_name=self.tcinputs['BackupsetName'],
            dest_client=self.client.display_name,
            destination_path=self.restore_file_path)
        self.wait_for_job_completion(restore_job)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()

    def restore_cross_machine(self):
        """ Restores the subclient
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        self.log.info("%s Starts cross machine restore for subclient %s", "*" * 8, "*" * 8)
        res_path = self.tcinputs['RestorePathForCrossMachine']
        dest_obj = self.commcell.clients.get(self.tcinputs['RestoreMachine'])
        display_name = dest_obj.display_name

        if self.dest_machine.check_directory_exists(res_path):
            self.dest_machine.remove_directory(res_path)
        self.dest_machine.create_directory(directory_name=res_path)

            
        self.navigate_to_client_page()

        restore_job = self.fs_sub_client.restore_subclient(
            subclient_name=self.sub_client_name,
            backupset_name=self.tcinputs['BackupsetName'],
            dest_client=display_name,
            destination_path=res_path)
        self.wait_for_job_completion(restore_job)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()
        return res_path

    def restore_by_job(self, job_id):
        """ Restores the subclient for specific job
                Args:
                    job_id  (str): job_id of the backup job to be restored
                Raises:
                    Exception :
                     -- if fails to run the restore operation
        """
        self.log.info("%s Starts restore for subclient for selected job %s", "*" * 8, "*" * 8)
        
        if self.machine.check_directory_exists(self.restore_file_path):
            self.machine.remove_directory(self.restore_file_path)
        self.machine.create_directory(self.restore_file_path, False)
        self.navigate_to_client_page()
        self.refresh()
        res_job = self.fs_sub_client.restore_subclient(
            subclient_name=self.sub_client_name,
            backupset_name=self.tcinputs['BackupsetName'],
            dest_client=self.client.display_name,
            destination_path=self.restore_file_path,
            job_id=job_id)
        self.wait_for_job_completion(res_job)
        self.navigate_to_client_page()

    def del_files(self, content):
        """ Deletes few files in the path
                Args:
                    content   (str): from where to delete files
        """
        self.log.info("%s deletes few files from a folder %s", "*" * 8, "*" * 8)
        files = self.machine.get_files_in_path(content)
        count = 0
        del_files = []
        for path in files:
            count += 1
            if count % 4 == 0:
                self.machine.delete_file(path)
                del_files.append(path)
        return del_files

    def restore_deleted_files(self, content):
        """ Restores the deletes files of subclient
                Args:
                    content   (str): restore deleted files from specific folders.
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        self.log.info("%s Starts restore for deleted files in subclient %s", "*" * 8, "*" * 8)
        
        if self.machine.check_directory_exists(self.restore_file_path):
            self.machine.remove_directory(self.restore_file_path)
        self.machine.create_directory(self.restore_file_path, False)
        self.navigate_to_client_page()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            subclient_name=self.sub_client_name,
            backupset_name=self.tcinputs['BackupsetName'],
            dest_client=self.client.display_name,
            destination_path=self.restore_file_path,
            deleted_items_path=[content])
        self.wait_for_job_completion(restore_job)
        self.navigate_to_client_page()

    def select_files(self, content):
        """ selects few files in the path
                Args:
                    content   (str): from where to delete files
        """
        self.log.info("%s selects few files from specified folder %s", "*" * 8, "*" * 8)
        files = self.machine.get_files_in_path(content)
        count = 0
        sel_files = []
        for path in files:
            count += 1
            if count % 3 == 0:
                sel_files.append(path)
        return sel_files

    def restore_selected_files(self, select_files):
        """ Restores the selected files from subclient
                Args:
                    select_files   list(file_paths): files to be restored.
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        self.log.info("%s Starts restore for subclient for selected files %s",
                      "*" * 8, "*" * 8)
        if self.machine.check_directory_exists(self.restore_file_path):
            self.machine.remove_directory(self.restore_file_path)
        self.machine.create_directory(self.restore_file_path, False)
        self.navigate_to_client_page()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            subclient_name=self.sub_client_name,
            backupset_name=self.tcinputs['BackupsetName'],
            dest_client=self.client.display_name,
            selected_files=select_files,
            destination_path=self.restore_file_path)
        self.wait_for_job_completion(restore_job)
        self.navigate_to_client_page()

    def kill_if_any_running_job(self):
        """Kills any active job running for the subclient"""
        self.log.info("%sKilling any active jobs for subclient%s", "*" * 8, "*" * 8)

        # Skips the query to DB if the case is run for metallic
        if not self.isMetallic:
            # Getting running job from csdb as its faster and efficient
            query = f"select * from APP_Application WITH(NOLOCK) where subclientName = '{self.sub_client_name}' and appTypeId = {self.appTypeId}"
            # CSDB is already initialised in cvtestcase.py
            self.csdb.execute(query)
            query_result = self.csdb.fetch_one_row()
            self.log.info(query_result)
            if len(query_result) > 1:
                # If the following subclient exists
                subclient_id = query_result[0]
                query = f"select * from JMBkpJobInfo WITH(NOLOCK) where applicationId = {subclient_id}"
                self.csdb.execute(query)
                query_result = self.csdb.fetch_one_row()
                if len(query_result) > 1:
                    # If there is running job for the subclient
                    self.log.info(query_result)
                    job_id = query_result[0]
                    self.log.info("Killing Job with JOB ID : %s", job_id)
                    self.navigator.navigate_to_jobs()
                    self.admin_console.access_tab('Active jobs')
                    # Need a try and catch to kill jobs as jobs may have completed before it is able to kill
                    try:
                        self.jobs.kill_job(job_id, wait=100)
                    except Exception as E:
                        self.log.info("Error occured at killing the job as job may have finished before kill happens")
                        return
                else:
                    self.log.info("No running jobs for the subclient")
        else:
            self.log.info("Running metallic testcase. Skipping querying the")

    @test_step
    def check_inplace_restore(self):
        """ Runs full backs and restore to validate inplace restore"""
        self.kill_if_any_running_job()
        self.backup_job(Backup.BackupType.FULL)
        self.refresh()
        source_hash = self.get_content_hash(self.content)
        self.restore_in_place()
        self.validate_inplace_restore(self.content, source_hash)

    @test_step
    def check_cross_machine_restore(self):
        """ Runs Incremental backup and cross_machine retore and validate backup """
        ts = time.time()
        self.machine.create_file(
            self.subclient.content[0] + self.delimiter + 'newfile' + str(ts) + '.html',
            'New file is created after first full backup')
        self.backup_job(Backup.BackupType.INCR)
        restore_path = self.restore_cross_machine()
        self.fs_helper.validate_cross_machine_restore(content_paths=self.subclient.content,
                                                      restore_path=restore_path,
                                                      dest_client=self.tcinputs['RestoreMachine'])

    @test_step
    def check_out_of_place_restore(self):
        """ Runs Incremental backup and out_of_place retore and validate backup """
        ts = time.time()
        self.machine.create_file(
            self.subclient.content[0] + self.delimiter + 'newfile1' + str(ts) + '.html',
            'New file is created after first incremental backup')
        self.backup_job(Backup.BackupType.INCR)
        self.restore_out_of_place()
        self.fs_helper.validate_backup(content_paths=self.subclient.content,
                                       restore_path=self.restore_file_path)

    @test_step
    def check_restore_by_delete_items(self):
        """ Runs Incremental backup and restores deleted items and validate deleted files """
        del_files = self.del_files(self.subclient.content[0])
        self.backup_job(Backup.BackupType.INCR)
        self.refresh()
        self.restore_deleted_files(self.subclient.content[0])
        self.fs_helper.validate_restore_for_selected_files(backup_files=del_files,
                                                           restore_path=self.restore_file_path)

    @test_step
    def check_restore_by_select_items(self):
        """ Runs Synth full backup and restores selected items and validate files are
            restored or not
        """
        select_files = self.select_files(self.subclient.content[0])
        self.backup_job(Backup.BackupType.SYNTH)
        self.restore_selected_files(select_files)
        self.fs_helper.validate_restore_for_selected_files(backup_files=select_files,
                                                           restore_path=self.restore_file_path)

    @test_step
    def check_restore_by_job(self):
        """ Runs Incremental backup and restores by job and validate backup"""
        ts = time.time()
        self.machine.create_file(
            self.subclient.content[0] + self.delimiter + 'newfile2' + str(ts) + '.html',
            'New file is created after first incremental backup')
        job_id = self.backup_job(Backup.BackupType.INCR)
        self.refresh()
        self.restore_by_job(job_id)
        self.fs_helper.validate_backup(content_paths=self.subclient.content,
                                       restore_path=self.restore_file_path)

    def delete_sub_client(self):
        """ Verifies whether subclient exists or not and then deletes the subclient """
        if self.fs_sub_client.is_subclient_exists(subclient_name=self.sub_client_name,
                                                  backupset_name=self.tcinputs['BackupsetName']):
            self.kill_if_any_running_job()
            self.navigate_to_client_page()
            self.log.info("%s Deletes subclient %s", "*" * 8, "*" * 8)
            self.fs_sub_client.delete_subclient(subclient_name=self.sub_client_name,
                                                  backupset_name=self.tcinputs['BackupsetName'])
            self.admin_console.wait_for_completion()

    def setup(self):
        """ Pre-requisites for this testcase """
        self.log.info("Initializing pre-requisites")
        self.browser = BrowserFactory().create_browser_object()
        self.log.info("%s Opening the browser %s", "*" * 8, "*" * 8)
        self.fs_helper = FSHelper(self)
        self.fs_helper.populate_tc_inputs(self, mandatory=False)
        self.isMetallic = self.tcinputs.get("IsMetallic", "false").lower() == "true"
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)

        # Updated login method to use paramters from config.json
        # Added this so that cases can be handled from autocenter
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

        self.jobs = Jobs(self.admin_console)
        self.file_server = FileServers(self.admin_console)
        self.fs_sub_client = Subclient(self.admin_console)
        self.machine = Machine(self.client)
        self.dest_machine = Machine(self.commcell.clients.get(self.tcinputs['RestoreMachine']))
        self.navigator = self.admin_console.navigator

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_pre_req()
            self.check_inplace_restore()
            self.check_cross_machine_restore()
            self.check_out_of_place_restore()
            self.check_restore_by_delete_items()
            self.check_restore_by_job()
            self.check_restore_by_select_items()

        except Exception as excp:
            handle_testcase_exception(self, excp)

    def tear_down(self):
        if self.cleanup_run:
            self.log.info("Performing cleanup")
            self.delete_sub_client()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
