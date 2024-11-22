# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: This test case verifies vm provisioning setting is functional and enabling auto-scale works

TestCase: Class for executing this test case
Sample JSON: {
        "ClientName": "VC_AZ",
        "InstanceName" : "azure resource manager",
        "AgentName" : "Virtual Server"
        "ServerGroup":  "SG",
        "ResourceGroup": "RG",
        "BackupsetName" : "TEST",
        "RegionInfo" : "[{'region name': 'North Central US', 'network name': 'NET,
        'subnet name': 'default', 'nsg name' : 'NSG'}]",
        "SubclientName": "SCS",
        "public Ip": false
        "AdvancedSettings": "{}"
        ""
}
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils.AutoScaleUtils import AutoScaleValidation
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from VirtualServer.VSAUtils import VsaTestCaseUtils


class TestCase(CVTestCase):
    """This class is used to validate auto-scale settings"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        super(TestCase, self).__init__()
        self.name = "Command Center : Auto scale configuration"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)

    def login(self):
        """Logs in to admin console"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, machine=self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.goto_adminconsole()
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.wait_for_completion()

        self.hypervisor_page = Hypervisors(self.admin_console)
        self.hypervisor_details = HypervisorDetails(self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.utils = TestCaseUtils(self)
            self.auto_scale_options = {"server group": self.tcinputs["ServerGroup"],
                                        "resource group": self.tcinputs["ResourceGroup"],
                                        "region specific info": eval(self.tcinputs["RegionInfo"]),
                                        "public Ip": self.tcinputs.get("public Ip", True),
                                        "advanced settings": eval(self.tcinputs.get("AdvancedSettings", "{}"))}

            self.tc_utils.initialize(self)

            self.login()
        except Exception as exp:
            raise CVTestCaseInitFailure(f'Failed to initialise testcase {str(exp)}')

    @test_step
    def validate_auto_scale_settings(self):
        """Validates the configured auto-scale options match input"""
        try:
            auto_scale_policy_properties = self.auto_scale_obj.auto_scale_policy
            if auto_scale_policy_properties['associatedClientGroup']['clientGroupName']\
                    != self.auto_scale_options['server group']:
                raise Exception("Server group validation failed. Configured server group"
                                f"{auto_scale_policy_properties['associatedClientGroup']['clientGroupName']}")
            if auto_scale_policy_properties['esxServers'][0]['esxServerName']\
                    != self.auto_scale_options['resource group']:
                raise Exception("Resource group validation failed. Configured resource group"
                f"{auto_scale_policy_properties['esxServers'][0]['esxServerName']}")
            auto_scale_region_info = self.auto_scale_obj.auto_scale_region_info
            if len(auto_scale_region_info) != len(self.auto_scale_options["region specific info"]):
                raise Exception("Number region configured validation failed."
                                f"Configured regions {auto_scale_region_info.keys()}")
            for region_info in self.auto_scale_options['region specific info']:
                region = region_info["region name"].replace(" ", "").lower()
                if region_info['subnet name'] != auto_scale_region_info[region]['subnetName']:
                    raise Exception(f"Subnet validation failed."
                                    f"Configured subnet {auto_scale_region_info[region]['subnetName']}")

                if region_info['network name'] != auto_scale_region_info[region]['networkName']:
                    raise Exception("Network configuration validation failed."
                                    f"Configured network {auto_scale_region_info[region]['networkName']}")
                if region_info.get('nsg name', None) != auto_scale_region_info[region].\
                        get('securityGroups', [{}])[0].get('name', None):
                    raise Exception("Network Security group validation failed.Configured group"
                                    f"{auto_scale_region_info[region].get('securityGroups', [])[0].get('name', None)}")
            if self.auto_scale_options.get('advanced settings', {}).get('public Ip', False) \
                    != auto_scale_policy_properties.get('isPublicIPSettingsAllowed', False):
                raise Exception("Public IP validation failed.Configured public IP setting"
                                f"{auto_scale_region_info.get('isPublicIPSettingsAllowed', False)}")

        except Exception as exp:
            raise CVTestStepFailure(str(exp))

    def run(self):
        """Runs the testcase in order"""
        try:
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_page.select_hypervisor(self.tcinputs["ClientName"])
            self.admin_console.select_configuration_tab()
            self.hypervisor_details.configure_vm_provisioning(self.auto_scale_options)
            self.hypervisor_details.disable_auto_scale()
            self.hypervisor_details.enable_auto_scale()
            self.auto_scale_obj = AutoScaleValidation(self.tc_utils.sub_client_obj)
            self.validate_auto_scale_settings()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
