# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: NFS objectstore Squashing Acceptance tests

"""
import sys
import random
import string

from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils

# from Server.NFSObjectStore.NFSObjectStoreConstants import DEFAULT_PASSWORD
# from Server.NFSObjectStore.NFSObjectStoreConstants import DEFAULT_ENCRYPTED_PASSWORD


class TestCase(CVTestCase):
    """Class for executing Basic functionality verification for NFS objectstore Squashing Acceptance tests"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "NFS objectstore Squashing Acceptance tests"
        self.product = self.products_list.OBJECTSTORE
        self.feature = self.features_list.OBJECTSTORENFS
        self.applicable_os = self.os_list.LINUX
        self.show_to_user = True
        # please note that storagePolicy is optional input
        self.tcinputs = {
            'NFSServerHostName': None,
            'clientHostname': None,
            'clientRootUsername': None,
            'clientRootPassword': None,
            'indexServerMA': None
        }
        self.nfsutil_obj = None
        self.NFS_server_obj = None
        self.expected_dir_details = None
        self.objstore_test_path = None
        self.snap_test_path = None
        self.local_tst_path = None
        self.mounted_dirs = []
        self.share_path = None
        self.non_root_username = None
        self.width = 100
        self.test_status = 0

    def validate_root_squash(self):
        """ validate root_squash """
        message = "subtest : validate NFS Objectstore ROOT_SQUASH".center(self.width, '-')
        self.log.info(message)
        self.test_status += self.nfsutil_obj.validate_squashed_user_perm(self.NFS_server_obj,
                                                                         "ROOT_SQUASH",
                                                                         self.tcinputs['clientRootUsername'],
                                                                         self.tcinputs['clientRootPassword'],
                                                                         self.share_path)

        self.test_status += self.nfsutil_obj.validate_squashed_user_perm(self.NFS_server_obj,
                                                                         "ROOT_SQUASH",
                                                                         self.non_root_username,
                                                                         self.tcinputs['DEFAULT_PASSWORD'],
                                                                         self.share_path)

        message = "subtest : ROOT_SQUASH end of subtest.".center(self.width, '-')
        self.log.info(message)

    def validate_all_squash(self):
        """ validate all_squash """
        message = "subtest : validate NFS Objectstore ALL_SQUASH".center(self.width, '-')
        self.log.info(message)
        self.test_status += self.nfsutil_obj.validate_squashed_user_perm(self.NFS_server_obj,
                                                                         "ALL_SQUASH",
                                                                         self.tcinputs['clientRootUsername'],
                                                                         self.tcinputs['clientRootPassword'],
                                                                         self.share_path)

        self.test_status += self.nfsutil_obj.validate_squashed_user_perm(self.NFS_server_obj,
                                                                         "ALL_SQUASH",
                                                                         self.non_root_username,
                                                                         self.tcinputs['DEFAULT_PASSWORD'],
                                                                         self.share_path)

        message = "subtest : ALL_SQUASH end of subtest.".center(self.width, '-')
        self.log.info(message)

    def validate_no_root_squash(self):
        """ validate no_root_squash """
        message = "subtest : validate NFS Objectstore NO_ROOT_SQUASH".center(self.width, '-')
        self.log.info(message)
        self.test_status += self.nfsutil_obj.validate_squashed_user_perm(self.NFS_server_obj,
                                                                         "NO_ROOT_SQUASH",
                                                                         self.tcinputs['clientRootUsername'],
                                                                         self.tcinputs['clientRootPassword'],
                                                                         self.share_path)

        self.test_status += self.nfsutil_obj.validate_squashed_user_perm(self.NFS_server_obj,
                                                                         "NO_ROOT_SQUASH",
                                                                         self.non_root_username,
                                                                          self.tcinputs['DEFAULT_PASSWORD'],
                                                                         self.share_path)

        message = "subtest : NO_ROOT_SQUASH end of subtest.".center(self.width, '-')
        self.log.info(message)

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        self.nfsutil_obj = NFSutils(self.tcinputs['clientHostname'],
                                    self.tcinputs['clientRootUsername'],
                                    self.tcinputs['clientRootPassword'],
                                    self.id,
                                    self.commcell)

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

    def run(self):
        """Main function for test case execution"""
        try:
            # to avoid uid caching issue with ganesha added random string
            self.non_root_username = "non_root_squash_user_" + \
                                     ''.join(random.choice(string.ascii_lowercase) for _ in range(4))
            self.log.info("creating a test non root user %s" % self.non_root_username)
            self.nfsutil_obj.machine_obj.add_user(self.non_root_username, self.tcinputs['DEFAULT_ENCRYPTED_PASSWORD'])

            self.validate_root_squash()

            self.validate_all_squash()

            self.validate_no_root_squash()

            if self.test_status != 0:
                raise Exception("NFS objectstore Squashing test %s failed" % self.id)
            else:
                self.log.error("NFS objectstore Squashing test %s passed" % self.id)

        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.nfsutil_obj.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        self.nfsutil_obj.machine_obj.delete_users([self.non_root_username])
        self.nfsutil_obj.obj_store_cleanup(mounted_paths=[self.nfsutil_obj.mount_dir])
        self.NFS_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                   delete_user=True)