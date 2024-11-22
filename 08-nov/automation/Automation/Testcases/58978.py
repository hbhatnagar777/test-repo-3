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
        self.name = "Companies - Create Security entities as Tenant Admin and Operator"

        self.infos = self.spool = self.plan = None
        self.tcinputs = {}

    def setup(self):
        """Setup function of this test case"""
        common_password = self.inputJSONnode['commcell']['commcellPassword']
        
        self.infos = OrganizationHelper(self.commcell).setup_company(ta_password= common_password, to_password= common_password)
        self.log.info(f"Company Name : {self.infos['company_name']}")
        
        # creating one company entity [plan] and at the end, Give rights for user on this plan.
        self.msp_org_helper = OrganizationHelper(commcell= self.commcell, company= self.infos['company_name'])
        self.stor_pool = self.msp_org_helper.share_random_msp_storage_with_company()
        if not self.stor_pool:
            self.spool = self.msp_org_helper.create_new_storage_share_with_company()
        
        self.log.info(f'Avaiable Storage Pools for Company ')
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
        if self.infos and self.commcell.organizations.has_organization(self.infos['company_name']): self.msp_org_helper.delete_company(wait= True)
        if self.infos and self.commcell.users.has_user(self.infos['to_name']): self.commcell.users.delete(self.infos['to_name'], new_user= 'admin')
        if self.spool and self.commcell.storage_pools.has_storage_pool(self.spool.storage_pool_name): self.commcell.storage_pools.delete(storage_pool_name= self.spool.storage_pool_name)

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