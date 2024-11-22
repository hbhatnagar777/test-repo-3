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

    create_tenant()             --  Creates tenant for this test case

    create_helper_object()      -- Creates oracle helper object

    navigate_to_subclient()     -- Navigates to oracle subclient

    create_test_data()          -- Creates the test data for given test case

    move_to_subclient_details_from_restore() -- Moves to subclient page from restore page

    uninstall_client_software() --  Uninstalls the client

    delete_instance()           --  Deletes the instance

    validate_data()             -- Validates data for restore

    run_backup()                -- Runs the backup

    run_restore()               -- Runs the restore

    cleanup()                   -- Cleanup function for test case


Input Example:

        "testCases": {
                        "63380": {
                        "HostName":["<fqdn of the machine"],
                        "InstanceName":"Name of the Instance",
                        "PdbName":"Name of pluggable database",
                        "ConnectString":"user/password@servicename",
                        "ssh_key_path": "path of the private key",
                    }
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from datetime import datetime
from Metallic.hubutils import HubManagement
from cvpysdk.commcell import Commcell
import time
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.AdminConsolePages.media_agents import MediaAgents
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Hub.Databases.databases import OciMetallic
from Application.CloudApps.oci_helper import OCIHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Hub.constants import HubServices, DatabaseTypes
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from AutomationUtils.idautils import CommonUtils
from Database.OracleUtils.oraclehelper import OracleHelper
from Web.AdminConsole.Components.dialog import RBackup
from Database.dbhelper import DbHelper
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue


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
        self.name = "ACCT1 for Single DBCS"
        self.commcell = None
        self.tcinputs = {
            'HostName': None,
            'InstanceName': None,
            'PdbName': None,
            'ConnectString': None
        }
        self.hub_mgmt = None
        self.admin_console = None
        self.backup_gateway = None
        self.browser = None
        self.config = get_config()
        self.db_instance_details = None
        self.oci_metallic_config = None
        self.company_name = None
        self.email = None
        self.service_catalogue = None
        self.tenant_username = None
        self.database_instances = None
        self.tenant_password = None
        self.subclient_page = None
        self.navigator = None
        self.instance = None
        self.client_name = None
        self.rtable = None
        self.servers_obj = None
        self.mediaagent_obj = None
        self.stack_id = None
        self.oci_helper = None
        self.iam_stack_id = None
        self.file_servers_obj = None
        self.tablespace_name = 'CV_63380'
        self.install_inputs = None
        self.db_helper_obj = None
        self.common_utils_obj = None

    def setup(self):
        """Setup function of this test case"""
        self.hub_mgmt = HubManagement(self, self.commcell.webconsole_hostname)
        self.hub_mgmt.delete_companies_with_prefix(prefix='OCI-DB-Automation')
        self.create_tenant()
        self.commcell = Commcell(webconsole_hostname=self.commcell.webconsole_hostname,
                                 commcell_username=self.tenant_username,
                                 commcell_password=self.tenant_password)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_password, stay_logged_in=True)
        self.service_catalogue = ServiceCatalogue(self.admin_console, HubServices.database, DatabaseTypes.oracle)
        self.oci_metallic_config = OciMetallic(self.admin_console)
        self.service_catalogue.click_get_started()
        self.service_catalogue.choose_service_from_service_catalogue(service=HubServices.database.value,
                                                                     id=DatabaseTypes.oracle.value)
        self.navigator = self.admin_console.navigator
        self.file_servers_obj = FileServers(self.admin_console)
        self.mediaagent_obj = MediaAgents(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)
        self.servers_obj = Servers(self.admin_console)
        self.client_name = self.tcinputs["HostName"][0].split(".")[0]
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.oci_helper = OCIHelper()
        self.db_helper_obj = DbHelper(self.commcell)
        self.common_utils_obj = CommonUtils(self.commcell)
        self.install_inputs = {
            "remote_clientname": self.tcinputs["HostName"][0],
            "remote_username": "opc",
            "ssh_key_path": self.tcinputs["ssh_key_path"]
        }

    @test_step
    def create_tenant(self):
        """create tenant user"""
        self.company_name = datetime.now().strftime("OCI-DB-Automation-PI-%d-%B-%H-%M")
        self.email = datetime.now().strftime(f"metallic_oci_db_%H-%M-%S@{self.company_name}.com")
        self.tenant_username = self.hub_mgmt.create_tenant(company_name=self.company_name,
                                                           email=self.email)
        self.tenant_password = self.config.Metallic.tenant_password

    @test_step
    def create_helper_object(self):
        """Creates oracle helper object"""
        self.client = self.commcell.clients.get(self.tcinputs["HostName"][0])
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        connect_string = self.tcinputs["ConnectString"]
        user, temp = connect_string.split('/')[0], connect_string.split('/')[1]
        passwd, service_name = temp.split('@')[0], temp.split('@')[1]
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance,
                                                 user, passwd)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def navigate_to_subclient(self):
        """Navigates to subclient page"""
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.log.info("Waiting for the instance to be auto discovered")
        time.sleep(120)
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

    @test_step
    def create_test_data(self, backup_level):
        """Creates the test data
           Args:
               backup_level   (str)   :  Backup level Full or Incr
        """
        df_location = self.oracle_helper_object.db_fetch_dbf_location()
        if backup_level.lower() == "incr":
            self.oracle_helper_object.db_connect_to_pdb(pdb_name=self.tcinputs["PdbName"])
            self.oracle_helper_object.db_populate_table(tblpref="CV_TABLE_", user="SYS")
        else:
            self.oracle_helper_object.db_connect_to_pdb(pdb_name=self.tcinputs["PdbName"])
            self.oracle_helper_object.db_create_tablespace(tablespace_name=self.tablespace_name,
                                                           location=df_location, num_files=1)
            self.oracle_helper_object.db_create_table(tablespace_name=self.tablespace_name,
                                                      table_prefix="CV_TABLE_", user="SYS",
                                                      number=1)

    @test_step
    def validate_data(self, row_limit):
        """Validates the data for the restore

           Args:
               row_limit   (int)   : Number of rows
        """
        self.log.info("Validating data")
        self.oracle_helper_object.db_connect_to_pdb(pdb_name=self.tcinputs["PdbName"])
        tablerecords = self.oracle_helper_object.db_table_validate(user="SYS", tablename="CV_TABLE_01")
        if tablerecords != row_limit:
            raise CVTestStepFailure("Validation failed")
        self.log.info("Validation Successful")

    @test_step
    def run_restore(self):
        """ method to run restore"""
        self.log.info("Preparing for Restore.")
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        self.admin_console.wait_for_completion(2000)
        restore_panel = self.db_instance_details.restore_folders(
            database_type=DBInstances.Types.ORACLE, all_files=True)
        self.admin_console.wait_for_completion(2000)
        job_id = restore_panel.in_place_restore()
        self.db_helper_obj.wait_for_job_completion(job_id)
        self.log.info("Restore completed")

    @test_step
    def run_backup(self, backup_level="Incr"):
        """Method to trigger backup
            Args:
                backup_level: Backup level "Full" or "Incr"
        """
        self.create_test_data(backup_level)
        if backup_level.lower() == "full":
            job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        else:
            job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.INCR)
        self.db_helper_obj.wait_for_active_jobs(job_filter="Backup", client_name=self.client_name)
        self.log.info("Oracle %s Backup is completed", backup_level)

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
    def oci_initial_setup(self):
        """configures and updates the client and backupgateway"""
        self.oci_metallic_config.configure(self.install_inputs)
        time.sleep(90)
        self.db_helper_obj.wait_for_active_jobs(job_filter="INSTALLCLIENT")
        self.upgrade_client_software(client_name=self.oci_metallic_config.backup_gateway)

    @test_step
    def uninstall_client_software(self, client_name):
        """Uninstalls the client software
           Args:
               client   (str)   : Name of the client
        """
        self.navigator.navigate_to_servers()
        self.admin_console.refresh_page()
        self.rtable.set_default_filter('Type', 'All')
        job = self.file_servers_obj.retire_server(server_name=client_name)
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
    def cleanup(self):
        """Method for the cleanup"""
        try:
            self.common_utils_obj.kill_active_jobs(client_name=self.client_name)
            self.delete_instance()
            self.uninstall_client_software(client_name=self.client_name)
            self.navigator.navigate_to_media_agents(istenantadmin=True)
            self.mediaagent_obj.retire_media_agent(media_agent=self.oci_metallic_config.backup_gateway)
            self.log.info("Waiting for media agent to retire")
            time.sleep(90)
            self.uninstall_client_software(client_name=self.oci_metallic_config.backup_gateway)
            self.oci_helper.run_destroy_job_on_stack(self.oci_metallic_config.gateway_stack_id)
            self.oci_helper.delete_stack(self.oci_metallic_config.gateway_stack_id)
            self.oci_helper.run_destroy_job_on_stack(self.oci_metallic_config.iam_stack_id)
            self.oci_helper.delete_stack(self.oci_metallic_config.iam_stack_id)
            self.oci_helper.set_db_state(action="stop")
        except Exception as exp:
            self.log.info(exp)
            self.log.info("Clean up failed. Passing testcase")
            self.status = constants.PASSED

    def run(self):
        """Run function of this test case"""
        try:
            self.oci_initial_setup()
            self.db_helper_obj.wait_for_active_jobs(job_filter="Backup", client_name=self.client_name)
            self.navigate_to_subclient()
            self.create_helper_object()
            self.run_backup(backup_level="full")
            self.run_restore()
            self.validate_data(row_limit=10)
            self.move_to_subclient_details_from_restore()
            self.run_backup(backup_level="incr")
            self.run_restore()
            self.validate_data(row_limit=20)
            self.cleanup()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
