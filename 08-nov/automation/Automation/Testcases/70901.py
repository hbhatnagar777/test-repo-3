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
from Server.Security.userhelper import UserHelper
import random, copy
from cvpysdk.security.security_association import SecurityAssociation

class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        This testcase Verifies:
            As Tenant Admin and Operator
                1. Adding user and verifying company tagging.
                2. Adding user group and verifying company tagging.
                3. Adding role and verifying company tagging.
                4. Assigning created role with created user.
                5. Giving rights for newly created user on new company plan.
        """
        super(TestCase, self).__init__()
        self.name = "N Level Reseller - Companies - Create Security entities as Tenant Admin and Operator"

        self.infos = self.spool = self.plan = None
        self.tcinputs = {
            "reseller_level": 2
        }

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
                                                                                                              password=common_password)
            self.result_string = f'Testcase executed with {self.tcinputs["reseller_level"]} level reseller'
            
            # switch the testcase flow to reseller
            self.commcell = self.reseller_company_info['ta_loginobj']
            self.commcell.refresh()
        
        self.infos = OrganizationHelper(self.commcell).setup_company(ta_password= common_password, to_password= common_password)
        self.log.info(f"Company Name : {self.infos['company_name']}")
        
        # creating one company entity [plan] and at the end, Give rights for user on this plan.
        self.msp_org_helper = OrganizationHelper(commcell= self.commcell, company= self.infos['company_name'])
        
        self.log.info('Available Storage Pools for Company ')
        self.log.info(self.infos['ta_loginobj'].storage_pools.all_storage_pools)
        self.ta_org_helper = OrganizationHelper(commcell= self.infos['ta_loginobj'], company= self.infos['company_name'])
        self.storage_pool, self.plan = self.ta_org_helper.create_plan_with_available_resource()
        
        self.infos['to_loginobj'].switch_to_company(self.infos['company_name'])
        
    def run(self):
        """Run function of this test case"""
        try:
            self.log.info('Performing actions as Tenant Admin..')
            self.infos['ta_loginobj'].refresh()
            self.create_entities(OrganizationHelper(self.infos['ta_loginobj'], company= self.infos['company_name']))
            
            self.log.info('Performing actions as Tenant Operator..')
            self.infos['to_loginobj'].refresh()
            self.create_entities(OrganizationHelper(self.infos['to_loginobj'], company= self.infos['company_name']))
            self.status = constants.PASSED
            self.log.info('Testcase Passed')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.commcell = self.original_commcell # switch back to original commcell
        self.commcell.refresh()
        
        OrganizationHelper(self.commcell).cleanup_orgs(marker=self.testcase_id)
        OrganizationHelper(self.commcell).cleanup_orgs(marker='DEL Automated')
        UserHelper(self.commcell).cleanup_users(marker='del_automated')
        
    @test_step
    def create_entities(self, obj):
        """Creates New Role / User / Usergroup and Assigns Role to Newly Created user"""
        temp = str(random.randint(0, 100000))

        permissions = random.sample(['Create Storage Policy', 'Change security settings', 'Edit Subclient Policy', 'Create Alert', 
        'Agent Scheduling', 'Create Plan', 'Create Subclient Policy', 'Edit Subclient Policy Associations', 'Execute Monitoring Policy', 'Alert Management'], 5)
        self.log.info(f'Selected Permissions : {permissions}')
        obj.add_role('role' + temp, permissions)
        obj.add_user('user' + temp , self.inputJSONnode['commcell']['commcellPassword'])
        obj.add_usergroup('usergrp' + temp)
        obj.assign_role_for_user(self.infos['company_alias'] + '\\' + 'user' + temp, 'role' + temp)
        
        associations_list = [{ 'user_name': self.infos['company_alias'] + '\\' + 'user' + temp,  'role_name': 'role' + temp}]
        self.log.info('Giving Rights for a user on Plan..')
        SecurityAssociation(self.commcell, self.plan)._add_security_association(association_list= associations_list, request_type= 'UPDATE') # for a new user giving rights on plan
        self.log.info('Added Security Association!')