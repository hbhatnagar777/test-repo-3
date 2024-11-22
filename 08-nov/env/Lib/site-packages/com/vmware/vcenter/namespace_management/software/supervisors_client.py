# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.software.supervisors.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.namespace_management.software.supervisors_client``
module provides classes for managing Supervisor upgrades.

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


class Prechecks(VapiInterface):
    """
    The ``Prechecks`` class provides methods to perform Supervisor upgrade
    pre-checks. This class was added in vSphere API 8.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.software.supervisors.prechecks'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _PrechecksStub)
        self._VAPI_OPERATION_IDS = {}

    class PrecheckSpec(VapiStruct):
        """
        The ``Prechecks.PrecheckSpec`` class contains the specification required to
        run Supervisor upgrade pre-checks. This class was added in vSphere API
        8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     target_version=None,
                    ):
            """
            :type  target_version: :class:`str`
            :param target_version: The target version indicates the Supervisor upgrade version against
                which the Supervisor upgrade pre-checks should run, the value for
                this field should be provided from the list of
                :attr:`com.vmware.vcenter.namespace_management.software_client.Clusters.Info.available_versions`.
                This attribute was added in vSphere API 8.0.3.0.
            """
            self.target_version = target_version
            VapiStruct.__init__(self)


    PrecheckSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.software.supervisors.prechecks.precheck_spec', {
            'target_version': type.StringType(),
        },
        PrecheckSpec,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Prechecks.Info`` class contains detailed information about the
        Supervisor upgrade pre-check results for multiple Supervisor upgrade
        version(s). This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     precheck_results=None,
                    ):
            """
            :type  precheck_results: :class:`list` of :class:`Prechecks.PrecheckResult` or ``None``
            :param precheck_results: Information about Supervisor upgrade pre-check results. This
                attribute was added in vSphere API 8.0.3.0.
                If None, the Supervisor upgrade pre-checks did not run or upgrade
                is not available.
            """
            self.precheck_results = precheck_results
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.software.supervisors.prechecks.info', {
            'precheck_results': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Prechecks.PrecheckResult'))),
        },
        Info,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``Prechecks.FilterSpec`` class contains request filter(s) for fetching
        the Supervisor upgrade pre-checks. This class was added in vSphere API
        8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     target_version=None,
                    ):
            """
            :type  target_version: :class:`str` or ``None``
            :param target_version: Supervisor upgrade version for which pre-check results should be
                queried. This attribute was added in vSphere API 8.0.3.0.
                If :class:`set`, return the pre-check results only for the
                specified target version. If None, return the pre-check results for
                all the Supervisor upgrade versions against which pre-checks have
                already been executed.
            """
            self.target_version = target_version
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.software.supervisors.prechecks.filter_spec', {
            'target_version': type.OptionalType(type.StringType()),
        },
        FilterSpec,
        False,
        None))


    class PrecheckResult(VapiStruct):
        """
        The ``Prechecks.PrecheckResult`` class contains the detailed information
        about Supervisor upgrade pre-checks against individual upgrade version.
        This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     target_version=None,
                     conditions=None,
                    ):
            """
            :type  target_version: :class:`str`
            :param target_version: Represents Supervisor upgrade version for which
                :attr:`Prechecks.PrecheckResult.conditions` belong to. This
                attribute was added in vSphere API 8.0.3.0.
            :type  conditions: :class:`list` of :class:`com.vmware.vcenter.namespace_management_client.Clusters.Condition`
            :param conditions: Supervisor upgrade pre-check results for
                :attr:`Prechecks.PrecheckResult.target_version`. This attribute was
                added in vSphere API 8.0.3.0.
            """
            self.target_version = target_version
            self.conditions = conditions
            VapiStruct.__init__(self)


    PrecheckResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.software.supervisors.prechecks.precheck_result', {
            'target_version': type.StringType(),
            'conditions': type.ListType(type.ReferenceType('com.vmware.vcenter.namespace_management_client', 'Clusters.Condition')),
        },
        PrecheckResult,
        False,
        None))



    def run(self,
            supervisor,
            spec,
            ):
        """
        Run Supervisor upgrade pre-checks. This operation will initiate
        Supervisor upgrade pre-checks for a specific target version. This
        method was added in vSphere API 8.0.3.0.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the supervisor on which upgraded pre-checks are run.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  spec: :class:`Prechecks.PrecheckSpec`
        :param spec: Specification for running Supervisor upgrade pre-checks.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if upgrade is not available for the Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if Supervisor upgrade is in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Upgrade privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the  contains invalid details.
        """
        return self._invoke('run',
                            {
                            'supervisor': supervisor,
                            'spec': spec,
                            })

    def get(self,
            supervisor,
            filter=None,
            ):
        """
        Returns information about Supervisor upgrade pre-checks. This method
        was added in vSphere API 8.0.3.0.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  filter: :class:`Prechecks.FilterSpec` or ``None``
        :param filter: Includes specification to fetch pre-check results for specific
            Supervisor upgrade version.
            If :class:`set` returns the pre-check results only for the
            specified target version. If None returns the pre-check results for
            all the versions against which pre-checks ran.
        :rtype: :class:`Prechecks.Info`
        :return: Supervisor upgrade pre-check results.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor could not be located or pre-check results not found
            for :attr:`Prechecks.FilterSpec.target_version` or pre-check
            results not found for any available upgrade version(s).
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'supervisor': supervisor,
                            'filter': filter,
                            })
class _PrechecksStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for run operation
        run_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'spec': type.ReferenceType(__name__, 'Prechecks.PrecheckSpec'),
        })
        run_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),

        }
        run_input_value_validator_list = [
        ]
        run_output_validator_list = [
        ]
        run_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/software/supervisors/{supervisor}/prechecks',
            request_body_parameter='spec',
            path_variables={
                'supervisor': 'supervisor',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'run',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'filter': type.OptionalType(type.ReferenceType(__name__, 'Prechecks.FilterSpec')),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
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
            url_template='/vcenter/namespace-management/software/supervisors/{supervisor}/prechecks',
            request_body_parameter='filter',
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
            'run': {
                'input_type': run_input_type,
                'output_type': type.VoidType(),
                'errors': run_error_dict,
                'input_value_validator_list': run_input_value_validator_list,
                'output_validator_list': run_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Prechecks.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'run': run_rest_metadata,
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.software.supervisors.prechecks',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Prechecks': Prechecks,
    }

