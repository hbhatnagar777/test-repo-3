# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Set operations specific to Query Set. Inheriting from the class- SetOperations.

QuerysetOperations is the only class defined in this module.

QuerysetOperations: Defines various queryset operations.

QuerysetOperations:

    create_set()    --  Creates a queryset.

    execute_set()   --  Executes the query- query_name from the queryset.

    add_to_set()    --  Adds query to a queryset.

QuerysetOperations Attributes:

    settype         --  Placeholder for the type of set i.e 'Query Set'.

    ini             --  An object of the Initiator class.

"""
from selenium import webdriver
from Web.Common.exceptions import NonFatalException
from AutomationUtils import logger
from dynamicindex.utils import setutils
from dynamicindex.utils.constants import DELETE_SET, QUERYSET, QUERYSET_NAME_PREFIX
from dynamicindex.utils.constants import QUERY_NAME_FORMAT
from dynamicindex.utils.constants import APPTYPE_ALL, APPTYPE_FILES, APPTYPE_EMAILS
from ..common.initiator import Initiator
from ..common.validation import Validation
from ..common.locators import CommonSetLocators
from ..common.locators import SearchPageLocators
from ..common.locators import MainPageLocators
from ..common.locators import Locators
from ..common.setoperations import SetOperations


class QuerysetOperations(SetOperations):
    """Defines various queryset operations."""
    settype = QUERYSET
    ini = None

    def __init__(self):
        """Initializes the instance attributes."""

        self.ini = Initiator()
        self.ini.create_driver_object()
        self.driver = self.ini.driver
        super(QuerysetOperations, self).__init__(self.driver, self.settype)
        self.logger = logger.get_log()

    def create_set(self, query, searchengine, apptype, special_chars=False):
        """Creates a queryset.

        Args:
            query            (str)   --  The search query.

            searchengine     (str)   --  Name of the searchengine.

            apptype          (str)   --  Application type.

            special_chars    (bool)  --  If the setname should contain special chars.

        Returns:
            tuple  -  A tuple containing the created setname & no. of items added to the query.

        Raises:
            NonFatalException:
                When a container with the given name already exists.

            Exception:
                When an error occurs while performing this operation.
        """
        if special_chars:
            queryset_name = QUERYSET_NAME_PREFIX + setutils.generate_charstream()
        else:
            # Appends a random string to the param - queryset_name.
            queryset_name = setutils.generate_random_name(QUERYSET_NAME_PREFIX)
        query_name = QUERY_NAME_FORMAT
        common = CommonSetLocators(self.settype, queryset_name, query_name, '')
        validation = Validation(self.driver)
        body_element = self.driver.find_element(*Locators.BODY_ELEMENT)
        self.triger_query(query, searchengine, apptype)
        number_of_items = validation.display_result(
            *SearchPageLocators.DISPLAY_RESULT_ALL_TEXT)
        self.logger.info("Query %s resulted in %d items", query, number_of_items)
        self.driver.find_element(*SearchPageLocators.SAVEQUERY_BUTTON).click()
        self.driver.find_element(*common.SAVEQUERY_QUERYNAME_INPUT_FIELD).send_keys(query_name)
        self.driver.find_element(*common.SET_EXPAND_ARROW).click()
        validation.wait_to_load()
        self.driver.find_element(*common.SET_CREATENEW_TEXT).click()
        self.driver.find_element(*common.CREATENEWSET_INPUT_FIELD).send_keys(queryset_name)
        self.driver.find_element(*common.SECONDMENU_OK_BUTTON).click()
        validation.wait_to_load()
        if common.CONTAINER_EXISTS_TEXT in body_element.text:
            self.logger.info("Container by the name %s already exists.", queryset_name)
            self.driver.find_element(*common.SAVEQUERYMENU_CLOSE_BUTTON).click()
            raise NonFatalException("Container with this name already exists.")
        elif validation.if_displayed(*common.SETNAME_EXISTS_TEXT):
            self.logger.info("Trying to create a set with special characters in its name.")
            self.driver.find_element(*common.CONFIRM_BUTTON).click()
            validation.wait_to_load()
            self.driver.find_element(*common.FIRSTMENU_OK_BUTTON).click()
            if validation.if_displayed(*common.MAXIMUMQUERIES_TEXT):
                self.logger.info(
                    "You have already saved maximum number of queries allowed.")
                raise Exception("You have already saved maximum number of queries allowed.")
            else:
                self.logger.info("Query set with an appropriate name is created successfully.")
                queryset_name = setutils.generate_created_setname(queryset_name)
        else:
            self.driver.find_element(*common.FIRSTMENU_OK_BUTTON).click()
            self.logger.info("Query set %s created successfully.", queryset_name)
            if common.QUERYSAVED_TEXT in self.driver.find_element(*Locators.BODY_ELEMENT).text:
                self.logger.info(common.QUERYSAVED_TEXT)

            elif validation.if_displayed(*common.MAXIMUMQUERIES_TEXT):
                self.logger.info(
                    "You have already saved maximum number of queries allowed.")
                raise Exception("You have already saved maximum number of queries allowed.")

        validation.close_search_tabs()
        self.open_specific_set(queryset_name)

        if validation.if_displayed(*common.DISPLAY_SET_ITEMS_TEXT):
            count = validation.display_result(
                *common.DISPLAY_SET_ITEMS_TEXT)
            self.logger.info(
                "Number of queries present in the query set %s is: %d", queryset_name, count)
            if count <= 0:
                self.logger.info("Query didn't get added.")
                self.logger.info("Going to delete the query set.")
                self.delete_set(queryset_name, DELETE_SET)
                raise Exception("Query didn't get added.")

            self.driver.find_element(*MainPageLocators.COLLAPSE_ARROW).click()
            validation.close_search_tabs()
            validation.loading()
        else:
            raise Exception("Couldn't check whether or not the query got added.")
        return queryset_name, number_of_items

    def execute_set(self, queryset_name, query_name, total_items):
        """Executes the query- query_name from the queryset.

        Args:
            queryset_name    (str)  --  Name of the queryset.

            query_name       (str)  --  Name of the query to be executed.

            total_items      (int)  --  No. of items returned by executing the query.

        Raises:
            NonFatalException:
                When the query can't be executed.

            Exception:
                When an error occurs while performing this operation.
        """
        common = CommonSetLocators(self.settype, queryset_name, query_name, '')
        validation = Validation(self.driver)
        ltype = {APPTYPE_ALL: SearchPageLocators.DISPLAY_RESULT_ALL_TEXT,
                 APPTYPE_FILES: SearchPageLocators.DISPLAY_RESULT_FS_TEXT,
                 APPTYPE_EMAILS: SearchPageLocators.DISPLAY_RESULT_EMAIL_TEXT}
        validation.close_search_tabs()
        self.logger.info("Executing the query '%s' from '%s'", query_name, queryset_name)
        self.open_specific_set(queryset_name)
        self.logger.info("Clicking on the query link '%s'", query_name)
        self.driver.find_element(*common.QUERYNAME_LINK).click()
        if validation.if_displayed(*common.EXECUTE_PERMISSION_NOT_AVAILABLE):
            self.logger.info(
                "Couldn't execute this query.")
            self.driver.find_element(*common.FIRSTMENU_OK_BUTTON).click()
            raise NonFatalException("Couldn't execute this query.")
        validation.wait_to_load()
        self.driver.find_element(*common.SETTAB).click()
        self.driver.find_element(*SearchPageLocators.SEARCHTAB2_CLOSE_BUTTON).click()
        self.driver.find_element(*common.SETTYPE_TAB).click()
        self.driver.find_element(*SearchPageLocators.SEARCHTAB_CLOSE_BUTTON).click()
        
        items_in_query = validation.display_result(*ltype[APPTYPE_ALL])
        if total_items == items_in_query:
            self.logger.info(
                "Number of items saved to query '%s' are '%d' and is correct.",
                query_name,
                total_items)
        else:
            self.logger.info(
                "Total items added: %d but no. obtained after executing the query is %d.",
                total_items,
                items_in_query)
            raise Exception("Number of items present in the query is not consistent.")
        validation.close_search_tabs()

    def add_to_set(self, queryset_name, keyword, searchengine, apptype):
        """Adds query to a queryset.

        Args:
            queryset_name     (str)  --  Name of the query set.

            keyword           (str)  --  The search query.

            searchengine      (str)  --  Name of the searchengine.

            apptype           (int)  --  Application type.

        Raises:
            NonFatalException:
                If 'Add' permission is not enabled for this set.

            Exception:
                When an error occurs while performing this operation.
        """
        query_name = setutils.generate_random_name(QUERY_NAME_FORMAT)
        common = CommonSetLocators(self.settype, queryset_name, query_name, '')
        validation = Validation(self.driver)
        validation.close_search_tabs()
        self.driver.find_element(*MainPageLocators.EXPAND_ARROW).click()
        self.open_specific_set(queryset_name)
        query_before = validation.display_result(
            *common.DISPLAY_SET_ITEMS_TEXT)
        validation.close_search_tabs()
        self.logger.info(
            "Adding a new query by the name %s to the query set %s", query_name, queryset_name)
        self.triger_query(keyword, searchengine, apptype)
        count_before = validation.display_result(
            *SearchPageLocators.DISPLAY_RESULT_ALL_TEXT)
        self.logger.info("The search query resulted in %d items.", count_before)
        self.driver.find_element(*SearchPageLocators.SAVEQUERY_BUTTON).click()
        self.driver.find_element(*common.SAVEQUERY_QUERYNAME_INPUT_FIELD).send_keys(query_name)
        self.driver.find_element(*common.SET_EXPAND_ARROW).click()
        if validation.if_displayed(*common.SET_CREATENEW_TEXT):
            if validation.if_displayed(*common.EXISTINGSET_NAME):
                self.logger.info("Add permission is enabled for queryset %s", queryset_name)
                element = self.driver.find_element(*common.EXISTINGSET_NAME)
                webdriver.ActionChains(self.driver).move_to_element(
                    element).click(element).perform()
                self.driver.find_element(*common.FIRSTMENU_OK_BUTTON).click()
                body_element = self.driver.find_element(*Locators.BODY_ELEMENT)
                if common.QUERYSAVED_TEXT in body_element.text:
                    self.logger.info(
                        "Query by the name %s has been added to the queryset.", query_name)
                elif validation.if_text_present_in_events(common.QUERYSAVED_TEXT):
                    self.logger.info(
                        "Query by the name %s has been added to the queryset.", query_name)
                else:
                    self.logger.info(
                        "Query by the name %s might not have been added to the set %s",
                        query_name,
                        queryset_name)
                validation.close_search_tabs()
                self.driver.find_element(*MainPageLocators.EXPAND_ARROW).click()
                self.open_specific_set(queryset_name)
                query_after = validation.display_result(
                    *common.DISPLAY_SET_ITEMS_TEXT)
                if query_after == query_before + 1:
                    self.logger.info(
                        "A total of %d queries are present in the queryset %s",
                        query_after, queryset_name)
                else:
                    self.logger.info(
                        "Total %d queries were present in the queryset before this operation.",
                        query_before)
                    self.logger.info(
                        "Total %d queries are present in the queryset after this operation.",
                        query_after)
                    raise Exception(
                        "Some error occurred while adding queries to the queryset.")
                validation.close_search_tabs()
            else:
                raise NonFatalException("Add permission is not enabled for this set.")
        validation.close_search_tabs()

    def __del__(self):
        self.driver.close()
