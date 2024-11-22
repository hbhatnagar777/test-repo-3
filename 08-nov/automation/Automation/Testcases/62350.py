# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: This test case verifies that the vmware replication ip customization works properly for both linux and
windows vms by verifying in the backend

TestCase: Class for executing this test case
Sample JSON: {
        "ClientName": "idc",
        "source_vms": ["vm1", "vm2"],
        "recovery_target": "target",
        "dns_1": "<destination machine dns primary>",
        "dns_2": "<destination machine dns secondary>",
}
"""
from time import sleep

import ipaddress
from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration._dr_operation import auto_instance_factory
from DROrchestration import UnplannedFailover, Failback
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils.VirtualServerUtils import validate_ipv4
from VirtualServer.VSAUtils.VMHelpers.VmwareVM import VmwareVM
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.virtualization_replication import SOURCE_HYPERVISOR_VMWARE
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep, wait_for_condition


class TestCase(CVTestCase):
    """This testcase is used to verify ip customization for linux and windows vmware vms"""
    test_step = TestStep()
    _HOSTNAME_1 = 'DestVMHost1'
    _HOSTNAME_2 = 'DestVMHost2'

    def __init__(self):
        """Initialises the objects and TC inputs"""
        super().__init__()
        self.name = "VMWare: IP customization verification (Windows proxy + FREL)"

        self.tcinputs = {
            "ClientName": None,
            "source_vms": [],
            "recovery_target": None,
        }
        self.source_hypervisor = None
        self.source_vms = None
        self.recovery_target = None
        self.storage_name = None
        self.dns_1 = None
        self.dns_2 = None

        self.utils = None

        self.vm_details = None
        self.destination_ips = {}

        self.browser = None
        self.admin_console = None
        self.replication_helper = None
        self.replication_group = None
        self.group_details = None

        self.unplanned_failover = None
        self.failback = None

    @property
    def group_name(self):
        """Returns the virtualization group name"""
        return ReplicationHelper.group_name(self.id)

    def wait_for_vm_to_boot(self, vm_obj, powered_off_failure=True):
        """
        Waits for VM to boot without having to wait for 15 minutes for a ping-able IP address
        vm_obj:              HypervisorVM object for the VM to be fetching IP for
        powered_off_failure: boolean for when powered off state should raise error
                                starts VM if it is powered off and failure is False
        """
        if powered_off_failure and vm_obj.power_state == 'poweredOff':
            # Raise exception if powered off is supposed to return failure here
            raise CVTestStepFailure(f'VM [{vm_obj.vm_name}] is not powered on')
        if not powered_off_failure:
            # If powered off failure is not True, power on VM
            vm_obj.power_on()
        for _ in range(15):
            # get VM IP and verify it is IPv4 and isn't self assigned
            vm_obj.update_vm_info(force_update=True)
            if validate_ipv4(vm_obj.ip):
                break
            self.log.info('Could not get IP for VM [%s] due to reason: Self assigned IP address for VM', vm_obj.vm_name)
            self.log.info('Waiting for 1 minute before trying again')
            sleep(60)
        else:
            raise Exception(f'Could not get VM [{vm_obj.vm_name}] to boot')

    def get_source_vm_details(self):
        """Gets the source VM ip address information from the hypervisor"""
        vm_details = {}
        source_instance = self.client.agents.get('virtual server').instances.get('vmware')
        source_auto_instance = auto_instance_factory(source_instance)
        for vm_name in self.source_vms:
            vm_obj = VmwareVM(source_auto_instance.hvobj, vm_name, vm_boot_skip=True)
            self.wait_for_vm_to_boot(vm_obj, powered_off_failure=False)
            gateway = [gateway_ip for gateway_ip in vm_obj.guest_default_gateways if '.' in gateway_ip]
            vm_details[vm_name] = {"ip_address": vm_obj.ip,
                                   "subnet_mask": vm_obj.guest_subnet_mask,
                                   "default_gateway": gateway[0]}
        return vm_details

    def login(self):
        """Logs in to admin console"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, machine=self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
        self.replication_group = ReplicationGroup(self.admin_console)
        self.group_details = ReplicationDetails(self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.utils = TestCaseUtils(self)
            self.source_hypervisor = self.tcinputs['ClientName']
            self.source_vms = self.tcinputs['source_vms']
            self.recovery_target = self.tcinputs['recovery_target']
            self.dns_1 = self.tcinputs.get('dns_1', '')
            self.dns_2 = self.tcinputs.get('dns_2', '')

            self.vm_details = self.get_source_vm_details()
        except Exception as exp:
            raise CVTestCaseInitFailure('Failed to initialise testcase') from exp

    @test_step
    def delete_replication_group(self):
        """Deletes the replication group if it exists already"""
        self.replication_helper.delete_replication_group(self.group_name, self.source_vms)

    @test_step
    def configure_replication_group(self):
        """Configures the replication group with default options"""
        vmware_configure = self.replication_group.configure_vmware()
        vmware_configure.content.set_name(self.group_name)
        for vm_name in self.source_vms:
            vmware_configure.content.select_vm_from_browse_tree(self.source_hypervisor,
                                                                {"VMs and templates": [vm_name]})
        sleep(5)
        vmware_configure.next()

        vmware_configure.target.select_recovery_target(self.recovery_target)
        vmware_configure.target.select_continuous_replication_type()
        vmware_configure.next()

        vmware_configure.storage_cache.continuous_rpstore.select_recovery_type(0)
        vmware_configure.next()

        for vm_name in self.source_vms:
            override_vm = vmware_configure.override_options.override_vms(vm_name)

            override_vm.set_hostname(self._HOSTNAME_1)
            ip_settings = override_vm.add_ip()
            # The source IP address must be set static in the operating system
            source_ip = self.vm_details[vm_name]
            ip_settings.set_source_ip(source_ip['ip_address'],
                                      source_ip['subnet_mask'],
                                      source_ip['default_gateway'])
            ip_settings.toggle_dhcp(enable=True)
            ip_settings.save()

            override_vm.save()
            vmware_configure.override_options.deselect_vms(vm_name)
        vmware_configure.next()

        sleep(5)
        vmware_configure.finish()

    @wait_for_condition(timeout=7200)
    def wait_for_sync_status(self, blr_pair, expected):
        """Waits for the sync status to meet expected value"""
        blr_pair.refresh()
        return blr_pair.pair_status.name.upper() == expected

    @test_step
    def verify_group_creation(self):
        """Verifies that the group has been configured with the correct settings in the command center"""
        if not self.replication_group.has_group(self.group_name):
            raise CVTestStepFailure(f"Group [{self.group_name}] does not exist on the replication groups page")
        self.replication_group.access_group(self.group_name)
        self.group_details.access_configuration_tab()

        for vm_name in self.source_vms:
            override_vm = self.group_details.configuration.edit_virtual_machines(vm_name,
                                                                                 vm_type=SOURCE_HYPERVISOR_VMWARE)
            self.utils.assert_comparison(override_vm.hostname, self._HOSTNAME_1)

            ip_settings = override_vm.edit_ip()
            source_ip = ip_settings.source_ip
            expected_source_ip = self.vm_details[vm_name]
            self.utils.assert_comparison(source_ip['sourceIpAddress'], expected_source_ip['ip_address'])
            self.utils.assert_comparison(source_ip['sourceSubnetMask'], expected_source_ip['subnet_mask'])
            self.utils.assert_comparison(source_ip['sourceDefaultGateway'], expected_source_ip['default_gateway'])
            self.utils.assert_comparison(ip_settings.dhcp_enabled, True)

            ip_settings.cancel()
            override_vm.cancel()
            self.group_details.configuration.deselect_vms([vm_name])

    @test_step
    def verify_sync_completion(self):
        """Verifies that the sync has completed on the created replication group"""
        self.log.info('Waiting for 2 minutes to let live sync update')
        sleep(120)
        self.unplanned_failover = UnplannedFailover(self.commcell, self.group_name)
        self.failback = Failback(self.commcell, self.group_name)
        for vm_pair_dict in self.unplanned_failover.vm_pairs.values():
            blr_pair = list(vm_pair_dict.values())[0].vm_pair
            self.log.info('Waiting for %s to sync', str(blr_pair))
            self.wait_for_sync_status(blr_pair, 'REPLICATING')

    @test_step
    def perform_failover(self):
        """Performs unplanned failover on the replication group"""

        self.unplanned_failover.refresh(hard_refresh=True)
        self.failback.refresh()
        self.unplanned_failover.pre_validation()
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)
        self.admin_console.refresh_page()
        job_id = self.group_details.unplanned_failover()
        self.log.info('Waiting for failover job id %s to complete', job_id)
        job = self.commcell.job_controller.get(job_id)
        job.wait_for_completion()
        self.utils.assert_comparison(job.status, 'Completed')

    @test_step
    def perform_failback(self):
        """Performs failback on the replication group"""
        self.failback.pre_validation()
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)
        job_id = self.group_details.failback()
        self.log.info('Waiting for failback job id %s to complete', job_id)
        job = self.commcell.job_controller.get(job_id)
        job.wait_for_completion()
        self.utils.assert_comparison(job.status, 'Completed')

    @test_step
    def verify_failover(self, dhcp=False):
        """Verifies that the DHCP failover has IP customization set"""
        self.unplanned_failover.post_validation()
        for source_vm in self.source_vms:
            dest_vm_obj = self.unplanned_failover.vm_pairs[source_vm]['Failover'].destination_vm.vm
            dest_vm_obj.update_vm_info(force_update=True)

            destination_ip = {"ip_address": dest_vm_obj.ip,
                              "subnet_mask": dest_vm_obj.guest_subnet_mask,
                              "default_gateway": [gateway_ip for gateway_ip in dest_vm_obj.guest_default_gateways
                                                  if '.' in gateway_ip][0]}
            if dhcp:
                self.destination_ips[source_vm] = destination_ip

    @test_step
    def verify_failback(self):
        """Verifies that the DRVM on failback has reverted ip customization"""
        self.failback.post_validation()

    @test_step
    def edit_group_static(self):
        """Sets static IP for the group with source and destination values"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)
        self.group_details.access_configuration_tab()

        for vm_name in self.source_vms:
            edit_vm = self.group_details.configuration.edit_virtual_machines(vm_name,
                                                                             vm_type=SOURCE_HYPERVISOR_VMWARE)
            edit_vm.set_hostname(self._HOSTNAME_2)

            ip_settings = edit_vm.edit_ip()
            ip_settings.toggle_dhcp(enable=False)
            ip_settings.set_destination_ip(self.destination_ips[vm_name]['ip_address'],
                                           self.destination_ips[vm_name]['subnet_mask'],
                                           self.destination_ips[vm_name]['default_gateway'],
                                           self.tcinputs.get('dns_1'),
                                           self.tcinputs.get('dns_2'))

            ip_settings.save()
            edit_vm.save()
            self.group_details.configuration.deselect_vms([vm_name])

    @test_step
    def verify_static_ip(self):
        """Verifies that the correct VM ip settings are set on the destination VM"""
        sleep(10)
        for vm_name in self.source_vms:
            edit_vm = self.group_details.configuration.edit_virtual_machines(vm_name,
                                                                             vm_type=SOURCE_HYPERVISOR_VMWARE)
            self.utils.assert_comparison(edit_vm.hostname, self._HOSTNAME_2)

            ip_settings = edit_vm.edit_ip(0)
            destination_ip = ip_settings.destination_ip
            expected_ip = self.destination_ips[vm_name]
            self.utils.assert_comparison(destination_ip['destinationIpAddress'], expected_ip['ip_address'])
            self.utils.assert_comparison(destination_ip['destinationSubnetMask'], expected_ip['subnet_mask'])
            self.utils.assert_comparison(destination_ip['destinationDefaultGateway'], expected_ip['default_gateway'])
            self.utils.assert_comparison(destination_ip['destinationPrefDnsServer'], self.dns_1)
            self.utils.assert_comparison(destination_ip['destinationAltDnsServer'], self.dns_2)

            ip_settings.cancel()
            edit_vm.cancel()
            self.group_details.configuration.deselect_vms([vm_name])

    def run(self):
        """Runs the testcase in order"""
        try:
            self.login()
            self.delete_replication_group()
            self.configure_replication_group()
            self.verify_group_creation()

            self.logout()
            self.verify_sync_completion()

            self.login()
            self.perform_failover()
            self.logout()
            self.verify_failover(dhcp=True)

            self.login()
            self.perform_failback()
            self.logout()
            self.verify_failback()

            self.login()
            self.edit_group_static()
            self.verify_static_ip()

            self.perform_failover()
            self.logout()
            self.verify_failover(dhcp=False)

            self.login()
            self.perform_failback()
            self.logout()
            self.verify_failback()

            self.login()
            self.delete_replication_group()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the testcase on terminate"""
        self.logout()
