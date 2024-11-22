# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that playback completes successfully when interrupted by checkpoint
operation

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    run_backup()                --  Runs a backup job and adds the job to Indexing validation

    has_partial_results()       --  Does browse operation and checks if the results are partial

    check_log()                 --  Checks if the given words are present in IndexServer log

"""

import traceback
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db

from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """This testcase verifies that playback completes successfully when interrupted by
    checkpoint operation"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Playback interrupted by checkpoint'
        self.product = self.products_list.MEDIAAGENT
        self.feature = self.features_list.INDEXING
        self.show_to_user = False

        self.tcinputs = {
            'StoragePolicyName': None,
            'TestDataPath': None
        }

        self.backupset = None
        self.subclient = None
        self.storage_policy = None

        self.cl_machine = None
        self.cl_delim = None
        self.idx_tc = None
        self.idx_help = None
        self.idx = None
        self.isc = None
        self.isc_machine = None

    def setup(self):
        """All testcase objects are initializes in this method"""

        try:

            self.backupset_name = self.tcinputs.get('Backupset', 'playback_interruption')
            self.subclient_name = self.tcinputs.get('Subclient', self.id)
            self.storagepolicy_name = self.tcinputs.get('StoragePolicyName')
            self.testdata_path = self.tcinputs.get('TestDataPath').split(';')

            self.cl_machine = Machine(self.client, self.commcell)
            self.cl_delim = self.cl_machine.os_sep

            self.idx_tc = IndexingTestcase(self)
            self.idx_help = IndexingHelpers(self.commcell)

            self.backupset = self.idx_tc.create_backupset(self.backupset_name, for_validation=False)

            self.subclient = self.idx_tc.create_subclient(
                name=self.subclient_name,
                backupset_obj=self.backupset,
                storage_policy=self.storagepolicy_name,
                content=self.testdata_path
            )

        except Exception as exp:
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))

            self.log.info('***** Running FULL job *****')
            self.idx_tc.run_backup(self.subclient, backup_level='Full')

            self.log.info('***** Editing testdata *****')
            self.idx_tc.create_only_files(self.subclient.content, count=20)

            self.log.info('***** Running INC job *****')
            self.idx_tc.run_backup(self.subclient, backup_level='Incremental')

            self.log.info('***** Initializing index server machine details ****')
            the_db = index_db.get(self.backupset)
            self.backupset.refresh()
            self.isc = self.backupset.index_server
            self.isc_machine = Machine(self.isc, self.commcell)

            self.log.info('***** Deleting DB *****')
            the_db.delete_db()

            self.log.info('***** Triggering playback by doing browse *****')

            if not self.has_partial_results():
                raise Exception('Browse results are not partial. Expecting playback to start')

            self.log.info('Full reconstruction started for the DB')

            the_db.checkpoint_db(by_all_index_backup_clients=False, registry_keys={
                'CHKPOINT_ITEMS_ADDED_MIN': 0,
                'CHKPOINT_MIN_DAYS': 0
            })

            self.log.info('Waiting 2 minutes for playback to complete')
            time.sleep(120)

            self.log.info('Checking if playback completed after checkpoint interruption')

            if self.has_partial_results():
                raise Exception('Got partial results after checkpoint interruption')

            self.log.info('Playback completed successfully with checkpoint interruption')

            self.log.info('***** Running SFULL job *****')
            sfull_job = self.subclient.backup('synthetic_full')

            self.log.info('SFULL job [{0}] started, waiting for restore vector to complete'.format(
                sfull_job.job_id
            ))
            time.sleep(60)

            self.log.info('***** Checking if SFULL playback started *****')

            lines = self.check_log(sfull_job, 'Begin playback of job')

            if not lines:
                raise Exception('Playback didn\'t start in expected time')

            self.log.info('***** Playback started for SFULL job *****')
            self.log.info('Starting checkpoint operation')

            the_db.checkpoint_db(by_all_index_backup_clients=False, registry_keys={
                'CHKPOINT_ITEMS_ADDED_MIN': 0,
                'CHKPOINT_MIN_DAYS': 0
            })

            self.log.info('Initiating playback by doing browse')
            self.subclient.browse()

            self.log.info('Waiting for SFULL job to complete')
            job_jm = JobManager(sfull_job)
            job_jm.wait_for_state('completed')
            self.log.info('SFULL job completed')

            self.log.info('***** Checking if playback completed after interruption *****')
            if not self.has_partial_results():
                self.log.info(
                    'SFULL playback completed successfully after checkpoint interruption')
                return True

            self.log.info('SFULL playback didn\'t resume. Trying again in 3 minutes')
            time.sleep(180)

            if self.has_partial_results():
                raise Exception('Browse results are still partial after playback interruption')

            self.log.info('Got complete browse result after checkpoint interruption')

            lines = self.check_log(sfull_job, 'Finished playback')

            if not lines:
                raise Exception(
                    'Got complete results, but cannot find "finished playback" log line')

            self.log.info('Verified playback complete log line for the SFULL job.')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def has_partial_results(self):
        """Does browse operation and checks if the results are partial"""

        self.log.info('Doing browse')

        dummy, resp = self.subclient.browse({
            '_raw_response': True
        })

        self.log.info('Browse results [{0}]'.format(resp))

        for browse_resp in resp['browseResponses']:
            if browse_resp.get('respType', 0) == 2:
                return True

        return False

    def check_log(self, job_obj, text):
        """Checks if the given words are present in IndexServer log"""

        rl_job_id = ' {0} '.format(job_obj.job_id)
        rl_words = [rl_job_id, text]

        return self.idx_tc.check_log_line(
            self.isc, self.isc_machine, 'IndexServer.log', rl_words)
