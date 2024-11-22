from abc import ABC, abstractmethod

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from Web.Common.page_object import WebAction

from Web.Common.cvbrowser import Browser
from Web.AdminConsole.adminconsole import AdminConsole


class CRComponent(ABC):
    """
    All components on custom reports directly or indirectly inherit this class
    """

    def __init__(self, title):
        """
        Args:
            title (str): Title of the CustomReport component
        """
        self.__browser: Browser = None
        self.__adminconsole: AdminConsole = None
        self.__driver: Browser.driver = None
        self.__x: str = None

        self.title = title
        self.dataset_name = None
        self.page_name = None
        self.id = None

    @property
    def _driver(self):
        if self.__driver is None:
            raise ValueError("driver not initialized, was add_component called ?")
        return self.__driver

    @property
    def _adminconsole(self):
        if self.__adminconsole is None:
            raise ValueError("adminconsole not initialized, was add_component called ?")
        return self.__adminconsole

    @property
    def _browser(self):
        if self.__browser is None:
            raise ValueError("browser not initialized, was add_component called ?")
        return self.__browser

    @_driver.setter
    def _driver(self, value):
        self.__driver = value

    @_browser.setter
    def _browser(self, value):
        self.__browser = value

    @_adminconsole.setter
    def _adminconsole(self, value):
        self.__adminconsole = value

    @property
    def _x(self):
        """Return the base component XPath.

        Simply kept it 'x' to avoid long names in xpath string"""
        if self.__x is None:
            self.__x = f"//*[@id='{self.id}']"
        return self.__x

    def _set_x(self, id_=None, xp=None):
        """
        Set base component XPath
        Args:
             id_ : Set the component ID, Base XPath will be derived
                as `"//*[@id='%s']" % id`
             xp : Directly use the supplied value as base XP, set id to None
                while using xp
        """
        if xp is None:
            self.__x = f"//*[@id='{id_}']"
        else:
            self.__x = xp

    @WebAction()
    def _select_current_component(self):
        """Clicks the current component"""
        WebDriverWait(self._driver, 20).until(expected_conditions.presence_of_element_located((By.XPATH, self._x)))
        component = self._driver.find_element(By.XPATH, self._x)
        component.click()

    def __str__(self):
        return f"<{self.__class__.__name__} Title=[{self.title}] ID=[{id(self)}]>"


class CRComponentViewer(CRComponent):
    """All the actions common to all _components on viewer go to this class"""

    @WebAction()
    def _get_id_from_component_title(self, title):
        """Get component ID from component Title"""
        try:
            web_obj = self._driver.find_element(By.XPATH,
                                                f"//*[contains(@class, 'title')]//*[text()='{title}']"
                                                f"/ancestor::div[contains(@class, 'panel-container')]")
        except NoSuchElementException:  # for column level id checks above xpath wont work
            web_obj = self._driver.find_element(By.XPATH,
                                                f"//*[text()='{title}']"
                                                f"/ancestor::div[contains(@class, 'panel-container')]")
        return web_obj.get_attribute("id")

    @WebAction()
    def _get_id_from_component_type(self):
        """Get component ID from component Type"""
        web_obj = self._driver.find_element(By.XPATH,
                                            f"//div[contains(@class, '{self.type}')]"
                                            f"/div[contains(@class, 'panel-container')]")
        return web_obj.get_attribute("id")

    @property
    @abstractmethod
    def type(self):
        """
        Override this as variable inside subclass and return the
        components type

        The type name has to exactly match what has been set on data-component-type on li tag
        of Component
        this will be used to access the component if title is not set
        """
        raise NotImplementedError

    def configure_viewer_component(self, adminconsole, page, comp_id=None):
        """
        Do not call this method explicitly, it would automatically be called
        when you add this component to Viewer
        """
        self._adminconsole = adminconsole
        self._browser = adminconsole.browser
        self._driver = adminconsole.browser.driver
        self.page_name = page
        if comp_id:
            self.id = comp_id
        elif self.title:
            self.id = self._get_id_from_component_title(self.title)
        else:
            self.id = self._get_id_from_component_type()
        self._set_x(self.id)
