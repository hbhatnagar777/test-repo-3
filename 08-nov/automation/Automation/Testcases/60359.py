# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ------------------------------------------------------------.--------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    verify_file_attributes()    --  to verify the attributes of the files.

    verify_modified_time()  --  to verify the modified time of the file.


"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper, ScanType
from AutomationUtils import constants
from FileSystem.FSUtils.fshelper import ScanType, FSHelper, IndexEnabled
from AutomationUtils import machine
import time
import threading
import sys


class ExcThread(threading.Thread):

    def __init__(self, target, args=None):
        self.args = args if args else []
        self.target = target
        self.exc = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.target(path=self.args)
        except Exception:
            self.exc = sys.exc_info()


class TestCase(CVTestCase):
    """Class for Cluster aware recall :  SOFS cluster volume"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Cluster aware recall :  SOFS cluster volume"
        self.base_folder_path = None
        self.client_name = ""
        self.origin_folder_path = None
        self.is_nas_turbo_type = False
        self.before_mtime = None
        self.OPHelper = None
        self.node1_machine = None
        self.recall_path = None
        self.tcinputs = {
            "TestPath": None,
            "RecallPath": None,
            "StoragePolicyName": None
        }

    def verify_file_attributes(self, path, valid_attributes=['ARCHIVE']):
        """ to verify the attributes of the files.   """

        if "windows" in self.OPHelper.client_machine.os_info.lower():
            attributes_list = self.OPHelper.client_machine.get_test_data_info(data_path=path,
                                                                              custom_meta_list="'Attributes'")
            for attributes, file in zip(attributes_list.strip().split('\r\n'),
                                        list(zip(*self.OPHelper.test_file_list))[0]):
                # self.log.info("the attributes of the file are %s",str(valid_attributes))
                if any(x.upper() not in attributes.upper() for x in valid_attributes):
                    raise Exception(
                        "Following File : " + file + " with Attributes : " + attributes + "Is not Expected. Valid is " +
                        str(valid_attributes))
                else:
                    self.log.info("Attributes of file %s are %s", file, attributes)

    def run_failover(self, active_node):
        """Function runs failover and send back new active node."""
        failover_verifier = active_node
        self.node1_machine.do_failover(cluster_group=self.client_name)
        time.sleep(60)
        actnode = self.client_machine.get_active_cluster_node(self.client_name)
        if failover_verifier.upper() == actnode.upper():
            self.log.info("Failed to Run failover")
            raise Exception("Failed to Run failover")
        else:
            self.log.info("Failover is complete and new Active node ={}  ".format(actnode))
        return active_node

    def verify_modified_time(self, path):
        """ Verify that Last Modified time of files is not changed. """

        changed_mtime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(path, self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastWriteTimeUtc'").strip()

        self.log.info("After mtime: %s", str(changed_mtime)[:19])
        self.log.info("Before mtime: %s", str(self.before_mtime)[:19])
        if str(self.before_mtime)[:19] != str(changed_mtime)[:19]:
            raise Exception("The mtime of the files have been changed.")
        else:
            self.log.info("The mtime of the files have not been changed.")

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.OPHelper.populate_inputs()
        self.recall_path = self.tcinputs.get('RecallPath')
        self.log.info("Test inputs populated successfully.")

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                        ("test4.txt", True), ("test5.txt", True), ("test6.txt", True),
                                        ("test7.txt", True), ("test8.txt", True), ("test9.txt", True)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED2")
        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')

        self.OPHelper.prepare_turbo_testdata(
            self.origin_folder_path,
            self.OPHelper.test_file_list,
            size1=100 * 1024 * 1024, size2=100 * 1024 * 1024
        )

        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(self.origin_folder_path)
        self.before_mtime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(self.origin_folder_path,
                                                             self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastWriteTimeUtc'").strip()
        self.log.info("Test data populated successfully.")

        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)
        self.OPHelper.create_subclient(delete=True, content=[self.origin_folder_path], scan_type=ScanType.RECURSIVE)
        update_properties = self.OPHelper.testcase.subclient.properties
        update_properties['fsSubClientProp']['checkArchiveBit'] = True
        self.OPHelper.testcase.subclient.update_properties(update_properties)

        if self.is_nas_turbo_type:
            update_properties = self.OPHelper.testcase.subclient.properties
            update_properties['fsSubClientProp']['enableNetworkShareAutoMount'] = True
            update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
            update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
            self.OPHelper.testcase.subclient.update_properties(update_properties)

        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": False,
            "fileModifiedTimeOlderThan": 0,
            "fileSizeGreaterThan": 8,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "fileAccessTimeOlderThan": 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True
        }

        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = 1
        self.OPHelper.testcase.subclient.backup_retention = False
        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules
        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Run two archive jobs to backup and stub data.
        2. Start recalling the files.
        3. Failover cluster to other available node which will fail current recalls
        4. Wait for failover to complete and repair the stubs
        5. Trigger another recall after repair is done
        6. Verify Modified time, checksum and attributes of the recalled file.
        """

        try:

            self.log.info(_desc)

            self.OPHelper.run_archive(repeats=2)
            recall_path1 = self.recall_path + '{0}{1}_{2}_data'.format(
                self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED2")
            recall_path_dir = self.OPHelper.client_machine.join_path(recall_path1, 'origin')

            self.verify_file_attributes(path=recall_path_dir,
                                        valid_attributes=self.tcinputs.get('RecalledStubAttributes',
                                                                           ['ARCHIVE', 'SPARSEFILE',
                                                                            'OFFLINE']))

            # time.sleep(3)
            nodes = self.client_machine.get_cluster_nodes(self.client_name)
            clustnode1 = nodes[0]
            node1 = self.commcell.clients.get(clustnode1)
            self.node1_machine = machine.Machine(node1, self._commcell)

            t1 = ExcThread(target=self.OPHelper.recall, args=(recall_path_dir,))
            t1.start()

            time.sleep(10)
            self.log.info("Starting failover of the cluster %s ", self.client_name)
            self.node1_machine.do_failover(cluster_group=self.client_name)
            self.log.info("Done with the failover of the cluster %s ", self.client_name)

            t1.join()

            self.log.info("Waiting for stubs to get repaired.")
            time.sleep(600)

            exc = t1.exc
            if exc:
                exc_type, exc_obj, exc_trace = exc
                self.log.info(exc_obj)

            self.log.info("Recalling rest of the files")
            try:
                self.OPHelper.recall(path=recall_path_dir)
            except Exception:
                self.log.info("Trying recall one more time after waiting for 2 min")
                time.sleep(120)
                self.OPHelper.recall(path=recall_path_dir)

            self.verify_file_attributes(path=recall_path_dir,
                                        valid_attributes=self.tcinputs.get('RecalledStubAttributes', ['ARCHIVE']))
            self.verify_modified_time(path=self.origin_folder_path)

            #Archive and recall again after failover
            self.OPHelper.run_archive(repeats=2)
            self.verify_file_attributes(path=self.origin_folder_path,
                                        valid_attributes=self.tcinputs.get('RecalledStubAttributes',
                                                                           ['ARCHIVE', 'SPARSEFILE',
                                                                            'OFFLINE']))
            self.log.info("Recalling the files after failover and archival")
            try:
                self.OPHelper.recall(path=recall_path_dir)
            except Exception:
                self.log.info("Trying recall one more time after waiting for 2 min")
                time.sleep(120)
                self.OPHelper.recall(path=recall_path_dir)

            self.log.info('Cluster aware recall :  SOFS cluster volume passed')

        except Exception as exp:
            self.log.error('Cluster aware recall :  SOFS cluster volume failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
