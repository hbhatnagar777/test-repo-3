# -*- coding: utf-8 -*-
# pylint: disable=W1202

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing DR operations

DRHelper is the only class defined in this file

DRHelper: Helper class to perform DR operations

DRHelper:

    __init__()                      --  initializes DR helper object

    killrunningdrjobs               --  Kills already running DR jobs

    trigger_dr_backup               --  triggers DR backup job

    create_script                   --  creates batch file on windows or shell file on unix.

    check_entity_existence          --  checks the exitence of the entity on the commcell.

    create_dr_entities              --  creates disk library and dr storage policy.

    dr_entities_cleanup             --  removes the disklibrary and dr policy created by create_dr_entities method

    restore_db_with_csrecovery_assistant    --  restores databases using CSRecoveryAssistant tool

    download_from_cvcloud           --   downloads the set folder from cvcloud.

    download_from_third_party_cloud --  downloads given set folder from third party cloud.

    get_latest_folder_network_dr_path -- Get the Latest DR Folder from a network DR Path

    get_cs_dump_in_path		        -- Gets the CS Dump from a given Path

    set_er_directory                -- Sets the ER Staging Directory for the provided Path
"""

import re
import time
from cvpysdk.disasterrecovery import DisasterRecovery
from cvpysdk.storage import DiskLibraries, DiskLibrary
from cvpysdk.policies.storage_policies import StoragePolicies, StoragePolicy
from cvpysdk.backupset import Backupsets, Backupset
from cvpysdk.subclient import Subclients, Subclient
from cvpysdk.job import Job
from cvpysdk.client import Client
from Server.JobManager.jobmanager_helper import JobManager
from Server.DisasterRecovery.drmanagement_helper import DRManagementHelper
from AutomationUtils.machine import Machine
from AutomationUtils import logger, config
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from AutomationUtils.constants import WINDOWS_TMP_DIR, UNIX_TMP_DIR
from MediaAgents.mediaagentconstants import CLOUD_SERVER_TYPES


class DRHelper(object):
    """Helper class to perform DR operations"""

    def __init__(self, commcell_object):
        """
        Initializes instance of the DRHelper class

            Args:
                commcell_object     (object)        --      commcell object

            NOTE:
                cs_machine_uname and cs_machine_password are required for performing CS Recovery operations.
                which can be provided in config.json under 'Schedule' key

        """
        self.log = logger.get_log()
        self._commcell = commcell_object
        self.dr = DisasterRecovery(self._commcell)
        self.management = DRManagementHelper(self._commcell)
        self.util = OptionsSelector(self._commcell)
        self.job_manager = JobManager(commcell=self._commcell)
        self.csclient = Client(self._commcell, self._commcell.commserv_name)
        self.config_json = config.get_config()
        if self.config_json.Schedule.cs_machine_uname:
            self.client_machine = Machine(self._commcell.commserv_client.client_hostname,
                                          username=self.config_json.Schedule.cs_machine_uname,
                                          password=self.config_json.Schedule.cs_machine_password)
        else:
            self.client_machine = Machine(self.csclient)
        self.dr_entities = CVEntities(self._commcell)
        self.install_path = self.csclient.install_directory
        self._dr_path = self.management.backup_metadata_folder

    def trigger_dr_backup(self, backup_type='full', compression=True, exclude_dbs=None, client_list=None,
                          advance_job_options=None, wait_for_completion=True):
        """
        Triggers a disaster recovery backup.

            Args:
                 backup_type     (str)       --          type of the backup to trigger.
                    default: 'full'

                    values:

                    "full"
                    "differential"

                compression     (bool)      --          True/False, compression to be enabled or not
                    default: True

                exclude_dbs     (list)      --          databases to be excluded during DR backup.
                    default: None

                    values:

                    'appstudio'
                    'history'
                    'cvcloud'
                    'workflow'
                    'dm2'

                client_list     (list)      --          log of the clients that need to be backed up.
                    default: None

                advance_job_options     (dict)  --      advance job options to be included.

                    values:

                    {
                        "priority": 66,
                        "start_in_suspended_state": False,
                        "start_when_activity_is_low": False,
                        "use_default_priority": True,
                        "enable_total_running_time": False,
                        "total_running_time": 3600,
                        "enable_number_of_retries": False,
                        "kill_running_job_when_total_running_time_expires": False,
                        "number_of_retries": 0,
                        "job_description": ""
                    }

                 wait_for_completion     (bool)  --      waits for the completion of the job.

            Returns:
                job object

            Raises:
                Exception:
                    when job doesn't reach expected state.
                """
        if exclude_dbs or client_list or advance_job_options:
            self.dr.advbackup = True
            if client_list is not None:
                self.dr.client_list = client_list
            self.dr.advanced_job_options = advance_job_options
            database_names = ['appstudio', 'history', 'cvcloud', 'workflow', 'dm2']
            if exclude_dbs:
                for db_name in exclude_dbs:
                    if db_name in database_names:
                        setattr(self.dr, 'is_' + db_name + '_db_enabled', False)
                    else:
                        raise Exception('Please pass the valid db names')
        self.dr.backup_type = backup_type
        self.dr.is_compression_enabled = compression
        self.log.info('Triggering a {0} dr backup'.format(backup_type))
        job_obj = self.dr.disaster_recovery_backup()
        self.job_manager.job = job_obj
        if wait_for_completion:
            self.job_manager.wait_for_state(expected_state=['completed', 'pending', 'completed w/ one or more errors'],
                                            retry_interval=120, time_limit=10)
            if self.job_manager.job.status.lower() in ['failed', 'pending', 'queued',
                                                       'completed w/ one or more errors']:
                raise Exception(
                    "job is in {0} state job id {1}, delay reason = {2}".format(
                        self.job_manager.job.status, self.job_manager.job.job_id, self.job_manager.job.delay_reason)
                )
        return job_obj

    def generate_path(self, machine_obj, alias='2', space_required=2048, create_path=False):
        """
        This function is to generate path for the DR backup.
        Args:
            machine_obj (Machine, optional) machine object to create path, default is self.client_machine_obj.
            alias (str, optional) alias name for the path, default is '2'.
            space_required (int, optional) minimum space requirement on client, default is 2048.
            create_path (bool, optional) create path on client, default is False.

        return:
            automation_path (str) generated path.
        """
        machine_drive = self.util.get_drive(machine_obj, int(space_required))
        automation_path = (machine_drive + 'automation_temp' + machine_obj.os_sep + alias +
                           '__' + time.strftime('%Y%m%d%H%M%S'))
        self.log.info(f"Generated path : {automation_path}")

        if create_path:
            machine_obj.create_directory(automation_path)

        return automation_path

    def delete_dr_folders(self, machine_obj, days=1, dr_path=None):
        """Cleanup function to delete the last run DR folders.

        Args:
            machine_obj (Machine): Machine object to perform the cleanup.
            days (int, optional): DR folders older than the given days will be cleaned up. Defaults to 1.
            dr_path (str, optional): DR path to perform the cleanup. Defaults to None.
        """
        if not dr_path:
            local_drive = self.util.get_drive(machine_obj, 2048)
            dr_path = local_drive + 'automation_temp' + machine_obj.os_sep
        self.log.info('Deleting the last run DR folders from : {0}'.format(dr_path))

        dirs = []
        try:
            dirs = machine_obj.get_folders_in_path(dr_path, recurse=False)
        except Exception as exc:
            self.log.error("Failed to get the DR folders: {0}".format(exc))
            self.log.info("Creating the directory {0}".format(dr_path))
            machine_obj.create_directory(dr_path)
        for dir_name in dirs:
            try:
                if self._dr_path != dir_name:
                    machine_obj.remove_directory(dir_name, days=days)
            except Exception as exc:
                self.log.error("Failed to delete the DR folders: {0}".format(exc))

    def kill_running_drjobs(self):
        """ Kill already running DR jobs"""
        try:
            self.log.info('Checking for running dr jobs')
            query = "select jobId from JMAdminJobInfoTable where opType = 11"
            jobs = self.util.exec_commserv_query(query)
            if jobs[0][0]:
                for job in jobs[1]:
                    self.log.info("DR job {0} is already running, kill and continue automation".format(job[0]))
                    try:
                        runningjob = Job(self._commcell, job[0])
                    except Exception as err:
                        self.log.error("Failed to create job object for"
                                       " job {0} and exception is {1}".format(job[0], err))
                    try:
                        runningjob.kill(True)
                    except Exception as err:
                        self.log.error(
                            "Failed to kill the job {} and exception is {} ".format(
                                job[0], err))
            else:
                self.log.info('there are no running dr jobs')
        except Exception as err:
            self.log.error("Failed to kill the job %s" % err)

    def create_script(self, content=''):
        """creates script with content passed, using machine class object.

        Args:
            content           (str)   --  content that is to be written to file

        Returns:
            path     (str)       --        Script path

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to create file
        """
        current_time = time.strftime('%Y-%m-%d-%H-%M-%S')
        if self.client_machine.os_info.lower() == 'windows':
            pre_scan_script = self.client_machine.join_path(
                WINDOWS_TMP_DIR,
                'temp' + current_time + ".bat")
        else:
            pre_scan_script = self.client_machine.join_path(
                UNIX_TMP_DIR,
                'temp' + current_time + ".sh")
        if self.client_machine.check_file_exists(pre_scan_script):
            self.log.info("deleting existing pre scan script {0}".format(pre_scan_script))
            self.client_machine.delete_file(pre_scan_script)
        self.log.info("creating pre scan command file {0}".format(pre_scan_script))
        self.client_machine.create_file(pre_scan_script, content)
        if self.client_machine.os_info.lower() == "unix":
            self.client_machine.change_file_permissions(pre_scan_script, '777')
        return pre_scan_script

    def check_entity_existence(self, entity_type, entity_object, hardcheck=True):
        """
        checks the existence of the entity on commcell.

            Args:
                entity_type     (str)      --           type of the entity

                values:
                'policy'
                'library'
                'backupset'
                'subclient'

                entity_object       (object/str)    --      object or name of the entity to be checked.

                hardcheck           (bool)          --      True/False, To raise exception or To return bool value

            Returns:
                 bool

            Raises:
                Exception:
                    when invalid arguments are passed

                    when hardcheck=true, and entity doesn't exist on the commcell

        """
        class_object = None
        if isinstance(entity_object, (DiskLibrary, StoragePolicy, Backupset, Subclient, str)):
            if isinstance(entity_object, DiskLibrary) or entity_type == 'library':
                class_object = DiskLibraries(self._commcell)
            elif isinstance(entity_object, StoragePolicy) or entity_type == 'policy':
                class_object = StoragePolicies(self._commcell)
            elif isinstance(entity_object, Backupset) or entity_type == 'backupset':
                class_object = Backupsets(self._commcell)
            elif isinstance(entity_object, Subclient) or entity_type == 'subclient':
                class_object = Subclients(self._commcell)
        else:
            raise Exception('please pass the valid arguments')
        class_object.refresh()
        if isinstance(entity_object, str):
            result = getattr(class_object, 'has_' + entity_type)(entity_object)
        else:
            result = getattr(class_object, 'has_' + entity_type)(entity_object.name)
        if not result:
            if hardcheck:
                raise Exception('{0} entity is not available'.format(entity_object))
            else:
                self.log.info('{0} entity is not available'.format(entity_object))
        return result

    def dr_prerequisites(self):
        """
         creates disklibrary and DR storage policy.

            Returns:
                dict   --  dictionary of disklibrary and DR storage policy

            Example:
                {
                "storagepolicy": DR_Policy,
                "disklib": DR_lib
                }

            Raises:
                Exception:
                    If the disklibary does not have enough free space.
                    if CommserveDR policy doesn't exist.
        """

        self.log.info('Checking for the existence of CommServeDR policy')
        if self.check_entity_existence('policy', StoragePolicy(
                self._commcell, storage_policy_name='CommServeDR'), hardcheck=False):
            DR_Policy = StoragePolicy(self._commcell, "CommServeDR")
            DR_lib = DiskLibrary(self._commcell, library_name=DR_Policy.library_name)
            free_space, unit = DR_lib.free_space.split()
            if unit.lower() == "tb" or (unit.lower() == 'gb' and float(free_space) > 5):
                return {
                    "storagepolicy": DR_Policy,
                    "disklib": DR_lib
                }
            else:
                raise Exception(f"The disklibary {DR_lib.name} does not have enough free space.")
        else:
            # Have to handle the scenario when there is no CommserveDR policy...
            raise Exception("CommserveDR policy doesn't exist")

    def dr_prerequisites_cleanup(self):
        """
        removes the disklibrary and dr storage policy which got created using dr_prerequisites() method.
        """
        self.log.info('Cleaning up created DR entities..')
        self.dr_entities.cleanup()

    def restore_db_with_csrecovery_assistant(self, dbdumplocation, operation="Staging",
                                             start_services_after_recovery=False, **options):
        """
        Restores CS using CSRecoveryAssistant.

            Args:
                 dbdumplocation     (str)       --      db dump location.

                 operation          (str)       --      type of the operation.

                    value:
                    'Staging'
                    'Recovery'

                start_services_after_recovery   (bool)  --  start the services post recovery or not.

                 options            (dict)      --      other additional parameters that can be passed
                                                        to CSRecovery tool
            Returns:
                None
            Raises:
                Exception:
                    if failed to restore the CS.
        """
        os_info = self.client_machine.os_info
        cmd = (self.install_path + '/Base/CSRecoveryAssistant.sh') if os_info == 'UNIX' \
            else 'CSRecoveryAssistant.exe'
        cmd = cmd + ' -operation %s ' % operation
        if 'skipdump' in options and options['skipdump'] is not None:
            cmd = cmd + '-skipdump '
        if dbdumplocation is not None:
            cmd = cmd + "-dbdumplocation %s" % dbdumplocation
        if 'dbfilelocation' in options and options['dbfilelocation'] is not None:
            cmd = cmd + "-dbfilelocation %s " % options['dbfilelocation']
        if 'licensepath' in options and options['licensepath'] is not None:
            cmd = cmd + "-license '%s' " % options['licensepath']
        if 'tononcluster' in options and options['tononcluster'] is not None:
            cmd = cmd + "-tononcluster "
        if 'tocluster' in options and options['tocluster'] is not None:
            cmd = cmd + "-tocluster "
        cmd = cmd + '\necho %errorlevel%'
        self.log.info("Command used for DB restore {}".format(cmd))
        script_path = self.create_script(content=cmd)
        self.log.info('Stopping and disabling the services on {0}'.format(self._commcell.commserv_name))
        if os_info == 'WINDOWS':
            stop_service_output = self.client_machine.execute_command(
                self.client_machine.join_path(self.install_path, "Base", "GxAdmin.exe").replace(
                    " ", "' '") + " -console -stopsvcgrp ALL -disable -timeout 400 -kill")
        elif os_info == 'UNIX':
            stop_service_output = self.client_machine.execute_command("commvault stop -all")

        if stop_service_output.exit_code != 0:
            raise Exception('failed to stop the services')
        self.log.info('waiting for the exit code of CSRecoveryAssistant...')
        csrecovery_output = self.client_machine.execute_command(script_path)
        if '\n1' in csrecovery_output.formatted_output or csrecovery_output.exit_code != 0:
            raise Exception("Error while restoring DataBases,"
                            "process returned exit code = {0},"
                            " cmd stdout = {1}".format(1, csrecovery_output.formatted_output))
        self.log.info("Successfuly Restored DB Files on CS")
        if start_services_after_recovery:
            self.log.info('starting the services on cs')
            if os_info == 'WINDOWS':
                output = self.client_machine.execute_command(
                    self.client_machine.join_path(
                        self.install_path, "Base", "GxAdmin.exe").replace(
                        " ", "' '") + " -console -startsvcgrp ALL -force 400")
            elif os_info == 'UNIX':
                output = self.client_machine.execute_command("commvault -all -force start")

            if str(output.output).find("fail") >= 0 or output.exit_code != 0:
                raise Exception("Services not started sucessfully, error %s" % str(output))
            self.log.info('Services started successfully')

    def download_from_third_party_cloud(self, vendor_name, loginname, password,
                                        mountpath, source_path, destination_path):
        """
        downloads given set folder from third party cloud.

            Args:
                vendor_name     (str)   --      name of the vendor

                    NOTE: please refer CLOUD_SERVER_TYPES in mediaagentconstants.py for supported vendor names

                loginname       (str)   --      login name

                password        (str)   --      password

                mountpath       (str)   --      name of the mountpath

                source_path     (str)   --      source_path
                    format: 'DR/<commcel_name>/<set_folder_name>'
                destination_path  (str) --      destination path for the download

            NOTE: please refer https://documentation.commvault.com/commvault/v11/article?p=97863.htm
                for more details on format of loginname, moutpath

            NOTE: Below functionality make use of CloudTestTool.exe which is under Base folder to download dumps
             from various cloud vendors

            Returns:
                None

            Raises:
                Exception:
                    when un-supported cloud vendor name is passed.
                    when destination directory is not found.
                    when format of loginName is incorrect
                    when failed to execute the download_cmd
        """
        if vendor_name in CLOUD_SERVER_TYPES:
            cloud_server_type = CLOUD_SERVER_TYPES.get(vendor_name)
        else:
            raise Exception('Please pass the valid cloud vendor name')
        if not self.client_machine.check_directory_exists(directory_path=destination_path):
            raise Exception('directory not found {0}'.format(destination_path))
        if vendor_name.lower() in ('amazon s3', 'google cloud storage'):
            cloud_creds = loginname.split('//')
            if len(cloud_creds) >= 2:
                download_cmd = self.client_machine.join_path(self.install_path, "Base", "CloudTestTool.exe").replace(
                    " ", "' '") + " -h {0} -u {1} -p {2} -b {3} -o download -S {4} -t {5} -D {6}".format(
                    cloud_creds[0], cloud_creds[1], password, mountpath, source_path, cloud_server_type,
                    destination_path)
            else:
                raise Exception('Please pass the valid format for loginname, hostname//accesskey')
        else:
            raise Exception('Please pass the valid cloud vendor name')
        self.log.info('Download cmd {0}'.format(download_cmd))
        download_cmd_output = self.client_machine.execute_command(download_cmd)
        if download_cmd_output.exit_code != 0:
            raise Exception('Failed with error = {0}'.format(download_cmd_output.formatted_output))
        else:
            self.log.info('Download successfull')

    def get_latest_folder_network_dr_path(self, local_mounted_path):
        """
        Method to get the latest DR folder from a mounted DR network Path

        Args:
            local_mounted_path  (str)   -- local Mounted path of network DR path

        Returns:
            The DR Folder Path if present or none
        """
        self.log.info("Getting the latest set folder in shared network path")
        sorted_script = "Get-ChildItem {0} | ? {{ $_.PSIsContainer }} | sort LastWriteTime | select Name".format(
            local_mounted_path)
        folder_output = self.client_machine.execute_command(sorted_script)
        output_list = list(map(lambda x: ' '.join(x), folder_output.formatted_output))
        output_list.reverse()
        for folder in output_list:
            if re.match(r"DR_[0-9]+$", folder):
                if not self.get_cs_dump_in_path(local_mounted_path + "\\" + folder):
                    continue
                return local_mounted_path + "\\" + folder

    def get_cs_dump_in_path(self, dr_folder):
        """
        Method to get the CS Dump in a given Folder Path

        Args:
        dr_folder   (str): DR Folder path from which CS Dump would be returned

        Returns:
            Commserver Dump name if present or None

        """
        files_present = self.client_machine.get_files_in_path(dr_folder)
        r = re.compile(r".*commserv_.*.dmp")
        return list(filter(r.match, files_present))

    def set_er_directory(self, path=None):
        """
        Sets the ER Staging Directory folder to the given path if provided else the default CommServeDR Location

        Args:
        path   (str): ER Staging Directory path to be set

        Returns:
            None
        """
        if not path:
            path = self.install_path + "\\CommserveDR"
        self.log.info("setting registry key ERStagingDirectory to CommserveDR location")
        self.client_machine.create_registry("CommServe", "ERStagingDirectory", path)
