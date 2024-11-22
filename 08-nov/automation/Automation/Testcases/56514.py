# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import traceback

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector

from Indexing.tools import idxcli
from Indexing.testcase import IndexingTestcase
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = 'Indexing - Workflow - Load balance index servers'
        self.workflow_name = 'Load Balance Index Servers'

        self._DEBUG = True

        self.old_is = None
        self.new_is = None
        self.idxcli = None
        self.idx_drive = None
        self.idx_fillpath = None
        self.os_windows = None

        self.last_load = False

        self.tcinputs = {
            'StoragePolicy': None,
            'ClientName': None,
        }


    """Setup function of this test case"""
    def setup(self):
        try:
            self.cl_machine = Machine(self.client, self.commcell)
            self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))

            self.idx_tc = IndexingTestcase(self)
            self.options_selector = OptionsSelector(self.commcell)

            # Check if workflow exists
            self.workflow_helper = WorkflowHelper(self, wf_name=self.workflow_name)
            if self.workflow_helper.has_workflow(self.workflow_name):
                self.log.info('Workflow [{0}] found!'.format(self.workflow_name))
            else:
                raise Exception('Workflow [{0}] not found!'.format(self.workflow_name))

            # Check primary drive pool has two valid data paths
            drive_pool_id = self.storage_policy.storage_policy_properties['copy'][0]['drivePool']['drivePoolId']
            data_paths = self.options_selector.exec_commserv_query("SELECT * FROM MMDataPath WHERE DrivePoolId = " + str(drive_pool_id))
            if len(data_paths[0]) < 2:
                raise Exception("No Shared Data Paths for index migration")

            # Create test backupset
            if self._DEBUG:
                self.backupset = self.agent.backupsets.get('load_balance_56514')
            else:
                self.backupset = self.idx_tc.create_backupset('load_balance_56514', for_validation=False)

            # Create test subclient
            if self._DEBUG:
                self.subclient = self.backupset.subclients.get('56514')
            else:
                self.subclient = self.idx_tc.create_subclient(
                    name="56514",
                    backupset_obj=self.backupset,
                    storage_policy=self.storage_policy.name
                )

            # Create test data
            if self._DEBUG == False:
                self.idx_tc.new_testdata(self.subclient.content)

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            self.result_string = str(exp)
            self.status = constants.FAILED
            raise Exception(exp)


    """Run function of this test case"""
    def run(self):
        try:
            self.log.info('Started executing {0} testcase'.format(self.id))

            # Run full backup
            if self._DEBUG == False:
                self.log.info('Running full backup for subclient: {0}'.format(self.subclient))
                self.idx_tc.run_backup(self.subclient, 'Full')

            self.backupset = self.agent.backupsets.get('load_balance_56514')
            self.old_is = self.backupset.index_server
            self.log.info('Backupset {0} using Index {1}'.format(self.backupset.name, self.old_is.client_name))

            # Load index server as Client Machine
            self.log.info('Connecting to Index Server: ' + self.old_is.name)
            _machine = Machine(self.old_is.name, self.commcell)

            if _machine.check_registry_exists('Indexing', 'USE_LAST_LOAD_FOR_METRICS') == False:
                _machine.create_registry('Indexing', 'USE_LAST_LOAD_FOR_METRICS', '1')
            else:
                self.log.info('USE_LAST_LOAD_FOR_METRICS already set')
                self.last_load = True

            # Check Free Space on Index
            self.log.info("Calculating free space on " + _machine.machine_name)
            storage = _machine.get_storage_details()
            self.media_agent = self.old_is
            self.idx_drive = self.media_agent.index_cache_path.split(':')[0]
            idx_freespace = storage[self.idx_drive]['available']
            idx_fillspace = int(idx_freespace - 11500)
            self.log.info("Filling " + str(idx_fillspace))

            if "Windows" in self.old_is.os_info:
                self.os_windows = True
            else:
                self.os_windows = False

            if self.os_windows:
                self.idx_fillpath = self.idx_drive + r":\Automation\load_balance_56514\fill_space.file"

                if _machine.check_directory_exists(self.idx_drive + r":\Automation\load_balance_56514") == False:
                    self.log.info("Creating temp directory")
                    _machine.create_directory(self.idx_drive + r":\Automation\load_balance_56514")
            else:
                self.idx_fillpath = r"/tmp/Automation/load_balance_56514/fill_space.file"

                if _machine.check_directory_exists(r"/tmp/Automation/load_balance_56514") == False:
                    self.log.info("Creating temp directory")
                    _machine.create_directory(r"/tmp/Automation/load_balance_56514")

            # Fill free space
            self.log.info("Creating 'fill' file")
            _machine.create_file(self.idx_fillpath, '1', idx_fillspace * 1024 * 1024) # * 1024(MB) * 1024(GB)

            # IdxCLI calculate metrics for load balance
            self.log.info('Calculate index server metrics')
            self.idxcli = idxcli.IdxCLI(self.old_is)
            load_balance = self.idxcli.do_tools_calculate_metrics()

            if load_balance:
                # Force fill Index Server Load
                self.log.info('Force fill server load for client')
                query = "UPDATE IdxServerLoad SET load='0.9001' WHERE clientId = " + self.old_is.client_id
                self.options_selector.update_commserve_db(query)
            else:
                self.log.error("Failed to run idxcli.do_tools_calculate_metrics()")
                self.result_string = str("Failed to run idxcli.do_tools_calculate_metrics()")
                self.status = constants.FAILED
                raise Exception("Failed to run idxcli.do_tools_calculate_metrics()")

            # Execute Load Balance Index Servers workflow
            self.log.info("Execute Load Balance Workflow")
            self.workflow_helper.execute({
                'storagePolicy': self.storage_policy.name
            })

            # Check if index server moved
            self.backupset.refresh()
            self.new_is = self.backupset.index_server
            self.log.info('Backupset {0} using Index {1}'.format(self.backupset, self.new_is.client_name))

            if self.old_is.client_name != self.new_is.client_name:
                self.log.info("Index server moved from {0} to {1}".format(self.old_is.client_name, self.new_is.client_name))
            else:
                self.log.error("Index server did not migrate")
                self.status = constants.FAILED
                raise Exception("Index server did not migrate")

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            self.result_string = str(exp)
            self.status = constants.FAILED
            raise Exception(exp)


    """Tear down function of this test case"""
    def tear_down(self):
        # Rebalance index load
        self.log.info('Rebalance index server load')
        self.idxcli.do_tools_calculate_metrics()

        # Delete temp dir
        if self.os_windows:
            temp_dir = self.idx_drive + r":\Automation\load_balance_56514"
        else:
            temp_dir = r"/tmp/Automation/load_balance_56514"

        self.log.info("Deleting temp directory [" + temp_dir + "]")
        self.cl_machine.remove_directory(directory_name=temp_dir)

        # Remove registry key
        if self._DEBUG == False:
            if self.last_load == False:
                self.log.info("Delete registry USE_LAST_LOAD_FOR_METRICS")
                self.cl_machine.remove_registry('Indexing', 'USE_LAST_LOAD_FOR_METRICS')
