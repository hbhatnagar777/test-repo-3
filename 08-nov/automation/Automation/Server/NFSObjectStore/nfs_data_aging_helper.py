# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for performing NFS server related operations in Commcell

NfsDataAgingHelper is the only class defined in this.

NfsDataAgingHelper: Provides methods which are relevant to NFS data aging tests

NfsDataAgingHelper:
    __init__()                       --  initialize instance of the
    NfsDataAgingHelper class

    create_synthetic_full_schedule() -- create synthetic full job for given client to
    run immediately

    run_synthetic_full()             -- create synthetic full job for given client
    to run immediately and wait for job to complete

    create_files_wait_for_job_complete() -- create files on given objectstore and wait
    for 3dfs backup job to complete

    delete_files_in_objectstore()    -- deletes half of the files from the given
    list randomly

    add_consider_retention_days_as_mins() -- Adds consider retention days reg
    key on index server

    remove_consider_retention_days_as_mins() -- removes consider retention days
    reg key on index server

    update_archfile_space_reclamation() -- updates commserve db to delete
    pruned afiles immediately

    validate_afiles_cleared()       -- validates afiles are cleared after data aging

    validate_nfs_pruner_thread()    -- validates NFS pruner thread runs and update
    index for delted items


"""
import datetime
import time
import random

from cvpysdk.policies.schedule_policies import SchedulePolicies

from AutomationUtils import logger
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Server.JobManager.jobmanager_helper import JobManager
from Server.NFSObjectStore.NFSObjectStoreConstants import NFS_PRUNER_MM_KEY
from Server.NFSObjectStore.NFSObjectStoreConstants import DATA_CUBE_SERVICE_NAME


class NfsDataAgingHelper:
    """Base class to execute NFS data aging related operations """

    def __init__(self, commcell, index_server_client_name):
        """Initialize instance of the NfsDataAgingHelper class..
            Args:
                commcell (obj)    -- instance of commcell

                index_server_client_name (str)  --  client name of index server

            Returns:
                object - instance of the ObjectstoreClientUtils class

            Raises:
                Exception:
                    if any error occurs in Initialize

        """
        self.log = logger.get_log()
        self.commcell = commcell
        self.schedule_policy = SchedulePolicies(self.commcell)
        self.index_server_machine_obj = Machine(index_server_client_name, self.commcell)
        self.index_server_client_obj = commcell.clients.get(index_server_client_name)
        self.job_manager = None
        self.retention_reg_changed = False
        self.utils = OptionsSelector(self.commcell)
        self.data_cube_serive_name = "{0}({1})".format(DATA_CUBE_SERVICE_NAME,
                                                       commcell.commserv_client.instance)

    def create_synthetic_full_schedule(self, client_name, policy_name):
        """create synthetic full job for given client to run immediately
            Args:
                client_name (str)    -- client name to be associated with schedule

                policy_name (str)    --  policy name to be used for schedule

            Returns:
                Instance of Schedule_Policy

            Raises:
                Exception:
                    if any error occurs in creating schedule policy

        """
        associations = [{'clientName': client_name}]
        schedule = [
            {
                'pattern': {
                    'freq_type': 'one_time',
                    "active_start_date": datetime.datetime.fromtimestamp(time.time()).strftime('%m/%d/%Y'),
                    "active_start_time": datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M')
                },
                'options': {
                    'backupLevel': 'Synthetic_full'
                }
            }
        ]
        agent_type = [
            {"appGroupName": "Protected Files"},
            {"appGroupName": "Archived Files"}
        ]
        self.log.info("creating schedule policy %s to run immediately", policy_name)
        schedule_policy_obj = self.schedule_policy.add(policy_name,
                                                       "Data Protection",
                                                       associations,
                                                       schedule,
                                                       agent_type)
        return schedule_policy_obj

    def run_synthetic_full(self, client_name, policy_name="synth_full_objectstore"):
        """create synthetic full job for given client to run immediately and wait for
           job to complete
            Args:
                client_name (str)    -- client name to be associated with schedule

                policy_name (str)    --  policy name to be used for schedule

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in running synthfull job

        """
        schedule_policy_obj = self.create_synthetic_full_schedule(client_name, policy_name)

        # check for backup Job complete
        self.log.info("checking Synth Full Job for objectstore client")
        jobs = self.commcell.job_controller.active_jobs(client_name=client_name,
                                                        options={'job_type': 'Synthetic Full'})
        max_try = 30
        job_triggered = False
        attempt = 0
        while attempt < max_try and not job_triggered:
            if bool(jobs):
                job_triggered = True
                continue
            else:
                self.log.info("SynthFull Job is not yet running for objectstore client")
                time.sleep(10)
                attempt += 1

            jobs = self.commcell.job_controller.active_jobs(client_name=client_name,
                                                            options={'job_type': '3DFS Backup'})

        if not job_triggered:
            self.log.exception("SynthFull job is not triggered for objectstore")
            return

        job = [key for key in jobs.keys()][0]
        self.job_manager = JobManager(_job=job, commcell=self.commcell)
        self.log.info("waiting for job %s for client %s to complete" % (job, client_name))
        self.job_manager.wait_for_state(expected_state='completed')
        self.log.info("SynthFull Job %s is completed", job)

        # delete schedule after run
        self.log.info("deleting schedule policy id: %s", schedule_policy_obj.schedule_policy_id)
        self.schedule_policy.delete(schedule_policy_obj.schedule_policy_name)

    def create_files_wait_for_job_complete(self,
                                           files_create,
                                           machine_obj,
                                           test_path,
                                           objectstore_client_name):
        """create files on given objectstore and wait for 3dfs backup job to complete
            Args:
                files_create (list)  -- List of file names to create files

                machine_obj (obj)    --  machine object of client where objectstore
                                         is mounted

                test_path   (str)    --  test path where files need to be created
                                         (also where objectstore is mounted)

                objectstore_client_name (str) -- name of objectstore client

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in creating file

        """
        self.log.info("creating test files %s on path %s" % (files_create, test_path))

        if not machine_obj.check_directory_exists(test_path):
            self.log.info("creating test path %s", test_path)
            machine_obj.create_directory(test_path)

        for name in files_create:
            file_path = machine_obj.join_path(test_path, name)
            machine_obj.create_file(file_path, '', file_size=1024*1024)

        self.log.info("test files created successfully")

        # check for backup Job complete
        self.log.info("checking backup Jobs for objectstore client")
        jobs = self.commcell.job_controller.active_jobs(client_name=objectstore_client_name,
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

            jobs = self.commcell.job_controller.active_jobs(client_name=objectstore_client_name,
                                                            options={'job_type': '3DFS Backup'})
            self.log.debug("active jobs %s", jobs)

        if not job_triggered:
            self.log.error("backup job is not triggered for objectstore")
            return

        job = [key for key in jobs.keys()][0]
        self.job_manager = JobManager(_job=job, commcell=self.commcell)
        self.log.info("waiting for job %s for client %s to complete" % (
            job, objectstore_client_name))
        self.job_manager.wait_for_state(expected_state='completed')
        self.log.info("backup Job %s is completed", job)

    def delete_files_in_objectstore(self, machine_obj, test_path, files_list):
        """deletes half of the files from the given list randomly
            Args:
                machine_obj (obj)    --  machine object of client where objectstore
                                         is mounted

                test_path   (str)    --  test path where files need to be created
                                         (also where objectstore is mounted)

                files_list (list)    --    List of file names to present in test path

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in deleting files
        """
        deleted_files = []
        index_of_files_to_be_deleted = random.sample(range(len(files_list)), int(len(files_list)/2))
        self.log.debug("Index of files to be deleted %s" % index_of_files_to_be_deleted)
        for index in index_of_files_to_be_deleted:
            file_path = machine_obj.join_path(test_path, files_list[index])
            machine_obj.delete_file(file_path)
            deleted_files.append(files_list[index])

        return deleted_files

    def add_consider_retention_days_as_mins(self):
        """Adds consider retention days reg key on index server
             Args:

             Returns:
                 None

             Raises:
                 Exception:
                     if any error occurs in adding reg key
         """
        # check if reg is already exist
        if not self.index_server_machine_obj.check_registry_exists(
                                        'DM2WebSearchServer',
                                        'ConsiderRetentionDaysAsMinutes'):
            self.index_server_machine_obj.create_registry(
                                                      'DM2WebSearchServer',
                                                      'ConsiderRetentionDaysAsMinutes',
                                                      'true')
            self.retention_reg_changed = True
            self.restart_cv_service_wait(self.data_cube_serive_name)
        else:
            self.log.info("ConsiderRetentionDaysAsMinutes registry already "
                          "set on index server.Skipping create")

    def remove_consider_retention_days_as_mins(self):
        """removes consider retention days reg key on index server
             Args:

             Returns:
                 None

             Raises:
                 Exception:
                     if any error occurs in deleting reg key
         """
        if self.retention_reg_changed:
            self.index_server_machine_obj.remove_registry(
                                            'DM2WebSearchServer',
                                            'ConsiderRetentionDaysAsMinutes')
            self.restart_cv_service_wait(self.data_cube_serive_name)
        else:
            self.log.info("retention registry is not added in test.skipping remove")

    def update_archfile_space_reclamation(self):
        """ updates commserve db to delete pruned afiles immediately
             Args:

             Returns:
                 None

             Raises:
                 Exception:
                     if any error occurs in updating CS DB
         """
        query = ("UPDATE ArchFileSpaceReclamation SET CreationTime = "
                 "CreationTime - (90 * 24 * 60 * 60)")
        self.utils.update_commserve_db(query)

    def validate_afiles_cleared(self, tc_obj):
        """validates afiles are cleared after data aging
            Args:
                tc_obj (obj)    --  testcase object which contain csdb instance

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in deleting files
        """
        # check archfile is cleared ArchFileSpaceReclamation table
        query = "select * from ArchFileSpaceReclamation"
        tc_obj.csdb.execute(query)
        results = tc_obj.csdb.fetch_all_rows()
        self.log.info("ArchFileSpaceReclamation results %s", results)
        if bool(results):
            self.log.info("no afiles found in ArchFileSpaceReclamation table")
        else:
            self.log.error("prunable afiles are not cleared in CS DB")

    def validate_nfs_pruner_thread(self,
                                   tc_obj,
                                   deleted_files,
                                   app_id,
                                   max_try=5):
        """ validates NFS pruner thread runs and update index for delted items
            Args:
                tc_obj (obj)    --  testcase object which contain csdb instance

                deleted_files (list) -- list of filenames deleted

                app_id (int)    -- application id of test objectstore

                max_try (int)   -- max attempt to check for is_visible is set to false

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in validation
        """
        self.log.info("validate nfs pruner thread")
        commcell_machine_obj = Machine(self.commcell.commserv_name, self.commcell)

        attempt = 0
        status = False
        while attempt < max_try and not status:
            if commcell_machine_obj.check_registry_exists("MediaManager",
                                                          NFS_PRUNER_MM_KEY):
                self.log.info("deleting MM registry in CS to run pruning Job")
                commcell_machine_obj.remove_registry("MediaManager",
                                                     NFS_PRUNER_MM_KEY)

            # wait for pruner thread to run
            time.sleep(60)

            self.log.info("check for is_visible flag set to false for deleted items")
            ret_val = tc_obj.nfs_solr_helper.check_is_visisble(deleted_files,
                                                               'latest',
                                                               app_id,
                                                               False)

            # if is_visible is set to false means pruner thread ran successfully
            # else give it one more try
            if ret_val:
                status = True
            else:
                attempt += 1

        if status:
            self.log.info("NFS pruner thread run successfully and "
                          "is_visible flag is set to false for deleted items")
        else:
            self.log.error("is_visisble flag is not set to false for deleted items")

    def get_files_checksum(self, machine_obj, test_path, file_names):
        """ gets md5sum for the given list of files
            Args:
                machine_obj (obj)    --  machine object for given test files

                test_path (list)     --  directory where test files are present

                file_names (int)    --  list of files in the directory to get the md5sum

            Returns:
                dictionary with filename as key and value as md5sum checksum of the file

            Raises:
                Exception:
                    if any error occurs in getting md5sum checksum
        """
        md5sum_dict = {}
        self.log.info("collecting md5 checksum for given files")
        for file_name in file_names:
            file_path = machine_obj.join_path(test_path, file_name)
            md5sum = machine_obj._get_file_hash(file_path)
            md5sum_dict[file_name] = md5sum
        self.log.debug("md5 checksum for given files %s", md5sum_dict)
        return md5sum_dict

    def compare_checksum(self, checksum_before_delete, checksum_after_delete):
        """ compares checksum for given files before and after delete
            Args:
                checksum_before_delete (dict)    --  dict with filename and checksum

                checksum_after_delete (dict)    --  dict with filename and checksum

            Returns:
                dictionary with filename as key and value as md5sum checksum of the file

            Raises:
                Exception:
                    when checksum of files doesn't match
        """
        status = True
        for file_name in checksum_after_delete.keys():
            if checksum_before_delete[file_name] != checksum_after_delete[file_name]:
                status = False
                self.log.error("checksum didn't match for file %s "
                               "checksum before delte:%s after delete:%s" %
                               (file_name,
                                checksum_before_delete[file_name],
                                checksum_after_delete[file_name]))
        if not status:
            raise Exception("checksum of non deleted files didn't match after data aging"
                            "checksum before:%s after:%s" %(checksum_before_delete,
                                                            checksum_after_delete))

        self.log.info("validation of checksum for non deleted items is successful")

    def restart_cv_service_wait(self, _cv_service_name):
        """ restarts specified cv service on the index server and wait for index client
            to be ready. In case of Linux index server,it will restart all services
            Args:
                _cv_service_name (str)    --  CV service name to be restarted

            Returns:
                None

            Raises:
                Exception:
                    if failed to restart CV service
        """
        self.log.info("restarting CV service %s " % _cv_service_name)
        self.index_server_client_obj.restart_service(_cv_service_name)
        max_attempt = 10
        attempt = 0
        while attempt < max_attempt:
            if self.index_server_client_obj.is_ready():
                break
            attempt += 1
            self.log.info("index server is not ready. waiting for 30 seconds.." 
                          "attempt:%s" % attempt)
            time.sleep(30)

        if not self.index_server_client_obj.is_ready():
            raise Exception("client %s is not ready" % self.index_server_client_obj.client_name)
        self.log.info("data cube service restarted successfully and client is ready")

    def start_cv_service_wait(self, _cv_service_name=None):
        """ starts specified cv service on the index server and wait for index client
            to be ready. In case of Linux index server,it will start all services
            Args:
                _cv_service_name (str)    --  CV service name to be restarted

            Returns:
                None

            Raises:
                Exception:
                    if failed to start CV service
        """
        if not _cv_service_name:
            _cv_service_name = self.data_cube_serive_name
        self.log.info("starting CV service %s " % _cv_service_name)
        self.index_server_client_obj.start_service(_cv_service_name)
        max_attempt = 10
        attempt = 0
        while attempt < max_attempt:
            if self.index_server_client_obj.is_ready():
                break
            attempt += 1
            self.log.info("index server is not ready. waiting for 30 seconds.." 
                          "attempt:%s" % attempt)
            time.sleep(30)

        if not self.index_server_client_obj.is_ready():
            raise Exception("client %s is not ready" % self.index_server_client_obj.client_name)
        self.log.info("data cube service started successfully and client is ready")

    def stop_cv_service_wait(self, _cv_service_name=None):
        """ starts specified cv service on the index server and wait for index client
            to be ready. In case of Linux index server,it will start all services
            Args:
                _cv_service_name (str)    --  CV service name to be restarted

            Returns:
                None
        """
        if not _cv_service_name:
            _cv_service_name = self.data_cube_serive_name
        self.log.info("stoping CV service %s " % _cv_service_name)
        self.index_server_client_obj.stop_service(_cv_service_name)
        