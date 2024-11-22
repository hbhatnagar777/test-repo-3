from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Troubleshoot page in admin console

Class:

    Troubleshoot : Provide basic functionality on the page
    CloudSendLog : give different method to select different options on the page

Functions inside Troubleshoot :

    access_by_computers()                        -- selects computer for job request
    access_by_job_id()                           -- selects network output
     access_commcell()                           -- To access commcell
    is_request_submit_success()                  -- check to request is  submitted
    submit()                                     -- To submit request
Functions and class inside CloudSendLog :
class :
    computer_info : different  computer option avilable on webpage to select options
    collection_info : different collection option avilable on webpage to select options
methods:
    get_request_id()                            -- request id for submitted request
    insert_comments()                           -- to insert comments
    select_collection__information()            -- to select different collection information
    select_computer_information()               -- to select different computer information
    select_email_notification()                 -- to select email
    select_output()                             -- to select different output options
    select_staging()                            -- to select staging machine

"""
from selenium.common.exceptions import NoSuchElementException
from AutomationUtils import logger
from selenium.webdriver.support.ui import Select
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.WebConsole.Reports.navigator import CommCellSearch
from enum import Enum


class Troubleshoot:
    """
    Class for cloud troubleshooting
    """

    def __init__(self, webconsole):
        """
        Args:
            webconsole (WebConsole): The webconsole object
        """
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self._log = logger.get_log()
        self._cc_search = CommCellSearch(webconsole)

    @WebAction()
    def _select_by_computers(self):
        """
        selects by computers tab
        """
        self._driver.find_element(By.XPATH, "//label[text()='By Computers']").click()

    @WebAction()
    def _select_by_job_id(self, job_id):
        """
        selects by JOBID tab
        """
        self._driver.find_element(By.XPATH, "//label[text()='By Job ID']").click()
        self._driver.find_element(By.ID, "JOBID").send_keys(job_id)

    @WebAction()
    def _select_remote_wia(self):
        """
        selects by Remote WIA tab
        """
        self._driver.find_element(By.XPATH, "//label[text()='Remote WIA Setup']").click()

    @WebAction()
    def _select_log_streaming(self):
        """
        selects Log Streaming to cloud tab
        """
        self._driver.find_element(By.XPATH, "//label[text()='Log Streaming to Cloud']").click()

    @WebAction()
    def _click_submit(self):
        """
        Click submit button
        """
        self._driver.find_element(By.ID, "sbmtGetLogs").click()

    @WebAction()
    def _read_req_submit_msg(self):
        """Reads the message that comes after request submitted"""
        return self._driver.find_element(By.XPATH, "//span[@class='submt-succs']").text

    @WebAction()
    def _click_here_submit_more_request(self):
        """clicks on click here option to go back to submit more request"""
        self._driver.find_element(By.XPATH, "//a[@class='gl-try-again evadded']").click()

    @WebAction()
    def _click_remote_troubleshooting_icon(self):
        """clicks the remote troubleshooting icon on Commcell Dashboard page"""
        self._driver.find_element(By.XPATH, "//*[@id='troubleShooting']").click()

    @PageService()
    def access_commcell(self, commcell_name):
        """
        Goto Commcell Dashboard page of a particular commcell
        Args:
            commcell_name: name of the commcell to access
        """
        self._webconsole.wait_till_load_complete()
        self._cc_search.access_commcell(commcell_name)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def click_troubleshooting_icon(self):
        """
        Clicks the troubleshooting icon on CC page to go to troubleshooting page
        """
        self._click_remote_troubleshooting_icon()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_by_computers(self):
        """
        access by computers tab
        """
        self._select_by_computers()

    @PageService()
    def access_by_job_id(self, job_id):
        """
        access by Job ID tab
        """
        self._select_by_job_id(job_id)

    @PageService()
    def access_remote_wia(self):
        """
        access Remote WIA setup tab
        """
        self._select_remote_wia()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_log_streaming(self):
        """
        access Log Streaming to cloud tab
        """
        self._select_log_streaming()

    @PageService()
    def submit(self):
        """
        Submit Troubleshoot request
        """
        self._click_submit()
        self._webconsole.wait_till_load_complete()

    def is_request_submit_success(self):
        """Checks if request submit is success"""
        if self._read_req_submit_msg() != 'Your request is submitted successfully.':
            return False
        return True

    @PageService()
    def go_back_to_submit_request(self):
        """Goes back to request submission page"""
        self._click_here_submit_more_request()
        self._webconsole.wait_till_load_complete()


class CloudSendLog(Troubleshoot):
    """
    class for select different options  from cloud
    """

    class computer_info(Enum):
        """ list of computer information available to select """
        CommServe = "commserve"
        MediaAgent = "ma"
        Clients = "cl"
        Client_Groups = "cg"

    class collection_info(Enum):
        """ list of collect information available to select """
        JobResults = "jobresultsbox"
        CSDB = "csdbbox"
        DB_LOGS = "dblogs"
        Other_DB = "otherdbs"
        ProcessDump = "procdump"
        LogFile = "logfilebox"
        Index = "indexbox"
        LogFragement = "logfragbox"

    def get_request_id(self):
        """
         This method track id if it is present
        Returns(str): It return request id for troubleshoot request

        """
        self._driver.refresh()
        self._webconsole.wait_till_load_complete()
        temp = self._driver.find_element(By.ID, "noDataNotificationPanel").text
        request_id = temp.split('Request ID:')[1].split('. ')[0]
        return int(request_id)

    @WebAction()
    def close_popup(self):
        """
              Checks for pop up and closes it if it is present
              """
        try:
            self._driver.find_element(By.ID, "runtimeDialog")
            self._driver.find_element(By.XPATH,
                                      "//button[@class='buttonContents dialogCancel vw-btn vw-btn-default']").click()
            self._webconsole.wait_till_load_complete()
        except NoSuchElementException:
            return

    @WebAction()
    def _select_checked_box_by_data_name(self, data_name):
        """
            selects by xpath
            data_name(str):
            """
        xpath = f"//span[@data-name = '{data_name}']"
        chkbox = self._driver.find_element(By.XPATH, xpath)
        if chkbox.get_attribute('data-state') == 'unchecked':
            self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _select_check_box_by_id(self, id):
        """
            selects by by check box id
             id(str) : check box id
            """
        chkbox = self._driver.find_element(By.ID, id)
        if chkbox.get_attribute('data-state') == 'unchecked':
            self._driver.find_element(By.ID, id).click()

    @WebAction()
    def _deselect_check_box_by_id(self, id):
        """
            deselects by check box id
            id(str) : check box id
            """
        chkbox = self._driver.find_element(By.ID, id)
        if chkbox.get_attribute('data-state') == 'checked':
            self._driver.find_element(By.ID, id).click()

    @WebAction()
    def _select_staging(self, version_of_stage):
        """
            selects by Remote WIA tab
            version_of_stage(str) : Staging name
            """
        self._select_check_box_by_id("csdbbox")
        self._select_check_box_by_id('stagebox')
        element = Select(self._driver.find_element(By.ID, "stageversion"))
        element.select_by_visible_text(version_of_stage)

    @WebAction()
    def _select_index(self):
        """
            select index
        """
        self._select_check_box_by_id("indexbox")

    @WebAction(delay=0)
    def _fill_textbox_by_id(self, element_id, value):
        """
            Fill the value in a text field with id element id.

            Args:
                element_id (str) -- the ID attribute of the element to be filled
                value (str)      -- the value to be filled in the element

            """
        element = self._driver.find_element(By.ID, element_id)
        element.clear()
        element.send_keys(value)

    @WebAction()
    def _fill_textbox_by_id_with_client_list(self, element_id, client_list):
        """
            fill text box with client names separated by comma
        """
        clients = ','.join(client_list)
        clients += ','
        self._fill_textbox_by_id(element_id, clients)

    @PageService()
    def select_computer_information(self, client_list):
        """
         select computer information from web page
            Args:
                client_list (list):  list of clients
            """
        self._select_checked_box_by_data_name("cl")
        self._fill_textbox_by_id_with_client_list("CLL", client_list)
        self._driver.find_element(By.ID, "collectinfo").click()

    @PageService()
    def select_pseudo_clients_vms(self, client_list):
        """
         select pseudo clients and vms from web page
            Args:
                client_list (list):  list of clients
            """
        self._select_checked_box_by_data_name("pcl")
        self._fill_textbox_by_id_with_client_list("PCL", client_list)
        self._driver.find_element(By.ID, "collectinfo").click()

    @PageService()
    def select_collection__information(self, information_list):
        """
              select collection information from web page
            Args:
                information_list (list):  list from Information_list enum
            """
        for each_info in information_list:
            self._select_check_box_by_id(each_info.value)

    @PageService()
    def select_output(self, upload_http=True, save_to_disk=False, chunking=True, chunk_size=512):
        """
              Select different output options
              chunk size should be in range  minimum 64MB and maximum 1048546 MB
            Args:
                upload_http(bool):
                save_to_disk(bool):
                chunking(bool):
                chunk_size(int):
            """
        if not upload_http:
            self._select_check_box_by_id(id="upld")
        if save_to_disk:
            self._driver.find_element(By.XPATH, "//span[@data-value = '13']").click()
        if not chunking:
            self._deselect_check_box_by_id(id="chunk-file-box")
        if chunking and self._driver.find_element(By.ID, "chunk-file-box").get_attribute('data-state') == 'checked':
            self._fill_textbox_by_id("splitFileSize", chunk_size)

    @PageService()
    def select_staging(self, version_of_stage):
        """
           select staging name , Note : To select staging you must have to select CommServe Database
           version_of_stage(str) : Staging name
            """
        self._select_staging(version_of_stage)

    @PageService()
    def select_index(self):
        """
            select index check box
        """
        self._select_index()

    @PageService()
    def select_email_notification(self, also_notify=False, emails=None, crm=False, crm_token=None):
        """
             Select email address and CRM token for notification
            Args:
                also_notify (bool):
                emails (list):          List of email id
                crm (bool):
                crm_token:
            """

        if also_notify:
            self._select_check_box_by_id(id="notifybox")
            temp = ','.join(emails)
            self._fill_textbox_by_id('NMAIL', temp)

        if crm:
            self._select_check_box_by_id(id="crmtoken")
            self._fill_textbox_by_id('CRMT', crm_token)

    @PageService()
    def insert_comments(self, comment):
        """
             Insert comments in comment box
            Args:
                comment(str): comment
            """
        self._fill_textbox_by_id('comments', comment)
