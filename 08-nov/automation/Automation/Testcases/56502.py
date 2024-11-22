# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies the "wait for playback" feature during archive index.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

     run()                      --  Contains the core testcase logic and it is the one executed

    check_archive_file_log()    --  Reads archive index log and verified if the expected text is present in it

    tear_down()                 --  Cleans the data created for Indexing validation

"""

import traceback

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db


class TestCase(CVTestCase):
    """This testcase verifies the "wait for playback" feature during archive index."""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Wait for playback'

        self.tcinputs = {
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.index_db = None
        self.is_sli = False
        self.index_server_machine = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        try:
            self.cl_machine = Machine(self.client, self.commcell)

            self.idx_tc = IndexingTestcase(self)
            self.idx_help = IndexingHelpers(self.commcell)

            self.backupset = self.idx_tc.create_backupset('wait_for_playback', for_validation=True)

            self.subclient = self.idx_tc.create_subclient(
                name='sc_wait_for_playback',
                backupset_obj=self.backupset,
                storage_policy=self.tcinputs.get('StoragePolicy')
            )

            if self.idx_help.get_agent_indexing_level(self.agent) == 'subclient':
                self.log.info('Agent is in subclient level index mode.')
                self.is_sli = True

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1) Run FULL backup
                2) If SLI already then jobs will run in wait for playback mode by default, else set registry key
                3) Run INC backup
                4) Verify wait for playback has happened & completed by looking at log lines in ArchiveIndex.log

        """
        try:

            sc_content = self.subclient.content

            self.log.info('Creating testdata')
            self.idx_tc.new_testdata(self.subclient.content)

            # FULL
            self.idx_tc.run_backup(self.subclient, backup_level='Full', verify_backup=False)

            if self.is_sli:
                self.index_db = index_db.get(self.subclient)
            else:
                self.index_db = index_db.get(self.backupset)
                self.index_db.isc_machine.create_registry('Indexing', 'WAIT_FOR_PLAYBACK', '1', 'Dword')

            self.idx_tc.edit_testdata(sc_content)
            inc_job = self.idx_tc.run_backup(self.subclient, 'incremental', verify_backup=False)

            self.check_archive_file_log(inc_job.job_id, 'Waiting for playback to complete')

            self.check_archive_file_log(inc_job.job_id, 'Playback completed')

            self.log.info('********** Wait for playback has been verified **********')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error(str(traceback.format_exc()))

    def check_archive_file_log(self, job_id, text):
        """Reads archive index log and verified if the expected text is present in it"""

        lines = self.idx_tc.check_log_line(
            self.index_db.index_server, self.index_db.isc_machine, 'ArchiveIndex.log', [job_id, text])

        self.log.info(lines)

        if not lines:
            raise Exception('Timed out looking for words [{0}]'.format(text))

        if text not in lines[0]:
            raise Exception('Cannot find log line [{0}]'.format(text))
        else:
            self.log.info('Found log line [{0}]'.format(text))

    def tear_down(self):
        """Cleans the data created for Indexing validation"""
        if self.status == constants.PASSED:
            self.backupset.idx.cleanup()
