# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing hypervisors CRUD case"""

    def __init__(self):
        """VSA VMware Hypervisor CRUD Operations"""
        super(TestCase, self).__init__()
        self.name = "VSA Oracle VM Hypervisor CRUD Operations"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.client_name = "OVM_CRUD_TEST_HYPERVISOR"
        self.vm_group_name = "OVM_CRUD_TEST_VM_GROUP"
        self.hypervisor_details_obj = None
        self.hypervisor_ac_obj = None
        self.admin_console = None
        self.vsa_obj = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            'ProxyList': None,
            'NewProxyList': None,
            'BackupContent': None,
            'Plan': None,
            'UserName': None,
            'Password': None,
            'UserName2': None,
            'Password2': None,
            'AgentName': None,
            'InstanceName': None
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
            decorative_log("creating hypervisor")
            self.admin_console.navigator.navigate_to_hypervisors()

            self.hypervisor_ac_obj.add_hypervisor(vendor=HypervisorDisplayName.ORACLE_VM.value,
                                                  host_name=self.tcinputs['HostName'],
                                                  server_name=self.client_name,
                                                  proxy_list=self.tcinputs['ProxyList'],
                                                  vs_password=self.tcinputs['Password'],
                                                  vs_username=self.tcinputs['UserName'],
                                                  vm_group_name=self.vm_group_name,
                                                  vm_content=self.tcinputs['BackupContent'],
                                                  plan=self.tcinputs['Plan']
                                                  )

            self.tcinputs['ClientName'] = self.client_name
            self.reinitialize_testcase_info()
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                     self.commcell, self.csdb)
            decorative_log("Validating hypervisor created with the inputs")
            self.vsa_obj.validate_hypervisor(self.client_name,
                                             validate_input={"vendor": HypervisorDisplayName.ORACLE_VM.value,
                                                             "server_name": self.client_name,
                                                             "proxy_list": self.tcinputs['ProxyList'],
                                                             "vs_username": self.tcinputs['UserName'],
                                                             "vm_group_name": self.vm_group_name,
                                                             "vm_content": self.tcinputs['BackupContent'],
                                                             "plan": self.tcinputs['Plan']})

            decorative_log("Updating hypervisor credentials")
            self.hypervisor_ac_obj.select_hypervisor(self.client_name)
            self.hypervisor_details_obj.edit_hypervisor_details(vendor=HypervisorDisplayName.ORACLE_VM.value,
                                                                vs_username=self.tcinputs['UserName2'],
                                                                vs_password=self.tcinputs['Password2'])

            decorative_log("Updating hypervisor access nodes")
            self.hypervisor_details_obj.edit_proxy(self.tcinputs['NewProxyList'], remove_existing_proxies=True)

            # Validate the hypervisor
            decorative_log("Validating hypervisor credentials and access nodes")
            self.vsa_obj.validate_hypervisor(self.client_name,
                                             validate_input={"vendor": HypervisorDisplayName.ORACLE_VM.value,
                                                             "vs_username": self.tcinputs['UserName2'],
                                                             "proxy_list": self.tcinputs[
                                                                 'NewProxyList']})

            # Delete the hypervisor
            decorative_log("Deleting hypervisor")
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.retire_hypervisor(self.client_name)

            # Validate whether hypervisor deleted or not.
            decorative_log("checking for deleted hypervisor")
            self.admin_console.navigator.navigate_to_hypervisors()
            if not self.hypervisor_ac_obj.is_hypervisor_exists(self.client_name):
                self.log.info("Hypervisor doesnt exist")
                pass
            else:
                self.log.error("hypervisor not deleted")
                raise Exception
        except Exception as exp:
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)
            handle_testcase_exception(self, exp)

        finally:
            try:
                self.admin_console.navigator.navigate_to_hypervisors()
                self.hypervisor_ac_obj.retire_hypervisor(self.client_name)
            except Exception as exp:
                pass
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
