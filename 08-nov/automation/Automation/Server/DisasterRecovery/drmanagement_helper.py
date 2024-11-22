# -*- coding: utf-8 -*-
# pylint: disable=W1202
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for performing Commcell -> Control Panel -> DR Management related operations.

DRManagementHelper: Class for performing DR Management operations

DRCommvaultCloudManagement: Class for downloading dr dumps from commvault cloud.

CreateCommcellInstance: Class for initializing a commcell object

DRManagementHelper:
==========================

    __init__()                          --   initializes DisasterRecoveryManagement class object

    refresh()                           --   retrives the latest dr settings

    set_local_dr_path                   --   sets the local dr path and validates the setting.

    set_network_dr_path                 --   sets the unc path and validates the setting.

    upload_metdata_to_commvault_cloud   --   sets ths account to be used for commvault cloud backup.

    upload_metdata_to_cloud_library     --   sets the libarary to be used for cloud backup.

    impersonate_user                    --   account to be used for execution of pre/post scripts

    use_impersonate_user                --  gets the setting use_impersonate_user

    number_of_metadata                  --  sets number of metadata folders to be retained
                                            and validates the setting..

    number_of_metadata                  --  gets the value of the setting, number of metadata to be retained.

    use_vss                             --  sets the property and validates the setting.

    use_vss                             --  gets the property

    wild_card_settings                  --  sets log file names to be backed up for selected
                                            clients and validates the setting..

    wild_card_settings                  --  gets the log file names.

    backup_metadata_folder              --  gets the metadata destination location or path.

    upload_backup_metadata_to_cloud     --  gets the property.

    upload_backup_metadata_to_cloud_lib --  sets the property and validates the setting..

    dr_storage_policy                   --  gets the associated dr storage policy

    dr_storage_policy                   --  sets the dr storage policy and validates the setting.

    pre_scan_process                    --  sets the property and validates the setting.

    pre_scan_process                    --  gets the property

    post_scan_process                   --  sets the property and validates the setting.

    post_scan_process                   --  gets the property

    pre_backup_process                  --  sets the property and validates the setting.

    pre_backup_process                  --  gets the property

    post_backup_process                 --  sets the property and validates the setting.

    post_backup_process                 --  gets the property

    run_post_scan_process               --  sets the property and validates the setting.

    run_post_scan_process               --  gets the property

    run_post_backup_process             --  sets the property and validates the setting.

    run_post_backup_process             --  gets the property

DRCommvaultCloudManagement
===============================

    __init__()                          --   initializes DRCommvaultCloudManagement class object.

    refresh()                           --   refreshes the company details.

    _get_info()                         --   executes /info api(get) to fetch the company details.

    request_info()                      --   executes /requests api(get) to fetch the information of all the requests
                                             which were requested on the company

    request_access                      --   executes /requests api(post) to request access for set folders on the
                                             Commcell level

    approve_deny_revoke_request       --   executes /request api(put) to approve, deny, revoke access for drbackup
                                           files at Commcell Level on the cloud

    get_company_name()                  --   gets the available company names.

    get_commcell_guids_of_company         --   gets the available commcell guid's for a given company.

    get_number_of_set_folders_of_a_commcell --  gets the count of set folders available for a given commcell.

    get_available_set_folders_of_a_commcell --  gets the available set folder names for a given commcell.

    get_file_names_of_a_set_folder          --  gets the file names for a given set folder name.

    get_set_id_of_a_set_folder              --  gets the set id for a given set folder name.

    get_status_of_last_dr_backup_job        --  gets the status of last dr backup

    get_file                                --  gets the file data in binary format.

    get_companyname_companyid_commcellguid_commcellid  --  gets the mapping of commcells associated to a company.

    get_dump_data                           --  gets the data in binary format which can be written to a file.

    download_from_cvcloud                   --  downloads given set folder from cvcloud to destination folder.

CreateCommcellInstance
===============================

    __init__()                             --   initializes CreateCommcellInstance object

    __call__()                             --   returns a Commcell object

"""
import os
import datetime
from time import gmtime, strftime

from AutomationUtils import logger
from AutomationUtils.machine import Machine
from cvpysdk.disasterrecovery import DisasterRecoveryManagement
from cvpysdk.policies.storage_policies import StoragePolicy
from cvpysdk.commcell import Commcell



class DRManagementHelper(object):
    """Class to perform all the disaster recovery management operations on commcell"""

    def __init__(self, commcell):
        """Initializes DisasterRecoveryManagement object

            Args:
            commcell    (object)    --  instance of commcell

        """
        self.log = logger.get_log()
        self.management = DisasterRecoveryManagement(commcell)
        self._commcell = commcell

    def refresh(self):
        """
        refreshes the dr settings associated with commcell.

        Returns:
            None
        """
        self.management.refresh()
        self.log.info('Settings have been refreshed successfully')

    def set_local_dr_path(self, path, validate=True):
        """
        Sets local DR path

            Args:
                 path       (str)       --         local path.

                 validate   (bool)      --         based on the bool value passed validation of setting
                                                   will be handled.

            Returns:
                None
        """
        self.management.set_local_dr_path(path=path)
        if validate:
            if self.management.backup_metadata_folder != path:
                raise Exception('{0} path has not been set successfully'.format(path))
            self.log.info('{0} path has been set successfully'.format(path))

    def set_network_dr_path(self, path, username, password, validate=True):
        """
        Sets network DR path

            Args:
                 path       (str)       --      UNC path.

                 username   (str)       --      username with admin privileges of the remote machine.

                 password   (str)       --      password.

                 validate   (bool)      --      whether to validate the setting has been updated successfully or not

            Returns:
                None
        """
        self.management.set_network_dr_path(path, username, password)
        if validate:
            if self.management.backup_metadata_folder != path:
                raise Exception('{0} path has not been set successfully'.format(path))
            self.log.info('{0} path has been set successfully'.format(path))

    def upload_metdata_to_commvault_cloud(self, flag, username=None, password=None, validate=True):
        """
        Enable/Disable upload metadata to commvault cloud setting.

            Args:
                 flag       (bool)      --      True/False.

                 username   (str)       --      username of the commvault cloud.

                 password   (str)       --      password of the commvault cloud.

                 validate   (bool)      --      whether to validate the setting has been updated successfully or not

            Returns:
                 None
        """
        self.management.upload_metdata_to_commvault_cloud(flag, username, password)
        if validate:
            if self.management.upload_backup_metadata_to_cloud != flag:
                raise Exception('upload metadata to commvault cloud is not set'
                                ' successfully with value {0}'.format(flag))
            self.log.info('upload metadata to commvault cloud = {0}'.format(flag))

    def upload_metdata_to_cloud_library(self, flag, libraryname=None, validate=True):
        """
        Enable/Disable upload metadata to cloud library

            Args:
                 flag       (bool)      --      True/False.

                 libraryname   (str/object)    --      Third party cloud library name or disklibrary object.

                 validate   (bool)      --      whether to validate the setting has been updated successfully or not

            Returns:
                None
        """
        self.management.upload_metdata_to_cloud_library(flag, libraryname)
        if validate:
            if self.management.upload_backup_metadata_to_cloud_lib != flag:
                raise Exception('upload metadata to cloud library is not set'
                                ' successfully with value {0}'.format(flag))
            self.log.info('upload metadata to cloud library = {0}'.format(flag))

    def impersonate_user(self, flag, username, password, validate=True):
        """
        Enable/Disable Impersonate user option for pre/post scripts.

            Args:
                flag        (bool)      --  True/False.

                username    (str)       --  username with admin privileges.

                password    (str)       --  password for the account.

                validate   (bool)      --      whether to validate the setting has been updated successfully or not

            Returns:
                None
        """
        self.management.impersonate_user(flag, username, password)
        if validate:
            if self.management.use_impersonate_user != flag:
                raise Exception('impersonate user is not set to value {0}'.format(flag))
            self.log.info('impersonate user = {0}'.format(flag))

    @property
    def use_impersonate_user(self):
        """
        gets the impersonate user(True/False)

            Returns:
                  True/False
        """
        return self.management.use_impersonate_user

    @property
    def number_of_metadata(self):
        """
         gets the value, Number of metadata folders to be retained.

            Returns:
                number of metadata     (int)
        """
        return self.management.number_of_metadata

    @number_of_metadata.setter
    def number_of_metadata(self, value):
        """
        Sets the value, Number of metadata folders to be retained.

            Args:
                value       (int)       --      number of metadata folders to be retained.

            Returns:
                None
        """
        self.management.number_of_metadata = value
        if self.management.number_of_metadata != value:
            raise Exception('number of metadata is not successfully with value {0}'.format(value))
        self.log.info('number of metadata = {0}'.format(value))

    @property
    def use_vss(self):
        """
        gets the value, use vss()

            Returns:
                True/False
        """
        return self.management.use_vss

    @use_vss.setter
    def use_vss(self, flag):
        """
        sets the value, use vss

            Args:
                 flag   (bool)      --      True/Flase

            Returns:
                None
        """
        self.management.use_vss = flag
        if self.management.use_vss != flag:
            raise Exception('use vss is not set successfully with value {0}'.format(flag))
        self.log.info('use vss = {0}'.format(flag))

    @property
    def wild_card_settings(self):
        """
        gets the wild card settings

            Returns:
                (list)       --     client logs that are to be backed up
        """
        return self.management.wild_card_settings.split(';')

    @wild_card_settings.setter
    def wild_card_settings(self, logs):
        """
        sets the wild card setting

            Args:
                 logs    (list)      --      log file names

            Returns:
                  None
        """
        self.management.wild_card_settings = logs
        log_names = self.management.wild_card_settings.lower()
        for log_name in logs:
            if log_name.lower() not in log_names:
                raise Exception('{0} log names has not set succesfully'.format(logs))
        self.log.info('{0} log names got updated successfully')

    @property
    def backup_metadata_folder(self):
        """
        gets the backup metadata folder

            Returns:
                 (str)      --      Backup metadata folder
        """
        return self.management.backup_metadata_folder

    @property
    def upload_backup_metadata_to_cloud(self):
        """
        gets the upload backup metadata to cloud setting

            Returns:
                 True/False
        """
        return self.management.upload_backup_metadata_to_cloud

    @property
    def upload_backup_metadata_to_cloud_lib(self):
        """
        gets the upload metadata to cloud lib

            Returns:
                (str)       --      Third party library name
        """
        return self.management.upload_backup_metadata_to_cloud_lib

    @property
    def dr_storage_policy(self):
        """
        gets the storage policy name, that is being used for DR backups

            Returns:
                (object)       --      storage policy object.
         """
        return StoragePolicy(self._commcell, self.management.dr_storage_policy)

    @dr_storage_policy.setter
    def dr_storage_policy(self, storage_policy_object):
        """
        sets the storage policy for DR jobs

            Args:
                storage_policy_object       (object)        --      object of the storage policy

            Returns:
                None
        """
        self.management.dr_storage_policy = storage_policy_object
        if self.management.dr_storage_policy != storage_policy_object.name:
            raise Exception('storage policy {0} has not been set successfully'.format(storage_policy_object.name))
        self.log.info('DR Storage policy = {0}'.format(storage_policy_object.name))

    @property
    def pre_scan_process(self):
        """
        gets the script path of the pre scan process

            Returns:
                (str)       --      script path
        """
        return self.management.pre_scan_process

    @pre_scan_process.setter
    def pre_scan_process(self, path):
        """
        sets the pre scan process.

            Args:
                 path   (str)      --   path of the pre scan script

            Returns:
                None
        """
        self.management.pre_scan_process = path
        if self.management.pre_scan_process != path:
            raise Exception('pre scan process script path = {0} has not updated successfully'.format(path))
        self.log.info('pre scan process = {0}'.format(path))

    @property
    def post_scan_process(self):
        """
        gets the script path of the post scan process

            Returns:
                (str)       --      script path
        """
        return self.management.post_scan_process

    @post_scan_process.setter
    def post_scan_process(self, path):
        """
         sets the post scan process.

            Args:
                 path   (str)      --   path of the post scan script

            Returns:
                None
        """
        self.management.post_scan_process = path
        if self.management.post_scan_process != path:
            raise Exception('post scan process script path = {0} has not updated successfully'.format(path))
        self.log.info('post scan process = {0}'.format(path))

    @property
    def pre_backup_process(self):
        """
        gets the script path of the pre backup process

            Returns:
                (str)       --      script path
        """
        return self.management.pre_backup_process

    @pre_backup_process.setter
    def pre_backup_process(self, path):
        """
         sets the pre backup process.

            Args:
                 path   (str)      --   path of the pre bfackup script

            Returns:
                None
        """
        self.management.pre_backup_process = path
        if self.management.pre_backup_process != path:
            raise Exception('pre backup process script path = {0} has not updated successfully'.format(path))
        self.log.info('pre backup process = {0}'.format(path))

    @property
    def post_backup_process(self):
        """
        gets the script path of the post backup process

            Returns:
                (str)       --      script path
        """
        return self.management.post_backup_process

    @post_backup_process.setter
    def post_backup_process(self, path):
        """
         sets the post backup process.

            Args:
                 path   (str)      --   path of the post backup script

            Returns:
                None
        """
        self.management.post_backup_process = path
        if self.management.post_backup_process != path:
            raise Exception('post backup process script path = {0} has not updated successfully'.format(path))
        self.log.info('post backup process = {0}'.format(path))

    @property
    def run_post_scan_process(self):
        """
        gets the value, run post scan process

            Returns:
                 True/False
        """
        return self.management.run_post_scan_process

    @run_post_scan_process.setter
    def run_post_scan_process(self, flag):
        """
        sets the value, run post scan process

            Args:
                 flag      (bool)   --      True/False

            Returns:
                None
        """
        self.management.run_post_scan_process = flag
        if self.management.run_post_scan_process != flag:
            raise Exception('run post scan process setting is not updated successfully')
        self.log.info('run post sacn process = {0}'.format(flag))

    @property
    def run_post_backup_process(self):
        """
         gets the value, run post backup process

            Returns:
                 True/False
        """
        return self.management.run_post_backup_process

    @run_post_backup_process.setter
    def run_post_backup_process(self, flag):
        """
        sets the value, run post backup process

            Args:
                 flag      (bool)   --      True/False

            Returns:
                None
        """
        self.management.run_post_backup_process = flag
        if self.management.run_post_backup_process != flag:
            raise Exception('run post backup process setting is not updated successfully')
        self.log.info('run post backup process = {0}'.format(flag))


class DRCommvaultCloudManagement(object):

    def __init__(self, commcell_object, company_name=None, commcell_guid=None):
        """Initializes DRCommvaultCloudManagement object

            Args:
                commcell_object    (object)    --  instance of commcell

        """
        self.log = logger.get_log()
        self._commcell = commcell_object
        self._status_service = self._commcell._services['CVDRBACKUP_STATUS']
        self._info_service = self._commcell._services['CVDRBACKUP_INFO']
        self._download_service = self._commcell._services['CVDRBACKUP_DOWNLOAD']
        self._request_service = self._commcell._services['CVDRBACKUP_REQUEST']
        self._history_report_service = self._commcell._services['CVDRBACKUP_REQUEST_HISTORY']

        self._cvpysdk_object = self._commcell._cvpysdk_object
        self._company_name = company_name
        self._commcell_guid = commcell_guid
        self._company_id = None
        self._companies = None
        self.commcell_id = None
        self._company_names = []
        self.refresh()

    def refresh(self):
        """
        runs the _get_info() method

            Returns:
                  None
        """
        self._get_info()

    def _get_info(self):
        """
        Gets the information of companies associated to cvcloud.
        Response's verbosity depends on the parameters passed.
        Response varies if company_id and commcell_guid is set.
        Set the company_id/commcell_guid using setters company_id/commcell_guid

            Returns:
                 None

            Raises:
                Exception:
                    if failed to get the required details from cvcloud
        """
        if self._company_id and self._commcell_guid:
            info_service = self._info_service + '?companyId=' + str(self._company_id) \
                           + '&csGuid=' + self._commcell_guid

        elif self._company_id is not None:
            info_service = self._info_service + '?companyId=' + str(self._company_id)

        else:
            info_service = self._info_service

        flag, response = self._cvpysdk_object.make_request(method='GET',
                                                           url=info_service)

        if flag:
            if response and response.json():
                self._companies = response.json().get('companies')
            else:
                raise Exception('Response received is empty')
        else:
            response_string = self._commcell._update_response_(response.text)
            raise Exception('Response was not successful, error = {0}'.format(response_string))

    def request_info(self):
        """
        Fetches the information of all the requests which were requested on the company.

            Prerequisites:
                Set the company_id with setter company_id, if not set.
                (Optional)Set the commcell_guid with setter commcell_guid, if not set.

            Args:
                None

            Returns:
                Total number of requests and detailed description about the requests done on the company
        """
        if self._company_id and self._commcell_guid:
            request_service = self._request_service + '?companyId=' + str(self._company_id) \
                              + '&csGuid=' + self._commcell_guid
        elif self._company_id is not None:
            request_service = self._request_service + '?companyId=' + str(self._company_id)
        else:
            raise Exception('Company ID is not set.  Please set the Company ID using setter company_id')
        flag, response = self._cvpysdk_object.make_request(method='GET',
                                                           url=request_service)
        if flag:
            if response and response.json():
                request = response.json().get('requests')
                return request
        else:
            response_string = self._commcell._update_response_(response.text)
            raise Exception('Response was not successful, error = {0}'.format(response_string))

    def request_access(self, comments: str):
        """
        Request Access for set folders on the Commcell level

            Prerequisite:
                Set the commcell_guid with setter commcell_guid, if not set.

            Args:
                comments      (str)    --  comment for accessing request

            Returns:
                (int)   --  request id if the request was sent successfully

            Raise:
                Exception:
                    if access request was already submitted
        """
        if self._commcell_guid is None:
            raise Exception('Commcell GUID is not set. Please set the commcell guid using setter commcell_guid')
        payload = {"commcell_guid": self._commcell_guid, "comments": comments}
        flag, response = self._cvpysdk_object.make_request(method='POST', url=self._request_service,
                                                           payload=payload)
        if flag:
            return response.json().get('request_id')
        else:
            response_string = self._commcell._update_response_(response.text)
            raise Exception('Response was not successful, error = {0}'.format(response_string))

    def approve_deny_revoke_request(self, request_id: int, approval_type: int,
                                    validity=None, comments=None):
        """
        Approve, Deny, Revoke access for drbackup files at Commcell Level on the cloud

            Prerequisites:
                Set the company_id with setter company_id, if not set.

            Args:
                request_id    (int)    --  request id of the submitted request
                approval_type:(int)    --  2 for approve
                                           3 for reject
                                           4 for revoke
                comments      (str)    --  comment for approving, rejecting, revoking request
                validity      (str)    --  yyyy-mm-dd-h-m-s (If not provided, sets lifetime access until revoked)

            Returns:
                Success:
                    if approved, rejected, revoked successfully

            Raise:
                Exception:
                    if validity passed is out of bounds
                """
        payload = {"company_id": self._company_id,
                   "request_id": request_id,
                   "approval_type": approval_type,
                   "validity": validity}

        if validity is not None:
            validity = validity.split('-')
            try:
                initial_time = datetime.datetime(int(validity[0]), int(validity[1]),
                                                 int(validity[2]), int(validity[3]), int(validity[4]), int(validity[5]))
                client_system_timezone = strftime("%z", gmtime())
                hours, minutes = float(client_system_timezone[1:3]), float(client_system_timezone[3:])
                local_timezone = datetime.timedelta(minutes=minutes, hours=hours)
                if client_system_timezone[0] == '+':
                    initial_time = initial_time - local_timezone
                else:
                    initial_time = initial_time + local_timezone
            except ValueError as error:
                self.log.info(error)
                raise Exception(error)
            payload["validity"] = str(initial_time.isoformat()) + 'Z'

        if comments is not None:
            payload["comments"] = comments
        flag, response = self._cvpysdk_object.make_request(method='PUT', url=self._request_service,
                                                           payload=payload)

        if flag:
            return response.json()
        else:
            response_string = self._commcell._update_response_(response.text)
            raise Exception('Response was not successful, error = {0}'.format(response_string))

    def get_company_names(self):
        """
        gets the company names.

            Returns:
                 (list)     --          list of company names
        """
        self.refresh()
        if self._companies:
            for company in self._companies:
                self._company_names.append(company.get('company_name'))
            return self._company_names
        else:
            raise Exception('Company details are not available')

    def get_commcell_guids_of_company(self, hardcheck=True):
        """
        gets the available commcell guid's for a given company name.

            Prerequisites:
                Set the company name using setter company_name if not set

            Args:
                hardcheck           (bool)  --      if company name not found and hardcheck = True
                    default:True                                    raises exception
                                                    if company name not found and hardcheck = False
                                                                    logs the error

            Returns:
                  (list)        --      list of commcell guid's

            Raises:
                  Exception:
                    if company not found and hardcheck = True, raises exception

                    if company not found and hardcheck = False, logs the error

        """
        commcell_guids = []
        company_found = False
        self.refresh()
        if self._companies:
            if self._commcell_guid:
                for company in self._companies:
                    if company.get('company_name') == self._company_name:
                        company_found = True
                        for commcell in company.get('commcells'):
                            commcell_guids.append(commcell.get('commcell_guid'))
                        return commcell_guids
                if not company_found and hardcheck:
                    raise Exception('{0} company not found'.format(self._company_name))
                else:
                    self.log.info('{0} company not found'.format(self._company_name))
            else:
                raise Exception('Data type of the input(s) is not valid')
        else:
            raise Exception('Company details are not available')

    def get_number_of_set_folders_of_a_commcell(self, hardcheck=True):
        """
        gets the count of set folders associated to a commcell.

            Prerequisites:
                Set the company_name with setter company_name, if not set.
                Set the commcell_guid with setter commcell_guid, if not set

            Args:
                hardcheck           (bool)  --      if company name not found and hardcheck = True
                    default:True                                    raises exception
                                                    if company name not found and hardcheck = False
                                                                    logs the error

            Returns:
                (int)           --      count of the available set folders for a given commcell

            Raises:
                  Exception:
                    if company not found and hardcheck = True, raises exception

                    if company not found and hardcheck = False, logs the error

            NOTE: use setters company_name and commcell_guid to set the company name and commcell guid
        """
        company_found = False
        commcell_guid_found = False
        self.refresh()
        if self._companies:
            if self._company_name and self._commcell_guid:
                for company in self._companies:
                    if company.get('company_name') == self._company_name:
                        company_found = True
                        for commcell in company.get('commcells'):
                            if commcell.get('commcell_guid') == self._commcell_guid:
                                commcell_guid_found = True
                                return commcell.get('num_sets')
                if (not company_found or not commcell_guid_found) and hardcheck:
                    raise Exception('one of the value is not found, {0} = {1}, {2} = {3}'.format(
                        self._company_name, company_found, self._commcell_guid, commcell_guid_found))
                else:
                    self.log.info('one of the value is not found, {0} = {1}, {2} = {3}'.format(
                        self._company_name, company_found, self._commcell_guid, commcell_guid_found))
            else:
                raise Exception('Data type of the input(s) is not valid')
        else:
            raise Exception('Company details are not available')

    def get_available_set_folders_of_a_commcell(self, hardcheck=True):
        """
        gets the names of available set folders for a given commcell.

            Prerequisites:
                Set the company_name with setter company_name, if not set.
                Set the commcell_guid with setter commcell_guid, if not set

            Args:
                hardcheck           (bool)  --      if company name not found and hardcheck = True
                    default:True                                    raises exception
                                                    if company name not found and hardcheck = False
                                                                    logs the error

            Returns:
                (int)           --      count of the available set folders for a given commcell

            Raises:
                  Exception:
                    if company not found and hardcheck = True, raises exception

                    if company not found and hardcheck = False, logs the error

        """
        set_folder_names = []
        company_found = False
        commcell_guid_found = False
        self.refresh()
        if self._companies:
            if self._company_name and self._commcell_guid:
                for company in self._companies:
                    if company.get('company_name') == self._company_name:
                        for commcell in company.get('commcells'):
                            if commcell.get('commcell_guid') == self._commcell_guid:
                                for folder in commcell.get('sets'):
                                    set_folder_names.append(folder.get('set_name'))
                                return set_folder_names
                if (not company_found or not commcell_guid_found) and hardcheck:
                    raise Exception('one of the value is not found, {0} = {1}, {2} = {3}'.format(
                        self._company_name, company_found, self._company_name, commcell_guid_found))
                else:
                    self.log.info('one of the value is not found, {0} = {1}, {2} = {3}'.format(
                        self._company_name, company_found, self._company_name, commcell_guid_found))
            else:
                raise Exception('Data type of the input(s) is not valid')
        else:
            raise Exception('Company details are not available')

    def get_file_names_of_a_set_folder(self, set_folder_name, hardcheck=True):
        """
        gets file names of a set folder for a given commcell and company.

            Prerequisites:
                Set the company_name with setter company_name, if not set.
                Set the commcell_guid with setter commcell_guid, if not set

            Args:
                set_folder_name    (str)    --      name of the set folder

                hardcheck           (bool)  --      if company name not found and hardcheck = True
                    default:True                                    raises exception
                                                    if company name not found and hardcheck = False
                                                                    logs the error

            Returns:
                (list)           --      list of file names for a given set folder

            Raises:
                  Exception:
                    if company not found and hardcheck = True, raises exception

                    if company not found and hardcheck = False, logs the error

            NOTE: set folder name format(eg: SET_123)
        """
        file_names = []
        company_found = False
        commcell_guid_found = False
        set_folder_found = False
        self.refresh()
        if self._companies:
            if self._company_name and self._commcell_guid and isinstance(set_folder_name, str):
                for company in self._companies:
                    if company.get('company_name') == self._company_name:
                        company_found = True
                        for commcell in company.get('commcells'):
                            if commcell.get('commcell_guid') == self._commcell_guid:
                                commcell_guid_found = True
                                for folder in commcell.get('sets'):
                                    if folder.get('set_name') == set_folder_name:
                                        set_folder_found = True
                                        for file in folder.get('files'):
                                            file_names.append(file.get('file_name'))
                                        return file_names
                if (not company_found or not commcell_guid_found or not set_folder_found) and hardcheck:
                    raise Exception('one of the value is not found, {0} = {1}, {2} = {3}, {4} = {5}'.format(
                        self._company_name, company_found, self._commcell_guid, commcell_guid_found, set_folder_name,
                        set_folder_found))
                else:
                    self.log.info('one of the value is not found, {0} = {1}, {2} = {3}, {4} = {5}'.format(
                        self._company_name, company_found, self._commcell_guid, commcell_guid_found, set_folder_name,
                        set_folder_found))
            else:
                raise Exception('Data type of the input(s) is not valid')
        else:
            raise Exception('Company details are not available')

    def get_set_id_of_a_set_folder(self, set_folder_name, hardcheck=True):
        """
        gets set id of a set folder for a given commcell and company.

            Prerequisites:
                Set the company_name with setter company_name, if not set.
                Set the commcell_guid with setter commcell_guid, if not set

            Args:
                company_name       (str)    --      name of the company

                commcell_guid        (str)    --    GUID of a commcell

                set_folder_name    (str)    --      name of the set folder

                hardcheck           (bool)  --      if company not found and hardcheck = True
                    default:True                                    raises exception
                                                    if company not found and hardcheck = False
                                                                    logs the error

            Returns:
                (int)           --      set id of a set folder.

            Raises:
                  Exception:
                    if company not found and hardcheck = True, raises exception

                    if company not found and hardcheck = False, logs the error

            NOTE: set folder name format(eg: SET_123)
        """
        company_found = False
        commcell_guid_found = False
        set_folder_found = False
        self.refresh()
        if self._companies:
            if self._company_name and self._commcell_guid and isinstance(set_folder_name, str):
                for company in self._companies:
                    if company.get('company_name') == self._company_name:
                        company_found = True
                        for commcell in company.get('commcells'):
                            if commcell.get('commcell_guid') == self._commcell_guid:
                                commcell_guid_found = True
                                for folder in commcell.get('sets'):
                                    if folder.get('set_name') == set_folder_name:
                                        set_folder_found = True
                                        return folder.get('set_id')
                if (not company_found or not commcell_guid_found or not set_folder_found) and hardcheck:
                    raise Exception('one of the value is not found, {0} = {1}, {2} = {3}, {4} = {5}'.format(
                        self._company_name, company_found, self._commcell_guid, commcell_guid_found, set_folder_name,
                        set_folder_found))
                else:
                    self.log.info('one of the value is not found, {0} = {1}, {2} = {3}, {4} = {5}'.format(
                        self._company_name, company_found, self._commcell_guid, commcell_guid_found, set_folder_name,
                        set_folder_found))
            else:
                raise Exception('Data type of the input(s) is not valid')
        else:
            raise Exception('Company details are not available')

    @property
    def get_status_of_last_dr_backup_job(self):
        """
        returns the status of last dr backup

            Raises:
                Exception:
                    when failed to get the required response

            Returns:
                (dict)  -   format as shown below
                {
                    "DRbackupURL": "",
                    "UploadStatus": int,
                    "DRLastUploadedTime": ""
                }
        """
        if self._commcell_guid:
            flag, response = self._cvpysdk_object.make_request(method='GET',
                                                               url=self._status_service % self._commcell_guid)
        else:
            raise Exception('Please set the commcell guid using setter commcell_guid')
        if flag:
            if response and response.json():
                return response.json()
            else:
                raise Exception('Response received is empty')
        else:
            response_string = self._commcell._update_response_(response.text)
            raise Exception('Response was not successful, error = {0}'.format(response_string))

    def get_companyname_companyid_commcellguid_commcellid(self):
        """
        Gets the mapping of commcells associated to a company.
        Useful for request_access method where commcell_guid is required
        Useful for request_info method where company_id is required

            Args:
                None

            Returns:
                A list of 4 element tuple consisting of company_name, company_id, commcell_guid. commcell_id
        """
        flag, response = self._cvpysdk_object.make_request(method='GET',
                                                           url=self._info_service)
        if flag:
            if response and response.json():
                all_companies = response.json().get('companies')
            else:
                raise Exception('Response received is empty')
        else:
            response_string = self._commcell._update_response_(response.text)
            raise Exception('Response was not successful, error = {0}'.format(response_string))
        company_name_is_to_company_id_is_to_commcell_guid_is_to_commcell_id = []
        for i in all_companies:
            for j in i.get('commcells'):
                company_name_is_to_company_id_is_to_commcell_guid_is_to_commcell_id.append((i.get('company_name'), i.get('company_id'),
                                                                          j.get('commcell_guid'), j.get('commcell_id')))
        return company_name_is_to_company_id_is_to_commcell_guid_is_to_commcell_id

    def get_dump_data(self, set_id, file_name):
        """
        gets the data in binary format which can be written to a file.

            Args:
                set_id      (int)   -       set_id associated to set folder in cvcloud

                file_name   (str)   -       file to be downloaded from cvcloud

            Returns:
                response    (bytes) -       downloaded data

            Raises:
                Exception:
                    if failed to get the required response.

            NOTE: set id can be obtained with method get_set_id_of_a_set_folder()
        """
        data = {
            "company_id" : self._company_id,
            "commcell_guid" : self._commcell_guid,
            "job_id" : set_id,
            "file_name" : file_name
        }
        flag, response = self._cvpysdk_object.make_request(method='POST', url=self._download_service, payload=data)
        if flag:
            if response and response.json():
                file_url = response.json().get('file_url', None)
                sas_token = response.json().get('SAS_token', None)
                if not file_url or not sas_token:
                    raise Exception('Failed to get the required response')
                flag, response = self._cvpysdk_object.make_request(method='GET', url=file_url + '?' + sas_token,
                                                                   headers=[], stream=True)
                if flag:
                    if response:
                        return response
                    raise Exception('Response received is empty')
                else:
                    response_string = self._commcell._update_response_(response.text)
                    raise Exception('Response was not successful, error = {0}'.format(response_string))
            else:
                raise Exception('Response received is empty')
        else:
            response_string = self._commcell._update_response_(response.text)
            raise Exception('Response was not successful, error = {0}'.format(response_string))

    def download_from_cvcloud(self, set_folder_name, destination_path,
                              chunk_size=1000000):
        """
        Downloads given set folder from cvcloud to destination folder.

            Prerequisites:
                Set the company_id with setter company_id, if not set.
                Set the commcell_guid with setter commcell_guid, if not set

            Args:
                set_folder_name     (str)   -   set folder name.

                destination_path    (str)   -   destination path for downloads.

                chunk_size          (int)   -   chunk size of the file.
                    default: 1000000

            Returns:
                None

            Raises:
                Exception:
                    if path doesn't exist
                    if set folder doesn't exist in cvcloud
                    if failed to download the file.
        """
        if self._commcell_guid is None:
            raise Exception('Commcell GUID is not set. Please set the commcell guid using setter commcell_guid')
        if self._company_id is None:
            raise Exception('Company ID is not set. Please set the company id using setter company_id')
        self.log.info('commcell guid is {0}'.format(self._commcell_guid))
        set_id = self.get_set_id_of_a_set_folder(set_folder_name)
        file_names = self.get_file_names_of_a_set_folder(set_folder_name)
        self.log.info('List of files in the set folder {1}, {0}'.format(file_names, set_folder_name))
        if Machine().check_directory_exists(destination_path):
            for file in file_names:
                self.log.info('Downloading file {0} .....'.format(file))
                data = self.get_dump_data(set_id, file)
                with open(os.path.join(destination_path, file), 'wb') as f:
                    for chunk in data.iter_content(chunk_size=chunk_size):
                        f.write(chunk)
                    self.log.info(
                        '{0} file downloaded to {1} directory successfully'.format(file, destination_path))
        else:
            raise Exception("{0} path doesn't exist".format(destination_path))

    def validate_drbackup_download_history_report(self, dataset_parameters: dict, acceptableCommcells: list):
        """
                Validates DR Download history report using dataset_parameters and acceptableCommcells list.

                    Args:
                        dataset_parameters  (dict)   -   dataset parameters in form of key/value

                        acceptableCommcells (list)   -   list of acceptable Commcell ID's that a user is part of

                    Returns:
                        None

                    Raises:
                        Exception:
                            if a user can see another tenant's commcell
                            if failed to get the required response

                NOTE: dataset_parameters should have datasetGuid as a key and should have value of DR Backup Download History dataset GUID
                """
        time_period = dataset_parameters.get('duration', 30) #if key not found default to 30 days
        time_period = '-P{}D P0D'.format(time_period)
        dataset_guid = dataset_parameters.get('datasetGuid', None)
        if dataset_guid is None:
            raise Exception("Dataset guid is None. Please provide Dataset guid")
        if len(acceptableCommcells) == 0:
            raise Exception("Commcells to verify history report are None. Please provide Commcells")
        url = self._history_report_service % (dataset_guid, time_period)
        flag, response = self._cvpysdk_object.make_request(method='GET', url=url)
        if flag:
            if response and response.json():
                records = response.json()['records']
                for record in records:
                    commcellID = record[-4]
                    if commcellID not in acceptableCommcells:
                        raise Exception("Commcell {} from other User Group is visible with metadata {}".format(commcellID, record))
            else:
                raise Exception('Response received is empty')
        else:
            response_string = self._commcell._update_response_(response.text)
            raise Exception('Response was not successful, error = {0}'.format(response_string))

    @property
    def company_name(self):
        """
        gets the name of the company

            Returns:
                (str)   --  name of the company
        """
        return self._company_name

    @company_name.setter
    def company_name(self, company_name: str):
        """
        sets the name of the company

            Args:
                company_name       (str)  --        name of the company
        """
        self._company_name = company_name
        self.refresh()

    @property
    def commcell_guid(self):
        """
        gets the GUID of the source commcell

            Returns:
                (str)   --  GUID of the commcell
        """
        return self._commcell_guid

    @commcell_guid.setter
    def commcell_guid(self, commcell_guid: str):
        """
         sets the GUID of the source commcell

            Args:
                commcell_guid   (str)   --  GUID of the commcell
        """
        self._commcell_guid = commcell_guid
        self.refresh()

    @property
    def company_id(self):
        """
        gets the company id of the company

            Returns:
                (int)   --  company id of the company
        """
        return self._company_id

    @company_id.setter
    def company_id(self, company_id: int):
        """
         sets the company id of the company

            Args:
                company_id  (int)   --    company id of the company
        """
        self._company_id = company_id


class CreateCommcellInstance:
    def __init__(self, web_console_hostname: str, commcell_username: str, commcell_password: str):
        """
        Creates a Commcell object

            Args:
                web_console_hostname    (str)   --   Console Hostname
                commcell_username       (str)   --   Username of Commcell
                commcell_password       (str)   --   Password associated for the above username

            Return:
                Commcell object
        """
        self._web_console_hostname = web_console_hostname
        self._commcell_username = commcell_username
        self._commcell_password = commcell_password

    def __call__(self):
        return Commcell(self._web_console_hostname, self._commcell_username, self._commcell_password)
