# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.appliance.vcenter.settings.v1.config.components.authcommon.
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


class Principal(VapiStruct):
    """
    ``Principal`` class represents the configuration for a Principal.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 name=None,
                 group=None,
                ):
        """
        :type  name: :class:`str`
        :param name: Principal name.
        :type  group: :class:`bool`
        :param group: Is a Group
        """
        self.name = name
        self.group = group
        VapiStruct.__init__(self)


Principal._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.authcommon.principal', {
        'name': type.StringType(),
        'group': type.BooleanType(),
    },
    Principal,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

