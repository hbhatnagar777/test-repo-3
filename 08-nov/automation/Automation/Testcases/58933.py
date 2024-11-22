# coding=utf-8
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    setup_environment() -- configures entities based on inputs

    get_active_files_store() -- gets active files DDB store id

    cleanup()   --  cleanups all created entities

    run_backup()    -- runs backup need for the case

    run_data_aging()    -- runs data aging job for storage policy copy created by case

    run_dv2_job()   -- runs DV2 job with options provided

    validate_dv2() -- validates the DDB verification job

Note: if no predefined entities provided in input, we will create them.
if need to use predefined entities like Library or SP. add them to input json

Sample JSON: values under [] are optional
"58933": {
            "ClientName": "client name",
            "AgentName": "File System",
            "MediaAgentName": "ma name",
            Optional :
            [
            "ScaleFactor": "ScaleFactor",
            "DDBPath": "E:\\DDBs\\dv2tests\\0", - path to be used for creating ddb during pool creation. For linux specify LVM path
            "MountPath": "E:\\Libraries\\dv2tests_defragmp", - mount path to use to create storage pool
            or
            "PlanName": "Plan Name"           - existing plan to use
            "PoolName" : "Pool name"
            ]
        }

design:
    run backup J1
    run quick full dv2
    Validate verification time
    run backup J2
    run quick incr dv2
    Validate verification time
    run backup J3
    run complete full dv2
    Validate verification time
    run backup J4
    run complete incr dv2
    Validate verification time
"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Simplify DV2 project - DV2 new GUI options case"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None
        }
        self.pool_name = None
        self.plan_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.content_path = None
        self.mount_path = None
        self.agent_name = None
        self.ddb_path = None
        self.scale_factor = None
        self.bkpset_obj = None
        self.subclient = None
        self.client = None
        self.primary_copy = None
        self.existing_entities = False
        self.ma_name = None
        self.client_name = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.is_user_defined_plan = False
        self.client_machine_obj = False
        self.ma_machine_obj = False
        self.client_drive = False
        self.ma_drive = False
        self.media_agent_obj = None
        self.mmhelper_obj = None
        self.plan = None
        self.option_obj = None
        self.status = constants.PASSED

    def setup(self):
        """
        Setup function of this test case. initialises entity names if provided in tcinputs otherwise assigns new names
        """
        self.option_obj = OptionsSelector(self.commcell)
        self.mmhelper_obj = MMHelper(self)
        suffix = round(time.time())
        self.mount_path = self.tcinputs.get("MountPath")
        self.ma_name = self.tcinputs.get("MediaAgentName")
        self.ddb_path = self.tcinputs.get("DDBPath")
        self.scale_factor = self.tcinputs.get("ScaleFactor")
        self.client_name = self.tcinputs.get("ClientName")
        self.plan_name = self.tcinputs.get("PlanName")
        self.pool_name = self.tcinputs.get("PoolName")
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.media_agent_obj = self.commcell.media_agents.get(self.ma_name)
        self.client_machine_obj = Machine(self.client)

        if self.tcinputs.get("PlanName") and self.tcinputs.get("PoolName"):
            self.is_user_defined_plan = True
            self.existing_entities = True
        else:
            self.plan_name = f"PLAN_{self.id}_{self.ma_name}"
            self.pool_name = f"STORAGEPOOL_{self.id}_{self.ma_name}"
            self.existing_entities = False
        #self.plan = self.commcell.plans.get(self.plan_name)

        if not self.existing_entities:
            if self.tcinputs.get("MountPath"):
                self.is_user_defined_mp = True
            if self.tcinputs.get("DDBPath"):
                self.is_user_defined_dedup = True
        if not self.is_user_defined_dedup and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        self.client_drive = self.option_obj.get_drive(self.client_machine_obj, 25 * 1024)
        if not self.is_user_defined_mp and not self.existing_entities:
            self.ma_drive = self.option_obj.get_drive(self.ma_machine_obj, 25 * 1024)

        if not self.existing_entities:
            if self.is_user_defined_mp:
                self.mount_path = self.ma_machine_obj.join_path(self.tcinputs.get("MountPath"), f"TC_{self.id}", f"LIB_{suffix}")
                self.log.info(f"Using user provided mount path {self.mount_path}")
            else:
                self.mount_path = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"LIB_{suffix}")
            if self.is_user_defined_dedup:
                self.ddb_path = self.ma_machine_obj.join_path(self.tcinputs.get("DDBPath"), f"TC_{self.id}", f"DDB_{suffix}")
                self.log.info(f"Using user provided dedup path {self.ddb_path}")
            else:
                self.ddb_path = self.ma_machine_obj.join_path(self.ma_drive, f"TC_{self.id}", f"DDB_{suffix}")

        self.backupset_name = f"BKPSET_{self.id}_{self.client_name}"
        self.subclient_name = f"SUBC_{self.id}_{self.client_name}"
        self.content_path = self.client_machine_obj.join_path(self.client_drive, f"TC_{self.id}_CONTENT")

    def setup_environment(self):
        """ configures all entities based tcinputs. if subclient or storage policy or library is provided,
        TC will use these entities and run the case """
        self.log.info("setting up environment...")
        # Create pool if pool name is not specified
        if not self.is_user_defined_plan:
            if not self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.log.info(f"Creating Storage Pool - {self.pool_name}")
                self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                                                self.ma_name, [self.ma_name] * 2,
                                                                [self.ddb_path, self.ddb_path])
            else:
                self.log.info(f"Storage Pool already exists - {self.pool_name}")
            # Create Plan if plan name is not specified using the pool name specified in json or pool created
            if not self.commcell.plans.has_plan(self.plan_name):
                self.log.info(f"Creating the Plan [{self.plan_name}]")
                self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
                self.log.info(f"Plan [{self.plan_name}] created")
            else:
                self.log.info(f"Plan already exists - {self.plan_name}")
                self.plan = self.commcell.plans.get(self.plan_name)
        else:
            self.log.info(f"Using User Provided Plan {self.plan_name}")
            self.plan = self.commcell.plans.get(self.plan_name)

        self.primary_copy = self.plan.storage_policy.get_copy('Primary')
        self.plan.schedule_policies['data'].disable()
        # Create a backupset
        self.log.info(f"Configuring Backupset - {self.backupset_name}")
        self.bkpset_obj = self.mmhelper_obj.configure_backupset(self.backupset_name)
        # Create subclient
        self.subclient = self.bkpset_obj.subclients.add(self.subclient_name)
        self.subclient.plan = [self.plan, [self.content_path]]

    def cleanup(self):
        """
        performs cleanup of all entities only if created by case.
        if case is using existing entities, cleanup is skipped.
        """
        try:
            if self.client_machine_obj.check_directory_exists(self.content_path):
                self.log.info(f"Deleting already existing content directory {self.content_path}")
                self.client_machine_obj.remove_directory(self.content_path)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info(f"Deleting backupset {self.backupset_name}")
                self.agent.backupsets.delete(self.backupset_name)
            if not self.existing_entities:
                if self.commcell.plans.has_plan(self.plan_name):
                    self.log.info("Reassociating all subclients to None")
                    self.plan.storage_policy.reassociate_all_subclients()
                    self.log.info(f"Deleting plan {self.plan_name}")
                    self.commcell.plans.delete(self.plan_name)
                if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                    self.log.info(f"Deleting Storage Pool {self.pool_name}")
                    self.commcell.storage_pools.delete(self.pool_name)
                self.log.info("Refresh libraries")
                self.commcell.disk_libraries.refresh()
                self.log.info("Refresh Storage Pools")
                self.commcell.storage_pools.refresh()
                self.log.info("Refresh Plans")
                self.commcell.plans.refresh()
            else:
                self.log.info("Not running cleanup of pools and plans as TC is using existing entities.")
                if self.plan:
                    self.plan.schedule_policies['data'].enable()
        except Exception as e:
            self.log.warning(f"Something went wrong while cleanup! {e}")

    def run_backup(self, backup_type="FULL", size=1.0):
        """
        this function runs backup by generating new content to get unique blocks for dedupe backups.
        if scalefactor is set in tcinput, creates factor times of backup data

        Args:
            backup_type (str): type of backup to run
                Default - FULL

            size (int): size of backup content to generate
                Default - 1 GB

        Returns:
        (object) -- returns job object to backup job
        """
        # add content
        additional_content = self.client_machine_obj.join_path(self.content_path, 'generated_content')
        if self.client_machine_obj.check_directory_exists(additional_content):
            self.client_machine_obj.remove_directory(additional_content)
        # if scale test param is passed in input json, multiply size by scale factor times and generate content
        if self.scale_factor:
            size = size * int(self.scale_factor)
        self.mmhelper_obj.create_uncompressable_data(self.client_name, additional_content, size)

        self.log.info("Running %s backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(backup_type, job.delay_reason)
            )
        self.log.info("Backup job completed.")
        return job

    def get_active_files_store(self):
        """returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.pool_name, 'primary')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

    def run_dv2_job(self, store, dv2_type, option):
        """
        Runs DV2 job with type and option selected and waits for job to complete

        Args:
            store (object) - object of the store to run DV2 job on

            dv2_type (str) - specify type either full or incremental

            option (str) - specify option, either quick or complete

        Returns:
             (object) - completed DV2 job object
        """

        self.log.info("running [%s] [%s] DV2 job on store [%s]...", dv2_type, option, store.store_id)
        if dv2_type == 'incremental' and option == 'quick':
            job = store.run_ddb_verification()
        elif dv2_type == 'incremental' and option == 'complete':
            job = store.run_ddb_verification(quick_verification=False)
        elif dv2_type == 'full' and option == 'quick':
            job = store.run_ddb_verification(incremental_verification=False)
        else:
            job = store.run_ddb_verification(incremental_verification=False, quick_verification=False)
        self.log.info("DV2 job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run dv2 job with error: {job.delay_reason}")
        self.log.info("DV2 job completed.")
        return job

    def validate_dv2(self, store, dv2_job, is_quick_dv2=True, incr_job_list=None, is_incremental=False):
        """
        validates the dv2 job for following:
        1. idxsidbStore table updation with right column based on option
        2. 2 phases for each dv2 job
        3. last verification time on expected jobs for incr type

        Args:
            store (object)          - store object to get dedupe store related details

            dv2_job (object)        - dv2 job object

            incr_job_list (list)    - list of jobs that are expected to be verified by incr DV2
                                    Default: None

            is_quick_dv2 (bool)     - set false if completed DV2 job validation
                                    Default: True

            is_incremental (bool)   - set true if incremental DV2 job. Default: False
                                    Note: need to pass expected jobs in set to true in incr_job_list
        """
        time.sleep(60)
        if incr_job_list is None:
            incr_job_list = []
        if is_quick_dv2:
            # quick dv2 time update
            self.log.info("VALIDATION: is lastQuickDDBVerificationTime updated after Quick dv2 job?")
            query = f"""select 1 from IdxSidbStore S, JMAdminJobStatsTable JM
                    where S.lastQuickDDBVerificationTime = JM.servstart
                    and S.sidbstoreid = {store.store_id} and JM.jobid = {dv2_job.job_id}
                    and S.LastDDBVerificationTime <> JM.servstart"""
            self.log.info("QUERY: %s", query)
            self.csdb.execute(query)
            result = self.csdb.fetch_one_row()
            self.log.info("RESULT: %s", result[0])
            if not result[0]:
                raise Exception("lastQuickDDBVerificationTime is not updated after quick DV2 job")
            self.log.info("lastQuickDDBVerificationTime is updated after Quick dv2 job!")
        else:
            # complete dv2 time update
            self.log.info("VALIDATION: is LastDDBVerificationTime updated after complete dv2 job?")
            query = f"""select 1 from IdxSidbStore S, JMAdminJobStatsTable JM
                                where S.lastQuickDDBVerificationTime <> JM.servstart
                                and S.sidbstoreid = {store.store_id} and JM.jobid = {dv2_job.job_id}
                                and S.LastDDBVerificationTime = JM.servstart"""
            self.log.info("QUERY: %s", query)
            self.csdb.execute(query)
            result = self.csdb.fetch_one_row()
            self.log.info("RESULT: %s", result[0])
            if not result[0]:
                raise Exception("LastDDBVerificationTime is not updated after complete DV2 job")
            self.log.info("LastDDBVerificationTime is updated after complete dv2 job!")

        # validate phase 2 for quick dv2
        self.log.info("VALIDATION: phase 2 for DV2 job")
        query = f"""select count(distinct phasenum) from JMAdminJobAttemptStatsTable where jobid = {dv2_job.job_id}"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", result[0])
        if result[0] == '' or int(result[0]) != 2:
            raise Exception("invalid phase count found for DV2 job")
        self.log.info("DV2 job was run with 2 phases!")

        # validate verification time update on job
        # Note: for incremental dv2, by design, we would have run full before incr. this means, all incr expected jobs
        #       are noted down in case thus only these jobs should be considered for incr verification.
        if is_incremental:
            self.log.info("VALIDATE: only expected jobs should be updated with verified time")
            query = f"""select distinct JMD.jobid from JMJobDataStats JMD, JMAdminJobStatsTable JMA
                    where JMD.archCheckEndTime between JMA.servStart and JMA.servEnd
                        and JMA.jobid = {dv2_job.job_id}"""
            self.log.info("QUERY: %s", query)
            self.csdb.execute(query)
            result = self.csdb.fetch_all_rows()
            self.log.info("RESULT: %s", result[0])
            if not len(incr_job_list) == len(result[0]):
                unexpected_job_list = list(set(result[0]) - set(incr_job_list))
                raise Exception(f"unexpected jobs verified by incr DV2 {unexpected_job_list}")
            self.log.info("only expected jobs are updated with incremental DV2")

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.setup_environment()
            self.run_backup()
            store_obj = self.get_active_files_store()
            quick_dv2 = self.run_dv2_job(store_obj, 'full', 'quick')
            self.validate_dv2(store_obj, quick_dv2)

            job = self.run_backup()
            quick_incr_dv2 = self.run_dv2_job(store_obj, 'incremental', 'quick')
            self.validate_dv2(store_obj, quick_incr_dv2, incr_job_list=[job], is_incremental=True)

            self.run_backup()
            complete_dv2 = self.run_dv2_job(store_obj, 'full', 'complete')
            self.validate_dv2(store_obj, complete_dv2, is_quick_dv2=False)

            job = self.run_backup()
            complete_incr_dv2 = self.run_dv2_job(store_obj, 'incremental', 'complete')
            self.validate_dv2(store_obj, complete_incr_dv2, is_quick_dv2=False, incr_job_list=[job], is_incremental=True)
        except Exception as exp:
            self.log.error(f"Failed to execute test case with error: {exp}")
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED.')
        else:
            self.log.warning('Test Case FAILED.')
        self.cleanup()
