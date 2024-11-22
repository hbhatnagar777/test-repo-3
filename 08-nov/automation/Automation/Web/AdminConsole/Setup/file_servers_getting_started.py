from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to file servers in getting started page
file servers : This class provides methods for file server setup completion

==============

    add_file_server_plan()   -- To add a new file server

    add_file_server_plan()          -- To add a new server plan

    check_file_server_added()       --checks if server is already added

    fs_setup_complete()            -- To run first Backup

"""


from selenium.webdriver.common.keys import Keys

from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Setup.getting_started import GettingStarted
from Web.Common.page_object import (
    PageService
)


class FileServers(GettingStarted):
    """
    Class for file servers getting started page in Admin console

    """
    def __init__(self, driver):
        """
        FileServers Class initialization

        """
        super(FileServers, self).__init__(driver)
        self.plan_obj = None
        self.driver = driver
        self.storage = None

    @PageService()
    def add_file_server_plan(self, plan_name, storage=None):
        """
        Completes the setup of file servers solution if not completed yet
        Returns:

        """
        if not self.plan_obj:
            self.plan_obj = Plans(self.driver)
        self.plan_obj.create_server_plan(plan_name, storage)
        self.log.info("STEP1:Server plan Creation completed.")

    @PageService()
    def add_file_server(self, hostname_list, username, password, plan=None,
                        reboot_if_required=False, go_to_next_step=False):
        """
        Adds a file server during setup completion
        Args:
            hostname_list:List of hoat names to install server
            username(string): username to access the server
            password(string):password of the server
            plan()string):plan to associate to the server
            reboot_if_required(bool): True if server could be rebooted during install
            go_to_next_step(bool):True when step is already completed and should press
                                    only continue

        Returns:None

        """
        if go_to_next_step:
            self.click_button("Continue")
            return
        if self.check_file_server_added():
            self.click_button(self.props['label.addAnotherServer'])
        if hostname_list:
            for hostname in hostname_list:
                self.driver.find_element(By.ID, 'hostName').send_keys(hostname)
                self.driver.find_element(By.ID, 'hostName').send_keys(Keys.RETURN)
        self.fill_form_by_id('fakeusernameremembered', username)
        self.fill_form_by_id('fakepasswordremembered', password)
        if plan:
            self.cv_single_select('Plan', plan)
        if reboot_if_required:
            self.checkbox_select('forceReboot')
        self.submit_form()
        self.wait_for_completion()
        if self.check_file_server_added():
            self.click_button("Continue")

    @PageService()
    def check_file_server_added(self):
        """
        checks if file server is added already
        Returns:true if server is added already

        """
        server_add_status = ""
        if self.check_if_entity_exists("xpath", "//div[@class='margin-top-35-minus ng-scope']/p"):
            server_add_status = self.driver.find_element(By.XPATH, 
                "//div[@class='margin-top-35-minus ng-scope']/p").text
        else:
            if self.check_if_entity_exists("xpath", "//div[@class=list-group-item]"):
                server_add_status = self.driver.find_element(By.XPATH, 
                    "//div[@class='list-group-item']").text
        if server_add_status in ('Server installation started',
                                 self.props['label.serverAlreadyAdded']):
            self.log.info("Server is already added for the solution")
            return True
        return False

    @PageService()
    def fs_setup_complete(self):
        """
        final step of FS solution setup
        Returns:None

        """
        if self.driver.find_element(By.XPATH, 
                "//button[contains(text(),'"\
                                + self.props['action.backupNow'] + "')]").is_displayed():
            self.click_button(self.props['action.backupNow'])
        else:
            raise Exception("backup now option not available during setup completion")
