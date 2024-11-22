# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Module for Configuring Object Storage clients from command center.

ObjectStorageMetallic: Class to set common options while creating Object Storage instances with react metallic pages

    select_trial_subscription()         -- Clicks on Start trial subscription dialog

    _select_region()                    --  Selects the region

    _click_generate_link()              --  Clicks on generate link for OCI and S3 backup gateway

    __wait_for_backup_gateway_template()--  Waits for launch cloudformation stack link to appear

    _get_backup_gateway_stack_url()     --  gets the Backup Gateway stack deployment URL

    _select_backup_gateway()            --  Selects the backup gateway

    _select_storage_account()           --  Selects the storage account

    _start_trail_for_mrr()              --  Begins start trial for MRR storage.

    browse_and_select()                 --  selects the entities in browse screen with given path

    select_content()                    --  Completes select backup content step in OCI client creation

    _set_plan()                         --  Sets the plan

    _create_plan()                      --  creates plan with default settings

    select_oss_vendor()                 --  selects the OSS vendor to be configured

    _get_authcode()                      --  Method to return authcode

ROCIObjectStorageInstance:  Class for creating OCI object storage client in Metallic page

    _get_iam_stack_url()                  --  gets the IAM stack deployment URL

    _upload_private_key()                 --    Uploads private key file for OCI credentials

    _create_oci_credentials()             --    method to create credentials

    _create_byos_oci()                    --    method to create storage account

    _create_mrr_storage()                 --    creates MRR OCI storage as secondary

    _create_oci_backup_gateway()          --    method to create new backup gateway

    select_compartment()                  --    Completes select compartment step in OCI client creation

    select_content()                      --    Completes select backup content step in OCI client creation

    _create_oci_client()                   --   Creates OCI Object Storage client

    configure()                            --   Method to run through all the steps in the wizard for OCI client creation

    oci_cleanup()                          --   Cleanups the resources created during the client creation

RAzureObjectStorageInstance:    Class for creating Azure object storage clients in Metallic page

    _create_azure_credentials()            --   Method to create credentials for azure clients

    _create_byos_blob()                    --   Method to create BYOS storage

    _create_mrr_storage()                  --   creates MRR Azure storage as secondary

    _create_azure_client()                 --   Method to create azure client

    _create_azure_subscription_client()            --   Method to create azure blob client

    _select_subscription_backup_content()          --   Method to add storage account for azure blob client

    _run_discover_instance()                --   Method to run discover instances job for azure blob client

    _select_backup_method()                 --   Selecting the backup method

    _create_backup_gateway()                --   Creates backup gateway in Azure

    azure_cleanup()                         --   cleans up the resources created during testcase execution

    configure()                             --   Method to run through all the steps in the wizard for Azure client creation

S3ObjectStorageInstance:    Class for creating S3 object storage client in Metallic page

    __confirm_iam_stack_created()          --   confirms the iam stack is created

    __get_iam_stack_url()                  --   gets the IAM stack deployment URL

    __select_backup_method()               --   Selecting the backup method

    __select_authentication()              --   Selects authentication for S3

    __create_backup_gateway()              --   Creates backup gateway in AWS

    __create_s3_credentials()              --   Method to create credentials

    __create_byos_s3()                     --   Method to create BYOS storage

    _create_mrr_storage()                  --   creates MRR Azure storage as secondary

    __create_s3_client()                   --   Method to create S3 client

    configure()                            --   Method to run through all the steps in the wizard for S3 client creation

    s3_cleanup()                           --   cleans up the resources created during testcase execution
"""
import time
from Application.CloudStorage.oci_helper import OCIMetallicHelper
from Application.CloudStorage.s3_helper import S3MetallicHelper
from AutomationUtils import config, logger
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Hub.constants import HubServices, FileObjectTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.object_storage import ObjectStorage as HubObjectStorage
from Web.AdminConsole.Hub.utils import Utils
from Web.Common.page_object import PageService, WebAction
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from selenium.webdriver.common.by import By
from Database.dbhelper import DbHelper
from Application.CloudApps.azure_helper import AzureResourceGroup, AzureCustomDeployment
from Web.AdminConsole.Hub.Databases.databases import RDatabasesMetallic


class ObjectStorageMetallic:
    """Class to set common options while creating Object Storage instances with react metallic pages"""

    def __init__(self, admin_console, vendor_type):
        """ Initialize the class

        Args:
            admin_console(AdminConsoleBase): instance of AdminConsoleBase

            vendor_type(str) : type of object storage vendor

        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.wizard = Wizard(admin_console)
        self.service = HubServices.object_storage
        self.service_catalogue = ServiceCatalogue(admin_console, service=self.service)
        self.app_type = FileObjectTypes.object_storage
        self.oss_vendor_type = vendor_type
        self.hub_dashboard = Dashboard(self._admin_console, self.service, self.app_type)
        self.hub_object_storage = HubObjectStorage(self._admin_console, vendor_type)
        self.utils_helper = Utils(self._admin_console)
        self.config_file = config.get_config()
        self.log = logger.get_log()
        self.table = Table(self._admin_console)
        self.rdropdown = RDropDown(self._admin_console)
        self._props = None
        self.azure_rg = AzureResourceGroup()
        self.azure_deployment = AzureCustomDeployment()
        self.db_metallic = RDatabasesMetallic(self._admin_console, "")

    @PageService()
    def select_trial_subscription(self):
        """ Clicks on Start trial subscription dialog
        """
        self.utils_helper.submit_dialog()
        self._admin_console.wait_for_completion()
        self.utils_helper.submit_dialog()
        self._admin_console.wait_for_completion()

    @PageService()
    def _select_region(self, region):
        """Selects the region"""
        self.wizard.select_drop_down_values(
            id='storageRegion', values=[region], partial_selection=True)
        self.wizard.click_next()

    @WebAction()
    def _click_generate_link(self):
        """Clicks on generate link for OCI and S3 backup gateway"""
        self._admin_console.click_by_xpath(
            "//button[contains(@class, 'MuiButtonBase-root')]/div[text()='Generate link']")

    @PageService()
    def __wait_for_backup_gateway_template(self, wait_time=150):
        """Waits for launch cloudformation stack link to appear"""
        curr_time = 0
        path = ("//a[contains(text(),'CloudFormation')] |"
                "//a[contains(text(),'Oracle Cloud Resource Stack')]")
        while not self._admin_console.check_if_entity_exists("xpath", path) and curr_time < wait_time:
            time.sleep(3)
            self._admin_console.log.info("waiting for Launch Stack URL.")
            curr_time += 3
        if curr_time >= wait_time:
            raise TimeoutError("Took more than expected time for loading launch cloud formation url")

    @PageService()
    def _get_backup_gateway_stack_url(self):
        """gets the Backup Gateway stack deployment URL"""
        self._click_generate_link()
        self.__wait_for_backup_gateway_template()
        path = ("//a[contains(text(),'CloudFormation')] |"
                "//a[contains(text(),'Oracle Cloud Resource Stack')]")
        return self._driver.find_element(By.XPATH, path).get_attribute('href')

    @PageService()
    def _select_backup_gateway(self, instance):
        """Selects the backup gateway"""
        self.wizard.click_refresh_icon()
        self.wizard.select_drop_down_values(
            id='accessNodes', values=[instance], wait_for_content_load=True)
        self.wizard.click_next()

    @PageService()
    def _select_storage_account(self, region):
        """Selects the storage account"""
        self.wizard.select_drop_down_values(
            id='metallicCloudStorageDropdown', values=[region])
        self.wizard.click_next()

    @PageService()
    def _start_trail_for_mrr(self):
        """Begins start trial for MRR storage"""
        storage_dialog = RModalDialog(admin_console=self._admin_console, title='Add cloud storage')
        storage_dialog.click_button_on_dialog('Start trial')
        self._admin_console.wait_for_completion()
        trial_dialog = RModalDialog(admin_console=self._admin_console,
                                    title='Successfully created a trial subscription')
        trial_dialog.click_button_on_dialog('Close')
        self._admin_console.wait_for_completion()

    @WebAction()
    def browse_and_select(self, path):
        """selects the entities in browse screen with given path
            Args:
                path(str) -- path of the entity
        """
        path = path.split('/')
        for i in range(len(path) - 1):
            self._admin_console.click_by_xpath(
                f"//span[text()='{path[i]}']/ancestor::span[@class='k-treeview-leaf']/preceding-sibling::span")
            self._admin_console.wait_for_completion()
        self._admin_console.click_by_xpath(
            f"//span[text()='{path[-1]}']/ancestor::span[@class='k-treeview-leaf']/preceding-sibling::div")
        self._admin_console.wait_for_completion()

    @PageService()
    def select_content(self, contents):
        """
        Completes select backup content step in OCI client creation
        Args:
            contents(str) -- backup contents
        """
        self._admin_console.click_button("Add")
        self._admin_console.click_button("Browse")
        self._admin_console.wait_for_completion()
        for content in contents:
            self.browse_and_select(content)
        self._admin_console.click_button("Save")
        self._admin_console.wait_for_completion()
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def _set_plan(self, name):
        """
        Sets the plan
        Args:
            name    (str)  :    The name of the plan
        """
        self.wizard.fill_text_in_field(id='searchPlanName', text=name)
        self.wizard.select_plan(name)
        self.wizard.click_next()

    @PageService()
    def _create_plan(self, name):
        """create plan with default settings
            Args:
                name(str): name of the plan for the plan creation.
        """
        self.wizard.click_add_icon()
        self._admin_console.wait_for_completion()
        self._admin_console.fill_form_by_id('planNameInputFld', name)
        self.db_metallic.click_looped_submit()
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def select_oss_vendor(self, vendor_name):
        """selects the OSS vendor to be configured"""
        try:
            self.service_catalogue.choose_service_from_service_catalogue(service=self.service.value, id=vendor_name)
        except Exception as exp:
            raise CVWebAutomationException(f"Exception raised in select_oss_vendor() Error: '{exp}'") from exp

    @WebAction()
    def _get_authcode(self):
        """ Method to return authcode """
        xpath = "//div//p[contains(text(), 'Commvault Cloud auth code')]/following-sibling::b"
        auth_code = self._admin_console.driver.find_element(By.XPATH, xpath).text
        return auth_code


class ROCIObjectStorageInstance(ObjectStorageMetallic):
    """Class for creating OCI object storage client in Metallic page"""

    def __init__(self, admin_console, vendor_type, oci_config):
        """Initializes the class
            Args:
            admin_console: instance of AdminConsoleBase

            vendor_type: type of object storage vendors

            oci_config: configs for authenticating with OCI cloud
        """
        super().__init__(admin_console, vendor_type)
        self.oci_metallic_helper = OCIMetallicHelper(oci_config)

    @WebAction()
    def _get_iam_stack_url(self):
        """gets the IAM stack deployment URL"""
        path = "//a[contains(text(),'Deploy to Oracle cloud')]"
        return self._driver.find_element(By.XPATH, path).get_attribute('href')

    @WebAction()
    def _upload_private_key(self):
        """Uploads private key file for OCI credentials"""
        self._driver.find_element(By.XPATH, "//input[@name='fileInput']").send_keys(
            self.config_file.ObjectStorage.oci.private_key_path)

    @PageService()
    def _create_oci_credentials(self):
        """method to create credentials"""
        dialog = RModalDialog(admin_console=self._admin_console, title='Add credential')
        stack_url = self._get_iam_stack_url()
        oci_config = self.oci_metallic_helper.configure_oci_role(stack_url)
        self.wizard.click_add_icon()
        self._admin_console.wait_for_completion()
        credential_name = f'OCIcred{time.time()}'
        dialog.fill_text_in_field("name", credential_name)
        dialog.fill_text_in_field("tenancyOCID", self.config_file.ObjectStorage.oci.tenancy)
        dialog.fill_text_in_field("userOCID", oci_config.user_id)
        dialog.fill_text_in_field("fingerprint", oci_config.fingerprint)
        self._upload_private_key()
        dialog.fill_text_in_field("privateKeysPassword", self.config_file.ObjectStorage.oci.private_key_password)
        self._admin_console.click_button('Save')
        return credential_name

    @PageService()
    def _create_byos_oci(self, storage_name, compartment_name, credential, standard=True):
        """method to create storage account
            Args:
                storage_name(str) -- name of the BYOS cloud storage

                compartment_name(str) -- name of the compartment in which this storage need to be created

                credential(str) -- credententials for creating this storage

                standard(bool) -- storage class is standard to infrequent
                 default : True
        """
        self.wizard.click_add_icon()
        self._admin_console.wait_for_completion()
        dialog = RModalDialog(admin_console=self._admin_console, title='Add cloud storage')
        dialog.select_dropdown_values(drop_down_id='cloudType', values=['Oracle Cloud Infrastructure Object Storage'])
        dialog.fill_text_in_field(element_id='cloudStorageName', text=storage_name)
        dialog.select_dropdown_values(drop_down_id='savedCredential', values=[credential])
        dialog.fill_text_in_field(element_id="configureCloudLibrary.CompartmentName", text=compartment_name)
        dialog.fill_text_in_field(element_id='mountPath', text=storage_name)
        if standard:
            dialog.select_dropdown_values(drop_down_id='storageClass', values=['Standard'])
        else:
            dialog.select_dropdown_values(drop_down_id='storageClass', values=['Standard-Infrequent Access'])
        self.db_metallic.click_looped_submit()

    @PageService()
    def _create_mrr_storage(self, region=None, standard=True):
        """creates MRR OCI storage as secondary
            Args:
                region(str):  region of the MRR storage.

                standard(bool) : storage class type
        """
        dialog = RModalDialog(admin_console=self._admin_console)
        self.rdropdown.wait_for_dropdown_load(drop_down_id='metallicCloudStorageDropdown')
        dialog.enable_toggle('secondaryCopyToggle')
        self.wizard.click_add_icon(index=1)
        self._admin_console.wait_for_completion()
        dialog.select_dropdown_values(drop_down_id='cloudType', values=['Air Gap Protect'])
        if standard:
            dialog.select_dropdown_values(drop_down_id='storageClass', values=['Standard'])
        else:
            dialog.select_dropdown_values(drop_down_id='storageClass', values=['Standard-Infrequent Access'])
        if region:
            dialog.select_dropdown_values(drop_down_id='region', values=[region], partial_selection=True)
        self._start_trail_for_mrr()
        self.db_metallic.click_looped_submit()
        self.wizard.click_next()

    @PageService()
    def _create_oci_backup_gateway(self, os_type, region):
        """method to create new backup gateway"""
        self.wizard.click_add_icon()
        dialog = RModalDialog(admin_console=self._admin_console, title='Add a new backup gateway')
        dialog.select_dropdown_values(drop_down_id='platform', values=[os_type])
        try:
            dialog.select_dropdown_values(drop_down_id='storageRegion', values=[region])
            raise Exception("Region can't be changed for the backup gateway")
        except Exception as exp:
            self.log.warning(exp)
            self.log.info("if the dropdown list has only one value, it will be disabled by selecting the default value")
        stack_url = self._get_backup_gateway_stack_url()
        stack_output = self.oci_metallic_helper.execute_oci_gateway_stack(stack_url)
        time.sleep(60)
        dialog.click_button_on_dialog(text='OK')
        self.wizard.click_refresh_icon()
        gateway = ''
        for resource in stack_output['resources']:
            if resource['type'] == 'oci_core_instance':
                gateway = resource['instances'][0]['attributes']['display_name']
                gateway = f"BackupGateway-{gateway}"
                break
        return gateway

    @PageService()
    def select_compartment(self, path):
        """
        Completes select compartment step in OCI client creation
        Args:
                path(str) -- path of the compartment
        """
        self.browse_and_select(path)
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def _create_oci_client(self, oci_client_name, path):
        """Creates OCI Object Storage client
            Args:
                oci_client_name(str) -- name of the oci client to be created.

                path(str) -- compartment path
        """
        self._admin_console.fill_form_by_id("objectStorageName", oci_client_name)
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        self.select_compartment(path)

    @PageService()
    def configure(self, region, backup_gateway_os_type, byos_storage_name, compartment_name, plan_name, client_name,
                  compartment_path, content, vendor_name):
        """
            Method to run through all the steps in the wizard for OCI client creation
            Args:
                region          (str):  Name of the region

                backup_gateway_os_type  (str):  Backup gateway name os type

                byos_storage_name (str): cloud storage name for primary storage

                compartment_name (str): name of the compartment in which the byos need to be created

                plan_name(str): name of the plan

                client_name(str): name of the oci client

                compartment_path(str): backup content compartment path

                content(str): backup content

                vendor_name (str) :name of the vendor
            """
        self.select_oss_vendor(vendor_name)
        self.wizard.click_next()
        credential_name = self._create_oci_credentials()
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        self._select_region(region)
        backup_gateway = self._create_oci_backup_gateway(os_type=backup_gateway_os_type, region=region)
        self._select_backup_gateway(backup_gateway)
        self._create_byos_oci(byos_storage_name, compartment_name, credential_name)
        self._create_mrr_storage()
        self._create_plan(plan_name)
        self._create_oci_client(client_name, compartment_path)
        self.select_content(content)
        self.wizard.click_button('Finish')
        self._admin_console.wait_for_completion()
        return backup_gateway

    def oci_cleanup(self):
        """Cleanups the resources created during the client creation"""
        self.oci_metallic_helper.cleanup()


class RAzureObjectStorageInstance(ObjectStorageMetallic):
    """Class for creating Azure object storage clients in Metallic page"""

    # class variable to map the backup method with the radio button id
    backup_method_map = {
        "Azure Blob": {
            "Gateway": "AzureBlobBackupGatewayOverviewimage",
            "Infrastructure": "ObjectStorageOverviewAzureBlob"
        },
        "Azure File": {
            "Gateway": "AzreFilesBackupGatewayOverviewimage",
            "Infrastructure": "ObjectStorageOverviewAzureFile"
        },
        "Azure Data Lake Storage Gen2": {
            "Gateway": "AzureDataLakeBackupGatewayOverview",
            "Infrastructure": "ObjectStorageOverviewAzureDataLake"
        }
    }

    def __init__(self, admin_console, vendor_type, commcell):
        """Initializes the class
            Args:
            admin_console: instance of AdminConsoleBase

            vendor_type: type of object storage vendors

            commcell: instance of commcell
        """
        super(RAzureObjectStorageInstance, self).__init__(admin_console, vendor_type)
        self.commcell = commcell
        self.db_helper = DbHelper(self.commcell)

    @PageService()
    def _create_azure_credentials(self, auth_type, **kwargs):
        """Method to create credentials for azure clients
            Args:
                auth_type(str)  -- authentication method
        """
        dialog = RModalDialog(admin_console=self._admin_console, title='Add credential')
        dialog.fill_text_in_field('name', f'BlobCred{int(time.time())}')
        if auth_type == 'Access key and Account name':
            dialog.fill_text_in_field('accountName', kwargs.get('account_name'))
            dialog.fill_text_in_field('accessKeyId', kwargs.get('access_key'))
        else:
            dialog.fill_text_in_field('tenantId', kwargs.get('tenant_id'))
            dialog.fill_text_in_field('applicationId', kwargs.get('application_id'))
            dialog.fill_text_in_field('applicationSecret', kwargs.get('app_password'))
        dialog.fill_text_in_field('description', "Azure credentials generated through automation")
        dialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def _create_byos_blob(self, storage_name, auth_type, **kwargs):
        """Method to create BYOS storage
            Args:
                storage_name(str) -- name of the BYOS cloud storage

                auth_type (str)  -- authentication type for the storage

            expected keyword args:

                byos_account_name(str) -- account name for the storage

                byos_access_key(str)  -- access key for the storage
        """
        self.wizard.click_add_icon()
        self._admin_console.wait_for_completion()
        dialog = RModalDialog(admin_console=self._admin_console, title='Add cloud storage')
        dialog.select_dropdown_values(drop_down_id='cloudType', values=['Microsoft Azure Storage'])
        dialog.fill_text_in_field(element_id='cloudStorageName', text=storage_name)
        if auth_type == "Access key and Account name":
            dialog.select_dropdown_values(drop_down_id='authentication', values=['Access key and Account name'])
        elif auth_type == 'IAM AD application':
            dialog.select_dropdown_values(drop_down_id='authentication', values=['IAM AD application'])
            dialog.fill_text_in_field(element_id='loginName', text=kwargs.get('byos_account_name'))
        else:
            dialog.select_dropdown_values(drop_down_id='authentication', values=["IAM VM role"])
            dialog.fill_text_in_field(element_id='loginName', text=kwargs.get('byos_account_name'))
        if auth_type != "IAM VM role":
            dialog.click_button_on_dialog(text=None, preceding_label=True, aria_label="Create new")
            self._admin_console.wait_for_completion()
            self._create_azure_credentials(auth_type, **kwargs)
        dialog.select_dropdown_values(drop_down_id='storageClass', values=['Hot'])
        dialog.fill_text_in_field(element_id='mountPath', text=storage_name)
        self.db_metallic.click_looped_submit()

    @PageService()
    def _create_mrr_storage(self, standard=True, **kwargs):
        """creates MRR Azure storage as secondary
        Args:
            standard(bool) -- standard or infrequent storage class need to be selected.
            default: True
        """
        dialog = RModalDialog(admin_console=self._admin_console)
        self.rdropdown.wait_for_dropdown_load(drop_down_id='metallicCloudStorageDropdown')
        dialog.enable_toggle('secondaryCopyToggle')
        self.wizard.click_add_icon(index=1)
        self._admin_console.wait_for_completion()
        dialog.select_dropdown_values(drop_down_id='cloudType', values=['Air Gap Protect'])
        if kwargs.get('backup_method') == 'Gateway':
            dialog.select_dropdown_values(drop_down_id='offering', values=['Azure Blob Storage'])
            dialog.select_dropdown_values(drop_down_id='region', values=['East US 2'], partial_selection=True)
        if standard:
            dialog.select_dropdown_values(drop_down_id='storageClass', values=['Hot tier'])
        else:
            dialog.select_dropdown_values(drop_down_id='storageClass', values=['Cool tier'])
        self._start_trail_for_mrr()
        self.db_metallic.click_looped_submit()
        self.wizard.click_next()

    @PageService()
    def _create_azure_client(self, client_name, auth_type, **kwargs):
        """Method to create azure client
            Args:
                client_name(str) -- name of the azure object storage client

                auth_type(str)  -- authentication type for object storage.
        """
        self._admin_console.fill_form_by_id("objectStorageName", client_name)
        self.wizard.select_drop_down_values(id='authenticationMethod', values=[auth_type])
        self.wizard.click_add_icon()
        self._create_azure_credentials(auth_type, **kwargs)
        if auth_type == 'IAM AD application':
            self.wizard.fill_text_in_field(id='adAccountName', text=kwargs.get('account_name'))
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def _create_azure_subscription_client(self, client_name, auth_type, **kwargs):
        """Method to create azure blob / azure datalake client
            Args:
                client_name(str) -- name of the azure object storage client

                auth_type(str)  -- authentication type for object storage.
        """
        dialog = RModalDialog(admin_console=self._admin_console)
        self.wizard.click_add_icon()
        dialog.fill_text_in_field(element_id='name', text=client_name)
        dialog.fill_text_in_field(element_id='subscriptionId', text=kwargs.get('subscription_id'))
        dialog.click_button_on_dialog(text=None, preceding_label=True, aria_label="Create new")
        self._create_azure_credentials(auth_type, **kwargs)
        dialog.click_submit()
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def _select_subscription_backup_content(self, account_name):
        """ Method to select storage account in the Backup Content step
              Args:
                  account_name (str) -- name of the storage account to be selected
        """
        self.wizard.click_add_icon()
        self.wizard.click_element("//ul[contains(@class, 'MuiList-root')]/li[contains(text(), 'Storage accounts')]")
        dialog = RModalDialog(admin_console=self._admin_console)
        self.browse_and_select(account_name)
        dialog.click_submit()
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def _run_discover_instance(self) -> str:
        """ Runs a discover instance job
            Returns:
                jobid (str) : job id of the discover instances job

        """
        self._admin_console.click_button_using_text('Discover instances')
        jobid = self._admin_console.get_jobid_from_popup()
        if not jobid:
            raise Exception("Discover Instance Job cannot be started, please check the logs")
        return jobid

    @PageService()
    def _select_backup_method(self, backup_method_id):
        """
        Selecting the backup method
        Args:
            backup_method_id              (str):  ID of the backup method radio button

        """
        self.wizard.select_radio_button(id=backup_method_id)

    @PageService()
    def _create_backup_gateway(self, **kwargs):
        """Creates backup gateway in Azure
        expected kwargs:
            gateway_os_type  (str) -- os type of the backup gateway

            rg_location      (str) -- location of the resource group

        returns : list of strings
            resource_group_name(str) -- name of the resource group

            backup_gateway_name(str) -- name of the backup gateway

        """
        self.wizard.click_add_icon()
        dialog = RModalDialog(admin_console=self._admin_console, title='Add new backup gateway')
        dialog.select_dropdown_values(drop_down_id='platformDropdown', values=[kwargs.get('gateway_os_type')])
        resource_group_name = f"AutomationResourceGroup-{int(time.time())}"
        authcode = self._get_authcode()

        if self.azure_rg.check_if_resource_group_exists(resource_group_name):
            self.log.info("Found Resource group- deleting it")
            self.azure_rg.delete_resource_group(rg_name=resource_group_name)
            self.log.info("Resource group is deleted successfully")

        rg_params = {'location': kwargs.get('rg_location')}
        self.azure_rg.create_resource_group(
            rg_name=resource_group_name,
            rg_params=rg_params
        )
        self.log.info("Waiting for the backupgateway deployment to complete")
        self.azure_deployment.deploy(rg_name=resource_group_name, authcode=authcode)
        self.log.info("Deployment successful!")

        dialog.click_button_on_dialog(id='Save')

        backup_gateway_name = self.azure_deployment.get_backup_gateway_name(rg_name=resource_group_name)
        return [resource_group_name, backup_gateway_name]

    def azure_cleanup(self, rg_name):
        """cleans up the resources created during testcase execution
            Args:
                rg_name(str)  -- name of the resource group
        """
        self.azure_rg.delete_resource_group(rg_name=rg_name)

    @PageService()
    def configure(self, byos_storage_name, plan_name, client_name,
                  auth_type='Access key and Account name', region='East US 2', **kwargs):
        """
            Method to run through all the steps in the wizard for Azure client creation
            Args:
                byos_storage_name (str): cloud storage name for primary storage

                plan_name(str): name of the plan

                client_name(str): name of the oci client

                auth_type(str): authentication type for object storage client
                    default:Access key and Account name

                region (str):  Name of the region

            Expected kwargs:
                backup_method(str) -- backup flow to be selected - Infrastructure/Gateway
            """
        vendor = kwargs.get('vendor_name')
        self.select_oss_vendor(vendor)
        self._admin_console.wait_for_completion()
        backup_method_id = self.backup_method_map[vendor][kwargs.get('backup_method')]
        self._select_backup_method(backup_method_id=backup_method_id)
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        self._select_region(region)
        azure_post_deployment_resources = None
        if kwargs.get('backup_method') == 'Gateway':
            azure_post_deployment_resources = self._create_backup_gateway(**kwargs)
            self._select_backup_gateway(azure_post_deployment_resources[1])
        self._create_byos_blob(byos_storage_name, auth_type, **kwargs)
        self._create_mrr_storage(**kwargs)
        self._create_plan(plan_name)
        if vendor in ['Azure Blob', 'Azure Data Lake Storage Gen2']:
            self._create_azure_subscription_client(client_name, auth_type, **kwargs)
            self._select_subscription_backup_content(account_name=kwargs.get('account_name'))
        else:
            self._create_azure_client(client_name, auth_type, **kwargs)
            self.select_content(kwargs.get('content'))
        self.wizard.click_button('Finish')
        self._admin_console.wait_for_completion()
        if vendor in ['Azure Blob', 'Azure Data Lake Storage Gen2']:
            jobid = self._run_discover_instance()
            if jobid:
                self.db_helper.wait_for_job_completion(jobid)
                self.log.info(f"Client discovery completed by discover job id - {jobid}")
            else:
                raise Exception("Client discovery failed. No job ID obtained.")
        return azure_post_deployment_resources


class S3ObjectStorageInstance(ObjectStorageMetallic):
    """Class for creating S3 object storage client in Metallic page"""

    backup_method_map = {
            "Gateway": "AwsS3BackupGateway",
            "Infrastructure": "AwsS3MetallicHostedInfra"
    }

    def __init__(self, admin_console, vendor_type):
        """Initializes the class
            Args:
            admin_console: instance of AdminConsoleBase

            vendor_type: type of object storage vendors
        """
        super().__init__(admin_console, vendor_type)
        self.s3_helper = None

    @WebAction()
    def __confirm_iam_stack_created(self):
        """confirms the iam stack is created"""
        self._admin_console.click_by_xpath("//span[contains(text(),'I confirm that the IAM')]")

    @WebAction()
    def __get_iam_stack_url(self):
        """gets the IAM stack deployment URL"""
        path = "//a[contains(text(),'Launch the CloudFormation Stack')]"
        return self._driver.find_element(By.XPATH, path).get_attribute('href')

    @PageService()
    def __select_authentication(self, auth_type):
        """Selects authentication for S3
        Args:
            auth_type(str) -- Authentication type
        """
        self.wizard.select_drop_down_values(id='authenticationMethod', values=[auth_type])
        iam_stack_url = self.__get_iam_stack_url()
        if auth_type == "Access and Secret Key":
            self.s3_helper.create_stack(stack_name='MetallicUserGroup', stack_url=iam_stack_url,
                                        capabilities=['CAPABILITY_NAMED_IAM'])
        elif auth_type == "IAM Role":
            self.s3_helper.create_stack(stack_name='MetallicRole', stack_url=iam_stack_url,
                                        capabilities=['CAPABILITY_NAMED_IAM'])
        elif auth_type == "STS assume role with IAM policy":
            self.s3_helper.create_stack(stack_name="MetallicAdminRole", stack_url=iam_stack_url,
                                        capabilities=['CAPABILITY_NAMED_IAM'])
        self.__confirm_iam_stack_created()
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def __select_backup_method(self, backup_method_id):
        """
        Selecting the backup method
        Args:
            backup_method_id              (str):  ID of the backup method radio button

        """
        self.wizard.select_radio_button(id=backup_method_id)

    @PageService()
    def __create_backup_gateway(self, **kwargs):
        """Creates backup gateway in AWS"""
        self.wizard.click_add_icon()
        dialog = RModalDialog(admin_console=self._admin_console, title='Add a new backup gateway')
        dialog.select_dropdown_values(drop_down_id='platform', values=[kwargs.get('gateway_os_type')])
        stack_url = self._get_backup_gateway_stack_url()
        gateway_stack = self.s3_helper.create_stack(
            stack_name=kwargs.get('stack_name'),
            stack_url=stack_url, params=kwargs.get('stack_params'))
        time.sleep(80)
        dialog.click_button_on_dialog(text='OK')
        self._admin_console.wait_for_completion()
        self.wizard.click_refresh_icon()
        if kwargs.get('gateway_os_type') == 'Windows':
            backup_gateway_name = f"BackupGateway-{gateway_stack.Resource('WindowsInstance').physical_resource_id}"
        else:
            backup_gateway_name = f"BackupGateway-{gateway_stack.Resource('LinuxInstance').physical_resource_id}"
        return backup_gateway_name

    @PageService()
    def __create_s3_credentials(self, auth_type):
        """Method to create credentials
            Args:
                auth_type(str) -- authentication method
        """
        dialog = RModalDialog(admin_console=self._admin_console, title='Add credential')
        dialog.fill_text_in_field(element_id='name', text=f'S3Cred{int(time.time())}')
        if auth_type == 'Access and Secret Key':
            dialog.fill_text_in_field(element_id='accessKeyId', text=self.config_file.aws_access_creds.access_key)
            dialog.fill_text_in_field(element_id='secretAccessKey', text=self.config_file.aws_access_creds.secret_key)
        else:
            dialog.fill_text_in_field(element_id='roleArn', text=self.config_file.aws_access_creds.tenant_role_arn)
            dialog.fill_text_in_field(element_id='externalId', text=self.config_file.aws_access_creds.external_id)
        dialog.fill_text_in_field(element_id='description', text="S3 credentials generated through automation")
        dialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def __create_byos_s3(self, storage_name, auth_type, byos_bucket_name, standard=True):
        """Method to create BYOS storage
            Args:
                storage_name(str) -- name of the BYOS cloud storage

                auth_type(str) -- type of authentication.

                byos_bucket_name(str) -- bucket name of the BYOS

                standard(bool) -- storage class is standard to infrequent
                 default : True
        """
        self.wizard.click_add_icon()
        self._admin_console.wait_for_completion()
        dialog = RModalDialog(admin_console=self._admin_console, title='Add cloud storage')
        dialog.select_dropdown_values(drop_down_id='cloudType', values=['Amazon S3'])
        dialog.fill_text_in_field(element_id='cloudStorageName', text=storage_name)
        if auth_type == "Access and Secret Key":
            dialog.select_dropdown_values(drop_down_id='authentication', values=['Access and secret keys'])
        elif auth_type == 'STS assume role with IAM policy':
            dialog.select_dropdown_values(drop_down_id='authentication', values=['STS assume role with IAM policy'])
        else:
            dialog.select_dropdown_values(drop_down_id='authentication', values=["IAM role"])
        if auth_type != "IAM Role":
            dialog.click_button_on_dialog(text=None, preceding_label=True, aria_label="Create new")
            self._admin_console.wait_for_completion()
            self.__create_s3_credentials(auth_type)
        dialog.fill_text_in_field(element_id='mountPath', text=byos_bucket_name)
        if standard:
            dialog.select_dropdown_values(drop_down_id='storageClass', values=['S3 Standard'])
        else:
            dialog.select_dropdown_values(drop_down_id='storageClass', values=['S3 Standard-Infrequent Access'])
        self.db_metallic.click_looped_submit()

    @PageService()
    def _create_mrr_storage(self, standard=True, **kwargs):
        """ Creates secondary storage for backup methods.
            For 'Gateway' method, it creates AGP with Azure Blob Storage.
            For 'Infrastructure' method, it creates Amazon S3 BYOS.
            Args:
                standard (bool) -- standard or infrequent storage class need to be selected.
                default: True
            Expected kwargs:
                backup_method(str) -- backup flow to be selected - Infrastructure/Gateway
        """
        dialog = RModalDialog(admin_console=self._admin_console)
        self.rdropdown.wait_for_dropdown_load(drop_down_id='metallicCloudStorageDropdown')
        dialog.enable_toggle('secondaryCopyToggle')
        self.wizard.click_add_icon(index=1)
        self._admin_console.wait_for_completion()
        if kwargs.get('backup_method') == 'Gateway':
            dialog.select_dropdown_values(drop_down_id='cloudType', values=['Air Gap Protect'])
            dialog.select_dropdown_values(drop_down_id='offering', values=['Azure Blob Storage'])
            dialog.select_dropdown_values(drop_down_id='region', values=['East US 2'], partial_selection=True)
            if standard:
                dialog.select_dropdown_values(drop_down_id='storageClass', values=['Hot tier'])
            else:
                dialog.select_dropdown_values(drop_down_id='storageClass', values=['Cool tier'])
        else:
            dialog.select_dropdown_values(drop_down_id='cloudType', values=['Amazon S3'], partial_selection=True)
            # TBD - logic for infrastructure flow
        self._start_trail_for_mrr()
        self.db_metallic.click_looped_submit()
        self.wizard.click_next()

    @PageService()
    def __create_s3_client(self, client_name, auth_type):
        """Method to create S3 client
            Args:
                client_name(str) -- s3 client name

                auth_type(str)  -- authentication type
        """
        wizard = Wizard(self._admin_console)
        self._admin_console.fill_form_by_id("objectStorageName", client_name)
        if auth_type != 'IAM Role':
            wizard.click_add_icon()
            self.__create_s3_credentials(auth_type)
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def configure(self, byos_storage_name, byos_bucket_name, client_name,
                  auth_type, **kwargs):
        """
            Method to run through all the steps in the wizard for S3 client creation
            Args:
                byos_storage_name (str): cloud storage name for primary storage

                byos_bucket_name(str): Name of the byos bucket for storage.

                client_name(str): name of the oci client

                auth_type(str) : authentication type

            Expected kwargs:
                backup_method(str) -- backup flow to be selected - Infrastructure/Gateway
            """
        self.s3_helper = S3MetallicHelper(kwargs.get('region'))
        self.select_oss_vendor(kwargs.get('vendor_name'))
        self._admin_console.wait_for_completion()
        backup_method_id = self.backup_method_map[kwargs.get('backup_method')]
        self.__select_backup_method(backup_method_id=backup_method_id)
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        self.__select_authentication(auth_type)
        self._select_region(kwargs.get('region_human_readable'))
        backup_gateway = None
        if kwargs.get('backup_method') == 'Gateway':
            backup_gateway = self.__create_backup_gateway(**kwargs)
            self._select_backup_gateway(backup_gateway)
        self.__create_byos_s3(byos_storage_name, auth_type, byos_bucket_name, standard=True)
        self._create_mrr_storage(**kwargs)
        self._create_plan(kwargs.get('plan_name'))
        self.__create_s3_client(client_name, auth_type)
        self.select_content(kwargs.get('content'))
        self.wizard.click_button('Finish')
        self._admin_console.wait_for_completion()
        return backup_gateway

    def s3_cleanup(self, stack_name):
        """cleans up the resources created during testcase execution
            Args:
                stack_name(str)  -- name of the backup gateway stack
        """
        self.s3_helper.delete_stack(stack_name)
