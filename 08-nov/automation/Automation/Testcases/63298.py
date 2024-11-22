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
        "63298": {
            "CloudStorageAccount": "",
            "CloudStorageProvider": "",
            "CloudStorageRegion": "",
            "MachineFQDN": "",
            "MachinePassword": "",
            "MachineUserName": "",
            "OS_TYPE": "",
            "RestorePath": "",
            "GatewayFQDN": "",
            "GatewayPassword": "",
            "GatewayUserName": "",
            "Disklibpath": "",
            "UNCusername": "",
            "UNCpassword": "",
            "BackupsetName" : ""
        }
    }
"""

import os.path
import time
import datetime

from cvpysdk.commcell import Commcell
from Metallic.hubutils import HubManagement
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.config import get_config
from FileSystem.FSUtils.fshelper import FSHelper
from Reports.utils import TestCaseUtils
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.media_agents import MediaAgents
from Web.AdminConsole.AdminConsolePages.Plans import Plans, RPO
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.Components.panel import Backup, RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.constants import HubServices, FileObjectTypes
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers, AddWizard
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.Storage.CloudStorage import CloudStorage
from Web.AdminConsole.Storage.CloudStorageDetails import CloudStorageDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from AutomationUtils.constants import WINDOWS_CVLT_PACKAGES_ID, UNIX_CVLT_PACKAGES_ID


class TestCase(CVTestCase):
    """
    Class for executing test case for FS acceptance on Hub
    """

    test_step = TestStep()

    def __init__(self):
        """Initializing the reference variables"""
        super(TestCase, self).__init__()
        self.name = "Metallic - File server push install & backup via gateway using new tenant admin"
        self.browser = None
        self.fs_obj = None
        self.hub_dashboard = None
        self.admin_console = None
        self.navigator = None
        self.jobs = None
        self.client_machine = None
        self.client = None
        self.metallic_fs = None
        self.file_server = None
        self.client_name = None
        self.backupset = None
        self.fs_sub_client = None
        self.fs_helper = None
        self.os_name = None
        self.delimiter = None
        self.install_validator = None
        self.dest_path = None
        self.slash_format = None
        self.restore_file_path = ""
        self.sub_client_name = None
        self.agentname = "File System"
        self.content = []
        self.exclusions = []
        self.exceptions = []
        self.packagelist = []
        self.custompkg_directory = None
        self.utils = TestCaseUtils(self)
        self.hubmgr = None
        self.tenantname = None
        self.tenantuser = None
        self.config = get_config()
        self.tenantpassword = None
        self.tenantencryptedpassword = None
        self.planname = None
        self.installinputs = None
        self.tcinputs = {
            "MachineFQDN": None,
            "MachineUserName": None,
            "MachinePassword": None,
            "CloudStorageAccount": None,
            "CloudStorageProvider": None,
            "CloudStorageRegion": None,
            "RestorePath": None,
            "OS_TYPE": None,
            "RestorePath": None,
            "GatewayFQDN": None,
            "Disklibpath": None,
            "UNCusername": None,
            "UNCpassword": None,
            "TestPath": None,
            "BackupsetName": None,
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
        """Refreshes the current page"""
        self.log.info("%s Refreshes browser %s", "*" * 8, "*" * 8)
        time.sleep(wait_time)
        self.admin_console.refresh_page()

    @test_step
    def select_backup_gateway(self):
        """configure backup gateway"""
        time.sleep(60)
        if not self.commcell.clients.has_client(self.tcinputs.get("GatewayFQDN")):
            self.log.info("client is not installed, start install...")
            self.set_installinputs(isClient=False)
            self.metallic_fs.add_new_gateway(self.installinputs)
        # time.sleep(60)
        self.commcell.refresh()
        self.gateway = self.commcell.clients.get(self.tcinputs.get("GatewayFQDN"))
        self.gatewayname = self.gateway.display_name
        self.gatewayname_on_dropdown = self.gateway.display_name + " (" + self.gateway.client_hostname + ")"
        self.metallic_fs.select_backup_gatway(self.gatewayname_on_dropdown)
        self.gatewaymachine = Machine(
            self.tcinputs.get("GatewayFQDN"),
            self.commcell,
            username=self.tcinputs.get("GatewayUserName"),
            password=self.tcinputs.get("GatewayPassword"),
        )

    def enable_network_gateway_role(self, gatewayname):
        """enable network gateway role for newly install backup gateway"""
        self.navigator.navigate_to_servers()
        self.refresh()
        myservers = Servers(self.admin_console)
        #myservers.action_update_software(gatewayname)
        myservers.select_client(gatewayname)
        self.admin_console.select_configuration_tab()
        _rpanel_info = RPanelInfo(self.admin_console, "Network settings")
        _rpanel_info.edit_tile()
        self.admin_console.checkbox_select(checkbox_id="enableGateway")
        self.admin_console.click_button('Save')

    def disable_cloud_storage_compliance_lock(self):
        """disable cloud storage compliance lock"""
        if self.tcinputs.get("CloudStorageAccount") == "Air Gap Protect":
            self.navigator.navigate_to_air_gap_protect_storage()
        else:
            self.navigator.navigate_to_cloud_storage()
        _cloud_storage = CloudStorage(self.admin_console)
        self.cloudstoragename = _cloud_storage.list_cloud_storage()[0]
        _cloud_storage.select_cloud_storage(_cloud_storage.list_cloud_storage()[0])
        _cloud_storage_details = CloudStorageDetails(self.admin_console)
        _cloud_storage_details.disable_compliance_lock()

    @test_step
    def configure_server(self):
        """push install new file servers"""
        self.admin_console.select_radio(id="PUSH")
        self.set_installinputs()
        self.log.info("Install inputs set")
        self.metallic_fs.push_add_new_server(self.tcinputs)

    def set_installinputs(self, isClient=True):
        """
        Creates a dictionary for test case inputs needed for customer package install.
            Args:
                isClient (boolean):    True if machine is client machine
        """
        inputs = {}
        try:
            if isClient:
                if self.os_name.lower() == "windows":
                    inputs["full_package_path"] = (
                        self.custompkg_directory + "\\WindowsFileServer64.exe"
                    )
                    inputs["registering_user_password"] = self.tenantpassword
                else:
                    inputs["full_package_path"] = (
                        self.custompkg_directory + "\\LinuxFileServer64.tar"
                    )
                    inputs[
                        "registering_user_password"
                    ] = self.config.Metallic.tenant_encrypted_password

                inputs["os_type"] = self.os_name.lower()
                inputs["remote_clientname"] = self.tcinputs.get("MachineFQDN")
                inputs["remote_username"] = self.tcinputs.get("MachineUserName")
                inputs["remote_userpassword"] = self.tcinputs.get("MachinePassword")
            else:
                inputs["full_package_path"] = (
                    self.custompkg_directory + "\\BackupGateway64.exe"
                )
                inputs["registering_user_password"] = self.tenantpassword
                inputs["os_type"] = "windows"
                inputs["remote_clientname"] = self.tcinputs.get("GatewayFQDN")
                inputs["remote_username"] = self.tcinputs.get("GatewayUserName")
                inputs["remote_userpassword"] = self.tcinputs.get("GatewayPassword")
            inputs["registering_user"] = self.tenantuser
            inputs["commcell"] = self.commcell
            self.installinputs = inputs
        except BaseException:
            raise Exception("failed to set inputs for interactive install")

    @test_step
    def configure_local_storage(self):
        """configure local storage"""
        self.localstoragename = self.gatewayname + "_disk_" + self.tenantname
        self.diskpath = self.tcinputs.get("Disklibpath") + "\\" + self.id
        isnetworkpath = False

        if ":" not in self.tcinputs.get("Disklibpath"):
            isnetworkpath = True
            self.srcdrive = self.gatewaymachine.mount_network_path(
                self.tcinputs.get("Disklibpath"),
                self.tcinputs.get("UNCusername"),
                self.tcinputs.get("UNCpassword"),
            )
            self.mountedpath = self.srcdrive + ":\\" + self.id
        else:
            self.mountedpath = self.diskpath

        if not self.metallic_fs.check_if_localstorage_exist(self.localstoragename):
            self.gatewaymachine.create_directory(self.mountedpath, force_create=True)

        self.metallic_fs.select_local_storage(
            self.localstoragename,
            self.gatewayname,
            self.diskpath,
            self.tcinputs.get("UNCusername"),
            self.tcinputs.get("UNCpassword"),
            networkpath=isnetworkpath,
        )

    @test_step
    def configure_cloud_storage(self, use_only_on_premise_storage=False):
        """configure cloud storage"""
        time.sleep(60)
        if not use_only_on_premise_storage:
            self.metallic_fs.select_cloud_storage(
                storageaccount=self.tcinputs.get("CloudStorageAccount"),
                storageregion=self.tcinputs.get("CloudStorageRegion"),
                storageprovider=self.tcinputs.get("CloudStorageProvider"),
                using_gateway=True,
                storagename=self.tenantname.lower(),
                partialselection=True)
        else:
            self.metallic_fs.select_cloud_storage(
                use_only_on_premise_storage=use_only_on_premise_storage
            )

    @test_step
    def configure_plan(self, planname, use_only_on_premise_storage=False):
        """configure and select plan
        Args:
            planname (str)    :    plan name
        """
        if use_only_on_premise_storage:
            self.retention_rpo = {
                "pri_ret_period": "30",
                "pri_ret_unit": "Day(s)",
                "sec_ret_period": "",
                "sec_ret_unit": "",
                "backup_frequency": "20",
                "backup_frequency_unit": "Hour(s)",
            }
        else:
            self.retention_rpo = {
                "pri_ret_period": "30",
                "pri_ret_unit": "Day(s)",
                "sec_ret_period": "30",
                "sec_ret_unit": "Day(s)",
                "backup_frequency": "20",
                "backup_frequency_unit": "Hour(s)",
            }
        self.metallic_fs.select_plan(planname, self.retention_rpo)

    @test_step
    def verify_plan(self, planname):
        """very plan retention
        Args:
            planname (str)    :    plan name
        """
        myplans = Plans(self.admin_console)
        self.admin_console.navigator.navigate_to_plan()
        if planname in myplans.list_plans():
            myplans.select_plan(planname)
            self.admin_console.access_tab("Backup destinations")
            time.sleep(120)
            rtable = Rtable(self.admin_console,
               id="planBackupDestinationTable")
            data = rtable.get_column_data("Retention period")
            # verify plan retention
            if "1 month" in data[0] and "1 month" in data[1]:
                self.log.info("newly created plan %s have correct retentions", planname)
            else:
                raise Exception("plans %s does not correct retention", planname)

            self.admin_console.access_tab("Overview")
            self.admin_console.checkbox_select(
                checkbox_id="metallicViewToggle")
            time.sleep(30)
            # verify plan rpo
            rpo = RPO(self.admin_console)
            if "Run incremental every 20 hour" in rpo.get_schedules()[0]:
                self.log.info("plan %s have correct rpo settings", planname)
            else:
                raise Exception("plans %s does not correct rpo settings", planname)
        else:
            raise Exception("plans was not created successfully")

    def wait_for_job_completion(self, job_id):
        """Function to wait till job completes
        Args:
            job_id (str): Entity which checks the job completion status
        """
        self.log.info("%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = self.commcell.job_controller.get(job_id)
        return job_obj.wait_for_completion(timeout=60)

    def init_pre_req(self):
        """Initialize tc inputs"""
        self.restore_file_path = self.tcinputs.get("RestorePath")

        self.fs_helper = FSHelper(self)
        # Create subclient as there is an issue where system state is getting selected by default
        self.sub_client_name = "Test_63298"
        self.dest_path = self.restore_file_path
        if self.os_name.lower() == "windows":
            self.delimiter = "\\"
            self.slash_format = "\\"
        else:
            self.delimiter = "/"
            self.slash_format = "/"

    @test_step
    def create_content(self):
        """Creates content in the client"""
        self.client_machine.create_directory(self.test_path, force_create=True)
        self.fs_helper.generate_testdata([".html", ".css"], self.test_path, 6)

    @test_step
    def create_subclient(self):
        """Creates new subclient
        Raises:
            Exception:
                -- if fails to add entity
        """
        self.navigate_to_subclients()
        self.fs_sub_client = Subclient(self.admin_console)
        if self.os_name.lower() == "windows":
            disablesystemstate = True
        else:
            disablesystemstate = False
        self.fs_sub_client.add_subclient(
            subclient_name=self.sub_client_name,
            plan_name=self.planname,
            contentpaths=self.content,
            backupset_name=self.tcinputs["BackupsetName"],
            define_own_content=True,
            disablesystemstate=disablesystemstate
        )

    @test_step
    def define_content(self):
        """set subclient content, exclusions and exceptions"""
        self.init_pre_req()
        self.test_path = self.tcinputs["TestPath"] + self.delimiter + "Test" + self.id
        self.content = [self.test_path]
        disablesystemstate = False
        # TODO - Will updates testcase once issue is fixed
        # As there is a issue with system state being selected , setting no content here
        # Will be creating a new subclient
        self.metallic_fs.set_backup_content_filters(
            contentpaths=[],
            contentfilters=[],
            contentexceptions=[],
            disablesystemstate=disablesystemstate,
        )
        time.sleep(60)

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
            hash_list.append(self.client_machine._get_folder_hash(directory_path=path))
        return hash_list

    def backup_job(self, backup_type):
        """Function to run a backup job
        Args:
            backup_type (BackupType) : Type of backup (FULL, INCR, DIFFERENTIAL, SYN_FULL)
        Raises:
            Exception :
             -- if fails to run the backup
        """
        self.navigate_to_subclients()
        self.log.info(
            "%s Starts Backup job %s for subclient %s", backup_type, "*" * 8, "*" * 8
        )
        job = self.fs_sub_client.backup_subclient(subclient_name=self.sub_client_name, backupset_name="defaultBackupSet", backup_type=backup_type)
        self.wait_for_job_completion(job)
        return job

    def restore_in_place(self):
        """Restores the subclient
        Raises:
            Exception :
             -- if fails to run the restore operation
        """
        self.log.info("%s Starts inplace restore for subclient %s", "*" * 8, "*" * 8)
        self.navigate_to_subclients()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            backupset_name="defaultBackupSet",
            subclient_name=self.sub_client_name,
            dest_client=self.client.display_name,
            unconditional_overwrite=True,
        )
        self.wait_for_job_completion(restore_job)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()

    def validate_inplace_restore(self, content_paths, content_hash_values):
        """Validates backup files are backedup or not
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
        """Restores the subclient
        Raises:
            Exception :
             -- if fails to run the restore operation
        """
        self.log.info(
            "%s Starts out_of_place restore for subclient %s", "*" * 8, "*" * 8
        )
        if self.client_machine.check_directory_exists(self.restore_file_path):
            self.client_machine.remove_directory(self.restore_file_path)
        self.client_machine.create_directory(self.restore_file_path, False)
        self.navigate_to_subclients()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            backupset_name="defaultBackupSet",
            subclient_name=self.sub_client_name,
            dest_client=self.client.display_name,
            destination_path=self.dest_path,
        )
        self.wait_for_job_completion(restore_job)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()

    def select_files(self, content):
        """selects few files in the path
        Args:
            content   (str): from where to select files
        """
        self.log.info("%s selects few files from specified folder %s", "*" * 8, "*" * 8)
        files = self.client_machine.get_files_in_path(content)
        sel_files = []
        for path in files:
            if "css" in path:
                sel_files.append(path)
        return sel_files

    def restore_selected_files(self, select_files):
        """Restores the selected files from subclient
        Args:
            select_files   list(file_paths): files to be restored.
        Raises:
            Exception :
             -- if fails to run the restore operation
        """
        self.log.info(
            "%s Starts restore for subclient for selected files %s", "*" * 8, "*" * 8
        )
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
            destination_path=self.dest_path
        )
        self.wait_for_job_completion(restore_job)
        self.navigate_to_subclients()

    def check_any_backup_runs(self):
        """Backup is initiated if there are no active job on subclient"""
        self.log.info("%s Runs Full Backup %s", "*" * 8, "*" * 8)
        self.navigator.navigate_to_jobs()
        self.rtable.search_for(self.sub_client_name)
        self.jobs = Jobs(self.admin_console)
        jobid = self.jobs.get_job_ids()
        if not jobid:
            job_id = self.backup_job(Backup.BackupType.INCR)
        else:
            job_id = jobid[0]
            self.wait_for_job_completion(jobid[0])
        return job_id

    @test_step
    def check_inplace_restore(self):
        """Runs full backup and restore to validate inplace restore"""
        self.check_any_backup_runs()
        self.refresh()
        source_hash = self.get_content_hash(self.content)
        self.restore_in_place()
        self.validate_inplace_restore(self.content, source_hash)

    @test_step
    def check_out_of_place_restore(self):
        """Runs Incremental backup and out_of_place retore and validate backup"""
        ts = time.time()
        self.client_machine.create_file(
            self.test_path + self.delimiter + "newfile1" + str(ts) + ".html",
            "New file is created after first incremental backup",
        )
        self.backup_job(Backup.BackupType.INCR)
        self.refresh()
        self.restore_out_of_place()
        self.fs_helper.validate_backup(
            content_paths=self.content,
            restore_path=self.restore_file_path,
            add_exclusions=self.exclusions,
            exceptions_list=self.exceptions,
        )

    @test_step
    def check_restore_by_select_items(self):
        """Runs Synth full backup and restores selected items and validate files are
        restored or not
        """
        select_files = self.select_files(self.content[0])
        self.backup_job(Backup.BackupType.SYNTH)
        self.refresh()
        self.restore_selected_files(select_files)
        self.fs_helper.validate_restore_for_selected_files(
            backup_files=select_files, restore_path=self.restore_file_path
        )

    def set_client_ostype(self):
        """
        get os type from input
        """
        if self.tcinputs.get("OS_TYPE").lower() == "windows":
            self.os_name = "Windows"
        else:
            self.os_name = "Unix"

    @test_step
    def verify_ddbpath(self):
        """verify DDB path was created for local storage"""
        self.ddb_path = self.gatewaymachine.join_path(
            os.path.splitdrive(self.gateway.install_directory)[0], "MetallicDDB"
        )
        self.log.info(self.ddb_path)
        if self.gatewaymachine.check_directory_exists(self.ddb_path):
            self.log.info("dedupe is enabled for the storage")
        else:
            raise Exception("dedupe was not enabled for the storage")

    @test_step
    def cleanup(self):
        """Cleanup test gateway and test clients"""

        self.disable_cloud_storage_compliance_lock()

        myservers = Servers(self.admin_console)
        self.navigator.navigate_to_servers()

        self.log.info("retire and delete file server: %s", self.client.display_name)
        if myservers.is_client_exists(
            self.client.display_name, select_from_all_server=True
        ):
            myservers.retire_server(
                self.client.display_name, select_from_all_server=True
            )
        time.sleep(30)
        self.navigator.navigate_to_jobs()
        self.rtable.search_for(self.client.display_name)
        jobid = self.jobs.get_job_ids()
        if len(jobid):
            self.wait_for_job_completion(jobid[0])

        self.navigator.navigate_to_servers()
        self.refresh()
        if myservers.is_client_exists(
            self.client.display_name, select_from_all_server=True
        ):
            myservers.delete_server(
                self.client.display_name, select_from_all_server=True
            )

        self.log.info("delete plan: %s", self.planname)
        myplan = Plans(self.admin_console)
        if myplan.is_plan_exists(self.planname):
            myplan.delete_plan(self.planname)

        self.log.info("delete disk storage: %s", self.localstoragename)
        mystorage = StorageMain(self.admin_console)
        existingstorages = mystorage.list_disk_storage()
        if self.localstoragename in existingstorages:
            mystorage.delete_disk_storage(self.localstoragename)

        existingcloudstorage = mystorage.list_cloud_storage()
        if self.cloudstoragename in existingcloudstorage:
            mystorage.delete_cloud_storage(self.cloudstoragename)

        self.log.info(
            "delete write protection and disable ransomeware on gateway machine, delete disk library path"
        )
        self.gatewaymachine.modify_ace(
            "Everyone",
            self.diskpath,
            "DeleteSubdirectoriesAndFiles",
            "Deny",
            remove=True,
            folder=True,
            inheritance="2",
        )

        self.gatewaymachine.modify_ace(
            "Everyone",
            self.diskpath,
            "Delete",
            "Deny",
            remove=True,
            folder=True,
            inheritance="2",
        )

        self.media_agent_obj = self.commcell.media_agents.get(self.gatewayname)
        self.media_agent_obj.set_ransomware_protection(False)
        if self.gatewaymachine.check_directory_exists(self.diskpath):
            self.gatewaymachine.remove_directory(self.diskpath)
            self.log.info("Deleted the disk library path and cache folder")

        self.log.info("retire gateway machine")
        self.navigator.navigate_to_servers()
        if myservers.is_client_exists(self.gatewayname, select_from_all_server=True):
            myservers.retire_server(self.gatewayname, select_from_all_server=True)
        time.sleep(30)
        self.navigator.navigate_to_jobs()
        self.rtable.search_for(self.gatewayname)
        jobid = self.jobs.get_job_ids()
        if len(jobid):
            self.wait_for_job_completion(jobid[0])

        mymediaagents = MediaAgents(self.admin_console)
        self.navigator.navigate_to_media_agents(istenantadmin=True)
        if mymediaagents.is_media_agent_exists(self.gatewayname):
            mymediaagents.retire_media_agent(self.gatewayname)
        self.refresh()

        self.navigator.navigate_to_servers()
        self.refresh()
        if myservers.is_client_exists(self.gatewayname, select_from_all_server=True):
            myservers.delete_server(self.gatewayname, select_from_all_server=True)

        self.log.info("after gateway machine is retired, remove C:\IndexCache folder")
        testmachine = Machine(
            machine_name=self.tcinputs.get("GatewayFQDN"),
            username=self.tcinputs.get("GatewayUserName"),
            password=self.tcinputs.get("GatewayPassword"),
        )
        if testmachine.check_directory_exists("C:\\Metallic"):
            testmachine.remove_directory("C:\\Metallic")
        if testmachine.check_directory_exists(self.ddb_path):
            testmachine.remove_directory(self.ddb_path)

    def create_tenant(self):
        """create tenant user"""
        suffix = str(int(time.time()))
        firstname = "fs" + suffix
        lastname = "fsauto" + suffix
        self.tenantname = datetime.datetime.now().strftime("FS-Automation-%d-%B-%H-%M")
        email = "fsauto" + suffix + "@test.com"
        self.hubmgr = HubManagement(self, self.commcell.webconsole_hostname)
        self.hubmgr.create_tenant(
            self.tenantname, email, firstname, lastname, "888-888-8886"
        )
        self.tenantuser = self.tenantname + "\\" + email.split("@")[0]
        self.tenantpassword = self.config.Metallic.tenant_password
        if self.os_name.lower() == "unix":
            self.tenantencryptedpassword = (
                self.config.Metallic.tenant_encrypted_password
            )

    def setup(self):
        """Pre-requisites for this testcase"""
        self.set_client_ostype()
        self.utils.reset_temp_dir()
        self.custompkg_directory = self.utils.get_temp_dir()
        if self.os_name.lower() == "windows":
            packages = WINDOWS_CVLT_PACKAGES_ID
        else:
            packages = UNIX_CVLT_PACKAGES_ID
        self.packagelist.append(packages["File System Core"])
        self.packagelist.append(packages["File System"])

        # Not adding storage accelerator as its pushed at the end
        # self.packagelist.append(packages['Storage Accelerator'])

        self.create_tenant()
        self.planname = self.tenantname + "-fs"
        self.browser = BrowserFactory().create_browser_object()
        self.browser.set_downloads_dir(self.custompkg_directory)
        self.commcell = Commcell(
            self.commcell.webconsole_hostname, self.tenantuser, self.tenantpassword
        )
        self.log.info("%s Opening the browser %s", "*" * 8, "*" * 8)
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname
        )
        self.admin_console.login(username=self.tenantuser, password=self.tenantpassword)

    def delete_tenant(self):
        """deactivate and delete the the tenant"""
        self.hubmgr.deactivate_tenant(self.tenantname)
        self.hubmgr.delete_tenant(self.tenantname)

    def wait_for_install_job_completion(self):
        """
        Waits for the job completion of the install job
        """
        self.wait_for_job_completion(self.metallic_fs.get_push_install_jobid())
        self.admin_console.click_button('Finish')
        self.commcell.refresh()
        self.client = self.commcell.clients.get(self.tcinputs.get("MachineFQDN"))
        self.client_name = self.client.display_name
        self.client_machine = Machine(self.tcinputs["MachineFQDN"], self.commcell)

    def run(self):
        """Main function for test case execution"""
        try:
            self.hub_dashboard = Dashboard(
                self.admin_console,
                HubServices.file_system,
                app_type=FileObjectTypes.file_server,
            )
            try:
                self.admin_console.click_button("OK, got it")
            except BaseException:
                pass
            self.hub_dashboard.click_get_started()
            self.navigate_to_service_catalog()
            self.hub_dashboard.choose_service_from_dashboard()
            self.hub_dashboard.click_new_configuration()
            self.job_details = JobDetails(self.admin_console)
            self.metallic_fs = AddWizard(self.admin_console)
            self.rtable = Rtable(self.admin_console)
            self.metallic_fs.select_file_server_env(backuptocloud=False)
            self.select_backup_gateway()
            self.enable_network_gateway_role(self.gatewayname)

            #need restart from beginning after network gateway is enabled for newly installed gateway
            self.navigate_to_service_catalog()
            self.hub_dashboard.choose_service_from_dashboard()
            self.hub_dashboard.click_new_configuration()
            self.metallic_fs.select_file_server_env(backuptocloud=False)
            self.select_backup_gateway()

            self.configure_local_storage()
            self.configure_cloud_storage()
            self.configure_plan(self.planname)
            self.configure_server()
            self.define_content()
            self.wait_for_install_job_completion()
            self.client_machine.verify_installed_packages(packages=self.packagelist)
            self.verify_plan(self.planname)
            # restart service
            self.navigate_to_file_servers()
            self.file_server = FileServers(self.admin_console)
            self.file_server.restart_client_service(self.client.display_name)
            time.sleep(300)

            self.create_content()
            self.create_subclient()
            self.check_inplace_restore()
            #for install case,  one backup/restore job is enough
            #self.check_out_of_place_restore()
            #self.check_restore_by_select_items()
            self.verify_ddbpath()
            self.cleanup()
            self.delete_tenant()
        except Exception as excp:
            self.log.info("Exception occurred during execution")
            self.log.info(f"For debug purposes Tenant : {self.tenantuser}")
            handle_testcase_exception(self, excp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
