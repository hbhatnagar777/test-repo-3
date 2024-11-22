# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.appliance.tls.manual_parameters.
#---------------------------------------------------------------------------

"""
The ``com.vmware.appliance.tls.manual_parameters_client`` module provides
classes for managing the manual/custom TLS parameters as an alternative for
using VMware-provided standard TLS Profiles.

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


class Global(VapiInterface):
    """
    ``Global`` class provides methods APIs to configure manual/custom TLS
    parameters. This class was added in vSphere API 8.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.appliance.tls.manual_parameters.global'
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

    class ProtocolVersionInfo(VapiStruct):
        """
        The ``Global.ProtocolVersionInfo`` class contains the information about the
        TLS protocol version and its ciphers. This class was added in vSphere API
        8.0.3.0.

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
        'com.vmware.appliance.tls.manual_parameters.global.protocol_version_info', {
            'version': type.StringType(),
            'ciphers': type.ListType(type.StringType()),
        },
        ProtocolVersionInfo,
        False,
        None))


    class SetSpec(VapiStruct):
        """
        The ``Global.SetSpec`` class contains the information about the TLS
        Profile. This class was added in vSphere API 8.0.3.0.

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
            :type  protocol_versions: :class:`list` of :class:`Global.ProtocolVersionInfo`
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


    SetSpec._set_binding_type(type.StructType(
        'com.vmware.appliance.tls.manual_parameters.global.set_spec', {
            'protocol_versions': type.ListType(type.ReferenceType(__name__, 'Global.ProtocolVersionInfo')),
            'curves': type.ListType(type.StringType()),
            'fips_enforced': type.BooleanType(),
        },
        SetSpec,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Global.Info`` class contains the information about a profile and its
        TLS configuration. This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     manual_active=None,
                     spec=None,
                    ):
            """
            :type  manual_active: :class:`bool`
            :param manual_active: Indicates if the current manual TLS parameters are activated for
                the appliance or standard TLS Profile is used instead of them. This
                attribute was added in vSphere API 8.0.3.0.
            :type  spec: :class:`Global.SetSpec`
            :param spec: Contains information about the configuration. This attribute was
                added in vSphere API 8.0.3.0.
            """
            self.manual_active = manual_active
            self.spec = spec
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.appliance.tls.manual_parameters.global.info', {
            'manual_active': type.BooleanType(),
            'spec': type.ReferenceType(__name__, 'Global.SetSpec'),
        },
        Info,
        False,
        None))



    def get(self):
        """
        Gets the current custom/manual global TLS parameters configured in the
        appliance. This method was added in vSphere API 8.0.3.0.


        :rtype: :class:`Global.Info`
        :return: The current protocol version, ciphers, and other TLS parameters.
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
            url_template='/appliance/tls/manual-parameters/global',
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
        }
        rest_metadata = {
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.appliance.tls.manual_parameters.global',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Global': Global,
    }

