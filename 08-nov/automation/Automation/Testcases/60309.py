# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This Testcase verifies that single stream synthetic full backup jobs with object based retention is run successfully
and the various versions and deleted items are being carry forwarded after each job.

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    verify_carry_forwarded_files()              -- Verifies if the syn-full job carries the deleted and indicated number
    of versions forward.

    get_versions_file()                         --  Gets a random file to do view all versions

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """This Testcase verifies that single stream synthetic full backup jobs with object based retention
    is run successfully and the various versions and deleted items are being carry forwarded after each job.

        Steps:
             1) Create backupset and subclient
             2) Enable Subclient properties -> Retention -> Extend storage policy retention -> Object based retention.
             3) Delete item retention -> Retain objects indefinitely
             4) File versions -> Retain 3 versions
             5) Create testdata and run FULL
             6) Modify file1, delete file2 run INC
             7) Repeat #6 for 5 jobs
             8) Run single stream SFULL job
             9) Repeat #6 to #7 (but with 2 jobs) and run 2nd SFULL job

"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - Synthetic full - Object based retention'

        self.tcinputs = {
            'StoragePolicy': None,
            'TestDataPath': None,
        }

        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_tc = None

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)

        self.backupset = self.idx_tc.create_backupset(f'{self.id}_sfull_obj_retention', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name=f'sc1_{self.id}',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            register_idx=False
        )

        self.subclient.file_version = {
            'Mode': 2,
            'DaysOrNumber': 3
        }

        self.subclient.backup_retention = True
        self.subclient.backup_retention_days = -1
        self.backupset.idx.register_subclient(self.subclient)
        self.subclient.idx = self.backupset.idx

    def run(self):
        """Contains the core testcase logic, and it is the one executed"""

        self.idx_tc.new_testdata(paths=self.subclient.content, count=4)
        self.idx_tc.run_backup_sequence(
            subclient_obj=self.subclient,
            steps=['Full', 'Edit', 'Incremental', 'Edit', 'Incremental',
                   'Edit', 'Incremental', 'Edit', 'Incremental', 'Edit', 'Incremental'],
            verify_backup=True
        )

        syn_job1 = self.idx_tc.run_backup(
            subclient_obj=self.subclient,
            backup_level='Synthetic_full'
        )

        self.log.info('***** Verifying carry forward from 1st cycle. Job [%s] *****', syn_job1.job_id)
        self.verify_carry_forwarded_files(syn_job1)

        self.idx_tc.run_backup_sequence(
            subclient_obj=self.subclient,
            steps=['Edit', 'Incremental', 'Edit', 'Incremental'],
            verify_backup=True
        )

        syn_job2 = self.idx_tc.run_backup(
            subclient_obj=self.subclient,
            backup_level='Synthetic_full'
        )

        self.log.info('***** Verifying carry forward from 2nd cycle. Job [%s] *****', syn_job2.job_id)
        self.verify_carry_forwarded_files(syn_job2)

    def verify_carry_forwarded_files(self, syn_job_id):
        """For each synthetic full job with object based retention, check if the
        indicated number of versions and the deleted files are carry forwarded """

        self.log.info('Picking a file and verifying for 3 additional versions')
        active_file = self.get_versions_file()
        self.log.info('File picked is [%s]', active_file)

        self.log.info('***** Verifying carry forward of multiple versions *****')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'versions',
            'job_id': syn_job_id.job_id,
            'path': active_file,
            'restore': {
                'do': True,
                'source_items': [active_file],
                'select_version': -1
            }
        })

        self.log.info('***** Verifying carry forward of deleted files *****')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'find',
            'job_id': syn_job_id.job_id,
            'show_deleted': True,
            'restore': {
                'do': True
            }
        })

        self.log.info('Carry forward of extra versions and deleted files is verified')

    def get_versions_file(self):
        """Gets a random file to do view all versions"""

        query = ("select path from indexing where "
                 "type = 'file' and status in ('modified', 'new') and "
                 "name like 'edit_file%' order by jobid desc limit 1")

        response = self.backupset.idx.db.execute(query)
        random_file = ''

        if response.rowcount != 0:
            random_file = response.rows[0][0]
        else:
            raise Exception('No file with versions exists')

        self.log.info(f'Path of the picked up file with versions is {random_file}')

        return random_file
