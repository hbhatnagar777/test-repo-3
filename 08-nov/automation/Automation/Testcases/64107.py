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
import time

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
from cvpysdk.credential_manager import Credentials


class TestCase(CVTestCase):
    """Class for executing hypervisors CRUD case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA HyperV hypervisors CRUD case"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.client_name = "Auto_02_c"
        self.vm_group_name = "Auto_02"
        self.hypervisor_details_obj = None
        self.hypervisor_ac_obj = None
        self.admin_console = None
        self.vsa_obj = None
        self.credential_obj = None
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
        self.credential_obj = Credentials(self.commcell)

    def run(self):
        try:
            # Creating Hyper-V client
            decorative_log("Creating Hyper-V Client")
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.add_hypervisor(vendor=hypervisor_type.MS_VIRTUAL_SERVER.value,
                                                  server_name=self.client_name,
                                                  vs_username=self.tcinputs.get('username', None),
                                                  vs_password=self.tcinputs.get('password', None),
                                                  proxy_list=self.tcinputs['Proxy_list'],
                                                  credential=self.tcinputs['credential'],
                                                  vm_group_name=self.vm_group_name,
                                                  vm_content=self.tcinputs['BackupContent'],
                                                  plan=self.tcinputs['Plan'],
                                                  host_name=self.tcinputs['hostname']
                                                  )

            self.tcinputs['ClientName'] = self.client_name
            self.reinitialize_testcase_info()
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                     self.commcell, self.csdb)

            # Validate the hypervisor creation
            decorative_log("Validating Hyper-V client created with the inputs")
            self.vsa_obj.validate_hypervisor(self.client_name,
                                             validate_input={"vendor": hypervisor_type.MS_VIRTUAL_SERVER.value,
                                                             "server_name": self.client_name,
                                                             "proxy_list": self.tcinputs['Proxy_list'],
                                                             "credential": self.tcinputs['credential'],
                                                             "vm_group_name": self.vm_group_name,
                                                             "vm_content": self.tcinputs['BackupContent'],
                                                             "plan": self.tcinputs['Plan'],
                                                             "username": self.tcinputs['username'],
                                                             "hostname": self.tcinputs['hostname']})

            # Update the hypervisor
            decorative_log("Updating Hyper-V client with new values")
            self.hypervisor_ac_obj.select_hypervisor(self.client_name)
            self.hypervisor_details_obj.edit_hypervisor_details(vendor=hypervisor_type.MS_VIRTUAL_SERVER.value,
                                                                vs_hostname=self.tcinputs['new_hostname'],
                                                                vs_username=self.tcinputs['new_username'],
                                                                vs_password=self.tcinputs['new_password'],
                                                                credential=self.tcinputs['new_credential'])

            # Validate the hypervisor
            decorative_log("Validating updated Hyper-V client")
            self.vsa_obj.validate_hypervisor(self.client_name,
                                             validate_input={"vendor": hypervisor_type.MS_VIRTUAL_SERVER.value,
                                                             "username": self.tcinputs['new_username'],
                                                             "hostname": self.tcinputs['new_hostname'],
                                                             "credential": self.tcinputs['new_credential']})

            # Delete the hypervisor
            decorative_log("Deleting Hyper-V client")
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.retire_hypervisor(self.client_name)
            self.log.info('Sleeping for 20 mins before deleting the credential')
            time.sleep(1200)
            self.log.info(f"Deleting credential if exists: {self.tcinputs['credential']}")
            if self.credential_obj.has_credential(self.tcinputs['credential']):
                self.credential_obj.delete(self.tcinputs['credential'])

            self.log.info(f"Deleting credential if exists: {self.tcinputs['new_credential']}")
            if self.credential_obj.has_credential(self.tcinputs['new_credential']):
                self.credential_obj.delete(self.tcinputs['new_credential'])

            # Validate whether hypervisor deleted or not.
            decorative_log("Checking for deleted Hyper-V client")
            self.admin_console.navigator.navigate_to_hypervisors()
            if not self.hypervisor_ac_obj.is_hypervisor_exists(self.client_name):
                self.log.info("Hypervisor doesnt exist")
            else:
                self.log.error("Hypervisor not deleted")
                raise Exception

            self.log.info("Checking if credentials are deleted")
            if self.credential_obj.has_credential(self.tcinputs['credential']) \
               or self.credential_obj.has_credential(self.tcinputs['new_credential']):
                self.log.error("Credential still present")
                raise Exception
            self.log.info('Credential deleted successfully')
            self.log.info("Deletion Validation complete")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)