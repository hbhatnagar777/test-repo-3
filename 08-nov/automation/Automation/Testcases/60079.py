# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case
(AWS Recovery Targets: Verification of creation and update of target)

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
Sample JSON: {
                    "tenant_username" : "tenant\\admin",
                    "tenant_password" : "password",
                    "display_name": "display_name",
                    "hypervisor": "hypervisor_name",
                    "access_node": "access_node_name",
                    "availability_zone": "availibility_zone_path",
                    "volume_type": "volume_type",
                    "iam_role": "iam_role_name",
                    "network_subnet": "subnet_path",
                    "security_group": "security_group",
                    "instance_type" : "instance_type",
                    "encryption_key": "encryption",
                    "expiration_time": "value",
                    "test_network": "test_subnet_path",
                    "test_instance_type": "test_instance_type",

                    "display_name_2": "display_name_2",
                    "access_node_2": "ccess_node_name_2",
                    "availability_zone_2": "availibility_zone_path_2",
                    "volume_type_2": "volume_type_2",
                    "encryption_key_2": "encryption_2",
                    "iam_role_2": "iam_role_name_2",
                    "network_subnet_2": "subnet_path_2",
                    "security_group_2": "security_group_2",
                    "instance_type_2" : "instance_type_2",
                    "expiration_time_2": "value_2",
                    "test_network_2": "test_subnet_path_2",
                    "test_instance_type_2": "test_instance_type_2"
}
"""

from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration.DRUtils.DRConstants import Vendors_Complete, Application_Type
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.DR.recovery_targets import RecoveryTargets, _AWSRecoveryTarget, _EditAWSRecoveryTarget
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """This testcase is for the creation AWS recovery target"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the class and variables are set to None"""
        super(TestCase, self).__init__()
        self.name = "AWS Recovery Target CRUD Test"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "hypervisor": None,
            "display_name": None,
            "access_node": None,
            "availability_zone": None,
            "volume_type": None,
            "iam_role": None,
            "network_subnet": None,
            "security_group": None,
            "instance_type": None,
            "encryption_key": None,
            "expiration_time": None,
            "test_network": None,
            "test_security_group": None,
            "test_instance_type": None,
            "display_name_2": None,
            "access_node_2": None,
            "availability_zone_2": None,
            "volume_type_2": None,
            "encryption_key_2": None,
            "iam_role_2": None,
            "network_subnet_2": None,
            "security_group_2": None,
            "instance_type_2": None,
            "expiration_time_2": None,
            "test_network_2": None,
            "test_security_group_2": None,
            "test_instance_type_2": None,
        }

        self.browser = None
        self.admin_console = None
        self.utils = None
        self.recovery_targets = None
        self.target = None
        self.edit_target = None

        self._destination_vendor = Vendors_Complete.AWS
        self._application_type = Application_Type.REPLICATION.value

    def setup(self):
        """Sets up the various variables and initiates the admin console"""
        self.utils = TestCaseUtils(self)
        self.hypervisor = self.tcinputs["hypervisor"]

        # DRVM Options
        self.display_name = self.tcinputs["display_name"]
        self.access_node = self.tcinputs['access_node']
        self.availability_zone = self.tcinputs['availability_zone']
        self.volume_type = self.tcinputs['volume_type']
        self.encryption_key = self.tcinputs['encryption_key']
        self.iam_role = self.tcinputs['iam_role']
        self.network_subnet = self.tcinputs['network_subnet']
        self.security_group = self.tcinputs['security_group']
        self.instance_type = self.tcinputs['instance_type']

        # Test Failover Options
        self.expiration_time = self.tcinputs['expiration_time']
        self.expiration_unit = self.tcinputs['expiration_unit']
        self.test_network = self.tcinputs['test_network']
        self.test_security_group = self.tcinputs["test_security_group"]
        self.test_instance_type = self.tcinputs['test_instance_type']

        # Edited DRVM Options
        self.edited_display_name = self.tcinputs["display_name_2"]
        self.edited_access_node = self.tcinputs['access_node_2']
        self.edited_availability_zone = self.tcinputs['availability_zone_2']
        self.edited_volume_type = self.tcinputs['volume_type_2']
        self.edited_encryption_key = self.tcinputs['encryption_key_2']
        self.edited_iam_role = self.tcinputs['iam_role_2']
        self.edited_network_subnet = self.tcinputs['network_subnet_2']
        self.edited_security_group = self.tcinputs['security_group_2']
        self.edited_instance_type = self.tcinputs['instance_type_2']

        # Edited Test Failover Options
        self.edited_expiration_time = self.tcinputs['expiration_time_2']
        self.edited_expiration_unit = self.tcinputs['expiration_unit_2']
        self.edited_test_network = self.tcinputs['test_network_2']
        self.edited_test_security_group = self.tcinputs["test_security_group_2"]
        self.edited_test_instance_type = self.tcinputs['test_instance_type_2']


    def _validate_recovery_target_options(self, observed_values : dict | list, expected_values : dict | list):
        """Validates the values of the recovery target options"""
        validation_keys = ["application_type", "destination_hypervisor", "access_node",
                           "drvm_name", "availability_zone", "instance_type", "volume_type",
                           "encryption_key", "iam_role", "network", "security_groups",
                           "test_failover_expiration_time", "test_failover_network",
                           "test_failover_security_groups", "test_failover_instance_type"]

        observed_values_dict = {key: value for key, value in zip(validation_keys, observed_values)} if isinstance(observed_values, list) else observed_values
        expected_values_dict = {key: value for key, value in zip(validation_keys, expected_values)} if isinstance(expected_values, list) else expected_values

        self.recovery_targets.validate_details(self._destination_vendor,
                                               observed_values=observed_values_dict,
                                               expected_values=expected_values_dict)


    @property
    def target_name(self):
        """Returns the initial target name for the recovery target"""
        return f"RecoveryTarget_TC_{self.id}_{self._destination_vendor.name}"

    @property
    def edited_target_name(self):
        """Returns the modified target name"""
        return f"RecoveryTarget_TC_{self.id}_{self._destination_vendor.name}_edited"

    def login(self):
        """Logs in to admin console"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser,
                                              self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(self.tcinputs['tenant_username'],
                                     self.tcinputs['tenant_password'])

            self.recovery_targets = RecoveryTargets(self.admin_console)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def logout(self):
        """Silent logout"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    @test_step
    def delete_recovery_target(self, target_name=None):
        """Tries to delete the recovery target"""
        target_name = self.target_name if target_name is None else target_name
        self.admin_console.navigator.navigate_to_replication_targets()
        self.recovery_targets.delete_recovery_target(target_name)

    @test_step
    def create_recovery_target(self):
        """Creates a recovery target in the recovery targets page"""
        self.admin_console.navigator.navigate_to_replication_targets()
        _labels = self.admin_console.props

        _application_type = _labels['label.replicationTarget'] if self._application_type == Application_Type.REPLICATION.value else _labels['label.regularTarget']
        aws_target: _AWSRecoveryTarget = self.recovery_targets.configure_recovery_target(application_type=_application_type,
                                                                                         vendor=self._destination_vendor.value,
                                                                                         name=self.target_name)

        # General Options
        aws_target.general.select_destination_hypervisor(self.hypervisor)
        aws_target.general.set_vm_display_name(self.display_name, _labels['label.prefix'])
        aws_target.general.select_access_node(self.access_node)
        aws_target.next()

        # Destination Options
        aws_target.select_availability_zone(self.availability_zone)
        aws_target.select_instance_type(self.instance_type)
        aws_target.select_iam_role(self.iam_role)
        aws_target.select_network_subnet(self.network_subnet)
        aws_target.select_security_group(self.security_group)
        aws_target.select_volume_type(self.volume_type)
        aws_target.select_encryption_key(self.encryption_key)
        aws_target.next()

        # Test failover options
        aws_target.set_expiration_time(self.expiration_time, self.expiration_unit)
        aws_target.select_network_subnet(self.test_network)
        aws_target.select_security_group(self.test_security_group)
        aws_target.select_instance_type(self.test_instance_type)
        aws_target.submit()

    @test_step
    def verify_target_creation(self):
        """Verifies the information of the recovery target on the recovery target page table"""
        self.admin_console.navigator.navigate_to_replication_targets()
        _target_details = self.recovery_targets.get_target_details(self.target_name)
        _labels = self.admin_console.props

        self.utils.assert_comparison(_target_details[_labels['label.name']], [self.target_name])
        self.utils.assert_comparison(_target_details[_labels['label.libraryVendorName']], [self._destination_vendor.value])
        self.utils.assert_comparison(_target_details[_labels['label.PolicyType']], [self._application_type])
        self.utils.assert_comparison(_target_details[_labels['label.destinationServer']], [self.hypervisor])

    @test_step
    def verify_target_details(self, after_edit=False):
        """Verifies the target details in the target's detail page"""
        self.admin_console.navigator.navigate_to_replication_targets()

        _labels = self.admin_console.props
        _affix_label = f"({_labels['label.prefix'] if not after_edit else _labels['label.suffix']})"
        _target_name = self.target_name if not after_edit else self.edited_target_name

        self.target = self.recovery_targets.access_target(_target_name)
        _target_details = self.target.get_target_summary()

        observed_values = [_target_details[_labels['label.applicationType']], _target_details[_labels['label.destinationServer']],
                           _target_details[_labels['label.accessNode']], _target_details[f"{_labels['label.changeVmDisplayName']} {_affix_label}"],
                           _target_details[_labels['label.availabilityZone']], _target_details[_labels['label.instanceType']][0],
                           _target_details[_labels['label.volumeType']], _target_details[_labels['label.encryptionKey']],
                           _target_details[_labels['label.iamRole']], _target_details[_labels['label.network']][0],
                           _target_details[_labels['label.securityGroupsLabel']][0], _target_details[_labels['label.expirationTime']],
                           _target_details[_labels['label.network']][1], _target_details[_labels['label.securityGroupsLabel']][1],
                           _target_details[_labels['label.instanceType']][1]]

        if not after_edit:
            expected_values = [self._application_type, self.hypervisor, self.access_node, self.display_name,
                               self.availability_zone.split("/")[-1], self.instance_type, self.volume_type, self.encryption_key,
                               self.iam_role, self.network_subnet, self.security_group, f"{self.expiration_time} {self.expiration_unit}",
                               self.test_network, self.test_security_group, self.test_instance_type]
        else:
            expected_values = [self._application_type, self.hypervisor, self.edited_access_node, self.edited_display_name,
                               self.edited_availability_zone, self.edited_instance_type, self.edited_volume_type, self.edited_encryption_key,
                               self.edited_iam_role, self.edited_network_subnet, self.edited_security_group, f"{self.edited_expiration_time} {self.edited_expiration_unit}",
                               self.edited_test_network, self.edited_test_security_group, self.edited_test_instance_type]

        self._validate_recovery_target_options(observed_values, expected_values)

    @test_step
    def edit_recovery_target(self):
        """Edits the target configuration"""
        edit_target : _EditAWSRecoveryTarget = self.target.edit_target(self.target_name, self._destination_vendor.value)
        _labels = self.admin_console.props

        edit_target.set_recovery_target_name(self.edited_target_name)
        edit_target.general.set_vm_display_name(self.edited_display_name, _labels['label.suffix'])
        edit_target.general.select_access_node(self.edited_access_node)
        edit_target.next()

        edit_target.select_availability_zone(self.edited_availability_zone)
        edit_target.select_instance_type(self.edited_instance_type)
        edit_target.select_iam_role(self.edited_iam_role)
        edit_target.select_network_subnet(self.edited_network_subnet)
        edit_target.select_security_group(self.edited_security_group)
        edit_target.select_volume_type(self.edited_volume_type)
        edit_target.select_encryption_key(self.edited_encryption_key)
        edit_target.next()

        edit_target.set_expiration_time(self.edited_expiration_time, self.edited_expiration_unit)
        edit_target.select_network_subnet(self.edited_test_network)
        edit_target.select_security_group(self.edited_test_security_group)
        edit_target.select_instance_type(self.edited_test_instance_type)
        edit_target.submit()

    def run(self):
        """Executes the testcase"""
        try:
            self.login()

            # Cleanup
            self.delete_recovery_target()
            self.delete_recovery_target(target_name=self.edited_target_name)
            
            # RT Creation and detail verification
            self.create_recovery_target()
            self.verify_target_creation()
            self.verify_target_details()

            self.edit_recovery_target()
            self.verify_target_details(after_edit=True)

            self.delete_recovery_target(target_name=self.edited_target_name)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Performs garbage collection for the TC"""
        self.logout()
