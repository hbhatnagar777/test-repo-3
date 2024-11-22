# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

 This testcase verifies copy level aging of checkpoints for subclient level Index

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    divide_jobs_into_cycles()                   --  divides the jobs into lists of job cycles

    get_jobids_on_copy()                        --  gets all job ids of the jobs present in the specified copy

    get_checkpoints_for_the_db()                --  gets all checkpoint jobids for the DB

"""

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Indexing.database import index_db
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies copy level aging of checkpoints for subclient level Index

        Steps:

            1. Have a storage policy with 2 copies
            2. Check if primary copy retention is set to 0 days, 2 cycles, if not set it
            3. Check if secondary copy retention is set to 0 days, 4 cycles, if not set it
            4. Run 2 cycles of jobs
            5. Prune the DB ( run both checkpoint and compaction)
            CP1 has cycles 1,2
            6. Run aux copy job
            7. Run 2 more cycles of jobs
            8. Prune the DB ( run both checkpoint and compaction)
            CP2 has cycles 1,2,3,4
            9. Run aux copy job
            10. Run data aging job
            11. Verify that from primary copy, first two cycles jobs along with CP1 job are aged
            12. Verify that from secondary, all cycles jobs with both CP1 and CP2 index backups jobs
            are retained

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing -  Copy level aging of checkpoints for subclient level index'
        self.tcinputs = {
            'StoragePolicy': None,

        }
        self.storage_policy = None
        self.jobs = None
        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.indexing_level = None
        self.idx_db = None
        self.cycles_list = None
        self.number_of_copies = None
        self.primary_copy = None
        self.secondary_copy = None
        self.checkpoint_jobs = {}

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))

        self.number_of_copies = len(self.storage_policy.copies)
        self.primary_copy = self.storage_policy.get_primary_copy()

        if self.number_of_copies >= 2:
            self.log.info('Number of copies in the storage policy: %s is %s',
                          self.storage_policy.name, self.number_of_copies)
            self.secondary_copy = self.storage_policy.get_secondary_copies()[0]
        else:
            raise Exception('The storage policy has only one copy')

        primary_copy_retention = self.primary_copy.copy_retention
        secondary_copy_retention = self.secondary_copy.copy_retention

        if primary_copy_retention['days'] != 0 or primary_copy_retention['cycles'] != 2:
            self.primary_copy.copy_retention = (0, 2, -1, 0)
        if secondary_copy_retention['days'] != 0 or secondary_copy_retention['cycles'] != 4:
            self.secondary_copy.copy_retention = (0, 4, -1, 0)

        self.log.info('Copy retention for primary copy is %s', self.primary_copy.copy_retention)
        self.log.info('Copy retention for secondary copy is %s', self.secondary_copy.copy_retention)

        self.backupset = self.idx_tc.create_backupset('63182_checkpoint_aging_at_copylvl', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='checkpoint_aging_at_copylvl_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            register_idx=True
        )

        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        if not self.indexing_level == 'subclient':
            raise Exception('This testcase is specific to subclient level index')

        self.subclient.index_pruning_type = 'cycles_based'
        self.subclient.index_pruning_cycles_retention = 2

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:
            self.log.info('Running 2 cycles of jobs')
            self.jobs = self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'Full'],
                verify_backup=True
            )

            self.idx_db = index_db.get(self.subclient)

            self.log.info('Running index backup job to checkpoint the DB')
            if not self.idx_db.checkpoint_db(by_all_index_backup_clients=False, registry_keys=True):
                raise Exception('Failed to checkpoint the DB')

            # CP1 has Full1, Full2

            aux_copy_job1 = self.storage_policy.run_aux_copy(storage_policy_copy_name=self.secondary_copy.copy_name)
            self.log.info(f"Aux copy job started, waiting for the job completion. Job ID: {aux_copy_job1.job_id}")
            if not aux_copy_job1.wait_for_completion():
                raise Exception(f"Failed to run aux copy job with error: {aux_copy_job1.delay_reason}")
            self.log.info("Aux copy job completed.")

            self.log.info('Running 2 cycles of jobs')
            self.jobs.extend(self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['Full', 'Full'],
                verify_backup=True
            ))

            self.log.info('Running index backup job to checkpoint the DB')
            if not self.idx_db.checkpoint_db(by_all_index_backup_clients=False, registry_keys=True):
                raise Exception('Failed to checkpoint the DB')

            # CP2 had Full1, Full2, Full3, Full4

            aux_copy_job2 = self.storage_policy.run_aux_copy(storage_policy_copy_name=self.secondary_copy.copy_name)
            self.log.info(f"Aux copy job started, waiting for the job completion. Job ID: {aux_copy_job2.job_id}")
            if not aux_copy_job2.wait_for_completion():
                raise Exception(f"Failed to run aux copy job with error: {aux_copy_job2.delay_reason}")
            self.log.info("Aux copy job completed.")

            self.checkpoint_jobs = self.get_checkpoints_for_the_db()
            self.log.info('The checkpoint jobs are %s', self.checkpoint_jobs)

            jobs_on_primary_before_da = self.get_jobids_on_copy(self.primary_copy)
            jobs_on_secondary_before_da = self.get_jobids_on_copy(self.secondary_copy)
            self.log.info('Backup jobs on primary copy before data aging are %s', jobs_on_primary_before_da)
            self.log.info('Backup jobs on secondary copy before data aging are %s', jobs_on_secondary_before_da)

            self.cycles_list = self.divide_jobs_into_cycles()
            self.cycles_list.reverse()
            self.log.info('The jobs per cycle list is %s', self.cycles_list)

            self.log.info('Running data aging job')

            da_job = self.commcell.run_data_aging(storage_policy_name=self.storage_policy.name,
                                                  is_granular=True,
                                                  include_all_clients=True)

            self.log.info("data aging job: %s", da_job.job_id)
            if not da_job.wait_for_completion():
                raise Exception(f"Failed to run data aging with error: {da_job.delay_reason}")
            self.log.info("Data aging job completed.")

            jobs_on_primary_after_da = self.get_jobids_on_copy(self.primary_copy)
            jobs_on_secondary_after_da = self.get_jobids_on_copy(self.secondary_copy)
            self.log.info('Backup jobs on primary copy after data aging are %s', jobs_on_primary_after_da)
            self.log.info('Backup jobs on secondary copy after data aging are %s', jobs_on_secondary_after_da)

            self.log.info('Verify if cycle 1 and 2 along with CP1 jobs are aged from primary copy')

            expected_aged_jobs = self.cycles_list[0]+self.cycles_list[1]
            expected_aged_checkpoint = self.checkpoint_jobs.get('CP1')

            for exp_job in expected_aged_jobs:
                if exp_job not in jobs_on_primary_after_da.get('data_backup'):
                    self.log.info('Excepted job with jobid : %s, got aged', exp_job)
                else:
                    raise Exception('Excepted job with jobid : %s, did not get aged', exp_job)

            if expected_aged_checkpoint not in jobs_on_primary_after_da.get('index_backup'):
                self.log.info('Excepted checkpoint CP1 with jobid : %s, got aged', expected_aged_checkpoint)
            else:
                raise Exception('Excepted checkpoint CP1 with jobid : %s, did not get aged', expected_aged_checkpoint)

            self.log.info('Verify if all cycle jobs along with CP1 and CP2 jobs are retained on secondary copy')

            if jobs_on_secondary_after_da == jobs_on_secondary_before_da:
                self.log.info('All 4 cycles jobs and both checkpoints on secondary copy are retained')
            else:
                job_list_before_da = (jobs_on_secondary_before_da.get('data_backup') +
                                      jobs_on_secondary_before_da.get('index_backup'))
                job_list_after_da = (jobs_on_secondary_after_da.get('data_backup') +
                                     jobs_on_secondary_after_da.get('index_backup'))
                job_diff = [job for job in job_list_before_da if job not in set(job_list_after_da)]
                self.log.error('Jobs wrongly got aged after da from secondary copy, they are %s', job_diff)
                raise Exception('Expected jobs and actual jobs on the secondary copy are not same')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def divide_jobs_into_cycles(self):
        """ Divides the jobs into lists of job cycles

                    returns:
                          list()   -- List of lists of job cycles
        """
        self.log.info('Putting the jobs of each cycle into sub lists from the list of all jobs that ran')
        list_of_cycles = []
        temp_cycle = []
        for job in self.jobs[::-1]:
            if job.backup_level == 'Synthetic Full' or job.backup_level == 'Full':
                temp_cycle.insert(0, job.job_id)
                list_of_cycles.append(temp_cycle)
                temp_cycle = []
            elif job.backup_level == 'Incremental':
                temp_cycle.insert(0, job.job_id)

        return list_of_cycles

    def get_jobids_on_copy(self, copy):
        """ Gets all job ids of the jobs present in the specified copy

                    Args:
                        copy (obj) - storage policy copy object to get the jobs from

                    returns:
                          list()   -- List job ids
        """

        copy_backup_job_ids = []
        copy_index_backup_job_ids = []
        for job_details in copy.get_jobs_on_copy():
            if job_details.get('@SubClient') == self.subclient.name:
                copy_backup_job_ids.append(job_details.get('@JobID'))

        self.csdb.execute("""select jobId from archFileCopy afc, archfile af where afc.archfileid = af.id and 
        af.name like '%{0}%' and afc.archcopyid = {1}""".format(self.idx_db.db_guid, copy.get_copy_id()))

        checkpoint_jobs_on_copy = self.csdb.fetch_all_rows(named_columns=True)
        for job in checkpoint_jobs_on_copy:
            copy_index_backup_job_ids.append(job.get('jobId'))

        copy_job_ids = {'data_backup': copy_backup_job_ids, 'index_backup': copy_index_backup_job_ids}
        return copy_job_ids

    def get_checkpoints_for_the_db(self):
        """ Gets all checkpoint jobids for the DB

                    returns:
                          dict()   -- Mapping of the checkpoint and their index job id
        """

        self.log.info('Executing query')

        self.csdb.execute("""
                    select jobid from archFile
                    left join App_IndexCheckpointInfo ici on ici.afileId = archfile.id
                    where name like '%{0}%'
                    order by archFile.id asc
                """.format(self.idx_db.db_guid))

        jobids_list = self.csdb.fetch_all_rows(named_columns=True)
        if jobids_list:
            checkpoint_jobs = {'CP1': jobids_list[0].get('jobid'), 'CP2': jobids_list[1].get('jobid')}
        else:
            raise Exception('No checkpoints found for DB')

        return checkpoint_jobs
