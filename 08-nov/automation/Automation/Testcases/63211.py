# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase verifies that multistream synthetic full job does not exceed the max limit of 4

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    get_streams()               --  Gets the number of streams consumed by the backup job

    tear_down()                 --  The function to run at the end of the testcase

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that multistream synthetic full job does not exceed the max limit of 4

        Steps:
            1) Run FULL, INC with huge data
            2) Delete JMSynthFullJobDataSizeBucketInGB and JMSynthFullJobMaxStreamNumber settings
            3) Run SFULL - Job should consume only 1 stream (since default bucket size is 100GB)
            4) Run INC
            5) Set JMSynthFullJobDataSizeBucketInGB setting
            6) Run SFULL - Job should consume max 4 streams (since data is split by the small bucket size)
            7) Run INC
            8) Set JMSynthFullJobMaxStreamNumber setting
            9) Run SFULL - Job should consume max number of streams as configured in testcase input

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Synthetic full - Limit max streams'

        self.tcinputs = {
            'TestDataPath': None,
            'CopyData': None,
            'StoragePolicy': None,
            'BucketSizeGB': None,
            'MaxStreamCount': None,
            # 'ReaderCount': None, # The number of readers to set on the subclient
            # 'DeleteBackupset': None, # Deletes the backupset after run. 0: only on pass, 1: always
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.tape_sp = None
        self.tape_sp_copy = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client, self.commcell)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.backupset = self.idx_tc.create_backupset(f'{self.id}_sfull_limit_streams', for_validation=False)

        self.subclient = self.idx_tc.create_subclient(
            name=f'sc1_{self.id}',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        self.subclient.allow_multiple_readers = True
        self.subclient.data_readers = self.tcinputs.get('ReaderCount', 10)

    def run(self):
        """Contains the core testcase logic"""

        self.log.info('***** SCENARIO 1 - No additional settings set *****')
        self.log.info('Deleting additional settings')
        self.commcell.delete_additional_setting('CommServDB.ResourceManager', 'JMSynthFullJobDataSizeBucketInGB')
        self.commcell.delete_additional_setting('CommServDB.ResourceManager', 'JMSynthFullJobMaxStreamNumber')

        self.idx_tc.run_backup_sequence(
            self.subclient, ['new', 'copy', 'full', 'edit', 'incremental'], verify_backup=False
        )

        job = self.idx_tc.run_backup(self.subclient, 'synthetic_full', advanced_options={
            'use_multi_stream': True,
            'use_maximum_streams': True
        })

        job_streams = self.get_streams(job)
        self.log.info('***** Number of streams used by job [%s] *****', job_streams)
        self.log.info('Expected: 1 (Default behavior. No additional settings are kept)')

        if self.get_streams(job) != 1:
            raise Exception(f'More than 1 stream used by synthetic full job. Consumed [{job_streams}] streams')

        self.log.info('Job consumed only [%s] stream as expected', job_streams)

        self.log.info('***** SCENARIO 2 - Bucket size is configured *****')
        self.log.info('Adding JMSynthFullJobDataSizeBucketInGB setting. Value [%s]', self.tcinputs.get('BucketSizeGB'))
        self.commcell.add_additional_setting(
            'CommServDB.ResourceManager', 'JMSynthFullJobDataSizeBucketInGB',
            'INTEGER', self.tcinputs.get('BucketSizeGB')
        )

        self.idx_tc.run_backup_sequence(
            self.subclient, ['edit', 'incremental'], verify_backup=False
        )

        job = self.idx_tc.run_backup(self.subclient, 'synthetic_full', advanced_options={
            'use_multi_stream': True,
            'use_maximum_streams': True
        })

        job_streams = self.get_streams(job)
        self.log.info('***** Number of streams used by job [%s] *****', job_streams)
        self.log.info('Expected: 4 (Max streams allowed)')

        if self.get_streams(job) != 4:
            raise Exception(f'Incorrect streams used by synthetic full job. Consumed [{job_streams}]. Expected [4]')

        self.log.info('Job consumed only [%s] stream as expected', job_streams)

        self.log.info('***** SCENARIO 3 - Bucket size & max streams are configured *****')
        self.log.info('Adding JMSynthFullJobMaxStreamNumber setting. Value [%s]', self.tcinputs.get('MaxStreamCount'))
        self.commcell.add_additional_setting(
            'CommServDB.ResourceManager', 'JMSynthFullJobMaxStreamNumber',
            'INTEGER', self.tcinputs.get('MaxStreamCount')
        )

        self.idx_tc.run_backup_sequence(
            self.subclient, ['edit', 'incremental'], verify_backup=False
        )

        job = self.idx_tc.run_backup(self.subclient, 'synthetic_full', advanced_options={
            'use_multi_stream': True,
            'use_maximum_streams': True
        })

        job_streams = self.get_streams(job)
        config_max_streams = int(self.tcinputs.get('MaxStreamCount'))
        self.log.info('***** Number of streams used by job [%s] *****', job_streams)
        self.log.info('Expected: [%s] (Configured)', config_max_streams)

        if self.get_streams(job) > config_max_streams:
            raise Exception(f'More streams consumed than configured. '
                            f'Consumed [{job_streams}] streams. Max [{config_max_streams}] allowed')

        self.log.info('Job consumed only [%s] stream as expected max [%s]', job_streams, config_max_streams)

        self.log.info('All scenarios verified successfully')

    def get_streams(self, job):
        """Gets the number of streams consumed by the backup job

            Args:
                job     (obj)   --      The job object to get the number of streams for

            Returns:
                (int)   --  The number of streams used by the job

        """

        self.csdb.execute(
            f"select numStreams from JMBkpStats where jobId = '{job.job_id}'"
        )
        row = self.csdb.fetch_one_row()
        if not row[0]:
            raise Exception(f'Cannot fetch stream count for job [{job.job_id}]')

        return int(row[0])

    def tear_down(self):
        """The function to run at the end of the testcase"""

        if not self.backupset:
            return

        delete_config = self.tcinputs.get('DeleteBackupset')
        should_delete = False

        if delete_config == 1 or (delete_config == 0 and self.status == constants.PASSED):
            should_delete = True

        if should_delete:
            self.log.info('Deleting backupset')
            try:
                self.agent.backupsets.refresh()
                self.agent.backupsets.delete(self.backupset.name)
                self.log.info('Backupset deleted successfully')
            except Exception as e:
                self.log.error('Failed to delete backupset [%s]', e)
