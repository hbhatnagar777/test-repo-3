# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for all the constants of Office 365 Web Automation
"""

from enum import Enum


class OneDrive(Enum):
    """
    Enum class for declaring all constants of OneDrive
    """
    OVERVIEW_TAB = "Overview"
    ACCOUNT_TAB = 'Users'
    CONTENT_TAB = 'Content'
    EMAIL_ADDRESS_TAB = 'Email address'
    ADD_BUTTON_ID = 'ID_USER'
    ADD_USER_BUTTON_ID = 'ADD_USER'
    ADD_USER_CARD_TEXT = 'Users'
    ADD_GROUP_CARD_TEXT = 'AD groups'
    REACT_BROWSE_RESTORE_XPATH = "//li[text()='Restore files']"
    LAST_DISCOVERY_CACHE_UPDATE_TIME = "//span[@data-ng-bind='addOffice365OneDriveAssociationCtrl.lastDiscoverCacheUpdateTime']"
    O365_PLAN_DROPDOWN_ID = 'office365OneDriveAddAssociation_isteven-multi-select_#5444'
    O365_PLAN_DROPDOWN_ID_REACT = 'cloudAppsPlansDropdown'
    BACKUP_MENU_ID = 'BACKUP_GRID'
    CHANGE_OFFICE365_PLAN_ID_REACT = 'Change plan'
    USER_CHANGE_OFFICE365_PLAN_ID = 'office365OneDriveUsersTable_actionContextMenu_CHANGE_PLAN'
    GROUP_CHANGE_OFFICE365_PLAN_ID = 'office365OneDriveContentTable_actionContextMenu_CHANGE_PLAN'
    CLICK_MORE_ID = "analytics-content-association-action-more"
    CLICK_CI_ID = "CONTENT_INDEXING"
    CLICK_RESTORE_ID = 'RESTORE_OPTIONS'
    ACCOUNT_RESTORE_XPATH = '//li[@id="batch-action-menu_RESTORE"]//a[@id="RESTORE"]'
    BROWSE_RESTORE_XPATH = '//li[@id="batch-action-menu_BROWSE"]//a[@id="BROWSE"]'
    EMAIL_ADDRESS_COLUMN_ID = 'cv-k-grid-td-URL'
    CONTENT_STATUS_COLUMN_ID = 'cv-k-grid-td-GROUP_STATUS'
    USERS_STATUS_COLUMN_ID = 'cv-k-grid-td-ACCOUNT_STATUS'
    MANAGE_ID_REACT = 'Manage'
    ENABLE_TEXT_REACT = 'Include in backup'
    DISABLE_TEXT_REACT = 'Exclude from backup'
    REMOVE_TEXT_REACT = 'Remove from content'
    DELETE_TEXT_REACT = 'Delete backup data'
    USERS_MANAGE_ID = 'office365OneDriveUsersTable_actionContextMenu_MANAGE'
    USERS_DELETE_ID = 'office365OneDriveUsersTable_actionContextMenu_REMOVE'
    USERS_DISABLE_ID = 'office365OneDriveUsersTable_actionContextMenu_DISABLE'
    USERS_ENABLE_ID = 'office365OneDriveUsersTable_actionContextMenu_ENABLE'
    GROUP_MANAGE_ID = 'office365OneDriveContentTable_actionContextMenu_MANAGE'
    GROUP_DELETE_ID = 'office365OneDriveContentTable_actionContextMenu_REMOVE'
    GROUP_DISABLE_ID = 'office365OneDriveContentTable_actionContextMenu_DISABLE'
    GROUP_ENABLE_ID = 'office365OneDriveContentTable_actionContextMenu_ENABLE'
    ACTIVE_BROWSE_TREE_ID = 'oneDriveBrowseTree_tv_active'
    BROWSE_TREE_ID = 'oneDriveBrowseTree'

    DISCOVER_PROCESS_NAME = 'cvclouddiscoverv2'
    MAX_STREAMS_COUNT = '10'
    INITIAL_DOC_COUNT = 5
    DOC_COUNT_FULL_BKP_JOB = 15
    DOC_COUNT_INCR_BKP_JOB = 5
    PIT_RESTORE_FOLDER_COUNT = 2  # User, My Drive and AutomationFolder
                                  # (Value is 2 for restore to disk)
    FILTERS_RESTORE_FOLDER_COUNT = 2  # User and My Drive
    REFRESH_CACHE_USER_COUNT = 6
    SERVER_PLAN_NAME = 'Automation_ServerPlan_'
    STORAGE_DICT = {'pri_storage': ''}
    RPO_DICT = {'StartTime': ''}

    RADIO_BUTTON_OVERWRITE = 'UNCONDITIONALLY_OVERWRITE'


class ExchangeOnline(Enum):
    """
    Enum class for declaring all constants on Exchange Online
    """
    OVERVIEW_TAB = "Overview"
    ACCOUNT_TAB = 'Mailboxes'
    CONTENT_TAB = 'Content'
    REPORTS_TAB= 'Reports'
    ADD_USER_CARD_TEXT = 'Mailboxes'
    EMAIL_ADDRESS_TAB = 'Email address'
    ADD_BUTTON_ID = 'addMailbox'
    ADD_USER_BUTTON_ID = 'undefined'
    LAST_DISCOVERY_CACHE_UPDATE_TIME = "//span[@data-ng-bind='createMbNewAssociationCtrl.lastDiscoverCacheUpdateTime']"
    O365_PLAN_DROPDOWN_ID = 'exchangePlan_isteven-multi-select_#2'
    BACKUP_MENU_ID = 'ARCHIVE_GRID'
    METALLIC_BACKUP_MENU_ID = 'archive'
    USER_CHANGE_OFFICE365_PLAN_ID = 'exchangeMBListTable_actionContextMenu_ADD_PLAN'
    GROUP_CHANGE_OFFICE365_PLAN_ID = 'exchangeMBListTable_actionContextMenu_ADD_PLAN'
    CLICK_RESTORE_ID = 'RESTORE'
    ACCOUNT_RESTORE_XPATH = '//li[@id="batch-action-menu_RESTORE_MAILBOX"]//a[@id="RESTORE_MAILBOX"]'
    ACCOUNT_RECOVERY_XPATH = '//li[@id="batch-action-menu_BROWSE_RECOVERY_POINT"]//a[@id="BROWSE_RECOVERY_POINT"]'
    MAILBOX_RESTORE_XPATH = '//li[@id="toolbar-menu_RESTORE"]//a[@id="RESTORE_MAILBOX"]'
    BROWSE_RESTORE_XPATH = '//li[@id="batch-action-menu_BROWSE"]//a[@id="BROWSE"]'
    ADD_MENU_ID = 'addAutoDiscover'
    MAX_STREAMS_COUNT = '10'
    EMAIL_ADDRESS_COLUMN_ID = 'cv-k-grid-td-EMAIL_ADDRESS'
    CONTENT_STATUS_COLUMN_ID = 'cv-k-grid-td-EMAIL_STATUS'
    USERS_STATUS_COLUMN_ID = 'cv-k-grid-td-EMAIL_STATUS'
    CREATE_OFFICE365_PLAN_BUTTON_ID = 'createOffice365Plan_button_#0103'
    USERS_MANAGE_ID = "exchangeMBListTable_actionContextMenu_MANAGE"
    USERS_DELETE_ID = "exchangeMBListTable_actionContextMenu_DELETE"
    USERS_DISABLE_ID = "exchangeMBListTable_actionContextMenu_DISABLE"
    USERS_ENABLE_ID = "//li[@id='exchangeMBListTable_actionContextMenu_ENABLE']//a[@id='ENABLE']"
    GROUP_MANAGE_ID = "//li[@id='exchangeMBListTable_actionContextMenu_MANAGE']"
    GROUP_DELETE_ID = "//li[@id='exchangeMBListTable_actionContextMenu_DELETE']//a[@id='DELETE']"
    GROUP_DISABLE_ID = "//li[@id='exchangeMBListTable_actionContextMenu_DISABLE']//a[@id='DISABLE']"
    GROUP_ENABLE_ID = "//li[@id='exchangeMBListTable_actionContextMenu_ENABLE']//a[@id='ENABLE']"
    RESTORE_PAGE_OPTION = 'APP_LEVEL_RESTORE'
    RADIO_BUTTON_OVERWRITE = 'UNCONDITIONALLY_OVERWRITE'
    CAB_TYPE = "CAB"
    PST_TYPE = "PST"
    MSG_FORMAT = "MSG"
    EML_FORMAT = "EML"
    CONFIGURATION = 'Configuration'
    DISCOVERY_TYPE="Discovery type"


class SharePointOnline(Enum):
    """
    Enum class for declaring all constants on SharePoint Online Pseudo Client
    """
    MAX_STREAMS_COUNT = '10'
    OVERVIEW_TAB = "Overview"
    CONTENT_TAB = 'Content'
    ACCOUNT_TAB = 'Sites'
    EMAIL_ADDRESS_TAB = 'Email address'
    SERVER_PLAN_NAME = 'SharePoint_V2_Automation_ServerPlan_'
    STORAGE_DICT = {'pri_storage': '',
                    'pri_ret_period': '1',
                    'ret_unit': 'Month(s)'}
    RPO_DICT = {'hours': '',
                'minutes': '',
                'am_or_pm': ''}
    ADD_BUTTON_ID = 'ADD_CONTENT'
    ADD_USER_BUTTON_ID = 'ADD_CONTENT'
    ADD_USER_CARD_TEXT = 'Sites'
    LAST_DISCOVERY_CACHE_UPDATE_TIME = "//span[@data-ng-bind='o365spReAssociateWebCtrl.lastDiscoverCacheUpdateTime']"
    AUTO_ASSOCIATION_GROUP_IDS = {
        "All Web Sites": 'ASSOCIATE_AUTO_DISCOVERED_ALL_SHAREPOINT_WEB_SITES',
        "All Teams Sites": 'ASSOCIATE_AUTO_DISCOVERED_SHAREPOINT_TEAM_SITES',
        "All Project Online Sites": 'ASSOCIATE_AUTO_DISCOVERED_PROJECT_ONLINE_SITES'
    }
    CREATE_OFFICE365_PLAN_BUTTON_ID = 'createOffice365Plan_button_#0103'
    O365_PLAN_DROPDOWN_ID = 'o365spReAssociateWebAssociation_isteven-select_#1'
    O365_PLAN_EDIT_DROPDOWN_ID = 'o365spEditAssociationCtrl_isteven-select_#1'
    O365_PLAN_RETENTION_DAYS_DROPDOWN_ID = 'cvTimeRelativePicker_isteven-multi-select_#6209'
    O365_PLAN_SELECT_RETENTION_DAYS_XPATH = "//*[@class='checkBoxContainer']//span[contains(text(),'{0}')]"
    BACKUP_MENU_ID = 'BackupWeb'
    BACKUP_MENU_ID_REACT = 'Backup'
    USER_CHANGE_OFFICE365_PLAN_ID = 'o365spWebsListTable_actionContextMenu_CHANGEPLAN'
    GROUP_CHANGE_OFFICE365_PLAN_ID = 'o365spAutoDiscoverListTable_actionContextMenu_CHANGEPLAN'
    CLICK_RESTORE_ID = 'RestoreWebs'
    REACT_RESTORE_XPATH = "//span[contains(@class, 'anaytics-content-association-action-restore-main-option')]"
    ACCOUNT_RESTORE_XPATH = '//li[@id="batch-action-menu_RESTORE_WEB_SITE"]//a[@id="RESTORE_WEB_SITE"]'
    ACCOUNT_RESTORE_REACT_XPATH = "//li[@role='menuitem' and contains(text(), 'Restore sites')]"
    BROWSE_RESTORE_XPATH = '//li[@id="batch-action-menu_RESTORE_WEB_DOC"]//a[@id="RESTORE_WEB_DOC"]'
    REACT_BROWSE_RESTORE_XPATH = "//li[@id='BROWSE']"
    RESTORE_SKIP_OPTION = 'whenDocExistsSkip'
    RESTORE_UNCONDITIONAL_OVERWRITE_OPTION = 'whenDocExistsOverwrite'
    EMAIL_ADDRESS_COLUMN_ID = 'cv-k-grid-td-URL'
    CONTENT_STATUS_COLUMN_ID = 'cv-k-grid-td-ACCOUNT_STATUS'
    USERS_STATUS_COLUMN_ID = 'cv-k-grid-td-ACCOUNT_STATUS'
    USERS_MANAGE_ID = 'o365spWebsListTable_actionContextMenu_MANAGE'
    USERS_DELETE_ID = 'o365spWebsListTable_actionContextMenu_RemoveWebs'
    USERS_DISABLE_ID = 'o365spWebsListTable_actionContextMenu_DONOTBACKUP'
    USERS_ENABLE_ID = 'o365spWebsListTable_actionContextMenu_ENABLE'
    GROUP_MANAGE_ID = 'o365spAutoDiscoverListTable_actionContextMenu_MANAGE'
    GROUP_DELETE_ID = 'o365spAutoDiscoverListTable_actionContextMenu_DELETE_AUTO_DISCOVER'
    GROUP_DISABLE_ID = 'o365spAutoDiscoverListTable_actionContextMenu_DONOTBACKUP'
    GROUP_ENABLE_ID = 'o365spAutoDiscoverListTable_actionContextMenu_ENABLE'
    ACTIVE_BROWSE_TREE_XPATH = ("//li[@role='treeitem' and @aria-expanded='true']"
                                "//span[contains(@class, 'text-content')]")
    BROWSE_TREE_XPATH = "//li[@role='treeitem']//span[contains(@class, 'text-content')]"
    RADIO_BUTTON_OVERWRITE = 'OVERWRITE'
    RADIO_BUTTON_OUTOFPLACE = 'OUTOFPLACE'
    MANAGE_ID_REACT = 'Manage'
    CHANGE_OFFICE365_PLAN_ID_REACT = 'Change plan'
    O365_PLAN_DROPDOWN_ID_REACT = 'cloudAppsPlansDropdown'


class Teams(Enum):
    OVERVIEW_TAB = "Overview"
    ACCOUNT_TAB = 'Teams'
    CONTENT_TAB = 'Content'
    EMAIL_ADDRESS_TAB = 'Email address'
    ADD_BUTTON_ID = 'ID_USER'
    ADD_USER_BUTTON_ID = 'ADD_USER'
    LAST_DISCOVERY_CACHE_UPDATE_TIME = "//span[@data-ng-bind='addAssociationsCtrl.lastDiscoverCacheUpdateTime']"
    O365_PLAN_DROPDOWN_ID = 'office365OneDriveAddAssociation_isteven-multi-select_#5444'
    BACKUP_MENU_ID = 'BACKUP_GRID'
    CLICK_RESTORE_ID = 'RESTORE_OPTIONS'
    ACCOUNT_RESTORE_XPATH = '//li[@id="batch-action-menu_RESTORE"]//a[@id="RESTORE"]'
    RADIO_BUTTON_OVERWRITE = 'UNCONDITIONALLY_OVERWRITE'
    RESTORE_PAGE_OPTION = 'APP_LEVEL_RESTORE'


class StatusTypes(Enum):
    DELETED = 'Deleted from content'
    DISABLED = 'Excluded from backup'
    ACTIVE = 'Included in backup'
    REMOVED = 'Removed'


class RestoreType(Enum):
    TO_DISK = 'Restore to Disk'
    IN_PLACE = 'Restore to original location'
    OOP = 'Restore to different OneDrive account'


class RestoreOptions(Enum):
    SKIP = 'SKIP'
    COPY = 'RESTORE_AS_COPY'
    OVERWRITE = 'UNCONDITIONALLY_OVERWRITE'


class O365PlanFilterType(Enum):
    INCLUDE = 'Include Files/Folders'
    EXCLUDE = 'Exclude Files/Folders'


class O365AppTabs(Enum):
    Overview = 'Overview'
    Configuration = 'Configuration'
    Reports = 'Reports'
    Content = 'Content'
    Monitoring = 'Monitoring'
    Teams = 'Teams'
    Mailbox = 'Mailboxes'
    Users = 'Users'
    Sites = 'Sites'


class O365Region(Enum):
    Default = 1
    Germany = 2
    China = 3
    US_GCC = 4
    US_GCC_HIGH = 5
    US_DOD = 6
    EAST_US_2 = "(US) East US 2"
    PLAN_EASTUS2 = 'o365-storage-eastus2'

class ClientRestoreType(Enum):
    Restore_Messages = "Restore messages"
    Restore_Mailboxes = "Restore mailboxes"
    Restore_Mailboxes_AD_Group = "Restore mailboxes by AD group"
    Restore_Files = "Restore files"
    Restore_Users = "Restore users"
    Restore_Users_AD_Group = "Restore users by AD group"
