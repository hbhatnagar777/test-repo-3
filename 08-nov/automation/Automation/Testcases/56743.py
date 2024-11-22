# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify vmware continuous replication CRUD operations

Sample input:
"56743": {
    "rpstorename":"RpStore name",
    "datastore":"datastore name",
    "src_client_name":"Source Client Name",
    "dest_client_name":"Dest client name"
    "resource_pool":"resourcepool name",
    "source_vm_network":"source vm network name",
    "destination_network":"destination vm network name",
    "recovery_target":"recovery target name",
    "Destination_host": "destination esx host name",
    "source_vm": "source vm name",
    "ClientName": "source hypervisor name",
    "storage_name": "storage name",
    }
"""

from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration.test_failover import TestFailover
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, wait_for_condition
from Web.AdminConsole.DR.monitor import ContinuousReplicationMonitor
from VirtualServer.VSAUtils import VirtualServerUtils
from AutomationUtils.machine import Machine
from VirtualServer.VSAUtils import VirtualServerHelper
from Web.AdminConsole.DR.rp_store import RpstoreOperations
from Web.AdminConsole.DR.recovery_targets import RecoveryPointStore
import time
from time import sleep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)

        self.name = "Live Sync IO: Restartability for Replication: services restart @ Head and @ Tail"
        self.vm = None
        self.testboot_vm = None
        self.rpstat_details1 = None
        self.tcinputs = {
            "ClientName": None,
            "source_vm": None,
            "recovery_target": None,
            "storage_name": None,
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
        self.destination_vm = None
        self.datastore = None
        self.rpstorename = None
        self.storage_name = None
        self.test_data_path = list()
        self.resource_pool = None
        self.source_vm_network = None
        self.destination_network = None
        self.Destination_host = None
        self.vm_noedit_details = None
        self.local_testdata_path = None
        self.controller = Machine()
        self.test_failover = None
        self.view_name = "56743_TC_view"
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
        self.storage_name = self.tcinputs["storage_name"]
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
            self.continuous_monitor = ContinuousReplicationMonitor(self.admin_console)
            self.commcell_object = self.commcell
            self.configure_rpstore = RecoveryPointStore(self.admin_console)
            self.auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            self.auto_client = VirtualServerHelper.AutoVSAVSClient(self.auto_commcell, self.client)
            self.auto_instance = VirtualServerHelper.AutoVSAVSInstance(self.auto_client, self.agent, self.instance)
            self.auto_instance.hvobj.VMs = self.tcinputs['source_vm']
            self.hypervisor = self.auto_instance.hvobj
            self.vm = self.hypervisor.VMs[self.tcinputs['source_vm']]
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
        # vmware_configure.storage_cache.select_continuous_storage(self.storage_name)
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

    def select_destination_option_grid(self):
        """select destination from actions grid on monitor page"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_grid_option("Destination")

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

        self.test_failover = TestFailover(self.commcell, self.group_name)
        self._log.info('Replication group [%s] exists and with correct information', group_name)

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    @test_step
    def wait_for_job(self, job_type, client_name=None):
        """Wait for BLR Jobs to complete.
        """
        _job_id = 0
        wait_counter = 0
        while not bool(_job_id):
            wait_counter += 1
            if wait_counter <= 89:
                self._log.info("Waiting for %s Job to Launch. Sleep for 10 seconds.", job_type)
                time.sleep(10)
                self._log.info("Fetching %s Job", job_type)
                if job_type == "Block Level Operation":
                    self.jobs = self.commcell.job_controller.active_jobs()
                else:
                    self.jobs = self.commcell.job_controller.active_jobs(client_name)
                self._log.info("Active Jobs on %s: %s", client_name, self.jobs)
                _job_id = self.get_job(self.jobs, job_type)
                self.log.info("Job Id: %s", _job_id)
            else:
                self.log.error(" %s Job was not launched even after 15 mins of wait time.", job_type)
                return False
        self._job_id = _job_id
        job_obj = self.commcell.job_controller.get(self._job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')

    def get_job(self, job, job_type):
        """Get List of Jobs matching a given Job Type
        """

        _job_ids = list(job.keys())
        for _job_id in _job_ids:
            _job_details = job[_job_id]
            if _job_details['operation'] == job_type:
                if "Backup" in job_type:
                    self.blr_subclientid = _job_details['subclient_id']
                return _job_id
        return 0

    @test_step
    def get_all_destination_vms(self):
        """Gets the destination VM Name"""
        destination_vm = None
        if self.target_details.vm_prefix:
            destination_vm = f'{self.target_details.vm_prefix}{self.source_vm}'

        elif self.target_details.vm_suffix:
            destination_vm = f'{self.source_vm}{self.target_details.vm_suffix}'

        self.destination_vm = destination_vm

    @test_step
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

    @test_step
    def create_view(self, source_vm, destination_vm):
        """"Create a replication view"""
        if self.continuous_monitor.has_replication_group(source_vm, destination_vm):
            if self.continuous_monitor.check_view(self.view_name):
                self.continuous_monitor.delete_view(self.view_name)
            self.continuous_monitor.create_view(self.view_name,
                                                {'Source': source_vm,
                                                 'Destination': destination_vm})
            self.continuous_monitor.select_view(self.view_name)

    @test_step
    def write_temp_data(self, is_replicating):
        """Writes data to the virtual machine

        Args:
            dir_name: Name of directory to be created on source VM

            dir_count: No of directories

            file_count: No of files per directory

            file_size: size of file

        """
        self.test_failover.pre_validation(is_replicating)

    @test_step
    def get_rp_stats(self):
        """Get list of RP store points for point in time boot operations"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_view(self.view_name)
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

    def check_pair_status(self, expected):
        """Checks the sync status of the BLR pair with the expected value"""
        self.wait_for_sync_status(expected)

    @wait_for_condition(timeout=300)
    def wait_for_sync_status(self, expected):
        """Waits for the sync status to meet expected value"""
        return (self.continuous_monitor.sync_status(self.tcinputs['source_vm'],
                                                    self.destination_vm) == expected)

    @test_step
    def compare_rps(self, rpstat_details1, rpstat_details2):
        """Compare the Rp's after Suspended state"""
        check_rp = all(rp_stat in rpstat_details2 for rp_stat in rpstat_details1)
        if check_rp is True:
            self.log.info("Verified successfully RP's before suspended state match RP's after resume")
        else:
            self.log.info("Before suspended state RP's doesn't match after resume state ")

    @test_step
    def perform_test_boot(self, source_vm, group_name, testboot_options):
        """Perform test boot on the destination VM"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_view(self.view_name)
        self.select_destination_option_grid()
        test_boot_job_id = self.continuous_monitor.continuous_test_bootvm(source_vm, group_name, testboot_options)
        job_obj = self.commcell.job_controller.get(test_boot_job_id)
        self.logout()
        self.log.info('Waiting for Job [%s] to complete', test_boot_job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')
        self.test_failover.job_phase_validation(test_boot_job_id)

    @test_step
    def attach_network(self, test_vm_name):
        """Attaches NIC card to test boot VM"""
        self.auto_instance.hvobj.VMs = test_vm_name
        self.hypervisor = self.auto_instance.hvobj
        self.testboot_vm = self.hypervisor.VMs[test_vm_name]
        self.testboot_vm.attach_network_adapter()
        self.testboot_vm.update_vm_info(prop="All")

    @test_step
    def test_diff(self):
        """Verifies the integrity of the test data on test booted VM"""
        self.test_failover.post_validation()
        self.log.info("Successfully replicated all test data to Boot VM.")

    @test_step
    def verify_deletion(self):
        """Verify replication group, vm group and schedules are deleted"""
        self.delete_replication_group()
        self.replication_helper.verify_group_deletion(self.group_name)

    @test_step
    def delete_pair(self, source_vm_name, destination_vm_name):
        """Deletes the pair and information if it exists"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        if self.continuous_monitor.has_replication_group(source_vm_name, destination_vm_name):
            if self.continuous_monitor.check_view(self.view_name):
                self.continuous_monitor.delete_view(self.view_name)
            self.continuous_monitor.create_view(self.view_name, {'Source': source_vm_name,
                                                                 'Destination': destination_vm_name})
            self.continuous_monitor.select_view(self.view_name)
            self.continuous_monitor.delete_pair()
            self.continuous_monitor.delete_view(self.view_name)

    @test_step
    def restart_client_services(self, client_name):
        """test"""
        self.client = self.commcell_object.clients.get(client_name)
        self.client.restart_services(True)

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
            self.restart_client_services(self.tcinputs["src_client_name"])
            self.restart_client_services(self.tcinputs["dest_client_name"])

            self.write_temp_data(False)
            # Wait for services to start again
            sleep(40)
            self.select_destination_option_grid()
            self.verify_pair_status(self.source_vm, self.destination_vm, "Re-syncing")
            self.check_pair_status('Replicating')
            self.restart_client_services(self.tcinputs["src_client_name"])
            self.restart_client_services(self.tcinputs["dest_client_name"])
            self.write_temp_data(True)
            self.select_destination_option_grid()
            self.check_pair_status('Replicating')

            self.select_destination_option_grid()
            self.create_view(self.source_vm, self.destination_vm)
            # wait for 5 mins for RP's to get created
            sleep(300)
            self.admin_console.refresh_page()
            self.get_rp_stats()
            self.testboot_options['recovery_point'] = self.rpstat_details1[-1]
            self.perform_test_boot(self.testboot_options, self.source_vm, self.destination_vm)
            sleep(100)
            self.attach_network(self.testboot_options['test_vm_name'])
            self.test_diff()
            self.verify_deletion()

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
