# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

 This Testcase verifies if the 'Load Balance Index Servers' workflow is working as expected for different modes

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    overload_index_server()                     --  Overloads the index server

    run_and_verify_workflow()                   -- Runs the load balance workflow and verifies if
                                                   the index migration happened

    clean_the_load()                            -- Cleans the fill files created to overload the machine

    tear_down()                                 --  tear down function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Indexing.database import index_db
from Indexing.testcase import IndexingTestcase
from Server.Workflow.workflowhelper import WorkflowHelper
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This Testcase verifies if the 'Load Balance Index Servers' workflow is working as expected for different modes

        Steps:
            1) Ensure that the storage storage given as input has multiple datapaths.
            2) Check if the 'Load Balance Index Servers' is a part of the list of workflows.
            3) Create backupset and subclient
            4) Run a Full
            5) Check the available space on index server and fill up the index cache on it accordingly to overload it.
            6) Run workflow in each mode
            7) Ensure that load has been updated successfully in the CSDB and  migration of the index has happened.
            8) Clear the load on the old index server.
            9) Run an INC job and repeat 5,6,7,8 steps for each mode of the workflow.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - Workflow - Load balance index servers -  Modes Validation'
        self.tcinputs = {
            'StoragePolicy': None,
            #  Optional 'ImplicitWait': 150
        }
        self.storage_policy = None
        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_tc = None
        self.workflow_helper = None
        self.options_selector = None
        self.implicit_wait_restart_services = None
        self.idx_help = None
        self.indexing_level = None
        self.index_servers = {}

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

        self.backupset = self.idx_tc.create_backupset('load_balance_workflow', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='load_balance_workflow_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            register_idx=True
        )
        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:
            self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full'],
                verify_backup=True
            )
            self.log.info('Running and verifying the workflow for mode:1 that is for a storage policy')
            self.run_and_verify_workflow(mode=1)
            self.subclient.refresh()
            self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['Edit', 'Incremental'],
                verify_backup=True
            )
            self.log.info('Running and verifying the workflow for mode:2 that is on an index server')
            self.run_and_verify_workflow(mode=2)
            self.subclient.refresh()
            self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['Edit', 'Incremental'],
                verify_backup=True
            )
            self.log.info('Running and verifying the workflow for mode:0 that is on all index servers')
            self.run_and_verify_workflow(mode=0)
            self.log.info('********* SUCCESS, test Case passed for verification of Load Balance Workflow. *********')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def overload_index_server(self):
        """ Identifies the index server and overloads it temporarily to test the working of
            'Load balance Index Servers' workflow
                Returns:
                    old_is (obj)                 -- Old index server client object

                    is_machine (obj)             -- Old index server machine object

                    idx_fill_path (str)          -- Path of the folder used to overload the Index server

                    load_history_filepath (str)  -- Path of load history file
        """
        self.implicit_wait_restart_services = self.tcinputs.get('ImplicitWait', 150)
        idx_db = index_db.get(self.subclient if self.indexing_level == 'subclient' else self.backupset)
        old_is = idx_db.index_server
        index_server = old_is.client_name
        self.log.info('The Current Index Server is %s', index_server)
        self.log.info('Connecting to Index Server Machine: %s', index_server)
        if index_server not in self.index_servers:
            is_machine = Machine(old_is, self.commcell)
            load_history_filepath = is_machine.join_path(
                old_is.log_directory, 'ResourceMonitor', 'IndexCacheStats_*.csv'
            )
            idx_fill_path = is_machine.join_path(idx_db.db_path, 'overload')
            self.index_servers[index_server] = {
                                                      'machine_obj': is_machine,
                                                      'is_obj': old_is,
                                                      'history_file_path': load_history_filepath,
                                                      'fill_path': idx_fill_path
                                                      }
        is_prop = self.index_servers.get(index_server)
        is_machine = is_prop.get('machine_obj')
        load_history_filepath = is_prop.get('history_file_path')
        idx_fill_path = is_prop.get('fill_path')
        idx_fill_filepath = is_machine.join_path(idx_fill_path, 'huge_file')

        if not is_machine.check_registry_exists('Indexing', 'USE_LAST_LOAD_FOR_METRICS'):
            self.log.info('Setting registry key USE_LAST_LOAD_FOR_METRICS with value 1')
            is_machine.create_registry('Indexing', 'USE_LAST_LOAD_FOR_METRICS', '1', 'DWord')
        else:
            self.log.info('USE_LAST_LOAD_FOR_METRICS already set')

        self.log.info('Getting the storage information on %s', is_machine.machine_name)
        # Storage details have to checked separately for Windows and
        # Unix as the Index Cache Path is not under any drive in case of Unix

        if 'Windows' in old_is.os_info:
            idx_drive = idx_db.db_path.split(':')[0]
            storage = is_machine.get_storage_details()
            idx_freespace = storage[idx_drive]['available']
            idx_totalspace = storage[idx_drive]['total']
        elif 'Unix' in old_is.os_info:
            storage = is_machine.get_storage_details(root=True)
            idx_freespace = storage['available']
            idx_totalspace = storage['total']
        else:
            raise Exception('Failed to fetch storage details as machine was not identified')

        idx_seventypercent_space = int((idx_totalspace * 7) / 10)
        idx_usedspace = int(idx_totalspace - idx_freespace)

        if idx_usedspace < idx_seventypercent_space:
            idx_fillspace = idx_seventypercent_space - idx_usedspace
            self.log.info('Filling %d MB space', idx_fillspace)

            if not is_machine.check_directory_exists(idx_fill_path):
                self.log.info('Creating temp overload directory to have fill files in')
                is_machine.create_directory(idx_fill_path)

            self.log.info('Creating fill files')
            each_file_size = int(idx_fillspace/10)
            while idx_fillspace >= each_file_size:
                is_machine.create_file(
                    file_path=f'{idx_fill_filepath}_{idx_fillspace}.txt',
                    content='1',
                    file_size=each_file_size * 1024 * 1024
                )
                idx_fillspace = idx_fillspace - each_file_size

        self.log.info('Deleting the Index Cache Stats file from Resource Monitor to remove the history of load')
        if is_machine.check_file_exists(load_history_filepath):
            is_machine.delete_file(load_history_filepath)

        self.log.info('Restarting services on Index Server')
        old_is.restart_services(implicit_wait=self.implicit_wait_restart_services)
        get_updated_load = f"select * from IdxServerLoad where clientId = '{old_is.client_id}'"
        self.csdb.execute(get_updated_load)
        idx_server_load = self.csdb.fetch_all_rows()[0]
        self.log.info('Current load parameters of the indexserver are %s', idx_server_load)

        if float(idx_server_load[2]) > 0.6:
            self.log.info('Load of overloaded index server updated successfully in CSDB')
        else:
            raise Exception('Load of overloaded index server not updated in CSDB')

        return old_is, is_machine, idx_fill_path, load_history_filepath

    def run_and_verify_workflow(self, mode):
        """Runs the load balance workflow and verifies if the index migration happened
            Args:
                mode              (int)        -- 0 - run workflow for all index servers
                                                  1 - run workflow for the associated storage policy
                                                  2 - run workflow for the assigned index server
        """

        old_is, is_machine, idx_fill_path, load_history_filepath = self.overload_index_server()
        if mode == 1:
            self.log.info(
                'Executing Load Balance Workflow in mode [%s] on storage policy %s', mode, self.storage_policy.name
            )
            wf_args = {"migrationMode": mode, "hiddenStoragePolicyId": self.storage_policy.storage_policy_id}
        elif mode == 2:
            self.log.info(
                'Executing Load Balance Workflow in mode [%s] on index server %s', mode, old_is.client_name
            )
            wf_args = {"migrationMode": mode, "hiddenServerId": old_is.client_id}
        elif mode == 0:
            self.log.info('Executing Load Balance Workflow in mode [%s]', mode)
            wf_args = {"migrationMode": mode}
        else:
            raise Exception(f'mode = {mode} is not a valid workflow mode')

        self.workflow_helper.execute(workflow_json_input=wf_args)
        self.log.info('**** Verifying Migration of Index ****')
        migrated_idx_db = index_db.get(self.subclient if self.indexing_level == 'subclient' else self.backupset)
        new_is = migrated_idx_db.index_server

        if old_is.client_name != new_is.client_name:
            self.log.info('Index server moved from %s to %s', old_is.client_name, new_is.client_name)
        else:
            raise Exception('Index server did not migrate')

        self.clean_the_load(old_is, is_machine, idx_fill_path, load_history_filepath)

    def clean_the_load(self, old_is, is_machine, idx_fill_path, load_history_filepath):
        """Cleaning the fill file used to overload the old index server
            Args:
                old_is (obj)                 -- Old index server client object

                is_machine (obj)             -- Old index server machine object

                idx_fill_path (str)          -- Path of the folder used to overload the Index server

                load_history_filepath (str)  -- Path of load history file
        """

        self.log.info('Clean the fill file that was used to overload')
        if is_machine.check_directory_exists(idx_fill_path):
            is_machine.remove_directory(idx_fill_path)
        if is_machine.check_file_exists(load_history_filepath):
            is_machine.delete_file(load_history_filepath)
        self.log.info('**** Restarting services on the [%s] Index Server to refresh load ****', old_is.client_name)
        old_is.restart_services(implicit_wait=self.implicit_wait_restart_services)

    def tear_down(self):
        """Teardown function of this test case"""
        try:
            if self.status == constants.FAILED:
                self.log.info(' Starting the clean up of the folder used to overload index server machine')
                for idx_server in self.index_servers:
                    is_name = self.index_servers.get(idx_server)
                    is_machine = is_name.get('machine_obj')
                    if is_machine.check_directory_exists(is_name.get('file_path')):
                        is_machine.remove_directory(is_name.get('file_path'))
                        self.log.info('Successfully cleaned the folder used to overload')
                    if is_machine.check_file_exists(is_name.get('history_file_path')):
                        is_machine.delete_file(is_name.get('history_file_path'))
                        self.log.info('Successfully cleaned the load history file')
                    self.log.info('**** Restarting services on the [%s] ****', is_name.get('is_obj').client_name)
                    is_name.get('is_obj').restart_services(implicit_wait=self.implicit_wait_restart_services)
        except Exception as excep:
            self.log.error('Failed to execute teardown with error: %s', excep)
