# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.consumption_domains.zone_associations.
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


class Cluster(VapiInterface):
    """
    The ``CLUSTER`` class provides methods to query zone-cluster associations.
    This class was added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.consumption_domains.zone_associations.cluster'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ClusterStub)
        self._VAPI_OPERATION_IDS = {}

    class ListItem(VapiStruct):
        """
        The ``Cluster.ListItem`` class describes a zone-cluster association. This
        class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     zone=None,
                     cluster=None,
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
            :type  cluster: :class:`str`
            :param cluster: Identifier of the cluster. This attribute was added in vSphere API
                8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            """
            self.zone = zone
            self.cluster = cluster
            VapiStruct.__init__(self)


    ListItem._set_binding_type(type.StructType(
        'com.vmware.vcenter.consumption_domains.zone_associations.cluster.list_item', {
            'zone': type.IdType(resource_types='com.vmware.vcenter.consumption_domains.Zone'),
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        },
        ListItem,
        False,
        None))


    class ListResult(VapiStruct):
        """
        The ``Cluster.ListResult`` class contains the list of zone-cluster
        associations. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     associations=None,
                    ):
            """
            :type  associations: :class:`list` of :class:`Cluster.ListItem`
            :param associations: The list of zone-cluster associations. This attribute was added in
                vSphere API 8.0.0.1.
            """
            self.associations = associations
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.consumption_domains.zone_associations.cluster.list_result', {
            'associations': type.ListType(type.ReferenceType(__name__, 'Cluster.ListItem')),
        },
        ListResult,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``Cluster.FilterSpec`` class contains attributes used to filter the
        results when listing associations between clusters and zones, see
        :func:`Cluster.list`. If multiple filtering criteria are provided in a
        ``Cluster.FilterSpec``, then the filtering is done based on all of them,
        i.e., every returned zone-cluster association must satisfy all the
        filtering criteria. This ``Cluster.FilterSpec`` class can be used to list
        zones associated with a given cluster as well as to list the clusters
        associated with a given zone. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     clusters=None,
                     zones=None,
                    ):
            """
            :type  clusters: :class:`set` of :class:`str` or ``None``
            :param clusters: Zone-cluster associations will be filtered such that each
                association that is returned will have a cluster identifier from
                this set of specified cluster identifiers. This attribute was added
                in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will contain identifiers for
                the resource type: ``ClusterComputeResource``.
                If None or empty, zone-cluster associations will not be filtered
                based on cluster identifiers. Associations with any cluster
                identifier will match this filter.
            :type  zones: :class:`set` of :class:`str` or ``None``
            :param zones: Zone-cluster associations will be filtered such that each
                association that is returned will have a zone identifier from this
                set of specified zone identifiers. This attribute was added in
                vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.consumption_domains.Zone``.
                If None or empty, zone-cluster associations will not be filtered
                based on zone identifiers. Associations with any zone identifier
                will match this filter.
            """
            self.clusters = clusters
            self.zones = zones
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.consumption_domains.zone_associations.cluster.filter_spec', {
            'clusters': type.OptionalType(type.SetType(type.IdType())),
            'zones': type.OptionalType(type.SetType(type.IdType())),
        },
        FilterSpec,
        False,
        None))



    def list(self,
             filter=None,
             ):
        """
        Returns zone-cluster associations that match the specified filter. This
        method was added in vSphere API 8.0.0.1.

        :type  filter: :class:`Cluster.FilterSpec` or ``None``
        :param filter: The specification of matching zone-cluster associations.
            If None, the behavior is equivalent to a
            :class:`Cluster.FilterSpec` with all attributes None, which means
            all the zone-cluster associations will be returned.
        :rtype: :class:`Cluster.ListResult`
        :return: Zone-cluster associations matching the :class:`Cluster.FilterSpec`.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have all of the privileges described as
            follows: - The resource com.vmware.vcenter.consumption_domains.Zone
            referenced by the parameter zones in ``Cluster.FilterSpec``
            requires System.Read privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            when unexpected error is encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``System.Read``.
        """
        return self._invoke('list',
                            {
                            'filter': filter,
                            })
class _ClusterStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'filter': type.OptionalType(type.ReferenceType(__name__, 'Cluster.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/consumption-domains/zone-associations/cluster',
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
                'output_type': type.ReferenceType(__name__, 'Cluster.ListResult'),
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
            self, iface_name='com.vmware.vcenter.consumption_domains.zone_associations.cluster',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Cluster': Cluster,
    }

