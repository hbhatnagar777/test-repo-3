# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.networks.service.
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


class DNS(VapiStruct):
    """
    ``DNS`` describes DNS servers and search domains for a given network. This
    class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 servers=None,
                 search_domains=None,
                ):
        """
        :type  servers: :class:`list` of :class:`str`
        :param servers: 
            
            :attr:`DNS.servers` is a list of IP addresses that clients may use
            for DNS resolution on a given network in priority order. 
            
            If empty, no DNS servers will be configured.. This attribute was
            added in vSphere API 8.0.0.1.
        :type  search_domains: :class:`list` of :class:`str`
        :param search_domains: 
            
            :attr:`DNS.search_domains` is a list of DNS search domains to be
            used on this network. 
            
            This field is useful for corporate networks or local domains that
            are not publicly resolvable. 
            
            If empty, no search domains will be configured.. This attribute was
            added in vSphere API 8.0.0.1.
        """
        self.servers = servers
        self.search_domains = search_domains
        VapiStruct.__init__(self)


DNS._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.networks.service.DNS', {
        'servers': type.ListType(type.StringType()),
        'search_domains': type.ListType(type.StringType()),
    },
    DNS,
    False,
    None))



class NTP(VapiStruct):
    """
    ``NTP`` class describes network time protocol configuration for a network.
    This class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 servers=None,
                ):
        """
        :type  servers: :class:`list` of :class:`str`
        :param servers: :attr:`NTP.servers` contains a list of servers in priority order
            that clients can use for network time protocol. This attribute was
            added in vSphere API 8.0.0.1.
        """
        self.servers = servers
        VapiStruct.__init__(self)


NTP._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.networks.service.NTP', {
        'servers': type.ListType(type.StringType()),
    },
    NTP,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

