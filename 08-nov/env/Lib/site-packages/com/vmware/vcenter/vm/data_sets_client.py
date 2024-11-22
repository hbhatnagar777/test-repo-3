# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.vm.data_sets.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.vm.data_sets_client`` module provides classes for
manipulating entries in data sets.

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


class Entries(VapiInterface):
    """
    The ``Entries`` class provides methods for manipulating individual entries
    in a data set. This class was added in vSphere API 8.0.0.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.vm.data_sets.entries'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _EntriesStub)
        self._VAPI_OPERATION_IDS = {}


    def set(self,
            vm,
            data_set,
            key,
            value,
            ):
        """
        Creates or updates an entry in a data set. If an entry whose key
        matches ``key`` already exists, it will replace the existing ``value``,
        otherwise it will create a new entry. This method was added in vSphere
        API 8.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  data_set: :class:`str`
        :param data_set: Identifier of the data set.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.vm.DataSet``.
        :type  key: :class:`str`
        :param key: The key of the entry to set. A key can be at most 4096 bytes.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.vm.data_sets.Entry``.
        :type  value: :class:`str`
        :param value: The value of the entry to set. A value can be at most 1MB.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the key is too large.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the value is too large.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the virtual machine is in a state that doesn't allow
            modifications, for example suspended.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the data set is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.UnableToAllocateResource` 
            if the new data set requires more resources than are available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the data set access mode prevents the operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the virtual hardware version of the virtual machine does not
            support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the ESXi host version does not support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.DataSets.DataSetEntrySet``.
        """
        return self._invoke('set',
                            {
                            'vm': vm,
                            'data_set': data_set,
                            'key': key,
                            'value': value,
                            })

    def get(self,
            vm,
            data_set,
            key,
            ):
        """
        Retrieves the value of an entry in a data set. This method was added in
        vSphere API 8.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  data_set: :class:`str`
        :param data_set: Identifier of the data set.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.vm.DataSet``.
        :type  key: :class:`str`
        :param key: The key of the entry to retrieve.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.vm.data_sets.Entry``.
        :rtype: :class:`str`
        :return: the value of the entry.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the data set is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if there is no entry associated with ``key`` in the ``data_set``.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the data set access mode prevents the operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the virtual hardware version of the virtual machine does not
            support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the ESXi host version does not support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.DataSets.DataSetEntryGet``.
        """
        return self._invoke('get',
                            {
                            'vm': vm,
                            'data_set': data_set,
                            'key': key,
                            })

    def delete(self,
               vm,
               data_set,
               key,
               ):
        """
        Deletes an entry in a data set. This method was added in vSphere API
        8.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  data_set: :class:`str`
        :param data_set: Identifier of the data set.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.vm.DataSet``.
        :type  key: :class:`str`
        :param key: The key of the entry to delete.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.vm.data_sets.Entry``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the virtual machine is in a state that doesn't allow
            modifications, for example suspended.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the data set is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if there is no entry associated with ``key`` in the ``data_set``.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the data set access mode prevents the operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the virtual hardware version of the virtual machine does not
            support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the ESXi host version does not support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.DataSets.DataSetEntryDelete``.
        """
        return self._invoke('delete',
                            {
                            'vm': vm,
                            'data_set': data_set,
                            'key': key,
                            })

    def list(self,
             vm,
             data_set,
             ):
        """
        Lists all entry keys in a data set. This method was added in vSphere
        API 8.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  data_set: :class:`str`
        :param data_set: Identifier of the data set.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.vm.DataSet``.
        :rtype: :class:`set` of :class:`str`
        :return: The keys belonging to the data set.
            The return value will contain identifiers for the resource type:
            ``com.vmware.vcenter.vm.data_sets.Entry``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the data set is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the data set access mode prevents the operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the virtual hardware version of the virtual machine does not
            support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the ESXi host version does not support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.DataSets.DataSetEntryList``.
        """
        return self._invoke('list',
                            {
                            'vm': vm,
                            'data_set': data_set,
                            })
class _EntriesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for set operation
        set_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
            'data_set': type.IdType(resource_types='com.vmware.vcenter.vm.DataSet'),
            'key': type.IdType(resource_types='com.vmware.vcenter.vm.data_sets.Entry'),
            'value': type.StringType(),
        })
        set_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unable_to_allocate_resource':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnableToAllocateResource'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/vcenter/vm/{vm}/data-sets/{dataSet}/entries/{key}',
            request_body_parameter='value',
            path_variables={
                'vm': 'vm',
                'data_set': 'dataSet',
                'key': 'key',
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
            'vm': type.IdType(resource_types='VirtualMachine'),
            'data_set': type.IdType(resource_types='com.vmware.vcenter.vm.DataSet'),
            'key': type.IdType(resource_types='com.vmware.vcenter.vm.data_sets.Entry'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/vm/{vm}/data-sets/{dataSet}/entries/{key}',
            path_variables={
                'vm': 'vm',
                'data_set': 'dataSet',
                'key': 'key',
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
            'vm': type.IdType(resource_types='VirtualMachine'),
            'data_set': type.IdType(resource_types='com.vmware.vcenter.vm.DataSet'),
            'key': type.IdType(resource_types='com.vmware.vcenter.vm.data_sets.Entry'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vcenter/vm/{vm}/data-sets/{dataSet}/entries/{key}',
            path_variables={
                'vm': 'vm',
                'data_set': 'dataSet',
                'key': 'key',
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
            'vm': type.IdType(resource_types='VirtualMachine'),
            'data_set': type.IdType(resource_types='com.vmware.vcenter.vm.DataSet'),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/vm/{vm}/data-sets/{dataSet}/entries',
            path_variables={
                'vm': 'vm',
                'data_set': 'dataSet',
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
            'set': {
                'input_type': set_input_type,
                'output_type': type.VoidType(),
                'errors': set_error_dict,
                'input_value_validator_list': set_input_value_validator_list,
                'output_validator_list': set_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.StringType(),
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
            'list': {
                'input_type': list_input_type,
                'output_type': type.SetType(type.IdType()),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'set': set_rest_metadata,
            'get': get_rest_metadata,
            'delete': delete_rest_metadata,
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.vm.data_sets.entries',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Entries': Entries,
    }

