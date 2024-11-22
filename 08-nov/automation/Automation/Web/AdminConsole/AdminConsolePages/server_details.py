# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the functions or operations that can be performed on the
a selected client on the AdminConsole

Class:

    ServerDetails()

Functions:

jobs()                       -- opens the jobs page of the server

open_agent()                 -- Opens the given type agent of the server

client_info()                -- displays the client information

action_restore_history()     -- Display the restore jobs

oracle_instance()            -- Add an instance for oracle agents

action_add_oracle_instance() -- Adds an oracle instance

action_add_hana_instance()   -- Adds a new SAP HANA instance


"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.panel import DropDown, ModalPanel, PanelInfo, RPanelInfo
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import PageService, WebAction


class ServerDetails:
    """
    This class provides the functions or operations that can be performed on the
    a selected client on the AdminConsole
    """

    def __init__(self, admin_console):
        """
        Init method to create objects of classes used in the file.

        Args:
            admin_console  (Object) : Admin console class object
        """
        self._admin_console = admin_console
        self._driver = self._admin_console.driver
        self.__table = Table(self._admin_console)
        self._drop_down = DropDown(self._admin_console)
        self._panel = ModalPanel(self._admin_console)
        self._panel_info = PanelInfo(self._admin_console, title='Cluster group')
        self._sla_panel = RPanelInfo(self._admin_console, title='SLA')
        self.log = self._admin_console.log

    @PageService()
    def jobs(self):
        """
        Opens the jobs page of the client.

        Returns:
            None

        Raises:
            Exception:
                 There is no link to open Jobs

        """
        self._admin_console.select_hyperlink("Jobs")

    @PageService()
    def open_agent(self, agent_type):
        """

        Args:
            agent_type (str): agent we want to open of the client

        Returns:
            None

        Raises:
            Exception:
                There is no agent with given name.
        """
        self.__table.access_link(agent_type)

    @WebAction()
    def client_info(self):
        """
        Gets the client information

        Returns:
            None

        Raises:
            Exception:
                None

        """
        client_info = {}
        items = self._driver.find_elements(By.XPATH, "//div[1]/cv-tile-component[@data-ac-id"
                                                   " = 'clientDetails-heading_clientGeneral-"
                                                   "clients']/div/div[3]/div/div[2]/ul/li")
        total = len(items)
        for index in range(1, total + 1):
            key = self._driver.find_element(By.XPATH, "//div[1]/cv-tile-component[@data-ac-id = "
                                                    "'clientDetails-heading_clientGeneral-clients'"
                                                    "]/div/div[3]/div/div[2]/ul/"
                                                    "li["+ str(index) + "]/span[1]").text
            val = self._driver.find_element(By.XPATH, "//div[1]/cv-tile-component[@data-ac-id"
                                                    " = 'clientDetails-heading_clientGeneral-"
                                                    "clients']/div/div[3]/div/div[2]/ul/"
                                                    "li["+ str(index) + "]/span[2]").text
            client_info[key] = val
        self.log.info(client_info)

    @PageService()
    def action_restore_history(self, server):
        """
        Opens the restore history.
        Args:
            server (str): Attribute we want to open restore history of

        Returns:
            Null

        Raises
            Exception:
                Restore History option not present

        """
        self.__table.access_action_item(server, "Restore history")

    @PageService()
    def _click_edit_cluster_group(self):
        """ Clicks on edit in cluster group tile """
        self._panel_info.edit_tile()

    @WebAction()
    def edit_job_directory(self, job_dir):
        """ Edits the job directory of cluster client """
        self._driver.find_element(By.ID, 'jobResultsDirectory').clear()
        self._admin_console.fill_form_by_id('jobResultsDirectory', job_dir)

    @PageService()
    def edit_nodes(self, nodes, add=None, delete=None):
        """ Edits the list of cluster client Nodes """
        if add:
            self._drop_down.select_drop_down_values(drop_down_id='nodes', values=nodes)
        if delete:
            self._drop_down.deselect_drop_down_values(1, values=nodes)

    @PageService()
    def edit_agents(self, agents):
        """ Edits the list of Agents in Cluster client details page """
        self._drop_down.select_drop_down_values(1, agents)

    @WebAction()
    def _enable_toggle(self):
        """
            Enable toggle in the panel
            This toggle is not apart of toggle control so couldn't use enable_toggle
            method from AdminConsoleBase or panelInfo class
        """
        self._driver.find_element(By.XPATH, '//*[@toggle-name="foreceSync"]/div').click()

    @PageService()
    def edit_cluster_group(self, nodes=None, agents=None, job_dir=None, force_sync=False, add=None, delete=None):
        """
        Edit cluster groups
        Args:
        Job_dir (str) : Job resultant directory
        nodes  (List) : List of nodes/clients
        agents (List) : List of agents
        """
        self._click_edit_cluster_group()
        if job_dir:
            self.edit_job_directory(job_dir)
        if nodes:
            self.edit_nodes(nodes, add=add, delete=delete)
        if agents:
            self.edit_agents(agents)
        if force_sync:
            self._enable_toggle()
        self._panel.submit()

    @PageService()
    def deconfigure_cluster_client(self, nodes):
        """ Deconfigures a cluster client """
        self._click_edit_cluster_group()
        self.edit_nodes(nodes, add=False, delete=True)
        self._panel.submit()

    @PageService()
    def enable_sla_toggle(self):
        """ enable the sla toggle from server configuration page"""
        self._admin_console.select_configuration_tab()
        self._admin_console.access_tile(id='tile-action-btn')
        self._sla_panel.enable_toggle("Exclude from SLA")


