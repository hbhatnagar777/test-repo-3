from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
upload page on the WebConsole

Upload is the only class defined in this file

Upload:
    __init__()              -- Initializes the upload class object
    _select_template()      -- Selects the template from the template dropdown
    _select_policy()        -- Selects the policy from the policy dropdown
    _submit_upload()        -- Clicks on the submit button to upload a file
    _myuploads_tab()        -- Switches to the my uploads tab on upload page
    _choose_file()          -- Chooses the file to upload
    _set_tag_name()         -- Sets the tag name for the file to be uploaded
    _get_upload_status()    -- Gets the status of the file uploaded
    upload()                -- Uploads a file from webconsole
    get_upload_status()     -- Gets the status of the file uploaded

"""
from AutomationUtils import logger, config
from Server import serverutils
from Web.Common.page_object import WebAction, PageService

_CONFIG = config.get_config()
_MONITORING_CONFIG = serverutils.get_logmonitoring_config()


class Upload(object):
    """
    Handles the operations on Upload page of Log Monitoring application
    """
    def __init__(self, webconsole):
        """Initializes Upload class object"""
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver
        self._log = logger.get_log()

    @WebAction()
    def _select_template(self):
        """
        Selects the template from the template dropdown
        """
        self._driver.find_element(By.XPATH, r"//select[@id = 'templateList']").click()
        self._driver.find_element(By.XPATH, 
            r"//select[@id = 'templateList']/option[text() = 'Simple Text Template']").click()

    @WebAction()
    def _select_policy(self, policy_name):
        """
        Selects the policy from the policy dropdown
        """
        self._driver.find_element(By.XPATH, r"//select[@id = 'policyList']").click()
        self._driver.find_element(By.XPATH, 
            r"//select[@id = 'policyList']/option[text() = '"+policy_name+"']").click()

    @WebAction()
    def _submit_upload(self):
        """
        Clicks on the submit button to upload a file
        """
        self._driver.find_element(By.XPATH, r"//input[@id = 'upload-files-submit']").click()

    @WebAction()
    def _myuploads_tab(self):
        """
        Switches to My Uploads tab on the upload page
        """
        self._driver.find_element(By.XPATH, r"//li[@id = 'myUploadsTab']").click()

    @WebAction()
    def _choose_file(self, file_path):
        """
        Choose the file to be uploaded
        Args:
             file_path: path of the file

        """
        self._driver.find_element(By.XPATH, r"//input[@id = 'uploadLink']").send_keys(file_path)

    @WebAction()
    def _set_tag_name(self):
        """Sets the tag name for the file to be uploaded"""
        self._driver.find_element(By.XPATH, 
            r"//input[@id = 'uploadTag']").send_keys(_MONITORING_CONFIG.TAG_NAME)

    @WebAction()
    def _get_upload_status(self, tag_name):
        """
        Gets the status of the file uploaded through web console

        Args:
            tag_name: tag name given for the file uploaded

        Example:
            "tag1"
        """
        status = None
        div_elem = self._driver.find_element(By.XPATH, 
            r"//div[@class='upload-table vw-data-table clearfix vw-start-hidden']")
        ul_elements = div_elem.find_elements(By.XPATH, 
            r".//ul[@class='table-row upload-set vw-data-row']")
        for ul_elem in ul_elements:
            li_elements = ul_elem.find_elements(By.XPATH, ".//li")
            for li_elem in li_elements:
                if li_elem.text == tag_name:
                    status = li_elem.find_element(By.XPATH, "./following-sibling::li").text
                    break
        return status

    @PageService()
    def upload(self, file_path, policy_name):
        """
        Uploads a file from the web console
        """
        self._choose_file(file_path)
        self._webconsole.wait_till_load_complete()
        self._set_tag_name()
        self._select_template()
        self._select_policy(policy_name)
        self._submit_upload()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def get_upload_status(self):
        """
        Gets the status of the file uploaded through web console
        """
        self._myuploads_tab()
        self._webconsole.wait_till_load_complete()
        return self._get_upload_status(_MONITORING_CONFIG.TAG_NAME)
