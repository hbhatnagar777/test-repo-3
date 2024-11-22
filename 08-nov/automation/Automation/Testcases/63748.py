# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing hypervisors CRUD case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Azure hypervisors CRUD case"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.client_name = "Auto_63748_c"
        self.vm_group_name = "Auto_63748"
        self.hypervisor_details_obj = None
        self.hypervisor_ac_obj = None
        self.admin_console = None
        self.vsa_obj = None
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
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.hypervisor_details_obj = HypervisorDetails(self.admin_console)
        self.hypervisor_ac_obj = Hypervisors(self.admin_console)

    def run(self):
        try:
            # Creating Non-MSI client
            decorative_log("Creating Non-MSI Client")
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.add_hypervisor(vendor=hypervisor_type.MICROSOFT_AZURE.value,
                                                  server_name=self.client_name,
                                                  proxy_list=self.tcinputs['Proxy_list'],
                                                  auth_type="Non-MSI",
                                                  credential=self.tcinputs['Credential'],
                                                  vm_group_name=self.vm_group_name,
                                                  vm_content=self.tcinputs['BackupContent'],
                                                  plan=self.tcinputs['Plan'],
                                                  subscription_id=self.tcinputs['Subscription_id']
                                                  )

            self.tcinputs['ClientName'] = self.client_name
            self.reinitialize_testcase_info()
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                     self.commcell, self.csdb)

            # Validate the hypervisor creation
            decorative_log("Validating Non-MSI client created with the inputs")
            self.vsa_obj.validate_hypervisor(self.client_name,
                                             validate_input={"vendor": hypervisor_type.MICROSOFT_AZURE.value,
                                                             "server_name": self.client_name,
                                                             "proxy_list": self.tcinputs['Proxy_list'],
                                                             "auth_type": "Non-MSI",
                                                             "credential": self.tcinputs['Credential'],
                                                             "vm_group_name": self.vm_group_name,
                                                             "vm_content": self.tcinputs['BackupContent'],
                                                             "plan": self.tcinputs['Plan'],
                                                             "subscription_id": self.tcinputs['Subscription_id']})

            # Update the hypervisor
            decorative_log("Updating Non-MSI client created")
            self.hypervisor_ac_obj.select_hypervisor(self.client_name)
            self.hypervisor_details_obj.edit_hypervisor_details(vendor=hypervisor_type.MICROSOFT_AZURE.value,
                                                                auth_type="Non-MSI",
                                                                subscription_id=self.tcinputs['New_subscription_id'],
                                                                credential=self.tcinputs['New_credential'])

            # Validate the hypervisor
            decorative_log("Validating Non-MSI client")
            self.vsa_obj.validate_hypervisor(self.client_name,
                                             validate_input={"auth_type": "Non-MSI",
                                                             "subscription_id": self.tcinputs['New_subscription_id'],
                                                             "credential": self.tcinputs['New_credential']})

            # Delete the hypervisor
            decorative_log("Deleting Non-MSI client")
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.retire_hypervisor(self.client_name)

            # Validate whether hypervisor deleted or not.
            decorative_log("Checking for deleted Non-MSI client")
            self.admin_console.navigator.navigate_to_hypervisors()
            if not self.hypervisor_ac_obj.is_hypervisor_exists(self.client_name):
                self.log.info("Hypervisor doesnt exist")
                pass
            else:
                self.log.error("Hypervisor not deleted")
                raise Exception

            # Creating MSI client
            decorative_log("Creating MSI Client")
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.add_hypervisor(vendor=hypervisor_type.MICROSOFT_AZURE.value,
                                                  server_name=self.client_name,
                                                  proxy_list=self.tcinputs['Proxy_list'],
                                                  auth_type="MSI",
                                                  vm_group_name=self.vm_group_name,
                                                  vm_content=self.tcinputs['BackupContent'],
                                                  plan=self.tcinputs['Plan'],
                                                  subscription_id=self.tcinputs['Subscription_id']
                                                  )

            # Validate the hypervisor creation
            decorative_log("Validating MSI client created with the inputs")
            self.vsa_obj.validate_hypervisor(self.client_name,
                                             validate_input={"vendor": hypervisor_type.MICROSOFT_AZURE.value,
                                                             "server_name": self.client_name,
                                                             "proxy_list": self.tcinputs['Proxy_list'],
                                                             "auth_type": "MSI",
                                                             "vm_content": self.tcinputs['BackupContent'],
                                                             "plan": self.tcinputs['Plan'],
                                                             "vm_group_name": self.vm_group_name,
                                                             "vm_content": self.tcinputs['BackupContent'],
                                                             "subscription_id": self.tcinputs['Subscription_id']})

            # Update the hypervisor
            decorative_log("Updating MSI client")
            self.hypervisor_ac_obj.select_hypervisor(self.client_name)
            self.hypervisor_details_obj.edit_hypervisor_details(vendor=hypervisor_type.MICROSOFT_AZURE.value,
                                                                auth_type="MSI",
                                                                subscription_id=self.tcinputs['New_subscription_id'])

            # Validate the hypervisor
            decorative_log("Validating MSI client after edit operation")
            self.vsa_obj.validate_hypervisor(self.client_name,
                                             validate_input={"auth_type": "MSI",
                                                             "subscription_id": self.tcinputs['New_subscription_id']})

            # Delete the hypervisor
            decorative_log("Deleting hypervisor")
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.retire_hypervisor(self.client_name)

            # Validate whether hypervisor deleted or not.
            decorative_log("Checking for deleted hypervisor")
            self.admin_console.navigator.navigate_to_hypervisors()
            if not self.hypervisor_ac_obj.is_hypervisor_exists(self.client_name):
                self.log.info("Hypervisor does not exist")
                pass
            else:
                self.log.error("Hypervisor not deleted")
                raise Exception
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)
