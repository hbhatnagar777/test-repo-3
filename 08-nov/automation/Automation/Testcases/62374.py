# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

     This Testcase verifies that all the operations like upload, backup and download of the RFC framework
    are working successfully.

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    check_for_rfc_backup()                      -- Checks if RFC files have been backed up by checking the
                                                   presence of valid rfc afile for the job.

    verify_rfc_upload()                         -- Fetches the rfc server and verifies rfc upload on it

    verify_rfc_download()                       -- Verifies the rfc download by performing a live browse

    validate_rfc_for_a_job()                    -- Verifies upload, backup and download of RFC in one for a job

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.testcase import IndexingTestcase
from Indexing.database import index_db
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """
    This Testcase verifies that all the operations like upload, backup and download of the RFC framework
    are working successfully.

    Steps:

        1. Create a backupset and subclient
        2. Run a block level Full job.
        3. Get the RFC server and verify the upload of RFC files
        4. Verify the backup of RFC files.
        5. Do a live browse and verify the download.
        6. Run a series of INC and SFULL
        7. Verify upload of RFC from each
        8. Verify the carry forward of the RFC files from previous INC to SFULL
        9. Do a browse and verify download of RFC from SFULL.

"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - RFC - Acceptance'
        self.tcinputs = {
            'StoragePolicy': None,
            'TestDataPath': None,

        }
        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.idx_db = None
        self.indexing_level = None
        self.storage_policy = None
        self.sp_primary_copy = None
        self.default_ma_machine = None
        self.rfc_servers = {}

    def setup(self):
        """All testcase objects have been initialized in this method"""
        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.backupset = self.idx_tc.create_backupset('rfc_acceptance', for_validation=False)
        self.subclient = self.idx_tc.create_subclient(
            name='rfc_acceptance_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            content=[self.tcinputs['TestDataPath']],
            register_idx=True
        )
        self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))
        self.sp_primary_copy = self.storage_policy.get_primary_copy()

        self.log.info('Enabling BlockLevel Option')
        self.subclient.block_level_backup_option = 1
        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:
            test_data_folder = self.cl_machine.join_path(self.subclient.content[0], 'testdata')
            self.log.info(test_data_folder)
            if self.cl_machine.check_directory_exists(directory_path=test_data_folder):
                self.cl_machine.remove_directory(directory_name=test_data_folder)
            self.cl_machine.create_directory(directory_name=test_data_folder)

            self.idx_tc.new_testdata(paths=test_data_folder, count=3)
            full1_cy1 = self.idx_tc.run_backup(
                subclient_obj=self.subclient,
                backup_level='Full',
                verify_backup=False
            )
            full1_cy1_id = full1_cy1.job_id

            self.idx_db = index_db.get(self.subclient if self.indexing_level == 'subclient' else self.backupset)
            ma_for_download = self.sp_primary_copy.media_agent
            if ma_for_download not in self.rfc_servers:
                self.default_ma_machine = Machine(ma_for_download, self.commcell)
                self.rfc_servers[ma_for_download] = self.default_ma_machine
            else:
                self.default_ma_machine = self.rfc_servers.get(ma_for_download)
            self.validate_rfc_for_a_job(job_id=full1_cy1_id)

            self.idx_tc.edit_testdata(paths=test_data_folder)
            inc1_cy1 = self.idx_tc.run_backup(
                subclient_obj=self.subclient,
                backup_level='Incremental',
                verify_backup=False
            )
            inc1_cy1_id = inc1_cy1.job_id
            self.validate_rfc_for_a_job(job_id=inc1_cy1_id)

            self.idx_tc.edit_testdata(paths=test_data_folder)
            inc2_cy1 = self.idx_tc.run_backup(
                subclient_obj=self.subclient,
                backup_level='Incremental',
                verify_backup=False
            )
            inc2_cy1_id = inc2_cy1.job_id
            self.validate_rfc_for_a_job(job_id=inc2_cy1_id)

            sfull1_cy1 = self.idx_tc.run_backup(
                subclient_obj=self.subclient,
                backup_level='Synthetic_full',
                verify_backup=False
            )
            sfull1_cy1_id = sfull1_cy1.job_id
            self.validate_rfc_for_a_job(job_id=sfull1_cy1_id)

            self.idx_tc.edit_testdata(paths=test_data_folder)
            inc1_cy2 = self.idx_tc.run_backup(
                subclient_obj=self.subclient,
                backup_level='Incremental',
                verify_backup=False
            )
            inc1_cy2_id = inc1_cy2.job_id
            self.validate_rfc_for_a_job(job_id=inc1_cy2_id)

            sfull1_cy2 = self.idx_tc.run_backup(
                subclient_obj=self.subclient,
                backup_level='Synthetic_full',
                verify_backup=False
            )
            sfull1_cy2_id = sfull1_cy2.job_id
            self.validate_rfc_for_a_job(job_id=sfull1_cy2_id)

            inc1_cy3 = self.idx_tc.run_backup(
                subclient_obj=self.subclient,
                backup_level='Incremental',
                verify_backup=False
            )
            inc1_cy3_id = inc1_cy3.job_id
            self.validate_rfc_for_a_job(job_id=inc1_cy3_id)

            sfull1_cy3 = self.idx_tc.run_backup(
                subclient_obj=self.subclient,
                backup_level='Synthetic_full',
                verify_backup=False
            )
            sfull1_cy3_id = sfull1_cy3.job_id
            self.validate_rfc_for_a_job(job_id=sfull1_cy3_id)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def check_for_rfc_backup(self, job_id):
        """ To verify if the rfc arch file for a job exists """

        self.log.info('********** Checking if RFC afile is created **********')
        query = "SELECT * FROM archFile WHERE fileType = 7 AND isValid = 1 AND jobId =" + job_id
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        if not row[0]:
            raise Exception(f'Job ID {job_id} did not contain RFC_AFILE')

        self.log.info('RFC afile is created')
        self.log.info('Backup of RFC files verified')

    def verify_rfc_upload(self, job_id):
        """ Fetches the rfc server for the job and verifies the RFC upload on the server """

        rfc_server = self.idx_help.get_rfc_server(job_id=job_id)
        rfc_server_name = rfc_server.name
        if rfc_server_name not in self.rfc_servers:
            rfc_server_machine = Machine(rfc_server_name, self.commcell)
            self.rfc_servers[rfc_server_name] = rfc_server_machine
        else:
            rfc_server_machine = self.rfc_servers.get(rfc_server_name)

        rfc_folder = self.idx_db.get_rfc_folder_path(rfc_server_machine, job_id)

        self.log.info('***** Checking for the uploaded rfc folder of the FULL job ******')
        if rfc_server_machine.check_directory_exists(rfc_folder):
            rfc_files = rfc_server_machine.get_files_in_path(rfc_folder)
            self.log.info('RFC files are %s', rfc_files)
            if len(rfc_files) != 0:
                self.log.info('Upload of the RFC verified for job: %s', job_id)
            else:
                raise Exception(f'Upload of RFC failed, no files in the RFC folder for job: {job_id}')
        else:
            raise Exception(f'RFC folder doesnt exist for job: {job_id}')

    def verify_rfc_download(self, job_id):
        """ Does a live browse and verifies the download of rfc """

        self.log.info(' Verify download for job: %s from ma: %s', job_id, self.default_ma_machine.machine_name)
        rfc_folder_for_download = self.idx_db.get_rfc_folder_path(self.default_ma_machine, job_id)

        if not self.default_ma_machine.check_directory_exists(rfc_folder_for_download):
            self.log.info('RFC folder on this ma is not present')
        else:
            self.default_ma_machine.remove_directory(rfc_folder_for_download)
            self.log.info('Deleting the existing folder')

        self.log.info('Do browse to verify download of RFC')
        try:
            self.subclient.browse(path=f'\\{self.subclient.content[0]}')
        except Exception:
            self.log.info('Live browse is taking time to fetch results, avoiding the time out error')

        if self.default_ma_machine.check_directory_exists(rfc_folder_for_download):
            downloaded_rfc_files = self.default_ma_machine.get_files_in_path(rfc_folder_for_download)
            self.log.info('Downloaded RFC files are %s', downloaded_rfc_files)
            if len(downloaded_rfc_files) != 0:
                self.log.info(' RFC folder is restored to complete download for live browse')
            else:
                raise Exception(f' Downloaded RFC folder has no RFC files at {rfc_folder_for_download}')
        else:
            raise Exception('Failed to verify download operation')

    def validate_rfc_for_a_job(self, job_id):
        """ Verifies upload, backup and download of RFC in one for a job  """

        self.verify_rfc_upload(job_id=job_id)
        self.log.info('***** Verifying RFC backup for the job: %s *****', job_id)
        self.check_for_rfc_backup(job_id=job_id)
        self.verify_rfc_download(job_id=job_id)
