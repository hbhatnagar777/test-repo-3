from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from time import sleep
from selenium.webdriver.support.ui import Select
from Web.Common.cvbrowser import BrowserFactory


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of xxxxxxxxxxxxxxxx test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "HyperScale Test Case"
        self.browser = None
        self.tcinputs = {
            "url": None,
            "root_pwd": None,
            "advanced_node_settings": None,
            "node1dp": None,
            "node1sp": None,
            "node2dp": None,
            "node2sp": None,
            "node3dp": None,
            "node3sp": None,
            "gateway": None,
            "cluster_network": None,
            "spnetmask": None,
            "dpnetmask": None,
            "hostname": None,
            "cspwd": None,
            "winprodkey": None,
            "ovirteng": None,
        }

    def HSConfig(self, user, pwd):
        """Connect to Hyperscale"""
        try:
            inputs = self.tcinputs
            self.browser.driver.get(inputs['url'])
            self.browser.driver.implicitly_wait(60)
            self.browser.driver.find_element(By.ID, "username").send_keys(user)
            self.browser.driver.implicitly_wait(60)
            self.browser.driver.find_element(By.ID, "password").send_keys(pwd)
            self.browser.driver.implicitly_wait(60)
            self.browser.driver.find_element(By.ID, "login_submit").click()
            self.browser.driver.implicitly_wait(100)
            self.log.info("logged in")
            return True
        except Exception as e:
            raise Exception(str(e))

    def commvault_hyperscale(self):
        """
        To set the details for Commvault Hyperscale
        """
        try:
            inputs = self.tcinputs
            userid_element = self.browser.driver.find_element(By.XPATH, '//div[2]/div[1]/h2').text
            if userid_element == 'Provide Node Information':
                if inputs['advanced_node_settings']:
                    print("opting for advanced node settings")
                    self.browser.driver.find_element(By.XPATH, 
                        "//div[2]/div[1]/div/div[3]/label[contains(text(), 'Click for advanced settings')]").click()
                    self.browser.driver.implicitly_wait(60)
                    sleep(30)
                    self.browser.driver.find_element(By.ID, "root_pwd").clear()
                    self.browser.driver.find_element(By.ID, 
                        "root_pwd").send_keys(inputs['root_pwd'])
                    self.browser.driver.find_element(By.ID, "root_confirm_pwd").clear()
                    self.browser.driver.find_element(By.ID, 
                        "root_confirm_pwd").send_keys(inputs['root_pwd'])

                    #######Fill details on Node 1#############
                    self.browser.driver.find_element(By.ID, "node-tab-1").click()
                    self.browser.driver.find_element(By.ID, "eno3").click()
                    self.browser.driver.find_element(By.ID, "ip-input").clear()
                    self.browser.driver.find_element(By.ID, "ip-input").send_keys(inputs['node1dp'])
                    self.browser.driver.implicitly_wait(30)
                    self.browser.driver.find_element(By.ID, "netmask-input").clear()
                    self.browser.driver.find_element(By.ID, 
                        "netmask-input").send_keys(inputs['dpnetmask'])
                    self.browser.driver.implicitly_wait(30)
                    select_element = Select(
                        self.browser.driver.find_element(By.ID, "network-type-input"))
                    select_element.select_by_index(1)
                    self.browser.driver.find_element(By.ID, "eno3").click()
                    self.browser.driver.implicitly_wait(60)
                    self.browser.driver.find_element(By.ID, "eno4").click()
                    self.browser.driver.find_element(By.ID, "ip-input").clear()
                    self.browser.driver.find_element(By.ID, "ip-input").send_keys(inputs['node1sp'])
                    self.browser.driver.implicitly_wait(30)
                    self.browser.driver.find_element(By.ID, "netmask-input").clear()
                    self.browser.driver.find_element(By.ID, 
                        "netmask-input").send_keys(inputs['spnetmask'])
                    self.browser.driver.implicitly_wait(30)
                    select_element = Select(
                        self.browser.driver.find_element(By.ID, "network-type-input"))
                    select_element.select_by_index(4)
                    self.browser.driver.find_element(By.ID, "eno4").click()

                    #######Fill details on Node 2#############
                    self.browser.driver.find_element(By.ID, "node-tab-2").click()
                    self.browser.driver.find_element(By.ID, "eno3").click()
                    self.browser.driver.find_element(By.ID, "ip-input").clear()
                    self.browser.driver.find_element(By.ID, "ip-input").send_keys(inputs['node2dp'])
                    self.browser.driver.implicitly_wait(30)
                    self.browser.driver.find_element(By.ID, "netmask-input").clear()
                    self.browser.driver.find_element(By.ID, 
                        "netmask-input").send_keys(inputs['dpnetmask'])
                    self.browser.driver.implicitly_wait(30)
                    select_element = Select(
                        self.browser.driver.find_element(By.ID, "network-type-input"))
                    select_element.select_by_index(1)
                    self.browser.driver.find_element(By.ID, "eno3").click()
                    self.browser.driver.implicitly_wait(60)
                    self.browser.driver.find_element(By.ID, "eno4").click()
                    self.browser.driver.find_element(By.ID, "ip-input").clear()
                    self.browser.driver.find_element(By.ID, "ip-input").send_keys(inputs['node2sp'])
                    self.browser.driver.implicitly_wait(30)
                    self.browser.driver.find_element(By.ID, "netmask-input").clear()
                    self.browser.driver.find_element(By.ID, 
                        "netmask-input").send_keys(inputs['spnetmask'])
                    self.browser.driver.implicitly_wait(30)
                    select_element = Select(
                        self.browser.driver.find_element(By.ID, "network-type-input"))
                    select_element.select_by_index(4)
                    self.browser.driver.find_element(By.ID, "eno4").click()

                    #######Fill details on Node 3#############
                    self.browser.driver.find_element(By.ID, "node-tab-3").click()
                    self.browser.driver.find_element(By.ID, "eno3").click()
                    self.browser.driver.find_element(By.ID, "ip-input").clear()
                    self.browser.driver.find_element(By.ID, "ip-input").send_keys(inputs['node3dp'])
                    self.browser.driver.implicitly_wait(30)
                    self.browser.driver.find_element(By.ID, "netmask-input").clear()
                    self.browser.driver.find_element(By.ID, 
                        "netmask-input").send_keys(inputs['dpnetmask'])
                    self.browser.driver.implicitly_wait(30)
                    select_element = Select(
                        self.browser.driver.find_element(By.ID, "network-type-input"))
                    select_element.select_by_index(1)
                    self.browser.driver.find_element(By.ID, "eno3").click()
                    self.browser.driver.implicitly_wait(60)
                    self.browser.driver.find_element(By.ID, "eno4").click()
                    self.browser.driver.find_element(By.ID, "ip-input").clear()
                    self.browser.driver.find_element(By.ID, "ip-input").send_keys(inputs['node3sp'])
                    self.browser.driver.implicitly_wait(30)
                    self.browser.driver.find_element(By.ID, "netmask-input").clear()
                    self.browser.driver.find_element(By.ID, 
                        "netmask-input").send_keys(inputs['spnetmask'])
                    self.browser.driver.implicitly_wait(30)
                    select_element = Select(
                        self.browser.driver.find_element(By.ID, "network-type-input"))
                    select_element.select_by_index(4)
                    self.browser.driver.find_element(By.ID, "eno4").click()
                    self.log.info("Network details furnished")
                    #######Yet to continue #############
                    self.browser.driver.find_element(By.ID, "submit_step").click()
                    sleep(30)
                    self.browser.driver.find_element(By.XPATH, 
                        "//div[1]/div/div/form/div[3]/button[2][@id='submit_step']").click()
                    self.browser.driver.implicitly_wait(200)
                    sleep(300)
                    self.log.info("CommVault HyperScale")
                else:
                    self.log.info("not opting for advanced node settings")
            return True

        except Exception as e:
            raise Exception(str(e))

    def commserv_info(self):
        """
        To set the details for CommServ
        """
        inputs = self.tcinputs
        self.log.info("Configuring Network was successful")

        if self.browser.driver.find_element(By.ID, "clusterInfoError"):
            # if
            # self.browser.driver.find_element(By.XPATH, "div[1]/div/div/form/div[2]/div[3]/h2[contains(text(),'CommServe
            # information'])"):
            self.log.info("Inputs for CommServ..")
            self.browser.driver.find_element(By.ID, "hostname").clear()
            self.browser.driver.find_element(By.ID, "hostname").send_keys(inputs['hostname'])

            self.browser.driver.find_element(By.ID, "pwd").clear()
            self.browser.driver.find_element(By.ID, "pwd").send_keys(inputs['cspwd'])

            self.browser.driver.find_element(By.ID, "confirm_pwd").clear()
            self.browser.driver.find_element(By.ID, "confirm_pwd").send_keys(inputs['cspwd'])

            self.browser.driver.find_element(By.ID, "window_product").clear()
            self.browser.driver.find_element(By.ID, 
                "window_product").send_keys(inputs['winprodkey'])

            self.browser.driver.find_element(By.ID, "virtual_engine").clear()
            self.browser.driver.find_element(By.ID, "virtual_engine").send_keys(inputs['ovirteng'])

            self.browser.driver.implicitly_wait(60)

            self.browser.driver.find_element(By.ID, "submit_step").click()

            self.browser.driver.implicitly_wait(60)
            print("commverse_info")
            sleep(3600)
            if self.browser.driver.find_element(By.XPATH, '//div/div/div[1]/div[1]/div'):
                warning = self.browser.driver.find_element(By.XPATH, 
                    '//div/div/div[1]/div[1]/div').text
                if str(warning) == 'HyperScale configuration completed with warnings.':
                    self.log.info(str(warning))
                    return True
            elif self.browser.driver.find_element(By.XPATH, '//div/div/div[1]/div[2]/div'):
                success = self.browser.driver.find_element(By.XPATH, 
                    '//div/div/div[1]/div[2]/div').text
                if str(success) == 'HyperScale configuration completed successfully!':
                    self.log.info(str(success))
                    return True
            else:
                print("Could not find the Hyperscale configuration page")
                return False
        else:
            return False

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing testcase")

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()

            self.log.info(
                "-------------------Start of the case----------")

            if self.HSConfig('root', 'cvadmin'):
                self.log.info("Hello")
                if self.commvault_hyperscale():
                    if self.commserv_info():
                        self.log.info('completed')
                        self.browser.driver.close()
                        self.browser.driver.quit()
            self.log.info("----------------------End of the case------------------")

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
