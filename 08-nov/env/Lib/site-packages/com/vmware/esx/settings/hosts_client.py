# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.settings.hosts.
#---------------------------------------------------------------------------

"""
The ``com.vmware.esx.settings.hosts_client`` module provides classes to manage
desired state configuration and software for a standalone ESX host.

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


class Configuration(VapiInterface):
    """
    The ``Configuration`` class provides methods to manage configuration of a
    ESX host. This class was added in vSphere API 8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.configuration'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ConfigurationStub)
        self._VAPI_OPERATION_IDS = {}

    class ExtractResult(VapiStruct):
        """
        The ``Info`` class defines the information about configuration extracted
        from a ESXi host. This class was added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     config=None,
                    ):
            """
            :type  config: :class:`str`
            :param config: ESXi host configuration encoded as JSON. This attribute was added
                in vSphere API 8.0.1.0.
            """
            self.config = config
            VapiStruct.__init__(self)


    ExtractResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.configuration.extract_result', {
            'config': type.StringType(),
        },
        ExtractResult,
        False,
        None))



    def extract(self,
                host,
                ):
        """
        Extracts a configuration document from the ESXi host,. This method was
        added in vSphere API 8.0.1.0.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`Configuration.ExtractResult`
        :return: The result contains the configuration of the ESXi host encoded as
            JSON.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.Modify``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.ClusterConfiguration.Modify``.
        """
        return self._invoke('extract',
                            {
                            'host': host,
                            })
class DepotOverrides(VapiInterface):
    """
    The ``DepotOverrides`` class provides methods to manage software depots
    overriden for a given host. In general ESX servers reach out to vCenter
    (VUM) to fetch the metadata and payloads required for lifecycle operations.
    But in ROBO environments ESX hosts can't (or because of bandwidth
    requirements shouldn't) reach out to vCenter to fetch payloads and
    metadata. This class allows setting host level overrides for depots. If any
    depots are provided for a host, then vCenter level depots are not used for
    that host's remediation. These are not synced periodically at vCenter and
    are only used by ESXs for lifecycle operations. This class was added in
    vSphere API 8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.depot_overrides'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _DepotOverridesStub)
        self._VAPI_OPERATION_IDS = {}

    class Info(VapiStruct):
        """
        The ``DepotOverrides.Info`` class defines the information regarding depot
        overrides for a given host. This class was added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     depots=None,
                    ):
            """
            :type  depots: :class:`list` of :class:`DepotOverrides.Depot`
            :param depots: List of the depot overrides. This attribute was added in vSphere
                API 8.0.1.0.
            """
            self.depots = depots
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.depot_overrides.info', {
            'depots': type.ListType(type.ReferenceType(__name__, 'DepotOverrides.Depot')),
        },
        Info,
        False,
        None))


    class Depot(VapiStruct):
        """
        The ``DepotOverrides.Depot`` class defines the information regarding a
        particular depot override for a given host. This class was added in vSphere
        API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     location=None,
                    ):
            """
            :type  location: :class:`str`
            :param location: Location of the depot override. This could be a location of zip
                file or location to an index.xml file. This attribute was added in
                vSphere API 8.0.1.0.
            """
            self.location = location
            VapiStruct.__init__(self)


    Depot._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.depot_overrides.depot', {
            'location': type.URIType(),
        },
        Depot,
        False,
        None))



    def get(self,
            host,
            ):
        """
        Returns the information about currently configured depot overrides for
        a given host. This method was added in vSphere API 8.0.1.0.

        :type  host: :class:`str`
        :param host: Identifier for the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`DepotOverrides.Info`
        :return: Information about currently configured depot overrides for a given
            host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleSettings.Read``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSettings.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            })

    def add(self,
            host,
            depot,
            ):
        """
        Adds a new depot override to the list of currently configured depot
        overrides for a given host. 
        
        **Warning:** Using HTTP is not secure. Please use HTTPS URLs instead..
        This method was added in vSphere API 8.0.1.0.

        :type  host: :class:`str`
        :param host: Identifier for the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  depot: :class:`DepotOverrides.Depot`
        :param depot: Information of a depot override.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If an invalid location is provided.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if depot override with given information already exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSettings.Write``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSettings.Write``.
        """
        return self._invoke('add',
                            {
                            'host': host,
                            'depot': depot,
                            })

    def remove(self,
               host,
               depot,
               ):
        """
        Removes a depot override from the list of currently configured depot
        overrides for a given host. This method was added in vSphere API
        8.0.1.0.

        :type  host: :class:`str`
        :param host: Identifier for the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  depot: :class:`DepotOverrides.Depot`
        :param depot: Information of the depot override to be removed.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no depot override with given information or no host
            associated with identifier {param.name host} in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSettings.Write``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSettings.Write``.
        """
        return self._invoke('remove',
                            {
                            'host': host,
                            'depot': depot,
                            })
class Software(VapiInterface):
    """
    The ``Software`` class provides methods to manage desired software
    specification of a standalone ESX host.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SoftwareStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'scan_task': 'scan$task'})
        self._VAPI_OPERATION_IDS.update({'stage_task': 'stage$task'})
        self._VAPI_OPERATION_IDS.update({'apply_task': 'apply$task'})
        self._VAPI_OPERATION_IDS.update({'check_task': 'check$task'})

    class ExportType(Enum):
        """
        The ``Software.ExportType`` class defines the formats in which software
        specification document or image can be exported. This enumeration was added
        in vSphere API 8.0.0.1.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        SOFTWARE_SPEC = None
        """
        Export software specification document. This class attribute was added in
        vSphere API 8.0.0.1.

        """
        ISO_IMAGE = None
        """
        Export ISO image. This class attribute was added in vSphere API 8.0.0.1.

        """
        OFFLINE_BUNDLE = None
        """
        Export offline bundle. This class attribute was added in vSphere API
        8.0.0.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ExportType` instance.
            """
            Enum.__init__(string)

    ExportType._set_values({
        'SOFTWARE_SPEC': ExportType('SOFTWARE_SPEC'),
        'ISO_IMAGE': ExportType('ISO_IMAGE'),
        'OFFLINE_BUNDLE': ExportType('OFFLINE_BUNDLE'),
    })
    ExportType._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.hosts.software.export_type',
        ExportType))


    class Status(Enum):
        """
        The ``Software.Status`` class defines the status result for a particular
        check. This enumeration was added in vSphere API 8.0.0.1.

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
        RETRY = None
        """
        The check failed because of an intermittent error, for example a service is
        overloaded. The client can choose to retry the health check before
        considering the check as failed. This class attribute was added in vSphere
        API 8.0.0.1.

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
        'RETRY': Status('RETRY'),
    })
    Status._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.hosts.software.status',
        Status))


    class ExportSpec(VapiStruct):
        """
        The ``Software.ExportSpec`` class contains information describing how a
        software specification or image should be exported. This class was added in
        vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     export_software_spec=None,
                     export_iso_image=None,
                     export_offline_bundle=None,
                    ):
            """
            :type  export_software_spec: :class:`bool`
            :param export_software_spec: Whether to export software specification document. This attribute
                was added in vSphere API 8.0.0.1.
            :type  export_iso_image: :class:`bool`
            :param export_iso_image: Whether to export ISO image. This attribute was added in vSphere
                API 8.0.0.1.
            :type  export_offline_bundle: :class:`bool`
            :param export_offline_bundle: Whether to export offline bundle. This attribute was added in
                vSphere API 8.0.0.1.
            """
            self.export_software_spec = export_software_spec
            self.export_iso_image = export_iso_image
            self.export_offline_bundle = export_offline_bundle
            VapiStruct.__init__(self)


    ExportSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.export_spec', {
            'export_software_spec': type.BooleanType(),
            'export_iso_image': type.BooleanType(),
            'export_offline_bundle': type.BooleanType(),
        },
        ExportSpec,
        False,
        None))


    class StageSpec(VapiStruct):
        """
        The ``Software.StageSpec`` class contains attributes that describe the
        specification to be used for staging the desired software document to a
        host. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     commit=None,
                    ):
            """
            :type  commit: :class:`str` or ``None``
            :param commit: The minimum commit identifier of the desired software document to
                be used during the :func:`Software.stage` method. This attribute
                was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
                if None or empty the stage method will use the latest commit to
                fetch the desired state document.
            """
            self.commit = commit
            VapiStruct.__init__(self)


    StageSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.stage_spec', {
            'commit': type.OptionalType(type.IdType()),
        },
        StageSpec,
        False,
        None))


    class ApplySpec(VapiStruct):
        """
        The ``Software.ApplySpec`` class contains attributes that describe the
        specification to be used for applying the desired software document to a
        host. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     commit=None,
                     accept_eula=None,
                    ):
            """
            :type  commit: :class:`str` or ``None``
            :param commit: The minimum commit identifier of the desired software document to
                be used during the :func:`Software.apply` method. This attribute
                was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
                if None or empty the apply method will use the latest commit to
                fetch the desired state document.
            :type  accept_eula: :class:`bool` or ``None``
            :param accept_eula: Accept the VMware End User License Agreement (EULA) before starting
                the :func:`Software.apply` method. The VMware EULA is available for
                download at, https://www.vmware.com/download/eula.html. This
                attribute was added in vSphere API 8.0.0.1.
                if None the :func:`Software.apply` method could fail due to the
                EULA not being accepted.
            """
            self.commit = commit
            self.accept_eula = accept_eula
            VapiStruct.__init__(self)


    ApplySpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.apply_spec', {
            'commit': type.OptionalType(type.IdType()),
            'accept_eula': type.OptionalType(type.BooleanType()),
        },
        ApplySpec,
        False,
        None))


    class StageStatus(VapiStruct):
        """
        The ``Software.StageStatus`` class contains attributes that describe the
        status of a :func:`Software.stage` method. This class was added in vSphere
        API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'status',
                {
                    'RUNNING' : [('progress', False)],
                    'RETRY_PENDING' : [('progress', False)],
                    'OK' : [('progress', False)],
                    'ERROR' : [('progress', False)],
                    'SKIPPED' : [],
                    'TIMED_OUT' : [],
                }
            ),
        ]



        def __init__(self,
                     status=None,
                     progress=None,
                     start_time=None,
                     end_time=None,
                     notifications=None,
                    ):
            """
            :type  status: :class:`Software.StageStatus.Status`
            :param status: The status of the method. This attribute was added in vSphere API
                8.0.0.1.
            :type  progress: :class:`com.vmware.cis.task_client.Progress` or ``None``
            :param progress: Progress of the operation. This attribute was added in vSphere API
                8.0.0.1.
                None for host StageStatus
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
            self.progress = progress
            self.start_time = start_time
            self.end_time = end_time
            self.notifications = notifications
            VapiStruct.__init__(self)


        class Status(Enum):
            """
            The ``Software.StageStatus.Status`` class contains the possible different
            status codes that can be returned while trying to :func:`Software.stage`
            the desired software specification to a host. This enumeration was added in
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
            RUNNING = None
            """
            The method is in progress. This class attribute was added in vSphere API
            8.0.0.1.

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
            RETRY_PENDING = None
            """
            The method is being scheduled for retry. This class attribute was added in
            vSphere API 8.0.0.1.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Status` instance.
                """
                Enum.__init__(string)

        Status._set_values({
            'RUNNING': Status('RUNNING'),
            'OK': Status('OK'),
            'SKIPPED': Status('SKIPPED'),
            'TIMED_OUT': Status('TIMED_OUT'),
            'ERROR': Status('ERROR'),
            'RETRY_PENDING': Status('RETRY_PENDING'),
        })
        Status._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.hosts.software.stage_status.status',
            Status))

    StageStatus._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.stage_status', {
            'status': type.ReferenceType(__name__, 'Software.StageStatus.Status'),
            'progress': type.OptionalType(type.ReferenceType('com.vmware.cis.task_client', 'Progress')),
            'start_time': type.DateTimeType(),
            'end_time': type.DateTimeType(),
            'notifications': type.ReferenceType('com.vmware.esx.settings_client', 'Notifications'),
        },
        StageStatus,
        False,
        None))


    class ApplyStatus(VapiStruct):
        """
        The ``Software.ApplyStatus`` class contains attributes that describe the
        status of an :func:`Software.apply` method. This class was added in vSphere
        API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'status',
                {
                    'RUNNING' : [('progress', False)],
                    'RETRY_PENDING' : [('progress', False)],
                    'OK' : [('progress', False)],
                    'ERROR' : [('progress', False)],
                    'SKIPPED' : [],
                    'TIMED_OUT' : [],
                }
            ),
        ]



        def __init__(self,
                     status=None,
                     progress=None,
                     start_time=None,
                     end_time=None,
                     notifications=None,
                    ):
            """
            :type  status: :class:`Software.ApplyStatus.Status`
            :param status: The status of the method. This attribute was added in vSphere API
                8.0.0.1.
            :type  progress: :class:`com.vmware.cis.task_client.Progress` or ``None``
            :param progress: Progress of the operation. This attribute was added in vSphere API
                8.0.0.1.
                None for host ApplyStatus
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
            self.progress = progress
            self.start_time = start_time
            self.end_time = end_time
            self.notifications = notifications
            VapiStruct.__init__(self)


        class Status(Enum):
            """
            The ``Software.ApplyStatus.Status`` class contains the possible different
            status codes that can be returned while trying to :func:`Software.apply`
            the desired software specification to host. This enumeration was added in
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
            RUNNING = None
            """
            The method is in progress. This class attribute was added in vSphere API
            8.0.0.1.

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
            RETRY_PENDING = None
            """
            The method is being scheduled for retry. This class attribute was added in
            vSphere API 8.0.0.1.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Status` instance.
                """
                Enum.__init__(string)

        Status._set_values({
            'RUNNING': Status('RUNNING'),
            'OK': Status('OK'),
            'SKIPPED': Status('SKIPPED'),
            'TIMED_OUT': Status('TIMED_OUT'),
            'ERROR': Status('ERROR'),
            'RETRY_PENDING': Status('RETRY_PENDING'),
        })
        Status._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.hosts.software.apply_status.status',
            Status))

    ApplyStatus._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.apply_status', {
            'status': type.ReferenceType(__name__, 'Software.ApplyStatus.Status'),
            'progress': type.OptionalType(type.ReferenceType('com.vmware.cis.task_client', 'Progress')),
            'start_time': type.DateTimeType(),
            'end_time': type.DateTimeType(),
            'notifications': type.ReferenceType('com.vmware.esx.settings_client', 'Notifications'),
        },
        ApplyStatus,
        False,
        None))


    class StageResult(VapiStruct):
        """
        The ``Software.StageResult`` class contains attributes that describe the
        result of a :func:`Software.stage` method. This class was added in vSphere
        API 8.0.0.1.

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
            :type  status: :class:`Software.StageStatus` or ``None``
            :param status: Specifies the status of the :func:`Software.stage` method on the
                specified :attr:`Software.StageResult.commit` of the desired
                software document. This attribute was added in vSphere API 8.0.0.1.
                None if the :func:`Software.stage` method is in progress.
            :type  commit: :class:`str`
            :param commit: The identifier of the commit used to fetch the desired software
                document to be staged to a host. This attribute was added in
                vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  host_info: :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information of the host to which the desired software document
                specified by the :attr:`Software.StageResult.commit` was staged.
                This attribute was added in vSphere API 8.0.0.1.
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
            :param notifications: Notifications providing additional information for
                :func:`Software.stage` method. These notifications are mutually
                exclusive with the notifications in ``Software.StageStatus``. This
                attribute was added in vSphere API 8.0.0.1.
            """
            self.status = status
            self.commit = commit
            self.host_info = host_info
            self.notifications = notifications
            VapiStruct.__init__(self)


    StageResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.stage_result', {
            'status': type.OptionalType(type.ReferenceType(__name__, 'Software.StageStatus')),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo'),
            'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        StageResult,
        False,
        None))


    class ApplyResult(VapiStruct):
        """
        The ``Software.ApplyResult`` class contains attributes that describe the
        result of an :func:`Software.apply` method. This class was added in vSphere
        API 8.0.0.1.

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
            :type  status: :class:`Software.ApplyStatus` or ``None``
            :param status: Specifies the aggregated status of the :func:`Software.apply`
                method. This attribute was added in vSphere API 8.0.0.1.
                None if the :func:`Software.apply` method is in progress.
            :type  commit: :class:`str`
            :param commit: The identifier of the commit used to fetch the desired software
                document to be applied to host. This attribute was added in vSphere
                API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  host_info: :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information of the host to which the desired software document
                specified by the :attr:`Software.ApplyResult.commit` was applied.
                This attribute was added in vSphere API 8.0.0.1.
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
            :param notifications: Notifications providing additional information for
                :func:`Software.apply` method. These notifications are mutually
                exclusive with the notifications in ``Software.ApplyStatus``. This
                attribute was added in vSphere API 8.0.0.1.
            """
            self.status = status
            self.commit = commit
            self.host_info = host_info
            self.notifications = notifications
            VapiStruct.__init__(self)


    ApplyResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.apply_result', {
            'status': type.OptionalType(type.ReferenceType(__name__, 'Software.ApplyStatus')),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo'),
            'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        ApplyResult,
        False,
        None))


    class CheckSpec(VapiStruct):
        """
        The ``Software.CheckSpec`` class contains attributes that describe the
        specification to be used for running checks on the host before the
        :func:`Software.apply` method. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     commit=None,
                    ):
            """
            :type  commit: :class:`str` or ``None``
            :param commit: The minimum commit identifier of the desired software document to
                be used during the check method. This attribute was added in
                vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
                if None or empty the check opertion will use the latest commit to
                fetch the desired state document.
            """
            self.commit = commit
            VapiStruct.__init__(self)


    CheckSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.check_spec', {
            'commit': type.OptionalType(type.IdType()),
        },
        CheckSpec,
        False,
        None))


    class CheckInfo(VapiStruct):
        """
        The ``Software.CheckInfo`` class contains attributes that describe a
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
        'com.vmware.esx.settings.hosts.software.check_info', {
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
            :param description: Description of what was the issue containing as much user-relevant
                context as possible. The user should be able to understand which
                sub-system failed and why. This attribute was added in vSphere API
                8.0.0.1.
            :type  resolution: :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param resolution: Possible resolution for the issue. This should contain actionable
                information that the user can use to resolve the issue. This
                attribute was added in vSphere API 8.0.0.1.
                Can be left None if no meaningful resolution exists.
            """
            self.description = description
            self.resolution = resolution
            VapiStruct.__init__(self)


    CheckIssue._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.check_issue', {
            'description': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
            'resolution': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        CheckIssue,
        False,
        None))


    class CheckStatus(VapiStruct):
        """
        The ``Software.CheckStatus`` class contains attributes that describe a
        check result. This class was added in vSphere API 8.0.0.1.

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
            :type  check: :class:`Software.CheckInfo`
            :param check: Information about this check. This attribute was added in vSphere
                API 8.0.0.1.
            :type  status: :class:`Software.Status`
            :param status: The status of this check. This attribute was added in vSphere API
                8.0.0.1.
            :type  check_issues: :class:`list` of :class:`Software.CheckIssue` or ``None``
            :param check_issues: List of :class:`Software.CheckIssue`s that the check reported. This
                attribute was added in vSphere API 8.0.0.1.
                If not :class:`set`, the service is still using the {#member
                issues}.
            """
            self.check = check
            self.status = status
            self.check_issues = check_issues
            VapiStruct.__init__(self)


    CheckStatus._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.check_status', {
            'check': type.ReferenceType(__name__, 'Software.CheckInfo'),
            'status': type.ReferenceType(__name__, 'Software.Status'),
            'check_issues': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Software.CheckIssue'))),
        },
        CheckStatus,
        False,
        None))


    class EntityCheckResult(VapiStruct):
        """
        The ``Software.EntityCheckResult`` class contains attributes that describe
        aggregated status of all checks performed on a specific entity. This class
        was added in vSphere API 8.0.0.1.

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
            :type  type: :class:`Software.EntityCheckResult.EntityType`
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
                of ``type`` is :attr:`Software.EntityCheckResult.EntityType.HOST`.
            :type  status: :class:`Software.Status`
            :param status: Aggregated status from all checks performed on this entity. This
                attribute was added in vSphere API 8.0.0.1.
            :type  check_statuses: :class:`list` of :class:`Software.CheckStatus`
            :param check_statuses: List of ``Software.CheckStatus`` for all checks performed. This
                attribute was added in vSphere API 8.0.0.1.
            """
            self.type = type
            self.host = host
            self.status = status
            self.check_statuses = check_statuses
            VapiStruct.__init__(self)


        class EntityType(Enum):
            """
            The ``Software.EntityCheckResult.EntityType`` class contains the entitites
            on which checks can be performed. This enumeration was added in vSphere API
            8.0.0.1.

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
            'com.vmware.esx.settings.hosts.software.entity_check_result.entity_type',
            EntityType))

    EntityCheckResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.entity_check_result', {
            'type': type.ReferenceType(__name__, 'Software.EntityCheckResult.EntityType'),
            'host': type.OptionalType(type.IdType()),
            'status': type.ReferenceType(__name__, 'Software.Status'),
            'check_statuses': type.ListType(type.ReferenceType(__name__, 'Software.CheckStatus')),
        },
        EntityCheckResult,
        False,
        None))


    class CheckResult(VapiStruct):
        """
        The ``Software.CheckResult`` class contains attributes that describe
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
            :type  status: :class:`Software.Status`
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
            :type  entity_result: :class:`Software.EntityCheckResult`
            :param entity_result: List of ``Software.EntityCheckResult`` for all entities for which
                checks have been run. This attribute was added in vSphere API
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
        'com.vmware.esx.settings.hosts.software.check_result', {
            'status': type.ReferenceType(__name__, 'Software.Status'),
            'start_time': type.DateTimeType(),
            'end_time': type.DateTimeType(),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo'),
            'entity_result': type.ReferenceType(__name__, 'Software.EntityCheckResult'),
        },
        CheckResult,
        False,
        None))




    def scan_task(self,
             host,
             ):
        """
        Scans the host against the host's desired state.. The result of this
        operation can be queried by calling the cis/tasks/{task-id} where the
        task-id is the response of this operation.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system or if
            desired software document is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        """
        task_id = self._invoke('scan$task',
                                {
                                'host': host,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType('com.vmware.esx.settings_client', 'HostCompliance'))
        return task_instance

    def get(self,
            host,
            ):
        """
        Returns the complete desired software specification. This method was
        added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`com.vmware.esx.settings_client.SoftwareInfo`
        :return: Host software specification.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            })

    def export(self,
               host,
               spec,
               ):
        """
        Exports the desired software specification document and/or image. This
        API will not export the solution section of the desired software
        specification. This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  spec: :class:`Software.ExportSpec`
        :param spec: 
        :rtype: :class:`dict` of :class:`Software.ExportType` and :class:`str`
        :return: A map from export type to URL of the exported data for that type.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is am unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system or if
            desired software document is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
        """
        return self._invoke('export',
                            {
                            'host': host,
                            'spec': spec,
                            })


    def stage_task(self,
              host,
              spec,
              ):
        """
        Stages the desired software document associated with the given host. If
        ``commit`` attribute is :class:`set`, it implies the minimum commit
        that the :func:`Software.stage` method should use, however if
        subsequent commits have been made to the desired state document the
        stage method will use the most recent desired state document. The
        result of this operation can be queried by calling the
        cis/tasks/{task-id} where the task-id is the response of this
        operation. This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  spec: :class:`Software.StageSpec`
        :param spec: stage specification.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the ``commit`` attribute of ``spec`` specifies an invalid
            commit, or the ``StageSpec#hosts`` attribute of ``spec`` specifies
            an invalid host or the ``host`` is not managed with a single
            software specification.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If there is another operation in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system or if
            desired software document is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.TimedOut` 
            If the operation times out.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host
        """
        task_id = self._invoke('stage$task',
                                {
                                'host': host,
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Software.StageResult'))
        return task_instance


    def apply_task(self,
              host,
              spec,
              ):
        """
        Applies the desired software document associated with the given host.
        If ``commit`` attribute is :class:`set`, it implies the minimum commit
        that the :func:`Software.apply` method should use, however if
        subsequent commits have been made to the desired state document the
        apply method will use the most recent desired state document. The
        result of this operation can be queried by calling the
        cis/tasks/{task-id} where the task-id is the response of this
        operation. This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  spec: :class:`Software.ApplySpec`
        :param spec: Apply specification.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyInDesiredState` 
            If the host is already at specified commit as described in the
            apply specification.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error or if the EULA has not been
            accepted. The accompanying error message will give more details
            about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the ``commit`` attribute of ``spec`` specifies an invalid
            commit.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If there is another operation in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system or if
            desired software document is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.TimedOut` 
            If the operation times out.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        """
        task_id = self._invoke('apply$task',
                                {
                                'host': host,
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Software.ApplyResult'))
        return task_instance


    def check_task(self,
              host,
              spec,
              ):
        """
        Runs checks on the host before applying the desired software document.
        Checks if host is in a good state to be updated with the desired
        software document. If ``commit`` attribute is :class:`set` it implies
        the minimum commit that the check method should use, however if
        subsequent commits have been made to the desired state document the
        check method will use the most recent desired state document. The
        result of this operation can be queried by calling the
        cis/tasks/{task-id} where the task-id is the response of this
        operation. This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  spec: :class:`Software.CheckSpec`
        :param spec: Check specification.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the ``commit`` attribute of ``spec`` specifies an invalid
            commit.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If there is another operation in progress or if the ``commit``
            attribute of ``spec`` specifies a commit that has already been
            applied.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.TimedOut` 
            If the operation times out.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        """
        task_id = self._invoke('check$task',
                                {
                                'host': host,
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Software.CheckResult'))
        return task_instance
class _ConfigurationStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for extract operation
        extract_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
        })
        extract_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        extract_input_value_validator_list = [
        ]
        extract_output_validator_list = [
        ]
        extract_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/configuration',
            path_variables={
                'host': 'host',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'extract',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'extract': {
                'input_type': extract_input_type,
                'output_type': type.ReferenceType(__name__, 'Configuration.ExtractResult'),
                'errors': extract_error_dict,
                'input_value_validator_list': extract_input_value_validator_list,
                'output_validator_list': extract_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'extract': extract_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.configuration',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _DepotOverridesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/hosts/{host}/depot-overrides',
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

        # properties for add operation
        add_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'depot': type.ReferenceType(__name__, 'DepotOverrides.Depot'),
        })
        add_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        add_input_value_validator_list = [
        ]
        add_output_validator_list = [
        ]
        add_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/depot-overrides',
            request_body_parameter='depot',
            path_variables={
                'host': 'host',
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
            'host': type.IdType(resource_types='HostSystem'),
            'depot': type.ReferenceType(__name__, 'DepotOverrides.Depot'),
        })
        remove_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        remove_input_value_validator_list = [
        ]
        remove_output_validator_list = [
        ]
        remove_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/depot-overrides',
            request_body_parameter='depot',
            path_variables={
                'host': 'host',
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

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'DepotOverrides.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'add': {
                'input_type': add_input_type,
                'output_type': type.VoidType(),
                'errors': add_error_dict,
                'input_value_validator_list': add_input_value_validator_list,
                'output_validator_list': add_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'remove': {
                'input_type': remove_input_type,
                'output_type': type.VoidType(),
                'errors': remove_error_dict,
                'input_value_validator_list': remove_input_value_validator_list,
                'output_validator_list': remove_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'add': add_rest_metadata,
            'remove': remove_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.depot_overrides',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _SoftwareStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for scan operation
        scan_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
        })
        scan_error_dict = {
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
        scan_input_value_validator_list = [
        ]
        scan_output_validator_list = [
        ]
        scan_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/software',
            path_variables={
                'host': 'host',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'scan',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

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
            url_template='/esx/settings/hosts/{host}/software',
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

        # properties for export operation
        export_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'spec': type.ReferenceType(__name__, 'Software.ExportSpec'),
        })
        export_error_dict = {
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
        export_input_value_validator_list = [
        ]
        export_output_validator_list = [
        ]
        export_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/software',
            request_body_parameter='spec',
            path_variables={
                'host': 'host',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'export',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for stage operation
        stage_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'spec': type.ReferenceType(__name__, 'Software.StageSpec'),
        })
        stage_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.timed_out':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'TimedOut'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        stage_input_value_validator_list = [
        ]
        stage_output_validator_list = [
        ]
        stage_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/software',
            request_body_parameter='spec',
            path_variables={
                'host': 'host',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'stage',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for apply operation
        apply_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'spec': type.ReferenceType(__name__, 'Software.ApplySpec'),
        })
        apply_error_dict = {
            'com.vmware.vapi.std.errors.already_in_desired_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyInDesiredState'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.timed_out':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'TimedOut'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        apply_input_value_validator_list = [
        ]
        apply_output_validator_list = [
        ]
        apply_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/software',
            request_body_parameter='spec',
            path_variables={
                'host': 'host',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'apply',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for check operation
        check_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'spec': type.ReferenceType(__name__, 'Software.CheckSpec'),
        })
        check_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.timed_out':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'TimedOut'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        check_input_value_validator_list = [
        ]
        check_output_validator_list = [
        ]
        check_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/software',
            request_body_parameter='spec',
            path_variables={
                'host': 'host',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'check',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'scan$task': {
                'input_type': scan_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': scan_error_dict,
                'input_value_validator_list': scan_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType('com.vmware.esx.settings_client', 'SoftwareInfo'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'export': {
                'input_type': export_input_type,
                'output_type': type.MapType(type.ReferenceType(__name__, 'Software.ExportType'), type.URIType()),
                'errors': export_error_dict,
                'input_value_validator_list': export_input_value_validator_list,
                'output_validator_list': export_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'stage$task': {
                'input_type': stage_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': stage_error_dict,
                'input_value_validator_list': stage_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'apply$task': {
                'input_type': apply_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': apply_error_dict,
                'input_value_validator_list': apply_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'check$task': {
                'input_type': check_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': check_error_dict,
                'input_value_validator_list': check_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
        }
        rest_metadata = {
            'scan': scan_rest_metadata,
            'get': get_rest_metadata,
            'export': export_rest_metadata,
            'stage': stage_rest_metadata,
            'apply': apply_rest_metadata,
            'check': check_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.software',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Configuration': Configuration,
        'DepotOverrides': DepotOverrides,
        'Software': Software,
        'enablement': 'com.vmware.esx.settings.hosts.enablement_client.StubFactory',
        'policies': 'com.vmware.esx.settings.hosts.policies_client.StubFactory',
        'software': 'com.vmware.esx.settings.hosts.software_client.StubFactory',
    }

