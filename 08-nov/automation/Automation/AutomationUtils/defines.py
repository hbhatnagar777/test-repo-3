from AutomationUtils.commonutils import enum

##INPUT ARGUMENTS##
TESTCASE_LIST = 'inputTestcaseList'
TESTSET_LIST = 'inputTestsetList'
CONVERT_INPUT = 'convertJson'
JSON_OUT_PATH = 'jsonOutputFile'
JSON_OUT_CONSOLE = 'consoleOutput'
JSON_OUT_FILE = 'consoleFile'
JSON_OUT_TABLE_CONSOLE = 'tableConsoleOutput'

##MISC##
COMMCELL_NODE = 'commcell_node'
DEFAULT_CS_VERSION = 'v11 B80 SP21' # Build script to set in future; replace with macro.

##Autocenter Defines Section##
AUTOCENTER_INPUT_TAG = "autocenter"
AUTOCENTER = enum(
    RequestID='RequestID',
)

##JSON Defines##
JSON_TESTSET_CONFIG_KEY = "testsetConfig"
JSON_TESTSET_INPUT_KEY = "testsets"
JSON_THREAD_COUNT_KEY = "THREADS"
JSON_TESTCASE_CONFIG_KEY = "testcaseConfig"
JSON_TESTCASE_UPDATEQA_KEY = "UpdateQA"
JSON_TESTCASE_INPUT_KEY = "testCases"
JSON_TESTCASE_INFO_KEY = "testCasesInfo"
JSON_COMMCELL_INPUT_KEY = "commcell"
JSON_EMAIL_INPUT_KEY = "email"
JSON_TESTCASE_PARALLEL = "ParallelExecution"

##THREAD Defines##
DEFAULT_TS_THREADS      =   1
DEFAULT_TC_THREADS      =   1

##TESTCASE Defines##
TC_REQ_AGENTNAME = "AgentName"
TC_UPDATE_QA = False
TC_TCINFO_TESTCASE_ID = 'testcaseID'
TC_TCINFO_TESTCASE_NAME = 'testcaseName'

##TESTSET Defines##
TS_PRODUCT_NAME = "TESTSET_PRODUCT_NAME"
TS_OS_TYPE = "TESTSET_OS_TYPE"
TS_APP_VER = "TESTSET_APPLICATION_VERSION"
TS_ADD_PROP = "TESTSET_ADDITIONAL_PROP"
TS_APP_VER_NOTSET = "<NOTSET>"
TS_ADD_PROP_NOTSET = "<NOTSET>"
TS_ID = 'id'
TS_CONTROLLER_ID = 'controllerid'
driver = "{SQL Server}"
unix_driver = "{ODBC Driver 17 for SQL Server}"
