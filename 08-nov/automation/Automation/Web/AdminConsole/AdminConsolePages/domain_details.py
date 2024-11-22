# -*- coding: utf-8 -*-s

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides functions or operations that can be performed on the Domains Details page

__return_elements_from_element_obj()    -- Returns elements with xpath from element object
modify_domain()                         -- edits the properties of a domain
extract_domain_info()                   -- returns details of the domain displayed on
                                            the Domain Details page
"""
from selenium.webdriver.common.by import By

from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.AdminConsolePages.identity_servers import Domains
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown


class DomainDetails:
    """
        This class provides the function or operations that can be performed
        on the Domains page on the AdminConsole
    """

    def __init__(self, adminpage_obj):

        self.__driver = adminpage_obj.driver
        self.__adminpage_obj = adminpage_obj
        self.__drop_down = RDropDown(adminpage_obj)
        self.__domains_obj = Domains(self.__adminpage_obj)
        self.__panel_info = RPanelInfo(adminpage_obj, 'General')

    @WebAction()
    def __return_elements_from_element_obj(self, elem, xpath):
        """Returns elements with xpath from element object"""

        return elem.find_elements(By.XPATH, xpath)

    @PageService()
    def modify_domain(self, domain_dict):
        """
        Modifies the domain information

        Args:

            domain_dict (dict)       : Dict of values to be modified.
                                       Accepted keys - username, password, domainName.


        Returns:
            None
        """

        self.__panel_info.edit_tile()

        for key, value in domain_dict.items():
            if key not in ['proxy_client', 'proxy_client_value']:
                self.__adminpage_obj.fill_form_by_id(key, value)

        if domain_dict.get('proxy_client'):
            self.__adminpage_obj.checkbox_select("accessViaClient")
            if domain_dict.get('proxy_client_value'):
                self.__drop_down.select_drop_down_values(
                    values=[domain_dict.get('proxy_client_value')], drop_down_id='proxies')
        else:
            self.__adminpage_obj.checkbox_deselect("accessViaClient")

        self.__adminpage_obj.click_button(self.__adminpage_obj.props['label.save'])
        self.__adminpage_obj.wait_for_completion()
        self.__adminpage_obj.check_error_message()

    @PageService()
    def extract_domain_info(self):
        """Returns dict of domain details of selected domain on the Domains Details page"""

        details_page_elems = self.__domains_obj.return_elements(
                                                            "//*[@id='tileContent_General']/ul/li")
        domain_info = {}

        for elem in details_page_elems:
            span = self.__return_elements_from_element_obj(elem,
                                                    ".//span[contains(@class,'pageDetailColumn')]")
            key = span[0].text
            value = span[1].text
            domain_info[key] = value
        return domain_info

    @PageService()
    def get_domain_details(self):
        """
        Displays all the details about the domain

        Returns:
            domain_details   (dict):  dict of domain details
        """
        domain_details = self.__panel_info.get_details()
        return domain_details
