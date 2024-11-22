from selenium.webdriver.common.by import By
"""
Classes and functions related to contract management skus page.
"""
from time import sleep

from selenium.webdriver.support.ui import Select
from Web.Common.exceptions import CVWebAutomationException
from Web.WebConsole.Reports.Billing.common import BillingGroupOptions
from Web.Common.page_object import (
    WebAction, PageService
)
from AutomationUtils import logger, config

_CONFIG = config.get_config()


class ManageSKU(BillingGroupOptions):
    """
    Sku page related operations for adding/editing/deleting sku
    """

    @WebAction()
    def _click_add_sku(self):
        """
        click add sku
        """
        self._driver.find_element(By.XPATH, "//*[@title = 'New SKU']").click()
        sleep(3)

    @PageService()
    def add_sku(self):
        """
        Clicks on add sku
        """
        self._click_add_sku()
        return SKUPanel(self._webconsole)

    @PageService()
    def edit_sku(self, sku_name):
        """
        Edits existing sku
        Args:
            sku_name(String): Specify the sku name
        Returns:SKUPanel object
        """
        self._click_edit(sku_name)
        return SKUPanel(self._webconsole)

    @PageService()
    def delete_sku(self, sku_name):
        """
        Deletes existing sku
        Args:
            sku_name(String): Specify the sku name
        """
        self._click_delete(sku_name)
        self._click_button_dialogue_yes()

    @PageService()
    def is_sku_exists(self, sku_name):
        """
        Checks specified sku exists
        Args:
            sku_name: Specify the sku name
        Returns:True/False
        """
        self._webconsole.wait_till_loadmask_spin_load()
        if self._get_element_with_text(sku_name):
            return True
        return False


class SKUPanel:
    """
    Communicates with sku panel
    """
    counting_type_capacity = "Capacity"
    counting_type_client_Access = "Client Access"

    def __init__(self, webconsole):
        """
            webconsole:Webconsole object
        """
        self._webconsole = webconsole
        self._browser = self._webconsole.browser
        self._driver = self._webconsole.browser.driver
        self._billing_group_options = BillingGroupOptions(self._webconsole)
        self._log = logger.get_log()

    @WebAction()
    def _fill_sku_name(self, name):
        """
        set sku name
        """
        self._driver.find_element(By.ID, "billingGroupName").clear()
        self._driver.find_element(By.ID, "billingGroupName").send_keys(name)

    @WebAction()
    def _fill_description(self, description):
        """
        Set description
        """
        self._driver.find_element(By.ID, "billingGroupDesc").clear()
        self._driver.find_element(By.ID, "billingGroupDesc").send_keys(description)

    @WebAction()
    def _select_counting_type_list(self, counting_type):
        """
        Select counting type
        """
        counting_type_select = Select(self._driver.find_element(By.ID, "countingType"))
        counting_type_list = [counting_types.text for counting_types in
                              counting_type_select.options]
        if counting_type not in counting_type_list:
            raise CVWebAutomationException("Specified counting type name couldn't be found:%",
                                           counting_type)
        counting_type_select.select_by_visible_text(counting_type)

    @WebAction()
    def _select_license_types(self, licence: list):
        """
        Select license type
        """
        for each_licence in licence:
            self._driver.find_element(By.XPATH, 
                "//*[@id='licenseTypesTab']//li[@data-name='" + each_licence + "']").click()

    @WebAction()
    def _select_agents(self, agent: list):
        """
        Select agents
        """
        for each_agent in agent:
            self._driver.find_element(By.XPATH, 
                "//*[@id='licenseTypesTab']//li[@data-name='" + each_agent + "']").click()

    @WebAction()
    def _click_button_add_license_type(self):
        """
        click add license type button
        """
        self._driver.find_element(By.XPATH, "//button[@data-tabid='licenseTypesTab' "
                                           "and @class = 'addItemButton']").click()

    @WebAction()
    def _click_button_remove_license_type(self):
        """
        Click remove license type button
        """
        self._driver.find_element(By.XPATH, "//button[@data-tabid='licenseTypesTab' "
                                           "and @class = 'removeItemButton']").click()

    @WebAction()
    def _click_button_add_agent_type(self):
        """
        Click add agent type button
        """
        self._driver.find_element(By.XPATH, "//button[@data-tabid='agentsTab' "
                                           "and @class = 'addItemButton']").click()

    @WebAction()
    def _click_button_remove_agent_type(self):
        """
        Click remove button of agent tab
        """
        self._driver.find_element(By.XPATH, "//button[@data-tabid='agentsTab' "
                                           "and @class = 'removeItemButton']").click()

    @WebAction()
    def _click_licence_tab(self):
        """
        click on license tab
        """
        self._driver.find_element(By.XPATH, "//a[@href = '#licenseTypesTab']").click()

    @WebAction()
    def _click_agents_tab(self):
        """
        click on agents tab
        """
        self._driver.find_element(By.XPATH, "//a[@href = '#agentsTab']").click()

    @WebAction()
    def _click_button_save(self):
        """
        Click on save button
        """
        self._driver.find_element(By.XPATH, "//button/span[text()='Save']").click()
        sleep(2)

    @WebAction()
    def _click_button_close(self):
        """
        Click on close button
        """
        self._driver.find_element(By.XPATH, "//button/span[text()='Close']").click()

    @PageService()
    def set_sku_name(self, name):
        """
        sets sku name
        Args:
            name(string): Specify the sku name
        """
        self._fill_sku_name(name)

    @PageService()
    def set_description(self, description):
        """
        Sets sku description
        Args:
            description(String): Specify the sku description
        """
        self._fill_description(description)

    @PageService()
    def select_counting_type(self, counting_type=counting_type_capacity):
        """
        Specify the counting type
        Args:
            counting_type(String):Client Access/Capacity
        """
        self._select_counting_type_list(counting_type)

    @PageService()
    def add_license_types(self, license_list):
        """
        Adds license types
        Args:
            license_list(list/string): Specify the license type
        """
        self._click_licence_tab()
        self._select_license_types(license_list)
        self._click_button_add_license_type()

    @PageService()
    def remove_license_types(self, license_list):
        """
        Removes license types
        Args:
            license_list: Specify the license types
        """
        self._click_licence_tab()
        self._select_license_types(license_list)
        self._click_button_remove_license_type()

    @PageService()
    def add_agents(self, agents):
        """
        Adds agents
        Args:
            agents(list/String):Specify the agents
        """
        self._click_agents_tab()
        self._select_agents(agents)
        self._click_button_add_agent_type()

    @PageService()
    def remove_agents(self, agents):
        """
        Removes specified agents from agents tab
        Args:
            agents(list/String): Specify the agents
        """
        self._click_agents_tab()
        self._select_agents(agents)
        self._click_button_remove_agent_type()

    @PageService()
    def save(self):
        """
        Saves sku and verifies sku dialogue is closed
        """
        sleep(1)
        self._click_button_save()
        sleep(3)
        self._webconsole.wait_till_loadmask_spin_load()
        if self._billing_group_options.is_dialog_form_visible():
            self._click_button_close()
            self._log.error("Save panel didn't close checking notification for error")
            notifications = self._webconsole.get_all_unread_notifications()
            raise CVWebAutomationException("Notification:" + str(notifications))
