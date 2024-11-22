from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Module to deal with Add Content Tab used in Admin console pages

AddContent
    edit_content                --      Click on edit and specify content.
    
    delete_content_path         --      Deletes selected content paths from the edit content tile.

RBackupContent:

    available_file_system()        :       Method to get supported file systems
    
    select_file_system()           :       Method to click on file system to configure / edit backup content
    
    add_backup_content()           :       Method to add backup content
    
    remove_all_backup_content()    :       Method to remove configured backup content
    
    add_exclude_content()          :       Method to add exclude content
    
    remove_all_exclude_content()   :       Method to remove exclude content
    
    add_exception_content()        :       Method to add exception content
    
    remove_all_exception_content() :       Method to remove exception content
    
    enable_backup_system_state()   :       Method to enable backup system state
    
    disable_backup_system_state()  :       Method to disable backup system state
    
    get_content_details()          :       Method to get all backup content details
    
"""

from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.core import Toggle, Checkbox, TreeView
from Web.AdminConsole.Components.dialog import RModalDialog


class AddContent(RModalDialog):
    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.admin_console = admin_console

    @WebAction()
    def _type_custom_path(self, path):
        """
        Type the custom path.

        Args:
            path    (str)   :   Path that needs to be typed in.

        """
        self.fill_text_in_field(element_id="custom-path", text=path)

    @WebAction()
    def _add_custom_path(self):
        """
        Add the custom path by clicking on plus glyphicon.
        """
        self.click_element("//div[contains(@class,'add-path-btn')]")

    @WebAction()
    def _select_checkbox_by_label(self, label):
        """
        Method to select checkbox by label

        Args:
            label (str)   --  The value of the label next to the checkbox.

        """
        if not self.admin_console.driver.find_element(By.XPATH, 
                f"//label[text()='{label}']/preceding-sibling::input").is_selected():
            self.admin_console.driver.find_element(By.XPATH, f"//label[text()='{label}']").click()

    @PageService()
    def edit_content(self, contents):
        """
        Click on edit and specify content
        Args:
            contents (list)  --  Content to add
        """
        self.click_add()
        self.click_element("//div[normalize-space()='Custom path']")

        for content in contents:
            self._type_custom_path(content)
            self.admin_console.wait_for_completion()
            self._add_custom_path()
            self.admin_console.wait_for_completion()
        self.click_submit()

    @PageService()
    def delete_content_path(self, path_list):
        """
        Deletes selected content paths from the edit content tile
        Args:
            path_list (list): paths to be deleted
        """
        for path in path_list:
            content_xpath = f"//div[@class='path-list']//div[@class='path-container']//div[contains(@class,'mui-tooltip') and contains(@class,'path-name') and @aria-label='{path}']/following-sibling::div[contains(@class,'remove-path-btn')]//button"
            self.click_element(content_xpath, is_entity_visible_only_on_hover=True)
        self.click_submit()


class RBackupContent:
    
    def __init__(self, admin_console):
        """Initalize the RBackupContent

        Args:
            admin_console    :   Instance of AdminConsoleBase
        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__tree_view = TreeView(self.__admin_console)
        
        self.__base_xpath = "//*[text()='Content to backup']//ancestor::div[contains(@class, 'MuiGrid-item')]"
        self.__content_panel_xpath = self.__base_xpath + "//h3[contains(., '{0}')]//ancestor::div[@class='folders-container']"
        self.__toggle = Toggle(admin_console, self.__base_xpath)
        self.__checkbox = Checkbox(admin_console, self.__base_xpath)
        
    @property
    def toggle(self):
        """Returns instance of toggle class"""
        return self.__toggle

    @property
    def checkbox(self):
        """Returns instance of checkbox class"""
        return self.__checkbox

    @WebAction()
    def __click_button_inside_panel(self, panel_name, text):
        """Method to click on button inside specified panel"""
        panel_xpath = self.__content_panel_xpath.format(panel_name)
        self.__driver.find_element(By.XPATH, 
            f"{panel_xpath}//button[contains(.,'{text}')]"
        ).click()
       
    @WebAction()
    def __click_button_on_action_list(self, text):
        """Methd to click on a button inside action list"""
        self.__driver.find_element(By.XPATH, f"//*[@id='action-list']//button[contains(.,'{text}')]").click()
        
    @WebAction()
    def __add_content(self, panel_name, content):
        """Method to add content"""
        self.__click_button_inside_panel(panel_name, 'Add')
        self.__click_button_on_action_list('Content')
        self.__tree_view.select_items(content)
        
    @WebAction()
    def __fill_custom_path(self, panel_name, custom_path):
        """Method to fill custom path"""
        panel_xpath = self.__content_panel_xpath.format(panel_name)
        input_box = f"{panel_xpath}//input[contains(@id, 'CustomPath')]"
        self.__driver.find_element(By.XPATH, input_box).send_keys(custom_path)
        self.__driver.find_element(By.XPATH, 
            f'{input_box}//following-sibling::button'
        ).click()

    @WebAction()
    def __add_custom_path(self, panel_name, custom_paths):
        """Method to add custom path"""
        self.__click_button_inside_panel(panel_name, 'Add')
        self.__click_button_on_action_list('Custom path')
        for custom_path in custom_paths:
            self.__fill_custom_path(panel_name, custom_path)
    
    @PageService()
    def available_file_system(self):
        """Method to return the available file systems (windows / unix)"""
        return [
            element.text
            for element in self.__driver.find_elements(By.XPATH, 
                f"{self.__base_xpath}//div[contains(@class, 'flexContainer')]//button"
            )
        ]
    
    @WebAction()
    def select_file_system(self, os_name:str):
        """Method to select windows / unix file system"""
        self.__driver.find_element(By.XPATH, 
            f"{self.__base_xpath}//button[contains(.,'{os_name}')]"
        ).click()
         
    @PageService()   
    def add_backup_content(self, content= [], custom_path= []):
        """Method to add backup content
        
        Args:
            content     (list)  : list of items to select
            custom_path (list)  : list of custom paths
            
        Example:
            content = ['Desktop', 'Music', 'Google Drive']
            custom_path = ['*.exe', '*.txt']
        """
        panel_name = 'Content to backup'
        
        if content:
            self.__add_content(panel_name, content)
            RModalDialog(self.__admin_console, 'Add content').click_submit()
            
        if custom_path:
            self.__add_custom_path(panel_name, custom_path)
        
    @PageService()    
    def remove_all_backup_content(self):
        """Method to clear backup content from the panel"""
        self.__click_button_inside_panel('Content to backup', 'Remove all')
      
    @PageService()
    def add_exclude_content(self, content= None, custom_path= None):
        """Method to add exclude content
        
        Args:
            content     (list)  : list of items to select
            custom_path (list)  : list of custom paths
            
        Example:
            content = ['Desktop', 'Music', 'Google Drive']
            custom_path = ['*.exe', '*.txt']
        """
        panel_name = 'Exclude - files/folders/patterns'

        if (content or custom_path) and self.__toggle.is_exists(
            id='isExcludedContentDefined'
        ):
            self.__toggle.enable(id='isExcludedContentDefined')

        if content:
            self.__add_content(panel_name, content)
            RModalDialog(self.__admin_console, 'Add exclusions').click_submit()

        if custom_path:
            self.__add_custom_path(panel_name, custom_path)
 
    @PageService()
    def remove_all_exclude_content(self):
        """Method to clear exclude content from the panel"""
        self.__click_button_inside_panel('Exclude - files/folders/patterns', 'Remove all')
    
    @PageService()
    def add_exception_content(self, content= None, custom_path= None):
        """Method to add exception content
        
        Args:
            content     (list)  : list of items to select
            custom_path (list)  : list of custom paths
            
        Example:
            content = ['Desktop', 'Music', 'Google Drive']
            custom_path = ['*.exe', '*.txt']
        """
        panel_name = 'Except for these files/folders'
        if (content or custom_path) and self.__toggle.is_exists(
            id='isFilterToExcludeContentDefined'
        ):
            self.__toggle.enable(id='isFilterToExcludeContentDefined')

        if content:
            self.__add_content(panel_name, content)
            RModalDialog(self.__admin_console, 'Add exceptions').click_submit()

        if custom_path:
            self.__add_custom_path(panel_name, custom_path)
    
    @PageService()
    def remove_all_exception_content(self):
        """Method to clear exception content from the panel"""
        self.__click_button_inside_panel('Except for these files/folders', 'Remove all')
    
    @PageService()
    def enable_backup_system_state(self, use_vss= True, only_with_full_backup= False):
        """Method to enable the backup system state

        Args:
            use_vss               (bool)  : whether to select or unselect vss option
            only_with_full_backup (bool)  : whether to select or unselect full backup option
        """
        self.__toggle.enable(id='backupSystemState')
        
        if use_vss:
            self.__checkbox.check(id='useVSSForSystemState')
        else:
            self.__checkbox.uncheck(id='useVSSForSystemState')
            
        if only_with_full_backup:
            self.__checkbox.check(id='backupSystemStateforFullBkpOnly')
        else:
            self.__checkbox.uncheck(id='backupSystemStateforFullBkpOnly')
        
    @PageService()
    def disable_backup_system_state(self):
        """Method to disable the backup system state"""
        self.__toggle.disable(id= 'backupSystemState')
        
    @WebAction()
    def __get_content_of_panel(self, panel_name):
        """Method to get the content of a panel"""
        panel_xpath = f"{self.__content_panel_xpath.format(panel_name)}//*[@class='folder-list']"

        if self.__admin_console.check_if_entity_exists("xpath", panel_xpath):
            return self.__driver.find_element(By.XPATH, panel_xpath).text.split('\n')
        return []
        
    @WebAction()
    def __get_content_details(self, file_system):
        """Method to get content details"""
        self.select_file_system(file_system)

        content = {'BACKUP_CONTENT': self.__get_content_of_panel('Content to backup')}
        content['EXCLUDED_CONTENT']  = self.__get_content_of_panel('Exclude - files/folders/patterns')
        content['EXCEPTION_CONTENT'] = self.__get_content_of_panel('Except for these files/folders')

        return content
    
    @WebAction()
    def __get_backup_system_state_details(self):
        """Method to get the backup system state details"""
        self.select_file_system('Windows')

        if self.__toggle.is_enabled(id= 'backupSystemState'):
            return {
                'backupSystemState': True,
                'useVss' : self.__checkbox.is_checked(id= 'useVSSForSystemState'),
                'onlyWithFullBackup' : self.__checkbox.is_checked(id= 'backupSystemStateforFullBkpOnly')
            }

        return  {'backupSystemState': False}
    
    @PageService()
    def get_content_details(self, file_system= '', backup_system_state= False):
        """Method to get the backup content details for all the file system
        
        Args:
            file_system         (str)   : backup content details for specified operating system
            backup_system_state (bool)  : whether backup system state details should be included or not
        """
        details = {}

        if self.__toggle.is_exists(id= 'isIncludedContentDefined'):
            return {} # content not defined yet

        # content details
        if file_system:
            details[file_system] = self.__get_content_details(file_system)
        else:
            for file_system in self.available_file_system():
                details[file_system] = self.__get_content_details(file_system)

        # backup system state details
        if backup_system_state:
            details['BACKUP_SYSTEM_STATE'] = self.__get_backup_system_state_details()

        return details
