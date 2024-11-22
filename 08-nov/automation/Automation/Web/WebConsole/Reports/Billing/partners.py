from selenium.webdriver.common.by import By
"""
Classes and functions related to contract management partners page.
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


class PartnersAssociation(BillingGroupOptions):
    """
    Class can associate partners with discount percentage and billing cycle and can be used to
    generate the royalty report
    """

    @WebAction()
    def _select_partners(self, partner):
        """
        Select partners
        """
        partner_select = Select(self._driver.find_element(By.ID, "partnerList"))
        partners_list = [partners.text for partners in partner_select.options]
        if partner not in partners_list:
            raise CVWebAutomationException("Specified partner name couldn't be found:%s in "
                                           "partners list", partner)
        partner_select.select_by_visible_text(str(partner))

    @WebAction()
    def _set_discount_percentage(self, value):
        """
        Set discount percentage
        """
        self._driver.find_element(By.ID, "minFee").clear()
        self._driver.find_element(By.ID, "minFee").send_keys(value)

    @WebAction()
    def _select_billing_cycle(self, billing_cycle=BillingConstants.BILLING_CYCLE_QUARTERLY):
        """
        select billing cycle
        """
        if billing_cycle == BillingConstants.BILLING_CYCLE_QUARTERLY:
            Select(self._driver.find_element(By.ID, "billingTypeList")).select_by_visible_text(str(
                BillingConstants.BILLING_CYCLE_QUARTERLY))
        else:
            Select(self._driver.find_element(By.ID, "billingTypeList")).select_by_visible_text(str(
                BillingConstants.BILLING_CYCLE_MONTHLY))

    @WebAction()
    def _select_use_as_purchase_order(self, use_as_purchase_order=
                                      BillingConstants.USE_AS_PURCHASE_ORDER_YES):
        """
        Select purchase order yes/no
        """
        if use_as_purchase_order == BillingConstants.USE_AS_PURCHASE_ORDER_YES:
            self._driver.find_element(By.XPATH, "//input[@name='useAsPOType' and "
                                               "@value='0']").click()
        else:
            self._driver.find_element(By.XPATH, "//input[@name='useAsPOType' and "
                                               "@value='1']").click()

    @WebAction()
    def set_discount_percentage_in_edit_panel(self, value):
        """
        set discount percentage in edit panel
        """
        self._driver.find_element(By.ID, "editMinFee").clear()
        self._driver.find_element(By.ID, "editMinFee").send_keys(value)

    @WebAction()
    def _select_billing_cycle_in_edit_panel(self, billing_cycle=
                                            BillingConstants.BILLING_CYCLE_QUARTERLY):
        """
        Select billing cycle in edit panel
        """
        Select(self._driver.find_element(By.ID, "editBillingTypeList")).select_by_visible_text(str(
            billing_cycle))

    @WebAction()
    def _select_use_as_purchase_order_in_edit_panel(self, use_as_purchase_order=
                                                    BillingConstants.USE_AS_PURCHASE_ORDER_YES):
        """
        select use as purchase order in edit panel
        """
        if use_as_purchase_order == BillingConstants.USE_AS_PURCHASE_ORDER_YES:
            self._driver.find_element(By.XPATH, "//input[@name='editUseAsPOType' "
                                               "and @value='0']").click()
        else:
            self._driver.find_element(By.XPATH, "//input[@name='editUseAsPOType' "
                                               "and @value='1']").click()

    @PageService()
    def associate(self, partner, discount_percentage=None,
                  billing_cycle=BillingConstants.BILLING_CYCLE_MONTHLY,
                  use_as_purchase_order=BillingConstants.USE_AS_PURCHASE_ORDER_YES):
        """
        Associate partner
        Args:
            partner(string): Specify the partner name
            discount_percentage(String): Specify the discount percentage
            billing_cycle: Select billing cycle Monthly/Quarterly use BillingConstants
            use_as_purchase_order: True/False use as purchase order
        """
        self._select_partners(partner)
        if discount_percentage is not None:
            self._set_discount_percentage(discount_percentage)
        self._select_billing_cycle(billing_cycle)
        self._select_use_as_purchase_order(use_as_purchase_order)
        self._click_associate()

    @PageService()
    def edit_partner_association(self, partner_name, discount_percentage=None, billing_cycle=None,
                                 use_as_purchase_order=None):
        """
        Edits specific partners association
        Args:
            partner_name(string): Specify the partner name
            discount_percentage: specify the discount percentage
            billing_cycle: Specify the billing cycle Monthly/Quarterly
            use_as_purchase_order: True/False
        """
        self._click_edit(partner_name)
        sleep(2)
        if discount_percentage is not None:
            self.set_discount_percentage_in_edit_panel(discount_percentage)
        if billing_cycle is not None:
            self._select_billing_cycle_in_edit_panel(billing_cycle)
        if use_as_purchase_order is not None:
            self._select_use_as_purchase_order_in_edit_panel(use_as_purchase_order)
        self._click_button_save()

    @PageService()
    def delete_partner_association(self, partner):
        """
        Deletes specified partner
        Args:
            partner: Specify the partner name
        """
        self._click_delete(partner)
        sleep(2)
        self._click_button_dialogue_yes()


class ManagePartners(BillingGroupOptions):
    """
    Class used to manage partners, can add/edit/delete partners
    """

    @WebAction()
    def _click_add_partner(self):
        """
        click add service provider
        """
        self._driver.find_element(By.XPATH, "//*[@title = 'Add Contract']").click()

    @PageService()
    def add_partner(self, partner_name, description, service_providers):
        """
        adds partners
        Args:
            partner_name(string): Specify the partner name
            description(string): Specify the the description
            service_providers: provide list of service providers to select
        """
        partner_panel = PartnerPanel(self._webconsole)
        self._click_add_partner()
        partner_panel.set_partner_name(partner_name)
        partner_panel.set_partner_description(description)
        partner_panel.add_service_providers(service_providers)
        partner_panel.save()

    @PageService()
    def edit_partner(self, partner, new_partner_name=None, description=None,
                     add_service_providers_list=None,
                     remove_service_providers_list=None):
        """
        Edit partners
        Args:
            partner(string): existing partner name to edit
            new_partner_name(string): update the existing partner name
            description(string): update the description
            add_service_providers_list: specify the list of service providers to add
            remove_service_providers_list: specify the list of service providers to remove
        """
        self._click_edit(partner)
        partner_panel = PartnerPanel(self._webconsole)
        if new_partner_name is not None:
            partner_panel.set_partner_name(new_partner_name)
        if description is not None:
            partner_panel.set_partner_description(description)
        if add_service_providers_list is not None:
            partner_panel.add_service_providers(add_service_providers_list)
        if remove_service_providers_list is not None:
            partner_panel.add_service_providers(remove_service_providers_list)
        partner_panel.save()

    @PageService()
    def delete_partner(self, partner):
        """
        Deletes specified service provider
        Args:
            partner(string): Specify the service provider name

        Returns:

        """
        self._click_delete(partner)
        self._click_button_dialogue_yes()

    @PageService()
    def is_partner_exists(self, partner_name):
        """
        Checks specified partner exists
        Args:
            partner_name: Specify the partner name
        Returns:True/False
        """
        self._webconsole.wait_till_loadmask_spin_load()
        if self._get_element_with_text(partner_name):
            return True
        return False


class PartnerPanel:
    """
    Class can be used add or edit the partners
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
    def _set_partner_name(self, partner):
        """
        Set partner name
        """
        self._driver.find_element(By.ID, "aggregatorName").clear()
        self._driver.find_element(By.ID, "aggregatorName").send_keys(partner)

    @WebAction()
    def _set_partner_description(self, description):
        """
        Set partner description
        """
        self._driver.find_element(By.ID, "aggregatorDesc").clear()
        self._driver.find_element(By.ID, "aggregatorDesc").send_keys(description)

    @WebAction()
    def _select_service_providers(self, service_providers: list):
        """
        select service provider
        """
        for each_service_provider in service_providers:
            self._driver.find_element(By.XPATH, "//li[@data-name='" + each_service_provider +
                                               "']").click()

    @WebAction()
    def _click_add_item_button(self):
        """
        Click add item button
        """
        self._driver.find_element(By.XPATH, "//*[@class = 'addItemButton']").click()

    @WebAction()
    def _click_remove_item_button(self):
        """
        Click remove item button
        """
        self._driver.find_element(By.XPATH, "//*[@class = 'removeItemButton']").click()

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
        Click on button close
        """
        self._driver.find_element(By.XPATH, "//button/span[text()='Close']").click()
        sleep(1)

    @PageService()
    def set_partner_name(self, partner_name):
        """
        sets partner name
        Args:
            partner_name(string):specify the partner name
        """
        self._set_partner_name(partner_name)

    @PageService()
    def set_partner_description(self, description):
        """
        Sets partner description
        Args:
            description(String): Specify the partner description
        """
        self._set_partner_description(description)

    @PageService()
    def add_service_providers(self, service_providers):
        """
        Adds service providers
        Args:
            service_providers:List of service providers
        """
        self._select_service_providers(service_providers)
        self._click_add_item_button()

    @PageService()
    def remove_service_providers(self, service_providers):
        """
        Removes selected service providers
        Args:
            service_providers: list of service providers
        """
        self._select_service_providers(service_providers)
        self._click_remove_item_button()

    @PageService()
    def save(self):
        """
        Partners will be created
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
