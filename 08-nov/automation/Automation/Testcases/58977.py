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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from queue import Queue
from threading import Thread

from cvpysdk.clientgroup import ClientGroups, ClientGroup
from cvpysdk.commcell import Commcell

from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper
from Server.organizationhelper import OrganizationHelper
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Companies - Create client groups as Tenant Admin and Operator"
        self.config = get_config()
        self.ta_clientgroup = "test58977_cg_ta"
        self.to_clientgroup = "test58977_cg_to"
        self.ta_smartclientgroup = "test58977_scg_ta"
        self.to_smartclientgroup = "test58977_scg_to"
        self.tcinputs = {
            "machine_host": None,
            "machine_username": None,
            "machine_password": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.password = self.config.MSPCompany.tenant_password
        self.infos = OrganizationHelper(self.commcell).setup_company(ta_password=self.password,
                                                                     to_password=self.password)
        self.company_name = self.infos['company_name']
        self.ta_commcell = self.infos['ta_loginobj']
        self.ta_scg_helper = SmartClientHelper(self.ta_commcell)

        self.to_commcell = self.infos['to_loginobj']
        self.to_commcell.switch_to_company(self.company_name)
        self.to_scg_helper = SmartClientHelper(self.to_commcell)
        self.clientgroup_obj = ClientGroups(self.commcell)
        self.config_json = get_config()
        self.machine_name = self.config_json.Install.windows_client.machine_host if not self.tcinputs else \
        self.tcinputs['machine_host']
        self.machine_username = self.config_json.Install.windows_client.machine_username if not self.tcinputs else \
        self.tcinputs['machine_username']
        self.machine_password = self.config_json.Install.windows_client.machine_password if not self.tcinputs else \
        self.tcinputs['machine_password']
        self.msp = OrganizationHelper(commcell=self.commcell)
        self.ta_org_helper = OrganizationHelper(self.ta_commcell, company=self.company_name)

        common_password = self.inputJSONnode['commcell']['commcellPassword']

        # uninstall client, if client is already installed - [we need fresh client for this test case]
        self.queue = Queue()
        self.t1 = Thread(target=lambda queue, clientname: queue.put(self.msp.uninstall_client(client_name=clientname)),
                         args=(self.queue, self.machine_name,))
        self.t1.start()

    def run(self):
        """Run function of this test case"""
        try:
            self.install_client()

            self.create_CG_as_tenant_admin()
            self.check_if_user_has_clientgroup(self.to_commcell, self.ta_clientgroup)

            self.create_CG_as_tenant_operator()
            self.check_if_user_has_clientgroup(self.ta_commcell, self.to_clientgroup)

            self.create_SCG_as_tenant_admin()
            self.check_if_user_has_clientgroup(self.to_commcell, self.ta_smartclientgroup)

            self.create_SCG_as_tenant_operator()
            self.check_if_user_has_clientgroup(self.ta_commcell, self.to_smartclientgroup)

            self.edit_company_scg_as_diff_persona()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        CG_list = [self.ta_clientgroup, self.ta_smartclientgroup, self.to_clientgroup, self.to_smartclientgroup]
        self.clientgroup_obj.refresh()
        for group in CG_list:
            self.clientgroup_obj.delete(group)

        self.commcell.refresh()

        if self.infos:
            self.commcell.users.delete(user_name=self.infos['to_name'], new_user='admin')
            msp_orghelper_obj = OrganizationHelper(self.commcell, self.company_name)
            msp_orghelper_obj.delete_company(wait=True)

    @test_step
    def create_CG_as_tenant_admin(self):
        """Creates a client group, add clients to it as a tenant admin"""
        clients_list = list(self.ta_commcell.clients.all_clients.keys())
        self.ta_commcell.client_groups.add(self.ta_clientgroup,
                                           clients_list,
                                           clientgroup_description="testdescp")
        self.check_if_cg_has_client(self.ta_clientgroup)

    @test_step
    def create_CG_as_tenant_operator(self):
        """Creates a client group, add clients to it as a tenant operator"""
        clients_list = list(self.to_commcell.clients.all_clients.keys())
        self.to_commcell.client_groups.add(self.to_clientgroup,
                                           clients_list,
                                           clientgroup_description="testdescp")
        self.check_if_cg_has_client(self.to_clientgroup)

    def check_if_user_has_clientgroup(self, user_commcell_obj, clientgroup):
        """Checks if the user has access to the clientgroup"""
        self.log.info("Checking if user has access to client group")
        user_commcell_obj.refresh()
        user_commcell_obj.client_groups.get(clientgroup)

    def check_if_cg_has_client(self, client_group_name):
        """Checks if client is associated to newly created client group"""
        self.commcell.refresh()
        client_group = self.commcell.client_groups.get(client_group_name)
        if self.client.client_name not in client_group.associated_clients:
            raise Exception("The client should be associated to the clientgroup")

        self.log.info(f"{self.client.client_name} is a part of clientgroup {client_group}")

    def create_SCG(self, commcell_obj, scg_helper_obj, name):
        cg_obj = ClientGroups(commcell_obj)
        scg_rule = cg_obj.create_smart_rule()
        scg_helper_obj.client_scope = 'Clients of User'
        scg_helper_obj.value = self.infos['ta_name']
        scg_helper_obj.group_name = name
        scg_helper_obj.description = "testdescp"
        scg_helper_obj.create_smart_client([scg_rule])

    @test_step
    def create_SCG_as_tenant_admin(self):
        """Creates a smart client group, add clients to it as tenant admin"""
        self.create_SCG(self.ta_commcell, self.ta_scg_helper, self.ta_smartclientgroup)
        self.check_if_cg_has_client(self.ta_smartclientgroup)

    @test_step
    def create_SCG_as_tenant_operator(self):
        """Creates a smart client group, add clients to it as tenant operator"""
        self.create_SCG(self.to_commcell, self.to_scg_helper, self.to_smartclientgroup)
        self.check_if_cg_has_client(self.to_smartclientgroup)

    @test_step
    def edit_company_scg_as_diff_persona(self):
        """Attempts to edit a company created smart client group"""
        self.log.info("Editing company smart client group as MSP admin")
        self.edit_company_scg(self.commcell)

        self.log.info("Editing company smart client group as tenant admin")
        self.edit_company_scg(self.ta_commcell)

        self.log.info("Editing company smart client group as tenant operator")
        self.edit_company_scg(self.to_commcell)

    def edit_company_scg(self, commcell):
        """Attempts to edit a company created smart client group"""
        scg_helper = SmartClientHelper(commcell, group_name=self.company_name)
        client_group = scg_helper.update_scope(self.company_name, 'Clients of user', self.infos['ta_name'])
        if client_group:
            raise Exception(
                f"{commcell.commcell_username} should not be able to edit default company client group"
            )
        else:
            self.log.info(
                f"Working as expected!,"
                f"{commcell.commcell_username} should not be able to edit default company client group")

    def install_client(self):
        """Installs a client for associating with CG"""
        # wait for client uninstallation to complete
        self.t1.join()
        # if uninstallation thread failed to clean up the existing client, will retry again
        self.log.info('Uninstallation Thread Joined... If it was a failure, will retry')
        if (self.queue.empty() or (not self.queue.get())) and (not self.msp.uninstall_client(self.machine_name)):
            raise Exception(f'Uninstalling Client [{self.machine_name}] Failed!')
        self.log.info(f'Uninstalling Client [{self.machine_name}] Success!')

        # installing file system client as tenant admin
        self.ta_commcell.refresh()

        # Installing Client with two tries
        if (
                not self.ta_org_helper.install_client(self.machine_name, self.machine_username,
                                                      self.machine_password)) and \
                (not self.ta_org_helper.install_client(self.machine_name, self.machine_username,
                                                       self.machine_password)):
            raise Exception(f'Client Install Failed even with two tries!')
        self.log.info('Client Installation Finished!')

        self.commcell.refresh()
        client = self.commcell.clients.get(name=self.machine_name)
        self.client = client
