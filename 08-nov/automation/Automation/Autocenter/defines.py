# These are strings seen by end users.
# VARIABLES
LOCKFILE_NAME = "AUTOMATION_CENTER.LOCK"
CONFIG_FILE_NAME = 'config.ini'

# ERROR STRINGS
CONFIG_FILE_NOT_FOUND = "Failed to load config file [%s]."
UPDATE_BIN_TRAN_KEY = 'UpdateBinTran'
SP_TRAN_REG_SZ = 'SP_Transaction'
TC_MONITOR_THRESHOLD = 900  # seconds
FAILED_READ_SETTINGS_DB = "Failed to read settings from database."

# These are strings seen by end users.
# VARIABLES
WEB_UPLOAD_LOG_URL = 'http://autocenter.automation.commvault.com/server_side/scripts/uploadFailLog.php'


# Input tags.
TESTCASEURL = "testcaseurl"
FAILUREURL = "testcasefailureurl"
TESTSET_URL = "testseturl"
LOG_UPLOAD = "loguploadurl"
AUTOCENTER = 'autocenter'
AC_HOST_MACHINE = "hostmachine"
AC_MACHINE_NAME = "name"
AC_USER_NAME = "user"
AC_PASSWORD = "password"
AUTOCENTER_PASSWORD = "autocenter_password"
AC_REQUEST_ID = 'requestID'
AC_TESTSET_ID = "ac_testset_id"
AC_CONTROLLER_NAME = "ac_controller_name"
AC_SKIP_TC_ID_IF_FAILED = "skip_tc_id_if_failed"
NO_CONTROLLER_FOUND_ERROR_ = "Failed to read controller machines from database."
DEV_AUTOCENTER = "Dev-Autocenter@commvault.com"
MAIL_SERVER = 'mail.commvault.com'
SMTP_SERVER = "smtpserver"
SENDER = "sender"
RECEIVER = "receiver"

# Autocenter execution status
AC_PASS = 1
AC_FAIL = 2
AC_RUNNING = 3
AC_UNRESPONSIVE = 3
