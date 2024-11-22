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
import time
import datetime
import sys

from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from Server.serverhelper import ServerTestCases

VERSION_INTERVAL_MINS = 3


class TestCase(CVTestCase):
    """Class for executing Basic functionality verification for NFS objectstore PIT views"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "NFS ObjectStore: Basic tests on PIT view for NFS client"
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
        self.NFS_server_obj = None
        self.expected_dir_details = None
        self.objstore_test_path = None
        self.snap_test_path = None
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

            # as we cannot change permission of mount root directory, need to create a sub directory
            self.objstore_test_path = self.nfsutil_obj.machine_obj.join_path(
                                                                        self.nfsutil_obj.mount_dir,
                                                                        'folder1')
            self.snap_test_path = self.nfsutil_obj.machine_obj.join_path(
                                                                    self.nfsutil_obj.snap_mount_dir,
                                                                    'folder1')

            self.NFS_server_obj = NFSHelper(self.tcinputs['NFSServerHostName'],
                                            self.commcell,
                                            self.inputJSONnode['commcell']['commcellUsername'],
                                            self.inputJSONnode['commcell']['commcellPassword'],
                                            self.tcinputs.get('storagePolicy'))

            self.log.info("Creating Object Store : {0}".format(self.nfsutil_obj.Obj_store_name))
            share_path = self.NFS_server_obj.create_nfs_objectstore(
                                                        self.nfsutil_obj.Obj_store_name,
                                                        self.NFS_server_obj.storage_policy,
                                                        self.tcinputs['indexServerMA'],
                                                        self.tcinputs['NFSServerHostName'],
                                                        self.tcinputs['clientHostname'],
                                                        squashing_type="NO_ROOT_SQUASH",
                                                        delete_if_exists=True)

            self.log.info("updating objectstore with version interval %s minutes" % VERSION_INTERVAL_MINS)
            self.NFS_server_obj.update_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                       version_interval=VERSION_INTERVAL_MINS)
            self.log.info("version interval updated successfully")

            time.sleep(30)
            self.nfsutil_obj.machine_obj.mount_nfs_share(self.nfsutil_obj.mount_dir,
                                                         self.tcinputs['NFSServerHostName'],
                                                         share_path)
            self.mounted_dirs.append(self.nfsutil_obj.mount_dir)

            self.log.info("NFS objectstore mounted successfully on {0}".format(
                self.nfsutil_obj.mount_dir))

            self.nfsutil_obj.machine_obj.create_directory(self.objstore_test_path, force_create=True)
            self.log.debug("directory {0} created successfully".format(
                                                                self.objstore_test_path))

            # generate test data
            self.nfsutil_obj.machine_obj.generate_test_data(self.objstore_test_path,
                                                            hlinks=False)
            self.log.info("Created test data on path {0}".format(self.objstore_test_path))
            
            self.log.info("waiting for version interval time of %s minutes before "
                          "modifying test data" % VERSION_INTERVAL_MINS)
            time.sleep(VERSION_INTERVAL_MINS*60)

            # giving some additional time
            time.sleep(30)

            # get snapshot of test data generated
            self.expected_dir_details = self.nfsutil_obj.machine_obj.get_snapshot(
                                                                self.objstore_test_path)
            self.log.info("details of test data generated :{0}".format(self.expected_dir_details))
        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in setup function")

    def run(self):
        """Main function for test case execution"""
        try:
            # Expected time stamp format : "MM-DD-YYYY HH:MM:SS"
            timestamp1 = datetime.datetime.fromtimestamp(
                                                    time.time()).strftime('%m-%d-%Y %H:%M:%S')
            self.log.info("time stamp noted to create PIT view {0}".format(timestamp1))

            # allowing some time after test data creation
            time.sleep(10)

            self.log.info("modifying test data after PIT view time stamp")

            # Now modify the test data to verify the snapshot content
            self.nfsutil_obj.machine_obj.modify_test_data(self.objstore_test_path,
                                                          modify=True)

            # allowing some time after modifying test data
            time.sleep(10)

            self.log.info("creating PIT view for timestamp {0}".format(timestamp1))
            # create NFS object store snapshot
            self.snap_mount_path = self.NFS_server_obj.create_objectstore_snap(
                                                                self.nfsutil_obj.Obj_store_name,
                                                                timestamp1,
                                                                self.tcinputs['clientHostname'])

            # mount NFS PIT view share
            self.nfsutil_obj.machine_obj.mount_nfs_share(
                                                   self.nfsutil_obj.snap_mount_dir,
                                                   self.tcinputs['NFSServerHostName'],
                                                   self.snap_mount_path)
            self.mounted_dirs.append(self.nfsutil_obj.snap_mount_dir)

            # get snapshot of PIT view
            snap_dir_details = self.nfsutil_obj.machine_obj.get_snapshot(
                                                                    self.snap_test_path)
            self.log.info("data available on snapshot:{0}".format(snap_dir_details))

            self.nfsutil_obj.compare_snapshot_data(self.objstore_test_path,
                                                   self.snap_test_path,
                                                   self.expected_dir_details,
                                                   snap_dir_details)

        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        self.nfsutil_obj.obj_store_cleanup(mounted_paths=self.mounted_dirs)
        self.NFS_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                   delete_user=True)
