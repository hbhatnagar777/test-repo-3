# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.networks.nsx.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.namespace_management.networks.nsx_client`` module
provides classes and classes for managing nsx resources.

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


class DistributedSwitches(VapiInterface):
    """
    The ``DistributedSwitches`` class provides methods to get the basic
    information of Distributed Switches. This class was added in vSphere API
    8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.networks.nsx.distributed_switches'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _DistributedSwitchesStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``DistributedSwitches.Summary`` class contains the basic information
        about a Distributed Switch. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     distributed_switch=None,
                     name=None,
                    ):
            """
            :type  distributed_switch: :class:`str`
            :param distributed_switch: Identifier of the switch. The value of this field refers to the
                UUID of a vim.DistributedVirtualSwitch. This attribute was added in
                vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``vSphereDistributedSwitch``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``vSphereDistributedSwitch``.
            :type  name: :class:`str`
            :param name: Human-readable identifier of the switch. This attribute was added
                in vSphere API 8.0.0.1.
            """
            self.distributed_switch = distributed_switch
            self.name = name
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.nsx.distributed_switches.summary', {
            'distributed_switch': type.IdType(resource_types='vSphereDistributedSwitch'),
            'name': type.StringType(),
        },
        Summary,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``DistributedSwitches.FilterSpec`` class contains attributes used to
        filter the results when listing Distributed Switches (see
        :func:`DistributedSwitches.list`). This class was added in vSphere API
        8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     compatible=None,
                     zones=None,
                    ):
            """
            :type  compatible: :class:`bool` or ``None``
            :param compatible: Compatibility criteria. If true, only Distributed Switches
                compatible with the vSphere Namespaces will be returned. If false,
                only Distributed Switches incompatible with the vSphere Namespaces
                will be returned. This attribute was added in vSphere API 8.0.0.1.
                If None, both compatible and incompatible Distributed Switches will
                be returned.
            :type  zones: :class:`list` of :class:`str`
            :param zones: Zone compatibility criteria. If zones are specified, the common
                distributed switches across the given zones will returned. A
                distributed switch is considered common if it is present in all of
                the vSphere clusters in a given zone. This attribute was added in
                vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``.
            """
            self.compatible = compatible
            self.zones = zones
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.nsx.distributed_switches.filter_spec', {
            'compatible': type.OptionalType(type.BooleanType()),
            'zones': type.ListType(type.IdType()),
        },
        FilterSpec,
        False,
        None))



    def list(self,
             filter=None,
             ):
        """
        Returns basic information of the Distributed Switches matching the
        :class:`DistributedSwitches.FilterSpec`. This method was added in
        vSphere API 8.0.0.1.

        :type  filter: :class:`DistributedSwitches.FilterSpec` or ``None``
        :param filter: Specification of matching Distributed Switches for which
            information should be returned.
            If None, the behavior is equivalent to a
            :class:`DistributedSwitches.FilterSpec` with all attributes None
            which means all Distributed Switches will be returned.
        :rtype: :class:`list` of :class:`DistributedSwitches.Summary`
        :return: List of Distributed Switches summaries matching the
            :class:`DistributedSwitches.FilterSpec`.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if one or more fields of the
            :class:`DistributedSwitches.FilterSpec` is incorrect.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list',
                            {
                            'filter': filter,
                            })
class Edges(VapiInterface):
    """
    The ``Edges`` class provides methods to retrieve the basic information for
    NSX Edges. This class was added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.networks.nsx.edges'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _EdgesStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``Edges.Summary`` class contains the basic information about an Edge.
        This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     edge_cluster=None,
                     name=None,
                     path=None,
                    ):
            """
            :type  edge_cluster: :class:`str`
            :param edge_cluster: Identifier of the Edge. This attribute was added in vSphere API
                8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``NSXEdgeCluster``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``NSXEdgeCluster``.
            :type  name: :class:`str`
            :param name: Human-readable identifier of the Edge. This attribute was added in
                vSphere API 8.0.0.1.
            :type  path: :class:`str`
            :param path: NSX Policy path of the Edge. This attribute was added in vSphere
                API 8.0.0.1.
            """
            self.edge_cluster = edge_cluster
            self.name = name
            self.path = path
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.nsx.edges.summary', {
            'edge_cluster': type.IdType(resource_types='NSXEdgeCluster'),
            'name': type.StringType(),
            'path': type.StringType(),
        },
        Summary,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``Edges.FilterSpec`` class contains attributes used to filter the
        results when listing Edges (see :func:`Edges.list`). This class was added
        in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     compatible=None,
                     distributed_switch=None,
                    ):
            """
            :type  compatible: :class:`bool` or ``None``
            :param compatible: Compatibility criteria. If true, only Edges which are compatible
                with vSphere Namespaces will be returned. If false, only Edges
                incompatible with vSphere Namespaces will be returned. This
                attribute was added in vSphere API 8.0.0.1.
                If None, both compatible and incompatible Edges will be returned.
            :type  distributed_switch: :class:`list` of :class:`str`
            :param distributed_switch: Distributed switch UUID criteria. If distributed switches
                identifiers are specified, they will be used to filter the Edges.
                To obtain the available distributed switch UUIDs, use:
                :func:`DistributedSwitches.list`. This attribute was added in
                vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``vSphereDistributedSwitch``. When methods return a value of this
                class as a return value, the attribute will contain identifiers for
                the resource type: ``vSphereDistributedSwitch``.
            """
            self.compatible = compatible
            self.distributed_switch = distributed_switch
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.nsx.edges.filter_spec', {
            'compatible': type.OptionalType(type.BooleanType()),
            'distributed_switch': type.ListType(type.IdType()),
        },
        FilterSpec,
        False,
        None))



    def list(self,
             filter=None,
             ):
        """
        Returns a list of Edges matching the given filter. This method was
        added in vSphere API 8.0.0.1.

        :type  filter: :class:`Edges.FilterSpec` or ``None``
        :param filter: Specification of matching Edges for which information should be
            returned.
            If None, the behavior is equivalent to a :class:`Edges.FilterSpec`
            with all attributes None which means all Edges will be returned.
        :rtype: :class:`list` of :class:`Edges.Summary`
        :return: List of Edge summaries matching the given filter.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if one or more fields of the :class:`Edges.FilterSpec` is
            incorrect.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have ``System.Read`` privilege.
        """
        return self._invoke('list',
                            {
                            'filter': filter,
                            })
class _DistributedSwitchesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'filter': type.OptionalType(type.ReferenceType(__name__, 'DistributedSwitches.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespace-management/networks/nsx/distributed-switches',
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

        operations = {
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'DistributedSwitches.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.networks.nsx.distributed_switches',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _EdgesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'filter': type.OptionalType(type.ReferenceType(__name__, 'Edges.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespace-management/networks/nsx/edges',
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

        operations = {
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'Edges.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.networks.nsx.edges',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'DistributedSwitches': DistributedSwitches,
        'Edges': Edges,
        'distributed_switches': 'com.vmware.vcenter.namespace_management.networks.nsx.distributed_switches_client.StubFactory',
        'edges': 'com.vmware.vcenter.namespace_management.networks.nsx.edges_client.StubFactory',
    }

