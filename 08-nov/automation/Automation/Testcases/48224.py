# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

 This Testcase verifies if we have can successful separate restores of various versions of a file

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    get_versions_file()                         --  Gets a random file to do view all versions



"""


from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """
    This Testcase verifies if we have can successful separate restores of various versions of a file

    Steps:
        1) Create backupset and subclient
        2) Run FULL, INC, INC
        3) Pick one file from testdata which has multiple versions during the run
        4) Verify view all versions for the file
        5) From latest cycle browse, restore the individual versions of the file i.e version 1, 2 and 3 in separate jobs
        6) From timerange browse, restore the versions of the file
"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - Individual version restore'
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
        self.backupset = self.idx_tc.create_backupset('version_restore', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='version_restore_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            register_idx=True
        )

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:
            jobs = self.idx_tc.run_backup_sequence(subclient_obj=self.subclient,
                                                   steps=['New', 'Full', 'Edit', 'Incremental', 'Edit', 'Incremental'],
                                                   verify_backup=True
                                                   )
            self.log.info('******* Picking a file and verifying for versions *******')
            active_file = self.get_versions_file()
            result = self.subclient.idx.validate_browse({
                 'operation': 'versions',
                 'path': active_file
            })
            self.log.info('******* Latest browse for all versions of the file *******')
            for version in range(1, len(result[1])+1):
                self.log.info(f'Doing browse and restore validation on version {version} of {active_file}')
                self.idx_tc.verify_browse_restore(self.backupset, {
                    'operation': 'versions',
                    'path': active_file,

                    'restore': {
                        'do': True,
                        'source_items': [active_file],
                        'select_version': version
                    }
                })


            self.log.info('******* Time range browse ********')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'versions',
                'path': active_file,
                'from_time': jobs[0].start_timestamp,
                'to_time': jobs[2].end_timestamp,
                'restore': {
                    'do': True,
                    'source_items': [active_file],
                    'select_version': -1
                }
            })

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def get_versions_file(self):
        """Gets a random file to do view all versions"""

        query = ("select path from indexing where "
                 "type = 'file' and status in ('modified', 'new') and name like 'edit_file%' "
                 "order by jobid desc limit 1")
        response = self.backupset.idx.db.execute(query)
        random_file = ''
        if response.rowcount != 0:
            random_file = response.rows[0][0]
        else:
            raise Exception('No file with versions exists')

        return random_file
