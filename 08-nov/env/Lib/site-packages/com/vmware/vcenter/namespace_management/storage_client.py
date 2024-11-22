# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.storage.
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


class Profiles(VapiInterface):
    """
    The ``Profiles`` class provides methods to get storage profiles compatible
    with control plane VMDKs which can be used to enable a Supervisor. A
    storage profile is compatible if it results in at least one datastore in
    each of the specified zones. This class was added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.storage.profiles'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ProfilesStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``Profiles.Summary`` class contains the information about compatible
        storage profiles and represents the result of :func:`Profiles.check`
        method. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     profile=None,
                     profile_name=None,
                     compatible=None,
                     items=None,
                     incompatibility_reasons=None,
                    ):
            """
            :type  profile: :class:`str`
            :param profile: Identifier of the compatible storage profile. A storage profile is
                compatible if it results in at least one datastore in each of the
                specified zones. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
            :type  profile_name: :class:`str`
            :param profile_name: Human-readable identifier of the storage profile. This attribute
                was added in vSphere API 8.0.0.1.
            :type  compatible: :class:`bool`
            :param compatible: Compatibility of this storage profile with the specified vSphere
                Zones. This attribute was added in vSphere API 8.0.0.1.
            :type  items: :class:`list` of :class:`Profiles.Item`
            :param items: The list of ``Profiles.Item`` wich correspond to the storage
                profile. This attribute was added in vSphere API 8.0.0.1.
            :type  incompatibility_reasons: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param incompatibility_reasons: The reason for incompatibility. If empty, this profile is
                compatible with the given vSphere Zones specified in the
                :class:`Profiles.FilterSpec`. This attribute was added in vSphere
                API 8.0.0.1.
            """
            self.profile = profile
            self.profile_name = profile_name
            self.compatible = compatible
            self.items = items
            self.incompatibility_reasons = incompatibility_reasons
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.storage.profiles.summary', {
            'profile': type.IdType(resource_types='SpsStorageProfile'),
            'profile_name': type.StringType(),
            'compatible': type.BooleanType(),
            'items': type.ListType(type.ReferenceType(__name__, 'Profiles.Item')),
            'incompatibility_reasons': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        Summary,
        False,
        None))


    class Item(VapiStruct):
        """
        The ``Profiles.Item`` class contains the datastores and vSphere Zone which
        they are in. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     zone=None,
                     datastores=None,
                    ):
            """
            :type  zone: :class:`str`
            :param zone: The vSphere Zones the datastore are in. This attribute was added in
                vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``.
            :type  datastores: :class:`list` of :class:`str`
            :param datastores: The datastores in the zone. This attribute was added in vSphere API
                8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``Datastore``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``Datastore``.
            """
            self.zone = zone
            self.datastores = datastores
            VapiStruct.__init__(self)


    Item._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.storage.profiles.item', {
            'zone': type.IdType(resource_types='com.vmware.vcenter.consumption_domains.Zone'),
            'datastores': type.ListType(type.IdType()),
        },
        Item,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``Profiles.FilterSpec`` class contains zones used to find compatible
        storage profiles. A storage profile is compatible if it results in at least
        one datastore in each of the specified zones. (see :func:`Profiles.check`).
        This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     zones=None,
                    ):
            """
            :type  zones: :class:`list` of :class:`str`
            :param zones: Zone compatibility criteria. The common storage profiles across the
                given zones will be returned. A storage profile is considered
                compatible if it results in at least one datastore in each of the
                given zones. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``.
            """
            self.zones = zones
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.storage.profiles.filter_spec', {
            'zones': type.ListType(type.IdType()),
        },
        FilterSpec,
        False,
        None))



    def check(self,
              filter,
              ):
        """
        Returns the compatible management storage profiles for enabling a WCP
        Supervisor across a given set of zones. A storage profile is compatible
        if it results in at least one datastore in each of the specified zones.
        This method was added in vSphere API 8.0.0.1.

        :type  filter: :class:`Profiles.FilterSpec`
        :param filter: Specification of the zones to consider when finding compatible
            storage profiles. The :class:`Profiles.FilterSpec` must contain at
            least 1 zone.
        :rtype: :class:`list` of :class:`Profiles.Summary`
        :return: List of storage profiles compatible across the given
            :class:`Profiles.FilterSpec`. The profiles returned will each
            result in at least one datastore in each zone.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if one or more fields of the :class:`Profiles.FilterSpec` is
            incorrect.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege on all of the
            Cluster Compute Resources in the specified vSphere Zones.
        """
        return self._invoke('check',
                            {
                            'filter': filter,
                            })
class _ProfilesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for check operation
        check_input_type = type.StructType('operation-input', {
            'filter': type.ReferenceType(__name__, 'Profiles.FilterSpec'),
        })
        check_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        check_input_value_validator_list = [
        ]
        check_output_validator_list = [
        ]
        check_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/storage/profiles',
            request_body_parameter='filter',
            path_variables={
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'check_compatibility',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'check': {
                'input_type': check_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'Profiles.Summary')),
                'errors': check_error_dict,
                'input_value_validator_list': check_input_value_validator_list,
                'output_validator_list': check_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'check': check_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.storage.profiles',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Profiles': Profiles,
    }

