from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides method for search and filter content and files.

Classes:

    vsa_search_restore ---> _Navigator() ---> login_page() ---> AdminConsoleBase() ---> Object()

    VsaSearchRestore() -- This class provides methods to search for files and content in the
                            backed up VM and filter them on extension

Functions:

    select_file_type()      --  filters the files with the specific extension

    search_for_content()    --  searches for content or files in the backed up VM

"""

from Web.Common.page_object import WebAction


class VsaSearchRestore:
    """
    This class provides methods to do various types of search, restore and download
    """

    def __init__(self, admin_console):
        """ """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver

    @WebAction()
    def select_file_type(self, file_types):
        """
        Selects the file types from the list of all file types in search results

        Args:
            file_types  (str / list):     All or list of all file types to select from in
                                                    search results

        Raises:
            Exception:
                if there are no file types to select from or
                if the given file type is not present in the list of file types

        """
        xpath = "//label[contains(.,'File Type')]/../cv-facet-parameters[1]"
        if self.__admin_console.check_if_entity_exists("xpath", xpath):
            if isinstance(file_types, str):
                if file_types.lower() == "all":
                    type_xpath = xpath + "/div//label[contains(.,'All')]"
                    self.__driver.find_element(By.XPATH, type_xpath).click()
                    self.__admin_console.wait_for_completion()
                    return
                else:
                    file_types = [file_types]

            for file_type in file_types:
                type_xpath = xpath + "/div//label[contains(.,'" + file_type + "')]"
                self.__driver.find_element(By.XPATH, type_xpath).click()
                self.__admin_console.wait_for_completion()
        else:
            raise Exception("There are no file types to select from")

    @WebAction()
    def select_data_type(self, data_types):
        """
        Selects the file types from the list of all file types in search results

        Args:
            data_types  (str / list):     All or list of all data types to select from in
                                                    search results

        Raises:
            Exception:
                if there are no data types to select from or
                if the given data type is not present in the list of data types

        """
        xpath = "//label[contains(.,'Data Type')]/../cv-facet-parameters[1]"
        if self.__admin_console.check_if_entity_exists("xpath", xpath):
            if isinstance(data_types, str):
                if data_types.lower() == "all":
                    type_xpath = xpath + "/div//label[contains(.,'All')]"
                    self.__driver.find_element(By.XPATH, type_xpath).click()
                    self.__admin_console.wait_for_completion()
                    return
                else:
                    data_types = [data_types]

            for data_type in data_types:
                type_xpath = xpath + "/div//label[contains(.,'" + data_type + "')]"
                self.__driver.find_element(By.XPATH, type_xpath).click()
                self.__admin_console.wait_for_completion()
        else:
            if self.__admin_console.check_if_entity_exists("xpath", "//span[@data-ng-show='showGrid' and "
                                                                    "contains(.,'No results found')]"):
                raise Exception("There are no results to display")

    @WebAction()
    def search_for_content(self,
                           file_name=None,
                           contains=None,
                           file_type=None,
                           modified=None,
                           include_folders=False):
        """
        Searches for files and content

        Args:
            file_name           (str):   name of the files to search for

            contains            (str):   the text that the filename of file should contain

            file_type           (str):   list of all file types to search

            modified            (str):   the time when the files were modified

            include_folders     (bool):         if folders should be included in the search

        Raises:
            Exception:
                if there is no option to search for files and content in the VM

        """
        clear = self.__driver.find_element(By.XPATH, "//cv-browse-vsa-search/form/div/input"
                                                  ).get_attribute("class")
        if "field-has-input" in clear:
            self.__driver.find_element(By.XPATH, "//cv-browse-vsa-search/form/div/span").click()
            self.__admin_console.wait_for_completion()

        self.__driver.find_element(By.XPATH, "//cv-browse-vsa-search/form/div/input").click()
        self.__admin_console.wait_for_completion()

        self.__driver.find_element(By.XPATH, "//cv-browse-vsa-search/form/div/input").clear()
        self.__admin_console.wait_for_completion()

        if not self.__admin_console.check_if_entity_exists("id", "search-filter-dropdown"):
            raise Exception("There is no way to search for files and content")

        if file_name:
            self.__admin_console.fill_form_by_id("fileName", file_name)

        if contains:
            self.__admin_console.fill_form_by_id("contains", contains)

        if file_type:
            self.__admin_console.select_value_from_dropdown("fileType", file_type)

        if modified:
            self.__admin_console.select_value_from_dropdown("modified", modified)

        if include_folders:
            self.__admin_console.checkbox_select("includeFolders")
        else:
            self.__admin_console.checkbox_deselect("includeFolders")

        self.__admin_console.submit_form()

    @WebAction()
    def validate_file_types(self, file_type):
        """
        Validates the filtered content and checks the result
        Args:
            file_type   (str):   the file type to validate

        Raises:
            Exception:
                if the file type is not present or
                the file types filter could not be applied

        """
        xpath = "//label[contains(.,'File Type')]/../cv-facet-parameters[1]"
        file_types = []
        if self.__admin_console.check_if_entity_exists("xpath", xpath):
            elements = self.__driver.find_elements(By.XPATH, xpath + "/div/div")
            for element in elements:
                text = element.find_element(By.XPATH, "./label").text.strip()
                file_types.append(text.split("(")[0].strip())

            if file_type not in file_types:
                raise Exception("The file type is not present")
        else:
            raise Exception("There are no file types to select from")

    @WebAction()
    def validate_contains(self, contains_text, name=True, folder=False):
        """
        Validates the file names in the search result matches with the text

        Args:
            contains_text   (str):   the text the filename should contain

            name            (bool):         if the filename should be matched

            folder          (bool):         if the folder name should be matched

        Raises:
            Exception:
                if the file name does not match the contains criteria

        """
        while True:
            elements = self.__driver.find_elements(By.XPATH, 
                "//div[@class='ui-grid-contents-wrapper']/div[2]//div[@class='ui-grid-canvas']"
                "/div")
            for element in elements:
                if name:
                    entity_name = element.find_element(By.XPATH, "./div/div[1]/div").text
                elif folder:
                    entity_name = element.find_element(By.XPATH, "./div/div[3]/div").text
                if contains_text not in entity_name:
                    raise Exception("The contains criteria does not match for file " + entity_name)
            if self.__admin_console.cv_table_next_button_exists():
                if self.__driver.find_element(By.XPATH, 
                        "//button[@ng-click='pageNext()']").is_enabled():
                    self.__driver.find_element(By.XPATH, 
                        "//button[@ng-click='pageNext()']/div").click()
                    self.__admin_console.wait_for_completion()
                    continue
                else:
                    break
            else:
                break

    @WebAction()
    def validate_folders(self):
        """
        Validates if folder results are displayed in the search result

        Raises:
            Exception:
                if folders are not present in the search result or
                data type filters could not be applied

        """
        xpath = "//label[contains(.,'Data Type')]/../cv-facet-parameters[1]"
        data_types = []
        if self.__admin_console.check_if_entity_exists("xpath", xpath):
            elements = self.__driver.find_elements(By.XPATH, xpath + "/div/div")
            for element in elements:
                text = element.find_element(By.XPATH, "./label").text.strip()
                data_types.append(text.split("(")[0].strip())
            if 'Folder' not in data_types:
                raise Exception("Folders are not present in the search result")
        else:
            raise Exception("Data type filters could not be obtained")
