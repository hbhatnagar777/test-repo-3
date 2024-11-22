# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify vmware continuous replication CRUD operations

Sample input:
"60407": {
    "tenant_username": <username>,
    "tenant_password": <password>,
    "rpstorename":"RpStore name",
    "rpstorename_2":"second RpStore name",
    "datastore":"datastore name",
    "resource_pool":"resourcepool name",
    "source_vm_network":"source vm network name",
    "destination_network":"destination vm network name",
    "source_vm_network_2":"second source vm network name",
    "destination_network_2":"second destination vm network name",
    "recovery_target":"recovery target name",
    "Destination_host": "destination esx host name",
    "source_vms": "source vm's name list",
    "ClientName": "source hypervisor name",
    "destination_vms": "destination vm list"
    }
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, wait_for_condition
from Web.AdminConsole.DR.recovery_targets import RecoveryPointStore
from Web.AdminConsole.DR.monitor import ContinuousReplicationMonitor
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
import time
from time import sleep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)

        self.name = "Continuous Replication Group CRUD Test"
        self.replication_group = None
        self.replication_details = None
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "ClientName": None,
            "source_vms": [],
            "recovery_target": None,
            "rpstorename": None,
            "Destination_host": None
        }
        self.source_hypervisor = None
        self.recovery_target = None
        self.replication_group = None
        self.source_vms = None
        self.destination_vms = None
        self.datastore = None
        self.rpstorename = None
        self.rpstorename_2 = None
        self.resource_pool = None
        self.source_vm_network = None
        self.destination_network = None
        self.source_vm_network_2 = None
        self.destination_network_2 = None
        self.Destination_host = None
        self.vm_noedit_details = None
        self.view_name = "Crud_TC_view"
        self.ccrp_1 = "6 minutes"
        self.acrp_1 = "2 hours"
        self.ccrp_2 = "5 minutes"
        self.acrp_2 = "1 hours"
        self.default_recovery_options = {
            "ccrp_interval": "5 minutes",
            "acrp_interval": "1 hour",
            "merge_rp_interval": "2 days",
            "retain_rp_interval": "7 days",
            "end_of_retention": "6 Hour(s)",
            "switch_to_latest": "15 minutes",
            "off_peak_interval": "No"
        }
        self.changed_recovery_options = {
            "ccrp_interval": "6 minutes",
            "acrp_interval": "2 Hour(s)",
            "merge_rp_interval": "3 days",
            "retain_rp_interval": "8 days",
            "end_of_retention": "7 Hour(s)",
            "switch_to_latest": "18 minutes",
            "off_peak_interval": "No"
        }
        self.retention_options = {
            "retention": "7 days",
            "merge": True,
            "merge_delay": "2 days",
            "max_rp_interval": "6 hours",
            "max_rp_offline": "15 minutes",
            "off_peak_only": False
        }
        self.changed_retention_options = {
            "retention": "8 days",
            "merge": True,
            "merge_delay": "3 days",
            "max_rp_interval": "7 hours",
            "max_rp_offline": "18 minutes",
            "off_peak_only": False
        }

        self.browser = None
        self.admin_console = None
        self.replication_helper = None
        self.replication_group = None
        self.group_details = None
        self.replication_details = None
        self.edit_vm = None

        self.target_details = None
        self.dr_helper = None

        self.rpstore = None
        self.vm_groups = None
        self.continuous_monitor = None

    def setup(self):
        """Sets up the Testcase"""

        self.utils = TestCaseUtils(self)
        self.source_hypervisor = self.tcinputs["ClientName"]
        self.recovery_target = self.tcinputs["recovery_target"]
        self.source_vms = self.tcinputs["source_vms"]
        self.rpstorename = self.tcinputs["rpstorename"]
        self.rpstorename_2 = self.tcinputs["rpstorename2"]
        self.datastore = self.tcinputs["datastore"]
        self.resource_pool = self.tcinputs["resource_pool"]
        self.Destination_host = self.tcinputs["Destination_host"]
        self.source_vm_network = self.tcinputs["source_vm_network"]
        self.destination_network = self.tcinputs["destination_network"]
        self.source_vm_network_2 = self.tcinputs["source_vm_network_2"]
        self.destination_network_2 = self.tcinputs["destination_network_2"]
        self.target_details = self.commcell.recovery_targets.get(self.recovery_target)
        self.destination_vms = self.tcinputs["destination_vms"]

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
            self.admin_console.login(self.tcinputs['tenant_username'],
                                     self.tcinputs['tenant_password'])
            self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
            self.replication_group = ReplicationGroup(self.admin_console)

            self.replication_details = ReplicationDetails(self.admin_console)
            self.rpstore = RecoveryPointStore(self.admin_console)
            self.vm_groups = VMGroups(self.admin_console)
            self.continuous_monitor = ContinuousReplicationMonitor(self.admin_console)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    @test_step
    def verify_overview(self, group_name: str, source_hypervisor: str, recovery_target: str, vendor_name: str):
        """Verifies the details of the replication group in the overview tab"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(group_name)

        summary = self.replication_details.overview.get_summary_details()
        self.utils.assert_comparison(summary['Source'], source_hypervisor)
        self.utils.assert_comparison(summary['Recovery target'], recovery_target)
        self.utils.assert_comparison(summary['Destination vendor'], vendor_name)
        self.utils.assert_comparison(summary['Replication type'], "Continuous")
        self.utils.assert_comparison(summary['Enable replication'], "ON")

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

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

        self._log.info('Replication group [%s] exists and with correct information', group_name)

    def select_destination_option_grid(self):
        """select destination from actions grid on monitor page"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_grid_option("Destination")

    @test_step
    def verify_pair_status(self, source_vm, destination_vm, pair_status, after_edit=False):
        """Verify on replication monitor table if pair is replicating"""

        for vm in source_vm:
            self.admin_console.refresh_page()
            self.select_destination_option_grid()

            _, table_content = self.continuous_monitor.get_replication_group_details(vm,
                                                                                     destination_vm[source_vm.index(vm)])
            table_content = table_content[0]
            self.utils.assert_comparison(table_content['Source'], vm)
            self.utils.assert_comparison(table_content['Destination'], destination_vm[source_vm.index(vm)])
            if not after_edit:
                self.utils.assert_comparison(table_content['Recovery type'], "Point in time recovery")
                self.utils.assert_comparison(table_content['Recovery point store'], self.rpstorename)
            else:
                self.utils.assert_comparison(table_content['Recovery type'], "Latest recovery")
            self.utils.assert_comparison(table_content['Sync status'], pair_status)

    def check_pair_status(self, source_vm, destination_vm, expected):
        """Checks the sync status of the BLR pair with the expected value"""

        self.admin_console.navigator.navigate_to_continuous_replication()
        self.select_destination_option_grid()
        self.wait_for_sync_status(source_vm, destination_vm, expected)

    @wait_for_condition(timeout=900)
    def wait_for_sync_status(self, source_vm, destination_vm, expected):
        """Waits for the sync status to meet expected value"""

        return (self.continuous_monitor.sync_status(source_vm,
                                                    destination_vm) == expected)

    @test_step
    def create_view(self, source_vm, destination_vm, view_name):
        """"Create a replication view"""

        if self.continuous_monitor.has_replication_group(source_vm, destination_vm):
            if self.continuous_monitor.check_view(view_name):
                self.continuous_monitor.delete_view(view_name)
            self.continuous_monitor.create_view(view_name,
                                                {'Source': source_vm,
                                                 'Destination': destination_vm})
            self.continuous_monitor.select_view(view_name)

    @test_step
    def delete_replication_group(self):

        """Deletes the replication group if it exists already"""
        self.replication_helper.delete_replication_group(self.group_name)

    @test_step
    def verify_disabled_fields(self, vm_id):
        """Verifies that the disabled fields are disabled or not"""
        self.admin_console.refresh_page()
        check_fields = ['displayNamePrefixSuffix', 'destinationHost', 'dataStore', 'resourcePool', 'vmFolder']
        self.replication_helper.verify_disabled_fields(self.group_name, self.source_vms[vm_id - 1],
                                                       self.replication_helper.Vendors.VMWARE.value, check_fields)

    @test_step
    def disable_enable_replication_group(self):
        """Disables the replication group and re-enables it to verify the group status"""
        self.replication_helper.verify_disable_enable_replication_group(self.group_name, True)
        sleep(120)

    def verify_recovery_options(self, group_name: str, recovery_type: int, rpstore_name: str, expected_values: dict):
        """
        Verify the recovery options in configuration tab for VSA continuous replication
        recovery_type       (int): 0 for latest recovery or 1 for point in time recovery
        rpstore_name        (str): Specify the rp store name
        expected_values     (dict): Dictionary with values given below
            ccrp_interval       (str): Specify the interval of crash consistent RP eg: '4 Hour(s)'
            acrp_interval       (str): Specify the interval of application consistent RP eg: '4 Hour(s)'
            merge_rp_interval   (str): Specify the merge recovery points older than interval eg: '3 days'
            retain_rp_interval  (str): Specify retention period for RP eg '7 days'
            end_of_retention    (str): Specify RP interval at the end of retention eg '6 Hour(s)'
            switch_to_latest    (str): Specify interval for switch to latest recovery if RpStore is offline eg '15 minutes'
            off_peak_interval   (str): Specify 'Yes' if off-peak enabled else 'No'
        """
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(group_name)
        self.replication_details.access_configuration_tab()
        recovery_options_details = self.replication_details.configuration.get_recovery_options()
        recovery_options_details = list(recovery_options_details.values())
        self._log.info('Starting verification of values for recovery options in configuration tab')
        if recovery_type == 0:
            self.utils.assert_comparison(recovery_options_details[0], "Latest recovery")
            self._log.info('Successfully verified configuration tab details for latest recovery type')
        else:
            self.utils.assert_comparison(recovery_options_details[0], "Point in time recovery")
            self.utils.assert_comparison(recovery_options_details[1], rpstore_name)
            index = 2
            for key in expected_values.keys():
                self.utils.assert_comparison(recovery_options_details[index], expected_values[key])
                index = index + 1
            self._log.info('Successfully verified configuration tab details for point in time recovery type')

    def change_recovery_type(self, after_edit=False):
        """Changes the recovery type of replication group in the configuration tab"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)
        self.replication_details.access_configuration_tab()
        self.replication_details.configuration.edit_recovery_options()
        if after_edit:
            self.rpstore.select_recovery_type(0)
            sleep(120)
        else:
            self.rpstore.select_recovery_type(1)
            self.rpstore.select_store(self.rpstorename)
            self.rpstore.configure_intervals(self.ccrp_2, self.acrp_2)
            self.rpstore.configure_retention(self.retention_options["retention"],
                                             self.retention_options["merge"],
                                             self.retention_options["merge_delay"],
                                             self.retention_options["max_rp_interval"],
                                             self.retention_options["max_rp_offline"],
                                             self.retention_options["off_peak_only"])
        self.admin_console.click_button('Save')

    @test_step
    def verify_configuration(self):
        """Verifies the details of the replication group in the configuration tab"""

        self.replication_helper.add_delete_vm_to_group(self.group_name, self.source_vms[-1],
                                                       self.replication_helper.Vendors.VMWARE.value)
        self.verify_recovery_options(self.group_name, 1, self.rpstorename, self.default_recovery_options)
        self.admin_console.refresh_page()
        self.replication_details.configuration.edit_recovery_options()
        self.rpstore.select_store(self.rpstorename_2)
        self.rpstore.configure_intervals(self.ccrp_1, self.acrp_1)
        self.rpstore.configure_retention(self.changed_retention_options["retention"],
                                         self.changed_retention_options["merge"],
                                         self.changed_retention_options["merge_delay"],
                                         self.changed_retention_options["max_rp_interval"],
                                         self.changed_retention_options["max_rp_offline"],
                                         self.changed_retention_options["off_peak_only"])
        self.admin_console.click_button('Save')
        self.verify_recovery_options(self.group_name, 1, self.rpstorename_2, self.changed_recovery_options)
        sleep(200)
        self.replication_details.configuration.edit_recovery_options()
        self.rpstore.select_store(self.rpstorename)
        self.rpstore.configure_intervals(self.ccrp_2, self.acrp_2)
        self.rpstore.configure_retention(self.retention_options["retention"],
                                         self.retention_options["merge"],
                                         self.retention_options["merge_delay"],
                                         self.retention_options["max_rp_interval"],
                                         self.retention_options["max_rp_offline"],
                                         self.retention_options["off_peak_only"])
        self.admin_console.click_button('Save')

        source_vm_list = [self.source_vms[0], self.source_vms[1]]

        destination_vm_list = list()
        if self.target_details.vm_prefix:
            destination_vm_list = [f'{self.target_details.vm_prefix}{vm_name}'
                                   for vm_name in source_vm_list]
        elif self.target_details.vm_suffix:
            destination_vm_list = [f'{vm_name}{self.target_details.vm_suffix}'
                                   for vm_name in source_vm_list]

        self.destination_vms = destination_vm_list
        vm_details_expected = dict()

        for vm_name in source_vm_list:
            vm_details_expected[vm_name] = {
                "Destination host": self.target_details.destination_host,
                "Datastore": self.target_details.datastore,
            }

        self.replication_helper.verify_configuration_vm_details(group_name=self.group_name,
                                                                source_vms=source_vm_list,
                                                                destination_vms=destination_vm_list,
                                                                expected_content=vm_details_expected)

    @test_step
    def verify_replication_monitor(self, after_edit=False):
        """Verify replication monitor table contains configured replication group"""

        self.admin_console.navigator.navigate_to_continuous_replication()
        self.admin_console.refresh_page()
        self.select_destination_option_grid()
        index = 0
        for source_vm in self.source_vms[:-1]:
            _, table_content = self.continuous_monitor.get_replication_group_details(source_vm,
                                                                                     self.destination_vms[index])
            table_content = table_content[0]
            self.utils.assert_comparison(table_content['Source'], source_vm)
            self.utils.assert_comparison(table_content['Destination'], self.destination_vms[index])
            if after_edit:
                self.utils.assert_comparison(table_content['Recovery type'], "Latest recovery")
            else:
                self.utils.assert_comparison(table_content['Recovery type'], "Point in time recovery")
                self.utils.assert_comparison(table_content['Recovery point store'], self.rpstorename)
            self.utils.assert_comparison(table_content['Sync status'], "Replicating")
            index += 1

    @test_step
    def delete_pair(self, source_vm_name, destination_vm_name):
        """Deletes the pair and information if it exists"""

        self.admin_console.navigator.navigate_to_continuous_replication()
        self.select_destination_option_grid()
        if self.continuous_monitor.has_replication_group(source_vm_name, destination_vm_name):
            if self.continuous_monitor.check_view(self.view_name):
                self.continuous_monitor.delete_view(self.view_name)
            self.continuous_monitor.create_view(self.view_name, {'Source': source_vm_name,
                                                                 'Destination': destination_vm_name})
            self.continuous_monitor.select_view(self.view_name)
            self.continuous_monitor.delete_pair()
            self.continuous_monitor.delete_view(self.view_name)

    @test_step
    def verify_overview_vm_deletion(self):
        """Deletes the VM from the overview tab and checks to see if it works"""

        self.delete_pair(self.source_vms[1], self.destination_vms[1])
        sleep(100)
        self.admin_console.refresh_page()
        column_content = self.continuous_monitor.get_column_data("Source", True)
        if self.source_vms[1] not in column_content:
            self._log.info("Pair with source VM %s got deleted successfully on overview tab", self.source_vms[1])
        if self.source_vms[1] in column_content:
            raise CVTestStepFailure("Waited for 5 Minutes exiting as pair didn't get deleted ")

    @test_step
    def verify_deletion(self):
        """Verify replication group, vm group and schedules are deleted"""
        self.delete_replication_group()
        self.replication_helper.verify_group_deletion(self.group_name)

    @test_step
    def verify_edit_vm(self, after_edit=False, vm_id=1):
        """Verifies the data on the edit VM page"""
        self.admin_console.refresh_page()
        self.edit_vm = self.replication_helper.get_edit_vm_details(self.group_name,
                                                                   self.source_vms[vm_id - 1],
                                                                   self.replication_helper.Vendors.VMWARE.value)
        _source, _destination = self.edit_vm.get_network_settings()
        if vm_id == 2:
            self.utils.assert_comparison(self.vm_noedit_details[-2], _source)
            self.utils.assert_comparison(self.vm_noedit_details[-1], _destination)
        elif after_edit:
            self.utils.assert_comparison(self.source_vm_network_2, _source)
            self.utils.assert_comparison(self.destination_network_2, _destination)
        else:
            self.utils.assert_comparison(self.source_vm_network, _source)
            self.utils.assert_comparison(self.destination_network, _destination)
        self.edit_vm.cancel()

    @test_step
    def edit_vm_details(self, vm_id=1):
        """Modify the group details to check if the detail change is registered on Command Center"""
        edit_vm = self.replication_helper.get_edit_vm_details(
            self.group_name, self.source_vms[vm_id - 1],
            self.replication_helper.Vendors.VMWARE.value)
        edit_network = edit_vm.edit_network()
        edit_network.select_source_network(self.source_vm_network_2)
        edit_network.select_destination_network(self.destination_network_2)
        edit_network.save()

    @test_step
    def configure_replication_group(self):
        """Create a continuous replication group"""

        self.admin_console.navigator.navigate_to_replication_groups()
        vmware_configure = self.replication_group.configure_vmware()
        vmware_configure.content.set_name(self.group_name)
        for vm_name in self.source_vms[:-1]:
            vmware_configure.content.select_vm_from_browse_tree(self.source_hypervisor,
                                                                {"VMs and templates": [vm_name]})
        vmware_configure.next()
        vmware_configure.target.select_recovery_target(self.recovery_target)
        vmware_configure.target.select_continuous_replication_type()
        vmware_configure.next()
        self.rpstore.select_recovery_type(1)
        self.rpstore.select_store(self.rpstorename)
        self.rpstore.configure_intervals(self.ccrp_2, self.acrp_2)
        self.rpstore.configure_retention(self.retention_options["retention"],
                                         self.retention_options["merge"],
                                         self.retention_options["merge_delay"],
                                         self.retention_options["max_rp_interval"],
                                         self.retention_options["max_rp_offline"],
                                         self.retention_options["off_peak_only"])
        vmware_configure.next()
        override_options = vmware_configure.override_options.override_vms(self.source_vms[0])
        override_options.set_destination_host(self.Destination_host)
        override_options.select_datastore(self.datastore)
        override_options.select_resource_pool(self.resource_pool)
        edit_network = override_options.edit_network()

        edit_network.select_source_network(self.source_vm_network)
        edit_network.select_destination_network(self.destination_network)
        edit_network.save()

        self.admin_console.click_button('Save')
        self.vm_noedit_details = vmware_configure.override_options.get_vmware_details(
            self.source_vms[1]
        )
        self.vm_noedit_details[2] = self.vm_noedit_details[2].split(" ")[0]
        self.utils.assert_comparison(self.target_details.destination_host, self.vm_noedit_details[1])
        self.utils.assert_includes(self.target_details.datastore, self.vm_noedit_details[2])
        self.utils.assert_comparison(self.target_details.resource_pool, self.vm_noedit_details[3])
        vmware_configure.next()
        sleep(5)
        vmware_configure.finish()

    def run(self):
        """Runs the testcase in order"""
        try:

            self.login()

            self.delete_replication_group()
            self.configure_replication_group()

            self.verify_replication_group_exists(self.group_name, self.source_hypervisor, self.recovery_target)
            self.select_destination_option_grid()
            self.verify_pair_status(self.source_vms[:-1], self.destination_vms, "Re-syncing")
            self.select_destination_option_grid()
            self.create_view(self.source_vms[0], self.destination_vms[0], "Src_VM1_View")
            self.check_pair_status(self.source_vms[0], self.destination_vms[0], 'Replicating')
            self.create_view(self.source_vms[1], self.destination_vms[1], "Src_VM2_View")
            self.check_pair_status(self.source_vms[1], self.destination_vms[1], 'Replicating')

            self.verify_overview(self.group_name, self.source_hypervisor, self.recovery_target,
                                 self.replication_helper.Vendors.VMWARE.value)
            self.disable_enable_replication_group()

            self.select_destination_option_grid()
            self.verify_pair_status(self.source_vms[:-1], self.destination_vms, "Re-syncing")
            self.logout()
            sleep(900)
            self.login()
            self.select_destination_option_grid()
            self.check_pair_status(self.source_vms[0], self.destination_vms[0], 'Replicating')
            self.check_pair_status(self.source_vms[1], self.destination_vms[1], 'Replicating')

            self.verify_configuration()

            self.verify_disabled_fields(vm_id=1)
            self.verify_edit_vm(after_edit=False, vm_id=1)
            self.verify_disabled_fields(vm_id=2)
            self.verify_edit_vm(after_edit=False, vm_id=2)

            self.edit_vm_details()
            self.verify_disabled_fields(vm_id=1)
            self.verify_edit_vm(after_edit=True, vm_id=1)
            self.verify_disabled_fields(vm_id=2)
            self.verify_edit_vm(after_edit=True, vm_id=2)

            self.verify_replication_monitor(after_edit=False)

            self.change_recovery_type(after_edit=True)

            self.select_destination_option_grid()
            self.verify_pair_status(self.source_vms[:-1], self.destination_vms, "Re-syncing", True)
            self.logout()
            sleep(900)
            self.login()
            self.select_destination_option_grid()
            self.check_pair_status(self.source_vms[0], self.destination_vms[0], 'Replicating')
            self.check_pair_status(self.source_vms[1], self.destination_vms[1], 'Replicating')

            self.verify_replication_monitor(after_edit=True)
            self.verify_overview_vm_deletion()
            self.verify_deletion()

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
