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
import random

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger
from Server.Plans.planshelper import PlansHelper
from AutomationUtils.options_selector import CVEntities
from FileSystem.FSUtils.fshelper import FSHelper
from Server.Plans import plansconstants
from Server.serverhelper import ServerTestCases
from Server.JobManager.jobmanager_helper import JobManager


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
        self.name = "[Server plan] Plan RPO and schedule operations"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.PLANS
        self.tcinputs = {}
        self.commcell_obj = None
        self.plans_api_helper = None
        self.fs_helper = None
        self.job_manager = None
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
            )
        }
        self.server = ServerTestCases(self)
        self.job_manager = JobManager(commcell=self.commcell_obj)
        self.fs_helper = FSHelper(self)
        self.cv_entities = CVEntities(self.commcell_obj)

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("\tStarted executing {0} testcase".format(self.id))
            self.fs_helper.populate_tc_inputs(self, mandatory=False)

            # Retrieve a Storage Pool
            dd_storage_pool = self.cv_entities.create_storage_pool(
                storage_pool_name="{0}-{1}".format(plansconstants.dedupe_storage, self.id),
                mountpath="C:\\{0}\\StoragePool{1}".format(self.id, time.time()),
                mediaagent=self.tcinputs["MediaAgent"],
                ddb_ma=self.tcinputs["MediaAgent"],
                deduppath="C:\\{0}\\StoragePool{1}".format(self.id, time.time())
            ).storage_pool_name

            tc_plans = []

            # Create a plan with
            plan_subtype = plansconstants.SUBTYPE_SERVER
            tc_plans.append(
                self.plans_api_helper['MSPAdmin'].create_base_plan(
                    plansconstants.SCHEDULE_SERVER_PLAN,
                    plan_subtype,
                    dd_storage_pool,
                    sla_in_minutes=120
                )
            )
            self._log.info(
                "\t1. Successfully created plan with deduplication storage pool"
            )

            # Validate plan creation
            self.plans_api_helper['MSPAdmin'].validate_plan_props(tc_plans[0])
            self._log.info("\t2. Validation of backend entities successful")

            if self.plans_api_helper['MSPAdmin'].validate_schedules(tc_plans[0].plan_name):
                self.log.info("\t2. Plans schedules validated")
            else:
                raise Exception("Schedule validation unsuccessful")

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
            self._log.info("\t3. Successfully associated subclient to plan.")

            self.backupset.backup()

            # Set plan incremental RPO in hours
            hourly = random.randint(1, 23)
            self.plans_api_helper['MSPAdmin'].modify_rpo(
                tc_plans[0].plan_name,
                {'hours': hourly}
            )
            self.log.info("\t4. Set plan RPO to an hourly continuous type")

            if self.plans_api_helper['MSPAdmin'].validate_rpo(
                    tc_plans[0].plan_name,
                    hourly * 60
                    ):
                self.log.info("\t4. Successfully validated the hourly incremental RPO modification")
            else:
                raise Exception("Incremental RPO validation failed")

            # Set plan incremental RPO in days
            freq = random.randint(1, 6)
            start_time = time.strftime('%H:%M')
            daily = {
                'days': {
                    'runEvery': freq,
                    'startTime': start_time
                }
            }
            self.plans_api_helper['MSPAdmin'].modify_rpo(
                tc_plans[0].plan_name,
                daily
            )
            self.log.info("\t5. Set plan RPO to a daily type")

            if self.plans_api_helper['MSPAdmin'].validate_rpo(
                    tc_plans[0].plan_name,
                    freq * plansconstants.DAILY_RPO,
                    pattern=daily
                    ):
                self.log.info("\t5. Successfully validated the daily incremental RPO modification")
            else:
                raise Exception("Incremental RPO validation failed")

            # Set plan full RPO in days
            self.plans_api_helper['MSPAdmin'].modify_rpo(
                tc_plans[0].plan_name,
                daily,
                full_schedule=True
            )
            self.log.info("\t6. Set plan full schedule to an daily type")

            if self.plans_api_helper['MSPAdmin'].validate_rpo(
                    tc_plans[0].plan_name,
                    freq * plansconstants.DAILY_RPO,
                    pattern=daily,
                    full_schedule=True
                    ):
                self.log.info("\t6. Successfully validated the daily fulls schedule modification")
            else:
                raise Exception("Daily full RPO validation failed")

            self.job_manager.kill_active_jobs(self.tcinputs["ClientName"])

            # Set plan incremental RPO in weeks
            start_time = time.strftime('%H:%M')
            weekly = {
                'weeks': {
                    'runEvery': 1,
                    'startTime': start_time,
                    'days': random.sample(plansconstants.WEEK_DAYS, k=4)
                }
            }
            self.plans_api_helper['MSPAdmin'].modify_rpo(
                tc_plans[0].plan_name,
                weekly
            )
            self.log.info("\t7. Set plan RPO to an weekly type")

            if self.plans_api_helper['MSPAdmin'].validate_rpo(
                    tc_plans[0].plan_name,
                    plansconstants.WEEKLY_RPO,
                    pattern=weekly
                    ):
                self.log.info("\t7. Successfully validated the weekly incremental RPO modification")
            else:
                raise Exception("Weekly Incremental RPO validation failed")

            # Set plan incremental RPO in minutes
            minutes = 45
            self.plans_api_helper['MSPAdmin'].modify_rpo(
                tc_plans[0].plan_name,
                {'minutes': minutes}
            )
            self.log.info("\t8. Set plan RPO to an minute continuous type")

            if self.plans_api_helper['MSPAdmin'].validate_rpo(
                    tc_plans[0].plan_name,
                    minutes
                    ):
                self.log.info("\t8. Successfully validated the minut ewise incremental RPO modification")
            else:
                raise Exception("Incremental RPO validation failed")

            # Validate log schedule RPO
            if self.plans_api_helper['MSPAdmin'].validate_rpo(
                    tc_plans[0].plan_name,
                    minutes,
                    pattern={'continuous': 240},
                    policy_type='log'
                    ):
                self.log.info("\t9. Successfully validated the weekly incremental RPO modification")
            else:
                raise Exception("Weekly Incremental RPO validation failed")

            self.plans_api_helper['MSPAdmin'].disable_schedule(tc_plans[0].plan_name)
            self._log.info("\t10. Disabled full schedule")

            # Validate subclient association with plan
            if (self.plans_api_helper['MSPAdmin'].validate_subclient_association(
                    tc_plans[0].plan_name,
                    self.tcinputs["ClientName"],
                    backupset_name,
                    plansconstants.DEFAULT_SUBCLIENT_NAME,
                    validate_rpo=True
                    )):
                self._log.info("\t11. Successfully validated subclient association")
            else:
                self.log.error("Validation of subclient assoication failed")

            # Dissociate entity from plan
            self.plans_api_helper['MSPAdmin'].dissociate_entity(
                self.tcinputs["ClientName"],
                backupset_name,
                plansconstants.DEFAULT_SUBCLIENT_NAME
            )
            self._log.info("\t12. Successfully dissociated subclient from plan")

            self.job_manager.kill_active_jobs(self.tcinputs["ClientName"])

            # Delete the plans
            for plan in tc_plans:
                tc_plan_delete = self.plans_api_helper[
                    'MSPAdmin'].delete_plan(
                        plan.plan_name
                    )
                if not tc_plan_delete:
                    self._log.error("Plan deletion failed")
                self._log.info("\t13. Successfully deleted plan")

        except Exception as exp:
            self.server.fail(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self._log.info("\tIn FINAL BLOCK")
        self.commcell_obj.storage_policies.delete(plansconstants.SCHEDULE_SERVER_PLAN)
        self.commcell_obj.storage_pools.delete("{0}-{1}".format(
            plansconstants.dedupe_storage, self.id))
        self.plans_api_helper['MSPAdmin'].cleanup_plans(plansconstants.SCHEDULE_SERVER_PLAN)
