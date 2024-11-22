# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.snapservice.
#---------------------------------------------------------------------------

"""
The ``com.vmware.snapservice_client`` module provides classes for configuring
and managing vSAN protection groups and snapshots

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

class TimeUnit(Enum):
    """
    The ``TimeUnit`` class contains the supported values for how often
    snapshots are taken.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    MINUTE = None
    """
    Minutes.

    """
    HOUR = None
    """
    Hours.

    """
    DAY = None
    """
    Day.

    """
    WEEK = None
    """
    Weeks.

    """
    MONTH = None
    """
    Months.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`TimeUnit` instance.
        """
        Enum.__init__(string)

TimeUnit._set_values({
    'MINUTE': TimeUnit('MINUTE'),
    'HOUR': TimeUnit('HOUR'),
    'DAY': TimeUnit('DAY'),
    'WEEK': TimeUnit('WEEK'),
    'MONTH': TimeUnit('MONTH'),
})
TimeUnit._set_binding_type(type.EnumType(
    'com.vmware.snapservice.time_unit',
    TimeUnit))



class ProtectionGroupStatus(Enum):
    """
    The ``ProtectionGroupStatus`` class contains the different states for the
    protection group. Does the status need to be specifically for snapshots?
    Are there other operations we will support for the Protection Group?

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    ACTIVE = None
    """
    Active

    """
    PAUSED = None
    """
    Paused

    """
    MARKED_FOR_DELETE = None
    """
    Marked for delete, 
    
    Indicates that the PG is soft deleted but has some PG snapshots and VM
    snapshots which are not yet expired.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`ProtectionGroupStatus` instance.
        """
        Enum.__init__(string)

ProtectionGroupStatus._set_values({
    'ACTIVE': ProtectionGroupStatus('ACTIVE'),
    'PAUSED': ProtectionGroupStatus('PAUSED'),
    'MARKED_FOR_DELETE': ProtectionGroupStatus('MARKED_FOR_DELETE'),
})
ProtectionGroupStatus._set_binding_type(type.EnumType(
    'com.vmware.snapservice.protection_group_status',
    ProtectionGroupStatus))




class TargetEntities(VapiStruct):
    """
    The ``TargetEntities`` class contains attributes specifying the target
    entities to be protected. The initial release will only support virtual
    machines.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 vm_name_patterns=None,
                 vms=None,
                ):
        """
        :type  vm_name_patterns: :class:`list` of :class:`str` or ``None``
        :param vm_name_patterns: One or more match patterns for virtual machines to be protected. 
            
            Uses standard POSIX Shell globbing pattern. See also, the POSIX
            Shell language:
            http://pubs.opengroup.org/onlinepubs/009695399/utilities/xcu_chap02.html#tag_02_13_01
            If None, :attr:`TargetEntities.vms` must be specified.
        :type  vms: :class:`set` of :class:`str` or ``None``
        :param vms: List of virtual machines to be protected.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``VirtualMachine``. When methods return a value of this class as a
            return value, the attribute will contain identifiers for the
            resource type: ``VirtualMachine``.
            If None, the virtual machines to be protected will be determined
            based on the :attr:`TargetEntities.vm_name_patterns`.
        """
        self.vm_name_patterns = vm_name_patterns
        self.vms = vms
        VapiStruct.__init__(self)


TargetEntities._set_binding_type(type.StructType(
    'com.vmware.snapservice.target_entities', {
        'vm_name_patterns': type.OptionalType(type.ListType(type.StringType())),
        'vms': type.OptionalType(type.SetType(type.IdType())),
    },
    TargetEntities,
    False,
    None))



class SnapshotSchedule(VapiStruct):
    """
    The ``SnapshotSchedule`` class contains attributes that define the
    frequency at which snapshots must be taken.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 unit=None,
                 interval=None,
                ):
        """
        :type  unit: :class:`TimeUnit`
        :param unit: Units for the interval.
        :type  interval: :class:`long`
        :param interval: Interval between each snapshot.
        """
        self.unit = unit
        self.interval = interval
        VapiStruct.__init__(self)


SnapshotSchedule._set_binding_type(type.StructType(
    'com.vmware.snapservice.snapshot_schedule', {
        'unit': type.ReferenceType(__name__, 'TimeUnit'),
        'interval': type.IntegerType(),
    },
    SnapshotSchedule,
    False,
    None))



class RetentionPeriod(VapiStruct):
    """
    The ``RetentionPeriod`` class contains attributes that define the duration
    for which each snapshot must be retained.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 unit=None,
                 duration=None,
                ):
        """
        :type  unit: :class:`TimeUnit`
        :param unit: Units for the retention period
        :type  duration: :class:`long`
        :param duration: Duration for the snapshot to be retained
        """
        self.unit = unit
        self.duration = duration
        VapiStruct.__init__(self)


RetentionPeriod._set_binding_type(type.StructType(
    'com.vmware.snapservice.retention_period', {
        'unit': type.ReferenceType(__name__, 'TimeUnit'),
        'duration': type.IntegerType(),
    },
    RetentionPeriod,
    False,
    None))



class SnapshotPolicy(VapiStruct):
    """
    The ``SnapshotPolicy`` class contains attributes that describe the
    frequency and retention for taking snapshots of the protection targets.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 name=None,
                 schedule=None,
                 retention=None,
                ):
        """
        :type  name: :class:`str`
        :param name: Name for the snapshot policy.
        :type  schedule: :class:`SnapshotSchedule`
        :param schedule: Schedule for the snapshots.
        :type  retention: :class:`RetentionPeriod`
        :param retention: Retention period for the snapshots.
        """
        self.name = name
        self.schedule = schedule
        self.retention = retention
        VapiStruct.__init__(self)


SnapshotPolicy._set_binding_type(type.StructType(
    'com.vmware.snapservice.snapshot_policy', {
        'name': type.StringType(),
        'schedule': type.ReferenceType(__name__, 'SnapshotSchedule'),
        'retention': type.ReferenceType(__name__, 'RetentionPeriod'),
    },
    SnapshotPolicy,
    False,
    None))



class ProtectionGroupSpec(VapiStruct):
    """
    The ``ProtectionGroupSpec`` class contains attributes that describe the
    desired protection group and the snapshot policies associated with it. A
    protection group is a group of entities that vSAN Snapshot Service protects
    together.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 name=None,
                 target_entities=None,
                 snapshot_policies=None,
                 locked=None,
                ):
        """
        :type  name: :class:`str`
        :param name: Name of the protection group.
        :type  target_entities: :class:`TargetEntities`
        :param target_entities: Target entities for the protection.
        :type  snapshot_policies: :class:`list` of :class:`SnapshotPolicy` or ``None``
        :param snapshot_policies: Snapshot policy for the protection targets.
            if None local protection will be skipped.
        :type  locked: :class:`bool` or ``None``
        :param locked: Indicates if the protection group is to be locked. A locked
            protection group cannot be modified or deleted by the user. All
            snapshots associated with the protection group will be secure and
            cannot be deleted. The system will automatically delete these
            snapshots upon expiry based on the retention period.
            if None the protection group will be considered as unlocked.
        """
        self.name = name
        self.target_entities = target_entities
        self.snapshot_policies = snapshot_policies
        self.locked = locked
        VapiStruct.__init__(self)


ProtectionGroupSpec._set_binding_type(type.StructType(
    'com.vmware.snapservice.protection_group_spec', {
        'name': type.StringType(),
        'target_entities': type.ReferenceType(__name__, 'TargetEntities'),
        'snapshot_policies': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'SnapshotPolicy'))),
        'locked': type.OptionalType(type.BooleanType()),
    },
    ProtectionGroupSpec,
    False,
    None))



class ProtectionGroupUpdateSpec(VapiStruct):
    """
    The ``ProtectionGroupUpdateSpec`` class contains attributes that describe
    the desired protection group and the snapshot policies associated with it.
    A protection group is a group of entities that vSAN Snapshot Service
    protects together.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 name=None,
                 target_entities=None,
                 snapshot_policies=None,
                ):
        """
        :type  name: :class:`str` or ``None``
        :param name: Name of the protection group.
            if None, the current proteciton group name will be retained.
        :type  target_entities: :class:`TargetEntities` or ``None``
        :param target_entities: Target entities for the protection. If :class:`set`, this will
            represent all the target entities for the protection group.
            if None, the existing target entities will be retained.
        :type  snapshot_policies: :class:`list` of :class:`SnapshotPolicy` or ``None``
        :param snapshot_policies: Snapshot policy for the protection targets. If :class:`set`, this
            will represent all the snapshot policies for the protection group.
            Any existing policies will be removed, if not specified in the new
            list.
            if None, existing snapshot policies will be retained.
        """
        self.name = name
        self.target_entities = target_entities
        self.snapshot_policies = snapshot_policies
        VapiStruct.__init__(self)


ProtectionGroupUpdateSpec._set_binding_type(type.StructType(
    'com.vmware.snapservice.protection_group_update_spec', {
        'name': type.OptionalType(type.StringType()),
        'target_entities': type.OptionalType(type.ReferenceType(__name__, 'TargetEntities')),
        'snapshot_policies': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'SnapshotPolicy'))),
    },
    ProtectionGroupUpdateSpec,
    False,
    None))



class ProtectionGroupInfo(VapiStruct):
    """
    The ``ProtectionGroupInfo`` class contains attributes that provide detailed
    information regarding the protection group and the snapshot policies
    associated with it.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 name=None,
                 status=None,
                 target_entities=None,
                 snapshot_policies=None,
                 last_snapshot_time=None,
                 oldest_snapshot_time=None,
                 vms=None,
                 snapshots=None,
                 locked=None,
                ):
        """
        :type  name: :class:`str`
        :param name: Name of the protection group.
        :type  status: :class:`ProtectionGroupStatus`
        :param status: Current status of the protection group.
        :type  target_entities: :class:`TargetEntities`
        :param target_entities: User provided target entities that must belong to the protection
            group.
        :type  snapshot_policies: :class:`list` of :class:`SnapshotPolicy`
        :param snapshot_policies: Snapshot policies for the protection targets.
        :type  last_snapshot_time: :class:`datetime.datetime` or ``None``
        :param last_snapshot_time: Time at which the last protection group snapshot was taken.
            is None if there are no snapshots taken for the protection group.
        :type  oldest_snapshot_time: :class:`datetime.datetime` or ``None``
        :param oldest_snapshot_time: Time at which the current oldest protection group snapshot was
            taken.
            is None if there are no snapshots taken for the protection group.
        :type  vms: :class:`set` of :class:`str`
        :param vms: List of virtual machines that belong to the protection group. This
            is a combined list of virtual machines from the dynamic vm name and
            the individual list of virtual machines specified during creation
            of the prtection group.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``VirtualMachine``. When methods return a value of this class as a
            return value, the attribute will contain identifiers for the
            resource type: ``VirtualMachine``.
        :type  snapshots: :class:`set` of :class:`str`
        :param snapshots: List of snapshots taken for the protection group.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``com.vmware.snapservice.protection_group.snapshot``. When methods
            return a value of this class as a return value, the attribute will
            contain identifiers for the resource type:
            ``com.vmware.snapservice.protection_group.snapshot``.
        :type  locked: :class:`bool`
        :param locked: Indicates if the protection group is to be locked. A locked
            protection group cannot be modified or deleted by the user. All
            snapshots associated with the protection group will be secure and
            cannot be deleted. The system will automatically delete these
            snapshots upon expiry based on the retention period
        """
        self.name = name
        self.status = status
        self.target_entities = target_entities
        self.snapshot_policies = snapshot_policies
        self.last_snapshot_time = last_snapshot_time
        self.oldest_snapshot_time = oldest_snapshot_time
        self.vms = vms
        self.snapshots = snapshots
        self.locked = locked
        VapiStruct.__init__(self)


ProtectionGroupInfo._set_binding_type(type.StructType(
    'com.vmware.snapservice.protection_group_info', {
        'name': type.StringType(),
        'status': type.ReferenceType(__name__, 'ProtectionGroupStatus'),
        'target_entities': type.ReferenceType(__name__, 'TargetEntities'),
        'snapshot_policies': type.ListType(type.ReferenceType(__name__, 'SnapshotPolicy')),
        'last_snapshot_time': type.OptionalType(type.DateTimeType()),
        'oldest_snapshot_time': type.OptionalType(type.DateTimeType()),
        'vms': type.SetType(type.IdType()),
        'snapshots': type.SetType(type.IdType()),
        'locked': type.BooleanType(),
    },
    ProtectionGroupInfo,
    False,
    None))



class Tasks(VapiInterface):
    """
    The ``Tasks`` class provides methods for managing the tasks related to long
    running operations.
    """

    _VAPI_SERVICE_ID = 'com.vmware.snapservice.tasks'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _TasksStub)
        self._VAPI_OPERATION_IDS = {}

    class FilterSpec(VapiStruct):
        """
        The ``Tasks.FilterSpec`` class contains attributes used to filter the
        results when listing tasks (see :func:`Tasks.list`). If multiple attributes
        are specified, only tasks matching all of the attributes match the filter. 
        
        Currently at least one of :attr:`Tasks.FilterSpec.tasks` or
        :attr:`Tasks.FilterSpec.services` must be specified and not empty.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     tasks=None,
                     operations=None,
                     services=None,
                     status=None,
                     users=None,
                    ):
            """
            :type  tasks: :class:`set` of :class:`str` or ``None``
            :param tasks: Identifiers of tasks that can match the filter.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.snapservice.task``. When methods return a value of
                this class as a return value, the attribute will contain
                identifiers for the resource type: ``com.vmware.snapservice.task``.
                This attribute may be None if other filters are specified. If None
                or empty, tasks with any identifier will match the filter.
            :type  operations: :class:`set` of :class:`str` or ``None``
            :param operations: Identifiers of operations. Tasks created by these operations match
                the filter (see
                :attr:`com.vmware.snapservice.tasks_client.CommonInfo.operation`). 
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.snapservice.operation``. When methods return a value
                of this class as a return value, the attribute will contain
                identifiers for the resource type:
                ``com.vmware.snapservice.operation``.
                If None or empty, tasks associated with any operation will match
                the filter.
            :type  services: :class:`set` of :class:`str` or ``None``
            :param services: Identifiers of services. Tasks created by operations in these
                services match the filter (see
                :attr:`com.vmware.snapservice.tasks_client.CommonInfo.service`).
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.snapservice.service``. When methods return a value of
                this class as a return value, the attribute will contain
                identifiers for the resource type:
                ``com.vmware.snapservice.service``.
                This attribute may be None if ``tasks`` is specified. If this
                attribute is None or empty, tasks for any service will match the
                filter.
            :type  status: :class:`set` of :class:`com.vmware.snapservice.tasks_client.Status` or ``None``
            :param status: Status that a task must have to match the filter (see
                :attr:`com.vmware.snapservice.tasks_client.CommonInfo.status`).
                If None or empty, tasks with any status match the filter.
            :type  users: :class:`set` of :class:`str` or ``None``
            :param users: Users who must have initiated the operation for the associated task
                to match the filter (see
                :attr:`com.vmware.snapservice.tasks_client.CommonInfo.user`).
                If None or empty, tasks associated with operations initiated by any
                user match the filter.
            """
            self.tasks = tasks
            self.operations = operations
            self.services = services
            self.status = status
            self.users = users
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.snapservice.tasks.filter_spec', {
            'tasks': type.OptionalType(type.SetType(type.IdType())),
            'operations': type.OptionalType(type.SetType(type.IdType())),
            'services': type.OptionalType(type.SetType(type.IdType())),
            'status': type.OptionalType(type.SetType(type.ReferenceType('com.vmware.snapservice.tasks_client', 'Status'))),
            'users': type.OptionalType(type.SetType(type.StringType())),
        },
        FilterSpec,
        False,
        None))


    class ListItem(VapiStruct):
        """
        The ``Tasks.ListItem`` class contains information about a task returned by
        :func:`Tasks.list` method

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     task=None,
                     info=None,
                    ):
            """
            :type  task: :class:`str`
            :param task: Identifier of the task for which this entry belongs to.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.snapservice.task``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.snapservice.task``.
            :type  info: :class:`com.vmware.snapservice.tasks_client.Info`
            :param info: Information regarding the task.
            """
            self.task = task
            self.info = info
            VapiStruct.__init__(self)


    ListItem._set_binding_type(type.StructType(
        'com.vmware.snapservice.tasks.list_item', {
            'task': type.IdType(resource_types='com.vmware.snapservice.task'),
            'info': type.ReferenceType('com.vmware.snapservice.tasks_client', 'Info'),
        },
        ListItem,
        False,
        None))


    class ListResult(VapiStruct):
        """
        The ``Tasks.ListResult`` class represents the result of :func:`Tasks.list`
        method.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     items=None,
                    ):
            """
            :type  items: :class:`list` of :class:`Tasks.ListItem`
            :param items: List of tasks.
            """
            self.items = items
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.snapservice.tasks.list_result', {
            'items': type.ListType(type.ReferenceType(__name__, 'Tasks.ListItem')),
        },
        ListResult,
        False,
        None))



    def list(self,
             filter=None,
             ):
        """
        Returns information about at most 1000 visible (subject to permission
        checks) tasks matching the :class:`Tasks.FilterSpec`.

        :type  filter: :class:`Tasks.FilterSpec` or ``None``
        :param filter: Specification of matching tasks.
            if None, the behavior is equivalent to a :class:`Tasks.FilterSpec`
            with all attributes None which means all tasks match the filter.
        :rtype: :class:`Tasks.ListResult`
        :return: ListResult including details of all the tasks.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if any of the specified parameters are invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInaccessible` 
            if a task's state cannot be accessed or over 1000 tasks matching
            the :class:`Tasks.FilterSpec`.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        """
        return self._invoke('list',
                            {
                            'filter': filter,
                            })

    def get(self,
            task,
            ):
        """
        Returns information about a task.

        :type  task: :class:`str`
        :param task: Task identifier.
            The parameter must be an identifier for the resource type:
            ``com.vmware.snapservice.task``.
        :rtype: :class:`com.vmware.snapservice.tasks_client.Info`
        :return: Information about the specified task.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the task is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInaccessible` 
            if the task's state cannot be accessed.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        """
        return self._invoke('get',
                            {
                            'task': task,
                            })
class _TasksStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'filter': type.OptionalType(type.ReferenceType(__name__, 'Tasks.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.resource_inaccessible':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInaccessible'),
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
            url_template='/snapservice/tasks',
            path_variables={
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
            'task': type.IdType(resource_types='com.vmware.snapservice.task'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_inaccessible':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInaccessible'),
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
            url_template='/snapservice/tasks/{task}',
            path_variables={
                'task': 'task',
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
                'output_type': type.ReferenceType(__name__, 'Tasks.ListResult'),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType('com.vmware.snapservice.tasks_client', 'Info'),
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
            self, iface_name='com.vmware.snapservice.tasks',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Tasks': Tasks,
        'clusters': 'com.vmware.snapservice.clusters_client.StubFactory',
        'info': 'com.vmware.snapservice.info_client.StubFactory',
        'tasks': 'com.vmware.snapservice.tasks_client.StubFactory',
    }

