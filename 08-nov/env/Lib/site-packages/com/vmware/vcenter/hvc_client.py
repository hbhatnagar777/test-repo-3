# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.hvc.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.hvc_client`` module provides classes to manage hybrid
links between a local and remote Platform Service Controller. Usage beyond
VMware Cloud on AWS is not supported.

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


class Links(VapiInterface):
    """
    The ``Links`` class provides methods to create, delete, get information,
    and list hybrid links between the local and foreign Platform Service
    Controller (PSC). Usage beyond VMware Cloud on AWS is not supported.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.hvc.links'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _LinksStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``Links.Summary`` class contains information about the hybrid link.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     link=None,
                     display_name=None,
                    ):
            """
            :type  link: :class:`str`
            :param link: Unique identifier for the link.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.hvc.Links``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.vcenter.hvc.Links``.
            :type  display_name: :class:`str`
            :param display_name: The display name is set to the domain name which was set during
                create.
            """
            self.link = link
            self.display_name = display_name
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.hvc.links.summary', {
            'link': type.IdType(resource_types='com.vmware.vcenter.hvc.Links'),
            'display_name': type.StringType(),
        },
        Summary,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``Links.CreateSpec`` class is the specification used for the hybrid
        link creation.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     psc_hostname=None,
                     port=None,
                     domain_name=None,
                     username=None,
                     password=None,
                     ssl_thumbprint=None,
                     admin_groups=None,
                    ):
            """
            :type  psc_hostname: :class:`str`
            :param psc_hostname: The PSC hostname for the domain to be linked.
            :type  port: :class:`str` or ``None``
            :param port: The HTTPS port of the PSC to be linked.
                If None 443 will be used as default.
            :type  domain_name: :class:`str`
            :param domain_name: The domain to which the PSC belongs.
            :type  username: :class:`str`
            :param username: The administrator username of the PSC.
            :type  password: :class:`str`
            :param password: The administrator password of the PSC.
            :type  ssl_thumbprint: :class:`str` or ``None``
            :param ssl_thumbprint: The ssl thumbprint of the server.
                if None no thumbprint is passed.
            :type  admin_groups: :class:`set` of :class:`str` or ``None``
            :param admin_groups: List of groups to be added to enable administrator access to.
                if None administrator access will not be set.
            """
            self.psc_hostname = psc_hostname
            self.port = port
            self.domain_name = domain_name
            self.username = username
            self.password = password
            self.ssl_thumbprint = ssl_thumbprint
            self.admin_groups = admin_groups
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.hvc.links.create_spec', {
            'psc_hostname': type.StringType(),
            'port': type.OptionalType(type.StringType()),
            'domain_name': type.StringType(),
            'username': type.StringType(),
            'password': type.SecretType(),
            'ssl_thumbprint': type.OptionalType(type.StringType()),
            'admin_groups': type.OptionalType(type.SetType(type.StringType())),
        },
        CreateSpec,
        False,
        None))


    class CertificateInfo(VapiStruct):
        """
        The ``Links.CertificateInfo`` class contains information about the SSL
        certificate for a destination PSC endpoint.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     ssl_thumbprint=None,
                    ):
            """
            :type  ssl_thumbprint: :class:`str`
            :param ssl_thumbprint: The SHA-256 thumbprint of the SSL certificate for the destination
                PSC endpoint.
            """
            self.ssl_thumbprint = ssl_thumbprint
            VapiStruct.__init__(self)


    CertificateInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.hvc.links.certificate_info', {
            'ssl_thumbprint': type.StringType(),
        },
        CertificateInfo,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Links.Info`` class contains information about link.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'connection_health_status',
                {
                    'UNHEALTHY' : [('health_status_message', True)],
                    'HEALTHY' : [],
                }
            ),
        ]



        def __init__(self,
                     connection_health_status=None,
                     health_status_message=None,
                    ):
            """
            :type  connection_health_status: :class:`Links.Info.HealthStatus` or ``None``
            :param connection_health_status: Health status of the connection
            :type  health_status_message: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param health_status_message: Localizable messages associated with health status
                This attribute is optional and it is only relevant when the value
                of ``connectionHealthStatus`` is
                :attr:`Links.Info.HealthStatus.UNHEALTHY`.
            """
            self.connection_health_status = connection_health_status
            self.health_status_message = health_status_message
            VapiStruct.__init__(self)


        class HealthStatus(Enum):
            """
            The ``Links.Info.HealthStatus`` class defines the possible states for
            health of a link.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            HEALTHY = None
            """
            Connection is healthy

            """
            UNHEALTHY = None
            """
            Connection issues will need to be remediated

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`HealthStatus` instance.
                """
                Enum.__init__(string)

        HealthStatus._set_values({
            'HEALTHY': HealthStatus('HEALTHY'),
            'UNHEALTHY': HealthStatus('UNHEALTHY'),
        })
        HealthStatus._set_binding_type(type.EnumType(
            'com.vmware.vcenter.hvc.links.info.health_status',
            HealthStatus))

    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.hvc.links.info', {
            'connection_health_status': type.OptionalType(type.ReferenceType(__name__, 'Links.Info.HealthStatus')),
            'health_status_message': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        Info,
        False,
        None))


    class Credentials(VapiStruct):
        """
        The ``Links.Credentials`` class specifies user credentials to make a
        successful connection to remote endpoint

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     user_name=None,
                     password=None,
                    ):
            """
            :type  user_name: :class:`str`
            :param user_name: Name of the user to authenticate
            :type  password: :class:`str`
            :param password: Password for the user.
            """
            self.user_name = user_name
            self.password = password
            VapiStruct.__init__(self)


    Credentials._set_binding_type(type.StructType(
        'com.vmware.vcenter.hvc.links.credentials', {
            'user_name': type.StringType(),
            'password': type.SecretType(),
        },
        Credentials,
        False,
        None))



    def create(self,
               spec,
               ):
        """
        Creates a new hybrid link between the local and foreign PSC. Usage
        beyond VMware Cloud on AWS is not supported.

        :type  spec: :class:`Links.CreateSpec`
        :param spec: Specification for the new link to be created.
        :rtype: :class:`str`
        :return: The identifier of the newly linked domain.
            The return value will be an identifier for the resource type:
            ``com.vmware.vcenter.hvc.Links``.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            If the link already exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the values of any of the attributes of the ``spec`` parameter
            are not valid.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the PSC or the VC version is not supported.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the user is not authorized.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``HLM.Manage``.
        """
        return self._invoke('create',
                            {
                            'spec': spec,
                            })

    def delete(self,
               link,
               ):
        """
        Deletes an existing hybrid link. This API should be used when unlink is
        initiated from Cloud Gateway.

        :type  link: :class:`str`
        :param link: Identifier of the hybrid link.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.hvc.Links``.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If the hybrid link associated with ``link`` does not exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the user is not authorized.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``HLM.Manage``.
        """
        return self._invoke('delete',
                            {
                            'link': link,
                            })

    def delete_with_credentials(self,
                                link,
                                credentials=None,
                                ):
        """
        Deletes an existing hybrid link. This API should be used when unlink is
        initiated from cloud vCenter. Usage beyond VMware Cloud on AWS is not
        supported.

        :type  link: :class:`str`
        :param link: Identifier of the hybrid link.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.hvc.Links``.
        :type  credentials: :class:`Links.Credentials` or ``None``
        :param credentials: Credentials to use for authentication to the remote system.
            This parameter is currently required. In the future, it may become
            optional.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the hybrid link associated with ``link`` does not exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is not authorized.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``HLM.Manage``.
        """
        return self._invoke('delete_with_credentials',
                            {
                            'link': link,
                            'credentials': credentials,
                            })

    def list(self):
        """
        Enumerates the list of registered hybrid links. Usage beyond VMware
        Cloud on AWS is not supported.


        :rtype: :class:`list` of :class:`Links.Summary`
        :return: The :class:`list` of hybrid link information.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        """
        return self._invoke('list', None)

    def get(self,
            link,
            ):
        """
        Gets information for a link. Usage beyond VMware Cloud on AWS is not
        supported.

        :type  link: :class:`str`
        :param link: Unique identifier of the link.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.hvc.Links``.
        :rtype: :class:`Links.Info`
        :return: Information about the link.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the hybrid link associated with ``link`` does not exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is not authorized to perform this operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceBusy` 
            if the service is busy.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``System.Read``.
        """
        return self._invoke('get',
                            {
                            'link': link,
                            })
class _LinksStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Links.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unverified_peer':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnverifiedPeer'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/hvc/links',
            path_variables={
            },
             header_parameters={
               },
            query_parameters={
            },
            content_type='application/json'
        )

        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'link': type.IdType(resource_types='com.vmware.vcenter.hvc.Links'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/hvc/links/{link_id}',
            path_variables={
                'link': 'link_id',
            },
             header_parameters={
               },
            query_parameters={
            },
            content_type='application/json'
        )

        # properties for delete_with_credentials operation
        delete_with_credentials_input_type = type.StructType('operation-input', {
            'link': type.IdType(resource_types='com.vmware.vcenter.hvc.Links'),
            'credentials': type.OptionalType(type.ReferenceType(__name__, 'Links.Credentials')),
        })
        delete_with_credentials_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        delete_with_credentials_input_value_validator_list = [
        ]
        delete_with_credentials_output_validator_list = [
        ]
        delete_with_credentials_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/hvc/links/{link}',
            path_variables={
                'link': 'link',
            },
             header_parameters={
                 },
            query_parameters={
            }
        )

        # properties for list operation
        list_input_type = type.StructType('operation-input', {})
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/hvc/links',
            path_variables={
            },
             header_parameters={
             },
            query_parameters={
            },
            content_type='application/json'
        )

        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'link': type.IdType(resource_types='com.vmware.vcenter.hvc.Links'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.resource_busy':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceBusy'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/hvc/links/{link}',
            path_variables={
                'link': 'link',
            },
             header_parameters={
               },
            query_parameters={
            }
        )

        operations = {
            'create': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.vcenter.hvc.Links'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
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
            'delete_with_credentials': {
                'input_type': delete_with_credentials_input_type,
                'output_type': type.VoidType(),
                'errors': delete_with_credentials_error_dict,
                'input_value_validator_list': delete_with_credentials_input_value_validator_list,
                'output_validator_list': delete_with_credentials_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'Links.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Links.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'create': create_rest_metadata,
            'delete': delete_rest_metadata,
            'delete_with_credentials': delete_with_credentials_rest_metadata,
            'list': list_rest_metadata,
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.hvc.links',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Links': Links,
        'management': 'com.vmware.vcenter.hvc.management_client.StubFactory',
    }

