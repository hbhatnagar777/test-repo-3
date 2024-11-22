from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the common functions or operations that can be performed on SMTPDashboard

"""

from AutomationUtils import logger
import traceback
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

class SMTPDashboard(object):

    """Class for SMTP Dashboard UI related operations"""

    def __init__(self, driver):
        """Initializes the Selenium driver object.
            Args:
                driver  (Object)  --  instance of selenium driver
            Returns:
                object  --  instance of SMTPDashboard class"""
        self.driver = driver
        self.interval = 1
        self.total_time = 600
        self.driver.implicitly_wait(2)
        self.log = logger.get_log()

    def dashboard_login(self,driver,servername,port,username,password):
        """Get login details for SMTPDashboard and perform login operation
            Args:
                driver  (object)  --  selenium driver
                servername (str)  -- SMTPServer machine name
                port (str)        -- SMTPServer port
                username (str)    -- username to login to dashboard
                password (str)    -- password to login to dashboard
           """

        try:
            url ="http://"+servername+":"+port
            driver.get(url)

            username_element=self.driver.find_element(By.XPATH, "//div[2]/form/div[1]/input")
            username_element.clear()
            username_element.send_keys(username)
            time.sleep(2)

            password_element=self.driver.find_element(By.XPATH, "//div[2]/form/div[2]/input")
            password_element.clear()
            password_element.send_keys(password)
            time.sleep(2)

            #Click on Login button

            timeout=5

            self.driver.find_element(By.XPATH, "//div[3]/button").click()

            self.waitForUrl()

        except Exception as e:
            self.log.error('Failed with error: ' + str(e))
            self.log.error('Stack Trace: ' + str(traceback.format_exc()))
            raise e


    def waitForUrl(self):
        """ Wait for the dashboard to load"""
        element_present = EC.presence_of_element_located((By.ID, 'checkboxTrustOffice365Ips'))
        WebDriverWait(self.driver, 10).until(element_present)

    def toggle_trustmsexchange_button(self):
            """ perform operation for toggle/untoggle checkbox for trustMSExchange """
            try:
               time.sleep(4)
               self.log.info("Clicking the toggle button")
               toggle_button_xpath="//*[@id='checkboxTrustOffice365Ips']"
               element=self.driver.find_element(By.XPATH, toggle_button_xpath)

               if element:
                    actions = ActionChains(self.driver)
                    actions.move_to_element(element).perform()
                    element.click()
                    time.sleep(4)
               else:
                  self.log.info("Toggle button not found")
                  raise Exception("Toggle button not found")

               self.log.info("Clicking the save settings button")

               #save settings

               settings_button_xpath="//div[@id=\'_page_setting\']/div[5]/div/button"

               if self.driver.find_element(By.XPATH, settings_button_xpath):
                    self.driver.find_element(By.XPATH, settings_button_xpath).click()
               else:
                  self.log.info("Settings button not found")
                  raise Exception("Save Settings button not found")

               time.sleep(6)

               # Switch the control to alert box and click OK
               assert self.driver.switch_to.alert.text == "Please restart services if required."
               self.driver.switch_to.alert.accept()

               self.log.info("Toggled the button. Restart the services and wait for services to come up")

               time.sleep(4)

               #click on restart service button

               restart_button_xpath="//div[@id=\'_page_setting\']/div[5]/div[2]/button"

               if self.driver.find_element(By.XPATH, restart_button_xpath):
                    self.driver.find_element(By.XPATH, restart_button_xpath).click()

               else:
                  self.log.info("Restart Service button not found")
                  raise Exception("Restart Service button not found")


               # Switch the control to alert box

               time.sleep(5)

               assert self.driver.switch_to.alert.text == "Do you want to restart the service now?"
               self.driver.switch_to.alert.accept()

               #wait for service restart

               time.sleep(20)

            except Exception as e:
               self.log.error('Failed with error: ' + str(e))
               raise e
