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

import datetime
import time
from datetime import timedelta, datetime
from cvpysdk.activateapps.constants import TargetApps
from cvpysdk.job import JobController
from cvpysdk.plan import Plan
from cvpysdk.schedules import SchedulePattern
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import CVEntities
from FileSystem.FSUtils.fshelper import FSHelper
from Server.JobManager.jobmanager_helper import JobManager
from Server.Plans import plansconstants
from Server.Plans.planshelper import PlansHelper
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
                                        "AgentName": "File System",
                                        "ClientName": "Client name",
                                        "TestPath": "Testpath",
                                        "MediaAgent": "Media_agent name",
                                        "StoragePolicyName": "Sp name",
                                        "ContentIndexingServer": "client where indexplayback happens"
                                        "IndexServer": "CI indexserver used"
                                        }
        """
        super(TestCase, self).__init__()
        self.name = "DC Plan Content Indexing Validation"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.PLANS
        self.tcinputs = {}
        self.test_path = ""
        self.commcell_obj = None
        self.plans_api_helper = None
        self.fs_helper = None
        self.job_manager = None
        self.cv_entities = None
        self.timeout = 300

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
        self.indexserver = self.tcinputs['IndexServer']
        self.server = ServerTestCases(self)
        self.job_manager = JobManager(commcell=self.commcell_obj)
        self.fs_helper = FSHelper(self)
        self.cv_entities = CVEntities(self.commcell_obj)

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("\tStarted executing {0} testcase".format(self.id))
            self.fs_helper.populate_tc_inputs(self, mandatory=False)
            test_path = self.test_path
            slash_format = self.slash_format
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            indexplayback = False
            attempt_count = 0
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
            self.backupset_name = "backupset_{0}".format(self.id)
            self.fs_helper.create_backupset(name=self.backupset_name, delete=True)
            subclient_name = "subclient_{0}".format(self.id)
            subclient_content = []
            subclient_content.append(test_path)
            self.csmachine = Machine(
                self.commcell_obj.commserv_client.client_name,
                self.commcell_obj
            )
            self.contentindexing_obj = Machine(
                self.tcinputs["ContentIndexingServer"],
                self.commcell_obj
            )
            run_path = ("%s%s%s" % (subclient_content[0], slash_format, str(self.runid)))
            full_data_path = ("%s%sfull" % (run_path, slash_format))
            self.log.info("Adding data under path: %s", full_data_path)
            files = 100
            self.windows_extensions = ".doc,.txt"
            self.fs_helper.generate_testdata(self.windows_extensions.split(','), full_data_path, no_of_files=files)
            self.fs_helper.create_subclient(
                name=subclient_name,
                storage_policy=tc_plans[0].plan_name,
                content=subclient_content
            )
            # Update Subclient with blocklevel value if not set
            self.log.info("Creating Subclient")
            self.plans_obj = self.commcell_obj.plans
            if self.plans_obj.has_plan(plansconstants.SCHEDULE_DC_PLAN):
                self.plans_obj.delete(plansconstants.SCHEDULE_DC_PLAN)
            job_control = JobController(commcell_object=self.commcell_obj)
            self.plans_obj.add_data_classification_plan(plansconstants.SCHEDULE_DC_PLAN, self.indexserver,
                                                        target_app=TargetApps.FS)
            self.dcplan = Plan(self.commcell_obj, plansconstants.SCHEDULE_DC_PLAN)

            timeframe = self.csmachine.get_system_time().splitlines()
            sch = SchedulePattern()
            schedule_pattern = {'freq_type': 'Daily'}
            schedule_json = sch.create_schedule_pattern(schedule_pattern)
            self.dcplan.schedule(self.dcplan.plan_name, schedule_json)
            self.log.info("DC plan created and Schedule Associated ")
            self.subclient.enable_dc_content_indexing(plansconstants.SCHEDULE_DC_PLAN)
            self.log.info("Subclient associated to DC plan ")
            # Associate a subclient to plan
            self.plans_api_helper['MSPAdmin'].entity_to_plan(
                tc_plans[0].plan_name,
                self.tcinputs["ClientName"],
                self.backupset_name,
                subclient_name
            )
            self._log.info("\t3. Successfully associated subclient to plan.")
            time.sleep(10)
            self.log.info("Checking Job status ")
            jobs = job_control.active_jobs(self.client_name)
            if bool(jobs):
                self.log.info("Job triggered by plan")
                Jobs_list = [a_dict for a_dict in jobs]
                job_obj = job_control.get(Jobs_list[0])
                self.log.info("Backup Job ran : %s", job_obj.job_id)
                if not job_obj.wait_for_completion():
                    raise Exception(
                        "Failed to run  Workflow job {0} for backup copy with error: {1}".format(
                            job_obj.job_id, job_obj.delay_reason)
                    )
                self.log.info("Successfully finished backup copy workflow Job :%s", job_obj.job_id)
            else:
                job_obj = self.fs_helper.run_backup_verify(backup_level="Full")[0]
                attempt_count = attempt_count + 1
                if not job_obj.wait_for_completion():
                    raise Exception(
                        "Failed to run backup job {0}  with error: {1}".format(
                            job_obj.job_id, job_obj.delay_reason)
                    )
                self.log.info("Successfully finished backup  Job :%s", job_obj.job_id)
            self.log.info("Checking playback status")
            while indexplayback == False and attempt_count <= 2:
                self.log.info("Waiting for play back to finish")
                time.sleep(self.timeout)
                logs = self.contentindexing_obj.get_logs_for_job_from_file(log_file_name="IndexServer.log",
                                                                           job_id=job_obj.job_id,
                                                                           search_term="Response from webserver:")
                if logs:
                    indexplayback = True
                    self.log.info("Play back succesful")
                else:
                    self.log.info("Play back didnt run for full succesful running next attempt")
                    job_incr1 = self.fs_helper.run_backup_verify(backup_level="Full")[0]
                    attempt_count = attempt_count + 1
                    if not job_incr1.wait_for_completion():
                        raise Exception(
                            "Failed to run backup job {0} with error: {1}".format(
                                job_incr1.job_id, job_incr1.delay_reason)
                        )
                    self.log.info("Successfully finished backup Job :%s", job_incr1.job_id)

            else:
                if attempt_count == 3 and indexplayback == False:
                    self.log.info(" Play Back Failed for 3 attempts...please check.... ")
                    raise Exception(
                        "play back to Solr is failing as we dont see any response from  webserver "
                    )
            # self.get_document_count_in_index(job_obj.job_id, full=True)
            current_time = datetime.now()
            future_time = current_time + timedelta(minutes=5)
            updated_time = future_time.strftime('%H:%M')
            schedule_pattern2 = {'freq_type': 'Daily', "active_start_time": updated_time,
                                 "repeat_days": 1}
            schedule_json = sch.create_schedule_pattern(schedule_pattern2)
            self.dcplan.schedule(self.dcplan.plan_name, schedule_json)
            self.log.info("Schedule updated to new time and waiting...")
            time.sleep(self.timeout)
            attempt = 0
            jobs = job_control.active_jobs(job_filter='MULTI_NODE_CONTENT_INDEXING')
            Jobs_list = [a_dict for a_dict in jobs]
            self.log.info("Jobs in list {0}".format(Jobs_list[0]))
            while Jobs_list is None and attempt < 10:
                time.sleep(10)
                jobs = job_control.active_jobs(job_filter='MULTI_NODE_CONTENT_INDEXING')
                attempt = attempt+1
                Jobs_list = [a_dict for a_dict in jobs]
            self.log.info("Jobs in list {0}".format(Jobs_list[0]))
            job_obj = job_control.get(Jobs_list[0])
            self.log.info("Content Indexing job ran : %s", job_obj.job_id)
            if not job_obj.wait_for_completion():
                raise Exception(
                    "Failed to run Backup job {0} with error: {1}".format(
                        job_obj.job_id, job_obj.delay_reason)
                )
            self.log.info("Successfully finished backup Job :%s", job_obj.job_id)
            if job_obj.num_of_files_transferred >= files:
                self.log.info("Files Qualified for CI")
            else:
                self.log.info("Files not Qualified for CI")
                self.log.info("Please check playback happend or not")
                raise Exception("Files not Qualified for CI")

            self.log.info("*************FULL job validation completed**********")

            self.log.info("*************INCR job validation started**********")
            incr_data_path = ("%s%sincr" % (run_path, slash_format))
            self.log.info("Adding data under path: %s", incr_data_path)
            files = 50
            self.windows_extensions = ".doc,.txt"
            self.fs_helper.generate_testdata(self.windows_extensions.split(','), incr_data_path, no_of_files=files)
            job_incr1 = self.fs_helper.run_backup_verify(backup_level="Incremental")[0]
            if not job_incr1.wait_for_completion():
                raise Exception(
                    "Failed to run  backup  job {0} with error: {1}".format(
                        job_incr1.job_id, job_incr1.delay_reason)
                )
            self.log.info("Successfully finished backup Job :%s", job_incr1.job_id)

            indexplayback = False
            attempt_count = 0
            while indexplayback == False and attempt_count <= 2:
                self.log.info("waiting for playback to complete")
                time.sleep(self.timeout)
                logs = self.contentindexing_obj.get_logs_for_job_from_file(log_file_name="IndexServer.log",
                                                                           job_id=job_incr1.job_id,
                                                                           search_term="Response from webserver:")
                if logs:
                    indexplayback = True
                    self.log.info("Play back succesful")
                else:
                    self.log.info("Play back didnt run for full succesful running next attempt")
                    incr_data_path=incr_data_path+str(attempt_count)
                    self.fs_helper.generate_testdata(self.windows_extensions.split(','), incr_data_path,
                                                     no_of_files=files)
                    job_incr1 = self.fs_helper.run_backup_verify(backup_level="Incremental")[0]
                    attempt_count = attempt_count + 1
                    if not job_incr1.wait_for_completion():
                        raise Exception(
                            "Failed to run backup job {0}  error: {1}".format(
                                job_incr1.job_id, job_incr1.delay_reason)
                        )
                    self.log.info("Successfully finished backup Job :%s", job_incr1.job_id)
            else:
                if attempt_count == 3 and indexplayback == False:
                    self.log.info(" Play Back Failed for 3 attempts...please check.... ")
                    raise Exception(
                        "play back to Solr is failing as we dont see any response from  webserver "
                    )
            current_time = datetime.now()
            future_time = current_time + timedelta(minutes=5)
            updated_time = future_time.strftime('%H:%M')
            schedule_pattern2 = {'freq_type': 'Daily', "active_start_time": updated_time,
                                 "repeat_days": 1}
            schedule_json = sch.create_schedule_pattern(schedule_pattern2)
            self.dcplan.schedule(self.dcplan.plan_name, schedule_json)
            self.log.info("Schedule updated to new time. and waiting...")
            time.sleep(280)
            attempt = 0
            jobs = job_control.active_jobs(job_filter='MULTI_NODE_CONTENT_INDEXING')
            Jobs_list = [a_dict for a_dict in jobs]
            while Jobs_list is None and attempt < 10:
                time.sleep(10)
                jobs = job_control.active_jobs(job_filter='MULTI_NODE_CONTENT_INDEXING')
                Jobs_list = [a_dict for a_dict in jobs]

            job_obj = job_control.get(Jobs_list[0])
            self.log.info("Content Indexing job ran : %s", job_obj.job_id)
            if not job_obj.wait_for_completion():
                raise Exception(
                    "Failed to run  Workflow job {0} for backup copy with error: {1}".format(
                        job_obj.job_id, job_obj.delay_reason)
                )
            self.log.info("Successfully finished backup copy workflow Job :%s", job_obj.job_id)
            if job_obj.num_of_files_transferred >= files:
                self.log.info("Files Qualified for CI")
            else:
                self.log.info("Files not Qualified for CI")
                raise Exception("Files not Qualified for CI")
                self.log.info("*************INCR job validation completed**********")
            self.log.info("RUN COMPLETED SUCCESFULLY")
            self.status = constants.PASSED

        except Exception as exp:
            self.server.fail(exp)
            self.status = constants.FAILED

        def tear_down(self):
            """Tear down function of this test case"""
            self._log.info("\tIn FINAL BLOCK")
            self.agent.backupsets.delete(self.backupset_name)
            self.commcell_obj.storage_policies.delete(plansconstants.SCHEDULE_SERVER_PLAN)
            self.commcell_obj.storage_pools.delete("{0}-{1}".format(
                plansconstants.dedupe_storage, self.id))
            self.plans_api_helper['MSPAdmin'].cleanup_plans(plansconstants.SCHEDULE_SERVER_PLAN)
            self.plans_api_helper['MSPAdmin'].cleanup_plans(plansconstants.SCHEDULE_DC_PLAN)
