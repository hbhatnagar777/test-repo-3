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

from os import name
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Server.organizationhelper import OrganizationHelper
from threading import Thread
from Laptop.laptophelper import LaptopHelper
from cvpysdk.subclient import Subclients
from AutomationUtils import config
from queue import Queue
from random import randint

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
            Change Company Operation wrt Plan Association
            1. MSP client with MSP plan         -- Should be migrate to company only if destination company has rights on plan associated with client
            2. Company client with MSP plan     -- Allow migration to commcell or company which has rights on plan associated with client
            3. MSP client with company plan     -- All migration only to that particular company
            4. Company client with Company plan -- Dont Allow any kind of migration

        """
        super(TestCase, self).__init__()
        self.name = "Companies - Change company"

        self.tcinputs = {
            'file_server': ''
        }
        self.company_storage_pool = None
        self.msp_storage_pool = None
        self.company1 = None
        self.company2 = None
        self.subclient = None
        self.created_company_spool = False
        self.created_msp_spool = False
        
        """
        Either pass Creds in tcinputs  or config.json [self.config_json.Install.windows_client] and [self.config_json.Laptop.Install.windows]
        tcinputs = {
                    "fs_client" : {
                        "machine_host": "",
                        "machine_username": "",
                        "machine_password": "" # base 64 encoded
                    },
                    "laptop_client" : {
                        "machine_host": "",
                        "machine_username": "",
                        "machine_password": "" # base 64 encoded
                    }
                }
        """

    def setup(self):
        """Setup function of this test case
        Prerequirements: Two Companies, One MSP Plan, One Company Created Plan, One Client        
        """
        self.msp_orghelper   = OrganizationHelper(commcell= self.commcell) 
        
        # make sure client is at commcell level
        self.client_name = self.tcinputs['file_server']
        self.client = self.commcell.clients.get(self.client_name)
        self.subclient = Subclients(self.client.agents.get('File System').backupsets.get('defaultBackupSet')).get('default')
        self.subclient.plan = None
        self.client.change_company_for_client('Commcell')

        # creating required entities
        self.company1 = OrganizationHelper(self.commcell).setup_company(ta_password= self.inputJSONnode['commcell']['commcellPassword'])
        self.company1_obj = self.company1['company_obj']
        self.company1_name = self.company1['company_name']
        self.log.info(f"1. Company Name : {self.company1_name}")

        self.company2 = OrganizationHelper(self.commcell).setup_company()
        self.company2_obj = self.company2['company_obj']
        self.company2_name = self.company2['company_name']
        self.log.info(f"2. Company Name : {self.company2_name}")
                
        # creating helper objects for both the companies
        self.msp_org_helper1 = OrganizationHelper(commcell= self.commcell, company= self.company1_name)
        self.msp_org_helper2 = OrganizationHelper(commcell= self.commcell, company= self.company2_name)

        self.company_storage_pool, self.company_plan, self.created_company_spool = self.msp_org_helper1.create_plan_for_company() # company plan
        self.msp_storage_pool, self.msp_plan = self.msp_orghelper.create_plan_with_available_resource()
        self.log.info(f'Created Plan => {self.msp_plan.plan_name}')
        
        self.company1_obj.refresh()
        self.company2_obj.refresh()
        
    def run(self):
        """Run function of this test case"""
        
        try:
            # change company for created pseudo client
            self.msp_orghelper.validate_change_company(client_name= self.client_name, destination_company= self.company1_name)
            self.log.info('Basic Validation is done!')
            
            # change company validation wrt plan association
            self.log.info(f'Subclient Plans : {self.subclient.plan}')
            self.log.info(f'Company 1 Plans : {self.company1_obj.plans}')
            self.log.info(f'Company 2 Plans : {self.company2_obj.plans}')
            self.log.info(f'Clients Company : {self.client.company_name}')
            self.msp_orghelper.validate_change_company_wrt_plan_assoc(client_obj= self.client, subclient_obj= self.subclient, msp_plan_name= self.msp_plan.plan_name,
                                                                        company1_obj= self.company1_obj, company1_plan= self.company_plan.plan_name, 
                                                                        company2_obj= self.company2_obj)
            self.log.info(f'Validation wrt to plan association is complete..')
                            
            # validate change company for server groups
            self.orghelper = OrganizationHelper(self.commcell, self.company1_name)
            self.orghelper.validate_server_group_change_company()
            self.log.info('Validated server group change company..')
            
            self.status = constants.PASSED
            self.log.info('Testcase Passed')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.commcell.refresh()
        if self.subclient: self.subclient.plan = None # to delete plan
        self.commcell.clients.get(self.client_name).change_company_for_client('Commcell')
        if self.company1 and self.commcell.organizations.has_organization(self.company1['company_name']): self.msp_org_helper1.delete_company(wait= True)
        if self.company2 and self.commcell.organizations.has_organization(self.company2['company_name']): self.msp_org_helper2.delete_company(wait= True)
        if self.commcell.plans.has_plan(plan_name= self.msp_plan.plan_name): self.commcell.plans.delete(plan_name= self.msp_plan.plan_name)
        if self.created_company_spool and self.commcell.storage_pools.has_storage_pool(self.company_storage_pool.storage_pool_name):
            self.commcell.storage_pools.delete(storage_pool_name= self.company_storage_pool.storage_pool_name)
            
    def uninstall_and_install_laptop(self):
        """Uninstalls and Re-Installs"""
        try:
            if not self.msp_orghelper.uninstall_client(client_name= self.laptop_client_name): return False
            if not self.msp_orghelper.install_laptop_client(self.laptop_client_details): return False
            self.log.info('Laptop Installation Finished!')
            return True
        except Exception as err:
            self.log.info(f'Exception in [uninstall_and_install_laptop] : {err}')
            return False
        
    def uninstall_and_install_fs_client(self):
        """Uninstalls and Re-Installs"""
        try:
            if not self.msp_orghelper.uninstall_client(client_name= self.fs_client_details['client_hostname']): return False
            if not self.msp_orghelper.install_client(hostname= self.fs_client_details['client_hostname'] , username= self.fs_client_details['machine_username'], 
                                              password= self.fs_client_details['machine_password']): return False
            self.log.info('FS Client Installation Finished!')
            return True
        except Exception as err:
            self.log.info(f'Exception in [uninstall_and_install_fs_client] : {err}')
            return False