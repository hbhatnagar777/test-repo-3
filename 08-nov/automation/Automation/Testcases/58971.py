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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Web.Common.page_object import TestStep
import random
from Server.organizationhelper import OrganizationHelper
from cvpysdk.subclient import Subclients
from threading import Thread
from AutomationUtils import config
from queue import Queue

class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        This testcase verifies:
            1. Associating plan to company
            2. Setting default plan for company.
            3. Switching default plans as MSP, TA and Operator.
            4. Functionality of default plan. New client should get assigned to default plan.
        """
        super(TestCase, self).__init__()
        self.name = "Companies - Create a company without a plan"

        self.plan1 = self.plan2 = self.spool1 = self.spool2 = self.infos = self.subclient = None
        self.tcinputs = {}
        """
        Either pass Client Details via Input Json or Config.json [config_json.Install.windows_client]
        tcinputs = {
            'machine_host' : '',
            'machine_username' : '',
            'machine_password' : '' # base 64 encoded password
        }
        """

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.machine_name = self.config_json.Install.windows_client.machine_host if not self.tcinputs else self.tcinputs['machine_host']
        self.machine_username = self.config_json.Install.windows_client.machine_username if not self.tcinputs else self.tcinputs['machine_username']
        self.machine_password = self.config_json.Install.windows_client.machine_password if not self.tcinputs else self.tcinputs['machine_password']
        
        common_password = self.inputJSONnode['commcell']['commcellPassword']
        self.admin = Commcell(self.commcell.webconsole_hostname, self.inputJSONnode['commcell']['commcellUsername'], common_password)
        
        # uninstall client, if client is already installed - [we need fresh client for this test case]
        self.msp = OrganizationHelper(commcell= self.admin)
        self.queue = Queue()
        self.t1 = Thread(target= lambda queue, clientname: queue.put(self.msp.uninstall_client(client_name= clientname)), args= (self.queue, self.machine_name, ))
        self.t1.start()
        
        # meanwhile client is uninstalling, create company and prepare plan list
        self.infos = OrganizationHelper(self.admin).setup_company(ta_password= common_password, to_password= common_password)
        self.log.info(f"Company Name : {self.infos['company_name']}")
        
        self.msp_orghelper_obj = OrganizationHelper(self.admin, self.infos['company_name'])
        self.infos['to_loginobj'].switch_to_company(self.infos['company_name'])
        
        # pick any 2 plans, if no plans available create new plans
        server_plans = self.admin.plans.filter_plans(plan_type= 'Server', company_name= 'Commcell').keys()
        if len(server_plans) < 2:
            self.spool1, self.plan1 = self.msp_orghelper_obj.create_plan_with_available_resource()
            self.spool2, self.plan2 = self.msp_orghelper_obj.create_plan_with_available_resource()
            self.plans_list = [self.plan1.plan_name, self.plan2.plan_name]
        else:
            self.plans_list = random.sample(server_plans, 2)
        self.log.info(f'Plans : {self.plans_list}')

    def run(self):
        """Run function of this test case"""
        try:   
            self.admin.refresh()
            # associate plans to company and edit default plans
            self.msp_orghelper_obj.associate_plans(self.plans_list)
            self.msp_orghelper_obj.switch_default_plans(self.plans_list)

            # switching default plan as tenant admin
            tenant_admin = OrganizationHelper(self.infos['ta_loginobj'], company= self.infos['company_name'])
            tenant_admin.switch_default_plans(self.plans_list)
            # we dont need tenant operator object later, so not creating any objects
            OrganizationHelper(self.infos['to_loginobj'], company= self.infos['company_name']).switch_default_plans(self.plans_list)

            default_plan = self.admin.organizations.get(self.infos['company_name']).default_plan[0]
            self.log.info(f'Client Should be Assigned to this default plan : {default_plan}')
            
            # wait for client uninstallation to complete
            self.t1.join()
            # if uninstallation thread failed to clean up the existing client, will retry again
            self.log.info('Uninstallation Thread Joined... If it was a failure, will retry')
            if (self.queue.empty() or (not self.queue.get())) and (not self.msp.uninstall_client(self.machine_name)):
                    raise Exception(f'Uninstalling Client [{self.machine_name}] Failed!')            
            self.log.info(f'Uninstalling Client [{self.machine_name}] Success!')

            # installing file system client as tenant admin
            self.infos['ta_loginobj'].refresh()
            
            # Installing Client with two tries
            if (not tenant_admin.install_client(self.machine_name, self.machine_username, self.machine_password)) and \
                (not tenant_admin.install_client(self.machine_name, self.machine_username, self.machine_password)):
                    raise Exception(f'Client Install Failed even with two tries!')
            self.log.info('Client Installation Finished!')

            self.admin.refresh()
            client = self.admin.clients.get(name= self.machine_name)
            self.subclient = Subclients(client.agents.get('File System').backupsets.get('defaultBackupSet')).get('default')
            self.log.info(f'Associated Plan : {self.subclient.plan}')
            
            # verification of default plan association
            if not self.subclient.plan:
                raise Exception('Client not associated to Default Plan')
            
            if default_plan.lower() == self.subclient.plan.lower():
                self.log.info('[PASSED] Client Associated to default plan')
            else:
                raise Exception('[FAILED] Client failed to associate to default plan')

            self.status = constants.PASSED
            self.log.info('Testcase Passed')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.admin.refresh()
        if self.subclient.plan: self.subclient.plan = None
        if self.infos:
            self.admin.users.delete(user_name= self.infos['to_name'], new_user= 'admin')
            # company should be completely deleted. So that currently installed client doesnot affect other testcase
            self.msp_orghelper_obj.delete_company(wait= True) # timeout = 15 min
        if self.plan1 and self.admin.plans.has_plan(plan_name= self.plan1.plan_name): self.admin.plans.delete(self.plan1.plan_name)
        if self.plan2 and self.admin.plans.has_plan(plan_name= self.plan2.plan_name): self.admin.plans.delete(self.plan2.plan_name)
        if self.spool1 and self.admin.storage_pools.has_storage_pool(self.spool1.storage_pool_name): self.admin.storage_pools.delete(self.spool1.storage_pool_name)                           
        if self.spool2 and self.admin.storage_pools.has_storage_pool(self.spool2.storage_pool_name): self.admin.storage_pools.delete(self.spool2.storage_pool_name)                           