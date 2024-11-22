# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.appliance.vcenter.settings.v1.config.components.inventoryauthorization.
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


class InventoryAuthorization(VapiStruct):
    """
    ``InventoryAuthorization`` class contains the Spec required for
    InventoryAuthorizationPlugin configurations.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 version=None,
                 service_provider_entities=None,
                ):
        """
        :type  version: :class:`str`
        :param version: The version of the authorization model this configuration is
            applicable to.
        :type  service_provider_entities: :class:`ServiceProviderEntities` or ``None``
        :param service_provider_entities: Service provider managed entities configuration of the vCenter.
        """
        self.version = version
        self.service_provider_entities = service_provider_entities
        VapiStruct.__init__(self)


InventoryAuthorization._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.inventoryauthorization.inventory_authorization', {
        'version': type.StringType(),
        'service_provider_entities': type.OptionalType(type.ReferenceType(__name__, 'ServiceProviderEntities')),
    },
    InventoryAuthorization,
    False,
    None))



class ServiceProviderEntities(VapiStruct):
    """
    ``ServiceProviderEntities`` class contains the configuration for the
    service provider managed entities inside VCenter, together with explicit
    inventory permissions inside the container.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 entities=None,
                 permissions=None,
                ):
        """
        :type  entities: :class:`list` of :class:`str`
        :param entities: List of full paths to the service provider managed entities inside
            the vCenter.
        :type  permissions: :class:`list` of :class:`Permission`
        :param permissions: List of the inventory permissions to set inside the container.
        """
        self.entities = entities
        self.permissions = permissions
        VapiStruct.__init__(self)


ServiceProviderEntities._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.inventoryauthorization.service_provider_entities', {
        'entities': type.ListType(type.StringType()),
        'permissions': type.ListType(type.ReferenceType(__name__, 'Permission')),
    },
    ServiceProviderEntities,
    False,
    None))



class Permission(VapiStruct):
    """
    ``Permission`` class represents a single inventory permission inside a
    container.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 entity=None,
                 principal=None,
                 role_name=None,
                 propagate=None,
                ):
        """
        :type  entity: :class:`str`
        :param entity: Full path to the entity for which the permission is set. The entity
            must be either one of the service provider managed entities, or a
            child thereof.
        :type  principal: :class:`com.vmware.appliance.vcenter.settings.v1.config.components.authcommon_client.Principal`
        :param principal: The principal for which the permission is set.
        :type  role_name: :class:`str`
        :param role_name: Name of a role in vCenter.
        :type  propagate: :class:`bool`
        :param propagate: Whether this permission propagates to child objects.
        """
        self.entity = entity
        self.principal = principal
        self.role_name = role_name
        self.propagate = propagate
        VapiStruct.__init__(self)


Permission._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.inventoryauthorization.permission', {
        'entity': type.StringType(),
        'principal': type.ReferenceType('com.vmware.appliance.vcenter.settings.v1.config.components.authcommon_client', 'Principal'),
        'role_name': type.StringType(),
        'propagate': type.BooleanType(),
    },
    Permission,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

