# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.supervisor_services.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.namespace_management.supervisor_services_client``
module provides classes for managing supervisor services that are extensions to
the Supervisor.

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


class ClusterSupervisorServices(VapiInterface):
    """
    The ``ClusterSupervisorServices`` class provides methods to manage a
    Supervisor Service on the vSphere Supervisors. This class was added in
    vSphere API 7.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisor_services.cluster_supervisor_services'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ClusterSupervisorServicesStub)
        self._VAPI_OPERATION_IDS = {}

    class ConfigStatus(Enum):
        """
        The ``ClusterSupervisorServices.ConfigStatus`` class describes the status
        of reaching the desired state configuration for the Supervisor Service.
        This enumeration was added in vSphere API 7.0.3.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        CONFIGURING = None
        """
        The Supervisor Service is being installed. This class attribute was added
        in vSphere API 7.0.3.0.

        """
        REMOVING = None
        """
        The Supervisor Service is being deleted. This class attribute was added in
        vSphere API 7.0.3.0.

        """
        CONFIGURED = None
        """
        The Supervisor Service has been configured correctly (i.e. the provided
        YAML content has been applied successfully to the cluster). This class
        attribute was added in vSphere API 7.0.3.0.

        """
        ERROR = None
        """
        Failed to install the Supervisor Service, user intervention needed. This
        class attribute was added in vSphere API 7.0.3.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ConfigStatus` instance.
            """
            Enum.__init__(string)

    ConfigStatus._set_values({
        'CONFIGURING': ConfigStatus('CONFIGURING'),
        'REMOVING': ConfigStatus('REMOVING'),
        'CONFIGURED': ConfigStatus('CONFIGURED'),
        'ERROR': ConfigStatus('ERROR'),
    })
    ConfigStatus._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.supervisor_services.cluster_supervisor_services.config_status',
        ConfigStatus))


    class CreateSpec(VapiStruct):
        """
        The ``ClusterSupervisorServices.CreateSpec`` class provides a specification
        required to create a Supervisor Service on a vSphere Supervisor. This class
        was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor_service=None,
                     version=None,
                     service_config=None,
                     yaml_service_config=None,
                    ):
            """
            :type  supervisor_service: :class:`str`
            :param supervisor_service: Identifier of the Supervisor Service. This Supervisor Service must
                be in the ``ACTIVATED`` state. This attribute was added in vSphere
                API 7.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.SupervisorService``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.SupervisorService``.
            :type  version: :class:`str`
            :param version: Identifier of the Supervisor Service version which contains the
                service definition. This Supervisor Service version must be in the
                ``ACTIVATED`` state. This attribute was added in vSphere API
                7.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
            :type  service_config: (:class:`dict` of :class:`str` and :class:`str`) or ``None``
            :param service_config: A generic key-value map for additional configuration parameters
                required during service creation. As an example, a third party
                operator might reference a private registry using parameters such
                as "registryName" for the registry name, "registryUsername" and
                "registryPassword" for the registry credentials. This attribute was
                added in vSphere API 7.0.3.0.
                If None, no additional configuration parameters will be applied
                when installing a Supervisor Service in the vSphere Supervisor.
            :type  yaml_service_config: :class:`str` or ``None``
            :param yaml_service_config: A set of additional configuration parameters to be applied during
                service creation. These parameters should be formatted as a base64
                encoded YAML document. 
                
                Parameters should be :class:`set` in at most one of
                ``serviceConfig`` or ``yamlServiceConfig``, and not both. The
                ``yamlServiceConfig`` supports complex data types and nested
                properties.. This attribute was added in vSphere API 8.0.0.1.
                If None, no additional configuration parameters will be applied
                when installing a Supervisor Service in the vSphere Supervisor.
            """
            self.supervisor_service = supervisor_service
            self.version = version
            self.service_config = service_config
            self.yaml_service_config = yaml_service_config
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.cluster_supervisor_services.create_spec', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
            'service_config': type.OptionalType(type.MapType(type.StringType(), type.StringType())),
            'yaml_service_config': type.OptionalType(type.StringType()),
        },
        CreateSpec,
        False,
        None))


    class SetSpec(VapiStruct):
        """
        The ``ClusterSupervisorServices.SetSpec`` class provides a specification
        required to set a new configuration on a Supervisor Service in a vSphere
        Supervisor. This class is applied in entirety, replacing the current
        specification fully. This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     version=None,
                     service_config=None,
                     yaml_service_config=None,
                    ):
            """
            :type  version: :class:`str`
            :param version: Identifier of the Supervisor Service version which contains the
                service definition. This Supervisor Service version must be in the
                ``ACTIVATED`` state. This attribute was added in vSphere API
                7.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
            :type  service_config: (:class:`dict` of :class:`str` and :class:`str`) or ``None``
            :param service_config: A generic key-value map for additional configuration parameters
                required during service upgrade. As an example, a third party
                operator might reference a private registry using parameters such
                as "registryName" for the registry name, "registryUsername" and
                "registryPassword" for the registry credentials. This attribute was
                added in vSphere API 7.0.3.0.
                If None, no additional configuration parameters will be applied
                when upgrading a Supervisor Service in the vSphere Supervisor.
            :type  yaml_service_config: :class:`str` or ``None``
            :param yaml_service_config: A set of additional configuration parameters to be applied during
                service upgrade. These parameters should be formatted as a base64
                encoded YAML document. 
                
                Parameters should be :class:`set` in at most one of
                ``serviceConfig`` or ``yamlServiceConfig``, and not both. The
                ``yamlServiceConfig`` supports complex data types and nested
                properties.. This attribute was added in vSphere API 8.0.0.1.
                If None, no additional configuration parameters will be applied
                when upgrading a Supervisor Service in the vSphere Supervisor.
            """
            self.version = version
            self.service_config = service_config
            self.yaml_service_config = yaml_service_config
            VapiStruct.__init__(self)


    SetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.cluster_supervisor_services.set_spec', {
            'version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
            'service_config': type.OptionalType(type.MapType(type.StringType(), type.StringType())),
            'yaml_service_config': type.OptionalType(type.StringType()),
        },
        SetSpec,
        False,
        None))


    class Message(VapiStruct):
        """
        The ``ClusterSupervisorServices.Message`` class contains the information
        about the Supervisor Service configuration on a vSphere Supervisor. This
        class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     severity=None,
                     details=None,
                    ):
            """
            :type  severity: :class:`ClusterSupervisorServices.Message.MessageSeverity`
            :param severity: Type of the message. This attribute was added in vSphere API
                7.0.3.0.
            :type  details: :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param details: Details about the message. This attribute was added in vSphere API
                7.0.3.0.
                If None, message details are not required for taking actions.
            """
            self.severity = severity
            self.details = details
            VapiStruct.__init__(self)


        class MessageSeverity(Enum):
            """
            The ``ClusterSupervisorServices.Message.MessageSeverity`` class represents
            the severity of the message. This enumeration was added in vSphere API
            7.0.3.0.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            INFO = None
            """
            Informational message. This may be accompanied by vCenter event. This class
            attribute was added in vSphere API 7.0.3.0.

            """
            WARNING = None
            """
            Warning message. This may be accompanied by vCenter event. This class
            attribute was added in vSphere API 7.0.3.0.

            """
            ERROR = None
            """
            Error message. This is accompanied by vCenter event and/or alarm. This
            class attribute was added in vSphere API 7.0.3.0.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`MessageSeverity` instance.
                """
                Enum.__init__(string)

        MessageSeverity._set_values({
            'INFO': MessageSeverity('INFO'),
            'WARNING': MessageSeverity('WARNING'),
            'ERROR': MessageSeverity('ERROR'),
        })
        MessageSeverity._set_binding_type(type.EnumType(
            'com.vmware.vcenter.namespace_management.supervisor_services.cluster_supervisor_services.message.message_severity',
            MessageSeverity))

    Message._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.cluster_supervisor_services.message', {
            'severity': type.ReferenceType(__name__, 'ClusterSupervisorServices.Message.MessageSeverity'),
            'details': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        Message,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``ClusterSupervisorServices.Info`` class contains the detailed
        information about a Supervisor Service on the vSphere Supervisor. This
        class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     desired_version=None,
                     service_namespace=None,
                     config_status=None,
                     messages=None,
                     current_version=None,
                     display_name=None,
                     description=None,
                     prefix=None,
                     yaml_service_config=None,
                    ):
            """
            :type  desired_version: :class:`str`
            :param desired_version: The desired version of this Supervisor Service. This attribute was
                added in vSphere API 7.0.3.0.
            :type  service_namespace: :class:`str` or ``None``
            :param service_namespace: Identifier of the namespace to allocate the Supervisor Service's
                operators. This attribute was added in vSphere API 7.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``. When methods return a
                value of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``.
                If None, there is an error when creating the service namespace or
                the namespace has not been created yet.
            :type  config_status: :class:`ClusterSupervisorServices.ConfigStatus`
            :param config_status: Current setting for ``ClusterSupervisorServices.ConfigStatus``.
                This attribute was added in vSphere API 7.0.3.0.
            :type  messages: :class:`list` of :class:`ClusterSupervisorServices.Message`
            :param messages: Current set of messages associated with the Supervisor Service on
                the vSphere Supervisor. This attribute was added in vSphere API
                7.0.3.0.
            :type  current_version: :class:`str` or ``None``
            :param current_version: The current version for the Supervisor Service. This attribute was
                added in vSphere API 7.0.3.0.
                If None, there is no version installed for the Supervisor Service.
            :type  display_name: :class:`str`
            :param display_name: A human readable name of the Supervisor Service. This attribute was
                added in vSphere API 7.0.3.0.
            :type  description: :class:`str` or ``None``
            :param description: A human readable description of the Supervisor Service. This
                attribute was added in vSphere API 7.0.3.0.
                If None, the description for the service version is empty.
            :type  prefix: :class:`str` or ``None``
            :param prefix: The prefix that will be added to the names of the Supervisor
                Service's kubernetes resources. This attribute was added in vSphere
                API 7.0.3.0.
                If None, the prefix is not assigned yet.
            :type  yaml_service_config: :class:`str` or ``None``
            :param yaml_service_config: The configuration parameters applied on this Supervisor Service,
                formatted as a base64 encoded YAML document. Any configuration that
                has been :class:`set` will be returned as base64 encoded YAML,
                including the ``serviceConfig``. This attribute was added in
                vSphere API 8.0.0.1.
                If None, the Supervisor Service has no configuration applied.
            """
            self.desired_version = desired_version
            self.service_namespace = service_namespace
            self.config_status = config_status
            self.messages = messages
            self.current_version = current_version
            self.display_name = display_name
            self.description = description
            self.prefix = prefix
            self.yaml_service_config = yaml_service_config
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.cluster_supervisor_services.info', {
            'desired_version': type.StringType(),
            'service_namespace': type.OptionalType(type.IdType()),
            'config_status': type.ReferenceType(__name__, 'ClusterSupervisorServices.ConfigStatus'),
            'messages': type.ListType(type.ReferenceType(__name__, 'ClusterSupervisorServices.Message')),
            'current_version': type.OptionalType(type.StringType()),
            'display_name': type.StringType(),
            'description': type.OptionalType(type.StringType()),
            'prefix': type.OptionalType(type.StringType()),
            'yaml_service_config': type.OptionalType(type.StringType()),
        },
        Info,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``ClusterSupervisorServices.Summary`` class contains the basic
        information about a Supervisor Service on the vSphere Supervisor. This
        class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor_service=None,
                     desired_version=None,
                     config_status=None,
                     current_version=None,
                    ):
            """
            :type  supervisor_service: :class:`str`
            :param supervisor_service: The identifier of the Supervisor Service. This attribute was added
                in vSphere API 7.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.SupervisorService``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.SupervisorService``.
            :type  desired_version: :class:`str`
            :param desired_version: The desired version of this Supervisor Service. This attribute was
                added in vSphere API 7.0.3.0.
            :type  config_status: :class:`ClusterSupervisorServices.ConfigStatus`
            :param config_status: Current setting for ``ClusterSupervisorServices.ConfigStatus``.
                This attribute was added in vSphere API 7.0.3.0.
            :type  current_version: :class:`str` or ``None``
            :param current_version: The current version for the Supervisor Service. This attribute was
                added in vSphere API 7.0.3.0.
                If None, there is no version installed for the Supervisor Service.
            """
            self.supervisor_service = supervisor_service
            self.desired_version = desired_version
            self.config_status = config_status
            self.current_version = current_version
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.cluster_supervisor_services.summary', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'desired_version': type.StringType(),
            'config_status': type.ReferenceType(__name__, 'ClusterSupervisorServices.ConfigStatus'),
            'current_version': type.OptionalType(type.StringType()),
        },
        Summary,
        False,
        None))



    def create(self,
               cluster,
               spec,
               ):
        """
        Create a Supervisor Service on the specified vSphere Supervisor. This
        method will apply the Supervisor Service version's service definition
        on the cluster. This method is possible only when the Supervisor
        Service and Supervisor Service version are in the ``ACTIVATED`` state.
        A Supervisor can be running on one or multiple vSphere Zones, and each
        vSphere Zone is associated with one or more vSphere Clusters. If a
        Supervisor running on the specified vSphere Cluster is running on
        additional vSphere Clusters, this operation will apply to Supervisor
        components running on the other vSphere Clusters in addition to the
        specified vSphere Cluster. To call this API on a Supervisor with
        multiple vSphere Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the Supervisor on which to create the service.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`ClusterSupervisorServices.CreateSpec`
        :param spec: Specification for the Supervisor Service on the cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if a Supervisor Service ID defined in ``spec`` exists on the
            Supervisor
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the specified cluster with ID ``cluster`` or Supervisor Service
            with the Supervisor Service ID defined in ``spec`` or version with
            the ID {param.name version} could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor doesn't support Supervisor Services, or if the
            Supervisor Service cannot be created in the current state, e.g. the
            supervisor service version is in the ``DEACTIVATED`` state.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the SupervisorServices.Install privilege
            on the specified cluster.
        """
        return self._invoke('create',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })

    def list(self,
             cluster,
             ):
        """
        Return the summaries about all Supervisor Services on the specified
        vSphere Supervisor. A Supervisor can be running on one or multiple
        vSphere Zones, and each vSphere Zone is associated with one or more
        vSphere Clusters. If a Supervisor running on the specified vSphere
        Cluster is running on additional vSphere Clusters, this operation will
        apply to Supervisor components running on the other vSphere Clusters in
        addition to the specified vSphere Cluster. To call this API on a
        Supervisor with multiple vSphere Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which to list the services.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`list` of :class:`ClusterSupervisorServices.Summary`
        :return: The list of summaries of all Supervisor Services on the cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor with the ID ``cluster`` could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor doesn't support Supervisor Services.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the System.Read privilege on the
            specified cluster.
        """
        return self._invoke('list',
                            {
                            'cluster': cluster,
                            })

    def get(self,
            cluster,
            supervisor_service,
            ):
        """
        Return information about the specific Supervisor Service on the
        specified vSphere Supervisor. A Supervisor can be running on one or
        multiple vSphere Zones, and each vSphere Zone is associated with one or
        more vSphere Clusters. If a Supervisor running on the specified vSphere
        Cluster is running on additional vSphere Clusters, this operation will
        apply to Supervisor components running on the other vSphere Clusters in
        addition to the specified vSphere Cluster. To call this API on a
        Supervisor with multiple vSphere Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which to get the service.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier for the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :rtype: :class:`ClusterSupervisorServices.Info`
        :return: The information for the specified Supervisor Service on the
            specified cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor with the ID ``cluster`` or the Supervisor Service
            does not exist on the Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor doesn't support Supervisor Services.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the SupervisorServices.Install privilege
            on the specified cluster.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            'supervisor_service': supervisor_service,
                            })

    def delete(self,
               cluster,
               supervisor_service,
               ):
        """
        Delete a Supervisor Service on the specified vSphere Supervisor. This
        method will remove the Supervisor Service with the specified identifier
        from the cluster, by removing the corresponding namespace and deleting
        the operator(s) associated with the Supervisor Service. Note that this
        operation doesn't deal with the application instances that are created
        by the associated operator(s), so existing application instances could
        be orphaned if users don't clean or migrate them. A Supervisor can be
        running on one or multiple vSphere Zones, and each vSphere Zone is
        associated with one or more vSphere Clusters. If a Supervisor running
        on the specified vSphere Cluster is running on additional vSphere
        Clusters, this operation will apply to Supervisor components running on
        the other vSphere Clusters in addition to the specified vSphere
        Cluster. To call this API on a Supervisor with multiple vSphere
        Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the Supervisor from which to delete the service.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier for the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor with the ID ``cluster`` or the Supervisor Service
            does not exist on the Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor doesn't support Supervisor Services.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the SupervisorServices.Install privilege
            on the specified cluster.
        """
        return self._invoke('delete',
                            {
                            'cluster': cluster,
                            'supervisor_service': supervisor_service,
                            })

    def set(self,
            cluster,
            supervisor_service,
            spec,
            ):
        """
        Set a new configuration to the specified Supervisor Service on the
        specified vSphere Supervisor. This method will apply the new Supervisor
        Service version's service definition to the existing Supervisor Service
        on the cluster. This method requires that the specified Supervisor
        Service is already installed in the specified Supervisor. Note that
        this operation doesn't interfere with the application instances that
        are created by the associated operator(s). So users should make sure
        the new version is still compatible with the existing application
        instances. A Supervisor can be running on one or multiple vSphere
        Zones, and each vSphere Zone is associated with one or more vSphere
        Clusters. If a Supervisor running on the specified vSphere Cluster is
        running on additional vSphere Clusters, this operation will apply to
        Supervisor components running on the other vSphere Clusters in addition
        to the specified vSphere Cluster. To call this API on a Supervisor with
        multiple vSphere Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the Supervisor from which to delete the service.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier for the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :type  spec: :class:`ClusterSupervisorServices.SetSpec`
        :param spec: Specification for the Supervisor Service on the cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor with the ID ``cluster`` or Supervisor Service with
            the ID ``supervisor_service`` or version with the ID {param.name
            version} could not be located, or the Supervisor Service does not
            exist on the Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor doesn't support Supervisor Services or the
            specified version is not in the ``ACTIVATED`` state.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the SupervisorServices.Install privilege
            on the specified cluster.
        """
        return self._invoke('set',
                            {
                            'cluster': cluster,
                            'supervisor_service': supervisor_service,
                            'spec': spec,
                            })
class Versions(VapiInterface):
    """
    The ``Versions`` class provides methods to manage a version object of a
    Supervisor Service. A Supervisor Service version can be enabled on the
    vSphere Supervisor. This class was added in vSphere API 7.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisor_services.versions'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _VersionsStub)
        self._VAPI_OPERATION_IDS = {}

    class State(Enum):
        """
        The ``Versions.State`` class defines the state of a Supervisor Service
        version. This enumeration was added in vSphere API 7.0.3.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        ACTIVATED = None
        """
        The is the default state of a Supervisor Service version upon creation. In
        this state, all operations on the version should work as normal. This class
        attribute was added in vSphere API 7.0.3.0.

        """
        DEACTIVATED = None
        """
        The is the deactivated state of a Supervisor Service version. In this
        state, certain operations on the version are disallowed, for example, the
        version cannot be created on the vSphere Supervisor clusters. This class
        attribute was added in vSphere API 7.0.3.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`State` instance.
            """
            Enum.__init__(string)

    State._set_values({
        'ACTIVATED': State('ACTIVATED'),
        'DEACTIVATED': State('DEACTIVATED'),
    })
    State._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.supervisor_services.versions.state',
        State))


    class ContentType(Enum):
        """
        The ``Versions.ContentType`` class defines the type of content that
        describes the format of Supervisor Service version definition. This
        enumeration was added in vSphere API 7.0.3.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        VSPHERE_APPS_YAML = None
        """
        The Supervisor Service version definition is provided as inline YAML
        document that follows the vSphere application service format. This class
        attribute was added in vSphere API 7.0.3.0.

        """
        CARVEL_APPS_YAML = None
        """
        The Supervisor Service version definition is provided as inline YAML
        document that follows the Carvel application package format. This class
        attribute was added in vSphere API 8.0.0.1.

        """
        CUSTOM_YAML = None
        """
        The Supervisor Service version definition is provided as inline YAML
        document that follows a plain Kubernetes YAML format. This class attribute
        was added in vSphere API 7.0.3.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ContentType` instance.
            """
            Enum.__init__(string)

    ContentType._set_values({
        'VSPHERE_APPS_YAML': ContentType('VSPHERE_APPS_YAML'),
        'CARVEL_APPS_YAML': ContentType('CARVEL_APPS_YAML'),
        'CUSTOM_YAML': ContentType('CUSTOM_YAML'),
    })
    ContentType._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.supervisor_services.versions.content_type',
        ContentType))


    class CreateSpec(VapiStruct):
        """
        The ``Versions.CreateSpec`` class provides a specification required to
        create a Supervisor Service version. Exactly one of
        :attr:`Versions.CreateSpec.custom_spec` or
        :attr:`Versions.CreateSpec.vsphere_spec` must be :class:`set`. This class
        was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     custom_spec=None,
                     vsphere_spec=None,
                     carvel_spec=None,
                    ):
            """
            :type  custom_spec: :class:`Versions.CustomCreateSpec` or ``None``
            :param custom_spec: The specification required to create a Supervisor Service version
                from inline content that is based on a plain Kubernetes YAML
                format. 
                
                . This attribute was added in vSphere API 7.0.3.0.
                If :class:`set`, the service version will be created from inline
                content based on a plain Kubernetes YAML format.
            :type  vsphere_spec: :class:`Versions.VsphereCreateSpec` or ``None``
            :param vsphere_spec: The specification required to create a Supervisor Service version
                from inline content that is based on the vSphere application
                service format. 
                
                . This attribute was added in vSphere API 7.0.3.0.
                If :class:`set`, the service version will be created from inline
                content based on the vSphere application service format.
            :type  carvel_spec: :class:`Versions.CarvelCreateSpec` or ``None``
            :param carvel_spec: The specification required to create a Supervisor Service version
                from inline content that is based on the Carvel application package
                format. 
                
                . This attribute was added in vSphere API 8.0.0.1.
                If :class:`set`, the service version will be created from inline
                content based on the Carvel application package format (Package and
                PackageMetadata resources should be declared).
            """
            self.custom_spec = custom_spec
            self.vsphere_spec = vsphere_spec
            self.carvel_spec = carvel_spec
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.versions.create_spec', {
            'custom_spec': type.OptionalType(type.ReferenceType(__name__, 'Versions.CustomCreateSpec')),
            'vsphere_spec': type.OptionalType(type.ReferenceType(__name__, 'Versions.VsphereCreateSpec')),
            'carvel_spec': type.OptionalType(type.ReferenceType(__name__, 'Versions.CarvelCreateSpec')),
        },
        CreateSpec,
        False,
        None))


    class CustomCreateSpec(VapiStruct):
        """
        The ``Versions.CustomCreateSpec`` class provides a specification required
        to create a Supervisor Service version from a plain Kubernetes YAML format.
        This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     version=None,
                     display_name=None,
                     description=None,
                     content=None,
                     trusted_provider=None,
                    ):
            """
            :type  version: :class:`str`
            :param version: The identifier of the Supervisor Service version. This must be a
                semantic version. This attribute was added in vSphere API 7.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
            :type  display_name: :class:`str`
            :param display_name: A human readable name of the Supervisor Service version. This
                attribute was added in vSphere API 7.0.3.0.
            :type  description: :class:`str` or ``None``
            :param description: A human readable description of the Supervisor Service version.
                This attribute was added in vSphere API 7.0.3.0.
                If None, the description for the service version will be empty.
            :type  content: :class:`str`
            :param content: Inline content that contains all service definition of the version,
                which shall be base64 encoded. The service definition here follows
                a plain Kubernetes YAML format. This attribute was added in vSphere
                API 7.0.3.0.
            :type  trusted_provider: :class:`bool` or ``None``
            :param trusted_provider: Whether or not the Supervisor Service version is from a trusted
                provider, this field must be set to false if the service version is
                not from a trusted provider. If it is set to be true, but the
                ``content`` is not signed or the signature is invalid, an
                ``InvalidArgument`` will be thrown. This attribute was added in
                vSphere API 7.0.3.0.
                If None, the default value is true. In this case, the ``content``
                must be signed and will be verified.
            """
            self.version = version
            self.display_name = display_name
            self.description = description
            self.content = content
            self.trusted_provider = trusted_provider
            VapiStruct.__init__(self)


    CustomCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.versions.custom_create_spec', {
            'version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
            'display_name': type.StringType(),
            'description': type.OptionalType(type.StringType()),
            'content': type.StringType(),
            'trusted_provider': type.OptionalType(type.BooleanType()),
        },
        CustomCreateSpec,
        False,
        None))


    class VsphereCreateSpec(VapiStruct):
        """
        The ``Versions.VsphereCreateSpec`` class provides a specification required
        to create a Supervisor Service version from vSphere application service
        format, which shall contain the Supervisor Service identifier, version
        identifier, display name and description information. This class was added
        in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'accept_EULA': 'accept_eula',
                                }

        def __init__(self,
                     content=None,
                     trusted_provider=None,
                     accept_eula=None,
                    ):
            """
            :type  content: :class:`str`
            :param content: Inline content that contains all service definition of the version
                in vSphere application service format, which shall be base64
                encoded. This attribute was added in vSphere API 7.0.3.0.
            :type  trusted_provider: :class:`bool` or ``None``
            :param trusted_provider: Whether or not the Supervisor Service version is from a trusted
                provider, this field must be set to false if the service version is
                not from a trusted provider. If it is set to be true, but the
                ``content`` is not signed or the signature is invalid, an
                ``InvalidArgument`` will be thrown. This attribute was added in
                vSphere API 7.0.3.0.
                If None, the default value is true. In this case, the ``content``
                must be signed and will be verified.
            :type  accept_eula: :class:`bool` or ``None``
            :param accept_eula: Whether or not the End User License Agreement (EULA) that is
                specified in the ``content`` is accepted. If a EULA is specified,
                this attribute must be set to be true so that the Supervisor
                Service version can be created. This attribute was added in vSphere
                API 7.0.3.0.
                If None, the default value is false.
            """
            self.content = content
            self.trusted_provider = trusted_provider
            self.accept_eula = accept_eula
            VapiStruct.__init__(self)


    VsphereCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.versions.vsphere_create_spec', {
            'content': type.StringType(),
            'trusted_provider': type.OptionalType(type.BooleanType()),
            'accept_EULA': type.OptionalType(type.BooleanType()),
        },
        VsphereCreateSpec,
        False,
        None))


    class CarvelCreateSpec(VapiStruct):
        """
        The ``Versions.CarvelCreateSpec`` class provides a specification required
        to create a Supervisor Service version from Carvel application package
        format (Package and PackageMetadata resources should be declared). This
        class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     content=None,
                    ):
            """
            :type  content: :class:`str`
            :param content: Inline content that contains all service definition of the version
                in Carvel application package format, which shall be base64
                encoded. This attribute was added in vSphere API 8.0.0.1.
            """
            self.content = content
            VapiStruct.__init__(self)


    CarvelCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.versions.carvel_create_spec', {
            'content': type.StringType(),
        },
        CarvelCreateSpec,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``Versions.Summary`` class contains the basic information about a
        Supervisor Service version. This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     version=None,
                     display_name=None,
                     state=None,
                     description=None,
                    ):
            """
            :type  version: :class:`str`
            :param version: The identifier of the Supervisor Service version. This attribute
                was added in vSphere API 7.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
            :type  display_name: :class:`str`
            :param display_name: A human readable name of the Supervisor Service version. This
                attribute was added in vSphere API 7.0.3.0.
            :type  state: :class:`Versions.State`
            :param state: The current ``Versions.State`` of the Supervisor Service version.
                This attribute was added in vSphere API 7.0.3.0.
            :type  description: :class:`str` or ``None``
            :param description: A human readable description of the Supervisor Service version.
                This attribute was added in vSphere API 7.0.3.0.
                If None, no description is available for the service version.
            """
            self.version = version
            self.display_name = display_name
            self.state = state
            self.description = description
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.versions.summary', {
            'version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
            'display_name': type.StringType(),
            'state': type.ReferenceType(__name__, 'Versions.State'),
            'description': type.OptionalType(type.StringType()),
        },
        Summary,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Versions.Info`` class contains detailed information about a
        Supervisor Service version. This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'EULA': 'eula',
                                }

        def __init__(self,
                     display_name=None,
                     description=None,
                     eula=None,
                     content_type=None,
                     content=None,
                     trust_verified=None,
                     state=None,
                     registered_by_default=None,
                    ):
            """
            :type  display_name: :class:`str`
            :param display_name: The human readable name of the Supervisor Service version. This
                attribute was added in vSphere API 7.0.3.0.
            :type  description: :class:`str` or ``None``
            :param description: A human-readable description of the Supervisor Service version.
                This attribute was added in vSphere API 7.0.3.0.
                If None, no description is available for the Supervisor Service
                version.
            :type  eula: :class:`str` or ``None``
            :param eula: The End User License Agreement (EULA) associated with the
                Supervisor Service version. This attribute was added in vSphere API
                7.0.3.0.
                If None, no EULA is available for the Supervisor Service version.
            :type  content_type: :class:`Versions.ContentType`
            :param content_type: The content type of ``content``. This attribute was added in
                vSphere API 7.0.3.0.
            :type  content: :class:`str` or ``None``
            :param content: Inline content that contains base64 encoded service definition for
                the version. This attribute was added in vSphere API 7.0.3.0.
                If None, no content is available for the Supervisor Service
                version.
            :type  trust_verified: :class:`bool`
            :param trust_verified: If true, the Supervisor Service version is from trusted provider
                and the trust is verified. This attribute was added in vSphere API
                7.0.3.0.
            :type  state: :class:`Versions.State`
            :param state: The current ``Versions.State`` of the version. This attribute was
                added in vSphere API 7.0.3.0.
            :type  registered_by_default: :class:`bool`
            :param registered_by_default: If ``true``, this Supervisor Service version has been registered on
                vCenter by default and cannot be removed. If ``false``, this
                service version has been registered by an administrator. This
                attribute was added in vSphere API 8.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.display_name = display_name
            self.description = description
            self.eula = eula
            self.content_type = content_type
            self.content = content
            self.trust_verified = trust_verified
            self.state = state
            self.registered_by_default = registered_by_default
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.versions.info', {
            'display_name': type.StringType(),
            'description': type.OptionalType(type.StringType()),
            'EULA': type.OptionalType(type.StringType()),
            'content_type': type.ReferenceType(__name__, 'Versions.ContentType'),
            'content': type.OptionalType(type.StringType()),
            'trust_verified': type.BooleanType(),
            'state': type.ReferenceType(__name__, 'Versions.State'),
            'registered_by_default': type.OptionalType(type.BooleanType()),
        },
        Info,
        False,
        None))



    def create(self,
               supervisor_service,
               spec,
               ):
        """
        Create a Supervisor Service version based on the provided service
        definition information for the version. This method was added in
        vSphere API 7.0.3.0.

        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier of the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :type  spec: :class:`Versions.CreateSpec`
        :param spec: Specification for the Supervisor Service version to be created.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if a Supervisor Service version with the same identifier already
            exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if an invalid field in ``spec`` is specified or if it contains any
            errors. For example, when the field trusted is set to be true, but
            no signature is provided or it is invalid or when a EULA is
            specified but not accepted.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor Service version cannot be created in the current
            state, for example, the Supervisor Service is in ``DEACTIVATED``
            state.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor Service with the ID ``supervisor_service`` could not
            be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the SupervisorServices.Manage privilege.
        """
        return self._invoke('create',
                            {
                            'supervisor_service': supervisor_service,
                            'spec': spec,
                            })

    def deactivate(self,
                   supervisor_service,
                   version,
                   ):
        """
        Deactivate a Supervisor Service version. This method will change the
        ``Versions.State`` of the version to ``DEACTIVATED`` state, which will
        make sure the version cannot be created on any Supervisor cluster. Note
        that this method should be called before deleting the version. This
        method was added in vSphere API 7.0.3.0.

        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier for the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :type  version: :class:`str`
        :param version: Identifier of the version.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor Service version cannot be deactivated in the
            current state, for example, the Supervisor Service is in
            ``ACTIVATED`` state and this version is the last version of the
            Supervisor Service in ``ACTIVATED`` state.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor Service with the ID ``supervisor_service`` or version
            with the ID ``version`` could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the SupervisorServices.Manage privilege.
        """
        return self._invoke('deactivate',
                            {
                            'supervisor_service': supervisor_service,
                            'version': version,
                            })

    def activate(self,
                 supervisor_service,
                 version,
                 ):
        """
        Activate a Supervisor Service version. This method will change the
        ``Versions.State`` of the version to ``ACTIVATED`` state. This method
        was added in vSphere API 7.0.3.0.

        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier for the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :type  version: :class:`str`
        :param version: Identifier of the version.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor Service version cannot be activated in the
            current state, for example, the Supervisor Service is in
            ``DEACTIVATED`` state.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor Service with the ID ``supervisor_service`` or version
            with the ID {param.name version} could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the SupervisorServices.Manage privilege.
        """
        return self._invoke('activate',
                            {
                            'supervisor_service': supervisor_service,
                            'version': version,
                            })

    def list(self,
             supervisor_service,
             ):
        """
        Return the information about all versions of the Supervisor Service.
        This method was added in vSphere API 7.0.3.0.

        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier of the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :rtype: :class:`list` of :class:`Versions.Summary`
        :return: The list of summary of all service versions of the Supervisor
            Service.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if service with the ID ``supervisor_service`` could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the System.Read privilege.
        """
        return self._invoke('list',
                            {
                            'supervisor_service': supervisor_service,
                            })

    def get(self,
            supervisor_service,
            version,
            ):
        """
        Return the information for the specified Supervisor Service version.
        This method was added in vSphere API 7.0.3.0.

        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier of the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :type  version: :class:`str`
        :param version: Identifier of the version.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
        :rtype: :class:`Versions.Info`
        :return: Information for the specified Supervisor Service version.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor Service with the ID ``supervisor_service`` or version
            with the ID {param.name version} could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'supervisor_service': supervisor_service,
                            'version': version,
                            })

    def delete(self,
               supervisor_service,
               version,
               ):
        """
        Delete a Supervisor Service version. This method only deletes the
        Supervisor Service version from vCenter if the version is in
        ``DEACTIVATED`` state and all instances of the version are removed from
        all Supervisors. Note that the ``deactivate`` method should be called
        to deactivate the version before the version can be deleted. 
        
        Note that deleting the last version of the ``supervisor_service`` does
        not delete the ``supervisor_service`` instance automatically.. This
        method was added in vSphere API 7.0.3.0.

        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier of the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :type  version: :class:`str`
        :param version: Identifier of the version.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request,
            e.g. if it is unable to reach a vSphere Supervisor that has the
            version enabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor Service version cannot be deleted in the current
            state, e.g. the version is not in ``DEACTIVATED`` state.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor Service with the ID ``supervisor_service`` or version
            with the ID {param.name version} could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the SupervisorServices.Manage privilege.
        """
        return self._invoke('delete',
                            {
                            'supervisor_service': supervisor_service,
                            'version': version,
                            })
class _ClusterSupervisorServicesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.ReferenceType(__name__, 'ClusterSupervisorServices.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/clusters/{cluster}/supervisor-services',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
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
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
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
            url_template='/vcenter/namespace-management/clusters/{cluster}/supervisor-services',
            path_variables={
                'cluster': 'cluster',
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
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
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
            url_template='/vcenter/namespace-management/clusters/{cluster}/supervisor-services/{supervisorService}',
            path_variables={
                'cluster': 'cluster',
                'supervisor_service': 'supervisorService',
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
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vcenter/namespace-management/clusters/{cluster}/supervisor-services/{supervisorService}',
            path_variables={
                'cluster': 'cluster',
                'supervisor_service': 'supervisorService',
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
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'spec': type.ReferenceType(__name__, 'ClusterSupervisorServices.SetSpec'),
        })
        set_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/vcenter/namespace-management/clusters/{cluster}/supervisor-services/{supervisorService}',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
                'supervisor_service': 'supervisorService',
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
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'ClusterSupervisorServices.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'ClusterSupervisorServices.Info'),
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
            'set': {
                'input_type': set_input_type,
                'output_type': type.VoidType(),
                'errors': set_error_dict,
                'input_value_validator_list': set_input_value_validator_list,
                'output_validator_list': set_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'create': create_rest_metadata,
            'list': list_rest_metadata,
            'get': get_rest_metadata,
            'delete': delete_rest_metadata,
            'set': set_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.supervisor_services.cluster_supervisor_services',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _VersionsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'spec': type.ReferenceType(__name__, 'Versions.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/supervisor-services/{supervisorService}/versions',
            request_body_parameter='spec',
            path_variables={
                'supervisor_service': 'supervisorService',
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

        # properties for deactivate operation
        deactivate_input_type = type.StructType('operation-input', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
        })
        deactivate_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        deactivate_input_value_validator_list = [
        ]
        deactivate_output_validator_list = [
        ]
        deactivate_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespace-management/supervisor-services/{supervisorService}/versions/{version}',
            path_variables={
                'supervisor_service': 'supervisorService',
                'version': 'version',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'deactivate',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for activate operation
        activate_input_type = type.StructType('operation-input', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
        })
        activate_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        activate_input_value_validator_list = [
        ]
        activate_output_validator_list = [
        ]
        activate_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespace-management/supervisor-services/{supervisorService}/versions/{version}',
            path_variables={
                'supervisor_service': 'supervisorService',
                'version': 'version',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'activate',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
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
            url_template='/vcenter/namespace-management/supervisor-services/{supervisorService}/versions',
            path_variables={
                'supervisor_service': 'supervisorService',
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
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
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
            url_template='/vcenter/namespace-management/supervisor-services/{supervisorService}/versions/{version}',
            path_variables={
                'supervisor_service': 'supervisorService',
                'version': 'version',
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
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vcenter/namespace-management/supervisor-services/{supervisorService}/versions/{version}',
            path_variables={
                'supervisor_service': 'supervisorService',
                'version': 'version',
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
            'deactivate': {
                'input_type': deactivate_input_type,
                'output_type': type.VoidType(),
                'errors': deactivate_error_dict,
                'input_value_validator_list': deactivate_input_value_validator_list,
                'output_validator_list': deactivate_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'activate': {
                'input_type': activate_input_type,
                'output_type': type.VoidType(),
                'errors': activate_error_dict,
                'input_value_validator_list': activate_input_value_validator_list,
                'output_validator_list': activate_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'Versions.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Versions.Info'),
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
        }
        rest_metadata = {
            'create': create_rest_metadata,
            'deactivate': deactivate_rest_metadata,
            'activate': activate_rest_metadata,
            'list': list_rest_metadata,
            'get': get_rest_metadata,
            'delete': delete_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.supervisor_services.versions',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'ClusterSupervisorServices': ClusterSupervisorServices,
        'Versions': Versions,
    }

