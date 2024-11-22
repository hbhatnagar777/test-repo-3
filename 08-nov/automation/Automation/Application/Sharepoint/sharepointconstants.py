# -*- coding: utf-8 -*-
#
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
#

"""Helper file for maintaining Sharepoint Automation Constants.

Any constant values related to Sharepoint Automation goes in this file.


"""

import os
from enum import Enum

# dict for sharepoint subclient properties
SP_SUBCLIENT_PROP_DICT = {
    "ContentDatabasenumStreams": 2,
    "ContentDatabaseVDITimeout": 300
}

SP_SUBCLIENT_STORAGE_DICT = {
    "networkAgents": 2,
}

# sharepoint strings
CONTENT_WEBAPP = '\\MB\\Farm\\Microsoft SharePoint Foundation Web Application\\{0}'
CONTENT_DB = '\\MB\\Farm\\Microsoft SharePoint Foundation Web Application\\{0}\\{1}'
WEBAPP_URL = 'http://{0}:{1}/'
DB_NAME = 'WSS_Content_{0}'
APP_POOL = 'SharePoint - {0}'
SUBCLIENT_NAME = 'Subclient{0}_{1}'
METADATA_BEFORE_FULL = "before_backup_full.txt"
METADATA_AFTER_RESTORE = "after_restore.txt"
TEST_FILE_DIR = r"C:\AutomationTesting\DOCS"

# paths for powershell scripts
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "Scripts")
CHECK_FILE = os.path.join(SCRIPT_PATH, 'check_file.ps1')
UPLOAD_FILE = os.path.join(SCRIPT_PATH, 'upload_file.ps1')
CREATE_LIST = os.path.join(SCRIPT_PATH, 'create_list.ps1')
CREATE_SITES = os.path.join(SCRIPT_PATH, 'create_sites.ps1')
CREATE_WEBAPP = os.path.join(SCRIPT_PATH, 'create_webapp.ps1')
DELETE_WEBAPP = os.path.join(SCRIPT_PATH, 'delete_webapp.ps1')
CREATE_META_DB = os.path.join(SCRIPT_PATH, 'create_meta_info_db.ps1')
GET_TEAMS_SITES = os.path.join(SCRIPT_PATH, 'GetAll-TeamsSites.ps1')
CREATE_SITE_COLLECTION = os.path.join(SCRIPT_PATH, 'Create-SiteCollection.ps1')
DELETE_SITE_COLLECTION = os.path.join(SCRIPT_PATH, 'Delete-SiteCollection.ps1')
DELETE_CONNECTED_GROUP = os.path.join(SCRIPT_PATH, 'Delete-ConnectedGroup.ps1')

AGENT_NAME = "Sharepoint Server"
BACKUPSET_NAME = "Sharepoint Online"
SUBCLIENT_NAME = "SharepointOnline"
INSTANCE_NAME = "defaultInstance"
MANUAL_DISCOVERY_PROCESS_NAME = 'CVSPAutoDiscoverScan'
MOV_DIR_PROCESS_NAME = 'moveDir'

ITEM_TYPE = {
    'site collections': 2,
    'web': 1
}

CSDB_QUERY = {
    'site collection count': "select count(*) from APP_CloudAppUserDetails where subClientId= {0} and modified =0 "
                             "and discoverByType =6 and itemtype ={1}",
    'site collection properties': "select displayName, smtpAddress from APP_CloudAppUserDetails where subClientId= {0}"
                                  " and modified =0 and discoverByType =6 and "
                                  "itemtype ={1} and smtpAddress like N'{2}'",
    'web properties': "select  displayName, smtpAddress, itemType, isAutoDiscovered, flags, planId, status from "
                      "APP_CloudAppUserDetails where subClientId= {0} and modified =0 and discoverByType =6  "
                      "and smtpAddress like N'{2}' ",
    'arch file properties': "select id from archfile where jobid={0} and fileType={1}",
    'arch chunk properties': "select physicalSize from archChunkMapping where archFileId={0}"
}

USER_ACCOUNT_SERVICE_TYPE = {
    'Sharepoint Global Administrator': 4,
    'Sharepoint Online': 51,
    'Sharepoint Azure Storage': 52
}

SHAREPOINT_REST_APIS_DICT_TEMPLATE = {
    'CREATE_SUBSITE': '{0}/_api/web/webinfos/add',
    'WEB': '{0}/_api/web',
    'WEB_SPECIFIC_METADATA': '{0}/_api/web/{1}',
    'FILES': "{0}/_api/web/GetFolderByServerRelativeUrl('{1}')/Files",
    'CREATE_FILE': "{0}/_api/web/GetFolderByServerRelativeUrl('{1}')/Files/add(url='{2}', overwrite=true)",
    'RENAME_FILE': "{0}/_api/web/getfilebyserverrelativeurl('{1}/{2}')/moveto(newurl='{1}/{3}',flags=1)",
    'CREATE_FOLDER': "{0}/_api/web/folders",
    'LISTS': "{0}/_api/web/lists",
    'LIST': "{0}/_api/web/lists/GetByTitle('{1}')",
    'LIST_FIELDS': "{0}/_api/web/Lists(guid'{1}')/Fields",
    'LIST_ITEMS': "{0}/_api/web/lists/GetByTitle('{1}')/items",
    'LIST_ITEMS_BY_LIST_ID': "{0}/_api/web/lists/GetById('{1}')/items",
    'LIST_ITEM': "{0}/_api/web/lists/GetByTitle('{1}')/items({2})",
    'LIST_ITEM_ATTACHMENT': "{0}/_api/web/lists/GetByTitle('{1}')/items({2})/AttachmentFiles/add(FileName='{3}')",
    'LIST_ITEM_SPECIFIC_METADATA': "{0}/_api/web/lists/GetByTitle('{1}')/items({2})/{3}",
    'LIST_ITEM_TITLE': "{0}/_api/web/lists/GetByTitle('{1}')/items({2})/Title",
    'GET_FILE_METADATA': "{0}/_api/web/GetFolderByServerRelativeUrl('{1}')/Files('{2}')",
    'GET_SPECIFIC_FILE_METADATA': "{0}/_api/web/GetFolderByServerRelativeUrl('{1}')/Files('{2}')/{3}",
    'FOLDER': "{0}/_api/web/GetFolderByServerRelativeUrl('{1}')"
}

LIST_FIELD_TYPES = {
    1: "Integer",
    2: "Single line of text",
    3: "Multiple lines of text",
    4: "Date and Time"
}

UTILS_PATH = os.path.dirname(__file__)
DATA_GENERATION_PATH = os.path.join(UTILS_PATH, "DataGeneration")
TEST_DATA_GENERATION_JSON = os.path.join(DATA_GENERATION_PATH, "data_generation.json")
SPECIAL_DATA_FOLDER_PATH = os.path.join(DATA_GENERATION_PATH, "DataWithSpecialCharsInName.zip")

LIST_VERSIONS_UNWANTED_PROPERTIES = {
    'Created_x005f_x0020_x005f_Date',
    'GUID',
    'Last_x005f_x0020_x005f_Modified',
    'AppAuthor',
    'AppEditor',
    'SMLastModifiedDate',
    'Modified',
    'Created',
    'UniqueId',
    'FileDirRef',
    'FileRef',
    'ScopeId',
    'Attachments',
    'owshiddenversion' # Added them until the MR 312981 gets resolved
}

HIDDEN_FOLDERS = ["m", "_cts", "_private", "images"]

DISK_RESTORE_AS_NATIVE_FILES_VALIDATE_FILES = {
    "root": [ 'Manifest.xml', 'Requirements.xml', 'RootObjectMap.xml',
             'SiteCollection.xml', 'SystemData.xml', 'SystemData_temp.xml', 'UserGroup.xml', 'UserGroup_temp.xml'],
    "cvtempbackup": ['0_LookupListMap_0.xml', 'Manifest.xml', 'Requirements.xml',
                     'RootObjectMap.xml', 'SiteCollection.xml', 'SystemData.xml'],
    "restored_item": ['CV_Version_Temp', 'ExportSettings.xml', 'LookupListMap.xml', 'Manifest.xml', 'Manifest_DefaultFolders.xml',
                      'Manifest_DefaultItems.xml', 'Manifest_Items.xml', 'Manifest_Lists.xml', 'Requirements.xml',
                      'RootObjectMap.xml', 'SystemData.xml', 'UserGroup.xml', 'ViewFormsList.xml']
}

FILE_VERSIONS_UNWANTED_PROPERTIES = {
    'Created'
}

GROUP_ASSOCIATION_CATEGORY_DISCOVERY_TYPE = {
    "All Web Sites": 9,
    "All Teams Sites": 10,
    "All Project Online Sites": 11
}

ALL_ITEMS_ADDITIONAL_PATHS = ["\\Contents", "\\Contents\\Lists", "\\Contents\\_catalogs", "\\Subsites"]
DEFAULT_LIBRARY = 'Shared Documents'
CLOUD_REGIONS = {
    'Default (Global Service)': 1,
    'Germany': 2,
    'China': 3,
    'U.S. Government GCC': 4,
    'U.S. Government GCC High': 5
}


class SharepointListTemplate(Enum):
    """
    List of supported Sharepoint list templates.
    """
    EVENTS = "C"
    TASKS = "T"
    XMLFORM = "F"
    DOCLIBRARY = "D"
    PICLIBRARY = "P"
    ANNOUNCEMENTS = "A"
    CONTACTS = "X"
    LINKS = "L"
    GANNTT_TASKS = "PT"
    WEBPAGE_LIB = "W"
    ISSUETRACK = "I"
    DISCUSS_BOARD = "DB"
