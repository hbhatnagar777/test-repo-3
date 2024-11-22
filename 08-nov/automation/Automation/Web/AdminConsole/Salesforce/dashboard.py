"""
Module for Salesforce Dashboard Page

SalesforceDashboard:

            get_Backup_health()             :           Obtains information from Backup Health section of the Dashboard
                                                        page

            get_Data_Distribution()         :           Obtains information from Data Distribution section of the
                                                        Dashboard page

            get_Environments()              :           Obtains information from Environment section of the Dashboard
                                                        page


"""


from cvpysdk.commcell import Commcell
from selenium.webdriver.common.by import By
import re
from Web.AdminConsole.adminconsole import AdminConsole
from ..Components.page_container import PageContainer
from Web.Common.page_object import PageService, WebAction


class SalesforceDashboard:

    def __init__(self, admin_console, commcell):
        """
                Constructor for the class

                Args:
                    admin_console (AdminConsole): AdminConsole object
                    commcell (Commcell): Commcell object
        """
        self.__admin_console = admin_console
        self.__commcell = commcell
        self.__page_container = PageContainer(self.__admin_console)
        self.__admin_console.load_properties(self)
        self._driver = admin_console.driver
        self._navigator = self.__admin_console.navigator
        self.file_name = None
        self.backup_health_chart = None
        self.backup_health_dict = {}

    @WebAction()
    def _fetch_object_values(self, chart_xpath):
        """
                Fetches the height of the bars
                Args:
                    chart_xpath: Xpath of the particular chart
        """
        bars = self._driver.find_elements(
            By.XPATH,
            f"{chart_xpath}//*[name()='g' and contains(concat(' ', @class, ' '), ' highcharts-series ')]"
            f"//*[name()='path' and @aria-label]"
        )
        return [re.search("(\w*)\.", bar.get_attribute('aria-label')).string for bar in bars]

    def _get_data_from_string(self, items):
        """
                Separates the value from string and creates a corresponding dictionary of matching key value pairs
                Args:
                    items (list): List of strings consisting of key and their values
        """
        temp_dict = {}
        for item in items:
            string = item
            string = string.replace(',', '')
            index1 = string.rfind(".")
            index2 = string.rfind(" ", 0, index1)
            temp_dict[string[0:index2]] = int(string[index2+1:index1])

        return temp_dict

    def _getChart(self, title):
        """
                Returns the xpath of the tile based on it's name
                Args:
                    title (str): Title of the tile which needs to be selected
        """
        xpath = f"//*[text()='{title}']"f"/ancestor::div[contains(@class, 'tile-container')]"
        return xpath

    @PageService()
    def get_Backup_health(self):
        """
                Fills the backup dictionary with values extracted from the Backup Health tile
        """
        self.backup_health_chart = self._getChart("Backup health")
        dict_items = self._fetch_object_values(self.backup_health_chart)
        self.backup_health_dict = self._get_data_from_string(dict_items)
        self.backup_health_dict[self.__admin_console.props["label.dashboard.backupHealth.entities.backedUp"]] = (
            self.backup_health_dict.pop('Objects backed up'))
        self.backup_health_dict[self.__admin_console.props["label.dashboard.backupHealth.entities.notBackedUp"]] = (
            self.backup_health_dict.pop('Objects not backed up recently'))
        self.backup_health_dict[self.__admin_console.props["label.dashboard.backupHealth.entities.neverBackedUp"]] = (
            self.backup_health_dict.pop('Objects never backed up'))
        return self.backup_health_dict

    @PageService()
    def get_Data_Distribution(self):
        """
                Empty function. Can be used to obtain data from Data Distribution tile
        """

    @PageService()
    def get_Environments(self):
        """
                Empty function. Can be used to obtain data from Environment tile
        """