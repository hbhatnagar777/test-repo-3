# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies aging of unwanted checkpoints for indexing feature 'Index pruning'

TestCase:
    __init__()                       --  Initializes the TestCase class

    setup()                          --  All testcase objects are initialized in this method

    run()                            --  Contains the core testcase logic and it is the one executed

    age_jobs()                       --  Age given jobs, run data aging and compaction

    create_checkpoint_and_get_time() --  Checkpoints db and returns (start-time, end-time) for checkpoint

    run_backup_and_checkpoint()      --  Run jobs and checkpoint, append them to respective lists

    attempt_validate()               --  Attempt validation several times

    is_checkpoint_flags_updated()    --  Checks if flags for checkpoints were changed as expected

    is_checkpoints_aged()            --  Checks if checkpoints were changed as expected

"""

import time

from cvpysdk.policies.storage_policies import StoragePolicyCopy

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from Indexing.database import index_db
from Indexing.helpers import IndexingHelpers
from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """This testcase verifies aging of unwanted checkpoints for indexing feature 'Index pruning'"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Pruning - Aging of unwanted checkpoints'

        self.tcinputs = {
            'StoragePolicy': None,
        }

        self.backupset_name = None
        self.subclient_name = None

        self.cl_machine = None
        self.idx_tc = None
        self.idx_helper = None
        self.indexing_level = None
        self.idx_db = None

        self.common_utils = None
        self.storage_policy_copy = None

        self.jobs = []
        self.checkpoints = []
        self.checkpoints_flags = []

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.backupset_name = f'PRUNING_AGING_UNWANTED_CHECKPOINTS'
        self.subclient_name = f'SUBCLIENT_1'

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.idx_helper = IndexingHelpers(self.commcell)

        self.indexing_level = self.idx_helper.get_agent_indexing_level(self.agent)
        if self.indexing_level != 'subclient':
            raise Exception(f'TestCase valid only for subclient level index.')

        self.backupset = self.idx_tc.create_backupset(name=self.backupset_name, for_validation=False)
        self.subclient = self.idx_tc.create_subclient(
            name=self.subclient_name,
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy']
        )

        # Modify index retention criteria
        self.subclient.index_pruning_type = 'cycles_based'
        self.subclient.index_pruning_cycles_retention = 2

        self.common_utils = CommonUtils(self)
        self.storage_policy_copy = StoragePolicyCopy(self.commcell, self.subclient.storage_policy, 'Primary')

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:

                1 - Run backup jobs and checkpoint-compaction twice for checkpoints to appear in App_IndexCheckpointInfo
                2 - Create backup jobs and checkpoints
                3 - Prune Db to change start-time for new checkpoints
                4 - Create backup jobs and checkpoints again
                5 - Age some jobs
                6 - Restart EventManagerService on CommServer
                7 - Wait and verify if flags are updated
                8 - Run data-aging
                9 - Verify if checkpoints are aged

                Scenario covered:
                -----

                1) aged job checkpoint is deleted
                2) redundant checkpoint
                3) retain 3 latest checkpoints

                Cycles to retain by pruning = 2

                full j1
                Initialize pruning

                full j2, full j3, full j4
                checkpoint   ( j1, j2, j3, j4 ) - CP1
                compaction   j1, j2 will be pruned

                full j5
                checkpoint  ( j3, j4, j5 ) - CP2

                full j6
                checkpoint  ( j3, j4, j5, j6 ) - CP3
                compaction  j3, j4 will be pruned

                full j7 inc j8
                checkpoint ( j5, j6, j7, j8 ) - CP4

                sfull j9 inc j10
                checkpoint ( j5, j6, j7, j8, j9, j10 ) - CP5

                sfull j11
                checkpoint ( j5, j6, j7, j8, j9, j10, j11 ) - CP6

                Age j2, j3, j4, j5 manually

                Restart EvMgrS

                Checkpoints expected to be retained:
                CP1, CP4, CP5, CP6

                CP1 is retained because it still contains j1
                CP4, 5, 6 will be retained because it is part of the last 3 latest startTime range

                CP2 will be aged because j3, j4, j5 are manually aged
                CP3 will be aged because j3, j4, j5 are manually aged and j6 is part of CP4

        """

        try:
            self.log.info('********** JOB 1 **********')
            self.idx_tc.run_backup_sequence(self.subclient, ['New', 'Full'])
            self.idx_db = index_db.get(self.subclient)

            self.log.info('********** Initializing dbPrune prop **********')
            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            self.log.info('********** JOB 2, 3, 4 **********')
            self.run_backup_and_checkpoint(['full', 'full', 'full'])  # CP1 + first full

            self.log.info(f'*************** Pruning JOB 1 and JOB 2 ***************')
            self.idx_db.compact_db(registry_keys=True)

            self.log.info('********** JOB 5 **********')
            self.run_backup_and_checkpoint(['full'])  # CP2

            self.log.info('********** JOB 6 **********')
            self.run_backup_and_checkpoint(['full'])  # CP3

            self.log.info(f'*************** Pruning JOB 3 and JOB 4 ***************')
            self.idx_db.compact_db(registry_keys=True)

            self.log.info('********** JOB 7 & INC JOB 8 **********')
            self.run_backup_and_checkpoint(['full', 'edit', 'incremental'])   # CP4

            self.log.info('********** JOB 9 & INC JOB 10 **********')
            self.run_backup_and_checkpoint(['synthetic_full', 'edit', 'incremental'])  # CP5

            self.log.info('********** JOB 11 **********')
            self.run_backup_and_checkpoint(['synthetic_full'])  # CP6

            self.log.info(self.jobs)
            self.log.info(self.checkpoints)

            job_ids = [job.job_id for job in self.jobs]
            to_age_jobs = job_ids[:4]
            self.log.info(f'********** Aging jobs [{to_age_jobs}] **********')
            self.age_jobs(jobs=to_age_jobs)

            # expected result for created checkpoints
            self.checkpoints_flags = [
                1,  # CP1 has jobs 1, 2, 3, 4 = Jobs 2, 3, 4 are aged, but job 1 is active. Will be retained
                0,  # CP3 has jobs 3, 4, 5, 6 = Jobs 3, 4, 5 are aged but job 6 is part of CP4. CP3 is aged.
                1,  # CP4 has jobs 5, 6, 7, 8 = Will be retained as it falls under last 3 checkpoint
                1,  # CP5 has jobs 5, 6, 7, 8, 9, 10 = Will be retained as it falls under last 3 checkpoint
                1,  # CP6 has jobs 5, 6, 7, 8, 9, 10, 11 = Will be retained as it falls under last 3 checkpoint
            ]

            self.log.info('******** Checkpoints available ********')
            self.log.info(self.checkpoints)
            # CP2 has jobs 3,4,5. CP2 will be aged immediately along with these jobs.
            deleted_checkpoint = self.checkpoints.pop(1)
            self.log.info('%s checkpoint is aged along with the job consisting it', deleted_checkpoint)
            self.log.info('Removing %s checkpoint from the list', deleted_checkpoint)

            self.log.info('******** Expected results for checkpoints ********')
            self.log.info(self.checkpoints_flags)

            self.log.info('*************** Restart event manager service to update checkpoint flags ***************')
            service_name = f'GxEvMgrS({self.commcell.commserv_client.instance})'
            self.commcell.commserv_client.restart_service(service_name=service_name)

            self.attempt_validate(
                description='Wait for checkpoint flags to update',
                total_attempts=3,
                wait_time_seconds=300,
                validate_method=self.is_checkpoint_flags_updated,
            )
            self.log.info('************** Checkpoints flags updated successfully. **************')

            self.log.info('********** Run Data-Aging forcefully **********')
            if not self.commcell.run_data_aging().wait_for_completion():
                raise Exception('Data aging failed.')

            self.attempt_validate(
                description='Wait for checkpoints to age.',
                total_attempts=3,
                wait_time_seconds=60,
                validate_method=self.is_checkpoints_aged,
            )
            self.log.info('************** Checkpoints aged successfully. **************')

            self.log.info('******************* SUCCESS, checkpoints were aged as expected. *******************')

        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)
            self.result_string = str(e)
            self.status = constants.FAILED
            self.log.exception(e)

    def age_jobs(self, jobs):
        """Age given jobs, run data aging and compaction

            Args:
                jobs (list) -- List of integer job-ids

            Raises:
                Exception:
                    If data-aging or compaction fails

        """

        for job_id in jobs:
            self.log.info(f'Aging job: {job_id}')
            self.storage_policy_copy.delete_job(job_id=str(job_id))

        self.common_utils.data_aging(self.storage_policy_copy.storage_policy, 'Primary')

        if not self.idx_db.compact_db(registry_keys=True):
            raise Exception('Compact index failed.')

    def create_checkpoint_and_get_time(self):
        """Checkpoints db and returns (start-time, end-time) for checkpoint

            Returns:
                tuple - Tuple of integers (start-time, end-time)

        """

        self.log.info('***** Running checkpoint job *****')
        if not self.idx_db.checkpoint_db(by_all_index_backup_clients=False, registry_keys=True):
            raise Exception('Checkpoint index failed.')

        checkpoint = self.idx_db.get_index_db_checkpoints()[-1]
        return int(checkpoint['startTime']), int(checkpoint['endTime'])

    def run_backup_and_checkpoint(self, steps):
        """Run jobs and checkpoint, append them to respective lists"""

        jobs = self.idx_tc.run_backup_sequence(subclient_obj=self.subclient, steps=steps)

        self.log.info(f'***** Running checkpoint job #{len(self.checkpoints)+1}')
        checkpoint = self.create_checkpoint_and_get_time()

        self.log.info(f'Adding jobs [{jobs}] to list')
        self.jobs.extend(jobs)

        self.log.info(f'Adding checkpoint [{checkpoint}] to list')
        self.checkpoints.append(checkpoint)

    def attempt_validate(self, description, total_attempts, wait_time_seconds, validate_method):
        """Run validation given number of times

            Args:
                description (str) -- describe what validate_method is doing
                total_attempts (int) -- number of times to run validate_method
                wait_time_seconds (int) -- waiting time between consecutive attempts
                validate_method: (function) -- function that performs validation

        """

        self.log.info(f'*************************** {description} ***************************')
        for attempt_number in range(1, total_attempts + 1):
            self.log.info(f'Waiting {wait_time_seconds} seconds before attempt {attempt_number}/{total_attempts}')
            time.sleep(wait_time_seconds)
            if validate_method(get_result=attempt_number != total_attempts):
                break

    def is_checkpoint_flags_updated(self, get_result=False):
        """Checks if flags for checkpoints were changed as expected

            Args:
                get_result (bool) -- True to return bool, False to raise exception

            Returns:
                bool - True if validation Fails

            Raises:
                Exception:
                    If validation fails
        """

        checkpoints = self.idx_db.get_index_db_checkpoints()
        self.log.info(checkpoints)

        checkpoint_dict = {}
        for checkpoint in checkpoints:
            key = (int(checkpoint['startTime']), int(checkpoint['endTime']))
            checkpoint_dict[key] = checkpoint_dict.get(key, 0) or int(checkpoint['flags'])

        self.log.info('********** Checkpoint flags retrieved from CommServDb **********')
        self.log.info(checkpoint_dict)

        for i, key in enumerate(self.checkpoints, 0):
            if key not in checkpoint_dict:
                raise Exception(f'Checkpoint {key} does not exist.')

            if self.checkpoints_flags[i] != checkpoint_dict[key]:
                if get_result:
                    return False
                else:
                    raise Exception(
                        f"Flags not updated for checkpoint: {key}, "
                        f"expected: {self.checkpoints_flags[i]}, found {checkpoint_dict[key]}")

        return True

    def is_checkpoints_aged(self, get_result=False):
        """Checks if checkpoints were changed as expected

            Args:
                get_result (bool) -- True to return bool, False to raise exception

            Returns:
                bool - True if validation Fails

            Raises:
                Exception:
                    If validation fails

        """

        checkpoints = self.idx_db.get_index_db_checkpoints()
        checkpoint_set = set([(int(checkpoint['startTime']), int(checkpoint['endTime'])) for checkpoint in checkpoints])

        self.log.info('********** Checkpoints retrieved from CommServDb **********')
        self.log.info(checkpoint_set)

        for i, key in enumerate(self.checkpoints, 0):
            not_aged = int(key in checkpoint_set)
            if self.checkpoints_flags[i] != not_aged:
                if get_result:
                    return False
                else:
                    raise Exception(f'Unexpected results for Checkpoint {key}, '
                                    f'expected: {self.checkpoints_flags[i]}, found: {not_aged}')

        return True
