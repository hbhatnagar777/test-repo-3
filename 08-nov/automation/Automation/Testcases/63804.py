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

    run()           --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils

from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors

from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Test case for performing CRUD on Nutanix AHV Hypervisor. """

    def __init__(self):
        """ Initializes test case class objects"""
        super(TestCase, self).__init__()
        self.name = "Hypervisor CRUD for Nutanix AHV"
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.hypervisor_details_obj = None
        self.hypervisor_ac_obj = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = ()

    def setup(self):
        decorative_log("Initalising Browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        decorative_log("Creating login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.hypervisor_details_obj = HypervisorDetails(self.admin_console)
        self.hypervisor_ac_obj = Hypervisors(self.admin_console)

    def run(self):
        """Main function for testcase execution"""
        try:
            self.admin_console.navigator.navigate_to_hypervisors()
            #delete if Hypervisor exists
            if self.hypervisor_ac_obj.is_hypervisor_exists(self.tcinputs['new_client']):
                self.hypervisor_ac_obj.retire_hypervisor(self.tcinputs['new_client'])
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.add_hypervisor(vendor=hypervisor_type.Nutanix.value,
                                                   server_name=self.tcinputs['new_client'],
                                                   host_name=self.tcinputs['host_name'],
                                                   proxy_list=self.tcinputs['proxy'],
                                                   vs_password=self.tcinputs['password'],
                                                   vs_username=self.tcinputs['username'],
                                                   vm_group_name=self.tcinputs['new_vmgroup'],
                                                   vm_content=self.tcinputs['vm_content'],
                                                   plan=self.tcinputs['plan']
                                        
                                                   )
            self.tcinputs['ClientName'] = self.tcinputs['new_client']
            self.reinitialize_testcase_info()
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser, self.commcell, self.csdb)
            #Validate Hypervisor
            self.vsa_obj.validate_hypervisor(hypervisor_name=self.tcinputs['new_client'],
                                             validate_input=
                                             {"vendor": hypervisor_type.Nutanix.value,
                                              "server_name": self.tcinputs['new_client'],
                                              "proxy_list": self.tcinputs['proxy'],
                                              "vm_group_name": self.tcinputs['new_vmgroup'],
                                              "plan": self.tcinputs['plan'],
                                              "vs_username" : self.tcinputs['username'],
                                               "host_name" : self.tcinputs['host_name'],
                                              "vm_content": self.tcinputs['vm_content']
                                             
                                              })
            #Delete Hypervisor
            decorative_log("Deleting hypervisor")
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.retire_hypervisor(self.tcinputs['new_client'])
            #Check if Hypervisor deleted
            decorative_log("Checking for deleted hypervisor")
            self.admin_console.navigator.navigate_to_hypervisors()
            if not self.hypervisor_ac_obj.is_hypervisor_exists(self.tcinputs['new_client']):
                self.log.info("Hypervisor deleted successfully")
            else:
                self.log.error("Hypervisor not deleted")
                raise Exception
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
