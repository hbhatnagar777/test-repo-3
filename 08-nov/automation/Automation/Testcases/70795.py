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

import random
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.organizationhelper import OrganizationHelper
from Server.Plans.planshelper import PlansHelper
from Server.Security.userhelper import UserHelper
from cvpysdk.commcell import Commcell
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
import traceback

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
        self.name = "Validate plan and schedule policy visibilities with different personas"
        self.tcinputs = {}

    def setup(self):
        """Setup function of this test case"""
        self.log.info('Setting up the environment for test case to evaluate plan visibilities for different cases...')

        retry_count = 0
        while retry_count < 3:
            try:
                self.set_entity_names()
                self.create_required_plans()
                self.create_required_companies()
                self.associate_plans_to_company()
                self.create_plan_as_tenant_admin()
                self.create_users_and_configure_permissions()
                self.refresh_login_objects()
                break
            except Exception as exp:
                self.log.error('Exception occurred: %s', exp)
                self.log.error(traceback.format_exc())
                retry_count += 1
                self.log.info(f'Retrying... Retry Attempt: {retry_count}')
        else:
            raise CVTestStepFailure('Failed to execute setup even after 3 retries')

    def run(self):
        """Run function of this test case"""
        try:
            # validate plan visibilities for different cases
            testcases = [
                # (testcaseid, plan_name, user_obj, expected_visibility)
                # it checks if user_obj has visibility to plan_name and its schedules wrt expected_visibility
                
                # validate plan visibility for msp plan
                (1, self.msp_plan_name, self.commcell, True),
                (2, self.msp_plan_name, self.tenant_admin_1, False), # it is not associated with company 1
                (3, self.msp_plan_name, self.tenant_admin_2, False), # it is not associated with company 2
                
                # validate permission based plan visibility
                (4, self.msp_plan_name, self.plan_subscription_user, True), # user has plan subscription role
                (5, self.msp_plan_name, self.no_permission_user, False),
                (6, self.company_1_plan_name, self.plan_subscription_user, False), # user does not have plan subscription role on company 1 plan
                (7, self.base_plan_name, self.plan_subscription_user, False),
                
                # validate plan visibility for company created plan
                (8, self.company_1_plan_name, self.commcell, True),
                (9, self.company_1_plan_name, self.tenant_admin_1, True),
                (10, self.company_1_plan_name, self.tenant_admin_2, False),
                
                # validate plan visibility for plan-company association
                (11, self.plan_company_assoc_test_plan_name, self.commcell, True),
                (12, self.plan_company_assoc_test_plan_name, self.tenant_admin_1, False), # it is not associated with company 1
                (13, self.plan_company_assoc_test_plan_name, self.tenant_admin_2, True), # it is associated with company 2
                
                # validate plan visibility for plans derived by tenants using the base plan
                (14, self.derived_plan_inherit_all, self.commcell, True),
                (15, self.derived_plan_inherit_all, self.tenant_admin_1, True),
                (16, self.derived_plan_inherit_all, self.tenant_admin_2, False), # it belongs to company 1
                
                (17, self.derived_plan_override_all, self.commcell, True),
                (18, self.derived_plan_override_all, self.tenant_admin_1, True),
                (19, self.derived_plan_override_all, self.tenant_admin_2, False), # it belongs to company 1
            ]

            for testcase_id, plan_name, user_obj, expected_visibility in testcases:
                self.validate_plan_visibility(testcase_id=testcase_id, plan_name=plan_name, user_obj=user_obj, expected_visibility=expected_visibility)
                
            # validate plan visibility as operator users
            self.commcell.switch_to_company(company_name=self.company_name_1)
            self.commcell.refresh()
            
            operator_testcases = [
                (20, self.msp_plan_name, self.commcell, False),
                (21, self.company_1_plan_name, self.commcell, True),
                (22, self.base_plan_name, self.commcell, True), # plan is associated with company 1
                (23, self.derived_plan_inherit_all, self.commcell, True),
                (24, self.derived_plan_override_all, self.commcell, True),
            ]
            
            for testcase_id, plan_name, user_obj, expected_visibility in operator_testcases:
                self.validate_plan_visibility(testcase_id=testcase_id, plan_name=plan_name, user_obj=user_obj, expected_visibility=expected_visibility)
            
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.commcell.reset_company()
        self.commcell.refresh()
        OrganizationHelper(self.commcell).cleanup_orgs(marker='TC 70795')
        PlansHelper(commcell_obj=self.commcell).cleanup_plans(marker='TC 70795')
        UserHelper(self.commcell).cleanup_users(marker='tc_70795')

    def validate_plan_visibility(self, testcase_id: int, plan_name: str, user_obj: Commcell, expected_visibility: bool) -> None:
        """Validate plan visibility for a user.

        Args:
            testcase_id (int): ID of the testcase.
            plan_name (str): Name of the plan to validate.
            user_obj (Commcell): Commcell object of the user.
            expected_visibility (bool): Expected visibility of the plan.

        Returns:
            bool: True if plan is visible, False otherwise.
        """
        # perform the validation for plan visibility
        plan_found = bool(user_obj.plans.has_plan(plan_name))
        log_str = f'[{testcase_id}]: Plan Found: [{plan_found}] and the expected visibility is: [{expected_visibility}]'
        self.log.info(log_str)
        
        if plan_found != expected_visibility:
            raise CVTestStepFailure(f'Plan visibility validation failed: {log_str}')

        self.log.info(f'[{testcase_id}]: Plan visibility validation passed!')

        # Do the validation for schedule policy visibility
        self.validate_schedule_policy_visibility(testcase_id=testcase_id, 
                                                 plan_name=plan_name, 
                                                 user_obj=user_obj, 
                                                 expected_visibility=expected_visibility
                                                 )
    
    def validate_schedule_policy_visibility(self, testcase_id: int, plan_name: str, user_obj: Commcell, expected_visibility: bool) -> None:
        """Validate schedule policy visibility for a user."""
        data_schedule_found, log_schedule_found, snap_schedule_found = self.__check_if_schedule_policies_are_visible(plan_name=plan_name, 
                                                                                                                     user_obj=user_obj
                                                                                                                     )
        log_str = f'[{testcase_id}]: Schedule policies found status: ' \
                    f'Data: {data_schedule_found}, Log: {log_schedule_found}, Backup Copy: {snap_schedule_found} ' \
                    f'Expected: {expected_visibility}'
        self.log.info(log_str)

        # cross-check with expected visibility
        if expected_visibility:
            if not all([data_schedule_found, log_schedule_found, snap_schedule_found]):
                raise CVTestStepFailure(f'Not all schedule policies found as expected: {log_str}')
        else:
            if any([data_schedule_found, log_schedule_found, snap_schedule_found]):
                raise CVTestStepFailure(f'Schedule policies found unexpectedly: {log_str}')
            
        self.log.info(f'[{testcase_id}]: Schedule policies visibility validated successfully for plan: [{plan_name}] '
                  f'with user: [{user_obj.commcell_username}]')

    def __check_if_schedule_policies_are_visible(self, plan_name: str, user_obj: Commcell) -> tuple:
        """Check if schedule policies are visible for the plan."""
        if user_obj.plans.has_plan(plan_name):
            plan_obj = user_obj.plans.get(plan_name)
            try:
                data_schedule_policy_found = bool(plan_obj.data_schedule_policy)
            except Exception:
                data_schedule_policy_found = False

            try:
                log_schedule_policy_found = bool(plan_obj.log_schedule_policy)
            except Exception:
                log_schedule_policy_found = False

            try:
                backup_copy_schedule_policy_found = bool(plan_obj.snap_schedule_policy)
            except Exception:
                backup_copy_schedule_policy_found = False
        else:
            data_schedule_policy_found = user_obj.schedule_policies.has_policy(plan_name)
            log_schedule_policy_found = user_obj.schedule_policies.has_policy(f'{plan_name} schedule policy for the database clients')
            backup_copy_schedule_policy_found = user_obj.schedule_policies.has_policy(f'{plan_name} backup copy schedule policy')

        return bool(data_schedule_policy_found), bool(log_schedule_policy_found), bool(backup_copy_schedule_policy_found)

    ################################### Helper Functions For Testcase ###################################################
    
    def set_entity_names(self):
        """Set entity names for this test case"""
        self.org_helper = OrganizationHelper(self.commcell)
        
        # company names
        self.company_name_1 = f'TC 70795 Company 1 - {random.randint(1, 1000)}'
        self.company_name_2 = f'TC 70795 Company 2 - {random.randint(1, 1000)}'

        # plan names
        self.msp_plan_name = f'TC 70795 MSP Plan - {random.randint(1, 1000)}'
        self.company_1_plan_name = f'{self.company_name_1} Plan'
        self.base_plan_name = f'TC 70795 Base Plan - {random.randint(1, 1000)}'
        self.plan_company_assoc_test_plan_name = f'TC 70795 PlanCompany Assoc - {random.randint(1, 1000)}'
        self.derived_plan_inherit_all = f'TC 70795 Derived Plan Inherit All - {random.randint(1, 1000)}'
        self.derived_plan_override_all = f'TC 70795 Derived Plan Override All - {random.randint(1, 1000)}'

        # user and role names
        self.plan_subscription_user_name = f'tc_70795_user_subscription_role_{random.randint(1, 1000)}'
        self.no_permission_user_name = f'tc_70795_user_no_permission{random.randint(1, 1000)}'
        self.plan_subscription_role_name = 'Plan Subscription Role'

    def create_users_and_configure_permissions(self):
        """Create users and configure permissions for this test case"""
        self.log.info('Creating users and configuring permissions for this test case...')

        # create commcell user and provide "Plan Subscription" role
        self.commcell.users.add(user_name=self.plan_subscription_user_name,
                                email=f'test{random.randint(1, 1000)}@domain.com', password=self.common_password)
        self.commcell.plans.get(self.msp_plan_name).update_security_associations(associations_list=[{
            'user_name': self.plan_subscription_user_name,
            'role_name': self.plan_subscription_role_name
        }], request_type='UPDATE'
        )
        self.plan_subscription_user = Commcell(self.commcell.webconsole_hostname, self.plan_subscription_user_name,
                                               self.common_password, verify_ssl=False)

        # create commcell user without any permissions
        self.commcell.users.add(user_name=self.no_permission_user_name,
                                email=f'test{random.randint(1, 1000)}@domain.com', password=self.common_password)
        self.no_permission_user = Commcell(self.commcell.webconsole_hostname, self.no_permission_user_name,
                                           self.common_password, verify_ssl=False)

    def create_required_plans(self):
        """Create required plans for this test case"""
        self.log.info(f'Creating plan as MSP... : [{self.msp_plan_name}]')
        self.org_helper.create_plan_with_available_resource(plan_name=self.msp_plan_name)
        
        self.log.info(f'Creating plan for plan-company association... : [{self.plan_company_assoc_test_plan_name}]')
        self.org_helper.create_plan_with_available_resource(plan_name=self.plan_company_assoc_test_plan_name)
        
        self.log.info(f'Creating base plan... : [{self.base_plan_name}]')
        self.org_helper.create_plan_with_available_resource(plan_name=self.base_plan_name)
        
    def create_required_companies(self):
        """Create required companies for this test case"""
        self.common_password = self.inputJSONnode['commcell']['commcellPassword']
        
        self.log.info(f'Creating company... : [{self.company_name_1}]')
        self.company_1_details = self.org_helper.setup_company(company_name=self.company_name_1,
                                                               ta_password=self.common_password)

        self.log.info(f'Creating company... : [{self.company_name_2}]')
        self.company_2_details = self.org_helper.setup_company(company_name=self.company_name_2,
                                                               ta_password=self.common_password)
        
        # login as tenant admin 1
        self.tenant_admin_1 = Commcell(self.commcell.webconsole_hostname, self.company_1_details['ta_name'],
                                       self.common_password, verify_ssl=False)
        self.tenant_admin_1_org_helper = OrganizationHelper(self.tenant_admin_1, self.company_name_1)

        # login as tenant admin 2
        self.tenant_admin_2 = Commcell(self.commcell.webconsole_hostname, self.company_2_details['ta_name'],
                                       self.common_password, verify_ssl=False)

    def associate_plans_to_company(self):
        """Associate plans to companies for this test case"""
        self.org_helper.associate_plans(plan_list=[self.plan_company_assoc_test_plan_name], company_name=self.company_name_2)

        # associate base plan to company 1
        self.org_helper.associate_plans(plan_list=[self.base_plan_name], company_name=self.company_name_1)

        # associate base plan to company 2 - but still derived plans should not be visible to company 2
        self.org_helper.associate_plans(plan_list=[self.base_plan_name], company_name=self.company_name_2)

    def create_plan_as_tenant_admin(self):
        """Create plan as tenant admin for this test case"""
        self.shared_storage = self.org_helper.share_random_msp_storage_with_company(
            company_name=self.company_name_1).storage_pool_name

        self.log.info(f'Creating plan for company 1 as tenant admin... : [{self.company_1_plan_name}]')
        self.tenant_admin_1.plans.add(plan_name=self.company_1_plan_name, plan_sub_type='Server', storage_pool_name='Disk Storage')

        self.log.info(f'Creating derived plan with inheritance... : [{self.derived_plan_inherit_all}]')
        self.ta_1_plans_helper = PlansHelper(commcell_obj=self.tenant_admin_1)
        self.ta_1_plans_helper.inherit_plan(base_plan_name=self.base_plan_name,
                                            derived_plan_name=self.derived_plan_inherit_all)

        self.log.info(f'Creating derived plan with override... : [{self.derived_plan_override_all}]')
        self.ta_1_plans_helper.inherit_plan(base_plan_name=self.base_plan_name,
                                            derived_plan_name=self.derived_plan_override_all,
                                            sla_in_minutes=60,
                                            storage_pool=self.shared_storage)
        
    def refresh_login_objects(self):
        """Refresh all login objects"""
        self.log.info('Refreshing all login objects...')
        self.commcell.refresh()
        self.tenant_admin_1.refresh()
        self.tenant_admin_2.refresh()
        self.plan_subscription_user.refresh()
        self.no_permission_user.refresh()