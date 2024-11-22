# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
All the classes needed to manage the browser
"""

import os
import shutil
import urllib.request
import zipfile
import time
import threading
from abc import ABC
from abc import abstractmethod
from enum import Enum
from typing import Callable
import certifi
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from Web.Common.exceptions import CVWebAutomationException

from AutomationUtils import (
    config,
    logger,
    constants as automation_constants
)
from AutomationUtils.machine import Machine


_CONF = config.get_config()
_CONSTANTS = _CONF.BrowserConstants


def _get_default_browser():
    default_browser_str = _CONSTANTS.DEFAULT_BROWSER
    for browser_type in Browser.Types:
        if browser_type.value == default_browser_str:
            return browser_type
    else:
        raise ValueError(f"[{default_browser_str}] browser not found")


class Browser(ABC):
    """
    Browser has the necessary interfaces that you can use to work with the
    selenium browser

    Since browser class is an abstract class it can't be used to create any
    objects, BrowserFactory is the class that will have to be used to
    manage the creation of Browsers.

    Please look into BrowserFactory to configure the Type of browser created

    > Creating Browser Object::

        from browser import BrowserFactory

        factory = BrowserFactory()
        browser = factory.create_browser_object()

    > Opening Browser:
    Please note that the browser would not have opened after you have
    created the browser object. You need to explicitly call the open()
    method to open browser like below::

        browser.open()

    > Handling Configurations:
    By default all the configurations are implicitly handled when you
    directly call browser.open(), if at all you need to do additional
    configurations you can look into corresponding methods inside
    Browser class

    > Example Usage:

     * Below is the recommended way create the browser, by importing
     the BrowserFactory class::

        from browser import BrowserFactory

        factory = BrowserFactory()

        browser = factory.create_browser_object()
        browser.configure_proxy("machine_name", port)  # use if you want to
                                                       # config the proxy
        browser.open()  # Only at this line the browser window would be open

        txt_box = browser.driver.find_element(By.XPATH, "//input['username']")
        txt_box.send_keys("admin")
        browser.close()

     * We also support method chaining to create the browser object
     in one line::

        from browser import BrowserFactory

        browser = BrowserFactory().create_browser_object().set_implicit_wait(30).open()
        browser.close()

     * Using ``with`` statement: Browser has a context manager implementation, which
      automatically calls the open and close methods inside the browser. Please note
      that stacktrace would be swallowed by the Browser's close method if any exception
      is raised while closing browser::

        from browser import BrowserFactory

        factory = BrowserFactory()

        # First browser instance
        with factory.create_browser_object() as browser1:
            input = browser1.driver.find_element(By.XPATH, "//input['username']")
            input.send_keys("admin")

        # Second browser instance
        with factory.create_browser_object() as browser2:
            input = browser2.driver.find_element(By.XPATH, "//input['username']")
            input.send_keys("admin")

        # Another approach
        browser = factory.create_browser_object()
        with browser:
            input = browser2.driver.find_element(By.XPATH, "//input['username']")
            input.send_keys("admin")

    """

    class Types(Enum):
        """Available browser types supported"""
        CHROME = "_ChromeBrowser"
        FIREFOX = "_FirefoxBrowser"
        IE = "_IEBrowser"
        BRAVE = "_BraveBrowser"
        EDGE = "_EdgeBrowser"

    def __init__(self, browser_name):
        """
        Args:
             browser_name (str): Can be any string which will be used to name the
             browser internally. When working with multiple browsers the browser
             name can be used to identify the browser on those modules where browser
             object was passed as an argument
        """
        self._driver: webdriver.Chrome = None
        self._http_proxy = {}
        self._browser_name = browser_name
        self._implicit_wait = _CONSTANTS.IMPLICIT_WAIT_TIME

        self._is_proxy_configured = False
        self._is_defaults_configured = False
        self._is_grid_configured = False
        self._downloads_dir = automation_constants.TEMP_DIR
        self._drag_utils = None
        self._LOG = logger.get_log()
        self._bmp_server = None
        self._bmp_proxy_server = None
        self.__cntrl_os = None
        self.__cntrl_mc = None


    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        Browser.close_silently(self)
        return False

    @property
    def driver(self):
        """
        Returns the selenium driver inside the browser

        IMPORTANT: Python 3.6 has a bug with Properties, do not
        replace the method call with definition

        Examples:
            browser.driver.find_elements(By.XPATH, "//your_xpath")
        """
        return self._get_driver()

    @property
    def name(self):
        """
        Returns the name of the browser used to create the browser
        """
        return self._browser_name

    @property
    def bmp_proxy_server(self):
        """
        Returns the BrowserMobProxy server object used to record Network calls
        """
        return self._bmp_proxy_server

    @property
    def controller_os(self):
        """
        Returns  the os of controller machine
        """
        if self.__cntrl_os is None:
            self.__cntrl_os = self.controller_machine.os_info
        return self.__cntrl_os

    @property
    def controller_machine(self):
        """
        Returns controller machine object
        """
        if self.__cntrl_mc is None:
            self.__cntrl_mc = Machine()
        return self.__cntrl_mc

    @abstractmethod
    def _get_new_webdriver_object(self):
        """
        Get the browser's driver object
        """
        raise NotImplementedError

    @abstractmethod
    def _configure_default_options(self):
        """
        Loads all the default configs for the browser to work.
        """
        raise NotImplementedError

    def _get_driver(self):
        if self._driver is None:
            raise ValueError("Driver does not exist, browser might not be open")
        return self._driver

    def _get_drag_util(self):
        """Read the JS utils file for drag and drop"""
        if self._drag_utils is None:
            fpath = os.path.join(
                automation_constants.AUTOMATION_DIRECTORY,
                "Web",
                "Common",
                "DragAndDropUtil.js"
            )
            self._drag_utils = open(fpath).read()
        return self._drag_utils

    @abstractmethod
    def configure_proxy(self,
                        machine=_CONF.HttpProxy.MACHINE_NAME,
                        port=_CONF.HttpProxy.PORT):
        """
        Configures the browser to route its requests via the specified machine's
        proxy socket

        Args:
            machine (str): The machine name to use
            port (str): port number to use
        """
        raise NotImplementedError

    @abstractmethod
    def configure_grid(self, machine):
        """
        This method is used to configure Grid options for the browser to open
        on some other specified machine.

        Args:
            machine (str): name of the machine where Grid has to run.

        Currently this method is not implemented for any browser, Please
        implement if need be.
        """
        raise NotImplementedError

    @abstractmethod
    def get_browser_type(self):
        """
        Returns the type of browser currently in use.

        Returns:
            Browser.Types: Enum containing the type of browser
        """
        raise NotImplementedError

    @abstractmethod
    def get_webdriver_options(self):
        """
        Returns the options used to configure the browser before its opened.

        Chrome is configured using the webdriver.ChromeOptions class and
        firefox is configured using the webdriver.FirefoxProfile class.

        By default only one options instance is created for, this method can
        be used to read the browser's configurations.
        """
        raise NotImplementedError

    def get_downloads_dir(self):
        """Returns the downloads directory currently in use"""
        return self._downloads_dir

    def get_implicit_wait_time(self):
        """Get the currently used wait time"""
        return self._implicit_wait

    def set_downloads_dir(self, dir_path):
        """Set the download directory to be used by the browser

        Please note that this will work only if the browser if not
        already opened.
        """
        if self._driver is not None:
            raise ValueError(
                "Can't set download dir when browser is already opened")
        self._downloads_dir = dir_path

    @abstractmethod
    def set_webdriver_options(self, options):
        """
        Use this option to set the options that browser has to be configured
        with. Please note that these options would have to be configured before
        the browser is opened

        Its recommenced you check the browser type and add the necessary
        options to configure the browser

        Example::

            chrome_options = webdriver.ChromeOptions()
            if browser.get_browser_type() == Browser.TYPE_CHROME:
                browser.set_webdriver_options(chrome_options)

            firefox_profile = webdriver.FirefoxProfile()
            if browser.get_browser_type() == Browser.TYPE_FIREFOX:
                browser.set_webdriver_options(firefox_options)

        As an alternative to the above recommended procedure you can also use
        the get_webdriver_options() and configure the options on it
        """
        raise NotImplementedError

    def set_implicit_wait_time(self, time=_CONSTANTS.IMPLICIT_WAIT_TIME):
        """
        Set the implicit wait time for the driver

        At time of writing this function, selenium did not have an elegant way
        to retrieve the wait time set, so if you set driver.implicitly_wait directly
        there is no way to retrieve the currently set wait time, we save the wait
        time to the _implicit_wait variable when its set via browser. This helps
        us to temporarily override the wait time for any specific action and set
        it back to the old value
        """
        self._implicit_wait = int(time)
        return self

    def maximize_window(self):
        """
        Maximize the browser object
        """
        self.driver.maximize_window()
        return self

    def open(self, maximize=True):
        """
        Opens the browser with the default configuration.

        By default opens with the default configuration, unless explicitly
        configuration methods are called to configure the browser

        Args:
            maximize                  (bool)   :  maximizes browser
                                                  default : True

        Returns: Browser object

        """
        self._LOG.debug("Opening browser [%s]", self.name)
        if not self._is_proxy_configured:
            self.configure_proxy()
        if _CONSTANTS.ENABLE_NETWORK_MONITORING:
            from browsermobproxy import Server
            self._LOG.debug("Creating BrowserMobProxy to record Network calls")
            if self._bmp_server is None:
                self._bmp_server = Server(
                    os.path.join(automation_constants.AUTOMATION_DIRECTORY, "CompiledBins",
                                 "bmp", "bin", "browsermob-proxy.bat")
                )
                self._bmp_server.start()
                time.sleep(3)
            self._bmp_proxy_server = self._bmp_server.create_proxy()
            time.sleep(3)
            proxy_port = self._bmp_proxy_server.proxy.split(":")[1]
            self._LOG.debug(f"BrowserMobProxy started successfully on localhost:{proxy_port}")
            self.configure_proxy("localhost", proxy_port)
            self._bmp_proxy_server.new_har("cvbrowser_network_calls")
        if not self._is_defaults_configured:
            self._configure_default_options()
        self._driver = self._get_new_webdriver_object()
        self._driver.implicitly_wait(self._implicit_wait)
        if _CONSTANTS.HEADLESS_MODE:  # In headless mode maximize might not given bigger screen
            self._driver.set_window_size(_CONSTANTS.SCREEN_WIDTH, _CONSTANTS.SCREEN_HEIGHT)
        elif maximize:
            self.maximize_window()
        return self

    def goto_file(self, file_path):
        """
        Access file using browser

        Args:
            file_path               (String) : file path to access in browser

        """
        self.driver.get(file_path)

    def close(self):
        """
        Closes the Web Browser. If you have multiple tabs open in the browser
        you would need to handle the tabs yourself, this method closes the whole
        browser.

        Its recommended not to use the driver.close method directly, instead
        call this method to keep the browser object in sync with driver object
        """
        if _CONSTANTS.ENABLE_NETWORK_MONITORING:
            self._LOG.debug("Stopping BrowserMobProxy server")
            if self._bmp_proxy_server is not None:
                self._bmp_proxy_server.close()
            if self._bmp_server is not None:
                self._bmp_server.stop()
            self._bmp_proxy_server = None
            self._bmp_server = None
        self._LOG.debug("Closing browser [%s]", self.name)
        if self.driver is not None:
            self.driver.close() # Fix to avoid CPU Spike. Chrome version >= 125
            self.driver.quit()
            del self._driver

    @staticmethod
    def close_silently(browser):
        """
        Use this method for webdriver cleanup inside finally statement
        where you don't want the testcase to fail because browser could
        not be closed

        Args:
             browser (Browser): Instance of Browser implementation
        """
        try:
            if browser is not None:
                if browser.driver is not None:
                    browser.close()
        except Exception as e:
            logger.get_log().warning(
                "Exception received while closing browser; " + str(e)
            )

    def click_web_element(self, web_element):
        """
        Use this to click on any UI component if selenium click fails
        with the following error even when the element is visible on the page

        `selenium.common.exceptions.WebDriverException: Message: unknown error:
        Element is not clickable at point (-5, 254)`

        Args:
            web_element: WebElement object
        """
        if not isinstance(web_element, WebElement):
            raise ValueError("argument is not an instance of WebElement")
        self._driver.execute_script("arguments[0].click();", web_element)

    def drag_and_drop_by_xpath(self, source_xpath, target_xpath):
        """
        Drag the source component identified by source xpath, and drop it on
        the target component identified by target_xpath.

        ActionChains was not working on all the pages consistently, use this as
        an alternative to it.

        Args:
            source_xpath (str): XPath of the source element
            target_xpath (str): XPath of the target element
        """
        if source_xpath.find("\"") != -1 or target_xpath.find("\"") != -1:
            raise ValueError("Double not supported in source_xpath or target_xpath")
        self.driver.find_element(By.XPATH, source_xpath)  # Validate for correct XPath
        self.driver.find_element(By.XPATH, target_xpath)  # Validate for correct XPath
        js = """
             function getElementByXpath(path) {
               return document.evaluate(
                    path, document, null, 
                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null).singleNodeValue;
             }
             source_object = getElementByXpath("%s")
             target_object = getElementByXpath("%s")
             $(source_object).simulateDragDrop({ dropTarget: $(target_object)});
             """ % (source_xpath, target_xpath)
        self.driver.execute_script(self._get_drag_util() + js)

    def open_new_tab(self):
        """
        To open a new tab in the current browser and open the URL
        """
        # To open a new tab
        self.driver.execute_script("window.open('');")

    def switch_to_latest_tab(self):
        """
        To switch to the latest tab
        """
        windows = self.driver.window_handles
        self.driver.switch_to.window(windows[-1])

    def switch_to_first_tab(self):
        """
        To switch to the latest tab
        """
        windows = self.driver.window_handles
        self.driver.switch_to.window(windows[0])

    def clear_browser_networkstats(self):
        """Clear the performance stats"""
        clear_cache_stats = """var performance = window.performance || window.mozPerformance || window.msPerformance 
        || window.webkitPerformance || {}; performance.clearResourceTimings() """
        if hasattr(_CONF, "PERFORMANCE_TEST") and _CONF.PERFORMANCE_TEST:
            self.driver.execute_script(clear_cache_stats)

    def get_browser_networkstats(self):
        js = """var performancetest = window.performance ; var networktest = performancetest.getEntriesByType('resource'); return networktest; """
        if hasattr(_CONF, "PERFORMANCE_TEST") and _CONF.PERFORMANCE_TEST:
            stats = self.driver.execute_script(js)
            return stats
        else:
            return None

    def accept_alert(self, alert_id):
        """Switch to the alert and accept it
            Args:
                alert_id : (str) -- ID of the alert opened
        """
        self.driver.find_element(By.XPATH, f'//*[@id="{alert_id}"]').click()
        test_pop = self.driver.switch_to.alert
        test_pop.accept()

    def get_text_from_alert(self):
        """Gets the text from alert box"""
        alert = self.driver.switch_to.alert
        text = alert.text
        alert.accept()
        return text

    def close_current_tab(self):
        """
        To close the current tab
        """
        self.driver.execute_script("window.close('');")

    def open_url_in_new_tab(self, url):
        """
        Opens the given url in a new tab and change focus on the new tab opened

        Args:
            url     (str)--the url to be opened

        Returns:None
        """
        self.driver.execute_script("window.open('" + url + "');")
        window_list = self.driver.window_handles
        for window_id in window_list:
            self.driver.switch_to.window(window_id)
            if self.driver.current_url == url:
                return

    def switch_to_tab(self, page_to_load):
        """

        Switches to the given page in browser

        Args:

            page_to_load (str)   --  Page to be loaded in the browser

        Returns: True if the page is found otherwise False
        """
        windows_list = self.driver.window_handles
        for window_id in range(len(windows_list)):
            self.driver.switch_to.window(windows_list[window_id])
            if self.driver.current_url == page_to_load:
                return True
        return False

    def wait_redirection(self, action: Callable, wait_time: int = 10, new_tabs: int = 0):
        """
        Waits for redirection after performing an action

        Args:
            action  (Callable)  -   an action function to call after which redirection is expected
            wait_time   (int)   -   how long to wait for redirection
            new_tabs (int)      -   number of new tabs expected to open instead of same tab redirection
        """
        initial_tabs = len(self.driver.window_handles)
        initial_url = self.driver.current_url
        action()
        if new_tabs:
            WebDriverWait(self.driver, wait_time).until(
                lambda driver: len(driver.window_handles) > initial_tabs,
                message=f'No new tabs opened, waited for {wait_time} seconds'
            )
            if (opened_tabs := len(self.driver.window_handles) - initial_tabs) != new_tabs:
                raise CVWebAutomationException(f"expected {new_tabs} tabs, but only {opened_tabs} tabs opened")
        else:
            WebDriverWait(self.driver, wait_time).until(
                lambda driver: driver.current_url != initial_url,
                message=f'No url change, waited for {wait_time} seconds'
            )

    @abstractmethod
    def get_latest_downloaded_file(self):
        """
        This method is used to get filepath after any file got downloaded.
        Reads the first file in the top in downloads (i.e. latest downloaded file)

        Currently, this method is only implemented for Chrome, Please
        implement for other browsers if need be.
        """
        raise NotImplementedError

    def get_js_variable(self, var_name: str):
        """
        Gets the given JavaScript variable's value from browser

        Args:
            var_name    (str)   -   name of variable (Example: 'cv.varX')

        Returns:
            var_value   (object)   -   value of that variable (could be str/dict/tuple depending on js data type)
        """
        return self._driver.execute_script(f'return {var_name};')

    def scroll_down(self):
        """
        Scrolls down to the bottom of the web page
        """
        self._driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")


class _ChromeBrowser(Browser):

    def __init__(self, browser_name):
        super().__init__(browser_name)
        self.__profile = None
        self._driver_process_name = 'chromedriver'

    def _connect_to_chrome(self, executable=None):
        if executable:
            service = ChromeService(os.path.join(automation_constants.AUTOMATION_DIRECTORY,
                                          "CompiledBins", executable))
        else:
            service = ChromeService()
        return webdriver.Chrome(service=service, options=self.get_webdriver_options())

    def _get_new_webdriver_object(self):
        if self._driver is None:
            if self.controller_os == 'WINDOWS':
                executable = "chromedriver.exe"
            else:
                executable = "chromedriver"
            try:
                self._driver = self._connect_to_chrome()  # selenium downloads the executable at run time
            except Exception as msg:  # fail safe for selenium manager issues
                self._LOG.exception(msg)
                self._LOG.info(
                    'Selenium manager failed to access latest chrome driver retrying manually'
                )
            # if selenium manager fails try to connect with existing chrome binary
            if self._driver is None:
                try:
                    self._driver = self._connect_to_chrome(executable)
                except Exception as msg:  # if existing chromedirver doesnt work then download fresh:
                    self._download_latest_driver()
                    self._driver = self._connect_to_chrome(executable)
        return self._driver

    def _download_latest_driver(self):
        """Download latest chromedriver"""
        path = os.path.join(automation_constants.AUTOMATION_DIRECTORY, "CompiledBins")
        fpath = os.path.join(path, 'chromedriver.zip')
        latest_release_url = 'https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE'
        self._LOG.info('Finding latest chromedriver version')
        file = urllib.request.urlopen(latest_release_url, cafile=certifi.where())
        version = file.read()
        self._LOG.info(f'Downloading chromedriver version {version.decode()} to : ' + fpath)
        if self.controller_os == 'WINDOWS':
            file_name = "chromedriver-win64"
        else:
            file_name = "chromedriver-linux64"
        url = (
            f'https://storage.googleapis.com/chrome-for-testing-public/{version.decode()}/win64/{file_name}.zip'
        )
        file = urllib.request.urlopen(url, cafile=certifi.where())
        # save file to system
        with open(fpath, 'wb') as output:
            output.write(file.read())
        if self.controller_machine.is_process_running(process_name=self._driver_process_name):
            self._LOG.info(f'Stopping running chromedriver process to update it with latest')
            self.controller_machine.kill_process(self._driver_process_name)
        self._LOG.info(f'unzipping chromedriver to path {path}')
        with zipfile.ZipFile(fpath, 'r') as zip_ref:
            zip_ref.extractall(path)

        # in unix set execute permission to chromedriver binary
        if self.controller_os != 'WINDOWS':
            shutil.copy(os.path.join(path, file_name, self._driver_process_name), path)
            self.controller_machine.change_file_permissions(
                os.path.join(path, self._driver_process_name), 755
            )
        else:
            shutil.copy(os.path.join(path, file_name, self._driver_process_name + '.exe'), path)

    def _configure_default_options(self):
        profile = self.get_webdriver_options()
        profile.add_experimental_option(
            "prefs",
            {"download.default_directory": self.get_downloads_dir(),
             "download.prompt_for_download": False,
             "download.directory_upgrade": True,
             "profile.password_manager_leak_detection":False,
             "plugins.plugins_disabled": ["Chrome PDF Viewer"],
             "safebrowsing.enabled": True,
             "profile.default_content_setting_values.automatic_downloads": 1})
        profile.add_argument('--ignore-certificate-errors')
        profile.add_argument('--disable-features=OverscrollHistoryNavigation')
        if _CONSTANTS.HEADLESS_MODE:
            profile.add_argument('--headless=new')
            # profile.add_argument('--no-sandbox') this causing high cpu usage.
            profile.add_argument('--disable-gpu')
            profile.add_argument(
                f'--window-size={_CONSTANTS.SCREEN_WIDTH},{_CONSTANTS.SCREEN_HEIGHT}'
            )
            # profile.add_argument("force-device-scale-factor=0.5")
            profile.add_experimental_option('excludeSwitches', ['enable-logging'])


    def get_browser_type(self):
        return Browser.Types.CHROME

    def get_webdriver_options(self):
        if self.__profile is None:
            self.__profile = webdriver.ChromeOptions()
            self.__profile.add_experimental_option('excludeSwitches', ['enable-logging'])  # disables chrome logging
        return self.__profile

    def configure_proxy(self,
                        machine=_CONF.HttpProxy.MACHINE_NAME,
                        port=_CONF.HttpProxy.PORT):
        self._is_proxy_configured = True
        if machine != "" and port != "":
            self._LOG.info('Configuring Http proxy')
            profile = self.get_webdriver_options()
            profile.add_argument("--proxy-server=http://%s:%s" % (machine, str(port)))

    def set_webdriver_options(self, options):
        self._is_defaults_configured = True
        self.__profile = options

    def configure_grid(self, machine):
        raise NotImplementedError(
            "Method not implemented for Chrome, please implement if need be")

    def get_latest_downloaded_file(self):
        """
        Returns the file path of latest downloaded file

        Returns:
            file_path   (str)   -   path of the latest downloaded file if it exists
            None                -   if downloads is empty
        """
        self._driver.execute_script("window.open()")
        self._driver.switch_to.window(self._driver.window_handles[-1])
        self._driver.get('chrome://downloads')
        # chrome://downloads loads very fast, but just to be safe lets wait 1 sec
        time.sleep(1)
        fname = None
        try:
            fname = self._driver.execute_script(
                        "return document.querySelector('downloads-manager')"
                        ".shadowRoot.querySelector('#downloadsList downloads-item')"
                        ".shadowRoot.querySelector('div#content  #file-link').text"
                    )
        except:
            pass
        self._driver.close()
        self._driver.switch_to.window(self._driver.window_handles[-1])
        if fname:
            return f'{self._downloads_dir}\\{fname}'
        else:
            return None

class _FirefoxBrowser(Browser):

    def __init__(self, browser_name):
        super().__init__(browser_name)
        self.__profile = None
        self.__options = None
        self._allowed_mime_types = (
            "application/pdf, text/csv,text/html, text/plain, application/xml, "
            "text/xml, application/octet-stream, application/vnd.ms-word,"
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document, "
            "application/vnd.openxmlformats-officedocument.presentationml.presentation, "
            "application/vnd.ms-excel, application/exe, application/vnd.ms-htmlhelp")

    def _connect_to_firefox(self, executable=None):
        if executable:
            service = FirefoxService(os.path.join(automation_constants.AUTOMATION_DIRECTORY,
                                                  "CompiledBins", executable))
        else:
            service = FirefoxService()
        return webdriver.Firefox(service=service, options=self.get_webdriver_options())

    def _get_new_webdriver_object(self):
        if self._driver is None:
            if self.controller_os == 'WINDOWS':
                executable = "geckodriver.exe"
            else:
                executable = "geckodriver"
        self._driver = self._connect_to_firefox()  # selenium downloads the executable at run time
        return self._driver

    def _configure_default_options(self):
        profile = self.get_profile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.helperApps.alwaysAsk.force", False)
        profile.set_preference("browser.download.manager.showWhenStarting",
                               False)
        profile.set_preference("browser.download.dir", self.get_downloads_dir())
        profile.set_preference("plugin.disable_full_page_plugin_for_types",
                               "application/pdf")
        profile.set_preference("pdfjs.disabled", True)
        profile.set_preference("browser.download.manager.showAlertOnComplete",
                               False)
        profile.set_preference("browser.download.viewableInternally.enabledTypes", "")
        profile.set_preference("browser.download.panel.shown", True)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk",
                               self._allowed_mime_types)
        if _CONSTANTS.HEADLESS_MODE:
            options = self.get_options()
            options.add_argument('--headless')
        profile.update_preferences()

    def get_browser_type(self):
        return Browser.Types.FIREFOX

    def get_webdriver_options(self):
        if self.__options is None:
            self.__options = Options()
        return self.__options

    def get_profile(self):
        if self.__profile is None:
            self.__profile = webdriver.FirefoxProfile()
        return self.__profile

    def configure_proxy(self,
                        machine=_CONF.HttpProxy.MACHINE_NAME,
                        port=_CONF.HttpProxy.PORT):
        self._is_proxy_configured = True
        if machine != "" and port != "":
            self._LOG.info('Configuring Http proxy')
            profile = self.get_webdriver_options()
            profile.set_preference("network.proxy.type", 1)
            profile.set_preference("network.proxy.http", str(machine))
            profile.set_preference("network.proxy.http_port", str(port))
            profile.update_preferences()

    def set_webdriver_options(self, options):
        self._is_defaults_configured = True
        self.__profile = options

    def configure_grid(self, machine):
        raise NotImplementedError(
            "Method not implemented for Firefox, please implement if need be")

    def get_latest_downloaded_file(self):
        """
        Returns the file path of latest downloaded file

        Returns:
            file_path   (str)   -   path of the latest downloaded file if it exists
            None                -   if downloads is empty
        """
        self._driver.execute_script("window.open()")
        self._driver.switch_to.window(self._driver.window_handles[-1])
        self._driver.get('about:downloads')
        time.sleep(1)
        fname = None
        try:
            fname = self._driver.execute_script(
                        "return document.querySelector('#downloadsListBox').childNodes[0]"
                        ".querySelector('.downloadTarget').value "
                    )
        except:
            pass
        self._driver.close()
        self._driver.switch_to.window(self._driver.window_handles[-1])
        if fname:
            return f'{self._downloads_dir}\\{fname}'
        else:
            return None


class _IEBrowser(Browser):

    def __init__(self, browser_name):
        super().__init__(browser_name)
        self.__capabilities = None
        self._implicit_wait = 10
        self._is_proxy_configured = True  # PTo skip proxy setting

    def _get_new_webdriver_object(self):
        driver_path = os.path.join(
            automation_constants.AUTOMATION_DIRECTORY,
            "CompiledBins", "IEDriverServer.exe")
        return webdriver.Ie(driver_path)

    def _configure_default_options(self):
        self.__capabilities = self.get_webdriver_options()
        self.__capabilities["ignoreZoomSetting"] = True
        self.__capabilities["nativeEvents"] = True
        self.__capabilities["ignoreProtectedModeSettings"] = True

    def get_browser_type(self):
        return Browser.Types.IE

    def get_webdriver_options(self):
        if self.__capabilities is None:
            self.__capabilities = webdriver.DesiredCapabilities.INTERNETEXPLORER
        return self.__capabilities

    def configure_proxy(self,
                        machine=_CONF.HttpProxy.MACHINE_NAME,
                        port=_CONF.HttpProxy.PORT):
        raise NotImplementedError

    def set_webdriver_options(self, options):
        self._is_defaults_configured = True
        self.__capabilities = options

    def configure_grid(self, machine):
        raise NotImplementedError(
            "Method not implemented for IE, please implement if need be")

    def get_latest_downloaded_file(self):
        raise NotImplementedError("Method not implemented for IE, please implement if needed")


class _BraveBrowser(_ChromeBrowser):
    def __init__(self, browser_name):
        super().__init__(browser_name)
        self.__profile = None

    def get_webdriver_options(self):
        if self.__profile is None:
            self.__profile = webdriver.ChromeOptions()
            self.__profile.binary_location = _CONSTANTS.BRAVE_BROWSER_PATH
        return self.__profile

class _EdgeBrowser(Browser):

    def __init__(self, browser_name):
        """
        Initialize an instance of the _EdgeBrowser class.

        Args:
            browser_name (str): The name of the browser ('_EdgeBrowser').

        """
        super().__init__(browser_name)
        self._driver_process_name = 'msedgedriver'
        self._driver = None
        self.__options = None

    def _connect_to_edge(self, executable=None):
        """
        Connect to the Edge browser using the Edge WebDriver.

        Args:
            executable (str)    :   EdgeDriver executable name ('msedgedriver.exe').

        Returns:
            WebDriver: An instance of the Edge WebDriver.

        """
        if executable:
            service = EdgeService(os.path.join(automation_constants.AUTOMATION_DIRECTORY,
                                          "CompiledBins", executable))
        else:
            service = EdgeService()
        return webdriver.Edge(service=service, options=self.get_webdriver_options())

    def _get_new_webdriver_object(self):
        """
        Get a new WebDriver object for the Edge browser.

        Returns:
            WebDriver: An instance of the Edge WebDriver.

        """
        if self._driver is None:
            executable = "msedgedriver.exe" if self.controller_os == 'WINDOWS' else "msedgedriver"
            try:
                self._driver = self._connect_to_edge()  # selenium downloads the executable at run time
            except Exception as msg:  # fail safe for selenium manager issues
                self._LOG.exception(msg)
                self._LOG.info(
                    'Selenium manager failed to access latest edge driver retrying manually'
                )

            # if selenium manager fails try to connect with existing edge binary
            if self._driver is None:
                try:
                    self._driver = self._connect_to_edge(executable)
                except Exception as msg:  # if existing edge driver doesnt work then download fresh:
                    self._download_latest_driver()
                    self._driver = self._connect_to_edge(executable)
        return self._driver

    def _download_latest_driver(self):
        """
        Download the latest version of the EdgeDriver executable.

        This method downloads the latest EdgeDriver executable and updates it in the system.

        """
        path = os.path.join(automation_constants.AUTOMATION_DIRECTORY, "CompiledBins")
        fpath = os.path.join(path, 'edgedriver.zip')
        latest_release_url = 'https://msedgedriver.azureedge.net/LATEST_STABLE'
        self._LOG.info('Finding latest edgedriver version')
        response = urllib.request.urlopen(latest_release_url, cafile=certifi.where())
        version = response.read().decode("utf-16").strip()
        self._LOG.info(f'Downloading edgedriver version {version} to: {fpath}')

        if self.controller_os == 'WINDOWS':
            file_name = "edgedriver_win32.zip"
        else:
            file_name = "edgedriver_linux64.zip"
        url = f'https://msedgedriver.azureedge.net/{version}/{file_name}'
        response_file = urllib.request.urlopen(url, cafile=certifi.where())

        # Save file to system
        with open(fpath, 'wb') as output:
            output.write(response_file.read())

        if self.controller_machine.is_process_running(process_name=self._driver_process_name):
            self._LOG.info('Stopping running edgedriver process to update it with the latest version')
            self.controller_machine.kill_process(self._driver_process_name)

        self._LOG.info(f'Unzipping edgedriver to path {path}')
        with zipfile.ZipFile(fpath, 'r') as zip_ref:
            zip_ref.extractall(path)

        # On Unix systems, set execute permission for edgedriver binary
        if self.controller_os != 'WINDOWS':
            self.controller_machine.change_file_permissions(os.path.join(path, self._driver_process_name), 755)

    def _configure_default_options(self):
        """
        Configure default options for the Edge browser.

        This method sets default options for the Edge browser, such as download settings, headless mode, etc.

        """
        options = self.get_webdriver_options()
        if self.controller_os == 'WINDOWS':
            options.use_chromium = True
            options.add_experimental_option("prefs", {
                "download.default_directory": self.get_downloads_dir(),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.plugins_disabled": ["Chrome PDF Viewer"],
                "safebrowsing.enabled": True
            })
            options.add_argument('--ignore-certificate-errors')
            if _CONSTANTS.HEADLESS_MODE:
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument(f'--window-size={_CONSTANTS.SCREEN_WIDTH},{_CONSTANTS.SCREEN_HEIGHT}')
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
        else:
            # Handle configuration for other operating systems
            pass

    def get_browser_type(self):
        """
        Get the type of the browser.

        Returns:
            str: The browser type, which is '_EdgeBrowser'.

        """
        return Browser.Types.EDGE

    def get_webdriver_options(self):
        """
        Get the WebDriver options for the Edge browser.

        Returns:
            WebDriverOptions: An instance of Edge WebDriverOptions.

        """
        if self.__options is None:
            self.__options = webdriver.EdgeOptions()
        return self.__options

    def configure_proxy(self, machine=_CONF.HttpProxy.MACHINE_NAME, port=_CONF.HttpProxy.PORT):
        """
        Configure HTTP proxy settings for the Edge browser.

        Args:
            machine (str)   : The proxy machine name or IP address.
            port (int)      : The proxy port number.

        """
        self._is_proxy_configured = True
        if machine and port:
            self._LOG.info('Configuring HTTP proxy')
            options = self.get_webdriver_options()
            options.add_argument(f"--proxy-server=http://{machine}:{str(port)}")

    def set_webdriver_options(self, options):
        """
        Set custom WebDriver options for the Edge browser.

        Args:
            options (WebDriverOptions): Custom Edge WebDriver options to set.

        """
        self._is_defaults_configured = True
        self.__options = options

    def configure_grid(self, machine):
        raise NotImplementedError("Method not implemented for Edge, please implement if needed")

    def get_latest_downloaded_file(self):
        """
        Returns the file path of latest downloaded file

        Returns:
            file_path   (str)   -   path of the latest downloaded file if it exists
            None                -   if downloads is empty
        """
        self._driver.execute_script("window.open()")
        self._driver.switch_to.window(self._driver.window_handles[-1])
        self._driver.get('edge://downloads/all')
        time.sleep(1)
        fname = None
        try:
            fname = self._driver.execute_script(
                        "return document.querySelectorAll('div[id*=\"downloads-item\"]')[0]"
                        ".querySelector('*[id*=\"open\"]').ariaLabel"
                    )
        except:
            pass
        self._driver.close()
        self._driver.switch_to.window(self._driver.window_handles[-1])
        if fname:
            return f'{self._downloads_dir}\\{fname}'
        else:
            return None


class BrowserFactory(object):
    """
    This class is used to control and manage the creation of the browsers
    used by the TestCases.

    Since this class is a singleton, all the instances would return the same
    instance, so calling the below code would always return True::

        factory1 = BrowserFactory()
        factory2 = BrowserFactory()
        return factory1 is factory2

    To create single instance of all browser types, use the Browser.Types enum,
    Example::

        factory = BrowserFactory()
        for _type in Browser.Types:
            browser = factory.create_browser_object(browser_type=_type)
            browser.open()

    For info on creating and configuring browsers, please refer Browser class
    """
    _thread_local = threading.local()
    _instance = {}

    def __init__(self):
        self._browsers = {}
        self._LOG = logger.get_log()

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls._thread_local, 'instance'):
            instance = super(BrowserFactory, cls).__new__(cls)
            cls._thread_local.instance = instance
        return cls._thread_local.instance

    def create_browser_object(self,
                              browser_type=_get_default_browser(),
                              name="defaultBrowser") -> Browser:
        """Creates and configures the type of browser to be created

        Args:
            browser_type (Browser.Type): Use the enum to create any
                specific browser other than the default one set on
                config.json file
            name (str): Name of the browser
        """
        self._LOG.debug(
            "Creating [%s] browser object with name [%s]",
            browser_type.value,
            name
        )
        if browser_type not in Browser.Types:
            raise KeyError(f"Unsupported browser type [{browser_type.value}] received")
        browser = globals()[browser_type.value]
        self._browsers[name] = browser(name)
        return self._browsers[name]

    def get_all_created_browsers(self):
        """Returns all the browser objects created by the BrowserFactory
         This also includes the browsers which are already closed
        """
        return self._browsers
