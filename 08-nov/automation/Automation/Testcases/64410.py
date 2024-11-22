# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

 This Testcase verifies if cross cycle browse with index pruning set to 3 cycles

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    divide_jobs_into_cycles()                   --  divides the jobs into lists of job cycles

    get_all_checkpoints()                       --  gets all the valid checkpoints available for the subclient index

    verify_restored_checkpoint()                --  verifies if the expected checkpoints are restored after the
                                                    cross cycle browse

    delete_index_db()                           --  to delete the index DBs from index cache

    verify_temp_db()                            --  verifies if temp DB folder is created for jobs without
                                                    checkpoint when browsed from

"""

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Indexing.database import index_db
from Indexing.database.ctree import CTreeDB
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This Testcase verifies if cross cycle browse when index pruning set to 3 cycles

        Steps:

            Index pruning > 2

                Jobs to run:
                1. Have another subclient with index pruning set to 3
                2. Run 4 cycles of jobs
                3. Prune the DB ( run both checkpoint and compaction )
                CP1 has cycles 1,2,3,4
                4. Run 2 cycles of jobs
                5. Prune the DB ( run both checkpoint and compaction )
                CP2 has cycles 2,3,4,5,6

                Main DB now has cycles 4,5,6

                Test steps:
                6. Do cross cycle browse from all cycles and verify that CP1 is restored as expected
                7. Delete the restored checkpoint DB from cache
                8. Do a cross cycle browse from cycles 2 and 3 and verify that CP2 is restored
                9. Repeat step 7
                10. Invalidate CP1
                11. Do a job based cross cycle browse from any of cycle 1 job, verify that a temp DB is created and the
                    job is played back

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - Cross Cycle Browse - With pruning set to 3 cycles'
        self.tcinputs = {
            'StoragePolicy': None,
        }
        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.indexing_level = None
        self.is_name = None
        self.is_machine = None
        self.idx_db = None
        self.jobs = None
        self.cycles_list = None
        self.checkpoint_timestamps = None

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)

        self.backupset = self.idx_tc.create_backupset('64410_cross_cyc_browse_pruning_3cycles', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='cross_cyc_browse_pruning_3cycles_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            register_idx=True
        )

        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        if not self.indexing_level == 'subclient':
            raise Exception('This testcase is specific to subclient level index')

        self.subclient.index_pruning_type = 'cycles_based'
        self.subclient.index_pruning_cycles_retention = 3

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:

            self.log.info('******** Running Jobs for Subclient, with '
                          'index pruning set to 3 cycles ********')

            self.log.info('Running 4 cycles of jobs')
            self.jobs = self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'Full', 'Full', 'Full'],
                verify_backup=True
            )

            self.idx_db = index_db.get(self.subclient)

            self.log.info('Running index pruning to prune old cycle jobs')
            if not self.idx_db.prune_db():
                raise Exception('Failed to prune the DB')

            # CP1 has Full1, Full2, Full3, Full4
            # Main DB has Full2, Full3, Full4

            self.log.info('Running 2 cycles of jobs')
            self.jobs.extend(self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['Full', 'Full'],
                verify_backup=True
            ))

            self.log.info('Running index pruning to prune old cycle jobs')
            if not self.idx_db.prune_db():
                raise Exception('Failed to prune the DB')

            # CP2 has Full2 to Full6
            # Main DB has Full4, Full5, Full6

            self.log.info('******** Verify Cross Cycle Browse for Subclient with '
                          'index pruning set to 3 cycles ********')

            self.is_name = self.idx_db.index_server
            index_server = self.is_name.client_name
            self.log.info('The Current Index Server is %s', index_server)
            self.log.info('Connecting to Index Server Machine: %s', index_server)

            self.is_machine = self.idx_db.isc_machine
            indexes_list = []
            all_indexes_list = self.is_machine.get_folders_in_path(
                folder_path=self.idx_db.backupset_path, recurse=False)
            if self.idx_db.backupset_path in all_indexes_list:
                all_indexes_list.remove(self.idx_db.backupset_path)
            for each_index in all_indexes_list:
                db_folder_name = each_index.split(self.is_machine.os_sep)[-1]
                if self.idx_db.db_guid in db_folder_name:
                    indexes_list.append(each_index)

            num_indexes_in_cache = len(indexes_list)
            self.log.info('The number of indexes in the index cache for the subclient are %d',
                          num_indexes_in_cache)
            self.log.info('The indexes in the list are %s', indexes_list)
            if num_indexes_in_cache > 1:
                raise Exception('More than 1 index DBs exist in cache, only '
                                'main DB should have been present')
            elif not num_indexes_in_cache:
                raise Exception('There are no index DBs in the cache')

            self.cycles_list = self.divide_jobs_into_cycles()
            self.cycles_list.reverse()
            self.log.info(' The list of jobs divided into different cycles is %s', self.cycles_list)

            self.checkpoint_timestamps = self.get_all_checkpoints()
            self.log.info('Checkpoints and their respective start '
                          'and end timestamps are %s', self.checkpoint_timestamps)

            self.log.info('******* Case 1: Perform a time range browse from all cycles'
                          ' and verify restore of CP1 and CP2 *******')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'subclient': self.subclient.subclient_name,
                'operation': 'browse',
                'from_time': self.cycles_list[0][0].start_timestamp,
                'to_time': self.cycles_list[5][0].end_timestamp,
                'show_deleted': True

            })

            self.log.info('Verifying the restored checkpoint CP1 and CP2 after the cross cycle browse')
            self.verify_restored_checkpoint(
                expected_checkpoints=['CP1', 'CP2']
            )

            self.log.info('Delete all restored checkpoint index DBs from the cache except the main DB')
            self.delete_index_db()

            self.log.info('******* Case 2 - Perform a time range browse from cycles 2 and 3 and'
                          ' verify restore of CP2 *******')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'subclient': self.subclient.subclient_name,
                'operation': 'browse',
                'from_time': self.cycles_list[1][0].start_timestamp,
                'to_time': self.cycles_list[2][0].end_timestamp,
                'show_deleted': True

            })
            self.log.info('Verifying the restored checkpoint CP2 after the cross cycle browse')
            self.verify_restored_checkpoint(
                expected_checkpoints=['CP2']
            )

            self.log.info('Delete all restored checkpoint index DBs from the cache except the main DB')
            self.delete_index_db()

            self.log.info('******* Case 3 - Invalidate CP1, perform a job based browse from cycle 1 and '
                          'verify temp DB is created for playback for cycle 1 jobs *******')

            self.log.info(' Invalidating CP1')
            invalidation_checkpoint_list = ['CP1']
            for each in invalidation_checkpoint_list:
                self.idx_tc.options_help.update_commserve_db(query=f"""
                            update app_indexcheckpointinfo set flags = 0
                            where starttime = {self.checkpoint_timestamps[each]['start_time']} and
                            endtime = {self.checkpoint_timestamps[each]['end_time']} and
                            dbname = '{self.idx_db.db_guid}'

                            """)

            self.idx_tc.verify_browse_restore(self.backupset, {
                'subclient': self.subclient.subclient_name,
                'operation': 'browse',
                'job_id': self.cycles_list[0][0].job_id,

            })

            self.log.info('Verifying the creation of temp DB after the cross cycle browse')
            self.verify_temp_db(jobs_without_checkpoint=self.cycles_list[0])

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
                temp_cycle.insert(0, job)
                list_of_cycles.append(temp_cycle)
                temp_cycle = []
            elif job.backup_level == 'Incremental':
                temp_cycle.insert(0, job)

        return list_of_cycles

    def get_all_checkpoints(self):
        """ Gets all the valid checkpoints available for the subclient index

                returns:
                          dict()   -- Mapping of checkpoints and their start and end timestamps

         """

        checkpoint_timestamps = {}
        self.log.info('********** Getting the checkpoints for the subclient **********')
        query = f""" 
            select * from App_IndexCheckpointInfo where dbname = '{self.idx_db.db_guid}' and 
            flags = 1 order by afileid asc
            """
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        if not rows:
            raise Exception('There are no checkpoints for the DB')
        self.log.info('All valid checkpoints are %s', rows)

        for i in range(0, len(rows)):
            checkpoint_timestamps[f'CP{i + 1}'] = {
                'start_time': rows[i][4],
                'end_time': rows[i][5]

            }
        return checkpoint_timestamps

    def verify_restored_checkpoint(self, expected_checkpoints):
        """ Verifies if the expected checkpoints are restored after the cross cycle browse

                        Args:

                                expected_checkpoints (list)  -- list of expected checkpoints that are to be restored

        """

        restored_checkpoints = []
        indexes_list = self.is_machine.get_folders_in_path(folder_path=self.idx_db.backupset_path, recurse=False)
        if self.idx_db.backupset_path in indexes_list:
            indexes_list.remove(self.idx_db.backupset_path)
        self.log.info('The indexes in the index cache after checkpoint restore are %s', indexes_list)
        for checkpoint in expected_checkpoints:
            checkpoint_start_time = self.checkpoint_timestamps[checkpoint].get('start_time')
            checkpoint_end_time = self.checkpoint_timestamps[checkpoint].get('end_time')
            for each_index in indexes_list:
                db_folder_name = each_index.split(self.is_machine.os_sep)[-1]
                if checkpoint_start_time in db_folder_name and checkpoint_end_time in db_folder_name:
                    self.log.info('The restored checkpoint:%s is at %s', checkpoint, each_index)
                    restored_checkpoints.append(checkpoint)

        if expected_checkpoints == restored_checkpoints:
            self.log.info('All the restored checkpoints are same as the expected checkpoints')
        else:
            raise Exception('There is a mismatch in expected and actual checkpoints that got restored')

    def delete_index_db(self,  remove_main_db=False):
        """ To delete the index DBs from index cache

                Args:

                        remove_main_db (boolean)     -- If main index DB should also be deleted or not

        """

        indexes_list = self.is_machine.get_folders_in_path(folder_path=self.idx_db.backupset_path, recurse=False)
        if self.idx_db.backupset_path in indexes_list:
            indexes_list.remove(self.idx_db.backupset_path)
        self.log.info('The indexes in the index cache after checkpoint restore are %s', indexes_list)
        if not remove_main_db:
            indexes_list.remove(self.idx_db.db_path)
        for each_index in indexes_list:
            self.is_machine.remove_directory(directory_name=each_index)

    def verify_temp_db(self, jobs_without_checkpoint):
        """ Verifies if temp DB folder is created for jobs without checkpoint when browsed from

                Args:

                        jobs_without_checkpoint(list) -- List of all jobs that are not part of any checkpoint

        """

        subclient_guid = ''
        expected_jobs = []
        indexes_list = self.is_machine.get_folders_in_path(folder_path=self.idx_db.backupset_path, recurse=False)
        if self.idx_db.backupset_path in indexes_list:
            indexes_list.remove(self.idx_db.backupset_path)
        self.log.info('The indexes in the index cache after temp DB creation are %s', indexes_list)
        for each_index in indexes_list:
            db_folder_name = each_index.split(self.is_machine.os_sep)[-1]
            if str(jobs_without_checkpoint[0].start_timestamp) in db_folder_name:
                self.log.info('The temp DB created for playback of job: %d is at %s',
                              jobs_without_checkpoint[0].job_id, each_index)
                subclient_guid = db_folder_name

        for each_job in jobs_without_checkpoint:
            expected_jobs.append(each_job.job_id)

        if subclient_guid:
            self.log.info('Getting index DB for the temp DB created')
            cycle_db = CTreeDB(
                self.commcell,
                self.is_name,
                self.backupset.guid,
                subclient_guid,
                self.subclient
            )
            self.log.info('Verifying the if jobs without checkpoint are in temp DB at %s', cycle_db.db_path)
            image_table = cycle_db.get_table(table='ImageTable')
            image_table_job_ids = image_table.get_column(column='JobId')
            self.log.info('Actual jobs in the index are %s', image_table_job_ids)
            self.log.info('Expected jobs in the index are %s', expected_jobs)
            if image_table_job_ids == expected_jobs:
                self.log.info('The expected jobs are present in the temp DB index')
            else:
                raise Exception('There is a mismatch in expected and actual jobs of the temp DB index')

        else:
            raise Exception('No temp DB created for jobs without checkpoint upon cross cycle browse')
