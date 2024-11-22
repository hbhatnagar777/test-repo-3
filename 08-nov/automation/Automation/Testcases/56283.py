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
        "storage_name" : "storage",
        "dns_1": "<destination machine dns primary>",
        "dns_2": "<destination machine dns secondary>",
}
"""
import ipaddress

from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration.replication import Replication
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils.VMHelpers.VmwareVM import VmwareVM
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.virtualization_replication import SOURCE_HYPERVISOR_VMWARE
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper, DRHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from DROrchestration.DRUtils.DRConstants import Vendors_Complete, ReplicationType, SiteOption, VendorViewModes
from Web.AdminConsole.DR.virtualization_replication import ConfigureVMWareVM, _VMwareVMOptions


class TestCase(CVTestCase):
    """This testcase is used to verify ip customization for linux and windows vmware vms"""
    test_step = TestStep()
    _HOSTNAME_1 = 'DestVMHost1'
    _HOSTNAME_2 = 'DestVMHost2'

    def __init__(self):
        """Initialises the objects and TC inputs"""
        super(TestCase, self).__init__()
        self.name = "VMWare: IP customization verification (Windows proxy + FREL)"

        self.tcinputs = {
            "ClientName": None,
            "source_vms": [],
            "recovery_target": None,
            "primary_storage_name": None,
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

        self.dr_helper = None

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
        elif not powered_off_failure:
            # If powered off failure is not True, power on VM
            vm_obj.power_on()
        for _ in range(15):
            try:
                # get VM IP and verify it is IPv4 and isn't self assigned
                vm_obj.update_vm_info(force_update=True)
                ipaddress.IPv4Address(vm_obj.ip)
                if '169.254.' in vm_obj.ip:
                    raise Exception('Self assigned IP address for VM')
                break
            except Exception as _exception:
                self.log.info(f'Could not get IP for VM [{vm_obj.vm_name}] due to reason: {_exception}')
                self.log.info('Waiting for 1 minute before trying again')
                sleep(60)
        else:
            raise Exception(f'Could not get VM [{vm_obj.vm_name}] to boot')

    def get_source_vm_details(self):
        """Gets the source VM ip address information from the hypervisor"""
        vm_details = {}
        self.dr_helper.source_auto_instance.hvobj.VMs = self.source_vms_input
        for vm_name in self.source_vms_input:
            vm = VmwareVM(self.dr_helper.source_auto_instance.hvobj, vm_name, vm_boot_skip=True)
            self.wait_for_vm_to_boot(vm, powered_off_failure=False)
            gateway = [gateway_ip for gateway_ip in vm.guest_default_gateways if '.' in gateway_ip]
            vm_details[vm_name] = {"ip_address": vm.ip,
                                   "subnet_mask": vm.guest_subnet_mask,
                                   "default_gateway": gateway[0]}
        return vm_details

    def verify_proxy_configuration(self, auto_instance):
        """Verifies that the proxy configuration is Windows + FREL"""
        hypervisor_name = auto_instance.auto_vsaclient.vsa_client.name
        for proxy_name in auto_instance.proxy_list:
            proxy_client = self.commcell.clients.get(proxy_name)
            if 'windows' not in proxy_client.os_info.lower():
                raise CVTestCaseInitFailure("Windows Proxy not configured on source hypervisor")
            try:
                if not self.dr_helper.source_auto_instance.fbr_ma:
                    raise CVTestCaseInitFailure(f"No proxy configured for FREL for {hypervisor_name}")
            except Exception:
                raise CVTestCaseInitFailure(f"Unable to fetch FREL information for {hypervisor_name}")

    def login(self):
        """Logs in to admin console"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, machine=self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.tcinputs['tenant_username'],
                                 self.tcinputs['tenant_password'])

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
            self.source_vms_input = sum(self.source_vms.values(), [])
            self.recovery_target = self.tcinputs['recovery_target']
            self.primary_storage_name = self.tcinputs["primary_storage_name"]
            self.dns_1 = self.tcinputs.get('dns_1', '')
            self.dns_2 = self.tcinputs.get('dns_2', '')

            self._source_vendor = Vendors_Complete.VMWARE.value
            self._destination_vendor = Vendors_Complete.VMWARE.value
            self._replication_type = ReplicationType.Periodic
            self._siteoption = SiteOption.HotSite
            self.view_mode = VendorViewModes.VMWARE.VMs.value
            self._unconditionally_overwrite = True

            self.dr_helper = DRHelper(self.commcell, self.csdb, self.client)

            recovery_target = self.commcell.recovery_targets.get(self.recovery_target)
            destination_client = self.commcell.clients.get(recovery_target.destination_hypervisor)
            dest_dr_helper = DRHelper(self.commcell, self.csdb, destination_client)

            self.verify_proxy_configuration(self.dr_helper.source_auto_instance)
            self.verify_proxy_configuration(dest_dr_helper.source_auto_instance)
            self.vm_details = self.get_source_vm_details()
        except Exception as exp:
            raise CVTestCaseInitFailure(f'Failed to initialise testcase {str(exp)}')

    @test_step
    def delete_replication_group(self):
        """Deletes the replication group if it exists already"""
        self.replication_helper.delete_replication_group(self.group_name, self.source_vms_input)

    @test_step
    def configure_replication_group(self):
        """Configures the replication group with default options"""
        self.admin_console.navigator.navigate_to_replication_groups()
        vmware_configure = self.replication_group.configure_virtualization(source_vendor=self._source_vendor,
                                                                           destination_vendor=self._destination_vendor,
                                                                           replication_type=self._replication_type.value)

        # Type Hinting
        vmware_configure: ConfigureVMWareVM

        # General
        vmware_configure.content.set_name(self.group_name)
        vmware_configure.content.select_production_site_hypervisor(self.source_hypervisor)
        vmware_configure.next()

        # Content
        vmware_configure.content.select_vm_from_browse_tree(self.source_vms, self.view_mode)
        vmware_configure.next()

        # Storage
        _storagecopy = vmware_configure.storage_cache.Storage_Copy
        vmware_configure.storage_cache.select_storage(self.primary_storage_name,
                                                      storage_copy=_storagecopy.Primary.value)
        vmware_configure.next()

        # Recovery Options
        vmware_configure.recovery_options.select_recovery_target(self.recovery_target)
        vmware_configure.recovery_options.select_rto(self._siteoption.value)
        vmware_configure.next()

        # Pre-Post Scripts (Configuration)
        vmware_configure.next()

        # Override Options
        for vm_name in self.source_vms_input:
            override_vm = vmware_configure.override_options.override_vms(vm_name)
            override_vm: _VMwareVMOptions
            override_vm.advance_options()

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
        vmware_configure.next()

        # Test Failover Options
        vmware_configure.next()

        # Advanced options
        vmware_configure.advanced_options.unconditionally_overwrite_vm(self._unconditionally_overwrite)
        vmware_configure.next()

        # Submit
        vmware_configure.finish()

    @test_step
    def verify_sync_completion(self):
        """Verifies that the sync has completed on the created replication group"""
        self.replication = Replication(self.commcell, self.group_name)
        self.replication.wait_for_first_backup()
        self.replication.get_running_replication_jobs()
        self.replication.post_validation(job_type='FULL', validate_test_data=False)
        self.dr_helper.source_subclient = self.group_name

    @test_step
    def verify_group_creation(self):
        """Verifies that the group has been configured with the correct settings in the command center"""
        self.admin_console.navigator.navigate_to_replication_groups()
        sleep(10)
        if not self.replication_group.has_group(self.group_name):
            raise CVTestStepFailure(f"Group [{self.group_name}] does not exist on the replication groups page")
        self.replication_group.access_group(self.group_name)
        self.group_details.access_configuration_tab()

        for vm_name in self.source_vms_input:
            override_vm = self.group_details.configuration.edit_virtual_machines(vm_name,
                                                                                 vm_type=SOURCE_HYPERVISOR_VMWARE)
            override_vm.advance_options()
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

    @test_step
    def perform_failover(self, planned=True):
        """Performs planned/unplanned failover on the replication group"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)
        if planned:
            job_id = self.group_details.planned_failover()
        else:
            job_id = self.group_details.unplanned_failover()
        self.log.info('Waiting for failover job id %s to complete', job_id)
        job = self.commcell.job_controller.get(job_id)
        job.wait_for_completion()
        self.utils.assert_comparison(job.status, 'Completed')

    @test_step
    def perform_failback(self):
        """Performs failback on the replication group"""
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
        if len(self.dr_helper.destination_vm_names) != len(self.source_vms_input):
            self.log.info(f'Source VMs: {self.source_vms_input}')
            self.log.info(f'Destination VMs: {self.dr_helper.destination_vm_names}')
            raise CVTestStepFailure('Not all source VMs are backed up')
        for vm_name in self.dr_helper.destination_vm_names:
            source_vm_name = [source_vm for source_vm in self.source_vms_input if source_vm in vm_name][0]
            vm = VmwareVM(self.dr_helper.destination_auto_instance.hvobj, vm_name, vm_boot_skip=True)
            self.wait_for_vm_to_boot(vm)

            if dhcp and vm.guest_dhcp_enabled is not None:
                self.utils.assert_comparison(vm.guest_dhcp_enabled, dhcp)
            elif vm.guest_dhcp_enabled is None:
                self.log.warn('DHCP could not be verified')
            destination_ip = {"ip_address": vm.ip,
                              "subnet_mask": vm.guest_subnet_mask,
                              "default_gateway": [gateway_ip for gateway_ip in vm.guest_default_gateways
                                                  if '.' in gateway_ip][0]}
            # Verify correct IPv4 addresses
            for ip_addr in destination_ip.values():
                try:
                    ipaddress.IPv4Address(ip_addr)
                except:
                    raise CVTestStepFailure(f"{vm.vm_name} VM's IP customization is incorrect {destination_ip}")
            # Verify IPs are not source IPs
            if destination_ip == self.vm_details[source_vm_name]:
                raise CVTestStepFailure(f"IP customization failed for VM {vm.vm_name}")
            if dhcp:
                # Add IP for static configuration later
                self.utils.assert_comparison(vm.guest_hostname, self._HOSTNAME_1)
                self.destination_ips[source_vm_name] = destination_ip
            else:
                # Compare static ip with the one that is defined in group
                self.utils.assert_comparison(vm.guest_hostname, self._HOSTNAME_2)
                self.utils.assert_comparison(destination_ip, self.destination_ips[source_vm_name])
                if self.dns_1:
                    self.utils.assert_includes(self.dns_1, vm.guest_dns)
                if self.dns_2:
                    self.utils.assert_includes(self.dns_2, vm.guest_dns)

    @test_step
    def verify_failback(self):
        """Verifies that the DRVM on failover has reverted ip customization"""
        for vm_name in self.source_vms_input:
            vm = VmwareVM(self.dr_helper.source_auto_instance.hvobj, vm_name, vm_boot_skip=True)
            self.wait_for_vm_to_boot(vm)
            if vm.guest_hostname in [self._HOSTNAME_1, self._HOSTNAME_2]:
                raise CVTestStepFailure(f"VM hostname does not revert for VM {vm.vm_name}")
            if vm.guest_dhcp_enabled is not None:
                self.utils.assert_comparison(vm.guest_dhcp_enabled, False)
            elif vm.guest_dhcp_enabled is None:
                self.log.info('DHCP could not be verified')
            self.utils.assert_comparison(vm.ip, self.vm_details[vm_name]['ip_address'])
            self.utils.assert_comparison(vm.guest_subnet_mask, self.vm_details[vm_name]['subnet_mask'])
            self.utils.assert_includes(self.vm_details[vm_name]['default_gateway'], vm.guest_default_gateways)
            if self.tcinputs.get('dns_1') in vm.guest_dns or self.tcinputs.get('dns_2') in vm.guest_dns:
                raise CVTestStepFailure("DNS settings are not correctly reverted on failback")

    @test_step
    def edit_group_static(self):
        """Sets static IP for the group with source and destination values"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)
        self.group_details.access_configuration_tab()

        for vm_name in self.source_vms_input:
            edit_vm = self.group_details.configuration.edit_virtual_machines(vm_name,
                                                                             vm_type=SOURCE_HYPERVISOR_VMWARE)
            edit_vm.advance_options()
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

    @test_step
    def verify_static_ip(self):
        """Verifies that the correct VM ip settings are set on the destination VM"""
        sleep(10)
        for vm_name in self.source_vms_input:
            edit_vm = self.group_details.configuration.edit_virtual_machines(vm_name,
                                                                             vm_type=SOURCE_HYPERVISOR_VMWARE)
            edit_vm.advance_options()
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
            self.perform_failover(planned=False)
            self.logout()
            self.verify_failover(dhcp=True)

            self.login()
            self.perform_failback()
            self.logout()
            self.verify_failback()

            self.login()
            self.edit_group_static()
            self.verify_static_ip()

            self.perform_failover(planned=True)
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
