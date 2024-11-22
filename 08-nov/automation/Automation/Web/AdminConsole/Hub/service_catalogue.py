# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Hub import constants as hcs
from Web.AdminConsole.Hub.constants import HubServices, DatabaseTypes
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService


class ServiceCatalogue:
    """
    This module provides the function or operations that can be performed on the
    Service Catalogue page on the Metallic Hub
    """

    def __init__(self, admin_console, service, app_type=None):
        """
        Initializes the properties of the class for the selected locale

        Args:
            admin_console   :   instance of the adminconsole class
            service         :   instance of HubServices class
            app_type        :   instance of any of the following classes:-
                                Office365AppTypes/DatabaseTypes/VMKubernetesTypes/RiskAnalysisType

        """
        self.__adminconsole = admin_console
        self.__driver = admin_console.driver
        self.__service = service
        self.__app_type = app_type
        self.__wizard = Wizard(self.__adminconsole)
        self.__Rtable = Rtable(self.__adminconsole)
        self.log = self.__adminconsole.log
        self.__page_container = PageContainer(admin_console)
        self.__panel = RPanelInfo(admin_console)

    @WebAction(delay=2)
    def __select_service(self, service, id=None, action=None):
        """
        Selects the service from the Service Catalogue page
        Args:
            service (str) -- HubService enum value
            id (str) -- Pass the id parameter for the service
            action(str) -- ServiceAction enum value. Type of action to perform. Ex: Configure, Manage, Learn More
        """
        if service == HubServices.office365.value:
            tile_name = "Microsoft 365"
        elif service == HubServices.Dynamics365.value:
            tile_name = "Dynamics 365"
        elif service == HubServices.object_storage.value:
            tile_name = "Object Storage"
        elif service == HubServices.database.value:
            tile_name = "Database"
        elif service == HubServices.ad.value:
            tile_name = "Active Directory"
        elif service == HubServices.salesforce.value:
            tile_name = "Salesforce"
        elif service == HubServices.risk_analysis.value:
            tile_name = HubServices.risk_analysis.value
        elif service == HubServices.google_workspace.value:
            tile_name = "Google Workspace"
        # Insert the tile_names according to the HubService Object
        else:
            raise CVWebAutomationException("Service Object not passed")

        perform_action = hcs.ServiceAction.CONFIGURE.value if action is None else action
        tile_xpath = "//div[contains(@class,'serviceTile')]//div/p[text()='{}']/" \
                     "ancestor::div/div[contains(@class,'MuiCardContent')]" \
                     "//button/div[text()='{}']".format(tile_name, perform_action)
        element = self.__driver.find_element(By.XPATH, tile_xpath)
        element.click()
        self.__adminconsole.wait_for_completion()
        if id:
            xpath = "//div//p[text()='{}']".format(id)
            if service == HubServices.ad.value:
                xpath = "//div[@class='row']//p[text()='Active Directory']"
            if self.__adminconsole.check_if_entity_exists("xpath", xpath):
                element = self.__driver.find_element(By.XPATH, xpath)
                element.click()
                self.__adminconsole.wait_for_completion()
        else:
            # NOTE: Don't raise exception if you want any other service action to be performed
            if not service == HubServices.risk_analysis.value:
                raise CVWebAutomationException("Pass the ID attribute")

    @WebAction(delay=2)
    def __is_office_365_trial_active(self):
        """Verifies if the office 365 trial is active"""
        subscription = self.__wizard.get_tile_content().split('\n')[0]
        if subscription == "You don't have a Office 365 subscription":
            is_trial_active = False
        else:
            is_trial_active = True
        return is_trial_active

    @WebAction(delay=2)
    def __is_dynamics_365_trial_active(self):
        """Verifies if the Dynamics 365 trial is active"""
        subscription = self.__wizard.get_tile_content().split('\n')[0]
        if subscription == "You don't have a Dynamics 365 subscription":
            is_trial_active = False
        else:
            is_trial_active = True
        return is_trial_active

    @WebAction(delay=2)
    def __is_azure_AD_trial_active(self):
        """Verifies if the Dynamics 365 trial is active"""
        subscription = self.__wizard.get_tile_content().split('\n')[0]
        if subscription == "Click Continue to start provisioning backup storage for Azure AD":
            is_trial_active = False
        else:
            is_trial_active = True
        return is_trial_active

    @WebAction(delay=2)
    def __is_salesforce_trial_active(self):
        """Verifies if the Salesforce trial is active"""
        subscription = self.__wizard.get_tile_content().split('\n')[0]
        if subscription == "You don't have a Salesforce subscription":
            is_trial_active = False
        else:
            is_trial_active = True
        return is_trial_active

    @WebAction(delay=2)
    def __is_risk_config_page_loaded(self):
        """
        Verifies if the risk analysis configure page is loaded
        Raises:
            Exception:
                If page fails to load
        """
        page_title_obj = self.__driver.find_elements(By.XPATH, "//*[contains(@class, 'page-title')]")
        page_title = page_title_obj[0].text
        if not page_title == hcs.RiskAnalysisConfigTitle[self.__app_type.name].value:
            raise CVWebAutomationException(
                f"Failed to load the risk analysis configure page for [{self.__app_type.value}]")
        else:
            self.log.info(f"Page loaded successfully for [{self.__app_type.value}]. Actual value [{page_title}]")

    @WebAction(delay=2)
    def __is_risk_manage_loaded(self):
        """
        Verifies if the risk analysis manage page is loaded
        Raises:
            Exception:
                If page fails to load
        """
        current_url = self.__driver.current_url
        if hcs.SDG_URL not in current_url:
            raise CVWebAutomationException("Failed to load the risk analysis manage page")
        self.log.info("Manage Page Loaded Successfully")

    @WebAction()
    def get_risk_subscription_type(self):
        """
        Returns the risk analysis subscription type
        """
        self.__select_service(HubServices.risk_analysis.value)
        title = self.__panel.title()
        if title == hcs.NO_SUBSCRIPTION:
            sub_type = hcs.RiskAnalysisSubType.NO_SUBSCRIPTION
            self.__panel.click_button("Close")
        elif title == hcs.SUBSCRIPTION_AND_NO_BACKUP:
            sub_type = hcs.RiskAnalysisSubType.SUBSCRIPTION_AND_NO_BACKUP
            self.__panel.click_button("Close")
        elif title == hcs.SUBSCRIPTION_AND_BACKUP:
            sub_type = hcs.RiskAnalysisSubType.SUBSCRIPTION_AND_BACKUP
            self.__panel.click_button_by_title("Close")
        else:
            sub_type = title
        return sub_type

    @WebAction(delay=2)
    def _check_for_errors(self):
        """Checks for errors while activating trial"""
        successful_trial_steps = ["Metallic Dynamics 365 subscription activated successfully",
                                  "Dynamics 365 plans created successfully",
                                  "Server plan for Dynamics 365 backups created successfully",
                                  "Metallic Office 365 subscription activated successfully",
                                  "Office 365 subscription activated successfully",
                                  "Office 365 plans created successfully",
                                  "Server plan for Office 365 backups created successfully",
                                  "Server plan for Azure AD backups created successfully",
                                  "Storage for Active Directory backups provisioned successfully in East US 2 region.",
                                  "Salesforce subscription activated successfully",
                                  "Server plan for Salesforce backups created successfully",
                                  "Google Workspace subscription activated successfully",
                                  "Google Workspace plans created successfully",
                                  "Server plan for Google Workspace backups created successfully"]
        attempts = 10
        while True:
            base_xpath = "//div[contains(@class, 'MuiGrid-root')]/span"
            if self.__service == HubServices.salesforce:
                base_xpath = "//div[contains(@class, 'MuiGrid-root')]/span[2]"
            elements = self.__driver.find_elements(By.XPATH, base_xpath)
            if all(element.text in successful_trial_steps for element in elements):
                self.log.info("Trial is active")
                break
            else:
                time.sleep(10)
                attempts -= 1
            if attempts == 0:
                success_xpath = "//div[contains(@class,'MuiAlert-standardSuccess')]"
                message_xpath = "//div[contains(@class,'MuiAlert-message')]"
                try:
                    if self.__driver.find_element(By.XPATH, success_xpath):
                        self.log.info("Trial is active")
                        break
                    else:
                        message = self.__driver.find_element(By.XPATH, message_xpath)
                        error_text = message.text
                        raise CVWebAutomationException(error_text)
                except NoSuchElementException:
                    self.log.info("Trial phase is not completed.")
                    time.sleep(10)
                    attempts = 3
                    continue

    @PageService()
    def click_get_started(self):
        """Clicks get started button for a new tenant"""
        try:
            if self.__adminconsole.check_if_entity_exists("xpath",
                                                          "//button[contains(.,'No thanks, I’ll explore on my own.')]"):
                self.__adminconsole.click_button(value='No thanks, I’ll explore on my own.')
            if self.__adminconsole.check_if_entity_exists("class", "bb-button"):
                self.__adminconsole.click_button('Got it')
            self.__adminconsole.close_popup()
            self.__adminconsole.wait_for_completion()
            if self.__adminconsole.check_if_entity_exists("name", "termsCheckbox"):
                self.__driver.execute_script("document.querySelector('#mdb-checkbox-1').click();")
            time.sleep(10)
            if self.__adminconsole.check_if_entity_exists("xpath", "//button[contains(.,'OK, got it')]"):
                self.__adminconsole.click_button('OK, got it')
            self.__adminconsole.click_button('Get started')
        except:
            pass

    @PageService()
    def choose_service_from_service_catalogue(self, service, id=None):
        """Choose service from service catalogue page"""
        if service == "Object Storage":
            # Object storage's component is of type page_container, else are mostly of type wizard.
            # If the component is of type page_container, do -> `if service in ['Object Storage' , 'New Entity'] :`
            self.close_welcome_panel()
            self.__select_service(service, id)
            self.__page_container.click_on_button_by_text("Start trial")
            self.__adminconsole.wait_for_completion()
            self.__adminconsole.click_button_using_text("Close")
            self.__adminconsole.wait_for_completion()
        elif service == HubServices.database.value and id == DatabaseTypes.sap_hana.value:
            self.__select_service(service, id)
            self.__adminconsole.unswitch_to_react_frame()
            self.__adminconsole.close_popup()
        elif service == HubServices.risk_analysis.value:
            self.close_welcome_panel()
            self.__select_service(service, id)
            self.__adminconsole.wait_for_completion()
        else:
            # Add the logic using wizard for other services
            self.__select_service(service, id)
            self.__adminconsole.wait_for_completion()
            # this Continue button will fail , update with Start trial followed by Close.
            if self.__adminconsole.check_if_entity_exists("id", "Submit"):
                self.__wizard.click_button(name="Continue")

    @PageService()
    def close_welcome_panel(self):
        """Closes the welcome panel if present"""
        if self.__adminconsole.check_if_entity_exists("xpath",
                                                      "//button[contains(@class, 'MuiButton-root')]//div[text()='No thanks, I’ll explore on my own.']"):
            self.__panel.click_button("No thanks, I’ll explore on my own.")

    @PageService()
    def start_office365_trial(self):
        """Starts the trial for office 365 service"""
        self.__select_service(service=self.__service.value, id=self.__app_type.value)
        if not self.__is_office_365_trial_active():
            self.__wizard.click_button(name="Start trial")
            self.__adminconsole.wait_for_completion()
            self._check_for_errors()
            self.__adminconsole.click_button_using_text("Close")
        self.__wizard.click_button(name="Continue")

    @PageService()
    def start_dynamics365_trial(self):
        """Starts the trial for Dynamics 365 service"""
        self.__select_service(service=self.__service.value, id="Dynamics 365")
        if not self.__is_dynamics_365_trial_active():
            self.__wizard.click_button(name="Start trial")
            self.__adminconsole.wait_for_completion()
            self._check_for_errors()
            self.__adminconsole.click_button_using_text("Close")
        self.__wizard.click_button(name="Continue")
        self.__adminconsole.wait_for_completion()

    @PageService()
    def start_azureAD_trial(self):
        """Starts the trial for Azure AD"""
        self.__select_service(service=self.__service.value, id="Azure AD")
        if not self.__is_azure_AD_trial_active():
            self.__wizard.click_button(name="Start trial")
            time.sleep(10)
            self.__adminconsole.wait_for_completion()
            self._check_for_errors()
            self.__adminconsole.click_button_using_text("Close")
        self.__wizard.click_button(name="Continue")
        self.__adminconsole.wait_for_completion()

    @PageService()
    def start_salesforce_trial(self):
        """Starts the trial for Salesforce"""
        self.__select_service(service=self.__service.value, id="Salesforce")
        if not self.__is_salesforce_trial_active():
            self.__wizard.click_button(name="Start trial")
            self.__adminconsole.wait_for_completion()
            self._check_for_errors()
            self.__adminconsole.click_button_using_text("Close")
        self.__wizard.click_button(name="Continue")
        self.__adminconsole.wait_for_completion()

    @PageService()
    def start_AD_trial(self):
        """Starts the trial for AD"""
        self.__select_service(service=self.__service.value, id="Active Directory")
        if not self.__is_AD_trial_active():
            self.__wizard.click_button(name="Start trial")
            self.__adminconsole.wait_for_completion()
            self._check_for_errors()
            self.__adminconsole.click_button_using_text("Close")
            self.__adminconsole.wait_for_completion()
        self.__wizard.click_button(name="Continue")
        self.__adminconsole.wait_for_completion()

    @PageService()
    def configure_risk_analysis(self):
        """Configures Risk Analysis"""
        self.__select_service(service=self.__service.value, id=self.__app_type.value)
        self.__adminconsole.wait_for_completion()
        self.__is_risk_config_page_loaded()

    @PageService()
    def manage_risk_analysis(self):
        """Manages Risk Analysis"""
        self.__select_service(service=self.__service.value, id=None, action=hcs.ServiceAction.MANAGE.value)
        self.__adminconsole.wait_for_completion()
        self.__is_risk_manage_loaded()

    @WebAction(delay=2)
    def __is_AD_trial_active(self):
        """Verifies if the Active Directory trial is active"""
        subscription = self.__wizard.get_tile_content().split('\n')[0]
        if subscription == "You don't have an Active Directory subscription":
            is_trial_active = False
        else:
            is_trial_active = True
        return is_trial_active
    
    @WebAction(delay=2)
    def __is_googleworkspace_trial_active(self):
        """Verifies if the Google Workspace trial is active"""
        if self.__adminconsole.check_if_entity_exists("xpath", "//form[contains(@class, 'form-wrapper')]"):
            self.__wizard.click_element("//input[@id='appInstallationConfirmation']")
            self.__wizard.click_next()
        subscription = self.__wizard.get_tile_content().split('\n')[0]
        if subscription == "You don't have a Google Workspace subscription":
            is_trial_active = False
        else:
            is_trial_active = True
        return is_trial_active

    @PageService()
    def start_googleworkspace_trial(self):
        """Starts the trial for Google Workspace"""
        self.__select_service(service=self.__service.value, id=self.__app_type.value)
        if not self.__is_googleworkspace_trial_active():
            self.__wizard.click_button(name="Start trial")
            self.__adminconsole.wait_for_completion()
            self._check_for_errors()
            self.__adminconsole.click_button_using_text("Close")
        self.__wizard.click_button(name="Continue")
        self.__adminconsole.wait_for_completion()

