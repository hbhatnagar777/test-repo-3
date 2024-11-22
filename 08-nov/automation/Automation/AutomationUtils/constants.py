# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for maintaining Core Automation Constants.

Any constant values related to the Automation Run goes in this file.

This file consists of the constants for:

    Automation Logger

    Test Cases Info

    Test Case Status

    Test Cases Directory

    Test Case Class Name

    Email Specific constants

    Template file for email

    Scripts path for Automation operations

    ...etc...

"""

from enum import Enum
import os
import re
import sys


def _get_log_dir_path():
    """Returns the log dir path depending on the operating system"""
    log_dir = None
    cur_dir = os.path.dirname(__file__)

    if "commvault" in cur_dir.lower():
        if 'win' in sys.platform.lower():
            return os.path.join(
                os.path.dirname(AUTOMATION_DIRECTORY),
                'Log Files', AUTOMATION_LOG_DIRECTORY_NAME
            )

        path = os.path.join(
            os.path.dirname(AUTOMATION_DIRECTORY), 'galaxy_vm'
        )

        instance = None
        with open(path, 'r') as f_obj:
            for line in f_obj.readlines():
                if 'GALAXY_INST' in line:
                    instance = re.findall(r'\"(.+?)\"', line)[0]
                    break

        if instance is None:
            raise Exception("Failed to get instance name")

        log_reg_path = '/etc/CommVaultRegistry/Galaxy/{0}/EventManager/.properties'.format(
            instance
        )

        with open(log_reg_path, 'r') as f_obj:
            for line in f_obj.readlines():
                if 'dEVLOGDIR' in line:
                    log_dir = re.findall(r'dEVLOGDIR (.+?)\n', line)[0]

        if log_dir is None:
            raise Exception("Failed to get log directory path")

        return os.path.join(log_dir, AUTOMATION_LOG_DIRECTORY_NAME)

    return os.path.join(AUTOMATION_DIRECTORY, 'Log Files')


# Logging specific constants
ALGORITHM_LIST = ["MD5", "SHA1", "SHA256", "SHA384", "SHA512"]
"""list:  Name of Cryptographic hash functions to compute checksum"""

AUTOMATION_EMAIL = "cvautomation@commvault.com"
''' default e-mail sender address for Automation Results. '''

AUTOMATION_LOG_FILE_NAME = 'Automation'
"""str:     Name of the log file to be created for the Automation Run."""

AUTOMATION_LOG_DIRECTORY_NAME = 'Automation'
"""str:     Name of the log directory to be created/ used while writing logs."""

LOG_FILE_ENCODING = 'utf-8'
"""str:     Encoding to be used for the Log File."""

LOG_BYTE_SIZE = 5242880
"""int:     Maximum size (in Bytes) of the log file before rolling over."""

MAX_INT_SIZE_SQL = 2147483647
"""int:     Maximum size for integer allowed in SQL."""

LOG_BACKUP_COUNT = 5
"""int:     Count of the backup files to be maintained after roll over."""

FORMAT_STRING = ('%(process)-6d %(thread)-6d %(asctime)-25s %(jobID)-10s %(module)-20s '
                 '%(funcName)-27s %(lineno)-6d %(levelname)-9s %(message)s')
"""str:     Format to be used for logging in the log file."""

# Test case specific constants
TEST_CASE_DIR = 'TestCases'
"""str:     Name of the Directory consisting of all the Test Cases for an Agent."""

TEST_CASE_CLASS_NAME = 'TestCase'
"""str:     Name of the class which represents a single test case in the test case py file."""

TEST_RESULTS_DICT = {
    "Test Case ID": 0,
    "Test Case Name": None,
    "Status": None,
    "Summary": None
}
"""dict:    Template dict to be updated for each test case with the test case run status."""

DIRECTORY_DEPTH = 3
"""int:     level of sub-directories that have to visited to find the test case"""

# HTML Template file
TEMPLATE_FILE = 'template.html'
"""str:     Name of the template HTML file to be used for generating the Test Set Run report."""

AUTOMATION_DIRECTORY = os.path.dirname(os.path.dirname(__file__))
"""str:     Directory path where the automation files are placed."""

ADMINCONSOLE_DIRECTORY = os.path.join(AUTOMATION_DIRECTORY, 'Web', 'AdminConsole')
"""str:     Directory path where the automation files are placed."""

AUTOMATION_UTILS_PATH = os.path.join(AUTOMATION_DIRECTORY, 'AutomationUtils')

AUTOMATION_BIN_PATH = os.path.join(AUTOMATION_DIRECTORY, 'CompiledBins')

ACTIVATE_UTIL_DB_PATH = os.path.join(AUTOMATION_BIN_PATH, 'entity.db')

CVTRIALS_DIRECTORY = os.path.join(AUTOMATION_DIRECTORY, 'CVTrials')

INSTALL_DIRECTORY = os.path.join(AUTOMATION_DIRECTORY, 'Install')

WORKFLOW_DIRECTORY = os.path.join(AUTOMATION_DIRECTORY, 'Server', 'Workflow', 'Workflows')
"""str:     Directory path where the workflow xml files are placed."""

VIRTUAL_SERVER_TESTDATA_PATH = os.path.join(AUTOMATION_DIRECTORY, 'VirtualServer', 'TestCases', 'TestData')
"""str:     Directory path of TestData inside TestCases inside Virtual Server."""

# Standalone logs location
STANDALONE_LOGS_LOCATION = os.path.join(AUTOMATION_DIRECTORY, 'logs')
"""str:     Directory path where the standalone logs should be placed."""

STANDALONE_LOG_FILE_NAME = "script"
"""str:     Name of the standalone log file to be created."""

# Test case run status
PASSED = 'PASSED'
"""str:     Status value where the test case ran and passed successfully."""

FAILED = 'FAILED'
"""str:     Status value where the test case ran, but failed."""

SKIPPED = 'SKIPPED'
"""str:     Status value where the test case run was skipped."""

# No Failure Reason
NO_REASON = ' -- '
"""str:     Default reason to be set for failure of any activity."""

# Automation Email
EMAIL_SUBJECT = 'ContentStore Automation Report '
"""str:     Subject of the Automation Run Email Report."""

# PowerShell Scripts for operations on Windows Clients
CREDENTIALS = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'Creds.ps1')
"""str:     Path of the PowerShel file to be used for generating the Credentials XML."""

DIRECTORY_EXISTS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'CheckIfDirectoryExists.ps1'
)
"""str:     Path of the PowerShell file to be used to check if a Folder/Directory exists or not."""

GET_HASH = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'GetHash.ps1'
)
"""str:     Path of the PowerShell file to be used to check if a File locked if not lock it ."""

GET_LOCK = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'LockFile.ps1'

)

"""str:     Path of the PowerShell file to be used to run cluster failover ."""

DO_CLUSTER_FAILOVER = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'dofailover.ps1'

)

"""str:     Path of the PowerShell file to be used to run cluster group failover to best possible node."""

DO_CLUSTER_GROUP_FAILOVER = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'dogroupfailover.ps1'

)

"""str:     Path of the PowerShell file to be used get the MD5 Hash of a File / Folder."""

GET_UNIX_HASH = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'GetHash.sh'
)
"""str:     Path of the Shell script to be used get the Hash of a File / Folder."""

COPY_FOLDER_THREADS = 8
"""int:     threads to be used for copy folder"""

COPY_FOLDER = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'CopyFolder.ps1')
"""str:     Path of the PowerShell file to be used to copy a folder to a remote machine."""

COPY_FILE = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'CopyFile.ps1')
"""str:     Path of the PowerShell file to be used to copy a file
                from local machine to the remote machine.
"""

MOUNT_NETWORK_PATH = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'MountNetworkPath.ps1'
)
"""str:     Path of the PowerShell file to be used to mount a network path to the local machine."""

UNMOUNT_NETWORK_PATH = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'UnMountNetworkPath.ps1'
)
"""str:     Path of the PowerShell file to be used to unmount a network path on this machine."""

CREATE_FILE = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'CreateFile.ps1')
"""str:     Path of the PowerShell file to be used to create a new file with some content in it."""

CREATE_DIRECTORY = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'MakeDir.ps1')
"""str:     Path of the PowerShell file to be used to create a folder / directory."""

CREATE_FILE_WITHSIZE = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'CreateFileWithSize.ps1')
"""str:     Path of the PowerShell file to be used
to create a new file with assigned length (filled with space) to it."""

GET_FILE_ATTRIBUTES = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'GetFileAttributes.ps1')
"""str:     Path of the PowerShell file to be used to get the attributes
of a file / folder."""

RENAME_ITEM = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'RenameItem.ps1')
"""str:     Path of the PowerShell file to be used to rename a file / folder."""

REMOVE_DIRECTORY = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'RemoveDir.ps1')
"""str:     Path of the PowerShell file to be used to remove a folder / directory."""

EXECUTE_COMMAND = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'ExecuteCommand.ps1'
)
"""str:     Path of the PowerShell file to be used to execute a PowerShell command."""

EXECUTE_EXE = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'ExecuteExe.ps1'
)
"""str:     Path of the PowerShell file to be used to execute a exe."""

BLOCK_PORT = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'BlockTcpPort.ps1'
)
"""str:     Path of the PowerShell file to be used to block tcp port."""

GENERATE_TEST_DATA = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'GenerateTestData.ps1'
)
"""str:     Path of the PowerShell file to be used to generate random test data."""

CREATE_UNCOMPRESSABLE_DATA_UNIX = os.path.join(
    os.path.dirname(__file__), "Scripts", "UNIX", "create_uncomp_data.bash"
)
"""str:     Path of the BASH Script file to be used to generate uncompressable test data."""

CREATE_UNCOMPRESSABLE_DATA_WINDOWS = os.path.join(
    os.path.dirname(__file__), "Scripts", "Windows", "create_uncomp_data.ps1"
)
"""str:     Path of the PowerShell file to be used to generate uncompressable test data."""

DELETE_NTH_FILES_UNIX = os.path.join(
    os.path.dirname(__file__), "Scripts", "UNIX", "DeleteNthFiles.sh"
)
"""str:     Path of the Shell Script file to be used to delete xth files."""

DELETE_NTH_FILES_WINDOWS = os.path.join(
    os.path.dirname(__file__), "Scripts", "Windows", "DeleteNthFiles.ps1"
)
"""str:     Path of the PowerShell file to be used to delete xth files."""


GET_SIZE = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'GetSize.ps1')
"""str:     Path of the PowerShell file to be used to get the size of a file / folder."""

GET_SIZE_ONDISK = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'GetSizeOnDisk.ps1')
"""str:     Path of the PowerShell file to be used to get the size on disk of a file / folder."""

HTML = """
<html>
    <h1>No Test Results Were Found.</h1>
</html>
"""

FILE_OR_FOLDER_LIST = os.path.join(os.path.dirname(
    __file__), 'Scripts', 'Windows', 'FileList.ps1')
"""str:     Path of the PowerShell file to be used to get the list of files in  folder."""

SCAN_DIRECTORY = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'ScanDirectory.ps1'
)
"""str:     Path of the PowerShell file to be used to scan directory and return their properties"""

CV_TIME_RANGE_LOGS = os.path.join(os.path.dirname(
    __file__), 'Scripts', 'Windows', 'CVTimeRangeLogs.ps1')
SCAN_DIRECTORY = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'ScanDirectory.ps1'
)
"""str:     Path of the PowerShell file to get commvault logs for a given time range."""

LATEST_FILE_OR_FOLDER = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'LatestFile.ps1'
)
"""str:     Path of the PowerShell file to be used to get the latest of file/folder in folder."""

REGISTRY_EXISTS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'CheckIfRegistryExists.ps1'
)
"""str:     Path of the PowerShell file to be used to check if a Registry exists or not."""

GET_REG_VALUE = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'GetRegValue.ps1'
)
"""str:     Path of the PowerShell file to be used to get the data of a Registry Key / Value."""

SET_REG_VALUE = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'SetRegValue.ps1'
)
"""str:     Path of the PowerShell file to be used to set the data of a Registry Key / Value."""

DELETE_REGISTRY = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'DeleteRegistry.ps1'
)
"""str:     Path of the PowerShell file to be used to delete a Registry Key / Value."""

# Path of archive file containing problematic data for UNIX clients
UNIX_PROBLEM_DATA = os.path.join(
    AUTOMATION_UTILS_PATH, 'TestData', 'problematicdata.tar.gz'
)
"""str:     Path of the UNIX problematic data tar file."""

# Shell scripts for operations on UNIX Clients
UNIX_MANAGE_DATA = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'ManageData.bash'
)
"""str:     Path of the UNIX Shell file to be used to manage data for given path."""

HADOOP_MANAGE_DATA = os.path.join(
    AUTOMATION_BIN_PATH, 'cvhadoop-manage-data.jar'
)
"""str:     Path of the jar file to be used to manage Hadoop data for given path."""

UNIX_GET_CPU_USAGE = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'GetCPUusage.bash'
)
"""str:     Path of the Unix shell fiel to be used to get CPU usage for a given process."""

UNIX_VERIFY_DC = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'VerifyDC.bash'
)
"""str:     Path of the UNIX Shell file to be used to check verify DC scan."""

UNIX_VOLUME_STATE = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'VolumeState.bash'
)
"""str:     Path of the UNIX Shell file to be used to check if volume state before running dc"""

UNIX_GET_RESTORE_STREAM_COUNT = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'GetRestoreStreamCount.bash'
)
"""str:     Path of the UNIX Shell file to be used to get restore stream count for a given job."""

UNIX_GET_NODE_AND_STREAM_COUNT = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'GetNodeAndStreamCount.bash'
)
"""str:     Path of the UNIX Shell file to be used to get node and stream count for a given distributed job."""

UNIX_DIRECTORY_EXISTS = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'DirectoryExists.sh'
)
"""str:     Path of the UNIX Shell file to be used to check if a folder/directory exists or not."""


UNIX_GET_CV_TIME_RANGE_LOGS = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'CVTimeRangeLogs.bash'
)
"""str:     Path of the UNIX Shell file to get commvault logs for a given time range."""

UNIX_REGISTRY_EXISTS = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'RegistryExists.sh'
)
"""str:     Path of the UNIX Shell file to be used to check if a registry exists or not."""

UNIX_CREATE_REGISTRY = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'CreateRegistry.sh'
)
"""str:     Path of the UNIX Shell file to be used to create a Registry File / Key."""

UNIX_SET_REG_VALUE = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'UNIX',
    'SetRegValue.sh')
"""str:     Path of the UNIX Shell file to be used to add / update the value of a registry key."""

TEMP_DIR = os.path.join(AUTOMATION_DIRECTORY, 'temp')
"""str:        path where the automation job temporary files are to be placed."""

ADMIN_CONSOLE_SCREENSHOT = os.path.join(TEMP_DIR, 'AdminConsole')
"""str:        path where screenshot of Admin Console automation failure are to be placed"""

# will load the default configs directly from template till the install
# script for config is ready
CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "CoreUtils", "Templates", "config.json"
)
"""str:     path where the config.json file has to be placed"""

TESTCASE_CUSTOM_DIR = os.path.join(AUTOMATION_DIRECTORY, "Custom", "Testcases")
"""str:     Directory where users should create / write their testcases."""

TESTCASE_SYSTEM_DIR = os.path.join(AUTOMATION_DIRECTORY, "Testcases")
"""str:     Directory where all system created testcases are stored."""

TESTCASE_VIRTUAL_SERVER_DIR = os.path.join(AUTOMATION_DIRECTORY, "VirtualServer", "Testcases")
"""str:     Directory path of testcases inside Testcases Folder in Virtual Server ."""

TESTCASE_SYSTEM_TYPE = 1
TESTCASE_USER_TYPE = 2

LOG_DIR = _get_log_dir_path()
""""str:    log directory path"""

UNIX_GIT_STATUS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'DevOps', 'GitStatus.sh'
)
"""str:     Path of the Shell file to be used to check git version."""

UNIX_GIT_PUSH = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'DevOps', 'GitPush.sh'
)
"""str:     Path of the Shell file to be used to push git repositories using git."""

UNIX_GIT_PULL = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'DevOps', 'GitPull.sh'
)
"""str:     Path of the Shell file to be used to pull repositories using git."""

UNIX_GIT_RESTORE_FROM_INDEX = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'DevOps', 'GitRestoreFromIndex.sh'
)
"""str:     Path of the Shell file to be used to restore repository content from its index."""

WINDOWS_GIT_STATUS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'DevOps', 'GitStatus.ps1'
)
"""str:     Path of the PowerShell file to be used to check git version."""

WINDOWS_GIT_PUSH = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'DevOps', 'GitPush.ps1'
)
"""str:     Path of the PowerShell file to be used to push git repositories using git."""

WINDOWS_GIT_PULL = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'DevOps', 'GitPull.ps1'
)
"""str:     Path of the PowerShell file to be used to pull repositories using git."""

WINDOWS_GIT_RESTORE_FROM_INDEX = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'DevOps', 'GitRestoreFromIndex.ps1'
)
"""str:     Path of the PowerShell file to be used to restore repository content from its index."""

UNIX_POSTGRES_STATUS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'PostgreSQL', 'PostgresStatus.sh'
)
"""str:     Path of the Shell file to be used to check Postgres Server status."""

UNIX_POSTGRES_START_STOP = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'PostgreSQL', 'PostgresStartStop.sh'
)
"""str:     Path of the Shell file to be used to Start / Stop Postgres Server."""

UNIX_POSTGRES_DATADIR = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'PostgreSQL', 'PostgresDataDir.sh'
)
"""str:     Path of the Shell file to be used get postgres data directory."""

WINDOWS_POSTGRES_STATUS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'PostgreSQL', 'PostgresStatus.ps1'
)
"""str:     Path of the PowerShell file to be used to check Postgres Server status."""

WINDOWS_POSTGRES_START_STOP = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'PostgreSQL', 'PostgresStartStop.ps1'
)
"""str:     Path of the PowerShell file to be used to Start / Stop Postgres Server."""

WINDOWS_POSTGRES_DATADIR = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'PostgreSQL', 'PostgresDataDir.ps1'
)
"""str:     Path of the Shell file to be used get postgres data directory."""

UNIX_ORACLE_RMAN_RECOVER = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'Oracle', 'OracleRecover.sh'
)
"""str:     Path of the Shell file to be used to invoke Oracle RMAN to run recover."""

UNIX_ORACLE_RESTART_DB = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'Oracle', 'OracleRestart.sh'
)
"""str:     Path of the Shell file to be used to restart Oracle DB using srvctl utility."""

CS_CVD_LOG_CHECK_FOR_CHUNK_COMMIT = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'checkChunkCommited.ps1'
)
"""str:     Path of the PowerShell file to be used to check if atleast one
chunk is commited for a given Job.
"""

UNIX_EXECUTE_COMMAND = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'ExecuteCommand.sh'
)

UNIX_COMMVAULT_PROCESS_DETAILS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'getCommvaultProcessDetails.sh'
)
"""str:     Path of the Shell file to be used to get all the commvault
process list for a given instance in JSON format.
"""

WINDOWS_COMMVAULT_PROCESS_DETAILS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'get_commvault_process.ps1'
)
"""str:     Path of the PowerShell file to be used to get all the commvault
process list for a given instance in JSON format.
"""

CREATE_D365_AZURE_APP = os.path.join(
    os.path.dirname(__file__),
    'Scripts',
    'Windows',
    'AzureAppGen.ps1'
)
"""str:     Path of the PowerShell file to create an Azure App"""

UNIX_INFORMIX_SERVER_OPERATIONS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'Informix', 'InformixServer.sh'
)
"""str:     Path of the Unix shell file to be used to perform informix related
operations on Unix client.
"""

WINDOWS_INFORMIX_SERVER_OPERATIONS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'Informix', 'InformixServer.ps1'
)
"""str:     Path of the Powershell file to be used to perform informix related
operations on Windows client.
"""

UNIX_MYSQL_SERVER_OPERATIONS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'MySQL', 'MySQL_Operations.sh'
)
"""str:     Path of the Unix shell file to be used to perform MySQL related
operations on Unix client.
"""

WINDOWS_MYSQL_SERVER_OPERATIONS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'MySQL', 'MySQL_Operations.ps1'
)
"""str:     Path of the Powershell file to be used to perform MySQL related
operations on Windows client.
"""

UNIX_MAXDB_SERVER_OPERATIONS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'MaxDB', 'maxdbserver.sh'
)
"""str:     Path of the Unix shell file to be used to perform MaxDB related
operations on Unix client.
"""

WINDOWS_MAXDB_SERVER_OPERATIONS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'MaxDB', 'maxdbserver.ps1'
)
"""str:     Path of the Powershell file to be used to perform MaxDB related
operations on Windows client.
"""

UNIX_MAXDB_DATA_OPERATIONS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'UNIX', 'MaxDB', 'maxdbdataops.sh'
)
"""str:     Path of the Unix shell file to be used to perform MaxDB related
operations on Unix client.
"""

WINDOWS_MAXDB_DATA_OPERATIONS = os.path.join(
    os.path.dirname(
        __file__), 'Scripts', 'Windows', 'MaxDB', 'maxdbdataops.ps1'
)
"""str:     Path of the Powershell file to be used to perform MaxDB related
operations on Windows client.
"""

WINDOWS_TMP_DIR = "C:\\tmp"
UNIX_TMP_DIR = "/tmp/"

# Powershell scripts for operations on Windows Clients
WINDOWS_ADD_DATA = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'AddData.ps1'
)
"""str:     Path of the WINDOWS Shell file to be used to generate and add data."""

WINDOWS_MODIFY_DATA = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'ModifyData.ps1'
)
"""str:     Path of the WINDOWS Shell file to be used to modify data for given path."""

WINDOWS_GET_DATA = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'GetData.ps1'
)
"""str:     Path of the WINDOWS Shell file to be used to get meta data for given path."""

WINDOWS_OPERATION = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'WindowsOperation.ps1'
)
"""str:     Path of the WINDOWS Shell file to be used to run windows operation."""

EXECUTE_COMMAND_UNC = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'ExecuteCommandUNC.ps1'
)
"""str:     Path of the WINDOWS Shell to delete a file or folder on unc path."""

WINDOWS_GET_ASCII_VALUE_FOR_PATH = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'GetASCIIValueForPath.ps1'
)
"""str:     Path of the WINDOWS Shell file to be used to get meta data for given path."""

WINDOWS_GENERATE_TEST_DATA_THREAD_COUNT = 4
"""str:     Number of threads to be used when generating test data."""

WINDOWS_GET_REGISTRY_ENTRY_FOR_SUBKEY = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'GetRegistryEntriesForSubKey.ps1'
)
"""str:     Path of the WINDOWS Shell file to get all registry entries for a given subkey."""

WINDOWS_PROBLEM_DATA = os.path.join(
    AUTOMATION_UTILS_PATH, 'TestData', 'windows_problematicdata.7z'
)
"""str:     Path of the Windows problematic data tar file."""

WINDOWS_GET_PROCESS_STATS = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'GetProcessStats.ps1'
)
"""str:     Path of the PowerShell file to be used to get process stats like memory, handle count etc."""

WINDOWS_GET_PROCESS_DUMP = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'GetProcessDump.ps1'
)
"""str:     Path of the PowerShell file to be used to get process stats like memory, handle count etc."""

UNIX_GET_PROCESS_STATS = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'UNIX', 'GetProcessStats.sh'
)
"""str:     Path of the PowerShell file to be used to get process stats like memory, handle count etc."""

BMR_VERIFY_VMWARE = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'onetouchvmwarevalidation.ps1'
)
"""str:     Path of the BMR verify script."""

BMR_VERIFY_HYPERV = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'Windows', 'onetouchhypervvalidation.ps1')

"""str:   BMR_VERIFY_hyperv  Path of the BMR hyper-V verify script."""

ORDERED_ENTITIES = ['disklibrary',
                    'storagepolicy',
                    'backupset',
                    'subclient',
                    'clientgroup']
''' List of entities to be created in the order defined here '''

ORDERED_ENTITIES_DICT = {item: {} for item in ORDERED_ENTITIES}
''' Empty entities dictionary'''

DELETE_ENTITIES_ORDER = list(reversed(ORDERED_ENTITIES))
''' List of entities to be deleted in the order defined here '''

DEFAULT_ENTITY_FORCE = True
''' Default value for creating the entities '''

DEFAULT_FILE_SIZE = 2500
''' Default file size in KB'''

DEFAULT_DIR_LEVEL = 1
''' Default sub directory levels to be created in test data '''

DESCRIPTION = "Automation"
''' Default description for entities created from automation.'''

IBMI_GET_DATA = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'IBMI', 'GetData.ksh'
)
"""str:     Path of the IBMI Shell file to be used to get meta data."""

IBMI_ADD_DATA = os.path.join(
    os.path.dirname(__file__), 'Scripts', 'IBMI', 'AddData.ksh'
)
"""str:     Path of the IBMI Shell file to be used to generate and add data."""

TESTDATA_DIR_NAME = "Commvault_Automation"
''' This would be the directory name for storing the temp data for a testcase run on clients '''

WINDOWS_DELIMITER = "!@##@!"
''' Helps to identify the list of folders to be ignored while computing
    hash when passed as a string to the script.
'''

UNIX_DELIMITER = "&^&^&"
''' Helps to identify the list of folders to be ignored while computing
    hash when passed as a string to the script.
'''

SYBASE_DUMP_BASED_WITH_CONFIGURED_INSTANCE = 1
'''Sybase Dump based backup copy with configured instance'''

SYBASE_DUMP_BASED_WITH_AUXILIARY_SERVER = 2
'''Sybase Dump based backup copy with auxiliary server'''

IGNORE_VALUES = ['none', 'na', '<notset>', 'null']
'''List of values to be ignored'''

ENGWEB_TESTCASE_URL = ("https://engweb.commvault.com/testcase/{}")
'''URL to access engweb testcase'''

VMS_UNIX_MOUNT_PATH = "/cv_vms_mnt"
'''The mount path on a unix proxy machine onto which OpenVMS test_path will be mounted'''

VMS_MOUNTED_DISK = "/cv_vms_disk"
'''The mapped name of OpenVMS disk containing test_path which needs to be mounted'''

# ALERT SPECIFIC CONSTANTS
CRITERIA_ID = {1: 'Succeeded',
               2: 'Alert every 2 attempts (Phase failures)',
               3: 'Failed',
               4: 'Skipped',
               5: 'Delayed by 1 Hrs',
               6: 'List Media',
               7: 'Initiated',
               8: 'Rolled Back',
               9: 'Media Needs Import',
               10: 'Media Handling Required',
               11: 'Media Picked up',
               12: 'Media Reached Destination',
               13: 'Media Returned to Source',
               14: 'Job Activity',
               15: 'ASR Backup Has occured.',
               16: 'Properties Modified',
               17: 'Alert Modified',
               18: 'Disk Space Low',
               19: 'Force deconfigured',
               20: 'Library went Offline',
               21: 'Scheduler Changes',
               22: 'Insufficient Storage',
               23: 'Media Handling Errors',
               24: 'Media Handling Required',
               25: 'Media Mount and Usage Errors',
               26: 'Maintenance Required',
               27: 'Maintenance Occured',
               28: 'User overwrite of Media',
               29: 'Drive went Offline',
               30: 'MediaAgent went Offline',
               31: 'Mountpath went Offline',
               32: 'Alert every 2 attempts (Network failures)',
               33: 'Exchange Journal Mailboxes 10000 Message Count Exceeded',
               34: 'Job Results Folder Low Space',
               35: 'Index Cache Folder Low Space',
               38: 'Updates Available',
               39: 'Release Upgrade Required',
               40: 'Updates Required',
               41: 'Media Ready in CAP Alert',
               42: 'Log file reached high watermark',
               43: 'Log file volume reached low watermark',
               44: 'No log play activity',
               45: 'No log transfer activity',
               46: 'No Data Protection',
               47: 'Classification Failed',
               48: 'No log transfer activity',
               49: 'Virtual Servers Added',
               50: 'V2 upgraded to V3',
               51: 'Media Recalled',
               52: 'Increase in Data size by 10 %',
               53: 'Decrease in Data size by 10 %',
               54: 'Job Started',
               55: 'Alert every 3 failed login attempts',
               56: 'Auxilary copy fallen behind alert',
               57: 'Job Completed with Errors',
               58: 'Alert Commserver license expires within 30 days',
               60: 'Alert Commserver license expires within 99 days',
               61: 'Log monitoring',
               62: 'Simpana Event monitoring',
               63: 'Non-encrypted media exported',
               64: 'Content Index data fallen behind alert',
               65: 'No Backup for last 3 Days',
               66: 'Certificate for client expired/revoked',
               67: 'Job exceeded running time',
               68: 'Failed files count exceeded threshold',
               69: 'Failed files Percent exceeded threshold',
               70: 'DDB Store got corrupted',
               71: 'Backup for subclient failed consecutively for 3 attempts',
               72: 'DDB disk space low',
               73: 'Alert when jobs in pending state exceed 30 percent or count of 15',
               74: 'Data backed up exceeds 5 GB',
               75: 'Custom Alert',
               76: 'Job Commmitted',
               77: 'Disk space low for Job results directory',
               78: 'Disk Space low for Index Cache',
               79: 'Disk Space low for Galaxy directory',
               80: 'Quota exceeded',
               81: 'Quota reaching threshold',
               82: 'Quota validation failed',
               83: 'Edge drive/share operations',
               84: 'DDB went Offline',
               85: 'Increase in object count by 10 percent',
               86: 'Failover started',
               87: 'Failover activity',
               88: 'Failover completed',
               89: 'Failover failed',
               90: 'Production Commserv is not reachable',
               91: 'Production Commserv is not running',
               92: 'Passive node is not reachable',
               93: 'Anomaly in events',
               94: 'Runtime anomaly in jobs',
               95: 'Anomaly in number of pending jobs',
               96: 'Anomaly in number of failed jobs',
               98: 'File system Quota Exceeded',
               99: 'File system Quota reaching threshold',
               100: 'File system quota validation failed',
               101: 'Job activity anomaly',
               102: 'Anomaly in number of succeeded jobs',
               103: 'Alert when client is offline for 15 Minutes',
               104: 'Anomaly in DDB pruning',
               105: 'Smart MA state Management',
               106: 'Job succeeded with warnings',
               200: 'Trigger Report (need to hide!)',
               10000: 'The current server configuration is invalid.',
               10001: 'Usage Analysis Processing is not enabled.',
               10002: 'Usage Logging is not enabled.',
               10003: 'Site Database is not online.',
               10004: 'Content Database site warning.',
               10005: 'Site Collection quota size exceeded.',
               10006: 'Site Collection has no usage quota assigned.',
               10007: 'Virtual Server has RecycleBin Disabled.',
               10008: 'Virtual Server has RecycleBinCleanUp Disabled.',
               10009: 'Unused disk space',
               10010: 'Partition is almost full',
               10011: 'Logical Volume is almost full',
               10012: 'Volume Group offline',
               10013: 'Logical Volume offline',
               10014: 'User exceeded file count soft limit quota',
               10015: 'Advisory Name for [UXFSAgent_GroupExceededFCSLe]',
               10016: 'User exceeded file count hard limit quota',
               10017: 'Group exceeded file count hard limit quota',
               10018: 'User exceeded block soft limit quota',
               10019: 'Group exceeded block soft limit quota',
               10020: 'User exceeded block hard limit quota',
               10021: 'Group exceeded block hard limit quota',
               10022: 'Volume is full',
               10024: 'Windows automatic updates are disabled',
               10025: 'Anti virus software might not be installed',
               10026: 'Software Firewall might not be installed',
               10027: 'User exceeded storage space soft limit.',
               10028: 'User exceeded storage space hard limit.',
               10029: 'Group exceeded storage space soft limit.',
               10030: 'Group exceeded storage space hard limit.',
               10031: 'File system quotas not enabled.',
               10032: 'Auto create statistics is disabled',
               10033: 'Auto update statistics is disabled',
               10034: 'Autoshrink is enabled',
               10035: 'Autoclose is enabled',
               10036: 'Advisory Name for [SQLAgent_DatabaseNotBackedUpAdvisory]',
               10037: 'Database log not backed up',
               10038: 'Simple recovery mode of production database',
               10040: 'Database in single-user mode',
               10041: 'Logical scan fragmentation for Index exceeds limit',
               10042: 'Extent scan fragmentation for Index exceeds limit',
               10043: 'Pool is full',
               10044: 'User is close to storage space quota',
               10045: 'Failing monitoring services of Exchange Server',
               10046: 'Excessive CPU utilization of Exchange Server',
               10047: 'Advisory Name for [ExchAgent_ClusterFailureAdvisory]',
               10048: 'Advisory Name for [ExchAgent_LowMemoryAdvisory]',
               10049: 'Disk space limited for Exchange Server',
               10050: 'Database has too few control files',
               10051: 'Database has guessable passwords',
               10052: 'Database public account has system privileges',
               10053: 'Database has users with unlimited login attempts',
               10054: 'Database public has execute privileges',
               10055: 'Advisory Name for [OracleAgent_DatabaseNoSpfileAdvisory]',
               10056: 'Advisory Name for [OracleAgent_DatabaseDictionaryManagedAdvisory]',
               10057: 'System tablespace has rollback',
               10058: 'Instance does not have archivelog mode',
               10059: 'Instance does not have auto undo',
               10060: 'Instance does not have assm',
               10061: 'Tablespace has unlimited extension',
               10062: 'Tablespace has both rollback and data',
               10063: 'Advisory Name for [OracleAgent_TablespaceNoFreeSpaceAdvisory]',
               10064: 'Advisory Name for [OracleAgent_SegmentTooManyExtentsAdvisory]',
               10065: 'Advisory Name for [OracleAgent_InstanceNotEnoughRedoSpaceAdvisory]',
               10066: 'Advisory Name for [OracleAgent_InstanceAverageWaitAdvisory]',
               10067: 'Advisory Name for [OracleAgent_UserTempTablespaceAsPermanentAdvisory]',
               10068: 'Advisory Name for [OracleAgent_UserSystemTablespaceAsDefaultAdvisory]',
               10069: 'Advisory Name for [OracleAgent_TablespaceUserDataInSystemAdvisory]',
               10070: 'Advisory Name for [OracleAgent_TableTooManyIndexesAdvisory]',
               10071: 'Advisory Name for [OracleAgent_TableChainedRowsAdvisory]',
               10072: 'NAS filer is not reachable',
               10073: 'NAS logical volume is full',
               10074: 'NAS logical volume is unavailable',
               10075: 'NAS CIFS share: logical volume is unavailable',
               10076: 'NAS CIFS share: logical volume is full',
               10077: 'NAS NFS share: logical volume is unavailable',
               10078: 'NAS NFS share: logical volume is full',
               10079: 'NAS Celerra is not reachable',
               10080: 'NAS Celerra Data Mover is not available',
               10081: 'NAS Celerra primary Data Mover has no standby',
               10082: 'NAS Celerra VDM is not replicated',
               10083: 'NAS Celerra slice volume is not in Storage Pool/Meta Volume',
               10084: 'NAS Celerra stripe volume is not in Storage Pool/Meta Volume',
               10085: 'NAS Celerra Meta Volume has no client volume or file system',
               10086: 'NAS Celerra Storage Pool is full',
               10087: 'NAS Celerra automatic extension is disabled for Storage Pool',
               10088: 'NAS Celerra disk volumes cannot be added to Storage Pool',
               10089: 'Advisory Name for [NASAgent_CelerraSPOvercommitAdvisory]',
               10090: 'Advisory Name for [NASAgent_FileSystemFullAdvisory]',
               10091: 'Advisory Name for [NASAgent_FileSystemNotSharedAdvisory]',
               10092: 'NAS Celerra max number of nested mount points under NMFS root',
               10093: 'NAS Celerra checkpoint name has invalid extension',
               10094: 'NAS Celerra quota policy is wrong for CIFS',
               10095: 'Advisory Name for [NASAgent_CIFSShareFileSystemUnavailableAdvisory]',
               10096: 'NAS Celerra CIFS share: CIFS server is unavailable',
               10097: 'NAS Celerra CIFS share: Data Mover is unavailable',
               10098: 'NAS CIFS share: file system is full',
               10099: 'NAS Celerra CIFS share: Storage Pool is full',
               10100: 'NAS file system hosting iSCSI LUNs is exported via CIFS share',
               10101: 'NAS Celerra NFS Share: Data Mover is unavailable',
               10102: 'NAS NFS Share: file system is full',
               10103: 'NAS Celerra NFS Share: Storage Pool is full',
               10104: 'NAS file system hosting iSCSI LUNs is exported via NFS share',
               10105: 'Advisory Name for [NASAgent_NetworkFSNotMountedAdvisory]',
               10106: 'NAS storage quota on quota tree exceeded Celerra max limit',
               10107: 'NAS storage quota for user exceeded Celerra max limit',
               10108: 'NAS storage quota for group exceeded Celerra max limit',
               10109: 'NAS vFiler is not available',
               10110: 'Advisory Name for [NASAgent_AggVolumeFullAdvisory]',
               10111: 'NAS aggregate is unavailable',
               10112: 'NAS aggregate is overcommitted',
               10113: 'Exchange Mailbox Store dismounted',
               10114: 'Exchange Public Folder Store dismounted',
               10115: 'Overapping Partitions'}

CATEGORY_ID = {'Configuration': 2,
               'Job Management': 1,
               'Media Management': 3,
               'Operation': 8,
               'Software Updates': 5,
               'Custom Rules': 9}

ALERT_CATEGORY_TYPE = {
    'Configuration': {'Client Group': 59,
                      'Clients': 10,
                      'Commcell': 12,
                      'Library': 16,
                      'License': 60,
                      'MediaAgents': 13,
                      'Schedules': 14,
                      'Storage Policy': 15
                      },

    'Job Management': {'Data Aging': 1,
                       'Data Classification': 27,
                       'Auxiliary Copy': 2,
                       'Data Protection': 3,
                       'Backup Copy Workflow': 61,
                       'Continuous Data Replication': 28,
                       'Data Verification': 6,
                       'DeDup DB Reconstruction': 55,
                       'Disaster Recovery Backup': 5,
                       'Information Management': 53,
                       'Media Erase': 9,
                       'Media Inventory': 7,
                       'Media Refreshing': 54,
                       'Offline Content Indexing': 29,
                       'Report': 52,
                       'Virtualize Me': 64,
                       'Workflow': 63
                       },

    'Media Management': {'Device Status': 21,
                         'Library Management': 17,
                         'Vault Tracker': 18
                         },

    'Operation': {'Event Viewer Events': 58,
                  'CommServe LiveSync': 74,
                  'Admin Alert': 75
                  },

    'Software Updates': {'Download Software': 19,
                         'Install Updates': 20,
                         'Updates Available To Download': 24,
                         },
    'Custom Rules': {'all': 65}
}

ALERT_NOTIFICATIONS = {
    'Email': 1,
    'Snmp': 4,
    'Event Viewer': 8,
    'Save To Disk': 512,
    'Rss Feeds': 1024,
    'Console Alerts': 8192,
    'Scom': 32768
}

SNAP_COPY_SCHEDULE_NAME = '{0} snap copy'
'''Storage policy snap copies have schedule associated. This is for the naming convention of that schedule.'''


class backup_level(Enum):
    """str:    constants for all backup levels defined in JMBackupLevelNames table
       defined for backup levels which are not having duplicate numbers in the same table
    """
    FULL = 'Full'
    INCREMENTAL = 'Incremental'
    SYNTHETICFULL = 'Synthetic Full'
    TRANSACTIONLOGNOTRNCATE = 'Trans. Log No Trunc.'
    TRANSACTIONLOG = 'Transaction Log'
    DIFFERENTIAL = 'Differential'
    ASR = 'ASR'
    ONLINEFULL = 'Online Full'
    OFFLINEFULL = 'Offline Full'
    REPLICATECREATE = 'Replicate create'
    REPLICATEINCREMENTALUPDATE = 'Replicate incremental update'


class OracleJobType(Enum):
    """constants for all possible oracle job types defined in JMJobOperationNames table
    """
    BACKUP = 'backup'
    RESTORE = 'restore'
    SNAP_TO_TAPE = 'snap to tape'
    SNAP_BACKUP = 'snap backup'
    ARCHIVE_RESTORE = 'archive restore'
    DATAMASKING = 'data masking'
    INSTANT_CLONE = 'instant clone'


class SnapShotEngineNames(Enum):
    """Class to maintain Snap Shot Engine Names"""

    SM_SNAPSHOT_ENGINE_NATIVE_NAME = "Native"
    SM_SNAPSHOT_ENGINE_HDS_NAME = "Hitachi Shadow Image"
    SM_SNAPSHOT_ENGINE_NETAPP_NAME = "NetApp"
    SM_SNAPSHOT_ENGINE_SYMMETRIX_NAME = "Dell EMC TimeFinder BCV"
    SM_SNAPSHOT_ENGINE_SYMMETRIX_SNAP_NAME = "Dell EMC TimeFinder Snap"
    SM_SNAPSHOT_ENGINE_CLARIION_SNAP_NAME = "Dell EMC VNX / CLARiiON SnapView / VNX Snap"
    SM_SNAPSHOT_ENGINE_CLARIION_CLONE_NAME = "Dell EMC VNX / CLARiiON SnapView Clone"
    SM_SNAPSHOT_ENGINE_HDS_NAME_SNAP = "Hitachi COW Snap"
    SM_SNAPSHOT_ENGINE_CDR_NAME = "Data Replicator"
    SM_SNAPSHOT_ENGINE_CDR_SNAP_NAME = "Data Replicator"
    SM_SNAPSHOT_ENGINE_EQUALLOGIC_NAME = "Dell Equallogic Snap"
    SM_SNAPSHOT_ENGINE_HPEVA_SNAP_NAME = "HPE EVA Snap"
    SM_SNAPSHOT_ENGINE_HPEVA_CLONE_NAME = "HPE EVA Clone"
    SM_SNAPSHOT_ENGINE_LSI_SNAP_NAME = "NetApp E-series / LSI Snap"
    SM_SNAPSHOT_ENGINE_LSI_CLONE_NAME = "NetApp E-series / LSI Volume Copy"
    SM_SNAPSHOT_ENGINE_IBMXIV_SNAP_NAME = "IBM XIV Snap"
    SM_SNAPSHOT_ENGINE_ISILON_SNAP_NAME = "Dell EMC Isilon Snap"
    SM_SNAPSHOT_ENGINE_DDR_SNAP_NAME = "Data Replicator"
    SM_SNAPSHOT_ENGINE_EQUALLOGIC_CLONE_NAME = "Dell Equallogic Clone"
    SM_SNAPSHOT_ENGINE_CELERRA_SNAP_NAME = "Dell EMC VNX / Celerra SnapSure Snap"
    SM_SNAPSHOT_ENGINE_IBMSVC_SNAP_NAME = "IBM Space-efficient FlashCopy"
    SM_SNAPSHOT_ENGINE_IBMSVC_CLONE_NAME = "IBM FlashCopy"
    SM_SNAPSHOT_ENGINE_COMPELLENT_SNAP_NAME = "Dell Compellent Snap"
    SM_SNAPSHOT_ENGINE_AUTO_SNAP_NAME = "Auto Discover Snap"
    SM_SNAPSHOT_ENGINE_AUTO_CLONE_NAME = "Auto Discover Clone"
    SM_SNAPSHOT_ENGINE_3PAR_SNAP_NAME = "HPE 3PAR StoreServ Snap"
    SM_SNAPSHOT_ENGINE_3PAR_CLONE_NAME = "HPE 3PAR StoreServ Clone"
    SM_SNAPSHOT_ENGINE_SYMMETRIX_CLONE_NAME = "Dell EMC TimeFinder Clone"
    SM_SNAPSHOT_ENGINE_ETERNUS_SNAP_NAME = "Fujitsu ETERNUS AF / DX Snap"
    SM_SNAPSHOT_ENGINE_ETERNUS_CLONE_NAME = "Fujitsu ETERNUS AF / DX Clone"
    SM_SNAPSHOT_ENGINE_HDS_CLI_CLONE_NAME = "Hitachi Shadow Image (CCI)"
    SM_SNAPSHOT_ENGINE_HDS_CLI_SNAP_NAME = "Hitachi Thin Image (CCI)"
    SM_SNAPSHOT_ENGINE_ORACLE_ZFS_SNAP_NAME = "Oracle ZFS Storage Snap"
    SM_SNAPSHOT_ENGINE_ORACLE_ZFS_CLONE_NAME = "Oracle ZFS Storage Clone"
    SM_SNAPSHOT_ENGINE_DATACORE_SNAP_NAME = "DataCore Snap"
    SM_SNAPSHOT_ENGINE_DATACORE_CLONE_NAME = "DataCore Clone"
    SM_SNAPSHOT_ENGINE_HUAWEI_SNAP_NAME = "Huawei OceanStor Snap"
    SM_SNAPSHOT_ENGINE_HUAWEI_CLONE_NAME = "Huawei OceanStor Clone"
    SM_SNAPSHOT_ENGINE_ETERNUS_SNAPOPCPLUS_NAME = "Fujitsu ETERNUS AF / DX SnapOPC+"
    SM_SNAPSHOT_ENGINE_INFINIDAT_SNAP_NAME = "INFINIDAT InfiniSnap"
    SM_SNAPSHOT_ENGINE_NIMBLE_SNAP_REPLICA_NAME = "HPE Nimble Storage Snap"
    SM_SNAPSHOT_ENGINE_VPLEX_SNAP_NAME = "Dell EMC VPLEX Snap"
    SM_SNAPSHOT_ENGINE_VPLEX_CLONE_NAME = "Dell EMC VPLEX Clone"
    SM_SNAPSHOT_ENGINE_SYMMETRIX_VP_SNAP_NAME = "Dell EMC TimeFinder VP Snap"
    SM_SNAPSHOT_ENGINE_VSA_SNAP_NAME = "Virtual Server Application Snap"
    SM_SNAPSHOT_ENGINE_NEC_ISTORAGE_SNAP_NAME = "NEC DynamicSnapVolume"
    SM_SNAPSHOT_ENGINE_NEC_ISTORAGE_CLONE_NAME = "NEC DynamicDataReplication"
    SM_SNAPSHOT_ENGINE_EXTERNAL_BACKUP_NAME = "External Backup"
    SM_SNAPSHOT_ENGINE_PURE_STORAGE_SNAP_NAME = "Pure Storage FlashArray Snap"
    SM_SNAPSHOT_ENGINE_CVBLOCK_SNAP_NAME = "Block Level Snap"
    SM_SNAPSHOT_ENGINE_LSI_PIT_NAME = "NetApp E-Series PiT"
    SM_SNAPSHOT_ENGINE_NUTANIX_SNAP_NAME = "Nutanix Snapshot"
    SM_SNAPSHOT_ENGINE_NUTANIX_CLONE_NAME = "Nutanix Clone"
    SM_SNAPSHOT_ENGINE_AMAZON_AWS_NAME = "Amazon Web Services"
    SM_SNAPSHOT_ENGINE_NETAPP_FLASHRAY_SNAP_NAME = "NetApp FlashRay Snap"
    SM_SNAPSHOT_ENGINE_VSA_VVOL_SNAP_NAME = "Virtual Server Agent Snap"
    SM_SNAPSHOT_ENGINE_VSA_VVOL_CLONE_NAME = "Virtual Server Agent Clone"
    SM_SNAPSHOT_ENGINE_SOLIDFIRE_SNAP_NAME = "NetApp SolidFire Snap"
    SM_SNAPSHOT_ENGINE_XTREMIO_SNAP_NAME = "Dell EMC XtremIO Snap"
    SM_SNAPSHOT_ENGINE_VMAX_SNAPVX_NAME = "Dell EMC TimeFinder SnapVX"
    SM_SNAPSHOT_ENGINE_UNITY_SNAP_NAME = "Dell EMC Unity Snap"
    SM_SNAPSHOT_ENGINE_SIM_NAME = "CommVault Engine Simulator"
    SM_SNAPSHOT_ENGINE_HDS_TARGETLESS_SNAP_NAME = "Hitachi Targetless Snap (CCI)"
    SM_SNAPSHOT_ENGINE_POWERSTORE_SNAP_NAME = "Dell EMC PowerStore Snap"
    SM_SNAPSHOT_ENGINE_VMAX_SNAPVXCLI_SNAP_NAME = "Dell EMC TimeFinder SnapVX(SYMCLI)"
    SM_SNAPSHOT_ENGINE_MICROSOFT_AZURE_SNAP_NAME = "Microsoft Azure Snap"
    SM_SNAPSHOT_ENGINE_GCP_SNAP_NAME = "Google Cloud Platform Snap"
    SM_SNAPSHOT_ENGINE_STORAGE_CENTER_DSM_SNAP_NAME = "Dell EMC Storage Center Snap (DSM)"


class DistributedClusterType(Enum):
    """Constants for all the cluster types
        currently supported for bigdata apps instances"""
    HADOOP = 2
    GPFS = 3
    GLUSTERFS = 11
    LUSTREFS = 13


class DistributedClusterPkgName(Enum):
    """Constants for all the cluster package names currently supported for big data apps"""
    HADOOP = 'Hadoop'
    GPFS = 'GPFS'
    GLUSTERFS = 'GLUSTERFS'
    LUSTREFS = 'LUSTREFS'
    UXFS = 'uxfs'


class Agents(Enum):
    """Constants for all agents"""
    FILE_SYSTEM = "file system"
    VIRTUAL_SERVER = "virtual server"


# ROLE SPECIFIC CONSTANTS
PERMISSION_ID = {
    1: "Administrative Management",
    2: "Agent Management",
    3: "Agent Scheduling",
    4: "Operations on Storage Policy \\  Copy",
    5: "Upload",
    6: "Download",
    7: "Install Package/Update",
    8: "Library Management",
    9: "License Management",
    10: "MediaAgent Management",
    11: "Library Administration",
    12: "Data Protection/Management Operations",
    13: "Browse",
    15: "Report Management",
    16: "Job Management",
    18: "Alert Management",
    20: "In Place Recover",
    22: "Out-of-Place Recover",
    24: "End User Access",
    25: "Compliance Search",
    26: "VaultTracker Operations",
    27: "Tag Management",
    29: "Legal Hold Management",
    31: "View",
    32: "Annotation Management",
    33: "Execute",
    34: "Add/Append",
    35: "Delete",
    36: "Recover and Download",
    38: "Live Browse",
    39: "In Place Full Machine Recovery",
    40: "Sharing",
    41: "Download Center Management",
    42: "Out of Place Full Machine Recovery",
    65: "Install Client",
    101: "Add, delete and modify a user",
    102: "Add, delete and modify a user group",
    107: "Change security settings",
    109: "Edit Monitoring Policy",
    110: "Execute Monitoring Policy",
    111: "Delete Monitoring Policy",
    115: "Create Schedule Policy",
    116: "Edit Schedule Policy",
    117: "Delete Schedule Policy",
    118: "Edit Schedule Policy Associations",
    134: "File Analytics",
    135: "Email Analytics",
    136: "Web Analytics",
    137: "Data Connectors",
    138: "Events Organizer",
    141: "Change Content",
    145: "Laptop",
    146: "Edge Drive",
    147: "eGovernance",
    148: "DLP",
    149: "eDiscovery",
    150: "Mobile Backup",
    151: "Create Alert",
    152: "Edit Alert",
    153: "Delete Alert",
    154: "Edit Alert Associations",
    155: "Add/Remove Recipients",
    156: "Create Plan",
    157: "Edit Plan",
    158: "Delete Plan",
    159: "Use Plan",
    160: "Create VM Snapshot",
    161: "Delete VM Snapshot",
    162: "Revert VM Snapshot",
    163: "Edit VM",
    164: "Delete VM",
    165: "Renew VM",
    210: "Delete Custom Property",
    215: "Archiving",
    216: "Search Share",
    218: "Use Credential",
    219: "Delete Data",
    220: "Modify Credential Account",
    221: "Create EDiscovery Task",
    222: "Edit EDiscovery Task",
    223: "View EDiscovery Task",
    224: "Delete EDiscovery Task",
    249: "Add Domain",
    250: "Edit Domain",
    251: "Delete Domain",
    252: "Use Proxy",
    253: "Delete Client"
}


WINDOWS_CVLT_PACKAGES_ID = {
    "File System Core": 1,
    "File System": 702,
    "Storage Accelerator": 54,
    "MediaAgent": 51,
    "CommServe": 20,
    "CommServe SNMP Enabler": 21,
    "WorkFlow Engine": 23,
    "CommServe Failover": 24,
    "Application Manager Node": 25,
    "Index Store": 55,
    "SharePoint iDataAgent": 101,
    "Exchange iDataAgent": 151,
    "Exchange Mailbox Archiver Agent": 158,
    "OWA Proxy Enabler": 160,
    "Domino Database": 201,
    "Domino Document": 202,
    "Domino Mailbox Archiver": 203,
    "Notes Add-In Client": 204,
    "Web Server": 252,
    "Compliance Search": 255,
    "Search Engine": 257,
    "Content Extractor": 259,
    "Index Gateway": 263,
    "PDF Converter": 264,
    "DB2 iDataAgent": 351,
    "Oracle iDataAgent": 352,
    "SQL Server": 353,
    "SAP for Oracle": 354,
    "SAP for MaxDB": 355,
    "Sybase iDataAgent": 356,
    "MySQL iDataAgent": 358,
    "Informix iDataAgent": 360,
    "PostgreSQL iDataAgent": 362,
    "Documentum iDataAgent": 363,
    "MongoDB iDataAgent": 381,
    "Splunk": 382,
    "Continuous Data Replicator": 451,
    "Driver for Continuous Data Replicator": 452,
    "VSS Provider": 453,
    "VSS Hardware Provider": 455,
    "IntelliSnap": 504,
    "Driver for File Archiver": 551,
    "File Share Archiver Client": 552,
    "1-Touch Server": 554,
    "CommCell Console": 701,
    "Active Directory iDataAgent": 703,
    "Image Level iDataAgent": 707,
    "Exchange Offline Mining Tool": 711,
    "Virtual Server": 713,
    "External Data Connector": 715,
    "Database Upgrade": 717,
    "Test Automation": 719,
    "High Availability Computing": 725,
    "Command Center": 726,
    "Metrics Server": 727,
    "Content Analyzer": 729,
    "Cloud Apps": 730,
    "Cloud Services": 732,
    "Advanced Indexing Pack": 733,
    "Office 365": 734,
    "VPN Access": 751,
    "Clinical Image Archiving": 752,
    "File System Add-On": 753,
    "Developer SDK - Python": 754,
    "Block Level Replication": 755,
    "CV Tools": 758,
    "DM2 Web services DB": 803,
    "Work Flow Enginge DB ": 808,
    "CVCloud DB": 809,
    "MongoDB": 952,
    "MS Access Database Engine": 953,
    "Message Queue": 954,
    "VCRedist Helper": 955,
    "Data Analysis Toolkit": 957
}


UNIX_CVLT_PACKAGES_ID = {
    "File System Core": 1002,
    "File System": 1101,
    "MediaAgent": 1301,
    "1-Touch Server": 1119,
    "Base0 Module": 1003,
    "Media Explorer": 1110,
    "Resource Pack": 1130,
    "CommCell Console": 1118,
    "CVGxOSSpec": 1903,
    "Application Base": 1004,
    "Serverless Data Manager": 1103,
    "Storage Accelerator": 1305,
    "Domino Mailbox Archiver": 1053,
    "SAP for Oracle": 1205,
    "SAP for Hana": 1210,
    "Image Level": 1104,
    "UNIX ImageLevel ProxyHost": 1125,
    "File Archiver for UNIX": 1109,
    "Cassandra": 1211,
    "Oracle": 1204,
    "IntelliSnap": 1402,
    "Storage Pool": 1139,
    "File System Core": 1002,
    "Hedvig Assist": 1176,
    "Continuous Data Replicator": 1114,
    "DB2": 1207,
    "Documentum": 1126,
    "Informix": 1201,
    "SAP for MaxDB": 1206,
    "MySQL": 1208,
    "External Data Connector": 1128,
    "CommServe": 1020,
    "QSnap": 1401,
    "SAP Archive": 1129,
    "Cloud Apps": 1140,
    "Command Center": 1135,
    "Index Store": 1306,
    "Content Extractor": 1173,
    "Data Analysis Toolkit": 1601,
    "WebServer": 1174,
    "WorkFlow Engine": 1023,
    "Novell OES File System": 1121,
    "Virtual Server": 1136,
    "File System for OpenVMS": 1138,
    "PostgreSQL": 1209,
    "Domino Database": 1051,
    "Domino Document": 1052,
    "SCSI Driver": 1105,
    "Sybase": 1202,
    "Hadoop": 1282,
    "CVGxRootDVD": 1902,
    "File System for IBM i": 1137,
    "SAN Storage Server": 1304,
    "Developer SDK - Python": 1154,
    "Index Gateway": 1156,
    "Message Queue": 1602,
    "Content Analyzer": 1108,
    "SQL Server": 1212,
    "High Availability Computing": 1157,
    "Cloud Services": 1178,
    "Test Automation": 1153,
    "MongoDB": 1281,
    "Splunk": 1283,
    "Advanced Indexing Pack": 1603,
    "CV Tools": 1179,
    "CommServe DB": 851,
    "Database Upgrade": 1180,
    "Metrics Server": 1177,
    "Commserve AppStudio DB": 861,
    "Commserve Audit DB": 858,
    "Commserve Cache DB": 859,
    "Metrics Reporting DB": 855,
    "DM2 Web services DB": 852,
    "Commserve History DB": 856,
    "Commserve ResourceMgr DB": 857,
    "Commserve Template DB": 860,
    "Workflow Engine DB": 854
}
