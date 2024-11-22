# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Settings page on the AdminConsole

Class:

    Settings()

Functions:

configure_password() -- change password of the current logged in user
register_cloud()     -- register the commserve to the cloud
configure_email()    -- configure email to the smtp server

"""
from selenium.webdriver.common.by import By

from Web.Common.page_object import WebAction
import time


class Settings:
    """
    class for page Settings
    """
    def __init__(self, admin_console):
        self.admin_console = admin_console
        self.driver = self.admin_console.driver
        self.log = self.admin_console.log

    @WebAction()
    def configure_password(self, old_password, new_password):
        """Changes the password of the currently logged in user
            old_password - current password of the user
            new_password - new password to be set for the user
        """
        self.log.info("Changing password for the current user")
        if self.admin_console.check_if_entity_exists("link", "Change password"):
            self.driver.find_element(By.LINK_TEXT, 
                "Change password").click()
            self.admin_console.wait_for_completion()
        self.driver.find_element(By.ID, "oldPassword").clear()
        self.driver.find_element(By.ID, 
            "oldPassword").send_keys(old_password)
        self.driver.find_element(By.ID, "newPassword").clear()
        self.driver.find_element(By.ID, 
            "newPassword").send_keys(new_password)
        self.driver.find_element(By.ID, "confirmPassword").clear()
        self.driver.find_element(By.ID, 
            "confirmPassword").send_keys(new_password)
        self.driver.find_element(By.XPATH, "//form/div[2]/button").click()
        self.admin_console.wait_for_completion()
        time.sleep(10)
        self.driver.find_element(By.LINK_TEXT, "here").click()
        self.admin_console.wait_for_completion()

    @WebAction()
    def register_cloud(self, cloud_email, cloud_password):
        """Registers the commserve to the cloud. it is a one time operation
            cloud_email    - email to login with to register to cloud
            cloud_password - password to login with to register to cloud
        """
        self.log.info("Registering to cloud")
        self.driver.find_element(By.LINK_TEXT, "Register to cloud").click()
        self.admin_console.wait_for_completion()
        self.driver.find_element(By.ID, "cloudEmail").send_keys(cloud_email)
        self.driver.find_element(By.ID, 
            "cloudPassword").send_keys(cloud_password)
        self.driver.find_element(By.XPATH, 
            "//ng-include[3]/div[2]/form/div[2]/button").click()
        self.admin_console.wait_for_completion()

    @WebAction()
    def configure_email(self, smtp_server, smtp_port, sender_email, sender_name):
        """Configures the email settings like smtp server, port and the sender name of the
            commserve
            smtp_server  - address of the smtp server to configure the email with
            smtp_port    - port of the smtp server
            sender_email - email to configure to the smtp server
            sender_name  - name to associate with the email
        """
        self.log.info("Configuring email as " + sender_email)
        self.driver.find_element(By.LINK_TEXT, "Configure email").click()
        self.admin_console.wait_for_completion()
        self.driver.find_element(By.ID, "smtpServer").clear()
        self.driver.find_element(By.ID, "smtpServer").send_keys(smtp_server)
        self.driver.find_element(By.ID, "smtpPort").clear()
        self.driver.find_element(By.ID, "smtpPort").send_keys(smtp_port)
        self.driver.find_element(By.ID, "senderEmail").clear()
        self.driver.find_element(By.ID, 
            "senderEmail").send_keys(sender_email)
        self.driver.find_element(By.ID, "senderName").clear()
        self.driver.find_element(By.ID, "senderName").send_keys(sender_name)
        self.driver.find_element(By.XPATH, 
            "//ng-include/div[2]/form/div[2]/button").click()
        self.admin_console.wait_for_completion()
