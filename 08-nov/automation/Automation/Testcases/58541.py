# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that index playback happening at the same time and the operation completes successfully.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    tear_down()                 --  Cleans the data created for Indexing validation

    run_backup_backupset()      --  Starts backup at the backupset level and waits for it to complete

"""
from cvpysdk.job import Job

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import commonutils

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that index playback happening at the same time and the operation
    completes successfully.

        Steps:
            1) Check if client is running in subclient level index mode
            2) Create a new backupset.
            3) Create 15 subclients under it (sequential)
            4) Start FULL backup job for all the subclients at the same time
            (start backup from backupset level). --> All the backup jobs should complete successfully
            5) Start INC backup job for all the subclients at the same time --> All jobs should complete successfully
            6) Do browse and restore at backupset level and verify the results.
            7) Start Synthetic full job for all the subclients --> All jobs should complete successfully
            8) Do browse at backupset level and verify results are obtained.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Subclient level index - Index playback of multiple subclients at same time'

        self.tcinputs = {
            'NumberOfSubclients': None,
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.index_db = None
        self.subclients = []

    def setup(self):
        """All testcase objects are initialized in this method"""

        try:
            self.cl_machine = Machine(self.client, self.commcell)

            self.idx_tc = IndexingTestcase(self)
            self.idx_help = IndexingHelpers(self.commcell)

            if self.idx_help.get_agent_indexing_level(self.agent) == 'backupset':
                raise Exception('Agent is in backupset level index. Cannot proceed with automation. '
                                'Please move this client-agent to subclient level index')

            self.backupset = self.idx_tc.create_backupset('SLI_MULTIPLE_SCS', for_validation=True)

            self.subclient_count = commonutils.get_int(self.tcinputs.get('NumberOfSubclients'), 15)
            self.subclients = []

            for i in range(self.subclient_count):
                sc_name = 'sc_' + str(i)
                self.log.info(f'Creating subclient [{sc_name}] - [{i+1}/{self.subclient_count}]')
                subclient = self.idx_tc.create_subclient(
                    name=sc_name,
                    backupset_obj=self.backupset,
                    storage_policy=self.tcinputs.get('StoragePolicy'),
                    delete_existing_testdata=False
                )

                self.log.info('Creating testdata')
                self.idx_tc.new_testdata(subclient.content)

                self.subclients.append(subclient)

            self.log.info('Refreshing subclients object')
            self.backupset.subclients.refresh()

        except Exception as exp:
            self.log.exception(exp)
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:

            self.run_backup_backupset('Full')

            for sc in self.subclients:
                self.idx_tc.edit_testdata(sc.content)

            self.run_backup_backupset('Incremental')

            self.log.info('Validating browse results at backupset level')
            self.backupset.idx.validate_browse_restore({
                '_verify_jobid': False,
                'restore': {
                    'do': True
                }
            })

            self.run_backup_backupset('Synthetic_Full')

            self.log.info('Validating browse results at backupset level after SFULL')
            self.backupset.idx.validate_browse_restore({
                '_verify_jobid': False,
                'restore': {
                    'do': True
                }
            })

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def run_backup_backupset(self, level='incremental'):
        """Starts backup at the backupset level and waits for it to complete

            Args:
                level       (str)   --  The type of backup to run

            Returns:
                None

            Raises:
                Exception when any one of the subclient's backup job fails

        """

        jobs_started = self.backupset.backup(backup_level=level)

        for job in jobs_started:
            if not isinstance(job, Job):
                self.log.error(f'Item [{job}] is not a valid job object. Skipping it')
                continue

            job_id = job.job_id
            self.log.info(f'Waiting for job [{job_id}] to complete')
            if not job.wait_for_completion():
                raise Exception(f'Job [{job_id}] - [{job.status}] Please check. Exiting testcase')
            else:
                self.log.info(f'Job [{job_id}] completed successfully')

            self.backupset.idx.record_job(job)

        self.log.info(f'All [{level}] backup jobs completed successfully')

    def tear_down(self):
        """Cleans the data created for Indexing validation"""
        if self.status == constants.PASSED:
            self.backupset.idx.cleanup()
