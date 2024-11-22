# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.host.entropy.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.host.entropy_client`` module provides classes to
manage entropy

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


class ExternalPool(VapiInterface):
    """
    The ``ExternalPool`` class provides methods to send entropy data and query
    external entropy pool information on an ESX host. Clients can check the
    entropy level of an ESX host using the :func:`ExternalPool.get` method to
    check . When the entropy level has dropped below a threshold, a client can
    use the :func:`ExternalPool.add` method to add additional entropy until as
    required. This class was added in vSphere API 8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.host.entropy.external_pool'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ExternalPoolStub)
        self._VAPI_OPERATION_IDS = {}

    class Status(Enum):
        """
        The ``ExternalPool.Status`` enum represents external entropy status on an
        ESX host. This enumeration was added in vSphere API 8.0.1.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        ENABLED = None
        """
        External entropy is enabled for the ESX host. This class attribute was
        added in vSphere API 8.0.1.0.

        """
        DISABLED = None
        """
        External entropy is disabled for the ESX host. This class attribute was
        added in vSphere API 8.0.1.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Status` instance.
            """
            Enum.__init__(string)

    Status._set_values({
        'ENABLED': Status('ENABLED'),
        'DISABLED': Status('DISABLED'),
    })
    Status._set_binding_type(type.EnumType(
        'com.vmware.vcenter.host.entropy.external_pool.status',
        Status))


    class AddSpec(VapiStruct):
        """
        The ``ExternalPool.AddSpec`` class defines parameters for the
        :func:`ExternalPool.add` method. This class was added in vSphere API
        8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     data=None,
                    ):
            """
            :type  data: :class:`str`
            :param data: Buffer for entropy data. This will carry entropy data received from
                the external entropy source. This attribute was added in vSphere
                API 8.0.1.0.
            """
            self.data = data
            VapiStruct.__init__(self)


    AddSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.host.entropy.external_pool.add_spec', {
            'data': type.BlobType(),
        },
        AddSpec,
        False,
        None))


    class AddResult(VapiStruct):
        """
        The ``ExternalPool.AddResult`` class provides result of the
        :func:`ExternalPool.add` method. This class was added in vSphere API
        8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     capacity=None,
                     currently_available=None,
                     low_watermark=None,
                     inactive_source_timeout=None,
                    ):
            """
            :type  capacity: :class:`long`
            :param capacity: Capacity of external entropy pool in bytes. This attribute was
                added in vSphere API 8.0.1.0.
            :type  currently_available: :class:`long`
            :param currently_available: Currently available amount of entropy in bytes in the external
                entropy pool. This attribute was added in vSphere API 8.0.1.0.
            :type  low_watermark: :class:`long`
            :param low_watermark: A threshold value in bytes. An audit record will be logged when
                :attr:`ExternalPool.AddResult.currently_available` drops below this
                value. This attribute was added in vSphere API 8.0.1.0.
            :type  inactive_source_timeout: :class:`long`
            :param inactive_source_timeout: A timeout period in seconds within which the client must call
                :func:`ExternalPool.get` method or :func:`ExternalPool.add` method.
                If no call is received before the timeout lapses an audit record
                will be created. 
                
                This is the timeout to detect any connection lost with the client..
                This attribute was added in vSphere API 8.0.1.0.
            """
            self.capacity = capacity
            self.currently_available = currently_available
            self.low_watermark = low_watermark
            self.inactive_source_timeout = inactive_source_timeout
            VapiStruct.__init__(self)


    AddResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.host.entropy.external_pool.add_result', {
            'capacity': type.IntegerType(),
            'currently_available': type.IntegerType(),
            'low_watermark': type.IntegerType(),
            'inactive_source_timeout': type.IntegerType(),
        },
        AddResult,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``ExternalPool.Info`` class contains entropy pool information on the
        ESX host. It provides external entropy pool details as well as timeout in
        seconds within which client has to keep calling :func:`ExternalPool.get`
        method. 
        
        Client has to monitor Info.currentlyAvailable parameter. Before the entropy
        level goes down below a threshold value the client has to send entropy data
        by calling :func:`ExternalPool.add` method.. This class was added in
        vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'status',
                {
                    'ENABLED' : [('capacity', True), ('currently_available', True), ('low_watermark', True), ('inactive_source_timeout', True)],
                    'DISABLED' : [],
                }
            ),
        ]



        def __init__(self,
                     status=None,
                     capacity=None,
                     currently_available=None,
                     low_watermark=None,
                     inactive_source_timeout=None,
                    ):
            """
            :type  status: :class:`ExternalPool.Status`
            :param status: This flag indicates entropy service is enabled or not in a ESX
                host. This attribute was added in vSphere API 8.0.1.0.
            :type  capacity: :class:`long`
            :param capacity: Capacity of external entropy pool in bytes. This attribute was
                added in vSphere API 8.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``status`` is :attr:`ExternalPool.Status.ENABLED`.
            :type  currently_available: :class:`long`
            :param currently_available: Currently available amount of entropy in bytes in the external
                entropy pool. This attribute was added in vSphere API 8.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``status`` is :attr:`ExternalPool.Status.ENABLED`.
            :type  low_watermark: :class:`long`
            :param low_watermark: A threshold value in bytes. An audit record will be logged when
                :attr:`ExternalPool.Info.currently_available` drops below this
                value. This attribute was added in vSphere API 8.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``status`` is :attr:`ExternalPool.Status.ENABLED`.
            :type  inactive_source_timeout: :class:`long`
            :param inactive_source_timeout: A timeout period in seconds within which the client must call
                :func:`ExternalPool.get` method or :func:`ExternalPool.add` method.
                If no call is received before the timeout lapses an audit record
                will be created. 
                
                This timeout is used to detect that connection with the client is
                lost.. This attribute was added in vSphere API 8.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``status`` is :attr:`ExternalPool.Status.ENABLED`.
            """
            self.status = status
            self.capacity = capacity
            self.currently_available = currently_available
            self.low_watermark = low_watermark
            self.inactive_source_timeout = inactive_source_timeout
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.host.entropy.external_pool.info', {
            'status': type.ReferenceType(__name__, 'ExternalPool.Status'),
            'capacity': type.OptionalType(type.IntegerType()),
            'currently_available': type.OptionalType(type.IntegerType()),
            'low_watermark': type.OptionalType(type.IntegerType()),
            'inactive_source_timeout': type.OptionalType(type.IntegerType()),
        },
        Info,
        False,
        None))



    def get(self,
            host,
            ):
        """
        Retrieves the entropy pool details of a host including current entropy
        level. This method was added in vSphere API 8.0.1.0.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`ExternalPool.Info`
        :return: Entropy details of a host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the host is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the host is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``Host.Entropy.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            })

    def add(self,
            host,
            spec,
            ):
        """
        Adds additional entropy to the pool. This API will accept maximum
        (:attr:`ExternalPool.Info.capacity` -
        :attr:`ExternalPool.Info.currently_available`) bytes of entropy. Extra
        entropy data sent will be discarded. This method was added in vSphere
        API 8.0.1.0.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  spec: :class:`ExternalPool.AddSpec`
        :param spec: contains buffer of entropy data.
        :rtype: :class:`ExternalPool.AddResult`
        :return: Result of ``add`` method.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the host is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the host is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``Host.Entropy.Write``.
        """
        return self._invoke('add',
                            {
                            'host': host,
                            'spec': spec,
                            })
class _ExternalPoolStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
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
            url_template='/vcenter/host/{host}/entropy/external-pool',
            path_variables={
                'host': 'host',
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

        # properties for add operation
        add_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'spec': type.ReferenceType(__name__, 'ExternalPool.AddSpec'),
        })
        add_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        add_input_value_validator_list = [
        ]
        add_output_validator_list = [
        ]
        add_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/host/{host}/entropy/external-pool',
            request_body_parameter='spec',
            path_variables={
                'host': 'host',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'add',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'ExternalPool.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'add': {
                'input_type': add_input_type,
                'output_type': type.ReferenceType(__name__, 'ExternalPool.AddResult'),
                'errors': add_error_dict,
                'input_value_validator_list': add_input_value_validator_list,
                'output_validator_list': add_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'add': add_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.host.entropy.external_pool',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'ExternalPool': ExternalPool,
    }

