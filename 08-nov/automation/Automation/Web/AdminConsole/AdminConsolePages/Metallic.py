# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on
the Metallic page on the AdminConsole

Class:

    Metallic()

Functions:

    get_solutions()     :   Returns all the available solutions
    select_solution()   :   Selects the given solution
    get_metallic_navigation_status()    :    Returns if Metallic Navigation is available or not

"""

from selenium.webdriver.common.by import By
from Web.Common.page_object import WebAction, PageService

class Metallic:
    """ Class for Metallic page of AdminConsole """
    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver

    @WebAction()
    def get_solutions(self):
        """Returns a list of all the available solutions"""
        solutions = []
        for i in range(1,11):
            solution_xpath = f'//*[contains(@data-ng-if,"solutionsConfigured")]/div[{i}]//h4'
            if self.__admin_console.check_if_entity_exists('xpath', solution_xpath):
                solutions.append(self.__driver.find_element(By.XPATH, solution_xpath).text)
        return solutions

    @PageService()
    def select_solution(self, solution_name):
        """Selects the given solution"""
        xpath = f'//*[contains(@data-ng-if,"solutionsConfigured")]'\
                f'//h4[contains(text(),"{solution_name}")]'
        self.__admin_console.click_by_xpath(xpath)
        self.__admin_console.check_error_message()

    @PageService()
    def get_metallic_navigation_status(self):
        """Returns if Metallic Navigation is available or not"""
        return self.__admin_console.navigator.check_if_id_exists('navigationItem_metallic')
