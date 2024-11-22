# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for all the constants of Hub Automation
"""

from enum import Enum


class HubServices(Enum):
    database = 'Database'
    endpoint = 'Endpoint'
    file_system = 'File Server'
    office365 = 'Office 365'
    salesforce = 'Salesforce'
    vm_kubernetes = 'Virtual Machines'
    kubernetes = 'Kubernetes'
    file_migration = "File Migration"
    Dynamics365 = 'Microsoft Dynamics 365'
    ad = "Azure AD and Microsoft AD"
    file_archiving = "File & Object Archive"
    cloud_command = "Cloud Command"
    object_storage = "Object Storage"
    risk_analysis = "Risk Analysis"
    auto_recovery = "Auto Recovery"
    google_workspace = "Google Workspace"


class ServiceAction(Enum):
    CONFIGURE = 'Configure'
    MANAGE = 'Manage'
    LEARN_MORE = 'Learn More'


class O365AppTypes(Enum):
    exchange = 'Exchange'
    sharepoint = 'SharePoint'
    onedrive = 'OneDrive'
    teams = 'Teams'


class FileObjectTypes(Enum):
    file_server = 'File Server'
    object_storage = 'Object Storage'


class DatabaseTypes(Enum):
    sql = 'SQL server'
    oracle = 'Oracle'
    sap_hana = 'SAP HANA'
    azure = 'Microsoft Azure'
    ORACLE_RAC = 'Oracle RAC'
    AWS = 'Amazon Web Services'


class VMKubernetesTypes(str, Enum):
    azure_vm = 'Azure VM'
    hyper_v = 'Hyper-V'
    kubernetes = 'Kubernetes'
    vmware = 'VMware'
    amazon = 'Amazon EC2'
    oci = 'OCI VM'
    nutanix = "Nutanix AHV"


class CCVMKubernetesTypes(str, Enum):
    azure_vm = 'Microsoft Azure'
    hyper_v = 'Microsoft Hyper-V'
    amazon = 'Amazon Web Services'
    vmware = 'VMware vCenter'
    oci = 'Oracle Cloud Infrastructure'
    nutanix = "Nutanix AHV"


class ADTypes(Enum):
    ad = "Microsoft AD"
    aad = "Azure AD"


class KubernetesDeploymentTypes(Enum):
    EKS = "EKS"
    AKS = "AKS"
    ONPREM = "ONPREM"


# Risk Analysis Command Center Constants and Enums
NO_SUBSCRIPTION = "Risk Analysis: Subscription not found"
SUBSCRIPTION_AND_NO_BACKUP = "Backup Required"
SUBSCRIPTION_AND_BACKUP = "Select a Risk Analysis Application"
SDG_URL = "commandcenter/#/sdg"


class RiskAnalysisType(Enum):
    EXCHANGE = "Exchange"
    ONEDRIVE = "OneDrive"


class RiskAnalysisConfigTitle(Enum):
    EXCHANGE = "Add Mailbox"
    ONEDRIVE = "Add OneDrive"


class RiskAnalysisSubType(Enum):
    NO_SUBSCRIPTION = 1
    SUBSCRIPTION_AND_NO_BACKUP = 2
    SUBSCRIPTION_AND_BACKUP = 3


class AutoRecoveryTypes(Enum):
    auto_recovery = "Auto Recovery"


class GoogleWorkspaceAppTypes(Enum):
    gdrive = "Google Drive"
    gmail = "Gmail"
