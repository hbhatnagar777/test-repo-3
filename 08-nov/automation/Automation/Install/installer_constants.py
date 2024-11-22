# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for maintaining deployment related Constants."""


import os
from enum import Enum
from AutomationUtils import constants
from AutomationUtils import config

COMMVAULT_REGISTRY_ROOT_WINDOWS = r'HKLM:\SOFTWARE\CommVault Systems\Galaxy'

COMMVAULT_REGISTRY_ROOT_32BIT_WINDOWS = r'HKLM:\SOFTWARE\Wow6432Node\CommVault Systems\Galaxy'

COMMVAULT_REGISTRY_GALAXY_INSTALLER_FLAGS = r"HKLM:\SOFTWARE\GalaxyInstallerFlags"

COMMVAULT_REGISTRY_ROOT_UNIX = r'/etc/CommVaultRegistry/Galaxy'

DEFAULT_DRIVE_LETTER = "C:"

ROOT_FILES_PATCHING_ID = 11000

UNIX_DEFAULT_DRIVE_LETTER = "/"

REMOTE_FILE_COPY_FOLDER = "AUTOMATION_LOC"

REMOTE_FILE_COPY_LOC = DEFAULT_DRIVE_LETTER + "\\AUTOMATION_LOC"

UNIX_REMOTE_FILE_COPY_LOC = UNIX_DEFAULT_DRIVE_LETTER + "AUTOMATION_LOC"

UNIX_DEFAULT_MOUNT_PATH = "/cvbuild"

MSSQL_REG_PATH = r"SOFTWARE\\Microsoft\\Microsoft SQL Server\\"

INTERACTIVE_INSTALL_EXE_PATH = os.path.join(constants.AUTOMATION_DIRECTORY, 'CompiledBins', 'interactiveinstall.exe')
"""str:        path where the interactiveinstall.exe binary is placed."""

REGISTER_ME_XML_OP = os.path.join(REMOTE_FILE_COPY_LOC, "registerme_output.xml")

FOREVERCELL_WORKFLOW_NAME = "Custom Install Package Creation"

FOREVERCELL_HOSTNAME = "cloud.commvault.com"

INSTALL_PLATFORMS = ['Windows', 'Mac']
''' Installation platforms supported for laptop testcases '''

PACKAGE_EXE_MAP = {
    "macOS_arm64": "macOSEndpoint_arm64.pkg",
    "Mac": "macOSEndpoint.pkg",
    "Windows": "WindowsEndpoint64.exe",
}

PACKAGES_TO_DOWNLOAD = {
    "File System Core Packages": {
        "macOS": "macOSEndpoint.pkg",
        "macOS_arm64": "macOSEndpoint_arm64.pkg",
        "Windows-x64": "WindowsEndpoint64.exe",
        "Windows-x86": "WindowsEndpoint32.exe"
    }
}
# Commenting out temporarily unless some real case comes in future to install proxy packages.
#     "Proxy Packages":{
#         "Windows-x64": "WinX64_Proxy.exe",
#         "Windows-x86": "Win32_Proxy.exe"
#     }

CURRENT_RELEASE_VERSION = "11.0.0"

CURRENT_BUILD_VERSION = "BUILD80"

DOWNLOAD_CENTER_CATEGORY = "Custom Package"

DOWNLOAD_CENTER_SUB_CATEGORY = "Packages"

PROXY_GROUP_NAME = 'Infrastructure - MSP Proxies (DMZ)'

PROXY_DEFAULT_PORT = '443'

EXCLUDE_FOLDERS = [
    "CVS",
    "ThirdParty",
    "LooseUpdates",
    "1",
    "14",
    "16",
    "101",
    "105",
    "106",
    "107",
    "108",
    "110",
    "111",
    "112",
    "113",
    "114",
    "115",
    "LaptopVPNPackages",
    "LaptopPackages",
    "RootFiles",
    "OEM",
    "OneTouch"]

LOOSEUPDATES_FOLDER = "LooseUpdates"
BINARY_PAYLOAD = "BinaryPayload"
BINARY_PAYLOAD_32 = "BinaryPayload32"
UNIX = "UNIX"
WINDOWS = "Windows"
UNIX_PATH = f"Unix/linux-x8664/"
UPDATES = "Updates"

REG_INTEGRATION_VALUE = r'IntegrationMode'
REG_INTEGRATION_VALUE_BATCH =  r'BatchUpdateMode'
REG_INTEGRATION_VALUE_LOOSE  = r'LooseUpdateMode'
REG_INTEGRATION_BATCH_MEDIA = r'BatchMedia'
REG_FRESH_INSTALL_REQUESTID = r'FRequestID'

BATCHBUILD_CURRENTBATCHSTAGE = r'CurrentBatchStage'
BATCHBUILD_PRECERT_BATCH = r'PrecertifyingBatch'
BATCHBUILD_PRECERT_LOOSE = r'PrecertLoose'
BATCHBUILD_PRECERT_SUCCESS = r'PrecertBatchSuccess'
BATCHBUILD_PRECERT_MEDIA_SUCCESS = r'PrecertMediaSuccess'
BATCHBUILD_PRECERT_FAILED = r'PrecertifyingUpdates'
BATCHBUILD_PRECERT_BATCH_MEDIA = r'PrecertifyingMedia'
BATCHBUILD_PRECERT_COMPLETE = r'BatchComplete'
REG_INTEGRATION_VALUE_BATCH_MEDIA   =   '1'

AUTOMATION = "Automation"
PRIMARY = "Primary"


THIRDPARTY_FOLDER = "ThirdParty"

SIM_CALL_WRAPPER_EXE = "SIMCallWrapper.exe"
SIM_CALL_WRAPPER_EXE_UNIX = "SIMCallWrapper"

QINSTALLER_RETURNCODES = {
    0: "SUCCESS",
    1: "FAILED",
    2: "CANCELED",
    3: "REBOOT_NEEDED",
    4: "LOGOFF_NEEDED",
    5: "REBOOT_AND_RESUME_NEEDED",
    6: "CLIENTNAME_CONFLICT",
    7: "NO_SRM_SERVER",
    8: "NO_LICENSE",
    9: "CS_HOST_NOT_RESOLVABLE",
    10: "INSTALL_FOLDER_NOT_EMPTY",
    11: "CLIENTNAME_IN_USE",
    12: "HOSTNAME_IN_USE",
    13: "UNFINISHED_INTERACTIVE_INSTALL_DETECTED",
    14: "PLATFORMS_NOT_ALLOWED",
    15: "UNFINISHED_INSTALL_DETECTED",
    16: "PORTS_IN_USE",
    17: "ALL_PLATFORMS_ALREADY_INSTALLED",
    18: "LOW_DISK_SPACE",
    19: "CLIENT_AUTHENTICATION_FAILED",
    20: "CLUSTER_VM_DETECTED",
    21: "FAILED_STOP_ORACLE_SERVICES",
    22: "ORACLE_SERVICES_RUNNING",
    23: "NO INSATTLED INSTANCE DETECTED",
    24: "SIM Operation Failed",
    25: "JOB IN PROGRESS",
    26: "PACKAGE_UPGRADE_NOT_ALLOWED",
    27: "REQUIRED_SERVICE_PACK_MISSING",
    28: "FAILED_TO_CREATE_APPLICATION",
    29: "FAILED_ENABLE_AUTHENTICATION_ALIAS",
    31: "MULTI_INSTANCE_NOT_ALLOWED",
    32: "LOW_MEMORY",
    33: "FailedStopDB2Services",
    34: "FailedStartOracleServices",
    35: "FailedStartDB2Services",
    36: "SearchIndexLocationPathNotValid",
    37: "InvalidSearchEnginePort",
    38: "SelectedPackagesAlreadyInstalled",
    39: "MissingPayload",
    40: "WrongCommandLine",
    41: "ExplorerPluginBinariesLocked",
    42: "FailedInstallThirdParty",
    43: "FailedInstallPackage",
    44: "FailedToStartServices",
    45: "FailedToExtractSEEFiles",
    46: "FailedToStopProcesses",
    47: "ConflictDiagUpdatesInCache",
    100: "AnotherInstanceRunning",
    125: "DBUpdateInstallFailed",
    126: "AlreadyUptoDate",
    127: "V8FWConfigDetected"
}

WINDOWS_SERVICES = {
    1: ['GxFWD', 'GxCVD'],
    20: ['GxEvMgrS', 'GxApM', 'GxQSDK', 'GxJobMgr', 'GXMLM'],
    23: ['CVJavaWorkflow'],
    25: ['GxApM'],
    51: ['GXMMM'],
    203: ['GxClMgrS'],
    252: ['GxClMgrS'],
    451: ['CvRepSvc'],
    552: ['GxFWD', 'GxClMgrS'],
    702: ['GxClMgrS'],
    713: ['GxBlr'],
    753: ['GxClMgrS'],
    755: ['GxBlr'],
    952: ['GxMONGO']
}

UNIX_SERVICES = {
    1002: ['cvd'],
    1101: ['ClMgrS', 'cvlaunchd'],
    1301: ['CvMountd']
}

DOWNLOAD_SOFTWARE_DEFAULT_MEDIA = "CVMedia"
CURRENT_RELEASE_ID = 16

EXTRACT_BAT_FILE = "ExtractBootstrapper.bat"

DB2LOGLOCATION = r"C:\DB2logs"

BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH = "BootStrapperExtractedPath"

UNIX_BOOTSTRAPPER_DOWNLOAD_LOC = "DownloadPackageLocation/"

UNIX_BOOTSTRAPPER_DOWNLOADPATH = "DownloadPackageLocationUnix\\Commvault"
WINDOWS_BOOTSTRAPPER_DOWNLOADPATH = "DownloadPackageLocationWindows\\Commvault"
UNIX_BOOTSTRAPPER_DOWNLOAD_OSID = [39, 28, 30, 14, 26, 29, 17, 18, 10, 11, 41]

WINDOWS_BOOTSTRAPPER_DOWNLOAD_OSID = [1, 3]

REMOTEFILECOPYLOC = "AUTOMATION_LOC\\"

BRANDING_DICT = {
    1: "Commvault",
    16: "Commvault Express",
    106: "Virtual Server",
    119: "Metallic"
}

WINDOWS_DEFAULT_INSTALLER_EXECUTABLE = "Setup.exe"

DOWNLOAD_SOFTWARE_DEFAULT_CVAPPLIANCE_MEDIA = "CVAppliance"


def oemid_edition_name(oem_id):
    """
    returns Edition name for given OEMID
    """
    return BRANDING_DICT[int(oem_id)]


OSNAME_LIST = {
    0: ("windows", "ThirdPartyPackage", "ThirdPartyPackage"),
    1: ("windows32", "Windows", "Win32"),
    3: ("windowsX64", "WinX64", "WinX64"),
    14: ("aixos", "aix-ppc", "aix-ppc"),
    15: ("linuxos", "linux-x86", "linux-x86"),
    16: ("linuxosX64", "linux-x8664", "linux-x8664"),
    17: ("linuxosPPC64", "linux-ppc64", "linux-ppc64"),
    18: ("linuxosS390", "linux-s390", "linux-s390"),
    29: ("linuxs390os", "linux-s390-31", "linux-s390-31"),
    20: ("hpos", "hp-ia64", "hp-ia64"),
    30: ("solsparcos", "sol-sparc-x86", "sol-sparc-x86"),
    23: ("solarisosX64", "sol-x8664", "sol-x8664"),
    24: ("darwinos", "dwn-x86", "dwn-x86"),
    27: ("darwinosx8664", "dwn-x8664", "dwn-x8664"),
    25: ("freeBSDos", "fbsd-x86", "fbsd-x86"),
    26: ("freeBSDosX64", "fbsd-x8664", "fbsd-x8664"),
    31: ("solos", "sol-x86", "sol-x86"),
    28: ("aixppcos", "aix-ppc-32", "aix-ppc-32"),
    22: ("solarisos", "sol-sparc", "sol-sparc"),
    32: ("linuxosPPC64le", "linux-ppc64-le", "linux-ppc64-le"),
    33: ("aixos5232", "aix52-32", "aix52-32")
}

class BinarySetIDMapping(Enum):
    """
    Class for os name to id mapping
    """
    WINDOWS_32 = 1
    WINDOWS_64 = 3
    UNIX_AIX = 39
    UNIX_FREEBSD86 = 28
    UNIX_FREEBSD64 = 30
    UNIX_HP = 14
    UNIX_LINUX86 = 17
    UNIX_LINUX64 = 18
    UNIX_S390 = 29
    UNIX_PPC64 = 26
    UNIX_SOLARIS64 = 11
    UNIX_SOLARIS_SPARC = 10
    UNIX_LINUX64LE = 41
    UNIX_LINUXARM = 42
    UNIX_MAC64 = 40
    UNIX_MACARM = 43

UNIX_ROOT_LIST = ["\\Unix\\cvpkgadd", "\\Unix\\cvpkgseed", "\\Unix\\detect", "\\Unix\\pkg.xml",
                  "\\Unix\\pkg.xml.description", "\\Unix\\silent_install", "\\Unix\\support",
                  "\\Unix\\version", "\\Unix\\linux-x8664\\BinaryInfo.xml",
                  "\\Unix\\linux-x8664\\BinaryInfo.xml.description"]

WIN_ROOT_LIST = ["\\Windows\\BinaryInfo.xml", "\\Windows\\BinaryInfo.xml.description"]

IGNORE_LIST = ["CVUpdates", "CVPackages", "DVDInfo.txt", "SPInfo.txt", "HotfixConfiguration.xml",
               "CUConfiguration", "LooseUpdates", "CVAppliance", "MaintenanceReleasesInfo.xml", "UpdatesInfo.xml",
               "InstallConfigStaticInfo.xml"]

WIN32_IGNORE_LIST = ["BinaryPayload32", "WebDeploy_x86_en-US.msi", "VCRedist_2017_14\\x86", "VCRedist_2013\\x86",
                     "VCRedist_2010SP1\\x86"]

EXCLUDE_OEM = [
    "\\101\\",
    "\\105\\",
    "\\106\\",
    "\\107\\",
    "\\108\\",
    "\\110\\",
    "\\111\\",
    "\\112\\",
    "\\113\\",
    "\\114\\",
    "\\115\\",
    "\\14\\",
    "\\16\\",
    "\\116\\",
    "\\118\\",
    "\\119\\"]

DOWNLOAD_WIN_IGNORE_LIST = ["\\MSSQL\\", "\\OEM\\", "\\BinaryInfo.xml", "\\BinaryInfo.xml.description",
                            "CloudServices", "CVTools","InstallConfigStaticInfo.xml"]
DOWNLOAD_UNIX_SKIP_LIST = ['cvpkgadd', 'cvpkgseed', 'detect', 'silent_install', 'support', 'BinaryInfo.xml',
                           'BinaryInfo.xml.description', 'pkgsinmedia.txt']
DOWNLOAD_IGNORE_PACKAGE_LIST = ['732']

DO_NOT_DOWNLOAD_FROM_INSTALL_JOB = {
    "key": "UpdateFlags",
    "value": "bDoNotDownloadFromInstallJob",
    "data": "1",
    "reg_type": "DWord"
}

EXCLUDE_LIST = [
    "CVS",
    "ThirdParty",
    "LooseUpdates",
    "1",
    "14",
    "16",
    "101",
    "105",
    "106",
    "107",
    "108",
    "110",
    "111",
    "112",
    "113",
    "114",
    "115",
    "LaptopVPNPackages",
    "LaptopPackages",
    "RootFiles",
    "OEM",
    "OneTouch",
    "SetupBoot.exe",
    "Brandlist.txt"]


class DefaultVisibilityLevels(Enum):
    """
    list of Visibility values supported
    """
    MASS_DISTRIBUTION = 1
    PIONEER_RELEASE = 4
    LAB_USERS = 16
    FOREVERCELL = 64
    METALLIC_PRODUCTION = 256
    METALLIC_LAB = 512
    PROD_COMMSERVER = 1024
    PRECERT_TIP_BUILD = 4096
    PRECERT_METALLIC = 8192


class BaselineStatus(Enum):
    """"
    list of Baseline values
    """
    UNKNOWN = 0
    UP_TO_DATE = 1
    NEEDS_UPDATE = 2
    AHEAD_OF_CACHE = 4
    CV_BASELINE_TOCS_BELOW = 4096
    NA = 8
    HOTFIX = 16


CURRENT_RELEASE_VERSION = "11.0.0"

CURRENT_BUILD_VERSION = "BUILD80"

DOWNLOAD_SOFTWARE_DEFAULT_MEDIA = "CVMedia"

DEFAULT_COMMSERV_USER = "admin"

DEFAULT_HTTP_SITE = config.get_config().Install.download_server

DEFAULT_CONFIG_URL_PREFIX = f"https://{DEFAULT_HTTP_SITE}"

DEFAULT_FEATURE_RELEASE_XML = f"https://{DEFAULT_HTTP_SITE}/{DOWNLOAD_SOFTWARE_DEFAULT_MEDIA}/" \
                              f"FeatureReleaseList.xml"

DEFAULT_MAINTENANCE_RELEASE_XML = f"https://{DEFAULT_HTTP_SITE}/CVUpdates/{CURRENT_RELEASE_VERSION}/" \
                                  f"{CURRENT_BUILD_VERSION}" \
                                  "/{0}/MaintenanceReleasesInfo.xml"

DEFAULT_CU_CONFIGURATION_XML = f"https://{DEFAULT_HTTP_SITE}/CVUpdates/{CURRENT_RELEASE_VERSION}/" \
                               f"{CURRENT_BUILD_VERSION}" \
                               "/{0}/CUConfiguration.xml"

DEFAULT_INSTALL_DIRECTORY_WINDOWS = "C:\\Program Files\\Commvault\\ContentStore"

DEFAULT_LOG_DIRECTORY_WINDOWS = f"{DEFAULT_INSTALL_DIRECTORY_WINDOWS}\\Log Files"

DEFAULT_INSTALL_DIRECTORY_UNIX = "/opt/commvault"

DEFAULT_LOG_DIRECTORY_UNIX = "/var/log/commvault/Log_Files"

DEFAULT_CV_APPLIANCE_XML_WINDOWS = f"{DEFAULT_CONFIG_URL_PREFIX}/CVAppliance/CVApplianceConfig_Windows.xml"

ScreensSeenOnlyDuringCustomPackageCreation = [
    "InstallTypeView",
    "CustomPackageProcessorTypeView",
    "CustomPackageInstalltypeView",
    "PackageOptionView",
    "FeatureSelectionView",
    "CustomPackageOptionsView",
    "CustomPackageInstanceSelectionView"]

ScreenNameChangeDuringInstallDict = {
    "CustomPackageGalaxyHomePathView": "DestinationPathView",
    "CompletionExitView": "ConfigurationCompleteExitView"}

IgnoreList = [
    "TaskStatusView",
    "InstallProgressView",
    "InstanceSelectionView"]

WINDOWS_FIREWALL_INBOUND_EXCLUSION_LIST = ['CommVault_Process_1_cvd', 'CommVault_Process_1_cvfwd']

DEFAULT_PACKAGE_INSTALL_PATH_WINDOWS = f"https://{DEFAULT_HTTP_SITE}/CVMedia/{CURRENT_RELEASE_VERSION}/" \
                                  f"{CURRENT_BUILD_VERSION}" \
                                  "/{0}/Windows/WinPackages.xml"
DEFAULT_PACKAGE_INSTALL_PATH_UNIX = f"https://{DEFAULT_HTTP_SITE}/CVMedia/{CURRENT_RELEASE_VERSION}/" \
                                  f"{CURRENT_BUILD_VERSION}" \
                                  "/{0}/Unix/pkg.xml"

BINARYINFO_PATH_WINDOWS = f"https://{DEFAULT_HTTP_SITE}/CVMedia/{CURRENT_RELEASE_VERSION}/" \
                                  f"{CURRENT_BUILD_VERSION}" \
                                  "/{0}/Windows/BinaryInfo.xml"

BINARYINFO_PATH_UNIX = f"https://{DEFAULT_HTTP_SITE}/CVMedia/{CURRENT_RELEASE_VERSION}/" \
                                  f"{CURRENT_BUILD_VERSION}" \
                                  "/{0}/Unix/{1}/BinaryInfo.xml"

SYNC_UNIX_CU_SKIP_LIST = ['cvpkgadd', 'cvpkgseed', 'detect', 'silent_install', 'support']