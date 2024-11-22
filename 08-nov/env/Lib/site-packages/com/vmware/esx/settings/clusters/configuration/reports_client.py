# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.settings.clusters.configuration.reports.
#---------------------------------------------------------------------------

"""


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


class LastApplyResult(VapiInterface):
    """
    The ``LastApplyResult`` class provides methods to get the most recent
    available result of applying the configuration to all hosts within a
    cluster. This class was added in vSphere API 8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.configuration.reports.last_apply_result'
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


    def get(self,
            cluster,
            ):
        """
        Returns the most recent available result of applying the configuration
        document to all hosts within the cluster. This method was added in
        vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: The cluster identifier.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`com.vmware.esx.settings.clusters_client.Configuration.ApplyResult`
        :return: Most recent available result of applying the desired configuration
            to all hosts within the cluster.
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
            if the caller does not have the necessary privileges to perform the
            request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.View``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.View``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })
class LastComplianceResult(VapiInterface):
    """
    The ``LastComplianceResult`` class provides methods to get the last
    available check compliance result for the cluster. This class was added in
    vSphere API 8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.configuration.reports.last_compliance_result'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _LastComplianceResultStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            cluster,
            ):
        """
        This API provides results from the last completed Check Compliance
        operation on the cluster. This method was added in vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`com.vmware.esx.settings.clusters.configuration_client.ClusterCompliance`
        :return: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` or no last
            compliance result was found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.View``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.View``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })
class LastPrecheckResult(VapiInterface):
    """
    The ``LastPrecheckResult`` class provides methods to get the most recent
    available result of Precheck. This class was added in vSphere API 8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.configuration.reports.last_precheck_result'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _LastPrecheckResultStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            cluster,
            ):
        """
        This API returns results from the last Precheck operation on the
        cluster. This method was added in vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`com.vmware.esx.settings.clusters.configuration_client.ClusterPrecheckResult`
        :return: Most recent available result of Precheck.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system or
            if there is no result associated with the cluster ``cluster``.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller does not have the necessary privileges to perform the
            request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.View``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.View``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })
class RecentTasks(VapiInterface):
    """
    The ``RecentTasks`` class provides methods to get the most recent
    configuration-related tasks. This class was added in vSphere API 8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.configuration.reports.recent_tasks'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _RecentTasksStub)
        self._VAPI_OPERATION_IDS = {}

    class DraftTasks(VapiStruct):
        """
        The ``RecentTasks.DraftTasks`` class contains attributes that specify the
        ID of the latest task to be executed for various operations on a draft.
        This class was added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     precheck=None,
                    ):
            """
            :type  precheck: :class:`str` or ``None``
            :param precheck: The ID of the last precheck task to be executed for this draft.
                This attribute was added in vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.cis.task``. When methods return a value of this class
                as a return value, the attribute will be an identifier for the
                resource type: ``com.vmware.cis.task``.
            """
            self.precheck = precheck
            VapiStruct.__init__(self)


    DraftTasks._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.reports.recent_tasks.draft_tasks', {
            'precheck': type.OptionalType(type.IdType()),
        },
        DraftTasks,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``RecentTasks.Info`` class contains attributes that specify the ID of
        the latest task to be executed for various operations. If a task is
        currently running, that ID will be returned, otherwise the most recently
        finished task will be returned. This class was added in vSphere API
        8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     check_compliance=None,
                     precheck=None,
                     draft_tasks=None,
                     apply=None,
                    ):
            """
            :type  check_compliance: :class:`str` or ``None``
            :param check_compliance: The ID of the last check-compliance task to be executed. This
                attribute was added in vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.cis.task``. When methods return a value of this class
                as a return value, the attribute will be an identifier for the
                resource type: ``com.vmware.cis.task``.
            :type  precheck: :class:`str` or ``None``
            :param precheck: The ID of the last precheck task to be executed. This attribute was
                added in vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.cis.task``. When methods return a value of this class
                as a return value, the attribute will be an identifier for the
                resource type: ``com.vmware.cis.task``.
            :type  draft_tasks: :class:`dict` of :class:`str` and :class:`RecentTasks.DraftTasks`
            :param draft_tasks: Map of draft IDs to the latest tasks executed for that draft. This
                attribute was added in vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``com.vmware.esx.settings.draft``. When methods return a
                value of this class as a return value, the key in the attribute
                :class:`dict` will be an identifier for the resource type:
                ``com.vmware.esx.settings.draft``.
            :type  apply: :class:`str` or ``None``
            :param apply: The ID of the last apply task to be executed. This attribute was
                added in vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.cis.task``. When methods return a value of this class
                as a return value, the attribute will be an identifier for the
                resource type: ``com.vmware.cis.task``.
            """
            self.check_compliance = check_compliance
            self.precheck = precheck
            self.draft_tasks = draft_tasks
            self.apply = apply
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.reports.recent_tasks.info', {
            'check_compliance': type.OptionalType(type.IdType()),
            'precheck': type.OptionalType(type.IdType()),
            'draft_tasks': type.MapType(type.IdType(), type.ReferenceType(__name__, 'RecentTasks.DraftTasks')),
            'apply': type.OptionalType(type.IdType()),
        },
        Info,
        False,
        None))



    def get(self,
            cluster,
            ):
        """
        This API returns the IDs of the configuration tasks most recently
        executed on this cluster. This method was added in vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`RecentTasks.Info`
        :return: A structure containing the most recent executions of draft- related
            tasks.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller does not have the necessary privileges to perform the
            request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.View``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.View``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })
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
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/configuration/reports/last-apply-result',
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
                'output_type': type.ReferenceType('com.vmware.esx.settings.clusters_client', 'Configuration.ApplyResult'),
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
            self, iface_name='com.vmware.esx.settings.clusters.configuration.reports.last_apply_result',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _LastComplianceResultStub(ApiInterfaceStub):
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
            url_template='/esx/settings/clusters/{cluster}/configuration/reports/last-compliance-result',
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
                'output_type': type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'ClusterCompliance'),
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
            self, iface_name='com.vmware.esx.settings.clusters.configuration.reports.last_compliance_result',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _LastPrecheckResultStub(ApiInterfaceStub):
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
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/configuration/reports/last-precheck-result',
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
                'output_type': type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'ClusterPrecheckResult'),
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
            self, iface_name='com.vmware.esx.settings.clusters.configuration.reports.last_precheck_result',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _RecentTasksStub(ApiInterfaceStub):
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
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/configuration/reports/recent-tasks',
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
                'output_type': type.ReferenceType(__name__, 'RecentTasks.Info'),
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
            self, iface_name='com.vmware.esx.settings.clusters.configuration.reports.recent_tasks',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'LastApplyResult': LastApplyResult,
        'LastComplianceResult': LastComplianceResult,
        'LastPrecheckResult': LastPrecheckResult,
        'RecentTasks': RecentTasks,
    }

