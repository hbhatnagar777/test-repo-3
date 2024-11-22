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
from Server.Plans.planshelper import PlansHelper
import random
import copy

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
        self.name = "N Level Reseller - Companies - Reseller mode"
        
        self.tcinputs = {
            "reseller_level": 2
        }

        self.msp_plan = self.msp_spool = self.spool = None
        self.created_new_plan = False
        self.created_new_storage_pool = False
        self.reseller_plan = None
        self.child_comp1 = self.child_comp2 = self.child_comp3 = self.reseller_comp = None

    def setup(self):
        """Setup function of this test case"""
        common_password = self.inputJSONnode['commcell']['commcellPassword']
        self.original_commcell = copy.deepcopy(self.commcell)
        self.testcase_id = str(self.id)
        
        # configure n level reseller
        if self.tcinputs.get('reseller_level', 0) > 0:
            self.reseller_company_info = OrganizationHelper(self.commcell).configure_n_level_reseller_company(testcase_id=self.testcase_id, 
                                                                                                              commcell=self.commcell,
                                                                                                              level=self.tcinputs['reseller_level'], 
                                                                                                              password=common_password,)
            self.result_string = f'Testcase executed with {self.tcinputs["reseller_level"]} level reseller'
            
            # switch the testcase flow to reseller
            self.commcell = self.reseller_company_info['ta_loginobj']
            self.commcell.refresh()

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

        # one storage pool is already shared with all tenant admins user group
        storage_pool_name = random.choice(list(self.reseller.storage_pools.all_storage_pools))
        
        self.log.info('Creating Plan as Reseller..')
        self.reseller_plan_name = f'DEL Automated Plan - {random.randint(0, 100000)}'
        self.reseller_plan = self.reseller.plans.add(plan_name= self.reseller_plan_name, plan_sub_type= "Server", storage_pool_name= storage_pool_name)
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
        self.commcell = self.original_commcell # switch back to admin view
        self.commcell.refresh()
        
        OrganizationHelper(self.commcell).cleanup_orgs(marker=self.testcase_id)
        OrganizationHelper(self.commcell).cleanup_orgs(marker='DEL Automated')
        PlansHelper(commcell_obj=self.commcell).cleanup_plans(marker='DEL Automated')
