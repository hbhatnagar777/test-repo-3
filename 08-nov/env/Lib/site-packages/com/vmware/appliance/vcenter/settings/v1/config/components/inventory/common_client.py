# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.appliance.vcenter.settings.v1.config.components.inventory.common.
#---------------------------------------------------------------------------

"""
The
``com.vmware.appliance.vcenter.settings.v1.config.components.inventory.common_client``
module provides data types to manage the vCenter Server Inventory common
configurations

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


class OptionValue(VapiStruct):
    """
    Describes the key/value pair of a configured option.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 key=None,
                 value=None,
                ):
        """
        :type  key: :class:`str` or ``None``
        :param key: The name of the option using dot notation to reflect the option's
            position in a hierarchy. For example, you might have an option
            called "Ethernet" and another option that is a child of that called
            "Connection". In this case, the key for the latter could be defined
            as "Ethernet.Connection"
        :type  value: :class:`str` or ``None``
        :param value: The value of the option. The Any data object type enables you to
            define any value for the option. Typically, however, the value of
            an option is of type String or Integer.
        """
        self.key = key
        self.value = value
        VapiStruct.__init__(self)


OptionValue._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.inventory.common.option_value', {
        'key': type.OptionalType(type.StringType()),
        'value': type.OptionalType(type.StringType()),
    },
    OptionValue,
    False,
    None))



class Permission(VapiStruct):
    """
    The Permission class contains spec to define permissions in vCenter Server.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 principal=None,
                 group=None,
                 propagate=None,
                 role_id=None,
                ):
        """
        :type  principal: :class:`str`
        :param principal: User/Group name associated with the permission.
        :type  group: :class:`bool`
        :param group: True if principal is a group.
        :type  propagate: :class:`bool`
        :param propagate: True if permission can be propagated to child entities.
        :type  role_id: :class:`long`
        :param role_id: Role associated with the permission.
        """
        self.principal = principal
        self.group = group
        self.propagate = propagate
        self.role_id = role_id
        VapiStruct.__init__(self)


Permission._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.inventory.common.permission', {
        'principal': type.StringType(),
        'group': type.BooleanType(),
        'propagate': type.BooleanType(),
        'role_id': type.IntegerType(),
    },
    Permission,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

