# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case
(AWS Replication group: Verify Creation and edit operations)
TestCase is the only class defined in this file.

TestCase: Class for executing this test case
Sample JSON: {
        "hypervisor": None,
        "source_vm1": None,
        "source_vm2": None,
        "source_vm3": None,
        "recovery_target": None,
        "storage": None,
        "secondary_storage": None,
        "instance_name": None,
        "availability_zone": None,
        "volume_type": None,
        "encryption_key": None,
        "network": None,
        "security_group": None,
        "instance_type": None,
        "volume_type_2": None,
        "encryption_key_2": None,
        "network_2": None,
        "security_group_2": None,
        "instance_type_2": None,
}
"""
from time import sleep
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.virtualization_replication import _Target, SOURCE_HYPERVISOR_AWS
from Web.AdminConsole.DR.recovery_targets import RecoveryTargets
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """This class is used to automate the replication"""
    test_step = TestStep()
    _AWS_VENDOR_NAME = "Amazon"
    _VM_TYPE = "Virtual Server"
    _REPLICATION_TYPE = "Periodic"
    _TARGET_FREQ_NUMBER = 4
    _TARGET_FREQ_UNIT = _Target.FREQUENCY_HOURS

    def __init__(self):
        """Initialises the objects and TC inputs"""
        super(TestCase, self).__init__()
        self.name = "AWS Replication group: Verify Creation and edit operations"
        self.tcinputs = {
            "hypervisor": None,
            "source_vm1": None,
            "source_vm2": None,
            "source_vm3": None,
            "recovery_target": None,
            "storage": None,
            "secondary_storage": None,
            "instance_name": None,
            "availability_zone": None,
            "volume_type": None,
            "encryption_key": None,
            "network": None,
            "security_group": None,
            "instance_type": None,
            "volume_type_2": None,
            "encryption_key_2": None,
            "network_2": None,
            "security_group_2": None,
            "instance_type_2": None,
        }
        self.utils = None
        self.browser = None
        self.admin_console = None
        self.replication_group = None
        self.group_details = None
        self.vm_group = None
        self.target_details = None
        self.edit_vm = None
        self.vm_noedit_details = None

    @property
    def group_name(self):
        """Returns the name for the replication group"""
        return f"AWS_Replication_Group_Operations_3_TC_{self.id}"

    def login(self):
        """Logs in to the admin console and initialises it"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, machine=(self.inputJSONnode['commcell']['webconsoleHostname']))
        self.admin_console.goto_adminconsole()
        self.admin_console.login(
            self.inputJSONnode['commcell']['commcellUsername'],
            self.inputJSONnode['commcell']['commcellPassword']
        )

        self.replication_group = ReplicationGroup(self.admin_console)
        self.group_details = ReplicationDetails(self.admin_console)
        self.vm_group = VMGroups(self.admin_console)

    def logout(self):
        """Silent logout"""
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    def setup(self):
        """Sets up the various variables and initiates the admin console"""
        try:
            self.utils = TestCaseUtils(self)
            self.login()
        except Exception as exp:
            raise CVTestCaseInitFailure(f"Could not initialise the test case {self.id} "
                                        f"due to following error:\n{str(exp)}")

    def get_recovery_target_details(self):
        """Gets the recovery target details for verification"""
        self.admin_console.navigator.navigate_to_replication_targets()
        recovery_target = RecoveryTargets(self.admin_console).access_target(
            self.tcinputs['recovery_target']
        )
        #TODO: Removal of additional span element necessary - FORM 123788
        summary = recovery_target.get_target_summary()
        self.target_details = [summary['Availability zone'],
                               summary['Volume type'],
                               summary['Encryption key'],
                               summary['Network'],
                               summary['Security groups'],
                               summary['Instance type']]

    @test_step
    def delete_replication_group(self):
        """Tries to delete the recovery target"""
        self.admin_console.navigator.navigate_to_replication_groups()
        if self.replication_group.has_group(self.group_name):
            self.replication_group.delete_group(self.group_name)

    @test_step
    def create_replication_group(self):
        """Creates and configures a new AWS replication group """
        aws_configure = self.replication_group.configure_aws()
        aws_configure.content.set_name(self.group_name)
        # TODO:change Search - 'instances' - 'VMs' in UI(Ref:AdminConsoleBase.py; fxn - search_vm)
        aws_configure.content.select_vm_from_browse_tree(self.tcinputs['hypervisor'],
                                                        {"By region": [self.tcinputs['source_vm1']]})
        aws_configure.content.select_vm_from_browse_tree(self.tcinputs['hypervisor'],
                                                        {"By region": [self.tcinputs['source_vm2']]})
        aws_configure.next()

        aws_configure.target.select_recovery_target(self.tcinputs['recovery_target'])
        aws_configure.target.validate_destination_vm(True)
        aws_configure.target.unconditionally_overwrite_vm(True)
        aws_configure.next()

        aws_configure.storage_cache.select_storage(self.tcinputs['storage'])
        aws_configure.storage_cache.select_secondary_storage(self.tcinputs['secondary_storage'])
        aws_configure.next()

        override_options = aws_configure.override_options.override_vms(self.tcinputs['source_vm1'])
        override_options.select_availability_zone(self.tcinputs['availability_zone'])
        override_options.select_volume_type(self.tcinputs['volume_type'])
        override_options.select_encryption_key(self.tcinputs['encryption_key'])
        override_options.select_network_subnet(self.tcinputs['network'])
        override_options.select_security_group(self.tcinputs['security_group'])
        override_options.select_instance_type(self.tcinputs['instance_type'])
        self.admin_console.click_button('Save')

        self.vm_noedit_details = aws_configure.override_options.get_aws_vm_details(
            self.tcinputs['source_vm2']
        )
        self.utils.assert_comparison(self.vm_noedit_details[1:], self.target_details)

        aws_configure.next()

        sleep(5)
        aws_configure.finish()

    @test_step
    def verify_creation(self):
        """Verify successful group creation with a visible entry in Replication groups table"""
        details = self.replication_group.get_replication_group_details_by_name(self.group_name)

        self.utils.assert_comparison(details['Group name'][0], self.group_name)
        self.utils.assert_comparison(details['Source'][0], self.tcinputs['hypervisor'])
        self.utils.assert_comparison(details['Destination'][0], self.tcinputs['recovery_target'])
        self.utils.assert_comparison(details['Type'][0], self._VM_TYPE)
        self.utils.assert_comparison(details['Replication type'][0], self._REPLICATION_TYPE)
        self.utils.assert_comparison(details['State'][0], 'Enabled')

    @test_step
    def verify_vm_group(self):
        """Verifies whether the VM group exists or not"""
        self.admin_console.navigator.navigate_to_vm_groups()
        self.admin_console.refresh_page()

        table_content = self.vm_group.get_details_by_vm_group(self.group_name)
        self.utils.assert_includes(self.group_name, table_content['Name'][0])
        self.utils.assert_comparison(table_content['Vendor'][0], self._AWS_VENDOR_NAME)
        self.utils.assert_comparison(table_content['Hypervisor'][0], self.tcinputs['hypervisor'])
        self.utils.assert_comparison(table_content['Plan'][0], f"{self.group_name}_ReplicationPlan")


    @test_step
    def disable_replication_group(self):
        """Disables the replication group and re-enables it to verify the group status"""
        self.group_details.overview.disable_replication_group()
        summary = self.group_details.overview.get_summary_details()
        self.utils.assert_comparison(summary['State'], 'Disabled')
        self.admin_console.refresh_page()
        self.group_details.overview.enable_replication_group()
        self.utils.assert_comparison(self.group_details.overview.get_summary_details().get('Is replication enabled?'), 'ON')

    @test_step
    def verify_overview(self):
        """Verifies the details of the replication group in the overview tab"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)

        summary = self.group_details.overview.get_summary_details()
        self.utils.assert_comparison(summary['Source'], self.tcinputs['hypervisor'])
        self.utils.assert_comparison(summary['Recovery target'], self.tcinputs['recovery_target'])
        self.utils.assert_comparison(summary['Destination vendor'], self._AWS_VENDOR_NAME)
        self.utils.assert_comparison(summary['Replication type'], self._REPLICATION_TYPE)
        self.utils.assert_comparison(summary['Is replication enabled?'], 'ON')

    @test_step
    def verify_configuration(self):
        """Verifies the details of the replication group in the configuration tab"""
        self.group_details.access_configuration_tab()

        rpo = self.group_details.configuration.get_rpo_details()
        self.utils.assert_includes(f"{self._TARGET_FREQ_NUMBER} {self._TARGET_FREQ_UNIT.lower()}", rpo['Replication frequency'])
        storages = self.group_details.configuration.get_storage_details()
        self.utils.assert_includes(self.tcinputs['storage'], storages)

        adv_options = self.group_details.configuration.get_advanced_options_details()
        self.utils.assert_comparison(adv_options['Unconditionally overwrite if VM already exists'], "ON")

        vm_details_1 = self.group_details.configuration.get_vm_details(self.tcinputs['source_vm1'])
        self.utils.assert_comparison(self.tcinputs['source_vm1'], vm_details_1['Source VM'])

        vm_details_2 = self.group_details.configuration.get_vm_details(self.tcinputs['source_vm2'])
        self.utils.assert_comparison(self.tcinputs['source_vm2'], vm_details_2['Source VM'])

    @test_step
    def add_delete_vm_to_group(self):
        """Add VM to group after creation"""
        add_vm = self.group_details.configuration.add_virtual_machines(vm_type=SOURCE_HYPERVISOR_AWS)
        add_vm.add_vm([self.tcinputs['source_vm_3']])

        new_vm_details = self.group_details.configuration.get_vm_details(self.tcinputs['source_vm_3'])
        if new_vm_details['Source VM'] != self.tcinputs['source_vm_3']:
            raise CVTestStepFailure(
                f"Expected value of Source VM {self.tcinputs['source_vm_3']} does not match "
                f"the collected value {new_vm_details['Source VM']}")
        self.group_details.configuration.remove_virtual_machines(self.tcinputs['source_vm_3'])
        try:
            self.admin_console.refresh_page()
            self.group_details.configuration.get_vm_details(self.tcinputs['source_vm_3'])
        except:
            self.log.info("VM successfully deleted from group")
        else:
            raise CVTestStepFailure("VM could not be deleted successfully")

    @test_step
    def verify_disabled_fields(self, vm_id):
        """Verifies that the disabled fields are disabled or not"""
        self.admin_console.refresh_page()
        self.edit_vm = self.group_details.configuration.edit_virtual_machines(self.tcinputs[f'source_vm{vm_id}'], vm_type=SOURCE_HYPERVISOR_AWS)

        check_fields = ['vmDisplayName', 'availabilityZone']
        for field_id in check_fields:
            field_disabled = self.edit_vm.is_field_disabled(field_id)
            if field_disabled is False:
                self.log.info("Field "f'{field_id}'" is disabled")
            if field_disabled:
                raise CVTestStepFailure(f'In Edit VM The field {field_id} is enabled, but must be disabled')

    @test_step
    def verify_edit_vm(self, after_edit=False, vm_id=1):
        """Verifies the data on the edit VM page"""
        sleep(10)
        if vm_id == 2:
            self.utils.assert_comparison(self.vm_noedit_details, self.edit_vm.network)
            # Addition pending
        elif after_edit:
            self.utils.assert_includes(self.edit_vm.volume_type, self.tcinputs["volume_type_2"])
            self.utils.assert_includes(self.edit_vm.encryption_key, self.tcinputs["encryption_key_2"])
            self.utils.assert_includes(self.edit_vm.network, self.tcinputs["network_2"])
            self.utils.assert_includes(self.edit_vm.security_group, self.tcinputs["security_group_2"])
            self.utils.assert_includes(self.edit_vm.instance_type, self.tcinputs["instance_type_2"])
        else:
            self.utils.assert_includes(self.edit_vm.volume_type, self.tcinputs["volume_type"])
            self.utils.assert_includes(self.edit_vm.encryption_key, self.tcinputs["encryption_key"])
            self.utils.assert_includes(self.edit_vm.network, self.tcinputs["network"])
            self.utils.assert_includes(self.edit_vm.security_group, self.tcinputs["security_group"])
            self.utils.assert_includes(self.edit_vm.instance_type, self.tcinputs["instance_type"])
        self.edit_vm.cancel()

    @test_step
    def edit_vm_details(self):
        """Modify the group details to check if the detail change is registered on Command Center"""
        self.admin_console.refresh_page()
        edit_vm = (self.group_details.configuration.edit_virtual_machines(self.tcinputs['source_vm1'], vm_type=SOURCE_HYPERVISOR_AWS))
        edit_vm.select_volume_type(self.tcinputs['volume_type_2'])
        edit_vm.select_encryption_key(self.tcinputs['encryption_key_2'])
        edit_vm.select_network_subnet(self.tcinputs['network_2'])
        edit_vm.select_security_group(self.tcinputs['security_group_2'])
        edit_vm.select_instance_type(self.tcinputs['instance_type_2'])
        edit_vm.save()

    def run(self):
        """Runs the testcase in order"""
        try:
            self.get_recovery_target_details()
            self.delete_replication_group()
            self.create_replication_group()
            self.verify_creation()
            self.verify_vm_group()

            self.verify_overview()
            self.disable_replication_group()
            self.verify_configuration()
            self.add_delete_vm_to_group()

            self.verify_disabled_fields(vm_id=1)
            self.verify_edit_vm(after_edit=False, vm_id=1)
            self.verify_disabled_fields(vm_id=2)
            self.verify_edit_vm(after_edit=False, vm_id=2)

            self.edit_vm_details()

            self.verify_disabled_fields(vm_id=1)
            self.verify_edit_vm(after_edit=True, vm_id=1)
            self.verify_disabled_fields(vm_id=2)
            self.verify_edit_vm(after_edit=True, vm_id=2)

            self.delete_replication_group()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Performs garbage collection for the TC"""
        self.logout()
