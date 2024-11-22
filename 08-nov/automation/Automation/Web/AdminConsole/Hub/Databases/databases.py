from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""
This module provides all the helper functions needed to configure databases from Metallic Hub

DatabasesMetallic is the only class defined in this file.

Classes:
    DatabasesMetallic   --  Provides the helper function needed to complete DB configuration

    Functions:

        __init__                            --          Constructor for the class

        do_pkg_download                     --          Downloads Metallic Package

        do_pkg_install                      --          Installs Metallic Package on client

        redirect_to_admin_console           --          Redirects to Admin Console from Hub

        select_backup_deploy                --          Selects the type of backup deploy

        select_database_environment         --          Selects the database environment

        select_trial_subscription           --          Clicks on Start trial subscription dialog

        configure_application_access        --           Downloads and installs the Metallic
                                                         software on the server and checks valid
                                                         installation

        select_existing _cloud_storage      --          To select existing cloud storage location

        select_configure_new_cloud_storage  --          To select configure a new cloud storage
                                                        location

        select_existing_plan                --          To select an existing plan

        select_create_new_plan              --          To select create new plan

        configure_databases                 --          Main helper function to configure the
                                                        database

    SAPHanaMetallic   --  Provides the helper function needed to complete SAP HANA DB configuration

        add_instance()                      --          Method to add salesforce app

        configure_application_access()      --          Downloads and installs the Metallic software
        on the server and checks valid installation

    OracleMetallic     --  Provides the helper function needed to complete Oracle DB configuration

        configure_application_access()      --          Downloads and installs the Metallic software
        on the server and checks valid installation

        select_backup_content()      --          Selects content to backup for new Oracle Metallic Configuration

        proceed_from_summary_page()         --          proceed from summary page after Oracle Database Configuration

        configure_oracle_database           --          Configures oracle database

    OCIMetallic             --  Provides the helper function needed to complete OCI DB configuration

        configure()                         --          Configures OCI DBCS from metallic hub

        create_credential()                 --          Creates the credential for the oci

        configure_oci_storage()             --          Creates a new oci cloud storage

        configure_oci_storage_plan()        --          Creates oci cloud storage and plan

        oci_select_region()                 --          Selects the region for the oci

        create_oci_iam_role()               --          Creates IAM role

        add_backup_gateway()                --          Creates stack and adds gateway

    RDatabasesMetallic      --  Provides helper function for configuring database from Command center Pages

        __init__                    --      Constructor for the class
        
        create_tenant               --      Creates a tenant with the given name
        
        click_looped_submit         --      Clicks on the submit button in a loop if error message is present

        select_trial_subscription   --      Clicks on Start trial subscription dialog

        select_database             --      selects the database to be configured
        
        select_backup_method        --      select the backup method
        
        _create_azure_app_credentials   --  Method to create Azure App credential
        
        _create_azure_storage_credentials --  Method to create Azure storage credential
        
        _create_azure_mrr_storage   --      Method to create MRR storage account
        
        _create_microsoft_azure_storage --  Method to create Microsoft Azure cloud storage
        
        _create_azure_storage       --      Method to create Azure cloud storage

        continue_trial_subscription --     Method to click on continue trial subscription option

        select_backup_deploy        --     Selects backup via cloud or access node

        select_vm_type              --     Selects cloud or on premise vm

        select_cloud_vm_details     --     Selects cloud vm details
        
        close_info_dialog           --     Method to close the information dialog

        select_on_prem_details      --     Selects on prem machine details

        create_new_plan             --     Creates a new plan

        do_rpk_install              --     Installs package on client

        select_cloud_storage        --     Selects relevant cloud storage for backup

        do_rpkg_download            --     Download package to machine

        upgrade_client_software     --     This will upgrade the software of the server or client
        
        wait_for_job_completion     --     Waits for completion of job and gets the object once job completes


    CloudDatabases     --   Class to set common options while creating cloud DB instances with
    react metallic pages

        select_database()                   --          selects the database to be configured

        select_backup_gateway()             --          selects backup gateway from drop down

        click_generate_link()               --          click on button to generate stack creation link

        get_backup_gateway_stack_url()     --          Fetches gateway stack creation URL

        create_aws_backup_gateway()        --          Creates backup gateway in AWS

        click_add_server()                  --          This will Click on Add servers from db_instance page and
                                                        select database
        
        _copy_ssl_file_to_access_node()     --          Copies ssl_ca file from azure blob to remote machine    


    RAWSMetallic        --  Class for AWS helper in metallic page

        _get_iam_stack_url()               --          Fetch iam stack role url

        _confirm_iam_stack_url()           --          Checks the iam stack check box
        
        __select_backup_method()            --          Method to select hosted or Gateway

        create_gateway()                    --          creates the backup gateway in metallic page

        _create_secondary_storage()         --          This will create the secondary storage during configuration

        configure()                         --          This configures the instance of AWS cloud DB's

        _select_authentication()           --          selects the authentication methods

        _create_byos_s3()                  --          add the storage in metallic page

        _create_cloud_account()               --          Creates the cloud account for AWS

        _select_cloud_account()               --          Selects the cloud account for AWS

        select_backup_content()             --             Selects the backup content during configuration 

    RAWSOracleMetallic   -- Class to create Oracle on AWS EC2 machine in metallic page

        cloud_db_engine()                   --          returns type of db

        create_in_bound_rule()              --          add gateway ip to EC2 oracle client inbound rules

        create_install_inputs()             --          make required inputs into the format for Oracle interactive
                                                        install
        create_gateway()                    --          Creates backup gateway

        configure()                         --          Creates AWS EC2 oracle instance

    RAWSDynamoDB()  --  Class to create AWS Dynamo DB in Metallic Page

        cloud_db_engine                     --          returns type of db 

    RAWSDocumentDB()    --  Class to create AWS Document DB instance in metallic page

        cloud_db_engine                     --          returns type of db 

    RAWSRedshift()   --  Class to create AWS Redshift DB in Metallic page

        cloud_db_engine                     --          returns type of db 

    RAWSRDS()   --  Class to create AWS RDS DB in Metallic page

        cloud_db_engine                     --          returns type of db
    
    AWSRDSExport()  --  Class to create AWS RDS Export in Metallic page

        cloud_db_engine                     --          returns type of db engine

        database_type                       --          returns type of db server
        
    RAzureDatabases()       --  Class for creating Microsoft Azure Database instances in Metallic page
     
        configure                         --          Creates Microsoft Azure Database instance

    RAzurePostgreSQLInstance()  --  Class for creating Microsoft Azure PostgreSQL in Metallic page

    RAzureMySQLInstance()       --  Class for creating Microsoft Azure MySQL in Metallic page

    RAzureMariaDBInstance()  --  Class for creating Microsoft Azure MariaDB in Metallic page

    RMSSQLMetallic()         --  Class for creating Microsoft SQL Server Instance in Metallic

        __init__                    --   Constructor for the class

        impersonate_user_sql        --   Impersonates user with sysadmin access with Credential Manager UI

        configure_sql_db            --   Configures and sets up SQL database from Metallic Hub

    RAzureSQLServerInstance()   --  Class for creating Microsoft Azure SQL in Metallic page

        _configure_instance()   --  Method to configure the Azure SQL instance details

        _create_credentials()   --  Method to create SQL Server credentials

        configure()             --  Method to create a Microsoft Azure SQL Server instance

"""
import time
import requests
import base64
import urllib.parse
from abc import abstractmethod
from time import sleep
from datetime import datetime, timedelta
from selenium.common.exceptions import NoSuchElementException
from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.constants import TEMP_DIR
from AutomationUtils.machine import Machine
from Install.install_custom_package import InstallCustomPackage
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Hub.constants import HubServices, DatabaseTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.utils import Utils
from Web.Common.page_object import PageService, WebAction
from Web.Common.exceptions import CVWebAutomationException, CVTestStepFailure
from Web.AdminConsole.Components.wizard import Wizard
from Application.CloudApps.azure_helper import AzureResourceGroup, AzureCustomDeployment
from Web.AdminConsole.Components.panel import RDropDown
from Application.CloudApps.oci_helper import OCIHelper
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.browse import RContentBrowse
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Metallic.hubutils import HubManagement

_CONFIG_DATA = get_config()


class DatabasesMetallic:
    """Provides helepr function for configuring database from Hub"""

    def __init__(self, adminconsole, app_type):
        """Constructor function for this class
        Args :
            adminconsole (obj:'AdminConsole')   : Object of AdminConsole class
            app_type (str)                      : Specify the database type. Should be from
                                                  Web.Adminconsole.Hub.constants DatabaseTypes class
        """
        self.service = HubServices.database
        self.app_type = app_type
        self.utils_helper = Utils(adminconsole)
        self.controller_obj = Machine()
        self._adminconsole = adminconsole
        self._driver = adminconsole.driver
        self._LOG = logger.get_log()
        self.hub_dashboard = None

    def __is_entity_exist_and_displayed(self, xpath):
        if self._adminconsole.check_if_entity_exists("xpath", xpath):
            return self._driver.find_element(By.XPATH, xpath).is_displayed()
        return False

    @WebAction()
    def __get_text_info_after_spinner(self):
        """Gets the text message that comes up after spinner element has completed"""
        success_xpath = "//small[@class = \"text-info ng-star-inserted\"]"
        success_xpath_hana = "//small[@class = \"text-info\"]"
        success_plan = "//small[contains(text(),\"We successfully created the plan\")]"
        fail_xpath1 = "//small[@class=\"text-danger\"]"
        fail_xpath2 = "//small[@class=\"text-danger error-msg\"]"

        if self.__is_entity_exist_and_displayed(success_xpath):
            success_text_box = self._driver.find_element(By.XPATH, success_xpath)
            self._LOG.info(success_text_box.text)
            return True, success_text_box.text
        elif self.__is_entity_exist_and_displayed(success_xpath_hana):
            success_text_box = self._driver.find_element(By.XPATH, success_xpath_hana)
            self._LOG.info(success_text_box.text)
            return True, success_text_box.text
        elif self.__is_entity_exist_and_displayed(success_plan):
            success_text_box = self._driver.find_element(By.XPATH, success_plan)
            self._LOG.info(success_text_box.text)
            return True, success_text_box.text
        elif self.__is_entity_exist_and_displayed(fail_xpath1):
            fail_text_box = self._driver.find_element(By.XPATH, fail_xpath1)
            self._LOG.error(fail_text_box.text)
            return False, fail_text_box.text
        elif self.__is_entity_exist_and_displayed(fail_xpath2):
            fail_text_box = self._driver.find_element(By.XPATH, fail_xpath2)
            self._LOG.error(fail_text_box.text)
            return False, fail_text_box.text

    @WebAction()
    def __select_plan_from_list_of_radio(self, plan_name):
        """Selects the given plan from the list of plans shown in 'Select Plan' tab
        Args:
            plan_name       (str)      :        Name of the plan
        """
        plan_xpath = f"//p[contains(text(),\"{plan_name}\")]"
        try:
            self._driver.find_element(By.XPATH, plan_xpath).click()
        except NoSuchElementException:
            raise CVWebAutomationException(f"__select_existing_plan() has raised "
                                           f"'NoSuchElementException'. Please check if the plan "
                                           f"name provided, {plan_name}, exists.")

    @WebAction()
    def __check_successful_configuration(self):
        """Checks whether configuration is a success or not"""
        config_success_xpath = "//h4[contains(text(),\"Initial configuration is complete!\")]"
        if not self._adminconsole.check_if_entity_exists("xpath", config_success_xpath):
            raise CVWebAutomationException("Plan creation/association failed")

    @WebAction()
    def __check_install_complete(self):
        """ method to check the install progress bar status """
        close_button = "//div[contains(@class, 'progress-bar-container')]//mdb-icon[contains(@class,'fas')]"
        count = 30
        found = False
        while count != 0:
            if self._adminconsole.check_if_entity_exists("xpath", close_button):
                found = True
                break
            self._LOG.info("Sleeping for 30 seconds before checking again")
            sleep(60)
            count = count - 1
        if not found:
            raise CVWebAutomationException("Installation is not completed within 30 mins")
        close_button = self._driver.find_element(By.XPATH, close_button)
        install_text = "//div[contains(@class, 'progress-bar-container')]"
        install_text = self._driver.find_element(By.XPATH, install_text).text
        if "100%" in install_text and "successful!" in install_text.lower():
            self._LOG.info("Installation is succesful")
            close_button.click()
            return True
        self._LOG.info("Installation failed")
        self._adminconsole.click_button('Cancel')
        return False

    def do_pkg_download(self, platform="windows"):
        """Helper function to the download of seed package
        Args:
            platform (str)      :   Platform of the client

        Returns:
            pkg_file_path (str) :   File path of the downloaded package
        """
        pkg_file_path = ""
        if self.app_type == DatabaseTypes.sql or self.app_type == DatabaseTypes.sap_hana:
            file_name = "MSSQLServer64.exe"
            if self.app_type == DatabaseTypes.sap_hana:
                file_name = "LinuxSeed64.tar"
            pkg_file_path = self.controller_obj.join_path(TEMP_DIR, file_name)
            if self.controller_obj.check_file_exists(pkg_file_path):
                self.controller_obj.delete_file(pkg_file_path)
            self._adminconsole.select_hyperlink("Download")
        elif self.app_type == DatabaseTypes.oracle:
            file_name = f"{platform}Seed64.tar"
            pkg_file_path = self.controller_obj.join_path(TEMP_DIR, file_name)
            if self.controller_obj.check_file_exists(pkg_file_path):
                self.controller_obj.delete_file(pkg_file_path)
            download_xpath = f"//td[text() = \"{platform}\"]/following-sibling::td/a[text() = \"Download\"]"
            self._adminconsole.click_by_xpath(download_xpath)

        i = 0
        while not self.controller_obj.check_file_exists(pkg_file_path):
            self._LOG.info("Please wait for download to finish")
            sleep(60)
            i += 1
            if i == 10:
                raise CVWebAutomationException("Download failed due to timeout")
        self._LOG.info("Package download completed!!")
        return pkg_file_path

    def do_pkg_install(self, commcell, pkg_file_path, install_inputs):
        """Helper function to do the DB package install
        Args:
            commcell                  : "Commcell object"

            pkg_file_path    (str)    : Seed package file path

            install_inputs   (dict)   : Dictionary input that goes for configuring DB package
                                        install

                                        dictionary passed should be:
                                        {
                                            "remote_clientname"     : "<FQDN of the machine>"
                                            "remote_username"       : "<username to connect to
                                                                        remote machine>",
                                            "remote_userpassword"   : "<password to connect to
                                                                        remote machine>",
                                            "os_type"               :  "<OS type of remote client>"
                                            "username"              : "<Username of CS to
                                                                        authenticate client>"
                                            "password"              : "<Password  of CS
                                                                        authenticate client>"
                                            "authcode" (optional)   : "<Authcode to
                                                                        authenticate client>"
                                        }
        """
        remote_machine_credentials = {
            "remote_clientname": install_inputs.get("remote_clientname"),
            "remote_username": install_inputs.get("remote_username"),
            "remote_userpassword": install_inputs.get("remote_userpassword")
        }
        install_helper = InstallCustomPackage(commcell,
                                              remote_machine_credentials,
                                              install_inputs.get("os_type"))

        if "authcode" in install_inputs.keys():
            install_helper.install_custom_package(pkg_file_path, install_inputs.get("authcode"))
        else:
            install_helper.install_custom_package(pkg_file_path,
                                                  install_inputs.get("username"),
                                                  install_inputs.get("password"))
        self._LOG.info("Install successfully completed!!")
        self.controller_obj.delete_file(pkg_file_path)

    @PageService()
    def __wait_for_cloud_storage_creation(self):
        """Waits for cloud storage creation to complete"""
        success_xpath = "//small[contains(text(),\"Successfully configured the Metallic storage\")]"
        i = 0
        while True:
            if self.__is_entity_exist_and_displayed(success_xpath):
                self._LOG.info("Cloud Storage successfully configured")
                break
            self._LOG.info("Please wait for storage to be configured")
            sleep(30)
            i += 1
            if i == 10:
                raise CVWebAutomationException("Storage configuration failed due to timeout")

    @PageService()
    def redirect_to_admin_console(self):
        """Redirects to Admin Console Page from Metallic Dashboard"""
        self.hub_dashboard.go_to_admin_console()

    @PageService()
    def select_backup_deploy(self, deploy_type='VIA_GATEWAY'):
        """Select the backup deploy option
        Args:
            deploy_type            (str)    :    Can be 'VIA_GATEWAY' or 'DIRECT_TO_CLOUD' depending
                                                 on deployment
                default value      (str)    :   'VIA_GATEWAY'  --> Backup via gateway option in Hub
        """
        if deploy_type == 'VIA_GATEWAY':
            self.utils_helper.select_radio_by_id("onPrem")
        elif deploy_type == 'DIRECT_TO_CLOUD':
            self.utils_helper.select_radio_by_id("cloud")
        else:
            raise CVWebAutomationException("Exception raised in select_backup_deploy(). Wrong "
                                           "deployment method")

    @PageService()
    def select_database_environment(self, environment_type='VIRTUAL_MACHINE'):
        """Selects the database environment
        Args:
            environment_type    (str)    :    Can be 'VIRTUAL_MACHINE' or 'PHYSICAL_SYSTEM' depending
                                                 on environment
                default:    'VIRTUAL_MACHINE'
        """
        if environment_type == 'VIRTUAL_MACHINE':
            self.utils_helper.select_radio_by_id("optVirtualMachine")
        elif environment_type == 'PHYSICAL_SYSTEM':
            self.utils_helper.select_radio_by_id("optPhysicalMachine")
        else:
            raise CVWebAutomationException("Exception raised in select_database_environment(). Wrong "
                                           "environment type method")

    @PageService()
    def select_trial_subscription(self):
        """ Clicks on Start trial subscription dialog
        """
        self.utils_helper.submit_dialog()
        self._adminconsole.wait_for_completion()
        self.utils_helper.submit_dialog()
        self._adminconsole.wait_for_completion()

    @PageService()
    def configure_application_access(self, commcell, install_inputs):
        """Downloads and installs the Metallic software on the server and checks valid installation
        Args:
            Args:

            commcell                  : Commcell object

            install_inputs   (dict)   : Dictionary input that goes for configuring DB package
                                        install

                                        dictionary passed should be:
                                        {
                                            "remote_clientname"     : "<FQDN of the machine>"
                                            "remote_username"       : "<username to connect to
                                                                        remote machine>",
                                            "remote_userpassword"   : "<password to connect to
                                                                        remote machine>",
                                            "os_type"               :  "<OS type of remote client>"
                                            "username"              : "<Username of CS to
                                                                        authenticate client>"
                                            "password"              : "<Password of CS to
                                                                        authenticate client>"
                                            "authcode" (optional)   : "<Authcode to
                                                                        authenticate client>"
                                        }
        """
        pkg_file_path = self.do_pkg_download()
        self.do_pkg_install(commcell, pkg_file_path, install_inputs)

        # Validates Install
        self._adminconsole.fill_form_by_id("hostName", install_inputs.get("remote_clientname"))
        self._adminconsole.click_button_using_text(value="Submit")
        self.utils_helper.wait_for_spinner()
        status, msg = self.__get_text_info_after_spinner()
        if not status:
            raise CVWebAutomationException(f"Failed to validate install with error : {msg}")
        if "existing configuration" in msg:
            self._LOG.info(
                "*" * 10 + " Existing installation found. Proceeding anyway!!  " + "*" * 10)
        else:
            self._LOG.info("*" * 10 + " Install successfully validated " + "*" * 10)

    @PageService()
    def select_cloud_storage(self, storage_account=None, cloud_provider=None, region=None, **kwargs):
        """Selects configure new cloud storage option
        Args:
            storage_account (str) :     Name of the storage account
            cloud_provider  (str) :     Name of the cloud storage provide
            region          (str) :     Name of the storage region

        Keyword Args (Used only when storage account is "Your Account"):
            storage_name    (str) :     New storage location name
            user_name       (str) :     Account Name
            password        (str) :     Access key ID
            container_name  (str) :     Container Name
            secondary_copy  (bool):     If True configures secondary copy on Metallic Cloud on the
                                        storage provided
            secondary_storage(str):     Name of the secondary storage
        """
        self.utils_helper.select_value_from_dropdown(form_control_name="storageAccountType",
                                                     value=storage_account)

        if self._adminconsole.check_if_entity_exists("xpath", "//div[contains(text(),\"You are not subscribed to\")]"):
            self._adminconsole.click_button_using_text(value="Start Trial")
            sleep(20)
            self._adminconsole.click_button_using_text(value="Close")

        try:
            self.utils_helper.select_value_from_dropdown(form_control_name="storageVendorType",
                                                         value=cloud_provider)
        except Exception as e:
            self._LOG.info(
                "*" * 10 + "Exception  : ", e, "Ignoring this now and moving on" + "*" * 10)
        self.utils_helper.select_value_from_dropdown(form_control_name="storageRegion",
                                                     value=region)
        if storage_account.lower() == "your account":
            self._adminconsole.fill_form_by_id("customerLibName", kwargs["storage_name"])
            self._adminconsole.fill_form_by_id("userName", kwargs["user_name"])
            self._adminconsole.fill_form_by_id("password", kwargs["password"])
            self._adminconsole.fill_form_by_id("containerName", kwargs["container_name"])
            if kwargs["secondary_copy"]:
                self.utils_helper.checkbox_select("enableVendorCopy")
                self.utils_helper.select_value_from_dropdown(form_control_name="secondaryCopyRegionSelect",
                                                             value=kwargs["secondary_storage"])
        if self._adminconsole.check_if_entity_exists('xpath', "//button/span[contains(text(),'Create')]"):
            self._adminconsole.click_button_using_text(value="Create")
            self.__wait_for_cloud_storage_creation()

    @PageService()
    def select_existing_plan(self, plan_name):
        """"Selects existing plan option
        Args:
            plan_name   (str)   :   Name of the plan to be selected
        """
        self.utils_helper.select_radio_by_id("optExistingPlan")
        self.__select_plan_from_list_of_radio(plan_name)

    @PageService()
    def select_create_new_plan(self, retention_period, **kwargs):
        """Creates a new plan with the arguments specified
        Args:
            retention_period   (str)  :   Can be '1 month', '1 year','3 year' or 'custom'

        Keyword Args (Used only when custom plan is selected:
            custom_retention   (str)  :   Custom Retention
            retention_unit     (str)  :   Retention Unit(days, months or years)
            backup_frequency   (str)  :   Full backup frequency
            backup_frequency_unit(str):   Full backup frequency unit(hours or days)
            log_frequency      (str)  :   Log Backup Frequency
            log_frequency_unit (str)  :   Log Backup Frequency unit(mins or hours)

        Returns:
            str :   Name of the new plan created
        """
        self.utils_helper.select_radio_by_id("optNewPlan")
        retention_period_dict = {
            "1 month": "1 Month Retention Plan",
            "1 year": "1 Year Retention Plan",
            "3 year": "3 Year Retention Plan",
            "custom": "Custom Plan"
        }
        if retention_period.lower() not in retention_period_dict.keys():
            raise CVWebAutomationException("Exception raised in select_create_new_plan : "
                                           "Invalid retention period specified. Please provide "
                                           "'1 month', '1 year', '3 year' or 'custom' as value "
                                           "for \"RetentionPeriod\"")

        self.__select_plan_from_list_of_radio(retention_period_dict[retention_period])

        if retention_period.lower() == "custom":
            self._adminconsole.fill_form_by_id("secondaryRetention", kwargs["custom_retention"])
            self.utils_helper.select_value_from_dropdown("secondaryRetentionUnit",
                                                         kwargs["retention_unit"])

            self._adminconsole.fill_form_by_id("backupFrequency", kwargs["backup_frequency"])
            self.utils_helper.select_value_from_dropdown("backupFrequencyUnit",
                                                         kwargs["backup_frequency_unit"])

            self._adminconsole.fill_form_by_id("logBackupFrequency", kwargs["log_frequency"])
            self.utils_helper.select_value_from_dropdown("logBackupFrequencyUnit",
                                                         kwargs["log_frequency_unit"])

        time1 = (datetime.now()).strftime("%H:%M:%S").replace(":", "")
        plan_name = "DB_{0}_Plan_{1}".format(self.app_type.value.replace(" ", "_"), time1)
        self._adminconsole.fill_form_by_id("planName", plan_name)
        self._adminconsole.click_button_using_text(value="Create")

        self.utils_helper.wait_for_spinner()
        status, msg = self.__get_text_info_after_spinner()
        if not status:
            raise CVWebAutomationException(f"Failed to create plan with error : {msg}")
        if "already exists" in msg:
            raise CVWebAutomationException(f"Plan with same name already exists. Error : {msg}")
        self._LOG.info(
            "*" * 10 + " Plan : {0}, successfully created ".format(plan_name) + "*" * 10)
        return plan_name

    @WebAction(delay=0)
    def __click_next_without_wait(self):
        """Clicks next without wait"""
        self._adminconsole.driver.find_element(By.XPATH, "//button[contains(.,'Next')]").click()

    def configure_database(self,
                           commcell,
                           install_inputs,
                           deploy_type='DIRECT_TO_CLOUD',
                           cloud_storage_inputs=None,
                           use_existing_plan=True,
                           plan_inputs=None):
        """Configures and sets up database from Metallic Hub

        Args:
            commcell                          : Commcell object

            install_inputs   (dict)           : Dictionary input that goes for configuring DB
                                                package install

                                                dictionary passed should be:
                                                {
                                                "remote_clientname"     : "<FQDN of the machine>"
                                                "remote_username"       : "<username to connect
                                                                            to remote machine>"
                                                "remote_userpassword"   : "<password to connect
                                                                            to remote machine>"
                                                "os_type"               :  "<OS type of remote
                                                                            client>"
                                                "username"              : "<Username of CS to
                                                                            authenticate client>"
                                                "password"              : "<Password of CS to
                                                                            authenticate client>"
                                                "authcode" (optional)   : "<Authcode to
                                                                            authenticate client>"
                                                }


            deploy_type                (str)    : Can be 'VIA_GATEWAY' or 'DIRECT_TO_CLOUD'
                                                  depending on deployment
                    default value      (str)    : 'DIRECT_TO_CLOUD'  --> Backup direct to cloud
                                                   option in Hub

            cloud_storage_inputs       (dict)   : Dictionary input that goes for configuring cloud
                                                  storage.

                                                   dictionary passed should be:
                                                  {
                                                   "StorageAccount": "<storage account>",
                                                   "CloudProvider" : "<cloud storage provider>",
                                                   "Region"        : "<storage region>"
                                                  }

            use_existing_plan          (bool)   : If True uses an existing plan, else configures a
                                                  new one with the provided inputs

            plan_inputs                (dict)   : Dictionary input that goes for plan
                                                  If use_existing_plan is true,
                                                  dictionary passed should be:
                                                  {
                                                   "PlanName": "<Existing plan name>"
                                                  }
                                                  If use_existing_plan is false,
                                                  dictionary passed should be:
                                                  {
                                                   "RetentionPeriod": "<Retention period>"
                                                  }
        Returns:
            str     :       Name of the new plan created if use_existing_plan is false
        """
        try:
            self.hub_dashboard = Dashboard(self._adminconsole, self.service, self.app_type)
            self.hub_dashboard.click_get_started()
            self.hub_dashboard.choose_service_from_dashboard()
            self.hub_dashboard.click_new_configuration()

            # select trial subscription
            self.select_database_environment()
            self._adminconsole.click_button_using_text(value="Next")
            self.select_trial_subscription()
            # Backup deployment
            self.select_backup_deploy(deploy_type)
            self._adminconsole.click_button_using_text(value="Next")

            self.configure_application_access(commcell, install_inputs)
            self.__click_next_without_wait()

            if "sql" not in self.app_type.name.lower():
                self.__check_install_complete()

            self.select_cloud_storage(
                cloud_storage_inputs["StorageAccount"],
                cloud_storage_inputs["CloudProvider"],
                cloud_storage_inputs["Region"])
            self._adminconsole.click_button_using_text(value="Next")

            if use_existing_plan:
                self.select_existing_plan(plan_inputs["PlanName"])
                plan_name = plan_inputs["PlanName"]
            else:
                plan_name = self.select_create_new_plan(plan_inputs["RetentionPeriod"])
            self._adminconsole.click_button_using_text(value="Next")

            self.utils_helper.wait_for_spinner()

            if "hana" not in self.app_type.name.lower():
                self.__check_successful_configuration()
                sleep(5)
                self._LOG.info("*" * 10 + " Finished initial configuration. Redirecting to Metallic Hub " + "*" * 10)
                self._adminconsole.click_button_using_text("Return to Hub")
                sleep(5)

            return plan_name

        except Exception as exp:
            raise CVWebAutomationException("Exception raised in configure_database()"
                                           "\nError: '{0}'".format(exp))


class RDatabasesMetallic:
    """React class that provides helper function for configuring database from metallic screens"""

    def __init__(self, adminconsole, app_type):
        """Constructor function for this class
        Args :
            adminconsole (obj:'AdminConsole')   : Object of AdminConsole class
            app_type (str)                      : Specify the database type. Should be from
                                                  Web.Adminconsole.Hub.constants DatabaseTypes class
        """
        self.service = HubServices.database
        self.app_type = app_type
        self.wizard = Wizard(adminconsole)
        self.rmodal = RModalDialog(adminconsole)
        self.controller_obj = Machine()
        self._adminconsole = adminconsole
        self._adminconsole.load_properties(self)
        self._driver = adminconsole.driver
        self.utils_helper = Utils(adminconsole)
        self.rdropdown = RDropDown(adminconsole)
        self._LOG = logger.get_log()
        self.hub_dashboard = None
        self.navigator = None
        self.service_catalogue = None

    @WebAction()
    def _is_error_message_present(self):
        """ Method to check if error message is present in the dialog
        Returns:
            bool : True if error message is present, else False
        """
        error_message_xpath = (
            "//*[contains(@class, 'MuiAlert-root')]/*[contains(@class, 'MuiAlert-message')]"
            "//div[contains(text(), 'Something went wrong. Please check the logs for details.')] | "
            "//*[contains(@class, 'MuiAlert-root')]/*[contains(@class, 'MuiAlert-message')]"
            "//div[contains(text(), 'Unable to create storage.')] |"
            "//*[contains(text(), 'Error while creating the plan')] |"
            "//*[contains(text(), 'Failed to create storage policy ')] |"
            "//*[contains(text(), 'Lock request time out period exceeded.')]"
        )
        return self._adminconsole.check_if_entity_exists(By.XPATH, error_message_xpath)

    @staticmethod
    def create_tenant(testcase_instance, tenant_name_prefix, ring_hostname):
        """Creates a tenant with the given name
        Args:
            testcase_instance       (TestCase) :  Testcase Instance
            tenant_name_prefix      (str)   :   Prefix of the tenant name
            ring_hostname           (str)   :   Ring hostname
        Returns:
            str     :       Name of the tenant created
        """
        # getting list of companies with given prefix
        tenant_mgmt = HubManagement(testcase_instance, ring_hostname)
        commcell_object = testcase_instance.commcell
        companies_list = commcell_object.organizations.all_organizations
        companies_list_with_given_prefix = [key for key, value in companies_list.items() if
                                            key.startswith(f"{tenant_name_prefix}-Automation".lower())]
        # checking if there are any companies within 24hrs
        for company in companies_list_with_given_prefix:
            company_date_time = datetime.strptime(company, f"{tenant_name_prefix}-Automation-%Y-%d-%B-%H-%M")
            organization = commcell_object.organizations.get(company)
            user_groups_in_company = organization.user_groups
            users_in_user_group = commcell_object.user_groups.get(user_groups_in_company[0]).users
            if datetime.now() - company_date_time < timedelta(hours=24):
                testcase_instance.log.info(f"Using existing company : {company}")
                tenant_username = users_in_user_group[0]
                break
            else:
                # deactivating and deleting the company if it is older than 24hrs
                tenant_mgmt.deactivate_tenant(company)
                tenant_mgmt.delete_tenant(company)
        # if there are no companies within 24hrs
        else:
            testcase_instance.log.info("Creating new company")
            company_name = datetime.now().strftime(f"{tenant_name_prefix}-Automation-%Y-%d-%B-%H-%M")
            email = datetime.now().strftime(f"automation_user@{company_name}.com")
            tenant_username = tenant_mgmt.create_tenant(company_name, email)
        return tenant_username

    @PageService()
    def click_looped_submit(self, max_attempts=5):
        """Clicks on the submit button in a loop
             Args :
                    max_attempts (int) : Maximum number of attempts
             """
        attempt = 0
        while attempt < max_attempts:
            self.rmodal.click_submit()
            # Check for error message on the screen
            if self._is_error_message_present():
                attempt += 1
                time.sleep(120)  # wait for 120 seconds before next attempt
            else:
                break

    @WebAction()
    def _click_add_icon(self):
        """method to click + icon to add credentials in storage account screen"""
        self._adminconsole.wait_for_completion()
        xpath = "//div[@aria-label='Create new' or @aria-label='Add']/button"
        self._adminconsole.driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def select_trial_subscription(self):
        """ Clicks on Start trial subscription dialog"""
        if self._adminconsole.check_if_entity_exists(entity_name='id', entity_value='manageSubscription'):
            xpath = "//div[@id='manageSubscription']//button[@aria-label='Start trial']"
            if self._adminconsole.check_if_entity_exists(entity_name='xpath', entity_value=xpath):
                self._driver.find_element(By.XPATH, xpath).click()
                self._adminconsole.wait_for_completion()
                subscription_dialog = RModalDialog(self._adminconsole, title='Subscription created')
                subscription_dialog.click_close()
                self._adminconsole.wait_for_completion()
        xpath = "//div[@id='manageSubscription']//button[@aria-label='Continue']"
        if self._adminconsole.check_if_entity_exists(entity_name='xpath', entity_value=xpath):
            self._driver.find_element(By.XPATH, xpath).click()
            self._adminconsole.wait_for_completion()

    @PageService()
    def select_database(self):
        """selects the database to be configured"""
        try:
            self.service_catalogue = ServiceCatalogue(self._adminconsole, self.service, self.app_type)
            self.service_catalogue.click_get_started()
            self.service_catalogue.choose_service_from_service_catalogue(service=self.service.value,
                                                                         id=self.app_type.value)

        except Exception as exp:
            raise CVWebAutomationException(
                f"Exception raised in select_database() Error: '{exp}'") from exp

    @PageService()
    def select_backup_method(self, backup_method_id):
        """
        Selecting the backup method
        Args:
            backup_method_id              (str):  ID of the backup method radio button

        """
        self.wizard.select_radio_button(id=backup_method_id)

    @PageService()
    def _create_azure_storage_credentials(self, storage_credential, storage_account_name, storage_password):
        """
        Method to create Azure storage credential
        Args:
            storage_credential              (str):  Name of the Azure storage credential
            storage_account_name            (str):  Storage Account name
            storage_password                (str):  Access key of the storage account
        """
        dialog = RModalDialog(admin_console=self._adminconsole, title=self._adminconsole.props['label.addCredential'])
        dialog.fill_text_in_field(element_id="name", text=storage_credential)
        dialog.fill_text_in_field(element_id="accountName", text=storage_account_name)
        dialog.fill_text_in_field(element_id="accessKeyId", text=storage_password)
        dialog.click_submit()

    @PageService()
    def _create_azure_app_credentials(self, credential_name):
        """
        Method to create Azure App credential
        Args:
            credential_name     (str):  Name of the Azure app credential
        """
        dialog = RModalDialog(admin_console=self._adminconsole, title=self._adminconsole.props['label.addCredential'])
        dialog.fill_text_in_field(element_id="name", text=credential_name)
        dialog.fill_text_in_field(element_id="tenantId", text=_CONFIG_DATA.Azure.Tenant)
        dialog.fill_text_in_field(element_id="applicationId", text=_CONFIG_DATA.Azure.App.ApplicationID)
        dialog.fill_text_in_field(element_id="applicationSecret", text=_CONFIG_DATA.Azure.App.ApplicationSecret)
        dialog.click_submit()

    @PageService()
    def _create_azure_mrr_storage(self):
        """Method to create MRR storage account"""
        self.wizard.select_drop_down_values(
            id='cloudType', values=[self._adminconsole.props['label.deviceType.METALLIC_RECOVERY_RESERVE']])
        xpath = "//button[contains(@class, 'MuiButton-root')]//div[text()='Start trial']"
        if self._adminconsole.check_if_entity_exists(entity_name='xpath', entity_value=xpath):
            self._adminconsole.click_button(value="Start trial")
            self._adminconsole.click_button(value="Close")
        self._adminconsole.click_button('Save')

    @PageService()
    def _create_microsoft_azure_storage(self, **kwargs):
        """
        Method to create Microsoft Azure cloud storage
        Keyword Args:
            cloud_storage_name      (str):  Name of the Metallic Azure storage to be created
            storage_credential      (str):  Name of the Azure Storage Credential
            storage_account_name    (str):  Storage Account name
            storage_password        (str):  Access key of the storage account
            container               (str):  Name of the storage container
            storage_auth_type       (str):  Type of Authentication for cloud storage
        """
        self.wizard.select_drop_down_values(
            id='cloudType', values=[self._adminconsole.props['label.deviceType.MICROSOFT_AZURE_STORAGE']])
        self._adminconsole.fill_form_by_id("cloudStorageName", kwargs.get("cloud_storage_name"))
        self.rdropdown.select_drop_down_values(drop_down_id="storageClass",
                                               values=[self._adminconsole.props['label.storageClass.AZURE_HOT']])
        match kwargs.get("storage_auth_type"):
            case "Access key and Account name":
                self.wizard.select_drop_down_values(
                    id='authentication', values=[self._adminconsole.props['label.azureAN']])
                self._click_add_icon()
                self._create_azure_storage_credentials(kwargs.get("storage_credential"),
                                                       kwargs.get("storage_account_name"),
                                                       kwargs.get("storage_password"))

            case "IAM AD application":
                self.wizard.select_drop_down_values(
                    id='authentication', values=[self._adminconsole.props['label.rbac']])
                self._adminconsole.fill_form_by_id("loginName", kwargs.get("storage_account_name"))
                self._click_add_icon()
                self._create_azure_app_credentials(kwargs.get("storage_credential"))

            case "IAM VM role":
                self.wizard.select_drop_down_values(
                    id='authentication', values=[self._adminconsole.props['label.managedIdentity']])
                self._adminconsole.fill_form_by_id("loginName", kwargs.get("storage_account_name"))

        self._adminconsole.fill_form_by_id("mountPath", kwargs.get("container"))
        self._adminconsole.click_button('Save')
        self._adminconsole.wait_for_completion()

    @PageService()
    def _create_azure_storage(self, **kwargs):
        """
        Method to create Azure cloud storage
        Keyword Args:
            is_secondary_storage            (bool): True if creating secondary copy
                    default :   False
            is_primary_mrr                  (bool): True if creating primary MRR Storage
                    default :   False
            is_secondary_mrr                (bool): True if creating secondary MRR Storage
                    default :   False
            cloud_storage_name      (str):  Name of the Metallic Azure storage to be created
            storage_credential              (str):  Name of the Azure Storage Credential
            storage_account_name    (str):  Storage Account name
            storage_password                (str):  Access key of the storage account
            container               (str):  Name of the storage container
            storage_auth_type       (int):  Type of Authentication for cloud storage
        """

        self.wizard.click_add_icon()
        self._adminconsole.wait_for_completion()
        if kwargs.get("is_primary_mrr"):
            self._create_azure_mrr_storage()
            if kwargs.get("is_secondary_storage"):
                self._adminconsole.wait_for_completion()
                self.wizard.enable_toggle(label=self._adminconsole.props['label.secondaryCopy'])
                self.wizard.click_add_icon(index=1)
                self._adminconsole.wait_for_completion()
                self._create_azure_mrr_storage()
        else:
            self._create_microsoft_azure_storage(**kwargs)
            if kwargs.get("is_secondary_storage"):
                self._adminconsole.wait_for_completion()
                self.wizard.enable_toggle(label=self._adminconsole.props['label.secondaryCopy'])
                self.wizard.click_add_icon(index=1)
                self._adminconsole.wait_for_completion()
                if kwargs.get("is_secondary_mrr"):
                    self.wizard.select_drop_down_values(
                        id='cloudType', values=['Air Gap Protect'])
                    dialog = self.rmodal
                    dialog.select_dropdown_values(drop_down_id="storageClass",
                                                  values=[self._adminconsole.props['label.metallicHot']])
                    dialog.click_submit()
                else:
                    self._create_microsoft_azure_storage(**kwargs)

    @PageService()
    def _select_storage_account(self, region):
        """
        Selects the storage account
        Args:
            region      (str):      Storage account name
        """
        self.wizard.click_refresh_icon()
        self._adminconsole.wait_for_completion()
        self.wizard.select_drop_down_values(
            id='metallicCloudStorageDropdown', values=[region])
        self.wizard.click_next()

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
        """
        Method to create plan with default settings
        Args:
            name        (str):  The name of the plan
        """
        self.wizard.click_icon_button_by_label(label="Add")
        self._adminconsole.wait_for_completion()
        self._adminconsole.fill_form_by_id('planNameInputFld', name)
        self.click_looped_submit()
        self._adminconsole.wait_for_completion()

    @PageService()
    def continue_trial_subscription(self):
        """Clicks on continue button for continuing trial subscription
        """
        self._adminconsole.click_button(value="Continue")

    @PageService()
    def proceed_from_summary_page(self):
        """Proceeds from the summary page after configuration is done"""
        self.wizard.click_button(name="Finish")

    @PageService()
    def select_backup_content(self):
        """Proceeds from the backup_content page for Oracle Metallic New Configuration"""
        self._adminconsole.click_button(value="Next")

    @PageService()
    def select_backup_deploy(self, deploy_type="Cloud"):
        """Select the backup deploy option
                Args:
                    deploy_type            (str)    :    Can be 'access_node' or 'cloud' depending
                                                         on deployment
                        default value      (str)    :   'Cloud'  --> Cloud option in DbInstanceLanding Page
        """
        if deploy_type.lower() == "cloud":
            self._adminconsole.select_radio(id="cloudStorage")
            self._adminconsole.click_button(value="Next")
        elif deploy_type.lower() == "access_node":
            self._adminconsole.select_radio(id="accessNode")
            self._adminconsole.click_button(value="Next")
        else:
            raise CVWebAutomationException("Exception raised in select_backup_deploy(). Wrong "
                                           "deployment method")

    @WebAction()
    def select_vm_type(self, vm_type="cloud"):
        """Selects cloud vm or on premise vm
        Args :
            vm_type     (str) : "Can be either cloud or onprem"
                default : "cloud"
        """
        if vm_type.lower() == "cloud":
            self._adminconsole.select_radio(id="cloudInstance")
        else:
            self._adminconsole.select_radio(id="onPremInstance")

    @PageService()
    def select_cloud_vm_details(self, vendor, app_type, oci_service_type=None):
        """Enters the cloud vm details for metallic software installation for Oracle
        Args:
            vendor              (str)       : "Can be either Microsoft Azure or Oracle Cloud Infrastructure or Amazon Web Services
            app_type            (str)       : "Can be either DatabaseTypes. Oracle or DatabaseTypes.oracle_rac
            oci_service_type    (str)       : "DB service type for Oracle Cloud infrastructure vm"
                                                default None
       """
        self.close_info_dialog()
        self.select_vm_type()
        self.rdropdown.select_drop_down_values(drop_down_id="vendorType", values=[vendor])
        if vendor == "Oracle Cloud Infrastructure":
            self.rdropdown.select_drop_down_values(drop_down_id="serviceType",
                                                   values=[oci_service_type])
        else:
            if app_type == DatabaseTypes.oracle:
                self.rdropdown.select_drop_down_values(drop_down_id="serviceType", values=["Oracle (single node)"])
            elif app_type == DatabaseTypes.ORACLE_RAC:
                self.rdropdown.select_drop_down_values(drop_down_id="serviceType",
                                                       values=["Oracle RAC(multi-node)"])
        self._adminconsole.click_button(value="Next")
        if self._adminconsole.check_if_entity_exists("xpath", '//div/*[text()="Trial in progress"]'):
            self.continue_trial_subscription()
        else:
            self._adminconsole.click_button(value="Start trial")
            self._adminconsole.click_button(value="Close")

    @PageService(react_frame=False)
    def close_info_dialog(self):
        """Method to close the information dialog"""
        if self._adminconsole.check_if_entity_exists("xpath", "//div[@id='pendo-guide-container']/button"):
            self._adminconsole.driver.find_element(By.XPATH, "//div[@id='pendo-guide-container']/button").click()

    @PageService()
    def select_on_prem_details(self, infrastructure, app_type):
        """Enters the details for on premise vm for Database Instance Landing Page
        Args:
            infrastructure   (str)    : Can either be Physical client or Virtual machine
            app_type                  : "Can be either DatabaseTypes.oracle, DatabaseTypes.oracle_rac, DatabaseTypes.sql
        """
        self.close_info_dialog()
        self.select_vm_type(vm_type="onprem")
        self.rdropdown.select_drop_down_values(drop_down_id="dbLocationType", values=[infrastructure])
        if app_type == DatabaseTypes.oracle:
            self.rdropdown.select_drop_down_values(drop_down_id="onPreServiceType", values=["Oracle (single node)"])
        elif app_type == DatabaseTypes.ORACLE_RAC:
            self.rdropdown.select_drop_down_values(drop_down_id="onPreServiceType",
                                                   values=["Oracle RAC(multi-node)"])
        self._adminconsole.click_button(value="Next")
        if self._adminconsole.check_if_entity_exists("xpath", '//div/*[text()="Trial in progress"]'):
            self.continue_trial_subscription()
        else:
            self._adminconsole.click_button(value="Start trial")
            self._adminconsole.click_button(value="Close")

    @PageService()
    def create_new_plan(self, retention_period, **kwargs):
        """Creates a new plan with the arguments specified
                Args:
                    retention_period   (str)  :   Can be '1 month', '1 year','3 year' or 'custom'

                 Keyword Args (Used only when custom plan is selected:
                    custom_retention   (str)  :   Custom Retention
                    retention_unit     (str)  :   Retention Unit(days, months or years)
                    backup_frequency   (str)  :   Full backup frequency
                    backup_frequency_unit(str):   Full backup frequency unit(hours or days)
                    log_frequency      (str)  :   Log Backup Frequency
                    log_frequency_unit (str)  :   Log Backup Frequency unit(mins or hours)

                Returns:
                    str :   Name of the new plan created
                """
        self.wizard.click_icon_button_by_label(label="Add")
        retention_period_dict = {
            "1 month": "1 Month Retention Plan",
            "1 year": "1 Year Retention Plan",
            "3 year": "3 Year Retention Plan",
            "custom": "Custom Plan"
        }
        if retention_period.lower() not in retention_period_dict.keys():
            raise CVWebAutomationException("Exception raised in select_create_new_plan : "
                                           "Invalid retention period specified. Please provide "
                                           "'1 month', '1 year', '3 year' or 'custom' as value "
                                           "for \"RetentionPeriod\"")
        time1 = (datetime.now()).strftime("%H:%M:%S").replace(":", "")
        plan_name = "DB_{0}_Plan_{1}".format(self.app_type.value.replace(" ", "_"), time1)
        self._adminconsole.fill_form_by_id(element_id="planNameInputFld", value=plan_name)
        if retention_period.lower() == "custom":
            self.wizard.select_radio_button(id="custom")
            self._adminconsole.fill_form_by_id(element_id="retentionPeriod", value=kwargs["retentionPeriod"])
            self.rdropdown.select_drop_down_values(drop_down_id="retentionPeriodUnit",
                                                   values=[kwargs["retentionPeriodUnit"]])
            self._adminconsole.fill_form_by_id(element_id="backupFrequency", value=kwargs["backupFrequency"])
            self.rdropdown.select_drop_down_values(drop_down_id="backupFrequencyUnit",
                                                   values=[kwargs["backupFrequencyUnit"]])
        elif retention_period.lower() == "1 year":
            self.wizard.select_radio_button(id="1Year")
        elif retention_period.lower() == "3 year":
            self.wizard.select_radio_button(id="3Year")
        self._adminconsole.click_button(value="Done")
        self._LOG.info(
            "*" * 10 + " Plan : {0}, successfully created ".format(plan_name) + "*" * 10)
        return plan_name

    @WebAction()
    def _get_install_command(self):
        """Returns install command for linux interactive install"""
        xpath = "//*[contains(text(), './silent_install')]"
        if not self._adminconsole.is_element_present(xpath):
            return ""
        return self._driver.find_element(By.XPATH, xpath).text

    @PageService()
    def do_pkg_install(self, pkg_file_path, install_inputs, commcell=None, silent_install=False):
        """Helper function to do the DB package install
        Args:
            commcell                  : "Commcell object"

            pkg_file_path    (str)    : Seed package file path

            install_inputs (list[dict])   : List of Dictionaries input that goes for configuring DB package
                                          install. Number of dictionaries should be equal to number of machines

                                          dictionary passed should be:
                                          {
                                              "remote_clientname"     : "<FQDN of the machine>"
                                              "remote_username"       : "<username to connect to
                                                                         remote machine>",
                                              "remote_userpassword"   : "<password to connect to
                                                                         remote machine>",
                                              "os_type"               :  "<OS type of remote client>"
                                              "username"              : "<Username of CS to
                                                                        authenticate client>"
                                              "password"              : "<Password  of CS
                                                                        authenticate client>"
                                              "authcode" (optional)   : "<Authcode to
                                                                        authenticate client>"
                                          }
            silent_install  (bool)  :   Boolean value on performing install silently
        """
        if isinstance(install_inputs, dict):
            install_inputs = [install_inputs]

        for i in range(len(install_inputs)):
            remote_machine_credentials = {
                "remote_clientname": install_inputs[i].get("remote_clientname"),
                "remote_username": install_inputs[i].get("remote_username"),
                "remote_userpassword": install_inputs[i].get("remote_userpassword")
            }
            time.sleep(60)
            install_command = self._get_install_command()
            if install_command and (install_inputs[i].get("os_type") == 'unix'):
                remote_machine = Machine(machine_name=remote_machine_credentials["remote_clientname"],
                                         username=remote_machine_credentials["remote_username"],
                                         password=remote_machine_credentials["remote_userpassword"])
                if remote_machine.check_directory_exists(directory_path='/metallic_install'):
                    remote_machine.remove_directory(directory_name='/metallic_install')
                remote_machine.create_directory(directory_name='/metallic_install')
                remote_machine.copy_from_local(local_path=pkg_file_path, remote_path="/metallic_install")
                file_name = remote_machine.get_files_in_path("/metallic_install", recurse=False)[0]
                op = remote_machine.execute_command(
                    f'cd /metallic_install && tar -xvf {file_name}')
                folder_names = remote_machine.get_folders_in_path("/metallic_install", recurse=False)
                if len(folder_names) == 1:
                    raise CVWebAutomationException("Extract command failed")
                op1 = remote_machine.execute_command(f'cd {folder_names[1]}/pkg && {install_command}')
            else:
                install_helper = InstallCustomPackage(commcell,
                                                      remote_machine_credentials,
                                                      install_inputs[i].get("os_type"))

                if "authcode" in install_inputs[i].keys():
                    install_helper.install_custom_package(pkg_file_path, install_inputs[i].get("authcode"))
                else:
                    if silent_install:
                        authcode = install_command[17:].split(" ")[1]
                        install_helper.install_custom_package(pkg_file_path,
                                                              install_inputs[i].get("username"),
                                                              install_inputs[i].get("password"),
                                                              authcode=authcode,
                                                              silent_install=silent_install,
                                                              plan_name=install_inputs[i].get("plan_name", None))
                    else:
                        install_helper.install_custom_package(pkg_file_path,
                                                              install_inputs[i].get("username"),
                                                              install_inputs[i].get("password"))

        self._LOG.info("Install successfully completed!!")
        self.controller_obj.delete_file(pkg_file_path)
        time_left = 480
        while time_left:
            self._LOG.info("Waiting for the registration to complete")
            self.wizard.click_icon_button_by_title(title="Refresh")
            time.sleep(30)
            time_left -= 30
            xpath = f"//div[@id='accessNodeDropdown']//ancestor::div[contains(@aria-disabled, 'true')]"
            if not self._adminconsole.is_element_present(xpath):
                self.rdropdown.select_drop_down_values(select_all=True, drop_down_id="seedPackageServer")
                break
        client_names = self.rdropdown.get_selected_values(drop_down_id="seedPackageServer")
        self.wizard.click_next()
        if len(client_names) == 0 or len(install_inputs) != len(client_names):
            raise CVWebAutomationException("Registration failed for one or more clients")
        elif len(client_names) == 1:
            return client_names[0]
        else:
            return client_names

    @PageService()
    def do_push_install(self, install_inputs):
        """method runs the push install
           install_inputs (dict)   :

                                          dictionary passed should be:
                                          {
                                              "remote_clientname"              : "<FQDN of the machine>"
                                              "remote_username"                : "username to connect to
                                                                                 remote machine,
                                              "remote_userpassword"            : "password to connect to
                                                                                 remote machine",
                                              "instance_name"                  : "Instance running on the machine",
                                              "ssh_key_path"   (optional)      : "private key for the remote machine",
                                              "unix_group"     (optional)      : "unix group for install"
                                          }
        """
        self.wizard.select_radio_button(id="PUSH")
        xpath = f"//button[contains(@class, 'MuiIconButton-root') and @aria-label='Reload data']"
        time_left = 30
        while not self._adminconsole.is_element_present(xpath) and time_left:
            self._LOG.info("Waiting for db services to be discovered")
            time.sleep(30)
            time_left -= 30
        if time_left < 300:
            dialog = RModalDialog(admin_console=self._adminconsole, title="Edit Oracle database service")
            self._adminconsole.click_by_xpath(
                xpath=f"//td[text()='{install_inputs['remote_clientname']}']/preceding-sibling::td[input]"
                      f"/child::input[@type='checkbox']")
            self._adminconsole.click_by_xpath(
                xpath=f"//td[text()='{install_inputs['remote_clientname']}']"
                      f"/following-sibling::td[contains(@class,'grid-cell')]"
                      f"/child::a[contains(@title,'Edit')]")

            dialog.fill_text_in_field(element_id="userName", text=install_inputs["remote_username"])
            if "ssh_key_path" in install_inputs and install_inputs["ssh_key_path"]:
                self._adminconsole.click_by_xpath(xpath=f"//input[contains(@id,'useSSHKey')]")
                self._driver.find_element_by_xpath("//input[@name='sshKeyPath']").send_keys(
                    install_inputs["ssh_key_path"])
            dialog.click_submit()
        self.wizard.click_button(name="Add")
        dialog = RModalDialog(admin_console=self._adminconsole, title="Add Oracle database service")
        dialog.fill_text_in_field(element_id="databaseService",
                                  text=install_inputs.get("instancename") or "databaseService")
        dialog.fill_text_in_field(element_id="hostName", text=install_inputs.get("remote_clientname") or "hostname")
        dialog.fill_text_in_field(element_id="userName", text=install_inputs.get("remote_username") or "username")
        if "ssh_key_path" in install_inputs and install_inputs["ssh_key_path"]:
            self._adminconsole.click_by_xpath(xpath=f"//input[contains(@id,'useSSHKey')]")
            self._driver.find_element_by_xpath("//input[@name='sshKeyPath']").send_keys(
                install_inputs["ssh_key_path"])
        else:
            dialog.fill_text_in_field(element_id="password",
                                      text=install_inputs.get("remote_userpassword") or "password")
            dialog.fill_text_in_field(element_id="conformPassword",
                                      text=install_inputs.get("remote_userpassword") or "password")
        if "unixGroup" in install_inputs and install_inputs["unixGroup"]:
            dialog.fill_text_in_field(element_id="unixGroup", text=install_inputs["unixGroup"])
        dialog.click_submit()
        if time_left < 300:
            self._adminconsole.click_by_xpath(
                xpath=f"//td[text()='databaseService']/preceding-sibling::td[input]/child::input[@type='checkbox']")
        self.wizard.click_button(name="Next")

    @PageService()
    def select_cloud_storage(self, cloud_vendor, storage_provider, region):
        """Helper function for selecting oracle cloud storage
        Args:
            cloud_vendor     (str)  :  selects cloud vendor for oracle storage
            storage_provider (str)  : Applicable for Metallic Recovery Reserve, Can be Azure Blob Storage or OCI Object
                                          Storage
            region            (str) : Region for Storage

        """
        self.wizard.click_add_icon()
        self._adminconsole.wait_for_completion()
        self.rdropdown.select_drop_down_values(drop_down_id="cloudType", values=[cloud_vendor], partial_selection=True)
        self.rdropdown.select_drop_down_values(drop_down_id="offering", values=[storage_provider],
                                               partial_selection=True)
        self._adminconsole.click_button(value="Start trial")
        self._adminconsole.click_by_xpath(xpath="//button[contains(@class, 'MuiButtonBase-root')]/div[text()='Close']")
        self.rdropdown.select_drop_down_values(drop_down_id="region", values=[region], partial_selection=True)
        self.click_looped_submit()
        self._adminconsole.wait_for_completion()
        self._adminconsole.click_button(value="Next")

    @WebAction()
    def __select_pkg_download(self, platform, file_name):
        """Selects the DB package for download
            Args    :
                platform (str)      :   Platform of the client, values can be AIX,HP-UX,linux,PowerPC,Solaris
                                            and Windows

                file_name           :   File Name of the install package
        """
        platform_dict = {"AIX": "AIX", "HP-UX": "HP-UX", "Linux": "Linux (64-bit)", "PowerPC": "PowerPC",
                         "Solaris": "Solaris", "Windows": "Windows (64-bit)"}
        download_xpath = ""
        if self.app_type == DatabaseTypes.oracle:
            xpath_platform = platform_dict.get(platform)
            download_xpath = f"//td[text() =\"{xpath_platform}\"]/following-sibling::td//a[@type='button']"
        elif self.app_type == DatabaseTypes.sql:
            download_xpath = f"//a[contains(@href, '{file_name}') and @type='button']"
        elif self.app_type == DatabaseTypes.sap_hana:
            xpath_platform = platform_dict.get(platform)
            download_xpath = f"//td[text() =\"{xpath_platform}\"]/following-sibling::td//a[@type='button']"
        self._adminconsole.driver.find_element(By.XPATH, download_xpath).click()
        time.sleep(10)
        self._adminconsole.wait_for_completion()

    @PageService()
    def do_pkg_download(self, platform="Windows"):
        """Helper function for the download of seed package
                Args:
                    platform (str)      :   Platform of the client, values can be AIX,HP-UX,unix,PowerPC,Solaris
                                            and Windows

                Returns:
                    pkg_file_path (str) :   File path of the downloaded package
        """
        file_name = ""
        if self.app_type == DatabaseTypes.oracle:
            file_name = f"{platform}OracleServer64.tar"
        elif self.app_type == DatabaseTypes.sql:
            file_name = "MSSQLServer64.exe" if platform == "Windows" else "MSSQLServer64.tar"
        elif self.app_type == DatabaseTypes.sap_hana:
            file_name = f"{platform}HANAServer64.tar"
        pkg_file_path = self.controller_obj.join_path(TEMP_DIR, file_name)
        if self.controller_obj.check_file_exists(pkg_file_path):
            self.controller_obj.delete_file(pkg_file_path)
        self.__select_pkg_download(platform, file_name)
        i = 0
        while not self.controller_obj.check_file_exists(pkg_file_path):
            self._LOG.info("Please wait for download to finish")
            sleep(60)
            i += 1
            if i == 10:
                raise CVWebAutomationException("Download failed due to timeout")
        self._LOG.info("Package download completed!!")
        return pkg_file_path

    def __is_entity_exist_and_displayed(self, xpath):
        if self._adminconsole.check_if_entity_exists("xpath", xpath):
            return self._driver.find_element(By.XPATH, xpath).is_displayed()
        return False

    @WebAction()
    def __get_text_info_after_spinner(self):
        """Gets the text message that comes up after spinner element has completed"""
        success_xpath = "//mdb-icon[contains(@class, \"green-text\")]"
        fail_xpath = "//mdb-icon[contains(@class, \"red-text\")]"
        fail_xpath1 = "//small[@class=\"text-danger\"]"
        fail_xpath2 = "//small[@class=\"text-danger error-msg\"]"
        if self.__is_entity_exist_and_displayed(success_xpath):
            success_text_box = self._driver.find_element(By.XPATH, success_xpath)
            self._LOG.info(success_text_box.text)
            return True, success_text_box.text
        elif self.__is_entity_exist_and_displayed(fail_xpath):
            fail_text_box = self._driver.find_element(By.XPATH, fail_xpath)
            self._LOG.error(fail_text_box.text)
            return False, fail_text_box.text
        elif self.__is_entity_exist_and_displayed(fail_xpath2):
            fail_text_box = self._driver.find_element(By.XPATH, fail_xpath2)
            self._LOG.error(fail_text_box.text)
            return False, fail_text_box.text
        elif self.__is_entity_exist_and_displayed(fail_xpath1):
            fail_text_box = self._driver.find_element(By.XPATH, fail_xpath1)
            self._LOG.error(fail_text_box.text)
            return False, fail_text_box.text

    @PageService()
    def upgrade_client_software(self, client):
        """
                Method to submit software upgrade for a client from UI
                Args:
                    client      (object)    :   client object
        """
        self._adminconsole.wait_for_completion()
        self.navigator = self._adminconsole.navigator
        self.navigator.navigate_to_servers()
        servers = Servers(self._adminconsole)
        self.wizard.table.reload_data()
        job = servers.action_update_software(client_name=client)
        return job

    def wait_for_job_completion(self, jobid, commcell):
        """ Waits for completion of job and gets the object once job completes
        Args:
            jobid       (str): Jobid
            commcell    (object): Object of commcell
        """
        commcell.refresh()
        job_obj = commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(f"Failed to run job:{jobid} with error: {job_obj.delay_reason}")
        self._LOG.info("Successfully finished %s job", jobid)


class SAPHanaMetallic(RDatabasesMetallic):
    """Provides helepr function for configuring SAP HANA database from Hub"""

    def __init__(self, admin_console):
        self._adminconsole = admin_console
        super().__init__(admin_console, DatabaseTypes.sap_hana)

    @PageService()
    def select_hana_backup_content(self):
        """Proceeds from the backup_content page for Oracle Metallic New Configuration"""
        self._adminconsole.click_button(value="Next")

    @PageService()
    def proceed_from_summary_page(self):
        """Proceeds from the summary page after configuration is done"""
        self._adminconsole.click_button(value="Finish")

    @WebAction()
    def __get_text_box_text(self, xpath):
        """Gets the success/failure textbox text
        Args:
            xpath (str):    xpath for success/failure text box
        """
        text_box = self._driver.find_element(By.XPATH, xpath)
        return text_box.text

    @PageService()
    def __get_text_info_after_spinner(self):
        """Gets the text message that comes up after spinner element has completed"""
        success_xpath = "//div[contains(@class, \"ng-star-inserted\") and contains(text(), 'successful')]"
        fail_xpath = "//div[@class = \"ng-star-inserted\"]"
        if self._adminconsole.check_if_entity_exists("xpath", success_xpath):
            success_text = self.__get_text_box_text(success_xpath)
            self._LOG.info(success_text)
            return True, success_text
        fail_text = self.__get_text_box_text(fail_xpath)
        self._LOG.error(fail_text)
        return False, fail_text

    @PageService()
    def add_instance(self, system_name, sid, database_user=None, database_password=None, store_key=None):
        """ Method to add sap hana app
        Args:
            system_name         (str):  Server Name
            sid                 (str):  SID name of HANA database
            database_user       (str):  Database username       (optional)
            database_password   (str):  Database user password  (optional)
            store_key           (str):  Store Key               (optional)

        """
        self._adminconsole.fill_form_by_id('clientName', system_name)
        self._adminconsole.fill_form_by_id('databaseName', sid)
        if database_user and database_password:
            self._adminconsole.fill_form_by_id('dbUsername', database_user)
            self._adminconsole.fill_form_by_id('dbPassword', database_password)
        elif store_key:
            self._adminconsole.select_radio(id='DBUser')
            self._adminconsole.fill_form_by_id('hdbStorekey', store_key)
        self._adminconsole.submit_form()

    @PageService()
    def configure_application_access(self, commcell, install_inputs):
        """Downloads and installs the Metallic software on the server and checks valid installation
        Args:
            commcell        (object):   Object of Commcell
            install_inputs  (dict)   : List of Dictionaries input that goes for configuring DB package
                                            install. Number of dictionaries should be equal to number of machines

                                          dictionary passed should be:
                                          {
                                              "remote_clientname"     : "<FQDN of the machine>"
                                              "remote_username"       : "<username to connect to
                                                                         remote machine>",
                                              "remote_userpassword"   : "<password to connect to
                                                                         remote machine>",
                                              "os_type"               :  "<OS type of remote client>"
                                              "username"              : "<Username of CS to
                                                                        authenticate client>"
                                              "password"              : "<Password  of CS
                                                                        authenticate client>"
                                              "authcode" (optional)   : "<Authcode to
                                                                        authenticate client>"
                                          }
        """
        pkg_file_path = self.do_pkg_download()
        self.do_pkg_install(commcell, pkg_file_path, install_inputs)

        self._adminconsole.fill_form_by_id("hostsNames", install_inputs['remote_clientname'])
        self._adminconsole.click_button('Add')
        self.utils_helper.wait_for_spinner()
        status, msg = self.__get_text_info_after_spinner()
        if not status:
            raise CVWebAutomationException(f"Failed to validate install with error : {msg}")
        self._LOG.info("*" * 10 + " Install successfully validated " + "*" * 10)

    @PageService()
    def configure_hana_database(self, cloud_storage_inputs=None, use_existing_plan=False, backup_to_cloud=True,
                                plan_inputs=None, select_storage_region=False):
        """Configures and sets up database from Metallic Hub

                Args:

                    cloud_storage_inputs       (dict)   : Dictionary input that goes for configuring cloud
                                                            storage.

                                                            dictionary passed should be:
                                                            {
                                                            "StorageAccount": "<storage account>",
                                                            "CloudProvider" : "<cloud storage provider>",
                                                            "region"        : "<storage region>"
                                                            }

                    use_existing_plan          (bool)   : If True uses an existing plan, else configures a
                                                            new one with the provided inputs
                    backup_to_cloud            (bool)   : If true, backs up via cloud, else uses backup gateway
                        default value                   : True

                    plan_inputs                (dict)   : Dictionary input that goes for plan
                                                            If use_existing_plan is true,
                                                            dictionary passed should be:
                                                            {
                                                            "PlanName": "<Existing plan name>"
                                                            }
                                                            If use_existing_plan is false,
                                                            dictionary passed should be:
                                                            {
                                                            "RetentionPeriod": "<Retention period>"
                                                            }
                    select_storage_region       (bool)  : If true, selects storage region first and proceeds
                                                            to next step - storage creation
                        default value                   : True
                Returns:
                    str     :       Name of the new plan created if use_existing_plan is false
        """
        if backup_to_cloud:
            self.select_backup_deploy()
        if select_storage_region:
            self.rdropdown.select_drop_down_values(drop_down_id="storageRegion",
                                                   values=[cloud_storage_inputs['region']],
                                                   partial_selection=True)
            self._adminconsole.click_button(value="Next")
        self.select_cloud_storage(cloud_storage_inputs["StorageAccount"],
                                  cloud_storage_inputs["CloudProvider"],
                                  cloud_storage_inputs["Region"])
        if use_existing_plan:
            try:
                self.wizard.select_plan(plan_name=plan_inputs["PlanName"])
                self._adminconsole.click_button(value="Next")
                plan_name = plan_inputs["PlanName"]
            except NoSuchElementException:
                raise CVWebAutomationException(f"No such element exception has been raised, "
                                               f"Please check if the provided plan name {plan_inputs['PlanName']} exists")
        else:
            plan_name = self.create_new_plan(retention_period=plan_inputs["RetentionPeriod"])
            self._adminconsole.click_button(value="Next")
        return plan_name


class OracleMetallic(RDatabasesMetallic):
    """Provides helper function for configuring Oracle database from Hub"""

    def __init__(self, admin_console):
        self._adminconsole = admin_console
        super(OracleMetallic, self).__init__(admin_console, DatabaseTypes.oracle)

    @PageService()
    def select_oracle_backup_content(self):
        """Proceeds from the backup_content page for Oracle Metallic New Configuration"""
        self._adminconsole.click_button(value="Next")

    @PageService()
    def proceed_from_summary_page(self):
        """Proceeds from the summary page after configuration is done"""
        self._adminconsole.click_button(value="Finish")

    @PageService()
    def configure_oracle_database(self, cloud_storage_inputs=None, use_existing_plan=False, backup_to_cloud=True,
                                  plan_inputs=None, select_storage_region=False):
        """Configures and sets up database from Metallic Hub

                Args:

                    cloud_storage_inputs       (dict)   : Dictionary input that goes for configuring cloud
                                                            storage.

                                                            dictionary passed should be:
                                                            {
                                                            "StorageAccount": "<storage account>",
                                                            "CloudProvider" : "<cloud storage provider>",
                                                            "region"        : "<storage region>"
                                                            }

                    use_existing_plan          (bool)   : If True uses an existing plan, else configures a
                                                            new one with the provided inputs
                    backup_to_cloud            (bool)   : If true, backs up via cloud, else uses backup gateway
                        default value                   : True

                    plan_inputs                (dict)   : Dictionary input that goes for plan
                                                            If use_existing_plan is true,
                                                            dictionary passed should be:
                                                            {
                                                            "PlanName": "<Existing plan name>"
                                                            }
                                                            If use_existing_plan is false,
                                                            dictionary passed should be:
                                                            {
                                                            "RetentionPeriod": "<Retention period>"
                                                            }
                    select_storage_region       (bool)  : If true, selects storage region first and proceeds
                                                            to next step - storage creation
                        default value                   : False
                Returns:
                    str     :       Name of the new plan created if use_existing_plan is false
        """
        if backup_to_cloud:
            self.select_backup_deploy()
        if select_storage_region:
            self.rdropdown.select_drop_down_values(drop_down_id="storageRegion",
                                                   values=[cloud_storage_inputs['region']],
                                                   partial_selection=True)
            self._adminconsole.click_button(value="Next")
        self.select_cloud_storage(cloud_storage_inputs["cloud_vendor"],
                                  cloud_storage_inputs["storage_provider"],
                                  cloud_storage_inputs["region"])
        if use_existing_plan:
            try:
                self.wizard.select_plan(plan_name=plan_inputs["PlanName"])
                self._adminconsole.click_button(value="Next")
                plan_name = plan_inputs["PlanName"]
            except NoSuchElementException:
                raise CVWebAutomationException(f"No such element exception has been raised, "
                                               f"Please check if the provided plan name {plan_inputs['PlanName']} exists")
        else:
            plan_name = self.create_new_plan(retention_period=plan_inputs["RetentionPeriod"])
            self._adminconsole.wait_for_completion()
            self._adminconsole.click_button(value="Next")
        return plan_name


class OciMetallic(RDatabasesMetallic):
    """provides helper function for configuring oci dbcs instances from the hub"""

    def __init__(self, admin_console):
        self.oci_helper = OCIHelper()
        self.api_key_data = None
        self.iam_stack_id = None
        self.gateway_stack_id = None
        self.backup_gateway = None
        super().__init__(admin_console, DatabaseTypes.oracle)

    @PageService()
    def configure(self, install_inputs=None):
        """
        Configures OCI DBCS from metallic hub
        Args:
            install_inputs (dict)
                                dictionary passed should be:
                                                {
                                                  "remote_clientname"   (str)        : "Hostname or fqdn
                                                                                        of the machine"
                                                  "remote_username"     (str)        : "username to connect to
                                                                                        remote machine,
                                                  "remote_userpassword" (str)        : "password to connect
                                                                                        to remote machine",
                                                  "ssh_key_path"        (str)        : "private key for
                                                                                        the remote machine",
                                                }
        """
        self.oci_helper.set_db_state(action="start")
        self.select_cloud_vm_details(vendor='Oracle Cloud Infrastructure',
                                     app_type=DatabaseTypes.oracle,
                                     oci_service_type="Database Cloud Service (single node)")
        self.iam_stack_id = self.create_oci_iam_role()
        suffix = datetime.now().strftime("%d:%H:%M:%S")
        self.create_credential(credential_name=f"Oci_cred_automation_iam_{suffix}")
        self.oci_select_region()
        self.gateway_stack_id, self.backup_gateway = self.add_backup_gateway()
        self.configure_oci_storage_plan()
        if "ssh_key_path" in install_inputs:
            self.do_push_install(install_inputs=install_inputs)
        else:
            pkg_file_path = self.do_pkg_download(platform="Linux")
            self.do_pkg_install(pkg_file_path=pkg_file_path, install_inputs=install_inputs)
        self.select_backup_content()
        self.proceed_from_summary_page()

    @PageService()
    def create_oci_iam_role(self):
        """
        Method creates the iam role for the oci
        """
        self.wizard.click_next()
        self._LOG.info('Creating IAM role')
        self.wizard.click_button(name="Copy link")
        zipurl = self._driver.find_element_by_xpath(f"//a[contains(text(),"
                                                    f"'Launch Oracle Cloud Stack Template')]").get_attribute("href")
        zipurl = zipurl.split('=')[1]
        b64encodedstr = base64.b64encode(requests.get(zipurl).content).decode('ascii')
        variables = {
            "tenancy_ocid": _CONFIG_DATA.OCI.oci_tenancy_id,
            "region": _CONFIG_DATA.OCI.oci_region,
            "user_email": "metallicociauto@metallic.io",
            "policy_compartment_ocid": _CONFIG_DATA.OCI.oci_compartment_id
        }
        stack_creation_data = {
            "encoded_file": b64encodedstr,
            "display_name": "automation_iam_role",
            "description": "Role with min permissions required",
            "compartment_id": _CONFIG_DATA.OCI.oci_compartment_id,
            "variables": variables

        }
        stack_info = self.oci_helper.create_stack(stack_creation_data=stack_creation_data)
        apply_job, stack_resources = self.oci_helper.run_apply_job_for_stack(stack_id=stack_info.id)
        self._LOG.info("Iam role is created")
        job_output = self.oci_helper.get_stack_apply_job_output(apply_job.id)
        username_details = job_output['outputs']['metallic_user']['value']
        username_details = self.oci_helper.oci_user_details(username=username_details)
        self.api_key_data = self.oci_helper.upload_api_key(username_details,
                                                           public_key_path=_CONFIG_DATA.OCI.iam_public_key_path)
        self._LOG.info("Uploaded public key for api authentication")
        return stack_info.id

    @PageService()
    def create_credential(self, credential_name="oci_auto_cred"):
        """ Method creates new credential for the oci onboarding

            Args:

                    credential_name     (str)   :-  Creates credential with given credential_name
        """
        self._LOG.info("Creating oci credential")
        self.wizard.click_icon_button_by_title(title="Create new")
        dialog = RModalDialog(admin_console=self._adminconsole, title='Add credential')
        dialog.fill_text_in_field(element_id="name", text=credential_name)
        dialog.fill_text_in_field(element_id="tenancyOCID", text=_CONFIG_DATA.OCI.oci_tenancy_id)
        dialog.fill_text_in_field(element_id="userOCID", text=self.api_key_data.user_id)
        dialog.fill_text_in_field(element_id="fingerprint", text=self.api_key_data.fingerprint)
        self._driver.find_element_by_xpath("//input[@name='fileInput']").send_keys(
            _CONFIG_DATA.OCI.iam_private_key_path)
        if _CONFIG_DATA.OCI.oci_private_key_password:
            dialog.fill_text_in_field(element_id="privateKeysPassword", text=_CONFIG_DATA.OCI.oci_private_key_password)
        dialog.fill_text_in_field(element_id="description", text="Automation created credential")
        dialog.click_submit()
        self.wizard.click_next()
        self._LOG.info("Created credential successfully")

    @PageService()
    def configure_oci_storage(self):
        """Creates a new cloud oci cloud storage
        """
        self.wizard.click_icon_button_by_title(title="Add")
        self._adminconsole.wait_for_completion()
        dialog = RModalDialog(admin_console=self._adminconsole, title="Add cloud storage")
        dialog.select_dropdown_values(drop_down_id="cloudType", values=["Oracle Cloud Infrastructure Object Storage"])
        dialog.fill_text_in_field(element_id="configureCloudLibrary.CompartmentName",
                                  text=_CONFIG_DATA.OCI.storage_compartment_name)
        dialog.fill_text_in_field(element_id="mountPath", text=_CONFIG_DATA.OCI.storage_bucket)
        dialog.click_submit()
        self.wizard.select_radio_button(id="secondaryCopyToggle")
        self.wizard.click_add_icon(index=1)
        dialog.select_dropdown_values(drop_down_id="cloudType", values=["Air Gap Protect"])
        dialog.select_dropdown_values(drop_down_id="storageClass", values=["Standard"])
        dialog.click_button_on_dialog(text="Start trial")
        self._adminconsole.wait_for_completion(2000)
        trial_dialog = RModalDialog(admin_console=self._adminconsole, title="Successfully created a trial subscription")
        trial_dialog.click_button_on_dialog('Close')
        dialog.click_submit()
        self._adminconsole.wait_for_completion(2000)
        self.wizard.click_next()

    @PageService()
    def configure_oci_storage_plan(self):
        """Creates a new cloud oci cloud storage and plan

                    Returns
                                     plan_name  (str)   : returns created plan name
                """
        self.configure_oci_storage()
        plan_name = self.create_new_plan(retention_period="1 Month")
        self.wizard.click_next()
        return plan_name

    def _get_gateway_stackinfo(self):
        """method returns the zipurl and the authcode from the copied url in clipboard
        Returns:
                    ziprul (str)      :   zipurl of the stack's terraform config

                    authcode(str)     :   Authcode for give tenancy

        """
        self._LOG.info("Extracting zipurl and authcode from url")
        url = self._driver.find_element_by_xpath(f"//a[contains(text(),"
                                                 f"'Oracle Cloud Resource Stack')]").get_attribute("href")
        url = urllib.parse.unquote(url)
        zipurl = url.split("&")[1]
        zipurl = zipurl.split("=")[1]
        zipvariables = url.split("&")[2]
        authcode = zipvariables.split("+")[1]
        authcode = authcode[:-1]
        authcode = authcode.replace('"', '')
        self._LOG.info(f"zipurl is {zipurl} and authcode is {authcode}")
        return zipurl, authcode

    @PageService()
    def oci_select_region(self, region="US East (Ashburn)"):
        """Selects the region for the oci
           Args:
                    region   (str)    :   selects the region for the oci
        """
        self.wizard.select_drop_down_values(id="storageRegion", values=[region])
        self.wizard.click_button(name="Next")

    @PageService()
    def add_backup_gateway(self, platform="Linux"):
        """Creates oci stack and adds a new oci backup gateway
           Args:
                     platform      (str)    : gateway platform type
           Returns:
                     stack_info.id (int)    : returns stack id
        """
        self.wizard.click_icon_button_by_title(title="Add")
        gateway_dialog = RModalDialog(admin_console=self._adminconsole, title="Backup gateway")
        gateway_dialog.select_dropdown_values(drop_down_id="platform", values=[platform])
        time.sleep(90)
        gateway_dialog.click_button_on_dialog(text="Generate link")
        time.sleep(90)
        zipurl, authcode = self._get_gateway_stackinfo()
        b64encodedstr = base64.b64encode(requests.get(zipurl).content).decode('ascii')
        stack_creation_data = {
            "encoded_file": b64encodedstr,
            "display_name": _CONFIG_DATA.OCI.stack.display_name,
            "description": _CONFIG_DATA.OCI.stack.description,
            "compartment_id": _CONFIG_DATA.OCI.stack.compartment_id,
            "variables": {
                "authcode": authcode,
                "availability_domain": _CONFIG_DATA.OCI.stack.availability_domain,
                "data_size": "25TB",
                "region": _CONFIG_DATA.OCI.oci_region,
                "tenancy_ocid": _CONFIG_DATA.OCI.oci_tenancy_id,
                "compartment_ocid": _CONFIG_DATA.OCI.stack.compartment_id,
                "instance_compartment_ocid": _CONFIG_DATA.OCI.stack.compartment_id,
                "nsg_compartment_ocid": _CONFIG_DATA.OCI.stack.compartment_id,
                "vcn_ocid": _CONFIG_DATA.OCI.stack.vcn_ocid,
                "subnet_ocid": _CONFIG_DATA.OCI.stack.subnet_ocid,
                "ssh_public_key": _CONFIG_DATA.OCI.stack.ssh_public_key
            }
        }
        self._LOG.info("Creating stack and running apply job.")
        stack_info = self.oci_helper.create_stack(stack_creation_data)
        apply_job_obj, stack_resources_info = self.oci_helper.run_apply_job_for_stack(stack_info.id)
        gateway_name = ""
        for resource in stack_resources_info.items:
            if "instance" in resource.resource_id:
                gateway_name = resource.resource_name
        gateway_name = "BackupGateway-" + gateway_name
        self._LOG.info(f"{gateway_name} is created.")
        gateway_dialog.click_button_on_dialog(text="OK")
        time_left = 480
        while time_left:
            self._LOG.info("Waiting for the registration to complete")
            self.wizard.click_icon_button_by_title(title="Refresh")
            time.sleep(30)
            time_left -= 30
            xpath = f"//div[@id='accessNodeDropdown']//ancestor::div[contains(@aria-disabled, 'true')]"
            if not self._adminconsole.is_element_present(xpath):

                break
        self.wizard.click_next()
        return stack_info.id, gateway_name


class CloudDatabases(RDatabasesMetallic):
    """Class to set common options while creating cloud DB instances with react metallic pages"""

    def __init__(self, admin_console, app_type=DatabaseTypes.azure, s3_helper=None):
        """ Initialize the class

        Args:
            admin_console: instance of AdminConsoleBase
            app_type: type of Application
        """
        self._admin_console = admin_console
        self.page_container = PageContainer(admin_console)
        self.s3_helper = s3_helper
        super().__init__(admin_console, app_type)
        if app_type == DatabaseTypes.azure:
            self.azure_rg = AzureResourceGroup()
            self.azure_deployment = AzureCustomDeployment()
        self.log = logger.get_log()

    @property
    @abstractmethod
    def cloud_db_engine(self):
        """Override this method and implement it as a variable
                whose value needs to be set for Cloud DB engine"""
        raise NotImplementedError

    @property
    @abstractmethod
    def database_type(self):
        """Override this method and implement it as a variable
                whose value needs to be set for Cloud DB engine"""
        raise NotImplementedError

    @PageService()
    def _configure_instance(self, **kwargs):
        """
        Method to configure instance
        Keyword Args:
            instance_name       (str):  Name of the instance
            database_user       (str):  Database username
            database_password   (str):  Database password
            maintenance_db      (str):  Maintenance database name
                default: postgres
            endpoint            (str):  Database instance endpoint
                default: None
            ssl                 (bool): True if SSL is enabled
                default: False
            ssl_ca              (str):  Path to the CA file on bakup gateway
            ad_auth             (bool): False if ad_auth has to be disabled for DB instance
        """
        self.wizard.select_drop_down_values(
            id='cloudInstanceDropdown', values=[kwargs.get("instance_name")])
        self.wizard.fill_text_in_field(id='databaseUser', text=kwargs.get("database_user"))
        if kwargs.get("ad_auth", False):
            self.wizard.enable_toggle(label=self._adminconsole.props['label.useADAuthentication'])
        else:
            self.wizard.fill_text_in_field(id='password', text=kwargs.get("database_password"))
            self.wizard.fill_text_in_field(id='confirmPassword', text=kwargs.get("database_password"))
        if kwargs.get("maintenance_db", None):
            self.wizard.fill_text_in_field(id='MaintainenceDB', text=kwargs.get("maintenance_db", "postgres"))
        if kwargs.get("endpoint", None):
            self.wizard.fill_text_in_field(id='endPoint', text=kwargs.get("endpoint", None))
        if kwargs.get("ssl", None):
            self.wizard.enable_toggle(label=self._adminconsole.props['label.useSSLOption'])
            if kwargs.get("ssl_ca", None):
                self.wizard.fill_text_in_field(id="sslCa", text=kwargs.get("ssl_ca", None))
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def _set_database_engine(self):
        """Selects the cloud database engine"""
        self.wizard.select_radio_button(self.cloud_db_engine)
        self.wizard.click_next()

    def _copy_ssl_file_to_access_node(self, backupgateway, commcell, cert_name):
        """Method to copy ssl_ca to access node
                Args:
                        backupgateway   (str)       : backupgateway name
                        commcell        (object)    : object of commcell
                        cert_name       (str)       : ssl_ca file name
        """
        destination_object = commcell.clients.get(backupgateway)
        destination_machine_object = Machine(destination_object)
        cv_home_path = destination_object.install_directory
        self.remote_path = destination_machine_object.join_path(cv_home_path, "db_ssl")
        destination_machine_object.create_directory(self.remote_path, force_create=True)
        source_blob = _CONFIG_DATA.MySQL.PublicSSLPathToDownload
        self.remote_path += cert_name
        command = f"Invoke-WebRequest {source_blob} -outfile {self.remote_path}"
        destination_machine_object.execute_command(command)

    @PageService()
    def _set_database_server_type(self):
        """Selects database server type for RDS(Export) backups"""
        self.wizard.select_radio_button(self.database_type)
        self.wizard.click_next()

    @PageService()
    def _select_region(self, region):
        """Selects the region

            Args:
                region(str) : region to get select human-readable
        """
        if self._admin_console.check_if_entity_exists("id", "storageRegion"):
            self.wizard.select_drop_down_values(
                id='storageRegion', values=[region], partial_selection=True)
        else:
            self.wizard.select_drop_down_values(
                id='regionsDropdown', values=[region], partial_selection=True)
        self.wizard.click_next()

    @PageService()
    def _select_backup_gateway(self, backup_gateway_name, partial_selection=True):
        """Selects the backup gateway
            Args:
                backup_gateway_name   (str) : name of the backup gateway

                partial_selection     (bool) : True if partial selection is required
        """
        self.wizard.click_refresh_icon()
        self._admin_console.wait_for_completion()
        if self._admin_console.check_if_entity_exists("id", "accessNodeDropdown"):
            self.wizard.select_drop_down_values(
                id='accessNodeDropdown', values=[backup_gateway_name], partial_selection=partial_selection)
        else:
            self.wizard.select_drop_down_values(
                id='backupGatewayDropdown', values=[backup_gateway_name], partial_selection=partial_selection)
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def __wait_for_backup_gateway_template(self, wait_time=150):
        """Waits for launch cloudformation stack link to appear"""
        curr_time = 0
        path = "//a[contains(text(),'CloudFormation')]"
        while not self._admin_console.check_if_entity_exists("xpath", path) and curr_time < wait_time:
            time.sleep(3)
            self._admin_console.log.info("waiting for Launch Stack URL.")
            curr_time += 3
        if curr_time >= wait_time:
            raise CVWebAutomationException("Took more than expected time for loading launch cloud formation url")

    @PageService()
    def _get_backup_gateway_stack_url(self):
        """gets the Backup Gateway stack deployment URL"""
        self.dialog.click_button_on_dialog(text="Generate link")
        self.__wait_for_backup_gateway_template()
        path = "//a[contains(text(),'CloudFormation')]"
        return self._driver.find_element(By.XPATH, path).get_attribute('href')

    @PageService()
    def _create_aws_backup_gateway(self, **kwargs):
        """
        Creates backup gateway in AWS
            Args:
                gateway_os_type     (str)           :  "Linux" or "Windows"
                stack_params        (list of dict)  :   keypair, vpcId, SubnetId
                stack_name          (str)           :   name of the backgateway
                region              (str)           :   name of the region where backup gateway should get created
                title               (str)           :   title of ModalDialog
            Example
                gateway_os_type = Linux,
                stack_params =[
                    {
                        "ParameterKey": "KeyName",
                        "ParameterValue": "sampath-key"
                    },
                    {
                        "ParameterKey": "VpcId",
                        "ParameterValue": "vpc-12345"
                    },
                    {
                        "ParameterKey": "SubnetId",
                        "ParameterValue": "subnet-12345"
                    }
                ]
        """
        self.wizard.click_add_icon()
        title = kwargs.get("title", "Add a new backup gateway")
        self.dialog = RModalDialog(admin_console=self._admin_console, title=title)
        self.dialog.select_dropdown_values(drop_down_id='platform', values=[kwargs.get('gateway_os_type')])
        stack_url = self._get_backup_gateway_stack_url()
        gateway_stack = self.s3_helper.create_stack(
            stack_name=kwargs.get('stack_name'),
            stack_url=stack_url, params=kwargs.get('stack_params'))
        self._LOG.info("Please wait stack to create")
        time.sleep(80)
        self.dialog.click_button_on_dialog(text='OK')
        self._admin_console.wait_for_completion()
        self.log.info("Waiting for backup gateway to load")
        self.wizard.click_refresh_icon()
        if kwargs.get('gateway_os_type') == 'Windows':
            backup_gateway_name = f"BackupGateway-{gateway_stack.Resource('WindowsInstance').physical_resource_id}"
        else:
            backup_gateway_name = f"BackupGateway-{gateway_stack.Resource('LinuxInstance').physical_resource_id}"
        return backup_gateway_name

    def _create_or_reuse_azure_backup_gateway(self, location, resource_group):
        """ Method to create or reuse the backup gateway
            Args:
                location        (str)   : location of the backup gateway
                resource_group  (str)   : name of the resource group to be used
            Returns:
                backup_gateway_name (str) : name of the backup gateway
        """
        resource_group_data_time = datetime.strptime(resource_group, f"automation-%Y-%d-%B-%H-%M")
        # check if resource group exists and is created within 24 hours
        if (self.azure_rg.check_if_resource_group_exists(resource_group)
                and datetime.now() - resource_group_data_time < timedelta(hours=24)):
            self.log.info("Using Existing Backup Gateway")
            deployment_name = f"deployment-{resource_group_data_time.strftime('%Y-%d-%B-%H-%M')}"
            backup_gateway_name = self.azure_deployment.get_backup_gateway_name(rg_name=resource_group,
                                                                                deployment_name=deployment_name)
            return backup_gateway_name
        # create new backup gateway
        return self._create_azure_backup_gateway(location, resource_group)

    def _create_azure_backup_gateway(self, location, resource_group):
        """Method to create new backup gateway"""
        self.wizard.click_add_icon()
        self._admin_console.wait_for_completion()
        authcode = self._get_authcode()

        # create RG -> check if exists, delete and recreate
        if self.azure_rg.check_if_resource_group_exists(resource_group):
            self.log.info("Found Resource group- deleting it")
            self.azure_rg.delete_resource_group(rg_name=resource_group)
            self.log.info("Resource group is deleted successfully")

        self.log.info("Creating a new Resource group")
        rg_params = {'location': location}
        self.azure_rg.create_resource_group(
            rg_name=resource_group,
            rg_params=rg_params
        )
        self.log.info("Created Resource group")

        # deploy the template
        self.log.info("Beginning the deployment... \n")
        resource_group_data_time = datetime.strptime(resource_group, f"automation-%Y-%d-%B-%H-%M")
        deployment_name = f"deployment-{resource_group_data_time.strftime('%Y-%d-%B-%H-%M')}"
        self.azure_deployment.deploy(rg_name=resource_group, authcode=authcode, deployment_name=deployment_name)
        self.log.info("Deployment successful!!")

        self.rmodal.click_close()

        backup_gateway_name = self.azure_deployment.get_backup_gateway_name(rg_name=resource_group,
                                                                            deployment_name=deployment_name)
        return backup_gateway_name

    @PageService()
    def _get_authcode(self):
        """ Method to return authcode """
        xpath = "//div//p[contains(text(), 'auth code')]/following-sibling::b"
        auth_code = self._admin_console.driver.find_element(By.XPATH, xpath).text
        self._admin_console.wait_for_completion()
        return auth_code

    @PageService()
    def _set_cloud_account(self, cloud_account):
        """
        Sets the cloud account
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                    configuring instance
        """
        self.wizard.select_drop_down_values(
            id='cloudAccount', values=[cloud_account])
        self.wizard.click_next()

    @PageService()
    def click_add_server(self):
        """Method to click on add server and select the db engine"""
        self.page_container.access_page_action('Add server')
        self._admin_console.wait_for_completion()
        self._set_database_engine()

    @WebAction()
    def click_add_cloud_db(self):
        """Click on Cloud DB under add instance in Instances Page"""
        self.page_container.access_page_action('Add instance')
        self.page_container.access_page_action('Cloud database service')
        self._admin_console.wait_for_completion()


class RAWSMetallic(CloudDatabases):
    """Class that provide helper functions for the AWS in Metallic"""

    def __init__(self, admin_console, app_type=DatabaseTypes.AWS, s3_helper=None, aws_helper=None):
        """Initialize the class

                   Args:
                   admin_console: instance of AdminConsoleBase
                   aws_helper: EC2 helper object
                        default: None
                   app_type:    type of Application
                        default: Databasetypes.AWS
                   s3_helper: instance of S3MetallicHelper
                        default: None
               """
        self.s3_helper = s3_helper
        self.aws_helper = aws_helper
        self.gateway_instance_name = None
        self._rcontentbrowse = RContentBrowse(admin_console)
        super().__init__(admin_console, app_type=app_type, s3_helper=self.s3_helper)

    @WebAction()
    def _get_iam_stack_url(self):
        """gets the IAM stack deployment URL"""
        path = "//a[contains(text(),'Launch the CloudFormation Stack')]"
        return self._driver.find_element(By.XPATH, path).get_attribute('href')

    @WebAction()
    def _confirm_iam_stack_created(self):
        """This select the checkbox creating MetallicRole stack"""
        self._admin_console.click_by_xpath("//span[contains(text(),'I confirm that the IAM')]")

    @PageService()
    def __select_backup_method(self, backup_method_id):
        """
        Selecting the backup method
        Args:
            backup_method_id              (str):  ID of the backup method radio button

        """
        self.log.info("Backup method selection")
        self.wizard.select_radio_button(id=backup_method_id)

    @PageService()
    def create_gateway(self, **kwargs):
        """
        This function will create a backup gateway and add in bound rule
        kwargs:
            stack_name          (str)   :name of Gateway in aws
            stack_params        (list of dict):keypair, vpcId, SubnetId
            region              (str)   :Name of the region where backup gateway should get created
            gateway_os_type     (str)   :Type of the gateway OS
            is_rds_export       (bool)  :Checks if backup method is RDS (Export)

            eg:
                stack_params =[
                    {
                        "ParameterKey": "KeyName",
                        "ParameterValue": "sampath-key"
                    },
                    {
                        "ParameterKey": "VpcId",
                        "ParameterValue": "vpc-12345"
                    },
                    {
                        "ParameterKey": "SubnetId",
                        "ParameterValue": "subnet-12345"
                    }
                ]
        """
        self._set_database_engine()
        if kwargs.get("is_rds_export"):
            self.wizard.click_next()
            self._set_database_server_type()
        else:
            self.__select_backup_method(backup_method_id="2")
            self.wizard.click_next()
        self._admin_console.wait_for_completion()
        self._select_authentication("IAM Role")
        reg = self.aws_helper.convert_region_codes_to_names(region_code=kwargs.get("region"))
        self._select_region(reg)
        self.gateway_instance_name = self._create_aws_backup_gateway(**kwargs, title="Add a new backup gateway")
        return self.gateway_instance_name

    @PageService()
    def _create_secondary_storage(self, storage_type="MRR", storage_provider="Azure"):
        """
            This function is to create the secondary storage

            Args:
                storage_type(str)   : Type of storage using
                    ("MRR", "S3")
                storage_provider(str):  Name of storage provider
                    ("Azure", "OCI")
        """
        self.dialog = RModalDialog(admin_console=self._admin_console)
        self.wizard.select_radio_button(id="secondaryCopyToggle")
        self.wizard.click_add_icon(index=1)
        storage_dict = {
            "MRR": "Metallic Recovery Reserve",
            "S3": "Amazon S3",
            "Azure": "Azure Blob Storage",
            "OCI": "OCI Object Storage"
        }
        self.dialog.select_dropdown_values(drop_down_id="cloudType", values=[storage_dict.get(storage_type, "")])
        if "mrr" in storage_type.lower():
            self.dialog.select_dropdown_values(drop_down_id="offering", values=[storage_dict.get(storage_provider, "")])
            if "azure" in storage_provider.lower():
                self.dialog.select_dropdown_values(drop_down_id="storageClass", values=["Hot tier"])
                self.dialog.select_dropdown_values(drop_down_id="region", values=["East US 2"])
                self.dialog.click_button_on_dialog(text="Start trial")
                self._adminconsole.wait_for_completion()
                trial_dialog = RModalDialog(admin_console=self._adminconsole,
                                            title="Successfully created a trial subscription")
                trial_dialog.click_button_on_dialog('Close')
                self.dialog.click_submit()

    @PageService()
    def configure(self, **kwargs):
        """
        This function is to configure the steps of creating dynamo db in metallic page

        Args:
            kwargs:
                region (str)    : region where the AWS db is hosted
                stack_name          (str)   :name of Gateway in aws
                stack_params        (list of dict):keypair, vpcId, SubnetId
                byos_storage_name       (str)   : Name of the s3 metallic storage name
                byos_bucket_name        (str)   : Name of s3 bucket name in AWS
                cloud_account_name  (str)       : Name of the cloud Account to access DB instance
                content       (list of strings) : content to be selected
                plan_name           (str)       :   name of the plan
                secondary_storage_name    (str) :   Type of Secondary storage like MRR or S3
                secondary_storage_provider (str):   Name of the storage provider to MRR (Azure or OCI)
                is_dynamo           (bool)      : Check if database service selected is dynamo db
                is_rds_export          (bool)   : Check if database service selected is rds Export

            Example:
                stack_params =[
                    {
                        "ParameterKey": "KeyName",
                        "ParameterValue": "sampath-key"
                    },
                    {
                        "ParameterKey": "VpcId",
                        "ParameterValue": "vpc-12345"
                    },
                    {
                        "ParameterKey": "SubnetId",
                        "ParameterValue": "subnet-12345"
                    }
                ]
        """
        self.wizard.select_radio_button(label="Amazon Web Services")
        self.wizard.click_next()
        self.select_trial_subscription()
        self._set_database_engine()
        if kwargs.get("is_rds_export"):
            self.wizard.click_next()
            self._set_database_server_type()
        else:
            self.__select_backup_method(backup_method_id="2")
            self.wizard.click_next()
        self._admin_console.wait_for_completion()
        self._select_authentication("IAM Role")
        reg = self.aws_helper.convert_region_codes_to_names(region_code=kwargs.get("region"))
        self._select_region(reg)
        self._select_backup_gateway(self.gateway_instance_name)
        self._create_byos_s3(kwargs.get("byos_storage_name"), "IAM Role", kwargs.get("byos_bucket_name"), standard=True)
        if kwargs.get("secondary_storage_name", "") != "":
            self._create_secondary_storage(storage_type=kwargs.get("secondary_storage_name", ""),
                                           storage_provider=kwargs.get("secondary_storage_provider", ""))
        self.wizard.click_next()
        self._create_plan(kwargs.get("plan_name"))
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        self._create_cloud_account(kwargs.get("cloud_account_name"))
        self._select_cloud_account(kwargs.get("cloud_account_name"))
        self.wizard.click_next()
        if kwargs.get("is_dynamo"):
            self.wizard.click_next()
        if kwargs.get("is_rds_export"):
            self._configure_instance(**kwargs)
        else:
            self.select_backup_content_aws(kwargs.get("content"))
        self._admin_console.wait_for_completion()
        self.proceed_from_summary_page()
        self._admin_console.wait_for_completion()

    def _select_authentication(self, auth_type):
        """Select IAM Role as the Authentication method
            Args:
                auth_type(str) : Type of authentication want to select
                eg:
                    "IAM ROLE"
                    "Access and Secret Key"
                    "STS assume role with IAM policy"
        """
        self.wizard.select_drop_down_values(id='authenticationMethod', values=[auth_type])
        iam_stack_url = self._get_iam_stack_url()
        self.s3_helper.create_stack(stack_name='MetallicRole', stack_url=iam_stack_url,
                                    capabilities=['CAPABILITY_NAMED_IAM'])
        self._confirm_iam_stack_created()
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def _create_byos_s3(self, storage_name, auth_type, byos_bucket_name, standard=True):
        """Method to create S3 BYOS storage
            Args:
                storage_name    (str)       : name of the BYOS cloud storage
                auth_type   (str)           : type of authentication.
                                                "Access and Secret Key" or "STS assume role with IAM policy"
                                                 or "IAM role"
                byos_bucket_name    (str)   : bucket name of the BYOS
                standard    (bool)          : storage class is standard to infrequent
                    default : True
        """
        self.wizard.click_add_icon()
        self._admin_console.wait_for_completion()
        title = "Add cloud storage"
        self.dialog = RModalDialog(admin_console=self._admin_console, title=title)
        self.dialog.select_dropdown_values(drop_down_id='cloudType', values=['Amazon S3'])
        self.dialog.fill_text_in_field(element_id='cloudStorageName', text=storage_name)
        if auth_type == "Access and Secret Key":
            self.dialog.select_dropdown_values(drop_down_id='authentication', values=['Access and secret keys'])
            self.dialog.fill_text_in_field(element_id='userName', text=self.config_file.aws_access_creds.access_key)
            self.dialog.fill_text_in_field(element_id='password', text=self.config_file.aws_access_creds.secret_key)
        elif auth_type == 'STS assume role with IAM policy':
            self.dialog.select_dropdown_values(drop_down_id='authentication', values=['STS assume role with IAM role'])
            self.dialog.fill_text_in_field(element_id='arnRole', text=self.config_file.aws_access_creds.tenant_role_arn)
        else:
            self.dialog.select_dropdown_values(drop_down_id='authentication', values=["IAM role"])
        self.dialog.fill_text_in_field(element_id='mountPath', text=byos_bucket_name)
        if standard:
            self.dialog.select_dropdown_values(drop_down_id='storageClass', values=['S3 Standard'])
        else:
            self.dialog.select_dropdown_values(drop_down_id='storageClass', values=['S3 Standard-Infrequent Access'])
        self.click_looped_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def _create_cloud_account(self, name):
        """
        This function will create the cloud account
        args:
            name (str)  :   name of the cloud account to be display
        """
        self.wizard.click_add_icon()
        self._admin_console.wait_for_completion()
        self._adminconsole.fill_form_by_id('name', name)
        self._adminconsole.click_button('Save')
        self._admin_console.wait_for_completion()

    @PageService()
    def _select_cloud_account(self, name):
        """
        selects the cloud account from the drop-down
        args:
            name (str)  :   selects the cloud account with given name
        """
        self.wizard.click_refresh_icon()
        self.wizard.select_drop_down_values(
            id='cloudAccount', values=[name])
        self._admin_console.wait_for_completion()

    def select_backup_content_aws(self, content):
        """
        Selects specific content to back up
        args:
            content (list of str)   :   "Content to be selected"
        """
        if content is not None:
            self.wizard.click_button("Edit")
            self._admin_console.wait_for_completion()
            self._adminconsole.click_button(id="AddContent")
            self._admin_console.wait_for_completion()
            self._rcontentbrowse.select_content(content=content)
            self._adminconsole.click_button('Done')
            content_dialog = RModalDialog(self._admin_console, title="Browse backup content")
            content_dialog.click_button_on_dialog(text='Save')
            self._adminconsole.click_button('Save')
        self.wizard.click_next()

class RAWSOracleMetallic(RAWSMetallic):
    """
    Provides helper function for configuring oracle database on EC2 VM'S
    """

    def __init__(self, admin_console, ec2_helper, s3_helper):
        """Initialize the class
            Args:
            admin_console   :   instance of AdminConsoleBase
            ec2_helper      :   EC2 helper object
            s3_helper       :   instance of S3MetallicHelper
        """
        self.db_helper = None
        self.ec2_helper = ec2_helper
        self.gateway_instance_name = None
        super().__init__(admin_console, app_type=DatabaseTypes.oracle, s3_helper=s3_helper, aws_helper=ec2_helper)

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return 'Oracle'

    def create_in_bound_rule(self, ec2_instance_name, region):
        """This will fetch newly created backup gateway IP and add to oracle client inbound rule
            Args:
                ec2_instance_name   (str)   :   name of the Oracle EC2 client
                region              (str)   :   Region where client is hosted
        """
        inbound_ip = self.ec2_helper.get_public_ip(instance_id=self.gateway_instance_name.replace('BackupGateway-', ''),
                                                   region=region)
        self.log.info(f"Fetched IP as {inbound_ip}")
        self.ec2_helper.add_inbound_rule(ec2_instance_name, region, inbound_ip)

    def create_install_inputs(self, **kwargs):
        """This is a helper function to create the interactive installation inputs
            Args:
                kwargs:
                    HostName        (str)   :IP of the Oracle client
                    clientName      (str)   :Name of the client displayed in metallic
                    ClientUsername  (str)   :Username of oracle client
                    ClientPassword  (str)   :Password of Oracle Client
                    tenant_username (str)   :username of the tenant created
                    tenant_password (str)   :Tenant password
                    instanceName    (str)   :instance name of oracle in client
        """
        install_inputs = {
            "HostName": kwargs.get("HostName"),
            "remote_clientname": kwargs.get("clientName"),
            "remote_username": kwargs.get("ClientUsername"),
            "remote_userpassword": kwargs.get("ClientPassword"),
            "os_type": kwargs.get("machine").os_info.lower(),
            "platform": kwargs.get("machine").os_flavour,
            "username": kwargs.get("tenant_username"),
            "password": kwargs.get("tenant_password"),
            "instancename": kwargs.get("instanceName")
        }
        return [install_inputs]

    @PageService()
    def create_gateway(self, **kwargs):
        """
        This function will create a backup gateway and add in bound rule
        kwargs:
            stack_name          (str)   :name of Gateway in aws
            stack_params        (list of dict):keypair, vpcId, SubnetId
            EC2_instance_name   (str)   : Name of the oracle client
            Region              (str)   :Name of the region where EC2 is hosted
        """
        self.wizard.click_next()
        self._select_authentication("IAM Role")
        region = self.ec2_helper.convert_region_codes_to_names(region_code=kwargs.get("Region"))
        self._select_region(region)
        self.gateway_instance_name = self._create_aws_backup_gateway(**kwargs, title="Backup gateway")
        self.create_in_bound_rule(kwargs.get("EC2_instance_name"), kwargs.get("Region"))
        return self.gateway_instance_name

    @PageService()
    def configure(self, byos_storage_name, byos_bucket_name, **kwargs):
        """This function is to configure the steps of creating oracle server hosted on AWS vm's
        Args:
            byos_storage_name       (str)   : Name of the s3 metallic storage name
            byos_bucket_name        (str)   : Name of s3 bucket name in AWS
            kwargs:
                EC2_instance_name   (str)   : Name of the oracle client
                Region              (str)   :Name of the region where EC2 is hosted
                plan_name           (str)   :Name of the plan created
                push_install        (Bool)  :Either to select type of install
                HostName            (str)   :IP of the Oracle client
                InstanceName        (str)   :Name of the EC2 client
                clientName          (str)   :Name of the client displayed in metallic
                ClientUsername      (str)   :Username of oracle client
                ClientPassword      (str)   :Password of Oracle Client
                tenant_username     (str)   :username of the tenant created
                tenant_password     (str)   :Tenant password
        """
        self.wizard.click_next()
        self._select_authentication("IAM Role")
        region = self.ec2_helper.convert_region_codes_to_names(region_code=kwargs.get("Region"))
        self._select_region(region)
        self._select_backup_gateway(self.gateway_instance_name)
        self._create_byos_s3(byos_storage_name, "IAM Role", byos_bucket_name, standard=True)
        self._create_plan("AWSMetallicOraclePlan")
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        install_inputs = self.create_install_inputs(**kwargs)
        if kwargs.get('push_install'):
            self.do_push_install(install_inputs)
        else:
            pkg_file_path = self.do_pkg_download(platform="Linux")
            self.do_pkg_install(commcell=kwargs.get("Commcell"), pkg_file_path=pkg_file_path,
                                install_inputs=install_inputs)
        self._admin_console.wait_for_completion()
        self.select_backup_content()
        self._admin_console.wait_for_completion()
        self.proceed_from_summary_page()


class RAWSDynamoDB(RAWSMetallic):
    """Class to setup Dynamo DB instance in metallic page"""

    def __init__(self, admin_console, aws_helper, s3_helper):
        """
            Initialize the class

            Args:
                admin_console: instance of AdminConsoleBase
                aws_helper: instance of dynamo_helper(amazonHelper)
                s3_helper   : instance of S3MetallicHelper
        """
        super().__init__(admin_console, s3_helper=s3_helper, aws_helper=aws_helper)

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return 'DynamoDB'


class RAWSDocumentDB(RAWSMetallic):
    """Class to setup DocumentDB instance in metallic page"""

    def __init__(self, admin_console, s3_helper, aws_helper):
        """
            Initialize the class

            Args:
                admin_console: instance of AdminConsoleBase
                aws_helper: instance of document_helper(amazonHelper)
                s3_helper   : instance of S3MetallicHelper
        """
        super().__init__(admin_console, s3_helper=s3_helper, aws_helper=aws_helper)

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return 'DocumentDB'


class RAWSRedshift(RAWSMetallic):
    """Class to setup Redshift DB instance in metallic page"""

    def __init__(self, admin_console, s3_helper, aws_helper):
        """
            Initialize the class

            Args:
                admin_console: instance of AdminConsoleBase
                aws_helper: instance of redshift_helper(amazonHelper)
                s3_helper   : instance of S3MetallicHelper
        """
        super().__init__(admin_console, s3_helper=s3_helper, aws_helper=aws_helper)

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return 'Redshift'


class RAWSRDS(RAWSMetallic):
    """Class to setup RDS instance in metallic page"""

    def __init__(self, admin_console, s3_helper, aws_helper):
        """
            Initialize the class

            Args:
                admin_console: instance of AdminConsoleBase
                aws_helper: instance of rds_helper(amazonHelper)
                s3_helper   : instance of S3MetallicHelper
        """
        super().__init__(admin_console, s3_helper=s3_helper, aws_helper=aws_helper)

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return 'RDS (Snapshot)'

class AWSRDSExport(RAWSMetallic):
    """Class for creating AWS RDS Export Instances in Metallic page"""
    def __init__(self, admin_console, s3_helper, aws_helper, database_type):
        """
            Initialize the class

            Args:
                admin_console: instance of AdminConsoleBase
                aws_helper: instance of rds_helper(amazonHelper)
                s3_helper   : instance of S3MetallicHelper
                database_type   : type of database server  - of type Hub.constants.DatabaseTypes
        """
        self.databasetype = database_type
        super().__init__(admin_console, s3_helper=s3_helper, aws_helper=aws_helper)

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return "RDS (Export)"

    @property
    def database_type(self):
        """return the database server type"""
        return self.databasetype



class RAzureDatabases(CloudDatabases):
    @property
    def cloud_db_engine(self):
        """Override this method and implement it as a variable
                whose value needs to be set for Cloud DB engine"""
        raise NotImplementedError

    @PageService()
    def _create_azure_db_cloud_account(self, cloud_account_name, credential_name, app_auth=False):
        """
        Method to create cloud account
        Args:
            cloud_account_name      (str):  Name of the cloud account
            credential_name         (str):  Name of the credential if Authentication is App based
        """
        self._admin_console.wait_for_completion()
        self.wizard.click_add_icon()
        self._admin_console.fill_form_by_id("name", cloud_account_name)
        self._admin_console.fill_form_by_id("subscriptionId", _CONFIG_DATA.Azure.Subscription)
        if app_auth:
            self.rmodal.disable_toggle(label=self._adminconsole.props['label.managedSvcIdentity'])
            self.rmodal.click_button_on_dialog(aria_label="Create new")
            self._create_azure_app_credentials(credential_name)
        else:
            self.rmodal.enable_toggle(label=self._adminconsole.props['label.managedSvcIdentity'])
        self._admin_console.click_button('Save')
        self._admin_console.wait_for_completion()

    @PageService()
    def configure(self, commcell, region, resource_group, **kwargs):
        """
        Creates Microsoft Azure Database instance
        Args:
            commcell                (Commcell): object of commcell
            region                  (str)   : Name of the region
            resource_group          (str)   : resource group to deploy VM

        Keyword Args:
            cloud_account           (str):  The cloud account that needs to be used for configuring instance
            plan                    (str):  Name of the plan
            instance_name           (str):  Database instance to be selected
            database_user           (str):  Username of Database User
            database_password       (str):  Password of Database User
            storage_account_name    (str):  Azure storage account name
            storage_password        (str):  Azure storage account password
            endpoint                (str):  Azure Database endpoint
            maintenance_db          (str):  Maintenance database name
                        default: postgres
            cloud_storage_name      (str):  Azure BYOS Storage name
            storage_credential      (str):  Azure storage credential name
            container               (str):  Container name
            app_auth                (bool): True if cloud account is created based on Azure App Authentication
            app_credential          (str):  Azure App credential name
            ssl                     (bool): False if ssl is disabled for DB instance
            ad_auth                 (bool): False if ad_auth has to be disabled for DB instance
            storage_auth_type       (str) : Type of Authentication for cloud storage
            is_primary_mrr          (bool): True if creating primary MRR Storage
                        default           :   False
            is_secondary_storage    (bool): True if creating secondary copy
                        default           :   False
            is_secondary_mrr        (bool): True if creating secondary MRR Storage
                        default           :   False


        Returns:
            backup_gateway          (str):  Name of the backup_gateway deployed
        """

        # navigate till backup gateway creation
        self.select_database()
        self.select_trial_subscription()
        self._set_database_engine()
        self.select_backup_method(backup_method_id='backupViaGateway')
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        self._select_region(region)
        backup_gateway = self._create_or_reuse_azure_backup_gateway(location=region, resource_group=resource_group)
        # after backup gateway creation, upgrade the remote machine software
        client = commcell.clients.get(backup_gateway)
        if client.properties['client']['versionInfo']['UpdateStatus'] == 0:
            jobid = self.upgrade_client_software(backup_gateway)
            self.wait_for_job_completion(jobid, commcell)
            self._copy_ssl_file_to_access_node(backupgateway=backup_gateway,
                                               commcell=commcell,
                                               cert_name='\\DigiCertGlobalRootCA.crt.pem')
            # start the db instance creation wizard flow
            self.navigator.navigate_to_service_catalogue()
            self.select_database()
            self.select_trial_subscription()
            self._set_database_engine()
            self.select_backup_method(backup_method_id='backupViaGateway')
            self.wizard.click_next()
            self._admin_console.wait_for_completion()
            self._select_region(region)
        parts = backup_gateway.split("-")
        bkp_gateway = ' ' + '(' + parts[0] + '-' + parts[1] + ')'
        bkp_gateway = backup_gateway + bkp_gateway
        self._select_backup_gateway(bkp_gateway)
        self._admin_console.wait_for_completion()
        self._create_azure_storage(**kwargs)
        self._admin_console.wait_for_completion()
        self.wizard.click_next()
        self._create_plan(kwargs.get("plan"))
        self.wizard.click_next()
        self._create_azure_db_cloud_account(kwargs.get("cloud_account"), kwargs.get("app_credential"),
                                            kwargs.get("app_auth", False))
        self._set_cloud_account(kwargs.get("cloud_account"))
        self._configure_instance(**kwargs)
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        self.wizard.click_button('Finish')
        return backup_gateway


class RAzurePostgreSQLInstance(RAzureDatabases):
    """Class for creating Microsoft Azure PostgreSQL in Metallic page"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return 'PostgreSQL'


class RAzureMySQLInstance(RAzureDatabases):
    """Class for creating Microsoft Azure MySQL in Metallic page"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return 'MySQL'


class RAzureMariaDBInstance(RAzureDatabases):
    """Class for creating Microsoft Azure MariaDB in Metallic page"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return 'MariaDB'


class RMSSQLMetallic(RDatabasesMetallic):
    """Class with helper methods to configure new SQL instance in metallic"""

    def __init__(self, admin_console):
        self._adminconsole = admin_console
        super(RMSSQLMetallic, self).__init__(admin_console, DatabaseTypes.sql)

    @WebAction()
    def __click_add_btn(self):
        """Clicks the '+' add button on the SQL Server Authentication"""
        xpath = "//button[@aria-label= 'Create new' and contains(@class, 'MuiIconButton-root')]"
        self._adminconsole.driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def click_add_credential_sql(self):
        """Clicks the add button ('+') on credential manager dialog box"""
        self.__click_add_btn()
        self._adminconsole.wait_for_completion()

    def impersonate_user_sql(self, username, password, description=None):
        """ Impersonates user with sysadmin access with Credential Manager UI

                        Args:
                            username (str)          --      User with sysadmin access

                            password (str)          --      Password for the above user

                           description (str)         --      Description for credential entity (Optional)

        """
        self.click_add_credential_sql()
        time_now = (datetime.now()).strftime("%H:%M:%S")
        time_now = time_now.replace(":", "_")
        credential_name = "Mtlc_SQL_Atmn_TC_" + time_now
        if not description:
            description = f"This credential is created as part of SQL onboarding automation run. Can be deleted"
        self.rmodal.fill_text_in_field("name", credential_name)
        # userAccount for Windows. userName for Linux
        if self._adminconsole.check_if_entity_exists("id", "userAccount"):
            self.rmodal.fill_text_in_field("userAccount", username)
        else:
            self.rmodal.fill_text_in_field("userName", username)
        self.rmodal.fill_text_in_field("password", password)
        self.rmodal.fill_text_in_field("description", description)

        self.rmodal.click_save_button()
        error_message = self._adminconsole.get_error_message()
        if error_message:
            raise CVWebAutomationException("Exception in creating credentials: {0}".format(error_message))
        self._LOG.info("*" * 10 + "Credentials created and impersonated." + "*" * 10)

    def configure_sql_db(self, commcell, cloud_storage_inputs, plan_inputs, install_inputs, impersonate_user_inputs,
                         use_existing_plan=False, backup_to_cloud=True, silent_install=False):
        """Configures and sets up database from Metallic Hub

                        Args:

                            commcell                            :   The CommCell object

                            cloud_storage_inputs       (dict)   : Dictionary input that goes for configuring cloud
                                                                    storage.

                                                                    dictionary passed should be:
                                                                    {
                                                                    "cloud_vendor": "<storage account>",
                                                                    "storage_provider" : "<cloud storage provider>",
                                                                    "region"        : "<storage region>"
                                                                    }

                            use_existing_plan          (bool)   : If True uses an existing plan, else configures a
                                                                    new one with the provided inputs
                            backup_to_cloud            (bool)   : If true, backs up via cloud, else uses backup gateway
                                default value                   : True

                            plan_inputs                (dict)   : Dictionary input that goes for plan
                                                                    If use_existing_plan is true,
                                                                    dictionary passed should be:
                                                                    {
                                                                    "PlanName": "<Existing plan name>"
                                                                    }
                                                                    If use_existing_plan is false,
                                                                    dictionary passed should be:
                                                                    {
                                                                    "RetentionPeriod": "<Retention period>"
                                                                    }

                            install_inputs              (dict)  :   Dictionary input that goes for configuring DB
                                                                    package install

                                                                    Dictionary passed should be:
                                                            {
                                                                "remote_clientname"     : "<FQDN of the machine>"
                                                                "remote_username"       : "<username to connect to
                                                                                            remote machine>",
                                                                "remote_userpassword"   : "<password to connect to
                                                                                            remote machine>",
                                                                "os_type"               :  "<OS type of remote client>"
                                                                "username"              : "<Username of CS to
                                                                                            authenticate client>"
                                                                "password"              : "<Password  of CS
                                                                                            authenticate client>"
                                                                "authcode" (optional)   : "<Authcode to
                                                                                            authenticate client>"
                                                            }

                            impersonate_user_inputs     (dict)  :  Dictionary inputs for impersonating user for MSSQL

                                                                    Dictionary passed should be :
                                                                    {
                                                                        "SQLImpersonateUser"       : "<User with
                                                                                                    sysadmin access>"
                                                                        "SQLImpersonatePassword"   : "<Password for the
                                                                                                    above user>"
                                                                        "tc_id"                    : "<Test Case id>"
                                                                        "description" (optional)   : "< Description for
                                                                                                    credential entity>"
                                                                    }

                            silent_install              (bool)  :   Boolean value on performing install silently

                        Returns:
                            str     :       Name of the new plan created if use_existing_plan is false
        """
        if backup_to_cloud:
            self.select_backup_deploy()
            self.select_cloud_storage(cloud_storage_inputs["cloud_vendor"],
                                      cloud_storage_inputs["storage_provider"],
                                      cloud_storage_inputs["region"])
            if use_existing_plan:
                try:
                    plan_name = plan_inputs["PlanName"]
                    self.wizard.select_plan(plan_name=plan_inputs["PlanName"])
                    self.wizard.click_next()
                except NoSuchElementException:
                    raise CVWebAutomationException(f"No such element exception has been raised, "
                                                   f"Please check if the provided plan name {plan_inputs['PlanName']} "
                                                   f"exists")
            else:
                plan_name = self.create_new_plan(retention_period=plan_inputs["RetentionPeriod"])
                self._LOG.info("*" * 10 + f"{plan_name} created!" + "*" * 10)
                self._adminconsole.click_button(value="Next")
            install_inputs["plan_name"] = plan_name
            if install_inputs.get("os_type") == "unix":
                self.do_pkg_install(self.do_pkg_download(platform="unix"), [install_inputs], commcell)
            else:
                self.do_pkg_install(
                    self.do_pkg_download(),
                    [install_inputs],
                    commcell,
                    silent_install=silent_install
                )
            self.impersonate_user_sql(impersonate_user_inputs["SQLImpersonateUser"],
                                      impersonate_user_inputs["SQLImpersonatePassword"]
                                      )
            self.wizard.click_next()
            self._LOG.info("*" * 10 + "At backup content panel now." + "*" * 10)
            self.wizard.click_next()
            self._LOG.info("*" * 10 + "At final summary page now" + "*" * 10)
            self._adminconsole.click_button(value="Finish")
            return plan_name

class RAzureSQLServerInstance(CloudDatabases):
    """Class for creating Microsoft Azure SQL in Metallic page"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return "Azure SQL Server and Managed SQL"

    @PageService()
    def _configure_instance(self, instance_name, storage_connection_string, **kwargs):
        """
            method to configure the Azure SQL instance details

            Args:
                instance_name       (str):  Name of the instance

                storage_connection_string   (str):  Storage connection string for the Azure storage account

            Keyword Args:
                credentials         (str or dict):  Name of existing credentials or dictionary of credentials to create

                Dictionary to pass for new credentials:
                {
                    credential_name:  The name for the new credentials
                    username:  The username for new credentials creation
                    password:  The password for new credentials creation
                    description:  The description for the new credentials
                }
        """
        self.wizard.select_drop_down_values(id='cloudInstanceDropdown', values=[instance_name])
        self._admin_console.fill_form_by_id('azureStorageConnectionString', storage_connection_string)
        credentials = kwargs.get('credentials')
        if isinstance(credentials, dict):
            credential_name = credentials.get('credential_name')
            username = credentials.get('username')
            password = credentials.get('password')
            description = credentials.get('description')
            if credential_name and username and password:
                self.wizard.click_refresh_icon()
                self.wizard.click_add_icon()
                self._create_credentials(credential_name, username, password, description)
        else:
            self.wizard.select_drop_down_values(id='connectionString', values=[credentials])
        self.wizard.click_next()

    @PageService()
    def _create_credentials(self, credential_name, username, password, description=None):
        """
            method to create SQL server credentials
            Args:
                credential_name     (str):  Name of credentials to create

                username            (str):  Name of the user

                password            (str):  Password for user

                description         (str, Optional):    Description of the credentials. Default is None
        """

        self._admin_console.fill_form_by_id('credentialName', credential_name)
        self._admin_console.fill_form_by_id('userName', username)
        self._admin_console.fill_form_by_id('password', password)

        if description:
            self._admin_console.fill_form_by_id('description', description)

    @PageService()
    def configure(
            self,
            region,
            backup_gateway,
            cloud_storage,
            plan,
            cloud_account,
            instance_name,
            storage_connection_string,
            **kwargs
            ):
        """
            Creates a Microsoft Azure SQL Server instance
            Args:
                region          (str):  Name of the region

                backup_gateway  (str):  Name of the backup gateway to use as access node

                cloud_storage   (str):  Name of cloud storage

                plan            (str):  The name of the plan

                cloud_account   (str):  The cloud account that needs to be used for configuring the instance

                instance_name   (str):  The Azure SQL instance to be selected

                storage_connection_string   (str):  Storage connection string for the Azure storage account

            Keyword Args:
                credentials     (str or dict):  Name of existing credentials or dictionary of credentials to create

                Dictionary to pass for new credentials:
                {
                    credential_name:  The name for the new credentials
                    username:  The username for new credentials creation
                    password:  The password for new credentials creation
                    description:  The description for the new credentials
                }

            """
        self._set_database_engine()
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        self._select_region(region)
        self._select_backup_gateway(backup_gateway)
        self._select_storage_account(cloud_storage)
        self._set_plan(plan)
        self._set_cloud_account(cloud_account)
        self._configure_instance(
            instance_name,
            storage_connection_string,
            **kwargs
        )
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        self.wizard.click_button(self._admin_console.props['Finish'])
