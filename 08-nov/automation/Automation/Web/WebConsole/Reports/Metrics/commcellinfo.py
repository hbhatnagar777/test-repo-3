from selenium.webdriver.common.by import By
"""
Module to get data from CommCell info page of Metrics
"""
from Web.Common.page_object import (
    WebAction, PageService
)


class CommCellInfo:
    """
        Class to Manage Users panel in Dashboard
        """
    def __init__(self, webconsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole

    @WebAction()
    def _get_commcell_id(self):
        """ Reads the CommCell ID"""
        ccid_xpath = "//td[text()='CommCell ID']/following-sibling::td[1]"
        return self._driver.find_element(By.XPATH, ccid_xpath).text

    @WebAction()
    def _get_gateway_ip(self):
        """ Reads the Gateway IP Address"""
        gway_xpath = "//td[text()='Gateway IP Address']/following-sibling::td[1]"
        return self._driver.find_element(By.XPATH, gway_xpath).text

    @WebAction()
    def _get_commserve_ip(self):
        """ Reads the CommCell IP"""
        ccip_xpath = "//td[text()='CommServe IP Address']/following-sibling::td[1]"
        return self._driver.find_element(By.XPATH, ccip_xpath).text

    @PageService()
    def get_commcell_id(self):
        """ Gets the CommCell ID"""
        self._get_commcell_id()

    @PageService()
    def get_gateway_ip(self):
        """ Gets the Gateway IP Address"""
        return self._get_gateway_ip()

    @PageService()
    def get_commserve_ip(self):
        """ Gets the CommCell IP"""
        self._get_commserve_ip()
