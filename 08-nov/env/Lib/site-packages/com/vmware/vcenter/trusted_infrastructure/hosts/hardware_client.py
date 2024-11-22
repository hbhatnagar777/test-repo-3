# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.trusted_infrastructure.hosts.hardware.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware_client`` module
provides classes to manage trusted hardware.

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


class Tpm(VapiInterface):
    """
    The ``Tpm`` interface provides methods to get available Trusted Platform
    Module (TPM) information on a host. This class was added in vSphere API
    8.0.0.1.
    """
    RESOURCE_TYPE = "com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm"
    """
    Resource type for TPM. This class attribute was added in vSphere API 8.0.0.1.

    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _TpmStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``Tpm.Summary`` class contains information that summarizes a TPM. This
        class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     tpm=None,
                     major_version=None,
                     minor_version=None,
                     active=None,
                    ):
            """
            :type  tpm: :class:`str`
            :param tpm: A unique identifier for the TPM instance. This attribute was added
                in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm``.
            :type  major_version: :class:`long`
            :param major_version: The TPM major version number. This attribute was added in vSphere
                API 8.0.0.1.
            :type  minor_version: :class:`long`
            :param minor_version: The TPM minor version number. This attribute was added in vSphere
                API 8.0.0.1.
            :type  active: :class:`bool`
            :param active: The TPM status. 
                
                Inactive TPMs cannot be used for sealing or attestation.. This
                attribute was added in vSphere API 8.0.0.1.
            """
            self.tpm = tpm
            self.major_version = major_version
            self.minor_version = minor_version
            self.active = active
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.summary', {
            'tpm': type.IdType(resource_types='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm'),
            'major_version': type.IntegerType(),
            'minor_version': type.IntegerType(),
            'active': type.BooleanType(),
        },
        Summary,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Tpm.Info`` class contains information that describes a TPM device.
        This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     major_version=None,
                     minor_version=None,
                     active=None,
                     manufacturer=None,
                     model=None,
                     firmware_version=None,
                     banks=None,
                    ):
            """
            :type  major_version: :class:`long`
            :param major_version: The TPM major version number. This attribute was added in vSphere
                API 8.0.0.1.
            :type  minor_version: :class:`long`
            :param minor_version: The TPM minor version number. This attribute was added in vSphere
                API 8.0.0.1.
            :type  active: :class:`bool`
            :param active: The TPM status. 
                
                Inactive TPMs cannot be used for sealing or attestation.. This
                attribute was added in vSphere API 8.0.0.1.
            :type  manufacturer: :class:`str` or ``None``
            :param manufacturer: The TPM manufacturer. This attribute was added in vSphere API
                8.0.0.1.
                if None, manufacturer is not available.
            :type  model: :class:`str` or ``None``
            :param model: The TPM model. This attribute was added in vSphere API 8.0.0.1.
                if None, model is not available.
            :type  firmware_version: :class:`str` or ``None``
            :param firmware_version: The TPM firmware version. This attribute was added in vSphere API
                8.0.0.1.
                if None, firmware version is not available.
            :type  banks: :class:`list` of :class:`com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm_client.PcrBank`
            :param banks: The list of the PCR banks of the TPM device. This attribute was
                added in vSphere API 8.0.0.1.
            """
            self.major_version = major_version
            self.minor_version = minor_version
            self.active = active
            self.manufacturer = manufacturer
            self.model = model
            self.firmware_version = firmware_version
            self.banks = banks
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.info', {
            'major_version': type.IntegerType(),
            'minor_version': type.IntegerType(),
            'active': type.BooleanType(),
            'manufacturer': type.OptionalType(type.StringType()),
            'model': type.OptionalType(type.StringType()),
            'firmware_version': type.OptionalType(type.StringType()),
            'banks': type.ListType(type.ReferenceType('com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm_client', 'PcrBank')),
        },
        Info,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``Tpm.FilterSpec`` class contains attributes used to filter the results
        when listing configured TPMs. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     major_versions=None,
                     active=None,
                    ):
            """
            :type  major_versions: :class:`set` of :class:`long` or ``None``
            :param major_versions: The TPM major version number. This attribute was added in vSphere
                API 8.0.0.1.
                if None or empty, the result will not be filtered by version
                number.
            :type  active: :class:`bool` or ``None``
            :param active: The TPM status. This attribute was added in vSphere API 8.0.0.1.
                if None, the result will not be filtered by status.
            """
            self.major_versions = major_versions
            self.active = active
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.filter_spec', {
            'major_versions': type.OptionalType(type.SetType(type.IntegerType())),
            'active': type.OptionalType(type.BooleanType()),
        },
        FilterSpec,
        False,
        None))



    def list(self,
             host,
             filter=None,
             ):
        """
        Return a list of configured TPMs on a host. This method was added in
        vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  filter: :class:`Tpm.FilterSpec` or ``None``
        :param filter: a filter for the returned list.
            if None, the behavior is equivalent to a :class:`Tpm.FilterSpec`
            with attributes None
        :rtype: :class:`list` of :class:`Tpm.Summary`
        :return: A list of configured TPMs.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if any argument is invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the host is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if too many requests are in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller is not authorized.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``Host.Tpm.Read``.
        """
        return self._invoke('list',
                            {
                            'host': host,
                            'filter': filter,
                            })

    def get(self,
            host,
            tpm,
            ):
        """
        Get the TPM details on a host. This method was added in vSphere API
        8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  tpm: :class:`str`
        :param tpm: the TPM identifier.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm``.
        :rtype: :class:`Tpm.Info`
        :return: The TPM info.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if any argument is invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the TPM is not found or host is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if too many requests are in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller is not authorized.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``Host.Tpm.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            'tpm': tpm,
                            })
class _TpmStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'filter': type.OptionalType(type.ReferenceType(__name__, 'Tpm.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
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
            url_template='/vcenter/trusted-infrastructure/hosts/{host}/hardware/tpm',
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

        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'tpm': type.IdType(resource_types='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
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
            url_template='/vcenter/trusted-infrastructure/hosts/{host}/hardware/tpm/{tpm}',
            path_variables={
                'host': 'host',
                'tpm': 'tpm',
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
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'Tpm.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Tpm.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Tpm': Tpm,
        'tpm': 'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm_client.StubFactory',
    }

