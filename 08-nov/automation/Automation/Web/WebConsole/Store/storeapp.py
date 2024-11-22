from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import os
import time
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys

from AutomationUtils import logger, config, constants
from Web.Common.exceptions import CVTimeOutException
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    WebAction,
    PageService
)


def get_store_config():
    return config.get_config(
        json_path=os.path.join(
            constants.AUTOMATION_DIRECTORY,
            "Reports",
            "store_config.json"
        )
    )


_CONFIG = config.get_config()
_STORE_CONFIG = get_store_config()


class StoreApp:

    """
    This class contains the methods used to interact with Store UI
    """

    _SEARCH_FIELD_XPATH = "//input[@placeholder='Search' and @type='text']"

    def __init__(self, webconsole):
        """
        Args:
             webconsole (WebConsole): WebConsole object
        """
        self._webconsole = webconsole
        self._browser = self._webconsole.browser
        self._driver = self._webconsole.browser.driver

        self._is_cloud_login_complete = False  # Check if cloud login is complete

    @WebAction()
    def _click_install_on_first_package(self):
        """Click Install on first package"""
        install_btn = self._driver.find_element(By.XPATH, 
                "//div[@class='actionBtn']/a[text()='Install']")
        install_btn.click()

    @WebAction()
    def _click_purchase_button(self):
        """Click Purchase button"""
        purchase_btn = self._driver.find_element(By.XPATH, 
            "//div[@class='actionBtn']/a[text()='Purchase']")
        purchase_btn.click()

    @WebAction()
    def _click_open_button(self):
        """Click Open button"""
        open_btn = self._driver.find_element(By.XPATH, 
            f"//div[@class='actionBtn']/a[text()='Open']")
        open_btn.click()

    @WebAction()
    def _click_update_on_first_package(self):
        """Click Update on first package"""
        update_btn = self._driver.find_element(By.XPATH, 
                "//div[@class='actionBtn']/a[text()='Update']")
        update_btn.click()

    @WebAction()
    def _click_download_on_first_package(self):
        """Click Download on first package"""
        download_btn = self._driver.find_element(By.XPATH, 
                "//div[@class='actionBtn']/a[text()='Download']")
        download_btn.click()

    @WebAction()
    def _click_package(self, name):
        """Click Package name"""
        package_link = self._driver.find_element(By.XPATH, 
            "//span[text()='" + name + "']")
        package_link.click()

    @WebAction()
    def _click_category(self, name):
        """Click on Package category"""
        category = self._driver.find_element(By.XPATH, 
            "//nav[contains(@class,'navigation')]//span[text()='%s']" % name
        )
        category.click()

    @WebAction()
    def _click_download_all_on_media_modal(self):
        """Click Download All on download media window"""
        download_all_btn = self._driver.find_element(By.XPATH, 
            "//button[text()='Download All']")
        download_all_btn.click()

    @WebAction()
    def _click_download_media_by_platform(self, platform):
        """Click the Package hyperlink on download media window"""
        download_lnk = self._driver.find_element(By.XPATH, 
            "//div[@class='modal-body']//tr[./td[text()='%s']]//span" % platform
        )
        download_lnk.click()

    @WebAction()
    def _click_close_on_download_window(self):
        """Click close on download media window"""
        close_btn = self._driver.find_element(By.XPATH, 
            "(//button[text()='Close'])[1]")
        close_btn.click()

    @WebAction()
    def _click_recent_activity(self):
        """Click Recent activity hyperlink"""
        self._driver.execute_script(  # To prevent opening in new tab
                """document.querySelector("[href='activity.do']").removeAttribute("target")"""
        )
        link = self._driver.find_element(By.LINK_TEXT, "Recent Activity")
        link.click()

    @WebAction()
    def _is_recent_updates_displayed(self):
        """Check Recent Updates table"""
        title = self._driver.find_element(By.XPATH, "//span[@title= 'Recent Updates']|//span[text()='Recent Updates']")
        if title:
            return True
        else:
            return False

    @WebAction()
    def _click_sub_category(self, sub_category):
        """Click sub-category"""
        sub_category_btn = self._driver.find_element(By.XPATH, 
            "//li/a[contains(text(), '%s')]" % sub_category)
        sub_category_btn.click()

    @WebAction()
    def _click_clear_button_on_search_box(self):
        """Click clear on Search box"""
        close_btn = self._driver.find_element(By.XPATH, 
            "//span[@class='glyphicon glyphicon-remove']"
        )
        close_btn.click()

    @WebAction()
    def _click_home_link_on_readme_page(self):
        """Click Home hyperlink on ReadmePage"""
        home_btn = self._driver.find_element(By.XPATH, "//a[text()='home']")
        home_btn.click()

    @WebAction()
    def _click_enable_auto_update(self):
        """Click enable auto-update button"""
        slider = self._driver.find_element(By.XPATH, 
            "//span[@class='store-au-span sprite icon-switch-off']"
        )
        slider.click()

    @WebAction()
    def _click_disable_auto_update(self):
        """Click disable auto-update button"""
        slider = self._driver.find_element(By.XPATH, 
            "//span[@class='store-au-span sprite icon-switch-on']"
        )
        slider.click()

    @WebAction()
    def _click_quick_filter(self, quick_filter):
        """Click the filter below search bar"""
        filter_button = self._driver.find_element(By.XPATH, 
            f"//*[@*='quick-filters']//*[text()='{quick_filter}']"
        )
        filter_button.click()

    @WebAction()
    def _click_ok_on_premium_window_popup(self):
        """Click OK on Premium info popup"""
        ok_btn = self._driver.find_element(By.XPATH, "//button[.='OK']")
        ok_btn.click()

    @WebAction()
    def _get_name_of_first_package(self):
        """Get name of the first package"""
        pkg_name = self._driver.find_element(By.XPATH, 
            "//span[@class='pkg-name-span ng-binding']"
        )
        return pkg_name.text

    @WebAction(log=False)
    def _get_package_list(self):
        """Get the packages displayed"""
        elements = self._driver.find_elements(By.XPATH, 
            "//span[@class='pkg-name-span ng-binding']"
        )
        return [element.text for element in elements]

    @WebAction(delay=0)
    def _get_status_of_first_package(self):
        """Get status of first package"""
        status = self._driver.find_element(By.XPATH, 
            "//div[@class='actionBtn']/a"
        )
        return status.text

    @WebAction(delay=0)
    def _get_category_of_first_package(self):
        """Get category name of the first package displayed"""
        category = self._driver.find_element(By.XPATH, 
            "//li[@data-ng-repeat='item in row']//h3")
        return category.text.replace(r"view all >", "").strip()

    @WebAction()
    def _get_packages_with_premium_icon(self):
        """Get the premium icon on the packages"""
        packages = self._driver.find_elements(By.XPATH, 
            "//*[@id='premium-package-icon']/preceding::div[@title]")
        return [package.text.strip() for package in packages]

    @WebAction()
    def _get_premium_popup_text(self):
        """Read info text from premium pop"""
        body_txt = self._driver.find_element(By.XPATH, 
            "//*[./*/*[.='Access to Premium Packages']]/*[contains(@class, 'modal-body')]"
        )
        return body_txt.text

    @WebAction(delay=5)
    def _get_access_restricted_popup_text(self):
        """Read info text from access restricted pop"""
        body_txt = self._driver.find_element(By.XPATH, 
            "//*[./*/*[.='Access Restricted']]/*[contains(@class, 'modal-body')]"
        )
        return body_txt.text

    @WebAction(log=False)
    def _get_currently_selected_quick_filter(self):
        """Get the currently selected quick filter"""
        quick_filter = self._driver.find_element(By.XPATH, 
            "//li[./*[contains(@class, 'active-filter')]]"
        )
        return quick_filter.text

    @WebAction()
    def _get_all_package_statuses(self):
        """Get all the package statuses visible"""
        return [
            pkg.text.strip() for pkg in
            self._driver.find_elements(By.XPATH, "//*[@class='actionBtn']/a")
        ]

    @WebAction()
    def _read_available_filter_names(self):
        """Get the name of available filters"""
        filters = self._driver.find_elements(By.XPATH, 
            "//li//*[contains(@class, 'quick-filter')]"
        )
        return [filter_.text.strip() for filter_ in filters]

    @WebAction(log=False)
    def _is_currently_selected_subcategory(self, sub_category):
        """Get currently selected sub-category"""
        category = self._driver.find_elements(By.XPATH, 
            "//a[@class='subcategory ng-binding active']")
        if category:
            return category[0].text.strip().lower() == sub_category.lower()
        else:
            return False

    @WebAction(log=False)
    def _is_currently_selected_category(self, category):
        """Get the currently active category"""
        _category = self._driver.find_elements(By.XPATH, 
            "//a[@class='active-category active']")
        if _category:
            return _category[0].text.strip().lower() == category.lower()
        else:
            return False

    @WebAction(log=False)
    def _is_currently_searched_string(self, search_string):
        """Check if currently searched string is"""
        search_field = self._driver.find_elements(By.XPATH, 
            StoreApp._SEARCH_FIELD_XPATH)
        if search_field:
            return search_field[0].get_attribute(
                "value").lower() == search_string.lower()
        return False

    @WebAction(log=False)
    def _is_store_app(self):
        """Check if current page is Store page"""
        try:
            js = """
            function isStore() { 
               divObj = document.getElementsByClassName("vm-mydata-title");
               if (divObj.length > 0) {
                  return divObj[0].innerText == "Store";
                }
               return false;
            }
            return isStore();
            """
            return self._driver.execute_script(js)
        except WebDriverException:
            return False

    @WebAction(log=False)
    def _is_readme_page(self):
        """Check if current page is readme page"""
        try:
            js = """
            function isReadmePage() {
                obj = document.getElementById("readmeFrame");
                return obj != null;
            }
            return isReadmePage();
            """
            return self._driver.execute_script(js)
        except WebDriverException:
            return False

    @WebAction(log=False)
    def _is_store_spin_displayed(self):
        """Check if Store's spinner loading is visible"""
        js = """
            function isSpinnerVisible() {
                obj = document.getElementsByClassName("spinner");
                if (obj)
                    if (obj.length > 0)
                        return obj[0].parentElement.getAttribute("class") != "ng-scope ng-hide";
                return false;
            }
            return isSpinnerVisible();
        """
        return self._driver.execute_script(js)

    @WebAction()
    def _is_download_media_window_open(self):
        """Check if download media window is open"""
        try:
            modal = self._driver.find_element(By.XPATH, 
                "//h4[@class='modal-title' and text()='Downloads']"
            )
            time.sleep(3)
            return modal.is_displayed()
        except WebDriverException:
            return False

    @WebAction()
    def _set_search_field(self, search_string):
        """Type search string on search field"""
        search_box = self._driver.find_element(By.XPATH, 
            StoreApp._SEARCH_FIELD_XPATH
        )
        search_box.clear()
        search_box.send_keys(search_string)
        search_box.send_keys(Keys.ENTER)

    @WebAction(log=False)
    def _lookup_auto_update_slider(self):  # TODO: Remove this method to get rid of stacking
        """Check if auto-update is enabled"""
        self._driver.find_element(By.XPATH, 
            "//span[@class='store-au-span sprite icon-switch-off']")

    def _load_all_packages(self):
        """Scroll down till all the packages are visible"""
        num_package_old = len(self._get_package_list())
        num_package_new = 0
        count = 0
        while num_package_old != num_package_new and count < 10:
            count += 1
            self._driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            self.wait_till_load_complete()
            time.sleep(3)
            num_package_old = num_package_new
            num_package_new = len(self._get_package_list())
        if count == 10:
            raise CVWebAutomationException("Load all packages ended prematurely")

    def _lookup_package(
            self, package_name, category="Reports", sub_category=None,
            quick_filter=None, escape_package_name=False):
        """Find package matching given category

        Args:
            package_name (str): Name of the package to search with
            category (str): Category under which to look for the package
            sub_category (str): The subcategory to search under
            escape_package_name (bool): If the package name has special chars to escape

        Returns:
            True if the package exists as the first result, else False
        """
        self._filter_by(category, sub_category, quick_filter)
        if not self._is_currently_searched_string(package_name):
            if escape_package_name:
                new_package_name = "\"" + package_name + "\""
                self._set_search_field(new_package_name)
            else:
                self._set_search_field(package_name)
            self.wait_till_load_complete(timeout=120)
        pkg_name = self._get_name_of_first_package()
        if pkg_name.lower() != package_name.lower():
            raise CVWebAutomationException(
                f"Unable to find package=[{package_name}], category=[{category}], "
                f"subcategory=[{sub_category}]"
            )
        self.wait_till_load_complete()  # added to tolerate the load screen disappear issue

    @PageService(log=False)
    def _wait_till_store_spin_load(self, timeout):
        """Wait till store spin load"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._is_store_spin_displayed() is False:
                return
            else:
                time.sleep(2)
        raise CVTimeOutException(
            timeout,
            "Load time exceeded on store page",
            self._driver.current_url
        )

    def _install_package(self, name, category, sub_category=None,
                         expected_status="Up-to-date", refresh=False, escape_package_name=False):
        """Common function to install package"""
        self._lookup_package(name, category, sub_category, escape_package_name=escape_package_name)
        pkg_status = self._get_status_of_first_package()
        if pkg_status == "Install":
            self._click_install_on_first_package()
        else:
            raise CVWebAutomationException(
                "Unable to install package [%s], existing package "
                "has status [%s]" % (name, pkg_status)
            )
        self.wait_till_load_complete()
        time.sleep(5)  # The loading screen disappears for a while before reappearing
        self.wait_till_load_complete()
        if refresh:
            self._driver.refresh()
            self.wait_till_load_complete()
        pkg_status_post_install = self._get_status_of_first_package()
        if expected_status != pkg_status_post_install:
            raise CVWebAutomationException(
                "Expecting status [%s], found [%s] for [%s]" % (
                    expected_status,
                    pkg_status_post_install,
                    name
                )
            )

    def _download_package(self, name, category, username, password,
                          sub_category=None, validate_cloud_login=False,
                          escape_package_name=False):
        """Download package from store"""

        self._lookup_package(
            name, category, sub_category,
            escape_package_name=escape_package_name
        )

        pkg_status = self._get_status_of_first_package()
        if pkg_status != "Download":
            raise CVWebAutomationException(
                "Unable to download p__set_button_expressionackage [%s], existing package has "
                "[%s] status" % (name, pkg_status)
            )
        self._click_download_on_first_package()
        time.sleep(3)
        self.wait_till_load_complete()
        if self._webconsole.is_login_page():
            self._webconsole.login(username, password, auto_open_login_page=False)
            self._is_cloud_login_complete = True
            self.wait_till_load_complete()
        else:
            # Login page for webconsole did not appear
            if validate_cloud_login and not self._is_cloud_login_complete:
                raise CVWebAutomationException(
                    "Download did not ask for authentication"
                )
        received_notification = self._webconsole.get_all_unread_notifications(expected_count=1)[0]
        expected_notification = f"Downloading \"{name}\""
        if received_notification.lower() != expected_notification.lower():
            raise CVWebAutomationException(
                f"Unexpected notification [{str(received_notification)}] "
                f"received during upgrade"
            )

    def _filter_by(self, category=None, sub_category=None, quick_filter=None):
        if category:
            if not self._is_currently_selected_category(category):
                self._click_category("Home")
                self.wait_till_load_complete()
                self._click_category(category)
                self.wait_till_load_complete()
        if sub_category:
            if not self._is_currently_selected_subcategory(sub_category):
                self._click_sub_category(sub_category)
                self.wait_till_load_complete()
        if quick_filter:
            selected_filter = self._get_currently_selected_quick_filter()
            if selected_filter.lower() != quick_filter.lower():
                self._click_quick_filter(quick_filter)
                self.wait_till_load_complete()

    def _update_package(self, name, category, sub_category=None, expected_status="Open", escape_package_name=False):
        """Common function to update package"""
        self._lookup_package(name, category, sub_category, escape_package_name=escape_package_name)
        pkg_status = self._get_status_of_first_package()
        if pkg_status == "Update":
            self._click_update_on_first_package()
        else:
            raise CVWebAutomationException(
                "Unable to update package [%s], existing package "
                "has status [%s]" % (name, pkg_status)
            )
        self.wait_till_load_complete()
        time.sleep(3)  # The loading screen disappears for a while before reappearing
        self.wait_till_load_complete()
        pkg_status = self._get_status_of_first_package()
        if pkg_status != expected_status:
            raise CVWebAutomationException(
                "Package [%s]'s status did not change to [Open] after"
                "install, current status [%s]" % (name, pkg_status)
            )

    @WebAction()
    def _refresh_page(self):
        """Refresh page"""
        self._browser.driver.refresh()

    @WebAction()
    def _sub_category(self):
        """Returns the subcategory available under Category"""
        sub_category = self._driver.find_elements(By.XPATH, 
            "//ul[@class='subcategories']//a"
        )
        return [element.text for element in sub_category]

    @PageService()
    def clear_search_field(self):
        """Clear search field"""
        if self._is_currently_searched_string(""):
            return   # currently no search string set
        self._click_clear_button_on_search_box()
        self.wait_till_load_complete()

    @PageService()
    def search_packages(self, search_string, category="Reports", refresh=False):
        """Search package with given search string

        Args:
            search_string<str>: String to enter into the search field on store
            category<str>: Clicks on the package category
        """
        if refresh:
            self._driver.refresh()
            self.wait_till_load_complete()
        self._click_category(category)
        self.wait_till_load_complete()
        self._set_search_field(search_string)
        self.wait_till_load_complete()
        return self._get_package_list()

    @PageService()
    def search_by_name_on_store_homepage(self, package_name):
        """Check if package exists by given name on homepage

        Args:
            package_name (str): Name of the package
        """
        self._set_search_field(package_name)
        self.wait_till_load_complete()
        pkg_name = self._get_name_of_first_package().lower()
        if pkg_name == package_name.lower():
            return True, self._get_category_of_first_package()
        else:
            return False, ""

    @PageService()
    def search_package_by_name(
            self, package_name, category="Reports", sub_category=None):
        """Check if any package exists by given criteria"""
        try:
            self._lookup_package(package_name, category, sub_category)
            return True
        except CVWebAutomationException:
            return False

    @PageService()
    def get_package_status(
            self, package_name, category, sub_category=None,
            refresh=False, escape_package_name=False):
        """Get status of package from button

        Args:
            package_name (str): name of the package
            category (str): Any of Workflows/Alerts/Reports
            sub_category (str): Name of sub category
            refresh (bool): Refresh page to get status

        Returns:
            (str): Any of Install/Up-to-Date/Update
        """
        if refresh:
            self._refresh_page()
            self.wait_till_load_complete()
        self._lookup_package(package_name, category, sub_category, escape_package_name=escape_package_name)
        pkg_status = self._get_status_of_first_package()
        return pkg_status

    @PageService()
    def get_packages(self, category="Reports"):
        """Get visible packages under category
        Retrieves the names of the packages visible under the specified category
        Not to be confused with get_all_packages which scrolls till the EOP

        Args:
            category (str): Category name which has to be clicked
        Returns:
            list: All the packages under the category
        """
        self._click_category(category)
        return self._get_package_list()

    @PageService()
    def get_sub_category(self, category="Reports"):
        """Get subcategories under category
        Retrieves the subcategory name visible under specified category

        Args:
            category (str): Category name
        Returns:
            list: Subcategories under the category
        """
        self._click_category(category)
        return self._sub_category()

    @PageService()
    def get_all_packages(self, category=None, sub_category=None, quick_filter=None):
        """Get all package name by scrolling till end of page"""
        self._filter_by(category, sub_category, quick_filter)
        self._load_all_packages()
        return self._get_package_list()

    @PageService()
    def goto_store_home(self):
        """Goto Store HomePage"""
        if self._is_readme_page():
            self._click_home_link_on_readme_page()
        else:
            self._click_category("Home")

    @PageService()
    def goto_readme(
            self, package_name, category="Reports", sub_category=None):
        """Open readme page of the specified package

        Args:
            package_name (str): name of the package
            category (str): Category under which to look for the package
            sub_category (str): Sub-category name of the package
        Returns:
            True if package is accessed
        """
        package_name_upper = " ".join([
            (n.strip()[0].upper() + n[1:]) for n in
            package_name.split(" ")
            if len(n.strip()) > 0
        ])  # Convert "Backup job summary" to "Backup Job Summary"
        self._lookup_package(package_name_upper, category, sub_category)
        self._click_package(package_name_upper)
        self.wait_till_load_complete()

    @PageService()
    def get_all_available_filters(self):
        """Get all the visible filters on page"""
        return self._read_available_filter_names()

    @PageService()
    def get_premium_info_message(
            self, package_name, category=None, sub_category=None, quick_filter=None):
        """Get Premium message displayed on the Premium Popup window"""
        self._lookup_package(
            package_name, category, sub_category, quick_filter
        )
        self._click_purchase_button()
        time.sleep(2)  # wait till model is opened
        msg = self._get_premium_popup_text()
        self._click_ok_on_premium_window_popup()
        return msg

    @PageService()
    def get_access_restricted_info_message(self, name, category, sub_category=None, escape_package_name=False):
        """Download of package from store for which access is restricted
        Returns: Access Restricted message displayed on the Popup window"""
        self._lookup_package(
            name, category, sub_category,
            escape_package_name=escape_package_name
        )
        self._wait_till_store_spin_load(10)
        self._click_download_on_first_package()
        msg = self._get_access_restricted_popup_text()
        time.sleep(2)
        self._click_ok_on_premium_window_popup()
        return msg

    @PageService(hide_args=True)
    def download_workflow(self, name,
                          username=_STORE_CONFIG.PREMIUM_USERNAME,
                          password=_STORE_CONFIG.PREMIUM_PASSWORD,
                          validate_cloud_login=False,
                          escape_package_name=False):
        """Download WorkFlow

        Args:
            name (str): name of the WF to download
            username (str): username for store login
            password (str): password for store login
            validate_cloud_login (bool): If set to true, will validate if the download
                is redirected to Store server's WebConsole login page
        """
        self._download_package(
            name, category="Workflows", username=username, password=password,
            validate_cloud_login=validate_cloud_login, escape_package_name=escape_package_name)

    @PageService(hide_args=True)
    def download_alert(self, name,
                       username=_STORE_CONFIG.PREMIUM_USERNAME,
                       password=_STORE_CONFIG.PREMIUM_PASSWORD,
                       validate_cloud_login=False):
        """Downloads the alert if it has 'Download' status

        Args:
            name (str): name of the alert to download
            username (str): username for store login
            password (str): password for store login
            validate_cloud_login (bool): If set to true, will validate if the download
                is redirected to Store server's WebConsole login page
        """
        self._download_package(
            name, category="Alerts", username=username, password=password,
            validate_cloud_login=validate_cloud_login)

    @PageService()
    def download_packages_with_multiple_platforms(
            self, name, category, platforms=None):
        """Download packages which have multiple download types

        Args:
            name (str): name of the package
            category (str): category under the package
            platforms (list): Leave it None to download all platforms, to download
                a specific list of platform, pass the platform as list
        """
        self._lookup_package(name, category)
        self._click_download_on_first_package()
        if self._is_download_media_window_open() is False:
            raise CVWebAutomationException(
                "Unable to open media download window modal")
        if platforms is not None:
            for platform in platforms:
                self._click_download_media_by_platform(platform)
                time.sleep(5)
        else:
            self._click_download_all_on_media_modal()
            time.sleep(5)
        self._click_close_on_download_window()

    @PageService(hide_args=True)
    def download_package(self,
                         name,
                         category,
                         username=_STORE_CONFIG.PREMIUM_USERNAME,
                         password=_STORE_CONFIG.PREMIUM_PASSWORD,
                         sub_category=None,
                         validate_cloud_login=False,
                         escape_package_name=False):
        """Download package"""
        self._download_package(
            name,
            category=category,
            sub_category=sub_category,
            username=username,
            password=password,
            validate_cloud_login=validate_cloud_login,
            escape_package_name=escape_package_name
        )

    @PageService(hide_args=True)
    def download_report(self,
                        name,
                        username=_STORE_CONFIG.PREMIUM_USERNAME,
                        password=_STORE_CONFIG.PREMIUM_PASSWORD,
                        validate_cloud_login=False):
        """Download the report

        Args:
            name (str): Report package name
            username (str): username for login
            password (str): password for login
            validate_cloud_login (bool): If set to true, will validate if the download
                is redirected to Store server's WebConsole login page
        """
        self._download_package(
            name,
            category="Reports",
            username=username,
            password=password,
            validate_cloud_login=validate_cloud_login
        )

    @PageService()
    def disable_auto_update(self):
        """Disable the auto-update if its enabled"""
        if self.is_auto_update_enabled() is True:
            self._click_disable_auto_update()

    @PageService()
    def install_quick_access_tool(self, tool_name, refresh=False):
        """Install quick access tool"""
        self._install_package(
            tool_name, category="Tools", sub_category="Quick Access",
            refresh=refresh
        )
        self._webconsole.get_all_unread_notifications(
            expected_count=2,
            expected_notifications=[
                "Tool installed successfully.",
                "Installing \"%s\"" % tool_name
            ]
        )

    @PageService()
    def install_report(self, report_name, refresh=False):
        """Install the report

        Args:
            report_name (str): Name of the report to install
            refresh (bool): Refresh page before checking for package
                status
        """
        self._install_package(
            report_name, category="Reports", expected_status="Open",
            refresh=refresh
        )
        received_notifications = [
            notification.lower() for notification in
            self._webconsole.get_all_unread_notifications(expected_count=2)
        ]
        expected_notifications=[
            ('Report ' + report_name + ' installed successfully.').lower(),
            ('Installing "' + report_name + '"').lower()
        ]
        if received_notifications != expected_notifications:
            raise CVWebAutomationException(
                f"Unexpected notification [{received_notifications}] received"
            )

    @PageService()
    def install_workflow(self, wf_name, refresh=False, escape_package_name=False):
        """Install the workflow from the store

        Args:
            wf_name (str): name of the workflow
            refresh (bool): Refresh page before checking for package
                status
        """
        self._install_package(
            wf_name, category="Workflows", expected_status="Open",
            refresh=refresh, escape_package_name=escape_package_name
        )
        self._webconsole.get_all_unread_notifications(
            expected_count=2,
            expected_notifications=[
                "Workflow installed successfully.",
                'Installing "' + wf_name + '"'
            ]
        )

    @PageService()
    def install_alert(self, alert_name):
        """Install the alert from the store

        Args:
            alert_name (str): name of the alert
        """
        self._install_package(
            alert_name, category="Alerts", expected_status="Up-to-date")
        self._webconsole.get_all_unread_notifications(
            expected_count=2,
            expected_notifications=[
                'Alert installed successfully.',
                'Installing "' + alert_name + '"'
            ]
        )

    @PageService()
    def install_app(self, app_name):
        """Installing app"""
        self._install_package(
            app_name, category="Apps", expected_status="Open"
        )
        self._webconsole.get_all_unread_notifications(
            expected_count=2,
            expected_notifications=[
                "App installed successfully.",
                f'Installing "{app_name}"'
            ]
        )

    @PageService()
    def is_auto_update_enabled(self):
        """Check if auto-update is enabled"""
        try:
            self._lookup_auto_update_slider()
            return False
        except NoSuchElementException:
            return True

    @PageService()
    def access_recent_activity_link(self):
        """Click recent activity link"""
        self._click_recent_activity()
        self.wait_till_load_complete()
        return self._is_recent_updates_displayed()

    @PageService()
    def is_recent_updates_table_displayed(self):
        """Check Recent Updates table is shown"""
        return self._is_recent_updates_displayed()

    @PageService()
    def validate_if_package_is_premium(self, package_name):
        """Check if package has premium status"""
        self._lookup_package(package_name)
        pkg_status = self._get_status_of_first_package()
        if pkg_status != "Purchase":
            raise CVWebAutomationException(
                "[%s] Does not have Purchase status, it has [%s] status" % (
                    package_name, pkg_status
                )
            )
        if package_name not in self._get_packages_with_premium_icon():
            raise CVWebAutomationException(
                "[%s] Does not have Premium icon" % package_name)

    @PageService()
    def update_quick_access_tool(self, tool_name):
        """Update the quick access tool"""
        self._update_package(
            tool_name, category="Tools", sub_category="Quick Access Tools")
        msgs = self._webconsole.get_all_unread_notifications(expected_count=2)
        err_msg = "Unexpected notification [%s] while installing tool [%s]"
        if msgs[0] != "Tool installed successfully.":
            raise CVWebAutomationException(err_msg % (msgs[0], tool_name))
        if msgs[1] != "Installing \"%s\"" % tool_name:
            raise CVWebAutomationException(err_msg % (msgs[1], tool_name))

    @PageService()
    def update_workflow(self, wf_name, escape_package_name=False):
        """Install the workflow from the store

        Args:
            wf_name (str): name of the workflow
        """
        self._update_package(wf_name, category="Workflows", escape_package_name=escape_package_name)
        msgs = self._webconsole.get_all_unread_notifications(expected_count=2)
        if msgs[1] != 'Installing "' + wf_name + '"':
            raise CVWebAutomationException(
                "Install workflow on [%s] returned [%s]" % (wf_name, msgs[1]))
        if msgs[0] != 'Workflow installed successfully.':
            raise CVWebAutomationException(
                "Received incorrect notification [%s] for [%s]" % (msgs[0], wf_name))

    @PageService()
    def update_report(self, report_name):
        """Update the report

        Args:
            report_name (str): Name of the report to install
        """
        self._update_package(report_name, category="Reports")
        msgs = self._webconsole.get_all_unread_notifications(expected_count=2)
        if msgs[1].lower() != ('Installing "' + report_name + '"').lower():
            raise CVWebAutomationException(
                "Installing report returned [%s] for report [%s]" % (
                    msgs[1], report_name
                )
            )
        expected_msg = ('Report ' + report_name + ' installed successfully.').lower()
        if msgs[0].lower() != expected_msg:
            raise CVWebAutomationException(
                "Report Import returned [%s] for report [%s]" % (
                    msgs[0], report_name
                )
            )

    @PageService()
    def update_alert(self, alert_name):
        """Install the alert from the store

        Args:
            alert_name (str): name of the alert
        """
        self._update_package(alert_name, category="Alerts", expected_status="Up-to-date")
        msgs = self._webconsole.get_all_unread_notifications(expected_count=2)
        if msgs[1] != 'Installing "' + alert_name + '"':
            raise CVWebAutomationException(
                "Install alert on [%s] returned [%s]" % (
                    alert_name, msgs[1]
                )
            )
        if msgs[0] != "Alert installed successfully.":
            raise CVWebAutomationException(
                "Received incorrect notification [%s] for [%s]" % (
                    msgs[0], alert_name
                )
            )

    @PageService()
    def enable_auto_update(self):
        """Clicks on auto-update slider if its disabled"""
        if self.is_auto_update_enabled() is False:
            self._click_enable_auto_update()

    @PageService(log=False)
    def wait_till_load_complete(self, timeout=120):
        """Wait till the loading is complete on Store page"""
        if self._is_store_app():
            self._wait_till_store_spin_load(timeout)
        self._webconsole.wait_till_load_complete()  # interleaved purposefully
        if self._is_store_app():
            self._wait_till_store_spin_load(timeout)

    @PageService()
    def filter_by(self, category=None, sub_category=None, quick_filter=None):
        """Filter the packages"""
        self._filter_by(category, sub_category, quick_filter)

    @PageService()
    def open_package(self, package_name, category="Reports", sub_category=None, quick_filter=None):
        """Opening package"""
        self._lookup_package(
            package_name, category=category, sub_category=sub_category,
            quick_filter=quick_filter
        )
        if self._get_status_of_first_package() != "Open":
            raise CVWebAutomationException(
                f"[{package_name}] does not have Open status"
            )
        self._click_open_button()
        self.wait_till_load_complete()

    @PageService()
    def get_all_package_statuses(self):
        """Get the status of all the available packages"""
        return self._get_all_package_statuses()


class ReadMe:

    """Contains the methods needed to interact with the Read me page."""

    def __init__(self, webconsole):
        """
        Args:
             webconsole (WebConsole): WebConsole object
        """
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self._store = StoreApp(webconsole)

    @WebAction(log=False)
    def _switch_to_readme_frame(self):
        """Change context to readme frame"""
        readme_frame = self._driver.find_element(By.CLASS_NAME, "readmeFrame")
        self._driver.switch_to.frame(readme_frame)

    @WebAction(log=False)
    def _switch_to_default_frame(self):
        """Switch to default readme page frame"""
        self._driver.switch_to.default_content()

    @WebAction()
    def _click_home(self):
        """Click home hyperlink"""
        link = self._driver.find_element(By.XPATH, "//a[@href and .='home']")
        link.click()

    @WebAction()
    def _click_release_details(self, release):
        """Click details link"""
        details = self._driver.find_element(By.XPATH, 
            "//*[@class='all-downloads']//tr/"
            f"td[.='{release}']/following-sibling::td/a"
        )
        details.click()

    @WebAction()
    def _click_download(self):
        """Click Download link"""
        download = self._driver.find_element(By.XPATH, "//button[.='Download']")
        download.click()

    @WebAction()
    def _get_readme_title(self):
        """Get package title from readme page"""
        page_title = self._driver.find_element(By.XPATH, 
            "//h1[@class='pkg-main-title ng-binding']"
        )
        return page_title.text

    @WebAction()
    def _get_readme_description(self):
        """Get package description from Readme page"""
        page_desc = self._driver.find_element(By.XPATH, 
            "//p[@class='pkg-main-desc ng-binding']"
        )
        return page_desc.text

    @WebAction()
    def _get_html_readme_row_count(self):
        """Get the number of rows"""
        rows = self._driver.find_elements(By.XPATH, 
            "//table//tr[@data-ng-repeat='data in $data']"
        )
        return len(rows)

    @WebAction()
    def _get_html_readme_title(self):
        """Read title from readme"""
        title_obj = self._driver.find_element(By.ID, "sectionTitle")
        return title_obj.text

    @WebAction()
    def _get_html_readme_description(self):
        """Read html readme's description"""
        desc_obj = self._driver.find_element(By.ID, "crdescription")
        return desc_obj.text

    @WebAction()
    def _get_html_readme_content_as_text(self):
        """Return text content inside HTML Readme

        *IMPORTANT* - Use this method after switching to readme frame
        """
        readme_obj = self._driver.find_element(By.XPATH, "//body")
        return readme_obj.text

    @WebAction()
    def _get_all_release_strings(self):
        """Get all the Released In strings"""
        return [
            element.text.strip()
            for element in self._driver.find_elements(By.XPATH, 
                "//*[@class='all-downloads']//tr/td[2]"
            )
        ]

    @WebAction()
    def _get_package_info(self, name):
        """Get package info"""
        info = self._driver.find_element(By.XPATH, 
            "//*[@class='pkg-info' and "
            f"contains(., '{name}')]/following-sibling::*"
        )
        return info.text

    @PageService()
    def download_package(self):
        """Download package"""
        self._click_download()
        self._store.wait_till_load_complete()

    @PageService()
    def get_readme_title(self):
        """Get readme page's title"""
        self._store.wait_till_load_complete()
        return self._get_readme_title()

    @PageService()
    def get_readme_description(self):
        """Get page description"""
        self._store.wait_till_load_complete()
        return self._get_readme_description()

    @PageService()
    def get_html_readme_title(self):
        """Get description from html export preview"""
        try:
            self._store.wait_till_load_complete()
            self._switch_to_readme_frame()
            return self._get_html_readme_title()
        finally:
            self._switch_to_default_frame()

    @PageService()
    def get_html_readme_description(self):
        """Get html readme description"""
        try:
            self._store.wait_till_load_complete()
            self._switch_to_readme_frame()
            return self._get_html_readme_description()
        finally:
            self._switch_to_default_frame()

    @PageService()
    def get_html_readme_row_count(self):
        """Get the number of rows in readme table"""
        try:
            self._store.wait_till_load_complete()
            self._switch_to_readme_frame()
            return self._get_html_readme_row_count()
        finally:
            self._switch_to_default_frame()

    @PageService()
    def get_html_readme_text_content(self):
        """Get the HTML readme's content as text"""
        try:
            self._store.wait_till_load_complete()
            self._switch_to_readme_frame()
            return self._get_html_readme_content_as_text()
        finally:
            self._switch_to_default_frame()

    @PageService()
    def get_sample_screenshot_message(self):
        """Check if SAMPLE SCREENSHOT title exists"""
        web_element = self._driver.find_elements(By.XPATH, 
            "//h2[contains(., 'Sample Screenshot')]"
        )
        if not web_element:
            raise CVWebAutomationException(
                "SAMPLE SCREENSHOT message not shown on readme page"
            )
        return web_element[0].text.strip()

    @PageService()
    def get_hyperlink_link_text(self):
        """Check if hyper link exists on readme"""
        try:
            self._switch_to_readme_frame()
            hyperlinks = self._driver.find_elements(By.XPATH, "//a[@href]")
            return [hyperlink.text for hyperlink in hyperlinks]
        finally:
            self._switch_to_default_frame()

    @PageService()
    def get_package_info(self):
        """Get package info shown"""
        return {
            "Category": self._get_package_info("Category"),
            "ReleasedIn": self._get_package_info("Released In")
        }

    @PageService()
    def get_all_release_versions(self):
        """Get all the release versions"""
        return self._get_all_release_strings()

    @PageService()
    def goto_release(self, release):
        """Open release by clicking Details link"""
        self._click_release_details(release)
        self._store.wait_till_load_complete()

    @PageService()
    def visit_hyperlink(self, link_name):
        """Open hyperlink in readme"""
        try:
            self._switch_to_readme_frame()
            link = self._driver.find_element(By.LINK_TEXT, link_name)
            link.click()
            if len(self._driver.window_handles) != 2:
                raise CVWebAutomationException(
                    "New tab did not open after clicking hyperlink"
                )
        finally:
            self._switch_to_default_frame()

    @PageService()
    def goto_store_home(self):
        """Open store from readme page"""
        self._click_home()
        self._webconsole.wait_till_load_complete()


class StoreLogin:

    """This class handles the operations related to store login"""

    _STORE_FRAME_ID = "loginframe"

    def __init__(self, webconsole):
        """
        Args:
            webconsole<WebConsole>: WebConsole object
        """
        self._webconsole = webconsole
        self._driver = self._webconsole.browser.driver
        self._store = StoreApp(webconsole)
        self._browser = webconsole.browser
        self._LOG = logger.get_log()

    def _is_store_login_popup_open(self):
        """Check if store login popup is open"""
        return (
            self._is_store_frame_switchable() or
            self._is_store_frame_already_focused()
        )

    @WebAction(log=False)
    def _is_store_frame_already_focused(self):
        """Check if already inside loginFrame"""
        try:
            frame = self._driver.find_element(By.TAG_NAME, "iframe")
            frame.find_element(By.XPATH, "//*[text()='Log on to Store']")
            return frame.is_displayed()
        except WebDriverException:
            return False

    def _is_store_frame_switchable(self):
        """Check if current frame can be switched to loginFrame"""
        try:
            self._switch_into_login_popup_frame()
            return True
        except WebDriverException:
            return False
        finally:
            self._switch_to_default_frame()

    @WebAction(log=False)
    def _switch_into_login_popup_frame(self):
        """Change frame to loginFrame"""
        self._driver.switch_to.frame(StoreLogin._STORE_FRAME_ID)

    @WebAction(log=False)
    def _switch_to_default_frame(self):
        """Exit loginFrame and enter default frame"""
        self._driver.switch_to.default_content()

    @WebAction(delay=1)
    def _set_username(self, username):
        """Set username on login popup"""
        text_box = self._driver.find_element(By.ID, "username")
        text_box.send_keys(username)

    @WebAction(hide_args=True, delay=1)
    def _set_password(self, password):
        """Set password on login popup"""
        pwd_box = self._driver.find_element(By.ID, "password")
        pwd_box.send_keys(password)

    @WebAction()
    def _read_store_login_popup_feedback(self):
        """Read error if login Store login fails"""
        feedback = self._driver.find_element(By.ID, "errorText")
        return feedback.text

    @WebAction(delay=1)
    def _click_login(self):
        """Click login on store login popup"""
        btn = self._driver.find_element(By.ID, "loginbtn")
        btn.click()

    @PageService(log=False)
    def wait_till_login_complete(self, timeout=60):
        """Wait till login is complete"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._is_store_login_popup_open() is False:
                return
            else:
                time.sleep(1)
        raise CVTimeOutException(
            timeout,
            "Login to store using Store Login Popup",
            self._driver.current_url
        )

    @PageService(hide_args=True)
    def login(self, username, password):
        """Login using store login popup"""
        try:
            if self._is_store_login_popup_open():
                self._switch_into_login_popup_frame()
                self._store.wait_till_load_complete()
                self._set_username(username)
                self._set_password(password)
                self._click_login()
                self._switch_to_default_frame()
                time.sleep(2)
                self.wait_till_login_complete()
                self._store.wait_till_load_complete()
                time.sleep(2)  # Sometimes the loading screen exits sooner
                self._store.wait_till_load_complete()
                if self._is_store_login_popup_open():
                    self._switch_into_login_popup_frame()
                    failure_msg = self._read_store_login_popup_feedback()
                    raise CVWebAutomationException(
                        f"Store login failed with [{failure_msg}]"
                    )
        finally:
            self._switch_to_default_frame()
