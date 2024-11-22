# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

"""File for performing NFS server related operations in Commcell

ObjectstoreClientUtils and NFSServerHelper are 2 classes defined in this file.

ObjectstoreClientUtils: Class for providing common functions for test clients

NFSServerHelper: Class for providing NFS server related operations

ObjectstoreClientUtils:
    __init__()                    --  initialize instance of the ObjectstoreClientUtils class
    by defining common test paths

    obj_store_cleanup()           --  performs basic cleanup operations for NFS objectstore

    compare_snapshot_data()       -- Performs common NFS objectstore snapshot comparison for
    given two paths

    compare_snapshot()            --  Performs common NFS objectstore snapshot comparsion for
    given two paths

    delete_files_in_path()        --  delete all the files (not directories) from the given path

    validate_root_data_access()   --  validate squashing is successful

    create_data_before_squash()   --  create data before squashing is applied to objectstore

    data_access_after_squash()    --  verify data created with root user can be accessed from
    user in question

    create_data_after_squash()    --  create test data as squashed user and verify that user id is
    squashed as expected

    validate_squashed_user_perm() --  Validates all types of Unix Squashing for NFS objectstore shares

    check_objectstore_backup_job()-- check for objectstore active backup Job and wait
    for its completion

    create_test_data_objecstore() -- create files on given objectstore and wait for
    3dfs backup job to complete

NFSServerHelper:
    __init__()                    --  initialize instance of the NFSServerHelper class

    create_nfs_objectstore()      --  creates NFS objectstore

    list_all_nfs_objectstore()    --  list currently available NFS objectstore shares

    show_nfs_objectstore()        --  Shows details about given NFS objectstore

    delete_nfs_objectstore()      --  Deletes given NFS objectstore

    update_nfs_objectstore()      --  Update details for the given NFS objectstore

    create_objectstore_snap()     --  creates NFS objectstore snap

    show_objectstore_snap()       --  shows currently available Snaps for the given share

    update_objectstore_snap()     --  pdate details for the given NFS objectstore snap

    delete_objectstore_snap()     --  Deletes given NFS objectstore snap

    get_objectstore_subclient_id()--  gets subclient ID for given objectstore name

    parse_3dnfs_logs()            --  parse 3dnfs logs for given pattern raised
    after given time stamp

"""
import re
import time
import datetime
import string
import random
import os

from AutomationUtils import logger
from AutomationUtils.machine import Machine
from cvpysdk.job import JobController
from Server.JobManager.jobmanager_helper import JobManager

from AutomationUtils.constants import UNIX_TMP_DIR
from AutomationUtils.constants import WINDOWS_TMP_DIR
from .NFSObjectStoreConstants import NFS_TEST_MOUNT_DIR_NAME
from .NFSObjectStoreConstants import NFS_TEST_SNAP_MOUNT_NAME
from .NFSObjectStoreConstants import NFS_OBJECTSTORE_NAME
from .NFSObjectStoreConstants import CVLT_BASE_DIR


class ObjectstoreClientUtils:
    """NFS objectstore utils class to perform common operations for test clients"""

    def __init__(self, client_name, username, password, test_id, commcell):
        """Initialize instance of the ObjectstoreClientUtils class..

            Args:
                client_name   (str)     -- hostname or IP address of test client machine

                username      (str)     -- login username of client_name

                password      (str)     -- login password of client_name

                test_id       (int)     -- testcase id of calling script

                commcell      (object)  --  instance of the Commcell class

            Returns:
                object - instance of the ObjectstoreClientUtils class
        """

        self.log = logger.get_log()
        if client_name in commcell.clients.all_clients:
            # if client machine is a commcell client
            self.machine_obj = Machine(client_name, commcell)
        else:
            # if client machine is not a commcell client
            self.machine_obj = Machine(client_name, username=username, password=password)

        if self.machine_obj.os_info.lower() == 'windows':
            tst_temp_path = WINDOWS_TMP_DIR
        else:
            tst_temp_path = UNIX_TMP_DIR

        self.automation_temp_dir = self.machine_obj.join_path(tst_temp_path, test_id)
        self.mount_dir = self.machine_obj.join_path(self.automation_temp_dir,
                                                    NFS_TEST_MOUNT_DIR_NAME + test_id)
        self.snap_mount_dir = self.machine_obj.join_path(self.automation_temp_dir,
                                                         NFS_TEST_SNAP_MOUNT_NAME + test_id)

        self.Obj_store_name = NFS_OBJECTSTORE_NAME + '-' + test_id + '-' + \
                              ''.join(random.choice(string.ascii_lowercase) for _ in range(6))
        self.client_name = client_name
        self.commcell = commcell
        self.hfs_software_list = ["Index Store","Indexing Server" ,"High Availability Computing"]

    def obj_store_cleanup(self, mounted_paths=None, force_cleanup=False):
        """Performs common NFS objectstore cleanup operations such has unmount local mount
        paths and delete objectstore created in test

            Args:
                mounted_paths (list)    -- list of local mount directories to unmount

                force_cleanup (bool)    --  forces unmount of stale file handles

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in the cleanup operations

        """
        if not mounted_paths:
            mounted_paths = []

        # cleanup will be called in case of previous abnormal exit. Hence conditions need to be
        # applied before deleting
        self.log.info("cleaning up test data")
        for mount_path in mounted_paths:
            if self.machine_obj.check_directory_exists(mount_path):
                if self.machine_obj.is_path_mounted(mount_path):
                    self.machine_obj.unmount_path(mount_path,
                                                  delete_folder=True,
                                                  force_unmount=force_cleanup)
                    self.log.info("path {0} unmounted successfully".format(mount_path))

        if self.machine_obj.check_directory_exists(self.automation_temp_dir):
            self.machine_obj.remove_directory(self.automation_temp_dir)
            self.log.info("test directory {0} deleted successfully".format(
                                                                self.automation_temp_dir))

    def compare_snapshot_data(self, path1, path2, snap1, snap2):
        """Performs common NFS objectstore snapshot comparison for given two paths

            Args:
                path1 (string)    --  first path of the folder to compare the data

                path2 (string)    --  second path of the folder to compare the data

                snap1 (list)      -- list containing details of path1. output of get_snapshot()

                snap2 (list)      -- list containing details of path2. output of get_snapshot()

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in the cleanup operations

        """
        # to make comparision easier lets replace the base folder of mount paths
        # before comparing the data
        snap2 = [line.replace(path2, path1) for line in snap2]
        self.log.debug("Simplified data to compare: {0}".format(str(snap2)))

        output = self.machine_obj._compare_lists(snap1, snap2, sort_list=True)
        if output[0]:
            self.log.info("snapshot data matched on share and PIT view")
        else:
            raise Exception("snapshot data didn't match. data diff:{0}".format(output[1]))

    def compare_snapshot(self, path1, path2):
        """gets the snapshots of given directories and performs common NFS objectstore snapshot
        comparison for given two paths

            Args:
                path1 (string)    --  first path of the folder to compare the data

                path2 (string)    --  second path of the folder to compare the data

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in the cleanup operations

        """
        snap1 = self.machine_obj.get_snapshot(path1)
        snap2 = self.machine_obj.get_snapshot(path2)

        self.compare_snapshot_data(path1, path2, snap1, snap2)

    def delete_files_in_path(self, dir_path):
        """delete all the files (not directories) from the given path

            Args:
                dir_path (string)    --  path of the directory to delete the files

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in the cleanup operations

        """
        try:
            for file_path in self.machine_obj.get_files_in_path(dir_path):
                self.machine_obj.delete_file(file_path)
        except Exception as excep:
            raise Exception("exception occurred in delete_files_in_path(), "
                            "Exception:{0}".format(excep))

    def validate_root_data_access(self, squash_type, exception, username):
        """validate squashing is successful

            Args:
                squash_type (string)    --  Unix Squash type

                exception   (bool)      --  received exception with squashed user file operation

                username (str)          --  username of the user attempting to access data

            Returns:
                Boolean (True - if test cases passed, False - if test case failed)

            Raises:
                True  - if test case is passed
                False - if test case is failed
        """
        ret_val = True
        if squash_type == "NO_ROOT_SQUASH" or \
                (squash_type == "ROOT_SQUASH" and username != "root"):
            if exception:
                ret_val = False
                self.log.error("access is denied for user %s with squash type %s" %
                               (username, squash_type))
            else:
                self.log.info("***** access is allowed for user %s with squash type %s as expected" %
                              (username, squash_type))
        else:
            if not exception:
                ret_val = False
                self.log.error("access is allowed with for user %s squash type %s" %
                               (username, squash_type))
            else:
                self.log.info("****** access is denied with for user %s with squash type %s as expected" %
                              (username, squash_type))

        return ret_val

    def create_data_before_squash(self, nfs_serv_obj, share_path, squash_type, username):
        """ create data before squashing is applied to objectstore

            Args:
                nfs_serv_obj (obj)    --  Instance of NFSServerHelper class

                share_path (string)   --  objectstore share path to be used in mount command

                squash_type (string)  -- squash type in test

                username    (string)  -- user name in test

            Returns:
                list [file path, directory path] created with root user
        """
        content = "writing from user {0}".format(self.machine_obj)
        root_squash_type = "NO_ROOT_SQUASH"

        self.log.info("modifying squash type %s for objectstore %s" % (root_squash_type, self.Obj_store_name))
        nfs_serv_obj.update_nfs_objectstore(self.Obj_store_name, squash_type=root_squash_type)

        # allowing some time to update NFS ganesha
        time.sleep(10)

        self.log.info("mounting NFS objectstore %s on  path %s" % (self.Obj_store_name, self.mount_dir))
        self.machine_obj.mount_nfs_share(self.mount_dir, nfs_serv_obj.nfs_server_hostname, share_path)

        file_path = self.machine_obj.join_path(self.mount_dir, "testfile-beforesquash")
        dir_path = self.machine_obj.join_path(self.mount_dir, "testdir-beforesquash")

        self.log.info("creating test data as user %s before squashing in share" % self.machine_obj)
        if self.machine_obj.check_file_exists(file_path):
            self.machine_obj.delete_file(file_path)
        self.machine_obj.create_file(file_path, content)

        if self.machine_obj.check_directory_exists(dir_path):
            self.machine_obj.remove_directory(dir_path)
        self.machine_obj.create_directory(dir_path)

        if squash_type == "ALL_SQUASH" or \
                (squash_type == "ROOT_SQUASH" and username == "root"):
            self.machine_obj.change_file_permissions(file_path, "755")
            self.machine_obj.change_file_permissions(dir_path, "755")
        else:
            self.machine_obj.change_file_permissions(file_path, "777")
            self.machine_obj.change_file_permissions(dir_path, "777")

        self.log.info("un-mounting objectstore share %s" % self.Obj_store_name)
        self.machine_obj.unmount_path(self.mount_dir)

        return file_path, dir_path

    def data_access_after_squash(self, nfs_serv_obj, squash_type, share_path, file_path, dir_path,
                                 user_machine_obj, username):
        """ verify data created with root user can be accessed from user in question

            Args:
                nfs_serv_obj (obj)    --  Instance of NFSServerHelper class

                squash_type (string)    --  Unix Squash type

                share_path (string)   --  objectstore share path to be used in mount command

                file_path  (string)   --  file path to be modified from given user

                dir_path   (string)   -- directory path in which file will be created with given user

                user_machine_obj (obj) -- machine object of user to be tested for squash

                username   (string)   -- username of the user to be tested for squash (i.e. user_machine_obj)

            Returns:
                True - if all test cases passed
                False - if any test case failed
        """
        content = "writing from user {0}".format(user_machine_obj)
        file_path_in_dir = self.machine_obj.join_path(dir_path, "testfile2")

        self.log.info("modifying squash type %s for objectstore %s" % (squash_type, self.Obj_store_name))
        nfs_serv_obj.update_nfs_objectstore(self.Obj_store_name, squash_type=squash_type)

        # allowing some time to update NFS ganesha
        time.sleep(10)

        self.log.info("mounting NFS objectstore %s on  path %s" % (self.Obj_store_name, self.mount_dir))
        self.machine_obj.mount_nfs_share(self.mount_dir, nfs_serv_obj.nfs_server_hostname, share_path)

        self.log.info("modifying file %s after squashing set to %s" % (file_path, squash_type))
        _exception = False
        try:
            user_machine_obj.modify_content_of_file(file_path)
        except Exception as excp:
            _exception = True
            self.log.info("exception received %s" % excp)

        ret_val_1 = self.validate_root_data_access(squash_type, _exception, username)

        self.log.info("creating file in folder %s after squashing set to %s" % (file_path_in_dir, squash_type))
        _exception = False
        try:
            user_machine_obj.create_file(file_path_in_dir, content)
        except Exception as excp:
            _exception = True
            self.log.info("exception received %s" % excp)

        ret_val_2 = self.validate_root_data_access(squash_type, _exception, username)

        self.log.info("un-mounting objectstore share %s" % self.Obj_store_name)
        self.machine_obj.unmount_path(self.mount_dir)

        return all([ret_val_1, ret_val_2])

    def create_data_after_squash(self, nfs_serv_obj, squash_type, share_path, user_machine_obj, username):
        """ create test data as squashed user and verify that user id is squashed as expected

            Args:
                nfs_serv_obj (obj)    --  Instance of NFSServerHelper class

                squash_type (string)    --  Unix Squash type

                share_path (string)   --  objectstore share path to be used in mount command

                user_machine_obj (obj) -- machine object of user to be tested for squash

                username         (str) -- user name of the squsahed user (i.e. user_machine_obj)

            Returns:
                True - if all test cases passed
                False - if any test case failed
        """
        content = "writing from user {0}".format(username)
        squashing = False
        if (squash_type == "ROOT_SQUASH" and username == "root") \
                or squash_type == "ALL_SQUASH":
            squashing = True
            _error_msg = "user %s is not squashed" % username
            _info_msg = "***** as expected, user %s is squashed" % username
        else:
            _error_msg = "user %s is squashed unexpectedly" % username
            _info_msg = "***** as expected, user %s is not squashed" % username

        file_path = self.machine_obj.join_path(self.mount_dir, "testfile-aftersquash")
        dir_path = self.machine_obj.join_path(self.mount_dir, "testdir-aftersquash")

        self.log.info("modifying squash type %s for objectstore %s" % (squash_type, self.Obj_store_name))
        nfs_serv_obj.update_nfs_objectstore(self.Obj_store_name, squash_type=squash_type)

        # allowing some time to update NFS ganesha
        time.sleep(10)

        self.log.info("mounting NFS objectstore %s on  path %s" % (self.Obj_store_name, self.mount_dir))
        self.machine_obj.mount_nfs_share(self.mount_dir, nfs_serv_obj.nfs_server_hostname, share_path)

        self.log.info("creating test file after squashing")
        user_machine_obj.create_file(file_path, content)
        owner_test_file = self.machine_obj.get_file_owner(file_path)
        ret_val = (owner_test_file == username) if squashing else (owner_test_file != username)
        if ret_val:
            self.log.error(_error_msg)
            self.log.error("test file path: %s, owner:%s" % (file_path, owner_test_file))
        else:
            self.log.info(_info_msg)

        self.log.info("creating test folder after squashing")
        user_machine_obj.create_directory(dir_path)
        owner_test_file = self.machine_obj.get_file_owner(dir_path)
        ret_val = (owner_test_file == username) if squashing else (owner_test_file != username)
        if ret_val:
            self.log.error(_error_msg)
            self.log.error("test file path: %s, owner:%s" % (file_path, owner_test_file))
        else:
            self.log.info(_info_msg)

        user_machine_obj.delete_file(file_path)
        user_machine_obj.remove_directory(dir_path)

        self.log.info("un-mounting objectstore share %s" % self.Obj_store_name)
        self.machine_obj.unmount_path(self.mount_dir)

        # to make it inline with other return type we are negating the return value below
        return not ret_val

    def validate_squashed_user_perm(self,
                                    nfs_serv_obj,
                                    squash_type,
                                    squash_username,
                                    squash_user_password,
                                    share_path):
        """Validates all types of Unix Squashing for NFS objectstore shares

            Args:
                nfs_serv_obj (obj)    --  Instance of NFSServerHelper class

                squash_type (string)    --  Unix Squash type.
                    expected values: ["ROOT_SQUASH", "ALL_SQUASH", "NO_ROOT_SQUASH"]

                squash_username (string)   --  user name to be used for validation

                squash_user_password (obj) -- password for the above squash user

                share_path         (str) -- NFS objectstore share path which will be used in mounting the share

            Returns:
                False - if all test cases passed
                True  - if any test case failed

            Raises:
                Exception:
                    if any error occurs in the validation

        """
        valid_squash_types = ["ROOT_SQUASH", "ALL_SQUASH", "NO_ROOT_SQUASH"]
        if squash_type not in valid_squash_types:
            raise Exception("invalid squash type %s passed" % squash_type)

        self.log.info("***** validating squash type %s with user %s" % (squash_type, squash_username))

        file_path, dir_path = self.create_data_before_squash(nfs_serv_obj, share_path, squash_type,
                                                             squash_username)

        user_machine_obj = Machine(self.client_name, username=squash_username, password=squash_user_password)
        ret_val_scenrio1 = self.data_access_after_squash(nfs_serv_obj, squash_type, share_path, file_path,
                                                dir_path, user_machine_obj, squash_username)

        ret_val_scenrio2 = self.create_data_after_squash(nfs_serv_obj, squash_type, share_path,
                                                         user_machine_obj, squash_username)
        self.machine_obj.delete_file(file_path)
        self.machine_obj.remove_directory(dir_path)

        return not all([ret_val_scenrio1, ret_val_scenrio2])

    def check_objectstore_backup_job(self, objectstore_client_name):
        """check for objectstore active backup Job and wait for its completion
            Args:
                objectstore_client_name (str)  -- name of objectstore

            Returns:
                None

            Raises:
                Exception:
                    if backup job doesn't complete successfully
        """
        self.commcell.refresh()
        # check for backup Job complete
        self.log.info("checking backup Jobs for objectstore client")
        jobs = self.commcell.job_controller.active_jobs(
            client_name=objectstore_client_name,
            options={'job_type': '3DFS Backup'})
        max_try = 30
        job_triggered = False
        attempt = 0
        while attempt < max_try and not job_triggered:
            if bool(jobs):
                job_triggered = True
            else:
                self.log.info("backup Job is not yet running for objectstore client")
                time.sleep(10)
                attempt += 1

            jobs = self.commcell.job_controller.active_jobs(
                client_name=objectstore_client_name,
                options={'job_type': '3DFS Backup'})
            self.log.debug("active jobs %s", jobs)

        if not job_triggered:
            self.log.error("backup job is not triggered for objectstore")
            return

        job = [key for key in jobs.keys()][0]
        job_manager = JobManager(_job=job, commcell=self.commcell)
        self.log.info("waiting for job %s for client %s to complete" % (
            job, objectstore_client_name))
        job_manager.wait_for_state(expected_state='completed')
        self.log.info("backup Job %s is completed", job)

    def create_test_data_objecstore(self,
                                    num_of_files_create,
                                    machine_obj,
                                    test_path,
                                    objectstore_client_name,
                                    file_size=(1024 * 1024 * 1024)):
        """create files on given objectstore and wait for 3dfs backup job to complete
            Args:
                num_of_files_create (int)  -- number of files to create

                machine_obj (obj)    --  machine object of client where objectstore
                                         is mounted

                test_path   (str)    --  test path where files need to be created
                                         (also where objectstore is mounted)

                objectstore_client_name (str) -- name of objectstore client

                file_size  (int)     --  file size to be created

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in creating file
        """
        self.log.info("creating %s test files on path %s" % (num_of_files_create,
                                                             test_path))

        if not machine_obj.check_directory_exists(test_path):
            self.log.info("creating test path %s", test_path)
            machine_obj.create_directory(test_path)

        for num in range(num_of_files_create):
            file_path = machine_obj.join_path(test_path, "testfile" + str(num))
            self.log.debug("creating file %s", file_path)
            machine_obj.create_file(file_path, '', file_size=file_size)

        self.log.info("test files created successfully")

        self.check_objectstore_backup_job(objectstore_client_name)
    
    def check_objectstore_install_job(self, objectstore_client_name):
        """check for objectstore active install Job and wait for its completion

            Returns:
                None

            Raises:
                Exception:
                    if Install job doesn't complete successfully
        """
        self.commcell.refresh()
        # check for Install Job complete
        self.log.info("checking Install Jobs for objectstore client")
        jobs = self.commcell.job_controller.active_jobs(
            client_name=objectstore_client_name,
            options={'job_type': 'Install Software'})
        max_try = 30
        job_triggered = False
        attempt = 0
        while attempt < max_try and not job_triggered:
            if bool(jobs):
                job_triggered = True
            else:
                self.log.info("Install Job is not yet running for objectstore client")
                time.sleep(10)
                attempt += 1

            jobs = self.commcell.job_controller.active_jobs(
                client_name=objectstore_client_name,
                options={'job_type': 'Install Software'})
            self.log.debug("active jobs %s", jobs)

        if not job_triggered:
            self.log.error("Install job is not triggered for objectstore")
            return

        job = [key for key in jobs.keys()][0]
        job_manager = JobManager(_job=job, commcell=self.commcell)
        self.log.info("waiting for job %s for client %s to complete" % (
            job, objectstore_client_name))
        job_manager.wait_for_state(expected_state='completed')
        self.log.info("Install Job %s is completed", job)
    
    def check_hfs_components(self, hfs_client_name, wait_time=30,attempts=10):
        """checks if all 3 componets are created when we create a new HFS share from Command center.

        Args:
            hfs_client_name (str): name of the file server
            wait_time (int): wait time for each component
        """
        curr = 0
        hac_cluster = False
        index_pool = False
        index_server = False
        while curr<attempts:
            self.log.info("Checking if HAC cluster {0}_HACCluster is created".format(hfs_client_name))
            if self.commcell.hac_clusters.has_cluster("{0}_HACCluster".format(hfs_client_name)):
                self.log.info("Got the required HAC cluster")
                hac_cluster = True
                break
            time.sleep(wait_time)
            curr += 1
        curr = 0
        while curr<attempts and hac_cluster:
            self.log.info("Checking if Index Pool {0}_IndexServerPool is created".format(hfs_client_name))
            if self.commcell.hac_clusters.has_cluster("{0}_IndexServerPool".format(hfs_client_name)):
                self.log.info("Got the required IndexServerPool")
                index_pool = True
                break
            time.sleep(wait_time)
            curr += 1
        curr = 0
        while curr<attempts and index_pool:
            self.log.info("Checking if Index Pool {0}_AnalyticsServer is created".format(hfs_client_name))
            if self.commcell.hac_clusters.has_cluster("{0}_AnalyticsServer".format(hfs_client_name)):
                self.log.info("Got the required IndexServer")
                index_server = True
                break
            time.sleep(wait_time)
            curr += 1
        
        if hac_cluster and index_pool and index_server:
            self.log.info("All components are created successfully")
        else:
            raise Exception("HFS component is not created successfully.")

    def delete_hfs_components(self, hfs_client_name=None, indexserver=None, indexpool=None, haccluster=None):
        """Delete all HFS components, indexserver, indexserverpool,HAC cluster

        Args:
            hfs_client_name (str): name of HFS file server name.
            indexserver (str): name of index server.
            indexpool (str): name of index server pool.
            haccluster (str): name of hac cluster.
        """
        if hfs_client_name:
            self.log.info(
                "Deleting " + "{0}_AnalyticsServer".format(hfs_client_name))
            self.commcell.index_servers.delete(
                "{0}_AnalyticsServer".format(hfs_client_name))
            self.log.info(
                "Deleting " + "{0}_IndexServerPool".format(hfs_client_name))
            self.commcell.index_pools.delete(
                "{0}_IndexServerPool".format(hfs_client_name))
            self.log.info(
                "Deleting " + "{0}_HACCluster".format(hfs_client_name))
            self.commcell.hac_clusters.delete(
                "{0}_HACCluster".format(hfs_client_name))
        else:
            if indexserver:
                self.log.info("Deleting IndexServer")
                self.commcell.index_servers.delete(indexserver)
            if indexpool:
                self.log.info("Deleting IndexServerPool")
                self.commcell.index_pools.delete(indexpool)
            if haccluster:
                self.log.info("Deleting HAC cluster")
                self.commcell.hac_clusters.delete(haccluster)


    def uninstall_hfs_softwares(self,hfs_client_name):
        """To uninstall all HFS/Indexing pacakges from File server machine

        Args:
            hfs_client_name (str): name of HFS file server name.
        """
        client_obj = self.commcell.clients.get(hfs_client_name)
        self.log.info("Uninstalling the HFS packages" + ' '.join(self.hfs_software_list))
        client_obj.uninstall_software(software_list=self.hfs_software_list) # to remove selected packages from the client

    
    def delete_db_entries(self,utility,entity):
        """to delete all the HFS DB entries
        Args:
            utility (object): utility object of OptionsSelector class
            entity (str): name of fileserver
        """
        if not entity:
            raise Exception("empty string not supported")
        query = "delete from IdxAccessPath where ClientId = {0}".format(
            self.client.client_id)
        self.log.info("Executing Query:" + query)
        utility.update_commserve_db(query)
        query = "delete from IdxCache where Description like '{0}_%' or Description like '%_{0}'".format(
            entity)
        self.log.info("Executing Query:" + query)
        utility.update_commserve_db(query)
        query = "delete from IdxPool where Description like '{0}_%' or Description like '%_{0}'".format(
            entity)
        self.log.info("Executing Query:" + query)
        utility.update_commserve_db(query)

    def remove_hfs_additional_software(self):
        """Removes dokany or ganesha packages based on machine type
        Returns:
            [type]: [description]
        """
        if self.machine_obj.os_info.lower() == 'windows':
            package = "Dokan Library 1.4.0.1000 (x64)"
        else:
            raise NotImplementedError("for ganesha not implemented yet")
        self.machine_obj.remove_additional_software(package=package)

class NFSServerHelper:
    """NFS objectstore class to perform NFS server related operations"""

    def __init__(self, nfs_server_hostname, commcell, commcell_user,
                 commcell_password, storage_policy=None):
        """Initialize instance of the NFSServerHelper class.

            Args:
                nfs_server_hostname  (str)       --  hostname of NFS server

                commcell            (object)     --  instance of the Commcell class

                commcell_user       (str)        -- commcell admin user name

                commcell_password   (str)        -- commcell admin password

                storage_policy      (str)        --  Storage policy to be used with objectstore
                    Value is None we will pick the first SP from commcell.storage_policies.all_storage_policies

            Returns:
                object - instance of the NFSServerHelper class
        """
        self.log = logger.get_log()
        self.nfs_server_hostname = nfs_server_hostname

        self.nfs_serv_client_obj = commcell.clients.get(nfs_server_hostname)
        self.nfs_serv_machine_obj = Machine(self.nfs_serv_client_obj)

        self.cvlt_basedir = self.nfs_serv_machine_obj.join_path(
                                                       self.nfs_serv_client_obj.install_directory,
                                                       CVLT_BASE_DIR)
        self.cmd_prefix = self.nfs_serv_machine_obj.join_path(
                                                    self.nfs_serv_client_obj.install_directory,
                                                    "galaxy_vm;")
        if self.nfs_serv_machine_obj.os_info.lower() == "windows":
            self.cmd_prefix = ''
            self.config_cmd_with_prefix = "\"{0}{1}ConfigureObjectStore.exe\"".format(
                                                            self.cvlt_basedir,
                                                            self.nfs_serv_machine_obj.os_sep)
            _qlogin_command = "& \"{0}{1}qlogin.exe\" -u {2} -clp \"{3}\"".format(
                                                            self.cvlt_basedir,
                                                            self.nfs_serv_machine_obj.os_sep,
                                                            commcell_user,
                                                            commcell_password)
        else:
            self.config_cmd_with_prefix = "{0}{1}{2}ConfigureObjectStore".format(
                                                            self.cmd_prefix,
                                                            self.cvlt_basedir,
                                                            self.nfs_serv_machine_obj.os_sep)
            _qlogin_command = "{0}{1}qlogin -u {2} -clp \'{3}\'".format(
                                                            self.cvlt_basedir,
                                                            self.nfs_serv_machine_obj.os_sep,
                                                            commcell_user,
                                                            commcell_password)
        self.job_controller = JobController(commcell)
        self.job_manager = None

        if storage_policy is None:
            storage_policies = commcell.storage_policies.all_storage_policies
            if storage_policies is None:
                # TODO: We can create a test storage policy with smart defaults
                raise Exception("No Storage policies seems to be available to run the test")

            # Expected output : {'Policyname' : 'PolicyID'}
            self.storage_policy = list(storage_policies.keys())[0]
        else:
            self.storage_policy = storage_policy

        self.log.debug("executing qlogin command %s" % _qlogin_command)
        output = self.nfs_serv_machine_obj.execute_command(_qlogin_command)
        if "User logged in successfully" not in output.output.strip():
            raise Exception(
                "Error executing qlogin command. output:{0} error:{1}".format(output.output,
                                                                              output.exception))
        self.log.debug(output.output)

        self.commcell = commcell
        self.log_file_name_3dnfs = "3dnfs.log"

    def create_nfs_objectstore(self, obj_store_name, storage_policy, index_server,
                               media_agent, allowed_nfs_clients="0.0.0.0",
                               versions_enabled=True, squashing_type="root_squash",
                               anon_uid=-2, anon_gid=-2, copy_precedence=0, acl_flag=False,
                               min_days_retain_deleted=None, min_versions_retain=None,
                               min_days_retain_old_versions=None, delete_if_exists=False,
                               retry_interval=30, max_attempts=5):
        """ Creates NFS object store

        Args:
            obj_store_name       (str) -- name of the objectstore to be created

            storage_policy       (str) -- storage policy name

            index_server         (str) -- Index server hostname or IP address

            media_agent          (str) -- hostname or IP address of MA where NFS server
                                          is configured

            allowed_nfs_clients  (str) -- list of comma separated IP address/hostnames to be
                                          allowed to access the share. default is all clients

            versions_enabled     (bool)-- flag to enable File versioning. default is True

            squashing_type       (str) -- squashing type. default is "root_squash"

            anon_uid             (int) -- anonymous UID to be used for squashing

            anon_gid             (int) -- anonymous GID to be used for squashing

            copy_precedence      (int) -- copy precedence. default is zero

            acl_flag             (bool)-- flag to enable ACL feature. default is False

            min_days_retain_deleted (int)  -- Minimum Days to retain Deleted Items

            min_versions_retain  (int) --  Minimum versions to retain

            min_days_retain_old_versions (int) -- Minimum days to retain the older versions

            delete_if_exists    (bool) -- checks if objectstore exists and deletes it before
                                          creation.
            retry_interval      (int) -- time interval in seconds to re attempt creating share

            max_attempts        (int) -- maximum attempts to retry creating share in case of failure
        Returns :
            on success, mount path of the objectstore created

        Raises:
            Exception:
                if any error occurred while creating objectstore

        Sample cmd : ConfigureObjectStore -o create -n <Object Store Name> -s <Storage Policy>
                    -i <Index Server Client Name> -m <Media Agent Client Name>
                    -c <Allowed clients> [-V Versions enabled flag] [-S Squashing Type]
                    [-u anonuid] [-g anongid] [-C Copy Precedence] [-A ACL enable flag <1|0>] [-h]

        Skip enter password : "-y" option is used to disable need of entering password during
             objectstore creation
        """

        mountpath = None

        if delete_if_exists:
            # check if previous run couldn't delete objectstore
            if obj_store_name in self.list_all_nfs_objectstore():
                self.log.info("Previous run didn't cleanup objectstore")
                self.delete_nfs_objectstore(obj_store_name, delete_user=True)

        # generate create command
        cmd = "{0} -o create".format(self.config_cmd_with_prefix)

        # Append all mandatory parameters first.
        cmd = "{0} -n {1} -s {2} -i {3} -m {4} -c {5} -V {6} -S {7} -u {8} " \
              "-g {9} -C {10} -A {11} -y -f".format(cmd,
                                                    obj_store_name,
                                                    storage_policy,
                                                    index_server,
                                                    media_agent,
                                                    allowed_nfs_clients,
                                                    int(versions_enabled),
                                                    squashing_type,
                                                    anon_uid,
                                                    anon_gid,
                                                    copy_precedence,
                                                    int(acl_flag))

        if min_days_retain_deleted is not None:
            cmd += " -D " + str(min_days_retain_deleted)
        if min_versions_retain is not None:
            cmd += " -V " + str(min_versions_retain)
        if min_days_retain_old_versions is not None:
            cmd += " -d " + str(min_days_retain_old_versions)

        for attempt in range(1, max_attempts+1):
            self.log.info("Executing command : {0}".format(cmd))
            exit_code, output, error = self.nfs_serv_client_obj.execute_command(cmd)
            if exit_code:
                self.log.error("Error creating NFS Objectstore. output:{0} error:{1}".format(
                    output, error))
                self.log.info("share creation will be retried after {1} seconds." 
                              "next attempt count:{0}".format((attempt+1), retry_interval))
                time.sleep(retry_interval)
                continue

            search_obj = re.search(r'^mount path = (.*)', output,
                                   flags=re.RegexFlag.M | re.RegexFlag.I)
            if search_obj:
                mountpath = search_obj.group(1)
                self.log.info(
                    "Successfully Created Objecstore:{0}, share path:{1}".format(obj_store_name,
                                                                                 mountpath))
                break
            else:
                self.log.error("Could not find mount path in "
                                "create_nfs_objectstore. output : {0}".format(output))
                self.log.info("share creation will be retried after {1} seconds." 
                              "next attempt count:{0}".format((attempt+1), retry_interval))
                time.sleep(retry_interval)
                continue

        if exit_code:
            raise Exception(
                "Error creating NFS Objectstore. output:{0} error:{1}".format(output, error))

        if not search_obj:
            raise Exception("Could not find mount path in "
                           "create_nfs_objectstore. output : {0}".format(output))

        return mountpath

    def list_all_nfs_objectstore(self):
        """ List all available objectsotre names

            Args: None

            Returns :
                list of available objectstore names. In case of no objectstore returns
                empty list

            Raises:
                Exception:
                    if any error occurred while listing objectstore

            Sample command :
                ConfigureObjectStore  -o list

            Sample Output:
                List of Object Store
                Object Store Name             Client Name             NFS Server
                1)    iozone_user             iozone_user             centostemp
                2)    FS_oper                 FS_oper                 centostemp

        """

        objstore_list = []
        cmd = "{0} -o list".format(self.config_cmd_with_prefix)

        self.log.info("Executing command : {0}".format(cmd))
        exit_code, output, error = self.nfs_serv_client_obj.execute_command(cmd)
        if exit_code:
            raise Exception(
                "Error listing NFS Objectstore. output:{0} error:{1}".format(output, error))

        lines = output.strip().split('\n')
        if len(lines) < 3:
            # its not good to raise exception as this fn can be used to check for zero
            # object stores
            self.log.info("Couldn't find any objectstore currently configured")
            return objstore_list  # return empty list

        # convert the output to list of objectstore names. refer the above sample output
        for i in range(2, len(lines)):
            objstore_list.append(lines[i].split()[1])
        self.log.debug("list of objectstore found: {0}".format(str(objstore_list)))
        return objstore_list

    def show_nfs_objectstore(self, obj_store_name):
        """ shows properties set for the given objectstore name

            Args:
                obj_store_name (str) -- name of the object store

            Returns :
                dictionary containing properties set for the given Object Store

            Raises:
                Exception:
                    if any error occurred while getting objectstore details

            Sample command :
                ConfigureObjectStore -o show -n <Object Store Name>

            Sample output :
                ConfigureObjectStore -o show -n sample_NFS_share
                ObjectStore Server                      :       centostemp
                Index Server                            :       Index_server
                Allowed clients                         :       #####
                Access Permission                       :       RW
                Versions Enabled                        :       YES
                Copy Precedence                         :       0
                ACL     Enabled                         :       NO
                Squash Type                             :       ROOT_SQUASH
                Anonymous UID                           :       -2
                Anonymous GID                           :       -2
                Share path to mount                     :       1.1.1.1:/sample_NFS_share

        """

        objstr_details = {}

        cmd = "{0} -o show -n {1}".format(self.config_cmd_with_prefix,
                                                              obj_store_name)
        self.log.info("Executing command : {0}".format(cmd))
        exit_code, output, error = self.nfs_serv_client_obj.execute_command(cmd)
        if exit_code:
            raise Exception(
                "Error while running command show objectstore.output:{0}"
                "error:{1}".format(output, error))

        if 'Invalid Object Store' in output:
            raise Exception("Invalid object store name: {0}".format(obj_store_name))

        for item in output.strip().split('\n'):
            key_value = item.split(":")
            # need to handle "Share path to mount" which has two ":" colons
            if 'Retention' in key_value[0]:
                key_value[0] += key_value[1]
                key_value[1] = ''
            value = ':'.join([x.strip() for x in key_value[1:]])  # joining remaining fields
            objstr_details[key_value[0].strip()] = value

        self.log.debug("objectstore:{0} properties:{1}".format(obj_store_name, objstr_details))
        return objstr_details

    def delete_nfs_objectstore(self, obj_store_name, delete_user=False):
        """ delete the given objectstore name

            Args:
                obj_store_name (str)  -- name of the object store

                delete_user    (bool) -- delete objectstore user

            Returns :
                True --> in case of successful delete

            Raises:
                Exception:
                    if any error occurred while deleting objectstore

            sample command :
                ConfigureObjectStore -o delete -n <Object Store Name> [-U]

            sample output:
                Object Store [share1] deleted successfully
        """

        cmd = "{0} -o delete -n " \
              "{1} -y".format(self.config_cmd_with_prefix,
                           obj_store_name)
        if delete_user:
            cmd = "{0} -U".format(cmd)

        self.log.info("Executing command : {0}".format(cmd))
        exit_code, output, error = self.nfs_serv_client_obj.execute_command(cmd)
        if exit_code:
            raise Exception("Error while running command delete objectstore."
                            "output:{0} error:{1}".format(output, error))

        if 'Invalid Object Store' in output:
            raise Exception("Invalid object store name: {0}".format(obj_store_name))

        self.log.info("objstore {0} deleted successfully".format(obj_store_name))
        return True

    def update_nfs_objectstore(self, obj_store_name, allowed_nfs_clients=None, access=None,
                               version_enabled=None, squash_type=None, anon_uid=None,
                               anon_gid=None, copy_precedence=None, acl_flag=None,
                               version_interval=None):

        """ update the property for the given objectstore name

            Args:
            allowed_nfs_clients  (str) -- semicolon separated list of IP address/hostnames to be
                                          allowed to access the share.

            versions_enabled     (bool)-- flag to enable File versioning. (True/False)

            squashing_type       (str) -- squashing type.

            anon_uid             (int) -- anonymous UID to be used for squashing

            anon_gid             (int) -- anonymous GID to be used for squashing

            copy_precedence      (int) -- copy precedence.

            acl_flag             (bool)-- flag to enable ACL feature. (True/False)

            version_interval     (int) -- minimum interval between 2 versions on the share

            Returns :
                None --> in case of successful update

            Raises:
                Exception:
                    if any error occurred while updating objectstore

            sample command :
                ConfigureObjectStore -o update -n <Object Store Name> [-c Allowed clients]
                [-a Access Permission (RW/RO)] [-V Versions enabled flag] [-S Squashing Type]
                [-u anonuid] [-g anongid] [-C Copy Precedence] [-A ACL enable flag <1|0>] [-h]

            Sample cmd Output:
            Update succeeded for Object Store  [Object Store Name]
            """

        # Append all mandatory parameters first.
        cmd = "{0} -o update -n {1} -f".format(self.config_cmd_with_prefix,
                                                                obj_store_name)

        # Optional : UIDs + GIDs + Access Permission + Cache retention in days +
        # archive file recut in days + dataagingdays
        if allowed_nfs_clients:
            cmd = "{0} -c {1}".format(cmd, allowed_nfs_clients)
        if access:
            cmd = "{0} -a {1}".format(cmd, access)
        if version_enabled is not None:
            cmd = "{0} -V {1}".format(cmd, int(version_enabled))
        if squash_type:
            cmd = "{0} -S {1}".format(cmd, squash_type)
        if anon_uid is not None:
            cmd = "{0} -u {1}".format(cmd, anon_uid)
        if anon_gid is not None:
            cmd = "{0} -g {1}".format(cmd, anon_gid)
        if copy_precedence is not None:
            cmd = "{0} -C {1}".format(cmd, copy_precedence)
        if acl_flag is not None:
            cmd = "{0} -A {1}".format(cmd, int(acl_flag))
        if version_interval is not None:
            cmd = "{0} -t {1}".format(cmd, int(version_interval))

        self.log.info("Executing command : {0}".format(cmd))
        exit_code, output, error = self.nfs_serv_client_obj.execute_command(cmd)
        if exit_code:
            raise Exception("Error while running command update objectstore."
                            "output:{0} error:{1}".format(output, error))

        if 'Invalid Object Store' in output:
            raise Exception("Invalid object store name: {0}".format(obj_store_name))

        self.log.info("objstore {0} updated successfully".format(obj_store_name))

    def create_objectstore_snap(self, obj_store_name, timestamp=None,
                                allowed_nfs_clients="0.0.0.0", snap_name=None, copy_precedence=0,
                                ma_client=None):
        """ creates snapshot for the given objectstore for given time stamp

            Args:
                obj_store_name      (str)  -- name of the objectstore

                timestamp           (str) -- timestamp in "MM-DD-YYYY HH:MM:SS" format

                allowed_nfs_clients (str) -- list of comma separated client IP
                                             addresses or hostname to get access for snap

                snap_name           (str) -- snap name to be used while creating

                copy_precedence     (int) -- copy precedence

                ma_client           (str) -- NFS server client name

            Returns :
                on success, returns the mount path of PIT view created

            Raises:
                Exception:
                    if any error occurred while creating PIT view

            Sample command :
                ConfigureObjectStore -o create_snap -n <Object Store Name>
                -T "MM-DD-YYYY HH:MM:SS" [-c Allowed clients] [-N Snap Name]
                [-C Copy Precedence]  [-m MediaAgent Client Name]

            Sample output:
                Create Snap for Object Store [share1] succeeded
                mount path = /share1-snap1
                CIFS Share Name (If Enabled) = /share1-snap1

        """

        snap_mountpath = None

        if not ma_client:
            ma_client = self.nfs_server_hostname
        
        # Append all mandatory parameters first.
        cmd = "{0} -o create_snap".format(self.config_cmd_with_prefix)

        # if TimeStamp is defined get the current time stamp
        if not timestamp:
            self.log.info("timestamp not passed, using current timestamp")
            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime(
                '%m-%d-%Y %H:%M:%S')

        cmd = "{0} -n {1} -T \"{2}\" -c {3} -C {4} -m {5}".format(cmd,
                                                                  obj_store_name,
                                                                  timestamp,
                                                                  allowed_nfs_clients,
                                                                  copy_precedence,
                                                                  ma_client)
        if snap_name:
            cmd = "{0} -N {1}".format(cmd, snap_name)

        self.log.info("Executing command : {0}".format(cmd))
        exit_code, output, error = self.nfs_serv_client_obj.execute_command(cmd)
        if exit_code:
            raise Exception("Error while running command create objectstoresnap."
                            "output:{0} error:{1}".format(output, error))

        search_obj = re.search(r'^mount path = (.*)', output, flags=re.M | re.I)
        if search_obj:
            snap_mountpath = search_obj.group(1)
        else:
            raise Exception("Could not find mount path in create_objectstore_snap"
                            "output: {0}".format(output))

        self.log.info("Sleeping for 30 seconds after Snap Creation")
        time.sleep(30)

        self.log.info("Created objectstore snap {0}".format(snap_mountpath))
        return snap_mountpath

    def show_objectstore_snap(self, obj_store_name):
        """ shows properties of all PIT views for the given objectstore

            Args:
                obj_store_name        (str)  -- name of the objectstore

            Returns:
                On Success, properties of all PIT views for the given objectstore

            Raises:
                Exception:
                    if any error occurred while creating PIT view

            sample command:
                ConfigureObjectStore -o show_snap -n <Object Store Name> [-h]

            sample output:
                        Object Store            :       share1
                        Snap Time               :       06-18-2018 15:10:15
                        Mount Path              :       /share1-snap1
                        NFS Clients             :       0.0.0.0
                        Snap Name               :       snap1
                        CopyPrecedence          :       0
                        ObjectStore Server      :       NFSserver

                        Object Store            :       share1
                        Snap Time               :       06-18-2018 15:10:17
                        Mount Path              :       /share1-snap2
                        NFS Clients             :       1.1.1.1,1.1.1.1
                        Snap Name               :       snap2
                        CopyPrecedence          :       0
                        ObjectStore Server      :       NFSserver

        """

        pit_details = {}

        cmd = "{0} -o show_snap -n {1}".format(self.config_cmd_with_prefix,
                                                                   obj_store_name)

        self.log.info("Executing command : {0}".format(cmd))
        exit_code, output, error = self.nfs_serv_client_obj.execute_command(cmd)
        if exit_code:
            raise Exception("Error while running command show objectstoresnap."
                            "output:{0} error:{1}".format(output, error))

        # TODO: It can be enhanced to return dictionary of dictionaries where each key represents
        #       snap name and value representing dictionary of snap details
        for item in output.strip().split('\n'):
            key_value = item.split(":")
            # need to handle "Snap Time" which has more than one ":" colons
            value = ':'.join([x.strip() for x in key_value[1:]])  # joining remaining fields
            pit_details[key_value[0].strip()] = value

        # return the return code and output as is
        self.log.debug(
            "objectstoresnap:{0}, properties:{1}".format(obj_store_name, pit_details))
        return pit_details

    def update_objectstore_snap(self, obj_store_name, mount_path=None, allowed_clients=None,
                                copy_precedence=None, ma_client=None, access_permission=None):
        """ update the properties for the given objectstore snap name

            Args:
                obj_store_name      (str) -- name of the objectstore

                mount_path          (str) -- PIT view mount path

                allowed_clients     (str) -- list of comma separated client IP
                                              addresses or hostname to get access for snap

                copy_precedence     (int) -- copy precedence

                ma_client           (str) -- NFS server client name

                access_permission   (str) -- Read-Only or Read-Write mode

            Returns:
                On Success, updates properties for given PIT view

            Raises:
                Exception:
                    if any error occurred while updating PIT view


            sample command:
                ConfigureObjectStore -o update_snap -n <Object Store Name> -p <Mount Path>
                < -c Allowed Clients | -C Copy Precedence | -m MediaAgent Client Name >

            sample output:
                Snap [/share1-snap1] updated successfully
        """

        cmd = "{0} -o update_snap".format(self.config_cmd_with_prefix)

        # Append all mandatory parameters first.
        cmd = "{0} -n {1} -p {2}".format(cmd, obj_store_name, mount_path)

        # Optional arguments
        if allowed_clients:
            cmd = "{0} -c {1}".format(cmd, allowed_clients)
        if copy_precedence is not None:
            cmd = "{0} -C {1}".format(cmd, copy_precedence)
        if ma_client:
            cmd = "{0} -m {1}".format(cmd, ma_client)
        if access_permission:
            cmd = "{0} -a {1}".format(cmd, access_permission)

        self.log.info("Executing command : {0}".format(cmd))
        exit_code, output, error = self.nfs_serv_client_obj.execute_command(cmd)
        if exit_code:
            raise Exception("Error while running command update objectstoresnap.\
                              output:{0} error:{1}".format(output, error))
        return True

    def delete_objectstore_snap(self, obj_store_name, mount_path=None,
                                delete_all_snaps=False):
        """ delete the given objectstore snap
            Args:
                obj_store_name  (str) -- name of the object store

                mount_path      (str) -- mount path of PIT view

                delete_all_snaps(bool)-- delete all snaps for given objectstore

            Returns:
                On Success, deletes appropriate PIT views for the given objectstore

            Raises:
                Exception:
                    if any error occurred while deleting PIT view

            sample command :
                ConfigureObjectStore -o delete_snap -n <Object Store Name> [ -A |-p Mount Path ]

            sample output:
                Object Store Snap deleted successfully
        """

        if not mount_path and not delete_all_snaps:
            raise Exception("should set at least one option. mount path or delete all snaps")

        cmd = "{0}echo \"erase and reuse media\" | {1}{2}ConfigureObjectStore -o " \
            "delete_snap -n {3}".format(self.cmd_prefix,
                                        self.cvlt_basedir,
                                        self.nfs_serv_machine_obj.os_sep,
                                        obj_store_name)

        if delete_all_snaps:
            cmd = "{0} -A".format(cmd)
        else:
            cmd = "{0} -p {1}".format(cmd, mount_path)

        self.log.info("Executing command : {0}".format(cmd))
        exit_code, output, error = self.nfs_serv_client_obj.execute_command(cmd)
        if exit_code:
            raise Exception("Error while running command delete objectstoresnap.\
                              output:%s error:%s".format(output, error))

    def update_job_idle_timeout(self, timeout=60):
        """ set 3dfs backup Job idle timeout
            Args:
                timeout (int)  -- 3dfs backup idle time out

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in update
        """
        self.nfs_serv_machine_obj.create_registry('3Dfs', 'nJobTimeout', timeout)

    def get_objectstore_subclient_id(self, obj_store_name):
        """ gets subclient ID for given objectstore name
            Args:
                obj_store_name (str)  -- name of objectstore

            Returns:
                subclient ID of objectstore

            Raises:
                Exception:
                    if any error occurs in getting subclient ID
        """
        self.commcell.refresh()
        _client = self.commcell.clients.get(obj_store_name)
        _agent = _client.agents.get('file system')
        _instance = _agent.instances.get('defaultinstancename')
        _backupset = _instance.backupsets.get(obj_store_name)
        _subclient_id = _backupset.subclients[obj_store_name.lower()]['id']

        return _subclient_id

    def parse_3dnfs_logs(self, match_pattern, time_stamp, max_attempt=5):
        """ parse 3dnfs logs for given pattern raised after given
            time stamp
            Args:
                match_pattern (str)  -- grep match pattern

                time_stamp   (datetime)  -- timestamp used to match the expected
                string in logs. Expected pattern: mm/yy HH:MM:SS

                max_attempt  (int)  -- maximum attempts used to match string
                in logs

            Returns:
                True -- if pattern match later to given time stamp
                False -- if pattern is not matched later to given time stamp

            Raises:
                Exception:
                    None
        """
        log_path = self.nfs_serv_machine_obj.client_object.log_directory

        if self.nfs_serv_machine_obj.os_info.lower() == 'Windows':
            raise Exception("Windows platform is currently not supported")

        all_log_files = self.nfs_serv_machine_obj.get_files_in_path(log_path)
        log_files = [x for x in all_log_files
                     if os.path.splitext(self.log_file_name_3dnfs)[0] in x]

        self.log.debug("list of 3dnfs log files %s", log_files)
        attempt = 1
        while True:
            self.log.debug("attempting to find required pattern "
                           "in 3dnfs debug logs. Attempt:%s", attempt)
            for log_file in log_files:
                command = '/usr/bin/bzgrep -e "{0}" {1}'.format(match_pattern,
                                                                log_file)
                ret_val, response, error = \
                    self.nfs_serv_machine_obj.client_object.execute_command(command)
                if ret_val == 0:
                    matched_lines = response.splitlines()
                    self.log.debug("all matched line without timeline %s", matched_lines)
                else:
                    continue

                for line in matched_lines:
                    log_time_stamp = ' '.join(line.split('###')[0].strip().split()[-2:])
                    if log_time_stamp >= time_stamp:
                        self.log.debug("log file time stamp:%s, given timestamp:%s",
                                       log_time_stamp, time_stamp)
                        self.log.info("pruner run successfully")
                        self.log.info("matched line in debug log %s", line)
                        return True

            attempt += 1
            if attempt > max_attempt:
                break
            time.sleep(60)

        self.log.error("expected string %s was not found with given"
                       "timestamp %s" % (match_pattern, time_stamp))
        return False



