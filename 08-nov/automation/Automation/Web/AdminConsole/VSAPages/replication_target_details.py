from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the methods that can be done on the Replication targets
details page.


Classes:

    Replicationtargetsdetails() ---> _Navigator() ---> LoginPage --->
    AdminConsoleBase() ---> object()

    Replicationtargetsdetails  --  This class contains the methods for action in
                               Replication targets page and is inherited by other
                               classes to perform VSA realted actions

    Functions:

    edit_replication_target()          --  Edits a replication target with the
                                           specified inputs and proxy

    replication_target_summary()       --  Lists the summary of the replication target
"""
from Web.AdminConsole.Components.panel import PanelInfo
from Web.Common.page_object import WebAction


class ReplicationTargetDetails:
    """
    This class contains all the methods for action in replication targets
    details page
    """

    def __init__(self, admin_console):
        """ """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver

    @WebAction()
    def edit_replication_target(
            self,
            new_target_name,
            new_proxy,
            new_dest_network):
        """
            edits the replication target details:
            new_target_name      -- (str) new name for the replication target
            new_proxy            -- (str) new proxy
            new_dest_network     -- (str) new destination network
        """
        self.__driver.execute_script("window.scrollTo(0,0)")
        if self.__admin_console.check_if_entity_exists("xpath", '//a[contains(text(),"Edit")]'):
            self.__driver.find_element(By.XPATH, '//a[contains(text(),"Edit")]').click()
            self.__admin_console.wait_for_completion()
            self.__admin_console.fill_form_by_id('replicationTargetName', new_target_name)
            self.__driver.find_element(By.XPATH, "//cv-select-proxy").click()
            self.__driver.find_element(By.XPATH, "//cv-select-proxy//div[@class='line-search']/input").send_keys(new_proxy)
            elements = self.__driver.find_elements(By.XPATH, "//cv-select-proxy//div[@class='checkBoxContainer']/div")
            for element in elements:
                if element.find_element(By.XPATH, "./div/label/span").text == " " + new_proxy:
                    element.find_element(By.XPATH, "./div/label/span").click()
            self.__admin_console.wait_for_completion()
            self.__admin_console.select_value_from_dropdown("networkSettingsDestination", new_dest_network)
            self.__driver.find_element(By.XPATH, "//div[@class='button-container']/button[2]").click()
            self.__admin_console.wait_for_completion()
        else:
            raise Exception("There is no Edit option")

    @WebAction()
    def replication_target_summary(self):
        """Lists the summary of the replication target
            Ex: {
                'Destination': 'blrvsavc',
                'VM display name ( Suffix )': '_rep',
                'Destination host': '1.1.1.1',
                'Proxy': 'nish_sp12',
                'Destination network': 'VM Network'
            }
            return details will return the summary
        """
        panel_details = PanelInfo(self.__admin_console)
        return panel_details.get_details()
