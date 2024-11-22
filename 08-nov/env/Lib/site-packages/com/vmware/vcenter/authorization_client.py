# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.authorization.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.authorization_client`` module provides classes for
managing authorization.

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


class PrivilegeChecks(VapiInterface):
    """
    The ``PrivilegeChecks`` class provides methods for retrieving permission
    privilege checks recorded by VPXD. 
    
    The privilege checks are recorded as VPXD makes them. The latest recorded
    privilege check can be retrieved by a call to
    com.vmware.vcenter.authorization.privilege_checks.Latest.get This allows
    for querying of all privilege checks before or after that moment. For
    example, if an administrator wants to record the privilege checks made by a
    given UI workflow, they can do the following. 1. Retrieve the latest
    privilege check and store it. 2. Go through the UI workflow. 3. Retrieve
    the latest privilege check and store it. 4. Invoke
    com.vmware.vcenter.authorization.PrivilegeChecks.list with the values from
    steps 1) and 3) along with any additional filters.. This class was added in
    vSphere API 8.0.0.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.authorization.privilege_checks'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _PrivilegeChecksStub)
        self._VAPI_OPERATION_IDS = {}

    class Principal(VapiStruct):
        """
        The ``PrivilegeChecks.Principal`` class contains an identity management
        principal ID. This class was added in vSphere API 8.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     name=None,
                     domain=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: The principal's username. This attribute was added in vSphere API
                8.0.0.0.
            :type  domain: :class:`str`
            :param domain: The principal's domain. This attribute was added in vSphere API
                8.0.0.0.
            """
            self.name = name
            self.domain = domain
            VapiStruct.__init__(self)


    Principal._set_binding_type(type.StructType(
        'com.vmware.vcenter.authorization.privilege_checks.principal', {
            'name': type.StringType(),
            'domain': type.StringType(),
        },
        Principal,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``PrivilegeChecks.Info`` class contains detailed information about a
        privilege check. This class was added in vSphere API 8.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     object=None,
                     principal=None,
                     privilege=None,
                    ):
            """
            :type  object: :class:`com.vmware.vapi.std_client.DynamicID`
            :param object: Object for which the privilege was checked. This attribute was
                added in vSphere API 8.0.0.0.
            :type  principal: :class:`PrivilegeChecks.Principal` or ``None``
            :param principal: Principal for which the privilege was checked. Note that the
                username and domain specified are case-insensitive. This attribute
                was added in vSphere API 8.0.0.0.
                If None the privilege was checked for an unauthenticated session.
            :type  privilege: :class:`str`
            :param privilege: Privilege that was checked. This attribute was added in vSphere API
                8.0.0.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.cis.authz.Privilege``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.cis.authz.Privilege``.
            """
            self.object = object
            self.principal = principal
            self.privilege = privilege
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.authorization.privilege_checks.info', {
            'object': type.ReferenceType('com.vmware.vapi.std_client', 'DynamicID'),
            'principal': type.OptionalType(type.ReferenceType(__name__, 'PrivilegeChecks.Principal')),
            'privilege': type.IdType(resource_types='com.vmware.cis.authz.Privilege'),
        },
        Info,
        False,
        None))


    class IterationSpec(VapiStruct):
        """
        The ``PrivilegeChecks.IterationSpec`` class contains attributes used to
        break results into pages when listing privilege checks, see
        :func:`PrivilegeChecks.list`). This class was added in vSphere API 8.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     size=None,
                     marker=None,
                     end_marker=None,
                     timeout_ms=None,
                    ):
            """
            :type  size: :class:`long` or ``None``
            :param size: Specifies the maximum number of results to return. This attribute
                was added in vSphere API 8.0.0.0.
                If None defaults to default page size, which is controlled by
                config.vpxd.privilegeChecks.pageSize advanced option.
            :type  marker: :class:`str` or ``None``
            :param marker: An opaque token which determines where the returned page should
                begin. This attribute was added in vSphere API 8.0.0.0.
                If None or empty, privilege checks will be returned from the first
                record.
            :type  end_marker: :class:`str` or ``None``
            :param end_marker: An opaque token which determines where the returned page should
                end. This attribute was added in vSphere API 8.0.0.0.
                If None or empty, privilege checks will be returned up to size, if
                set, or up to the default page size.
            :type  timeout_ms: :class:`long` or ``None``
            :param timeout_ms: Indicates how long the request should wait in ms for a matching
                check if :attr:`PrivilegeChecks.IterationSpec.marker` is set, and
                there no matching checks to be added to the result. This attribute
                was added in vSphere API 8.0.0.0.
                If None or empty, the request will not wait for additional
                privilege checks and will return immediately.
            """
            self.size = size
            self.marker = marker
            self.end_marker = end_marker
            self.timeout_ms = timeout_ms
            VapiStruct.__init__(self)


    IterationSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.authorization.privilege_checks.iteration_spec', {
            'size': type.OptionalType(type.IntegerType()),
            'marker': type.OptionalType(type.StringType()),
            'end_marker': type.OptionalType(type.StringType()),
            'timeout_ms': type.OptionalType(type.IntegerType()),
        },
        IterationSpec,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``PrivilegeChecks.FilterSpec`` class contains attributes based on which
        privilege checks can be filtered. Any privilege check matching at least one
        of the conditions is returned. This class was added in vSphere API 8.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     objects=None,
                     sessions=None,
                     principals=None,
                     privileges=None,
                     op_ids=None,
                    ):
            """
            :type  objects: :class:`list` of :class:`com.vmware.vapi.std_client.DynamicID` or ``None``
            :param objects: IDs of the objects on which the privilege check was performed. This
                attribute was added in vSphere API 8.0.0.0.
                If None all objects match.
            :type  sessions: :class:`set` of :class:`str` or ``None``
            :param sessions: Sessions for which the check was performed. This attribute was
                added in vSphere API 8.0.0.0.
                If None all sessions match.
            :type  principals: :class:`list` of (:class:`PrivilegeChecks.Principal` or ``None``) or ``None``
            :param principals: Principles for which the privilege check was performed. The None
                ``PrivilegeChecks.Principal`` value matches privilege checks for
                anonymous sessions. This attribute was added in vSphere API
                8.0.0.0.
                If None all principles match.
            :type  privileges: :class:`set` of :class:`str` or ``None``
            :param privileges: Privileges that were checked. This attribute was added in vSphere
                API 8.0.0.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.cis.authz.Privilege``. When methods return a value of
                this class as a return value, the attribute will contain
                identifiers for the resource type:
                ``com.vmware.cis.authz.Privilege``.
                If None all privileges match.
            :type  op_ids: :class:`set` of :class:`str` or ``None``
            :param op_ids: OpIDs of the requests for which the check was performed. This
                attribute was added in vSphere API 8.0.0.0.
                If None all opIDs match.
            """
            self.objects = objects
            self.sessions = sessions
            self.principals = principals
            self.privileges = privileges
            self.op_ids = op_ids
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.authorization.privilege_checks.filter_spec', {
            'objects': type.OptionalType(type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'DynamicID'))),
            'sessions': type.OptionalType(type.SetType(type.StringType())),
            'principals': type.OptionalType(type.ListType(type.OptionalType(type.ReferenceType(__name__, 'PrivilegeChecks.Principal')))),
            'privileges': type.OptionalType(type.SetType(type.IdType())),
            'op_ids': type.OptionalType(type.SetType(type.StringType())),
        },
        FilterSpec,
        False,
        None))


    class ListResult(VapiStruct):
        """
        The ``PrivilegeChecks.ListResult`` class contains information about the
        performed privilege checks, if there are any further privilege checks
        available for reading, and if there are privilege checks potentially
        missing. This class was added in vSphere API 8.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     items=None,
                     marker=None,
                     truncated=None,
                    ):
            """
            :type  items: :class:`list` of :class:`PrivilegeChecks.Info`
            :param items: Privilege checks that match the
                specified:class:`PrivilegeChecks.FilterSpec` and
                :class:`PrivilegeChecks.IterationSpec` in chronological order as
                they were performed. Each check is recorded only the first time it
                is made. If more than one privilege check matches a given
                :class:`PrivilegeChecks.FilterSpec` (for example, two different
                opIDs checked System.Read for the same object and the same
                principal, a FilterSpec which specifies only the principal will
                only contain the first check). This attribute was added in vSphere
                API 8.0.0.0.
            :type  marker: :class:`str`
            :param marker: An opaque marker indicating the last returned privilege check. If
                there are more privilege checks collected than were returned, the
                next ones can be retrieved directly by passing this value to
                another call to
                com.vmware.vcenter.authorization.PrivilegeChecks.list. 
                
                . This attribute was added in vSphere API 8.0.0.0.
            :type  truncated: :class:`bool`
            :param truncated: In case :attr:`PrivilegeChecks.IterationSpec.marker` was specified
                and valid, but the privilege check indicated by it is no longer
                stored, ListResult.truncated is set to True to indicate that some
                privilege checks are potentially missing. 
                
                The number of privilege checks stored is determined by the value of
                config.vpxd.privilegeChecks.bufferSize advanced option.. This
                attribute was added in vSphere API 8.0.0.0.
            """
            self.items = items
            self.marker = marker
            self.truncated = truncated
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.authorization.privilege_checks.list_result', {
            'items': type.ListType(type.ReferenceType(__name__, 'PrivilegeChecks.Info')),
            'marker': type.StringType(),
            'truncated': type.BooleanType(),
        },
        ListResult,
        False,
        None))



    def list(self,
             iteration=None,
             filter=None,
             ):
        """
        Queries the privilege checks matching given criteria. This method was
        added in vSphere API 8.0.0.0.

        :type  iteration: :class:`PrivilegeChecks.IterationSpec` or ``None``
        :param iteration: Contains optional settings for pagination of the result.
            if unset, the oldest privilege checks recorded are returned, paged
            by the default page size. 
            
            The default page size can be changed from
            config.vpxd.privilegeChecks.pageSize advanced option.
        :type  filter: :class:`PrivilegeChecks.FilterSpec` or ``None``
        :param filter: Contains optional settings by which the privilege checks should be
            filtered.
            if unset, recorded privilege checks matching the iteration spec are
            returned.
        :rtype: :class:`PrivilegeChecks.ListResult`
        :return: Detailed information about the privileges collected so far.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if filter or iteration spec contain invalid values.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the iteration spec contains a marker that could not be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``Sessions.CollectPrivilegeChecks``.
        """
        return self._invoke('list',
                            {
                            'iteration': iteration,
                            'filter': filter,
                            })
class _PrivilegeChecksStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'iteration': type.OptionalType(type.ReferenceType(__name__, 'PrivilegeChecks.IterationSpec')),
            'filter': type.OptionalType(type.ReferenceType(__name__, 'PrivilegeChecks.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/authorization/privilege-checks',
            path_variables={
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'list',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'list': {
                'input_type': list_input_type,
                'output_type': type.ReferenceType(__name__, 'PrivilegeChecks.ListResult'),
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
            self, iface_name='com.vmware.vcenter.authorization.privilege_checks',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'PrivilegeChecks': PrivilegeChecks,
        'privilege_checks': 'com.vmware.vcenter.authorization.privilege_checks_client.StubFactory',
        'vt_containers': 'com.vmware.vcenter.authorization.vt_containers_client.StubFactory',
    }

