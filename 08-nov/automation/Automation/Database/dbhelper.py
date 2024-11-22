# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing database related operations.

DbHelper is the only class defined in this file.

DbHelper: Class for performing operations generic to all the database iDAs


DbHelper:
    __init__()                          --  initialise object of DbHelper object

    run_backup()                        --  initiates the backup job for the specified subclient

    prepare_aux_copy_restore()          --  method to create a secondary copy in the name
    'automation_copy' for the storage policy, if it is not already existing. Once the storage
    policy is created the aux copy is run for the created secondary copy

    run_backup_copy()                   --  method to run backup copy job for given storage policy
    and return the copy precedence associated with the primary snap copy once the job is completed

    get_snap_log_backup_job()           --  returns the log backup job object if provided
    the snap backup job id

    get_backup_copy_job()               --   waits for the backup copy job to get completed and
    returns the job object associated with inline backup copy job of snap backup

    check_if_restore_from_revert        -- checks if the hardware revert is performed on the restore

    check_if_restore_from_snap_copy     -- checks if the restore job is run from snap copy or not

    check_if_backup_copy_run_on_proxy   --  checks if the job is run on the proxy client or not

    check_chunk_commited()              --  checks if atleast one chunk is committed for the
    initiated job

    get_index_cache_path()              --  checks the MA logs and fetches Index cache
    location for the job specified

    get_volume_id()                     --  method to fetch the volume id associated
    with the snap backup

    synthfull_validation()              --  method to run synthfull backup job and
    validate the synthfull job

    delete_v2_index_restart_service()   --  method to delete index cahce and restart index

    _get_last_job_of_subclient()        --  get the last backup job run for the subclient

    _get_index_cache_ma()               --  gets the index cahce MA used by the job

    delete_v1_index_restart_service()   --  method to delete index cahce and restart index service

    delete_client_access_control()      --  method to delete client entries from App_ClientAccessControl

    get_ma_names()                      --  Gets the Media_agent names associated with the storage_policy

    get_proxy_names()                   --  Method to get the list of proxies associated with pseudoclient

    install_db_agent()                  --  method to install DB agent on a client machine

    check_permissions_after_install()   --  Method to verify group permissions in a client

    run_aux_copy_for_cloud_storage()    --  Method to run aux copy job for replicating content to secondary cloud storage

    wait_for_job_completion()           --  Waits for completion of the job

    compare_dictionaries()              --  Compares two dictionaries for validation

    wait_for_active_jobs()              --  Waits for the active jobs on the client

    clear_automation_credentials()     --   Clears all credentials with the given prefix

    unzip_downloaded_file()            --   Unzips the downloaded file on to the specified location
"""

import time
from cvpysdk.exception import SDKException
from cvpysdk.job import JobController
from cvpysdk.storage import MediaAgent
from cvpysdk.internetoptions import InternetOptions
from AutomationUtils import logger
from AutomationUtils import database_helper
from AutomationUtils import machine
from AutomationUtils import idautils
from AutomationUtils import config
from Indexing.database import index_db
from Install.install_helper import InstallHelper
import xml.etree.ElementTree as ElementTree
from Web.Common.exceptions import CVException
from deepdiff import DeepDiff
from cvpysdk.credential_manager import Credentials
from datetime import datetime, timedelta
import os
import zipfile
from glob import glob


class DbHelper(object):
    """Class for performing operations generic to all the database iDAs"""

    def __init__(self, commcell):
        """Initialize the DbHelper object.

            Args:
                commcell             (obj)  --  Commcell object

            Returns:
                object - instance of DbHelper class

        """
        self._commcell = commcell
        self._csdb = database_helper.get_csdb()
        self.log = logger.get_log()
        self.credential_manager = Credentials(self._commcell)
        self.zip_file = None

    def run_backup(
            self,
            subclient,
            backup_type,
            inc_with_data=False):
        """Initiates the backup job for the specified subclient

            Args:
                subclient      (obj)   -- Subclient object

                backup_type    (str)   -- Backup type to perform on subclient
                                            Either FULL or INCREMENTAL

                inc_with_data  (bool)  --  flag to determine if the incremental backup
                includes data or not

            Returns:
                job            (obj)   -- Returns Job object

            Raises:
                Exception:
                    if unable to run backup job

        """
        self.log.info("#####Starting Subclient %s Backup#####", backup_type)
        if inc_with_data:
            job = subclient.backup(backup_type, inc_with_data=inc_with_data)
        else:
            job = subclient.backup(backup_type)
        self.log.info(
            "Started %s backup with Job ID: %s", backup_type, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )

        self.log.info("Successfully finished %s backup job", backup_type)
        return job

    def prepare_aux_copy_restore(self, storage_policy):
        """ Method to create a secondary copy in the name 'automation_copy'
        for the storage policy, if it is not already existing.
        Once the storage policy is created the aux copy is run for the created
        secondary copy.

            Args:
                storage_policy   (str)   -- Name of the storage policy

            Returns:
                copy_precendence (str)  -- Copy precedence associated with the
                new copy created

            Raises:
                SDKException:
                    if Aux copy Job fails to run

                    if failed to get copy details from policy

        """
        storage_policy_object = self._commcell.storage_policies.get(storage_policy)
        library_name = storage_policy_object.library_name
        disk_library_object = self._commcell.disk_libraries.get(library_name)
        media_agent_name = disk_library_object.media_agents_associated[0]
        if not media_agent_name or media_agent_name == '':
            raise Exception("Unable to get the Media agent name")
        if not storage_policy_object.has_copy("automation_copy"):
            storage_policy_object.create_secondary_copy(
                "automation_copy",
                library_name,
                media_agent_name)

        job = storage_policy_object.run_aux_copy(
            "automation_copy",
            media_agent_name)

        self.log.info(
            "Started aux copy job with Job ID: %s", str(job.job_id))

        if not job.wait_for_completion():
            raise SDKException(
                'Job',
                '102',
                'Failed to run aux copy job with error: {1}'.format(
                    job.delay_reason))

        policy_copies = storage_policy_object.copies
        if policy_copies.get('automation_copy'):
            if policy_copies['automation_copy'].get('copyPrecedence'):
                return policy_copies['automation_copy']['copyPrecedence']
        raise SDKException(
            'Storage',
            '102',
            'Failed to get copy precedence from policy')

    def run_backup_copy(self, storage_policy):
        """ Method to run backup copy job for given storage policy
        and return the copy precedence associated with the primary snap
        copy once the job is completed.

            Args:
                storage_policy          (str)   -- Name of the storage policy

            Returns:
                copy_precendence (str)  -- Copy precedence associated with the
                primary snap copy created

            Raises:
                SDKException:
                    if backup copy Job fails to run

                    if failed to get copy details from policy

        """
        storage_policy_object = self._commcell.storage_policies.get(storage_policy)
        try:
            job = storage_policy_object.run_backup_copy()

            self.log.info(
                "Started backup copy job with Job ID: %s", job.job_id)

            if not job.wait_for_completion():
                raise SDKException(
                    'Job',
                    '102',
                    'Failed to run backup copy job with error: {1}'.format(
                        job.delay_reason))
        except Exception as exp:
            ignore_errors = [
                "Job will not be started. Snap Backup Copy job does not need to Run",
                "There are no jobs that need to be backup copied",
                "Unable to process jobs as there are existing active workflow jobs processing same subclients"
            ]
            if not any(error_string in exp.exception_message for error_string in ignore_errors):
                raise Exception('Unable to run backup copy job')
        try:
            copy_precedence = storage_policy_object.get_copy_precedence("primary snap")
        except SDKException as e:
            self.log.info("Snapshot copy named primary copy doesn't exist. Trying snap copy . . .")
            copy_precedence = storage_policy_object.get_copy_precedence("snap copy")
        return copy_precedence

    def get_snap_log_backup_job(self, job_id):
        """ Returns the log backup job object if provided
        the snap backup job id

            Args:
                job_id          (str)  -- snap backup job id

            Returns:
                job             (obj)  -- Job object associated with log backup

        """
        query = (
            "select jobId from JMBkpStats where subTaskId=(select subTaskId "
            "from JMBkpStats where jobid={0}) and bkpLevel='2' and appId=(select "
            "appId from JMBkpStats where jobid={0}) and jobId!={0}").format(job_id)
        while True:
            self._csdb.execute(query)
            cur = self._csdb.fetch_one_row()
            if cur[0] != '':
                return self._commcell.job_controller.get(cur[0])
            self.log.info(
                "Log backup is not completed yet. Sleeping for 30 seconds, before trying again")
            time.sleep(30)

    def get_backup_copy_job(self, job_id):
        """waits for the backup copy job to get completed and returns the job
        object associated with inline backup copy job of snap backup

            Args:
                job_id          (str)  -- snap backup job id

            Returns:
                job             (obj)  -- Job object associated with backup copy job

            Raises:
                Exception:
                    if backup copy job fails to run

        """
        common_utils = idautils.CommonUtils(self._commcell)
        backup_copy_job_id = ''
        while backup_copy_job_id == '' or backup_copy_job_id == '0':
            backup_copy_job_id = common_utils.get_backup_copy_job_id(job_id)
        self.log.info("backup copy job is started with Job ID: %s", backup_copy_job_id)
        self.log.info("Waiting for backup copy job to finish")
        backup_copy_job = self._commcell.job_controller.get(backup_copy_job_id)
        if not backup_copy_job.wait_for_completion():
            raise Exception(
                "Failed to run backup copy job with error: {0}".format(
                    backup_copy_job.delay_reason
                )
            )
        return backup_copy_job

    def check_if_restore_from_revert(self, job_object, client_object=None, machine_object=None):
        """checks if the restore job is run from hardware revert

                    Args:
                        job_object      (obj)       --      Job object associated with restore job

                        client_object   (obj)       --      client object of client associated with the job

                            default: None

                        machine_object  (obj)       --      machine object of client associated with the job

                            default: None

                    Returns:
                        True - if the restore job is from hardware revert

                        False - if restore job is not from hardware revert

                """
        if client_object is None:
            client_object = self._commcell.clients.get(job_object.client_name)
        client_log_directory = client_object.log_directory
        if machine_object is None:
            machine_object = machine.Machine(client_object)
        client_log_directory = machine_object.join_path(client_log_directory, "CVMA.log")
        command = f"sed -n \"/{job_object.job_id}.*CVMASnapHandlerInternal::initialize()" \
                  f".*CVMASnapHandlerInternal::revertVolumeSnaps.*].$/p\" " \
                  f"{client_log_directory}"
        output = machine_object.execute_command(command).formatted_output
        if output != '':
            return True
        return False

    def check_if_restore_from_snap_copy(self, job_object, client_object=None, machine_object=None):
        """checks if the restore job is run from snap copy or not

            Args:
                job_object      (obj)       --      Job object associated with restore job

                client_object   (obj)       --      client object of client associated with the job

                    default: None

                machine_object  (obj)       --      machine object of client associated with the job

                    default: None

            Returns:
                True - if the restore job is from snap copy

                False - if restore job is not from snap copy

        """
        if client_object is None:
            client_object = self._commcell.clients.get(job_object.client_name)
        client_log_directory = client_object.log_directory
        if machine_object is None:
            machine_object = machine.Machine(client_object)
        client_log_directory = machine_object.join_path(client_log_directory, "CVMA.log")
        command = (
                      "sed -n \"/%s.*SERVICE.*Received.*CVMA_VOL_SNAP_OPERATION_REQ.*/s/://gp\" %s") % (
                      job_object.job_id, client_log_directory)
        if "windows" in machine_object.os_info.lower():
            command = (
                          "(Select-String -Path \"%s\" -Pattern"
                          " \"%s.*SERVICE.*Received.*CVMA_VOL_SNAP_OPERATION_REQ.*\")") % (
                          client_log_directory, job_object.job_id)
        output = machine_object.execute_command(command).formatted_output
        if output != '':
            return True
        return False

    def check_if_backup_copy_run_on_proxy(self, job_id, proxy_client_object):
        """ checks if the job is run on the proxy client or not

            Args:
                job_id                (str)       --      Job id of backup copy job

                proxy_client_object   (obj)       --      client object of procy client

                    default: None

            Returns:
                True - if the restore job is from snap copy

                False - if restore job is not from snap copy

        """
        self.log.info("Checking if backup copy run on proxy: %s", proxy_client_object.client_name)
        machine_object = machine.Machine(proxy_client_object)
        log_file = "clBackupParent.log"
        if "windows" in machine_object.os_info.lower():
            log_file = "clBackup.log"
        return machine_object.check_if_pattern_exists_in_log(job_id, log_file)

    def check_chunk_commited(self, job_id):
        """ Checks if atleast one chunk is committed
        for the initiated job

        Args:

            job_id               (str)  -- Job ID

        Returns:

            (bool)    --  Returns true on success/False on failure

        """
        query = (
            "select * FROM archChunkMapping where jobId = {0} and physicalSize > '0'".format(
                job_id))
        self._csdb.execute(query)
        if len(self._csdb.rows[0]) == 1 and self._csdb.rows[0][0] == '':
            return False
        return True

    def get_index_cache_path(
            self,
            job_id,
            ma_machine_object,
            backupset=None,
            version=1):
        """ Checks the MA logs and fetches Index cache
        location for the job specified

            Args:
                job_id              (str)   --  Job ID

                ma_machine_object   (obj)   --  Machine object of media agent

                backupset           (obj)   --  Backupset Object

                    default:    None

                version             (int)   -- Indexing version

                    Accepted values: 1 and 2

                    default:    1

            Returns:
                (str)     --  Returns Index cache location for the Job

            Raises:
                Exception:
                    if backupset is None when index version is 2

        """
        index_cache_location = ma_machine_object.get_registry_value(
            ma_machine_object.join_path("Machines", ma_machine_object.client_object.client_name),
            "dFSINDEXCACHE")
        self.log.info("Index cache location of MA: %s", index_cache_location)
        if version == 1:
            command = None
            log_dir_path = ma_machine_object.client_object.log_directory
            if "windows" in ma_machine_object.os_info.lower():
                command = (
                              "(Select-String -Path \"%s\CreateIndex.log\" -Pattern"
                              " \"%s.*INDEXCACHEDIR:.*job.*%s.*creating\")") % (log_dir_path, job_id, job_id)
            else:
                command = (
                              "sed -n \"/%s.*INDEXCACHEDIR.*job.*%s.*creating/s/:/ "
                              "/gp\" %s") % (job_id, job_id, log_dir_path)
            new_directory_created = None
            while True:
                new_directory_created = ma_machine_object.execute_command(command).formatted_output
                if new_directory_created != '':
                    break
            new_directory_created = new_directory_created.split("'")[1]
            self.log.info(
                "Index cache directory to be backed-up for this Job: %s",
                new_directory_created)
            return new_directory_created

        if backupset is None:
            raise Exception(
                'backup set object needs to be passed for index verison 2')
        indexing_directory_path = ma_machine_object.join_path(
            index_cache_location,
            "CVIdxLogs",
            str(self._commcell.commcell_id),
            backupset.guid,
            "J{0}".format(job_id))
        self.log.info(
            "Index cache directory to be backed-up for this Job: %s",
            indexing_directory_path)
        return indexing_directory_path

    def get_volume_id(self, snap_backup_jobid):
        """ method to fetch the volume ids associated with the snap backup
            Args:
                snap_backup_jobid   (int)  -- snap backup job id

            Returns:
                volume_id           (list) -- volume ids associated with
                the snap backup

            Raise:
                Exception:
                    if unable to find volume id

        """
        query = "select SMVolumeId from SMVolume where jobid='{0}'".format(
            snap_backup_jobid)
        self._csdb.execute(query)
        cur = self._csdb.rows
        if cur[0][0] != '':
            return cur
        self.log.error(
            "Unable to find the volume id for given backup job")
        raise Exception("Unable to find the volume id for given backup job")

    def synthfull_backup_validation(
            self, client_object, machine_object, subclient_object, is_synthfull_loop=False):
        """ method to run synthfull backup job and validate the synthfull job

        Args:

                client_object       (obj)   --  Client object

                machine_object      (obj)   --  Machine class object

                subclient_object    (obj)   --  Subclient Object

                is_synthfull_loop   (bool)  --  flag to determine if this is the
                synthfull loop testcase

                    default: False

        Raise:
            Exception:
                if failed to run mount job

                if unable to verify the mounted snap

                if failed to run unmount job

        """
        ##### run synthfull backup jobs ######
        self.log.info("Starting synthetic full backup.")
        synth_job = self.run_backup(subclient_object, "synthetic_full")
        self.log.info("Synthetic full backup %s is finished", synth_job.job_id)

        self.log.info(
            ("Running data aging on storage policy:%s copy:primary to "
             "make sure the restore is triggered from Synthfull backup"),
            subclient_object.storage_policy)

        common_utils = idautils.CommonUtils(self._commcell)
        data_aging_job = common_utils.data_aging(
            subclient_object.storage_policy, "primary", False)
        if not data_aging_job.wait_for_completion():
            raise Exception(
                "Failed to run data aging job with error: {0}".format(
                    data_aging_job.delay_reason
                )
            )
        self.log.info("Dataaging job run is:%s", data_aging_job.job_id)

        if is_synthfull_loop:
            return
        ######### Synth full validation #########
        self.log.info("Mounting the snap in client at:/tmp/testcase_mount")
        volume_id = int(self.get_volume_id(synth_job.job_id))
        self.log.info("Volume ID: %s", volume_id)
        # mount the snap in the client
        array_mgmt_object = self._commcell.array_management
        machine_object.execute_command("mkdir -p /tmp/testcase_mount")
        mount_job = array_mgmt_object.mount(
            [[volume_id]],
            client_object.client_name,
            "/tmp/testcase_mount")
        self.log.info(
            "Mounting the snapshot in the client with job:%s",
            mount_job.job_id)
        if not mount_job.wait_for_completion():
            raise Exception(
                "Failed to run mount job with error: {0}".format(
                    mount_job.delay_reason
                )
            )
        self.log.info("Succesfully mounted the snapshot in the client")

        # Validate the data
        # Run find command to check if the data is corrupted
        command = ("find /tmp/testcase_mount -type f -print "
                   "-exec cp -r {} /dev/null \; > readsnapdata")
        output = machine_object.execute_command(command)
        if output.exception_message != '':
            raise Exception("Unable to verify the mounted snap from synhfull job")
        self.log.info("Synthfull job is verified")

        # Unmount the snap
        self.log.info("Unmounting snapshot")
        unmount_job = array_mgmt_object.unmount(
            [[volume_id]])
        self.log.info(
            "UnMounting the snapshot in the client with job:%s",
            unmount_job.job_id)
        if not unmount_job.wait_for_completion():
            raise Exception(
                "Failed to run unmount job with error: {0}".format(
                    unmount_job.delay_reason
                )
            )
        self.log.info("Snapshot is unmounted")

    def delete_v2_index_restart_service(self, backupset):
        """ method to delete index cache and restart index services

        Args:
            backupset (obj) --  Backupset object

        """
        index_database = index_db.get(backupset)
        self.log.info('Deleting DB [%s]', index_database.db_path)
        index_database.delete_db()
        self.log.info('Shutting down index server after delete/rename operation')
        index_database.idx_cli.do_tools_shutdown_index_server()

    def _get_last_job_of_subclient(self, subclient):
        """ get the last backup job run for the subclient

        Args:
            subclient (obj) --  Subclient object

        Return:
            job_id -- Returns the job ID

        """
        job_controller = JobController(self._commcell)
        job_dict = job_controller.finished_jobs(
            subclient._client_object.client_name, lookup_time=24, job_filter='Backup')
        job_list = []
        for job in job_dict:
            if int(job_dict[job]['subclient_id']) == int(subclient.subclient_id):
                job_list.append(job)
        latest_job = sorted(job_list)[-1]
        return latest_job

    def _get_index_cache_ma(self, job_id):
        """ gets the MA used by the Job

        Args:
            job_id  (str)   --  Job ID

        """
        query = f"""select name from APP_Client where id=
                (select attributeValueInt from JMJobOptions where attributeName=
                'Current Index Cache MediaAgent' and jobId={job_id})"""
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        if cur[0] == '':
            raise Exception("Unable to get the media agent Name for the last backup job")
        media_agent_name = cur[0]
        return media_agent_name

    def delete_v1_index_restart_service(self, subclient):
        """ method to delete index cache and restart index service

        Args:
            subclient (obj) --  Subclient object

        """
        latest_job = self._get_last_job_of_subclient(subclient)
        media_agent_name = self._get_index_cache_ma(latest_job)
        media_agent = MediaAgent(self._commcell, media_agent_name)
        ma_machine = machine.Machine(media_agent_name, self._commcell)
        index_cache_path = media_agent.index_cache_path
        index_cache_path = ma_machine.join_path(
            index_cache_path, 'Cv_Index', '2', str(subclient.subclient_id))
        self.log.info("Deleting contents of the path:%s", index_cache_path)
        ma_machine.remove_directory(index_cache_path)
        self.log.info("Killing the IndexingService proces on MA")
        ma_machine.kill_process("IndexingService")

    def set_http_proxy_for_cs(self, proxy_server, proxy_port):
        """Sets the http proxy server at Commserve level
        Args:
            proxy_server  (str) --  Name of the http proxy server

            proxy_port  (int)   --  Port number for http proxy

        """
        internet_options_obj = InternetOptions(self._commcell)
        internet_options_obj.set_http_proxy(proxy_server, proxy_port)

    def block_cloud_endpoint_on_accessnode(self, access_node, validate=True):
        """Method to edit the hosts file on access node to point cloud endpoints to
        loop back address so that direct connections to cloud do not work. Ensure that
        config.json file under C:\Program Files\Commvault\ContentStore\Automation\
        CoreUtils\Templates is populated with the endpoints to block in list format
        Example :
        "BlockCloudEndPoints": {
            "endpoints": [
            "127.0.0.1     rds.ap-south-1.amazonaws.com",
            "127.0.0.1     dynamodb.ap-southeast-1.amazonaws.com",
            "127.0.0.1     sts.us-east-1.amazonaws.com"
            ]
        }

        Args:
            access_node (str)    --  Name of the access node/ client name

            validate (boolean)  --  Runs ping command to validate if editing hosts file is successful
                            True-Runs ping command to check if cloud endpoint loops back to localhost
                            False- Just adds the entries into hosts file and skips running ping
        """
        try:
            _CONF = config.get_config()
            _CONSTANTS = _CONF.BlockCloudEndPoints
            end_points = _CONSTANTS.endpoints
            if not isinstance(end_points, list):
                raise Exception("The config file is not populated with entries to block"
                                "or format is incorrect")
            access_node_obj = machine.Machine(access_node, self._commcell)
            os_type = access_node_obj.os_info
            if os_type == 'UNIX':
                host_file = r'/etc/'
                temp_location = r'/tmp/'
                cp_command = r'\cp /etc/hosts /tmp/hosts_edit'
                ping_command = r'ping -c 4 '
            elif os_type == 'WINDOWS':
                host_file = r'C:\\Windows\\System32\\drivers\\etc\\'
                temp_location = r'C:\\'
                cp_command = 'cmd /c "cd C:\\Windows\\System32\\drivers\\etc && copy hosts C:\\hosts_edit"'
                ping_command = 'ping '
            else:
                raise Exception('Supported OS types are: WINDOWS and UNIX')
            access_node_obj.execute_command(cp_command)
            access_node_obj.append_to_file(temp_location + 'hosts_edit', "\n")
            for line in end_points:
                access_node_obj.append_to_file(temp_location + 'hosts_edit', line)
            access_node_obj.rename_file_or_folder(
                host_file + 'hosts', host_file + 'hosts_original')
            access_node_obj.move_file(temp_location + 'hosts_edit', host_file + 'hosts')
            if validate:
                result = access_node_obj.execute_command(ping_command + end_points[0]).output
                if result.find('127.0.0.1') > 0:
                    self.log.info("Internet access successfully blocked")
                else:
                    self.log.exception("Access node is able to connect to given services "
                                       "check BlockCloudEndPoints key in config.json")
        except Exception as exp:
            self.cleanup_http_proxy_config(access_node)
            raise Exception("Blocking cloud endpoints is not successful: %s", exp)

    def cleanup_http_proxy_config(self, access_node):
        """Removes the http proxy setting at Commserve level and reverts the
        host entries on access node that were added to block cloud endpoints

        Args:
            access_node (str)   --  Name of the access node/client
        """
        internet_options_obj = InternetOptions(self._commcell)
        internet_options_obj.disable_http_proxy()
        self.log.info("Disabled http proxy setting on Commserver successfully")
        access_node_obj = machine.Machine(access_node, self._commcell)
        os_type = access_node_obj.os_info
        if os_type == 'UNIX':
            host_file = r'/etc/'
            temp_location = r'/tmp/'
        elif os_type == 'WINDOWS':
            host_file = r'C:\\Windows\\System32\\drivers\\etc\\'
            temp_location = r'C:\\'
        else:
            raise Exception('Unsupported operating system type found')
        if access_node_obj.check_file_exists(host_file + 'hosts_original'):
            access_node_obj.delete_file(host_file + 'hosts')
            access_node_obj.move_file(host_file + 'hosts_original', host_file + 'hosts')
        if access_node_obj.check_file_exists(temp_location + 'hosts_edit'):
            access_node_obj.delete_file(temp_location + 'hosts_edit')

    def delete_client_access_control(self, client1=None, client2=None, client_list=None):
        """ method to delete client entries from App_ClientAccessControl

            Args:
                client1 (obj)  -- client1 object
                client2 (obj)  -- client2 object
                client_list (list) -- list of IDs of clients

            Raise:
            Exception:
                if failed to o delete client entries
                from App_ClientAccessControl table

        """
        cs_sql_user = config.get_config().SQL.Username
        cs_sql_password = config.get_config().SQL.Password
        if not (cs_sql_user or cs_sql_password):
            raise Exception(" CSDB crdentials are not in config file.")
        server_name = f"{self._commcell.commserv_hostname}\commvault"

        if client_list:
            clients = ','.join([str(client_id) for client_id in client_list])
        else:
            clients = ','.join([str(client_id) for client_id in [client1.client_id, client2.client_id]])

        try:
            query = ("delete from App_ClientAccessControl "
                     "where AccessedClientId in ({0}) or PrivilegedClientId in ({0})".format(clients))
            csdb = database_helper.MSSQL(server_name, cs_sql_user, cs_sql_password, "CommServ")
            csdb.execute(query)
            self.log.info("Client entries deleted from CSDB")
            csdb.close()
        except Exception as exp:
            raise Exception("Unable to delete client entries from App_ClientAccessControl table.") from exp

    def get_ma_names(self, storage_policy):
        """Gets the Media_agent name associated with the storage_policy

        Args:
            storage_policy   (str)   -- Storage Policy name

        Returns:
            Returns list of media agent names

        Raises:
            Exception:
                if failed to get the MA name associated with the Storage policy

        """
        if not isinstance(storage_policy, str):
            raise Exception("The storage_policy has to be string")

        query = ("select name from APP_Client where id in "
                 "(select HostClientId from MMDataPath where CopyId in "
                 "(SELECT id FROM archgroupcopy where archGroupId="
                 "(select id from archGroup where name='{0}')))".format(storage_policy))
        self._csdb.execute(query)
        cur = self._csdb.fetch_all_rows()
        if cur:
            ma_names = []
            for ma_name in cur:
                ma_names.append(ma_name[0])
            self.log.info("Fetched MA Names {0}".format(ma_names))
            return ma_names
        else:
            raise Exception("Failed to get the MA names from database")

    def get_proxy_names(self, pseudoclient):
        """ Method to get the list of proxies associated with pseudoclient
        Args:
            pseudoclient    (obj)   -- pseudoclient object
        Returns:
            list of proxy names associated with pseudoclient
        Raises:
            Exception:
                If failed to fetch the proxy names of the associated psudoclient
        """

        client_id = pseudoclient.client_id
        query = ("select attrVal from APP_InstanceProp where componentNameId in "
                 "(select instance from APP_application where clientId={0} and appTypeId=106 "
                 "and subclientName='default') and attrName like 'Vs Member Servers'".format(client_id))
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        if cur:
            root = ElementTree.fromstring(cur[0])
            proxy_list = list()
            for child in root:
                proxy_list.append(child[0].attrib['clientName'])
            self.log.info("Fetched proxy list {0}".format(proxy_list))
            return proxy_list
        else:
            raise Exception("Failed to fetch proxy list from database")

    def install_db_agent(self, agent_name, machine_object, storage_policy=None, **kwargs):
        """ method to install DB agent on a client machine

        Args:
            agent_name    (str)   -- Name of the agent to be installed

            machine_object  (obj)   --  Machine obejct of the client

            storage_policy  (str)   --  Name of the storage policy
            to be associated to the client

            **kwargs:
            db2_logs_dir    (dict)   --  DB2 Logs directory
                Ex: db2_logs_location = {
                                "db2ArchivePath": "/opt/Archive/",
                                "db2RetrievePath": "/opt/Retrieve/",
                                "db2AuditErrorPath": "/opt/Audit/"
                        }

        Raises:
            Exception:
                if installation fails on the client

        """
        install_helper = InstallHelper(self._commcell, machine_object)
        job = install_helper.install_software(
            [machine_object.machine_name], [agent_name], storage_policy_name=storage_policy,
            allowMultipleInstances=True, **kwargs)
        self.log.info(
            "Started push install with Job ID: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run install job with error: {job.delay_reason}")
        self.log.info("Successfully finished install job")
        install_helper.commcell.clients.refresh()
        self._commcell.clients.refresh()

    def check_permissions_after_install(self, client, group_name):
        """ Method to verify group permissions in a client

        Args:

            client      (obj)   -- Client Object

            group_name  (str)   --  Name of the group to verify

        Raises:
            Exception:
                if permissions are not provided for postgres group

        """
        machine_object = machine.Machine(client)
        log_group = machine_object.get_file_group(client.log_directory)
        job_results_group = machine_object.get_file_group(client.job_results_directory)
        base_group = machine_object.get_file_group(machine_object.join_path(client.install_directory, "Base"))
        self.log.info(
            "LOG directory group: %s, Base directory Group: %s, Job Results Directory Group: %s",
            log_group, job_results_group, base_group)
        if not group_name == log_group == job_results_group == base_group:
            raise Exception(f"Group of CV directories is not set to {group_name}")
        self.log.info(f"Unix group is auto detected and set as '{group_name}' during install")

    def run_aux_copy_for_cloud_storage(self, storage_policy):
        """Method to run aux copy job for replicating content to secondary storage for cloud storage
            Args:
                storage_policy(str) -- storage policy name on which aux copy job need to be run
        """
        try:
            storage_policy_object = self._commcell.storage_policies.get(storage_policy)
            job = storage_policy_object.run_aux_copy()
            self.log.info("Started backup copy job with Job ID: %s", job.job_id)
            if not job.wait_for_completion():
                raise Exception(f"Failed to run job:{job.job_id} with error: {job.delay_reason}")
            self.log.info(f"Successfully finished {job.job_id} job")
        except SDKException:
            self.log.info("An exception occurred while running a fresh aux copy job. "
                          "Checking if any aux copy job got triggered by schedule")
            job_controller_object = JobController(self._commcell)
            jobs = job_controller_object.active_jobs(job_filter='')
            self.log.info(jobs)
            is_aux_copy_job_started = False
            for job in jobs.keys():
                if jobs[job]['job_type'] == 'Aux Copy (Dash)':
                    job_object = job_controller_object.get(job)
                    job_summary = job_object.summary
                    if job_summary['plan']['planName'] == storage_policy:
                        is_aux_copy_job_started = True
                        current_job = job_controller_object.get(job)
                        self.log.info(f"waiting for aux copy job - {job} to get finished")
                        current_job.wait_for_completion()
                        self.log.info(f'job {job} got completed')
            if is_aux_copy_job_started:
                try:
                    storage_policy_object = self._commcell.storage_policies.get(storage_policy)
                    job = storage_policy_object.run_aux_copy()
                    self.log.info(
                        "Running the aux copy just after finishing the scheduled aux copy job "
                        "to make sure all the backed up content to get replicated")
                    if not job.wait_for_completion():
                        raise Exception(f"Failed to run job:{job.job_id} with error: {job.delay_reason}")
                    self.log.info(f"Successfully finished {job.job_id} job")
                except SDKException:
                    self.log.info("The Scheduled job must have replicated the data to the secondary copy")
            if not is_aux_copy_job_started:
                raise Exception("No Aux copy jobs were ran. please check and take necessary actions")

    def wait_for_job_completion(self, jobid):
        """
        Waits for completion of the job
        Args:
            jobid   (str): Jobid
        """
        job_obj = self._commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise SDKException('Job', '102',
                               f"Failed to run job:{jobid} with error: {job_obj.delay_reason}")
        self.log.info(f"Successfully finished {jobid} job")

    def compare_dictionaries(self, source_dictionary, destination_dictionary):
        """Compares two dictionaries for validation
            Args:
                source_dictionary(dict):    dictionary1 to compare the contents of dictionaries

                destination_dictionary(dict):   dictionary2 to compare the contents of dictionaries
        """
        self.log.info("received data for validation are:")
        self.log.info(f"Source: {source_dictionary}")
        self.log.info(f"Destination: {destination_dictionary}")
        if len(source_dictionary) != len(destination_dictionary):
            self.log.info(f"Difference : {source_dictionary.keys() - destination_dictionary.keys()}")
            raise CVException(
                f"Number of Keys didn't match hash1 {len(source_dictionary)} and hash2 {len(destination_dictionary)}")
        if source_dictionary == destination_dictionary:
            self.log.info("Both the given dictionaries are intact")
        else:
            self.log.info(f"Difference : {DeepDiff(source_dictionary, destination_dictionary)}")
            self.log.warning("Entities didn't match in the given the dictionaries")

    def wait_for_active_jobs(self, job_filter, client_name=None):
        """Method waits for the active jobs running on client
           Args:
                job_filter(str) : Type of the job to filter
                client_name(str): Name of the client
        """
        self._commcell.refresh()
        active_jobs = self._commcell.job_controller.active_jobs(
            client_name=client_name, job_filter=job_filter)
        for job in active_jobs:
            self.log.info(f"Waiting for job with id: {job} to complete")
            self._commcell.job_controller.get(job).wait_for_completion()
            self.log.info("Job Completed Successfully")

    def clear_automation_credentials(self, credential_prefix, hours=3):
        """
        Clears all credentials starting with the provided prefix
        if the credential has been there for more than the input hours.

        Args:
            credential_prefix (str): The prefix of the credentials to be cleared. Should have timestamp separated by "-" at the end.
                                    e.g. - "automation-credential-1712907257"
            hours (int): The hours to compare with the credential timestamp.
        """
        time_diff = datetime.now() - timedelta(hours=hours)
        credential_list = self.credential_manager.all_credentials

        for credential in credential_list:
            if credential.startswith(credential_prefix):
                timestamp_str = credential.split("-")[-1]
                timestamp = int(timestamp_str)
                cred_time = datetime.fromtimestamp(timestamp)

                if cred_time < time_diff:
                    try:
                        self.credential_manager.delete(credential)
                    except Exception as e:
                        self.log.info(f"Error occurred while removing credential {credential}: {str(e)}")

    def unzip_downloaded_file(self, base_path, dest_path):
        """
        Unzips the downloaded data on the base path to the destination path

        Args:
            base_path (str): The base path of the downloaded data
            dest_path (str): The destination path to unzip the data
        """

        # Find the zip file starting with the prefix 'Download_' in the base path directory
        self.zip_file = next(iter(glob(os.path.join(base_path, 'Download_*.zip'))), None)
        self.log.info(f"Found zip file: {self.zip_file}")

        if self.zip_file is None:
            raise FileNotFoundError(f"No zip file starting with 'Download_' found in the directory {base_path}")

        # Unzip the file
        with zipfile.ZipFile(self.zip_file, 'r') as zfile:
            zfile.extractall(dest_path)
        self.log.info(f"Unzipped the file to {dest_path}")
        os.remove(self.zip_file)
        self.log.info(f"Deleted the zip file {self.zip_file}")
