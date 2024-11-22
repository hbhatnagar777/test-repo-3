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

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.Common.page_object import handle_testcase_exception
from cvpysdk.client import Clients
from random import randrange


class TestCase(CVTestCase):
    """Test case for performing CRUD on VMware Cloud director Organization Hypervisor. """

    def __init__(self):
        """ Initializes test case class objects"""
        super(TestCase, self).__init__()
        self.name = "VMware Cloud director Hypervisor CRUD"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.tenant_client = 'tenant_hyp_del_' + str(randrange(10000, 99999))
        self.vm_group_name = 'vm_group_del_' + self.tenant_client
        self.browser = None
        self.parent_vsa_obj = None
        self.vsa_obj = None
        self.admin_console = None
        self.hypervisor_details_obj = None
        self.hypervisor_ac_obj = None
        self.associated_vcenter_names = None
        self.utils = TestCaseUtils(self)

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

        def create_and_validate(hv_inputs=None, tenant=False):

            self.hypervisor_ac_obj.add_hypervisor(**hv_inputs)

            self.tcinputs['ClientName'] = self.tenant_client
            self.reinitialize_testcase_info()
            vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser, self.commcell, self.csdb)
            self.vsa_obj = vsa_obj

            vsa_obj.validate_hypervisor(hypervisor_name=self.tcinputs['ClientName'],
                                        validate_input=inputs)

        try:

            """
            create_and_validate(tenant=True)
            delete tenant

            """
            organization = self.tcinputs['VMContent']['Content'][0]['Organizations']['Organizations'][0].split('/')[0]
            inputs = {
                "vendor": HypervisorDisplayName.Vcloud.value,
                "vm_group_name": self.vm_group_name,
                "plan": self.tcinputs['Plan'],
                "server_name": self.tenant_client,
                "vm_content": self.tcinputs['VMContent'],
                "admin_hypervisor": self.tcinputs["ClientName"],
                "vcloud_organization": organization,
                "company": self.tcinputs["Company"]
            }
            create_and_validate(inputs, tenant=True)
            self.admin_console.navigator.navigate_to_hypervisors()
            if self.hypervisor_ac_obj.is_hypervisor_exists(self.tenant_client):
                self.hypervisor_ac_obj.retire_hypervisor(self.tenant_client)
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):

        self.log.info("Cleaning up Tenant hypervisor")
        clients_obj = Clients(self.commcell)
        try:
            clients_obj.delete(self.tenant_client)
            self.log.info("Tenant vCloud hypervisor deleted - {}".format(self.tenant_client))
        except Exception as exp:
            self.log.info("Tenant hypervisor might already be cleaned up - {}".format(str(exp)))
