# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: LoopOver Small Files: Create, Modify and Delete with Rsync From Local to NFS Share

"""
import sys
import random

from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing Basic functionality verification for NFS objectstore PIT views"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "LoopOver Small Files: Create, Modify and Delete with Rsync From Local" \
                    " to NFS Share"
        self.product = self.products_list.OBJECTSTORE
        self.feature = self.features_list.OBJECTSTORENFS
        self.applicable_os = self.os_list.LINUX
        self.show_to_user = True
        self.tcinputs = {
            'NFSServerHostName': None,
            'clientHostname': None,
            'clientUsername': None,
            'clientPassword': None,
            'indexServerMA': None,
            'numWrites': 10
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

            if self.NFS_server_obj.nfs_serv_machine_obj.os_info.lower() == 'windows':
                raise Exception("Test case is not applicable for windows MA. We don't have support for rsync")
                
            self.log.info("Creating Object Store : {0}".format(self.nfsutil_obj.Obj_store_name))
            share_path = self.NFS_server_obj.create_nfs_objectstore(
                                                        self.nfsutil_obj.Obj_store_name,
                                                        self.NFS_server_obj.storage_policy,
                                                        self.tcinputs['indexServerMA'],
                                                        self.tcinputs['NFSServerHostName'],
                                                        self.tcinputs['clientHostname'],
                                                        squashing_type="NO_ROOT_SQUASH",
                                                        delete_if_exists=True)

            self.nfsutil_obj.machine_obj.mount_nfs_share(self.nfsutil_obj.mount_dir,
                                                         self.tcinputs['NFSServerHostName'],
                                                         share_path)
            self.mounted_dirs.append(self.nfsutil_obj.mount_dir)

            self.log.info("NFS objectstore mounted successfully on {0}".format(
                self.nfsutil_obj.mount_dir))
        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in setup function")

    def run(self):
        """Main function for test case execution"""
        if self.NFS_server_obj.nfs_serv_machine_obj.os_info.lower() == 'windows':
                raise Exception("Test case is not applicable for windows MA. We don't have support for rsync")
        width = 100
        try:
            for loop in range(int(self.tcinputs['numWrites'])):
                message = "iteration {0}".format(loop)
                message = message.center(width, '-')
                self.log.info(message)

                self.nfsutil_obj.machine_obj.create_directory(self.local_tst_path, force_create=True)
                self.log.debug("test local directory {0} created successfully".format(
                    self.local_tst_path))

                self.log.info("generating test data on local test path {0}".format(
                    self.local_tst_path))
                self.nfsutil_obj.machine_obj.generate_test_data(self.local_tst_path,
                                                                hlinks=False,
                                                                dirs=random.randint(3, 10),
                                                                files=random.randint(5, 20),
                                                                slinks=random.randint(5, 10))

                self.log.info(
                    "Syncing data between folders {0} and {1}".format(self.local_tst_path,
                                                                      self.nfsutil_obj.mount_dir))
                self.nfsutil_obj.machine_obj.rsync_local(self.local_tst_path,
                                                         self.nfsutil_obj.mount_dir)
                # TODO: meta data and ACL should be compared ?
                _ , folder_diff = self.nfsutil_obj.machine_obj.compare_checksum(self.local_tst_path,
                                                                            self.objstore_test_path)
                if folder_diff:
                    self.log.error("folders data didn't match for paths %s %s. folders diff %s"
                                   % (self.local_tst_path, self.objstore_test_path, folder_diff))
                else:
                    self.log.info("folders data matched for paths %s %s" % (self.local_tst_path,
                                                                             self.objstore_test_path))

                self.log.info("modifying data on local test path")
                self.nfsutil_obj.machine_obj.modify_test_data(self.local_tst_path,
                                                              modify=True)

                self.log.info(
                    "Syncing data between folders {0} and {1}".format(self.local_tst_path,
                                                                      self.nfsutil_obj.mount_dir))
                self.nfsutil_obj.machine_obj.rsync_local(self.local_tst_path,
                                                         self.nfsutil_obj.mount_dir)
                # TODO: meta data and ACL should be compared ?
                _, folder_diff = self.nfsutil_obj.machine_obj.compare_checksum(self.local_tst_path,
                                                                               self.objstore_test_path)
                if folder_diff:
                    self.log.error("folders data didn't match for paths %s %s. folders diff %s"
                                   % (self.local_tst_path, self.objstore_test_path, folder_diff))
                else:
                    self.log.info("folders data matched for paths %s %s" % (self.local_tst_path,
                                                                             self.objstore_test_path))

                self.nfsutil_obj.machine_obj.remove_directory(self.local_tst_path)
                self.log.info("test directory {0} removed successfully".format(
                    self.local_tst_path))
                self.nfsutil_obj.machine_obj.remove_directory(self.objstore_test_path)
                self.log.info("test directory {0} removed successfully".format(
                    self.objstore_test_path))

                message = "end of iteration {0}".format(loop)
                message = message.center(width, '-')
                self.log.info(message)
        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        self.nfsutil_obj.obj_store_cleanup(mounted_paths=self.mounted_dirs)
        self.NFS_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                   delete_user=True)
