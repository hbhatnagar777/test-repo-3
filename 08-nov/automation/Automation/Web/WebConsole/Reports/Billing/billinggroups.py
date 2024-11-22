from selenium.webdriver.common.by import By
"""
File is used to interact with contract management billing group options.
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


class BillingGroupAssociation(BillingGroupOptions):
    """
    Class contains Billing group association page functions
    """

    @WebAction()
    def _select_commcell_group(self, commcell_group):
        """
        Selects commcell group
        """
        commcell_group_select = Select(self._driver.find_element(By.ID, "customerList"))
        commcell_groups_list = [commcell_groups.text for commcell_groups in
                                commcell_group_select.options]
        if commcell_group not in commcell_groups_list:
            raise CVWebAutomationException("Specified commcell group name couldn't be found:%s",
                                           commcell_group)
        commcell_group_select.select_by_visible_text(commcell_group)

    @WebAction()
    def _select_billing_group(self, billing_group_name):
        """
        Selects billing group
        """
        billing_group_select = Select(self._driver.find_element(By.ID, "contractList"))
        billing_group_list = [billing_group.text for billing_group in billing_group_select.options]
        if billing_group_name not in billing_group_list:
            raise CVWebAutomationException("Specified billing group name couldn't be found:%s in "
                                           "billing group list", billing_group_name)
        billing_group_select.select_by_visible_text(billing_group_name)

    @WebAction()
    def _select_billing_group_in_edit_association(self, billing_group_name):
        """
        Selects billings group in edit association panel
        """
        billing_group_select = Select(self._driver.find_element(By.ID, "editContractList"))
        billing_group_list = [billing_group.text for billing_group in billing_group_select.options]
        if billing_group_name not in billing_group_list:
            raise CVWebAutomationException("Specified billing group name couldn't be found:%s in "
                                           "billing group list", billing_group_name)
        billing_group_select.select_by_visible_text(billing_group_name)

    @WebAction()
    def _set_vd_lower_limit(self, lower_limit=None):
        """
        Sets the Volume discount lower limit
        """
        if lower_limit == 0 or lower_limit is None or lower_limit == "":
            self._log.info("Leaving blank for lower limit")
        else:
            self._driver.find_element(By.ID, "vdLowerLimit").clear()
            self._driver.find_element(By.ID, "vdLowerLimit").send_keys(lower_limit)

    @WebAction()
    def _set_vd_upper_limit(self, upper_limit=None):
        """
        Sets the Volume discount upper limit
        """
        if upper_limit == 0 or upper_limit is None or upper_limit == "":
            self._log.info("Leaving blank for upper limit")
        else:
            self._driver.find_element(By.ID, "vdUpperLimit").clear()
            self._driver.find_element(By.ID, "vdUpperLimit").send_keys(upper_limit)

    @WebAction()
    def _set_discount_percentage(self, disc_percent=0):
        """
        Sets the Volume discount percentage
        """
        self._driver.find_element(By.ID, "vdDiscount").send_keys(disc_percent)

    @WebAction()
    def _click_button_add_vol_discount(self):
        """
        Click on Add Volume Discount
        """
        self._driver.find_element(By.ID, "addVdDetailBtn").click()

    @WebAction()
    def _click_button_clear_vol_discount(self):
        """
        Clear Volume Discount
        """
        self._driver.find_element(By.ID, "clearVdDetailBtn").click()

    @PageService()
    def associate(self, commcell_group=None, billing_group=None):
        """
        Associates specified commcell group with billing group
        Args:
            commcell_group(String): Specify the commcell group
            billing_group(String): Specify the billing group
        """
        if commcell_group is not None:
            self._select_commcell_group(commcell_group)
        if billing_group is not None:
            self._select_billing_group(billing_group)
        self._click_associate()

    @PageService()
    def edit_association(self, commcell_group_name, billing_group_name):
        """
        Edits Association
        Args:
            commcell_group_name(String): Specify the commcell group name
            billing_group_name(String): Specify the billing group name
        """
        self._click_edit(commcell_group_name)
        self._select_billing_group_in_edit_association(billing_group_name)
        self._set_vd_lower_limit(0)
        self._set_vd_upper_limit(0)
        self._set_discount_percentage(10)
        self._click_button_add_vol_discount()
        self._click_button_save()

    @PageService()
    def delete_association(self, name):
        """
        Deletes specified association
        Args:
            name(String): Provide association name to delete
        """
        self._click_delete(name)
        self._click_button_dialogue_yes()

    @PageService()
    def is_association_exists(self, commcell_group_name):
        """
        Checks specified association exists
        Args:
            commcell_group_name(string): Specify the commcell group name
        Returns:True/False
        """
        self._webconsole.wait_till_loadmask_spin_load()
        if self._get_element_with_text(commcell_group_name):
            return True
        return False


class ManageBillingGroups(BillingGroupOptions):
    """
    Functions used to manage billing group(Add/edit/delete billing groups)
    """

    @WebAction()
    def _click_add_billing_group(self):
        """
        clicks on add billing group
        """
        self._driver.find_element(By.ID, "addContractButton").click()

    @WebAction()
    def _get_approved_column_element_of_billing_group(self, billing_group):
        """
        Gets approved column elements
        """
        approved_check_mark = self._driver.find_element(By.XPATH, 
            "//td[@title='" + str(billing_group) + "' and @data-label='Billing Group']/..//td"
                                                   "[@data-label='Approved']/div")
        return approved_check_mark

    @WebAction()
    def _mark_approved(self, billing_group_name):
        """
        Specified billing group will be marked as approved
        """
        approved_element = self._get_approved_column_element_of_billing_group(billing_group_name)
        status = approved_element.get_attribute("data-state")
        if status == "unchecked":
            approved_element.click()
        else:
            self._log.info("Already in Approved state")

    @PageService()
    def access_add_billing_group(self):
        """
        New billing group panel will be opened
        Returns:BillingGroupPanel object
        """
        self._click_add_billing_group()
        billing_group = BillingGroupPanel(self._webconsole)
        return billing_group

    @PageService()
    def edit_billing_group(self, billing_group_name):
        """
        Edit existing billing group name
        Args:
            billing_group_name(string): Specify the billing group name
        Returns:BillingGroupPanel object
        """
        self._click_edit(billing_group_name)
        billing_group = BillingGroupPanel(self._webconsole)
        return billing_group

    @PageService()
    def delete_billing_group(self, billing_group):
        """
        Deletes specified billing group
        Args:
            billing_group(string): Billing group name
        """
        self._click_delete(billing_group)
        self._click_button_dialogue_yes()

    @PageService()
    def is_billing_group_exists(self, billing_group_name):
        """
        Checks if billing group specified billing group exists
        Args:
            billing_group_name(String): Specify Billing group name

        Returns:True/False
        """
        self._webconsole.wait_till_loadmask_spin_load()
        if self._get_element_with_text(billing_group_name):
            return True
        return False


class BillingGroupPanel:
    """
    Can used for editing or creating new billing group
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
    def _fill_billing_group_name(self, name):
        """
        Sets billing group name
        """
        self._driver.find_element(By.ID, "contractName").clear()
        self._driver.find_element(By.ID, "contractName").send_keys(name)

    @WebAction()
    def _fill_billing_group_description(self, description):
        """
        Sets billing group description
        """
        self._driver.find_element(By.ID, "contractDesc").clear()
        self._driver.find_element(By.ID, "contractDesc").send_keys(description)

    @WebAction()
    def _select_currency(self, currency='USD'):
        """
        Selects currency
        """
        Select(self._driver.find_element(By.ID, "contractCurrencyList")).\
            select_by_visible_text(str(currency))

    @WebAction()
    def _select_sku(self, sku):
        """
        Selects sku
        """
        sku_select = Select(self._driver.find_element(By.ID, "billingGroupList"))
        skus_list = [skus.text for skus in sku_select.options]
        if sku not in skus_list:
            raise CVWebAutomationException("Specified sku name couldn't be found:%s in "
                                           "skus list", sku)
        sku_select.select_by_visible_text(str(sku))

    @WebAction()
    def _set_base_line(self, base_line):
        """
        Sets base line value
        """
        self._driver.find_element(By.ID, "initialQuantity").clear()
        self._driver.find_element(By.ID, "initialQuantity").send_keys(base_line)

    @WebAction()
    def _set_unit_price(self, price):
        """
        Sets unit price value
        """
        self._driver.find_element(By.ID, "price").clear()
        self._driver.find_element(By.ID, "price").send_keys(price)

    @WebAction()
    def _set_lower_limit(self, value):
        """
        Sets lower limit value
        """
        self._driver.find_element(By.ID, "lowerLimit").clear()
        self._driver.find_element(By.ID, "lowerLimit").send_keys(value)

    @WebAction()
    def _set_upper_limit(self, value=None):
        """
        Sets upper limit value
        """
        if value == 0 or value is None or value == "":
            self._log.info("Leaving blank for upper limit")
        else:
            self._driver.find_element(By.ID, "upperLimit").clear()
            self._driver.find_element(By.ID, "upperLimit").send_keys(value)

    @WebAction()
    def _click_button_add_sku_price(self):
        """
        Clicks on add sku button
        """
        self._driver.find_element(By.ID, "addContractDetailBtn").click()

    @WebAction()
    def _include_in_volume_discount(self, vol_discount):
        """
        Clicks on include in volume discount button
        """
        vol_disc_select = Select(self._driver.find_element(By.ID, "IncludeInVDList"))
        vol_disc_select.select_by_visible_text(vol_discount)

    @WebAction()
    def _click_button_clear(self):
        """
        Clears the entries in sku panel
        """
        self._driver.find_element(By.ID, "clearContractDetailBtn").click()

    @WebAction()
    def _click_button_save(self):
        """
        Click on save
        """
        self._driver.find_element(By.XPATH, "//button/span[text()='Save']").click()
        sleep(2)

    @WebAction()
    def _click_button_close(self):
        """
        Click on close button
        """
        self._driver.find_element(By.XPATH, "//button/span[text()='Close']").click()
        sleep(2)

    @PageService()
    def set_billing_group_name(self, name):
        """
        Set billing group name
        Args:
            name(string): Specify the name of billing group
        """
        self._fill_billing_group_name(name)

    @PageService()
    def set_billing_group_description(self, description):
        """
        Set billing group description
        Args:
            description: Specify the description
        """
        self._fill_billing_group_description(description)

    @PageService()
    def save(self):
        """
        Saves the changes made on billing group
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

    @PageService()
    def close(self):
        """
        Close the billing group panel
        """
        self._click_button_close()

    @PageService()
    def add_sku_price(self):
        """
        adds sku price in billing group panel
        Args:
            value(string): Specify the price
        """
        self._click_button_add_sku_price()

    @PageService()
    def include_in_volume_discount(self,vol_discount_value):
        """
        Includes in volume discount in billing group panel
        Args:
            value(string): Specify Yes or No
        """
        self._include_in_volume_discount(vol_discount_value)

    @PageService()
    def clear(self):
        """
        Clears the entries from billing group
        """
        self._click_button_clear()

    @PageService()
    def set_upper_limit(self, upper_limit_value):
        """
        Sets upper lime value
        Args:
            upper_limit_value:Specify upper limit value
        """
        self._set_upper_limit(upper_limit_value)

    @PageService()
    def set_lower_limit(self, lower_limit_value):
        """
        Sets lower limit value
        Args:
            lower_limit_value:Specify the lower limit value
        """
        self._set_lower_limit(lower_limit_value)

    @PageService()
    def set_unit_price(self, price):
        """
        Sets unit price value
        Args:
            price: Specify the unit price value
        """
        self._set_unit_price(price)

    @PageService()
    def select_sku(self, sku_name):
        """
        selects specified  sku
        Args:
            sku_name(string): Specify the sku name
        """
        self._select_sku(sku_name)

    @PageService()
    def set_base_line(self, base_line_value):
        """
        Sets base line value
        Args:
            base_line_value(string): Specify the base line value
        """
        self._set_base_line(base_line_value)

    @PageService()
    def select_currency(self, currency='USD'):
        """
        selects specified currency
        Args:
            currency: Specify the currency type
        """
        self._select_currency(currency)
