# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" It contains constants for kubernetes

Classes defined :

    ErrorReasonRepo     :   Enum of JPRs for different Kubernetes job failures

    LogLineRepo         :   Enum of log lines for backup and restore scenarios

    DebugFiles          :   Enum for debug file names

"""

# json fields for kubectl output
from enum import Enum

FIELD_STATUS = 'status'
FIELD_CONTAINER_STATUS = 'containerStatuses'
FIELD_CONDITIONS = 'conditions'
FIELD_READY = 'ready'
FIELD_READY_PRE = 'Ready'
FIELD_ITEMS = 'items'
FIELD_VERSION = 'apiVersion'
FIELD_METADATA = 'metadata'
FIELD_NAME = 'name'
FIELD_NAMESPACE = 'namespace'
FIELD_KIND = 'kind'
FIELD_LABELS = 'labels'
FIELD_DEPLOYMENT = 'Deployment'
FIELD_SPEC = 'spec'
FIELD_TEMPLATE = 'template'
FIELD_CONTAINERS = 'containers'
FIELD_IMAGE = 'image'
FIELD_MIN_REPLICA = 'minReplicas'
FIELD_MAX_REPLICA = 'maxReplicas'
FIELD_AVAIL_REPLICA = 'availableReplicas'
FIELD_READY_REPLICA = 'readyReplicas'
FIELD_BEHAVIOR = 'behavior'
FIELD_METRICS = 'metrics'
FIELD_STATUS_RUNNING = 'Running'
FIELD_STATUS_STOPPED = 'Stopped'
FIELD_CONFIG_MAP = 'ConfigMap'
FIELD_CONFIG_JSON = 'config.json'
FIELD_DATA = 'data'
FIELD_RESOURCE = 'resource'
FIELD_TARGET = 'target'
FIELD_UTILIZATION = 'Utilization'
FIELD_AVG_UTILIZATION = 'averageUtilization'
FIELD_TYPE = 'type'
FIELD_CUR_REPLICAS = 'currentReplicas'
FIELD_DES_REPLICAS = 'desiredReplicas'
FIELD_SCALE_TIME = 'lastScaleTime'
FIELD_CUR_METRICS = 'currentMetrics'
FIELD_CURRENT = 'current'

# AKS cluster related fields
FIELD_POWER_STATE = 'powerState'
FIELD_CODE = 'code'

# Fields for RestoreModifier
FIELD_SELECTORS = 'selectors'
FIELD_MODIFIERS = 'modifiers'

# YAML FILE RELATED
EXTRACTING_GITHUB_YAML_URL = "https://raw.githubusercontent.com/liuyt1/yaml/main/extracting.yaml"
EXTRACTING_APP_NAME = 'cvextractor'

# predefined keys for automation
KEY_SCALED_UP = "ScaleUpTime"
KEY_SCALED_DOWN = "ScaleDownTime"
KEY_TIME = "Timestamp"
KEY_PODS = "Pods"
KEY_POD_METRICS = 'POD_Metrics'
KEY_NODE_METRICS = 'NODE_Metrics'
KEY_POD_CPU = 'CPU(cores)'
KEY_POD_MEMORY = 'MEMORY(bytes)'
KEY_POD_NAME = 'NAME'
KEY_POD_CPU_MAX = 'MAX CPU(cores)'
KEY_POD_MEMORY_MAX = 'MAX MEMORY(bytes)'
KEY_POD_CPU_MIN = 'MIN CPU(cores)'
KEY_POD_MEMORY_MIN = 'MIN MEMORY(bytes)'
KEY_POD_CPU_AVG = 'AVG CPU(cores)'
KEY_POD_MEMORY_AVG = 'AVG MEMORY(bytes)'
KEY_NODE_CPU_PERCENT = 'CPU%'
KEY_NODE_CPU_PERCENT_MAX = 'MAX CPU%'
KEY_NODE_CPU_PERCENT_MIN = 'MIN CPU%'
KEY_NODE_CPU_PERCENT_AVG = 'AVG CPU%'
KEY_NODE_MEMORY_PERCENT = 'MEMORY%'
KEY_NODE_MEMORY_PERCENT_MIN = 'MIN MEMORY%'
KEY_NODE_MEMORY_PERCENT_MAX = 'MAX MEMORY%'
KEY_NODE_MEMORY_PERCENT_AVG = 'AVG MEMORY%'
KEY_CPU_UNIT = 'm'  # millicores
KEY_MEMORY_UNIT = 'Mi'  # Megabytes

# CS DB
DB_FIELD_COMMVAULT = r'\COMMVAULT'
DB_FIELD_COMMSERV = 'commserv'
AUTOMATION_POD_METRICS_TBL = 'Automation_Pod_Metrics'
TABL_FIELD_BUILDID = 'BuildId'
TABL_FIELD_TIMESTAMP = 'TimeStamp'
TABL_FIELD_NAME = 'Name'
TABL_FIELD_CPUINMILLICORES = 'CpuinMilliCores'
TABL_FIELD_MEMORYINMIB = 'MemoryinMiB'
TABL_FIELD_CSVERSION = 'CSVersion'
AUTOMATION_POD_METRICS_TBL_SCRIPT = """IF OBJECT_ID('Automation_Pod_Metrics', 'U') IS NULL
	CREATE TABLE Automation_Pod_Metrics (
		BuildId int,
		CSVersion varchar(50),
		TimeStamp int,
		Name varchar(255),
		CpuinMilliCores int,
		MemoryinMiB int
	);"""

# performance open datasource & Solr fields
FIELD_TYPE_INT = "int"
FIELD_TYPE_STRING = "string"
FIELD_TYPE_LONG = "long"
FIELD_TYPE_DATE = "date"
FIELD_TYPE_FLOAT = "tdouble"
FIELD_TYPE_DATE_TIME = "utcdatetime"
REPORTS_FOLDER_PATH = 'ExportedPath'

POD_DATA_SOURCE_COLUMN = [
    TABL_FIELD_BUILDID,
    TABL_FIELD_CSVERSION,
    TABL_FIELD_TIMESTAMP,
    TABL_FIELD_NAME,
    TABL_FIELD_CPUINMILLICORES,
    TABL_FIELD_MEMORYINMIB]
POD_DATA_SOURCE_COLUMN_TYPES = [
    FIELD_TYPE_INT,
    FIELD_TYPE_STRING,
    FIELD_TYPE_DATE,
    FIELD_TYPE_STRING,
    FIELD_TYPE_INT,
    FIELD_TYPE_INT
]
ROLE_DATA_ANALYTICS = "Data Analytics"
SCHEMA_FIELDS = {
    "fieldName": "",
    "type": "string",
    "indexed": True,
    "stored": True,
    "multiValued": False,
    "searchDefault": True,
    "autocomplete": False
}


# VolumeSnapshotClasses object constants
class VolumeSnapshotClasses(Enum):
    """Constant values to use VolumeSnapshotClasses objects"""

    GROUP = "snapshot.storage.k8s.io"
    PLURAL = "volumesnapshotclasses"


# Constant labels
class AutomationLabels(Enum):
    """Constant labels used in automation"""
    CV_POD_LABEL = "cv-backup-admin"
    CV_POD_SELECTOR = "cv-backup-admin="
    AUTOMATION_LABEL = "k8s-automation"
    AUTOMATION_SELECTOR = "k8s-automation="


# Error reasons as constants for Kubernetes jobs
class ErrorReasonRepo(Enum):
    """Repository of Error Reasons for Kubernetes Jobs"""
    # 0 : Application Name, 1 : AccessNode Name,
    UNABLE_TO_CREATE_NEW_APPLICATION = "Unable to create new application [{0}] from access node [{1}]. [Could not" \
                                       " create Application"

    ERROR_RESTORING_DATA = "Unable to write to the virtual disk"

# Common Log lines to check for Kubernetes log files
class LogLineRepo(Enum):
    """Repository of Log Lines to check"""
    RESTORE_FAILURE_NAMESPACE_EXISTS = r"manifest not found for resource \[[a-z0-9\-]*\:[a-z0-9\-]*\]"
    RESTORE_FAILURE_APPLICATION_EXISTS = r"Application \[[A-Za-z0-9\`\-]*\] already exists"
    RESTORE_APP_IN_SYSTEM_NAMESPACE_EXISTS = r"Application \[[A-Za-z0-9\`\-]*\] already exists in system namespace"

    # 0: Missing resource name, 1: Namespace, 2: kind, 3: Application name
    MISSING_CONFIG = "Resource name:{0} namespace:{1} kind:{2} is missing during the backup of app" \
                     " {3}. Restore may succeed but the application may not start."

    # 0: cpu limit, 1 memory limit, 2: cpu request 3: memory request
    WORKER_POD_RESOURCES = '"resources":{{"limits":{{"cpu":"{0}","memory":"{1}"}},"requests":{{"cpu":"{2}",' \
                           '"memory":"{3}"}}}}'

    SNAP_FAIL_LIVE_VOLUME_FALLBACK = "Snapshot creation failed. Backing up from live volume"

    PVC_FAIL_LIVE_VOLUME_FALLBACK = "Backing up from live volume as PVC"

    WORKER_POD_YAML = "Creating Worker Pod"
    BACKUP_KFC1 = "K8s backup version=\[V2\]"
    BACKUP_KFC2 = "Initializing KFCClient backup manager"

    BACKUP_V3_1 = "K8s backup version=\[V3\]"
    BACKUP_V3_2 = "BackupVMFileCollectionViaExtension"
    BACKUP_V3_3 = "StartBackupExtension"

    PVC_YAML = "Creating PVC from Snapshot"

    SNAPSHOT_YAML = "Creating cv snapshot object with config"


# Debug files for Kubernetes jobs
class DebugFiles(Enum):
    """Debug File names for Kubernetes"""
    WORKER_POD_CREATE = "/tmp/k8s_worker_created.sleep"
    WORKER_POD_DELETE = "/tmp/k8s_worker_deleting.sleep"


# Kubernetes additional settings constants
class KubernetesAdditionalSettings(Enum):
    """Additional Settings for Kubernetes"""
    CATEGORY = "VirtualServer"
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"
    SHOW_SYSTEM_NAMESPACES = "bK8sShowSystemNamespaces"
    WORKER_CPU_MAX = "sK8sWorkerCpuMax"
    WORKER_CPU_MIN = "sK8sWorkerCpuMin"
    WORKER_MEM_MIN = "sK8sWorkerMemMin"
    WORKER_MEM_MAX = "sK8sWorkerMemMax"
    HELM_BACKUP = "bK8sHelmChartBackup"
    RESTORE_MODIFIER = "bK8sEnableRestoreModifiers"
    SERVICE_CATALOG_MODIFIER = "bK8sEnableServiceCatalogModifier"
    LIVE_VOLUME_FALLBACK = "bK8sSnapFallBackLiveBkp"
    WORKER_NAMESPACE = "sK8sWorkerNamespace"


class RestoreModifierConstants(Enum):
    """Constants used in RestoreModifier CRD"""
    GROUP = "k8s.cv.io"
    VERSION = "v1"
    KIND = "RestoreModifier"
    NAMESPACE = "cv-config"
    PLURAL = "restoremodifiers"

    # Fields for Selector
    SELECTOR_ID = 'id'
    SELECTOR_NAME = 'name'
    SELECTOR_NAMESPACE = 'namespace'
    SELECTOR_KIND = 'kind'
    SELECTOR_LABELS = 'labels'
    SELECTOR_FIELD = 'field'

    # Fields for selector.field
    SELECTOR_FIELD_PATH = 'path'
    SELECTOR_FIELD_VALUE = 'value'
    SELECTOR_FIELD_EXACT = 'exact'
    SELECTOR_FIELD_CRITERIA = 'criteria'

    # Fields for Modifier
    MODIFIER_SELECTOR_ID = 'selectorId'
    MODIFIER_ACTION = 'action'
    MODIFIER_VALUE = 'value'
    MODIFIER_NEW_VALUE = 'newValue'
    MODIFIER_PATH = 'path'
    MODIFIER_PARAMETERS = 'parameters'


class CVTaskConstants(Enum):
    """Constants used in CVTask manifest"""
    GROUP = 'k8s.cv.io'
    VERSION = 'v1'
    KIND = 'CvTask'
    PLURAL = 'cvtasks'

    FIELD_PRE_BACKUP_SNAPSHOT = 'preBackupSnapshot'
    FIELD_POST_BACKUP_SNAPSHOT = 'postBackupSnapshot'

    TYPE_COMMAND = 'Command'
    TYPE_LOCAL_SCRIPT = 'LocalScript'
    TYPE_SCRIPT_TEXT = 'ScriptText'


class CVTaskSetConstants(Enum):
    """Constants used in CVTaskSet manifest"""
    GROUP = 'k8s.cv.io'
    VERSION = 'v1'
    KIND = 'CvTaskSet'
    PLURAL = 'cvtasksets'

    FIELD_APP_NAME = 'appName'
    FIELD_APP_NAMESPACE = 'appNamespace'
    FIELD_LABEL_SELECTORS = 'labelSelectors'
    FIELD_TASKS = 'tasks'

    FIELD_CV_TASK_ID = 'id'
    FIELD_CV_TASK_NAME = 'cvTaskName'
    FIELD_CV_TASK_NAMESPACE = 'cvTaskNamespace'
    FIELD_CONTAINER_NAME = 'containerName'
    FIELD_EXECUTION_LEVEL = 'executionLevel'
    FIELD_IS_DISABLED = 'isDisabled'
    FIELD_EXECUTION_ORDER = 'executionOrder'

    EXE_LEVEL_APPLICATION = 'Application'
    EXE_LEVEL_NAMESPACE = 'Namespace'
    EXE_LEVEL_CLUSTER = 'Cluster'
