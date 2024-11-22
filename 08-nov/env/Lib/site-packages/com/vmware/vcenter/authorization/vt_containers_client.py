# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.authorization.vt_containers.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.authorization.vt_containers_client`` module provides
classes for managing vTContainers.

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


class Mappings(VapiInterface):
    """
    The ``Mappings`` class can be used to manage the relationship between
    containerized objects and vTContainer instances. A containerized object is
    any data object that is associated with a vTContainer instance, and can be
    of any resource type. 
    
    Each vTContainer instance can hold any number of containerized objects, but
    there is a service defined limit to the number of vTContainer instances
    that can be associated with a single containerized object. 
    
    When a containerized object is deleted, its mappings to vTContainer
    instances are automatically removed. However, a vTContainer instance cannot
    be deleted until all mappings to it have been removed.. This class was
    added in vSphere API 8.0.3.0.
    """
    RESOURCE_TYPE = "com.vmware.vcenter.authorization.vt_containers.Mapping"
    """
    The resource type for vTContainer mappings. This class attribute was added in
    vSphere API 8.0.3.0.

    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.authorization.vt_containers.mappings'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _MappingsStub)
        self._VAPI_OPERATION_IDS = {}

    class Info(VapiStruct):
        """
        The ``Mappings.Info`` class contains all of the information about a
        containerized object mapping. This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     vtcontainer=None,
                     object=None,
                    ):
            """
            :type  vtcontainer: :class:`str`
            :param vtcontainer: Identifier of the vTContainer instance. This attribute was added in
                vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.authorization.VtContainer``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.authorization.VtContainer``.
            :type  object: :class:`com.vmware.vapi.std_client.DynamicID`
            :param object: Identifier of the containerized object. This attribute was added in
                vSphere API 8.0.3.0.
            """
            self.vtcontainer = vtcontainer
            self.object = object
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.authorization.vt_containers.mappings.info', {
            'vtcontainer': type.IdType(resource_types='com.vmware.vcenter.authorization.VtContainer'),
            'object': type.ReferenceType('com.vmware.vapi.std_client', 'DynamicID'),
        },
        Info,
        False,
        None))


    class ListItem(VapiStruct):
        """
        The ``Mappings.ListItem`` class contains all of the information about a
        containerized object mapping returned by the :func:`Mappings.list` method.
        This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     mapping=None,
                     info=None,
                    ):
            """
            :type  mapping: :class:`str`
            :param mapping: Identifier of the vTContainer mapping. This attribute was added in
                vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.authorization.vt_containers.Mapping``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.authorization.vt_containers.Mapping``.
            :type  info: :class:`Mappings.Info`
            :param info: Information about the vTContainer mapping. This attribute was added
                in vSphere API 8.0.3.0.
            """
            self.mapping = mapping
            self.info = info
            VapiStruct.__init__(self)


    ListItem._set_binding_type(type.StructType(
        'com.vmware.vcenter.authorization.vt_containers.mappings.list_item', {
            'mapping': type.IdType(resource_types='com.vmware.vcenter.authorization.vt_containers.Mapping'),
            'info': type.ReferenceType(__name__, 'Mappings.Info'),
        },
        ListItem,
        False,
        None))


    class ListResult(VapiStruct):
        """
        The ``Mappings.ListResult`` class represents the result of the
        :func:`Mappings.list` method. This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     items=None,
                     marker=None,
                    ):
            """
            :type  items: :class:`list` of :class:`Mappings.ListItem`
            :param items: List of vTContainer mappings. This attribute was added in vSphere
                API 8.0.3.0.
            :type  marker: :class:`str` or ``None``
            :param marker: An opaque string in support of pagination which indicates that more
                items are available. The marker can be used in subsequent calls to
                the :func:`Mappings.list` method to retrieve the next set of items.
                This attribute was added in vSphere API 8.0.3.0.
                If None there are no additional items.
            """
            self.items = items
            self.marker = marker
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.authorization.vt_containers.mappings.list_result', {
            'items': type.ListType(type.ReferenceType(__name__, 'Mappings.ListItem')),
            'marker': type.OptionalType(type.StringType()),
        },
        ListResult,
        False,
        None))


    class IterationSpec(VapiStruct):
        """
        The ``Mappings.IterationSpec`` class contains attributes used to limit the
        number of items returned from the :func:`Mappings.list` method. This class
        was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     marker=None,
                     size=None,
                    ):
            """
            :type  marker: :class:`str` or ``None``
            :param marker: An opaque string in support of pagination which may be specified to
                retrieve the next set of items. The marker is obtained from the
                :class:`Mappings.ListResult` class that is returned by the
                :func:`Mappings.list` method. This attribute was added in vSphere
                API 8.0.3.0.
                If None the first set of items is returned.
            :type  size: :class:`long` or ``None``
            :param size: Maximum number of items to return in a single call. This attribute
                was added in vSphere API 8.0.3.0.
                If None defaults to a size defined by the service.
            """
            self.marker = marker
            self.size = size
            VapiStruct.__init__(self)


    IterationSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.authorization.vt_containers.mappings.iteration_spec', {
            'marker': type.OptionalType(type.StringType()),
            'size': type.OptionalType(type.IntegerType()),
        },
        IterationSpec,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``Mappings.FilterSpec`` class contains attributes used to filter the
        items returned from a :func:`Mappings.list` method. This class was added in
        vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     vtcontainers=None,
                     types=None,
                    ):
            """
            :type  vtcontainers: :class:`set` of :class:`str` or ``None``
            :param vtcontainers: A set of vTContainers. This attribute was added in vSphere API
                8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.authorization.VtContainer``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.authorization.VtContainer``.
                If None or empty, the result will not be filtered by vTContainer
                instance.
            :type  types: :class:`set` of :class:`str` or ``None``
            :param types: A set of object resource types. This attribute was added in vSphere
                API 8.0.3.0.
                If None or empty, the result will not be filtered by object
                resource type.
            """
            self.vtcontainers = vtcontainers
            self.types = types
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.authorization.vt_containers.mappings.filter_spec', {
            'vtcontainers': type.OptionalType(type.SetType(type.IdType())),
            'types': type.OptionalType(type.SetType(type.StringType())),
        },
        FilterSpec,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``Mappings.CreateSpec`` class contains the information necessary for
        associating an object with a vTContainer instance. This class was added in
        vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     vtcontainer=None,
                     object=None,
                    ):
            """
            :type  vtcontainer: :class:`str`
            :param vtcontainer: Identifier of the vTContainer instance. This attribute was added in
                vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.authorization.VtContainer``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.authorization.VtContainer``.
            :type  object: :class:`com.vmware.vapi.std_client.DynamicID`
            :param object: Identifier of the object that will be containerized. This attribute
                was added in vSphere API 8.0.3.0.
            """
            self.vtcontainer = vtcontainer
            self.object = object
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.authorization.vt_containers.mappings.create_spec', {
            'vtcontainer': type.IdType(resource_types='com.vmware.vcenter.authorization.VtContainer'),
            'object': type.ReferenceType('com.vmware.vapi.std_client', 'DynamicID'),
        },
        CreateSpec,
        False,
        None))



    def create(self,
               spec,
               ):
        """
        Creates a new mapping that associates an object with a vTContainer
        instance. This method was added in vSphere API 8.0.3.0.

        :type  spec: :class:`Mappings.CreateSpec`
        :param spec: The specification of a new mapping.
        :rtype: :class:`str`
        :return: The identifier of the new mapping.
            The return value will be an identifier for the resource type:
            ``com.vmware.vcenter.authorization.vt_containers.Mapping``.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the configuration already exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the inputs are not valid.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the limit of mappings for the specified object has been reached.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the vTContainer or the object does not exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the object type does not support containerization.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller does not have the Authorization.ModifyPermissions
            privilege on the specified object.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller does not have privilege to access objects in the
            specified vTContainer.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``Authorization.ModifyVTContainerMappings``.
        """
        return self._invoke('create',
                            {
                            'spec': spec,
                            })

    def list(self,
             filter=None,
             iterate=None,
             ):
        """
        Returns the list of mappings indicating the containerized objects and
        their associated vTContainer instances. This method was added in
        vSphere API 8.0.3.0.

        :type  filter: :class:`Mappings.FilterSpec` or ``None``
        :param filter: The specification of matching mappings to be retrieved.
            If None all mappings will be returned.
        :type  iterate: :class:`Mappings.IterationSpec` or ``None``
        :param iterate: The specification of a page to be retrieved.
            if None the first set of items will be returned.
        :rtype: :class:`Mappings.ListResult`
        :return: A list of mappings.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the inputs are not valid.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``System.Read``.
        """
        return self._invoke('list',
                            {
                            'filter': filter,
                            'iterate': iterate,
                            })

    def get(self,
            mapping,
            ):
        """
        Returns information about a single mapping indicating the containerized
        object and its associated vTContainer instance. This method was added
        in vSphere API 8.0.3.0.

        :type  mapping: :class:`str`
        :param mapping: The mapping identifier.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.authorization.vt_containers.Mapping``.
        :rtype: :class:`Mappings.Info`
        :return: The mapping information.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the mapping is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller does not have privilege to access objects in the
            vTContainer that is associated with the mapping.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``System.Read``.
        """
        return self._invoke('get',
                            {
                            'mapping': mapping,
                            })

    def delete(self,
               mapping,
               ):
        """
        Removes a mapping. The related object will no longer be associated with
        the vTContainer instance. This method was added in vSphere API 8.0.3.0.

        :type  mapping: :class:`str`
        :param mapping: The mapping identifier.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.authorization.vt_containers.Mapping``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the mapping is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller does not have the Authorization.ModifyPermissions
            privilege on the object that is associated with the mapping.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller does not have privilege to access objects in the
            vTContainer that is associated with the mapping.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``Authorization.ModifyVTContainerMappings``.
        """
        return self._invoke('delete',
                            {
                            'mapping': mapping,
                            })
class _MappingsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Mappings.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/authorization/vt-containers/mappings',
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

        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'filter': type.OptionalType(type.ReferenceType(__name__, 'Mappings.FilterSpec')),
            'iterate': type.OptionalType(type.ReferenceType(__name__, 'Mappings.IterationSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/authorization/vt-containers/mappings',
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
            'mapping': type.IdType(resource_types='com.vmware.vcenter.authorization.vt_containers.Mapping'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/authorization/vt-containers/mappings/{mapping}',
            path_variables={
                'mapping': 'mapping',
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
            'mapping': type.IdType(resource_types='com.vmware.vcenter.authorization.vt_containers.Mapping'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vcenter/authorization/vt-containers/mappings/{mapping}',
            path_variables={
                'mapping': 'mapping',
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
            'create': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.vcenter.authorization.vt_containers.Mapping'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ReferenceType(__name__, 'Mappings.ListResult'),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Mappings.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
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
            'create': create_rest_metadata,
            'list': list_rest_metadata,
            'get': get_rest_metadata,
            'delete': delete_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.authorization.vt_containers.mappings',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Mappings': Mappings,
    }

