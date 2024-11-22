# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.consumption_domains.zones.cluster.
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


class Associations(VapiInterface):
    """
    The ``Associations`` class provides methods to manage associations of a
    single consumption-domain zone to multiple vSphere clusters. This class was
    added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.consumption_domains.zones.cluster.associations'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _AssociationsStub)
        self._VAPI_OPERATION_IDS = {}

    class Status(VapiStruct):
        """
        The ``Associations.Status`` class contains information about the outcome of
        the method to add a set of vSphere clusters to a zone or the method to
        remove a set of vSphere clusters from a zone. It also contains information
        about the partial failures, in case the addition/removal failed for a
        subset of clusters. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     success=None,
                     failed_clusters=None,
                    ):
            """
            :type  success: :class:`bool`
            :param success: This is true if the complete method succeeded without any errors.
                Otherwise, it is false if all or some methods have failed. This
                attribute was added in vSphere API 8.0.0.1.
            :type  failed_clusters: :class:`dict` of :class:`str` and :class:`Exception`
            :param failed_clusters: Associations between the identifiers of the clusters for which the
                operation failed and the reason of the failure. This attribute was
                added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``ClusterComputeResource``. When methods return a value of
                this class as a return value, the key in the attribute
                :class:`dict` will be an identifier for the resource type:
                ``ClusterComputeResource``.
            """
            self.success = success
            self.failed_clusters = failed_clusters
            VapiStruct.__init__(self)


    Status._set_binding_type(type.StructType(
        'com.vmware.vcenter.consumption_domains.zones.cluster.associations.status', {
            'success': type.BooleanType(),
            'failed_clusters': type.MapType(type.IdType(), type.AnyErrorType()),
        },
        Status,
        False,
        None))



    def add(self,
            zone,
            clusters,
            ):
        """
        Maps a consumption-domain zone to the specified vSphere clusters. If a
        cluster or a subset of specified clusters are already members of the
        specified zone, the result is success for those clusters. This method
        supports partial success, i.e., it is possible that a subset of the
        specified clusters get successfully associated with the specified zone
        but the association fails for a subset of clusters. The returned result
        will contain the details about only those clusters for which the
        association failed. This method was added in vSphere API 8.0.0.1.

        :type  zone: :class:`str`
        :param zone: Identifier of the zone to be mapped to the specified vSphere
            clusters.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.consumption_domains.Zone``.
        :type  clusters: :class:`set` of :class:`str`
        :param clusters: Set of identifiers of vSphere clusters to which the the specified
            zone should be mapped.
            The parameter must contain identifiers for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`Associations.Status`
        :return: Status see . If the method failed, returns the reason of failures.
            There will be an error message indicating the identifier of the
            cluster for which the association failed and the reason of failure.
            The cluster identifiers that are not present in  will have been
            successfully associated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if more than one cluster or an empty set of clusters is specified.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the specified zone is not known to this vCenter server.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have all of the privileges described as
            follows: - The resource com.vmware.vcenter.consumption_domains.Zone
            referenced by the parameter zone requires Zones.Manage privilege. -
            Each resource of ClusterComputeResource referenced by the parameter
            clusters requires Zone.ObjectAttachable privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            when unexpected error is encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``com.vmware.vcenter.consumption_domains.Zone``
              referenced by the parameter ``zone`` requires ``Zone.Manage``.
        """
        return self._invoke('add',
                            {
                            'zone': zone,
                            'clusters': clusters,
                            })

    def remove(self,
               zone,
               clusters,
               ):
        """
        Removes the mapping between the specified consumption-domain zone and
        vSphere clusters. If a cluster or a subset of specified clusters are
        not members of the specified zone, then the result is a success for
        those clusters. In order to remove the mapping between a zone and a
        cluster, there must not be any workload running in that zone because
        removing the mapping between a zone and a cluster could result in
        undefined behavior for the entities depending on this mapping to be
        present. This method supports partial success, i.e., it is possible
        that the mapping gets successfully removed for a subset of the clusters
        but fails for another subset of the clusters. The returned result will
        contain the details about only those clusters for which the method
        failed. This method was added in vSphere API 8.0.0.1.

        :type  zone: :class:`str`
        :param zone: Identifier of the zone for which the mapping needs to be removed.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.consumption_domains.Zone``.
        :type  clusters: :class:`set` of :class:`str`
        :param clusters: Set of identifiers of vSphere clusters which need to be removed
            from the mapping.
            The parameter must contain identifiers for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`Associations.Status`
        :return: Status see . If the method failed, returns the reason of failures.
            There will be an error message indicating the identifier of the
            cluster for which the association removal failed and the reason of
            failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the specified zone is not known to this vCenter server.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if there is a workload running in the specified zone and depends on
            this zone's cluster associations to be present.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have all of the privileges described as
            follows: - The resource com.vmware.vcenter.consumption_domains.Zone
            referenced by the parameter zone requires Zones.Manage privilege. -
            Each resource of ClusterComputeResource referenced by the parameter
            clusters requires Zone.ObjectAttachable privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            when unexpected error is encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``com.vmware.vcenter.consumption_domains.Zone``
              referenced by the parameter ``zone`` requires ``Zone.Manage``.
        """
        return self._invoke('remove',
                            {
                            'zone': zone,
                            'clusters': clusters,
                            })

    def get(self,
            zone,
            ):
        """
        Returns identifiers of the clusters that are mapped to the specified
        consumption-domain zone. This method was added in vSphere API 8.0.0.1.

        :type  zone: :class:`str`
        :param zone: Identifier of the zone to be queried for its associated vSphere
            clusters.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.consumption_domains.Zone``.
        :rtype: :class:`set` of :class:`str`
        :return: The set of vSphere clusters mapped to the specified zone.
            The return value will contain identifiers for the resource type:
            ``ClusterComputeResource``.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the specified zone is not known to this vCenter server.
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
            
            * The resource ``com.vmware.vcenter.consumption_domains.Zone``
              referenced by the parameter ``zone`` requires ``System.Read``.
        """
        return self._invoke('get',
                            {
                            'zone': zone,
                            })
class _AssociationsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for add operation
        add_input_type = type.StructType('operation-input', {
            'zone': type.IdType(resource_types='com.vmware.vcenter.consumption_domains.Zone'),
            'clusters': type.SetType(type.IdType()),
        })
        add_error_dict = {
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        add_input_value_validator_list = [
        ]
        add_output_validator_list = [
        ]
        add_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/consumption-domains/zones/cluster/{zone}/associations',
            request_body_parameter='clusters',
            path_variables={
                'zone': 'zone',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'add',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for remove operation
        remove_input_type = type.StructType('operation-input', {
            'zone': type.IdType(resource_types='com.vmware.vcenter.consumption_domains.Zone'),
            'clusters': type.SetType(type.IdType()),
        })
        remove_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        remove_input_value_validator_list = [
        ]
        remove_output_validator_list = [
        ]
        remove_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/consumption-domains/zones/cluster/{zone}/associations',
            request_body_parameter='clusters',
            path_variables={
                'zone': 'zone',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'remove',
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
            url_template='/vcenter/consumption-domains/zones/cluster/{zone}/associations',
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
            'add': {
                'input_type': add_input_type,
                'output_type': type.ReferenceType(__name__, 'Associations.Status'),
                'errors': add_error_dict,
                'input_value_validator_list': add_input_value_validator_list,
                'output_validator_list': add_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'remove': {
                'input_type': remove_input_type,
                'output_type': type.ReferenceType(__name__, 'Associations.Status'),
                'errors': remove_error_dict,
                'input_value_validator_list': remove_input_value_validator_list,
                'output_validator_list': remove_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.SetType(type.IdType()),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'add': add_rest_metadata,
            'remove': remove_rest_metadata,
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.consumption_domains.zones.cluster.associations',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Associations': Associations,
    }

