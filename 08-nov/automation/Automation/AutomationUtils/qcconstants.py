# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for maintaining QC related Constants.

All QC constants like the Product / OS / Feature, are added as Enum(s) to this file.


Classes(Enum):

    Products    --      Enum(s) for all the Products/Agents maintained in the Commvault QC Database

    OS          --      Enum(s) for Operating Systems maintained in the Commvault QC Database

    Features    --      Enum(s) for Features maintained in the Commvault QC Database

"""

from enum import Enum


class OS(Enum):
    """For Internal Use Only.

        Constants for all the Operating Systems currently supported by Commvault Systems.

        Any test case is written for one of the following Operating Systems, and must be specified
        in the test case source file.

        This is picked from Commvault Quality Center Database.

    """
    AIX = 'AIX'
    ANDROID = 'ANDROID'
    BLACKBERRY = 'BLACKBERRY'
    BOS = 'BOS'
    DART = 'DART'
    ENAS = 'ENAS'
    HP = 'HP'
    iOS = 'iOS'
    LINUX = 'LINUX'
    MAC = 'MAC'
    NETAPP = 'NETAPP'
    NETWARE = 'NETWARE'
    NA = 'NA'   # The default OS if there is none specified.
    SOL = 'SOL'
    UNIX = 'UNIX'
    WINDOWS = 'WINDOWS'


class Features(Enum):
    """For Internal Use Only.

        Constants for all the Features currently supported by Commvault Systems.

        Any test case is written for a specific feature, and must be specified in the test case
        source file.

        This is picked from Commvault Quality Center Database.

    """
    ACTIVITYCONTROL = "Activity Control"
    ADDINS = "Add-Ins"
    ADDITIONALSETTINGS = "Additional Settings"
    ADMINCONSOLE = "Admin Console"
    ALERT = "Alert"
    ANALYTICS = "Analytics"
    APPAWAREBACKUP = "AppAware Backup"
    AUDITTRAIL = "Audit Trail"
    AUTOMATION = "Automation"
    AUXILIARYCOPY = "Auxiliary Copy"
    BACKWARDCOMPATIBILITY = "Backward Compatibility"
    BLOCKLEVELBACKUP = "Block Level Backup"
    BLOCKREPLICATION = "Block Replication"
    BMR = "BMR"
    BRANDING = "Branding"
    CASEMANAGER = "Case Manager"
    CLIENTCONFIGURATION = "Client Configuration"
    CLIENTGROUP = "Client Group"
    CLUSTER = "Cluster"
    COMMANDLINE = "Command Line"
    COMMCELLMIGRATION = "Commcell Migration"
    CONTENTINDEXING = "Content Indexing"
    CORPORATEEVENTMANAGEMENT = "Corporate Event Management"
    DATAAGING = "Data Aging"
    DATALOSSPREVENTION = "Data Loss Prevention"
    DATAPROTECTION = "Data Protection"
    DATARECOVERY = "Data Recovery"
    DATATRANSPORT = "Data Transport"
    DATAVERIFICATION = "Data Verification"
    DATABASELAYER = "Database Layer"
    DEDUPLICATION = "Deduplication"
    DISASTERRECOVERY = "Disaster Recovery"
    DRIVERS = "Drivers"
    ENCRYPTION = "Encryption"
    EVENTS = "Events"
    EXPLORERPLUGIN = "Explorer Plugin"
    EXTERNALDATACONNECTOR = "External Data Connector"
    GDPR = "GDPR"
    HARDWAREREFRESH = "Hardware Refresh"
    IDENTITYMANAGEMENT = "Identity Management"
    INDEXING = "Indexing"
    INFRASTRUCTURETOOLS = "Infrastructure Tools"
    INSTALL = "Install"
    JAVACONSOLE = "Java Console"
    JOBMANAGEMENT = "Job Management"
    LICENSING = "Licensing"
    LIVEBROWSE = "Live Browse"
    LIVEMOUNT = "Live Mount"
    LIVESYNC = "Live Sync"
    LOCALIZATION = "Localization"
    LOGFILE = "Log File"
    MEDIAMANAGEMENT = "MediaManagement"
    MOBILECONSOLE = "Mobile Console"
    NAMECHANGE = "Name Change"
    NETWORK = "Network"
    NOTAPPLICABLE = "Not Applicable"
    OBJECTSTORENFS = "Object Store - NFS"
    PERFORMANCE = "Performance"
    PLANS = "Plans"
    REPORTS = "Reports"
    RESOURCEMANAGEMENT = "ResourceManagement"
    RESTAPI = "REST API"
    SCALABILITY = "Scalability"
    SCHEDULEANDSCHEDULEPOLICY = "Schedule and Schedule Policy"
    SEARCH = "Search"
    SECURITYANDROLES = "Security and Roles"
    SERVICES = "Services"
    SNAPBACKUP = "Snap Backup"
    STORAGEPOLICY = "Storage Policy"
    STORAGEPOOLS = "Storage Pools"
    SUBCLIENTPOLICY = "Subclient Policy"
    SYNTHETICFULL = "Synthetic Full"
    UPDATES = "Updates"
    UPGRADE = "Upgrade"
    VMPROVISIONING = "VM Provisioning"
    WEBCONSOLE = "Web Console"
    WORKFLOW = "Workflow"
    USERDEFINED = "UserDefined"
    DRORCHESTRATION = "DR Orchestration"
    CVFAILOVER = "Cv Failover"


class Products(Enum):
    """For Internal Use Only.

        Constants for all the Products / Agents currently supported by Commvault Systems.

        Any test case is written for a specific product / agent, and must be specified in the
        test case source file.

        This is picked from Commvault Quality Center Database.

    """
    ACTIVEDIRECTORY = "Active Directory"
    CASSANDRA = "Cassandra"
    CLINICALARCHIVING = "Clinical Archiving"
    CLOUDCONNECTOR = "Cloud Connector"
    COMMSERVER = "Commserver"
    COMMVAULTAPPLIANCE = "Commvault Appliance"
    CONTENTANALYZER = "ContentAnalyzer"
    CONTENTINDEXING = "Content Indexing"
    CONTENTSTOREMAILSERVER = "ContentStore Mail Server"
    CONTINUOUSDATAREPLICATOR = "Continuous Data Replicator"
    CTE = "CTE"
    CVLEGAL = "CVLegal"
    DATACUBE = "Data Cube"
    DB2 = "DB2"
    DB2DPF = "DB2-DPF"
    DOCUMENTUM = "Documentum"
    DOWNLOADCENTER = "Download Center"
    EDGEDRIVE = "Edge Drive"
    ENGINEERINGINFRASTRUCTURE = "ENGINEERING INFRASTRUCTURE"
    EXCHANGECOMPLIANCEARCHIVER = "Exchange Compliance Archiver"
    EXCHANGEDB = "Exchange DB"
    EXCHANGEMB = "Exchange MB"
    EXCHANGEMBARCHIVER = "Exchange MB Archiver"
    EXCHANGEPF = "Exchange PF"
    EXCHANGEPFARCHIVER = "Exchange PF Archiver"
    FILEMONITORING = "File Monitoring"
    FILESYSTEM = "FileSystem"
    FILESYSTEMARCHIVER = "Filesystem Archiver"
    FILESYSTEMIMAGELEVEL = "Filesystem Image Level"
    GREENPLUM = "Greenplum"
    GROUPWISE = "Groupwise"
    HADOOP = "Hadoop"
    IBMISERIES = "IBM iSeries"
    INFORMIX = "Informix"
    LAPTOP = "Laptop"
    LOGMONITORING = "Log Monitoring"
    LOTUSNOTESARCHIVER = "Lotus Notes Archiver"
    LOTUSNOTESDB = "Lotus Notes DB"
    LOTUSNOTESDOC = "Lotus Notes Doc"
    MEDIAAGENT = "Media Agent"
    METRICSREPORTS = "METRICS REPORTS"
    MOBILEAPP = "MOBILE APP"
    MSSQL = "MS SQL"
    MYSQL = "MySQL"
    NDMP = "NDMP"
    NDS = "NDS"
    NONE = "None"  # This is the default product if none is specified
    OBJECTSTORE = "Object Store"
    OPENVMS = "OpenVMS"
    ORACLE = "Oracle"
    ORACLERAC = "Oracle RAC"
    POSTGRESQL = "PostgreSql"
    RECORDSMANAGER = "Records Manager"
    SALESFORCE = "Salesforce"
    SAPHANA = "SAP HANA"
    SAPMAXDB = "SAP MAXDB"
    SAPORACLE = "SAP ORACLE"
    SEARCHENGINE = "Search Engine"
    SHAREPOINT = "Sharepoint"
    SOFTWARESTORE = "Software Store"
    SYBASE = "Sybase"
    SYSTEMMONITORING = "System Monitoring"
    TSC = "TSC"
    TSCDRIVE = "TSC-DRIVE"
    TSCHBA = "TSC-HBA"
    TSCLIBRARY = "TSC-LIBRARY"
    TSCROUTER = "TSC-ROUTER"
    TSCVTL = "TSC-VTL"
    VIRTUALIZATIONALICLOUD  = "Virtualization AliCloud"
    VIRTUALIZATIONAMAZON = "Virtualization Amazon"
    VIRTUALIZATIONAZURE = "Virtualization Azure"
    VIRTUALIZATIONFUSIONCOMPUTE = "Virtualization FusionCompute"
    VIRTUALIZATIONHYPERV = "Virtualization HyperV"
    VIRTUALIZATIONNUTANIX = "Virtualization Nutanix"
    VIRTUALIZATIONOPENSTACK = "Virtualization OpenStack"
    VIRTUALIZATIONORACLECLOUD = "Virtualization Oracle Cloud"
    VIRTUALIZATIONORACLEVM = "Virtualization OracleVM"
    VIRTUALIZATIONRHEV = "Virtualization RHEV"
    VIRTUALIZATIONVMWARE = "Virtualization VMWare"
    VIRTUALIZATIONXEN = "Virtualization Xen"
    VIRTUALIZATIONOCI = "Virtualization Oracle Cloud Infrastructure"
    VMPROVISIONING = "VM Provisioning"
    WORKFLOW = "Workflow"
    USERDEFINED = "UserDefined"
    DRORCHESTRATION = "DROrchestration"
    VIRTUALIZATIONVCLOUD = "Virtualization VCloud"
    VIRTUALIZATIONGCCLOUD = "Virtualization Google cloud"
