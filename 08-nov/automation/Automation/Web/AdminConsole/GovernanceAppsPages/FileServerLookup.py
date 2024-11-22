# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the File Server lookup page
which is opened while adding a Data Source in Sensitive Data Analysis Project Details
page.


Classes:

    FileServerLookup() ---> SensitiveDataAnalysisProjectDetails() --->
    SensitiveDataAnalysis() ---> GovernanceApps() ---> object()


FileServerLookup  --  This class contains all the methods for action in
     File Server lookup page page and is inherited by other classes to
    perform GDPR related actions

    Functions:

    _select_mailboxes() -- Selects the given Mailbox
    __get_advanced_settings_expansion_element() -- Gets Advanced settings bar WebElement
    is_advanced_settings_expanded() -- Checks if Advanced settings is expanded
    expand_advanced_settings() -- Expands the advanced settings bar if collapsed
    collapse_advanced_settings() -- Collapses the advanced settings bar if expanded
    _select_machine_to_analyze()  --  Search for the machine to Analyze
    add_file_server() -- Adds data source file server
    add_one_drive_server() --  Adds data source OneDrive Server
    add_one_drive_v2_server() -- Adds OneDrive V2 Server data source
    add_exchange_server() --  Adds data source Exchange Server
    add_database_server() -- Adds data source database server
    add_gdrive_server() -- Adds data source  gdrive server
    add_fso_server_group_datasource()  -- Adds FSO Server Group Data source
    select_inventory()  --  Select the inventory from the dropdown
    select_identity_server() --  Select the inventory from the dropdown
    create_credentials()     --  Creates a new credentials in the system vault
    saas_select_server_to_analyze() --  Selects a Risk Analysis Exchange/OneDrive Server to Analyze in SaaS
    saas_add_one_drive_ds()         --  Adds OneDrive v2 server data source for SaaS
    saas_add_exchange_ds()          --  Adds Exchange data source for SaaS
    _add_datasource_helper()        --  Adds a SDG type datasource for OneDrive/Exchange Servers

ObjectStorageClient -- This class contains methods for creating/adding an object storage client from the FSO UI

    Functions:

    _create_credential()                    --  Creates credentials from the ModalPanel Cloud App UI from FSO
    create_client()                         --  Created a Cloud App client
    select_client()                         --  Selects a cloud App client if it exists
    add_data_source()                       --  Adds a data source for the cloud app client

"""
import re

import dynamicindex.utils.constants as cs
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.browse import CVAdvancedTree, RContentBrowse
from Web.AdminConsole.Components.core import RfacetPanel, TreeView, Checkbox
from Web.AdminConsole.Components.panel import (RDropDown, RModalPanel,
                                               RPanelInfo)
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.GovernanceAppsPages.SensitiveDataAnalysisProjectDetails import \
    SensitiveDataAnalysisProjectDetails
from Web.Common.page_object import PageService, WebAction


class FileServerLookup(SensitiveDataAnalysisProjectDetails):
    """
     This class contains all the methods for action in File Server Lookup page
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__table = Rtable(self.__admin_console)
        self.__cv_tree = CVAdvancedTree(self.__admin_console)
        self.__dropdown = RDropDown(self.__admin_console)
        self._excludeServerTypeValidationList = [
            self.__admin_console.props['label.datasource.exchange'],
            self.__admin_console.props['label.datasource.sharepoint'],
            self.__admin_console.props['label.serverGroup']
        ]
        self._inv_facet = RfacetPanel(admin_console, 'Inventory')
        self.__treeview = TreeView(self.__admin_console)
        self.__browse = RContentBrowse(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)
        self.__checkbox = Checkbox(self.__admin_console)
        self.__modal_panel = RModalPanel(self.__admin_console)

    @WebAction()
    def _select_mailboxes(self, mailbox):
        """
        Check Selected Mailbox
        Args:
            mailbox (str) - Mailbox to be selected
        """

        self.__admin_console.driver.find_element(By.XPATH,
            f'//div[contains(@class,"cv-kendo-grid")]//div[text()="{mailbox}"]/preceding::td[2]') \
            .click()

    @WebAction()
    def __select_fso_crawl_type(self, crawl_type='Quick'):
        """
        Select FSO crawl type for backed up DS, Full and Quick
        Args:
            crawl_type (str): FSO crawl type (Quick/Full)
        """
        self.__admin_console.driver.find_element(By.XPATH,
            f"//label/span[text()='{crawl_type}']"
        ).click()

    @WebAction()
    def __get_advanced_settings_expansion_element(self):
        """ Gets Advanced settings bar WebElement

        Returns : Advanced settings bar WebElement

        """
        return self.driver.find_element(By.XPATH, "//div[contains(@class,'accordion-header')]")

    @PageService()
    def is_advanced_settings_expanded(self):
        """ Checks if Advanced settings is expanded

        Returns (bool) : True if expanded

        """
        element = self.__get_advanced_settings_expansion_element()
        return 'expanded' in element.get_attribute('class')

    @PageService()
    def expand_advanced_settings(self):
        """ Expands the advanced settings bar if collapsed """
        if not self.is_advanced_settings_expanded():
            element = self.__get_advanced_settings_expansion_element()
            element.click()
            self.__admin_console.wait_for_completion()

    @PageService()
    def collapse_advanced_settings(self):
        """ Collapses the advanced settings bar if expanded """
        if self.is_advanced_settings_expanded():
            element = self.__get_advanced_settings_expansion_element()
            element.click()
            self.__admin_console.wait_for_completion()

    @PageService()
    def saas_select_server_to_analyze(self, server_name):
        """
        Selects a Risk Analysis Exchange/OneDrive Server to Analyze in SaaS
        Args:
            server_name(str)        --  Name of the server to be analyzed
        """
        self.log.info(f"Searching and selecting datasource server with name {server_name}")
        self.__table.select_rows([server_name], search_for=True)
        self.__admin_console.click_button(self.__admin_console.props['label.next'])

    @WebAction()
    def _select_machine_to_analyze(
            self, search_name, search_category, agent_installed=False,
            data_source_type='File system', inventory_name=None, **kwargs):
        """
        Search for the machine to Analyze

            Args:
                search_name (str) - Name to search for
                search_category (str) - Search Category to search for
                Values:
                    "Client name",
                    "Domain Name",
                    "Operating system",
                    "Host name",
                    "Server Group Name",
                    "All"
                agent_installed (Bool) - Verify if Agent Installed
                data_source_type (str) - SDG Data Source Type
                inventory_name  (str)  - name of the inventory to be used

            Available kwargs:
                identity_server (str)  - name of the identity server
                 
            Raise:
                Exception if Machine not found in the search
                Exception if Agent Installed status is shown otherwise than expected
        """
        search_category_dict = {
            "Client name": self.__admin_console.props['label.serverName'],
            "Domain Name": self.__admin_console.props['label.domainName'],
            "Operating system": self.__admin_console.props['label.operatingSystem'],
            "Host name": "Host name",
            "Server Group Name": self.__admin_console.props['label.clientGroupName'],
            "All": self.__admin_console.props['label.all']
        }
        # Inventory selection
        tmp_txt = search_name
        identity_server = kwargs.get("identity_server", None)
        if inventory_name:
            self.log.info(
                f"Selecting inventory other than default - {inventory_name}")
            self.select_inventory(inventory_name)
        if identity_server:
            self.log.info(f"Selecting the identity server {identity_server}")
            self.select_identity_server(identity_server)
        self.log.info("Entering Search Name: %s", search_name)
        if not inventory_name:
         self.__table.search_for(search_name)
        # Default inventory and user inventories have a different file server view
        elif inventory_name:
         self.__admin_console.fill_form_by_xpath("//div[contains(@class,'searchInput')]//input", search_name)
         self.__admin_console.wait_for_completion()
         table_data = self.__table.get_table_data()
         tmp_txt = table_data[search_category_dict[search_category]][0]
         self.log.info("Host Name Obtained is: %s", tmp_txt)
         if re.search(str(search_name), tmp_txt, re.IGNORECASE):
            self.log.info("Found: %s" % search_name)
         else:
            raise Exception("Couldn't find: %s" % search_name)
         if data_source_type.strip() not in self._excludeServerTypeValidationList:
            tmp_txt = table_data['Server type'][0]
            self.log.info("Agent Status Obtained is: %s", tmp_txt)
            if agent_installed:
                if re.search('Agent installed', tmp_txt, re.IGNORECASE) or \
                        re.search('Content indexing enabled', tmp_txt, re.IGNORECASE):
                    self.log.info(
                        "Agent installed or Content Indexing Enabled as expected")
                else:
                    raise Exception("Agent not installed")
            else:
                if re.search('Agent not installed', tmp_txt, re.IGNORECASE):
                    self.log.info("Agent not installed as expected")
                elif re.search('Network share', tmp_txt, re.IGNORECASE):
                    self.log.info("NAS Client exists")
                else:
                    raise Exception("Agent installed")
        self.log.info("Selecting the machine to analyze")
        self.__table.select_rows([tmp_txt])
        self.__admin_console.wait_for_completion()
        self.log.info("Clicking on Next button")
        self.__admin_console.click_button(
            self.__admin_console.props['label.next'])

    @PageService()
    def add_file_server(self, search_name, search_category, display_name, country_name, directory_path=None, **kwargs):
        """
        Adds data source file server

            Args:
                search_name (str) - Name to search for
                search_category (str) - Search Category to search for
                Values:
                    "Client name",
                    "Domain Name",
                    "Operating system",
                    "Host name",
                    "All"
                display_name (str) - Display name for this data source
                country_name (str) - Country name to be selected
                Values:
                    "United Kingdom",
                    "United States"
                directory_path (str) - Directory Path for Entity Extraction

                Available kwargs:

                username (str) - Username to access the Directory Path
                password (str) - Password to access the Directory Path
                agent_installed (Bool) - Verify if Agent Installed or Content indexing enabled
                enable_monitoring (Bool) - Enable the File monitoring toggle
                live_crawl (Bool) - Selects Live Crawl in case of Agent Installed
                backup_data_import (Bool) - Selects import from Backed up data option
                                             in case of Agent Installed
                access_node (str) - Access Node machine to crawl the data in case of
                                             Agent Not Installed
                fso_server (bool): Identifies if files server is added as FSO server
                crawl_type (str): Type of crawl operation to perform
                inventory_name  (str)  : Name of inventory to be used
                identity_server (str)  : Name of the identity server
                credential      (str)   :   Credential name to be used while creating datasource
                create_credential   (bool)  :   Boolean value to create a credential on the go or not
        """

        username = kwargs.get("username", None)
        password = kwargs.get("password", None)
        agent_installed = kwargs.get("agent_installed", False)
        enable_monitoring = kwargs.get("enable_monitoring", False)
        live_crawl = kwargs.get("live_crawl", False)
        backup_data_import = kwargs.get("backup_data_import", False)
        access_node = kwargs.get("access_node", False)
        fso_server = kwargs.get("fso_server", False)
        crawl_type = kwargs.get("crawl_type", 'Quick')
        inventory_name = kwargs.get("inventory_name", None)
        identity_server = kwargs.get("identity_server", None)
        credential = kwargs.get("credential", None)
        create_credential = kwargs.get("create_credential", False)

        self._select_machine_to_analyze(
            search_name=search_name,
            search_category=search_category,
            agent_installed=agent_installed,
            inventory_name=inventory_name,identity_server=identity_server)
        self.__admin_console.fill_form_by_id("datasourceName", display_name)
        # Plan Name required for FSO, not required for SDG
        url = self.__admin_console.current_url()
        if "clienttype=client" in url.lower():
            self.log.info("Selecting The Plan")
            self.__dropdown.select_drop_down_values(values=[GovernanceApps.plan_name],
                                                    drop_down_id="plan")
        if country_name:
            self.__dropdown.select_drop_down_values(values=[country_name], drop_down_id='countryCodeDropdown')
            self.__admin_console.wait_for_completion()
        if not agent_installed:
            self.__admin_console.fill_form_by_id("sourcePath", directory_path)
            if credential is not None:
                if create_credential:
                    self.create_credentials(credential, username, password)
                self.__dropdown.select_drop_down_values(
                    drop_down_id="credentials", values=[credential])
            else:
                self.__checkbox.uncheck(label="Saved credentials")
                self.__admin_console.fill_form_by_id("userName", username)
                self.__admin_console.fill_form_by_id("password", password)
            if enable_monitoring:
                self.__admin_console.enable_toggle(index=0, cv_toggle=True)
            if access_node:
                self.__dropdown.select_drop_down_values(
                    drop_down_id='accessNodes', values=[access_node])
        if live_crawl:
            self.__admin_console.select_radio(id="sourceType")
            self.__admin_console.wait_for_completion()
            self.__wizard.click_icon_button_by_title(self.__admin_console.props['label.update'])
            self.__treeview.clear_all()
            self.__browse.select_path(directory_path)
            self.__browse.save_path()
            if enable_monitoring:
                self.__admin_console.enable_toggle(index=0, cv_toggle=True)
        if backup_data_import:
            self.__admin_console.select_radio(id="backupType")
            self.__admin_console.wait_for_completion()
        if fso_server:
            self.__select_fso_crawl_type(crawl_type)
        self.__admin_console.click_button(self.__admin_console.props['button.label.create'])
        self.__admin_console.check_error_message()

    @PageService()
    def add_one_drive_server(self, search_name, search_category, display_name,
                             country_name, agent_installed=True, subclient_list=None, inventory_name=None):
        """
        Adds data source one drive server
        Args:
            search_name (str) - Name to search for
            search_category (str) - Search Category to search for
            Values:
                "Client name",
                "Domain Name",
                "Operating system",
                "Host name",
                "All"
            display_name (str) - Display name for this data source
            country_name (str) - Country name to be selected
            Values:
                "United Kingdom",
                "United States"
            agent_installed (bool): Verify if Agent Installed
            subclient_list (list): List of subclients
            inventory_name  (str)  : Name of inventory to be used

        """
        self._select_machine_to_analyze(
            search_name=search_name,
            search_category=search_category,
            agent_installed=agent_installed,
            inventory_name=inventory_name)
        self.__admin_console.fill_form_by_id("datasourceName", display_name)
        self.__dropdown.select_drop_down_values(values=[country_name], drop_down_id='countryCodeDropdown')
        self.__admin_console.wait_for_completion()
        if not subclient_list:
            self.__admin_console.select_radio("importFromBackup")
        else:
            self.__admin_console.select_radio("localCrawl")
            self.__admin_console.click_button(
                self.__admin_console.props['label.add']
            )
            self.__cv_tree.select_elements(search_name.lower(), subclient_list)
            self.__admin_console.wait_for_completion()

            self.__admin_console.click_button(
                self.__admin_console.props['button.label.create']
            )
        self.__admin_console.check_error_message()

    @PageService()
    def add_one_drive_v2_server(self, search_name, search_category, display_name,
                                country_name, agent_installed=True, subclient_list=None, inventory_name=None):
        """
        Adds OneDrive v2 server data source
        Args:
            search_name (str) - Name to search for
            search_category (str) - Search Category to search for
            Values:
                "Client name",
                "Domain Name",
                "Operating system",
                "Host name",
                "All"
            display_name (str) - Display name for this data source
            country_name (str) - Country name to be selected
            Values:
                "United Kingdom",
                "United States"
            agent_installed (bool): Verify if Agent Installed
            subclient_list (list): List of subclients
            inventory_name  (str)  : Name of inventory to be used

        """
        self._select_machine_to_analyze(search_name=search_name, search_category=search_category,
                                        agent_installed=agent_installed, inventory_name=inventory_name)
        self._add_datasource_helper(display_name, country_name, subclient_list)

    @PageService()
    def saas_add_one_drive_ds(self, search_name, display_name, country_name, subclient_list=None):
        """
        Adds OneDrive v2 server data source for SaaS
        Args:
            search_name (str)       - Name to search for
            display_name (str)      - Display name for this data source
            country_name (str)      - Country name to be selected
                Values:
                    "United Kingdom",
                    "United States"
            subclient_list (list)   - List of subclients

        """
        self.log.info(f"Adding OneDrive datasource for server {search_name} with name {display_name}")
        self.saas_select_server_to_analyze(search_name)
        self._add_datasource_helper(display_name, country_name, subclient_list)

    @PageService()
    def add_exchange_server(self, search_name, search_category, display_name,
                            country_name, agent_installed=True, list_of_mailboxes=None, inventory_name=None):
        """
        Adds data source exchange server
        Args:
            search_name (str) - Name to search for
            search_category (str) - Search Category to search for
            Values:
                "Client name",
                "Domain Name",
                "Operating system",
                "Host name",
                "All"
            display_name (str) - Display name for this data source
            country_name (str) - Country name to be selected
            Values:
                "United Kingdom",
                "United States"
            agent_installed (Bool) - Verify if Agent Installed
            list_of_mailboxes (list) - list of mailboxes to be added
            inventory_name  (str)  : Name of inventory to be used
        """
        self._select_machine_to_analyze(search_name=search_name, search_category=search_category,
                                        agent_installed=agent_installed, inventory_name=inventory_name,
                                        data_source_type=self.__admin_console.props['label.datasource.exchange'])
        self._add_datasource_helper(display_name, country_name, list_of_mailboxes)

    @PageService()
    def saas_add_exchange_ds(self, search_name, display_name, country_name, mailbox_list=None):
        """
        Adds Exchange data source for SaaS
        Args:
            search_name (str)   - Name to search for
            display_name (str)  - Display name for this data source
            country_name (str)  - Country name to be selected
                Values:
                    "United Kingdom",
                    "United States"
            mailbox_list (list) - list of mailboxes to be added

        """
        self.log.info(f"Adding Exchange datasource for server {search_name} with name {display_name}")
        self.saas_select_server_to_analyze(search_name)
        self._add_datasource_helper(display_name, country_name, mailbox_list)

    @PageService()
    def _add_datasource_helper(self, display_name, country_name, list_of_content):
        """
        Adds a SDG type datasource for OneDrive/Exchange Servers
        Args:
            display_name (str) - Display name for this data source
            country_name (str) - Country name to be selected
            Values:
                "United Kingdom",
                "United States"
            list_of_content (list) - list of content to be added
        """
        self.__admin_console.fill_form_by_id("datasourceName", display_name)
        self.__dropdown.select_drop_down_values(values=[country_name], drop_down_id='countryCodeDropdown')
        self.__admin_console.wait_for_completion()
        if not list_of_content:
            self.__admin_console.select_radio("allMailboxes")
        else:
            self.__admin_console.select_radio("selectMailboxes")
            self.__admin_console.click_button(
                self.__admin_console.props['label.add']
            )
            self.__table.select_rows(list_of_content, search_for=True)
            self.__admin_console.click_button(
                self.__admin_console.props["label.button.save"]
            )
        self.__admin_console.click_button(self.__admin_console.props['button.label.create'])
        self.__admin_console.check_error_message()

    @PageService()
    def add_database_server(self, search_name, search_category, display_name,
                            instance_name, country_name, agent_installed=True, inventory_name=None):
        """
        Adds data source database server
        Args:
            search_name (str) - Server name to search for
            search_category (str) - Search Category to search for
            Values:
                "Client name",
                "Domain Name",
                "Operating system",
                "Host name",
                "All"
            display_name (str) - Display name for this data source
            instance_name (str) - DB Instance name
            country_name (str) - Country name to be selected
            Values:
                "United Kingdom",
                "United States"
            agent_installed (bool): Verify if Agent Installed
            inventory_name  (str)  : Name of inventory to be used

        """
        self._select_machine_to_analyze(
            search_name=search_name,
            search_category=search_category,
            agent_installed=agent_installed,
            inventory_name=inventory_name)
        self.__admin_console.fill_form_by_id("datasourceName", display_name)
        self.__dropdown.select_drop_down_values(values=[country_name], drop_down_id='countryCodeDropdown')
        self.__admin_console.select_value_from_dropdown("instance", instance_name)
        self.__admin_console.click_button(self.__admin_console.props['label.finish'])
        self.__admin_console.check_error_message()

    @PageService()
    def add_gdrive_server(self, search_name, search_category, display_name,
                          country_name, agent_installed=True, inventory_name=None):
        """
        Adds data source  gdrive server
        Args:
            search_name (str) - Name to search for
            search_category (str) - Search Category to search for
            Values:
                "Client name",
                "Domain Name",
                "Operating system",
                "Host name",
                "All"
            display_name (str) - Display name for this data source
            country_name (str) - Country name to be selected
            Values:
                "United Kingdom",
                "United States"
            agent_installed (bool): Verify if Agent Installed
            inventory_name  (str)  : Name of inventory to be used

        """
        self._select_machine_to_analyze(
            search_name=search_name,
            search_category=search_category,
            agent_installed=agent_installed,
            inventory_name=inventory_name)
        self.__admin_console.fill_form_by_id("datasourceName", display_name)
        self.__dropdown.select_drop_down_values(values=[country_name], drop_down_id='countryCodeDropdown')
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button(self.__admin_console.props['label.finish'])
        self.__admin_console.check_error_message()

    @PageService()
    def add_share_point_server(self, search_name, search_category, display_name,
                               country_name, agent_installed=True, backupset=None, sites=None, inventory_name=None):
        """
        Adds data source Share Point server
        Args:
            search_name (str) - Name to search for
            search_category (str) - Search Category to search for
            Values:
                "Client name",
                "Domain Name",
                "Operating system",
                "Host name",
                "All"
            display_name (str) - Display name for this data source
            country_name (str) - Country name to be selected
            Values:
                "United Kingdom",
                "United States"
            agent_installed (bool): Verify if Agent Installed
            backupset (str): name of the backupset
            sites (str): list of sites which has to selected
            inventory_name  (str)  : Name of inventory to be used

        """
        self._select_machine_to_analyze(
            search_name=search_name,
            search_category=search_category,
            agent_installed=agent_installed,
            inventory_name=inventory_name,
            data_source_type=self.__admin_console.props['label.datasource.sharepoint'])
        self.__admin_console.fill_form_by_id("datasourceName", display_name)
        self.__dropdown.select_drop_down_values(values=[country_name], drop_down_id='countryCodeDropdown')
        self.__admin_console.wait_for_completion()
        self.__admin_console.select_value_from_dropdown("backupSet", backupset)
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button(self.__admin_console.props['label.browse'])
        self.__admin_console.wait_for_completion()
        list_of_sites = [sites]
        self.__cv_tree.select_elements_by_full_path(list_of_sites, "sharepoint")
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button(self.__admin_console.props['label.save'])
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button(self.__admin_console.props['label.finish'])
        self.__admin_console.check_error_message()

    @PageService()
    def add_fso_server_group_datasource(self, server_group_name, search_category, country_name, inventory_name=None):
        """
        Add FSO Server group Datasource
        Args:
            server_group_name (str) : Name of server group to run analytics on
            search_category (str) - Search Category to search for
               Values:
                    "Server Group Name",
                    "All"
            country_name (str) : Country Name
            inventory_name  (str)  : Name of inventory to be used
        """
        self._select_machine_to_analyze(search_name=server_group_name, search_category=search_category,
                                        inventory_name=inventory_name,
                                        data_source_type=self.__admin_console.props['label.serverGroup'])
        self.__dropdown.select_drop_down_values(values=[GovernanceApps.plan_name], drop_down_id="ediscoveryPlan")
        self.__dropdown.select_drop_down_values(values=[country_name], drop_down_id='countryCodeDropdown')
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button(self.__admin_console.props['label.finish'])
        self.__admin_console.check_error_message()

    @PageService()
    def select_inventory(self, inventory_name):
        """
            Select the inventory from the dropdown
        """
        self.__dropdown.select_drop_down_values(
            drop_down_id='Inventory', values=[inventory_name], facet=True)
        self.__admin_console.wait_for_completion()
        
    @PageService()
    def select_identity_server(self, identity_server):
        """
            Select the inventory from the dropdown
            Args:
            identity_server (str) : Name of the identity server
        """
        self.__dropdown.select_drop_down_values(
            drop_down_id='Identity server', values=[identity_server], preserve_selection=True)
        self.__admin_console.wait_for_completion()


    @PageService()
    def create_credentials(self, credential_name, username, password):
        """Method to create a new credential from configure file server page while adding datasource"""
        self.__wizard.click_icon_button_by_title(self.__admin_console.props['label.createNew'])
        self.__admin_console.wait_for_completion()
        self.__admin_console.fill_form_by_id("name", credential_name)
        self.__admin_console.fill_form_by_id("userAccount", username)
        self.__admin_console.fill_form_by_id("password", password)
        self.__wizard.click_button(self.__admin_console.props['label.save'])
        self.__admin_console.wait_for_completion()


class ObjectStorageClient:
    """class for object storage client creation"""

    def __init__(self, admin_console, cloud_app_type, config):
        """
               Creates a new ObjectStorageClient object
               Args:
                    admin_console   (Obj)       :   Admin console Objext
                    cloud_app_type  (str)       :   String specifying the cloud app type
                    config          (Obj)       :   Tuple of config.json


        """
        self._admin_console = admin_console
        self.CONFIG = config
        self.cloud_app_type = cloud_app_type
        self.dropdown = RDropDown(self._admin_console)
        self.table = Rtable(self._admin_console)
        self.modal_panel = RModalPanel(self._admin_console)
        self.log = self._admin_console.log

    @PageService()
    def _create_credential(self, credential_name):
        """
        Create a Credential Object in Cloud App Modal
        Returns:
            None
        """
        self.log.info("Creating Credentials with provided access key and account name")
        self._admin_console.click_by_id('selectWithCreateButton_button_#2034_credential')
        self._admin_console.fill_form_by_id('credentialName', credential_name)
        self._admin_console.fill_form_by_id('userName', self.CONFIG.AccountName)
        self._admin_console.fill_form_by_id('password', self.CONFIG.AccessKey)
        self._admin_console.fill_form_by_id('description', "Object Storage Test Credentials")
        self.modal_panel.submit()

    @PageService()
    def create_client(self, client_name, credential_name, access_node):
        """
        Creates an Object Storage client with the given inputs
        Returns:
            None
        """
        self._admin_console.access_tile('ADD_CLIENT')
        self._admin_console.click_by_id(cs.CLOUD_APP_TILE_NAMES[self.cloud_app_type])
        self._admin_console.wait_for_completion()
        self._admin_console.fill_form_by_id('cloudStorageName', client_name)
        self._admin_console.fill_form_by_id('hostURL', self.CONFIG.EndpointUrl)
        if self.cloud_app_type != cs.GCP:
            self._admin_console.select_value_from_dropdown(select_id='authenticationType',
                                                           value=cs.CLOUD_APP_AUTH_TYPES[self.cloud_app_type][0])
        self.dropdown.select_drop_down_values(drop_down_id="selectId", values=[credential_name])
        self.dropdown.select_drop_down_values(drop_down_id='clientId', values=[access_node])
        self.modal_panel.submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def select_client(self, client_name):
        """
        Selects the Cloud App client if it exists in the table
        Args:
            client_name (str)    :   object storage client name
        Returns:
            bool                                :   False if client was not found, True if it was found and selected
        """
        if 'Server name' in self.table.get_visible_column_names() and \
                self.table.is_entity_present_in_column(
                    'Server name', client_name):
            self.table.select_rows([client_name])
            self._admin_console.click_button_using_text('Next')
            return True
        else:
            return False

    @PageService()
    def add_data_source(self, object_storage_client, datasource_name, plan_name, credential_name, access_node):
        """
            Adds the object storage folder for crawling
            Args:
                object_storage_client (str)     :   Object storage client name
                datasource_name (str)           :   Data source name
                plan_name       (str)           :   Plan name
                credential_name (str)           :   Credential name
                access_node     (str)           :   Access Node

            Returns:
                None
        """
        url = self._admin_console.current_url()
        if "clienttype=client" in url.lower():
            if not self.select_client(object_storage_client):
                self.create_client(object_storage_client, credential_name, access_node)
        self.log.info("Adding Data Source")
        self._admin_console.fill_form_by_id('dsName', datasource_name)
        if "clienttype=client" in url.lower():
            self.dropdown.select_drop_down_values(drop_down_id='ediscoveryPlan', values=[plan_name])
        container_name = self.CONFIG.ContainerName
        container_name = container_name.strip('\\/ ')
        directory_path = f"/{container_name}"
        self.log.info(f'Directory path={directory_path}')
        self._admin_console.click_button(self._admin_console.props['label.browse'])
        container_elist = self._admin_console.driver.find_elements(By.XPATH,
            f"//label[contains( @title, '{container_name}')]")
        if len(container_elist) < 1:
            raise ValueError("The container_name provided does not exist")
        container_elist[0].click()
        self._admin_console.click_button(self._admin_console.props['label.save'])
        self._admin_console.click_button(self._admin_console.props['label.finish'])
