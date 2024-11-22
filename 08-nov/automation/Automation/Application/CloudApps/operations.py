# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module for communicating with cvpysdk for all commvault related operations.

CvOperation class is defined in this file.

CvOperation: Performs Commvault related operations using cvpysdk

CvOperation:
        __init__(cloud_object)  --  Initializes the CvOperation object

        delete_client() --  Performs deletion of OneDrive client

        kill_job()  --  Kills the specified job

        wait_until_discovery_is_complete()  --  Waits for discovery to be complete till specified time

        _wait_time  --  Waits for the specified interval of time

        restore_subclient() --  Runs restore for subclient object of cvpysdk

        verify_browse() --  Verifies the commvault browse with Google folders

        check_job_status()  --  Checks the status of job until it is finished and
            raises exception on pending, failure etc.

        cleanup()   --  Method to remove temp data which is generated/stored during automation run

        get_number_of_successful_items()    --  Method to get number of items successful in a backup job

        check_playback_completion()         --  Checks whether playback for the backup job is completed or not

        get_job_results_dir()               --  Get the full job results directory

        update_user_associations()         --  Include, Exclude, Remove and associate users in subclient

        update_group_associations()         --  Include, Exclude, Remove and associate users in subclient

        update_custom_category_associations()       --  Include, Exclude and  Remove custom groups in subclient

"""

from __future__ import unicode_literals
import os
import shutil
from random import randrange
import time
from Server.JobManager.jobmanager_constants import JobOpCode
from Server.JobManager.jobmanager_helper import JobManager
from cvpysdk.exception import SDKException
from AutomationUtils.machine import Machine
from . import constants
from .exception import CVCloudException
from ..Office365.solr_helper import CVSolr
from dynamicindex.utils import constants as cs


class CvOperation:
    """Class for performing Commvault operations"""

    def __init__(self, cc_object):
        """Initializes the CvOperation object

                Args:

                    cc_object  (object)  --  instance of CloudConnector class

                Returns:

                    object  --  instance of CvOperation class

        """
        self.cc_object = cc_object
        self.tc_object = self.cc_object.tc_object
        self.commcell = self.tc_object.commcell
        self.backupset = self.tc_object.backupset
        self.instance = self.tc_object.instance
        self.subclient = self.tc_object.subclient
        self.log = self.tc_object.log
        self.app_name = self.__class__.__name__  # Used for exception list
        self.dbo = self.cc_object.dbo
        self.fs_client = None
        self.fs_agent = None
        self.fs_bkpset = None
        self.fs_subclient = None
        self.subclients_object = None

    def delete_client(self, client_name):
        """Performs deletion of OneDrive client

            Args:
                client_name (str)   --   client name

            Raises:
                CVCloudException:
                    if client deletion is not successful
        """
        try:
            job_helper = self.commcell.job_controller

            for job_id in job_helper.active_jobs(client_name):
                job = self.commcell.job_controller.get(job_id)
                self.kill_job(job)

            self.log.info("Deleting client [{0}] from client list".format(client_name))
            self.commcell.clients.delete(client_name)
            self.log.info(f'Client [{client_name}] has been deleted from the client list successfully.')

        except Exception as exception:
            self.log.exception(f'Exception raise while deleting client: {str(exception)}')
            raise CVCloudException(self.app_name, '501', f'Exception raised in deleting client\nError: {exception}')

    def kill_job(self, job, wait_for_job_to_kill=True):
        """Kills the specified job

            Args:
                  job (object)                    --    object of Job
                  wait_for_job_to_kill (boolean)  --    wait till job status is changed to Killed
                    default: True

            Raises:
                CVCloudException:
                    if kill operation for job was not successful
        """
        try:
            self.log.info("Killing active job [{0}]".format(job.job_id))
            job.kill(wait_for_job_to_kill)
            if job.status.lower() == 'killed':
                self.log.info('Job is killed successfully')
            elif job.status.lower() == 'committed':
                self.log.info('Job is committed successfully')
            else:
                raise CVCloudException(self.app_name, '501', f'Job is not killed with status: {job.status.lower()}')
        except Exception as exception:
            self.log.exception(f'Failed to kill job with exception: {str(exception)}')
            raise CVCloudException(self.app_name, '501', f'Failed to kill job {job.job_id} with error :{exception}')

    def wait_until_discovery_is_complete(self, time_out=1200, poll_interval=30):
        """
            Waits for discovery to be complete till specified time

            Args:
                time_out (int)         --  maximum wait time(seconds), for the process to complete
                poll_interval (int)    --  time(seconds) to sleep before checking status of discovery again

            returns:
                user_response (list)    -- users' details list fetched from discovered content queried against user_id
        """
        try:
            current_time = time.time()
            end_time = current_time + time_out
            while current_time <= end_time:
                discovery_status, total_records = self.tc_object.subclient.verify_discovery_onedrive_for_business_client()
                if discovery_status:
                    self.log.info('Discovery successful')
                    return discovery_status
                else:
                    self.log.info("Discovery is not complete yet")
                    self._wait_time(poll_interval, "Waiting for the discovery to complete")
                current_time = time.time()
            self.log.exception("Discovery did not complete in stipulated time %d ", time_out)
            raise CVCloudException('OneDrive', '101')
        except Exception as exception:
            self.log.exception(f'Exception during discovery: {str(exception)}')
            raise CVCloudException(self.app_name, '906')

    def _wait_time(self, time_sec=300, log_message=None):
        """Waits for the specified interval of time. Default time = 300 seconds

            Args:

                time_sec (int)      --   time in secs

                log_message (str)   --   message to be displayed

        """
        if log_message is not None:
            self.log.info(str(log_message))
        self.log.info("Sleeping for [%s] seconds", str(time_sec))
        time.sleep(time_sec)

    def restore_subclient(self, oop=False, to_disk=False, incremental=False):
        """Runs restore for subclient object of cvpysdk.
        Stores job list in the db. Raises exception if restore job is not successful

                Args:

                    oop (boolean)  --  set it True to run out of place restore
                                        Default: False

                    to_disk (boolean)  --  Set if True to run out of place restore to disk

                    incremental  (boolean)  --  Set True if only incremental data has to be restored

        """

        try:
            instance_type = self.tc_object.instance.ca_instance_type
            from_time = None
            to_time = None
            if incremental:
                # we need to get start time and end time of last incremental job
                # fetch the last incremental job id from local db
                self.log.info('This is incremental job level restore')
                backup_list = self.dbo.get_content('backup_table')

                for content in backup_list:
                    if content['backup_level'] == 'Incremental':
                        self.log.info('Following job will be used for job level restore: %s',
                                      content)
                        from_time = content.get('start_time')
                        to_time = content.get('to_time')
                        break

            if oop:
                if instance_type == 'GMAIL':

                    paths, dictionary = self.tc_object.subclient.browse(path='\\Gmail')
                    random_number = randrange(len(paths))
                    source_label = 'INBOX'
                    oop_source = [f'{paths[random_number]}\\{source_label}']
                    self.log.info(
                        'Setting source path for OOP restore as "%s"', oop_source)
                    random_number = randrange(len(paths))
                    destination_label = 'automation'
                    oop_destination = paths[random_number].split("\\")[2] + '/' + destination_label
                    self.log.info(
                        'Setting destination path for OOP restore as "%s"', oop_destination)
                    job = self.tc_object.subclient.restore_out_of_place(
                        self.tc_object.client, oop_destination, oop_source)
                    data = {'job_list': [job.job_id, oop_source, oop_destination]}
                    self.dbo.save_into_table('job', data, data_type='list')

                elif instance_type in ['GDRIVE', 'ONEDRIVE']:

                    paths1, dictionary = self.tc_object.subclient.browse(path=f'\\{instance_type}')
                    self.log.info('paths in 1st iteration: %s', paths1)
                    random_number = randrange(len(paths1))
                    user_id = paths1[random_number].split('\\')[2]
                    self.log.info('user id: %s', user_id)
                    paths, dictionary = self.tc_object.subclient.browse(path=paths1[random_number])
                    self.log.info('paths in 2nd iteration: %s', paths)
                    if instance_type == 'GDRIVE':
                        folder_id = self.cc_object.gdrive.get_folder_id(user_id)
                        oop_source = [f'{paths[0]}\\{folder_id}']
                    else:
                        if len(paths) == 2:
                            oop_source = [f'{paths[1]}\\{constants.ONEDRIVE_FOLDER}']
                        else:
                            oop_source = [f'{paths[0]}\\{constants.ONEDRIVE_FOLDER}']
                    self.log.info('oop source: %s', oop_source)

                    if to_disk:
                        self.log.info('This is restore to disk')
                        self.log.info('oop destination: %s', constants.DESTINATION_TO_DISK)
                        job = self.tc_object.subclient.restore_out_of_place(
                            client=self.tc_object.instance.proxy_client,
                            destination_path=constants.DESTINATION_TO_DISK,
                            paths=oop_source,
                            to_disk=True)
                        data = {
                            'job_list': [
                                job.job_id,
                                oop_source,
                                constants.DESTINATION_TO_DISK,
                                user_id]}
                        self.dbo.save_into_table('job', data, data_type='_list_disk')
                    else:
                        # destination path should be other user smtp address plus the folder name
                        # client should be google client
                        # source item as above
                        # rest_to_google = true, rest_to_diff_account = true, dest_user_account =
                        # user smtp
                        self.log.info('This is OOP restore to other user account')
                        random_number = randrange(len(paths1))
                        dest_user_id = paths1[random_number].split('\\')[2]
                        self.log.info('Destination user id: %s', dest_user_id)
                        if instance_type == 'GDRIVE':
                            self.cc_object.gdrive.delete_single_folder(dest_user_id)
                        else:
                            self.cc_object.one_drive.delete_folder(user_id=dest_user_id)
                        dest_path = dest_user_id
                        job = self.tc_object.subclient.restore_out_of_place(
                            client=self.tc_object.client,
                            destination_path=dest_path,
                            paths=oop_source,
                            to_disk=False)
                        data = {'job_list': [job.job_id, oop_source, dest_user_id, user_id]}
                        self.dbo.save_into_table('job', data, data_type='_list_oop')

            else:
                if instance_type in ['GDRIVE', 'ONEDRIVE']:
                    source_path_list = []
                    paths1, dictionary = self.tc_object.subclient.browse(path=f'\\{instance_type}')
                    self.log.info('paths in 1st iteration: %s', paths1)

                    for path in paths1:
                        user_id = path.split('\\')[2]
                        self.log.info('user id: %s', user_id)
                        paths, dictionary = self.tc_object.subclient.browse(path=path)
                        self.log.info('paths in 2nd iteration: %s', paths)
                        if instance_type == 'GDRIVE':
                            folder_id = self.cc_object.gdrive.get_folder_id(user_id)
                            oop_source = f'{paths[0]}\\{folder_id}'
                        else:
                            if len(paths) == 2:
                                oop_source = f'{paths[1]}\\{constants.ONEDRIVE_FOLDER}'
                            else:
                                oop_source = f'{paths[0]}\\{constants.ONEDRIVE_FOLDER}'
                        source_path_list.append(oop_source)
                        self.log.info('Source path list: %s', source_path_list)

                else:
                    source_path_list, dictionary = self.tc_object.subclient.browse(path='\\')
                job = self.tc_object.subclient.restore_in_place(paths=source_path_list,
                                                                from_time=from_time,
                                                                to_time=to_time)

        except SDKException as excp:
            raise CVCloudException(self.app_name, '401', str(excp))
        except Exception as excp:
            raise CVCloudException(self.app_name, '501', str(excp))
        self.check_job_status(job, backup_level_tc='RESTORE')

    def restore_fs_to_od(self,
                         destination_path,
                         source_path):
        """Restores file system backed up data to a user account on OneDrive

                Args:

                    destination_path  (str)  --  Destination path on OneDrive

                    source_path  (str)  --  Source path on File System

                Returns:

                    Job  (instance)  --  Instance of Job class of cvpysdk
        """
        try:
            paths = source_path

            self.fs_subclient._backupset_object._instance_object._restore_association = self.fs_subclient._subClientEntity
            request_json = self.fs_bkpset._restore_json(
                paths=paths,
                in_place=False,
                client=self.tc_object.client,
                destination_path=destination_path,
                overwrite=True,
                restore_data_and_acl=True,
                copy_precedence=None,
                from_time=None,
                to_time=None
            )
            dest_user_account = destination_path
            rest_different_account = True
            restore_to_google = True

            request_json["taskInfo"]["subTasks"][0]["options"][
                "restoreOptions"]['cloudAppsRestoreOptions'] = {
                "instanceType": self.tc_object.instance.ca_instance_type,
                "googleRestoreOptions": {
                    "strDestUserAccount": dest_user_account,
                    "folderGuid": "",
                    "restoreToDifferentAccount": rest_different_account,
                    "restoreToGoogle": restore_to_google
                }
            }
            request_json["taskInfo"]["subTasks"][0]["options"][
                "restoreOptions"]["destination"]["noOfStreams"] = 1
            request_json["taskInfo"]["subTasks"][0]["options"][
                "restoreOptions"]["destination"]["destinationInstance"] = {
                "instanceName": self.tc_object.instance.instance_name,
                "appName": self.tc_object.agent.agent_name,
                "clientName": self.tc_object.client.client_name
            }
            request_json["taskInfo"]["subTasks"][0]["options"][
                "restoreOptions"]["qrOption"] = {"destAppTypeId": 134}
            self.log.info("Restore JSON: %s", request_json)
            return self.fs_bkpset._process_restore_response(request_json)
        except SDKException as excp:
            raise CVCloudException(self.app_name, '401', str(excp))
        except Exception as excp:
            raise CVCloudException(self.app_name, '501', str(excp))

    def verify_browse(self):
        """Verifies the commvault browse with Google folders"""

        sc_content = self.tc_object.subclient.content

        sc_content_list = []
        gmail_browse_path = '\\Gmail'
        try:
            for content in sc_content:
                sc_content_list.append(content.get('SMTPAddress'))
            paths, dictionary = self.tc_object.subclient.browse(path=gmail_browse_path)
            self.log.debug('paths: %s', paths)
            for path in paths:
                self.log.debug('path: %s', path)
                userid = path.split('\\')[2]
                if userid not in sc_content_list:
                    self.log.exception(
                        'User account not found in browse content: %s', path)
                    raise CVCloudException(self.app_name, '801')
                else:
                    paths1, dict1 = self.tc_object.subclient.browse(path=path)
                    self.log.info('paths1: %s', paths1)

                    for path1 in paths1:
                        label = path1.split('\\')[3]

                        if label.upper() == 'SENT MAIL':
                            label = 'SENT'
                        if label.upper() == 'DRAFTS':
                            label = 'DRAFT'
                        if label.find('\x16') >= 0:
                            self.log.info('found slash')
                            label = label.replace('\x16', '/')
                            self.log.info('slash replaced: %s', label)

                        if_exists, total_messages = self.dbo.search_label(label, userid)
                        if if_exists:
                            self.log.info(
                                'Label %s exist in the list got from Google.', label)
                            try:
                                paths2, dict2 = self.tc_object.subclient.browse(path=path1)

                                # # # Paths2 can be a nested label too or a combination of
                                # nested label and messages. Identify here # # #

                            except SDKException as excp:
                                if excp.exception_id == '110':
                                    self.log.info(
                                        'There is no mail in Label: %s', label)
                                    paths2 = []
                                else:
                                    self.log.exception(
                                        'Exception while browsing GMail label')
                                    raise CVCloudException(
                                        self.app_name, '901', str(excp))

                            if len(paths2) == total_messages:
                                self.log.info(
                                    'number of mails matched in the label: %s', label)
                            else:
                                self.log.error(
                                    'paths2: %s', paths2)

                                self.log.exception(
                                    'Number of mails are not matching in label: %s', label)
                                raise CVCloudException(
                                    self.app_name, '902')
                        else:
                            self.log.exception(
                                'Label got from browse could not be found in '
                                'Google Dict: %s', label)
                            raise CVCloudException(self.app_name, '903')

        except Exception as excpt:
            self.log.exception('Exception in browse verification.')
            raise CVCloudException(self.app_name, '501', str(excpt))

    def check_job_status(self, job, backup_level_tc):
        """Checks the status of job until it is finished and
            raises exception on pending, failure etc.

                Args:

                    job (Object of job class of CVPySDK)

                    backup_level_tc  (str)  --  Type of backup level intended

        """
        job_type = job.job_type
        backup_level = job.backup_level
        if job_type == 'Restore':
            backup_level = ""

        self.log.info('%s %s started for subclient "%s" with job id: "%s"',
                      backup_level, job_type, self.tc_object.subclient.subclient_name, job.job_id)

        if not job.wait_for_completion():
            pending_reason = job.pending_reason

            raise CVCloudException(
                self.app_name, '101', pending_reason)

        self.log.info(
            '%s job completed successfully.', job_type)

        if job_type == 'Backup':
            self.log.info('Checking whether backup level converted')
            job.refresh()
            new_backup_level = job.backup_level
            if new_backup_level.lower() != backup_level_tc.lower():
                self.log.error('Backup level converted to %s. Testcase required backup level: %s',
                               (new_backup_level, backup_level_tc))
                raise CVCloudException(self.app_name, '104')
            self.log.info('Backup level is as intended')
        data = {
            'backup_level': backup_level,
            'jobid': job.job_id,
            'job_type': job_type,
            'start_time': job.start_time,
            'end_time': job.end_time
        }
        self.dbo.save_into_table('backup', data, '_table')

    def create_subclient(
            self,
            name,
            content,
            filter_content=None,
            exception_content=None,
            trueup_option=True,
            trueup_days=30,
            scan_type=1,
            data_readers=2,
            allow_multiple_readers=False,
            read_buffer_size=512,
            block_level_backup=None,
            delete=True,
            data_access_nodes=None,
            **kwargs
    ):
        """Creates subclient under current testcase backupset
            with specified parameters

            Args:
                name (str)                       -- subclient name

                content (list)                   -- content list

                filter_content (list)            -- filter list
                    default: None

                exception_conent (list)          -- exception list
                    default: None

                trueup_option (bool)             -- enable / disable true up
                    default: True

                trueup_days (int)                -- trueup after n days value of the subclient
                    default: 30

                data_readers (int)               -- number of data readers
                    default: 2

                allow_multiple_readers (bool)    -- enable / disable allow multiple readers
                    default: False

                read_buffer_size (int)           -- read buffer size in KB
                    default: 512

                delete (bool)                    -- indicates whether existing subclient should be deleted
                    default: False

                scan_type(ScanType(Enum))        --  scan type (RECURSIVE/OPTIMIZED/CHANGEJOURNAL)
                    default: ScanType.RECURSIVE

                data_access_nodes(list)          -- Data Access nodes for NFS share or big data apps
                    default : None

                block_level_backup (str)         -- blocklevel backup data switch
                    default: None

                \*\*kwargs  (dict)              --  Optional arguments.

                Available kwargs Options:

                    software_compression(SoftwareCompression(Enum)) :   Software compression property for a subclient.
                    (ON_CLIENT/ON_MEDIA_AGENT/USE_STORAGE_POLICY_SETTINGS/OFF)

            Returns:
                None

            Raises:
                Exception - Any error occurred during Subclient creation

        """
        try:
            # Create FS client object using cloud apps proxy client
            storage_policy = self.tc_object.subclient.storage_policy
            self.fs_client = self.tc_object.commcell.clients.get(self.tc_object.instance.proxy_client)
            self.fs_agent = self.fs_client.agents.get('file system')
            self.fs_bkpset = self.fs_agent.backupsets.get('defaultBackupSet')
            self.log.info("Checking if subclient %s exists.", name)
            self.subclients_object = self.fs_bkpset.subclients

            if self.subclients_object.has_subclient(name):
                if delete:
                    self.log.info("Subclient exists, deleting subclient %s", name)
                    self.subclients_object.delete(name)
                    self.log.info("Creating subclient %s", name)
                else:
                    self.log.info("Subclient exists, use existing subclient %s", name)
                    self.fs_subclient = self.subclients_object.get(name)
                    return self.fs_subclient
            else:
                self.log.info("Subclient doesn't exist, creating subclient %s", name)

            self.fs_subclient = (
                self.subclients_object.add(name, storage_policy)
            )
            # self.fs_subclient.content = content

            self.update_subclient(
                content=content,
                filter_content=filter_content,
                exception_content=exception_content,
                trueup_option=trueup_option,
                trueup_days=trueup_days,
                scan_type=scan_type,
                data_readers=data_readers,
                allow_multiple_readers=allow_multiple_readers,
                block_level_backup=block_level_backup,
                read_buffer_size=read_buffer_size,
                data_access_nodes=data_access_nodes,
                software_compression=kwargs.get('software_compression', None)
            )

        except Exception as excp:
            self.log.error('Subclient Creation Failed with error: %s', str(excp))
            raise Exception('Subclient Creation Failed with error: {0}'.format(str(excp)))

    def update_subclient(self,
                         storage_policy=None,
                         content=None,
                         filter_content=None,
                         exception_content=None,
                         trueup_option=None,
                         trueup_days=None,
                         scan_type=None,
                         data_readers=None,
                         allow_multiple_readers=None,
                         read_buffer_size=None,
                         block_level_backup=None,
                         createFileLevelIndex=False,
                         data_access_nodes=None,
                         backup_system_state=None,
                         **kwargs):
        """Updates subclient property of current
            testcase subclient with specified parameters

            Args:
                storage_policy (str)            -- storage policy to assign to subclient
                    default: None

                content (list)                  -- content list
                    default: None

                filter_content (list)           -- filter list
                    default: None

                exception_conent (list)         -- exception list
                    default: None

                trueup_option (bool)            -- enable / disable true up
                    default: None

                trueup_days (int)               -- trueup after n days value of the subclient
                    default: None

                scan_type(ScanType(Enum))       -- scan type(RECURSIVE/OPTIMIZED/CHANGEJOURNAL)
                    default: None

                data_readers (int)              -- number of data readers
                    default: None

                allow_multiple_readers (bool)   -- enable / disable allow multiple readers
                    default: None

                read_buffer_size (int)          -- read buffer size in KB
                    default: None

                data_access_nodes (list)        -- sets the list passed as data access nodes
                or backup nodes for this subclient

                blockLevelBackup                -- enable/Disable Blocklevel Option
                    default:None

                createFileLevelIndex            -- Enable/Diable Metadata option
                     default:False

                backup_system_state             --  Enable/Disable system state option
                     default:None

                \*\*kwargs  (dict)              --  Optional arguments.

                Available kwargs Options:

                    software_compression(SoftwareCompression(Enum)) :   Software compression property for a subclient.
                    (ON_CLIENT/ON_MEDIA_AGENT/USE_STORAGE_POLICY_SETTINGS/OFF)

            Returns:
                None

            Raises:
                Exception - Any error occurred during Subclient Property update

        """
        try:
            if storage_policy is not None:
                self.fs_subclient.storage_policy = storage_policy
            if content is not None:
                self.fs_subclient.content = content
            if filter_content is not None:
                self.fs_subclient.filter_content = filter_content
            if exception_content is not None:
                self.fs_subclient.exception_content = exception_content
            if scan_type is not None:
                self.fs_subclient.scan_type = scan_type
            if trueup_option is not None:
                self.fs_subclient.trueup_option = trueup_option
            if trueup_days is not None:
                self.fs_subclient.trueup_days = trueup_days
            if data_readers is not None:
                if data_access_nodes is not None:
                    self.fs_subclient.data_readers = 2 * len(data_access_nodes)
                else:
                    self.fs_subclient.data_readers = data_readers
            if allow_multiple_readers is not None:
                if data_access_nodes is not None:
                    self.fs_subclient.allow_multiple_readers = True
                else:
                    self.fs_subclient.allow_multiple_readers = (
                        allow_multiple_readers)
            if read_buffer_size is not None:
                self.fs_subclient.read_buffer_size = read_buffer_size

            if block_level_backup is not None:
                self.fs_subclient.block_level_backup_option = block_level_backup
            if createFileLevelIndex is not False:
                self.fs_subclient.create_file_level_index_option = createFileLevelIndex

            if backup_system_state is not None:
                self.fs_subclient.system_state_option = backup_system_state

            if kwargs.get('software_compression', None):
                self.fs_subclient.software_compression = kwargs.get('software_compression')

        except Exception as excp:
            self.log.error('Subclient Update Failed with error: %s', str(excp))
            raise Exception('Subclient Update Failed with error: {0}'.format(str(excp)))

    def cleanup(self):
        """This method will remove temp data which is generated/stored during automation run.
        This method doesn't remove TinyDB database. That database is purged before a new run.
        Directory paths are fetched from Cloud Apps constants file.
        """
        try:
            if os.path.exists(constants.GMAIL_DOCUMENT_DIRECTORY):
                shutil.rmtree(constants.GMAIL_DOCUMENT_DIRECTORY)
                self.log.info(
                    'Documents directory %s was deleted successfully',
                    constants.GMAIL_DOCUMENT_DIRECTORY)
            if os.path.exists(constants.GDRIVE_DOCUMENT_DIRECTORY):
                shutil.rmtree(constants.GDRIVE_DOCUMENT_DIRECTORY)
                self.log.info(
                    'Documents directory %s was deleted successfully',
                    constants.GDRIVE_DOCUMENT_DIRECTORY)
            if os.path.exists(constants.ONEDRIVE_DOCUMENT_DIRECTORY):
                shutil.rmtree(constants.ONEDRIVE_DOCUMENT_DIRECTORY)
                self.log.info(
                    'Documents directory %s was deleted successfully',
                    constants.ONEDRIVE_DOCUMENT_DIRECTORY)
            if os.path.exists(constants.DOWNLOAD_DIRECTORY):
                shutil.rmtree(constants.DOWNLOAD_DIRECTORY)
                self.log.info(
                    'Downloads directory %s was deleted successfully',
                    constants.DOWNLOAD_DIRECTORY)
            if os.path.exists(constants.ONEDRIVE_DOWNLOAD_DIRECTORY):
                shutil.rmtree(constants.ONEDRIVE_DOWNLOAD_DIRECTORY)
                self.log.info(
                    'Downloads directory %s was deleted successfully',
                    constants.ONEDRIVE_DOWNLOAD_DIRECTORY)
        except Exception:
            self.log.exception('Could not delete documents directory. Delete it manually.')

    def verify_discover(self):
        """Method to verify user discovery"""
        try:
            users = self.tc_object.subclient.discover()
            user_list = []

            for user in users:
                user_list.append(user['contentName'])
            self.log.info('No of users by subclient discovery: %s', len(user_list))
            google_users = self.cc_object.gadmin.users
            self.log.info('No of user by Google discovery: %s',
                          len(self.cc_object.gadmin.users))
            if not user_list == google_users:
                self.log.error('user discovery is not matching.')
                raise CVCloudException(self.app_name, '905')
        except Exception as excp:
            self.log.exception('Exception during discovery verification')
            raise CVCloudException(self.app_name, '906', str(excp))

    def get_backup_files(self):
        """Method to browse the subclient and gets the number of backup files of a onedrive user

           Returns:
               List of files that got backup (str)
        """
        backup_items_list = []
        try:
            user_id = None
            sc_content = self.tc_object.subclient.content

            for content in sc_content:
                user_id = content.get('SMTPAddress')
            backup_files = self.tc_object.subclient.browse(path='\\OneDrive\\{0}\\My Drive\\{1}'
                                                           .format(user_id, constants.ONEDRIVE_FOLDER))
            backup_files = backup_files[0]
            if backup_files:
                for file in backup_files:
                    file = file.rsplit('\\', 1)[1]
                    backup_items_list.append(file)
                self.log.info('number of backup files : [%s]', len(backup_items_list))
                return backup_items_list

        except Exception as excp:
            self.log.exception('Exception while getting Backup Items')
            raise CVCloudException(self.app_name, '908', str(excp))

    def get_number_of_failed_items(self, job_id):
        """Method to get number of failed items from the job.
                Returns the number of failed items (files + folders)

            Args:
                job_id    --  backup Job object

            Returns:
                Number of failed items from the job

        """
        number_of_failed_items = 0
        try:
            details = job_id._get_job_details()
            failure = details['jobDetail']['detailInfo']['failures']
            if failure:
                for i, w in enumerate(failure.split()):
                    if i % 2 == 0:
                        number_of_failed_items += int(w)
                self.log.info('number of failed files : [%s]', number_of_failed_items)
                return number_of_failed_items

        except Exception as excp:
            self.log.exception('Exception while getting Number of Failed Items')
            raise CVCloudException(self.app_name, '907', str(excp))

    def get_number_of_successful_items(self, job):
        """ Method to get number of items successful in a backup job

            Args:
                job (object)        --  backup job object

            Returns:
                backup_count (int)  -- number of items successful
        """
        try:
            details = job._get_job_details()
            backup_count = details['jobDetail']['detailInfo']['numOfObjects']
            return int(backup_count)
        except Exception as exception:
            self.log.exception('Exception while getting Number of successful items in a backup job')
            raise CVCloudException(self.app_name, '908', str(exception))

    def check_playback_completion(self, job_id):
        """Checks whether playback for the job is completed or not

             Args:
                job_id (int)    --  id of backup job
            Raises:
                Exception       --  When playback results in failure
        """
        try:
            self.log.info("Check whether play back for the job is completed successfully or not")
            solr = CVSolr(self.cc_object)
            solr.check_all_items_played_successfully(job_id)
        except Exception as exception:
            self.log.exception(f"An error occurred while checking completion of play back for the job {job_id}")
            raise exception

    def wait_for_ci_job(self):
        """
        Get latest completed/running Content Indexing job of the client
        Operation Code (opType) for Content Indexing is 113
        """
        ci_job = self.subclient.find_latest_job(job_filter=JobOpCode.CONTENT_INDEXING_OPCODE.value)
        try:
            job_manager = JobManager(_job=ci_job, commcell=self.commcell)
            return job_manager.wait_for_state('completed')
        except Exception:
            return False

    def validate_ci_job(self, job_id):
        """Validate CI job
            Args:
                job_id(int)  -- job id of backup job

            Returns:
                int     -- Count of content indexed items
        """
        self.log.info("Validating CI Job")
        self.cvSolr = CVSolr(self.cc_object)
        solr_results = self.cvSolr.create_url_and_get_response(
            {cs.FIELD_JOB_ID: job_id, cs.DOCUMENT_TYPE_PARAM: '1', cs.CONTENT_INDEXING_STATUS: '1'})
        return int(self.cvSolr.get_count_from_json(solr_results.content))

    def get_job_results_dir(self):
        """
        Get the full job results directory
        Note: Make sure Test case object is initialized with client and subclient objects
              before calling this function
        """
        base_path = self.tc_object.client.job_results_directory

        if not base_path:
            proxy_client = self.commcell.clients.get(self.tc_object.tcinputs['AccessNode'])
            base_path = proxy_client.job_results_directory

        self.windows_machine = Machine(self.tc_object.tcinputs['AccessNode'], self.commcell)
        full_path = self.windows_machine.join_path(base_path, "CV_JobResults", "iDataAgent",
                                                   "Cloud Apps Agent",
                                                   str(self.commcell.commcell_id),
                                                   str(self.tc_object.subclient.subclient_id))

        self.log.info("Job results dir: %s", full_path)
        return full_path
        
    def update_user_associations(self, users_list, operation, office_365_plan_id=None):
        """
        Include, Exclude, Remove and associate users in subclient

        Args:

            users_list (list)      --      list of users whose association to be edited

            operation (int)         --      type of operation to be performed
                                                Example: 1 - Associate
                                                         2 - Enable
                                                         3 - Disable
                                                         4 - Remove

            office_365_plan_id (int)           --    id of office 365 plan
        """
        try:
            user_account_info = []
            for user in users_list:
                user_account_info.extend(self.tc_object.subclient._get_user_details(user))
            if office_365_plan_id:
                self.tc_object.subclient.update_users_association_properties(
                    user_accounts_list=user_account_info,
                    operation=operation,
                    plan_id=office_365_plan_id)
            else:
                self.tc_object.subclient.update_users_association_properties(
                    user_accounts_list=user_account_info,
                    operation=operation)

            user_dict, no_of_records = self.tc_object.subclient.browse_for_content(discovery_type=1)
            users_list = [user['smtpAddress'] for user in user_account_info]
            associated_users_list = list(user_dict.keys())

            if operation == 1:
                for user in users_list:
                    if user in associated_users_list:
                        self.log.info(f"{user} user is associated for backup")
                    else:
                        self.log.exception(f"{user} user is not associated for backup as expected")
                        raise Exception(f"{user} user is not associated for backup as expected")
            elif operation == 2:
                for user in users_list:
                    if user_dict[user]['accountStatus'] == 0:
                        self.log.info(f"{user} user is enabled for backup")
                    else:
                        self.log.exception(f"{user} user is not enabled for backup as expected")
                        raise Exception(f"{user} user is not enabled for backup as expected")
            elif operation == 3:
                for user in users_list:
                    if user_dict[user]['accountStatus'] == 2:
                        self.log.info(f"{user} user is disabled for backup")
                    else:
                        self.log.exception(f"{user} user is not disabled for backup as expected")
                        raise Exception(f"{user} user is not disabled for backup as expected")
            elif operation == 4:
                for user in users_list:
                    if user in associated_users_list:
                        self.log.exception(f"{user} user is not removed from backup content as expected")
                        raise Exception(f"{user} user is not removed from backup content as expected")
                    else:
                        self.log.info(f"{user} user is removed from backup content")

        except Exception as exception:
            self.log.exception("Exception while removing users from backup content: %s", str(exception))
            raise exception

    def update_group_associations(self, groups_list, operation, office_365_plan_id=None):
        """
        Include, Exclude, Remove and associate groups in subclient

        Args:

            groups_list (list)      --      list of groups whose association to be edited

            operation (int)         --      type of operation to be performed
                                                Example: 1 - Associate
                                                         2 - Enable
                                                         3 - Disable
                                                         4 - Remove

            office_365_plan_id (int)           --    id of office 365 plan
        """
        try:
            groups_info = []
            for group in groups_list:
                groups_info.extend(self.tc_object.subclient._get_group_details(group))
            if office_365_plan_id:
                self.tc_object.subclient.update_users_association_properties(
                    groups_list=groups_info,
                    operation=operation,
                    plan_id=office_365_plan_id
                )
            else:
                self.tc_object.subclient.update_users_association_properties(
                    groups_list=groups_info,
                    operation=operation)

            group_dict, no_of_records = self.tc_object.subclient.browse_for_content(discovery_type=2)
            groups_list = [group['name'] for group in groups_info]
            associated_groups_list = list(group_dict.keys())

            if operation == 1:
                for group in groups_list:
                    if group in associated_groups_list:
                        self.log.info(f"{group} group is associated for backup")
                    else:
                        self.log.exception(f"{group} group is not associated for backup as expected")
                        raise Exception(f"{group} group is not associated for backup as expected")
            elif operation == 2:
                for group in groups_list:
                    if group_dict[group]['accountStatus'] == 0:
                        self.log.info(f"{group} group is enabled for backup")
                    else:
                        self.log.exception(f"{group} group is not enabled for backup as expected")
                        raise Exception(f"{group} group is not enabled for backup as expected")
            elif operation == 3:
                for group in groups_list:
                    if group_dict[group]['accountStatus'] == 2:
                        self.log.info(f"{group} group is disabled for backup")
                    else:
                        self.log.exception(f"{group} group is not disabled for backup as expected")
                        raise Exception(f"{group} group is not disabled for backup as expected")
            elif operation == 4:
                for group in groups_list:
                    if group in associated_groups_list:
                        self.log.exception(f"{group} group is not removed from backup as expected")
                        raise Exception(f"{group} group is not removed from backup as expected")
                    else:
                        self.log.info(f"{group} group is removed for backup")

        except Exception as exception:
            self.log.exception("Exception while removing users from backup content: %s", str(exception))
            raise exception

    def update_custom_category_associations(self, custom_category, operation):
        """
        Include, Exclude and  Remove custom groups in subclient

        Args:

            custom_category (str)      --      name of custom group whose association to be edited

            operation (int)         --      type of operation to be performed
                                                Example: 0 - Enable
                                                         1 - Remove
                                                         2 - Disable
        """
        try:
            self.tc_object.subclient.update_custom_categories_association_properties(category_name=custom_category,
                                                                                     operation=operation)

            group_dict, no_of_records = self.tc_object.subclient.browse_for_content(discovery_type=31)
            associated_groups_list = list(group_dict.keys())

            if operation == 0:
                if group_dict[custom_category]['accountStatus'] == 0:
                    self.log.info(f"{custom_category} group is enabled for backup")
                else:
                    self.log.exception(f"{custom_category} group is not enabled for backup as expected")
                    raise Exception(f"{custom_category} group is not enabled for backup as expected")

            elif operation == 1:
                if custom_category in associated_groups_list:
                    self.log.exception(f"{custom_category} group is not removed from backup as expected")
                    raise Exception(f"{custom_category} group is not removed from backup as expected")
                else:
                    self.log.info(f"{custom_category} group is removed for backup")

            elif operation == 2:
                if group_dict[custom_category]['accountStatus'] == 2:
                    self.log.info(f"{custom_category} group is disabled for backup")
                else:
                    self.log.exception(f"{custom_category} group is not disabled for backup as expected")
                    raise Exception(f"{custom_category} group is not disabled for backup as expected")

        except Exception as exception:
            self.log.exception("Exception while editing custom category association from backup content: %s", str(exception))
            raise CVCloudException(self.app_name, '909', str(exception))
