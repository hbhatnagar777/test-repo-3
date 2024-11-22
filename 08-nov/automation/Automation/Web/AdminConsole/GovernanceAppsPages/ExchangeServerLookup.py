from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Exchange Server lookup page
which is opened while adding a Data Source in Sensitive Data Analysis Project Details
page.
"""
from selenium.common.exceptions import NoSuchElementException
from Web.Common.page_object import WebAction, PageService
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.table import Table, CVTable


class ExchangeServerLookup:
    """
    This Class Contains All Methods for Exchange Server Lookup Page
    """
    add_data_source = None
    select_exchange_obj = None
    configure_exchange_obj = None
    review_exchange_data_source = None

    def __init__(self, admin_console):
        self.__table = Table(admin_console)
        self.add_data_source = AddDataSource(admin_console)
        self.select_exchange_obj = SelectExchangeHost(admin_console)
        self.configure_exchange_obj = ConfigureExchangeHost(admin_console)
        self.review_exchange_data_source = ReviewExchangeDataSource(admin_console)


class AddDataSource:
    """
    Select Add Data Source
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console

    @WebAction()
    def _click_add_data_source(self):
        """
        Click Add DataSource Option
        """
        self._admin_console.driver.find_element(By.XPATH, 
            "//span[@class='ng-binding' and text()='Add']").click()

    @WebAction()
    def _click_exchange_data_source(self, data_source_type):
        """
        Select Exchange as Data Source Type
        Args:
            data_source_type: Datasource Type To Add

        Returns:

        """
        self._admin_console.driver.find_element(By.XPATH, 
            f"//span[@class='uib-dropdown dropdown open']/ul//span[text()='{data_source_type}']") \
            .click()

    @PageService()
    def select_add_data_source(self, data_source_type='Exchange'):
        """
            Selects the Exchange system data source to be added

            Args:
                data_source_type (str) - Type of the data source to be selected
            Raise:
                CVWebAutomationException if invalid data source type provided
        """
        self._click_add_data_source()
        self._admin_console.wait_for_completion()
        if "Exchange".lower() == str(data_source_type).lower():
            self._click_exchange_data_source(data_source_type)
        else:
            raise CVWebAutomationException("Invalid data source type: %s" % data_source_type)
        self._admin_console.wait_for_completion()


class SelectExchangeHost:
    """
    Select Exchange Proxy Server
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__cv_table = CVTable(self.__admin_console)

    @WebAction()
    def _search(self, search_name):
        """
        Search for Exchange Server Client
        Args:
            search_name (str) - Exchange Server Client Hostname
        """
        search_bar = self.__admin_console.driver.find_element(By.XPATH, 
            "//div[@class='review-items-search']//input")
        search_bar.clear()
        search_bar.send_keys(f"{str(search_name)}")

    @PageService()
    def select_exchange_host(self, search_name, search_criteria):
        """
        Search for Exchange Server to Analyze
        Args:
            search_name (str) - Client Name To Search For.
            search_criteria (str) - Search Criteria for filtering Exchange Server Name
                Values:
                    "Client name",
                    "Operating system",Not a Part of table header
                    "Host name",
                    "All"

        """
        self.__admin_console.select_value_from_dropdown("dataColumn", search_criteria)
        self.__admin_console.wait_for_completion()
        self._search(search_name)
        self.__admin_console.wait_for_completion()
        client_list = self.__cv_table.get_column_data(search_criteria)
        temp_text = ""
        if len(client_list) > 0:
            temp_text = client_list.pop(0)
        if temp_text.lower() != str(search_name).lower():
            raise CVWebAutomationException(f"Could Not Find: {search_name}")
        temp_text = ""
        status_list = self.__cv_table.get_column_data("Status")
        if len(status_list) > 0:
            temp_text = status_list.pop(0)

        if "Agent installed".lower() != str(temp_text).lower():
            raise CVWebAutomationException("Agent Not Installed")

        self.__cv_table.select_checkbox(0)
        self.__admin_console.click_button("Next")


class ConfigureExchangeHost:
    """Configure Data Source"""

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__cv_table = CVTable(self.__admin_console)

    @WebAction()
    def _enter_display_name(self, display_name):
        """
        Entering Display Name
        Args:
            display_name (str) - Display Name for Datasource
        """
        self.__admin_console.fill_form_by_id("displayName", display_name)

    @WebAction()
    def _enter_country_name(self, country_name):

        """
        Enter Country Name
        Args:
            country_name (str) - Country Name
        """
        self.__admin_console.select_value_from_dropdown("country", country_name)

    @WebAction()
    def _select_mailboxes(self, mailbox):
        """
        Check Selected Mailbox
        Args:
            mailbox (str) - Mailbox to be selected
        """

        self.__admin_console.driver.find_element(By.XPATH, 
            f'//div[@id="exchangeBrowseGrid"]/div[4]//table/tbody/tr[td//text()[contains(.,"{str(mailbox)}")]]/td[1]') \
            .click()

    @PageService()
    def configure_exchange_host(self, display_name, country_name,
                                list_of_mailboxes=["All mailboxes"]):
        """
        Configure Exchange Server Host
        Args:
            display_name: Name of Exchange Data Source
            country_name: Country Name of Server
            list_of_mailboxes: List of mailboxes to be added

        Returns:

        """
        self._enter_display_name(display_name)
        self._enter_country_name(country_name)
        self.__admin_console.wait_for_completion()
        if len(list_of_mailboxes) == 1 and list_of_mailboxes[0].lower() == "all mailboxes":
            self.__admin_console.select_radio("allMailboxes")
        else:
            self.__admin_console.select_radio("selectMailboxes")

            self.__admin_console.click_button("Browse")
            for mailbox in list_of_mailboxes:
                self._select_mailboxes(mailbox)

            self.__admin_console.click_button("Save")

        self.__admin_console.click_button("Finish")


class ReviewExchangeDataSource:
    """Review Data Source"""

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__cv_table = CVTable(self.__admin_console)

    @WebAction()
    def _search(self, subject):
        """
        Search on Basis of Subject Of Mail
        Args:
            subject: Subject Of Mail

        Returns:

        """
        search_string = f'(Subject:"{subject}")'
        search_bar = self.__admin_console.driver.find_element(By.XPATH, 
            '//div[@class="review-items-search"]/form/input')
        search_bar.clear()
        search_bar.send_keys(search_string)

    @PageService()
    def select_mail(self, subject):
        """
        Select Mail for a given Subject
        Args:
            subject: Subject for Mail

        Returns:

        """
        self._search(subject)
        self.__admin_console.wait_for_completion()
        try:
            self.__cv_table.access_link(subject)
        except NoSuchElementException:
            raise CVWebAutomationException(f"Mail Subject Not Found {subject}")
