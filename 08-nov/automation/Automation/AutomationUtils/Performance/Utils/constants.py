# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for maintaining Constants related to performance monitor of process/clients.

    JobTypes: Class for maintaining various job types

    JobPhases: Class for maintaining various job phases for job

    JobPhaseNames:  Class for maintaining individual job phase names

    JobStatus: Class for specifying different job status

    Binary:  Binary names for a commvault process/Service

    WindowsProcessCounters:   Typeperf counters for the process

    WindowsMachineCounters:   TypePerf counters for the machine

    UnixProcessCounters:    Top command output position for process stats

    UnixMachineCounters:   Top command output position for Machine stats

    CustomCounters :    Specifies the custom counter for the process/Machine

    Platforms: Class for specifying different platforms(Windows/Unix)

    CounterTypes: Class for specifying different counter types

    GeneralConstants: Class for specifying general constants

    TimerIntervals: Class for specifying different time intervals used in performance monitoring


"""
import os
import socket
from AutomationUtils.constants import AUTOMATION_UTILS_PATH, AUTOMATION_DIRECTORY


class CustomCounters():
    """Custom counters which needs to be monitored"""
    CAPTURE_NETWORK_PORT_USAGE = True


class UnixMachineCounters():
    """Top command output position for Machine stats"""
    MACHINE_CPU = "$$2"
    MACHINE_AVAILABLE_MEMORY_IN_MB = "$$37"
    MACHINE_FREE_MEMORY_IN_MB = "$$23"
    MACHINE_CPU_FIFTEEN_MIN_LOAD_AVERAGE = "$$355"
    # Add all counters to below list. we need this attribute to remove invalid
    # counters in case of mixed environment[Example : MA - Windows , Source
    # client : Linux] and also if we need to capture all
    COUNTER_VALUES = [
        MACHINE_CPU,
        MACHINE_FREE_MEMORY_IN_MB,
        MACHINE_AVAILABLE_MEMORY_IN_MB,
        MACHINE_CPU_FIFTEEN_MIN_LOAD_AVERAGE]


class UnixProcessCounters():
    """Top command output position for process stats"""
    PROCESS_HANDLE_COUNT = "$255"
    PROCESS_THREAD_COUNT = "$256"
    PROCESS_VIRTUAL_BYTES = "$5"
    PROCESS_WORKING_SET_PRIVATE = "$6"
    PROCESS_WORKING_SET = "$7"
    PROCESS_PID = "$1"
    PROCESS_CPU = "$9"
    # Add all counters to below list. we need this attribute to remove invalid
    # counters in case of mixed environment[Example : MA - Windows , Source
    # client : Linux] and also if we need to capture all
    COUNTER_VALUES = [
        PROCESS_HANDLE_COUNT,
        PROCESS_THREAD_COUNT,
        PROCESS_VIRTUAL_BYTES,
        PROCESS_WORKING_SET_PRIVATE,
        PROCESS_WORKING_SET,
        PROCESS_PID,
        PROCESS_CPU]


class WindowsProcessCounters():
    """Typeperf counters for the process"""
    PROCESS_HANDLE_COUNT = r"\Process({pname}*)\Handle Count"
    PROCESS_THREAD_COUNT = r"\Process({pname}*)\Thread Count"
    PROCESS_PRIVATE_BYTES = r"\Process({pname}*)\Private Bytes"
    PROCESS_VIRTUAL_BYTES = r"\Process({pname}*)\Virtual Bytes"
    PROCESS_WORKING_SET = r"\Process({pname}*)\Working Set"
    PROCESS_PID = r"\Process({pname}*)\ID Process"
    PROCESS_WORKING_SET_PRIVATE = r"\Process({pname}*)\Working Set - Private"
    PROCESS_CPU = r"\Process({pname}*)\% Processor Time"
    # Add all counters to below list. we need this attribute to remove invalid
    # counters in case of mixed environment[Example : MA - Windows , Source
    # client : Linux] and also if we need to capture all
    COUNTER_VALUES = [
        PROCESS_HANDLE_COUNT,
        PROCESS_THREAD_COUNT,
        PROCESS_VIRTUAL_BYTES,
        PROCESS_WORKING_SET_PRIVATE,
        PROCESS_WORKING_SET,
        PROCESS_PID,
        PROCESS_CPU,
        PROCESS_PRIVATE_BYTES]


class WindowsMachineCounters():
    """Typeperf counters for the machine"""
    MACHINE_CPU = r"\Processor(_Total)\% Processor Time"
    MACHINE_AVAILABLE_MEMORY_IN_MB = r"\Memory\available mbytes"
    MACHINE_PROCESSOR_QUEUE_LENGTH = r"\System\Processor Queue Length"
    MACHINE_DISK_AVG_QUEUE_LENGTH = r"\PhysicalDisk(_Total)\Avg. Disk Queue Length"
    # Add all counters to below list. we need this attribute to remove invalid
    # counters in case of mixed environment[Example : MA - Windows , Source
    # client : Linux] and also if we need to capture all
    COUNTER_VALUES = [
        MACHINE_CPU,
        MACHINE_AVAILABLE_MEMORY_IN_MB,
        MACHINE_PROCESSOR_QUEUE_LENGTH,
        MACHINE_DISK_AVG_QUEUE_LENGTH]


class Platforms():
    """Class for specifying different platforms(Windows/Unix)"""
    Windows = 'Windows'
    Unix = 'Unix'


class Binary():
    """Binary names for a commvault process/Service"""
    I_FIND = {Platforms.Windows: "IFind.exe"}
    CL_BACKUP = {Platforms.Windows: "CLBackup.exe"}
    DATA_CUBE = {Platforms.Windows: "DataCube.exe", Platforms.Unix: "CVAnalytics"}
    # for content extractor, unix will have process name as Java. user can have multiple java process so adding unique
    # keyword to filter this process
    CONTENT_EXTRACTOR = {Platforms.Windows: "CVContentPreview.exe", Platforms.Unix: "DcontentExtractor"}
    MESSAGE_QUEUE = {Platforms.Windows: "CvMessageQueue.exe", Platforms.Unix: "MessageQueue"}
    EXPORTER = {Platforms.Windows: "exporter2.exe", Platforms.Unix: "cvexporter2"}
    PYTHON = {Platforms.Windows: "python.exe", Platforms.Unix: "python"}
    SEARCH_ENGINE = {Platforms.Windows: "tomcat.exe"}
    CVD = {Platforms.Windows: "cvd.exe", Platforms.Unix: "cvd"}
    AUX_COPY = {Platforms.Windows: "AuxCopy.exe", Platforms.Unix: "auxCopy"}
    AUX_COPY_MGR = {Platforms.Windows: "AuxCopyMgr.exe", Platforms.Unix: "AuxCopyMgr"}
    CVODS = {Platforms.Windows: "CVODS.exe", Platforms.Unix: "CVODS"}
    CVCI_ANALYTICS = {Platforms.Windows: "CVCIAnalytics.exe", Platforms.Unix: "CVCIAnalytics"}
    CV_DISTRIBUTOR = {Platforms.Windows: "CVDistributor.exe", Platforms.Unix: "CVDistributor"}
    CL_RESTORE = {Platforms.Windows: "CLRestore.exe", Platforms.Unix: "clRestore"}
    INDEX_GATEWAY = {Platforms.Windows: "dotnet.exe", Platforms.Unix: "dotnet"}


class GeneralConstants():
    """Class for specifying general constants"""

    TIMER_PHASE = "TimerPhase"
    TIMER_BASED_MONITOR = "Time Based Monitor"
    # cache keywords
    DRIVE_CACHE = "_Drive_stats_folder"
    MACHINE_OBJ_CACHE = "_Machine_obj"
    CLIENT_OBJ_CACHE = "_Client_obj"

    # Timer
    LAST_EXECUTION_TIME = "LastExecutionTime"
    PORT_USAGE_STATS = "portusage"

    # folder path on controller. This folder will be shared so that exported performance graph can be viewed directly
    # by clicking href tag in report mail
    # it is being used by multiple files and multiple threads. Hence didnt go for drive selection from optionselector
    FOLDER_NAME = "Automation_Performance_Stats"
    CONTROLLER_FOLDER_PATH = os.path.join(AUTOMATION_DIRECTORY, "Temp", FOLDER_NAME)
    HOST_NAME = socket.gethostname()
    CONTROLLER_SHARE_FOLDER_PATH = f"\\\\{socket.gethostbyname(HOST_NAME)}\\{FOLDER_NAME}"
    # stats file older than 7 days will get deleted from controller
    STATS_FILE_DELETE_DAYS = 7

    # Parameters
    CLIENT_PARAM = "client"
    BINARY_PARAM = "binary"
    BINARY_PID_PARAM = "binaryprocessids"
    COUNTERS_PARAM = "counters"
    PLATFORM_PARAM = "platform"
    STATS_FOLDER_PARAM = "statsfolder"
    STATS_FILE_PARAM = "statsfile"
    COMMAND_LINE_PARAM = "cmdlineparams"
    COUNTER_TYPE_PARAM = "countertype"
    PORT_USAGE_PARAM = "portusagestats"
    DATA_SOURCE_NAME_PARAM = "DataSourceName"
    PHASE_NAME_PARAM = "JobPhase"
    CONFIGURATIONS_NAME_PARAM = "MonitorConfigurations"
    EXPORT_REPORT_PARAM = "PerformanceGraphLocation"
    CSV_REPORT_PARAM = "PerformanceOutputLocation"
    MIN_MAX_PARAM = "CounterValues(Min/Max)"
    USERNAME_PARAM = "client_username"
    PASSWORD_PARAM = "client_password"

    # Process command line
    CVODS_APP_NAME = 'appname'
    JOB_ID_CMD_LINE_PARAM = "-j "
    JOB_TOKEN_CMD_LINE_PARAM = "-jt "
    JOB_ID_CMD_LINE_PARAM_OTHER = "-c "
    ANALYTICS_MGR_SERVICE_NAME = 'AnalyticsMgrService'
    INDEX_SERVER_SERVICE_NAME = "IndexServer"
    INDEX_GATEWAY_COMMAND_LINE_KEYWORD = 'CvIndexGateway.dll'

    # Email constants
    EMAIL_NODE_NAME = "email"
    RECEIVER_NODE_VALUE = "receiver"

    # File / Folder and Registry
    BASE_FOLDER = "Base"
    CI_SERVER_SERVICE = "GxSearchServer"
    WINDOWS_NEW_LINE = "\r\n"
    PYTHON_NEW_LINE = "\n"
    FILE_WRITE_MODE = "w"
    FILE_READ_MODE = "r"
    CONTROLLER_MACHINE_CONFIG_JSON_FILE_NAME = "Machine_Hardware_Configs.Json"
    CONTROLLER_PERFORMANCE_CONFIG_JSON_FILE_NAME = "Performance_Job_Configs.Json"
    CONTROLLER_PERFORMANCE_JOB_DETAILS_JSON_FILE_NAME = "Performance_Job_Details.Json"
    CONTROLLER_REPORTS_FOLDER_NAME = "Reports"
    CONTROLLER_EXPORT_HTML_FOLDER_NAME = "ExportedHtml"
    REPORTS_FILE_NAME = "Performance Reports"
    COMMAND_PROMPT_BINARY = "cmd.exe"
    COUNTERS_TEXT_FILE = "_Counters.txt"
    COUNTERS_BASH_FILE = "_Counters.bash"
    STATS_OUTPUT_TEXT_FILE = "_Output.csv"
    TYPEPERF_EXE = "typeperf.exe"
    TYPEPERF_TIME_STAMP_HEADER = "(PDH-CSV 4.0)"
    BASH_TIME_STAMP_HEADER = "Time"
    BASH_EXE = "bash"
    REGISTRY_DWORD = "DWord"
    PERFMON_HEADER_PID_REG_KEY = "ProcessNameFormat"
    PERFMON_REGISTRY = r"HKLM:\SYSTEM\CurrentControlSet\Services\PerfProc\Performance"
    PERFMON_HEADER_WITH_PID_ON = 2

    # Automation Report constants
    KEY_THROUGHPUT_WRITE = "Throughput Write(GB/H)"
    KEY_THROUGHPUT_READ = "Throughput Read(GB/H)"
    KEY_THROUGHPUT_DELETE = "Throughput Delete(GB/H)"
    PROCESS_FILTER_ATTRIBUTE = "AutomationFilters.filter.include."
    MACHINE_FILTER_ATTRIBUTE = "AutomationFilterss.filter.include."
    XML_REPORT_PAGE = 'Page'
    XML_REPORT_PAGE_NAME = 'pageName'
    MACHINE_REPORT_PAGE = 'MachineStats'
    PROCESS_REPORT_PAGE = 'ProcessStats'
    POD_REPORT_PAGE = 'PodStats'
    REPORT_EXPORT_TYPE = "html"
    REPORT_XML = os.path.join(
        AUTOMATION_UTILS_PATH,
        "Performance",
        "Utils",
        "templates",
        "Performance_Automation_Reports.xml")
    HANDLER_NAME = "default"
    DATA_SOURCE_ID_PARAM = "dsId"
    HANDLER_ID_PARAM = "handlerId"
    DATA_SOURCE_ID_XML_FIND = f"./dataSets/dataSet/DataSet/dCubeDataSet/{DATA_SOURCE_ID_PARAM}"
    HANDLER_ID_XML_FIND = f"./dataSets/dataSet/DataSet/dCubeDataSet/dsHandler/{HANDLER_ID_PARAM}"
    EMAIL_SUBJECT = "Performance Automation Report"
    LOGO_FILE = os.path.join(
        AUTOMATION_UTILS_PATH,
        "Performance",
        "Utils",
        "templates",
        "logo.jpg")
    HEADING_COMMSERV_DETAILS = "Commserv Details"
    HEADING_MACHINE_CONFIG = "Machine Configuration Details"
    HEADING_MONITORED_CONFIG = "Monitored Performance Stats Results"
    HEADING_JOB_DETAILS = "Job Details"
    HEADING_JOB_EVENTS = "Job Events"
    HEADING_PAST_JOB_HISTORY = "Past Job History"
    HEADING_DATA_SOURCE_DETAILS = "DataSource Details"
    HEADING_EXTRACT_DURATION_DETAILS = "FileType Extract Duration Details"

    # Failure threshold controls
    PUSH_ERROR_THRESHOLD = 5
    FILE_DOWNLOAD_ERROR_THRESHOLD = 5
    MONITOR_THREAD_ERROR_THRESHOLD = 5
    REMOTE_CLIENT_PROCESS_START_THRESHOLD = 5
    JOB_DETAILS_FETCH_THRESHOLD = 5
    # Process
    PUSH_THREAD_NAME = "DataSource_Push_Thread"
    UNIX_PROCESS_BASH_FILE_NAME = "GetProcessPerformanceStats.bash"
    UNIX_MACHINE_BASH_FILE_NAME = "GetMachinePerformanceStats.bash"
    UNIX_PROCESS_BASH_SCRIPT = os.path.join(AUTOMATION_UTILS_PATH, "Scripts", "UNIX", UNIX_PROCESS_BASH_FILE_NAME)
    UNIX_MACHINE_BASH_SCRIPT = os.path.join(AUTOMATION_UTILS_PATH, "Scripts", "UNIX", UNIX_MACHINE_BASH_FILE_NAME)

    # DataSource constants
    ZERO_VALUE_ROWS_SKIP = False
    SOLR_INTEGER_FIELD_SUFFIX = "_i"
    Process_Data_Source_Name = "AutomationJobPerformance_Process"
    Machine_Data_Source_Name = "AutomationJobPerformance_Machine"
    Pod_Data_Source_Name = "Automation_Pod_Metrics"
    Job_Details_Data_Source_Name = "AutomationJobPerformance_JobDetails"
    Machine_Config_Data_Source_Name = "AutomationJobPerformance_MachineConfig"
    Automation_performance_Report_Name = "Performance_Automation_Reports"
    NETSTAT_STATE_LIST_UNIX = [
        'fin-wait-2_i',
        'fin-wait-1_i',
        'established_i',
        'time-wait_i',
        'closed_i',
        'close-wait_i',
        'listening_i',
        'closing_i',
        'UDP_i']
    NETSTAT_STATE_LIST_WINDOWS = [
        'FinWait2_i',
        'FinWait1_i',
        'Bound_i',
        'Closed_i',
        'CloseWait_i',
        'Closing_i',
        'Established_i',
        'TimeWait_i',
        'Listen_i',
        'UDP_i']
    COLUMN_NET_STATS = "NetStat Details"
    COLUMN_FILE_TYPE = "File Types"
    COLUMN_EXTRACT_DURATION_STATS = "Extract Duration Stats"
    COLUMN_COMMSERV_NAME = 'Commserv Name'
    COLUMN_COMMSERV_VERSION_REPORT = 'Commserv Version'
    COLUMN_MONITOR_TYPE = "Performance Monitor Type"
    COLUMN_BUILD_ID = "BuildId"
    COLUMN_TIME = "Time"
    COLUMN_BINARY = "Binary"
    COLUMN_HANDLE_COUNT = "HandleCount"
    COLUMN_THREAD_COUNT = "ThreadCount"
    COLUMN_PRIVATE_BYTES = "PrivateBytes"
    COLUMN_WORKING_SET = "WorkingSet"
    COLUMN_WORKING_SET_PRIVATE = "WorkingSetPrivate"
    COLUMN_VIRTUAL_BYTES = "VirtualBytes"
    COLUMN_PROCESS_ID = "ProcessId"
    COLUMN_MACHINE_NAME = "MachineName"
    COLUMN_CLIENT_NAME = "ClientName"
    COLUMN_MACHINE_CPU_USAGE = "CPUusage"
    COLUMN_MACHINE_AVAILBLE_MEMORY = "MemoryAvailableinMB"
    COLUMN_MACHINE_FREE_MEMORY = "MemoryFreeinMB"
    COLUMN_PROCESSOR_QUEUE_LENGTH = "ProcessorQueueLength"
    COLUMN_DISK_QUEUE_LENGTH = "AvgDiskQueueLength"
    COLUMN_MACHINE_CPU_FIFTEEN_MIN_LOAD_AVERAGE = "LoadAvg15Mins"
    COLUMN_COMMSERV_VERSION = "CSVersion"
    COLUMN_PLATFORM = "Platform"
    COLUMN_CPU_MODEL = "CPUModel"
    COLUMN_NO_OF_CORES = "NumberOfCores"
    COLUMN_LOGICAL_PROCESSORS = "NumberOfLogicalProcessors"
    COLUMN_OS_BIT = "OSArchitecture"
    COLUMN_MAX_CLOCK_SPEED = "MaxClockSpeed"
    COLUMN_RAM_SIZE = "RAM"
    COLUMN_OS = "OS"
    COLUMN_OS_FLAVOUR = "OSFlavour"
    COLUMN_STORAGE = "Storage"
    COLUMN_JOB_ID = "JobId"
    COLUMN_JOB_TYPE = "JobType"
    COLUMN_JOB_STATUS = "JobStatus"
    COLUMN_JOB_START = "StartTime"
    COLUMN_JOB_END = "EndTime"
    COLUMN_JOB_EVENTS = "JobEvents"
    COLUMN_JOB_DURATION = "JobDurationinMins"
    COLUMN_JOB_CONFIG = "JobConfig"
    COLUMN_COUNTERS = "Counters"
    COLUMN_DATA_SOURCE_NAME = "data_source_name"
    COLUMN_CLIENT_ID = 'ClientId'
    COLUMN_DS_NAME = "DataSource"
    COLUMN_INDEXING_SPEED = 'Docs Indexed per hour'

    # Dynamic column for job details data source
    DYNAMIC_COLUMN_AUTOMATION_JOB_TYPE = "AutomationJobType_i"
    DYNAMIC_COLUMN_TOTAL_DOCS = "TotalDocs_l"
    DYNAMIC_COLUMN_SUCCESS_DOCS = "SuccessDocs_l"
    DYNAMIC_COLUMN_FAILED_DOCS = "FailedDocs_l"
    DYNAMIC_COLUMN_SKIPPED_DOCS = "SkippedDocs_l"
    DYNAMIC_COLUMN_CA_SUCCESS_DOCS = "CASuccessDocs_l"
    DYNAMIC_COLUMN_CA_FAILED_DOCS = "CAFailedDocs_l"
    DYNAMIC_COLUMN_SOURCE_NAME = "SourceName_s"
    DYNAMIC_COLUMN_SOURCE_SIZE = "SourceSize_s"

    # Dynamic column for machine details data source
    DYNAMIC_COLUMN_THROUGH_PUT_READ = "ThroughPutRead_s"
    DYNAMIC_COLUMN_THROUGH_PUT_WRITE = "ThroughPutWrite_s"
    DYNAMIC_COLUMN_THROUGH_PUT_DELETE = "ThroughPutDelete_s"

    # Solr field types
    FIELD_TYPE_INT = "int"
    FIELD_TYPE_STRING = "string"
    FIELD_TYPE_LONG = "long"
    FIELD_TYPE_DATE = "date"
    FIELD_TYPE_FLOAT = "tdouble"
    FIELD_TYPE_DATE_TIME = "utcdatetime"

    # DataSource details
    ROLE_DATA_ANALYTICS = "Data Analytics"
    MACHINE_CONFIG_DATA_SOURCE_COLUMN = [
        COLUMN_COMMSERV_VERSION,
        COLUMN_BUILD_ID,
        COLUMN_MACHINE_NAME,
        COLUMN_CLIENT_NAME,
        COLUMN_CPU_MODEL,
        COLUMN_NO_OF_CORES,
        COLUMN_LOGICAL_PROCESSORS,
        COLUMN_OS_BIT,
        COLUMN_OS,
        COLUMN_OS_FLAVOUR,
        COLUMN_MAX_CLOCK_SPEED,
        COLUMN_RAM_SIZE,
        COLUMN_STORAGE]
    MACHINE_CONFIG_DATA_SOURCE_COLUMN_TYPES = [
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_INT,
        FIELD_TYPE_INT,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_INT,
        FIELD_TYPE_INT,
        FIELD_TYPE_STRING]
    PROCESS_DATA_SOURCE_COLUMN = [
        COLUMN_COMMSERV_VERSION,
        COLUMN_PLATFORM,
        COLUMN_BUILD_ID,
        COLUMN_BINARY,
        COLUMN_MACHINE_NAME,
        COLUMN_PROCESS_ID,
        COLUMN_TIME,
        COLUMN_HANDLE_COUNT,
        COLUMN_THREAD_COUNT,
        COLUMN_PRIVATE_BYTES,
        COLUMN_VIRTUAL_BYTES,
        COLUMN_WORKING_SET,
        COLUMN_WORKING_SET_PRIVATE,
        COLUMN_MACHINE_CPU_USAGE]
    PROCESS_DATA_SOURCE_COLUMN_TYPES = [
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_INT,
        FIELD_TYPE_DATE,
        FIELD_TYPE_INT,
        FIELD_TYPE_INT,
        FIELD_TYPE_LONG,
        FIELD_TYPE_LONG,
        FIELD_TYPE_LONG,
        FIELD_TYPE_LONG,
        FIELD_TYPE_FLOAT]

    MACHINE_DATA_SOURCE_COLUMN = [
        COLUMN_COMMSERV_VERSION,
        COLUMN_PLATFORM,
        COLUMN_BUILD_ID,
        COLUMN_MACHINE_NAME,
        COLUMN_TIME,
        COLUMN_MACHINE_CPU_USAGE,
        COLUMN_MACHINE_AVAILBLE_MEMORY,
        COLUMN_MACHINE_FREE_MEMORY,
        COLUMN_PROCESSOR_QUEUE_LENGTH,
        COLUMN_DISK_QUEUE_LENGTH,
        COLUMN_MACHINE_CPU_FIFTEEN_MIN_LOAD_AVERAGE]

    MACHINE_DATA_SOURCE_COLUMN_TYPES = [
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_DATE,
        FIELD_TYPE_FLOAT,
        FIELD_TYPE_FLOAT,
        FIELD_TYPE_FLOAT,
        FIELD_TYPE_FLOAT,
        FIELD_TYPE_FLOAT,
        FIELD_TYPE_FLOAT]

    JOB_DETAILS_DATA_SOURCE_COLUMN = [
        COLUMN_COMMSERV_VERSION,
        COLUMN_BUILD_ID,
        COLUMN_JOB_ID,
        COLUMN_JOB_TYPE,
        COLUMN_JOB_STATUS,
        COLUMN_JOB_START,
        COLUMN_JOB_END,
        COLUMN_JOB_EVENTS,
        COLUMN_JOB_CONFIG,
        COLUMN_JOB_DURATION]

    JOB_DETAILS_DATA_SOURCE_COLUMN_TYPES = [
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_INT,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_LONG,
        FIELD_TYPE_LONG,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_LONG
    ]

    # field mappings to convert counters to appropriate solr fields in open data source
    COUNTERS_FIELD_MAPPING = {

        WindowsProcessCounters.PROCESS_PID.split("\\")[-1]: COLUMN_PROCESS_ID,
        WindowsProcessCounters.PROCESS_HANDLE_COUNT.split("\\")[-1]: COLUMN_HANDLE_COUNT,
        WindowsProcessCounters.PROCESS_THREAD_COUNT.split("\\")[-1]: COLUMN_THREAD_COUNT,
        WindowsProcessCounters.PROCESS_PRIVATE_BYTES.split("\\")[-1]: COLUMN_PRIVATE_BYTES,
        WindowsProcessCounters.PROCESS_VIRTUAL_BYTES.split("\\")[-1]: COLUMN_VIRTUAL_BYTES,
        WindowsProcessCounters.PROCESS_WORKING_SET.split("\\")[-1]: COLUMN_WORKING_SET,
        WindowsProcessCounters.PROCESS_WORKING_SET_PRIVATE.split("\\")[-1]: COLUMN_WORKING_SET_PRIVATE,
        WindowsProcessCounters.PROCESS_CPU.split("\\")[-1]: COLUMN_MACHINE_CPU_USAGE,
        WindowsMachineCounters.MACHINE_CPU.split("\\")[-1]: COLUMN_MACHINE_CPU_USAGE,
        WindowsMachineCounters.MACHINE_AVAILABLE_MEMORY_IN_MB.split("\\")[-1]: COLUMN_MACHINE_AVAILBLE_MEMORY,
        WindowsMachineCounters.MACHINE_DISK_AVG_QUEUE_LENGTH.split("\\")[-1]: COLUMN_DISK_QUEUE_LENGTH,
        WindowsMachineCounters.MACHINE_PROCESSOR_QUEUE_LENGTH.split("\\")[-1]: COLUMN_PROCESSOR_QUEUE_LENGTH,
        TYPEPERF_TIME_STAMP_HEADER: COLUMN_TIME,
        BASH_TIME_STAMP_HEADER: COLUMN_TIME,
        UnixProcessCounters.PROCESS_CPU: COLUMN_MACHINE_CPU_USAGE,
        UnixProcessCounters.PROCESS_WORKING_SET_PRIVATE: COLUMN_WORKING_SET_PRIVATE,
        UnixProcessCounters.PROCESS_VIRTUAL_BYTES: COLUMN_VIRTUAL_BYTES,
        UnixProcessCounters.PROCESS_THREAD_COUNT: COLUMN_THREAD_COUNT,
        UnixProcessCounters.PROCESS_HANDLE_COUNT: COLUMN_HANDLE_COUNT,
        UnixProcessCounters.PROCESS_PID: COLUMN_PROCESS_ID,
        UnixProcessCounters.PROCESS_WORKING_SET: COLUMN_WORKING_SET,
        UnixMachineCounters.MACHINE_CPU: COLUMN_MACHINE_CPU_USAGE,
        UnixMachineCounters.MACHINE_AVAILABLE_MEMORY_IN_MB: COLUMN_MACHINE_AVAILBLE_MEMORY,
        UnixMachineCounters.MACHINE_FREE_MEMORY_IN_MB: COLUMN_MACHINE_FREE_MEMORY,
        UnixMachineCounters.MACHINE_CPU_FIFTEEN_MIN_LOAD_AVERAGE: COLUMN_MACHINE_CPU_FIFTEEN_MIN_LOAD_AVERAGE,

        # Field mapping to itself as sometime headers from csv file matches with those of data source
        COLUMN_WORKING_SET_PRIVATE: COLUMN_WORKING_SET_PRIVATE,
        COLUMN_WORKING_SET: COLUMN_WORKING_SET,
        COLUMN_PROCESS_ID: COLUMN_PROCESS_ID,
        COLUMN_HANDLE_COUNT: COLUMN_HANDLE_COUNT,
        COLUMN_THREAD_COUNT: COLUMN_THREAD_COUNT,
        COLUMN_VIRTUAL_BYTES: COLUMN_VIRTUAL_BYTES,
        COLUMN_MACHINE_AVAILBLE_MEMORY: COLUMN_MACHINE_AVAILBLE_MEMORY,
        COLUMN_MACHINE_FREE_MEMORY: COLUMN_MACHINE_FREE_MEMORY,
        COLUMN_MACHINE_CPU_USAGE: COLUMN_MACHINE_CPU_USAGE,
        COLUMN_MACHINE_CPU_FIFTEEN_MIN_LOAD_AVERAGE: COLUMN_MACHINE_CPU_FIFTEEN_MIN_LOAD_AVERAGE,
        COLUMN_COMMSERV_VERSION: COLUMN_COMMSERV_VERSION,
        COLUMN_PLATFORM: COLUMN_PLATFORM

    }

    # Exception codes
    NO_VALID_PROCESS = "No such process"
    REMOTE_CONNECTION_ERROR = "Remote end closed connection"
    IGNORE_EXCEPTION = "Ignoring the recurrent exception"
    IGNORE_SPECIFIC_EXCEPTIONS = "Specific Exception happened for error : "
    FILE_NOT_EXISTS = "No such file or directory"
    MAX_RETRY_EXCEEDED = "Max retries exceeded with url"
    JSON_RESPONSE_ERROR = "json.decoder.JSONDecodeError: Extra data"
    IGNORE_REMOTE_ERRORS = [REMOTE_CONNECTION_ERROR, MAX_RETRY_EXCEEDED, JSON_RESPONSE_ERROR]

    # Error codes
    ERROR_STATS_NOT_COLLECTED_ONCE = "Performance stats was not collected at least once for this configurations"
    ERROR_MISSING_PERFORMANCE_STATS_FOR_PHASE = "Performance stats was not collected properly for few of the job phases"
    ERROR_MONITOR_THREAD_INIT_FAIL = 'Monitor thread Init crossed the failure threshold. Fail the collection'
    ERROR_MONITOR_THREAD_FAIL = 'Monitor thread crossed the failure threshold. Fail the collection'
    ERROR_MONITOR_THREAD_PROCESS_START = 'Unable to start remote client process for monitoring. Fail the collection'
    ERROR_JOB_DETAILS_FETCH_FAILED = "Unable to fetch details for the given job. Please check logs"

    # class names
    WINDOWS_PROCESS_COUNTER = 'WindowsProcessCounters'
    WINDOWS_MACHINE_COUNTER = 'WindowsMachineCounters'
    UNIX_PROCESS_COUNTER = 'UnixProcessCounters'
    UNIX_MACHINE_COUNTER = 'UnixMachineCounters'

    # har related constants
    HAR_API_DETAILS_HEADING = "Top %s - time consuming API's"
    HAR_DS_BUILD_ID = "BuildId"
    HAR_URL_COLUMN = "URL"
    HAR_REQUEST_TYPE_COLUMN = "Requesttype"
    HAR_RESPONSE_CODE_COLUMN = "Responsecode"
    HAR_TOTAL_TIME_COLUMN = "Totaltime"
    HAR_WAIT_TIME_COLUMN = "Waittime"
    HAR_TIMESTAMP_COLUMN = "timestamp"
    HAR_START_TIME_COLUMN = "Starttime"
    HAR_PERF_FOLDER_NAME = "HAR_Dumps"
    HAR_SERVER_IP_COLUMN = "ServerIP"
    HAR_PAGE_NAME_COLUMN = "PageName"
    HAR_DS_NAME = "Automated_HAR_dump_data_source"
    HAR_DS_FIELD_SCHEMA = {
        "indexed": True,
        "stored": True,
        "multiValued": False,
        "searchDefault": True,
        "autocomplete": False
    }
    HAR_DS_FIELD_TYPES = [
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_STRING,
        FIELD_TYPE_INT,
        FIELD_TYPE_DATE_TIME,
        FIELD_TYPE_INT,
        FIELD_TYPE_INT
    ]
    HAR_DS_FIELD_NAMES = [
        HAR_DS_BUILD_ID,
        HAR_SERVER_IP_COLUMN,
        HAR_PAGE_NAME_COLUMN,
        HAR_URL_COLUMN,
        HAR_REQUEST_TYPE_COLUMN,
        HAR_RESPONSE_CODE_COLUMN,
        HAR_START_TIME_COLUMN,
        HAR_WAIT_TIME_COLUMN,
        HAR_TOTAL_TIME_COLUMN
    ]


class CounterTypes():
    """Class for specifying different counter types"""
    PROCESS_COUNTER = 'Process'
    MACHINE_COUNTER = 'Machine'


class JobStatus():
    """Class for specifying different job status"""
    COMPLETED = "completed"
    FAILED = "failed"
    COMPLETED_WITH_ERRORS = "completed w/ one or more errors"
    PENDING = "pending"
    WAITING = "waiting"
    SUSPENDED = "suspended"


class TimerIntervals():
    """Class for specifying different time intervals used in performance monitoring"""
    MAIN_THREAD_SLEEP_IN_MINS = 1
    MONITOR_THREAD_RESTART_INTERVAL_IN_MINS = 10
    MONITOR_THREAD_SLEEP_IN_MINS = 1
    PUSH_THREAD_SLEEP_IN_MINS = 1
    PERFORMANCE_STATS_INTERVAL_IN_SECS = 5
    JOB_STATUS_FAIL_RETRY = 10
    PUSH_CONFIG_FAIL_RETRY = 5
    NON_COMMVAULT_CLIENT_REMOTE_COMMAND_EXECUTE_WAIT_IN_SECS = 40

    # Below timer depends on MONITOR_THREAD_RESTART_INTERVAL_IN_MINS. Keep it as x multiply of that counter value
    PORT_USAGE_CAPTURE_TIME_INTERVAL_IN_MINS = 20


class JobPhaseNames():
    """Class for maintaining individual job phase names"""
    LIVE_SCAN = "Live Scan"
    CONTENT_PUSH = "Content Push"
    IMPORT_INDEX = "Import"
    INDEX_EXTRACTION = "Content Indexing"
    ANALYSIS = "Analysis"
    DUMMY_DATA_CUBE = "Dummy DataCube"
    DUMMY_CONTENT_EXTRACTOR = "Dummy CVContentPreview"
    DUMMY_MESSAGE_QUEUE = "Dummy AMQ"
    DUMMY_EXPORTER = "Dummy Exporter"
    DUMMY_PYTHON = "Dummy Python"
    DUMMY_AUX_COPY = "Dummy AuxCopy"
    DUMMY_AUX_COPY_MGR = "Dummy AuxCopyMgr"
    DUMMY_EMPTY = "Dummy EMPTY"
    DUMMY_SEARCH_ENGINE = "Dummy SearchEngine"
    DUMMY_CVD = "Dummy CVD"
    DUMMY_CVODS = "Dummy CVODS"
    DUMMY_CVCI_ANALYTICS = "Dummy CvciAnalytics"
    DUMMY_CLRESTORE = "Dummy CLRestore"
    DUMMY_INDEX_GATEWAY = "Dummy IndexGateway"


class JobTypes():
    """Class for maintaining various job types"""
    TIME_BASED_JOB_MONITORING = 888
    DUMMY_JOB_TYPE = 0
    FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT = 1
    FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT_WITH_EE = 2
    FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_METADATA_ONLY = 3
    FILE_SYSTEM_BACKUP_IMPORT_INDEX = 4
    FILE_SYSTEM_BACKUP_INDEX_EXTRACTION = 5
    FSO_BACKUP_QUICK_SCAN = 6
    FSO_BACKUP_FULL_SCAN_SOURCE_CI = 7
    FSO_BACKUP_FULL_SCAN = 8
    FSO_LIVE_CRAWL = 9

    # Add jobs which has associated data source for it
    DATA_SOURCE_SUPPORTED_JOB_TYPES = [
        FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT_WITH_EE,
        FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT,
        FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_METADATA_ONLY,
        FILE_SYSTEM_BACKUP_IMPORT_INDEX,
        FILE_SYSTEM_BACKUP_INDEX_EXTRACTION,
        FSO_BACKUP_QUICK_SCAN,
        FSO_BACKUP_FULL_SCAN_SOURCE_CI,
        FSO_BACKUP_FULL_SCAN,
        FSO_LIVE_CRAWL
    ]

    # Add jobs which has associated data source and Entity extraction enabled
    DATA_SOURCE_ENTITY_EXTRACT_JOB_TYPES = [
        FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT_WITH_EE,
        FILE_SYSTEM_BACKUP_IMPORT_INDEX,
        FILE_SYSTEM_BACKUP_INDEX_EXTRACTION
    ]

    # Add sub job types of Online crawl job which uses access node
    ONLINE_CRAWL_JOB = [
        FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT_WITH_EE,
        FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT,
        FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_METADATA_ONLY
    ]

    # Add jobs which has extractedduration populated in fs data source
    CONTENT_CRAWLS = [
        FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT_WITH_EE,
        FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT,
        FILE_SYSTEM_BACKUP_INDEX_EXTRACTION
    ]


class JobPhases():
    """Class for maintaining various job phases for job

        get_job_phase()         --      returns the list of phases of particular job


    """
    DUMMY_JOB_TYPE = ['Default Phases']
    TIME_BASED_JOB_MONITORING = [GeneralConstants.TIMER_PHASE]
    FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT = [JobPhaseNames.LIVE_SCAN, JobPhaseNames.CONTENT_PUSH]
    FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT_WITH_EE = [JobPhaseNames.LIVE_SCAN, JobPhaseNames.CONTENT_PUSH]
    FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_METADATA_ONLY = [JobPhaseNames.LIVE_SCAN]
    FILE_SYSTEM_BACKUP_IMPORT_INDEX = [JobPhaseNames.IMPORT_INDEX]
    FILE_SYSTEM_BACKUP_INDEX_EXTRACTION = [JobPhaseNames.INDEX_EXTRACTION]
    FSO_BACKUP_QUICK_SCAN = [JobPhaseNames.ANALYSIS]
    FSO_BACKUP_FULL_SCAN_SOURCE_CI = [JobPhaseNames.IMPORT_INDEX]
    FSO_BACKUP_FULL_SCAN = [JobPhaseNames.INDEX_EXTRACTION]
    FSO_LIVE_CRAWL = [JobPhaseNames.LIVE_SCAN]

    def get_job_phase(self, job_type):
        """returns the job phases for the given job type
                Args:

                    job_type        (int)       --  job type

                Returns:

                    list        --  phases of job

        """
        if job_type == 0:
            return self.DUMMY_JOB_TYPE
        elif job_type == 1:
            return self.FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT
        elif job_type == 2:
            return self.FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT_WITH_EE
        elif job_type == 3:
            return self.FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_METADATA_ONLY
        elif job_type == 4:
            return self.FILE_SYSTEM_BACKUP_IMPORT_INDEX
        elif job_type == 5:
            return self.FILE_SYSTEM_BACKUP_INDEX_EXTRACTION
        elif job_type == 6:
            return self.FSO_BACKUP_QUICK_SCAN
        elif job_type == 7:
            return self.FSO_BACKUP_FULL_SCAN_SOURCE_CI
        elif job_type == 8:
            return self.FSO_BACKUP_FULL_SCAN
        elif job_type == 888:
            return self.TIME_BASED_JOB_MONITORING
        elif job_type == 9:
            return self.FSO_LIVE_CRAWL
        else:
            return []
