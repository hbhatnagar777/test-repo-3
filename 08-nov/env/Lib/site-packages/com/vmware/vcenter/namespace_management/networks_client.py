# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.networks.
#---------------------------------------------------------------------------

"""


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


class IPAssignment(VapiStruct):
    """
    ``IPAssignment`` class is used to assign IP addresses to be used for
    various functions in a Supervisor Kubernetes Cluster. This class was added
    in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 assignee=None,
                 ranges=None,
                ):
        """
        :type  assignee: :class:`IPAssignment.Assignment` or ``None``
        :param assignee: :attr:`IPAssignment.assignee` is the role assignee for the given IP
            Ranges. This attribute was added in vSphere API 8.0.0.1.
            This field defaults to ANY.
        :type  ranges: :class:`list` of :class:`IPRange`
        :param ranges: :attr:`IPAssignment.ranges` lists the available IP addresses that
            can be consumed by Supervisor to run the cluster. This attribute
            was added in vSphere API 8.0.0.1.
        """
        self.assignee = assignee
        self.ranges = ranges
        VapiStruct.__init__(self)


    class Assignment(Enum):
        """
        ``IPAssignment.Assignment`` lists the different entities that require IP
        ranges. These assignments fulfill different needs in the Kubernetes
        environment. This enumeration was added in vSphere API 8.0.0.1.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        POD = None
        """
        :attr:`IPAssignment.Assignment.POD` represents the IP address that is
        allocatable to Kubernetes Pods. This assignment is currently only
        applicable on NSX-T networks. This class attribute was added in vSphere API
        8.0.0.1.

        """
        NODE = None
        """
        :attr:`IPAssignment.Assignment.NODE` represents IP ranges that is allocated
        to nodes for both the control plane and Tanzu Kubernetes Grid Clusters.
        This assignment is currently only applicable on VDS networks. This class
        attribute was added in vSphere API 8.0.0.1.

        """
        SERVICE = None
        """
        :attr:`IPAssignment.Assignment.SERVICE` represents the IP ranges that
        Kubernetes can use for its cluster IP addresses. Cluster IPs are internal
        to the cluster, but can be exposed via edge services such as load balancer,
        ingress, and egress. This class attribute was added in vSphere API 8.0.0.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Assignment` instance.
            """
            Enum.__init__(string)

    Assignment._set_values({
        'POD': Assignment('POD'),
        'NODE': Assignment('NODE'),
        'SERVICE': Assignment('SERVICE'),
    })
    Assignment._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespace_management.networks.IP_assignment.assignment',
        Assignment))

IPAssignment._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.networks.IP_assignment', {
        'assignee': type.OptionalType(type.ReferenceType(__name__, 'IPAssignment.Assignment')),
        'ranges': type.ListType(type.ReferenceType(__name__, 'IPRange')),
    },
    IPAssignment,
    False,
    None))



class IPManagement(VapiStruct):
    """
    ``IPManagement`` class dictates IP addressing configuration for the network
    that hosts the Supervisor. This class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 dhcp_enabled=None,
                 gateway_address=None,
                 ip_assignments=None,
                ):
        """
        :type  dhcp_enabled: :class:`bool` or ``None``
        :param dhcp_enabled: :attr:`IPManagement.dhcp_enabled` If set true, configures IP
            address using the DHCP server on the broadcast domain unless the
            corresponding :attr:`IPManagement.ip_assignments` are set. This
            attribute was added in vSphere API 8.0.0.1.
            If None this field defaults to true.
        :type  gateway_address: :class:`str` or ``None``
        :param gateway_address: :attr:`IPManagement.gateway_address` is the IP address combined
            with the subnet prefix length (e.g. 192.168.1.1/24) of the default
            gateway of this network. This attribute was added in vSphere API
            8.0.0.1.
            If :attr:`IPManagement.dhcp_enabled` is not set, or this is an NSX
            network, this address must be set.
        :type  ip_assignments: :class:`list` of :class:`IPAssignment` or ``None``
        :param ip_assignments: :attr:`IPManagement.ip_assignments` are a list of roles that can be
            allocated to IP addresses. If :attr:`IPManagement.gateway_address`
            is specified, these assignments must be on the same subnet. This
            attribute was added in vSphere API 8.0.0.1.
            These assignments are optional when using DHCP.
        """
        self.dhcp_enabled = dhcp_enabled
        self.gateway_address = gateway_address
        self.ip_assignments = ip_assignments
        VapiStruct.__init__(self)


IPManagement._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.networks.IP_management', {
        'dhcp_enabled': type.OptionalType(type.BooleanType()),
        'gateway_address': type.OptionalType(type.StringType()),
        'ip_assignments': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'IPAssignment'))),
    },
    IPManagement,
    False,
    None))



class IPRange(VapiStruct):
    """
    
    
    The ``IPRange`` class is used to express a range of IP addresses. The IP
    address supported by this structure will depend on the IP version that is
    being used by Supervisor. 
    
    Currently, the Supervisor only supports IPv4.. This class was added in
    vSphere API 8.0.0.1.

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
        :param address: :attr:`IPRange.address` is the starting IP address of the
            ``IPRange``. This attribute was added in vSphere API 8.0.0.1.
        :type  count: :class:`long`
        :param count: 
            
            :attr:`IPRange.count` is number of IP addresses in the range. 
            
            For example: 
            
            A /24 subnet will have a count of 256. 
            
            A /24 subnet with a gateway address and a broadcast address will
            have a count of 254.. This attribute was added in vSphere API
            8.0.0.1.
        """
        self.address = address
        self.count = count
        VapiStruct.__init__(self)


IPRange._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.networks.IP_range', {
        'address': type.StringType(),
        'count': type.IntegerType(),
    },
    IPRange,
    False,
    None))



class Services(VapiStruct):
    """
    ``Services`` class describes services that assists applications in
    communicating on a network. This class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 dns=None,
                 ntp=None,
                ):
        """
        :type  dns: :class:`com.vmware.vcenter.namespace_management.networks.service_client.DNS` or ``None``
        :param dns: :attr:`Services.dns` describes DNS servers and search domains for a
            given network. This attribute was added in vSphere API 8.0.0.1.
            If unset, no DNS settings will be configured.
        :type  ntp: :class:`com.vmware.vcenter.namespace_management.networks.service_client.NTP` or ``None``
        :param ntp: :attr:`Services.ntp` describes NTP servers running on this network
            that networked applications can use for synchronizing time. This
            attribute was added in vSphere API 8.0.0.1.
            If unset, no NTP settings will be configured.
        """
        self.dns = dns
        self.ntp = ntp
        VapiStruct.__init__(self)


Services._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.networks.services', {
        'dns': type.OptionalType(type.ReferenceType('com.vmware.vcenter.namespace_management.networks.service_client', 'DNS')),
        'ntp': type.OptionalType(type.ReferenceType('com.vmware.vcenter.namespace_management.networks.service_client', 'NTP')),
    },
    Services,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
        'edges': 'com.vmware.vcenter.namespace_management.networks.edges_client.StubFactory',
        'nsx': 'com.vmware.vcenter.namespace_management.networks.nsx_client.StubFactory',
        'service': 'com.vmware.vcenter.namespace_management.networks.service_client.StubFactory',
    }

