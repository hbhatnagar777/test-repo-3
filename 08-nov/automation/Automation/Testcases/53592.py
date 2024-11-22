# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Verifies PIT view has the expected content with proper meta data from NFS share.

"""
import sys

from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from Server.NFSObjectStore.NFSACLHelper import NfsAclHelper as NFSACLHelper
from Server.serverhelper import ServerTestCases

class TestCase(CVTestCase):
    """Class for executing Basic functionality verification for NFS objectstore PIT views"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "NFS ObjectStore: Basic tests on NFS ACL"
        self.product = self.products_list.OBJECTSTORE
        self.feature = self.features_list.OBJECTSTORENFS
        self.applicable_os = self.os_list.LINUX
        self.show_to_user = True
        self.retval = 0
        self.tcinputs = {
            'NFSServerHostName': None,
            'clientHostname': None,
            'clientUsername': None,
            'clientPassword': None,
            'indexServerMA': None
        }
        self.nfsutil_obj = None
        self.nfs_server_obj = None
        self.expected_dir_details = None
        self.objstore_test_path = None
        self.snap_test_path = None
        self.mounted_dirs = []
        self.rcvd_exception = False
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

            self.nfs_acl_helper = NFSACLHelper(self.tcinputs['clientHostname'],
                                               self.commcell)

            self.nfs_server_obj = NFSHelper(self.tcinputs['NFSServerHostName'],
                                            self.commcell,
                                            self.inputJSONnode['commcell']['commcellUsername'],
                                            self.inputJSONnode['commcell']['commcellPassword'],
                                            self.tcinputs.get('storagePolicy'))

            self.log.info("Creating Object Store with ACL enabled: {0}".format(
                self.nfsutil_obj.Obj_store_name))
            share_path = self.nfs_server_obj.create_nfs_objectstore(
                                                        self.nfsutil_obj.Obj_store_name,
                                                        self.nfs_server_obj.storage_policy,
                                                        self.tcinputs['indexServerMA'],
                                                        self.tcinputs['NFSServerHostName'],
                                                        self.tcinputs['clientHostname'],
                                                        squashing_type="NO_ROOT_SQUASH",
                                                        acl_flag=True,
                                                        delete_if_exists=True)

            if self.nfsutil_obj.machine_obj.is_path_mounted(
                    self.nfsutil_obj.mount_dir):
                self.log.info("path {0} is already mounted. trying to forcefully unmount".format(
                    self.nfsutil_obj.mount_dir))
                self.nfsutil_obj.machine_obj.unmount_path(self.nfsutil_obj.mount_dir,
                                                          force_unmount=True)

            self.log.info("trying to mount share {0} on local path {1}".format(
                                                                        share_path,
                                                                        self.nfsutil_obj.mount_dir))
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
        try:
            test_path = self.nfsutil_obj.machine_obj.join_path(self.nfsutil_obj.mount_dir,
                                                               self.id)
            self.log.info("creating test directory {0}".format(test_path))
            if not self.nfsutil_obj.machine_obj.create_directory(test_path, force_create=True):
                raise Exception("test directory {0} creation failed".format(test_path))

            self.nfsutil_obj.machine_obj.change_file_permissions(
                                                        test_path,
                                                        self.nfs_acl_helper.allow_other_users)

            acl_tests = "all"
            self.log.info("verifying {1} ACL permissions for files"
                          " on test path {0}".format(test_path, acl_tests))
            self.nfs_acl_helper.verify_ace_file_permissions(test_path,
                                                            file_operations=acl_tests)

            self.log.info("verifying {1} ACL permissions for directory"
                          " on test path {0}".format(test_path, acl_tests))
            self.nfs_acl_helper.verify_ace_folder_permissions(test_path,
                                                              file_operations=acl_tests)
        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in run function")
            self.rcvd_exception = True

    def tear_down(self):
        """Tear down function"""
        # lets not clean up if any exceptions are raised in run function for debugging
        if not self.rcvd_exception:
            self.nfsutil_obj.obj_store_cleanup(mounted_paths=self.mounted_dirs)
            self.nfs_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                       delete_user=True)
        else:
            self.log.error("test failed in run function. not running clean up"
                           " for debugging the issue")
