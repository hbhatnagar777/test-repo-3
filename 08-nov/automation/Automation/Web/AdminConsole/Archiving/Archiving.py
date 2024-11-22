from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for,
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Archiving page.

Classes:

    Archiving() ---> _Navigator() ---> login_page ---> AdminConsoleBase() ---> object()

Archiving --  This class contains all the methods for action in Solutions -> Archiving page

    Functions:

    createnewserver()           --  create new network share server
    select_filesize_mtime_rule()    -- select filesize and mtime rules under archiving dashboard
    enablearchivingrules()    -- enable archiving rules for the newly created network share server
    editfileservercontent()    -- edit file server content
    editfileserverownerprop()    -- de-select file server collect owner info
    runanalyticjob()    -- run online crawler job for selected network share file server
"""
import os
from Web.AdminConsole.Components.table import Rtable, Table
from Web.Common.page_object import PageService, WebAction
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.core import Checkbox
from Web.AdminConsole.Components.panel import RModalPanel, RDropDown, RPanelInfo
from Web.AdminConsole.Components.browse import RBrowse, RContentBrowse
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import RRestorePanel
import time

from AutomationUtils.constants import DistributedClusterPkgName


class ArchiveRestorePanel(RRestorePanel):
    def __init__(self, admin_console):
        super(RArchiveRestorePanel, self).__init__(admin_console)
		self.__checkbox = Checkbox(admin_console)

    @PageService()
    def deselect_restore_data_instead_of_stub(self):
        """Method to deselect Restore Data instead of Stub in restore panel"""
        self.__checkbox.uncheck(id='restoreDataInsteadOfStub')
        self._admin_console.wait_for_completion()


class Archiving:
    """
     This class contains all the methods for action in Solutions -> Archiving Page
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._admin_console.load_properties(self)

        # Components required
        self.__table = Rtable(self._admin_console)
        self.__drop_down = RDropDown(self._admin_console)
        self.__panel = RModalPanel(self._admin_console)
        self.__panel_info = RPanelInfo(self._admin_console)
        self.__restore_panel = ArchiveRestorePanel(self._admin_console)
        self.__browse = RBrowse(self._admin_console)
        self.__contentbrowse = RContentBrowse(self._admin_console)

    @PageService()
    def add_new_server(self, server_type, host_name, access_node, plan, archive_paths, ndmp=False, is_cifs=True,
                       username=None, password=None, exclusions=None, exceptions=None, display_name=None,
                       migrate=False):
        """
                Create new File Server

                    Args:
                        server_type (str)  - "NAS", "Unix", or "Windows"

                        host_name (str)  - new host name

                        archive_paths (list)  - subclient content paths for new archive client

                        username (str)  - user credentials to be used to run Archive

                        password (str)  - user credentials used to run Archive

                        access_node(str)  - the access node for new network share

                        plan(str)   -   Archival plan to be used.

                        ndmp(bool)  -   NDMP or Non-NDMP client

                        is_cifs(bool) -   True for "cifs", else "nfs"

                        exclusions(list)  - subclient exclusion paths for new archive client

                        exceptions(list)  - subclient exception paths for new archive client

                        migrate (bool)  -   To perform filer migration

                    Raises:
                        Exceptions: if unable to create new network share server
                """
        self._admin_console.click_button("Add server")

        self._admin_console.access_sub_menu("NAS")

        self._admin_console.fill_form_by_id(element_id="archiveHostName", value=host_name)

        if display_name:
            self._admin_console.fill_form_by_id(element_id="displayName", value=display_name)
        else:
            self._admin_console.fill_form_by_id(element_id="displayName", value=host_name)

        if ndmp:
            self._admin_console.enable_toggle(index=0, cv_toggle=True)
        else:
            self._admin_console.disable_toggle(index=0, cv_toggle=True)

        if is_cifs:
            self._admin_console.select_radio("cifsShareType")

        self.__drop_down.select_drop_down_values(drop_down_id="accessnode-dropdown", values=[access_node], default_unselect=False)

        self.__drop_down.select_drop_down_values(drop_down_id="planSummaryDropdown", values=[plan])

        self._admin_console.fill_form_by_id(element_id="Username", value=username)
        self._admin_console.fill_form_by_id(element_id="password", value=password)
        self._admin_console.fill_form_by_id(element_id="confirmPassword", value=password)

        for path in archive_paths:
            self.add_custom_path(path)
            self._admin_console.wait_for_completion()
            self.click_add_custom_path()

        if exclusions:
            self._admin_console.select_hyperlink(
                self._admin_console.props['label.Exclusions'])
            for path in exclusions:
                self.add_custom_path(path)
                self._admin_console.wait_for_completion()
                self.click_add_custom_path()
                self._admin_console.wait_for_completion()

        if exceptions:
            self._admin_console.select_hyperlink(
                self._admin_console.props['label.Exceptions'])
            for path in exceptions:
                self.add_custom_path(path)
                self._admin_console.wait_for_completion()
                self.click_add_custom_path()
                self._admin_console.wait_for_completion()

        if migrate:
            # To be implemented for filer migration project.
            self._admin_console.enable_toggle(index=2, cv_toggle=True)
            self.__drop_down.select_drop_down_values(drop_down_id="nasServerMigrationSource", values=[])

        self._admin_console.submit_form()

    @WebAction()
    def add_custom_path(self, path):
        """Add custom paths in the path input box
                Args:
                    path (str)      :   Data path to be added
        """
        custom_path_input_xpath = "//input[@placeholder='Enter custom path']"
        custom_path_input = self._driver.find_elements(By.XPATH, custom_path_input_xpath)
        for path_input in custom_path_input:
            if path_input.is_displayed():
                path_input.clear()
                path_input.send_keys(path)

    @WebAction()
    def click_add_custom_path(self):
        """Clicks the add custom path icon"""
        add_path_icon_xpath = "//i[@title='Add']"
        custom_path_add = self._driver.find_elements(By.XPATH, add_path_icon_xpath)
        for path_add in custom_path_add:
            if path_add.is_displayed():
                path_add.click()

    @PageService()
    def create_new_server(self, index_engine, nwshare_name, src_path, impersonate_user,
                          impersonate_password, access_node):
        """
        Create new File Server

            Args:
                index_engine (str)  - the index engine that will be used for new network share
                nwshare_name (str)  - new network share name
                src_path (str)  - subclient content path for new network share
                impersonate_user (str)  - user credentials to be used to run filescan and backup
                impersonate_password (str)  - user credentials used to run filescan and backup
                access_node(str)  - the access node for new network share
            Raises:
                Exceptions: if unable to create new network share server
        """
        self._admin_console.select_hyperlink("Add file server")
        self._admin_console.select_value_from_dropdown("indexingEngine", index_engine)
        self._admin_console.fill_form_by_id("Name", nwshare_name)
        self._admin_console.fill_form_by_id("Description", "automation")
        self._admin_console.click_button("Add paths")
        self._admin_console.click_button("Add paths")
        self._admin_console.fill_form_by_id("addMultipleContentTextarea", src_path)
        self._admin_console.log.info("      click ok button on Add/Edit multiple content")
        self._admin_console.click_button("OK")
        self._admin_console.log.info("   click ok button on add/edit content")
        self._admin_console.click_button("OK")
        self._admin_console.fill_form_by_id("Username", impersonate_user)
        self._admin_console.fill_form_by_id("password", impersonate_password)
        self._admin_console.select_value_from_dropdown("accessNode", access_node)
        self._admin_console.checkbox_select("collectOwnerInfo")
        self._admin_console.log.info('   uncheck schedule file discovery')
        self._admin_console.checkbox_deselect("scheduleToRun")
        self._admin_console.log.info('   click save button on create file server page')
        self._admin_console.submit_form()
        if self._admin_console.current_url().find("archivingDataSources") == -1:
            self._admin_console.log.info("failed to create new file server")
            raise CVWebAutomationException("failed to create new file server")
        else:
            self._admin_console.log.info('successfully created the new file server')

    @WebAction()
    def __select_file_size(self):
        """
        Selects file size
        """
        filesize = self._driver.find_element(By.XPATH, "//div[@id='fileSizeSlider']/ul/li/span").text
        assertsizeval = ["1MB", "25MB", "26MB", "27MB", "28MB", "24MB", "23MB", "22MB"]
        if filesize in assertsizeval:
            self._driver.find_element(By.XPATH, "//div[@id='fileSizeSlider']/ul/li/span").click()

    @WebAction()
    def __get_file_size(self):
        """
        gets file size
        """
        return self._driver.find_element(By.XPATH, ".//*[@id='fileSizeSlider']/span[7]").text

    @WebAction()
    def __select_modified_size(self):
        """
        Selects file size
        """
        filemtime = self._driver.find_element(By.XPATH, 
            "//div[@id='fileModifiedSlider']/ul/li[2]/span").text
        assertmtimeval = "6m"
        if filemtime == assertmtimeval:
            self._driver.find_element(By.XPATH, 
                "//div[@id='fileModifiedSlider']/ul/li[2]/span").click()

    @WebAction()
    def __get_modified_size(self):
        """
        gets file size
        """
        return self._driver.find_element(By.XPATH, ".//*[@id='fileModifiedSlider']/span[7]").text

    @PageService()
    def select_filesize_mtime_rule(self):
        """
        select_FileSize_Mtime_rule:  Select file size and modifiedtime rule on archiving dashboard
        Raises:
            Exception: if unable to select filesize mtime rules
        """

        self.__select_file_size()
        self._admin_console.wait_for_completion()
        rulestringsize = self.__get_file_size()
        self.__select_modified_size()
        self._admin_console.wait_for_completion()
        rulestringmtime = self.__get_modified_size()
        assertsizeval = ["1MB", "25MB", "26MB", "27MB", "28MB", "24MB", "23MB", "22MB"]
        assertmtimeval = "6m"
        if (str(rulestringsize) in assertsizeval) & (str(rulestringmtime) == "6months"):
            self._admin_console.log.info("    Rule settings validation successfull")
            self._admin_console.driver.find_element(By.XPATH, ".//*[@id='rulesSaveBtn']").click()
            self._admin_console.wait_for_completion()
        else:
            self._admin_console.log.info("Size condition:   ")
            self._admin_console.log.info((str(rulestringsize) in assertsizeval))
            self._admin_console.log.info("Mtime condition:  ")
            self._admin_console.og.info(str(rulestringmtime) == assertmtimeval)
            raise Exception("size rule or modified time rule validation failed")

    @PageService()
    def enable_archiving_rules(self, nwshare_name, plan, access_node):
        """
        Enable Archive Rules

        Args:
            nwshare_name (str)  - the network share file server name where we will enable archiving
            plan (str)    - the plan to be used to enable archiving
            access_node(str)  - the access node for new network share
        Raises:
            if unable to enable archiving rules

        """
        self._admin_console.log.info("search and click for newly created network share server")
        self.__table.access_link(nwshare_name)

        self._admin_console.log.info("On Archiving dashboard, selecting rules")
        self.select_filesize_mtime_rule()

        self._admin_console.log.info("click start archiving button on archiving dashboard")
        self._admin_console.click_button("Start archiving")

        self._admin_console.log.info("on Archiving properties page, selecting plan")
        self._admin_console.select_value_from_dropdown("plan", plan)

        self._admin_console.log.info("selecting access node")
        self._admin_console.select_value_from_dropdown("accessNode", access_node)

        self._admin_console.log.info("Click Start archiving")
        self._admin_console.submit_form()
        self._admin_console.wait_for_completion()

        if self._admin_console.current_url().find("archivingDataSources") == -1:
            self._admin_console.log.info("failed to enable archiving rules")
            raise CVWebAutomationException("failed to enable archiving rules")
        else:
            self._admin_console.log.info('successfully enabled archiving rules for the new file server')

    @PageService()
    def edit_file_server_content(self, src_path2):
        """
        edit file server content

        Args:
            src_path2 (str) : new file server content

        Raises:
            Exception: if unable to modify file server content
        """

        self._admin_console.log.info("click Edit to modify content")
        self._admin_console.tile_select_hyperlink("Content", "Edit")

        self._admin_console.log.info("click Add paths on add/edit file path page")
        self._admin_console.click_button("Add paths")

        self._admin_console.log.info("modify content path on add/modify multiple content page")
        self._admin_console.fill_form_by_id("addMultipleContentTextarea", src_path2)

        self._admin_console.log.info("click ok button on add/modify multiple content page")
        self._admin_console.click_button("OK")

        self._admin_console.log.info("click ok on add/edit content page")
        self._admin_console.click_button("OK")
        elemxpath = \
            ".//*[@id='wrapper']/div[2]/div[2]/div/div/div/div[2]/div[1]/cv-tile-component[1]/div/div[3]/span/span[1]"
        if self._admin_console.check_if_entity_exists("xpath", elemxpath):
            self._admin_console.log.info("successfully modified file content")
        else:
            raise CVWebAutomationException("failed to modify content")

    @PageService()
    def edit_file_server_owner_prop(self):
        """
        modify file server content owner info
        Raises:
            if unable to modify collect file owner option
        """

        self._admin_console.log.info("click Edit to modify file server collect owner info")
        self._admin_console.tile_select_hyperlink("Owner information", "Edit")
        self._admin_console.checkbox_deselect("collectOwnerInfo")
        self._admin_console.log.info('   click save button on collect owner informaiton page')
        self._admin_console.submit_form()
        elemxpath = \
            ".//*[@id='wrapper']/div[2]/div[2]/div/div/div/div[2]/div[1]/cv-tile-component[3]/div/div[3]/span/span[1]"
        if self._admin_console.check_if_entity_exists("xpath", elemxpath):
            self._admin_console.log.info("successfully modified collect owner info")
        else:
            raise CVWebAutomationException("failed to modify collect owner info")

    @PageService()
    def run_analytic_job(self, nwshare_name):
        """
        run online crawler job for selected network share

        Args:
            nwshare_name:  network share server name where analytics job need run

        Raises:
            Exception: fail to run analytics job

        """
        self._admin_console.log.info("select run analytics action for selected network share server")
        self.__table.access_action_item(nwshare_name, 'Run analytics', 'Actions')
        self._admin_console.wait_for_completion()

        if self._admin_console.current_url().find(nwshare_name) == -1:
            self._admin_console.log.info("failed to click run analytics for the network share server")
            raise CVWebAutomationException(
                "failed to click run analytics for the network share server"
            )
        else:
            self._admin_console.log.info('successfully started analytics job for the network share file server')

    @PageService()
    def add_distributed_app(self, pkg, server_name, access_nodes, plan_name, archive_paths, exclusions=None,
                            exceptions=None, existing_server=False):
        """Create distributed file server with given parameters.

            Args:
                pkg              (enum)  -- Instance of constants.DistributedClusterPkgName

                server_name      (str)   -- Name of the server to be created.

                access_nodes     (list)  -- list of access nodes to select

                plan_name        (str)   -- plan name to select

                archive_paths (list)  - subclient content paths for new archive client

                exclusions(list)  - subclient exclusion paths for new archive client

                exceptions(list)  - subclient exception paths for new archive client

                existing_server(bool)   -   Add an existing server as Archive Server if True.

        """
        add_menu_id = None

        if pkg == DistributedClusterPkgName.LUSTREFS:
            add_menu_id = 'Lustre'
        elif pkg == DistributedClusterPkgName.GPFS:
            add_menu_id = 'IBM Spectrum Scale (GPFS)'
        elif pkg == 'HADOOP':
            add_menu_id = 'Hadoop'

        if add_menu_id is None:
            raise CVWebAutomationException("Invalid Distributed Cluster Package name provided")

        self._admin_console.click_button("Add server")

        self._admin_console.access_sub_menu(add_menu_id)

        if existing_server:
            self._admin_console.select_hyperlink('Existing file server')
            self.__drop_down.select_drop_down_values(drop_down_id="setUpFileArchiving_isteven-multi-select_#6867",
                                                     values=[server_name],
                                                     partial_selection=True)
        else:
            self._admin_console.fill_form_by_id('archiveHostName', server_name)

        if pkg != "HADOOP":
            self.__drop_down.select_drop_down_values(drop_down_id="accessnode-dropdown",
                                                     values=access_nodes,
                                                     partial_selection=True,
                                                     default_unselect=False)
        else:
            self.__drop_down.select_drop_down_values(drop_down_id="setUpFileArchiving_isteven-multi-select_#6887",
                                                     values=access_nodes,
                                                     partial_selection=True,
                                                     default_unselect=False)

        self.__drop_down.select_drop_down_values(drop_down_id='planSummaryDropdown', values=[plan_name])

        for path in archive_paths:
            self.add_custom_path(path)
            self._admin_console.wait_for_completion()
            self.click_add_custom_path()

        if exclusions:
            self._admin_console.select_hyperlink(
                self._admin_console.props['label.Exclusions'])
            for path in exclusions:
                self.add_custom_path(path)
                self._admin_console.wait_for_completion()
                self.click_add_custom_path()
                self._admin_console.wait_for_completion()

        if exceptions:
            self._admin_console.select_hyperlink(
                self._admin_console.props['label.Exceptions'])
            for path in exceptions:
                self.add_custom_path(path)
                self._admin_console.wait_for_completion()
                self.click_add_custom_path()
                self._admin_console.wait_for_completion()

        self._admin_console.submit_form()

    @PageService()
    def retire_server(self, server_name, wait=True):
        """Performs retire action for the given server

        Args:
                server_name     (str) -- server name to retire
        """
        self.__table.access_action_item(server_name, self._admin_console.props['action.retire'])

        self._admin_console.fill_form_by_id("confirmText", self._admin_console.props['action.retire'].upper())
        self._admin_console.click_button_using_text(self._admin_console.props['action.retire'])
        if wait:
            return self._admin_console.get_jobid_from_popup()

    @PageService()
    def delete_server(self, server_name):
        """Performs delete action for the given server

        Args:
                server_name     (str) -- server name to delete
        """
        self.__table.access_action_item(server_name, self._admin_console.props['action.delete'])
        self._admin_console.fill_form_by_id("confirmText", self._admin_console.props['action.delete'].upper())
        self._admin_console.click_button(self._admin_console.props['action.delete'])

    @PageService()
    def access_server(self, client_name):
        """
        Method to access the required server

        Args:
            client_name (str)      : Name of the client to be accessed

        Returns :
            None

        Raises:
            Exception :

            -- if the client doesn't exist

        """

        self.__table.access_link(client_name)
        self._admin_console.wait_for_completion()

    @PageService()
    def run_archive(
            self,
            client_name,
            notify=False):
        """
        Method to backup the given subclient

        Args:
             client_name (str)      : Name of the client to be backed up

            notify(bool)           : To notify via mail about the backup

        Returns :
             job_id : Job ID of the backup job

        Raises:
            Exception :

             -- if fails to run the backup
        """

        self.__table.access_action_item(client_name, "Archive")

        if notify:
            self._driver.find_element(By.XPATH, "*//span[contains(text(),'Notify via email')]").click()

        self.__panel.submit()

        _job_id = self._admin_console.get_jobid_from_popup()
        self._admin_console.wait_for_completion()
        return _job_id

    @PageService()
    def restore_subclient(
            self,
            client_name,
            proxy_client=None,
            restore_path=None,
            backupset_name=None,
            subclient_name=None,
            unconditional_overwrite=False,
            restore_ACLs=False,
            restore_data_instead_of_stub=True,
            impersonate_user=None,
            impersonate_password=None,
            selected_files=None,
            show_deleted_files=False):
        """
                Method to Restore the given client data

                Args:
                     client_name (str)      : Name of the client

                     proxy_client (str)      : Name of the proxy client

                     restore_path(str)      : The destination path to which content
                                              should be restored to

                     backupset_name (str)   : backup set name of the client

                     subclient_name (str)   : subclient name

                     unconditional_overwrite(bool)  : To overwrite unconditionally
                                                      on destination path

                     restore_ACLs(bool)     :   Whether to restore ACLs or not

                     restore_data_instead_of_stub(bool)   :   True if to restore data instead of stub.

                     impersonate_user(str)  :   Impersonate Username for network share clients.

                     impersonate_password(str)  :   Impersonate Password for network share clients.

                     selected_files (list)  : list of (str) paths pf restore content

                     show_deleted_files (bool): To show deleted items or not.

                Returns :
                     job_id : job id of the restore

                Raises:
                    Exception :

                     -- if fails to run the restore operation
                """

        self.__table.access_action_item(
            client_name, self._admin_console.props['label.restore'])
        self._admin_console.wait_for_completion()
        if backupset_name:
            self.__restore_panel.select_backupset_and_subclient(backupset_name, subclient_name)
            self.__restore_panel.submit(wait_for_load=True)

        if show_deleted_files:
            time.sleep(10)
            self.__contentbrowse.select_action_dropdown_value(value='Show deleted items', index=0)

        if selected_files:
            if selected_files[0].startswith('\\\\'):
                loc = selected_files[0].find('\\', 2)
                host = selected_files[0][:loc]
                paths = [host]
                path = os.path.dirname(selected_files[0][loc+1:])
                paths.extend(path.split('\\'))
            else:
                delimiter = '\\'
                paths = os.path.dirname(selected_files[0])
                if '/' in selected_files[0]:
                    delimiter = '/'
                if delimiter == '/':
                    paths = paths.strip('/')
                paths = paths.split(delimiter)
            select_files = [os.path.basename(file) for file in selected_files]
            for folder in paths:
                self._admin_console.wait_for_completion()
                self.__browse.access_folder(folder)
            self.__browse.select_files(file_folders=select_files)
        else:
            self.__browse.select_files(select_all=True)
        self.__browse.submit_for_restore()
        self._admin_console.wait_for_completion()

        if proxy_client:
            self.__restore_panel.select_restore_destination_client(destination_client_name=proxy_client)

        self.__restore_panel.toggle_acl_restore_checkbox(check_option_to=restore_ACLs)

        if not restore_data_instead_of_stub:
            self.__restore_panel.deselect_restore_data_instead_of_stub()

        if restore_path:
            self.__checkbox.toggle_restore_to_original_folder_checkbox(check_option_to=False)
            self.__restore_panel.add_destination_path_for_restore(restore_path)

        if impersonate_user:
            self.__restore_panel.impersonate_user(username=impersonate_user, password=impersonate_password)

        if unconditional_overwrite:
            self.__restore_panel.toggle_unconditional_overwrite_checkbox()
        self._admin_console.log.info("wait for click restore option")
        self.__restore_panel.click_restore_button()
        try: 
            self._admin_console.click_button('Yes')
        except:
            pass

        return self._admin_console.get_jobid_from_popup()

    @WebAction()
    def _click_action_dropdown(self):
        """ Selects action dropdown in restore page """

        self._admin_console.unswitch_to_react_frame()
        elem = f"//a[contains(@class,'uib-dropdown-toggle')]/span[contains(@class,'right ng-binding')]"
        self._driver.find_element(By.XPATH, elem).click()

    @WebAction()
    def _click_sub_link(self, text):
        """ Selects items from action dropdown in restore page
        Args:
            text(str): The select the specific entity from dropdown
        """
        self._driver.find_element(By.XPATH, 
            f"//span[@data-ng-bind-html='subLinks.label' and text()='{text}']").click()
        self._admin_console.wait_for_completion()

    @PageService()
    def subclient_level_restore(self, backupset_name='defaultBackupSet', subclient_name="default", dest_client=None,
                                restore_path=None, unconditional_overwrite=False, notify=False, selected_files=None,
                                hadoop_restore=False, show_deleted_files=False):

        """
                        Method to Restore the given client data

                        Args:
                             restore_path(str)      : The destination path to which content
                                                      should be restored to

                             backupset_name (str)   : backup set name of the client

                             subclient_name (str)   : subclient name

                             dest_client (str)  :   Destination Client Name

                             unconditional_overwrite(bool)  : To overwrite unconditionally
                                                              on destination path

                            hadoop_restore(bool)   : To indicate restore is for hadoop server
                                                        default: False

                            selected_files (list)  : list of (str) paths of restore content

                            notify (bool)          : To notify via mail about the restore

                            selected_files (list)  : list of (str) paths pf restore content

                            show_deleted_files (bool)   : To show deleted files

                        Returns :
                             job_id : job id of the restore

                        Raises:
                            Exception :

                             -- if fails to run the restore operation
                        """

        table = Table(self._admin_console)
        table.access_action_item(subclient_name, "Restore")
        self._admin_console.wait_for_completion()

        if show_deleted_files:
            time.sleep(10)
            self._click_action_dropdown()
            self._admin_console.wait_for_completion()
            self._click_sub_link('Show deleted items')
            self._admin_console.wait_for_completion()

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

        if hadoop_restore and restore_path is not None:
            self.__restore_panel.access_tab(self._admin_console.props['label.OOPRestore'])
        if dest_client:
            self.__restore_panel.select_destination_client(dest_client)
        if restore_path:
            self.__restore_panel.select_browse_for_restore_path(toggle_inplace=not hadoop_restore)
            self.__contentbrowse.select_path(restore_path)
            self.__contentbrowse.save_path()
        if unconditional_overwrite:
            self.__restore_panel.select_overwrite()
        job_id = self.__restore_panel.submit_restore(notify)

        return job_id

