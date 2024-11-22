from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
subclient of the File System agent on the AdminConsole

Class:
    FsSubclientDetails

Functions:


    backup_history()               -- To view backup history of client

    restore_history()              -- To view restore history of client

    backup()                       -- To backup selected subclient

    delete_subclient()             --  To delete the subclient

    restore_recovery_point_with_timestamp() -- Performs a restore from calender with timestamp

    restore_recovery_points()      -- Performs a point in time restore

    assign_plan()                  -- To assign a plan to a subclient

    set_backup_activity()          -- Enable or disable the data backup option

    set_pre_backup_command()       -- Sets the pre backup process

    set_post_backup_command()      --  Sets the post backup process

    set_pre_post_advanced()        -- To set pre and post process scan/backup commands.

    clear_pre_post_commands()      --  Clears the pre post commands set already

    edit_content()                 -- edit the content of the subclient for backup

    enable_snapshot_engine()       -- Sets the snapshot engine for the subclient

    set_block_level()              -- To set block level option

    set_block_level_file_indexing() -- To set block level File indexing option
    
    mount_multiple_snaps_subclient_level() -- To mount multiple snaps which has common job id

    revert_snap_subclient_level() -- To Revert the volume with snap job id

"""
import os
from AutomationUtils.machine import Machine
from Web.AdminConsole.Components.browse import Browse, ContentBrowse
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.AdminConsole.Components.panel import Backup, PanelInfo, DropDown, RDropDown
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.FileServerPages.file_servers import RestorePanel
from Web.Common.page_object import PageService, WebAction
import time
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.Components.dialog import RModalDialog

class FsSubclientDetails:

    """
    This class provides the function or operations that can be performed on the
    subclient of the File System iDA on the AdminConsole
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
        self.__panel = PanelInfo(self.__admin_console)
        self.__snappanel = PanelInfo(self.__admin_console, 'Snapshot')
        self.__blockpanel = PanelInfo(self.__admin_console, 'Block level backup')
        self.__backuppanel = Backup(self.__admin_console)
        self.__restore_panel = RestorePanel(self.__admin_console)
        self.__browse = Browse(self.__admin_console)
        self.__dropdown = DropDown(self.__admin_console)
        self.__admin_console.load_properties(self)

        self.__rtable = Rtable(self.__admin_console)
        self.navigator = self.__admin_console.navigator
        self.fs_servers = FileServers(self.__admin_console)
        self.fs_subclient = FsSubclient(self.__admin_console)
        self.log = self.__admin_console.log
        self.dropdown = RDropDown(self.__admin_console)
        self.__rmodal_dialog = RModalDialog(self.__admin_console)

    @PageService()
    def backup(self, backup_level, notify=False, drop_down=False):
        """"Back up option on the title bar
        Args:

            backup_level   (enum)   : type of backup

            notify         (bool)   : To notify via mail about the backup

            drop_down      (bool)   : To access the backup action from drop down

        Returns :
             job_id : Job ID of the backup job

        Raises:
            Exception :

             -- if fails to run the backup
        """
        if drop_down:
            self.__admin_console.access_menu_from_dropdown(self.__admin_console.props['label.globalActions.backup'])
        else:
            self.__admin_console.access_menu(self.__admin_console.props['label.globalActions.backup'])
        job_id = self.__backuppanel.submit_backup(backup_level, notify)

        return job_id

    @PageService()
    def backup_history(self):
        """"Backup history containing jobs of all subclients"""
        self.__admin_console.access_menu(self.__admin_console.props['label.BackupHistory'])

    @PageService()
    def restore_history(self):
        """"Restore history containing jobs of all subclients"""
        self.__admin_console.access_menu_from_dropdown(self.__admin_console.props['label.RestoreHistory'])

    @PageService()
    def delete_subclient(self):
        """
        Deletes the subclient

        Raises:
            Exception:
                if the subclient could not be deleted

        """
        self.__admin_console.access_menu_from_dropdown(self.__admin_console.props['action.delete'])
        self.__modal_dialog.type_text_and_delete("DELETE")
        self.__admin_console.check_error_message()

    @WebAction()
    def _change_plan(self, plan):
        """
        change the plan associated to subclient

            Args:
                     plan(Str)           : Plan to be selected

        """
        xp = f"//span[contains(text(),'Edit')]"
        self.__driver.find_elements(By.XPATH, xp)[0].click()
        self.__admin_console.wait_for_completion()
        self.__dropdown.select_drop_down_values(0, [plan])
        self.__driver.find_element(By.XPATH, '//span[@class="k-icon k-i-check"]').click()

    @PageService()
    def assign_plan(self, plan):
        """
        To assign the specified plan to the subclient.

            Args:
                     plan(Str)           : Plan to be selected

        Raises:
            Exception:
                if the plan cannot be set
        """
        self._change_plan(plan)

    @PageService()
    def set_backup_activity(self, enable):
        """
        Enable or disable the Backup Enabled toggle.

            Args:
                     enable(bool)           : True: Enables the data backup field

                                              False : Disables the data backup field
        Returns:
            None

        Raises:
            Exception:
                Toggle button not found
        """
        if enable:
            self.__panel.enable_toggle(self.__admin_console.props['label.backupEnabled'])
        else:
            self.__panel.disable_toggle(self.__admin_console.props['label.backupEnabled'])


    @PageService()
    def restore_recovery_point_with_timestamp(self, calender, dest_client=None, restore_path=None, unconditional_overwrite=False,
        notify=False, search_pattern=None,measure_time = False,acl = True , data = True, include_folders = True, 
        impersonate_user=None, **kwargs):
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

                Returns :
                     job_id : job id of the restore

                Raises:
                    Exception :

                     -- if fails to run the restore operation
                     -- if time_limit for browse exceeds parameter passed

        """
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
    def restore_recovery_points(self, recovery_time, dest_client=None, restore_path=None, unconditional_overwrite=False,
                                notify=False, selected_files=None, hadoop_restore=False, **kwargs):
        """"Point in time restores by selecting the date for recovery points

                Args:

                     recovery_time(str)     : The date specified in DD--MM--YYYY format

                     dest_client (str)      : Name of the destination client

                     restore_path(str)      : The destination path to which content should be restored to

                     unconditional_overwrite(bool)  : To overwrite unconditionally on destination path

                     notify(bool)           : To notify via mail about the restore

                     selected_files (list)  : list of (str) paths of restore content

                     hadoop_restore(bool)   : To indicate restore is for hadoop server
                         default: False

                Returns :
                     job_id : job id of the restore

                Raises:
                    Exception :

                     -- if fails to run the restore operation

        """
        self.__admin_console.recovery_point_restore(recovery_time)
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

                for folder in paths:
                    self.__browse.access_folder(folder.strip(':'))
            select_files = [os.path.basename(file) for file in selected_files]
            self.__browse.select_for_restore(file_folders=select_files)

        else:
            self.__browse.select_for_restore(all_files=True)
        self.__browse.submit_for_restore()
        if hadoop_restore and restore_path is not None:
            self.__restore_panel.access_tab(self.__admin_console.props['label.OOPRestore'])
        if dest_client:
            self.__restore_panel.select_destination_client(dest_client)
        if restore_path:
            if kwargs.get('ndmp'):
                self.__admin_console.checkbox_deselect("inplace")
                self.__admin_console.fill_form_by_id('restorePath', restore_path)
            else:
                self.__restore_panel.select_browse_for_restore_path(toggle_inplace=True and not hadoop_restore)
                self.__contentbrowse.select_path(restore_path)
                self.__contentbrowse.save_path()
        if unconditional_overwrite:
            self.__restore_panel.select_overwrite()
        job_id = self.__restore_panel.submit_restore(notify)

        return job_id

    @WebAction()
    def _choose_pre_backup_process(self):
        """
        CLicks on the pre backup process folder icon

        """
        self.__driver.find_element(By.XPATH, f'//a[@ng-click="prepostCommandsTileCtrl.setBackupCommands()"]/span').click()

        self.__admin_console.wait_for_completion()


    @WebAction()
    def _choose_post_backup_process(self):
        """
       click on the post backup process folder icon.

        """
        self.__driver.find_element(By.XPATH, f'//a[@ng-click="prepostCommandsTileCtrl.setBackupCommands(true)"]/span').click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def set_pre_backup_command(self, command_path):

        """
       Sets the pre backup processes.

        Returns:
            None

        Raises:
            Exception:
                command button not found

        """
        self._choose_pre_backup_process()
        self.__contentbrowse.select_path(command_path)
        self.__contentbrowse.save_path()

    @PageService()
    def set_post_backup_command(self, command_path):

        """
       Sets the post backup processes.

        Returns:
            None

        Raises:
            Exception:
                command button not present

        """
        self._choose_post_backup_process()
        self.__contentbrowse.select_path(command_path)
        self.__contentbrowse.save_path()

    @WebAction()
    def _add_command_process(self, index, path):
        """
        To click on folders to browse and select the pre/post commands
        """
        xp = f"//span[@class='k-icon k-i-folder-more font-size-page-title']"
        self.__driver.find_elements(By.XPATH, xp)[index].click()
        self.__admin_console.wait_for_completion()
        self.__contentbrowse.select_path(path)
        self.__contentbrowse.save_path()

    @PageService()
    def set_pre_post_advanced(self, pre_scan_process=None, post_scan_process=None, pre_backup_process=None,
                              post_backup_process=None, run_scan_all_attempts=False, run_backup_all_attempts=False,
                              impersonate_user=False, username=None, password=None):
        """
        To set pre and post process commands.
        """
        self.__admin_console.select_hyperlink(self.__admin_console.props['label.advancedSetting'])

        if pre_scan_process:
            self._add_command_process(0, pre_scan_process)

        if post_scan_process:
            self._add_command_process(1, post_scan_process)

        if pre_backup_process:
            self._add_command_process(2, pre_backup_process)

        if post_backup_process:
            self._add_command_process(3, post_backup_process)

        if run_scan_all_attempts:
            self.__panel.enable_toggle(self.__admin_console.props['label.runPostScan'])

        if run_backup_all_attempts:
            self.__panel.enable_toggle(self.__admin_console.props['label.runPostBackup'])

        if impersonate_user:
            self.__panel.enable_toggle(self.__admin_console.props['label.impersonateUser'])
            if impersonate_user == "Enter credentials":
                self.__admin_console.check_radio_button(impersonate_user)
                self.__admin_console.fill_form_by_id("uname", username)
                self.__admin_console.fill_form_by_id("pass", password)
            else:
                self.__admin_console.check_radio_button(impersonate_user)

        self.__backuppanel.submit()

    @PageService()
    def clear_pre_post_commands(self, input_id):
        """

        Clears the pre post commands set already

        Args :

                input_id(str)   - The input field ID that needs to be cleared.

                    Examples:

                        preBackupCommand    -   For Pre backup command
                        postBackupCommand   -   For Post backup commands
                        preScanCommand      -   For Pre Scan command
                        postScanCommand     -   For Post Scan commands

        Returns:
            None

        Raises:
            Exception:
                The pre/post commands could not be reset.
        """
        self.__admin_console.select_hyperlink(self.__admin_console.props['label.advancedSetting'])
        self.__driver.find_element(By.ID, input_id).clear()
        self.__backuppanel.submit()

    @PageService()
    def edit_content(self, browse_and_select_data, backup_data,
                     del_content=None, exceptions=None,
                     del_exceptions=None, exclusions=None,
                     del_exclusions=None, file_system='Windows',
                     only_edit_content=False):
        """
        Edits the content of the subclient by adding or removing files and folders.

        Args:

            browse_and_select_data(bool)  : Pass True to browse and select data,
                                            False for custom path

            backup_data     (list(paths)) : Data to be backed up by new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            del_content     (list(paths)) : Data to be removed in new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exclusions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exclusions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            del_exclusions     (list(paths)) : Removed exclsuions of new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exceptions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exceptions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            del_exceptions     (list(paths)) : Removed exclsuions of new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']


            file_system       (string)     :  file system of the client
                Eg. - 'Windows' or 'Unix'

            only_edit_content (bool) : Allows to use modal for only editing content

        Returns:
            None

        Raises:
            Exception:
                There is no option to edit the content of the collection
        """
        if not only_edit_content:
            self.__admin_console.tile_select_hyperlink(self.__admin_console.props['header.content'],
                                                       self.__admin_console.props['action.edit'])
        if del_content:
            for path in del_content:
                self.remove_existing_path(path, 0)

        if browse_and_select_data:
            self.__admin_console.select_hyperlink(self.__admin_console.props['action.browse'])
            self.__browse_and_select_data(backup_data, file_system)
        else:
            for path in backup_data:
                self.__add_custom_path(path)
                self.__click_add_custom_path()

        if del_exclusions:
            self.__admin_console.select_hyperlink(self.__admin_console.props['label.Exclusions'])
            for path in del_exclusions:
                self.remove_existing_path(path, 1)

        if exclusions:
            self.__admin_console.select_hyperlink(self.__admin_console.props['label.Exclusions'])
            for path in exclusions:
                self.__add_custom_path(path)
                self.__click_add_custom_path()

        if del_exceptions:
            self.__admin_console.select_hyperlink(self.__admin_console.props['label.Exceptions'])
            for path in del_exceptions:
                self.remove_existing_path(path, 2)

        if exceptions:
            self.__admin_console.select_hyperlink(self.__admin_console.props['label.Exceptions'])
            for path in exceptions:
                self.__add_custom_path(path)
                self.__click_add_custom_path()

        self.__admin_console.click_button(self.__admin_console.props['OK'])
        self.__admin_console.check_error_message()
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @WebAction()
    def remove_existing_path(self, path, index=0):
        """ Deletes the existing files
                Args:
                     path(str)     :   file path to be removed
                     index(int)    :   index used for Content / Exclusions / Exceptions
        """
        elem1 = f"//div[contains(@class,'ui-grid-cell ng-scope ui-grid-coluiGrid')]/span[(text()='{path}')]/parent::div"
        result = self.__driver.find_elements(By.XPATH, elem1)
        get_id = ''
        for file in result:
            if file.is_displayed():
                get_id = self.__driver.find_element(By.XPATH, elem1).get_attribute("id").split('-')
                get_id = get_id[0]+'-'+get_id[1]
        if get_id:
            elem1 = f"//div[contains(@class,'ui-grid-selection')]/ancestor::div[contains(@class,'ui-grid-cell ng-scope') and contains(@id,'{get_id}')]"
            self.__driver.find_element(By.XPATH, elem1).click()
        self.__admin_console.select_hyperlink(self.__admin_console.props['label.globalActions.remove'], index)

    @WebAction()
    def __add_custom_path(self, path):
        """Add custom paths in the path input box
                Args:
                    path (str)      :   Data path to be added
        """
        custom_path_input_xpath = "//input[@placeholder='Enter custom path']"
        custom_path_input = self.__driver.find_elements(By.XPATH, custom_path_input_xpath)
        for path_input in custom_path_input:
            if path_input.is_displayed():
                path_input.clear()
                path_input.send_keys(path)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_add_custom_path(self):
        """Clicks the add custom path icon"""
        add_path_icon_xpath = "//i[@title='Add']"
        custom_path_add = self.__driver.find_elements(By.XPATH, add_path_icon_xpath)
        for path_add in custom_path_add:
            if path_add.is_displayed():
                path_add.click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __browse_and_select_data(self, backup_data, file_system):
        """
        selects backup data through FS Browse

        Args:

            backup_data     (list(paths)) : Data to be backed up by new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            file_system      (string)     :  file system of the client
                Eg. - 'Windows' or 'Unix'

        Returns:
            None

        Raises:
            Exception:
                if not able to select data
        """

        for data in backup_data:
            count = 0
            flag = True
            if file_system.lower() == 'windows':
                pattern = "\\"
            else:
                pattern = "/"
            directories = []
            start = 0
            while flag:
                tag = data.find(pattern, start)
                if tag == -1:
                    flag = False
                else:
                    count += 1
                    start = tag+1

            for i in range(0, count+1):
                directory, sep, folder = data.partition(pattern)
                data = folder
                if directory != '':
                    directories.append(directory)
            path = len(directories)

            try:
                for i in range(0, path-1):
                    if self.__driver.find_element(By.XPATH, 
                            "//span[text() = '" + str(directories[i]) + "']/../../button").\
                            get_attribute("class") == 'ng-scope collapsed':
                        self.__driver.find_element(By.XPATH, 
                            "//span[text() = '"+str(directories[i])+"']/../../button").click()
                dest = path-1
                dest_elem = self.__driver.find_elements(By.XPATH, 
                                "//span[text() = '" + str(directories[dest]) + "']")
                for elem in dest_elem:
                    if elem.is_displayed():
                        elem.click()
                        break

                self.__admin_console.click_button(self.__admin_console.props['label.save'])

            except Exception as excep:
                self.__admin_console.click_button(self.__admin_console.props['label.save'])
                self.__admin_console.click_button(self.__admin_console.props['label.cancel'])
                raise excep

    @PageService()
    def enable_snapshot_engine(self, enable_snapshot, engine_name=None):
        """
        Sets the snapshot engine for the subclient
        Args:
            enable_snapshot (bool):     to enable / disable snap backups on the subclient

            engine_name     (str):   name of the snapshot engine

        Returns:
            None

        Raises:
            Exception:
                if not able to change snapshot
        """
        toggle = self.__snappanel.get_toggle_element(self.__admin_console.props['label.enableHardwareSnapshot'])
        status = self.__snappanel.is_toggle_enabled(toggle)
        if enable_snapshot:
            if status:
                self.__admin_console.tile_select_hyperlink(self.__admin_console.props['label.snapshot'], self.__admin_console.props['action.edit'])
            else:
                self.__snappanel.enable_toggle(self.__admin_console.props['label.enableHardwareSnapshot'])
            if not engine_name:
                raise Exception("The engine name is not provided")
            self.__dropdown.select_drop_down_values(0, [engine_name])
        else:
            self.__snappanel.disable_toggle(self.__admin_console.props['label.enableHardwareSnapshot'])
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @PageService()
    def set_block_level(self, blocklevel):
        """
        Sets the block level option for the subclient

        Args:
            blocklevel (bool):     To enable / disable block level on the subclient

        Returns:
            None

        Raises:
            Exception:
                if not able to change snapshot
        """
        if blocklevel:
            # toggle = self.__blockpanel.get_toggle_element(self.__admin_console.props['label.blockLevelBackup'])

            self._FsSubclientDetails__blockpanel.enable_toggle\
                (self._FsSubclientDetails__admin_console.props['label.blockLevelBackup'])
        else:
            self._FsSubclientDetails__blockpanel.disable_toggle\
                (self._FsSubclientDetails__admin_console.props['label.blockLevelBackup'])

    @PageService()
    def set_block_level_file_indexing(self, blocklevel_fi):
        """
        Sets the block level file indexing option for the subclient

        Args:
            blocklevel_fi (bool):     To enable / disable block level on the subclient

        Returns:
            None

        Raises:
            Exception:
                if not able to change snapshot
        """
        if blocklevel_fi:
            self._FsSubclientDetails__blockpanel.enable_toggle\
                (self._FsSubclientDetails__admin_console.props['label.data.indexing'])
        else:
            self._FsSubclientDetails__blockpanel.disable_toggle\
                (self._FsSubclientDetails__admin_console.props['label.data.indexing'])

    @PageService()
    def set_data_access_nodes(self, access_nodes):
        """
        Sets the data access nodes for NAS clients

        Args:
            access_nodes (list(str)) : List of access nodes
        
        Returns:
            None
        Raises:
            Exception:
                if not able to set the access
        """

        if access_nodes:
            self.__admin_console.tile_select_hyperlink("Access nodes", "Edit")
            self.__dropdown.select_drop_down_values(drop_down_id="accessnode-dropdown",
                                                    values=access_nodes)
            self.__admin_console.click_button(self.__admin_console.props['label.save'])

