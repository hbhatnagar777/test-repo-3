from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""
This module provides the function that can be used to run test cases of FS for Hub
"""

import time

from Install.install_custom_package import InstallCustomPackage
from Web.AdminConsole.Components.panel import ModalPanel
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService

class MetallicFS:
    """class for file servers on Hub"""

    def __init__(self, admin_console):
        """
        Args:
        admin_console(AdminConsole): adminconsole object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._mpanel = ModalPanel(admin_console)

    @staticmethod
    def set_inputs(testcase):
        """
            Creates a dictionary for test case inputs needed for customer package install.
        Args:
            testcase (obj):          Testcase object
        Returns:
            inputs (dict):    Key value dictionary for the required inputs
        Raises
            Exception:
                If failed to get the inputs
        """
        inputs = {}
        try:
            if testcase.os_name.lower() == 'windows':
                inputs["full_package_path"] = testcase.custompkg_directory + "\\WindowsFileServer64.exe"
                inputs["registering_user_password"] = testcase.tenantpassword
            else:
                inputs["full_package_path"] = testcase.custompkg_directory + "\\LinuxFileServer64.tar"
                inputs["registering_user_password"] = testcase.tenantencryptedpassword
            inputs["registering_user"] = testcase.tenantuser
            inputs['os_type'] = testcase.os_name.lower()
            inputs["remote_clientname"] = testcase.tcinputs.get("MachineFQDN")
            inputs["remote_username"] = testcase.tcinputs.get("MachineUserName")
            inputs["remote_userpassword"] = testcase.tcinputs.get("MachinePassword")
            return inputs
        except:
            raise Exception("failed to set inputs for install")

    @WebAction()
    def __click_file_server(self):
        """Method to click on "New Configuration" button"""
        xpath = \
            "//a[@class='dropdown-item configuration-item ng-star-inserted']" + \
            "/span[contains(text(),'File Server')]"
        if self._admin_console.check_if_entity_exists('xpath', xpath):
            self._driver.find_element(By.XPATH, xpath).click()
            self._admin_console.wait_for_completion()
        else:
            raise CVWebAutomationException("New Configuration option does not exist")

    @WebAction()
    def __select_deploy_option(self, radioid):
        """
        Method to select option for deploy your backup. two option: cloud or onPrem
        Args:
            radioid (str)  : value should be "onPrem" or "cloud"
        """
        xpath = f"//input[@type = 'radio'][@id='{radioid}']/following-sibling::label"
        if self._admin_console.check_if_entity_exists('xpath', xpath):
            self._driver.find_element(By.XPATH, xpath).click()
            self._admin_console.wait_for_completion()
        else:
            raise CVWebAutomationException("backup to cloud or using proxy radio option does not exist")

    @WebAction()
    def __select_os(self, os_type):
        """select Operating system type"""
        if os_type.lower() == "windows":
            xpath = "//input[@type = 'radio'][@id='optWindows']/following-sibling::label"
        else:
            xpath = "//input[@type = 'radio'][@id='optUnix']/following-sibling::label"
        if self._admin_console.check_if_entity_exists('xpath', xpath):
            self._driver.find_element(By.XPATH, xpath).click()
            self._admin_console.wait_for_completion()
        else:
            raise CVWebAutomationException("windows/unix os option does not exist")

    @WebAction()
    def __select_existing_stoage_location(self, value):
        """select drop down value from existing cloud values
        Args:
            value    (str)    :   storage location
        """
        xpath = "//mdb-select[@label='Cloud storage location']"
        if self._admin_console.check_if_entity_exists('xpath', xpath):
            self._driver.find_element(By.XPATH, xpath).click()
            self._admin_console.wait_for_completion()
        else:
            self._admin_console.log.info("select a cloud location option does not exist")
            return 0

        dropdown_xpath = \
            f"//span[contains(text(), '{value}')]"
        if self._admin_console.check_if_entity_exists('xpath', dropdown_xpath):
            self._driver.find_element(By.XPATH, dropdown_xpath).click()
            self._admin_console.wait_for_completion()
            return 1
        else:
            self._admin_console.log.info("storage location does not exist")
            return 0

    @WebAction()
    def __select_storage_account(self, storageaccount):
        """
        select storage account 
        Args:
            storageaccount    (str)    :   storage acount name
        """
        xpath = "//mdb-select[@label='Storage account']"
        if self._admin_console.check_if_entity_exists('xpath', xpath):
            self._driver.find_element(By.XPATH, xpath).click()
            self._admin_console.wait_for_completion()
            storagevalue = f"//li/span[contains(text(),'{storageaccount}')]"
            if self._admin_console.check_if_entity_exists('xpath', storagevalue):
                self._driver.find_element(By.XPATH, storagevalue).click()
                self._admin_console.wait_for_completion()
            else:
                self._admin_console.log.info("storage account does not exist under the drop down")
        else:
            raise CVWebAutomationException("storage account option does not exist")

    @WebAction()
    def __select_storage_region(self, storageregion):
        """
        select cloud storage provider
        Args:
            storageregion   (str)    :     cloud storage region
        """
        xpath = "//mdb-select[@label='Storage region']"
        if self._admin_console.check_if_entity_exists('xpath', xpath):
            self._driver.find_element(By.XPATH, xpath).click()
            self._admin_console.wait_for_completion()
            storagevalue = f"//li/span[contains(text(), '{storageregion}')]"
            if self._admin_console.check_if_entity_exists('xpath', storagevalue):
                self._driver.find_element(By.XPATH, storagevalue).click()
                self._admin_console.wait_for_completion()
            else:
                self._admin_console.log.info("storage region does not exist under the drop down")
        else:
            raise CVWebAutomationException("Storage region option does not exist")

    @WebAction()
    def __create_storage(self):
        """
        create cloud backup storage
        """
        self._admin_console.click_button_using_text("Create")
        self.__wait_for_cloud_storage_creation()

    def __wait(self, wait_time):
        """
        wait for wait_time
        Args:
            wait_time (int)    :  wait time
        """
        time.sleep(wait_time)

    def __check_entity_exist_and_displayed(self, xpath):
        """check an entity exist and is displayed"""
        if self._admin_console.check_if_entity_exists('xpath',xpath):
            return self._driver.find_element(By.XPATH, xpath).is_displayed()
        else:
            return False

    @PageService()
    def __wait_for_configure_server(self):
        """wait for FS server configuration complete. max wait 5 minutes"""
        failed_xpath = "//small[contains(text(),'We failed to install the software')]"
        success_xpath = "//small[contains(text(),'Successfully installed software')]"
        exist_xpath ="//small[contains(text(),'We found an existing configuration for this server')]"
        i = 0
        while i < 10:
            self.__wait(30)
            if self.__check_entity_exist_and_displayed(failed_xpath):
                raise Exception("Failed to install software")
            elif self.__check_entity_exist_and_displayed(success_xpath):
                self._admin_console.log.info("successfully installed software")
                break
            elif self.__check_entity_exist_and_displayed(exist_xpath):
                self._admin_console.log.info("Found an existing configuration for this server, continue")
                break
            else:
                self._admin_console.log.info("configuration is still going on, please wait")
                i += 1
                if i == 10:
                    raise Exception("time out waiting for configuration complete")

    @PageService()
    def __wait_for_cloud_storage_creation(self):
        """wait for new cloud storage configuration complete, max wait 5 minutes"""
        success_xpath = "//small[contains(text(),'Successfully configured the Metallic storage')]"
        i = 0
        while i < 10:
            self.__wait(30)
            if self.__check_entity_exist_and_displayed(success_xpath):
                self._admin_console.log.info("Successfully configured the Metallic storage")
                break
            else:
                self._admin_console.log.info("Please wait while we configure cloud storage")
                i += 1
                if i == 10:
                    raise Exception("time out waiting for configuration complete")

    @PageService()
    def __wait_for_plan_creation(self):
        """wait for new plan creation complete, max wait 10 minutes"""
        success_xpath = "//small[contains(text(),'We successfully created the plan')]"
        fail_xpath = "//small[contains(text(),'Role does not Exists')]"
        i = 0
        while i < 10:
            self.__wait(60)
            if self.__check_entity_exist_and_displayed(success_xpath):
                self._admin_console.log.info("successfully created the plan")
                break
            elif self.__check_entity_exist_and_displayed(fail_xpath):
                self._admin_console.log.info("Role does not exists to create plan")
                raise Exception("Failed to create new plan")
            else:
                self._admin_console.log.info("Please wait while create the plan")
                i += 1
                if i == 10:
                    raise Exception("time out waiting for plan creation")

    @PageService()
    def __wait_for_view_job_progress(self):
        """wait for submitting backup job, max wait 10 minutes"""
        success_xpath = "//small[contains(text(),'the submitted job')]"
        i = 0
        while i < 10:
            self.__wait(60)
            if self.__check_entity_exist_and_displayed(success_xpath):
                self._admin_console.log.info("successfully submitted backu pjob")
                break
            else:
                self._admin_console.log.info("Please wait while starting backup job")
                i += 1
                if i == 10:
                    raise Exception("time out waiting for submitting backup job")

    @PageService()
    def set_file_server_env(self, physical=True):
        """
        Select file server environment
        """
        self.__click_file_server()
        self._admin_console.wait_for_completion()
        if physical:
            self._mpanel.select_radio_button_and_type("Physical", type_text=False, text="")
        else:
            self._mpanel.select_radio_button_and_type("Virtual", type_text=False, text="")
        self._admin_console.click_button_using_text("Next")
        self._admin_console.click_button_using_text("Request to Trial")
        self._admin_console.wait_for_completion(120)
        self._admin_console.click_button("OK")
        
    @PageService()
    def download_package_for_newserver(self, os_name, backuptocloud=True):
        """
        Configure new file server
        Args:
            backuptocloud (str)     : true if backup to cloud
            os_name    (str)        : os type, "Windows" or "Unix"
        """
        if backuptocloud:
            self.__select_deploy_option("cloud")
        else:
            self.__select_deploy_option("onPrem")
        self._admin_console.wait_for_completion()
        self._admin_console.click_button_using_text("Next")
        self.__select_os(os_name)
        self._admin_console.select_hyperlink("Download")
        self._admin_console.wait_for_completion(wait_time=500)
        self.__wait(300)

    def install_fs(self, testcase):
        """FS installation and registration for metallic
        Args:
            testcase (obj):          Testcase instance
        """
        tcinputs = self.set_inputs(testcase)
        install_helper = InstallCustomPackage(testcase.commcell, tcinputs, tcinputs.get('os_type'))
        install_helper.install_custom_package(
            full_package_path=tcinputs.get('full_package_path'),
            username=tcinputs.get('registering_user'),
            password=tcinputs.get('registering_user_password')
            )

    @PageService()
    def configure_new_server(self, testcase):
        """
        Install and configure new server, once done, click Next button 
        Args:
            testcase (obj)   : testcase instance
        """
        self.install_fs(testcase)
        self._admin_console.fill_form_by_id("hostName", testcase.tcinputs.get("MachineFQDN"))
        self._admin_console.click_button_using_text("Submit")
        self.__wait_for_configure_server()
        self._admin_console.click_button_using_text("Next")
        self._admin_console.wait_for_completion()

    @PageService()
    def configure_cloud_storage(self, storageaccount, storageregion):
        """
        configure new cloud stoarge location
        Args:
            storageaccount (str)    :    storage account name
            storage region (str)    :    storage region
        """
        self.__select_storage_account(storageaccount)
        self.__select_storage_region(storageregion)
        self.__create_storage()
        self._admin_console.click_button_using_text("Next")
        self._admin_console.wait_for_completion()

    @PageService()
    def configure_plan(self, planname):
        """configure new server plan"""
        namestrs = planname.split("-")
        self._admin_console.fill_form_by_id("planName", namestrs[-1])
        self._admin_console.click_button_using_text("Create")
        self.__wait_for_plan_creation()
        self._admin_console.click_button_using_text("Next")
        self.__wait(300)

    @PageService()
    def return_to_hub(self):
        """
        after initial configuration complete, click Return to Hub button and go back to Hub
        """
        self._admin_console.click_button_using_text("Return to Hub")
        self._admin_console.wait_for_completion()

    @PageService()
    def click_advanced_view(self):
        """click advanced view option"""
        self._admin_console.select_hyperlink("Advanced View")

    @PageService()
    def click_back_up_now(self):
        """
        after initial configuration complete, click back up now option
        """
        self._admin_console.click_button_using_text("Back up now")
        self.__wait_for_view_job_progress()
        self._admin_console.select_hyperlink("View the progress")
        self._admin_console.wait_for_completion(wait_time=500)
