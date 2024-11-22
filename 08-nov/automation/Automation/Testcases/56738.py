# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Live Sync IO: VM Recovery ( DR Operations): TEST Failover operations for continuous pair

Sample input:
"56738": {
    "group_name":"Replication group name"
    }
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper, DRHelper
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, wait_for_condition
from Web.AdminConsole.DR.monitor import ContinuousReplicationMonitor
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from AutomationUtils.machine import Machine
from Web.AdminConsole.DR.rp_store import RpstoreOperations
from Web.AdminConsole.DR.recovery_targets import RecoveryPointStore
from time import sleep
from DROrchestration.test_failover import TestFailover


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)

        self.hypervisor = None
        self.name = "Live Sync IO: VM Recovery ( DR Operations): TEST Failover"
        self.vm = None
        self.testboot_vm = None
        self.rpstat_details1 = None
        self.tcinputs = {
            "group_name": None
        }
        self.replication_group = None
        self.source_vm = None
        self.dr_helper = None
        self.destination_vm = None
        self.group_name = None

        self.rpstorename = None
        self.test_failover = None
        self.controller = Machine()
        self.view_name = "56738_TC_view"
        self.testboot_options = {
            "test_vm_name": "Automation56738_TestVm",
            "expiration_time": "0:2",
            "recovery_type": "Recovery point time",
            "recovery_point": ""
        }

    def setup(self):
        """Sets up the Testcase"""
        self.utils = TestCaseUtils(self)
        self.group_name = self.tcinputs["group_name"]
        self.test_failover = TestFailover(self.commcell, self.group_name)
        self.source_vm = [*self.test_failover.group.vm_pairs][0]
        self.rpstorename = self.test_failover.group.vm_pairs.get(self.source_vm).pair_properties['blrRecoveryOpts']['granularV2']['rpStoreName']
        self.destination_vm = self.test_failover.group.vm_pairs.get(self.source_vm).destination_vm

    def login(self):
        """Logs in to admin console"""
        try:

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
            self.replication_group = ReplicationGroup(self.admin_console)
            self.rpstore = RpstoreOperations(self.admin_console)
            self.configure_rpstore = RecoveryPointStore(self.admin_console)
            self.vm_groups = VMGroups(self.admin_console)
            self.continuous_monitor = ContinuousReplicationMonitor(self.admin_console)
            self.dr_helper = DRHelper(self.commcell, self.csdb, self.client)
            self.dr_helper.source_auto_instance.hvobj.VMs = self.tcinputs['source_vm']
            self.hypervisor = self.dr_helper.source_auto_instance.hvobj
            self.vm = self.dr_helper.source_auto_instance.hvobj.VMs[self.tcinputs['source_vm']]
            self.vm.update_vm_info(prop="All")

        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def select_destination_option_grid(self):
        """select destination from actions grid on monitor page"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_grid_option("Destination")

    @test_step
    def verify_pair_status(self, source_vm, destination_vm, pair_status):
        """Verify on replication monitor table if pair is replicating"""
        _, table_content = self.continuous_monitor.get_replication_group_details(source_vm, destination_vm)
        table_content = table_content[0]
        self.utils.assert_comparison(table_content['Source'], source_vm)
        self.utils.assert_comparison(table_content['Destination'], destination_vm)
        self.utils.assert_comparison(table_content['Recovery type'], "Point in time recovery")
        self.utils.assert_comparison(table_content['Recovery point store'], self.rpstorename)
        self.utils.assert_comparison(table_content['Sync status'], pair_status)

    def check_pair_status(self, expected):
        """Checks the sync status of the BLR pair with the expected value"""
        self.wait_for_sync_status(expected)

    @wait_for_condition(timeout=3500)
    def wait_for_sync_status(self, expected):
        """Waits for the sync status to meet expected value"""
        return (self.continuous_monitor.sync_status(self.source_vm,
                                                    self.destination_vm) == expected)

    @test_step
    def create_view(self, source_vm, destination_vm):
        """"Create a replication view"""

        self.admin_console.navigator.navigate_to_continuous_replication()
        if self.continuous_monitor.has_replication_group(source_vm, destination_vm):
            if self.continuous_monitor.check_view(self.view_name):
                self.continuous_monitor.delete_view(self.view_name)
            self.continuous_monitor.create_view(self.view_name,
                                                {'Source': source_vm,
                                                 'Destination': destination_vm})
            self.continuous_monitor.select_view(self.view_name)

    @test_step
    def perform_resync(self):
        """Performs a resync operation"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_view(self.view_name)
        self.continuous_monitor.resync()
        sleep(200)
        self.select_destination_option_grid()
        self.check_pair_status('Replicating')

    @test_step
    def write_temp_data(self):
        """Writes data to the virtual machine and performs prevalidation for testfailover operation
        """
        self.test_failover.pre_validation()

    @test_step
    def get_rp_stats(self, recover_from="Recovery point time"):
        """Get list of RP store points for point in time boot operations"""

        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_view(self.view_name)

        self.rpstat_details1 = self.rpstore.get_all_rp_stats(recover_from)

    @test_step
    def perform_test_boot(self, testboot_options):
        """Perform test boot on the destination VM"""

        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_view(self.view_name)
        test_boot_job_id = self.continuous_monitor.continuous_test_bootvm(testboot_options)
        job_obj = self.commcell.job_controller.get(test_boot_job_id)
        # self.logout()
        self.log.info('Waiting for Job [%s] to complete', test_boot_job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')
        self.test_failover.job_phase_validation(test_boot_job_id)

    @test_step
    def attach_network(self, test_vm_name):
        """Attaches NIC card to test boot VM"""

        self.dr_helper.source_auto_instance.hvobj.VMs = test_vm_name
        self.testboot_vm = self.dr_helper.source_auto_instance.hvobj.VMs[test_vm_name]
        self.testboot_vm.attach_network_adapter()
        sleep(150)
        self.testboot_vm.update_vm_info(force_update=True)
        self.testboot_vm.update_vm_info(prop="All")

    @test_step
    def test_diff(self):
        """Verifies the integrity of the test data on test booted VM"""
        self.test_failover.update_testfailovervm_details(self.testboot_options['test_vm_name'])
        self.test_failover.post_validation()

    @test_step
    def delete_testboot_vm(self, source_vm_name, testboot_vm_name):
        """Delete the current test boot VM"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.pair_details = self.continuous_monitor.access_pair_details(source_vm_name)
        self.pair_details.continuous_delete_testboot(self.testboot_options['test_vm_name'])

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def run(self):
        """Runs the testcase in order"""
        try:

            self.login()
            self.select_destination_option_grid()
            self.verify_pair_status(self.source_vm, self.destination_vm, "Re-syncing")
            self.select_destination_option_grid()
            self.check_pair_status('Replicating')

            self.select_destination_option_grid()
            self.verify_pair_status(self.source_vm, self.destination_vm, "Replicating")
            self.select_destination_option_grid()
            self.create_view(self.source_vm, self.destination_vm)

            self.write_temp_data()
            self.perform_resync()

            ### Perform test boot using Oldest point in time
            ### Wait for 5 mins for initial RP to get created
            self.admin_console.refresh_page()
            sleep(200)
            self.testboot_options['recovery_type'] = "Oldest point in time"
            self.perform_test_boot(self.testboot_options)
            sleep(150)
            self.attach_network(self.testboot_options['test_vm_name'])
            self.test_diff()

            self.delete_testboot_vm(self.source_vm, self.testboot_options['test_vm_name'])

            ### Perform test boot using Recovery point time
            ### Wait for 5 mins for initial RP to get created
            self.admin_console.refresh_page()
            self.write_temp_data()
            ### Wait for 6 mins for RP with the data added to get created
            sleep(600)
            self.get_rp_stats()
            self.testboot_options['recovery_point'] = self.rpstat_details1[-1]
            self.perform_test_boot(self.testboot_options)
            sleep(50)
            self.attach_network(self.testboot_options['test_vm_name'])
            self.test_diff()

            self.delete_testboot_vm(self.source_vm, self.testboot_options['test_vm_name'])

            ### Perform test boot using Application consistent recovery point time
            # #wait for 15 mins for initial ACRP to get created
            self.write_temp_data()
            self.admin_console.refresh_page()
            ### Wait for RP to get created
            sleep(900)
            self.get_rp_stats("Application consistent recovery point time")
            self.testboot_options['recovery_point'] = self.rpstat_details1[-1]
            self.testboot_options['recovery_type'] = "Application consistent recovery point time"
            self.perform_test_boot(self.testboot_options)
            sleep(50)
            self.attach_network(self.testboot_options['test_vm_name'])
            self.test_diff()

            self.delete_testboot_vm(self.source_vm, self.testboot_options['test_vm_name'])

            ### Perform test boot using Latest recovery point time
            ### Wait for 5 mins for initial RP to get created
            self.write_temp_data()
            self.admin_console.refresh_page()
            sleep(400)
            self.testboot_options['recovery_type'] = "Latest recovery point"
            self.perform_test_boot(self.testboot_options)
            sleep(50)
            self.attach_network(self.testboot_options['test_vm_name'])
            self.test_diff()

            self.delete_testboot_vm(self.source_vm, self.testboot_options['test_vm_name'])

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
