# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for maintaining install related Messages."""

QINSTALL_PKG_INFO_MISSING_AFTER_DOWNLOAD = "Required media version [Build.SPversion] with transaction Id [transId] "\
    " is missing in the Software Cache. CommServe may be installed with a lower version media. Please check the "\
    "media in Software Cache and try updating the CommServe before updating clients."
QINSTALL_PKG_INFO_MISSING = "Unable to obtain package information required to install selected packages."
QINSTALL_ERROR_REG_SERVICE = "Failed to Install File System Core Package. A Firewall may be preventing connection. " \
    "Username/password provided could be incorrect. Could not connect to or start Remote Registry Service on client. "\
    "Remote Registry Service may be disabled. Make sure you can connect to Remote Machine Registry from "\
    "Software Cache machine you are using."
QINSTALL_ERROR_LOGON = "Client might not have connectivity from CommServer/Remote Cache or " \
                       "user credentials provided are incorrect.<br/>Source: CS_NAME, Process: DistributeSoftware"
QINSTALL_REPAIR_FAILED_CLIENT_NOT_REACHABLE = "Communication services may not be running on the client. "\
    "Please re-submit the job with client machine credentials."
QUPDATE_UNREACHABLE_CLIENT = "Cannot establish a connection to client. Probable Reasons: " \
                             "1. Client services may be down. " \
                             "2. There may be a firewall preventing connection. A network connection may not exist."
QUPDATE_UNREACHABLE_CLIENT_UPDATE = "Cannot establish a connection to client. There may be a firewall preventing " \
                                    "connection. A network connection may not exist."
QUPDATE_UNREACHABLE_CLIENT_SERVICES = "Client services may be down"
QINSTALL_SWCACHE_PACKAGES_MISSING =	"Remote Software Cache is empty or does not contain the required packages for "\
    "client's operating system. Make sure that required packages are present in CommServe cache and remote cache is "\
    "configured to sync packages. Remote cache's sync settings of packages can be configured from 'Add/Remove "\
    "Software Configuration' window."
QINSTALL_ERROR_CREATE_TASK = "Failed to install File System Core Package, the credentials entered may not have "\
    "permission to use WMI on remote machine. Please check WMI configuration and user credentials."
QINSTALL_LOW_DISK_SPACE = "Install cannot proceed, Low disk space on client."
QINSTALL_ERROR_ACCESS_REMOTE_REG = "Failed to install Base Package. Failed to access remote registry"
QUPDATE_LOW_CACHE_SPACE = "Install Updates cannot proceed, Low disk space on the client."
QINSTALL_BASE_PACKAGE_FAILED_GENERIC_WRONG_CREDENTIALS = "Failed to install File System Core Package with error "\
    "[Failed to compute the binary set name of client [CLIENT_NAME] with error " \
    "[TIME_STAMP:The user name or password is incorrect."
QINSTALL_FAILED_TO_DETERMINE_PROCESSOR = "Failed to install File System Core Package, could not determine " \
                                         "processor/OS type of client"
QINSTALL_FAILED_TO_COMPUTE_BINARY_SET = "Failed to install File System Core Package with error " \
                                        "[Failed to compute the binary set name of client [CLIENT_NAME] with error " \
                                        "[1140851256:The user name or password is incorrect.].]. " \
                                        "For more information, visit [[https://documentation.commvault.com/" \
                                        "commvault/v11/article?p=1971.htm]]" \
                                        "<br>Source: CS_NAME, Process: DistributeSoftware"
QINSTALL_CONNECTION_ERROR = "Connection error. Check if services are running on client"
QDOWNLOAD_SOFTWARE_SYNC_ERROR = "Sync failed for software cache(s) [MACHINE_NAME]."
