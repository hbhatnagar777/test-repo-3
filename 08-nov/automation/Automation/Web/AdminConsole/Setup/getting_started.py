from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to getting started page

==============

    expand_solutions()  -- Expands all the solutions listed

    get_solutions_listed()  -- Returns the solutions listed

    get_setup_completion_state() -- fetches the setup completion state

    finish_setup_later()--Clicks the finish this later option in getting started or solution page

    click_get_started()--clicks the link, get started or lets finish it

    access_tab()                -- access tabs under guided setup

    access_panel()              -- Method to click on the given panel with the title

    navigate_to_services()      -- navigate to services tab under guided setup

    navigate_to_metallic()      -- navigate to metallic tile under services

    get_metallic_link_status    -- returns if its already linked to metallic

    link_metallic_account()     -- register to metallic services

    unlink_metallic_account()   -- unregister to metallic services

    mark_solution_complete()    -- Marks the given solution as complete

    configure_wizard_for_solution()       -- Configure guided setup wizard for solution

    go_to_app_for_solution()    -- Go to application for solution if setup is complete

"""


from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Setup.core_setup import Setup
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.AdminConsole.Components.panel import PanelInfo


class GettingStarted:
    """
    Class for file servers getting started page in Admin console

    """

    def __init__(self, admin_console: AdminConsole):
        """
        Setup Class initialization

        """
        self.admin_console = admin_console
        self.setup_obj = Setup(admin_console)
        self.driver = admin_console.driver
        self.log = admin_console.log
        self.admin_console.load_properties(self)
        self.__modal_dialog = ModalDialog(self.admin_console)
        self.__panelinfo = PanelInfo(self.admin_console)

    @WebAction()
    def __access_configure(self):
        """ Clicks on configure menuitem """
        self.admin_console.click_by_xpath(
            f'//div[@class="btn-group ng-scope dropdown open"]//li[@role="menuitem"]//span[contains(text(),' +
            f'"{self.admin_console.props["label.configure"]}")]'
        )

    @WebAction()
    def __access_go_to_app(self):
        """ Clicks on Go to app menuitem """
        self.admin_console.click_by_xpath(
            f'//div[@class="btn-group ng-scope dropdown open"]//li[@role="menuitem"]//span[contains(text(),' +
            f'"{self.admin_console.props["label.app"]}")]'
        )

    @WebAction()
    def __skip_core_setup(self):
        """ Clicks on skip option of getting started page"""
        xpath = "//div[@class='core-setup-block setup-banner']//a[@data-ng-click='skipInitialSetup()']"
        if self.admin_console.check_if_entity_exists(By.XPATH, xpath):
            self.driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def expand_solutions(self):
        """Expand all available solutions within the tab"""
        if self.__panelinfo.check_if_hyperlink_exists_on_tile(
            self.admin_console.props['label.moreSolutions']):
            self.__panelinfo.open_hyperlink_on_tile(
                self.admin_console.props['label.moreSolutions'])

    @WebAction()
    def get_solutions_listed(self):
        """
            To get the solutions getting listed in getting started page
            Returns: Dictionary of solutions with "marked as completed" status
                Example:
                    {'File server': True, 'Databases': False}
        """
        solutions = {}
        self.expand_solutions()
        xpath = "//div[contains(@class, 'app-tiles')]/div/div"
        for i, _ in enumerate(self.admin_console.driver.find_elements(By.XPATH, xpath), 1):
            xpath_updated = f"{xpath}[{i}]//h3"
            solution_name = self.admin_console.driver.find_element(By.XPATH, xpath_updated).text
            solution_status = self.admin_console.check_if_entity_exists(
                "xpath", f"{xpath_updated}/../..//*[contains(@class, 'ion-android-done')]")
            solutions[solution_name] = solution_status
        return solutions

    @PageService()
    def get_setup_completion_state(self, solution):
        """
            fetches the setup completion state
            Args:
                solution(string):name of the solution
            Returns:True,when setup is completed
            Raise:
                CVWebAutomationException : if solution is not listed

        """
        panel_xpath = f"//div[contains(@class, 'guidedSetupTileClickableTile')]//p[contains(text(), '{solution}')]" \
                      "/ancestor::div[position()=2]"
        tick_xpath = '//span[contains(@class, "float-right")]'
        if self.admin_console.check_if_entity_exists('xpath', panel_xpath):
            if self.admin_console.check_if_entity_exists('xpath', panel_xpath + tick_xpath):
                return True
            else:
                return False
        else:
            raise CVWebAutomationException("Solution is not listed.")

    @PageService()
    def configure_wizard_for_solution(self, solution, new_guided_setup=False):
        """
            Clicks on configure for solution in getting started page
            Args:
                solution    (string)    :   name of the solution
                new_guided_setup    (bool)  :   whether to use react UI changes or not
        """
        if new_guided_setup:
            xpath = (f"//div[contains(@class, 'MuiCardHeader-root')]//*[contains(text(), '{solution}')]"
                     f"/ancestor::div[contains(@class, 'MuiCard-root')]//button[contains(@aria-label, 'Configure')]")
            self.admin_console.click_by_xpath(xpath)
        else:
            if self.get_setup_completion_state(solution):
                self.access_panel(solution)
                self.__access_configure()
            else:
                self.access_panel(solution)

    @PageService()
    def got_to_app_for_solution(self, solution):
        """
            Clicks the go to app for solution in getting started page
            Args:
                solution    (string)    :   name of the solution
            Raise:
                CVWebAutomationException    :   if setup is not completed for solution
        """

        if self.get_setup_completion_state(solution):
            self.access_panel(solution)
            self.__access_go_to_app()
        else:
            raise CVWebAutomationException('Setup not completed for solution.')

    @WebAction()
    def finish_setup_later(self):
        """
        Clicks the finish this later option in getting started or solution page
        Returns: None

        """
        # Load all props
        getattr(self.admin_console, 'navigator')
        try:
            self.admin_console.select_hyperlink(self.admin_console.props['label.finishLater'])
        except Exception as exp:
            try:
                self.log.info("%s", str(exp))
                self.admin_console.select_hyperlink(self.admin_console.props['label.finishLaterCTA'])
            except Exception as exp:
                raise Exception(str(exp))

    @WebAction()
    def click_get_started(self):
        """
        clicks the link, get started or lets finish it
        Returns:None

        """
        # Load all props
        getattr(self.admin_console, 'navigator')
        try:
            if self.admin_console.check_if_entity_exists('xpath',
                                           '//span[@data-ng-bind="coreSetupSubHeaderCompleted"]'):
                self.log.info("core setup completed")
                return False
            elif self.admin_console.check_if_entity_exists("xpath",
                                             "//div[@data-ng-if='coreSetupCompleted']"):
                self.log.info("Core setup completed")
                return False
            self.log.info("click on get started if listed")
            self.admin_console.select_hyperlink(self.admin_console.props['label.letsGetStarted']+" ")
            return True
        except Exception as exp:
            try:
                self.log.info("%s", str(exp))
                self.admin_console.select_hyperlink(self.admin_console.props['label.finishSetupCTA']+" ")
                return True
            except Exception as exp:
                raise Exception(str(exp))

    @WebAction()
    def access_tab(self, tab_header):
        """Method to click on given tab under guided setups"""

        self.driver.find_element(By.XPATH, 
            f"//a[@class='nav-link ng-binding' and text() ='{tab_header}']").click()
        self.admin_console.wait_for_completion()

    @WebAction()
    def access_panel(self, panel_title):
        """Method to click on the given panel with the title"""

        """Method to click on the given panel with the title"""

        panel_xpath = f"//div[contains(@class, 'guidedSetupTileClickableTile')]//p[contains(text(), '{panel_title}')]" \
                      "/ancestor::div[position()=2]"
        if self.admin_console.check_if_entity_exists('xpath', panel_xpath):
            self.driver.find_element(By.XPATH, panel_xpath).click()
            self.admin_console.wait_for_completion()
        else:
            raise CVWebAutomationException("Solution is not listed.")

    @PageService()
    def navigate_to_services(self):
        """Navigates to services page"""

        self.admin_console.navigator.navigate_to_getting_started()
        self.access_tab('Services')

    @PageService()
    def navigate_to_metallic(self):
        """Navigates to metallic registration page"""

        self.navigate_to_services()
        self.admin_console.access_tile('appsCloud_metallicSetup')

    @WebAction()
    def get_metallic_link_status(self):
        """
            To get the metallic link status
            Returns: True if already linked
        """
        xpath = f"//button[contains(.,'{self.admin_console.props['label.MetallicUnsubscribe']}')]"
        if self.admin_console.check_if_entity_exists('xpath', xpath):
            element = self.admin_console.driver.find_element(By.XPATH, xpath)
            return element.is_displayed()

    @PageService()
    def link_metallic_account(self, username, password):
        """To register to metallic services

        Args:
             username: metallic company user
             password: metallic company password

        """

        self.admin_console.fill_form_by_id("userName", username)
        self.admin_console.fill_form_by_id("userNamePassword", password)
        self.admin_console.submit_form('linkMetallicAccount')
        self.admin_console.check_error_message()

    @PageService()
    def unlink_metallic_account(self):
        """Unregister to metallic services"""

        self.navigate_to_metallic()
        self.admin_console.click_button(self.admin_console.props['label.MetallicUnsubscribe'])
        self.admin_console.click_button('Yes')
        self.admin_console.check_error_message()

    @WebAction()
    def mark_solution_complete(self, solution_name):
        """Marks the solution complete"""
        self.access_panel(solution_name)
        xpath = "//*[contains(@class,'mark-as-complete')]/a"
        if self.admin_console.check_if_entity_exists('xpath', xpath):
            self.admin_console.click_by_xpath(xpath)
            self.admin_console.check_error_message()

    @PageService()
    def skip_coresetup_completion(self):
        "skip the core setup configuration on freshly installed cs"
        self.__skip_core_setup()
        self.admin_console.wait_for_completion()

    @WebAction()
    def __select_configure_button_of_card(self, card_title):
        """Selects configure option of the card"""
        xpath = (
            f"//p[text()='{card_title}']/ancestor::div[contains(@class, 'MuiCard-root')]/"
            "descendant::button[@aria-label='Configure']"
        )
        self.driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def select_card(self, card_title):
        """Selects configure option of the card"""
        self.__select_configure_button_of_card(card_title)
        self.admin_console.wait_for_completion()
        