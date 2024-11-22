# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
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
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger
from AutomationUtils.options_selector import CVEntities
from Server.Plans.planshelper import PlansHelper
from FileSystem.FSUtils.fshelper import FSHelper
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from Server.Plans import plansconstants
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing this Test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       —  name of this test case

                product         (str)       —  applicable product for this
                                               test case
                    Ex: self.products_list.FILESYSTEM

                features        (str)       —  qcconstants feature_list item
                    Ex: self.features_list.DATAPROTECTION

                tcinputs        (dict)      —  dict of test case inputs with
                                               input name as dict key
                                               and value as input type
                        Ex: {
                             "MY_INPUT_NAME": "MY_INPUT_TYPE"
                            }
        """
        super(TestCase, self).__init__()
        self.name = "MSP Testcase: Plan association and inheritance"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.PLANS
        self.tcinputs = {
            "TenantUsername": None,
            "TenantPassword": None,
            "CompanyName": None
        }
        self.commcell_obj = None
        self.tenant_commcell_obj = None
        self.plans_api_helper = None
        self.user_helper = None
        self.fs_helper = None
        self.cv_entities = None

    def setup(self):
        """Setup function of this test case"""
        self._log = logger.get_log()
        self.commcell_obj = self._commcell
        self.tcinputs["MSPCommCell"] = self.inputJSONnode[
            'commcell']['webconsoleHostname']
        self.tcinputs["MSPadminUser"] = self.inputJSONnode[
            'commcell']['commcellUsername']
        self.tcinputs["MSPadminUserPwd"] = self.inputJSONnode[
            'commcell']['commcellPassword']
        self.plans_api_helper = {
            'MSPAdmin': PlansHelper(
                self.tcinputs["MSPCommCell"],
                self.tcinputs["MSPadminUser"],
                self.tcinputs["MSPadminUserPwd"],
                commcell_obj=self.commcell_obj
            ),
            'TenantAdmin': None
        }
        self.ug_helper = UsergroupHelper(self.commcell_obj)
        self.server = ServerTestCases(self)
        self.fs_helper = FSHelper(self)
        self.cv_entities = {
            'MSPAdmin': CVEntities(self.commcell_obj),
            'TenantAdmin': None
        }

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("Started executing {0} testcase".format(self.id))
            self.fs_helper.populate_tc_inputs(self, mandatory=False)

            # Delete or rename existing base plan
            if (self.plans_api_helper['MSPAdmin'].plans_obj.has_plan(
                    plansconstants.BASE_SERVER_PLAN)):
                try:
                    self.plans_api_helper['MSPAdmin'].delete_plan(
                        plansconstants.BASE_SERVER_PLAN
                    )
                    self._log.info("\tSuccessfully deleted {0} plan".format(
                        plansconstants.BASE_SERVER_PLAN
                        )
                                  )
                except Exception as exp:
                    self._log.info(
                        "Unable to delete base plan due to - {0}".format(
                            str(exp)
                        )
                    )
                    self.plans_api_helper['MSPAdmin'].plans_obj.get(
                        plansconstants.BASE_SERVER_PLAN
                    ).plan_name = "delete50721 {0}{1}".format(
                        plansconstants.BASE_SERVER_PLAN,
                        time.time()
                    )
                    self.plans_api_helper['MSPAdmin'].plans_obj.refresh()
                    self._log.info("\tRenamed existing base plan")

            # Create a storage pool
            tc_storage_pool = self.cv_entities['MSPAdmin'].create_storage_pool(
                storage_pool_name="{0}-{1}".format(plansconstants.dedupe_storage, self.id),
                mountpath="C:\\{0}\\StoragePool{1}".format(self.id, time.time()),
                mediaagent=self.tcinputs["MediaAgent"],
                ddb_ma=self.tcinputs["MediaAgent"],
                deduppath="C:\\{0}\\StoragePool{1}".format(self.id, time.time())
            ).storage_pool_name

            # Create a base plan
            plan_subtype = plansconstants.SUBTYPE_SERVER
            tc_base_plan = self.plans_api_helper['MSPAdmin'].create_base_plan(
                plansconstants.BASE_SERVER_PLAN,
                plan_subtype,
                tc_storage_pool,
            )
            self._log.info(
                "\t1. Successfully created {0} plan with {1} storage pool".format(
                    tc_base_plan.plan_name,
                    tc_storage_pool
                )
            )

            # Validate plan creation
            self.plans_api_helper['MSPAdmin'].validate_plan_props(tc_base_plan)
            self._log.info("\t2. Validation of backend entities successful")

            # Associate plan to company
            self.plans_api_helper['MSPAdmin'].plan_to_company(
                self.tcinputs['CompanyName'],
                tc_base_plan.plan_name
            )
            self._log.info(
                "\t3. Successfully associated {0} plan to {1} company".format(
                    tc_base_plan.plan_name,
                    self.tcinputs['CompanyName']
                )
            )

            # Set base plan as default plan
            self.plans_api_helper['MSPAdmin'].company_default_plan(
                self.tcinputs['CompanyName'],
                tc_base_plan.plan_name
            )

            # Validate company's default plan
            if self.plans_api_helper['MSPAdmin'].validate_default_plan(
                self.tcinputs['CompanyName'],
                    tc_base_plan.plan_name):
                self.log.info('\t4. Validation of default plan association successful')
            else:
                self.log.error('\t4. Validation of default plan association falied')

            # Verify the required roles for the tenant user groups
            self.plans_api_helper['MSPAdmin'].validate_tenant_roles(
                tc_base_plan.plan_name,
                '{0}\\{1}'.format(
                    self.tcinputs["CompanyName"],
                    plansconstants.TENANT_ADMIN)
            )
            self.log.info('\t5. Successfully validated the roles of tenant users on the plan')

            # Set up tenant environment
            self.plans_api_helper['TenantAdmin'] = PlansHelper(
                self.tcinputs["MSPCommCell"],
                username=self.tcinputs["TenantUsername"],
                password=self.tcinputs["TenantPassword"]
            )

            self.cv_entities['TenantAdmin'] = CVEntities(self.plans_api_helper['TenantAdmin'].commcell_obj)

            self.log.info('\t6. Successfully logged in as tenant admin')
            # Attempt derivation with inheritance disabled
            tc_derived_plans = None
            try:
                tc_derived_plans = self.plans_api_helper[
                    'TenantAdmin'].inherit_plan(
                        tc_base_plan.plan_name,
                        'Auto_derived_serverplan_{0}'.format(time.time())
                    )
            except Exception as exp:
                self._log.info(str(exp))
                self._log.info(
                    "\t7. Successfully validated inheritance disabled case"
                )
            if tc_derived_plans:
                raise Exception(
                    "Plan derivation successful with inheritance disabled"
                )

            # Enable base plan inheritance with RPO and storage set as private
            override_restriction = {
                'privateEntities': [1, 4]
            }
            tc_base_plan = self.plans_api_helper[
                'MSPAdmin'].modify_inheritance(
                    tc_base_plan.plan_name,
                    override_restriction
                )
            self._log.info("\t8. Successfully enabled inheritance")

            # Validate override restrictions
            self.plans_api_helper['MSPAdmin'].validate_overriding(
                tc_base_plan.plan_name,
                override_restriction
            )

            # Associate tenant to media agent
            self.ug_helper.modify_security_associations(
                {
                    'assoc1': {
                        'mediaAgentName': [self.tcinputs["MediaAgent"]],
                        'role': ['Tenant Admin']
                    }
                },
                '{0}\\{1}'.format(
                    self.tcinputs["CompanyName"],
                    plansconstants.TENANT_ADMIN)
            )
            self._log.info("\t10. Successfully added permissions for tenant user for storage pool")

            # Tenant creates a storage pool
            tc_storage_pool = self.cv_entities['TenantAdmin'].create_storage_pool(
                storage_pool_name="{0}-{1}-Tenant".format(plansconstants.dedupe_storage, self.id),
                mountpath="C:\\{0}\\StoragePoolTenant{1}".format(self.id, time.time()),
                mediaagent=self.tcinputs["MediaAgent"],
                ddb_ma=self.tcinputs["MediaAgent"],
                deduppath="C:\\{0}\\StoragePoolTenant{1}".format(self.id, time.time())
            ).storage_pool_name

            # Create derived plans
            derived_plans = []
            derived_plans.append(
                self.plans_api_helper['TenantAdmin'].inherit_plan(
                    tc_base_plan.plan_name,
                    'Auto_derived_serverplan_{0}'.format(time.time()),
                    storage_pool=tc_storage_pool,
                    sla_in_minutes=60
                )
            )
            self._log.info(
                "\t11. Successfully created a derived plan with private RPO & storage"
            )

            self.plans_api_helper['MSPAdmin'].validate_inheritance(
                tc_base_plan.plan_name,
                derived_plans[-1].plan_name,
                override_restriction
            )

            # Modify override restrictions to optional
            override_restriction = {}
            tc_base_plan = self.plans_api_helper[
                'MSPAdmin'].modify_inheritance(
                    tc_base_plan.plan_name,
                    override_restriction
                )
            self._log.info("\t12. Successfully modified inheritance")

            self.plans_api_helper['MSPAdmin'].validate_overriding(
                tc_base_plan.plan_name,
                override_restriction
            )

            derived_plans.append(
                self.plans_api_helper['TenantAdmin'].inherit_plan(
                    tc_base_plan.plan_name,
                    'Auto_derived_serverplan_{0}'.format(time.time())
                )
            )
            self._log.info(
                "\t13. Successfully created derived plan with optional inheritance"
            )

            self.plans_api_helper['MSPAdmin'].validate_inheritance(
                tc_base_plan.plan_name,
                derived_plans[-1].plan_name,
                override_restriction
            )

            # Set derived plan operation window
            self.plans_api_helper['TenantAdmin'].set_operation_window(
                derived_plans[0].plan_name, plansconstants.window
            )
            self._log.info(
                "\t14. Successfully set operation window of derived plan"
            )

            # Validate derived plan operation window
            if (self.plans_api_helper['MSPAdmin'].validate_operation_window(
                    derived_plans[0].plan_name, plansconstants.window
                    )):
                self._log.info("\t14. Successfully validated operation window of derived plan")
            else:
                raise Exception("Failed to validate operation window of derived plan")

            # Set derived plan full operation window
            self.plans_api_helper['TenantAdmin'].set_operation_window(
                derived_plans[0].plan_name, plansconstants.full_window, full=True
            )
            self._log.info(
                "\t15. Successfully set full operation window of derived plan"
            )

            # Validate derived plan full operation window
            if (self.plans_api_helper['TenantAdmin'].validate_operation_window(
                    derived_plans[0].plan_name, plansconstants.full_window, full=True
                    )):
                self._log.info("\t15. Successfully validated full operation window of derived plan")
            else:
                raise Exception("Failed to validate full operation window of derived plan")

            # Delete derived plan operation window
            self.plans_api_helper['TenantAdmin'].set_operation_window(
                derived_plans[0].plan_name, None
            )
            self._log.info(
                "\t16. Successfully deleted operation window of derived plan"
            )

            # Validate derived plan operation window
            if (self.plans_api_helper['TenantAdmin'].validate_operation_window(
                    derived_plans[0].plan_name, None
                    )):
                self._log.info("\t16. Successfully validated operation window deletion of derived plan")
            else:
                raise Exception("Failed to validate operation window of derived plan")

            # Delete derived plan full operation window
            self.plans_api_helper['TenantAdmin'].set_operation_window(
                derived_plans[0].plan_name, None, full=True
            )
            self._log.info(
                "\t17. Successfully deleted full operation window of derived plan"
            )

            # Validate derived plan full operation window
            if (self.plans_api_helper['TenantAdmin'].validate_operation_window(
                    derived_plans[0].plan_name, None, full=True
                    )):
                self._log.info("\t17. Successfully validated full operation window deletion of derived plan")
            else:
                raise Exception("Failed to validate full operation window of derived plan")

            # Modify override restrictions to enforce entities
            override_restriction = {
                'enforcedEntities': [1, 4]
            }
            tc_base_plan = self.plans_api_helper[
                'MSPAdmin'].modify_inheritance(
                    tc_base_plan.plan_name,
                    override_restriction
                )
            self._log.info("\t18. Successfully modified inheritance")

            self.plans_api_helper['MSPAdmin'].validate_overriding(
                tc_base_plan.plan_name,
                override_restriction
            )

            derived_plans.append(
                self.plans_api_helper['TenantAdmin'].inherit_plan(
                    tc_base_plan.plan_name,
                    'Auto_derived_serverplan_{0}'.format(time.time())
                )
            )
            self._log.info(
                "\t19. Successfully created derived plan with enforced rules"
            )

            self.plans_api_helper['MSPAdmin'].validate_inheritance(
                tc_base_plan.plan_name,
                derived_plans[-1].plan_name,
                override_restriction
            )

            # Delete the derived plans
            for plan in derived_plans:
                tc_plan_delete = self.plans_api_helper[
                    'TenantAdmin'].delete_plan(
                        plan.plan_name
                    )
                if not tc_plan_delete:
                    self._log.error("Plan deletion failed")
                self._log.info("\t20. Successfully deleted derived plan")

            # Set default plan as none
            self.plans_api_helper['MSPAdmin'].company_default_plan(
                self.tcinputs['CompanyName']
            )
            self._log.info("\t21. Successfully removed base plan as company's default plan")

        except Exception as exp:
            self.server.fail(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self._log.info("\tIn FINAL BLOCK")
        self.plans_api_helper['MSPAdmin'].delete_plan(
            plansconstants.BASE_SERVER_PLAN
        )
        self.commcell_obj.storage_pools.delete("{0}-{1}".format(
            plansconstants.dedupe_storage, self.id))
        self.commcell_obj.storage_pools.delete("{0}-{1}-Tenant".format(
            plansconstants.dedupe_storage, self.id))
        self.plans_api_helper['MSPAdmin'].cleanup_plans('delete59104')
