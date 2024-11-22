# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case:

 Testcase verifies if we are soft deleting File system backup jobs as per the retention settings
 of storage policy copies or not

TestCase: Class for executing this test case

TestCase:
    __init__()                             --  initialize TestCase class

    setup()                                --  setup function of this test case

    run()                                  --  run function of this test case

    modify_backup_time()                   --  modifies backup time for the given backup job id

    is_job_soft_deleted()                  --  verifies if all the job is soft deleted from the given copy or not

    is_job_soft_deleted_from_all_copies() --  verifies if all the job is soft deleted from all the copies or not

"""

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """ This testcase verifies if we are soft deleting File system backup jobs as per the retention settings
        of storage policy copies or not

        Steps:
            1. Run 3 cycles of FS backup jobs to a storage policy with two copies
            2. Run aux copy
            3. Modify backup time for the first two jobs in the list
            4. Verify if backup jobs are soft deleted or not from the copy with minimum retention
            5. Modify backup time again for the first two jobs in the list
            6. Verify if backup jobs are soft deleted from all the copies or not
            7. Run synthetic full
    """
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - Days Based Retention - Acceptance'
        self.tcinputs = {
            'StoragePolicy': None
        }
        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.client_index_version = None
        self.backupset = None
        self.subclient = None
        self.jobs = None
        self.first_job = None
        self.second_job = None
        self.storage_policy = None
        self.storage_policy_name = None
        self.primary_copy = None
        self.secondary_copy = None

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))
        self.backupset = self.idx_tc.create_backupset('days_based_retention_accp_bkpst', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
                name='days_based_retention_accp_sc',
                backupset_obj=self.backupset,
                storage_policy=self.tcinputs['StoragePolicy'],
                register_idx=True
        )
        self.idx_help = IndexingHelpers(self.commcell)

        number_of_copies = len(self.storage_policy.copies)
        self.primary_copy = self.storage_policy.get_primary_copy()
        if number_of_copies >= 2:
            self.log.info('Number of copies in the storage policy: %s is %s',
                          self.storage_policy.name, number_of_copies)
            self.secondary_copy = self.storage_policy.get_secondary_copies()[0]
        else:
            raise Exception('The storage policy has only one copy')

        self.log.info('Copy precedences are %d %d', self.primary_copy.copy_precedence,
                      self.secondary_copy.copy_precedence)

        self.log.info('Client: %s', self.client.client_name)
        self.storage_policy_name = str(self.tcinputs.get('StoragePolicy'))
        self.log.info('Storage policy is: %s', self.storage_policy_name)
        self.log.info('Checking Client indexing version..')
        self.client_index_version = self.idx_help.get_agent_indexing_version(self.client)
        self.log.info('Client indexing version is %s', self.client_index_version)
        if self.client_index_version == 'v2':
            self.log.info('Client is in V2')
        else:
            self.log.info('Client is in V1')
            raise Exception('Failing the testcase as Client is in V1')

        self.log.info('Checking if feature is enabled at CS level')
        if self.commcell.get_gxglobalparam_value('EnableDaysOnlyRetention') == 'true':
            self.log.info('Days based retention feature is enabled at CS level')
        else:
            raise Exception('Days based retention feature is NOT enabled at CS level')

        self.log.info('Checking if feature is enabled at Client %s level', self.client.client_name)
        self.csdb.execute(f"""
            select value from APP_AdvanceSettings 
            where keyname = 'EnableDaysOnlyRetention' 
            and relativePath = 'CommServDB.Client' 
            and entityId in (select id from app_client where name = '{self.client.client_name}') 
               """)
        self.log.info('Feature is at Client level: %s', self.csdb.fetch_one_row()[0])
        if self.csdb.fetch_one_row()[0] == 'true':
            self.log.info('Feature is enabled at Client level')
        else:
            self.log.info('Feature is NOT enabled at Client level')
            raise Exception('Failing the testcase as feature is NOT enabled at Client level')

        if self.primary_copy.copy_retention['cycles'] <= 2:
            raise Exception('Primary copy retention (Cycles) is less than or equal to 2 cycles')
        if self.secondary_copy.copy_retention['cycles'] <= 2:
            raise Exception('Secondary copy retention (Cycles) is less than or equal to 2 cycles')

        self.log.info('storage policy copies are: %s and %s',
                      self.primary_copy.copy_name, self.secondary_copy.copy_name)
        self.log.info('Primary copy is: %s and retention days is: %d',
                      self.primary_copy.copy_name, self.primary_copy.copy_retention['days'])
        self.log.info('Secondary copy is: %s and retention days is: %d',
                      self.secondary_copy.copy_name, self.secondary_copy.copy_retention['days'])

        self.log.info('Primary copy precedence is: %d and Secondary copy precedence is: %d',
                      self.primary_copy.copy_precedence, self.secondary_copy.copy_precedence)

        self.log.info('Backup jobs will be deleted from %s copy after %d days',
                      self.primary_copy.copy_name, self.primary_copy.copy_retention['days'])
        self.log.info('Backup jobs will be deleted from %s copy after %d days',
                      self.secondary_copy.copy_name, self.secondary_copy.copy_retention['days'])

    def run(self):
        """Contains the core testcase logic, and it is the one executed"""
        try:

            self.log.info("Running 3 cycles of jobs")
            self.jobs = self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'Edit', 'Incremental', 'Synthetic_full',
                       'Edit', 'Incremental', 'Synthetic_full', 'Edit', 'Incremental']
                    )
            self.log.info("Ran backup jobs successfully")

            self.log.info('********** Running AUX copy **********')
            self.idx_tc.cv_ops.aux_copy(storage_policy=self.storage_policy, sp_copy=self.secondary_copy.copy_name,
                                        media_agent=self.primary_copy.media_agent, wait=True)
            self.log.info('********** AUX copy job completed successfully **********')

            self.log.info('Inform the validation framework that aux copy is done')
            self.backupset.idx.do_after_aux_copy(self.storage_policy_name, self.secondary_copy.copy_precedence)

            for job in self.jobs:
                self.log.info('Jobs in the list are: %d', job.job_id)

            self.first_job = self.jobs[0].job_id
            self.second_job = self.jobs[1].job_id
            self.log.info('First two jobs in the list are: ')
            self.log.info('Job ID: %d', int(self.first_job))
            self.log.info('Job ID: %d', int(self.second_job))

            self.log.info("Run Data aging job")
            self.idx_tc.cv_ops.data_aging()
            self.log.info('Data aging job completed successfully')

            min_retention_days = min(self.primary_copy.copy_retention['days'],
                                     self.secondary_copy.copy_retention['days'])
            max_retention_days = max(self.primary_copy.copy_retention['days'],
                                     self.secondary_copy.copy_retention['days'])

            self.log.info('Min retention days: %d', min_retention_days)
            self.log.info('Max retention days: %d', max_retention_days)
            diff_in_retention_days = (max_retention_days - min_retention_days)

            self.log.info('Modifying backup time by %d days', min_retention_days)
            self.log.info('For backup jobs: %d and %d ', self.first_job, self.second_job)
            self.modify_backup_time(self.jobs[0].job_id, min_retention_days)
            self.modify_backup_time(self.jobs[1].job_id, min_retention_days)

            self.log.info('Running Data aging job')
            self.idx_tc.cv_ops.data_aging()
            self.log.info('Data aging job completed successfully')

            self.log.info('Checking if jobs %d and %d are '
                          'soft aged from primary copy', self.first_job, self.second_job)

            if not self.is_job_soft_deleted(self.first_job, self.primary_copy.copy_name):
                raise Exception('First job is NOT soft deleted from primary copy')

            if not self.is_job_soft_deleted(self.second_job, self.primary_copy.copy_name):
                raise Exception('Second job is NOT soft deleted from primary copy')

            if self.is_job_soft_deleted(self.first_job, self.secondary_copy.copy_name):
                raise Exception('First job is soft deleted from secondary copy')

            if self.is_job_soft_deleted(self.second_job, self.secondary_copy.copy_name):
                raise Exception('Second job is soft deleted from secondary copy')

            self.log.info('Job ids: %d and %d are soft aged from primary copy.'
                          'But not from secondary copy.', self.first_job, self.second_job)
            self.log.info('This is expected.')

            self.log.info('Now verify copy precedence browse for these two jobs')

            self.log.info('Verify job level browse for the first two jobs with copy precedence 1')
            self.log.info('Verifying job level browse for the first job with copy precedence 1')
            try:
                response1 = self.subclient.browse({
                    'show_deleted': False,
                    'from_time': self.jobs[0].start_timestamp,
                    'to_time': self.jobs[0].end_timestamp,  # value should either be the Epoch time or the Timestamp
                    'copy_precedence': self.primary_copy.copy_precedence
                 })
                self.log.info('Response is %s', response1[0][0])
            except Exception as exp1:
                self.log.info('Exceptions is: %s', str(exp1))
                if 'no backups found' in str(exp1).lower():
                    self.log.info('Job is soft aged, hence browse did not return any results')
                else:
                    raise Exception('Please check the exception with browse')

            try:
                response2 = self.subclient.browse({
                    'show_deleted': False,
                    'from_time': self.jobs[1].start_timestamp,
                    'to_time': self.jobs[1].end_timestamp,  # value should either be the Epoch time or the Timestamp
                    'copy_precedence': self.primary_copy.copy_precedence
                })
                self.log.info('Response is %s', response2[0][0])
            except Exception as exp2:
                self.log.info('Exceptions is: %s', str(exp2))
                if 'no backups found' in str(exp2).lower():
                    self.log.info('Job is soft aged, hence browse did not return any results')
                else:
                    raise Exception('Please check the exception with browse')

            self.log.info('Verified job level browse for the first two jobs with copy precedence 1')

            self.log.info('Verify job level browse for the first two jobs with copy precedence 2')
            response3 = self.idx_tc.verify_browse_restore(self.backupset, {
                    'show_deleted': False,
                    'from_time': self.jobs[0].start_timestamp,
                    'to_time': self.jobs[0].end_timestamp,
                    'copy_precedence': self.secondary_copy.copy_precedence
                })
            self.log.info('Response is %s', response3)

            response4 = self.idx_tc.verify_browse_restore(self.backupset, {
                    'show_deleted': False,
                    'from_time': self.jobs[1].start_timestamp,
                    'to_time': self.jobs[1].end_timestamp,
                    'copy_precedence': self.secondary_copy.copy_precedence
                 })
            self.log.info('Response is %s', response4)
            self.log.info('Verified job level browse for the first two jobs with copy precedence 2')

            self.log.info('Modifying backup time by %d days for backup jobs: %d and %d',
                          diff_in_retention_days, self.first_job, self.second_job)
            self.modify_backup_time(self.jobs[0].job_id, diff_in_retention_days)
            self.modify_backup_time(self.jobs[1].job_id, diff_in_retention_days)

            self.log.info('Running Data aging job')
            self.idx_tc.cv_ops.data_aging()
            self.log.info('Data aging job completed successfully')

            self.log.info('Checking if jobs %d and %d are soft aged '
                          'from secondary copy', self.first_job, self.second_job)

            if not self.is_job_soft_deleted(self.first_job, self.secondary_copy.copy_name):
                raise Exception('First job is NOT soft deleted from secondary copy')
            if not self.is_job_soft_deleted(self.second_job, self.secondary_copy.copy_name):
                raise Exception('Second job is NOT soft deleted from secondary copy')

            if not self.is_job_soft_deleted_from_all_copies(self.first_job):
                raise Exception('First job is NOT soft deleted from all the copies')
            if not self.is_job_soft_deleted_from_all_copies(self.second_job):
                raise Exception('Second job is NOT soft deleted from all the copies')

            self.log.info('Job ids: %d and %d are soft aged from secondary copy too',
                          self.first_job, self.second_job)
            self.log.info('This is expected')

            self.log.info('Running synthetic full job')
            self.jobs = self.idx_tc.run_backup_sequence(subclient_obj=self.subclient,
                                                        steps=['Synthetic_full'], verify_backup=True)
            self.log.info('Ran synthetic full job')

            self.log.info('Done with all the cases')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def modify_backup_time(self, job_id, no_of_days):
        """ Modifies backup time for the given job id
                Args:
                    job_id (int) -- Job for which we want to modify backup time
                    no_of_days (int) -- Number of days to modify backup time
                returns:
                    bool -- Returns true if backup time has been modified successfully
        """
        self.log.info('Modifying backup time for job: %d by %d days', job_id, no_of_days)
        self.idx_tc.options_help.update_commserve_db(f"""
                        update JMBkpStats 
                       set servStartDate = servStartDate - '{no_of_days}'*86400, 
                       servEndDate = servEndDate - '{no_of_days}'*86400 
                       where jobId = '{job_id}'  
                       """)
        self.log.info('Modified backup time for job: %d by %d days', job_id, no_of_days)

    def is_job_soft_deleted(self, job_id, storage_policy_copy_name):
        """ Verifies if job is soft deleted from the given storage policy copy
                Args:
                    job_id (int) -- Job for which we want to modify backup time
                    storage_policy_copy_name (string) -- Storage policy copy on which we need to verify
                                                    if job is deleted or not

                returns:
                    bool -- Returns true if job is soft deleted
        """
        self.log.info('Checking if job id: %d is soft aged from copy %s or not', job_id, storage_policy_copy_name)
        query = """
            SELECT ISNULL((SELECT TOP 1 0 FROM archFile AF WITH(READUNCOMMITTED)
            JOIN archFileCopy AFC WITH (READUNCOMMITTED) ON AFC.archFileId = AF.id 
            AND AFC.commCellId = AF.commCellId
            WHERE AF.fileType IN (2, 6) AND AFC.flags&65536=0 
            AND AF.jobId = '{job_id}' AND AFC.archCopyId in 
            (select id from archGroupCopy where archGroupId in 
            (select id from archGroup where name = '{self.storage_policy_name}') 
            and name = '{storage_policy_copy}') ), 1)
            """
        self.log.info('Sql query is: %s', query)

        self.csdb.execute(f"""
            SELECT ISNULL((SELECT TOP 1 0 FROM archFile AF WITH(READUNCOMMITTED)
            JOIN archFileCopy AFC WITH (READUNCOMMITTED) ON AFC.archFileId = AF.id 
            AND AFC.commCellId = AF.commCellId
            WHERE AF.fileType IN (2, 6) AND AFC.flags&65536=0 
            AND AF.jobId = '{job_id}' AND AFC.archCopyId in 
            (select id from archGroupCopy where archGroupId in 
            (select id from archGroup where name = '{self.storage_policy_name}') 
            and name = '{storage_policy_copy_name}') ), 1)
            """)
        self.log.info('Query output: %s', self.csdb.fetch_one_row()[0])

        if int(self.csdb.fetch_one_row()[0]):
            self.log.info('Job id: %d is soft aged from copy %s', job_id, storage_policy_copy_name)
            return True
        else:
            self.log.info('job id: %d is NOT soft aged from copy %s', job_id, storage_policy_copy_name)
            return False

    def is_job_soft_deleted_from_all_copies(self, job_id):
        """ Verifies if job is soft deleted from all the copies or not
                Args:
                    job_id (int) -- Job for which we want to modify backup time

                returns:
                    bool -- Returns true if job is soft deleted
        """
        query = """
            SELECT ISNULL((SELECT TOP 1 0 FROM archFile AF WITH(READUNCOMMITTED)
            JOIN archFileCopy AFC WITH (READUNCOMMITTED) ON AFC.archFileId = AF.id 
            AND AFC.commCellId = AF.commCellId
            WHERE AF.fileType IN (2, 6) AND AFC.flags&65536=0 
            AND AF.jobId = '{job_id}'), 1)
        """
        self.log.info('Sql query is: %s', query)

        self.csdb.execute(f"""
            SELECT ISNULL((SELECT TOP 1 0 FROM archFile AF WITH(READUNCOMMITTED)
            JOIN archFileCopy AFC WITH (READUNCOMMITTED) ON AFC.archFileId = AF.id 
            AND AFC.commCellId = AF.commCellId
            WHERE AF.fileType IN (2, 6) AND AFC.flags&65536=0 
            AND AF.jobId = '{job_id}'), 1)
            """)

        self.log.info('Checking if job id: %d is soft aged from all the copies', job_id)
        self.log.info('Query output: %s', self.csdb.fetch_one_row()[0])

        if int(self.csdb.fetch_one_row()[0]):
            self.log.info('Job id: %d is soft aged from all the copies', job_id)
            return True
        else:
            self.log.info('job id: %d is NOT soft aged from all the copies', job_id)
            return False
