# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.identity.broker.tenants.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.identity.broker.tenants_client`` module provides
classes to manage external authentication broker tenant data.

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


class TokenInfo(VapiStruct):
    """
    The ``TokenInfo`` class contains detailed information about the tenant
    token. This class was added in vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """
    BEARER_TOKEN_METHOD_TYPE = "Bearer"
    """
    Class attribute indicating that the security token is a bearer token. This
    class attribute was added in vSphere API 8.0.1.0.

    """




    def __init__(self,
                 token_type=None,
                 access_token=None,
                 expires_in=None,
                ):
        """
        :type  token_type: :class:`str`
        :param token_type: The type of the token issued. The access token type provides the
            client with the information required to successfully utilize the
            access token to make a protected resource request (along with
            type-specific attributes). The client MUST NOT use an access token
            if it does not understand the token type. 
            
            "Bearer" token type as defined in RFC 6750 is supported.. This
            attribute was added in vSphere API 8.0.1.0.
        :type  access_token: :class:`str`
        :param access_token: Tenant client access token issued by the authorization server. This
            attribute was added in vSphere API 8.0.1.0.
        :type  expires_in: :class:`long` or ``None``
        :param expires_in: The lifetime in seconds of the access token. For example, the value
            "3600" denotes that the access token will expire in one hour from
            the time the response was generated. This attribute was added in
            vSphere API 8.0.1.0.
            None if not applicable for issued token.
        """
        self.token_type = token_type
        self.access_token = access_token
        self.expires_in = expires_in
        VapiStruct.__init__(self)


TokenInfo._set_binding_type(type.StructType(
    'com.vmware.vcenter.identity.broker.tenants.token_info', {
        'token_type': type.StringType(),
        'access_token': type.StringType(),
        'expires_in': type.OptionalType(type.IntegerType()),
    },
    TokenInfo,
    False,
    None))



class AdminClient(VapiInterface):
    """
    The ``AdminClient`` interface provides methods to read the token info of
    tenant admin client. The tenant client belongs to the pre-configured
    tenant(s), that were created at bootstrap of vcenter trustmanagement
    service. The tenant admin client tokens can be used to perform API
    invocations within a tenant entity. This class was added in vSphere API
    8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.identity.broker.tenants.admin_client'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _AdminClientStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            tenant,
            ):
        """
        Returns the tenant admin client token info associated with
        pre-configured tenant(s) owned by vcenter trustmanagment service. This
        method was added in vSphere API 8.0.1.0.

        :type  tenant: :class:`str`
        :param tenant: The tenant name for which the admin client token needs to be
            returned.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.identity.broker.tenant``.
        :rtype: :class:`TokenInfo`
        :return: :class:`TokenInfo` class that contains a newly issued tenant admin
            client token.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if any other error occurs.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if no tenant owned by vcenter trustmanagment service, with the
            input parameter found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if not authorized to invoke the operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIdentityProviders.Manage``.
        """
        return self._invoke('get',
                            {
                            'tenant': tenant,
                            })
class OperatorClient(VapiInterface):
    """
    The ``OperatorClient`` interface provides methods to read the token info of
    operator client. The operator client belongs to the pre-configured HWS
    tenant, that was created at bootstrap/installation of broker. The operator
    client tokens can be used to call the tenant management APIs like create,
    get and delete of tenant entity. This class was added in vSphere API
    8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.identity.broker.tenants.operator_client'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _OperatorClientStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self):
        """
        Return the operator client token info in Broker. The operator client
        was created at bootstrap or installation of broker. This token can be
        used to manage tenant entity APIs. This method was added in vSphere API
        8.0.1.0.


        :rtype: :class:`TokenInfo`
        :return: :class:`TokenInfo` class that contains a newly issued operator
            client token.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if any other error occurs.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if no operator client details found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if not authorized to invoke the operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIdentityProviders.Manage``.
        """
        return self._invoke('get', None)
class _AdminClientStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'tenant': type.IdType(resource_types='com.vmware.vcenter.identity.broker.tenant'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
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
            url_template='/vcenter/identity/broker/tenants/{tenant}/admin-client',
            path_variables={
                'tenant': 'tenant',
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
                'output_type': type.ReferenceType(__name__, 'TokenInfo'),
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
            self, iface_name='com.vmware.vcenter.identity.broker.tenants.admin_client',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _OperatorClientStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {})
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
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
            url_template='/vcenter/identity/broker/tenants/operator-client',
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
                'output_type': type.ReferenceType(__name__, 'TokenInfo'),
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
            self, iface_name='com.vmware.vcenter.identity.broker.tenants.operator_client',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'AdminClient': AdminClient,
        'OperatorClient': OperatorClient,
    }

