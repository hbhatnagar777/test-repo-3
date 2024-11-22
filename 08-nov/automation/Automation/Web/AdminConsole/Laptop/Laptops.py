from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on
on the Laptops page in admin console

Class:

    Laptops()

Functions:

_init_()                        :     initialize the class object

__set_host_name()               :     fill the hostname field with the specified name

__set_user_name()               :     fill the username field with the specified user name

__set_password()                :     fill the password field with the value

__set_confirm_password()        :     fill the confirm password field with the value

__select_os_option()            :     select the radio button based on given input

__get_text_from_dialog()        :     Gets the notification text

__client_configuration_status   : Configuartion status of the client

get_jobid_from_screen()         :     Gets the job id from screen

get_client_configuration_status() : to get the client configuration status

check_if_error_text()           :     Read the error text from popup

add_windows_laptop()            :     Method to add new windows laptop

add_mac_laptop()                :     Method to add new mac laptop

deactivate_laptop()             :     Method to deactivate the laptop

action_update_software()        :     To invoke update software operation in the laptop page

action_check_readiness()        :     To run check readiness operation on the given client in Laptop page

action_send_logs()              :     To perform send logs operation on the given client in Laptop page

action_retire_client()          :     Retire the given client

activate_laptop_byuser()        :     activate the laptop by enduser

activate_laptop_byplan()        :     activate the laptop by given plan name

subclient_backup_now()          :    To perform backup operation

cancel_the_form()               :    To perform cancel operation

laptop_summary_info()           :    get the summary info from admin console laptop page

restore_from_job()              :    Method for job based restore

restore_from_actions()          :    Method to Restore the given client data from actions

restore_from_details_page()     :    Method to Restore the given client data from details page

browse_restore_storage_policies() :  To restore from all the storage policy copies for the region-based plan

select_backuplevel_and_submit_backupjob()    : select the backup type and click on submit button from modal panel

backup_from_actions()                        : Method to submit the backup job from laptop actions

backup_from_detailspage()                    : Method to submit backup job from details page

restore_from_actions()                       : Method to submit restore job from actions

restore_from_details_page()                  : Method to submit restore job from details page

access_view_jobs()                           : Method to view the jobs from details page

suspend_job_from_detailspage()               : Method to suspend the job from details page and check the status   

resume_job_from_detailspage()                : Method to resume the backup job from laptop details page

"""

import re
import time
from AutomationUtils import logger
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Components.panel import PanelInfo, Backup, RPanelInfo, RModalPanel
from Web.AdminConsole.Components.panel import DropDown, RDropDown
from Web.AdminConsole.Components.core import Checkbox
from Web.AdminConsole.Components.browse import Browse, ContentBrowse, RBrowse, RContentBrowse
from Web.AdminConsole.FileServerPages.file_servers import RestorePanel
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.exceptions import CVWebAutomationException


class Laptops:
    """
    Class for Laptops page
    """

    def __init__(self, admin_page):
        """
        Method to initiate the Laptops class

        Args:
            admin_page   (Object) :   Admin Page Class object
        """
        self.__admin_console = admin_page
        self.__driver = admin_page.driver
        self.__admin_console.load_properties(self)
        self.__rdialog = RModalDialog(admin_page)
        self.__table = Rtable(admin_page)
        self.__cvtable = Table(admin_page)
        self.__rbrowse = RBrowse(admin_page)
        self.__browse = Browse(admin_page)
        self.__rpanel = RPanelInfo(admin_page)
        self.__backup = Backup(admin_page)
        self.__navigator = admin_page.navigator
        self.__rdrop_down = RDropDown(admin_page)
        self.__jobs = Jobs(admin_page)
        self.__rmodelpanel= RModalPanel(admin_page)
        self.__checkbox = Checkbox(admin_page)
        self.__props = self.__admin_console.props
        self.__restore_panel = RestorePanel(admin_page)
        self.__content_browse = ContentBrowse(admin_page)
        self.log = logger.get_log()

    @WebAction()
    def __set_host_name(self, host_name):
        """
        Method to set the hostname

        Args:
            host_name (string): Machine Host name

        """
        self.__admin_console.fill_form_by_id("hostName", host_name)

    @WebAction()
    def __set_user_name(self, user_name):
        """
        Method to set username

        Args:
            user_name (string): Machine User name

        """
        self.__admin_console.fill_form_by_id("fakeUserName", user_name)

    @WebAction()
    def __set_password(self, password):
        """
        Method to set password

        Args:
            password (string): Machine password

        """
        self.__admin_console.fill_form_by_id("fakePassword", password)

    @WebAction()
    def __set_confirm_password(self, confirm_password):
        """
        Method to set confirm password

        Args:

            confirm_password (string): confirm password

        """
        self.__admin_console.fill_form_by_id("confirmPassword", confirm_password)

    @WebAction()
    def __select_os_option(self, value):
        """
        Method to select the radio button based on "Value"

        Args:

            value (string): value of the element

        """

        self.__driver.find_element(By.XPATH, 
            "//input[@type='radio' and @value='" + value + "']").click()

    @WebAction()
    def __get_text_from_dialog(self):
        """
        Gets the notification text

        Returns:

            notification_text (str): the notification string

        """
        xpath = "//div[@class='modal-content']/div/div/div/p"
        if self.__admin_console.check_if_entity_exists("xpath", xpath):
            return self.__driver.find_element(By.XPATH, xpath).text
        xpath = "//div[@class='modal-content']/div/div/div/div"
        return self.__driver.find_element(By.XPATH, xpath).text

    @WebAction()
    def __client_configuration_status(self):
        """
        Get configuration status of the client"
       """

        xpath = f"//td[@id='cv-k-grid-td-deviceSummary.isClientDeconfigured']"\
        f"//span[contains(@class,'k-icon')and @cv-toggle='tooltip']"

        elem = self.__driver.find_element(By.XPATH, xpath)

        return elem.get_attribute('cv-toggle-content')
    
    @WebAction()
    def __click_browsebutton_icon(self):
        """
        Click the browse icon in the restore window
        """
        xpath = f"//div[@class='destPathWrapper']//*[name()='svg'][@role='button']"
        self.__driver.find_element(By.XPATH, xpath).click()
    
    @WebAction()
    def __click_backup_submit(self):
        """
        Click the browse icon in the restore window
        """
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Submit']").click()
    

    @WebAction()
    def __set_backup_level(self, backup_type):
        """ Sets backup type

        Args:
            backup_type (BackupType): Type of backup should be one among the types defined in
                                      BackupType enum
        """
        self.__driver.find_element(By.XPATH, 
            "//input[@type='radio' and @value='" + backup_type.value + "']").click()

    @WebAction()
    def __click_on_viewjobs_button(self):
        """
        click on view jobs button from laptop details page
        """
        self.__driver.find_element(By.XPATH, "//div[contains(text(),'View jobs')]").click()

    @WebAction()
    def __click_on_suspend_button(self):
        """
        click on suspend button from laptop details page
        """
        self.__driver.find_element(By.XPATH, "//button[@title='Suspend job']").click()

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
        click on resume button from laptop details page
        """
        self.__driver.find_element(By.XPATH, "//button[@title='Resume job']").click()
        

    @WebAction()
    def __click_on_restore_button(self):
        """
        click on resume button from laptop details page
        """
        self.__driver.find_element(By.XPATH, "(//button[@aria-label='Restore'])[1]").click()
        
    @WebAction()
    def __get_configuration_status(self, status):
        """
        get the configuration status from laptop details page
        """
        xpath = f"//div[@aria-label='{status}']"
        if self.__admin_console.check_if_entity_exists("xpath", xpath):
            return True
        else:
            return False

    @WebAction()
    def __read_user_title(self):
        """
        read the user title from security details page
        """
        xpath = "*//h1[@class='page-title']"
        user_title = self.__driver.find_element(By.XPATH, xpath).text
        return user_title
    
    @PageService()
    def get_jobid_from_screen(self):
        """
        Gets the job id from screen

        Returns:

            job_id (int):  the job id for the submitted request

        """
        job_text = self.__get_text_from_dialog()
        if not job_text:
            raise Exception("No notification is popped up to extract job id")
        job_id = re.findall(r'\d+', job_text)[0]
        self.log.info("Job %s has started", str(job_id))
        return job_id

    @PageService()
    def get_client_configuration_status(self, status='Configured'):
        """
        Gets the client configuration status

        Returns:

        """
        client_status = self.__get_configuration_status(status)
        return client_status

    @PageService()
    def add_windows_laptop(self,
                           host_name,
                           user_name,
                           password=None,
                           confirm_password=None):
        """
        Method to add new windows laptop

        Args:
            host_name (string): hostname of the laptop

            user_name (string): user_name of the laptop

            password (string): password of the laptop

            confirm_password (string): password of the laptop

        Returns:
            None

        Raises:
            Exception:
                if failed to add laptop

        """
        self.__admin_console.select_hyperlink('Add laptop')
        self.__select_os_option('WINDOWS')
        self.__set_host_name(host_name)
        self.__set_user_name(user_name)
        self.__set_password(password)
        self.__set_confirm_password(confirm_password)

        self.__admin_console.submit_form()
        job_id = self.get_jobid_from_screen()
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()
        return job_id

    @PageService()
    def add_mac_laptop(self,
                       host_name,
                       user_name,
                       password=None,
                       confirm_password=None):
        """
        Method to add new mac laptop

        Args:
            host_name (string): hostname of the laptop

            user_name (string): user_name of the laptop

            password (string): password of the laptop

            confirm_password (string): password of the laptop

        Returns:
            None

        Raises:
            Exception:
                if failed to add laptop

        """
        self.__admin_console.select_hyperlink('Add laptop')
        self.__select_os_option('UNIX_LINUX')

        self.__set_host_name(host_name)
        self.__set_user_name(user_name)
        self.__set_password(password)
        self.__set_confirm_password(confirm_password)

        self.__admin_console.submit_form()
        job_id = self.get_jobid_from_screen()
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()
        return job_id


    @PageService()
    def deactivate_laptop(self, client_name):
        """
        Method to deactivate the laptop

        Args:

            client_name (string): client_name of the laptop

        Returns:
            None

        Raises:
            Exception:
                -- if fails to deactivate laptop
        """
        self.__table.access_action_item(client_name, 'Deactivate')
        self.__admin_console.click_button('Yes')
        self.__admin_console.check_error_message()

    @PageService()
    def action_update_software(self, client_name=None, reboot=False):
        """
        To invoke update software method in the laptop page

        Args:
            client_name     (str) -- client to update software on

            reboot         (bool)    -- set to True if reboot required
                                            default: False

        Returns:
            None

        Raises:
            Exception
                --if given input is invalid

                --if there is no update software option for the client

                --if Job failed

        """

        self.__table.access_action_item(client_name, 'Update software')
        if reboot:
            self.__admin_console.toggle_enable('forceReboot')

        self.__admin_console.click_button('Yes')
        job_id = self.get_jobid_from_screen()
        self.__admin_console.click_button("OK")
        self.__admin_console.check_error_message()
        return job_id


    @PageService()
    def action_check_readiness(self, client_name=None):
        """To run check readiness operation on the given client in Laptop page

        Args:
            client_name     (str) -- client on which check readiness to be performed

            Returns:
               None

            Raises:
                Exception

                    if given input is invalid

                    if there is an error message after submitting the request

        """

        self.__table.access_action_item(client_name, 'Check readiness')
        self.__admin_console.check_error_message()


    @PageService()
    def action_retire_client(self, client_name):
        """Retire the given client

        Args:

        client_name     (str) -- client which need to be retired

        Returns:
            None

        Raises:
            Exception
                if client_name is invalid

                if there is an error message after submitting the requestt
        """
        self.__table.access_action_item(client_name, 'Retire')
        self.__admin_console.fill_form_by_id('typedConfirmationRetire', 'Retire')
        self.__admin_console.click_button('Retire')
        job_id = self.__admin_console.get_jobid_from_popup(wait_time=10)
        self.__admin_console.check_error_message()
        return job_id

    @PageService()
    def activate_laptop_byuser(self, client_name):
        """activate the laptop by enduser

        Args:

        client_name     (str) -- client which need to be activated

        Returns:
            None

        Raises:
            Exception
                if client_name is invalid

                if there is an error message after submitting the requestt
        """

        self.__table.access_action_item(client_name, 'Activate')
        self.__admin_console.select_radio(id='user')
        self.__admin_console.click_button('Save')
        self.__admin_console.check_error_message()

    @PageService()
    def activate_laptop_byplan(self, client_name, plan_name):
        """activate the laptop by given plan name

        Args:

        client_name     (str) -- client which need to be activated

        Returns:
            None

        Raises:
            Exception
                if client_name is invalid

                if there is an error message after submitting the requestt
        """
        self.__table.access_action_item(client_name, 'Activate')
        self.__admin_console.select_radio(id='plan')
        if plan_name:
            self.__rdrop_down.select_drop_down_values(0, [plan_name])
        self.__admin_console.click_button('Save')
        self.__admin_console.check_error_message()

    @PageService()
    def subclient_backup_now(self, client_name, backup_type):
        """To perform backup operation

        Args:

        client_name     (str) -- client which need to be retired

        Backup_type    (str)  -- Type the of backup to be performed on client
        (INCR , FULL, SYNTHETIC FULL)

        Returns:
            None

        Raises:
            Exception
                if client_name is invalid

                if there is an error message after submitting the request
        """
        self.__table.access_link(client_name)
        self.__admin_console.wait_for_completion(600)
        i = 1
        while i<=5:
            if self.__admin_console.check_if_entity_exists(
                    "xpath", '//*[@id="deviceDetails"]//button[@aria-label="Backup now"]'):
                break
            time.sleep(60)
            i=i+1
        self.__admin_console.refresh_page()
        self.__admin_console.click_button(value='Backup now')
        job_id = self.__backup.submit_backup(backup_type)
        self.log.info("backup job {0} started to for the client {1}".format(job_id, client_name))
        return job_id


    @PageService()
    def cancel_the_form(self):
        """To perform cancel operation

        Raises:
            Exception

                if unable to click on cancel button
        """

        self.__admin_console.cancel_form()

    @PageService()
    def restore_from_job(self, jobid, source_data_path=None, dest_path=None):
        """
        Method for job based restore

        Args:

             Jobid (str)      : job id to restore the data

             source_data_path(str)   : Sourece data of teh client to be restored

             dest_path(str)         : Destination place to restore the data

        Returns :
              job id  (int) : Job id of the restore job

        Raises:
            Exception :
             -- if fails to run the restore operation

        """
        backup_jobid = str(jobid)
        self.__navigator.navigate_to_jobs()
        if self.__jobs.if_job_exists(backup_jobid):
            self.__jobs.access_job_by_id(backup_jobid)
        else:
            self.__jobs.access_job_history()
            if not self.__jobs.if_job_exists(backup_jobid):
                raise CVWebAutomationException("jobs is not present in Active jobs or job history")
        self.__table.access_action_item(jobid, 'Restore')
        self.__browse.select_path_for_restore(source_data_path)
        self.__browse.submit_for_restore()
        if dest_path:
            self.__admin_console.checkbox_deselect('inplace')
            self.__restore_panel._click_browse()
            self.__admin_console.wait_for_completion() 
            self.__content_browse.select_path(dest_path)
            self.__content_browse.save_path()
        self.__admin_console.submit_form()
        restore_job_id = self.__admin_console.get_jobid_from_popup()
        return restore_job_id
    
    @PageService()
    def select_backuplevel_and_submit_backupjob(self, backup_type, notify=False, v2_laptop=False):
        """
        select the backup type and click on submitt button from modal panel
        
        Args:
        backup_type (BackupType): Type of backup should be one among the types defined in
        BackupType enum
        
        notify (bool)           : to enable by email
        
           Returns:
                    job_id: job id from notification
       """
        
        self.__set_backup_level(backup_type)
        if notify is True:
            self.__checkbox.check(self.__props['label.notifyUserOnJobCompletion'])
        if v2_laptop is False:
            self.__click_backup_submit()
            _jobid = self.__admin_console.get_jobid_from_popup()
            self.__admin_console.wait_for_completion()
            return _jobid
        else:
            self.__click_backup_submit()
            notification = self.__admin_console.get_notification(wait_time=0)
            return notification

    @PageService()
    def backup_from_actions(self, client_name, backup_type):
        """To perform backup operation

        Args:

        client_name     (str) -- client which need to be retired

        Backup_type    (str)  -- Type the of backup to be performed on client
        (INCR , FULL, SYNTHETIC FULL)

        Returns:
            job_id (id)   -- job id

        Raises:
            Exception
                if client_name is invalid

                if there is an error message after submitting the request
        """
        
        self.__table.access_action_item(client_name, 'Backup now')
        self.__admin_console.wait_for_completion()
        job_id = self.select_backuplevel_and_submit_backupjob(backup_type)
        self.log.info("backup job {0} started to for the client {1}".format(job_id, client_name))
        return job_id

    @PageService()
    def backup_from_detailspage(self, client_name, backup_type):
        """To perform backup operation from details page

        Args:

        client_name     (str) -- client which need to be retired

        Backup_type    (str)  -- Type the of backup to be performed on client
        (INCR , FULL, SYNTHETIC FULL)

        Returns:
            job_id (id)   -- job id

        Raises:
            Exception
                if client_name is invalid

                if there is an error message after submitting the request
        """
        
        self.__table.access_link(client_name)
        self.__admin_console.click_button(value='Backup now')
        job_id = self.select_backuplevel_and_submit_backupjob(backup_type)
        self.log.info("backup job {0} started to for the client {1}".format(job_id, client_name))
        return job_id

    @PageService()
    def restore_from_actions(self, client_name, source_data_path=None, dest_path=None):
        """
        Method to Restore the given client data from actions

        Args:

             client_name (str)      : Name of the client

             source_data_path(str)   : Sourece data of teh client to be restored

             dest_path(str)         : Destination place to restore the data

        Returns :
              job id  (int) : Job id of the restore job

        Raises:
            Exception :
             -- if fails to run the restore operation

        """
        self.__table.access_action_item(client_name, 'Restore')
        self.__admin_console.wait_for_completion()
        self.__rbrowse.select_path_for_restore(source_data_path, use_tree=False, admin_mode=True)
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

    @PageService()
    def restore_from_details_page(self, client_name, source_data_path=None, dest_path=None):
        """
        Method to Restore the given client data from details page

        Args:

             client_name (str)      : Name of the client

             source_data_path(str)   : Sourece data of teh client to be restored

             dest_path(str)         : Destination place to restore the data

        Returns :
              job id  (int) : Job id of the restore job

        Raises:
            Exception :
             -- if fails to run the restore operation

        """

        self.__table.access_link(client_name)
        self.__click_on_restore_button()
        self.__rbrowse.select_path_for_restore(source_data_path, use_tree=False, admin_mode=True)
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
    
    @PageService()
    def browse_restore_storage_policies(self, plan_name, client_name):
        """
        Method to restore from all the storage policy copies for the region-based plan

        Args:
              plan_name (str)        : Name of the region-based plan
        """
        self.__navigator.navigate_to_devices()
        self.__table.access_link(client_name)
        self.__admin_console.wait_for_completion()
        self.__admin_console.refresh_page()
        self.__rpanel.click_button('Restore')
        self.__admin_console.wait_for_completion()
        list_of_copies = self.__rbrowse.get_restore_copies_for_plan(plan_name)
        self.log.info(list_of_copies)
        for copy in list_of_copies:
            self.log.info(f"Trying to restore from {copy}")
            self.__admin_console.refresh_page()
            self.__rbrowse.select_action_dropdown_value(copy, 2)
            folder = self.__rbrowse.get_column_data('Name')
            self.__rbrowse.select_path_for_restore(path=folder[0])
            self.__rbrowse.submit_for_restore()
            self.log.info("Submitted for restore")
            self.__rdialog.click_button_on_dialog('Restore')
            restore_job_id = self.__admin_console.get_jobid_from_popup()
            self.log.info(f"Started Restore Job, ID: {restore_job_id}")
            self.__admin_console.wait_for_completion()

    @PageService()
    def is_laptop_exists(self, Laptop_name):
        """ check client entry existence from file server page
        Args:
                Laptop_name     (str) -- Laptop name to search

        returns: boolean
            True: if server exists
            false: if server does not exist
        """
        status = self.__table.is_entity_present_in_column(column_name='Name', entity_name=Laptop_name)
        return status

    @PageService()
    def view_restore_jobs(self, Laptop_name):
        """
        Method to view job history for the client

                Args:
                     Laptop_name (str)      : Name of the device
        """
        self.__table.access_action_item(Laptop_name, "Restore jobs")

    @PageService()
    def access_laptop(self, laptop_name):
        """
        Method to access a laptop client from listing page

        Args:
            laptop_name(str) = name of the device to access
        """
        self.__table.access_link(laptop_name)
        self.__admin_console.wait_for_completion()
        
    @PageService()
    def access_view_jobs(self):
        """
        Method to access job history page from view jobs button of the laptop page

        """
        self.__click_on_viewjobs_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def suspend_job_from_detailspage(self):
        """
        Suspend the backup job from laptop details page
 
        """
        self.__click_on_suspend_button()
        suspend_job_status = self.__job_status_from_backuptile()
        if 'Status Suspended' not in  suspend_job_status:
            raise Exception(" Job status is not showing correctly from backup tile when suspended")
        self.log.info("Backup Job suspended successfully")
            
    @PageService()
    def resume_job_from_detailspage(self):
        """
        resume the backup job from laptop details page
 
        """
        self.__click_on_resume_button()
        self.log.info("Resumed the backup job successfully")

    @PageService()
    def get_users_page_title(self):
        """
        get the user title from user details page
 
        """
        user_title = self.__read_user_title()
        return user_title 
    
    @PageService()
    def delete_from_listingpage(self, client_name):
        """
        Method to delete client

        Args:
            client_name (str) : Name of the client to be deleted

        Raises:
            Exception:
                -- if fails delete client with given name
        """
        self.__table.access_action_item(client_name, 'Delete')
        self.__rdialog.type_text_and_delete("DELETE")
        notification = self.__admin_console.get_notification()
        self.__admin_console.wait_for_completion()
        return notification

