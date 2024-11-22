# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.supervisors.networks.workload.
#---------------------------------------------------------------------------

"""
The
``com.vmware.vcenter.namespace_management.supervisors.networks.workload_client``
module provides classes to configure workload network of a Supervisor.

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

class NetworkType(Enum):
    """
    
    
    ``NetworkType`` enumerates types of networks supported by the Supervisor
    for workloads.. This enumeration was added in vSphere API 8.0.0.1.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    NSXT = None
    """
    
    
    Indicates an NSX-T backed network.. This class attribute was added in
    vSphere API 8.0.0.1.

    """
    VSPHERE = None
    """
    
    
    Indicates vSphere Networking.. This class attribute was added in vSphere
    API 8.0.0.1.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`NetworkType` instance.
        """
        Enum.__init__(string)

NetworkType._set_values({
    'NSXT': NetworkType('NSXT'),
    'VSPHERE': NetworkType('VSPHERE'),
})
NetworkType._set_binding_type(type.EnumType(
    'com.vmware.vcenter.namespace_management.supervisors.networks.workload.network_type',
    NetworkType))




class Network(VapiStruct):
    """
    
    
    ``Network`` class represents configuration for a network running workloads
    on a Supervisor.. This class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """

    _validator_list = [
        UnionValidator(
            'network_type',
            {
                'NSXT' : [('nsx', True)],
                'VSPHERE' : [('vsphere', True)],
            }
        ),
    ]



    def __init__(self,
                 network=None,
                 network_type=None,
                 nsx=None,
                 vsphere=None,
                 services=None,
                 ip_management=None,
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
        :type  network_type: :class:`NetworkType`
        :param network_type: 
            
            :attr:`Network.network_type` describes the type of network.. This
            attribute was added in vSphere API 8.0.0.1.
        :type  nsx: :class:`NsxNetwork`
        :param nsx: 
            
            :attr:`Network.nsx` specifies network configuration that is
            specific to NSX-T networks.. This attribute was added in vSphere
            API 8.0.0.1.
            This attribute is optional and it is only relevant when the value
            of ``networkType`` is :attr:`NetworkType.NSXT`.
        :type  vsphere: :class:`VSphereNetwork`
        :param vsphere: 
            
            :attr:`Network.vsphere` specifies network configuration that is
            specific to vSphere networks.. This attribute was added in vSphere
            API 8.0.0.1.
            This attribute is optional and it is only relevant when the value
            of ``networkType`` is :attr:`NetworkType.VSPHERE`.
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
        """
        self.network = network
        self.network_type = network_type
        self.nsx = nsx
        self.vsphere = vsphere
        self.services = services
        self.ip_management = ip_management
        VapiStruct.__init__(self)


Network._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.networks.workload.network', {
        'network': type.OptionalType(type.IdType()),
        'network_type': type.ReferenceType(__name__, 'NetworkType'),
        'nsx': type.OptionalType(type.ReferenceType(__name__, 'NsxNetwork')),
        'vsphere': type.OptionalType(type.ReferenceType(__name__, 'VSphereNetwork')),
        'services': type.OptionalType(type.ReferenceType('com.vmware.vcenter.namespace_management.networks_client', 'Services')),
        'ip_management': type.OptionalType(type.ReferenceType('com.vmware.vcenter.namespace_management.networks_client', 'IPManagement')),
    },
    Network,
    False,
    None))



class NsxNetwork(VapiStruct):
    """
    
    
    ``NsxNetwork`` specifies network backing configuration that is specific to
    the workload network.. This class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 dvs=None,
                 namespace_subnet_prefix=None,
                ):
        """
        :type  dvs: :class:`str`
        :param dvs: 
            
            :attr:`NsxNetwork.dvs` is the Managed Object ID of a vSphere
            Distributed Virtual Switch. You can use it to connect to an NSX-T
            Network.. This attribute was added in vSphere API 8.0.0.1.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``vSphereDistributedSwitch``. When methods return a value of this
            class as a return value, the attribute will be an identifier for
            the resource type: ``vSphereDistributedSwitch``.
        :type  namespace_subnet_prefix: :class:`long` or ``None``
        :param namespace_subnet_prefix: 
            
            :attr:`NsxNetwork.namespace_subnet_prefix` indicates the size of
            the subnet reserved for namespace segments.. This attribute was
            added in vSphere API 8.0.0.1.
            Defaults to /28.
        """
        self.dvs = dvs
        self.namespace_subnet_prefix = namespace_subnet_prefix
        VapiStruct.__init__(self)


NsxNetwork._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.networks.workload.nsx_network', {
        'dvs': type.IdType(resource_types='vSphereDistributedSwitch'),
        'namespace_subnet_prefix': type.OptionalType(type.IntegerType()),
    },
    NsxNetwork,
    False,
    None))



class VSphereNetwork(VapiStruct):
    """
    
    
    ``VSphereNetwork`` specifies workload network configuration that is
    specific to vSphere networks.. This class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 dvpg=None,
                ):
        """
        :type  dvpg: :class:`str`
        :param dvpg: 
            
            :attr:`VSphereNetwork.dvpg` is the Managed Object ID of a vSphere
            Distributed Virtual Port Group. You can use it to connect to a
            vSphere Network.. This attribute was added in vSphere API 8.0.0.1.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``vSphereDistributedPortGroup``. When methods return a value of
            this class as a return value, the attribute will be an identifier
            for the resource type: ``vSphereDistributedPortGroup``.
        """
        self.dvpg = dvpg
        VapiStruct.__init__(self)


VSphereNetwork._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.networks.workload.V_sphere_network', {
        'dvpg': type.IdType(resource_types='vSphereDistributedPortGroup'),
    },
    VSphereNetwork,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

