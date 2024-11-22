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
from Server.Plans.planshelper import PlansHelper
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
        self.name = "REST API functionality for Server Plans"
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
                commcell_obj=self.commcell_obj
            ),
            'TenantAdmin': PlansHelper(
                self.tcinputs["MSPCommCell"],
                username=self.tcinputs["TenantUsername"],
                password=self.tcinputs["TenantPassword"]
            )
        }
        self.server = ServerTestCases(self)

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("Started executing {0} testcase".format(self.id))

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

            # Retrieve any Storage Pool
            tc_storage_pool = self.plans_api_helper[
                'MSPAdmin'].get_storage_pool()

            # Create a base plan
            plan_subtype = plansconstants.SUBTYPE_SERVER
            tc_base_plan = self.plans_api_helper['MSPAdmin'].create_base_plan(
                plansconstants.BASE_SERVER_PLAN,
                plan_subtype,
                tc_storage_pool,
            )
            self._log.info(
                "\tSuccessfully created {0} plan with {1} storage pool".format(
                    tc_base_plan.plan_name,
                    tc_storage_pool
                )
            )

            # Validate plan creation
            self.plans_api_helper['MSPAdmin'].validate_plan_props(tc_base_plan)
            self._log.info("\tValidation of backend entities successful")

            # Associate plan to company
            self.plans_api_helper['MSPAdmin'].plan_to_company(
                self.tcinputs['CompanyName'],
                tc_base_plan.plan_name
            )
            self._log.info(
                "Successfully associated {0} plan to {1} company".format(
                    tc_base_plan.plan_name,
                    self.tcinputs['CompanyName']
                )
            )

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
                    "\tSuccessfully validated inheritance disabled case"
                )
            if tc_derived_plans:
                raise Exception(
                    "Plan derivation successful with inheritance disabled"
                )

            # Enable base plan inheritance with RPO set as private
            override_restriction = {
                'privateEntities': [4]
            }
            tc_base_plan = self.plans_api_helper[
                'MSPAdmin'].modify_inheritance(
                    tc_base_plan.plan_name,
                    override_restriction
                )
            self._log.info("\tSuccessfully enabled inheritance")

            # Validate override restrictions
            self.plans_api_helper['MSPAdmin'].validate_overriding(
                tc_base_plan.plan_name,
                override_restriction
            )

            # Create derived plans
            derived_plans = []
            derived_plans.append(
                self.plans_api_helper['TenantAdmin'].inherit_plan(
                    tc_base_plan.plan_name,
                    'Auto_derived_serverplan_{0}'.format(time.time()),
                    sla_in_minutes=60
                )
            )
            self._log.info(
                "\tSuccessfully created a derived plan with private RPO"
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
                "\tSuccessfully created derived plan with optional inheritance"
            )

            self.plans_api_helper['MSPAdmin'].validate_inheritance(
                tc_base_plan.plan_name,
                derived_plans[-1].plan_name,
                override_restriction
            )

            # Modify override restrictions to enforce entities
            override_restriction = {
                'enforcedEntities': [1, 4, 256, 512, 1024]
            }
            tc_base_plan = self.plans_api_helper[
                'MSPAdmin'].modify_inheritance(
                    tc_base_plan.plan_name,
                    override_restriction
                )

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
                "\tSuccessfully created derived plan with enforced rules"
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
                self._log.info("\tSuccessfully deleted derived plan")

        except Exception as exp:
            self.server.fail(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self._log.info("\tIn FINAL BLOCK")
        self.plans_api_helper['MSPAdmin'].cleanup_plans('delete50721')
