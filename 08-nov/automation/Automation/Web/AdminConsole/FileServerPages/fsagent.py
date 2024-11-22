# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on
all the iDA on the AdminConsole

Class:
    FsAgent

Functions:

    add_backupset()                     -- Adds a new backupset to the Fs iDA.

    view_backup_history()               -- To view backup history of client

    view_restore_history()              -- To view restore history of client

    backup()                            -- To backup selected subclient

    release_license()                   -- Releases license of the client

    restore_recovery_points()           -- Performs a point in time restore

    restore_recovery_point_with_timestamp -- Performs restore from calender at backupset level

    virtualize_me()                     -- Performs a Virtualize Me job.

    add_ibmi_backupset()                -- To add new IBMi backupSet

    instant_clone()                     -- To run Instant Clone for intellisnap subclient

    search_and_restore_files()          -- Restores the selected files after search

    
Class:
    FSSubClient

Functions:

    add_fs_subclient()                  -- Adds a new subclient to the Fs iDA.

    add_ibmi_subclient()                -- Adds a new IBMi subclient.

    restore_nas_subclient()             -- Restores nas subclient

    get_list_of_backupsets()		    -- Method to get the list of backupsets from server page

    is_backupset_exists()			    -- Method to verify if backup set exists from client page

    ibmi_restore_subclient()			--  Restores IBMi data from  selected subclient

    is_ibmi_subclient_exists()          -- Verify the existance of IBMi subclient/s under backupSet

    is_subclient_exists()               --Checks whether the subclient exists or not

    backup_subclient()                  -- backs up the selected subclient

    restore_subclient()                 -- Restores specified subclient

    download_selected_items()           -- Downloads selected files in a subclient

    preview_selected_items()            -- Previews the selected file

    restore_subclient_by_job()          -- Restores specific job in a subclient

    restore_selected_items()           -- Restores specific selected/deleted files

    search_and_restore_files()         -- Restores the selected files after search

    backup_history_subclient()          -- To view backup history of subclient

    delete_subclient()                  -- Deletes the specified subclient

    delete_backup_set()                 -- Deletes the specified backupset


Class:
    _AddBackupset

Functions:

    add_backupset()             -- To create a new backupset


Class:
    _AddSubclient

Functions:

    add_subclient()             -- To create a new subclient

    add_ibmi_subclient()        -- Adds a new IBMi subclient.

"""
import os
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.browse import Browse, ContentBrowse
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.AdminConsole.Components.panel import Backup, RPanelInfo, DropDown, ModalPanel, RDropDown, RModalPanel
from Web.AdminConsole.Components.table import Table , Rtable
from Web.AdminConsole.FileServerPages.file_servers import RestorePanel, AddPanel
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
import time

class FsAgent:
    """
    This class provides the function or operations that can be performed on
    FS Agent on the AdminConsole
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object

        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver

        # Components required
        self.__table = Table(self.__admin_console)
        self.__modal_dialog = ModalDialog(self.__admin_console)
        self.__contentbrowse = ContentBrowse(self.__admin_console)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__backuppanel = Backup(self.__admin_console)
        self.__restore_panel = RestorePanel(self.__admin_console)
        self.__browse = Browse(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rmodal_panel = RModalPanel(self.__admin_console)
        self.fsbackupset = _AddBackupset(self.__admin_console)
        self.__admin_console.load_properties(self)

    @WebAction()
    def _select_backupset_recovery_points(self, backupset_name):
        """To select backupset for recovery points
            Args:
                backupset_name (str)    : Name of the backupset to be selected
        """
        self.__driver.find_element(By.XPATH, 
            f"//div[@class='backup-filter margin-left-10 ng-scope']").click()
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.XPATH, 
            f"//div[@class='backup-filter margin-left-10 ng-scope']//span[text()='{backupset_name}']").click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def add_backupset(self,
                      backup_set,
                      plan,
                      define_own_content=False,
                      browse_and_select_data=False,
                      backup_data=None,
                      impersonate_user=None,
                      exclusions=None,
                      exceptions=None,
                      backup_system_state=False,
                      file_system="Windows",
                      remove_plan_content=False):

        """
        Method to Add New Backupset

        Args:

            backup_set      (string)       :name of the backupset we want to associate
                                            we want to create

            plan           (string)       : plan name to be used as policy for new sub client
                                            backup

            browse_and_select_data(bool)  : Pass True to browse and select data,
                                            False for custom path

            backup_data     (list(paths)) : Data to be backed up by new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']


            exclusions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exclusions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exceptions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exceptions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            backup_system_state (boolean)  :  boolean values to determine if syatem state to
                                            be backed up or not

            file_system       (string)     :  file system of the client
                Eg. - 'Windows' or 'Unix'

            remove_plan_content (bool)      : True for removing content inherited from plan
                                              False for keeping content inherited from plan
        Raises:
            Exception:
                -- if fails to add backupset
        """

        self.fsbackupset.add_backupset(backup_set, plan, define_own_content, browse_and_select_data,
                                       backup_data, impersonate_user, exclusions, exceptions,
                                       backup_system_state, file_system, remove_plan_content)

    @PageService()
    def view_backup_history(self):
        """"Backup history containing jobs of all subclients"""
        self.__admin_console.access_menu_from_dropdown(
            self.__admin_console.props['label.BackupHistory'])

    @PageService()
    def view_restore_history(self):
        """"Restore history containing jobs of all subclients"""
        self.__admin_console.access_menu_from_dropdown(
            self.__admin_console.props['label.RestoreHistory'])

    @PageService()
    def backup(self, backup_level, backupset_name=None, subclient_name=None, notify=False):
        """"Back up option on the title bar
        Args:

             backupset_name (str)   : backup set name of the client

             subclient_name (str)   : subclient to be backed up

             backup_level   (enum)   : type of backup

            notify(bool)           : To notify via mail about the backup

        Returns :
             job_id : Job ID of the backup job

        Raises:
            Exception :

             -- if fails to run the backup
        """
        self.__admin_console.access_menu(self.__admin_console.props['label.globalActions.backup'])
        if backupset_name:
            job_id = self.__backuppanel.submit_backup(backup_level, backupset_name,
                                                      subclient_name, notify)
        else:
            job_id = self.__backuppanel.submit_backup(backup_type=backup_level, notify=notify)

        return job_id
    
    @PageService()
    def restore_recovery_point_with_timestamp(self, calender, dest_client=None,restore_path=None, unconditional_overwrite=False,
        notify=False, search_pattern=None,measure_time = False,include_folders = True, acl = True , data = True , impersonate_user=None, 
        **kwargs):
        """"Point in time restores by selecting the date andfor recovery points

                Args:

                     calender(dict)     : {   'year':     2017,
                                    'month':    december,
                                    'date':     31,
                                    'hours':    09,
                                    'minutes':  19,
                                    'session':  'AM'
                                }

                     dest_client (str)      : Name of the destination client


                     restore_path(str)      : The destination path to which content should be restored to

                     unconditional_overwrite(bool)  : To overwrite unconditionally on destination path

                     notify(bool)           : To notify via mail about the restore

                     search_pattern (str)  : search pattern to search for during browse
                                             As this a backupset level browse to see content for a particular subclient need search pattern 

                     measure_time (bool)    : Measure time in mins to wait for browse to complete. If it exceed raise Exception
                                              3 mins provided as default value
                                              Adding the following flag as we had a TR where browse was taking too long

                     acl (bool)             : To restore ACL or not

                     data(bool)             : Whether or not to restore data

                     impersonate_use (dict) : Whether or not to impersonate user
                    
                     include_folders (bool): True is to include folder while search is applied

                Returns :
                     job_id : job id of the restore

                Raises:
                    Exception :

                     -- if fails to run the restore operation
                     -- if time_limit for browse exceeds parameter passed

        """
        self._select_backupset_recovery_points(kwargs.get('backupset_name','defaultBackupSet'))
        self.__admin_console.date_picker(calender)
        if measure_time:
            start_time = time.time()
            self.__admin_console.tile_select_hyperlink("Recovery point", "Restore")
            elapsed_time = time.time() - start_time
            elapsed_time_minutes = elapsed_time / 60
            if elapsed_time_minutes > 3 :
                raise Exception("Time limit for browse exceeded")
        else :
            self.__admin_console.tile_select_hyperlink("Recovery point", "Restore")

        if search_pattern:
            self.__restore_panel.search_files_for_restore(file_name = search_pattern,include_folders=include_folders)       
        self.__browse.select_for_restore(all_files=True)
        self.__browse.submit_for_restore()
        if dest_client:
            self.__restore_panel.select_destination_client(dest_client)
        
        if not acl:
            self.__restore_panel.deselect_acl_for_restore()

        if not data:
            self.__restore_panel.deselect_data_for_restore()

        if restore_path:
            self.__admin_console.checkbox_deselect("inplace")
            self.__admin_console.fill_form_by_id('restorePath', restore_path)

        if unconditional_overwrite:
            self.__restore_panel.select_overwrite()
        
        if impersonate_user:
            self.__admin_console.enable_toggle(0)
            self.__admin_console.fill_form_by_name("impersonateUserName", impersonate_user['username'])
            self.__admin_console.fill_form_by_name("impersonatePassword", impersonate_user['password'])

        if not impersonate_user and not kwargs.get('ndmp') and kwargs.get('nas', None) and kwargs.get('nfs'):
            job_id = self.__restore_panel.submit_restore(notify, impersonate_dialog=True)
        else:
            job_id = self.__restore_panel.submit_restore(notify)

        return job_id

    @PageService()
    def release_license(self):
        """"Releases license of the client"""
        self.__admin_console.access_menu(self.__admin_console.props['label.releaseLicense'])
        self.__modal_dialog.click_submit()

    @PageService()
    def restore_recovery_points(self, backupset_name, recovery_time, dest_client=None,
                                restore_path=None, unconditional_overwrite=False, notify=False):
        """"Point in time restores by selecting the date for recovery points

                Args:

                     backupset_name (str)   : backup set name of the client

                     recovery_time(str)     : The date specified in DD--MM--YYYY format

                     dest_client (str)      : Name of the destination client

                     restore_path(str)      : The destination path to which content should
                                              be restored to

                     unconditional_overwrite(bool)  : To overwrite unconditionally
                                                      on destination path

                     notify(bool)           : To notify via mail about the restore

                Returns :
                     job_id : job id of the restore

                Raises:
                    Exception :

                     -- if fails to run the restore operation

        """
        self._select_backupset_recovery_points(backupset_name)
        self.__admin_console.recovery_point_restore(recovery_time)
        self.__browse.select_for_restore(all_files=True)
        self.__browse.submit_for_restore()
        if dest_client:
            self.__restore_panel.select_destination_client(dest_client)
        if restore_path:
            self.__restore_panel.select_browse_for_restore_path()
            self.__contentbrowse.select_path(restore_path)
            self.__contentbrowse.save_path()
        if unconditional_overwrite:
            self.__restore_panel.select_overwrite()
        job_id = self.__restore_panel.submit_restore(notify)

        return job_id

    @PageService()
    def virtualize_me(self, backupset_name, recovery_target, deselect_volumes=None, vm_name=None, hostname=None,
                      network_label=None, clone=False, overwrite_vm=False):
        """"Triggers a virtualizeMe job for the client"""

        self.__admin_console.access_menu_from_dropdown(self.__admin_console.props['label.virtualizeMe'])
        self.__admin_console.select_value_from_dropdown(select_id='Backup set', value=backupset_name)
        self.__admin_console.select_value_from_dropdown(select_id='virtualizationTarget', value=recovery_target)

        if vm_name:
            self.__admin_console.fill_form_by_name(name='displayName', value=vm_name)

        if hostname:
            self.__admin_console.fill_form_by_name(name='hostName', value=hostname)

        if network_label:
            self.__admin_console.select_value_from_dropdown(select_id='networkSettings', value=network_label)

        if deselect_volumes:
            self.__dropdown.deselect_drop_down_values(index=0, values=deselect_volumes)

        if clone:
            self.__admin_console.checkbox_select(checkbox_id='cloneSelected')
        if overwrite_vm:
            self.__admin_console.checkbox_select(checkbox_id='overwrite')

        self.__modal_dialog.click_submit()
        job_id = self.__admin_console.get_jobid_from_popup()
        return job_id

    @PageService()
    def add_ibmi_backupset(self, backup_set, plan):
        """        Method to Add New IBMi backupSet

        Args:
            backup_set      (string)      : Backup set name.

            plan           (string)       : plan name to be used as policy for new sub client
                                            backup

        Raises:
            Exception:
                -- if fails to add entity
        """
        self.__admin_console.access_menu_from_dropdown(
            self.__admin_console.props['action.CreateNewBackupset'])
        self.__admin_console.fill_form_by_id("backupSetName", backup_set)
        self.__dropdown.select_drop_down_values(index=0, values=[plan])
        self.__admin_console.click_button_using_text(self.__admin_console.props['OK'])
        self.__admin_console.wait_for_completion()


    @PageService()
    def instant_clone(self, clone_mount_path):
        """Create Instant Clone for FS"""

        self.__browse.select_for_restore(all_files=True)
        self.__admin_console.click_by_xpath("//a[contains(@class,'btn-primary') and contains(text(),'Instant clone')]")
        self.__admin_console.fill_form_by_id("cloneMountPath", clone_mount_path)
        self.__admin_console.click_button(id="fsCloneModalSubmitButton")
        job_id = self.__admin_console.get_jobid_from_popup()
        self.__admin_console.wait_for_completion()
        return job_id

    @PageService()
    def set_workload_region(self,  region):
        """assigns workload region to a file server

        Args:
            region (str): the region name
        """
        self.__rpanel.edit_tile_entity('Workload region')
        self.__rdropdown.select_drop_down_values(drop_down_id="regionDropdown_",
                                                values=[region])
        self.__rpanel.click_button(self.__admin_console.props["label.save"])

    @PageService()
    def get_region(self, region_type):
        """ Method used to get the assigned region for the entity

        Args:
            region_type(str): Workload/ Backup
        returns:
            workload/ Backup region assigned to the entity
        """
        regions = self.__rpanel.get_details()
        if region_type.upper() == "WORKLOAD":
            return regions['Workload region']

        elif region_type.upper() == "BACKUP" and 'Backup destination region' in regions:
            return regions['Backup destination region']
        else:
            return "No region"

    @PageService()
    def set_plan(self, plan):
        """
        Method to assign Plan to a virtual machine

        Args:
            plan(str) = plan name
        """
        self.__rpanel.edit_tile_entity('Plan')
        self.__admin_console.wait_for_completion()
        self.__rdropdown.select_drop_down_values(drop_down_id="subclientPlanSelection", values=[plan])
        self.__admin_console.wait_for_completion()
        self.__rmodal_panel.save()

    @PageService()
    def search_and_restore_files(self, file_name, backupset_name, dest_client=None,
                                 restore_path=None, impersonate_user=None, notify=False, **kwargs):
        """
        Searches files from fsAgentDetails page and restores files from the search results
        
        Args:
            file_name (str) : File name or wildcards to search
            backupset_name (str) : Name of the backupset
            dest_client (str) : Destination client name
            restore_path (str) : Destination path
            impersonate_user (dict) : Dictionary containing username and password for impersonation
            notify (bool) : To notify via mail about the restore
            **kwargs :
                cifs (bool) : True for CIFS agent
                nfs (bool)  : True for NFS agent
        """

        self.__restore_panel.search_files_for_restore(file_name=file_name,
                                                      backupset_name=backupset_name)

        self.__admin_console.wait_for_completion()

        self.__browse.select_for_restore(all_files=True)
        self.__browse.submit_for_restore()

        if dest_client:
            self.__restore_panel.select_destination_client(dest_client)

        if restore_path:
            self.__restore_panel._select_checkbox("inplace")
            self.__admin_console.fill_form_by_id('restorePath', restore_path)

        if impersonate_user:
            self.__admin_console.enable_toggle(0)
            self.__admin_console.fill_form_by_name("impersonateUserName", impersonate_user['username'])
            self.__admin_console.fill_form_by_name("impersonatePassword", impersonate_user['password'])

        if not impersonate_user and not kwargs.get('ndmp') and kwargs.get('nfs'):
            jobid = self.__restore_panel.submit_restore(notify, impersonate_dialog=True)
        else:
            jobid = self.__restore_panel.submit_restore(notify)
        
        return jobid
        
class FsSubclient:

    def __init__(self, admin_console):
        """ Initialize the base panel """

        self.admin_console_base = admin_console
        self.driver = admin_console.driver
        # components required
        self.__table = Table(self.admin_console_base)
        self.__rtable = Rtable(self.admin_console_base)
        self.__modal_dialog = ModalDialog(self.admin_console_base)
        self.__contentbrowse = ContentBrowse(self.admin_console_base)
        self.__rpanel = RPanelInfo(self.admin_console_base)
        self.__backuppanel = Backup(self.admin_console_base)
        self.__restore_panel = RestorePanel(self.admin_console_base)
        self.__browse = Browse(self.admin_console_base)
        self.__plan = Plans(self.admin_console_base)
        self.__plan_details = PlanDetails(self.admin_console_base)
        self.fsubclient = _AddSubclient(self.admin_console_base)
        self.admin_console_base.load_properties(self)
        self.__dropdown = DropDown(self.admin_console_base)
        self.__modal_panel = ModalPanel(self.admin_console_base)

    @PageService()
    def add_fs_subclient(self,
                         backup_set,
                         subclient_name,
                         plan,
                         define_own_content=False,
                         browse_and_select_data=False,
                         backup_data=None,
                         impersonate_user=None,
                         exclusions=None,
                         exceptions=None,
                         file_system='Windows',
                         remove_plan_content=False,
                         toggle_own_content=False):
        """
        Method to Add New Subclient

        Args:
            subclient_name (string)       : Name of the new sub client to be added

            backup_set      (string)       :name of the backupset we want to associate
                                            with the subclient to

            plan           (string)       : plan name to be used as policy for new sub client
                                            backup

            define_own_content  (bool)    : Pass True to define own content
                                            False for associated plan content

            browse_and_select_data(bool)  : Pass True to browse and select data,
                                            False for custom path

            backup_data     (list(paths)) : Data to be backed up by new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            impersonate_user    (string): Specify username (eg: for UNC paths).

            exclusions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exclusions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exceptions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exceptions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            file_system       (string)     :  file system of the client
                Eg. - 'Windows' or 'Unix'

            remove_plan_content (bool)      : True for removing content inherited from plan
                                              False for keeping content inherited from plan

            toggle_own_content  (bool)      : True to toggle override backup content
                                              False for not toggling
        Raises:
            Exception:
                -- if fails to initiate backup
        """

        self.fsubclient.add_subclient(backup_set, subclient_name, plan,
                                      define_own_content, browse_and_select_data,
                                      backup_data, impersonate_user, exclusions,
                                      exceptions, file_system, remove_plan_content, toggle_own_content)

    @PageService()
    def add_nas_subclient(self, subclient_name, subclient_content, nas_plan, exclusions=None, exceptions=None,
                          **kwargs):
        """
        Creates a NAS SubClient

        Args:
            subclient_name  (str)    : Name of the subclient to be created

            subclient_content  (list) (str): Paths on the File Server to be added as backup path

            nas_plan (str)   : Name of the plan used to backup the contents of the subclient

            exclusions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exclusions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exceptions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exceptions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

        """
        self.fsubclient.add_nas(subclient_name, subclient_content, nas_plan,
                                exclusions, exceptions, **kwargs)

    @PageService()
    def add_ibmi_subclient(self,
                           subclient_name,
                           plan,
                           backup_set="defaultBackupSet",
                           save_while_active="*LIB",
                           active_wait_time=0,
                           sync_queue=None,
                           command_to_run=None,
                           define_own_content=False,
                           backup_data=None,
                           exclusions=None,
                           exceptions=None
                           ):
        """
            Method to Add New IBMi Subclient

            Args:
                subclient_name (string)         : Name of the new sub client to be added

                plan           (string)         : plan name to be used as policy for new sub client
                                                backup

                backup_set      (string)        : Name of the backupset

                save_while_active(string)       : save while active options to be used.

                active_wait_time(int)           : Save while active wait time.

                sync_queue      (string)        : Syncronization queue in the format <LIB>/<MSGQ>.

                command_to_run  (string)        : command to run after reaching check-point.

                define_own_content  (bool)    : Pass True to define own content
                                                False for associated plan content

                backup_data     (list(paths)) : Data to be backed up by new sub client created
                    Eg. backup_data = ['/QSYS.LIB/A*.LIB', '/QSYS.LIB/B*.LIB']

                exclusions       (list(paths)) : Data to be backed up by new sub client created
                    Eg. exclusions = ['/QSYS.LIB/ABCD.LIB', '/QSYS.LIB/BCD*.LIB']

                exceptions       (list(paths)) : Data to be backed up by new sub client created
                    Eg. exceptions = ['/QSYS.LIB/BCD1.LIB', '/QSYS.LIB/BCD2.LIB']

            Raises:
                Exception:
                    -- if fails to initiate backup
        """

        self.fsubclient.add_ibmi_subclient(subclient_name,
                                           plan,
                                           backup_set=backup_set,
                                           save_while_active=save_while_active,
                                           active_wait_time=active_wait_time,
                                           sync_queue=sync_queue,
                                           command_to_run=command_to_run,
                                           define_own_content=define_own_content,
                                           backup_data=backup_data,
                                           exclusions=exclusions,
                                           exceptions=exceptions
                                           )

    @WebAction()
    def __choose_backup_set(self, backup_set_name):
        """
        Method to choose backup set

        Args:
            backup_set_name : Name of the back up set
        """
        self.__table.view_by_title(backup_set_name)
        self.admin_console_base.wait_for_completion()

    @PageService()
    def get_list_of_backupsets(self):
        """
        Method to get the list of backupsets from server page

        Returns :
            list of all BackupSets
        """
        return self._get_list_of_backupsets()

    @WebAction()
    def _get_list_of_backupsets(self):
        """
        Method to get the list of backupsets from server page

        Returns :
            list of all backupsets
        """
        self.__table.select_dropdown(label="Backup sets")
        tags = self.driver.find_elements(By.XPATH, "//div[@id='fs-content-group-dropdown']//a")
        backupsets = [each_tag.text for each_tag in tags]
        self.__table.select_dropdown(label="Backup sets")
        return backupsets

    @WebAction()
    def is_backupset_exists(self, backupset_name):
        """
        Method to verify if backup set exists from client page

        Args:
            backup_set_name : Name of the back up set

        Returns :
             status : existance of backupset
                    true/false
        """
        backupset_list = self.get_list_of_backupsets()
        return backupset_name in backupset_list

    @PageService()
    def ibmi_restore_subclient(self, backupset_name, subclient_name, dest_client=None, restore_path=None,
                               unconditional_overwrite=False, selected_files=None):
        """"Restores IBMi data from  selected subclient

        Args:

            backupset_name (str)   : Name of the backup set of the client

            subclient_name (str)   : Name of the subclient

            dest_client (str)      : Name of the destination client

            restore_path(str)      : The destination path to which content should
                          be restored to

             unconditional_overwrite(bool)  : To overwrite unconditionally
                                              on destination path

            selected_files (list)   : list of files or folder to be restored
        Returns :
             job_id : job id of the restore

        Raises:
            Exception :

                -- if fails to run the restore operation
        """
        if backupset_name != 'defaultBackupSet':
            self.__choose_backup_set(backupset_name)
        self.__table.access_action_item(
            subclient_name,
            self.admin_console_base.props['label.globalActions.restore'])
        if selected_files:
            delimiter = '\\'
            paths = os.path.dirname(selected_files[0])
            if '/' in selected_files[0]:
                delimiter = '/'
            if delimiter == '/':
                paths = paths.strip('/')
            paths = paths.split(delimiter)
            select_files = [os.path.basename(file) for file in selected_files]
            for folder in paths:
                self.__browse.access_folder(folder)
            self.__browse.select_for_restore(file_folders=select_files)

        else:
            self.__browse.select_for_restore(all_files=True)
        self.__browse.submit_for_restore()

        if dest_client:
            self.__restore_panel.select_destination_client(dest_client)

        if restore_path:
            self.__restore_panel._select_checkbox("inplace")
            self.admin_console_base.fill_form_by_id("restorePath", restore_path)
        if unconditional_overwrite:
            self.__restore_panel.select_overwrite()
        return self.__restore_panel.submit_restore()

    @PageService()
    def is_ibmi_subclient_exists(self, backup_set,
                                 subclient_name="All"):
        """"        Method to verify the existance of subclient/s under backupSet

        Args:
            backup_set      (string)      : Backup set name.

            subclient_name (string)       : Name of the subclient of verify all auto-created
                                            subclients

        Raises:
            Exception:
                -- if fails to find auto-created subclients.
        Return:
            status:
             --True or False
        """
        self.__choose_backup_set(backup_set)
        result = None
        if subclient_name == "All":
            subclient_names = ['*ALLDLO', '*ALLUSR', '*CFG', '*HST log', '*IBM', '*LINK', '*SECDTA']
            if "defaultBackupSet" in backup_set:
                subclient_names.append('DR Subclient')
            for each in subclient_names:
                result = self.is_subclient_exists(each)
                if not result:
                    raise CVWebAutomationException("subclient {0} doesnt exist under backupset "
                                                   "{1}".format(each, backup_set))
        else:
            result = self.is_subclient_exists(subclient_name)
        return result

    @PageService()
    def is_subclient_exists(self, subclient_name):
        """ Checks whether the subclient exists or not
        Args:
            subclient_name (str): name of the subclient

        Returns :
            -- bool value True(if subclient exists)
                          False(if subclient doesn't exist)
        """
        subclient_names = self.__table.get_column_data('Name', fetch_all=True)
        if subclient_name in subclient_names:
            return True
        else:
            return False

    @PageService()
    def backup_subclient(self, backupset_name, subclient_name, backup_type, notify=False):
        """" Runs backup for the selected subclient
        Args:

             backupset_name (str)   : backup set name of the client

             subclient_name (str)   : subclient to be backed up

             backup_level   (enum)   : type of backup

            notify(bool)           : To notify via mail about the backup

        Returns :
             job_id : Job ID of the backup job

        Raises:
            Exception :

             -- if fails to run the backup
        """
        if backupset_name != 'defaultBackupSet':
            self.__choose_backup_set(backupset_name)
        self.__table.access_action_item(
            subclient_name, self.admin_console_base.props['label.globalActions.backup'])
        job_id = self.__backuppanel.submit_backup(backup_type=backup_type, notify=notify)

        return job_id

    @PageService()
    def restore_subclient(self, backupset_name, subclient_name, dest_client=None, diff_os=False,
                          acl=True, data=True, restore_aux_copy=False, storage_copy_name=None,
                          plan_name=None, restore_path=None,
                          unconditional_overwrite=False, notify=False, selected_files=None,
                          impersonate_user=None, **kwargs):
        """"Restores the selected subclient

        Args:

             dest_client (str)      : Name of the destination client

             diff_os (bool)         : If the destination machine is of same os_type
                                      as client the value is False
                                      If the destination machine is of different os_type
                                      as client the value is True

             acl    (bool)          : to select access control list option is True
                                      and to disable acl is False

             data    (bool)          : To select data option it is true
                                      else false

             restore_aux_copy(bool) : True if trigger restore from aux copy
                                      else False

             storage_copy_name(str) : The name of the storage copy name

             plan_name(str)         : The name of the plan

             restore_path(str)      : The destination path to which content should
                                      be restored to

             backupset_name (str)   : backup set name of the client

             subclient_name (str)   : subclient name

             unconditional_overwrite(bool)  : To overwrite unconditionally
                                              on destination path

             notify(bool)           : To notify via mail about the restore
            selected_files (list)   : list of files or folder to be restored
            impersonate_user (dict): Dict consisting of {"username": None, "password": None}

            kwargs (dict)                    -- dictionary of optional arguments
                Available kwargs Options:

                    blocklevel               (bool)   --  option to enable blocklevel
                        default: False

                    filelevel                (bool)   --  option to enable File level restore
                        default: False

                    volumelevel              (bool)   --  option to enable Volume level restore
                        default: False
        Returns :
             job_id : job id of the restore

        Raises:
            Exception :

                -- if fails to run the restore operation
        """
        if backupset_name != 'defaultBackupSet':
            self.__choose_backup_set(backupset_name)
        self.__table.access_action_item(
            subclient_name,
            self.admin_console_base.props['label.globalActions.restore'])

        self.admin_console_base.wait_for_completion()
        
        if restore_aux_copy:
            self.__browse.select_adv_options_submit_restore(storage_copy_name,
                                                            plan_name)

        if kwargs.get('blocklevel'):
            if kwargs.get('filelevel'):
                self.admin_console_base.click_by_id('fileLevelRestore')
            if kwargs.get('volumelevel'):
                self.admin_console_base.click_by_id('fileLevelRestore')
        if selected_files:
            delimiter = '\\'
            paths = os.path.dirname(selected_files[0])
            if paths:
                if '/' in selected_files[0]:
                    delimiter = '/'
                if delimiter == '/':
                    paths = paths.strip('/')
                    paths = paths.strip(':')
                paths = paths.split(delimiter)

                if kwargs.get('cifs'):
                    paths[0] = '\\\\' + paths[0]
                for folder in paths:
                    self.__browse.access_folder(folder.strip(':'))
            select_files = [os.path.basename(file) for file in selected_files]
            self.__browse.select_for_restore(file_folders=select_files)

        else:
            self.__browse.select_for_restore(all_files=True)
        self.__browse.submit_for_restore()
        self.admin_console_base.wait_for_completion()

        if dest_client:
            self.__restore_panel.select_destination_client(dest_client)

        if not acl:
            self.__restore_panel.deselect_acl_for_restore()

        if not data:
            self.__restore_panel.deselect_data_for_restore()

        if restore_path:
            self.admin_console_base.checkbox_deselect("inplace")

            # Acl is deselected when deselecting inplace
            if acl and kwargs.get('nas'):
                elem1 = self.driver.find_elements(By.XPATH,
                    "//*[@id='acls' and contains(@class,'ng-empty')]")
                if elem1:
                    self.__restore_panel.deselect_acl_for_restore()
            if ((kwargs.get('cifs') or kwargs.get('nfs')) and paths[0] in restore_path) or kwargs.get('ndmp'):
                self.admin_console_base.fill_form_by_id('restorePath', restore_path)
            else:
                if not diff_os:
                    self.__restore_panel.select_browse_for_restore_path(toggle_inplace=False)
                else:
                    self.__restore_panel.select_browse_in_restore()
                self.__contentbrowse.select_path(restore_path)
                self.__contentbrowse.save_path()

        if unconditional_overwrite:
            self.__restore_panel.select_overwrite()

        if impersonate_user:
            self.admin_console_base.enable_toggle(0)
            self.admin_console_base.fill_form_by_name("impersonateUserName", impersonate_user['username'])
            self.admin_console_base.fill_form_by_name("impersonatePassword", impersonate_user['password'])

        if not impersonate_user and not kwargs.get('ndmp') and kwargs.get('nas', None) and kwargs.get('nfs'):
            return self.__restore_panel.submit_restore(notify, impersonate_dialog=True)

        return self.__restore_panel.submit_restore(notify, impersonate_dialog=False)

    @PageService()
    def download_selected_items(self, subclient_name, backupset_name='defaultBackupSet',
                                download_files=None, file_system='Windows',
                                dest_client=None, restore_path=None, diff_os=False,
                                version_nums=None, files_size=0,
                                unconditional_overwrite=False, notify=False):
        """Downloads the selected file/folders
        Args:
            download_files (list(files)) : files to be downloaded

            backupset_name (str)   : backup set name of the client

            subclient_name (str)   : subclient name

            file_system (str): file system of the client

            dest_client (str)      : Name of the destination client

            restore_path(str)      : The destination path to which content should
                                      be restored to

            diff_os (bool)         : If the destination machine is of same os_type
                                      as client the value is False
                                      If the destination machine is of different os_type
                                      as client the value is True

            version_nums (list): To download the specified version of file
                               (eg - ['1', '2'])

            files_size   (int): Size of the files to be downloaded (in MB)

            unconditional_overwrite(bool)  : To overwrite unconditionally
                                              on destination path

            notify(bool)           : To notify via mail about the restore
        """
        if backupset_name != 'defaultBackupSet':
            self.__choose_backup_set(backupset_name)
        self.__table.access_action_item(
            subclient_name,
            self.admin_console_base.props['label.globalActions.restore'])
        if file_system == 'Windows':
            delimiter = '\\'
            concat = 0
        else:
            delimiter = '/'
            concat = 1

        if download_files:
            if version_nums:
                self.__browse.select_multiple_version_of_files(download_files[0][concat:],
                                                               version_nums)
            else:
                paths = os.path.dirname(download_files[0])
                if delimiter == '/':
                    paths = paths.strip('/')
                paths = paths.split(delimiter)
                select_files = [os.path.basename(file) for file in download_files]
                for folder in paths:
                    self.__browse.access_folder(folder)
                    self.admin_console_base.wait_for_completion()
                self.__browse.select_for_restore(file_folders=select_files)

            notification = self.__browse.submit_for_download()
            self.admin_console_base.wait_for_completion()

            if files_size > 1024:
                msg = "Downloads are not available for selections larger than 1.00 GB." + \
                      " Please use the restore option instead."
                if not notification == msg:
                    raise CVWebAutomationException(notification)

                if dest_client:
                    self.__restore_panel.select_destination_client(dest_client)

                if restore_path:
                    if not diff_os:
                        self.__restore_panel.select_browse_for_restore_path()
                    else:
                        self.__restore_panel.select_browse_in_restore()
                    self.__contentbrowse.select_path(restore_path)
                    self.__contentbrowse.save_path()

                if unconditional_overwrite:
                    self.__restore_panel.select_overwrite()

                return self.__restore_panel.submit_restore(notify)

            else:
                return ""

    @PageService()
    def preview_selected_items(self, subclient_name, backupset_name='defaultBackupSet',
                               preview_file_path=None):
        """Preview the selected file
        Args:
            preview_file_path (str) : file to be selected to preview

            backupset_name (str)   : backup set name of the client

            subclient_name (str)   : subclient name

        """
        if backupset_name != 'defaultBackupSet':
            self.__choose_backup_set(backupset_name)
        self.__table.access_action_item(
            subclient_name,
            self.admin_console_base.props['label.globalActions.restore'])

        if preview_file_path:
            self.__browse.select_for_preview(preview_file_path)
            self.admin_console_base.wait_for_completion()
            self.__browse.close_preview_file()

    @PageService()
    def navigate_to_job_details_for_subclient_for_jobid(self,backupset_name,subclient_name,job_id):
        """Open up the job details page for the selected job in subclient
        
        Args : 
        
             job_id(str)            : job_id of the backup job to be restored

             backupset_name (str)   : backup set name of the client

             subclient_name (str)   : subclient name
        Returns :
            None
        Raises:
            Exception :
                -- if fails to find the job_id
                -- if fails to get job ids from table
        """
        self.backup_history_subclient(backupset_name, subclient_name)
        job_ids = self.__table.get_column_data('Job Id')
        if job_ids:
            if job_id in job_ids:
                self.__table.access_action_item(job_id, "View job details")
            else :
                raise Exception("The given job id %s does not exist",job_id)
        else : 
            raise Exception("Job Id could not be picked up from the table")
        

    @PageService()
    def restore_subclient_by_job(self, backupset_name, subclient_name, job_id,
                                 dest_client=None, diff_os=False, restore_path=None,
                                 unconditional_overwrite=False, notify=False, selected_files=None,
                                 impersonate_user=None,**kwargs):
        """ Restores the selected job in subclient

        Args:

             dest_client (str)      : Name of the destination client

             diff_os (bool)         : If the destination machine is of same os_type
                                      as client the value is False
                                      If the destination machine is of different os_type
                                      as client the value is True

             restore_path(str)      : The destination path to which content
                                      should be restored to

             job_id(str)            : job_id of the backup job to be restored

             backupset_name (str)   : backup set name of the client

             subclient_name (str)   : subclient name

             unconditional_overwrite(bool)  : To overwrite unconditionally
                                              on destination path

             notify(bool)           : To notify via mail about the restore
            selected_files (list)   : list of files or folders to be restored
        Returns :
             job_id : job id of the restore

        Raises:
            Exception :
                -- if fails to find the job_id
                -- if fails to run the restore operation
        """
        self.backup_history_subclient(backupset_name, subclient_name)
        rows_count = self.__rtable.get_total_rows_count(job_id)

        if rows_count != 0:
            self.__rtable.access_action_item(job_id, "Restore")
            if selected_files:
                delimiter = '\\'
                paths = os.path.dirname(selected_files[0])
                if paths:
                    if '/' in selected_files[0]:
                        delimiter = '/'
                    if delimiter == '/':
                        paths = paths.strip('/')
                        paths = paths.strip(':')
                    paths = paths.split(delimiter)

                if kwargs.get('cifs'):
                    paths = paths[2:]
                    paths[0] = '\\\\' + paths[0]

                for folder in paths:
                    self.__browse.access_folder(folder.strip(':'))
                select_files = [os.path.basename(file) for file in selected_files]
                self.__browse.select_for_restore(file_folders=select_files)

            else:
                self.__browse.select_for_restore(all_files=True)
            self.__browse.submit_for_restore()

            if dest_client:
                self.__restore_panel.select_destination_client(dest_client)

            if restore_path:
                self.admin_console_base.checkbox_deselect("inplace")
                if kwargs.get('cifs') or kwargs.get('nfs') or kwargs.get('ndmp'):
                    self.admin_console_base.fill_form_by_id('restorePath', restore_path)
                else:
                    self.__restore_panel.select_browse_for_restore_path(toggle_inplace=False)
                    self.__contentbrowse.select_path(restore_path)
                    self.__contentbrowse.save_path()

            if unconditional_overwrite:
                self.__restore_panel.select_overwrite()

            if impersonate_user:
                self.admin_console_base.enable_toggle(0)
                self.admin_console_base.fill_form_by_name("impersonateUserName", impersonate_user['username'])
                self.admin_console_base.fill_form_by_name("impersonatePassword", impersonate_user['password'])

            if not impersonate_user and not kwargs.get('ndmp') and kwargs.get('nfs'):
                jobid = self.__restore_panel.submit_restore(notify, impersonate_dialog=True)
            else:
                jobid = self.__restore_panel.submit_restore(notify)

        else:
            raise Exception("No such job_id found")

        return jobid

    @PageService()
    def restore_selected_items(self, backupset_name, subclient_name, del_file_content_path=None,
                               selected_files=None, dest_client=None, diff_os=False,
                               restore_path=None, unconditional_overwrite=False,
                               notify=False, select_hidden_files=None, modified_file=None,
                               version_nums=[], file_system='Windows', impersonate_user=None, **kwargs):
        """ Restores the deleted/selected/hidden/modified files in backup content

        Args:

            dest_client (str):      Name of the destination client

            diff_os (bool)         : If the destination machine is of same os_type
                                     as client the value is False
                                     If the destination machine is of different os_type
                                     as client the value is True

            restore_path(str): The destination path to which content
                               should be restored to
                               (eg - 'C:\\Restore' or '/opt/Restore')

            del_file_content_path(str): to restore deleted files from a particular path
                                           (eg - 'C:\\Test' or '/opt/Test')

            selected_files (list(file_paths)): list of selected files to be restored
                                               (all selected files should have same
                                                folder_path)
                                               (eg - ['C:\\Test\\1.html',
                                                      'C:\\Test\\2.html'] or
                                                  ['/opt/Test/1.html, '/opt/Test/2.html''])

            select_hidden_files (list(file_paths)): list of hidden files to be selected
                                                    (eg - ['C:\\Test\\1.html',
                                                           'C:\\Test\\2.html']
                                                    or   ['/opt/Test/1.html,
                                                          '/opt/Test/2.html''])

            modified_file(str): to restore modified file from a particular path
                                (eg - 'C:\\Test\\file.txt' or
                                      '/opt/Test/file.txt')

            version_nums(list(str(version_no))): To select the specified version
                                                 (eg - ['1', '2'])

            backupset_name (str)   : backup set name of the client

            subclient_name (str)   : subclient name

            unconditional_overwrite(bool)  : To overwrite unconditionally
                                             on destination path

            notify(bool)           : To notify via mail about the restore

            file_system (str): file system of the client

        Returns :
            job_id : job id of the restore

        Raises:
            Exception :

                -- if fails to run the restore operation
        """
        if backupset_name != 'defaultBackupSet':
            self.__choose_backup_set(backupset_name)
        self.__table.access_action_item(
            subclient_name,
            self.admin_console_base.props['label.globalActions.restore'])

        if file_system == 'Windows':
            delimiter = '\\'
            concat = 0
        else:
            delimiter = '/'
            concat = 1

        if modified_file:
            if len(version_nums) == 0:
                version_nums = ['1']
            self.__browse.select_multiple_version_of_files(modified_file[concat:],
                                                           version_nums)
        if del_file_content_path:
            self.__browse.select_deleted_items_for_restore(del_file_content_path[concat:],
                                                           delimiter)
        if select_hidden_files:
            self.__browse.select_hidden_items(select_hidden_files, delimiter)

        if selected_files:
            paths = os.path.dirname(selected_files[0])
            if delimiter == '/':
                paths = paths.strip('/')
            paths = paths.split(delimiter)

            if kwargs.get('cifs'):
                paths[0] = '\\\\' + paths[0]

            select_files = [os.path.basename(file) for file in selected_files]
            for folder in paths:
                self.__browse.access_folder(folder)
            self.__browse.select_for_restore(file_folders=select_files)

        self.__browse.submit_for_restore()

        if dest_client:
            self.__restore_panel.select_destination_client(dest_client)

        if restore_path:

            if kwargs.get('cifs') or kwargs.get('nfs') or kwargs.get('ndmp'):
                self.admin_console_base.checkbox_deselect("inplace")
                self.admin_console_base.fill_form_by_id('restorePath', restore_path)
            else:
                if not diff_os:
                    self.__restore_panel.select_browse_for_restore_path()
                else:
                    self.__restore_panel.select_browse_in_restore()
                self.__contentbrowse.select_path(restore_path)
                self.__contentbrowse.save_path()

        if unconditional_overwrite:
            self.__restore_panel.select_overwrite()
        
        if impersonate_user:
            self.admin_console_base.enable_toggle(0)
            self.admin_console_base.fill_form_by_name("impersonateUserName", impersonate_user['username'])
            self.admin_console_base.fill_form_by_name("impersonatePassword", impersonate_user['password'])

        if not impersonate_user and not kwargs.get('ndmp') and kwargs.get('nfs'):
            return self.__restore_panel.submit_restore(notify, impersonate_dialog=True)

        return self.__restore_panel.submit_restore(notify)

    @PageService()
    def search_and_restore_files(self, backupset_name, subclient_name, dest_client=None,
                                 diff_os=False, file_name=None, match_string=None, file_type=None,
                                 modified_time=None, from_time=None, to_time=None,
                                 include_folders=True, show_deleted_files=True, restore_path=None,
                                 unconditional_overwrite=False, notify=False):
        """"Restores the selected files after search

        Args:
             backupset_name (str)   : backup set name of the client

             subclient_name (str)   : subclient name

             dest_client (str)      : Name of the destination client

             diff_os (bool)         : If the destination machine is of same os_type
                                      as client the value is False
                                      If the destination machine is of different os_type
                                      as client the value is True

             file_name (String): Name of file to be searched
                                (eg:'file.txt', 'test.html')

             match_string  (String): pattern string that the files contain
                                (eg:'html', 'automation')

             file_type  (String): The type of the file to be searched
                                 (eg:'Audio', 'Image', 'Office', 'Video',
                                     'System', 'Executable')

             modified_time   (String): Modified time of file to be searched
                                 (eg:'Today', 'Yesterday', 'This week')

             from_time   (str): The files backed up from date(eg: 01-April-2020)

             to_time     (str): The files backed up to this date(eg: 01-April-2020)

             include_folders (bool): True is to include folder while search is applied

             show_deleted_files (bool): True is to apply search for deleted items

             restore_path(str)      : The destination path to which content should
                                      be restored to

             unconditional_overwrite(bool)  : To overwrite unconditionally
                                              on destination path

             notify(bool)           : To notify via mail about the restore

        Returns :
             job_id : job id of the restore

        """
        if backupset_name != 'defaultBackupSet':
            self.__choose_backup_set(backupset_name)
        self.__table.access_action_item(
            subclient_name,
            self.admin_console_base.props['label.globalActions.restore'])
        self.__restore_panel.search_files_for_restore(file_name, match_string, file_type,
                                                      modified_time, from_time, to_time,
                                                      include_folders, show_deleted_files)
        self.__browse.select_for_restore(all_files=True)
        self.__browse.submit_for_restore()

        if dest_client:
            self.__restore_panel.select_destination_client(dest_client)

        if restore_path:
            if not diff_os:
                self.__restore_panel.select_browse_for_restore_path()
            else:
                self.__restore_panel.select_browse_in_restore()
            self.__contentbrowse.select_path(restore_path)
            self.__contentbrowse.save_path()

        if unconditional_overwrite:
            self.__restore_panel.select_overwrite()

        return self.__restore_panel.submit_restore(notify)

    @PageService()
    def backup_history_subclient(self, backupset_name, subclient_name):
        """" Backup history of the subclient
                Args:

                     backupset_name (str)   : backup set name of the client

                     subclient_name (str)   : subclient name

        """
        if backupset_name != 'defaultBackupSet':
            self.__choose_backup_set(backupset_name)
        self.__table.access_action_item(
            subclient_name, self.admin_console_base.props['label.BackupHistory'])

    @PageService()
    def delete_subclient(self, backupset_name, subclient_name):
        """" Delete subclient
                Args:

                     backupset_name (str)   : backup set name of the client

                     subclient_name (str)   : subclient name

        """
        if backupset_name != 'defaultBackupSet':
            self.__choose_backup_set(backupset_name)
        if self.__table.is_entity_present_in_column('Name', subclient_name):
            self.__table.access_action_item(
                subclient_name, self.admin_console_base.props['action.delete'])
            if self.admin_console_base.check_if_entity_exists("xpath", "//div[contains(@class, 'form-group')]//input"):
                self.__modal_dialog.type_text_and_delete('DELETE')
            else:
                self.__modal_dialog.click_submit()
        self.admin_console_base.wait_for_completion()

    @PageService()
    def access_subclient(self, backupset_name, subclient_name):
        """" Access the subclient
                Args:

                     backupset_name (str)   : backup set name of the client

                     subclient_name (str)   : subclient name

        """
        if backupset_name != 'defaultBackupSet':
            self.__choose_backup_set(backupset_name)
        self.__table.access_link(subclient_name)
        self.admin_console_base.wait_for_completion()

    @PageService()
    def access_subclient_tab(self):
        """Access subclient tab"""
        self.admin_console_base.select_hyperlink('Subclients')

    @PageService()
    def delete_backup_set(self, backup_set_name):
        """
        Method to delete backup set

        Args:
            backup_set_name : Name of the back up set
        """
        if backup_set_name != 'defaultBackupSet':
            self.__choose_backup_set(backup_set_name)
        self.admin_console_base.select_hyperlink("Delete backup set")
        self.__modal_dialog.type_text_and_delete('DELETE')

    @PageService()
    def access_cifs(self):
        """Accesses the CIFS protocol page for NAS"""
        self.admin_console_base.select_hyperlink('CIFS')

    @PageService()
    def access_nfs(self):
        """Accesses the CIFS protocol page for NAS"""
        self.admin_console_base.select_hyperlink('NFS')

    @PageService()
    def select_instant_clone(self, subclient_name):
        """Select Instant Clone at subclient level"""
        self.__table.access_action_item(subclient_name, self.admin_console_base.props['action.commonAction.instantClone'])


class _AddBackupset(AddPanel):

    def __init__(self, admin_console):
        """
        Args:
        admin_console(AdminConsole): adminconsole
        object
        """
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.__driver = admin_console.driver

    @PageService()
    def add_backupset(self,
                      backup_set,
                      plan,
                      define_own_content=False,
                      browse_and_select_data=None,
                      backup_data=None,
                      impersonate_user=None,
                      exclusions=None,
                      exceptions=None,
                      backup_system_state=False,
                      file_system="Windows",
                      remove_plan_content=False):
        """"        Method to Add New Subclient

        Args:
            backup_set      (string)      : Backup set name.

            plan           (string)       : plan name to be used as policy for new sub client
                                            backup

            define_own_content(bool) :     Pass True to define own content
                                           False for associated plan content

            browse_and_select_data(bool)  : Pass True to browse and select data,
                                            False for custom path

            backup_data     (list(paths)) : Data to be backed up by new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            impersonate_user    (string): Specify username (eg: for UNC paths).

            exclusions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exclusions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exceptions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exceptions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            backup_system_state (String)      : System state to be enabled or not.

            file_system       (string)     :  file system of the client
                Eg. - 'Windows' or 'Unix'

            remove_plan_content (bool)      : True for removing content inherited from plan
                                              False for keeping content inherited from plan
        Raises:
            Exception:
                -- if fails to add entity
        """

        self.__admin_console.access_menu_from_dropdown(
            self.__admin_console.props['action.CreateNewBackupset'])
        self.__admin_console.fill_form_by_id("backupSetName", backup_set)

        self.add(plan, define_own_content, browse_and_select_data, backup_data,
                 impersonate_user, exclusions, exceptions, backup_system_state,
                 file_system, remove_plan_content, True)


class _AddSubclient(AddPanel):

    def __init__(self, admin_console):

        """
        Args:
        admin_console(AdminConsole): adminconsole
        object
        """
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__dropdown = DropDown(self.__admin_console)
        self.__modal_panel = ModalPanel(self.__admin_console)

    @PageService()
    def add_subclient_name_and_plan(self, subclient_name, plan_name=None):
        """Selects the subclient name and plan for it"""
        self.__admin_console.select_hyperlink(
            self.__admin_console.props['action.subclientCreation'])
        self.__admin_console.fill_form_by_id("contentGroupName", subclient_name)
        if plan_name:
            self.select_plan(plan_name)

    @PageService()
    def add_nas(self,
                subclient_name,
                subclient_content,
                nas_plan,
                exclusions=None,
                exceptions=None,
                impersonate_user=None
                ):
        """
        Creates a NAS SubClient

        Args:
            subclient_name  (str)    : Name of the subclient to be created

            subclient_content  (list) (str): Paths on the File Server to be added as backup path

            nas_plan (str)   : Name of the plan used to backup the contents of the subclient

            exclusions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exclusions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exceptions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exceptions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']
            impersonate_user (str or dict with username and password keys): user credentials to impersonate client as
        """

        self.add_subclient_name_and_plan(subclient_name, nas_plan)
        self.set_custom_content(subclient_content)
        if impersonate_user:
            self.__admin_console.select_hyperlink(
                self.__admin_console.props['label.impersonateUser'])
            self.set_impersonate_user_credentials(impersonate_user)

        if exclusions:
            self.__admin_console.select_hyperlink(
                self.__admin_console.props['label.Exclusions'])
            self.set_custom_content(exclusions)

        if exceptions:
            self.__admin_console.select_hyperlink(
                self.__admin_console.props['label.Exceptions'])
            self.set_custom_content(exceptions)

        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @PageService()
    def add_subclient(self,
                      backup_set,
                      subclient_name,
                      plan,
                      define_own_content=False,
                      browse_and_select_data=None,
                      backup_data=None,
                      impersonate_user=None,
                      exclusions=None,
                      exceptions=None,
                      file_system="Windows",
                      remove_plan_content=False,
                      toggle_own_content=True):
        """"function to add subclient

            plan           (string)       : plan name to be used as policy for new sub client
                                            backup

            browse_and_select_data(bool)  : Pass True to browse and select data,
                                            False for custom path

            backup_data     (list(paths)) : Data to be backed up by new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']


            exclusions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exclusions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exceptions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exceptions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            file_system       (string)     :  file system of the client
                Eg. - 'Windows' or 'Unix'

            remove_plan_content (bool)      : True for removing content inherited from plan
                                              False for keeping content inherited from plan

            toggle_own_content  (bool)      : Pass True to toggle override backup content
                                              False for not toggling

        Raises:
            Exception:
                -- if fails to add entity
        """

        self.add_subclient_name_and_plan(subclient_name)
        if backup_set != 'defaultBackupSet':
            self.__dropdown.select_drop_down_values(0, [backup_set])

        self.add(plan=plan, define_own_content=define_own_content,
                 browse_and_select_data=browse_and_select_data,
                 backup_data=backup_data, impersonate_user=impersonate_user,
                 exclusions=exclusions, exceptions=exceptions,
                 file_system=file_system, remove_plan_content=remove_plan_content,
                 toggle_own_content=toggle_own_content, submit=True)

    @PageService()
    def add_ibmi_subclient(self,
                           subclient_name,
                           plan,
                           backup_set="defaultBackupSet",
                           save_while_active="*LIB",
                           active_wait_time=0,
                           sync_queue=None,
                           command_to_run=None,
                           define_own_content=False,
                           backup_data=None,
                           exclusions=None,
                           exceptions=None
                           ):
        """
            Method to Add New IBMi Subclient

            Args:
                subclient_name (string)         : Name of the new sub client to be added

                plan           (string)         : plan name to be used as policy for new sub client
                                                backup

                backup_set      (string)        : Name of the backupset

                save_while_active(string)       : save while active options to be used.

                active_wait_time(int)           : Save while active wait time.

                sync_queue      (string)        : Syncronization queue in the format <LIB>/<MSGQ>.

                command_to_run  (string)        : command to run after reaching check-point.

                define_own_content  (bool)    : Pass True to define own content
                                                False for associated plan content

                backup_data     (list(paths)) : Data to be backed up by new sub client created
                    Eg. backup_data = ['/QSYS.LIB/A*.LIB', '/QSYS.LIB/B*.LIB']

                exclusions       (list(paths)) : Data to be backed up by new sub client created
                    Eg. exclusions = ['/QSYS.LIB/ABCD.LIB', '/QSYS.LIB/BCD*.LIB']

                exceptions       (list(paths)) : Data to be backed up by new sub client created
                    Eg. exceptions = ['/QSYS.LIB/BCD1.LIB', '/QSYS.LIB/BCD2.LIB']

            Raises:
                Exception:
                    -- if fails to initiate backup
        """
        self.__admin_console.select_hyperlink(
            self.__admin_console.props['action.subclientCreation'])
        self.__admin_console.fill_form_by_id("subclientName", subclient_name)
        if backup_set != 'defaultBackupSet':
            self.__dropdown.select_drop_down_values(0, [backup_set])

        self.__admin_console.select_value_from_dropdown(select_id='saveWhileActive', value=save_while_active)
        if save_while_active != "*NO":
            self.__admin_console.fill_form_by_id("activeWaitTime", active_wait_time)

        if save_while_active == "*SYNCLIB":
            if sync_queue is not None:
                self.__admin_console.fill_form_by_id("syncQueue", sync_queue)
            if command_to_run is not None:
                self.__admin_console.fill_form_by_id("commandToRun", command_to_run)

        self.__dropdown.select_drop_down_values(1, [plan])

        if define_own_content:
            self.__modal_panel._expand_accordion(name="Content")
            self.__admin_console.wait_for_completion()
            self.__driver.find_element(By.ID, 'createFsSubclient_button_#9980').click()
            self.__admin_console.wait_for_completion()
            self.__admin_console.select_value_from_dropdown(select_id='content', value="Custom content")

            if backup_data is not None:
                self.__driver.find_element(By.ID, 'manageFSSubclientContentModal_button_#4693').click()
                self.__admin_console.wait_for_completion()
                self.__admin_console.fill_form_by_id("addMultipleContentTextarea",
                                                        '\n'.join([str(elem) for elem in backup_data]))
                self.__admin_console.click_button(self.__admin_console.props['OK'])
                if exclusions is not None:
                    self.__modal_panel._expand_accordion(name="Exclusions")
                    self.__admin_console.wait_for_completion()
                    self.__driver.find_element(By.ID, 'manageFSSubclientContentModal_button_#0995').click()
                    self.__admin_console.fill_form_by_id("addMultipleContentTextarea",
                                                            '\n'.join([str(elem) for elem in exclusions]))
                    self.__admin_console.click_button(self.__admin_console.props['OK'])

                if exceptions is not None:
                    self.__modal_panel._expand_accordion(name="Exceptions")
                    self.__admin_console.wait_for_completion()
                    self.__driver.find_element(By.ID, 'manageFSSubclientContentModal_button_#5679').click()
                    self.__admin_console.wait_for_completion()
                    self.__admin_console.fill_form_by_id("addMultipleContentTextarea",
                                                            '\n'.join([str(elem) for elem in exclusions]))
                    self.__admin_console.click_button(self.__admin_console.props['OK'])
                self.__admin_console.click_button(self.__admin_console.props['OK'])
        self.__admin_console.click_button(self.__admin_console.props['Save'])
