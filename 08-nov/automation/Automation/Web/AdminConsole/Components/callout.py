from selenium.common import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

"""
Module to deal with Callout used in Admin console pages

Callout:

        is_callout_open --  Checks if callout is open

        perform_action  --  Performs required action from callout

        access_link     --  Access link inside callout using text or other property

CompanyEntitiesCallout:

        get_entities_data   --  Reads the entities count displayed in callout

        access_entity_link  --  Clicks the entity count link next to given entity

NotificationHeaderCallout:
"""

from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import (WebAction, PageService)


class Callout:
    """Callout Component used in Command Center"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._table = Table(self._admin_console)
        self._xp = "//div[@class='popover-body']"

    @WebAction()
    def is_callout_open(self):
        """Checks if callout is already open

        Returns:
            True    -   if callout is open already
            False   -   if no callout is found
        """
        return self._admin_console.check_if_entity_exists("xpath", self._xp)

    @WebAction()
    def perform_action(self, action):
        """Performs required action from callout"""
        self._driver.find_element(By.XPATH, self._xp + f"//span[text()='{action}']").click()

    @WebAction()
    def access_link(self, link_text, **options):
        """
        Access any link inside callout
        
        Args:
            link_text   (str)   -   text of the link, can be None if not known
            options:
                any html property (str) - the value for that property
                example:
                    id      (str)      -   id value for the link element
                    class   (str)      -   class value for the link element
        """
        link_xp = self._xp + "//a["
        if link_text:
            link_xp += f"text()='{link_text}' and "
        if options:
            for xp_constraint, xp_value in options.items():
                link_xp += f"contains(@{xp_constraint}, '{xp_value}') and "
        link_xp = link_xp.rstrip(" and ") + "]"
        self._driver.find_element(By.XPATH, link_xp).click()

    @WebAction()
    def __get_entities_count(self) -> dict:
        """Gets the entities and corresponding counts displayed in the callout"""
        items = self._driver.find_elements(By.XPATH, f"{self._xp}//a")
        entity_counts = {}

        for item in items:
            key = item.find_element(By.XPATH, './span[1]').text
            value_elements = item.find_elements(By.XPATH, './span[2]')
            value = value_elements[0].text if value_elements else ''
            entity_counts[key] = value

        return entity_counts

    @PageService()
    def get_entities_count(self) -> dict:
            """
            Method to get the entities and corresponding counts displayed in the callout.

            Returns:
                dict: A dictionary containing the entities as keys and their corresponding counts as values.
                      Example: {'Entity1': '10', 'Entity2': '5', 'Entity3': ''}
            """
            return self.__get_entities_count()

class CompanyEntitiesCallout(Callout):
    """
    Class for the callout opened when accessing entities column link in companies page
    """

    def __init__(self, admin_console):
        """
        init function of EntitiesCallout class
        """
        super().__init__(admin_console)

    @WebAction()
    def __get_entities_counts(self):
        """
        Returns the entity and corresponding counts displayed in callout as dict
        """
        entity_counts = {}
        td_elems = self._driver.find_elements(By.XPATH, 
            f"{self._xp}//div[contains(@class, 'd-flex') and not(contains(@class, 'wrap'))]"
        )
        for td_elem in td_elems:
            entity_name = td_elem.find_element(By.XPATH, "./*[2]").text
            entity_count = td_elem.find_element(By.XPATH, "./*[3]").text
            entity_counts[entity_name] = entity_count
        return entity_counts

    @PageService()
    def get_entities_data(self):
        """
        Gets the entities and corresponding counts

        Returns:
            dict    -   dict with entity name as key and count as value
                        example:    {
                            'Alerts definitions': '1',
                            'Server group': '2',
                            'User group': '3'
                        }
        """
        return self.__get_entities_counts()

    @WebAction()
    def __click_entity_count(self, entity_name):
        """
        Clicks the entity count link next to entity label

        Args:
            entity_name (str)   -   the entity name
        """
        self._driver.find_element(By.XPATH, 
            f"{self._xp}//span[text()='{entity_name}']/following-sibling::a"
        ).click()

    @PageService()
    def access_entity_link(self, entity_name):
        """
        Clicks the entity count redirection link

        Args:
            entity_name -   name of entity to access link of
        """
        self.__click_entity_count(entity_name)
        self._admin_console.wait_for_completion()


class NotificationHeaderCallout(Callout):
    """Callout Component for performing operations on top header notifications"""

    def __init__(self, admin_console, title=None):
        """Method to initialize NotificationHeaderCallout class"""
        super().__init__(admin_console)
        self.title = title
        self.__base_element = None
        if self.title:
            self._xp = (f"//li[contains(@class, 'notification-header')]"
                        f"//*[text()='{title}']//ancestor::div[@class='popover-body']")

    @property
    def base_element(self) -> WebElement:
        """Base element for callout"""
        if not self.__base_element:
            self.__get_base_element()

        # Hacky way to check if base element is not stale
        try:
            self.__base_element.text
        except (StaleElementReferenceException, NoSuchElementException):
            self.__get_base_element()

        return self.__base_element

    @WebAction()
    def __get_base_element(self) -> WebElement:
        """Method to get base element"""
        self.__base_element = self._driver.find_element(By.XPATH, self._xp)

        return self.__base_element

    @PageService()
    def get_notifications(self) -> list:
        """Method to get notifications

        Returns:
            List of notifications from notification callout
            Example: {"Notif 1": ["May 28, 10:20 PM"], "Notif 2": []}...]
        """
        notif_list = []
        if notif_items := self.base_element.find_elements(By.XPATH, "//div[contains(@class,'notification-item')]"):
            for notif in notif_items:
                text = notif.text.split('\n')
                notif_list.append({text[0]: text[1]})

            return notif_list

        notif_items = self.base_element.find_elements(By.XPATH, ".//span[@class = 'notification-item-text']")
        for item in notif_items:
            sub_texts = item.find_elements(By.XPATH, ".//*[@class='notification-sub-title']")
            notif_text = item.find_element(By.XPATH, ".//*[@class='notification-title']")

            notif_list.append({notif_text.text: ([sub_text.text for sub_text in sub_texts])})

        return notif_list
