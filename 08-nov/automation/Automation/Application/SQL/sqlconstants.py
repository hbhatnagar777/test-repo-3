"""Helper file for maintaining SQL Automation Constants.

Any constant values related to SQL Automation goes in this file.

"""

# constants for renaming database on restore
DATABASE_ORIG_NAME = 'orig_name'
DATABASE_NEW_NAME = 'new_name'

# database restore format
VDI_RESTORE_FORMAT = "|{0}|#12!{1}|#12!{2}|#12!{3}|#12!{4}"

# dict for sql subclient properties
SQL_SUBCLIENT_PROP_DICT = {
    'subclientRecoveryType': 1,
    'disableAutoDiscovery': True,
    'numberOfBackupStreams': 2,
    'numberOfTransactionLogStreams': 2,
    'backupRules': 3,
    'blockSize': 65536,
    'bufferCount': 20,
    'maxTransferSize': 2097152,
    'disableLogConsistencyCheck': False
}

SQL_SUBCLIENT_STORAGE_DICT = {
    "networkAgents": 2,
    "applicableReadSize": 2048,
    "softwareCompression": 0
}

# sql job error strings
ERROR_OVERWRITE = "not selected unconditional overwrite"

# sql database access states
RESTRICTED_USER = "RESTRICTED_USER"
MULTI_USER = "MULTI_USER"
SINGLE_USER = "SINGLE_USER"

# sql subclient types
SUBCLIENT_DATABASE = "DATABASE"
SUBCLIENT_FFG   = "FILE_FILEGROUP"

# sql restore types
DATABASE_RESTORE = 'DATABASE_RESTORE'
STEP_RESTORE = 'STEP_RESTORE'
RECOVER_ONLY = 'RECOVER_ONLY'

# sql recovery types
STATE_RECOVER = 'STATE_RECOVER'
STATE_NORECOVER = 'STATE_NORECOVER'
STATE_STANDBY = 'STATE_STANDBY'

# sql log files
SQL_BACKUP_LOG = 'SQLBackup.log'
SQL_RESTORE_LOG = 'SQLRestore.log'

# sql azure
SQL_AZ_INS_SUFFIX = 'database.windows.net'