import time
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.virtualization_replication import ConfigureAzureVM
from DROrchestration.DRUtils.DRConstants import Vendors_Complete, ReplicationType, TimePeriod, SiteOption
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper, DRHelper
from cvpysdk.recovery_targets import RecoveryTarget
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.constants import HubServices, AutoRecoveryTypes
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import handle_testcase_exception, TestStep

class TestCase(CVTestCase):
    """
    Class for executing test case for Orchestration replication group creation in metallic
    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Metallic - Orchestration: Replication Group Creation"
        self.browser = None
        self.hub_dashboard = None
        self.admin_console = None
        self.navigator = None
        self.replication_group = None
        self.source_hypervisor = None
        self.source_vms = None
        self.recovery_target = None
        self.tcinputs = {
            "TenantUsername": None,
            "TenantPassword": None,
            "ClientName": None,
            "SourceVMs": [],
            "VmGroup": None,
            "CopyforReplication": None,
            "RecoveryTarget": None,
            "drvm_name": None
        }

    def navigate_to_service_catalog(self):
        """navigates to service catalog"""
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_service_catalogue()

    def login(self):
        """Logs in to admin console"""
        self.admin_console = AdminConsole(BrowserFactory().create_browser_object().open(),
                                          machine=self.inputJSONnode
                                          ['commcell']['webconsoleHostname'])
        self.admin_console.login(self.tcinputs['TenantUsername'],
                                 self.tcinputs['TenantPassword'])
        self.replication_helper = ReplicationHelper(self.commcell,
                                                        self.admin_console)
        self.replication_group = ReplicationGroup(self.admin_console)
    
    @property
    def group_name(self):
        """Returns the replication group name"""
        return self.replication_helper.group_name(self.id)

    def setup(self):
        """ Pre-requisites for this testcase """
        self.tenantuser = self.tcinputs.get("TenantUsername", "")
        self.tenantpassword = self.tcinputs.get("TenantPassword", "")
        self.source_hypervisor = self.tcinputs.get("ClientName", "")
        self.source_vms = self.tcinputs.get("SourceVMs", [])
        self.vm_group = self.tcinputs.get("VmGroup", "")
        self.copy_for_replication = self.tcinputs.get("CopyforReplication", "")
        self.recovery_target = self.tcinputs.get("RecoveryTarget", "")
        self.drvm_name = self.tcinputs.get("drvm_name", "")
        self._frequency_duration = 4
        self._frequency_unit = TimePeriod.HOURS
        self._source_vendor = Vendors_Complete.AZURE.value
        self._destination_vendor = Vendors_Complete.AZURE.value
        self._replication_type = ReplicationType.Orchestrated
        self._siteoption = SiteOption.WarmSite
        self.target_details: RecoveryTarget = self.commcell.recovery_targets.get(
            self.recovery_target)
        self._unconditionally_overwrite = True
        self._continue_to_next_priority = True
        self._delay_between_priorities = 5
        
    @test_step
    def configure_replication_group(self):
        """Create a replication group with a single copy and overrides"""
        azure_configure = self.replication_group.configure_virtualization(source_vendor=self._source_vendor,
                                                                          destination_vendor=self._destination_vendor,
                                                                          replication_type=self._replication_type.value,
                                                                          is_metallic=True)

        # Type Hinting
        azure_configure: ConfigureAzureVM

        # General
        azure_configure.content.set_name(self.group_name)
        azure_configure.content.select_production_site_hypervisor(self.source_hypervisor)
        azure_configure.next()

        # Content
        azure_configure.content.select_vm_group(self.vm_group, self.source_vms, False)
        azure_configure.next()

        # Storage
        azure_configure.storage_cache.select_copy_for_replication(self.copy_for_replication)
        azure_configure.next()

        # Recovery Options
        azure_configure.recovery_options.select_recovery_target(self.recovery_target)
        azure_configure.next()

        # TODO : Pre-Post Scripts (Configuration)
        azure_configure.next()

        # Override Options
        azure_configure.next()

        # Advanced Options
        azure_configure.advanced_options.unconditionally_overwrite_vm(self._unconditionally_overwrite)
        azure_configure.advanced_options.continue_to_next_priority(self._continue_to_next_priority)
        azure_configure.advanced_options.set_delay_between_priority(self._delay_between_priorities)
        azure_configure.next()

        # Submit group creation request
        azure_configure.finish()

    @test_step
    def delete_replication_group(self):
        """Deletes the replication group if it exists already"""
        self.replication_helper.delete_replication_group(self.group_name)
    
    @test_step
    def verify_replication_group_exists(self):
        """Verify replication group exists in Replication Groups page"""
        self.replication_helper.verify_replication_group_exists(group_name=self.group_name,
                                                                source_hypervisor=self.source_hypervisor,
                                                                target_name=self.recovery_target,
                                                                site=self._siteoption.name,
                                                                replication_type='Orchestrated replication',
                                                                group_state='Recovery ready')

    def run(self):
        """Main function for test case execution"""
        self.login()
        try:
            self.hub_dashboard = Dashboard(self.admin_console,
                                           HubServices.auto_recovery,
                                           app_type=AutoRecoveryTypes.auto_recovery)
            try:
                self.admin_console.click_button("OK, got it")
            except BaseException:
                pass
            self.delete_replication_group()
            self.navigate_to_service_catalog()
            self.hub_dashboard.choose_service_from_dashboard()
            time.sleep(10)
            self.configure_replication_group()
            self.verify_replication_group_exists()

        except Exception as excp:
            handle_testcase_exception(self, excp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
