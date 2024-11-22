# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.snapservice.clusters.virtual_machines.
#---------------------------------------------------------------------------

"""
The ``com.vmware.snapservice.clusters.virtual_machines_client`` module provides
classes for managing virtual machines in a vSAN cluster.

"""

__author__ = 'VMware, Inc.'
__docformat__ = 'restructuredtext en'

import sys
from warnings import warn

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


class Snapshots(VapiInterface):
    """
    The ``Snapshots`` class provides methods to manage snapshots for a
    protection group.
    """

    _VAPI_SERVICE_ID = 'com.vmware.snapservice.clusters.virtual_machines.snapshots'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SnapshotsStub)
        self._VAPI_OPERATION_IDS = {}

    class Type(Enum):
        """
        The ``Snapshots.Type`` enumeration contains valid snapshot types.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        SCHEDULED = None
        """
        Indicates that a snapshot was taken as part of a periodic schedule.

        """
        ONE_TIME = None
        """
        Indicates that the snapshot was taken as a one time operation triggered by
        the user.

        """
        SYSTEM_CREATED = None
        """
        Indicates that the snapshot was taken by the system

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Type` instance.
            """
            Enum.__init__(string)

    Type._set_values({
        'SCHEDULED': Type('SCHEDULED'),
        'ONE_TIME': Type('ONE_TIME'),
        'SYSTEM_CREATED': Type('SYSTEM_CREATED'),
    })
    Type._set_binding_type(type.EnumType(
        'com.vmware.snapservice.clusters.virtual_machines.snapshots.type',
        Type))


    class FilterSpec(VapiStruct):
        """
        The ``Snapshots.FilterSpec`` class contains attributes used to filter the
        results when listing snapshots for a protection group. See
        :func:`Snapshots.list`. When multiple filters are specified, it operates as
        an AND operation. The snapshots returned will match all the specified
        filters.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     expires_after=None,
                     expires_before=None,
                     created_after=None,
                     created_before=None,
                     snapshots=None,
                     names=None,
                     snapshot_type=None,
                    ):
            """
            :type  expires_after: :class:`datetime.datetime` or ``None``
            :param expires_after: Minimum expiration time for the snapshots that must match the
                filter.
                If None snapshots with any expiration time match the filter.
            :type  expires_before: :class:`datetime.datetime` or ``None``
            :param expires_before: Maximum expiration time for the snapshots that must match the
                filter.
                If None snapshots with any expiration time match the filter.
            :type  created_after: :class:`datetime.datetime` or ``None``
            :param created_after: Minimum creation date for the snapshots that must match the filter.
                If None snapshots with any creation time match the filter.
            :type  created_before: :class:`datetime.datetime` or ``None``
            :param created_before: Maximum creation date for the snapshots that must match the filter.
                If None snapshots with any creation time match the filter.
            :type  snapshots: :class:`set` of :class:`str` or ``None``
            :param snapshots: Identifiers of the snapshots that must match the filter.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.snapservice.vm.snapshot``. When methods return a value
                of this class as a return value, the attribute will contain
                identifiers for the resource type:
                ``com.vmware.snapservice.vm.snapshot``.
                If None snapshots with any identifier match the filter.
            :type  names: :class:`set` of :class:`str` or ``None``
            :param names: Names of the snapshots that must match the filter.
                If None snapshots with any name match the filter.
            :type  snapshot_type: :class:`Snapshots.Type` or ``None``
            :param snapshot_type: Snapshot type that must match the filter.
                If None snapshots with any type match the filter.
            """
            self.expires_after = expires_after
            self.expires_before = expires_before
            self.created_after = created_after
            self.created_before = created_before
            self.snapshots = snapshots
            self.names = names
            self.snapshot_type = snapshot_type
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.virtual_machines.snapshots.filter_spec', {
            'expires_after': type.OptionalType(type.DateTimeType()),
            'expires_before': type.OptionalType(type.DateTimeType()),
            'created_after': type.OptionalType(type.DateTimeType()),
            'created_before': type.OptionalType(type.DateTimeType()),
            'snapshots': type.OptionalType(type.SetType(type.IdType())),
            'names': type.OptionalType(type.SetType(type.StringType())),
            'snapshot_type': type.OptionalType(type.ReferenceType(__name__, 'Snapshots.Type')),
        },
        FilterSpec,
        False,
        None))


    class Info(VapiStruct):
        """
        Information regarding a virtual machine snapshot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     name=None,
                     snapshot_type=None,
                     created_at=None,
                     expires_at=None,
                     vm=None,
                     pg=None,
                     disk_snapshots=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: Snapshot name. For a snapshot triggered by a periodic schedule,
                name will be system generated.
            :type  snapshot_type: :class:`Snapshots.Type`
            :param snapshot_type: Snapshot type.
            :type  created_at: :class:`datetime.datetime`
            :param created_at: Creation time.
            :type  expires_at: :class:`datetime.datetime` or ``None``
            :param expires_at: Expiry time.
                None if there is no expiry for the snapshot.
            :type  vm: :class:`str`
            :param vm: Identifier of the virtual machine for which the snapshot was taken.
                
                TODO: Remove this once the VM snapshot List/Get is implemented, We
                do not need this since the query is already being performed on a
                specific VM.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``VirtualMachine``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``VirtualMachine``.
            :type  pg: :class:`str` or ``None``
            :param pg: Identifier of the protection group for which this snapshot was
                taken.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.snapservice.protection_group``. When methods return a
                value of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.snapservice.protection_group``.
                None if the snapshot was not taken as part of a protection group.
            :type  disk_snapshots: :class:`list` of :class:`com.vmware.snapservice.clusters.virtual_machines.disks_client.Snapshots.Info`
            :param disk_snapshots: List of virtual machine disk snapshots that were taken for this
                snapshot instance.
            """
            self.name = name
            self.snapshot_type = snapshot_type
            self.created_at = created_at
            self.expires_at = expires_at
            self.vm = vm
            self.pg = pg
            self.disk_snapshots = disk_snapshots
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.virtual_machines.snapshots.info', {
            'name': type.StringType(),
            'snapshot_type': type.ReferenceType(__name__, 'Snapshots.Type'),
            'created_at': type.DateTimeType(),
            'expires_at': type.OptionalType(type.DateTimeType()),
            'vm': type.IdType(resource_types='VirtualMachine'),
            'pg': type.OptionalType(type.IdType()),
            'disk_snapshots': type.ListType(type.ReferenceType('com.vmware.snapservice.clusters.virtual_machines.disks_client', 'Snapshots.Info')),
        },
        Info,
        False,
        None))


    class ListItem(VapiStruct):
        """
        The ``Snapshots.ListItem`` class contains information about a protection
        group returned by :func:`Snapshots.list` method

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     snapshot=None,
                     info=None,
                    ):
            """
            :type  snapshot: :class:`str`
            :param snapshot: Identifier of the virtual machine snapshot.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.snapservice.vm.snapshot``. When methods return a value
                of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.snapservice.vm.snapshot``.
            :type  info: :class:`Snapshots.Info`
            :param info: Information about the virtual machine snapshot.
            """
            self.snapshot = snapshot
            self.info = info
            VapiStruct.__init__(self)


    ListItem._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.virtual_machines.snapshots.list_item', {
            'snapshot': type.IdType(resource_types='com.vmware.snapservice.vm.snapshot'),
            'info': type.ReferenceType(__name__, 'Snapshots.Info'),
        },
        ListItem,
        False,
        None))


    class ListResult(VapiStruct):
        """
        The ``Snapshots.ListResult`` class represents the result of
        :func:`Snapshots.list` method.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     items=None,
                    ):
            """
            :type  items: :class:`list` of :class:`Snapshots.ListItem`
            :param items: List of items
            """
            self.items = items
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.virtual_machines.snapshots.list_result', {
            'items': type.ListType(type.ReferenceType(__name__, 'Snapshots.ListItem')),
        },
        ListResult,
        False,
        None))



    def list(self,
             cluster,
             vm,
             filter=None,
             ):
        """
        List the snapshots for the given virtual machine.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  filter: :class:`Snapshots.FilterSpec` or ``None``
        :param filter: Specification of matching snapshots for which information should be
            returned.
            If None, the behavior is equivalent to a
            :class:`Snapshots.FilterSpec` with all attributes None which means
            all virtual machine snapshots match the filter.
        :rtype: :class:`Snapshots.ListResult`
        :return: Information about the snapshots matching the
            :class:`Snapshots.FilterSpec` for the specified virtual machine.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` or no or no
            virtual machine associated with ``vm``in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If validation of the ``filter`` fails.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the caller is not authorized to perform the operation.
        """
        return self._invoke('list',
                            {
                            'cluster': cluster,
                            'vm': vm,
                            'filter': filter,
                            })

    def get(self,
            cluster,
            vm,
            snapshot,
            ):
        """
        Get the detailed information regarding the specified virtual machine
        snapshot.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  snapshot: :class:`str`
        :param snapshot: Identifier of the virtual machine snapshot.
            The parameter must be an identifier for the resource type:
            ``com.vmware.snapservice.vm.snapshot``.
        :rtype: :class:`Snapshots.Info`
        :return: Information about the virtual mahcine snapshot.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If no cluster associated with ``cluster`` or no virtual machine
            associated with ``vm`` or no snapshot associated with ``snapshot``
            is found in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the caller is not authorized to perform the operation.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            'vm': vm,
                            'snapshot': snapshot,
                            })
class _SnapshotsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'vm': type.IdType(resource_types='VirtualMachine'),
            'filter': type.OptionalType(type.ReferenceType(__name__, 'Snapshots.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/snapservice/clusters/{cluster}/virtual-machines/{vm}/snapshots',
            path_variables={
                'cluster': 'cluster',
                'vm': 'vm',
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

        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'vm': type.IdType(resource_types='VirtualMachine'),
            'snapshot': type.IdType(resource_types='com.vmware.snapservice.vm.snapshot'),
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
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/snapservice/clusters/{cluster}/virtual-machines/{vm}/snapshots/{snapshot}',
            path_variables={
                'cluster': 'cluster',
                'vm': 'vm',
                'snapshot': 'snapshot',
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
            'list': {
                'input_type': list_input_type,
                'output_type': type.ReferenceType(__name__, 'Snapshots.ListResult'),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Snapshots.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.snapservice.clusters.virtual_machines.snapshots',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Snapshots': Snapshots,
        'disks': 'com.vmware.snapservice.clusters.virtual_machines.disks_client.StubFactory',
    }

