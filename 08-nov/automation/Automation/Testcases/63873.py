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
    __init__()                  --  initialize TestCase class
 
    setup()                     --  setup function of this test case
 
    run()                       --  run function of this test case
 
    initial_setup()             --  Creates tenant for this test case and completes metallic configuration
 
    create_helper_object()      -- Creates oracle helper object
 
    navigate_to_subclient()     -- Navigates to oracle subclient
 
    create_test_data()          -- Creates the test data for given test case
 
    move_to_subclient_details_from_restore() -- Moves to subclient page from restore page
 
    uninstall_client_software() --  Uninstalls the client

    active_jobs_action()        --  method to kill or wait for the active jobs of client
 
    delete_tenant()             --  Deletes the tenant created by automation
 
    validate_restore()          -- Validates data for restore
 
    run_backup()                -- Runs the backup
 
    run_restore()               -- Runs the restore
 
    wait_for_job_completion()   -- Waits for completion of job launched from command center

    upgrade_client_software()   -- Navigates to file servers page and upgrades client software
 
    cleanup()                   -- Cleanup function for test case

Create an Azure EC2 instance and install oracle database. The instance must allow ICMP and connection to port 1521.

Input Example:

    "testCases":
            {
                "62367": {
                      "HostName":"client",
                      "ClientUsername":"root",
                      "ClientPassword":"password",
                      "InstanceName":"instance",
                      "ConnectString":"username/password@servicename"

                      'RingHostname': "hostname",                   (optional, if not provided, hostname
                                                                        in input json will be used)
                      'StorageAccount': "Metallic HOT GRS Tier",    (optional)
                      'CloudProvider': "Microsoft Azure storage",   (optional)
                      'Region': "East US (Virginia)",               (optional)
                      'RetentionPeriod': "1 month",                 (optional)
                      'TestData': "[10, 20, 100]"  (eg. [No. of Datafiles, No. of Tables, No. of Rows in each table)
                                                    as list or string representation of list ie. "[10, 20, 100]"
                                                                    (optional, default:[1,1,100])
                    }
            }
 
"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from datetime import datetime
from Metallic.hubutils import HubManagement
from cvpysdk.commcell import Commcell
import ast
import time
from AutomationUtils.machine import Machine
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Hub.Databases.databases import OracleMetallic
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.constants import HubServices, DatabaseTypes
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from AutomationUtils.idautils import CommonUtils
from Database.OracleUtils.oraclehelper import OracleHelper
from Web.AdminConsole.Components.panel import Backup
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
 
            Properties to be initialized:
 
                name            (str)       --  name of this test case
 
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
 
        """
        super(TestCase, self).__init__()
        test_step = TestStep()
        self.oracle_helper_object = None
        self.name = "Oracle acceptance for Azure onboarding in metallic"
        self.commcell = None
        self.tcinputs = {
            'HostName': None,
            'ClientUsername': None,
            'ClientPassword': None,
            'InstanceName': None,
            'ConnectString': None
        }
        self.hub_mgmt = None
        self.admin_console = None
        self.backup_gateway = None
        self.browser = None
        self.config = get_config()
        self.db_instance_details = None
        self.oci_metallic_config = None
        self.hub_dashboard = None
        self.company_name = None
        self.email = None
        self.tenant_username = None
        self.database_instances = None
        self.tenant_pswrd = None
        self.subclient_page = None
        self.navigator = None
        self.instance = None
        self.client_name = None
        self.rtable = None
        self.servers_obj = None
        self.mediaagent_obj = None
        self.stack_id = None
        self.oracle_metallic_configuration = None
        self.iam_stack_id = None
        self.file_servers_obj = None
        self.tablespace_name = 'CV_63873'
        self.install_inputs = None
        self.db_helper_obj = None
        self.common_utils_obj = None
        self.service = None
        self.app_type = None
        self.infrastructure = None
        self.test_data = [1, 1, 100]
        self.tables = {"full": "CV_TABLE_", "incr": "CV_TABLE_INCR_"}
        self.table_list = []
        self.tenant_created = None
        self.database_type = None
        self.plan_name = None
        self.is_config_success = None

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Started executing %s testcase", self.id)
        ring_hostname = self.tcinputs.get("RingHostname", self.commcell.webconsole_hostname)
        self.hub_mgmt = HubManagement(self, self.commcell.webconsole_hostname)
        self.hub_mgmt.delete_companies_with_prefix(prefix='Azure-Oracle-DB-Automation')
        self.company_name = datetime.now().strftime("Azure-Oracle-DB-Automation-PI-%d-%B-%H-%M")
        self.email = datetime.now().strftime(f"metallic_azure_oracle_db_%H-%M-%S@{self.company_name}.com")
        self.tenant_username = self.hub_mgmt.create_tenant(self.company_name, self.email)
        self.tenant_pswrd = get_config().Metallic.tenant_password
        self.tenant_created = True
        self.commcell = Commcell(ring_hostname, self.tenant_username, self.tenant_pswrd)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_pswrd, stay_logged_in=True)
        self.hub_dashboard = Dashboard(self.admin_console, HubServices.database, DatabaseTypes.oracle)
        self.rtable = Rtable(self.admin_console)
        self.oracle_metallic_configuration = OracleMetallic(self.admin_console)
        self.db_helper_obj = DbHelper(self.commcell)
        self.common_utils_obj = CommonUtils(self.commcell)
        self.service = HubServices.database
        self.app_type = DatabaseTypes.oracle
        self.infrastructure = "Microsoft Azure"
        self.database_type = DBInstances.Types.ORACLE
        self.install_inputs = {}
        if self.tcinputs.get("TestData"):
            if isinstance(self.tcinputs["TestData"], str):
                self.test_data = ast.literal_eval(self.tcinputs["TestData"])
            else:
                self.test_data = self.tcinputs["TestData"]

    @test_step
    def create_helper_object(self):
        """Creates oracle helper object"""
        self.client = self.commcell.clients.get(self.client_name)
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        connect_string = self.tcinputs["ConnectString"]
        user, temp = connect_string.split('/')[0], connect_string.split('/')[1]
        passwd, service_name = temp.split('@')[0], temp.split('@')[1]
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance,
                                                 user, passwd)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA, host_name=self.tcinputs['HostName'])
        self.oracle_helper_object.check_instance_status()

    @test_step
    def navigate_to_subclient(self):
        """Navigates to subclient page"""
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.log.info("Checking if instance exists")
        self.admin_console.refresh_page()
        if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                      self.tcinputs["InstanceName"],
                                                      self.client_name):
            self.log.info("Instance found")
        else:
            raise CVTestStepFailure("Instance not found to be auto discovered")
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["InstanceName"],
                                                self.client_name)
        self.db_instance_details.edit_instance_update_credentials(
            self.tcinputs["ConnectString"])
        self.db_instance_details.click_on_entity('default')

    @test_step
    def move_to_subclient_details_from_restore(self):
        """"Moves to the subclient page"""
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.click_on_entity('default')

    def create_test_data(self, backup_level="Full"):
        """Creates test data
        Args:
            backup_level   (str): Backup level "Full" or "Incr"
        """
        self.log.info("Generating Sample Data for test")
        num_of_files, table_limit, row_limit = self.test_data
        if backup_level.lower() == "full":
            self.oracle_helper_object.create_sample_data(
                self.tablespace_name, table_limit, num_of_files, row_limit)
            self.oracle_helper_object.db_execute('alter system switch logfile')
            self.log.info("Test Data Generated successfully")
        else:
            user = "{0}_user".format(self.tablespace_name.lower())
            self.oracle_helper_object.db_create_table(
                self.tablespace_name, self.tables.get("incr"), user, table_limit, row_limit)
        tables = [f"{self.tables.get(backup_level.lower())}" + '{:02}'.format(i) for i in
                  range(1, self.test_data[1] + 1)]
        self.table_list.extend(tables)

    @test_step
    def validate_restore(self):
        """method to validate restore"""
        num_of_files, table_limit, row_limit = self.test_data
        self.log.info("Validating Backed up content")
        for test_table_prefix in self.tables.values():
            self.oracle_helper_object.validation(
                self.tablespace_name, num_of_files, test_table_prefix, row_limit, table_limit)
        self.log.info("Validation Successfull.")

    @test_step
    def run_restore(self):
        """ method to run restore"""
        self.log.info("Cleaning up tablespace and data before restore")
        self.oracle_helper_object.oracle_data_cleanup(
            tables=self.table_list, tablespace=self.tablespace_name,
            user="{0}_user".format(self.tablespace_name.lower()))

        self.log.info("Preparing for Restore.")
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = restore_panel.in_place_restore()
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )

    @test_step
    def run_backup(self, backup_level="Incr"):
        """Method to trigger backup
            Args:
                backup_level: Backup level "Full" or "Incr"
        """
        self.create_test_data(backup_level)
        if backup_level.lower() == "full":
            job_id = self.subclient_page.backup(backup_type=Backup.BackupType.FULL)
        else:
            job_id = self.subclient_page.backup(backup_type=Backup.BackupType.INCR)
        self.wait_for_job_completion(job_id)
        self.log.info("Oracle %s Backup is completed", backup_level)
        if backup_level.lower() == "full":
            self.oracle_helper_object.backup_validation(job_id, 'Online Full')
        else:
            self.oracle_helper_object.backup_validation(job_id, 'Incremental')

    @test_step
    def upgrade_client_software(self, client_name):
        """
        updates the client software
        """
        self.navigator.navigate_to_servers()
        self.admin_console.refresh_page()
        self.rtable.set_default_filter('Type', 'All')
        self.admin_console.unswitch_to_react_frame()
        job = self.servers_obj.action_update_software(client_name=client_name)
        self.db_helper_obj.wait_for_job_completion(job)
        self.log.info("Client software Upgrade successful.")

    @test_step
    def initial_setup(self):
        """ method for initial setup to perform installation,
        assign cloud storage and pick plan """
        machine = Machine(machine_name=self.tcinputs["HostName"], username=self.tcinputs["ClientUsername"],
                          password=self.tcinputs["ClientPassword"])
        cloud_storage_inputs = {"cloud_vendor": self.tcinputs.get("cloud_vendor") or "Metallic Recovery Reserve",
                                "storage_provider": self.tcinputs.get("storage_provider") or "Azure Blob Storage",
                                "region": self.tcinputs.get("region") or "East US 2"}
        self.hub_dashboard = Dashboard(self.admin_console, self.service, self.app_type)
        self.hub_dashboard.click_get_started()
        self.hub_dashboard.choose_service_from_dashboard()
        self.hub_dashboard.click_new_configuration()
        self.navigator = self.admin_console.navigator
        install_inputs = {
            "remote_clientname": self.tcinputs["HostName"],
            "remote_username": self.tcinputs["ClientUsername"],
            "remote_userpassword": self.tcinputs["ClientPassword"],
            "os_type": machine.os_info.lower(),
            "platform": machine.os_flavour,
            "username": self.tenant_username,
            "password": "3a1111972bc0091bb72079fc296201851a8ebe2f548febf1f",
        }
        self.oracle_metallic_configuration.select_cloud_vm_details(self.infrastructure, self.app_type)
        self.admin_console.click_button(value="Next")
        self.plan_name = self.oracle_metallic_configuration.configure_oracle_database(
            backup_to_cloud=False,
            select_storage_region=True,
            cloud_storage_inputs=cloud_storage_inputs,
            use_existing_plan=False,
            plan_inputs={"RetentionPeriod": self.tcinputs.get("RetentionPeriod") or "1 month"})
        pkg_file_path = self.oracle_metallic_configuration.do_pkg_download(platform="Linux")
        self.client_name = self.oracle_metallic_configuration.do_pkg_install(
            pkg_file_path, install_inputs, self.commcell)
        self.plan_name = self.company_name + '-' + self.plan_name
        self.is_config_success = True
        self.oracle_metallic_configuration.select_oracle_backup_content()
        self.oracle_metallic_configuration.proceed_from_summary_page()
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)
        self.file_servers_obj = FileServers(self.admin_console)
        self.servers_obj = Servers(self.admin_console)

    @test_step
    def uninstall_client_software(self):
        """Uninstalls the client software"""
        self.navigator.navigate_to_servers()
        self.admin_console.refresh_page()
        self.rtable.set_default_filter('Type', 'All')
        job = self.file_servers_obj.retire_server(server_name=self.client_name)
        self.db_helper_obj.wait_for_job_completion(job)
        self.log.info("Client uninstalled successfully")

    @test_step
    def delete_instance(self):
        """Deletes the oracle instance"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs['InstanceName'],
                                                self.client_name)
        self.common_utils_obj.kill_active_jobs(client_name=self.client_name)
        self.log.info("Deleting instance")
        self.db_instance_details.delete_instance()

    @test_step
    def active_jobs_action(self, action="kill"):
        """ Method to kill/wait for the active jobs running for the client
            Args:
                action  (str):  "wait" or "kill" active jobs
        """
        self.commcell.refresh()
        display_name = self.client_name
        for client in self.commcell.clients.all_clients:
            if client.startswith(self.client_name):
                display_name = client
                break
        active_jobs = self.commcell.job_controller.active_jobs(display_name)
        self.log.info("Active jobs for the client:%s", active_jobs)
        if active_jobs:
            for job in active_jobs:
                if action == "kill":
                    self.log.info("Killing Job:%s", job)
                    self.commcell.job_controller.get(job).kill(wait_for_job_to_kill=True)
                else:
                    self.log.info("Waiting for job %s to complete", job)
                    self.commcell.job_controller.get(job).wait_for_completion(timeout=5)
            self.active_jobs_action(action=action)
        else:
            self.log.info("No Active Jobs found for the client.")
        return display_name

    @test_step
    def delete_tenant(self):
        """deactivate and delete the the tenant"""
        if self.tenant_created:
            self.hub_mgmt.deactivate_tenant(self.company_name)
            self.hub_mgmt.delete_tenant(self.company_name)

    @test_step
    def cleanup(self):
        """ cleanup method """
        try:
            self.navigator.navigate_to_db_instances()
            self.database_instances.select_instance(
                DBInstances.Types.ORACLE,
                self.tcinputs['InstanceName'],
                self.tcinputs["HostName"])
            self.active_jobs_action()
            self.log.info("Deleting instance")
            self.db_instance_details.delete_instance()
            self.uninstall_client_software()
            self.delete_tenant()
            self.log.info("Deleting Automation generated Oracle data")
            self.oracle_helper_object.oracle_data_cleanup(
                tables=self.table_list, tablespace=self.tablespace_name,
                user="{0}_user".format(self.tablespace_name.lower()))
        except Exception as exp:
            self.log.info(exp)
            self.log.info("Clean up failed!! Failing testcase")
            self.status = constants.FAILED

    def tear_down(self):
        """ tear down method for testcase """
        if self.status == constants.PASSED:
            self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def run(self):
        """Run function of this test case"""
        try:
            self.initial_setup()
            display_name = self.active_jobs_action(action="wait")
            self.upgrade_client_software(display_name)
            self.navigate_to_subclient()
            self.create_helper_object()
            self.run_backup(backup_level="Full")
            self.run_backup(backup_level="Incr")
            self.run_restore()
            self.validate_restore()
            self.cleanup()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
