# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.supervisors.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.namespace_management.supervisors_client`` module
provides classes for operating a Supervisor.

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

class SizingHint(Enum):
    """
    The ``SizingHint`` class determines the configuration of Kubernetes API
    server and the worker nodes. It also determines the default values
    associated with the maximum number of pods and services. Use
    :func:`com.vmware.vcenter.namespace_management_client.ClusterSizeInfo.get`
    to get information associated with a ``SizingHint``. This enumeration was
    added in vSphere API 8.0.0.1.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    TINY = None
    """
    Cluster size of 'tiny'. This class attribute was added in vSphere API
    8.0.0.1.

    """
    SMALL = None
    """
    Cluster size of 'small'. This class attribute was added in vSphere API
    8.0.0.1.

    """
    MEDIUM = None
    """
    Cluster size of 'medium'. This class attribute was added in vSphere API
    8.0.0.1.

    """
    LARGE = None
    """
    Cluster size of 'large'. This class attribute was added in vSphere API
    8.0.0.1.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`SizingHint` instance.
        """
        Enum.__init__(string)

SizingHint._set_values({
    'TINY': SizingHint('TINY'),
    'SMALL': SizingHint('SMALL'),
    'MEDIUM': SizingHint('MEDIUM'),
    'LARGE': SizingHint('LARGE'),
})
SizingHint._set_binding_type(type.EnumType(
    'com.vmware.vcenter.namespace_management.supervisors.sizing_hint',
    SizingHint))




class ControlPlane(VapiStruct):
    """
    
    
    ``ControlPlane`` class describes the control plane configuration. It allows
    you to adjust configuration such as size, network, and storage required to
    support the control plane runtime.. This class was added in vSphere API
    8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 network=None,
                 login_banner=None,
                 size=None,
                 storage_policy=None,
                ):
        """
        :type  network: :class:`com.vmware.vcenter.namespace_management.supervisors.networks.management_client.Network`
        :param network: 
            
            The management :attr:`ControlPlane.network` is used by vCenter and
            the control plane to manage the cluster. vCenter and the NSX (if
            used) management plane must be accessible from this network. 
            
            The Supervisor requires that management network traffic is not L3
            routable from workload network traffic.. This attribute was added
            in vSphere API 8.0.0.1.
        :type  login_banner: :class:`str` or ``None``
        :param login_banner: 
            
            :attr:`ControlPlane.login_banner` is a disclaimer displayed prior
            to login via the Kubectl plugin.. This attribute was added in
            vSphere API 8.0.0.1.
            If this banner is None, no message will be displayed to users.
        :type  size: :class:`SizingHint` or ``None``
        :param size: 
            
            :attr:`ControlPlane.size` controls the size and resources allocated
            to the Kubernetes API server and the worker nodes.. This attribute
            was added in vSphere API 8.0.0.1.
            Defaults to SMALL.
        :type  storage_policy: :class:`str` or ``None``
        :param storage_policy: 
            
            :attr:`ControlPlane.storage_policy` identifies the storage policy
            backing the Supervisor Kubernetes API server.. This attribute was
            added in vSphere API 8.0.0.1.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``SpsStorageProfile``. When methods return a value of this class as
            a return value, the attribute will be an identifier for the
            resource type: ``SpsStorageProfile``.
            This resource is required.
        """
        self.network = network
        self.login_banner = login_banner
        self.size = size
        self.storage_policy = storage_policy
        VapiStruct.__init__(self)


ControlPlane._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.control_plane', {
        'network': type.ReferenceType('com.vmware.vcenter.namespace_management.supervisors.networks.management_client', 'Network'),
        'login_banner': type.OptionalType(type.StringType()),
        'size': type.OptionalType(type.ReferenceType(__name__, 'SizingHint')),
        'storage_policy': type.OptionalType(type.IdType()),
    },
    ControlPlane,
    False,
    None))



class ImageRegistry(VapiStruct):
    """
    The ``ImageRegistry`` class contains the specification required to
    configure container image registry endpoint. This class was added in
    vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 hostname=None,
                 port=None,
                 username=None,
                 password=None,
                 certificate_chain=None,
                ):
        """
        :type  hostname: :class:`str`
        :param hostname: IP address or the hostname of container image registry. This
            attribute was added in vSphere API 8.0.0.1.
        :type  port: :class:`long` or ``None``
        :param port: Port number of the container image registry. This attribute was
            added in vSphere API 8.0.0.1.
            If None, defaults to 443.
        :type  username: :class:`str` or ``None``
        :param username: A username to be used for username/password authentication with
            this registry. This attribute was added in vSphere API 8.0.3.0.
            If None then the username/password authentication will not be used.
        :type  password: :class:`str` or ``None``
        :param password: The password for the user. This attribute was added in vSphere API
            8.0.3.0.
            If None then the password is unset, only for write operations. For
            read operations (GET and LIST), this value is always nil.
        :type  certificate_chain: :class:`str` or ``None``
        :param certificate_chain: PEM-encoded CA chain which is used to verify x509 certificates
            received from the server. This attribute was added in vSphere API
            8.0.3.0.
            If None then the verification will be skipped.
        """
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.certificate_chain = certificate_chain
        VapiStruct.__init__(self)


ImageRegistry._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.image_registry', {
        'hostname': type.StringType(),
        'port': type.OptionalType(type.IntegerType()),
        'username': type.OptionalType(type.StringType()),
        'password': type.OptionalType(type.SecretType()),
        'certificate_chain': type.OptionalType(type.StringType()),
    },
    ImageRegistry,
    False,
    None))



class ImageSyncConfig(VapiStruct):
    """
    ``ImageSyncConfig`` class describes how the Supervisor Cluster and
    Kubernetes retrieves VM and container images that will run on the cluster.
    This class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 registry=None,
                 repository=None,
                 kubernetes_content_library=None,
                 content_libraries=None,
                ):
        """
        :type  registry: :class:`ImageRegistry` or ``None``
        :param registry: The :attr:`ImageSyncConfig.registry` class contains the
            specification required to configure container image registry
            endpoint. This attribute was added in vSphere API 8.0.0.1.
            Defaults to Docker Hub if None.
        :type  repository: :class:`str` or ``None``
        :param repository: 
            
            The :attr:`ImageSyncConfig.repository` specifies the default
            container image repository to use when the Kubernetes Pod
            specification does not specify it. For example, ``hub.docker.com``
            is the image repository for a Pod whose image specification is
            ``hub.docker.com/nginx``.. This attribute was added in vSphere API
            8.0.0.1.
            If None, and if docker hub is the configured
            :attr:`ImageSyncConfig.registry`, then
            :attr:`ImageSyncConfig.repository` defaults to Docker Hub. If
            Docker Hub is not the configured image registry,
            :attr:`ImageSyncConfig.repository` remains unset. 
            
            If {#member} repository is None, you must supply an image
            repository in your Pod spec or else images will not be able to be
            synced into the cluster.
        :type  kubernetes_content_library: :class:`str` or ``None``
        :param kubernetes_content_library: 
            
            :attr:`ImageSyncConfig.kubernetes_content_library` is the UUID of
            the Content Library which holds the VM Images for Tanzu Kubernetes
            Service for vSphere. 
            
            This Content Library should be subscribed to VMware's hosted
            vSphere Kubernetes Service Repository. Optionally, you can
            configure your own local content library and host images locally..
            This attribute was added in vSphere API 8.0.0.1.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.content.Library``. When methods return a value of this
            class as a return value, the attribute will be an identifier for
            the resource type: ``com.vmware.content.Library``.
            If the Content Library identifier is None, you will not be able to
            deploy Tanzu Kubernetes Clusters.
        :type  content_libraries: :class:`list` of :class:`ContentLibrarySpec` or ``None``
        :param content_libraries: 
            
            :attr:`ImageSyncConfig.content_libraries` is a list of Content
            Libraries that will be associated with a Supervisor. 
            
            This list refers to existing Content Libraries in the vSphere
            inventory. These Content Libraries and the Content Library items
            belonging to them will be read-only across all vSphere Namespaces. 
            This list cannot overlap with the
            :attr:`ImageSyncConfig.kubernetes_content_library`. . This
            attribute was added in vSphere API 8.0.2.0.
            If None,  no additional Content Libraries will be set for the
            Supervisor apart from the default Kubernetes Service Content
            Library. 
        """
        self.registry = registry
        self.repository = repository
        self.kubernetes_content_library = kubernetes_content_library
        self.content_libraries = content_libraries
        VapiStruct.__init__(self)


ImageSyncConfig._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.image_sync_config', {
        'registry': type.OptionalType(type.ReferenceType(__name__, 'ImageRegistry')),
        'repository': type.OptionalType(type.StringType()),
        'kubernetes_content_library': type.OptionalType(type.IdType()),
        'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ContentLibrarySpec'))),
    },
    ImageSyncConfig,
    False,
    None))



class ContentLibrarySpec(VapiStruct):
    """
    The ``ContentLibrarySpec`` class contains the specification required to
    configure Content Libraries with a Supervisor. This class was added in
    vSphere API 8.0.2.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 content_library=None,
                ):
        """
        :type  content_library: :class:`str`
        :param content_library: 
            
            :attr:`ContentLibrarySpec.content_library` is the Content Library
            ID associated with a Supervisor. The Content Library specified
            should exist in the vSphere inventory.. This attribute was added in
            vSphere API 8.0.2.0.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.content.Library``. When methods return a value of this
            class as a return value, the attribute will be an identifier for
            the resource type: ``com.vmware.content.Library``.
        """
        self.content_library = content_library
        VapiStruct.__init__(self)


ContentLibrarySpec._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.content_library_spec', {
        'content_library': type.IdType(resource_types='com.vmware.content.Library'),
    },
    ContentLibrarySpec,
    False,
    None))



class WorkloadsStorageConfig(VapiStruct):
    """
    ``WorkloadsStorageConfig`` class describes how vSphere and Kubernetes will
    persist images and volumes to disk. This class was added in vSphere API
    8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 cloud_native_file_volume=None,
                 ephemeral_storage_policy=None,
                 image_storage_policy=None,
                ):
        """
        :type  cloud_native_file_volume: :class:`CNSFileConfig` or ``None``
        :param cloud_native_file_volume: :attr:`WorkloadsStorageConfig.cloud_native_file_volume` specifies
            the Cloud Native Storage file volume support on the Supervisor.
            This feature provides ``ReadWriteMany`` container volumes support.
            This attribute was added in vSphere API 8.0.0.1.
            If None, file volume support will not be enabled on the Supervisor.
        :type  ephemeral_storage_policy: :class:`str` or ``None``
        :param ephemeral_storage_policy: :attr:`WorkloadsStorageConfig.ephemeral_storage_policy` identifies
            the storage policy associated with ephemeral disks of all the
            Kubernetes PodVMs in the cluster. This attribute was added in
            vSphere API 8.0.0.1.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``SpsStorageProfile``. When methods return a value of this class as
            a return value, the attribute will be an identifier for the
            resource type: ``SpsStorageProfile``.
            If None during cluster enablement, the ephemeral storage policy
            will be defaulted to the configured
            :attr:`ControlPlane.storage_policy`.
        :type  image_storage_policy: :class:`str` or ``None``
        :param image_storage_policy: The :attr:`WorkloadsStorageConfig.image_storage_policy` class
            contains the specification required to configure storage used for
            PodVM container images. This attribute was added in vSphere API
            8.0.0.1.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``SpsStorageProfile``. When methods return a value of this class as
            a return value, the attribute will be an identifier for the
            resource type: ``SpsStorageProfile``.
            If None, the image storage policy will be set to the specified
            :attr:`WorkloadsStorageConfig.ephemeral_storage_policy` if
            provided. This field will inherit any defaults for ephemeral
            storage policy set by the system.
        """
        self.cloud_native_file_volume = cloud_native_file_volume
        self.ephemeral_storage_policy = ephemeral_storage_policy
        self.image_storage_policy = image_storage_policy
        VapiStruct.__init__(self)


WorkloadsStorageConfig._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.workloads_storage_config', {
        'cloud_native_file_volume': type.OptionalType(type.ReferenceType(__name__, 'CNSFileConfig')),
        'ephemeral_storage_policy': type.OptionalType(type.IdType()),
        'image_storage_policy': type.OptionalType(type.IdType()),
    },
    WorkloadsStorageConfig,
    False,
    None))



class CNSFileConfig(VapiStruct):
    """
    The ``CNSFileConfig`` class contains the specification required to set the
    configuration for Cloud Native Storage file volume support on Supervisor.
    This class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 vsan_clusters=None,
                ):
        """
        :type  vsan_clusters: :class:`list` of :class:`str`
        :param vsan_clusters: 
            
            :attr:`CNSFileConfig.vsan_clusters` is a list of clusters to be
            used for provisioning file volumes. 
            
            As a prerequisite these clusters must have vSAN and vSAN file
            services enabled, and must be in the same vCenter as the
            Supervisor. 
            
            Currently this list must have a single entry which is the cluster
            identifier of the current cluster. This cluster must be a vSAN
            cluster and must have vSAN File Service enabled. 
            
            If a cluster in the list is not a vSAN cluster or does not have
            vSAN File Service enabled, an InvalidArgument error will be thrown
            from
            :func:`com.vmware.vcenter.namespace_management_client.Clusters.enable`,
            :func:`com.vmware.vcenter.namespace_management_client.Clusters.update`
            and
            :func:`com.vmware.vcenter.namespace_management_client.Clusters.set`
            APIs. 
            
            An empty list may be specified to disable file volume support on
            the Supervisor.. This attribute was added in vSphere API 8.0.0.1.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``ClusterComputeResource``. When methods return a value of this
            class as a return value, the attribute will contain identifiers for
            the resource type: ``ClusterComputeResource``.
        """
        self.vsan_clusters = vsan_clusters
        VapiStruct.__init__(self)


CNSFileConfig._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.CNS_file_config', {
        'vsan_clusters': type.ListType(type.IdType()),
    },
    CNSFileConfig,
    False,
    None))



class Workloads(VapiStruct):
    """
    
    
    ``Workloads`` class describes configuration that affects the behavior and
    lifecycle of Kubernetes workloads.. This class was added in vSphere API
    8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'kube_API_server_options': 'kube_api_server_options',
                            }

    def __init__(self,
                 network=None,
                 edge=None,
                 kube_api_server_options=None,
                 images=None,
                 storage=None,
                ):
        """
        :type  network: :class:`com.vmware.vcenter.namespace_management.supervisors.networks.workload_client.Network`
        :param network: 
            
            The workloads :attr:`Workloads.network` describes configuration for
            the primary workload network. 
            
            Workloads will communicate with each other and will reach external
            networks over this network. 
            
            The IP ranges configured on this network are managed primarily
            within Kubernetes.. This attribute was added in vSphere API
            8.0.0.1.
        :type  edge: :class:`com.vmware.vcenter.namespace_management.networks.edges_client.Edge`
        :param edge: 
            
            :attr:`Workloads.edge` configuration determines how network traffic
            will enter and leave the cluster. 
            
            The IP ranges configured on this network are managed by the
            Supervisor and the load balancer.. This attribute was added in
            vSphere API 8.0.0.1.
        :type  kube_api_server_options: :class:`KubeAPIServerOptions` or ``None``
        :param kube_api_server_options: 
            
            :attr:`Workloads.kube_api_server_options` declares configuration
            options for the Kubernetes API Server.. This attribute was added in
            vSphere API 8.0.0.1.
            If None, the default configuration will be used.
        :type  images: :class:`ImageSyncConfig` or ``None``
        :param images: 
            
            :attr:`Workloads.images` specifies how images will be stored and
            pulled into the cluster.. This attribute was added in vSphere API
            8.0.0.1.
            If None, image sync configuration will default to the settings
            described within the ``ImageSyncConfig`` class.
        :type  storage: :class:`WorkloadsStorageConfig` or ``None``
        :param storage: 
            
            :attr:`Workloads.storage` specifies which persistent storage is
            configured and accessible for workloads to consume. You can
            configure policies for both images and volumes.. This attribute was
            added in vSphere API 8.0.0.1.
            If None, configuration will be copied from the control plane when
            possible. If not, some storage features may be unavailable.
        """
        self.network = network
        self.edge = edge
        self.kube_api_server_options = kube_api_server_options
        self.images = images
        self.storage = storage
        VapiStruct.__init__(self)


Workloads._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.workloads', {
        'network': type.ReferenceType('com.vmware.vcenter.namespace_management.supervisors.networks.workload_client', 'Network'),
        'edge': type.ReferenceType('com.vmware.vcenter.namespace_management.networks.edges_client', 'Edge'),
        'kube_API_server_options': type.OptionalType(type.ReferenceType(__name__, 'KubeAPIServerOptions')),
        'images': type.OptionalType(type.ReferenceType(__name__, 'ImageSyncConfig')),
        'storage': type.OptionalType(type.ReferenceType(__name__, 'WorkloadsStorageConfig')),
    },
    Workloads,
    False,
    None))



class KubeAPIServerSecurity(VapiStruct):
    """
    ``KubeAPIServerSecurity`` class declares security options configured on the
    Kubernetes API server. This class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 certificate_dns_names=None,
                ):
        """
        :type  certificate_dns_names: :class:`list` of :class:`str`
        :param certificate_dns_names: 
            
            :attr:`KubeAPIServerSecurity.certificate_dns_names` lists
            additional DNS names to associate with the Kubernetes API server. 
            
            These DNS names are embedded in the TLS certificate presented by
            the API server as subject alternative names, which can be used in
            conjunction with your DNS server to securely connect a client to
            the server.. This attribute was added in vSphere API 8.0.0.1.
        """
        self.certificate_dns_names = certificate_dns_names
        VapiStruct.__init__(self)


KubeAPIServerSecurity._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.kube_API_server_security', {
        'certificate_dns_names': type.ListType(type.StringType()),
    },
    KubeAPIServerSecurity,
    False,
    None))



class KubeAPIServerOptions(VapiStruct):
    """
    
    
    ``KubeAPIServerOptions`` declares options for the Kubernetes API Server. 
    
    The API server is used to manage workloads on the workload network.. This
    class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 security=None,
                ):
        """
        :type  security: :class:`KubeAPIServerSecurity` or ``None``
        :param security: 
            
            :attr:`KubeAPIServerOptions.security` allows you to specify
            configuration options for the API server security.. This attribute
            was added in vSphere API 8.0.0.1.
            If None, default security parameters will be configured.
        """
        self.security = security
        VapiStruct.__init__(self)


KubeAPIServerOptions._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.kube_API_server_options', {
        'security': type.OptionalType(type.ReferenceType(__name__, 'KubeAPIServerSecurity')),
    },
    KubeAPIServerOptions,
    False,
    None))



class Conditions(VapiInterface):
    """
    The ``Conditions`` class provides methods to retrieve conditions related to
    a particular Supervisor. This class was added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisors.conditions'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ConditionsStub)
        self._VAPI_OPERATION_IDS = {}

    class Severity(Enum):
        """
        The ``Conditions.Severity`` class represents the severity of the message.
        This enumeration was added in vSphere API 8.0.0.1.

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
        Informational message. This class attribute was added in vSphere API
        8.0.0.1.

        """
        WARNING = None
        """
        Warning message. This class attribute was added in vSphere API 8.0.0.1.

        """
        ERROR = None
        """
        Error message. This class attribute was added in vSphere API 8.0.0.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Severity` instance.
            """
            Enum.__init__(string)

    Severity._set_values({
        'INFO': Severity('INFO'),
        'WARNING': Severity('WARNING'),
        'ERROR': Severity('ERROR'),
    })
    Severity._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.supervisors.conditions.severity',
        Severity))


    class Message(VapiStruct):
        """
        The ``Conditions.Message`` class contains user-readable information related
        to a ``Conditions.Condition``. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     severity=None,
                     details=None,
                    ):
            """
            :type  severity: :class:`Conditions.Severity`
            :param severity: Type of the message. This attribute was added in vSphere API
                8.0.0.1.
            :type  details: :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param details: Details about the message. This attribute was added in vSphere API
                8.0.0.1.
                If None, message details are not required for taking actions.
            """
            self.severity = severity
            self.details = details
            VapiStruct.__init__(self)


    Message._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.conditions.message', {
            'severity': type.ReferenceType(__name__, 'Conditions.Severity'),
            'details': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        Message,
        False,
        None))


    class Condition(VapiStruct):
        """
        The ``Conditions.Condition`` class defines an observation of the
        configuration state of a Supervisor. This class was added in vSphere API
        8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     type=None,
                     description=None,
                     status=None,
                     last_transition_time=None,
                     reason=None,
                     severity=None,
                     messages=None,
                    ):
            """
            :type  type: :class:`str`
            :param type: The type of the condition is a CamelCase, machine readable
                identifier, indicating the configuration stage.
                InfrastructureInitialized, ControlPlaneVMsDeployed and
                ControlPlaneVMsConfigured are examples of such identifiers. This
                attribute was added in vSphere API 8.0.0.1.
            :type  description: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param description: Description of the condition type in a human readable format. This
                attribute was added in vSphere API 8.0.0.1.
            :type  status: :class:`Conditions.Condition.Status`
            :param status: The status of the condition. This attribute was added in vSphere
                API 8.0.0.1.
            :type  last_transition_time: :class:`datetime.datetime` or ``None``
            :param last_transition_time: Last time the condition transitioned from one state to another. A
                transition happens when the value of status or severity field
                changes. This attribute was added in vSphere API 8.0.0.1.
                if None, there are no ongoing operations related to bringing the
                condition to the desired state.
            :type  reason: :class:`str`
            :param reason: A brief CamelCase message indicating details about the reason for
                the last transition. FailedWithSystemError,
                ManagementDNSServersMissing and WaitForNodeUpgrade are examples of
                such messages. This attribute was added in vSphere API 8.0.0.1.
            :type  severity: :class:`Conditions.Severity`
            :param severity: Provides an explicit classification of the reason identifier. Can
                be set when the value of status is not TRUE. This attribute was
                added in vSphere API 8.0.0.1.
            :type  messages: :class:`list` of :class:`Conditions.Message`
            :param messages: A list of human-readable messages that provide additional details
                about the last transition. This attribute was added in vSphere API
                8.0.0.1.
            """
            self.type = type
            self.description = description
            self.status = status
            self.last_transition_time = last_transition_time
            self.reason = reason
            self.severity = severity
            self.messages = messages
            VapiStruct.__init__(self)


        class Status(Enum):
            """
            Status of the condition, which can be one of TRUE, FALSE or UNKNOWN. This
            enumeration was added in vSphere API 8.0.0.1.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            TRUE = None
            """
            Indicates that the condition has reached the desired state. This class
            attribute was added in vSphere API 8.0.0.1.

            """
            FALSE = None
            """
            Indicates that the condition has not reached the desired state. This class
            attribute was added in vSphere API 8.0.0.1.

            """
            UNKNOWN = None
            """
            Indicates that the status of the condition can not be determined. This
            class attribute was added in vSphere API 8.0.0.1.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Status` instance.
                """
                Enum.__init__(string)

        Status._set_values({
            'TRUE': Status('TRUE'),
            'FALSE': Status('FALSE'),
            'UNKNOWN': Status('UNKNOWN'),
        })
        Status._set_binding_type(type.EnumType(
            'com.vmware.vcenter.namespace_management.supervisors.conditions.condition.status',
            Status))

    Condition._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.conditions.condition', {
            'type': type.StringType(),
            'description': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
            'status': type.ReferenceType(__name__, 'Conditions.Condition.Status'),
            'last_transition_time': type.OptionalType(type.DateTimeType()),
            'reason': type.StringType(),
            'severity': type.ReferenceType(__name__, 'Conditions.Severity'),
            'messages': type.ListType(type.ReferenceType(__name__, 'Conditions.Message')),
        },
        Condition,
        False,
        None))


    class ConditionGroup(VapiStruct):
        """
        The ``Conditions.ConditionGroup`` class defines a group for the observation
        of related configuration states of Supervisor. This class was added in
        vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     type=None,
                     description=None,
                     conditions=None,
                    ):
            """
            :type  type: :class:`str`
            :param type: The type of the condition group is a CamelCase, machine readable
                identifier, indicating the group of related configuration stages.
                UpgradePrechecks, and Components are examples of such identifiers.
                This attribute was added in vSphere API 8.0.3.0.
            :type  description: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param description: Description of the condition group type in a human readable format.
                This attribute was added in vSphere API 8.0.3.0.
            :type  conditions: :class:`list` of :class:`Conditions.Condition`
            :param conditions: Information about all the conditions constituting condition group,
                each condition represents the configuration stage. This attribute
                was added in vSphere API 8.0.3.0.
            """
            self.type = type
            self.description = description
            self.conditions = conditions
            VapiStruct.__init__(self)


    ConditionGroup._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.conditions.condition_group', {
            'type': type.StringType(),
            'description': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
            'conditions': type.ListType(type.ReferenceType(__name__, 'Conditions.Condition')),
        },
        ConditionGroup,
        False,
        None))



    def get(self,
            supervisor,
            ):
        """
        Get all conditions of a given Supervisor. This method was added in
        vSphere API 8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: the identifier for a Supervisor.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :rtype: :class:`list` of :class:`Conditions.Condition`
        :return: List of :class:`Conditions.Condition` objects related to the given
            Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if authorization information cannot be retrieved.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the Supervisor cannot be found, or if the user does not have
            read privilege on it.
        """
        return self._invoke('get',
                            {
                            'supervisor': supervisor,
                            })
class ContainerImageRegistries(VapiInterface):
    """
    The ``ContainerImageRegistries`` class provides methods to manage container
    image registries on a Supervisor. Supervisor service and PodVM container
    images will be pulled from those defined container registries. This class
    was added in vSphere API 8.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisors.container_image_registries'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ContainerImageRegistriesStub)
        self._VAPI_OPERATION_IDS = {}

    class CreateSpec(VapiStruct):
        """
        The ``ContainerImageRegistries.CreateSpec`` class provides a specification
        required to create a container image registry. This class was added in
        vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     name=None,
                     image_registry=None,
                     default_registry=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: Name of the container image registry. This name is unique across
                all container image registries in one Supervisor. This attribute
                was added in vSphere API 8.0.3.0.
            :type  image_registry: :class:`ImageRegistry`
            :param image_registry: The :attr:`ContainerImageRegistries.CreateSpec.image_registry`
                class contains the specification required to configure a container
                image registry endpoint. This attribute was added in vSphere API
                8.0.3.0.
            :type  default_registry: :class:`bool` or ``None``
            :param default_registry: Indicates if this container image registry serves as the default
                option when multiple registries exist, and no specific registry is
                specified. If there is already a default image registry, the new
                registry set to default will overwrite the original default
                setting. If there are one or more container image registries
                associated with the Supervisor, but none of them is set as the
                default, Docker Hub will be treated as the default. This attribute
                was added in vSphere API 8.0.3.0.
                If None, this registry is not used as the default option.
            """
            self.name = name
            self.image_registry = image_registry
            self.default_registry = default_registry
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.container_image_registries.create_spec', {
            'name': type.StringType(),
            'image_registry': type.ReferenceType(__name__, 'ImageRegistry'),
            'default_registry': type.OptionalType(type.BooleanType()),
        },
        CreateSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``ContainerImageRegistries.UpdateSpec`` class contains the
        specification required to update a container image registry. This class was
        added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     name=None,
                     hostname=None,
                     port=None,
                     username=None,
                     password=None,
                     certificate_chain=None,
                     default_registry=None,
                    ):
            """
            :type  name: :class:`str` or ``None``
            :param name: Name of the container image registry. This attribute was added in
                vSphere API 8.0.3.0.
                If None then no update will be made.
            :type  hostname: :class:`str` or ``None``
            :param hostname: IP address or the hostname of the container image registry. This
                attribute was added in vSphere API 8.0.3.0.
                If None then no update will be made.
            :type  port: :class:`long` or ``None``
            :param port: Port number of the container image registry. This attribute was
                added in vSphere API 8.0.3.0.
                If None then no update will be made.
            :type  username: :class:`str` or ``None``
            :param username: A username to be used for username/password authentication with
                this registry. This attribute was added in vSphere API 8.0.3.0.
                If None then no update will be made.
            :type  password: :class:`str` or ``None``
            :param password: The password for the user. This attribute was added in vSphere API
                8.0.3.0.
                If None then no update will be made.
            :type  certificate_chain: :class:`str` or ``None``
            :param certificate_chain: certificateChain contains PEM-encoded CA chain which is used to
                verify x509 certificates received from the server. This attribute
                was added in vSphere API 8.0.3.0.
                If None then no update will be made.
            :type  default_registry: :class:`bool` or ``None``
            :param default_registry: Indicates if this registry is used as default. This attribute was
                added in vSphere API 8.0.3.0.
                If None then no update will be made.
            """
            self.name = name
            self.hostname = hostname
            self.port = port
            self.username = username
            self.password = password
            self.certificate_chain = certificate_chain
            self.default_registry = default_registry
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.container_image_registries.update_spec', {
            'name': type.OptionalType(type.StringType()),
            'hostname': type.OptionalType(type.StringType()),
            'port': type.OptionalType(type.IntegerType()),
            'username': type.OptionalType(type.StringType()),
            'password': type.OptionalType(type.SecretType()),
            'certificate_chain': type.OptionalType(type.StringType()),
            'default_registry': type.OptionalType(type.BooleanType()),
        },
        UpdateSpec,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``ContainerImageRegistries.Info`` class contains the detailed
        information about the container image registry. This class was added in
        vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     id=None,
                     name=None,
                     image_registry=None,
                     default_registry=None,
                    ):
            """
            :type  id: :class:`str`
            :param id: Identifier of the container image registry. This attribute was
                added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.ContainerImageRegistry``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.ContainerImageRegistry``.
            :type  name: :class:`str`
            :param name: Name of the container image registry. This attribute was added in
                vSphere API 8.0.3.0.
            :type  image_registry: :class:`ImageRegistry`
            :param image_registry: The :attr:`ContainerImageRegistries.Info.image_registry` class
                contains the specification of the container image registry
                endpoint. This attribute was added in vSphere API 8.0.3.0.
            :type  default_registry: :class:`bool`
            :param default_registry: Indicates if this registry is used as default. This attribute was
                added in vSphere API 8.0.3.0.
            """
            self.id = id
            self.name = name
            self.image_registry = image_registry
            self.default_registry = default_registry
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.container_image_registries.info', {
            'id': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.ContainerImageRegistry'),
            'name': type.StringType(),
            'image_registry': type.ReferenceType(__name__, 'ImageRegistry'),
            'default_registry': type.BooleanType(),
        },
        Info,
        False,
        None))



    def create(self,
               supervisor,
               spec,
               ):
        """
        Defines a new container image registry for the given Supervisor. This
        method was added in vSphere API 8.0.3.0.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor on which the container image registry
            is created.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  spec: :class:`ContainerImageRegistries.CreateSpec`
        :param spec: Specification for setting up the container image registry.
        :rtype: :class:`ContainerImageRegistries.Info`
        :return: Information about the container image registry created on the
            Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the name of the container image registry specified in ``spec``
            already exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            for any other errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``supervisor`` doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the Namespaces.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if this Supervisor cluster does not support configuring container
            image registries.
        """
        return self._invoke('create',
                            {
                            'supervisor': supervisor,
                            'spec': spec,
                            })

    def update(self,
               supervisor,
               container_image_registry,
               spec,
               ):
        """
        Update the given container image registry configuration for the given
        Supervisor. This method was added in vSphere API 8.0.3.0.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor on which the container image registry
            is created.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  container_image_registry: :class:`str`
        :param container_image_registry: Identifier for the container image registry.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.ContainerImageRegistry``.
        :type  spec: :class:`ContainerImageRegistries.UpdateSpec`
        :param spec: Specification for updating the container image registry
            configuration.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the name of the container image registry specified in ``spec``
            already exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            for any other errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``supervisor`` or ``container_image_registry`` doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the Namespaces.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if this Supervisor cluster does not support configuring container
            image registries.
        """
        return self._invoke('update',
                            {
                            'supervisor': supervisor,
                            'container_image_registry': container_image_registry,
                            'spec': spec,
                            })

    def delete(self,
               supervisor,
               container_image_registry,
               ):
        """
        Delete the given container image registry from the given Supervisor.
        This method was added in vSphere API 8.0.3.0.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor on which the container image registry
            is created.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  container_image_registry: :class:`str`
        :param container_image_registry: Identifier for the container image registry.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.ContainerImageRegistry``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            for any other errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``supervisor`` or ``container_image_registry`` doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the Namespaces.Manage privilege.
        """
        return self._invoke('delete',
                            {
                            'supervisor': supervisor,
                            'container_image_registry': container_image_registry,
                            })

    def list(self,
             supervisor,
             ):
        """
        Lists all container image registries on the given Supervisor. This
        method was added in vSphere API 8.0.3.0.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor on which the container image registry
            is created.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :rtype: :class:`list` of :class:`ContainerImageRegistries.Info`
        :return: The list of all configured container image registries for the given
            Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            for any other errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``supervisor`` doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the System.Read privilege.
        """
        return self._invoke('list',
                            {
                            'supervisor': supervisor,
                            })

    def get(self,
            supervisor,
            container_image_registry,
            ):
        """
        Get information about the given container image registry for the given
        Supervisor. This method was added in vSphere API 8.0.3.0.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor on which the container image registry
            is created.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  container_image_registry: :class:`str`
        :param container_image_registry: Identifier for the container image registry.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.ContainerImageRegistry``.
        :rtype: :class:`ContainerImageRegistries.Info`
        :return: Information about the given container image registry for the given
            Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            for any other errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``supervisor`` or ``container_image_registry`` doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'supervisor': supervisor,
                            'container_image_registry': container_image_registry,
                            })
class Summary(VapiInterface):
    """
    
    
    The ``Summary`` class provides methods to retrieve the current states of
    Supervisors. 
    
    Only the basic information of the given Supervisor is being queried.. This
    class was added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisors.summary'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SummaryStub)
        self._VAPI_OPERATION_IDS = {}

    class ConfigStatus(Enum):
        """
        The ``Summary.ConfigStatus`` class describes the status of reaching the
        desired state configuration for the Supervisor. This enumeration was added
        in vSphere API 8.0.0.1.

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
        The Namespace configuration is being applied to the Supervisor. This class
        attribute was added in vSphere API 8.0.0.1.

        """
        REMOVING = None
        """
        The Namespace configuration is being removed from the Supervisor. This
        class attribute was added in vSphere API 8.0.0.1.

        """
        RUNNING = None
        """
        The Supervisor is configured correctly with the Namespace configuration.
        This class attribute was added in vSphere API 8.0.0.1.

        """
        ERROR = None
        """
        Failed to apply the Namespace configuration to the Supervisor, user
        intervention needed. This class attribute was added in vSphere API 8.0.0.1.

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
        'RUNNING': ConfigStatus('RUNNING'),
        'ERROR': ConfigStatus('ERROR'),
    })
    ConfigStatus._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.supervisors.summary.config_status',
        ConfigStatus))


    class KubernetesStatus(Enum):
        """
        The ``Summary.KubernetesStatus`` class describes the Supervisor's ability
        to deploy pods. This enumeration was added in vSphere API 8.0.0.1.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        READY = None
        """
        The Supervisor is able to accept pods. This class attribute was added in
        vSphere API 8.0.0.1.

        """
        WARNING = None
        """
        The Supervisor may be able to accept pods, but has warning messages. This
        class attribute was added in vSphere API 8.0.0.1.

        """
        ERROR = None
        """
        The Supervisor may not be able to accept pods and has error messages. This
        class attribute was added in vSphere API 8.0.0.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`KubernetesStatus` instance.
            """
            Enum.__init__(string)

    KubernetesStatus._set_values({
        'READY': KubernetesStatus('READY'),
        'WARNING': KubernetesStatus('WARNING'),
        'ERROR': KubernetesStatus('ERROR'),
    })
    KubernetesStatus._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.supervisors.summary.kubernetes_status',
        KubernetesStatus))


    class Stats(VapiStruct):
        """
        The ``Summary.Stats`` class contains the basic runtime statistics about a
        Supervisor. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     cpu_used=None,
                     cpu_capacity=None,
                     memory_used=None,
                     memory_capacity=None,
                     storage_used=None,
                     storage_capacity=None,
                    ):
            """
            :type  cpu_used: :class:`long`
            :param cpu_used: Overall CPU usage of the Supervisor, in MHz. This is the sum of CPU
                usage across all worker nodes in the Supervisor. This attribute was
                added in vSphere API 8.0.0.1.
            :type  cpu_capacity: :class:`long`
            :param cpu_capacity: Total CPU capacity in the Supervisor, in MHz. This is the sum of
                CPU capacities from all worker nodes in the Supervisor. This
                attribute was added in vSphere API 8.0.0.1.
            :type  memory_used: :class:`long`
            :param memory_used: Overall memory usage of the Supervisor, in mebibytes. This is the
                sum of memory usage across all worker nodes in the Supervisor. This
                attribute was added in vSphere API 8.0.0.1.
            :type  memory_capacity: :class:`long`
            :param memory_capacity: Total memory capacity of the Supervisor in mebibytes. This is the
                sum of memory capacities from all worker nodes in the Supervisor.
                This attribute was added in vSphere API 8.0.0.1.
            :type  storage_used: :class:`long`
            :param storage_used: Overall storage used by the Supervisor, in mebibytes. This is the
                sum of storage used across all worker nodes in the Supervisor. This
                attribute was added in vSphere API 8.0.0.1.
            :type  storage_capacity: :class:`long`
            :param storage_capacity: Overall storage capacity of the Supervisor, in mebibytes. This is
                the sum of total storage available from all worker nodes in the
                Cluster. This attribute was added in vSphere API 8.0.0.1.
            """
            self.cpu_used = cpu_used
            self.cpu_capacity = cpu_capacity
            self.memory_used = memory_used
            self.memory_capacity = memory_capacity
            self.storage_used = storage_used
            self.storage_capacity = storage_capacity
            VapiStruct.__init__(self)


    Stats._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.summary.stats', {
            'cpu_used': type.IntegerType(),
            'cpu_capacity': type.IntegerType(),
            'memory_used': type.IntegerType(),
            'memory_capacity': type.IntegerType(),
            'storage_used': type.IntegerType(),
            'storage_capacity': type.IntegerType(),
        },
        Stats,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Summary.Info`` class contains the basic information about the
        statistics and status related to the Supervisor. This class was added in
        vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     name=None,
                     stats=None,
                     config_status=None,
                     kubernetes_status=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: Name of the Supervisor. This attribute was added in vSphere API
                8.0.0.1.
            :type  stats: :class:`Summary.Stats`
            :param stats: Basic runtime statistics for the Supervisor. This attribute was
                added in vSphere API 8.0.0.1.
            :type  config_status: :class:`Summary.ConfigStatus`
            :param config_status: Current status of reaching the desired state configuration for the
                Supervisor. This attribute was added in vSphere API 8.0.0.1.
            :type  kubernetes_status: :class:`Summary.KubernetesStatus`
            :param kubernetes_status: Current Status of the Supervisor's ability to deploy pods. This
                attribute was added in vSphere API 8.0.0.1.
            """
            self.name = name
            self.stats = stats
            self.config_status = config_status
            self.kubernetes_status = kubernetes_status
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.summary.info', {
            'name': type.StringType(),
            'stats': type.ReferenceType(__name__, 'Summary.Stats'),
            'config_status': type.ReferenceType(__name__, 'Summary.ConfigStatus'),
            'kubernetes_status': type.ReferenceType(__name__, 'Summary.KubernetesStatus'),
        },
        Info,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        A ``Summary.FilterSpec`` can be specified to filter summary output by any
        allowed criteria. An empty ``Summary.FilterSpec`` will cause all results of
        the query to be returned. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     config_status=None,
                     kubernetes_status=None,
                    ):
            """
            :type  config_status: :class:`Summary.ConfigStatus` or ``None``
            :param config_status: Matches Supervisors with :attr:`Summary.Info.config_status` equal
                to the specified value. This attribute was added in vSphere API
                8.0.0.1.
                if None this filter is not applied.
            :type  kubernetes_status: :class:`Summary.KubernetesStatus` or ``None``
            :param kubernetes_status: Matches Supervisors with the :attr:`Summary.Info.kubernetes_status`
                equal to the specified value. This attribute was added in vSphere
                API 8.0.0.1.
                if None this filter is not applied.
            """
            self.config_status = config_status
            self.kubernetes_status = kubernetes_status
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.summary.filter_spec', {
            'config_status': type.OptionalType(type.ReferenceType(__name__, 'Summary.ConfigStatus')),
            'kubernetes_status': type.OptionalType(type.ReferenceType(__name__, 'Summary.KubernetesStatus')),
        },
        FilterSpec,
        False,
        None))


    class ListItem(VapiStruct):
        """
        The ``Summary.ListItem`` class contains information about a Supervisor
        returned by :func:`Summary.list` method. This class was added in vSphere
        API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor=None,
                     info=None,
                    ):
            """
            :type  supervisor: :class:`str`
            :param supervisor: The immutable identifier of the Supervisor generated during
                enablement. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
            :type  info: :class:`Summary.Info`
            :param info: The current state of the Supervisor. This attribute was added in
                vSphere API 8.0.0.1.
            """
            self.supervisor = supervisor
            self.info = info
            VapiStruct.__init__(self)


    ListItem._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.summary.list_item', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'info': type.ReferenceType(__name__, 'Summary.Info'),
        },
        ListItem,
        False,
        None))


    class ListResult(VapiStruct):
        """
        The ``Summary.ListResult`` class represents the result of
        :func:`Summary.list` method. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     items=None,
                    ):
            """
            :type  items: :class:`list` of :class:`Summary.ListItem`
            :param items: List of items. This attribute was added in vSphere API 8.0.0.1.
            """
            self.items = items
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.summary.list_result', {
            'items': type.ListType(type.ReferenceType(__name__, 'Summary.ListItem')),
        },
        ListResult,
        False,
        None))



    def get(self,
            supervisor,
            ):
        """
        Queries the current state of the specified Supervisor. This method was
        added in vSphere API 8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: the identifier for a supervisor
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :rtype: :class:`Summary.Info`
        :return: :class:`Summary.Info` of the Supervisor matching the provided
            identifier.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the Supervisor matching the ID does not exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have ``Namespaces.Manage`` privilege and the
            ``System.Read`` privilege on all vSphere Clusters hosting the
            Supervisor.
        """
        return self._invoke('get',
                            {
                            'supervisor': supervisor,
                            })

    def list(self,
             filter=None,
             ):
        """
        Queries the current state of all Supervisors. Optionally, apply the
        filter to Supervisors that match the criteria in the
        :class:`Summary.FilterSpec`. This method was added in vSphere API
        8.0.0.1.

        :type  filter: :class:`Summary.FilterSpec` or ``None``
        :param filter: Set of parameters that can be used to constrain the results of the
            method.
            if None all records will be returned.
        :rtype: :class:`Summary.ListResult`
        :return: ListResult of :class:`Summary.Info` of all Supervisors matching the
            criteria in the :class:`Summary.FilterSpec`.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have ``Namespaces.Manage`` privilege and the
            ``System.Read`` privilege on all vSphere Clusters hosting the
            Supervisor.
        """
        return self._invoke('list',
                            {
                            'filter': filter,
                            })
class SupervisorServices(VapiInterface):
    """
    The ``SupervisorServices`` class provides methods to install and manage
    running instances of Supervisor Services on a Supervisor cluster. Existing
    methods under
    :class:`com.vmware.vcenter.namespace_management.supervisor_services_client.ClusterSupervisorServices`
    will be migrated to this interface. This class was added in vSphere API
    8.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisors.supervisor_services'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SupervisorServicesStub)
        self._VAPI_OPERATION_IDS = {}

    class Message(VapiStruct):
        """
        The ``SupervisorServices.Message`` class contains the information about the
        Supervisor Service on a Supervisor, it could be compatibility information,
        service status information, etc. This class was added in vSphere API
        8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     severity=None,
                     details=None,
                    ):
            """
            :type  severity: :class:`SupervisorServices.Message.MessageSeverity`
            :param severity: Type of the message. This attribute was added in vSphere API
                8.0.3.0.
            :type  details: :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param details: Details about the message. This attribute was added in vSphere API
                8.0.3.0.
                If None, message details are not required for taking actions.
            """
            self.severity = severity
            self.details = details
            VapiStruct.__init__(self)


        class MessageSeverity(Enum):
            """
            The ``SupervisorServices.Message.MessageSeverity`` class represents the
            severity of the message. This enumeration was added in vSphere API 8.0.3.0.

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
            attribute was added in vSphere API 8.0.3.0.

            """
            WARNING = None
            """
            Warning message. This may be accompanied by vCenter event. This class
            attribute was added in vSphere API 8.0.3.0.

            """
            ERROR = None
            """
            Error message. This is accompanied by vCenter event and/or alarm. This
            class attribute was added in vSphere API 8.0.3.0.

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
            'com.vmware.vcenter.namespace_management.supervisors.supervisor_services.message.message_severity',
            MessageSeverity))

    Message._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.supervisor_services.message', {
            'severity': type.ReferenceType(__name__, 'SupervisorServices.Message.MessageSeverity'),
            'details': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        Message,
        False,
        None))


    class PrecheckSpec(VapiStruct):
        """
        The ``SupervisorServices.PrecheckSpec`` class contains the specification
        required to check whether a Supervisor Service version is compatible with
        the Supervisor cluster. This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     target_version=None,
                    ):
            """
            :type  target_version: :class:`str`
            :param target_version: Identifier of the Supervisor Service version that the prechecks are
                running for. This attribute was added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
            """
            self.target_version = target_version
            VapiStruct.__init__(self)


    PrecheckSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.supervisor_services.precheck_spec', {
            'target_version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
        },
        PrecheckSpec,
        False,
        None))


    class PrecheckResult(VapiStruct):
        """
        This class contains the result of the last valid
        :func:`SupervisorServices.precheck` method for installing or upgrading to a
        Supervisor Service version on a specific Supervisor. This class was added
        in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     target_version=None,
                     original_version=None,
                     status=None,
                     status_messages=None,
                     precheck_finish_time=None,
                    ):
            """
            :type  target_version: :class:`str`
            :param target_version: Identifier of the target Supervisor Service version that the
                prechecks were running for. This attribute was added in vSphere API
                8.0.3.0.
            :type  original_version: :class:`str` or ``None``
            :param original_version: Identifier of the version of the Supervisor Service installed on
                the Supervisor at the time when the prechecks were performed. It
                should always match the version of the Supervisor Service currently
                installed on the Supervisor. If the Supervisor Service on the
                Supervisor has been upgraded or deleted since the last prechecks,
                the stale results will be purged. This attribute was added in
                vSphere API 8.0.3.0.
                If None, there was no version installed when the prechecks were
                performed.
            :type  status: :class:`SupervisorServices.PrecheckResult.Status`
            :param status: Status of the last precheck result. This attribute was added in
                vSphere API 8.0.3.0.
            :type  status_messages: :class:`list` of :class:`SupervisorServices.Message` or ``None``
            :param status_messages: A set of messages that provide additional details of the last valid
                precheck result, including errors and warnings for potential
                incompatibility. This attribute was added in vSphere API 8.0.3.0.
                If None, the target version is compatible with the Supervisor.
            :type  precheck_finish_time: :class:`datetime.datetime`
            :param precheck_finish_time: The timestamp at which the compatibility pre-check finished. This
                attribute was added in vSphere API 8.0.3.0.
            """
            self.target_version = target_version
            self.original_version = original_version
            self.status = status
            self.status_messages = status_messages
            self.precheck_finish_time = precheck_finish_time
            VapiStruct.__init__(self)


        class Status(Enum):
            """
            Status of a precheck result, can be either compatible or incompatible. This
            enumeration was added in vSphere API 8.0.3.0.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            COMPATIBLE = None
            """
            The target version is compatible with the Supervisor. This class attribute
            was added in vSphere API 8.0.3.0.

            """
            INCOMPATIBLE = None
            """
            The target version is incompatible with the Supervisor. This class
            attribute was added in vSphere API 8.0.3.0.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Status` instance.
                """
                Enum.__init__(string)

        Status._set_values({
            'COMPATIBLE': Status('COMPATIBLE'),
            'INCOMPATIBLE': Status('INCOMPATIBLE'),
        })
        Status._set_binding_type(type.EnumType(
            'com.vmware.vcenter.namespace_management.supervisors.supervisor_services.precheck_result.status',
            Status))

    PrecheckResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.supervisor_services.precheck_result', {
            'target_version': type.StringType(),
            'original_version': type.OptionalType(type.StringType()),
            'status': type.ReferenceType(__name__, 'SupervisorServices.PrecheckResult.Status'),
            'status_messages': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'SupervisorServices.Message'))),
            'precheck_finish_time': type.DateTimeType(),
        },
        PrecheckResult,
        False,
        None))



    def precheck(self,
                 supervisor,
                 supervisor_service,
                 spec,
                 ):
        """
        Initiates a pre-check for installing or upgrading to a Supervisor
        Service version on the given Supervisor. For example, if a Supervisor
        is running version 1.0 of a service, use this API with a target version
        of 2.0 to know if the service version 2.0 is also compatible with this
        Supervisor. The pre-check result can be fetched asynchronously by
        :func:`SupervisorServices.get_precheck_result` method. This method was
        added in vSphere API 8.0.3.0.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor on which to initiate the pre-check.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier of the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :type  spec: :class:`SupervisorServices.PrecheckSpec`
        :param spec: Specification for the Supervisor Service pre-check.
        :rtype: :class:`str`
        :return: The task identifier for the precheck operation.
            The return value will be an identifier for the resource type:
            ``com.vmware.cis.task``.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor with the ID ``supervisor`` or Supervisor Service with
            the ID ``supervisor_service`` or the version defined in ``spec``
            could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor is configuring or being removed.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the Supervisor doesn't support Supervisor Service or Supervisor
            Service precheck.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the SupervisorServices.Install privilege
            on the specified Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            for any other error.
        """
        return self._invoke('precheck',
                            {
                            'supervisor': supervisor,
                            'supervisor_service': supervisor_service,
                            'spec': spec,
                            })

    def get_precheck_result(self,
                            supervisor,
                            supervisor_service,
                            target_version,
                            ):
        """
        Get the result of the last valid :func:`SupervisorServices.precheck`
        method for a specific Supervisor Service version on a Supervisor. If
        the Supervisor Service on the Supervisor has been installed, upgraded
        or deleted since the last :func:`SupervisorServices.precheck` method,
        the stale result will be purged and the user should re-initiate a
        :func:`SupervisorServices.precheck` method. This method was added in
        vSphere API 8.0.3.0.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier for the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :type  target_version: :class:`str`
        :param target_version: Identifier for the target version to run the pre-check with.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
        :rtype: :class:`SupervisorServices.PrecheckResult`
        :return: The result of the last valid :func:`SupervisorServices.precheck`
            method for the Supervisor Service version on the Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor with the ID ``supervisor`` or Supervisor Service with
            the ID ``supervisor_service`` or version with the ID
            ``target_version`` could not be located or there is no valid
            pre-check result available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the Supervisor doesn't support Supervisor Service or Supervisor
            Service precheck.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the SupervisorServices.Install privilege
            on the specified Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            for any other error.
        """
        return self._invoke('get_precheck_result',
                            {
                            'supervisor': supervisor,
                            'supervisor_service': supervisor_service,
                            'target_version': target_version,
                            })
class Topology(VapiInterface):
    """
    The ``Topology`` class provides methods to query the topological layout of
    the infrastructure a Supervisor is running on. This class was added in
    vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisors.topology'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _TopologyStub)
        self._VAPI_OPERATION_IDS = {}

    class Info(VapiStruct):
        """
        The ``Topology.Info`` class contains the basic information about the
        association between vSphere Zones and vSphere Clusters. This class was
        added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     zone=None,
                     clusters=None,
                    ):
            """
            :type  zone: :class:`str`
            :param zone: Identifier of this vSphere Zone. This attribute was added in
                vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``.
            :type  clusters: :class:`list` of :class:`str`
            :param clusters: A list of vSphere Cluster identifiers that are associated with the
                vSphere Zone. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will contain identifiers for
                the resource type: ``ClusterComputeResource``.
            """
            self.zone = zone
            self.clusters = clusters
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.topology.info', {
            'zone': type.IdType(resource_types='com.vmware.vcenter.consumption_domains.Zone'),
            'clusters': type.ListType(type.IdType()),
        },
        Info,
        False,
        None))



    def get(self,
            supervisor,
            ):
        """
        Queries the current association between vSphere Zones and vSphere
        Clusters from the given Supervisor ID. A Supervisor can be running on
        one or multiple vSphere Zones, and each vSphere Zone is associated with
        one or more vSphere Clusters. Use the vSphere Cluster IDs obtained from
        :func:`Topology.get` to call the APIs that requires a vSphere Cluster
        ID instead of a Supervisor. This method was added in vSphere API
        8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for a Supervisor.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :rtype: :class:`list` of :class:`Topology.Info`
        :return: List of :class:`Topology.Info` of vSphere Zone and vSphere Cluster
            associations.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if given Supervisor does not exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have ``Namespaces.Manage`` privilege and the
            ``System.Read`` privilege on all vSphere Clusters hosting the
            Supervisor.
        """
        return self._invoke('get',
                            {
                            'supervisor': supervisor,
                            })
class _ConditionsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/conditions',
            path_variables={
                'supervisor': 'supervisor',
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
                'output_type': type.ListType(type.ReferenceType(__name__, 'Conditions.Condition')),
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
            self, iface_name='com.vmware.vcenter.namespace_management.supervisors.conditions',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _ContainerImageRegistriesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'spec': type.ReferenceType(__name__, 'ContainerImageRegistries.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/container-image-registries',
            request_body_parameter='spec',
            path_variables={
                'supervisor': 'supervisor',
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

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'container_image_registry': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.ContainerImageRegistry'),
            'spec': type.ReferenceType(__name__, 'ContainerImageRegistries.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/container-image-registries/{containerImageRegistry}',
            request_body_parameter='spec',
            path_variables={
                'supervisor': 'supervisor',
                'container_image_registry': 'containerImageRegistry',
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
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'container_image_registry': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.ContainerImageRegistry'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
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
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/container-image-registries/{containerImageRegistry}',
            path_variables={
                'supervisor': 'supervisor',
                'container_image_registry': 'containerImageRegistry',
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
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
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
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/container-image-registries',
            path_variables={
                'supervisor': 'supervisor',
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
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'container_image_registry': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.ContainerImageRegistry'),
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
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/container-image-registries/{containerImageRegistry}',
            path_variables={
                'supervisor': 'supervisor',
                'container_image_registry': 'containerImageRegistry',
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
                'output_type': type.ReferenceType(__name__, 'ContainerImageRegistries.Info'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'update': {
                'input_type': update_input_type,
                'output_type': type.VoidType(),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': update_output_validator_list,
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
                'output_type': type.ListType(type.ReferenceType(__name__, 'ContainerImageRegistries.Info')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'ContainerImageRegistries.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'create': create_rest_metadata,
            'update': update_rest_metadata,
            'delete': delete_rest_metadata,
            'list': list_rest_metadata,
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.supervisors.container_image_registries',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _SummaryStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
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
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/summary',
            path_variables={
                'supervisor': 'supervisor',
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
            'filter': type.OptionalType(type.ReferenceType(__name__, 'Summary.FilterSpec')),
        })
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
            url_template='/vcenter/namespace-management/supervisors/summaries',
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
                'output_type': type.ReferenceType(__name__, 'Summary.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ReferenceType(__name__, 'Summary.ListResult'),
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
            self, iface_name='com.vmware.vcenter.namespace_management.supervisors.summary',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _SupervisorServicesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for precheck operation
        precheck_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'spec': type.ReferenceType(__name__, 'SupervisorServices.PrecheckSpec'),
        })
        precheck_error_dict = {
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        precheck_input_value_validator_list = [
        ]
        precheck_output_validator_list = [
        ]
        precheck_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/supervisor-services/{supervisorService}',
            request_body_parameter='spec',
            path_variables={
                'supervisor': 'supervisor',
                'supervisor_service': 'supervisorService',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'precheck',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for get_precheck_result operation
        get_precheck_result_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'target_version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
        })
        get_precheck_result_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        get_precheck_result_input_value_validator_list = [
        ]
        get_precheck_result_output_validator_list = [
        ]
        get_precheck_result_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/supervisor-services/{supervisorService}/versions/{targetVersion}/precheck',
            path_variables={
                'supervisor': 'supervisor',
                'supervisor_service': 'supervisorService',
                'target_version': 'targetVersion',
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
            'precheck': {
                'input_type': precheck_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.task'),
                'errors': precheck_error_dict,
                'input_value_validator_list': precheck_input_value_validator_list,
                'output_validator_list': precheck_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get_precheck_result': {
                'input_type': get_precheck_result_input_type,
                'output_type': type.ReferenceType(__name__, 'SupervisorServices.PrecheckResult'),
                'errors': get_precheck_result_error_dict,
                'input_value_validator_list': get_precheck_result_input_value_validator_list,
                'output_validator_list': get_precheck_result_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'precheck': precheck_rest_metadata,
            'get_precheck_result': get_precheck_result_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.supervisors.supervisor_services',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _TopologyStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
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
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/topology',
            path_variables={
                'supervisor': 'supervisor',
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
                'output_type': type.ListType(type.ReferenceType(__name__, 'Topology.Info')),
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
            self, iface_name='com.vmware.vcenter.namespace_management.supervisors.topology',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Conditions': Conditions,
        'ContainerImageRegistries': ContainerImageRegistries,
        'Summary': Summary,
        'SupervisorServices': SupervisorServices,
        'Topology': Topology,
        'identity': 'com.vmware.vcenter.namespace_management.supervisors.identity_client.StubFactory',
        'networks': 'com.vmware.vcenter.namespace_management.supervisors.networks_client.StubFactory',
        'recovery': 'com.vmware.vcenter.namespace_management.supervisors.recovery_client.StubFactory',
    }

