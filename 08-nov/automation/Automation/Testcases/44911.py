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

    cleanup()       --  cleanup the entities created in this/previous runs

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    run_validations()    --  runs the validations

    run_tape_validations() -- runs tape validations to check for multiplexing

Sample JSON:
    "44911": {
        "ClientName": "Name of Client",
        "PrimaryCopyMediaAgent": "Name of Source MA",
        "SecondaryCopyMediaAgent": "Name of Destination MA",
        "AgentName": "File System",
        "tapeLibraryName": "Name of the Tape Library",
        "LibraryControllerMA": "MA which Controls Library",
        "DriveControllerMA": "MA which controls Drives"
            }
    Note: Both the MediaAgents can be the same machine
    Configuration Note :

    The tape library should be as following
        Library Controller : MA1
        Drive Controller : MA1

Steps:

1: Configure the environment: create a pool, plan-with Primary, Secondary Copy,
                              (DSA disabled for the Policy), a BackupSet,a SubClient

2: Run a Backup Job and then an AuxCopy Job

3: Run DB Validations whether DSA is disabled? and is DSA not working?

4: Enable DSA, Create a new Secondary Copy and run AuxCopy again

5: Run DB Validations whether DSA is enabled? and is DSA working?

6: CleanUp the environment

"""
import time

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = 'AuxCopy Without DSA and Tape Copy.'
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None
        }
        self.mm_helper = None
        self.ma_machine_1 = None
        self.ma_machine_2 = None
        self.dedupe_helper = None
        self.client_machine = None
        self.ma_1_path = None
        self.ma_2_path = None
        self.mount_path = None
        self.client_path = None
        self.mount_path_2 = None
        self.dedup_path = None
        self.dedup_path_2 = None
        self.dedup_path_3 = None
        self.dedup_path_4 = None
        self.content_path = None
        self.subclient = None
        self.backupset = None
        self.tape_copy = None
        self.tape_copy_name = None
        self.copy_name = None
        self.copy = None
        self.pool_name = None
        self.pool_name_2 = None
        self.plan = None
        self.subclient_name = None
        self.backupset_name = None
        self.plan_name = None
        self.tape_library_name = None
        self.tape_library_id = None
        self.tape_library = None
        self.secondary_copy_name = None
        self.library_controller_ma = None
        self.library_controller_obj = None
        self.drive_controller_ma = None
        self.drive_controller_obj = None

    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.ma_machine_1 = Machine(self.tcinputs['PrimaryCopyMediaAgent'], self.commcell)
        self.ma_machine_2 = Machine(self.tcinputs['SecondaryCopyMediaAgent'], self.commcell)
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

        self.client_machine, self.client_path = self.mm_helper.generate_automation_path(self.client.client_name, 25*1024)
        self.ma_machine_1, self.ma_1_path = self.mm_helper.generate_automation_path(self.tcinputs['PrimaryCopyMediaAgent'], 25*1024)
        self.ma_machine_2, self.ma_2_path = self.mm_helper.generate_automation_path(self.tcinputs['SecondaryCopyMediaAgent'], 25*1024)
        self.mount_path = self.ma_machine_1.join_path(self.ma_1_path, 'MP')
        self.mount_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'MP2')
        self.dedup_path = self.ma_machine_1.join_path(self.ma_1_path, 'Dedup')
        self.dedup_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'Dedup2')
        self.dedup_path_3 = self.ma_machine_1.join_path(self.ma_1_path, "Dedup3")
        self.dedup_path_4 = self.ma_machine_2.join_path(self.ma_2_path, 'Dedup4')
        self.content_path = self.client_machine.join_path(self.client_path, 'Content')
        self.tape_copy_name = str(self.id) + '_Tape_Copy'
        self.copy_name = str(self.id) + '_Copy'
        self.pool_name = str(self.id) + '_Pool'
        self.pool_name_2 = self.pool_name + '_2'
        self.backupset_name = str(self.id) + '_BS'
        self.subclient_name = str(self.id) + '_SC'
        self.plan_name = str(self.id) + '_Plan'
        self.secondary_copy_name = str(self.id) + '_Copy2'
        self.tape_library_name = self.tcinputs['tapeLibraryName']
        self.library_controller_ma = self.tcinputs["LibraryControllerMA"]
        self.drive_controller_ma = self.tcinputs["DriveControllerMA"]
        self.library_controller_obj = self.commcell.media_agents.get(self.library_controller_ma)
        self.drive_controller_obj = self.commcell.media_agents.get(self.drive_controller_ma)

    def cleanup(self):
        """Cleanup the entities created in this/previous Runs"""
        try:
            self.log.info("****************************** Cleanup Started ******************************")
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.backupset = self.agent.backupsets.get(self.backupset_name)
                self.subclient = self.backupset.subclients.get(self.subclient_name)
                if self.backupset.subclients.has_subclient(self.subclient_name):
                    self.subclient.plan = None
                self.log.info(f"Deleting backupset {self.backupset_name}")
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info(f"Deleting plan  {self.plan_name}")
                self.commcell.plans.delete(self.plan_name)

            if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.log.info(f"Deleting pool  {self.pool_name}")
                self.commcell.storage_pools.delete(self.pool_name)

            if self.commcell.storage_pools.has_storage_pool(self.pool_name_2):
                self.log.info(f"Deleting pool  {self.pool_name_2}")
                self.commcell.storage_pools.delete(self.pool_name_2)

            if self.commcell.storage_pools.has_storage_pool(self.tape_library_name):
                self.log.info(f"Deleting the tape pool")
                self.commcell.storage_pools.delete(self.tape_library_name)

            if self.commcell.tape_libraries.has_library(self.tape_library_name):
                self.log.info(f"Deleting the tape library")
                self.commcell.tape_libraries.delete(self.tape_library_name)


            # Run DataAging
            data_aging_job = self.commcell.run_data_aging()
            self.log.info(f"Data Aging job [{data_aging_job.job_id}] has started.")
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    f"Data Aging job [{data_aging_job.job_id}] has failed with {data_aging_job.delay_reason}.")
                raise Exception(f'Data Aging job {data_aging_job.job_id} Failed Reason: {data_aging_job.delay_reason}')
            self.log.info(f"Data Aging job [{data_aging_job.job_id}] has completed.")
            self.log.info('****************************** Cleanup Completed ******************************')
        except Exception as exe:
            self.log.error(f'************ERROR in Cleanup. Might need to Clean Manually: {exe}')

    def run(self):
        """Run Function of this case"""
        try:
            self.log.info("Cleaning up the entities from older runs")
            self.cleanup()

            self.configure_tape_library()

            # 1: Configure the environment
            self.mm_helper.create_uncompressable_data(self.client.client_name,
                                                      self.content_path, 4)

            self.tape_library = self.commcell.tape_libraries.get(self.tape_library_name)
            self.tape_library_id = self.tape_library.library_id

            # CREATE STORAGE POOLS
            self.log.info(f"Creating the pool [{self.pool_name}]")
            self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                            self.tcinputs['PrimaryCopyMediaAgent'],
                                            [self.tcinputs['PrimaryCopyMediaAgent'], self.tcinputs['PrimaryCopyMediaAgent']],
                                            [self.dedup_path, self.dedup_path_3])
            self.log.info(f"Pool [{self.pool_name}] Created.")

            self.log.info(f"Creating the pool [{self.pool_name_2}]")
            self.commcell.storage_pools.add(self.pool_name_2, self.mount_path_2,
                                            self.tcinputs['SecondaryCopyMediaAgent'],
                                            [self.tcinputs['SecondaryCopyMediaAgent']] * 2,
                                            [self.dedup_path_2, self.dedup_path_4])
            self.log.info(f"Pool [{self.pool_name_2}] Created.")

            self.commcell.storage_pools.refresh()
            self.commcell.plans.refresh()

            # Create Plan with 50 Streams. By default it is 50
            self.log.info(f"Plan Present: {self.commcell.plans.has_plan(self.plan_name)}")
            self.log.info(f"Creating the Plan [{self.plan_name}]")
            self.commcell.plans.refresh()
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
            self.log.info(f"Plan [{self.plan_name}] created")

            # Disabling the DSA
            self.log.info('Disabling DSA for StoragePolicy')
            self.plan.storage_policy.modify_dynamic_stream_allocation(False)

            # disabling the schedule policy
            self.log.info('Disabling the schedule policy')
            self.plan.schedule_policies['data'].disable()

            # ADDING A STORAGE COPY TO THE PLAN
            self.log.info(f"Adding the secondary copy [{self.copy_name}]")
            self.plan.add_storage_copy(self.copy_name, self.pool_name_2)
            self.log.info(f"secondary copy [{self.copy_name}] added.")

            # remove association for storage_policy with system created auto copy schedule
            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.copy_name)

            # add backupset
            self.log.info(f"Adding the backup set [{self.backupset_name}]")
            self.backupset = self.mm_helper.configure_backupset(self.backupset_name)
            self.log.info(f"Backup set Added [{self.backupset_name}]")

            # add subclient
            self.log.info(f"Adding the subclient set [{self.subclient_name}]")
            self.subclient = self.backupset.subclients.add(self.subclient_name)
            self.log.info(f"Subclient set Added [{self.subclient_name}]")

            # Add plan and content to the subclient
            self.log.info("Adding plan to subclient")
            self.subclient.plan = [self.plan, [self.content_path]]

            # 2: Run a Backup Job and then an AuxCopy Job
            self.log.info('Running Backup Job')
            backup_job = self.subclient.backup(backup_level='Full')
            if not backup_job.wait_for_completion():
                raise Exception(f'Backup Job {backup_job.job_id} Failed with JPR: {backup_job.delay_reason}')
            self.log.info(f'Backup Job Completed: {backup_job.job_id}')
            time.sleep(60)


            self.log.info('Running AuxCopy Job')
            aux_copy_job = self.plan.storage_policy.run_aux_copy(use_scale=False)
            if not aux_copy_job.wait_for_completion():
                raise Exception(f'AuxCopy Job {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')
            self.log.info(f'AuxCopy Job Completed: {aux_copy_job.job_id}', aux_copy_job.job_id)

            # 3: Run DB Validations whether DSA is disabled? and is DSA not working?
            self.run_validations(1, aux_copy_job.job_id)

            # 4: Enable DSA, Create a new Secondary Copy and run AuxCopy again
            # Enabling DSA for the Storage Policy
            self.log.info('Enabling DSA for StoragePolicy')
            self.plan.storage_policy.modify_dynamic_stream_allocation(True)

            if self.plan.storage_policy.has_copy(self.copy_name):
                self.plan.storage_policy.delete_secondary_copy(self.copy_name)

            self.log.info('Creating Second SP copy for old Aux with DSA Case')
            self.plan.add_storage_copy(self.secondary_copy_name, self.pool_name_2)
            self.log.info(f"secondary copy [{self.secondary_copy_name}] added.")

            # remove association for storage_policy with system created auto copy schedule
            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name,
                                                    self.secondary_copy_name)

            self.log.info('Running AuxCopy Job')
            aux_copy_job = self.plan.storage_policy.run_aux_copy(use_scale=False)
            if not aux_copy_job.wait_for_completion():
                raise Exception(f'AuxCopy Job {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')
            self.log.info(f'AuxCopy Job Completed: {aux_copy_job.job_id}')

            # 5: Run DB Validations whether DSA is enabled? and is DSA working?
            self.run_validations(2, aux_copy_job.job_id)

            # ADDING A TAPE STORAGE COPY TO THE PLAN
            self.log.info(f"Adding the tape copy [{self.tape_copy_name}]")
            self.plan.storage_policy.create_secondary_copy(copy_name=self.tape_copy_name, library_name=self.tape_library_name,
                                                           tape_library_id=self.tape_library_id, media_agent_name=self.tcinputs['DriveControllerMA'])
            self.log.info(f"Tape Copy [{self.copy_name}] added.")

            self.log.info('Running AuxCopy Job on Tape Copy')
            aux_copy_job = self.plan.storage_policy.run_aux_copy(storage_policy_copy_name=self.tape_copy_name, media_agent=self.tcinputs['DriveControllerMA'], use_scale=False)
            if not aux_copy_job.wait_for_completion():
                raise Exception(f'Tape AuxCopy Job {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')
            self.log.info(f'AuxCopy Job on Tape Completed: {aux_copy_job.job_id}', aux_copy_job.job_id)

            self.tape_copy = self.plan.storage_policy.get_copy(self.tape_copy_name)
            secondary_copy_id = self.tape_copy.get_copy_id()
            self.run_tape_validations(backup_job.job_id, secondary_copy_id)

        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error(f'TC Failed. Exception {exe}')

    def configure_tape_library(self):
        self.log.info("Detecting and configuring tape library")
        ma_list_to_pass = []
        ma_list_to_pass.append(int(self.library_controller_obj.media_agent_id))
        ma_list_to_pass.append(int(self.drive_controller_obj.media_agent_id))

        self.tape_lib_obj = self.commcell.tape_libraries.configure_tape_library(self.tape_library_name, ma_list_to_pass)
        self.tape_library_name = self.tape_lib_obj.library_name
        self.log.info(f"Library configured successfully. Tape Library Name : [{self.tape_lib_obj.library_name}]")

    def run_validations(self, case_number, job_id):
        """Runs The Validations
            Args:

                case_number             (int)  --   1- DSA Disabled
                                                    2- DSA Enabled

                job_id                  (str)  --   Id of AuxCopy Job
            """
        self.log.info('****************************** Validations ******************************')

        to_check = ['Disabled', 'Enabled']
        self.log.info(f'**** Validation 1 : DSA {to_check[case_number - 1]} ****')
        query = """select flags & 131072
                from archGroup where name = '{0}'""".format(self.plan.storage_policy.storage_policy_name)
        self.log.info(f'QUERY: {query}', query)
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info(f'Result: {row}')
        if int(row[0]) == 0:
            flag = 'Disabled'
        else:
            flag = 'Enabled'
        if case_number == 1 and flag == 'Disabled':
            self.log.info(f'Validation Success - DSA {flag}')
        elif case_number == 2 and flag == 'Enabled':
            self.log.info(f'Validation Success - DSA {flag}')
        else:
            self.log.error(f'Validation Failed - DSA {flag}')
            self.status = constants.FAILED

        to_check = ['<>0', '=0']
        self.log.info(f'**** Validation 2 : No Entries with Segment Id{to_check[case_number - 1]} ****')
        query = """select count(*) from archchunktocopyDSA
                where AdminJobId = {0} and segmentID{1}
                """.format(job_id, to_check[case_number - 1])
        self.log.info(f'QUERY: {query}')
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info(f'Result: {row}')
        if int(row[0]) == 0:
            self.log.info(f'Validation Passed : No entries with SegmentId{to_check[case_number - 1]}')
        else:
            self.log.error(f'Validation Failed : Populated entries with SegmentId{to_check[case_number - 1]}',)
            self.status = constants.FAILED
        self.log.info("****************************** Validations Complete ******************************")

    def run_tape_validations(self, job_id, secondary_copy_id):
        """Runs The Validations
            Args:

                job_id                  (str)  --   Id of AuxCopy Job

                secondary_copy_id       (str)  --   Id of the tape_copy
            """
        self.log.info('****************************** Validations ******************************')

        self.log.info('Validation: Check Multiplexing Occurred or not.')

        self.log.info('Getting chunk to archFile Mapping Count')
        query = """select DISTINCT count(*)
                    from archChunkMapping acm
                    INNER JOIN archFile af on af.id = acm.archFileId
                    where acm.archCopyId={0} and af.jobId = {1}""".format(secondary_copy_id, job_id)
        self.log.info(f'QUERY: {query}')
        self.csdb.execute(query)
        chunkToArchFileMapping = self.csdb.fetch_one_row()
        self.log.info(f'Result: {chunkToArchFileMapping}')
        self.log.info("Got Chunk to archFile Mapping Count")

        self.log.info('Getting chunk to archFile Mapping Count')
        query = """select count( DISTINCT acm.archChunkId)
                    from archChunkMapping acm
                    INNER JOIN archFile af on af.id = acm.archFileId
                    where acm.archCopyId={0} and af.jobId = {1}""".format(secondary_copy_id, job_id)
        self.log.info(f'QUERY: {query}')
        self.csdb.execute(query)
        chunks = self.csdb.fetch_one_row()
        self.log.info(f'Result: {chunks}')
        self.log.info("Got Chunk to archFile Mapping Count")

        if chunks < chunkToArchFileMapping:
            self.log.info("Multiplexing Occurred")
        else:
            raise Exception("Multiplexing Not Occurred.")

        self.log.info("****************************** Validations Complete ******************************")

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 6: CleanUp the environment
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
