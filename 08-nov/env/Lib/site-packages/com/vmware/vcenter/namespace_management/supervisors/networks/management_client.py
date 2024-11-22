# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.supervisors.networks.management.
#---------------------------------------------------------------------------

"""
The
``com.vmware.vcenter.namespace_management.supervisors.networks.management_client``
module provides classes for Supervisor management network configuration.

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

class NetworkBackingEnum(Enum):
    """
    ``NetworkBackingEnum`` enumerates types of network backings supported by
    the Supervisor for the management network. This enumeration was added in
    vSphere API 8.0.0.1.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    NETWORK = None
    """
    Indicates a virtual infrastructure management Network. It may include items
    like opaque networks or Distributed Virtual Port Groups. This field is
    deprecated, use :attr:`NetworkBackingEnum.NETWORK_SEGMENT` instead.. This
    class attribute was added in vSphere API 8.0.0.1.

    .. deprecated:: vSphere API 8.0.3.0

    """
    NETWORK_SEGMENT = None
    """
    Indicates a virtual infrastructure management Network Segment. The Network
    Segment can be backed by either a single Port Group or a set of Port Groups
    in the same layer 2 broadcast domain. From this set of one or more Port
    Groups, at least one Port Group must be available on each vSphere Zone and
    its associated vSphere clusters that Supervisor control plane is configured
    to be enabled on. This class attribute was added in vSphere API 8.0.3.0.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`NetworkBackingEnum` instance.
        """
        Enum.__init__(string)

NetworkBackingEnum._set_values({
    'NETWORK': NetworkBackingEnum('NETWORK'),
    'NETWORK_SEGMENT': NetworkBackingEnum('NETWORK_SEGMENT'),
})
NetworkBackingEnum._set_binding_type(type.EnumType(
    'com.vmware.vcenter.namespace_management.supervisors.networks.management.network_backing_enum',
    NetworkBackingEnum))



class ProxySettingsSource(Enum):
    """
    
    
    The settings can be inherited from the vCenter settings, so the Supervisor
    settings will be synced. The settings can be applied directly on the
    Supervisor level, or the Supervisor can be configured not to use a proxy..
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
    VC_INHERITED = None
    """
    
    
    Proxy settings will be inherited from the vCenter settings. vCenter and
    Supervisor settings will be kept in sync.. This class attribute was added
    in vSphere API 8.0.0.1.

    """
    CLUSTER_CONFIGURED = None
    """
    Proxy settings will be configured at the Supervisor level. This class
    attribute was added in vSphere API 8.0.0.1.

    """
    NONE = None
    """
    No proxy settings will be applied to the Supervisor. This class attribute
    was added in vSphere API 8.0.0.1.

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
    'com.vmware.vcenter.namespace_management.supervisors.networks.management.proxy_settings_source',
    ProxySettingsSource))




class Network(VapiStruct):
    """
    
    
    ``Network`` class represents configuration for a network used to manage the
    Supervisor control plane. vCenter and, if used, NSX Manager and/or external
    Load Balancers, etc. should be reachable on this network.. This class was
    added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'floating_IP_address': 'floating_ip_address',
                            }

    def __init__(self,
                 network=None,
                 backing=None,
                 services=None,
                 ip_management=None,
                 floating_ip_address=None,
                 proxy=None,
                ):
        """
        :type  network: :class:`str` or ``None``
        :param network: 
            
            :attr:`Network.network` is a unique identifier for this network
            which can be referenced later for updates or queries.. This
            attribute was added in vSphere API 8.0.0.1.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.Network``. When methods
            return a value of this class as a return value, the attribute will
            be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.Network``.
            If unset, an ID will be generated.
        :type  backing: :class:`NetworkBacking`
        :param backing: 
            
            :attr:`Network.backing` specifies the network backing to use as the
            uplink to the management network.. This attribute was added in
            vSphere API 8.0.0.1.
        :type  services: :class:`com.vmware.vcenter.namespace_management.networks_client.Services` or ``None``
        :param services: 
            
            :attr:`Network.services` specifies which network services are
            configured on this network. These network services are expected to
            be accessible via the associated distributed virtual port group or
            distributed virtual switch.. This attribute was added in vSphere
            API 8.0.0.1.
            If unset, network services may be automatically configured. If you
            want to disable any configuration of network services, explicitly
            set this class to empty.
        :type  ip_management: :class:`com.vmware.vcenter.namespace_management.networks_client.IPManagement` or ``None``
        :param ip_management: 
            
            :attr:`Network.ip_management` describes how IP addressing is
            configured on this network.. This attribute was added in vSphere
            API 8.0.0.1.
            If unset, this network becomes a DHCP network. Your DHCP server
            must support client identifiers to successfully enable a
            Supervisor.
        :type  floating_ip_address: :class:`str` or ``None``
        :param floating_ip_address: 
            
            :attr:`Network.floating_ip_address` is an IP address that provides
            a stable endpoint to the control plane. This address if specified
            must be an unused statically allocated IP address on the management
            network.. This attribute was added in vSphere API 8.0.0.1.
            If None and the management network is a static network, this
            address should be allocated in a static IP configuration which
            occurs when
            :attr:`com.vmware.vcenter.namespace_management.networks_client.IPManagement.dhcp_enabled`
            is set to false. If None and the management network is a DHCP
            network, The Supervisor will attempt to use the DHCP server to
            allocate this address. You should ensure the DHCP server is
            configured to persist IP addresses indefinitely using client
            identifiers if this configuration is used.
        :type  proxy: :class:`ProxyConfiguration` or ``None``
        :param proxy: 
            
            Proxy configuration will be applied to the Supervisor. The proxy
            should be reachable from the management network and will be used
            for image pulling and container traffic exiting out of the
            Supervisor.. This attribute was added in vSphere API 8.0.0.1.
            If None the settings will be inherited from the vCenter settings if
            available.
        """
        self.network = network
        self.backing = backing
        self.services = services
        self.ip_management = ip_management
        self.floating_ip_address = floating_ip_address
        self.proxy = proxy
        VapiStruct.__init__(self)


Network._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.networks.management.network', {
        'network': type.OptionalType(type.IdType()),
        'backing': type.ReferenceType(__name__, 'NetworkBacking'),
        'services': type.OptionalType(type.ReferenceType('com.vmware.vcenter.namespace_management.networks_client', 'Services')),
        'ip_management': type.OptionalType(type.ReferenceType('com.vmware.vcenter.namespace_management.networks_client', 'IPManagement')),
        'floating_IP_address': type.OptionalType(type.StringType()),
        'proxy': type.OptionalType(type.ReferenceType(__name__, 'ProxyConfiguration')),
    },
    Network,
    False,
    None))



class NetworkBacking(VapiStruct):
    """
    A ``NetworkBacking`` enumerates the possible options for uplinking to a
    Supervisor management network. This class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """

    _validator_list = [
        UnionValidator(
            'backing',
            {
                'NETWORK' : [('network', True)],
                'NETWORK_SEGMENT' : [('network_segment', True)],
            }
        ),
    ]



    def __init__(self,
                 backing=None,
                 network=None,
                 network_segment=None,
                ):
        """
        :type  backing: :class:`NetworkBackingEnum`
        :param backing: Selects the backing used for a management network. This attribute
            was added in vSphere API 8.0.0.1.
        :type  network: :class:`str`
        :param network: The Managed Object ID of the Network object. This attribute was
            added in vSphere API 8.0.0.1.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type: ``Network``.
            When methods return a value of this class as a return value, the
            attribute will be an identifier for the resource type: ``Network``.
            This attribute is optional and it is only relevant when the value
            of ``backing`` is :attr:`NetworkBackingEnum.NETWORK`.
        :type  network_segment: :class:`com.vmware.vcenter.namespace_management.supervisors.networks_client.NetworkSegment`
        :param network_segment: The Backing Network Segment. This attribute was added in vSphere
            API 8.0.3.0.
            This attribute is optional and it is only relevant when the value
            of ``backing`` is :attr:`NetworkBackingEnum.NETWORK_SEGMENT`.
        """
        self.backing = backing
        self.network = network
        self.network_segment = network_segment
        VapiStruct.__init__(self)


NetworkBacking._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.networks.management.network_backing', {
        'backing': type.ReferenceType(__name__, 'NetworkBackingEnum'),
        'network': type.OptionalType(type.IdType()),
        'network_segment': type.OptionalType(type.ReferenceType('com.vmware.vcenter.namespace_management.supervisors.networks_client', 'NetworkSegment')),
    },
    NetworkBacking,
    False,
    None))



class ProxyConfiguration(VapiStruct):
    """
    
    
    The ``ProxyConfiguration`` class defines proxy configuration to be used by
    the Supervisor.. This class was added in vSphere API 8.0.0.1.

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
        :param proxy_settings_source: 
            
            The source of the proxy settings. 
            
            If :attr:`ProxySettingsSource.VC_INHERITED` or
            :attr:`ProxySettingsSource.NONE` is specified, then the other
            configuration in ``ProxyConfiguration`` will be ignored.. This
            attribute was added in vSphere API 8.0.0.1.
        :type  https_proxy_config: :class:`str` or ``None``
        :param https_proxy_config: 
            
            HTTPS proxy configuration. Examples: 
            
            * http://username:password\\\\@proxy.vmware.com:8080
            * https://proxy.vmware.com:4443
            
            
            
            This will be used if :attr:`ProxySettingsSource.CLUSTER_CONFIGURED`
            is used for the source, otherwise this will be ignored.. This
            attribute was added in vSphere API 8.0.0.1.
            If None no HTTPS proxy will be used.
        :type  http_proxy_config: :class:`str` or ``None``
        :param http_proxy_config: 
            
            HTTP proxy configuration. Examples: 
            
            * http://username:password\\\\@proxy.vmware.com:8080
            * https://proxy.vmware.com:4443
            
            
            
            This will be used if :attr:`ProxySettingsSource.CLUSTER_CONFIGURED`
            is used for the source, otherwise this will be ignored.. This
            attribute was added in vSphere API 8.0.0.1.
            If None no HTTP proxy will be used.
        :type  no_proxy_config: :class:`list` of :class:`str` or ``None``
        :param no_proxy_config: 
            
            List of addresses that should be accessed directly. 
            
            This will be used if :attr:`ProxySettingsSource.CLUSTER_CONFIGURED`
            is used for the source, otherwise this will be ignored.. This
            attribute was added in vSphere API 8.0.0.1.
            If None there won't be any excluded addresses.
        :type  tls_root_ca_bundle: :class:`str` or ``None``
        :param tls_root_ca_bundle: 
            
            Proxy TLS root CA bundle which will be used to verify the proxy's
            certificates. Every certificate in the bundle is expected to be in
            PEM format. 
            
            This will be used if :attr:`ProxySettingsSource.CLUSTER_CONFIGURED`
            is used for the source, otherwise this will be ignored.. This
            attribute was added in vSphere API 8.0.0.1.
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
    'com.vmware.vcenter.namespace_management.supervisors.networks.management.proxy_configuration', {
        'proxy_settings_source': type.ReferenceType(__name__, 'ProxySettingsSource'),
        'https_proxy_config': type.OptionalType(type.StringType()),
        'http_proxy_config': type.OptionalType(type.StringType()),
        'no_proxy_config': type.OptionalType(type.ListType(type.StringType())),
        'tls_root_ca_bundle': type.OptionalType(type.StringType()),
    },
    ProxyConfiguration,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

