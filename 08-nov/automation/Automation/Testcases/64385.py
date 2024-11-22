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
        "64385": {
            "MachineFQDN": ,
            "MachineUserName": ,
            "MachinePassword": ,
            "PlanName": ,
            "TestPath": ,
            "CloudStorageName": ,
            "GatewayFQDN": ,
            "os_type": 
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
        self.name = "Metallic On-Prem File Servers onboarding for new Unix flavors - AIX, HPUX, Solaris (Interactive install)"
        self.browser = None
        self.hub_dashboard = None
        self.admin_console = None
        self.navigator = None
        self.jobs = None
        self.client_machine = None
        self.slash_format = None
        self.client = None
        self.metallic_fs = None
        self.is_hub_visible = None
        self.file_server = None
        self.client_name = None
        self.fs_sub_client = None
        self.fs_helper = None
        self.file_server_utils = None
        self.delimiter = None
        self.subclient_obj = None
        self.install_machine_obj = None
        self.plan_obj = None
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
            "PlanName": None,
            "TestPath": None,
            "CloudStorageName": None,
            "GatewayFQDN": None,
            "os_type": None
        }

    def set_installinputs(self):
        """
        Creates a dictionary for test case inputs needed for customer package install.
            Args:
                isClient (boolean):    True if machine is client machine
        """
        inputs = {}
        inputs['os_type'] = self.tcinputs.get("os_type").lower()
        if "aix" in inputs['os_type']:
            inputs["full_package_path"] = self.custompkg_directory + \
                "\\AixFileServer64.tar"
        elif "hp-ux" in inputs['os_type']:
            inputs["full_package_path"] = self.custompkg_directory + \
                "\\HpuxFileServer64.tar"
        elif "solaris" in inputs['os_type']:
            inputs["full_package_path"] = self.custompkg_directory + \
                "\\SolarisFileServer64.tar"
        elif "powerpc" in inputs['os_type']:
            inputs["full_package_path"] = self.custompkg_directory + \
                "\\PowerpcFileServer64.tar"

        inputs["remote_clientname"] = self.tcinputs.get("MachineFQDN")
        inputs["remote_username"] = self.tcinputs.get("MachineUserName")
        inputs["remote_userpassword"] = self.tcinputs.get(
            "MachinePassword")
        inputs["commcell"] = self.commcell

        return inputs

    def navigate_to_client_page(self):
        """Navigates to the client page"""
        self.navigate_to_file_servers()
        self.file_server.access_server(self.client.display_name)
        self.admin_console.access_tab("Subclients")

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
    def configure_server(self):
        """silent installs new file server"""
        install_inputs = self.set_installinputs()
        self.metallic_fs.add_new_server_silent_install(install_inputs)

    @test_step
    def configure_cloud_storage(self):
        """configure cloud storage"""

        self.metallic_fs.select_cloud_storage(storagename=self.tcinputs.get("CloudStorageName"))

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
        self.sub_client_name = "default"
        self.delimiter = "/"
        self.slash_format = "/"
        self.restore_file_path = self.tcinputs.get("TestPath") + self.delimiter + f"{self.id}_restore"

    def create_content(self):
        """Creates content in the client"""
        self.client_machine.create_directory(self.test_path, force_create=True)
        self.fs_helper.generate_testdata([".html", ".css"], self.test_path, 6)

    @test_step
    def define_content(self):
        """set subclient content, exclusions and exceptions"""
        self.init_pre_req()
        self.test_path = self.tcinputs["TestPath"] + self.delimiter + "Test" + self.id
        self.content = [self.test_path]
        self.metallic_fs.set_backup_content_filters(
            contentpaths=self.content,
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
            backupset_name="defaultBackupSet",
            subclient_name=self.sub_client_name,
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

        restore_job = self.fs_sub_client.restore_subclient(
            subclient_name=self.sub_client_name,
            backupset_name="defaultBackupSet",
            dest_client=self.client.display_name,
            destination_path=self.restore_file_path,
        )
        self.wait_for_job_completion(restore_job)
        self.browser.driver.back()
        self.admin_console.wait_for_completion()

    @test_step
    def check_out_of_place_restore(self):
        """Runs Incremental backup and out_of_place retore and validate backup"""
        ts = time.time()
        self.navigate_to_client_page()
        self.backup_job(Backup.BackupType.FULL)
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
                self.client.display_name, select_from_all_server=True, wait=False
            )
        time.sleep(30)
        self.navigator.navigate_to_jobs()
        self.rtable.search_for(self.client.display_name)
        jobid = self.jobs.get_job_ids()
        if len(jobid):
            self.wait_for_job_completion(jobid[0])

        self.file_server_utils.disable_complaince_lock(self.commcell, self.planname)

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

        self.utils.reset_temp_dir()
        self.custompkg_directory = self.utils.get_temp_dir()
        packages = UNIX_CVLT_PACKAGES_ID
        self.packagelist.append(packages["File System Core"])
        self.packagelist.append(packages["File System"])

        # Creating machine object for the install machine

        self.install_machine_obj = Machine(self.tcinputs.get("MachineFQDN"),
                                           username=self.tcinputs.get("MachineUserName"),
                                           password=self.tcinputs.get("MachinePassword"))

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

    def refresh_commcell_entities(self):
        """
        Waits for the job completion of the install job
        """
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
        """

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

            if self.fs_helper.compare_lists(subclient_obj.content, self.content):
                self.log.info("Content is corrreclty populated")
            else:
                self.log.info("Content provided while adding server: ", self.content)
                self.log.info("Content from the subclient properties: ", subclient_obj.content)
                raise Exception("Content is not populated correctly")
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
    def configure_local_storage(self):
        """configure local storage"""

        self.metallic_fs.select_local_storage(
            backup_to_cloud_storage=True
        )

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
            self.refresh_commcell_entities()
            self.client_machine.verify_installed_packages(packages=self.packagelist)
            self.init_subclient_and_plan_obj()
            self.verify_smart_defaults(self.subclient_obj, self.plan_obj)
            self.create_content()
            self.check_out_of_place_restore()
            self.cleanup()

        except Exception as excp:
            self.log.info("Exception occurred during execution")
            handle_testcase_exception(self, excp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
