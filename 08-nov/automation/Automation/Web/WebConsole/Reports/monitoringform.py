from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Operations related to monitoring page.


ManageCommcells:

    __init__()                          --  initialize instance of the ManageCommcells class,
                                             and the class attributes.

    filter_by_commcell_name()           --  filter monitoring page by commcell name.

    filter_by_commcell_version()        --  filter monitoring page by commcell version.

    get_commcell_action_options()       --  Get commcell action options available for any commcell.


"""
from time import sleep

from selenium.webdriver.common.action_chains import ActionChains

from AutomationUtils import logger
from Web.Common.page_object import WebAction, PageService
from Web.WebConsole.Reports.Metrics.components import MetricsTable
from Web.WebConsole.Reports.cte import Security
from Web.WebConsole.webconsole import WebConsole


class ManageCommcells:
    """Manage commcells is the class to do operations on commcell monitoring page"""
    class CommcellActions:
        """Different options which are available for commcell"""
        WEBCONSOLE = "Web Console"
        ADMIN_CONSOLE = "Command Center"
        CONSOLE = "Console"
        SECURITY = "Security"
        DELETE = "Delete"

    def __init__(self, web_console: WebConsole):
        self._driver = web_console.browser.driver
        self._web_console = web_console
        self._commcells_table = MetricsTable(self._web_console, table_name=None)
        self._log = logger.get_log()

    @WebAction()
    def _is_commcell_name_filtered(self, commcell_name):
        """
        Verify commcell monitoring page is already filtered by commcell name using url
        Args:
            commcell_name        (String)     --         name of the commcell

        Returns(Boolean) : True if page is filtered with commcell name else return false
        """
        _str = "Name-LIKE-%s" % commcell_name
        return _str in self._driver.current_url

    @WebAction()
    def _clear_commcell_name(self):
        """
        Clear the CommCell name text from the monitroing page.
        """
        self._driver.find_element(By.XPATH, "//*[@id='ccTableWrapper_filterText-2']").clear()

    @WebAction()
    def _mouse_hover_commcell(self, commcell_name):
        """Mouse over commcell name"""
        commcell = self._driver.find_element(By.XPATH, "//a[text()='" + commcell_name + "']")
        hover = ActionChains(self._driver).move_to_element(commcell)
        hover.perform()
        sleep(2)

    @WebAction()
    def _get_commcell_action_options(self):
        """Returns available actions present on commcell"""
        options = []
        options_obj = self._driver.find_elements(By.XPATH, "//li[contains(@class, "
                                                          "'commcell-action')]/a")
        for each_option in options_obj:
            if each_option.is_displayed():
                options.append(each_option.text)
            else:
                continue
        return options

    def get_commcell_action_options(self, commcell_name):
        """
        returns list of action string present on commcell in monitoring page.
        """
        self.filter_by_commcell_name(commcell_name)
        self._mouse_hover_commcell(commcell_name)
        self._click_view_options()
        return self._get_commcell_action_options()

    @WebAction()
    def _click_action_option(self, option):
        """Click on specified option"""
        sleep(2)
        self._driver.find_element(By.XPATH, "//li//a[text() = '"
                                           + option + "']").click()

    @WebAction()
    def _click_view_options(self):
        """click view to see different options available for commcell"""
        open_button = self._driver.find_element(By.XPATH, "//div[@class='openButton']")
        self._driver.execute_script('arguments[0].click();', open_button)

    @WebAction()
    def _click_edit_commcell(self):
        """click edit commcell option """
        self._driver.find_element(By.XPATH, "//*[@title='Edit CommCell Name']").click()

    @WebAction()
    def _click_new_cc_name(self, new_commcell):
        """
        click one new commcell text box
        Args:
            new_commcell:     (String)   --            name of the new commcell
        """
        xpath = "//input[@class='new-cc-name']"
        edit_cc = self._driver.find_element(By.XPATH, xpath)
        edit_cc.clear()
        edit_cc.send_keys(new_commcell)

    @WebAction()
    def _click_commcell(self, commcell):
        """
        clicks on the new commcell name
        """
        self._driver.find_element(By.XPATH, "//a[text()='%s']" % commcell).click()

    
    @PageService()
    def access_commcell(self, commcell):
        """
        fileters and clicks on the given commcell
        Args:
            commcell: (String) --    name of the commcell
        """
        self.filter_by_commcell_name(commcell)
        self._click_commcell(commcell)
        self._web_console.wait_till_load_complete()


    @WebAction()
    def _save_commcell_name(self):
        """
        save the new commcell name
        """
        self._driver.find_element(By.XPATH, "//span[@title='Save CommCell Name']").click()


    @WebAction()
    def _confirm_deletion(self):
        """Confirm delete"""
        self._driver.find_element(By.CLASS_NAME, 'confirm').send_keys('Confirm')
        self._driver.find_element(By.XPATH, "//a[@class = 'deleteButton']").click()

    @WebAction()
    def _get_commcell_disabled_icon(self):
        """Get commcell is disabled icon"""
        return self._driver.find_elements(By.XPATH, "//*[@class = 'disabledIcon']//..")

    @WebAction()
    def _look_up_for_commcell(self, commcell_name):
        """Get commcell object present in commcell monitoring page"""
        return self._driver.find_elements(By.XPATH, "//a[text()='" + commcell_name + "']")

    @PageService()
    def filter_by_commcell_name(self, commcell_name):
        """
        Filter by specified commcell name on column 'Commcell Name'
        Args:
            commcell_name          (String)     --        name of the commcell
        """
        if not self._is_commcell_name_filtered(commcell_name):
            self._commcells_table.set_filter('CommCell Name', value=commcell_name)
        self._web_console.wait_till_load_complete()

    @PageService()
    def filter_by_commcell_version(self, version):
        """
        Filter by commcell version on column 'Version'
        Args:
            version               (String)     --        commcell version
        """
        self._commcells_table.set_filter('Version', version)
        self._web_console.wait_till_load_complete()

    @PageService()
    def access_commcell_web_console(self, commcell_name):
        """
        click on webconsole option of commcell, present in monitoring page

        Args:
            commcell_name       (String)   --            name of the commcell
        """
        self.filter_by_commcell_name(commcell_name)
        self._mouse_hover_commcell(commcell_name)
        self._click_view_options()
        self._click_action_option(self.CommcellActions.WEBCONSOLE)

    @PageService()
    def access_commcell_admin_console(self, commcell_name):
        """
        click on admin console option of commcell, present in monitoring page

        Args:
            commcell_name       (String)   --            name of the commcell
        """
        self.filter_by_commcell_name(commcell_name)
        self._mouse_hover_commcell(commcell_name)
        self._click_view_options()
        self._click_action_option(self.CommcellActions.ADMIN_CONSOLE)

    @PageService()
    def access_commcell_console(self, commcell_name):
        """
        click on commcell console option of commcell, present in monitoring page

        Args:
            commcell_name       (String)   --            name of the commcell
        """
        self.filter_by_commcell_name(commcell_name)
        self._mouse_hover_commcell(commcell_name)
        self._click_view_options()
        self._click_action_option(self.CommcellActions.CONSOLE)

    @PageService()
    def access_commcell_security(self, commcell_name):
        """
        click on commcell security option of commcell, present in monitoring page

        Args:
            commcell_name       (String)   --            name of the commcell

        """
        self.filter_by_commcell_name(commcell_name)
        self._mouse_hover_commcell(commcell_name)
        self._click_view_options()
        self._click_action_option(self.CommcellActions.SECURITY)
        self._web_console.wait_till_load_complete()
        return Security(self._web_console)

    @PageService()
    def delete_commcell(self, commcell_name):
        """
        Delete specified commcell

        Args:
            commcell_name:     (String)   --           name of the commcell
        """
        self.filter_by_commcell_name(commcell_name)
        self._mouse_hover_commcell(commcell_name)
        self._click_view_options()
        self._click_action_option(self.CommcellActions.DELETE)
        self._confirm_deletion()
        self._web_console.wait_till_load_complete()

    @PageService()
    def rename_commcell(self, commcell_name, new_commcell):
        """
        Rename specified commcell

        Args:
            commcell_name:     (String)   --           name of the commcell

        """
        self._mouse_hover_commcell(commcell_name)
        self._click_edit_commcell()
        self._click_new_cc_name(new_commcell)
        self._save_commcell_name()
        self._web_console.wait_till_load_complete()
        self._clear_commcell_name()

    @PageService()
    def get_column_values(self, column_name):
        """Get list of the row values"""
        return self._commcells_table.get_data_from_column(column_name)

    @PageService()
    def is_commcell_disabled(self, commcell_name):
        """check if commcell is disabled"""
        self.filter_by_commcell_name(commcell_name=commcell_name)
        icon_object = self._get_commcell_disabled_icon()
        if icon_object:
            return icon_object[0].text == commcell_name
        return False

    @PageService()
    def is_commcell_exists(self, commcell_name):
        """Check if commcell exists in monitoring page"""
        self.filter_by_commcell_name(commcell_name=commcell_name)
        if self._look_up_for_commcell(commcell_name):
            return True
        return False

