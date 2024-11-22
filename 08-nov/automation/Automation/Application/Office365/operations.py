# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module for communicating with cvpysdk for all commvault related operations.

SharepointCvOperation class is defined in this file.

SharepointCvOperation: Performs Commvault related operations using cvpysdk

SharepointCvOperation:

    __init__()                                      --      initializes the SharepointCvOperation object by
                                                            calling commcell object of cvpysdk

    validate_office_365_list()                      --      checks the presence of client id in office365
                                                            entities i.e. if the client is listed properly
                                                            after creation.

    validate_infrastructure_details()               --      validates infrastructure details of client
                                                            i.e., index server is associated correctly after
                                                            creation and  access nodes are associated properly in
                                                            the pseudo client

    validate_share_point_client_details()           --      validates share point account details of pseudo
                                                            client. SharePoint client details- Global admin,
                                                            azure details

    validate_server_plan()                          --      validates server plan.

    validate_client_creation()                      --      validates the client creation

    add_share_point_pseudo_client()                 --      adds Share Point Pseudo Client to commcell

    run_manual_discovery()                          --      triggers manual discovery of pseudo client

    get_plan_obj()                                  --      returns plan object of the given plan name

    check_sites_under_add_webs()                    --      checks whether SP content i.e, sites/webs is available under
                                                            add webs or not

    configure_group_for_backup()                    --      configures auto association group for backup

    update_auto_association_group_properties()      --      updates auto association group properties

    validate_additional_service_accounts()          --      validates whether users listed under service accounts or not

    get_latest_ci_job                               --      Get latest completed/running Content Indexing job of the client

    suspend_job()                                   --      suspends the specified job

    resume_job()                                    --      resumes the specified job

    kill_job()                                      --      kills the specified job

    delete_share_point_pseudo_client()              --      performs deletion of share point pseudo client

    wait_time()                                     --      waits for the specified interval of time

    check_playback_completion()                     --      checks whether playback for the job is completed or not

    run_backup()                                    --      runs backup for pseudo client at subclient level

    get_job_advance_details()                       --      returns advance job details

    monitor_job_advance_details()                   --      monitors job status stats till the backup of specified
                                                            number of webs is finished

    validate_num_webs_in_backup()                   --      validates number of webs picked up for backup

    browse_for_sp_sites()                           --      checks whether SP content i.e, sites/webs are available
                                                            under add webs or not and waits till content is available
                                                            under add webs

    get_sites_user_account_info()                   --      returns dictionary of user account information of specified
                                                            sites

    associate_content_for_backup()                  --      associates content for backup

    associates_sites_for_backup()                   --      associates sites for backup

    include_sites_in_backup()                       --      enables sites for backup

    exclude_sites_from_backup()                     --      disables sites from backup

    remove_sites_from_backup_content()              --      removes sites from backup content

    get_backup_reference_time_of_associated_webs()  --      returns backup reference time of all associated webs

    validate_backup_reference_time()                --      validates backup reference time for committed and
                                                            uncommitted webs

    validate_restartability()                       --      validates count of completed webs and to be processed webs
                                                            with current status of webs in the job

    suspend_resume_job()                            --      suspends and resumes job based on provided number of webs
                                                            to be completed and waits till the backup job is completed

    check_job_status()                              --      checks the status of job until it is finished and
                                                            raises exception on pending, failure etc

    update_azure_storage_details()                  --      updates azure storage details in sharepoint backupset properties

    run_restore()                                   --      runs a restore job on the specified Sharepoint client

    disk_restore()                                  --      runs disk restore for specified Sharepoint client

    process_index_retention_rules()                 --      makes API call to process index retention rules

    delete_backupset()                              --      Deletes the backupset present in the client

"""
import time
import re
from base64 import b64encode
from xml.etree import ElementTree
from Application.Office365.solr_helper import CVSolr
from AutomationUtils.machine import Machine
from AutomationUtils.windows_machine import WindowsMachine
from ..Sharepoint import sharepointconstants as constants, sharepointconstants
from dynamicindex.utils import constants as cs


class SharepointCvOperation:
    """Class for performing Commvault operations"""

    def __init__(self, sp_object):
        """Initializes the SharepointCvOperation object by calling commcell object of cvpysdk.

                Args:
                    sp_object (object)  --  instance of Share Point Online class

                Returns:
                    object               --  instance of SharepointCvOperation class

        """

        self.tc_object = sp_object.tc_object
        self.sp_object = sp_object
        self.commcell = self.tc_object.commcell
        self.tcinputs = self.tc_object.tcinputs
        self.csdb = self.tc_object.csdb
        self.log = self.tc_object.log
        self.app_name = self.__class__.__name__  # Used for exception list
        self._client = None
        self._agent = None
        self._backupset = None
        self._subclient = None
        self.instance = None
        self.site_user_account_info = None
        self.plan_obj = None
        self.restore_retry_count = 0

    @property
    def agent(self):
        """Returns the agent object"""
        if self._agent is None:
            self._agent = self.client.agents.get(constants.AGENT_NAME)
        return self._agent

    @property
    def backupset(self):
        """Returns the backupset object"""
        if self._backupset is None:
            self._backupset = self.agent.backupsets.get(self.sp_object.backupset_name)
        return self._backupset

    @property
    def subclient(self):
        """Returns the subclient object"""
        if self._subclient is None:
            self._subclient = self.backupset.subclients.get(self.sp_object.subclient_name)
        return self._subclient

    @property
    def client(self):
        """Returns the client object"""
        if self._client is None:
            self._client = self.commcell.clients.get(self.sp_object.pseudo_client_name)
        return self._client

    def get_job_results_dir(self, full_path=False):
        """
        Get the full job results directory
        """
        base_path = self.client.properties.get('client').get('jobResulsDir').get('path')
        if not base_path:
            proxy_client = self.commcell.clients.get(self.sp_object.access_nodes_list[0])
            base_path = proxy_client.job_results_directory
        self.log.info("Job results dir: %s", base_path)
        if full_path:
            windows_machine = Machine(self.sp_object.access_nodes_list[0], self.commcell)
            full_path = windows_machine.join_path(base_path, "SharePointV2", "Backup",
                                                  str(self.subclient.subclient_id))
            self.log.info("Job results dir full path: %s", full_path)
            return full_path
        return base_path

    def validate_office_365_list(self):
        """This function checks the presence of client id in office365
        entities i.e. if the client is listed properly after creation.
        """
        try:
            client_id = self.commcell.clients.office_365_clients.get(self.sp_object.backupset_name.lower() if self.sp_object.v1 else
                    self.sp_object.pseudo_client_name.lower(), {}).get('id', -1)
            if client_id != self.client.client_id:
                raise Exception(f"{self.sp_object.pseudo_client_name} not found in office 365 entities.")
            self.log.info('Pseudo Client is listed in Office365 Entities')
        except Exception as exception:
            self.log.exception("Exception while validating office 365 entities list: %s", str(exception))
            raise exception

    def validate_infrastructure_details(self):
        """This function validates infrastructure details of client
        Infrastructure details - Index server and member server details
        """
        try:
            client_properties = self.client.properties
            if self.sp_object.index_server in client_properties.get("pseudoClientInfo", {}). \
                    get("sharepointPseudoClientProperties", {}).get("indexServer", {}).get("mediaAgentName", ""):
                self.log.info('Index Server : \'{0}\' details are set properly'.format(self.sp_object.index_server))
            else:
                raise Exception(
                    'Index Server : \'{0}\' details are not set properly'.format(self.sp_object.index_server))

            member_servers = client_properties.get("pseudoClientInfo", {}). \
                get("sharepointPseudoClientProperties", {}).get("spMemberServers", {}).get("memberServers", [])
            if member_servers:
                for member_server in member_servers:
                    if member_server.get("client", {}).get("clientName", "") not in self.sp_object.access_nodes_list:
                        raise Exception('Member Servers  : {0} details are not set properly'.format(
                            self.sp_object.access_nodes_list))
                else:
                    self.log.info('Member Servers : {0} details  are set properly'.format(
                        self.sp_object.access_nodes_list))
            else:
                raise Exception('Failed to find member server : {0} details'.format(
                    self.sp_object.access_nodes_list))
            self.log.info('Index Server Details and Member Server Details are validated successfully')

        except Exception as exception:
            self.log.exception("Exception while validating infrastructure details: %s", str(exception))
            raise exception

    def validate_share_point_client_details(self):
        """This function validates share point account details of
        pseudo client. SharePoint client details- Global admin, azure details.
        """
        try:
            backupset_properties = self.backupset.properties
            if self.sp_object.v1:
                spOfficeBackupsetProp = backupset_properties.get("sharepointBackupSet", {}).get(
                    "spOffice365BackupSetProp",
                    {})
                if spOfficeBackupsetProp.get("office365Credentials",
                                             {}).get("userName",
                                                     "") == self.sp_object.user_username and spOfficeBackupsetProp.get(
                    "isModernAuthEnabled", "") == self.sp_object.is_modern_auth_enabled:
                    self.log.info('SharePoint Office 365 Credential set successfully')
                else:
                    raise Exception("SharePoint Office 365 Credential not set properly")
                sharepointBackupset = backupset_properties.get("sharepointBackupSet", {}).get(
                    "spOffice365BackupSetProp",
                    {})
                if sharepointBackupset.get("azureUserAccount",
                                           "") == self.sp_object.azure_username and sharepointBackupset.get(
                    "tenantUrlItem", "") == self.sp_object.tenant_url:
                    self.log.info('Azure User Account and Tenant Url set properly')
                else:
                    raise Exception('Azure User Account and Tenant Url not set properly')
                planEntity = backupset_properties.get("planEntity", {})
                if planEntity.get("planName", "") == self.sp_object.server_plan:
                    self.log.info('Server Plan set properly')
                else:
                    raise Exception('Server Plan not set properly')

            else:
                accounts = backupset_properties.get("sharepointBackupSet", {}). \
                    get("spOffice365BackupSetProp", {}).get("serviceAccounts", {}).get("accounts", [])
                if accounts:
                    for account in accounts:
                        if account.get("serviceType", "") == constants.USER_ACCOUNT_SERVICE_TYPE[
                            "Sharepoint Global Administrator"] \
                                and account.get("userAccount", {}).get("userName",
                                                                       "") == self.sp_object.global_administrator:
                            self.log.info('SharePoint Global Admin Details are set properly')
                            break
                    else:
                        raise Exception("SharePoint Global Admin Details are not set properly")
                else:
                    raise Exception('Service Accounts information is not found')

            if not self.sp_object.v1 or self.sp_object.is_modern_auth_enabled:
                azure_apps = backupset_properties.get("sharepointBackupSet", {}). \
                    get("spOffice365BackupSetProp", {}).get("azureAppList", {}).get("azureApps", [])
                if azure_apps:
                    if azure_apps[0].get("azureDirectoryId", "") == self.sp_object.azure_app_tenant_id \
                            and azure_apps[0].get("azureAppId", "") == self.sp_object.azure_app_id:
                        self.log.info('Azure Details are set properly')
                    else:
                        raise Exception('Azure Details are not set properly')
                else:
                    raise Exception('Azure apps information is not found')
        except Exception as exception:
            self.log.exception("Exception while validating SharePoint client details: %s", str(exception))
            raise exception

    def validate_server_plan(self):
        """This function validates server plan.
        """
        if self.subclient.plan == self.sp_object.server_plan:
            self.log.info('Server Plan is set properly')
        else:
            raise Exception('Server Plan is not set properly')

    def validate_client_creation(self):
        """This function validates the client creation
        """
        self.log.info('Checking for created client in office365 entitites')
        self.validate_office_365_list()
        if not self.sp_object.v1:
            self.log.info('Validating Infrastructure Details of client')
            self.validate_infrastructure_details()
        self.log.info('Validating Global Administrator and Azure Details')
        self.validate_share_point_client_details()
        if not self.sp_object.v1:
            self.log.info('Validating Server Plan')
            self.validate_server_plan()

    def validate_pseudo_client_present(self):
        """Checks/validates if Pseudo Client is already present or not
        """
        try:
            self.log.info('Checking if pseudo client is present or not %s',
                          self.sp_object.pseudo_client_name)
            if self.sp_object.v1:
                if self.agent.backupsets.has_backupset(self.sp_object.backupset_name):
                    self.log.info('V1 Client exists: %s', self.sp_object.pseudo_client_name)
                    return
            else:
                if self.commcell.clients.has_client(self.sp_object.pseudo_client_name):
                    self.log.info('V2 Client exists: %s', self.sp_object.pseudo_client_name)
                    return
            self.log.info('Client does not exist: %s', self.sp_object.pseudo_client_name)
            raise Exception(f'Client {self.sp_object.pseudo_client_name} is not present')
        except Exception as exception:
            self.log.exception("An error occurred while checking for the presence of share point client\nError: '{0}'".
                               format(exception))
            raise exception


    def add_share_point_pseudo_client(self, cloud_region=1):
        """Adds Share Point Pseudo Client to commcell

            args:

            cloud_region (int):   stores the cloud region for the SharePoint client
                                    - Default (Global Service) [1]
                                    - Germany [2]
                                    - China [3]
                                    - U.S. Government GCC [4]
                                    - U.S. Government GCC High [5]
        """
        try:
            self.log.info('Creating Share Point Client %s',
                          self.sp_object.pseudo_client_name)
            if self.sp_object.v1:
                if self.agent.backupsets.has_backupset(self.sp_object.backupset_name):
                    self.log.info('Client exists. Deleting it and creating')
                    self.delete_share_point_pseudo_client(self.sp_object.pseudo_client_name)
                self.agent.backupsets.add_v1_sharepoint_client \
                    (self.sp_object.backupset_name, self.sp_object.server_plan,
                     self.sp_object.pseudo_client_name, tenant_url=self.sp_object.tenant_url,
                     user_username=self.sp_object.user_username, user_password=
                     self.sp_object.user_password, is_modern_auth_enabled=self.sp_object.is_modern_auth_enabled,
                     azure_username=self.sp_object.azure_username, azure_secret=self.sp_object.azure_secret,
                     azure_app_id=self.sp_object.azure_app_id,
                     azure_app_key_id=self.sp_object.azure_app_secret,
                     azure_directory_id=self.sp_object.azure_app_tenant_id)
            else:
                if self.commcell.clients.has_client(self.sp_object.pseudo_client_name):
                    self.log.info('Client exists. Deleting it and creating')
                    self.delete_share_point_pseudo_client(self.sp_object.pseudo_client_name)
                kwargs = {
                    'tenant_url': self.sp_object.tenant_url,
                    'azure_app_id': self.sp_object.azure_app_id,
                    'azure_app_key_id': self.sp_object.azure_app_secret,
                    'azure_directory_id': self.sp_object.azure_app_tenant_id,
                    'is_modern_auth_enabled': self.sp_object.is_modern_auth_enabled,
                    'cloud_region': cloud_region
                }
                if self.sp_object.global_administrator:
                    kwargs.update({
                        "global_administrator": self.sp_object.global_administrator,
                        "global_administrator_password": self.sp_object.global_administrator_password,

                    })
                else:
                    kwargs.update({
                        'user_username': self.sp_object.user_username,
                        'user_password': self.sp_object.user_password
                    })
                if self.sp_object.cert_string:
                    kwargs.update({
                        "cert_string": self.sp_object.cert_string,
                        "cert_password": self.sp_object.cert_password
                    })
                if len(self.sp_object.access_nodes_list) > 1:
                    kwargs['shared_jr_directory'] = self.sp_object.job_results_directory
                if self.sp_object.azure_username:
                    kwargs['azure_username'] = self.sp_object.azure_username
                    kwargs['azure_secret'] = self.sp_object.azure_secret
                self.commcell.clients.add_share_point_client(self.sp_object.pseudo_client_name,
                                                             self.sp_object.server_plan,
                                                             constants.USER_ACCOUNT_SERVICE_TYPE,
                                                             self.sp_object.index_server,
                                                             self.sp_object.access_nodes_list, **kwargs)
            self.log.info("Sharepoint Client has been created successfully")
        except Exception as exception:
            self.log.exception("An error occurred while creating share point client\nError: '{0}'".
                               format(exception))
            raise exception

    def run_manual_discovery(self, wait_for_discovery_to_complete=False):
        """Triggers manual discovery for pseudo client

               Args :

                    wait_for_discovery_to_complete (bool)   --  flag if it needs to wait till the completion of discovery
        """
        try:
            self.log.info('Running manual discovery')
            self.subclient.run_manual_discovery()
            self.log.info("Triggered manual discovery successfully")
            if wait_for_discovery_to_complete:
                if not self.sp_object.machine_name:
                    self.log.exception("Access node host name is not provided to track discovery process")
                    raise Exception("Access node host name is not provided to track discovery process")
                self.wait_for_process_to_complete(
                    machine_name=self.sp_object.machine_name,
                    process_name=sharepointconstants.MANUAL_DISCOVERY_PROCESS_NAME,
                    time_out=5400,
                    poll_interval=60,
                    cvf_file=True)
                self.log.info("Manual Discovery is completed successfully")
        except Exception as exception:
            self.log.exception("An error occurred while running manual discovery")
            raise exception

    def wait_for_process_to_complete(
            self, machine_name, process_name, time_out=600, poll_interval=60, cvf_file=False):
        """"Waits for the specified process to complete

               Args :

                        machine_name    (str)   --  name of the machine

                        process_name    (str)   --  name of the process

                        time_out        (int)   --  maximum wait time for the process to complete

                        poll_interval   (int)   --  poll interval time

                        cvf_file        (str)   --  whether to check for cvf file for the process
        """
        try:
            if cvf_file:
                access_nodes_size = len(self.sp_object.access_nodes_list)
                start_time = time.time()
                result = False
                while (poll_start := time.time()) < start_time + time_out:
                    exited = [False for _ in range(access_nodes_size)]
                    for i, node in enumerate(self.sp_object.access_nodes_list):
                        machine = WindowsMachine(node, self.commcell)
                        if access_nodes_size > 1:
                            jr_path = self.sp_object.job_results_directory
                        else:
                            jr_path = self.get_job_results_dir()
                        parent_path = machine.join_path(jr_path, "SharePointV2", "Backup")
                        backupset_id = str(self.backupset.backupset_id)
                        full_path = machine.join_path(
                            parent_path, file_name := f"{backupset_id}{process_name}.cvf")
                        self.log.info(f"Checking for file {file_name}")
                        exited[i] = bool(full_path not in machine.get_files_in_path(parent_path, recurse=False))
                        self.log.info(f"File exists: {not exited[i]}")
                    if all(exited):
                        result = True
                        break
                    poll_time = min(int(time.time() - poll_start), poll_interval)
                    self.wait_time(poll_interval - poll_time, f'{process_name} is still running')
            else:
                machine = WindowsMachine(machine_name, self.commcell)
                result = machine.wait_for_process_to_exit(process_name, time_out, poll_interval)
            if not result:
                self.log.error(f" {process_name} is not completed in stipulated time:{time_out}")
                raise Exception(f" {process_name} is not completed in stipulated time:{time_out}")
            self.log.info(f"{process_name} is completed successfully")
        except Exception as exception:
            self.log.exception(f"An error occurred while waiting for {process_name} process to complete")
            raise exception

    def get_plan_obj(self, plan_name):
        """"Returns plan object of the given plan name

                Args :

                    plan_name (str)     --  name of the plan

                Returns:

                    plan_obj            --  plan class object

        """
        if self.commcell.plans.has_plan(plan_name):
            return self.commcell.plans.get(plan_name)
        else:
            raise Exception(
                'Plan: "{0}" does not exist in the Commcell'.format('plan_name')
            )

    def check_sites_under_add_webs(self, discovery_type):
        """Checks whether SP content i.e, sites/webs is available under add webs or not.
           If available, returns the discovered sites info and number of discovered sites

                Args :

                      discovery_type (int)   --   type of discovery for content
                                                  for all Associated Web/Sites = 6
                                                  for all Non-Associated Web/Sites = 7

        """
        try:
            self.log.info('Checking browse for content')
            site_dict, no_of_records = self.subclient.browse_for_content(discovery_type)
            if int(no_of_records or 0) > 0:
                self.log.info('Content is available under add webs ')
            else:
                self.log.info('Content is not available under add webs')
            return site_dict, no_of_records
        except Exception as exception:
            self.log.exception("An error occurred while checking SharePoint content")
            raise exception

    def configure_group_for_backup(self, association_group_name, office_365_plan_id):
        """Configures auto association group for backup

                Args:

                        association_group_name (str)   --     name of auto association group

                        office_365_plan_id (id)        --     id of office 365 plan

        """
        try:
            discovery_type = constants.GROUP_ASSOCIATION_CATEGORY_DISCOVERY_TYPE.get(association_group_name)
            self.subclient.configure_group_for_backup(discovery_type, association_group_name, office_365_plan_id)
            self.log.info(f"Configured {association_group_name} group for backup")
        except Exception as exception:
            self.log.exception("An error occurred while configuring group for backup")
            raise exception

    def update_auto_association_group_properties(self, association_group_name, account_status=None,
                                                 office_365_plan_id=None):
        """Updates auto association group properties

                Args:

                        association_group_name (str)   --     name of auto association group

                        account_status (int)           --     0 - Including group in backup
                                                              1 - Removing group from content
                                                              2 - Excluding group from content

                        office_365_plan_id (id)        --     id of office 365 plan

        """
        try:
            discovery_type = constants.GROUP_ASSOCIATION_CATEGORY_DISCOVERY_TYPE.get(association_group_name)
            self.subclient.update_auto_association_group_properties(discovery_type, association_group_name,
                                                                    account_status, office_365_plan_id)
            if account_status is not None:
                if account_status == 0:
                    self.log.info(f"Included {association_group_name} group in backup")
                elif account_status == 1:
                    self.log.info(f"Removed {association_group_name} group from content")
                elif account_status == 2:
                    self.log.info(f"Excluded {association_group_name} group from backup")
            elif office_365_plan_id:
                self.log.info(f"Office 365 plan is updated")

        except Exception as exception:
            self.log.exception("An error occurred while enabling group for backup")
            raise exception

    def validate_additional_service_accounts(self):
        """Validates whether users listed under service accounts or not
        """
        try:
            if self.sp_object.is_modern_auth_enabled or not self.sp_object.global_administrator:
                self.log.info(
                    "Additional service accounts are not created for modern auth enabled or custom configured client")
            else:
                self.log.info('Validating users creation')
                self.backupset.refresh()
                backupset_properties = self.backupset.properties
                accounts = backupset_properties.get("sharepointBackupSet", {}). \
                    get("spOffice365BackupSetProp", {}).get("serviceAccounts", {}).get("accounts", [])
                user_count = 0
                service_type = constants.USER_ACCOUNT_SERVICE_TYPE['Sharepoint Online']
                if accounts:
                    for account in accounts:
                        if account.get("serviceType", -1) == service_type:
                            # validate whether users listed properly or not
                            user_count = user_count + 1
                            username = account.get("userAccount", {}).get("userName", "")
                            user = self.sp_object.sp_api_object.get_user(username)
                            if user:
                                self.log.info("User {0} is validated".format(username))
                    if user_count >= 5:
                        self.log.info("All users created are validated")
                    else:
                        self.log.error("No new users data is found")
                else:
                    self.log.error("Service Accounts information is not found in api response")
                    raise Exception('Service Accounts information is not found')
        except Exception as exception:
            self.log.exception("An error occurred while validating additional service accounts")
            raise exception

    def get_latest_ci_job(self):
        """
        Get latest completed/running Content Indexing job of the client
        Operation Code (opType) for Content Indexing is 113
        """
        ci_job = self.subclient.find_latest_job(job_filter='113')
        return ci_job

    def validate_ci_job(self, job_id):
        """Validate CI jobs
            Args:
                job_id(int)   --  job_id of backup job

            Return:
                int   --   Count of content indexed items
        """

        self.log.info("Validating CI Job")
        self.cvSolr = CVSolr(self.sp_object)
        solr_results = self.cvSolr.create_url_and_get_response(
            {cs.FIELD_JOB_ID: job_id, cs.DOCUMENT_TYPE_PARAM: '1', cs.CONTENT_INDEXING_STATUS: '1'})
        return int(self.cvSolr.get_count_from_json(solr_results.content))

    def suspend_job(self, job, wait_for_job_to_pause=True):
        """Suspends the specified job

            Args:

                job (object)                     --    object of Job

                wait_for_job_to_pause (boolean)  --    wait till job status is changed to Suspended
                                                       default: True

        """
        try:
            self.log.info(f"Suspending job {job.job_id}")
            job.pause(wait_for_job_to_pause)
            self.log.info(f"Job with id {job.job_id} is suspended")
        except Exception as exception:
            self.log.exception("Exception while suspending job: %s", str(exception))
            raise exception

    def resume_job(self, job, wait_for_job_to_resume=True):
        """Resumes the specified job

            Args:

                job (object)                      --    object of Job

                wait_for_job_to_resume (boolean)  --    wait till job status is changed to Running
                                                        default: True

        """
        try:
            self.log.info(f"Resumes job {job.job_id}")
            job.resume(wait_for_job_to_resume)
            self.log.info(f"Job with id {job.job_id} is resumed")
        except Exception as exception:
            self.log.exception("Exception while resumed job: %s", str(exception))
            raise exception

    def kill_job(self, job, wait_for_job_to_kill=True):
        """Kills the specified job

            Args:

                  job (object)                    --    object of Job

                  wait_for_job_to_kill (boolean)  --    wait till job status is changed to Killed
                                                        default: True

        """
        try:
            self.log.info("Killing active job [{0}]".format(job.job_id))
            job.kill(wait_for_job_to_kill)
            time.sleep(15)
            if job.status.lower() == 'killed':
                self.log.info('Job is killed successfully')
            elif job.status.lower() == 'committed':
                self.log.info('Job is committed successfully')
            else:
                raise Exception('Job is not killed with Job status : {0}'.format(job.status.lower()))
        except Exception as exception:
            self.log.exception("Failed to kill job [{0}] with error : {1}".format(job.job_id, exception))

    def delete_share_point_pseudo_client(self, client_name):
        """Performs deletion of share point pseudo client

            Args:

                client_name (str)   --   client name

        """
        try:

            job_helper = self.commcell.job_controller
            for job_id in job_helper.active_jobs(client_name):
                job = self.commcell.job_controller.get(job_id)
                self.kill_job(job)
            if self.sp_object.v1:
                self.log.info("Deleting client [{0}] from client list".format(self.sp_object.backupset_name))
                self.agent.backupsets.delete(self.sp_object.backupset_name)
            else:
                self.log.info("Deleting client [{0}] from client list".format(client_name))
                self.commcell.clients.delete(client_name)
            self.log.info("Client [{0}] has been deleted from the "
                          "client list successfully.".format(
                self.sp_object.backupset_name if self.sp_object.v1 else client_name))
        except Exception as exception:
            self.log.exception("Exception raised in deleting clients()\nError: '{0}'".format(exception))

    def wait_time(self, time_sec=300, log_message=None):
        """Waits for the specified interval of time. Default time = 300 seconds

            Args:

                time_sec (int)      --   time in secs

                log_message (str)   --   message to be displayed

        """
        if log_message is not None:
            self.log.info(str(log_message))
        self.log.info("Sleeping for [%s] seconds", str(time_sec))
        time.sleep(time_sec)

    def check_playback_completion(self, job_id, deleted_objects_count=0):
        """Checks whether playback for the job is completed or not

             Args:

                job_id (int)          --   id of job

                deleted_objects_count(int)  -- total objects deleted before job

        """
        try:
            self.log.info("Check whether play back for the job is completed successfully or not")
            solr = CVSolr(self.sp_object)
            solr.check_all_items_played_successfully(job_id, deleted_objects_count=deleted_objects_count)
        except Exception as exception:
            self.log.exception(f"An error occurred while checking completion of play back for the job {job_id}")
            raise exception

    def run_backup(self, backup_level="incremental", wait_for_job_to_complete=True, deleted_objects_count=0):
        """Runs backup for pseudo client at subclient level

            Args:

                backup_level (str)                     --   type of backup

                wait_for_job_to_complete (boolean)     --   whether to wait till the job gets completed or not

                deleted_objects_count(int)              -- count of deleted objects

            Returns:

                 job (object)                          --   instance of job object

        """
        try:
            self.log.info('Running backup job.')
            self.log.info('Running backup for client %s', self.sp_object.pseudo_client_name)
            job = self.subclient.backup(backup_level=backup_level, advanced_options={"bkpLatestVersion": True})
            self.log.info('Backup job started; job ID: %s', job.job_id)
            if wait_for_job_to_complete:
                self.check_job_status(job)
                if self.sp_object.v1:
                    self.wait_time(log_message="To avoid failures and let the job finish gracefully")
                else:
                    self.check_playback_completion(job.job_id, deleted_objects_count=deleted_objects_count)
            return job
        except Exception as exception:
            self.log.exception("An error occurred while running backup")
            raise exception

    def get_job_advance_details(self, job, retry_count=0):
        """Returns advance job details

             Args:

                 job (object)        --   instance of job object

                 retry_count (int)   --   number of retries tried
        """
        try:
            advanced_job_details = job.advanced_job_details(job.ADVANCED_JOB_DETAILS.BKUP_INFO)
            job_stats = advanced_job_details.get('bkpInfo', {}).get('exchMbInfo', {}).get('SourceMailboxCounters', {})
            if job_stats:
                return job_stats
            else:
                if retry_count > 6:
                    raise Exception('Job Details are empty even after 6 retries')
                self.wait_time(60, f"Job Details are empty. Retrying after {60} secs")
                return self.get_job_advance_details(job, retry_count + 1)
        except Exception as exception:
            self.log.exception("Exception raised while getting job advance details: %s" % str(exception))
            raise exception

    def monitor_job_advance_details(self, job, num_webs, time_out=3600, poll_interval=30):
        """Monitors job status stats till the backup of specified number of webs is finished

             Args:

                    job (object)            --      instance of job object

                    num_webs (int)          --      number of webs

                    time_out (int)          --      time limit(in secs) to monitor job advance details
                                                    Default: 3600 secs

                    poll_interval (int)     --      poll interval to get advance job details
                                                    Default: 30 secs
        """
        try:
            current_time = time.time()
            end_time = current_time + time_out
            while current_time <= end_time:
                job_advance_details = self.get_job_advance_details(job)
                committed_webs = len(self.get_committed_webs_list(job.job_id))
                self.log.info(f"Job Advance Details for job {job.job_id}: {job_advance_details}")
                if job_advance_details.get("TotalMBs", "") < num_webs:
                    self.log.exception("Expected number of sites are not associated for backup")
                    raise Exception("Expected number of sites are not associated for backup")
                elif committed_webs >= num_webs:
                    self.log.info("Monitoring of job advance details is done")
                    return committed_webs
                self.wait_time(poll_interval, f"Waiting for backup of {num_webs} webs to complete")
                current_time = time.time()
            self.log.info("Monitoring of job advance details is not completed under stipulated time %d ", time_out)
        except Exception as exception:
            self.log.exception("Exception while monitoring advance details of job: %s", str(exception))
            raise exception

    def validate_num_webs_in_backup(self, job, num_webs):
        """Validates number of webs picked up for backup

             Args:

                    job (object)            --      instance of job object

                    num_webs (int)          --      number of webs that should be picked up in backup

        """
        try:
            job_advance_details = self.get_job_advance_details(job)
            self.log.info(f"Job Advance Details for job {job.job_id}: {job_advance_details}")
            api_num_webs = job_advance_details.get("TotalMBs", "")
            if api_num_webs == num_webs:
                self.log.info(f"The backup job has picked up {num_webs} webs for backup as expected")
            else:
                self.log.exception(f"The backup job has picked up {api_num_webs} webs instead of {num_webs} webs")
                raise Exception(f"The backup job has picked up {api_num_webs} webs instead of {num_webs} webs")
        except Exception as exception:
            self.log.exception("Exception while validating number of webs picked up for backup: %s", str(exception))
            raise exception

    def browse_for_sp_sites(self, time_out=5400, poll_interval=30, paths=None):
        """Checks whether SP content i.e, sites/webs are available under
        add webs or not and waits till content is available under add webs

            Args:
                    time_out (int)          --      time limit in secs

                    poll_interval (int)     --      poll interval to check content under add webs

        """
        try:
            # Discovery Type =7,  (for all Web/Sites) Associated or Non-Associated Content
            if self.sp_object.v1:
                self.subclient.discover_sharepoint_sites(paths)
            else:
                discovery_type = 7
                current_time = time.time()
                end_time = current_time + time_out
                self.site_user_account_info = {}
                while current_time <= end_time:
                    site_dict, no_of_records = self.check_sites_under_add_webs(discovery_type)
                    if site_dict:
                        if self.sp_object.site_url in site_dict.keys():
                            self.site_user_account_info[self.sp_object.site_url] = site_dict[
                                self.sp_object.site_url].get(
                                'userAccountInfo', {})
                            return no_of_records
                        else:
                            self.log.info("Site is not yet discovered to associate")
                            self.wait_time(60, "waiting for site to get discovered")
                    time.sleep(poll_interval)
                    current_time = time.time()
                self.log.info("Browse for content is not available under stipulated time %d ", time_out)
                raise Exception("Browse for content is not available under add webs")
        except Exception as exception:
            raise Exception("Exception raised while waiting for browse for content: %s" % str(exception))

    def get_sites_user_account_info(self, sites_list):
        """Returns dictionary of user account information of specified sites

            Args:

                sites_list (list)          --      list of site urls

        """
        try:
            # Discovery Type =7,  (for all Web/Sites) Associated or Non-Associated Content
            discovery_type = 7
            site_dict, no_of_records = self.check_sites_under_add_webs(discovery_type)
            site_user_account_info = {}
            if site_dict:
                for site in sites_list:
                    if site in site_dict.keys():
                        site_user_account_info[site] = site_dict[site].get('userAccountInfo', {})
                    else:
                        self.log.exception(f"{site} is not discovered. Unable to get site user account information")
                        raise Exception(f"{site} is not discovered. Unable to get site user account information")
                return site_user_account_info
            else:
                self.log.exception(f"No sites are discovered.Please run discovery/wait for discovery to complete")
                raise Exception(f"No sites are discovered.Please run discovery/wait for discovery to complete")
        except Exception as exception:
            raise Exception("Exception raised while getting user account information for sites: %s" % str(exception))

    def associate_content_for_backup(self, office_365_plan_id=None, content=None):
        """Associates some content for backup

                Args:

                    office_365_plan_id (int)     --    id of office 365 plan

                    content (list)               --     list of path to be associated with backupset
                    Example : ["https://cvautomation.sharepoint.com/sites/TestSite"]

        """
        try:
            self.wait_time(30, "waiting to associate content")
            # A backup is run automatically when a pseudo client is created, So kill that job
            self.log.info("Kill all active jobs of pseudo client")
            job_helper = self.commcell.job_controller
            for job_id in job_helper.active_jobs(self.sp_object.pseudo_client_name):
                job = self.commcell.job_controller.get(job_id)
                self.kill_job(job)
            if self.sp_object.v1:
                content_json = [{"sharepointContents": {
                    "ContentPath": '<EVGui_SharePointItem fullPath=\"' + val + '\" siteCollectionPath=\"' + val + '\" databaseInstance=\"1\" objectType=\"3\" contentPath=\"\\MB\\' + val + '\" relativePath=\"' + val + '\" />'}}
                    for val in
                    content]
                self.subclient.content = content_json
            else:
                self.associates_sites_for_backup(sites_user_account_info=self.site_user_account_info,
                                                 office_365_plan_id=office_365_plan_id)
                # Discovery Type = 6, (for all Web/Sites) Associated Content
                discovery_type = 6
                site_dict, no_of_records = self.subclient.browse_for_content(discovery_type)
                if no_of_records > 0:
                    self.log.info(f"{self.sp_object.site_url} site is associated for backup")
                    self.log.info("{0} records are associated for back up".format(no_of_records))
                else:
                    self.log.exception("Error in displaying content for backup")
                    raise Exception("Error in displaying content for backup")
        except Exception as exception:
            self.log.exception("Exception while associating content for backup: %s", str(exception))
            raise exception

    def associates_sites_for_backup(self, sites_list=None, sites_user_account_info=None, office_365_plan_id=None):
        """Associates sites for backup

            Args:

                sites_list (dict)                  --    list of sites to be associated for backup

                sites_user_account_info (dict)     --    dictionary of user account information of sites to be
                                                         associated for backup

                office_365_plan_id (int)           --    id of office 365 plan
        """
        try:
            if sites_list:
                sites_user_account_info = self.get_sites_user_account_info(sites_list)
            elif not sites_user_account_info:
                self.log.exception("Please provide either sites list or sites user account info to associate sites")
                raise Exception("Please provide either sites list or sites user account info to associate sites")
            self.subclient.update_sites_association_properties(
                site_user_accounts_list=list(sites_user_account_info.values()),
                operation=1,
                plan_id=office_365_plan_id)
            site_dict, no_of_records = self.subclient.browse_for_content(discovery_type=6)
            sites_list = list(sites_user_account_info.keys())
            associated_sites_list = list(site_dict.keys())
            for site in sites_list:
                if site in associated_sites_list:
                    self.log.info(f"{site} site is associated for backup")
                else:
                    self.log.exception(f"{site} site is not associated for backup as expected")
                    raise Exception(f"{site} site is not associated for backup as expected")
        except Exception as exception:
            self.log.exception("Exception while associating content for backup: %s", str(exception))
            raise exception

    def include_sites_in_backup(self, sites_list):
        """Enables sites for backup

            Args:

                 sites_list (dict)                  --    list of sites to be included in backup

        """
        try:
            sites_user_account_info = self.get_sites_user_account_info(sites_list)
            self.subclient.update_sites_association_properties(
                site_user_accounts_list=list(sites_user_account_info.values()),
                operation=2)
            site_dict, no_of_records = self.subclient.browse_for_content(discovery_type=6)
            sites_list = list(sites_user_account_info.keys())
            for site in sites_list:
                if site_dict[site]['accountStatus'] == 0 and site_dict[site]['userAccountInfo']['commonFlags'] == 4:
                    self.log.info(f"{site} site is enabled for backup")
                else:
                    self.log.exception(f"{site} site is not enabled for backup as expected")
                    raise Exception(f"{site} site is not enabled for backup as expected")
        except Exception as exception:
            self.log.exception("Exception while enabling content for backup: %s", str(exception))
            raise exception

    def exclude_sites_from_backup(self, sites_list):
        """Disables sites from backup

            Args:

               sites_list (dict)            --    list of sites to be excluded from backup

        """
        try:
            sites_user_account_info = self.get_sites_user_account_info(sites_list)
            self.subclient.update_sites_association_properties(
                site_user_accounts_list=list(sites_user_account_info.values()),
                operation=3)
            site_dict, no_of_records = self.subclient.browse_for_content(discovery_type=6)
            sites_list = list(sites_user_account_info.keys())
            for site in sites_list:
                if site_dict[site]['accountStatus'] == 2 and site_dict[site]['userAccountInfo']['commonFlags'] == 4:
                    self.log.info(f"{site} site is disabled for backup")
                else:
                    self.log.exception(f"{site} site is not disabled for backup as expected")
                    raise Exception(f"{site} site is not disabled for backup as expected")
        except Exception as exception:
            self.log.exception("Exception while disabling content for backup: %s", str(exception))
            raise exception

    def remove_sites_from_backup_content(self, sites_list):
        """Removes sites from backup content

            Args:

                sites_list (dict)              --    list of sites to be removed from backup content

        """
        try:
            sites_user_account_info = self.get_sites_user_account_info(sites_list)
            self.subclient.update_sites_association_properties(
                site_user_accounts_list=list(sites_user_account_info.values()),
                operation=4)
            site_dict, no_of_records = self.subclient.browse_for_content(discovery_type=6)
            sites_list = list(sites_user_account_info.keys())
            removed_sites_list = list(site_dict.keys())
            for site in sites_list:
                if site in removed_sites_list:
                    self.log.exception(f"{site} site is not removed from backup content as expected")
                    raise Exception(f"{site} site is not removed from backup content as expected")
                else:
                    self.log.info(f"{site} site is removed from backup content")
            time.sleep(30)
        except Exception as exception:
            self.log.exception("Exception while removing sites from backup content: %s", str(exception))
            raise exception

    def get_backup_reference_time_of_associated_webs(self):
        """Returns backup reference time of all associated webs
        """
        try:
            # Discovery Type = 6, (for all Sites/Subsites) Associated Content
            discovery_type = 6
            backup_reference_time_dict = {}
            site_dict, no_of_records = self.subclient.browse_for_content(discovery_type)
            for site, site_props in site_dict.items():
                backup_reference_time_dict[site] = site_props.get("userAccountInfo", {}).get("lastBackupJobRanTime",
                                                                                             {}).get("time")
            return backup_reference_time_dict
        except Exception as exception:
            self.log.exception("Exception while getting backup reference time of all associated webs: %s",
                               str(exception))
            raise exception

    def get_committed_webs_list(self, job_id):
        """Returns the list of committed webs

            Args:

                job_id (int)            --      backup job ID to get list of committed webs list

            Returns:

                committed_webs (list)   --      list of committed webs

        """
        try:
            job_results_dir = self.get_job_results_dir(full_path=True)
            machine_obj = Machine(self.sp_object.access_nodes_list[0], self.commcell)
            for file in machine_obj.get_files_in_path(folder_path=job_results_dir + '\\WebsTracker', recurse=False):
                if str(job_id) + "ProcessedWebsInJob" in file:
                    processed_webs_list = [web.split(":")[0] for web in machine_obj.read_file(file).split("\n") if web !='']
                    break
            else:
                raise Exception("Processed Webs file is not present for specified job at Shared JR. Please "
                                "check if registry key 'bKeep.Processed.Webs.File' is enabled on access node or not")
            committed_webs = []
            for web_id in processed_webs_list:
                web_folder = job_results_dir + '\\coord\\' + web_id
                self.log.info(f"Reading site url from {web_folder} path")
                if machine_obj.check_directory_exists(directory_path=web_folder):
                    xml_generic = machine_obj.read_file(web_folder + '\\CollectTot.cvf')
                    web_properties = ElementTree.fromstring(xml_generic)
                    committed_webs.append(web_properties.attrib.get('fullPath'))
                else:
                    raise Exception("Committed web coord folder is not present at Shared JR to get site full path")
            self.log.info(f"Committed webs in job {job_id} are {committed_webs}")
            return committed_webs
        except Exception as exception:
            self.log.exception("Exception while getting committed webs list: %s", str(exception))
            raise exception

    def get_uncommitted_webs_list(self, total_webs, committed_webs):
        """Returns the list of committed webs

            Args:

                total_webs (list)       --      list of total webs selected for backup

                committed_webs (list)   --      list of committed webs

            Returns:

                uncommitted_webs (list)   --      list of uncommitted webs

        """
        return [web for web in total_webs if web not in committed_webs]

    def validate_backup_reference_time(self, uncommited_sites_list=None):
        """Validates backup reference time for committed and uncommitted webs

            Args:

               uncommited_sites_list (list)     --    list of uncommitted sites in backup

        """
        if uncommited_sites_list is None:
            uncommited_sites_list = []
        try:
            backup_reference_time_dict = self.get_backup_reference_time_of_associated_webs()
            for site_url, backup_reference_time in backup_reference_time_dict.items():
                if site_url in uncommited_sites_list:
                    if backup_reference_time != 0:
                        self.log.exception(
                            f"Backup reference time of {site_url} is updated though task was not completed")
                        raise Exception(f"Backup reference time of {site_url} is updated though task was not completed")
                    else:
                        self.log.info(f"The site {site_url} is not committed as expected")
                else:
                    if backup_reference_time > 0:
                        self.log.info(f"The backup reference time of {site_url} is {backup_reference_time}")
                    else:
                        self.log.exception(f"Backup reference time of {site_url} is not updated")
                        raise Exception(f"Backup reference time of {site_url} is not updated")
        except Exception as exception:
            self.log.exception("Exception while validating backup reference time: %s", str(exception))
            raise exception

    def validate_restartability(self, job, completed_webs, to_be_processsed_webs):
        """Validates count of completed webs and to be processed webs with current status of webs in the job

                Args:

                      job (object)                  --      instance of job object

                      completed_webs (int)          --      number of backed up webs

                      to_be_processsed_webs (int)   --      number of webs to be picked up after resume

            """
        try:
            job_adv_details = self.get_job_advance_details(job)
            api_completed_webs = job_adv_details.get("SuccessfulMBs") + job_adv_details.get("SuccessfulWithWarningMBs")
            api_to_be_processed_webs = job_adv_details.get("ToBeProcessedMBs")
            self.log.info(f"Completed webs: {completed_webs}\n To be processed webs: {to_be_processsed_webs}")
            self.log.info(f"API completed webs: {api_completed_webs}\n API to be processed webs: "
                          f"{api_to_be_processed_webs}")
            if to_be_processsed_webs == api_to_be_processed_webs and completed_webs == api_completed_webs:
                self.log.info("Validated restartability successfully")
            else:
                self.log.info("Completed webs and to be processed webs count is not matched")
        except Exception as exception:
            self.log.exception("Exception while validating restartability: %s", str(exception))
            raise exception

    def suspend_resume_job(self, total_webs, num_webs_to_be_completed):
        """Suspends and resumes job based on provided number of webs to be completed and waits till the backup job is
           completed
           Example: total_webs = 5 and num_webs_to_be_completed = 2
                    For every completion of 2 webs, suspends the backup job & validates restartability till all the webs
                    are backed up

               Args:

                     total_webs (int)                 --      total number of webs in backup job

                     num_webs_to_be_completed (int)   --      number of webs to be completed everytime job is
                                                              suspended and resumed

        """
        try:
            """Setting number of streams to number of webs to be completed to suspend job for below reasons
            1. Because of multi-streaming all the webs are being processed very quickly. 
            2. With the change to update CS with site stats for every 15 mins, 
            the API is unable to fetch the exact status of processed webs even though they are backed up.
            Therefore, to not let backup complete in 15 mins,  restricting streams count for only suspend and resume case"""
            self.subclient.data_readers = num_webs_to_be_completed
            job = self.run_backup(wait_for_job_to_complete=False)
            for to_be_completed_num_webs in range(num_webs_to_be_completed, total_webs, num_webs_to_be_completed):
                self.wait_time(30, f"Waiting for backup to start")
                completed_num_webs = self.monitor_job_advance_details(job, to_be_completed_num_webs)
                to_be_processsed_webs = total_webs - completed_num_webs
                self.suspend_job(job)
                self.wait_time(30, f"Waiting before resuming backup job")
                self.resume_job(job)
                self.validate_restartability(job, completed_num_webs, to_be_processsed_webs)
            self.check_job_status(job)
            # Due to the support of allowing partial backup, can't validate play back for suspend and resume case as
            # number of objects in the job will be greater than number of items on index.
            self.wait_time(120, "Waiting for play back to finish")
        except Exception as exception:
            self.log.exception("Exception while suspending and resuming job: %s", str(exception))
            raise exception

    def check_job_status(self, job):
        """Checks the status of job until it is finished and raises exception on pending, failure etc.

                Args:

                    job (Object of job class of CVPySDK)

        """
        try:
            self.log.info('%s running for subclient %s with job id: %s', job.job_type,
                          self.subclient.subclient_name, job.job_id)

            if not job.wait_for_completion(timeout=120):
                self.log.exception("Pending Reason %s", job.pending_reason)
                raise Exception("Pending Reason %s", job.pending_reason)
            if job.status == "Completed w/ one or more errors" or job.state == "Completed w/ one or more errors":
                self.log.info('%s job completed successfully.', job.job_type)
            elif not (job.status.lower() == "completed" or job.state.lower() == "completed"):
                raise Exception(
                    "Job " + str(job.job_id) + "is not completed and has job status: " \
                    + job.status
                )
            self.log.info('%s job completed successfully.', job.job_type)
        except Exception as exception:
            self.log.exception("Exception while checking job status: %s", str(exception))
            raise exception

    def update_azure_storage_details(self):
        """Updates azure storage details in SharePoint backupset properties
        """
        try:
            self.backupset.refresh()
            if self.sp_object.azure_username and self.sp_object.azure_secret:
                azure_secret = b64encode(self.sp_object.azure_secret.encode()).decode()
                service_type = constants.USER_ACCOUNT_SERVICE_TYPE["Sharepoint Azure Storage"]
                azure_account_information = {
                    "serviceType": service_type,
                    "userAccount": {
                        "password": azure_secret,
                        "userName": self.sp_object.azure_username
                    }
                }
                self.backupset.azure_storage_details = azure_account_information
                self.wait_time(60, "Waiting to get backupset properties updated")
                self.log.info("Azure storage details are updated for restore in backupset properties")
            else:
                raise Exception("Please initialize azure storage details")
        except Exception as exception:
            self.log.exception("Exception while updating azure storage details: %s", str(exception))
            raise exception

    def is_azure_storage_account_available(self):
        """Checks whether azure storage account is present in backupset properties or not"""
        try:
            self.log.info("Checking if azure storage details present")
            accounts = self.backupset.properties.get("sharepointBackupSet", {}). \
                get("spOffice365BackupSetProp", {}).get("serviceAccounts", {}).get("accounts", [])
            service_type = constants.USER_ACCOUNT_SERVICE_TYPE['Sharepoint Azure Storage']
            if accounts:
                for account in accounts:
                    if account.get("serviceType", -1) == service_type:
                        return True
                else:
                    return False
        except Exception as exception:
            self.log.exception("An error occurred while checking whether azure storage account is present or not")
            raise exception

    def get_log_folder_for_node(self, access_node):
        """Gets the log folder for the access node

            Args:
                access_node (str)       :   Name of the access node
        """
        if not self.tcinputs.get('LogFolder', {}).get(access_node):
            raise Exception("Log folder for the AN needs to be passed in the inputs. Value at regkey: "
                            r"HKLM\SOFTWARE\CommVault Systems\Galaxy\[Instance #]\Event Manager"
                            r"\dEVLOGDIR. Expected in an object at 'LogFolder' in tcinputs with AN name "
                            "as key and log file path as value")
        return self.tcinputs['LogFolder'][access_node]

    def identify_coord_node_for_restore(self, job_id):
        """Identifies the coordinator node for the restore job

            Args:
                job_id  (str)               :   Job ID of the restore job

            Returns:
                tuple:
                    access_node (str)       :   Coordinator node,
                    file_path   (str)       :   Path to log file
        """
        logfile_name = 'CVSPRestore.log'
        try:
            self.log.info(f"Identifying coord node for the job {job_id}")
            for access_node in self.sp_object.access_nodes_list:
                wm_obj = WindowsMachine(access_node, self.commcell)
                log_folder = self.get_log_folder_for_node(access_node)
                try:
                    file_path = wm_obj.join_path(log_folder, logfile_name)
                    file_data = wm_obj.read_file(file_path)
                except Exception as ie:
                    self.log.error(f"{logfile_name} not found in {access_node}: {ie}")
                    continue
                if re.search(f"{job_id}.+CVSPRestore has started", file_data):
                    self.log.info(f"Found coord node {access_node} for the job {job_id}")
                    return access_node, file_path
            raise Exception(f"Unable to find coordinator for restore job {job_id}")
        except Exception as e:
            self.log.error(f"Error while trying to identify coord node: {e}")
            raise e

    def validate_restore_on_multiple_nodes(self, job_id):
        """Validates whether restore is running on multiple access nodes or not

            Args:
                job_id  (str)       :   Job ID of the restore job
        """
        try:
            self.log.info(f"Validating restore on multiple access nodes")
            coord_node, file_path = self.identify_coord_node_for_restore(job_id)
            wm_obj = WindowsMachine(coord_node, self.commcell)
            lines_in_file = wm_obj.read_file(file_path).split('\n')

            webs_sent, webs_summary = {}, {}
            for line in lines_in_file:
                matches = re.search(str(job_id) + r".+Sending Web \[(.+)].+ to agent \[(.+)]", line)
                if matches:
                    webs_sent[matches.group(1).strip()] = matches.group(2).strip()
                    continue

                matches = re.search(str(job_id) + r".+Web (.+) +--> +(.+) +--> +Agent (.+)", line)
                if matches:
                    webs_summary[matches.group(1).strip()] = [matches.group(2).strip(), matches.group(3).strip()]

            if (webs_sent_count := len(webs_sent)) != (webs_fin_count := len(webs_summary)):
                raise Exception(f"{webs_sent_count} webs were sent but {webs_fin_count} were returned")

            for web, [status, _] in webs_summary.items():
                if status.lower() != "restored":
                    raise Exception(f"Status for {web}: {status}")
            for web in webs_sent:
                if webs_sent[web] != webs_summary[web][1]:
                    raise Exception(
                        f"{web} was sent to {webs_sent[web]} but reported by {webs_summary[web][1]}")

            unique_nodes = len(set(list(webs_sent.values()) + [x[1] for x in webs_summary.values()]))
            if unique_nodes != len(self.sp_object.access_nodes_list):
                raise Exception(f"{unique_nodes} nodes were used for restore for pseudoclient "
                                f"with {len(self.sp_object.access_nodes_list)} nodes")
            self.log.info(f"Restore on multiple access nodes is validated")
        except Exception as e:
            self.log.error(f"Error while validating restore on multiple access nodes: {e}")
            raise e

    def run_restore(self, multiple_access_nodes=False, **kwargs):
        """Runs a restore job on the specified SharePoint client

            Args:

                multiple_access_nodes   (bool)  --      whether to validate restore is running on
                                                        multiple access nodes

            Kwargs:

                paths (list)       --     list of sites or webs to be restored
                    Example: [
                        "MB\\https://cvdevtenant.sharepoint.com/sites/TestSite\\/\\Shared Documents\\TestFolder",
                        "MB\\https://cvdevtenant.sharepoint.com/sites/TestSite\\/\\Lists\\TestList"
                        ]

        """
        job = None
        try:
            self.log.info("Triggering Restore Job")
            if kwargs.get("destination_site", ""):
                self.log.info('Setting source path for OOP restore as %s', kwargs.get("paths", []))
                destination_site = kwargs.get("destination_site")
                oop_destination = ('<EVGui_SharePointItem fullPath=\"' + destination_site
                                   + '\" siteCollectionPath=\"' + destination_site
                                   + '\" Reserved_1=\"STS\" Reserved_2=\"'
                                   + kwargs.get("destination_site_title")
                                   + '\" objectType=\"4\" webPath=\"' + destination_site
                                   + '\" contentPath=\"\\MB\\' + destination_site
                                   + '\" relativePath=\"/\" />')

                self.log.info(
                    'Setting destination path for OOP restore as %s' % str(oop_destination))
                job = self.subclient.out_of_place_restore(kwargs.get("paths"), oop_destination)
            else:
                job = self.subclient.restore_in_place(**kwargs)
            self.log.info(
                "Waiting For Completion Of Restore Job With Job ID:{0}".format(job.job_id))
            self.check_job_status(job)
        except Exception as exception:
            if exception and self.restore_retry_count < 5:
                self.log.error("Error in triggering restore job {0} Retrying once again".format(exception))
                self.wait_time(30, "Waiting to retry restore")
                self.restore_retry_count = self.restore_retry_count + 1
                self.run_restore(**kwargs)
            else:
                error_message = "Error in triggering restore job {0} and retry count [{1}] exceeded" \
                    .format(exception, self.restore_retry_count)
                self.log.error(error_message)
                raise error_message
        if multiple_access_nodes:
            self.validate_restore_on_multiple_nodes(job.job_id)
        return job

    def disk_restore(self,
                     destination_path,
                     destination_client,
                     disk_restore_type,
                     paths=None,
                     overwrite=True):
        """Runs disk restore for subclient object of cvpysdk

            Args:

                    destination_path (str)   --  destination path for restore

                    destination_client (str) --  destination client for restore

                    disk_restore_type (int)  --  type of disk restore

                    paths (list)             --  sharePoint library/list path to restore

                    overwrite (boolean)      --  set it True to restore with overwrite
                                                 Default: True

        """
        if paths is None:
            paths = [r"\MB"]
        try:
            if not self.commcell.clients.has_client(destination_client.lower()):
                raise Exception("Client name %s not found" % str(destination_client.lower()))
            remote_machine = Machine(destination_client, self.commcell)
            remote_machine.remove_directory(destination_path, 0)
            job = self.subclient.disk_restore(
                paths=paths, destination_client=destination_client,
                destination_path=destination_path, disk_restore_type=disk_restore_type,
                overwrite=overwrite, in_place=False)
            self.log.info('Disk Restore job started; job ID: %s' % str(job.job_id))
            self.check_job_status(job)
            return job
        except Exception as exception:
            self.log.exception("An error occurred while running disk restore")
            raise exception

    def process_index_retention_rules(self, index_server_client_id):
        """Makes API call to process index retention rules

          Args:
                index_server_client_id (int)  --  client id of index server

        """
        try:
            self.log.info("Processing index rentention rules")
            self.subclient.process_index_retention_rules(index_server_client_id)
            self.wait_time(120, "Waiting for retention rules to process")
            self.log.info("Processed index retention rules")
        except Exception as exception:
            self.log.exception("An error occurred while processing index retention rules")
            raise exception

    def delete_backupset(self):
        """
        Deletes the backupset present in the client
            Raises:
                If fails to delete the backupset
        """
        try:
            self.log.info(f"Trying to delete backupset with name [{self.sp_object.backupset_name}]")
            if self._agent is None:
                self._agent = self.client.agents.get(constants.AGENT_NAME)
            self.agent.backupsets.delete(self.sp_object.backupset_name)
            self.log.info(f"Successfully deleted backupset with name [{self.sp_object.backupset_name}]")
        except:
            self.log.exception("An error occurred while deleting the backupset")

    def delete_sharepoint_backup_data(self, guids, search_string=None, folder_delete=False, search_and_delete_all=False):
        """
        Delete data by their CVObjectGUIDs if selecting individual items
                         or SPWebGUID if searching by keyword and deleting all
            Args:
                guids (list)                    :   list of CVObjectGUID or SPWebGUID of the object/site item to delete
                search_string (str)             :   Search string to delete using "Search and delete all" using CVObjectGUID
                folder_delete (bool)            :   True if a folder is to be deleted for which a BULK JOB is triggered
                search_and_delete_all (bool)    :   True if "Search and delete all" is being done
        """
        try:
            job = self.subclient.delete_data(guids, search_string, folder_delete, search_and_delete_all)
            self.log.info(f"Delete data was successful for {guids}")
            return job
        except Exception as e:
            self.log.error(f'Error while trying to delete data from SharePoint V2 client when folder_delete '
                           f'is {folder_delete} and search and delete all is {search_and_delete_all}: {e}')
            raise Exception("Delete data operation failed")

    def update_max_streams(self, streams_count):
        """Updates the max streams count for the pseudoclient

            Args:

                streams_count    (int)   :   New value for Max streams

        """
        try:
            self.subclient.data_readers = streams_count
            self.log.info(f"Max streams count has been updated to {streams_count}")
        except Exception as e:
            self.log.exception(f'Error while updating max streams count: {e}')
            raise e
