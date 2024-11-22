# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function that can be used to run ad agent for metallic
"""
from time import sleep

from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Hub.constants import HubServices, ADTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Components.dialog import ModalDialog

from Web.AdminConsole.AD.page_ops import check_link_text, check_element, check_parent
from selenium.webdriver.common.by import By

class MetallicAD:

    """class for ad agent on mettalic"""

    def __init__(self, admin_console):
        """
        initial class
        Args:
            admin_console    (AdminConsole): adminconsole object
        """
        self.adminconsole = admin_console
        self.driver = admin_console.driver
        self.dashboard = Dashboard(self.adminconsole, HubServices.ad, ADTypes.aad)
        self.log = admin_console.log
        self.dialog_ = ModalDialog(admin_console)


    @PageService()
    def switch_browse_to_agentview(self):
        """
        switch to aegnt view
        """
        check_link_text(self.driver, "Active Directory").click()
        self.log.info("switch back to agent view page from browse page")

    @PageService()
    def switch_to_ad(self):
        """
        select ad from catalog service page
        """
        headtext = check_element(self.driver,"class", "heading")
        if headtext.text == 'Metallic Service Catalog':
            self.log.debug("metallic service catalog page is displayed, go to ad")
            ad_card = check_element(self.driver,
                                    "tag", "span",
                                    **{"text": "Azure AD and Microsoft AD"})
            check_parent(ad_card).click()
            self.adminconsole.wait_for_completion()
            headtext = check_element(self.driver,"class", "heading")
            if headtext.text == "Active Directory":
                self.log.debug("switch to ad page")
            else:
                self.log.error(f"switch to ad failed, {headtext.text}")

    @PageService()
    def switch_to_hub(self):
        """
        switch to hub dashboard
        """
        self.adminconsole.refresh_page()
        header = check_element(self.driver,'id','cv-header')
        self.log.debug(f"cv header text is {header.text}")
        for _ in header.find_elements(By.TAG_NAME, 'a'):
            link_ = _.get_attribute('href')
            self.log.debug(f"found a link with content {link_}")
            if link_ :
                if link_.startswith("https"):
                    self.log.debug(f'found the dashbaord link {link_}')
                    check_parent(_).click()
                    self.log.info("switch back to hub dashboard")
                    break

    @PageService()
    def create_azuread(self, clientname, clientspage, tcinputs):
        """
        create azure ad app from hub
        Args:
            clientname    (string):    client name
            clientspage    (obj):    ad agent clients page object
            tcinputs        (dict):     test case input file diction
        """
        self.switch_to_ad()
        self.log.debug("click New configuration")
        self.dashboard.click_new_configuration()
        self.adminconsole.wait_for_completion()
        try:
            check_element(self.driver,"tag", "button",
                          **{"text": "Continue"}).click()
            self.log.debug("First time azure ad configuration")
            sleep(30)
        except:
            self.log.debug("First time configure is not show")
        self.adminconsole.wait_for_completion()
        # introduction page
        self.adminconsole.click_button_using_text("Next")
        # configure page
        self.adminconsole.wait_for_completion()
        self.adminconsole.refresh_page()
        self.adminconsole.fill_form_by_id("azureAppName", clientname)
        main_window = self.driver.current_window_handle
        check_element(self.driver, "id", "o365-sign-in-with-msft-onboarding-icon").click() # open ms page
        sleep(20)
        clientspage.aad_creation_auth(tcinputs, main_window)
        self.adminconsole.wait_for_completion()
        # click close and create the app
#        self.dialog_.click_submit()
        check_element(self.driver, "id", "globalAppProceedBtn").click()
        self.adminconsole.wait_for_completion()
        check_element(self.driver, "tag", "button",
                      **{"text" : "Create"}).click()
        self.adminconsole.wait_for_completion()
        self.adminconsole.wait_for_completion()
        self.log.debug(f"azure ad client {clientname} is created")
        # self.adminconsole.access_tab("Overview")
        self.log.debug("swtich to azure ad over view tab")
