# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.compute.policies.capabilities.vm.placement.anti_affinity_with_vcls.
#---------------------------------------------------------------------------

"""
The
``com.vmware.vcenter.compute.policies.capabilities.vm.placement.anti_affinity_with_vcls_client``
module provides classes for anti-affinity with vSphere Cluster Services (vCLS)
VMs capability offered by vCenter.

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


class CreateSpec(VapiStruct):
    """
    The ``CreateSpec`` class contains information used to create a new
    anti-affinity with vSphere Cluster Services (vCLS) VMs policy, see
    :func:`com.vmware.vcenter.compute_client.Policies.create`. vSphere Cluster
    Services (vCLS) VMs are anti-affine with virtual machines that share the
    tag indicated by :attr:`CreateSpec.vm_tag`.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 vm_tag=None,
                 capability='com.vmware.vcenter.compute.policies.capabilities.vm.placement.anti_affinity_with_vcls',
                 name=None,
                 description=None,
                ):
        """
        :type  vm_tag: :class:`str`
        :param vm_tag: Identifier of a tag that can be associated with a virtual machine.
            vSphere Cluster Services (vCLS) VMs are anti-affine with virtual
            machines that share the tag indicated by :attr:`CreateSpec.vm_tag`.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.cis.tagging.Tag:VirtualMachine``. When methods return
            a value of this class as a return value, the attribute will be an
            identifier for the resource type:
            ``com.vmware.cis.tagging.Tag:VirtualMachine``.
        :type  capability: :class:`str`
        :param capability: Identifier of the capability this policy is based on.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.vcenter.compute.policies.Capability``. When methods
            return a value of this class as a return value, the attribute will
            be an identifier for the resource type:
            ``com.vmware.vcenter.compute.policies.Capability``.
        :type  name: :class:`str`
        :param name: Name of the policy. The name needs to be unique within this vCenter
            server.
        :type  description: :class:`str`
        :param description: Description of the policy.
        """
        self.vm_tag = vm_tag
        self._capability = capability
        self.name = name
        self.description = description
        VapiStruct.__init__(self)

    @property
    def capability(self):
        """
        Return the discriminator value
        """
        return self._capability

CreateSpec._set_binding_type(type.StructType(
    'com.vmware.vcenter.compute.policies.capabilities.vm.placement.anti_affinity_with_vcls.create_spec', {
        'vm_tag': type.IdType(resource_types='com.vmware.cis.tagging.Tag:VirtualMachine'),
        'capability': type.IdType(resource_types='com.vmware.vcenter.compute.policies.Capability'),
        'name': type.StringType(),
        'description': type.StringType(),
    },
    CreateSpec,
    False,
    None))



class Info(VapiStruct):
    """
    The ``Info`` class contains information about anti-affinity with vSphere
    Cluster Services (vCLS) VMs policy, see
    :func:`com.vmware.vcenter.compute_client.Policies.get`. vSphere Cluster
    Services (vCLS) VMs are anti-affine with virtual machines that share the
    tag indicated by :attr:`Info.vm_tag`.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 vm_tag=None,
                 name=None,
                 description=None,
                 capability='com.vmware.vcenter.compute.policies.capabilities.vm.placement.anti_affinity_with_vcls',
                ):
        """
        :type  vm_tag: :class:`str`
        :param vm_tag: Identifier of a tag that can be associated with a virtual machine.
            vSphere Cluster Services (vCLS) VMs are anti-affine with virtual
            machines that share the tag indicated by :attr:`Info.vm_tag`.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.cis.tagging.Tag:VirtualMachine``. When methods return
            a value of this class as a return value, the attribute will be an
            identifier for the resource type:
            ``com.vmware.cis.tagging.Tag:VirtualMachine``.
        :type  name: :class:`str`
        :param name: Name of the policy.
        :type  description: :class:`str`
        :param description: Description of the policy.
        :type  capability: :class:`str`
        :param capability: Identifier of the capability this policy is based on.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.vcenter.compute.policies.Capability``. When methods
            return a value of this class as a return value, the attribute will
            be an identifier for the resource type:
            ``com.vmware.vcenter.compute.policies.Capability``.
        """
        self.vm_tag = vm_tag
        self.name = name
        self.description = description
        self._capability = capability
        VapiStruct.__init__(self)

    @property
    def capability(self):
        """
        Return the discriminator value
        """
        return self._capability

Info._set_binding_type(type.StructType(
    'com.vmware.vcenter.compute.policies.capabilities.vm.placement.anti_affinity_with_vcls.info', {
        'vm_tag': type.IdType(resource_types='com.vmware.cis.tagging.Tag:VirtualMachine'),
        'name': type.StringType(),
        'description': type.StringType(),
        'capability': type.IdType(resource_types='com.vmware.vcenter.compute.policies.Capability'),
    },
    Info,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

