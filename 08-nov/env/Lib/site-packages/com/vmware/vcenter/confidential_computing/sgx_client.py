# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.confidential_computing.sgx.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.confidential_computing.sgx_client`` module covers VC
functionality to work with Intel CPUs Software Guard Extensions (SGX) on the
hosts. 

Software Guard Extensions (SGX) is a feature of recent Intel CPUs that allows
users applications to create secure regions of memory-called enclaves-inside
their address space. An enclave is opaque to all software running outside of
the enclave, including the operating system and the hypervisor. In addition to
this isolation functionality, Intel SGX also provides remote attestation
capabilities, allowing external entities to verify that a specific SGX enclave
is running on a host. An enclave's attestation quote is rooted on an
Intel-issued Platform Certification Key (PCK) certificate that binds the
current platform's SGX cryptographic identity to Intel, essentially certifying
that it is a valid Intel SGX platform.

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


class Hosts(VapiInterface):
    """
    The ``Hosts`` classes provides methods to register Intel Software Guard
    Extensions (SGX) for the hosts. This class was added in vSphere API
    8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.confidential_computing.sgx.hosts'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _HostsStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'register_task': 'register$task'})

    class RegisterSpec(VapiStruct):
        """
        The ``Hosts.RegisterSpec`` class contains the data necessary to identify
        the host. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     host_id=None,
                    ):
            """
            :type  host_id: :class:`str`
            :param host_id: The host's identifier. This attribute was added in vSphere API
                8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``HostSystem``.
            """
            self.host_id = host_id
            VapiStruct.__init__(self)


    RegisterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.confidential_computing.sgx.hosts.register_spec', {
            'host_id': type.IdType(resource_types='HostSystem'),
        },
        RegisterSpec,
        False,
        None))




    def register_task(self,
                 spec,
                 ):
        """
        Register host by stored SGX configuration. This method was added in
        vSphere API 8.0.0.1.

        :type  spec: :class:`Hosts.RegisterSpec`
        :param spec: Described the host that need to be registered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            for any other error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the host ID is not valid.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceBusy` 
            if register for same host is already in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the system does not support SGX Registration.
        """
        task_id = self._invoke('register$task',
                                {
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.VoidType())
        return task_instance
class _HostsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for register operation
        register_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Hosts.RegisterSpec'),
        })
        register_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_busy':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceBusy'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        register_input_value_validator_list = [
        ]
        register_output_validator_list = [
        ]
        register_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/confidential-computing/sgx/hosts',
            request_body_parameter='spec',
            path_variables={
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'register',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'register$task': {
                'input_type': register_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': register_error_dict,
                'input_value_validator_list': register_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
        }
        rest_metadata = {
            'register': register_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.confidential_computing.sgx.hosts',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Hosts': Hosts,
    }

