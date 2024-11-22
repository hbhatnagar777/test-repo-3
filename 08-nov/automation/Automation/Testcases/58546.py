# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that during backup job media agent fail over happens and archive index is gathering all the logs
from the backup MAs

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    get_job_media_agent()       --  Queries the active MA used by the job

    tear_down()                 --  Cleans the data created for Indexing validation

"""

import time

from cvpysdk.storage import MediaAgents

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.commonutils import get_int

from Server.JobManager.jobmanager_helper import JobManager

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db


class TestCase(CVTestCase):
    """This testcase verifies that media agent fail over works as expected

        Steps:
            1) Have a storage policy with two data paths.
                a) Each data path having different MAs (grid store configuration)
                b) Data path configuration be "round robin"
            2) Prepare a huge dataset to backup the client manually.
            3) Create a backupset, subclient
            4) Set the subclient content to the already existing data.
            5) Run a FULL  backup
            6) When job is in backup phase, suspend the job
            7) Mark the active MA (example MA1 as offline)
            8) Resume the backup job
            9) Verify if job is running in new MA.
            10) Repeat steps 6 - 9 couple of times.
            10) Wait for job to complete.
            11) Verify if job completes successfully with no errors.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - MediaAgent failover'

        self.tcinputs = {
            'Testdata': None,
            'RestoreLocation': None,
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.testdata = None
        self.restore_location = None

        self.media_agents = None
        self.to_disable_ma = None

        self.full_job = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        try:
            self.cl_machine = Machine(self.client, self.commcell)

            self.testdata = self.tcinputs.get('Testdata')
            self.restore_location = self.tcinputs.get('RestoreLocation')

            self.idx_tc = IndexingTestcase(self)
            self.idx_help = IndexingHelpers(self.commcell)

            self.backupset = self.idx_tc.create_backupset('MA_FAILOVER', for_validation=False)

            self.subclient = self.idx_tc.create_subclient(
                name='sc1_ma_failover',
                backupset_obj=self.backupset,
                storage_policy=self.tcinputs.get('StoragePolicy'),
                content=[self.testdata]
            )

            self.media_agents = MediaAgents(self.commcell)

            self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)

        except Exception as exp:
            self.log.exception(exp)
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic"""
        try:

            self.full_job = self.subclient.backup('Full')

            jm_obj = JobManager(self.full_job)
            jm_obj.wait_for_phase('backup')

            failover_attempts = get_int(self.tcinputs.get('FailoverAttempts'), 2)

            for attempt in range(failover_attempts):
                self.log.info(f'***** Failover attempt [{attempt+1}/{failover_attempts}] *****')
                time.sleep(10)

                if self.to_disable_ma:
                    self.log.info(f'Marking previously used MA [{self.to_disable_ma.media_agent_name}] as enabled')
                    self.to_disable_ma.set_state(True)

                if self.full_job.is_finished:
                    self.log.error('Job already completed ahead (before doing failover)')
                    break

                self.full_job.pause(wait_for_job_to_pause=True)
                self.log.info('Job is suspended')

                if self.full_job.is_finished:
                    self.log.error('Job already completed ahead (after suspend)')
                    break
                else:
                    self.to_disable_ma = self.get_job_media_agent(self.full_job)

                self.log.info(f'Marking MA [{self.to_disable_ma.media_agent_name}] as disabled')
                self.to_disable_ma.set_state(False)

                self.full_job.resume(wait_for_job_to_resume=True)
                self.log.info('Job is resumed')

                if self.full_job.is_finished:
                    self.log.error('Job already completed ahead (after resume)')
                    break
                else:
                    new_ma = self.get_job_media_agent(self.full_job)

                if new_ma.media_agent_name == self.to_disable_ma.media_agent_name:
                    raise Exception('MediaAgent did not failover. Exiting')
                else:
                    self.log.info(f'***** MediaAgent failover happened. New MA [{new_ma.media_agent_name}] *****')

            if self.full_job.is_finished:
                self.log.error('Job already completed ahead')
            else:
                jm_obj.wait_for_state('completed')

            if self.to_disable_ma:
                self.log.info(f'Marking previously used MA [{self.to_disable_ma.media_agent_name}] as enabled')
                self.to_disable_ma.set_state(True)

            self.log.info('********** Job completed successfully after multiple failovers **********')

            self.idx_tc.cv_ops.subclient_restore_out_of_place(
                client=self.client,
                destination_path=self.restore_location,
                paths=[self.testdata],
                subclient=self.subclient
            )

            files_source = self.cl_machine.number_of_items_in_folder(
                self.testdata, recursive=True, include_only='files')

            files_destination = self.cl_machine.number_of_items_in_folder(
                self.restore_location, recursive=True, include_only='files')

            self.log.info(f'Number of files source [{files_source}] destination [{files_destination}]')

            if files_destination == files_source:
                self.log.info('All files are restored. Backup is intact')
            else:
                raise Exception('Mismatch in number of files restored')

            self.full_job = None

            self.log.info('***** Getting IndexServer for the backupset *****')
            idx_db = index_db.get(self.subclient if self.indexing_level == 'subclient' else self.backupset)

            self.log.info('********** Trying log restore and playback **********')
            if not idx_db.reconstruct_db(rename=True, delete_logs=True, total_browse_attempts=2):
                raise Exception('Index did not get up to date by full reconstruction after deleting db and logs.')

            self.log.info('Index is up to date after full reconstruction')

            self.log.info('********** MA failover automation passed *********')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

        finally:
            if self.to_disable_ma:
                self.log.info('********** Marking the MA online **********')
                self.to_disable_ma.set_state(True)

            if self.full_job and not self.full_job.is_finished:
                self.log.info('********** FULL job is stuck for some reason. Killing it **********')
                self.full_job.kill(wait_for_job_to_kill=True)

    def get_job_media_agent(self, the_job):
        """Queries the active MA used by the job

            Args:
                the_job     (obj)       --  The CvPySDK job object

            Returns:
                (obj)   --  The MA CvPySDK object

            Raises:
                Exception, if no MA is set for the job

        """

        attempts = 1
        total_attempts = 3

        while attempts <= total_attempts:
            self.log.info(f'Attempt [{attempts}/{total_attempts}] in fetching active MA')

            get_ma_query = f"select shortMediaAgent from JMJobInfo where jobId = '{the_job.job_id}'"
            self.log.info(f'Querying the MA used by job [{get_ma_query}]')

            self.csdb.execute(get_ma_query)
            row = self.csdb.fetch_one_row()

            self.log.info(f'Active MA now {row}')

            if not row[0]:
                self.log.error('MA is not yet set after resume. Trying again.')
                attempts += 1
                time.sleep(5)
                continue

            ma_obj = self.media_agents.get(row[0])
            return ma_obj

        raise Exception('All attempts exhausted. Cannot get the active MA used by job')

    def tear_down(self):
        """Cleans the data created during the testcase"""

        if self.cl_machine and self.restore_location and self.status == constants.PASSED:
            self.log.info('Deleting restore directory')
            try:
                self.cl_machine.remove_directory(self.restore_location)
            except Exception as exp:
                self.log.error('Exception while deleting the restore directory')
