# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file contains DR backup validation from Admin Console
Manage --> system --> maintenance --> DR backup

DRValidateHelper is the only class defined in this file

DRValidateHelper:
    __init__(test_object)                               --          initialize instance of the DRValidateHelper class.

    validate                                            --          entry point for all the testcases.

    __generate_path                                     --          to generate path for the DR backup.

    __kill_running_drjobs                               --          to kill already running DR jobs.

    __prereq                                            --          to set the default values for DR backup.

    __get_network_share                                 --          to get a new network share path in new directory.

    __remove_network_share                              --          to remove folder of network path.

    __wait_for_job_trigger                              --          to wait for DR Backup job to trigger.

    __delete_dr_folders                                 --          to delete the last run DR folders.

    __download_wait                                     --          to wait for download to complete.

    run_backup_job                                      --          to run a DR backup job.

    run_restore_job                                     --          to run a DR restore job.

    run_download_job                                    --          to run a DR download job.

    add_new_copy                                        --          to add a new copy to the CommServeDR Default Region.

    confirm_delete_model                                --          to confirm the delete operation.

    _get_retention_period                               --          to get retention period on copy from archAgingRule table for CommServeDR Plan.

    _get_copy_list                                      --          to get the list of copy for CommServeDR Plan.

    validate_backup_retain                              --          to validate no. of backup to get retained.

    validate_local_drive                                --          to validate local path of the drive for DR backup.

    validate_network_share                              --          to validate network path of the drive for DR backup.

    validate_backup_data_metallic_cloud                --          to validate backup data for commvault cloud option.

    validate_backup_data_cloud_library                  --          to validate backup data for 3rd party cloud library.

    validate_run_backup_job                             --          to validate a DR backup job.

    validate_restore                                    --          to validate a DR restore job.

    validate_download_job                               --          to validate a DR download job.

    validate_drbackup_schedule                          --          to validate a DR backup schedule.

    validate_drbackup_repeat_schedule                   --          to validate a DR backup repeat schedule.

    validate_backup_destinations                        --          to validate backup destinations.

    validate_backup_destinations_regions                --          to validate backup destinations regions table.

    validate_dr_copy_details                            --          to validate DR copy details.

    validate_delete_copy                                --          to validate delete of a copy from the CommServeDR default Region.

    delete_dr_job                                       --          to validate delete of a DR job from the Backup Destinations Copy.

"""
import time
import zipfile

from cvpysdk.commcell import Commcell
from cvpysdk.client import Client
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.alert import Alert
from cvpysdk.disasterrecovery import DisasterRecoveryManagement
from AutomationUtils.machine import Machine
from AutomationUtils import logger, options_selector
from cvpysdk.job import Job
from AutomationUtils.idautils import CommonUtils
from Web.AdminConsole.AdminConsolePages.maintenance import DRBackupDaily
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from cvpysdk.storage import DiskLibraries
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService


class DRValidateHelper(object):
    """This class performs all the web based UI operation task on DR backup (Daily) page."""

    def __init__(self, admin_console: AdminConsole, commcell: Commcell, client_name: Commcell =None):
        self.log = logger.get_log()
        self.management = DisasterRecoveryManagement(commcell)
        self.client_machine_obj = Machine(client_name, commcell_object=commcell)
        self.common_utils = CommonUtils(commcell)
        self.commcell = commcell
        self.job_manager = self.common_utils.job_manager
        self.__drbackup_daily = DRBackupDaily(admin_console)
        self._util = options_selector.OptionsSelector(commcell)
        self._jobs = Jobs(admin_console)
        self._disk_libraries = DiskLibraries(self.commcell)
        self._admin_console = admin_console
        self._panel_info = RPanelInfo(admin_console)
        self._local_machine_obj = Machine()
        self._table = Rtable(admin_console)
        self._browse = RBrowse(admin_console)
        self._dr_path = self.management.backup_metadata_folder
        self.__delete_dr_folders()
        self._secondary_copy = 'copy'
        self._primary_copy = 'Primary'
        self._storage_pool = None

    def validate(self, test_list: dict):
        """This function is the entry point for all the testcases

        Args:
            test_list (dict, optional): set of all the tests.
        """
        self.__prereq()
        for tests in test_list:
            if tests == 'backup_retain':
                self.log.info('Checking for Number of Backup retain.')
                self.validate_backup_retain(val=1)

            elif tests == 'network_share':
                self.log.info('Checking for Network Share.')
                if 'windows' in self.commcell.commserv_client.os_info.lower():
                    self.validate_network_share(share_password=test_list["network_share"]["password"],
                                                username=test_list["network_share"]["username"],
                                                hostname=test_list["network_share"]["hostname"])
                else:
                    self.log.info(
                        'Network share is not supported for {0}'.format(self.commcell.commserv_client.os_info))

            elif tests == 'local_drive':
                self.log.info('Checking for Local drive path.')
                self.validate_local_drive(
                    path=self.__generate_path(alias='local_drive'))

            elif tests == 'validate_run_DRBackup':
                self.log.info('Validating run DRBackup.')
                self.validate_run_backup_job(job_types=test_list["validate_run_DRBackup"]["job_types"])

            elif tests == 'validate_dbbackup_restore':
                self.log.info('Validating restore DRBackup.')
                self.__prereq()
                self.validate_restore()

            elif tests == 'validate_drbackup_upload_metallic_cloud':
                self.log.info('Validating DRBackup to Metallic Cloud.')
                self.validate_backup_data_metallic_cloud(turn_on=True)

            elif tests == 'validate_drbackup_upload_third_party_cloud':
                self.log.info('Validating DRBackup to Third Party Cloud.')
                cloud_library_name = test_list["validate_drbackup_upload_third_party_cloud"]["CloudLibraryName"]
                self.validate_backup_data_cloud_library(cloud_library_name=cloud_library_name, turn_on=True)

            elif tests == 'validate_drbackup_download':
                self.log.info('Validating DRBackup download.')
                self.__prereq()
                download_path = test_list["validate_drbackup_download"]["download_path"]
                download_filenames = test_list["validate_drbackup_download"]["download_filenames"]
                self.validate_download_job(download_path, download_filenames)

            elif tests == 'validate_drbackup_schedule':
                self.log.info('Validating DRBackup schedule.')
                self.validate_drbackup_schedule()

            elif tests == 'validate_drbackup_repeat_schedule':
                self.log.info('Validating DRBackup repeat schedule.')
                self.__prereq()
                self.validate_drbackup_repeat_schedule()
            elif tests == 'validate_backup_destinations':
                self.log.info('Validating Backup Destinations.')
                self._storage_pool = test_list["validate_backup_destinations"]["storage_pool"]
                self.validate_backup_destinations()
        self.__prereq()

    def __generate_path(self, alias: str='2', space_required: int=2048, machine_obj: Machine=None) -> str:
        """
        This function is to generate path for the DR backup.
        Args:
            alias (str, optional) alias name for the path, default is '2'.
            space_required (int, optional) minimum space requirement on client, default is 2048.
            machine_obj (Machine, optional) machine object to create path, default is self.client_machine_obj.

        return:
            automation_path (str) generated path.
        """
        if not machine_obj:
            machine_obj = self.client_machine_obj
        machine_drive = self._util.get_drive(machine_obj, int(space_required))
        automation_path = machine_drive + 'temp' + machine_obj.os_sep + alias + '__' + time.strftime('%Y%m%d%H%M%S')
        machine_obj.create_directory(automation_path)

        self.log.info(f"Generated path : {automation_path}")

        return automation_path

    def __kill_running_drjobs(self):
        """ Kill already running DR jobs."""
        try:
            self.log.info('Checking for running dr jobs')
            query = "select jobId from JMAdminJobInfoTable where opType = 11"
            jobs = self._util.exec_commserv_query(query)
            if jobs[0][0]:
                for job in jobs[1]:
                    self.log.info("DR job {0} is already running, kill and continue automation".format(job[0]))
                    try:
                        running_job = Job(self.commcell, job[0])
                        running_job.kill(True)
                    except Exception as err:
                        self.log.error(
                            "Failed to kill the job {0} and exception is {1} ".format(
                                job[0], err))
            else:
                self.log.info('there are no running dr jobs')
        except Exception as err:
            self.log.error("Failed to kill the job %s" % err)

    def __prereq(self):
        """This function is to set the default values for DR backup."""

        export_settings = {
            "retain": 2,
            "metallic": {
                "turn_on": False
            },
            "cloud_library": {
                "turn_on": False
            }
        }
        schedule_settings = {
            "daily_start_time": "12:00 PM",
            "repeat_schedule": {
                "enable": False
            }
        }
        self.__kill_running_drjobs()
        if not self._admin_console.is_element_present(locator='//*[@id="drBackup"]'):
            self._admin_console.navigator.navigate_to_maintenance()
            self.__drbackup_daily.access_dr_backup()
        self._admin_console.access_tab(self._admin_console.props['label.overview'])
        panel_details = self._panel_info.get_details()
        if 'Network share' in panel_details['Destination']:
            export_settings["local_drive"] = self.__generate_path(alias='local_drive')

        self.__drbackup_daily.edit(export_settings=export_settings, schedule_settings=schedule_settings)

    def __get_network_share(self, machine_obj: Machine) ->dict[str, str]:
        """this function created network share on client machines.

        Args:
            machine_obj (Machine): machine object on which network share to be created.

        Returns:
            dict: contains details about the share created.
                E.g.
                {
                    'path': '\\\\<machine_name>\\<dir_name>',
                    'dir_name': '<dir_name>'
                }
        """
        path = self.__generate_path(alias='share', machine_obj=machine_obj)
        base_path = path.split('\\')[-1]
        self.log.info('Sharing directory {0} on {1} machine'.format(path, machine_obj.machine_name))
        machine_obj.share_directory(share_name=base_path, directory=path)
        shared_path = '\\\\' + machine_obj.machine_name + '\\{0}'.format(base_path)
        self.log.info('Shared path is {0}'.format(shared_path))
        return {
            "path": shared_path,
            "dir_name": base_path,
            "local_path": path
        }

    def __remove_network_share(self, value: dict, machine_obj: Machine):
        """Used to remove the shared folder.

        Args:
            value (dict): details about the shared path.
            machine_obj (Machine): machine object on which network share to be removed.
                E.g.
                {
                    'path': '\\\\<machine_name>\\<dir_name>',
                    'dir_name': '<dir_name>'
                }
        """
        self.log.info('Removing shared directory {0} on {1} machine'.format(value['path'],
                                                                            machine_obj.machine_name))
        machine_obj.unshare_directory(share_name=value['dir_name'])
        machine_obj.remove_directory(directory_name=value['local_path'])

    def __wait_for_job_trigger(self, max_wait_time:float) -> int:
        """To wait for DR Backup job to trigger.

        Args:
            max_wait_time (float): maximum time to wait for job to trigger.

        Raises:
            Exception: If job failed to trigger.

        Returns:
            int: job id of the triggered job.
        """
        self.log.info("Waiting for DR backup job to trigger..")
        self.log.info('Checking for running dr jobs')
        query = "select jobId from JMAdminJobInfoTable where opType = 11"
        jobs = self._util.exec_commserv_query(query)
        while time.time() < max_wait_time and jobs[0][0] == '':
            time.sleep(30)
            self.log.info('Checking for running dr jobs')
            jobs = self._util.exec_commserv_query(query)
        if not jobs[0][0]:
            raise Exception('Expected DR backup job is not running')
        self.log.info('Job is triggered successfully with jobid: {0}'.format(jobs[0][0]))
        return jobs[0][0]

    def __delete_dr_folders(self, days: int=1):
        """To delete the last run DR folders.

        Args:
            days (int, optional): DR folders older than the given days will be cleaned up. Defaults to 1.
        """
        self.log.info('Deleting the last run DR folders..')
        machine_drive = self._util.get_drive(self.client_machine_obj, 2048)
        dr_path = machine_drive + 'temp' + self.client_machine_obj.os_sep
        try:
            dirs = self.client_machine_obj.get_folders_in_path(dr_path, recurse=False)
            for dir_name in dirs:
                if self._dr_path != dir_name:
                    self.client_machine_obj.remove_directory(dir_name, days=days)
        except Exception as err:
            self.log.error("Failed to delete the DR folders: {0}".format(err))

    def __download_wait(self, path_to_downloads: str, timeout: int=3 * 60):
        """To wait for download to complete.

        Args:
            path_to_downloads (str): path to download location of browser.
            timeout (int, optional): timeout in seconds. Defaults to 3 Minutes.
        """
        self.log.info('Waiting for download to complete..')
        timeout_time = time.time() + timeout
        dl_wait = True
        while dl_wait and timeout_time > time.time():
            time.sleep(5)
            dl_wait = False
            for name in self._local_machine_obj.get_files_in_path(path_to_downloads):
                if '.crdownload' in name:
                    dl_wait = True

    @PageService()
    def run_backup_job(self, job_type: str='full') -> int:
        """This function is used for running DR backup job.

        Args:
            job_type (str) -- type of backup job to run. 'full' or 'diff', Default is 'full'

        Return:
            backup_jobid (int) returns the id of backup job

        Raises:
            Exception: if invalid job type is provided
        """
        self._admin_console.click_button(self._admin_console.props['action.run'])
        if job_type == 'full':
            self._admin_console.select_radio(value='FULL')
        elif job_type == 'Differential':
            self._admin_console.select_radio(value='DIFFERENTIAL')
        else:
            raise CVWebAutomationException('Invalid job type')
        self._admin_console.click_button(self._admin_console.props['action.runJob'], wait_for_completion=False)
        backup_jobid = self._admin_console.get_jobid_from_popup(wait_time=120)
        return backup_jobid

    @PageService()
    def run_restore_job(self, backup_jobid: str, restore_destination: str):
        """This function is used for running DR restore job.

        Args:
            backup_jobid (int) -- backup job, to be restored
            restore_destination (str) -- destination path to restore the DR backup

        Return:
            restore_job_id (int) returns the id of restore job

        """
        self._jobs.job_completion(backup_jobid, skip_job_details=True, timeout=10 * 60)
        self._admin_console.navigator.navigate_to_maintenance()
        self.__drbackup_daily.access_dr_backup()
        self._admin_console.click_button(self._admin_console.props['action.restore'])
        self._table.access_link(backup_jobid)

        self._admin_console.click_button(self._admin_console.props['action.restore'])

        self._browse.select_files(select_all=True)
        self._admin_console.click_button(self._admin_console.props['action.restore'])

        self._admin_console.fill_form_by_id("destinationPathdestinationPathInput", value=restore_destination)
        self._admin_console.submit_form()

        restore_job_id = self._admin_console.get_jobid_from_popup(wait_time=120)
        return restore_job_id

    @PageService()
    def run_download_job(self, backup_jobid: str, download_file_names: list[str]):
        """This function is used for running DR download job.

        Args:
            backup_jobid (int) -- backup job id
            download_file_names (List(str)) -- list of name of the file to download. Example
                ['Mongo_GlobalConfigManager', 'CacheDB', 'Mongo_GCMTracking']
        """
        self._jobs.job_completion(backup_jobid, skip_job_details=True, timeout=5 * 60)
        self._admin_console.navigator.navigate_to_maintenance()
        self.__drbackup_daily.access_dr_backup()
        self._admin_console.click_button(self._admin_console.props['action.restore'])
        self._table.access_link(backup_jobid)
        self._admin_console.click_button(self._admin_console.props['action.restore'])

        folder_name = 'DR_' + str(backup_jobid)
        self.log.info(f"Selecting files from: {folder_name}")
        self._browse.set_search_string(folder_name, {"include_folders": {'enable': True}})
        self._browse.access_folder(folder_name)
        self._browse.select_files(file_folders=download_file_names, partial_selection=True)
        self._admin_console.click_button(self._admin_console.props['action.commonAction.download'])

    def add_new_copy(self):
        """This function is used to add a new copy to the CommServeDR Default Region"""
        additional_storage = {'storage_name': self._secondary_copy,
                              'storage_pool': self._storage_pool}
        PlanDetails(self._admin_console).edit_server_plan_storage_pool(additional_storage, {}, False)

    def confirm_delete_model(self) -> str:
        """This function is used to confirm the delete operation

        Returns:
            str -- message after the confirmation of dialog
        """
        confirm_dialog = RModalDialog(self._admin_console, 'Confirm')
        delete_alert = Alert(self._admin_console)
        confirm_dialog.fill_text_in_field('confirmText', 'Delete')
        confirm_dialog.select_checkbox('onReviewConfirmCheck')
        confirm_dialog.click_submit(wait=False)
        delete_job_dialog = RModalDialog(self._admin_console, 'Delete job')
        if delete_job_dialog.is_dialog_present():
            delete_job_dialog.click_submit(wait=False)
        message = delete_alert.get_content()
        return message

    def _get_retention_period(self, copy_name: str) -> str:
        """
        To get retention period on copy from archAgingRule table for CommServeDR Plan
        Args:
             copy_name (str) -- Name of the copy

        Returns:
            int    --  retention days set on the copy
        """

        query = f"""SELECT	AGR.retentionDays
                    FROM	archAgingRule AGR
                    JOIN	archGroupCopy AGC
                            ON     AGR.copyId = AGC.id
                    JOIN	archGroup AG
                            ON     AGC.archGroupId = AG.id
                    WHERE	AG.name = 'CommServeDR'
                    AND     AGC.name = '{copy_name}'"""
        self.log.info("QUERY: %s", query)
        _, cur = self._util.exec_commserv_query(query)
        self.log.info("RESULT: %s", cur[0])
        if cur[0][0] != '':
            return cur[0][0]
        raise Exception("Unable to fetch retention period")

    def _get_copy_list(self) -> list[str]:
        """To get the list of copy for CommServeDR Plan

        Returns:
            List[str]    --  list of copy names
        """
        query = f"""
        SELECT AGC.name
        FROM archGroupCopy AGC
        JOIN archGroup AG
        ON AGC.archGroupId = AG.id
        WHERE AG.name = 'CommServeDR'"""

        self.log.info("QUERY: %s", query)
        _, copy_list = self._util.exec_commserv_query(query)
        if copy_list[0][0]:
            flat_copy_list = [item for sublist in copy_list for item in sublist]
            return flat_copy_list
        raise Exception("Unable to fetch copy list")

    def validate_backup_retain(self, val: int):
        """This function is to validate the number of DR backup metadata to retain.

        Args:
            val (int): No. of DR backup metadata to retain

        Raises:
            CVWebAutomationException: If the value is not set as the number of metadata
        """
        export_settings = {
            "retain": val
        }

        self.__drbackup_daily.edit(export_settings=export_settings)
        self.log.info("Sleep for 10 sec for data to get written on DB")
        time.sleep(10)
        panel_details = self._panel_info.get_details()
        self.management.refresh()
        if self.management.number_of_metadata != val and panel_details['Number of DR backups to retain'] != val:
            raise CVWebAutomationException(
                'The value {0} is not set as the number of metadata'.format(val))
        else:
            self.log.info('Backup retain feature is validated successfully.')

    def validate_local_drive(self, path):
        """This function is to validate the local path as destination for DR backup metadata.

        Args:
            path (str): valid local path for DR backup metadata destination

        Raises:
            CVWebAutomationException: If path set from UI doesn't match from backend
        """
        export_settings = {
            "local_drive": path
        }
        self.__drbackup_daily.edit(export_settings=export_settings)
        self.log.info("Sleep for 10 sec for data to get written on DB")
        time.sleep(10)
        panel_details = self._panel_info.get_details()
        self.management.refresh()
        if (self.management.backup_metadata_folder != path and
                panel_details['Destination'] == 'Local drive [{0}]'.format(path)):
            raise CVWebAutomationException(
                'Path {0} not set as local value of DR backup'.format(path))
        else:
            self.log.info('Local drive feature is validated successfully.')

    def validate_network_share(self, share_password: str, username: str, hostname: str):
        """This function is to validate the network share as DR backup metadata.

        Args:
            share_password (str): password for the network share.
            username (str): username for the network share.
            hostname (str): hostname of the machine.

        Raises:
            CVWebAutomationException: If path set from UI doesn't match from backend.
        """
        machine_obj = Machine(hostname, username=username, password=share_password)
        self.log.info('Checking for Network Share on ''{0}'.format(machine_obj.machine_name))

        network_path = self.__get_network_share(machine_obj=machine_obj)
        export_settings = {
            "network_share": {
                "path": network_path["path"],
                "username": username,
                "password": share_password
            }
        }
        self.__drbackup_daily.edit(export_settings=export_settings)
        self.log.info("Sleep for 10 sec for data to get written on DB")
        time.sleep(10)
        panel_details = self._panel_info.get_details()
        self.management.refresh()
        if (self.management.backup_metadata_folder != network_path["path"] and
                panel_details['Destination'] == 'Network share [{0}]'.format(network_path["path"])):
            raise CVWebAutomationException(
                'Path {0} not set as Network share value of DR backup'.format(network_path["path"]))

        self.management.set_local_dr_path(self.__generate_path(alias='local_drive', machine_obj=machine_obj))
        self.__remove_network_share(network_path, machine_obj=machine_obj)

        self.log.info('Network Share feature is validated successfully.')

    def validate_backup_data_metallic_cloud(self, turn_on: bool=False):
        """To validate Upload DR backup metadata to Metallic cloud.
        Args:
            turn_on (bool, optional): To specify enable/disable the Metallic Cloud feature. Defaults to False.

        Raises:
            CVWebAutomationException: If Upload backup metadata to Metallic cloud option is turned on from UI but disabled at backend.
            CVWebAutomationException: If Upload backup metadata to Metallic cloud option is turned off from UI but enabled at backend.
        """
        export_settings = {
            "metallic": {
                "turn_on": True
            }
        }
        self.__drbackup_daily.edit(export_settings=export_settings)
        self.log.info("Sleep for 10 sec for data to get written on DB")
        time.sleep(10)
        self.management.refresh()
        if not self.management.upload_backup_metadata_to_cloud and turn_on:
            raise CVWebAutomationException(
                'Upload backup metadata to Metallic cloud option is disabled at backend while it is turned on from UI')
        elif self.management.upload_backup_metadata_to_cloud and not turn_on:
            raise CVWebAutomationException(
                'Upload backup metadata to Metallic cloud option is enabled at backend while it is turned off from UI')
        else:
            self.log.info('Upload to Metallic Cloud is validated successfully.')
        self.management.upload_metdata_to_commvault_cloud(flag=False)

    def validate_backup_data_cloud_library(self, cloud_library_name: str, turn_on: bool=False):
        """To validate Upload backup metadata to 3rd party cloud vendor.
        Args:
            cloud_library_name (str): The name of cloud library.
            turn_on (bool, optional): To specify enable/disable the cloud libray feature. Defaults to False.

        Raises:
            Exception: if Cloud library is not configured.
            CVWebAutomationException: If Upload backup metadata to 3rd party cloud vendor option is turned on from UI but disabled at backend.
            CVWebAutomationException: If Upload backup metadata to 3rd party cloud vendor option is turned off from UI but enabled at backend.
        """
        if not self._disk_libraries.has_library(cloud_library_name):
            raise Exception('{0} Library is not available'.format(cloud_library_name))
        export_settings = {
            "cloud_library": {
                "turn_on": turn_on,
                "cloud_library_name": cloud_library_name
            }
        }
        self.__drbackup_daily.edit(export_settings=export_settings)
        self.log.info("Sleep for 10 sec for data to get written on DB")
        time.sleep(10)
        self.management.refresh()
        if not self.management.upload_backup_metadata_to_cloud_lib and turn_on:
            raise CVWebAutomationException(
                'Upload backup metadata to 3rd party cloud option is disabled at backend while it is turned on from UI')
        elif self.management.upload_backup_metadata_to_cloud_lib and not turn_on:
            raise CVWebAutomationException(
                'Upload backup metadata to 3rd party cloud option is enabled at backend while it is turned off from UI')
        else:
            self.log.info('Upload to 3rd party Cloud is validated successfully.')
        self.management.upload_metdata_to_cloud_library(flag=False)

    def validate_run_backup_job(self, job_types: tuple=tuple(['full'])):
        """To validate run DR backup job operation.

        Args:
            job_types (List(str), optional): Type of DR backup job i.e (['full', 'Differential']).
            Defaults to ['Differential'].
        """
        for job_type in job_types:
            self.__kill_running_drjobs()
            ui_job_id = self.run_backup_job(job_type)
            try:
                self.log.info('Checking for running dr jobs')
                query = "select jobId from JMAdminJobInfoTable where opType = 11"
                jobs = self._util.exec_commserv_query(query)
                if jobs[0][0] and jobs[0][0] == ui_job_id:
                    job_details = self._jobs.job_completion(jobs[0][0], timeout=10 * 60)
                    self.management.refresh()
                    if job_details['Type'] != 'Disaster Recovery Backup':
                        raise CVWebAutomationException(
                            'validation failed. DR backup job type: {0}, '
                            'Expected: Disaster Recovery Backup'.format(job_details['Type']))
                    if job_type.lower() != job_details['Backup type'].lower():
                        raise CVWebAutomationException(
                            'validation failed. DR backup job type: {0}, '
                            'Expected: {1}'.format(job_details['Backup type'], job_type))
                    if job_details['Backup set'] != 'DR-BackupSet':
                        raise CVWebAutomationException(
                            'validation failed. DR backup job backup set: {0}, '
                            'Expected: DR-BackupSet'.format(job_details['Backup set']))
                    if job_details['Destination'] != self.management.backup_metadata_folder:
                        raise CVWebAutomationException(
                            'validation failed. DR backup job destination: {0}, '
                            'Expected: {1}'.format(job_details['Destination'],
                                                   self.management.backup_metadata_folder))
                    if job_details['Status'] != 'Completed':
                        raise CVWebAutomationException(
                            'validation failed with DR backup job status: {0}'.format(job_details['Status']))
                    self._admin_console.navigator.navigate_to_maintenance()
                    self.__drbackup_daily.access_dr_backup()
                else:
                    raise CVWebAutomationException(
                        ('validation failed: Job Id in UI [{0}] is different '
                         'from job ID in backend [{1}]').format(ui_job_id, jobs[0][0]))

            except CVWebAutomationException as excp:
                raise CVWebAutomationException('validation failed with DR backup job: {0}'.format(excp))
        self.log.info('Validating run DRBackup Completed Successfully.')

    def validate_restore(self):
        """To validate restore job operation.

        Raises:
            CVWebAutomationException: If restore job failed to complete successfully.
        """
        backup_jobid = self.run_backup_job()
        restore_job_id = self.run_restore_job(str(backup_jobid), self.__generate_path(alias='restore'))

        job_details = self._jobs.job_completion(restore_job_id, timeout=10 * 60)
        job_status = job_details['Status']
        if job_status != 'Completed':
            raise CVWebAutomationException(
                'validation failed with restore job status: {0}'.format(job_status))
        else:
            self.log.info('Validating restore DRBackup Completed Successfully.')

    def validate_download_job(self, download_path: str, download_filenames: list[str]):
        """To validate download job operation.

        Args:
            download_path (str): path to download location of browser.
            download_filenames (list[str]): The list of files to download can be partial file names. E.g.
                 ['Mongo_GlobalConfigManager', 'CacheDB', 'Mongo_GCMTracking']

                Raises:
                    Exception: If download job failed to complete successfully.
        """
        backup_jobid = self.run_backup_job()
        self.run_download_job(str(backup_jobid), download_filenames)
        self.__download_wait(download_path)
        downloaded_files = self._local_machine_obj.get_files_in_path(download_path)
        self.log.info('Downloaded files are: {0}'.format(downloaded_files))
        for file in downloaded_files:
            if file.endswith('.zip'):
                self.log.info('Extracting the downloaded file: {0}'.format(file))
                with zipfile.ZipFile(file, 'r') as zip_file:
                    zip_file.extractall(download_path)
                self._local_machine_obj.delete_file(file)

        _, result = self._util.exec_commserv_query("select dirName, fileName_srm from {0} where jobid = {1}".format(
            "GXDRFULL", backup_jobid))
        source_path, _ = result[0][0], result[0][1]

        downloaded_files = self._local_machine_obj.get_files_in_path(download_path)
        self.log.info('Files to be validated are: {0}'.format(downloaded_files))
        for file in downloaded_files:
            source_filename = '_'.join(file.split('_')[1:])
            source_file_path = source_path + self.client_machine_obj.os_sep + source_filename
            is_same = self.client_machine_obj.compare_files(self._local_machine_obj, source_file_path, file)
            if not is_same:
                raise Exception('validation failed, files hash values are not same.')

        self.log.info('Validating download DRBackup files Completed Successfully..')

    def validate_drbackup_schedule(self):
        """To validate DR backup schedule operation."""

        self.log.info('Started Validating DRBackup Schedule..')
        daily_schedule_time = time.time() + 120
        new_schedule_time = time.strftime("%I:%M %p", time.localtime(daily_schedule_time))
        self.log.info("New schedule time: {}".format(new_schedule_time))
        schedule_settings = {
            "daily_start_time": new_schedule_time
        }
        self.__drbackup_daily.edit(schedule_settings=schedule_settings)
        max_wait_time = daily_schedule_time + 30
        self.__wait_for_job_trigger(max_wait_time)
        self.log.info('Validating DRBackup Schedule Completed Successfully..')

    def validate_drbackup_repeat_schedule(self):
        """To validate DR backup repeat schedule operation."""
        self.log.info('Started Validating DRBackup Repeat Schedule..')
        curr_time = time.time()
        schedule_time = time.strftime("%I:%M %p", time.localtime(curr_time - 60))
        self.log.info("New time for repeat schedule: {}".format(schedule_time))
        until = time.strftime("%I:%M %p", time.localtime(curr_time + 300))
        schedule_settings = {
            "daily_start_time": schedule_time,
            "repeat_schedule": {
                "enable": True,
                "repeat_every": "00:04",
                "until": until
            }
        }
        self.__drbackup_daily.edit(schedule_settings=schedule_settings)
        max_wait_time = curr_time + 240
        self.__wait_for_job_trigger(max_wait_time)

        self.log.info('Validating disable repeat schedule')
        self.__kill_running_drjobs()
        self._admin_console.navigator.navigate_to_maintenance()
        self.__drbackup_daily.access_dr_backup()
        curr_time = time.time()
        schedule_time = time.strftime("%I:%M %p", time.localtime(curr_time - 60))
        schedule_settings = {
            "daily_start_time": schedule_time,
            "repeat_schedule": {
                "enable": False
            }
        }
        self.__drbackup_daily.edit(schedule_settings=schedule_settings)
        max_wait_time = curr_time + 120 + 30
        try:
            self.__wait_for_job_trigger(max_wait_time)
        except Exception as e:
            self.log.info('Exception as expected: {0}'.format(str(e)))

        self.log.info('Validating DRBackup Repeat Schedule Completed Successfully..')

    def validate_backup_destinations(self):
        """To validate backup destinations page."""
        self.log.info('Validating Backup Destinations page..')
        self.log.info('navigating to Backup Destinations page')
        self.__drbackup_daily.access_dr_backup_destinations()

        self.log.info('adding a new copy in Backup destinations table')
        self.add_new_copy()

        self.log.info('validating backup destinations regions table')
        # Both Primary and secondary copy should be present in the regions table
        self.validate_backup_destinations_regions()

        self.log.info(f'validating the {self._primary_copy} copy details page')
        self.validate_dr_copy_details(self._primary_copy)

        self.log.info(f'validating delete dr job operation on {self._primary_copy}')
        # The delete operation should not be successful for DRBackup Policy.
        self.validate_delete_dr_job()

        self.log.info('navigating to Backup Destinations page')
        self.__drbackup_daily.access_dr_backup_destinations()

        self.log.info(f'validating {self._secondary_copy} copy details page')
        self.validate_dr_copy_details(self._secondary_copy)

        self.log.info('validating delete dr job operation')
        # The delete operation should not be successful for secondary copy.
        self.validate_delete_dr_job()

        self.log.info('navigating to Backup Destinations page')
        self.__drbackup_daily.access_dr_backup_destinations()

        self.log.info(f'validating delete copy operation on {self._secondary_copy} from backup destinations table')
        # The copy should get deleted successfully.
        self.validate_delete_copy(self._secondary_copy)

        self.log.info('Validating Backup Destinations page Completed Successfully..')

    def validate_backup_destinations_regions(self):
        """To validate backup destinations regions table."""
        regions_table = Rtable(self._admin_console, title='Regions')
        backup_destinations_table = Rtable(self._admin_console,
                                           xpath="//div[contains(@id,'planBackupDestinationTable')]")
        regions_table.expand_row(self._admin_console.props['label.defaultRegion'])
        backup_destination_count = (
            regions_table.get_column_data(self._admin_console.props['label.backupDestinationCount']))[0]
        copy_list_ui = backup_destinations_table.get_column_data('Name')
        copy_list_ui = [item.split('\n')[0] for item in copy_list_ui]
        copy_list_db = self._get_copy_list()
        if len(copy_list_ui) != int(backup_destination_count):
            raise CVWebAutomationException('Copy list count in UI not matching with DB on Backup destinations')
        if set(copy_list_ui) != set(copy_list_db):
            raise CVWebAutomationException(
                f'Copy list in UI {copy_list_ui} not matching with DB {copy_list_db} on Backup destinations page')

    def validate_dr_copy_details(self, copy_name: str):
        """To validate copy details page.

        Args:
            copy_name (str, optional): Name of the copy. Defaults to 'Primary'.

        Raises:
            CVWebAutomationException: If Compliance lock is disabled for Primary copy.
            CVWebAutomationException: If Copy type is not matching with the given copy name.
            CVWebAutomationException: If Retention period is not matching with the given copy name.
        """
        backup_destinations_table = Rtable(self._admin_console,
                                           xpath="//div[contains(@id,'planBackupDestinationTable')]")
        backup_destinations_table.access_link(copy_name)
        general_panel = RPanelInfo(admin_console=self._admin_console, title=self._admin_console.props['label.general'])
        if (not general_panel.is_toggle_enabled(label = self._admin_console.props['label.softwareWORM']) and
                copy_name == 'Primary'):
            raise CVWebAutomationException('Compliance lock should be enabled for Primary copy')
        else:
            try:
                general_panel.disable_toggle(self._admin_console.props['label.softwareWORM'])
                raise CVWebAutomationException('Compliance lock should not be disabled for Primary copy')
            except Exception as e:
                self.log.info('Exception as expected: {0}'.format(str(e).split('\n', 1)[0]))

        retention_rules_panel = RPanelInfo(admin_console=self._admin_console,
                                           title=self._admin_console.props['label.extended.retention.title'])
        retention_rules_panel_details = retention_rules_panel.get_details()
        retention_period_db = self._get_retention_period(copy_name)
        if retention_rules_panel_details['Retention period'] == '1 month':
            retention_period_ui = '30'
        else:
            retention_period_ui = retention_rules_panel_details['Retention period'].split()[0]
        if retention_period_ui != retention_period_db:
            raise CVWebAutomationException(f"Retention period [{0}] shown in UI is not matching with DB [{1}]".format(
                retention_period_ui, retention_period_db))
        self.log.info('Copy details validation for {0} completed successfully'.format(copy_name))

    def validate_delete_copy(self, copy_name: str):
        """This function is used to validate the functionality of delete a copy from the CommServeDR Default Region

        Args:
            copy_name (str) -- Name of the copy to be deleted

        Raises:
            CVWebAutomationException: If the copy is not deleted
        """
        backup_destinations_table = Rtable(self._admin_console,
                                           xpath="//div[contains(@id,'planBackupDestinationTable')]")
        backup_destinations_table.access_action_item(copy_name, self._admin_console.props['label.delete'], search=False)

        alert_message = self.confirm_delete_model()
        expected_message = f"Backup destination {copy_name} has been deleted successfully"

        if alert_message not in expected_message:
            raise CVWebAutomationException(f"Expected message: {expected_message}, Actual message: {alert_message}")

    def validate_delete_dr_job(self):
        """This function is used to validate the functionality of delete a DR job from the Backup Destinations Copy

        Raises:
            CVWebAutomationException: If the DR job is deleted
        """
        self._admin_console.access_tab(self._admin_console.props['header.jobs'])
        jobs_listing_table = Rtable(self._admin_console, title=self._admin_console.props['label.jobs.title'])
        jobs_listing_table.apply_filter_over_column(self._admin_console.props['label.status'], 'Available')
        job_list = jobs_listing_table.get_column_data(self._admin_console.props['label.jobId'])
        if job_list:
            jobs_listing_table.access_action_item(job_list[0],
                                                  self._admin_console.props['label.deleteJob'],
                                                  search=False)

            alert_message = self.confirm_delete_model()
            expected_message = ("Delete operation skipped "
                                "Manual deletion of jobs from a worm storage policy is not allowed..")

            if alert_message not in expected_message:
                raise CVWebAutomationException(f"Expected message: {expected_message}, Actual message: {alert_message}")
        self.log.info("No DR job available to delete")
