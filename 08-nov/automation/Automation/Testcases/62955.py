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
"""
import time, datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Table, Rtable, Rfilter
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs

class TestCase(CVTestCase):
    """ Command center: Testcase to check all types backup/restore and
                        verify Verify BLocklevel  cases through command center.
    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Verify BLocklevel cases from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.table = None
        self.machine = None
        self.dest_machine = None
        self.fs_sub_client = None
        self.fs_subclient_details = None
        self.jobs_page = None
        self.rt =None
        self.fs_helper = None
        self.os_name = None
        self.delimiter = None
        self.dest_path = None
        self.path_data = None
        self.restore_file_path = ''
        self.restore_path = ''
        self.sub_client_name = 'Test_57912'
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

    @test_step
    def navigate_to_client_page(self):
        """ Navigates to the input client page """
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_file_servers()
        self.table.access_link(self.client.display_name)  # navigates to selected client page

    @test_step
    def navigate_to_client_page(self):
        """ Navigates to the input client page """
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_file_servers()
        self.table.access_link(self.client.display_name)  # navigates to selected client pag


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
        """ Define the subclient content, exclusions and exceptions """
        self.os_name = self.client._properties['client']['osInfo']['Type']
        self.restore_file_path = self.tcinputs['RestorePath']
        path = self.tcinputs['BackupPath']

        if self.os_name == "Windows":
            self.delimiter = "\\"
            self.dest_path = self.restore_file_path.replace("\\", "/")
            self.path_data = path + self.delimiter + 'Test57912'
            self.restore_path = self.restore_file_path+ self.delimiter + 'Test57912'
        else:
            self.delimiter = "/"
            self.dest_path = self.restore_file_path[1:]
            self.path_data = path + self.delimiter + 'Test57912'
            self.restore_path = self.restore_file_path + self.delimiter + 'Test57912'
        self.fs_helper.populate_tc_inputs(self, mandatory=False)
        self.fs_helper.generate_testdata(['.html', '.py'], self.path_data, 100)
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

    @test_step
    def add_subclient(self):
        """ Creates new subclient
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


    @test_step
    def enable_blocklevel(self):
        """Enable blocklevel on specific subclient
            Raises:
                Exception:
                    -- if fails to add entity

        """
        self.navigate_to_client_page()
        self.fs_sub_client.access_subclient(self.tcinputs['BackupsetName'],
                                            subclient_name=self.sub_client_name)
        self.fs_subclient_details.set_block_level(blocklevel=True)

    @test_step
    def enable_blocklevel_file_indexing(self):
        """Enable blocklevel file indexing  on specific subclient
            Raises:
                Exception:
                    -- if fails to add entity

        """
        self.navigate_to_client_page()
        self.fs_sub_client.access_subclient(self.tcinputs['BackupsetName'],
                                            subclient_name=self.sub_client_name)
        self.fs_subclient_details.set_block_level_file_indexing(blocklevel_fi=True)



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
        job = self.fs_sub_client.backup_subclient(self.tcinputs['BackupsetName'],
                                                  self.sub_client_name, backup_type, False)
        self.wait_for_job_completion(job)
        return job

    def restore_in_place(self):
        """ Restores the subclient
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        self.log.info("%s Starts inplace restore for subclient %s", "*" * 8, "*" * 8)

        restore_job = self.fs_sub_client.restore_subclient(
            backupset_name=self.tcinputs['BackupsetName'],
            subclient_name=self.sub_client_name,
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

        restore_job = self.fs_sub_client.restore_subclient(
            backupset_name=self.tcinputs['BackupsetName'],
            subclient_name=self.sub_client_name,
            dest_client=self.client.display_name,
            restore_path=self.dest_path,
            blocklevel=True,
            filelevel=True)
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
        if self.dest_machine.os_info.lower() == 'windows':
            path = res_path.replace('\\', '/')
        else:
            path = res_path[1:]

        if self.dest_machine.os_info.lower() == self.os_name.lower():
            different_os = False
        else:
            different_os = True
        restore_job = self.fs_sub_client.restore_subclient(
            backupset_name=self.tcinputs['BackupsetName'],
            subclient_name=self.sub_client_name,
            dest_client=display_name,
            diff_os=different_os,
            restore_path=path)
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
        res_job = self.fs_sub_client.restore_subclient_by_job(
            backupset_name=self.tcinputs['BackupsetName'],
            subclient_name=self.sub_client_name,
            job_id=job_id,
            dest_client=self.client.display_name,
            restore_path=self.dest_path)
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
        restore_job = self.fs_sub_client.restore_selected_items(
            backupset_name=self.tcinputs['BackupsetName'],
            subclient_name=self.sub_client_name,
            del_file_content_path=content,
            dest_client=self.client.display_name,
            restore_path=self.dest_path,
            file_system=self.os_name)
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
        restore_job = self.fs_sub_client.restore_selected_items(
            backupset_name=self.tcinputs['BackupsetName'],
            subclient_name=self.sub_client_name,
            selected_files=select_files,
            dest_client=self.client.display_name,
            restore_path=self.dest_path,
            file_system=self.os_name)
        self.wait_for_job_completion(restore_job)
        self.navigate_to_client_page()

    def check_any_backup_runs(self):
        """Backup is initiated if there are active job on subclient"""
        self.log.info("%s Runs Full Backup %s", "*" * 8, "*" * 8)
        self.fs_sub_client.backup_history_subclient(backupset_name=self.tcinputs['BackupsetName'],
                                                    subclient_name=self.sub_client_name)
        self.admin_console.access_tab('Active jobs')
        jobid = self.table.get_column_data('Job Id')
        self.browser.driver.back()
        self.browser.driver.back()
        self.admin_console.wait_for_completion()
        self.navigate_to_client_page()
        if not jobid:
            job_id = self.backup_job(Backup.BackupType.FULL)
        else:
            job_id = jobid[0]
            self.wait_for_job_completion(jobid[0])
        return job_id

    @test_step
    def check_inplace_restore(self):
        """ Runs full backs and restore to validate inplace restore"""
        self.check_any_backup_runs()
        self.refresh()
        source_hash = self.get_content_hash(self.content)
        self.restore_in_place()
        self.validate_inplace_restore(self.content, source_hash)

    @test_step
    def check_cross_machine_restore(self):
        """ Runs Incremental backup and cross_machine retore and validate backup """
        self.machine.create_file(self.content[0] + self.delimiter + 'newfile.html',
                                 'New file is created after first full backup')
        self.backup_job(Backup.BackupType.INCR)
        self.refresh()
        restore_path = self.restore_cross_machine()
        self.fs_helper.validate_cross_machine_restore(content_paths=self.subclient.content,
                                                      restore_path=restore_path,
                                                      dest_client=self.tcinputs['RestoreMachine'])

    @test_step
    def check_out_of_place_restore(self, backuptype='INCR'):
        """ Runs Incremental backup and out_of_place retore and validate backup """
        self.path_data = self.path_data + self.delimiter + backuptype + \
                         datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.fs_helper.populate_tc_inputs(self, mandatory=False)
        self.fs_helper.generate_testdata(['.html', '.py'], self.path_data, 10)
        if backuptype == 'FULL':
            self.backup_job(Backup.BackupType.FULL)
        elif backuptype == 'SYNTH':
            self.backup_job(Backup.BackupType.SYNTH)
        else:
            self.backup_job(Backup.BackupType.INCR)
        self.refresh()
        self.restore_out_of_place()
        self.fs_helper.validate_backup(content_paths=self.subclient.content,
                                       restore_path=self.restore_file_path)

    @test_step
    def check_file_indexing_job(self):
        """ FIle indexing job validation in Job controller and get job id """
        job_type = "File Indexing"
        self.navigator.navigate_to_jobs()
        self.jobs_page.access_active_jobs()
        self.rt.search_for(job_type)
        ids_list = self.jobs_page.get_job_ids()
        self.jobs_page.add_filter('Subclient', self.sub_client_name, Rfilter.contains)
        id_list = self.jobs_page.get_job_ids()
        self.jobs_page.clear_filter('Subclient', self.sub_client_name)
        if id_list is None:
            id_list = ids_list
        for job in id_list:
            self.wait_for_job_completion(job)
        self.navigate_to_client_page()

    @test_step
    def check_restore_by_job(self):
        """ Runs Synth full backup and restores by job and validate backup"""
        job_id = self.backup_job(Backup.BackupType.SYNTH)
        self.refresh()
        self.restore_by_job(job_id)
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
        """ Restores selected items and validate files are restored or not """
        select_files = self.select_files(self.subclient.content[0])
        self.restore_selected_files(select_files)
        self.fs_helper.validate_restore_for_selected_files(backup_files=select_files,
                                                           restore_path=self.restore_file_path)

    @test_step
    def delete_sub_client(self):
        """ Verifies whether subclient exists or not and then deletes the subclient """
        if self.fs_sub_client.is_subclient_exists(self.sub_client_name):
            self.log.info("%s Deletes subclient %s", "*" * 8, "*" * 8)
            self.fs_sub_client.delete_subclient(self.tcinputs['BackupsetName'],
                                                self.sub_client_name)
            self.admin_console.wait_for_completion()

    def setup(self):
        """ Pre-requisites for this testcase """
        self.log.info("Initializing pre-requisites")
        self.browser = BrowserFactory().create_browser_object()
        self.log.info("%s Opening the browser %s", "*" * 8, "*" * 8)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        self.fs_helper = FSHelper(self)
        self.table = Table(self.admin_console)
        self.fs_sub_client = FsSubclient(self.admin_console)
        self.fs_subclient_details = FsSubclientDetails(self.admin_console)
        self.jobs_page = Jobs(self.admin_console)
        self.rt = Rtable(self.admin_console)
        self.machine = Machine(self.client)
        self.dest_machine = Machine(self.tcinputs['RestoreMachine'], self.commcell)

    def run(self):
        """Main function for test case execution"""
        try:
            self.define_content()
            self.navigate_to_client_page()
            self.add_subclient()
            self.enable_blocklevel()
            time.sleep(30)
            self.navigate_to_client_page()
            self.check_out_of_place_restore(backuptype='FULL')
            self.navigate_to_client_page()
            self.check_out_of_place_restore(backuptype='INCR')
            self.navigate_to_client_page()
            self.check_out_of_place_restore(backuptype='SYNTH')
            self.delete_sub_client()

        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.log.info("Performing cleanup")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
