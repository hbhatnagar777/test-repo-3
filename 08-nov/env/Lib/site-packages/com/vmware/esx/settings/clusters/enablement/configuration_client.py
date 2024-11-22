# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.settings.clusters.enablement.configuration.
#---------------------------------------------------------------------------

"""
The ``com.vmware.esx.settings.clusters.enablement.configuration_client`` module
provides classes to manage enablement of configuration on an ESX cluster.

"""

__author__ = 'VMware, Inc.'
__docformat__ = 'restructuredtext en'

import sys
from warnings import warn

from com.vmware.cis_client import Tasks
from vmware.vapi.stdlib.client.task import Task
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


class Transition(VapiInterface):
    """
    The ``Transition`` class provides methods to manage transition of an
    existing cluster to a desired configuration managed cluster. This class was
    added in vSphere API 8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.enablement.configuration.transition'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _TransitionStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'check_eligibility_task': 'check_eligibility$task'})
        self._VAPI_OPERATION_IDS.update({'import_from_host_task': 'import_from_host$task'})
        self._VAPI_OPERATION_IDS.update({'validate_config_task': 'validate_config$task'})
        self._VAPI_OPERATION_IDS.update({'precheck_task': 'precheck$task'})
        self._VAPI_OPERATION_IDS.update({'enable_task': 'enable$task'})

    class Source(Enum):
        """
        The ``Transition.Source`` class describes the possible sources for
        specifying the desired configuration of the cluster. This enumeration was
        added in vSphere API 8.0.1.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        FILE = None
        """
        This indicates that desired configuration originated from a file. This
        class attribute was added in vSphere API 8.0.1.0.

        """
        HOST = None
        """
        This indicates that desired configuration originated from a reference host.
        This class attribute was added in vSphere API 8.0.1.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Source` instance.
            """
            Enum.__init__(string)

    Source._set_values({
        'FILE': Source('FILE'),
        'HOST': Source('HOST'),
    })
    Source._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.enablement.configuration.transition.source',
        Source))


    class Hints(VapiStruct):
        """
        The ``Transition.Hints`` contains attributes that specifies additional
        information about the transition workflow. This data should be used as
        guidelines throughout the transition process. This class was added in
        vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     requires_reference_host=None,
                    ):
            """
            :type  requires_reference_host: :class:`bool` or ``None``
            :param requires_reference_host: This hint indicates whether a reference host is required to
                transition the cluster. This hint is set to true if the framework
                detects that cluster is not managed by vLCM. The value does not
                change based on the state of the transition workflow, or the value
                of the reference host, or status of the reference host. This
                attribute was added in vSphere API 8.0.3.0.
                If field is None then the reference host is not required.
            """
            self.requires_reference_host = requires_reference_host
            VapiStruct.__init__(self)


    Hints._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.enablement.configuration.transition.hints', {
            'requires_reference_host': type.OptionalType(type.BooleanType()),
        },
        Hints,
        False,
        None))


    class ReferenceHost(VapiStruct):
        """
        The ``Transition.ReferenceHost`` contains attributes that specify the
        reference host information used by the transition process. This class was
        added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     host=None,
                     host_info=None,
                    ):
            """
            :type  host: :class:`str`
            :param host: Reference host ID. This attribute was added in vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``HostSystem``.
            :type  host_info: :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Host Info for Reference host. This attribute was added in vSphere
                API 8.0.1.0.
            """
            self.host = host
            self.host_info = host_info
            VapiStruct.__init__(self)


    ReferenceHost._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.enablement.configuration.transition.reference_host', {
            'host': type.IdType(resource_types='HostSystem'),
            'host_info': type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo'),
        },
        ReferenceHost,
        False,
        None))


    class State(VapiStruct):
        """
        The ``Transition.State`` class contains attributes that describe the latest
        state of transitioning a cluster to desired configuration management
        platform. This class was added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'source',
                {
                    'HOST' : [('host', True)],
                    'FILE' : [('filename', True)],
                }
            ),
        ]



        def __init__(self,
                     author=None,
                     start_time=None,
                     modified_time=None,
                     source=None,
                     host=None,
                     filename=None,
                    ):
            """
            :type  author: :class:`str`
            :param author: Author of transition. This attribute was added in vSphere API
                8.0.1.0.
            :type  start_time: :class:`datetime.datetime`
            :param start_time: The start time of the transition process. This attribute was added
                in vSphere API 8.0.1.0.
            :type  modified_time: :class:`datetime.datetime`
            :param modified_time: Last modified time of the transition process. This attribute was
                added in vSphere API 8.0.1.0.
            :type  source: :class:`Transition.Source`
            :param source: Source of reference configuration. This attribute was added in
                vSphere API 8.0.1.0.
            :type  host: :class:`Transition.ReferenceHost`
            :param host: Reference host. This attribute was added in vSphere API 8.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``source`` is :attr:`Transition.Source.HOST`.
            :type  filename: :class:`str`
            :param filename: Filename of the imported configuration. This attribute was added in
                vSphere API 8.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``source`` is :attr:`Transition.Source.FILE`.
            """
            self.author = author
            self.start_time = start_time
            self.modified_time = modified_time
            self.source = source
            self.host = host
            self.filename = filename
            VapiStruct.__init__(self)


    State._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.enablement.configuration.transition.state', {
            'author': type.StringType(),
            'start_time': type.DateTimeType(),
            'modified_time': type.DateTimeType(),
            'source': type.ReferenceType(__name__, 'Transition.Source'),
            'host': type.OptionalType(type.ReferenceType(__name__, 'Transition.ReferenceHost')),
            'filename': type.OptionalType(type.StringType()),
        },
        State,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Transition.Info`` class contains attributes that describe the current
        status of transition process in the cluster. This class was added in
        vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'status',
                {
                    'STARTED' : [('state', True)],
                    'NOT_ALLOWED_IN_CURRENT_STATE' : [('state', True)],
                    'NOT_STARTED' : [('fast_track', True)],
                    'ENABLED' : [],
                    'ENABLE_IN_PROGRESS' : [],
                    'SOFTWARE_SPECIFICATION_NOT_SET' : [],
                }
            ),
        ]



        def __init__(self,
                     status=None,
                     state=None,
                     fast_track=None,
                     hints=None,
                    ):
            """
            :type  status: :class:`Transition.Info.Status`
            :param status: Status of transition on a cluster. This attribute was added in
                vSphere API 8.0.1.0.
            :type  state: :class:`Transition.State`
            :param state: State of the transition. This field is :class:`set` if the cluster
                is currently being transitioned to desired configuration management
                platform. This attribute was added in vSphere API 8.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``status`` is one of :attr:`Transition.Info.Status.STARTED` or
                :attr:`Transition.Info.Status.NOT_ALLOWED_IN_CURRENT_STATE`.
            :type  fast_track: :class:`bool`
            :param fast_track: Flag describing if fast transition workflow is eligible on the
                cluster. Fast transition allows user to enable desired
                configuration platform on the cluster with default configuration.
                The cluster is eligible if transition workflow is not started and
                the cluster is empty. This attribute was added in vSphere API
                8.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``status`` is :attr:`Transition.Info.Status.NOT_STARTED`.
            :type  hints: :class:`Transition.Hints`
            :param hints: This field provides additional information about the transition
                workflow. This attribute was added in vSphere API 8.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.status = status
            self.state = state
            self.fast_track = fast_track
            self.hints = hints
            VapiStruct.__init__(self)


        class Status(Enum):
            """
            The ``Transition.Info.Status`` class contains the possible status codes
            describing the transition state of the cluster. This enumeration was added
            in vSphere API 8.0.1.0.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            ENABLED = None
            """
            Transition has completed successfully and the cluster is managed through
            the desired configuration management platform. This class attribute was
            added in vSphere API 8.0.1.0.

            """
            ENABLE_IN_PROGRESS = None
            """
            Transition has started and :func:`Transition.enable` task is running on the
            cluster. This class attribute was added in vSphere API 8.0.1.0.

            """
            NOT_ALLOWED_IN_CURRENT_STATE = None
            """
            Cluster is not in a state to transition to desired configuration management
            platform. The cluster ends up in this state if another user identified by
            :attr:`Transition.State.author` has already started transition. This class
            attribute was added in vSphere API 8.0.1.0.

            """
            NOT_STARTED = None
            """
            Transition has not started on the cluster. This class attribute was added
            in vSphere API 8.0.1.0.

            """
            SOFTWARE_SPECIFICATION_NOT_SET = None
            """
            Desired software specification is not set on the cluster. This is a
            pre-requisite to transition a cluster to desired configuration management
            platform. This class attribute was added in vSphere API 8.0.1.0.

            """
            STARTED = None
            """
            Transition has started on the cluster. This class attribute was added in
            vSphere API 8.0.1.0.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Status` instance.
                """
                Enum.__init__(string)

        Status._set_values({
            'ENABLED': Status('ENABLED'),
            'ENABLE_IN_PROGRESS': Status('ENABLE_IN_PROGRESS'),
            'NOT_ALLOWED_IN_CURRENT_STATE': Status('NOT_ALLOWED_IN_CURRENT_STATE'),
            'NOT_STARTED': Status('NOT_STARTED'),
            'SOFTWARE_SPECIFICATION_NOT_SET': Status('SOFTWARE_SPECIFICATION_NOT_SET'),
            'STARTED': Status('STARTED'),
        })
        Status._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.clusters.enablement.configuration.transition.info.status',
            Status))

    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.enablement.configuration.transition.info', {
            'status': type.ReferenceType(__name__, 'Transition.Info.Status'),
            'state': type.OptionalType(type.ReferenceType(__name__, 'Transition.State')),
            'fast_track': type.OptionalType(type.BooleanType()),
            'hints': type.OptionalType(type.ReferenceType(__name__, 'Transition.Hints')),
        },
        Info,
        False,
        None))


    class EligibilityResult(VapiStruct):
        """
        This ``Transition.EligibilityResult`` class contains attributes that
        describe the result of the eligibility checks performed on the cluster to
        determine if the cluster can transition to desired configuration management
        platform. This class was added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     status=None,
                     notifications=None,
                    ):
            """
            :type  status: :class:`Transition.EligibilityResult.Status`
            :param status: Status of eligibility checks performed on a cluster. This attribute
                was added in vSphere API 8.0.1.0.
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
            :param notifications: Notifications providing additional information about the status of
                eligibility checks. This attribute was added in vSphere API
                8.0.1.0.
                This field is None when :attr:`Transition.EligibilityResult.status`
                is ELLIGIBLE.
            """
            self.status = status
            self.notifications = notifications
            VapiStruct.__init__(self)


        class Status(Enum):
            """
            The ``Transition.EligibilityResult.Status`` class contains the possible
            status codes describing the result of eligibility checks. This enumeration
            was added in vSphere API 8.0.1.0.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            ELIGIBLE = None
            """
            This indicates that the cluster meets all the eligibility requirements.
            This class attribute was added in vSphere API 8.0.1.0.

            """
            NOT_ELIGIBLE = None
            """
            This indicates that the cluster does not meet the eligibility requirements.
            This class attribute was added in vSphere API 8.0.1.0.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Status` instance.
                """
                Enum.__init__(string)

        Status._set_values({
            'ELIGIBLE': Status('ELIGIBLE'),
            'NOT_ELIGIBLE': Status('NOT_ELIGIBLE'),
        })
        Status._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.clusters.enablement.configuration.transition.eligibility_result.status',
            Status))

    EligibilityResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.enablement.configuration.transition.eligibility_result', {
            'status': type.ReferenceType(__name__, 'Transition.EligibilityResult.Status'),
            'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        EligibilityResult,
        False,
        None))


    class FileSpec(VapiStruct):
        """
        The ``Transition.FileSpec`` contain attributes that contains the details of
        the file being imported during transition process. This class was added in
        vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     filename=None,
                     config=None,
                    ):
            """
            :type  filename: :class:`str`
            :param filename: Filename of the imported configuration. This attribute was added in
                vSphere API 8.0.1.0.
            :type  config: :class:`str`
            :param config: Configuration from the imported file. This attribute was added in
                vSphere API 8.0.1.0.
            """
            self.filename = filename
            self.config = config
            VapiStruct.__init__(self)


    FileSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.enablement.configuration.transition.file_spec', {
            'filename': type.StringType(),
            'config': type.StringType(),
        },
        FileSpec,
        False,
        None))


    class ValidateResult(VapiStruct):
        """
        The ``Transition.ValidateResult`` class contains attributes that describe
        the validity of the imported desired configuration, and compliance
        information. This class was added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'status',
                {
                    'INVALID' : [('errors', True)],
                    'VALID' : [('compliance', True)],
                }
            ),
        ]



        def __init__(self,
                     status=None,
                     errors=None,
                     compliance=None,
                    ):
            """
            :type  status: :class:`Transition.ValidateResult.Status`
            :param status: Status indicating whether the configuration draft validated
                successfully. This attribute was added in vSphere API 8.0.1.0.
            :type  errors: :class:`list` of :class:`com.vmware.esx.settings.clusters.configuration_client.ValidationError`
            :param errors: Lists all validation errors identified in the configuration draft.
                This attribute was added in vSphere API 8.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``status`` is :attr:`Transition.ValidateResult.Status.INVALID`.
            :type  compliance: :class:`com.vmware.esx.settings.clusters.configuration_client.ClusterCompliance`
            :param compliance: Cluster Compliance result. This attribute was added in vSphere API
                8.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``status`` is :attr:`Transition.ValidateResult.Status.VALID`.
            """
            self.status = status
            self.errors = errors
            self.compliance = compliance
            VapiStruct.__init__(self)


        class Status(Enum):
            """
            The ``Transition.ValidateResult.Status`` class contains the possible status
            codes describing the result of validating configuration draft. This
            enumeration was added in vSphere API 8.0.1.0.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            INVALID = None
            """
            This indicates that the configuration draft is invalid. This class
            attribute was added in vSphere API 8.0.1.0.

            """
            VALID = None
            """
            This indicates that the configuration draft is valid. This class attribute
            was added in vSphere API 8.0.1.0.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Status` instance.
                """
                Enum.__init__(string)

        Status._set_values({
            'INVALID': Status('INVALID'),
            'VALID': Status('VALID'),
        })
        Status._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.clusters.enablement.configuration.transition.validate_result.status',
            Status))

    ValidateResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.enablement.configuration.transition.validate_result', {
            'status': type.ReferenceType(__name__, 'Transition.ValidateResult.Status'),
            'errors': type.OptionalType(type.ListType(type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'ValidationError'))),
            'compliance': type.OptionalType(type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'ClusterCompliance')),
        },
        ValidateResult,
        False,
        None))


    class EnableResult(VapiStruct):
        """
        The ``Transition.EnableResult`` class contains attributes that describes
        the result of enabling configmanager on a cluster as part of the transition
        process. This class was added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'status',
                {
                    'ERROR' : [('errors', True)],
                    'SUCCESS_APPLY_INITIATED' : [('apply_task_ID', True)],
                    'RUNNING' : [],
                    'SUCCESS' : [],
                }
            ),
        ]


        _canonical_to_pep_names = {
                                'apply_task_ID': 'apply_task_id',
                                }

        def __init__(self,
                     status=None,
                     errors=None,
                     apply_task_id=None,
                    ):
            """
            :type  status: :class:`Transition.EnableResult.Status`
            :param status: Status of enabling configmanager on a cluster. This attribute was
                added in vSphere API 8.0.1.0.
            :type  errors: :class:`list` of :class:`com.vmware.esx.settings_client.Notification`
            :param errors: List of errors if any. This attribute was added in vSphere API
                8.0.1.0.
                This attribute is optional and it is only relevant when the value
                of ``status`` is :attr:`Transition.EnableResult.Status.ERROR`.
            :type  apply_task_id: :class:`str`
            :param apply_task_id: ID of the Apply task invoked once ConfigManager is enabled on the
                cluster. This attribute was added in vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.cis.task``. When methods return a value of this class
                as a return value, the attribute will be an identifier for the
                resource type: ``com.vmware.cis.task``.
                This attribute is optional and it is only relevant when the value
                of ``status`` is
                :attr:`Transition.EnableResult.Status.SUCCESS_APPLY_INITIATED`.
            """
            self.status = status
            self.errors = errors
            self.apply_task_id = apply_task_id
            VapiStruct.__init__(self)


        class Status(Enum):
            """
            The ``Transition.EnableResult.Status`` class contains the status of Enable
            API. This enumeration was added in vSphere API 8.0.1.0.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            ERROR = None
            """
            Failed to enable ConfigManager on the cluster. This class attribute was
            added in vSphere API 8.0.1.0.

            """
            RUNNING = None
            """
            The task is in-progress. This class attribute was added in vSphere API
            8.0.1.0.

            """
            SUCCESS = None
            """
            ConfigMnager enabled on the cluster. This class attribute was added in
            vSphere API 8.0.1.0.

            """
            SUCCESS_APPLY_INITIATED = None
            """
            ConfigMnager enabled on the cluster and remediation was initiated. This
            class attribute was added in vSphere API 8.0.1.0.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Status` instance.
                """
                Enum.__init__(string)

        Status._set_values({
            'ERROR': Status('ERROR'),
            'RUNNING': Status('RUNNING'),
            'SUCCESS': Status('SUCCESS'),
            'SUCCESS_APPLY_INITIATED': Status('SUCCESS_APPLY_INITIATED'),
        })
        Status._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.clusters.enablement.configuration.transition.enable_result.status',
            Status))

    EnableResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.enablement.configuration.transition.enable_result', {
            'status': type.ReferenceType(__name__, 'Transition.EnableResult.Status'),
            'errors': type.OptionalType(type.ListType(type.ReferenceType('com.vmware.esx.settings_client', 'Notification'))),
            'apply_task_ID': type.OptionalType(type.IdType()),
        },
        EnableResult,
        False,
        None))



    def get(self,
            cluster,
            ):
        """
        This API returns the current transition state of the cluster. This
        method was added in vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`Transition.Info`
        :return: The transition state of the cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.View``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.View``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })


    def check_eligibility_task(self,
                          cluster,
                          ):
        """
        The API performs eligibility checks on the cluster to see if it can be
        transitioned to desired configuration management platform. This method
        was added in vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('check_eligibility$task',
                                {
                                'cluster': cluster,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Transition.EligibilityResult'))
        return task_instance

    def cancel(self,
               cluster,
               ):
        """
        This API cancels the workflow to transition the cluster to desired
        configuration platform. If the status of transition is
        :attr:`Transition.Info.Status.STARTED`, the associated state
        information will be deleted. Otherwise, cancel will not be allowed and
        the API will throw an error. This method was added in vSphere API
        8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If the status of transition process is not
            :attr:`Transition.Info.Status.STARTED`.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.Modify``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.Modify``.
        """
        return self._invoke('cancel',
                            {
                            'cluster': cluster,
                            })

    def import_from_file(self,
                         cluster,
                         spec,
                         ):
        """
        The API imports the desired configuration from a file. Import API does
        not validate the configuration against the schema. The result will
        specify if the configuration was imported successfully. The result will
        provide localized error message if the import operation failed. This
        method was added in vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Transition.FileSpec`
        :param spec: Input structure containing file information.
        :rtype: :class:`com.vmware.esx.settings.clusters.configuration_client.DraftImportResult`
        :return: Output structure containing the status of the operation and error
            if any.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.Modify``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.Modify``.
        """
        return self._invoke('import_from_file',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })


    def import_from_host_task(self,
                         cluster,
                         host,
                         ):
        """
        The API imports the desired configuration from a reference host in the
        cluster. The API also adds host-specific and host-overrides from the
        other hosts in the cluster. Import API does not validate the
        configuration against the schema. The result will specify if the
        configuration was imported successfully. The result will provide
        localized error message if the import operation failed. This method was
        added in vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  host: :class:`str`
        :param host: Identifier of the reference host
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('import_from_host$task',
                                {
                                'cluster': cluster,
                                'host': host,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'DraftImportResult'))
        return task_instance

    def export_config(self,
                      cluster,
                      ):
        """
        This API will export configuration associated with the cluster
        generated as part of the transition workflow. The API will throw an
        error if the transition state is not
        :attr:`Transition.Info.Status.STARTED`. This method was added in
        vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster on which operation should be performed.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`com.vmware.esx.settings.clusters.configuration_client.ExportResult`
        :return: This output structure of type
            :class:`com.vmware.esx.settings.clusters.configuration_client.ExportResult`
            contains the configuration document encoded as JSON.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some other unknown internal error. The accompanying
            error message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If the status of transition process is not
            :attr:`Transition.Info.Status.STARTED`.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If the cluster is not found in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.Export``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.Export``.
        """
        return self._invoke('export_config',
                            {
                            'cluster': cluster,
                            })

    def export_schema(self,
                      cluster,
                      ):
        """
        This API will export schema associated with the cluster. The API will
        throw an error if the transition state is not
        :attr:`Transition.Info.Status.STARTED`. This method was added in
        vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster on which operation should be performed.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`com.vmware.esx.settings.clusters.configuration_client.SchemaResult`
        :return: This output structure of type
            :class:`com.vmware.esx.settings.clusters.configuration_client.SchemaResult`
            containing the schema document encoded as JSON.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some other unknown internal error. The accompanying
            error message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If the status of transition process is not
            :attr:`Transition.Info.Status.STARTED`.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If the cluster is not found in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.Export``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.Export``.
        """
        return self._invoke('export_schema',
                            {
                            'cluster': cluster,
                            })


    def validate_config_task(self,
                        cluster,
                        ):
        """
        The API validates the imported desired configuration against the schema
        and on the hosts with validation plugins. If the document is valid, the
        API will check all the hosts for compliance with the desired
        configuration. The API returns validation errors if the configuration
        is not valid on any of the host. If the configuration is valid, the API
        returns compliance information. This method was added in vSphere API
        8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('validate_config$task',
                                {
                                'cluster': cluster,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Transition.ValidateResult'))
        return task_instance


    def precheck_task(self,
                 cluster,
                 ):
        """
        The API computes impact of transitioning the cluster to be managed by
        desired configuration platform. It also runs health checks to verify
        the cluster's health before transitioning. The API returns the impact
        on the hosts in the cluster and the result of health checks from the
        cluster and hosts. Health checks are run only if the host needs be
        rebooted or put in maintenanceMode. This method was added in vSphere
        API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('precheck$task',
                                {
                                'cluster': cluster,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'ClusterPrecheckResult'))
        return task_instance


    def enable_task(self,
               cluster,
               ):
        """
        The API enables ConfigManager on the cluster. Before setting the
        desired configuration state, the API verifies the eligibility of the
        cluster to transition to desired configuration platform. The API then
        validates and sets the configuration draft as the desired configuration
        of the cluster, thus enabling ConfigManager. The API finally initiates
        remediation by invoking Apply. Apply is not invoked if the cluster is
        empty. The API does not wait for remediation to complete before
        returning. If any of the above step fails, the API will fail and result
        will contain descriptive error messages. This method was added in
        vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('enable$task',
                                {
                                'cluster': cluster,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Transition.EnableResult'))
        return task_instance
class _TransitionStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/enablement/configuration/transition',
            path_variables={
                'cluster': 'cluster',
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

        # properties for check_eligibility operation
        check_eligibility_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        check_eligibility_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        check_eligibility_input_value_validator_list = [
        ]
        check_eligibility_output_validator_list = [
        ]
        check_eligibility_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/enablement/configuration/transition',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'checkEligibility',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for cancel operation
        cancel_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        cancel_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        cancel_input_value_validator_list = [
        ]
        cancel_output_validator_list = [
        ]
        cancel_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/enablement/configuration/transition',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'cancel',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for import_from_file operation
        import_from_file_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.ReferenceType(__name__, 'Transition.FileSpec'),
        })
        import_from_file_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        import_from_file_input_value_validator_list = [
        ]
        import_from_file_output_validator_list = [
        ]
        import_from_file_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/enablement/configuration/transition',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'importFromFile',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for import_from_host operation
        import_from_host_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'host': type.IdType(resource_types='HostSystem'),
        })
        import_from_host_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        import_from_host_input_value_validator_list = [
        ]
        import_from_host_output_validator_list = [
        ]
        import_from_host_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/enablement/configuration/transition',
            request_body_parameter='host',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'importFromHost',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for export_config operation
        export_config_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        export_config_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        export_config_input_value_validator_list = [
        ]
        export_config_output_validator_list = [
        ]
        export_config_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/enablement/configuration/transition',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'exportConfig',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for export_schema operation
        export_schema_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        export_schema_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        export_schema_input_value_validator_list = [
        ]
        export_schema_output_validator_list = [
        ]
        export_schema_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/enablement/configuration/transition',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'exportSchema',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for validate_config operation
        validate_config_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        validate_config_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        validate_config_input_value_validator_list = [
        ]
        validate_config_output_validator_list = [
        ]
        validate_config_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/enablement/configuration/transition',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'validateConfig',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for precheck operation
        precheck_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        precheck_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        precheck_input_value_validator_list = [
        ]
        precheck_output_validator_list = [
        ]
        precheck_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/enablement/configuration/transition',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'precheck',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for enable operation
        enable_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        enable_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        enable_input_value_validator_list = [
        ]
        enable_output_validator_list = [
        ]
        enable_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/enablement/configuration/transition',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'enable',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Transition.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'check_eligibility$task': {
                'input_type': check_eligibility_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': check_eligibility_error_dict,
                'input_value_validator_list': check_eligibility_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'cancel': {
                'input_type': cancel_input_type,
                'output_type': type.VoidType(),
                'errors': cancel_error_dict,
                'input_value_validator_list': cancel_input_value_validator_list,
                'output_validator_list': cancel_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'import_from_file': {
                'input_type': import_from_file_input_type,
                'output_type': type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'DraftImportResult'),
                'errors': import_from_file_error_dict,
                'input_value_validator_list': import_from_file_input_value_validator_list,
                'output_validator_list': import_from_file_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'import_from_host$task': {
                'input_type': import_from_host_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': import_from_host_error_dict,
                'input_value_validator_list': import_from_host_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'export_config': {
                'input_type': export_config_input_type,
                'output_type': type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'ExportResult'),
                'errors': export_config_error_dict,
                'input_value_validator_list': export_config_input_value_validator_list,
                'output_validator_list': export_config_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'export_schema': {
                'input_type': export_schema_input_type,
                'output_type': type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'SchemaResult'),
                'errors': export_schema_error_dict,
                'input_value_validator_list': export_schema_input_value_validator_list,
                'output_validator_list': export_schema_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'validate_config$task': {
                'input_type': validate_config_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': validate_config_error_dict,
                'input_value_validator_list': validate_config_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'precheck$task': {
                'input_type': precheck_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': precheck_error_dict,
                'input_value_validator_list': precheck_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'enable$task': {
                'input_type': enable_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': enable_error_dict,
                'input_value_validator_list': enable_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'check_eligibility': check_eligibility_rest_metadata,
            'cancel': cancel_rest_metadata,
            'import_from_file': import_from_file_rest_metadata,
            'import_from_host': import_from_host_rest_metadata,
            'export_config': export_config_rest_metadata,
            'export_schema': export_schema_rest_metadata,
            'validate_config': validate_config_rest_metadata,
            'precheck': precheck_rest_metadata,
            'enable': enable_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.clusters.enablement.configuration.transition',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Transition': Transition,
    }

