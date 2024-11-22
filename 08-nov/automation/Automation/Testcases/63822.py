"""
Main file for executing this test case


    Add controller Ip to inbound rules of EC2

    Turn on the Oracle Listener and confirm the connectivity(turn off firewall)

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    initial_setup()             --  method for initial setup to perform installation,
                                    assign cloud storage and pick plan

    get_install_job_id()        --  fetches the push install job id

    active_jobs_action()        --  method to kill or wait for the active jobs of client

    navigate_to_subclient()      --  navigates to specified subclient

    create_helper_object()      --  creates object of OracleHelper class

    create_test_data()          --  method for creating test data

    run_backup()                --  method to run backup

    run_restore()               --  method to run restore

    validate_restore()          --  method to validate test data

    delete_tenant()             --  method to deactivate and delete the tenant

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case

    tear_down()                 --  tear down method for testcase

Input Example:

    "testCases":
            {
                "63822":
                        {
                          "EC2InstanceName":"EC2 Machine Name",
                          "Region":"Region where VM is hosted and all operations are happening",
                          "userName":"root",
                          "password":"password",
                          "instanceName":"instance",
                          "ConnectString":"username/password@servicename",
                          "key-pair":"key pair for backup gateway(AWS)",
                          "vpc":"vpc for backup gateway(AWS)",
                          "subnet":"subnet for backup gateway(AWS)",
                          "gateway_os_type":"OS type for gateway access node",
                          "plan_name":"plan name in metallic",
                          "tenantCred":"Encrypted password of the oracle client"
                          "push install":"bool to select the way of installation"
                          'RingHostname': "hostname",                   (optional, if not provided, hostname
                                                                            in input json will be used)

                          'StorageAccount': "Metallic HOT GRS Tier",    (optional)
                          'CloudProvider': "Microsoft Azure storage",   (optional)
                          'RetentionPeriod': "1 month",                 (optional)
                          'TestData': "[10, 20, 100]"  (eg. [No. of Datafiles, No. of Tables, No. of Rows in each table)
                                                        as list or string representation of list ie. "[10, 20, 100]"
                                                                        (optional, default:[1,1,100])
                        }
            }
    ### Add a cron job to the oracle client with these commands

        crontab -e
            @reboot sleep 45 && /oracle.sh
        service crond restart

    ### also, add this as bash script in "/" folder naming "oracle.sh"
            #/!/bin/bash

            sudo systemctl stop firewalld
            su - oracle << EOF
            . ~/.bash_profile
            sqlplus / as sysdba
            startup mount;
            alter database archivelog;
            alter database open;
            exit;
            echo "Oracle is started"
            lsnrctl start
            EOF

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
from Database.dbhelper import DbHelper
from Metallic.hubutils import HubManagement
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Hub.constants import HubServices, DatabaseTypes
from Web.AdminConsole.Hub.Databases.databases import RAWSOracleMetallic
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.table import Rtable
from Application.CloudApps.amazon_helper import AmazonEC2Helper
from Application.CloudStorage.s3_helper import S3MetallicHelper, S3Helper
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.AdminConsole.Components.dialog import RBackup


class TestCase(CVTestCase):
    """Class for executing """
    test_step = TestStep()

    def __init__(self):
        """ Main function for test case execution """
        super(TestCase, self).__init__()
        self.name = "Test for Oracle IDA from Metallic Command Center on AWS cloud"
        self.dbhelper = None
        self.backup_gateway = None
        self.byos_bucket_name = None
        self.byos_storage_name = None
        self.stack_name = None
        self.HostName = None
        self.EC2_HostName = None
        self.ec2_helper = None
        self.s3_helper = None
        self.s3_container_helper = None
        self.gateway_created = None
        self.oracle_metallic_configuration = None
        self.oracle_helper_object = None
        self.database_type = None
        self.test_data = None
        self.wizard = None
        self.r_table = None
        self.hub_dashboard = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_63822'
        self.tenant_mgmt = None
        self.company_name = None
        self.company_email = None
        self.tenant_username = None
        self.tenant_pswrd = None
        self.tenant_created = None
        self.app_type = None
        self.service = None
        self.tables = {"full": "CV_TABLE_", "incr": "CV_TABLE_INCR_"}
        self.table_list = []
        self.vendor = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.config_files = get_config()
        self.service_catalogue = None

    def setup(self):
        """ Method to set up test variables"""
        self.log.info(f"Started Executing {self.id} testcase")
        ring_hostname = self.tcinputs.get("RingHostname", self.commcell.webconsole_hostname)
        self.tenant_mgmt = HubManagement(self, ring_hostname)
        self.tenant_mgmt.delete_companies_with_prefix(prefix="ORACLE-DB-Automation-AWS-SK")
        self.company_name = datetime.now().strftime("ORACLE-DB-Automation-AWS-SK-%d-%B-%H-%M")
        self.company_email = datetime.now().strftime(f"metallic_oracle_db_AWS_SK_%H-%M-%S@{self.company_name}.com")
        self.tenant_username = self.tenant_mgmt.create_tenant(self.company_name, self.company_email)
        self.tenant_pswrd = self.config_files.Metallic.tenant_password
        self.tenant_created = True
        self.commcell = Commcell(ring_hostname, self.tenant_username, self.tenant_pswrd)

        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_pswrd, stay_logged_in=True)
        self.database_type = DBInstances.Types.ORACLE
        self.service = HubServices.database
        self.app_type = DatabaseTypes.oracle
        self.hub_dashboard = Dashboard(self.admin_console, self.service, self.app_type)
        self.wizard = Wizard(self.admin_console)
        self.r_table = Rtable(self.admin_console)
        self.dbhelper = DbHelper(self.commcell)
        self.s3_helper = S3MetallicHelper(self.tcinputs["Region"])
        self.s3_container_helper = S3Helper(self)
        self.vendor = "Amazon Web Services"
        self.ec2_helper = AmazonEC2Helper(
            self.config_files.aws_access_creds.access_key, self.config_files.aws_access_creds.secret_key)
        self.oracle_metallic_configuration = RAWSOracleMetallic(admin_console=self.admin_console,
                                                                ec2_helper=self.ec2_helper, s3_helper=self.s3_helper)
        self.ec2_helper.start_ec2_instance(instance_name=self.tcinputs['EC2InstanceName'],
                                           region=self.tcinputs['Region'])

        self.log.info("fetching EC2 instance IP")
        self.EC2_HostName = self.ec2_helper.get_public_ip(
            instance_name=self.tcinputs['EC2InstanceName'], region=self.tcinputs['Region'])
        self.HostName = self.ec2_helper.get_private_ip(
            instance_name=self.tcinputs['EC2InstanceName'], region=self.tcinputs['Region'])
        self.HostName = "ip-" + str(self.HostName).replace(".", "-")
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        if self.tcinputs.get("TestData"):
            if isinstance(self.tcinputs["TestData"], str):
                self.test_data = ast.literal_eval(self.tcinputs["TestData"])
            else:
                self.test_data = self.tcinputs["TestData"]


    @test_step
    def initial_setup(self):
        """initial setup method"""
        machine = Machine(machine_name=self.EC2_HostName, username=self.tcinputs["userName"],
                          password=self.tcinputs["password"])
        self.hub_dashboard.click_get_started()
        self.service_catalogue.choose_service_from_service_catalogue(self.service.value, id="Oracle")
        self.oracle_metallic_configuration.select_cloud_vm_details(self.vendor, self.app_type)
        params = [
            {
                "ParameterKey": "KeyName",
                "ParameterValue": self.tcinputs.get("key-pair")
            },
            {
                "ParameterKey": "VpcId",
                "ParameterValue": self.tcinputs.get("vpc")
            },
            {
                "ParameterKey": "SubnetId",
                "ParameterValue": self.tcinputs.get("subnet")
            }
        ]
        self.stack_name = "awsmetallicoracle" + datetime.now().strftime("sk%d%B%H%M")
        self.byos_storage_name = "awsmetallicoraclestorage" + datetime.now().strftime("sk%d%B%H%M").lower()
        self.byos_bucket_name = "awsmetallicoraclebucket" + datetime.now().strftime("sk%d%B%H%M").lower()
        self.backup_gateway = self.oracle_metallic_configuration.create_gateway(
            stack_params=params,
            gateway_os_type=self.tcinputs["gateway_os_type"], stack_name=self.stack_name,
            EC2_instance_name=self.tcinputs.get("EC2InstanceName"),
            Region=self.tcinputs.get("Region"),
        )
        job = self.oracle_metallic_configuration.upgrade_client_software(self.backup_gateway)
        self.dbhelper.wait_for_job_completion(job)
        time.sleep(300)
        self.log.info("Client software Upgrade successful.")
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.oracle_metallic_configuration.click_add_server()
        self.oracle_metallic_configuration.select_cloud_vm_details(self.vendor, self.app_type)
        self.oracle_metallic_configuration.configure(
            self.byos_storage_name, self.byos_bucket_name,
            HostName=self.HostName, clientName=self.EC2_HostName,
            ClientUsername=self.tcinputs["userName"], ClientPassword=self.tcinputs["password"],
            tenant_username=self.tenant_username, tenant_password=self.tcinputs["tenantCred"],
            ClientOS="Linux", Commcell=self.commcell,
            EC2_instance_name=self.tcinputs.get("EC2InstanceName"),
            Region=self.tcinputs.get("Region"),
            push_install=self.tcinputs.get("push_install"), machine=machine,
            instanceName=self.tcinputs.get("instanceName")
        )
        if self.tcinputs.get("push_install"):
            _jobid = self.get_install_job_id()
            self.dbhelper.wait_for_job_completion(_jobid)
        self.gateway_created = True
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)

    def get_install_job_id(self):
        """
        This will fetch the push install job id.
        """
        active_jobs = self.commcell.job_controller.active_jobs()
        self.log.info(f"Install jobs for the client:{active_jobs}")
        return list(active_jobs.keys())[0]

    @test_step
    def active_jobs_action(self, action="kill"):
        """ Method to kill/wait for the active jobs running for the client
            Args:
                action  (str):  "wait" or "kill" active jobs
        """
        self.commcell.refresh()
        display_name = self.HostName
        for client in self.commcell.clients.all_clients:
            if client.startswith(self.HostName):
                display_name = client
                break
        active_jobs = self.commcell.job_controller.active_jobs(display_name)
        self.log.info(f"Active jobs for the client:{active_jobs}")
        if active_jobs:
            for job in active_jobs:
                if action == "kill":
                    self.log.info(f"Killing Job:{job}")
                    self.commcell.job_controller.get(job).kill(wait_for_job_to_kill=True)
                else:
                    self.log.info(f"Waiting for job {job} to complete")
                    self.commcell.job_controller.get(job).wait_for_completion(timeout=5)
            self.active_jobs_action(action=action)
        else:
            self.log.info("No Active Jobs found for the client.")

    @test_step
    def navigate_to_subclient(self):
        """Navigates to Instance page"""
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.log.info("Checking if instance exists")
        self.r_table.reload_data()
        if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                      self.tcinputs["instanceName"],
                                                      self.HostName):
            self.log.info("Instance found")
        else:
            raise CVTestStepFailure("Instance not found to be auto discovered")
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["instanceName"],
                                                self.HostName)
        self.db_instance_details.edit_instance_update_credentials(
            self.tcinputs["ConnectString"])
        self.log.info("The program is sleeping for 60 seconds")
        time.sleep(60)
        self.db_instance_details.click_on_entity('default')

    @test_step
    def create_helper_object(self):
        """Creates oracle helper object"""
        self.commcell.refresh()
        self.client = self.commcell.clients.get(self.HostName)
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["instanceName"])
        ora_creds = self.tcinputs["ConnectString"].split('@')[0].split('/')
        self.oracle_helper_object = OracleHelper(
            self.commcell, self.client, self.instance, ora_creds[0], ora_creds[1])
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA, host_name=self.EC2_HostName)
        self.oracle_helper_object.check_instance_status()

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
            user = f"{self.tablespace_name.lower()}_user"
            self.oracle_helper_object.db_create_table(
                self.tablespace_name, self.tables.get("incr"), user, table_limit, row_limit)
        tables = [f"{self.tables.get(backup_level.lower())}" + f'{i:02}' for i in
                  range(1, self.test_data[1] + 1)]
        self.table_list.extend(tables)

    @test_step
    def run_backup(self, backup_level="Incr"):
        """Method to trigger backup
            Args:
                backup_level(str): Backup level "Full" or "Incr"
        """
        self.create_test_data(backup_level)
        if backup_level.lower() == "full":
            job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        else:
            job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.INCR)
        self.dbhelper.wait_for_job_completion(job_id)
        self.log.info(f"Oracle {backup_level} Backup is completed")
        if backup_level.lower() == "full":
            self.oracle_helper_object.backup_validation(job_id, 'Online Full')
        else:
            self.oracle_helper_object.backup_validation(job_id, 'Incremental')

    @test_step
    def run_restore(self):
        """ method to run restore"""
        self.log.info("Cleaning up tablespace and data before restore")
        self.oracle_helper_object.oracle_data_cleanup(
            tables=self.table_list, tablespace=self.tablespace_name,
            user=f"{self.tablespace_name.lower()}_user")

        self.log.info("Preparing for Restore.")
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['instanceName'])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = restore_panel.in_place_restore()
        self.dbhelper.wait_for_job_completion(job_id)
        self.log.info("Restore completed")

    @test_step
    def validate_restore(self):
        """method to validate restore"""
        num_of_files, table_limit, row_limit = self.test_data
        self.log.info("Validating Backed up content")
        for test_table_prefix in self.tables.values():
            self.oracle_helper_object.validation(
                self.tablespace_name, num_of_files, test_table_prefix, row_limit, table_limit,
                host_name=self.EC2_HostName)
        self.log.info("Validation Successfull.")

    def delete_tenant(self):
        """
        This deletes the tenant created
        """
        self.tenant_mgmt.deactivate_tenant(self.company_name)
        self.tenant_mgmt.delete_tenant(self.company_name)

    @test_step
    def cleanup(self):
        """ cleanup method """
        try:
            self.ec2_helper.stop_ec2_instance(instance_name=self.tcinputs['EC2InstanceName'],
                                           region=self.tcinputs['Region'])
            self.delete_tenant()
            s3_session = self.s3_container_helper.create_session_s3(
                access_key=self.config_files.aws_access_creds.access_key
                , secret_access_key=self.config_files.aws_access_creds.secret_key, region=self.tcinputs.get('Region'))
            self.s3_container_helper.delete_container_s3(s3_session, self.byos_bucket_name)
            inbound_ip = self.ec2_helper.get_public_ip(instance_id=self.backup_gateway.replace('BackupGateway-', ''),
                                                       region=self.tcinputs.get('Region'))
            self.ec2_helper.remove_inbound_rule(instance_name=self.tcinputs.get('EC2InstanceName'),
                                                region=self.tcinputs.get('Region'),
                                                inbound_ip=inbound_ip)
            self.s3_helper.delete_stack(stack_name=self.stack_name)
            self.oracle_helper_object.oracle_data_cleanup(
                tables=self.table_list, tablespace=self.tablespace_name,
                user=f"{self.tablespace_name.lower()}_user")
        except Exception as exp:
            self.log.info(exp)
            self.log.info("Clean up failed!! Failing testcase")
            self.status = constants.FAILED

    def run(self):
        """ Main function for test case execution """
        try:
            self.initial_setup()
            self.navigate_to_subclient()
            self.active_jobs_action(action="wait")
            self.create_helper_object()

            self.run_backup(backup_level="Full")
            self.run_backup(backup_level="Incr")

            self.run_restore()
            self.validate_restore()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """
        Function to run after automation execution
        """
        self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
