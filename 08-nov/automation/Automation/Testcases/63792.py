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
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils

from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.Common.page_object import handle_testcase_exception
from cvpysdk.client import Clients

from random import randrange


class TestCase(CVTestCase):
    """Test case for performing CRUD on VMware Cloud director Hypervisor. """

    def __init__(self):
        """ Initializes test case class objects"""
        super(TestCase, self).__init__()
        self.name = "VMware Cloud director Hypervisor CRUD"
        self.test_individual_status = True
        self.browser = None
        self.parent_vsa_obj = None
        self.vsa_obj = None
        self.tenant_client = None
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

        self.associated_vcenter_names = [i.split(".")[0] + '_' + self.client_name
                                         for i in self.tcinputs['AssociatedVcenters'].keys()]

        self.hypervisor_details_obj = HypervisorDetails(self.admin_console)
        self.hypervisor_ac_obj = Hypervisors(self.admin_console)

    def run(self):
        """Main function for testcase execution"""

        def create_and_validate(hv_inputs=None, tenant=False):
            self.hypervisor_ac_obj.add_hypervisor(**hv_inputs)

            self.tcinputs['ClientName'] = self.client_name if not tenant else self.tenant_client
            self.reinitialize_testcase_info()

            vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser, self.commcell, self.csdb)

            if tenant:
                self.vsa_obj = vsa_obj
            else:
                self.parent_vsa_obj = vsa_obj

            vsa_obj.validate_hypervisor(hypervisor_name=self.tcinputs['ClientName'],
                                        validate_input=inputs)

        try:

            """
            create_and_validate()
            ...
            edit and validate()
            ...
            create_and_validate(tenant=True)
            delete tenant
            
            delete admin flow
            """

            inputs = {}

            for idx, client in enumerate(self.tcinputs['Clients']):
                self.client_name = client['ClientName']
                self.tcinputs['Credential'] = client['Credential']
                self.tcinputs['HostName'] = client['HostName']
                self.tcinputs['VMContent'] = self.tcinputs['VMContents'][idx]
                self.client_name = 'vCloud_Del_' + str(randrange(10000, 99999))
                self.vm_group_name = 'vm_group_' + self.client_name
                if idx == 0:
                    associated_vcenters_creds = dict(list(self.tcinputs['AssociatedVcenters'].items())[:2])
                elif idx == 1:
                    associated_vcenters_creds = dict(list(self.tcinputs['AssociatedVcenters'].items())[1:])

                self.associated_vcenter_names = [
                    i.split(".")[0] + '_' + self.client_name for i in associated_vcenters_creds.keys()]


                inputs = {
                    "vendor": HypervisorDisplayName.Vcloud.value,
                    "proxy_list": self.tcinputs['ProxyList'][-1:],
                    "credential": self.tcinputs['Credential'],
                    "vm_group_name": self.vm_group_name,
                    "plan": self.tcinputs['Plan'],
                    "associated_vcenters": self.associated_vcenter_names,
                    "server_name": self.client_name,
                    "vm_content": self.tcinputs['VMContent'],
                    "host_name": self.tcinputs['HostName'],
                    "ssl_check": {}
                }
                create_and_validate(inputs)

                self.hypervisor_ac_obj.select_hypervisor(self.client_name)
                decorative_log("Updating hypervisor access nodes")
                self.hypervisor_details_obj.edit_proxy(proxies=self.tcinputs['Edit_proxy_list'],
                                                       remove_existing_proxies=True)
                self.hypervisor_details_obj.edit_hypervisor_details(saved_credentials=self.tcinputs['Credential'][-1],
                                                                    vendor=HypervisorDisplayName.Vcloud.value)

                inputs['proxy_list'] = self.tcinputs['ProxyList']
                inputs['credentials'] = self.tcinputs['Credential'][-1]

            # Tenant Hypervisor CRUD
            self.tenant_client = 'tenant_' + self.client_name
            organization = self.tcinputs['VMContent']['Content'][0].split('/')[0]

            tenant_inputs = {}

            for key in tenant_keys:
                if key in inputs.keys():
                    tenant_inputs[key] = inputs[key]

            tenant_inputs['admin_hypervisor'] = self.client_name
            tenant_inputs['server_name'] = self.tenant_client
            tenant_inputs['vcloud_organization'] = organization

            create_and_validate(tenant_inputs, tenant=True)

            inputs['tenant_accounts'] = [self.tenant_client]

            inputs['server_name'] = self.client_name
            self.parent_vsa_obj.validate_hypervisor(hypervisor_name=self.client_name, validate_input=inputs)

            self.admin_console.navigator.navigate_to_hypervisors()
            if self.hypervisor_ac_obj.is_hypervisor_exists(self.tenant_client):
                self.hypervisor_ac_obj.retire_hypervisor(self.tenant_client)

            self.parent_vsa_obj.retire_associated_vcenters()
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.retire_hypervisor(self.client_name)

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close(self.browser)

    def tear_down(self):

        self.log.info("Cleaning up hypervisors.")

        clients_obj = Clients(self.commcell)

        try:
            clients_obj.delete(self.tenant_client)
            self.log.info("Tenant vCloud hypervisor deleted - {}".format(self.tenant_client))
        except Exception as exp:
            self.log.info("Tenant hypervisor might already be cleaned up - {}".format(str(exp)))

        try:
            for vcenter in self.associated_vcenter_names:
                clients_obj.delete(vcenter)
                self.log.info("Cleaned up associated vCenter - {}".format(vcenter))
        except Exception as exp:
            self.log.info("Associated vCenters might already be cleaned up. Check Exception - " + str(exp))

        try:
            clients_obj.delete(self.client_name)
            self.log.info("Cleaned up vCloud Hypervisor - {}".format(self.client_name))
        except Exception as exp:
            self.log.info("vCloud Hypervisor might not exist or was already cleaned up - " + str(exp))