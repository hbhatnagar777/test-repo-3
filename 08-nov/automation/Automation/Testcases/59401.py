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

    restart_clmgrs_service()    -- Restart ClMgrS service after adding registry key for the changes to take effect

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper, ScanType
from AutomationUtils import constants
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
            self.target(*self.args)
        except Exception:
            self.exc = sys.exc_info()


class TestCase(CVTestCase):
    """Class for Recall stubs - Service restart"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Recall stubs - Service restart"
        self.base_folder_path = None
        self.origin_folder_path = None
        self.is_nas_turbo_type = False
        self.before_mtime = None
        self.OPHelper = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }

    def verify_file_attributes(self, path, valid_attributes=['ARCHIVE']):
        """ to verify the attributes of the files.   """

        if "windows" in self.OPHelper.client_machine.os_info.lower():
            attributes_list = self.OPHelper.client_machine.get_test_data_info(data_path=path,
                                                                              custom_meta_list="'Attributes'")
            for attributes, file in zip(attributes_list.strip().split('\r\n'),
                                        list(zip(*self.OPHelper.test_file_list))[0]):
                if any(x.upper() not in attributes.upper() for x in valid_attributes):
                    raise Exception(
                        "Following File : " + file + " with Attributes : " + attributes + "Is not Expected. Valid is " +
                        str(valid_attributes))
                else:
                    self.log.info("Attributes of file %s are %s", file, attributes)

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

    def restart_clmgrs_service(self):
        """
            Restart ClMgrS service after adding registry key for the changes to take effect
        """

        self.log.info("Restarting ClMgrS")

        if self.tcinputs.get("ProxyClient", None):
            client_node = self.commcell.clients.get(self.tcinputs['ProxyClient'])
        else:
            client_node = self.client
        if "windows" in client_node.os_info.lower():
            client_instance = client_node.instance
            service_name = 'GxClMgrS({})'.format(client_instance)
            client_node.restart_service(service_name)
            return True
        else:
            client_node.restart_service()

        self.log.info("Waiting for service restart to complete")
        time.sleep(120)

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.OPHelper.populate_inputs()
        self.log.info("Test inputs populated successfully.")

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                        ("test4.txt", True), ("test5.txt", True), ("test6.txt", True),
                                        ("test7.txt", True), ("test8.txt", True), ("test9.txt", True),
                                        ("test10.txt", True), ("test11.txt", True), ("test12.txt", True),
                                        ("test13.txt", True), ("test14.txt", True), ("test15.txt", True),
                                        ("test16.txt", True), ("test17.txt", True), ("test18.txt", True)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED2")
        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')

        self.OPHelper.prepare_turbo_testdata(
            self.origin_folder_path,
            self.OPHelper.test_file_list,
            size1=1024 * 1024, size2=1024 * 1024
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
        3. Restart ClMgrs in the middle of recall.
        4. Wait for the clmgrs to be restarted.
        5. Trigger another recall after ClMgrs is restarted.
        6. Verify Modified time, checksum and attributes of the recalled file.
        """

        try:

            self.log.info(_desc)
            self.OPHelper.run_archive(repeats=2)

            t1 = ExcThread(target=self.OPHelper.recall, args=(self.origin_folder_path,))

            t1.start()
            time.sleep(5)
            self.restart_clmgrs_service()
            t1.join()
            exc = t1.exc
            if exc:
                exc_type, exc_obj, exc_trace = exc
                self.log.info(exc_obj)

            self.log.info("Waiting for ClMgrs to Start completely.")
            time.sleep(600)
            try:
                self.OPHelper.recall(path=self.origin_folder_path)
            finally:
                self.OPHelper.recall(path=self.origin_folder_path)

            self.verify_file_attributes(path=self.origin_folder_path,
                                        valid_attributes=self.tcinputs.get('RecalledStubAttributes', ['ARCHIVE']))
            self.verify_modified_time(path=self.origin_folder_path)

            self.log.info('Recall stubs - Service restart passed')

        except Exception as exp:
            self.log.error('Recall stubs - Service restart failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
