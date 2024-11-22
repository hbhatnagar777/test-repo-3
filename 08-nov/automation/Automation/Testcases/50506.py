# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Basic File and Directory Operations On NFS Share

"""
import sys

from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing Basic functionality verification for NFS objectstore PIT views"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic File and Directory Operations On NFS Share"
        self.product = self.products_list.OBJECTSTORE
        self.feature = self.features_list.OBJECTSTORENFS
        self.applicable_os = self.os_list.LINUX
        self.show_to_user = True
        # please note that storagePolicy is optional input
        self.tcinputs = {
            'NFSServerHostName': None,
            'clientHostname': None,
            'clientUsername': None,
            'clientPassword': None,
            'indexServerMA': None
        }
        self.nfsutil_obj = None
        self.NFS_server_obj = None
        self.expected_dir_details = None
        self.objstore_test_path = None
        self.snap_test_path = None
        self.local_tst_path = None
        self.test_dir_name = 'folder1'
        self.mounted_dirs = []
        self.server = None
        self.share_path = None

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")
        self.server = ServerTestCases(self)
        try:
            self.nfsutil_obj = NFSutils(self.tcinputs['clientHostname'],
                                        self.tcinputs['clientUsername'],
                                        self.tcinputs['clientPassword'],
                                        self.id,
                                        self.commcell)

            self.objstore_test_path = self.nfsutil_obj.machine_obj.join_path(
                                                                        self.nfsutil_obj.mount_dir,
                                                                        self.test_dir_name)

            # as we cannot change permission of mount root directory, need to create a sub directory
            self.local_tst_path = self.nfsutil_obj.machine_obj.join_path(
                                                                self.nfsutil_obj.automation_temp_dir,
                                                                'localtestdir',
                                                                self.test_dir_name)

            self.NFS_server_obj = NFSHelper(self.tcinputs['NFSServerHostName'],
                                            self.commcell,
                                            self.inputJSONnode['commcell']['commcellUsername'],
                                            self.inputJSONnode['commcell']['commcellPassword'],
                                            self.tcinputs.get('storagePolicy'))

            self.log.info("Creating Object Store : {0}".format(self.nfsutil_obj.Obj_store_name))
            self.share_path = self.NFS_server_obj.create_nfs_objectstore(
                                                        self.nfsutil_obj.Obj_store_name,
                                                        self.NFS_server_obj.storage_policy,
                                                        self.tcinputs['indexServerMA'],
                                                        self.tcinputs['NFSServerHostName'],
                                                        self.tcinputs['clientHostname'],
                                                        squashing_type="NO_ROOT_SQUASH",
                                                        delete_if_exists=True)
        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in setup function")

    def run(self):
        """Main function for test case execution"""
        width = 100
        try:
            for nfs_mount_version in ["3", "4"]:
                message = "verify basic file operations for nfs v{0} client ".center(width+10, '*')
                self.log.info(message.format(nfs_mount_version))
                self.nfsutil_obj.machine_obj.mount_nfs_share(self.nfsutil_obj.mount_dir,
                                                             self.tcinputs['NFSServerHostName'],
                                                             self.share_path,
                                                             version=nfs_mount_version)

                self.log.info("NFS objectstore mounted with version {1} successfully on {0}".format(
                    self.nfsutil_obj.mount_dir, nfs_mount_version))

                self.nfsutil_obj.machine_obj.create_directory(self.objstore_test_path, force_create=True)
                self.log.debug("directory {0} created successfully".format(
                    self.objstore_test_path))

                self.nfsutil_obj.machine_obj.create_directory(self.local_tst_path, force_create=True)
                self.log.debug("directory {0} created successfully".format(
                    self.local_tst_path))

                # sub_test 1: verify open and write operations by copying data to objectstore path
                message = "subtest : verify open() and write()".center(width, '-')
                self.log.info(message)
                self.nfsutil_obj.machine_obj.generate_test_data(self.local_tst_path,
                                                                hlinks=False)
                self.log.info("Created test data on path {0}".format(self.local_tst_path))

                self.log.info("copying test data from local path to nfs mount path")
                self.nfsutil_obj.machine_obj.copy_folder(self.local_tst_path,
                                                         self.nfsutil_obj.mount_dir,
                                                         optional_params='p')

                self.nfsutil_obj.compare_snapshot(self.local_tst_path,
                                                  self.objstore_test_path)
                message = "subtest : end of subtest.".center(width, '-')
                self.log.info(message)

                # sub_test 2, 3: verify append operations and rename file operations
                # below list contains the toggle for modify and rename operations in
                # generate_test_data() each element of list represent flag
                # for operations [modify, rename]

                # file_operations = [[append], [rename]]
                file_operations = [[True, False], [False, True]]

                for operation_flags in file_operations:
                    if operation_flags[0]:
                        operation = "append"
                        message = "subtest : verify append() operation".center(width, '-')
                    else:
                        operation = "rename"
                        message = "subtest : verify rename() operation".center(width, '-')
                    self.log.info(message)

                    self.nfsutil_obj.machine_obj.modify_test_data(self.local_tst_path,
                                                                  modify=operation_flags[0],
                                                                  rename=operation_flags[1])
                    self.log.info("test data {0}ed on path {1}".format(operation,
                                                                       self.local_tst_path))

                    self.nfsutil_obj.machine_obj.modify_test_data(self.objstore_test_path,
                                                                  modify=operation_flags[0],
                                                                  rename=operation_flags[1])
                    self.log.info("test data {0}ed on path {1}".format(operation,
                                                                       self.local_tst_path))

                    self.nfsutil_obj.compare_snapshot(self.local_tst_path,
                                                      self.objstore_test_path)
                    message = "subtest : end of subtest.".center(width, '-')
                    self.log.info(message)

                # subtest 4 : rename dirs and sub dirs
                try:
                    for path in [self.local_tst_path, self.objstore_test_path]:
                        folders_list = self.nfsutil_obj.machine_obj.get_folders_in_path(path)
                        self.log.info("folders found on path {1}: {0}".format(folders_list, path))
                        # we are assuming that folders list are sorted recursively.
                        # We need to go in reverse direction to avoid parent name change
                        # excluding the parent directory
                        for folder in folders_list[::-1][:-1]:
                            self.log.info("renaming file {0} to {1}".format(folder, folder+"_renamed"))
                            self.nfsutil_obj.machine_obj.rename_file_or_folder(folder,
                                                                               folder+"_renamed")

                    self.nfsutil_obj.compare_snapshot(self.local_tst_path, self.objstore_test_path)
                except Exception as e:
                    self.log.error("rename failed with error {0}".format(e))

                # subtest 5 : delete only files in the directories
                message = "subtest : verify delete() file operation".center(width, '-')
                self.log.info(message)
                self.nfsutil_obj.delete_files_in_path(self.local_tst_path)
                self.log.info("files under directory {0} deleted successfully".format(
                                                                            self.local_tst_path))
                self.nfsutil_obj.delete_files_in_path(self.objstore_test_path)
                self.log.info("files under directory {0} deleted successfully".format(
                                                                            self.objstore_test_path))
                self.nfsutil_obj.compare_snapshot(self.local_tst_path,
                                                  self.objstore_test_path)
                message = "subtest : end of subtest.".center(width, '-')
                self.log.info(message)

                # subtest 6 : delete directories. need to clear the data
                message = "subtest : verify delete() directory operation".center(width, '-')
                self.log.info(message)
                self.nfsutil_obj.machine_obj.generate_test_data(self.objstore_test_path,
                                                                hlinks=False)
                self.log.info("Created test data on path {0}".format(self.objstore_test_path))
                self.nfsutil_obj.machine_obj.remove_directory(self.objstore_test_path)
                if self.nfsutil_obj.machine_obj.check_directory_exists(self.objstore_test_path):
                    self.log.error("directory delete on share path failed")
                    self.log.error("directory content {0}".format(
                        self.nfsutil_obj.machine_obj.get_snapshot(self.objstore_test_path)))
                    raise Exception("directory delete on share path failed")
                self.log.info("directory delete on objectstore share path is successful")

                self.nfsutil_obj.machine_obj.unmount_path(self.nfsutil_obj.mount_dir)

                message = "subtest : end of subtest.".center(width, '-')
                self.log.info(message)

                message = "subtest :basic file operations for nfs v{0} client is successful".center(
                    width+10, '*')
                self.log.info(message.format(nfs_mount_version))
        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        self.nfsutil_obj.obj_store_cleanup(mounted_paths=self.mounted_dirs)
        self.NFS_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                   delete_user=True)
