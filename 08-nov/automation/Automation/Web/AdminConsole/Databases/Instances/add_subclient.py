from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module implements the methods for creating a new subclient
or table group or database group or similar entities
Each database has a class that contains methods to add subclient for that database

AddCloudDBSubClient:
Functions:

select_cloud_regions()      :   Clicks on the region to add cloud content

_expand_cloud_region()      :   Expand the given region in the content 

_click_on_items_inside_region() :   Select the data inside the region specified

select_items_under_regions()    :   Select all the content under set of regions

AddDynamoDBSubClient:
Functions:

add_dynamodb_subclient()    :   Method to add subclient for dynamodb

AddRedshiftSubClient:
Functions:

add_redshift_subclient()    :   Method to add subclient for redshift

AddDocumentDbSubClient:
Functions:

add_docdb_subclient()       :   Method to add subclient for docdb

AddPostgreSQLSubClient:
Functions:

add_subclient()             :   method to add postgreSQL dumpbased subclient


AddMySQLSubClient:
Functions:

add_subclient()             :   method to add MySQL subclient

AddInformixSubClient:
Functions:

add_subclient()             :   Method to add Informix subclient

AddOracleSubClient:
Functions:

add_subclient()             :   Method to add Oracle subclient

AddDB2SubClient:
Functions:

add_subclient()             :   Method to add DB2 subclient

AddMSSQLSubclient:

    select_databases()      :   Method to select databases for subclient content

    add_subclient()         :   Method to add MSSQL subclient

AddSpannerSubclient:

    select_databases()      :   Selects the databases to be added to the subclient from the list

    add_spanner_subclient() :   Creates a new Cloud Spanner subclient

AddSAPOracleSubClient:

add_subclient()             :   Method to add SAP Oracle subclient

"""

from datetime import datetime
from Web.Common.page_object import (
    PageService, WebAction
)
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RModalPanel
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.browse import RContentBrowse
from Web.AdminConsole.Components.core import TreeView



class AddCloudDBSubClient(RModalPanel):
    """Class to implement common methods for adding cloud database subclient"""

    def __init__(self, admin_console):
        super(AddCloudDBSubClient, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__panel = RPanelInfo(self.__admin_console)
        self._content_browse = RContentBrowse(self._admin_console)


    @WebAction()
    def __click_on_cloud_region(self, region_name):
        """Clicks on the region to add cloud content
        Args:
            region_name (str):  Name of the region to be selected
        """
        self._driver.find_element(By.XPATH,
            f"//span[contains(text(),'{region_name}')]").click()

    @PageService()
    def select_cloud_regions(self, region_list):
        """Clicks on the region to add cloud content
        Args:
            region_list (list):  Name of the region to be selected
        """
        for region in region_list:
            self.__click_on_cloud_region(region)

    @WebAction()
    def _expand_cloud_region(self, region):
        """Expands the cloud region by clicking on the arrow near region
        Args:
            region  (str):  Full name of the cloud region

                            Example: ap-south-1
        """
        self._content_browse.expand_folder_path(folder=region)
        self._admin_console.wait_for_completion()

    @WebAction()
    def _click_on_items_inside_region(self, region, items_list):
        """Clicks on the items inside the cloud regions
        Args:
            region  (str):  Full nmae of the cloud region

                            Example: Asia Pacific (Mumbai) (ap-south-1)

            items_list  (list)  : List of items to be selected under region
        """
        self._content_browse.select_content(items_list)

    @PageService()
    def select_items_under_regions(self, mapping_dict):
        """Selects one or more items (like tables, clusters) under cloud regions
        Args:
            mapping_dict (dict) : The dictionary containing the full region names as keys
                                and LIST of items to be selected under them as value
                                Example --
                                mapping_dict={
                                'full region-1 name':['table1','table2','table3']
                                'full region-2 name':['item1','item2','item3']
                                }
        """
        for key, value in mapping_dict.items():
            self._expand_cloud_region(key)
            self._click_on_items_inside_region(key, value)


class AddDynamoDBSubClient(AddCloudDBSubClient):
    """Class to represent the add subclient panel for DynamoDB"""

    def __init__(self, admin_console):
        super(AddDynamoDBSubClient, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__dialog = RModalDialog(self.__admin_console)

    def add_dynamodb_subclient(self, subclient_name, plan, content,
                               streams=2, adjust_read_capacity=0):
        """Method to add subclient for dynamodb

        Args:
        subclient_name  (str):  Name of subclient
        plan            (str):  Name of plan
        content (list): List of names of regions to be added as content
        streams (int):  Number of streams to be set
        adjust_read_capacity (int): value that needs to be set for
                                    adjust read capacity
        """

        self.__dialog.fill_text_in_field('subclientName', subclient_name)
        self.__dialog.select_dropdown_values(values=[plan], drop_down_id='plan')
        if streams != 2:
            self.__dialog.fill_text_in_field('numberOfStreams', streams)
        if adjust_read_capacity != 0:
            self.__dialog.enable_toggle(toggle_element_id='adjustReadCapacity')
            adjust_read_capacity = str(adjust_read_capacity)
            self.__dialog.fill_text_in_field('units', adjust_read_capacity)
        self.__dialog.click_button_on_dialog(id="AddContent")
        self.__admin_console.wait_for_completion()
        if isinstance(content, dict):
            self.select_items_under_regions(content)
        elif isinstance(content, list):
            self.select_cloud_regions(content)
        content_dialog = RModalDialog(self._admin_console, title="Browse backup content")
        content_dialog.click_button_on_dialog(text='Save')
        self.__dialog.click_submit()
        self.__admin_console.check_error_message()


class AddRedshiftSubClient(AddCloudDBSubClient):
    """Class to add subclient for Redshift"""

    def __init__(self, admin_console):
        super(AddRedshiftSubClient, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__panel = RPanelInfo(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)

    @PageService()
    def add_redshift_subclient(self, subclient_name, plan, content):
        """Method to add subclient for redshift

        Args:
        subclient_name  (str):  Name of subclient
        plan            (str):  Name of plan
        content         (list): List of names of regions to be added as content
        """

        self.__dialog.fill_text_in_field('subclientName', subclient_name)
        self.__dialog.select_dropdown_values(drop_down_id='plan',
                                             values=[plan])
        self.__dialog.click_button_on_dialog(id="AddContent")
        self.__admin_console.wait_for_completion()
        self.select_items_under_regions(content)
        content_dialog = RModalDialog(self._admin_console, title="Browse backup content")
        content_dialog.click_button_on_dialog(text='Save')
        self.__dialog.click_submit()
        self.__admin_console.check_error_message()

class AddDocumentDbSubClient(AddCloudDBSubClient):
    """Class to add subclient for DOCDB"""
    def __init__(self, admin_console):
        super(AddDocumentDbSubClient, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__panel = RPanelInfo(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)

    @PageService()
    def add_docdb_subclient(self, subclient_name, plan, content):
        """Method to add subclient for docdb

        Args:
        subclient_name  (str):  Name of subclient
        plan            (str):  Name of plan
        content         (list): List of names of regions to be added as content
        """

        self.__dialog.fill_text_in_field('subclientName', subclient_name)
        self.__dialog.select_dropdown_values(drop_down_id='plan',
                                             values=[plan])
        self.__dialog.click_button_on_dialog(id="AddContent")
        self.__admin_console.wait_for_completion()
        self.select_items_under_regions(content)
        content_dialog = RModalDialog(self._admin_console, title="Browse backup content")
        content_dialog.click_button_on_dialog(text='Save')
        self.__dialog.click_submit()
        self.__admin_console.check_error_message()


class AddPostgreSQLSubClient(RModalDialog):
    """Class to represent the restore panel for PostgreSQL"""

    def __init__(self, admin_console):
        super(AddPostgreSQLSubClient, self).__init__(admin_console)
        self.__admin_console = admin_console

    def add_subclient(self, subclient_name, number_backup_streams,
                      collect_object_list, plan, database_list):
        """
        method to add postgreSQL dumpbased subclient

        Args:
            subclient_name          (str):  Name of the subclient

            number_backup_streams   (int): number of streams used for backup

            collect_object_list     (bool): boolean value to specify if collect object
            list needs to be enabled

            plan                    (str):  plan name to be assigned to subclient

            database_list           (list): list of databases which needs to be part
            of subclient content

        """
        self.fill_text_in_field('subclientName', subclient_name)
        self.fill_text_in_field('numberOfStreams', number_backup_streams)
        if collect_object_list:
            self.select_checkbox('collectObjectList')

        self.select_dropdown_values(values=[plan], drop_down_id='plan')
        self.select_items(database_list)
        self.click_button_on_dialog('Save')


class AddMySQLSubClient(RModalDialog):
    """Class to represent the add subclient panel of MySQL"""

    def __init__(self, admin_console):
        super(AddMySQLSubClient, self).__init__(admin_console)

    @PageService()
    def add_subclient(self, subclient_name, number_backup_streams, database_list, plan):
        """
        method to add MySQL subclient

        Args:
            subclient_name          (str):  Name of the subclient

            number_backup_streams   (int): number of streams used for backup

            database_list           (list): list of databases which needs to be part
                                            of subclient content

            plan                    (str):  plan name to be assigned to subclient

        """
        self.fill_text_in_field('subclientName', subclient_name)
        self.fill_text_in_field('numberOfStreams', number_backup_streams)
        self.select_dropdown_values(values=[plan], drop_down_id='plan')
        self.select_items(database_list)
        self.click_button_on_dialog('Save')


class AddInformixSubClient(RModalDialog):
    """Class to represent the add subclient panel of Informix"""

    def __init__(self, admin_console):
        super(AddInformixSubClient, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.props = self.__admin_console.props

    @WebAction()
    def __select_dbspace(self):
        """
        Method to select automation created dbspace cvauto1 as content for selective subclient
        """
        self._driver.find_element(By.XPATH, "//span[contains(text(),'cvauto1')]").click()

    @PageService()
    def add_subclient(self, subclient_name, plan, bkp_mode, incr_level=1):
        """
        Method to add Informix subclient

        Args:
            subclient_name  (str):  Name of the subclient
            plan            (str):  Plan to be assigned to subclient
            bkp_mode        (str):  Backup mode as in command center with no space between words
                Accepted Values  :  'Entireinstance', 'Wholesystem', 'Selective',
                                    'Fulllogicallogs' and 'Fullandcurrentlogicallogs'
            incr_level      (int):  backup level for incremental backups
                Accepted Values  :  1 or 2

        """
        backuptypes = {
            'entireinstance': 'label.entireInstance',
            'wholesystem': 'label.wholeSystem',
            'selective': 'label.selective',
            'fulllogicallogs': 'label.fullLogicalLogs',
            'fullandcurrentlogicallogs': 'label.fullCurrentLogicalLogs'
        }
        self.fill_text_in_field('subclientName', subclient_name)
        self.select_dropdown_values(values=[plan], drop_down_id='plan')
        self.select_dropdown_values(drop_down_id='backupMode', values=[self.props[backuptypes[bkp_mode.lower()]]])
        if bkp_mode.lower() == "selective":
            self.__select_dbspace()
        self.fill_text_in_field('backupLevel', incr_level)
        self.click_submit()


class AddOracleSubClient(RModalPanel):
    """Class to represent the add subclient panel of Oracle"""

    def __init__(self, admin_console):
        super(AddOracleSubClient, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.props = self.__admin_console.props
        self.__panel_dropdown = RDropDown(self.__admin_console)
        self.__content_browse = RContentBrowse(self.__admin_console)

    @PageService()
    def add_subclient(self, subclient_name, plan, number_backup_streams=2,
                      backup_mode="Selective online full", archive_log_backup=True,
                      delete_archive_logs=True, table_browse=False, content=None):
        """
        method to add Oracle subclient

        Args:
            subclient_name          (str):  Name of the subclient

            number_backup_streams   (int): number of streams used for backup
                default: 2

            plan                    (str):  plan name to be assigned to subclient

            backup_mode             (str):  "Online database"/"Subset of online database"/"Offline database"/"Archive log backup"/"Select online full"
                default: Online

            content                 (list): List of components to be selected

            archive_log_backup      (bool): True if Archive log backups
                default: True

            delete_archive_logs     (bool): True if delete archive logs is to be enabled
                default: True

            table_browse            (bool): True if table-level browse is to be enabled
                default:False
        """
        self.__admin_console.fill_form_by_name('subclientName', subclient_name)
        self.__admin_console.fill_form_by_name('numberOfStreams', number_backup_streams)
        self.__panel_dropdown.select_drop_down_values(values=[plan],
                                                      drop_down_id='plan')

        self.__panel_dropdown.select_drop_down_values(values=[backup_mode],
                                                      drop_down_id='backupMode')
        if backup_mode != 'Offline database':
            if backup_mode == 'Online database' or 'Subset of online database':
                if content:
                    self.__content_browse.select_content(content)
                if not archive_log_backup:
                    self.__admin_console.checkbox_deselect('backupArchivelog')
            if not delete_archive_logs:
                self.__admin_console.checkbox_deselect('archiveDelete')
        if table_browse:
            self.__admin_console.checkbox_select('enableTableBrowse')
        self.__admin_console.click_button_using_id('Save')


class AddDB2SubClient(RModalDialog):
    """Class to represent the add subclient panel of DB2"""

    def __init__(self, admin_console):
        super(AddDB2SubClient, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__browse = RBrowse(self.__admin_console)

    @PageService()
    def add_subclient(self, subclient_name, plan, number_data_streams, data_backup,
                      type_backup, exclude_logs, backup_logs, delete_logs, partitioned_database=False):
        """
            method to add DB2 subclient

        Args:
            subclient_name          (str):  Name of the subclient

            plan                    (str):  plan name to be assigned to subclient

            number_data_streams     (int): number of streams used for backup

            data_backup             (bool): boolean value to specify data backup

            type_backup             (str): type of backup - online or offline

            exclude_logs            (bool): To backup logs or not into backup image

            backup_logs             (bool): Backup archived logs or not

            delete_logs             (bool): Delete archived logs after backup or not
        """
        self.fill_text_in_field("subclientName", subclient_name)
        self.select_dropdown_values(
            drop_down_id='plan', values=[plan])
        if partitioned_database:
            self.click_button_on_dialog(text="Edit")
            edit_eb2_partition_node_dropdown = RModalDialog(self._admin_console, title="Edit DB2 partition node")
            edit_eb2_partition_node_dropdown.fill_text_in_field("noOfStreams", number_data_streams)
            edit_eb2_partition_node_dropdown.click_submit()
        else:
            self.fill_text_in_field("numberOfStreams", number_data_streams)
        if data_backup:
            self.enable_disable_toggle(id="dataOptions", enable=True)
            if type_backup.lower() == "online":
                self.select_dropdown_values(
                    drop_down_id='backupMode', values=['Online database'])
                if not partitioned_database:
                    if exclude_logs:
                        self.select_checkbox(checkbox_id="exLogsBacku")
                    else:
                        self.deselect_checkbox(checkbox_id="exLogsBacku")

                if backup_logs:
                    self.enable_disable_toggle(id="archLogBackup", enable=True)
                    if delete_logs:
                        self.select_checkbox("delArchiveLogsAft")
                    else:
                        self.deselect_checkbox("delArchiveLogsAft")
                else:
                    self.enable_disable_toggle(id="archLogBackup", enable=False)

            elif type_backup.lower() == "offline":
                self.select_dropdown_values(
                    drop_down_id='backupMode', values=['Offline database'])

            else:
                raise Exception("Invalid backup type")

        else:
            self.enable_disable_toggle(id="dataOptions", enable=False)

            if backup_logs:
                self.enable_disable_toggle(id="archLogBackup", enable=True)
                if delete_logs:
                    self.select_checkbox(checkbox_id="delArchiveLogsAft")
                else:
                    self.deselect_checkbox(checkbox_id="delArchiveLogsAft")
            else:
                self.enable_disable_toggle(id="archLogBackup", enable=False)
                raise Exception("Select atleast one backup option.")

        self.click_submit()


class AddMSSQLSubclient(RModalDialog):
    """Class to represent the add subclient panel for MSSQL"""
    def __init__(self, admin_console):
        super(AddMSSQLSubclient, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__react_dropdown = RDropDown(self.__admin_console)

    @PageService()
    def select_databases(self, db_list):
        """Selects the databases to be added to the subclient from the list

            Args:

                db_list (list)        --     List of database names to be added

        """
        for db in db_list:
            self.__admin_console.fill_form_by_xpath(
                "//div[@class='grid-main-container']//input[@aria-label='grid-search']", db)
            db_xpath = f"//*[text()='{db}']//preceding::td[@role='gridcell']/input[@type='checkbox']"
            if not self.__admin_console.check_if_entity_exists("xpath", db_xpath):
                raise CVWebAutomationException(f"{db} not found in content")
            self.__admin_console.click_by_xpath(db_xpath)

    @PageService()
    def add_subclient(self, sqlhelper, plan_name, database_list=None):
        """Creates a new SQL subclient

            Args:

                sqlhelper (:obj:'SQLHelper')      :   SQLHelper object

                plan_name (str)                   :   Plan name for the new subclient

                database_list (list/Optional)     :   List of databases to associate.
                Default is None and will add all databases created during setup.
        """
        time1 = (datetime.now()).strftime("%H%M%S")
        subclientname = "Subclient{0}_{1}".format(sqlhelper.sqlautomation.tcobject.id, time1)
        self.__admin_console.fill_form_by_id("subclientName", subclientname)

        if database_list is None:
            self.select_databases(sqlhelper.subcontent)
        else:
            self.select_databases(database_list)

        self.select_dropdown_values(values=[plan_name], drop_down_id='plan')
        self.__admin_console.click_button_using_id("Save")
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

        sqlhelper.sqlautomation.tcobject.instance.subclients.refresh()
        sqlhelper.subclient = sqlhelper.sqlautomation.tcobject.instance.subclients.get(
            subclientname)
        sqlhelper.time1 = time1


class AddSpannerSubclient(RModalDialog):
    """Class to represent the add subclient panel for Cloud Spanner"""
    def __init__(self, admin_console):
        super(AddSpannerSubclient, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__tree = TreeView(self.__admin_console)

    @PageService()
    def select_databases(self, db_list):
        """Selects the databases to be added to the subclient from the list

            Args:

                db_list (list)        --     List of database names to be added

        """
        self.__tree.select_items(db_list)

    @PageService()
    def add_spanner_subclient(self, spanner_helper, plan_name, database_list=None):
        """Creates a new Cloud Spannersubclient

            Args:

                spanner_helper (:obj:'SpannerHelper')   :   SpannerHelper object

                plan_name (str)                         :   Plan name for the new subclient

                database_list (list)                    :   List of databases to associate. Default is None
        """
        tctime = spanner_helper.tctime.replace(":", "")
        subclient_name = "AutoSubclient{0}_{1}".format(spanner_helper.tcobject.id, tctime)

        self.__admin_console.fill_form_by_name("subclientName", subclient_name)
        self.select_databases(database_list)
        self.select_dropdown_values(values=[plan_name], drop_down_id='plan')
        self.click_button_on_dialog('Save')
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

        spanner_helper.tcobject.instance.subclients.refresh()
        spanner_helper.subclient = spanner_helper.tcobject.instance.subclients.get(subclient_name)

class AddSAPOracleSubClient(RModalDialog):
    """Class to represent the add subclient panel of Oracle"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.props = self.__admin_console.props
        
    @PageService()
    def add_subclient(self, subclient_name, plan, number_backup_streams=2,
                      backup_mode="Selective online full", backup_device="UTIL_FILE",
                      archive_log_backup=True, delete_archive_logs=True, disable_switch_log=False, create_second_copy_logs=False):
        """
        method to add Oracle subclient

        Args:
            subclient_name          (str):  Name of the subclient

            number_backup_streams   (int): number of streams used for backup
                default: 2

            plan                    (str):  plan name to be assigned to subclient

            backup_mode             (str):  "Online database"/"Subset of online database"/"Offline database"/"Archive log backup"/"Selective online full"
                default: Online
            
            backup_device           (str):  "UTIL_FILE"/"RMAN_UTIL"/"UTIL_FILE_ONLINE"

            archive_log_backup      (bool): True if Archive log backups
                default: True

            delete_archive_logs     (bool): True if delete archive logs is to be enabled
                default: True

            disable_switch_log      (bool): True if switch log needs to be disabled
                default:False

            create_second_copy_logs (bool): True if logs need to have second copy
                default:False
            
        """
        self.fill_text_in_field('subclientName', subclient_name)
        self.fill_text_in_field('numberOfStreams', number_backup_streams)
        self.select_dropdown_values(values=[plan],
                                                      drop_down_id='plan')

        self.select_dropdown_values(values=[backup_mode],
                                                      drop_down_id='backupMode')
        self.select_radio_by_id(backup_device)
        if backup_mode != 'Offline database':
            if backup_mode=='Online database' or 'Subset of online database':
                if not archive_log_backup:
                    self.deselect_checkbox('backupArchivelog')
            if not delete_archive_logs:
                    self.deselect_checkbox('archiveDelete')
            if disable_switch_log:
                self.select_checkbox('disableSwitchCurrentLog')
            if create_second_copy_logs:
                self.select_checkbox('archiveLogSecondCopy')
        self.click_submit()

