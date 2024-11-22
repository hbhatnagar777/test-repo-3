from selenium.webdriver.common.by import By
"""
Classes and functions related to contract management service provider page.
"""
from time import sleep

from selenium.webdriver.support.ui import Select
from Web.Common.exceptions import CVWebAutomationException
from Web.WebConsole.Reports.Billing.common import BillingGroupOptions
from Web.WebConsole.Reports.Billing.common import BillingConstants
from Web.Common.page_object import (
    WebAction, PageService
)
from AutomationUtils import logger, config

_CONFIG = config.get_config()


class ServiceProvider(BillingGroupOptions):
    """
    Function used communicate with service provider page
    """

    @WebAction()
    def _select_service_provider(self, service_provider_name):
        """
        Select service provider
        """
        service_provider_select = Select(self._driver.find_element(By.ID, "aggregatorList"))
        service_provider_list = [service_providers.text for service_providers in
                                 service_provider_select.options]
        if service_provider_name not in service_provider_list:
            raise CVWebAutomationException("Specified service provider name couldn't be found:%s"
                                           % service_provider_name)
        service_provider_select.select_by_visible_text(str(service_provider_name))

    @WebAction()
    def _set_min_fee(self, fee=None):
        """
        Sets minimum fee
        """
        if fee is not None:
            self._driver.find_element(By.ID, "minFee").clear()
            self._driver.find_element(By.ID, "minFee").send_keys(fee)

    @WebAction()
    def _select_billing_cycle(self, billing_cycle=BillingConstants.BILLING_CYCLE_MONTHLY):
        """
        Select billing cycle
        """
        if billing_cycle == BillingConstants.BILLING_CYCLE_QUARTERLY:
            Select(self._driver.find_element(By.ID, "billingTypeList")).select_by_visible_text(str(
                BillingConstants.BILLING_CYCLE_QUARTERLY))
        else:
            Select(self._driver.find_element(By.ID, "billingTypeList")).select_by_visible_text(str(
                BillingConstants.BILLING_CYCLE_MONTHLY))

    @WebAction()
    def _select_radio_button_use_as_purchase_order_yes(self):
        """
        select use as purchase order 'Yes' button
        """
        self._driver.find_element(By.XPATH, "//input[@name='useAsPOType' and @value='0']").click()

    @WebAction()
    def _select_radio_button_use_as_purchase_order_no(self):
        """
        Select use as purchase order 'no' button
        """
        self._driver.find_element(By.XPATH, "//input[@name='useAsPOType' and @value='1']").click()

    @WebAction()
    def _set_minimum_fee_in_edit_panel(self, fee):
        """
        set min fee value
        """
        self._driver.find_element(By.XPATH, "//*[@id = 'editMinFee']").clear()
        self._driver.find_element(By.XPATH, "//*[@id = 'editMinFee']").send_keys(fee)

    @WebAction()
    def _select_billing_cycle_in_edit_panel(self, cycle_type=
                                            BillingConstants.BILLING_CYCLE_MONTHLY):
        """
        select billing cycle in edit panel
        """
        Select(self._driver.find_element(By.ID, "editBillingTypeList")).select_by_visible_text(str(
            cycle_type))

    @WebAction()
    def _select_use_as_purchase_order_in_edit_panel(self, use_as_purchase_order=
                                                    BillingConstants.USE_AS_PURCHASE_ORDER_YES):
        """
        Select use as purchase order yes/no
        """
        if use_as_purchase_order == BillingConstants.USE_AS_PURCHASE_ORDER_YES:
            self._driver.find_element(By.XPATH, "//input[@name='editUseAsPOType' "
                                               "and @value='0']").click()
        else:
            self._driver.find_element(By.XPATH, "//input[@name='editUseAsPOType' "
                                               "and @value='1']").click()

    @PageService()
    def _select_use_as_purchase_order_status(self, status=BillingConstants.
                                             USE_AS_PURCHASE_ORDER_YES):
        """
        Sets generated royalty report to be used as Purchase or not
        Args:
            status: Yes/No
        """
        if status == BillingConstants.USE_AS_PURCHASE_ORDER_YES:
            self._select_radio_button_use_as_purchase_order_yes()
        else:
            self._select_radio_button_use_as_purchase_order_no()

    @PageService()
    def associate(self, service_provider, minimum_fee=None,
                  billing_cycle=BillingConstants.BILLING_CYCLE_MONTHLY,
                  use_as_purchase_oder=BillingConstants.USE_AS_PURCHASE_ORDER_YES):
        """
        Associate Specified service provider with minimum fee and billing cycle
        Args:
            service_provider(String): Specify the service provider
            minimum_fee(Number): Specify the minimum fee
            billing_cycle:Select Monthly/Quarterly
            use_as_purchase_oder:Yes/No
        """
        self._select_service_provider(service_provider)
        if minimum_fee is not None:
            self._set_min_fee(minimum_fee)
        self._select_billing_cycle(billing_cycle)
        self._select_use_as_purchase_order_status(use_as_purchase_oder)
        self._click_associate()

    @PageService()
    def edit_association(self, service_provider, fee=None, billing_cycle=None,
                         user_as_purchase_order=None):
        """
        Can be used to edit the association.
        Args:
            service_provider(String): Specify the service provider name
            fee(Number): Updated fee
            billing_cycle(String): Monthly/Quarterly
            user_as_purchase_order:Yes/No
        """
        self._click_edit(service_provider)
        if fee is not None:
            self._set_minimum_fee_in_edit_panel(fee)
        if billing_cycle is not None:
            self._select_billing_cycle_in_edit_panel(billing_cycle)
        if user_as_purchase_order is not None:
            self._select_use_as_purchase_order_in_edit_panel(user_as_purchase_order)
        self._click_button_save()

    @PageService()
    def delete_association(self, service_provider):
        """
        Deletes specified association
        Args:
            service_provider(String): Specify the service provider name to be deleted
        """
        self._click_delete(service_provider)
        self._click_button_dialogue_yes()


class ManageServiceProvider(BillingGroupOptions):
    """
    Manages service providers like add/delete/edit.
    """
    def __init__(self, webconsole):
        super().__init__(webconsole)
        self._webconsole = webconsole
        self.service_provider = ServiceProviderPanel(self._webconsole)

    @WebAction()
    def _click_add_service_provider(self):
        """
        click add service provider
        """
        self._driver.find_element(By.XPATH, "//*[@title = 'Add Contract']").click()

    @PageService()
    def add_service_provider(self, service_provider_name, description, commcell_groups):
        """
        Add specified service provider
        Args:
            service_provider_name(string):Specify the service provider name
            description(String): Specify the description
            commcell_groups(String):Specify the commcell group name
        """
        self._click_add_service_provider()
        self.service_provider.set_service_provider_name(service_provider_name)
        self.service_provider.set_description(description)
        self.service_provider.add_commcell_groups(commcell_groups)
        self.service_provider.save()

    @PageService()
    def edit_service_provider(self, service_provider_name, service_provider_new_name=None,
                              description=None, commcell_groups_to_add=None,
                              commcell_groups_to_remove=None):
        """

        Args:
            service_provider_name(String): Specify the existing service provider name
            service_provider_new_name(): Specify the new service provider name
            description: Specify the description
            commcell_groups_to_add: Specify the list of commcell groups to be added
            commcell_groups_to_remove: Specify the list of commcell groups to be removed
        """
        self._click_edit(service_provider_name)
        if service_provider_new_name is not None:
            self.service_provider.set_service_provider_name(service_provider_new_name)
        if description is not None:
            self.service_provider.set_description(description)
        if commcell_groups_to_add is not None:
            self.service_provider.add_commcell_groups(commcell_groups_to_add)
        if commcell_groups_to_remove is not None:
            self.service_provider.remove_commcell_groups(commcell_groups_to_remove)
        self.service_provider.save()

    @PageService()
    def delete_service_provider(self, service_provider):
        """
        Deletes service provider
        Args:
            service_provider(String): Specify the service provider name
        """
        self._click_delete(service_provider)
        self._click_button_dialogue_yes()

    @PageService()
    def is_service_provider_exists(self, service_provider_name):
        """
        Checks specified service provider exists
        Args:
            service_provider_name: Specify the service provider name
        Returns:True/False
        """
        self._webconsole.wait_till_loadmask_spin_load()
        if self._get_element_with_text(service_provider_name):
            return True
        return False


class ServiceProviderPanel:
    """
    Functions used for Adding new service provider
    """
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
    def _set_service_provider_name(self, service_provider):
        """
        set service provider name
        """
        self._driver.find_element(By.ID, "aggregatorName").send_keys(service_provider)

    @WebAction()
    def _set_description(self, description):
        """
        Set description
        """
        self._driver.find_element(By.ID, "aggregatorDesc").send_keys(description)

    @WebAction()
    def _select_commcell_group(self, commcell_groups: list):
        """
        Select commcell group
        """
        for each_commcell_group in commcell_groups:
            self._driver.find_element(By.XPATH, "//li[@data-name='" + each_commcell_group +
                                               "']").click()

    @WebAction()
    def _click_button_add_commcell_group(self):
        """
        Click on add commcell group button
        """
        self._driver.find_element(By.XPATH, "//*[@class='addItemButton']").click()

    @WebAction()
    def _click_button_remove_commcell_group(self):
        """
        Click on remove commcell group button
        """
        self._driver.find_element(By.XPATH, "//*[@class='removeItemButton']").click()

    @WebAction()
    def _click_button_save(self):
        """
        Click button save
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
    def set_service_provider_name(self, name):
        """
        Sets service provider name
        Args:
            name(String): Specify the service provider name
        """
        self._set_service_provider_name(name)

    @PageService()
    def set_description(self, description):
        """
        Sets service provider description
        Args:
            description(String):Specify the description
        """
        self._set_description(description)

    @PageService()
    def add_commcell_groups(self, commcell_groups):
        """
        Selects specified commcell groups for creating/editing service provider
        Args:
            commcell_groups(list): List of commcell groups
        """
        self._select_commcell_group(commcell_groups)
        self._click_button_add_commcell_group()

    @PageService()
    def remove_commcell_groups(self, commcell_groups):
        """
        Removes specified commcell groups for creating/editing service provider
        Args:
            commcell_groups(List): list of commcell groups
        """
        self._select_commcell_group(commcell_groups)
        self._click_button_remove_commcell_group()

    @PageService()
    def save(self):
        """
        Saves service provider and verifies service provider dialogue is closed
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
