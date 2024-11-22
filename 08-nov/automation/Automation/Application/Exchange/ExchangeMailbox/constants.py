# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for all the constants of ExchangeMailbox

"""

import os
from enum import Enum

APP_TYPE = 137
AGENT_NAME = "Exchange Mailbox"


class mailbox_type(Enum):
    """
    Enum class for declaring all the mailbox types
    """

    USER = "usermailbox"
    JOURNAL = "journalmailbox"
    CONTENTSTORE = "contentstoremailbox"


class Office365GroupType(Enum):
    """
        Enum class for declaring all Office 365 Group Types
    """
    DISTRIBUTION = 'MailUniversalDistributionGroup'
    OFFICE365 = 'GroupMailbox'
    ROLEGROUP = 'RoleGroup'


class OpType(Enum):
    """
        Enum class for declaring Restore optypes
    """
    OVERWRITE = "OVERWRITE"
    SKIP = "SKIP"
    OOPOVERWRITE = "OOPOVERWRITE"


class environment_types(Enum):
    """
    Enum class for declaring all the mailbox types
    """

    EXCHANGE_ONPREMISE = 1
    HYBRID = 2
    EXCHANGE_ONLINE_AD = 3
    EXCHANGE_ONLINE = 4


class SolrDocumentType(Enum):
    """
    Enum class for declaring solr data types
    """

    MAILBOX = 5
    FOLDER = 4
    MESSAGE = 2


class SolrDocumentCIState(Enum):
    """
    Enum class for declaring solr mask states
    """

    TRUE_UP = 3333
    END_USER_ERASED = 3334
    PARENT_FOLDER_ERASED = 3335


BACKUPSET_IDS = {
    "user mailbox": 1,
    "journal mailbox": 2,
    "contentStore mailbox": 3
}

DELETE_MESSAGE_COUNT = 5
SYNC_PROCESS_WAIT_TIME = 600
SYNC_PROCESS_POLL_INTERVAL = 10
AD_MAILBOX_MONITORING_EXE = f'AdMailboxMonitor'
TRUE_UP_PROCESS_EXE = f'CVExIdxSyncCoordinator'
RETENTION_TASK_EXE = f'CvExAutomatedtask'
CV_WELL_KNOWN_FOLDER_NAMES = [
    'calendar',
    'contacts',
    'inbox',
    'tasks',
    'notes']

GET_INDEXED_GUIDS_QUERY = "Select indexingGUID from ArchiveResults"

GET_MAILBOX_ASSOC_POLICY = "SELECT policyType, policyId \
  FROM APP_EmailConfigPolicies \
  WHERE modified = 0 and componentNameId = ( Select assocId from APP_EmailConfigPolicyAssoc WHERE [APP_EmailConfigPolicyAssoc].[smtpAdrress] = '%s' and clientId = %s and modified = 0)"

GET_BACKUP_PROP = "select B.properties  From App_IndexDBInfo A, IdxDbState B " \
                  "Where A.id = B.dbId and A.type = 137 AND A.backupSetId = %s"

GET_PUBLIC_FOLDER_GUID = "SELECT userGuid FROM APP_EmailConfigPolicyAssoc where" \
                         " displayName = \'All Public Folders\' and clientId = %s"

CHECK_MAILBOX_DELETED_FLAG = "Select * from APP_EmailConfigPolicyAssoc" \
                             " where deleted = 1 and modified != 0 " \
                             "and clientId = %s and smtpAdrress = '%s'"

GET_ASSOC_MBX_COUNT = "select count(*) from APP_EmailConfigPolicyAssoc where clientId = %s \
                        and mailBoxType Is Not Null "

SOLR_TYPE_DICT = {

    1: "standalone",
    5: "multinode"
}

RESTORE_AS_STUB_DICT = {
    'restore_as_stubs': True,
    'leave_message_body': True,
    'truncate_body': False,
    'truncate_body_to_bytes': 0,
    'collect_msgs_days_after': 0,
    'collect_msgs_larger_than': 0,
    'collect_msg_with_attach': False
}

SOLR_KEYWORDS_MAPPING = {

    'cistatus': 'ContentIndexingStatus',
    'cijid': 'CIJobId',
    'afid': 'AchiveFileId',
    'afof': 'ArchiveFileOffset',
    'msgclass': 'MessageClass',
    'fmsmtp': 'FromSMTP',
    'conv': 'Subject',
    'hasattach': 'HasAttachment',
    'hasAnyAttach': 'HasAnyAttachment',
    'folder': 'Folder',
    'entity_ssn': 'entity_ssn',
    'entity_ccn': 'entity_ccn',
    'CAState': 'CAState'
}

CASE_FILTER_AND_SOLR_MAPPING = {

    "EMAIL_RECIPIENTLIST": 'rclst',
    'EMAIL_SUBJECT': 'conv',
    'EMAIL_TO': 'to',
    'EMAIL_CC': 'cc',
    'EMAIL_BCC_ADMIN': "bcc",
    'EMAIL_ATTACHMENTNAME': 'attname',
    'FOLDER': 'folder'

}

ARCHIVE = 'Archive'
CLEANUP = 'Cleanup'
RETENTION = 'Retention'
JOURNAL = 'Journal'

MBX_JOURNAL = "JOURNAL"
MBX_USER = "USER"
TOP_OF_INFO_STORE = "top of information store"

BACKUPSET_NAME = "Automation_%s"
SUBCLIENT_NAME = "Automation_sub_%d_%s"

EXCHNAGE_CLIENT_NAME = 'ExchangeClient_%s'

CASE_CLIENT_NAME = 'CaseClient_%s'

CASE_CLIENT_BK_NAME = 'CaseClientBackedup_%s'

CASE_CLIENT_CI_NAME = 'CaseClientCI_%s'

CASE_CLIENT_EE_NAME = 'CaseClientEE_%s'

DEFINITION_NAME = 'AutomationDef'

OFFICE_365_PLAN_DEFAULT = 'AutoOffice365Plan_%s'

OFFICE_365_PLAN_DELETED_ITEM_RETENTION_ENABLED = 'AutoOffice365Plan_deleted_item_retention_%s'

OFFICE_365_PLAN_ATTACHMENTS = 'AutoOffice365Plan_with_attachments_%s'

OFFICE_365_PLAN_LARGER_THAN = 'AutoOffice365Plan_larger_than_%s'

OFFICE_365_PLAN_OLDER_THAN = 'AutoOffice365Plan_older_than_%s'

ARCHIVE_PLAN_DEFAULT = 'archive_plan_default_%s'

ARCHIVE_POLICY_DEFAULT = 'archive_default_%s'

ARCHIVE_POLICY_DELETED_ITEM_REETENTION_ENABLED = 'archive_deleted_item_retention_%s'

ARCHIVE_POLICY_ATTACHMENTS = 'archive_with_attachments_%s'

ARCHIVE_POLICY_LARGER_THAN = 'archive_larger_than_%s'

ARCHIVE_POLICY_OLDER_THAN = 'archive_older_than_%s'

CLEANUP_POLICY_DEFAULT = 'cleanup_default_%s'

CLEANUP_POLICY_OLDER_THAN = 'cleanup_older_than_%s'

CLEANUP_POLICY_LARGER_THAN = 'cleanup_larger_than_%s'

CLEANUP_POLICY_ADD_RECALL_LINK = 'cleanup_add_recall_link_%s'

CLEANUP_POLICY_LEAVE_MESSAGE_BODY = 'cleanup_leave_message_body_%s'

CLEANUP_POLICY_SKIP_UNREAD_MESSAGE = 'cleanup_skip_unread_message_%s'

CLEANUP_POLICY_HAS_ATTACHMENTS = 'cleanup_has_attachments_%s'

CLEANUP_POLICY_PRUNING_MESSAGES = 'cleanup_pruning_messages_%s'

CLEANUP_POLICY_PRUNING_STUBS = 'cleanup_pruning_stubs_%s'

RETENTION_POLICY_DEFAULT = 'retention_default_%s'

RETENTION_POLICY_DAYS_FOR_PRUNING = 'retention_retention_time_%s'

DELETE_RETENTION_POLICY_DEFAULT = 'delete_retention_default_%s'

JOURNAL_POLICY_DEFAULT = 'journal_default_%s'

CLEANUP_POLICY_DEFAULT_DELETE = 'cleanup_delete_default_%s'

CLEANUP_POLICY_DELETE_OLDER_THAN = 'cleanup_delete_older_than_%s'

CLEANUP_POLICY_DELETE_LARGER_THAN = 'cleanup_delete_larger_than_%s'

CLEANUP_POLICY_DELETE_SKIP_UNREAD_MESSAGE = 'cleanup_delete_skip_unread_message_%s'

CLEANUP_POLICY_DELETE_HAS_ATTACHMENTS = 'cleanup_delete_has_attachments_%s'

OFFICE_365_PLAN_DEFAULT = 'AutoOffice365Plan_%s'

OFFICE_365_PLAN_DELETED_ITEM_RETENTION_ENABLED = 'AutoOffice365Plan_deleted_item_retention_%s'

OFFICE_365_PLAN_ATTACHMENTS = 'AutoOffice365Plan_with_attachments_%s'

OFFICE_365_PLAN_LARGER_THAN = 'AutoOffice365Plan_larger_than_%s'

OFFICE_365_PLAN_OLDER_THAN = 'AutoOffice365Plan_older_than_%s'

OFFICE_365_PLAN_CLEANUP = 'AutoOffice365Plan_Cleanup_%s'

OFFICE_365_PLAN_ARCHIVE = 'AutoOffice365Plan_Archive_%s'

OFFICE_365_PLAN_CI = 'AutoOffice365Plan_CI_%s'

OFFICE_365_PLAN_ARCHIVE_LARGER_THAN = 'AutoOffice365Plan_Archive_Larger_Than_%s'

OFFICE_365_PLAN_ARCHIVE_DAYS = 'AutoOffice365Plan_Archive_Days_%s'

UTILS_PATH = os.path.dirname(__file__)

SCRIPT_PATH = os.path.join(os.path.dirname(UTILS_PATH), "PowershellScripts")

"""Path of the PowerShell file to be used to execute a create onpremise mailbox"""
CREATE_MAILBOX = os.path.join(SCRIPT_PATH, 'create_mailbox.ps1')

"""Path of the PowerShell file to be used to execute a create journal mailbox"""
CREATE_JOURNAL_MAILBOX = os.path.join(
    SCRIPT_PATH, 'create_journal_mailbox.ps1')

"""Path of the PowerShell file to be used to execute a send emails to users"""
SEND_EMAIL = os.path.join(SCRIPT_PATH, 'send_email_exchange_online.ps1')

""" Path of the PowerShell file to be used to delete content of onpremise
mailbox PowerShell command."""
CLEANUP_CONTENT_ONPREMISE = os.path.join(
    SCRIPT_PATH, 'delete_content_exchange_onpremise.ps1')

"""Path of the PowerShell file to be used to execute import pst"""
IMPORT_PST = os.path.join(SCRIPT_PATH, 'import_pst.ps1')

"""Path of the PowerShell file to be used to execute create databases"""
CREATE_DATABASES = os.path.join(SCRIPT_PATH, 'create_databases.ps1')

"""Path of the PowerShell file to be used to execute get online users"""
GET_ONLINE_USERS = os.path.join(SCRIPT_PATH, 'get_online_users.ps1')

"""Path of the PowerShell file to be used to execute get o365 groups"""
GET_O365_GROUPS = os.path.join(SCRIPT_PATH, 'get_o365_groups.ps1')

"""Path of the PowerShell file to be used to execute get databses"""
GET_DATABASES = os.path.join(SCRIPT_PATH, 'get_all_databases.ps1')

"""Path of the PowerShell file to be used to execute create archive mailbox"""
CREATE_ARCHIVE_MAILBOX = os.path.join(
    SCRIPT_PATH, 'create_archive_mailbox.ps1')

"""Path of the PowerShell file to be used to execute a PowerShell command."""
EXDBCOPY_OPS = os.path.join(SCRIPT_PATH, 'exdbcopy_operations.ps1')

"""Path of the PowerShell file to be used to execute a PowerShell command."""
GET_MBNAMES = os.path.join(SCRIPT_PATH, 'get_mailbox_names.ps1')

"""Path of the PowerShell file to be used to execute a PowerShell command."""
MOUNTDISMOUNT_EXDB = os.path.join(SCRIPT_PATH, 'mount_dismount_exdb.ps1')

"""Path of the PowerShell file to be used to execute a PowerShell command."""
OVERWRITE = os.path.join(SCRIPT_PATH, 'overwrite_exdb.ps1')

"""Path of the PowerShell file to be used to execute a PowerShell command."""
REMOVE_DATABASE = os.path.join(SCRIPT_PATH, 'remove_database.ps1')

"""Path of the PowerShell file to be used to execute a PowerShell command."""
CREATE_MAILBOXES = os.path.join(SCRIPT_PATH, 'create_mailboxes.ps1')

"""Path of the PowerShell file to be used to execute a PowerShell command."""
CHECK_MAILBOX = os.path.join(SCRIPT_PATH, 'check_mailbox.ps1')

"""Path of the PowerShell file to be used to get local Online users"""
GET_ONLINE_AD_USERS = os.path.join(SCRIPT_PATH, 'get_online_adusers.ps1')

"""Path of the PowerShell to create Office365 Group"""
CREATE_OFFICE365_GROUP = os.path.join(SCRIPT_PATH, 'create_o365_group.ps1')

"""Path of the PowerShell to assign Users to Offce 365 Group"""
ASSIGN_USERS_O365_GROUP = os.path.join(
    SCRIPT_PATH, 'add_members_office365_group.ps1')

"""Path of the PowerShell file to be used to get online AD groups"""
GET_ONLINE_AD_GROUPS = os.path.join(SCRIPT_PATH, 'get_online_ad_groups.ps1')

"""Path of the PowerShell file to be used to get users of group"""
GET_MEMBERS_OF_GROUP = os.path.join(SCRIPT_PATH, 'get_members_of_group.ps1')

"""Path of the PowerShell Script to check permissions for service accounts"""
CHECK_SERVICE_ACCOUNT_PERMISSIONS = os.path.join(
    SCRIPT_PATH, 'check_service_account_permissions.ps1')

"""Get Licensed Mailboxes"""
LICENSED_MAILBOXES = os.path.join(SCRIPT_PATH, "get_licensed_exmb_users.ps1")

"""Number of mailboxes in a distribution group"""
DIST_GROUP_MEMBER_COUNT = os.path.join(
    SCRIPT_PATH, 'get_dist_group_user_count.ps1')

"""Type of Group: Office365GroupMailbox or MailDistributionGroup"""
AD_GROUP_TYPE = os.path.join(SCRIPT_PATH, 'get_group_type.ps1')

"""Number of mailboxes in an Office 365 Group"""
O365_USER_COUNT = os.path.join(SCRIPT_PATH, 'get_o365_group_member_count.ps1')

"""Path of the PowerShell to perform operations for Exchange Online Mailbox"""
EXCH_ONLINE_MAILBOX_PSH_OPS = os.path.join(SCRIPT_PATH, 'exch_online_mailbox_ops.ps1')

"""Path of the PowerShell to perform operations for Exchange Onine Office 365 Group"""
EXCH_ONLINE_O365_PSH_OPS = os.path.join(SCRIPT_PATH, 'exch_o365_group_ops.ps1')

"""Path of the PowerShell to perform operations for Exchange Online Public Folder"""
EXCH_ONLINE_PF_OPS = os.path.join(SCRIPT_PATH, 'exch_online_public_folder_ops.ps1')

"""Path of the PowerShell to fetch the GUID of a mailbox"""
GET_MAILBOX_GUID = os.path.join(SCRIPT_PATH, 'get_mailbox_guid.ps1')

"""Path of the Powershell to fetch the online groups"""
GET_ALL_GROUPS = os.path.join(SCRIPT_PATH, "get_online_groups.ps1")

RETRIEVED_FILES_PATH = os.path.join(UTILS_PATH, "RetrievedFiles")

TEST_DATA_GENERATION_JSON = os.path.join(
    UTILS_PATH, "DataGeneration", "data_generation.json")

"""Default database directory"""
EXCHANGE_DATABASES = "C:\\ExchangeDatabases"
CONTENT_STORE_PROP_FILE = os.path.join(
    UTILS_PATH, "RetrievedFiles", "smtp_prop.txt")

SMTP_SERVER = "exserver2013-1.commvault365.com"
ADMIN_USER = "demouser2@commvault365.com"
ADMIN_PWD = "Y29tbXZhdWx0ITEy"
SEND_SCRIPT_PATH = "C:\\Scripts\\PowerCDO"
NUMBER_OF_MAILBOXES = 5
DEFAULT_WEBCONSOLE = 'Y3ZhZG1pbg=='
EXCHANGE_QUEUE_TIMEOUT = 1200  # 20 min
LOCAL_WORKING_DIR = "C:\\Scripts\\AutomationTemp"
SMTP_PATH = r"C:\Scripts\PowerCDO"

EXCHMB_REG_FOLDER = "MSExchangeMBAgent"

CV_STUB_PARAMETER = 'V="12"'

"""Service URLs for REST API operations."""
SERVICES_DICT_TEMPLATE = {
    'PREVIEW_URL': '/Email/message/Preview?docId=%s&appId=%s&commcellId=2&guid=%s'
}

EXCHANGE_PLAN_NAME = 'AutoDiscover%s'

EXCHANGE_PLAN_SUBTYPE = 'ExchangeUser'

EXCHANGE_PLAN_DEFAULT = 'ExchangePlan_%s'

PUBLIC_FOLDER_DEFAULT = 'CV_Test_PublicFolder_%s'

MAILBOX_FOLDER = 'CV_Test_MailboxFolder_%s'

MS_TEAMS_EXPLORATORY_SKU = "710779e8-3d4a-4c88-adb9-386c958d1fdf"

USAGE_LOCATION_IND = 'IN'

# Graph API constants below this
MS_AUTH_TOKEN_URL = 'https://login.microsoftonline.com/%s/oauth2/v2.0/token'

EXMB_SCOPE = 'https://graph.microsoft.com/.default'

MS_GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0/'

MS_GRAPH_GROUPS_ENDPOINT = 'groups'

MS_GRAPH_GROUP_MEMBERS = '/{0}/members'

MS_GRAPH_USERS_ENDPOINT = 'users'

MS_GRAPH_DIRECTORY_OBJECTS = "directoryObjects"

MS_NEW_MS365_GROUP = {
    "displayName": "",
    "mailEnabled": True,
    "mailNickname": "",
    "securityEnabled": True,
    "groupTypes": [
        "Unified"
    ]
}

MS_NEW_SECURITY_GROUP = {
    "displayName": "",
    "mailEnabled": False,
    "mailNickname": "",
    "securityEnabled": True
}

MS_MODIFY_USER = {
    "userPrincipalName": "",
    "mail": ""
}

LICENSE_OP_DICT = {
    "addLicenses": [],
    "removeLicenses": []
}

MS_GRAPH_BETA_ENDPOINT='https://graph.microsoft.com/beta/'


class CSSendEmailHelper(Enum):
    """Enum to specify class type"""

    LARGE = "Large"
    SMALL = "Small"
    UNICODE = "Unicode"
    DEFAULT = None
    SMTPCACHEEMAILSDIR = "SMTPCacheEmails"
    O365EMAILSDIR = "O365Emails"


EXCHANGE_AGENT = "exchange mailbox"
EXCHANGE_INSTANCE = "defaultinstancename"
EXCHANGE_BACKUPSET = "user mailbox"
EXCHANGE_SUBCLIENT = "usermailbox"
