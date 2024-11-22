# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.consumption_domains.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.consumption_domains_client`` module provides classes
for managing consumption domain capabilities offered by vCenter.

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


class Zones(VapiInterface):
    """
    The ``Zones`` class provides methods to manage consumption-domain zones.
    This class was added in vSphere API 8.0.0.1.
    """
    RESOURCE_TYPE = "com.vmware.vcenter.consumption_domains.Zone"
    """
    The resource type for consumption-domain zones. This class attribute was added
    in vSphere API 8.0.0.1.

    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.consumption_domains.zones'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ZonesStub)
        self._VAPI_OPERATION_IDS = {}

    class Info(VapiStruct):
        """
        The ``Zones.Info`` class contains commonly used information about a
        specific zone. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     description=None,
                    ):
            """
            :type  description: :class:`str`
            :param description: Description of the zone. This attribute was added in vSphere API
                8.0.0.1.
            """
            self.description = description
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.consumption_domains.zones.info', {
            'description': type.StringType(),
        },
        Info,
        False,
        None))


    class ListItem(VapiStruct):
        """
        The ``Zones.ListItem`` class contains commonly used information about a
        zone. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     zone=None,
                     info=None,
                    ):
            """
            :type  zone: :class:`str`
            :param zone: Identifier of the zone. This attribute was added in vSphere API
                8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``.
            :type  info: :class:`Zones.Info`
            :param info: Information about the zone. This attribute was added in vSphere API
                8.0.0.1.
            """
            self.zone = zone
            self.info = info
            VapiStruct.__init__(self)


    ListItem._set_binding_type(type.StructType(
        'com.vmware.vcenter.consumption_domains.zones.list_item', {
            'zone': type.IdType(resource_types='com.vmware.vcenter.consumption_domains.Zone'),
            'info': type.ReferenceType(__name__, 'Zones.Info'),
        },
        ListItem,
        False,
        None))


    class ListResult(VapiStruct):
        """
        The ``Zones.ListResult`` class contains the returned zones, see
        :func:`Zones.list`. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     items=None,
                    ):
            """
            :type  items: :class:`list` of :class:`Zones.ListItem`
            :param items: The list of zones. This attribute was added in vSphere API 8.0.0.1.
            """
            self.items = items
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.consumption_domains.zones.list_result', {
            'items': type.ListType(type.ReferenceType(__name__, 'Zones.ListItem')),
        },
        ListResult,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``Zones.FilterSpec`` class contains attributes used to filter the
        results when listing configured zones, see :func:`Zones.list`. This class
        was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     zones=None,
                    ):
            """
            :type  zones: :class:`set` of :class:`str` or ``None``
            :param zones: Matches all zones corresponding to the specified set of zone
                identifiers. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``.
                If None or empty, results will not be filtered for specific zone
                identifiers.
            """
            self.zones = zones
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.consumption_domains.zones.filter_spec', {
            'zones': type.OptionalType(type.SetType(type.IdType())),
        },
        FilterSpec,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``Zones.CreateSpec`` class contains the information required to create
        a zone. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     zone=None,
                     description=None,
                    ):
            """
            :type  zone: :class:`str`
            :param zone: Identifier of the zone. It has the following restrictions: 1. The
                ID must be 63 characters or less (cannot be empty), 2. The ID must
                begin and end with a lowercase alphanumeric character ([a-z0-9]),
                3. The ID must only contain dashes (-), and lowercase alphanumerics
                in between, 4. The ID must be unique within the vCenter in which it
                is created. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``.
            :type  description: :class:`str` or ``None``
            :param description: Description of the zone. This attribute was added in vSphere API
                8.0.0.1.
                If None or empty, an empty description is set.
            """
            self.zone = zone
            self.description = description
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.consumption_domains.zones.create_spec', {
            'zone': type.IdType(resource_types='com.vmware.vcenter.consumption_domains.Zone'),
            'description': type.OptionalType(type.StringType()),
        },
        CreateSpec,
        False,
        None))



    def list(self,
             spec=None,
             ):
        """
        Returns information about the zones available on this vCenter server,
        where the zones need to match :class:`Zones.FilterSpec`. This method
        was added in vSphere API 8.0.0.1.

        :type  spec: :class:`Zones.FilterSpec` or ``None``
        :param spec: Return only the zones matching the specified filters.
            If None, the behavior is equivalent to a :class:`Zones.FilterSpec`
            with all attributes None, which means all zones are returned.
        :rtype: :class:`Zones.ListResult`
        :return: The list of zones available on this vCenter that match the criteria
            specified in :class:`Zones.FilterSpec`.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have all of the privileges described as
            follows: - The resource com.vmware.vcenter.consumption_domains.Zone
            referenced by the parameter zones in ``Zones.FilterSpec`` requires
            System.Read privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            when unexpected error is encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``System.Read``.
        """
        return self._invoke('list',
                            {
                            'spec': spec,
                            })

    def get(self,
            zone,
            ):
        """
        Returns the information about a specific zone. This method was added in
        vSphere API 8.0.0.1.

        :type  zone: :class:`str`
        :param zone: Identifier of the zone for which information should be retrieved.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.consumption_domains.Zone``.
        :rtype: :class:`Zones.Info`
        :return: Detailed information about the specified zone.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if a zone with this identifier does not exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have all of the privileges described as
            follows: - The resource com.vmware.vcenter.consumption_domains.Zone
            referenced by the parameter zone requires System.Read privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            when unexpected error is encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``System.Read``.
        """
        return self._invoke('get',
                            {
                            'zone': zone,
                            })

    def create(self,
               spec,
               ):
        """
        Creates a zone based on the provided specifications. This method was
        added in vSphere API 8.0.0.1.

        :type  spec: :class:`Zones.CreateSpec`
        :param spec: Specifications for the zone to be created.
        :rtype: :class:`str`
        :return: The identifier of the created zone.
            The return value will be an identifier for the resource type:
            ``com.vmware.vcenter.consumption_domains.Zone``.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if a zone with the same identifier already exists in this vCenter
            server.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if any of the input information in the ``createSpec`` is invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have Zones.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            when unexpected error is encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``Zone.Manage``.
        """
        return self._invoke('create',
                            {
                            'spec': spec,
                            })

    def delete(self,
               zone,
               ):
        """
        Deletes the zone with the specified identifier. In order to delete a
        zone, there must not be any workload running in that zone because
        deleting the zone without removing all the dependencies on that zone
        can cause undefined behavior for the entities depending on this zone to
        be present. This method was added in vSphere API 8.0.0.1.

        :type  zone: :class:`str`
        :param zone: Identifier of the zone to be deleted.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.consumption_domains.Zone``.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if no zone with the specified identifier is found in this vCenter
            server.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if there is a workload running in the specified zone and depends on
            this zone to be present.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have all of the privileges described as
            follows: - The resource com.vmware.vcenter.consumption_domains.Zone
            referenced by the parameter zone requires Zones.Manage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            when unexpected error is encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``Zone.Manage``.
        """
        return self._invoke('delete',
                            {
                            'zone': zone,
                            })
class _ZonesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'spec': type.OptionalType(type.ReferenceType(__name__, 'Zones.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/consumption-domains/zones',
            path_variables={
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'zone': type.IdType(resource_types='com.vmware.vcenter.consumption_domains.Zone'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/consumption-domains/zones/{zone}',
            path_variables={
                'zone': 'zone',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Zones.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/consumption-domains/zones',
            request_body_parameter='spec',
            path_variables={
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'zone': type.IdType(resource_types='com.vmware.vcenter.consumption_domains.Zone'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vcenter/consumption-domains/zones/{zone}',
            path_variables={
                'zone': 'zone',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'list': {
                'input_type': list_input_type,
                'output_type': type.ReferenceType(__name__, 'Zones.ListResult'),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Zones.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'create': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.vcenter.consumption_domains.Zone'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'delete': {
                'input_type': delete_input_type,
                'output_type': type.VoidType(),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': delete_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
            'get': get_rest_metadata,
            'create': create_rest_metadata,
            'delete': delete_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.consumption_domains.zones',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Zones': Zones,
        'zone_associations': 'com.vmware.vcenter.consumption_domains.zone_associations_client.StubFactory',
    }

