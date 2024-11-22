from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the common functions/operations that can be performed on the Database
instance details page, the page that opens after selecting an instance from Databases page.

Since some agents have restore option only from instance and few have from
both instance and subclient level, We have two ENUMs and maps.
One is to associate Database types with add subclient class
Another one is to associate Database types with restore panel class

DBInstanceDetails:
------------------
    get_instance_details()              --  Returns details of Instance

    get_instance_entities()             --  Returns the list of items/entities in the Instance
    details page which could be one of the following:subclients or Table groups or Backupsets
    or Database groups

    delete_instance()                   --  Deletes the instance

    list_backup_history_of_entity()     --  Clicks on 'Backup history' from given entity's action items

    click_on_entity()                   --  Clicks the given entity which can be subclient or
    backupset or table group

    click_add_subclient()               --  Clicks on add subclient/table group/ database group
    and returns the object of add subclient class of database corresponding to database_type
    argument

    access_restore()                    --  Clicks on the restore button below the recovery
    points in instance page

    access_instant_clone()              --  Clicks on the instant clone button below the recovery
    points in instance page

    clear_all_selection()               --  Clicks on clear all checkbox in browse page if present

    restore_folders()                   --  Clicks on the given items, analogous to folders in the
    browse page and submits restore. Also returns the object of restore panel class corresponding
    to database_type argument

    restore_files_from_multiple_pages() --  Clicks on items from multiple pages recursively in
    browse page and submits restore. Also returns the object of restore panel class corresponding
    to database_type argument

    access_configuration_tab()          --  Clicks on 'Configuration' tab on instance details page

    access_subclients_tab()             --  Clicks on 'Subclients' tab on instance details page

    access_overview_tab()               --  Clicks on 'Overview' tab on instance details page

    select_entities_tab()               --  Clicks on the entity tab on instance details page

    edit_instance_change_plan()         --  Edits instance to change plan associated

    instant_clone()                     --  Clicks on Instant clone in instance details page and
    returns the object of instant clone class corresponding to database_type argument

    list_restore_history_of_entity()     --  Clicks on 'Restore history' from given entity's action items

    delete_entity()                      --  Deletes the entity from instance details page

    click_on_edit()                      --  Clicks on edit in the General tile in instance details
                                             page

    discover_databases()                -- Clicks on discover database link

    access_actions_item_of_entity()     --  Clicks on 'Database groups/Backupset' tab 
                                            on the instance details page, 
                                            performs action on the provided entity

MySQLInstanceDetails:
---------------------
    enable_xtrabackup()                 --  Edits instance to enable xtrabackup option and
                                            specify xtrabackup log directory

    enable_standby_instance()           --  Edits instance to enable standby instance option
                                            and specify standby instance

    add_ssl_ca_path()                   --  Edits the instance to add ssl ca file path


PostgreSQLInstanceDetails instance Attributes:
----------------------------------------------

    **binary_directory**                --  returns postgres binary directory

    **library_directory**               --  returns postgres Library directory

    **archive_log_directory**           --  returns postgres archive log directory

    **version**                         --  returns postgres server version

    **user**                            --  returns postgres user

    **port**                            --  returns postgres server port

    **unix_user**                       --  returns unix user

    unix_user()                         --  setter for unix user

Db2InstanceDetails instance Attributes:
---------------------------------------

    **db2_home_directory**              --  returns db2 home directory

    **db2_version**                     --  returns db2 application version

    **db2_user_name**                   --  returns db2 instance user name

    db2_edit_instance_properties()      --  Method to modify DB2 instance username property

    add_db2_database()                  --  Method to add database on instance details page

    db2_backup()                        --  Method to run backup job for DB2 database from instance details page

CloudDBInstanceDetails:
-----------------------
    modify_region_for_cloud_account()   --  Method to set region restriction for cloud account

    edit_cloud_mysql_ssl_properties()   --  Method to Edit Cloud MySQL SSL properties

InformixInstanceDetails instance Attributes:
---------------------------------------

    **informix_home**                   --  returns informix home directory

    **onconfig**                        --  returns informix onconfig filename

    **sqlhosts**                        --  returns informix sqlhosts file path

    **informix_username**               --  returns informix user name


OracleInstanceDetails:
----------------------
    edit_instance_update_credentials()  --  Edits instance to change connect string and
                                            plan associated
    edit rac_instance_details()         --  Edit instance to change connect string for Rac nodes

MSSQLInstanceDetails:
----------------------

    add_subclient()                     --  Method to create a MSSQL subclient

    impersonate_user()                  --  Impersonates user for MSSQL using discrete credentials

    impersonate_user_with_cred_manager  --  Impersonated user for MSSQL using credential manager

SpannerInstanceDetails:
----------------------

    db_type()                           --  Returns the DBInstances Type enum of Cloud Spanner

    add_subclient()                     --  Creates a Cloud Spanner subclient

SAPHANAInstanceDetails:
----------------------

    update_credentials()                --  Updates instance details

MultinodeDatabaseInstanceDetails:
--------------------------------

PostgreSQLClusterInstanceDetails:
---------------------------------

    cluster_type()                      --  Returns the type of the database cluster (e.g., 'native' or 'EFM').

    cluster_nodes()                     --  Returns the number of nodes in the database cluster.

    archive_log_delete()                --  Returns whether archive logs are set to be deleted (True or False).

    master_if_standby_unavailable()     --  Returns whether the master server is used for backup if the standby server
                                            is unavailable (True or False).

    master_for_log_backup()             --  Returns whether the master server is always used for 
                                            log backups (True or False).
    
    move_cluster_node_up()              -- changes the priority of cluster by moving the specified node up
    
    move_cluster_node_down()            -- changes the priority of cluster by moving the specified node down
    
    delete_cluster_node()               -- deletes a specified node form the cluster
    
    edit_cluster_node()                 -- edit the node's properties
    
    add_cluster_node()                  -- add a new node to the cluster


SAPOracleInstanceDetails:
----------------------
    edit_instance_update_credentials()  --  Edits instance to change connect string and
                                            plan associated
    
    
    toggle_master_if_standby_unavailable()  -- Toggles use master is standby unavailable option
      
"""
from enum import Enum
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from datetime import datetime
from Web.Common.page_object import (
    PageService, WebAction
)
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import PanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog, RBackup
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Databases.db_instances import DBInstances

from Web.AdminConsole.Databases.Instances.add_subclient import AddDynamoDBSubClient
from Web.AdminConsole.Databases.Instances.add_subclient import AddMySQLSubClient
from Web.AdminConsole.Databases.Instances.add_subclient import AddPostgreSQLSubClient
from Web.AdminConsole.Databases.Instances.add_subclient import AddRedshiftSubClient
from Web.AdminConsole.Databases.Instances.add_subclient import AddDocumentDbSubClient
from Web.AdminConsole.Databases.Instances.add_subclient import AddInformixSubClient
from Web.AdminConsole.Databases.Instances.add_subclient import AddOracleSubClient
from Web.AdminConsole.Databases.Instances.add_subclient import AddMSSQLSubclient
from Web.AdminConsole.Databases.Instances.add_subclient import AddSpannerSubclient
from Web.AdminConsole.Databases.Instances.add_subclient import AddSAPOracleSubClient
from Web.AdminConsole.Databases.Instances.restore_panels import DynamoDBRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import OracleRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import DB2RestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import RedshiftRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import InformixRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import CosmosDBSQLRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import CosmosDBCASSANDRARestorePanel
from Web.AdminConsole.Databases.Instances.instant_clone import OracleInstantClone
from Web.AdminConsole.Databases.Instances.restore_panels import PostgreSQLRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import MySQLRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import SybaseRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import SAPOracleRestorePanel


class DBInstanceDetails:
    """Class for Database Instances page"""

    class SubclientTypes(Enum):
        """Enum to represent classes for adding subclient"""
        DYNAMODB = "AddDynamoDBSubClient"
        MYSQL = "AddMySQLSubClient"
        REDSHIFT = "AddRedshiftSubClient"
        DOCUMENTDB = "AddDocumentDbSubClient"
        INFORMIX = "AddInformixSubClient"
        ORACLE = "AddOracleSubClient"
        MSSQL = "AddMSSQLSubclient"
        SPANNER = "AddSpannerSubclient"
        POSTGRES = "AddPostgreSQLSubClient"
        SYBASE = "AddSybaseSubClient"
        SAP_ORACLE = "AddSAPOracleSubClient"

    class RestorePanelTypes(Enum):
        """Enum to represent classes for implementing restore panel"""
        DYNAMODB = "DynamoDBRestorePanel"
        ORACLE = "OracleRestorePanel"
        DB2 = "DB2RestorePanel"
        MYSQL = "MySQLRestorePanel"
        REDSHIFT = "RedshiftRestorePanel"
        DOCUMENTDB = "DocumentDbRestorePanel"
        INFORMIX = "InformixRestorePanel"
        COSMOSDB_SQL = "CosmosDBSQLRestorePanel"
        COSMOSDB_CASSANDRA = "CosmosDBCASSANDRARestorePanel"
        MSSQL = "SQLRestorePanel"
        POSTGRES = "PostgreSQLRestorePanel"
        SPANNER = "SpannerRestorePanel"
        SYBASE = "SybaseRestorePanel"
        SAP_ORACLE = "SAPOracleRestorePanel"

    class InstantClonePanelTypes(Enum):
        """Enum to represent class for implementing instant clone panel"""
        ORACLE = "OracleInstantClone"

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): Object of AdminConsole class
        """
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console)
        self.__browse = RBrowse(self.__admin_console)
        self.__panel = RPanelInfo(self.__admin_console)
        self._panel_dropdown = RDropDown(self.__admin_console)
        self._dialog = RModalDialog(self.__admin_console)
        self.__instance_panel = RPanelInfo(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.__page_container = PageContainer(self.__admin_console)
        self.props = self.__admin_console.props
        self.__add_subclient_map = {
            DBInstances.Types.DYNAMODB: DBInstanceDetails.SubclientTypes.DYNAMODB,
            DBInstances.Types.MYSQL: DBInstanceDetails.SubclientTypes.MYSQL,
            DBInstances.Types.REDSHIFT: DBInstanceDetails.SubclientTypes.REDSHIFT,
            DBInstances.Types.DOCUMENTDB: DBInstanceDetails.SubclientTypes.DOCUMENTDB,
            DBInstances.Types.INFORMIX: DBInstanceDetails.SubclientTypes.INFORMIX,
            DBInstances.Types.ORACLE: DBInstanceDetails.SubclientTypes.ORACLE,
            DBInstances.Types.MSSQL: DBInstanceDetails.SubclientTypes.MSSQL,
            DBInstances.Types.SPANNER: DBInstanceDetails.SubclientTypes.SPANNER,
            DBInstances.Types.POSTGRES: DBInstanceDetails.SubclientTypes.POSTGRES,
            DBInstances.Types.SYBASE: DBInstanceDetails.SubclientTypes.SYBASE,
            DBInstances.Types.SAP_ORACLE: DBInstanceDetails.SubclientTypes.SAP_ORACLE
        }
        self.__restore_panel_map = {
            DBInstances.Types.DYNAMODB: DBInstanceDetails.RestorePanelTypes.DYNAMODB,
            DBInstances.Types.ORACLE: DBInstanceDetails.RestorePanelTypes.ORACLE,
            DBInstances.Types.MYSQL: DBInstanceDetails.RestorePanelTypes.MYSQL,
            DBInstances.Types.REDSHIFT: DBInstanceDetails.RestorePanelTypes.REDSHIFT,
            DBInstances.Types.DOCUMENTDB: DBInstanceDetails.RestorePanelTypes.DOCUMENTDB,
            DBInstances.Types.INFORMIX: DBInstanceDetails.RestorePanelTypes.INFORMIX,
            DBInstances.Types.COSMOSDB_SQL: DBInstanceDetails.RestorePanelTypes.COSMOSDB_SQL,
            DBInstances.Types.COSMOSDB_CASSANDRA: DBInstanceDetails.RestorePanelTypes.COSMOSDB_CASSANDRA,
            DBInstances.Types.DB2: DBInstanceDetails.RestorePanelTypes.DB2,
            DBInstances.Types.ORACLE_RAC: DBInstanceDetails.RestorePanelTypes.ORACLE,
            DBInstances.Types.POSTGRES: DBInstanceDetails.RestorePanelTypes.POSTGRES,
            DBInstances.Types.SPANNER: DBInstanceDetails.RestorePanelTypes.SPANNER,
            DBInstances.Types.DB2_MULTINODE: DBInstanceDetails.RestorePanelTypes.DB2,
            DBInstances.Types.SYBASE: DBInstanceDetails.RestorePanelTypes.SYBASE,
            DBInstances.Types.SAP_ORACLE: DBInstanceDetails.RestorePanelTypes.SAP_ORACLE
        }
        self.__instant_clone_panel_map = {
            DBInstances.Types.ORACLE: DBInstanceDetails.InstantClonePanelTypes.ORACLE
        }

    @PageService()
    def get_instance_details(self):
        """Returns details of Instance"""
        self.__page_container.select_overview_tab()
        self.__instance_panel = RPanelInfo(self.__admin_console, title='General')
        return self.__instance_panel.get_details()

    @PageService()
    def get_instance_entities(self):
        """
        Returns the list of items/entities in the Instance details page which could
        be one of the following:
        subclients or Table groups or Backupsets or Database groups
        """
        self.__page_container.select_entities_tab()
        return self.__table.get_column_data(self.__admin_console.props['label.name'])

    @PageService()
    def delete_instance(self, check_errors=False):
        """Deletes the instance
        Args:
                check_errors (bool):    Checks and returns alert
        """
        self.__page_container.access_page_action_from_dropdown('Delete')
        self._dialog.type_text_and_delete('DELETE')
        self.__admin_console.wait_for_completion()

        if check_errors:
            return self._alert.check_error_message(raise_error=False)

    @PageService()
    def click_on_entity(self, entity_name):
        """Clicks the given entity which can be subclient or backupset or table group
        Args:
            entity_name (str)  :    Name of the entity which needs to be clicked

        """
        self.__page_container.select_entities_tab()
        self.__table.access_link(entity_name)

    @PageService()
    def click_add_subclient(self, database_type):
        """Clicks on add subclient/table group/ database group and returns the object
        of add subclient class of database corresponding to database_type argument

        Args:
            database_type (Types):   Type of database should be one among the types
                                     defined in 'Types' enum in DBInstances.py file

        Returns:
            Object (SubclientTypes):  Object of class in SubclientTypes corresponding to
                                        database_type
        """
        self.__page_container.select_entities_tab()
        self.__page_container.click_button(id='addSubclient')
        return globals()[self.__add_subclient_map[database_type].value](self.__admin_console)

    @PageService()
    def list_backup_history_of_entity(self, entity_name):
        """Clicks on 'Backup history' from any entity's action items(like subclient)
        Args:
            entity_name (str)   :   Name of entity to view backup history
        """
        self.__page_container.select_entities_tab()
        self.__table.access_action_item(entity_name,
                                        self.__admin_console.props['label.BackupHistory'])

    @PageService()
    def access_restore(self):
        """Clicks on the restore button below the recovery points in instance page"""
        self.__page_container.select_overview_tab()
        self.__instance_panel = RPanelInfo(self.__admin_console)
        self.__instance_panel.click_button(self.__admin_console.props['action.restore'])

    @PageService()
    def access_instant_clone(self):
        """Clicks on the Instant clone button below the recovery points in instance page"""
        self.__page_container.select_overview_tab()
        self.__instance_panel = RPanelInfo(self.__admin_console)
        self.__instance_panel.click_button(self.__admin_console.props['label.clone'])

    @PageService()
    def clear_all_selection(self):
        """Clicks on clear all checkbox in browse page if present"""
        self.__browse.clear_all_selection()

    @PageService()
    def restore_folders(self, database_type, items_to_restore=None, all_files=False,
                        copy=None):
        """ Selects files and folders to restore

        Args:
            database_type (Types):   Type of database should be one among the types defined
                                      in 'Types' enum in DBInstances.py file

            items_to_restore (list):  the list of files and folders to select for restore

                default: None

            all_files        (bool):  select all the files shown for restore / download

                default: False

            copy            (str):  The name of the copy to browse from
                                    Example- "Secondary" or "Copy-2"
                default: None

        Returns:
            Object (RestorePanelTypes): Object of class in RestorePanelTypes corresponding
                                        to database_type
        """
        if copy:
            self.__browse.select_storage_copy(copy, database=True)
        self.clear_all_selection()
        self.__browse.select_files(items_to_restore, all_files)
        self.__browse.submit_for_restore()
        return globals()[self.__restore_panel_map[database_type].value](self.__admin_console)

    @PageService()
    def restore_files_from_multiple_pages(self, database_type, mapping_dict, root_node,
                                          copy=None):
        """Clicks on items from multiple pages recursively in browse page
        and submits restore. Also returns the object of restore panel class
        corresponding to database_type argument

        Args:
            database_type (Types):   Type of database should be one among the types defined
                                      in 'Types' enum in DBInstances.py file

            mapping_dict (dict) : The dictionary containing the folder names as keys
                                and list of files to be selected under them as value

                Example:
                    mapping_dict={
                    'FOLDER1':['file1','file2','file3']
                    'FOLDER2':['fileA','fileB','fileC']
                    }

            root_node   (str):  The name of the subclient/instance on which browse operation
                                    was performed or the name of the root folder that
                                    appears on the browse page

            copy        (str):  The name of the copy to browse from
                                Example- "Secondary" or "Copy-2"

        Returns:
            Object (RestorePanelTypes): Object of class in RestorePanelTypes corresponding
                                        to database_type
        """
        if copy:
            self.__browse.select_storage_copy(copy, database=True)
        for folder, file_list in mapping_dict.items():
            self.__browse.select_path_for_restore(path=folder, file_folders=file_list)
        self.__browse.submit_for_restore()
        return globals()[self.__restore_panel_map[database_type].value](self.__admin_console)

    @PageService()
    def access_configuration_tab(self):
        """Clicks on 'Confiugration' tab on the instance details page"""
        self.__admin_console.access_tab(
            self.__admin_console.props['heading.settings'])

    @PageService()
    def access_subclients_tab(self):
        """Clicks on 'Subclients' tab on the instance details page"""
        self.__admin_console.access_tab('Subclients')

    @PageService()
    def access_overview_tab(self):
        """Clicks on 'Overview' tab on the instance details page"""
        self.__admin_console.access_tab(
            self.__admin_console.props['heading.overview'])

    def select_entities_tab(self):
        """Clicks on the entity tab on the instance details page"""
        self.__page_container.select_entities_tab()

    @PageService()
    def edit_instance_change_plan(self, new_plan):
        """ Edits instance to change plan
            Args:
                new_plan    (str):   New plan for the instance
        """
        try:
            self.__instance_panel = RPanelInfo(self.__admin_console, "General")
            self.click_on_edit()
        except (NoSuchElementException, ElementNotInteractableException):
            self.__admin_console.select_hyperlink(
                self.__admin_console.props['action.edit'])
        self._panel_dropdown.select_drop_down_values(
            values=[new_plan],
            drop_down_id='planDropdown')
        try:
            self.__instance_panel.click_button(self.__admin_console.props['label.submit'])
        except (NoSuchElementException, ElementNotInteractableException):
            self.__admin_console.submit_form()
        self.__admin_console.wait_for_completion()

    @PageService()
    def instant_clone(self, database_type):
        """Method for accessing instant clone panel in instance details
        Args:
            database_type (Types):   Type of database should be one among the types defined
                                      in 'Types' enum in DBInstances.py file
        Returns:
            Object (InstantClonePanelTypes): Object of class in InstantClonePanelTypes corresponding
                                        to database_type
        """
        self.access_instant_clone()
        return globals()[self.__instant_clone_panel_map[database_type].value](self.__admin_console)

    @PageService()
    def list_restore_history_of_entity(self, entity_name):
        """Clicks on 'Restore history' from any entity's action items(like subclient)
        Args:
            entity_name (str)   :   Name of entity to view restore history
        """
        self.__page_container.select_entities_tab()
        self.__table.access_action_item(entity_name,
                                        self.__admin_console.props['label.RestoreHistory'])

    @PageService()
    def delete_entity(self, entity_name):
        """Deletes the entity from entity's action item
        Args:
            entity_name (str)   :   Name of entity to delete
        """
        self.__page_container.select_entities_tab()
        self.__table.access_action_item(entity_name, 'Delete')
        self._dialog = RModalDialog(self.__admin_console)
        self._dialog.type_text_and_delete('DELETE')
        self.__admin_console.wait_for_completion()

    @PageService()
    def click_on_edit(self):
        """Clicks the edit button on Instance Details page"""
        self.__panel.edit_tile()

    @PageService()
    def discover_databases(self):
        """
        Clicks on Discover Databases Link
        """
        self.__page_container.select_entities_tab()
        self.__table.access_toolbar_menu(self.__admin_console.props['label.discoverDatabases'])

    @PageService()
    def access_actions_item_of_entity(self, entity_name, action_item):
        """
        Clicks on 'Database groups/Backupset' tab on the instance details page and
        performs action on the provided entity
        Args:
            entity_name (str)   :   Name of entity
            action_item (str)   :   Name of action item
        """
        self.__page_container.select_entities_tab()
        self.__table.access_action_item(entity_name, action_item)


class PostgreSQLInstanceDetails(DBInstanceDetails):
    """
    This class provides the function or operations to perform on postgres instance page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(PostgreSQLInstanceDetails, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.postgres_instance_properties = None

    @property
    def binary_directory(self):
        """returns postgres binary directory"""
        if not self.postgres_instance_properties:
            self.postgres_instance_properties = self.get_instance_details()
        return self.postgres_instance_properties['Binary directory']

    @property
    def library_directory(self):
        """returns postgres Library directory"""
        if not self.postgres_instance_properties:
            self.postgres_instance_properties = self.get_instance_details()
        return self.postgres_instance_properties['Library directory']

    @property
    def archive_log_directory(self):
        """returns postgres archive log directory"""
        if not self.postgres_instance_properties:
            self.postgres_instance_properties = self.get_instance_details()
        return self.postgres_instance_properties['Archive log directory']

    @property
    def version(self):
        """returns postgres server version"""
        if not self.postgres_instance_properties:
            self.postgres_instance_properties = self.get_instance_details()
        return self.postgres_instance_properties['Version']

    @property
    def user(self):
        """returns postgres user"""
        if not self.postgres_instance_properties:
            self.postgres_instance_properties = self.get_instance_details()
        return self.postgres_instance_properties['PostgreSQL user name']

    @property
    def port(self):
        """returns postgres server port"""
        if not self.postgres_instance_properties:
            self.postgres_instance_properties = self.get_instance_details()
        return self.postgres_instance_properties['Port']

    @WebAction()
    def _get_unix_user(self):
        """ gets unix user from instance details"""
        return self.__admin_console.driver.find_element(By.XPATH,
                                                        '//input[@name="unixUsername"]').get_attribute('value')

    @property
    def unix_user(self):
        """returns unix user"""
        self.click_on_edit()
        self.__admin_console.wait_for_completion()
        self._dialog.expand_accordion(
            self.props['label.assets.database.connectionDetails'])
        user_name = self._get_unix_user()
        self.__admin_console.submit_form()
        return user_name

    @unix_user.setter
    def unix_user(self, user_name):
        """ setter for unix username

        Args:
            user_name   (str)   --  Unix user name to set
        """
        self.click_on_edit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.expand_accordion(self.props['label.assets.database.connectionDetails'])
        self.__admin_console.fill_form_by_name('unixUsername', user_name)
        self.__admin_console.submit_form()


class Db2InstanceDetails(DBInstanceDetails):
    """This class provides the function or operations to perform on postgres instance page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(Db2InstanceDetails, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.db2_instance_properties = None
        self.__table = Rtable(self.__admin_console)
        self.__panel = RPanelInfo(self.__admin_console)

    @property
    def db2_home_directory(self):
        """returns db2 home directory"""
        if not self.db2_instance_properties:
            self.db2_instance_properties = self.get_instance_details()
        return self.db2_instance_properties['Home']

    @property
    def db2_version(self):
        """returns db2 version"""
        if not self.db2_instance_properties:
            self.db2_instance_properties = self.get_instance_details()
        return self.db2_instance_properties['Version']

    @property
    def db2_user_name(self):
        """returns db2 user name"""
        if not self.db2_instance_properties:
            self.db2_instance_properties = self.get_instance_details()
        return self.db2_instance_properties['User name']

    @PageService()
    def db2_edit_instance_properties(self, username, password, plan=None, credential_name=None):
        """
        Changes DB2 instance configurations.
        Args:
            username      (str)        -- New username

            password      (str)        -- New password

            credential_name(str)        -- Credential Name

            plan          (str)        -- New Plan
                default: None

        Returns:
            True            -- If change is successful

        Raises:
            Exception:
                If change of properties is unsuccessful
        """
        self.__panel.edit_tile()
        if plan:
            self._panel_dropdown.select_drop_down_values(drop_down_id='planDropdown', values=[plan])
        if credential_name:
            self._panel_dropdown.select_drop_down_values(drop_down_id='credentialsdbInstance', values=[credential_name])
        self.__admin_console.click_button(id='editCredentialButton')
        self.__admin_console.fill_form_by_id('name', credential_name)
        self.__admin_console.fill_form_by_id('userName', username)
        self.__admin_console.fill_form_by_id('password', password)
        self._dialog.click_save_button()
        self.__admin_console.wait_for_completion()
        self.__admin_console.submit_form()
        _error_message = self.__admin_console.get_error_message()
        if _error_message == "":
            return True
        raise Exception("Exception in editing configuration: {0}".format(_error_message))

    @PageService()
    def add_db2_database(self, database_name, plan):
        """
        Adds DB2 database
        Args:
            database_name      (str)        -- Database name

            plan               (str)        -- Storage plan for the database

        Returns:
            True            -- If change is successful

        Raises:
            Exception:
                If change of properties is unsuccessful
        """
        self.__table.access_toolbar_menu('Add database')

        self.__admin_console.fill_form_by_id("dbName", database_name)

        self._panel_dropdown.select_drop_down_values(
            drop_down_id='planDropdown', values=[plan])

        self.__admin_console.submit_form()
        _error_message = self.__admin_console.get_error_message()
        if _error_message == "":
            return True
        raise Exception("Exception in adding database: {0}".format(_error_message))

    @PageService()
    def db2_backup(self, database_name, subclient_name, backup_type="full"):
        """
        Submits backup job from the instance details page
        Args:
            database_name               (str)               -- Name of database

            subclient_name              (str)               -- Name of subclient

            backup_type                 (str)               -- backup type

                default: full

        Returns
            (str) -- Backup job id

        """
        backup_map = {
            "full": RBackup.BackupType.FULL,
            "incremental": RBackup.BackupType.INCR,
            "differential": RBackup.BackupType.DIFF
        }
        backup_type = backup_type.lower()
        backup_type = backup_map[backup_type]

        self.__table.access_action_item(database_name,
                                        self.__admin_console.props['action.backup'])

        return RBackup(self.__admin_console).submit_backup(backup_type=backup_type,
                                                           backupset_name=database_name,
                                                           subclient_name=subclient_name)


class MySQLInstanceDetails(DBInstanceDetails):
    """This class provides the function or operations to perform on MySQL instance page
        """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(MySQLInstanceDetails, self).__init__(admin_console)
        self.__admin_console = admin_console

    @PageService()
    def enable_xtrabackup(self, xtra_backup_bin_path):
        """Edits the instance to enable Xtrabackup
            Args:
                xtra_backup_bin_path    (str):  XtraBackup Bin path
        """
        self.click_on_edit()
        self._dialog.expand_accordion(self.__admin_console.props['label.assets.database.advancedOptions'])
        self._dialog.enable_toggle(toggle_element_id="hotBackup")
        self._dialog.select_radio_by_value("enableXtraBackup")
        self._dialog.submit_file('xtraBackupPath', xtra_backup_bin_path)
        self._dialog.click_submit()

    @PageService()
    def enable_standby_instance_backup(self, standby_instance, run_logs_on_source=False):
        """Edits the instance to enable standby instance for backup
            Args:
                standby_instance    (str):  Name of the standby instance
                run_logs_on_source  (Boolean):  True if transaction logs are to be
                                                run on source
                    Default:    False
        """
        self.click_on_edit()
        self._dialog.expand_accordion(self.__admin_console.props['label.assets.database.advancedOptions'])
        self._dialog.enable_toggle(toggle_element_id="enableProxyBackup")
        self._dialog.select_dropdown_values(values=[standby_instance], drop_down_id="standbyInstance")
        if run_logs_on_source:
            self._dialog.select_checkbox(checkbox_id="runLogBackupsOnSource")
        self._dialog.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def add_ssl_ca_path(self, ssl_ca_path, raise_error=True):
        """Edits the instance to add ssl ca file path
            Args:
                ssl_ca_path    (str):  SSL CA file path

                raise_error    (bool): flag to check if instance
                edit error needs to be raised or not

                    default: True

        """
        self.click_on_edit()
        self._dialog.expand_accordion(self.__admin_console.props['label.assets.database.advancedOptions'])
        self._dialog.enable_toggle(toggle_element_id="useSSLOption")
        self._dialog.fill_text_in_field(element_id="sslCa", text=ssl_ca_path)
        self._dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message(raise_error)

    @PageService()
    def disable_use_ssl_option(self):
        """Disables the use ssl option"""
        self.click_on_edit()
        self._dialog.expand_accordion(self.__admin_console.props['label.assets.database.advancedOptions'])
        self._dialog.disable_toggle(toggle_element_id="useSSLOption")
        self._dialog.click_submit()
        self.__admin_console.wait_for_completion()


class CloudDBInstanceDetails(DBInstanceDetails):
    """This class provides the common functions or operations that can be performed on
        instances of cloud databases like RDS, dynamodb, redshift, documentdb"""

    def __init__(self, admin_console):
        """Method to initialize CloudDBIstanceDetails class
        Args:
            admin_console (AdminConsole):   Object of AdminConsole class
        """
        super().__init__(admin_console)
        self.__admin_console = admin_console

    @PageService()
    def modify_region_for_cloud_account(self, region_name):
        """Method to set a region restriction for cloud account
        Args:
            region_name (list): The list of cloud regions that needs to be set/enabled
                                for the cloud account
        """
        self.access_configuration_tab()
        settings_panel = RPanelInfo(self.__admin_console,
                                    title=self.__admin_console.props['label.nav.settings'])
        settings_panel.edit_tile_entity(
            self.__admin_console.props['dbObjType.region'])
        _panel_dropdown = RDropDown(self.__admin_console)
        _panel_dropdown.select_drop_down_values(values=region_name,
                                                drop_down_id='regionDropdown')
        settings_panel.click_button('Submit')

    @PageService()
    def edit_cloud_mysql_ssl_properties(self, ssl_ca, ssl_cert, ssl_key):
        """ Method to Edit Cloud MySQL SSL properties
        Args:
            ssl_ca           (str):  SSL CA file path on proxy
            ssl_cert         (str):  SSL Cert filepath on proxy
            ssl_key          (str):  SSL Key filepath on proxy
        """
        self.click_on_edit()
        self._dialog.expand_accordion(self.__admin_console.props['label.assets.database.advancedOptions'])
        self._dialog.enable_toggle(toggle_element_id="useSSLOption")
        self._dialog.fill_text_in_field(element_id="sslCa", text=ssl_ca)
        self._dialog.fill_text_in_field(element_id="sslCert", text=ssl_cert)
        self._dialog.fill_text_in_field(element_id="sslKey", text=ssl_key)
        self._dialog.click_submit()

class InformixInstanceDetails(DBInstanceDetails):
    """This class provides the function or operations to perform on Informix instance page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(InformixInstanceDetails, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.informix_instance_properties = None

    @property
    def informix_home(self):
        """returns informix home directory"""
        if not self.informix_instance_properties:
            self.informix_instance_properties = self.get_instance_details()
        return self.informix_instance_properties['Informix home']

    @property
    def onconfig(self):
        """returns informix onconfig file name"""
        if not self.informix_instance_properties:
            self.informix_instance_properties = self.get_instance_details()
        return self.informix_instance_properties['Onconfig file']

    @property
    def sqlhosts(self):
        """returns informix sqlhosts file path"""
        if not self.informix_instance_properties:
            self.informix_instance_properties = self.get_instance_details()
        return self.informix_instance_properties['SQLHOSTS file']

    @property
    def informix_username(self):
        """returns informix user name"""
        if not self.informix_instance_properties:
            self.informix_instance_properties = self.get_instance_details()
        return self.informix_instance_properties['User name']


class OracleInstanceDetails(DBInstanceDetails):
    """This class provides the function or operations to perform on Oracle instance page
       """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(OracleInstanceDetails, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__panel = RPanelInfo(self.__admin_console)

    @PageService()
    def edit_instance_update_credentials(self, connect_string, plan=None):
        """Method to Update connect string for oracle instance
            Args:
                connect_string  (str):  Connect string for the server in the format:
                                        <Username>/<Password>@<Service Name>
                plan            (str):  New plan for the instance
                    default: None

        """
        credentials, service_name = connect_string.split("@")
        username, password = credentials.split("/")
        self.__panel.edit_tile()
        if plan:
            self._panel_dropdown.select_drop_down_values(
                values=[plan], drop_down_id='planDropdown')
        self.__admin_console.fill_form_by_name('dbUserName', username)
        self.__admin_console.fill_form_by_name('dbPassword', password)
        self.__admin_console.fill_form_by_name('serviceName', service_name)
        self.__admin_console.click_button(id="Save")

    @PageService()
    def edit_rac_instance_details(self, server_name, db_username, db_password, db_instance_name,clear=False):
        """Edits rac instance Details
            Args:
                server_name (str) : Name of the rac node
                db_username (str) : Username for database
                db_password (str) : Password for the database
                db_instance_name (str) : Name of the instance
                clear       (Bool)   :   True if you want to clear connect string details
                                        default : False
        """
        path = f"//div[contains(@aria-label,\'{server_name}\')]/ancestor::tr//div[@aria-label='Edit']"
        self.__admin_console.click_by_xpath(path)
        if clear:
            self.__admin_console.fill_form_by_id(element_id="dbUserName", value="/")
            self.__admin_console.fill_form_by_id(element_id="serviceName", value=" ")
        else:
            self.__admin_console.fill_form_by_id(element_id="dbUserName", value=db_username)
            self.__admin_console.fill_form_by_id(element_id="dbPassword", value=db_password)
            self.__admin_console.fill_form_by_id(element_id="serviceName", value=db_instance_name)
        self.__admin_console.click_button(id="Save")


class MSSQLInstanceDetails(DBInstanceDetails):
    """
    This class provides the helper functions to perform operations on MSSQL instance page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(MSSQLInstanceDetails, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__panel = PanelInfo(self.__admin_console)

    @property
    def db_type(self):
        return DBInstances.Types.MSSQL

    @PageService()
    def add_subclient(self, sqlhelper, plan_name, **kwargs):
        """ Creates a MSSQL subclient

            Args:
                sqlhelper (:obj:'SQLHelper')            --  SQLHelper object

                plan_name (str)                         --  Plan name for the new subclient

            Keyword Args:
                database_list (list)                    --  List of databases to associate. Default is None

        """
        self.click_add_subclient(self.db_type).add_subclient(sqlhelper, plan_name, **kwargs)

    @PageService()
    def impersonate_user(self, username, password, plan_name):
        """ Impersonates user with sysadmin access

            Args:
                username (str)          --      User with sysadmin access

                password (str)          --      Password for the above user

                plan_name (str)         --      Plan Name for instance(This is required because
                                                Admin Console requires a plan to be assigned
                                                every time Edit is clicked)

        """
        self.click_on_edit()
        self._panel_dropdown.select_drop_down_values(
            values=[plan_name],
            drop_down_id='planSummaryDropdown')
        self.__admin_console.enable_toggle(toggle_id="toggle", cv_toggle=True)
        self.__admin_console.select_radio("uselocalSystemAccountImp")
        self.__admin_console.fill_form_by_name("username", username)
        self.__admin_console.fill_form_by_name("password", password)
        self.__admin_console.submit_form()
        _error_message = self.__admin_console.get_error_message()
        if _error_message == "":
            return True
        raise CVWebAutomationException("Exception in impersonating user: {0}".format(_error_message))

    @PageService()
    def impersonate_user_with_cred_manager(self, username, password, tc_id, description=None):
        """ Impersonates user with sysadmin access with Credential Manager UI

                        Args:
                            username (str)          --      User with sysadmin access

                            password (str)          --      Password for the above user

                            tc_id  (int)            --      Test Case id (Needed only to create name and description)

                           description (str)         --      Description for credential entity (Optional)

        """
        self.__panel.edit_tile_entity(self.props["label.sqlServerAccount"])

        self._dialog.enable_toggle(self.props["label.overrideHigherLevelsSettings"])
        self.__admin_console.select_radio("uselocalSystemAccountImp")
        self._dialog.click_add()

        time_now = (datetime.now()).strftime("%H:%M:%S")
        time_now = time_now.replace(":", "_")
        credential_name = "Atmn_TC_" + str(tc_id) + "_" + time_now
        if not description:
            description = f"This credential is created as part of automation run of testcase {tc_id}. Can be deleted"

        self.__admin_console.fill_form_by_name("credentialName", credential_name)
        self.__admin_console.fill_form_by_name("userName", username)
        self.__admin_console.fill_form_by_name("password", password)
        self.__admin_console.fill_form_by_id("description", description)

        self.__admin_console.submit_form(form_name="addEditUserForm")
        error_message = self.__admin_console.get_error_message()
        if error_message:
            raise CVWebAutomationException("Exception in creating credentials: {0}".format(error_message))

        self.__admin_console.submit_form(form_name="addSqlServerForm")
        error_message = self.__admin_console.get_error_message()
        if error_message:
            raise CVWebAutomationException("Exception in impersonating user: {0}".format(error_message))

        return True


class SpannerInstanceDetails(DBInstanceDetails):
    """
    This class provides the helper functions to perform operations on a Google Spanner instance page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(SpannerInstanceDetails, self).__init__(admin_console)

    @property
    def db_type(self):
        return DBInstances.Types.SPANNER

    @PageService()
    def add_subclient(self, spanner_helper, plan_name, database_list=None):
        """ Creates a Cloud Spanner subclient

            Args:
                spanner_helper (:obj:'SpannerHelper')   --  SpannerHelper object

                plan_name (str)                         --  Plan name for the new subclient

                database_list (list)                    --  List of databases to associate. Default is None

        """
        self.click_add_subclient(self.db_type).add_spanner_subclient(spanner_helper, plan_name, database_list)


class CosmosDBCassandraInstanceDetails(DBInstanceDetails):
    """
    This class provides the helper functions to perform operations on CosmosDB Cassandra API instance page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(CosmosDBCassandraInstanceDetails, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__browse = RBrowse(admin_console)
        self.__panel = RPanelInfo(admin_console)
        self.__table = Rtable(admin_console)

    @PageService()
    def restore_folders(
            self,
            database_type,
            dbaccount,
            items_to_restore=None,
            all_files=False,
            copy=None):
        """ Selects files and folders to restore

        Args:
            database_type (Types):   Type of database should be one among the types defined
                                      in 'Types' enum in DBInstances.py file

            dbaccount (str)      :   Cosmos DB account

            items_to_restore (list):  the list of files and folders to select for restore

                default: None

            all_files        (bool):  select all the files shown for restore / download

                default: False

            copy            (str):  The name of the copy to browse from
                                    Example- "Secondary" or "Copy-2"
                default: None

        Returns:
            Object (RestorePanelTypes): Object of class in RestorePanelTypes corresponding
                                        to database_type
        """
        if copy:
            self.__browse.select_storage_copy(copy, database=True)
        self.__table.access_link_by_column(
            entity_name=self.__admin_console.props['dbObjType.storageaccount.azure.cosmos.db.table.api'],
            link_text=dbaccount)
        self.__browse.select_files(items_to_restore, all_files)
        self.__browse.submit_for_restore()
        return CosmosDBCASSANDRARestorePanel(self.__admin_console)

    @PageService()
    def access_table_groups_tab(self):
        """Clicks on 'Table groups' tab on the instance details page"""
        self.__admin_console.access_tab(
            self.__admin_console.props['label.tableGroups'])


class SybaseInstanceDetails(DBInstanceDetails):
    """
    This class provides the function or operations to perform on sybase instance page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(SybaseInstanceDetails, self).__init__(admin_console)
        self.__admin_console = admin_console


class SAPHANAInstanceDetails(DBInstanceDetails):
    """
    This class provides the helper functions to perform operations on a SAP HANA instance page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(SAPHANAInstanceDetails, self).__init__(admin_console)
        self.__admin_console = admin_console

    @PageService()
    def update_credentials(self, username, password):
        """ Updates instance details

            Args:
                    username (str)              --      new username for DB

                    password (str)              --      new password for DB
        """
        self.__admin_console.click_button(id='tile-action-btn')
        self.__admin_console.select_radio(id='USER')
        self.__admin_console.fill_form_by_name('dbUsername', username)
        self.__admin_console.fill_form_by_name('dbPassword', password)
        self.__admin_console.click_button(id='Save')


class MultinodeDatabaseInstanceDetails(DBInstanceDetails):
    """
    This class provides the helper functions to perform operations on a Multinode Database instance page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console  (obj)                 --  The admin console class object

        """
        super(MultinodeDatabaseInstanceDetails, self).__init__(admin_console)
        self.__admin_console = admin_console


class PostgreSQLClusterInstanceDetails(PostgreSQLInstanceDetails):
    """
    This class provides the helper functions to perform operations on a Postgres Cluster Database instance page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """

        super(PostgreSQLClusterInstanceDetails, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.postgres_cluster_instance_properties = None

    @property
    def cluster_type(self):
        """
        Returns the type of the database cluster (e.g., 'primary' or 'standby').
        """
        if not self.postgres_cluster_instance_properties:
            self.postgres_cluster_instance_properties = self.get_instance_details()
        return self.postgres_cluster_instance_properties['Cluster type']

    @property
    def cluster_nodes(self):
        """
        Returns the number of nodes in the database cluster.
        """
        if not self.postgres_cluster_instance_properties:
            self.postgres_cluster_instance_properties = self.get_instance_details()
        return self.postgres_cluster_instance_properties['Cluster nodes']

    @property
    def archive_log_delete(self):
        """
        Returns whether archive logs are set to be deleted (True or False).
        """
        if not self.postgres_cluster_instance_properties:
            self.postgres_cluster_instance_properties = self.get_instance_details()
        return self.postgres_cluster_instance_properties['Delete archive logs']

    @property
    def master_if_standby_unavailable(self):
        """
        Returns whether the master server is used if the standby server is unavailable (True or False).
        """
        if not self.postgres_cluster_instance_properties:
            self.postgres_cluster_instance_properties = self.get_instance_details()
        return self.postgres_cluster_instance_properties['Use the master server if the standby server is not available']

    @property
    def master_for_log_backup(self):
        """
        Returns whether the master server is always used for log backups (True or False).
        """
        if not self.postgres_cluster_instance_properties:
            self.postgres_cluster_instance_properties = self.get_instance_details()
        return self.postgres_cluster_instance_properties['Always use the master server to back up logs']

    @PageService()
    def move_cluster_node_up(self, node_num):
        """
        Changes the priority of cluster nodes by moving the specifies node up
        Args:
            node_num (int) : priority of node to be changed
        """
        self.access_configuration_tab()
        node_panel = RPanelInfo(self.__admin_console, title="PostgreSQL cluster nodes")
        node_panel.edit_tile()
        edit_panel = RModalDialog(self.__admin_console, title='Edit PostgreSQL cluster nodes')
        edit_panel.click_button_on_dialog(aria_label='Move up', button_index=node_num)
        edit_panel.click_save_button()
        self.__admin_console.driver.refresh()

    @PageService()
    def move_cluster_node_down(self, node_num):
        """
        Changes the priority of cluster nodes by moving the specifies node down
        Args:
            node_num (int) : priority of node to be changed
        """
        self.access_configuration_tab()
        node_panel = RPanelInfo(self.__admin_console, title="PostgreSQL cluster nodes")
        node_panel.edit_tile()
        edit_panel = RModalDialog(self.__admin_console, title='Edit PostgreSQL cluster nodes')
        edit_panel.click_button_on_dialog(aria_label='Move down', button_index=node_num)
        edit_panel.click_save_button()
        self.__admin_console.driver.refresh()

    @PageService()
    def delete_cluster_node(self, node_num):
        """
        deletes the node from the cluster
        Args:
            node_num (int) : priority of node to be deleted
        """
        self.access_configuration_tab()
        node_panel = RPanelInfo(self.__admin_console, title="PostgreSQL cluster nodes")
        node_panel.edit_tile()
        edit_panel = RModalDialog(self.__admin_console, title='Edit PostgreSQL cluster nodes')
        edit_panel.click_button_on_dialog(aria_label='Delete', button_index=node_num)
        edit_panel.click_save_button()
        self.__admin_console.driver.refresh()

    @PageService()
    def edit_cluster_node(self, node_num, node_to_edit, cluster_bin=None, cluster_conf=None):
        """
        edits a node's properties in the cluster
        Args:
            node_num (int) : priority of node to be changed
            node_to_edit (dict) : dictionary containing the values to be edited
            cluster_conf (str) : conf path of cluster manager
            cluster_bin (str) : bin path of cluster manager
        Note:
            node_to_edit : The nodes list is a list of dict of a node that contains the following
            give only the pair that needs to be edited
            {
                password (str): The password for accessing the PostgreSQL server
                port (int): The port number on which the PostgreSQL server is running
                bin_dir (str): The directory where PostgreSQL binary files are located
                lib_dir (str): The directory where PostgreSQL library files are located
                archive_wal_dir (str): The directory where Write-Ahead Logging (WAL) files are archived
            }
        """
        self.access_configuration_tab()
        node_panel = RPanelInfo(self.__admin_console, title="PostgreSQL cluster nodes")
        node_panel.edit_tile()
        edit_panel = RModalDialog(self.__admin_console, title='Edit PostgreSQL cluster nodes')
        edit_panel.click_button_on_dialog(aria_label='Edit', button_index=node_num)
        edit_dialog = RModalDialog(self.__admin_console, title="Edit PostgreSQL cluster node")
        if 'password' in node_to_edit.keys():
            edit_dialog.fill_text_in_field(element_id='dbPassword', text=node_to_edit.get('password'))
        if 'port' in node_to_edit.keys():
            edit_dialog.fill_text_in_field(element_id='port', text=node_to_edit.get('port'))
        if 'bin_dir' in node_to_edit.keys():
            edit_dialog.fill_text_in_field(element_id='binaryPath', text=node_to_edit.get('bin_dir'))
        if 'lib_dir' in node_to_edit.keys():
            edit_dialog.fill_text_in_field(element_id='libPath', text=node_to_edit.get('lib_dir'))
        if 'archive_wal_dir' in node_to_edit.keys():
            edit_dialog.fill_text_in_field(element_id='archiveLogPath', text=node_to_edit.get('archive_wal_dir'))
        if cluster_bin:
            edit_dialog.fill_text_in_field(element_id='clusterBinaryPath', text=cluster_bin)
        if cluster_conf:
            edit_dialog.fill_text_in_field(element_id='clusterConfigFile', text=cluster_conf)
        edit_panel.click_save_button()
        self.__admin_console.driver.refresh()

    @PageService()
    def add_cluster_node(self, node_to_add, cluster_bin=None, cluster_conf=None):
        """
        adds a new node to the cluster
        Args:
            node_to_add (dict) : dictionary containing the values to be edited
            cluster_conf (str) : conf path of cluster manager
            cluster_bin (str) : bin path of cluster manager
        Note:
            node_to_add : The nodes list is a list of dict of a node that contains the following
            {
                server (str): The name of the server.
                password (str): The password for accessing the PostgreSQL server
                port (int): The port number on which the PostgreSQL server is running
                bin_dir (str): The directory where PostgreSQL binary files are located
                lib_dir (str): The directory where PostgreSQL library files are located
                archive_wal_dir (str): The directory where Write-Ahead Logging (WAL) files are archived
            }
        """
        self.access_configuration_tab()
        node_panel = RPanelInfo(self.__admin_console, title="PostgreSQL cluster nodes")
        node_panel.edit_tile()
        edit_panel = RModalDialog(self.__admin_console, title='Edit PostgreSQL cluster nodes')
        edit_panel. click_button_on_dialog(text='Add')
        add_dialog = RModalDialog(self.__admin_console, title="Add PostgreSQL cluster node")
        add_dialog.select_dropdown_values(drop_down_id='serverDropdown', values=[node_to_add.get('server')])
        add_dialog.fill_text_in_field(element_id='dbPassword', text=node_to_add.get('password'))
        add_dialog.fill_text_in_field(element_id='port', text=node_to_add.get('port'))
        add_dialog.fill_text_in_field(element_id='binaryPath', text=node_to_add.get('bin_dir'))
        add_dialog.fill_text_in_field(element_id='libPath', text=node_to_add.get('lib_dir'))
        add_dialog.fill_text_in_field(element_id='archiveLogPath', text=node_to_add.get('archive_wal_dir'))
        if cluster_bin:
            add_dialog.fill_text_in_field(element_id='clusterBinaryPath', text=cluster_bin)
            add_dialog.fill_text_in_field(element_id='clusterConfigFile', text=cluster_conf)
        add_dialog.click_save_button()
        edit_panel.click_save_button()
        self.__admin_console.driver.refresh()
    


    @PageService()
    def toggle_master_if_standby_unavailable(self, enable=True):
        """
        Toggles use master is standby unavailable option
        Args:
            enable (bool) : selector deselect the option (default:true)
        """
        self.click_on_edit()
        edit_panel = RModalDialog(self.__admin_console, title='Edit PostgreSQL instance')
        if enable:
            edit_panel.select_checkbox('useMasterForDataBkp')
        else:
            edit_panel.deselect_checkbox('useMasterForDataBkp')
        edit_panel.click_submit()

class SAPOracleInstanceDetails(DBInstanceDetails):
    """
    This class provides the function or operations to perform on SAP Oracle instance page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.__panel = RPanelInfo(self.__admin_console)
    
    @PageService()
    def edit_instance_update_credentials(self, connect_string, plan=None):
        """Method to Update connect string for oracle instance
            Args:
                connect_string  (str):  Connect string for the server in the format:
                                        <Username>/<Password>@<Service Name>
                plan            (str):  New plan for the instance
                    default: None

        """
        credentials, service_name = connect_string.split("@")
        username, password = credentials.split("/")
        self.__panel.edit_tile()
        if plan:
            self._panel_dropdown.select_drop_down_values(
                values=[plan], drop_down_id='planDropdown')
        self.__admin_console.fill_form_by_name('dbUserName', username)
        self.__admin_console.fill_form_by_name('dbPassword', password)
        self.__admin_console.fill_form_by_name('serviceName', service_name)
        self.__admin_console.click_button(id="Save")
     
