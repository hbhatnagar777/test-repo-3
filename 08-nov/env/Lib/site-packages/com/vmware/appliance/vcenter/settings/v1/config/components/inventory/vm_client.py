# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.appliance.vcenter.settings.v1.config.components.inventory.vm.
#---------------------------------------------------------------------------

"""
The ``com.vmware.appliance.vcenter.settings.v1.config.components inventory.vm``
module provides classes to manage the ConfigManagement.

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


class VirtualMachineConfig(VapiStruct):
    """
    The ``VirtualMachineConfig`` class contains information about virtual
    machine configurations present in the cluster.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 name=None,
                 parent_path=None,
                 resource_pool=None,
                 config=None,
                 permissions=None,
                ):
        """
        :type  name: :class:`str`
        :param name: Name of the vCenter Server virtual machine configuration.
        :type  parent_path: :class:`str` or ``None``
        :param parent_path: Parent path for the virtual machine configuration.
            If None, then virtual machine placed in root folder.
        :type  resource_pool: :class:`str` or ``None``
        :param resource_pool: The identifier of current ResourcePool defining the resource
            allocation for this virtual machine.
            If None, this is a Template VM or current user session has no
            access to the resource pool.
        :type  config: :class:`ConfigInfo` or ``None``
        :param config: Configuration of the VirtualMachine.
            If None, then there is no configuration.
        :type  permissions: :class:`list` of :class:`com.vmware.appliance.vcenter.settings.v1.config.components.inventory.common_client.Permission` or ``None``
        :param permissions: Permissions defined on the virtual machine.
            If None, then no permissions defined on this inventory object.
        """
        self.name = name
        self.parent_path = parent_path
        self.resource_pool = resource_pool
        self.config = config
        self.permissions = permissions
        VapiStruct.__init__(self)


VirtualMachineConfig._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.inventory.vm.virtual_machine_config', {
        'name': type.StringType(),
        'parent_path': type.OptionalType(type.StringType()),
        'resource_pool': type.OptionalType(type.StringType()),
        'config': type.OptionalType(type.ReferenceType(__name__, 'ConfigInfo')),
        'permissions': type.OptionalType(type.ListType(type.ReferenceType('com.vmware.appliance.vcenter.settings.v1.config.components.inventory.common_client', 'Permission'))),
    },
    VirtualMachineConfig,
    False,
    None))



class ConfigInfo(VapiStruct):
    """
    The ``ConfigInfo`` class provides configuration of a VirtualMachine.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 hardware=None,
                 cpu_allocation=None,
                 memory_allocation=None,
                ):
        """
        :type  hardware: :class:`VirtualHardware`
        :param hardware: Hardware configuration of the VirtualMachine.
        :type  cpu_allocation: :class:`ResourceAllocationInfo` or ``None``
        :param cpu_allocation: Resource limits for the CPU.
        :type  memory_allocation: :class:`ResourceAllocationInfo` or ``None``
        :param memory_allocation: Resource limits for the memory.
        """
        self.hardware = hardware
        self.cpu_allocation = cpu_allocation
        self.memory_allocation = memory_allocation
        VapiStruct.__init__(self)


ConfigInfo._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.inventory.vm.config_info', {
        'hardware': type.ReferenceType(__name__, 'VirtualHardware'),
        'cpu_allocation': type.OptionalType(type.ReferenceType(__name__, 'ResourceAllocationInfo')),
        'memory_allocation': type.OptionalType(type.ReferenceType(__name__, 'ResourceAllocationInfo')),
    },
    ConfigInfo,
    False,
    None))



class VirtualHardware(VapiStruct):
    """
    The ``VirtualHardware`` class provides the virtual hardware configuration
    of a VirtualMachine.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'num_CPU': 'num_cpu',
                            'memory_MB': 'memory_mb',
                            }

    def __init__(self,
                 num_cpu=None,
                 memory_mb=None,
                ):
        """
        :type  num_cpu: :class:`long`
        :param num_cpu: Number of virtual CPUs.
        :type  memory_mb: :class:`long`
        :param memory_mb: Memory size in MB.
        """
        self.num_cpu = num_cpu
        self.memory_mb = memory_mb
        VapiStruct.__init__(self)


VirtualHardware._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.inventory.vm.virtual_hardware', {
        'num_CPU': type.IntegerType(),
        'memory_MB': type.IntegerType(),
    },
    VirtualHardware,
    False,
    None))



class ResourceAllocationInfo(VapiStruct):
    """
    The ``ResourceAllocationInfo`` class provides resource allocation of
    VirtualMachine.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 reservation=None,
                 limit=None,
                ):
        """
        :type  reservation: :class:`long` or ``None``
        :param reservation: Amount of resource that is guaranteed available. Units are MB for
            memory, MHz for CPU.
            If None, then there is no reservation.
        :type  limit: :class:`long` or ``None``
        :param limit: The utilization will not exceed this limit, even if there are
            available resources. If set to -1, then there is no fixed limit on
            resource usage (only bounded by available resources and shares).
            Units are MB for memory, MHz for CPU.
            If None, then there is no limit.
        """
        self.reservation = reservation
        self.limit = limit
        VapiStruct.__init__(self)


ResourceAllocationInfo._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.inventory.vm.resource_allocation_info', {
        'reservation': type.OptionalType(type.IntegerType()),
        'limit': type.OptionalType(type.IntegerType()),
    },
    ResourceAllocationInfo,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

