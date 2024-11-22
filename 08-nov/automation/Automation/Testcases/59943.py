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

from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell

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
        self.name = "Companies - Privacy feature at company level"
        self.ta_commcell = None
        self.organization = None
        self.client = None
        self.backupset = None
        self.instance = None
        self.client_name = None
        self.config = get_config()
        self.tcinputs = {
            "machine_host": None,
            "machine_username": None,
            "machine_password": None,
            "plan_name": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.password = self.config.MSPCompany.tenant_password
        self.infos = OrganizationHelper(self.commcell).setup_company(ta_password=self.password)
        self.company_name = self.infos['company_name']
        self.ta_commcell = self.infos['ta_loginobj']

        self.client_owner_name = "clientowner"
        self.commcell.users.add(self.client_owner_name,
                                   "client@owner.com",
                                   "Client Owner",
                                   password=self.password)

        self.owner_commcell = Commcell(self.commcell.webconsole_hostname,
                                       commcell_username=self.client_owner_name,
                                       commcell_password=self.password)
        self.organization = self.ta_commcell.organizations.get(self.company_name)
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
        self.client = self.install_client()
        self.client_name = self.client.client_name

        self.client.add_client_owner([self.client_owner_name])

        self.plan = self.commcell.plans.get(self.tcinputs['plan_name'])
        self.plan_name = self.tcinputs['plan_name']
        self.msp_orghelper_obj = OrganizationHelper(self.commcell, self.company_name)


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
        return client

    @test_step
    def validate_tenant_privacy(self):
        """Step to validate the company data privacy"""
        self.log.info("Enabling company data privacy at company level")
        self.organization.enable_company_data_privacy()
        client = self.ta_commcell.clients.get(self.machine_name)
        self.agent = client.agents.get('File System')
        self.instance = self.agent.instances.get('DefaultInstanceName')
        self.backupset = self.instance.backupsets.get("defaultbackupset")
        try:
            self.backupset.browse()
            raise Exception("MSP admin should not be able to browse tenant data")
        except Exception as exp:
            self.log.info("MSP admin should not be able to browse tenant data")

    def run(self):
        """Run function of this test case"""
        try:
            self.run_backup()

            self.log.info("Enabling Privacy at Commcell Level")
            self.commcell.enable_privacy()

            self.validate_tenant_privacy()

            self.validate_owner_privacy_negative_case()

            self.validate_owner_privacy()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.commcell.refresh()

        if self.infos:
            msp_orghelper_obj = OrganizationHelper(self.commcell, self.company_name)
            msp_orghelper_obj.delete_company(wait=True)
        self.commcell.disable_privacy()
        self.commcell.users.delete(self.client_owner_name, "admin")

    @test_step
    def validate_owner_privacy_negative_case(self):
        """Negative case to verify that owner privacy is not usable unless permission is
        given by tenant admin
        """
        client = self.owner_commcell.clients.get(self.machine_name)
        try:
            client.enable_owner_privacy()
            raise Exception("The Owner should not be able to enable this option unless Tenant Admin gives permission")
        except Exception as exp:
            self.log.info("Working, The Owner should not be able to enable this option unless Tenant Admin gives permission")

    @test_step
    def validate_owner_privacy(self):
        """Validating client privacy which can be enabled by owner"""
        self.organization.enable_owner_data_privacy()
        client = self.owner_commcell.clients.get(self.machine_name)
        client.enable_owner_privacy()
        self.agent = client.agents.get('File System')
        self.instance = self.agent.instances.get('DefaultInstanceName')
        self.backupset = self.instance.backupsets.get("defaultbackupset")
        self.backupset.browse()

    def run_backup(self):
        """Runs backup on newly created client"""
        value = {
            'client_display_name': self.client_name,
            'agent': "File System",
            'backupset_name': "defaultBackupSet",
            'subclient_name': "default",
            'plan_name': self.plan_name
        }
        subc_obj, job = self.msp_orghelper_obj.run_backup_on_company_client(value)
        job.wait_for_completion()
