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
"""

from time import sleep
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper, IndexEnabled

class TestCase(CVTestCase):

    """Class for executing Blocklevel  Data Protection - Full,Incremental,Synthfull
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
                Step3.4,Run failover .
                Step3.5, Run a File level Restore
                        and verify correct data is restored.
                Step3.6, Add new data for the incremental
                Step3.7, Run an incremental backup for the subclient
                        and verify it completes without failures.
                Step3.8, Run failover.
                Step3.9, Run a File level Restore
                        and verify correct data is restored.
                Step3.10, Run an synthfull for the subclient and
                        verify it completes without failures
                Step3.11, Run a Volume level Restore
                        and verify correct data is restored.
                Step3.12, Run a File level Restore
                        and verify correct data is restored
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Windows Blocklevel  Cluster Native Validation"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
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



    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        try:
            # Initialize test case inputs
            self.helper = FSHelper(self)
            FSHelper.populate_tc_inputs(self)

            test_path = self.test_path
            slash_format = self.slash_format
            helper = self.helper
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy

            self.log.info(""" Blocklevel  Cluster validation - Full,Incremental,Synthfull
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
                                        Step3.4,Run failover .
                                        Step3.5, Run a File level Restore
                                            and verify correct data is restored.
                                        Step3.6, Add new data for the incremental
                                        Step3.7, Run an incremental backup for the subclient
                                            and verify it completes without failures.
                                        Step3.8, Run failover.
                                        Step3.9, Run a File level Restore
                                            and verify correct data is restored.
                                        Step3.10, Run an synthfull for the subclient and
                                            verify it completes without failures
                                        Step3.11, Run a Volume level Restore
                                            and verify correct data is restored.
                                        Step3.12, Run a File level Restore
                                            and verify correct data is restored""")

            self.log.info("Step1, Create backupset for "
                          "this testcase if it doesn't exist")
            backupset_name = "backupset_" + self.id
            helper.create_backupset(backupset_name)

            self.log.info("Step2, For each of the allowed scan type Create all operations")

            for scan_type in ScanType:
                self.log.info(
                    "Step3, For each of the allowed index_type"
                    "Meta data colection Enabled/Not do operatons")
                for index_type in IndexEnabled:
                    if scan_type.name == 'CHANGEJOURNAL':
                        continue
                    elif scan_type.name == 'OPTIMIZED' and index_type.name == 'NOINDEX':
                        self.log.info(
                            "Without Medata collection"
                            "we dont have any metadata collection so scan type Doesnt matter"
                        )
                        continue
                    elif scan_type.name == 'OPTIMIZED' and index_type.name == 'INDEX':
                        self.log.info(
                            "Skipping as Index case ran with Recursive scan"
                        )
                        continue

                    else:
                        # Assigning mountpoint as content based on Scan and Index type
                        if scan_type.name == 'RECURSIVE' and index_type.name == 'INDEX':
                            test_path = self.test_path
                            helper = self.helper
                            if test_path.endswith(slash_format):
                                test_path = str(test_path).rstrip(slash_format)
                        elif scan_type.name == 'RECURSIVE' and index_type.name == 'NOINDEX':
                            test_path = self.test_path2
                            helper = self.helper
                            if test_path.endswith(slash_format):
                                test_path = str(test_path).rstrip(slash_format)

                        self.log.info("Running operations on Scan Type: %s", str(scan_type))
                        self.log.info("Running operations on Index Type: %s", str(index_type))
                        # SKip chain journal scan for Unix
                        if (self.applicable_os != 'WINDOWS'
                                and
                                scan_type.value == ScanType.CHANGEJOURNAL.value):
                            continue
                        # Skip DC if verify_dc is not provided
                        if (self.applicable_os != 'WINDOWS'
                                and scan_type.value == ScanType.OPTIMIZED.value):
                            if not self.verify_dc:
                                continue
                        self.log.info("Step3.1,  Create subclient for the scan type %s "
                                      "Index type if it doesn't exist.", scan_type.name)
                        nodes = self.helper.get_cluster_nodes()
                        node1, node2 = nodes[0], nodes[1]
                        self.log.info("The nodes of cluster are {0} and  {1}".format(node1, node2))
                        active_node = self.helper.active_cluster_node(self.client_name)
                        if active_node == node1:
                            passive_node = node2
                        else:
                            passive_node = node1
                        self.log.info("Activenode = {0} , Passivenode = {1}".format(active_node, passive_node))
                        subclient_name = ("subclient_%s_%s_%s" %\
                                         (self.id, scan_type.name.lower(), index_type.name.lower()))
                        subclient_content = []
                        subclient_content.append(test_path)
                        restore_path = self.restore_path
                        slash_format = self.slash_format
                        helper = self.helper
                        if restore_path.endswith(slash_format):
                            restore_path = str(restore_path).rstrip(slash_format)
                        tmp_path = ("%s%scvauto_tmp%s%s%s%s" %\
                                   (restore_path, slash_format, slash_format, subclient_name,\
                                    slash_format, str(self.runid)))
                        synthfull_tmp_path = ("%s%scvauto_tmp%s%s%s%s" % \
                                              (restore_path, slash_format, slash_format,\
                                               subclient_name, slash_format, str(self.runid)))
                        synthfull_run_path = ("%s%s%s" %(subclient_content[0], \
                                                        slash_format, str(self.runid)))
                        synthfull_datapath = synthfull_run_path
                        run_path = ("%s%s%s" %(subclient_content[0], slash_format, str(self.runid)))
                        vlr_source = ("%s%s%s" %(str(test_path), slash_format, str(self.runid)))
                        vlr_destination = ("%s%s%s" %(str(restore_path), slash_format,\
                                                      str(self.runid)))
                        full_data_path = ("%s%sfull" %(run_path, slash_format))
                        self.log.info("Step3.1,  Create subclient for the scan type if it doesn't exist")
                        # Create Subclient if doesnt exist
                        helper.create_subclient(
                            name=subclient_name,
                            storage_policy=storage_policy,
                            content=subclient_content,
                            scan_type=scan_type
                            )
                        # Update Subclient with blocklevel value if not set
                        self.log.info("Enabling BlockLevel Option")
                        helper.update_subclient(content=subclient_content,
                                                block_level_backup=1)
                        if index_type.name == "INDEX":
                            self.log.info("Enabling Metadata collection")
                            helper.update_subclient(content=subclient_content,
                                                    createFileLevelIndex=True)
                        self.log.info("Step3.2, Add full data for the current run")
                        self.log.info("Adding data under path: %s", full_data_path)
                        self.client_machine.generate_test_data(
                            full_data_path
                        )
                        if not scan_type.value == ScanType.RECURSIVE.value:
                            self.log.info("Waiting for journals to get flushed")
                            sleep(self.wait_time)
                        self.log.info(
                            "Step3.3,Run a full backup for the subclient"
                            "and verify it completes without failures")
                        job_full = helper.run_backup_verify(scan_type, "Full")[0]
                        self.log.info(
                            "Step3.4, Do failover ")
                        self.helper.do_failover(self.client_name, passive_node)
                        sleep(300)
                        active_node = self.helper.active_cluster_node(self.client_name)
                        if active_node == passive_node:
                            self.log.info("Failover done moved to  {0}".format(passive_node))
                        else:
                            self.log.info("Failover failed to  {0}".format(passive_node))
                            raise Exception("Failed to Run failover")
                        if active_node == node1:
                            passive_node = node2
                        else:
                            passive_node = node1
                        self.log.info("Activenode = {0} , Passivenode = {1}".format(active_node, passive_node))
                        self.log.info("Step3.5, Run a File level Restore"
                                      "and verify correct data is restored.")
                        helper.run_restore_verify(
                            slash_format,
                            full_data_path,
                            tmp_path, "full", job_full, proxy_client=self.client_name)
                        self.log.info("Step3.6, Add new data for the incremental")
                        incr_diff_data_path = run_path + slash_format + "incr_diff"

                        self.client_machine.generate_test_data(
                            incr_diff_data_path, dirs=5, files=20, file_size=50
                        )
                        self.log.info("Step3.7, Run an incremental backup for the subclient"
                                      "and verify it completes without failures.")
                        job_incr1 = helper.run_backup_verify(
                            scan_type, "Incremental")[0]
                        self.log.info("Step3.8, Do failover ")
                        self.helper.do_failover(self.client_name, passive_node)
                        sleep(300)
                        active_node = self.helper.active_cluster_node(self.client_name)
                        if active_node == passive_node:
                            self.log.info("Failover done moved to  {0}".format(passive_node))
                        else:
                            self.log.info("Failover failed to  {0}".format(passive_node))
                        if active_node == node1:
                            passive_node = node2
                        else:
                            passive_node = node1
                        self.log.info("Activenode = {0} , Passivenode = {1}".format(active_node, passive_node))
                        self.log.info(
                            "Step3.9, Run a File level Restore"
                            "and verify correct data is restore."
                        )
                        helper.run_restore_verify(
                            slash_format,
                            incr_diff_data_path,
                            tmp_path, "incr_diff", job_incr1, proxy_client=self.client_name)
                        self.log.info("Step3.10, Run an synthfull for the subclient and"
                                      "verify it completes without failures.")

                        self.log.info("Step3.6, Add new data for the incremental2")
                        incr_diff2_data_path = run_path + slash_format + "incr_diff2"
                        self.client_machine.generate_test_data(
                            incr_diff2_data_path, dirs=5, files=20, file_size=50
                        )
                        self.log.info("Step3.7, Run an incremental backup for the subclient"
                                      "and verify it completes without failures.")
                        job_incr1 = helper.run_backup_verify(
                            scan_type, "Incremental")[0]
                        self.log.info("Step3.8, Do failover ")
                        self.helper.do_failover(self.client_name, passive_node)
                        sleep(300)
                        active_node = self.helper.active_cluster_node(self.client_name)
                        if active_node == passive_node:
                            self.log.info("Failover done moved to  {0}".format(passive_node))
                        else:
                            self.log.info("Failover failed to  {0}".format(passive_node))
                        if active_node == node1:
                            passive_node = node2
                        else:
                            passive_node = node1
                        self.log.info("Activenode = {0} , Passivenode = {1}".format(active_node, passive_node))
                        self.log.info(
                            "Step3.9, Run a File level Restore"
                            "and verify correct data is restore."
                        )
                        helper.run_restore_verify(
                            slash_format,
                            incr_diff2_data_path,
                            tmp_path, "incr_diff2", job_incr1, proxy_client=self.client_name)

                        helper.run_backup_verify(scan_type, "Synthetic_full")
                        self.log.info("Step3.12, Run a File level Restore"
                                      "and verify correct data is restored.")
                        helper.run_restore_verify(
                            slash_format,
                            synthfull_datapath,
                            synthfull_tmp_path, str(self.runid), proxy_client=self.client_name)
                        self.log.info("<<<<<<< Cycle 1 completed >>>>>>")
                        self.client_machine.remove_directory(
                            subclient_content[0])
                        self.log.info("** %s SCAN TYPE USED", scan_type.name)
                        self.log.info("** %s INDEXTYPE USED", index_type.name)
                        self.log.info("RUN COMPLETED SUCCESFULLY")
                        self.client_machine.remove_directory(tmp_path)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
