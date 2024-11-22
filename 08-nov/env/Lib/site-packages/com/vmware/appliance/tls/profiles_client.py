# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.appliance.tls.profiles.
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


class Global(VapiInterface):
    """
    ``Global`` class provides methods APIs to configure standard TLS profile. 
    
    This is a profile based management for TLS usage on vCenter and the
    interface is for managing standard/built-in profiles globally in the
    appliance.. This class was added in vSphere API 8.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.appliance.tls.profiles.global'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _GlobalStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'set_task': 'set$task'})

    class Info(VapiStruct):
        """
        The ``Global.Info`` class contains the information about the profile name.
        This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     profile=None,
                    ):
            """
            :type  profile: :class:`str`
            :param profile: Defines the standard profile name. This attribute was added in
                vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.appliance.tls.profiles``. When methods return a value
                of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.appliance.tls.profiles``.
            """
            self.profile = profile
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.appliance.tls.profiles.global.info', {
            'profile': type.IdType(resource_types='com.vmware.appliance.tls.profiles'),
        },
        Info,
        False,
        None))


    class SetSpec(VapiStruct):
        """
        The ``Global.SetSpec`` class contains the information about the profile
        name. This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     profile=None,
                    ):
            """
            :type  profile: :class:`str`
            :param profile: Defines the standard profile name. This attribute was added in
                vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.appliance.tls.profiles``. When methods return a value
                of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.appliance.tls.profiles``.
            """
            self.profile = profile
            VapiStruct.__init__(self)


    SetSpec._set_binding_type(type.StructType(
        'com.vmware.appliance.tls.profiles.global.set_spec', {
            'profile': type.IdType(resource_types='com.vmware.appliance.tls.profiles'),
        },
        SetSpec,
        False,
        None))



    def get(self):
        """
        Gets the name of the current TLS Profile configured globally. This
        method was added in vSphere API 8.0.3.0.


        :rtype: :class:`Global.Info`
        :return: the name of the current global TLS Profile.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the session is not authenticated
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is not authorized. User needs to have operator
            privileges.
        """
        return self._invoke('get', None)


    def set_task(self,
            spec,
            ):
        """
        Sets any one of the standard profiles globally in the appliance. The
        result of this operation can be queried by calling the
        cis/tasks/{task-id} with the task-id in the response of this call. In
        case of a VCHA enabled cluster, setting a profile expects the VCHA
        cluster to be healthy and in maintenance or disabled mode before
        proceeding with the operation. This method was added in vSphere API
        8.0.3.0.

        :type  spec: :class:`Global.SetSpec`
        :param spec: Defines the name of the standard profile to be configured.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is some unknown internal error. appropriate error in case
            of VCHA enabled cluster if VCHA is not healthy or if it is in
            enabled state. The accompanying error message will give more
            details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the session is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is not authorized. User needs to have
            superAdministrator privileges to perform this operation.
        """
        task_id = self._invoke('set$task',
                                {
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.VoidType())
        return task_instance
class _GlobalStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {})
        get_error_dict = {
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
            url_template='/appliance/tls/profiles/global',
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

        # properties for set operation
        set_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Global.SetSpec'),
        })
        set_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/appliance/tls/profiles/global',
            request_body_parameter='spec',
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
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Global.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'set$task': {
                'input_type': set_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': set_error_dict,
                'input_value_validator_list': set_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'set': set_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.appliance.tls.profiles.global',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Global': Global,
    }

