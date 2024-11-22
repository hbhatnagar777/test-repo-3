from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Module to manage CommCell health in Metrics report.
"""
from time import sleep
from Web.Common.page_object import (WebAction, PageService)


class HealthConstants:
    """Health constants"""
    STATUS_CRITICAL = 'Critical'
    STATUS_WARNING = 'Warning'
    STATUS_GOOD = 'Good'
    STATUS_INFO = 'Info'
    VIEW_BY_CATEGORY = 'category'
    VIEW_BY_SEVERITY = 'severity'


class Health:
    """
    Class to manage Health Page
    """
    def __init__(self, webconsole):

        self._driver = webconsole.browser.driver
        self._webconsole = webconsole
        self._browser = webconsole.browser

    @WebAction()
    def _click_view_by(self):
        """click view by drop down"""
        xpath = "//div[@class='viewOptions hideOnExportFriendly'][1]/span"
        view_by = self._driver.find_element(By.XPATH, xpath)
        self._browser.click_web_element(view_by)

    @WebAction()
    def _click_view_by_category(self):
        """click view by category"""
        self._driver.find_element(By.XPATH, "//button[text()='By Category']").click()

    @WebAction()
    def _click_view_by_severity(self):
        """click view by severity"""
        self._driver.find_element(By.XPATH, "//button[text()='By Severity']").click()

    @WebAction()
    def _click_show_hidden_tile(self):
        """click on show hidden tile option"""
        xpath = "//*[@data-ng-click='showHiddenTileMenu=true']"
        show_hidden_tile = self._driver.find_element(By.XPATH, xpath)
        self._browser.click_web_element(show_hidden_tile)

    @WebAction()
    def _get_remark_links(self):
        """get remark links for all the tiles"""
        links = []
        href_elements = self._driver.find_elements(By.XPATH, f"//div[contains(@id,'remark')]//a[contains(@href, *)]")
        for href in href_elements:
            links.append(href.get_attribute('href'))
        return links

    @WebAction()
    def _get_hidden_tiles(self):
        """
        Gets the list of hidden tiles
        Returns: Tiles list
        """
        tiles = self._driver.find_elements(By.XPATH, "//*[@id='showHiddenTile']//li")
        tiles_list = []
        for each_tile in tiles:
            tiles_list.append(each_tile.text)
        return tiles_list

    @WebAction()
    def _click_show_all_tiles(self):
        """click show all tiles option"""
        show_tiles = self._driver.find_element(By.ID, 'showAllTile')
        self._browser.click_web_element(show_tiles)

    @WebAction(delay=5)
    def _get_all_visible_tiles(self):
        """ Get all the visible tiles """
        tiles = self._driver.find_elements(By.XPATH, "//h4[@class='tileTitle']/div")
        tiles_list = []
        for each_tile in tiles:
            tiles_list.append(each_tile.text)
        return tiles_list

    @WebAction()
    def _click_status_critical(self):
        """Click the Critical status in health report"""
        xpath = "//div[@title='Health Parameters in Critical Status']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _click_status_warning(self):
        """Click the warning status in report."""
        xpath = "//div[@title='Health Parameters in Warning Status']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _click_status_good(self):
        """Click the good status in report"""
        xpath = "//div[@title='Health Parameters in Good Status']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _click_status_information(self):
        """Click the information status in report"""
        xpath = "//div[@title='Health Parameters in Info Status']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _get_category(self):
        """
        Get the report categories
        Returns:
            list: List of categories
        """
        categories_list = []
        categories = self._driver.find_elements(By.XPATH, "//h3[@class='ng-binding']")
        for each_category in categories:
            categories_list.append(each_category.text)
        return categories_list

    @WebAction()
    def _get_tiles_with_status(self):
        """
          Get status with corresponding reports as dictionary
        Returns:
            dict: Tiles with corresponding status
        """
        tile_status = [HealthConstants.STATUS_CRITICAL, HealthConstants.STATUS_WARNING,
                       HealthConstants.STATUS_GOOD, HealthConstants.STATUS_INFO]
        report_by_status = {}
        for each_status in tile_status:
            tiles = []
            xpath = "//label[@class='tileIcon sprite reports-health-%s']/following-sibling::div"\
                    % (
                        each_status
                    )
            tiles_name = self._driver.find_elements(By.XPATH, xpath)
            for each_tiles in tiles_name:
                tiles.append(each_tiles.text)
            report_by_status[each_status] = tiles
        return report_by_status

    @WebAction()
    def _get_tiles_with_category(self):
        """
        Gets tiles and it's category
        Returns:
            dict:Tile name and corresponding category
        """
        categories = self._get_category()
        categories_dict = {}
        for each_category in categories:
            tiles = []
            xpath = "//h3[text()='" + each_category + "']/../..//h4[@class='tileTitle']"
            tiles_obj_list = self._driver.find_elements(By.XPATH, xpath)
            for each_tile in tiles_obj_list:
                tiles.append(each_tile.text)
            categories_dict[each_category] = tiles
        return categories_dict

    @WebAction()
    def _get_client_group_names(self):
        """Reads the client group names from top of the health page"""
        return self._driver.find_element(By.XPATH, "//li[@id='metaClientGrp']/span").text

    @WebAction()
    def _read_critical_tiles_count(self):
        """Reads the critical tiles count from the filter panel"""
        critical_xp = ("//div[@title='Health Parameters in Critical Status']"
                       "/div[@class='dash-status-number ng-binding']")
        return int(self._driver.find_element(By.XPATH, critical_xp).text)

    @WebAction()
    def _read_warning_tiles_count(self):
        """Reads the Warning tiles count from the filter panel"""
        critical_xp = ("//div[@title='Health Parameters in Warning Status']"
                       "/div[@class='dash-status-number ng-binding']")
        return int(self._driver.find_element(By.XPATH, critical_xp).text)

    @WebAction()
    def _read_good_tiles_count(self):
        """Reads the Good tiles count from the filter panel"""
        critical_xp = ("//div[@title='Health Parameters in Good Status']"
                       "/div[@class='dash-status-number ng-binding']")
        return int(self._driver.find_element(By.XPATH, critical_xp).text)

    @WebAction()
    def _read_info_tiles_count(self):
        """Reads the info tiles count from the filter panel"""
        critical_xp = ("//div[@title='Health Parameters in Info Status']"
                       "/div[@class='dash-status-number ng-binding']")
        return int(self._driver.find_element(By.XPATH, critical_xp).text)

    @WebAction()
    def _get_view_details_tiles(self):
        """Get tiles which have view details link"""
        xpath = "//*[@class='sprite reports-health-detail floatingAction']/../../../." \
                ".//*[@data-name]"
        return [each_tile.text for each_tile in self._driver.find_elements(By.XPATH, xpath)]

    @PageService()
    def view_by_category(self):
        """View the report based on category"""
        self._click_view_by_category()

    @PageService()
    def view_by_severity(self):
        """View the report based on severity"""
        self._click_view_by_severity()

    @PageService()
    def get_remark_links(self):
        """gets the list of remark links for all the tiles"""
        return self._get_remark_links()

    @PageService()
    def get_hidden_tiles(self):
        """
        Gets the list of hidden tiles
        Returns:
            list: Hidden tile list
        """
        self.show_hidden_tile()
        return self._get_hidden_tiles()

    @PageService()
    def get_view_details_tiles(self) -> list:
        """Get tiles names which has view details link"""
        return self._get_view_details_tiles()

    @PageService()
    def filter_by_critical(self):
        """Click the status critical"""
        self._click_status_critical()

    @PageService()
    def filter_by_warning(self):
        """Filter by status warning"""
        self._click_status_warning()

    @PageService()
    def filter_by_good(self):
        """Click the status good"""
        self._click_status_good()

    @WebAction()
    def filter_by_information(self):
        """Click the status info"""
        self._click_status_information()
        sleep(4)

    @PageService()
    def is_tile_hidden(self, tile_name):
        """Check whether the tile is hidden
        Returns:
            bool: True for tile not hidden , False for tile hidden
        """
        if tile_name in self._get_all_visible_tiles():
            return False
        else:
            return True

    @PageService()
    def get_tiles_with_status(self):
        """
        Get status with corresponding reports in dictionary
        Returns:
            dict: Tile and corresponding status
        """
        return self._get_tiles_with_status()

    @PageService()
    def get_category_list(self):
        """
        Get the report categories
        Returns:
            list: List of visible categories
        """
        return self._get_category()

    @PageService()
    def get_tiles_with_category(self):
        """
        Get tiles and corresponding category in dictionary
        Returns:
            dict: Tile name and corresponding category
        """
        return self._get_tiles_with_category()

    @PageService()
    def get_visible_tiles(self):
        """
        Get the list of visible tiles in the report.
        Returns:
            list: List of visible tiles.
        """
        return self._get_all_visible_tiles()

    @PageService()
    def show_all_tiles(self):
        """Show all tiles"""
        self._click_show_all_tiles()

    @PageService()
    def show_hidden_tile(self):
        """Click show hidden tiles"""
        self._click_show_hidden_tile()

    @PageService()
    def get_client_group_names(self):
        """
        Gets the Client group names from the Health page

        Returns:
            list: Group names
        """
        group_names = self._get_client_group_names()
        return group_names.split(': ')[1].split(',')

    @PageService()
    def get_critial_tiles_count(self):
        """
        Gets the Critical tiles count from the filter panel
        :return: Critical tiles count
        """
        return self._read_critical_tiles_count()

    @PageService()
    def get_warning_tiles_count(self):
        """
        Gets the warning tiles count from the filter panel
        :return: warning tiles count
        """
        return self._read_warning_tiles_count()

    @PageService()
    def get_good_tiles_count(self):
        """
        Gets the Good tiles count from the filter panel
        :return: Good tiles count
        """
        return self._read_good_tiles_count()

    @PageService()
    def get_info_tiles_count(self):
        """
        Gets the info tiles count from the filter panel
        :return: info tiles count
        """
        return self._read_info_tiles_count()

    def get_total_tiles_count(self):
        """
        Gets the Total tiles count from the all status filter panel
        :return: Total tiles count
        """
        return (self.get_critial_tiles_count() +
                self.get_warning_tiles_count() +
                self.get_good_tiles_count() +
                self.get_info_tiles_count()
                )
