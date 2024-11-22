# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
alerts triggered for the AdminConsole

Class:

    TriggeredAlerts())

Functions:

delete_all()          -- deletes all the triggered alets
delete_alert()         -- Deletes all the alerts with the given criteria
dump_alerts_info()     -- prints the alert info for a scpecific machine and alert
all_triggered_alerts() -- prints all the alerts triggered for all the clients
select_alert_type()    -- Displays only the alerts of the given type


"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.AdminConsolePages.Alerts import Alerts
from Web.Common.page_object import WebAction


class TriggeredAlerts(Alerts):
    """
    class for operations that can be performed on the alerts triggered for the AdminConsole
    """
    @WebAction()
    def delete_all(self):
        """Deletes all the triggered alerts
             """
        self.driver.find_element(By.CSS_SELECTOR, 
            "div.ui-grid-selection-row-header-buttons.ui-grid-icon-ok.ng-scope").click()
        self.driver.find_element(By.XPATH, 
            "//a[contains(text(),'Delete')]").click()
        self.wait_for_completion()
        self.driver.find_element(By.XPATH, 
            "//div[3]/button[@text='Yes']").click()

    @WebAction()
    def delete_alert(self, computer_name, alert_info):
        """Deletes all the alerts with the given criteria
            computer_name - name of the computer you want to delete the alert for
            alert_info    - alert you want to delete
        """
        self.driver.find_element(By.ID, "search-field").clear()
        self.driver.find_element(By.ID, "search-field").send_keys(alert_info)
        rows = self.driver.find_elements(By.XPATH, 
            "//cv-grid/div/div[2]/div/div[1]/div[3]/div[2]/div[@class='ui-grid-canvas']/div")
        elements = []
        index = 0
        for row in rows:
            index += 1
            cname = row.find_element(By.XPATH, "./div/div/div[5]/div")
            if cname.text == computer_name:
                ainfo = cname.find_element(By.XPATH, 
                    "./../../div[6]/div/a")
                if ainfo.text == alert_info:
                    # coming out of the loop since by default,
                    # the alerts are displayed by the recently detected time.
                    # So as soon as the first matching pair is found the
                    # loop exits.
                    elements.append(index)
            else:
                continue
        if not elements:
            self.log.info("No such alert was found for the given computer")
        else:
            for elem in elements:
                self.driver.find_element(By.XPATH, 
                    "//cv-grid/div/div[2]/div/div[1]/div[2]/div/div[2]/div/div[" + str(elem) +
                    "]/div/div/div/div/div/div").click()
            self.driver.execute_script("window.scrollTo(0,0)")
            self.driver.find_element(By.LINK_TEXT, "Delete").click()
            self.wait_for_completion()
            self.driver.find_element(By.XPATH, "//div[3]/button[2]").click()
            self.wait_for_completion()

    @WebAction()
    def dump_alerts_info(self, computer_name, alert_info):
        """Dumps the alert info for the latest generated alert,
            of the specified computer name and alert type

            computer_name - name of the computer you want to dump alerts info
            alert_info    - alert you want to dump

            Ex: {
                'Previous Backup Size': '20.46 MB',
                'Storage Policies Used': 'Hawkeye_SP_Dedup',
                'CommCell': 'IRONMAN',
                'Detected Criteria': 'Decrease in Data size by 10 percentage',
                'Subclient': 'IndexBackup',
                'Failed Counts': '0',
                'Type': 'Job Management - Data Protection',
                'Status': 'Succeeded',
                'Current Backup Size': '0 Bytes',
                'Start Time': 'Sun Nov 15 00:00:13 2015',
                'End Time': 'Sun Nov 15 00:00:25 2015',
                'Backup Level': 'Full',
                'User': 'Administrator',
                'Scheduled Time': 'Sun Nov 15 00:00:03 2015',
                'Backup Set': 'defaultBackupSet',
                'Previous Job ID': '8639',
                'Protected Counts': '0',
                'Agent Type': 'Linux File System',
                'Client': 'Hawkeye',
                'Job ID': '8649',
                'Percentage Change': '-100',
                'Detected Time': 'Sun Nov 15 00:00:27 2015'
            }
        """
        self.driver.find_element(By.ID, "search-field").clear()
        self.driver.find_element(By.ID, "search-field").send_keys(alert_info)
        rows = self.driver.find_elements(By.XPATH, 
            "//cv-grid/div/div[2]/div/div[1]/div[3]/div[2]/div[@class='ui-grid-canvas']/div")
        elements = ""
        for row in rows:
            cname = row.find_element(By.XPATH, "./div/div/div[5]/div")
            if cname.text == computer_name:
                ainfo = cname.find_element(By.XPATH, 
                    "./../../div[6]/div/a")
                if ainfo.text == alert_info:
                    # coming out of the loop since by default,
                    # the alerts are displayed by the recently detected time.
                    # So as soon as the first matching pair is found the
                    # loop exits.
                    elements = ainfo
                    break
            else:
                continue
        if not elements:
            raise Exception("No such alert triggered for " + computer_name)
        else:
            elements.click()
            self.wait_for_completion()
            my_dict = {}
            arows = self.driver.find_elements(By.XPATH, 
                "//table[@id='contentTbl']/tbody/tr")
            index = 0  # for row numbering
            for arow in arows:
                if index == 0 or index == 3:
                    index += 1
                    continue
                else:
                    elems_uls = arow.find_elements(By.XPATH, "./td/ul")
                    for elem_ul in elems_uls:
                        data = elem_ul.text
                        lines = data.splitlines()
                        for line in lines:
                            line = line.strip()
                            key, val = line.split(": ", 1)
                            my_dict[key] = val
                    index += 1
            self.log.info(my_dict)
            self.driver.find_element(By.XPATH, 
                "/html/body/div[1]/div/div/a[@class='modal__close-btn']").click()
            self.wait_for_completion()

    @WebAction()
    def all_triggered_alerts(self):
        """Dumps all the alerts triggered for all the clients
            Ex: {
                'Detected Criterion': 'Decrease in Data size by 10 percentage',
                'Detected time': 'Wed Nov 18 00:26:15 2015',
                'Type': 'Job Management - Data Protection',
                'Computer name': 'ADMINCONSOLECB',
                'Alert info': 'Decrease in data size'
            }
        """
        # for finding the rows
        rows = self.driver.find_elements(By.XPATH, 
            "//cv-grid/div/div[2]/div/div[1]/div[3]/div[2]/div[@class='ui-grid-canvas']/div")
        keys = [
            'Detected Criterion',
            'Type',
            'Detected time',
            'Computer name',
            'Alert info']
        for row in rows:
            cols = row.find_elements(By.XPATH, "./div/div/div")
            index = 0  # for skipping first column and last column
            assign_key = 0  # for assigning keys
            alert_info = {}
            for col in cols:
                if index == 0 or index == 6:
                    index += 1
                    continue
                elif index == 5:
                    val = col.find_element(By.XPATH, "./div/a").text
                    alert_info[keys[assign_key]] = val
                    index += 1
                    assign_key += 1
                else:
                    val = col.find_element(By.XPATH, "./div").text
                    alert_info[keys[assign_key]] = val
                    assign_key += 1
                    index += 1
            self.log.info(alert_info)

    # We need to check if all alerts is triggered for the given criteria.
    # dump the alert information as dictionary. ===  DONE
    # 4.      Alerts get last alert triggered for the give client and alert
    # type.Return Type should be dict === DONE

    @WebAction()
    def select_alert_type(self, alert_type):
        """
        Displays only the alerts of the given type
        :param alert_type       (str)   --  type of alert to select
        """
        self.driver.find_element(By.XPATH, 
            "//cv-grid/div/div[1]/div/div/span[1]/a/span[1]").click()
        elements = self.driver.find_elements(By.XPATH, 
            "//cv-grid/div/div[1]/div/div/span[1]/ul/li")
        for elem_li in elements:
            if elem_li.find_element(By.XPATH, "./a/span").text == alert_type:
                elem_li.find_element(By.XPATH, "./a/span").click()
                self.wait_for_completion()
                break
