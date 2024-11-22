# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.supervisors.recovery.backup.
#---------------------------------------------------------------------------

"""
The
``com.vmware.vcenter.namespace_management.supervisors.recovery.backup_client``
module provides classes for Supervisor backup operations.

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


class Archives(VapiInterface):
    """
    The ``Archives`` class provides methods to manage Supervisor Backup
    archives stored on vCenter Server Appliance file system. This class was
    added in vSphere API 8.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisors.recovery.backup.archives'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ArchivesStub)
        self._VAPI_OPERATION_IDS = {}

    class FilterSpec(VapiStruct):
        """
        The ``Archives.FilterSpec`` class contains attributes used to filter the
        result when listing Backup archives (see :func:`Archives.list`). This class
        was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     archive=None,
                     usable=None,
                    ):
            """
            :type  archive: :class:`str` or ``None``
            :param archive: Matches Backup archives with :attr:`Archives.Info.archive` equal to
                the specified value. This attribute was added in vSphere API
                8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.backup.Archive``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.backup.Archive``.
                if None this filter is not applied.
            :type  usable: :class:`bool` or ``None``
            :param usable: Matches Backup archives with :attr:`Archives.Info.usable` equal to
                the specified value. This attribute was added in vSphere API
                8.0.3.0.
                if None this filter is not applied.
            """
            self.archive = archive
            self.usable = usable
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.recovery.backup.archives.filter_spec', {
            'archive': type.OptionalType(type.IdType()),
            'usable': type.OptionalType(type.BooleanType()),
        },
        FilterSpec,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Archives.Info`` contains information about a Supervisor Backup
        archive. This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     archive=None,
                     supervisor=None,
                     location=None,
                     timestamp=None,
                     supervisor_version=None,
                     namespaces=None,
                     comment=None,
                     usable=None,
                     unusable_reasons=None,
                    ):
            """
            :type  archive: :class:`str`
            :param archive: Backup archive identifier. This attribute was added in vSphere API
                8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.backup.Archive``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.backup.Archive``.
            :type  supervisor: :class:`str`
            :param supervisor: Identifier of the Supervisor captured in the backup. This attribute
                was added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
            :type  location: :class:`str`
            :param location: Absolute path to Backup archive on vCenter Server Appliance file
                system. This attribute was added in vSphere API 8.0.3.0.
            :type  timestamp: :class:`datetime.datetime`
            :param timestamp: Time when the Supervisor backup method was completed. This
                attribute was added in vSphere API 8.0.3.0.
            :type  supervisor_version: :class:`str`
            :param supervisor_version: Version of the Supervisor captured in the backup. This is a
                semantic version string in the form
                v1.26.1+vmware.2-vsc0.1.1-20805373, where the prefix is the
                Kubernetes version (v1.26.1) and the suffix is the Supervisor build
                version (vsc0.1.1-20805373). This attribute was added in vSphere
                API 8.0.3.0.
            :type  namespaces: :class:`list` of :class:`str`
            :param namespaces: A list of Supervisor Namespaces captured in the backup. This
                attribute was added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``. When methods return a
                value of this class as a return value, the attribute will contain
                identifiers for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``.
            :type  comment: :class:`str`
            :param comment: Comment provided when invoking :func:`Jobs.create` method. This
                attribute was added in vSphere API 8.0.3.0.
            :type  usable: :class:`bool`
            :param usable: Backup archive usability for
                :func:`com.vmware.vcenter.namespace_management.supervisors.recovery.restore_client.Jobs.create`
                method. It is set to ``false`` in following cases: 
                
                * The ``supervisor`` is not found.
                * Backup was taken on a newer vCenter Server. i.e. Supervisor build
                  version component of the ``supervisorVersion`` value is more recent
                  than Supervisor build version component of ``supervisor``
                  :attr:`com.vmware.vcenter.namespace_management.software_client.Clusters.Info.current_version`
                  and all of the
                  :attr:`com.vmware.vcenter.namespace_management.software_client.Clusters.Info.available_versions`.
                * Kubernetes version component of the ``supervisorVersion`` value
                  is not a supported on the current vCenter Server version. Refer
                  "VMware vSphere with Tanzu" Release notes for Kubernetes versions
                  supported on a vCenter Server version.
                * Invalid format.
                
                If ``false``, the list of reasons that make it unusable will be
                given in the ``unusableReasons`` field. This attribute was added in
                vSphere API 8.0.3.0.
            :type  unusable_reasons: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param unusable_reasons: Reasons that make Bacup archive unusable. Will be empty if
                ``usable`` value is ``true``. This attribute was added in vSphere
                API 8.0.3.0.
            """
            self.archive = archive
            self.supervisor = supervisor
            self.location = location
            self.timestamp = timestamp
            self.supervisor_version = supervisor_version
            self.namespaces = namespaces
            self.comment = comment
            self.usable = usable
            self.unusable_reasons = unusable_reasons
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.recovery.backup.archives.info', {
            'archive': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.backup.Archive'),
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'location': type.StringType(),
            'timestamp': type.DateTimeType(),
            'supervisor_version': type.StringType(),
            'namespaces': type.ListType(type.IdType()),
            'comment': type.StringType(),
            'usable': type.BooleanType(),
            'unusable_reasons': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        Info,
        False,
        None))



    def list(self,
             filter=None,
             ):
        """
        List all Backup archives that are stored on vCenter Server Appliance
        file system. Optionally, apply the filter to Backup archives that match
        the criteria in the {#link FilterSpec}. This method was added in
        vSphere API 8.0.3.0.

        :type  filter: :class:`Archives.FilterSpec` or ``None``
        :param filter: Set of parameters that can be used to constrain the results of the
            method.
            if None all records will be returned.
        :rtype: :class:`list` of :class:`Archives.Info`
        :return: Information about Backup archives stored on vCenter Server
            Appliance file system matching the {#link FilterSpec}.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is missing the System.Read privilege.
        """
        return self._invoke('list',
                            {
                            'filter': filter,
                            })
class Jobs(VapiInterface):
    """
    The ``Jobs`` class provides methods to create Supervisor backup jobs. This
    class was added in vSphere API 8.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisors.recovery.backup.jobs'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _JobsStub)
        self._VAPI_OPERATION_IDS = {}

    class CreateSpec(VapiStruct):
        """
        The ``Jobs.CreateSpec`` class contains inputs to be specified for
        :func:`Jobs.create`. This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     comment=None,
                     ignore_health_check_failure=None,
                    ):
            """
            :type  comment: :class:`str` or ``None``
            :param comment: Comment to help identify resulting Backup archive. This attribute
                was added in vSphere API 8.0.3.0.
                If None comment will be empty.
            :type  ignore_health_check_failure: :class:`bool` or ``None``
            :param ignore_health_check_failure: Ignore Supervisor health check failure when taking Supervisor
                backup. Supervisor is considered unhealthy if either
                :attr:`com.vmware.vcenter.namespace_management.supervisors_client.Summary.Info.config_status`
                or
                :attr:`com.vmware.vcenter.namespace_management.supervisors_client.Summary.Info.kubernetes_status`
                value, as returned by
                :func:`com.vmware.vcenter.namespace_management.supervisors_client.Summary.get`
                method is set to ERROR. This attribute was added in vSphere API
                8.0.3.0.
                if None or set to ``false``, health check failure of Supervisor
                will not be ignored and will result in :func:`Jobs.create` method
                to report failure.
            """
            self.comment = comment
            self.ignore_health_check_failure = ignore_health_check_failure
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.recovery.backup.jobs.create_spec', {
            'comment': type.OptionalType(type.StringType()),
            'ignore_health_check_failure': type.OptionalType(type.BooleanType()),
        },
        CreateSpec,
        False,
        None))



    def create(self,
               supervisor,
               spec,
               ):
        """
        Initiate a Supervisor Backup job. The Backup captures Supervisor
        Control plane state that includes a snapshot of etcd, required
        certificates and container images for infrastructure components. Once
        the job succeeds, corresponding Backup archive will be stored on
        vCenter Appliance file system. These Backup archives can be looked up
        and managed using operations provided by :class:`Archives` class and
        can be used to restore the Supervisor using
        :func:`com.vmware.vcenter.namespace_management.supervisors.recovery.restore_client.Jobs.create`.
        This method was added in vSphere API 8.0.3.0.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  spec: :class:`Jobs.CreateSpec`
        :param spec: Specifies input parameters for backup create job.
        :rtype: :class:`str`
        :return: The task identifier for the backup job. On success, the task's
            result property will be set to
            The return value will be an identifier for the resource type:
            ``com.vmware.cis.task``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if a backup job is already pending for the Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if Supervisor is not healthy and {#member
            CreateSpec.ignoreHealthCheckFailure} is not set to ``true`` or if
            Supervisor is not fully enabled yet.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the given Supervisor cannot be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is missing the Namespaces.Backup privilege on the
            Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if version of the specified Supervisor does not support backup.
        """
        return self._invoke('create',
                            {
                            'supervisor': supervisor,
                            'spec': spec,
                            })
class _ArchivesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'filter': type.OptionalType(type.ReferenceType(__name__, 'Archives.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
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
            url_template='/vcenter/namespace-management/supervisors/recovery/backup/archives',
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

        operations = {
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'Archives.Info')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.supervisors.recovery.backup.archives',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _JobsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'spec': type.ReferenceType(__name__, 'Jobs.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/recovery/backup/jobs',
            request_body_parameter='spec',
            path_variables={
                'supervisor': 'supervisor',
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
            'create': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.task'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'create': create_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.supervisors.recovery.backup.jobs',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Archives': Archives,
        'Jobs': Jobs,
    }

