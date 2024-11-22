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
        self.name = "NFS ObjectStore - Create PIT views with a different NFS Server other than" \
                    " that of the actual ObjectStore"
        self.product = self.products_list.OBJECTSTORE
        self.feature = self.features_list.OBJECTSTORENFS
        self.applicable_os = self.os_list.LINUX
        self.testcase = TestCase
        self.show_to_user = True
        self.tcinputs = {
            'NFSServerHostName': None,
            'SecondNFSServerHostName': None,
            'ClientHostname': None,
            'ClientUsername': None,
            'ClientPassword': None,
            'IndexServerClientName': None,
        }
        self.nfsutil_obj = None
        self.NFS_server_obj = None
        self.expected_dir_details = None
        self.objstore_test_path = None
        self.snap_test_path = None
        self.local_tst_path = None
        self.test_dir_name = 'folder1'
        self.mounted_dirs = []
        self.pit_write_path = None
        self.client = None
        self.snap_mount_path = None

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        self.nfsutil_obj = NFSutils(self.tcinputs['ClientHostname'],
                                    self.tcinputs['ClientUsername'],
                                    self.tcinputs['ClientPassword'],
                                    self.id,
                                    self.commcell)

        self.objstore_test_path = self.nfsutil_obj.\
            machine_obj.join_path(self.nfsutil_obj.mount_dir, self.test_dir_name)

        # as we cannot change permission of mount root directory, need to create a sub directory
        self.local_tst_path = self.nfsutil_obj.machine_obj.\
            join_path(self.nfsutil_obj.automation_temp_dir, 'localtestdir', self.test_dir_name)

        self.snap_test_path = self.nfsutil_obj.machine_obj.\
            join_path(self.nfsutil_obj.snap_mount_dir, self.test_dir_name)

        self.NFS_server_obj = NFSHelper(self.tcinputs['NFSServerHostName'],
                                        self.commcell,
                                        self.inputJSONnode['commcell']['commcellUsername'],
                                        self.inputJSONnode['commcell']['commcellPassword']
                                        )

        self.log.info("Creating Object Store: {0}".format(self.nfsutil_obj.Obj_store_name))
        share_path = self.NFS_server_obj.\
            create_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                   self.NFS_server_obj.storage_policy,
                                   self.tcinputs['IndexServerClientName'],
                                   self.tcinputs['NFSServerHostName'],
                                   allowed_nfs_clients="0.0.0.0",
                                   squashing_type="NO_ROOT_SQUASH",
                                   delete_if_exists=True)

        self.nfsutil_obj.machine_obj.mount_nfs_share(self.nfsutil_obj.mount_dir,
                                                     self.tcinputs['ClientHostname'],
                                                     share_path)
        self.mounted_dirs.append(self.nfsutil_obj.mount_dir)

        self.log.info("NFS objectstore mounted successfully on %s", self.nfsutil_obj.mount_dir)

    def run(self):
        """Main function for test case execution"""
        try:
            self.nfsutil_obj.machine_obj.create_directory(self.local_tst_path)
            self.log.debug("Successfully created directory: %s", self.local_tst_path)

            self.nfsutil_obj.machine_obj.generate_test_data(self.local_tst_path,
                                                            hlinks=False,
                                                            dirs=random.randint(1, 1))

            self.nfsutil_obj.machine_obj.copy_folder(self.local_tst_path,
                                                     self.nfsutil_obj.mount_dir)

            self.log.info("Sleeping...")
            time.sleep(60)

            # Expected time stamp format: "MM-DD-YYYY HH:MM:SS"
            timestamp1 = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y %H:%M:%S')
            self.log.info("Timestamp noted to create PIT view is: %s", timestamp1)

            # Create a PIT with the second NFS Server
            self.snap_mount_path = self.NFS_server_obj.\
                create_objectstore_snap(obj_store_name=self.nfsutil_obj.Obj_store_name,
                                        timestamp=timestamp1,
                                        allowed_nfs_clients=self.tcinputs['ClientHostname'],
                                        copy_precedence=0,
                                        ma_client=self.tcinputs['SecondNFSServerHostName'])

            # Making the PIT to RW access mode
            self.NFS_server_obj.update_objectstore_snap(self.nfsutil_obj.Obj_store_name,
                                                        mount_path=self.snap_mount_path,
                                                        access_permission="RW")

            # Mount the PIT view
            self.nfsutil_obj.machine_obj.mount_nfs_share(self.nfsutil_obj.snap_mount_dir,
                                                         self.tcinputs['SecondNFSServerHostName'],
                                                         self.snap_mount_path)
            self.mounted_dirs.append(self.nfsutil_obj.snap_mount_dir)

            self.log.info("PIT '%s' has been created successfully with the second NFS Server, "
                          "in RW mode", self.snap_mount_path)

            # Restore data from the PIT
            restore_dir = self.nfsutil_obj.machine_obj.join_path(self.local_tst_path,
                                                                 'PITRestorePath')
            self.nfsutil_obj.machine_obj.create_directory(restore_dir, True)
            self.nfsutil_obj.machine_obj.copy_folder(self.nfsutil_obj.snap_mount_dir,
                                                     restore_dir)
            self.log.info("Restore passed from the PIT: %s", self.snap_mount_path)

            # Try writing data to the RW PIT
            self.pit_write_path = self.nfsutil_obj.\
                machine_obj.join_path(self.nfsutil_obj.snap_mount_dir, 'PITWritePath')
            self.nfsutil_obj.machine_obj.copy_folder(self.local_tst_path, self.pit_write_path)
            self.log.info("Write Operation to the RW PIT '%s' successful", self.snap_mount_path)

            # Cleaning-up
            self.nfsutil_obj.machine_obj.remove_directory(self.local_tst_path)
            self.nfsutil_obj.machine_obj.remove_directory(restore_dir)
            self.nfsutil_obj.machine_obj.remove_directory(self.objstore_test_path)

            self.log.info("Testcase PASSED.")

        except Exception as excp:
            log_error = "Detailed Exception: {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.nfsutil_obj.server.fail(excp, "Test case failed in run function")
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""
        self.nfsutil_obj.obj_store_cleanup(mounted_paths=self.mounted_dirs)
        self.NFS_server_obj.delete_objectstore_snap(self.nfsutil_obj.Obj_store_name,
                                                    self.snap_mount_path, False)
        self.NFS_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                   delete_user=True)
