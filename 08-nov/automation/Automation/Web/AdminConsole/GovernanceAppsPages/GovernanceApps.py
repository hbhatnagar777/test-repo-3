from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Governance Apps page.

GovernanceApps  --  This class contains all the methods for action in Governance Apps
                    page and is inherited by other classes to perform GDPR related
                    actions.

    Functions:

    select_inventory_manager()           --  Opens the Inventory manager page
    select_sensitive_data_analysis()     --  Opens the sensitive data analysis page
    select_request_manager()             --  Opens the request manager page
    select_entity_manager()              --  Opens the entity manager page
    select_compliance_search()           --  Opens the Compliance Search page
    select_permission_report()           --  Opens Entitlement manager page
    select_case_manager()                --  Opens Case manager page
    select_file_storage_optimization()   --  Opens FSO page
    select_sda_getting_started           --  Opens the sensitive data analysis page
                                             from getting started page
    get_component_value()                --  Returns the text of custom HIT component on activate custom reports
    __select_link()                      --  Clicks on the link with given text
    __select_link_getting_started()      --  Clicks on the link with given text

"""

from Web.Common.page_object import WebAction, PageService


class GovernanceApps:
    """
     This class contains all the methods for action in Governance Apps Page
    """
    inventory_name = None
    plan_name = None

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        self.__admin_console = admin_console
        self.driver = self.__admin_console.driver
        self.log = self.__admin_console.log

    @PageService()
    def select_inventory_manager(self):
        """
        Clicks on the Inventory Manager page
        """
        self.__select_link(self.__admin_console.props['label.inventorymanager'])

    @PageService()
    def select_sensitive_data_analysis(self):
        """
        Clicks on the Sensitive data analysis link
        """
        self.__select_link(self.__admin_console.props['label.gdpr'])

    @PageService()
    def select_request_manager(self):
        """
        Clicks on the request manager link
        """
        self.__select_link(self.__admin_console.props['label.taskmanager'])

    @PageService()
    def select_entity_manager(self, sub_type=0):
        """
        Clicks on the entity manager link

            Args:

                sub_type        (int)       --  Sub type of entity page which needs to be opened.
                                                    Default:0

                                    0   - Custom entity
                                    1   - Classifiers
        """
        self.__select_link(self.__admin_console.props['label.entitymanager'])
        if sub_type == 1:
            self.__admin_console.access_tab(self.__admin_console.props['label.classifiermanager.classifiers'])
            self.__admin_console.wait_for_completion()

    @PageService()
    def select_compliance_search(self):
        """
        Clicks on the compliance search link
        """
        self.__select_link(self.__admin_console.props['label.complianceSearch'])

    @PageService()
    def select_permission_report(self):
        """
        Clicks on Entitlement management link
        """
        self.__select_link(self.__admin_console.props['label.userPermissions'])

    @PageService()
    def select_case_manager(self):
        """
        Clicks on Case Manager link
        """
        self.__select_link(self.__admin_console.props['label.casemanager'])

    @PageService()
    def select_file_storage_optimization(self):
        """
        Clicks on File Storage Optimization link
        """
        self.__select_link(self.__admin_console.props['label.analytics'])

    @PageService()
    def select_entitlement_manager(self):
        """
        Clicks on Entitlement Manager link
        """
        self.__select_link(self.__admin_console.props['label.userPermissions'])

    @PageService()
    def select_sda_getting_started(self):
        """
        Clicks on the Sensitive data analysis link on getting started page
        """
        self.__select_link_getting_started(self.__admin_console.props['label.gdpr'])

    @WebAction()
    def __select_link(self, label):
        """
        Clicks on the link with given text
        Args:
                label (str)  - Link with the given label to be accessed
        """
        self.driver.find_element(By.XPATH, 
            "//h4[contains(text(),'" + label + "')]").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __select_link_getting_started(self, label):
        """
        Clicks on the link with given text
        Args:
                label (str)  - Link with the given label to be accessed
        """
        self.driver.find_element(By.XPATH, 
            "//h3[contains(text(),'" + label + "')]").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def get_component_value(self, comp_id, label):
        """Returns the text of custom HIT component on activate custom reports"""
        return self.driver.find_element(
            By.XPATH, f'//*[@id="{comp_id}"]//h4[text()="{label}"]/following-sibling::h5').text