# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Email Templates page on the AdminConsole

Class:

    EmailTemplates()

Functions:

    modify_email_header_footer()  --   Method to add email header and footer

"""
from selenium.webdriver.common.by import By
from Web.Common.page_object import WebAction, PageService


class EmailHeaderFooter:
    """ Class for Email Header and footer configuration page  """

    def __init__(self, adminpage_obj):

        self.__adminpage_obj = adminpage_obj
        self.__adminpage_obj.load_properties(self)
        self.__driver = adminpage_obj.driver

    @WebAction()
    def __switch_to_header_iframe(self):
        """ Switch the driver object to header editor iframe """

        email_header_iframe_xpath = "//div[@id='header-editor']" \
                                    "//iframe[contains(@class, 'k-content')]"
        self.__driver.switch_to.frame(self.__driver.find_element(By.XPATH, email_header_iframe_xpath))

    @WebAction()
    def __switch_to_footer_iframe(self):
        """ Switch the driver object to header editor iframe """

        email_footer_iframe_xpath = "//div[@id='footer-editor']" \
                                    "//iframe[contains(@class, 'k-content')]"
        self.__driver.switch_to.frame(self.__driver.find_element(By.XPATH, email_footer_iframe_xpath))

    @WebAction()
    def __populate_header_or_footer_body(self, text_content, append_content):
        """
        Fill the header or footer body with text content

        Args:
            text_content    (str): Content to be used in header/footer
            append_content (bool): pass True to append content to existing header/footer,
                                   pass False to clear older content
        """
        if not append_content:
            self.__driver.find_element(By.XPATH, "//body").clear()
        self.__driver.find_element(By.XPATH, "//body").send_keys(text_content)

    @PageService()
    def modify_email_header_footer(self,
                                   email_header,
                                   email_footer,
                                   append_content=False):
        """
        Method to create email header or footer

        Args:
            email_header(str)       :   Text to be added as email header
            email_footer(str)       :   Text to be added as email footer
            append_content (bool)   :   pass True to append content to existing header/footer,
                                        pass False to clear older content

        Returns:
            None

        Raises:
            Exception:
                if fails to create email header or footer
        """
        if email_header:
            self.__switch_to_header_iframe()
            self.__populate_header_or_footer_body(email_header, append_content)
            self.__driver.switch_to.default_content()

        if email_footer:
            self.__switch_to_footer_iframe()
            self.__populate_header_or_footer_body(email_footer, append_content)
            self.__driver.switch_to.default_content()

        self.__adminpage_obj.click_button("Save")
        self.__adminpage_obj.wait_for_completion()
