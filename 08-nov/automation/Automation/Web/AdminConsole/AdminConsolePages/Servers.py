# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on
a servers of the all agents on the AdminConsole

Class:

    Servers()

Functions:

    select_client()                 -- select and open a client

    server_backup()                 -- Backup the given server

    action_jobs()                   -- opens the jobs page of the client

    select_client()                 -- select and open a client

    action_job()                    -- opens the job page of the given client

    action_add_software()           -- displays support for adding software for the client

    action_update_software()        -- displays support for updating software for the client

    action_release_licence()        -- opens the release license page of the given client

    reload_data()                   -- reloads the table data

    retire_server()                 -- performs retire action for the given server

    delete_server()                 -- performs delete action for the given server

    action_check_readiness()        -- performs check readiness on client

    action_send_logs()              -- opens the los page of client

    add_server_new_windows_or_unix_server()       -- To create a new Windows/UNIX Server

    add_server_existing_windows_or_unix_server()  -- To add packages in existing Windows/UNIX Server

    add_server_ibmi_server()        -- To create new IBMi Server

    add_server_openvms_server()     -- To create new OpenVMS Server

    add_ma_role()                   -- To Add MA role to the server

    OpeniDA()                       -- opens the iDA associated with the client
    
    action_view_network_summary()   -- opens the network summary page of the client and return the summary
    
    action_push_network_configuration() -- Performs push network configuration on the client

"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.AdminConsolePages.view_logs import ViewLogsPanel
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Table, Rtable
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.panel import DropDown
from Web.Common.exceptions import CVWebAutomationException


class Servers:

    """
    Class for Server page of adminconsole
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Table(admin_console)
        self.__rtable = Rtable(admin_console)

        self._drop_down = DropDown(self._admin_console)
        self._dialog = ModalDialog(self._admin_console)
        self._rdialog = RModalDialog(self._admin_console)
        self._alert = Alert(self._admin_console)
        self._admin_console.load_properties(self)
        self.driver = self._admin_console.driver

    def filter_client_type(self, client_type: str):
        """Wrapper to filter by client type compatible with old and new SPs"""
        if 1000 > self._admin_console.service_pack >= 37 or self._admin_console.service_pack >= 3700:
            self.__rtable.select_view(client_type)
        else:
            self.__rtable.filter_type(client_type)

    @PageService()
    def select_client(self, client_name):
        """
        Navigates to the client page

        Args:
            client_name (str): name of the client we need to select

        Returns:
            None

        Raises:
            Exception:
                There is no server with given name

        """
        self.__table.access_link(client_name)

    '''
    deprecated method

    @WebAction()
    def server_backup(self, server_name, agent_name, subclient_name, backup_level):
        """
        Backup the given server

        Args:
            server_name     (str): Server name to backed up

            agent_name      (str): Agent type of server

            subclient_name  (str): subclient to be backed up

            backup_level  (BackupType) : type of backup, among the type in Backup.BackupType enum

        Returns:
            None

        Raises:
            Exception:
                Correct type of backup not selected
        """
        col_no = self.table_column_no('Backup')
        self.__table.search_for(server_name)
        if self._admin_console.check_if_entity_exists("link", server_name):
            self._admin_console.driver.find_element(By.XPATH, "//a[text()='" + server_name + "']/../../../div["
                                              + str(col_no) + "]/span/a").click()
            self._admin_console.wait_for_completion()
            self._admin_console.check_error_message()
            elements = self.driver.find_elements(By.XPATH, "//label[contains(text(),'"
                                                          + agent_name + "')]/../../div/ul/li")
            for elem in elements:
                if elem.find_element(By.XPATH, "./div/span[3]/label[contains(text(),'"
                                              + subclient_name + "')]"):
                    elem.find_element(By.XPATH, "./div/span[2]//input").click()
                    break
            self._admin_console.submit_form()
            backup = Backup(self)
            return backup.submit_backup(backup_level)
    '''

    @PageService()
    def add_gateway(self, client_name, host_name):
        """
        Adds gateway settings on the existing clients

        Args:
            client_name (str): he server on which gateway needs to be added

            host_name (str): the host name of the server

        Returns:
            None

        Raises:
            Exception:
                There is no option to add gateway
        """
        self._admin_console.select_hyperlink("Add gateway")
        self._admin_console.fill_form_by_id("clientName", client_name)
        self._admin_console.fill_form_by_id("hostName", host_name)
        self._admin_console.submit_form()

    @PageService()
    def action_jobs(self, client_name):
        """Displays the jobs running on the given client

        Args:
            client_name     (str) -- client name for displaying its job manager

        Returns:
            None

        Raises:
            Exception

                if client_name is invalid

                if there is no jobs option for the client

        """
        self.__table.access_action_item(client_name, 'Jobs')

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
                                            default: False

            packages        (list)      -- list of packages to be installed

            reboot          (bool)      -- set to True if reboot required
                                            default: False

        Returns:
            (str)    --   the job id for the submitted request

        Raises:
            Exception

                if given input is invalid

                if there is no add software option for the client

        """
        self.__table.access_action_item(client_name, 'Add software')
        if select_all_packages:
            self._drop_down.select_drop_down_values(drop_down_id='agents', select_all=True)
        elif packages:
            self._drop_down.select_drop_down_values(drop_down_id='agents', values=packages)
        else:
            raise CVWebAutomationException('Packages list is not provided')
        if reboot:
            self.driver.find_element(By.XPATH, "//span[contains(text(), 'Reboot if required')]").click()
        self._admin_console.submit_form()

        if self._admin_console.check_if_entity_exists(
                "xpath",
                '//div[@data-ng-controller="pushInstallController"]//a[contains(@href,"jobs")]'):

            # To get the job id
            jobid = self.driver.find_element(By.XPATH, 
                '//div[@data-ng-controller="pushInstallController"]//a[contains(@href,"jobs")]'
            ).text

        else:
            raise CVWebAutomationException("Job not started, please check the logs")

        # To click OK button
        self._admin_console.click_button("OK")

        # return the job id
        return jobid

    @WebAction()
    def action_update_software(self, client_name=None, reboot=False):
        """selects the update software option for the given client

        Args:
            client_name     (str) -- client to update software on

            reboot      (bool)    -- set to True if reboot required
                                        default: False

        Returns:
            (str)    --   the job id for the submitted request

        Raises:
            Exception

                if given input is invalid

                if there is no update software option for the client

        """
        self.filter_client_type(self._admin_console.props['viewname.all'])
        self.__rtable.access_action_item(client_name, 'Upgrade software')
        upgrade_server_modal = RModalDialog(admin_console=self._admin_console, title='Confirm software upgrade')

        if reboot:
            upgrade_server_modal.checkbox.check(id='rebootClient')

        upgrade_server_modal.click_submit(wait=False)

        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def action_release_license(self, client_name):
        """Displays the release license for the given client

        Args:
            client_name     (str) -- client name to display the release license

        Returns:
            None

        Raises:
            Exception

                if client_name is invalid

                if there is no release license option for the client

        """
        self.__table.access_action_item(client_name, 'Release license')

    @PageService()
    def reload_data(self):
        """
        Reloads the table data

        Returns:
            None
        """
        self.__rtable.reload_data()

    @PageService()
    def retire_server(self, server_name, select_from_all_server=False, wait = True):
        """Performs retire action for the given server

        Sometimes for example when their is a MA with storage, we can't directly retire
        At that time it throws an error message we return that as an exception and close the error dialog

        Args:
            server_name                 (str) -- server name to retire

            select_from_all_server      (bool) -- Boolean value to specify if All servers needs to be listed, default: False

            wait                        (bool) -- Boolean value to specify if we need to wait for completion
                                                  of retire button click before trying to get job id from popup, default: True

        Raises:
            CVWebAutomationException

                if the server can't be retired due to some reason

                if none of the expected dialog found
        """
        if select_from_all_server:
            self.filter_client_type(self._admin_console.props['viewname.all'])
        else:
            self.filter_client_type(self._admin_console.props['viewname.Infrastructure'])
        self.__rtable.access_action_item(server_name, self._admin_console.props['action.commonAction.retire'])

        title = f"Retire {server_name}"
        r_modal_dialog = RModalDialog(self._admin_console,title=title)

        if r_modal_dialog.check_if_button_exists('Retire'):
            self._rdialog.fill_text_in_field(element_id='confirmText', text='RETIRE')
            self._rdialog.click_submit(wait)
            return self._alert.get_jobid_from_popup()
        elif self._admin_console.check_if_entity_exists("xpath", "//*[contains(text(),'Cannot retire')]"):
                ele = self.driver.find_element(By.XPATH, "//*[contains(text(),'Cannot retire')]")
                error_msg = ele.text
                self._admin_console.click_button_using_text(self._admin_console.props['label.close'])
                raise CVWebAutomationException(error_msg)
        else:
            raise CVWebAutomationException("No Expected Dialog Found")

    @PageService()
    def delete_server(self, server_name, select_from_all_server=False):
        """Performs delete action for the given server

        Args:
                server_name     (str) -- server name to delete
                select_from_all_server      (bool) -- Boolean value to specify if
                All servers needs to be listed

                        default: False
        """
        if select_from_all_server:
            self.filter_client_type(self._admin_console.props['viewname.all'])
        else:
            self.filter_client_type(self._admin_console.props['viewname.Infrastructure'])
        self.__rtable.access_action_item(server_name, self._admin_console.props['label.globalActions.delete'])
        self._admin_console.fill_form_by_id("confirmText", "DELETE")
        self._admin_console.click_button("Delete")
        self._admin_console.wait_for_completion()
        self._admin_console.check_error_message()

    @PageService()
    def action_check_readiness(self, client_name):
        """performs check readiness for the given client

        Args:
            client_name     (str) -- client to perform check readiness on

        Returns:
            None

        Raises:
            Exception

                if client_name is invalid

                if there is no uninstall software option for the client

        """
        self.__table.access_action_item(client_name, 'Check readiness')

    @PageService()
    def action_view_network_summary(self, server_name):
        """selects the view network summary option for the given client

        Args:
            server_name     (str) -- client to view network summary

        Returns:
            returns text from clipboard.

        Raises:
            Exception

                if server_name is invalid

                if there is no view network summary option for the client

        """
        self.__rtable.access_action_item(server_name, self._admin_console.props['action.commonAction.viewNetworkConf'])
        clipboard_content = self._rdialog.copy_content_of_file_from_dialog(element_id="viewSummary")
        self._rdialog.click_close()
        return clipboard_content

    @PageService()
    def action_push_network_configuration(self, server_name):
        """selects the push network configuration option for the given client

        Args:
            server_name     (str) -- client to push network configuration

        Returns:
            None

        Raises:
            Exception

                if server_name is invalid

                if there is no push network configuration option for the client

        """
        self.__rtable.access_action_item(server_name, self._admin_console.props['action.commonAction.pushNetworkConf'])
        self._rdialog.click_submit()
        self._admin_console.check_error_message()

    @PageService()
    def action_send_logs(self, client_name):
        """selects the send logs option for the given client

        Args:
            client_name     (str) -- client logs to be send

        Returns:
            None

        Raises:
            Exception

                if client_name is invalid

                if there is no send logs option for the client

        """
        self.__table.access_action_item(client_name, 'Send logs')

    @PageService(hide_args=True)
    def add_server_new_windows_or_unix_server(
            self,
            hostname=None,
            username=None,
            password=None,
            os_type='windows',
            packages=None,
            select_all_packages=False,
            plan=None,
            unix_group=None,
            reboot=False,
            install_path=None,
            remote_cache=None):
        """To create a new server

        Args:

            hostname   (list)  -- list of servers to install packages on

            username    (str)   -- username of the server machine

            password    (str)   -- password of the server machine

            os_type     (str)   -- os type of the server machine
                                    default: windows

            packages    (list)  -- packages to be installed on the machine

            select_all_packages (bool) -- set to True to install all the packages
                                            default: False

            plan        (str)   -- plan to run install

            unix_group  (str)   -- unix group for UNIX machine

            reboot      (bool)  -- set to True to reboot if required
                                    default: False

            install_path (str)  -- Installing client on specified path ( Optional )

            remote_cache (str)  -- Client name of remote cache machine ( Optional )

        Returns:
            (str)    --   the job id for the submitted request

        Raises:
            Exception

                if given inputs are not valid

                if there is no add server option
        """
        self.__rtable.access_toolbar_menu(self._admin_console.props['label.installSoftware'])
        add_server_modal = RModalDialog(admin_console=self._admin_console, title='Add server')
        hostname = [f"{name.strip()}\n" for name in hostname]
        for each in hostname:
            add_server_modal.fill_text_in_field("hostname", each)
        add_server_modal.disable_toggle('savedCredentials')
        add_server_modal.fill_text_in_field("username", username)
        add_server_modal.fill_text_in_field("password", password)
        add_server_modal.fill_text_in_field("confirm_password", password)

        if 'windows' in os_type.lower():
            add_server_modal.select_radio_by_id('windows')
        else:
            add_server_modal.select_radio_by_id('unix')
            if unix_group:
                self._admin_console.fill_form_by_id("unixGroup", unix_group)

        if remote_cache:
            add_server_modal.select_dropdown_values(drop_down_id='remoteCacheClientDropdown', values=[remote_cache])

        if select_all_packages:
            add_server_modal.select_dropdown_values(drop_down_id='packageDropdown', values=None, select_all=True)
        # To install selected packages
        elif packages:
            add_server_modal.select_dropdown_values(drop_down_id='packageDropdown', values=packages)
        else:
            raise CVWebAutomationException('Packages list is not provided')

        if plan:
            add_server_modal.select_dropdown_values(drop_down_id='planListDropdown_nogroupsInput', values=[plan])

        # To reboot client if required
        if reboot:
            add_server_modal.enable_toggle('reboot')

        if install_path and self._admin_console.check_if_entity_exists("id", "installation_location"):
            add_server_modal.fill_text_in_field("installation_location", install_path)

        add_server_modal.click_submit()
        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def add_server_existing_windows_or_unix_server(self):
        """To create a new server

        Args:

        Returns:
            None
        """
        self._admin_console.select_hyperlink("Add server")
        self._admin_console.select_hyperlink("Add Windows/UNIX file server")

    @PageService()
    def add_server_ibmi_server(self):
        """To create a new server
        """
        self._admin_console.select_hyperlink("Add Server")
        self._admin_console.select_hyperlink("Add IBM i server")

    @PageService()
    def add_server_openvms_server(self):
        """To create a new server
        """
        self._admin_console.select_hyperlink("Add Server")
        self._admin_console.select_hyperlink("Add OpenVMS server")

    @PageService()
    def add_ma_role(self,server_name):
        """
        To Add MA role to the server
        
        Args:
            server_name (str)             --  Name of the server to which MA role needs to be added
        """
        
        self.filter_client_type(self._admin_console.props['viewname.all'])
        self.__rtable.access_action_item(server_name, self._admin_console.props['action.addMARole'])
        self._admin_console.check_error_message()    

    @WebAction()
    def open_agent(self, agent_name, server_name):
        """
        Directly opens the given agent of the client.

        Args:
            agent_name    (str):  name of the agent we need to select

            server_name   (str): name of the server we need to select

        Returns:
            None

        Raises:
            Exception:
                There is no server with the name

        """
        self.__table.search_for(server_name)
        if self._admin_console.check_if_entity_exists("link", server_name):
            if self._admin_console.check_if_entity_exists(
                    "xpath",
                    "//a[text()='" +
                    server_name +
                    "']/../../../div[2]//a[text()='" +
                    agent_name +
                    "']"):
                self.driver.find_element(By.XPATH, 
                    "//a[text()='" +
                    server_name +
                    "']/../../../div[2]//a[text()='" +
                    agent_name +
                    "']").click()
                self._admin_console.wait_for_completion()
            else:
                raise Exception("There is no iDA {0} for client {1}".format(
                    agent_name, server_name))
        else:
            raise Exception("There is no client with the name {0}".format(server_name))

    @WebAction()
    def sap_hana_client(
            self,
            client_name,
            instance_name,
            instance_number,
            os_user,
            server,
            sql_location,
            users,
            data_storage_policy,
            log_storage_policy,
            command_storage_policy,
            store_key=None,
            db_user=None,
            db_password=None):
        """
            Adds a SAP HANA client
            :param client_name:
            :param instance_name:
            :param instance_number:
            :param os_user:
            :param server:
            :param sql_location:
            :param users:
            :param data_storage_policy:
            :param log_storage_policy:
            :param command_storage_policy:
            :param store_key:
            :param db_user:
            :param db_password:
        """
        self._admin_console.log.info("Adding a SAP HANA client")
        self.driver.find_element(By.NAME, "hostName").send_keys(client_name)
        self.driver.find_element(By.NAME, "databaseName").send_keys(instance_name)
        self.driver.find_element(By.NAME, "databaseNumber").send_keys(instance_number)
        self.driver.find_element(By.NAME, "osUsername").send_keys(os_user)
        self._admin_console.select_value_from_dropdown("primaryHanaServer", server)
        self.driver.find_element(By.NAME, "hdbSqlLocation").clear()
        self.driver.find_element(By.NAME, "hdbSqlLocation").send_keys(sql_location)
        if store_key is not None:
            self.driver.find_element(By.XPATH, 
                "//form/cv-tabset-component/div/div[1]/div/label[7]/div/input[1]").click()
            self.driver.find_element(By.NAME, "hdbStorekey").send_keys(store_key)
        else:
            self.driver.find_element(By.NAME, "dbUsername").send_keys(db_user)
            self.driver.find_element(By.NAME, "dbPassword").send_keys(db_password)
        self.driver.find_element(By.LINK_TEXT, "Details").click()
        if users is not None:
            for user in users:
                self._admin_console.select_value_from_dropdown("users", user)
                self.driver.find_element(By.XPATH, 
                    "//button[@class='btn btn-primary add-user-btn cvBusyOnAjax']").click()
        self.driver.find_element(By.LINK_TEXT, "Storage").click()
        self._admin_console.select_value_from_dropdown("dataStoragePolicy", data_storage_policy)
        self._admin_console.select_value_from_dropdown("logStoragePolicy", log_storage_policy)
        self._admin_console.select_value_from_dropdown("commandStoragePolicy", command_storage_policy)

        self.driver.find_element(By.XPATH, "//section/form/div/button[2]").click()
        self._admin_console.wait_for_completion()

    @PageService()
    def add_cluster_client(self, clustername, hostname, os_type, backup_plan, dir, nodes, agents, force_sync=None):
        """
        Adding Cluster Client
        clustername         (str)   : name of the cluster client
        hostname            (str)   : hostname of the cluster client
        os_type             (str)   : Windows / Linux
        backup_plan         (list)  : Plan to set for a client
        dir                 (str)   : Resultant directory
        Nodes               (list)  : List of cluster nodes
        Agents              (list)  : List of common agents present in all the nodes
        force_sync          (bool)  : Enable/Disable Force sync configuration on remote nodes
        :return:
        """
        self._admin_console.select_hyperlink("Add server")
        self._admin_console.access_sub_menu(self._admin_console.props['label.clusterServer'])
        self._admin_console.fill_form_by_id('clusterName', clustername)
        self._admin_console.fill_form_by_id('hostName', hostname)
        if os_type == "Windows":
            self._admin_console.select_radio('osTypeWINDOWS')
        elif os_type == 'Unix and Linux':
            self._admin_console.select_radio('osTypeUNIX')
        self._drop_down.select_drop_down_values(0, backup_plan)
        self._admin_console.fill_form_by_id('jobResultsDirectory', dir)
        self._drop_down.select_drop_down_values(1, nodes)
        self._drop_down.select_drop_down_values(2, agents)
        if force_sync:
            self.driver.enable_toggle(0)

        self._admin_console.submit_form(True, 'addClusterServerForm')
        self._admin_console.check_error_message()
        return True

    @PageService()
    def delete_cluster_client(self, client_name):
        """ Deleting cluster client """
        self.__table.access_action_item(client_name, self._admin_console.props['action.delete'])
        self._dialog.type_text_and_delete('Delete')

    @PageService()
    def reset_filters(self):
        """Method to reset the filters applied on the page"""
        self.__rtable.reset_filters()

    @PageService()
    def get_all_servers(self, server_type=None, company=None):
        """ Returns all the server names present on server page

        Args:
            server_type (string): Server Type for filter
            company (string): Company to filter

        Returns:
            List: List of all the servers matching the given args
        """
        if server_type:
            self.filter_client_type(server_type)

        if company:
            self.__rtable.select_company(company)

        server_names = self.__rtable.get_column_data("Name", fetch_all=True)
        return server_names

    @PageService()
    def is_client_exists(self, server_name, select_from_all_server=False):
        """ check client entry existence from file server page
        Args:
                server_name     (str) -- server name to retire
                select_from_all_server      (bool) -- Boolean value to specify if
                All servers needs to be listed

                        default: False
        returns: boolean
            True: if server exists
            false: if server does not exists
        """
        if select_from_all_server:
            self.filter_client_type(self._admin_console.props['viewname.all'])
        else:
            self.filter_client_type(self._admin_console.props['viewname.Infrastructure'])
        status = self.__rtable.is_entity_present_in_column(column_name='Name',
                                                           entity_name=server_name)
        return status
    
    @PageService()
    def view_logs(self, client_name):
        """ Method to select view logs on specified client

            Args:
                  client_name (str) --- Name of client on which view logs option to check.
            Returns:
                viewlogspanel (object)  --- Returns viewlogs panel object

            Raises:
                Exception:

                    -- if fails to run view logs operation

        """
        self.filter_client_type(self._admin_console.props['viewname.all'])
        self.__rtable.access_action_item(client_name, self._admin_console.props['action.viewLogs'])
        self._admin_console.check_error_message()
        return ViewLogsPanel(self._admin_console)
