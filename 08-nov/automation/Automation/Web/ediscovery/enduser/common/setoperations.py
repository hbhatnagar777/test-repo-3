# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Inherit from this class for accessing the set operations which are common to all the sets.

SetOperations is the only class defined in this module.

SetOperations: Implements common set operations.

SetOperations:

    open_specific_set()       --  Opens the set with display-name setname of type settype.

    open_mysets()             --  Opens 'My Sets'.

    triger_query()            --  Fires a search query.

    delete_set()              --  Deletes the content in the set or the set itself.

    share_set()               --  Shares the set with a user.

"""
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException
from Web.Common.exceptions import NonFatalException
from AutomationUtils import logger
from dynamicindex.utils import setutils
from dynamicindex.utils.constants import DELETE_SELECTED, DELETE_PAGE, DELETE_ALL, DELETE_SET
from dynamicindex.utils.constants import SHARE_ADD_PERMISSION, SHARE_DELETE_PERMISSION
from dynamicindex.utils.constants import SHARE_EXECUTE_PERMISSION, SHARE_VIEW_PERMISSION
from dynamicindex.utils.constants import SHARE_ALL_PERMISSION, SHARE_NO_PERMISSION
from dynamicindex.utils.constants import APPTYPE_FILES, APPTYPE_EMAILS, APPTYPE_ALL
from dynamicindex.utils.constants import ONE_MINUTE
from .validation import Validation
from .locators import CommonSetLocators
from .locators import MainPageLocators
from .locators import SearchPageLocators
from .locators import Locators


class SetOperations(object):
    """Implements common set operations."""

    def __init__(self, driver, settype):
        """Initializes the instance attributes.

        Args:
           driver    (object)  --  An instance of WebDriver class.

           settype   (str)     --  Type of the set.
        """
        self.logger = logger.get_log()
        self.driver = driver
        self.settype = settype

    def open_specific_set(self, setname):
        """Opens the set with display-name setname of type settype.

        Args:
            setname    (str)  --  Name of the set.
        """
        common = CommonSetLocators(self.settype, setname, '', '')
        validation = Validation(self.driver)
        validation.close_search_tabs()
        self.open_mysets()
        self.driver.find_element(*common.SETTYPE_TEXT).click()
        self.logger.debug("%s is now open.", self.settype)
        validation.loading()
        second = 0
        while True:
            if second > ONE_MINUTE / 20:
                self.logger.info(
                    "Couldn't select %s even after waiting for around a minute.", setname)
                break

            if validation.if_displayed(
                    *common.EXPAND_QUERYSET) or validation.if_displayed(
                    *common.SETNAME_TEXT):
                self.logger.info("Going to select %s", setname)
                self.driver.find_element(*common.SETNAME_TEXT).click()
                self.logger.info("Collapsing the %s button.", self.settype)
                if validation.if_displayed(*common.SETTYPE2_TEXT):
                    self.driver.find_element(*common.SETTYPE2_TEXT).click()
                else:
                    self.driver.find_element(*common.SETTYPE_TEXT).click()  
                break
            else:
                 if validation.if_displayed(*common.SETTYPE2_TEXT):
                    self.driver.find_element(*common.SETTYPE2_TEXT).click()
                 else:
                    self.driver.find_element(*common.SETTYPE_TEXT).click()  
                 second += 1

        validation.wait_to_load()

    def open_mysets(self):
        """Opens 'My Sets'."""
        validation = Validation(self.driver)
        self.logger.info("Going to expand the Search Menu.")
        try:
            if validation.if_displayed(
                    *MainPageLocators.EXPAND_ARROW) and self.driver.find_element(
                    *MainPageLocators.EXPAND_ARROW).is_enabled():
                self.logger.info("Clicking the expand arrow.")
                self.driver.find_element(*MainPageLocators.EXPAND_ARROW).click()
                button_text = self.driver.find_element(*MainPageLocators.MYSETS_BUTTON_TEXT)
                if button_text.is_displayed():
                    self.logger.info("Clicking on 'My Sets' button.")
                    self.driver.find_element(
                        *MainPageLocators.MYSETS_BUTTON).click()
        except WebDriverException:
            self.logger.info("Sleeping for 10 seconds.")
            time.sleep(10)
            self.logger.info("Clicking the backup expand arrow.")
            self.driver.find_element(*MainPageLocators.BACKUPEXPAND_ARROW).click()
            button_text = self.driver.find_element(*MainPageLocators.MYSETS_BUTTON_TEXT)
            if button_text.is_displayed():
                self.logger.info("Clicking on 'My Sets' button.")
                self.driver.find_element(*MainPageLocators.MYSETS_BUTTON).click()

    def triger_query(self, query, searchengine, apptype):
        """Fires a search query.

        Args:
            query           (str)  --  Search query to be fired.

            searchengine    (str)  --  Name of the search engine.

            apptype         (int)  --  Application type.

        """
        apptype_button = {
            APPTYPE_FILES: SearchPageLocators.FILES_BUTTON,
            APPTYPE_EMAILS: SearchPageLocators.EMAILS_BUTTON,
            APPTYPE_ALL: SearchPageLocators.FILESEMAILS_BUTTON}
        validation = Validation(self.driver)
        self.logger.info("Clicking on 'Advanced Search' button.")
        self.driver.find_element(*MainPageLocators.ADVANCEDSEARCH_BUTTON).click()
        self.driver.find_element(*MainPageLocators.SEARCHOPTIONS_LINK).click()
        validation.loading()
        self.logger.info("Clicking on the search engine dropdown button.")
        self.driver.find_element(*MainPageLocators.SEARCHENGINE_MENU).click()
        searchengine_xpath = MainPageLocators.set_searchengine(self, searchengine)
        actions = ActionChains(self.driver)
        self.logger.info("Choosing the search engine '%s'", searchengine)
        element = self.driver.find_element(*searchengine_xpath)
        actions.move_to_element(element).click().perform()
        self.logger.info("Clicking on 'Keyword' link.")
        self.driver.find_element(*MainPageLocators.KEYWORD_LINK).click()
        action_keyword = ActionChains(self.driver)
        validation.wait_to_load()
        self.logger.info("Sending query to the textarea element.")
        textarea_element = self.driver.find_element(*MainPageLocators.KEYWORD_TEXTAREA)
        action_keyword.send_keys_to_element(textarea_element, query).perform()
        self.logger.info("Submitting the search query.")
        self.driver.find_element(
            *MainPageLocators.SEARCH_SUBMIT_BUTTON).click()
        validation.wait_for_element(
            ONE_MINUTE/6, *SearchPageLocators.DISPLAY_RESULT_ALL_TEXT)
        validation.wait_for_element(
            ONE_MINUTE/6, *SearchPageLocators.FILESEMAILS_MENU)
        validation.wait_to_load()
        self.driver.find_element(*SearchPageLocators.FILESEMAILS_MENU).click()
        self.logger.info("Choosing the required apptype.")
        self.driver.find_element(*apptype_button[apptype]).click()

    def delete_set(self, setname, deletion_range):
        """Deletes the content in the set or the set itself, based on the param deletion_range.

        Args:
            setname           (str)  --  Name of the set.

            deletion_range    (int)  --  Denotes the range of elements to be deleted.

        Raises:
            NonFatalException:
                If the user doesn't have delete privileges on the set.
        """
        common = CommonSetLocators(self.settype, setname, '', '')
        validation = Validation(self.driver)
        deletion_xpath = {
            DELETE_SELECTED: common.DELETESELECTED_RADIO_BUTTON,
            DELETE_PAGE: common.DELETEPAGE_RADIO_BUTTON,
            DELETE_ALL: common.DELETEALL_RADIO_BUTTON,
            DELETE_SET: common.DELETESET_RADIO_BUTTON}
        self.logger.info("Going to delete the container %s.", setname)
        self.open_specific_set(setname)
        validation.loading()
        count_before = validation.display_result(
            *common.DISPLAY_SET_ITEMS_TEXT)
        self.driver.find_element(*common.DELETE_LAST_BUTTON).click()
        validation.wait_to_load()
        if validation.if_displayed(*common.CONFIRMDELETION_TEXT):
            self.driver.find_element(*deletion_xpath[deletion_range]).click()
            self.driver.find_element(*common.CONFIRM_BUTTON).click()
            if deletion_range == DELETE_SET:
                body_element = self.driver.find_element(*Locators.BODY_ELEMENT)
                expected_string = self.settype + " " + setname + " deleted successfully."
                if expected_string in body_element.text:
                    self.logger.info(
                        "The container %s has been deleted.", setname)
            else:
                self.driver.find_element(*MainPageLocators.EXPAND_ARROW).click()
                self.open_specific_set(setname)
                count_after = validation.display_result(
                    *common.DISPLAY_SET_ITEMS_TEXT)
                self.logger.info("Number of queries before deletion: %d", count_before)
                self.logger.info("Number of queries after deletion: %d", count_after)
        else:
            self.logger.info("User doesn't have 'Delete Privilege' on this set.")
            raise NonFatalException("User doesn't have 'Delete Privilege' on this set.")

    def share_set(self, setname, owner, share_with_user, permission):
        """Shares the set with a user.

        Args:
            setname            (str)  --  Name of the set.

            owner              (str)  --  Owner of the set.

            share_with_user    (str)  --  The username with which the set is to be shared.

            permission         (int)  --  Sharing permission on the set.

        Returns:
            str  -  The shared setname.
        """
        common = CommonSetLocators(self.settype, setname, '', share_with_user)
        validation = Validation(self.driver)
        permissions = {
            SHARE_ADD_PERMISSION: common.SHARE_ADDAPPEND_RADIO_BUTTON,
            SHARE_DELETE_PERMISSION: common.SHARE_DELETE_RADIO_BUTTON,
            SHARE_EXECUTE_PERMISSION: common.SHARE_EXECUTE_RADIO_BUTTON,
            SHARE_VIEW_PERMISSION: common.SHARE_VIEW_RADIO_BUTTON,
            SHARE_ALL_PERMISSION: 'Set all permissions',
            SHARE_NO_PERMISSION: 'Set no permissions'}
        self.open_specific_set(setname)
        self.logger.info(
            "Going to share the container %s of type %s with user %s",
            setname,
            self.settype,
            share_with_user)
        self.logger.info("Clicking on 'Share' button")
        self.driver.find_element(*common.SHARE_BUTTON).click()
        self.driver.find_element(*common.SHARE_USERADD_BUTTON).click()
        validation.wait_to_load()
        self.logger.info("Sharing the set with the user %s", share_with_user)
        self.driver.find_element(*common.SHARE_WITHUSER_TEXT).click()
        self.logger.info("Going to wait till all elements are fully loaded.")
        self.driver.find_element(*common.SECONDMENU_OK_BUTTON).click()
        if permission == SHARE_ALL_PERMISSION:
                # Adding all the permissions when permission number supplied is
                # SHARE_ALL_PERMISSION.
            for entry in permissions:
                self.driver.find_element(*permissions[entry]).click()
        elif permission == SHARE_NO_PERMISSION:
            self.logger.info("Going to deselect the default permission (View).")
            self.driver.find_element(*permissions[SHARE_VIEW_PERMISSION]).click()
        elif permission != SHARE_VIEW_PERMISSION:
            # Permission on 4th number in the list i.e. View permission is set by default
            self.logger.info(
                "Going to set permission with the xpath- %s", permissions[permission][1])
            self.driver.find_element(*permissions[permission]).click()
        self.logger.info("Clicking 'OK' button.")
        self.driver.find_element(*common.FIRSTMENU_OK_BUTTON).click()
        self.logger.info("Going to wait till the elements are fully loaded.")
        validation.wait_to_load()
        msg_xpath = common.SHARE_MESSAGE_TEXT
        validation.wait_for_element(ONE_MINUTE, *msg_xpath)
        message = self.driver.find_element(*msg_xpath).text
        self.logger.info(message)
        setname = setutils.get_setname(owner, setname)
        return setname
