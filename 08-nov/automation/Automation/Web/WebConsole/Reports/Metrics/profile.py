from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""All Profile manipulations goes into this file"""
from time import sleep

from selenium.common.exceptions import WebDriverException
from selenium.webdriver import ActionChains

from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService


class Profile:
    """Class to manage Profile Activities"""
    def __init__(self, webconsole):
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver

    @WebAction()
    def __click_sla_trend_details(self):
        """Clicks details menu of SLA Trend chart"""
        menu = self._driver.find_element(By.XPATH, "//*[@title='SLA Trend']/following-sibling::a[@title='Details']")
        menu.click()

    @WebAction()
    def __click_document_details(self):
        """Clicks details menu of Documents tile"""
        menu = self._driver.find_element(By.XPATH, 
            "//*[@title='Uploaded Documents']/following-sibling::a[@title='Details']")
        menu.click()

    @WebAction()
    def __click_customer_satisfaction_details(self):
        """Clicks details menu of SLA Trend chart"""
        menu = self._driver.find_element(By.XPATH, 
            "//*[@title='Customer Satisfaction']/following-sibling::a[@title='Details']")
        menu.click()

    @WebAction()
    def __click_download_button(self, file):
        """Clicks Download Button"""
        download = self._driver.find_element(By.XPATH, f"//*[@title='{file}']/following-sibling::*/a")
        download.click()

    @WebAction()
    def __hover_over_download(self, file):
        """Hovers over the given file"""
        view = self._driver.find_element(By.XPATH, f"//td[@title='{file}']/ancestor::tr")
        action_chain = ActionChains(self._driver)
        action = action_chain.move_to_element(view)
        action.perform()

    @WebAction()
    def __click_customer_satisfaction_add_button(self):
        """Clicks customer satisfaction add button"""
        add = self._driver.find_element(By.XPATH, "//*[@title='Submit Customer Satisfaction']")
        add.click()

    @WebAction()
    def __enter_notes(self, notes):
        """Enters the given notes in the text area"""
        textarea = self._driver.find_element(By.XPATH, "//*[@id='notes']")
        textarea.send_keys(notes)

    @WebAction()
    def __switch_frame(self):
        """Switches to iframe"""
        frame = self._driver.find_element(By.XPATH, "//*[@class='modal-iframe']")
        self._driver.switch_to.frame(frame)

    @WebAction()
    def __click_submit(self):
        """clicks submit button for customer satisfaction"""
        button = self._driver.find_element(By.XPATH, "//*[@id='okButton']")
        button.click()

    @WebAction()
    def __is_document_upload_icon_visible(self):
        """Checks for the upload icon"""
        try:
            self._driver.find_element(By.XPATH, "//*[@id='uploadLink']")
            return True
        except WebDriverException:
            return False

    @WebAction()
    def __click_new_folder_icon(self):
        """Clicks new folder icon"""
        icon = self._driver.find_element(By.XPATH, "//a[@title='New Folder']")
        icon.click()

    @WebAction()
    def __enter_folder_name(self, name):
        """Enters folder name"""
        textbox = self._driver.find_element(By.XPATH, "//*[@id='folderLocation']")
        textbox.clear()
        textbox.send_keys(name)

    @WebAction()
    def __click_create_folder_button(self):
        """Clicks create folder button"""
        button = self._driver.find_element(By.XPATH, "//button[contains(text(),'Create Folder')]")
        button.click()

    @WebAction()
    def __select_check_box(self, name):
        """Selects the checkbox"""
        checkbox = self._driver.find_element(By.XPATH, 
            f"//*[@title='{name}']/ancestor::tr/td/div[@role='checkbox']")
        checkbox.click()

    @WebAction()
    def __click_more_actions(self):
        """Clicks the more actions button"""
        button = self._driver.find_element(By.XPATH, "//*[@id='moreActionsLink']")
        button.click()

    @WebAction()
    def __click_delete(self):
        """Clicks delete """
        button = self._driver.find_element(By.XPATH, "//*[@id='deleteLink']")
        button.click()

    @WebAction()
    def __click_yes_on_confirmation(self):
        """Clicks yes on confirmation"""
        button = self._driver.find_element(By.XPATH, "//*[.='Yes']")
        button.click()

    @PageService()
    def is_document_upload_icon_visible(self):
        """Returns true if the upload icon is visible"""
        return self.__is_document_upload_icon_visible()

    @PageService()
    def access_customer_satisfaction_report(self):
        """Opens the Customer SatisfactionReport"""
        self.__click_customer_satisfaction_details()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_sla_trend_report(self):
        """Opens the SLA Trend Report"""
        self.__click_sla_trend_details()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def submit_customer_satisfaction(self, notes):
        """Submits customer satisfaction for non commvault users"""
        try:
            self.__click_customer_satisfaction_add_button()
            sleep(5)
            self.__switch_frame()
            # customer satisfaction is not implemented
            self.__enter_notes(notes)
            self.__click_submit()
        except WebDriverException as exception:
            raise CVWebAutomationException(exception)

    @PageService()
    def create_new_folder(self, name):
        """Creates a new folder"""
        self._webconsole.clear_all_notifications()
        self.__click_new_folder_icon()
        self.__enter_folder_name(name)
        self.__click_create_folder_button()
        self._webconsole.wait_till_load_complete()
        sleep(10)
        self._webconsole.get_all_unread_notifications(expected_notifications=["Automation Folder has been created."],
                                                      expected_count=1)

    @PageService()
    def download_file_in_documents(self, file):
        """Downloads the given file"""
        # This PageService should go into the Edge Drive Module. Considering time constraints it has been written here
        # Currently downloads the file only in the top most directory. Directory navigation is not implemented
        self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(1)
        self.__hover_over_download(file)
        sleep(1)
        self.__click_download_button(file)
        self._webconsole.get_all_unread_notifications(expected_notifications=["Submitted request to download document"])
        self._driver.execute_script("window.scrollTo(0, 0);")

    @PageService()
    def delete_folder_in_documents(self, name):
        """Deletes the given folder"""
        self.__click_document_details()
        self._driver.switch_to.window(self._driver.window_handles[-1])
        self._webconsole.wait_till_load_complete()
        try:
            self.__select_check_box(name)
        except WebDriverException:
            self._driver.close()
            self._driver.switch_to.window(self._driver.window_handles[-1])
            raise CVWebAutomationException("No such folder exist")

        self.__click_more_actions()
        self.__click_delete()
        self.__click_yes_on_confirmation()
        self._webconsole.wait_till_load_complete()
        self._driver.close()
        self._driver.switch_to.window(self._driver.window_handles[-1])


