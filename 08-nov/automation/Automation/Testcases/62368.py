# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    tear_down()                 --  tear down method for testcase

    wait_for_job_completion()   --  waits for completion of job

    navigate_to_instance()      --  navigates to specified instance

    add_instance()              --  creates a new instance of specified type
                                    with specified name and details

    edit_rac_instance()         --  Edits rac instance properties

    create_helper_object()      --  creates object of OracleHelper class

    run_restore()               --  method to run restore and validate test data

    delete_tenant()             --  method to deactivate and delete the tenant

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
        {
            "62368":
                {
                    "RingHostname" : "hostname",                   (optional, if not provided, hostname
                                                                   in input json will be used)
                    "StorageAccount" : "Metallic Recovery Reserve", (optional)
                    "CloudProvider" : "Microsoft Azure Storage", (optional)
                    "RacNodeHostname1" : "Host name of first node",
                    "RacNodeHost1Username" : "User name of first node",
                    "RacNode1Password" : "Password of first node" ,
                    "RacNodeHostName2" : "Hostname of second node",
                    "RacNodeHost2Username" : "User name of second node",
                    "RacNode2Password" : "Password of the second node",
                    "RacInstanceName": "name of the instance",
                    "RacClusterName": "name of the cluster",
                        (optional, if instance is not already present)
                    "RacServers" : "Name of the Rac Servers",
                    "RacInstance" : "Name of Rac instance",
                    "Connect Password" : "Password for instance",
                    "OracleHomeDir" : "Oracle Home directory path for nodes",
                    "PdbName" : "Name of pdb to generate test data",
                    "RacNodes": [{
                        "RacInstance": "name of the node instance",
                        "RacServer": "display name of rac server node",
                        "ConnectUsername": "username for connect string",
                        "ConnectPassword": "password for connect string",
                        "OracleHomeDir": "location of oracle home dir"
                    },{
                        "RacInstance": "name of the node instance",
                        "RacServer": "display name of rac server node",
                        "ConnectUsername": "username for connect string",
                        "ConnectPassword": "password for connect string",
                        "OracleHomeDir": "location of oracle home dir"
                    }]

                }
        }


"""
import ast
import json
from datetime import datetime
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from Database.OracleUtils.oraclehelper import OracleRACHelper
from Metallic.hubutils import HubManagement
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails, OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Hub.Databases.databases import OracleMetallic
from Web.AdminConsole.Hub.constants import HubServices, DatabaseTypes
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.AdminConsole.Components.wizard import Wizard
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for oracle rac """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "ACCT1-Acceptance test for Oracle RAC on Metallic"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_62368'
        self.database_type = None
        self.hub_dashboard = None
        self.service = None
        self.app_type = None
        self.tcinputs = {
            'RingHostname': None,
            'StorageAccount': None,
            'CloudProvider': None,
            'Region': None,
            'RacNodeHostName1': None,
            'RacNodeHost1Username': None,
            'RacNode1Password': None,
            'RacNodeHostName2': None,
            'RacNodeHost2Username': None,
            'RacNode2Password': None,
            'RacInstanceName': None,
            'RacClusterName': None,
            'RacNodes': None,
            'RacInstance': None,
            'ConnectUsername': None,
            'ConnectPassword': None,
            'RacServers': None,
            'OracleHomeDir': None
            }
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.automation_instance = None
        self.oracle_metallic_configuration = None
        self.company_name = None
        self.email = None
        self.tenant_username = None
        self.tenant_pswrd = None
        self.plan_name = None
        self.wizard = None
        self.tenant_mgmt = None
        self.admin_user_commcell = None
        self.is_config_success = False


    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        ring_hostname = self.tcinputs.get("RingHostname", self.commcell.webconsole_hostname)
        self.service = HubServices.database
        self.tenant_mgmt = HubManagement(self, ring_hostname)
        self.infrastructure = "Virtual machine"
        self.app_type = DatabaseTypes.ORACLE_RAC
        self.company_name = datetime.now().strftime("62368-Automation-%d-%B-%H-%M")
        self.email = datetime.now().strftime(f"metallic_oracle_db_%H-%M-%S@{self.company_name}.com")
        self.tenant_username = self.tenant_mgmt.create_tenant(self.company_name, self.email)
        self.tenant_pswrd = get_config().Metallic.tenant_password
        self.tenant_created = True
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(self.tenant_username,self.tenant_pswrd,stay_logged_in=True)
        self.wizard = Wizard(self.admin_console)
        self.database_type = DBInstances.Types.ORACLE_RAC
        self.oracle_metallic_configuration = OracleMetallic(self.admin_console)
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        self.commcell = Commcell(ring_hostname,
                                 self.tenant_username,
                                 self.tenant_pswrd)
        self.adminusername = self.tcinputs["commcellUsername"]
        self.adminPassword = self.tcinputs["commcellPassword"]
        self.admin_user_commcell = Commcell(ring_hostname,self.adminusername,self.adminPassword)
        if self.tcinputs.get("RacInstance"):
            if isinstance(self.tcinputs["RacInstance"], str):
                self.racInstance = ast.literal_eval(self.tcinputs["RacInstance"])
            else:
                self.racInstance = self.tcinputs["RacInstance"]
        if self.tcinputs.get("RacServers"):
            if isinstance(self.tcinputs["RacServers"], str):
                self.racServers = ast.literal_eval(self.tcinputs["RacServers"])
            else:
                self.racServers = self.tcinputs["RacServers"]
        if self.tcinputs.get("ConnectUsername"):
            if isinstance(self.tcinputs["ConnectUsername"], str):
                self.connectUsername = ast.literal_eval(self.tcinputs["ConnectUsername"])
            else:
                self.connectUsername = self.tcinputs["ConnectUsername"]
        if self.tcinputs.get("ConnectPassword"):
            if isinstance(self.tcinputs["ConnectPassword"], str):
                self.connectPassword = ast.literal_eval(self.tcinputs["ConnectPassword"])
            else:
                self.connectPassword = self.tcinputs["ConnectPassword"]

    def tear_down(self):
        """ tear down method for testcase """
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    @test_step
    def initial_setup(self):
        """ method for initial setup to perform installation,
        assign cloud storage and pick plan """

        node_one_machine = Machine(machine_name=self.tcinputs["RacNodeHostName1"],
                                   username=self.tcinputs["RacNodeHost1Username"],
                                   password=self.tcinputs["RacNode1Password"])
        node_two_machine = Machine(machine_name=self.tcinputs["RacNodeHostName2"],
                                   username=self.tcinputs["RacNodeHost2Username"],
                                   password=self.tcinputs["RacNode2Password"])

        node_one_cloud_storage_inputs = {
                                "cloud_vendor": self.tcinputs.get("cloud_vendor") or "Air Gap Protect",
                                "storage_provider": self.tcinputs.get("storage_provider") or "Azure Blob Storage",
                                "region": self.tcinputs.get("region") or "East US 2"}

        self.service_catalogue.click_get_started()
        self.service_catalogue.choose_service_from_service_catalogue(service=self.service.value,
                                                                     id=DatabaseTypes.oracle.value)


        node_one_install_inputs = [
                                   {"remote_clientname": self.tcinputs["RacNodeHostName1"],
                                    "remote_username": self.tcinputs["RacNodeHost1Username"],
                                    "remote_userpassword": self.tcinputs["RacNode1Password"],
                                    "os_type": node_one_machine.os_info.lower(),
                                    "platform": node_one_machine.os_flavour,
                                    "username": self.tenant_username,
                                    "password": "3a1111972bc0091bb72079fc296201851a8ebe2f548febf1f"},
                                    {"remote_clientname": self.tcinputs["RacNodeHostName2"],
                                    "remote_username": self.tcinputs["RacNodeHost2Username"],
                                    "remote_userpassword": self.tcinputs["RacNode2Password"],
                                    "os_type": node_two_machine.os_info.lower(),
                                    "platform": node_one_machine.os_flavour,
                                    "username": self.tenant_username,
                                    "password": "3a1111972bc0091bb72079fc296201851a8ebe2f548febf1f"},
                                   {"remote_clientname": self.tcinputs["RacNodeHostName3"],
                                    "remote_username": self.tcinputs["RacNodeHost3Username"],
                                    "remote_userpassword": self.tcinputs["RacNode3Password"],
                                    "os_type": node_two_machine.os_info.lower(),
                                    "platform": node_one_machine.os_flavour,
                                    "username": self.tenant_username,
                                    "password": "3a1111972bc0091bb72079fc296201851a8ebe2f548febf1f"}
                                   ]

        self.oracle_metallic_configuration.select_on_prem_details(self.infrastructure, self.app_type)
        self.plan_name= self.oracle_metallic_configuration.configure_oracle_database(
            cloud_storage_inputs=node_one_cloud_storage_inputs,
            use_existing_plan=False,
            plan_inputs={"RetentionPeriod": self.tcinputs.get("RetentionPeriod") or "1 month"})

        pkg_file_path = self.oracle_metallic_configuration.do_pkg_download(platform="Linux")

        self.oracle_metallic_configuration.do_pkg_install(pkg_file_path=pkg_file_path,
                                                          install_inputs=node_one_install_inputs,commcell=self.commcell)
        self.is_config_success = True
        self.oracle_metallic_configuration.select_oracle_backup_content()
        self.oracle_metallic_configuration.proceed_from_summary_page()
        self.servers = Servers(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion(timeout=180):
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )

    @test_step
    def add_instance(self):
        """Adds new instance"""
        required_inputs = [
            "RacInstance",
            "RacServer",
            "ConnectUsername",
            "ConnectPassword",
            "OracleHomeDir",
        ]
        input_nodes = self.tcinputs.get("RacNodes")
        rac_nodes = json.loads(input_nodes) if isinstance(input_nodes, str) else input_nodes
        if not all(key in node for key in required_inputs for node in rac_nodes):
            raise CVTestStepFailure("Provide {0} for each node".format(", ".join(required_inputs)))

        self.log.info("Trying to create new instance with the provided inputs")
        self.database_instances.add_oracle_rac_instance(rac_instance_name=self.tcinputs["RacInstanceName"],
                                                        rac_cluster_name=self.tcinputs["RacClusterName"],
                                                        rac_nodes=rac_nodes,
                                                        plan=self.plan_name)
        self.automation_instance = True

        self.log.info("Selecting the newly created instance")
        self.database_instances.select_instance(DBInstances.Types.ORACLE_RAC,
                                                self.tcinputs["RacInstanceName"],
                                                self.tcinputs["RacClusterName"])

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.ORACLE_RAC,
                                                self.tcinputs["RacInstanceName"],
                                                self.tcinputs["RacClusterName"])

    @test_step
    def navigate_to_instance_details(self):
        "Navigates to Instance Details Page"
        self.log.info("Navigating to DB Instances page")
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.log.info("Checking if instance exists")
        if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE_RAC,
                                                      self.tcinputs["RacInstanceName"],
                                                      self.tcinputs["RacClusterName"]):
            self.log.info("Instance found")
            self.navigate_to_instance()
        else:
            self.log.info("Instance not found. Creating new instance")
            self.add_instance()
            self.log.info("Instance successfully created")

    @test_step
    def active_jobs_action(self, action="kill"):
        """ Method to kill/wait for the active jobs running for the client
            Args:
                action  (str):  "wait" or "kill" active jobs
        """
        self.commcell.refresh()
        display_name = self.tcinputs["ServerName"]
        for client in self.commcell.clients.all_clients:
            if client.startswith(self.tcinputs["ServerName"]):
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
                    self.commcell.job_controller.get(job).wait_for_completion(timeout=40)
            self.active_jobs_action(action=action)
        else:
            self.log.info("No Active Jobs found for the client.")

    @test_step
    def edit_rac_instance(self):
        """Edits rac instance properties"""
        self.ora_instance_details=OracleInstanceDetails(self.admin_console)
        self.db_instance_details.access_configuration_tab()
        self.ora_instance_details.edit_rac_instance_details(server_name=self.racServers[0],
                                                     db_username=self.connectUsername[0],
                                                     db_password=self.connectPassword[0],
                                                     db_instance_name=self.racInstance[0])
        self.db_instance_details.access_subclients_tab()
    @test_step
    def create_helper_object(self):
        """Creates oracle RAC helper object"""
        self.commcell.refresh()
        self.client = self.commcell.clients.get(self.tcinputs["RacClusterName"])
        self.instance = self.client.agents.get("oracle rac").instances.get(self.tcinputs["RacInstanceName"])
        self.oracle_helper_object = OracleRACHelper(self.commcell, self.client, self.instance,
                                                    admin_user_commcell=self.admin_user_commcell)
        self.oracle_helper_object.db_connect()
        self.oracle_helper_object.check_instance_status()

    @test_step
    def generate_test_data(self,cdb,pdb_name,backup_level="Full"):
        """Creates test data
            Args:
                cdb            (bool): True if database is cdb, False if it is non-cdb
                backup_level   (str): Backup level "Full" or "Incr"
                pdb_name        (str): Name of pdb to generate test data
        """
        table_limit = 1
        num_of_files = 1
        row_limit = 10
        if cdb=="True":
            if backup_level.lower() == "full":
                self.oracle_helper_object.db_connect_to_pdb(pdb_name=pdb_name)
                self.oracle_helper_object.create_sample_data(
                self.tablespace_name, table_limit, num_of_files)
                self.oracle_helper_object.db_connect_to_pdb(pdb_name="CDB$ROOT")
                self.oracle_helper_object.db_execute('alter system switch logfile')
                self.log.info("Test Data Generated successfully")
            else :
                self.log.info("Generating Sample Data for Incremental Backup")
                self.oracle_helper_object.db_connect_to_pdb(pdb_name=pdb_name)
                user = "{0}_user".format(self.tablespace_name.lower())
                self.oracle_helper_object.db_create_table(
                self.tablespace_name, "CV_TABLE_INCR_", user, table_limit,row_limit)
                self.log.info("Successfully generated sample data for incremental backups")
        else:
            if backup_level.lower() == "full":
                self.oracle_helper_object.create_sample_data(
                    self.tablespace_name, table_limit, num_of_files)
                self.oracle_helper_object.db_execute('alter system switch logfile')
                self.log.info("Test Data Generated successfully")
            else:
                self.log.info("Generating Sample Data for Incremental Backup")
                user = "{0}_user".format(self.tablespace_name.lower())
                self.oracle_helper_object.db_create_table(
                    self.tablespace_name, "CV_TABLE_INCR_", user, table_limit, row_limit)
                self.log.info("Successfully generated sample data for incremental backups")




    @test_step
    def run_backup(self,cdb,pdb_name=None,backup_level="Full"):
        """Method to trigger backup
            Args:
                cdb:           True if database is cdb, false if it is non cdb
                pdb_name :     Name of pdb to generate test data
                               default : None
                backup_level: Backup level "Full" or "Incr"
        """

        self.generate_test_data(cdb,pdb_name,backup_level)
        if backup_level.lower() == "full":
            self.db_instance_details.click_on_entity("default")
            job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        else:
            job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.INCR)
        self.wait_for_job_completion(job_id)
        self.log.info("Oracle %s Backup is completed", backup_level)
        if backup_level.lower() == "full":
            self.oracle_helper_object.backup_validation(job_id, 'Online Full')
        else:
            self.oracle_helper_object.backup_validation(job_id, 'Incremental')

    @test_step
    def clear_rac_instance(self):
        """Clears rac instance details"""
        self.ora_instance_details = OracleInstanceDetails(self.admin_console)
        self.subclient_page.return_to_instance(self.tcinputs["RacInstanceName"])
        self.db_instance_details.access_configuration_tab()
        self.ora_instance_details.edit_rac_instance_details(server_name=self.racServers[0],
                                                            db_username=self.connectUsername[0],
                                                            db_password=self.connectPassword[0],
                                                            db_instance_name=self.racInstance[0], clear=True)

    @test_step
    def run_restore(self):
        """ method to run restore"""
        self.log.info("Cleaning up tablespace and data before restore")
        self.oracle_helper_object.oracle_data_cleanup(
        tables=["CV_TABLE_01", "CV_TABLE_INCR_01"], tablespace=self.tablespace_name)
        self.db_instance_details.access_overview_tab()
        self.db_instance_details.access_restore()
        self.admin_console.wait_for_completion(wait_time=1000)
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = restore_panel.in_place_restore(recover_to="most recent backup")
        self.wait_for_job_completion(job_id)
        self.log.info("Oracle RAC Restore completed")

    @test_step
    def validate_restore(self):
        """method to validate restore"""
        table_limit = 1
        num_of_files = 1
        row_limit = 10
        self.oracle_helper_object.validation(self.tablespace_name, num_of_files,
                                            "CV_TABLE_01", row_limit)
        self.oracle_helper_object.validation(self.tablespace_name, num_of_files,
                                            "CV_TABLE_INCR_01", row_limit)
        self.log.info("Validation Successful.")

    @test_step
    def delete_tenant(self):
        """deactivate and delete the tenant"""
        if self.tenant_created:
            self.tenant_mgmt.deactivate_tenant(self.company_name)
            self.tenant_mgmt.delete_tenant(self.company_name)

    @test_step
    def cleanup(self):
        """Cleans up testcase created instance"""
        try:
            self.navigate_to_instance()
            self.database_instances.select_instance(DBInstances.Types.ORACLE_RAC,
                                                    self.tcinputs["RacInstanceName"],
                                                    self.tcinputs["RacClusterName"])
            self.log.info("Deleting instance")
            self.db_instance_details.delete_instance()
            self.delete_tenant()
            self.log.info("Deleting Automation generated Oracle data")
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01", "CV_TABLE_INCR_01"], tablespace=self.tablespace_name)
        except Exception as exp:
            self.log.info(exp)
            self.log.info("Clean up failed!! Failing testcase")



    def run(self):
        """ Main function for test case execution """
        try:
            self.log.info("#" * (10) + "  Oracle RAC Backup/Restore Operations  " + "#" * (10))
            self.initial_setup()
            self.navigate_to_instance_details()
            self.active_jobs_action(action="wait")
            self.edit_rac_instance()
            self.create_helper_object()
            self.run_backup(cdb=self.tcinputs["cdb"],pdb_name=self.tcinputs["PdbName"],backup_level="Full")
            self.run_backup(cdb=self.tcinputs["cdb"],pdb_name=self.tcinputs["PdbName"],backup_level="Incr")
            self.clear_rac_instance()
            self.run_restore()
            self.validate_restore()
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.log.info("Logging out of the admin console")
            AdminConsole.logout_silently(self.admin_console)
            self.log.info("Closing the browser")
            Browser.close_silently(self.browser)
