# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Object storage Accounts listing page

    access_account()          --    Access account details page

    view_by_vendors()       --    Filters table to view by vendor

    get_clients()           -- gets all visible client names

    is_account_exists()     --  Returns true if account exists otherwise false

    add_azure_gen2_client()   --  adds Azure Gen 2 Object Storage

    add_ibm_client()        --  adds IBM Object Storage client

    add_ali_client()        --  adds Ali Object Storage client

    add_google_client()     --adds google cloud object storage client

    add_azure_blob_client() -- adds Azure Blob Object Storage client

    add_object_storage_client() --  adds the object storage client from wizard

    get_sla()               --Gets sla value for client

    create_content_group()          --  Creates content group

    edit_content_group()    --Edits the contents of content group

    delete_selected_content_from_content_group() -- Deletes selected content from content group
    
    validate_backup_jobs()  --Validates if jobs are present in the backup history

    validate_default_subclient_content()    -- validates default subclient contents

    backup()        -- runs backups jobs for object storage clients

    delete_object_storage_client_credentials()  -- deletes client and associated credentials

    restore_to_disk()               -- restores to disk from object storage

    change_auth_type                -- changes the auth type of client

    change_scan_type()              -- changes the scan type of content group

    cleanup_credentials()           -- deletes automation generated credentials
"""
import os
import time
from enum import Enum
from Database.dbhelper import DbHelper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.ObjectStorage.content_group import ContentGroup
from Web.AdminConsole.ObjectStorage.object_details import ObjectDetails
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from Web.AdminConsole.AdminConsolePages.credential_manager import CredentialManager
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.page_container import PageContainer

from Web.AdminConsole.ObjectStorage.clients.add_client import (
    CreateAzureGen2,
    CreateAliClient,
    CreateIbmClient,
    CreateGoogleClient,
    CreateAzureBlob,
    CreateS3Client,
    CreateAzureFileShare,
    RCreateObjectStorageClient
)
from AutomationUtils import logger
from Web.Common.exceptions import CVException


class ObjectStorage:
    """ Class for Object storage Accounts page """

    class Types(Enum):
        GOOGLE = "Google Cloud"
        Azure_Blob = "Azure Blob"
        AZURE_FILE = "Azure File"
        Alibaba_Cloud_OSS = "Alibaba Cloud OSS"
        IBM_Cloud_oss = "IBM Cloud Object Storage"
        Azure_DL_Gen2 = "Azure Data Lake Storage Gen2"
        Amazon_S3 = "Amazon S3"
        OCI = "OCI Object Storage"

    def __init__(self, admin_console, commcell_obj=None):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
            commcell_obj (Commcell): commcell object
        """
        self.admin_console = admin_console
        self.table = Table(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.admin_console.load_properties(self)
        self.log = logger.get_log()
        self.object_details = ObjectDetails(self.admin_console)
        self.content_group = ContentGroup(self.admin_console)
        self.credential_manager = CredentialManager(self.admin_console)
        self.page_container = PageContainer(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.commcell = commcell_obj
        self.db_helper = DbHelper(self.commcell)

    @PageService()
    def access_account(self, name):
        """
        Access account details page
        Args:
            name (str): Object storage name
        """
        self.rtable.view_by_title('All')
        self.rtable.reload_data()
        self.rtable.access_link(name)
        self.admin_console.access_tab(self.admin_console.props['pageHeader.contentGroups'])

    @PageService()
    def view_by_vendor(self, name):
        """
        Filter table view by vendor
        Args:
            name (str): vendor name
        """
        self.table.view_by_title(name)

    @PageService()
    def get_clients(self):
        """
        gets all visbile client names
        """
        return self.table.get_column_data(self.admin_console.props['label.name'])

    @PageService()
    def is_account_exists(self, object_storage_type, name):
        """
        Returns true if account exists
        Args:
            object_storage_type (any) : Object Storage Type
            name (str): Object Storage name
        """
        if not isinstance(object_storage_type, self.Types):
            raise Exception('Invalid object storage type')
        self.rtable.set_default_filter(filter_id='Vendor', filter_value=object_storage_type.value)
        if self.rtable.is_entity_present_in_column('Name', name):
            return True
        return False

    @PageService()
    def add_azure_gen2_client(
            self,
            name,
            proxy_client,
            auth_type,
            plan,
            credential=None,
            access_key=None,
            secret_key=None,
            tenant_id=None,
            app_id=None,
            app_secret_key=None,
            environment="AzureCloud"
    ):
        """
        Creates Azure gen2 client
        Args:
            name (str)          -- name of client to be created
                proxy_client (str)  -- name of proxy client
                auth_type(str)         -- type of authentication (Keys/IAM VM/IAM AD)
                    Accepted values - Access and secret keys / IAM VM Authentication / IAM AD Authentication
                plan(str)           -- name of backup plan
                credential (str)    -- Credential to set for Object Storage account
                access_key (str)    -- access key of Azure Cloud account
                secret_key (str)    -- secret key of Azure Cloud account
                tenant_id(str)      -- Tenant id of ad application
                app_id(str)         -- Application id of AD Application
                app_secret_key(str) -- Application secret key of AD Application
                environment(str)    -- Environment of AD Application
        """
        self.table.access_toolbar_menu('ADD_CLOUD_STORAGE')
        CreateAzureGen2(self.admin_console).create_client(
            name=name,
            proxy_client=proxy_client,
            auth_type=auth_type,
            backup_plan=plan,
            credential=credential,
            access_key=access_key,
            secret_key=secret_key,
            tenant_id=tenant_id,
            app_id=app_id,
            app_secret_key=app_secret_key,
            environment=environment
        )
        self.admin_console.check_error_message()

    @PageService()
    def add_ali_client(
            self,
            name,
            proxy_client,
            backup_plan,
            url,
            credential=None,
            access_key=None,
            secret_key=None,
    ):
        """Creates Ali Client
            Args:
                name (str)      -- name of client to be created
                proxy_client (str)  --name of proxy client
                backup_plan(str)    --name of backup plan
                url (str)           -- Region to which the account is pointed
                credential (str)    -- Credential to set for Object Storage account
                access_key (str)    -- access key of Ali Cloud account
                secret_key (str)    -- secret key of Ali Cloud account

            Returns:
                object - Object storage if client is created successfully
        """
        self.table.access_toolbar_menu('ADD_CLOUD_STORAGE')
        CreateAliClient(self.admin_console).create_client(
            name,
            proxy_client,
            backup_plan,
            credential,
            access_key,
            secret_key,
            url
        )
        self.admin_console.check_error_message()

    @PageService()
    def add_ibm_client(
            self,
            name,
            proxy_client,
            backup_plan,
            url,
            credential=None,
            access_key=None,
            secret_key=None,
    ):
        """Creates IBM Client
            Args:
                name (str)      -- name of client to be created
                proxy_client (str)  --name of proxy client
                backup_plan(str)    --name of backup plan
                credential (str)    -- Credential to set for Object Storage account
                access_key (str)    -- access key of IBM Cloud account
                secret_key (str)    -- secret key of IBM Cloud account
                url (str)           -- Region to which the account is pointed

            Returns:
                object - Object storage if client is created successfully
        """
        self.table.access_toolbar_menu('ADD_CLOUD_STORAGE')
        CreateIbmClient(self.admin_console).create_client(
            name=name,
            proxy_client=proxy_client,
            backup_plan=backup_plan,
            credential=credential,
            access_key=access_key,
            secret_key=secret_key,
            url=url
        )
        self.admin_console.check_error_message()

    @PageService()
    def add_google_client(
            self,
            name,
            proxy_client,
            plan, url,
            credential=None,
            access_key=None,
            secret_key=None
    ):
        """Creates Google Client
            Args:
                name (str)          -- name of client to be created
                proxy_client (str)  -- name of proxy client
                plan(str)           -- name of backup plan
                credential (str)    -- Credential to set for Object Storage account
                access_key (str)    -- access key of Google Cloud account
                secret_key (str)    -- secret key of Google Cloud account
                url (str)           -- Region to which the account is pointed

            Returns:
                object - Object storage if client is created successfully
        """
        self.table.access_toolbar_menu('ADD_CLOUD_STORAGE')
        CreateGoogleClient(self.admin_console).create_client(
            name=name,
            proxy_client=proxy_client,
            backup_plan=plan,
            access_key=access_key,
            secret_key=secret_key,
            url=url,
            credential=credential
        )
        self.admin_console.check_error_message()

    @PageService()
    def add_azure_blob_client(
            self,
            proxy_client,
            plan,
            credential=None,
            tenant_id=None,
            app_id=None,
            app_secret_key=None,
            cloud_name=None,
            subscription_id=None,
            backup_content=None
    ):
        """Creates Azure Blob Client
            Args:
                proxy_client (str)  -- name of proxy client
                plan(str)           -- name of backup plan
                credential (str)    -- Credential to set for Object Storage account
                tenant_id(str)      -- Tenant id of ad application
                app_id(str)         -- Application id of AD Application
                app_secret_key(str) -- Application secret key of AD Application
                cloud_name(str)     -- Name of cloud account for azure datalake/blob
                subscription_id(str) -- Subscription id of AD Application
                backup_content(list) -- content to be backed up
            Returns:
                object - Object storage if client is created successfully
        """
        credential_name = CreateAzureBlob(self.admin_console, self.commcell).create_client(
            proxy_client=proxy_client,
            backup_plan=plan,
            credential=credential,
            tenant_id=tenant_id,
            app_id=app_id,
            app_secret_key=app_secret_key,
            cloud_name=cloud_name,
            subscription_id=subscription_id,
            backup_content=backup_content
        )
        self.admin_console.check_error_message()
        return credential_name

    @PageService()
    def add_s3_client(
            self,
            name,
            proxy_client,
            auth_type,
            plan, url,
            credential=None,
            access_key=None,
            secret_key=None,
            role_arn=None
    ):
        """Creates Amazon S3 Client
        Args:
            name (str)          -- name of client to be created
            proxy_client (str)  -- name of proxy client
            auth_type(str)         -- type of authentication (Keys/IAM/STS)
            Accepted values - Access and secret keys / IAM role / STS assume role with IAM role
            plan(str)           -- name of backup plan
            credential (str)    -- Credential to set for Object Storage account
            access_key (str)    -- access key of S3 Cloud account
            secret_key (str)    -- secret key of S3 Cloud account
            url (str)           -- Region to which the account is pointed
            role_arn (str)      -- Role ARN of STS Assume Role

        Returns:
            object - Object storage if client is created successfully
        """
        self.table.access_toolbar_menu('ADD_CLOUD_STORAGE')
        CreateS3Client(self.admin_console).create_client(
            name=name,
            proxy_client=proxy_client,
            auth_type=auth_type,
            backup_plan=plan,
            url=url,
            credential=credential,
            access_key=access_key,
            secret_key=secret_key,
            role_arn=role_arn
        )
        self.admin_console.check_error_message()

    @PageService()
    def add_azure_file_share_client(
            self,
            name,
            proxy_client,
            plan,
            credential=None,
            access_key=None,
            secret_key=None,
    ):
        """Creates Azure Blob Client
            Args:
                name (str)          -- name of client to be created
                proxy_client (str)  -- name of proxy client
                plan(str)           -- name of backup plan
                credential (str)    -- Credential to set for Object Storage account
                access_key (str)    -- access key of Azure Cloud account
                secret_key (str)    -- secret key of Azure Cloud account
            Returns:
                object - Object storage if client is created successfully
        """
        self.table.access_toolbar_menu('ADD_CLOUD_STORAGE')
        CreateAzureFileShare(self.admin_console).create_client(
            name=name,
            proxy_client=proxy_client,
            backup_plan=plan,
            credential=credential,
            access_key=access_key,
            secret_key=secret_key
        )
        self.admin_console.check_error_message()

    @PageService()
    def add_object_storage_client(
            self,
            name,
            proxy_client,
            plan,
            backup_content,
            auth_type='Access and secret keys',
            url=None,
            credential=None,
            access_key=None,
            secret_key=None,
            tenant_id=None,
            app_id=None,
            app_secret_key=None,
            vendor_name=None,
            role_arn=None,
            compartment_path=None,
            cloud_name=None,
            subscription_id=None
    ):
        """Creates Azure Blob Client
            Args:
                name (str)          -- name of client to be created
                proxy_client (str)  -- name of proxy client
                plan(str)           -- name of backup plan
                backup_content(list) -- content to set from wizard
                auth_type(str)      -- type of authentication (Keys/IAM VM/IAM AD)
                Accepted values     -- Access and secret keys / IAM VM Authentication / IAM AD Authentication
                url(str)     --  url of Azure Blob account
                credential (str)    -- Credential to set for Object Storage account
                access_key (str)    -- access key of Azure Cloud account
                secret_key (str)    -- secret key of Azure Cloud account
                tenant_id(str)      -- Tenant id of ad application
                app_id(str)         -- Application id of AD Application
                app_secret_key(str) -- Application secret key of AD Application
                vendor_name(str)    -- vendor name of the object storage client
                role_arn(str)       -- role arn of the sts client
                compartment_path(str)--compartment path for oci client
                cloud_name(str)     -- Name of cloud account for azure datalake/blob
                subscription_id(str) -- Subscription id of AD Application
            Returns:
                object - Object storage if client is created successfully
        """
        self.admin_console.click_button_using_text('Add object storage')
        credential_name = RCreateObjectStorageClient(self.admin_console, vendor_name, self.commcell).create_client(
            name=name,
            proxy_client=proxy_client,
            auth_type=auth_type,
            backup_plan=plan,
            credential=credential,
            access_key=access_key,
            secret_key=secret_key,
            tenant_id=tenant_id,
            app_id=app_id,
            app_secret_key=app_secret_key,
            url=url,
            backup_content=backup_content,
            role_arn=role_arn,
            compartment_path=compartment_path,
            cloud_name=cloud_name,
            subscription_id=subscription_id
        )
        self.admin_console.check_error_message()
        return credential_name

    @PageService()
    def get_sla(self, client_name):
        """
        Gets sla value for client
        Args:
            client_name (str): Object storage name
        Returns:
            (str): SLA value
        """
        self.table.search_for(client_name)
        sla_column = self.table.get_column_data(self.admin_console.props['label.nav.sla'])
        return sla_column[0]

    @PageService()
    def validate_default_subclient_content(self, default_subclient_content):
        """Validates default subclient's content which was set in wizard"""
        self.admin_console.access_tab(self.admin_console.props['pageHeader.contentGroups'])
        contents = self.object_details.get_content_group_contents()
        if contents == default_subclient_content:
            self.log.info("content matched with content set through wizard")
        else:
            self.log.warning(f"given : {default_subclient_content}")
            self.log.warning(f"in default subclient: {contents}")
            self.log.warning("Contents set through wizard and content on default subclient is different")

    @PageService()
    def create_content_group(self, **kwargs):
        """Creates Content group"""
        self.object_details.create_content_group(
            kwargs.get('content_group_name'),
            kwargs.get("plan"),
            [kwargs.get("content")]
        )
        self.log.info(f"Content group {kwargs.get('content_group_name')} got created")

    @PageService()
    def edit_content_group(self, content_group_name, content):
        """ Edits the contents of content group
            content_group_name(str):    name of the content group to edit the content

            content(str):   content to which the content group's content to be changed.
        """
        self.object_details.access_content_group(content_group_name)
        self.content_group.edit_contents([f"/{content}"])
        self.admin_console.wait_for_completion()
        self.log.info("Contents edited for content group")

    @PageService()
    def change_scan_type(self, object_storage_name, scan_type, content_group_name):
        """ Changes the scan type of content group
            Args:
                object_storage_name(str): object storage name
                scan_type(str): scan type to be set
                content_group_name(str): name of content group
        """
        self.object_details.access_content_group(content_group_name)
        self.admin_console.access_tab(self.admin_console.props['pageHeader.Configuration'])
        self.content_group.change_scan_type(scan_type)
        self.page_container.click_breadcrumb(object_storage_name)
        self.admin_console.wait_for_completion()
        self.admin_console.access_tab(self.admin_console.props['pageHeader.contentGroups'])
        self.log.info("Scan type changed successfully")

    @PageService()
    def delete_selected_content_from_content_group(self, content_group_name, paths):
        """ Deletes selected content from content group
            Args:
                content_group_name (str): name of the content group
                paths (list): content to be deleted
        """
        self.object_details.access_content_group(content_group_name)
        if not isinstance(paths, list):
            raise TypeError(f"Expected a list, got {type(paths)}")
        self.content_group.delete_content_path(paths)
        self.admin_console.wait_for_completion()
        self.log.info("Selected content deleted from content group")

    @PageService()
    def validate_backup_jobs(self, backup_job_list, react=False):
        """ Validates if jobs are run from backup history
             backup_job_list(list): backups jobs list with job ids
        """
        self.content_group.backup_history()
        job_ids = self.content_group.get_job_ids(react)
        for job in backup_job_list:
            if job not in job_ids:
                raise CVException(f"Job :{job} is not present in backup history")
        self.log.info("Validation completed")

    @PageService()
    def backup(self, backup_type, content_group_name):
        """ Performs backup for object storage account
                Args:
                    backup_type: Type of backup FULL/INCR/SYNTH

                    content_group_name(str): To run backup on given content group
                """
        if backup_type is RBackup.BackupType.FULL:
            jobid = self.object_details.submit_backup(
                content_group_name, backup_type
            )
        elif backup_type is RBackup.BackupType.SYNTH:
            _jobid = self.content_group.submit_backup(backup_type)
            jobid = _jobid[0]
        else:
            jobid = self.content_group.submit_backup(backup_type)

        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Backup ran Successfully")

        return jobid

    @PageService()
    def delete_object_storage_client_and_credentials(self, client_name, credential_name=None):
        """Deletes the already existing client
            Args:
                client_name(str):   Object storage client name

                credential_name(str):   credential entity name
        """

        self.rtable.access_link(client_name)
        utils = CommonUtils(self)
        utils.kill_active_jobs(client_name)
        self.object_details.delete_account()
        self.admin_console.wait_for_completion()

        if credential_name:
            time.sleep(60)
            self.navigator.navigate_to_credential_manager()
            self.admin_console.wait_for_completion()
            self.credential_manager.action_remove_credential(credential_name)
        self.admin_console.wait_for_completion()
        self.log.info("Object Storage Account Deleted")

    @PageService()
    def restore_to_disk(self, **kwargs):
        """ Restores data to disk
        Expect Args:
            dest_fs_client(str) -- destination fs client for restore to disk

            source_path(str)    -- where original data is downloaded

            bucket_name(str)    -- bucket name for restore content selection
        """
        destination_object = self.commcell.clients.get(kwargs.get("dest_fs_client"))
        destination_machine = Machine(destination_object)
        remote_path = destination_machine.join_path(destination_object.install_directory, "restored_contents")
        destination_machine.create_directory(remote_path, force_create=True)

        original_on_remote = destination_machine.join_path(destination_object.install_directory,
                                                           "original_contents")
        destination_machine.create_directory(original_on_remote, force_create=True)
        source_path = kwargs.get('source_path')
        bucket_name = kwargs.get('bucket_name')
        self.log.info(f"Source path is {source_path}")
        self.log.info(f"Original Data path on destination machine {original_on_remote}")
        destination_machine.copy_from_local(source_path, original_on_remote)

        rstr_obj = self.object_details.submit_restore([bucket_name])
        jobid = rstr_obj.to_disk(kwargs.get("dest_fs_client"), remote_path)
        self.db_helper.wait_for_job_completion(jobid)
        self.log.info("Restore job ran Successfully")

        self.log.info("validation for restore to disk")

        head, source_path_tail = os.path.split("{}".format(source_path))
        original_content_path = destination_machine.join_path(original_on_remote, source_path_tail)

        restored_content_path = destination_machine.join_path(remote_path, kwargs.get("bucket_name"))

        restore_status = destination_machine.compare_folders(destination_machine,
                                                             original_content_path,
                                                             restored_content_path)
        if len(restore_status) > 0:
            raise CVException("Restore to Given destination Failed During Validation")
        self.log.info("Restore to Disk Succeeded")
        destination_machine.remove_directory(remote_path)
        destination_machine.remove_directory(original_on_remote)

    @PageService()
    def change_auth_type(self, auth_type, **kwargs):
        """ Changes the auth_type
              Expected kwargs :
                For  auth_type : Access key and Account name
                    account_name (str) : Account name
                    access_key (str)   : Access key
                For auth_type : IAM VM Role
                    ad_account_name (str)  : AD account name
        """
        self.admin_console.access_tab(self.admin_console.props['pageHeader.Configuration'])
        self.content_group.change_instance_auth_type(auth_type, **kwargs)
        self.admin_console.wait_for_completion()
        self.log.info("Authentication method changed successfully")

    @PageService()
    def cleanup_credentials(self, hours):
        """
            Deletes automation generated credentials that have been there for more than the input hours.
            Args:
                hours (int): The hours to compare with the credential timestamp.
            """
        self.db_helper.clear_automation_credentials("automation-credential-", hours)
        self.admin_console.wait_for_completion()
        self.log.info("Cleaned up automation generated credentials successfully")
