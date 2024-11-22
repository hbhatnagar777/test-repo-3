# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
File servers page in admin console

FileServers:

    access_server()       -> Method to access the required file server

    backup_subclient()    -> Method to run backup operation from file servers page

    run_check_readiness() -> Method to run check readiness operation from file servers page

    restore_client()      -> Method to run restore operation from file servers page

    view_jobs()           -> Method to view the jobs of the sever

    install_windows_unix_client()	-> Method to add Windows/Unix Server

    add_distributed_app()           -> Create distributed file server with given parameters.

    add_ibmi_client()               -> Method to add a new IBMi client.

    is_client_exists()              -> check client entry from file servers page

    retire_ibmi_client()            -> Performs retire action for the given IBMi client
    
    navigate_to_file_server_tab()   -> access the File server tab of Manage-->File servers (tab if exists).

    retire_server()                 -> retire client

    action_uninstall_software()     -> uninstall all/selected packages

    action_update_software()        -> Update client

    action_add_software()           -> Add packages to existing client

    delete_server()                 -> delete client

    reconfigure_server()             -> reconfigure client

    __get_protocols_text()          -> Gets text from the dialog box containing all protocols

    action_list_snaps()             :       Lists the snaps on client level with the given name

RestorePanel:

    select_destination_client()     :       Select destination client for restore

    select_nas_destination_client()     :   Select nas destination for nas


    select_backupset_and_subclient():       Selects the backup set and subclient to be restored

    search_files_for_restore()      :       Search for the files to restore

    select_overwrite()              :       Selects the unconditional overwrite option

    select_browse_for_restore_path():       click on browse during selecting destination path

    submit_restore()                :       restores the data as per options selected

    select_agent()                  :       selects the CIFS / NFS protocol in restore panel


AddPanel:

    add_custom_path()               :       Adds data paths to content,exclusions,exceptions tab

    click_add_custom_path()         :       clicks the add custom path plus icon

    toggle_own_content()            :       Toggle to override backup content

    browse_and_select_data()        :       To browse and choose content data

    remove_plan_content()           :       To remove inherited plan content

    add()                           :       Method to add content,exclusions,exceptions

AddWizard:

    select_file_server_env()        :       Select file server environment when configuring new server on metallic

    add_new_gateway()               :       Add a new gateway when configuring new server on metallic

    add_new_server()                :       interactively install and configure new server

    configure_region()              :       select region

    configure_AWS_permission()      :       configure authentication method for AWS

    select_backup_gatway()          :       select gateway node and click next button

    add_new_server_silent_install() :       Install and configure new server using Silent Install command

    select_backup_gateway()         :       Select gateway node when configuring new server on metallic

    interactive_install_machine()   :       interactive install and registering new servers

    push_add_new_server()           :       Push install new servers 

    select_local_storage()          :       configure and select new local storage

    select_cloud_storage()          :       Configure/select cloud storage

    select_plan()                   :       Select plan name when configuring new server

    add_new_plan()                  :       Add new plan

    set_backup_content_filters()    :       Configure backup content, filters and exceptions

"""
import os, time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from AutomationUtils.constants import DistributedClusterPkgName
from Install.install_custom_package import InstallCustomPackage
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.table import Rtable, Table
from Web.AdminConsole.Components.panel import (Backup, ModalPanel, DropDown, 
                                               PanelInfo, RDropDown, RPanelInfo, 
                                               RModalPanel)
from Web.AdminConsole.Components.browse import Browse, ContentBrowse
from Web.AdminConsole.NAS.nas_file_servers import NASFileServers
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog, RBackup
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from selenium.webdriver.common.keys import Keys
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.FSPages.RFsPages.RFs_InstallHelper import RFsInstallHelper
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils


class FileServers:
    """class for file servers page"""

    def __init__(self, admin_console):
        """
        Args:
        admin_console(AdminConsole): adminconsole
        object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._admin_console.load_properties(self)
        self._navigator = self._admin_console.navigator
        self.nas_file_server = NASFileServers(self._admin_console)

        # Components required
        self.__table = Rtable(self._admin_console)
        self.__oldtable = Table(self._admin_console)
        self.__panel = Backup(self._admin_console)
        self.__panelinfo = PanelInfo(self._admin_console, 'Snap')
        self.__restore_panel = RestorePanel(self._admin_console)
        self.__browse = Browse(self._admin_console)
        self.__contentbrowse = ContentBrowse(self._admin_console)
        self.__drop_down = DropDown(self._admin_console)
        self.__modal_panel = ModalPanel(self._admin_console)
        self.__rmodal_panel = RModalPanel(self._admin_console)
        self.__addpanel = AddPanel(self._admin_console)
        self.__rdropdown = RDropDown(self._admin_console)
        self.__page_container = PageContainer(self._admin_console)
        self._sla_panel = PanelInfo(self._admin_console, title='SLA')
        self.__dialog = RModalDialog(admin_console)
        self.__rbackup = RBackup(admin_console)
        self.__fileserver_utils = FileServersUtils(admin_console)
        self.__wizard = Wizard(admin_console)

    @WebAction()
    def __get_affected_client(self):
        """ Method to get affected client list"""
        return self._driver.find_element(By.XPATH,
                                         "//p[@ng-bind-html='previewCompanyChangeCtrl.eligibleServersString']").text

    @WebAction()
    def __click_add_client_button(self):
        """Method to click plus icon button on Add file server pane"""
        xpath = "//span[@id='add-host-name']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __expand_backup_configuration_accordion(self):
        """Method to expand Backup Configuration accordion which contains plan input"""
        acc_xp = \
            "//span[contains(text(), 'Backup configuration')]/ancestor::div[contains(@class, 'cv-accordion-header')]"
        accordion_elt = self._driver.find_element(By.XPATH, acc_xp)
        if "expanded" not in accordion_elt.get_attribute("class"):
            ActionChains(self._driver).move_to_element(
                accordion_elt).click().perform()

    @WebAction()
    def __get_job_id_page(self):
        """
        Returns job_id from the page

        """
        return self._driver.find_element(By.XPATH,
                                         '//div[@data-ng-controller="pushInstallController"]//a[contains(@href,"jobs")]').text

    @WebAction()
    def __get_job_id_dialog(self):
        """
        Returns job_id from the dialog that appears

        """
        return self._driver.find_element(By.XPATH, '//div[contains(text(), "Job ID:")]').text

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
    def access_agent(self, agent):
        """
        Method to access the NAS Agent

        Args:
            agent (str)      : Name of the agent (CIFS/NFS/NDMP) to be accessed

        Returns :
            True: if agent exists
            False: if agent does not exist

        Raises:
            Exception :

            -- if the client doesn't exist

        """
        if self._admin_console.check_if_entity_exists('link', agent):
            self.__oldtable.access_link(agent)
            self._admin_console.wait_for_completion()
            return True
        return False

    @PageService()
    def enable_sla_toggle(self):
        """ enable sla toggle on FS subclient configuration panel """
        self._admin_console.select_configuration_tab()
        self._sla_panel.enable_toggle("Exclude from SLA")

    @PageService()
    def enable_snap(self, client_name):
        """Method to enable Intellisnap at Client
        Args:
            client_name (str)      : Name of the client
        """
        self.access_server(client_name)
        self.rpnlinfo = RPanelInfo(self._admin_console, "Snapshot management")
        self.rpnlinfo.enable_toggle(self._admin_console.props['label.snapEnabled'])

    @PageService()
    def backup_subclient(
            self,
            client_name,
            backup_level,
            backupset_name=None,
            subclient_name=None,
            notify=False,
            **kwargs):
        """
        Method to backup the given subclient

        Args:
             client_name (str)      : Name of the client to be backed up

             backupset_name (str)   : backup set name of the client

             subclient_name (str)   : subclient to be backed up

             backup_level   (enum)   : type of backup

            notify(bool)           : To notify via mail about the backup

            \*\*kwargs  (dict)              --  Optional arguments.

            Available kwargs Options:

                    agent   (str)   :   The agent, if applicable.
                    Accepted values are NDMP, CIFS and NFS.

        Returns :
             job_id : Job ID of the backup job

        Raises:
            Exception :

             -- if fails to run the backup
        """

        if str(backup_level).split('.')[1].lower() == "full":
            backup_level = RBackup.BackupType.FULL
        elif str(backup_level).split('.')[1].lower() == "incremental":
            backup_level = RBackup.BackupType.INCR
        elif str(backup_level).split('.')[1].lower() == "synthfull":
            backup_level = RBackup.BackupType.SYNTH

        self.__table.access_action_item(client_name, "Backup")

        if kwargs.get("agent", None):
            self.__restore_panel.select_agent(kwargs.get("agent").upper())
            self._admin_console.wait_for_completion()
        if backupset_name:
            self.__restore_panel.select_backupset_and_subclient(backupset_name, subclient_name)
            self.__restore_panel.submit(wait_for_load=True)
        elif subclient_name:
            self.__restore_panel.select_subclient(subclient_name)
            self.__restore_panel.submit(wait_for_load=True)

        job_id = self.__rbackup.submit_backup(backup_level, notify)

        return job_id

    @PageService()
    def run_check_readiness(self, client_name):
        """ Method to run check readiness on the given client

              Args:
                  client_name (str) --- Name of client on which check readiness operation to run

              Returns:
                      None

              Raises:
                      Exception:

                         -- if fails to run check readiness operation

              """
        self.__table.access_action_item(
            client_name, self._admin_console.props['label.readinessCheck'])
        self._admin_console.check_error_message()

    @PageService()
    def view_live_logs(self, client_name):
        """ Method to run check readiness on the given client

              Args:
                  client_name (str) --- Name of client on which check readiness operation to run

              Returns:
                      None

              Raises:
                      Exception:

                         -- if fails to run check readiness operation

              """
        self.__table.access_action_item(client_name, 'View logs')
        self._admin_console.check_error_message()

    @PageService()
    def restore_subclient(
            self,
            client_name,
            dest_client=None,
            restore_path=None,
            backupset_name=None,
            subclient_name=None,
            unconditional_overwrite=False,
            notify=False,
            selected_files=None,
            **kwargs):
        """
                Method to Restore the given client data

                Args:
                     client_name (str)      : Name of the client

                     dest_client (str)      : Name of the destination client

                     restore_path(str)      : The destination path to which content
                                              should be restored to

                     backupset_name (str)   : backup set name of the client

                     subclient_name (str)   : subclient name

                     unconditional_overwrite(bool)  : To overwrite unconditionally
                                                      on destination path

                     notify(bool)           : To notify via mail about the restore
                     selected_files (list)  : list of (str) paths pf restore content

                    kwargs  (dict)          :   Optional keyword arguments.

                        impersonate_user    (dict)  :  username and password are keys.

                        agent (str)         :  CIFS, NFS, NDMP

                Returns :
                     job_id : job id of the restore

                Raises:
                    Exception :

                     -- if fails to run the restore operation
                """

        self.__table.access_action_item(
            client_name, self._admin_console.props['label.restore'])

        if kwargs.get("agent", None):
            self.__restore_panel.select_agent(kwargs.get("agent").upper())
            self._admin_console.wait_for_completion()
        if backupset_name:
            self.__restore_panel.select_backupset_and_subclient(backupset_name, subclient_name)
            self.__restore_panel.submit(wait_for_load=True)
        elif subclient_name:
            self.__restore_panel.select_subclient(subclient_name)
            self.__restore_panel.submit(wait_for_load=True)

        return self.__fileserver_utils.restore(
            dest_client=dest_client,
            destination_path=restore_path,
            unconditional_overwrite=unconditional_overwrite,
            selected_files=selected_files,
            **kwargs
        )

    @PageService()
    def view_jobs(self, client_name):
        """
                Method to view job history for the client

                Args:
                     client_name (str)      : Name of the client

                Returns :
                     None

                Raises:
                    Exception :

                     -- if fails to run the view jobs operation
                """
        self.__table.access_action_item(
            client_name, 'View jobs')

    @PageService()
    def migrate_client_to_company(self, client_name, company_name):
        """
        Method to migrate client from one company to another

        Args:
            client_name (str) ; Name of the client to be migrated

            company_name (str) : Name of the company to be migrated to

        """
        self.__table.access_action_item(client_name, 'Change company')
        self.__drop_down.select_drop_down_values(0, list(company_name))
        self.__modal_panel.submit()
        client = self.__get_affected_client()
        if not client_name == client:
            raise CVWebAutomationException('Affected client list displays %s instead of %s' % (client, client_name))
        self.__modal_panel.submit()
        self._admin_console.check_error_message()

    @WebAction()
    def _enable_toggle(self, text):
        """ Method to select toggle
        Args:

            text(str): The text beside the toggle button

        """
        self._driver.find_element(By.XPATH, f"//span[contains(text(),'{text}')]").click()

    @WebAction()
    def _click_toggle(self, text):
        """ Method to select toggle
        Args:

            text(str): The text beside the toggle button

        """
        self._driver.find_element(By.XPATH, f"//span[contains(text(),'{text}')]").click()

    @WebAction()
    def _set_port_number(self, port):
        """ Method to select toggle
        Args:

            port(int): The text beside the toggle button

        """
        self._driver.find_element(By.ID, "sshPortNumber").send_keys(port)

    @WebAction()
    def _clear_port_number(self):
        """ Method to select toggle"""
        self._driver.find_element(By.ID, "sshPortNumber").clear()

    @WebAction()
    def _select_server_type(self, server_type):
        """ Selects Server Type"""
        self._driver.find_element(By.XPATH, f"//div[contains(text(),'{server_type}')]").click()

    @WebAction()
    def validate_type_filter(self):
        """ Validates if Type filter is present in File Servers page """
        return self._admin_console.check_if_entity_exists(
            "xpath", "//span[text()='Type']/../a[contains(@class,'uib-dropdown-toggle')]")

    @PageService()
    def install_windows_unix_client(self,
                                    file_server_host_name,
                                    username,
                                    password,
                                    os_type="Windows",
                                    reboot_required=False,
                                    plan=None,
                                    port=None,
                                    define_own_content=False,
                                    exclusions=None,
                                    exceptions=None,
                                    remove_plan_content=False,
                                    backup_system_state=False,
                                    browse_and_select_data=False,
                                    impersonate_user=None,
                                    backup_data=None):
        """Method to install a new file server

        Args:

            file_server_host_name(str)   :   hostname of the server to be added

            username(str)   :   username of the server being added

            password(str)   :   password of the server being added

            os_type(Str)         :   The Operating system of the server(windows/Unix)

            reboot_required(bool)     :  Reboot server

            port(int)        :  The non-standard SSH port number. Applicable only to Unix/Linux

            plan(str)        :  The plan to be associated with the server

            define_own_content(bool)    :   True if we want to override plan content
                                            False if we don't want to override plan content

            browse_and_select_data(bool)  : Pass True to browse and select data,
                                            False for custom path

            backup_data     (list(paths)) : Data to be backed up by new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']


            exclusions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exclusions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exceptions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exceptions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            backup_system_state (boolean)  :  boolean values to determine if system state to
                                            be backed up or not

            impersonate_user    (string): Specify username (eg: for UNC paths).

            remove_plan_content (bool)      : True for removing content inherited from plan
                                              False for keeping content inherited from plan

        """
        self._admin_console.click_button(value="Add server")
        #self._admin_console.props['label.dataSource']
        #if data source is file server
        self._admin_console.select_radio(id="WIN_OR_UNIX_FS")
        self._admin_console.wait_for_completion()
        self._admin_console.click_button(value="Next")
        self._admin_console.fill_form_by_id("displayName", file_server_host_name)
        self._driver.find_element(By.ID, 'displayName').send_keys(Keys.ENTER)
        self._admin_console.fill_form_by_id("hostName", file_server_host_name)
        self._admin_console.fill_form_by_id("fakeusernameremembered", username)
        self._admin_console.fill_form_by_id("fakepasswordremembered", password)
        self._admin_console.fill_form_by_id(
            "confirmPasswordPushInstall", password)
        if os_type == "Windows":
            self._admin_console.select_radio("osTypeWINDOWS")
        elif os_type == "Unix" or os_type == 'Linux':
            self._admin_console.select_radio("osTypeUNIX")
            if port:
                self._enable_toggle(self._admin_console.props['label.userSSHPortNumber'])
                self._admin_console.wait_for_completion()
                self._clear_port_number()
                self._admin_console.wait_for_completion()
                self._set_port_number(port)
                self._admin_console.wait_for_completion()
        else:
            raise Exception("File server OS type not valid")
        if reboot_required:
            self._enable_toggle(self._admin_console.props['label.foreceReboot'])

        if plan:
            self.__expand_backup_configuration_accordion()
            self.__addpanel.add(
                plan=plan,
                define_own_content=define_own_content,
                browse_and_select_data=browse_and_select_data,
                backup_data=backup_data,
                impersonate_user=impersonate_user,
                exclusions=exclusions,
                exceptions=exceptions,
                file_system=os_type,
                remove_plan_content=remove_plan_content,
                backup_system_state=backup_system_state,
                submit=False)

        self._admin_console.click_button_using_text("Install")
        job_id = self._admin_console.get_jobid_from_popup()
        return job_id

    @PageService()
    def add_distributed_app(self, pkg, server_name, access_nodes, plan_name):
        """Create distributed file server with given parameters.

            Args:
                pkg              (enum)  -- Instance of constants.DistributedClusterPkgName

                server_name      (str)   -- Name of the server to be created.

                access_nodes     (list)  -- list of access nodes to select

                plan_name        (str)   -- plan name to select

        """
        add_menu_id = None
        if pkg == DistributedClusterPkgName.GLUSTERFS:
            add_menu_id = 'addGlusterServer'
        elif pkg == DistributedClusterPkgName.LUSTREFS:
            add_menu_id = 'addLustreServer'
        elif pkg == DistributedClusterPkgName.GPFS:
            add_menu_id = 'addGPFSServer'
        if add_menu_id is None:
            raise CVWebAutomationException("Invalid Distributed Cluster Package name provided")

        self._admin_console.click_button("Add server")
        self._admin_console.unswitch_to_react_frame()
        self._admin_console.click_by_id(add_menu_id)

        self._admin_console.fill_form_by_id('serverName', server_name)
        self.__drop_down.select_drop_down_values(drop_down_id='accessnode-selection-dropdown', values=access_nodes)
        self.__drop_down.select_drop_down_values(drop_down_id='planSummaryDropdown', values=[plan_name])
        self._admin_console.submit_form()

    @PageService()
    def add_ibmi_client(self,
                        server_name,
                        file_server_host_name,
                        username,
                        password,
                        access_node,
                        data_path=None,
                        port=None,
                        plan=None,
                        subsystem_description=None,
                        job_queue=None,
                        create_jobq=None,
                        job_priority=None,
                        run_priority=None
                        ):
        """Method to add a new IBMi client.

        Args:

            server_name(str)                :   Name of the client

            file_server_host_name(str)      :   hostname of the server to be added

            username(str)                   :   username of the server being added

            password(str)                   :   password of the server being added

            access_node(list)                :   Name of the access node client

            data_path(str)                  :   Commvault data path on client machine.
                default: None (to take default value populated in CC)

            port(int)                       :  The port number on client machine
                default: None

            plan(str)                       :  The plan to be associated with the server
                default: None

            subsystem_description(str)      :   Subsystem description in <LIB>/<SBSD> format.
                default: None

            job_queue(str)                  :   job queue in <LIB>/<JOBQ> format.
                default: None

            create_jobq(bool)               :   Create the jobq under CVLIBOBJ library
                default: None

            job_priority(int)               :   job priority of Commvault jobs on client machine
                defalt: None

            run_priority(int)               : run priority of Commvault jobs on client machine
                default: None
        Return: notification

        """
        # Click on add server from file server page
        self._admin_console.click_button("Add server")

        # Select type of client as IBMi client under wizard: Configure File Server
        self.__wizard.select_radio_card('IBM i')
        self.__wizard.click_next()

        # Fill Server configuration details of IBMi client
        self.__wizard.fill_text_in_field(id="serverName", text=server_name)
        self.__wizard.fill_text_in_field(id="hostName", text=file_server_host_name)
        self.__wizard.fill_text_in_field(id="ibmiUserName", text=username)
        self._set_password(element_id="ibmiPassword", password=password)
        self._set_password(element_id="ibmiConfirmPassword", password=password)
        self.__wizard.click_next()

        # Fill Access node & plan details under wizard:Backup configuration
        self.__rdropdown.select_drop_down_values(drop_down_id="ibmiAccessNode", values=access_node)
        if plan:
            self.__wizard.select_plan(plan_name=plan)
        else:
            self._click_toggle(text="Configure plan")
        self.__wizard.click_next()

        # Populate data path and IBMi port details
        # if data_path:
        #     # Entering data path is currently removed from react pages.
        # if port:
        #     # Entering client port number is currently removed from react pages.

        # Fill IBMi advanced options for client configuration
        if subsystem_description:
            self.__wizard.fill_text_in_field(id="subSystemDescription", text=subsystem_description)
            self._admin_console.wait_for_completion()
        if job_queue:
            self.__wizard.fill_text_in_field(id="jobQueue", text=job_queue)
            self._admin_console.wait_for_completion()
        if create_jobq:
            self._click_toggle(text="Create job queue")
            self._admin_console.wait_for_completion()
        if job_priority:
            self.__wizard.fill_text_in_field(id="jobPriority", text=str(job_priority))
            self._admin_console.wait_for_completion()
        if run_priority:
            self.__wizard.fill_text_in_field(id="runPriority", text=str(run_priority))
            self._admin_console.wait_for_completion()
        self.__wizard.click_button(name="Add")
        notification = self._admin_console.get_notification(wait_time=600)
        return notification

    @WebAction(hide_args=True)
    def _set_password(self, element_id, password):
        """Enter password in specified element found by ID"""
        pwd_box = self._driver.find_element(By.ID, element_id)
        pwd_box.send_keys(password)

    @PageService()
    def is_client_exists(self, server_name):
        """ check client entry existence from file server page
        Args:
                server_name     (str) -- server name to retire

        returns: boolean
            True: if server exists
            false: if server does not exists
        """
        status = self.__table.is_entity_present_in_column(column_name='Name',
                                                          entity_name=server_name)
        return status

    @PageService()
    def retire_ibmi_client(self, server_name):
        """Performs retire action for the given IBMi client

        Args:
                server_name     (str) -- IBMi client name to retire
        """
        self.__table.access_action_item(server_name, self._admin_console.props['action.commonAction.retire'])
        self._admin_console.fill_form_by_id("confirmText",
                                            self._admin_console.props['action.commonAction.retire'].upper())
        self._admin_console.click_button_using_text(self._admin_console.props['action.commonAction.retire'])
        notification = self._admin_console.get_notification(wait_time=300)
        return notification

    @PageService()
    def navigate_to_file_server_tab(self):
        """ access the File server tab of Manage-->File servers (tab if exists).
        """
        self._navigator.navigate_to_file_servers()
        if self._admin_console.check_if_entity_exists("id", "FileServersList"):
            self._admin_console.access_tab("File servers")

    @PageService()
    def retire_server(self, server_name):
        """Performs retire action for the given server

        Args:
                server_name     (str) -- server name to retire
        """
        self.__table.access_action_item(server_name, self._admin_console.props['action.commonAction.retire'])
        self._admin_console.fill_form_by_id("confirmText",
                                            self._admin_console.props['action.commonAction.retire'].upper())
        self._admin_console.click_button_using_text(self._admin_console.props['action.commonAction.retire'])
        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def action_add_software(
            self,
            client_name=None,
            select_all_packages=False,
            packages=None,
            reboot=False):
        """selects the Add software option for the given client

        Args:
            client_name     (str)       -- client to add software on

            select_all_packages  (bool)  -- selects all the packages if set True
                                            (default: False)

            packages        (list)      -- list of packages to be installed

            reboot          (bool)      -- set to True if reboot required
                                            (default: False)
        """
        self._admin_console.refresh_page()
        self.__table.access_action_item(
            client_name, self._admin_console.props['action.addSoftware'])
        if select_all_packages:
            self.__drop_down.select_drop_down_values(0, select_all=True)
        elif packages:
            self.__drop_down.select_drop_down_values(0, packages)
        else:
            raise CVWebAutomationException('Packages list is not provided')
        if reboot:
            self._enable_toggle(self._admin_console.props['label.foreceReboot'])
        self._admin_console.submit_form()
        job_id = self.__get_job_id_page()
        self._admin_console.click_button(self._admin_console.props['OK'])
        return job_id

    @PageService()
    def action_update_software(self, client_name=None, reboot=False):
        """selects the update software option for the given client

        Args:
            client_name     (str) -- client to update software on

            reboot      (bool)    -- set to True if reboot required
         """
        self._admin_console.refresh_page()
        self.__table.access_action_item(
            client_name, self._admin_console.props['label.upgradeSoftware'])
        if reboot:
            self._enable_toggle(self._admin_console.props['label.foreceReboot'])

        self._admin_console.click_button_using_text(self._admin_console.props['button.yes'])
        self._admin_console.unswitch_to_react_frame()
        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def action_uninstall_software(self, client_name=None, packages=None):
        """
        uninstalls selected packages for a client
        Args:
            client_name     (str)       -- client to uninstall software on
            packages        (list)      -- list of packages to be uninstalled

        """
        self.__table.access_action_item(
            client_name, self._admin_console.props['label.uninstallSoftware'])
        if packages:
            self.__drop_down.select_drop_down_values(0, packages)
            self._admin_console.click_button(self._admin_console.props['action.uninstall'])
        else:
            raise CVWebAutomationException('Packages list is not provided')
        self._admin_console.click_button_using_text(self._admin_console.props['button.yes'])
        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def action_sendlogs(self, client_name=None):
        """selects sendlogs option for the given client"""
        self.__table.access_action_item(
            client_name, self._admin_console.props['action.commonAction.sendLogs'])

    @PageService()
    def filter_file_server_by_type(self, fs_type='Windows'):
        """Method to filter file server list from the Type filter drop down"""
        self.__rdropdown.select_drop_down_values(values=[fs_type], drop_down_id="Type")
        self._admin_console.wait_for_completion()

    @PageService()
    def add_nas_client(self, name, host_name, plan, vendor=None, **kwargs):
        """
        Adds a new NAS File Server with the Chosen iDAs and Access Node.

        Args:
            name        (str)    :   The  name of the NAS/Network Share client to be created.

            host_name   (str)    :   The host name of the NAS/Network Share client to be created.

            plan        (str)    :   The name of the plan that needs to be associated to the client.

            vendor      (Vendor(Enum))  :   The name of the vendor, supports following values.
                -   DELL_EMC_ISILON

            \*\*kwargs  (dict)              --  Optional arguments.

            Available kwargs Options:

                    array_details   (dict)  :   The dictionary of array details.
                     Dictionary contains the keys array_name, control_host, username and password.

                        array_name      (str)    :   Name of the array.

                        control_host    (str)    :   Control host name if applicable to the array.

                        username        (str)    :   Username for the array, defined in CoreUtils\config.json.

                        password        (str)    :   Password for the array, defined in CoreUtils\config.json.

                         access_nodes    (str)   :   access nodes for the array

                    cifs            (dict)  :   The dictionary of CIFS Agent details.
                    Dictionary contains the keys access_nodes, impersonate_user and content.

                        access_nodes        (list)  :   List of access node names, access node names are strings.

                        impersonate_user    (dict)  :   The dictionary of impersonation account details.
                        Dictionary contains the keys username and password.

                            username    (str)    :   Username of the account, defined in CoreUtils\config.json.

                            password    (str)    :   Password of the account, defined in CoreUtils\config.json.

                            client_level_content    (list)  :   List of content paths, content paths are strings.
                     ndmp            (dict)  :   The dictionary of NDMP Agent details.
                    Dictionary contains the keys access_nodes, impersonate_user and content.

                        access_nodes        (list)  :   List of access node names, access node names are strings.

                        impersonate_user    (dict)  :   The dictionary of impersonation account details.
                        Dictionary contains the keys username and password.

                            username    (str)    :   Username of the account, defined in CoreUtils\config.json.

                            password    (str)    :   Password of the account, defined in CoreUtils\config.json.

                            credential_manager (bool) : if credential manager cred passed in json set to True else False

                            credential_manager_name (str) : credential manager name

                           client_level_content  (list)  :   List of content paths, content paths are strings.
                     nfs            (dict)  :   The dictionary of CIFS Agent details.
                    Dictionary contains the keys access_nodes, impersonate_user and content.

                        access_nodes        (list)  :   List of access node names, access node names are strings.

                        client_level_content     (list)  :   List of content paths, content paths are strings.

        """
        self.nas_file_server.add_nas_client(name, host_name, plan, vendor, **kwargs)

    @WebAction()
    def __get_protocols_text(self):
        """Gets text from the dialog box containing all protocols"""

        xp = f'//div[contains(@class, "sc-himrzO ibttMo MuiFormControl-root")]/label/' \
             f'span[contains(@class, "MuiFormControlLabel-label")]'
        return [i.text for i in self._admin_console.driver.find_elements(By.XPATH, xp)]

    @WebAction()
    def __release_licence_agent(self, agent):
        """ Release CIFS and NFS Licenses
            Args:
                Agent - str - CIFS/NFS/NDMP
        """
        self.__dialog.select_checkbox(checkbox_label=agent)

    @PageService()
    def release_license(self):
        """"
              Release CIFS and NFS Licenses
        """

        self._admin_console.click_button_using_text("Release license")
        if "Server File System - Linux File System" in self.__get_protocols_text():
            self.__release_licence_agent("Server File System - Linux File System")

        if "Server File System - Windows File System" in self.__get_protocols_text():
            self.__release_licence_agent("Server File System - Windows File System")

        if "NDMP - NDMP" in self.__get_protocols_text():
            self.__release_licence_agent("NDMP - NDMP")

        if "Hardware Snapshot Enabler - Snap Backup" in self.__get_protocols_text():
            self.__release_licence_agent("Hardware Snapshot Enabler - Snap Backup")

        self._admin_console.click_button("Save")

    @PageService()
    def delete_client(self, server_name):
        """
        Performs delete action for given server

        Args:
            server_name     (str):   the name of the server

        """
        self.__table.access_action_item(server_name, "Delete")
        self._admin_console.fill_form_by_id("confirmText", "DELETE")
        self._admin_console.click_button("Delete")
        self._admin_console.get_notification(wait_time=60)

    @PageService()
    def restart_client_service(self, server_name):
        """
        Restart services on given server

        Args:
             server_name (str)      : Name of the server
        """
        self.__table.access_action_item(
            server_name, self._admin_console.props['label.globalActions.restartServices'])
        self._admin_console.click_button_using_text('Yes')
        self._admin_console.wait_for_completion()

    @PageService()
    def reconfigure_server(self, server_name):
        """
        Performs reconfigure action for the given server

        Args:
            server_name     (str):   the name of the server
        """

        self.__table.access_action_item(server_name, self._admin_console.props['label.reconfigure'])
        self._admin_console.click_button_using_text(self._admin_console.props['action.commonAction.reconfigure'])
        self._admin_console.click_button_using_text('Yes')
        self._admin_console.get_notification(wait_time=60)

    @PageService()
    def change_server_name(self, name):
        """
        Renames the file server name
        Args:
            name(str): name of the server to be renamed
        """
        self.__page_container.edit_title(name)
        self._admin_console.wait_for_completion()

    @PageService()
    def manage_plan(self, server, plan):
        """
        add/manage plan for a server
        Args:
            server(str): name of the file server
            plan(str): plan to be assigned to the File server
        """
        self._navigator.navigate_to_file_servers()
        self.__table.access_action_item(server, 'Manage plan')
        self.__rdropdown.select_drop_down_values(drop_down_id="subclientPlanSelection", values=[plan])
        self.__rmodal_panel.save()

    @PageService()
    def action_list_snaps(self, client_name):
        """
        Lists the snaps on client level with the given name

        Args :
            client_name   (str)   --  the name of the client whose snaps are to listed
        """
        self._admin_console.refresh_page()
        self.__table.access_action_item(client_name, self._admin_console.props['action.listSnaps'])


class RestorePanel(RModalPanel):
    """ Class to handle restore panel related operations """

    @WebAction()
    def _select_checkbox(self, element):
        """ Method to toggle inplace option"""
        self._driver.find_element(By.XPATH,
                                  f'//label[@for="{element}"]'
                                  ).click()

    @WebAction()
    def _click_browse(self):
        """ Method to click on browse button during destination path selection screen """
        if self._admin_console.check_if_entity_exists('id', 'BrowsePath'):
            self._driver.find_element(By.ID, 'BrowsePath').click()
        else:
            self._driver.find_element(By.XPATH,
                                      '//button[@id="fsRestoreOptions_button_#6719"]'
                                      ).click()

    @WebAction()
    def __enable_notify_via_email(self):
        """ Enables notify via email checkbox """
        self._driver.find_element(By.XPATH, "*//span[contains(text(),'Notify via email')]").click()

    @WebAction()
    def _click_agent(self, agent_name):
        """
        Clicks the Protocol (CIFS / NFS) for NAS Clients
        """
        old_table = Table(self._admin_console)
        old_table.view_by_title(value=agent_name, label="Protocol")
        self._admin_console.wait_for_completion()

    @WebAction()
    def _click_backupset_and_subclient(self, backupset_name, subclient_name):
        """Selects the required backup set and subclient
        Args:
            backupset_name (String) : Name of backup set to be selected

            subclient_name (String) : Name of the subclient to be selected

        """
        rdropdown = RDropDown(self._admin_console)
        rtable = Rtable(self._admin_console)
        if rdropdown.is_dropdown_exists(drop_down_id="Backup sets"):
            rtable.set_default_filter(
                filter_id="Backup sets", filter_value=backupset_name
            )

        self.select_subclient(subclient_name)
        self._admin_console.wait_for_completion()

    @WebAction()
    def __click_subclient(self, subclient_name):
        """Method to click on subclient"""
        subclient = self._driver.find_element(By.XPATH, f"//div[normalize-space()='{subclient_name}']/ancestor::tr//input")
        if subclient.is_displayed():
            subclient.click()

    @PageService()
    def select_backupset_and_subclient(self, backupset_name, subclient_name):
        """Selects the required backup set and subclient
        Args:
            backupset_name (String): Name of backup set to be selected

            subclient_name (String): Name of the subclient to be selected

        """
        self._click_backupset_and_subclient(backupset_name, subclient_name)

    @PageService()
    def select_agent(self, agent_name):
        """
        Selects the Protocol (CIFS / NFS) for NAS Clients
        """

        self._click_agent(agent_name)

    @WebAction()
    def __click_search(self):
        """Clicks the search option in restore page"""
        self.__clear_search()
        self._driver.find_element(By.XPATH,
                                  "//input[contains(@placeholder,'Search for files')]").click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def __clear_search(self):
        """Clears the search"""
        clear = self._driver.find_elements(By.XPATH,
                                           "//span[contains(@class,'form-control-clear glyphicon')]")
        if clear:
            if clear[0].is_displayed():
                clear[0].click()

    @WebAction()
    def _enter_search_value(self, search_type, value):
        """Enters the value in search
                Args:
                    search_type (String): Category type (eg:filename, contains)
                    value   (String): Value to be entered
        """
        search = self._driver.find_element(By.XPATH,
                                           f"//span[@class='ng-binding ng-scope']//label[text()='{search_type}']/following-sibling::input")
        search.click()
        search.clear()
        search.send_keys(value)

    @WebAction()
    def _select_value(self, label, value):
        """Selects file type
                Args:
                    label (String): Category type (eg:Modified, fileType)
                    value (String): Value to be entered
                                        (eg:'file.txt', 'test.html')
        """
        self._driver.find_element(By.XPATH,
                                  f"//label[text()='{label}']/following-sibling::select/option[@label='{value}']").click()

    @WebAction()
    def __click_time_tab(self, label):
        """Select the time tab
                Args:
                    label   (String): Category type (eg:From Time, To Time)
        """
        self._driver.find_element(By.XPATH,
                                  f"//label[text()='{label}']/following-sibling::span/button[@class='btn btn-default']").click()

    @WebAction()
    def _select_time_range(self, label, time):
        """Selects the time range
                Args:
                    label   (String): Category type (eg:From Time, To Time)
                    time (str): the backup date in 01-March-2019 format
        """
        self.__click_time_tab(label)
        if time:
            calender = {'date': time.split("-")[0], 'month': time.split("-")[1], 'year': time.split("-")[2]}
            self._admin_console.date_picker(calender)

    @WebAction()
    def __check_check_box(self, label, value):
        """ Checks if the checkbox is selected or not
                Args:
                    label (String): Category type (eg:IncludeFolders:, showDeletedFiles:)
                    value (bool): Value to be entered
                                        (eg:'file.txt', 'test.html')
        """
        elem = self._driver.find_elements(By.XPATH, f"//*[@id='{label}' and contains(@class,'ng-not-empty')]")
        elem1 = self._driver.find_elements(By.XPATH, f"//*[@id='{label}' and contains(@class,'ng-empty')]")
        if elem1 and value:
            self._select_checkbox(label)
        if elem and not value:
            self._select_checkbox(label)
        self._admin_console.wait_for_completion()

    @WebAction()
    def __submit_search(self):
        """Submit the search option"""
        self._driver.find_element(By.XPATH, f"//*[@id='cv-search-box_button_#9364']").click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _select_backupset_from_search(self, backupset_name):
        """
        Selects the backupset name in search for files
        Args:
            backupset_name (str): Name of the backupset to select from search
        """
        self._driver.find_element(By.XPATH,
                                  f'//label[contains(text(), "Backup set")]/following-sibling::select/option[@label="{backupset_name}"]'
                                  ).click()
        self._admin_console.wait_for_completion()

    @PageService()
    def search_files_for_restore(self, file_name=None, contains=None, file_type=None, modified=None,
                                 backupset_name=None, from_time=None, to_time=None, include_folders=True,
                                 show_deleted_files=True):
        """Search the files based on the parametes provided
                Args:
                    file_name (String): Name of file to be searched
                                        (eg:'file.txt', 'test.html')
                    contains  (String): pattern string that the files contain
                                        (eg:'html', 'automation')
                    file_type  (String): The type of the file to be searched
                                         (eg:'Audio', 'Image', 'Office', 'Video',
                                             'System', 'Executable')
                    modified   (String): Modified time of file to be searched
                                         (eg:'Today', 'Yesterday', 'This week')
                    backupset_name (String): Name of the backupset to be deleted.
                                            (Applicable when searching files from fsagent)
                    from_time   (String): The files backed up from date
                    to_time     (String): The files backed up to this date
                    include_folders (bool): True is to include folder while search is applied
                    show_deleted_files (bool): True is to apply search for deleted items
        """
        self.__click_search()
        if file_name:
            self._enter_search_value('Filename:', file_name)

        if contains:
            self._enter_search_value('Contains:', contains)

        if file_type:
            self._select_value("File Type:", file_type)

        if modified:
            if modified != 'Time Range':
                self._select_value("Modified:", modified)
            else:
                self._select_value("Modified:", modified)
                if from_time:
                    self._select_time_range("From time", from_time)
                if to_time:
                    self._select_time_range("To time", to_time)

        # To select backupset from search bar in fsAgentDetails page
        if backupset_name:
            self._select_backupset_from_search(backupset_name)

        self.__check_check_box("IncludeFolders:", include_folders)
        self.__check_check_box("showDeletedFiles:", show_deleted_files)
        self.__submit_search()

    @PageService()
    def select_destination_client(self, client_name):
        """Method to select client from drop down in restore panel"""

        self._admin_console.wait_for_completion()
        self._dropdown.select_drop_down_values(0, values=[client_name], partial_selection=True)
        self._admin_console.wait_for_completion()

    @PageService()
    def select_overwrite(self):
        """Method to select unconditional overwrite in restore panel"""
        self._select_checkbox("overwrite")
        self._admin_console.wait_for_completion()

    @PageService()
    def deselect_acl_for_restore(self):
        """Method to deselect acls option in restore panel"""
        self._select_checkbox("acls")
        self._admin_console.wait_for_completion()

    @PageService()
    def deselect_data_for_restore(self):
        """Method to deselect data option in restore panel"""
        self._select_checkbox("data")
        self._admin_console.wait_for_completion()

    @PageService()
    def select_browse_for_restore_path(self, toggle_inplace=True):
        """Method to click on browse in restore panel
        Args:

            toggle_inplace (bool): to toggle inplace option
                default: True

        """
        if toggle_inplace:
            self._select_checkbox("inplace")
        self.select_browse_in_restore()

    @PageService()
    def select_browse_in_restore(self):
        """Method to click on browse in restore panel"""
        self._click_browse()
        self._admin_console.wait_for_completion()

    @PageService()
    def submit_restore(self, notify=False, impersonate_dialog=False):
        """ Method to submit restore job
        Args:

            notify (bool): to enable by email

        Returns:
            job_id: job id from notification
        """

        if notify:
            self.__enable_notify_via_email()
        self.submit(wait_for_load=True)
        if impersonate_dialog:
            dialog = ModalDialog(self._admin_console)
            dialog.click_submit()
        return self._admin_console.get_jobid_from_popup(wait_time=20)

    @PageService()
    def select_subclient(self, subclient_name):
        """Method to select subclient while restore
        Args:
            subclient_name (str): subclient name to choose
        """
        self.__click_subclient(subclient_name)


class AddPanel:

    def __init__(self, admin_console):
        """
        Args:
        admin_console(AdminConsole): adminconsole
        object
        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver

        # Components required
        self.__table = Rtable(self.__admin_console)
        self.__panel = Backup(self.__admin_console)
        self.__browse = Browse(self.__admin_console)
        self.__plan_details = PlanDetails(self.__admin_console)
        self.__contentbrowse = ContentBrowse(self.__admin_console)
        self.__dropdown = DropDown(self.__admin_console)

    @WebAction()
    def add_custom_path(self, path):
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

    @WebAction()
    def click_add_custom_path(self):
        """Clicks the add custom path icon"""
        add_path_icon_xpath = "//i[@title='Add']"
        custom_path_add = self.__driver.find_elements(By.XPATH, add_path_icon_xpath)
        for path_add in custom_path_add:
            if path_add.is_displayed():
                path_add.click()

    @WebAction()
    def toggle_own_content(self):
        """toggles the override backup content option"""
        self.__driver.find_element(By.XPATH,
                                   f'//span[@class="help-label ng-binding" and text()="Define your own backup content"]').click()

    @WebAction()
    def browse_and_select_data(self, backup_data, file_system):
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
                    start = tag + 1

            for i in range(0, count + 1):
                directory, sep, folder = data.partition(pattern)
                data = folder
                if directory != '':
                    directories.append(directory)
            path = len(directories)

            for i in range(0, path - 1):
                if self.__driver.find_element(By.XPATH,
                                              "//span[contains(text(),'" + str(directories[i]) + "')]/../../button"). \
                        get_attribute("class") == 'ng-scope collapsed':
                    self.__admin_console.click_by_xpath(
                        "//span[contains(text(),'" + str(directories[i]) + "')]/../../button")
                dest = i + 1
            self.__admin_console.click_by_xpath(
                "//span[contains(text(),'" + str(directories[dest]) + "')]")
        self.__admin_console.click_button(self.__admin_console.props['label.save'])

    @WebAction(delay=5)
    def __click_remove_plan_content(self):
        """
        removes the content inherited from plan
        """
        elem = "//div[contains(@class,'ui-grid-selection-row-header-buttons ui-grid-icon-ok ng-pristine ng-untouched ng-valid ng-scope')]"
        checkbox = self.__driver.find_elements(By.XPATH, elem)
        for files in checkbox:
            if files.is_displayed():
                files.click()

    @WebAction()
    def __select_credentials(self, value):
        """ Selects radio button for Impersonate User"""
        self.__driver.find_element(By.XPATH, f"//span[contains(text(),'{value}')]").click()

    @PageService()
    def access_content_tab(self):
        """Access the content tab"""
        self.__panel.access_tab(self.__admin_console.props['label.content'])

    @PageService()
    def access_exclusions_tab(self):
        """Access the content tab"""
        self.__panel.access_tab(self.__admin_console.props['label.Exclusions'])

    @PageService()
    def access_exceptions_tab(self):
        """Access the content tab"""
        self.__panel.access_tab(self.__admin_console.props['label.Exceptions'])

    @PageService()
    def select_plan(self, plan_name):
        """Selects the plan from the dropdown"""
        self.__dropdown.select_drop_down_values(drop_down_id='planSummaryDropdown', values=[plan_name])

    @PageService()
    def remove_plan_content(self):
        """Clicks the remove plan content"""
        self.__click_remove_plan_content()
        self.__admin_console.wait_for_completion()
        self.__admin_console.select_hyperlink(self.__admin_console.props['label.globalActions.remove'])

    @PageService()
    def set_custom_content(self, data):
        """Sets the custom paths for all types of data"""
        for path in data:
            self.add_custom_path(path)
            self.click_add_custom_path()
            self.__admin_console.wait_for_completion()
            if self.__admin_console.check_if_entity_exists("xpath", "//h1[text()='Impersonate user']"):
                self.__admin_console.cancel_form()

    @PageService()
    def set_impersonate_user_credentials(self, impersonate_user):
        """Sets the credentials for the impersonate user"""
        if isinstance(impersonate_user, str):
            self.__select_credentials("Use saved credentials")
            self.__admin_console.cv_single_select("Saved credentials", impersonate_user)
            self.__admin_console.submit_form()

        elif isinstance(impersonate_user, dict):
            self.__admin_console.fill_form_by_name('loginName', impersonate_user['username'])
            self.__admin_console.fill_form_by_name('password', impersonate_user['password'])
            self.__admin_console.submit_form()

    @PageService()
    def submit(self):
        """Submits the modal form"""
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @PageService()
    def add(self,
            plan,
            define_own_content=False,
            browse_and_select_data=False,
            backup_data=None,
            impersonate_user=None,
            exclusions=None,
            exceptions=None,
            backup_system_state=None,
            file_system='Windows',
            remove_plan_content=False,
            submit=True,
            toggle_own_content=True):
        """
        Method to Add content,exclusions,exceptions

        Args:
            plan (string): plan name to be used as policy for new sub client backup.

            define_own_content(bool): Pass True to define own content
                                        False for associated plan content

            browse_and_select_data(bool): Pass True to browse and select data,
                                            False for custom path

            backup_data     (list(paths)): Data to be backed up by new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            impersonate_user    (string): Specify username (eg: for UNC paths).

            exclusions       (list(paths)): Data to be backed up by new sub client created
                Eg. exclusions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exceptions       (list(paths)): Data to be backed up by new sub client created
                Eg. exceptions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            backup_system_state (String): System state to be enabled or not.

            file_system       (string):  file system of the client
                Eg. - 'Windows' or 'Unix'

            remove_plan_content (bool): True for removing content inherited from plan
                                              False for keeping content inherited from plan

            submit              (bool): True if the user wants to submit the form
                                      : False if the user doesn't want to submit the form

            toggle_own_content  (bool): Pass True to toggle override backup content
                                        False for not toggling
        Raises:
            Exception:
                -- if fails to add entity

        """

        self.select_plan(plan)

        #Need toggle feature for File System solution
        #Changed default value for toggle_own_content in fsagent as testcase should pass the required parameters
        if define_own_content:
            if toggle_own_content:
                self.__admin_console.enable_toggle(index=0, cv_toggle=True)

        if remove_plan_content:

            # Backup content is not derived from plan for NAS file servers
            if file_system.lower() != 'nas':
                self.remove_plan_content()

            if browse_and_select_data:
                self.__admin_console.select_hyperlink(self.__admin_console.props['header.content'])
                self.__admin_console.select_hyperlink(self.__admin_console.props['action.browse'])
                self.browse_and_select_data(backup_data, file_system)
                self.__admin_console.wait_for_completion()

            else:
                self.set_custom_content(backup_data)

            if impersonate_user:
                self.__admin_console.select_hyperlink(
                    self.__admin_console.props['label.impersonateUser'])
                self.__admin_console.wait_for_completion()

                self.set_impersonate_user_credentials(impersonate_user)

            if exclusions:
                self.access_exclusions_tab()
                self.set_custom_content(exclusions)

            if exceptions:
                self.access_exceptions_tab()
                self.set_custom_content(exceptions)

            if backup_system_state:
                self.__admin_console.enable_toggle(0)
            elif backup_system_state is not None:
                self.__admin_console.disable_toggle(0)

        if submit:
            self.submit()


class AddWizard:

    def __init__(self, admin_console):
        """
        Args:
        admin_console(AdminConsole): adminconsole object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.__rdropdown = RDropDown(self._admin_console)
        self.__wizard = Wizard(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__rtable = Rtable(admin_console)

    @WebAction()
    def __refresh_server_list(self, formid, index=0):
        """click refresh button for server list"""
        xpath = "//*[@id='" + formid + "']//button"
        elems = self._driver.find_elements(By.XPATH, xpath)
        self._admin_console.scroll_into_view_using_web_element(elems[index])
        elems[index].click()

    def __click_download(self, os_name=None):
        """
        click download option
        """
        xpath_gateway_windows = "//div[contains(text(),'Windows (64-bit)')]"
        if self._admin_console.check_if_entity_exists('xpath', xpath_gateway_windows):
            self._driver.find_element(By.XPATH, xpath_gateway_windows).click()
        else:
            if os_name and "windows (32-bit)" in os_name.lower():
                self.__rtable.access_link_without_text("Windows (32-bit)", "Download")
            elif os_name and "windows" in os_name.lower():
                self.__rtable.access_link_without_text("Windows (64-bit)", "Download")
            elif os_name and ("linux" in os_name.lower() or "unix" in os_name.lower()):
                self.__rtable.access_link_without_text("Linux (64-bit)", "Download")
            elif os_name and "hp-ux" in os_name.lower():
                self.__rtable.access_link_without_text("HP-UX", "Download")
            elif os_name and "powerpc" in os_name.lower():
                self.__rtable.access_link_without_text("PowerPC", "Download")
            elif os_name and "solaris" in os_name.lower():
                self.__rtable.access_link_without_text("Solaris (64-bit)", "Download")
            elif os_name and "aix" in os_name.lower():
                self.__rtable.access_link_without_text("AIX", "Download")
            elif os_name and "sparc" in os_name.lower():
                self.__rtable.access_link_without_text("Sparc (64-bit)", "Download")
            elif os_name and "freebsd" in os_name.lower():
                self.__rtable.access_link_without_text("FreeBSD (64-bit)", "Download")
            else:
                self._admin_console.log.info("Download option does not show up")

    @WebAction()
    def __add_custom_path(self, path):
        """
        Add custom paths in the custom path input box
            Args:
                path (str)      :   Data path to be added
        """
        custom_input_xpath = "//input[@id='custom-path']"
        custom_path_input = self._admin_console.driver.find_elements(By.XPATH,
                                                                     custom_input_xpath)[-1:][0]
        custom_path_input.clear()
        custom_path_input.send_keys(path)
        custom_path_input.send_keys(Keys.RETURN)

    def add_path(self, path):
        self.__add_custom_path(path)

    def __is_plan_selected(self, plan_name):
        """check whether provided plan is selected
            Args:
                plan_name (str)      :   plan name
        """
        xp = f"//span[contains(text(),'{plan_name}')]"
        span_elem = self._admin_console.driver.find_element(By.XPATH, xp)
        plan_elem = span_elem.find_element(By.XPATH, "..")
        # if plan is selected, border-left-color is "rgba(121, 77, 232, 1)"
        if "rgba(121, 77, 232, 1)" not in plan_elem.value_of_css_property(
                "border-left-color"):
            return False
        else:
            return True

    @WebAction()
    def _get_last_element(self, value):
        """get the last element with value as text value
            Args:
                value    (str)    :    element value
        """
        return self._admin_console.driver.find_elements(By.XPATH, f"//button[contains(.,'{value}')]")[-1]

    @PageService()
    def configure_iam_role_for_oci(self, credential: str = None):
        """
        Creates a stack in oci or uses an existing one if credential is provided

        Args:
            credential (str): Credential to use
        """

        if credential:
            self.__rdropdown.select_drop_down_values(values=[credential], drop_down_id="credentials")
        else:
            # Create stack
            pass

        self.__wizard.click_next()

    @PageService()
    def select_file_server_env(self, physical=False, backuptocloud=True, on_premise=True, cloudvendor=''):
        """
        Select file server environment when configuring new servers
            Args:
                physical (bool)      :   is physical or virtual machine
                backuptocloud (bool) :   backup to cloud or backup via gateway
                on_premise (bool) : Whether to configure soultion for on_premise client or not
                cloudvendor (str) : The clound vendor on which the machine resides
        """
        
        if on_premise:
            time.sleep(30)
            self.__wizard.select_radio_button(id='physicalSystem')
            self._admin_console.scroll_into_view("Cancel")
            if physical:
                self.__wizard.select_drop_down_values(id="fsLocationType", values=["Physical client"])
            else:
                self.__wizard.select_drop_down_values(id="fsLocationType", values=["Virtual machine"])
            self.__wizard.click_next()
            try:
                self.__dialog.click_button_on_dialog(text="Continue")
            except BaseException:
                pass
            try:
                self._admin_console.click_button("Start trial")
                self._get_last_element("Close").click()
                self.__wizard.click_button("Close")
            except BaseException:
                pass

            if backuptocloud:
                self.__wizard.select_radio_button(id='cloudStorage')
            else:
                self.__wizard.select_radio_button(id='accessNode')
            time.sleep(120)
            self.__wizard.click_next()
        else:
            self.__wizard.select_radio_button(id="virtualMachine")
            if cloudvendor == 'Microsoft Azure':
                self.__wizard.select_drop_down_values(id="vendorType", values=["Microsoft Azure"])
            elif cloudvendor == 'Amazon Web Services':
                self.__wizard.select_drop_down_values(id="vendorType", values=["Amazon Web Services"])
            else:
                self.__wizard.select_drop_down_values(id="vendorType", values=["Oracle Cloud Infrastructure"])

            self.__wizard.click_next()
            try:
                self.__dialog.click_button_on_dialog(text="Continue")
            except BaseException:
                pass
            try:
                self._admin_console.click_button("Start trial")
                self._get_last_element("Close").click()
                self.__wizard.click_button("Close")
            except BaseException:
                pass
            if (cloudvendor == 'Amazon Web Services') and not backuptocloud:
                self.__wizard.select_radio_button(id='DeployByob')
            self.__wizard.click_next()

    @PageService()
    def configure_region(self, region):
        """configures region
            Args:
                region   (string) :  region name
        """
        self.__wizard.select_drop_down_values(id="storageRegion", values=region)
        self.__wizard.click_next()

    @PageService()
    def configure_AWS_permission(self, authmethod="IAM Role"):
        """configure authentication method for AWS
            Args:
                authmethod    (sring)  :  authentication method, default value "IAM Role"
		"""
        self.__wizard.select_drop_down_values(id="authenticationMethod", values=[authmethod])
        self.__wizard.checkbox.check(id='undefined')
        self.__wizard.click_next()

    @PageService()
    def add_new_gateway(self, installinputs):
        """
        add new gateway node
            Args:
                installinputs (dict)    :    Inputs for Install
        """
        self.__wizard.click_add_icon()
        time.sleep(60)
        self.__click_download()
        time.sleep(300)
        self.__dialog.click_close()
        self.interactive_install_machine(installinputs)
        self.__wizard.click_refresh_icon()
        time.sleep(60)

    @PageService()
    def add_new_server(self, installinputs):
        """
        interactively install and configure new server, once done, click Next button
            Args:
                installinputs (dict)    :    Inputs for Installation
        """
        self.__click_download(installinputs['os_type'])
        time.sleep(300)
        self.interactive_install_machine(installinputs)
        time.sleep(180)
        self.__refresh_server_list('serverConfigurationForm', index=0)
        time.sleep(60)

        installinputs["commcell"].refresh()
        servername = installinputs["commcell"].clients.get(
            installinputs["remote_clientname"]).display_name

        self.__wizard.select_drop_down_values(id='serverName', values=[servername])
        self.__wizard.click_next()

    @PageService()
    def add_new_server_silent_install(self, installinputs):
        """
        Install and configure new server using Silent Install command, once done, click Next button
            Args:
                installinputs (dict)    :    Inputs for Installation
        """
        fsinstallhelper = RFsInstallHelper(self._admin_console)
        self.__click_download(installinputs['os_type'])
        time.sleep(300)
        fsinstallhelper.silent_install_machine(installinputs)
        time.sleep(180)

        installinputs["commcell"].clients.refresh()
        try:
            servername = installinputs["commcell"].clients.get(
                installinputs["remote_clientname"]).client_name
        except Exception:
            servername = installinputs["commcell"].clients.get(
                installinputs["commcell_client_name"]).client_name

        if "windows" in installinputs['os_type'].lower():
            self._admin_console.select_radio(id="windows")
        else:
            self._admin_console.select_radio(id="unix")
        
        self.__refresh_server_list('serverConfigurationForm', index=1)
        time.sleep(60)

        self.__rdropdown.select_drop_down_values(drop_down_id="serverName", values=[servername])

        self.__wizard.click_next()

    @PageService()
    def select_backup_gatway(self, gatewayname):
        """
        select gateway node and click next button
            Args:
                gatewayname (str)    :    gateway name
        """
        gateways = [gatewayname]
        self.__wizard.click_refresh_icon()
        self.__wizard.select_drop_down_values(
            id='accessNodeDropdown', values=gateways)

        self.__wizard.click_next()

    def interactive_install_machine(self, installinputs):
        """interactive install and register new machines
            Args:
                installinputs {}:          install inputs dict
        """
        install_helper = InstallCustomPackage(
            installinputs.get('commcell'),
            installinputs,
            installinputs.get('os_type'))
        install_helper.install_custom_package(
            full_package_path=installinputs.get('full_package_path'),
            username=installinputs.get('registering_user'),
            password=installinputs.get('registering_user_password')
        )

    @PageService()
    def push_add_new_server(self, installinputs):
        """
        push install and configure new server, once done, click Next button
            Args:
                installinputs (dict)    :    Inputs for Installation
        """
        self._admin_console.fill_form_by_id("serverName", installinputs["MachineFQDN"])
        self._driver.find_element(By.ID, 'serverName').send_keys(Keys.DOWN)
        self._driver.find_element(By.ID, 'serverName').send_keys(Keys.ENTER)
        self._admin_console.fill_form_by_id("hostName", installinputs["MachineFQDN"])
        self._admin_console.fill_form_by_id("userName", installinputs["MachineUserName"])
        self._admin_console.fill_form_by_id("password", installinputs["MachinePassword"])
        self._admin_console.fill_form_by_id("confirmPassword", installinputs["MachinePassword"])
        self._admin_console.select_radio(installinputs["OS_TYPE"].lower())
        #take value from backened instead from frontend 
        #THIS WILL BE IMPLEMENTED IN UPCOMING FORMS
        # if installinputs.get("UseNonStandardSSH",None):
        #     #TODO
        #     self._admin_console.fill_form_by_id("sshPortNumber", installinputs["sshPortNumber"])

        # if installinputs.get("InstallationLocation",None):
        #         self._admin_console.fill_form_by_id("installLocation", installinputs["InstallationLocation"])

        # if installinputs.get("Reboot",None):
        #     #TODO 
        #     # Checkbox tick  
        #     pass   
        self._admin_console.click_button(value='Next')

    def check_if_localstorage_exist(self, localstoragename):
        """
        check if local storage name exist
            Args:
                localstoragename    (str)    :    local disk storage name
        """
        existingstorages = self.__rdropdown.get_values_of_drop_down(
            'metallicLocalStorageDropdown')
        if len(existingstorages):
            if localstoragename in existingstorages:
                return True
        else:
            return False

    @PageService()
    def select_local_storage(
            self,
            localstoragename=None,
            gatewayname=None,
            diskpath=None,
            smbusername=None,
            smbpassword=None,
            networkpath=True,
            backup_to_cloud_storage=False
    ):
        """
        configure and select new local storage
            Args:
                localstoragename (str)    :    local storage name
                gatewayname (str)         :    gateway machine name
                diskpath (str)            :    local disk library path
                smbusername (str)         :    user name for UNC storage path
                smbpassword (str)         :    password for UNC storage path
                networkpath (bool)        :    disk library path is UNC path or not
        """

        # Sometimes, the storages and plans take a while to load
        self._admin_console.wait_for_completion()

        if backup_to_cloud_storage:
            self.__wizard.enable_toggle("Backup to cloud storage only")
        else:
            storagenames = [localstoragename]
            mediaagents = [gatewayname]

            if not self.check_if_localstorage_exist(localstoragename):
                self.__wizard.click_add_icon()
                self.__dialog.fill_text_in_field(
                    element_id='name', text=localstoragename)
                self._admin_console.select_hyperlink("Add")
                time.sleep(15)
                backup_location_dialog = RModalDialog(
                    admin_console=self._admin_console, title='Add backup location')
                backup_location_dialog.select_dropdown_values(
                    drop_down_id='mediaAgent', values=mediaagents)
                if networkpath:
                    backup_location_dialog.select_radio_by_id(radio_id='networkRadioDisk')
                    backup_location_dialog.fill_text_in_field(
                        element_id='credential.userName-custom-input', text=smbusername)
                    backup_location_dialog.fill_text_in_field(
                        element_id='credential.password-custom-input', text=smbpassword)
                backup_location_dialog.fill_text_in_field(element_id='path', text=diskpath)
                backup_location_dialog.click_button_on_dialog(text='Add')
                time.sleep(30)
                self._admin_console.click_button("Save")
                time.sleep(300)
                try:
                    self._admin_console.click_button("Save")
                    time.sleep(300)
                except BaseException:
                    pass
            self.__wizard.select_drop_down_values(
                id='metallicLocalStorageDropdown', values=storagenames)
        self.__wizard.click_next()

    @PageService()
    def select_cloud_storage(
            self,
            storageaccount=None,
            storageregion=None,
            storageprovider=None,
            storagename=None,
            using_gateway=False,
            use_only_on_premise_storage=False,
            storageclass="S3 Standard",
            authentication="Access and secret keys",
            s3credential=None,
            s3bucket=None,
            s3accesskey=None,
            s3secretkey=None,
            partialselection=False
    ):
        """
        configure and select new cloud storage
            Args:
                storageaccount (str)        :    storage account name
                storageregion (str)         :    storage region
                storageprovider (str)       :    storage provider name
                storagename (str)           :    cloud storage name
                use_only_on_premise_storage (bool) : Whether only backup to local is required
                partialselection  (bool) : select the storage whose name contains the provided storagename if true

        """

        # Sometimes, the storages and plans take a while to load
        self._admin_console.wait_for_completion()

        if not use_only_on_premise_storage:
            time.sleep(60)

            existingstorages = self.__rdropdown.get_values_of_drop_down(drop_down_id="metallicCloudStorageDropdown")
            if (len(existingstorages) != 0 and storagename in existingstorages):
                self.__wizard.select_drop_down_values(
                    id='metallicCloudStorageDropdown', values=[storagename])
            else:
                self.__wizard.click_add_icon()
                time.sleep(120)
                cloud_storage_dialog = RModalDialog(admin_console=self._admin_console, title='Add cloud storage')
                cloud_storage_dialog.select_dropdown_values(
                    drop_down_id='cloudType', values=[storageaccount])
                if storageaccount == "Air Gap Protect":
                    cloud_storage_dialog.select_dropdown_values(
                        drop_down_id='offering', values=[storageprovider])
                    if using_gateway:
                        storageclass = self.__rdropdown.get_values_of_drop_down('storageClass')[
                            0]
                        self.__wizard.select_drop_down_values(
                            id='storageClass', values=[storageclass])
                    try:
                        self._admin_console.click_button("Start trial")
                        self._get_last_element("Close").click()
                        self.__wizard.click_button("Close")
                    except BaseException:
                        pass
                    time.sleep(300)
                    self._admin_console.scroll_into_view("region")
                    cloud_storage_dialog.select_dropdown_values(
                        drop_down_id='region', values=[storageregion])
                elif storageaccount == "Amazon S3":
                    cloud_storage_dialog.fill_text_in_field(element_id='cloudStorageName', text=storagename)
                    cloud_storage_dialog.select_dropdown_values(drop_down_id="storageClass", values=[storageclass])
                    cloud_storage_dialog.select_dropdown_values(drop_down_id="authentication", values=[authentication])
                    cloud_storage_dialog.fill_text_in_field(element_id='mountPath', text=s3bucket)
                    #support "IAM role" authentication or "access and secret keys"
                    if authentication == "Access and secret keys":
                        savedcreds = self.__rdropdown.get_values_of_drop_down(drop_down_id='savedCredential')
                        if (len(savedcreds) != 0 and s3credential in savedcreds):
                            cloud_storage_dialog.select_dropdown_values(drop_down_id='savedCredential',
                                                                        values=[s3credential])
                        else:
                            add_credential_dialog = RModalDialog(
                                admin_console=self._admin_console,
                                title=self._admin_console.props['label.addCredential'])
                            self._admin_console.click_by_xpath(
                                "//div[@aria-label= 'Create new' or @aria-label='Add']/button")
                            self._admin_console.scroll_into_view("secretAccessKey")
                            add_credential_dialog.fill_input_by_xpath(text=s3credential, element_id='name')
                            add_credential_dialog.fill_input_by_xpath(text=s3accesskey, element_id='accessKeyId')
                            add_credential_dialog.fill_input_by_xpath(text=s3secretkey, element_id='secretAccessKey')
                            add_credential_dialog.click_button_on_dialog(text='Save')
                            time.sleep(200)
                    #re-enter the storage name
                    cloud_storage_dialog.fill_text_in_field(element_id='cloudStorageName', text=storagename)
                cloud_storage_dialog.click_button_on_dialog(text="Save")
                time.sleep(300)
                try:
                    self._admin_console.click_button("Save")
                    time.sleep(300)
                except BaseException:
                    pass
                self.__wizard.select_drop_down_values(
                    id='metallicCloudStorageDropdown', values=[storagename], partial_selection=partialselection)
        else:
            self._driver.find_element(By.ID, "onlLocalBackupEnabledToggle").click()

        self.__wizard.click_next()

    @PageService()
    def select_plan(self, planname, retention=None):
        """configure and select new server plan
            Args:
                planname (string): new plan name

                retention (dict) : Dict containing retention and backup frequency
                    Eg,    retention = {'pri_ret_period': None,
                                     'pri_ret_unit': None,
                                     'sec_ret_period': None,
                                     'sec_ret_unit': None,
                                     'backup_frequency': None,
                                     'backup_frequency_unit': None}
        """
        # Sometimes, the storages and plans take a while to load
        self._admin_console.wait_for_completion()

        if retention:
            self.add_new_plan(planname, retention)
        else:
            self.__wizard.fill_text_in_field(
                id="searchPlanName", text=planname)
            if not self.__is_plan_selected(planname):
                self.__wizard.select_plan(planname)
        self.__wizard.click_next()

    def add_new_plan(self, plan_name, retention=None):
        """Add a new plan
            Args:
                planname (str)      :   plan name
                retention_rpo (dict) : Dict containing retention and backup frequency
                Eg,    retention = {'pri_ret_period': None,
                                 'pri_ret_unit': None,
                                 'sec_ret_period': None,
                                 'sec_ret_unit': None,
                                 'backup_frequency': None,
                                 'backup_frequency_unit': None}
        """
        self.__wizard.click_add_icon()
        self.__dialog.fill_text_in_field(
            element_id="planNameInputFld", text=plan_name)
        if retention:
            self.__dialog.enable_toggle(toggle_element_id='custom')
            if len(retention['pri_ret_period'].strip()):
                self.__dialog.fill_text_in_field(
                    element_id='retentionPeriod',
                    text=retention['pri_ret_period'])
                self.__dialog.select_dropdown_values(
                    drop_down_id='retentionPeriodUnit', values=[
                        retention['pri_ret_unit']])
            if len(retention['sec_ret_period'].strip()):
                self.__dialog.fill_text_in_field(
                    element_id='secondaryRetentionPeriod',
                    text=retention['sec_ret_period'])
                self.__dialog.select_dropdown_values(
                    drop_down_id='secondaryRetentionPeriodUnit', values=[
                        retention['sec_ret_unit']])
            if len(retention['backup_frequency'].strip()):
                self.__dialog.fill_text_in_field(
                    element_id='backupFrequency',
                    text=retention['backup_frequency'])
                self.__dialog.select_dropdown_values(
                    drop_down_id='backupFrequencyUnit', values=[
                        retention['backup_frequency_unit']])
        #retype plan name
        self.__dialog.fill_text_in_field(
            element_id="planNameInputFld", text=plan_name)

        self._admin_console.click_button_using_text("Done")
        self._admin_console.wait_for_completion(wait_time=600)
        time.sleep(360)

    @PageService()
    def set_backup_content_filters(
            self,
            contentpaths,
            contentfilters,
            contentexceptions,
            disablesystemstate=False,
            impersonate_user=None,
            is_nas_subclient=False,
            saved_credentials=None):
        """configure backup content, filters and exceptions when adding new servers
            Args:
                contentpaths   (list)    :    content paths
                filters        (list)    :    list of filters
                exceptions     (list)    :    list of exceptions
                impersonate_user (dict)  :    dict containing username and password for content impersonation
                disablesystemstate  (bool)     :    need disable system state or not
                is_nas_subclient   (bool) :    True to create a NAS subclient. Defaults to False
                saved_credentials (str)  :   saved credential for content impersonation
        """
        next_button_xpath = "//button[contains(.,'Next')]"
        self.__wizard.click_add_icon(index=0)
        self._admin_console.click_button(value='Custom path')

        for contentpath_index in range(len(contentpaths)):
            self.__add_custom_path(contentpaths[contentpath_index])
            if impersonate_user and contentpath_index == 0:
                self._admin_console.wait_for_completion()
                self.__dialog.deselect_checkbox(checkbox_id="toggleFetchCredentials")
                self.__dialog.fill_text_in_field("userName", impersonate_user["username"])
                self.__dialog.fill_text_in_field("password", impersonate_user["password"])
                self.__dialog.click_submit()
            elif saved_credentials and contentpath_index == 0:
                self._admin_console.wait_for_completion()
                self.__rdropdown.select_drop_down_values(drop_down_id='credentials', values=[saved_credentials])
                self.__dialog.click_submit()

        if len(contentfilters):
            self._admin_console.scroll_into_view(next_button_xpath)

            self.__wizard.click_add_icon(index=1)
            self._admin_console.click_button(value='Custom path')
            for contentfilter in contentfilters:
                self.__add_custom_path(contentfilter)

            try:
                self.__wizard.select_drop_down_values(
                    id='globalFilters', values=["Off"])
            except:
                # When FSGuardRails key is enabled, then we dont show the global filter dropdown
                pass
        if len(contentexceptions):
            self._admin_console.scroll_into_view(next_button_xpath)
            self.__wizard.enable_toggle('Define exceptions')
            self.__wizard.click_add_icon(index=2)
            self._admin_console.click_button(value='Custom path')
            for contentexception in contentexceptions:
                self.__add_custom_path(contentexception)
        if disablesystemstate:
            self._admin_console.scroll_into_view(next_button_xpath)
            self.__wizard.select_radio_button(id='backup-system-state')

        if not is_nas_subclient:
            self.__wizard.click_next()

    @PageService()
    def check_file_server_summary_info(self):
        """check the label list from summary page, return true if no empty labels"""
        rpanelinfo = RPanelInfo(self._admin_console)
        paneldetails = rpanelinfo.get_details()
        for k, v in paneldetails.items():
            if v.strip() == "" or k.strip() == "":
                return False
        return True

    @PageService()
    def get_push_install_jobid(self):
        """get push install job id from summary page href link"""
        jobid = self._admin_console.driver.find_element(
            By.XPATH, "//a[text()='View the progress of the submitted job']").get_attribute('href').split('/')[-1]
        return jobid
    
    @PageService()
    def open_push_install_job_and_wait_for_completion(self, timeout=30):
        """
        Opens the link having text 'View the progress of the submitted job' and waits for job completion.
        Upon clicking the link, the job details is opened in the new tab.
        Once the job is completed, the job details tab will be closed and clicks on 'Finish' in the Add Wizard

        Args:
            timeout (int): Timeout in minutes for the install job to complete

        Raises Exception if the install job is not completed successfully
        """

        original_handle = self._admin_console.driver.current_window_handle
        self._admin_console.select_hyperlink("View the progress of the submitted job")

        time.sleep(10)

        self._admin_console.wait_for_completion()

        for handle in self._admin_console.driver.window_handles:
            if handle != original_handle:
                self._admin_console.driver.switch_to.window(handle)

        from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
        job_details = JobDetails(self._admin_console)

        job_details.job_completion(timeout)

        job_status = job_details.get_status().lower()

        if job_status != "completed":
            raise Exception(f"Install job has {job_status}")

        self._admin_console.driver.close()

        self._admin_console.driver.switch_to.window(original_handle)

        self._admin_console.click_button("Finish")
