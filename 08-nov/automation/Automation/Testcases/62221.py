# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

 This Testcase verifies if the 'Load Balance Index Servers' workflow is migrating the right indices.

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    do_backup()                                 --  To run backup for each subclient

    overload_index_server()                     --  Overloads the index server

    run_and_verify_workflow()                   --  Runs the load balance workflow and verifies if
                                                    the index migration happened

    validate_migration()                        --  Validates the migration of indices

    tear_down()                                 --  tear down function of this test case

"""
import threading
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Indexing.database import index_db
from Indexing.testcase import IndexingTestcase
from Server.Workflow.workflowhelper import WorkflowHelper
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This Testcase verifies if the 'Load Balance Index Servers' workflow is migrating the right indices.

        Steps:
            1) Ensure that the storage storage given as input has multiple datapaths.
            2) Check if the 'Load Balance Index Servers' is a part of the list of workflows.
            3) Create multiple backupsets and subclients
            4) Run a Full for each subclient
            5) Check the available space on index server of all these subcleints and fill up the
               index cache on it accordingly to overload it.
            6) Run the load balance workflow
            7) Ensure that load has been updated successfully in the CSDB and the physcial migration of the
             index has happened.
            8) Clear the added the load on all machines.

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - Workflow - Load balance index servers - Index Validation'
        self.tcinputs = {
            'StoragePolicy': None,
            #  Optional 'ImplicitWait': 150
        }
        self.storage_policy = None
        self.backupsets = []
        self.subclients = []
        self.cl_machine = None
        self.idx_tc = None
        self.workflow_helper = None
        self.options_selector = None
        self.implicit_wait_restart_services = None
        self.idx_help = None
        self.indexing_level = None
        self.idx_fill_paths = {}
        self.old_is = None
        self.is_machine = None
        self.load_history_filepath = None
        self.new_is = None
        self.new_is_machine = None
        self.new_is_ma = None
        self.load_history_filepath_new_is = None
        self.dbnames = []
        self.transferred_filepaths = []

    def setup(self):
        """All testcase objects have been initialized in this method"""

        workflow_name = 'Load Balance Index Servers'
        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.options_selector = OptionsSelector(self.commcell)
        self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))
        self.workflow_helper = WorkflowHelper(self, wf_name=workflow_name)

        if not self.workflow_helper.has_workflow(workflow_name):
            raise Exception(f'Workflow {workflow_name}  not found!')

        data_paths_query = f"""
                    SELECT * FROM MMDataPath where copyid in
                    (Select id from archGroupCopy where copy=1 and archgroupid ={self.storage_policy.storage_policy_id})
                """
        self.csdb.execute(data_paths_query)
        data_paths = self.csdb.fetch_all_rows()
        if len(data_paths) < 2:
            raise Exception('No Shared Data Paths for index migration')

        count = 10
        for i in range(0, count):
            self.backupsets.append(self.idx_tc.create_backupset(f'load_balance_workflow_{i}', for_validation=False))
            self.subclients.append(self.idx_tc.create_subclient(
                name=f'load_balance_workflow_sc_{i}',
                backupset_obj=self.backupsets[i],
                storage_policy=self.tcinputs['StoragePolicy'],
                register_idx=False
            ))

        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)



    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:
            threads = []
            for subclient in self.subclients:
                exe_thread = threading.Thread(
                    target=self.do_backup,
                    args=(subclient,)
                )
                exe_thread.start()
                threads.append(exe_thread)
            for exe_thread in threads:
                exe_thread.join()

            self.log.info('Running and verifying the workflow for mode:1 that is for a storage policy')
            self.run_and_verify_workflow()
            self.log.info('********* SUCCESS, test Case passed for verification of Load Balance Workflow. *********')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def do_backup(self, subclient):
        """ Does backup for a given subclient
                Args:
                    subclient             (obj)        -- Subclient object for which the full backup
                                                          job has to be performed
        """

        self.log.info('Starting the Full backup for %s', subclient.name)
        self.idx_tc.run_backup_sequence(
            subclient_obj=subclient,
            steps=['New', 'Full']
        )

    def overload_index_server(self):
        """ Identifies the index server and overloads it temporarily to test the working of
            'Load balance Index Servers' workflow
        """
        self.implicit_wait_restart_services = self.tcinputs.get('ImplicitWait', 150)
        idx_db = index_db.get(self.subclients[0] if self.indexing_level == 'subclient' else self.backupsets[0])
        self.old_is = idx_db.index_server
        index_server = self.old_is.client_name
        self.log.info('The Current Index Server is %s', index_server)
        self.log.info('Connecting to Index Server Machine: %s', index_server)

        self.is_machine = Machine(self.old_is, self.commcell)
        self.load_history_filepath = self.is_machine.join_path(
            self.old_is.log_directory, 'ResourceMonitor', 'IndexCacheStats_*.csv'
        )

        for i in range(0, len(self.subclients)):
            idx_db = index_db.get(self.subclients[i] if self.indexing_level == 'subclient' else self.backupsets[i])
            sc_id = self.subclients[i].subclient_id
            idx_fill_path = self.is_machine.join_path(idx_db.db_path, f'huge_file_{sc_id}.txt')
            self.idx_fill_paths[idx_db.db_guid] = {
                'full_file_path': idx_fill_path,
                'file_name': f'huge_file_{sc_id}.txt',
                'backupset_guid': idx_db.backupset_guid
            }

        if not self.is_machine.check_registry_exists('Indexing', 'USE_LAST_LOAD_FOR_METRICS'):
            self.log.info('Setting registry key USE_LAST_LOAD_FOR_METRICS with value 1')
            self.is_machine.create_registry('Indexing', 'USE_LAST_LOAD_FOR_METRICS', '1', 'DWord')
        else:
            self.log.info('USE_LAST_LOAD_FOR_METRICS already set')

        self.log.info('Getting the storage information on %s', self.is_machine.machine_name)
        # Storage details have to checked separately for Windows and
        # Unix as the Index Cache Path is not under any drive in case of Unix

        if 'Windows' in self.old_is.os_info:
            idx_drive = idx_db.db_path.split(':')[0]
            storage = self.is_machine.get_storage_details()
            idx_freespace = storage[idx_drive]['available']
            idx_totalspace = storage[idx_drive]['total']
        elif 'Unix' in self.old_is.os_info:
            storage = self.is_machine.get_storage_details(root=True)
            idx_freespace = storage['available']
            idx_totalspace = storage['total']
        else:
            raise Exception('Failed to fetch storage details as machine was not identified')

        idx_seventypercent_space = int((idx_totalspace * 95) / 100)
        idx_usedspace = int(idx_totalspace - idx_freespace)
        if idx_usedspace < idx_seventypercent_space:
            idx_fillspace = idx_seventypercent_space - idx_usedspace
            self.log.info('Filling %d MB space', idx_fillspace)

            self.log.info('Creating fill files')
            each_file_size = int(idx_fillspace / len(self.subclients))
            for each_path in self.idx_fill_paths:
                if idx_fillspace >= each_file_size:
                    self.is_machine.create_file(
                        file_path=self.idx_fill_paths[each_path]['full_file_path'],
                        content='1',
                        file_size=each_file_size * 1024 * 1024
                    )
                    idx_fillspace = idx_fillspace - each_file_size


        self.log.info('Deleting the Index Cache Stats file from Resource Monitor to remove the history of load')
        if self.is_machine.check_file_exists(self.load_history_filepath):
            self.is_machine.delete_file(self.load_history_filepath)

        self.log.info('Restarting services on Index Server')
        self.old_is.restart_services(implicit_wait=self.implicit_wait_restart_services)
        get_updated_load = f"select * from IdxServerLoad where clientId = '{self.old_is.client_id}'"
        self.csdb.execute(get_updated_load)
        idx_server_load = self.csdb.fetch_all_rows()[0]
        self.log.info('Current load parameters of the indexserver are %s', idx_server_load)

        if float(idx_server_load[2]) > 0.6:
            self.log.info('Load of overloaded index server updated successfully in CSDB')
        else:
            raise Exception('Load of overloaded index server not updated in CSDB')

    def run_and_verify_workflow(self):
        """Runs the load balance workflow and verifies if the index migration happened"""

        self.overload_index_server()
        mode = 1  #run workflow for the associated storage policy
        self.log.info(
            'Executing Load Balance Workflow in mode [%s] on storage policy %s', mode, self.storage_policy.name
        )
        wf_args = {"migrationMode": mode, "hiddenStoragePolicyId": self.storage_policy.storage_policy_id}

        wf_job = self.workflow_helper.execute(workflow_json_input=wf_args)

        self.log.info('**** Verifying Migration of Index ****')
        get_migration_list = f"select indexId, toClientId from IdxServerMigrations" \
                             f" where jobId='{wf_job.job_id}' and isMigrated = 1"
        self.csdb.execute(get_migration_list)
        migrated_indices = self.csdb.fetch_all_rows()
        self.log.info(migrated_indices)
        if not migrated_indices:
            raise Exception('No Index has been Migrated')

        get_new_is = f"select name from APP_Client where id = '{migrated_indices[0][1]}' "
        self.csdb.execute(get_new_is)
        new_is_name = self.csdb.fetch_all_rows()[0][0]
        self.new_is = self.commcell.clients.get(new_is_name)
        self.new_is_machine = Machine(new_is_name, self.commcell)
        self.new_is_ma = self.commcell.media_agents.get(new_is_name)
        self.load_history_filepath_new_is = self.new_is_machine.join_path(
            self.new_is.log_directory, 'ResourceMonitor', 'IndexCacheStats_*.csv'
        )

        for each_index in migrated_indices:
            get_dbname = f"select dbName from App_IndexDBInfo where id='{each_index[0]}'"
            self.csdb.execute(get_dbname)
            dbname = self.csdb.fetch_all_rows()[0][0]
            self.dbnames.append(dbname)
        self.log.info('Migrated indices are :%s', self.dbnames)
        self.validate_migration()

    def validate_migration(self):
        """ Validates the physical migration of the indices"""
        for each_dbname in self.dbnames:
            self.log.info(' Checking if the db: %s, has been migrated', each_dbname)
            if each_dbname in self.idx_fill_paths:
                new_file_path = self.new_is_machine.join_path(
                   self.new_is_ma.index_cache_path,
                   self.idx_fill_paths[each_dbname]['backupset_guid'],
                   each_dbname,
                   self.idx_fill_paths[each_dbname]['file_name']
                )
                if self.new_is_machine.check_file_exists(new_file_path):
                    self.transferred_filepaths.append(new_file_path)
                    self.log.info('Migration of %s db has been verified', each_dbname)
                else:
                    self.log.info('The file at %s does not exist', new_file_path )
                    raise Exception(f'Migration of {each_dbname} db has failed')

    def tear_down(self):
        """To clean the added load on both old and new Index servers"""
        try:
            for i in range(0, len(self.subclients)):
                idx_db = index_db.get(self.subclients[i] if self.indexing_level == 'subclient' else self.backupsets[i])
                idx_db.delete_db()

            for each_file in self.transferred_filepaths:
                if self.new_is_machine.check_file_exists(each_file):
                    self.new_is_machine.delete_file(each_file)
                if self.is_machine.check_file_exists(each_file):
                    self.is_machine.delete_file(each_file)

            self.log.info('Deleting the Index Cache Stats file from Resource Monitor of Old Index Server')
            if self.is_machine.check_file_exists(self.load_history_filepath):
                self.is_machine.delete_file(self.load_history_filepath)
            self.log.info('Restarting services on Old Index Server')
            self.old_is.restart_services(implicit_wait=self.implicit_wait_restart_services)

            self.log.info('Deleting the Index Cache Stats file from Resource Monitor of New Index Server')
            if self.new_is_machine.check_file_exists(self.load_history_filepath_new_is):
                self.new_is_machine.delete_file(self.load_history_filepath_new_is)
            self.log.info('Restarting services on new Index Server')
            self.new_is.restart_services(implicit_wait=self.implicit_wait_restart_services)
        except Exception as e:
            self.log.error('Failed to unload the old and new index servers: [%s]', e)
