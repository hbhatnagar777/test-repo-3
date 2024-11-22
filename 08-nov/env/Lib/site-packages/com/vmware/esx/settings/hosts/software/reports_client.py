# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.settings.hosts.software.reports.
#---------------------------------------------------------------------------

"""
The ``com.vmware.esx.settings.hosts.software.reports_client`` module provides
classes to manage reports pertaining to the desired state software for
standalone ESXi hosts.

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


class ApplyImpact(VapiInterface):
    """
    The ``ApplyImpact`` class provides methods to get the impact of an apply
    method on a standalone ESXi host. This class was added in vSphere API
    8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.reports.apply_impact'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ApplyImpactStub)
        self._VAPI_OPERATION_IDS = {}

    class Impact(VapiStruct):
        """
        The ``ApplyImpact.Impact`` class contains attributes that describe what the
        impact is of a particular step during the apply method. This class was
        added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     message=None,
                    ):
            """
            :type  message: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param message: Description of the impact. This attribute was added in vSphere API
                8.0.0.1.
            """
            self.message = message
            VapiStruct.__init__(self)


    Impact._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.reports.apply_impact.impact', {
            'message': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
        },
        Impact,
        False,
        None))


    class HostImpact(VapiStruct):
        """
        The ``ApplyImpact.HostImpact`` class contains attributes that describe the
        summary of how the standalone ESXi host will be impacted during an apply
        method. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     impact=None,
                     commit=None,
                     host_info=None,
                    ):
            """
            :type  impact: :class:`list` of :class:`ApplyImpact.Impact`
            :param impact: Impact of steps performed during the apply method. This attribute
                was added in vSphere API 8.0.0.1.
            :type  commit: :class:`str`
            :param commit: Identifier of the commit on which the impact is generated. This
                attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  host_info: :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information of the host. This attribute was added in vSphere API
                8.0.0.1.
            """
            self.impact = impact
            self.commit = commit
            self.host_info = host_info
            VapiStruct.__init__(self)


    HostImpact._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.reports.apply_impact.host_impact', {
            'impact': type.ListType(type.ReferenceType(__name__, 'ApplyImpact.Impact')),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo'),
        },
        HostImpact,
        False,
        None))



    def get(self,
            host,
            ):
        """
        Returns a summary of how a standalone ESXi host will be impacted during
        an apply method. The impact is generated from the compliance
        information obtained from
        :func:`com.vmware.esx.settings.hosts.software_client.Compliance.get`.
        This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: The host identifier.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`ApplyImpact.HostImpact`
        :return: Summary of how hosts will be impacted during an apply method
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            })
class LastApplyResult(VapiInterface):
    """
    The ``LastApplyResult`` class provides methods to get the most recent
    available result of applying the desired software document to a standalone
    ESXi host. This class was added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.reports.last_apply_result'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _LastApplyResultStub)
        self._VAPI_OPERATION_IDS = {}

    class ApplyStatus(VapiStruct):
        """
        The ``LastApplyResult.ApplyStatus`` class contains attributes that describe
        the status of an apply method. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     status=None,
                     start_time=None,
                     end_time=None,
                     notifications=None,
                    ):
            """
            :type  status: :class:`LastApplyResult.ApplyStatus.Status`
            :param status: The status of the method. This attribute was added in vSphere API
                8.0.0.1.
            :type  start_time: :class:`datetime.datetime`
            :param start_time: Time when the method started. This attribute was added in vSphere
                API 8.0.0.1.
            :type  end_time: :class:`datetime.datetime`
            :param end_time: Time when the method completed. This attribute was added in vSphere
                API 8.0.0.1.
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications`
            :param notifications: Notifications providing additional information about the status of
                the method. This attribute was added in vSphere API 8.0.0.1.
            """
            self.status = status
            self.start_time = start_time
            self.end_time = end_time
            self.notifications = notifications
            VapiStruct.__init__(self)


        class Status(Enum):
            """
            The ``LastApplyResult.ApplyStatus.Status`` class contains the possible
            different status codes that can be returned while trying to apply the
            desired software specification to a standalone host. This enumeration was
            added in vSphere API 8.0.0.1.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            OK = None
            """
            The method completed successfully. This class attribute was added in
            vSphere API 8.0.0.1.

            """
            SKIPPED = None
            """
            The method was skipped. This class attribute was added in vSphere API
            8.0.0.1.

            """
            TIMED_OUT = None
            """
            The method timed out. This class attribute was added in vSphere API
            8.0.0.1.

            """
            ERROR = None
            """
            The method encountered an unspecified error. This class attribute was added
            in vSphere API 8.0.0.1.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Status` instance.
                """
                Enum.__init__(string)

        Status._set_values({
            'OK': Status('OK'),
            'SKIPPED': Status('SKIPPED'),
            'TIMED_OUT': Status('TIMED_OUT'),
            'ERROR': Status('ERROR'),
        })
        Status._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.hosts.software.reports.last_apply_result.apply_status.status',
            Status))

    ApplyStatus._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.reports.last_apply_result.apply_status', {
            'status': type.ReferenceType(__name__, 'LastApplyResult.ApplyStatus.Status'),
            'start_time': type.DateTimeType(),
            'end_time': type.DateTimeType(),
            'notifications': type.ReferenceType('com.vmware.esx.settings_client', 'Notifications'),
        },
        ApplyStatus,
        False,
        None))


    class ApplyResult(VapiStruct):
        """
        The ``LastApplyResult.ApplyResult`` class contains attributes that describe
        the result of an apply method. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     status=None,
                     commit=None,
                     host_info=None,
                     notifications=None,
                    ):
            """
            :type  status: :class:`LastApplyResult.ApplyStatus` or ``None``
            :param status: Specifies the status of the apply method. This attribute was added
                in vSphere API 8.0.0.1.
                None if the apply method is in progress.
            :type  commit: :class:`str`
            :param commit: The identifier of the commit used to fetch the desired software
                document to be applied to the standalone host. This attribute was
                added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  host_info: :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information of the host to which the desired software document
                specified by the :attr:`LastApplyResult.ApplyResult.commit` needs
                to be applied to. This attribute was added in vSphere API 8.0.0.1.
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
            :param notifications: Notifications providing additional information for
                :func:`com.vmware.esx.settings.hosts_client.Software.apply` method.
                These notifications are mutually exclusive with the notifications
                in ``LastApplyResult.ApplyStatus``. This attribute was added in
                vSphere API 8.0.0.1.
            """
            self.status = status
            self.commit = commit
            self.host_info = host_info
            self.notifications = notifications
            VapiStruct.__init__(self)


    ApplyResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.reports.last_apply_result.apply_result', {
            'status': type.OptionalType(type.ReferenceType(__name__, 'LastApplyResult.ApplyStatus')),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo'),
            'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        ApplyResult,
        False,
        None))



    def get(self,
            host,
            ):
        """
        Returns the most recent available result of applying the desired
        software document to the standalone ESXi host. This method was added in
        vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: the host identifier.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`LastApplyResult.ApplyResult`
        :return: Most recent available result of applying the desired software
            document to the standalone ESXi host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no standalone host associated with ``host`` in the
            system or if there is no result associated with the host ``host``
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            })
class LastCheckResult(VapiInterface):
    """
    The ``LastCheckResult`` class provides methods to get the most recent
    available result of the checks that have been run on the standalone host
    before the application of the desired software document to the host. This
    class was added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.reports.last_check_result'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _LastCheckResultStub)
        self._VAPI_OPERATION_IDS = {}

    class Status(Enum):
        """
        The ``LastCheckResult.Status`` class defines the status result for a
        particular check. This enumeration was added in vSphere API 8.0.0.1.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        OK = None
        """
        The check indicates a success. This class attribute was added in vSphere
        API 8.0.0.1.

        """
        WARNING = None
        """
        The check indicates a warning. This class attribute was added in vSphere
        API 8.0.0.1.

        """
        TIMEOUT = None
        """
        The check did not return in a timely manner. This class attribute was added
        in vSphere API 8.0.0.1.

        """
        ERROR = None
        """
        The check indicates an error. This class attribute was added in vSphere API
        8.0.0.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Status` instance.
            """
            Enum.__init__(string)

    Status._set_values({
        'OK': Status('OK'),
        'WARNING': Status('WARNING'),
        'TIMEOUT': Status('TIMEOUT'),
        'ERROR': Status('ERROR'),
    })
    Status._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.hosts.software.reports.last_check_result.status',
        Status))


    class CheckInfo(VapiStruct):
        """
        The ``LastCheckResult.CheckInfo`` class contains attributes that describe a
        particular check. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     check=None,
                     name=None,
                     description=None,
                     originator=None,
                    ):
            """
            :type  check: :class:`str`
            :param check: The check identifier. This attribute was added in vSphere API
                8.0.0.1.
            :type  name: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param name: The check name. This attribute was added in vSphere API 8.0.0.1.
            :type  description: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param description: Human-readable check description. This attribute was added in
                vSphere API 8.0.0.1.
            :type  originator: :class:`str` or ``None``
            :param originator: The service that performed the check. This attribute was added in
                vSphere API 8.0.0.1.
                Only :class:`set` if there is an originator available for this
                check.
            """
            self.check = check
            self.name = name
            self.description = description
            self.originator = originator
            VapiStruct.__init__(self)


    CheckInfo._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.reports.last_check_result.check_info', {
            'check': type.StringType(),
            'name': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
            'description': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
            'originator': type.OptionalType(type.StringType()),
        },
        CheckInfo,
        False,
        None))


    class CheckIssue(VapiStruct):
        """


        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     description=None,
                     resolution=None,
                    ):
            """
            :type  description: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param description: Description of the issue encountered. This attribute was added in
                vSphere API 8.0.0.1.
            :type  resolution: :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param resolution: Possible resolution for the issue. This attribute was added in
                vSphere API 8.0.0.1.
                Can be left None if no meaningful resolution exists.
            """
            self.description = description
            self.resolution = resolution
            VapiStruct.__init__(self)


    CheckIssue._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.reports.last_check_result.check_issue', {
            'description': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
            'resolution': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        CheckIssue,
        False,
        None))


    class CheckStatus(VapiStruct):
        """
        The ``LastCheckResult.CheckStatus`` class contains attributes that describe
        a check result. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     check=None,
                     status=None,
                     check_issues=None,
                    ):
            """
            :type  check: :class:`LastCheckResult.CheckInfo`
            :param check: Information about this check. This attribute was added in vSphere
                API 8.0.0.1.
            :type  status: :class:`LastCheckResult.Status`
            :param status: The status of this check. This attribute was added in vSphere API
                8.0.0.1.
            :type  check_issues: :class:`list` of :class:`LastCheckResult.CheckIssue` or ``None``
            :param check_issues: The issues encountered while running this check. This attribute was
                added in vSphere API 8.0.0.1.
            """
            self.check = check
            self.status = status
            self.check_issues = check_issues
            VapiStruct.__init__(self)


    CheckStatus._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.reports.last_check_result.check_status', {
            'check': type.ReferenceType(__name__, 'LastCheckResult.CheckInfo'),
            'status': type.ReferenceType(__name__, 'LastCheckResult.Status'),
            'check_issues': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'LastCheckResult.CheckIssue'))),
        },
        CheckStatus,
        False,
        None))


    class EntityCheckResult(VapiStruct):
        """
        The ``LastCheckResult.EntityCheckResult`` class contains attributes that
        describe aggregated status of all checks performed on a specific entity.
        This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'type',
                {
                    'HOST' : [('host', True)],
                }
            ),
        ]



        def __init__(self,
                     type=None,
                     host=None,
                     status=None,
                     check_statuses=None,
                    ):
            """
            :type  type: :class:`LastCheckResult.EntityCheckResult.EntityType`
            :param type: The entity type for which these checks are being run. This
                attribute was added in vSphere API 8.0.0.1.
            :type  host: :class:`str`
            :param host: If the entity type is HOST then the host identifier for which the
                checks have been run. This attribute was added in vSphere API
                8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``HostSystem``.
                This attribute is optional and it is only relevant when the value
                of ``type`` is
                :attr:`LastCheckResult.EntityCheckResult.EntityType.HOST`.
            :type  status: :class:`LastCheckResult.Status`
            :param status: Aggregated status from all checks performed on this entity. This
                attribute was added in vSphere API 8.0.0.1.
            :type  check_statuses: :class:`list` of :class:`LastCheckResult.CheckStatus`
            :param check_statuses: List of ``LastCheckResult.CheckStatus`` for all checks performed.
                This attribute was added in vSphere API 8.0.0.1.
            """
            self.type = type
            self.host = host
            self.status = status
            self.check_statuses = check_statuses
            VapiStruct.__init__(self)


        class EntityType(Enum):
            """
            The ``LastCheckResult.EntityCheckResult.EntityType`` class contains the
            entities on which checks can be performed. This enumeration was added in
            vSphere API 8.0.0.1.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            HOST = None
            """
            Entity type Host. This class attribute was added in vSphere API 8.0.0.1.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`EntityType` instance.
                """
                Enum.__init__(string)

        EntityType._set_values({
            'HOST': EntityType('HOST'),
        })
        EntityType._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.hosts.software.reports.last_check_result.entity_check_result.entity_type',
            EntityType))

    EntityCheckResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.reports.last_check_result.entity_check_result', {
            'type': type.ReferenceType(__name__, 'LastCheckResult.EntityCheckResult.EntityType'),
            'host': type.OptionalType(type.IdType()),
            'status': type.ReferenceType(__name__, 'LastCheckResult.Status'),
            'check_statuses': type.ListType(type.ReferenceType(__name__, 'LastCheckResult.CheckStatus')),
        },
        EntityCheckResult,
        False,
        None))


    class CheckResult(VapiStruct):
        """
        The ``LastCheckResult.CheckResult`` class contains attributes that describe
        aggregated status of all checks performed. This class was added in vSphere
        API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     status=None,
                     start_time=None,
                     end_time=None,
                     commit=None,
                     host_info=None,
                     entity_result=None,
                    ):
            """
            :type  status: :class:`LastCheckResult.Status`
            :param status: Aggregated status from all checks performed. This attribute was
                added in vSphere API 8.0.0.1.
            :type  start_time: :class:`datetime.datetime`
            :param start_time: Time when the operation started. This attribute was added in
                vSphere API 8.0.0.1.
            :type  end_time: :class:`datetime.datetime`
            :param end_time: Time when the operation completed. This attribute was added in
                vSphere API 8.0.0.1.
            :type  commit: :class:`str`
            :param commit: The identifier of the commit on which checks have been run. This
                attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  host_info: :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information about the host for which checks have been requested to
                be run. This attribute was added in vSphere API 8.0.0.1.
            :type  entity_result: :class:`LastCheckResult.EntityCheckResult`
            :param entity_result: List of ``LastCheckResult.EntityCheckResult`` for all entities for
                which checks have been run. This attribute was added in vSphere API
                8.0.0.1.
            """
            self.status = status
            self.start_time = start_time
            self.end_time = end_time
            self.commit = commit
            self.host_info = host_info
            self.entity_result = entity_result
            VapiStruct.__init__(self)


    CheckResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.reports.last_check_result.check_result', {
            'status': type.ReferenceType(__name__, 'LastCheckResult.Status'),
            'start_time': type.DateTimeType(),
            'end_time': type.DateTimeType(),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo'),
            'entity_result': type.ReferenceType(__name__, 'LastCheckResult.EntityCheckResult'),
        },
        CheckResult,
        False,
        None))



    def get(self,
            host,
            ):
        """
        Returns the most recent available result of checks run on the
        standalone host before the application of the desired software document
        to the host. This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: The host identifier.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`LastCheckResult.CheckResult`
        :return: Most recent available result of the checks run on the host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no standalone host associated with ``host`` in the
            system or if there is no result associated with the host ``host``.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSoftwareRemediation.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            })
class _ApplyImpactStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/hosts/{host}/software/reports/apply-impact',
            path_variables={
                'host': 'host',
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
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'ApplyImpact.HostImpact'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.software.reports.apply_impact',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _LastApplyResultStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/hosts/{host}/software/reports/last-apply-result',
            path_variables={
                'host': 'host',
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
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'LastApplyResult.ApplyResult'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.software.reports.last_apply_result',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _LastCheckResultStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/hosts/{host}/software/reports/last-check-result',
            path_variables={
                'host': 'host',
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
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'LastCheckResult.CheckResult'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.software.reports.last_check_result',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'ApplyImpact': ApplyImpact,
        'LastApplyResult': LastApplyResult,
        'LastCheckResult': LastCheckResult,
    }

