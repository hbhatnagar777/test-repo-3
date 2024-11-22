# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.
#---------------------------------------------------------------------------

"""


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


class ComplianceStatus(VapiInterface):
    """
    This class provides methods to manage hardware hardware compatibility
    overrides for storage devices. This class was added in vSphere API 7.0.2.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.compliance_status'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ComplianceStatusStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'update_task': 'update$task'})

    class ComplianceAction(Enum):
        """
        The ``ComplianceStatus.ComplianceAction`` class enumerates the possible
        compliance status overrides for a storage device. This enumeration was
        added in vSphere API 7.0.2.1.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        MARK_AS_VERIFIED = None
        """
        Specifying this override for a storage device would ignore the
        compatibility issues if any, and treat the drive as compliant with VMware
        Compatibility Guide (VCG). This class attribute was added in vSphere API
        7.0.2.1.

        """
        FLAG_AS_INCOMPATIBLE = None
        """
        Specifying this override for a storage device would flag the drive as
        non-compliant with VMware Compatibility Guide (VCG). This class attribute
        was added in vSphere API 7.0.2.1.

        """
        SUPPRESS_WARNING = None
        """
        Specifying this override for a storage device would suppress the
        compatibility issues if any. This class attribute was added in vSphere API
        7.0.2.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ComplianceAction` instance.
            """
            Enum.__init__(string)

    ComplianceAction._set_values({
        'MARK_AS_VERIFIED': ComplianceAction('MARK_AS_VERIFIED'),
        'FLAG_AS_INCOMPATIBLE': ComplianceAction('FLAG_AS_INCOMPATIBLE'),
        'SUPPRESS_WARNING': ComplianceAction('SUPPRESS_WARNING'),
    })
    ComplianceAction._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.compliance_status.compliance_action',
        ComplianceAction))


    class Service(Enum):
        """
        The ``ComplianceStatus.Service`` class specifies information about vSphere
        services that have service specific VMware compatibility Guide
        certification. This enumeration was added in vSphere API 8.0.0.1.

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
        'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.compliance_status.service',
        Service))


    class Key(VapiStruct):
        """
        The ``ComplianceStatus.Key`` class specifies information about the storage
        device for which this override must be applied to. This class was added in
        vSphere API 7.0.2.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     model=None,
                     vendor=None,
                     capacity=None,
                     part_number=None,
                     firmware_version=None,
                     driver_name=None,
                     driver_version=None,
                     release=None,
                     validated_features_in_use=None,
                    ):
            """
            :type  model: :class:`str`
            :param model: 
            :type  vendor: :class:`str`
            :param vendor: 
            :type  capacity: :class:`long`
            :param capacity: 
            :type  part_number: :class:`str` or ``None``
            :param part_number: storage device part number. This attribute was added in vSphere API
                7.0.2.1.
                If None the override will be applied to the entries without a part
                number.
            :type  firmware_version: :class:`str` or ``None``
            :param firmware_version: storage device firmware version. This attribute was added in
                vSphere API 7.0.2.1.
                If None the override is applied to the entries with an unknown
                firmware version.
            :type  driver_name: :class:`str` or ``None``
            :param driver_name: Driver name of this storage device if applicable/available. This
                attribute was added in vSphere API 8.0.0.1.
                This attribute will be None if there is no driver associated with
                the device.
            :type  driver_version: :class:`str` or ``None``
            :param driver_version: Driver version of this storage device if applicable/available. This
                attribute was added in vSphere API 8.0.0.1.
                This attribute will be None if there is no driver associated with
                the device.
            :type  release: :class:`str` or ``None``
            :param release: vSphere release that an override must be applied to. This attribute
                was added in vSphere API 7.0.2.1.
                If this attribute is unset,
                :class:`com.vmware.vapi.std.errors_client.InvalidArgument` is
                thrown. The field is left optional to support wildcard matching in
                a future release.
            :type  validated_features_in_use: (:class:`dict` of :class:`ComplianceStatus.Service` and :class:`set` of :class:`str`) or ``None``
            :param validated_features_in_use: Validated features for which this override applies If a service is
                specified but no specific features are included, the device is
                taken to be in use by the service. This attribute was added in
                vSphere API 8.0.0.1.
                If this attribute is None this is taken to mean that the device is
                active for the vSAN service (and no specific features). This is
                done in order to support 7.0 U3 clients which do not set this
                field. Subset of validated features for which we provide
                certification - for example RDMA, not IPV6 Note that this list
                represents the features in actual current use, which could include
                features for which the device is not certified
            """
            self.model = model
            self.vendor = vendor
            self.capacity = capacity
            self.part_number = part_number
            self.firmware_version = firmware_version
            self.driver_name = driver_name
            self.driver_version = driver_version
            self.release = release
            self.validated_features_in_use = validated_features_in_use
            VapiStruct.__init__(self)


    Key._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.compliance_status.key', {
            'model': type.StringType(),
            'vendor': type.StringType(),
            'capacity': type.IntegerType(),
            'part_number': type.OptionalType(type.StringType()),
            'firmware_version': type.OptionalType(type.StringType()),
            'driver_name': type.OptionalType(type.StringType()),
            'driver_version': type.OptionalType(type.StringType()),
            'release': type.OptionalType(type.StringType()),
            'validated_features_in_use': type.OptionalType(type.MapType(type.ReferenceType(__name__, 'ComplianceStatus.Service'), type.SetType(type.StringType()))),
        },
        Key,
        False,
        None))


    class ReclassificationSpec(VapiStruct):
        """
        The ``ComplianceStatus.ReclassificationSpec`` class contains information
        about the storage device and the corresponding override that must be
        applied to the specified device. Note: This data structure is specifically
        limited to a 'Key'/'Value' pair to model smaller changes to the larger
        overall set of overrides applicable to a given storage device. This class
        was added in vSphere API 7.0.2.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     key=None,
                     override=None,
                    ):
            """
            :type  key: :class:`ComplianceStatus.Key`
            :param key: Information about the storage device for which this override must
                be applied to. This attribute was added in vSphere API 7.0.2.1.
            :type  override: :class:`ComplianceStatus.ComplianceAction` or ``None``
            :param override: Compliance status override for the stroage device. This attribute
                was added in vSphere API 7.0.2.1.
                If this attribute is None any existing compliance override for the
                specified device will be reset.
            """
            self.key = key
            self.override = override
            VapiStruct.__init__(self)


    ReclassificationSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.compliance_status.reclassification_spec', {
            'key': type.ReferenceType(__name__, 'ComplianceStatus.Key'),
            'override': type.OptionalType(type.ReferenceType(__name__, 'ComplianceStatus.ComplianceAction')),
        },
        ReclassificationSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``ComplianceStatus.UpdateSpec`` class describes the updates to be made
        to the compatibility overrides for storage devices in a cluster. This class
        was added in vSphere API 7.0.2.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     device_reclassifications=None,
                    ):
            """
            :type  device_reclassifications: :class:`list` of :class:`ComplianceStatus.ReclassificationSpec`
            :param device_reclassifications: List of compatibility overrides to be applied for the storage
                devices in a cluster. This attribute was added in vSphere API
                7.0.2.1.
            """
            self.device_reclassifications = device_reclassifications
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.compliance_status.update_spec', {
            'device_reclassifications': type.ListType(type.ReferenceType(__name__, 'ComplianceStatus.ReclassificationSpec')),
        },
        UpdateSpec,
        False,
        None))




    def update_task(self,
               cluster,
               update_spec,
               ):
        """
        Updates the Compliance staus overrides for storage devices in a
        cluster. This method also updates the existing
        :class:`com.vmware.esx.settings.clusters.software.reports_client.CheckResult`
        if any, based on the device reclassification specified in
        :class:`ComplianceStatus.UpdateSpec` The storage device categorization
        based on the compliance status from the last check result will remain
        the same until a
        :func:`com.vmware.esx.settings.clusters.software.reports_client.HardwareCompatibility.check`
        method is invoked. This method was added in vSphere API 7.0.2.1.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  update_spec: :class:`ComplianceStatus.UpdateSpec`
        :param update_spec: Specification for updating the compliance status overrides for
            storage devices in a cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is an unknown error. The accompanying error message will
            give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if there is no cluster associated with the ``cluster``
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if one of the values in the update specification is invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        """
        task_id = self._invoke('update$task',
                                {
                                'cluster': cluster,
                                'update_spec': update_spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.VoidType())
        return task_instance
class VcgEntries(VapiInterface):
    """
    This class provides methods to manage VMware Compatibility Guide (VCG)
    product overrides for storage devices in a cluster. This class was added in
    vSphere API 7.0.2.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.vcg_entries'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _VcgEntriesStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'update_task': 'update$task'})

    class Key(VapiStruct):
        """
        The ``VcgEntries.Key`` class specifies information about the storage device
        for which this override must be applied to. This class was added in vSphere
        API 7.0.2.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     model=None,
                     vendor=None,
                     capacity=None,
                     part_number=None,
                     firmware_version=None,
                    ):
            """
            :type  model: :class:`str`
            :param model: 
            :type  vendor: :class:`str`
            :param vendor: 
            :type  capacity: :class:`long`
            :param capacity: 
            :type  part_number: :class:`str` or ``None``
            :param part_number: storage device part number. This attribute was added in vSphere API
                7.0.2.1.
                If None the override will be applied to the entries without a part
                number.
            :type  firmware_version: :class:`str` or ``None``
            :param firmware_version: storage device firmware version. This attribute was added in
                vSphere API 7.0.2.1.
                If None the override is applied to all firmware versions.
            """
            self.model = model
            self.vendor = vendor
            self.capacity = capacity
            self.part_number = part_number
            self.firmware_version = firmware_version
            VapiStruct.__init__(self)


    Key._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.vcg_entries.key', {
            'model': type.StringType(),
            'vendor': type.StringType(),
            'capacity': type.IntegerType(),
            'part_number': type.OptionalType(type.StringType()),
            'firmware_version': type.OptionalType(type.StringType()),
        },
        Key,
        False,
        None))


    class ProductSelectionSpec(VapiStruct):
        """
        The ``VcgEntries.ProductSelectionSpec`` class contains information about
        the storage device and the corresponding VMware Compatibility Guide (VCG)
        product override that must be applied to the specified device. This class
        was added in vSphere API 7.0.2.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     key=None,
                     vcg_product=None,
                    ):
            """
            :type  key: :class:`VcgEntries.Key`
            :param key: Information about the storage device for which this override must
                be applied to. This attribute was added in vSphere API 7.0.2.1.
            :type  vcg_product: :class:`str` or ``None``
            :param vcg_product: VMware Compatibility Guide (VCG) product selection that must be
                applied to the specified storage device. This attribute was added
                in vSphere API 7.0.2.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.vcg_product``. When methods return a
                value of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.esx.settings.vcg_product``.
                if None any existing vcg selection for the storage device will be
                removed
            """
            self.key = key
            self.vcg_product = vcg_product
            VapiStruct.__init__(self)


    ProductSelectionSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.vcg_entries.product_selection_spec', {
            'key': type.ReferenceType(__name__, 'VcgEntries.Key'),
            'vcg_product': type.OptionalType(type.IdType()),
        },
        ProductSelectionSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``VcgEntries.UpdateSpec`` class desribes the updates to be made to the
        compatibility overrides for storage devices in a cluster. This class was
        added in vSphere API 7.0.2.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     product_selections=None,
                    ):
            """
            :type  product_selections: :class:`list` of :class:`VcgEntries.ProductSelectionSpec`
            :param product_selections: List of VMware Compatibility Guide (VCG) overrides to be applied
                for the storage devices in a cluster. This attribute was added in
                vSphere API 7.0.2.1.
            """
            self.product_selections = product_selections
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.vcg_entries.update_spec', {
            'product_selections': type.ListType(type.ReferenceType(__name__, 'VcgEntries.ProductSelectionSpec')),
        },
        UpdateSpec,
        False,
        None))




    def update_task(self,
               cluster,
               update_spec,
               ):
        """
        Updates the storage device VMware Compatibility Guide (VCG) product
        overrides for a cluster. This method also updates the existing
        :class:`com.vmware.esx.settings.clusters.software.reports_client.CheckResult`
        if any, based on the additional information provided by the vcg product
        overrides for the devices. The storage device categorization based on
        the compliance status from the last check result will remain the same
        until a
        :func:`com.vmware.esx.settings.clusters.software.reports_client.HardwareCompatibility.check`
        method is invoked. This method was added in vSphere API 7.0.2.1.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  update_spec: :class:`VcgEntries.UpdateSpec`
        :param update_spec: Specification for updating the compatibility overrides for the
            cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is an unknown error. The accompanying error message will
            give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if there is no cluster associated with the ``cluster``
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if one of the values in the update specification is invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        """
        task_id = self._invoke('update$task',
                                {
                                'cluster': cluster,
                                'update_spec': update_spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.VoidType())
        return task_instance
class _ComplianceStatusStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'update_spec': type.ReferenceType(__name__, 'ComplianceStatus.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/esx/settings/clusters/{cluster}/software/reports/hardware-compatibility/storage-device-overrides/compliance-status',
            request_body_parameter='update_spec',
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
            'update$task': {
                'input_type': update_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
        }
        rest_metadata = {
            'update': update_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.compliance_status',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _VcgEntriesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'update_spec': type.ReferenceType(__name__, 'VcgEntries.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/esx/settings/clusters/{cluster}/software/reports/hardware-compatibility/storage-device-overrides/vcg-entries',
            request_body_parameter='update_spec',
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
            'update$task': {
                'input_type': update_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
        }
        rest_metadata = {
            'update': update_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.clusters.software.reports.hardware_compatibility.storage_device_overrides.vcg_entries',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'ComplianceStatus': ComplianceStatus,
        'VcgEntries': VcgEntries,
    }

