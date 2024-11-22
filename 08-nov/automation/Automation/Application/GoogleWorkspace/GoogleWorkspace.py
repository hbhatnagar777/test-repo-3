import time

from google.oauth2 import service_account
from googleapiclient.discovery import build
from AutomationUtils import logger
from Application.CloudApps.exception import CVCloudException
from AutomationUtils.config import get_config
from . import constants
from .solr_helper import SolrHelper
from AutomationUtils.database_helper import CommServDatabase

GOOGLE_CONFIG = get_config().DynamicIndex.Activate.GoogleWorkspace


class GoogleWorkspace:
    """Class for Google Workspace Common functions"""

    def __init__(self, commcell):
        self._solr_helper = None
        self.client_name = None
        self.log = logger.get_log()
        self.log.info('Logger initialized for Google Client')
        self.commcell = commcell
        self.client = None
        self.app_name = self.__class__.__name__  # Used for exception list
        self.csdb = CommServDatabase(self.commcell)

    @property
    def client(self):
        """Treats the client as a read-only attribute."""
        try:
            if not self._client:
                if not self.client_name or not self.commcell.clients.has_client(self.client_name):
                    raise Exception("Client does not exist. Check the client name")
                self._client = self.commcell.clients.get(self.client_name)
            return self._client
        except Exception as err:
            self.log.exception("Exception while getting client object.")
            raise Exception(err)

    @property
    def agent(self):
        if self.client is not None:
            return self.client.agents.get(constants.AGENT_NAME)
        else:
            raise Exception("Please create valid client first")

    @property
    def backupset(self):
        """Returns backupset commcell object."""
        if self.client is not None:
            agent = self.client.agents.get(constants.AGENT_NAME)
            return agent.backupsets.get(constants.BACKUPSET_NAME)
        else:
            raise Exception('Please create client')

    @property
    def subclient(self):
        """Returns subclient commcell object"""
        return self.backupset.subclients.get(constants.SUBCLIENT_NAME)

    @property
    def solr_helper(self):
        """Returns solr helper object"""
        if self._solr_helper is None:
            return SolrHelper(self)
        return self._solr_helper

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

    def delete_client(self, client_name):
        """Performs deletion of Google client

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
            self.log.info("Client [{0}] has been deleted from the "
                          "client list successfully.".format(client_name))
        except Exception as exception:
            self.log.exception("Exception raised in deleting clients()\nError: '{0}'".format(exception))
            raise Exception

    def _create_client(self, plan_name, client_name, indexserver,
                       service_account_details, credential_name, instance_type, **kwargs):
        """
        Creates a Google Client

        Args:
            - plan_name (str): Name of server plan
            - client_name (str): The name to be assigned to the client.
            - client_group_name (str): The group name to which the client belongs.
            - indexserver (str): The index server address used for the client.
            - service_account_details (dict): A dictionary containing service account details
              required for authentication and authorization.
            - credential_name (str): Credential Name that created in Credential Vault.
            - jr_path (str): Job Results Dir path.
            - instance_type (int): Type of Google client
        """
        try:
            self.client_name = client_name
            if self.commcell.clients.has_client(client_name):
                self.log.info('Client already exists. Deleting it!')
                self.delete_client(client_name)
            self.commcell.clients.add_googleworkspace_client(plan_name, client_name, indexserver,
                                                             service_account_details, credential_name,
                                                             instance_type=instance_type, **kwargs)
            self.log.info('Client Created Successfully')
            self._solr_helper = SolrHelper(self)
        except Exception as err:
            self.log.exception("Exception while creating client")
            raise Exception(err)

    def _create_association(self, users, plan):
        """
        Adds content to client.

        Args:
            - users (list) - List of users needs to add into client.
            - plan (str) - Google Workspace Plan needs to associate with users.
        """
        try:
            self.log.info(f'Adding following users \n\t {users}')
            self.subclient.add_users_v2(users=users, plan_name=plan)
        except Exception as err:
            self.log.exception("Exception while adding content")
            raise Exception(err)

    def _validate_discovered_users(self, api_obj):
        """
        Validates the discovered users

        Args:
            - api_obj : GoogleWorkspaceAPI object.
        """
        try:
            flag, user_accounts = self.subclient.verify_user_discovery_v2()

            discovered_users = [user['smtpAddress'] for user in user_accounts]
            self.log.info(f"Discovered Users : {discovered_users}")

            api_users = [user['primaryEmail'] for user in api_obj.users]
            self.log.info(f"Actual Users : {api_users}")

            self.log.info('Validating Discovered Users')
            for user in api_users:
                if user not in discovered_users:
                    raise CVCloudException(self.app_name, '501', f'[{user}] not found in Discovered Users list')

            self.log.info('Discovery Successfully Completed')
        except Exception as err:
            self.log.exception("Exception while validating discovered users")
            raise Exception(err)

    def _run_backup(self, users_list, is_mailbox=False):
        """Runs backup for google client
        Args:
            users_list (list) : list of users to run backup
            is_mailbox (boolean) : determines if GMAIL mailbox or not
        """
        try:
            if users_list is None:
                self.log.info("Running Client Level Backup")
                backup_job = self.subclient.run_client_level_backup(is_mailbox)
            else:
                self.log.info(f"Running User Level Backup for Users : [{users_list}]")
                backup_job = self.subclient.run_user_level_backup(users_list, is_mailbox)

            self.log.info(f'Job triggered successfully. Job ID : {backup_job.job_id}')
            backup_job.wait_for_completion()

            if backup_job.summary['status'].lower() != 'completed':
                self.log.info(f"Backup Job didn't completed successfully. Job Status : {backup_job.summary['status']}")
                raise Exception

            self.log.info("Job completed Successfully!")
            self.log.info(f"Job details are : {backup_job.summary}")
            self.backup_count = int(backup_job.summary['totalNumOfFiles'])

            solr_count = self.solr_helper.check_all_items_played_successfully(select_dict={'JobId': backup_job.job_id,
                                                                                           'DocumentType':
                                                                                               constants.GMAIL_MESSAGE_DOCUMENT_TYPE if is_mailbox
                                                                                               else constants.GDRIVE_FILE_DOCUMENT_TYPE})
            self.log.info(f"Documents Count from Backup : {self.backup_count}")
            self.log.info(f"Documents Count from Index : {solr_count}")

            if int(solr_count) != self.backup_count:
                self.log.info(f"Backup Job Count and Index Count doesn't match")
                raise Exception
            self.log.info(f"Backup Job Count and Index Count Matched!")

        except:
            self.log.exception("Backup operation failed. ")
            raise Exception

    def _run_restore(self, users_list, **kwargs):
        """
                Runs Restore for Google client
                        Args:
                            users_list (list) :  List of SMTP addresses of users
                            **kwargs (dict) : Additional parameters
                                overwrite (bool) : unconditional overwrite files during restore (default: False)
                                restore_as_copy (bool) : restore files as copy during restore (default: False)
                                skip_file_permissions (bool) : If True, restore of file permissions are skipped (default: False)
        """
        try:
            self.log.info(f"Running Restore for these users {users_list}")
            restore_job = self.subclient.in_place_restore_v2(users_list, **kwargs)
            self.log.info(f"Restore Job ID : {restore_job.job_id}")
            restore_job.wait_for_completion()
            if restore_job.status.lower() != 'completed':
                self.log.info(
                    f"Restore Job didn't completed successfully. Job Status : {restore_job.summary['status']}")
                raise Exception

            job_details = restore_job.details['jobDetail']
            self.log.info("Job completed Successfully!")
            self.log.info(f"Job details are : {job_details}")

            if self.backup_count != int(job_details['detailInfo']['numOfObjects']):
                self.log.info(f"Backup count and Restore count is not matched!!")
                raise Exception

            self.log.info('Restore Job Successful!')
        except:
            self.log.exception("Restore operation failed. ")
            raise Exception

    @client.setter
    def client(self, value):
        self._client = value


class GoogleDrive(GoogleWorkspace):
    """Class for Google Drive Operations"""

    def __init__(self, commcell):
        super().__init__(commcell)
        self.api_obj = GdriveAPI()

    @property
    def client_properties(self):
        """Return Google Drive client properties"""
        return self.agent.instances.get(constants.GDRIVE_INSTANCE_NAME).properties

    def create_client(self, plan_name, client_name, client_group_name, indexserver,
                      service_account_details, credential_name, jr_path):
        """
                Creates a Google Drive Client

                Args:
                    - plan_name (str): Name of server plan
                    - client_name (str): The name to be assigned to the client.
                    - client_group_name (str): The group name to which the client belongs.
                    - indexserver (str): The index server address used for the client.
                    - service_account_details (dict): A dictionary containing service account details
                      required for authentication and authorization.
                    - credential_name (str): Credential Name that created in Credential Vault.
                    - jr_path (str): Job Results Dir path.
                    - instance_type (int): Type of Google client
        """
        self._create_client(plan_name, client_name, indexserver,
                            service_account_details, credential_name,
                            instance_type=constants.GDRIVE_INSTANCE_TYPE,
                            **{
                                'client_group_name': client_group_name,
                                'jr_path': jr_path
                            })

    def _validate_discovered_shareddrives(self, api_obj):
        """
                Validates the discovered shared drives

                Args:
                    - api_obj : GoogleWorkspaceAPI object.
                """
        try:
            flag, shared_drives = self.subclient.verify_shareddrive_discovery_v2()

            discovered_shared_drives = [shared_drive['folderId'] for shared_drive in shared_drives]
            self.log.info(f"Discovered Shared Drives : {discovered_shared_drives}")

            api_shared_drives = [shared_drive['id'] for shared_drive in api_obj.shared_drives]
            self.log.info(f"Actual Shared Drives : {api_shared_drives}")

            self.log.info('Validating Discovered Shared Drives')
            for shared_drive in api_shared_drives:
                if shared_drive not in discovered_shared_drives:
                    raise CVCloudException(self.app_name, '501',
                                           f'[{shared_drive}] not found in Discovered Shared Drive list')

            self.log.info('Discovery Successfully Completed')
        except Exception as err:
            self.log.exception("Exception while validating discovered shareddrives")
            raise Exception(err)

    def validate_discovered_users(self):
        """
                Validates the discovered users

                Args:
                    - api_obj : GoogleWorkspaceAPI object.
        """
        self._validate_discovered_users(self.api_obj)
        self._validate_discovered_shareddrives(self.api_obj)

    def create_association(self, users, plan):
        """
                Adds content to client.

                Args:
                    - users (list) - List of users needs to add into client.
                    - plan (str) - Google Workspace Plan needs to associate with users.
        """
        self._create_association(users, plan)

    def run_backup(self, users_list=None):
        """
        Runs backup for google client
                Args:
                    users_list (list) : list of users to run backup
        """
        return self._run_backup(users_list)

    def run_restore(self, users_list, **kwargs):
        """
                Runs Restore for Google client
                        Args:
                            users_list (list) :  List of SMTP addresses of users
                            **kwargs (dict) : Additional parameters
                                overwrite (bool) : unconditional overwrite files during restore (default: False)
                                restore_as_copy (bool) : restore files as copy during restore (default: False)
                                skip_file_permissions (bool) : If True, restore of file permissions are skipped (default: False)
        """
        return self._run_restore(users_list, **kwargs)


class GoogleMail(GoogleWorkspace):
    """Class for Google Mail operations"""

    def __init__(self, commcell):
        super().__init__(commcell)
        self.api_obj = GmailAPI()

    @property
    def client_properties(self):
        """Returns GMail Client Properties"""
        return self.agent.instances.get(constants.GMAIL_INSTANCE_NAME).properties

    def create_client(self, plan_name, client_name, client_group_name, indexserver,
                      service_account_details, credential_name, jr_path):
        """
                Creates a Google Client

                Args:
                    - plan_name (str): Name of server plan
                    - client_name (str): The name to be assigned to the client.
                    - client_group_name (str): The group name to which the client belongs.
                    - indexserver (str): The index server address used for the client.
                    - service_account_details (dict): A dictionary containing service account details
                      required for authentication and authorization.
                    - credential_name (str): Credential Name that created in Credential Vault.
                    - jr_path (str): Job Results Dir path.
                    - instance_type (int): Type of Google client
        """
        self._create_client(plan_name, client_name, indexserver,
                            service_account_details, credential_name,
                            instance_type=constants.GMAIL_INSTANCE_TYPE,
                            **{
                                'client_group_name': client_group_name,
                                'jr_path': jr_path
                            })

    def validate_discovered_users(self):
        """
                Validates the discovered users

                Args:
                    - api_obj : GoogleWorkspaceAPI object.
        """
        self._validate_discovered_users(self.api_obj)

    def create_association(self, users, plan):
        """
                Adds content to client.

                Args:
                    - users (list) - List of users needs to add into client.
                    - plan (str) - Google Workspace Plan needs to associate with users.
        """
        self._create_association(users, plan)

    def run_backup(self, users_list=None):
        """
        Runs backup for google client
                Args:
                    users_list (list) : list of users to run backup
        """
        return self._run_backup(users_list, is_mailbox=True)

    def run_restore(self, users_list, **kwargs):
        """
                Runs Restore for Google client
                        Args:
                            users_list (list) :  List of SMTP addresses of users
                            **kwargs (dict) : Additional parameters
                                overwrite (bool) : unconditional overwrite files during restore (default: False)
                                restore_as_copy (bool) : restore files as copy during restore (default: False)
                                skip_file_permissions (bool) : If True, restore of file permissions are skipped (default: False)
        """
        return self._run_restore(users_list, **kwargs)


class GoogleWorkspaceAPI:
    """Class for Google Workspace API related Operations"""

    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_CONFIG.ServiceAccountFile, scopes=GOOGLE_CONFIG.Scopes)
        self.delegated_credentials = credentials.with_subject(GOOGLE_CONFIG.SuperAdmin)

    def _get_users(self):
        """Gets the list of     users"""
        service = build('admin', 'directory_v1', credentials=self.delegated_credentials)
        users = []
        page_token = None

        while True:
            results = service.users().list(customer='my_customer', orderBy='email', pageToken=page_token).execute()
            users.extend(results.get('users', []))

            page_token = results.get('nextPageToken')
            if not page_token:
                break

        return users

    def _get_groups(self):
        """Gets the list of Groups"""
        service = build('admin', 'directory_v1', credentials=self.delegated_credentials)
        groups = []
        page_token = None

        while True:
            results = service.groups().list(customer='my_customer', orderBy='email', pageToken=page_token).execute()
            groups.extend(results.get('groups', []))

            page_token = results.get('nextPageToken')
            if not page_token:
                break
        return groups


class GmailAPI(GoogleWorkspaceAPI):
    def __init__(self):
        super().__init__()
        self.refresh()

    @property
    def users(self):
        return self.users

    @property
    def groups(self):
        return self.groups

    def get_users(self):
        """Gets the list of users"""
        return self._get_users()

    def get_groups(self):
        """Gets the list of groups"""
        return self._get_groups()

    def refresh(self):
        """Refresh to assign users and Groups"""
        self.users = self.get_users()
        self.groups = self.get_groups()


class GdriveAPI(GoogleWorkspaceAPI):
    def __init__(self):
        super().__init__()
        self.refresh()

    def get_users(self):
        """Gets the list of users"""
        return self._get_users()

    def __get_shared_drives(self):
        """Gets the list of Shared Drives"""
        service = build('drive', 'v3', credentials=self.delegated_credentials)
        shared_drives = []
        page_token = None

        while True:
            results = service.drives().list(useDomainAdminAccess=True, pageToken=page_token).execute()
            shared_drives.extend(results.get('drives', []))
            if 'nextPageToken' not in results:
                break
            page_token = results['nextPageToken']
        return shared_drives

    @property
    def users(self):
        return self.users

    @property
    def groups(self):
        return self.groups

    @property
    def shared_drives(self):
        return self.shared_drives

    def get_groups(self):
        """Gets the list of groups"""
        return self._get_groups()

    def get_share_drive(self):
        """Gets the list of shared drives"""
        return self.__get_shared_drives()

    def refresh(self):
        """Refresh to assign users, groups and shared drives. """
        self.users = self.get_users()
        self.groups = self.get_groups()
        self.shared_drives = self.get_share_drive()
