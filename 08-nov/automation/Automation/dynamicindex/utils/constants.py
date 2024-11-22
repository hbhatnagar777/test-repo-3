# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" It contains constants which will be used throughout the app."""

from AutomationUtils.constants import AUTOMATION_DIRECTORY
import enum
import os

# log file constants
DM2_WEB_LOG = 'DM2Web'
DM2_WEB_LOG_FILE = 'DM2Web.log'

# Kubernetes extracting cluster constants
INDEX_GATEWAY_LOG_NAME = 'IndexGateway.log'
REGION_EASTUS2 = 'eastus2'
REGION_EASTUS = 'eastus'
CLIENT_ENTITY_TYPE = 'CLIENT'
WORKLOAD_ENTITY_TYPE = '1'
CE_LOG_UNIX = 'CvContentExtractor'
POD_LOG_PATH = 'var/log/commvault/Log_Files'
CE_STAT_LOG_PATTERN = 'Stat - TASK'
CE_STAT_SEARCH_TEXT_PATTERN = '[SEARCHTEXT]'
ACR_NAME = 'extractingContainerRegistry'
EXTRACTING_SERVICE_NAME = 'cvextractor'
NER_VM_SIZE = 'standard_e4ds_v5'
EXTRACTING_CONTAINER_NAME = 'contentextractor'
FIELD_APPID = 'appId'
FIELD_PASSWORD = 'password'
FIELD_TENANT = 'tenant'
FIELD_STATUS = 'status'
FIELD_LOADBALANCER = 'loadBalancer'
FIELD_INGRESS = 'ingress'
FIELD_EXTERNAL_IP = 'ip'
KEY_EXTRACTING_SERVICE_URL = 'ContentExtractorAKS'
KEY_REDIS_CACHE_CONFIG = 'AzureRedisCache'
KEY_FILE_SHARE_STORAGE = 'AzureFileStorage'
CLOUD_APP_STORAGE_QSCRIPT = 'SetCloudAppStorageResource'
KEY_ENABLED = 'ENABLED'
KEY_COMMCELL = 'Commcell'
KEY_ALLOW_GLOBAL_LOADBALANCER_URL = 'AllowGlobalLoadBalancerURL'
KEY_LOADBALANCER_URL = 'LoadBalancerURL'
KEY_LOADBALANCER_SECRET_KEY = 'LoadBalancerKey'
KEY_ALLOW_REDISCACHE_URL = 'AllowGlobalRedisCacheURL'
KEY_REDISCACHE = 'RedisCacheKey'
KEY_REDISCACHE_URL = 'RedisCacheURL'
SECRET_KEY_CLUSTER = '00DBFC72-72F7-46D7-B39C-B66B0FAD48C7'
DATA_TYPE_STRING = 'STRING'
DEFAULT_RESOURCE_GROUP = "DIAutomationGroup"
DEFAULT_CLUSTER_NAME = "DICluster"
DEFAULT_AZURE_LOCATION = "eastus2"
FEATURE_TYPE_SDG = 'SensitiveDataGovernance'
FEATURE_TYPE_CI = 'ContentIndexing'
FEATURE_TYPE_ALL = f"{FEATURE_TYPE_CI},{FEATURE_TYPE_SDG}"

# Application type
APPTYPE_ALL = 100
APPTYPE_FILES = 33
APPTYPE_EMAILS = 54
# Permissions
SHARE_ADD_PERMISSION = 1
SHARE_DELETE_PERMISSION = 2
SHARE_EXECUTE_PERMISSION = 3
SHARE_VIEW_PERMISSION = 4
SHARE_ALL_PERMISSION = 5
SHARE_NO_PERMISSION = 6
# Set deletion range
DELETE_SELECTED = 1
DELETE_PAGE = 2
DELETE_ALL = 3
DELETE_SET = 4
# Exportset formats
PST = 1
CAB = 2
NSF = 3
HTML = 4
# SELECTION RANGE
SELECTED = 1
THIS_PAGE = 2
ALL = 3
# Job operation type
PRECHECK = "preoperation"
POSTCHECK = "postoperation"
# Custom names
QUERYSET = "Query Set"
EXPORTSET = "Export Set"
# Wait times & limits
RANDOM_INT_LOWER_LIMIT = 100
RANDOM_INT_UPPER_LIMIT = 100000
TWO_MINUTES = 1200
ONE_MINUTE = 60
# Violation
CHARS_NOT_ALLOWED_IN_SETNAME = "/\\:*?\"<>|@;&^()%#+"
# Set names
NUM_CHARS = 5
NUM_DIGITS = 2
# Set names
QUERYSET_NAME_PREFIX = "qs"
QUERY_NAME_FORMAT = "query"

# Content Extraction Constants
CE_SERVICE_NAME = "CVContentPreview(Instance001)"
CE_SERVICE_NAME_UNIX = "CvPreview"
EXTRACTOR_THREAD_TIME_OUT = "extractorThreadTimeout"
CA_REGISTRY = "ContentAnalyzer"
EXCEL_MAX_SIZE_IN_MB = "excelMaxSizeInMB"
CA_SERVICE_NAME_WINDOWS = "CONTENTANALYZER"
CA_SERVICE_NAME_UNIX = "ContentAnalyzer"
RECALL_BASED_PREVIEW_SETTING = 'RecallBasedPreviewAllowed'
AUTO_SHUTDOWN_TIMER_REGISTRY = 'CAQueueInactivityTimeout'
AUTO_SHUTDOWN_DEFAULT_TIMER_TASK_DELAY = 10
AUTO_SHUTDOWN_NO_PYTHON_RUNNING_ERROR = 'Python client is not running on CA client'
AUTO_SHUTDOWN_NOT_WORKING = 'Auto shutdown didnt happen properly'
AUTO_SHUTDOWN_WORKING = 'Auto shutdown happened properly'

# CS DB
DB_FIELD_COMMVAULT = r'\COMMVAULT'
DB_FIELD_COMMSERV = 'commserv'

# Registry types
REG_DWORD = "DWord"
REG_STRING = 'String'

# Application Names
SENSITIVE_DATA_GOVERNANCE = "Sensitive data governance"
FILE_STORAGE_OPTIMIZATION = "File storage optimization"

# Index server constants
IDLE_CORE_TIMEOUT_REG_KEY = 'idleCoreTimeoutSecs'
MAX_LOADED_CORE_REG_KEY = 'idleCoreUnloadMaxLoadCores'
IDLE_CORE_ENABLE_REG_KEY = 'enableIdleCoresUnload'
FIELD_START_TIME = 'startTime'
FIELD_UPTIME = 'uptime'
ANALYTICS_SERVICE_NAME = "CVAnalytics(Instance001)"
ANALYTICS_SERVICE_TIME_OUT = 30  # 30 seconds
FIELD_CLIENT_NAME = 'ClientName'
FIELD_FILE = 'File'
QUERY_EXTRACTOR_TIME_OUT_DOCS = {"IsFile": 1,
                                 "ErrorMessage": "\"Entity extraction request timed out\""}
QUERY_CVSTUB_CRITERIA = {"IsStub": 1}
QUERY_NON_STUB_FILE_CRITERIA = {"IsStub": 0, "IsFile": 1}
QUERY_FILE_CRITERIA = {"IsFile": 1}
QUERY_FOLDER_CRITERIA = {"IsFolder": 1}
QUERY_CISTATE_SUCCESS = {"cistate": 1}
QUERY_CISTATE_ITEMSTATE_SUCCESS = {("cistate", "ItemState"): 1}
QUERY_CISTATE_SKIPPED = {"cistate": 17}
QUERY_CISTATE_DELETE = {"cistate": 3334}
QUERY_CASTATE_SUCCESS = {"CAState": 1}
QUERY_CASTATE_FAILED = {"CAState": 0}
QUERY_NON_DELETE_ITEMS = {("cistate", "ItemState"): [0, 1, 2, 3, 17, 16]}
QUERY_100_ROWS = {"rows": 100}
QUERY_ZERO_ROWS = {"rows": 0}
QUERY_SENSITIVE_FILES = {'entities_extracted': '*'}
NUM_FOUND_PARAM = "numFound"
SYNC_TOTAL_PARAM = 'Total'
SYNC_SUCCESS_STATE_PARAM = 'SuccessState'
SIZE_ON_DISK_BYTES_PARAM = 'SizeOnDisk'
SENSITIVE_DOCS_PARAM = 'SensitiveDocuments'
ENTITY_ID_PARAM = 'EntityID'
NUM_DOCS_PARAM = "numDocs"
RESPONSE_PARAM = "response"
DOCS_PARAM = "docs"
URL_PARAM = "Url"
ASSOCIATED_DS_PARAM = 'AssociatedDS'
ASSOCIATED_DS_TYPE_PARAM = 'AssociatedDSType'
DOCUMENTS_PARAM = 'Documents'
SIZE_IN_BYTES_PARAM = 'SizeInBytes'
SOLUTION_TYPE_PARAM = 'SolutionType'
DATA_SOURCE_NAME_KEY = 'data_source_name'
DATA_SOURCE_ID_KEY = 'data_source'
SIZE_SOLR_KEY = 'Size'
SUBJECT_SOLR_KEY = 'Subject'
DOCUMENT_TYPE_PARAM = 'DocumentType'
APPLICATION_ID_PARAM = 'ApplicationId'
FOLDER_SIZE_PARAM = 'FolderSize_lv'
FOLDERS_COUNT_PARAM = 'FolderCount_iv'
FILES_COUNT_PARAM = 'FileCount_iv'
ACCESS_TIME_PARAM = 'FolderAccessTime_dt'
STATS_PARAM = "stats"
STATS_FIELD_SET_PARAM = "stats.field"
STATS_FIELD_PARAM = "stats_fields"
FACET_PARAM = "facet"
FACET_FIELD_SET_PARAM = "facet.field"
FACET_FIELDS_PARAM = "facet_fields"
FACET_COUNTS_PARAM = "facet_counts"
MIN_PARAM = 'min'
MAX_PARAM = 'max'
MEAN_PARAM = 'mean'
COUNT_PARAM = "count"
SUM_PARAM = 'sum'
ROWS_PARAM = "rows"
FIELD_FILE_EXTENSION = "FileExtension"
FIELD_EXTRACT_DURATION = "extractedDuration_s"
FIELD_JOB_ID = "JobId"
FIELD_MODIFIED_TIME = "ModifiedTime"
FIELD_URL = "Url_sort"
FIELD_CONTENT = "content"
FIELD_ALL_ENTITIES = "entity_*"
FIELD_KEYWORD_SEARCH = "keyword"
SKIP_FOLDER_CHECK = -1
SOLR_DATE_STRING = "%Y-%m-%dT%H:%M:%SZ"
ANALYTICS_PROCESS_NAME = 'DataCube'
ANALYTICS_REG_KEY = 'Analytics'
ANALYTICS_DIR_REG_KEY = 'analyticsDataDir'
ANALYTICS_DISABLE_ACCESS_CONTROL_REG_KEY = 'bDisableAnalyticsAccessControl'
SOLR_JVM_MEMORY_REG_KEY = 'JvmMx'
SOLR_JVM_MEMORY_REG_KEY_PATH = 'HKLM:\\SOFTWARE\\Wow6432Node\\Apache Software Foundation\\Procrun 2.0\\' \
                               'CVAnalytics(Instance001)\\Parameters\\Java'
SOLR_CONFIG_REG_KEY_PATH = 'Analytics\\Config'
SOLR_COMPUTE_FOLDER_STATS_KEY = 'solr.folderAccessTimeUpdate.isEnabled'
INDEX_DIRECTORY_DEFAULT_NAME = "IndexDirectory%s"
MIN_JVM = 4
MAX_JVM = 32
DEFAULT_JVM_MEMORY = '8191'
DEFAULT_SOLR_PORT = '20000'
BACKUP_INDEX_DIR = 'Index'
BACKUP_INDEX_DIR_UNIX = 'index'
BACKUP_CONF_DIR = 'Config'
BACKUP_CONF_SETS = 'configsets'
BACKUP_CONF_HOME = 'confHome'
DATA_ANALYTICS_DEFAULT_CORES = [
    'cvcoreaudit0',
    'cvcoreaudit1',
    'cvcoreaudit2',
    'cvcoreaudit3',
    'cvcorefla0',
    'cvcorefla1',
    'cvcorefla2',
    'cvcorefla3',
    'cvcorefla4',
    'cvcorefla5',
    'cvcorefla6',
    'cvcorefla7']
SYSTEM_DEFAULT_CORES = [
    'indexserverinfo',
    'cvemptyshard',
    'datasourceinfo'
]
COMPLIANCE_AUDIT_CORE = 'complianceaudit'
DATA_ANALYTICS_DYNAMIC_CORES = ['DC_', 'fsindex_']
NO_DATA_AVAILABLE = "No data available"
CONTENT_INDEXING_STATUS = "ContentIndexingStatus"
CA_STATE = "CAState"

# DataCube Constants
FILE_TYPES_DATA_GEN = [
    'pdf',
    'doc',
    'docx',
    'xls',
    'xlsx',
    'db',
    'ppt',
    'txt',
    'html']
FILE_SYSTEM_MULTINODE_CORE = 'fsindex_{IS}_multinode'
USER_MAILBOX_MULTINODE_CORE = 'UM_{IS}_multinode'
DCUBE_USER_PERMISSION_LIST = [
    'Data Connectors',
    'Data Protection/Management Operations',
    'Agent Management',
    'View',
    'Install Client']
FILE_SYSTEM_DSTYPE = "5"
OPEN_DATASOURCE_DSTYPE = "11"
OPEN_DS_PREFIX = "DC_open_"
FILE_DS_PREFIX = "DC_file_"
ENTITY_EXTRACTION_PROPERTY = ['iscaenabled', 'caconfig', 'caclientid']
ENTITY_EXTRACTION_ENABLED = 'iscaenabled'
ENTITY_EXTRACTION_CONFIG = 'caconfig'
ENTITY_EXTRACTION_CLOUDID = 'caclientid'
OPEN_DS_PROPERTY = ['candelete', 'appname']
OPEN_DS_PROPERTY_VALUES = ["true", "DATACUBE"]
OPEN_DS_PROPERTIES = [
    {"propertyName": OPEN_DS_PROPERTY[x],
     "propertyValue": OPEN_DS_PROPERTY_VALUES[x]}
    for x in range(0, len(OPEN_DS_PROPERTY))]
FILE_DS_EE_COLUMN = ["content"]
FILE_DS_DYNAMIC_PROPERTY = [
    'createclient',
    'candelete',
    'appname',
    'includedirectoriespath',
    'doincrementalscan',
    'username',
    'password',
    'pushonlymetadata',
    'accessnodeclientid',
    'excludefilters',
    'minumumdocumentsize',
    'maximumdocumentsize',
    'includefilters'
]
FILE_DS_INCLUDE_FILE_TYPES = "*.doc, *.docx, *.xls, *.xlsx, *.ppt, *.pptx, *.msg, *.txt, *.rtf, *.eml, *.pdf, " \
                             "*.htm, *.html, *.jpg, *.png, *.jpeg, *.xml, *.csv, *.log, *.ods, *.odt, *.odg, " \
                             "*.odp, *.dot, *.pages, *.bmp, *.xmind"
FILE_DS_DYNAMIC_PROPERTY_VALUES = [
    "archiverClient",
    "true",
    "DATACUBE",
    "",
    "false",
    "",
    "",
    "true",
    "",
    "",
    "0",
    "52428800",
    FILE_DS_INCLUDE_FILE_TYPES
]
SCHEMA_FIELDS = {
    "fieldName": "",
    "type": "string",
    "indexed": True,
    "stored": True,
    "multiValued": False,
    "searchDefault": True,
    "autocomplete": False
}
VIEW_PERMISSION = 201
EDIT_PERMISSION = 202
EXECUTE_PERMISSION = 204
SHARE_PERMISSION = 107
USER_ASSOCIATION_TYPE = 13
SHARE_ADD = 2
SHARE_DELETE = 3
SOLR_FETCH_ONE_ROW = "rows=1"
SOLR_FETCH_HUNDRED_ROW = "rows=100"
ENTITY_EXTRACTION_JSON_PROP = [
    'EntityExtractionRER',
    'EntityExtractionNER',
    'EntityExtractionDE',
    'EntityExtractionFields']

# Activate Entity Names
ENTITY_EMAIL = "Email"
ENTITY_PHONE = "Phone"
ENTITY_IP = "IP Address"
ENTITY_CREDIT_CARD = "CreditCard"
ENTITY_SSN = "SSN"
ENTITY_PERSON = "Person Name"
ENTITY_AUTOMATION = "AutomationFreshCADate"
ENTITY_AUTOMATION_KEYWORDS = "date"
ENTITY_AUTOMATION_REGEX = "(?:[0-9]{4}-[0-9]{2}-[0-9]{2})"
ENTITY_CREDIT_CARD_NEW = 'Credit Card Number'
ENTITY_US_SSN = 'US Social Security number'

# Activate Column/Entity Names for advance search
ADVANCE_SEARCH_FIELDS = [
    "Credit card number",
    "US Social Security number",
    "IP address",
    "US Passport",
    "US Individual Taxpayer Identification Number",
    "Email",
    "US Driver License",
    "Sentiment tags",
    "Routing Transit Number",
    "File name",
    "File Path",
    "Column",
    "Subject",
    "To",
    "From",
    "Cc",
    "Mailbox",
    "Folder",
    "Body",
    "Attachment"
]

# Sqlite DB constants for generated PII data
DB_ENTITY_DELIMITER = "****"
DB_COLUMN_NAMES = [
    'Credit Card Number',
    'US Social Security number',
    'IP Address',
    'PASSPORT',
    'US Individual Taxpayer Identification Number',
    'Email',
    'DL',
    'Sentiment tags',
    'Routing transit number',
    "FileName",
    "FilePath",
    "Column",
    "Subject",
    "To_Mail",
    "From_Mail",
    "CC",
    "Mailbox",
    "Folder",
    "SearchText",
    "Attachment"
]
DB_COLUMN_TO_KEY = [
    'entity_ccn',
    'entity_ssn',
    'entity_ip',
    'entity_us_passport',
    'entity_itin',
    'entity_email',
    'entity_usdl',
    'entity_finance_tags',
    'entity_rtn',
    "FileName_idx",
    "Url_idx",
    "Column_idx",
    "Subject_idx"
]

# Activate Entity Key-solr field mappings
ENTITY_KEY_EMAIL = "entity_email"
ENTITY_KEY_PHONE = "entity_phone"
ENTITY_KEY_IP = "entity_ip"
ENTITY_KEY_CREDIT_CARD = "entity_ccn"
ENTITY_KEY_SSN = "entity_ssn"
ENTITY_KEY_PERSON = "entity_person"
ENTITY_KEY_AUTOMATION = "entity_automationfreshcadate"

# Activate Data Source Names
ONE_DRIVE = "OneDrive"
EXCHANGE = "Exchange"
EXCHANGE_ONLINE = "ExchangeOnline"
DATABASE = "Database"
FILE_SYSTEM = "File system"
GOOGLE_DRIVE = "Google Drive"
GMAIL = "Gmail"
SHAREPOINT = "SharePoint"

# Activate Dashboard Types
SIZE_DISTRIBUTION_DASHBOARD = 'Size Distribution Dashboard'
TREE_SIZE_DASHBOARD = "Tree Size Dashboard"
DUPLICATES_DASHBOARD = 'Duplicates Dashboard'
FILE_OWNERSHIP_DASHBOARD = 'File Ownership Dashboard'
FILE_SECURITY_DASHBOARD = "File Security Dashboard"
TIME_DATA = 'Access/Modified/Created Time'

# FSO Cloud Apps Data Source Names
AZURE = "AZURE"
AWS = "AWS"
GCP = "GCP"

# FSO Dashboard Types
FSO_DASHBOARDS_TO_VERIFY = {
    'ALL': ['reports.sizeDistribution', 'reports.treeSize', 'reports.fileDuplicate',
            'reports.fileSecurity', 'reports.fileOwnership'],
    'AZURE': ['reports.sizeDistribution', 'reports.treeSize', 'reports.fileDuplicate'],
    'AWS': ['reports.sizeDistribution', 'reports.treeSize', 'reports.fileOwnership'],
    'GCP': ['reports.sizeDistribution', 'reports.treeSize', 'reports.fileOwnership']
}

# FSO Tabs in Dashboard
FSO_DASHBOARD_TABS_TO_VERIFY = {
    'ALL': ['Created Time', 'Access Time', 'Modified Time'],
    'AZURE': ['Created Time', 'Modified Time'],
    'AWS': ['Modified Time'],
    'GCP': ['Created Time']
}

FSO_DASHBOARD_FILTERS_ID = {
    'Created Time': 'Created time',
    'Access Time': 'Access time',
    'Modified Time': 'Modified time'
}

# Cloud Apps Client Auth Types
CLOUD_APP_AUTH_TYPES = {'AZURE': {0: 'Access key and Account name', 1: 'IAM VM role', 2: 'IAM AD application'},
                        'AWS': {0: 'Access and secret keys', 1: 'IAM role', 2: 'STS assume role with IAM role'},
                        'GCP': {0: 'N/A'}
                        }

# FSO Metadata DB column names
FSO_METADATA_FIELD_PARENT_DIR = 'PARENT_DIR'
FSO_METADATA_FIELD_NAME = 'NAME'
FSO_METADATA_FIELD_PATH = 'PATH'
FSO_METADATA_FIELD_FILE_SIZE = 'FILE_SIZE'
FSO_METADATA_FIELD_MIME_TYPE = 'MIME_TYPE'
FSO_METADATA_FIELD_MODIFIED_TIME = 'MODIFIED_TIME'
FSO_METADATA_FIELD_CREATED_TIME = 'CREATED_TIME'
FSO_METADATA_FIELD_ACCESS_TIME = 'ACCESS_TIME'
FSO_METADATA_FIELD_FILE_OWNER = 'FILE_OWNER'
FSO_METADATA_FIELD_PARENT_DIR_PERMISSION = 'PARENT_DIR_PERMISSION'
FSO_METADATA_FIELD_FILE_PERMISSION = 'FILE_PERMISSION'
FSO_METADATA_FIELD_FILE_PERMISSION_READABLE = 'FILE_PERMISSION_READABLE'
FSO_METADATA_FIELD_IS_DIR = 'IS_DIR'
FSO_METADATA_FIELD_FILE_TYPE = 'FILE_TYPE'

# Credential Manager vendor type
VENDOR_TYPE = {
    'AZURE': 'Microsoft Azure',
    'AWS': 'Amazon Web Services',
    'GCP': 'Google Cloud Platform'}

# Auth Type access key and secret key ( Credential Manager )
AUTH_TYPE_ACCESS_SECRET_KEYS_GCP = 'Access & Secret keys'
AUTH_TYPE_ACCESS_SECRET_KEYS_AWS = 'Access & Secret Keys'
AUTH_TYPE_ACCESS_SECRET_KEYS_AZURE = 'Access key and Account name'

# Id of the tile for each cloud app in Object Storage UI Panel
CLOUD_APP_TILE_NAMES = {'AZURE': 'AZURE_BLOB', 'AWS': 'AMAZON_S3', 'GCP': 'GOOGLE_CLOUD'}
OBJECT_STORAGE = "Object storage"

# Data Source to GDPR DB column field mapping for advance search output
ADVANCE_SEARCH_DB_OUTPUT_FIELD = {
    ONE_DRIVE: 'FileName',
    EXCHANGE: 'Subject',
    FILE_SYSTEM: 'FilePath',
    GOOGLE_DRIVE: 'FileName',
    DATABASE: 'Column'
}

# Constants for Sharing Permission
VIEW = 'View'
EDIT = 'Edit'

# Plan type constant
SERVER = 'Server'

# Activate solution constant
ACTIVATE = 1024

# Activate Tenant operator operation type
NONE = "NONE"
OVERWRITE = "OVERWRITE"
UPDATE = "UPDATE"
DELETE = "DELETE"

# Activate data controller role constant
DATA_CONTROLLER_ROLE = "Data Controller"
VIEW_ROLE = "View"

# Activate Security Constants
PROVIDER_DOMAIN_NAME = "providerDomainName"
USER_NAME = "userName"
ROLE = "role"

# Activate Compliance
COMPLIANCE_ROLE = "Compliance"

# Machine class constants
TYPE_FILES = "files"
TYPE_FOLDERS = "folders"

# DB Field to Group Exchange Advance Search Output
EXCHANGE_MAILBOX_DB_FIELD = "Mailbox"
EXCHANGE_ATTACHMENT_FIELD = "Attachment"
EXCHANGE_ATTACHMENT_MAILBOXES_FIELD = "AttachmentMailboxes"
DB_SEARCH_TEXT_FIELD = "SearchText"

# GDPR DB Table Names
ENTITY_TABLE_NAME = "entity"
METADATA_TABLE_NAME = "metadata"

# Country Name
USA_COUNTRY_NAME = "United States of America"
INDIA_COUNTRY_NAME = "India"

# FSO Subclient Properties
FSO_SUBCLIENT_PROPS = {
    "fsSubClientProp": {
        "catalogACL": True,
        "catalogAdditional": True,
        "preserveFileAccessTime": True,
        "scanOption": 1
    }
}
# Search Categories used while adding a file server
CLIENT_NAME = "Client name"
HOST_NAME = "Host name"
SERVER_GROUP_NAME = "Server Group Name"

# Job constants
JOB_FAILED = 'failed'
JOB_WITH_ERROR = 'completed w/ one or more errors'
JOB_COMPLETE = 'completed'
INDEX_IMPORT_JOB_TYPE = "Index Import"
AUTO_SCALE_INDEX_PREPARE = "Autoscale Index Prepare"
AUTO_SCALE_INDEX_MOVE = "Autoscale Index Move"

# Load Balancing Constants
SOURCE_CLIENT_ID = "srcclientId"
DESTINATION_CLIENT_ID = "dstclientId"
INDEX_SIZE_LIMIT_IN_MB = "IndexSizeLimitInMB"
INDEX_ITEM_COUNTS = "IndexItemCounts"
INDEX_MOVE_NUM_LIMIT = "IndexMoveNumLimit"
REPICK_CORES_NUM_DAYS = "repickCoresNumDays"
FREE_SPACE_CORES_LIMIT = "FreeSpacePercentLimit"
GX_GLOBAL_PARAM_CATEGORY = "CommServDB.GxGlobalParam"
LAST_INDEX_SERVER_STATS_SYNC_TIME = "nLastIndexServerStatsSyncTime"
CVD_SERVICE_NAME = "GxCVD(Instance001)"
ENGLISH = "ENGLISH"
CONTINUE = "Continue"

# Plan Constants
SERVER_BACKUP_PLAN_TYPE = 2

# Package Name Constants
CONTENT_ANALYZER = "Content Analyzer"
INDEX_STORE = "Index Store"
FILE_SYSTEM_PACKAGE = 'FILE_SYSTEM'
WEB_CONSOLE = 'WEB_CONSOLE'
WEB_SERVER = 'WEB_SERVER'

# Powershell file constants
DENY = 'Deny'
FULL_CONTROL = 'FullControl'

# TPPM constants
CLIENT_ENTITY_ID = 3
TPPM_TYPE = 8
DEFAULT_CA_PORT = 22000
TPPM_CONFIG = f'acl clnt=* dst=@self@ ports={DEFAULT_CA_PORT}'
COMMSERV_REG_KEY = 'CommServe'
WEB_SERVER_ENABLE_TPPM_KEY = 'EnableTppmForCSDB'

# Permission ACL Constants
PERMISSION_FULL_CONTROL = "F"
PERMISSION_READ = "R"
PERMISSION_WRITE = "W"
PERMISSION_EXECUTE = "RX"
PERMISSION_MODIFY = "M"
PERMISSION_DELETE = "D"
PERMISSION_NO_ACCESS = "N"
PERMISSION_DENY = "DENY"

PERMISSION_FULL_CONTROL_FORMATTED = "Full control"
PERMISSION_READ_FORMATTED = "Read"
PERMISSION_WRITE_FORMATTED = "Write"
PERMISSION_READ_WRITE_FORMATTED = "Read,Write"
PERMISSION_EXECUTE_FORMATTED = "Read & execute"
PERMISSION_EXECUTE_WRITE_FORMATTED = "Read & execute,Write"
PERMISSION_MODIFY_FORMATTED = "Modify"
PERMISSION_DELETE_FORMATTED = "Delete"
PERMISSION_NO_ACCESS_FORMATTED = "No access"

# Classifier Constants
TRAIN_STATUS_COMPLETED = "Completed"
TRAIN_STATUS_FAILED = "Failed"
TRAIN_STATUS_NOT_READY = "Not ready"
DONUT_CHART_NAME = 'Files By Classifier'
CLASSIFIER_FACET_FILTER_NAME = 'Files by classifier'
UNCLASSIFIED_FIELD_NAME = 'Unclassified'
CLASSIFIER_ML_API = 'http://localhost:5004/api/2.0/mlflow/experiments/get-by-name?experiment_name='
CLASSIFIER_SOLR_DATASET_ENTITY_QUERY = 'http://localhost:22000/solr/datasets/select?q=entity_id:'
CLASSIFIER_SOLR_DATASET_INFO_ENTITY_QUERY = 'http://localhost:22000/solr/datasets_info/select?q=entity_id:'
CLASSIFIER_ENTITY_TYPE = 4
CLASSIFIER_ARTIFACT_LOCATION = 'artifact_location'
CLASSIFIER_EXPERIMENT = 'experiment'
CLASSIFIER_ATTRIBUTE_TRAINING_STATUS = 'trainingStatus'
CLASSIFIER_ATTRIBUTE_MODEL_GUID = 'modelGUID'
CLASSIFIER_ATTRIBUTE_MODEL_URI = 'modelURI'
CLASSIFIER_ATTRIBUTE_CA_USED = 'CAUsedInTraining'
CLASSIFIER_ATTRIBUTE_SYNC_CA = 'syncedContentAnalyzers'
CLASSIFIER_ATTRIBUTE_CLIENTID = 'clientId'
CLASSIFIER_ATTRIBUTE_LAST_MODEL_TRAIN_TIME = 'lastModelTrainTime'
CLASSIFIER_DETAILS_JSON_NODE = 'classifierDetails'
CLASSIFIER_SYNC_CA_LIST_JSON_NODE = 'contentAnalyzerList'
CLASSIFIER_ENTITY_ID = 'entity_id'
# Retention
ONE_MONTH = 1


# Solr files action constants
class file_actions(enum.Enum):
    SOLR_FILE_DELETE_OPERATION = 'delete'
    SOLR_FILE_DEFER_OPERATION = 'defer'
    SOLR_FILE_KEEP_OPERATION = 'keep'


SOLR_FILE_DELETE_OPERATION_ID = 91
SOLR_FILE_DEFER_OPERATION_ID = 92
SOLR_FILE_KEEP_OPERATION_ID = 92
MARK_FILE_JSON_OPERATION_KEY = 'operation'
MARK_FILE_JSON_FILES_KEY = 'files'
PAYLOAD_FILE_PARAM = 'file'
PAYLOAD_DATA_SOURCE_ID_PARAM = 'dsid'
PAYLOAD_CONTENT_ID_PARAM = 'contentid'
PAYLOAD_CLIENT_ID_PARAM = 'ClientId'
PAYLOAD_CREATED_TIME_PARAM = 'CreatedTime'
PAYLOAD_SUB_CLIENT_ID_PARAM = 'subclientid'
PAYLOAD_CATEGORY_TAG_PARAM = 'categorytag'
PAYLOAD_FOLDER_ACCESS_TIME_TTL_PARAM = 'FolderAccessTimeTTL_dt'
PAYLOAD_FOLDER_ACCESS_TIME_TTL_VALUE = '2070-01-01T00:00:00Z'
PAYLOAD_CATEGORY_TAG_VALUE_DEFER = 'Defer'
PAYLOAD_CATEGORY_TAG_VALUE_KEEP = 'Raw vendor data'
DATA_SOURCE_ID_PARAM = "SourceId"
CLIENT_ID_PARAM = "ClientId"
CONTENT_ID_PARAM = "contentid"
IS_FILE_PARAM = "IsFile:1"
TAG_ID_PARAM = "TagIds"
REVIEW_ACTION_REVIEWED_DOC_PARAM = "ReviewedDocuments"
CREATED_TIME_PARAM = "CreatedTime"
SUB_CLIENT_ID_PARAM = "SubclientId"
MARK_FOR_DELETE_BV_PARAM = "MarkForDelete_bv"
MARK_FOR_DELETE_TIME_DT_PARAM = "MarkForDeleteTime_dt"
MARK_FOR_DELETE_USER_NAME_SV_PARAM = "MarkForDeleteUserName_sv"
MARK_FOR_DELETE_USER_GUID_SV_PARAM = "MarkForDeleteUserGuid_sv"
IGNORE_FROM_DELETE_BV = "IgnoreFromDeletion_bv"
IGNORE_FROM_DELETE_TIME_DT = "IgnoreFromDeletionTime_dt"
IGNORE_FROM_DELETE_USER_GUID_SV = "IgnoreFromDeletionUserGuid_sv"
IGNORE_FROM_DELETE_USER_NAME_SV = "IgnoreFromDeletionUserName_sv"
IGNORE_FROM_DELETE_USER_CATEGORY_SV = "IgnoreFromDeletionCategory_sv"
FOLDER_ACCESS_TIME_TTL_DT = "FolderAccessTimeTTL_dt"
MAX_FILES_TO_MARK = 50
MARK_FILES_REQUEST_JSON = {MARK_FILE_JSON_OPERATION_KEY: SOLR_FILE_KEEP_OPERATION_ID,
                           MARK_FILE_JSON_FILES_KEY: []}
SOLR_FILE_OPERATIONS_MAP = {file_actions.SOLR_FILE_KEEP_OPERATION: SOLR_FILE_KEEP_OPERATION_ID,
                            file_actions.SOLR_FILE_DEFER_OPERATION: SOLR_FILE_DEFER_OPERATION_ID,
                            file_actions.SOLR_FILE_DELETE_OPERATION: SOLR_FILE_DELETE_OPERATION_ID}
PAYLOAD_CATEGORY_TAG_VALUE_MAP = {file_actions.SOLR_FILE_KEEP_OPERATION: PAYLOAD_CATEGORY_TAG_VALUE_KEEP,
                                  file_actions.SOLR_FILE_DEFER_OPERATION: PAYLOAD_CATEGORY_TAG_VALUE_DEFER}
IGNORE_FROM_DELETION_KEYS_MAP = [IGNORE_FROM_DELETE_BV, IGNORE_FROM_DELETE_TIME_DT, IGNORE_FROM_DELETE_USER_GUID_SV,
                                 IGNORE_FROM_DELETE_USER_NAME_SV, IGNORE_FROM_DELETE_USER_CATEGORY_SV]
MARK_FOR_DELETE_KEYS_MAP = [MARK_FOR_DELETE_BV_PARAM, MARK_FOR_DELETE_TIME_DT_PARAM,
                            MARK_FOR_DELETE_USER_GUID_SV_PARAM, MARK_FOR_DELETE_USER_NAME_SV_PARAM]
OPERATION_ATTRIBUTES_SOLR_MAP = {file_actions.SOLR_FILE_DELETE_OPERATION: MARK_FOR_DELETE_KEYS_MAP,
                                 file_actions.SOLR_FILE_DEFER_OPERATION: IGNORE_FROM_DELETION_KEYS_MAP,
                                 file_actions.SOLR_FILE_KEEP_OPERATION: IGNORE_FROM_DELETION_KEYS_MAP}

# Risks
RETENTION_NOT_SET = "Retention not set"

# OS Type
WINDOWS = "windows"
UNIX = "unix"

# unix machine constants
CVLAUNCH_PROCESS_NAME = 'cvlaunchd'

# Constants Used For Subclient Creation
FILE_SYSTEM_IDA = "File System"
EXCHANGE_IDA = "Exchange Mailbox"
DEFAULT_BACKUPSET = "defaultBackupSet"
USER_MAILBOX_BACKUPSET = "user mailbox"
USER_MAILBOX_SUBCLIENT = "usermailbox"

# Content Indexing policy constants
CI_POLICY_TYPE = "ContentIndexing"

# CI Job Type Constant

CI_JOB_NAME = "Content Indexing"

# File Monitoring Operations
FILE_MONITORING_OPERATIONS = ["Modified", "Deleted", "Accessed", "Renamed"]

# Office365 datasource name constants
SHAREPOINT_INDEX = "sharepointindex_"
EXCHANGE_INDEX = "UM_"
ONEDRIVE_INDEX = "onedriveindex_"
MULTI_NODE = "_multinode"
CONF_HOME = "confHome"
RESTORE_LEVEL = 'RESTORE'

# Office365 reuse index dict constants
DOCUMENT_CI_EE_SUCCESS = {"CAState": "1",
                          "ContentIndexingStatus": "1",
                          "DocumentType": "1"
                          }

DOCUMENT_CI_EE_STATUS = {"facet.field": ["ContentIndexingStatus", "CAState"],
                         "facet": "on",
                         "wt": "json",
                         "rows": "0"
                         }

# Pruning constants
EVENT_MANAGER_SERVICE = "GxEvMgrS(Instance001)"
EVENT_MANAGER_REG = "EventManager"
PRUNE_REGISTRY_MINS = "AppPruneDataSourcesMinutes"

# datasource property constants
PROPERTY_NAME = "propertyName"
PROPERTY_VALUE = "propertyValue"
SUBCLIENT_PROPERTY = "subclientid"

# client properties update JSON
SP_PROPS_UPDATE_JSON = {
    "pseudoClientInfo": {
        "clientType": 78,
        "sharepointPseudoClientProperties": {
            "indexServer": {
                "mediaAgentId": 2,
                "mediaAgentName": ""
            }
        }
    }
}

# Review actions
IGNORE_RISKS = "Ignore Risks"
IGNORE_FILES = "Ignore Files"
SET_RETENTION = "Set Retention"
MOVE_FILES = "Move Files"
DELETE_FILES = "Delete Files"
ARCHIVE_FILES = "Archive"
TAG_FILES = "Tag"
DELETE_FROM_BACKUP = "delete_from_backup"
REDACTION = "redaction"
DOCUMENT_CHAINING = "document_chaining"
STATUS = "Status"
ID = "Id"
COMPLETED = "Completed"
REQUEST_CONFIGURED = "Request configured"
CRITERIA = "Criteria"
ID = "Id"
DETAILS = "Details"
DATA_CURATION="Threat Scan"
BACKUP="Backup"
START_THREAT_SCAN = "Threat scan"
DELETE_ANOMALY = "Delete anomaly"
MARK_SAFE = "Mark safe"
MARK_CORRUPT = "Mark corrupt"
DOWNLOAD = "Download"
NOT_REVIEWED = "Not reviewed"
REVIEWED = "Reviewed"
ACCEPTED = "Accepted"
DECLINED = "Declined"
FDA_ANOMALY = "File data analysis"
TA_ANOMALY = "Threat analysis"
THREAT_SCAN_FOLDER = "temp"
THREAT_SCAN_PLAN_PREFIX = "ODA_DCPLAN_"
RECOVER_FILES = "Recover files"
THREAT_SCAN_EVENT_CODE = "69:60"
RESTORE_JOB = "Restore"
ADD_SERVER_ERROR = "Object reference not set to an instance of an object."

# FSO Dashboard Facet Filters
FILTER_NAME = "FILTER_NAME"
FILTER_VALUE = "FILTER_VALUE"
FILTER_SIZE = "Size"
SIZE_0KB_1MB = "0KB to 1MB"
SIZE_1MB_50MB = "1MB to 50MB"
SIZE_50MB_1GB = "50MB to 1GB"
SIZE_1GB_50GB = "1GB to 50GB"
SIZE_50GB_500GB = "50GB to 500GB"
SIZE_RANGE_VALUES = {
    SIZE_0KB_1MB: (0, 1048576),
    SIZE_1MB_50MB: (1048576, 52428800),
    SIZE_50MB_1GB: (52428800, 1073741824),
    SIZE_1GB_50GB: (1073741824, 53687091200),
    SIZE_50GB_500GB: (53687091200, 536870912000)
}

FILTER_EXTENSION = "FileExtension"
EXTENSION_TYPE_MEDIA = "Media"
EXTENSION_TYPE_WEB_PAGES = "Web Pages"
EXTENSION_TYPE_ARCHIVES = "Archives"
EXTENSION_TYPE_DOCUMENTS = "Documents"
EXTENSION_TYPE_OTHERS = "Others"
EXTENSION_GROUP_VALUES = {
    EXTENSION_TYPE_MEDIA: ('avi', 'bmp', 'gif', 'jpeg', 'jpg', 'mid', 'mp3',
                           'mp4', 'mpeg', 'mpg', 'png', 'qt', 'wav', 'wmv', 'mov'),
    EXTENSION_TYPE_WEB_PAGES: ('asp', 'aspx', 'htm', 'html', 'jsp', 'mht', 'js', 'css', 'php', 'json'),
    EXTENSION_TYPE_ARCHIVES: ('arj', 'bz2', 'cab', 'cpio', 'gz', 'jar', 'rar', 'tar', 'tgz', 'Z', 'zip'),
    EXTENSION_TYPE_DOCUMENTS: ('csv', 'doc', 'docx', 'dot', 'mpp', 'pdf', 'ppt', 'pptx', 'ps', 'rtf', 'txt',
                               'xls', 'xlsx', 'xlsm', 'pptm', 'docm', 'pdax', 'xml', 'xhtml', 'xps', 'rpt', 'oxps'),
    EXTENSION_TYPE_OTHERS: ('avi', 'bmp', 'gif', 'jpeg', 'jpg', 'mid', 'mp3', 'mp4', 'mpeg', 'mpg', 'png', 'qt',
                            'wav', 'wmv', 'mov', 'asp', 'aspx', 'htm', 'html', 'jsp', 'mht', 'js', 'css', 'php',
                            'json', 'arj', 'bz2', 'cab', 'cpio', 'gz', 'jar', 'rar', 'tar', 'tgz', 'Z', 'zip',
                            'csv', 'doc', 'docx', 'dot', 'mpp', 'pdf', 'ppt', 'pptx', 'ps', 'rtf', 'txt', 'xls',
                            'xlsx', 'xlsm', 'pptm', 'docm', 'pdax', 'xml', 'xhtml', 'xps', 'rpt', 'oxps')
}

FILTER_MODIFIED_TIME = "ModifiedTime"
FILTER_ACCESS_TIME = "AccessTime"
FILTER_CREATED_TIME = "CreatedTime"
FACET_FILTERS = [FILTER_SIZE, FILTER_EXTENSION, FILTER_MODIFIED_TIME, FILTER_ACCESS_TIME, FILTER_CREATED_TIME]
TIME_0_1_YEAR = "0 to 1 Year"
TIME_1_2_YEAR = "1 to 2 Years"
TIME_2_3_YEAR = "2 to 3 Years"
TIME_3_4_YEAR = "3 to 4 Years"
TIME_4_5_YEAR = "4 to 5 Years"
TIME_ABOVE_5_YEAR = "5 Years+"
TIME_RANGE_VALUES = {
    TIME_0_1_YEAR: (0, 31536000),
    TIME_1_2_YEAR: (31536000, 63072000),
    TIME_2_3_YEAR: (63072000, 94608000),
    TIME_3_4_YEAR: (94608000, 126144000),
    TIME_4_5_YEAR: (126144000, 157680000),
    TIME_ABOVE_5_YEAR: (157680000, 1000000000000)
}

# FSO Datasource export fields
DASHBOARDS_CSV_FIELDS = {SIZE_DISTRIBUTION_DASHBOARD: {'AccessTime': 'Accessed', 'CreatedTime': 'Created', 'FileName': 'File name',
                                          'ModifiedTime': 'Modified', 'Size': 'Size', 'Url': 'Path',
                                          'AllowWriteUsername': 'Allow write username',
                                          'AllowModifyUsername': 'Allow modify username',
                                          'AllowFullControlUsername': 'Allow full control username',
                                          'OwnerName': 'Owner name', 'Department': 'Department'},

                         TREE_SIZE_DASHBOARD: {'AccessTime': 'File Access Time', 'Url': 'Path', 'OwnerName': 'File Owner',
                                  'DocumentType': 'DocumentType', 'FileCount_iv': 'Files', 'FolderCount_iv': 'Folders',
                                  'FolderSize_lv': 'Folder Size'},

                         FILE_SECURITY_DASHBOARD: {"Size": "Size", "Url": "Path", "DocumentType": "DocumentType",
                                      "AllowWriteUsername": "Write Access", "AllowModifyUsername": "Modify Access",
                                      "AllowFullControlUsername": "Full Control", "OwnerName": "Owner",
                                      "AllowListUsername": "List Access"},

                         DUPLICATES_DASHBOARD: {"AccessTime": "Access Time", "Url": "File Path", "OwnerName": "File Owner", "Size": "Total Size", "FileName": "File Name"}}

# Activate Datasource management constants
CONFIG_HOST_NAME = "hostname"
CONFIG_USER_NAME = "username"
CONFIG_PASSWORD = "password"
DEFAULT_FILE_COUNT = 20
ONLINE_CRAWL_DS = "LiveCrawlSources"
BACKEDUP_DS = "BackedupSources"
DEFAULT_CSV_NAME = "import_ds_%s.csv"
CSV_HEADER_HOST_NAME = "Server Host Name"
CSV_DATA_SOURCE_NAME = "Data Source Name"
CSV_UNC_SHARE_PATH = "Share Path"
CSV_HEADER_COUNTRY = "Country"
CSV_HEADER_USERNAME = "User Name"
CSV_HEADER_PASSWORD = "Password"
CSV_HEADER_DC_PLAN = "DC Plan"
CSV_HEADER_ACCESS_NODE = "Access Node"
CSV_HEADER_FROM_BACKUP = "Backedup Status"
CSV_HEADER_CRAWL_TYPE = "Crawl Type"
LIVE_CRAWL_TYPE = 1
FROM_BACKUP_CRAWL_TYPE = 2
DEFAULT_BACKUP_STATUS = 0
FROM_BACKUP_STATUS = 1
CSV_HEADERS = [CSV_HEADER_HOST_NAME,
               CSV_DATA_SOURCE_NAME,
               CSV_UNC_SHARE_PATH,
               CSV_HEADER_COUNTRY,
               CSV_HEADER_USERNAME,
               CSV_HEADER_PASSWORD,
               CSV_HEADER_DC_PLAN,
               CSV_HEADER_ACCESS_NODE,
               CSV_HEADER_FROM_BACKUP,
               CSV_HEADER_CRAWL_TYPE]

# Index Server Core Names Prefix
EDISCOVERYLDAP = "eDiscoveryLDAP_"

# Index Server Files That Are Not Backed Up
TLOG = 'tlog'
LOCK = 'lock'

# Index Server Files
CORE_PROPERTIES = 'core.properties'
SEGMENTS = 'segments'

# Index Server Backup Types
INCREMENTAL = "Incremental"
FULL = "Full"
SYNTHETIC_FULL = "Synthetic full"

# FSO Server Details Dictionary key names
CUSTOM_PROPERTY_NAME = 'name'
CUSTOM_PROPERTY_VALUE = 'value'
FSO_SERVER_DETAIL_CHILD_KEY = 'childs'
DATA_SOURCE_PATH_KEY = "path"
FSO_DS_CUSTOM_PROP_KEY = "customProperties"
CUSTOM_PROP_NAME_VALUE_KEY = "nameValues"
FSO_DATA_SOURCE_CRAWL_TYPE = "crawlType"
FSO_DATA_SOURCE_DOCUMENT_COUNT = "documentCount"
FSO_DATA_SOURCE_NAME_KEY = "datasourceName"

# Broken permissions constants
INHERITANCE_SETTINGS = ['OI', 'CI', 'IO', 'NP', 'I']
BASIC_WINDOWS_PERMISSIONS = ['D', 'M', 'RX', 'R', 'W']

# solr.runQuartzAtInterval : "true"
# solr.triggerIntervalSeconds : (String value) <interval in seconds>
INDEX_SERVER_HEALTH_MONITORING_SOLR_COLLECTION = 'indexserverinfo'
INDEX_SERVER_HEALTH_RUN_SCHEDULER_AT_INTERVAL = 'solr.runQuartzAtInterval'
INDEX_SERVER_HEALTH_SUMMARY_DOC_TRIGGER_INTERVAL = 'solr.triggerIntervalSeconds'
# Summary doc will get generated every 1 min
INDEX_SERVER_HEALTH_SUMMARY_DOC_TRIGGER_INTERVAL_IN_MINS = 1
INDEX_SERVER_HEALTH_INDICATORS = {
    'DISK': 'disk',
    'MEMORY': 'mem',
    'CPU': 'cpu'
}
INDEX_SERVER_HEALTH_DISK_SPACE_PERCENTAGE = 'thresholdDiskSpacePercentage'
INDEX_SERVER_HEALTH_DISK_SPACE_BYTES = 'thresholdFreeDiskSpaceBytes'
INDEX_SERVER_HEALTH_CPU_USAGE_MEDIAN_THRESHOLD = 'medianCpuUsageThreshold'
INDEX_SERVER_HEALTH_MAX_CPU_CORES_THRESHOLD = 'maxCpuCoresThreshold'
INDEX_SERVER_HEALTH_MAX_CPU_USAGE_THRESHOLD = 'maxCpuUsageThreshold'

INDEX_SERVER_HEALTH_MEM_USAGE_PERCENTAGE_THRESHOLD = 'heapMemUsagePercentageThreshold'
INDEX_SERVER_HEALTH_MEM_EXCEEDED_TIME = 'heapMemoryExceededTimes'
INDEX_SERVER_HEALTH_MEM_BYTES_THRESHOLD = 'thresholdHeapMemoryBytes'

INDEX_SERVER_HEALTH_DISK_THRESHOLDS = {
    'thresholdFreeDiskSpaceBytes': 1099511627776,
    'thresholdFreeDiskSpacePercentage': 15
}
INDEX_SERVER_HEALTH_MEMORY_THRESHOLDS = {
    'heapMemoryExceededTimes': 50,
    'heapMemUsagePercentageThreshold': 95,
    'indexDirSizeThreshold': 8796093022208,
    'totalDocsThreshold': 1500000000,
    'thresholdHeapMemoryBytes': 33285996544
}
INDEX_SERVER_HEALTH_CPU_THRESHOLDS = {
    'maxCpuCoresThreshold': 16,
    'maxCpuUsageThreshold': 99,
    'medianCpuUsageThreshold': 70,
    'indexDirSizeThreshold': 8796093022208,
    'totalDocsThreshold': 1500000000
}

INDEX_SERVER_HEALTH_ACTION_CODE_CPU_HIGH_INCREASE_VCPUS = 300
INDEX_SERVER_HEALTH_ACTION_CODE_CPU_HIGH_CONTACT_MR_DEV = 330
INDEX_SERVER_HEALTH_ACTION_CODE_MEM_HIGH_INCREASE_JVM_HEAP = 500
INDEX_SERVER_HEALTH_ACTION_CODE_MEM_HIGH_CONTACT_MR_DEV = 550
INDEX_SERVER_HEALTH_ACTION_CODE_LOW_DISK_SPACE = 750
INDEX_SERVER_HEALTH_ACTION_CODE_ADD_A_NODE = 1000

# Unusual file activity constants           
ENCRYPTION_KEY = "ENABLE_ECRYPTION"
CORRUPTION_KEY = "ENABLE_CORRUPTION"
DUMMY_CONFIG_FILE_SECTION = "section"

# Compliance Search constants
DOWNLOAD_FOLDER_NAME = "Export_%s_Download"
DOWNLOAD_FOLDER_PATH = os.path.join(AUTOMATION_DIRECTORY, "Temp", DOWNLOAD_FOLDER_NAME)


# Tenant name constant

ONEDRIVE_TENANT = 'onedrive{0}'
EXCHANGE_TENANT = 'exchange{0}'
SHAREPOINT_TENANT = 'sharepoint{0}'

# Rehydrator Constants
BUCKET_TEST_PROGRESS = "test_case_progress"


class SDGTestSteps(enum.Enum):
    GENERATE_SDG_DATA = 1
    CREATE_CLIENT = 2
    ADD_USER = 3
    PERFORM_BACKUP = 4
    CREATE_INVENTORY = 5
    CREATE_SDG_PLAN = 6
    CREATE_SDG_PROJECT = 7
    CREATE_SDG_DATASOURCE = 8
    PERFORM_SDG_DS_CRAWL = 9
    PERFORM_REVIEW = 10
    PERFORM_CLEANUP = 11
    ADD_MAILBOX = 12


class RAServiceCatalogSteps(enum.Enum):
    VALIDATE_TENANT_WO_SUB = 1
    VALIDATE_TENANT_W_SUB_NO_BKP = 2
    VALIDATE_TENANT_W_SUB = 3
    VALIDATE_RA_OD_CONFIGURE = 4
    VALIDATE_RA_EXCH_CONFIGURE = 5
    VALIDATE_RA_MANAGE = 6


class RATab(enum.Enum):
    OVERVIEW = "label.overview"
    PROJECTS = "label.projects"
    ENTITY_MANAGER = "label.entitymanager"


class CITestSteps(enum.Enum):
    CREATE_COMPANY = 1
    CHANGE_PASSWORD = 2
    START_TRIAL = 3
    ENABLE_CI = 4
    ADD_COMPLIANCE_ROLE = 5
    CREATE_CLIENT = 6
    ADD_USER = 7
    PERFORM_BACKUP = 8
    CONTENT_INDEXING = 9
    CREATE_EXPORT_SET = 10


def is_step_complete(bucket, current_step):
    """checks if a given steps is complete for test_case_progress rehydrator bucket"""
    completed_steps = bucket.get()
    current_step = 2 ** current_step
    return completed_steps & current_step == current_step


def set_step_complete(bucket, current_step):
    """Updates a completed step to test_case_progress rehydrator bucket"""
    current_step = 2 ** current_step
    steps_completed = bucket.get()
    if not steps_completed & current_step == current_step:
        bucket.set(steps_completed + current_step)


# Navigation constant
EDISCOVERY = 'ediscovery'
PROFILE = 'profile'
GDPR = 'gdpr'
CASE_MANAGER = 'caseManager'
ANALYTICS = 'analytics'
GETTING_STARTED = 'gettingStarted'
