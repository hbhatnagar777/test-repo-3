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
from Web.Common.page_object import TestStep
from Server.organizationhelper import OrganizationHelper
import random

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
            1. Creating Reseller Company
            2. As a Reseller - Creating Child Company, associating MSP plan during creation
            3. Creating Plan as a Reseller
            4. As a Reseller - Creating Child Company, associating reseller created plan during creation
            5. As a Reseller - Create Company with no plans and later associate reseller plan
            
        """
        super(TestCase, self).__init__()
        self.name = "Companies - Reseller mode"
        
        self.tcinputs = {}

        self.msp_plan = self.msp_spool = self.spool = None
        self.created_new_plan = False
        self.created_new_storage_pool = False
        self.reseller_plan = None
        self.child_comp1 = self.child_comp2 = self.child_comp3 = self.reseller_comp = None

    def setup(self):
        """Setup function of this test case"""
        common_password = self.inputJSONnode['commcell']['commcellPassword']

        if server_plans := self.commcell.plans.filter_plans(
            plan_type='Server', company_name='Commcell'
        ).keys():
            self.msp_plan = self.commcell.plans.get(plan_name= random.sample(list(server_plans), 1)[0])

        else:
            self.msp_spool, self.msp_plan = OrganizationHelper(self.commcell).create_plan_with_available_resource()
            self.created_new_plan = True
        self.reseller_comp = OrganizationHelper(self.commcell).setup_company(ta_password= common_password, plans= [self.msp_plan.plan_name])
        self.log.info(f"Reseller Company Name : {self.reseller_comp['company_name']}")
        self.reseller = self.reseller_comp['ta_loginobj']
        self.msp_orghelper_obj = OrganizationHelper(self.commcell, self.reseller_comp['company_name'])

        self.log.info('Enabling Reseller Mode...')
        self.msp_orghelper_obj.enable_reseller_and_verify()
        self.reseller_orghelper_obj = OrganizationHelper(self.reseller, self.reseller_comp['company_name'])

        self.spool = self.msp_orghelper_obj.share_random_msp_storage_with_company()
        if not self.spool:
            self.spool = self.msp_orghelper_obj.create_new_storage_share_with_company()
            self.created_new_storage_pool = True

        self.log.info('Creating Plan as Reseller..')
        self.reseller_plan_name = f'DEL Automated Plan - {random.randint(0, 100000)}'
        self.reseller_plan = self.reseller.plans.add(plan_name= self.reseller_plan_name, plan_sub_type= "Server", storage_pool_name= self.spool.storage_pool_name)
        self.reseller_comp['company_obj'].refresh()
        self.reseller.refresh()

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info('Creating Child Company with plan...')
            self.child_comp1 = self.reseller_orghelper_obj.setup_company(plans= [self.msp_plan.plan_name]) # with plan

            self.log.info('Creating Child Company without plan...')
            self.child_comp2 = self.reseller_orghelper_obj.setup_company() # without plan
            self.log.info('Associating plan after company creation...')
            self.child_comp2['company_obj'].plans = [self.reseller_plan_name]
            # self.child_comp2['company_obj'].plans = [self.msp_plan.plan_name] # this fails as per current design, so commenting this

            self.log.info('Creating Child Company with Reseller plan...')
            self.child_comp3 = self.reseller_orghelper_obj.setup_company(plans= [self.reseller_plan_name]) # with reseller plan

            self.status = constants.PASSED
            self.log.info('Testcase Passed')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.commcell.organizations.refresh()
        # delete one child company as admin
        if self.child_comp1 and self.commcell.organizations.has_organization(self.child_comp1['company_name']): self.commcell.organizations.delete(self.child_comp1['company_name'])
        # delete one child company as Reseller
        if self.child_comp2 and self.commcell.organizations.has_organization(self.child_comp2['company_name']): self.reseller.organizations.delete(self.child_comp2['company_name'])
        # delete reseller company before deleting child company
        if self.reseller_comp and self.commcell.organizations.has_organization(self.reseller_comp['company_name']): self.commcell.organizations.delete(self.reseller_comp['company_name'])
        # last child company which is migrated to commcell, delete as admin
        if self.child_comp3 and self.commcell.organizations.has_organization(self.child_comp3['company_name']): self.commcell.organizations.delete(self.child_comp3['company_name'])

        if self.reseller_plan and self.commcell.plans.has_plan(plan_name= self.reseller_plan_name): self.commcell.plans.delete(plan_name= self.reseller_plan_name)
        if self.created_new_plan and self.commcell.plans.has_plan(plan_name= self.msp_plan.plan_name): self.commcell.plans.delete(plan_name= self.msp_plan.plan_name)
        if self.created_new_storage_pool and self.commcell.storage_pools.has_storage_pool(self.spool.storage_pool_name): self.commcell.storage_pools.delete(storage_pool_name= self.spool.storage_pool_name)
        if self.msp_spool and self.commcell.storage_pools.has_storage_pool(self.msp_spool.storage_pool_name): self.commcell.storage_pools.delete(storage_pool_name= self.msp_spool.storage_pool_name)