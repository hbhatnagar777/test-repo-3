# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.networks.nsx.edges.
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


class Compatibility(VapiInterface):
    """
    The ``Compatibility`` class provides methods to retrieve the basic and
    Namespaces compatibility information of Edges. This class was added in
    vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.networks.nsx.edges.compatibility'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _CompatibilityStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``Compatibility.Summary`` class contains information about an Edge,
        including whether it is compatible with the vCenter Namespaces feature and
        incompatibility reasons. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     edge_cluster=None,
                     name=None,
                     compatible=None,
                     incompatibility_reasons=None,
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
            :param name: User-friendly identifier of the Edge. This attribute was added in
                vSphere API 8.0.0.1.
            :type  compatible: :class:`bool`
            :param compatible: Compatibility of this Edge with vSphere Namespaces. This attribute
                was added in vSphere API 8.0.0.1.
            :type  incompatibility_reasons: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param incompatibility_reasons: List of reasons for incompatibility. If empty, this Edge is
                compatible. This attribute was added in vSphere API 8.0.0.1.
            """
            self.edge_cluster = edge_cluster
            self.name = name
            self.compatible = compatible
            self.incompatibility_reasons = incompatibility_reasons
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.networks.nsx.edges.compatibility.summary', {
            'edge_cluster': type.IdType(resource_types='NSXEdgeCluster'),
            'name': type.StringType(),
            'compatible': type.BooleanType(),
            'incompatibility_reasons': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        Summary,
        False,
        None))



    def check(self,
              filter=None,
              ):
        """
        Returns a list of Edges matching the given filter and their
        compatibility information. This method was added in vSphere API
        8.0.0.1.

        :type  filter: :class:`com.vmware.vcenter.namespace_management.networks.nsx_client.Edges.FilterSpec` or ``None``
        :param filter: Specification of matching Edges for which information should be
            returned.
            If None, the behavior is equivalent to a given filter with all
            attributes None which means all Edges will be returned.
        :rtype: :class:`list` of :class:`Compatibility.Summary`
        :return: List of Edge compatibility summaries matching the given filter.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if one or more fields of the given filter is incorrect.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have ``System.Read`` privilege.
        """
        return self._invoke('check',
                            {
                            'filter': filter,
                            })
class _CompatibilityStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for check operation
        check_input_type = type.StructType('operation-input', {
            'filter': type.OptionalType(type.ReferenceType('com.vmware.vcenter.namespace_management.networks.nsx_client', 'Edges.FilterSpec')),
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
            url_template='/vcenter/namespace-management/networks/nsx/edges',
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
                'output_type': type.ListType(type.ReferenceType(__name__, 'Compatibility.Summary')),
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
            self, iface_name='com.vmware.vcenter.namespace_management.networks.nsx.edges.compatibility',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Compatibility': Compatibility,
    }

