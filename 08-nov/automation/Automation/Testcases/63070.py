# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

 This Testcase verifies if upon having create new index setting, new index is created with every full/sfull

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    get_new_db()                                --  gets the index DB object for the index of each cycle

    verify_jobs_in_index()                      --  verifies if all the jobs of the cycle are present in cycle's index

    divide_jobs_into_cycles()                   --  divides the jobs into lists of job cycles

    get_and_verify_index()                      -- creates DB object for point in time DB and verifies
                                                   if expected jobs are present in the DB

    verify_index_post_browse()                  -- verifies after the browse from each cycle that no job from that cycle got played back into the main DB
                                                   or into a newly created temp DB

"""

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Indexing.database import index_db
from Indexing.database.ctree import CTreeDB
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This Testcase verifies if upon having create new index setting, new index is created with every full/sfull

        Steps:
            1. Enable the create new index option in the commcell settings
            2. Run 3 cycles of jobs
            3. Verify that with each full/sfull, new index is being created with the latest cycle
            4. Verify that the index of each cycle has all the jobs of that cycle
            5. Verify job based browse for each cycle.

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - Create New Index - Acceptance'
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
        self.is_name = None
        self.is_machine = None
        self.idx_db = None
        self.indexes_list = None
        self.cycles_list = None

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))

        self.backupset = self.idx_tc.create_backupset('63070_create_newidx_accp_bkpst', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='create_newidx_accp_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            register_idx=True
        )

        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        if not self.indexing_level == 'subclient':
            raise Exception('This testcase is specific to subclient level index')

        self.subclient.index_pruning_type = 'cycles_based'
        self.subclient.index_pruning_cycles_retention = 1

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:
            self.log.info('Running 3 cycles of jobs')
            self.jobs = self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'Edit', 'Incremental', 'Synthetic_full',
                       'Edit', 'Incremental', 'Synthetic_full', 'Edit', 'Incremental'],
                verify_backup=True
            )

            self.idx_db = index_db.get(self.subclient)
            self.is_name = self.idx_db.index_server
            index_server = self.is_name.client_name
            self.log.info('The Current Index Server is %s', index_server)
            self.log.info('Connecting to Index Server Machine: %s', index_server)

            self.is_machine = self.idx_db.isc_machine
            self.indexes_list = self.is_machine.get_folders_in_path(
                folder_path=self.idx_db.backupset_path,
                recurse=False
            )
            self.log.info('The indexes in the index cache for the subclient are %s', self.indexes_list)

            self.cycles_list = self.divide_jobs_into_cycles()
            self.cycles_list.reverse()
            self.log.info('The list of jobs divided into different cycles is %s', self.cycles_list)

            self.log.info('******** Verifying that the index for cycle 1 jobs is present **********')
            self.get_and_verify_index(job_cycle=1)

            self.log.info('********** Verifying that the index for cycle 2 jobs is present ***********')
            self.get_and_verify_index(job_cycle=2)

            self.log.info('************ Verifying that the index for cycle 3/latest cycle jobs is present ************')
            self.get_and_verify_index(job_cycle=3, is_latest_cycle=True)

            self.log.info('Verify find from first cycle job')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'job_id': self.cycles_list[0][0].job_id,
                'show_deleted': True,
                'restore': {
                    'do': True
                }
            })
            self.verify_index_post_browse()

            self.log.info('Verify find from second cycle job')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'job_id': self.cycles_list[1][1].job_id,
                'show_deleted': True,
                'restore': {
                    'do': True
                }
            })
            self.verify_index_post_browse()

            self.log.info('Verify find from third cycle job')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'job_id': self.cycles_list[2][1].job_id,
                'show_deleted': True,
                'restore': {
                    'do': True
                }
            })
            self.verify_index_post_browse()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def get_new_db(self, job):
        """ Gets the index DB object for the index of each cycle

                Args:
                     job (obj) -- Starting job of the referring cycle

                returns:
                    (obj)  -- DB object for the index of the referring cycle

        """

        subclient_guid = None
        job_start_time = str(job.start_timestamp)
        self.log.info('Checking if a separate index with the job id :%s and job start time: %s '
                      'is created/exists', job.job_id, job_start_time)
        for each_index in self.indexes_list:
            db_folder_name = each_index.split('\\')[-1]
            if job_start_time in db_folder_name:
                subclient_guid = db_folder_name

        if subclient_guid is None:
            raise Exception(f'No DB path for the index with the job {job.job_id} is found on the index server')

        cycle_db = CTreeDB(
            self.commcell,
            self.is_name,
            self.backupset.guid,
            subclient_guid,
            self.subclient
        )

        return cycle_db

    def verify_jobs_in_index(self, idx_db, jobs_in_cycle):
        """ Verifies if all the jobs of one cycle are present in their own cycle's index

                    Args:
                         idx_db (obj)  -- DB object for the index of the referring cycle

                        jobs_in_cycle (list) -- list of jobs present in the referring cycle

        """
        self.log.info('Verifying the jobs in the index at %s', idx_db.db_path)
        expected_job_ids = []
        for job in jobs_in_cycle:
            expected_job_ids.append(job.job_id)
        image_table = idx_db.get_table(table='ImageTable')
        image_table_job_ids = image_table.get_column(column='JobId')
        self.log.info('Actual jobs in the index are %s', image_table_job_ids)
        self.log.info('Expected jobs in the index are %s', expected_job_ids)
        if image_table_job_ids == expected_job_ids:
            self.log.info('The expected jobs are present in the current cycle index')
        else:
            raise Exception('There is a mismatch in expected and actual jobs of the cycle present in index')

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
                temp_cycle.insert(0, job)
                list_of_cycles.append(temp_cycle)
                temp_cycle = []
            elif job.backup_level == 'Incremental':
                temp_cycle.insert(0, job)

        return list_of_cycles

    def get_and_verify_index(self, job_cycle, is_latest_cycle=False):
        """ Creates DB object for point in time DB and verifies if expected jobs are present in the DB

                           Args:
                                 job_cycle (int)           -- The cycle number for which index has to be verified

                                 is_latest_cycle (boolean) -- If the cycle for which index is being verified is latest
                                                             cycle or not
                                                             default: False
               """

        cycle_jobs = self.cycles_list[job_cycle-1]
        self.log.info('Getting DB object for the index of cycle %s ', job_cycle)
        if is_latest_cycle:
            cycle_db = self.idx_db
        else:
            cycle_db = self.get_new_db(job=cycle_jobs[0])
        self.log.info('Checking if all cycle %s jobs are present in the respective index of the cycle', job_cycle)
        self.verify_jobs_in_index(idx_db=cycle_db, jobs_in_cycle=cycle_jobs)

    def verify_index_post_browse(self):
        """ Verifies after the browse from each cycle that no job from that cycle got played back into the main DB
            or into a newly created temp DB.
        """
        self.log.info('Post browse verification of the index')
        self.log.info('Verify that the main/latest cycle DB still has only the latest cycle jobs only')
        self.get_and_verify_index(job_cycle=3, is_latest_cycle=True)
        self.log.info('Verify only three indexes are present in the index cache for the three cycles jobs that ran')
        indexes_list = self.is_machine.get_folders_in_path(folder_path=self.idx_db.backupset_path, recurse=False)
        num_indexes_in_cache = len(indexes_list)
        self.log.info('The number of indexes in the index cache for the subclient are %d', num_indexes_in_cache)
        self.log.info('The indexes in the index cache for the subclient post the browse are %s', indexes_list)
        if num_indexes_in_cache != 3:
            raise Exception(f'The number of indexes in cache is not 3')

