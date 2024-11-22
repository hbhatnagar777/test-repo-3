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
from AutomationUtils.options_selector import CVEntities
from FileSystem.FSUtils.fshelper import FSHelper
from Server.Plans import plansconstants
from Server.serverhelper import ServerTestCases
from Server.Security.userhelper import UserHelper


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
        self.name = "[Server plan] Plan backup destinations and storage operations"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.PLANS
        self.tcinputs = {}
        self.commcell_obj = None
        self.plans_api_helper = None
        self.fs_helper = None
        self.cv_entities = None
        self.user_helper = None

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
            'CommcellUser': None
        }
        self.server = ServerTestCases(self)
        self.fs_helper = FSHelper(self)
        self.cv_entities = CVEntities(self.commcell_obj)
        self.user_helper = UserHelper(self.commcell_obj)

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("\tStarted executing {0} testcase".format(self.id))
            self.fs_helper.populate_tc_inputs(self, mandatory=False)

            # Create a storage pool
            dd_storage_pool = self.cv_entities.create_storage_pool(
                storage_pool_name="{0}-{1}".format(plansconstants.dedupe_storage, self.id),
                mountpath="C:\\{0}\\StoragePool{1}".format(self.id, time.time()),
                mediaagent=self.tcinputs["MediaAgent"],
                ddb_ma=self.tcinputs["MediaAgent"],
                deduppath="C:\\{0}\\StoragePool{1}".format(self.id, time.time())
            ).storage_pool_name

            tc_plans = []

            # Create a plan with dedupe storage
            plan_subtype = plansconstants.SUBTYPE_SERVER
            tc_plans.append(
                self.plans_api_helper['MSPAdmin'].create_base_plan(
                    '{0}-Dedupe'.format(plansconstants.STORAGE_SERVER_PLAN),
                    plan_subtype,
                    dd_storage_pool
                )
            )
            self._log.info(
                "\t1. Successfully created plan with deduplication storage pool"
            )

            # Validate plan creation
            self.plans_api_helper['MSPAdmin'].validate_plan_props(tc_plans[0])
            self._log.info("\t2. Validation of backend entities successful")

            # Create a non dedupe storage pool
            req_payload = plansconstants.ndd_storage_pool
            req_payload['storagePolicyName'] = "{0}-{1}".format(plansconstants.non_dedupe_storage, self.id)
            req_payload['storage'][0]['mediaAgent']['mediaAgentName'] = self.tcinputs["MediaAgent"]
            req_payload['storage'][0]['path'] = "C:\\{0}\\StoragePool{1}".format(self.id, time.time())
            req_payload['storagePolicyCopyInfo']['mediaAgent']['mediaAgentName'] = self.tcinputs["MediaAgent"]

            ndd_storage_pool = self.plans_api_helper['MSPAdmin'].create_ndd_storage(
                req_payload
            )

            # Create a plan with non-dedupe storage
            plan_subtype = plansconstants.SUBTYPE_SERVER
            tc_plans.append(
                self.plans_api_helper['MSPAdmin'].create_base_plan(
                    '{0}-Non-Dedupe'.format(plansconstants.STORAGE_SERVER_PLAN),
                    plan_subtype,
                    ndd_storage_pool
                )
            )
            self._log.info(
                "\t3. Successfully created plan with non-dedupe storage pool"
            )

            # Validate plan creation
            self.plans_api_helper['MSPAdmin'].validate_plan_props(tc_plans[1])
            self._log.info("\t4. Validation of backend entities successful")

            # Add a dedupe copy to the non-dedupe plan
            copy_name = self.plans_api_helper['MSPAdmin'].add_copy(
                tc_plans[1].plan_name,
                dd_storage_pool,
                retention=1,
                extended_retention=plansconstants.extended_retention_rule)
            self._log.info("\t5. Added a backup copy to the plan")

            temp_copy = {
                copy_name: {
                    'storagePool': dd_storage_pool,
                    'retention': 1,
                    'extendedRetention': plansconstants.extended_retention_rule
                }
            }

            # Validate the copies of the plan
            if (self.plans_api_helper['MSPAdmin'].validate_copies(
                    tc_plans[1].plan_name,
                    ndd_storage_pool,
                    secondary_copy=temp_copy
                    )):
                self._log.info("\t5. Successfully validated backup copies")
            else:
                raise Exception("Validation of copies failed")

            # Validated autocopy schedule for the plan's storage policy
            if (self.plans_api_helper['MSPAdmin'].validate_autocopy(
                    tc_plans[1].plan_name,
                    plansconstants.autocopy_schedule
                    )):
                self._log.info("\t6. Successfully validated autocopy schedule")
            else:
                raise Exception("Autocopy schedule validation failed")

            # Delete the secondary copy
            if self.plans_api_helper['MSPAdmin'].delete_copy(tc_plans[1].plan_name, plansconstants.SECONDARY_COPY_NAME):
                self._log.info("\t7. Successfully deleted secondary copy")
            else:
                self._log.error("Copy - {0} failed to delete".format(plansconstants.SECONDARY_COPY_NAME))
                raise Exception("Secondary copy deletion failed")

            # Validate the copies of the plan
            if (self.plans_api_helper['MSPAdmin'].validate_copies(
                    tc_plans[1].plan_name,
                    ndd_storage_pool
                    )):
                self._log.info("\t7. Successfully validated backup copies")
            else:
                raise Exception("Validation of copies failed")

            # Validated autocopy schedule for the plan's storage policy
            if not (self.plans_api_helper['MSPAdmin'].validate_autocopy(
                    tc_plans[1].plan_name,
                    plansconstants.autocopy_schedule
                    )):
                self._log.info("\t7. Successfully validated autocopy schedule")
            else:
                raise Exception("Autocopy schedule validation failed")

            # Delete the primary copy
            if self.plans_api_helper['MSPAdmin'].delete_copy(tc_plans[0].plan_name, 'Primary'):
                self._log.error("Primary copy was deleted")
                raise Exception("Primary copy deletion succeeded")
            else:
                self._log.info("\t8. Failed to delete primary copy")

            # Validate the copies of the plan
            if (self.plans_api_helper['MSPAdmin'].validate_copies(
                    tc_plans[1].plan_name,
                    ndd_storage_pool,
                    )):
                self._log.info("\t8. Successfully validated backup copies")
            else:
                raise Exception("Validation of copies failed")

            # Create a commcell user with limited permissions
            user_obj = self.user_helper.create_user(
                'automation-user-{0}'.format(self.id),
                '{0}@commvault.com'.format(self.id),
                password='automation-user-{0}'.format(self.id),
                security_dict={
                    'assoc2': {
                        'planName': [tc_plans[0].plan_name],
                        'role': ['Plan Subscription Role']
                    }
                }
            )

            self.plans_api_helper['CommcellUser'] = PlansHelper(
                self.tcinputs["MSPCommCell"],
                username=user_obj.user_name,
                password='automation-user-{0}'.format(self.id)
            )

            # Commcell user attempts to delete plan
            if self.plans_api_helper['CommcellUser'].delete_plan(tc_plans[0].plan_name):
                self._log.error("Commcell user was able to delte plan")
                raise Exception("Security test failed")
            else:
                self._log.info("\t9. Commcell user with limited permission prevented from deleting plan")

            # Create a new backupset
            backupset_name = "backupset_{0}".format(self.id)
            self.fs_helper.create_backupset(name=backupset_name, delete=True)

            # Associate a subclient to plan
            self.plans_api_helper['MSPAdmin'].entity_to_plan(
                tc_plans[0].plan_name,
                self.tcinputs["ClientName"],
                backupset_name,
                plansconstants.DEFAULT_SUBCLIENT_NAME
            )
            self._log.info("\t10. Successfully associated subclient to plan.")

            # Validate subclient association with plan
            if (self.plans_api_helper['MSPAdmin'].validate_subclient_association(
                    tc_plans[0].plan_name,
                    self.tcinputs["ClientName"],
                    backupset_name,
                    plansconstants.DEFAULT_SUBCLIENT_NAME
                    )):
                self._log.info("\t10. Successfully validated subclient association")
            else:
                raise Exception("Validation of subclient assoication failed")

            # Dissociate entity from plan
            self.plans_api_helper['MSPAdmin'].dissociate_entity(
                self.tcinputs["ClientName"],
                backupset_name,
                plansconstants.DEFAULT_SUBCLIENT_NAME
            )
            self._log.info("\t11. Successfully dissociated subclient from plan")

            # Associate plan's storage policy to subclient
            self.plans_api_helper['MSPAdmin'].policy_to_subclient(
                tc_plans[1].plan_name,
                self.tcinputs['ClientName'],
                backupset_name,
                plansconstants.DEFAULT_SUBCLIENT_NAME
            )
            self._log.info("\t12. Successfully associated policy to subclient")

            # Validate subclient association with plan
            if (self.plans_api_helper['MSPAdmin'].validate_subclient_association(
                    tc_plans[1].plan_name,
                    self.tcinputs["ClientName"],
                    backupset_name,
                    plansconstants.DEFAULT_SUBCLIENT_NAME
                    )):
                self._log.info("\t12. Successfully validated subclient association")
            else:
                raise Exception("Validation of subclient assoication failed")

            self.plans_api_helper['MSPAdmin'].dissociate_entity(
                self.tcinputs["ClientName"],
                backupset_name,
                plansconstants.DEFAULT_SUBCLIENT_NAME
            )
            self._log.info("\t13. Successfully dissociated subclient from plan")

            # Delete the plans
            for plan in tc_plans:
                tc_plan_delete = self.plans_api_helper[
                    'MSPAdmin'].delete_plan(
                        plan.plan_name
                    )
                if not tc_plan_delete:
                    self._log.error("Plan deletion failed")
                self._log.info("\t14. & 15. Successfully deleted plan")

        except Exception as exp:
            self.server.fail(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self._log.info("\tIn FINAL BLOCK")
        self.user_helper.delete_user(
            'automation-user-{0}'.format(self.id),
            new_user=self.commcell_obj.commcell_username)
        self.commcell_obj.storage_pools.delete("{0}-{1}".format(
            plansconstants.dedupe_storage, self.id))
        self.commcell_obj.storage_pools.delete("{0}-{1}".format(
            plansconstants.non_dedupe_storage, self.id))
        self.plans_api_helper['MSPAdmin'].cleanup_plans(plansconstants.STORAGE_SERVER_PLAN)
