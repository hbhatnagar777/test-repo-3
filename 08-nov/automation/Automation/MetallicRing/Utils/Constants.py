# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" It contains constants which will be used throughout the ring configuration."""

import os
import enum
from AutomationUtils.constants import AUTOMATION_DIRECTORY


class Infra(enum.Enum):
    """Enum for representing the infrastructure types"""
    WS = 1
    WC = 2
    MA = 3
    IS = 4
    NWP = 5
    CS = 6


class VMHost(enum.Enum):
    """Enum for representing the infrastructure types"""
    HYPERV = 1
    VSPHERE = 2
    AZURE = 3


class OSType(enum.Enum):
    """Enum for representing the infrastructure types"""
    WINDOWS = 1
    LINUX = 2


class WaitTime(enum.Enum):
    """Enum for representing the different wait times"""
    ONE_MIN = 1
    TWO_MIN = 2
    THREE_MIN = 3


class RingProvisionType(enum.Enum):
    STRICT = 1
    VIRTUALIZATION = 2
    CONTAINERS = 3
    CUSTOM = 4


class CustomClientGroups(enum.Enum):
    CS = "Infrastructure - CommServe"
    MA_ALL = "Infrastructure - Media Agents (All)"
    MA_WIN = "Metallic Windows MAs"
    MA_UNIX = "Metallic Linux MAs"
    MA_UNIX_TENANT = "Tenant Linux MAs"
    WEC = "Infrastructure - Web Consoles (All,DMZ)"
    WES = "Infrastructure - Web Servers (All)"
    AZURE_MA_US_EAST_2 = "Infrastructure - Azure MAs (East US2)"
    INFRA_PROXIES = "Infrastructure - Proxies (All,DMZ)"


class VisibilityLevel(enum.Enum):
    SOFTWARE = 16
    CLOUD = 512


JOB_STREAMS = 3000

# index server roles

role_name_dict = {"Data Analytics": "ais",
                  "Exchange Index": "eis",
                  "OneDrive Index": "ois",
                  "SharePoint Index": "spis",
                  "Teams Index": "tis",
                  "Dynamic365 Index": "dis",
                  "ActiveDirectory Index": "adis"
                  }

# job status constants

PASSED = "Passed"
FAILED = "FAILED"
STARTED = "STARTED"
RESUMED = "RESUMED"

# common constants

SERVER = "Server"
OEM_REGISTRY = "nCurrentOEMID"
METALLIC_OEM = 119
WFS_TO_DISABLE = ["DeleteLibraryMountPathAuthorization"]
WC_URL = "https://%s/webconsole/clientDetails/fsDetails.do?clientName=CLIENTNAME"
SCHEDULE_LIST = ["System Created Install Software",
                 "System created Download Software",
                 "System Created DBMaintenance schedule",
                 "System Created Install Software for Laptops"]

SCHEDULE_INSTALL_UPDATES_JSON = {
    "schedule_name": "Install updates every week Sunday at 1:00 PM",
    "freq_type": "weekly",
    "active_start_time": "13:00",
    "repeat_weeks": 1,
    "weekdays": ["Sunday"]
}

SCHEDULE_DOWNLOAD_SOFTWARE_JSON = {
    "schedule_name": "Download updates every week Sunday at 9:00 AM",
    "freq_type": "weekly",
    "active_start_time": "09:00",
    "repeat_weeks": 1,
    "weekdays": ["Sunday"]
}

SCHEDULE_SERVER_PLAN_JSON = {
    "schedule_name": "Download updates every week Sunday at 9:00 AM",
    "freq_type": "weekly",
    "active_start_time": "09:00",
    "repeat_weeks": 1,
    "weekdays": ["Sunday"]
}

REPORT_NAME = "ReportName"
REPORT_XML = "ReportXML"
REPORT_PATH = os.path.join(AUTOMATION_DIRECTORY, "MetallicRing", "Utils", "ReportXMLs")
REPORT_DICT_LIST = [{REPORT_NAME: "No Backup for 4 days", REPORT_XML: REPORT_PATH + "\\No Backup for 4 days.xml"},
                    {REPORT_NAME: "Office365BackupHealth", REPORT_XML: REPORT_PATH + "\\Office365BackupHealth.xml"},
                    {REPORT_NAME: "Tenant Account Users", REPORT_XML: REPORT_PATH + "\\Tenant Account Users.xml"},
                    {REPORT_NAME: "User login summary", REPORT_XML: REPORT_PATH + "\\User login summary.xml"}]

# cloud storage constants
# %s should be replaced by ring name.
# Ex: scn-drlib-%s should be scn-drlib-m051. m051 is the ring name
CLOUD_STORAGE_CREDS = "DR_SA_%s"
CLOUD_STORAGE_LIBRARY_NAME = "scn-drlib-%s"
CLOUD_STORAGE_CONTAINER_NAME = "scn-drlib-%s"
CLOUD_STORAGE_CLASS = "Use container's default storage class"
CLOUD_STORAGE_TYPE = "Microsoft Azure Storage"

CLOUD_STORAGE_POOL_NAME = "Infrastructure-Metallic"
CLOUD_SERVER_PLAN_NAME = "Infrastructure-Metallic-Server-Plan"

LOCAL_STORAGE_POOL_NAME = "Infrastructure-Metallic"
LOCAL_SERVER_PLAN_NAME = "Infrastructure-Metallic-Server-Plan"

CMD_FORMATTED_OP = "formatted"

RING_EMAIL_SUFFIX = "@ringprov.commvault.com"
RING_FROM_EMAIL_SUFFIX = "@commvault.com"

METALLIC_RUN_CONFIG_DIRECTORY_NAME = "MetallicRunConfig"

METALLIC_CONFIG_DIRECTORY = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration"
)

METALLIC_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "metallic_config.json"
)

METALLIC_CONTROLLER_INPUT_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "controller_input.json"
)

METALLIC_DEPLOYMENT_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "deployment_metallic_template.json"
)

WEB_CONSOLE_CERTIFICATE_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "WebConsoleCertificate", "testlab.commvault.com.pfx"
)

HYPERV_CONFIG_TEMPLATE_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "TerraformConfig", "HyperV", "hyperv_config.tf_template"
)

HYPERV_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "TerraformConfig", "HyperV", "%s", "hyperv_config.tf.json"
)

VSphere_CONFIG_TEMPLATE_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "TerraformConfig", "VSphere", "vsphere_config.tf_template"
)

VSphere_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "TerraformConfig", "VSphere", "vsphere_config.tf.json"
)

ALERT_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "alerts_config.json"
)

ADDITIONAL_SETTING_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "additional_settings_config.json"
)

CLIENT_GROUP_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "client_group_config.json"
)
SMART_FOLDER_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "smart_folder_config.json"
)

NETWORK_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Configuration", "firewall_config.json"
)

SQLLITE_DB_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicRing", "Utils", "MetallicDB", "MetallicRing.db"
)

# TERRAFORM CONSTANTS

TERRAFORM_INIT_SUCCESS = "Terraform has been successfully initialized!"
TERRAFORM_VALIDATION_SUCCESS = "The configuration is valid."
TERRAFORM_PLAN_SUCCESS = "Plan: %s to add, 0 to change, 0 to destroy."
TERRAFORM_APPLY_SUCCESS = "Apply complete! Resources: %s added, 0 changed, 0 destroyed."
TERRAFORM_DESTROY_SUCCESS = "Destroy complete! Resources: 0 added, 0 changed, %s destroyed."

SECURITY_ASSOCIATION_ALL = {
    "entities": {
        "entity": [
            {
                "_type_": 0,
                "flags": {
                    "includeAll": True
                }
            }
        ]
    },
    "properties": {
        "role": {
            "roleName": ""
        }
    }
}

ENTITY_TYPE_COMMCELL_ENTITY = 1
ENTITY_TYPE_IDENTITY_SERVER = 61
ENTITY_TYPE_CG_STR = "CLIENT_GROUP"
ENTITY_TYPE_CLIENT_STR = "CLIENT"
ROLE_TENANT_OPERATOR = "Tenant Operator"
ROLE_CC_ADMIN = "Commcell Admin"
ROLE_CC_ADMIN_PERMISSION = ["Annotation Management", "Browse", "Change Content",
                            "Data Protection/Management Operations",
                            "Delete Client", "End User Access", "In Place Recover",
                            "Install Package/Update", "Live Browse", "Out-of-Place Recover", "Overwrite on Restore",
                            "Run Command with System Account", "Run Command with User Account", "Tag Management",
                            "VPN Management", "Archiving", "Edge Drive", "Laptop", "Mobile Backup", "DLP"]

ROLE_CC_ADMIN_CATEGORY = ["Alert", "Analytics", "Billing", "Client Group", "Commcell", "Content Director",
                          "Credential Management", "Custom Property", "Developer Tools", "EDiscoveryTask",
                          "Global",
                          "Monitoring Policy", "Plan", "Region Management", "ResourcePool", "Schedule Policy",
                          "Storage Management", "Storage Policy Management", "Storage Provisioning",
                          "Subclient Policy", "User Management", "VM Operations", "Webhook"]

SNAP_NAME = "VM Name %s - Snap before ring configuration. Time - %s"
WIN_EXP_DOMAIN_ADDED = "Given Machine is already part of a domain"
UNIX_EXP_DOMAIN_ADDED = "Already joined to this domain"
EXP_WINRM_REBOOT_ERROR = "The WinRM client received an HTTP server error status (500), but the remote " \
                         "service did not include any other information about the cause of the failure."
EXP_WSM_REBOOT_ERROR = "The HTTP error (12152) is: The server returned an invalid or unrecognized response"
FIREWALL_NOT_RUNNING_ERROR = "firewalld is not running"
WC_CLIENT_GROUP_NAME = "Infrastructure - Web Consoles (All,DMZ)"
WS_CLIENT_GROUP_NAME = "Infrastructure - Web Servers (All)"
MAS_WIN_CLIENT_GROUP_NAME = "Windows MAs"
MAS_UNIX_CLIENT_GROUP_NAME = "Linux MAs"
INFRA_CLIENT_GROUP_NAME = "Infrastructure (All)*"
ADD_SETTING_WEBCONSOLE_URL = "WebConsoleURL"
ADD_SETTING_WEBCONSOLE_URL_VALUE = "%s/webconsole/clientDetails/fsDetails.do?clientName=CLIENTNAME"
ADD_SETTING_CUSTOM_HOME = "customHomeUrl"
ADD_SETTING_CUSTOM_HOME_VALUE = "%s/commandcenter/#/serviceCatalogV2"
ADD_SETTING_PACKAGE_WIN32 = "PackageUrlWin32"
ADD_SETTING_PACKAGE_WIN64 = "PackageUrlWin64"
ADD_SETTING_PACKAGE_MAC = "PackageUrlMac"
CG_SCOPE_COMMCELL = "<<commcell_name>>"
CG_SCOPE_USER = "<<user_name>>"
CG_VALUE_RING = "<<ring_id>>"
CG_FILTER_VALUE_DOMAIN = "<<domain_name>>"
CG_ASSOC_CG_KEY = "Associated Client Group"
CG_DISPLAY_NAME_KEY = "Client Display Name"
CG_OS_TYPE_KEY = "OS Type"
CG_HOSTNAME_KEY = "Hostname"
CG_CLIENT_PROXY = "Client acts as proxy"
CG_UNIVERSAL_INSTALLER_NAME = "Universal Installer"
CG_CLEANROOM_AZURE_US = "Infrastructure - Cleanroom - Azure (East US2)"
CMP_NAME = "SECompany01"
CMP_USER_NAME = "SE_01"
GP_VB_LEVEL_KEY = "Patch Visibility Level"
WEBCONSOLE_TOMCAT_REG_KEY = "sZTOMCATHOME"
WEBCONSOLE_REG_SECTION = "WebConsole"
WEBCONSOLE_WS_HOST_REG_KEY = "sZDM2WEBSERVERHOSTNAME"
WEBCONSOLE_CONF_FOLDER = "conf"
WEBCONSOLE_SERVER_XML_FILE = "server.xml"
WEBCONSOLE_SERVER_DEST_XML_FILE = "server_backup_automation%s.xml"
WEBCONSOLE_CERT_NAME = "testlab.commvault.com.pfx"
WEBCONSOLE_TOMCAT_SERVICE = "GxTomcatInstance001"
WEBCONSOLE_UNIX_TOMCAT_SERVICE = "Tomcat"
REG_SECTION_SESSION = "Session"
REG_KEY_CVD_PORT = "nCVDPORT"
REGION_TYPE_WORKLOAD = "WORKLOAD"
REGION_EASTUS2 = "eastus2"
REGION_EASTUS2_CODE = "c1us02"
WORKFLOW_NAME = "workflowName"
CSR_WORKFLOW = "Cloud Storage Archive Recall"
WF_ROLE = "ExecuteWorkflowRole"
WF_EXEC_PERM = "Execute Workflow"
ROLE = "role"
REQUEST_TYPE_UPDATE = "UPDATE"
UG_TENANT_ADMIN = "Tenant Admin"
UG_MASTER = "master"
CVD_SERVICE = "cvd"
CVD_PORT = 8400
HTTPS_PROTOCOL = "https"
HTTP_PROTOCOL = "http"
SMART_FOLDER_XML = "<App_PerformSmartFolderReq operationType='1'>" \
                   "<folderDetail description='' isAutomatic='1'>" \
                   "<parentEntity _type_='27' appName='' " \
                   "applicationId='0' backupsetId='0' backupsetName='' " \
                   "clientGroupId='0' clientGroupName='' clientId='0' clientName='' " \
                   "instanceId='0' instanceName='' subclientId='0' " \
                   "subclientName=''/>" \
                   "<folder folderType='28' smartFolderId='0' smartFolderName='%s'/>" \
                   "<folderRule op='0'>" \
                   "<rules>" \
                   "<rule op='0'>" \
                   "<rules>" \
                   "<rule filterID='14' propID='%s' propType='2' value='%s'/>" \
                   "</rules>" \
                   "</rule>" \
                   "</rules>" \
                   "</folderRule><folderSecurity associationsOperationType='1'/></folderDetail>" \
                   "</App_PerformSmartFolderReq>"

MANUAL_FOLDER_XML = "<App_PerformSmartFolderReq operationType='1'>" \
                    "<folderDetail description='' isAutomatic='0'>" \
                    "<parentEntity _type_='27' appName='' applicationId='0' backupsetId='0' backupsetName='' " \
                    "clientGroupId='0' clientGroupName='' clientId='0' clientName='' instanceId='0' instanceName='' " \
                    "subclientId='0' subclientName=''/>" \
                    "<folder _type_='127' folderType='28' smartFolderId='0' smartFolderName='%s'/>" \
                    "%s" \
                    "<folderSecurity associationsOperationType='1'/>" \
                    "</folderDetail></App_PerformSmartFolderReq> "

DELETE_FOLDER_XML = "<App_PerformSmartFolderReq operationType='3'>" \
                    "<folderDetail><folder smartFolderName='%s'/></folderDetail></App_PerformSmartFolderReq>"

ALERT_CREATE_REQUEST = {
    "alert_type": 0,
    "notif_type": [
        1
    ],
    "notifTypeListOperationType": 0,
    "alert_severity": 0,
    "nonGalaxyUserOperationType": 0,
    "criteria": 0,
    "associationOperationType": 0,
    "entities": {},
    "userListOperationType": 0,
    "users": ["commcell users"],
    "alert_name": "alert name",
    "nonGalaxyList": {
        "nonGalaxyUserList": [
            {
                "nonGalaxyUser": "Email ID to Notify"
            }
        ]
    }
}

ALERT_ENTITY_TYPE_MA = "media_agents"
ALERT_ENTITY_TYPE_ALL = "All"

ALERT_CRITERIA = {
    "Succeeded": 1,
    "Alert every 2 attempts (Phase failures)": 2,
    "Failed": 3,
    "Skipped": 4,
    "Delayed by 1 Hrs": 5,
    "List Media": 6,
    "Initiated": 7,
    "Rolled Back": 8,
    "Media Needs Import": 9,
    "Media Handling Required": 24,
    "Media Picked up": 11,
    "Media Reached Destination": 12,
    "Media Returned to Source": 13,
    "Job Activity": 14,
    "ASR Backup Has occured.": 15,
    "Properties Modified": 16,
    "Alert Modified": 17,
    "Disk Space Low": 18,
    "Force deconfigured": 19,
    "Library went Offline": 20,
    "Scheduler Changes": 21,
    "Insufficient Storage": 22,
    "Media Handling Errors": 23,
    "Media Mount and Usage Errors": 25,
    "Maintenance Required": 26,
    "Maintenance Occured": 27,
    "User overwrite of Media": 28,
    "Drive went Offline": 29,
    "MediaAgent went Offline": 30,
    "Mountpath went Offline": 31,
    "Alert every 2 attempts (Network failures)": 32,
    "Exchange Journal Mailboxes 10000 Message Count Exceeded": 33,
    "Job Results Folder Low Space": 34,
    "Index Cache Folder Low Space": 35,
    "Updates Available": 38,
    "Release Upgrade Required": 39,
    "Updates Required": 40,
    "Media Ready in CAP Alert": 41,
    "Log file reached high watermark": 42,
    "Log file volume reached low watermark": 43,
    "No log play activity": 44,
    "No log transfer activity": 48,
    "No Data Protection": 46,
    "Classification Failed": 47,
    "Virtual Servers Added": 49,
    "V2 upgraded to V3": 50,
    "Media Recalled": 51,
    "Increase in Data size by 10 %": 52,
    "Decrease in Data size by 10 %": 53,
    "Job Started": 54,
    "Alert every 3 failed login attempts": 55,
    "Auxilary copy fallen behind alert": 56,
    "Job Completed with Errors": 57,
    "Alert Commserver license expires within 30 days": 58,
    "Alert Commserver license expires within 99 days": 60,
    "Log monitoring": 61,
    "Simpana Event monitoring": 62,
    "Non-encrypted media exported": 63,
    "Content Index data fallen behind alert": 64,
    "No Backup for last 3 Days": 65,
    "Certificate for client expired/revoked": 66,
    "Job exceeded running time": 67,
    "Failed files count exceeded threshold": 68,
    "Failed files Percent exceeded threshold": 69,
    "DDB Store got corrupted": 70,
    "Backup for subclient failed consecutively for 3 attempts": 71,
    "DDB disk space low": 72,
    "Alert when jobs in pending state exceed 30 percent or count of 15": 73,
    "Data backed up exceeds 5 GB": 74,
    "Custom Alert": 75,
    "Job Commmitted": 76,
    "Disk space low for Job results directory": 77,
    "Disk Space low for Index Cache": 78,
    "Disk Space low for Galaxy directory": 79,
    "Quota exceeded": 80,
    "Quota reaching threshold": 81,
    "Quota validation failed": 82,
    "Edge drive/share operations": 83,
    "DDB went Offline": 84,
    "Increase in object count by 10 percent": 85,
    "Failover started": 86,
    "Failover activity": 87,
    "Failover completed": 88,
    "Failover failed": 89,
    "Production Commserv is not reachable": 90,
    "Production Commserv is not running": 91,
    "Passive node is not reachable": 92,
    "Anomaly in events": 93,
    "Runtime anomaly in jobs": 94,
    "Anomaly in number of pending jobs": 95,
    "Anomaly in number of failed jobs": 96,
    "File system Quota Exceeded": 98,
    "File system Quota reaching threshold": 99,
    "File system quota validation failed": 100,
    "Job activity anomaly": 101,
    "Anomaly in number of succeeded jobs": 102,
    "Alert when client is offline for 15 Minutes": 103,
    "Anomaly in DDB pruning": 104,
    "Smart MA state Management": 105,
    "Job succeeded with warnings": 106,
    "Trigger Report (need to hide!)": 200,
    "The current server configuration is invalid.": 10000,
    "Usage Analysis Processing is not enabled.": 10001,
    "Usage Logging is not enabled.": 10002,
    "Site Database is not online.": 10003,
    "Content Database site warning.": 10004,
    "Site Collection quota size exceeded.": 10005,
    "Site Collection has no usage quota assigned.": 10006,
    "Virtual Server has RecycleBin Disabled.": 10007,
    "Virtual Server has RecycleBinCleanUp Disabled.": 10008,
    "Unused disk space": 10009,
    "Partition is almost full": 10010,
    "Logical Volume is almost full": 10011,
    "Volume Group offline": 10012,
    "Logical Volume offline": 10013,
    "User exceeded file count soft limit quota": 10014,
    "Advisory Name for [UXFSAgent_GroupExceededFCSLe]": 10015,
    "User exceeded file count hard limit quota": 10016,
    "Group exceeded file count hard limit quota": 10017,
    "User exceeded block soft limit quota": 10018,
    "Group exceeded block soft limit quota": 10019,
    "User exceeded block hard limit quota": 10020,
    "Group exceeded block hard limit quota": 10021,
    "Volume is full": 10022,
    "Windows automatic updates are disabled": 10024,
    "Anti virus software might not be installed": 10025,
    "Software Firewall might not be installed": 10026,
    "User exceeded storage space soft limit.": 10027,
    "User exceeded storage space hard limit.": 10028,
    "Group exceeded storage space soft limit.": 10029,
    "Group exceeded storage space hard limit.": 10030,
    "File system quotas not enabled.": 10031,
    "Auto create statistics is disabled": 10032,
    "Auto update statistics is disabled": 10033,
    "Autoshrink is enabled": 10034,
    "Autoclose is enabled": 10035,
    "Advisory Name for [SQLAgent_DatabaseNotBackedUpAdvisory]": 10036,
    "Database log not backed up": 10037,
    "Simple recovery mode of production database": 10038,
    "Database in single-user mode": 10040,
    "Logical scan fragmentation for Index exceeds limit": 10041,
    "Extent scan fragmentation for Index exceeds limit": 10042,
    "Pool is full": 10043,
    "User is close to storage space quota": 10044,
    "Failing monitoring services of Exchange Server": 10045,
    "Excessive CPU utilization of Exchange Server": 10046,
    "Advisory Name for [ExchAgent_ClusterFailureAdvisory]": 10047,
    "Advisory Name for [ExchAgent_LowMemoryAdvisory]": 10048,
    "Disk space limited for Exchange Server": 10049,
    "Database has too few control files": 10050,
    "Database has guessable passwords": 10051,
    "Database public account has system privileges": 10052,
    "Database has users with unlimited login attempts": 10053,
    "Database public has execute privileges": 10054,
    "Advisory Name for [OracleAgent_DatabaseNoSpfileAdvisory]": 10055,
    "Advisory Name for [OracleAgent_DatabaseDictionaryManagedAdvisory]": 10056,
    "System tablespace has rollback": 10057,
    "Instance does not have archivelog mode": 10058,
    "Instance does not have auto undo": 10059,
    "Instance does not have assm": 10060,
    "Tablespace has unlimited extension": 10061,
    "Tablespace has both rollback and data": 10062,
    "Advisory Name for [OracleAgent_TablespaceNoFreeSpaceAdvisory]": 10063,
    "Advisory Name for [OracleAgent_SegmentTooManyExtentsAdvisory]": 10064,
    "Advisory Name for [OracleAgent_InstanceNotEnoughRedoSpaceAdvisory]": 10065,
    "Advisory Name for [OracleAgent_InstanceAverageWaitAdvisory]": 10066,
    "Advisory Name for [OracleAgent_UserTempTablespaceAsPermanentAdvisory]": 10067,
    "Advisory Name for [OracleAgent_UserSystemTablespaceAsDefaultAdvisory]": 10068,
    "Advisory Name for [OracleAgent_TablespaceUserDataInSystemAdvisory]": 10069,
    "Advisory Name for [OracleAgent_TableTooManyIndexesAdvisory]": 10070,
    "Advisory Name for [OracleAgent_TableChainedRowsAdvisory]": 10071,
    "NAS filer is not reachable": 10072,
    "NAS logical volume is full": 10073,
    "NAS logical volume is unavailable": 10074,
    "NAS CIFS share: logical volume is unavailable": 10075,
    "NAS CIFS share: logical volume is full": 10076,
    "NAS NFS share: logical volume is unavailable": 10077,
    "NAS NFS share: logical volume is full": 10078,
    "NAS Celerra is not reachable": 10079,
    "NAS Celerra Data Mover is not available": 10080,
    "NAS Celerra primary Data Mover has no standby": 10081,
    "NAS Celerra VDM is not replicated": 10082,
    "NAS Celerra slice volume is not in Storage Pool/Meta Volume": 10083,
    "NAS Celerra stripe volume is not in Storage Pool/Meta Volume": 10084,
    "NAS Celerra Meta Volume has no client volume or file system": 10085,
    "NAS Celerra Storage Pool is full": 10086,
    "NAS Celerra automatic extension is disabled for Storage Pool": 10087,
    "NAS Celerra disk volumes cannot be added to Storage Pool": 10088,
    "Advisory Name for [NASAgent_CelerraSPOvercommitAdvisory]": 10089,
    "Advisory Name for [NASAgent_FileSystemFullAdvisory]": 10090,
    "Advisory Name for [NASAgent_FileSystemNotSharedAdvisory]": 10091,
    "NAS Celerra max number of nested mount points under NMFS root": 10092,
    "NAS Celerra checkpoint name has invalid extension": 10093,
    "NAS Celerra quota policy is wrong for CIFS": 10094,
    "Advisory Name for [NASAgent_CIFSShareFileSystemUnavailableAdvisory]": 10095,
    "NAS Celerra CIFS share: CIFS server is unavailable": 10096,
    "NAS Celerra CIFS share: Data Mover is unavailable": 10097,
    "NAS CIFS share: file system is full": 10098,
    "NAS Celerra CIFS share: Storage Pool is full": 10099,
    "NAS file system hosting iSCSI LUNs is exported via CIFS share": 10100,
    "NAS Celerra NFS Share: Data Mover is unavailable": 10101,
    "NAS NFS Share: file system is full": 10102,
    "NAS Celerra NFS Share: Storage Pool is full": 10103,
    "NAS file system hosting iSCSI LUNs is exported via NFS share": 10104,
    "Advisory Name for [NASAgent_NetworkFSNotMountedAdvisory]": 10105,
    "NAS storage quota on quota tree exceeded Celerra max limit": 10106,
    "NAS storage quota for user exceeded Celerra max limit": 10107,
    "NAS storage quota for group exceeded Celerra max limit": 10108,
    "NAS vFiler is not available": 10109,
    "Advisory Name for [NASAgent_AggVolumeFullAdvisory]": 10110,
    "NAS aggregate is unavailable": 10111,
    "NAS aggregate is overcommitted": 10112,
    "Exchange Mailbox Store dismounted": 10113,
    "Exchange Public Folder Store dismounted": 10114,
    "Overapping Partitions": 10115
}

EMAIL_HTML_CONSTANT = """<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SaaS Ring Configuration Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            font-size: 13px;
        }
        .header {
            font-size: 20px;
            padding: 15px;
            background-color: #854896;
            border-bottom: 1px solid #ddd;
            color: white;
        }
        .container {
            width: 100%;
            background: #ffffff;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            padding: 20px;
            text-align: left;
        }
        .content {
            padding: 20px;
        }
        .info-label {
            font-size: 1rem;
            margin: 10px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #dddddd;
            text-align: left;
            padding: 12px;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
    </style>
</head>
<body>
	<div class="header">
		<h3>SaaS Ring Configuration Report</h3>
	</div>
	<div class="content">
		<p><b>Ring URL</b> - <<<RING_NAME>>>.commvault.com</p>
		<p><b>CommCell Name</b> - <<<COMMCELL_NAME>>></p>
		<table>
			<tr>
				<th>Step</th>
				<th>Task Name</th>
				<th>Status</th>
				<th>Start Time</th>
				<th>End Time</th>
				<th>Reason</th>
			</tr>
			<<<TABLE_DATA>>>
		</table>
	</div>
</body>
</html>
"""

EMAIL_PR_HTML_CONSTANT = """\
                    <html>
                    <head><center><div class="header"><br><br>
                      <h1>New request received to approve pull request for ring <<<RING_NAME>>></h1>
                    </div><center>	  
                    <style>
                    table {
                      font-family: arial, sans-serif;
                      border-collapse: collapse;
                      width: 90%;
                    }
                    body {
                      font-family: Arial;
                      margin: 0;
                    }
                    td, th {
                      border: 1px solid #dddddd;
                      text-align: left;
                      padding: 20px;
                    }

                    tr:nth-child(even) {
                      background-color: #dddddd;
                    }
                    .header {
                        font-family: arial, sans-serif;
                      text-align: center;
                      font-size: 15px;
                    }
                    .para {
                      font-family: arial, sans-serif;
                      text-align: center;
                      font-size: 14px;
                    }
                    .text {
                      display: block;
                      width: 100px;
                      overflow: hidden;
                      white-space: nowrap;
                      text-overflow: ellipsis;
                    }
                    </style>
                    </head>
                    <body>
                    <center>
                    <div class="para">
                    <label>Ring Name - <<<RING_NAME>>>.commvault.com</label><br>
                    <label>Commcell Name - <<<COMMCELL_NAME>>></label>
                    <br/>
                    <label>Please approve/deny pull request created for Ring - <<<RING_NAME>>></label>
                    </div>
                    <br>
                    </center>
                    </body>
                    </html>
        """
EMAIL_WELCOME_TRACK_CONSTANT = """<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SaaS Ring Provisioning Status</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            font-size: 13px;
        }
        .container {
            padding: 20px;
            text-align: left;
        }
        .content {
            padding: 20px;
        }
        .header {
            font-size: 20px;
            padding: 15px;
            background-color: #854896;
            border-bottom: 1px solid #ddd;
            color: white;
        }
    </style>
</head>
<body>
        <div class="header">
            <h3>SaaS Ring Provisioning for your Ring [<<<RING_NAME>>>] with Commcell [<<<COMMCELL_NAME>>>] has started</h3>
        </div>
        <div class="container">
            <p class="info-label"><b>Ring URL</b> - <<<RING_NAME>>>.testlab.commvault.com</p>
            <p class="info-label"><b>CommCell Name</b> - <<<COMMCELL_NAME>>></p>
            <p class="info-label">Track the status of your Ring [<<<RING_NAME>>>] from here: <a href="<<<STATUS_URL>>>">SaaS Ring Status</a></p>
        </div>
</body>
</html>
"""

EMAIL_INIT_FAILURE_CONSTANT = """<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SaaS Ring Provisioning Status</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            font-size: 13px;
        }
        .container {
            padding: 20px;
            text-align: left;
        }
        .content {
            padding: 20px;
        }
        .header {
            font-size: 20px;
            padding: 15px;
            background-color: #854896;
            border-bottom: 1px solid #ddd;
            color: white;
        }
    </style>
</head>
<body>
        <div class="header">
            <h3>SaaS Ring Provisioning for your Ring [<<<RING_NAME>>>] has failed to start</h3>
        </div>
        <div class="container">
            <p class="info-label"><b>Ring URL</b> - <<<RING_NAME>>>.testlab.commvault.com</p>
			<p>Failure Reason: <<<EXCEPTION>>></p>
            <p class="info-label">Please check if all the required services in your CommServe, 
            Command Center and Web Server are up and re-run the SaaS Ring Provisioning job.</p>
        </div>
</body>
</html>
"""

EMAIL_NEXT_STEPS_CONSTANT = """<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            font-size: 13px;
        }
        .header {
            font-size: 20px;
            padding: 15px;
            background-color: #854896;
            border-bottom: 1px solid #ddd;
            color: white;
        }
        .content {
            padding: 20px;
        }
        table {
            font-family: Arial, sans-serif;
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            border: 1px solid #dddddd;
            text-align: left;
            padding: 15px;
            font-size: 13px;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        ul {
            padding-left: 20px;
        }
        li {
            padding: 5px 0;
            line-height: 1.5;
        }
		.para1 {
            padding: 15px 0;
            line-height: 1.8;
		}
    </style>
</head>
<body>
    <div class="header">
        <h3>SaaS Ring Provisioning for [<<<RING_NAME>>>] with CommCell [<<<COMMCELL_NAME>>>] Completed Successfully</h3>
    </div>
    <div class="content">
        <p class="para1">
            <strong>Ring URL:</strong> <<<RING_NAME>>>.testlab.commvault.com<br>
            <strong>CommCell Name:</strong> <<<COMMCELL_NAME>>>
        </p>
        <table class="striped">
            <thead>
                <tr>
                    <th>Details</th>
                    <th>Information</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Base URL</td>
                    <td><a href="https://<<<RING_NAME>>>.testlab.commvault.com">https://<<<RING_NAME>>>.testlab.commvault.com</a></td>
                </tr>
                <tr>
                    <td>Ring Owner</td>
                    <td><<<OWNER>>></td>
                </tr>
                <tr>
                    <td>Test Tenant</td>
                    <td><<<COMPANY_NAME>>></td>
                </tr>
                <tr>
                    <td>Credentials</td>
                    <td><<<COMPANY_NAME>>>\<<<USERNAME>>>, password is the same as the MSP admin password</td>
                </tr>
            </tbody>
        </table>
        <p class="para1">
			For the next steps, please refer to the 
			<a href="https://platformdocs.commvault.com/docs/backend/saas-ring-provisioning/saas-ring-ci#additional-resources" target="_blank" rel="noopener noreferrer">
				Additional Resources Section.</a> 
		</p>        
    </div>
</body>
</html>
"""

WF_START_TAG = "<Workflow_StartWorkflow><workflow workflowName='%s'/></Workflow_StartWorkflow>"
WF_TRIALS_V2_POPUP_INPUT_XML = '<Workflow_PopupInputRequest ' \
                               'sessionId="%s" jobId="%s" processStepId="%s" ' \
                               'okClicked="1" action="OK" ' \
                               'inputXml="&lt;inputs>' \
                               '&lt;firstName class=&quot;java.lang.String&quot;>' \
                               '%s&lt;/firstName>' \
                               '&lt;lastName class=&quot;java.lang.String&quot;>%s' \
                               '&lt;/lastName>' \
                               '&lt;companyName class=&quot;java.lang.String&quot;>' \
                               '%s&lt;/companyName>' \
                               '&lt;email class=&quot;java.lang.String&quot;>%s' \
                               '&lt;/email>' \
                               '&lt;country class=&quot;java.lang.String&quot;>United States&lt;/country>&lt;' \
                               'commcell class=&quot;java.lang.String&quot;>' \
                               '%s&lt;/commcell>' \
                               '&lt;phone class=&quot;java.lang.String&quot;>%s' \
                               '&lt;/phone>&lt;/inputs>">' \
                               '<client clientId="%s" clientName="%s" ' \
                               'hostName="%s"/>' \
                               '<commCell commCellId="%s" commCellName="%s"/>' \
                               '</Workflow_PopupInputRequest>'
WF_TRIALS_V2_INFO_INPUT_XML = '<Workflow_InformationalMessageRequest ' \
                              'sessionId="%s" ' \
                              'jobId="%s" ' \
                              'processStepId="%s" okClicked="1" action="OK">' \
                              '<client clientId="%s" clientName="%s" ' \
                              'hostName="%s" />' \
                              '<commCell commCellId="%s" commCellName="%s" csGUID=""/>' \
                              '</Workflow_InformationalMessageRequest> '

TRIAL = "trial"


class RegionId(enum.Enum):
    EASTUS2_ID = 8


class ProductType(enum.Enum):
    O365 = 25
