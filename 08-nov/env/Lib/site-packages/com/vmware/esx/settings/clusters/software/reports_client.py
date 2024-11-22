# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.settings.clusters.software.reports.
#---------------------------------------------------------------------------

"""
The ``com.vmware.esx.settings.clusters.software.reports_client`` module
provides classes to manage reports pertaining to the desired state software for
a cluster of ESXi hosts.

"""

__author__ = 'VMware, Inc.'
__docformat__ = 'restructuredtext en'

import sys
from warnings import warn

from com.vmware.cis_client import Tasks
from vmware.vapi.stdlib.client.task import Task
from vmware.vapi.bindings import type
from vmware.vapi.bindings.converter import TypeConverter
from vmware.vapi.bindings.enum import Enum
from vmware.vapi.bindings.error import VapiError
from vmware.vapi.bindings.struct import VapiStruct
from vmware.vapi.bindings.stub import (
    ApiInterfaceStub, StubFactoryBase, VapiInterface)
from vmware.vapi.bindings.common import raise_core_exception
from vmware.vapi.data.validator import (UnionValidator, HasFieldsOfValidator)
from vmware.vapi.exception import CoreException
from vmware.vapi.lib.constants import TaskType
from vmware.vapi.lib.rest import OperationRestMetadata

class ComplianceStatusDetail(Enum):
    """
    The ``ComplianceStatusDetail`` class contains the essential status values
    for compliance with respect to target VMware Compatibility Guide (VCG).
    This enumeration was added in vSphere API 7.0.2.1.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    CERTIFIED = None
    """
    Hardware is specifically certified for target vSphere version according to
    the VCG/HCL. This class attribute was added in vSphere API 7.0.2.1.

    """
    NOT_CERTIFIED = None
    """
    Hardware is specifically not certified for target vSphere version according
    to the VCG/HCL. This class attribute was added in vSphere API 7.0.2.1.

    """
    HCL_DATA_UNAVAILABLE = None
    """
    HCL data can not be fetched to validate cluster hardware. This class
    attribute was added in vSphere API 7.0.2.1.

    """
    HOSTS_UNAVAILABLE = None
    """
    Hosts in cluster are not available to validate cluster hardware. This class
    attribute was added in vSphere API 7.0.2.1.

    """
    FIRMWARE_VERSION_UNKNOWN = None
    """
    No firmware version information is available (for example no Hardware
    Support Manager, HSM, configured in the cluster's Software Spec to get
    Firmware Details
    :class:`com.vmware.esx.settings_client.HardwareSupportPackageInfo` class or
    the system failed to retrieve the current firmware version of a device
    using the specified HSM. This class attribute was added in vSphere API
    7.0.2.1.

    """
    UNKNOWN = None
    """
    When given hardware may be certified for a release but its status can't be
    definitively determined due to ambiguity in server model, CPU series, or
    BIOS version. This class attribute was added in vSphere API 7.0.2.1.

    """
    VENDOR_UPDATE = None
    """
    When BIOS or firmware has been updated from a certified entry found in the
    VMware Compatibility Guide (VCG). This class attribute was added in vSphere
    API 7.0.2.1.

    """
    USER_VERIFIED = None
    """
    When a server or device's HCL compliance status has been overridden by the
    user to mark the system as compliant. This class attribute was added in
    vSphere API 7.0.2.1.

    """
    USER_FLAGGED = None
    """
    When a server or device's HCL compliance status has been overridden by the
    user to mark the system as non-compliant. This class attribute was added in
    vSphere API 7.0.2.1.

    """
    MUTED = None
    """
    When a user requests a non-compliance or HCL compliance unavailable warning
    to be suppressed. This class attribute was added in vSphere API 7.0.2.1.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`ComplianceStatusDetail` instance.
        """
        Enum.__init__(string)

ComplianceStatusDetail._set_values({
    'CERTIFIED': ComplianceStatusDetail('CERTIFIED'),
    'NOT_CERTIFIED': ComplianceStatusDetail('NOT_CERTIFIED'),
    'HCL_DATA_UNAVAILABLE': ComplianceStatusDetail('HCL_DATA_UNAVAILABLE'),
    'HOSTS_UNAVAILABLE': ComplianceStatusDetail('HOSTS_UNAVAILABLE'),
    'FIRMWARE_VERSION_UNKNOWN': ComplianceStatusDetail('FIRMWARE_VERSION_UNKNOWN'),
    'UNKNOWN': ComplianceStatusDetail('UNKNOWN'),
    'VENDOR_UPDATE': ComplianceStatusDetail('VENDOR_UPDATE'),
    'USER_VERIFIED': ComplianceStatusDetail('USER_VERIFIED'),
    'USER_FLAGGED': ComplianceStatusDetail('USER_FLAGGED'),
    'MUTED': ComplianceStatusDetail('MUTED'),
})
ComplianceStatusDetail._set_binding_type(type.EnumType(
    'com.vmware.esx.settings.clusters.software.reports.compliance_status_detail',
    ComplianceStatusDetail))



class Service(Enum):
    """
    The ``Service`` class specifies information about vSphere solutions that
    have solution specific VMware compatibility Guide certification. This
    enumeration was added in vSphere API 8.0.0.1.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    VSAN = None
    """


    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`Service` instance.
        """
        Enum.__init__(string)

Service._set_values({
    'VSAN': Service('VSAN'),
})
Service._set_binding_type(type.EnumType(
    'com.vmware.esx.settings.clusters.software.reports.service',
    Service))



class ComplianceStatus(Enum):
    """
    The ``ComplianceStatus`` class contains the possible different status of
    compliance with respect to target version.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    COMPATIBLE = None
    """
    Target hardware is compliant with VMware Compatibility Guide (VCG)

    """
    INCOMPATIBLE = None
    """
    Target hardware is not (recognizably) compliant with VMware Compatibility
    Guide (VCG)

    """
    HCL_DATA_UNAVAILABLE = None
    """
    HCL data can not be fetched to validate cluster hardware.

    """
    UNAVAILABLE = None
    """
    Target hardware compliance with VMware Compatibility Guide (VCG) cannot be
    determined.

    """
    NO_FIRMWARE_PROVIDER = None
    """
    No Firmware HSM present in Software Spec to get Firmware Details
    :class:`com.vmware.esx.settings_client.HardwareSupportPackageInfo` class

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`ComplianceStatus` instance.
        """
        Enum.__init__(string)

ComplianceStatus._set_values({
    'COMPATIBLE': ComplianceStatus('COMPATIBLE'),
    'INCOMPATIBLE': ComplianceStatus('INCOMPATIBLE'),
    'HCL_DATA_UNAVAILABLE': ComplianceStatus('HCL_DATA_UNAVAILABLE'),
    'UNAVAILABLE': ComplianceStatus('UNAVAILABLE'),
    'NO_FIRMWARE_PROVIDER': ComplianceStatus('NO_FIRMWARE_PROVIDER'),
})
ComplianceStatus._set_binding_type(type.EnumType(
    'com.vmware.esx.settings.clusters.software.reports.compliance_status',
    ComplianceStatus))



class FirmwareVersionMatchingCriteria(Enum):
    """
    The ``FirmwareVersionMatchingCriteria`` class contains the criteria for
    firmware version comparison. This enumeration was added in vSphere API
    8.0.0.1.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    EXACT = None
    """


    """
    MINIMUM = None
    """


    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`FirmwareVersionMatchingCriteria` instance.
        """
        Enum.__init__(string)

FirmwareVersionMatchingCriteria._set_values({
    'EXACT': FirmwareVersionMatchingCriteria('EXACT'),
    'MINIMUM': FirmwareVersionMatchingCriteria('MINIMUM'),
})
FirmwareVersionMatchingCriteria._set_binding_type(type.EnumType(
    'com.vmware.esx.settings.clusters.software.reports.firmware_version_matching_criteria',
    FirmwareVersionMatchingCriteria))




class DriverFirmwareVersion(VapiStruct):
    """
    The ``DriverFirmwareVersion`` class contains information about device's
    driver and firmware version combination from Hardware Compatibility List or
    from the target versions from the desired state.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 driver_version=None,
                 firmware_version=None,
                 driver_name=None,
                ):
        """
        :type  driver_version: :class:`str`
        :param driver_version: Driver Version.
        :type  firmware_version: :class:`str`
        :param firmware_version: Firmware Version. This will be an empty string if the target
            firmware version cannot be determined.
        :type  driver_name: :class:`str`
        :param driver_name: Driver Name.
        """
        self.driver_version = driver_version
        self.firmware_version = firmware_version
        self.driver_name = driver_name
        VapiStruct.__init__(self)


DriverFirmwareVersion._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.software.reports.driver_firmware_version', {
        'driver_version': type.StringType(),
        'firmware_version': type.StringType(),
        'driver_name': type.StringType(),
    },
    DriverFirmwareVersion,
    False,
    None))



class PciDeviceConstraint(VapiStruct):
    """
    The ``PciDeviceConstraint`` class contain information about PCI device's
    hardware compatibility certification including details like driver and/or
    firmware versions and the set of validated features supported. This class
    was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 firmware_version=None,
                 firmware_version_match=None,
                 driver_name=None,
                 driver_version=None,
                 supported_features=None,
                ):
        """
        :type  firmware_version: :class:`str` or ``None``
        :param firmware_version: Certified Firmware Version. This attribute was added in vSphere API
            8.0.0.1.
            This attribute will be None - If there is no firware version
            specified for the device
        :type  firmware_version_match: :class:`FirmwareVersionMatchingCriteria` or ``None``
        :param firmware_version_match: Criteria for matching firmware version. This attribute was added in
            vSphere API 8.0.0.1.
            This attribute will be None when firmware version is not set
        :type  driver_name: :class:`str` or ``None``
        :param driver_name: Certified Driver Name. This attribute was added in vSphere API
            8.0.0.1.
            This attribute will be None If there is no driver certification for
            the device
        :type  driver_version: :class:`str` or ``None``
        :param driver_version: Certified Driver Version(Exact Matching criteria). This attribute
            was added in vSphere API 8.0.0.1.
            This attribute will be None If there is no driver certification for
            the device.
        :type  supported_features: :class:`dict` of :class:`Service` and :class:`set` of :class:`str`
        :param supported_features: Map of solutions and the corresponding features that the device is
            certified for in the VMware Compatibility Guide If map is empty,
            device is not certified for any specific solutions like vSAN. If
            Service is set but features are empty, means device is certified
            for solution. If Service is set and features is also set, means
            device is certified for specific features. This attribute was added
            in vSphere API 8.0.0.1.
        """
        self.firmware_version = firmware_version
        self.firmware_version_match = firmware_version_match
        self.driver_name = driver_name
        self.driver_version = driver_version
        self.supported_features = supported_features
        VapiStruct.__init__(self)


PciDeviceConstraint._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.software.reports.pci_device_constraint', {
        'firmware_version': type.OptionalType(type.StringType()),
        'firmware_version_match': type.OptionalType(type.ReferenceType(__name__, 'FirmwareVersionMatchingCriteria')),
        'driver_name': type.OptionalType(type.StringType()),
        'driver_version': type.OptionalType(type.StringType()),
        'supported_features': type.MapType(type.ReferenceType(__name__, 'Service'), type.SetType(type.StringType())),
    },
    PciDeviceConstraint,
    False,
    None))



class StorageDeviceConstraint(VapiStruct):
    """
    The ``StorageHclConstraint`` class contains information about Storage
    device's hardware compatibility certification including details like driver
    and/or firmware versions and the set of validated features supported. This
    class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 firmware_version=None,
                 firmware_version_match=None,
                 driver_name=None,
                 driver_version=None,
                 supported_features=None,
                ):
        """
        :type  firmware_version: :class:`str` or ``None``
        :param firmware_version: Certified Firmware Version. This attribute was added in vSphere API
            8.0.0.1.
            This attribute will be None- If there is no firware version
            specified for the device
        :type  firmware_version_match: :class:`FirmwareVersionMatchingCriteria` or ``None``
        :param firmware_version_match: Criteria for matching firmware version. This attribute was added in
            vSphere API 8.0.0.1.
            This attribute will be None when firmware version is not set
        :type  driver_name: :class:`str` or ``None``
        :param driver_name: Certified Driver Name. This attribute was added in vSphere API
            8.0.0.1.
            This attribute will be None If there is no driver certification for
            the device
        :type  driver_version: :class:`str` or ``None``
        :param driver_version: Certified Driver Version. This attribute was added in vSphere API
            8.0.0.1.
            This attribute will be None If there is no driver certification for
            the device
        :type  supported_features: :class:`dict` of :class:`Service` and :class:`set` of :class:`str`
        :param supported_features: Map of solutions and the corresponding features that the device is
            certified for in the VMware Compatibility Guide If map is empty,
            device is not certified for any specific solutions like vSAN If
            Service is set but features are empty, means device is certified
            for solution. If Service is set and features is also set, means
            device is certified for specific features. This attribute was added
            in vSphere API 8.0.0.1.
            This attribute is optional because it was added in a newer version
            than its parent node.
        """
        self.firmware_version = firmware_version
        self.firmware_version_match = firmware_version_match
        self.driver_name = driver_name
        self.driver_version = driver_version
        self.supported_features = supported_features
        VapiStruct.__init__(self)


StorageDeviceConstraint._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.software.reports.storage_device_constraint', {
        'firmware_version': type.OptionalType(type.StringType()),
        'firmware_version_match': type.OptionalType(type.ReferenceType(__name__, 'FirmwareVersionMatchingCriteria')),
        'driver_name': type.OptionalType(type.StringType()),
        'driver_version': type.OptionalType(type.StringType()),
        'supported_features': type.OptionalType(type.MapType(type.ReferenceType(__name__, 'Service'), type.SetType(type.StringType()))),
    },
    StorageDeviceConstraint,
    False,
    None))



class PciDevice(VapiStruct):
    """
    The ``PciDevice`` class contains information about a PCI Device.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 display_name=None,
                 driver_name=None,
                 vendor=None,
                 vid=None,
                 did=None,
                 svid=None,
                 ssid=None,
                ):
        """
        :type  display_name: :class:`str`
        :param display_name: Display name of the device.
        :type  driver_name: :class:`str`
        :param driver_name: Driver Name of the device.
        :type  vendor: :class:`str`
        :param vendor: Vendor Name of the device.
        :type  vid: :class:`str`
        :param vid: PCI VID of the device.
        :type  did: :class:`str`
        :param did: PCI DID of the device.
        :type  svid: :class:`str`
        :param svid: PCI SVID of the device.
        :type  ssid: :class:`str`
        :param ssid: PCI SSID of the device.
        """
        self.display_name = display_name
        self.driver_name = driver_name
        self.vendor = vendor
        self.vid = vid
        self.did = did
        self.svid = svid
        self.ssid = ssid
        VapiStruct.__init__(self)


PciDevice._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.software.reports.pci_device', {
        'display_name': type.StringType(),
        'driver_name': type.StringType(),
        'vendor': type.StringType(),
        'vid': type.StringType(),
        'did': type.StringType(),
        'svid': type.StringType(),
        'ssid': type.StringType(),
    },
    PciDevice,
    False,
    None))



class PciDeviceComplianceInfo(VapiStruct):
    """
    The ``PciDeviceComplianceInfo`` class contains information that describe
    the compliance of a pci device with respect to the component present in the
    target software specification.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 status=None,
                 device=None,
                 compatible_versions=None,
                 host_info=None,
                 target=None,
                 validated_features_in_use=None,
                 supported=None,
                 constraints=None,
                 compatibility_guide_link=None,
                 notifications=None,
                ):
        """
        :type  status: :class:`ComplianceStatus`
        :param status: High-level compliance status of the device.
        :type  device: :class:`PciDevice`
        :param device: Pci Device Details
        :type  compatible_versions: :class:`list` of :class:`str`
        :param compatible_versions: List of vSphere Versions compatible for this device. This field is
            populated only for device found INCOMPATIBLE
        :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
        :param host_info: Affected List of Host IDs where this device is found.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``HostSystem``. When methods return a value of this class as
            a return value, the key in the attribute :class:`dict` will be an
            identifier for the resource type: ``HostSystem``.
        :type  target: :class:`DriverFirmwareVersion`
        :param target: Driver and Firmware Version from Image Specification.
        :type  validated_features_in_use: :class:`dict` of :class:`Service` and :class:`set` of :class:`str`
        :param validated_features_in_use: Validated features in use on this device If Service is set but
            features is empty, device is active for solution Subset of
            validated features for which we provide certification - for example
            RDMA, not IPV6 Inclusion in this set of features is independent of
            the certification status of device. In other words it's possible a
            device is configured to use a feature it is not certified. This
            attribute was added in vSphere API 8.0.0.1.
            This attribute is optional because it was added in a newer version
            than its parent node.
        :type  supported: :class:`list` of :class:`DriverFirmwareVersion`
        :param supported: List of Supported Driver and Firmware Version combination from
            Harware Compatibility List.

            .. deprecated:: vSphere API 8.0.0.1
        :type  constraints: :class:`list` of :class:`PciDeviceConstraint`
        :param constraints: List of Supported Driver and Firmware Version combination and
            corresponding supportedFeatures from VMware Compatibility Guide
            (VCG) listing for the given vSphere version. This attribute was
            added in vSphere API 8.0.0.1.
            This attribute is optional because it was added in a newer version
            than its parent node.
        :type  compatibility_guide_link: :class:`str` or ``None``
        :param compatibility_guide_link: Provides link to the VMware Compatibility Guide for further
            information on the compatibility.
            If None there is no VMware Compatibility link available as this is
            device used by VSAN.
        :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
        :param notifications: Device Specific notifications describing the compliance result.
            This attribute will be None if there are no notifications
        """
        self.status = status
        self.device = device
        self.compatible_versions = compatible_versions
        self.host_info = host_info
        self.target = target
        self.validated_features_in_use = validated_features_in_use
        self.supported = supported
        self.constraints = constraints
        self.compatibility_guide_link = compatibility_guide_link
        self.notifications = notifications
        VapiStruct.__init__(self)


PciDeviceComplianceInfo._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.software.reports.pci_device_compliance_info', {
        'status': type.ReferenceType(__name__, 'ComplianceStatus'),
        'device': type.ReferenceType(__name__, 'PciDevice'),
        'compatible_versions': type.ListType(type.StringType()),
        'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
        'target': type.ReferenceType(__name__, 'DriverFirmwareVersion'),
        'validated_features_in_use': type.OptionalType(type.MapType(type.ReferenceType(__name__, 'Service'), type.SetType(type.StringType()))),
        'supported': type.ListType(type.ReferenceType(__name__, 'DriverFirmwareVersion')),
        'constraints': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'PciDeviceConstraint'))),
        'compatibility_guide_link': type.OptionalType(type.URIType()),
        'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
    },
    PciDeviceComplianceInfo,
    False,
    None))



class PciDeviceCompliance(VapiStruct):
    """
    The ``PciDeviceCompliance`` class contains information that describe the
    compliance result of all pci device from all hosts in the clsuter with
    respect to the component present in the target software specification.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 status=None,
                 compatible_devices=None,
                 incompatible_devices=None,
                 incompatible_driver_firmware=None,
                ):
        """
        :type  status: :class:`ComplianceStatus`
        :param status: Over all Compliance status of PCI Devices in Cluster with
            respective to all hosts in the cluster.
        :type  compatible_devices: :class:`list` of :class:`PciDeviceComplianceInfo`
        :param compatible_devices: Compatible Device Compliance result for all devices present on all
            hosts in the cluster compared with the corresponding component in
            the software specification. The key is the DeviceName and value is
            the PciDeviceComplianceInfo object.
        :type  incompatible_devices: :class:`list` of :class:`PciDeviceComplianceInfo`
        :param incompatible_devices: Incompatible Device Compliance result for all devices present on
            all hosts in the cluster compared with the corresponding component
            in the software specification. The key is the DeviceName and value
            is the PciDeviceComplianceInfo object.
        :type  incompatible_driver_firmware: :class:`list` of :class:`PciDeviceComplianceInfo`
        :param incompatible_driver_firmware: Incompatible Driver Firmware combination Compliance result for all
            devices present on hosts in the cluster compared with the
            corresponding component in the software specification. The key is
            the DeviceName and value is the PciDeviceComplianceInfo object.
        """
        self.status = status
        self.compatible_devices = compatible_devices
        self.incompatible_devices = incompatible_devices
        self.incompatible_driver_firmware = incompatible_driver_firmware
        VapiStruct.__init__(self)


PciDeviceCompliance._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.software.reports.pci_device_compliance', {
        'status': type.ReferenceType(__name__, 'ComplianceStatus'),
        'compatible_devices': type.ListType(type.ReferenceType(__name__, 'PciDeviceComplianceInfo')),
        'incompatible_devices': type.ListType(type.ReferenceType(__name__, 'PciDeviceComplianceInfo')),
        'incompatible_driver_firmware': type.ListType(type.ReferenceType(__name__, 'PciDeviceComplianceInfo')),
    },
    PciDeviceCompliance,
    False,
    None))



class StorageDeviceInfo(VapiStruct):
    """
    The ``StorageDeviceInfo`` class contains attributes describing a storage
    device. This class was added in vSphere API 7.0.2.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 model=None,
                 vendor=None,
                 part_number=None,
                 capacity=None,
                ):
        """
        :type  model: :class:`str`
        :param model: Storage device model. This attribute was added in vSphere API
            7.0.2.1.
        :type  vendor: :class:`str`
        :param vendor: Storage device vendor. This attribute was added in vSphere API
            7.0.2.1.
        :type  part_number: :class:`str` or ``None``
        :param part_number: Hardware part number of the storage device. This attribute was
            added in vSphere API 7.0.2.1.
            This attribute will be unest if part number information is not
            available for the storage device.
        :type  capacity: :class:`long`
        :param capacity: Capacity of the storage device in bytes. This attribute was added
            in vSphere API 7.0.2.1.
        """
        self.model = model
        self.vendor = vendor
        self.part_number = part_number
        self.capacity = capacity
        VapiStruct.__init__(self)


StorageDeviceInfo._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.software.reports.storage_device_info', {
        'model': type.StringType(),
        'vendor': type.StringType(),
        'part_number': type.OptionalType(type.StringType()),
        'capacity': type.IntegerType(),
    },
    StorageDeviceInfo,
    False,
    None))



class StorageDeviceCompatibility(VapiStruct):
    """
    The ``StorageDeviceCompatibility`` class contains information that describe
    the compliance of a storage device with respect to the component present in
    the target software specification. This class was added in vSphere API
    7.0.2.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 status=None,
                 compatible_versions=None,
                 supported_firmware_versions=None,
                 constraints=None,
                 vcg_product=None,
                 model=None,
                 partner=None,
                 compatibility_guide_link=None,
                 used_for_compliance=None,
                 user_selected=None,
                 notifications=None,
                ):
        """
        :type  status: :class:`ComplianceStatus`
        :param status: Compliance status of the storage device, when computed based on
            this VMware Compatibility Guide (VCG) listing. This attribute was
            added in vSphere API 7.0.2.1.
        :type  compatible_versions: :class:`list` of :class:`str` or ``None``
        :param compatible_versions: List of vSphere Versions compatible for this storage device. This
            attribute was added in vSphere API 7.0.2.1.
            This attribute will be None if the storage device is certified for
            the target ESXi version.
        :type  supported_firmware_versions: :class:`list` of :class:`str` or ``None``
        :param supported_firmware_versions: List of minimum firmware versions supported from VMware
            Compatibility Guide (VCG) listing for the given vSphere version.
            This attribute was added in vSphere API 7.0.2.1.
            This attribute will be None if the storage device is not certified
            for the target ESXi version or the storage device is only certified
            in combination with specific driver versions, in which case
            listedDriverFirmwareVersions below will be set.

            .. deprecated:: vSphere API 8.0.0.1
        :type  constraints: :class:`list` of :class:`StorageDeviceConstraint`
        :param constraints: List of Supported Firmware Versions and corresponding supported
            features from VMware Compatibility Guide (VCG) listing for the
            given vSphere version. This attribute was added in vSphere API
            8.0.0.1.
            This attribute is optional because it was added in a newer version
            than its parent node.
        :type  vcg_product: :class:`str`
        :param vcg_product: Identifier of the VMware Compatibility Guide (VCG) listing for the
            product. This attribute was added in vSphere API 7.0.2.1.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.esx.settings.vcg_product``. When methods return a
            value of this class as a return value, the attribute will be an
            identifier for the resource type:
            ``com.vmware.esx.settings.vcg_product``.
        :type  model: :class:`str`
        :param model: Model name of the storage device as listed in the VMware
            Compatibility Guide (VCG) listing. This may not be the same as the
            :attr:`StorageDeviceInfo.model`. This attribute was added in
            vSphere API 7.0.2.1.
        :type  partner: :class:`str`
        :param partner: OEM partner name of the storage device as listed in the VMware
            Compatibility Guide (VCG) listing. This attribute was added in
            vSphere API 7.0.2.1.
        :type  compatibility_guide_link: :class:`str`
        :param compatibility_guide_link: Provides link to the VMware Compatibility Guide (VCG) listing for
            further information on the compatibility. This attribute was added
            in vSphere API 7.0.2.1.
        :type  used_for_compliance: :class:`bool`
        :param used_for_compliance: Flag to indicate whether this VMware compatibility Guide (VCG)
            listing was used to compute the overall compatibility of the
            storage device. This attribute was added in vSphere API 7.0.2.1.
        :type  user_selected: :class:`bool`
        :param user_selected: Flag to indicate if the user has selected this VMware Compatibility
            Guide (VCG) listing to be considered to compute the overall
            compatibility of the storage device. This attribute was added in
            vSphere API 7.0.2.1.
        :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
        :param notifications: VMware compatibility Guide (VCG) listing specific notifications
            describing the compliance result. This attribute was added in
            vSphere API 7.0.2.1.
            This attribute will be None if there are no notifications
        """
        self.status = status
        self.compatible_versions = compatible_versions
        self.supported_firmware_versions = supported_firmware_versions
        self.constraints = constraints
        self.vcg_product = vcg_product
        self.model = model
        self.partner = partner
        self.compatibility_guide_link = compatibility_guide_link
        self.used_for_compliance = used_for_compliance
        self.user_selected = user_selected
        self.notifications = notifications
        VapiStruct.__init__(self)


StorageDeviceCompatibility._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.software.reports.storage_device_compatibility', {
        'status': type.ReferenceType(__name__, 'ComplianceStatus'),
        'compatible_versions': type.OptionalType(type.ListType(type.StringType())),
        'supported_firmware_versions': type.OptionalType(type.ListType(type.StringType())),
        'constraints': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'StorageDeviceConstraint'))),
        'vcg_product': type.IdType(resource_types='com.vmware.esx.settings.vcg_product'),
        'model': type.StringType(),
        'partner': type.StringType(),
        'compatibility_guide_link': type.URIType(),
        'used_for_compliance': type.BooleanType(),
        'user_selected': type.BooleanType(),
        'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
    },
    StorageDeviceCompatibility,
    False,
    None))



class StorageDeviceComplianceInfo(VapiStruct):
    """
    The ``StorageDeviceComplianceInfo`` class contains attributes that describe
    the compliance information of a storage device. This class was added in
    vSphere API 7.0.2.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 storage_device_info=None,
                 device_count=None,
                 status=None,
                 detail=None,
                 host_info=None,
                 firmware_version=None,
                 validated_features_in_use=None,
                 driver_name=None,
                 driver_version=None,
                 matches=None,
                 used_by_vsan=None,
                 notifications=None,
                ):
        """
        :type  storage_device_info: :class:`StorageDeviceInfo`
        :param storage_device_info: Information of the storage device. This attribute was added in
            vSphere API 7.0.2.1.
        :type  device_count: :class:`long`
        :param device_count: Indicate the number of actual physical storage devices represented
            by this info. This attribute was added in vSphere API 8.0.0.1.
            This attribute is optional because it was added in a newer version
            than its parent node.
        :type  status: :class:`ComplianceStatus`
        :param status: Compliance status of the storage device. When there are multiple
            possible VMware Compatibility Guide (VCG) matches for the storage
            device, the compliance status would be set to
            :attr:`ComplianceStatus.UNAVAILABLE` Each match found would be
            listed under :attr:`StorageDeviceComplianceInfo.matches` with the
            corresponding compliance status of the storage device if compared
            against the constraints specified in the match. This attribute was
            added in vSphere API 7.0.2.1.
        :type  detail: :class:`ComplianceStatusDetail`
        :param detail: Detailed compliance status of the storage device. This attribute
            was added in vSphere API 7.0.2.1.
        :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
        :param host_info: Affected List of Host IDs where this device is found. This
            attribute was added in vSphere API 7.0.2.1.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``HostSystem``. When methods return a value of this class as
            a return value, the key in the attribute :class:`dict` will be an
            identifier for the resource type: ``HostSystem``.
        :type  firmware_version: :class:`str` or ``None``
        :param firmware_version: Firmware version on the storage device. This attribute was added in
            vSphere API 7.0.2.1.
            This attribute will be None if the firmware version on the storage
            device is unknown or cannot be determined.
        :type  validated_features_in_use: :class:`dict` of :class:`Service` and :class:`set` of :class:`str`
        :param validated_features_in_use: Validated Features in use on the storage device If Service is set
            but features is empty, device is active for solution Subset of
            validated features for which we provide certification - for example
            RDMA, not IPV6 Inclusion in this set of features is independent of
            the certification status of device. In other words it's possible a
            device is configured to use a feature it is not certified. This
            attribute was added in vSphere API 8.0.0.1.
            This attribute is optional because it was added in a newer version
            than its parent node.
        :type  driver_name: :class:`str` or ``None``
        :param driver_name: Driver name on the storage device. This attribute was added in
            vSphere API 8.0.0.1.
            This attribute will be None if there is no driver associated with
            the device.
        :type  driver_version: :class:`str` or ``None``
        :param driver_version: Driver Version on the storage device. This attribute was added in
            vSphere API 8.0.0.1.
            This attribute will be None if there is no driver associated with
            the device.
        :type  matches: :class:`list` of :class:`StorageDeviceCompatibility`
        :param matches: Provides information about possible compatibility matches for the
            given storage device. 
            
            There could be multiple possible matches available in the
            compatibility data.. This attribute was added in vSphere API
            7.0.2.1.
        :type  used_by_vsan: :class:`bool`
        :param used_by_vsan: Indicates if the storage device is in use by vSAN. When this flag
            is set to true, the hardware compatibility is computed against vSAN
            HCL constraints. This attribute was added in vSphere API 7.0.2.1.

            .. deprecated:: vSphere API 8.0.0.1
        :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
        :param notifications: Device Specific notifications describing the compliance result.
            This attribute was added in vSphere API 7.0.2.1.
            This attribute will be None if there are no notifications
        """
        self.storage_device_info = storage_device_info
        self.device_count = device_count
        self.status = status
        self.detail = detail
        self.host_info = host_info
        self.firmware_version = firmware_version
        self.validated_features_in_use = validated_features_in_use
        self.driver_name = driver_name
        self.driver_version = driver_version
        self.matches = matches
        self.used_by_vsan = used_by_vsan
        self.notifications = notifications
        VapiStruct.__init__(self)


StorageDeviceComplianceInfo._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.software.reports.storage_device_compliance_info', {
        'storage_device_info': type.ReferenceType(__name__, 'StorageDeviceInfo'),
        'device_count': type.OptionalType(type.IntegerType()),
        'status': type.ReferenceType(__name__, 'ComplianceStatus'),
        'detail': type.ReferenceType(__name__, 'ComplianceStatusDetail'),
        'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
        'firmware_version': type.OptionalType(type.StringType()),
        'validated_features_in_use': type.OptionalType(type.MapType(type.ReferenceType(__name__, 'Service'), type.SetType(type.StringType()))),
        'driver_name': type.OptionalType(type.StringType()),
        'driver_version': type.OptionalType(type.StringType()),
        'matches': type.ListType(type.ReferenceType(__name__, 'StorageDeviceCompatibility')),
        'used_by_vsan': type.BooleanType(),
        'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
    },
    StorageDeviceComplianceInfo,
    False,
    None))



class StorageDeviceCompliance(VapiStruct):
    """
    The ``StorageDeviceCompliance`` class contains information that describe
    the compliance result of all storage devices from all hosts in the cluster
    with respect to the storage device model and the firmware certification.
    This class was added in vSphere API 7.0.2.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 status=None,
                 compatible_devices=None,
                 incompatible_devices=None,
                 unknown_devices=None,
                 notifications=None,
                ):
        """
        :type  status: :class:`ComplianceStatus`
        :param status: Overall compliance status of storage devices in the cluster with
            respect to all hosts in the cluster. This attribute was added in
            vSphere API 7.0.2.1.
        :type  compatible_devices: :class:`list` of :class:`StorageDeviceComplianceInfo`
        :param compatible_devices: Lists compliance information for storage devices found to be
            compliant with VMware Compatibility Guide (VCG) during the last
            check method. 
            
            Note that complianceStatus of every device is not necessarily
            COMPATIBLE due to changes made after this check was run; entries
            are only rearranged when a new check method is invoked.
            lastOverrideTime being greater than the scanTime is an indication
            that there were changes made after the last check method. This
            attribute was added in vSphere API 7.0.2.1.
        :type  incompatible_devices: :class:`list` of :class:`StorageDeviceComplianceInfo`
        :param incompatible_devices: Lists compliance information for storage devices found to be
            non-compliant with VMware Compatibility Guide (VCG) during the last
            check method. 
            
            Note that complianceStatus of every device is not necessarily
            INCOMPATIBLE due to changes made after this check was run; entries
            are only rearranged when a new check method is invoked.
            lastOverrideTime being greater than the scanTime is an indication
            that there were changes made after the last check method. This
            attribute was added in vSphere API 7.0.2.1.
        :type  unknown_devices: :class:`list` of :class:`StorageDeviceComplianceInfo`
        :param unknown_devices: Lists storage devices whose compliance information could not be
            computed successfully during the last check method. 
            
            Note that complianceStatus of every device is not necessarily
            UNAVAILABLE due to changes made after this check was run; entries
            are only rearranged when a new check method is invoked.
            lastOverrideTime being greater than the scanTime is an indication
            that there were changes made after the last check method. This
            attribute was added in vSphere API 7.0.2.1.
        :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
        :param notifications: Storage device compliance specific notifications describing the
            compliance result. This attribute was added in vSphere API 7.0.2.1.
            This attribute will be None if there are no notifications
        """
        self.status = status
        self.compatible_devices = compatible_devices
        self.incompatible_devices = incompatible_devices
        self.unknown_devices = unknown_devices
        self.notifications = notifications
        VapiStruct.__init__(self)


StorageDeviceCompliance._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.software.reports.storage_device_compliance', {
        'status': type.ReferenceType(__name__, 'ComplianceStatus'),
        'compatible_devices': type.ListType(type.ReferenceType(__name__, 'StorageDeviceComplianceInfo')),
        'incompatible_devices': type.ListType(type.ReferenceType(__name__, 'StorageDeviceComplianceInfo')),
        'unknown_devices': type.ListType(type.ReferenceType(__name__, 'StorageDeviceComplianceInfo')),
        'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
    },
    StorageDeviceCompliance,
    False,
    None))



class CheckResult(VapiStruct):
    """
    The ``CheckResult`` class contains information to describe HCL compliance
    result of a cluster on target software specification.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 status=None,
                 scan_time=None,
                 updated_since_last_check=None,
                 v_san_data_only=None,
                 commit=None,
                 base_image_version=None,
                 pci_device_compliance=None,
                 storage_device_compliance=None,
                 notifications=None,
                 note=None,
                ):
        """
        :type  status: :class:`ComplianceStatus`
        :param status: Overall compliance status of Cluster with respective to all hosts
            in the cluster.
        :type  scan_time: :class:`datetime.datetime`
        :param scan_time: HCL Validation check time.
        :type  updated_since_last_check: :class:`bool`
        :param updated_since_last_check: Flag to indicate if there were any hardware compatibility overrides
            were performed after the last check method. This attribute was
            added in vSphere API 7.0.2.1.
            This attribute is optional because it was added in a newer version
            than its parent node.
        :type  v_san_data_only: :class:`bool` or ``None``
        :param v_san_data_only: HCL Validation Computed only for vSAN Clusters.
            None to show vSAN in UI
        :type  commit: :class:`str` or ``None``
        :param commit: Spec Identifier of the desired configuration on which the HCL scan
            is performed to generate this result, populated by the HCL
            validation.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.esx.settings.commit``. When methods return a value of
            this class as a return value, the attribute will be an identifier
            for the resource type: ``com.vmware.esx.settings.commit``.
            This attribute will be None if validation was performed against a
            draft.
        :type  base_image_version: :class:`str`
        :param base_image_version: Target base image version E.g., version = BaseImageSpec->Version
            :attr:`com.vmware.esx.settings_client.BaseImageSpec.version` class
        :type  pci_device_compliance: :class:`PciDeviceCompliance` or ``None``
        :param pci_device_compliance: Compliance result for the Pci Devices that are present in all hosts
            of the cluster.
            This attribute will be None if Pci device compliance was not
            computed.
        :type  storage_device_compliance: :class:`StorageDeviceCompliance` or ``None``
        :param storage_device_compliance: Compliance result for storage devices in all the hosts of the
            cluster. Currently only includes SAS/SATA storage devices. This
            attribute was added in vSphere API 7.0.2.1.
            This attribute will be None if storage device compliance was not
            computed.
        :type  notifications: :class:`com.vmware.esx.settings_client.Notifications`
        :param notifications: Notifications returned by the HCL Validation operation.
        :type  note: :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param note: Localizable disclaimer notice to show on the UI detailing the type
            of checks are done by the HCL Validaiton. Example : HCL Validation
            is only done on storage and network controllers.
        """
        self.status = status
        self.scan_time = scan_time
        self.updated_since_last_check = updated_since_last_check
        self.v_san_data_only = v_san_data_only
        self.commit = commit
        self.base_image_version = base_image_version
        self.pci_device_compliance = pci_device_compliance
        self.storage_device_compliance = storage_device_compliance
        self.notifications = notifications
        self.note = note
        VapiStruct.__init__(self)


CheckResult._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.software.reports.check_result', {
        'status': type.ReferenceType(__name__, 'ComplianceStatus'),
        'scan_time': type.DateTimeType(),
        'updated_since_last_check': type.OptionalType(type.BooleanType()),
        'v_san_data_only': type.OptionalType(type.BooleanType()),
        'commit': type.OptionalType(type.IdType()),
        'base_image_version': type.StringType(),
        'pci_device_compliance': type.OptionalType(type.ReferenceType(__name__, 'PciDeviceCompliance')),
        'storage_device_compliance': type.OptionalType(type.ReferenceType(__name__, 'StorageDeviceCompliance')),
        'notifications': type.ReferenceType('com.vmware.esx.settings_client', 'Notifications'),
        'note': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
    },
    CheckResult,
    False,
    None))



class ApplyImpact(VapiInterface):
    """
    The ``ApplyImpact`` class provides methods to get the impact of an apply
    method on a cluster.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.software.reports.apply_impact'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ApplyImpactStub)
        self._VAPI_OPERATION_IDS = {}

    class ApplyImpactSpec(VapiStruct):
        """
        The ``ApplyImpact.ApplyImpactSpec`` class contains attributes that describe
        the specification to be used for getting the impact of an apply method on
        an ESXi cluster.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     hosts=None,
                    ):
            """
            :type  hosts: :class:`set` of :class:`str` or ``None``
            :param hosts: The specific hosts for which an impact is to be generated.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
                if None or empty impact is generated for all hosts within the
                cluster.
            """
            self.hosts = hosts
            VapiStruct.__init__(self)


    ApplyImpactSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.apply_impact.apply_impact_spec', {
            'hosts': type.OptionalType(type.SetType(type.IdType())),
        },
        ApplyImpactSpec,
        False,
        None))


    class Impact(VapiStruct):
        """
        The ``ApplyImpact.Impact`` class contains attributes that describe what the
        impact is of a particular step during the apply method.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     message=None,
                    ):
            """
            :type  message: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param message: Description of the impact.
            """
            self.message = message
            VapiStruct.__init__(self)


    Impact._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.apply_impact.impact', {
            'message': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
        },
        Impact,
        False,
        None))


    class ClusterImpact(VapiStruct):
        """
        The ``ApplyImpact.ClusterImpact`` class contains attributes that describe
        the summary of how hosts within a cluster will be impacted during an apply
        method.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     impact=None,
                     host_impact=None,
                     commit=None,
                     host_info=None,
                    ):
            """
            :type  impact: :class:`list` of :class:`ApplyImpact.Impact`
            :param impact: Impact of steps performed during the setup and cleanup phase of the
                apply method.
            :type  host_impact: :class:`dict` of :class:`str` and :class:`list` of :class:`ApplyImpact.Impact`
            :param host_impact: Impact summary for each host within the clsuter.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  commit: :class:`str`
            :param commit: Identifier of the commit on which the impact is generated.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information of hosts within the cluster.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            """
            self.impact = impact
            self.host_impact = host_impact
            self.commit = commit
            self.host_info = host_info
            VapiStruct.__init__(self)


    ClusterImpact._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.apply_impact.cluster_impact', {
            'impact': type.ListType(type.ReferenceType(__name__, 'ApplyImpact.Impact')),
            'host_impact': type.MapType(type.IdType(), type.ListType(type.ReferenceType(__name__, 'ApplyImpact.Impact'))),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
        },
        ClusterImpact,
        False,
        None))



    def get(self,
            cluster,
            spec=None,
            ):
        """
        Returns a summary of how hosts within the cluster will be impacted
        during an apply method. The impact is generated from the compliance
        information obtained from
        :func:`com.vmware.esx.settings.clusters.software_client.Compliance.get`

        :type  cluster: :class:`str`
        :param cluster: The cluster identifier.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`ApplyImpact.ApplyImpactSpec` or ``None``
        :param spec: 
            Specification for how much information should be returned.
        :rtype: :class:`ApplyImpact.ClusterImpact`
        :return: Summary of how hosts will be impacted during an apply method
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })
class HardwareCompatibility(VapiInterface):
    """
    The ``HardwareCompatibility`` class provides methods to manage HCL
    Validation of a software specification of an ESX cluster.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _HardwareCompatibilityStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'check_task': 'check$task'})

    class ComplianceStatus(Enum):
        """
        The ``HardwareCompatibility.ComplianceStatus`` class contains the possible
        different status of compliance with respect to target version.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        COMPATIBLE = None
        """
        Target hardware is compliant with VCG/HCL. This includes (from the
        ComplianceStatusDetail: 
        
        
        
        * COMPLIANT
        * VENDOR_UPDATE
        * USER_OVERRIDE

        """
        INCOMPATIBLE = None
        """
        Target hardware is not (recognizably) compliant with VCG/HCL This includes
        (from the ComplianceStatusDetail): 
        
        
        
        * NONCOMPLIANT
        * USER_FLAGGED
        * NONCOMPLIANCE_MUTED

        """
        HCL_DATA_UNAVAILABLE = None
        """
        HCL data can not be fetched to validate cluster hardware.

        """
        UNAVAILABLE = None
        """
        Target hardware compliance with VCG/HCL cannot be determined This includes
        (from the ComplianceStatusDetail): 
        
        
        
        * HCL_DATA_UNAVAILABLE
        * UNAVAILABLE
        * NO_FIRMWARE_PROVIDER
        * UNKNOWN

        """
        NO_FIRMWARE_PROVIDER = None
        """
        No Firmware HSM present in Software Spec to get Firmware Details
        :class:`com.vmware.esx.settings_client.HardwareSupportPackageInfo` class

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ComplianceStatus` instance.
            """
            Enum.__init__(string)

    ComplianceStatus._set_values({
        'COMPATIBLE': ComplianceStatus('COMPATIBLE'),
        'INCOMPATIBLE': ComplianceStatus('INCOMPATIBLE'),
        'HCL_DATA_UNAVAILABLE': ComplianceStatus('HCL_DATA_UNAVAILABLE'),
        'UNAVAILABLE': ComplianceStatus('UNAVAILABLE'),
        'NO_FIRMWARE_PROVIDER': ComplianceStatus('NO_FIRMWARE_PROVIDER'),
    })
    ComplianceStatus._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.compliance_status',
        ComplianceStatus))


    class CheckSummary(VapiStruct):
        """
        The ``HardwareCompatibility.CheckSummary`` class contains information to
        describe the HCL compliance summary result of a cluster on target software
        specification.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     status=None,
                     scan_time=None,
                     commit=None,
                     base_image_version=None,
                     summary_result=None,
                     notifications=None,
                    ):
            """
            :type  status: :class:`HardwareCompatibility.ComplianceStatus`
            :param status: Overall compliance status of the cluster with respective to all
                hosts in the cluster.
            :type  scan_time: :class:`datetime.datetime`
            :param scan_time: HCL Validation check time.
            :type  commit: :class:`str` or ``None``
            :param commit: Spec Identifier of the desired configuration on which the HCL scan
                is performed to generate this result, populated by the HCL
                validation.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
                This attribute will be None if validation was performed against a
                draft.
            :type  base_image_version: :class:`str`
            :param base_image_version: Target base image version E.g., version = BaseImageSpec->Version
                :attr:`com.vmware.esx.settings_client.BaseImageSpec.version` class
            :type  summary_result: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param summary_result: Over all Compliance result for cluster for the software
                specification.
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications`
            :param notifications: Notifications returned by the HCL Validation operation.
            """
            self.status = status
            self.scan_time = scan_time
            self.commit = commit
            self.base_image_version = base_image_version
            self.summary_result = summary_result
            self.notifications = notifications
            VapiStruct.__init__(self)


    CheckSummary._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.check_summary', {
            'status': type.ReferenceType(__name__, 'HardwareCompatibility.ComplianceStatus'),
            'scan_time': type.DateTimeType(),
            'commit': type.OptionalType(type.IdType()),
            'base_image_version': type.StringType(),
            'summary_result': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
            'notifications': type.ReferenceType('com.vmware.esx.settings_client', 'Notifications'),
        },
        CheckSummary,
        False,
        None))



    def get(self,
            cluster,
            ):
        """
        Returns the HCL validation check summary.

        :type  cluster: :class:`str`
        :param cluster: identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`HardwareCompatibility.CheckSummary`
        :return: CheckSummary HCL validation summary.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some other unknown internal error. The accompanying
            error message will give more details about the failure and any
            possible resolution(s).
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.HardwareCompatibility.Read``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.HardwareCompatibility.Read``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })


    def check_task(self,
              cluster,
              ):
        """
        Initiates a Cluster HCL Validation check for a given cluster. The
        result of this operation can be queried by calling the
        cis/tasks/{task-id} where the task-id is the response of this
        operation.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some other unknown internal error. The accompanying
            error message will give more details about the failure and any
            possible resolution(s).
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('check$task',
                                {
                                'cluster': cluster,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'CheckResult'))
        return task_instance
class LastApplyResult(VapiInterface):
    """
    The ``LastApplyResult`` class provides methods to get the most recent
    available result of applying the desired software document to all hosts
    within a cluster.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.software.reports.last_apply_result'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _LastApplyResultStub)
        self._VAPI_OPERATION_IDS = {}

    class ApplyStatus(VapiStruct):
        """
        The ``LastApplyResult.ApplyStatus`` class contains attributes that describe
        the status of an apply method.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'status',
                {
                    'OK' : [('progress', False)],
                    'RETRY_PENDING' : [('progress', False)],
                    'ERROR' : [('progress', False)],
                    'SKIPPED' : [],
                    'TIMED_OUT' : [],
                }
            ),
        ]



        def __init__(self,
                     status=None,
                     progress=None,
                     start_time=None,
                     end_time=None,
                     notifications=None,
                    ):
            """
            :type  status: :class:`LastApplyResult.ApplyStatus.Status`
            :param status: The status of the method.
            :type  progress: :class:`com.vmware.cis.task_client.Progress` or ``None``
            :param progress: Progress of the operation. This attribute was added in vSphere API
                7.0.2.1.
                None for #ApplyStatus of the cluster
            :type  start_time: :class:`datetime.datetime`
            :param start_time: Time when the method started.
            :type  end_time: :class:`datetime.datetime`
            :param end_time: Time when the method completed.
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications`
            :param notifications: Notifications providing additional information about the status of
                the method.
            """
            self.status = status
            self.progress = progress
            self.start_time = start_time
            self.end_time = end_time
            self.notifications = notifications
            VapiStruct.__init__(self)


        class Status(Enum):
            """
            The ``LastApplyResult.ApplyStatus.Status`` class contains the possible
            different status codes that can be returned while trying to apply the
            desired software specification to hosts within the cluster.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            OK = None
            """
            The method completed successfully.

            """
            SKIPPED = None
            """
            The method was skipped.

            """
            TIMED_OUT = None
            """
            The method timed out.

            """
            ERROR = None
            """
            The method encountered an unspecified error.

            """
            RETRY_PENDING = None
            """
            The method is being scheduled for retry. This class attribute was added in
            vSphere API 7.0.2.1.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Status` instance.
                """
                Enum.__init__(string)

        Status._set_values({
            'OK': Status('OK'),
            'SKIPPED': Status('SKIPPED'),
            'TIMED_OUT': Status('TIMED_OUT'),
            'ERROR': Status('ERROR'),
            'RETRY_PENDING': Status('RETRY_PENDING'),
        })
        Status._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.clusters.software.reports.last_apply_result.apply_status.status',
            Status))

    ApplyStatus._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.last_apply_result.apply_status', {
            'status': type.ReferenceType(__name__, 'LastApplyResult.ApplyStatus.Status'),
            'progress': type.OptionalType(type.ReferenceType('com.vmware.cis.task_client', 'Progress')),
            'start_time': type.DateTimeType(),
            'end_time': type.DateTimeType(),
            'notifications': type.ReferenceType('com.vmware.esx.settings_client', 'Notifications'),
        },
        ApplyStatus,
        False,
        None))


    class ApplyResult(VapiStruct):
        """
        The ``LastApplyResult.ApplyResult`` class contains attributes that describe
        the result of an apply method.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     status=None,
                     commit=None,
                     host_info=None,
                     host_status=None,
                     successful_hosts=None,
                     failed_hosts=None,
                     skipped_hosts=None,
                     notifications=None,
                    ):
            """
            :type  status: :class:`LastApplyResult.ApplyStatus`
            :param status: Specifies the aggregated status of the apply method.
            :type  commit: :class:`str`
            :param commit: The identifier of the commit used to fetch the desired software
                document to be applied to all hosts within the cluster.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information of the hosts in this cluster to which the desired
                software document specified by the
                :attr:`LastApplyResult.ApplyResult.commit` should be applied to.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  host_status: :class:`dict` of :class:`str` and :class:`LastApplyResult.ApplyStatus`
            :param host_status: Status of the hosts in this cluster to which the desired software
                document specified by the
                :attr:`LastApplyResult.ApplyResult.commit` was applied to. Hosts on
                which the apply method was sucessful are specified by
                :attr:`LastApplyResult.ApplyResult.successful_hosts`. Hosts on
                which the apply method failed are specified by
                :attr:`LastApplyResult.ApplyResult.failed_hosts`. Hosts which were
                skipped by the apply method are specified by
                :attr:`LastApplyResult.ApplyResult.skipped_hosts`.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  successful_hosts: :class:`set` of :class:`str`
            :param successful_hosts: Hosts in this cluster to which the desired software document
                specified by the :attr:`LastApplyResult.ApplyResult.commit` has
                been successfully applied to.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  failed_hosts: :class:`set` of :class:`str`
            :param failed_hosts: Hosts in this cluster to which the desired software document
                specified by the :attr:`LastApplyResult.ApplyResult.commit` failed
                to be applied to.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  skipped_hosts: :class:`set` of :class:`str`
            :param skipped_hosts: Hosts in this cluster that were skipped by the apply method.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
            :param notifications: Notifications providing additional information for
                :func:`com.vmware.esx.settings.clusters_client.Software.apply`
                method. These notifications are mutually exclusive with the
                notifications in ``LastApplyResult.ApplyStatus``. This attribute
                was added in vSphere API 7.0.2.1.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.status = status
            self.commit = commit
            self.host_info = host_info
            self.host_status = host_status
            self.successful_hosts = successful_hosts
            self.failed_hosts = failed_hosts
            self.skipped_hosts = skipped_hosts
            self.notifications = notifications
            VapiStruct.__init__(self)


    ApplyResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.last_apply_result.apply_result', {
            'status': type.ReferenceType(__name__, 'LastApplyResult.ApplyStatus'),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
            'host_status': type.MapType(type.IdType(), type.ReferenceType(__name__, 'LastApplyResult.ApplyStatus')),
            'successful_hosts': type.SetType(type.IdType()),
            'failed_hosts': type.SetType(type.IdType()),
            'skipped_hosts': type.SetType(type.IdType()),
            'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        ApplyResult,
        False,
        None))



    def get(self,
            cluster,
            ):
        """
        Returns the most recent available result of applying the desired
        software document to all hosts within the cluster.

        :type  cluster: :class:`str`
        :param cluster: The cluster identifier.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`LastApplyResult.ApplyResult`
        :return: Most recent available result of applying the desired software
            document to all hosts within the cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system or
            if there is no result associated with the cluster ``cluster``
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })
class LastCheckResult(VapiInterface):
    """
    The ``LastCheckResult`` class provides methods to get the most recent
    available result of the checks that have been run on a cluster before the
    application of the desired software document to all hosts within the
    cluster.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.software.reports.last_check_result'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _LastCheckResultStub)
        self._VAPI_OPERATION_IDS = {}

    class Status(Enum):
        """
        The ``LastCheckResult.Status`` class defines the status result for a
        particular check.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        OK = None
        """
        The check indicates a success.

        """
        WARNING = None
        """
        The check indicates a warning.

        """
        TIMEOUT = None
        """
        The check did not return in a timely manner.

        """
        ERROR = None
        """
        The check indicates an error.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Status` instance.
            """
            Enum.__init__(string)

    Status._set_values({
        'OK': Status('OK'),
        'WARNING': Status('WARNING'),
        'TIMEOUT': Status('TIMEOUT'),
        'ERROR': Status('ERROR'),
    })
    Status._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.software.reports.last_check_result.status',
        Status))


    class CheckInfo(VapiStruct):
        """
        The ``LastCheckResult.CheckInfo`` class contains attributes that describe a
        particular check.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     check=None,
                     name=None,
                     description=None,
                    ):
            """
            :type  check: :class:`str`
            :param check: The check identifier.
            :type  name: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param name: The check name.
            :type  description: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param description: Human-readable check description.
            """
            self.check = check
            self.name = name
            self.description = description
            VapiStruct.__init__(self)


    CheckInfo._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.last_check_result.check_info', {
            'check': type.StringType(),
            'name': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
            'description': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
        },
        CheckInfo,
        False,
        None))


    class CheckStatus(VapiStruct):
        """
        The ``LastCheckResult.CheckStatus`` class contains attributes that describe
        a check result.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     check=None,
                     status=None,
                     issues=None,
                    ):
            """
            :type  check: :class:`LastCheckResult.CheckInfo`
            :param check: Information about this check.
            :type  status: :class:`LastCheckResult.Status`
            :param status: The status of this check.
            :type  issues: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param issues: The issues encountered while running this check.
            """
            self.check = check
            self.status = status
            self.issues = issues
            VapiStruct.__init__(self)


    CheckStatus._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.last_check_result.check_status', {
            'check': type.ReferenceType(__name__, 'LastCheckResult.CheckInfo'),
            'status': type.ReferenceType(__name__, 'LastCheckResult.Status'),
            'issues': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        CheckStatus,
        False,
        None))


    class EntityCheckResult(VapiStruct):
        """
        The ``LastCheckResult.EntityCheckResult`` class contains attributes that
        describe aggregated status of all checks performed on a specific entity.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'type',
                {
                    'CLUSTER' : [('cluster', True)],
                    'HOST' : [('host', True)],
                }
            ),
        ]



        def __init__(self,
                     type=None,
                     cluster=None,
                     host=None,
                     status=None,
                     check_statuses=None,
                    ):
            """
            :type  type: :class:`LastCheckResult.EntityCheckResult.EntityType`
            :param type: The entity type for which these checks are being run.
            :type  cluster: :class:`str`
            :param cluster: If the entity type is CLUSTER then the cluster identifier for which
                the checks have been run.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
                This attribute is optional and it is only relevant when the value
                of ``type`` is
                :attr:`LastCheckResult.EntityCheckResult.EntityType.CLUSTER`.
            :type  host: :class:`str`
            :param host: If the entity type is HOST then the host identifier for which the
                checks have been run.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``HostSystem``.
                This attribute is optional and it is only relevant when the value
                of ``type`` is
                :attr:`LastCheckResult.EntityCheckResult.EntityType.HOST`.
            :type  status: :class:`LastCheckResult.Status`
            :param status: Aggregated status from all checks performed on this entity.
            :type  check_statuses: :class:`list` of :class:`LastCheckResult.CheckStatus`
            :param check_statuses: List of ``LastCheckResult.CheckStatus`` for all checks performed.
            """
            self.type = type
            self.cluster = cluster
            self.host = host
            self.status = status
            self.check_statuses = check_statuses
            VapiStruct.__init__(self)


        class EntityType(Enum):
            """
            The ``LastCheckResult.EntityCheckResult.EntityType`` class contains the
            entitites on which checks can be performed.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            CLUSTER = None
            """
            Entity type Cluster

            """
            HOST = None
            """
            Entity type Host

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`EntityType` instance.
                """
                Enum.__init__(string)

        EntityType._set_values({
            'CLUSTER': EntityType('CLUSTER'),
            'HOST': EntityType('HOST'),
        })
        EntityType._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.clusters.software.reports.last_check_result.entity_check_result.entity_type',
            EntityType))

    EntityCheckResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.last_check_result.entity_check_result', {
            'type': type.ReferenceType(__name__, 'LastCheckResult.EntityCheckResult.EntityType'),
            'cluster': type.OptionalType(type.IdType()),
            'host': type.OptionalType(type.IdType()),
            'status': type.ReferenceType(__name__, 'LastCheckResult.Status'),
            'check_statuses': type.ListType(type.ReferenceType(__name__, 'LastCheckResult.CheckStatus')),
        },
        EntityCheckResult,
        False,
        None))


    class CheckResult(VapiStruct):
        """
        The ``LastCheckResult.CheckResult`` class contains attributes that describe
        aggregated status of all checks performed.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     status=None,
                     start_time=None,
                     end_time=None,
                     commit=None,
                     host_info=None,
                     entity_results=None,
                    ):
            """
            :type  status: :class:`LastCheckResult.Status`
            :param status: Aggregated status from all checks performed.
            :type  start_time: :class:`datetime.datetime`
            :param start_time: Time when the operation started.
            :type  end_time: :class:`datetime.datetime`
            :param end_time: Time when the operation completed.
            :type  commit: :class:`str`
            :param commit: The identifier of the commit on which checks have been run.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information about the hosts in this cluster for which checks have
                been requested to be run.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  entity_results: :class:`list` of :class:`LastCheckResult.EntityCheckResult`
            :param entity_results: List of ``LastCheckResult.EntityCheckResult`` for all entities for
                which checks have been run.
            """
            self.status = status
            self.start_time = start_time
            self.end_time = end_time
            self.commit = commit
            self.host_info = host_info
            self.entity_results = entity_results
            VapiStruct.__init__(self)


    CheckResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.last_check_result.check_result', {
            'status': type.ReferenceType(__name__, 'LastCheckResult.Status'),
            'start_time': type.DateTimeType(),
            'end_time': type.DateTimeType(),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
            'entity_results': type.ListType(type.ReferenceType(__name__, 'LastCheckResult.EntityCheckResult')),
        },
        CheckResult,
        False,
        None))



    def get(self,
            cluster,
            ):
        """
        Returns the most recent available result of checks run on the cluster
        before the application of the desired software document to all hosts
        within the cluster.

        :type  cluster: :class:`str`
        :param cluster: The cluster identifier.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`LastCheckResult.CheckResult`
        :return: Most recent result available of the checks run on the cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system or
            if there is no result associated with the cluster ``cluster``
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })
class _ApplyImpactStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.OptionalType(type.ReferenceType(__name__, 'ApplyImpact.ApplyImpactSpec')),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/software/reports/apply-impact',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'ApplyImpact.ClusterImpact'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.clusters.software.reports.apply_impact',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _HardwareCompatibilityStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/software/reports/hardware-compatibility',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for check operation
        check_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        check_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        check_input_value_validator_list = [
        ]
        check_output_validator_list = [
        ]
        check_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/software/reports/hardware-compatibility',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'check',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'HardwareCompatibility.CheckSummary'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'check$task': {
                'input_type': check_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': check_error_dict,
                'input_value_validator_list': check_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'check': check_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.clusters.software.reports.hardware_compatibility',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _LastApplyResultStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/software/reports/last-apply-result',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'LastApplyResult.ApplyResult'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.clusters.software.reports.last_apply_result',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _LastCheckResultStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/software/reports/last-check-result',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'LastCheckResult.CheckResult'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.clusters.software.reports.last_check_result',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'ApplyImpact': ApplyImpact,
        'HardwareCompatibility': HardwareCompatibility,
        'LastApplyResult': LastApplyResult,
        'LastCheckResult': LastCheckResult,
        'hardware_compatibility': 'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility_client.StubFactory',
    }

