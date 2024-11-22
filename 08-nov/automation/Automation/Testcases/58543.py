# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that job level validation during index playback works as expected

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    modify_jobs()               --  Modify the job's archive file status to valid/invalid

    tear_down()                 --  Cleans the data created for Indexing validation

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import commonutils

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db


class TestCase(CVTestCase):
    """This testcase verifies that job level validation during index playback works as expected

        Steps:
            1) Assumption - Client is in subclient level index (required since only browse from previous cycle
            does job level validation)
            2) Create a new backupset and subclient
            3) Run FULL --> INC1 --> SFULL --> INC2 --> INC3
            4) Mark the afile of FULL, INC1 and INC2 as invalid in the CS DB
            5) Delete the DB and do FULL reconstruction
            6) FULL, INC1  and INC2 won't be played back to the Index.
            7) Mark INC2 job as valid.
            8) Run SFULL job
            9) The INC2 job should have be played back
            10) Verify SFULL results
            11) Do browse on FULL, INC, now both these jobs should also be played back.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Job level validation'

        self.tcinputs = {
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.index_db = None
        self.jobs = []
        self.export_tables = None
        self.invalidate_jobs = []

    def setup(self):
        """All testcase objects are initialized in this method"""

        try:
            self.cl_machine = Machine(self.client, self.commcell)

            self.idx_tc = IndexingTestcase(self)
            self.idx_help = IndexingHelpers(self.commcell)

            if self.idx_help.get_agent_indexing_level(self.agent) == 'backupset':
                raise Exception('This testcase can work only in client with subclient level index')

            self.backupset = self.idx_tc.create_backupset('JOB_LEVEL_VALIDATION', for_validation=True)

            self.subclient = self.idx_tc.create_subclient(
                name='sc1_job_level_validation',
                backupset_obj=self.backupset,
                storage_policy=self.tcinputs.get('StoragePolicy')
            )

        except Exception as exp:
            self.log.exception(exp)
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:

            self.jobs = self.idx_tc.run_backup_sequence(
                self.subclient, ['new', 'full', 'edit', 'incremental', 'edit',
                                 'synthetic_full', 'edit', 'incremental', 'edit', 'incremental'])

            self.log.info('********** Creating the index DB object **********')
            if self.idx_help.get_agent_indexing_level(self.agent) == 'backupset':
                self.index_db = index_db.get(self.backupset)
            else:
                self.index_db = index_db.get(self.subclient)

            full_job = self.jobs[0]
            inc1_job = self.jobs[1]
            inc2_job = self.jobs[3]

            # Adding FULL, INC1, INC2 to the validate list
            self.invalidate_jobs = [full_job.job_id, inc1_job.job_id, inc2_job.job_id]

            self.log.info(f'***** Jobs picked for invalidation [{self.invalidate_jobs}] *****')

            # Marking jobs as invalid
            self.modify_jobs(self.invalidate_jobs, 'invalid')

            self.log.info('********** Reconstructing the DB after invalidation **********')
            if not self.index_db.reconstruct_db(rename=False):
                raise Exception('Reconstruction of DB failed. Please check.')

            self.log.info('********** Reading image table **********')
            image_table = self.index_db.get_table(table='imageTable')
            self.log.info(f'Image table records {image_table.rows}')
            jobs_in_index = image_table.get_column('JobId')
            self.log.info(f'Jobs in index [{jobs_in_index}]')

            for job in self.invalidate_jobs:
                if job in jobs_in_index:
                    raise Exception(f'Job [{job}] is still in the index. Please check')
                else:
                    self.log.info(f'********** Job [{job}] is not present in the Index **********')

            # Marking jobs as valid
            self.modify_jobs(self.invalidate_jobs, 'valid')

            self.idx_tc.run_backup(self.subclient, 'synthetic_full', verify_backup=False)

            self.log.info('********** Reading image table after SFULL **********')
            image_table.refresh()
            self.log.info(f'Image table records {image_table.rows}')
            jobs_in_index = image_table.get_column('JobId')
            self.log.info(f'Jobs in index [{jobs_in_index}]')

            if inc2_job.job_id in jobs_in_index:
                self.log.info(
                    f'***** Job validation happened. Job [{inc2_job.job_id}] is played back in index by SFULL *****')
            else:
                raise Exception(f'Job [{inc2_job.job_id}] is still missing in the index after SFULL')

            self.log.info('********** Validating browse of first cycle  **********')
            self.backupset.idx.validate_browse_restore({
                'from_time': str(commonutils.get_int(full_job.start_timestamp) - 3),
                'to_time': str(commonutils.get_int(inc1_job.end_timestamp) + 3),
                'restore': {
                    'do': False
                }
            })

            self.log.info('********** Job validation happened. Browse of previous cycle is successful *********')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def modify_jobs(self, job_list, action):
        """Modify the job's archive file status to valid/invalid

            Args:

                job_list    (list)  --  List of job IDs to act on

                action      (str)   --  Action to take. Supported values - valid, invalid

        """

        isvalid = '1' if action == 'valid' else '0'

        for job in job_list:
            self.log.info(f'***** Marking job [{job}] as [{action}] *****')
            self.idx_tc.options_help.update_commserve_db(f"""
                update archfile set isvalid = '{isvalid}' where jobid = '{job}' and fileType = 2
            """)

    def tear_down(self):
        """Cleans the data created for Indexing validation"""
        if self.status == constants.PASSED:
            self.backupset.idx.cleanup()
