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

    setup()                     --  Method to setup test variables

    initial_setup()             --  method for initial setup to perform installation,
    asign cloud storage and pick plan

    upgrade_client_software()   --  updates the client software

    navigate_to_instance()      --  navigates to the instance details page

    navigate_to_subclient()     --  method to navigate to subclient page

    run_backup()                --  method to run backup

    run_restore()               --  method to run restore

    kill_active_jobs()          --  Method to kill the active jobs running for the client

    cleanup()                   --  cleanup method

    wait_for_job_completion()   --  Waits for completion of job and gets the job object

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "60050":
                        {
                            "SystemName": None,
                            "SID": None,
                            "HostName": None,
                            "DatabaseUserName": None,
                            "DatabasePassword": None,
                            "ClientUsername": None,
                            "ClientPassword": None,
                            "StorageAccount": None,
                            "CloudProvider": None,
                            "Region": None,
                            "HyperVServer": None,
                            "HyperVUserName": None,
                            "HyperVPassword": None,
                            "HyperVVMName": None,
                            "HyperVSnapName": None
                        }
            }

"""

from datetime import datetime
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils.vmoperations import HyperVOperations
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import SAPHANAInstanceDetails
from Web.AdminConsole.Databases.backupset import Backupset
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Databases.Instances.restore_panels import SAPHANARestorePanel
from Web.AdminConsole.Hub.constants import HubServices, DatabaseTypes
from Web.AdminConsole.Hub.Databases.databases import SAPHanaMetallic
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.Components.panel import RDropDown


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for SAP HANA on Metallic """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic ACC1 for SAP HANA"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            "SystemName": None,
            "SID": None,
            "HostName": None,
            "DatabaseUserName": None,
            "DatabasePassword": None,
            'ClientUsername': None,
            'ClientPassword': None,
            'StorageAccount': None,
            'CloudProvider': None,
            'Region': None,
            'HyperVServer': None,
            'HyperVUserName': None,
            'HyperVPassword': None,
            'HyperVVMName': None,
            'HyperVSnapName': None
        }
        self.service = None
        self.hub_dashboard = None
        self.app_type = None
        self.teams = None
        self.database_instances = None
        self.db_instance_details = None
        self.hana_metallic_configuration = None
        self.is_metallic_success = False
        self.system_name = None
        self.databases_page = None
        self.subclient_page = None
        self.page_container = None

        self.tenant_mgmt = None
        self.company_name = None
        self.email = None
        self.tenant_username = None
        self.tenant_pswrd = None
        self.hyperv = None
        self.hub_dashboard = None
        self.service_catalogue = None
        self.infrastructure = None
        self.plan_name = None
        self.rtable = None
        self.servers_obj = None

    def setup(self):
        """ Method to setup test variables """
        self.hyperv = HyperVOperations(self.tcinputs["HyperVServer"],
                                       self.tcinputs["HyperVUserName"],
                                       self.tcinputs["HyperVPassword"]
                                       )
        self.revert_vm()
        ring_hostname = self.tcinputs.get("ring_hostname", self.commcell.webconsole_hostname)
        self.tenant_mgmt = HubManagement(self, ring_hostname)
        self.company_name = datetime.now().strftime("HANA-DB-Automation-%d-%B-%H-%M")
        self.email = datetime.now().strftime(f"metallic_hana_db_%H-%M-%S@{self.company_name}.com")
        self.tenant_username = self.tenant_mgmt.create_tenant(self.company_name, self.email)
        self.tenant_pswrd = get_config().Metallic.tenant_password

        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_pswrd, stay_logged_in=True)
        self.commcell = Commcell(ring_hostname,
                                 self.tenant_username,
                                 self.tenant_pswrd)
        self.service = HubServices.database
        self.infrastructure = "Virtual machine"
        self.app_type = DatabaseTypes.sap_hana
        self.hub_dashboard = Dashboard(self.admin_console, self.service, self.app_type)
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        self.hana_metallic_configuration = SAPHanaMetallic(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.servers_obj = Servers(self.admin_console)

        self.system_name = self.tenant_username.split('\\')[0].replace('-', '')
        self.system_name = f"{self.system_name}_{self.tcinputs['SystemName']}"
        self.log.info("System Name: %s", self.system_name)

    @test_step
    def revert_vm(self):
        """ method to revert vm snapshot """
        self.hyperv.revert_snapshot(self.tcinputs["HyperVVMName"], self.tcinputs["HyperVSnapName"])
        self.hyperv.power_on_vm(self.tcinputs["HyperVVMName"])

    @test_step
    def initial_setup(self):
        """ method for initial setup to perform installation,
        assign cloud storage and pick plan """
        install_inputs = {
            "remote_clientname": self.tcinputs['HostName'],
            "remote_username": self.tcinputs['ClientUsername'],
            "remote_userpassword": self.tcinputs['ClientPassword'],
            "os_type": "unix",
            "username": self.tenant_username,
            "password": "3a1111972bc0091bb72079fc296201851a8ebe2f548febf1f"
        }
        cloud_storage_inputs = {"StorageAccount": self.tcinputs.get("StorageAccount") or "Metallic HOT GRS Tier",
                                "CloudProvider": self.tcinputs.get("CloudProvider") or "Microsoft Azure storage",
                                "Region": self.tcinputs.get("Region") or "East US (Virginia)"}
        plan_inputs = {"RetentionPeriod": "1 month"}
        self.service_catalogue.click_get_started()
        self.service_catalogue.choose_service_from_service_catalogue(self.service.value, "SAP HANA")
        self.hana_metallic_configuration.select_on_prem_details(self.infrastructure, self.app_type)
        self.plan_name = self.hana_metallic_configuration.configure_hana_database(cloud_storage_inputs, plan_inputs=plan_inputs)
        pkg_file_path = self.hana_metallic_configuration.do_pkg_download(platform="Linux")
        self.system_name = self.hana_metallic_configuration.do_pkg_install(
            commcell=self.commcell, pkg_file_path=pkg_file_path, install_inputs=install_inputs)
        self.hana_metallic_configuration.select_hana_backup_content()
        self.hana_metallic_configuration.proceed_from_summary_page()
        self.is_metallic_success = True
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = SAPHANAInstanceDetails(self.admin_console)
        self.databases_page = Backupset(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)
        self.page_container = PageContainer(self.admin_console)

    @test_step
    def upgrade_client_software(self):
        """
        updates the client software
        """
        self.navigator.navigate_to_servers()
        self.admin_console.refresh_page()
        self.rtable.set_default_filter('Type', 'All')
        self.admin_console.unswitch_to_react_frame()
        job = self.servers_obj.action_update_software(client_name=self.tcinputs['HostName'])
        self.wait_for_job_completion(job)
        self.log.info("Client software Upgrade successful.")

    @test_step
    def navigate_to_instance(self):
        """ navigates to the instance details page"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.SAP_HANA,
            self.tcinputs['SID'], self.system_name)

    @test_step
    def navigate_to_subclient(self):
        """ method to navigate to subclient page"""
        self.navigate_to_instance()
        self.db_instance_details.update_credentials(self.tcinputs["DatabaseUserName"],
                                                    self.tcinputs["DatabasePassword"])
        self.admin_console.refresh_page()
        self.page_container.select_entities_tab()
        self.db_instance_details.click_on_entity(self.tcinputs['SID'])
        self.page_container.select_entities_tab()
        self.databases_page.access_subclient('default')

    @test_step
    def run_backup(self):
        """ method to run backup """
        self.log.info("Running Full Backup.")
        job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(job_id)
        job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.INCR)
        self.wait_for_job_completion(job_id)

    @test_step
    def run_restore(self):
        """ method to run restore """
        self.navigate_to_instance()
        self.log.info("Running Restore Job")
        drop_down = RDropDown(self.admin_console)
        drop_down.select_drop_down_values(drop_down_id='backupSetsDropdown', values=[self.tcinputs['SID']])
        self.databases_page.access_restore()
        restore_panel = SAPHANARestorePanel(self.admin_console)
        restore_job = restore_panel.in_place_restore()
        self.wait_for_job_completion(restore_job)

    @test_step
    def kill_active_jobs(self):
        """ Method to kill the active jobs running for the client """
        self.commcell.refresh()
        active_jobs = self.commcell.job_controller.active_jobs(self.system_name)
        self.log.info("Active jobs for the client:%s", active_jobs)
        if active_jobs:
            for job in active_jobs:
                self.log.info("Killing Job:%s", job)
                self.commcell.job_controller.get(job).kill(True)
            active_jobs = self.commcell.job_controller.active_jobs(self.system_name)
            if active_jobs:
                self.kill_active_jobs()
            self.log.info("All active jobs are killed")
        else:
            self.log.info("No Active Jobs found for the client.")

    @test_step
    def cleanup(self):
        """ cleanup method """
        if self.is_metallic_success:
            self.navigator.navigate_to_db_instances()
            if self.database_instances.is_instance_exists(
                    self.database_instances.Types.SAP_HANA,
                    self.tcinputs['SID'], self.system_name):
                self.kill_active_jobs()
                self.database_instances.select_instance(
                    self.database_instances.Types.SAP_HANA,
                    self.tcinputs['SID'],
                    self.system_name)
                self.db_instance_details.delete_instance()

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
        self.log.info("Successfully finished %s job", jobid)

    def run(self):
        """ Main function for test case execution """
        try:
            self.initial_setup()
            self.upgrade_client_software()
            self.navigate_to_subclient()
            self.run_backup()
            self.run_restore()
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.tenant_mgmt.deactivate_tenant(self.tenant_username)
            self.tenant_mgmt.delete_tenant(self.tenant_username)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.hyperv.power_off_vm(self.tcinputs["HyperVVMName"])
