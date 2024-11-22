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
    "64384": {
        "MachineFQDN": "",
        "MachineUserName": "",
        "MachinePassword": "",
        "GatewayFQDN": "",
        "LocalStorageName": "",
        "CloudStorageName": "",
        "PlanName": "",
        "TestPath": "",
        "OS_TYPE": ""
    }
}
"""

import time
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.config import get_config
from FileSystem.FSUtils.fshelper import FSHelper
from Reports.utils import TestCaseUtils
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.constants import HubServices, FileObjectTypes
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers, AddWizard
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from AutomationUtils.constants import UNIX_CVLT_PACKAGES_ID


class TestCase(CVTestCase):
    """
    Class for executing test case for FS acceptance on Hub
    """

    test_step = TestStep()

    def __init__(self):
        """Initializing the reference variables"""
        super(TestCase, self).__init__()
        self.name = "Metallic On-Prem File Servers onboarding for new Unix flavors - AIX, HPUX, Solaris (Push install)"
        self.browser = None
        self.hub_dashboard = None
        self.admin_console = None
        self.navigator = None
        self.jobs = None
        self.client_machine = None
        self.client = None
        self.metallic_fs = None
        self.file_server_utils = None
        self.is_hub_visible = None
        self.file_server = None
        self.client_name = None
        self.fs_sub_client = None
        self.fs_helper = None
        self.os_name = None
        self.delimiter = None
        self.subclient_obj = None
        self.plan_obj = None
        self.slash_format = None
        self.restore_file_path = ""
        self.sub_client_name = None
        self.content = []
        self.exclusions = []
        self.exceptions = []
        self.packagelist = []
        self.custompkg_directory = None
        self.utils = TestCaseUtils(self)
        self.config = get_config()
        self.planname = None
        self.tcinputs = {
            "MachineFQDN": None,
            "MachineUserName": None,
            "MachinePassword": None,
            "GatewayFQDN": None,
            "LocalStorageName": None,
            "PlanName": None,
            "TestPath": None,
            "OS_TYPE": None
        }

    def navigate_to_client_page(self):
        """Navigates to the client page"""
        self.navigate_to_file_servers()
        self.file_server.access_server(self.client.display_name)
        self.admin_console.access_tab("Subclients")
        self.admin_console.wait_for_completion()

    def navigate_to_file_servers(self):
        """Navigates to file server page"""
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")

    def refresh(self, wait_time=30):
        """Refreshes the current page"""
        self.log.info("%s Refreshes browser %s", "*" * 8, "*" * 8)
        time.sleep(wait_time)
        self.admin_console.refresh_page()

    @test_step
    def select_backup_gateway(self):
        """configure backup gateway"""
        if not self.commcell.clients.has_client(self.tcinputs.get("GatewayFQDN")):
            raise Exception("Provided gateway does not exist. Please provide an existing gateway")

        self.commcell.refresh()
        self.gateway = self.commcell.clients.get(self.tcinputs.get("GatewayFQDN"))
        self.gatewayname = self.gateway.display_name
        self.gatewayname_on_dropdown = self.gateway.display_name + " (" + self.gateway.client_hostname + ")"
        self.metallic_fs.select_backup_gatway(self.gatewayname_on_dropdown)
        self.gatewaymachine = Machine(self.gateway)

    @test_step
    def configure_server(self):
        """push install new file servers"""
        self.admin_console.select_radio(id="PUSH")
        self.metallic_fs.push_add_new_server(self.tcinputs)

    @test_step
    def configure_local_storage(self):
        """configure local storage"""
        self.localstoragename = self.tcinputs.get("LocalStorageName")

        if not self.metallic_fs.check_if_localstorage_exist(self.localstoragename):
            raise Exception("Please provide an existing local storage")

        self.metallic_fs.select_local_storage(
            self.localstoragename,
            self.gatewayname
        )

    @test_step
    def configure_cloud_storage(self):
        """configure cloud storage"""

        self.metallic_fs.select_cloud_storage(
            use_only_on_premise_storage=True
        )

    @test_step
    def configure_plan(self, planname):
        """configure and select plan
        Args:
            planname (str)    :    plan name
        """
        self.metallic_fs.select_plan(planname)

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

        self.file_server = FileServers(self.admin_console)
        self.fs_helper = FSHelper(self)
        self.jobs = Jobs(self.admin_console)
        self.fs_sub_client = Subclient(self.admin_console)
        self.file_server_utils = FileServersUtils(self.admin_console)
        self.sub_client_name = f"Test_{self.id}"
        self.delimiter = "/"
        self.restore_file_path = self.tcinputs.get("TestPath") + self.delimiter + f"{self.id}_restore"
        self.slash_format = "/"

    def create_content(self):
        """Creates content in the client"""
        self.client_machine.create_directory(self.test_path, force_create=True)
        self.fs_helper.generate_testdata([".html", ".css"], self.test_path, 6)

    def create_subclient(self):
        """Creates new subclient
        Raises:
            Exception:
                -- if fails to add entity
        """

        self.navigate_to_client_page()
        self.fs_sub_client.add_subclient(
            subclient_name=self.sub_client_name,
            backupset_name="defaultBackupSet",
            plan_name=self.planname,
            define_own_content=True,
            contentpaths=self.content,
            remove_plan_content=False
        )

    @test_step
    def define_content(self):
        """set subclient content, exclusions and exceptions"""
        self.init_pre_req()
        self.test_path = self.tcinputs["TestPath"] + self.delimiter + "Test" + self.id
        self.content = [self.test_path]
        self.metallic_fs.set_backup_content_filters(
            contentpaths=[],
            contentfilters=[],
            contentexceptions=[]
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
            hash_list.append(self.client_machine.get_checksum_list(path))
        return hash_list

    def backup_job(self, backup_type):
        """Function to run a backup job
        Args:
            backup_type (BackupType) : Type of backup (FULL, INCR, DIFFERENTIAL, SYN_FULL)
        Raises:
            Exception :
            -- if fails to run the backup
        """
        self.navigate_to_client_page()
        self.log.info(
            "%s Starts Backup job %s for subclient %s", backup_type, "*" * 8, "*" * 8
        )
        job = self.fs_sub_client.backup_subclient(
            self.sub_client_name,
            backup_type,
            "defaultBackupSet"
        )
        self.wait_for_job_completion(job)
        return job

    def restore_in_place(self):
        """Restores the subclient
        Raises:
            Exception :
            -- if fails to run the restore operation
        """
        self.log.info("%s Starts inplace restore for subclient %s", "*" * 8, "*" * 8)
        self.navigate_to_client_page()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            subclient_name=self.sub_client_name,
            backupset_name="defaultBackupSet",
            dest_client=self.client.display_name,
            unconditional_overwrite=True,
        )
        self.wait_for_job_completion(restore_job)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()

    def validate_restore(self, content_paths, content_hash_values):
        """Validates backup files are backedup or not
        Args:
            content_paths   list(paths): list of paths that are restored
            content_hash_values     list(hash_values): list of hash_values before restore
        """
        self.log.info("%s Validates inplace restore %s", "*" * 8, "*" * 8)
        restore_hash = self.get_content_hash(content_paths)
        if self.fs_helper.compare_lists(restore_hash, content_hash_values):
            self.log.info("Checksum comparision successfull")
        else:
            raise Exception("Checksum comparision failed")

    def restore_out_of_place(self):
        """Restores the subclient
        Raises:
            Exception :
            -- if fails to run the restore operation
        """
        self.log.info(
            "%s Starts out_of_place restore for subclient %s", "*" * 8, "*" * 8
        )

        self.client_machine.create_directory(self.restore_file_path, True)
        self.navigate_to_client_page()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            subclient_name=self.sub_client_name,
            backupset_name="defaultBackupSet",
            dest_client=self.client.display_name,
            destination_path=self.restore_file_path,
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

        self.client_machine.create_directory(self.restore_file_path, True)
        self.navigate_to_client_page()
        self.refresh()
        restore_job = self.fs_sub_client.restore_subclient(
            backupset_name="defaultBackupSet",
            subclient_name=self.sub_client_name,
            selected_files=select_files,
            dest_client=self.client.display_name,
            destination_path=self.restore_file_path
        )
        self.wait_for_job_completion(restore_job)
        self.navigate_to_client_page()

    def check_any_backup_runs(self):
        """Backup is initiated if there are no active job on subclient"""
        self.log.info("%s Runs Full Backup %s", "*" * 8, "*" * 8)
        
        job_id = self.backup_job(Backup.BackupType.INCR)
        
        self.wait_for_job_completion(job_id)
        return job_id

    @test_step
    def check_inplace_restore(self):
        """Runs full backup and restore to validate inplace restore"""
        self.check_any_backup_runs()
        self.refresh()
        source_hash = self.get_content_hash(self.content)
        self.restore_in_place()
        self.validate_restore([self.content], source_hash)

    @test_step
    def check_out_of_place_restore(self):
        """Runs Incremental backup and out_of_place retore and validate backup"""
        ts = time.time()
        self.client_machine.create_file(
            self.test_path + self.delimiter + "newfile1" + str(ts) + ".html",
            "New file is created after first incremental backup",
        )
        source_hash = self.get_content_hash(self.content)
        self.backup_job(Backup.BackupType.INCR)
        self.refresh()
        self.restore_out_of_place()
        restore_path = self.client_machine.join_path(self.restore_file_path, self.test_path[1:])
        self.validate_restore([restore_path], source_hash)

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
        self.os_name = "Unix"

    @test_step
    def cleanup(self):
        """Cleanup test gateway and test clients"""

        if self.client_machine.check_directory_exists(self.test_path):
            self.client_machine.remove_directory(self.test_path)

        if self.client_machine.check_directory_exists(self.restore_file_path):
            self.client_machine.remove_directory(self.restore_file_path)

        myservers = Servers(self.admin_console)
        self.navigator.navigate_to_servers()

        self.log.info("retire and delete file server: %s", self.client.display_name)
        if myservers.is_client_exists(
                self.client.display_name, select_from_all_server=True
        ):
            myservers.retire_server(
                self.client.display_name, select_from_all_server=True,  wait=False
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

        self.refresh()
        if not myservers.is_client_exists(
                self.client.display_name, select_from_all_server=True
        ):
            self.log.info("Client is deleted successfully.")
        else:
            raise Exception("Client is present in the table post deletion")

    def setup(self):
        """Pre-requisites for this testcase"""

        self.planname = self.tcinputs.get("PlanName")

        self.set_client_ostype()
        self.utils.reset_temp_dir()
        self.custompkg_directory = self.utils.get_temp_dir()
        packages = UNIX_CVLT_PACKAGES_ID
        self.packagelist.append(packages["File System Core"])
        self.packagelist.append(packages["File System"])

        # Not adding storage accelerator as its pushed at the end
        # self.packagelist.append(packages['Storage Accelerator'])

        self.browser = BrowserFactory().create_browser_object()
        self.browser.set_downloads_dir(self.custompkg_directory)
        self.commcell = Commcell(
            self.commcell.webconsole_hostname, self.config.ADMIN_USERNAME, self.config.ADMIN_PASSWORD
        )
        self.log.info("%s Opening the browser %s", "*" * 8, "*" * 8)
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname
        )
        self.admin_console.login(username=self.config.ADMIN_USERNAME,
                                 password=self.config.ADMIN_PASSWORD)

    def wait_for_install_job_completion(self):
        """
        Waits for the job completion of the install job
        """
        self.metallic_fs.open_push_install_job_and_wait_for_completion(timeout=56)
        self.commcell.refresh()
        self.client = self.commcell.clients.get(self.tcinputs.get("MachineFQDN"))
        self.client_name = self.client.display_name
        self.client_machine = Machine(self.tcinputs["MachineFQDN"], self.commcell)

    def init_subclient_and_plan_obj(self):
        """
        Initiates subclient and plan object
        """

        agent_obj = self.client.agents.get('file system')
        agent_obj.backupsets.refresh()
        backupset_obj = agent_obj.backupsets.get("defaultBackupSet")
        backupset_obj.subclients.refresh()
        self.subclient_obj = backupset_obj.subclients.get("default")

        self.commcell.plans.refresh()
        self.plan_obj = self.commcell.plans.get(self.planname)

    @test_step
    def verify_smart_defaults(self, subclient_obj, plan_obj):
        """
        Verifies Smart defaults

        For a push installed client: We should only have iDataAgent

        Args:
            client_id: Id of the client to execute query
            subclien_obj: Subclient object
            plan_obj: Plan object
            verfiy_ida_fom_db: (bool) To check only one iDataAgent is present for a push installed Client.
        """

        # if verfiy_ida_from_db:
        #     query = f"select * from APP_IDAName with(NOLOCK) where clientid={client_id}"
        #     self.log.info(f"Executing query: {query}")
        #     self.csdb.execute(query)
        #     query_result = self.csdb.fetch_all_rows()
        #     self.log.info(f"Query output: {query_result}")

        #     if len(query_result) != 1:
        #         raise Exception("Client has more than one iDataAgent for a push installed client. It should only have one")
        #     else:
        #         self.log.info("Push installed client has only one iDataAgent")

        plan_obj.refresh()

        plan_props = plan_obj.properties

        idaType = 2

        self.log.info("Checking the subclient properties")

        # Using mulitple if statements to check if any one property is incorrect

        subclient_obj.refresh()

        # Using local var to reduce mutliple requests
        subclient_props = subclient_obj.properties

        # Common properties for Windows and Unix

        if subclient_props["fsSubClientProp"]["followMountPointsMode"] == 1:
            self.log.info("Follow mount points is enabled")
        else:
            raise Exception("Follow mount points is not enabled")

        if subclient_props["fsSubClientProp"]["useGlobalFilters"] == 0:
            self.log.info("Use Cell level Policy is turned off by default")
        else:
            raise Exception("Use Cell level Policy is not turned off by default")

        if subclient_props["fsSubClientProp"]["isTrueUpOptionEnabledForFS"]:
            self.log.info("TrueUp Option is enabled")
        else:
            raise Exception("TrueUp is not enabled")

        if subclient_props["fsSubClientProp"]["runTrueUpJobAfterDaysForFS"] == 30:
            self.log.info("TrueUp days is set to 30")
        else:
            raise Exception(
                f'TrueUp days is set to {subclient_props["fsSubClientProp"]["runTrueUpJobAfterDaysForFS"]} \
                this should be 30 by default')

        if subclient_props["commonProperties"]["numberOfBackupStreams"] == 0:
            self.log.info("Optimal data readers are set")
        else:
            raise Exception("Optimal Data Readers are not set")

        if subclient_props["commonProperties"]["allowMultipleDataReaders"]:
            self.log.info("Allow multiple readers is set to True")
        else:
            raise Exception("Multiple data readers are not set")

        if subclient_props["commonProperties"]["firstBackupTime"] == 0:
            self.log.info("First backup time is set to 0")
        else:
            raise Exception(f"First backup time is set to {subclient_props['commonProperties']['firstBackupTime']} \
                            it should be 0 by default")

        if subclient_props["commonProperties"]["lastBackupTime"] == 0:
            self.log.info("First backup time is set to 0")
        else:
            raise Exception(f"Last backup time is set to {subclient_props['commonProperties']['lastBackupTime']} \
                            it should be 0 by default")

        # OS related subclient properties

        if "windows" in self.client.os_info.lower():

            if subclient_props["fsSubClientProp"]["scanOption"] == 2:
                self.log.info("Scan Option is set to Optimized for Windows")
            else:
                raise Exception("Scan Option is not set to Optimized for Windows")

            if subclient_props["fsSubClientProp"]["useVSS"]:
                self.log.info("VSS is enabled")
            else:
                raise Exception("VSS is not enabled by default")

        else:

            idaType = 3

            if subclient_props["fsSubClientProp"]["scanOption"] == 1:
                self.log.info("Scan Option is set to Recursive for Unix")
            else:
                raise Exception("Scan Option is not Recusive for Unix")

            if subclient_props["fsSubClientProp"]["unixMtime"]:
                self.log.info("Unix Mtime is set")
            else:
                raise Exception("Unix Mtime is not set")

            if subclient_props["fsSubClientProp"]["unixCtime"]:
                self.log.info("Unix Ctime is set")
            else:
                raise Exception("Unix Ctime is not set")

        # Properties associated with plan

        if subclient_props["useLocalContent"]:
            self.log.info("Plan content is overriden")
        else:
            subclient_content = subclient_props['content']
            all_ida_contents = plan_props["laptop"]["content"]["backupContent"]

            for ida_contents in all_ida_contents:

                if ida_contents['idatype'] == idaType:

                    plan_content = ida_contents["subClientPolicy"]["subClientList"][0]['content']

                    if subclient_content == plan_content:
                        self.log.info("Subclient content and Plan content are same")
                    else:
                        self.log.info("Subclient Content: " + subclient_content)
                        self.log.info("Plan content: " + plan_content)
                        raise Exception("Subclient content and plan content differ")

                    if idaType == 2:

                        if subclient_props["subClientEntity"]["subclientName"] == "default":

                            plan_system_state = ida_contents["subClientPolicy"]["subClientList"][0]['fsSubClientProp'][
                                'backupSystemState']
                            subclient_system_state = subclient_props["fsSubClientProp"]["backupSystemState"]

                            if plan_system_state == subclient_system_state:
                                self.log.info("System state option for Windows is honoured with Plan")
                            else:
                                self.log.info(f"Plan System State option for Windows: {plan_system_state}")
                                self.log.info(f"Subclient System State option: {subclient_system_state}")
                                raise Exception(
                                    "Plan System State and Subclient System state does not match for Windows")

                        else:

                            self.log.info("Not default subclient, skipping backup system state check")

        self.log.info("Successfully verfied the subclient properties")

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

            self.admin_console.navigator.navigate_to_service_catalogue()
            self.admin_console.wait_for_completion()

            self.hub_dashboard.click_get_started()
            self.hub_dashboard.choose_service_from_dashboard()
            self.hub_dashboard.click_new_configuration()

            self.job_details = JobDetails(self.admin_console)
            self.metallic_fs = AddWizard(self.admin_console)
            self.rtable = Rtable(self.admin_console)

            self.metallic_fs.select_file_server_env(physical=True, backuptocloud=False)
            self.select_backup_gateway()
            self.configure_local_storage()
            self.configure_cloud_storage()
            self.configure_plan(self.planname)
            self.configure_server()
            self.define_content()
            self.wait_for_install_job_completion()
            self.client_machine.verify_installed_packages(packages=self.packagelist)
            self.init_subclient_and_plan_obj()
            self.verify_smart_defaults(self.subclient_obj, self.plan_obj)
            self.create_content()
            self.create_subclient()
            self.check_inplace_restore()
            self.check_out_of_place_restore()
            self.check_restore_by_select_items()
            self.cleanup()

        except Exception as excp:
            self.log.info("Exception occurred during execution")
            handle_testcase_exception(self, excp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
