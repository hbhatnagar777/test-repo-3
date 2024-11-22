# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.appliance.tls.
#---------------------------------------------------------------------------

"""
The ``com.vmware.appliance.tls_client`` module provides classes for managing
the TLS Profiles.

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


class Profiles(VapiInterface):
    """
    ``Profiles`` class provides methods APIs to list the details of available
    standard TLS Profiles. This class was added in vSphere API 8.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.appliance.tls.profiles'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ProfilesStub)
        self._VAPI_OPERATION_IDS = {}

    class ProtocolVersionInfo(VapiStruct):
        """
        The ``Profiles.ProtocolVersionInfo`` class contains the information about
        the TLS protocol version and its ciphers. This class was added in vSphere
        API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     version=None,
                     ciphers=None,
                    ):
            """
            :type  version: :class:`str`
            :param version: Defines the TLS protocol version. This attribute was added in
                vSphere API 8.0.3.0.
            :type  ciphers: :class:`list` of :class:`str`
            :param ciphers: Defines the TLS protocol ciphers in IANA form. This attribute was
                added in vSphere API 8.0.3.0.
            """
            self.version = version
            self.ciphers = ciphers
            VapiStruct.__init__(self)


    ProtocolVersionInfo._set_binding_type(type.StructType(
        'com.vmware.appliance.tls.profiles.protocol_version_info', {
            'version': type.StringType(),
            'ciphers': type.ListType(type.StringType()),
        },
        ProtocolVersionInfo,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Profiles.Info`` class contains the information about the TLS Profile.
        This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     protocol_versions=None,
                     curves=None,
                     fips_enforced=None,
                    ):
            """
            :type  protocol_versions: :class:`list` of :class:`Profiles.ProtocolVersionInfo`
            :param protocol_versions: Defines the list of TLS protocol version and their ciphers. This
                attribute was added in vSphere API 8.0.3.0.
            :type  curves: :class:`list` of :class:`str`
            :param curves: Defines the TLS Profile curves in IANA form. This attribute was
                added in vSphere API 8.0.3.0.
            :type  fips_enforced: :class:`bool`
            :param fips_enforced: Indicates if FIPS 140-3 compliance is enforced for the TLS Profile.
                If FIPS is not enforced, some TLS features that have not been yet
                FIPS validated can be enabled by some crypto modules. If FIPS is
                enforced, non FIPS validated TLS features wont be in effect. This
                attribute was added in vSphere API 8.0.3.0.
            """
            self.protocol_versions = protocol_versions
            self.curves = curves
            self.fips_enforced = fips_enforced
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.appliance.tls.profiles.info', {
            'protocol_versions': type.ListType(type.ReferenceType(__name__, 'Profiles.ProtocolVersionInfo')),
            'curves': type.ListType(type.StringType()),
            'fips_enforced': type.BooleanType(),
        },
        Info,
        False,
        None))


    class ListItem(VapiStruct):
        """
        The ``Profiles.ListItem`` class contains the information about the standard
        profile name and their TLS configuration. This class was added in vSphere
        API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     profile=None,
                     info=None,
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
            :type  info: :class:`Profiles.Info`
            :param info: Contains information about the TLS Profile configuration. This
                attribute was added in vSphere API 8.0.3.0.
            """
            self.profile = profile
            self.info = info
            VapiStruct.__init__(self)


    ListItem._set_binding_type(type.StructType(
        'com.vmware.appliance.tls.profiles.list_item', {
            'profile': type.IdType(resource_types='com.vmware.appliance.tls.profiles'),
            'info': type.ReferenceType(__name__, 'Profiles.Info'),
        },
        ListItem,
        False,
        None))


    class ListResult(VapiStruct):
        """
        The ``Profiles.ListResult`` class contains the information about the list
        of TLS Profiles. This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     profiles=None,
                    ):
            """
            :type  profiles: :class:`list` of :class:`Profiles.ListItem`
            :param profiles: Defines the list of available standard TLS Profiles. This attribute
                was added in vSphere API 8.0.3.0.
            """
            self.profiles = profiles
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.appliance.tls.profiles.list_result', {
            'profiles': type.ListType(type.ReferenceType(__name__, 'Profiles.ListItem')),
        },
        ListResult,
        False,
        None))



    def get(self,
            profile,
            ):
        """
        Gets the TLS parameters of a particular profile. This method was added
        in vSphere API 8.0.3.0.

        :type  profile: :class:`str`
        :param profile: Name of the TLS Profile for which the info is needed.
            The parameter must be an identifier for the resource type:
            ``com.vmware.appliance.tls.profiles``.
        :rtype: :class:`Profiles.Info`
        :return: The TLS parameters of the passed profile.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the session is not authenticated
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is not authorized. User needs to have operator
            privileges.
        """
        return self._invoke('get',
                            {
                            'profile': profile,
                            })

    def list(self):
        """
        Gets the list of all the available standard TLS Profiles and their
        configuration. This method was added in vSphere API 8.0.3.0.


        :rtype: :class:`Profiles.ListResult`
        :return: The list of all standard TLS Profiles and their configuration.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the session is not authenticated
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is not authorized. User needs to have operator
            privileges.
        """
        return self._invoke('list', None)
class _ProfilesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'profile': type.IdType(resource_types='com.vmware.appliance.tls.profiles'),
        })
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
            url_template='/appliance/tls/profiles/{profile}',
            path_variables={
                'profile': 'profile',
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
        list_input_type = type.StructType('operation-input', {})
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
            url_template='/appliance/tls/profiles',
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
                'output_type': type.ReferenceType(__name__, 'Profiles.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ReferenceType(__name__, 'Profiles.ListResult'),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.appliance.tls.profiles',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Profiles': Profiles,
        'manual_parameters': 'com.vmware.appliance.tls.manual_parameters_client.StubFactory',
        'profiles': 'com.vmware.appliance.tls.profiles_client.StubFactory',
    }

