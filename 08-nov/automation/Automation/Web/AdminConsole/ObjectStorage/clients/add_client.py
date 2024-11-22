# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This file contains _NewClient class which inherits from Modal Panel.

Perform the following steps when trying to add support for a new object storage client:
    1. Create a class for the new agent and inherit from _NewClient
    2. Implement the vendor_name() in the class
        to return the values specific to the agent
    3. Define a method in the class to create instance for the specific agent

_NewClient:
------------
    vendor_name()   --  Abstract method to set the Object Storage vendor name

    _select_vendor()    --  Abstract method to select the vendor

    _set_client_name()  --  Abstract method to set the client name

CreateAzureGen2:
-----------------
    vendor_name()   --  Returns vendor for Object Storage type

    create_client() --  Creates Azure Gen2 client

CreateAliGen2:
-----------------
    vendor_name()   --  Returns vendor for Object Storage type

    create_client() --  Creates Alibaba client

CreateIbmGen2:
-----------------
    vendor_name()   --  Returns vendor for Object Storage type

    create_client() --  Creates IBM Cloud client

CreateGoogleClient:
--------------------
     vendor_name()   --  Returns vendor for Object Storage type

    create_client() --  Creates Google Cloud client

CreateS3Client:
--------------------
     vendor_name()   --  Returns vendor for Object Storage type

    create_client() --  Creates Amazon S3 Cloud client

CreateAzureBlob:
--------------------
     vendor_name()   --  Returns vendor for Object Storage type

    create_client() --  Creates Azure Blob client

RCreateObjectStorageClient:
----------------------
     vendor_name()   --   host url of the vendor

     create_client() --   Creates Object Storage Client

"""

from abc import abstractmethod
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.panel import ModalPanel
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.dialog import RModalDialog
import time
from selenium.common.exceptions import NoSuchElementException
from AutomationUtils import config
from Database.dbhelper import DbHelper
from selenium.webdriver.common.by import By


class _NewClient(ModalPanel):
    """class for object storage client creation"""

    @property
    @abstractmethod
    def vendor_name(self):
        """Override this method and implement it as a variable whose
        value is set to the host url as per the vendor"""
        raise NotImplementedError

    def _select_vendor(self):
        """Selects vendor"""
        self._admin_console.access_sub_menu(self.vendor_name)

    def _set_vendor(self, vendor):
        """Sets vendor on guided setup page"""
        self._dropdown.select_drop_down_values(
            drop_down_id="addCloudStorageContent_isteven-multi-select_#6986", values=[vendor])

    def _set_client_name(self, name):
        """
        set Client name
        Args:
            name (str): Client name
        """
        self._admin_console.fill_form_by_id('cloudStorageName', name)

    def _set_host_url(self, url):
        """
        set Cloud storage host url
        Args:
            url (str): Cloud storage host url
        """
        self._admin_console.fill_form_by_id('hostURL', url)

    def _set_credential(self, credential_name):
        """
        sets credential from dropdown
        Args:
            credential_name (str): Credential Name
        """
        self._dropdown.select_drop_down_values(drop_down_id='credential',
                                               values=[credential_name])

    def _click_plus_for_new_credential(self):
        """
        click plus to add new credential
        """
        self._admin_console.click_by_xpath(
            "//button[@data-ng-click='handlerOpenCreateModal()']")

    def _set_access_name(self, name):
        """
        set Cloud storage account name
        Args:
            name (str): account name
        """
        self._admin_console.fill_form_by_id('userName', name)

    def _set_access_pwd(self, key):
        """
        set Cloud storage account key or secret key
        Args:
            key (str): account key
        """
        self._admin_console.fill_form_by_id('password', key)

    def _set_user_name(self, name):
        """
        set Cloud storage name
        Args:
            name (str): Client name
        """
        self._admin_console.fill_form_by_id('userName', name)

    def _set_credential_name(self, name):
        """
        set Credential Name
        Args:
            name (str): Credential Name
        """
        self._admin_console.fill_form_by_id('credentialName', name)

    def _set_access_node(self, name):
        """
        set Cloud storage access node
        Args:
            name (str): Plan name
        """
        self._dropdown.select_drop_down_values(drop_down_id='cappsAccessNodes_isteven-multi-select_#8659',
                                               values=[name])

    def _set_plan(self, name):
        """
        set Cloud storage name
        Args:
            name (str): Plan name
        """
        self._dropdown.select_drop_down_values(drop_down_id='planSummaryDropdown', values=[name])

    def _click_authentication_type(self):
        """
        clicks on Authentication type dropdown
        """
        self._admin_console.click_by_xpath("//select[contains(@id, 'authenticationType')]")

    def _select_authentication_type(self, name):
        """
        selects Authentication type
        Args:
            name(str): Authentication type
        """
        self._admin_console.click_by_xpath(
            f"//select[contains(@id, 'authenticationType')]/option[contains(@label,'{name}')]")

    def _set_role_arn(self, role_arn):
        """
               sets role ARN
               Args:
                   role_arn(str): Role ARN
               """
        self._admin_console.fill_form_by_id('RoleARN', role_arn)

    def _set_account_name(self, name):
        """
        set Cloud storage account name
        Args:
            name (str): account name
        """
        self._admin_console.fill_form_by_id('adAccoutName', name)

    def _set_tenant_id(self, tenant_id):
        """
        sets tenant ID for AD application authentication
        Args:
            tenant_id(str): tenant id
        """
        self._admin_console.fill_form_by_id("tenantId", tenant_id)

    def _set_application_id(self, application_id):
        """
        sets tenant ID for AD application authentication
        Args:
            application_id(str): application id
        """
        self._admin_console.fill_form_by_id("applicationId", application_id)

    def _set_application_secret(self, key):
        """
        sets tenant ID for AD application authentication
        Args:
            key(str): secret key
        """
        self._admin_console.fill_form_by_id("applicationPassword", key)

    def _set_environment(self, value='AzureCloud'):
        """
        sets Environment from dropdown
        Args:
            value (str): Environment Name
        """
        self._dropdown.select_drop_down_values(drop_down_id='environmentList',
                                               values=[value])


class CreateAzureGen2(_NewClient):
    """
    used to create Azure Gen2 client
    """

    @property
    def vendor_name(self):
        """For vendor selection
        """
        return self._admin_console.props['label.clientType.azureDataLake']

    @PageService()
    def create_client(
            self, name, proxy_client,
            auth_type,
            backup_plan,
            url="dfs.core.windows.net",
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
            name (str)          -- Name of client to be created
            proxy_client (str)  -- Name of proxy client
            auth_type(str)         -- type of authentication (Keys/IAM VM/IAM AD)
                    Accepted values - Access and secret keys / IAM VM Authentication / IAM AD Authentication
            backup_plan(str)    -- Name of backup plan
            url (str)           -- Region to which the account is pointed
            credential (str)    -- Credential to set for Object Storage account
            access_key (str)    -- Access key of Azure Cloud account
            secret_key (str)    -- Secret key of Azure Cloud account
            tenant_id(str)      -- Tenant id of ad application
            app_id(str)         -- Application id of AD Application
            app_secret_key(str) -- Application secret key of AD Application
            environment(str)    -- Environment of AD Application
        """

        self._select_vendor()
        self._set_client_name(name)
        self._set_host_url(url)
        self._click_authentication_type()
        self._select_authentication_type(auth_type)
        if auth_type != 'IAM VM role':
            if credential:
                self._set_credential(credential)
            else:
                if auth_type == 'Access key and Account name':
                    self._click_plus_for_new_credential()
                    self._set_credential_name('automation-credential')
                    self._set_access_name(access_key)
                    self._set_access_pwd(secret_key)
                    self.submit()
                else:
                    self._click_plus_for_new_credential()
                    self._set_credential_name('automation-credential')
                    self._set_tenant_id(tenant_id)
                    self._set_application_id(app_id)
                    self._set_application_secret(app_secret_key)
                    self._set_environment(environment)
                    self.submit()
                    self._admin_console.wait_for_completion()
        if auth_type != 'Access key and Account name':
            self._set_account_name(access_key)
        self._set_access_node(proxy_client)
        self._set_plan(backup_plan)
        self.submit()


class CreateAliClient(_NewClient):
    """
    Class used to create Ali client
    """

    @property
    def vendor_name(self):
        """Returns:

            object-  host url of the vendor
        """
        return self._admin_console.props['label.clientType.alibabaOSS']

    @PageService()
    def create_client(
            self, name, proxy_client,
            backup_plan,
            credential,
            access_key,
            secret_key,
            url
    ):
        """
        Creates Ali Client
        Args:
            name (str)      -- name of client to be created
            proxy_client (str)  --name of proxy client
            backup_plan(str)    --name of backup plan
            credential (str)    -- Credential to set for Object Storage account
            access_key (str)    -- access key of Ali Cloud account
            secret_key (str)    -- secret key of Ali Cloud account
            url (str)           -- Region to which the account is pointed

        Returns:
            object - Object storage if client is created successfully

        """
        self._select_vendor()
        self._set_client_name(name)
        self._set_host_url(url)
        if credential:
            self._set_credential(credential)
        else:
            self._click_plus_for_new_credential()
            self._admin_console.wait_for_completion()
            self._set_credential_name('automation-credential')
            self._set_user_name(access_key)
            self._set_access_pwd(secret_key)
            self._admin_console.wait_for_completion()
        self._set_access_node(proxy_client)
        self._set_plan(backup_plan)
        self.submit()


class CreateIbmClient(_NewClient):
    """
        Class used to create IBM client
    """

    @property
    def vendor_name(self):
        """
        Returns:
            object-  host url of the vendor
        """
        return self._admin_console.props['label.clientType.ibmCOS']

    @PageService()
    def create_client(
            self, name,
            proxy_client,
            backup_plan,
            credential=None,
            access_key=None,
            secret_key=None,
            url=None
    ):
        """
               Creates IBM Client
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
        self._select_vendor()
        self._set_client_name(name)
        self._set_host_url(url)
        if credential:
            self._set_credential(credential)
        else:
            self._click_plus_for_new_credential()
            self._admin_console.wait_for_completion()
            self._set_credential_name('automation-credential')
            self._set_user_name(access_key)
            self._set_access_pwd(secret_key)
            self._admin_console.wait_for_completion()
        self._set_access_node(proxy_client)
        self._set_plan(backup_plan)
        self.submit()


class CreateGoogleClient(_NewClient):
    """
    Class to create Create Google Object Storage Client
    """

    @property
    def vendor_name(self):
        """
        Returns:
            object  -  host url of the vendor
        """
        return self._admin_console.props['label.clientType.googleCloud']

    @PageService()
    def create_client(
            self, name, proxy_client,
            backup_plan, url,
            credential=None,
            access_key=None,
            secret_key=None
    ):
        """
        Creates Google Object Storage Client
        Args:
            name (str)          -- Name of client to be created
            proxy_client (str)  -- Name of proxy client
            backup_plan(str)    -- Name of backup plan
            credential (str)    -- Credential to set for Object Storage account
            access_key (str)    -- Access key of Google Cloud account
            secret_key (str)    -- Secret key of Google Cloud account
            url (str)           -- Region to which the account is pointed

        Returns:
            object - Object storage if client is created successfully
        """

        self._select_vendor()
        self._set_client_name(name)
        self._set_host_url(url)
        if credential is not "":
            self._set_credential(credential)
        else:
            self._click_plus_for_new_credential()
            self._set_credential_name('automation-credential')
            self._set_access_name(access_key)
            self._set_access_pwd(secret_key)
            self.submit()
        self._set_access_node(proxy_client)
        self._set_plan(backup_plan)
        self.submit()


class CreateS3Client(_NewClient):
    """
    Class to create Create Amazon S3 Object Storage Client
    """

    @property
    def vendor_name(self):
        """
        Returns:
            object  -  host url of the vendor
        """
        return self._admin_console.props['label.clientType.amazonS3']

    @PageService()
    def create_client(
            self, name, proxy_client,
            auth_type,
            backup_plan, url,
            credential=None,
            access_key=None,
            secret_key=None,
            role_arn=None
    ):
        """
        Creates Amazon S3 Object Storage Client
        Args:
            name (str)          -- Name of client to be created
            proxy_client (str)  -- Name of proxy client
            auth_type(str)      -- Type of Authentication(Keys/IAM/STS)
                Accepted values - Access and secret keys / IAM role / STS assume role with IAM role
            backup_plan(str)    -- Name of backup plan
            url (str)           -- Region to which the account is pointed
            credential (str)    -- Credential to set for Object Storage account
            access_key (str)    -- Access key of S3 Cloud account
            secret_key (str)    -- Secret key of S3 Cloud account
            role_arn (str)      -- Role ARN of STS Assume Role

        Returns:
            object - Object storage if client is created successfully
        """

        self._select_vendor()
        self._set_client_name(name)
        self._set_host_url(url)
        self._click_authentication_type()
        self._select_authentication_type(auth_type)
        if auth_type is not 'IAM role':
            if credential is not "":
                self._set_credential(credential)
            else:
                if auth_type is 'Access and secret keys':
                    self._click_plus_for_new_credential()
                    self._set_credential_name('automation-credential')
                    self._set_access_name(access_key)
                    self._set_access_pwd(secret_key)
                    self.submit()
                else:
                    self._click_plus_for_new_credential()
                    self._set_credential_name('automation-credential')
                    self._set_role_arn(role_arn)
        self._set_access_node(proxy_client)
        self._set_plan(backup_plan)
        self.submit()


class CreateAzureFileShare(_NewClient):
    """
    Class to create  Amazon S3 Object Storage Client
    """

    @property
    def vendor_name(self):
        """
        Returns:
            object  -  host url of the vendor
        """
        return self._admin_console.props['label.clientType.azureFile']

    @PageService()
    def create_client(
            self, name, proxy_client,
            backup_plan,
            url="file.core.windows.net",
            credential=None,
            access_key=None,
            secret_key=None
    ):
        """
        Creates Azure Blob Object Storage Client
        Args:
            name (str)          -- Name of client to be created
            proxy_client (str)  -- Name of proxy client
            backup_plan(str)    -- Name of backup plan
            url (str)           -- Region to which the account is pointed
            credential (str)    -- Credential to set for Object Storage account
            access_key (str)    -- Access key of Azure Cloud account
            secret_key (str)    -- Secret key of Azure Cloud account
        Returns:
            object - Object storage if client is created successfully
        """

        self._select_vendor()
        self._set_client_name(name)
        self._set_host_url(url)
        if credential is not "":
            self._set_credential(credential)
        else:
            self._click_plus_for_new_credential()
            self._set_credential_name('automation-credential')
            self._set_access_name(access_key)
            self._set_access_pwd(secret_key)
            self.submit()
        self._set_access_node(proxy_client)
        self._set_plan(backup_plan)
        self.submit()


class _RNewClient(Wizard):
    """class for object storage client creation with react screens"""

    def __init__(self, admin_console):
        super().__init__(adminconsole=admin_console)
        self.config_file = config.get_config()
        self.__admin_console = admin_console
        self.wizard = Wizard(adminconsole=self.__admin_console)
        self.dialog = RModalDialog(self.__admin_console)

    @property
    @abstractmethod
    def vendor_name(self):
        """Override this method and implement it as a variable whose
        value is set to the host url as per the vendor"""
        raise NotImplementedError

    def _select_vendor(self):
        """Selects vendor"""
        self.select_radio_card(self.vendor_name)
        self.click_next()
        self.__admin_console.wait_for_completion()

    def _set_client_name(self, name):
        """
        set Client name
        Args:
            name (str): Client name
        """
        self.__admin_console.fill_form_by_id('objectStorageName', name)

    def _set_host_url(self, url):
        """
        set Cloud storage host url
        Args:
            url (str): Cloud storage host url
        """
        self.__admin_console.fill_form_by_id('hostURL', url)

    def _set_credential(self, credential_name):
        """
        sets credential from dropdown
        Args:
            credential_name (str): Credential Name
        """
        self.select_drop_down_values(id='credentials',
                                     values=[credential_name])

    def _click_plus_for_new_credential(self):
        """
        click plus to add new credential
        """
        self.click_add_icon()

    def _set_access_pwd(self, key):
        """
        set Cloud storage account key or secret key
        Args:
            key (str): account key
        """
        if self.__admin_console.check_if_entity_exists("id", 'secretAccessKey'):
            self.__admin_console.fill_form_by_id('secretAccessKey', key)
        elif self.__admin_console.check_if_entity_exists("id", 'apiKey'):
            self.__admin_console.fill_form_by_id('apiKey', key)
        else:
            raise NoSuchElementException(f"Element not found for {key}")

    def _set_user_name(self, name):
        """
        set Cloud storage name
        Args:
            name (str): Client name
        """
        if self.__admin_console.check_if_entity_exists("id", 'accessKeyId'):
            self.__admin_console.fill_form_by_id('accessKeyId', name)
        elif self.__admin_console.check_if_entity_exists("id", 'userAccount'):
            self.__admin_console.fill_form_by_id('userAccount', name)
        else:
            raise NoSuchElementException(f"Element not found for {name}")

    def _set_ad_account_name(self, name):
        """
        set Cloud storage name
        Args:
            name (str): Client name
        """
        self.fill_text_in_field(id='adAccountName', text=name)

    def _set_tenant_ocid(self):
        """
        Sets tenant ocid for credentials
        """
        self.__admin_console.fill_form_by_id('tenancyOCID', self.config_file.ObjectStorage.oci.tenancy)

    def _set_user_ocid(self):
        """
        Sets user ocid for credentials
        """
        self.__admin_console.fill_form_by_id('userOCID', self.config_file.ObjectStorage.oci.user_id)

    def _set_finger_print(self):
        """
        Sets finger_print for credentials
        """
        self.__admin_console.fill_form_by_id('fingerprint', self.config_file.ObjectStorage.oci.fingerprint)

    def _set_private_key(self):
        """
        uploads pem file
        """
        self.__admin_console.driver.find_element(By.XPATH, "//input[@accept='.pem']").send_keys(
            self.config_file.ObjectStorage.oci.private_key_path)

    def _set_private_key_password(self):
        """
        Sets private_key_password for credentials
        """
        self.__admin_console.fill_form_by_id('privateKeysPassword',
                                             self.config_file.ObjectStorage.oci.private_key_password)

    def _set_credential_name(self, name):
        """
        set Credential Name
        Args:
            name (str): Credential Name
        """
        self.__admin_console.fill_form_by_id('name', name)

    def _set_access_node(self, name):
        """
        set Cloud storage access node
        Args:
            name (str): Plan name
        """
        self.select_drop_down_values(id='accessNodes',
                                     values=list(name.split(',')))
        self.click_next()
        self.__admin_console.wait_for_completion()

    def _set_plan(self, name):
        """
        set Cloud storage name
        Args:
            name (str): Plan name
        """
        self.select_plan(name)
        self.click_next()
        self.__admin_console.wait_for_completion()

    def _create_cloud_account(self, name, subscription_id):
        """
             set Cloud account name
             Args:
                 name (str): account name
                 subscription_id (str) : subscription id
             """
        self.dialog.select_radio_by_id("customConfig")
        self.dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.dialog.fill_text_in_field('name', name)
        self.dialog.fill_text_in_field('subscriptionId', subscription_id)

    def _select_authentication_type(self, name):
        """
        selects Authentication type
        Args:
            name(str): Authentication type
        """
        self.select_drop_down_values(id='authenticationMethod', values=[name])

    def _set_role_arn(self, role_arn):
        """
               sets role ARN
               Args:
                   role_arn(str): Role ARN
               """
        self.__admin_console.fill_form_by_id('roleArn', role_arn)

    def _set_account_name(self, name):
        """
        set Cloud storage account name
        Args:
            name (str): account name
        """
        self.__admin_console.fill_form_by_id('accountName', name)

    def _set_tenant_id(self, tenant_id):
        """
        sets tenant ID for AD application authentication
        Args:
            tenant_id(str): tenant id
        """
        self.__admin_console.fill_form_by_id("tenantId", tenant_id)

    def _set_application_id(self, application_id):
        """
        sets tenant ID for AD application authentication
        Args:
            application_id(str): application id
        """
        self.__admin_console.fill_form_by_id("applicationId", application_id)

    def _set_application_secret(self, key):
        """
        sets tenant ID for AD application authentication
        Args:
            key(str): secret key
        """
        self.__admin_console.fill_form_by_id("applicationSecret", key)

    def __wait_for_the_browse_elements(self, xpath, wait_time=150):
        """waits for the browse elements to appear"""
        curr_time = 0
        while not self.__admin_console.check_if_entity_exists("xpath", xpath) and curr_time < wait_time:
            time.sleep(3)
            self.__admin_console.log.info("waiting for browse contents to appear")
            curr_time += 3
        if curr_time >= wait_time:
            raise CVWebAutomationException("browse contents didn't loaded")

    @WebAction()
    def _browse_and_select(self, path):
        """selects the entities in browse screen with given path
            Args:
                path(str) -- path of the entity
        """
        path = path.split('/')
        if path and path[0] == '':
            path.pop(0)

        self.__wait_for_the_browse_elements(f"//span[text()='{path[0]}']/ancestor::span[@class='k-treeview-leaf']")
        for i in range(len(path) - 1):
            self.__admin_console.click_by_xpath(
                f"//span[text()='{path[i]}']/ancestor::span[@class='k-treeview-leaf']/preceding-sibling::span")
            self.__admin_console.wait_for_completion()
        xpath = f"//span[text()='{path[-1]}']/ancestor::span[@class='k-treeview-leaf']/preceding-sibling::div"
        self.__admin_console.scroll_into_view(xpath)
        self.__admin_console.click_by_xpath(xpath)
        self.__admin_console.wait_for_completion()

    @PageService()
    def _select_content(self, contents):
        """
        Completes select backup content step in client creation
        Args:
            contents(str) -- backup contents
        """
        self.__admin_console.click_button("Add")
        self.__admin_console.click_button("Browse")
        self.__admin_console.wait_for_completion()
        for content in contents:
            self._browse_and_select(content)
        self.__admin_console.click_button("Save")
        self.__admin_console.wait_for_completion()
        self.click_next()
        self.__admin_console.wait_for_completion()

    @PageService()
    def _select_subscription_backup_content(self, account_name):
        """ Method to select storage account in the Backup Content step
              Args:
                  account_name (str) -- name of the storage account to be selected
        """
        self.wizard.click_add_icon()
        self.__admin_console.wait_for_completion()
        self.wizard.click_element("//ul[contains(@class, 'MuiList-root')]/li[contains(text(), 'Storage accounts')]")
        self.__admin_console.wait_for_completion()
        dialog = RModalDialog(admin_console=self.__admin_console)
        self._browse_and_select(account_name)
        dialog.click_submit()
        self.wizard.click_next()
        self.__admin_console.wait_for_completion()

    @PageService()
    def _run_discover_instance(self) -> str:
        """ Runs a discover instance job
            Returns:
                jobid (str) : job id of the discover instances job

        """
        self.__admin_console.click_button_using_text(self.__admin_console.props['pageHeader.discoverInstances'])
        jobid = self.__admin_console.get_jobid_from_popup()
        if not jobid:
            raise Exception("Discover Instance Job cannot be started, please check the logs")
        return jobid

    @PageService()
    def _select_compartment(self, path):
        """
        Completes select compartment step in OCI client creation
        Args:
                path(str) -- path of the compartment
        """
        self._browse_and_select(path)
        self.click_next()
        self.__admin_console.wait_for_completion()


class RCreateObjectStorageClient(_RNewClient):
    """
    Class to Create an Object Storage Client from react wizard
    """

    def __init__(self, admin_console, vendor_name, commcell):
        super().__init__(admin_console=admin_console)
        self.__admin_console = admin_console
        self.vendor_name_map = {"Azure Blob": 'label.clientType.azureBlob', "Azure File": 'label.clientType.azureFile',
                                "Alibaba Cloud OSS": 'label.clientType.alibabaOSS',
                                "Azure Data Lake Storage Gen2": 'label.clientType.azureDataLake',
                                "Amazon S3": 'label.clientType.amazonS3',
                                "Google Cloud": 'label.clientType.googleCloud',
                                "IBM Cloud Object Storage": 'label.clientType.ibmCOS',
                                "OCI Object Storage": "label.clientType.oracleCloudInfrastructure"}
        self.cloud_vendor_name = vendor_name
        self.db_helper = DbHelper(commcell)
        self.cred_dialog = RModalDialog(self.__admin_console, title="Add credential")

    @property
    def vendor_name(self):
        """
        Returns:
            object  -  host url of the vendor
        """
        return self.__admin_console.props[self.vendor_name_map[self.cloud_vendor_name]]

    @PageService()
    def create_client(
            self, name, proxy_client,
            auth_type,
            backup_plan,
            url,
            credential=None,
            access_key=None,
            secret_key=None,
            tenant_id=None,
            app_id=None,
            app_secret_key=None,
            backup_content=None,
            role_arn=None,
            compartment_path=None,
            cloud_name=None,
            subscription_id=None
    ):
        """
        Creates Object Storage Client
        Args:
            name (str)          -- Name of client to be created
            proxy_client (str)  -- Name of proxy client
            auth_type(str)         -- type of authentication (Keys/IAM VM/IAM AD)
            backup_plan(str)    -- Name of backup plan
            url (str)           -- url of Azure Blob Account
            credential (str)    -- Credential to set for Object Storage account
            access_key (str)    -- Access key of Azure Cloud account
            secret_key (str)    -- Secret key of Azure Cloud account
            tenant_id(str)      -- Tenant id of ad application
            app_id(str)         -- Application id of AD Application
            app_secret_key(str) -- Application secret key of AD Application
            backup_content(list) -- content to set from wizard
            role_arn(str)       -- role arn of the sts client
            compartment_path(str)--compartment path for oci client
            cloud_name(str) -- Name of cloud account for azure datalake/blob
            subscription_id(str) -- Subscription id of AD application
        Returns:
            object - Object storage if client is created successfully
        """

        self._select_vendor()

        # Step 1. Select Plan
        self._set_plan(backup_plan)

        # Step 2. Select Access Node
        self._set_access_node(proxy_client)

        if self.cloud_vendor_name not in ['Azure Data Lake Storage Gen2', 'Azure Blob']:
            # Step 3. Add object storage
            self._set_client_name(name)
            self._set_host_url(url)
            if self.cloud_vendor_name == "Amazon S3":
                self._select_authentication_type(auth_type)
        else:
            # Step 3. Add cloud account
            self.click_add_icon()
            self.__admin_console.wait_for_completion()
            self._create_cloud_account(cloud_name, subscription_id)

        # Add object storage or Cloud account step's credential creation / selection
        credential_name = None
        if auth_type != 'IAM role':
            if credential:
                self.select_drop_down_values("credentials", [credential])

            elif not credential and self.cloud_vendor_name in ['Azure Blob', 'Azure Data Lake Storage Gen2']:
                credential_name = f'automation-credential-{int(time.time())}'
                self.dialog.click_add()
                self.cred_dialog.fill_input_by_xpath(text=credential_name, element_id='name')
                self.cred_dialog.fill_input_by_xpath(text=tenant_id, element_id='tenantId')
                self.cred_dialog.fill_input_by_xpath(text=app_id, element_id='applicationId')
                self.cred_dialog.fill_input_by_xpath(text=app_secret_key, element_id='applicationSecret')
                self.cred_dialog.click_submit()
                self.__admin_console.wait_for_completion()
                self.dialog.click_submit()
            else:
                credential_name = f'automation-credential-{int(time.time())}'
                self._click_plus_for_new_credential()
                self._set_credential_name(credential_name)
                if auth_type == 'Access and secret keys':
                    self._set_user_name(access_key)
                    self._set_access_pwd(secret_key)
                elif auth_type == 'Access key and Account name':
                    self._set_account_name(access_key)
                    self._set_user_name(secret_key)
                elif auth_type == 'IAM AD application':
                    self._set_tenant_id(tenant_id)
                    self._set_application_id(app_id)
                    self._set_application_secret(app_secret_key)
                elif auth_type == 'STS assume role with IAM policy':
                    self._set_role_arn(role_arn)
                elif auth_type == 'oci_iam':
                    self._set_tenant_ocid()
                    self._set_user_ocid()
                    self._set_finger_print()
                    self._set_private_key()
                    self._set_private_key_password()
                self.__admin_console.click_button_using_text('Save')
                self.__admin_console.wait_for_completion()
                if auth_type == 'IAM VM role' or auth_type == 'IAM AD application':
                    self._set_ad_account_name(access_key)
        self.click_next()
        self.__admin_console.wait_for_completion()

        # OCI specific step
        if self.cloud_vendor_name == "OCI Object Storage":
            self._select_compartment(compartment_path)

        # Step 4. Select Backup Content
        if self.cloud_vendor_name in ['Azure Blob', 'Azure Data Lake Storage Gen2']:
            self._select_subscription_backup_content(backup_content)
        else:
            self._select_content(backup_content)

        # Step 5. Click Finish
        self.click_button('Finish')

        # Run discover instances - Azure specific
        if self.cloud_vendor_name in ['Azure Blob', 'Azure Data Lake Storage Gen2']:
            jobid = self._run_discover_instance()
            if jobid:
                self.db_helper.wait_for_job_completion(jobid)
            else:
                raise Exception("Client discovery failed. No job ID obtained.")
        self.__admin_console.wait_for_completion()
        return credential_name


class CreateAzureBlob(_RNewClient):
    """
    Class to Creates a Azure Blob Object Storage Client
    """
    def __init__(self, admin_console, commcell):
        super().__init__(admin_console=admin_console)
        self.__admin_console = admin_console
        self.db_helper = DbHelper(commcell)
        self.cred_dialog = RModalDialog(self.__admin_console, title="Add credential")

    @property
    def vendor_name(self):
        """
        Returns:
            object  -  host url of the vendor
        """
        return self.__admin_console.props['label.clientType.azureBlob']

    @PageService()
    def create_client(
            self, proxy_client,
            backup_plan,
            backup_content=None,
            tenant_id=None,
            app_id=None,
            app_secret_key=None,
            subscription_id=None,
            cloud_name=None,
            credential=None
    ):
        """
        Creates Azure Blob Object Storage Client
        Args:
            proxy_client (str)   -- Name of proxy client
            backup_plan(str)     -- Name of backup plan
            tenant_id(str)       -- Tenant id of ad application
            app_id(str)          -- Application id of AD Application
            app_secret_key(str)  -- Application secret key of AD Application
            cloud_name(str)      -- Name of cloud account for azure datalake/blob
            subscription_id(str) -- Subscription id of AD application
            backup_content(list) -- content to set from wizard
            credential (str)     -- Credential to be selected
        Returns:
            object - Object storage if client is created successfully
        """

        self._select_vendor()

        # Step 1. Select Plan
        self._set_plan(backup_plan)

        # Step 2. Select Access Node
        self._set_access_node(proxy_client)

        # Step 3. Add cloud account
        self.click_add_icon()
        self.__admin_console.wait_for_completion()
        self._create_cloud_account(cloud_name, subscription_id)

        credential_name = None
        if credential:
            self.select_drop_down_values("credentials", [credential])
        else:
            # Add cloud account step's credential creation / selection
            credential_name = f'automation-credential-{int(time.time())}'
            self.dialog.click_add()
            self.cred_dialog.fill_input_by_xpath(text=credential_name, element_id='name')
            self.cred_dialog.fill_input_by_xpath(text=tenant_id, element_id='tenantId')
            self.cred_dialog.fill_input_by_xpath(text=app_id, element_id='applicationId')
            self.cred_dialog.fill_input_by_xpath(text=app_secret_key, element_id='applicationSecret')
            self.cred_dialog.click_submit()
            self.__admin_console.wait_for_completion()
            self.dialog.click_submit()
        self.click_next()
        self.__admin_console.wait_for_completion()

        # Step 4. Select Backup Content
        self._select_subscription_backup_content(backup_content)

        # Step 5. Click Finish
        self.click_button('Finish')

        # Run discover instances - Azure specific
        jobid = self._run_discover_instance()
        if jobid:
            self.db_helper.wait_for_job_completion(jobid)
        else:
            raise Exception("Client discovery failed. No job ID obtained.")
        self.__admin_console.wait_for_completion()

        return credential_name

