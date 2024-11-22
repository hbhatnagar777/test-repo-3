from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" All the operations on the Reports homepage.

ReportsHomePage:

    _click_report_name                      --      Click the name of the report.

    _click_search_by_column                 --       Click the name of the report.

    _click_search_by_content                --      Clicks the list with report content.

    _get_advanced_search_result             --      Fetches the list of elements after advanced
                                                    search.

    _get_all_reports_objects                --      Get all the reports objects.

    _get_reports_with_update_icon           --      Read the report names with.

    _set_search_field                       --      Set search string on reports page.

    advanced_search_by_column               --      Get all the reports having the column
                                                    entered in the reports search bar.

    advanced_search_by_content              --      Get all the reports having the content
                                                    entered in the reports search bar.

    get_all_report_details                  --      Get all the reports with its URLs.

    get_reports_having_update               --      Read the report names with.

    goto_report                             --      Get the list of all reports which have a newer
                                                    version on StoreServer.

    is_advanced_search_report_exists        --      Checks whether report exist after advanced
                                                    search.

    search_report                           --      Search for report on WW Reports page.

"""

from time import sleep

from AutomationUtils.config import get_config
from Web.Common.page_object import (
    WebAction,
    PageService
)

_CONFIG = get_config()


class ReportsHomePage:
    """ Contains all Web Actions and Page services realted to Reports Home Page."""
    def __init__(self, webconsole):
        self.webconsole = webconsole
        self.browser = webconsole.browser
        self._driver = webconsole.browser.driver

    @WebAction()
    def _click_report_name(self, report_name):
        """ Click the name of the report. """
        self._driver.find_element(By.XPATH, 
            f"//div[@id='reportSearchDiv']//li[@id='reportItem']//a[text()='{report_name}']"
        ).click()

    @WebAction()
    def _click_search_by_column(self):
        """ Clicks the list with report column. """
        content = self._driver.find_element(By.XPATH, "//li[@id='reportColumn']")
        content.click()

    @WebAction()
    def _click_search_by_content(self):
        """ Clicks the list with report content. """
        content = self._driver.find_element(By.XPATH, "//li[@id='reportContent']")
        content.click()

    @WebAction()
    def _get_advanced_search_result(self, report_name):
        """ Fetches the list of elements after advanced search.

        Args:
            report_name: name of the report which is to be present.

        Returns: List of elements having report_name as its value for the title attribute.

        """
        result = self._driver.find_elements(By.XPATH, 
            "//div[@id='advanceSearchDiv']//li/a[@title='"+report_name+"']")
        return result

    @WebAction()
    def _get_all_reports_objects(self):
        """ Get all the reports objects. """
        return self._driver.find_elements(By.XPATH, "//li[@class='reportItem']/a")

    @WebAction()
    def _get_reports_with_update_icon(self):
        """ Read the report names with. """
        report_objects = self._driver.find_elements(By.XPATH, 
            "//*[span[@title='Update available']]"
        )
        return [
            report_object.text
            for report_object in report_objects
            if report_object.is_displayed()
        ]

    @WebAction()
    def _set_search_field(self, string):
        """ Set search string on reports page. """
        search_field = self._driver.find_element(By.ID, "reportFilterSearch")
        search_field.clear()
        search_field.send_keys(string)
        sleep(2)

    @WebAction()
    def _access_creport_by_name(self, report_name):
        """"Access report directly with name"""
        self._driver.get(
            f"{self.webconsole.base_url}reportsplus/reportViewer.jsp?reportName={report_name}"
        )

    @PageService()
    def advanced_search_by_column(self, keyword):
        """ Get all the reports having the column entered in the reports search bar.

        Args:
            keyword (string) : search key to be entered in the reports search bar

        """
        self._set_search_field(keyword)
        self._click_search_by_column()
        self.webconsole.wait_till_load_complete()

    @PageService()
    def advanced_search_by_content(self, keyword):
        """ Get all the reports having the content entered in the reports search bar.

        Args:
            keyword (string) : search key to be entered in the reports search bar

        """
        self._set_search_field(keyword)
        self._click_search_by_content()
        self.webconsole.wait_till_load_complete()

    @PageService()
    def get_all_report_details(self):
        """
        Get all the reports with its URLs.
        Returns:
            list: dictionary of report details with name and href
        """
        _report_names = []
        reports = []
        for each_report_obj in self._get_all_reports_objects():
            if str(each_report_obj.text) not in _report_names and each_report_obj.text != '':
                reports.append(
                    {
                        'name': str(each_report_obj.text),
                        'href': each_report_obj.get_attribute('href')
                     }
                )
                _report_names.append(each_report_obj.text)
        return reports

    @PageService()
    def get_reports_having_update(self):
        """ Get the list of all reports which have a newer version on StoreServer. """
        return self._get_reports_with_update_icon()

    @PageService()
    def goto_report(self, report_name):
        """Open report"""
        self._set_search_field(report_name)
        self._click_report_name(report_name)
        self.webconsole.wait_till_load_complete()

    @PageService()
    def is_advanced_search_report_exists(self, report_name):
        """ Checks whether report exist after advanced search.

        Args:
            report_name: name of the report which is to be present.

        Returns:
            True - If any report exist after search.

            False - If report doesn't exist.

        """
        result = self._get_advanced_search_result(report_name)
        return False if len(result) != 1 else True

    @PageService()
    def search_report(self, report_name):
        """ Search for report on WW Reports page. """
        self._set_search_field(report_name)

    @PageService()
    def access_hidden_report(self, report_name):
        """Access hidden report directly with name"""
        self._access_creport_by_name(report_name)
        self.webconsole.wait_till_load_complete()
