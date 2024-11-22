# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.namespace_management_client`` module provides classes
for managing Namespaces.

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

class ProxySettingsSource(Enum):
    """
    The settings can be inherited from the vCenter settings, so the cluster
    settings will be synced. The settings can be applied directly on the
    cluster level, or the cluster can be configured not to use a proxy. This
    enumeration was added in vSphere API 7.0.3.00100.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    VC_INHERITED = None
    """
    Proxy settings will be inherited from the vCenter settings. vCenter and
    cluster settings will be kept in sync. This class attribute was added in
    vSphere API 7.0.3.00100.

    """
    CLUSTER_CONFIGURED = None
    """
    Proxy settings will be configured at the cluster level. This class
    attribute was added in vSphere API 7.0.3.00100.

    """
    NONE = None
    """
    No proxy settings will be applied to the cluster. This class attribute was
    added in vSphere API 7.0.3.00100.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`ProxySettingsSource` instance.
        """
        Enum.__init__(string)

ProxySettingsSource._set_values({
    'VC_INHERITED': ProxySettingsSource('VC_INHERITED'),
    'CLUSTER_CONFIGURED': ProxySettingsSource('CLUSTER_CONFIGURED'),
    'NONE': ProxySettingsSource('NONE'),
})
ProxySettingsSource._set_binding_type(type.EnumType(
    'com.vmware.vcenter.namespace_management.proxy_settings_source',
    ProxySettingsSource))



class SizingHint(Enum):
    """
    The ``SizingHint`` class determines the configuration of Kubernetes API
    server and the worker nodes. It also determines the default values
    associated with the maximum number of pods and services. Use
    :func:`ClusterSizeInfo.get` to get information associated with a
    ``SizingHint``.

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
    Cluster size of 'tiny'.

    """
    SMALL = None
    """
    Cluster size of 'small'.

    """
    MEDIUM = None
    """
    Cluster size of 'medium'.

    """
    LARGE = None
    """
    Cluster size of 'large'.

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
    'com.vmware.vcenter.namespace_management.sizing_hint',
    SizingHint))




class IPRange(VapiStruct):
    """
    The ``IPRange`` class is used to express a range of IP addresses. The
    formats supported by this structure will depend on the IP addressing scheme
    that is being used by vSphere Namespaces. Currently, vSphere Namespaces
    only supports IPv4. This class was added in vSphere API 7.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 address=None,
                 count=None,
                ):
        """
        :type  address: :class:`str`
        :param address: The starting address of the range. This attribute was added in
            vSphere API 7.0.1.0.
        :type  count: :class:`long`
        :param count: The number of IP addresses in the range. This attribute was added
            in vSphere API 7.0.1.0.
        """
        self.address = address
        self.count = count
        VapiStruct.__init__(self)


IPRange._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.IP_range', {
        'address': type.StringType(),
        'count': type.IntegerType(),
    },
    IPRange,
    False,
    None))



class Ipv4Cidr(VapiStruct):
    """
    The ``Ipv4Cidr`` class contains the specification for representing CIDR
    notation of IP range. For example, this can be used to represent 256 IP
    addresses using 10.10.10.0/24.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 address=None,
                 prefix=None,
                ):
        """
        :type  address: :class:`str`
        :param address: The IPv4 address.
        :type  prefix: :class:`long`
        :param prefix: The CIDR prefix.
        """
        self.address = address
        self.prefix = prefix
        VapiStruct.__init__(self)


Ipv4Cidr._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.ipv4_cidr', {
        'address': type.StringType(),
        'prefix': type.IntegerType(),
    },
    Ipv4Cidr,
    False,
    None))



class ProxyConfiguration(VapiStruct):
    """
    The ``ProxyConfiguration`` class defines proxy configuration to be used by
    the Supervisor. This class was added in vSphere API 7.0.3.00100.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """

    _validator_list = [
        UnionValidator(
            'proxy_settings_source',
            {
                'CLUSTER_CONFIGURED' : [('https_proxy_config', False), ('http_proxy_config', False), ('no_proxy_config', False), ('tls_root_ca_bundle', False)],
                'VC_INHERITED' : [],
                'NONE' : [],
            }
        ),
    ]



    def __init__(self,
                 proxy_settings_source=None,
                 https_proxy_config=None,
                 http_proxy_config=None,
                 no_proxy_config=None,
                 tls_root_ca_bundle=None,
                ):
        """
        :type  proxy_settings_source: :class:`ProxySettingsSource`
        :param proxy_settings_source: The source of the proxy settings. If
            :attr:`ProxySettingsSource.VC_INHERITED` or
            :attr:`ProxySettingsSource.NONE` is specified, then the other
            configuration in ``ProxyConfiguration`` will be ignored. This
            attribute was added in vSphere API 7.0.3.00100.
        :type  https_proxy_config: :class:`str` or ``None``
        :param https_proxy_config: HTTPS proxy configuration. Examples: 
            
            * http://username:password\\\\@proxy.vmware.com:8080
            * https://proxy.vmware.com:4443
            
            This will be used if :attr:`ProxySettingsSource.CLUSTER_CONFIGURED`
            is used for the source, otherwise this will be ignored. This
            attribute was added in vSphere API 7.0.3.00100.
            If None no HTTPS proxy will be used.
        :type  http_proxy_config: :class:`str` or ``None``
        :param http_proxy_config: HTTP proxy configuration. Examples: 
            
            * http://username:password\\\\@proxy.vmware.com:8080
            * https://proxy.vmware.com:4443
            
            This will be used if :attr:`ProxySettingsSource.CLUSTER_CONFIGURED`
            is used for the source, otherwise this will be ignored. This
            attribute was added in vSphere API 7.0.3.00100.
            If None no HTTP proxy will be used.
        :type  no_proxy_config: :class:`list` of :class:`str` or ``None``
        :param no_proxy_config: List of addresses that should be accessed directly. This will be
            used if :attr:`ProxySettingsSource.CLUSTER_CONFIGURED` is used for
            the source, otherwise this will be ignored. This attribute was
            added in vSphere API 7.0.3.00100.
            If None there won't be any excluded addresses.
        :type  tls_root_ca_bundle: :class:`str` or ``None``
        :param tls_root_ca_bundle: Proxy TLS root CA bundle which will be used to verify the proxy's
            certificates. Every certificate in the bundle is expected to be in
            PEM format. This will be used if
            :attr:`ProxySettingsSource.CLUSTER_CONFIGURED` is used for the
            source, otherwise this will be ignored. This attribute was added in
            vSphere API 7.0.3.00100.
            If None only the vCenter certificates applied in VECS (VMware
            Endpoint Certificate Store) will be used.
        """
        self.proxy_settings_source = proxy_settings_source
        self.https_proxy_config = https_proxy_config
        self.http_proxy_config = http_proxy_config
        self.no_proxy_config = no_proxy_config
        self.tls_root_ca_bundle = tls_root_ca_bundle
        VapiStruct.__init__(self)


ProxyConfiguration._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.proxy_configuration', {
        'proxy_settings_source': type.ReferenceType(__name__, 'ProxySettingsSource'),
        'https_proxy_config': type.OptionalType(type.StringType()),
        'http_proxy_config': type.OptionalType(type.StringType()),
        'no_proxy_config': type.OptionalType(type.ListType(type.StringType())),
        'tls_root_ca_bundle': type.OptionalType(type.StringType()),
    },
    ProxyConfiguration,
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
            :attr:`com.vmware.vcenter.namespace_management.supervisors_client.ControlPlane.storage_policy`.
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
    'com.vmware.vcenter.namespace_management.workloads_storage_config', {
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
            from :func:`Clusters.enable`, :func:`Clusters.update` and
            :func:`Clusters.set` APIs. 
            
            An empty list may be specified to disable file volume support on
            the Supervisor.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``ClusterComputeResource``. When methods return a value of this
            class as a return value, the attribute will contain identifiers for
            the resource type: ``ClusterComputeResource``.
        """
        self.vsan_clusters = vsan_clusters
        VapiStruct.__init__(self)


CNSFileConfig._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.CNS_file_config', {
        'vsan_clusters': type.ListType(type.IdType()),
    },
    CNSFileConfig,
    False,
    None))



class Clusters(VapiInterface):
    """
    The ``Clusters`` class provides methods to enable and disable vSphere
    Namespaces on a vSphere cluster.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.clusters'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ClustersStub)
        self._VAPI_OPERATION_IDS = {}

    class ConfigStatus(Enum):
        """
        The ``Clusters.ConfigStatus`` class describes the status of reaching the
        desired state configuration for the cluster.

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
        The Namespace configuration is being applied to the cluster.

        """
        REMOVING = None
        """
        The Namespace configuration is being removed from the cluster.

        """
        RUNNING = None
        """
        The cluster is configured correctly with the Namespace configuration.

        """
        ERROR = None
        """
        Failed to apply the Namespace configuration to the cluster, user
        intervention needed.

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
        'com.vmware.vcenter.namespace_management.clusters.config_status',
        ConfigStatus))


    class KubernetesStatus(Enum):
        """
        The ``Clusters.KubernetesStatus`` class describes the cluster's ability to
        deploy pods.

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
        The cluster is able to accept pods.

        """
        WARNING = None
        """
        The cluster may be able to accept pods, but has warning messages.

        """
        ERROR = None
        """
        The cluster may not be able to accept pods and has error messages.

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
        'com.vmware.vcenter.namespace_management.clusters.kubernetes_status',
        KubernetesStatus))


    class NetworkProvider(Enum):
        """
        Identifies the network plugin that cluster networking functionalities for
        this vSphere Namespaces Cluster.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        NSXT_CONTAINER_PLUGIN = None
        """
        NSX-T Container Plugin.

        """
        VSPHERE_NETWORK = None
        """
        vSphere Networking. This class attribute was added in vSphere API 7.0.1.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`NetworkProvider` instance.
            """
            Enum.__init__(string)

    NetworkProvider._set_values({
        'NSXT_CONTAINER_PLUGIN': NetworkProvider('NSXT_CONTAINER_PLUGIN'),
        'VSPHERE_NETWORK': NetworkProvider('VSPHERE_NETWORK'),
    })
    NetworkProvider._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.clusters.network_provider',
        NetworkProvider))


    class Message(VapiStruct):
        """
        The ``Clusters.Message`` class contains the information about the object
        configuration.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     severity=None,
                     details=None,
                     kb_article_link=None,
                     id=None,
                    ):
            """
            :type  severity: :class:`Clusters.Message.Severity`
            :param severity: Type of the message.
            :type  details: :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param details: Details about the message.
                If None, message details are not required for taking actions.
            :type  kb_article_link: :class:`str` or ``None``
            :param kb_article_link: Optional link to a KB article providing more details about the
                message. This attribute was added in vSphere API 8.0.2.0.
                if None there is not KB article associated with the message.
            :type  id: :class:`str` or ``None``
            :param id: Unique identifier of the message. This attribute was added in
                vSphere API 8.0.2.0.
                if None there is no id associated with the message.
            """
            self.severity = severity
            self.details = details
            self.kb_article_link = kb_article_link
            self.id = id
            VapiStruct.__init__(self)


        class Severity(Enum):
            """
            The ``Clusters.Message.Severity`` class represents the severity of the
            message.

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
            Informational message. This may be accompanied by vCenter event.

            """
            WARNING = None
            """
            Warning message. This may be accompanied by vCenter event.

            """
            ERROR = None
            """
            Error message. This is accompanied by vCenter event and/or alarm.

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
            'com.vmware.vcenter.namespace_management.clusters.message.severity',
            Severity))

    Message._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.message', {
            'severity': type.ReferenceType(__name__, 'Clusters.Message.Severity'),
            'details': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
            'kb_article_link': type.OptionalType(type.StringType()),
            'id': type.OptionalType(type.StringType()),
        },
        Message,
        False,
        None))


    class Stats(VapiStruct):
        """
        The ``Clusters.Stats`` class contains the basic runtime statistics about a
        vSphere Namespaces-enabled cluster.

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
            :param cpu_used: Overall CPU usage of the cluster, in MHz. This is the sum of CPU
                usage across all worker nodes in the cluster.
            :type  cpu_capacity: :class:`long`
            :param cpu_capacity: Total CPU capacity in the cluster available for vSphere Namespaces,
                in MHz. This is the sum of CPU capacities from all worker nodes in
                the cluster.
            :type  memory_used: :class:`long`
            :param memory_used: Overall memory usage of the cluster, in mebibytes. This is the sum
                of memory usage across all worker nodes in the cluster.
            :type  memory_capacity: :class:`long`
            :param memory_capacity: Total memory capacity of the cluster available for vSphere
                Namespaces, in mebibytes. This is the sum of memory capacities from
                all worker nodesin the cluster.
            :type  storage_used: :class:`long`
            :param storage_used: Overall storage used by the cluster, in mebibytes. This is the sum
                of storage used across all worker nodes in the cluster.
            :type  storage_capacity: :class:`long`
            :param storage_capacity: Overall storage capacity of the cluster available for vSphere
                Namespaces, in mebibytes. This is the sum of total storage
                available from all worker nodes in the cluster.
            """
            self.cpu_used = cpu_used
            self.cpu_capacity = cpu_capacity
            self.memory_used = memory_used
            self.memory_capacity = memory_capacity
            self.storage_used = storage_used
            self.storage_capacity = storage_capacity
            VapiStruct.__init__(self)


    Stats._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.stats', {
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


    class Condition(VapiStruct):
        """
        The ``Clusters.Condition`` class defines an observation of the
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
                ControlPlaneVMsConfigured are examples of such identifiers.. This
                attribute was added in vSphere API 8.0.0.1.
            :type  description: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param description: Description of the condition type in a human readable format. This
                attribute was added in vSphere API 8.0.0.1.
            :type  status: :class:`Clusters.Condition.Status`
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
                the last transition. 
                
                FailedWithSystemError, ManagementDNSServersMissing and
                WaitForNodeUpgrade are examples of such messages.. This attribute
                was added in vSphere API 8.0.0.1.
            :type  severity: :class:`Clusters.Condition.Severity`
            :param severity: Provides an explicit classification of the reason identifier. Set
                when the value of status is FALSE. This attribute was added in
                vSphere API 8.0.0.1.
            :type  messages: :class:`list` of :class:`Clusters.Message`
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
            'com.vmware.vcenter.namespace_management.clusters.condition.status',
            Status))

        class Severity(Enum):
            """
            The ``Clusters.Condition.Severity`` class represents the severity of the
            message. This enumeration was added in vSphere API 8.0.0.1.

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
            'com.vmware.vcenter.namespace_management.clusters.condition.severity',
            Severity))

    Condition._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.condition', {
            'type': type.StringType(),
            'description': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
            'status': type.ReferenceType(__name__, 'Clusters.Condition.Status'),
            'last_transition_time': type.OptionalType(type.DateTimeType()),
            'reason': type.StringType(),
            'severity': type.ReferenceType(__name__, 'Clusters.Condition.Severity'),
            'messages': type.ListType(type.ReferenceType(__name__, 'Clusters.Message')),
        },
        Condition,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``Clusters.Summary`` class contains the basic information about the
        cluster statistics and status related to vSphere Namespaces.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     cluster=None,
                     cluster_name=None,
                     stats=None,
                     config_status=None,
                     kubernetes_status=None,
                    ):
            """
            :type  cluster: :class:`str`
            :param cluster: Identifier for the cluster.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            :type  cluster_name: :class:`str`
            :param cluster_name: Name of the cluster.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource.name``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``ClusterComputeResource.name``.
            :type  stats: :class:`Clusters.Stats`
            :param stats: Basic runtime statistics for the cluster.
            :type  config_status: :class:`Clusters.ConfigStatus`
            :param config_status: Current setting for ``Clusters.ConfigStatus``.
            :type  kubernetes_status: :class:`Clusters.KubernetesStatus`
            :param kubernetes_status: Current setting for ``Clusters.KubernetesStatus``.
            """
            self.cluster = cluster
            self.cluster_name = cluster_name
            self.stats = stats
            self.config_status = config_status
            self.kubernetes_status = kubernetes_status
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.summary', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'cluster_name': type.IdType(resource_types='ClusterComputeResource.name'),
            'stats': type.ReferenceType(__name__, 'Clusters.Stats'),
            'config_status': type.ReferenceType(__name__, 'Clusters.ConfigStatus'),
            'kubernetes_status': type.ReferenceType(__name__, 'Clusters.KubernetesStatus'),
        },
        Summary,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Clusters.Info`` class contains detailed information about the cluster
        statistics and status related to vSphere Namespaces.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'network_provider',
                {
                    'NSXT_CONTAINER_PLUGIN' : [('ncp_cluster_network_info', True)],
                    'VSPHERE_NETWORK' : [('workload_networks', True), ('load_balancers', True)],
                }
            ),
        ]


        _canonical_to_pep_names = {
                                'master_DNS': 'master_dns',
                                'worker_DNS': 'worker_dns',
                                'Master_DNS_names': 'master_dns_names',
                                'master_DNS_search_domains': 'master_dns_search_domains',
                                'master_NTP_servers': 'master_ntp_servers',
                                }

        def __init__(self,
                     size_hint=None,
                     stat_summary=None,
                     config_status=None,
                     conditions=None,
                     messages=None,
                     kubernetes_status=None,
                     kubernetes_status_messages=None,
                     api_server_management_endpoint=None,
                     api_server_cluster_endpoint=None,
                     api_servers=None,
                     tls_management_endpoint_certificate=None,
                     tls_endpoint_certificate=None,
                     network_provider=None,
                     ncp_cluster_network_info=None,
                     workload_networks=None,
                     workload_ntp_servers=None,
                     load_balancers=None,
                     service_cidr=None,
                     master_management_network=None,
                     master_dns=None,
                     worker_dns=None,
                     master_storage_policy=None,
                     ephemeral_storage_policy=None,
                     cns_file_config=None,
                     login_banner=None,
                     master_dns_names=None,
                     image_storage=None,
                     default_image_registry=None,
                     default_image_repository=None,
                     master_dns_search_domains=None,
                     master_ntp_servers=None,
                     default_kubernetes_service_content_library=None,
                     cluster_proxy_config=None,
                     content_libraries=None,
                    ):
            """
            :type  size_hint: :class:`SizingHint`
            :param size_hint: Current setting for ``SizingHint``. This affects the size and
                resources allocated to the Kubernetes API server. This attribute
                was added in vSphere API 7.0.1.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  stat_summary: :class:`Clusters.Stats`
            :param stat_summary: Basic runtime statistics for the cluster.
            :type  config_status: :class:`Clusters.ConfigStatus`
            :param config_status: Current setting for ``Clusters.ConfigStatus``.
            :type  conditions: :class:`list` of :class:`Clusters.Condition`
            :param conditions: The conditions that need to be met for the cluster to reach the
                desired state. This attribute was added in vSphere API 8.0.0.1.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  messages: :class:`list` of :class:`Clusters.Message`
            :param messages: Current set of messages associated with the object.
            :type  kubernetes_status: :class:`Clusters.KubernetesStatus`
            :param kubernetes_status: Current setting for ``Clusters.KubernetesStatus``.
            :type  kubernetes_status_messages: :class:`list` of :class:`Clusters.Message`
            :param kubernetes_status_messages: Current set of messages associated with the object.
            :type  api_server_management_endpoint: :class:`str`
            :param api_server_management_endpoint: Kubernetes API Server IP address on the management network. This is
                a floating IP and assigned to one of the control plane VMs on the
                management network. 
                
                This endpoint is used by vSphere components.
            :type  api_server_cluster_endpoint: :class:`str`
            :param api_server_cluster_endpoint: Kubernetes API Server IP address via cluster network. This is the
                IP address of the Kubernetes LoadBalancer type service fronting the
                apiservers. 
                
                This endpoint is the one configured in kubeconfig after login, and
                used for most human and application interaction with Kubernetes.
            :type  api_servers: :class:`set` of :class:`str`
            :param api_servers: Identifier of the Kubernetes API servers. These are the IP
                addresses of the VM instances for the Kubernetes control plane on
                the management network.
            :type  tls_management_endpoint_certificate: :class:`str` or ``None``
            :param tls_management_endpoint_certificate: PEM-encoded x509 certificate used by TLS endpoint on Kubernetes API
                servers when accessed from the management network, e.g. from ESX
                servers or VCSA.
                :class:`set` only when
                :attr:`Clusters.Info.api_server_management_endpoint` is used.
            :type  tls_endpoint_certificate: :class:`str` or ``None``
            :param tls_endpoint_certificate: PEM-encoded x509 certificate(s) used by TLS endpoint on Kubernetes
                API servers when accessed via the load balancer, e.g. devops user
                on corporate network. 
                
                In case of a certificates chain, the order of the certificates in
                this field is important. The first certificate must be the leaf
                certificate for your domain name, the second the intermediate
                certificate(s) and the last one must be the root certificate.
                :class:`set` only when
                :attr:`Clusters.Info.api_server_management_endpoint` is used.
            :type  network_provider: :class:`Clusters.NetworkProvider`
            :param network_provider: The provider of cluster networking for this vSphere Namespaces
                cluster.
            :type  ncp_cluster_network_info: :class:`Clusters.NCPClusterNetworkInfo`
            :param ncp_cluster_network_info: Specification for the NSX Container Plugin cluster network.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN`.
            :type  workload_networks: :class:`Clusters.WorkloadNetworksInfo`
            :param workload_networks: Information about workload networks associated with the cluster.
                This attribute was added in vSphere API 7.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK`.
            :type  workload_ntp_servers: :class:`list` of :class:`str` or ``None``
            :param workload_ntp_servers: Information about NTP server DNS names or IP addresses to use for
                workloads such as Tanzu Kubernetes Grid VMs, specified in order of
                preference. This attribute was added in vSphere API 7.0.1.0.
                None when NTP server for Kubernetes API servers is used.
            :type  load_balancers: :class:`list` of :class:`LoadBalancers.Info`
            :param load_balancers: Information related to the Load balancer used for provisioning
                virtual servers in the namespace. This attribute was added in
                vSphere API 7.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK`.
            :type  service_cidr: :class:`Ipv4Cidr`
            :param service_cidr: CIDR block from which Kubernetes allocates service cluster IP
                addresses.
            :type  master_management_network: :class:`Clusters.NetworkSpec`
            :param master_management_network: Specification for the management network on Kubernetes API server.
                This attribute was added in vSphere API 7.0.1.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  master_dns: :class:`list` of :class:`str` or ``None``
            :param master_dns: List of DNS server IP addresses to use on Kubernetes API server,
                specified in order of preference.
                If None, no default DNS servers are set.
            :type  worker_dns: :class:`list` of :class:`str` or ``None``
            :param worker_dns: List of DNS server IP addresses to use for pods that execute on the
                worker nodes (which are native pods on ESXi hosts in the vSphere
                Namespaces Supervisor).
                If None, no default DNS servers are set.
            :type  master_storage_policy: :class:`str`
            :param master_storage_policy: Identifier of storage policy associated with Kubernetes API server.
                This attribute was added in vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  ephemeral_storage_policy: :class:`str`
            :param ephemeral_storage_policy: Identifier of storage policy associated with ephemeral disks of all
                the Kubernetes Pods in the cluster. This attribute was added in
                vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  cns_file_config: :class:`CNSFileConfig` or ``None``
            :param cns_file_config: Specification for configuring Cloud Native Storage file volume
                support on Supervisor. This feature provides support for
                provisioning ReadWriteMany persistent volumes on this cluster
                and/or external clusters. This attribute was added in vSphere API
                7.0.3.0.
                If None, it means the file volume support is not enabled on this
                Supervisor.
            :type  login_banner: :class:`str` or ``None``
            :param login_banner: Disclaimer to be displayed prior to login via the Kubectl plugin.
                This attribute was added in vSphere API 7.0.1.0.
                If None, just skip it.
            :type  master_dns_names: :class:`list` of :class:`str` or ``None``
            :param master_dns_names: List of DNS names to associate with the Kubernetes API server.
                These DNS names are embedded in the TLS certificate presented by
                the API server. This attribute was added in vSphere API 7.0.1.0.
                If None, no DNS names are embedded in the TLS certificate.
            :type  image_storage: :class:`Clusters.ImageStorageSpec`
            :param image_storage: Specification for storage to be used for container images. This
                attribute was added in vSphere API 7.0.1.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  default_image_registry: :class:`Clusters.ImageRegistry` or ``None``
            :param default_image_registry: Default image registry to use when Kubernetes Pod container
                specification does not specify it as part of the container image
                name. This attribute was added in vSphere API 7.0.1.0.
                If None, defaults to Docker Hub.
            :type  default_image_repository: :class:`str` or ``None``
            :param default_image_repository: Default image repository to use when Kubernetes Pod container
                specification does not specify it as part of the container image
                name. This attribute was added in vSphere API 7.0.1.0.
                If None, defaults to Docker Hub official repository in case of
                Docker Hub image registry, otherwise defaults to empty string.
            :type  master_dns_search_domains: :class:`list` of :class:`str` or ``None``
            :param master_dns_search_domains: List of domains (for example "vmware.com") to be searched when
                trying to lookup a host name on Kubernetes API server, specified in
                order of preference.
                If None, no default DNS search domains are set.
            :type  master_ntp_servers: :class:`list` of :class:`str` or ``None``
            :param master_ntp_servers: List of NTP server DNS names or IP addresses to use on Kubernetes
                API server, specified in order of preference. This attribute was
                added in vSphere API 7.0.1.0.
                If None, VMware Tools based time synchronization is enabled.
            :type  default_kubernetes_service_content_library: :class:`str` or ``None``
            :param default_kubernetes_service_content_library: Identifier of the Content Library which holds the VM Images for
                vSphere Kubernetes Service. 
                
                This Content Library should be subscribed to VMware's hosted
                vSphere Kubernetes Service Repository.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.content.Library``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``com.vmware.content.Library``.
                If None, no Content Library set for vSphere Kubernetes Service.
            :type  cluster_proxy_config: :class:`ProxyConfiguration`
            :param cluster_proxy_config: Proxy configuration that is applied to the Supervisor. The proxy
                should be reachable from the management network and is used for
                image pulling and container traffic exiting out of the Supervisor. 
                Note that the proxy password will be removed from the URLs as per
                Section 3.2.1 of RFC3986 security recommendation. This attribute
                was added in vSphere API 7.0.3.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  content_libraries: :class:`list` of :class:`Clusters.ContentLibrarySpec` or ``None``
            :param content_libraries: List of Content Libraries associated with a Supervisor. This list
                refers to existing Content Libraries in the vSphere inventory.
                These Content Libraries and the Content Library items belonging to
                them are read-only across all vSphere Namespaces. This list does
                not overlap with the
                :attr:`Clusters.Info.default_kubernetes_service_content_library`. .
                This attribute was added in vSphere API 8.0.2.0.
                If None,  no additional Content Libraries are set for the
                Supervisor apart from the default Kubernetes Service Content
                Library. 
            """
            self.size_hint = size_hint
            self.stat_summary = stat_summary
            self.config_status = config_status
            self.conditions = conditions
            self.messages = messages
            self.kubernetes_status = kubernetes_status
            self.kubernetes_status_messages = kubernetes_status_messages
            self.api_server_management_endpoint = api_server_management_endpoint
            self.api_server_cluster_endpoint = api_server_cluster_endpoint
            self.api_servers = api_servers
            self.tls_management_endpoint_certificate = tls_management_endpoint_certificate
            self.tls_endpoint_certificate = tls_endpoint_certificate
            self.network_provider = network_provider
            self.ncp_cluster_network_info = ncp_cluster_network_info
            self.workload_networks = workload_networks
            self.workload_ntp_servers = workload_ntp_servers
            self.load_balancers = load_balancers
            self.service_cidr = service_cidr
            self.master_management_network = master_management_network
            self.master_dns = master_dns
            self.worker_dns = worker_dns
            self.master_storage_policy = master_storage_policy
            self.ephemeral_storage_policy = ephemeral_storage_policy
            self.cns_file_config = cns_file_config
            self.login_banner = login_banner
            self.master_dns_names = master_dns_names
            self.image_storage = image_storage
            self.default_image_registry = default_image_registry
            self.default_image_repository = default_image_repository
            self.master_dns_search_domains = master_dns_search_domains
            self.master_ntp_servers = master_ntp_servers
            self.default_kubernetes_service_content_library = default_kubernetes_service_content_library
            self.cluster_proxy_config = cluster_proxy_config
            self.content_libraries = content_libraries
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.info', {
            'size_hint': type.OptionalType(type.ReferenceType(__name__, 'SizingHint')),
            'stat_summary': type.ReferenceType(__name__, 'Clusters.Stats'),
            'config_status': type.ReferenceType(__name__, 'Clusters.ConfigStatus'),
            'conditions': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Clusters.Condition'))),
            'messages': type.ListType(type.ReferenceType(__name__, 'Clusters.Message')),
            'kubernetes_status': type.ReferenceType(__name__, 'Clusters.KubernetesStatus'),
            'kubernetes_status_messages': type.ListType(type.ReferenceType(__name__, 'Clusters.Message')),
            'api_server_management_endpoint': type.StringType(),
            'api_server_cluster_endpoint': type.StringType(),
            'api_servers': type.SetType(type.StringType()),
            'tls_management_endpoint_certificate': type.OptionalType(type.StringType()),
            'tls_endpoint_certificate': type.OptionalType(type.StringType()),
            'network_provider': type.ReferenceType(__name__, 'Clusters.NetworkProvider'),
            'ncp_cluster_network_info': type.OptionalType(type.ReferenceType(__name__, 'Clusters.NCPClusterNetworkInfo')),
            'workload_networks': type.OptionalType(type.ReferenceType(__name__, 'Clusters.WorkloadNetworksInfo')),
            'workload_ntp_servers': type.OptionalType(type.ListType(type.StringType())),
            'load_balancers': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'LoadBalancers.Info'))),
            'service_cidr': type.ReferenceType(__name__, 'Ipv4Cidr'),
            'master_management_network': type.OptionalType(type.ReferenceType(__name__, 'Clusters.NetworkSpec')),
            'master_DNS': type.OptionalType(type.ListType(type.StringType())),
            'worker_DNS': type.OptionalType(type.ListType(type.StringType())),
            'master_storage_policy': type.OptionalType(type.IdType()),
            'ephemeral_storage_policy': type.OptionalType(type.IdType()),
            'cns_file_config': type.OptionalType(type.ReferenceType(__name__, 'CNSFileConfig')),
            'login_banner': type.OptionalType(type.StringType()),
            'Master_DNS_names': type.OptionalType(type.ListType(type.StringType())),
            'image_storage': type.OptionalType(type.ReferenceType(__name__, 'Clusters.ImageStorageSpec')),
            'default_image_registry': type.OptionalType(type.ReferenceType(__name__, 'Clusters.ImageRegistry')),
            'default_image_repository': type.OptionalType(type.StringType()),
            'master_DNS_search_domains': type.OptionalType(type.ListType(type.StringType())),
            'master_NTP_servers': type.OptionalType(type.ListType(type.StringType())),
            'default_kubernetes_service_content_library': type.OptionalType(type.IdType()),
            'cluster_proxy_config': type.OptionalType(type.ReferenceType(__name__, 'ProxyConfiguration')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Clusters.ContentLibrarySpec'))),
        },
        Info,
        False,
        None))


    class ContentLibrarySpec(VapiStruct):
        """
        The ``Clusters.ContentLibrarySpec`` class contains the specification
        required to configure Content Libraries with a Supervisor. This class was
        added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     content_library=None,
                    ):
            """
            :type  content_library: :class:`str`
            :param content_library: Content Library ID associated with a Supervisor. The Content
                Library specified should exist in the vSphere inventory. This
                attribute was added in vSphere API 8.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.content.Library``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``com.vmware.content.Library``.
            """
            self.content_library = content_library
            VapiStruct.__init__(self)


    ContentLibrarySpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.content_library_spec', {
            'content_library': type.IdType(resource_types='com.vmware.content.Library'),
        },
        ContentLibrarySpec,
        False,
        None))


    class Ipv4Range(VapiStruct):
        """
        The ``Clusters.Ipv4Range`` contains specification to configure multiple
        interfaces in IPv4. The range of IPv4 addresses is derived by incrementing
        the startingAddress to the specified addressCount. To use the object for a
        single IPv4 address specification, set addressCount to 1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     starting_address=None,
                     address_count=None,
                     subnet_mask=None,
                     gateway=None,
                    ):
            """
            :type  starting_address: :class:`str`
            :param starting_address: The IPv4 address denoting the start of the range.
            :type  address_count: :class:`long`
            :param address_count: The number of IP addresses in the range. Addresses are derived by
                incrementing :attr:`Clusters.Ipv4Range.starting_address`.
            :type  subnet_mask: :class:`str`
            :param subnet_mask: Subnet mask to be set.
            :type  gateway: :class:`str`
            :param gateway: The IPv4 address of the gateway associated with the range indicated
                by :attr:`Clusters.Ipv4Range.starting_address` and
                :attr:`Clusters.Ipv4Range.address_count`.
            """
            self.starting_address = starting_address
            self.address_count = address_count
            self.subnet_mask = subnet_mask
            self.gateway = gateway
            VapiStruct.__init__(self)


    Ipv4Range._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.ipv4_range', {
            'starting_address': type.StringType(),
            'address_count': type.IntegerType(),
            'subnet_mask': type.StringType(),
            'gateway': type.StringType(),
        },
        Ipv4Range,
        False,
        None))


    class WorkloadNetworksEnableSpec(VapiStruct):
        """
        The ``Clusters.WorkloadNetworksEnableSpec`` contains the specification
        required to configure workload networks for a vSphere Namespaces Cluster
        during Enable operation. These workload networks will be used as backing
        network for Tanzu Kubernetes Cluster VMs and Kubernetes control plane VMs.
        This class was added in vSphere API 7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor_primary_workload_network=None,
                     network_list=None,
                    ):
            """
            :type  supervisor_primary_workload_network: :class:`Networks.CreateSpec`
            :param supervisor_primary_workload_network: The  of the vSphere Namespaces network that will be used by
                Kubernetes control plane VMs to expose Kubernetes API server to
                devops users and other workloads. It can also used as backing
                network for Tanzu Kubernetes Cluster VMs. This attribute was added
                in vSphere API 7.0.1.0.
            :type  network_list: :class:`list` of :class:`Networks.CreateSpec` or ``None``
            :param network_list: classes for additional list of vSphere Namespaces networks to be
                associated with this cluster. This attribute was added in vSphere
                API 7.0.1.0.
                If None no additional networks will be associated with the cluster.
            """
            self.supervisor_primary_workload_network = supervisor_primary_workload_network
            self.network_list = network_list
            VapiStruct.__init__(self)


    WorkloadNetworksEnableSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.workload_networks_enable_spec', {
            'supervisor_primary_workload_network': type.ReferenceType(__name__, 'Networks.CreateSpec'),
            'network_list': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Networks.CreateSpec'))),
        },
        WorkloadNetworksEnableSpec,
        False,
        None))


    class WorkloadNetworksInfo(VapiStruct):
        """
        The ``Clusters.WorkloadNetworksInfo`` contains information related to
        configuration of vSphere Namespaces Network objects. This class was added
        in vSphere API 7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor_primary_workload_network=None,
                     network_list=None,
                    ):
            """
            :type  supervisor_primary_workload_network: :class:`Networks.Info`
            :param supervisor_primary_workload_network: 
                
                vSphere Namespaces network used by Kubernetes control plane VMs to
                access load-balanced services on the various workload networks.
                
                . This attribute was added in vSphere API 7.0.1.0.
            :type  network_list: :class:`list` of :class:`Networks.Info` or ``None``
            :param network_list: List of vSphere Namespaces networks associated with this cluster.
                This attribute was added in vSphere API 7.0.1.0.
                If None no additional networks are associated with the cluster.
            """
            self.supervisor_primary_workload_network = supervisor_primary_workload_network
            self.network_list = network_list
            VapiStruct.__init__(self)


    WorkloadNetworksInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.workload_networks_info', {
            'supervisor_primary_workload_network': type.ReferenceType(__name__, 'Networks.Info'),
            'network_list': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Networks.Info'))),
        },
        WorkloadNetworksInfo,
        False,
        None))


    class NetworkSpec(VapiStruct):
        """
        The ``Clusters.NetworkSpec`` contains information related to network
        configuration for one or more interfaces.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'mode',
                {
                    'DHCP' : [('floating_IP', False)],
                    'STATICRANGE' : [('address_range', True)],
                }
            ),
        ]


        _canonical_to_pep_names = {
                                'floating_IP': 'floating_ip',
                                }

        def __init__(self,
                     floating_ip=None,
                     network=None,
                     network_segment=None,
                     mode=None,
                     address_range=None,
                    ):
            """
            :type  floating_ip: :class:`str` or ``None``
            :param floating_ip: Optionally specify the Floating IP used by the cluster control
                plane in case of DHCP.
                If None, the existing effective management network floating IP will
                be used.
            :type  network: :class:`str`
            :param network: Identifier for the network.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type: ``Network``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type: ``Network``.

                .. deprecated:: vSphere API 8.0.3.0
                    Use :attr:`Clusters.NetworkSpec.network_segment` instead. 
            :type  network_segment: :class:`com.vmware.vcenter.namespace_management.supervisors.networks_client.NetworkSegment` or ``None``
            :param network_segment: Backing Network segment. This attribute was added in vSphere API
                8.0.3.0.
                If None, :attr:`Clusters.NetworkSpec.network` is used as the
                backing network. Otherwise, this value takes precedence over
                :attr:`Clusters.NetworkSpec.network`.
            :type  mode: :class:`Clusters.NetworkSpec.Ipv4Mode`
            :param mode: The address assignment mode.
            :type  address_range: :class:`Clusters.Ipv4Range`
            :param address_range: Settings for the interfaces on the network.
                This attribute is optional and it is only relevant when the value
                of ``mode`` is :attr:`Clusters.NetworkSpec.Ipv4Mode.STATICRANGE`.
            """
            self.floating_ip = floating_ip
            self.network = network
            self.network_segment = network_segment
            self.mode = mode
            self.address_range = address_range
            VapiStruct.__init__(self)


        class Ipv4Mode(Enum):
            """
            The ``Clusters.NetworkSpec.Ipv4Mode`` class defines various IPv4 address
            assignment modes.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            DHCP = None
            """
            The address is automatically assigned by a DHCP server.

            """
            STATICRANGE = None
            """
            The address is static.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Ipv4Mode` instance.
                """
                Enum.__init__(string)

        Ipv4Mode._set_values({
            'DHCP': Ipv4Mode('DHCP'),
            'STATICRANGE': Ipv4Mode('STATICRANGE'),
        })
        Ipv4Mode._set_binding_type(type.EnumType(
            'com.vmware.vcenter.namespace_management.clusters.network_spec.ipv4_mode',
            Ipv4Mode))

    NetworkSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.network_spec', {
            'floating_IP': type.OptionalType(type.StringType()),
            'network': type.IdType(resource_types='Network'),
            'network_segment': type.OptionalType(type.ReferenceType('com.vmware.vcenter.namespace_management.supervisors.networks_client', 'NetworkSegment')),
            'mode': type.ReferenceType(__name__, 'Clusters.NetworkSpec.Ipv4Mode'),
            'address_range': type.OptionalType(type.ReferenceType(__name__, 'Clusters.Ipv4Range')),
        },
        NetworkSpec,
        False,
        None))


    class ImageRegistry(VapiStruct):
        """
        The ``Clusters.ImageRegistry`` class contains the specification required to
        configure container image registry endpoint.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     hostname=None,
                     port=None,
                    ):
            """
            :type  hostname: :class:`str`
            :param hostname: IP address or the hostname of container image registry.
            :type  port: :class:`long` or ``None``
            :param port: Port number of the container image registry.
                If None, defaults to 443.
            """
            self.hostname = hostname
            self.port = port
            VapiStruct.__init__(self)


    ImageRegistry._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.image_registry', {
            'hostname': type.StringType(),
            'port': type.OptionalType(type.IntegerType()),
        },
        ImageRegistry,
        False,
        None))


    class ImageStorageSpec(VapiStruct):
        """
        The ``Clusters.ImageStorageSpec`` class contains the specification required
        to configure storage used for container images.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     storage_policy=None,
                    ):
            """
            :type  storage_policy: :class:`str`
            :param storage_policy: Identifier of the storage policy.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
            """
            self.storage_policy = storage_policy
            VapiStruct.__init__(self)


    ImageStorageSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.image_storage_spec', {
            'storage_policy': type.IdType(resource_types='SpsStorageProfile'),
        },
        ImageStorageSpec,
        False,
        None))


    class NCPClusterNetworkInfo(VapiStruct):
        """
        The ``Clusters.NCPClusterNetworkInfo`` class contains the NSX Container
        Plugin-specific cluster networking configuration.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     pod_cidrs=None,
                     ingress_cidrs=None,
                     egress_cidrs=None,
                     cluster_distributed_switch=None,
                     nsx_edge_cluster=None,
                     default_ingress_tls_certificate=None,
                     nsx_tier0_gateway=None,
                     namespace_subnet_prefix=None,
                     routed_mode=None,
                    ):
            """
            :type  pod_cidrs: :class:`list` of :class:`Ipv4Cidr`
            :param pod_cidrs: CIDR blocks from which Kubernetes allocates pod IP addresses.
            :type  ingress_cidrs: :class:`list` of :class:`Ipv4Cidr`
            :param ingress_cidrs: CIDR blocks from which NSX assigns IP addresses for Kubernetes
                Ingresses and Kubernetes Services of type LoadBalancer.
            :type  egress_cidrs: :class:`list` of :class:`Ipv4Cidr`
            :param egress_cidrs: CIDR blocks from which NSX assigns IP addresses used for performing
                SNAT from container IPs to external IPs.
            :type  cluster_distributed_switch: :class:`str`
            :param cluster_distributed_switch: 
                
                vSphere Distributed Switch used to connect this cluster.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``vSphereDistributedSwitch``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``vSphereDistributedSwitch``.
            :type  nsx_edge_cluster: :class:`str`
            :param nsx_edge_cluster: NSX Edge cluster to be used for Kubernetes Services of type
                LoadBalancer, Kubernetes Ingresses, and NSX SNAT.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``NSXEdgeCluster``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``NSXEdgeCluster``.
            :type  default_ingress_tls_certificate: :class:`str`
            :param default_ingress_tls_certificate: PEM-encoded x509 certificate used by NSX as a default fallback
                certificate for Kubernetes Ingress services.
            :type  nsx_tier0_gateway: :class:`str` or ``None``
            :param nsx_tier0_gateway: NSX Tier0 Gateway used for this cluster. This attribute was added
                in vSphere API 7.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``NSXTier0Gateway``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``NSXTier0Gateway``.
                This is :class:`set` when the cluster uses NSX-T.
            :type  namespace_subnet_prefix: :class:`long` or ``None``
            :param namespace_subnet_prefix: Size of the subnet reserved for namespaces segments. This attribute
                was added in vSphere API 7.0.2.0.
                If None, defaults to 28.
            :type  routed_mode: :class:`bool` or ``None``
            :param routed_mode: Routed mode for this cluster. This attribute was added in vSphere
                API 7.0.2.0.
                If None, defaults to False.
            """
            self.pod_cidrs = pod_cidrs
            self.ingress_cidrs = ingress_cidrs
            self.egress_cidrs = egress_cidrs
            self.cluster_distributed_switch = cluster_distributed_switch
            self.nsx_edge_cluster = nsx_edge_cluster
            self.default_ingress_tls_certificate = default_ingress_tls_certificate
            self.nsx_tier0_gateway = nsx_tier0_gateway
            self.namespace_subnet_prefix = namespace_subnet_prefix
            self.routed_mode = routed_mode
            VapiStruct.__init__(self)


    NCPClusterNetworkInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.NCP_cluster_network_info', {
            'pod_cidrs': type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr')),
            'ingress_cidrs': type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr')),
            'egress_cidrs': type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr')),
            'cluster_distributed_switch': type.IdType(resource_types='vSphereDistributedSwitch'),
            'nsx_edge_cluster': type.IdType(resource_types='NSXEdgeCluster'),
            'default_ingress_tls_certificate': type.StringType(),
            'nsx_tier0_gateway': type.OptionalType(type.IdType()),
            'namespace_subnet_prefix': type.OptionalType(type.IntegerType()),
            'routed_mode': type.OptionalType(type.BooleanType()),
        },
        NCPClusterNetworkInfo,
        False,
        None))


    class NCPClusterNetworkEnableSpec(VapiStruct):
        """
        The ``Clusters.NCPClusterNetworkEnableSpec`` class encapsulates the NSX
        Container Plugin-specific cluster networking configuration parameters for
        the vSphere Namespaces Cluster Enable operation.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     pod_cidrs=None,
                     ingress_cidrs=None,
                     egress_cidrs=None,
                     cluster_distributed_switch=None,
                     nsx_edge_cluster=None,
                     nsx_tier0_gateway=None,
                     namespace_subnet_prefix=None,
                     routed_mode=None,
                    ):
            """
            :type  pod_cidrs: :class:`list` of :class:`Ipv4Cidr`
            :param pod_cidrs: CIDR blocks from which Kubernetes allocates pod IP addresses. This
                range should not overlap with those in
                :attr:`Clusters.EnableSpec.service_cidr`,
                :attr:`Clusters.NCPClusterNetworkEnableSpec.ingress_cidrs`,
                :attr:`Clusters.NCPClusterNetworkEnableSpec.egress_cidrs`, or other
                services running in the datacenter. All Pod CIDR blocks must be of
                at least subnet size /23.
            :type  ingress_cidrs: :class:`list` of :class:`Ipv4Cidr`
            :param ingress_cidrs: CIDR blocks from which NSX assigns IP addresses for Kubernetes
                Ingresses and Kubernetes Services of type LoadBalancer. These
                ranges should not overlap with those in
                :attr:`Clusters.NCPClusterNetworkEnableSpec.pod_cidrs`,
                :attr:`Clusters.EnableSpec.service_cidr`,
                :attr:`Clusters.NCPClusterNetworkEnableSpec.egress_cidrs`, or other
                services running in the datacenter.
            :type  egress_cidrs: :class:`list` of :class:`Ipv4Cidr`
            :param egress_cidrs: CIDR blocks from which NSX assigns IP addresses used for performing
                SNAT from container IPs to external IPs. These ranges should not
                overlap with those in
                :attr:`Clusters.NCPClusterNetworkEnableSpec.pod_cidrs`,
                :attr:`Clusters.EnableSpec.service_cidr`,
                :attr:`Clusters.NCPClusterNetworkEnableSpec.ingress_cidrs`, or
                other services running in the datacenter.
            :type  cluster_distributed_switch: :class:`str` or ``None``
            :param cluster_distributed_switch: vSphere Distributed Switch used to connect this cluster.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``vSphereDistributedSwitch``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``vSphereDistributedSwitch``.
                This field is required when configuring a cluster that uses NSX-T.
                If None and using NSXe, the system will choose a suitable vSphere
                Distributed Switch.
            :type  nsx_edge_cluster: :class:`str` or ``None``
            :param nsx_edge_cluster: NSX Edge cluster to be used for Kubernetes Services of type
                LoadBalancer, Kubernetes Ingresses, and NSX SNAT.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``NSXEdgeCluster``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``NSXEdgeCluster``.
                This field is required when configuring a cluster that uses NSX-T.
                If None and using NSXe, the system will choose a suitable NSX Edge
                cluster.
            :type  nsx_tier0_gateway: :class:`str` or ``None``
            :param nsx_tier0_gateway: NSX Tier0 Gateway used for this cluster. This attribute was added
                in vSphere API 7.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``NSXTier0Gateway``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``NSXTier0Gateway``.
                This field is required when configuring a cluster that uses NSX-T.
            :type  namespace_subnet_prefix: :class:`long` or ``None``
            :param namespace_subnet_prefix: Size of the subnet reserved for namespaces segments. This attribute
                was added in vSphere API 7.0.2.0.
                If None, defaults to 28.
            :type  routed_mode: :class:`bool` or ``None``
            :param routed_mode: Routed mode for this cluster. When set to True, the traffic in the
                cluster is not NATed. When this field is set to True,
                :attr:`Clusters.NCPClusterNetworkEnableSpec.egress_cidrs` is not
                allowed. This attribute was added in vSphere API 7.0.2.0.
                If None, defaults to False.
            """
            self.pod_cidrs = pod_cidrs
            self.ingress_cidrs = ingress_cidrs
            self.egress_cidrs = egress_cidrs
            self.cluster_distributed_switch = cluster_distributed_switch
            self.nsx_edge_cluster = nsx_edge_cluster
            self.nsx_tier0_gateway = nsx_tier0_gateway
            self.namespace_subnet_prefix = namespace_subnet_prefix
            self.routed_mode = routed_mode
            VapiStruct.__init__(self)


    NCPClusterNetworkEnableSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.NCP_cluster_network_enable_spec', {
            'pod_cidrs': type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr')),
            'ingress_cidrs': type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr')),
            'egress_cidrs': type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr')),
            'cluster_distributed_switch': type.OptionalType(type.IdType()),
            'nsx_edge_cluster': type.OptionalType(type.IdType()),
            'nsx_tier0_gateway': type.OptionalType(type.IdType()),
            'namespace_subnet_prefix': type.OptionalType(type.IntegerType()),
            'routed_mode': type.OptionalType(type.BooleanType()),
        },
        NCPClusterNetworkEnableSpec,
        False,
        None))


    class NCPClusterNetworkUpdateSpec(VapiStruct):
        """
        The ``Clusters.NCPClusterNetworkUpdateSpec`` class encapsulates the NSX
        Container Plugin-specific cluster networking configuration parameters for
        the vSphere Namespaces Cluster Update operation.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     pod_cidrs=None,
                     ingress_cidrs=None,
                     egress_cidrs=None,
                     default_ingress_tls_certificate=None,
                    ):
            """
            :type  pod_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param pod_cidrs: CIDR blocks from which Kubernetes allocates pod IP addresses. This
                range should not overlap with those in
                :attr:`Clusters.EnableSpec.service_cidr`,
                :attr:`Clusters.NCPClusterNetworkUpdateSpec.ingress_cidrs`,
                :attr:`Clusters.NCPClusterNetworkUpdateSpec.egress_cidrs`, or other
                services running in the datacenter. An update operation only allows
                for addition of new CIDR blocks to the existing list. All Pod CIDR
                blocks must be of at least subnet size /23.
                If None, CIDRs from which Kubernetes allocates pod IP addresses
                will not be modified.
            :type  ingress_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param ingress_cidrs: CIDR blocks from which NSX assigns IP addresses for Kubernetes
                Ingresses and Kubernetes Services of type LoadBalancer. These
                ranges should not overlap with those in
                :attr:`Clusters.NCPClusterNetworkUpdateSpec.pod_cidrs`,
                :attr:`Clusters.EnableSpec.service_cidr`,
                :attr:`Clusters.NCPClusterNetworkUpdateSpec.egress_cidrs`, or other
                services running in the datacenter. An update operation only allows
                for addition of new CIDR blocks to the existing list.
                If None, CIDRs from which Kubernetes allocates ingress IP addresses
                will not be modified.
            :type  egress_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param egress_cidrs: CIDR blocks from which NSX assigns IP addresses used for performing
                SNAT from container IPs to external IPs. These ranges should not
                overlap with those in
                :attr:`Clusters.NCPClusterNetworkUpdateSpec.pod_cidrs`,
                :attr:`Clusters.EnableSpec.service_cidr`,
                :attr:`Clusters.NCPClusterNetworkUpdateSpec.ingress_cidrs`, or
                other services running in the datacenter. An update operation only
                allows for addition of new CIDR blocks to the existing list.
                If None, CIDR from which Kubernetes allocates egress IP addresses
                will not be modified.
            :type  default_ingress_tls_certificate: :class:`str` or ``None``
            :param default_ingress_tls_certificate: PEM-encoded x509 certificate used by NSX as a default fallback
                certificate for Kubernetes Ingress services.
                If None, the Kubernetes Ingress services certificate will not be
                modified.
            """
            self.pod_cidrs = pod_cidrs
            self.ingress_cidrs = ingress_cidrs
            self.egress_cidrs = egress_cidrs
            self.default_ingress_tls_certificate = default_ingress_tls_certificate
            VapiStruct.__init__(self)


    NCPClusterNetworkUpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.NCP_cluster_network_update_spec', {
            'pod_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'ingress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'egress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'default_ingress_tls_certificate': type.OptionalType(type.StringType()),
        },
        NCPClusterNetworkUpdateSpec,
        False,
        None))


    class NCPClusterNetworkSetSpec(VapiStruct):
        """
        The ``Clusters.NCPClusterNetworkSetSpec`` class encapsulates the NSX
        Container Plugin-specific cluster networking configuration parameters for
        the vSphere Namespaces Cluster Set operation.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     pod_cidrs=None,
                     ingress_cidrs=None,
                     egress_cidrs=None,
                     default_ingress_tls_certificate=None,
                    ):
            """
            :type  pod_cidrs: :class:`list` of :class:`Ipv4Cidr`
            :param pod_cidrs: CIDR blocks from which Kubernetes allocates pod IP addresses. This
                range should not overlap with those in
                :attr:`Clusters.EnableSpec.service_cidr`,
                :attr:`Clusters.NCPClusterNetworkSetSpec.ingress_cidrs`,
                :attr:`Clusters.NCPClusterNetworkSetSpec.egress_cidrs`, or other
                services running in the datacenter. A set operation only allows for
                addition of new CIDR blocks to the existing list. All Pod CIDR
                blocks must be of at least subnet size /23.
            :type  ingress_cidrs: :class:`list` of :class:`Ipv4Cidr`
            :param ingress_cidrs: CIDR blocks from which NSX assigns IP addresses for Kubernetes
                Ingresses and Kubernetes Services of type LoadBalancer. These
                ranges should not overlap with those in
                :attr:`Clusters.NCPClusterNetworkSetSpec.pod_cidrs`,
                :attr:`Clusters.EnableSpec.service_cidr`,
                :attr:`Clusters.NCPClusterNetworkSetSpec.egress_cidrs`, or other
                services running in the datacenter. A set operation only allows for
                addition of new CIDR blocks to the existing list.
            :type  egress_cidrs: :class:`list` of :class:`Ipv4Cidr`
            :param egress_cidrs: CIDR blocks from which NSX assigns IP addresses used for performing
                SNAT from container IPs to external IPs. These ranges should not
                overlap with those in
                :attr:`Clusters.NCPClusterNetworkSetSpec.pod_cidrs`,
                :attr:`Clusters.EnableSpec.service_cidr`,
                :attr:`Clusters.NCPClusterNetworkSetSpec.ingress_cidrs`, or other
                services running in the datacenter. A set operation only allows for
                addition of new CIDR blocks to the existing list.
            :type  default_ingress_tls_certificate: :class:`str`
            :param default_ingress_tls_certificate: PEM-encoded x509 certificate used by NSX as a default fallback
                certificate for Kubernetes Ingress services.
            """
            self.pod_cidrs = pod_cidrs
            self.ingress_cidrs = ingress_cidrs
            self.egress_cidrs = egress_cidrs
            self.default_ingress_tls_certificate = default_ingress_tls_certificate
            VapiStruct.__init__(self)


    NCPClusterNetworkSetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.NCP_cluster_network_set_spec', {
            'pod_cidrs': type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr')),
            'ingress_cidrs': type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr')),
            'egress_cidrs': type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr')),
            'default_ingress_tls_certificate': type.StringType(),
        },
        NCPClusterNetworkSetSpec,
        False,
        None))


    class EnableSpec(VapiStruct):
        """
        The ``Clusters.EnableSpec`` class contains the specification required to
        enable vSphere Namespaces on a cluster.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'network_provider',
                {
                    'NSXT_CONTAINER_PLUGIN' : [('ncp_cluster_network_spec', True)],
                    'VSPHERE_NETWORK' : [('workload_networks_spec', True), ('load_balancer_config_spec', True)],
                }
            ),
        ]


        _canonical_to_pep_names = {
                                'master_DNS': 'master_dns',
                                'worker_DNS': 'worker_dns',
                                'master_DNS_search_domains': 'master_dns_search_domains',
                                'master_NTP_servers': 'master_ntp_servers',
                                'Master_DNS_names': 'master_dns_names',
                                }

        def __init__(self,
                     size_hint=None,
                     service_cidr=None,
                     network_provider=None,
                     ncp_cluster_network_spec=None,
                     workload_networks_spec=None,
                     workload_ntp_servers=None,
                     load_balancer_config_spec=None,
                     master_management_network=None,
                     master_dns=None,
                     worker_dns=None,
                     master_dns_search_domains=None,
                     master_ntp_servers=None,
                     master_storage_policy=None,
                     ephemeral_storage_policy=None,
                     cns_file_config=None,
                     login_banner=None,
                     master_dns_names=None,
                     image_storage=None,
                     default_image_registry=None,
                     default_image_repository=None,
                     default_kubernetes_service_content_library=None,
                     cluster_proxy_config=None,
                     content_libraries=None,
                    ):
            """
            :type  size_hint: :class:`SizingHint`
            :param size_hint: This affects the size and resources allocated to the Kubernetes API
                server. It also affects the suggested default serviceCidr and
                podCidrs.
            :type  service_cidr: :class:`Ipv4Cidr`
            :param service_cidr: CIDR block from which Kubernetes allocates service cluster IP
                addresses. This range should not overlap with those in
                :attr:`Clusters.NCPClusterNetworkEnableSpec.pod_cidrs`,
                :attr:`Clusters.NCPClusterNetworkEnableSpec.ingress_cidrs`,
                :attr:`Clusters.NCPClusterNetworkEnableSpec.egress_cidrs`, or other
                services running in the datacenter.
            :type  network_provider: :class:`Clusters.NetworkProvider`
            :param network_provider: The provider of cluster networking for this vSphere Namespaces
                cluster.
            :type  ncp_cluster_network_spec: :class:`Clusters.NCPClusterNetworkEnableSpec`
            :param ncp_cluster_network_spec: Specification for the NSX Container Plugin cluster network.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN`.
            :type  workload_networks_spec: :class:`Clusters.WorkloadNetworksEnableSpec`
            :param workload_networks_spec: Specification for the workload networks to be associated with the
                cluster. This attribute was added in vSphere API 7.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK`.
            :type  workload_ntp_servers: :class:`list` of :class:`str` or ``None``
            :param workload_ntp_servers: List of NTP server DNS names or IP addresses to use for workloads
                such as Tanzu Kubernetes Grid VMs, specified in order of
                preference. This attribute was added in vSphere API 7.0.1.0.
                If None, NTP server for Kubernetes API servers will be used.
            :type  load_balancer_config_spec: :class:`LoadBalancers.ConfigSpec`
            :param load_balancer_config_spec: The load balancer configuration is derived from the
                user-provisioned load balancer that will be used to operate a load
                balancer that fronts vSphere Namespaces cluster servers, Tanzu
                Kubernetes Grid API servers, and other servers upon request. 
                
                This configuration is required for network providers that do not
                have a default load balancer included.. This attribute was added in
                vSphere API 7.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK`.
            :type  master_management_network: :class:`Clusters.NetworkSpec`
            :param master_management_network: Specification for the management network on Kubernetes API server.
                :attr:`Clusters.NetworkSpec.mode` must be STATICRANGE as we require
                Kubernetes API server to have a stable address.
            :type  master_dns: :class:`list` of :class:`str` or ``None``
            :param master_dns: List of DNS server IP addresses to use on Kubernetes API server,
                specified in order of preference.
                If None, no default DNS servers are set.
            :type  worker_dns: :class:`list` of :class:`str` or ``None``
            :param worker_dns: List of DNS server IP addresses to use on the worker nodes,
                specified in order of preference.
                If None, no default DNS servers are set.
            :type  master_dns_search_domains: :class:`list` of :class:`str` or ``None``
            :param master_dns_search_domains: List of domains (for example "vmware.com") to be searched when
                trying to lookup a host name on Kubernetes API server, specified in
                order of preference.
                If None, no default DNS search domains are set.
            :type  master_ntp_servers: :class:`list` of :class:`str` or ``None``
            :param master_ntp_servers: List of NTP server DNS names or IP addresses to use on Kubernetes
                API server, specified in order of preference.
                If None, VMware Tools based time synchronization is enabled.
            :type  master_storage_policy: :class:`str`
            :param master_storage_policy: Identifier of storage policy associated with Kubernetes API server.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
            :type  ephemeral_storage_policy: :class:`str`
            :param ephemeral_storage_policy: Identifier of storage policy associated with ephemeral disks of all
                the Kubernetes Pods in the cluster.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
            :type  cns_file_config: :class:`CNSFileConfig` or ``None``
            :param cns_file_config: Specification for configuring Cloud Native Storage file volume
                support on Supervisor. This feature provides support for
                provisioning ReadWriteMany persistent volumes on this cluster
                and/or external clusters. This attribute was added in vSphere API
                7.0.3.0.
                If None, file volume support will not be enabled on this
                Supervisor.
            :type  login_banner: :class:`str` or ``None``
            :param login_banner: Disclaimer to be displayed prior to login via the Kubectl plugin.
                If None, just skip it.
            :type  master_dns_names: :class:`list` of :class:`str` or ``None``
            :param master_dns_names: List of DNS names to associate with the Kubernetes API server.
                These DNS names are embedded in the TLS certificate presented by
                the API server.
                If None, no DNS names are embedded in the TLS certificate.
            :type  image_storage: :class:`Clusters.ImageStorageSpec`
            :param image_storage: Specification for storage to be used for container images.
            :type  default_image_registry: :class:`Clusters.ImageRegistry` or ``None``
            :param default_image_registry: Default image registry to use when Kubernetes Pod container
                specification does not specify it as part of the container image
                name.
                If None, defaults to Docker Hub.
            :type  default_image_repository: :class:`str` or ``None``
            :param default_image_repository: Default image repository to use when Kubernetes Pod container
                specification does not specify it as part of the container image
                name.
                If None, defaults to Docker Hub official repository in case of
                Docker Hub image registry, otherwise defaults to empty string.
            :type  default_kubernetes_service_content_library: :class:`str` or ``None``
            :param default_kubernetes_service_content_library: Identifier of the Content Library which holds the VM Images for
                vSphere Kubernetes Service. 
                
                This Content Library should be subscribed to VMware's hosted
                vSphere Kubernetes Service Repository.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.content.Library``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``com.vmware.content.Library``.
                If None, the Content Library will be automatically generated and
                configured to the Supervisor.
            :type  cluster_proxy_config: :class:`ProxyConfiguration` or ``None``
            :param cluster_proxy_config: Proxy configuration that will be applied to the Supervisor. The
                proxy should be reachable from the management network and will be
                used for image pulling and container traffic exiting out of the
                Supervisor. This attribute was added in vSphere API 7.0.3.00100.
                If None the settings will be inherited from the vCenter settings if
                available.
            :type  content_libraries: :class:`list` of :class:`Clusters.ContentLibrarySpec` or ``None``
            :param content_libraries: List of Content Libraries that will be associated with a
                Supervisor. This list should refer to existing Content Libraries in
                the vSphere inventory. These Content Libraries and the Content
                Library items belonging to them will be read-only across all
                vSphere Namespaces. This list does not overlap with the
                :attr:`Clusters.EnableSpec.default_kubernetes_service_content_library`.
                . This attribute was added in vSphere API 8.0.2.0.
                If None,  no additional Content Libraries will be set for the
                Supervisor apart from the default Kubernetes Service Content
                Library. 
            """
            self.size_hint = size_hint
            self.service_cidr = service_cidr
            self.network_provider = network_provider
            self.ncp_cluster_network_spec = ncp_cluster_network_spec
            self.workload_networks_spec = workload_networks_spec
            self.workload_ntp_servers = workload_ntp_servers
            self.load_balancer_config_spec = load_balancer_config_spec
            self.master_management_network = master_management_network
            self.master_dns = master_dns
            self.worker_dns = worker_dns
            self.master_dns_search_domains = master_dns_search_domains
            self.master_ntp_servers = master_ntp_servers
            self.master_storage_policy = master_storage_policy
            self.ephemeral_storage_policy = ephemeral_storage_policy
            self.cns_file_config = cns_file_config
            self.login_banner = login_banner
            self.master_dns_names = master_dns_names
            self.image_storage = image_storage
            self.default_image_registry = default_image_registry
            self.default_image_repository = default_image_repository
            self.default_kubernetes_service_content_library = default_kubernetes_service_content_library
            self.cluster_proxy_config = cluster_proxy_config
            self.content_libraries = content_libraries
            VapiStruct.__init__(self)


    EnableSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.enable_spec', {
            'size_hint': type.ReferenceType(__name__, 'SizingHint'),
            'service_cidr': type.ReferenceType(__name__, 'Ipv4Cidr'),
            'network_provider': type.ReferenceType(__name__, 'Clusters.NetworkProvider'),
            'ncp_cluster_network_spec': type.OptionalType(type.ReferenceType(__name__, 'Clusters.NCPClusterNetworkEnableSpec')),
            'workload_networks_spec': type.OptionalType(type.ReferenceType(__name__, 'Clusters.WorkloadNetworksEnableSpec')),
            'workload_ntp_servers': type.OptionalType(type.ListType(type.StringType())),
            'load_balancer_config_spec': type.OptionalType(type.ReferenceType(__name__, 'LoadBalancers.ConfigSpec')),
            'master_management_network': type.ReferenceType(__name__, 'Clusters.NetworkSpec'),
            'master_DNS': type.OptionalType(type.ListType(type.StringType())),
            'worker_DNS': type.OptionalType(type.ListType(type.StringType())),
            'master_DNS_search_domains': type.OptionalType(type.ListType(type.StringType())),
            'master_NTP_servers': type.OptionalType(type.ListType(type.StringType())),
            'master_storage_policy': type.IdType(resource_types='SpsStorageProfile'),
            'ephemeral_storage_policy': type.IdType(resource_types='SpsStorageProfile'),
            'cns_file_config': type.OptionalType(type.ReferenceType(__name__, 'CNSFileConfig')),
            'login_banner': type.OptionalType(type.StringType()),
            'Master_DNS_names': type.OptionalType(type.ListType(type.StringType())),
            'image_storage': type.ReferenceType(__name__, 'Clusters.ImageStorageSpec'),
            'default_image_registry': type.OptionalType(type.ReferenceType(__name__, 'Clusters.ImageRegistry')),
            'default_image_repository': type.OptionalType(type.StringType()),
            'default_kubernetes_service_content_library': type.OptionalType(type.IdType()),
            'cluster_proxy_config': type.OptionalType(type.ReferenceType(__name__, 'ProxyConfiguration')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Clusters.ContentLibrarySpec'))),
        },
        EnableSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``Clusters.UpdateSpec`` class contains the specification required to
        update the configuration on the Cluster. This class is applied partially,
        and only the specified fields will replace or modify their existing
        counterparts.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'network_provider',
                {
                    'NSXT_CONTAINER_PLUGIN' : [('ncp_cluster_network_spec', False)],
                    'VSPHERE_NETWORK' : [],
                }
            ),
        ]


        _canonical_to_pep_names = {
                                'floating_IP': 'floating_ip',
                                'master_DNS': 'master_dns',
                                'worker_DNS': 'worker_dns',
                                'master_DNS_search_domains': 'master_dns_search_domains',
                                'master_NTP_servers': 'master_ntp_servers',
                                'Master_DNS_names': 'master_dns_names',
                                }

        def __init__(self,
                     size_hint=None,
                     floating_ip=None,
                     network_provider=None,
                     ncp_cluster_network_spec=None,
                     master_dns=None,
                     worker_dns=None,
                     master_dns_search_domains=None,
                     master_ntp_servers=None,
                     master_storage_policy=None,
                     ephemeral_storage_policy=None,
                     cns_file_config=None,
                     login_banner=None,
                     master_dns_names=None,
                     image_storage=None,
                     default_image_registry=None,
                     default_image_repository=None,
                     tls_endpoint_certificate=None,
                     default_kubernetes_service_content_library=None,
                     workload_ntp_servers=None,
                     cluster_proxy_config=None,
                     content_libraries=None,
                    ):
            """
            :type  size_hint: :class:`SizingHint` or ``None``
            :param size_hint: This affects the size and resources allocated to the Kubernetes API
                server.
                If None, size and resources allocated to Kubernetes API server will
                not be modified.
            :type  floating_ip: :class:`str` or ``None``
            :param floating_ip: Optionally, you can edit the floating IP address that is assigned
                to the Supervisor in case the DHCP server fails during the
                Supervisor enablement process. The field is only relevant when the
                DHCP mode of the Supervisor management network is set with
                :attr:`Clusters.EnableSpec.master_management_network`. Set this
                floating IP parameter to remediate a supervisor enablement failure
                in the case where it was detected that the DHCP server does not
                support DHCP client identifiers. This attribute was added in
                vSphere API 7.0.3.0.
                If None, the existing effective management network floating IP will
                not be modified.
            :type  network_provider: :class:`Clusters.NetworkProvider` or ``None``
            :param network_provider: The provider of cluster networking for this vSphere Namespaces
                cluster.
                If None, the existing effective cluster network specification will
                not be modified.
            :type  ncp_cluster_network_spec: :class:`Clusters.NCPClusterNetworkUpdateSpec` or ``None``
            :param ncp_cluster_network_spec: Updated specification for the cluster network configuration.
                If None, the existing effective cluster network specification will
                not be modified.
            :type  master_dns: :class:`list` of :class:`str` or ``None``
            :param master_dns: List of DNS server IP addresses to use on Kubernetes API server,
                specified in order of preference.
                If :class:`set`, DNS servers set on Kubernetes API server will be
                replaced. Otherwise, they will not be modified.
            :type  worker_dns: :class:`list` of :class:`str` or ``None``
            :param worker_dns: List of DNS server IP addresses to use on the worker nodes,
                specified in order of preference.
                If :class:`set`, DNS servers set on worker nodes will be replaced.
                Otherwise, they will not be modified.
            :type  master_dns_search_domains: :class:`list` of :class:`str` or ``None``
            :param master_dns_search_domains: List of domains (for example "vmware.com") to be searched when
                trying to lookup a host name on Kubernetes API server, specified in
                order of preference.
                If :class:`set`, DNS search domains on Kubernetes API server will
                be replaced. Otherwise, they will not be modified.
            :type  master_ntp_servers: :class:`list` of :class:`str` or ``None``
            :param master_ntp_servers: List of NTP server DNS names or IP addresses to use on Kubernetes
                API server, specified in order of preference.
                If :class:`set`, NTP servers on Kubernetes API server will be
                replaced. Otherwise, they will not be modified.
            :type  master_storage_policy: :class:`str` or ``None``
            :param master_storage_policy: Identifier of storage policy associated with Kubernetes API server.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
                If None, storage policy associated with Kubernetes API server will
                not be modified.
            :type  ephemeral_storage_policy: :class:`str` or ``None``
            :param ephemeral_storage_policy: Identifier of storage policy associated with ephemeral disks of all
                the Kubernetes Pods in the cluster.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
                If None, storage policy associated with ephemeral disks of all the
                Kubernetes Pods will not be modified.
            :type  cns_file_config: :class:`CNSFileConfig` or ``None``
            :param cns_file_config: Specification for configuring Cloud Native Storage file volume
                support on Supervisor. This feature provides support for
                provisioning ReadWriteMany persistent volumes on this cluster
                and/or external clusters. This attribute was added in vSphere API
                7.0.3.0.
                If None, configuration for file volumes will remain unchanged.
            :type  login_banner: :class:`str` or ``None``
            :param login_banner: Disclaimer to be displayed prior to login via the Kubectl plugin.
                If None, disclaimer to be displayed prior to login via the Kubectl
                plugin will not be modified.
            :type  master_dns_names: :class:`list` of :class:`str` or ``None``
            :param master_dns_names: List of DNS names to associate with the Kubernetes API server.
                These DNS names are embedded in the CSR for TLS certificate
                presented by the API server. The provided value will replace
                existing DNS names. This attribute was added in vSphere API
                8.0.2.00300.
                If None, existing DNS names will not be modified.
            :type  image_storage: :class:`Clusters.ImageStorageSpec` or ``None``
            :param image_storage: Specification for storage to be used for container images.
                If None, configuration of storage used for container images is not
                modified.
            :type  default_image_registry: :class:`Clusters.ImageRegistry` or ``None``
            :param default_image_registry: Default image registry to use when Kubernetes Pod container
                specification does not specify it as part of the container image
                name.
                If None, default image registry will not be modified.
            :type  default_image_repository: :class:`str` or ``None``
            :param default_image_repository: Default image repository to use when Kubernetes Pod container
                specification does not specify it as part of the container image
                name.
                If None, default image repository will not be modified.
            :type  tls_endpoint_certificate: :class:`str` or ``None``
            :param tls_endpoint_certificate: PEM-encoded x509 certificate(s) issued for Kubernetes API Server. 
                Certificate(s) used must be created by signing the Certificate
                Signing Request obtained from the Namespace Certificate Management
                API.   
                
                Because a Kubernetes CertificateSigningRequest is created on an
                existing Namespaces-enabled cluster, you must use the
                ``Clusters.UpdateSpec`` to specify this
                :attr:`Clusters.UpdateSpec.tls_endpoint_certificate` on an existing
                cluster rather than during initially enabling Namespaces on a
                cluster. 
                
                In case of providing the trust chain, the certificates should be
                simply concatenated into a single string.
                If None, Kubernetes API Server certificate(s) will not be modified.
            :type  default_kubernetes_service_content_library: :class:`str` or ``None``
            :param default_kubernetes_service_content_library: Identifier of the Content Library which holds the VM Images for
                vSphere Kubernetes Service. 
                
                This Content Library should be subscribed to VMware's hosted
                vSphere Kubernetes Service Repository. 
                
                Modifying or clearing the Content Library identifier will not
                affect existing vSphere Kubernetes Service clusters. However,
                upgrades or scale-out of existing clusters may be affected if the
                new Content Library doesn't have the necessary VM Images.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.content.Library``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``com.vmware.content.Library``.
                If None, the Content Library will not be modified.
            :type  workload_ntp_servers: :class:`list` of :class:`str` or ``None``
            :param workload_ntp_servers: List of NTP server DNS names or IP addresses to use for workloads
                such as Tanzu Kubernetes Grid VMs, specified in order of
                preference. This attribute was added in vSphere API 7.0.1.0.
                If None, NTP servers for workloads will be unmodified.
            :type  cluster_proxy_config: :class:`ProxyConfiguration` or ``None``
            :param cluster_proxy_config: 
                
                Proxy configuration that will be applied to the Supervisor. The
                proxy should be reachable from the management network and will be
                used for image pulling and container traffic exiting out of the
                Supervisor. 
                
                Modifying these settings will result in a restart of the container
                runtime. Workloads might fail to pull their images for a short
                period of time. 
                
                There will be no effect on the currently running containers.. This
                attribute was added in vSphere API 7.0.3.00100.
                If None no change will be made to the cluster.
            :type  content_libraries: :class:`list` of :class:`Clusters.ContentLibrarySpec` or ``None``
            :param content_libraries: List of Content Libraries that will be associated with a
                Supervisor. This list should refer to existing Content Libraries in
                the vSphere inventory. These Content Libraries and the Content
                Library items belonging to them will be read-only across all
                vSphere Namespaces. This list does not overlap with the
                :attr:`Clusters.UpdateSpec.default_kubernetes_service_content_library`.
                . This attribute was added in vSphere API 8.0.2.0.
                If None,  no additional Content Libraries will be set for the
                Supervisor apart from the default Kubernetes Service Content
                Library. 
            """
            self.size_hint = size_hint
            self.floating_ip = floating_ip
            self.network_provider = network_provider
            self.ncp_cluster_network_spec = ncp_cluster_network_spec
            self.master_dns = master_dns
            self.worker_dns = worker_dns
            self.master_dns_search_domains = master_dns_search_domains
            self.master_ntp_servers = master_ntp_servers
            self.master_storage_policy = master_storage_policy
            self.ephemeral_storage_policy = ephemeral_storage_policy
            self.cns_file_config = cns_file_config
            self.login_banner = login_banner
            self.master_dns_names = master_dns_names
            self.image_storage = image_storage
            self.default_image_registry = default_image_registry
            self.default_image_repository = default_image_repository
            self.tls_endpoint_certificate = tls_endpoint_certificate
            self.default_kubernetes_service_content_library = default_kubernetes_service_content_library
            self.workload_ntp_servers = workload_ntp_servers
            self.cluster_proxy_config = cluster_proxy_config
            self.content_libraries = content_libraries
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.update_spec', {
            'size_hint': type.OptionalType(type.ReferenceType(__name__, 'SizingHint')),
            'floating_IP': type.OptionalType(type.StringType()),
            'network_provider': type.OptionalType(type.ReferenceType(__name__, 'Clusters.NetworkProvider')),
            'ncp_cluster_network_spec': type.OptionalType(type.ReferenceType(__name__, 'Clusters.NCPClusterNetworkUpdateSpec')),
            'master_DNS': type.OptionalType(type.ListType(type.StringType())),
            'worker_DNS': type.OptionalType(type.ListType(type.StringType())),
            'master_DNS_search_domains': type.OptionalType(type.ListType(type.StringType())),
            'master_NTP_servers': type.OptionalType(type.ListType(type.StringType())),
            'master_storage_policy': type.OptionalType(type.IdType()),
            'ephemeral_storage_policy': type.OptionalType(type.IdType()),
            'cns_file_config': type.OptionalType(type.ReferenceType(__name__, 'CNSFileConfig')),
            'login_banner': type.OptionalType(type.StringType()),
            'Master_DNS_names': type.OptionalType(type.ListType(type.StringType())),
            'image_storage': type.OptionalType(type.ReferenceType(__name__, 'Clusters.ImageStorageSpec')),
            'default_image_registry': type.OptionalType(type.ReferenceType(__name__, 'Clusters.ImageRegistry')),
            'default_image_repository': type.OptionalType(type.StringType()),
            'tls_endpoint_certificate': type.OptionalType(type.StringType()),
            'default_kubernetes_service_content_library': type.OptionalType(type.IdType()),
            'workload_ntp_servers': type.OptionalType(type.ListType(type.StringType())),
            'cluster_proxy_config': type.OptionalType(type.ReferenceType(__name__, 'ProxyConfiguration')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Clusters.ContentLibrarySpec'))),
        },
        UpdateSpec,
        False,
        None))


    class SetSpec(VapiStruct):
        """
        The ``Clusters.SetSpec`` class contains the specification required to set a
        new configuration on the Cluster. This class is applied in entirety,
        replacing the current specification fully.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'network_provider',
                {
                    'NSXT_CONTAINER_PLUGIN' : [('ncp_cluster_network_spec', True)],
                    'VSPHERE_NETWORK' : [],
                }
            ),
        ]


        _canonical_to_pep_names = {
                                'floating_IP': 'floating_ip',
                                'master_DNS': 'master_dns',
                                'worker_DNS': 'worker_dns',
                                'master_DNS_search_domains': 'master_dns_search_domains',
                                'master_NTP_servers': 'master_ntp_servers',
                                'Master_DNS_names': 'master_dns_names',
                                }

        def __init__(self,
                     size_hint=None,
                     floating_ip=None,
                     network_provider=None,
                     ncp_cluster_network_spec=None,
                     master_dns=None,
                     worker_dns=None,
                     master_dns_search_domains=None,
                     master_ntp_servers=None,
                     master_storage_policy=None,
                     ephemeral_storage_policy=None,
                     cns_file_config=None,
                     login_banner=None,
                     master_dns_names=None,
                     image_storage=None,
                     default_image_registry=None,
                     default_image_repository=None,
                     default_kubernetes_service_content_library=None,
                     workload_ntp_servers=None,
                     cluster_proxy_config=None,
                     content_libraries=None,
                    ):
            """
            :type  size_hint: :class:`SizingHint`
            :param size_hint: This affects the size and resources allocated to the Kubernetes API
                server.
            :type  floating_ip: :class:`str` or ``None``
            :param floating_ip: Optionally, you can edit the floating IP address that is assigned
                to the Supervisor in case the DHCP server fails during the
                Supervisor enablement process. The field is only relevant when the
                DHCP mode of the Supervisor management network is set with
                :attr:`Clusters.EnableSpec.master_management_network`. 
                
                Set this floating IP parameter to remediate a supervisor enablement
                failure in the case where it was detected that the DHCP server does
                not support DHCP client identifiers.. This attribute was added in
                vSphere API 7.0.3.0.
                If None, the existing effective management network floating IP will
                not be modified.
            :type  network_provider: :class:`Clusters.NetworkProvider`
            :param network_provider: The provider of cluster networking for this vSphere Namespaces
                cluster.
            :type  ncp_cluster_network_spec: :class:`Clusters.NCPClusterNetworkSetSpec`
            :param ncp_cluster_network_spec: Specification for the NSX Container Plugin cluster network.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN`.
            :type  master_dns: :class:`list` of :class:`str` or ``None``
            :param master_dns: List of DNS server IP addresses to use on Kubernetes API server,
                specified in order of preference.
                If None, DNS servers set on Kubernetes API server will be cleared.
            :type  worker_dns: :class:`list` of :class:`str` or ``None``
            :param worker_dns: List of DNS server IP addresses to use on the worker nodes,
                specified in order of preference.
                If None, DNS servers set on worker nodes will be cleared.
            :type  master_dns_search_domains: :class:`list` of :class:`str` or ``None``
            :param master_dns_search_domains: List of domains (for example "vmware.com") to be searched when
                trying to lookup a host name on Kubernetes API server, specified in
                order of preference.
                If None, DNS search domains set on Kubernetes API server will be
                cleared.
            :type  master_ntp_servers: :class:`list` of :class:`str` or ``None``
            :param master_ntp_servers: List of NTP server DNS names or IP addresses to use on Kubernetes
                API server, specified in order of preference.
                If None, VMware Tools based time synchronization is enabled and any
                set NTP servers are cleared.
            :type  master_storage_policy: :class:`str`
            :param master_storage_policy: Identifier of storage policy associated with Kubernetes API server.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
            :type  ephemeral_storage_policy: :class:`str`
            :param ephemeral_storage_policy: Identifier of storage policy associated with ephemeral disks of all
                the Kubernetes Pods in the cluster.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
            :type  cns_file_config: :class:`CNSFileConfig` or ``None``
            :param cns_file_config: Specification for configuring Cloud Native Storage file volume
                support on Supervisor. This feature provides support for
                provisioning ReadWriteMany persistent volumes on this cluster
                and/or external clusters. This attribute was added in vSphere API
                7.0.3.0.
                If None, file volume support will not be enabled on this
                Supervisor.
            :type  login_banner: :class:`str` or ``None``
            :param login_banner: Disclaimer to be displayed prior to login via the Kubectl plugin.
                If None, disclaimer to be displayed prior to login via the Kubectl
                plugin will be cleared.
            :type  master_dns_names: :class:`list` of :class:`str` or ``None``
            :param master_dns_names: List of DNS names to associate with the Kubernetes API server.
                These DNS names are embedded in the CSR for TLS certificate
                presented by the API server. The provided value will replace
                existing DNS names. This attribute was added in vSphere API
                8.0.2.00300.
                If None, existing DNS names will be cleared.
            :type  image_storage: :class:`Clusters.ImageStorageSpec`
            :param image_storage: Specification for storage to be used for container images.
            :type  default_image_registry: :class:`Clusters.ImageRegistry` or ``None``
            :param default_image_registry: Default image registry to use when Kubernetes Pod container
                specification does not specify it as part of the container image
                name.
                If None, default image registry will be set to Docker Hub.
            :type  default_image_repository: :class:`str` or ``None``
            :param default_image_repository: Default image repository to use when Kubernetes Pod container
                specification does not specify it as part of the container image
                name.
                If None, default image repository will be set to Docker Hub
                official repository in case of Docker Hub image registry, otherwise
                will be set to empty string.
            :type  default_kubernetes_service_content_library: :class:`str` or ``None``
            :param default_kubernetes_service_content_library: 
                
                Identifier of the Content Library which holds the VM Images for
                vSphere Kubernetes Service. 
                
                This Content Library should be subscribed to VMware's hosted
                vSphere Kubernetes Service Repository. 
                
                Modifying or clearing the Content Library identifier will not
                affect existing vSphere Kubernetes Service clusters. However,
                upgrades or scale-out of existing clusters may be affected if the
                new Content Library doesn't have the necessary VM Images.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.content.Library``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``com.vmware.content.Library``.
                If None, the Content Library identifier will be cleared.
            :type  workload_ntp_servers: :class:`list` of :class:`str` or ``None``
            :param workload_ntp_servers: List of NTP server DNS names or IP addresses to use for workloads
                such as Tanzu Kubernetes Grid VMs, specified in order of
                preference. This attribute was added in vSphere API 7.0.1.0.
                If None, NTP for Kubernetes API servers will be used.
            :type  cluster_proxy_config: :class:`ProxyConfiguration` or ``None``
            :param cluster_proxy_config: 
                
                Proxy configuration that will be applied to the Supervisor. The
                proxy should be reachable from the management network and will be
                used for image pulling and container traffic exiting out of the
                Supervisor. 
                
                Modifying these settings will result in a restart of the container
                runtime. Workloads might fail to pull their images for a short
                period of time. 
                
                There will be no effect on the currently running containers.. This
                attribute was added in vSphere API 7.0.3.00100.
                If None the settings will be inherited from the vCenter settings if
                available.
            :type  content_libraries: :class:`list` of :class:`Clusters.ContentLibrarySpec` or ``None``
            :param content_libraries: List of Content Libraries that will be associated a the Supervisor.
                This list should refer to existing Content Libraries in the vSphere
                inventory. These Content Libraries and the Content Library items
                belonging to them will be read-only across all vSphere Namespaces.
                This list does not overlap with the
                :attr:`Clusters.SetSpec.default_kubernetes_service_content_library`.
                . This attribute was added in vSphere API 8.0.2.0.
                If None,  no additional Content Libraries will be set for the
                Supervisor apart from the default Kubernetes Service Content
                Library. 
            """
            self.size_hint = size_hint
            self.floating_ip = floating_ip
            self.network_provider = network_provider
            self.ncp_cluster_network_spec = ncp_cluster_network_spec
            self.master_dns = master_dns
            self.worker_dns = worker_dns
            self.master_dns_search_domains = master_dns_search_domains
            self.master_ntp_servers = master_ntp_servers
            self.master_storage_policy = master_storage_policy
            self.ephemeral_storage_policy = ephemeral_storage_policy
            self.cns_file_config = cns_file_config
            self.login_banner = login_banner
            self.master_dns_names = master_dns_names
            self.image_storage = image_storage
            self.default_image_registry = default_image_registry
            self.default_image_repository = default_image_repository
            self.default_kubernetes_service_content_library = default_kubernetes_service_content_library
            self.workload_ntp_servers = workload_ntp_servers
            self.cluster_proxy_config = cluster_proxy_config
            self.content_libraries = content_libraries
            VapiStruct.__init__(self)


    SetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.clusters.set_spec', {
            'size_hint': type.ReferenceType(__name__, 'SizingHint'),
            'floating_IP': type.OptionalType(type.StringType()),
            'network_provider': type.ReferenceType(__name__, 'Clusters.NetworkProvider'),
            'ncp_cluster_network_spec': type.OptionalType(type.ReferenceType(__name__, 'Clusters.NCPClusterNetworkSetSpec')),
            'master_DNS': type.OptionalType(type.ListType(type.StringType())),
            'worker_DNS': type.OptionalType(type.ListType(type.StringType())),
            'master_DNS_search_domains': type.OptionalType(type.ListType(type.StringType())),
            'master_NTP_servers': type.OptionalType(type.ListType(type.StringType())),
            'master_storage_policy': type.IdType(resource_types='SpsStorageProfile'),
            'ephemeral_storage_policy': type.IdType(resource_types='SpsStorageProfile'),
            'cns_file_config': type.OptionalType(type.ReferenceType(__name__, 'CNSFileConfig')),
            'login_banner': type.OptionalType(type.StringType()),
            'Master_DNS_names': type.OptionalType(type.ListType(type.StringType())),
            'image_storage': type.ReferenceType(__name__, 'Clusters.ImageStorageSpec'),
            'default_image_registry': type.OptionalType(type.ReferenceType(__name__, 'Clusters.ImageRegistry')),
            'default_image_repository': type.OptionalType(type.StringType()),
            'default_kubernetes_service_content_library': type.OptionalType(type.IdType()),
            'workload_ntp_servers': type.OptionalType(type.ListType(type.StringType())),
            'cluster_proxy_config': type.OptionalType(type.ReferenceType(__name__, 'ProxyConfiguration')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Clusters.ContentLibrarySpec'))),
        },
        SetSpec,
        False,
        None))



    def enable(self,
               cluster,
               spec,
               ):
        """
        Enable vSphere Namespaces on the cluster. This operation sets up
        Kubernetes instance for the cluster along with worker nodes.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which vSphere Namespaces will be
            enabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Clusters.EnableSpec`
        :param spec: Specification for setting up the Kubernetes API server and the
            worker nodes.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the cluster already has vSphere Namespaces enabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if resources/objects could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.UnableToAllocateResource` 
            if the specified cluster is not licensed or resource pool
            reservation for control plane VMs fails.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified cluster is not supported for vSphere Namespaces,
            the cluster's hosts do not have the required ESX version, or for
            any other incompatibilities.
        """
        return self._invoke('enable',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })

    def disable(self,
                cluster,
                ):
        """
        Disable vSphere Namespaces on the cluster. This operation tears down
        the Kubernetes instance and the worker nodes associated with vSphere
        Namespaces enabled cluster.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster for which vSphere Namespaces will be
            disabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor cluster is being restored from a backup. When a
            Supervisor cluster is restored, there's a window of time during
            which the restored Supervisor cluster's state is being synchronized
            back to vCenter. During that time, Supervisor cluster's disablement
            is not allowed.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the Supervisor cluster could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        """
        return self._invoke('disable',
                            {
                            'cluster': cluster,
                            })

    def get(self,
            cluster,
            ):
        """
        Returns information about a specific cluster.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which vSphere Namespaces are enabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`Clusters.Info`
        :return: Information about the desired state of the specified cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if cluster could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified cluster does not have vSphere Namespaces enabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })

    def list(self):
        """
        Returns information about all clusters on which vSphere Namespaces are
        enabled on this vCenter.


        :rtype: :class:`list` of :class:`Clusters.Summary`
        :return: List of summary of all clusters with vSphere Namespaces enabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list', None)

    def set(self,
            cluster,
            spec,
            ):
        """
        Set a new configuration on the cluster object. The specified
        configuration is applied in entirety and will replace the current
        configuration fully.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which vSphere Namespaces is enabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Clusters.SetSpec`
        :param spec: New specification for the Supervisor cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if vSphere Namespaces is being disabled on this Supervisor cluster
            or if the Supervisor cluster is being restored from a backup. When
            a Supervisor cluster is restored, there's a window of time during
            which the restored Supervisor cluster's state is being synchronized
            back to vCenter. During that time, Supervisor cluster's
            configuration modifications are not allowed.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the Supervisor cluster could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the Supervisor cluster's hosts are not configured with
            sufficient resources for the new Kubernetes API Server size.
        """
        return self._invoke('set',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })

    def update(self,
               cluster,
               spec,
               ):
        """
        Update configuration on the cluster object. The specified configuration
        is applied partially and None fields in ``spec`` will leave those parts
        of configuration as-is.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which vSphere Namespaces is enabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Clusters.UpdateSpec`
        :param spec: New specification for the Supervisor cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if vSphere Namespaces is being disabled on this Supervisor cluster
            or if the Supervisor cluster is being restored from a backup. When
            a Supervisor cluster is restored, there's a window of time during
            which the restored Supervisor cluster's state is being synchronized
            back to vCenter. During that time, Supervisor cluster's
            configuration modifications are not allowed.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the Supervisor cluster could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the Supervisor cluster's hosts are not configured with
            sufficient resources for the new Kubernetes API Server size.
        """
        return self._invoke('update',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })

    def rotate_password(self,
                        cluster,
                        ):
        """
        Request a new root password for all control plane nodes in the cluster.
        This operation generates a new root password and configures every
        control plane node in the cluster to accept it for authentication.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster for which the password is being
            generated.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if cluster could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the cluster is in the process of password rotation.
        """
        return self._invoke('rotate_password',
                            {
                            'cluster': cluster,
                            })
class HostsConfig(VapiInterface):
    """
    The ``HostsConfig`` class provides methods to retrieve information about
    vSphere Namespaces support and licensing.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.hosts_config'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _HostsConfigStub)
        self._VAPI_OPERATION_IDS = {}

    class Info(VapiStruct):
        """
        The ``HostsConfig.Info`` class contains information about vSphere
        Namespaces support and licensing.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     namespaces_supported=None,
                     namespaces_licensed=None,
                    ):
            """
            :type  namespaces_supported: :class:`bool`
            :param namespaces_supported: True if vSphere Namespace feature is supported in this VC.
            :type  namespaces_licensed: :class:`bool`
            :param namespaces_licensed: True if vSphere Namespace feature is licensed on any hosts in this
                VC.
            """
            self.namespaces_supported = namespaces_supported
            self.namespaces_licensed = namespaces_licensed
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.hosts_config.info', {
            'namespaces_supported': type.BooleanType(),
            'namespaces_licensed': type.BooleanType(),
        },
        Info,
        False,
        None))



    def get(self):
        """
        Returns support and licensing information about hosts under a VC.


        :rtype: :class:`HostsConfig.Info`
        :return: Information about vSphere Namespaces support and licensing.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get', None)
class LoadBalancers(VapiInterface):
    """
    ``LoadBalancers`` represent the user provisioned load balancers. The load
    balancers provided may be used to front the API servers in both, vSphere
    Namespaces Cluster and Tanzu Kubernetes Grid clusters. Note: The lifecycle
    of these load balancers is not managed by vSphere. This class was added in
    vSphere API 7.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.load_balancers'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _LoadBalancersStub)
        self._VAPI_OPERATION_IDS = {}

    class Provider(Enum):
        """
        The ``LoadBalancers.Provider`` enumerates the kinds of load balancers
        supported by vSphere Namespaces. This enumeration was added in vSphere API
        7.0.1.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        HA_PROXY = None
        """
        HAProxy load balancer. This class attribute was added in vSphere API
        7.0.1.0.

        """
        AVI = None
        """
        NSX Advanced Load Balancer. This class attribute was added in vSphere API
        7.0.2.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Provider` instance.
            """
            Enum.__init__(string)

    Provider._set_values({
        'HA_PROXY': Provider('HA_PROXY'),
        'AVI': Provider('AVI'),
    })
    Provider._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.load_balancers.provider',
        Provider))


    class ConfigSpec(VapiStruct):
        """
        The ``LoadBalancers.ConfigSpec`` encapsulates load balancer configuration
        on vSphere Namespaces. This class was added in vSphere API 7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'provider',
                {
                    'HA_PROXY' : [('ha_proxy_config_create_spec', True)],
                    'AVI' : [('avi_config_create_spec', True)],
                }
            ),
        ]



        def __init__(self,
                     id=None,
                     address_ranges=None,
                     provider=None,
                     ha_proxy_config_create_spec=None,
                     avi_config_create_spec=None,
                    ):
            """
            :type  id: :class:`str`
            :param id: An identifier that identifies a load balancer and can be used to
                query or configure load balancer properties via these resources.
                The identifier has DNS_LABEL restrictions as specified in `
                <https://tools.ietf.org/html/rfc1123>`_. This must be an
                alphanumeric (a-z and 0-9) string, with a maximum length of 63
                characters and with the '-' character allowed anywhere except the
                first or last character. This name is unique across all Namespaces
                in this vCenter server. This attribute was added in vSphere API
                7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.LoadBalancerConfig``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.LoadBalancerConfig``.
            :type  address_ranges: :class:`list` of :class:`IPRange`
            :param address_ranges: List of address ranges that will be used to derive frontend IP
                addresses for L4 virtual servers. This field is ignored in case of
                Avi load balancer provider. In case of HA_PROXY load balancer
                provider, at least one range must be provided. This attribute was
                added in vSphere API 7.0.1.0.
            :type  provider: :class:`LoadBalancers.Provider`
            :param provider: The :attr:`LoadBalancers.ConfigSpec.provider` selects a provider
                from the list of available providers to be used with vSphere
                Namespaces. This attribute was added in vSphere API 7.0.1.0.
            :type  ha_proxy_config_create_spec: :class:`LoadBalancers.HAProxyConfigCreateSpec`
            :param ha_proxy_config_create_spec: The ``LoadBalancers.HAProxyConfigCreateSpec`` is a conditional
                configuration made available upon selecting the HA_PROXY load
                balancer provider. It is used to configure the load balancer at run
                time. This attribute was added in vSphere API 7.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``provider`` is :attr:`LoadBalancers.Provider.HA_PROXY`.
            :type  avi_config_create_spec: :class:`LoadBalancers.AviConfigCreateSpec`
            :param avi_config_create_spec: The ``LoadBalancers.AviConfigCreateSpec`` is a conditional
                configuration made available upon selecting the Avi load balancer
                provider. It is used to configure the load balancer at run time.
                This attribute was added in vSphere API 7.0.2.0.
                This attribute is optional and it is only relevant when the value
                of ``provider`` is :attr:`LoadBalancers.Provider.AVI`.
            """
            self.id = id
            self.address_ranges = address_ranges
            self.provider = provider
            self.ha_proxy_config_create_spec = ha_proxy_config_create_spec
            self.avi_config_create_spec = avi_config_create_spec
            VapiStruct.__init__(self)


    ConfigSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.config_spec', {
            'id': type.IdType(resource_types='com.vmware.vcenter.namespace_management.LoadBalancerConfig'),
            'address_ranges': type.ListType(type.ReferenceType(__name__, 'IPRange')),
            'provider': type.ReferenceType(__name__, 'LoadBalancers.Provider'),
            'ha_proxy_config_create_spec': type.OptionalType(type.ReferenceType(__name__, 'LoadBalancers.HAProxyConfigCreateSpec')),
            'avi_config_create_spec': type.OptionalType(type.ReferenceType(__name__, 'LoadBalancers.AviConfigCreateSpec')),
        },
        ConfigSpec,
        False,
        None))


    class SetSpec(VapiStruct):
        """
        The ``LoadBalancers.SetSpec`` encapsulates configuration allowed for
        setting a new configuration for a load balancer. This class was added in
        vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'provider',
                {
                    'HA_PROXY' : [('ha_proxy_config_set_spec', True)],
                    'AVI' : [('avi_config_set_spec', True)],
                }
            ),
        ]



        def __init__(self,
                     address_ranges=None,
                     provider=None,
                     ha_proxy_config_set_spec=None,
                     avi_config_set_spec=None,
                    ):
            """
            :type  address_ranges: :class:`list` of :class:`IPRange`
            :param address_ranges: List of address ranges that will be used to derive frontend IP
                addresses for L4 virtual servers. This field is ignored in case of
                Avi load balancer provider. In case of HA_PROXY load balancer
                provider, at least one range must be provided. A set operation only
                allows for addition of new IP ranges to the existing list of IP
                ranges. This attribute was added in vSphere API 7.0.3.0.
            :type  provider: :class:`LoadBalancers.Provider`
            :param provider: The :attr:`LoadBalancers.SetSpec.provider` selects a provider from
                the list of available providers to be used with vSphere Namespaces.
                This attribute was added in vSphere API 7.0.3.0.
            :type  ha_proxy_config_set_spec: :class:`LoadBalancers.HAProxyConfigSetSpec`
            :param ha_proxy_config_set_spec: The ``LoadBalancers.HAProxyConfigSetSpec`` is a conditional
                configuration made available upon selecting the HA_PROXY load
                balancer provider. It is used to configure the load balancer at run
                time. This attribute was added in vSphere API 7.0.3.0.
                This attribute is optional and it is only relevant when the value
                of ``provider`` is :attr:`LoadBalancers.Provider.HA_PROXY`.
            :type  avi_config_set_spec: :class:`LoadBalancers.AviConfigSetSpec`
            :param avi_config_set_spec: The ``LoadBalancers.AviConfigSetSpec`` is a conditional
                configuration made available upon selecting the Avi load balancer
                provider. It is used to configure the load balancer at run time.
                This attribute was added in vSphere API 7.0.3.0.
                This attribute is optional and it is only relevant when the value
                of ``provider`` is :attr:`LoadBalancers.Provider.AVI`.
            """
            self.address_ranges = address_ranges
            self.provider = provider
            self.ha_proxy_config_set_spec = ha_proxy_config_set_spec
            self.avi_config_set_spec = avi_config_set_spec
            VapiStruct.__init__(self)


    SetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.set_spec', {
            'address_ranges': type.ListType(type.ReferenceType(__name__, 'IPRange')),
            'provider': type.ReferenceType(__name__, 'LoadBalancers.Provider'),
            'ha_proxy_config_set_spec': type.OptionalType(type.ReferenceType(__name__, 'LoadBalancers.HAProxyConfigSetSpec')),
            'avi_config_set_spec': type.OptionalType(type.ReferenceType(__name__, 'LoadBalancers.AviConfigSetSpec')),
        },
        SetSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``LoadBalancers.UpdateSpec`` encapsulates configuration allowed for
        when updating configuration for load balancers. This class was added in
        vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'provider',
                {
                    'HA_PROXY' : [('ha_proxy_config_update_spec', False)],
                    'AVI' : [('avi_config_update_spec', False)],
                }
            ),
        ]



        def __init__(self,
                     address_ranges=None,
                     provider=None,
                     ha_proxy_config_update_spec=None,
                     avi_config_update_spec=None,
                    ):
            """
            :type  address_ranges: :class:`list` of :class:`IPRange` or ``None``
            :param address_ranges: List of address ranges that will be used to derive frontend IP
                addresses for L4 virtual servers. This field is ignored in case of
                Avi load balancer provider. In case of HA_PROXY load balancer
                provider, at least one range must be provided. An update operation
                only allows for addition of new IP ranges to the existing list of
                IP ranges. This attribute was added in vSphere API 7.0.3.0.
                If None, the existing list of address ranges will not be modified.
            :type  provider: :class:`LoadBalancers.Provider` or ``None``
            :param provider: The :attr:`LoadBalancers.UpdateSpec.provider` selects a provider
                from the list of available providers to be used with vSphere
                Namespaces. This attribute was added in vSphere API 7.0.3.0.
                If :class:`set`, corresponding load balancer UpdateSpec will be
                used to update the configuration. Note: This field cannot be
                updated and can only be used a qualifer for the provider specific
                update spec.
            :type  ha_proxy_config_update_spec: :class:`LoadBalancers.HAProxyConfigUpdateSpec` or ``None``
            :param ha_proxy_config_update_spec: The ``LoadBalancers.HAProxyConfigUpdateSpec`` is a conditional
                configuration made available upon selecting the HA_PROXY load
                balancer provider. It is used to configure the load balancer at run
                time. This attribute was added in vSphere API 7.0.3.0.
                If None, the HAProxy load balancer configuration will not be
                modified.
            :type  avi_config_update_spec: :class:`LoadBalancers.AviConfigUpdateSpec` or ``None``
            :param avi_config_update_spec: The ``LoadBalancers.AviConfigUpdateSpec`` is a conditional
                configuration made available upon selecting the Avi load balancer
                provider. It is used to configure the load balancer at run time.
                This attribute was added in vSphere API 7.0.3.0.
                If None, the Avi load balancer configuration will not be modified.
            """
            self.address_ranges = address_ranges
            self.provider = provider
            self.ha_proxy_config_update_spec = ha_proxy_config_update_spec
            self.avi_config_update_spec = avi_config_update_spec
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.update_spec', {
            'address_ranges': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'IPRange'))),
            'provider': type.OptionalType(type.ReferenceType(__name__, 'LoadBalancers.Provider')),
            'ha_proxy_config_update_spec': type.OptionalType(type.ReferenceType(__name__, 'LoadBalancers.HAProxyConfigUpdateSpec')),
            'avi_config_update_spec': type.OptionalType(type.ReferenceType(__name__, 'LoadBalancers.AviConfigUpdateSpec')),
        },
        UpdateSpec,
        False,
        None))


    class Server(VapiStruct):
        """
        A ``LoadBalancers.Server`` represents an endpoint used to configure load
        balancers. This class was added in vSphere API 7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     host=None,
                     port=None,
                    ):
            """
            :type  host: :class:`str`
            :param host: Load balancer hostname or IPv4 address. This attribute was added in
                vSphere API 7.0.1.0.
            :type  port: :class:`long`
            :param port: Load balancer port. This attribute was added in vSphere API
                7.0.1.0.
            """
            self.host = host
            self.port = port
            VapiStruct.__init__(self)


    Server._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.server', {
            'host': type.StringType(),
            'port': type.IntegerType(),
        },
        Server,
        False,
        None))


    class HAProxyConfigCreateSpec(VapiStruct):
        """
        ``LoadBalancers.HAProxyConfigCreateSpec`` captures the configuration data
        required for Supervisor Service Type:LoadBalancer to have an external load
        balancer be created via HAProxy. This class was added in vSphere API
        7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     servers=None,
                     username=None,
                     password=None,
                     certificate_authority_chain=None,
                    ):
            """
            :type  servers: :class:`list` of :class:`LoadBalancers.Server`
            :param servers: Servers is a list of the addresses for the data plane API servers
                used to configure Virtual Servers. This attribute was added in
                vSphere API 7.0.1.0.
            :type  username: :class:`str`
            :param username: An administrator user name for accessing the HAProxy Data Plane API
                server. This attribute was added in vSphere API 7.0.1.0.
            :type  password: :class:`str`
            :param password: The password for the administrator user. This attribute was added
                in vSphere API 7.0.1.0.
            :type  certificate_authority_chain: :class:`str`
            :param certificate_authority_chain: CertificateAuthorityChain contains PEM-encoded CA chain which is
                used to verify x509 certificates received from the server. This
                attribute was added in vSphere API 7.0.1.0.
            """
            self.servers = servers
            self.username = username
            self.password = password
            self.certificate_authority_chain = certificate_authority_chain
            VapiStruct.__init__(self)


    HAProxyConfigCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.HA_proxy_config_create_spec', {
            'servers': type.ListType(type.ReferenceType(__name__, 'LoadBalancers.Server')),
            'username': type.StringType(),
            'password': type.SecretType(),
            'certificate_authority_chain': type.StringType(),
        },
        HAProxyConfigCreateSpec,
        False,
        None))


    class HAProxyConfigSetSpec(VapiStruct):
        """
        ``LoadBalancers.HAProxyConfigSetSpec`` captures the configuration data
        required for Supervisor Service Type:LoadBalancer to have an external load
        balancer be created via HA Proxy. This class was added in vSphere API
        7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     servers=None,
                     username=None,
                     password=None,
                     certificate_authority_chain=None,
                    ):
            """
            :type  servers: :class:`list` of :class:`LoadBalancers.Server`
            :param servers: Servers is a list of the addresses for the data plane API servers
                used to configure HAProxy. Note: This field cannot be updated and
                should match existing list of servers. This attribute was added in
                vSphere API 7.0.3.0.
            :type  username: :class:`str`
            :param username: An administrator user name for accessing the HAProxy Data Plane API
                server. This attribute was added in vSphere API 7.0.3.0.
            :type  password: :class:`str`
            :param password: The password for the administrator user. This attribute was added
                in vSphere API 7.0.3.0.
            :type  certificate_authority_chain: :class:`str`
            :param certificate_authority_chain: CertificateAuthorityChain contains PEM-encoded CA chain which is
                used to verify x509 certificates received from the server. This
                attribute was added in vSphere API 7.0.3.0.
            """
            self.servers = servers
            self.username = username
            self.password = password
            self.certificate_authority_chain = certificate_authority_chain
            VapiStruct.__init__(self)


    HAProxyConfigSetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.HA_proxy_config_set_spec', {
            'servers': type.ListType(type.ReferenceType(__name__, 'LoadBalancers.Server')),
            'username': type.StringType(),
            'password': type.SecretType(),
            'certificate_authority_chain': type.StringType(),
        },
        HAProxyConfigSetSpec,
        False,
        None))


    class HAProxyConfigUpdateSpec(VapiStruct):
        """
        ``LoadBalancers.HAProxyConfigUpdateSpec`` captures the configuration data
        required for Supervisor Service Type:LoadBalancer to have an external load
        balancer be created via HAProxy. This class was added in vSphere API
        7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     username=None,
                     password=None,
                     certificate_authority_chain=None,
                    ):
            """
            :type  username: :class:`str` or ``None``
            :param username: An administrator user name for accessing the HAProxy Data Plane API
                server. This attribute was added in vSphere API 7.0.3.0.
                If None, the existing username will not be modified.
            :type  password: :class:`str` or ``None``
            :param password: The password for the administrator user. This attribute was added
                in vSphere API 7.0.3.0.
                If None, the existing password will not be modified.
            :type  certificate_authority_chain: :class:`str` or ``None``
            :param certificate_authority_chain: CertificateAuthorityChain contains PEM-encoded CA chain which is
                used to verify x509 certificates received from the server. This
                attribute was added in vSphere API 7.0.3.0.
                If None, the existing PEM-encoded CA chain will not be modified.
            """
            self.username = username
            self.password = password
            self.certificate_authority_chain = certificate_authority_chain
            VapiStruct.__init__(self)


    HAProxyConfigUpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.HA_proxy_config_update_spec', {
            'username': type.OptionalType(type.StringType()),
            'password': type.OptionalType(type.SecretType()),
            'certificate_authority_chain': type.OptionalType(type.StringType()),
        },
        HAProxyConfigUpdateSpec,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``LoadBalancers.Summary`` contains contains basic information related
        to the load balancer for provisioning virtual servers in the namespace.
        This class was added in vSphere API 7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     id=None,
                     provider=None,
                    ):
            """
            :type  id: :class:`str`
            :param id: An DNS compliant identifier for a load balancer, which can be used
                to query or configure the load balancer properties. This attribute
                was added in vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.LoadBalancerConfig``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.LoadBalancerConfig``.
            :type  provider: :class:`LoadBalancers.Provider`
            :param provider: Load balancer provider for the namespace. This attribute was added
                in vSphere API 7.0.1.0.
            """
            self.id = id
            self.provider = provider
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.summary', {
            'id': type.IdType(resource_types='com.vmware.vcenter.namespace_management.LoadBalancerConfig'),
            'provider': type.ReferenceType(__name__, 'LoadBalancers.Provider'),
        },
        Summary,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``LoadBalancers.Info`` contains information related to the load
        balancer for provisioning virtual servers in the namespace. This class was
        added in vSphere API 7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'provider',
                {
                    'HA_PROXY' : [('ha_proxy_info', True)],
                    'AVI' : [('avi_info', True)],
                }
            ),
        ]



        def __init__(self,
                     id=None,
                     address_ranges=None,
                     provider=None,
                     ha_proxy_info=None,
                     avi_info=None,
                    ):
            """
            :type  id: :class:`str`
            :param id: An DNS compliant identifier for a load balancer, which can be used
                to query or configure the load balancer properties. This attribute
                was added in vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.LoadBalancerConfig``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.LoadBalancerConfig``.
            :type  address_ranges: :class:`list` of :class:`IPRange`
            :param address_ranges: IP address range from which virtual servers are assigned their IPs.
                This attribute was added in vSphere API 7.0.1.0.
            :type  provider: :class:`LoadBalancers.Provider`
            :param provider: Load balancer provider for the namespace. This attribute was added
                in vSphere API 7.0.1.0.
            :type  ha_proxy_info: :class:`LoadBalancers.HAProxyInfo`
            :param ha_proxy_info: The ``LoadBalancers.HAProxyInfo`` is a conditional configuration
                made available upon selecting the HA_PROXY load balancer provider.
                It is used to configure the load balancer at run time. This
                attribute was added in vSphere API 7.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``provider`` is :attr:`LoadBalancers.Provider.HA_PROXY`.
            :type  avi_info: :class:`LoadBalancers.AviInfo`
            :param avi_info: The ``LoadBalancers.AviInfo`` is a conditional configuration made
                available upon selecting the Avi load balancer provider. It is used
                to configure the load balancer at run time. This attribute was
                added in vSphere API 7.0.2.0.
                This attribute is optional and it is only relevant when the value
                of ``provider`` is :attr:`LoadBalancers.Provider.AVI`.
            """
            self.id = id
            self.address_ranges = address_ranges
            self.provider = provider
            self.ha_proxy_info = ha_proxy_info
            self.avi_info = avi_info
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.info', {
            'id': type.IdType(resource_types='com.vmware.vcenter.namespace_management.LoadBalancerConfig'),
            'address_ranges': type.ListType(type.ReferenceType(__name__, 'IPRange')),
            'provider': type.ReferenceType(__name__, 'LoadBalancers.Provider'),
            'ha_proxy_info': type.OptionalType(type.ReferenceType(__name__, 'LoadBalancers.HAProxyInfo')),
            'avi_info': type.OptionalType(type.ReferenceType(__name__, 'LoadBalancers.AviInfo')),
        },
        Info,
        False,
        None))


    class HAProxyInfo(VapiStruct):
        """
        The ``LoadBalancers.HAProxyInfo`` contains information related to the
        HAProxy load balancer in the namespace. This class was added in vSphere API
        7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     servers=None,
                     username=None,
                     certificate_authority_chain=None,
                    ):
            """
            :type  servers: :class:`list` of :class:`LoadBalancers.Server`
            :param servers: A list of the addresses for the DataPlane API servers used to
                configure HAProxy. This attribute was added in vSphere API 7.0.1.0.
            :type  username: :class:`str`
            :param username: An administrator user name for accessing the HAProxy Data Plane API
                server. This attribute was added in vSphere API 7.0.1.0.
            :type  certificate_authority_chain: :class:`str`
            :param certificate_authority_chain: PEM-encoded CA certificate chain which is used to verify x509
                certificates received from the server. This attribute was added in
                vSphere API 7.0.1.0.
            """
            self.servers = servers
            self.username = username
            self.certificate_authority_chain = certificate_authority_chain
            VapiStruct.__init__(self)


    HAProxyInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.HA_proxy_info', {
            'servers': type.ListType(type.ReferenceType(__name__, 'LoadBalancers.Server')),
            'username': type.StringType(),
            'certificate_authority_chain': type.StringType(),
        },
        HAProxyInfo,
        False,
        None))


    class AviConfigCreateSpec(VapiStruct):
        """
        ``LoadBalancers.AviConfigCreateSpec`` captures the configuration data
        required for integration with the Avi Software Load Balancer. This class
        was added in vSphere API 7.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     server=None,
                     username=None,
                     password=None,
                     certificate_authority_chain=None,
                     cloud_name=None,
                    ):
            """
            :type  server: :class:`LoadBalancers.Server`
            :param server: Server is the address for the Avi Controller, used to configure
                Virtual Servers. This attribute was added in vSphere API 7.0.2.0.
            :type  username: :class:`str`
            :param username: An administrator user name for accessing the Avi Controller. This
                attribute was added in vSphere API 7.0.2.0.
            :type  password: :class:`str`
            :param password: The password for the administrator user. This attribute was added
                in vSphere API 7.0.2.0.
            :type  certificate_authority_chain: :class:`str`
            :param certificate_authority_chain: CertificateAuthorityChain contains PEM-encoded CA chain which is
                used to verify x509 certificates received from the server. This
                attribute was added in vSphere API 7.0.2.0.
            :type  cloud_name: :class:`str` or ``None``
            :param cloud_name: The cloud name for the Avi Controller. This attribute was added in
                vSphere API 8.0.2.00300.
                Only :class:`set` if custom cloud name is configured for this Avi
                Controller. If None, it defaults to "Default-Cloud".
            """
            self.server = server
            self.username = username
            self.password = password
            self.certificate_authority_chain = certificate_authority_chain
            self.cloud_name = cloud_name
            VapiStruct.__init__(self)


    AviConfigCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.avi_config_create_spec', {
            'server': type.ReferenceType(__name__, 'LoadBalancers.Server'),
            'username': type.StringType(),
            'password': type.SecretType(),
            'certificate_authority_chain': type.StringType(),
            'cloud_name': type.OptionalType(type.StringType()),
        },
        AviConfigCreateSpec,
        False,
        None))


    class AviConfigSetSpec(VapiStruct):
        """
        ``LoadBalancers.AviConfigSetSpec`` captures the configuration data required
        for integration with the Avi Software Load Balancer. This class was added
        in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     server=None,
                     username=None,
                     password=None,
                     certificate_authority_chain=None,
                    ):
            """
            :type  server: :class:`LoadBalancers.Server`
            :param server: Server is the address for the Avi Controller, used to configure
                Virtual Servers. Note: This field cannot be updated and should
                match existing value. This attribute was added in vSphere API
                7.0.3.0.
            :type  username: :class:`str`
            :param username: An administrator user name for accessing the Avi Controller. This
                attribute was added in vSphere API 7.0.3.0.
            :type  password: :class:`str`
            :param password: The password for the administrator user. This attribute was added
                in vSphere API 7.0.3.0.
            :type  certificate_authority_chain: :class:`str`
            :param certificate_authority_chain: CertificateAuthorityChain contains PEM-encoded CA chain which is
                used to verify x509 certificates received from the server. This
                attribute was added in vSphere API 7.0.3.0.
            """
            self.server = server
            self.username = username
            self.password = password
            self.certificate_authority_chain = certificate_authority_chain
            VapiStruct.__init__(self)


    AviConfigSetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.avi_config_set_spec', {
            'server': type.ReferenceType(__name__, 'LoadBalancers.Server'),
            'username': type.StringType(),
            'password': type.SecretType(),
            'certificate_authority_chain': type.StringType(),
        },
        AviConfigSetSpec,
        False,
        None))


    class AviConfigUpdateSpec(VapiStruct):
        """
        ``LoadBalancers.AviConfigUpdateSpec`` captures the configuration data
        required for integration with the Avi Software Load Balancer. This class
        was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     username=None,
                     password=None,
                     certificate_authority_chain=None,
                    ):
            """
            :type  username: :class:`str` or ``None``
            :param username: An administrator user name for accessing the Avi Controller. This
                attribute was added in vSphere API 7.0.3.0.
                If None, the existing username will not be modified.
            :type  password: :class:`str` or ``None``
            :param password: The password for the administrator user. This attribute was added
                in vSphere API 7.0.3.0.
                If None, the existing password will not be modified.
            :type  certificate_authority_chain: :class:`str` or ``None``
            :param certificate_authority_chain: CertificateAuthorityChain contains PEM-encoded CA chain which is
                used to verify x509 certificates received from the server. This
                attribute was added in vSphere API 7.0.3.0.
                If None, the existing PEM-encoded CA chain will not be modified.
            """
            self.username = username
            self.password = password
            self.certificate_authority_chain = certificate_authority_chain
            VapiStruct.__init__(self)


    AviConfigUpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.avi_config_update_spec', {
            'username': type.OptionalType(type.StringType()),
            'password': type.OptionalType(type.SecretType()),
            'certificate_authority_chain': type.OptionalType(type.StringType()),
        },
        AviConfigUpdateSpec,
        False,
        None))


    class AviInfo(VapiStruct):
        """
        The ``LoadBalancers.AviInfo`` contains information related to the Avi
        software load balancer in the namespace. This class was added in vSphere
        API 7.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     server=None,
                     username=None,
                     certificate_authority_chain=None,
                     cloud_name=None,
                    ):
            """
            :type  server: :class:`LoadBalancers.Server`
            :param server: Server is the address for the Avi Controller, used to configure
                Virtual Servers. This attribute was added in vSphere API 7.0.2.0.
            :type  username: :class:`str`
            :param username: An administrator user name for accessing the Avi Controller. This
                attribute was added in vSphere API 7.0.2.0.
            :type  certificate_authority_chain: :class:`str`
            :param certificate_authority_chain: PEM-encoded CA certificate chain which is used to verify x509
                certificates received from the server. This attribute was added in
                vSphere API 7.0.2.0.
            :type  cloud_name: :class:`str` or ``None``
            :param cloud_name: The cloud name for the Avi Controller. This attribute was added in
                vSphere API 8.0.2.00300.
                Only :class:`set` if custom cloud name is configured for this Avi
                Controller. If None, it defaults to "Default-Cloud".
            """
            self.server = server
            self.username = username
            self.certificate_authority_chain = certificate_authority_chain
            self.cloud_name = cloud_name
            VapiStruct.__init__(self)


    AviInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.load_balancers.avi_info', {
            'server': type.ReferenceType(__name__, 'LoadBalancers.Server'),
            'username': type.StringType(),
            'certificate_authority_chain': type.StringType(),
            'cloud_name': type.OptionalType(type.StringType()),
        },
        AviInfo,
        False,
        None))



    def get(self,
            cluster,
            id,
            ):
        """
        Returns information :class:`LoadBalancers.Info` about the load balancer
        associated with the given cluster. This method was added in vSphere API
        7.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster the load balancer is associated with.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  id: :class:`str`
        :param id: Identifier of the load balancer
            :attr:`LoadBalancers.ConfigSpec.id`.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.LoadBalancerConfig``.
        :rtype: :class:`LoadBalancers.Info`
        :return: Information about load balancer associated with a cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``cluster`` or ``id`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified cluster does not have vSphere Namespaces enabled.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            'id': id,
                            })

    def list(self,
             cluster,
             ):
        """
        Returns information about all load balancers associated with the given
        cluster. This method was added in vSphere API 7.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster the load balancers are associated with.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`list` of :class:`LoadBalancers.Summary`
        :return: List of summary of all load balancers associated with a clusters.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``cluster`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified cluster does not have vSphere Namespaces enabled.
        """
        return self._invoke('list',
                            {
                            'cluster': cluster,
                            })

    def set(self,
            cluster,
            id,
            spec,
            ):
        """
        Applies the entire load balancer ``spec`` to an existing load balancer
        configuration. This method was added in vSphere API 7.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster the load balancer is associated with.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  id: :class:`str`
        :param id: Identifier of the load balancer.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.LoadBalancerConfig``.
        :type  spec: :class:`LoadBalancers.SetSpec`
        :param spec: Information about the load balancer object to be set.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if if ``spec`` contain any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the associated cluster is being disabled or if the load balancer
            config is already marked for delete.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``cluster`` or ``id`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified cluster does not have vSphere Namespaces enabled.
        """
        return self._invoke('set',
                            {
                            'cluster': cluster,
                            'id': id,
                            'spec': spec,
                            })

    def update(self,
               cluster,
               id,
               spec,
               ):
        """
        Updates the load balancer configuration. The specified configuration is
        applied partially and None fields in ``spec`` will leave those parts of
        configuration as-is. This method was added in vSphere API 7.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster the load balancer is associated with.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  id: :class:`str`
        :param id: Identifier of the load balancer.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.LoadBalancerConfig``.
        :type  spec: :class:`LoadBalancers.UpdateSpec`
        :param spec: Information about the load balancer object to be updated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if if ``spec`` contain any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the associated cluster is being disabled or if the load balancer
            config is already marked for delete.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``cluster`` or ``id`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified cluster does not have vSphere Namespaces enabled.
        """
        return self._invoke('update',
                            {
                            'cluster': cluster,
                            'id': id,
                            'spec': spec,
                            })
class NSXTier0Gateway(VapiInterface):
    """
    The ``NSXTier0Gateway`` provides methods to get information of NSX Tier0
    Gateways. This class was added in vSphere API 7.0.2.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.NSX_tier0_gateway'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _NSXTier0GatewayStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``NSXTier0Gateway.Summary`` class contains information about an NSX-T
        Tier0 Gateway. This class was added in vSphere API 7.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     tier0_gateway=None,
                     display_name=None,
                     path=None,
                    ):
            """
            :type  tier0_gateway: :class:`str`
            :param tier0_gateway: Identifier of the NSX-T Tier0 or Tier0-VRF Gateway. This attribute
                was added in vSphere API 7.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``NSXTier0Gateway``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``NSXTier0Gateway``.
            :type  display_name: :class:`str`
            :param display_name: Display name of the NSX-T Gateway. This attribute was added in
                vSphere API 7.0.2.0.
            :type  path: :class:`str`
            :param path: NSX Policy path of the NSX-T Gateway. This attribute was added in
                vSphere API 7.0.2.0.
            """
            self.tier0_gateway = tier0_gateway
            self.display_name = display_name
            self.path = path
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.NSX_tier0_gateway.summary', {
            'tier0_gateway': type.IdType(resource_types='NSXTier0Gateway'),
            'display_name': type.StringType(),
            'path': type.StringType(),
        },
        Summary,
        False,
        None))



    def list(self,
             distributed_switch,
             ):
        """
        Returns information of NSX-T Tier0 Gateways associated with a
        Distributed Switch. This method was added in vSphere API 7.0.2.0.

        :type  distributed_switch: :class:`str`
        :param distributed_switch: Identifier of a Distributed Switch. Only CVDS type of distributed
            switches is supported. Only Tier0 Gateways that are associated with
            the particular Distributed Switch will be listed.
            The parameter must be an identifier for the resource type:
            ``vSphereDistributedSwitch``.
        :rtype: :class:`list` of :class:`NSXTier0Gateway.Summary`
        :return: List of summaries of Tier0 Gateways associated with the given
            Distributed Switch.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InternalServerError` 
            if the server reports an unknown internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if no existing Tier0 Gateways associated with the given Distributed
            Switch can be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list',
                            {
                            'distributed_switch': distributed_switch,
                            })
class Networks(VapiInterface):
    """
    The ``Networks`` class provides lifecycle methods on vSphere Namespaces
    networks associated with a vSphere cluster. This class was added in vSphere
    API 7.0.1.0.
    """
    RESOURCE_TYPE = "com.vmware.vcenter.namespace_management.Network"
    """
    The resource type for network. This class attribute was added in vSphere API
    7.0.1.0.

    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.networks'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _NetworksStub)
        self._VAPI_OPERATION_IDS = {}

    class IPAssignmentMode(Enum):
        """
        The ``Networks.IPAssignmentMode`` class defines various IP address
        assignment modes. This enumeration was added in vSphere API 7.0.3.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        DHCP = None
        """
        The address is automatically assigned by a DHCP server. This class
        attribute was added in vSphere API 7.0.3.0.

        """
        STATICRANGE = None
        """
        The address is assigned from a static range. This class attribute was added
        in vSphere API 7.0.3.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`IPAssignmentMode` instance.
            """
            Enum.__init__(string)

    IPAssignmentMode._set_values({
        'DHCP': IPAssignmentMode('DHCP'),
        'STATICRANGE': IPAssignmentMode('STATICRANGE'),
    })
    IPAssignmentMode._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.networks.IP_assignment_mode',
        IPAssignmentMode))


    class LoadBalancerSize(Enum):
        """
        The ``Networks.LoadBalancerSize`` enumerates the kinds of load balancer
        sizes supported by NSX. Small load balancer can host 10 to 20 virtual
        servers depending on NSX-T version. Medium load balancer can host 100
        virtual servers. Large load balancer can host 1000 virtual servers. This
        enumeration was added in vSphere API 7.0.2.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        SMALL = None
        """
        Load balancer size of 'small'. This class attribute was added in vSphere
        API 7.0.2.0.

        """
        MEDIUM = None
        """
        Load balancer size of 'medium'. This class attribute was added in vSphere
        API 7.0.2.0.

        """
        LARGE = None
        """
        Load balancer size of 'large'. This class attribute was added in vSphere
        API 7.0.2.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`LoadBalancerSize` instance.
            """
            Enum.__init__(string)

    LoadBalancerSize._set_values({
        'SMALL': LoadBalancerSize('SMALL'),
        'MEDIUM': LoadBalancerSize('MEDIUM'),
        'LARGE': LoadBalancerSize('LARGE'),
    })
    LoadBalancerSize._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.networks.load_balancer_size',
        LoadBalancerSize))


    class VsphereDVPGNetworkCreateSpec(VapiStruct):
        """
        The ``Networks.VsphereDVPGNetworkCreateSpec`` class describes the
        configuration specification of a vSphere DVPG-backed Namespaces Network
        object. This class was added in vSphere API 7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     portgroup=None,
                     ip_assignment_mode=None,
                     address_ranges=None,
                     gateway=None,
                     subnet_mask=None,
                    ):
            """
            :type  portgroup: :class:`str`
            :param portgroup: Identifier of the vSphere Distributed Portgroup backing the vSphere
                network object. This attribute was added in vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type: ``Network``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type: ``Network``.
            :type  ip_assignment_mode: :class:`Networks.IPAssignmentMode` or ``None``
            :param ip_assignment_mode: IP address assignment mode. If set to DHCP, then field
                :attr:`Networks.VsphereDVPGNetworkCreateSpec.address_ranges` must
                be set to an empty list and fields
                :attr:`Networks.VsphereDVPGNetworkCreateSpec.gateway` and
                :attr:`Networks.VsphereDVPGNetworkCreateSpec.subnet_mask` must be
                set to empty strings. This attribute was added in vSphere API
                7.0.3.0.
                If None, defaults to STATICRANGE.
            :type  address_ranges: :class:`list` of :class:`IPRange`
            :param address_ranges: Usable IP pools on this network. This attribute was added in
                vSphere API 7.0.1.0.
            :type  gateway: :class:`str`
            :param gateway: Gateway for the network. This attribute was added in vSphere API
                7.0.1.0.
            :type  subnet_mask: :class:`str`
            :param subnet_mask: Subnet mask of the network. This attribute was added in vSphere API
                7.0.1.0.
            """
            self.portgroup = portgroup
            self.ip_assignment_mode = ip_assignment_mode
            self.address_ranges = address_ranges
            self.gateway = gateway
            self.subnet_mask = subnet_mask
            VapiStruct.__init__(self)


    VsphereDVPGNetworkCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.vsphere_DVPG_network_create_spec', {
            'portgroup': type.IdType(resource_types='Network'),
            'ip_assignment_mode': type.OptionalType(type.ReferenceType(__name__, 'Networks.IPAssignmentMode')),
            'address_ranges': type.ListType(type.ReferenceType(__name__, 'IPRange')),
            'gateway': type.StringType(),
            'subnet_mask': type.StringType(),
        },
        VsphereDVPGNetworkCreateSpec,
        False,
        None))


    class NsxNetworkCreateSpec(VapiStruct):
        """
        The ``Networks.NsxNetworkCreateSpec`` class describes the configuration
        specification of a NSXT-backed Namespaces Network configuration. This class
        was added in vSphere API 7.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     namespace_network_cidrs=None,
                     ingress_cidrs=None,
                     egress_cidrs=None,
                     nsx_tier0_gateway=None,
                     subnet_prefix_length=None,
                     routed_mode=None,
                     load_balancer_size=None,
                    ):
            """
            :type  namespace_network_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param namespace_network_cidrs: CIDR blocks from which Kubernetes allocates IP addresss for all
                workloads that attach to the namespace, including PodVMs, TKGS and
                VM Service VMs. This range should not overlap with those in
                :attr:`Networks.NsxNetworkCreateSpec.ingress_cidrs`,
                :attr:`Networks.NsxNetworkCreateSpec.egress_cidrs`, or other
                services running in the datacenter. This attribute was added in
                vSphere API 7.0.2.0.
                This field is required when
                :attr:`Networks.NsxNetworkCreateSpec.nsx_tier0_gateway` or any of
                :attr:`Networks.NsxNetworkCreateSpec.ingress_cidrs`,
                :attr:`Networks.NsxNetworkCreateSpec.egress_cidrs` are specified.
                An update operation only allows for addition of new CIDR blocks to
                the existing list.
            :type  ingress_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param ingress_cidrs: CIDR blocks from which NSX assigns IP addresses for Kubernetes
                Ingresses and Kubernetes Services of type LoadBalancer. These
                ranges should not overlap with those in
                :attr:`Networks.NsxNetworkCreateSpec.namespace_network_cidrs`,
                :attr:`Networks.NsxNetworkCreateSpec.egress_cidrs`, or other
                services running in the datacenter. This attribute was added in
                vSphere API 7.0.2.0.
                This field is required when
                :attr:`Networks.NsxNetworkCreateSpec.nsx_tier0_gateway` or any of
                :attr:`Networks.NsxNetworkCreateSpec.namespace_network_cidrs`,
                :attr:`Networks.NsxNetworkCreateSpec.egress_cidrs` is specified. An
                update operation only allows for addition of new CIDR blocks to the
                existing list.
            :type  egress_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param egress_cidrs: CIDR blocks from which NSX assigns IP addresses used for performing
                SNAT from container IPs to external IPs. These ranges should not
                overlap with those in
                :attr:`Networks.NsxNetworkCreateSpec.namespace_network_cidrs`,
                :attr:`Networks.NsxNetworkCreateSpec.ingress_cidrs`, or other
                services running in the datacenter. This attribute was added in
                vSphere API 7.0.2.0.
                This field is required when
                :attr:`Networks.NsxNetworkCreateSpec.routed_mode` is set to False
                and :attr:`Networks.NsxNetworkCreateSpec.nsx_tier0_gateway` or any
                of :attr:`Networks.NsxNetworkCreateSpec.namespace_network_cidrs`,
                :attr:`Networks.NsxNetworkCreateSpec.ingress_cidrs` is specified.
                When :attr:`Networks.NsxNetworkCreateSpec.routed_mode` is set to
                True, this field is not allowed. An update operation only allows
                for addition of new CIDR blocks to the existing list.
            :type  nsx_tier0_gateway: :class:`str` or ``None``
            :param nsx_tier0_gateway: NSX Tier0 Gateway used for the namespace. This field does not allow
                update once applied. This attribute was added in vSphere API
                7.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``NSXTier0Gateway``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``NSXTier0Gateway``.
                This field is required when configuring a cluster that uses NSX-T.
            :type  subnet_prefix_length: :class:`long` or ``None``
            :param subnet_prefix_length: Size of the subnet reserved for namespace segments. This attribute
                was added in vSphere API 7.0.2.0.
                If None, defaults to 28. This field does not allow update once
                applied.
            :type  routed_mode: :class:`bool` or ``None``
            :param routed_mode: Routed mode for thw namespace. When set to True, the traffic in the
                namespace is not NATed. This attribute was added in vSphere API
                7.0.2.0.
                If None, defaults to False. When this field is set to True,
                :attr:`Networks.NsxNetworkCreateSpec.egress_cidrs` is not allowed.
                This field does not allow update once applied.
            :type  load_balancer_size: :class:`Networks.LoadBalancerSize` or ``None``
            :param load_balancer_size: The size of the NSX Load Balancer used by the namespace. This field
                does not allow update once applied. This attribute was added in
                vSphere API 7.0.2.0.
                If None, defaults to :attr:`Networks.LoadBalancerSize.SMALL`.
            """
            self.namespace_network_cidrs = namespace_network_cidrs
            self.ingress_cidrs = ingress_cidrs
            self.egress_cidrs = egress_cidrs
            self.nsx_tier0_gateway = nsx_tier0_gateway
            self.subnet_prefix_length = subnet_prefix_length
            self.routed_mode = routed_mode
            self.load_balancer_size = load_balancer_size
            VapiStruct.__init__(self)


    NsxNetworkCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.nsx_network_create_spec', {
            'namespace_network_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'ingress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'egress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'nsx_tier0_gateway': type.OptionalType(type.IdType()),
            'subnet_prefix_length': type.OptionalType(type.IntegerType()),
            'routed_mode': type.OptionalType(type.BooleanType()),
            'load_balancer_size': type.OptionalType(type.ReferenceType(__name__, 'Networks.LoadBalancerSize')),
        },
        NsxNetworkCreateSpec,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``Networks.CreateSpec`` class contains the specification required to
        create a vSphere Namespaces network object. This class was added in vSphere
        API 7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'network_provider',
                {
                    'VSPHERE_NETWORK' : [('vsphere_network', True)],
                    'NSXT_CONTAINER_PLUGIN' : [('nsx_network', True)],
                }
            ),
        ]



        def __init__(self,
                     network=None,
                     network_provider=None,
                     vsphere_network=None,
                     nsx_network=None,
                    ):
            """
            :type  network: :class:`str`
            :param network: Identifier of the network. This has DNS_LABEL restrictions as
                specified in ` <https://tools.ietf.org/html/rfc1123>`_. This must
                be an alphanumeric (a-z and 0-9) string and with maximum length of
                63 characters and with the '-' character allowed anywhere except
                the first or last character. This name must be unique within a
                cluster. This attribute was added in vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``.
            :type  network_provider: :class:`Clusters.NetworkProvider`
            :param network_provider: The network provider that will manage the vSphere Namespaces
                network object. This attribute was added in vSphere API 7.0.1.0.
            :type  vsphere_network: :class:`Networks.VsphereDVPGNetworkCreateSpec`
            :param vsphere_network: The create spec for a DVPG-backed Namespaces network object,
                supported by :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK`
                network provider. This attribute was added in vSphere API 7.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK`.
            :type  nsx_network: :class:`Networks.NsxNetworkCreateSpec`
            :param nsx_network: The create spec for a NSXT-backed Namespaces network configuration,
                supported by :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN`
                network provider. This attribute was added in vSphere API 7.0.2.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN`.
            """
            self.network = network
            self.network_provider = network_provider
            self.vsphere_network = vsphere_network
            self.nsx_network = nsx_network
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.create_spec', {
            'network': type.IdType(resource_types='com.vmware.vcenter.namespace_management.Network'),
            'network_provider': type.ReferenceType(__name__, 'Clusters.NetworkProvider'),
            'vsphere_network': type.OptionalType(type.ReferenceType(__name__, 'Networks.VsphereDVPGNetworkCreateSpec')),
            'nsx_network': type.OptionalType(type.ReferenceType(__name__, 'Networks.NsxNetworkCreateSpec')),
        },
        CreateSpec,
        False,
        None))


    class VsphereDVPGNetworkSetSpec(VapiStruct):
        """
        The ``Networks.VsphereDVPGNetworkSetSpec`` class contains new configuration
        to set on an existing a vSphere DVPG-backed Namespaces Network object. This
        class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     portgroup=None,
                     address_ranges=None,
                     gateway=None,
                     subnet_mask=None,
                    ):
            """
            :type  portgroup: :class:`str`
            :param portgroup: Identifier of the vSphere Distributed Portgroup backing the vSphere
                network object. If the network object is associated with a
                Namespace or is
                :attr:`Clusters.WorkloadNetworksEnableSpec.supervisor_primary_workload_network`,
                modification to existing portgroup will result in the operation
                failing with a ``com.vmware.vapi.std.errors_client.ResourceInUse``
                exception. This attribute was added in vSphere API 7.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type: ``Network``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type: ``Network``.
            :type  address_ranges: :class:`list` of :class:`IPRange`
            :param address_ranges: Usable IP pools on this network. If the network object is
                associated with a Namespace or is
                :attr:`Clusters.WorkloadNetworksEnableSpec.supervisor_primary_workload_network`,
                then replacement of or modification to any existing range in this
                list will result in operation failing with a
                ``com.vmware.vapi.std.errors_client.ResourceInUse`` exception. To
                add new address ranges to the list, existing address ranges have to
                be passed in without modifications. This attribute was added in
                vSphere API 7.0.3.0.
            :type  gateway: :class:`str`
            :param gateway: Gateway for the network. If the network object is associated with a
                Namespace or is
                :attr:`Clusters.WorkloadNetworksEnableSpec.supervisor_primary_workload_network`,
                then modification to existing gateway will result in the operation
                failing with a ``com.vmware.vapi.std.errors_client.ResourceInUse``
                exception. This attribute was added in vSphere API 7.0.3.0.
            :type  subnet_mask: :class:`str`
            :param subnet_mask: Subnet mask of the network. If the network object is associated
                with a Namespace or is
                :attr:`Clusters.WorkloadNetworksEnableSpec.supervisor_primary_workload_network`,
                then modification to existing subnet mask will result in the
                operation failing with a
                ``com.vmware.vapi.std.errors_client.ResourceInUse`` exception. This
                attribute was added in vSphere API 7.0.3.0.
            """
            self.portgroup = portgroup
            self.address_ranges = address_ranges
            self.gateway = gateway
            self.subnet_mask = subnet_mask
            VapiStruct.__init__(self)


    VsphereDVPGNetworkSetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.vsphere_DVPG_network_set_spec', {
            'portgroup': type.IdType(resource_types='Network'),
            'address_ranges': type.ListType(type.ReferenceType(__name__, 'IPRange')),
            'gateway': type.StringType(),
            'subnet_mask': type.StringType(),
        },
        VsphereDVPGNetworkSetSpec,
        False,
        None))


    class NsxNetworkSetSpec(VapiStruct):
        """
        The ``Networks.NsxNetworkSetSpec`` class contains new configuration to set
        on an existing NSXT-backed Namespaces Network configuration. This class was
        added in vSphere API 7.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     namespace_network_cidrs=None,
                     ingress_cidrs=None,
                     egress_cidrs=None,
                    ):
            """
            :type  namespace_network_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param namespace_network_cidrs: CIDR blocks from which Kubernetes allocates IP addresses for all
                workloads that attach to the namespace, including PodVMs, TKGS and
                VM Service VMs. Only appending additional Cidr is allowed.
                Modification to existing Cidr ranges will result in the operation
                failing with a ``com.vmware.vapi.std.errors_client.ResourceInUse``
                exception. Appending invalid Cidr e.g. overlapping or broadcast or
                reserved Cidr will result in the operation failing with a
                ``com.vmware.vapi.std.errors_client.InvalidArgument`` exception.
                This attribute was added in vSphere API 7.0.2.0.
                If None, the current value will be retained.
            :type  ingress_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param ingress_cidrs: CIDR blocks from which NSX assigns IP addresses for Kubernetes
                Ingresses and Kubernetes Services of type LoadBalancer. Only
                appending additional Cidr is allowed. Modification to existing Cidr
                ranges will result in the operation failing with a
                ``com.vmware.vapi.std.errors_client.ResourceInUse`` exception.
                Appending invalid Cidr e.g. overlapping or broadcast or reserved
                Cidr will result in the operation failing with a
                ``com.vmware.vapi.std.errors_client.InvalidArgument`` exception.
                This attribute was added in vSphere API 7.0.2.0.
                If None, the current value will be retained.
            :type  egress_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param egress_cidrs: CIDR blocks from which NSX assigns IP addresses used for performing
                SNAT from container IPs to external IPs. Only appending additional
                Cidr is allowed. Modification to existing Cidr ranges will result
                in the operation failing with a
                ``com.vmware.vapi.std.errors_client.ResourceInUse`` exception.
                Appending invalid Cidr e.g. overlapping or broadcast or reserved
                Cidr will result in the operation failing with a
                ``com.vmware.vapi.std.errors_client.InvalidArgument`` exception.
                This attribute was added in vSphere API 7.0.2.0.
                If None, the current value will be retained.
            """
            self.namespace_network_cidrs = namespace_network_cidrs
            self.ingress_cidrs = ingress_cidrs
            self.egress_cidrs = egress_cidrs
            VapiStruct.__init__(self)


    NsxNetworkSetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.nsx_network_set_spec', {
            'namespace_network_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'ingress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'egress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
        },
        NsxNetworkSetSpec,
        False,
        None))


    class SetSpec(VapiStruct):
        """
        The ``Networks.SetSpec`` class contains the specification required to set a
        new configuration of a vSphere Namespaces network object. This class is
        applied in entirety, replacing the current specification fully. This class
        was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'network_provider',
                {
                    'VSPHERE_NETWORK' : [('vsphere_network', True)],
                    'NSXT_CONTAINER_PLUGIN' : [('nsx_network', True)],
                }
            ),
        ]



        def __init__(self,
                     network_provider=None,
                     vsphere_network=None,
                     nsx_network=None,
                    ):
            """
            :type  network_provider: :class:`Clusters.NetworkProvider`
            :param network_provider: The network provider that will manage the vSphere Namespaces
                network object. This attribute was added in vSphere API 7.0.3.0.
            :type  vsphere_network: :class:`Networks.VsphereDVPGNetworkSetSpec`
            :param vsphere_network: Modified configuration specification for a DVPG-backed Namespaces
                network object, supported by
                :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK` network provider.
                This attribute was added in vSphere API 7.0.3.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK`.
            :type  nsx_network: :class:`Networks.NsxNetworkSetSpec`
            :param nsx_network: Modified configuration specification for a NSXT-backed Namespaces
                network configuration, supported by
                :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN` network
                provider. This attribute was added in vSphere API 7.0.2.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN`.
            """
            self.network_provider = network_provider
            self.vsphere_network = vsphere_network
            self.nsx_network = nsx_network
            VapiStruct.__init__(self)


    SetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.set_spec', {
            'network_provider': type.ReferenceType(__name__, 'Clusters.NetworkProvider'),
            'vsphere_network': type.OptionalType(type.ReferenceType(__name__, 'Networks.VsphereDVPGNetworkSetSpec')),
            'nsx_network': type.OptionalType(type.ReferenceType(__name__, 'Networks.NsxNetworkSetSpec')),
        },
        SetSpec,
        False,
        None))


    class VsphereDVPGNetworkUpdateSpec(VapiStruct):
        """
        The ``Networks.VsphereDVPGNetworkUpdateSpec`` class contains new
        configuration to update on an existing a vSphere DVPG-backed Namespaces
        Network object. This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     portgroup=None,
                     address_ranges=None,
                     gateway=None,
                     subnet_mask=None,
                    ):
            """
            :type  portgroup: :class:`str` or ``None``
            :param portgroup: Identifier of the vSphere Distributed Portgroup backing the vSphere
                network object. If the network object is associated with a
                Namespace or is
                :attr:`Clusters.WorkloadNetworksEnableSpec.supervisor_primary_workload_network`,
                then modification to existing portgroup will result in the
                operation failing with a
                ``com.vmware.vapi.std.errors_client.ResourceInUse`` exception. This
                attribute was added in vSphere API 7.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type: ``Network``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type: ``Network``.
                If None, the current value will be retained.
            :type  address_ranges: :class:`list` of :class:`IPRange` or ``None``
            :param address_ranges: Usable IP pools on this network. If the network object is
                associated with a Namespace or is
                :attr:`Clusters.WorkloadNetworksEnableSpec.supervisor_primary_workload_network`,
                then replacement of or modification to any existing range in this
                list will result in operation failing with a
                ``com.vmware.vapi.std.errors_client.ResourceInUse`` exception. To
                add new address ranges to the list, existing address ranges have to
                be passed in without modifications. This attribute was added in
                vSphere API 7.0.3.0.
                If None, the current value will be retained.
            :type  gateway: :class:`str` or ``None``
            :param gateway: Gateway for the network. If the network object is associated with a
                Namespace or is
                :attr:`Clusters.WorkloadNetworksEnableSpec.supervisor_primary_workload_network`,
                then modification to existing gateway will result in the operation
                failing with a ``com.vmware.vapi.std.errors_client.ResourceInUse``
                exception. This attribute was added in vSphere API 7.0.3.0.
                If None, the current value will be retained.
            :type  subnet_mask: :class:`str` or ``None``
            :param subnet_mask: Subnet mask of the network. If the network object is associated
                with a Namespace or is
                :attr:`Clusters.WorkloadNetworksEnableSpec.supervisor_primary_workload_network`,
                then modification to existing subnet mask will result in the
                operation failing with a
                ``com.vmware.vapi.std.errors_client.ResourceInUse`` exception. This
                attribute was added in vSphere API 7.0.3.0.
                If None, the current value will be retained.
            """
            self.portgroup = portgroup
            self.address_ranges = address_ranges
            self.gateway = gateway
            self.subnet_mask = subnet_mask
            VapiStruct.__init__(self)


    VsphereDVPGNetworkUpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.vsphere_DVPG_network_update_spec', {
            'portgroup': type.OptionalType(type.IdType()),
            'address_ranges': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'IPRange'))),
            'gateway': type.OptionalType(type.StringType()),
            'subnet_mask': type.OptionalType(type.StringType()),
        },
        VsphereDVPGNetworkUpdateSpec,
        False,
        None))


    class NsxNetworkUpdateSpec(VapiStruct):
        """
        The ``Networks.NsxNetworkUpdateSpec`` class contains new configuration to
        update on an existing a NSXT-backed Namespaces Network configuration. This
        class was added in vSphere API 7.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     namespace_network_cidrs=None,
                     ingress_cidrs=None,
                     egress_cidrs=None,
                    ):
            """
            :type  namespace_network_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param namespace_network_cidrs: CIDR blocks from which Kubernetes allocates IP addresses for all
                workloads that attach to the namespace, including PodVMs, TKGS and
                VM Service VMs. Only appending additional Cidr is allowed.
                Modification to existing Cidr ranges will result in the operation
                failing with a ``com.vmware.vapi.std.errors_client.ResourceInUse``
                exception. Appending invalid Cidr e.g. overlapping or broadcast or
                reserved Cidr will result in the operation failing with a
                ``com.vmware.vapi.std.errors_client.InvalidArgument`` exception.
                This attribute was added in vSphere API 7.0.2.0.
                If None, the current value will be retained.
            :type  ingress_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param ingress_cidrs: CIDR blocks from which NSX assigns IP addresses for Kubernetes
                Ingresses and Kubernetes Services of type LoadBalancer. Only
                appending additional Cidr is allowed. Modification to existing Cidr
                ranges will result in the operation failing with a
                ``com.vmware.vapi.std.errors_client.ResourceInUse`` exception.
                Appending invalid Cidr e.g. overlapping or broadcast or reserved
                Cidr will result in the operation failing with a
                ``com.vmware.vapi.std.errors_client.InvalidArgument`` exception.
                This attribute was added in vSphere API 7.0.2.0.
                If None, the current value will be retained.
            :type  egress_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param egress_cidrs: CIDR blocks from which NSX assigns IP addresses used for performing
                SNAT from container IPs to external IPs. Only appending additional
                Cidr is allowed. Modification to existing Cidr ranges will result
                in the operation failing with a
                ``com.vmware.vapi.std.errors_client.ResourceInUse`` exception.
                Appending invalid Cidr e.g. overlapping or broadcast or reserved
                Cidr will result in the operation failing with a
                ``com.vmware.vapi.std.errors_client.InvalidArgument`` exception.
                This attribute was added in vSphere API 7.0.2.0.
                If None, the current value will be retained.
            """
            self.namespace_network_cidrs = namespace_network_cidrs
            self.ingress_cidrs = ingress_cidrs
            self.egress_cidrs = egress_cidrs
            VapiStruct.__init__(self)


    NsxNetworkUpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.nsx_network_update_spec', {
            'namespace_network_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'ingress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'egress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
        },
        NsxNetworkUpdateSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``Networks.UpdateSpec`` class contains the specification required to
        update the configuration of a vSphere Namespaces network object. This class
        is applied partially, and only the specified fields will replace or modify
        their existing counterparts. This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'network_provider',
                {
                    'VSPHERE_NETWORK' : [('vsphere_network', True)],
                    'NSXT_CONTAINER_PLUGIN' : [('nsx_network', True)],
                }
            ),
        ]



        def __init__(self,
                     network_provider=None,
                     vsphere_network=None,
                     nsx_network=None,
                    ):
            """
            :type  network_provider: :class:`Clusters.NetworkProvider`
            :param network_provider: The network provider that will manage the vSphere Namespaces
                network object. This attribute was added in vSphere API 7.0.3.0.
            :type  vsphere_network: :class:`Networks.VsphereDVPGNetworkUpdateSpec`
            :param vsphere_network: Updated configuration specification for a DVPG-backed Namespaces
                network object, supported by
                :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK` network provider.
                This attribute was added in vSphere API 7.0.3.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK`.
            :type  nsx_network: :class:`Networks.NsxNetworkUpdateSpec`
            :param nsx_network: Updated configuration specification for a NSXT-backed Namespaces
                network configuration, supported by
                :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN` network
                provider. This attribute was added in vSphere API 7.0.2.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN`.
            """
            self.network_provider = network_provider
            self.vsphere_network = vsphere_network
            self.nsx_network = nsx_network
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.update_spec', {
            'network_provider': type.ReferenceType(__name__, 'Clusters.NetworkProvider'),
            'vsphere_network': type.OptionalType(type.ReferenceType(__name__, 'Networks.VsphereDVPGNetworkUpdateSpec')),
            'nsx_network': type.OptionalType(type.ReferenceType(__name__, 'Networks.NsxNetworkUpdateSpec')),
        },
        UpdateSpec,
        False,
        None))


    class VsphereDVPGNetworkInfo(VapiStruct):
        """
        The ``Networks.VsphereDVPGNetworkInfo`` class describes the configuration
        specification of a vSphere DVPG-backed Namespaces Network object. This
        class was added in vSphere API 7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     portgroup=None,
                     ip_assignment_mode=None,
                     address_ranges=None,
                     gateway=None,
                     subnet_mask=None,
                    ):
            """
            :type  portgroup: :class:`str`
            :param portgroup: Identifier of the vSphere Distributed Portgroup backing the vSphere
                network object. This attribute was added in vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type: ``Network``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type: ``Network``.
            :type  ip_assignment_mode: :class:`Networks.IPAssignmentMode` or ``None``
            :param ip_assignment_mode: IP address assignment mode. This attribute was added in vSphere API
                7.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  address_ranges: :class:`list` of :class:`IPRange`
            :param address_ranges: Usable IP pools on this network. This attribute was added in
                vSphere API 7.0.1.0.
            :type  gateway: :class:`str`
            :param gateway: Gateway for the network. This attribute was added in vSphere API
                7.0.1.0.
            :type  subnet_mask: :class:`str`
            :param subnet_mask: Subnet mask of the network. This attribute was added in vSphere API
                7.0.1.0.
            """
            self.portgroup = portgroup
            self.ip_assignment_mode = ip_assignment_mode
            self.address_ranges = address_ranges
            self.gateway = gateway
            self.subnet_mask = subnet_mask
            VapiStruct.__init__(self)


    VsphereDVPGNetworkInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.vsphere_DVPG_network_info', {
            'portgroup': type.IdType(resource_types='Network'),
            'ip_assignment_mode': type.OptionalType(type.ReferenceType(__name__, 'Networks.IPAssignmentMode')),
            'address_ranges': type.ListType(type.ReferenceType(__name__, 'IPRange')),
            'gateway': type.StringType(),
            'subnet_mask': type.StringType(),
        },
        VsphereDVPGNetworkInfo,
        False,
        None))


    class NsxNetworkInfo(VapiStruct):
        """
        The ``Networks.NsxNetworkInfo`` class describes the configuration
        specification of a NSXT-backed Namespaces Network configuration. This class
        was added in vSphere API 7.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     namespace_network_cidrs=None,
                     ingress_cidrs=None,
                     egress_cidrs=None,
                     nsx_tier0_gateway=None,
                     subnet_prefix_length=None,
                     routed_mode=None,
                     load_balancer_size=None,
                    ):
            """
            :type  namespace_network_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param namespace_network_cidrs: CIDR blocks from which Kubernetes allocates IP addresses for all
                workloads that attach to the namespace, including PodVMs, TKGS and
                VM Service VMs. This attribute was added in vSphere API 7.0.2.0.
                If None, cluster level settings specified in
                :attr:`Clusters.NCPClusterNetworkInfo.pod_cidrs` will be applied.
            :type  ingress_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param ingress_cidrs: CIDR blocks from which NSX assigns IP addresses for Kubernetes
                Ingresses and Kubernetes Services of type LoadBalancer. This
                attribute was added in vSphere API 7.0.2.0.
                If None, cluster level settings specified in
                :attr:`Clusters.NCPClusterNetworkInfo.ingress_cidrs` will be
                applied.
            :type  egress_cidrs: :class:`list` of :class:`Ipv4Cidr` or ``None``
            :param egress_cidrs: CIDR blocks from which NSX assigns IP addresses used for performing
                SNAT from container IPs to external IPs. This attribute was added
                in vSphere API 7.0.2.0.
                If None, cluster level settings specified in
                :attr:`Clusters.NCPClusterNetworkInfo.egress_cidrs` will be
                applied.
            :type  nsx_tier0_gateway: :class:`str` or ``None``
            :param nsx_tier0_gateway: NSX Tier0 Gateway used for this namespace. This attribute was added
                in vSphere API 7.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``NSXTier0Gateway``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``NSXTier0Gateway``.
                If None, cluster level settings specified in
                :attr:`Clusters.NCPClusterNetworkInfo.nsx_tier0_gateway` will be
                applied.
            :type  subnet_prefix_length: :class:`long` or ``None``
            :param subnet_prefix_length: Size of the subnet reserved for namespace segments. This attribute
                was added in vSphere API 7.0.2.0.
                If None, cluster level settings specified in
                :attr:`Clusters.NCPClusterNetworkInfo.namespace_subnet_prefix` will
                be applied.
            :type  routed_mode: :class:`bool` or ``None``
            :param routed_mode: Routed mode for this namespace. When set to True, the traffic in
                the namespace is not NATed. This attribute was added in vSphere API
                7.0.2.0.
                If None, cluster level settings specified in
                :attr:`Clusters.NCPClusterNetworkInfo.routed_mode` will be applied.
            :type  load_balancer_size: :class:`Networks.LoadBalancerSize` or ``None``
            :param load_balancer_size: The size of the NSX Load Balancer used by the namespace. This
                attribute was added in vSphere API 7.0.2.0.
                If None, then :attr:`Networks.LoadBalancerSize.SMALL` is used.
            """
            self.namespace_network_cidrs = namespace_network_cidrs
            self.ingress_cidrs = ingress_cidrs
            self.egress_cidrs = egress_cidrs
            self.nsx_tier0_gateway = nsx_tier0_gateway
            self.subnet_prefix_length = subnet_prefix_length
            self.routed_mode = routed_mode
            self.load_balancer_size = load_balancer_size
            VapiStruct.__init__(self)


    NsxNetworkInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.nsx_network_info', {
            'namespace_network_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'ingress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'egress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Ipv4Cidr'))),
            'nsx_tier0_gateway': type.OptionalType(type.IdType()),
            'subnet_prefix_length': type.OptionalType(type.IntegerType()),
            'routed_mode': type.OptionalType(type.BooleanType()),
            'load_balancer_size': type.OptionalType(type.ReferenceType(__name__, 'Networks.LoadBalancerSize')),
        },
        NsxNetworkInfo,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Networks.Info`` class contains detailed information about a specific
        vSphere Namespaces network. This class was added in vSphere API 7.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'network_provider',
                {
                    'VSPHERE_NETWORK' : [('vsphere_network', True)],
                    'NSXT_CONTAINER_PLUGIN' : [('nsx_network', True)],
                }
            ),
        ]



        def __init__(self,
                     network=None,
                     network_provider=None,
                     vsphere_network=None,
                     nsx_network=None,
                     namespaces=None,
                    ):
            """
            :type  network: :class:`str`
            :param network: Identifier of the network. This attribute was added in vSphere API
                7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``.
            :type  network_provider: :class:`Clusters.NetworkProvider`
            :param network_provider: The network provider that will manage the vSphere Namespaces
                network object. This attribute was added in vSphere API 7.0.1.0.
            :type  vsphere_network: :class:`Networks.VsphereDVPGNetworkInfo`
            :param vsphere_network: Updated configuration specification for a DVPG-backed Namespaces
                network object, supported by
                :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK` network provider.
                This attribute was added in vSphere API 7.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.VSPHERE_NETWORK`.
            :type  nsx_network: :class:`Networks.NsxNetworkInfo`
            :param nsx_network: Configuration specification for a NSXT-backed Namespaces network
                configuration, supported by
                :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN` network
                provider. This attribute was added in vSphere API 7.0.2.0.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN`.
            :type  namespaces: :class:`list` of :class:`str` or ``None``
            :param namespaces: A list of Supervisor Namespaces associated with this network. This
                attribute was added in vSphere API 7.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``. When methods return a
                value of this class as a return value, the attribute will contain
                identifiers for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.network = network
            self.network_provider = network_provider
            self.vsphere_network = vsphere_network
            self.nsx_network = nsx_network
            self.namespaces = namespaces
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.info', {
            'network': type.IdType(resource_types='com.vmware.vcenter.namespace_management.Network'),
            'network_provider': type.ReferenceType(__name__, 'Clusters.NetworkProvider'),
            'vsphere_network': type.OptionalType(type.ReferenceType(__name__, 'Networks.VsphereDVPGNetworkInfo')),
            'nsx_network': type.OptionalType(type.ReferenceType(__name__, 'Networks.NsxNetworkInfo')),
            'namespaces': type.OptionalType(type.ListType(type.IdType())),
        },
        Info,
        False,
        None))



    def create(self,
               cluster,
               spec,
               ):
        """
        Create a vSphere Namespaces network object associated with the given
        cluster. This method was added in vSphere API 7.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Networks.CreateSpec`
        :param spec: Information about the network object to be created.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if a network by the name as specified in the
            ``Networks.CreateSpec`` already exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the associated cluster is being disabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``cluster`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if ``spec`` contains NsxNetworkCreateSpec which is unsupported via
            create API.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        """
        return self._invoke('create',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })

    def set(self,
            cluster,
            network,
            spec,
            ):
        """
        Set a new configuration for the vSphere Namespaces network object
        associated with the given cluster. This method was added in vSphere API
        7.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  network: :class:`str`
        :param network: Identifier for the vSphere Namespaces network.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.Network``.
        :type  spec: :class:`Networks.SetSpec`
        :param spec: Information about the network object to be set.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the associated cluster is being disabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``cluster`` or the ``network`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            if the network is in use and the ``spec`` contains field values
            that are un-settable in such a case.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        """
        return self._invoke('set',
                            {
                            'cluster': cluster,
                            'network': network,
                            'spec': spec,
                            })

    def update(self,
               cluster,
               network,
               spec,
               ):
        """
        Update the configuration of the vSphere Namespaces network object
        associated with the given cluster. This method was added in vSphere API
        7.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  network: :class:`str`
        :param network: Identifier for the vSphere Namespaces network.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.Network``.
        :type  spec: :class:`Networks.UpdateSpec`
        :param spec: Information about the network object to be updated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the associated cluster is being disabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``cluster`` or the ``network`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            if the network is in use and the ``spec`` contains field values
            that are un-updatable in such a case.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        """
        return self._invoke('update',
                            {
                            'cluster': cluster,
                            'network': network,
                            'spec': spec,
                            })

    def get(self,
            cluster,
            network,
            ):
        """
        Return information about a specific vSphere Namespaces network. This
        method was added in vSphere API 7.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  network: :class:`str`
        :param network: Identifier for the vSphere Namespaces network.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.Network``.
        :rtype: :class:`Networks.Info`
        :return: List of information about all vSphere Namespaces networks in the
            cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if cluster or network could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            'network': network,
                            })

    def list(self,
             cluster,
             ):
        """
        Return information about all vSphere Namespaces networks in the
        cluster. This method was added in vSphere API 7.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`list` of :class:`Networks.Info`
        :return: Information about the specified vSphere Namespaces network..
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if cluster or network could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list',
                            {
                            'cluster': cluster,
                            })

    def delete(self,
               cluster,
               network,
               ):
        """
        Delete the vSphere Namespaces object in the cluster. This method was
        added in vSphere API 7.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  network: :class:`str`
        :param network: Identifier for the vSphere Namespaces network.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.Network``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if cluster or network could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            if the network is associated with a Namespace.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        """
        return self._invoke('delete',
                            {
                            'cluster': cluster,
                            'network': network,
                            })
class SupervisorServices(VapiInterface):
    """
    The ``SupervisorServices`` class provides methods to manage a Supervisor
    Service object. Supervisor services can be extensions to the vSphere
    Supervisor and provide services to applications running in vSphere
    Supervisor. They are often provided by 3rd party vendors. This class was
    added in vSphere API 7.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisor_services'
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

    class State(Enum):
        """
        The ``SupervisorServices.State`` class defines the state of a Supervisor
        Service. This enumeration was added in vSphere API 7.0.3.0.

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
        The is the default state of a Supervisor Service upon creation. In this
        state, at least one version of the Supervisor Service is activated. This
        class attribute was added in vSphere API 7.0.3.0.

        """
        DEACTIVATED = None
        """
        The is the deactivated state of a Supervisor Service. In this state, all
        existing versions of the Supervisor Service will be deactivated, and cannot
        be activated. In addition to that, no new versions can be added to the
        Supervisor Service. This class attribute was added in vSphere API 7.0.3.0.

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
        'com.vmware.vcenter.namespace_management.supervisor_services.state',
        State))


    class ValidationStatus(Enum):
        """
        The ``SupervisorServices.ValidationStatus`` class defines the type of
        status for validating content of a Supervisor Service version. This
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
        VALID = None
        """
        Indicates the content is valid for a Supervisor Service version. This class
        attribute was added in vSphere API 7.0.3.0.

        """
        VALID_WITH_WARNINGS = None
        """
        Indicates the content is valid for a Supervisor Service version, but the
        content may contain information that should be reviewed closely and could
        prevent the Supervisor Service version to be created successfully later,
        which is explained in ``warningMessages``. For example, the content may
        specify a Supervisor Service version that already exists on this vCenter.
        This class attribute was added in vSphere API 7.0.3.0.

        """
        INVALID = None
        """
        Indicates the content is invalid for a Supervisor Service version, in which
        case the reasons can be found in ``errorMessages``. This class attribute
        was added in vSphere API 7.0.3.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ValidationStatus` instance.
            """
            Enum.__init__(string)

    ValidationStatus._set_values({
        'VALID': ValidationStatus('VALID'),
        'VALID_WITH_WARNINGS': ValidationStatus('VALID_WITH_WARNINGS'),
        'INVALID': ValidationStatus('INVALID'),
    })
    ValidationStatus._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.supervisor_services.validation_status',
        ValidationStatus))


    class CreateSpec(VapiStruct):
        """
        The ``SupervisorServices.CreateSpec`` class provides a specification
        required to create a Supervisor Service. Exactly one of
        :attr:`SupervisorServices.CreateSpec.custom_spec` or
        :attr:`SupervisorServices.CreateSpec.vsphere_spec` must be :class:`set`.
        This class was added in vSphere API 7.0.3.0.

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
            :type  custom_spec: :class:`SupervisorServices.CustomCreateSpec` or ``None``
            :param custom_spec: The specification required to create a Supervisor Service with a
                version from inline content that is based on a plain Kubernetes
                YAML format. 
                
                . This attribute was added in vSphere API 7.0.3.0.
                If :class:`set`, the service will be created from a version based
                on a plain Kubernetes YAML format.
            :type  vsphere_spec: :class:`SupervisorServices.VsphereCreateSpec` or ``None``
            :param vsphere_spec: The specification required to create a Supervisor Service with a
                version from inline content that is based on the vSphere
                application service format. 
                
                . This attribute was added in vSphere API 7.0.3.0.
                If :class:`set`, the service will be created from a version based
                on the vSphere application service format.
            :type  carvel_spec: :class:`SupervisorServices.CarvelCreateSpec` or ``None``
            :param carvel_spec: The specification required to create a Supervisor Service with a
                version from inline content that is based on the Carvel application
                package format. 
                
                . This attribute was added in vSphere API 8.0.0.1.
                If :class:`set`, the service will be created from a version based
                on the Carvel application package format (Package and
                PackageMetadata resources should be declared).
            """
            self.custom_spec = custom_spec
            self.vsphere_spec = vsphere_spec
            self.carvel_spec = carvel_spec
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.create_spec', {
            'custom_spec': type.OptionalType(type.ReferenceType(__name__, 'SupervisorServices.CustomCreateSpec')),
            'vsphere_spec': type.OptionalType(type.ReferenceType(__name__, 'SupervisorServices.VsphereCreateSpec')),
            'carvel_spec': type.OptionalType(type.ReferenceType(__name__, 'SupervisorServices.CarvelCreateSpec')),
        },
        CreateSpec,
        False,
        None))


    class CustomCreateSpec(VapiStruct):
        """
        The ``SupervisorServices.CustomCreateSpec`` class provides a specification
        required to create a Supervisor Service with a version from a plain
        Kubernetes YAML format. This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor_service=None,
                     display_name=None,
                     description=None,
                     version_spec=None,
                    ):
            """
            :type  supervisor_service: :class:`str`
            :param supervisor_service: The identifier of the Supervisor Service. This has DNS_LABEL
                restrictions as specified in `
                <https://tools.ietf.org/html/rfc1123>`_. This must be an
                alphanumeric (a-z and 0-9) string and with maximum length of 63
                characters and with the '-' character allowed anywhere except the
                first or last character. This identifier must be unique across all
                Namespaces in this vCenter server. Additionally, the ID
                'namespaces' is reserved and must not be used. This attribute was
                added in vSphere API 7.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.SupervisorService``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.SupervisorService``.
            :type  display_name: :class:`str`
            :param display_name: A human readable name of the Supervisor Service. This attribute was
                added in vSphere API 7.0.3.0.
            :type  description: :class:`str` or ``None``
            :param description: A human readable description of the Supervisor Service. This
                attribute was added in vSphere API 7.0.3.0.
                If None, the Supervisor Service description will be empty.
            :type  version_spec: :class:`com.vmware.vcenter.namespace_management.supervisor_services_client.Versions.CustomCreateSpec`
            :param version_spec: Supervisor service version specification that provides the service
                definition for one Supervisor Service version. This attribute was
                added in vSphere API 7.0.3.0.
            """
            self.supervisor_service = supervisor_service
            self.display_name = display_name
            self.description = description
            self.version_spec = version_spec
            VapiStruct.__init__(self)


    CustomCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.custom_create_spec', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'display_name': type.StringType(),
            'description': type.OptionalType(type.StringType()),
            'version_spec': type.ReferenceType('com.vmware.vcenter.namespace_management.supervisor_services_client', 'Versions.CustomCreateSpec'),
        },
        CustomCreateSpec,
        False,
        None))


    class VsphereCreateSpec(VapiStruct):
        """
        The ``SupervisorServices.VsphereCreateSpec`` class provides a specification
        required to create a Supervisor Service with a version from vSphere
        application service format, which shall contain the service identifier,
        display name and description information. This class was added in vSphere
        API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     version_spec=None,
                    ):
            """
            :type  version_spec: :class:`com.vmware.vcenter.namespace_management.supervisor_services_client.Versions.VsphereCreateSpec`
            :param version_spec: Supervisor service version specification that provides the service
                definitions for one Supervisor Service version. This attribute was
                added in vSphere API 7.0.3.0.
            """
            self.version_spec = version_spec
            VapiStruct.__init__(self)


    VsphereCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.vsphere_create_spec', {
            'version_spec': type.ReferenceType('com.vmware.vcenter.namespace_management.supervisor_services_client', 'Versions.VsphereCreateSpec'),
        },
        VsphereCreateSpec,
        False,
        None))


    class CarvelCreateSpec(VapiStruct):
        """
        The ``SupervisorServices.CarvelCreateSpec`` class provides a specification
        required to create a Supervisor Service with a version from Carvel
        application package format (Package and PackageMetadata resources should be
        declared). This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     version_spec=None,
                    ):
            """
            :type  version_spec: :class:`com.vmware.vcenter.namespace_management.supervisor_services_client.Versions.CarvelCreateSpec`
            :param version_spec: Supervisor service version specification that provides the service
                definitions for one Supervisor Service version. This attribute was
                added in vSphere API 8.0.0.1.
            """
            self.version_spec = version_spec
            VapiStruct.__init__(self)


    CarvelCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.carvel_create_spec', {
            'version_spec': type.ReferenceType('com.vmware.vcenter.namespace_management.supervisor_services_client', 'Versions.CarvelCreateSpec'),
        },
        CarvelCreateSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``SupervisorServices.UpdateSpec`` class provides a specification
        required to update a Supervisor Service. This class was added in vSphere
        API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     display_name=None,
                     description=None,
                    ):
            """
            :type  display_name: :class:`str` or ``None``
            :param display_name: A human readable name of the Supervisor Service. This attribute was
                added in vSphere API 7.0.3.0.
                If None, the display name of the service will not be modified.
            :type  description: :class:`str` or ``None``
            :param description: A human readable description of the Supervisor Service. This
                attribute was added in vSphere API 7.0.3.0.
                If None, the description of the service will not be modified.
            """
            self.display_name = display_name
            self.description = description
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.update_spec', {
            'display_name': type.OptionalType(type.StringType()),
            'description': type.OptionalType(type.StringType()),
        },
        UpdateSpec,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``SupervisorServices.Summary`` class contains the basic information
        about a Supervisor Service version. This class was added in vSphere API
        7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor_service=None,
                     display_name=None,
                     state=None,
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
            :type  display_name: :class:`str`
            :param display_name: The human readable name of the Supervisor Service. This attribute
                was added in vSphere API 7.0.3.0.
            :type  state: :class:`SupervisorServices.State`
            :param state: The current ``SupervisorServices.State`` of the Supervisor Service.
                This attribute was added in vSphere API 7.0.3.0.
            """
            self.supervisor_service = supervisor_service
            self.display_name = display_name
            self.state = state
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.summary', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'display_name': type.StringType(),
            'state': type.ReferenceType(__name__, 'SupervisorServices.State'),
        },
        Summary,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``SupervisorServices.Info`` class contains detailed information about a
        Supervisor Service. This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     display_name=None,
                     state=None,
                     description=None,
                     has_default_versions_registered=None,
                     must_be_installed=None,
                    ):
            """
            :type  display_name: :class:`str`
            :param display_name: The human readable name of the Supervisor Service. This attribute
                was added in vSphere API 7.0.3.0.
            :type  state: :class:`SupervisorServices.State`
            :param state: The current ``SupervisorServices.State`` of the Supervisor Service.
                This attribute was added in vSphere API 7.0.3.0.
            :type  description: :class:`str` or ``None``
            :param description: A human readable description of the Supervisor Service. This
                attribute was added in vSphere API 7.0.3.0.
                If None, no description is available for the Supervisor Service.
            :type  has_default_versions_registered: :class:`bool`
            :param has_default_versions_registered: If ``true``, this Supervisor Service has at least one version
                registered by default on vCenter, and those default versions cannot
                be deleted. If ``false``, this service does not have any default
                registered versions. This attribute was added in vSphere API
                8.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  must_be_installed: :class:`bool`
            :param must_be_installed: If ``true``, this Supervisor Service will be installed by default
                on each Supervisor, though the version may differ on different
                Supervisors. Users can upgrade this version later, but cannot
                uninstall the service. If ``false``, this service will not be
                installed by default on Supervisors. This attribute was added in
                vSphere API 8.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.display_name = display_name
            self.state = state
            self.description = description
            self.has_default_versions_registered = has_default_versions_registered
            self.must_be_installed = must_be_installed
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.info', {
            'display_name': type.StringType(),
            'state': type.ReferenceType(__name__, 'SupervisorServices.State'),
            'description': type.OptionalType(type.StringType()),
            'has_default_versions_registered': type.OptionalType(type.BooleanType()),
            'must_be_installed': type.OptionalType(type.BooleanType()),
        },
        Info,
        False,
        None))


    class ContentCheckSpec(VapiStruct):
        """
        The ``SupervisorServices.ContentCheckSpec`` class provides a specification
        required for validation checks on the content of a Supervisor Service
        version. This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     content=None,
                    ):
            """
            :type  content: :class:`str` or ``None``
            :param content: The content of a Supervisor Service version, which shall be base64
                encoded. This attribute was added in vSphere API 7.0.3.0.
                If None, the content shall be provided separately. In the current
                release, this field is required, otherwise ``InvalidArgument`` will
                be thrown.
            """
            self.content = content
            VapiStruct.__init__(self)


    ContentCheckSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.content_check_spec', {
            'content': type.OptionalType(type.StringType()),
        },
        ContentCheckSpec,
        False,
        None))


    class VsphereAppsCheckResult(VapiStruct):
        """
        The ``SupervisorServices.VsphereAppsCheckResult`` class contains the
        information of a Supervisor Service version that is retrieved from the
        content in vSphere application service format as a result of the
        :func:`SupervisorServices.check_content` method. This class was added in
        vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor_service=None,
                     version=None,
                     display_name=None,
                     description=None,
                     eula=None,
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
            :type  description: :class:`str` or ``None``
            :param description: A human readable description of the Supervisor Service version.
                This attribute was added in vSphere API 7.0.3.0.
                If None, no description is available for the Supervisor Service
                version.
            :type  eula: :class:`str` or ``None``
            :param eula: The End User License Agreement (EULA) of the Supervisor Service
                version. This attribute was added in vSphere API 7.0.3.0.
                If None, no EULA is available for the Supervisor Service version.
            """
            self.supervisor_service = supervisor_service
            self.version = version
            self.display_name = display_name
            self.description = description
            self.eula = eula
            VapiStruct.__init__(self)


    VsphereAppsCheckResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.vsphere_apps_check_result', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
            'display_name': type.StringType(),
            'description': type.OptionalType(type.StringType()),
            'eula': type.OptionalType(type.StringType()),
        },
        VsphereAppsCheckResult,
        False,
        None))


    class CarvelAppsCheckResult(VapiStruct):
        """
        The ``SupervisorServices.CarvelAppsCheckResult`` class contains the
        information of a Supervisor Service version that is retrieved from the
        content in Carvel application package format as a result of the
        :func:`SupervisorServices.check_content` method. This class was added in
        vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor_service=None,
                     version=None,
                     display_name=None,
                     description=None,
                    ):
            """
            :type  supervisor_service: :class:`str`
            :param supervisor_service: The identifier of the Supervisor Service. This attribute was added
                in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.SupervisorService``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.SupervisorService``.
            :type  version: :class:`str`
            :param version: The identifier of the Supervisor Service version. This attribute
                was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor_services.Version``.
            :type  display_name: :class:`str`
            :param display_name: A human readable name of the Supervisor Service version. This
                attribute was added in vSphere API 8.0.0.1.
            :type  description: :class:`str` or ``None``
            :param description: A human readable description of the Supervisor Service version.
                This attribute was added in vSphere API 8.0.0.1.
                If None, no description is available for the Supervisor Service
                version.
            """
            self.supervisor_service = supervisor_service
            self.version = version
            self.display_name = display_name
            self.description = description
            VapiStruct.__init__(self)


    CarvelAppsCheckResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.carvel_apps_check_result', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'version': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor_services.Version'),
            'display_name': type.StringType(),
            'description': type.OptionalType(type.StringType()),
        },
        CarvelAppsCheckResult,
        False,
        None))


    class CheckResult(VapiStruct):
        """
        The ``SupervisorServices.CheckResult`` class defines the result of the
        validation checks on the content of a Supervisor Service version. This
        class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'status',
                {
                    'VALID_WITH_WARNINGS' : [('warning_messages', True)],
                    'INVALID' : [('error_messages', True)],
                    'VALID' : [],
                }
            ),
            UnionValidator(
                'content_type',
                {
                    'VSPHERE_APPS_YAML' : [('vsphere_apps_check_result', False)],
                    'CARVEL_APPS_YAML' : [('carvel_apps_check_result', False)],
                    'CUSTOM_YAML' : [],
                }
            ),
        ]



        def __init__(self,
                     status=None,
                     content_type=None,
                     vsphere_apps_check_result=None,
                     carvel_apps_check_result=None,
                     warning_messages=None,
                     error_messages=None,
                    ):
            """
            :type  status: :class:`SupervisorServices.ValidationStatus`
            :param status: Indicates if the provided content is valid. This attribute was
                added in vSphere API 7.0.3.0.
            :type  content_type: :class:`com.vmware.vcenter.namespace_management.supervisor_services_client.Versions.ContentType` or ``None``
            :param content_type: The type of the provided content. When this ``contentType`` is
                :attr:`com.vmware.vcenter.namespace_management.supervisor_services_client.Versions.ContentType.CUSTOM_YAML`,
                the ``status`` is always ``VALID`` because a custom format is not
                validated. This attribute was added in vSphere API 7.0.3.0.
                If None, the content type cannot be determined from the provided
                content.
            :type  vsphere_apps_check_result: :class:`SupervisorServices.VsphereAppsCheckResult` or ``None``
            :param vsphere_apps_check_result: The information about the Supervisor Service version retrieved from
                the provided content as a result of validation checks if the
                content is in the vSphere application format. This attribute was
                added in vSphere API 7.0.3.0.
                If None, the content is not in the vSphere application service
                format, or the ``status`` is ``INVALID``.
            :type  carvel_apps_check_result: :class:`SupervisorServices.CarvelAppsCheckResult` or ``None``
            :param carvel_apps_check_result: The information about the Supervisor Service version retrieved from
                the provided content as a result of validation checks if the
                content is in the Carvel application format. This attribute was
                added in vSphere API 8.0.0.1.
                If None, the content is not in the Carvel application package
                format, or the ``status`` is ``INVALID``.
            :type  warning_messages: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param warning_messages: A list of messages indicating why the content was considered valid
                but contains information that should be reviewed closely. This
                attribute was added in vSphere API 7.0.3.0.
                This attribute is optional and it is only relevant when the value
                of ``status`` is
                :attr:`SupervisorServices.ValidationStatus.VALID_WITH_WARNINGS`.
            :type  error_messages: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param error_messages: A list of messages indicating why the content was considered
                invalid. This attribute was added in vSphere API 7.0.3.0.
                This attribute is optional and it is only relevant when the value
                of ``status`` is
                :attr:`SupervisorServices.ValidationStatus.INVALID`.
            """
            self.status = status
            self.content_type = content_type
            self.vsphere_apps_check_result = vsphere_apps_check_result
            self.carvel_apps_check_result = carvel_apps_check_result
            self.warning_messages = warning_messages
            self.error_messages = error_messages
            VapiStruct.__init__(self)


    CheckResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisor_services.check_result', {
            'status': type.ReferenceType(__name__, 'SupervisorServices.ValidationStatus'),
            'content_type': type.OptionalType(type.ReferenceType('com.vmware.vcenter.namespace_management.supervisor_services_client', 'Versions.ContentType')),
            'vsphere_apps_check_result': type.OptionalType(type.ReferenceType(__name__, 'SupervisorServices.VsphereAppsCheckResult')),
            'carvel_apps_check_result': type.OptionalType(type.ReferenceType(__name__, 'SupervisorServices.CarvelAppsCheckResult')),
            'warning_messages': type.OptionalType(type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'))),
            'error_messages': type.OptionalType(type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'))),
        },
        CheckResult,
        False,
        None))



    def check_content(self,
                      spec,
                      ):
        """
        Perform validation checks on the content of a Supervisor Service
        version defined in the ``spec``. The method returns the validation
        status and relevant Supervisor Service version information that are
        available in the content. A custom format will always return a
        ``VALID`` status. Only vSphere and Carvel packages can return multiple
        validation statuses. This method was added in vSphere API 7.0.3.0.

        :type  spec: :class:`SupervisorServices.ContentCheckSpec`
        :param spec: Specification for the content to be checked.
        :rtype: :class:`SupervisorServices.CheckResult`
        :return: A check result containing validation status and relevant Supervisor
            Service version information from the provided content, if the
            content is valid. In case of invalid content, it will return a list
            of error messages.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the provided ``spec`` is invalid. For example, the provided
            :attr:`SupervisorServices.ContentCheckSpec.content` is empty or not
            base64 encoded.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the System.Read privilege.
        """
        return self._invoke('check_content',
                            {
                            'spec': spec,
                            })

    def create(self,
               spec,
               ):
        """
        Create a Supervisor Service. If version specs are provided in the
        ``spec``, new Supervisor Service versions will be created as part of
        the operation. This method was added in vSphere API 7.0.3.0.

        :type  spec: :class:`SupervisorServices.CreateSpec`
        :param spec: Specification for the Supervisor Service with version definition.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if a Supervisor Service with the same identifier already exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors or if an invalid name is specified.
            For example, when the service is from a trusted provider, but no
            signature is provided or it is invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the SupervisorServices.Manage privilege.
        """
        return self._invoke('create',
                            {
                            'spec': spec,
                            })

    def update(self,
               supervisor_service,
               spec,
               ):
        """
        Update a Supervisor Service. This method was added in vSphere API
        7.0.3.0.

        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier for the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :type  spec: :class:`SupervisorServices.UpdateSpec`
        :param spec: Specification for the Supervisor Service metadata to be updated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors or if an invalid name is specified.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor Service with the ID ``supervisor_service`` could not
            be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the SupervisorServices.Manage privilege.
        """
        return self._invoke('update',
                            {
                            'supervisor_service': supervisor_service,
                            'spec': spec,
                            })

    def deactivate(self,
                   supervisor_service,
                   ):
        """
        Deactivate a Supervisor Service. This method will change the
        ``SupervisorServices.State`` of the supervisor service to
        ``DEACTIVATED`` state, and deactivate all versions of the supervisor
        service. Note that this method should be called before deleting the
        Supervisor Service. This method was added in vSphere API 7.0.3.0.

        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier for the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor Service is already in ``DEACTIVATED`` state.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor Service with the ID ``supervisor_service`` could not
            be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the SupervisorServices.Manage privilege.
        """
        return self._invoke('deactivate',
                            {
                            'supervisor_service': supervisor_service,
                            })

    def activate(self,
                 supervisor_service,
                 ):
        """
        Activate a Supervisor Service. This method will change the
        ``SupervisorServices.State`` of the supervisor service to in
        ``ACTIVATED`` state, and activate all versions of the supervisor
        service. This method was added in vSphere API 7.0.3.0.

        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier for the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor Service is already in ``ACTIVATED`` state.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor Service with the ID ``supervisor_service`` could not
            be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have the SupervisorServices.Manage privilege.
        """
        return self._invoke('activate',
                            {
                            'supervisor_service': supervisor_service,
                            })

    def list(self):
        """
        Return the information about all Supervisor Services on this vCenter.
        This method was added in vSphere API 7.0.3.0.


        :rtype: :class:`list` of :class:`SupervisorServices.Summary`
        :return: The list of summary of all Supervisor Services.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the System.Read privilege.
        """
        return self._invoke('list', None)

    def get(self,
            supervisor_service,
            ):
        """
        Return the information for the specified Supervisor Service. This
        method was added in vSphere API 7.0.3.0.

        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier for the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :rtype: :class:`SupervisorServices.Info`
        :return: Information for the specified Supervisor Service.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor Service with the ID ``supervisor_service`` could not
            be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'supervisor_service': supervisor_service,
                            })

    def delete(self,
               supervisor_service,
               ):
        """
        Delete a Supervisor Service. This method only deletes the Supervisor
        Service from vCenter if the Supervisor Service is in ``DEACTIVATED``
        state, and all versions of the Supervisor Service are removed from
        vCenter. Note that the ``deactivate`` method should be called to
        deactivate the Supervisor Service before the Supervisor Service can be
        deleted. This method was added in vSphere API 7.0.3.0.

        :type  supervisor_service: :class:`str`
        :param supervisor_service: Identifier for the Supervisor Service.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.SupervisorService``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the Supervisor Service cannot be deleted in the current state,
            e.g. a version of the Supervisor Service is not in ``DEACTIVATED``
            state.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if Supervisor Service with the ID ``supervisor_service`` could not
            be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the SupervisorServices.Manage privilege.
        """
        return self._invoke('delete',
                            {
                            'supervisor_service': supervisor_service,
                            })
class Supervisors(VapiInterface):
    """
    The ``Supervisors`` service manages the lifecycle of the Supervisor. This
    interface replaces the :class:`Clusters` service. This class was added in
    vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisors'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SupervisorsStub)
        self._VAPI_OPERATION_IDS = {}

    class EnableSpec(VapiStruct):
        """
        
        
        The ``Supervisors.EnableSpec`` class contains the specification required to
        enable a Supervisor. 
        
        The ability to add multiple workload networks at enablement has been
        deprecated. Please use the :class:`Networks` APIs to add additional
        workload networks after the cluster has been enabled.. This class was added
        in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     name=None,
                     control_plane=None,
                     workloads=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: A :attr:`Supervisors.EnableSpec.name` is a user-friendly identifier
                for this Supervisor. This attribute was added in vSphere API
                8.0.0.1.
            :type  control_plane: :class:`com.vmware.vcenter.namespace_management.supervisors_client.ControlPlane`
            :param control_plane: :attr:`Supervisors.EnableSpec.control_plane` specifies
                configuration for the Supervisor control plane. This attribute was
                added in vSphere API 8.0.0.1.
            :type  workloads: :class:`com.vmware.vcenter.namespace_management.supervisors_client.Workloads`
            :param workloads: :attr:`Supervisors.EnableSpec.workloads` specifies configuration
                for compute, network, and storage for workloads. This attribute was
                added in vSphere API 8.0.0.1.
            """
            self.name = name
            self.control_plane = control_plane
            self.workloads = workloads
            VapiStruct.__init__(self)


    EnableSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.enable_spec', {
            'name': type.StringType(),
            'control_plane': type.ReferenceType('com.vmware.vcenter.namespace_management.supervisors_client', 'ControlPlane'),
            'workloads': type.ReferenceType('com.vmware.vcenter.namespace_management.supervisors_client', 'Workloads'),
        },
        EnableSpec,
        False,
        None))


    class EnableOnComputeClusterSpec(VapiStruct):
        """
        
        
        The ``Supervisors.EnableOnComputeClusterSpec`` class contains the
        specification required to enable a Supervisor on a vSphere cluster. 
        
        The ability to add multiple workload networks at enablement has been
        deprecated. Please use the :class:`Networks` APIs to add additional
        workload networks after the cluster has been enabled.. This class was added
        in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     zone=None,
                     name=None,
                     control_plane=None,
                     workloads=None,
                    ):
            """
            :type  zone: :class:`str` or ``None``
            :param zone: :attr:`Supervisors.EnableOnComputeClusterSpec.zone` describes
                consumption fault domain zone available to the Supervisor and its
                workloads. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``.
                Zone will be created and associated with the cluster. If None, the
                zone name will be generated based on the cluster managed object ID.
                The zone can be managed with the consumption fault domain zone api.
            :type  name: :class:`str`
            :param name: A :attr:`Supervisors.EnableSpec.name` is a user-friendly identifier
                for this Supervisor. This attribute was added in vSphere API
                8.0.0.1.
            :type  control_plane: :class:`com.vmware.vcenter.namespace_management.supervisors_client.ControlPlane`
            :param control_plane: :attr:`Supervisors.EnableSpec.control_plane` specifies
                configuration for the Supervisor control plane. This attribute was
                added in vSphere API 8.0.0.1.
            :type  workloads: :class:`com.vmware.vcenter.namespace_management.supervisors_client.Workloads`
            :param workloads: :attr:`Supervisors.EnableSpec.workloads` specifies configuration
                for compute, network, and storage for workloads. This attribute was
                added in vSphere API 8.0.0.1.
            """
            self.zone = zone
            self.name = name
            self.control_plane = control_plane
            self.workloads = workloads
            VapiStruct.__init__(self)


    EnableOnComputeClusterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.enable_on_compute_cluster_spec', {
            'zone': type.OptionalType(type.IdType()),
            'name': type.StringType(),
            'control_plane': type.ReferenceType('com.vmware.vcenter.namespace_management.supervisors_client', 'ControlPlane'),
            'workloads': type.ReferenceType('com.vmware.vcenter.namespace_management.supervisors_client', 'Workloads'),
        },
        EnableOnComputeClusterSpec,
        False,
        None))


    class EnableOnZonesSpec(VapiStruct):
        """
        
        
        The ``Supervisors.EnableOnZonesSpec`` class contains the specification
        required to enable the Supervisor on a set of vSphere Zones. 
        
        The ability to add multiple workload networks at enablement has been
        deprecated. Please use the :class:`Networks` APIs to add additional
        workload networks after the cluster has been enabled.. This class was added
        in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     zones=None,
                     name=None,
                     control_plane=None,
                     workloads=None,
                    ):
            """
            :type  zones: :class:`list` of :class:`str`
            :param zones: :attr:`Supervisors.EnableOnZonesSpec.zones` describe consumption
                fault domain zones available to the Supervisor and its workloads.
                Only one or three zones are supported. This attribute was added in
                vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``.
            :type  name: :class:`str`
            :param name: A :attr:`Supervisors.EnableSpec.name` is a user-friendly identifier
                for this Supervisor. This attribute was added in vSphere API
                8.0.0.1.
            :type  control_plane: :class:`com.vmware.vcenter.namespace_management.supervisors_client.ControlPlane`
            :param control_plane: :attr:`Supervisors.EnableSpec.control_plane` specifies
                configuration for the Supervisor control plane. This attribute was
                added in vSphere API 8.0.0.1.
            :type  workloads: :class:`com.vmware.vcenter.namespace_management.supervisors_client.Workloads`
            :param workloads: :attr:`Supervisors.EnableSpec.workloads` specifies configuration
                for compute, network, and storage for workloads. This attribute was
                added in vSphere API 8.0.0.1.
            """
            self.zones = zones
            self.name = name
            self.control_plane = control_plane
            self.workloads = workloads
            VapiStruct.__init__(self)


    EnableOnZonesSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.enable_on_zones_spec', {
            'zones': type.ListType(type.IdType()),
            'name': type.StringType(),
            'control_plane': type.ReferenceType('com.vmware.vcenter.namespace_management.supervisors_client', 'ControlPlane'),
            'workloads': type.ReferenceType('com.vmware.vcenter.namespace_management.supervisors_client', 'Workloads'),
        },
        EnableOnZonesSpec,
        False,
        None))



    def enable_on_zones(self,
                        spec,
                        ):
        """
        
        
        Enable a Supervisor on a set of vSphere Zones. The cluster control
        plane and its workloads will be eligible for placement across the
        zones. Enabling on multiple zones enables fault tolerance for
        applications deployed on more than one zone in case of a zone failure. 
        
        To verify if the Supervisor is compatible with the provided Zones use:
        :func:`ClusterCompatibility.list`.. This method was added in vSphere
        API 8.0.0.1.

        :type  spec: :class:`Supervisors.EnableOnZonesSpec`
        :param spec: Specification for configuring the Supervisor and Workloads.
        :rtype: :class:`str`
        :return: ID of the Supervisor object being enabled.
            The return value will be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if one or more zones already host a another Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the provided zones could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.UnableToAllocateResource` 
            if the one or more zones are not licensed.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the zones are not supported for the Supervisor, the zones' hosts
            do not have the required ESX version, or for any other
            incompatibilities.
        """
        return self._invoke('enable_on_zones',
                            {
                            'spec': spec,
                            })

    def enable_on_compute_cluster(self,
                                  cluster,
                                  spec,
                                  ):
        """
        
        
        Enable the Supervisor on a single vSphere cluster. This operation sets
        up the Kubernetes instance for the cluster along with worker nodes. A
        consumption fault domain zone will automatically be created if the
        specified cluster is not already associated with a vSphere Zone. 
        
        To verify if the Supervisor is compatible with this vSphere cluster
        use: :func:`ClusterCompatibility.list`. 
        
        A Supervisor can be running on one or multiple vSphere Zones, and each
        vSphere Zone is associated with one or more vSphere Clusters. If a
        Supervisor running on the specified vSphere Cluster is running on
        additional vSphere Clusters, this operation will apply to Supervisor
        components running on the other vSphere Clusters in addition to the
        specified vSphere Cluster. 
        
        To call this API on a Supervisor with multiple vSphere Clusters, use
        :func:`com.vmware.vcenter.namespace_management.supervisors_client.Topology.get`
        to get the vSphere Clusters associated with the given Supervisor. Any
        cluster from the list returned can be used as the input of this API..
        This method was added in vSphere API 8.0.0.1.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster used to enable the Supervisor Cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Supervisors.EnableOnComputeClusterSpec`
        :param spec: Specification for configuring the Supervisor and Workloads.
        :rtype: :class:`str`
        :return: ID of the Supervisor object being enabled.
            The return value will be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the cluster already has the Supervisor enabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if resources/objects could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.UnableToAllocateResource` 
            if the specified cluster is not licensed.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified cluster is not supported for the Supervisor, the
            cluster's hosts do not have the required ESX version, or for any
            other incompatibilities.
        """
        return self._invoke('enable_on_compute_cluster',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })
class VirtualMachineClasses(VapiInterface):
    """
    The ``VirtualMachineClasses`` class provides management methods for
    customizable virtual machine classes. A virtual machine class represents a
    policy and configuration resource which defines a set of attributes to be
    used in the configuration of a virtual machine instance. This class was
    added in vSphere API 7.0.2.00100.
    """
    RESOURCE_TYPE = "com.vmware.vcenter.namespace_management.VirtualMachineClass"
    """
    The resource type for VM class. This class attribute was added in vSphere API
    7.0.2.00100.

    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.virtual_machine_classes'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _VirtualMachineClassesStub)
        self._VAPI_OPERATION_IDS = {}

    class ConfigStatus(Enum):
        """
        ConfigStatus represents the config status of the VM class. This enumeration
        was added in vSphere API 7.0.2.00100.

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
        Indicates that the instance of the ``VirtualMachineClasses`` is ready to be
        used. This class attribute was added in vSphere API 7.0.2.00100.

        """
        REMOVING = None
        """
        Indicates that the instance of the ``VirtualMachineClasses`` is being
        deleted. At this state the VM class cannot be associated with new
        Namespace. This class attribute was added in vSphere API 7.0.2.00100.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ConfigStatus` instance.
            """
            Enum.__init__(string)

    ConfigStatus._set_values({
        'READY': ConfigStatus('READY'),
        'REMOVING': ConfigStatus('REMOVING'),
    })
    ConfigStatus._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.virtual_machine_classes.config_status',
        ConfigStatus))


    class InstanceStorageVolume(VapiStruct):
        """
        The ``VirtualMachineClasses.InstanceStorageVolume`` class contains the
        specification required to configure instance storage for virtual machines.
        An admin can create VM classes with instance storage volumes and assign
        them to Supervisor namespaces for consumption. These VM classes can be used
        to create virtual machines that have instance storage volumes attached as
        disks. The generated instance volumes are placed on vSan direct datastores.
        This class was added in vSphere API 8.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     size=None,
                    ):
            """
            :type  size: :class:`long`
            :param size: The size of instance storage volume in mebibytes (MiB) available
                for the virtual machine of this class. This attribute was added in
                vSphere API 8.0.0.0.
            """
            self.size = size
            VapiStruct.__init__(self)


    InstanceStorageVolume._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.virtual_machine_classes.instance_storage_volume', {
            'size': type.IntegerType(),
        },
        InstanceStorageVolume,
        False,
        None))


    class InstanceStorage(VapiStruct):
        """
        The ``VirtualMachineClasses.InstanceStorage`` class encapsulates
        information about storage policy and instance storage volumes. This class
        was added in vSphere API 8.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     policy=None,
                     volumes=None,
                    ):
            """
            :type  policy: :class:`str`
            :param policy: Policy corresponding to the instance storage. To use VM class with
                instance storage, this policy should also be associated with
                Supervisor namespace. See
                com.vmware.vcenter.namespaces.Instances.StorageSpec. This attribute
                was added in vSphere API 8.0.0.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
            :type  volumes: :class:`list` of :class:`VirtualMachineClasses.InstanceStorageVolume`
            :param volumes: List of instance storage volumes. At least one volume is required
                when configuring a VM class with instance storage. This attribute
                was added in vSphere API 8.0.0.0.
            """
            self.policy = policy
            self.volumes = volumes
            VapiStruct.__init__(self)


    InstanceStorage._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.virtual_machine_classes.instance_storage', {
            'policy': type.IdType(resource_types='SpsStorageProfile'),
            'volumes': type.ListType(type.ReferenceType(__name__, 'VirtualMachineClasses.InstanceStorageVolume')),
        },
        InstanceStorage,
        False,
        None))


    class VGPUDevice(VapiStruct):
        """
        The ``VirtualMachineClasses.VGPUDevice`` class contains the configuration
        corresponding to a vGPU device. This class was added in vSphere API
        7.0.3.0.

        .. deprecated:: vSphere API 8.0.2.0
            Use device changes in VirtualMachineConfigSpec associated with the VM
            class to add vGPU devices. 

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     profile_name=None,
                    ):
            """
            :type  profile_name: :class:`str`
            :param profile_name: Profile name corresponding to the device. This attribute was added
                in vSphere API 7.0.3.0.
            """
            warn('com.vmware.vcenter.namespace_management.VirtualMachineClasses.VGPUDevice is deprecated as of release vSphere API 8.0.2.0.', DeprecationWarning)
            self.profile_name = profile_name
            VapiStruct.__init__(self)


    VGPUDevice._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.virtual_machine_classes.VGPU_device', {
            'profile_name': type.StringType(),
        },
        VGPUDevice,
        False,
        None))


    class DynamicDirectPathIODevice(VapiStruct):
        """
        The ``VirtualMachineClasses.DynamicDirectPathIODevice`` class contains the
        configuration corresponding to a Dynamic DirectPath I/O device. This class
        was added in vSphere API 7.0.3.0.

        .. deprecated:: vSphere API 8.0.2.0
            Use device changes in VirtualMachineConfigSpec associated with the VM
            class to add Dynamic DirectPath I/O devices. 

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     vendor_id=None,
                     device_id=None,
                     custom_label=None,
                    ):
            """
            :type  vendor_id: :class:`long`
            :param vendor_id: The vendor ID of this device. This attribute was added in vSphere
                API 7.0.3.0.
            :type  device_id: :class:`long`
            :param device_id: The device ID of this device. This attribute was added in vSphere
                API 7.0.3.0.
            :type  custom_label: :class:`str` or ``None``
            :param custom_label: The custom label attached to this device. This attribute was added
                in vSphere API 7.0.3.0.
                If None, custom label is not used to identify the device.
            """
            warn('com.vmware.vcenter.namespace_management.VirtualMachineClasses.DynamicDirectPathIODevice is deprecated as of release vSphere API 8.0.2.0.', DeprecationWarning)
            self.vendor_id = vendor_id
            self.device_id = device_id
            self.custom_label = custom_label
            VapiStruct.__init__(self)


    DynamicDirectPathIODevice._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.virtual_machine_classes.dynamic_direct_path_IO_device', {
            'vendor_id': type.IntegerType(),
            'device_id': type.IntegerType(),
            'custom_label': type.OptionalType(type.StringType()),
        },
        DynamicDirectPathIODevice,
        False,
        None))


    class VirtualDevices(VapiStruct):
        """
        The ``VirtualMachineClasses.VirtualDevices`` class contains information
        about the virtual devices associated with a VM class. This class was added
        in vSphere API 7.0.3.0.

        .. deprecated:: vSphere API 8.0.2.0
            Use device changes in VirtualMachineConfigSpec associated with the VM
            class to add vGPU and Dynamic DirectPath I/O virtual devices. 

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'dynamic_direct_path_IO_devices': 'dynamic_direct_path_io_devices',
                                }

        def __init__(self,
                     vgpu_devices=None,
                     dynamic_direct_path_io_devices=None,
                    ):
            """
            :type  vgpu_devices: :class:`list` of :class:`VirtualMachineClasses.VGPUDevice` or ``None``
            :param vgpu_devices: List of vGPU devices. This attribute was added in vSphere API
                7.0.3.0.
                If None, no vGPU devices are present.
            :type  dynamic_direct_path_io_devices: :class:`list` of :class:`VirtualMachineClasses.DynamicDirectPathIODevice` or ``None``
            :param dynamic_direct_path_io_devices: List of Dynamic DirectPath I/O devices. This attribute was added in
                vSphere API 7.0.3.0.
                If None, no Dynamic DirectPath I/O devices are present.
            """
            warn('com.vmware.vcenter.namespace_management.VirtualMachineClasses.VirtualDevices is deprecated as of release vSphere API 8.0.2.0.', DeprecationWarning)
            self.vgpu_devices = vgpu_devices
            self.dynamic_direct_path_io_devices = dynamic_direct_path_io_devices
            VapiStruct.__init__(self)


    VirtualDevices._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.virtual_machine_classes.virtual_devices', {
            'vgpu_devices': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'VirtualMachineClasses.VGPUDevice'))),
            'dynamic_direct_path_IO_devices': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'VirtualMachineClasses.DynamicDirectPathIODevice'))),
        },
        VirtualDevices,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``VirtualMachineClasses.CreateSpec`` class contains the specification
        required to create a VM class object. This class was added in vSphere API
        7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'memory_MB': 'memory_mb',
                                }

        def __init__(self,
                     id=None,
                     cpu_count=None,
                     cpu_reservation=None,
                     memory_mb=None,
                     memory_reservation=None,
                     description=None,
                     devices=None,
                     instance_storage=None,
                     config_spec=None,
                    ):
            """
            :type  id: :class:`str`
            :param id: Identifier of the virtual machine class. This has DNS_LABEL
                restrictions as specified in `
                <https://tools.ietf.org/html/rfc1123>`_. This must be an
                alphanumeric (a-z and 0-9) string and with maximum length of 63
                characters and with the '-' character allowed anywhere except the
                first or last character. This name is unique in this vCenter
                server. This attribute was added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.VirtualMachineClass``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.VirtualMachineClass``.
            :type  cpu_count: :class:`long`
            :param cpu_count: The number of CPUs configured for virtual machine of this class.
                This attribute was added in vSphere API 7.0.2.00100.
            :type  cpu_reservation: :class:`long` or ``None``
            :param cpu_reservation: The percentage of total available CPUs reserved for a virtual
                machine. We multiply this percentage by the minimum frequency
                amongst all the cluster nodes to get the CPU reservation that is
                specified to vSphere in MHz. This attribute was added in vSphere
                API 7.0.2.00100.
                If None, no CPU reservation is requested for the virtual machine.

                .. deprecated:: vSphere API 8.0.2.0
                    Use CPU allocation in
                    :attr:`VirtualMachineClasses.CreateSpec.config_spec` instead to
                    reserve CPUs for a virtual machine. 
            :type  memory_mb: :class:`long`
            :param memory_mb: The amount of memory in MB configured for virtual machine of this
                class. This attribute was added in vSphere API 7.0.2.00100.
            :type  memory_reservation: :class:`long` or ``None``
            :param memory_reservation: The percentage of available memory reserved for a virtual machine
                of this class. Memory reservation must be set to 100% for VM class
                with vGPU or Dynamic DirectPath I/O devices. This attribute was
                added in vSphere API 7.0.2.00100.
                If None, no memory reservation is requested for virtual machine.

                .. deprecated:: vSphere API 8.0.2.0
                    Use memory allocation in
                    :attr:`VirtualMachineClasses.CreateSpec.config_spec` instead to
                    reserve memory for a virtual machine. 
            :type  description: :class:`str` or ``None``
            :param description: Description for the VM class. This attribute was added in vSphere
                API 7.0.2.00100.
                If None, no description is added to the VM class.
            :type  devices: :class:`VirtualMachineClasses.VirtualDevices` or ``None``
            :param devices: Virtual devices that will be attached to the VMs created with this
                class. This attribute was added in vSphere API 7.0.3.0.
                If None, no Virtual device will be attached to the VMs created with
                this class.

                .. deprecated:: vSphere API 8.0.2.0
                    Use device changes in
                    :attr:`VirtualMachineClasses.CreateSpec.config_spec` instead to
                    add vGPU and Dynamic DirectPath I/O virtual devices. 
            :type  instance_storage: :class:`VirtualMachineClasses.InstanceStorage` or ``None``
            :param instance_storage: Instance storage that will be attached to the VMs created with this
                class. This attribute was added in vSphere API 8.0.0.0.
                If None, instance storage specification will not be created.
            :type  config_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param config_spec: A VirtualMachineConfigSpec associated with the VM class. This
                attribute was added in vSphere API 8.0.2.0.
                If None, no config spec will be associated to the VM Class.
            """
            self.id = id
            self.cpu_count = cpu_count
            self.cpu_reservation = cpu_reservation
            self.memory_mb = memory_mb
            self.memory_reservation = memory_reservation
            self.description = description
            self.devices = devices
            self.instance_storage = instance_storage
            self.config_spec = config_spec
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.virtual_machine_classes.create_spec', {
            'id': type.IdType(resource_types='com.vmware.vcenter.namespace_management.VirtualMachineClass'),
            'cpu_count': type.IntegerType(),
            'cpu_reservation': type.OptionalType(type.IntegerType()),
            'memory_MB': type.IntegerType(),
            'memory_reservation': type.OptionalType(type.IntegerType()),
            'description': type.OptionalType(type.StringType()),
            'devices': type.OptionalType(type.ReferenceType(__name__, 'VirtualMachineClasses.VirtualDevices')),
            'instance_storage': type.OptionalType(type.ReferenceType(__name__, 'VirtualMachineClasses.InstanceStorage')),
            'config_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
        },
        CreateSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``VirtualMachineClasses.UpdateSpec`` class contains the specification
        required to update a VM class object. This class was added in vSphere API
        7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'memory_MB': 'memory_mb',
                                }

        def __init__(self,
                     cpu_count=None,
                     cpu_reservation=None,
                     memory_mb=None,
                     memory_reservation=None,
                     description=None,
                     devices=None,
                     instance_storage=None,
                     config_spec=None,
                    ):
            """
            :type  cpu_count: :class:`long` or ``None``
            :param cpu_count: The number of CPUs configured for virtual machine of this class.
                This attribute was added in vSphere API 7.0.2.00100.
                If None the current value the will not be modified.
            :type  cpu_reservation: :class:`long` or ``None``
            :param cpu_reservation: The percentage of total available CPUs reserved for a virtual
                machine. We multiply this percentage by the minimum frequency
                amongst all the cluster nodes to get the CPU reservation that is
                specified to vSphere in MHz. This attribute was added in vSphere
                API 7.0.2.00100.
                If None, no CPU reservation is requested for the virtual machine.

                .. deprecated:: vSphere API 8.0.2.0
                    Use CPU allocation in
                    :attr:`VirtualMachineClasses.UpdateSpec.config_spec` instead to
                    reserve CPUs for a virtual machine. 
            :type  memory_mb: :class:`long` or ``None``
            :param memory_mb: The amount of memory in MB configured for virtual machine of this
                class. This attribute was added in vSphere API 7.0.2.00100.
                If None the current value the will not be modified.
            :type  memory_reservation: :class:`long` or ``None``
            :param memory_reservation: The percentage of available memory reserved for a virtual machine
                of this class. Memory reservation must be set to 100% for VM class
                with vGPU or Dynamic DirectPath I/O devices. This attribute was
                added in vSphere API 7.0.2.00100.
                If None, no memory reservation is requested for virtual machine.

                .. deprecated:: vSphere API 8.0.2.0
                    Use memory allocation in
                    :attr:`VirtualMachineClasses.UpdateSpec.config_spec` instead to
                    reserve memory for a virtual machine. 
            :type  description: :class:`str` or ``None``
            :param description: Description for the VM class. This attribute was added in vSphere
                API 7.0.2.00100.
                If None, description is not updated.
            :type  devices: :class:`VirtualMachineClasses.VirtualDevices` or ``None``
            :param devices: Virtual devices corresponding to the VM class. This attribute was
                added in vSphere API 7.0.3.0.
                If None, virtual devices will not be updated.

                .. deprecated:: vSphere API 8.0.2.0
                    Use device changes in
                    :attr:`VirtualMachineClasses.UpdateSpec.config_spec` instead to
                    add vGPU and Dynamic DirectPath I/O virtual devices. 
            :type  instance_storage: :class:`VirtualMachineClasses.InstanceStorage` or ``None``
            :param instance_storage: Instance storage associated with the VM class. This attribute was
                added in vSphere API 8.0.0.0.
                If None, instance storage specification will not be updated.
            :type  config_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param config_spec: A VirtualMachineConfigSpec associated with the VM class. This
                attribute was added in vSphere API 8.0.2.0.
                If None, the config spec will not be updated.
            """
            self.cpu_count = cpu_count
            self.cpu_reservation = cpu_reservation
            self.memory_mb = memory_mb
            self.memory_reservation = memory_reservation
            self.description = description
            self.devices = devices
            self.instance_storage = instance_storage
            self.config_spec = config_spec
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.virtual_machine_classes.update_spec', {
            'cpu_count': type.OptionalType(type.IntegerType()),
            'cpu_reservation': type.OptionalType(type.IntegerType()),
            'memory_MB': type.OptionalType(type.IntegerType()),
            'memory_reservation': type.OptionalType(type.IntegerType()),
            'description': type.OptionalType(type.StringType()),
            'devices': type.OptionalType(type.ReferenceType(__name__, 'VirtualMachineClasses.VirtualDevices')),
            'instance_storage': type.OptionalType(type.ReferenceType(__name__, 'VirtualMachineClasses.InstanceStorage')),
            'config_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
        },
        UpdateSpec,
        False,
        None))


    class Message(VapiStruct):
        """
        The ``VirtualMachineClasses.Message`` class contains the information about
        the object configuration. This class was added in vSphere API 7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     severity=None,
                     details=None,
                    ):
            """
            :type  severity: :class:`VirtualMachineClasses.Message.MessageSeverity`
            :param severity: Type of the message. This attribute was added in vSphere API
                7.0.2.00100.
            :type  details: :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param details: Details about the message. This attribute was added in vSphere API
                7.0.2.00100.
                If None, message details are not required for taking actions.
            """
            self.severity = severity
            self.details = details
            VapiStruct.__init__(self)


        class MessageSeverity(Enum):
            """
            The ``VirtualMachineClasses.Message.MessageSeverity`` class represents the
            severity of the message. This enumeration was added in vSphere API
            7.0.2.00100.

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
            attribute was added in vSphere API 7.0.2.00100.

            """
            WARNING = None
            """
            Warning message. This may be accompanied by vCenter event. This class
            attribute was added in vSphere API 7.0.2.00100.

            """
            ERROR = None
            """
            Error message. This is accompanied by vCenter event and/or alarm. This
            class attribute was added in vSphere API 7.0.2.00100.

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
            'com.vmware.vcenter.namespace_management.virtual_machine_classes.message.message_severity',
            MessageSeverity))

    Message._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.virtual_machine_classes.message', {
            'severity': type.ReferenceType(__name__, 'VirtualMachineClasses.Message.MessageSeverity'),
            'details': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        Message,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``VirtualMachineClasses.Info`` class contains detailed information
        about the virtual machine class. This class was added in vSphere API
        7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'memory_MB': 'memory_mb',
                                }

        def __init__(self,
                     id=None,
                     cpu_count=None,
                     cpu_reservation=None,
                     memory_mb=None,
                     memory_reservation=None,
                     description=None,
                     namespaces=None,
                     vms=None,
                     config_status=None,
                     messages=None,
                     devices=None,
                     instance_storage=None,
                     config_spec=None,
                    ):
            """
            :type  id: :class:`str`
            :param id: Identifier for the VM class. This attribute was added in vSphere
                API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.VirtualMachineClass``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.VirtualMachineClass``.
            :type  cpu_count: :class:`long`
            :param cpu_count: The number of CPUs configured for virtual machine of this class.
                This attribute was added in vSphere API 7.0.2.00100.
            :type  cpu_reservation: :class:`long` or ``None``
            :param cpu_reservation: The percentage of total available CPUs reserved for a virtual
                machine. We multiply this percentage by the minimum frequency
                amongst all the cluster nodes to get the CPU reservation that is
                specified to vSphere in MHz. This attribute was added in vSphere
                API 7.0.2.00100.
                If None, no CPU reservation is requested for the virtual machine.

                .. deprecated:: vSphere API 8.0.2.0
            :type  memory_mb: :class:`long`
            :param memory_mb: The amount of memory in MB configured for virtual machine of this
                class. This attribute was added in vSphere API 7.0.2.00100.
            :type  memory_reservation: :class:`long` or ``None``
            :param memory_reservation: The percentage of available memory reserved for a virtual machine
                of this class. This attribute was added in vSphere API 7.0.2.00100.
                If None, no memory reservation is requested for virtual machine.

                .. deprecated:: vSphere API 8.0.2.0
            :type  description: :class:`str`
            :param description: Description of the VM class. This attribute was added in vSphere
                API 7.0.2.00100.
            :type  namespaces: :class:`set` of :class:`str`
            :param namespaces: Set of Namespaces associated with this VM class. This attribute was
                added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``. When methods return a
                value of this class as a return value, the attribute will contain
                identifiers for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``.
            :type  vms: :class:`set` of :class:`str`
            :param vms: Set of virtual machines deployed for VM class. This attribute was
                added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``VirtualMachine``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``VirtualMachine``.
            :type  config_status: :class:`VirtualMachineClasses.ConfigStatus`
            :param config_status: Configstatus of VM class. This attribute was added in vSphere API
                7.0.2.00100.
            :type  messages: :class:`list` of :class:`VirtualMachineClasses.Message`
            :param messages: Current set of messages associated with the object. This attribute
                was added in vSphere API 7.0.2.00100.
            :type  devices: :class:`VirtualMachineClasses.VirtualDevices`
            :param devices: Virtual devices corresponding to the VM class. This attribute was
                added in vSphere API 7.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.

                .. deprecated:: vSphere API 8.0.2.0
            :type  instance_storage: :class:`VirtualMachineClasses.InstanceStorage` or ``None``
            :param instance_storage: Instance storage associated with the VM class. This attribute was
                added in vSphere API 8.0.0.0.
                If None, no instance storage is present.
            :type  config_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param config_spec: A VirtualMachineConfigSpec associated with the VM class. This
                attribute was added in vSphere API 8.0.2.0.
                If None, a config spec is not used to configure this VM class.
            """
            self.id = id
            self.cpu_count = cpu_count
            self.cpu_reservation = cpu_reservation
            self.memory_mb = memory_mb
            self.memory_reservation = memory_reservation
            self.description = description
            self.namespaces = namespaces
            self.vms = vms
            self.config_status = config_status
            self.messages = messages
            self.devices = devices
            self.instance_storage = instance_storage
            self.config_spec = config_spec
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.virtual_machine_classes.info', {
            'id': type.IdType(resource_types='com.vmware.vcenter.namespace_management.VirtualMachineClass'),
            'cpu_count': type.IntegerType(),
            'cpu_reservation': type.OptionalType(type.IntegerType()),
            'memory_MB': type.IntegerType(),
            'memory_reservation': type.OptionalType(type.IntegerType()),
            'description': type.StringType(),
            'namespaces': type.SetType(type.IdType()),
            'vms': type.SetType(type.IdType()),
            'config_status': type.ReferenceType(__name__, 'VirtualMachineClasses.ConfigStatus'),
            'messages': type.ListType(type.ReferenceType(__name__, 'VirtualMachineClasses.Message')),
            'devices': type.OptionalType(type.ReferenceType(__name__, 'VirtualMachineClasses.VirtualDevices')),
            'instance_storage': type.OptionalType(type.ReferenceType(__name__, 'VirtualMachineClasses.InstanceStorage')),
            'config_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
        },
        Info,
        False,
        None))



    def create(self,
               spec,
               ):
        """
        Create a VM class object. This method was added in vSphere API
        7.0.2.00100.

        :type  spec: :class:`VirtualMachineClasses.CreateSpec`
        :param spec: Information about the VM class object to be created.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if a VM class by the name as specified in the ``spec`` already
            exists in the vCenter inventory.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the input ``spec.instanceStorage.policy`` refers to an invalid
            storage policy or if the input ``spec`` includes settings that are
            out of acceptable bounds or a combination of settings that are not
            internally consistent with the input ``spec``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have VirtualMachineClasses.Manage privilege.
        """
        return self._invoke('create',
                            {
                            'spec': spec,
                            })

    def update(self,
               vm_class,
               spec,
               ):
        """
        Update the configuration of the VM class object. This method was added
        in vSphere API 7.0.2.00100.

        :type  vm_class: :class:`str`
        :param vm_class: Identifier for the VM class.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.VirtualMachineClass``.
        :type  spec: :class:`VirtualMachineClasses.UpdateSpec`
        :param spec: Information about the VM class object to be updated.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if a VM class by the name as specified in the ``spec`` already
            exists in the vCenter inventory.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the input ``spec.instanceStorage.policy`` refers to an invalid
            storage policy or if the input ``spec`` includes settings that are
            out of acceptable bounds or a combination of settings that are not
            internally consistent with the input ``spec``.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if or the ``vm_class`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have VirtualMachineClasses.Manage privilege.
        """
        return self._invoke('update',
                            {
                            'vm_class': vm_class,
                            'spec': spec,
                            })

    def get(self,
            vm_class,
            ):
        """
        Return information about a VM class. This method was added in vSphere
        API 7.0.2.00100.

        :type  vm_class: :class:`str`
        :param vm_class: Identifier for the VM class.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.VirtualMachineClass``.
        :rtype: :class:`VirtualMachineClasses.Info`
        :return: Information about the specified VM class.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if VM class can not be found in the vCenter inventory.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'vm_class': vm_class,
                            })

    def list(self):
        """
        Return information about all VirtualMachine classes. This method was
        added in vSphere API 7.0.2.00100.


        :rtype: :class:`list` of :class:`VirtualMachineClasses.Info`
        :return: List of information about all VirtualMachine classes
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list', None)

    def delete(self,
               vm_class,
               ):
        """
        Delete the VM class object. This method was added in vSphere API
        7.0.2.00100.

        :type  vm_class: :class:`str`
        :param vm_class: Identifier for the VM class.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.VirtualMachineClass``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            - TBD
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            VM class could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have VirtualMachineClasses.Manage privilege.
        """
        return self._invoke('delete',
                            {
                            'vm_class': vm_class,
                            })
class ClusterAvailableVersions(VapiInterface):
    """
    The ``ClusterAvailableVersions`` class provides methods to retrieve
    available upgrade versions of WCP and detailed information about each
    upgrade.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.cluster_available_versions'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ClusterAvailableVersionsStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``ClusterAvailableVersions.Summary`` class contains the information
        about each available upgrade version.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     version=None,
                     name=None,
                     description=None,
                     release_date=None,
                     release_notes=None,
                    ):
            """
            :type  version: :class:`str`
            :param version: Version of the upgrade.
            :type  name: :class:`str`
            :param name: Name of the upgrade.
            :type  description: :class:`str`
            :param description: Description of the upgrade.
            :type  release_date: :class:`datetime.datetime`
            :param release_date: Release date of the upgrade.
            :type  release_notes: :class:`str`
            :param release_notes: Release details of the upgrade.
            """
            self.version = version
            self.name = name
            self.description = description
            self.release_date = release_date
            self.release_notes = release_notes
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.cluster_available_versions.summary', {
            'version': type.StringType(),
            'name': type.StringType(),
            'description': type.StringType(),
            'release_date': type.DateTimeType(),
            'release_notes': type.StringType(),
        },
        Summary,
        False,
        None))



    def list(self):
        """
        Get information about each available upgrade.


        :rtype: :class:`list` of :class:`ClusterAvailableVersions.Summary`
        :return: Information for each upgrade.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list', None)
class ClusterCompatibility(VapiInterface):
    """
    The ``ClusterCompatibility`` class provides methods to get
    Namespace-related compatibility information for clusters in this vCenter.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.cluster_compatibility'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ClusterCompatibilityStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``ClusterCompatibility.Summary`` class contains the information about
        the compatibility of a vSphere cluster.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     cluster=None,
                     compatible=None,
                     incompatibility_reasons=None,
                    ):
            """
            :type  cluster: :class:`str`
            :param cluster: Identifier of the vSphere cluster.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            :type  compatible: :class:`bool`
            :param compatible: Compatibility of this vSphere cluster. If false, the list of
                incompatibility issues will be given in the
                ``incompatibilityReasons`` field.
            :type  incompatibility_reasons: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param incompatibility_reasons: Reasons for incompatibility.
            """
            self.cluster = cluster
            self.compatible = compatible
            self.incompatibility_reasons = incompatibility_reasons
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.cluster_compatibility.summary', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'compatible': type.BooleanType(),
            'incompatibility_reasons': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        Summary,
        False,
        None))


    class ZoneSummary(VapiStruct):
        """
        The ``ClusterCompatibility.ZoneSummary`` class contains the information
        about the compatibility of a vSphere Zone and the vSphere clusters
        associated with it. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     zone=None,
                     compatible=None,
                     cluster_summaries=None,
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
            :type  compatible: :class:`bool`
            :param compatible: Flag to indicate whether the current Zone can be used to enable a
                Supervisor cluster. If false, the list of incompatibility issues
                will be given in the ``clusterSummaries`` field. This attribute was
                added in vSphere API 8.0.0.1.
            :type  cluster_summaries: :class:`list` of :class:`ClusterCompatibility.Summary`
            :param cluster_summaries: A list of information about the compatibility of vSphere clusters
                associated with this vSphere Zone. This attribute was added in
                vSphere API 8.0.0.1.
            """
            self.zone = zone
            self.compatible = compatible
            self.cluster_summaries = cluster_summaries
            VapiStruct.__init__(self)


    ZoneSummary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.cluster_compatibility.zone_summary', {
            'zone': type.IdType(resource_types='com.vmware.vcenter.consumption_domains.Zone'),
            'compatible': type.BooleanType(),
            'cluster_summaries': type.ListType(type.ReferenceType(__name__, 'ClusterCompatibility.Summary')),
        },
        ZoneSummary,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``ClusterCompatibility.FilterSpec`` class contains attributes used to
        filter the results when listing clusters (see
        :func:`ClusterCompatibility.list`) and their compatibility information.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     compatible=None,
                     network_provider=None,
                    ):
            """
            :type  compatible: :class:`bool` or ``None``
            :param compatible: Set this flag to true to only list vSphere clusters that are
                currently compatible with the Namespaces feature. If set to false,
                both compatible and incompatible vSphere clusters will be listed.
                If None, both compatible and incompatible vSphere clusters will be
                listed.
            :type  network_provider: :class:`Clusters.NetworkProvider` or ``None``
            :param network_provider: The network provider whose networks will be considered. This
                attribute was added in vSphere API 7.0.1.0.
                If None, this will default to
                :attr:`Clusters.NetworkProvider.NSXT_CONTAINER_PLUGIN`.
            """
            self.compatible = compatible
            self.network_provider = network_provider
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.cluster_compatibility.filter_spec', {
            'compatible': type.OptionalType(type.BooleanType()),
            'network_provider': type.OptionalType(type.ReferenceType(__name__, 'Clusters.NetworkProvider')),
        },
        FilterSpec,
        False,
        None))


    class FilterSpecV2(VapiStruct):
        """
        The ``ClusterCompatibility.FilterSpecV2`` class contains attributes used to
        filter the results when listing clusters (see
        :func:`ClusterCompatibility.list_v2`) and their compatibility information.
        This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     compatible=None,
                     network_provider=None,
                    ):
            """
            :type  compatible: :class:`bool` or ``None``
            :param compatible: Set this flag to true to only return vSphere clusters that are
                currently compatible with the Namespaces feature. If set to false,
                both compatible and incompatible vSphere clusters will be returned.
                This attribute was added in vSphere API 8.0.0.1.
                If None, both compatible and incompatible vSphere clusters will be
                listed.
            :type  network_provider: :class:`com.vmware.vcenter.namespace_management.supervisors.networks.workload_client.NetworkType` or ``None``
            :param network_provider: The network type that will be considered. A Supervisor can only be
                enabled with this network type if all hosts are compatible for this
                specific network type. This attribute was added in vSphere API
                8.0.0.1.
                If None, this will default to
                :attr:`com.vmware.vcenter.namespace_management.supervisors.networks.workload_client.NetworkType.NSXT`.
            """
            self.compatible = compatible
            self.network_provider = network_provider
            VapiStruct.__init__(self)


    FilterSpecV2._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.cluster_compatibility.filter_spec_v2', {
            'compatible': type.OptionalType(type.BooleanType()),
            'network_provider': type.OptionalType(type.ReferenceType('com.vmware.vcenter.namespace_management.supervisors.networks.workload_client', 'NetworkType')),
        },
        FilterSpecV2,
        False,
        None))


    class ZoneFilterSpec(VapiStruct):
        """
        The ``ClusterCompatibility.ZoneFilterSpec`` class contains attributes used
        to filter the results when listing vSphere Zones (see
        :func:`ClusterCompatibility.list_v2`) and their compatibility information.
        This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     zones=None,
                    ):
            """
            :type  zones: :class:`list` of :class:`str` or ``None``
            :param zones: A list of vSphere Zone identifiers which will be used to filter
                vSphere Zones that correspond to this specific set of identifiers.
                This attribute was added in vSphere API 8.0.0.1.
                If None or empty, results will not be filtered for specific vSphere
                Zone identifiers.
            """
            self.zones = zones
            VapiStruct.__init__(self)


    ZoneFilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.cluster_compatibility.zone_filter_spec', {
            'zones': type.OptionalType(type.ListType(type.StringType())),
        },
        ZoneFilterSpec,
        False,
        None))


    class ZoneCompatibilityInfo(VapiStruct):
        """
        The ``ClusterCompatibility.ZoneCompatibilityInfo`` class contains the
        information about the compatibility between a list of vSphere Zones. This
        class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     compatible=None,
                     zone_summaries=None,
                     incompatibility_reasons=None,
                    ):
            """
            :type  compatible: :class:`bool`
            :param compatible: Flag to indicate whether the vSphere Zones are compatible with each
                other. If false, the list of incompatibility issues will be given
                in the ``incompatibilityReasons`` field. This attribute was added
                in vSphere API 8.0.0.1.
            :type  zone_summaries: :class:`list` of :class:`ClusterCompatibility.ZoneSummary`
            :param zone_summaries: Information about the compatibility of a list of vSphere Zones and
                the vSphere clusters associated with them. This attribute was added
                in vSphere API 8.0.0.1.
            :type  incompatibility_reasons: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param incompatibility_reasons: Reasons for incompatibility between the vSphere Zones. This
                attribute was added in vSphere API 8.0.0.1.
            """
            self.compatible = compatible
            self.zone_summaries = zone_summaries
            self.incompatibility_reasons = incompatibility_reasons
            VapiStruct.__init__(self)


    ZoneCompatibilityInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.cluster_compatibility.zone_compatibility_info', {
            'compatible': type.BooleanType(),
            'zone_summaries': type.ListType(type.ReferenceType(__name__, 'ClusterCompatibility.ZoneSummary')),
            'incompatibility_reasons': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        ZoneCompatibilityInfo,
        False,
        None))



    def list(self,
             filter=None,
             ):
        """
        Returns Namespaces compatibility information for all vSphere clusters
        in the vCenter Server matching the
        :class:`ClusterCompatibility.FilterSpec`. The result contains only
        visible (subject to permission checks) clusters.

        :type  filter: :class:`ClusterCompatibility.FilterSpec` or ``None``
        :param filter: Specification of matching clusters for which information should be
            returned.
            If None, the behavior is equivalent to a
            :class:`ClusterCompatibility.FilterSpec` with all attributes None
            which means all NSX-T clusters the user is authorized to view will
            be returned.
        :rtype: :class:`list` of :class:`ClusterCompatibility.Summary`
        :return: Namespaces compatibility information for the clusters matching the
            the :class:`ClusterCompatibility.FilterSpec`.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``filter`` contains any error.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege on the vSphere
            clusters.
        """
        return self._invoke('list',
                            {
                            'filter': filter,
                            })

    def list_v2(self,
                zone_filter=None,
                cluster_filter=None,
                ):
        """
        Returns Namespaces compatibility information for all vSphere clusters
        that match the  and are associated with the vSphere Zones in the
        vCenter Server that match the . The result contains only visible
        (subject to permission checks) clusters. This method was added in
        vSphere API 8.0.0.1.

        :type  zone_filter: :class:`ClusterCompatibility.ZoneFilterSpec` or ``None``
        :param zone_filter: Specification used to filter the results when listing vSphere
            Zones.
            If None, the behavior is equivalent to a  with all attributes None
            which means all available vSphere Zones will be returned.
        :type  cluster_filter: :class:`ClusterCompatibility.FilterSpecV2` or ``None``
        :param cluster_filter: Specification of matching vSphere clusters for which information
            should be returned.
            If None, the behavior is equivalent to a  with all attributes None
            which means all NSX-T clusters the user is authorized to view will
            be returned.
        :rtype: :class:`ClusterCompatibility.ZoneCompatibilityInfo`
        :return: Namespaces compatibility information for vSphere Zones that match
            the  and the vSphere clusters associated with them that match the .
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``zone_filter`` or ``cluster_filter`` contain any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege on the vSphere
            clusters associated with the vSphere Zones.
        """
        return self._invoke('list_v2',
                            {
                            'zone_filter': zone_filter,
                            'cluster_filter': cluster_filter,
                            })
class ClusterSizeInfo(VapiInterface):
    """
    The ``ClusterSizeInfo`` class provides methods to retrieve various sizes
    available for enabling Namespaces and information about each size.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.cluster_size_info'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ClusterSizeInfoStub)
        self._VAPI_OPERATION_IDS = {}

    class VmInfo(VapiStruct):
        """
        The ``ClusterSizeInfo.VmInfo`` class contains the information about the
        configuration of the virtual machines which would be created for
        Namespaces.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     count=None,
                     cores_per_socket=None,
                     memory=None,
                     capacity=None,
                    ):
            """
            :type  count: :class:`long`
            :param count: Number of CPU cores.
            :type  cores_per_socket: :class:`long`
            :param cores_per_socket: Number of CPU cores per socket.
            :type  memory: :class:`long`
            :param memory: Memory size, in mebibytes.
            :type  capacity: :class:`long`
            :param capacity: Overall capacity of the disks in the virtual machine, in mebibytes.
            """
            self.count = count
            self.cores_per_socket = cores_per_socket
            self.memory = memory
            self.capacity = capacity
            VapiStruct.__init__(self)


    VmInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.cluster_size_info.vm_info', {
            'count': type.IntegerType(),
            'cores_per_socket': type.IntegerType(),
            'memory': type.IntegerType(),
            'capacity': type.IntegerType(),
        },
        VmInfo,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``ClusterSizeInfo.Info`` class contains the information about limits
        associated with a ``SizingHint``.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     num_supported_pods=None,
                     num_supported_services=None,
                     default_service_cidr=None,
                     default_pod_cidr=None,
                     master_vm_info=None,
                     worker_vm_info=None,
                    ):
            """
            :type  num_supported_pods: :class:`long`
            :param num_supported_pods: The maximum number of supported pods.
            :type  num_supported_services: :class:`long`
            :param num_supported_services: The maximum number of supported services.
            :type  default_service_cidr: :class:`Ipv4Cidr`
            :param default_service_cidr: Default CIDR range from which Kubernetes allocates service cluster
                IP addresses.
            :type  default_pod_cidr: :class:`Ipv4Cidr`
            :param default_pod_cidr: Default CIDR range from which Kubernetes allocates pod IP
                addresses.
            :type  master_vm_info: :class:`ClusterSizeInfo.VmInfo`
            :param master_vm_info: Information about Kubernetes API server virtual machine
                configuration.
            :type  worker_vm_info: :class:`ClusterSizeInfo.VmInfo` or ``None``
            :param worker_vm_info: Information about worker virtual machine configuration.
                If None, the configuration of the worker VM is not fixed.
            """
            self.num_supported_pods = num_supported_pods
            self.num_supported_services = num_supported_services
            self.default_service_cidr = default_service_cidr
            self.default_pod_cidr = default_pod_cidr
            self.master_vm_info = master_vm_info
            self.worker_vm_info = worker_vm_info
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.cluster_size_info.info', {
            'num_supported_pods': type.IntegerType(),
            'num_supported_services': type.IntegerType(),
            'default_service_cidr': type.ReferenceType(__name__, 'Ipv4Cidr'),
            'default_pod_cidr': type.ReferenceType(__name__, 'Ipv4Cidr'),
            'master_vm_info': type.ReferenceType(__name__, 'ClusterSizeInfo.VmInfo'),
            'worker_vm_info': type.OptionalType(type.ReferenceType(__name__, 'ClusterSizeInfo.VmInfo')),
        },
        Info,
        False,
        None))



    def get(self):
        """
        Get information about the default values associated with various sizes.


        :rtype: :class:`dict` of :class:`SizingHint` and :class:`ClusterSizeInfo.Info`
        :return: Information for each size.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        """
        return self._invoke('get', None)
class DistributedSwitchCompatibility(VapiInterface):
    """
    The ``DistributedSwitchCompatibility`` class provides methods to get
    Namespaces compatibility information of Distributed Switches in this
    vCenter.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.distributed_switch_compatibility'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _DistributedSwitchCompatibilityStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``DistributedSwitchCompatibility.Summary`` class contains information
        about the compatibility of a vSphere Distributed Switch with the Namespaces
        feature.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     distributed_switch=None,
                     compatible=None,
                     incompatibility_reasons=None,
                     network_provider=None,
                     compatible_networks=None,
                    ):
            """
            :type  distributed_switch: :class:`str`
            :param distributed_switch: Identifier of the switch. If
                :attr:`DistributedSwitchCompatibility.Summary.network_provider` is
                either None or is set to NSXT_CONTAINER_PLUGIN, the value of this
                field will refer to the UUID of a vim.DistributedVirtualSwitch.
                Otherwise, the value of the field will refer to the ID of a
                vim.DistributedVirtualSwitch.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``vSphereDistributedSwitch``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``vSphereDistributedSwitch``.
            :type  compatible: :class:`bool`
            :param compatible: Compatibility of this switch with vSphere Namespaces.
            :type  incompatibility_reasons: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param incompatibility_reasons: List of reasons for incompatibility.
                If None, this Distributed Switch is compatible.
            :type  network_provider: :class:`Clusters.NetworkProvider` or ``None``
            :param network_provider: The network provider whose networks were considered. This attribute
                was added in vSphere API 7.0.1.0.
                If None, clients clients should assume the value to be
                NSXT_CONTAINER_PLUGIN.
            :type  compatible_networks: :class:`list` of :class:`str` or ``None``
            :param compatible_networks: List of compatible (PortGroup) Networks under the distributed
                switch. This attribute was added in vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``Network``. When methods return a value of this class as a return
                value, the attribute will contain identifiers for the resource
                type: ``Network``.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.distributed_switch = distributed_switch
            self.compatible = compatible
            self.incompatibility_reasons = incompatibility_reasons
            self.network_provider = network_provider
            self.compatible_networks = compatible_networks
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.distributed_switch_compatibility.summary', {
            'distributed_switch': type.IdType(resource_types='vSphereDistributedSwitch'),
            'compatible': type.BooleanType(),
            'incompatibility_reasons': type.OptionalType(type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'))),
            'network_provider': type.OptionalType(type.ReferenceType(__name__, 'Clusters.NetworkProvider')),
            'compatible_networks': type.OptionalType(type.ListType(type.IdType())),
        },
        Summary,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``DistributedSwitchCompatibility.FilterSpec`` class contains attributes
        used to filter the results when listing Distributed Switches (see
        :func:`DistributedSwitchCompatibility.list`) and their compatibility
        information.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     compatible=None,
                     network_provider=None,
                    ):
            """
            :type  compatible: :class:`bool` or ``None``
            :param compatible: Compatibility criteria for matching the filter. If true, only
                Distributed Switches which are compatible with vSphere Namespaces
                match the filter. If false, only Distributed Switches which are
                incompatible with vSphere Namespaces match the filter.
                If None, both compatible and incompatible Distributed Switches
                match the filter.
            :type  network_provider: :class:`Clusters.NetworkProvider` or ``None``
            :param network_provider: The network provider whose networks will be considered. If unset,
                this will default to NSXT_CONTAINER_PLUGIN. This attribute was
                added in vSphere API 7.0.1.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.compatible = compatible
            self.network_provider = network_provider
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.distributed_switch_compatibility.filter_spec', {
            'compatible': type.OptionalType(type.BooleanType()),
            'network_provider': type.OptionalType(type.ReferenceType(__name__, 'Clusters.NetworkProvider')),
        },
        FilterSpec,
        False,
        None))



    def list(self,
             cluster,
             filter=None,
             ):
        """
        Returns Namespaces compatibility information of Distributed Switches in
        vCenter associated with the vCenter cluster, matching the
        :class:`DistributedSwitchCompatibility.FilterSpec`.

        :type  cluster: :class:`str`
        :param cluster: Identifier of a vCenter Cluster. Only Distributed Switches
            associated with the vCenter Cluster will be considered by the
            filter.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  filter: :class:`DistributedSwitchCompatibility.FilterSpec` or ``None``
        :param filter: Specification of matching Distributed Switches for which
            information should be returned.
            If None, the behavior is equivalent to a
            :class:`DistributedSwitchCompatibility.FilterSpec` with all
            attributes None which means all Distributed Switches match the
            filter.
        :rtype: :class:`list` of :class:`DistributedSwitchCompatibility.Summary`
        :return: Namespaces compatibility information for Distributed Switches
            matching the the
            :class:`DistributedSwitchCompatibility.FilterSpec`.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InternalServerError` 
            if the server reports an unknown internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if no cluster with the given ``cluster`` ID can be found
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list',
                            {
                            'cluster': cluster,
                            'filter': filter,
                            })
class EdgeClusterCompatibility(VapiInterface):
    """
    The ``EdgeClusterCompatibility`` class provides methods to get Namespaces
    compatibility information of NSX Edge Clusters.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.edge_cluster_compatibility'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _EdgeClusterCompatibilityStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``EdgeClusterCompatibility.Summary`` class contains information about
        an NSX-T Edge Cluster, including its compatibility with the vCenter
        Namespaces feature.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     edge_cluster=None,
                     display_name=None,
                     compatible=None,
                     incompatibility_reasons=None,
                    ):
            """
            :type  edge_cluster: :class:`str`
            :param edge_cluster: Identifier of the Edge Cluster.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``NSXEdgeCluster``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``NSXEdgeCluster``.
            :type  display_name: :class:`str`
            :param display_name: Display name of the Edge Cluster.
            :type  compatible: :class:`bool`
            :param compatible: Compatibility of this Edge Cluster with Namespaces feature.
            :type  incompatibility_reasons: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param incompatibility_reasons: List of reasons for incompatibility.
                If None, this Edge Cluster is compatible.
            """
            self.edge_cluster = edge_cluster
            self.display_name = display_name
            self.compatible = compatible
            self.incompatibility_reasons = incompatibility_reasons
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.edge_cluster_compatibility.summary', {
            'edge_cluster': type.IdType(resource_types='NSXEdgeCluster'),
            'display_name': type.StringType(),
            'compatible': type.BooleanType(),
            'incompatibility_reasons': type.OptionalType(type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'))),
        },
        Summary,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``EdgeClusterCompatibility.FilterSpec`` class contains attributes used
        to filter the results when listing Edge Clusters (see
        :func:`EdgeClusterCompatibility.list`) and their compatibility information.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     compatible=None,
                    ):
            """
            :type  compatible: :class:`bool` or ``None``
            :param compatible: Compatibility criteria for matching the filter. If true, only Edge
                Clusters which are compatible with vSphere Namespaces match the
                filter. If false, only Edge Clusters which are incompatible with
                vSphere Namespaces match the filter.
                If None, both compatible and incompatible Edge Clusters match the
                filter.
            """
            self.compatible = compatible
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.edge_cluster_compatibility.filter_spec', {
            'compatible': type.OptionalType(type.BooleanType()),
        },
        FilterSpec,
        False,
        None))



    def list(self,
             cluster,
             distributed_switch,
             filter=None,
             ):
        """
        Returns Namespaces compatibility information of NSX-T Edge Clusters
        matching the :class:`EdgeClusterCompatibility.FilterSpec`.

        :type  cluster: :class:`str`
        :param cluster: Identifier of a vCenter Cluster. Only Edge Clusters that are
            associated with the particular vCenter Cluster will be considered
            by the filter.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  distributed_switch: :class:`str`
        :param distributed_switch: Identifier of a Distributed Switch. Only Edge Clusters that are
            associated with the particular Distributed Switch will be
            considered by the filter.
            The parameter must be an identifier for the resource type:
            ``vSphereDistributedSwitch``.
        :type  filter: :class:`EdgeClusterCompatibility.FilterSpec` or ``None``
        :param filter: Specification of matching Edge Clusters for which information
            should be returned.
            If None, the behavior is equivalent to a
            :class:`EdgeClusterCompatibility.FilterSpec` with all attributes
            None which means all Edge Clusters match the filter.
        :rtype: :class:`list` of :class:`EdgeClusterCompatibility.Summary`
        :return: List of summaries of Edge Clusters associated with the given
            vCenter Cluster and Distributed Switch matching the
            :class:`EdgeClusterCompatibility.FilterSpec`.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InternalServerError` 
            if the server reports an unknown internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if no cluster with the given ``cluster`` ID can be found
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list',
                            {
                            'cluster': cluster,
                            'distributed_switch': distributed_switch,
                            'filter': filter,
                            })
class SupportBundle(VapiInterface):
    """
    The ``SupportBundle`` class provides methods to retrieve the cluster's
    Namespaces-related support bundle download location.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.support_bundle'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SupportBundleStub)
        self._VAPI_OPERATION_IDS = {}

    class Token(VapiStruct):
        """
        The ``SupportBundle.Token`` class contains information about the token
        required in the HTTP GET request to generate the support bundle.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     token=None,
                     expiry=None,
                    ):
            """
            :type  token: :class:`str`
            :param token: A one-time, short-lived token required in the HTTP header of the
                request to the url. This token needs to be passed in as a header
                with the name "wcp-support-bundle-token".
            :type  expiry: :class:`str`
            :param expiry: Expiry time of the token
            """
            self.token = token
            self.expiry = expiry
            VapiStruct.__init__(self)


    Token._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.support_bundle.token', {
            'token': type.StringType(),
            'expiry': type.StringType(),
        },
        Token,
        False,
        None))


    class Location(VapiStruct):
        """
        The ``SupportBundle.Location`` class contains the URI location to download
        the per-cluster support bundle from, as well as a token required (as a
        header on the HTTP request) to get the bundle. The validity of the token is
        5 minutes. After the token expires, any attempt to call the URI with said
        token will fail.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     url=None,
                     wcp_support_bundle_token=None,
                    ):
            """
            :type  url: :class:`str`
            :param url: Support Bundle Download URL.
            :type  wcp_support_bundle_token: :class:`SupportBundle.Token`
            :param wcp_support_bundle_token: Information about the token required in the HTTP GET request to
                generate the support bundle.
            """
            self.url = url
            self.wcp_support_bundle_token = wcp_support_bundle_token
            VapiStruct.__init__(self)


    Location._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.support_bundle.location', {
            'url': type.StringType(),
            'wcp_support_bundle_token': type.ReferenceType(__name__, 'SupportBundle.Token'),
        },
        Location,
        False,
        None))



    def create(self,
               cluster,
               ):
        """
        Returns the location :class:`SupportBundle.Location` information for
        downloading the Namespaces-related support bundle for the specified
        cluster. 
        
        Retrieving a support bundle involves two steps: 
        
        * Step 1: Invoke method to provision a token and a URI.
        * Step 2: Make an HTTP GET request using URI and one time used token
          returned in step 1 to generate the support bundle and return it.
        
        There can only be one valid token per cluster at any given time. If
        this method is invoked again for the same cluster identifier while a
        token still valid, the API will return the same
        :class:`SupportBundle.Location` response. 
        
        The HTTP GET request will: 
        
        * return 401 (Not Authorized) if the download URL is recognized, but
          the token is invalid.
        * otherwise return 200 (OK), mark the token used (invalidating it for
          any future use), open a application/tar download stream for the client,
          and start the bundle process. As part of its work, the API will
          orchestrate support bundling on the worker nodes of a cluster. If a
          failure occurs during the collection of support bundle from worker
          node, the API will not abort the request, but will log a warning and
          move on to processing other worker nodes' bundles. The API will only
          abort its operation if the content of the stream has been corrupted.
          When the API has to abort its operation (and the response stream), it
          will not provide any indication of failures to the client. The client
          will need to verify validity of the resultant file based on the format
          specified in the response's Content-Disposition header.

        :type  cluster: :class:`str`
        :param cluster: Identifier of cluster for which the Namespaces-related support
            bundle should be generated.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`SupportBundle.Location`
        :return: the download location of the support bundle for the cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the specified cluster is not registered on this vCenter server.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Global.Diagnostics privilege.
        """
        return self._invoke('create',
                            {
                            'cluster': cluster,
                            })
class NamespaceResourceOptions(VapiInterface):
    """
    The ``NamespaceResourceOptions`` class provides methods to get the objects
    used to create and modify resource quotas on a namespace.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.namespace_resource_options'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _NamespaceResourceOptionsStub)
        self._VAPI_OPERATION_IDS = {}

    class Info(VapiStruct):
        """
        The ``NamespaceResourceOptions.Info`` class contains the information about
        the objects used to set and update resource quota keys on a namespace.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     create_resource_quota_type=None,
                     update_resource_quota_type=None,
                    ):
            """
            :type  create_resource_quota_type: :class:`str`
            :param create_resource_quota_type: Identifier of the class used to set resource quotas on the
                namespace. See com.vmware.vcenter.namespaces.Instances#create and
                com.vmware.vcenter.namespaces.Instances#set.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vapi.structure``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``com.vmware.vapi.structure``.
            :type  update_resource_quota_type: :class:`str`
            :param update_resource_quota_type: Identifier of the class used to update resource quotas on the
                namespace. See com.vmware.vcenter.namespaces.Instances#update.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vapi.structure``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``com.vmware.vapi.structure``.
            """
            self.create_resource_quota_type = create_resource_quota_type
            self.update_resource_quota_type = update_resource_quota_type
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.namespace_resource_options.info', {
            'create_resource_quota_type': type.IdType(resource_types='com.vmware.vapi.structure'),
            'update_resource_quota_type': type.IdType(resource_types='com.vmware.vapi.structure'),
        },
        Info,
        False,
        None))



    def get(self,
            cluster,
            ):
        """
        Get the information about the objects used to set and update resource
        quota keys for version of Kubernetes running on {#link cluster}.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster hosting the namespace on which the
            resource quota needs to be set.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`NamespaceResourceOptions.Info`
        :return: Information about the structures representing the resource spec.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if cluster could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified cluster is not enabled for Namespaces.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })
class _ClustersStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for enable operation
        enable_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.ReferenceType(__name__, 'Clusters.EnableSpec'),
        })
        enable_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unable_to_allocate_resource':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnableToAllocateResource'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        enable_input_value_validator_list = [
        ]
        enable_output_validator_list = [
        ]
        enable_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/clusters/{cluster}',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'enable',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for disable operation
        disable_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        disable_error_dict = {
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
        disable_input_value_validator_list = [
        ]
        disable_output_validator_list = [
        ]
        disable_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/clusters/{cluster}',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'disable',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
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
            url_template='/vcenter/namespace-management/clusters/{cluster}',
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
            url_template='/vcenter/namespace-management/clusters',
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
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.ReferenceType(__name__, 'Clusters.SetSpec'),
        })
        set_error_dict = {
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
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/vcenter/namespace-management/clusters/{cluster}',
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

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.ReferenceType(__name__, 'Clusters.UpdateSpec'),
        })
        update_error_dict = {
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
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespace-management/clusters/{cluster}',
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

        # properties for rotate_password operation
        rotate_password_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        rotate_password_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),

        }
        rotate_password_input_value_validator_list = [
        ]
        rotate_password_output_validator_list = [
        ]
        rotate_password_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/clusters/{cluster}',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'rotate_password',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'enable': {
                'input_type': enable_input_type,
                'output_type': type.VoidType(),
                'errors': enable_error_dict,
                'input_value_validator_list': enable_input_value_validator_list,
                'output_validator_list': enable_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'disable': {
                'input_type': disable_input_type,
                'output_type': type.VoidType(),
                'errors': disable_error_dict,
                'input_value_validator_list': disable_input_value_validator_list,
                'output_validator_list': disable_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Clusters.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'Clusters.Summary')),
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
            'update': {
                'input_type': update_input_type,
                'output_type': type.VoidType(),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': update_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'rotate_password': {
                'input_type': rotate_password_input_type,
                'output_type': type.VoidType(),
                'errors': rotate_password_error_dict,
                'input_value_validator_list': rotate_password_input_value_validator_list,
                'output_validator_list': rotate_password_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'enable': enable_rest_metadata,
            'disable': disable_rest_metadata,
            'get': get_rest_metadata,
            'list': list_rest_metadata,
            'set': set_rest_metadata,
            'update': update_rest_metadata,
            'rotate_password': rotate_password_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.clusters',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _HostsConfigStub(ApiInterfaceStub):
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
            url_template='/vcenter/namespace-management/capability',
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
                'output_type': type.ReferenceType(__name__, 'HostsConfig.Info'),
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
            self, iface_name='com.vmware.vcenter.namespace_management.hosts_config',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _LoadBalancersStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'id': type.IdType(resource_types='com.vmware.vcenter.namespace_management.LoadBalancerConfig'),
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
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespace-management/clusters/{cluster}/load-balancers/{id}',
            path_variables={
                'cluster': 'cluster',
                'id': 'id',
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
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespace-management/clusters/{cluster}/load-balancers',
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

        # properties for set operation
        set_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'id': type.IdType(resource_types='com.vmware.vcenter.namespace_management.LoadBalancerConfig'),
            'spec': type.ReferenceType(__name__, 'LoadBalancers.SetSpec'),
        })
        set_error_dict = {
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
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/vcenter/namespace-management/clusters/{cluster}/load-balancers/{id}',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
                'id': 'id',
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
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'id': type.IdType(resource_types='com.vmware.vcenter.namespace_management.LoadBalancerConfig'),
            'spec': type.ReferenceType(__name__, 'LoadBalancers.UpdateSpec'),
        })
        update_error_dict = {
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
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespace-management/clusters/{cluster}/load-balancers/{id}',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
                'id': 'id',
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
                'output_type': type.ReferenceType(__name__, 'LoadBalancers.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'LoadBalancers.Summary')),
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
            'update': {
                'input_type': update_input_type,
                'output_type': type.VoidType(),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': update_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'list': list_rest_metadata,
            'set': set_rest_metadata,
            'update': update_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.load_balancers',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _NSXTier0GatewayStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'distributed_switch': type.IdType(resource_types='vSphereDistributedSwitch'),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.internal_server_error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InternalServerError'),
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
            url_template='/vcenter/namespace-management/nsx-tier0-gateways',
            path_variables={
            },
            query_parameters={
                'distributed_switch': 'distributed_switch',
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
                'output_type': type.ListType(type.ReferenceType(__name__, 'NSXTier0Gateway.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.NSX_tier0_gateway',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _NetworksStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.ReferenceType(__name__, 'Networks.CreateSpec'),
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
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
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
            url_template='/vcenter/namespace-management/clusters/{cluster}/networks',
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

        # properties for set operation
        set_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'network': type.IdType(resource_types='com.vmware.vcenter.namespace_management.Network'),
            'spec': type.ReferenceType(__name__, 'Networks.SetSpec'),
        })
        set_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_in_use':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInUse'),
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
            url_template='/vcenter/namespace-management/clusters/{cluster}/networks/{network}',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
                'network': 'network',
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
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'network': type.IdType(resource_types='com.vmware.vcenter.namespace_management.Network'),
            'spec': type.ReferenceType(__name__, 'Networks.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_in_use':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInUse'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespace-management/clusters/{cluster}/networks/{network}',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
                'network': 'network',
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
            'network': type.IdType(resource_types='com.vmware.vcenter.namespace_management.Network'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
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
            url_template='/vcenter/namespace-management/clusters/{cluster}/networks/{network}',
            path_variables={
                'cluster': 'cluster',
                'network': 'network',
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
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
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
            url_template='/vcenter/namespace-management/clusters/{cluster}/networks',
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

        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'network': type.IdType(resource_types='com.vmware.vcenter.namespace_management.Network'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_in_use':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInUse'),
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
            url_template='/vcenter/namespace-management/clusters/{cluster}/networks/{network}',
            path_variables={
                'cluster': 'cluster',
                'network': 'network',
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
            'set': {
                'input_type': set_input_type,
                'output_type': type.VoidType(),
                'errors': set_error_dict,
                'input_value_validator_list': set_input_value_validator_list,
                'output_validator_list': set_output_validator_list,
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
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Networks.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'Networks.Info')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
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
            'set': set_rest_metadata,
            'update': update_rest_metadata,
            'get': get_rest_metadata,
            'list': list_rest_metadata,
            'delete': delete_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.networks',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _SupervisorServicesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for check_content operation
        check_content_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'SupervisorServices.ContentCheckSpec'),
        })
        check_content_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        check_content_input_value_validator_list = [
        ]
        check_content_output_validator_list = [
        ]
        check_content_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/supervisor-services',
            path_variables={
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'checkContent',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'SupervisorServices.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
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
            url_template='/vcenter/namespace-management/supervisor-services',
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

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
            'spec': type.ReferenceType(__name__, 'SupervisorServices.UpdateSpec'),
        })
        update_error_dict = {
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

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespace-management/supervisor-services/{supervisorService}',
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
            url_template='/vcenter/namespace-management/supervisor-services/{supervisorService}',
            path_variables={
                'supervisor_service': 'supervisorService',
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
            url_template='/vcenter/namespace-management/supervisor-services/{supervisorService}',
            path_variables={
                'supervisor_service': 'supervisorService',
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
            url_template='/vcenter/namespace-management/supervisor-services',
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
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
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
            url_template='/vcenter/namespace-management/supervisor-services/{supervisorService}',
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

        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'supervisor_service': type.IdType(resource_types='com.vmware.vcenter.namespace_management.SupervisorService'),
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
            url_template='/vcenter/namespace-management/supervisor-services/{supervisorService}',
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

        operations = {
            'check_content': {
                'input_type': check_content_input_type,
                'output_type': type.ReferenceType(__name__, 'SupervisorServices.CheckResult'),
                'errors': check_content_error_dict,
                'input_value_validator_list': check_content_input_value_validator_list,
                'output_validator_list': check_content_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'create': {
                'input_type': create_input_type,
                'output_type': type.VoidType(),
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
                'output_type': type.ListType(type.ReferenceType(__name__, 'SupervisorServices.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'SupervisorServices.Info'),
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
            'check_content': check_content_rest_metadata,
            'create': create_rest_metadata,
            'update': update_rest_metadata,
            'deactivate': deactivate_rest_metadata,
            'activate': activate_rest_metadata,
            'list': list_rest_metadata,
            'get': get_rest_metadata,
            'delete': delete_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.supervisor_services',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _SupervisorsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for enable_on_zones operation
        enable_on_zones_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Supervisors.EnableOnZonesSpec'),
        })
        enable_on_zones_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unable_to_allocate_resource':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnableToAllocateResource'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        enable_on_zones_input_value_validator_list = [
        ]
        enable_on_zones_output_validator_list = [
        ]
        enable_on_zones_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/supervisors',
            request_body_parameter='spec',
            path_variables={
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'enable_on_zones',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for enable_on_compute_cluster operation
        enable_on_compute_cluster_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.ReferenceType(__name__, 'Supervisors.EnableOnComputeClusterSpec'),
        })
        enable_on_compute_cluster_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unable_to_allocate_resource':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnableToAllocateResource'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        enable_on_compute_cluster_input_value_validator_list = [
        ]
        enable_on_compute_cluster_output_validator_list = [
        ]
        enable_on_compute_cluster_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/supervisors/{cluster}',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'enable_on_compute_cluster',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'enable_on_zones': {
                'input_type': enable_on_zones_input_type,
                'output_type': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
                'errors': enable_on_zones_error_dict,
                'input_value_validator_list': enable_on_zones_input_value_validator_list,
                'output_validator_list': enable_on_zones_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'enable_on_compute_cluster': {
                'input_type': enable_on_compute_cluster_input_type,
                'output_type': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
                'errors': enable_on_compute_cluster_error_dict,
                'input_value_validator_list': enable_on_compute_cluster_input_value_validator_list,
                'output_validator_list': enable_on_compute_cluster_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'enable_on_zones': enable_on_zones_rest_metadata,
            'enable_on_compute_cluster': enable_on_compute_cluster_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.supervisors',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _VirtualMachineClassesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'VirtualMachineClasses.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
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
            url_template='/vcenter/namespace-management/virtual-machine-classes',
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

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'vm_class': type.IdType(resource_types='com.vmware.vcenter.namespace_management.VirtualMachineClass'),
            'spec': type.ReferenceType(__name__, 'VirtualMachineClasses.UpdateSpec'),
        })
        update_error_dict = {
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

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespace-management/virtual-machine-classes/{vm_class}',
            request_body_parameter='spec',
            path_variables={
                'vm_class': 'vm_class',
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
            'vm_class': type.IdType(resource_types='com.vmware.vcenter.namespace_management.VirtualMachineClass'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
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
            url_template='/vcenter/namespace-management/virtual-machine-classes/{vm_class}',
            path_variables={
                'vm_class': 'vm_class',
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
            url_template='/vcenter/namespace-management/virtual-machine-classes',
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

        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'vm_class': type.IdType(resource_types='com.vmware.vcenter.namespace_management.VirtualMachineClass'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.resource_in_use':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInUse'),
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
            url_template='/vcenter/namespace-management/virtual-machine-classes/{vm_class}',
            path_variables={
                'vm_class': 'vm_class',
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
                'output_type': type.ReferenceType(__name__, 'VirtualMachineClasses.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'VirtualMachineClasses.Info')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
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
            'update': update_rest_metadata,
            'get': get_rest_metadata,
            'list': list_rest_metadata,
            'delete': delete_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.virtual_machine_classes',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _ClusterAvailableVersionsStub(ApiInterfaceStub):
    def __init__(self, config):
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
            url_template='/vcenter/namespace-management/software/cluster-available-versions',
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
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'ClusterAvailableVersions.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.cluster_available_versions',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _ClusterCompatibilityStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'filter': type.OptionalType(type.ReferenceType(__name__, 'ClusterCompatibility.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
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
            url_template='/vcenter/namespace-management/cluster-compatibility',
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

        # properties for list_v2 operation
        list_v2_input_type = type.StructType('operation-input', {
            'zone_filter': type.OptionalType(type.ReferenceType(__name__, 'ClusterCompatibility.ZoneFilterSpec')),
            'cluster_filter': type.OptionalType(type.ReferenceType(__name__, 'ClusterCompatibility.FilterSpecV2')),
        })
        list_v2_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        list_v2_input_value_validator_list = [
        ]
        list_v2_output_validator_list = [
        ]
        list_v2_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespace-management/cluster-compatibility/v2',
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
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'ClusterCompatibility.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list_v2': {
                'input_type': list_v2_input_type,
                'output_type': type.ReferenceType(__name__, 'ClusterCompatibility.ZoneCompatibilityInfo'),
                'errors': list_v2_error_dict,
                'input_value_validator_list': list_v2_input_value_validator_list,
                'output_validator_list': list_v2_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
            'list_v2': list_v2_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.cluster_compatibility',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _ClusterSizeInfoStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {})
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespace-management/cluster-size-info',
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
                'output_type': type.MapType(type.ReferenceType(__name__, 'SizingHint'), type.ReferenceType(__name__, 'ClusterSizeInfo.Info')),
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
            self, iface_name='com.vmware.vcenter.namespace_management.cluster_size_info',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _DistributedSwitchCompatibilityStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'filter': type.OptionalType(type.ReferenceType(__name__, 'DistributedSwitchCompatibility.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.internal_server_error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InternalServerError'),
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
            url_template='/vcenter/namespace-management/distributed-switch-compatibility',
            path_variables={
            },
            query_parameters={
                'cluster': 'cluster',
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
                'output_type': type.ListType(type.ReferenceType(__name__, 'DistributedSwitchCompatibility.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.distributed_switch_compatibility',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _EdgeClusterCompatibilityStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'distributed_switch': type.IdType(resource_types='vSphereDistributedSwitch'),
            'filter': type.OptionalType(type.ReferenceType(__name__, 'EdgeClusterCompatibility.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.internal_server_error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InternalServerError'),
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
            url_template='/vcenter/namespace-management/edge-cluster-compatibility',
            path_variables={
            },
            query_parameters={
                'cluster': 'cluster',
                'distributed_switch': 'distributed_switch',
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
                'output_type': type.ListType(type.ReferenceType(__name__, 'EdgeClusterCompatibility.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.edge_cluster_compatibility',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _SupportBundleStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
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
            url_template='/vcenter/namespace-management/clusters/{cluster}/support-bundle',
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

        operations = {
            'create': {
                'input_type': create_input_type,
                'output_type': type.ReferenceType(__name__, 'SupportBundle.Location'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'create': create_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.support_bundle',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _NamespaceResourceOptionsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
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
            url_template='/vcenter/namespace-management/clusters/{cluster}/workload-resource-options',
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

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'NamespaceResourceOptions.Info'),
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
            self, iface_name='com.vmware.vcenter.namespace_management.namespace_resource_options',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Clusters': Clusters,
        'HostsConfig': HostsConfig,
        'LoadBalancers': LoadBalancers,
        'NSXTier0Gateway': NSXTier0Gateway,
        'Networks': Networks,
        'SupervisorServices': SupervisorServices,
        'Supervisors': Supervisors,
        'VirtualMachineClasses': VirtualMachineClasses,
        'ClusterAvailableVersions': ClusterAvailableVersions,
        'ClusterCompatibility': ClusterCompatibility,
        'ClusterSizeInfo': ClusterSizeInfo,
        'DistributedSwitchCompatibility': DistributedSwitchCompatibility,
        'EdgeClusterCompatibility': EdgeClusterCompatibility,
        'SupportBundle': SupportBundle,
        'NamespaceResourceOptions': NamespaceResourceOptions,
        'clusters': 'com.vmware.vcenter.namespace_management.clusters_client.StubFactory',
        'cns': 'com.vmware.vcenter.namespace_management.cns_client.StubFactory',
        'networks': 'com.vmware.vcenter.namespace_management.networks_client.StubFactory',
        'software': 'com.vmware.vcenter.namespace_management.software_client.StubFactory',
        'stats': 'com.vmware.vcenter.namespace_management.stats_client.StubFactory',
        'storage': 'com.vmware.vcenter.namespace_management.storage_client.StubFactory',
        'supervisor_services': 'com.vmware.vcenter.namespace_management.supervisor_services_client.StubFactory',
        'supervisors': 'com.vmware.vcenter.namespace_management.supervisors_client.StubFactory',
    }

