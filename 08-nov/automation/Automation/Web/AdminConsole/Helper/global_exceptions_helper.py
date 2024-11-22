from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""

This module provides the function or operations that can be used to run
basic operations on Global Exceptions page.


GlobalExceptionsMain : This class provides methods for global exceptions related operations

    __init__()                           --     Initialize object of TestCase class associated

    create_global_filter()   	         --     Toa Add a new windows or unix global filter

    modify_global_filter()   	         --     To modify/Edit the windows or unix  global filter

    del_global_filter()     	         --     To delete the global filter

    _get_filter_value()                  --     To get the global filter values

    validate_global_filter() 	         --     To validate the global filter values

"""

from Web.AdminConsole.AdminConsolePages.global_exceptions import GlobalExceptions


class GlobalExceptionsMain:
    """Helper file to provide arguments and handle function call to main file"""

    def __init__(self, admin_page):
        """Initialize method for GlobalExceptionsMainMain """

        self.__admin_console = admin_page
        self.__global_exceptions = GlobalExceptions(admin_page)

        self._global_filter_path = {'windows_global_filter_path': 'C:\test1.txt',
                                    'unix_global_filter_path': 'root/test1.bat'}
        self._old_global_filter_path = None

    @property
    def global_filter_path(self):
        """ Get global filter path"""
        return self._global_filter_path

    @global_filter_path.setter
    def global_filter_path(self, value):
        """ Set windows global filter path"""
        self._global_filter_path = value
        if self._old_global_filter_path is None:
            self._old_global_filter_path = value

    def create_global_filter(self):
        """ calls the function to create a global filter """
        self.__admin_console.navigate_to_global_exceptions()
        self.__global_exceptions.add_global_filter(self.global_filter_path)

    def modify_global_filter(self):
        """"" Calls the function to modify\edit a global filter """

        self.__admin_console.navigate_to_global_exceptions()
        self.__global_exceptions.edit_global_filter(self._old_global_filter_path, self.global_filter_path)

    def del_global_filter(self):
        """Calls the function to delete the global filter"""

        self.__admin_console.navigate_to_global_exceptions()
        self.__global_exceptions.delete_global_filter(self.global_filter_path)

    def _get_filter_value(self, value):
        """to get the attribute value"""
        self.__global_exceptions.open_global_filter(value)
        filter_value = self.__admin_console.driver.find_element(By.ID, "filterEditData").get_attribute('value')
        return filter_value

    def validate_global_filter(self):
        """Validates  global path , if path is retained correctly or not"""
        if self.global_filter_path['windows_global_filter_path']:
            if not self._get_filter_value(
                    self.global_filter_path['windows_global_filter_path']) == \
                    self.global_filter_path['windows_global_filter_path']:
                exp = "windows global exception validation failed, windows global filter path " \
                      "was not retained correctly"
                raise Exception(exp)
            self.__admin_console.log.info("Windows Global filter path is retained correctly")
            self.__admin_console.cancel_form()

        if self.global_filter_path['unix_global_filter_path']:
            if not self._get_filter_value(
                    self.global_filter_path['unix_global_filter_path']) == \
                    self.global_filter_path['unix_global_filter_path']:
                exp = "validation failed, unix global filter path was not retained correctly"
                raise Exception(exp)
            self.__admin_console.log.info("Unix Global filter path is retained correctly")
            self.__admin_console.cancel_form()
