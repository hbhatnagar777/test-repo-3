# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the Laptops page in EDGE Mode

EdgeMain:

    navigate_to_client_settings_page  -- It navigate to the settings page of the given laptop in edgmode
    
    navigate_to_client_restore_page   --  It navigate to the Restore page of the given laptop in Edgemode
    
    get_client_names()                -- It returns all the client names from listing page in edgemode
    
    get_client_data()                 -- It returns all the details from listing page for given client

EdgeSettings:

    is_backup_running()               -- verify currently any backup running or not from client details page
    
    click_on_backup_button()          -- this method trigger backup from settings page for v1 laptop
    
    click_on_backup_button_for_v2()   -- this method trigger backup from setting page for v2 laptop
    
    resume_backup_job()               -- it resume the backup job from laptop details page
    
    wait_for_kill_button_visible()    -- it wait for the kill button visible after job submitted
    
    kill_backup_job()                 -- it kill the backup job
    
    wait_for_job_paused()             -- it wait for the backup job to be paused
    
    wait_for_pause_button_visible()   -- it will wait for pause button visible after job submitted
    
    click_suspend_button()            -- click on suspend button when job running
    
    add_client_backup_content()       -- This method is used to add backup content from edit backup content tile
    
    add_client_exception_content()    -- This method is used to add exception as content from edit backup content tile
    
    remove_backup_content()           -- Remove the given backup content from backup tile
    
    remove_exclude_content()          -- Remove the given exclude content from backup tile

EdgeRestore:
   
    track_upload_progress()          --  This method is used to track the progress of the upload file
     
    upload_file_in_livebrowse()      --  This method used to upload the files in live browse
    
    create_folder()                  --  create the folder in live browse          

    browse_and_restore()             --  it browse and restore the data from given path

    select_deleted_items_in_edgemode()   -- This method is used to select the deleted items in egemode
    
EdgeShares:

    create_private_share                 --  Method used to Create private shares for laptop clients
     
    create_public_share                  --  Method to Create public shares for laptop clients 
    
    navigate_to_webconsole_shares_page   --  This method navigates to shares page in webconsole

    read_shared_by_me_data               --  This method is used to read all data from shared by me tab
    
    read_shared_with_me_data             --  This method is used to read all data from shares with me tab
    
    delete_private_share                 --  This method is used to delete the shares as owner
    
   __check_filetype_based_on_extension   --  it identifies the file extension and group the file types based 
                                             on extension and which has same tag while previewing
   
    verify_file_preview                  --  This method is used to verify the preview of the file
    
    verify_download_from_preview         -- This method is used to verify the downloads from preview of the file

"""
import time
import os
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from AutomationUtils import logger
from Web.Common.page_object import (WebAction, PageService)
from Web.Common.exceptions import CVWebAutomationException,CVWebNoData,CVTimeOutException
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.panel import RPanelInfo, RModalPanel
from Web.AdminConsole.Components.core import Checkbox
from selenium.webdriver.common.keys import Keys


class EdgeMain:
    """
    Class for Laptops page in Edgemode
    """

    def __init__(self, admin_page):
        """ Initialize the React table object

                Args:

                   admin_page      (obj)       --  Admin console class object

        """
        self.__admin_console = admin_page
        self.__driver = admin_page.driver
        self.__navigator = admin_page.navigator
        self.__admin_console._load_properties(self)
        self.log = logger.get_log()
        self._xpath = "//div[contains(@class,'page-container')]//child::div[@class='details']"
        
    @WebAction()
    def __scroll_to_element(self, element):
        """Scrolls to element position"""
        self.__driver.execute_script("arguments[0].scrollIntoView();", element)

    @WebAction()
    def __scroll_reset(self):
        """Scrolls back to top left default position"""
        self.__admin_console.scroll_into_view(self._xpath + "//div[contains(@class,'nameAndActions')][1]")
    
    @PageService()
    def __get_clients_list(self):
        """Read all client names from page"""
        clients_xp = "//div[contains(@class,'nameAndActions')]"
        clientrows = self.__driver.find_elements(By.XPATH, self._xpath + clients_xp)
        client_names = []
        for row in clientrows:
            self.__scroll_to_element(row)
            if row.is_displayed() and row.text != '':
                client_names.append(row.text)
        self.__scroll_reset()
        return client_names
    
    @WebAction()
    def __get_column_data(self):
        """Read all clients column data from laptop page"""
        clients_xp = "//div[contains(@class,'columns')]/div"
        rows = self.__driver.find_elements(By.XPATH, self._xpath + clients_xp)
        cloumns_info = []
        for each_row in rows:
            self.__scroll_to_element(each_row)
            cloumns_info.append(each_row)
        self.__scroll_reset()
        return cloumns_info
    
    @WebAction()
    def __get_client_restore_buttons(self):
        """Read all clients restore buttons info from page"""
        clients_xp = "//button[@aria-label='Restore']"
        button_object = self.__driver.find_elements(By.XPATH, self._xpath + clients_xp)
        restore_buttons_list = []
        for each_object in button_object:
            self.__scroll_to_element(each_object)
            restore_buttons_list.append(each_object)
        self.__scroll_reset()
        return restore_buttons_list

    @WebAction()
    def __get_client_settings_buttons(self):
        """Read all client settings buttons info from page"""
        clients_xp = "//button[@aria-label='Settings']"
        button_object = self.__driver.find_elements(By.XPATH, self._xpath + clients_xp)
        settings_buttons_list = []
        for each_object in button_object:
            self.__scroll_to_element(each_object)
            settings_buttons_list.append(each_object)
        self.__scroll_reset()
        return settings_buttons_list    
    
    def __get_clients_info_list(self):
        """Get all clients info present from laptops page in edgemode"""
        clients_list = self.__get_clients_list()
        clients_info = self.__get_column_data()
        restore_buttons_list = self.__get_client_restore_buttons()
        settings_buttons_list = self.__get_client_settings_buttons()
        sla_status=[]
        nextbackup_time=[]
        lastbackup_size=[]
        Lastjob_status=[]
        lastbackup_time=[]
        client_info_list=[]
        
        for column_data in clients_info:
            if "SLA status" in str(column_data.text):
                sla_status.append(str(column_data.text).split("SLA status\n")[1])
            elif "Next backup time" in str(column_data.text):
                nextbackup_time.append(str(column_data.text).split("Next backup time\n")[1])

            elif "Last backup size" in str(column_data.text):
                lastbackup_size.append(str(column_data.text).split("Last backup size\n")[1])

            elif "Last job status" in str(column_data.text):
                Lastjob_status.append(str(column_data.text).split("Last job status\n")[1])
           
            elif "Last backup time" in str(column_data.text):
                lastbackup_time.append(str(column_data.text).split("Last backup time\n")[1])
                
        file_cat = zip(clients_list, 
                       restore_buttons_list, 
                       lastbackup_time, 
                       Lastjob_status, 
                       lastbackup_size,
                       nextbackup_time,
                       sla_status,
                       settings_buttons_list)
        for each_item in file_cat:
            temp_dict = {'clientName': '', 'RestoreButton': '', 'Last backup time': '', 'Last job status': '', 'Last backup size': '',
                      'Next backup time': '', 'SLA status': '', 'SettingsButton': ''}
            temp_dict['clientName'] = each_item[0]
            temp_dict['RestoreButton'] = each_item[1]
            temp_dict['Last backup time'] = each_item[2]
            temp_dict['Last job status'] = each_item[3]
            temp_dict['Last backup size'] = each_item[4]
            temp_dict['Next backup time'] = each_item[5]
            temp_dict['SLA status'] = each_item[6]
            temp_dict['SettingsButton'] = each_item[7]
            client_info_list.append(temp_dict)
        return client_info_list

    @PageService()
    def navigate_to_client_settings_page(self, client_name):
        """Navigate to settings page from laptop listing page"""
        client_info = self.__get_clients_info_list()
        for each_client_row in client_info:
            if client_name.lower() == each_client_row['clientName'].lower():
                setting_button= each_client_row['SettingsButton']
                setting_button.click()
                break
        self.__admin_console.wait_for_completion()

    @PageService()
    def navigate_to_client_restore_page(self, client_name):
        """Navigate to Restore page from laptop listing page"""
        self.__navigator.navigate_to_devices_edgemode()
        client_info = self.__get_clients_info_list()
        for each_client_row in client_info:
            if client_name.lower() == each_client_row['clientName'].lower():
                restore_button= each_client_row['RestoreButton']
                restore_button.click()
                break
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_client_names(self):
        """Get all client names from laptop page in edge mode"""
        client_names = self.__get_clients_list()
        if not len(client_names):
            raise CVWebNoData('Laptop page not showing any clients')
        return client_names

    @PageService()
    def get_client_data(self, client_name):
        """return all clients data as list of dictionary"""
        clients_info = self.__get_clients_info_list()
        for client_row in clients_info:
            if client_name == client_row['clientName']:
                client_row.pop('RestoreButton')
                client_row.pop('SettingsButton')
                return client_row
        
class EdgeSettings():
    """client settings page in edgemode"""

    def __init__(self, admin_page):
        """ Initialize the edge settings page object

                Args:

                   admin_page      (obj)       --  Admin console class object

        """
        self.__admin_console = admin_page
        self.__driver = admin_page.driver
        self.__rmodelpanel= RModalPanel(admin_page)
        self.__checkbox = Checkbox(admin_page)
        self.__admin_console._load_properties(self)
        self.__content_panel_xpath = "//h3[contains(., '{0}')]//ancestor::div[@class='folders-container']"
        self.log = logger.get_log()
    
    @WebAction()
    def __is_backup_running(self):
        """verify currently any backup running on the client"""
        xpath = "//div[@class='jobDetails']/child::p[normalize-space()='Status Running']" 
        if self.__admin_console.check_if_entity_exists("xpath", xpath):
            return True
        return False
    
    @WebAction()
    def __click_on_suspend_button(self, os_type):
        """
        click on suspend button from laptop details page
        """
        if os_type!="Windows":
            time.sleep(10)
        xpath = "//div[@aria-label='Suspend job']"
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __click_on_1hour_option(self):
        """
        click on 1 hour suspend option from laptop details page
        """
        self.__driver.find_element(By.XPATH, "//li[contains(.,'1 hour')]").click()
                
    @WebAction()
    def __click_on_kill_button(self):
        """
        click on kill button 
        """
        self.__driver.find_element(By.XPATH, "//button[@title='Kill job']").click()
        
    @WebAction()
    def __job_status_from_backuptile(self, timeout=60):
        """
        Read job status from backup panel
        """
        xpath = "//div[@class='jobDetails']/child::p[normalize-space()='Status Suspended']"
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.__admin_console.check_if_entity_exists("xpath", xpath):
                job_status = self.__driver.find_element(By.XPATH, xpath).text
                return job_status
            else:
                time.sleep(1)
                    
        raise Exception("backup status is not showing as suspended")
    
    @WebAction()
    def __click_on_resume_button(self):
        """
        click on resume button 
        """
        self.__driver.find_element(By.XPATH, "//button[@title='Resume job']").click()

    @WebAction()
    def __wait_for_pause_button_visible(self):
        """ Wait for pause button visible"""
        xpath = "//button[@aria-label='Suspend job']"
        pause_elemnt = self.__driver.find_element(By.XPATH, xpath)
        return pause_elemnt.is_displayed()
    
    @WebAction()
    def __is_kill_button_visible(self):
        """ Wait for kill button displayed"""
        try:
            kill_elemnt = self.__driver.find_element(By.XPATH, "//button[@title='Kill job']")
            return kill_elemnt.is_displayed()
        except CVWebAutomationException:
            return False
    
    @WebAction()
    def __scroll_to_element(self, element):
        """Scrolls to element position"""
        self.__driver.execute_script("arguments[0].scrollIntoView();", element)
    
    @WebAction()
    def __get_all_content_elements(self):
        """get all backup content elements from edit backup content modal"""
        xpath = "//div [@class='folders-container']//li[contains(@class,'folder-item')]"
        all_content_elem = self.__driver.find_elements(By.XPATH, xpath)
        return all_content_elem
        
    @WebAction()
    def __get_all_button_elements(self):
        """get all backup content remove buttons from edit backup content modal"""
        xpath = "//div [@class='folders-container']//li[contains(@class,'folder-item')]"
        buttonxp = xpath + '//child::button'
        all_button_elem = self.__driver.find_elements(By.XPATH, buttonxp)
        return all_button_elem 
    
    @WebAction(delay=0)
    def __remove_selected_content(self, content_elem, button_elem):
        """remove the given content from edit backup content tile"""
        self.__admin_console.mouseover_and_click(content_elem, button_elem)
    
    @WebAction()
    def __click_button_on_action_list(self, text):
        """Methd to click on a button inside action list"""
        self.__driver.find_element(By.XPATH, f"//*[@id='action-list']//button[contains(.,'{text}')]").click()
        
    @WebAction()
    def __add_backup_content(self, content, node_name):
        """Method to add content"""
        self.__click_button_on_action_list('Browse')
        self.__rmodelpanel.collapse_treeview_node(node_name)
        for each_item in content:
            self.__checkbox.check(label=each_item)
            self.__admin_console.wait_for_completion()
        self.__edit_backup_save_button(index=1)

    @WebAction()
    def __fill_custom_path(self, panel_name, custom_path):
        """Method to fill custom path"""
        panel_xpath = self.__content_panel_xpath.format(panel_name)
        input_box = panel_xpath + "//input[contains(@id, 'CustomPath')]"
        self.__driver.find_element(By.XPATH, input_box).send_keys(custom_path)
        self.__driver.find_element(By.XPATH, input_box + '//following-sibling::button').click()
        
    @WebAction()
    def __add_custom_path(self, panel_name, custom_paths):
        """Method to add custom path"""
        self.__click_button_on_action_list('Custom path')
        for custom_path in custom_paths:
            self.__fill_custom_path(panel_name, custom_path)
            
    @WebAction()
    def __access_exclude_tab(self):
        """access the exclude tab from edit backup content"""
        xpath = "//div[contains(@class,'tabs-actions-bar')]//span[contains(.,'Exclude')]"
        self.__driver.find_element(By.XPATH, xpath).click()
        self.__admin_console.wait_for_completion()
    
    @WebAction()
    def __click_on_add_button(self):
        """ Click on Add button from Edit backup content panel"""
        xpath = "//div[text()='Add']/ancestor::div[contains(@class, 'panel-actions')]"
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __edit_backup_save_button(self, index=0):
        """Click on save button from the edit backup content panel
            Args:
                index(number)   : -- index 1 is for save button on "add content" modal panel
                                  -- index 0 is for save button from "Edit backup content " modal panel 
                
        """
        elems = self.__driver.find_elements(By.XPATH, 
            f"//div[contains(@class, 'mui-modal-footer')]/descendant::button/div[text()='Save']")
        elems[index].click()
    
    @PageService()
    def is_backup_running(self):
        """verify currently any backup running on the client"""
        self.__driver.refresh()
        self.__admin_console.wait_for_completion()
        return self.__is_backup_running()
    
    @PageService()
    def click_on_backup_button(self, wait=True):
        """Method to click on backup now button in edgemode as enduser
    
        Returns:
            job_id (id)   -- job id
    
        Raises:
            Exception
    
                if there is an error message after submitting the request

        """
        self.__admin_console.click_button(value='Backup now', wait_for_completion=False)
        job_id = self.__admin_console.get_jobid_from_popup(wait_time=5)
        if wait:
            self.__admin_console.wait_for_completion()
        if not job_id:                             
            raise CVWebAutomationException("Unable to read jobid from popup")
        return job_id

    @PageService()
    def click_on_backup_button_for_v2(self):
        """Method to click on backup now button in edgemode as enduser for v2 laptop
        Raises:
            Exception
    
                if there is an error message after submitting the request

        """
        self.__admin_console.click_button(value='Backup now', wait_for_completion=False)
        notification = self.__admin_console.get_notification(wait_time=0)
        self.__admin_console.wait_for_completion()
        if 'Backup job started successfully' not in notification:                             
            raise CVWebAutomationException("Notification is not showing correctly when backup triggered for v2")
    
    @PageService()
    def resume_backup_job(self):
        """
        resume the backup job
 
        """
        self.__click_on_resume_button()
        self.log.info("Resumed the backup job successfully")

    @PageService()
    def wait_for_kill_button_visible(self, timeout=60):
        """Wait for kill button to be displayed"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.__is_kill_button_visible() is False:
                time.sleep(0.5)
            else:
                return True
        raise CVTimeOutException(
            timeout,
            "Timeout occurred while waiting for kill button to click",
            self.__driver.current_url
        )

    @PageService()
    def kill_backup_job(self):
        """
        kill the backup job 
 
        """
        if self.wait_for_kill_button_visible()is True:
            self.__click_on_kill_button()
        
    @PageService()
    def wait_for_job_paused(self, timeout=100):
        """verify whether job paused or not"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if  self.__job_status_from_backuptile()is False:
                time.sleep(1)
            else:
                return True
        raise CVTimeOutException(
            timeout,
            "Timeout occurred, Backup job is not paused",
            self.__driver.current_url
        )       

    @PageService()
    def wait_for_pause_button_visible(self, timeout=60):
        """Wait for pause button to be visible"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.__wait_for_pause_button_visible() is False:
                time.sleep(1)
            else:
                return True
        raise CVTimeOutException(
            timeout,
            "Timeout occurred while waiting for pause button to click",
            self.__driver.current_url
        )

    @PageService()
    def click_suspend_button(self, os_type):
        """Click on suspend button"""
        if self.wait_for_pause_button_visible()is True:
            self.__click_on_suspend_button(os_type)
            self.__click_on_1hour_option()
 
    @PageService()
    def add_client_backup_content(self,  content= None, custom_path= None, node_name='Library'):
        """Method to add backup content
        Args:
            content     (list)  : list of items to select
            custom_path (list)  : list of custom paths
            custom_path (str)  : node name to be collaps to select content
        Example:
            content = ['Desktop', 'Documents', 'Pictures']
            custom_path = ['C:\abc']
            node_name   = [Library or C:]
        """
        panel_name ='Content to backup'
        backup_tile = RPanelInfo(self.__admin_console, 'Backup content')
        backup_tile.edit_tile()
        self.__admin_console.wait_for_completion()
        self.__click_on_add_button()
        if content:
            self.__add_backup_content(content, node_name)
            self.__edit_backup_save_button()
            
        if custom_path:
            self.__add_custom_path(panel_name, custom_path)
            self.__edit_backup_save_button()
            
    @PageService()
    def add_client_exception_content(self, content= None, custom_path= None, node_name='Library'):
        """Method to add exception content
        Args:
            content     (list)  : list of items to select
            custom_path (list)  : list of custom paths
            custom_path (str)  : node name to be collaps to select content

            
        Example:
            content = ['Desktop', 'Documents', 'Pictures']
            custom_path = ['C:\abc']
            node_name   = [Library or C:]
        """
        panel_name = 'Exclude files, folders or patterns'
        backup_tile = RPanelInfo(self.__admin_console, 'Backup content')
        backup_tile.edit_tile()
        self.__admin_console.wait_for_completion()
        self.__access_exclude_tab()
        self.__admin_console.wait_for_completion()
        self.__click_on_add_button()
        self.__admin_console.wait_for_completion()
        if content:
            self.__add_backup_content(content, node_name)
            self.__edit_backup_save_button()
            
        if custom_path:
            self.__add_custom_path(panel_name, custom_path)
            self.__edit_backup_save_button()
                    
    @PageService()
    def remove_backup_content(self, content_name):
        """Method to remove the backup content 
        Args:
            content     (str)  : item to remove
            
        Example:
            content = 'Desktop'
        """
        backup_tile = RPanelInfo(self.__admin_console, 'Backup content')
        backup_tile.edit_tile()
        self.__admin_console.wait_for_completion()
        content_list= self.__get_all_content_elements()
        button_list= self.__get_all_button_elements()
        if content_list:
            for content_elem in content_list:
                if content_elem.is_displayed() and content_elem.text != '':
                    if content_elem.text ==content_name:
                        col_idx = content_list.index(content_elem)
                        button_elem = button_list[col_idx]
                        self.__scroll_to_element(content_elem)
                        self.__remove_selected_content(content_elem, button_elem)
                        break
        self.__edit_backup_save_button()
        
    @PageService()
    def remove_exclude_content(self, exclude_name):
        """Method to remove Exclude content
        Args:
            exclude_names     (str)  : item to remove
            
        Example:
            exclude_names = 'Desktop'
        """
        backup_tile = RPanelInfo(self.__admin_console, 'Backup content')
        backup_tile.edit_tile()
        self.__admin_console.wait_for_completion()
        self.__access_exclude_tab()
        self.__admin_console.wait_for_completion()
        content_list= self.__get_all_content_elements()
        button_list= self.__get_all_button_elements()
        if content_list:
            for content_elem in content_list:
                if content_elem.is_displayed() and content_elem.text != '':
                    if content_elem.text ==exclude_name:
                        col_idx = content_list.index(content_elem)
                        button_elem = button_list[col_idx]
                        self.__scroll_to_element(content_elem)
                        self.__remove_selected_content(content_elem, button_elem)
                        break
        self.__edit_backup_save_button()

class EdgeRestore:
    """client restore page in edgemode"""

    def __init__(self, admin_page):
        """ Initialize the edge Restore page object

                Args:

                   admin_page      (obj)       --  Admin console class object

        """
        self.__admin_console = admin_page
        self.__driver = admin_page.driver
        self.__navigator = admin_page.navigator
        self.__props = self.__admin_console.props
        self.__rbrowse = RBrowse(admin_page)
        self.__rpanel = RPanelInfo(admin_page)
        self.__checkbox = Checkbox(admin_page)
        self.__rmodelpanel= RModalPanel(admin_page)
        self.log = logger.get_log()
        self.__xp = "//div[@id='deviceBrowseForAgents']"
        self.__action_panel_xpath = self.__xp + "//div[contains(@class, 'top-panel-container')]"
    
    @WebAction()
    def __click_browsebutton_icon(self):
        """
        Click the browse icon in the restore window
        """
        xpath = f"//div[@class='destPathWrapper']//*[name()='svg'][@role='button']"
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __find_upload_input_element(self):
        """
        Find the element of the input file when upload button clicked
        """
        xpath = "//input[@id='upload']"
        upload_file_input_element = self.__driver.find_element(By.XPATH, xpath)
        return upload_file_input_element
   
    @WebAction()
    def __upload_progress_percentage(self):
        """track the upload progress of file"""
        xpath = "//div[@class='modal-title']/div[@class='progressUpdate']"
        ulpoad_progress = self.__driver.find_element(By.XPATH, xpath)
        return ulpoad_progress.text

    @WebAction()
    def __upload_progress_status(self):
        """get upload progress status"""
        xpath = "//div[@class='modal-title']/div[@class='progressStatus']"
        ulpoad_status = self.__driver.find_element(By.XPATH, xpath)
        return ulpoad_status.text

    @WebAction()
    def __enter_folder_name(self, folder_name):
        """enter folder name in folder location"""
        self.__driver.find_element(By.ID, "folderName").clear()
        self.__driver.find_element(By.ID, "folderName").send_keys(Keys.CONTROL, "A")
        self.__driver.find_element(By.ID, "folderName").send_keys(folder_name)
        time.sleep(2)

    @WebAction()
    def __click_on_create_folder_button(self):
        """click on create folder button """
        xpath = "//button[contains(.,'Create folder')]"
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __click_on_show_deleted_items(self):
        """click on show deleted items button button """
        xpath = "//div[@aria-label='Show deleted items']//button"
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __select_showusersettings_option(self):
        """select show user settings option"""
        xpath = "//div[@aria-label='Show user settings']"
        self.__driver.find_element(By.XPATH, xpath).click()
                    
    @WebAction()
    def __select_hideusersettings_option(self):
        """select hide user settings option"""
        xpath = "//div[@aria-label='Hide user settings']"
        self.__driver.find_element(By.XPATH, xpath).click()

    
    @PageService()
    def track_upload_progress(self):
        """track the upload progress of file"""
        status_percentage = self.__upload_progress_percentage()
        status_text = self.__upload_progress_status()
        if '(100%)' in status_percentage:
            if status_text == 'Upload Completed':
                self.log.info('Progress percentage at 100%, No errors reported on GUI')
            else:
                raise CVWebAutomationException(" Upload precentage showing 100% But upload status is showing as{0}".format(status_text))
        else:
            raise CVWebAutomationException("files failed to upload")
   
    @PageService()
    def upload_file_in_livebrowse(self, file_list):
        """
        Uploads a file in live browse
        
        Args:

            file_list(str/List)   : list of the files to be uploaded 
        """
        if isinstance(file_list, str):
            file_list = [file_list]
        upload_file_input = self.__find_upload_input_element()
        for each_file in file_list:
            self.log.info("Inserting file: %s for upload", each_file)
            upload_file_input.send_keys(each_file)
        self.__admin_console.wait_for_completion()

    @PageService()
    def create_folder(self, folder_name):
        """create folder in live browse"""
        self.__admin_console.click_button_using_text('Create Folder')
        self.__enter_folder_name(folder_name)
        self.__click_on_create_folder_button()
        self.__admin_console.wait_for_completion()
        
    @PageService()
    def browse_and_restore(self, source_data_path=None, dest_path=None, navigate_to_sourcepath=True):
        """
        Method to Restore the given client data in edgemode

        Args:

             source_data_path(str)   : Sourece data of teh client to be restored

             dest_path(str)         : Destination place to restore the data
             
             navigate_to_sourcepath(Bool) :True or False
             (if it it True then only it navigate to source path and select the given source path) 

        Returns :
              job id  (int) : Job id of the restore job

        Raises:
            Exception :
             -- if fails to run the restore operation

        """
        if navigate_to_sourcepath is True:
            self.__rbrowse.select_path_for_restore(source_data_path, use_tree=False)

        self.__rpanel.click_button('Restore')
        if dest_path:
            self.__checkbox.uncheck(self.__props['label.restoreToOriginal'])
            self.__click_browsebutton_icon()
            self.__admin_console.wait_for_completion()
            self.__rmodelpanel.select_path_from_treeview(dest_path)
            self.__rmodelpanel.save()
        self.__rmodelpanel.click_restore_button()
        restore_job_id = self.__admin_console.get_jobid_from_popup()
        return restore_job_id

    def get_deleted_files(self) -> list:
        """Gets the deleted files on that page
        """
        return [file for file in self.__rbrowse.get_column_data() if 'Deleted' in file]
  
    @PageService()
    def select_deleted_items_in_edgemode(self, content_path: str,
                                         files_folders: list = None, use_tree: bool = True) -> None:
        """Selects deleted files and folders to restore

            Args:

                content_path            (str)       :   Path to navigate which contains the content

                files_folders           (list)      :   Deleted files to be selected from table
                                                        (eg- 'C:\\Files\\Text.html'  or
                                                            '/opt/files/text.txt')

                use_tree                (bool)      :   To use folder tree to navigate instead of row links
        """
        self.__click_on_show_deleted_items()
        self.__rbrowse.navigate_path(content_path, use_tree=use_tree)
        deleted_files = [deleted_file.removesuffix('\nDeleted') for deleted_file in self.get_deleted_files()]
        if files_folders:
            for deleted_file in files_folders:
                if deleted_file in deleted_files:
                    self.__rbrowse.select_files([deleted_file])
        else:
            self.__rbrowse.select_files(deleted_files)

    @PageService()
    def select_usersetings_option(self, option='show_user_settings'):
        """create folder in live browse
        
            Args:

                option (str)  : option to show or hide the user settings  
                    EX: show_user_settings / hide_user_settings

        """
        if option=='show_user_settings':
            self.__select_showusersettings_option()
        else:            
            self.__select_hideusersettings_option()
        time.sleep(5)
        self.log.info("User settings option selected based on given input")

    @PageService()
    def user_settings_restore(self):
        """User settings restore"""
        self.__rbrowse.navigate_path("Libraries", use_tree=False)
        self.select_usersetings_option()
        self.__rbrowse.select_files(select_all=True)
        self.__rbrowse.submit_for_restore()
        self.__admin_console.checkbox_select('unconditionalOverwrite')
        self.__rmodelpanel.click_restore_button()
        restore_job_id = self.__admin_console.get_jobid_from_popup()
        return restore_job_id

        
class EdgeShares:
    """client shares in edgemode"""

    def __init__(self, admin_page):
        """ Initialize the edge Restore page object

                Args:

                   admin_page      (obj)       --  Admin console class object

        """
        self.__admin_console = admin_page
        self.__driver = admin_page.driver
        self.__navigator = admin_page.navigator
        self.__rbrowse = RBrowse(admin_page)
        self.log = logger.get_log()
        self._xp = "//div[@id='sharesTable_wrapper']//descendant::table[@id='sharesTable']"
        self._table_xp = "//table[@id='browsetable']"
        self._share_created_time=None
        

    @WebAction()
    def __select_privateshare_accesstype(self, access_type):
        """select access type of the private share"""
        view_list_xp = "//ul[contains(@aria-labelledby, 'permissions-chip-label')]"
        
        self.__driver.find_element(By.XPATH, "//div[@id='permissions']").click()
        if access_type.lower() == 'view':
            view_xp = view_list_xp + "//span[contains(.,'Can view')]"
        else: 
            view_xp = view_list_xp + "//span[contains(.,'Can edit')]"

        self.__driver.find_element(By.XPATH, view_xp).click()

    @WebAction()
    def __select_edit_publicshare(self):
        """select edit tab of the public share"""

        self.__driver.find_element(By.XPATH, "//span[contains(.,'Edit')]").click()

    @WebAction()
    def __click_share_button(self):
        """
        Click on share button from share panel
        """
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Share']").click()

    @WebAction()
    def __click_publicshare_done_button(self):
        """
        Click on done button from pubic share panel
        """
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Done']").click()

    @WebAction()
    def __select_recepient_user(self, recepient_user):
        """click on user field input box"""
        try:
            userfield_element = self.__driver.find_element(By.XPATH, "//input[@id='share_usersAndGroupsList']")
            userfield_element.click()
            userfield_element.send_keys(recepient_user)
            time.sleep(10)
            suggested_users_list = self.__driver.find_elements(By.XPATH, "//ul[@id='share_usersAndGroupsList-listbox']")
            for each_suggested_user in suggested_users_list:
                if recepient_user in each_suggested_user.text:
                    each_suggested_user.click()
            self.__driver.find_element(By.XPATH, "//button[@aria-label='Add']").click()

        except Exception as excp:
            raise Exception("Could not able to add users to share the file/folder {0}".format(excp))
            
    @WebAction()
    def __select_share_expire_option(self, expire_option):
        """select an option for when share will get expire"""
        if expire_option == 'Never':
            self.__driver.find_element(By.XPATH, "//input[@id='never']").click()
            self.log.info("selected share expire option as: 'Never'")
        elif expire_option == '5 days':
            self.__driver.find_element(By.XPATH, "//span[normalize-space()='Expire the link in']").click()
            self.log.info("selected share expire option as: '5 Days'")

    @WebAction()
    def __navigate_to_shares_page(self):
        """Navigate to shares page"""
        xpath = '//a[contains(@href,"/mydata/shares.do")]'
        shares_page = self.__driver.find_element(By.XPATH, xpath)
        shares_page.click()

    @WebAction()
    def __access_shares_tab(self, share_type):
        """access the share tab based on sharetype"""
        
        if share_type == 'SharedWithMe':
            self.__driver.find_element(By.ID, "sharedWithMeLi").click()
        elif share_type == 'SharedByMe':
            self.__driver.find_element(By.ID, "sharedByMeLi").click()
        elif share_type == 'PublicShare':
            self.__driver.find_element(By.ID, "publicShareLi").click()
        time.sleep(30)
        
    @WebAction()
    def __get_row_data(self, row_idx):
        """Reads the row data"""
        comp_xp = "//tbody[@id='sharesBody']"
        row_xp = comp_xp + "/tr[%d]/td" % row_idx
        row_data = []
        for cellvalue in self.__driver.find_elements(By.XPATH, row_xp):
            self.__driver.execute_script('arguments[0].scrollIntoView();', cellvalue)
            row_data.append(cellvalue.text)
        return row_data

    @WebAction()
    def __get_publicshare_row_data(self, row_idx):
        """Reads the row data"""
        comp_xp = "//tbody[@id='filetablebody']"
        row_xp = comp_xp + "/tr[%d]/td" % row_idx
        row_data = []
        for cellvalue in self.__driver.find_elements(By.XPATH, row_xp):
            self.__driver.execute_script('arguments[0].scrollIntoView();', cellvalue)
            row_data.append(cellvalue.text)
        return row_data
    
    @WebAction()
    def __get_table_elements_length(self):
        """get table length"""
        table_row_xp = "//tbody[@id='sharesBody']//tr"
        return len(self.__driver.find_elements(By.XPATH, self._xp + table_row_xp))

    @WebAction()
    def __get_publicshare_table_elements_length(self):
        """get table length"""
        table_xp = "//div[@id='listScrollbarViewport']//descendant::table[@class='innerBrowseTable']"
        table_row_xp = "//tbody[@id='filetablebody']//tr"
        return len(self.__driver.find_elements(By.XPATH, table_xp  + table_row_xp))
    
    @WebAction()
    def __get_table_elements(self):
        """get all table elements"""
        table_row_xp = "//tbody[@id='sharesBody']//tr"
        table_elems = self.__driver.find_elements(By.XPATH, self._xp + table_row_xp)
        return table_elems

    @WebAction()
    def __get_table_delete_buttons_elements(self, private_share=True):
        """get table delete elements"""
        if private_share is True:
            delete_button_xp = "//span[@title='Delete Share']"
        else:            
            delete_button_xp = "//span[@title='Delete Link']"
        delete_button_elems = self.__driver.find_elements(By.XPATH, self._xp + delete_button_xp)
        return delete_button_elems

    @WebAction()
    def __scroll_to_element(self, element):
        """Scrolls to element position"""
        self.__driver.execute_script("arguments[0].scrollIntoView();", element)

    @WebAction(delay=0)
    def __unshare_selected_folder(self, content_elem, button_elem):
        """remove the given content from edit backup content tile"""
        self.__admin_console.mouseover_and_click(content_elem, button_elem)
        time.sleep(5)
        button_xp = "//button[contains(@class,'okSaveClick')]"
        self.__driver.find_element(By.XPATH, button_xp).click()
    
    @WebAction()
    def __validate_preview_elements(self, xp):
        """verify preview elements exists ot not """
        preview_xp = f"//div[contains(@class, 'preview-content')]"
        xp = preview_xp + xp
        find_elem = self.__driver.find_element(By.XPATH, xp)
        return find_elem

    @WebAction()
    def __validate_imagefiles_element(self):
        """verify preview element for image files"""
        img_xp = f"//div[contains(@class, 'contentArea')]//img[@id='thumbImg']"
        find_elem = self.__driver.find_element(By.XPATH, img_xp)
        return find_elem

    @WebAction()
    def __get_preview_details(self):
        """read the preview details"""
        xp = f"//div[contains(@class, 'contentArea')]//descendant::div//div[@id='file-details']"
        preview_details = self.__driver.find_element(By.XPATH, xp).text
        return preview_details
    
    @WebAction()
    def __click_preview_download_button(self) -> None:
        """Clicks download button of previewed file
        """

        download_button_xpath = "//button[@aria-label='Download']"
        download_button_element = self.__driver.find_element(By.XPATH, download_button_xpath)
        download_button_element.click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __read_public_share_link(self) -> None:
        """Read public share link"""
        share_link_xpath = "//div[@class='link-container']"
        public_share_xpath = self.__driver.find_element(By.XPATH, share_link_xpath)
        return public_share_xpath.text

    @WebAction()
    def __select_all_items(self) -> None:
        """select all items checkbox"""
        all_checkbox_xpath = f"{self._table_xp}//tr//th/div[contains(@role,'checkbox')]"
        self.__driver.find_element(By.XPATH, all_checkbox_xpath).click()

    @WebAction()
    def __select_file_folder(self, name) -> None:
        """select checkbox of given file and folder"""
        selector = [f"text()='{name}'", f"contains(text(), '{name}')"]
        row_xpath = f"{self._table_xp}//*[{selector}]/parent::td/preceding-sibling::td"
        rows = self.__driver.find_elements(By.XPATH, row_xpath)
        if not rows:
            raise NoSuchElementException("Rows not found with name [%s]" % name)
        for each_row in rows:
            hover = ActionChains(self.__driver).move_to_element(each_row)
            hover.perform()
            time.sleep(1)
            each_row.click()

    @WebAction()
    def __download_from_shares(self) -> None:
        """Clicks download button of previewed file"""

        download_xpath = "//a[@id='downloadLink']"
        self.__driver.find_element(By.XPATH, download_xpath).click()
        self.__admin_console.wait_for_completion()
        
    @PageService()
    def create_private_share(self, 
                             path_tobe_shared,
                             folder_or_file_name, 
                             recepient_user, 
                             share_access_type='view', 
                             expire_selection='Never'
                             ):
        """
        Method to Create private shares for laptop clients 

        Args:

            path_tobe_shared(str)      : Folder or file path which need to be shared
            
            folder_or_file_name(str)   : Name of the shared file or folder

            recepient_user(str)        : User name with whom folder will be shared
            
            share_access_type(str)     : Share access type ex: view or edit
            
            expire_selection(str)      : share expire value
            
        Raises:
            Exception :
             -- if fails to share file / folder

        """
        self.__rbrowse.select_path_for_restore(path_tobe_shared, file_folders=[folder_or_file_name])
        self.__rbrowse.select_action_dropdown_value(index=0, value='Share')
        self.__select_privateshare_accesstype(share_access_type)
        self.__select_recepient_user(recepient_user)
        self.__select_share_expire_option(expire_selection)
        self.__click_share_button()
        notification = self.__admin_console.get_notification()
        self.__admin_console.wait_for_completion()
        notification_text = f'Share {folder_or_file_name} is created'
        if notification_text in notification:
            self.log.info("File / Folder {0} shared successfully".format(folder_or_file_name))
        else:
            raise CVWebAutomationException("Unexpected notification [%s] private share creation failing"
                                           .format(notification))
    @PageService()
    def create_public_share(self, 
                            path_tobe_shared, 
                            folder_or_file_name,
                            share_access_type='view', 
                            expire_selection='Never'):
        """
        Method to Create public shares for laptop clients 

        Args:

            path_tobe_shared(str)      : Folder or file path which need to be shared
            
            folder_or_file_name(str)   : Name of the shared file or folder

            expire_selection(str)      : share expire value
            
        Raises:
            Exception :
             -- if fails to share file / folder

        """
        self.__rbrowse.select_path_for_restore(path_tobe_shared, file_folders=[folder_or_file_name])
        self.__rbrowse.select_action_dropdown_value(index=0, value='Get public link')
        if share_access_type.lower() == 'Edit':
            self.__select_edit_publicshare()
        self.__select_share_expire_option(expire_selection)
        public_share_link = self.__read_public_share_link()
        self.__click_publicshare_done_button()
        notification = self.__admin_console.get_notification(wait_time=0)
        self.__admin_console.wait_for_completion()
        notification_text = f'Link updated successfully'
        if notification_text in notification:
            self.log.info("File / Folder {0} shared successfully".format(folder_or_file_name))
        else:
            raise CVWebAutomationException("Unexpected notification [%s] private share creation failing"
                                           .format(notification))
        return public_share_link
            
    @PageService()        
    def navigate_to_webconsole_shares_page(self, share_type):
        """ This method is used to navigate to shares page of the webconsole"""
        self.__navigator.navigate_to_my_data()
        windows = self.__admin_console.driver.window_handles
        self.__admin_console.driver.switch_to.window(windows[1])
        self.__admin_console.wait_for_completion()
        self.__navigate_to_shares_page()
        self.__admin_console.wait_for_completion()
        self.__access_shares_tab(share_type)
        
    @PageService()
    def read_shared_by_me_data(self):
        """This method is used to read all data from shared by me tab"""
        table_data = []
        final_res = []
        table_len = self.__get_table_elements_length()
        for each_row_idx in range(1, table_len+1):
            table_data.append(self.__get_row_data(each_row_idx))
        for _idx, each_row in enumerate(table_data):
            share_dict = {'Name': '', 'Source': '', 'Path': '','Date Created': '', 'Expiry': ''}
            share_dict['Name'] = each_row[0]
            share_dict['Source'] = each_row[1]
            share_dict['Path'] = each_row[2]
            share_dict['Date Created'] = each_row[3]
            share_dict['Expiry'] = each_row[4]
            final_res.append(share_dict)
        return final_res
    
    @PageService()
    def read_shared_with_me_data(self):
        """This method is used to read all data from shares with me tab"""
        table_data = []
        final_res = []
        table_len = self.__get_table_elements_length()
        for each_row_idx in range(1, table_len+1):
            table_data.append(self.__get_row_data(each_row_idx))
        for _idx, each_row in enumerate(table_data):
            share_dict = {'Name': '', 'Owner': '', 'Date Created': '', 'Expiry': ''}
            share_dict['Name'] = each_row[0]
            share_dict['Owner'] = each_row[1]
            share_dict['Date Created'] = each_row[2]
            share_dict['Expiry'] = each_row[3]
            final_res.append(share_dict)
        return final_res

    @PageService()
    def read_publicshare_data(self):
        """This method is used to read all data from public share link"""
        table_data = []
        final_res = []
        table_len = self.__get_publicshare_table_elements_length()
        for each_row_idx in range(1, table_len+1):
            table_data.append(self.__get_publicshare_row_data(each_row_idx))
        for _idx, each_row in enumerate(table_data):
            share_dict = {'Name': '', 'Date Modified': '', 'Size': ''}
            share_dict['Name'] = each_row[1]
            share_dict['Date Modified'] = each_row[2]
            share_dict['Size'] = each_row[3]
            final_res.append(share_dict)
        return final_res

    @PageService()
    def delete_private_share(self, folder_name, share_type='SharedByMe', private_share=True):
        """This method is used to delete the share as owner
        
        Args:

            folder_name(str)  : Folder or file path which need to be deleted from shares
            
            share_type(str)   : Type of the share to navigate in shares page 

            private_share(Bool) : True or false (if it true it consider as private share)
            
        """
        self.navigate_to_webconsole_shares_page(share_type)
        content_list= self.__get_table_elements()
        button_list= self. __get_table_delete_buttons_elements(private_share)
        for content_elem in content_list:
            if content_elem.is_displayed() and content_elem.text != '':
                if folder_name in content_elem.text:
                    col_idx = content_list.index(content_elem)
                    button_elem = button_list[col_idx]
                    self.__scroll_to_element(content_elem)
                    self.__unshare_selected_folder(content_elem, button_elem)
                    break
                
    def __check_filetype_based_on_extension(self, file_name):
        """
        There are many types of files and each of them can be checked by visibility of one class or the other.
        based on extension grouping the file types which have similar tags while previwing
        
        Args:

            file_names(list)      : name of the file name
            

        """
        if file_name.lower().endswith(".mp4"):
            file_type_found = 'video'
        if file_name.lower().endswith(".mp3"):
            file_type_found = 'audio'
        if file_name.lower().endswith(".txt") or file_name.lower().endswith(".py") or file_name.lower().endswith(
                ".csv") or file_name.lower().endswith(".log"):
            file_type_found = 'text/py/csv/log'
        if file_name.lower().endswith(".pdf"):
            file_type_found = 'pdf'
        if file_name.lower().endswith(".ppt") or file_name.lower().endswith(".pptx") or file_name.lower().endswith(
                ".doc") or file_name.lower().endswith(".docx"):
            file_type_found = 'ppt/word'
        if file_name.lower().endswith(".exe") or file_name.lower().endswith(".xml"):
            file_type_found = 'exe/xml'
        if file_name.lower().endswith(".xls") or file_name.lower().endswith(".xlsx"):
            file_type_found = 'excel'
        if file_name.lower().endswith(".png") or file_name.lower().endswith(".gif") or file_name.lower().endswith(
                ".jpg") or file_name.lower().endswith(".bmp"):
            file_type_found = 'image'
            
        return file_type_found
    
    def verify_file_preview(self, file_names):
        """This method is used to verify the preview of the file
        
        Args:

            file_names(list)      : list of the files names to be previewd 
            
        """
        no_preview_xp = "//div[contains(@class, 'contentArea')]/descendant::div/div[@class='preview-state']"
        preview_failed_files=[]
        preview_details = {}
        for each_file in file_names:
            self.log.info("-----Verifying Preview for file: {0} -----" .format(each_file))
            file_type_found = self.__check_filetype_based_on_extension(each_file)
            self.__rbrowse.select_for_preview(each_file)
            time.sleep(10) # waiting for preview to be open for all types of files
            if self.__admin_console.check_if_entity_exists('xpath', no_preview_xp):
                preview_text = self.__driver.find_element(By.XPATH, no_preview_xp)
                if "Preview not available" or "Loading preview" in preview_text.text:
                    preview_failed_files.append(each_file)
            else:
                try:
                    if file_type_found == 'pdf':
                        pdf_xp = f"//descendant::table//div[@id='page1-div']"
                        find_elem = self.__validate_preview_elements(pdf_xp)
                        if find_elem:
                            file_details = self.__get_preview_details()
                            preview_details[each_file]=file_details
                            
                        elif file_type_found == 'video':
                            pass #yet to be implemented

                        elif file_type_found  == 'audio':
                            pass #yet to be implemented

                    elif file_type_found == 'ppt/word':
                        ppt_xp = f"//descendant::table//p"
                        find_elem = self.__validate_preview_elements(ppt_xp)
                        if find_elem:
                            file_details = self.__get_preview_details()
                            preview_details[each_file]=file_details
                    elif file_type_found == 'image':
                        find_elem = self.__validate_imagefiles_element()
                        if find_elem:
                            file_details = self.__get_preview_details()
                            preview_details[each_file]=file_details
                    elif file_type_found == 'text/py/csv/log':
                        txt_xp = f"//pre"
                        find_elem = self.__validate_preview_elements(txt_xp)
                        if find_elem:
                            file_details = self.__get_preview_details()
                            preview_details[each_file]=file_details

                    elif file_type_found == 'excel':
                        xls_xp = f"//descendant::table//h1"
                        find_elem = self.__validate_preview_elements(xls_xp)
                        if find_elem:
                            file_details = self.__get_preview_details()
                            preview_details[each_file]=file_details
                    self.__rbrowse.close_preview_file()

                except Exception as exp:
                    preview_failed_files.append(each_file)
        return preview_failed_files, preview_details
                    
    @PageService()
    def verify_download_from_preview(self, file_names, local_machine, download_directory, utils_object):
        """This method is used to verify the downloads from preview of the file
        
        Args:

            file_names(list)        : list of the files names to be previewd 
            
            local_machine(object)   : object of the local machine where file will be downloaded
            
            download_directory(str) : downloaded directory from local machine where file will be downloaded
            
            utils_object(object)    : object of the utils object
        """
        download_files_hashes = {}
        for each_file in file_names:
            file_name_ext = os.path.splitext(each_file)
            file_extension = file_name_ext[1]
            self.log.info("-----Preview and downloading for file: {0} -----" .format(each_file))
            self.__rbrowse.select_for_preview(each_file)
            time.sleep(10) # waiting for preview to be open for all types of files
            self.__click_preview_download_button()
            notification = self.__admin_console.get_notification()
            self.__admin_console.wait_for_completion()
            if notification:
                raise CVWebAutomationException("Unexpected notification [%s] while file is download "
                                               .format(notification))
            utils_object.wait_for_file_to_download(file_extension, timeout_period=300)
            
            file_hash = local_machine.get_file_hash(download_directory + '\\' + each_file)
            download_files_hashes[each_file]=file_hash
            self.__rbrowse.close_preview_file()
          
        return download_files_hashes                    
            
    @PageService()
    def download_items_from_shares(self, content_path: str, 
                                         select_all=True,
                                         navigate_to_folder=True, 
                                         files_folders: list = None) -> None:
        """Selects items for download from share

            Args:

                content_path            (str)       :   Path to navigate which contains the content
                
                navigate_to_folder      (bool)      :  True / False

                files_folders           (list)      :   Deleted files to be selected from table
                                                        (eg- 'C:\\Files\\Text.html'  or
                                                            '/opt/files/text.txt')
        """
        if navigate_to_folder is True:
            shares_info= self.read_shared_by_me_data()
            for each_item in shares_info:
                if each_item['Name']==content_path:
                    self.__admin_console.select_hyperlink(content_path)
        if select_all is True:
            self.__select_all_items()
        elif files_folders:
            for each_name in files_folders:
                self.__select_file_folder(each_name)
        else:
            raise CVWebAutomationException("No files or folders given to select")
        self.__download_from_shares()
                 
