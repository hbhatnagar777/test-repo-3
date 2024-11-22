from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the ClientDetails page on the WebConsole

ClientDetails is the only class defined in this file

"""
import time
from Web.Common.page_object import WebAction, PageService
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from Web.Common.exceptions import CVWebAutomationException
from selenium.webdriver.common.action_chains import ActionChains
from Web.Common.exceptions import CVTimeOutException
from selenium.webdriver.common.keys import Keys
from AutomationUtils import logger


class ClientDetails:
    """
    Handles the operations on ClientDetails page of My data application
    """
    def __init__(self, webconsole):
        """Initializes ClientDetails class object"""
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self._log = logger.get_log()

    @WebAction()
    def _is_backup_running(self):
        """verify currently any backup running on the client"""
        return self._driver.find_element(By.CLASS_NAME, "vw-backup-current").text != ''

    @WebAction()
    def _raise_if_backup_button_not_found(self):
        """verify backup button exists or not"""

        self._driver.find_element(By.ID, "runBackupLink")

    @WebAction()
    def _is_backup_button_ready(self):
        """verify backup button ready or not"""
        if not self._driver.find_element(By.ID, "runBackupLink").text == "Backup Now":
            raise NoSuchElementException("Backup button seem to be not ready")
        return True

    @WebAction()
    def _click_on_backup_button(self):
        """ Click on backup button to initiating backup """
        self._driver.find_element(By.ID, "runBackupLink").click()

    @WebAction()
    def _wait_for_pause_button_visible(self):
        """ Wait for pause button visible"""
        xpath = r"//*/span[@id='pauseResume']/span[@class='vw-text']"
        pause_elemnt = self._driver.find_element(By.XPATH, xpath)
        return pause_elemnt.is_displayed()

    @WebAction()
    def _click_pause_menu_dropdown(self):
        """Click pause menu dropdown opener"""
        xpath = r"//*/span[@id='pauseResume']/span[@class='vw-text']"
        if self._driver.find_element(By.XPATH, xpath).text == 'Pause':
            pause_menu = self._driver.find_element(By.XPATH, xpath)
            pause_menu.click()

    @WebAction()
    def _click_pause_1_hour(self):
        """Click 'pause 1 hour' option from pause menu dropdown"""
        pause_hour = self._driver.find_element(By.XPATH, "//*/a[@class='pause1Hour']")
        pause_hour.click()

    @WebAction()
    def _verify_job_paused(self):
        """verify whether job paused or not"""
        field = self._driver.find_element(By.XPATH, "//label[@id='backupJobPaused']")
        return field.text == "Job Paused"

    @WebAction()
    def _get_job_id(self):
        """Get the job id"""
        return self._driver.find_element(By.XPATH, "//span[@class='jobId']").text

    @WebAction()
    def _click_on_resume_job(self):
        """click on resume button to resume the paused job"""
        xpath = r"//*/span[@id='pauseResume']/span[@class='vw-text']"
        if self._driver.find_element(By.XPATH, xpath).text == 'Resume':
            resume_button = self._driver.find_element(By.XPATH, xpath)
            resume_button.click()

    @WebAction()
    def _is_kill_button_visible(self):
        """ Wait for kill button displayed"""
        try:
            kill_elemnt = self._driver.find_element(By.XPATH, ".//*[@id='kill']/span")
            return kill_elemnt.is_displayed()
        except WebDriverException:
            return False

    @WebAction()
    def _click_kill_button(self):
        """ click on kill button to kill the backup job """
        kill_button = self._driver.find_element(By.XPATH, ".//*[@id='kill']/span")
        kill_button.click()

    @WebAction()
    def _click_on_edit(self):
        """ click on edit button to add the content"""
        click_edit = self._driver.find_element(By.XPATH, "//*/a[@id='changeBackupContentLink']")
        click_edit.click()

    @WebAction()
    def _access_outer_frame(self):
        """
        Switch to outer content frame
        """
        frame = self._driver.find_element(By.CLASS_NAME, "modal-iframe")
        self._driver.switch_to.frame(frame)

    @WebAction()
    def _click_on_custom_path(self):
        """
        click on 'type custom path' option
        """
        custom_path = self._driver.find_element(By.XPATH, "//*[contains(@class,'header-label')]")
        if custom_path.text == '+ Type custom path':
            custom_path.click()

    @WebAction()
    def _add_custom_path(self, file_path):
        """
        Add the custom path and press enter
        """
        custom_path = self._driver.find_element(By.XPATH, "//*[contains(@class,'content-custom-path')]")
        custom_path.send_keys(file_path)
        custom_path.send_keys(Keys.ENTER)

    @WebAction()
    def _mouse_hover(self):
        """
            Performs an action where the mouse hovers over the type custom path
        """
        element = self._driver.find_element(By.XPATH, "//*[contains(@class,'header-label')]")
        hover = ActionChains(self._driver).move_to_element(element)
        hover.perform()

    @WebAction()
    def _click_on_save(self):
        """click on save button """
        save_button = self._driver.find_element(By.XPATH, "//*/a[@id='saveButton']")
        if save_button.text == 'Save':
            save_button.click()

    @WebAction()
    def _click_on_cancel(self):
        """click on cancel button """
        cancel_button = self._driver.find_element(By.XPATH, "//*/a[@id='cancelButton']")
        if cancel_button.text == 'Cancel':
            cancel_button.click()

    @WebAction()
    def _click_on_include_content(self):
        """click on include content button """
        self._driver.find_element(By.XPATH, "//*[@id='contentsLookup']").click()

    @WebAction()
    def _select_browse_content(self, content):
        """click on add / browse content button """
        select_content = self._driver.find_element(By.XPATH, "//*/a[@title = '%s']" %
                                                            str(content))
        select_content.click()
        time.sleep(3)

    @WebAction()
    def _click_on_select(self):
        """click on add content button """
        self._driver.find_element(By.XPATH, "//*[@class='okSaveButton']").click()

    @WebAction()
    def _expand_browse_content_path(self):
        """click on add content button """
        self._driver.find_element(By.XPATH, "//*/span[@class='dynatree-expander']").click()

    @WebAction()
    def _access_inner_frame(self):
        """
        Switch to inner content frame
        """
        self._driver.switch_to.default_content()
        iframe = self._driver.find_elements(By.TAG_NAME, 'iframe')[1]
        self._driver.switch_to.frame(iframe)

    @WebAction()
    def _click_on_exclude_table_id(self):
        """
        click on  exclude files / folders area
        """
        xpath = "//table[@id='exclude-table-id']/thead/tr/td[2]/span"
        client_xpath = self._driver.find_element(By.XPATH, xpath)
        client_xpath.click()

    @WebAction()
    def _add_exclude_file_path(self, file_path):
        """
        add exclude files in input path
        """
        xpath = ".//*[@id='exclude-table-id']/thead/tr/td[2]/span[2]/input"
        custom_path = self._driver.find_element(By.XPATH, xpath)
        custom_path.send_keys(file_path)
        custom_path.send_keys(Keys.ENTER)

    @WebAction()
    def _select_checkbox_for_required_file(self, index):
        """
        check the check box for required files
        """
        xpath = ".//*[@id='localContentList']/td[1]/div"
        checkbox_list = self._driver.find_elements(By.XPATH, xpath)
        checkbox_list[index].click()

    @WebAction()
    def _get_list_of_files_path(self):
        """
        get list of files from content frame
        """
        xpath = ".//*[@id='localContentList']/td[2]"
        objects_list = self._driver.find_elements(By.XPATH, xpath)
        files_list = []
        for each_object in objects_list:
            files_list.append(each_object.text)
        return files_list

    @WebAction()
    def _click_on_deletepath(self, file_type):
        """
        click on delete path
        """
        xpath = ".//*[@id='dialog']/div[%s]/table/thead/tr/th[4]/span"
        remove_file = self._driver.find_element(By.XPATH, xpath % str(file_type))
        remove_file.click()

    @WebAction()
    def _click_to_lock_client(self):
        """
        click to lock the client
        """
        self._driver.find_element(By.XPATH, "//a[@id='lockClient']").click()

    @WebAction()
    def _enter_password(self, password):
        """
        enter the password to lock / unclock the client
        """
        enter_pwd = self._driver.find_element(By.XPATH, "//input[@id='passwordText']")
        enter_pwd.send_keys(password)

    @WebAction()
    def _click_button_ok(self):
        """
        Click on popup dialogue ok
        """
        self._driver.find_element(By.ID, "okButton").click()


    @WebAction()
    def _is_privacy_feature_disabled(self):
        """
        verify privacy feature is diabled or not
        """
        try:
            if self._driver.find_element(By.XPATH, "//a[contains(@class,'unlocked')]"):
                return True
        except Exception as ex:
            self._log.info("privacy feature is enabled [%s]" % str(ex))
            return False

    @PageService()
    def is_backup_running(self):
        """verify currently any backup running on the client"""
        return self._is_backup_running()

    @PageService()
    def click_on_backup_button(self, cloud_direct=False):
        """click on backup button
            Args:
                cloud_direct(boolean)  -- if true it indicates cloud laptop

            Raises:
                Exception if:
                    - failed during execution of module
        """

        self._raise_if_backup_button_not_found()
        if self._is_backup_button_ready():
            if not cloud_direct:
                self._click_on_backup_button()
            else:
                """click on download button and watch for notifications"""
                self._webconsole.clear_all_notifications()
                self._click_on_backup_button()
                message = "Backup submitted successfully"
                count = 1
                wait_time = 3
                while count <= wait_time:
                    err_msgs = self._webconsole.get_all_error_notifications()
                    if err_msgs:
                        raise CVWebAutomationException("Backup job submission for cloud laptop failed with error"
                                                       % (err_msgs[0]))
                    msgs = self._webconsole.get_all_info_notifications()
                    if message in msgs:
                        self._log.info("Cloud Backup job submitted successfully")
                        break
                    else:
                        if msgs:
                            if msgs[0] or msgs[1] != message:
                                raise CVWebAutomationException("Unexpected notification [%s] when backup job submitted"
                                                               % (msgs[1]))
                        else:
                            raise CVWebAutomationException("Unable to read notification while backup job submitted")
                        self._log.info("Sleeping for {0} seconds".format(10))
                        time.sleep(10)
                        count = count + 1

    @PageService()
    def wait_for_pause_button_visible(self, timeout=60):
        """Wait for pause button to be visible"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._wait_for_pause_button_visible() is False:
                time.sleep(1)
            else:
                return True
        raise CVTimeOutException(
            timeout,
            "Timeout occurred while waiting for pause button to click",
            self._driver.current_url
        )

    @PageService()
    def click_pause_button(self):
        """Click on pause button for 1 hour"""
        if self.wait_for_pause_button_visible()is True:
            self._click_pause_menu_dropdown()
            time.sleep(1)
            self._click_pause_1_hour()

    @PageService()
    def wait_for_job_paused(self, timeout=60):
        """verify whether job paused or not"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._verify_job_paused()is False:
                time.sleep(1)
            else:
                return True
        raise CVTimeOutException(
            timeout,
            "Timeout occurred, Backup job is not paused",
            self._driver.current_url
        )

    @PageService()
    def get_job_id(self):
        """Get the job id"""
        job_id = self._get_job_id()
        job_id = job_id.rsplit(sep=':', maxsplit=1)[1].replace(")", '').strip()
        return job_id

    @PageService()
    def click_on_resume_job(self):
        """click on resume button to resume the paused job"""
        self._click_on_resume_job()

    @PageService()
    def wait_for_kill_button_visible(self, timeout=60):
        """Wait for kill button to be displayed"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._is_kill_button_visible() is False:
                time.sleep(0.5)
            else:
                return True
        raise CVTimeOutException(
            timeout,
            "Timeout occurred while waiting for kill button to click",
            self._driver.current_url
        )

    @PageService()
    def click_kill_button(self):
        """click on kill button to kill the backup job"""
        if self.wait_for_kill_button_visible()is True:
            self._click_kill_button()

    @PageService()
    def add_custom_path(self, file_path):
        """add custom path as backup content"""
        self._click_on_edit()
        self._access_outer_frame()
        self._mouse_hover()
        self._click_on_custom_path()
        self._add_custom_path(file_path)
        self._click_on_save()

    @PageService()
    def add_browse_content(self, content):
        """add browse content as backup content"""
        self._click_on_edit()
        self._access_outer_frame()
        self._click_on_include_content()
        self._access_inner_frame()
        self._select_browse_content(content)
        self._click_on_select()
        self._access_outer_frame()
        self._click_on_save()

    @PageService()
    def exclude_custon_content(self, file_path):
        """exclude custom path from backup content"""
        self._click_on_edit()
        self._access_outer_frame()
        self._click_on_exclude_table_id()
        self._add_exclude_file_path(file_path)
        self._click_on_save()

    @PageService()
    def remove_include_files(self, file_path_name):
        """remove the included files from backup content"""
        self._click_on_edit()
        self._access_outer_frame()
        files_list = self._get_list_of_files_path()
        if file_path_name in files_list:
            for index in range(len(files_list)):
                if files_list[index] in file_path_name:
                    self._select_checkbox_for_required_file(index)
            self._click_on_deletepath(1)
            self._click_on_save()
        else:
            self._click_on_cancel()
            self._log.info('[{0}] is not part of content to remove'.format(file_path_name))

    @PageService()
    def remove_exclude_files(self, file_path_name):
        """remove the excluded files from backup content"""
        self._click_on_edit()
        self._access_outer_frame()
        files_list = self._get_list_of_files_path()
        if file_path_name in files_list:
            for index in range(len(files_list)):
                if files_list[index] in file_path_name:
                    self._select_checkbox_for_required_file(index)
            self._click_on_deletepath(2)
            self._click_on_save()
        else:
            self._click_on_cancel()
            self._log.info('[{0}] is not part of content to remove'.format(file_path_name))

    @PageService()
    def enable_privacy_feature(self, password):
        """Enable the privacy feature"""
        if self._is_privacy_feature_disabled():
            self._click_to_lock_client()
            self._enter_password(password)
            self._click_button_ok()

    @PageService()
    def disable_privacy_feature(self, password):
        """Disable the privacy feature"""
        if not self._is_privacy_feature_disabled():
            self._click_to_lock_client()
            self._enter_password(password)
            self._click_button_ok()
