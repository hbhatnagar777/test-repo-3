# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Live Sync IO: Restartability for Replication: Suspend, Resume, Stop and Start

Sample input:
"56741": {
    "rpstorename":"RpStore name",
    "datastore":"datastore name",
    "resource_pool":"resourcepool name",
    "source_vm_network":"source vm network name",
    "destination_network":"destination vm network name",
    "recovery_target":"recovery target name",
    "Destination_host": "destination esx host name",
    "source_vm": "source vm name",
    "ClientName": "source hypervisor name",
    }
"""

from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration.test_failover import TestFailover
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
import time
from time import sleep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)

        self.name = "Live Sync IO: Restartability for Replication: Suspend, Resume, Stop and Start"
        self.vm = None
        self.testboot_vm = None
        self.rpstat_details1 = None
        self.rpstat_details2 = None
        self.tcinputs = {
            "ClientName": None,
            "source_vm": None,
            "recovery_target": None,
            "rpstorename": None,
            "Destination_host": None,
            "datastore": None,
            "resource_pool": None,
            "source_vm_network": None,
            "destination_network": None,
        }
        self.source_hypervisor = None
        self.recovery_target = None
        self.replication_group = None
        self.source_vm = None
        self.dr_helper = None
        self.destination_vm = None
        self.datastore = None
        self.rpstorename = None
        self.test_data_path = list()
        self.resource_pool = None
        self.source_vm_network = None
        self.destination_network = None
        self.Destination_host = None
        self.vm_noedit_details = None
        self.test_failover = None
        self.local_testdata_path = None
        self.controller = Machine()
        self.view_name = "56741_TC_view"
        self.ccrp_2 = "5 minutes"
        self.acrp_2 = "1 hours"
        self.testboot_options = {
            "test_vm_name": "Automation56741_TestVm",
            "expiration_time": "0:2",
            "recovery_type": "Recovery point time",
            "recovery_point": ""
        }
        self.retention_options = {
            "retention": "7 days",
            "merge": True,
            "merge_delay": "2 days",
            "max_rp_interval": "6 hours",
            "max_rp_offline": "15 minutes",
            "off_peak_only": False
        }

    def setup(self):
        """Sets up the Testcase"""

        self.utils = TestCaseUtils(self)
        self.source_hypervisor = self.tcinputs["ClientName"]
        self.recovery_target = self.tcinputs["recovery_target"]
        self.source_vm = self.tcinputs["source_vm"]
        self.rpstorename = self.tcinputs["rpstorename"]
        self.datastore = self.tcinputs["datastore"]
        self.resource_pool = self.tcinputs["resource_pool"]
        self.Destination_host = self.tcinputs["Destination_host"]
        self.source_vm_network = self.tcinputs["source_vm_network"]
        self.destination_network = self.tcinputs["destination_network"]
        self.target_details = self.commcell.recovery_targets.get(self.recovery_target)

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
            self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
            self.replication_group = ReplicationGroup(self.admin_console)
            self.rpstore = RpstoreOperations(self.admin_console)
            self.configure_rpstore = RecoveryPointStore(self.admin_console)
            self.vm_groups = VMGroups(self.admin_console)
            self.continuous_monitor = ContinuousReplicationMonitor(self.admin_console)
            self.dr_helper = DRHelper(self.commcell, self.csdb, self.client)
            self.dr_helper.source_auto_instance.hvobj.VMs = self.tcinputs['source_vm']
            self.vm = self.dr_helper.source_auto_instance.hvobj.VMs[self.tcinputs['source_vm']]
            self.vm.update_vm_info(prop="All")

        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    @test_step
    def delete_replication_group(self):
        """Deletes the replication group if it exists already"""
        self.replication_helper.delete_replication_group(self.group_name)

    @test_step
    def configure_replication_group(self):
        """Create a continuous replication group"""

        self.admin_console.navigator.navigate_to_replication_groups()
        vmware_configure = self.replication_group.configure_vmware()
        vmware_configure.content.set_name(self.group_name)

        vmware_configure.content.select_vm_from_browse_tree(self.source_hypervisor,
                                                            {"VMs and templates": [self.source_vm]})
        vmware_configure.next()
        vmware_configure.target.select_recovery_target(self.recovery_target)
        vmware_configure.target.select_continuous_replication_type()
        vmware_configure.next()
        self.configure_rpstore.select_recovery_type(1)
        self.configure_rpstore.select_store(self.rpstorename)
        self.configure_rpstore.configure_intervals(self.ccrp_2, self.acrp_2)
        self.configure_rpstore.configure_retention(self.retention_options["retention"],
                                         self.retention_options["merge"],
                                         self.retention_options["merge_delay"],
                                         self.retention_options["max_rp_interval"],
                                         self.retention_options["max_rp_offline"],
                                         self.retention_options["off_peak_only"])
        vmware_configure.next()
        override_options = vmware_configure.override_options.override_vms(self.source_vm)
        override_options.set_destination_host(self.Destination_host)
        override_options.select_datastore(self.datastore)
        override_options.select_resource_pool(self.resource_pool)
        edit_network = override_options.edit_network()
        edit_network.select_source_network(self.source_vm_network)
        edit_network.select_destination_network(self.destination_network)
        edit_network.save()
        self.admin_console.click_button('Save')
        self.vm_noedit_details = vmware_configure.override_options.get_vmware_details(
            self.source_vm
        )
        self.vm_noedit_details[2] = self.vm_noedit_details[2].split(" ")[0]
        self.utils.assert_comparison(self.target_details.destination_host, self.vm_noedit_details[1])
        self.utils.assert_includes(self.target_details.datastore, self.vm_noedit_details[2])
        self.utils.assert_comparison(self.target_details.resource_pool, self.vm_noedit_details[3])
        vmware_configure.next()
        sleep(5)
        vmware_configure.finish()

    @test_step
    def verify_replication_group_exists(self, group_name, source_hypervisor, target_name):
        """
        Verifies that the replication group exists
        """
        self.admin_console.navigator.navigate_to_replication_groups()
        self.admin_console.refresh_page()

        if not self.replication_group.has_group(group_name):
            raise CVTestStepFailure(f'Replication group [{group_name}] does not exist')
        group_row = self.replication_group.get_replication_group_details_by_name(group_name)
        self.utils.assert_comparison(group_row['Group name'][0], group_name)
        self.utils.assert_comparison(group_row['Source'][0], source_hypervisor)
        self.utils.assert_comparison(group_row['Destination'][0], target_name)
        self.utils.assert_comparison(group_row['Type'][0], 'VM - hot site')
        self.utils.assert_comparison(group_row['Replication type'][0], 'Continuous')
        self.utils.assert_comparison(group_row['State'][0], 'Enabled')

        self.test_failover = TestFailover(self.commcell, self.group_name, [self.source_vm])
        self._log.info('Replication group [%s] exists and with correct information', group_name)

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    @test_step
    def get_all_destination_vms(self):
        """Gets the destination VM Name"""
        destination_vm = None
        if self.target_details.vm_prefix:
            destination_vm = f'{self.target_details.vm_prefix}{self.source_vm}'

        elif self.target_details.vm_suffix:
            destination_vm = f'{self.source_vm}{self.target_details.vm_suffix}'

        self.destination_vm = destination_vm

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

    @wait_for_condition(timeout=500)
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
    def write_temp_data(self):
        """Writes data to the virtual machine

        Args:
            dir_name: Name of directory to be created on source VM

            dir_count: No of directories

            file_count: No of files per directory

            file_size: size of file

        """
        self.test_failover.pre_validation()

    @test_step
    def get_rp_stats(self, after_edit=False):
        """Get list of RP store points for point in time boot operations"""

        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_view(self.view_name)
        if after_edit:
            self.rpstat_details2 = self.rpstore.get_all_rp_stats()
        else:
            self.rpstat_details1 = self.rpstore.get_all_rp_stats()

    @test_step
    def suspend_pair(self):
        """Suspends a replication pair"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_view(self.view_name)
        self.continuous_monitor.suspend()

    @test_step
    def verify_resume(self):
        """Performs a resume operation"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_view(self.view_name)
        self.continuous_monitor.resume()
        self.check_pair_status('Replicating')

    @test_step
    def verify_stop(self):
        """Performs a stop operation"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_view(self.view_name)
        self.continuous_monitor.stop()
        self.check_pair_status('Stopped')

    @test_step
    def verify_start(self):
        """Performs a stop operation"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_view(self.view_name)
        self.continuous_monitor.start()
        sleep(200)
        self.check_pair_status('Replicating')

    @test_step
    def compare_rps(self, rpstat_details1, rpstat_details2):
        """Compare the Rp's after Suspended state"""
        check_rp = all(rp_stat in rpstat_details2 for rp_stat in rpstat_details1)
        if check_rp is True:
            self.log.info("Verified successfully RP's before suspended state match RP's after resume")
        else:
            raise Exception("Before suspended state RP's doesn't match after resume state")

    @test_step
    def perform_test_boot(self, testboot_options):
        """Perform test boot on the destination VM"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_view(self.view_name)
        test_boot_job_id = self.continuous_monitor.continuous_test_bootvm(testboot_options)
        job_obj = self.commcell.job_controller.get(test_boot_job_id)
        self.logout()
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
        self.testboot_vm.update_vm_info(force_update=True)
        self.testboot_vm.update_vm_info(prop="All")

    @test_step
    def test_diff(self):
        """Verifies the integrity of the test data on test booted VM"""
        self.test_failover.post_validation()
        self.log.info("Successfully replicated all test data to Boot VM.")

    @test_step
    def create_data(self):
        """Creates the test data on VM"""
        self.blr_helper.write_temp_data("DataSet1", 1, 1, 10)
        self.log.info("Test Data creation completed. Waiting for 1.5 mins for RP to get created")
        time.sleep(90)

    @wait_for_condition(timeout=300)
    def wait_for_sync_status(self, expected):
        """Waits for the sync status to meet expected value"""
        return (self.continuous_monitor.sync_status(self.tcinputs['source_vm'],
                                                    self.destination_vm) == expected)

    def run(self):
        """Runs the testcase in order"""
        try:

            self.login()
            self.delete_replication_group()

            self.configure_replication_group()
            self.verify_replication_group_exists(self.group_name, self.source_hypervisor, self.recovery_target)

            self.get_all_destination_vms()
            self.select_destination_option_grid()
            self.verify_pair_status(self.source_vm, self.destination_vm, "Re-syncing")
            self.check_pair_status('Replicating')
            self.select_destination_option_grid()
            self.verify_pair_status(self.source_vm, self.destination_vm, "Replicating")
            self.create_view(self.source_vm, self.destination_vm)

            # # wait for 5 mins for RP's to get created
            sleep(300)
            self.admin_console.refresh_page()
            self.write_temp_data()
            # # Wait for 6 mins for RP's to get created
            sleep(400)
            self.get_rp_stats(after_edit=False)
            self.suspend_pair()
            self.check_pair_status('Suspended')
            sleep(300)
            self.verify_resume()
            sleep(200)
            self.get_rp_stats(after_edit=True)
            self.compare_rps(self.rpstat_details1, self.rpstat_details2)
            self.testboot_options['recovery_point'] = self.rpstat_details1[2]
            self.perform_test_boot(self.testboot_options)
            sleep(50)
            self.attach_network(self.testboot_options['test_vm_name'])
            self.test_diff()
            self.verify_stop()
            self.write_temp_data()
            sleep(100)
            self.verify_start()
            sleep(400)
            self.get_rp_stats(after_edit=False)
            sleep(300)
            self.testboot_options['recovery_point'] = self.rpstat_details1[2]
            self.perform_test_boot(self.testboot_options)
            sleep(50)
            self.attach_network(self.testboot_options['test_vm_name'])
            self.test_diff()
            self.delete_replication_group()

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
