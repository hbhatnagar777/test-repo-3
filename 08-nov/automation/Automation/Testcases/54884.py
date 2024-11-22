# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Endurance test for creating objectstore and PIT view creation

"""
import sys
import random
import datetime
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils

class TestCase(CVTestCase):
    """Class for executing Basic functionality verification for NFS objectstore PIT views"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "NFS ObjectStore - Run tests for re-writable PITs"
        self.product = self.products_list.OBJECTSTORE
        self.feature = self.features_list.OBJECTSTORENFS
        self.applicable_os = self.os_list.LINUX
        self.show_to_user = True
        self.tcinputs = {
            'NFSServerHostName': None,
            'ClientHostname': None,
            'ClientUsername': None,
            'ClientPassword': None,
            'IndexServerClientName': None,
        }
        self.nfsutil_obj = None
        self.nfs_server_obj = None
        self.expected_dir_details = None
        self.objstore_test_path = None
        self.snap_test_path = None
        self.local_tst_path = None
        self.test_dir_name = 'folder1'
        self.mounted_dirs = []
        self.pit_write_path = None

    def setup(self):
        """ Setup function of this test case """
        self.log.info("Executing Testcase")

        self.nfsutil_obj = NFSutils(self.tcinputs['ClientHostname'],
                                    self.tcinputs['ClientUsername'],
                                    self.tcinputs['ClientPassword'], self.id, self.commcell)

        self.objstore_test_path = self.nfsutil_obj.machine_obj.\
            join_path(self.nfsutil_obj.mount_dir, self.test_dir_name)

        # as we cannot change permission of mount root directory, need to create a sub directory
        self.local_tst_path = self.nfsutil_obj.machine_obj.\
            join_path(self.nfsutil_obj.automation_temp_dir, 'localtestdir', self.test_dir_name)

        self.snap_test_path = self.nfsutil_obj.machine_obj.\
            join_path(self.nfsutil_obj.snap_mount_dir, self.test_dir_name)

        self.nfs_server_obj = NFSHelper(self.tcinputs['NFSServerHostName'], self.commcell,
                                        self.inputJSONnode['commcell']['commcellUsername'],
                                        self.inputJSONnode['commcell']['commcellPassword'])

        self.log.info("Creating Object Store: %s", self.nfsutil_obj.Obj_store_name)
        share_path = self.nfs_server_obj.\
        create_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                               self.nfs_server_obj.storage_policy,
                               self.tcinputs['IndexServerClientName'],
                               self.tcinputs['NFSServerHostName'],
                               self.tcinputs['ClientHostname'], squashing_type="NO_ROOT_SQUASH",
                               delete_if_exists=True)

        self.nfsutil_obj.machine_obj.\
            mount_nfs_share(self.nfsutil_obj.mount_dir, self.tcinputs['ClientHostname'], share_path)
        self.mounted_dirs.append(self.nfsutil_obj.mount_dir)

        self.log.info("NFS objectstore mounted successfully on '%s'", self.nfsutil_obj.mount_dir)

    def run(self):
        """Main function for test case execution"""
        try:
            self.nfsutil_obj.machine_obj.create_directory(self.local_tst_path)
            self.log.debug("Directory '%s' created successfully", self.local_tst_path)

            self.nfsutil_obj.machine_obj.\
                generate_test_data(self.local_tst_path, hlinks=False, dirs=random.randint(3, 10),
                                   files=random.randint(5, 20), slinks=random.randint(5, 10))

            self.nfsutil_obj.machine_obj.\
                copy_folder(self.local_tst_path, self.nfsutil_obj.mount_dir)

            self.nfsutil_obj.machine_obj.compare_folders(
                self.nfsutil_obj.machine_obj, self.local_tst_path, self.objstore_test_path)

            # Expected time stamp format: "MM-DD-YYYY HH:MM:SS"
            timestamp1 = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y %H:%M:%S')
            self.log.info("Timestamp noted to create PIT view is: %s", timestamp1)

            # Create a PIT in Read-Only mode (default mode)
            snap_mount_path = self.nfs_server_obj.\
                create_objectstore_snap(self.nfsutil_obj.Obj_store_name, timestamp1,
                                        self.tcinputs['ClientHostname'])

            # Mount NFS PIT view share
            self.nfsutil_obj.machine_obj.mount_nfs_share(self.nfsutil_obj.snap_mount_dir,
                                                         self.tcinputs['NFSServerHostName'],
                                                         snap_mount_path)

            # Make sure the PIT content matches the Share content, before the PIT Write operation.
            self.nfsutil_obj.compare_snapshot(self.objstore_test_path, self.snap_test_path)

            self.pit_write_path = self.nfsutil_obj.machine_obj.\
                join_path(self.nfsutil_obj.snap_mount_dir, 'PITWritePath')

            try:
                # Try writing data to the RO PIT. It should fail
                self.nfsutil_obj.machine_obj.create_directory(self.pit_write_path)

            except:
                # Write operation on the PIT failed as expected because it is in RO mode
                self.log.info("Write operation failed on a Read-Only snap. Updating snap to RW")
                self.nfs_server_obj.update_objectstore_snap(self.nfsutil_obj.Obj_store_name,
                                                            mount_path=snap_mount_path,
                                                            access_permission="RW")

                # Try write operation on the PIT after updating to Read-write mode.
                self.nfsutil_obj.machine_obj.copy_folder(self.local_tst_path, self.pit_write_path)
                self.log.info("Write operation SUCCESSFUL on the RW PIT '%s'. Proceeding to "
                              "compare the contents of PIT and test data", snap_mount_path)

                # If folders match, then Write to PIT was successful. So compare the contents
                self.nfsutil_obj.machine_obj.\
                    compare_folders(self.nfsutil_obj.machine_obj, self.local_tst_path,
                                    self.pit_write_path)
                self.log.info("Contents of the RW PIT '%s' and local data match.", snap_mount_path)

                # Cleaning-up
                self.nfsutil_obj.machine_obj.remove_directory(self.local_tst_path)
                self.nfsutil_obj.machine_obj.remove_directory(self.objstore_test_path)
                self.nfsutil_obj.machine_obj.unmount_path(self.nfsutil_obj.snap_mount_dir)

                self.log.info("Testcase PASSED.")

            # If there is no exception
            else:
                self.log.info("Able to create directory on the PIT '%s', in default RO mode."
                              "So FAILING the testcase.", snap_mount_path)
                self.status = constants.FAILED

        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.nfsutil_obj.server.fail(excp, "Test case failed in run function")
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""
        self.nfsutil_obj.obj_store_cleanup(mounted_paths=self.mounted_dirs)
        self.nfs_server_obj.\
            delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name, delete_user=True)
