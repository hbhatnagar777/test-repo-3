import time

from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides functions and operations that can be performed on Salesforce Restore page

SalesforceRestore:

    __select_restore_type()                 --  Click on restore_type on Select restore type screens

    __select_files_for_restore()            --  Selects files for restore on Browse page

    __submit_restore()                      --  Submits restore job and gets job id from popup

    _restore_to_database()                  --  Fill Salesforce restore options form for object level restore from media
                                                to database

    _restore_to_file_system()               --  Fill Salesforce restore options form for object level restore from media
                                                to File System

    _restore_to_salesforce()                --  Fill Salesforce restore options form for object level restore from media
                                                to Salesforce

    object_level_restore()                  --  Submit restore job for object level restore

    metadata_restore()                      --  Submits restore job for Metadata restore

    get_rows_from_record_level_restore()    --  Gets table data for sf_object from record level restore page

    record_level_restore()                  --  Submits restore job for record level restore
"""
from Application.CloudApps.SalesforceUtils.constants import DbType
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.browse import Browse, RBrowse
from Web.AdminConsole.Components.panel import DropDown, ModalPanel, RDropDown, RModalPanel
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.core import Checkbox
from Web.Common.exceptions import CVWebAutomationException
from .constants import (
    DependentLevel,
    ParentLevel,
    RestoreType,
    RestoreTarget,
    ReactRestoreTarget,
    RecordLevelVersion,
    OLD_DATABASE_FORM,
    DATABASE_FORM,
    DESTINATION_CLIENT,
    RDESTINATION_CLIENT,
    GroupOperation,
    ColumnOperation, FieldMapping
)
from dataclasses import dataclass
from selenium.common.exceptions import NoSuchElementException


@dataclass()
class RuleModel:
    """read only class to hold rule level data for simplified filters"""
    column: str
    value: str
    filter: ColumnOperation = ColumnOperation.CONTAINS


@dataclass()
class RuleGroupModel:
    """read only class to hold rule group level data for simplified filters"""
    operation: GroupOperation = GroupOperation.ANY
    rules: list[RuleModel] = None


@dataclass()
class SimplifiedFilterModel:
    """read only class to hold rule groups data for simplified filters"""
    operation: GroupOperation = GroupOperation.ALL
    rule_groups: list[RuleGroupModel] = None


class SalesforceRestore:
    """Class to handle restore operations of Salesforce apps from Select Restore Type page"""

    def __init__(self, admin_console):
        """
        Constructor for this class

        Args:
            admin_console (AdminConsole): AdminConsole object

        Returns:
            None:
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = self.__admin_console.driver
        self.__drop_down = DropDown(self.__admin_console)
        self.__rdrop_down = RDropDown(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__dialog = ModalDialog(self.__admin_console)
        self.__browse = Browse(self.__admin_console)
        self.__panel = ModalPanel(self.__admin_console)
        self.restore_func = {
            RestoreTarget.SALESFORCE: self._restore_to_salesforce,
            RestoreTarget.DATABASE: self._restore_to_database,
            RestoreTarget.FILE_SYSTEM: self._restore_to_file_system
        }

    @PageService()
    def __select_restore_type(self, restore_type):
        """
        Click on restore_type on Select restore type page

        Args:
            restore_type (RestoreType): Restore type

        Returns:
            None:
        """
        self.__admin_console.click_by_xpath(f"//a[div[text()='{restore_type.value}']]")

    @PageService()
    def __select_restore_target(self, restore_target):
        """
        Selects radio button for restore target

        Args:
            restore_target (RestoreTarget):

        Returns:
            None
        """
        self.__admin_console.click_by_xpath(f"//input[@value='{restore_target.value}']")

    @PageService()
    def __select_files_for_restore(self, path=None, file_folders=None):
        """
        Selects files for restore on Browse page

        Args:
            path (str): source path to be expanded
            file_folders (list[str]): list of files/folders to pass to Browse object. (Default is None, and all files
                                        and folders in path are selected for restore)

        Returns:
            None:

        Examples:
            To select all files, don't pass either path or file_folders

            To select all files/folders in a path, simply pass the path parameter like path='/Objects/'

            To select one or more files/folders in a path, pass both path and file_folders like path='/Objects/',
            file_folders=['Account', 'Contact']
        """
        if path and file_folders:
            self.__browse.select_path_for_restore(path, file_folders)
        else:
            self.__browse.select_for_restore(all_files=True)
        self.__browse.submit_for_restore()

    @PageService()
    def __click_on_submit(self, wait=True, button_text=None):
        """
        Clicks on restore button on restore panel

        Args:
            wait (bool): if True, waits for page to load, else returns without waiting
            button_text (str): Button text for submit button (by default submits form on restore panel)

        Returns:
            None:
        """
        if not button_text:
            self.__admin_console.submit_form(wait=wait)
        else:
            self.__admin_console.click_button(button_text, wait_for_completion=wait)

    @PageService()
    def __submit_restore(self, restore_target, button_text=None):
        """
        Submits restore job and gets job id from popup

        Args:
            restore_target (RestoreTarget): salesforce, database or file_system

        Returns:
            int: Job Id
        """
        if restore_target == RestoreTarget.SALESFORCE:
            self.__click_on_submit(button_text=button_text)
            self.__panel.submit(wait_for_load=False)
        else:
            self.__click_on_submit(wait=False, button_text=button_text)
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def _restore_to_database(self, options):
        """
        Fill Salesforce restore options form for object level restore from media to database

        Args:
            options (dict): restore options for restore to db form

        Returns:
            None:

        Examples:
            options = {
                db_type (DbType): (default is DbType.POSTGRESQL),

                db_host_name (str): hostname/ip address of db server,

                db_instance (str): instance name for SQL Server,

                db_name (str): ,

                db_port (int): (default is 1433 if db_type is DbType.SQLSERVER, else 5432),

                db_user_name (str): ,

                db_password (str): ,

                restore_only_latest (bool): (default is True)
            }

        Raises:
            Exception:
                If required keys are not present in options dict,
                If test connection to database fails
        """
        self.__select_restore_target(RestoreTarget.DATABASE)
        db_type = options.pop('db_type', DbType.POSTGRESQL)
        if isinstance(db_type, DbType):
            db_type = db_type.value
        self.__drop_down.select_drop_down_values(
            drop_down_id=OLD_DATABASE_FORM['db_type'],
            values=[db_type]
        )
        for name, value in ((OLD_DATABASE_FORM[val], options[val]) for val in options if 'db_' in val):
            self.__admin_console.fill_form_by_name(name, value)
        self.__admin_console.click_button(self.__admin_console.props['label.testConnection'])
        message_text = self.__dialog.get_text()
        if message_text != self.__admin_console.props['label.testConnectionSucceeded']:
            self.__dialog.click_cancel()
            raise Exception(f'Connection to db unsuccessful with error message: {message_text}')
        self.__dialog.click_submit()
        if not options.get('restore_only_latest', True):
            self.__admin_console.checkbox_deselect('restoreCatalogDatabase')

    @PageService()
    def _restore_to_file_system(self, options):
        """
        Fill Salesforce restore options form for object level restore from media to File System

        Args:
            options (dict): restore options for restore to file system form

        Returns:
            None:

        Examples:
             restore_options = {
                destination_client (str): Destination client (Can be any access node, default is access node of
                Salesforce organization for which restore was triggered)

                destination_path (str): path to restore on client (Default is download cache path on access node),
            }
        """
        self.__select_restore_target(RestoreTarget.FILE_SYSTEM)
        if destination := options.get('destination_client', None):
            self.__admin_console.select_value_from_dropdown(DESTINATION_CLIENT, destination)
        if destination_path := options.get('destination_path', None):
            self.__admin_console.fill_form_by_name('destinationPath', destination_path)

    @PageService()
    def _restore_to_salesforce(self, options):
        """
        Fill Salesforce restore options form for object level restore from media to Salesforce

        Args:
            options (dict): restore options for restore to salesforce form, if None, defaults are used

        Returns:
            None:

        Examples:
            restore_options = {
                destination_organization (str): Destination Salesforce organization (Default is Salesforce
                organization for which restore was triggered),

                disable_triggers (bool): (default is True),

                masking_policies (list[str]): List of data masking policies to select
            }
        """
        self.__select_restore_target(RestoreTarget.SALESFORCE)
        if destination := options.get('destination_organization', None):
            self.__admin_console.select_value_from_dropdown(DESTINATION_CLIENT, destination)
            if options.get('masking_policies', None):
                self.__admin_console.checkbox_select('enable-data-masking')
                self.__drop_down.select_drop_down_values(
                    values=options['masking_policies'],
                    drop_down_id='policy-select'
                )
        if not options.get('disable_triggers', True):
            self.__admin_console.checkbox_deselect('disableTriggersAndRules')

    @PageService()
    def __select_parent_and_dependent_levels(self, parent_level=None, dependent_level=None):
        """
        Selects parent level and dependent level for restore

        Args:
            parent_level (ParentLevel): select parent objects (Default is ParentLevel.NONE)
            dependent_level (DependentLevel): select child objects (Default is DependentLevel.NONE)

        Returns:
            None:
        """
        if parent_level:
            self.__drop_down.select_drop_down_values(
                drop_down_id='cappsRestoreOptionsSF_isteven-multi-select_#4723',
                values=[parent_level.value]
            )
        if dependent_level:
            self.__drop_down.select_drop_down_values(
                drop_down_id='cappsRestoreOptionsSF_isteven-multi-select_#1456',
                values=[dependent_level.value]
            )

    @PageService(hide_args=True)
    def object_level_restore(
            self,
            path=None,
            file_folders=None,
            restore_target=RestoreTarget.SALESFORCE,
            **restore_options
    ):
        """
        Submits restore job for object level restore

        Args:
            path (str): path to pass to Browse object (Default is None and all content is selected for restore)
            file_folders (list[str]): list of files/folders to pass to Browse object. (Default is None, and all files
                                        and folders in path are selected for restore)
            restore_target (RestoreTarget): salesforce, database or file_system (default is RestoreTarget.SALESFORCE)

        Keyword Args:
            parent_level (ParentLevel): select parent objects (Default is ParentLevel.NONE)
            dependent_level (DependentLevel): select child objects (Default is DependentLevel.NONE)
            destination_organization (str): Destination Salesforce organization
                    (Default is Salesforce organization for which restore was triggered)
            disable_triggers (bool): (default is True)
            masking_policies (list[str]): List of data masking policies to select
            db_type (DbType): (default is DbType.POSTGRESQL)
            db_host_name (str): hostname/ip address of db server
            db_instance (str): instance name for SQL Server
            db_name (str):
            db_port (int): (default is 1433 if db_type is DbType.SQLSERVER, else 5432)
            db_user_name (str):
            db_password (str):
            restore_only_latest (bool): (default is True)
            destination_client (str): Destination client (Can be any access node, default is access node of Salesforce
                    organization for which restore was triggered)
            destination_path (str): path to restore on client (Default is download cache path on access node)

        Returns:
            int: job id

        Examples:
            To select all Objects and Files, don't pass either path or file_folders

            To select either all Object or all Files, simply pass the path parameter like path='/Objects/' or
            path='/Files/

            To select one or more Objects/Files, pass both path and file_folders like path='/Objects/',
            file_folders=['Account', 'Contact']

            for restore to Salesforce:

            restore_options = {
                destination_organization (str): Destination Salesforce organization (Default is Salesforce
                organization for which restore was triggered),

                disable_triggers (bool): (default is True),

                masking_policies (list[str]): List of data masking policies to select
            }

            for restore to DB:

            restore_options = {
                db_type (DbType): (default is DbType.POSTGRESQL),

                db_host_name (str): hostname/ip address of db server,

                db_instance (str): instance name for SQL Server,

                db_name (str): ,

                db_port (int): (default is 1433 if db_type is DbType.SQLSERVER, else 5432),

                db_user_name (str): ,

                db_password (str): ,

                restore_only_latest (bool): (default is True)
            }

            for restore to file system:

            restore_options = {
                destination_client (str): Destination client (Can be any access node, default is access node of
                Salesforce organization for which restore was triggered)

                destination_path (str): path to restore on client (Default is download cache path on access node),
            }
        """
        self.__select_restore_type(RestoreType.OBJECT_LEVEL)
        self.__select_files_for_restore(path, file_folders)
        self.restore_func[restore_target](restore_options)
        self.__select_parent_and_dependent_levels(
            parent_level=restore_options.get('parent_level'),
            dependent_level=restore_options.get('dependent_level')
        )
        return self.__submit_restore(restore_target)

    def metadata_restore(
            self,
            path=None,
            file_folders=None,
            restore_target=RestoreTarget.SALESFORCE,
            **restore_options
    ):
        """
        Submits restore job for Metadata restore

        Args:
            path (str): path to pass to Browse object (Default is None and all content is selected for restore)
            file_folders (list[str]): list of files/folders to pass to Browse object. (Default is None, and all files
                                        and folders in path are selected for restore)
            restore_target (RestoreTarget): salesforce, database or file_system (default is RestoreTarget.SALESFORCE)

        Returns:
            int: Job Id

        Examples:
            To select all metadata, don't pass either path or file_folders

            To select all metadata components in a folder, pass the folder path to the path parameter like
            path='/Metadata/unpackaged/objects'

            To select one or more metadata components in a folder, path the folder path to the path parameter and the
            component file names to file_folders like file_folders=['Account.object', 'Contact.object']

            for restore to Salesforce:

            restore_options = {
                destination_organization (str): Destination Salesforce organization (Default is Salesforce
                organization for which restore was triggered)
            }

            for restore to file system:

            restore_options = {
                destination_client (str): Destination client (Can be any access node, default is access node of
                Salesforce organization for which restore was triggered)

                destination_path (str): path to restore on client (Default is download cache path on access node),
            }
        """
        if restore_target == RestoreTarget.DATABASE:
            raise Exception('Metadata restore to database not supported')
        self.__select_restore_type(RestoreType.METADATA)
        self.__select_files_for_restore(path, file_folders)
        self.restore_func[restore_target](restore_options)
        return self.__submit_restore(restore_target, self.__admin_console.props['action.submitRestore'])

    @WebAction()
    def __close_alert_popup(self):
        """Checks if there is an alert and closes it"""
        if self.__admin_console.check_if_entity_exists("xpath", "//div[contains(@role, 'alert')]"):
            self.__admin_console.driver.find_element(By.XPATH,
                                                     "//div[contains(@role, 'alert')]//button[contains(@aria-label, 'close')]"
                                                     ).click()
            self.__admin_console.wait_for_completion()

    @PageService()
    def __filter_records(self, record_ids=None):
        """
        Filters records on record level restore page and sets pagination to 1000

        Args:
            record_ids (list[str]): List of record ids to select

        Returns:
            None:
        """
        if record_ids:
            self.__rtable.access_menu_from_dropdown(
                menu_id=self.__admin_console.props['label.setAdvancedFilter'],
                label=self.__admin_console.props['label.advancedFilterCleared']
            )
            record_ids = [f"'{record_id}'" for record_id in record_ids]
            self.__admin_console.fill_form_by_name('queryField', f"WHERE id IN ({','.join(record_ids)})")
            self.__admin_console.click_by_xpath(
                f"//button[div[text() = '{self.__admin_console.props['OK']}']]"
            )
            if len(record_ids) > 10:
                self.__rtable.set_pagination(1000)
        else:
            self.__rtable.set_pagination(1000)

    @PageService()
    def __select_records_for_restore(self, record_ids=None):
        """
        Selects records and clicks on restore

        Args:
            record_ids (list[str]): List of record ids to select

        Returns:
            None:
        """
        self.__filter_records(record_ids)
        self.__rtable.select_all_rows()

    @PageService()
    def get_rows_from_record_level_restore(
            self,
            sf_object,
            fields=None,
            record_ids=None,
            version=RecordLevelVersion.LATEST
    ):
        """
        Gets table data for sf_object from record level restore page. If record_ids are provided, only those records for
        which id matches are returned, otherwise first 1000 records are returned.

        Args:
            sf_object (str): Name of Salesforce object
            record_ids (list[str]): List of record ids
            version (RecordLevelVersion): Show latest/all/deleted versions (Default is latest)
            fields (list[str]): list of any additional fields to select in addition to the default ones

        Returns:
            list[dict]: list of dicts of rows
        """
        self.__select_restore_type(RestoreType.RECORD_LEVEL)
        self.__close_alert_popup()
        self.__rdrop_down.select_drop_down_values(index=0, values=[sf_object])
        self.__filter_records(record_ids)
        if version is not RecordLevelVersion.LATEST:
            self.__rtable.access_menu_from_dropdown(
                menu_id=self.__admin_console.props[version.value],
                label=self.__admin_console.props['label.showingLatestVersion']
            )
        if fields:
            self.__rtable.display_hidden_column(*fields)
        else:
            fields = self.__rtable.get_visible_column_names()
        table_data = dict()
        for field in fields:
            table_data[field] = self.__rtable.get_column_data(field)
        return [dict(zip(table_data.keys(), row_data)) for row_data in zip(*table_data.values())]

    @PageService()
    def record_level_restore(
            self,
            sf_object,
            record_ids=None,
            fields=None,
            restore_target=RestoreTarget.SALESFORCE,
            **restore_options
    ):
        """
        Submits restore job for record level restore

        Args:
            sf_object (str): Name of salesforce object to restore
            record_ids (list[str]): List of record ids to restore (if None, first 1000 records are selected)
            fields (list[str]): List of fields to select for restore (if None, all fields are selected)
            restore_target (RestoreTarget): salesforce or file_system (default is RestoreTarget.SALESFORCE)

        Keyword Args:
            parent_level (ParentLevel): select parent objects (Default is ParentLevel.NONE)
            dependent_level (DependentLevel): select child objects (Default is DependentLevel.NONE)
            destination_organization (str): Destination Salesforce organization
                    (Default is Salesforce organization for which restore was triggered)
            disable_triggers (bool): (default is True)
            masking_policies (list[str]): List of data masking policies to select
            destination_client (str): Destination client (Can be any access node, default is access node of Salesforce
                    organization for which restore was triggered)
            destination_path (str): path to restore on client (Default is download cache path on access node)

        Returns:
            int: job id

        Examples:
            for restore to Salesforce:

            restore_options = {
                destination_organization (str): Destination Salesforce organization (Default is Salesforce
                organization for which restore was triggered),

                disable_triggers (bool): (default is True),

                masking_policies (list[str]): List of data masking policies to select
            }

            for restore to file system:

            restore_options = {
                destination_client (str): Destination client (Can be any access node, default is access node of
                Salesforce organization for which restore was triggered)

                destination_path (str): path to restore on client (Default is download cache path on access node),
            }
        """
        if restore_target == RestoreTarget.FILE_SYSTEM:
            raise Exception('Record level restore to File System is not supported')
        self.__select_restore_type(RestoreType.RECORD_LEVEL)
        self.__close_alert_popup()
        self.__rdrop_down.select_drop_down_values(index=0, values=[sf_object])
        self.__select_records_for_restore(record_ids)
        self.__rtable.access_toolbar_menu(self.__admin_console.props['action.restore'])
        self.restore_func[restore_target](restore_options)
        if fields:
            self.__drop_down.select_drop_down_values(
                drop_down_id='cappsRestoreOptionsSF_isteven-multi-select_#4778',
                values=fields
            )
        self.__select_parent_and_dependent_levels(
            parent_level=restore_options.get('parent_level'),
            dependent_level=restore_options.get('dependent_level')
        )
        return self.__submit_restore(restore_target)


class RSalesforceRestore:
    """Class to handle restore operations of Salesforce apps from Select Restore Type page"""

    def __init__(self, admin_console):
        """
        Constructor for this class

        Args:
            admin_console (AdminConsole): AdminConsole object

        Returns:
            None:
        """
        self.__admin_console = admin_console
        self.__checkbox = Checkbox(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.__driver = self.__admin_console.driver
        self.__rdrop_down = RDropDown(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__rdialog = RModalDialog(self.__admin_console)
        self.__simple_filter_dialog = RModalDialog(self.__admin_console,
                                                   xpath="//a[text()='Add rule group']/ancestor::div[contains(@class,"
                                                         " 'mui-modal-dialog mui-modal-centered')]")
        self.__rconfirm_dialog = RModalDialog(self.__admin_console,
                                              title=self.__admin_console.props['title.confirmSubmit'])
        self.__rbrowse = RBrowse(self.__admin_console)
        self.__rpanel = RModalPanel(self.__admin_console)

        self.restore_func = {
            ReactRestoreTarget.SALESFORCE: self._restore_to_salesforce,
            ReactRestoreTarget.DATABASE: self._restore_to_database,
            ReactRestoreTarget.FILE_SYSTEM: self._restore_to_file_system
        }

    @PageService()
    def seed_sandbox(self, dest_org, options={}):
        """
             Fill Salesforce sandbox seed options

             Args:
                 options (dict): restore options for seeding form, if None, defaults are used

             Returns:
                 Job_id

             Examples:
                 options = {
                     disable_triggers (bool): (default is True),
                     insert_null (bool): (default is False),
                     associate_ownership: (default is True),
                     masking_policies (list[str]): List of data masking policies to select
                 }
             """

        self.__rdrop_down.select_drop_down_values(values=[dest_org], drop_down_id="destinationOrganization")
        self.__select_restore_options(options)
        return self.__submit_restore()

    @PageService()
    def __select_restore_options(self, options):
        """
                    Method to fill restore options

                    Args:
                        options (dict): restore options, if None, defaults are used

                    Returns:
                        None

                    Examples:
                        options = {
                            disable_triggers (bool): (default is True),
                            insert_null (bool): (default is False),
                            associate_ownership: (default is True),
                            masking_policies (list[str]): List of data masking policies to select
                        }
                    """
        for label, checkbox_id in [("disable_triggers", 'disableTriggers'),
                                   ("insert_null", 'insertNullValues'),
                                   ("associate_ownership",
                                    'associateOwnershipToLoggedInUser')]:
            if label in options:
                if options.get(label):
                    self.__checkbox.check(id=checkbox_id)
                else:
                    self.__checkbox.uncheck(id=checkbox_id)

        if options.get("masking_policies", False):
            self.__rdialog.enable_toggle(toggle_element_id="enableMasking")
            self.__rdrop_down.select_drop_down_values(values=options.get("masking_policies"),
                                                      drop_down_id="maskingPolicy")

    @PageService()
    def __select_restore_type(self, restore_type):
        """
        Click on restore_type on Select restore type page

        Args:
            restore_type (RestoreType): Restore type

        Returns:
            None:
        """
        self.__admin_console.click_by_xpath(f"//h2[text()='{restore_type.value}']")

    @PageService()
    def __select_restore_target(self, restore_target):
        """
        Selects radio button for restore target

        Args:
            restore_target (ReactRestoreTarget):

        Returns:
            None
        """
        try:
            self.__admin_console.click_by_xpath(f"//input[@value='{restore_target.value}']")
        except NoSuchElementException:
            if restore_target != ReactRestoreTarget.SALESFORCE:
                raise Exception(f"Restore to {restore_target.value} not available for the user")

    @PageService()
    def __select_files_for_restore(self, path=None, file_folders=None, download=False):
        """
        Selects files for restore on Browse page

        Args:
            path (str): source path to be expanded
            file_folders (list[str]): list of files/folders to pass to Browse object. (Default is None, and all files
                                        and folders in path are selected for restore)
            download (bool): flag to perform a download operation instead of restore
        Returns:
            None:

        Examples:
            To select all files, don't pass either path or file_folders

            To select all files/folders in a path, simply pass the path parameter like path='/Objects/'

            To select one or more files/folders in a path, pass both path and file_folders like path='/Objects/',
            file_folders=['Account', 'Contact']
        """
        if path and file_folders:
            self.__rbrowse.select_path_for_restore(path, file_folders)
        else:
            self.__rbrowse.select_files(all_files=True)
        if download:
            self.__rbrowse.click_download()
        else:
            self.__rbrowse.submit_for_restore()

    @PageService()
    def __submit_restore(self):
        """
        Submits restore job and gets job id from popup

        Returns:
            int: Job Id
        """
        self.__rdialog.click_submit()
        self.__rconfirm_dialog.click_submit(wait=False)
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def _restore_to_database(self, options):
        """
        Fill Salesforce restore options form for object level restore from media to database

        Args:
            options (dict): restore options for restore to db form

        Returns:
            None:

        Examples:
            options = {
                db_type (DbType): (default is DbType.POSTGRESQL),

                db_host_name (str): hostname/ip address of db server,

                db_instance (str): instance name for SQL Server,

                db_name (str): ,

                db_port (int): (default is 1433 if db_type is DbType.SQLSERVER, else 5432),

                db_user_name (str): ,

                db_password (str): ,

                restore_only_latest (bool): (default is True)
            }

        Raises:
            Exception:
                If required keys are not present in options dict,
                If test connection to database fails
        """
        self.__select_restore_target(ReactRestoreTarget.DATABASE)
        db_type = options.pop('db_type', DbType.POSTGRESQL)
        if isinstance(db_type, DbType):
            db_type = db_type.value
        self.__rdrop_down.select_drop_down_values(
            drop_down_id=DATABASE_FORM['db_type'],
            values=[db_type]
        )
        for name, value in ((DATABASE_FORM[val], options[val]) for val in options if 'db_' in val):
            self.__admin_console.fill_form_by_name(name, value)
        self.__test_connection()
        if not options.get('restore_only_latest', True):
            self.__admin_console.checkbox_deselect('restoreCatalogDatabase')

    @PageService()
    def __test_connection(self):
        """
        Method to perform test connection to DB

        Raise:
            CvWebAutomationException if test connection fails

        """
        self.__rdialog.click_button_on_dialog(text=self.__admin_console.props['label.testConnection'])
        self.__validate_test_connection()

    @WebAction()
    def __validate_test_connection(self):
        """
           Method to validate test connection status

           Raise:
               CVWebAutomationException if test connection fails

        """

        button = self.__driver.find_element(
            By.XPATH,
            f"//button[@aria-label='{self.__admin_console.props['label.testConnection']}']")
        self.__admin_console.wait_for_completion()
        if not len(button.find_elements(By.XPATH, "span")) > 1:
            raise CVWebAutomationException(
                f'Connection to db unsuccessful with error message: {self.__admin_console.get_error_message()}')

    @PageService()
    def _restore_to_file_system(self, options):
        """
        Fill Salesforce restore options form for object level restore from media to File System

        Args:
            options (dict): restore options for restore to file system form

        Returns:
            None:

        Examples:
             restore_options = {
                destination_client (str): Destination client (Can be any access node, default is access node of
                Salesforce organization for which restore was triggered)

                destination_path (str): path to restore on client (Default is download cache path on access node),
            }
        """
        self.__select_restore_target(ReactRestoreTarget.FILE_SYSTEM)
        if destination := options.get('destination_client', None):
            self.__rdrop_down.select_drop_down_values(drop_down_id=RDESTINATION_CLIENT, values=[destination])
        if destination_path := options.get('destination_path', None):
            self.__admin_console.fill_form_by_name('destinationPath', destination_path)

    @PageService()
    def _restore_to_salesforce(self, options):
        """
        Fill Salesforce restore options form for object level restore from media to Salesforce

        Args:
            options (dict): restore options for restore to salesforce form, if None, defaults are used

        Returns:
            None:

        Examples:
            restore_options = {
                destination_organization (str): Destination Salesforce organization (Default is Salesforce
                organization for which restore was triggered),

                disable_triggers (bool): (default is True),

                masking_policies (list[str]): List of data masking policies to select
            }
        """
        self.__select_restore_target(ReactRestoreTarget.SALESFORCE)
        if destination := options.get('destination_organization', None):
            self.__rdrop_down.select_drop_down_values(values=[destination], drop_down_id=RDESTINATION_CLIENT)
            if options.get('masking_policies', None):
                time.sleep(5)
                self.__rdialog.enable_toggle(toggle_element_id="enableMasking")
                self.__rdrop_down.select_drop_down_values(values=options.get("masking_policies"),
                                                          drop_down_id="maskingPolicy")
        if not options.get('disable_triggers', True):
            self.__checkbox.uncheck(id='disableTriggers')

        if options.get('field_filters', False):
            self.__checkbox.check(id="advancedQuery")
            self.apply_simplified_filter(options.get('field_filters'))
            self.save_simplified_filters()

        if options.get('field_mapping', False):
            time.sleep(5)
            self.__rdrop_down.select_drop_down_values(
                drop_down_id='fieldMappingType',
                values=[options['field_mapping'].value if isinstance(options['field_mapping'], FieldMapping)
                        else options['field_mapping']])

    @PageService()
    def __select_parent_and_dependent_levels(self, parent_level=ParentLevel.ALL, dependent_level=DependentLevel.NONE):
        """
        Selects parent level and dependent level for restore

        Args:
            parent_level (ParentLevel): select parent objects (Default is ParentLevel.ALL)
            dependent_level (DependentLevel): select child objects (Default is DependentLevel.NONE)

        Returns:
            None:
        """
        if parent_level:
            self.__rdrop_down.select_drop_down_values(
                drop_down_id='restoreParentType',
                values=[parent_level.value]
            )
        if dependent_level:
            self.__rdrop_down.select_drop_down_values(
                drop_down_id='dependentRestoreLevel',
                values=[dependent_level.value]
            )

    @PageService(hide_args=True)
    def object_level_restore(
            self,
            path=None,
            file_folders=None,
            restore_target=ReactRestoreTarget.SALESFORCE,
            **restore_options
    ):
        """
        Submits restore job for object level restore

        Args:
            path (str): path to pass to Browse object (Default is None and all content is selected for restore)
            file_folders (list[str]): list of files/folders to pass to Browse object. (Default is None, and all files
                                        and folders in path are selected for restore)
            restore_target (ReactRestoreTarget): salesforce, database or file_system (default is ReactRestoreTarget.SALESFORCE)

        Keyword Args:
            parent_level (ParentLevel): select parent objects (Default is ParentLevel.NONE)
            dependent_level (DependentLevel): select child objects (Default is DependentLevel.NONE)
            destination_organization (str): Destination Salesforce organization
                    (Default is Salesforce organization for which restore was triggered)
            disable_triggers (bool): (default is True)
            masking_policies (list[str]): List of data masking policies to select
            db_type (DbType): (default is DbType.POSTGRESQL)
            db_host_name (str): hostname/ip address of db server
            db_instance (str): instance name for SQL Server
            db_name (str):
            db_port (int): (default is 1433 if db_type is DbType.SQLSERVER, else 5432)
            db_user_name (str):
            db_password (str):
            restore_only_latest (bool): (default is True)
            destination_client (str): Destination client (Can be any access node, default is access node of Salesforce
                    organization for which restore was triggered)
            destination_path (str): path to restore on client (Default is download cache path on access node)

        Returns:
            int: job id

        Examples:
            To select all Objects and Files, don't pass either path or file_folders

            To select either all Object or all Files, simply pass the path parameter like path='/Objects/' or
            path='/Files/

            To select one or more Objects/Files, pass both path and file_folders like path='/Objects/',
            file_folders=['Account', 'Contact']

            for restore to Salesforce:

            restore_options = {
                destination_organization (str): Destination Salesforce organization (Default is Salesforce
                organization for which restore was triggered),

                disable_triggers (bool): (default is True),

                masking_policies (list[str]): List of data masking policies to select
            }

            for restore to DB:

            restore_options = {
                db_type (DbType): (default is DbType.POSTGRESQL),

                db_host_name (str): hostname/ip address of db server,

                db_instance (str): instance name for SQL Server,

                db_name (str): ,

                db_port (int): (default is 1433 if db_type is DbType.SQLSERVER, else 5432),

                db_user_name (str): ,

                db_password (str): ,

                restore_only_latest (bool): (default is True)
            }

            for restore to file system:

            restore_options = {
                destination_client (str): Destination client (Can be any access node, default is access node of
                Salesforce organization for which restore was triggered)

                destination_path (str): path to restore on client (Default is download cache path on access node),
            }
        """
        self.__select_restore_type(RestoreType.OBJECT_LEVEL)
        if restore_options.get('download', False):
            self.__select_files_for_restore(path, file_folders, download=True)
            return
        self.__select_files_for_restore(path, file_folders)
        self.restore_func[restore_target](restore_options)
        self.__select_parent_and_dependent_levels(
            parent_level=restore_options.get('parent_level'),
            dependent_level=restore_options.get('dependent_level')
        )
        return self.__submit_restore()

    def metadata_restore(
            self,
            path=None,
            file_folders=None,
            restore_target=ReactRestoreTarget.SALESFORCE,
            **restore_options
    ):
        """
        Submits restore job for Metadata restore

        Args:
            path (str): path to pass to Browse object (Default is None and all content is selected for restore)
            file_folders (list[str]): list of files/folders to pass to Browse object. (Default is None, and all files
                                        and folders in path are selected for restore)
            restore_target (ReactRestoreTarget): salesforce, database or file_system (default is ReactRestoreTarget.SALESFORCE)

        Returns:
            int: Job Id

        Examples:
            To select all metadata, don't pass either path or file_folders

            To select all metadata components in a folder, pass the folder path to the path parameter like
            path='/Metadata/unpackaged/objects'

            To select one or more metadata components in a folder, path the folder path to the path parameter and the
            component file names to file_folders like file_folders=['Account.object', 'Contact.object']

            for restore to Salesforce:

            restore_options = {
                destination_organization (str): Destination Salesforce organization (Default is Salesforce
                organization for which restore was triggered)
            }

            for restore to file system:

            restore_options = {
                destination_client (str): Destination client (Can be any access node, default is access node of
                Salesforce organization for which restore was triggered)

                destination_path (str): path to restore on client (Default is download cache path on access node),
            }
        """
        if restore_target == ReactRestoreTarget.DATABASE:
            raise Exception('Metadata restore to database not supported')
        self.__select_restore_type(RestoreType.METADATA)
        if restore_options.get('download', False):
            self.__select_files_for_restore(path, file_folders, download=True)
            return
        self.__select_files_for_restore(path, file_folders)
        self.restore_func[restore_target](restore_options)
        return self.__submit_restore()

    @WebAction()
    def __close_alert_popup(self):
        """Checks if there is an alert and closes it"""
        if self.__admin_console.check_if_entity_exists("xpath", "//div[contains(@class, 'toaster-icon')]"):
            self.__admin_console.driver.find_element(By.XPATH,
                                                     "//div[contains(@class, 'toaster-icon')]//button[contains(@class, "
                                                     "'close')] "
                                                     ).click()
            self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_to_add_rule(self, group_number):
        """
        Method to click on Add rule option

        Args:
            group_number (int): Index of the rule group

        Returns:

        """
        self.__admin_console.click_by_xpath(
            f"//div[@id='ruleGroupsList.{group_number}.value.op']"
            f"/ancestor::div[contains(@class,'rule-group-separator')]//a[text()='Add rule']")

    @WebAction()
    def __save_rule(self, group_number, rule_number):
        """
        Method to click tick mark and save rule

        Args:
            group_number (int): Index of the rule group
            rule_number (int): Index of the rule


        Returns:

        """
        self.__driver.find_element(By.XPATH,
                                   f"//button[@id='ruleGroupsList.{group_number}.value.rules.{rule_number}"
                                   f".value-save-button']").click()

    @PageService()
    def __fill_rule_values(self, group_number, rule_number, column, value, operation):
        """
        Method to fill rule values

        Args:
           group_number (int): Index of the rule group
           rule_number (int): Index of the rule
           column (str): Column name for applying filter
           value (str): Value for the column
           operation (ColumnOperation): Operation for the filter

        Returns:

        """
        self.__rdrop_down.wait_for_dropdown_load(
            f"ruleGroupsList.{group_number}.value.rules.{rule_number}.value.column")
        self.__rdrop_down.select_drop_down_values(
            drop_down_id=f"ruleGroupsList.{group_number}.value.rules.{rule_number}.value.column", values=[column])
        self.__rdrop_down.select_drop_down_values(
            drop_down_id=f"ruleGroupsList.{group_number}.value.rules.{rule_number}.value.operation",
            values=[operation.value])
        self.__simple_filter_dialog.fill_text_in_field(
            f"ruleGroupsList.{group_number}.value.rules.{rule_number}.value.parameter", value)
        self.__save_rule(group_number, rule_number)

    @PageService()
    def __add_rule(self, group_number, rule_number, column, value, operation=ColumnOperation.CONTAINS):
        """
        Method to add rule

        Args:
           group_number (int): Index of the rule group
           rule_number (int): Index of the rule
           column (str): Column for applying filter
           value (str): Value for the column
           operation (ColumnOperation): Operation for the filter

        Returns:
           None:
        """
        if not self.__admin_console.check_if_entity_exists("id",
                                                           f"ruleGroupsList.{group_number}.value.rules"
                                                           f".{rule_number}.value-save-button"):
            self.__click_to_add_rule(group_number)
        self.__fill_rule_values(group_number, rule_number, column, value, operation)

    @PageService()
    def __change_group_operation(self, group_number, operation):
        """
        Method to change group level operation

        Args:
           group_number (int): Index of the group
           operation (GroupOperation): Operation for that group

        Returns:
           None:
        """
        self.__rdrop_down.select_drop_down_values(drop_down_id=f"ruleGroupsList.{group_number}.value.op",
                                                  values=[operation.value])

    @PageService()
    def __change_overall_operation(self, operation):
        """
        Method to change operation b/w rule groups

        Args:
          operation (GroupOperation): Operation b/w rule groups

        Returns:
          None:
        """
        self.__rdrop_down.select_drop_down_values(drop_down_id="ruleGroupsOp",
                                                  values=[operation.value])

    @PageService()
    def apply_simplified_filter(self, model: SimplifiedFilterModel):
        """
        Method to apply simplified filter values

        Args:
           model (SimplifiedFilterModel): Object having simplified filter data

        Returns:
           None:
        """
        for group_idx, rule_group in enumerate(model.rule_groups):
            self.__add_rule_group(group_idx)
            for rule_idx, rule in enumerate(rule_group.rules):
                self.__add_rule(group_idx, rule_idx, rule.column, rule.value, rule.filter)
            self.__change_group_operation(group_idx, rule_group.operation)
        self.__change_overall_operation(model.operation)

    @PageService()
    def save_simplified_filters(self):
        """Method to save the simplified filter"""
        self.__simple_filter_dialog.click_button_on_dialog(self.__admin_console.props["label.ok"])

    @PageService()
    def __add_rule_group(self, group_number):
        """
        Method to click on Add rule group option

        Args:
           group_number (int): Index of the group

        Returns:
           None:
        """
        if not self.__admin_console.check_if_entity_exists("id", f"ruleGroupsList.{group_number}.value.op"):
            self.__simple_filter_dialog.select_link_on_dialog(text=self.__admin_console.props["label.addRuleGroup"])

    @PageService()
    def __clear_simplified_filter(self):
        """
        Method to clear simplified filters

        """
        self.__rtable.access_menu_from_dropdown(
            menu_id=self.__admin_console.props["label.clearAdvancedFilter"],
            label=self.__admin_console.props['label.advancedFilterCleared']
        )

    @PageService()
    def __filter_records(self, record_ids=None):
        """
        Filters records on record level restore page and sets pagination to 1000

        Args:
            record_ids (list[str]): List of record ids to select

        Returns:
            None:
        """
        if record_ids:
            self.__rtable.access_menu_from_dropdown(
                menu_id=self.__admin_console.props["label.setAdvancedFilter"],
                label=self.__admin_console.props['label.advancedFilterCleared']
            )
            simplified_model = SimplifiedFilterModel(rule_groups=[RuleGroupModel(operation=GroupOperation.ANY,
                                                                                 rules=[RuleModel(
                                                                                     column="Id",
                                                                                     value=record_id,
                                                                                     filter=ColumnOperation.EQUALS_TO)
                                                                                     for record_id in record_ids])])

            self.apply_simplified_filter(simplified_model)
            self.save_simplified_filters()
            if len(record_ids) > 10:
                self.__rtable.set_pagination(1000)
        else:
            self.__rtable.set_pagination(1000)

    @PageService()
    def __select_records_for_restore(self, record_ids=None):
        """
        Selects records and clicks on restore

        Args:
            record_ids (list[str]): List of record ids to select

        Returns:
            None:
        """
        self.__filter_records(record_ids)
        self.__rtable.select_all_rows()

    @PageService()
    def get_rows_from_record_level_restore(
            self,
            sf_object,
            fields=None,
            record_ids=None,
            version=RecordLevelVersion.LATEST
    ):
        """
        Gets table data for sf_object from record level restore page. If record_ids are provided, only those records for
        which id matches are returned, otherwise first 1000 records are returned.

        Args:
            sf_object (str): Name of Salesforce object
            record_ids (list[str]): List of record ids
            version (RecordLevelVersion): Show latest/all/deleted versions (Default is latest)
            fields (list[str]): list of any additional fields to select in addition to the default ones

        Returns:
            list[dict]: list of dicts of rows
        """
        self.__select_restore_type(RestoreType.RECORD_LEVEL)
        self.__close_alert_popup()
        self.__rdrop_down.select_drop_down_values(drop_down_id="objectSelector", values=[sf_object])
        self.__filter_records(record_ids)
        if version is not RecordLevelVersion.LATEST:
            self.__rtable.access_menu_from_dropdown(
                menu_id=self.__admin_console.props[version.value],
                label=self.__admin_console.props['label.showingLatestVersion']
            )
        if fields:
            self.__rtable.display_hidden_column(fields)
        else:
            fields = self.__rtable.get_visible_column_names()
        table_data = dict()
        for field in fields:
            table_data[field] = self.__rtable.get_column_data(field)
        return [dict(zip(table_data.keys(), row_data)) for row_data in zip(*table_data.values())]

    @PageService()
    def record_level_restore(
            self,
            sf_object,
            record_ids=None,
            fields=None,
            restore_target=ReactRestoreTarget.SALESFORCE,
            **restore_options
    ):
        """
        Submits restore job for record level restore

        Args:
            sf_object (str): Name of salesforce object to restore
            record_ids (list[str]): List of record ids to restore (if None, first 1000 records are selected)
            fields (list[str]): List of fields to select for restore (if None, all fields are selected)
            restore_target (ReactRestoreTarget): salesforce or file_system (default is ReactRestoreTarget.SALESFORCE)

        Keyword Args:
            parent_level (ParentLevel): select parent objects (Default is ParentLevel.NONE)
            dependent_level (DependentLevel): select child objects (Default is DependentLevel.NONE)
            destination_organization (str): Destination Salesforce organization
                    (Default is Salesforce organization for which restore was triggered)
            disable_triggers (bool): (default is True)
            masking_policies (list[str]): List of data masking policies to select
            destination_client (str): Destination client (Can be any access node, default is access node of Salesforce
                    organization for which restore was triggered)
            destination_path (str): path to restore on client (Default is download cache path on access node)

        Returns:
            int: job id

        Examples:
            for restore to Salesforce:

            restore_options = {
                destination_organization (str): Destination Salesforce organization (Default is Salesforce
                organization for which restore was triggered),

                disable_triggers (bool): (default is True),

                masking_policies (list[str]): List of data masking policies to select
            }

            for restore to file system:

            restore_options = {
                destination_client (str): Destination client (Can be any access node, default is access node of
                Salesforce organization for which restore was triggered)

                destination_path (str): path to restore on client (Default is download cache path on access node),
            }
        """
        if restore_target == ReactRestoreTarget.FILE_SYSTEM:
            raise Exception('Record level restore to File System is not supported')
        self.__select_restore_type(RestoreType.RECORD_LEVEL)
        self.__close_alert_popup()
        self.__rdrop_down.select_drop_down_values(drop_down_id="objectSelector", values=[sf_object])
        self.__select_records_for_restore(record_ids)
        self.__rtable.access_toolbar_menu(self.__admin_console.props['action.restore'])
        self.restore_func[restore_target](restore_options)
        if fields:
            self.__rdrop_down.select_drop_down_values(
                drop_down_id='fields',
                values=fields
            )
        self.__select_parent_and_dependent_levels(
            parent_level=restore_options.get('parent_level'),
            dependent_level=restore_options.get('dependent_level')
        )
        return self.__submit_restore()

