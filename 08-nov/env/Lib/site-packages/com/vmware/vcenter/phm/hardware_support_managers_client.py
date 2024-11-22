# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.phm.hardware_support_managers.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.phm.hardware_support_managers_client`` module provides
classes for proactive hardware management (PHM) in vCenter.

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


class ManagedHosts(VapiInterface):
    """
    The ``ManagedHosts`` class contains operations related to the managed host
    list maintained by each hardware support managers (HSM).
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.phm.hardware_support_managers.managed_hosts'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ManagedHostsStub)
        self._VAPI_OPERATION_IDS = {}

    class UpdateSpec(VapiStruct):
        """
        The ``ManagedHosts.UpdateSpec`` class specifies a list of managed hosts
        added or removed by a proactive hardware management, see
        :func:`ManagedHosts.update`.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     hosts_to_add=None,
                     hosts_to_remove=None,
                    ):
            """
            :type  hosts_to_add: :class:`list` of :class:`str` or ``None``
            :param hosts_to_add: A list of managed hosts added by an HSM.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
                This attribute may be None meaning this update does not contain any
                newly added managed hosts.
            :type  hosts_to_remove: :class:`list` of :class:`str` or ``None``
            :param hosts_to_remove: A list of managed hosts removed by an HSM.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
                This attribute may be None meaning this update does not contain any
                removed managed hosts.
            """
            self.hosts_to_add = hosts_to_add
            self.hosts_to_remove = hosts_to_remove
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.hardware_support_managers.managed_hosts.update_spec', {
            'hosts_to_add': type.OptionalType(type.ListType(type.IdType())),
            'hosts_to_remove': type.OptionalType(type.ListType(type.IdType())),
        },
        UpdateSpec,
        False,
        None))


    class ListResult(VapiStruct):
        """
        The ``ManagedHosts.ListResult`` class contains a list of managed hosts
        stored by proactive hardware management, see :func:`ManagedHosts.list`.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     managed_hosts=None,
                    ):
            """
            :type  managed_hosts: :class:`list` of :class:`str`
            :param managed_hosts: All managed hosts stored at PHM side.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            """
            self.managed_hosts = managed_hosts
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.hardware_support_managers.managed_hosts.list_result', {
            'managed_hosts': type.ListType(type.IdType()),
        },
        ListResult,
        False,
        None))



    def update(self,
               key,
               spec,
               ):
        """
        Modify the list of HSM managed hosts stored at PHM side. The managed
        hosts are the resources created and owned by HSM. Whenever there is any
        change in the managed host list, HSM uses this API to inform PHM.

        :type  key: :class:`str`
        :param key: HSM key of the targeted hardware support manager
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.phm.HardwareSupportManager``.
        :type  spec: :class:`ManagedHosts.UpdateSpec`
        :param spec: update spec on the change of managed host list
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the specified ``key`` does not exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the specified ``spec`` is invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if user has not provided adequate credentials.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if PHM service hits an internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if PHM service is not able to handle request.
        """
        return self._invoke('update',
                            {
                            'key': key,
                            'spec': spec,
                            })

    def list(self,
             key,
             ):
        """
        Get ``ManagedHosts.ListResult`` class, the list of managed hosts of a
        specified HSM.

        :type  key: :class:`str`
        :param key: HSM key of the targeted hardware support manager
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.phm.HardwareSupportManager``.
        :rtype: :class:`ManagedHosts.ListResult`
        :return: ``ManagedHosts.ListResult`` contains managed hosts of a specified
            HSM.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if specified ``key`` does not exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if user has not provided adequate credentials.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if PHM service hits an internal error.
        """
        return self._invoke('list',
                            {
                            'key': key,
                            })
class ResourceBundle(VapiInterface):
    """
    The ``ResourceBundle`` class contains operations related to the message
    resource bundle maintained by each hardware support managers (HSM).
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.phm.hardware_support_managers.resource_bundle'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ResourceBundleStub)
        self._VAPI_OPERATION_IDS = {}

    class ResourceInfo(VapiStruct):
        """
        The ``ResourceBundle.ResourceInfo`` class encapsulates the message
        resources for a locale.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     locale=None,
                     messages=None,
                    ):
            """
            :type  locale: :class:`str`
            :param locale: Locale for the message definitions. The locale specification needs
                to comply with RFC4646 language subtags. For common subtags, see
                https://en.wikipedia.org/wiki/IETF_language_tag
            :type  messages: :class:`dict` of :class:`str` and :class:`str`
            :param messages: Message definitions
            """
            self.locale = locale
            self.messages = messages
            VapiStruct.__init__(self)


    ResourceInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.hardware_support_managers.resource_bundle.resource_info', {
            'locale': type.StringType(),
            'messages': type.MapType(type.StringType(), type.StringType()),
        },
        ResourceInfo,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``ResourceBundle.UpdateSpec`` class describes the changes in the
        resource bundle provided by an HSM. See :func:`ResourceBundle.update`.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     bundle_to_change=None,
                    ):
            """
            :type  bundle_to_change: :class:`list` of :class:`ResourceBundle.ResourceInfo` or ``None``
            :param bundle_to_change: Changes in resouce bundle.
                This attribute may be None meaning no change in resource bundle.
            """
            self.bundle_to_change = bundle_to_change
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.hardware_support_managers.resource_bundle.update_spec', {
            'bundle_to_change': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ResourceBundle.ResourceInfo'))),
        },
        UpdateSpec,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``ResourceBundle.Info`` class contains a vendor's resource bundle
        stored by proactive hardware management, see :func:`ResourceBundle.get`.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     vendor_resource_infos=None,
                    ):
            """
            :type  vendor_resource_infos: :class:`list` of :class:`ResourceBundle.ResourceInfo`
            :param vendor_resource_infos: Entire vendor's resource bundle - a list of
                ``ResourceBundle.ResourceInfo`` stored at PHM side.
            """
            self.vendor_resource_infos = vendor_resource_infos
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.hardware_support_managers.resource_bundle.info', {
            'vendor_resource_infos': type.ListType(type.ReferenceType(__name__, 'ResourceBundle.ResourceInfo')),
        },
        Info,
        False,
        None))



    def update(self,
               key,
               spec,
               ):
        """
        Modify the vendor resource bundle of an HSM maintained at PHM side. A
        vendor's resource bundle is owned and provided by the vendor's HSM.
        Whenever there is any change in the resource bundle, HSM uses this API
        to inform PHM about the change.

        :type  key: :class:`str`
        :param key: HSM key of the targeted hardware support manager
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.phm.HardwareSupportManager``.
        :type  spec: :class:`ResourceBundle.UpdateSpec`
        :param spec: update spec on the change of resource bundle
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the specified ``key`` does not exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the specified ``spec`` is invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if user has not provided adequate credentials.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if PHM service hits an internal error.
        """
        return self._invoke('update',
                            {
                            'key': key,
                            'spec': spec,
                            })

    def get(self,
            key,
            ):
        """
        Get ``ResourceBundle.Info`` class, the resource bundle of a specified
        HSM.

        :type  key: :class:`str`
        :param key: HSM key of the targeted hardware support manager
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.phm.HardwareSupportManager``.
        :rtype: :class:`ResourceBundle.Info`
        :return: ``ResourceBundle.Info`` contains resource bundle of a specified
            HSM.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if specified ``key`` does not exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if user has not provided adequate credentials.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if PHM service hits an internal error.
        """
        return self._invoke('get',
                            {
                            'key': key,
                            })
class _ManagedHostsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'key': type.IdType(resource_types='com.vmware.vcenter.phm.HardwareSupportManager'),
            'spec': type.ReferenceType(__name__, 'ManagedHosts.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/phm/hardware-support-managers/{key}/managed-hosts',
            request_body_parameter='spec',
            path_variables={
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
            'key': type.IdType(resource_types='com.vmware.vcenter.phm.HardwareSupportManager'),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/phm/hardware-support-managers/{key}/managed-hosts',
            path_variables={
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

        operations = {
            'update': {
                'input_type': update_input_type,
                'output_type': type.VoidType(),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': update_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ReferenceType(__name__, 'ManagedHosts.ListResult'),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'update': update_rest_metadata,
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.phm.hardware_support_managers.managed_hosts',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _ResourceBundleStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'key': type.IdType(resource_types='com.vmware.vcenter.phm.HardwareSupportManager'),
            'spec': type.ReferenceType(__name__, 'ResourceBundle.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/phm/hardware-support-managers/{key}/resource-bundle',
            request_body_parameter='spec',
            path_variables={
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
            'key': type.IdType(resource_types='com.vmware.vcenter.phm.HardwareSupportManager'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/phm/hardware-support-managers/{key}/resource-bundle',
            path_variables={
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

        operations = {
            'update': {
                'input_type': update_input_type,
                'output_type': type.VoidType(),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': update_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'ResourceBundle.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'update': update_rest_metadata,
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.phm.hardware_support_managers.resource_bundle',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'ManagedHosts': ManagedHosts,
        'ResourceBundle': ResourceBundle,
    }

