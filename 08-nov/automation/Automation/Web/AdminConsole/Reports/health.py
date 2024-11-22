from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Module to manage CommCell health in admin console health report.
"""
from time import sleep
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.page_container import PageContainer

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
    def __init__(self, admin_console):

        self._admin_console = admin_console
        self.driver = admin_console.driver
        self.page_container = PageContainer(self._admin_console)

    @WebAction()
    def _click_view_by_category(self):
        """click view by category"""
        self.driver.find_element(By.XPATH, "//div[contains(text(),'By category')]").click()

    @WebAction()
    def _click_view_by_severity(self):
        """click view by severity"""
        self.driver.find_element(By.XPATH, "//div[contains(text(),'By severity')]").click()

    @WebAction()
    def _click_show_hidden_tile(self):
        """click on show hidden tile option"""
        self.page_container.access_page_action("Hidden tiles").click()
        '''xpath = "//div[contains(text(),'Hidden tiles')]"
        show_hidden_tile = self.driver.find_element(By.XPATH, xpath)
        show_hidden_tile.click()'''

    @WebAction()
    def _get_remark_links(self):
        """get remark links for all the tiles"""
        links = []
        href_elements = self.driver.find_elements(By.XPATH, f"//p[contains(@class,'remark-item')]//"
                                                           f"a[contains(@href, *)]")
        for href in href_elements:
            links.append(href.get_attribute('href'))
        return links
    # currently returns empty tags as well as issue in report

    @WebAction()
    def _get_hidden_tiles(self):
        """
        Gets the list of hidden tiles
        Returns: Tiles list
        """
        tiles = self.page_container.get_action_list()
        tiles.pop(0)
        tiles_list = []
        for each_tile in tiles:
            tiles_list.append(each_tile)
        return tiles_list

    @WebAction(delay=5)
    def _get_all_visible_tiles(self):
        """ Get all the visible tiles """
        tiles = self.driver.find_elements(By.XPATH, "//div[@class='tile-title']/a")
        tiles_list = []
        for each_tile in tiles:
            tiles_list.append(each_tile.text)
        return tiles_list

    @WebAction()
    def _click_status_all(self):
        """Click the All status in health report"""
        xpath = "//div[contains(@class,'severity-filter-dropdown')]/div"
        self.driver.find_element(By.XPATH, xpath).click()
        select_all = self.driver.find_element(By.XPATH, "//span[text()='All']")
        select_all.click()

    @WebAction()
    def _click_status_critical(self):
        """Click the Critical status in health report"""
        xpath = "//div[contains(@class,'severity-filter-dropdown')]/div"
        self.driver.find_element(By.XPATH, xpath).click()
        sleep(2)
        critical = self.driver.find_element(By.XPATH, "//span[text()='Critical']")
        critical.click()

    @WebAction()
    def _click_status_warning(self):
        """Click the warning status in report."""
        xpath = "//div[contains(@class,'severity-filter-dropdown')]/div"
        self.driver.find_element(By.XPATH, xpath).click()
        sleep(2)
        warning = self.driver.find_element(By.XPATH, "//span[text()='Warning']")
        warning.click()

    @WebAction()
    def _click_status_good(self):
        """Click the good status in report"""
        xpath = "//div[contains(@class,'severity-filter-dropdown')]/div"
        self.driver.find_element(By.XPATH, xpath).click()
        sleep(2)
        good = self.driver.find_element(By.XPATH, "//span[text()='Good']")
        good.click()

    @WebAction()
    def _click_status_information(self):
        """Click the information status in report"""
        xpath = "//div[contains(@class,'severity-filter-dropdown')]/div"
        self.driver.find_element(By.XPATH, xpath).click()
        sleep(2)
        information = self.driver.find_element(By.XPATH, "//span[text()='Information']")
        information.click()

    @WebAction()
    def _get_category(self):
        """
        Get the report categories
        Returns:
            list: List of categories
        """
        categories_list = []
        categories = self.driver.find_elements(By.XPATH, "//h3")
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
            xpath = "//div[@class='tile-header %s']/..//div[@class='tile-title']" % each_status
            tiles_name = self.driver.find_elements(By.XPATH, xpath)
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
            xpath = "//h3[text()='" + each_category + "']/..//div[@class='tile-title']/a"
            tiles_obj_list = self.driver.find_elements(By.XPATH, xpath)
            for each_tile in tiles_obj_list:
                tiles.append(each_tile.text)
            categories_dict[each_category] = tiles
        return categories_dict

    @WebAction()
    def _get_client_group_names(self):
        """Reads the client group names from top of the health page"""
    # report missing these details
    # to be implemented

    @WebAction()
    def _read_critical_tiles_count(self):
        """Reads the Critical tiles count from the filter panel"""
        critical_xp = "//div[@class='aggregate-icon critical']/../div[@class='aggregate-detail']/h1"
        return int(self.driver.find_element(By.XPATH, critical_xp).text)

    @WebAction()
    def _read_warning_tiles_count(self):
        """Reads the Warning tiles count from the filter panel"""
        warning_xp = "//div[@class='aggregate-icon warning']/../div[@class='aggregate-detail']/h1"
        return int(self.driver.find_element(By.XPATH, warning_xp).text)

    @WebAction()
    def _read_good_tiles_count(self):
        """Reads the Good tiles count from the filter panel"""
        good_xp = "//div[@class='aggregate-icon good']/../div[@class='aggregate-detail']/h1"
        return int(self.driver.find_element(By.XPATH, good_xp).text)

    @WebAction()
    def _read_info_tiles_count(self):
        """Reads the Info tiles count from the filter panel"""
        info_xp = "//div[@class='aggregate-icon info']/../div[@class='aggregate-detail']/h1"
        return int(self.driver.find_element(By.XPATH, info_xp).text)

    @WebAction()
    def _get_view_details_tiles(self):
        """Get tiles which have view details link"""
        xpath = "//div[@title='View details']/../..//*[@class='tile-title']//*[@title]"
        return [each_tile.text for each_tile in self.driver.find_elements(By.XPATH, xpath)]

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
        self._admin_console.wait_for_completion()

    @PageService()
    def filter_by_warning(self):
        """Filter by status warning"""
        self._click_status_warning()
        self._admin_console.wait_for_completion()

    @PageService()
    def filter_by_good(self):
        """Click the status good"""
        self._click_status_good()
        self._admin_console.wait_for_completion()

    @WebAction()
    def filter_by_information(self):
        """Click the status info"""
        self._click_status_information()
        self._admin_console.wait_for_completion()

    @WebAction()
    def select_all_severity(self):
        """Show all severity tiles"""
        self._click_status_all()
        self._admin_console.wait_for_completion()

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
        self.page_container.access_page_action("Show all")

    @PageService()
    def show_hidden_tile(self):
        """Click show hidden tiles"""
        self.page_container.access_page_action("Hidden tiles")

    @PageService()
    def get_client_group_names(self):
        """
        Gets the Client group names from the Health page

        Returns:
            list: Group names
        """
        group_names = self._get_client_group_names()
        return group_names.split(': ')[1].split(',')
    # functionality missing from current report

    @PageService()
    def get_critical_tiles_count(self):
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
        return (self.get_critical_tiles_count() +
                self.get_warning_tiles_count() +
                self.get_good_tiles_count() +
                self.get_info_tiles_count()
                )
