# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this metallic test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

import json
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log, subclient_initialize
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing hypervisors CRUD case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic AWS hypervisors CRUD case"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.client_name = "AWS_CRUD_Auto_Client"
        self.vm_group_name = "AWS_CRUD_VMGroup"
        self.tenant_vm_group = "TC_test_tenant_vmgroup"
        self.tenant_client_name = "AWS_CRUD_Auto_tenant"
        self.hypervisor_details_obj = None
        self.hypervisor_ac_obj = None
        self.admin_console = None
        self.vsa_obj = None
        self.vsa_obj_tenant = None
        self.dashboard = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
        }

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs['username'],
                                 self.tcinputs['password'])

        self.dashboard = Dashboard(self.admin_console, service=HubServices.vm_kubernetes)
        self.hypervisor_details_obj = HypervisorDetails(self.admin_console)
        self.hypervisor_ac_obj = Hypervisors(self.admin_console)

    def run(self):
        try:
            decorative_log("Validating hypervisor")
            self.admin_console.navigator.navigate_to_hypervisors()
            self.tcinputs['ClientName'] = self.client_name
            self.reinitialize_testcase_info()
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                     self.commcell, self.csdb)
            #self.vsa_obj.auto_vsa_subclient = subclient_initialize(self)
            try:
                role_name = list(json.loads(self.tcinputs['RoleARN']).keys())[0]
                role_arn = list(json.loads(self.tcinputs['RoleARN']).values())[0]
            except:
                role_name = list(self.tcinputs['RoleARN'].keys())[0]
                role_arn = list(self.tcinputs['RoleARN'].values())[0]

            decorative_log("Validating admin hypervisor created with the inputs")
            self.vsa_obj.validate_hypervisor(self.client_name,
                                              validate_input={"vendor": hypervisor_type.AMAZON_AWS.value,
                                                              "server_name": self.client_name,
                                                              "proxy_list": self.tcinputs['Proxy_list'],
                                                              "auth_type": "STS assume role with IAM policy",
                                                              "credential": role_arn,
                                                              "regions": self.tcinputs['Regions'],
                                                              "vm_group_name": self.vm_group_name,
                                                              "vm_content": self.tcinputs['BackupContent'],
                                                              "plan": self.tcinputs['Plan']})

            # Validating tenant hypervisor
            try:
                tenant_role_arn = list(json.loads(self.tcinputs['TenantCredential']).values())[0]
            except:
                tenant_role_arn = list(self.tcinputs['TenantCredential'].values())[0]

            self.admin_console.navigator.navigate_to_hypervisors()
            self.tcinputs['ClientName'] = self.tenant_client_name
            self.reinitialize_testcase_info()
            self.vsa_obj_tenant = AdminConsoleVirtualServer(self.instance, self.browser, self.commcell, self.csdb)

            decorative_log("Validating tenant hypervisor created with the inputs")
            self.vsa_obj_tenant.validate_hypervisor(self.tenant_client_name,
                                                    validate_input={"vendor": hypervisor_type.AMAZON_AWS.value,
                                                                    "server_name": self.tenant_client_name,
                                                                    "admin_hypervisor": self.client_name,
                                                                    "auth_type": self.tcinputs['Auth_type'],
                                                                    "credential": tenant_role_arn,
                                                                    "regions": self.tcinputs['Regions'],
                                                                    "vm_group_name": self.tenant_vm_group,
                                                                    "vm_content": self.tcinputs['TenantBackupContent'],
                                                                    "plan": self.tcinputs['Plan']})

            # Update the hypervisor
            decorative_log("Updating hypervisor created with Access secret")
            self.hypervisor_ac_obj.select_hypervisor(self.client_name)
            self.hypervisor_details_obj.edit_hypervisor_details(vendor=hypervisor_type.AMAZON_AWS.value,
                                                                auth_type=self.tcinputs['Auth_type'],
                                                                credential=self.tcinputs['Credential'])
            # Validate the hypervisor
            decorative_log("Validating hypervisor with Access secret")
            self.vsa_obj.validate_hypervisor(self.client_name,
                                             validate_input={"vendor": hypervisor_type.AMAZON_AWS.value,
                                                             "auth_type": self.tcinputs['Auth_type'],
                                                             "credential": self.tcinputs['Credential']})

            # Update the hypervisor
            decorative_log("Updating hypervisor created with IAM")
            self.hypervisor_ac_obj.select_hypervisor(self.client_name)
            self.hypervisor_details_obj.edit_hypervisor_details(vendor=hypervisor_type.AMAZON_AWS.value,
                                                                auth_type="IAM role")

            # Validate the hypervisor
            decorative_log("Validating hypervisor with IAM")
            self.vsa_obj.validate_hypervisor(self.client_name,  validate_input={"vendor": hypervisor_type.AMAZON_AWS.value,
                                                                                "auth_type": "IAM role",
                                                                                "credential": None})
            decorative_log("Updating hypervisor back with STS for next run")
            self.hypervisor_ac_obj.select_hypervisor(self.client_name)
            self.hypervisor_details_obj.edit_hypervisor_details(vendor=hypervisor_type.AMAZON_AWS.value,
                                                                auth_type="STS assume role with IAM policy",
                                                                credential=role_name)
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)
