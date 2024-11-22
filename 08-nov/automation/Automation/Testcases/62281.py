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

    initial_setup()             --  method for initial setup to perform installation,
                                    assign cloud storage and pick plan

    create_test_data()          --  method for creating test data

    tear_down()                 --  tear down method for testcase

    wait_for_job_completion()   --  waits for completion of job

    navigate_to_instance()      --  navigates to specified instance

    create_helper_object()      --  creates object of OracleHelper class

    run_backup()                --  method to run backup

    run_restore()               --  method to run restore

    validate_restore()          --  method to validate test data

    update_display_names()      --  method to track display names of clients

    active_jobs_action()        --  method to kill or wait for the active jobs of client

    delete_tenant()             --  method to deactivate and delete the the tenant

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "62281":
                        {
                          "HostName":"client",
                          "ClientUsername":"root",
                          "ClientPassword":"password",
                          "InstanceName" :"instance",
                          "ConnectString":"username/password@servicename"

                          "DestinationHostName":"client",
                          "DestinationClientUsername":"root",
                          "DestinationClientPassword":"password",
                          "DestinationInstanceName" :"instance",
                          "DestinationConnectString":"username/password@servicename"

                          'RingHostname': "hostname",                   (optional, if not provided, hostname
                                                                            in input json will be used)
                          'StorageAccount': "Metallic HOT GRS Tier",    (optional)
                          'CloudProvider': "Microsoft Azure storage",   (optional)
                          'Region': "East US (Virginia)",               (optional)
                          'RetentionPeriod': "1 month",                 (optional)
                          'TestData': "[10, 20, 100]"  (eg. [No. of Datafiles, No. of Tables, No. of Rows in each table)
                                                        as list or string representation of list ie. "[10, 20, 100]"
                                                                        (optional, default:[1,1,100])
                          "RedirectAllPath": "redirect/all/path"    (optional)
                        }
            }

"""

import ast
import time
from cvpysdk.commcell import Commcell
from datetime import datetime
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Database.OracleUtils.oraclehelper import OracleHelper
from Metallic.hubutils import HubManagement
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Hub.constants import HubServices, DatabaseTypes
from Web.AdminConsole.Hub.Databases.databases import OracleMetallic
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue


class TestCase(CVTestCase):
    """ Class for executing acceptance Test for oracle on metallic out of place restore"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic out of place restore test case for Oracle"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_62281'
        self.database_type = None
        self.tcinputs = {
            'HostName': None,
            'ClientUsername': None,
            'ClientPassword': None,
            'InstanceName': None,
            'ConnectString': None,
            'DestinationHostName': None,
            'DestinationClientUsername': None,
            'DestinationClientPassword': None,
            'DestinationInstanceName': None,
            'DestinationConnectString': None
        }
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.automation_instance = None
        self.oracle_metallic_configuration = None
        self.service = None
        self.service_catalogue = None
        self.app_type = None
        self.tenant_mgmt = None
        self.company_name = None
        self.company_email = None
        self.tenant_username = None
        self.tenant_pswrd = None
        self.email = None
        self.plan_name = None
        self.is_config_success = False
        self.tenant_created = False
        self.test_data = [1, 1, 100]
        self.tables = {"full": "CV_TABLE_", "incr": "CV_TABLE_INCR_"}
        self.table_list = []
        self.wizard = None
        self.table = None
        self.infrastructure = None
        self.dest_client = None
        self.dest_instance = None
        self.dest_oracle_helper_object = None
        self.src_display_name = None
        self.dst_display_name = None

    def setup(self):
        """ Method to setup test variables """
        # Create new tenant user
        self.log.info("Started executing %s testcase", self.id)
        ring_hostname = self.tcinputs.get("RingHostname", self.commcell.webconsole_hostname)
        self.tenant_mgmt = HubManagement(self, ring_hostname)
        self.tenant_mgmt.delete_companies_with_prefix(prefix="ORACLE-DB-Automation")
        self.company_name = datetime.now().strftime("ORACLE-DB-Automation-%d-%B-%H-%M")
        self.email = datetime.now().strftime(f"metallic_oracle_db_%H-%M-%S@{self.company_name}.com")
        self.tenant_username = self.tenant_mgmt.create_tenant(self.company_name, self.email)
        self.tenant_pswrd = get_config().Metallic.tenant_password
        self.tenant_created = True
        self.commcell = Commcell(ring_hostname, self.tenant_username, self.tenant_pswrd)

        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_pswrd, stay_logged_in=True)
        self.oracle_metallic_configuration = OracleMetallic(self.admin_console)
        self.database_type = DBInstances.Types.ORACLE
        self.service = HubServices.database
        self.app_type = DatabaseTypes.oracle
        self.table = Rtable(self.admin_console)
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        self.wizard = Wizard(self.admin_console)
        self.infrastructure = "Virtual machine"
        if self.tcinputs.get("TestData"):
            if isinstance(self.tcinputs["TestData"], str):
                self.test_data = ast.literal_eval(self.tcinputs["TestData"])
            else:
                self.test_data = self.tcinputs["TestData"]

    @test_step
    def initial_setup(self):
        """ method for initial setup to perform installation,
        assign cloud storage and pick plan """
        machine = Machine(machine_name=self.tcinputs["HostName"], username=self.tcinputs["ClientUsername"],
                          password=self.tcinputs["ClientPassword"])
        cloud_storage_inputs = {"cloud_vendor": self.tcinputs.get("cloud_vendor") or "Air Gap Protect",
                                "storage_provider": self.tcinputs.get("storage_provider") or "Azure Blob Storage",
                                "region": self.tcinputs.get("region") or "(US) East US 2"}
        self.service_catalogue.click_get_started()
        self.service_catalogue.choose_service_from_service_catalogue(service=self.service.value, id=self.app_type.value)
        install_inputs = {
            "remote_clientname": self.tcinputs["HostName"],
            "remote_username": self.tcinputs["ClientUsername"],
            "remote_userpassword": self.tcinputs["ClientPassword"],
            "os_type": machine.os_info.lower(),
            "platform": machine.os_flavour,
            "username": self.tenant_username,
            "password": "3a1111972bc0091bb72079fc296201851a8ebe2f548febf1f",
        }
        dest_machine = Machine(machine_name=self.tcinputs["DestinationHostName"],
                               username=self.tcinputs["DestinationClientUsername"],
                               password=self.tcinputs["DestinationClientPassword"])
        install_inputs_dest = {
            "remote_clientname": self.tcinputs["DestinationHostName"],
            "remote_username": self.tcinputs["DestinationClientUsername"],
            "remote_userpassword": self.tcinputs["DestinationClientPassword"],
            "os_type": dest_machine.os_info.lower(),
            "platform": dest_machine.os_flavour,
            "username": self.tenant_username,
            "password": "3a1111972bc0091bb72079fc296201851a8ebe2f548febf1f",
        }
        self.oracle_metallic_configuration.select_on_prem_details(self.infrastructure, self.app_type)
        self.plan_name = self.oracle_metallic_configuration.configure_oracle_database(
            cloud_storage_inputs=cloud_storage_inputs,
            use_existing_plan=False,
            plan_inputs={"RetentionPeriod": self.tcinputs.get("RetentionPeriod") or "1 month"})
        pkg_file_path = self.oracle_metallic_configuration.do_pkg_download(platform="Linux")
        self.oracle_metallic_configuration.do_pkg_install(
            commcell=self.commcell, pkg_file_path=pkg_file_path, install_inputs=[install_inputs, install_inputs_dest])
        self.plan_name = self.company_name + '-' + self.plan_name
        self.is_config_success = True
        self.oracle_metallic_configuration.select_oracle_backup_content()
        self.oracle_metallic_configuration.proceed_from_summary_page()
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)
        self.update_display_names()

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
        tables = [f"{self.tables.get(backup_level.lower())}" + '{:02}'.format(i) for i in range(1, self.test_data[1]+1)]
        self.table_list.extend(tables)

    def tear_down(self):
        """ tear down method for testcase """
        if self.status == constants.PASSED:
            self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

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
    def navigate_to_instance(self):
        """Method to navigate to instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.table.reload_data()
        self.admin_console.refresh_page()
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["DestinationInstanceName"],
                                                self.tcinputs["DestinationHostName"])
        time.sleep(30)     # The execution is going to sleep as we wait for instances to be discovered
        self.db_instance_details.edit_instance_update_credentials(
            self.tcinputs["DestinationConnectString"])
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.admin_console.refresh_page()
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["HostName"])
        time.sleep(30)     # The execution is going to sleep as we wait for instances to be discovered
        self.db_instance_details.edit_instance_update_credentials(
            self.tcinputs["ConnectString"])
        self.admin_console.wait_for_completion()
        self.db_instance_details.access_subclients_tab()
        self.db_instance_details.click_on_entity('default')

    @test_step
    def create_helper_object(self):
        """Creates oracle helper objects"""
        self.commcell.refresh()
        self.log.info("Creating helper object for source instance")
        self.client = self.commcell.clients.get(self.src_display_name)
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        ora_creds = self.tcinputs["ConnectString"].split('@')[0].split('/')
        self.oracle_helper_object = OracleHelper(
            self.commcell, self.client, self.instance, ora_creds[0], ora_creds[1])
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

        self.log.info("creating helper object for destination instance")
        self.dest_client = self.commcell.clients.get(self.dst_display_name)
        self.dest_instance = self.dest_client.agents.get("oracle").instances.get(
            self.tcinputs["DestinationInstanceName"])
        ora_creds = self.tcinputs["DestinationConnectString"].split('@')[0].split('/')
        self.dest_oracle_helper_object = OracleHelper(
            self.commcell, self.dest_client, self.dest_instance, ora_creds[0], ora_creds[1])
        self.dest_oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.dest_oracle_helper_object.check_instance_status()

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
        self.wait_for_job_completion(job_id)
        self.log.info("Oracle %s Backup is completed", backup_level)
        if backup_level.lower() == "full":
            self.oracle_helper_object.backup_validation(job_id, 'Online Full')
        else:
            self.oracle_helper_object.backup_validation(job_id, 'Incremental')

    @test_step
    def run_restore(self):
        """ method to run restore"""
        self.log.info("Preparing for Restore.")
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        redirect_all_path = ''
        if "RedirectAllPath" in self.tcinputs:
            redirect_all_path = self.tcinputs["RedirectAllPath"]
        job_id = restore_panel.out_of_place_restore(
            self.tcinputs["DestinationHostName"],
            self.tcinputs["DestinationInstanceName"],
            redirect_all_path=redirect_all_path)
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")

    @test_step
    def validate_restore(self):
        """method to validate restore"""
        num_of_files, table_limit, row_limit = self.test_data
        self.log.info("Validating Backed up content")
        for test_table_prefix in self.tables.values():
            self.dest_oracle_helper_object.validation(
                self.tablespace_name, num_of_files, test_table_prefix, row_limit, table_limit)
        self.log.info("Validation Successful.")

    @test_step
    def update_display_names(self):
        """Method to update client display names"""
        self.commcell.refresh()
        for client_name in self.commcell.clients.all_clients:
            if client_name.startswith(self.tcinputs.get("HostName").lower()):
                self.src_display_name = client_name
                break
        for client_name in self.commcell.clients.all_clients:
            if client_name.startswith(self.tcinputs.get("DestinationHostName").lower()):
                self.dst_display_name = client_name
                break

    @test_step
    def active_jobs_action(self, client="source", action="kill"):
        """ Method to kill/wait for the active jobs running for the client
            Args:
                client(str): "source"/"destination"
                action  (str):  "wait" or "kill" active jobs
        """
        self.commcell.refresh()
        if client == "source":
            display_name = self.src_display_name
        else:
            display_name = self.dst_display_name

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
            self.active_jobs_action(client=client, action=action)
        else:
            self.log.info("No Active Jobs found for the client.")

    @test_step
    def delete_tenant(self):
        """deactivate and delete the tenant"""
        if self.tenant_created:
            self.tenant_mgmt.deactivate_tenant(self.company_name)
            self.tenant_mgmt.delete_tenant(self.company_name)

    @test_step
    def delete_instance(self, instance_name, host_name, client_type):
        """kill jobs and delete instance"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.ORACLE, instance_name, host_name)
        self.active_jobs_action(client=client_type)
        self.log.info("Deleting instance")
        self.db_instance_details.delete_instance()

    @test_step
    def cleanup(self):
        """ cleanup method """
        try:
            self.delete_instance(self.tcinputs["InstanceName"],
                                 self.tcinputs['HostName'], "source")
            self.delete_instance(self.tcinputs["DestinationInstanceName"],
                                 self.tcinputs['DestinationHostName'], "destination")
            self.delete_tenant()
            self.log.info("Deleting Automation generated Oracle data")
            self.oracle_helper_object.oracle_data_cleanup(
                tables=self.table_list, tablespace=self.tablespace_name,
                user="{0}_user".format(self.tablespace_name.lower()))
            self.dest_oracle_helper_object.oracle_data_cleanup(
                tables=self.table_list, tablespace=self.tablespace_name,
                user="{0}_user".format(self.tablespace_name.lower()))
        except Exception as exp:
            self.log.info(exp)
            self.log.info("Clean up failed!! Failing testcase")
            self.status = constants.FAILED

    def run(self):
        """ Main function for test case execution """
        try:
            self.initial_setup()
            self.navigate_to_instance()
            self.active_jobs_action(action="wait", client="source")
            self.create_helper_object()

            self.run_backup(backup_level="Full")
            self.run_backup(backup_level="Incr")

            self.run_restore()
            self.validate_restore()

        except Exception as exp:
            handle_testcase_exception(self, exp)
