"""
This module is used to process the actions on apps. This includes Android as well as IOS.
"""
import abc
from time import sleep
from appium import webdriver
from appium.webdriver.common.touch_action import TouchAction
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException

from AutomationUtils import logger


class AppManager(metaclass=abc.ABCMeta):
    """
    AppManager has the necessary interfaces and definitions that can used to work with the appium driver
    """

    def __init__(self):
        self._driver = None
        self._desired_capabilities = {}
        self.log = logger.get_log()

    @property
    def driver(self):
        """
        Used for different actions to be performed on appium driver.
        """
        if self._driver is None:
            raise TypeError("Driver does not exist.")
        return self._driver

    def set_implicit_wait_time(self, time_out=30):
        """
        Set the implicit wait time for the driver
        Args:
            time_out: Wait till specified seconds
        default: 30 seconds
        """
        self.driver.implicitly_wait(time_out)

    def disable_implicit_wait_time(self):
        """
        set the implicit wait time to 0.
        """
        self.driver.implicitly_wait(0)

    def _create_driver(self):
        """
        Creates driver and launches the app.
        """
        self._driver = webdriver.Remote('http://localhost:4723/wd/hub', self._desired_capabilities)

    def open_app(self):
        """
        Configures desired capabilities, creates the driver and sets default implicit wait time.
        """
        self.log.info("Opening app.")
        self._configure_desired_capabilities()
        self._create_driver()
        self.set_implicit_wait_time()

    def close(self):
        """
        Closes the driver.
        """
        if self.driver is not None:
            self.driver.close()

    @abc.abstractmethod
    def _configure_desired_capabilities(self):
        """
        Set required desired capabilities.
        """
        raise NotImplementedError

    def quit_driver(self):
        """
        Quits the driver instance.
        """
        if self.driver is not None:
            self.driver.quit()

    def scroll_down(self):
        """
        Scrolls to down into any app.
        """
        self._driver.swipe(270, 500, 270, 200)
        sleep(5)

    def scroll_up(self):
        """
        Scrolls to up in any app.
        """
        self.driver.swipe(470, 200, 270, 500, 200)
        sleep(5)

    def drag_to_top(self):
        """
        Drags to the top in screen.
        """
        while True:
            list_of_text = self.get_list_of_elements()
            self.scroll_up()
            list_of_text_2 = self.get_list_of_elements()
            #  Top element is same as top element after scrolling 2 times then it has reached to top in the screen.
            if list_of_text == list_of_text_2:
                return

    def get_list_of_elements(self):
        """
        Gets all the elements in screen and stores in elements list.
        """
        list_of_elements = []
        elements = []
        try:
            elements = self.driver.find_elements(By.CLASS_NAME, "android.widget.TextView")
        except Exception as e:
            pass
        for each_element in elements:
            list_of_elements.append(each_element.text)
        return list_of_elements

    def _get_element_by_text(self, element_text):
        """
        Finds element by specified text.
        Args:
            element_text: (String) Specify the element text to find.

        Returns: Returns element if its found or else returns empty list.

        """
        element = self._driver.find_elements(By.XPATH, "//*[@text='" + element_text + "']")
        if element:
            return element[0]
        else:
            return element

    def get_element_by_text(self, element_text, scroll=True):
        """
        Finds the object with specified element_text and return the element. If its not found the scrolls down if
        scrolling is enabled.
        :param element_text:Specify the element text to be searched on screen.
        :param scroll:True/False
            Default: True(Scrolling is enabled.)
        :return:Web driver Element
        """
        if scroll is True:
            self.disable_implicit_wait_time()
        last_element = None
        while True:
            self.log.info("Finding element with the text:%s", str(element_text))
            element = self._get_element_by_text(element_text)
            if element:
                self.set_implicit_wait_time()
                return element
            elif element == [] and scroll is False:
                #  In case of options like 'YES'/'No', its not required to scroll.
                raise NoSuchElementException(msg="Failed to find element:%s" % element_text)
            else:
                #  If element is not found on screen,then scrolls down till last element and searched for the element.
                elements_list = self.get_list_of_elements()
                previous_element = last_element
                last_element = elements_list[-1]
                if previous_element == last_element:
                    raise NoSuchElementException(msg="Failed to find element after scroll:%s" % element_text)
                self.scroll_down()
                sleep(5)

    def long_press_element(self, element):
        """
        Long press on specified element.
        :param element:<Object>web driver element
        """
        action = TouchAction(self.driver)
        action.long_press(element).release().perform()

    def hide_keyboard(self):
        """
        Hides keyboard if its opened.
        """
        try:
            self.driver.hide_keyboard()
        except WebDriverException:
            pass
