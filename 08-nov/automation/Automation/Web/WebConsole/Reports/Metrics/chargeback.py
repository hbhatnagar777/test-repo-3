from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Operations common to chargeback and its related reports goes here"""

from time import sleep

from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select

from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService


class MonoState:
    """Abstract class for singleton"""
    _state = {}

    def __new__(cls):
        self = super(MonoState, cls).__new__(cls)
        self.__dict__ = cls._state
        return self


class GlobalPrice(MonoState):
    """A Singleton Class which is used to manipulate the Global Price"""

    def __init__(self):
        self.__driver = None
        self.__webconsole = None

    @property
    def _driver(self):
        if self.__driver is None:
            raise ValueError("driver not initialized, was add_global called ?")
        return self.__driver

    @property
    def _webconsole(self):
        if self.__webconsole is None:
            raise ValueError("webconsole not initialized, was add_global called ?")
        return self.__webconsole

    @_driver.setter
    def _driver(self, value):
        self.__driver = value

    @_webconsole.setter
    def _webconsole(self, value):
        self.__webconsole = value

    def configure_global_price(self, webconsole):
        """Configures the global price object

        Do not call this method explicitly, it would automatically be called
        when you add global price to chargeback
        """
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver

    @WebAction()
    def __click_discount(self, set_):
        """Clicks discount checkbox"""
        checkbox = self._driver.find_element(By.XPATH, "//*[@id='discount']")
        if checkbox.is_selected() != set_:
            checkbox.click()

    @WebAction()
    def __is_discount_selected(self):
        """Returns True if checkbox is selected"""
        checkbox = self._driver.find_element(By.XPATH, "//*[@id='discount']")
        return True if checkbox.is_selected else False

    @WebAction()
    def __set_percentage(self, percentage):
        """Set percentage"""
        text_field = self._driver.find_element(By.XPATH, "//*[@id='discountpercent']")
        text_field.clear()
        text_field.send_keys(percentage)

    @WebAction()
    def __get_percentage(self):
        """Get percentage"""
        text_field = self._driver.find_element(By.XPATH, "//*[@id='discountpercent']")
        return text_field.get_attribute("value")

    @WebAction()
    def __set_discount_size(self, storage_limit):
        """Set discount size"""
        text_field = self._driver.find_element(By.XPATH, "//*[@id='discountsize']")
        text_field.clear()
        text_field.send_keys(storage_limit)

    @WebAction()
    def __get_discount_size(self):
        """Get discount size"""
        text_field = self._driver.find_element(By.XPATH, "//*[@id='discountsize']")
        return text_field.get_attribute("value")

    @WebAction()
    def __select_entity(self, entity):
        """Selects the given entity from the drop down"""
        element = self._driver.find_element(By.XPATH, "//*[@id='discountlevel']")
        drop_down = Select(element)
        drop_down.select_by_visible_text(entity)

    @WebAction()
    def __get_selected_entity(self):
        """Returns the selected entity from the drop down"""
        select = Select(self._driver.find_element(By.XPATH, "//*[@id='discountlevel']"))
        selected_option = select.first_selected_option
        return selected_option.text

    @WebAction()
    def __click_button(self, button_name):
        """Clicks save and recalculate"""
        button = self._driver.find_element(By.XPATH, f"//span[contains(text(),'{button_name}')]")
        button.click()

    @WebAction()
    def __set_field(self, label, value):
        """Sets the given input field with the given value"""
        text_field = self._driver.find_element(By.XPATH, 
            f"//label[contains(text(),'{label}')]/following-sibling::input")
        text_field.clear()
        text_field.send_keys(value)

    @WebAction()
    def __get_field(self, label):
        """Sets the given input field with the given value"""
        text_field = self._driver.find_element(By.XPATH, 
            f"//label[contains(text(),'{label}')]/following-sibling::input")
        return text_field.get_attribute("value")

    @PageService()
    def set_front_end_cost(self, backup, archive):
        """Sets the front end cost per TB

        Args:
            backup (str)  : backup cost

            archive (str) : archive cost

        """
        self.__set_field("Backup", backup)
        self.__set_field("Archive", archive)

    @PageService()
    def set_current_month_or_week_cost(self, primary_app, protected_app, data_on_media):
        """Sets the current month or week cost per TB

        Args:
            primary_app     (str):    primary application cost

            protected_app   (str):    protected application cost

            data_on_media   (str):    data on media cost

        """
        self.__set_field("Primary Application", primary_app)
        self.__set_field("Protected Application", protected_app)
        self.__set_field("Data on Media", data_on_media)

    @PageService()
    def set_lifetime_cost(self, total_protected_app, total_data_on_media):
        """Sets lifetime cost per TB

        Args:
            total_protected_app (str):  total protected application cost

            total_data_on_media (str):  total data on media cost

        """
        self.__set_field("Total Protected Application", total_protected_app)
        self.__set_field("Total Data on Media", total_data_on_media)

    @PageService()
    def set_additional_cost(self, per_client, per_subclient):
        """Sets additional cost

        Args:
            per_client      (str): per client ocst

            per_subclient   (str): per subclient cost

        """
        self.__set_field("Per Client", per_client)
        self.__set_field("Per SubClient", per_subclient)

    @PageService()
    def discount(self, set_=True, percentage=None, storage_limit=None, entity=None):
        """Sets discount on the given entity

        Args:
            set_ (bool):  Sets the discount

                Default : True

            percentage(str): Percentage of discount

                Default : None [Leaves the preloaded discount]

            storage_limit(str): Limit of storage for which the discount is applied

                Default : None [Leaves the preloaded size]

            entity(str) :  Entity for which the discount is applied (Client , Subclinet)

                Default : None [Leaves the preloaded entity]

        """
        self.__click_discount(set_)
        if set_:
            self.__set_percentage(percentage)
            self.__set_discount_size(storage_limit)
            self.__select_entity(entity)

    @PageService()
    def save_and_recalculate(self):
        """Saves and recalculates the Global Price"""
        self.__click_button("Save & Re-calculate")
        self._webconsole.wait_till_load_complete()

    @PageService()
    def get_price_details(self):
        """Returns the Global Price details"""
        return {
            "Backup": self.__get_field("Backup"),
            "Archive": self.__get_field("Archive"),
            "Primary Application": self.__get_field("Primary Application"),
            "Protected Application": self.__get_field("Protected Application"),
            "Data on Media": self.__get_field("Data on Media"),
            "Total Protected Application": self.__get_field("Total Protected Application"),
            "Total Data on Media": self.__get_field("Total Data on Media"),
            "Per Client": self.__get_field("Per Client"),
            "Per SubClient": self.__get_field("Per SubClient"),
            "Discount Percentage": self.__get_percentage(),
            "Discount Size": self.__get_discount_size(),
            "Discount Entity": self.__get_selected_entity(),
            "Discount Selection": self.__is_discount_selected()
        }

    @PageService()
    def close(self):
        """Closes the Global Price"""
        self.__click_button("Close")


class Chargeback:
    """This class holds all operations on Chargeback report"""

    def __init__(self, webconsole):
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver

    @WebAction()
    def __click_global_price(self):
        """Clicks Global Price"""
        element = self._driver.find_element(By.XPATH, "//*[@id='global_price']")
        element.click()

    @WebAction()
    def __click_billing_tags(self):
        """Clicks Global Price"""
        element = self._driver.find_element(By.XPATH, "//*[@id='tagsSettings']")
        element.click()

    @WebAction()
    def __select_drop_down(self, drop_down_name, group_by):
        """Selects the given dropdown with the given value"""
        element = self._driver.find_element(By.XPATH, f"//*[contains(text(),'{drop_down_name}')]//select")
        drop_down = Select(element)
        drop_down.select_by_visible_text(group_by)

    @WebAction()
    def __select_time_interval(self, time_interval):
        """Selects the time interval"""
        interval = {
            "Monthly": "1",
            "Weekly": "2",
            "Daily": "4"
        }
        try:
            value = interval[time_interval]
        except KeyError:
            raise ValueError("Value not found")
        self._driver.find_element(By.XPATH, f"//span//input[@value='{value}']").click()

    @WebAction()
    def __select_exclude_deconfigured_subclients(self, do_check):
        """Selects the Exclude Deconfigured Subclients checkbox if the passed argument is true"""
        checkbox = self._driver.find_element(By.XPATH, "//*[@id='excludeDeSCs']")
        if checkbox.is_selected() != do_check:
            checkbox.click()

    @WebAction()
    def __include_dr_subclients(self, do_check):
        """Selects the Exclude Deconfigured Subclients checkbox if the passed argument is true"""
        checkbox = self._driver.find_element(By.XPATH, "//*[@id='includeDRSubclients']")
        if checkbox.is_selected() != do_check:
            checkbox.click()

    @WebAction()
    def __select_display_fet(self, display_fet):
        """Selects the Display FET checkbox if the passed argument is true"""
        checkbox = self._driver.find_element(By.XPATH, "//*[@id='showFET']")
        if checkbox.is_selected() != display_fet:
            checkbox.click()

    @WebAction()
    def __click_button(self, name):
        """Clicks the given button"""
        button = self._driver.find_element(By.XPATH, f"//a[contains(text(),'{name}')]")
        button.click()

    @WebAction()
    def __get_time_frame_value(self):
        """Reads time frame value"""
        time_frame = self._driver.find_element(By.XPATH, "(//*[@id='reportSummary']//td)[2]")
        return time_frame.text

    @PageService()
    def read_time_frame_value(self):
        """Read time frame value present in chargeback report"""
        return self.__get_time_frame_value()

    @PageService()
    def add_global_price(self, global_price):
        """Adds the Global Price to the ChargeBack Report.

        Args:
            global_price (GlobalPrice) : instance of the GlobalPrice class

        """
        if not isinstance(global_price, GlobalPrice):
            raise TypeError("Invalid component type")
        self.open_global_price()
        global_price.configure_global_price(self._webconsole)

    @PageService()
    def generate_report(
            self, group_by, size_unit="TB", time_interval="Monthly",
            exclude_deconfigured_subclients=False, display_fet=False, include_dr_subclients = False
    ):
        """Generates the report

        Args:
            group_by(str): Clause to group the entities in the chargeback report

            size_unit(str): Size unit

                Default: TB

            time_interval(str): Time interval

                Default: Monthly

            exclude_deconfigured_subclients(bool): Exclude Deconfigured Subclients

                Default: False

            display_fet(bool): Display FET for clients with both VSA and other agents installed

                Default: False

        """
        self.__select_drop_down("Group By", group_by)
        self.__select_drop_down("Size Unit", size_unit)
        self.__select_time_interval(time_interval)
        self.__select_exclude_deconfigured_subclients(exclude_deconfigured_subclients)
        self.__select_display_fet(display_fet)
        self.__include_dr_subclients(include_dr_subclients)
        self.__click_button("Generate Report")
        self._webconsole.wait_till_load_complete()

    @PageService()
    def open_chargeback_trends(self):
        """Opens the chargeback trends report"""
        self.__click_button("Chargeback Trends")
        self._webconsole.wait_till_load_complete()

    @PageService()
    def open_global_price(self):
        """Opens Global Price"""
        self.__click_global_price()

    @PageService()
    def access_billing_tags(self):
        """Opens Manage Billing Tags report"""
        self.__click_billing_tags()
        self._webconsole.wait_till_load_complete()


class ManageBillingTags:
    """This contains methods for Manage Billing tags page"""

    def __init__(self, webconsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole

    def add_new_billing_tag(self, tag):
        """Adds new billing tag

        Args:
            tag(Tag): instance of the Tag class

        """
        if not isinstance(tag, Tag):
            raise TypeError("Invalid component type")
        self.__click_new("Billing Tags")
        self._webconsole.wait_till_load_complete()
        tag.configure_tag(self._webconsole)

    @WebAction()
    def __click_new(self, table_name):
        """Clicks new button on the given table"""
        button = self._driver.find_element(By.XPATH, f"//span[.='{table_name}']/ancestor::h1//*[@value='New']")
        button.click()

    @WebAction()
    def __click_save(self):
        """Clicks save button"""
        save = self._driver.find_element(By.XPATH, "//*[@title='Save']")
        save.click()

    @WebAction()
    def __click_trash_icon_for_billing_tag(self, name):
        """Clicks the trash icon"""
        delete = self._driver.find_element(By.XPATH, f"//*[@title='{name}']//*[@title='Delete']")
        delete.click()

    @WebAction()
    def __click_trash_icon(self, name):
        """Clicks the trash icon"""
        delete = self._driver.find_element(By.XPATH, f"//*[@title='{name}']/following-sibling::td//span")
        delete.click()

    @WebAction()
    def __select_entity(self, entity_name, value):
        """Selects the given value on the given entity"""
        element = self._driver.find_element(By.XPATH, f"//*[@data-label='{entity_name}']//input")
        if value == "":
            element.click()
            element.send_keys(Keys.ARROW_DOWN + "\n")
        else:
            element.click()
            sleep(2)
            element.send_keys(value)
            sleep(5)
            element.send_keys(Keys.ARROW_DOWN + "\n")
            sleep(2)

    @WebAction()
    def __select_tag(self, level, tag_name):
        """Selects the given tag name"""
        element = self._driver.find_element(By.XPATH, 
            f"//*[contains(text(),'{level}')]/ancestor::h1//select[@id='tagsList']")
        drop_down = Select(element)
        drop_down.select_by_visible_text(tag_name)
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def __hover(self, table_name, tag_name):
        """Fetches all objects with the given tag name"""
        element = self._driver.find_element(By.XPATH, 
            f"//span[.='{table_name}']/ancestor::h1/following-sibling::div//td[.='{tag_name}']")
        action_chain = ActionChains(self._driver)
        action = action_chain.move_to_element(element)
        action.perform()

    @WebAction()
    def __get_tag_count(self, table_name, tag_name):
        """Fetches all objects with the given tag name"""
        return len(self._driver.find_elements(By.XPATH, 
            f"//span[.='{table_name}']/ancestor::h1/following-sibling::div//td[.='{tag_name}']"))

    @WebAction()
    def __has_tag(self, table_name, tag_name):
        """Checks for the given tag in the given table"""
        element = self._driver.find_elements(By.XPATH, 
            f"//span[.='{table_name}']/ancestor::h1/following-sibling::div//td[.='{tag_name}']")
        return True if element else False

    @PageService()
    def has_billing_tag(self, name):
        """Returns true if the billing tag is found

        Args:
            name(str): Name of the tag to be deleted

        """
        return self.__has_tag("Billing Tags", name)

    @PageService()
    def delete_billing_tag(self, name):
        """Deletes the billing tag

        Args:
            name(str): Name of the tag to be deleted

        """
        self.__hover("Billing Tags", name)
        self.__click_trash_icon_for_billing_tag(name)
        alert = self._driver.switch_to.alert
        sleep(1)
        alert.accept()
        error = self._webconsole.get_all_error_notifications()
        if error:
            raise CVWebAutomationException(error)

    @PageService()
    def add_associate_billing_tag(self, tag_name, commcell, client_gp=None, client=None,
                                  agent=None, instance=None, backupset=None, subclient=None):
        """Associates billing tag

        Args:
            tag_name    (str): Name of the tag

                Default: None

            commcell    (str): Name of the commcell

                Default: None

            client_gp   (str): Name of the client group

                Default: None

            client      (str): Name of the client

                Default: None

            agent       (str): Name of the agent

                Default: None

            instance    (str): Name of the instance

                Default: None

            backupset   (str): Name of the backupset

                Default: None

            subclient   (str): Name of the subclient

                Default: None

        """
        self.__select_tag("Associate Billing Tags", tag_name)
        self.__click_new("Associate Billing Tags")
        self.__select_entity("CommCell Name", commcell)
        if client_gp:
            self.__select_entity("Client Group", client_gp)
        if client:
            self.__select_entity("Client", client)
        if agent:
            self.__select_entity("Agent", agent)
        if instance:
            self.__select_entity("Instance", instance)
        if backupset:
            self.__select_entity("Backupset", backupset)
        if subclient:
            self.__select_entity("Subclient", subclient)
        self.__click_save()
        self._webconsole.wait_till_load_complete()
        errors = self._webconsole.get_all_error_notifications()
        if errors:
            raise CVWebAutomationException(errors)

    @PageService()
    def add_storage_policy_copy_association_for_tag(self, tag_name, commcell, storage_policy="", copy_name=""):
        """Associates Storage policy copy for tag

        Args:
            tag_name        (str): Name of the tag

            commcell        (str): Name of the commcell

            storage_policy  (str): Name of the storage policy

                Default: Selects the first entry in the drop down

            copy_name       (str): Name of the copy name

                Default: Selects the first entry in the drop down

        """
        self.__select_tag("Storage Policy Copy Associations For Tag", tag_name)
        self.__click_new("Storage Policy Copy Associations For Tag")
        self.__select_entity("CommCell Name", commcell)
        self.__select_entity("Storage Policy", storage_policy)
        self.__select_entity("Copy Name", copy_name)
        self.__click_save()
        self._webconsole.wait_till_load_complete()
        errors = self._webconsole.get_all_error_notifications()
        if errors:
            raise CVWebAutomationException(errors)

    @PageService()
    def add_agent_association_for_tag(self, tag_name, agent="", commcell=""):
        """Associates Storage policy copy for tag

        Args:
            tag_name(str): Name of the tag

            agent(str):  Name of the agent

                Default: Selects the first entry in the drop down

            commcell(str): Name of the commcell

                Default: Selects the first entry in the drop down

        """
        self.__select_tag("Agent Associations For Tag", tag_name)
        self.__click_new("Agent Associations For Tag")
        self.__select_entity("Agent", agent)
        self.__select_entity("CommCell Name", commcell)
        self.__click_save()
        self._webconsole.wait_till_load_complete()
        errors = self._webconsole.get_all_error_notifications()
        if errors:
            raise CVWebAutomationException(errors)

    @PageService()
    def delete_associate_billing_tags(self, tag_name):
        """Deletes all associated tags with the given tag

        Args:
            tag_name   (str): Name of the tag

        """
        self.__select_tag("Associate Billing Tags", "All")
        for _ in range(self.__get_tag_count("Associate Billing Tags", tag_name)):
            self.__hover("Associate Billing Tags", tag_name)
            self.__click_trash_icon(tag_name)
            alert = self._driver.switch_to.alert
            alert.accept()
            errors = self._webconsole.get_all_error_notifications()
            if errors:
                raise CVWebAutomationException(errors)

    @PageService()
    def delete_storage_policy_copy_association_for_tags(self, tag_name):
        """Deletes all the storage policy associations with the given tag

        Args:
            tag_name    (str):   Name of the tag

        """
        self.__select_tag("Storage Policy Copy Associations For Tag", "All")
        for _ in range(self.__get_tag_count("Storage Policy Copy Associations For Tag", tag_name)):
            self.__hover("Storage Policy Copy Associations For Tag", tag_name)
            self.__click_trash_icon(tag_name)
            alert = self._driver.switch_to.alert
            alert.accept()
            errors = self._webconsole.get_all_error_notifications()
            if errors:
                raise CVWebAutomationException(errors)

    @PageService()
    def delete_agent_association_for_tags(self, tag_name):
        """Deletes all the agesnt associations with the given tag

        Args:
            tag_name    (str):   Name of the tag

        Returns:

        """
        self.__select_tag("Agent Associations For Tag", "All")
        for _ in range(self.__get_tag_count("Agent Associations For Tag", tag_name)):
            self.__hover("Agent Associations For Tag", tag_name)
            self.__click_trash_icon(tag_name)
            alert = self._driver.switch_to.alert
            alert.accept()
            errors = self._webconsole.get_all_error_notifications()
            if errors:
                raise CVWebAutomationException(errors)


class Tag:
    """Class for a tag and ites related operations"""

    def __init__(self):
        self.__driver = None
        self.__webconsole = None

    @property
    def _driver(self):
        if self.__driver is None:
            raise ValueError("driver not initialized, was add_new_billing_tag called ?")
        return self.__driver

    @property
    def _webconsole(self):
        if self.__webconsole is None:
            raise ValueError("webconsole not initialized, was add_new_billing_tag called ?")
        return self.__webconsole

    @_driver.setter
    def _driver(self, value):
        self.__driver = value

    @_webconsole.setter
    def _webconsole(self, value):
        self.__webconsole = value

    def configure_tag(self, webconsole):
        """Configures the tag object"""
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver

    @WebAction()
    def __set_input_field(self, column, content):
        """Sets the given input corresponding to the given column"""
        text_field = self._driver.find_element(By.XPATH, f"//*[@data-label='{column}']//input")
        text_field.clear()
        text_field.send_keys(content)

    @WebAction()
    def __set_drop_down(self, column, size_type):
        """Sets the given frop down corresponding to the given column"""
        element = self._driver.find_element(By.XPATH, f"//*[@data-label='{column}']//select")
        drop_down = Select(element)
        drop_down.select_by_visible_text(size_type)

    @WebAction()
    def __click_save(self):
        """Clicks save button"""
        save = self._driver.find_element(By.XPATH, "//*[@title='Save']")
        save.click()

    @PageService()
    def add_name(self, name):
        """Adds name

        Args:
            name(str): Name for the Tag

        """
        self.__set_input_field('Tag Name', name)

    @PageService()
    def add_size_type(self, size_type="Frontend Backup"):
        """Adds size type

        Args:
            size_type(str): type of the size

                Default: Frontend backup

        """
        self.__set_drop_down("Size Type", size_type)

    @PageService()
    def add_price(self, value="Global Price"):
        """Adds Price

        Args:
            value(str): type of the size

                Default: Global Price

        """
        self.__set_input_field("Price (/TB)", value)

    @PageService()
    def add_additional_price_details(self, price_level, value="5"):
        """Adds additional price details

        Args:
            price_level(str): Entity for which additional price is to be applied

            value(str): additional price for the entity

                Default: 5

        """
        self.__set_drop_down("Additional Price Level", price_level)
        if price_level != "N/A":
            self.__set_input_field("Additional Price", value)

    @PageService()
    def add_discount(self, discount_level, size="2", percentage="10"):
        """Adds discount

        Args:
            discount_level  (str):  Entity for which discount is to be applied

            size            (str):  Storage limit for which discount is to be applied

            percentage      (str):  Percentage of discount to be applied

        """
        self.__set_drop_down("Discount Level", discount_level)
        if discount_level != "N/A":
            self.__set_input_field("Discount Size (TB)", size)
            self.__set_input_field("Discount (%)", percentage)

    @PageService()
    def save(self):
        """Saves the new billing tag"""
        self.__click_save()
        self._webconsole.wait_till_load_complete()
        errors = self._webconsole.get_all_error_notifications()
        if errors:
            raise CVWebAutomationException(errors)


class ChargebackTrends:
    """Contains methods for operations on the Chargeback trends page"""

    def __init__(self, webconsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole

    @WebAction()
    def __click_details(self, chart_name):
        """Clicks the details link of the given chart"""
        details = self._driver.find_element(By.XPATH, f"//*[contains(text(),'{chart_name}')]/../a[@title='Details']")
        details.click()

    @PageService()
    def view_commcell_details(self):
        """Opens the Monthly Chargeback Trends by Commcell"""
        self.__click_details("CommCells")
        self._webconsole.wait_till_load_complete()

    @PageService()
    def view_client_details(self):
        """Opens the Monthly Chargeback Trends by Client"""
        self.__click_details("Client")
        self._webconsole.wait_till_load_complete()

    @PageService()
    def view_agents_details(self):
        """Opens the Monthly Chargeback Trends by Agents"""
        self.__click_details("Agents")
        self._webconsole.wait_till_load_complete()

    @PageService()
    def view_storage_policies_details(self):
        """Opens the Monthly Chargeback Trends by Storage Policies"""
        self.__click_details("Storage Policies")
        self._webconsole.wait_till_load_complete()
