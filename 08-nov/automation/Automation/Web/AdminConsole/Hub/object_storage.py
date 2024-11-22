from selenium.webdriver.common.by import By
import time
import boto3
from Web.Common.page_object import WebAction, PageService
from urllib.parse import urlparse, parse_qs
from AutomationUtils import config


class ObjectStorage:
    def __init__(self, admin_console, service_type):
        self.__admin_console = admin_console
        self.__driver = self.__admin_console.driver
        self.log = self.__admin_console.log
        self.service_type = service_type
        self.aws_connection = None
        self.config = config.get_config()
        self.cloud_formation_obj = None
        self.role_arn = self.config.aws_access_creds.tenant_role_arn

    @WebAction()
    def __click_next_button(self):
        """Clicks on Next Button"""
        self.__admin_console.click_button_using_text("Next")

    @WebAction()
    def __click_select_service_drop_down(self):
        """Clicks on Select Service DropDown"""
        select_service_xpath = f"//div[contains(text(),'Select a service type')]"
        self.__admin_console.click_by_xpath(select_service_xpath)

    @WebAction()
    def __select_service_type(self):
        """Selects Service Type"""
        service_type_xpath = f"//span[contains(@class, 'deselect-option') and contains(text(), '{self.service_type}')]"
        self.__admin_console.click_by_xpath(service_type_xpath)

    @WebAction()
    def __fill_client_name(self, client_name):
        """Fills Client Name in the form"""
        self.__admin_console.fill_form_by_id('clientName', client_name)

    @WebAction()
    def __fill_storage_name(self, storage_name):
        """Fills Storage Name in the form for s3 client"""
        self.__admin_console.fill_form_by_id('storageName', storage_name)

    @WebAction()
    def __fill_account_name(self, account_name):
        """Fills Account Name"""
        self.__admin_console.fill_form_by_id('userName', account_name)

    @WebAction()
    def __fill_account_key(self, account_key):
        """Fills Account Key"""
        self.__admin_console.fill_form_by_id('password', account_key)

    @WebAction()
    def __fill_access_key(self, access_key):
        """Fills Access key"""
        self.__admin_console.fill_form_by_id('accessKey', access_key)

    @WebAction()
    def __fill_secret_key(self, secret_key):
        """Fills Secret Key"""
        self.__admin_console.fill_form_by_id('secretKey', secret_key)

    @WebAction()
    def __fill_role_arn(self, role_arn):
        """Fills Role Arn"""
        self.__admin_console.fill_form_by_id('roleArn', role_arn)

    @WebAction()
    def __click_create_button(self):
        """Clicks on Create Button"""
        self.__admin_console.click_button_using_text("Create")

    @WebAction()
    def __click_existing_storage_location_option(self):
        """Clicks on Existing Storage Location Option"""
        self.__admin_console.click_by_xpath(
            f"//p[contains(text(),'Select an existing cloud storage location')]")

    @WebAction()
    def __click_new_storage_location_option(self):
        """Clicks on Existing Storage Location Option"""
        self.__admin_console.click_by_xpath(
            f"//p[contains(text(),'Configure a new cloud storage location')]")

    @WebAction()
    def __click_select_cloud_location_drop_down(self):
        """Clicks on Select Cloud Location Dropdown"""
        self.__admin_console.click_by_xpath(
            f"//div[contains(@class, 'placeholder') and contains(text(),'Select a cloud location')]")

    @WebAction()
    def __select_authentication_method(self, auth_type):
        """Selects Authentication method"""
        self.__admin_console.click_by_xpath("//div[contains(text(),'authentication')]")
        self.__admin_console.click_by_xpath(f"//li/span[contains(text(),'{auth_type}')]")

    @WebAction()
    def __select_new_or_old_gateway(self, gtype):
        """chooses existing or new backup gateway"""
        if gtype != 'existing':
            self.__admin_console.click_by_xpath(f"//label/p[contains(text(),'{gtype} backup gateway')]")

    @WebAction()
    def __select_gateway(self, ip):
        """selects an existing hostname"""
        self.__admin_console.click_by_xpath("//div[contains(text(),'existing backup gateway')]")
        self.__admin_console.click_by_xpath(f"//span[contains(text(),'{ip}')]")

    @WebAction()
    def __click_select_region_drop_down(self):
        """Clicks on Select Cloud Location Dropdown"""
        self.__admin_console.click_by_xpath(
            f"//div[contains(@class, 'placeholder') and contains(text(),'Select a region')]")

    @WebAction()
    def __click_select_storage_region_drop_down(self):
        """Clicks on Select Cloud Location Dropdown"""
        self.__admin_console.click_by_xpath(
            f"//div[contains(text(),'Select a storage region')]")

    @WebAction()
    def __select_region(self, region):
        """selects region for gateway
            Args:
                region(str)-- the region for backup gateway.
        """
        self.__click_select_region_drop_down()
        time.sleep(2)
        self.__admin_console.click_by_xpath(f"//span[contains(text(),'{region}')]")

    @WebAction()
    def __select_storage_region(self, region):
        """selects region for storage
            Args:
                region(str)-- the region of the storage.
        """
        self.__click_select_storage_region_drop_down()
        time.sleep(2)
        self.__admin_console.click_by_xpath(f"//span[contains(text(),'{region}')]")

    @WebAction()
    def __click_select_platform(self):
        """clicks platform dropdown"""
        self.__admin_console.click_by_xpath("//div[contains(text(),'Select a platform')]")

    @WebAction()
    def __select_platform(self, platform):
        """selects platform
            Args:
                platform(str)--selects a windows or linux machine for gateway.
        """
        self.__click_select_platform()
        self.__admin_console.click_by_xpath(f"//li/span[contains(text(),'{platform}')]")

    @WebAction()
    def __click_generate_link(self):
        """clicks on generate link button"""
        self.__admin_console.click_button_using_text("Generate link")

    @WebAction()
    def __click_refresh_list(self):
        """clicks on the refresh_list button for new backup gateway ip"""
        self.__admin_console.click_button_using_text('Refresh list')

    @WebAction()
    def __select_from_bkp_gw_list(self,ip):
        """selects the new backup gateway from the list"""
        self.__admin_console.click_by_xpath("//div[contains(text(),'Select a backup gateway')]")
        self.__admin_console.click_by_xpath(f"//span[contains(text(),{ip})]")

    @WebAction()
    def __click_save(self):
        """clicks on Submit button"""
        self.__admin_console.click_button_using_text('Save')

    @WebAction()
    def __click_add_storage(self):
        """creating new storage location for s3"""
        self.__admin_console.click_button_using_text('Add new storage location')

    @WebAction()
    def __fill_storage_name_loc(self, store_name):
        """fills storage name
             Args:
                 store_name(str)-- name of the storage account.
        """
        self.__admin_console.fill_form_by_id("storageLocationName", store_name)

    @WebAction()
    def __fill_bucket_name(self, bucket):
        """fills bucket name of backup
            Args:
                bucket(str) - bucket which stores the backup data.
        """
        self.__admin_console.fill_form_by_id("bucketName", bucket)

    @WebAction()
    def __fill_access_key_loc(self, access_key):
        """fills keys for storage location
            Args:
                access_key(str)--access key of the s3 account(which stores the backup data).
        """
        self.__admin_console.fill_form_by_id("userName", access_key)

    @WebAction()
    def __fill_secret_key_loc(self, secret_key):
        """fills keys for storage loc
            Args:
                secret_key(str)--secret key of the s3 account(which stores the backup data).
        """
        self.__admin_console.fill_form_by_id("password", secret_key)

    @WebAction()
    def __fill_role_arn_loc(self, roleArn):
        """fills keys for storage loc
            Args:
                roleArn(str)-- Role Arn for accessing s3 bucket.
        """
        self.__admin_console.fill_form_by_id("stpCreds", roleArn)

    @WebAction()
    def __select_cloud_storage_location(self, cloud_storage_loc):
        """Selects Cloud Storage Location

            Args:
                cloud_storage_loc (str)  --  Cloud Storage Location
        """
        self.__admin_console.click_by_xpath(
            f"//span[contains(text(),'{cloud_storage_loc}')]")

    @WebAction()
    def __click_select_account_holder_drop_down(self):
        """Clicks on Select Cloud Location Dropdown"""
        self.__admin_console.click_by_xpath(
            f"//div[contains(@class, 'placeholder') and contains(text(),'Select the storage account holder')]")

    @WebAction()
    def __select_storage_account_holder(self):
        """Selects Cloud Storage Location"""
        self.__admin_console.click_by_xpath(
            f"//span[contains(@class, 'deselect-option') and contains(text(),'Metallic')]")

    @WebAction()
    def __click_existing_plan_option(self):
        """Clicks on Existing Plan Option"""
        self.__admin_console.click_by_xpath(
            f"//p[contains(text(),'Use an existing plan')]")

    @WebAction()
    def __click_new_plan_option(self):
        """Clicks on New Plan Option"""
        self.__admin_console.click_by_xpath(
            f"//p[contains(text(),'Create a new plan')]")

    @WebAction()
    def __select_one_month_retention_plan(self):
        """Selects one month retention plan"""
        self.__admin_console.click_by_xpath(
            f"//p[contains(text(),'1 Month Retention Plan')]"
        )

    @WebAction()
    def __fill_new_plan_name(self, plan_name):
        """Fills New Plan Name

            Args:
                plan_name   (str)    --  New Plan Name
        """
        self.__admin_console.fill_form_by_id('planName', plan_name)

    @WebAction()
    def __select_existing_plan(self, plan):
        """Selects Existing Plan

                    Args:
                        plan (str)  --  Existing Plan Name
        """
        self.__admin_console.click_by_xpath(
            f"//p[contains(text(),'{plan}')]")

    @WebAction()
    def __click_backup_button(self):
        """Clicks on Backup Now Button"""
        self.__admin_console.click_by_xpath(
            f"//button[contains(@class, 'btn-secondary') and contains(text(),'Back up now')]")

    @WebAction()
    def __click_view_progress(self):
        """Clicks on View Progress link"""
        self.__admin_console.click_by_xpath("//a[contains(text(),'View the progress')]")

    @WebAction()
    def __click_on_bucket_for_selection(self, bucket):
        """clicks on the buckets for backup"""
        self.__admin_console.click_by_xpath(f"//li/div/span[contains(text(),'{bucket}')]")

    @WebAction()
    def __get_cloudformation_stack_url_for_role(self):
        """gets the backup gateway cloudformation url"""
        path = "//a[contains(text(),'Launch CloudFormation Stack')]"
        return self.__driver.find_element(By.XPATH, path).get_attribute('href')

    @WebAction()
    def __confirm_iam_user_group_created(self):
        """confirms the iam user group is created for access key and secret key authentication"""
        self.__admin_console.click_by_xpath("//label[contains(text(),'I confirm that the IAM User Group called ')]")

    @WebAction()
    def __confirm_iam_role_created(self):
        """confirms the iam role is created for I AM Role or STS assume role authentication"""
        self.__admin_console.click_by_xpath("//label[contains(text(),'I confirm that the IAM Role called ')]")

    @WebAction()
    def __get_cloudformation_stack_url_for_backup_gateway(self):
        """gets the backup gateway cloudformation url"""
        path = "//a/span[contains(text(),'Launch CloudFormation Template')]/parent::*"
        return self.__driver.find_element(By.XPATH, path).get_attribute('href')

    @WebAction()
    def __enable_backup_acls(self):
        """checks the checkbox of Backup ACL"""
        self.__admin_console.click_by_xpath("//div[contains(text(),'Back up ACL')]")

    @PageService()
    def __wait_for_role_stack_template(self, wait_time=150):
        """Waits for launch cloudformation stack link to appear"""
        curr_time = 0
        path = "//a[contains(text(),'Launch CloudFormation Stack')]"
        while not self.__admin_console.check_if_entity_exists("xpath", path) and curr_time < wait_time:
            time.sleep(3)
            self.__admin_console.log.info(f"waiting for Launch Stack URL.")
            curr_time += 3
        if curr_time >= wait_time:
            raise TimeoutError("Took more than expected time for loading launch cloud formation url")

    @PageService()
    def __wait_for_backup_gateway_template(self, wait_time=150):
        """Waits for launch cloudformation stack link to appear"""
        curr_time = 0
        path = "//a/span[contains(text(),'Launch CloudFormation Template')]"
        while not self.__admin_console.check_if_entity_exists("xpath", path) and curr_time < wait_time:
            time.sleep(3)
            self.__admin_console.log.info(f"waiting for Launch Stack URL.")
            curr_time += 3
        if curr_time >= wait_time:
            raise TimeoutError("Took more than expected time for loading launch cloud formation url")

    @PageService()
    def __wait_for_s3_content_configuration(self, wait_time=150):
        """Waits for content group to get configured"""
        curr_time = 0
        path = "//div[contains(text(),'Successfully configured the content group')]"
        while not self.__admin_console.check_if_entity_exists("xpath", path) and curr_time < wait_time:
            time.sleep(3)
            self.__admin_console.log.info("waiting for content group to get configured")
            curr_time += 3
        if curr_time >= wait_time:
            raise TimeoutError("Took more than expected time for configuring content group")

    @PageService()
    def __wait_for_plan_asocc(self, wait_time=150):
        """waits until plan gets associated with object storage client"""
        curr_time = 0
        text = "Please wait while we associate the object storage client to the plan"
        xpath = f"//small[contains(text(),{text})]"
        while self.__admin_console.check_if_entity_exists("xpath", xpath) and curr_time < wait_time:
            time.sleep(7)
            self.log.info("Waiting for plan to get associated with the client")
            curr_time += 7
        if curr_time >= wait_time:
            raise TimeoutError("Took more than expected time for associating plan with client")

    @PageService()
    def __wait_for_storage_configuration(self, wait_time=150):
        """Waits for Metallic Storage to be configured for Azure Blob and FileShare client.
        """
        curr_time = 0
        text_xpath = f"//small[contains(text(),'Successfully configured the Metallic storage')]"
        while not self.__admin_console.check_if_entity_exists("xpath", text_xpath) and curr_time < wait_time:
            time.sleep(10)
            self.__admin_console.log.info(f"Waiting for Metallic Storage to be configured.")
            curr_time += 10
        if curr_time >= wait_time:
            raise TimeoutError("Took more than expected time for configuring storage")
        self.__admin_console.log.info(f"Metallic Storage is now configured.")

    @PageService()
    def __wait_for_storage_configuration_of_s3(self, wait_time=150):
        """Waits for Metallic Storage to be configured for S3 client.
        """
        curr_time = 0
        text_xpath = f"//div[contains(text(),'We successfully configured the storage')]"
        while not self.__admin_console.check_if_entity_exists("xpath", text_xpath) and curr_time < wait_time:
            time.sleep(10)
            curr_time += 10
            self.__admin_console.log.info(f"Waiting for Metallic Storage to be configured.")
        if curr_time >= wait_time:
            raise TimeoutError("Took more than expected time for configuring storage")
        self.__admin_console.log.info(f"Metallic Storage is now configured.")

    @PageService()
    def __wait_for_bkp_gw_list(self, ip, wait_time=150):
        """Waits until backup gateway list loads"""
        curr_time = 0
        text_xpath = f"//div[contains(text(),{ip})]"
        while not self.__admin_console.check_if_entity_exists("xpath", text_xpath) and curr_time < wait_time:
            time.sleep(10)
            self.__admin_console.log.info("waiting for backup gateway list to load.")
            curr_time += 10
        if curr_time >= wait_time:
            raise TimeoutError("Took more than expected time for loading backup gateways list")
        self.__admin_console.log.info("successfully loaded.")

    @PageService()
    def __wait_to_submit(self, ip, wait_time=150):
        """Waits until the backup gateway gets configured with the company.
        """
        curr_time = 0
        text_xpath = f"//div/span[contains(text(),{ip})]"
        while not self.__admin_console.check_if_entity_exists("xpath", text_xpath) and curr_time < wait_time:
            time.sleep(10)
            self.__admin_console.log.info(f"waiting for save to finish.")
            curr_time += 10
        if curr_time >= wait_time:
            raise TimeoutError("Took more than expected time for configuring backup gateway with the company")
        self.__admin_console.log.info(f"successfully configured.")

    @PageService()
    def configure_permissions(self, auth_type):
        """Configures the S3 permission page
            Args:
                auth_type(str)- Authentication mode to configure AWS gateway.
        """
        self.__select_authentication_method(auth_type)
        if auth_type == "Access and Secret Key":
            self.role_stack_creation('MetallicUserGroup')
            self.__confirm_iam_user_group_created()
        elif auth_type == "IAM Role":
            self.role_stack_creation('MetallicRole')
            self.__confirm_iam_role_created()
        elif auth_type == "STS assume role with IAM policy":
            self.role_stack_creation("MetallicAdminRole", self.config.aws_access_creds.tenant_metallic_role_region)
            self.__confirm_iam_role_created()
        self.__click_next_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_backup_gateway(self, backup_gateway_region, region, platform, stack_name=None, params=None):
        """configures the backup gateway page
            Args:
                backup_gateway_region(str) - the region name of the backup gateway in metallic page.
                                                (Eg-Ohio,N. Virginia,...etc)

                region(str) -       the region code of the backup gateway.(Eg-us-east-2,us-east-1,...etc)

                platform(str) -     windows or linux instance that need to be created.

                stack_name(str) -   Name of the cloud formation stack.

                params(list) -      List of parameters need to for stack creation.
        """
        self.__select_region(backup_gateway_region)
        self.__select_platform(platform)
        self.__click_generate_link()
        self.__wait_for_backup_gateway_template()
        ip = self.backup_gateway_stack_creation(stack_name, params, region)
        time.sleep(180)
        self.__click_refresh_list()
        self.__wait_for_bkp_gw_list(ip)
        self.__click_save()
        self.__wait_to_submit(ip)
        time.sleep(60)
        self.__click_next_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_content(self, buckets):
        """selecting contents need to be backed up
            Args:
                buckets(list) - list of buckets that need to be backed up.
        """
        for bucket in buckets:
            self.__click_on_bucket_for_selection(bucket)
        self.__enable_backup_acls()
        self.__admin_console.click_button_using_text("Add content")
        self.__wait_for_s3_content_configuration()
        self.__click_next_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def selecting_storage_loc(self, auth_type, store_name, bucket_name, access_key=None, secret_key=None):
        """selects the new storage loc
            Args:
                auth_type(str) --   Authentication type for storage configuration.
                store_name(str) --  Name of the cloud storage.
                bucket_name(str)--  Bucket name to store the backup data.
                access_key(str)--   access key of the s3 account.
                secret_key(str)--   secret key of the s3 account.
        """
        self.__click_add_storage()
        self.__fill_storage_name_loc(store_name)
        self.__fill_bucket_name(bucket_name)
        if auth_type == "Access and Secret Key":
            self.__fill_access_key_loc(access_key)
            self.__fill_secret_key_loc(secret_key)
        if auth_type == "STS assume role with IAM policy":
            self.__fill_role_arn_loc(self.role_arn)
        self.__click_create_button()
        self.__wait_for_storage_configuration_of_s3()
        self.log.info("added new storage location")
        self.__click_next_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_service(self):
        """Selects Object Storage Service Type"""
        self.__click_select_service_drop_down()
        self.__select_service_type()
        self.__click_next_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def create_storage_account(self, client_name, account_name, account_key):
        """Creates a Storage Account with given Name and Credentials

            Args:
                client_name (str)    --  Name of the Storage Account
                account_name    (str)    --  Name of the Azure Account
                account_key (str)    --  Azure Account key
        """
        self.__fill_client_name(client_name)
        self.__fill_account_name(account_name)
        self.__fill_account_key(account_key)
        self.__click_create_button()
        self.__admin_console.wait_for_completion()
        self.__click_next_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def create_s3_storage_account(self, client_name, auth_type, account_name=None, account_key=None):
        """Creates a Storage Account with given Name and Credentials

            Args:
                client_name (str)    --  Name of the Storage Account
                auth_type (str) --              Authentication method for the oss client
                account_name    (str)    --  Name of the Azure Account
                account_key (str)    --  Azure Account key
        """
        self.__fill_storage_name(client_name)
        self.__select_authentication_method(auth_type)
        if auth_type == "Access and Secret Key":
            self.__fill_access_key(account_name)
            self.__fill_secret_key(account_key)
        if auth_type == "STS assume role with IAM policy":
            self.__fill_role_arn(self.role_arn)
        self.__click_create_button()
        self.__admin_console.wait_for_completion()
        self.__click_next_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def configure_new_cloud_storage(self, cloud_storage_loc):
        """Configures a New Cloud Storage

            Args:
                cloud_storage_loc   (str)    --  New Cloud Storage Location
        """

        self.__click_select_account_holder_drop_down()
        self.__select_storage_account_holder()
        self.__click_create_button()
        self.__wait_for_storage_configuration()
        self.__click_next_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def configure_new_plan(self, plan):
        """Configures a New Plan

            Args:
                plan    (str)    --  New Plan Name
        """
        self.__click_new_plan_option()
        self.__select_one_month_retention_plan()
        self.__fill_new_plan_name(plan)
        self.__click_create_button()
        self.__admin_console.wait_for_completion()
        self.__click_next_button()
        self.__wait_for_plan_asocc()
        self.__admin_console.wait_for_completion()

    @PageService()
    def configure_existing_cloud_storage(self, cloud_storage_loc):
        """Configures an Existing Cloud Storage

            Args:
                cloud_storage_loc   (str)    --  Existing Cloud Storage Location
        """
        self.__click_existing_storage_location_option()
        self.__click_select_cloud_location_drop_down()
        self.__select_cloud_storage_location(cloud_storage_loc)
        self.__click_next_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def configure_existing_plan(self, plan):
        """Configures an Existing Plan

            Args:
                plan    (str)    --  Existing Plan Name
        """
        self.__click_existing_plan_option()
        self.__select_existing_plan(plan)
        self.__click_next_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def run_backup(self):
        """Runs Backup"""
        self.__click_backup_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def view_progress(self):
        """View Backup job's progress"""
        self.__click_view_progress()

    def aws_session(self, region):
        """Create a session with aws account.
            Args:
                region(str) --   Region for the aws boto3 session.
        """

        try:
            self.aws_connection = boto3.Session(region_name=region)
            self.cloud_formation_obj = self.aws_connection.client(
                'cloudformation', region_name=region,
                aws_access_key_id=self.config.aws_access_creds.access_key,
                aws_secret_access_key=self.config.aws_access_creds.secret_key)
            self.log.info("Connection successful for AWS")
        except Exception as err:
            self.log.exception("Unexpected error: %s" % err)
            raise err

    def backup_gateway_stack_creation(self, stackName, params, region):
        """creates a cloud formation stack
                Args:
                    stackName(str)--Name of the cloud formation stack.
                    params(list)-- Parameters to create stack.
                    region(str)-- Region in which stack need to be created.

                Returns:
                    string -- returns ip of the backup gateway.
        """
        stack_url = self.__get_cloudformation_stack_url_for_backup_gateway()
        stack_params = parse_qs(urlparse(stack_url).fragment)
        template_url = stack_params['/stacks/quickcreate?templateURL'][0]
        authcode = stack_params["param_AuthCode"][0]
        params.append({"ParameterKey": "AuthCode", "ParameterValue": authcode})
        backup_gateway_package = stack_params["param_BackupGatewayPackage"][0]
        params.append({"ParameterKey": "BackupGatewayPackage",
                       "ParameterValue": backup_gateway_package})
        auth_type = stack_params["param_Authentication"][0]
        params.append({"ParameterKey": "Authentication",
                       "ParameterValue": auth_type})
        self.aws_session(region)
        try:
            self.cloud_formation_obj.create_stack(StackName=stackName,
                                                  TemplateURL=template_url, Parameters=params)
            self.wait_for_stack_creation(stackName)
        except self.cloud_formation_obj.exceptions.AlreadyExistsException:
            self.delete_stack(stackName)
            self.backup_gateway_stack_creation(stackName, params, region)
            self.log.info("ec2 instance already exists. Please delete the existing stack or provide other stack name")
        except Exception as exp:
            self.log.exception(exp)
            raise Exception
        return self.get_stack_output(stackName, region, self.config.aws_access_creds.access_key,
                                     self.config.aws_access_creds.secret_key)

    def role_stack_creation(self, stackName, region='us-east-1'):
        """creates the cloud formation stack
                Args:
                    stackName(str)--Name of the cloud formation stack.
                    region(str)--   region in which stack need to be created

                Returns:
                    string -- role arn of the cloud formation stack
        """
        self.__wait_for_role_stack_template()
        stack_url = self.__get_cloudformation_stack_url_for_role()
        stack_params = parse_qs(urlparse(stack_url).fragment)
        template_url = stack_params['/stacks/quickcreate?templateURL'][0]
        self.aws_session(region)
        try:
            self.cloud_formation_obj.create_stack(StackName=stackName,
                                                  TemplateURL=template_url,
                                                  Capabilities=['CAPABILITY_NAMED_IAM'])
            self.wait_for_stack_creation(stackName)
        except self.cloud_formation_obj.exceptions.AlreadyExistsException:
            self.log.info(f'Stack already exist. Using this existing stack {stackName}')
            pass
        except Exception as exp:
            self.log.exception(exp)
            raise Exception
        return self.get_stack_output(stackName, region, self.config.aws_access_creds.access_key,
                                     self.config.aws_access_creds.secret_key)

    def delete_stack(self, stackName):
        """deletes the cloud formation stack
            Args:
                stackName(str)-Name of the cloud formation stack.
        """
        self.cloud_formation_obj.delete_stack(StackName=stackName)
        self.log.info("stack delete started")
        self.wait_for_stack_deletion(stackName)
        self.log.info(f"{stackName} deleted successfully")

    def wait_for_stack_creation(self, stack_name):
        """Waits for stack to get created
            Args:
                stack_name(str) -- Name of the cloud formation stack.
        """
        waiter = self.cloud_formation_obj.get_waiter('stack_create_complete')
        self.log.info("waiting for stack to get created")
        waiter.wait(StackName=stack_name)

    def wait_for_stack_deletion(self, stack_name):
        """Waits for stack to get deleted
            Args:
                stack_name(str)-Name of the cloud formation stack.
        """
        waiter = self.cloud_formation_obj.get_waiter('stack_delete_complete')
        self.log.info("waiting for stack to get deleted")
        waiter.wait(StackName=stack_name)

    @staticmethod
    def get_stack_output(stackName, region, access_key, secret_key):
        """Gets the stack output value
           Args:
               stackName(str)-- Name of the cloud formation stack.
               region(str)--    Region in which cloud formation stack exist.
               access_key(str)--access key to the s3 account
               secret_key(str)--secret key to the s3 account

            Returns:
                string -- output of the cloud formation stack
        """

        resources = boto3.resource('cloudformation',
                                   region_name=region,
                                   aws_access_key_id=access_key,
                                   aws_secret_access_key=secret_key)
        stack = resources.Stack(stackName)
        output = stack.outputs[0]['OutputValue']
        return output
