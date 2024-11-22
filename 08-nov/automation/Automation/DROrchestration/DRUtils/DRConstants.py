# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module contains constant values and enums for Disaster Recovery (DR)
"""

from enum import Enum
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type


class Vendors(Enum):
    """ENUM Class for Vendor names"""
    VMWARE = hypervisor_type.VIRTUAL_CENTER.value
    AZURE = hypervisor_type.AZURE.value
    HYPERV = hypervisor_type.MS_VIRTUAL_SERVER.value
    AWS = hypervisor_type.AMAZON_AWS.value


class Vendors_Complete(Enum):
    """ENUM Class for Vendor names"""
    VMWARE = 'VMware vCenter'
    AZURE = 'Microsoft Azure'
    HYPERV = 'Microsoft Hyper-V'
    AWS = 'Amazon Web Services'

class Vendor_Instancename_Mapping(Enum):
    """ENUM Class for Vendor names"""
    VMWARE = 'vmware'
    AZURE = 'azure resource manager'
    HYPERV = 'hyper-v'
    AWS = 'amazon web services'

class Vendor_PolicyType_Mapping(Enum):
    """ENUM Class for Vendor names"""
    VMWARE = 13
    AZURE = 7
    HYPERV = 2
    AWS = 1

class _AWS_TransportModes(Enum):
    """
    Enum class representing the transport modes for AWS
    """

    DirectWrite = 'Amazon EBS direct'
    HotAdd = 'Commvault HotAdd'
    Import = 'Import'
    Automatic = 'Automatic (default)'


class _Azure_TransportModes(Enum):
    """
    Enum class representing the transport modes for Azure
    """

    Automatic = 'Automatic (default)'


class _HyperV_TransportModes(Enum):
    """
    Enum class representing the transport modes for HyperV
    """

    Automatic = 'Automatic (default)'


class _VMWare_TransportModes(Enum):
    """
    Enum class representing the transport modes for VMWare
    """

    Automatic = 'Automatic (default)'
    HotAdd = 'Commvault HotAdd'
    SAN = 'SAN'
    NAS = 'NAS'
    NBD_SSL = 'NBD SSL'
    NBD = 'NBD'


class VendorTransportModes:
    AWS = _AWS_TransportModes
    AZURE = _Azure_TransportModes
    HYPERV = _HyperV_TransportModes
    VMWARE = _VMWare_TransportModes


class ReplicationType(Enum):
    """Enum Class for replication type to ID mapping"""
    Periodic = 'PERIODIC'
    Orchestrated = 'BACKUP'
    Continuous = 'CONTINUOUS'


class SiteOption(Enum):
    """ENUM Class for Site Option to ID mapping"""

    HotSite = "HOT"
    WarmSite = "WARM"


class TimePeriod(Enum):
    """Enum Class for replication operation level"""
    MINUTES = "Minute(s)"
    HOURS = "Hour(s)"
    DAYS = "day(s)"
    WEEKS = "Week(s)"
    MONTHS = "Month(s)"
    YEARS = "Year(s)"
    INFINITE = "Infinite"

class _AWS_ViewModes(Enum):
    """
    Enum class representing the view modes for AWS
    """

    Instance = 'Instance View'
    Region = 'Region View'
    Tags = 'Tags View'
    InstanceType = 'InstanceType View'


class _Azure_ViewModes(Enum):
    """
    Enum class representing the view modes for Azure
    """

    VMs = 'VMs'
    ResourceGroups = 'Resource Groups'
    Regions = 'Regions'
    StorageAccounts = 'Storage Accounts'
    Tags = 'Tags'


class _HyperV_ViewModes(Enum):
    """
    Enum class representing the view modes for HyperV
    """

    VMs = 'VMs'
    Hosts = 'Hosts'
    Storage = 'Storage'


class _VMWare_ViewModes(Enum):
    """
    Enum class representing the view modes for VMWare
    """

    Hosts = 'Hosts'
    VMs = 'VMs and templates'
    Datastores = 'Datastores'
    Tags = 'Tags'


class VendorViewModes:
    AWS = _AWS_ViewModes
    AZURE = _Azure_ViewModes
    HYPERV = _HyperV_ViewModes
    VMWARE = _VMWare_ViewModes


class Application_Type(Enum):
    """Enum Class for Application Type"""
    REPLICATION = "Replication"
    REGULAR = "Regular"
