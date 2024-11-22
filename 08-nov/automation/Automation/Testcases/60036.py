# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that we are able to browse and restore the first running backup job for a subclient.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""

import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Server.JobManager.jobmanager_helper import JobManager

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that we are able to browse and restore the first running backup job for a subclient.

        Steps:
            1) Set additional setting to enable browse of running job.
            2) Create a new backupset, subclient.
            3) Start a FULL backup job.
            4) While job is in backup phase, do browse, find and restore.
            5) Verify if they work and give some results and does not fail.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Browse of first running backup job'

        self.tcinputs = {
            'TestData': None,
            'RestoreLocation': None,
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.testdata = None
        self.idx_db = None

        self.did_browse = False
        self.did_restore = False
        self.did_find = False

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client, self.commcell)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.backupset = self.idx_tc.create_backupset('running_job_browse', for_validation=False)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy'),
            content=[self.tcinputs.get('TestData')]
        )

        self.log.info('***** Adding additional setting to enable browse of running job *****')
        self.commcell.add_additional_setting(
            'CommServDB.GxGlobalParam',
            'AllowBrowseForRunningJob',
            'INTEGER',
            '1'
        )

    def run(self):
        """Contains the core testcase logic"""

        self.log.info('***** Running FULL backup *****')
        full_job = self.subclient.backup('full')
        self.log.info('Started full job [%s]', full_job.job_id)

        full_job = JobManager(full_job)
        full_job.wait_for_phase(phase='backup')
        self.log.info('Job is in backup phase')

        init_wait_time = self.tcinputs.get('InitialWait', 10)
        self.log.info('Waiting for [%s] seconds before trying browse, find, restore', init_wait_time)
        time.sleep(init_wait_time)

        # BROWSE
        while not full_job.job.is_finished and full_job.job.phase.lower() == 'backup':
            browse_items = []
            try:
                self.log.info('***** Doing browse *****')
                browse_items, _ = self.subclient.browse(path=self.subclient.content[0])
                self.log.info('Got [%s] items in browse result', len(browse_items))
            except Exception as e:
                self.log.error('Got no browse results. Exception [%s]', e)

            if not browse_items:
                self.log.error('No browse items received. Trying again in 5 seconds.')
                time.sleep(5)
                continue
            else:
                self.did_browse = True
                self.log.info('Browse is successful')
                break

        # FIND
        while not full_job.job.is_finished and full_job.job.phase.lower() == 'backup':
            find_items = []
            try:
                self.log.info('***** Doing find *****')
                find_items, _ = self.subclient.find(filename='*', page_size='1000')
                self.log.info('Got [%s] items in find result', len(find_items))
            except Exception as e:
                self.log.error('Got no find results. Exception [%s]', e)

            if not find_items:
                self.log.error('No find items received. Trying again in 5 seconds.')
                time.sleep(5)
                continue
            else:
                self.did_find = True
                self.log.info('Find is successful')
                break

        # RESTORE
        while not full_job.job.is_finished and full_job.job.phase.lower() == 'backup':
            self.log.info('***** Doing restore *****')
            restored_items = 0
            restore_location = self.tcinputs.get('RestoreLocation')
            try:
                self.cl_machine.remove_directory(restore_location)
            except Exception as e:
                self.log.error('Failed to delete restore directory [%s]', e)

            restore_job = self.subclient.restore_out_of_place(
                client=self.client,
                destination_path=restore_location,
                paths=self.subclient.content
            )
            self.log.info('Started restore job [%s]', restore_job.job_id)

            if restore_job.wait_for_completion():
                self.log.info('Restore job completed successfully')
                restored_items = self.cl_machine.number_of_items_in_folder(
                    restore_location, include_only='files', recursive=True)
                self.log.info('Restored items [%s]', restored_items)
                break
            else:
                self.log.error('Restore job failed')

            if restored_items:
                self.did_restore = True
                self.log.info('Find is successful')

        full_job.wait_for_state(expected_state='completed')
        self.log.info('Full job completed')

        self.log.info('***** Tried all operations on a running job *****')
        result = [self.did_browse, self.did_find, self.did_restore]
        self.log.info('Result of browse, find, restore [%s]', result)

        if any(result):
            self.log.info('We are able to at least do one of browse, find, restore of a running job.')
        else:
            self.log.error('None of the operations worked during the running job')
            self.status = constants.FAILED

    def tear_down(self):
        if self.commcell:
            self.log.info('Deleting the additional setting')
            try:
                self.commcell.delete_additional_setting('CommServDB.GxGlobalParam', 'AllowBrowseForRunningJob')
            except Exception as e:
                self.log.error('Exception while deleting additional setting [%s]', e)
