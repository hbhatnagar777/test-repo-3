# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2021 Commvault Systems, Inc.
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
import datetime
import random

from cvpysdk import schedules

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger
from Server.Plans.planshelper import PlansHelper
from AutomationUtils.options_selector import CVEntities
from Server.Plans import plansconstants
from Server.serverhelper import ServerTestCases
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils.machine import Machine
from Server.Scheduler import schedulerhelper
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
        self.name = "[Server plan] Synthetic full backup schedule execution from server plans"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.PLANS
        self.tcinputs = {}
        self.commcell_obj = None
        self.plans_api_helper = None
        self.job_manager = None
        self.cv_entities = None
        self.sch_obj = None
        self.sch_helper = None
        self.dd_storage_pool = None
        self.test_plan_name = None
        self.tc_plans = []

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
        self.cv_entities = CVEntities(self.commcell_obj)
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self)
        self.cs_machine_obj = Machine(self.commcell_obj.commserv_client)
        self.schedules_obj = schedules.Schedules(self.commcell_obj)

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("\tStarted executing {0} testcase".format(self.id))

            # Create a Storage Pool
            self.dd_storage_pool = self.cv_entities.create_storage_pool(
                storage_pool_name="{0}-{1}-{2}".format(plansconstants.dedupe_storage, self.id, time.time()),
                mountpath=plansconstants.STORAGE_PATH.format(self.id, time.time()),
                mediaagent=self.tcinputs["MediaAgent"],
                ddb_ma=self.tcinputs["MediaAgent"],
                deduppath=plansconstants.STORAGE_PATH.format(self.id, time.time())
            ).storage_pool_name

            # Create a plan
            plan_subtype = plansconstants.SUBTYPE_SERVER
            self.tc_plans.append(
                self.plans_api_helper['MSPAdmin'].create_base_plan(
                    "{0}-{1}".format(plansconstants.INCREMENTAL_SERVER_PLAN, time.time()),
                    plan_subtype,
                    self.dd_storage_pool
                )
            )
            self.test_plan_name = self.tc_plans[0].plan_name
            self._log.info(
                "\t1. Successfully created plan with template inputs"
            )

            # Validate plan creation
            self.plans_api_helper['MSPAdmin'].validate_plan_props(self.tc_plans[0])
            self._log.info("\t2. Validation of backend entities successful")

            if self.plans_api_helper['MSPAdmin'].validate_schedules(self.tc_plans[0].plan_name):
                self.log.info("\t2. Plans schedules validated")
            else:
                raise Exception("Schedule validation unsuccessful")

            self.plans_api_helper['MSPAdmin'].disable_schedule(self.tc_plans[0].plan_name)

            entity_inputs = {
                'target':
                {
                    'client': self.tcinputs["ClientName"],
                    'agent': "File system",
                    'instance': "defaultinstancename",
                    'storagepolicy': self.test_plan_name
                },
                'backupset':
                {
                    'name': "backupset_{0}_synthetic".format(self.id),
                    'force': True
                },
                'subclient':
                {
                    'name': "subclient_{0}_synthetic".format(self.id),
                    'force': True
                }
            }

            self.cv_entities.create(entity_inputs)

            self.log.info("\t3. New backup set and subclient created with the server plans")

            # -------------------------- Trigger first continuous full & incremental job --------------

            self.schedules_obj.refresh()
            self.sch_helper = schedulerhelper.SchedulerHelper(
                self.schedules_obj.get(
                    schedule_id=self.tc_plans[0].schedule_policies['data'].all_schedules[0]['schedule_id']),
                self.commcell_obj
            )
            self.sch_helper.timezone = 'Asia/Calcutta'

            self.log.info("Monitoring the trigger of the first backup job")

            self.sch_helper.continuous_schedule_wait(wait_jobs_count=1)

            self.plans_api_helper['MSPAdmin'].modify_rpo(
                self.tc_plans[0].plan_name,
                {'minutes': 5}
            )
            self.log.info("\t3. Set plan RPO to 5 minutes")

            job_obj = self.sch_helper.get_latest_job()

            self.schedules_obj.refresh()
            self.sch_helper = schedulerhelper.SchedulerHelper(
                self.schedules_obj.get(
                    schedule_id=self.tc_plans[0].schedule_policies['data'].all_schedules[0]['schedule_id']),
                self.commcell_obj
            )
            self.sch_helper.timezone = 'Asia/Calcutta'

            self.log.info("\t5. Montitoring the trigger of the minutes schedule")

            self.sch_helper.continuous_schedule_wait(first_job=job_obj, wait_jobs_count=1)

            # Set plan incremental RPO in years on a particular day of a year to avoid conflicts
            yearly = {
                'year': {
                    'freq_recurrence_factor': random.randint(1, 12),
                    'freq_interval': random.randint(1, 25),
                    'startTime': time.strftime('%H:%M')
                }
            }
            self.plans_api_helper['MSPAdmin'].modify_rpo(
                self.tc_plans[0].plan_name,
                yearly
            )

            # -------------------------- Monitor Synth full job --------------

            self.cs_machine_obj.toggle_time_service()

            self.schedules_obj.refresh()

            self.sch_helper = schedulerhelper.SchedulerHelper(
                self.schedules_obj.get(
                    schedule_id=self.tc_plans[0].schedule_policies['data'].all_schedules[1]['schedule_id']),
                self.commcell_obj
            )
            self.sch_helper.timezone = 'Asia/Calcutta'

            self.log.info("\t- Montitoring the trigger of the synth full backup.")

            next_run_date = self.sch_helper.schedule_start_time + datetime.timedelta(31)
            if self.commcell_obj.is_linux_commserv:
                self.cs_machine_obj.execute_command(
                    'date --set="{}"'.format(next_run_date.strftime("%m/%d/%Y %H:%M"))
                )
            else:
                self.cs_machine_obj.execute_command(
                    'set-date -date "{}"'.format(next_run_date.strftime("%m/%d/%Y %H:%M"))
                )
            time.sleep(40)
            self.job_manager.job = self.sch_helper.check_job_for_taskid(retry_interval=30)[0]
            self.job_manager.wait_for_state()

            self.cs_machine_obj.toggle_time_service(stop=False)

            # Dissociate entity from plan
            self.plans_api_helper['MSPAdmin'].dissociate_entity(
                self.tcinputs["ClientName"],
                "backupset_{0}_synthetic".format(self.id),
                "subclient_{0}_synthetic".format(self.id)
            )
            self._log.info("\t6. Successfully dissociated subclient from plan")

            self.job_manager.kill_active_jobs(self.tcinputs["ClientName"])

            # Delete the plans
            for plan in self.tc_plans:
                tc_plan_delete = self.plans_api_helper[
                    'MSPAdmin'].delete_plan(
                        plan.plan_name
                    )
                if not tc_plan_delete:
                    self._log.error("Plan deletion failed")
                self._log.info("\t7. Successfully deleted plan")

        except Exception as exp:
            self.server.fail(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self._log.info("\tIn FINAL BLOCK")
        self._schedule_creator.cleanup()
        self.plans_api_helper['MSPAdmin'].cleanup_plans(self.test_plan_name)
        self.commcell_obj.storage_policies.delete(self.test_plan_name)
        self.commcell_obj.storage_pools.delete(self.dd_storage_pool)
        self.cv_entities.cleanup()
