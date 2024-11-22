# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.supervisors.networks.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.namespace_management.supervisors.networks_client``
module provides classes for Supervisor network configuration.

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


class NetworkSegment(VapiStruct):
    """
    ``NetworkSegment`` class represents a layer 2 broadcast domain. This class
    was added in vSphere API 8.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 networks=None,
                ):
        """
        :type  networks: :class:`list` of :class:`str`
        :param networks: List of Standard Port Groups or Distributed Virtual Port Groups or
            Opaque Network identifiers that are part of the same layer 2
            broadcast domain. This attribute was added in vSphere API 8.0.3.0.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``Network``. When methods return a value of this class as a return
            value, the attribute will contain identifiers for the resource
            type: ``Network``.
        """
        self.networks = networks
        VapiStruct.__init__(self)


NetworkSegment._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespace_management.supervisors.networks.network_segment', {
        'networks': type.ListType(type.IdType()),
    },
    NetworkSegment,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
        'management': 'com.vmware.vcenter.namespace_management.supervisors.networks.management_client.StubFactory',
        'workload': 'com.vmware.vcenter.namespace_management.supervisors.networks.workload_client.StubFactory',
    }

