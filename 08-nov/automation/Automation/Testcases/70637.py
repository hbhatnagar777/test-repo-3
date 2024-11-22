# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Main file for executing this test case

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  Initialize TestCase class

    setup()                                 --  Setup function of this test case

    run()                                   --  Run function of this test case

    change_index_server()                   --  Changes index server from MA1 to MA2

    verify_rfc_files()                      --  Fetches the rfc server for the job and verifies
                                                the RFC upload on the server

    verify_index_files()                    --  Verifies IDX_DB, Idxlogs & RFC files in index server


"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db
from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """
    This testcase verifies that whenever the index server is changed, a catalog migration job is
    started which migrates all index DBs, logs and RFC.

    Steps:
        1. Associate the subclient to a storage policy with two datapath MAs.
        3. Run a sequence of jobs for the subclient with MA1 as the index server.
        4. Check that index DB, action logs & RFC for subclient are created in index cache on MA1.
        5. Change the index server from MA1 to MA2 and verify it.
        6. Verify that a catalog migration job runs and completes.
        7. After the job completes, Verify that index DB, action logs and RFC for this subclient are
         all moved to index cache on MA2.

"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = 'Indexing - Catalog migration on IndexServer change'
        self.tcinputs = {
            'StoragePolicy': None
        }
        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_db = None
        self.idx_help = None
        self.idx_tc = None
        self.sp_primary_copy = None
        self.indexing_level = None

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        storage_policy_name = self.tcinputs.get('StoragePolicy')
        self.backupset = self.idx_tc.create_backupset(
            name='70637_catalog_migration',
            for_validation=True)
        storage_policy = self.commcell.storage_policies.get(storage_policy_name)
        self.sp_primary_copy = storage_policy.get_primary_copy()

        self.subclient = self.idx_tc.create_subclient(
            name='catalog_migration_sc',
            backupset_obj=self.backupset,
            storage_policy=storage_policy_name,
            register_idx=True
        )
        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)

    def run(self):
        """Contains the core testcase logic, and it is the one executed"""
        try:
            self.log.info('************* Running backup job *************')
            full_job = self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full'],
                verify_backup=True
            )
            self.log.info('Full Backup Job completed successfully')
            job_id = full_job[0].job_id

            self.log.info('*** Verifying index files ***')
            self.verify_index_files(job_id)

            self.log.info('***** Changing IndexServer *****')
            new_indexserver = self.change_index_server()

            self.log.info('*** Verifying the changed Index server in csdb ***')
            query = ("SELECT currentIdxServer from app_IndexDBinfo where dbName = '" +
                     self.subclient.subclient_guid + "'")
            self.csdb.execute(query)
            row = self.csdb.fetch_one_row()
            if row[0] == new_indexserver.client_id:
                self.log.info('Index server change is verfied.')
            else:
                raise Exception('ERROR--- Index server is not changed')

            self.log.info('*** Verifying index files on new index server [%s] ***',
                          new_indexserver.client_name)
            self.verify_index_files(job_id)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def change_index_server(self):
        """Changes the IndexServer MA for the backupset/subclient"""

        self.log.info(
            'Fetching all datapath MAs of the primary copy of the subclient storage policy')
        get_all_datapath_mas = f"""select name from app_client where id in (select distinct 
                                HostClientId from MMdatapath where 
                                copyid = {self.sp_primary_copy.get_copy_id()})"""
        self.csdb.execute(get_all_datapath_mas)
        datapath_mas = self.csdb.fetch_all_rows()
        if len(datapath_mas) < 2:
            raise Exception('There are no 2 or more unique datapaths available for storage policy.')
        self.log.info('All unique datapth MAs for the storage policy-- %s', str(datapath_mas))

        entity_obj = self.subclient if self.indexing_level == 'subclient' else self.backupset
        entity_obj.refresh()
        old_ma = entity_obj.index_server.client_name
        self.log.info('Current IndexServer MA is [%s]', old_ma)
        if old_ma == datapath_mas[0]:
            new_indexserver = datapath_mas[1][0]
        else:
            new_indexserver = datapath_mas[0][0]

        self.log.info('Changing IndexServer to [%s]', new_indexserver)
        entity_obj.index_server = self.commcell.clients.get(new_indexserver)
        time.sleep(100)
        active_jobs = self.commcell.job_controller.active_jobs().items()
        for jid, data in active_jobs:
            if data['operation'] == 'Catalog Migration':
                self.log.info('Catalog migration job with jobid %s is running.', jid)
                job_obj = self.commcell.job_controller.get(jid)
                self.log.info('waiting for job %s to complete.', jid)
                job_obj.wait_for_completion()
                break

        entity_obj.refresh()
        new_ma = entity_obj.index_server
        if old_ma != new_ma.client_name:
            self.log.info('IndexServer is changed to [%s]', new_ma.client_name)
            return new_ma
        raise Exception("ERROR--- Index server is not changed")

    def verify_rfc_files(self, job_id):
        """ Fetches the rfc server for the job and verifies the RFC upload on the server

            Args:
                    job_id  (str)   --   Job ID of the job for which RFC upload has to be verified

        """
        self.log.info('***** Verifying for the uploaded rfc files for job ******')
        rfc_server = self.idx_help.get_rfc_server(job_id=job_id)
        rfc_server_name = rfc_server.name
        self.log.info('RFC server for the job id: %s is %s', job_id, rfc_server_name)
        rfc_server_machine = Machine(rfc_server_name, self.commcell)
        rfc_folder = self.idx_db.get_rfc_folder_path(rfc_server_machine=rfc_server_machine,
                                                     job_id=job_id)

        if rfc_server_machine.check_directory_exists(rfc_folder):
            rfc_files = rfc_server_machine.get_files_in_path(rfc_folder)
            self.log.info('RFC files under %s with size: %s Bytes', rfc_folder,
                          rfc_server_machine.get_folder_size(rfc_folder, in_bytes=True))
            if len(rfc_files) != 0:
                self.log.info('Upload of the RFC verified at %s', rfc_folder)
                return True
            return False
        return False

    def verify_index_files(self, job_id):
        """ Verifies IDX_DB, Idxlogs and RFC files in index server

               Args:
                    job_id  (str)   --   Job ID of the job for which RFC upload has to be verified

        """
        self.idx_db = index_db.get(self.subclient if self.indexing_level == 'subclient' else
                                   self.backupset)

        self.log.info('Index server for Backup is---- %s', self.idx_db.index_server.client_name)
        idx_folder_size = self.idx_db.isc_machine.get_folder_size(self.idx_db.db_path)
        if self.idx_db.db_exists and idx_folder_size != 0:
            self.log.info('Index DB for subclient %s exists in the cache with size: %s MBs.',
                          self.subclient.name, idx_folder_size)
        else:
            raise Exception('Index DB for subclient %s does not exist in the cache OR it is empty.',
                            self.subclient.name)

        logs = self.idx_db.get_logs_in_cache(job_id_only=True)
        if job_id in logs:
            job_logs_folder = self.idx_db.isc_machine.join_path(self.idx_db.logs_path, 'J' + job_id)
            logs_folder_size = self.idx_db.isc_machine.get_folder_size(job_logs_folder,
                                                                       in_bytes=True)
            if logs_folder_size != 0:
                self.log.info('Existence of action logs for job id %s is verified in the cache with'
                              ' size: %s Bytes', job_id, logs_folder_size)
            else:
                raise Exception('Verification failed for existence of Action logs, folder is empty '
                                'with job id %s.', job_id)
        else:
            raise Exception('Verification failed for existence of Action logs, no logs exist for '
                            'job id %s.', job_id)

        if self.verify_rfc_files(job_id):
            self.log.info('Existence of RFC files for the job id %s is verified in the cache.',
                          job_id)
        else:
            raise Exception('Verification failed for existence of RFC files, no RFC Files exist for'
                            ' job id %s', job_id)
