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

    setup()         --  Initializes pre-requisites for this test case

    run()           --  run function of this test case

Input Example:

   "testCases": {
        "63264": {
            "MachineFQDN": "",
            "MachinePassword": "",
            "MachineUserName": "",
            "OS_TYPE": "",
            "RestorePath": "",
            "CloudStorage": "",
            "Plan": ""
        }
    }

for Unix FS, we need take coder tool v3 encoded tenant_user_password as input in config.json:

    "Metallic": {
        ...,
        "tenant_password": "",
        "tenant_encrypted_password": ""
    }
"""

import time

from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.config import get_config
from AutomationUtils.constants import WINDOWS_CVLT_PACKAGES_ID, UNIX_CVLT_PACKAGES_ID
from FileSystem.FSUtils.fshelper import FSHelper
from Reports.utils import TestCaseUtils
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.Components.panel import Backup, RPanelInfo
from Web.AdminConsole.Storage.CloudStorage import CloudStorage
from Web.AdminConsole.Storage.CloudStorageDetails import CloudStorageDetails
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.constants import HubServices, FileObjectTypes
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers, AddWizard
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """
    Class for executing test case for FS acceptance on Hub
    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Metallic - File server interactive install & backup direct to cloud using existing tenant admin, gateway and storage"
        self.browser = None
        self.fs_obj = None
        self.hub_dashboard = None
        self.admin_console = None
        self.navigator = None
        self.jobs = None
        self.client_machine = None
        self.client = None
        self.config = get_config()
        self.metallic_fs = None
        self.file_server = None
        self.client_name = None
        self.backupset = None
        self.fs_sub_client = None
        self.fs_helper = None
        self.os_name = None
        self.delimiter = None
        self.dest_path = None
        self.slash_format = None
        self.restore_file_path = ''
        self.sub_client_name = None
        self.agentname = "File System"
        self.content = []
        self.exclusions = []
        self.exceptions = []
        self.custompkg_directory = None
        self.packagelist = []
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "MachineFQDN": "",
            "MachinePassword": "",
            "MachineUserName": "",
            "OS_TYPE": "",
            "RestorePath": "",
            "CloudStorage": "",
            "Plan": ""
        }

    def navigate_to_subclients(self):
        """ Navigates to the client page """
        self.navigate_to_file_servers()
        self.file_server.access_server(self.client.display_name)
        time.sleep(60)
        self.admin_console.access_tab("Subclients")
        self.refresh()

    def navigate_to_file_servers(self):
        """ Navigates to file server page"""
        self.navigator.navigate_to_file_servers()
        time.sleep(60)
        self.admin_console.access_tab("File servers")
        self.refresh(60)

    def navigate_to_service_catalog(self):
        """navigates to service catalog"""
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_service_catalogue()

    def refresh(self, wait_time=30):
        """ Refreshes the current page """
        self.log.info("%s Refreshes browser %s", "*" * 8, "*" * 8)
        time.sleep(wait_time)
        self.admin_console.refresh_page()

    @test_step
    def select_backup_gateway(self):
        """ configure backup gateway"""
        if not self.commcell.clients.has_client(self.tcinputs["GatewayFQDN"]):
            self.log.info("client is not installed, start install...")
            raise Exception("gateway does not exist")
        self.gateway = self.commcell.clients.get(self.tcinputs["GatewayFQDN"])
        self.gatewayname = self.gateway.display_name
        self.metallic_fs.select_backup_gatway(self.gatewayname)

    @test_step
    def configure_server(self):
        """ interactive install new file servers"""
        self.admin_console.select_radio(self.os_name.lower())
        self.set_installinputs()
        self.metallic_fs.add_new_server(self.installinputs)
        self.commcell.refresh()
        self.client = self.commcell.clients.get(self.tcinputs["MachineFQDN"])
        self.client_name = self.client.display_name
        self.client_machine = Machine(
            self.client_name,
            self.commcell,
            username=self.tcinputs.get("MachineUserName"),
            password=self.tcinputs.get("MachinePassword"))
        #verify correct packages are installed
        self.client_machine.verify_installed_packages(packages=self.packagelist)

    def set_installinputs(self):
        """
        Creates a dictionary for test case inputs needed for customer package install.
            Args:
                isClient (boolean):    True if machine is client machine
        """
        inputs = {}
        try:
            if self.os_name.lower() == 'windows':
                inputs["full_package_path"] = self.custompkg_directory + \
                    "\\WindowsFileServer64.exe"
                inputs["registering_user_password"] = self.config.ADMIN_PASSWORD
            else:
                inputs["full_package_path"] = self.custompkg_directory + \
                    "\\LinuxFileServer64.tar"
                inputs["registering_user_password"] = self.config.Metallic.tenant_encrypted_password

            inputs['os_type'] = self.os_name.lower()
            inputs["remote_clientname"] = self.tcinputs.get("MachineFQDN")
            inputs["remote_username"] = self.tcinputs.get("MachineUserName")
            inputs["remote_userpassword"] = self.tcinputs.get(
                "MachinePassword")

            inputs["registering_user"] = self.config.ADMIN_USERNAME
            inputs["commcell"] = self.commcell
            self.installinputs = inputs
        except BaseException:
            raise Exception("failed to set inputs for interactive install")

    @test_step
    def configure_local_storage(self):
        """ configure local storage """
        self.localstoragename = self.tcinputs.get("LocalStorage")
        time.sleep(60)
        if not self.metallic_fs.check_if_localstorage_exist(
                self.localstoragename):
            raise Exception("local storage does not exist")
        self.metallic_fs.select_local_storage(self.localstoragename,
                                              self.gatewayname)

    @test_step
    def configure_cloud_storage(self):
        """ configure cloud storage"""
        time.sleep(60)
        self.metallic_fs.select_cloud_storage(
            storagename=self.tcinputs.get("CloudStorage"))

    @test_step
    def configure_plan(self):
        """ configure and select plan"""
        time.sleep(60)
        planname = self.tcinputs.get("Plan")
        self.metallic_fs.select_plan(planname, retention=None)

    def wait_for_job_completion(self, job_id):
        """ Function to wait till job completes
            Args:
                job_id (str): Entity which checks the job completion status
        """
        self.log.info("%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = self.commcell.job_controller.get(job_id)
        return job_obj.wait_for_completion(timeout=60)

    def init_pre_req(self):
        """ Initialize tc inputs"""
        self.restore_file_path = self.tcinputs['RestorePath']
        self.agent = self._client.agents.get(self.agentname)
        self.backupset = self._agent.backupsets.get("defaultBackupSet")
        self.fs_helper = FSHelper(self)
        self.sub_client_name = "default"
        self.dest_path = self.restore_file_path

        if self.os_name.lower() == "windows":
            self.delimiter = "\\"
            #self.dest_path = self.restore_file_path.replace("\\", "/")
            self.slash_format = '\\'
        else:
            self.delimiter = "/"
            #self.dest_path = self.restore_file_path[1:]
            self.slash_format = '/'

    @test_step
    def define_content_and_filters(self):
        """ set subclient content, exclusions and exceptions """
        self.init_pre_req()
        if self.os_name.lower() == "windows":
            self.test_path = self.client.job_results_directory + \
                self.delimiter + "Test" + self.id
        else:
            self.test_path = "/opt/Test" + self.id
        self.client_machine.create_directory(self.test_path, force_create=True)
        self.fs_helper.generate_testdata(['.html', '.css'], self.test_path, 4)

        files_list = self.client_machine.get_files_in_path(self.test_path)
        self.exclusions = [
            file for file in files_list if file.endswith(".html")]
        for i in range(0, len(self.exclusions)):
            if i % 3 == 0:
                self.exceptions.append(self.exclusions[i])

        self.content = [self.test_path]
        disablesystemstate = False
        self.metallic_fs.set_backup_content_filters(
            self.content, self.exclusions, self.exceptions, disablesystemstate)

    @test_step
    def verify_summary_and_click_finish(self):
        """ verify summary page options and complete the configuration"""
        if self.metallic_fs.check_file_server_summary_info():
             self.log.info("file server summary page have no empty entry")
        else:
            raise Exception("file server summary page have empty entry")
        self.admin_console.click_button('Finish')

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
            hash_list.append(
                self.client_machine._get_folder_hash(
                    directory_path=path))
        return hash_list

    def backup_job(self, backup_type):
        """ Function to run a backup job
            Args:
                backup_type (BackupType) : Type of backup (FULL, INCR, DIFFERENTIAL, SYN_FULL)
            Raises:
                Exception :
                 -- if fails to run the backup
        """
        self.navigate_to_subclients()
        self.log.info("%s Starts Backup job %s for subclient %s", backup_type,
                      "*" * 8, "*" * 8)
        job = self.fs_sub_client.backup_subclient(subclient_name=self.sub_client_name, backupset_name="defaultBackupSet", backup_type=backup_type)
        self.wait_for_job_completion(job)
        return job

    def restore_in_place(self):
        """ Restores the subclient
            Raises:
                Exception :
                 -- if fails to run the restore operation
         """
        self.log.info(
            "%s Starts inplace restore for subclient %s",
            "*" * 8,
            "*" * 8)
        self.navigate_to_subclients()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            backupset_name="defaultBackupSet",
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
        self.log.info(
            "%s Starts out_of_place restore for subclient %s",
            "*" * 8,
            "*" * 8)
        if self.client_machine.check_directory_exists(self.restore_file_path):
            self.client_machine.remove_directory(self.restore_file_path)
        self.client_machine.create_directory(self.restore_file_path, False)
        self.navigate_to_subclients()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            backupset_name="defaultBackupSet",
            subclient_name=self.sub_client_name,
            dest_client=self.client.display_name,
            destination_path=self.dest_path)
        self.wait_for_job_completion(restore_job)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()

    def select_files(self, content):
        """ selects few files in the path
            Args:
                content   (str): from where to select files
        """
        self.log.info(
            "%s selects few files from specified folder %s",
            "*" * 8,
            "*" * 8)
        files = self.client_machine.get_files_in_path(content)
        sel_files = []
        for path in files:
            if "css" in path:
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
        if self.client_machine.check_directory_exists(self.restore_file_path):
            self.client_machine.remove_directory(self.restore_file_path)
        self.client_machine.create_directory(self.restore_file_path, False)
        self.navigate_to_subclients()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            backupset_name="defaultBackupSet",
            subclient_name=self.sub_client_name,
            selected_files=select_files,
            dest_client=self.client.display_name,
            destination_path=self.dest_path)
        self.wait_for_job_completion(restore_job)
        self.navigate_to_subclients()

    def check_any_backup_runs(self):
        """Backup is initiated if there are no active job on subclient"""
        self.log.info("%s Runs Full Backup %s", "*" * 8, "*" * 8)
        self.navigator.navigate_to_jobs()
        self.rtable = Rtable(self.admin_console)
        self.rtable.search_for(self.client.display_name)
        self.jobs = Jobs(self.admin_console)
        self.fs_sub_client = Subclient(self.admin_console)
        jobid = self.jobs.get_job_ids()
        if not jobid:
            job_id = self.backup_job(Backup.BackupType.INCR)
        else:
            job_id = jobid[0]
            self.wait_for_job_completion(jobid[0])
        return job_id

    @test_step
    def check_inplace_restore(self):
        """ Runs full backup and restore to validate inplace restore"""
        self.check_any_backup_runs()
        self.refresh()
        source_hash = self.get_content_hash(self.content)
        self.restore_in_place()
        self.validate_inplace_restore(self.content, source_hash)

    @test_step
    def check_out_of_place_restore(self):
        """ Runs Incremental backup and out_of_place retore and validate backup """
        ts = time.time()
        self.client_machine.create_file(
            self.test_path + self.delimiter + 'newfile1' + str(ts) + '.html',
            'New file is created after first incremental backup')
        self.backup_job(Backup.BackupType.INCR)
        self.refresh()
        self.restore_out_of_place()
        self.fs_helper.validate_backup(content_paths=self.content,
                                       restore_path=self.restore_file_path,
                                       add_exclusions=self.exclusions,
                                       exceptions_list=self.exceptions)

    @test_step
    def check_restore_by_select_items(self):
        """ Runs Synth full backup and restores selected items and validate files are
            restored or not
        """
        select_files = self.select_files(self.content[0])
        self.backup_job(Backup.BackupType.SYNTH)
        self.refresh()
        self.restore_selected_files(select_files)
        self.fs_helper.validate_restore_for_selected_files(backup_files=select_files,
                                                           restore_path=self.restore_file_path)

    def set_client_ostype(self):
        """
        get os type from input
        """
        if self.tcinputs.get("OS_TYPE").lower() == "windows":
            self.os_name = "Windows"
        else:
            self.os_name = "Unix"

    def disable_cloud_storage_compliance_lock(self):
        """disable cloud storage compliance lock"""
        if self.tcinputs.get("CloudStorageAccount") == "Air Gap Protect":
            self.navigator.navigate_to_air_gap_protect_storage()
        else:
            self.navigator.navigate_to_cloud_storage()

        _cloud_storage = CloudStorage(self.admin_console)
        _cloud_storage.select_cloud_storage(self.tcinputs.get("CloudStorage"))
        _cloud_storage_details = CloudStorageDetails(self.admin_console)
        _cloud_storage_details.disable_compliance_lock()

    @test_step
    def cleanup(self):
        """ Cleanup test clients """
        self.disable_cloud_storage_compliance_lock()
        myservers = Servers(self.admin_console)
        self.navigator.navigate_to_servers()

        self.log.info(
            "retire and delete file server: %s",
            self.client.display_name)
        if myservers.is_client_exists(
                self.client.display_name, select_from_all_server=True):
            myservers.retire_server(
                self.client.display_name,
                select_from_all_server=True)
        time.sleep(30)
        self.navigator.navigate_to_jobs()
        self.rtable.search_for(self.client.display_name)
        jobid = self.jobs.get_job_ids()
        if len(jobid):
            self.wait_for_job_completion(jobid[0])

        self.navigator.navigate_to_servers()
        self.refresh()
        if myservers.is_client_exists(
                self.client.display_name, select_from_all_server=True):
            myservers.delete_server(
                self.client.display_name,
                select_from_all_server=True)

    def setup(self):
        """ Pre-requisites for this testcase """
        self.set_client_ostype()
        self.utils.reset_temp_dir()
        self.custompkg_directory = self.utils.get_temp_dir()
        if self.os_name.lower() == "windows":
            packages = WINDOWS_CVLT_PACKAGES_ID
        else:
            packages = UNIX_CVLT_PACKAGES_ID
        self.packagelist.append(packages['File System Core'])
        self.packagelist.append(packages['File System'])
        self.packagelist.append(packages['Storage Accelerator'])
        self.browser = BrowserFactory().create_browser_object()
        self.browser.set_downloads_dir(self.custompkg_directory)
        self.log.info("%s Opening the browser %s", "*" * 8, "*" * 8)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.config.ADMIN_USERNAME,
                                 password=self.config.ADMIN_PASSWORD)

    def run(self):
        """Main function for test case execution"""
        try:
            self.hub_dashboard = Dashboard(self.admin_console,
                                           HubServices.file_system,
                                           app_type=FileObjectTypes.file_server)

            self.refresh(60)
            try:
                self.admin_console.click_button("OK, got it")
            except:
                pass
            self.navigate_to_service_catalog()
            self.hub_dashboard.choose_service_from_dashboard()
            self.hub_dashboard.click_new_configuration()
            self.metallic_fs = AddWizard(self.admin_console)
            self.metallic_fs.select_file_server_env(backuptocloud=True)
            self.configure_cloud_storage()
            self.configure_plan()

            self.configure_server()
            self.define_content_and_filters()
            self.verify_summary_and_click_finish()

            # restart service
            self.navigate_to_file_servers()
            self.file_server = FileServers(self.admin_console)
            self.file_server.restart_client_service(self.client.display_name)
            time.sleep(180)

            self.check_inplace_restore()
            #for install case, one backup/restore job is enough
            #self.check_out_of_place_restore()
            #self.check_restore_by_select_items()

            self.cleanup()

        except Exception as excp:
            handle_testcase_exception(self, excp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
