# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case

    run_failover()         --  Runs failover of cluster node

"""
from time import sleep
from AutomationUtils import machine
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper

class TestCase(CVTestCase):

    """Class for executing FS Cluster Data Protection - Full,Incremental,Synthfull
        This test case does the following
        Step1, Create backupset for this testcase if it doesn't exist.
            Step2, For each of the allowed scan type
                    do the following on the backupset
                Step3, For each of the allowed index_type (Meta data colection Enabled/Not)
                    do the following on the backupset
                        Step3.1,  Create subclient for the scan type if it doesn't exist and enable
                        blocklevel and metadat collection options.
                        Step3.2, Add full data for the current run.
                        Step3.3, Run a full backup for the subclient
                            and verify it completes without failures.
                        Step3.4, Run a Volume level Restore
                            and verify correct data is restored.
                        Step3.5, Run a File level Restore
                            and verify correct data is restored.
                        Step 3.6, Run Failover
                        Step3.6, Add new data for the incremental-1
                        Step3.7, Run an incremental backup for the subclient
                            and verify it completes without failures.
                        Step3.8, Run a Volume level Restore
                            and verify correct data is restored.
                        Step3.9, Run a File level Restore
                            and verify correct data is restored.
                        Step3.10, Add new data for the incremental-2
                        Step3.11, Run an incremental backup for the subclient
                            and verify it completes without failures.
                        Step3.12, Run a Volume level Restore
                            and verify correct data is restored.
                        Step3.13, Run a File level Restore
                            and verify correct data is restored
                        Step 3.14, Run Failover
                        Step3.15, Run an incremental-3 backup for the subclient
                            and verify it completes without failures.
                        Step3.16, Run a Volume level Restore
                            and verify correct data is restored.
                        Step3.17, Run a File level Restore
                            and verify correct data is restored.
                        Step3.18, Add new data for the incremental
                        Step3.19, Run an incremental-4 backup for the subclient
                            and verify it completes without failures.
                        Step3.20, Run a Volume level Restore
                            and verify correct data is restored.
                        Step3.21, Run a File level Restore
                            and verify correct data is restored
                        Step 3.22, Run Failover
                        Step3.23, Run an incremental-5 backup for the subclient
                            and verify it completes without failures.
                        Step3.24, Run a Volume level Restore
                            and verify correct data is restored.
                        Step3.25, Run a File level Restore
                            and verify correct data is restored.
                        Step3.26, Run an synthfull for the subclient and
                            verify it completes without failures
                        Step3.27, Run a Volume level Restore
                            and verify correct data is restored.
                        Step3.28, Run a File level Restore
                            and verify correct data is restored.
    """
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Windows FS  Cluster Data Protection"\
            " - Full,Incremental,Synthetic Full"
        self.tcinputs = {
            "TestPath": None,
            "TestPath2": None,
            "TestPath3": None,
            "RestorePath": None,
            "StoragePolicyName": None
        }
        self.client_name = ""
        self.client_machine = None
        self.runid = ""
        self.slash_format = ""
        self.test_path = ""
        self.test_path2 = ""
        self.test_path3 = ""
        self.restore_path = ""
        self.storage_policy = None
        self.verify_dc = None
        self.wait_time = 30
        self.active_node = None
        self.passive_node = None
        self.node1_machine = None
        self.node2_machine = None
        self.node1 = None
        self.node2 = None
        self.helper = FSHelper(TestCase)

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)
            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.log.info(""" Blocklevel  Data Protection - Full,Incremental,Synthfull
                    This test case does the following
                    Step1, Create backupset for this testcase if it doesn't exist.
                        Step2, For each of the allowed scan type
                                do the following on the backupset
                        Step3.1,  Create subclient for the scan type if it doesn't exist and enable
                        blocklevel and metadat collection options.
                        Step3.2, Add full data for the current run.
                        Step3.3, Run a full backup for the subclient
                            and verify it completes without failures.
                        Step3.5, Run a File level Restore
                            and verify correct data is restored.
                        Step 3.6, Run Failover 
                        Step3.6, Add new data for the incremental-1
                        Step3.7, Run an incremental backup for the subclient
                            and verify it completes without failures.
                        Step3.9, Run a File level Restore
                            and verify correct data is restored.
                        Step3.10, Add new data for the incremental-2
                        Step3.11, Run an incremental backup for the subclient
                            and verify it completes without failures.
                        Step3.13, Run a File level Restore
                            and verify correct data is restored
                        Step 3.14, Run Failover								
                        Step3.15, Run an incremental-3 backup for the subclient
                            and verify it completes without failures..
                        Step3.17, Run a File level Restore
                            and verify correct data is restored.
                        Step3.18, Add new data for the incremental
                        Step3.19, Run an incremental-4 backup for the subclient
                            and verify it completes without failures.
                        Step3.21, Run a File level Restore
                            and verify correct data is restored								
                        Step 3.22, Run Failover								
                        Step3.23, Run an incremental-5 backup for the subclient
                            and verify it completes without failures.
                        Step3.25, Run a File level Restore
                            and verify correct data is restored.																
                        Step3.26, Run an synthfull for the subclient and
                            verify it completes without failures
                        Step3.28, Run a File level Restore
                            and verify correct data is restored.""")
            self.log.info("Step1, Create backupset for "
                     "this testcase if it doesn't exist")
            backupset_name = "backupset_" + self.id
            self.helper.create_backupset(backupset_name)
            nodes = self.client_machine.get_cluster_nodes(self.client_name)
            clusnode1, clusnode2 = nodes[0], nodes[1]
            self.node1 = self.commcell.clients.get(nodes[0])
            self.node2 = self.commcell.clients.get(nodes[1])
            self.node1_machine = machine.Machine(self.node1, self._commcell)
            self.node2_machine = machine.Machine(self.node2, self._commcell)
            self.active_node, self.passive_node = self.run_failover(clusnode1, clusnode2)
            for scan_type in ScanType:
                self.log.info(
                    "Step3, For each of the allowed index_type"
                    "Meta data colection Enabled/Not do operatons")
                if scan_type.name == 'CHANGEJOURNAL':
                    continue
                elif scan_type.name == 'OPTIMIZED':
                    self.log.info(
                        "Without Medata collection"
                        "we dont have any metadata collection so scan type Doesnt matter"
                    )
                    continue
                else:
                    # Assigning mountpoint as content based on Scan and Index type
                    if scan_type.name == 'RECURSIVE':
                        test_path = self.test_path
                        if test_path.endswith(self.slash_format):
                            test_path = str(test_path).rstrip(self.slash_format)
                    self.log.info("Running operations on Scan Type: %s", str(scan_type))
                    self.log.info("Step3.1,  Create subclient for the scan type %s "
                             "Index type if it doesn't exist.", scan_type.name)
                    subclient_name = ("subclient_{}_{}".format(self.id, scan_type.name.lower()))
                    subclient_content = []
                    subclient_content.append(test_path)
                    restore_path = self.restore_path
                    if self.restore_path.endswith(self.slash_format):
                        self.restore_path = str(self.restore_path).rstrip(self.slash_format)
                    tmp_path = self.client_machine.join_path(self.restore_path, "cvauto_tmp", subclient_name, str(self.runid))
                    synthfull_tmp_path = self.client_machine.join_path(self.restore_path, "cvauto_tmp", subclient_name, str(self.runid))
                    synthfull_run_path = self.client_machine.join_path(subclient_content[0], str(self.runid))
                    synthfull_datapath = synthfull_run_path
                    run_path = self.client_machine.join_path(subclient_content[0], str(self.runid))
                    full_data_path = self.client_machine.join_path(run_path, "full")
                    self.log.info("Step3.1,  Create subclient for the scan type if it doesn't exist")
                    # Create Subclient if doesnt exist
                    self.helper.create_subclient(
                        name=subclient_name,
                        storage_policy=self.storage_policy,
                        content=subclient_content,
                        scan_type=scan_type
                        )
                    self.log.info("Step3.2, Add full data for the current run")

                    self.log.info("Adding data under path: %s", full_data_path)
                    self.client_machine.generate_test_data(
                        full_data_path
                    )
                    #wait for for journals to get flushed
                    if not scan_type.value == ScanType.RECURSIVE.value:
                        self.log.info("Waiting for journals to get flushed")
                        sleep(self.wait_time)
                    self.log.info(
                        "Step3.3,Run a full backup for the subclient"
                        "and verify it completes without failures")
                    job_full = self.helper.run_backup_verify(scan_type, "Full")[0]
                    self.log.info("Step3.5, Run a File level Restore"
                                  "and verify correct data is restored.")
                    self.helper.run_restore_verify(
                        self.slash_format,
                        full_data_path,
                        tmp_path, "full", job_full, proxy_client=self.client_name)
                    self.log.info("Step 3.6, Run Failover ")
                    self.active_node, self.passive_node = self.run_failover(clusnode1, clusnode2)
                    self.log.info("Step3.6, Add new data for the incremental-1")
                    incr_diff_data_path = run_path + self.slash_format + "incr_diff"
                    self.client_machine.generate_test_data(
                        incr_diff_data_path, dirs=5, files=20, file_size=50)
                    self.log.info("Step3.7, Run an incremental backup for the subclient"
                             "and verify it completes without failures.")
                    job_incr1 = self.helper.run_backup_verify(
                        scan_type, "Incremental")[0]
                    self.log.info(
                        "Step3.9, Run a File level Restore"
                        "and verify correct data is restore."
                    )
                    self.helper.run_restore_verify(
                        self.slash_format,
                        incr_diff_data_path,
                        tmp_path, "incr_diff", job_incr1, proxy_client=self.client_name)
                    self.log.info("Step 3.10, Run Failover")
                    self.active_node, self.passive_node = self.run_failover(clusnode1, clusnode2)
                    self.log.info("Step3.10, Add new data for the incremental-2")
                    incr_diff_data_path = run_path + self.slash_format + "incr_diff2"
                    self.client_machine.generate_test_data(
                        incr_diff_data_path, dirs=5, files=20, file_size=50
                    )
                    self.log.info("Step3.11, Run an incremental backup for the subclient"
                             "and verify it completes without failure")
                    job_incr1 = self.helper.run_backup_verify(
                        scan_type, "Incremental")[0]
                    self.log.info(
                        "Step3.13, Run a File level Restore"
                        "and verify correct data is restored"
                    )
                    self.helper.run_restore_verify(
                        self.slash_format,
                        incr_diff_data_path,
                        tmp_path, "incr_diff2", job_incr1, proxy_client=self.client_name)
                    self.log.info("Step3.14, Add new data for the incremental-3")
                    incr_diff_data_path = run_path + self.slash_format + "incr_diff3"
                    self.client_machine.generate_test_data(
                        incr_diff_data_path, dirs=5, files=20, file_size=50
                    )
                    self.log.info("Step3.15, Run an incremental backup for the subclient"
                             "and verify it completes without failures.")
                    job_incr1 = self.helper.run_backup_verify(
                        scan_type, "Incremental")[0]
                    self.log.info(
                        "Step3.17, Run a File level Restore"
                        "and verify correct data is restore."
                    )
                    self.helper.run_restore_verify(
                        self.slash_format,
                        incr_diff_data_path,
                        tmp_path, "incr_diff3", job_incr1, proxy_client=self.client_name)
                    self.log.info("Step 3.19, Run Failover	")
                    self.active_node, self.passive_node = self.run_failover(clusnode1, clusnode2)
                    self.log.info("Step3.19, Add new data for the incremental-4")
                    incr_diff_data_path = run_path + self.slash_format + "incr_diff4"
                    self.client_machine.generate_test_data(
                        incr_diff_data_path, dirs=5, files=20, file_size=50
                    )
                    self.log.info("Step3.19, Run an incremental backup for the subclient"
                             "and verify it completes without failures.")
                    job_incr1 = self.helper.run_backup_verify(
                        scan_type, "Incremental")[0]
                    self.log.info(
                        "Step3.21, Run a File level Restore"
                        "and verify correct data is restore."
                    )
                    self.helper.run_restore_verify(
                        self.slash_format,
                        incr_diff_data_path,
                        tmp_path, "incr_diff4", job_incr1, proxy_client=self.client_name)
                    self.log.info("Step 3.22, Run Failover")
                    self.active_node, self.passive_node = self.run_failover(clusnode1, clusnode2)
                    self.log.info("Step3.23, Add new data for the incremental-5")
                    incr_diff_data_path = run_path + self.slash_format + "incr_diff5"
                    self.client_machine.generate_test_data(
                        incr_diff_data_path, dirs=5, files=20, file_size=50
                    )
                    self.log.info("Step3.23, Run an incremental backup for the subclient"
                             "and verify it completes without failures.")
                    job_incr1 = self.helper.run_backup_verify(
                        scan_type, "Incremental")[0]
                    # Compare Source and Destination and check files restored.
                    self.log.info(
                        "Step3.25, Run a File level Restore"
                        "and verify correct data is restore."
                    )
                    self.helper.run_restore_verify(
                        self.slash_format,
                        incr_diff_data_path,
                        tmp_path, "incr_diff5", job_incr1, proxy_client=self.client_name)

                    self.log.info("Step3.26, Run an synthfull for the subclient and"
                             "verify it completes without failures.")
                    self.helper.run_backup_verify(scan_type, "Synthetic_full")
                    self.log.info("Step3.28, Run a File level Restore"
                             "and verify correct data is restored.")
                    self.helper.run_restore_verify(
                        self.slash_format,
                        synthfull_datapath,
                        synthfull_tmp_path, str(self.runid), proxy_client=self.client_name)
                    self.log.info("<<<<<<< Cycle 1 completed >>>>>>")
                    self.client_machine.remove_directory(
                        subclient_content[0])
                    self.log.info("** %s SCAN TYPE USED", scan_type.name)
                    self.log.info("RUN COMPLETED SUCCESFULLY")
                    self.client_machine.remove_directory(tmp_path)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)


    def run_failover(self, clusnode1, clusnode2):
        """Function runs failover and send back active and passive node."""
        actnode = self.client_machine.get_active_cluster_node(self.client_name)
        actnode = actnode.upper()
        clusnode1 = clusnode1.upper()
        clusnode2 = clusnode2.upper()
        failover_verifier = actnode
        if actnode == clusnode1:
            self.active_node = clusnode1
            self.passive_node = clusnode2
        else:
            self.active_node = clusnode2
            self.passive_node = clusnode1
        self.log.info(" Before running failover Active Node = {} , Passive Node = {}".format(self.active_node, self.passive_node))
        if self.active_node == clusnode1:
            self.node1_machine.do_failover(self.active_node, self.passive_node)
        else:
            self.node2_machine.do_failover(self.active_node, self.passive_node)
        sleep(60)
        actnode = self.client_machine.get_active_cluster_node(self.client_name)
        if failover_verifier == actnode:
            self.log.info("Failed to Run failover")
            raise Exception("Failed to Run failover")
        else:
            actnode = actnode.upper()
            if actnode == clusnode1:
                self.active_node = clusnode1
                self.passive_node = clusnode2
            else:
                self.active_node = clusnode2
                self.passive_node = clusnode1
            self.log.info("Failover Done Active node ={}  , Passive node = {}".format(self.active_node, self.passive_node))
        return self.active_node, self.passive_node
