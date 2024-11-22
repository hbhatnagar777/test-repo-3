# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.snapservice.clusters.protection_groups.
#---------------------------------------------------------------------------

"""
The ``com.vmware.snapservice.clusters.protection_groups_client`` module
provides classes for managing protection groups in a vSAN cluster.

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


class Snapshots(VapiInterface):
    """
    The ``Snapshots`` class provides methods to manage snapshots for a
    protection group.
    """

    _VAPI_SERVICE_ID = 'com.vmware.snapservice.clusters.protection_groups.snapshots'
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
        self._VAPI_OPERATION_IDS.update({'create_task': 'create$task'})

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
        'com.vmware.snapservice.clusters.protection_groups.snapshots.type',
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
                ``com.vmware.snapservice.protection_group.snapshot``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.snapservice.protection_group.snapshot``.
                If None snapshots with any identifier match the filter.
            :type  names: :class:`set` of :class:`str` or ``None``
            :param names: Names of the snapshots that must match the filter.
                If None snapshots with any name match the filter.
            """
            self.expires_after = expires_after
            self.expires_before = expires_before
            self.created_after = created_after
            self.created_before = created_before
            self.snapshots = snapshots
            self.names = names
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.protection_groups.snapshots.filter_spec', {
            'expires_after': type.OptionalType(type.DateTimeType()),
            'expires_before': type.OptionalType(type.DateTimeType()),
            'created_after': type.OptionalType(type.DateTimeType()),
            'created_before': type.OptionalType(type.DateTimeType()),
            'snapshots': type.OptionalType(type.SetType(type.IdType())),
            'names': type.OptionalType(type.SetType(type.StringType())),
        },
        FilterSpec,
        False,
        None))


    class VmSnapshotSummary(VapiStruct):
        """
        The ``Snapshots.VmSnapshotSummary`` class contains commonly used
        information about a virtual machine snapshot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     snapshot=None,
                     name=None,
                     created_at=None,
                     expires_at=None,
                     vm=None,
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
            :type  name: :class:`str`
            :param name: Snapshot name. For a snapshot triggered by a periodic scchedule,
                name will be system generated.
            :type  created_at: :class:`datetime.datetime`
            :param created_at: Creation time.
            :type  expires_at: :class:`datetime.datetime` or ``None``
            :param expires_at: Expiry time.
                None if there is no expiry for the snapshot.
            :type  vm: :class:`str`
            :param vm: Identifier of the virtual machine for which the snapshot was taken.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``VirtualMachine``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``VirtualMachine``.
            """
            self.snapshot = snapshot
            self.name = name
            self.created_at = created_at
            self.expires_at = expires_at
            self.vm = vm
            VapiStruct.__init__(self)


    VmSnapshotSummary._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.protection_groups.snapshots.vm_snapshot_summary', {
            'snapshot': type.IdType(resource_types='com.vmware.snapservice.vm.snapshot'),
            'name': type.StringType(),
            'created_at': type.DateTimeType(),
            'expires_at': type.OptionalType(type.DateTimeType()),
            'vm': type.IdType(resource_types='VirtualMachine'),
        },
        VmSnapshotSummary,
        False,
        None))


    class Info(VapiStruct):
        """
        Information regarding a protection group snapshot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     name=None,
                     snapshot_type=None,
                     start_time=None,
                     end_time=None,
                     expires_at=None,
                     pg=None,
                     vm_snapshots=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: Snapshot name. For a snapshot triggered by a periodic scchedule,
                name will be system generated.
            :type  snapshot_type: :class:`Snapshots.Type`
            :param snapshot_type: Snapshot type.
            :type  start_time: :class:`datetime.datetime`
            :param start_time: Time at which the protection group snapshot operation started.
            :type  end_time: :class:`datetime.datetime`
            :param end_time: Time at which the protection group snapshot operation completed.
            :type  expires_at: :class:`datetime.datetime` or ``None``
            :param expires_at: Expiry time.
                None if there is no expiry for the snapshot.
            :type  pg: :class:`str`
            :param pg: Identifier of the protection group for which the snapshot was
                taken.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.snapservice.protection_group``. When methods return a
                value of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.snapservice.protection_group``.
            :type  vm_snapshots: :class:`list` of :class:`Snapshots.VmSnapshotSummary`
            :param vm_snapshots: List of virtual machine snapshots that were taken for this snapshot
                instance.
            """
            self.name = name
            self.snapshot_type = snapshot_type
            self.start_time = start_time
            self.end_time = end_time
            self.expires_at = expires_at
            self.pg = pg
            self.vm_snapshots = vm_snapshots
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.protection_groups.snapshots.info', {
            'name': type.StringType(),
            'snapshot_type': type.ReferenceType(__name__, 'Snapshots.Type'),
            'start_time': type.DateTimeType(),
            'end_time': type.DateTimeType(),
            'expires_at': type.OptionalType(type.DateTimeType()),
            'pg': type.IdType(resource_types='com.vmware.snapservice.protection_group'),
            'vm_snapshots': type.ListType(type.ReferenceType(__name__, 'Snapshots.VmSnapshotSummary')),
        },
        Info,
        False,
        None))


    class ListItem(VapiStruct):
        """
        The ``Snapshots.ListItem`` class contains information about a protection
        group snapshot returned by :func:`Snapshots.list` method

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
            :param snapshot: Identifier of the protection group snapshot.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.snapservice.protection_group.snapshot``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.snapservice.protection_group.snapshot``.
            :type  info: :class:`Snapshots.Info`
            :param info: Information about the protection group snapshot.
            """
            self.snapshot = snapshot
            self.info = info
            VapiStruct.__init__(self)


    ListItem._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.protection_groups.snapshots.list_item', {
            'snapshot': type.IdType(resource_types='com.vmware.snapservice.protection_group.snapshot'),
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
                     snapshots=None,
                    ):
            """
            :type  snapshots: :class:`list` of :class:`Snapshots.ListItem`
            :param snapshots: List of items.
            """
            self.snapshots = snapshots
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.protection_groups.snapshots.list_result', {
            'snapshots': type.ListType(type.ReferenceType(__name__, 'Snapshots.ListItem')),
        },
        ListResult,
        False,
        None))


    class CreateResult(VapiStruct):
        """
        The ``Snapshots.CreateResult`` class contains information regarding the
        operation to create protection group snapshot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'snapshot_type',
                {
                    'SCHEDULED' : [('policy', False)],
                    'ONE_TIME' : [],
                    'SYSTEM_CREATED' : [],
                }
            ),
        ]



        def __init__(self,
                     snapshot_type=None,
                     total_vms=None,
                     successful_vms=None,
                     failed_vms=None,
                     policy=None,
                     snapshot=None,
                    ):
            """
            :type  snapshot_type: :class:`Snapshots.Type`
            :param snapshot_type: Type of the snapshot.
            :type  total_vms: :class:`long`
            :param total_vms: Total number of virtual machines considered for the snapshot
                operation.
            :type  successful_vms: :class:`long`
            :param successful_vms: Number of virtual machines that were successfully snapshotted.
            :type  failed_vms: :class:`long`
            :param failed_vms: Number of virtual machines the system failed to create snapshots
                for.
            :type  policy: :class:`str` or ``None``
            :param policy: Name of the snapshot policy this snapshot corresponds to.
                None if the snapshot was not a scheduled snapshot.
            :type  snapshot: :class:`str`
            :param snapshot: Identifier of the protection group snapshot.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.snapservice.protection_group.snapshot``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.snapservice.protection_group.snapshot``.
            """
            self.snapshot_type = snapshot_type
            self.total_vms = total_vms
            self.successful_vms = successful_vms
            self.failed_vms = failed_vms
            self.policy = policy
            self.snapshot = snapshot
            VapiStruct.__init__(self)


    CreateResult._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.protection_groups.snapshots.create_result', {
            'snapshot_type': type.ReferenceType(__name__, 'Snapshots.Type'),
            'total_vms': type.IntegerType(),
            'successful_vms': type.IntegerType(),
            'failed_vms': type.IntegerType(),
            'policy': type.OptionalType(type.StringType()),
            'snapshot': type.IdType(resource_types='com.vmware.snapservice.protection_group.snapshot'),
        },
        CreateResult,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``Snapshots.CreateSpec`` class contains attributes that describe
        specification for creating a manual protection group snapshot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     name=None,
                     retention=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: Name of the protection group snapshot.
            :type  retention: :class:`com.vmware.snapservice_client.RetentionPeriod` or ``None``
            :param retention: Retention period for the snapshot. Indicates the duration for which
                this snapshot must be retained in the system.
                if None the snapshot will be retained till the life of the cluster
                that the protection group belongs to or the life of the protection
                group itself.
            """
            self.name = name
            self.retention = retention
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.protection_groups.snapshots.create_spec', {
            'name': type.StringType(),
            'retention': type.OptionalType(type.ReferenceType('com.vmware.snapservice_client', 'RetentionPeriod')),
        },
        CreateSpec,
        False,
        None))




    def create_task(self,
               cluster,
               pg,
               spec,
               ):
        """
        Create a snapshot for the given protection group.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  pg: :class:`str`
        :param pg: Identifier of the protection group.
            The parameter must be an identifier for the resource type:
            ``com.vmware.snapservice.protection_group``.
        :type  spec: :class:`Snapshots.CreateSpec`
        :param spec: specification for the protection group snapshot.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If there is another operation in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` or no protection
            group associated with ``pg`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If validation of the ``spec`` fails.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the caller is not authorized to perform the operation.
        """
        task_id = self._invoke('create$task',
                                {
                                'cluster': cluster,
                                'pg': pg,
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Snapshots.CreateResult'))
        return task_instance

    def list(self,
             cluster,
             pg,
             filter=None,
             ):
        """
        List the snapshots for the given protection group.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  pg: :class:`str`
        :param pg: Identifier of the protection group.
            The parameter must be an identifier for the resource type:
            ``com.vmware.snapservice.protection_group``.
        :type  filter: :class:`Snapshots.FilterSpec` or ``None``
        :param filter: Specification of matching snapshots for which information should be
            returned.
            If None, the behavior is equivalent to a
            :class:`Snapshots.FilterSpec` with all attributes None which means
            all protection group snapshots match the filter.
            :class:`Snapshots.FilterSpec` for the specified protection group.
        :rtype: :class:`Snapshots.ListResult`
        :return: Information about the snapshots matching the
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` or no or no
            protection group associated with ``pg``in the system.
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
                            'pg': pg,
                            'filter': filter,
                            })

    def get(self,
            cluster,
            pg,
            snapshot,
            ):
        """
        Get the detailed information regarding the specified protection group
        snapshot.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  pg: :class:`str`
        :param pg: Identifier of the protection group.
            The parameter must be an identifier for the resource type:
            ``com.vmware.snapservice.protection_group``.
        :type  snapshot: :class:`str`
        :param snapshot: Identifier of the protection group snapshot.
            The parameter must be an identifier for the resource type:
            ``com.vmware.snapservice.protection_group.snapshot``.
        :rtype: :class:`Snapshots.Info`
        :return: Information about the specified protection group snapshot.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If no cluster associated with ``cluster`` or no protection group
            associated with ``pg`` or no snapshot associated with ``snapshot``
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
                            'pg': pg,
                            'snapshot': snapshot,
                            })

    def delete(self,
               cluster,
               pg,
               snapshot,
               ):
        """
        Delete the specified protection group snapshot.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  pg: :class:`str`
        :param pg: Identifier of the protection group.
            The parameter must be an identifier for the resource type:
            ``com.vmware.snapservice.protection_group``.
        :type  snapshot: :class:`str`
        :param snapshot: Identifier of the protection group snapshot.
            The parameter must be an identifier for the resource type:
            ``com.vmware.snapservice.protection_group.snapshot``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If no cluster associated with ``cluster`` or no protection group
            associated with ``pg`` or no snapshot associated with ``snapshot``
            is found in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the caller is not authorized to perform the operation.
        """
        return self._invoke('delete',
                            {
                            'cluster': cluster,
                            'pg': pg,
                            'snapshot': snapshot,
                            })
class _SnapshotsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'pg': type.IdType(resource_types='com.vmware.snapservice.protection_group'),
            'spec': type.ReferenceType(__name__, 'Snapshots.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
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
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/snapservice/clusters/{cluster}/protection-groups/{pg}/snapshots',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
                'pg': 'pg',
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

        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'pg': type.IdType(resource_types='com.vmware.snapservice.protection_group'),
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
            url_template='/snapservice/clusters/{cluster}/protection-groups/{pg}/snapshots',
            path_variables={
                'cluster': 'cluster',
                'pg': 'pg',
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
            'pg': type.IdType(resource_types='com.vmware.snapservice.protection_group'),
            'snapshot': type.IdType(resource_types='com.vmware.snapservice.protection_group.snapshot'),
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
            url_template='/snapservice/clusters/{cluster}/protection-groups/{pg}/snapshots/{snapshot}',
            path_variables={
                'cluster': 'cluster',
                'pg': 'pg',
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

        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'pg': type.IdType(resource_types='com.vmware.snapservice.protection_group'),
            'snapshot': type.IdType(resource_types='com.vmware.snapservice.protection_group.snapshot'),
        })
        delete_error_dict = {
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
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/snapservice/clusters/{cluster}/protection-groups/{pg}/snapshots/{snapshot}',
            path_variables={
                'cluster': 'cluster',
                'pg': 'pg',
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
            'create$task': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
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
            'delete': {
                'input_type': delete_input_type,
                'output_type': type.VoidType(),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': delete_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'create': create_rest_metadata,
            'list': list_rest_metadata,
            'get': get_rest_metadata,
            'delete': delete_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.snapservice.clusters.protection_groups.snapshots',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Snapshots': Snapshots,
    }

