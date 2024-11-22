# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module to define constants for Cloud Connector Automation"""

import os

# CloudConnector Constants #

AGENT_NAME = 'Cloud Apps'

SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/admin.directory.user.security',
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/drive'
]

KEY_FILE_PATH = '{0}'

CLIENT_EMAIL = '{0}'

ADMIN_EMAIL = '{0}'

GOOGLE_API_DICT = {
    'GAdmin': ['admin', 'directory_v1'],
    'GMail': ['gmail', 'v1'],
    'GDrive': ['drive', 'v3']
}

CRED_STORAGE_FILE = '.creds.json'

# Maximum users which gsuite admin api will return for list user query.
# Valid value 1 to 500
USER_SEARCH_MAX_COUNT = 200

LABEL_IDS_TO_SKIP = [
    'CATEGORY_PERSONAL',
    'CATEGORY_SOCIAL',
    'CATEGORY_UPDATES',
    'CATEGORY_FORUMS',
    'CHAT',
    'CATEGORY_PROMOTIONS',
    'SPAM',
    'IMPORTANT',
    'STARRED',
    'UNREAD'
]

VALID_LABEL_IDS = [
    'INBOX',
    'DRAFT',
    'SENT',
    'TRASH'
]

GMAIL_DB_NAME = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'gmail_db.json')

GDRIVE_DB_NAME = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'gdrive_db.json')

ONEDRIVE_DB_NAME = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'onedrive_db.json')

JOB_LIST_TABLE = 'job_list'

MESSAGES_TABLE = '_messages'

MESSAGES_AFTER_RES_TABLE = '_messages_after_res'

MESSAGES_AFTER_OOP_SOURCE = '_messages_oop_source'

MESSAGES_AFTER_OOP_DESTINATION = '_messages_oop_destination'

LABELS_TABLE = '_labels'

GDRIVE_TABLE = '_files'

USER_TABLE = '_users'

GDRIVE_CREATED_TABLE = '_created_files_list'

GDRIVE_DOCUMENT_DIRECTORY = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'GDrive_Docs')

GMAIL_DOCUMENT_DIRECTORY = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'GMail_Docs')

DOWNLOAD_DIRECTORY = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'downloads')

ONEDRIVE_DOCUMENT_DIRECTORY = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'OneDrive_Docs')

ONEDRIVE_DOWNLOAD_DIRECTORY = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'onedrive_downloads')

DATA_AGENT_TYPE = 'cloud apps'

INPUT_FILE = 'inputs.json'

GET_CLOUDAPPS_CLIENTS = 'Client?PseudoClientType=CloudApps'

GET_CLOUDAPPS_INSTANCE = 'instance?clientId={0}'

CLOUD_APPS_INSTANCE_TYPE_GMAIL = 1

CLOUD_APPS_INSTANCE_TYPE_GDRIVE = 2

WD_FORMAT_PDF = 17

GDRIVE_FOLDER = 'CVTestData'

NO_OF_MAILS_TO_CREATE = 10

NO_OF_DOCS_TO_CREATE = 5

DESTINATION_TO_DISK = 'C:\\Windows\\Temp'

DESTINATION_TO_DISK_AFTER_RESTORE = '%s\\%s\\My Drive\\%s'

FOLDER_METADATA = {
    'name': '',
    'mimeType': 'application/vnd.google-apps.folder'
}

FOLDER_METADATA_CVID = {
    'name': '',
    'mimeType': 'application/vnd.google-apps.folder',
    'properties': {'CVID': ''}
}

# OneDrive related constants

ONEDRIVE_CLIENT = 'Onedrive_v2_automation_{0}'

ONEDRIVE_AGENT = 'Cloud Apps'

ONEDRIVE_INSTANCE = 'OneDrive'

ONEDRIVE_BACKUPSET = 'defaultbackupset'

ONEDRIVE_SUBCLIENT = 'default'

ONEDRIVE_INDEX_APPTYPE_ID = 200118

ONEDRIVE_FOLDER = 'AutomationFolder'

MY_DRIVE_FOLDER = 'My Drive'

ONENOTE_FOLDER = 'Notebooks'

CLIENT_ID = '{0}'

CLIENT_SECRET = '{0}'

TENANT = '{0}'

AUTH_TOKEN_URL = 'https://login.microsoftonline.com/%s/oauth2/v2.0/token'

ONEDRIVE_SCOPE = 'https://graph.microsoft.com/.default'

MS_GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0/'

MS_GET_USERS = 'users'

MS_GET_GROUPS = 'groups'

MS_GET_GROUP_MEMBERS = '/{0}/members'

MS_CREATE_FOLDER = '/drive/items/root/children'

MS_CREATE_FOLDERS = '/drive/items/{0}/children'

MS_UPDATE_FILE = '/{0}/drive/items/{1}/content'

MS_UPLOAD_FILE = '/{0}/drive/items/root:/{1}/{2}:/content'

MS_UPLOAD_FILE_TO_ROOT = '/{0}/drive/root:/{1}:/content'

MS_UPLOAD_FILE_WITH_ID = '/{0}/drive/items/{1}:/{2}:/content'

MS_GET_ROOT_ID = '/{0}/drive/root'

MS_GET_ROOT_CHILDREN = '/{0}/drive/root/children'

MS_GET_FOLDER_CHILDREN = '/{0}/drive/items/{1}/children'

MS_GET_FOLDER_CHILDREN_PATH = '/{0}/drive/root:/{1}:/children'

MS_UPDATE_DRIVEITEM = '/{0}/drive/items/{1}'

MS_DELETE_ITEM = '/{0}/drive/items/{1}'

MS_CREATE_NOTEBOOK = '/{0}/onenote/notebooks'

MS_GET_SECTION = '/{0}/onenote/notebooks/sections'

MS_GET_ALL_SECTIONS = '/{0}/onenote/sections'

MS_CREATE_SECTION = '/{0}/onenote/notebooks/{1}/sections'

MS_CREATE_SECTION_IN_SECTION_GROUP = '/{0}/onenote/sectionGroups/{1}/sections'

MS_CREATE_PAGE = '/{0}/onenote/sections/{1}/pages'

MS_GET_PAGE_CONTENT = '/{0}/onenote/pages/{1}/content'

MS_CREATE_SECTION_GROUP = '/{0}/onenote/notebooks/{1}/sectionGroups'

MS_CREATE_SUB_SECTION_GROUP = '/{0}/onenote/sectionGroups/{1}/sectionGroups'

ONEDRIVE_TABLE = '_files'

LATEST_FILES = '_latest_files'

FOLDER_TABLE = '_folder'

USER_PAGE_SIZE = 500

ONEDRIVE_DELTA_QUERY = '/{0}/drive/root/delta?token={1}'

GENERATE_FILES_PATH = 'C:\\Temp'

NO_OF_FILES_TO_UPLOAD = 20

# FS to OneDrive restore related constants

TEST_DATA_PATH = 'C:\\fsod'

SUBCLIENT_NAME = 'TestFSOD'

# cloud storage specific constants

AMAZONS3_INSTANCE_TYPE = 5

AZUREBLOB_INSTANCE_TYPE = 6

ORACLECLOUD_INSTANCE_TYPE = 14

OPENSTACK_INSTANCE_TYPE = 15

# Registry Key Constants

REG_KEY_BASE = 'Base'

BASE_KEY = 'dBASEHOME'

PATH_KEY = 'dGALAXYHOME'

REG_KEY_IDATAAGENT = 'iDataAgent'

SIMULATE_FAILURE_ITEMS_KEY = 'nSimulateCloudAppsBackupFailureAfterNItems'

SIMULATE_FAILURE_ITEMS_VALUE = 6

SIMULATE_FAILURE_ITEMS_REG_TYPE = 'DWord'

ONEDRIVE_JOB_DIRECTORY_PATH = '\\iDataAgent\\JobResults\\CV_JobResults\\iDataAgent\\GCloudAgent\\2\\{0}\\OneDrive_{' \
                              '1}.db '

ONEDRIVE_DISCOVER_PATH = '\\iDataAgent\\JobResults\\CV_JobResults\\iDataAgent\\GCloudAgent\\{0}_{1}' \
                         '\\discover_mode_users_client{0}.db3 '

ONEDRIVE_V2_USER_DISCOVER_PATH = ('\\iDataAgent\\JobResults\\CV_JobResults\\iDataAgent\\Cloud Apps Agent'
                                  '\\DiscoveryCache\\{0}_{1}\\discover_mode_users_client{0}.db3 ')

ONEDRIVE_V2_GROUP_DISCOVER_PATH = ('\\iDataAgent\\JobResults\\CV_JobResults\\iDataAgent\\Cloud Apps Agent'
                                   '\\DiscoveryCache\\{0}_{1}\\discover_mode_group_client{0}.db3 ')

ONEDRIVE_NEW_USER = {
    "accountEnabled": True,
    "displayName": "OneDriveDiscoveryAutomationUser",
    "mailNickname": "",
    "userPrincipalName": "",
    "passwordProfile": {
        "forceChangePasswordNextSignIn": False,
        "password": "#####"
    }
}

ONEDRIVE_UPDATE_USER = {
    "userPrincipalName": "",
    "mailNickname": ""
}

ONEDRIVE_NEW_GROUP = {
    "displayName": "",
    "mailEnabled": False,
    "mailNickname": "",
    "securityEnabled": True
}

