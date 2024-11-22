# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespaces.user.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.namespaces.user_client`` module provides classes to
access namespaces for non-administrative users.

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


class Instances(VapiInterface):
    """
    The ``Instances`` class provides methods to access namespaces for
    non-administrative users.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespaces.user.instances'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _InstancesStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``Instances.Summary`` class contains information about a namespace that
        user is authorized to access.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     namespace=None,
                     master_host=None,
                    ):
            """
            :type  namespace: :class:`str`
            :param namespace: Identifier of the namespace.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``. When methods return a
                value of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``.
            :type  master_host: :class:`str`
            :param master_host: IP address or FQDN of the API endpoint for the given namespace.
            """
            self.namespace = namespace
            self.master_host = master_host
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.user.instances.summary', {
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'master_host': type.StringType(),
        },
        Summary,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``Instances.FilterSpec`` class contains attributes used to filter the
        results when listing user namespaces (see :func:`Instances.list`). This
        class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     username=None,
                     groups=None,
                    ):
            """
            :type  username: :class:`str` or ``None``
            :param username: Identifier of the user. This attribute was added in vSphere API
                8.0.0.1.
                If :class:`set`, only return namespaces the given user has
                permissions to access. If None, this filter is not applied.
            :type  groups: :class:`list` of :class:`str` or ``None``
            :param groups: List of group names. This attribute was added in vSphere API
                8.0.0.1.
                If :class:`set`, only return namespaces that are associated with
                the given group(s). If None, this filter is not applied.
            """
            self.username = username
            self.groups = groups
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.user.instances.filter_spec', {
            'username': type.OptionalType(type.StringType()),
            'groups': type.OptionalType(type.ListType(type.StringType())),
        },
        FilterSpec,
        False,
        None))



    def list(self,
             filter=None,
             ):
        """
        Returns namespaces matching the :class:`Instances.FilterSpec`.

        :type  filter: :class:`Instances.FilterSpec` or ``None``
        :param filter: Specification of matching principals for which namespaces should be
            returned. This parameter was added in vSphere API 8.0.0.1.
            If None, the behavior is equivalent to a FilterSpec with all
            attributes None, and this method will return the namespaces that
            user making the call is authorized to access.
        :rtype: :class:`list` of :class:`Instances.Summary`
        :return: List of Namespace identifiers together with the API endpoint for
            each namespace.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the user does not have Namespaces.ListAccess privilege to
            perform this operation.
        """
        return self._invoke('list',
                            {
                            'filter': filter,
                            })
class _InstancesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'filter': type.OptionalType(type.ReferenceType(__name__, 'Instances.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
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
            url_template='/vcenter/namespaces-user/namespaces',
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
                'output_type': type.ListType(type.ReferenceType(__name__, 'Instances.Summary')),
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
            self, iface_name='com.vmware.vcenter.namespaces.user.instances',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Instances': Instances,
    }

