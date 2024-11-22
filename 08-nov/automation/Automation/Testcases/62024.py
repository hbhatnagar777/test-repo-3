# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Verifies PIT view has correct version of the file when created using below file operations
        1. file append
        2. truncate
        3. rename
        4. unlink
"""
import time
import datetime
import sys

from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from Server.serverhelper import ServerTestCases

VERSION_INTERVAL_MINS = 1
VERSIONS_SUPPORTED = ["VERSION_USING_UNLINK",
                      "VERSION_USING_RENAME",
                      "VERSION_USING_TRUNCATE",
                      "VERSION_USING_APPEND"]


class TestCase(CVTestCase):
    """Class for executing Basic functionality verification for NFS objectstore PIT views"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify HFS PIT view for different file operation supported"
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
            'SolrCloudName': None,
            'storagePolicy': None

        }
        self.nfsutil_obj = None
        self.NFS_server_obj = None
        self.objstore_test_path = None
        self.snap_test_path = None
        self.mounted_dirs = []
        self.server = None
        self.objstore_test_file = None
        self.file_size = 15 * 1024 * 1024
        self.objstore_test_file = None
        self.objstore_test_file_rename = None
        self.snap_test_file = None
        self.snap_test_file_rename = None

    def modify_test_data(self, file_operation):
        """
        modifies test file based on file operation passed

        Args:
            file_operation     (str)   - file operation to be performed on the file to create new version

         Returns:
                None

        Raises:
            Exception:
                If failed to execute the file modify command

        """
        self.log.info("modifying test data with operation %s" % file_operation)

        if file_operation == "VERSION_USING_TRUNCATE":
            if self.nfsutil_obj.machine_obj.os_info.lower() == 'windows':
                truncate_cmd = "fsutil file seteof %s %s".format(self.objstore_test_file,
                                                                 int(self.file_size / 2))
            else:
                truncate_cmd = "/usr/bin/truncate -s %s %s".format(int(self.file_size / 2),
                                                                   self.objstore_test_file)
            self.nfsutil_obj.machine_obj.execute_command(truncate_cmd)
        elif file_operation == "VERSION_USING_RENAME":
            self.nfsutil_obj.machine_obj.rename_file_or_folder(self.objstore_test_file,
                                                               self.objstore_test_file_rename)
        elif file_operation == "VERSION_USING_UNLINK":
            self.nfsutil_obj.machine_obj.delete_file(self.objstore_test_file)
        elif file_operation == "VERSION_USING_APPEND":
            self.nfsutil_obj.machine_obj.append_to_file(self.objstore_test_file,
                                                        "data modified")

    def verify_hfs_snap_file(self, file_operation):
        """
        verifies HFS pit view share has correct version of the file

        Args:
            file_operation     (str)   - file operation used to create the version

         Returns:
                None

        Raises:
            Exception:
                If file in PIT view version doesn't match with expected one

        """
        self.log.info("verifying data on PIT view")
        # get snapshot of test data generated
        share_checksum = self.nfsutil_obj.machine_obj.get_snapshot(self.objstore_test_path)
        snap_checksum = self.nfsutil_obj.machine_obj.get_snapshot(self.snap_test_path)
        self.log.info("data on share %s, data on PIT share %s" % (share_checksum,
                                                                  snap_checksum))
        if file_operation == "VERSION_USING_UNLINK":
            if self.nfsutil_obj.machine_obj.check_file_exists(self.snap_test_file):
                raise Exception("file %s exists on PIT vew" % self.snap_test_file)
        else:
            self.nfsutil_obj.compare_snapshot_data(self.objstore_test_path,
                                                   self.snap_test_path,
                                                   share_checksum,
                                                   snap_checksum)

    def validate_file_version(self):
        """
        validate HFS file version are created for all the file operations supported

        Raises:
            Exception:
                In case of any issues in validation

        """
        self.objstore_test_file = self.nfsutil_obj.machine_obj.join_path(self.objstore_test_path, 'file1')
        self.objstore_test_file_rename = self.nfsutil_obj.machine_obj.join_path(self.objstore_test_path,
                                                                                'file1_renamed')
        self.snap_test_file = self.nfsutil_obj.machine_obj.join_path(self.snap_test_path, 'file1')
        self.snap_test_file_rename = self.nfsutil_obj.machine_obj.join_path(self.snap_test_path,
                                                                            'file1_renamed')
        width = 50
        self.log.info('-' * width)
        for op_type in VERSIONS_SUPPORTED:
            message = "validating HFS file versions using file operation %s" % op_type
            message = message.center(width, '-')
            self.log.info(message)
            self.nfsutil_obj.machine_obj.create_file(self.objstore_test_file, '', file_size=self.file_size)
            self.log.info("waiting for version interval time of %s minutes before "
                          "modifying test data" % VERSION_INTERVAL_MINS)
            time.sleep(VERSION_INTERVAL_MINS * 60)

            # giving some additional time
            time.sleep(30)

            self.modify_test_data(op_type)

            # allowing some time after modifying test data
            time.sleep(60)

            # Expected time stamp format : "MM-DD-YYYY HH:MM:SS"
            timestamp1 = datetime.datetime.fromtimestamp(
                time.time()).strftime('%m-%d-%Y %H:%M:%S')

            self.log.info("creating PIT view for timestamp {0}".format(timestamp1))
            # create NFS object store snapshot
            snap_mount_path = self.NFS_server_obj.create_objectstore_snap(
                self.nfsutil_obj.Obj_store_name,
                timestamp1,
                self.tcinputs['clientHostname'])

            # mount NFS PIT view share
            self.nfsutil_obj.machine_obj.mount_nfs_share(
                self.nfsutil_obj.snap_mount_dir,
                self.tcinputs['NFSServerHostName'],
                snap_mount_path)
            self.log.debug("PIT view mounted successfully at %s" % self.nfsutil_obj.snap_mount_dir)

            time.sleep(60)
            try:
                self.verify_hfs_snap_file(op_type)
            except Exception as e:
                raise Exception("exception in validating pit view. exception %s" % e)
            finally:
                # deleting PIT views will be taken care when share is deleted
                self.nfsutil_obj.machine_obj.unmount_path(self.nfsutil_obj.snap_mount_dir)

            if self.nfsutil_obj.machine_obj.check_file_exists(self.objstore_test_file):
                self.nfsutil_obj.machine_obj.delete_file(self.objstore_test_file)

            self.log.info('-' * width)

        self.nfsutil_obj.check_objectstore_backup_job(self.nfsutil_obj.Obj_store_name)

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
                                                        self.tcinputs['SolrCloudName'],
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

        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in setup function")

    def run(self):
        """Main function for test case execution"""
        try:
            self.validate_file_version()
        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        self.nfsutil_obj.obj_store_cleanup(mounted_paths=self.mounted_dirs)
        self.NFS_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                   delete_user=True)
