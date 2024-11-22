from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the browse and restore page on the WebConsole

Browse is the only class defined in this file

"""
import time
from Web.Common.page_object import WebAction, PageService
from Web.Common.exceptions import CVWebAutomationException
from AutomationUtils import logger
from selenium.webdriver.common.keys import Keys


class LiveBrowse:
    """
    Handles the operations on Browse page of My data application
    """
    def __init__(self, webconsole):
        """Initializes Browse class object"""
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self._log = logger.get_log()

    @WebAction()
    def _click_on_showing_latest_backups(self):
        """
        Selects the template from the template dropdown
        """
        latest_backup = self._driver.find_element(By.XPATH, "//span[@id='timeRangeText']")
        latest_backup.click()

    @WebAction()
    def _click_windows_live_machine_data(self):
        """Click on windows live machine data option"""
        live_machine = self._driver.find_element(By.XPATH, "//a[@class='browseLiveMachine']")
        live_machine.click()

    @WebAction()
    def _click_mac_live_machine_data(self):
        """Click on mac live machine data option"""
        live_machine = self._driver.find_element(By.XPATH, "//a[@class='timeRangeLatestData']")
        live_machine.click()

    @WebAction()
    def _upload_file(self):
        """Uploads a file to webconsole"""
        upload_button = self._driver.find_element(By.XPATH, "//a[@id='uploadLink']")
        upload_file = upload_button.find_element(By.CSS_SELECTOR, 'input[type="file"]')
        upload_button.click()
        return upload_file
        # upload_file.send_keys(file_path)

    @WebAction()
    def _upload_progress_status(self):
        """get upload progress status"""
        ulpoad_status = self._driver.find_element(By.XPATH, "//span[@class='progressStatus']")
        return ulpoad_status.text

    @WebAction()
    def _upload_progress_percentage(self):
        """track the upload progress of file"""
        ulpoad_progress = self._driver.find_element(By.XPATH, "//span[@class='progressPercentage']")
        return ulpoad_progress.text

    @PageService()
    def select_live_machine_data_option(self, os_info):
        """select live machine data option"""
        self._click_on_showing_latest_backups()
        time.sleep(1)
        if os_info.lower() == 'windows':
            self._click_windows_live_machine_data()
        else:
            self._click_mac_live_machine_data()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def upload_file(self, file_list):
        """Uploads a file to webconsole"""
        upload_file = self._upload_file()
        for each_file in file_list:
            self._log.info("Inserting file: %s for upload", each_file)
            upload_file.send_keys(each_file)

    @PageService()
    def track_upload_progress(self):
        """track the upload progress of file"""
        status_text = self._upload_progress_status()
        status_percentage = self._upload_progress_percentage()
        if status_percentage == '(100%)':
            if status_text == 'Upload Completed with errors':
                raise CVWebAutomationException("One or more files failed to upload")
            elif status_text == 'Upload Completed':
                self._log.info('Progress percentage at 100%, No errors reported on GUI')
        else:
            raise CVWebAutomationException("files failed to upload")

    @PageService()
    def refresh_live_browse_data(self):
        """refresh browser to see the changes"""
        self._driver.refresh()

    @WebAction()
    def _click_on_create_folder(self):
        """click on create folder option"""
        create_folder_button = self._driver.find_element(By.XPATH, "//a[@id='createFolder']")
        create_folder_button.click()

    @WebAction()
    def _enter_folder_name(self, folder_name):
        """enter folder name in folder location"""
        folder_location = self._driver.find_element(By.XPATH, "//input[@id='folderLocation']")
        folder_location.send_keys(folder_name)

    @WebAction()
    def _click_on_create_folder_button(self):
        """click on create folder button """
        create_folder = self._driver.find_element(By.XPATH, "//button[contains(text(),'Create Folder')]")
        create_folder.click()

    @PageService()
    def create_folder(self, folder_name):
        """create folder"""
        self._click_on_create_folder()
        self._enter_folder_name(folder_name)
        self._click_on_create_folder_button()

    @WebAction()
    def _click_on_download_button(self):
        """click on download button"""
        download_button = self._driver.find_element(By.XPATH, "//a[@id='downloadLink']")
        download_button.click()

    @PageService()
    def click_on_download_and_watch_for_notifications(self, wait_time=3):
        """click on download button and watch for notifications"""
        self._webconsole.clear_all_notifications()
        self._click_on_download_button()
        count = 1
        while count <= wait_time:
            err_msgs = self._webconsole.get_all_error_notifications()
            if err_msgs:
                raise CVWebAutomationException("Error notification [%s] while download request submitted"
                                               % (err_msgs[0]))
            msgs = self._webconsole.get_all_info_notifications()
            if msgs:
                message = "Download from live machine depends on the size of download, please be patient"
                if msgs[0] or msgs[1] != message:
                    raise CVWebAutomationException("Unexpected notification [%s] while download request submitted"
                                                   % (msgs[1]))
            else:
                raise CVWebAutomationException("Unable to read notification while downloading file or folder")
            self._log.info("Sleeping for {0} seconds".format(10))
            time.sleep(10)
            count = count + 1
