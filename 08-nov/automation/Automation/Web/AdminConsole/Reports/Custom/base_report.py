from abc import ABC

from selenium.webdriver.common.by import By

from Web.Common.page_object import WebAction, PageService


class BaseReportPage(ABC):
    """
    Common operations for CustomReport Viewer and Builder
    """

    def __init__(self, adminconsole):
        """
        initializes base report page
        """
        self._adminconsole = adminconsole
        self._browser = adminconsole.browser
        self._driver = adminconsole.browser.driver

    @WebAction()
    def __get_all_component_titles(self):
        """Get all component titles"""
        titles = self._driver.find_elements(By.XPATH,
                                            "//*[contains(@class, 'panel-title')]"
                                            )
        return [title.text for title in titles]

    @WebAction()
    def __get_all_input_names(self):
        """Get the name of all the inputs"""
        return [
            ip.text for ip in
            self._driver.find_elements(By.XPATH, "//*[contains(@class, 'inputsRow')]//label")
            if ip.is_displayed()
        ]

    @PageService()
    def get_all_component_titles(self, page=None):
        """Returns the title of all custom report components

        Return:
            (list): Text containing all component names
        """
        # if page:
        #     self.switch_page(page)
        return self.__get_all_component_titles()

    @PageService()
    def get_all_input_names(self):
        """Get all the available input names"""
        return self.__get_all_input_names()
