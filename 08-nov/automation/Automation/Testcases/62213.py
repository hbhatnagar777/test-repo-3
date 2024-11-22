# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Live Sync IO: Continuous Replication - Negative cases

Sample input: "62213": {"vm_name":"Enter vm name to be selected when
creating pair", "ClientName":"Enter source hypervisor name", "recovery_target_datastore_full":"Enter recovery target
having datastore set as one which esx operations are to be performed", "recovery_target_datastore_full":"Enter
recovery target having datastore set as one whose space is fully occupied"} """

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, wait_for_condition
from Web.AdminConsole.DR.monitor import ContinuousReplicationMonitor
from time import sleep
from DROrchestration.test_failover import TestFailover
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.recovery_target_esx_operation = None
        self.recovery_target_datastore_full = None
        self.vm_name = None
        self.source_hypervisor = None
        self.name = "Continuous Replication - Negative cases"
        self.tcinputs = {
            "vm_name": None,
            "ClientName": None,
            "recovery_target_esx_operation": None,
            "recovery_target_datastore_full": None
        }
        self.replication_group = None
        self.destination_vm = None
        self.test_failover = None

    def setup(self):
        """Sets up the Testcase"""
        self.utils = TestCaseUtils(self)
        self.vm_name = self.tcinputs['vm_name']
        self.source_hypervisor = self.tcinputs['ClientName']
        self.recovery_target_esx_operation = self.tcinputs['recovery_target_esx_operation']
        self.recovery_target_datastore_full = self.tcinputs['recovery_target_datastore_full']

    @property
    def group_name(self):
        """Returns the replication group name"""
        return ReplicationHelper.group_name(self.id)

    def login(self):
        """Logs in to admin console"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.replication_group = ReplicationGroup(self.admin_console)
            self.test_failover = TestFailover(self.commcell, self.group_name)
            self.source_vm = [*self.test_failover.group.vm_pairs][0]
            self.destination_vm = self.test_failover.group.vm_pairs.get(self.source_vm).destination_vm
            self.continuous_monitor = ContinuousReplicationMonitor(self.admin_console)
            self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
            self.target_details = self.commcell.recovery_targets.get(self.recovery_target_esx_operation)

        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def select_destination_option_grid(self):
        """select destination from actions grid on monitor page"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_grid_option("Destination")

    def check_pair_status(self, expected):
        """Checks the sync status of the BLR pair with the expected value"""
        self.wait_for_sync_status(expected)

    @wait_for_condition(timeout=3500)
    def wait_for_sync_status(self, expected):
        """Waits for the sync status to meet expected value"""
        return (self.continuous_monitor.sync_status(self.source_vm,
                                                    self.destination_vm) == expected)

    @test_step
    def perform_resync(self):
        """Perform stop operation on the pair"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.resync(self.source_vm, self.destination_vm)
        self.check_pair_status('Re-syncing')

    @test_step
    def enable_maintenance_mode(self):
        """Enable maintenance mode on esx server"""
        self.test_failover.destination_auto_instance.hvobj.enable_maintenance_mode(self.target_details.destination_host)

    @test_step
    def disable_maintenance_mode(self):
        """Disable maintenance mode on esx server"""
        self.test_failover.destination_auto_instance.hvobj.disable_maintenance_mode(self.target_details.destination_host)

    @test_step
    def reboot_esx_host(self):
        """Reboot an ESXi host"""
        self.test_failover.destination_auto_instance.hvobj.enter_standby_mode(self.target_details.destination_host)
        self.test_failover.destination_auto_instance.hvobj.exit_standby_mode(self.target_details.destination_host)

    @test_step
    def configure_replication_group(self, group_name, recovery_target_name):
        """Create a continuous replication group"""
        self.admin_console.navigator.navigate_to_replication_groups()
        vmware_configure = self.replication_group.configure_vmware()
        vmware_configure.content.set_name(group_name)
        vmware_configure.content.select_vm_from_browse_tree(self.source_hypervisor, {"VMs and templates": [self.vm_name]})
        vmware_configure.next()
        vmware_configure.target.select_recovery_target(recovery_target_name)
        vmware_configure.target.select_continuous_replication_type()
        vmware_configure.next()
        vmware_configure.storage_cache.continuous_rpstore.select_recovery_type(0)
        vmware_configure.next()
        sleep(5)
        vmware_configure.finish()

    @test_step
    def delete_replication_group(self):
        """Deletes the replication group if it exists already"""
        self.replication_helper.delete_replication_group(self.group_name)

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def run(self):
        """Runs the testcase in order"""
        try:
            self.login()
            self.configure_replication_group(self.group_name, self.recovery_target_esx_operation)
            self.select_destination_option_grid()
            self.check_pair_status("Re-syncing")
            # ## Add the dest host in maintenance mode and check if pair returns to replicating state
            # # TODO:Change status when fix for valid event is created for events
            self.enable_maintenance_mode()
            # ### Currently JPR is shown as resyncing creating a MR to add a valid JPR will add changes to suite later once event is added
            self.select_destination_option_grid()
            self.check_pair_status("Re-syncing")
            self.disable_maintenance_mode()
            self.select_destination_option_grid()
            self.check_pair_status("Re-syncing")


            # ### When replication is in progress add host to maintenance mode
            self.enable_maintenance_mode()
            self.select_destination_option_grid()
            self.check_pair_status("Replicating")
            self.disable_maintenance_mode()
            self.select_destination_option_grid()
            self.check_pair_status("Replicating")

            # ### While resync in progress restart dest esx server verify pair gets in replicating mode
            self.perform_resync()
            self.enable_maintenance_mode()
            self.reboot_esx_host()
            self.disable_maintenance_mode()
            self.select_destination_option_grid()
            self.check_pair_status("Replicating")
            #
            # ### While the replication is in progress restart dest esx server verify pair gets in replicating mode
            self.enable_maintenance_mode()
            self.reboot_esx_host()
            self.disable_maintenance_mode()
            self.select_destination_option_grid()
            self.check_pair_status("Replicating")
            self.delete_replication_group()

            # ### Create a pair where destination datatstore is full verify JPR on pair
            # #TODO:Change status when fix for valid event is created for events
            sleep(100)
            self.configure_replication_group(self.group_name, self.recovery_target_datastore_full)
            ### Currently pair doesnt show valid JPR and is stuck in resync phase when dest datastore is full
            ### will a MR and update this case after fix is given
            self.select_destination_option_grid()
            self.check_pair_status("Re-syncing")
            self.delete_replication_group()

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()

