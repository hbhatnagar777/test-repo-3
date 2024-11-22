# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.phm.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.phm_client`` module provides classes for proactive
hardware management (PHM) in vCenter.

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


class About(VapiInterface):
    """
    The ``About`` class returns information about the proactive hardware
    management API.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.phm.about'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _AboutStub)
        self._VAPI_OPERATION_IDS = {}

    class Info(VapiStruct):
        """
        About info of proactive hardware management

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     version=None,
                     api_version=None,
                    ):
            """
            :type  version: :class:`str`
            :param version: Proactive hardware management product version
            :type  api_version: :class:`str`
            :param api_version: Proactive hardware management API version
            """
            self.version = version
            self.api_version = api_version
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.about.info', {
            'version': type.StringType(),
            'api_version': type.StringType(),
        },
        Info,
        False,
        None))



    def get(self):
        """
        Retrieves Proactive Hardware Management(PHM) about information
        including product and API version.


        :rtype: :class:`About.Info`
        :return: Proactive Hardware Management about information
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if user has not provided adequate credentials.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if PHM service hits an internal error.
        """
        return self._invoke('get', None)
class HardwareSupportManagers(VapiInterface):
    """
    The ``HardwareSupportManagers`` class contains operation for managing
    registrations of hardware support managers (HSM). Each vendor's HSM needs
    to register itself with PHM in order to provide proactive hardware
    management with vCenter.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.phm.hardware_support_managers'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _HardwareSupportManagersStub)
        self._VAPI_OPERATION_IDS = {}

    class HealthUpdateInfoSeverity(Enum):
        """
        The ``HardwareSupportManagers.HealthUpdateInfoSeverity`` class defines
        severity levels for all ``HardwareSupportManagers.HealthUpdateInfo``.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        CRITICAL = None
        """
        Critical severity

        """
        WARNING = None
        """
        Warning severity

        """
        INFO = None
        """
        Info severity

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`HealthUpdateInfoSeverity` instance.
            """
            Enum.__init__(string)

    HealthUpdateInfoSeverity._set_values({
        'CRITICAL': HealthUpdateInfoSeverity('CRITICAL'),
        'WARNING': HealthUpdateInfoSeverity('WARNING'),
        'INFO': HealthUpdateInfoSeverity('INFO'),
    })
    HealthUpdateInfoSeverity._set_binding_type(type.EnumType(
        'com.vmware.vcenter.phm.hardware_support_managers.health_update_info_severity',
        HealthUpdateInfoSeverity))


    class HealthUpdateInfoPurpose(Enum):
        """
        The ``HardwareSupportManagers.HealthUpdateInfoPurpose`` class defines
        purpose categories for all ``HardwareSupportManagers.HealthUpdateInfo``.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        FAILURE = None
        """
        Indicates failure of a hardware component.

        """
        PREDICTIVE_FAILURE = None
        """
        Indicates predictive failure of a hardware component.

        """
        SOFTWARE_INCOMPATIBILITY = None
        """
        Indicates software incompatiblity.

        """
        SECURITY_INFORMATION = None
        """
        Indicates security related information.

        """
        HEALTH_STATISTIC = None
        """
        Indicates health statistic information about a hardware component.

        """
        MISCELLANEOUS = None
        """
        Indicates unclassified purpose category.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`HealthUpdateInfoPurpose` instance.
            """
            Enum.__init__(string)

    HealthUpdateInfoPurpose._set_values({
        'FAILURE': HealthUpdateInfoPurpose('FAILURE'),
        'PREDICTIVE_FAILURE': HealthUpdateInfoPurpose('PREDICTIVE_FAILURE'),
        'SOFTWARE_INCOMPATIBILITY': HealthUpdateInfoPurpose('SOFTWARE_INCOMPATIBILITY'),
        'SECURITY_INFORMATION': HealthUpdateInfoPurpose('SECURITY_INFORMATION'),
        'HEALTH_STATISTIC': HealthUpdateInfoPurpose('HEALTH_STATISTIC'),
        'MISCELLANEOUS': HealthUpdateInfoPurpose('MISCELLANEOUS'),
    })
    HealthUpdateInfoPurpose._set_binding_type(type.EnumType(
        'com.vmware.vcenter.phm.hardware_support_managers.health_update_info_purpose',
        HealthUpdateInfoPurpose))


    class HealthUpdateInfoComponentCategory(Enum):
        """
        The ``HardwareSupportManagers.HealthUpdateInfoComponentCategory`` class
        defines target component categories for all
        ``HardwareSupportManagers.HealthUpdateInfo``.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        COMPUTE = None
        """
        Target component is part of compute resources.

        """
        MEMORY = None
        """
        Target component is part of memory resources.

        """
        STORAGE = None
        """
        Target component is part of storage resources.

        """
        NETWORK = None
        """
        Target component is part of network resources.

        """
        BOOT = None
        """
        Target component is part of boot drives.

        """
        MISCELLANEOUS = None
        """
        Target componet is something else other than the above categories.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`HealthUpdateInfoComponentCategory` instance.
            """
            Enum.__init__(string)

    HealthUpdateInfoComponentCategory._set_values({
        'COMPUTE': HealthUpdateInfoComponentCategory('COMPUTE'),
        'MEMORY': HealthUpdateInfoComponentCategory('MEMORY'),
        'STORAGE': HealthUpdateInfoComponentCategory('STORAGE'),
        'NETWORK': HealthUpdateInfoComponentCategory('NETWORK'),
        'BOOT': HealthUpdateInfoComponentCategory('BOOT'),
        'MISCELLANEOUS': HealthUpdateInfoComponentCategory('MISCELLANEOUS'),
    })
    HealthUpdateInfoComponentCategory._set_binding_type(type.EnumType(
        'com.vmware.vcenter.phm.hardware_support_managers.health_update_info_component_category',
        HealthUpdateInfoComponentCategory))


    class HealthUpdateInfo(VapiStruct):
        """
        The ``HardwareSupportManagers.HealthUpdateInfo`` class defines a type of
        health update to be supported.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     id=None,
                     description=None,
                     severity=None,
                     purpose=None,
                     component_category=None,
                    ):
            """
            :type  id: :class:`str`
            :param id: Unique identifier
            :type  description: :class:`str`
            :param description: Message key for the message that provides important information
                about the health update info.
            :type  severity: :class:`HardwareSupportManagers.HealthUpdateInfoSeverity`
            :param severity: Severity
            :type  purpose: :class:`HardwareSupportManagers.HealthUpdateInfoPurpose`
            :param purpose: Functional purpose category
            :type  component_category: :class:`HardwareSupportManagers.HealthUpdateInfoComponentCategory`
            :param component_category: Target component category
            """
            self.id = id
            self.description = description
            self.severity = severity
            self.purpose = purpose
            self.component_category = component_category
            VapiStruct.__init__(self)


    HealthUpdateInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.hardware_support_managers.health_update_info', {
            'id': type.StringType(),
            'description': type.StringType(),
            'severity': type.ReferenceType(__name__, 'HardwareSupportManagers.HealthUpdateInfoSeverity'),
            'purpose': type.ReferenceType(__name__, 'HardwareSupportManagers.HealthUpdateInfoPurpose'),
            'component_category': type.ReferenceType(__name__, 'HardwareSupportManagers.HealthUpdateInfoComponentCategory'),
        },
        HealthUpdateInfo,
        False,
        None))


    class HealthUpdateInfoConfig(VapiStruct):
        """
        The ``HardwareSupportManagers.HealthUpdateInfoConfig`` class specifies
        default enablement on a supported
        ``HardwareSupportManagers.HealthUpdateInfo``.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     health_update_info=None,
                     default_enabled=None,
                    ):
            """
            :type  health_update_info: :class:`HardwareSupportManagers.HealthUpdateInfo`
            :param health_update_info: Indicate a supported ``HardwareSupportManagers.HealthUpdateInfo``.
            :type  default_enabled: :class:`bool`
            :param default_enabled: Indicate whether or not the
                ``HardwareSupportManagers.HealthUpdateInfo`` is enabled by default.
            """
            self.health_update_info = health_update_info
            self.default_enabled = default_enabled
            VapiStruct.__init__(self)


    HealthUpdateInfoConfig._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.hardware_support_managers.health_update_info_config', {
            'health_update_info': type.ReferenceType(__name__, 'HardwareSupportManagers.HealthUpdateInfo'),
            'default_enabled': type.BooleanType(),
        },
        HealthUpdateInfoConfig,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``HardwareSupportManagers.CreateSpec`` class provides a new hardware
        support manager registration data for creating a registration entry, see
        :func:`HardwareSupportManagers.create`.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     key=None,
                     base_url=None,
                     server_certificate=None,
                     health_update_info_default_configs=None,
                    ):
            """
            :type  key: :class:`str`
            :param key: Globally unique key identifier of the HSM registered with PHM
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.phm.HardwareSupportManager``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.phm.HardwareSupportManager``.
            :type  base_url: :class:`str`
            :param base_url: The full URL path for all HSM endpoints. (e.g.
                https://{hsm_api_host}/vsphere-proactive-hw-mgmt)
            :type  server_certificate: :class:`str`
            :param server_certificate: The full unabbreviated certificate used by HSM API host in PEM
                format. The PEM string must contain only the end-entity (leaf)
                certificate of the certificate chain of trust. It must NOT contain
                any private keys or anything else except a single x509 certificate.
            :type  health_update_info_default_configs: :class:`list` of :class:`HardwareSupportManagers.HealthUpdateInfoConfig`
            :param health_update_info_default_configs: The default configuration on a list of supported
                ``HardwareSupportManagers.HealthUpdateInfo`` and their enablements.
            """
            self.key = key
            self.base_url = base_url
            self.server_certificate = server_certificate
            self.health_update_info_default_configs = health_update_info_default_configs
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.hardware_support_managers.create_spec', {
            'key': type.IdType(resource_types='com.vmware.vcenter.phm.HardwareSupportManager'),
            'base_url': type.StringType(),
            'server_certificate': type.StringType(),
            'health_update_info_default_configs': type.ListType(type.ReferenceType(__name__, 'HardwareSupportManagers.HealthUpdateInfoConfig')),
        },
        CreateSpec,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``HardwareSupportManagers.Info`` class contains an existing hardware
        support manager registration data, see :func:`HardwareSupportManagers.get`.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     base_url=None,
                     server_certificate=None,
                     health_update_info_default_configs=None,
                    ):
            """
            :type  base_url: :class:`str`
            :param base_url: The full URL path for all HSM endpoints. (e.g.
                https://{hsm_api_host}/vsphere-proactive-hw-mgmt)
            :type  server_certificate: :class:`str`
            :param server_certificate: The full unabbreviated certificate used by HSM API host in PEM
                format. The PEM string must contain only the end-entity (leaf)
                certificate of the certificate chain of trust. It must NOT contain
                any private keys or anything else except a single x509 certificate.
            :type  health_update_info_default_configs: :class:`list` of :class:`HardwareSupportManagers.HealthUpdateInfoConfig`
            :param health_update_info_default_configs: The default configuration on a list of supported
                ``HardwareSupportManagers.HealthUpdateInfo`` and their enablements.
            """
            self.base_url = base_url
            self.server_certificate = server_certificate
            self.health_update_info_default_configs = health_update_info_default_configs
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.hardware_support_managers.info', {
            'base_url': type.StringType(),
            'server_certificate': type.StringType(),
            'health_update_info_default_configs': type.ListType(type.ReferenceType(__name__, 'HardwareSupportManagers.HealthUpdateInfoConfig')),
        },
        Info,
        False,
        None))


    class ListResult(VapiStruct):
        """
        The ``HardwareSupportManagers.ListResult`` class contains a list of
        registered hardware support manager keys, see
        :func:`HardwareSupportManagers.list`.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     registered_hsm_keys=None,
                    ):
            """
            :type  registered_hsm_keys: :class:`list` of :class:`str`
            :param registered_hsm_keys: List of registered HSM keys.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.phm.HardwareSupportManager``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.phm.HardwareSupportManager``.
            """
            self.registered_hsm_keys = registered_hsm_keys
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.hardware_support_managers.list_result', {
            'registered_hsm_keys': type.ListType(type.IdType()),
        },
        ListResult,
        False,
        None))


    class SetSpec(VapiStruct):
        """
        The ``HardwareSupportManagers.SetSpec`` class provides a new hardware
        support manager registration data for replacing an existing registration
        entry, see :func:`HardwareSupportManagers.set`.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     base_url=None,
                     server_certificate=None,
                     health_update_info_default_configs=None,
                    ):
            """
            :type  base_url: :class:`str`
            :param base_url: The full URL path for all HSM endpoints. (e.g.
                https://{hsm_api_host}/vsphere-proactive-hw-mgmt)
            :type  server_certificate: :class:`str`
            :param server_certificate: The full unabbreviated certificate used by HSM API host in PEM
                format. The PEM string must contain only the end-entity (leaf)
                certificate of the certificate chain of trust. It must NOT contain
                any private keys or anything else except a single x509 certificate.
            :type  health_update_info_default_configs: :class:`list` of :class:`HardwareSupportManagers.HealthUpdateInfoConfig`
            :param health_update_info_default_configs: The default configuration on a list of supported
                ``HardwareSupportManagers.HealthUpdateInfo`` and their enablements.
            """
            self.base_url = base_url
            self.server_certificate = server_certificate
            self.health_update_info_default_configs = health_update_info_default_configs
            VapiStruct.__init__(self)


    SetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.phm.hardware_support_managers.set_spec', {
            'base_url': type.StringType(),
            'server_certificate': type.StringType(),
            'health_update_info_default_configs': type.ListType(type.ReferenceType(__name__, 'HardwareSupportManagers.HealthUpdateInfoConfig')),
        },
        SetSpec,
        False,
        None))



    def create(self,
               spec,
               ):
        """
        Register an HSM with PHM.

        :type  spec: :class:`HardwareSupportManagers.CreateSpec`
        :param spec: Registration creation spec
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if PHM fails to process input ``spec``.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the HSM is already registered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if user has not provided adequate credentials.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if PHM service hits an internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if PHM service is not able to handle request.
        """
        return self._invoke('create',
                            {
                            'spec': spec,
                            })

    def get(self,
            key,
            ):
        """
        Retrieve registration information for a specified HSM.

        :type  key: :class:`str`
        :param key: identifier of a hardware support manager
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.phm.HardwareSupportManager``.
        :rtype: :class:`HardwareSupportManagers.Info`
        :return: Registration information for a specified HSM.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if specified ``key`` cannot be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if user has not provided adequate credentials.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if PHM service hits an internal error.
        """
        return self._invoke('get',
                            {
                            'key': key,
                            })

    def list(self):
        """
        Get ``HardwareSupportManagers.ListResult`` class, the list of
        registered HSM keys.


        :rtype: :class:`HardwareSupportManagers.ListResult`
        :return: ``HardwareSupportManagers.ListResult`` contains all registered HSM
            keys.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if user has not provided adequate credentials.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if PHM service hits an internal error.
        """
        return self._invoke('list', None)

    def set(self,
            key,
            spec,
            ):
        """
        Set an existing HSM registration with PHM.

        :type  key: :class:`str`
        :param key: HSM key for the HSM to be set
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.phm.HardwareSupportManager``.
        :type  spec: :class:`HardwareSupportManagers.SetSpec`
        :param spec: Registration update spec
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if PHM fails to process input ``spec``.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if specified HSM ``key`` cannot be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if user has not provided adequate credentials.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if PHM service hits an internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if PHM service is not able to handle request.
        """
        return self._invoke('set',
                            {
                            'key': key,
                            'spec': spec,
                            })

    def delete(self,
               key,
               ):
        """
        Unregister an existing HSM with PHM.

        :type  key: :class:`str`
        :param key: HSM key for the HSM to be updated
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.phm.HardwareSupportManager``.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if specified HSM ``key`` cannot be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if user has not provided adequate credentials.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if PHM service hits an internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if PHM service is not able to handle request.
        """
        return self._invoke('delete',
                            {
                            'key': key,
                            })
class _AboutStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {})
        get_error_dict = {
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
            url_template='/vcenter/phm/about',
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
                'output_type': type.ReferenceType(__name__, 'About.Info'),
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
            self, iface_name='com.vmware.vcenter.phm.about',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _HardwareSupportManagersStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'HardwareSupportManagers.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/phm/hardware-support-managers',
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
            url_template='/vcenter/phm/hardware-support-managers/{key}',
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
        list_input_type = type.StructType('operation-input', {})
        list_error_dict = {
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
            url_template='/vcenter/phm/hardware-support-managers',
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
            'key': type.IdType(resource_types='com.vmware.vcenter.phm.HardwareSupportManager'),
            'spec': type.ReferenceType(__name__, 'HardwareSupportManagers.SetSpec'),
        })
        set_error_dict = {
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/vcenter/phm/hardware-support-managers/{key}',
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

        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'key': type.IdType(resource_types='com.vmware.vcenter.phm.HardwareSupportManager'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vcenter/phm/hardware-support-managers/{key}',
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
            'create': {
                'input_type': create_input_type,
                'output_type': type.VoidType(),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'HardwareSupportManagers.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ReferenceType(__name__, 'HardwareSupportManagers.ListResult'),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'set': {
                'input_type': set_input_type,
                'output_type': type.VoidType(),
                'errors': set_error_dict,
                'input_value_validator_list': set_input_value_validator_list,
                'output_validator_list': set_output_validator_list,
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
        }
        rest_metadata = {
            'create': create_rest_metadata,
            'get': get_rest_metadata,
            'list': list_rest_metadata,
            'set': set_rest_metadata,
            'delete': delete_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.phm.hardware_support_managers',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'About': About,
        'HardwareSupportManagers': HardwareSupportManagers,
        'hardware_support_managers': 'com.vmware.vcenter.phm.hardware_support_managers_client.StubFactory',
    }

