# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.settings.hosts.software.
#---------------------------------------------------------------------------

"""
The ``com.vmware.esx.settings.hosts.software_client`` module provides classes
to manage desired software on a standalone host.

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


class AddOn(VapiInterface):
    """
    The ``AddOn`` class provides methods to manage desired OEM add-on
    specification for a given standalone host. This class was added in vSphere
    API 8.0.0.1.
    """
    RESOURCE_TYPE = "com.vmware.esx.settings.add_on"
    """
    Resource type for add-on resource. This class attribute was added in vSphere
    API 8.0.0.1.

    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.add_on'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _AddOnStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            host,
            ):
        """
        Returns the desired OEM add-on specification for a given host. This
        method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`com.vmware.esx.settings_client.AddOnInfo`
        :return: Desired OEM add-on specification.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system or if
            desired OEM add-on specification is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
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
class BaseImage(VapiInterface):
    """
    The ``BaseImage`` class provides methods to manage desired ESX base image.
    This class was added in vSphere API 8.0.0.1.
    """
    RESOURCE_TYPE = "com.vmware.esx.settings.base_image"
    """
    Resource type for base-image resource. This class attribute was added in
    vSphere API 8.0.0.1.

    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.base_image'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _BaseImageStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            host,
            ):
        """
        Returns the desired base-image specification set for given host. This
        method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`com.vmware.esx.settings_client.BaseImageInfo`
        :return: Base-image specification.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
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
              ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            })
class Commits(VapiInterface):
    """
    The ``Commits`` class provides methods to manage committed changes to
    desired software document. This class was added in vSphere API 8.0.0.1.
    """
    RESOURCE_TYPE = "com.vmware.esx.settings.commit"
    """
    Resource type for commit resource. This class attribute was added in vSphere
    API 8.0.0.1.

    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.commits'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _CommitsStub)
        self._VAPI_OPERATION_IDS = {}

    class ApplyStatusType(Enum):
        """
        The ``Commits.ApplyStatusType`` class defines possible values regarding the
        application of this commit. This enumeration was added in vSphere API
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
        APPLIED = None
        """
        Commit has been applied to the host. This class attribute was added in
        vSphere API 8.0.0.1.

        """
        NOT_APPLIED = None
        """
        Commit hasn't been applied to the host. This class attribute was added in
        vSphere API 8.0.0.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ApplyStatusType` instance.
            """
            Enum.__init__(string)

    ApplyStatusType._set_values({
        'APPLIED': ApplyStatusType('APPLIED'),
        'NOT_APPLIED': ApplyStatusType('NOT_APPLIED'),
    })
    ApplyStatusType._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.hosts.software.commits.apply_status_type',
        ApplyStatusType))


    class Info(VapiStruct):
        """
        The ``Commits.Info`` class defines the information about software draft.
        This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     author=None,
                     commit_time=None,
                     description=None,
                     apply_status=None,
                    ):
            """
            :type  author: :class:`str`
            :param author: Author of the commit. This attribute was added in vSphere API
                8.0.0.1.
            :type  commit_time: :class:`datetime.datetime`
            :param commit_time: Creation time of the commit. This attribute was added in vSphere
                API 8.0.0.1.
            :type  description: :class:`str`
            :param description: Description accompanying this commit. This attribute was added in
                vSphere API 8.0.0.1.
            :type  apply_status: :class:`Commits.ApplyStatusType`
            :param apply_status: Apply status of the commit. This attribute was added in vSphere API
                8.0.0.1.
            """
            self.author = author
            self.commit_time = commit_time
            self.description = description
            self.apply_status = apply_status
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.commits.info', {
            'author': type.StringType(),
            'commit_time': type.DateTimeType(),
            'description': type.StringType(),
            'apply_status': type.ReferenceType(__name__, 'Commits.ApplyStatusType'),
        },
        Info,
        False,
        None))



    def get(self,
            host,
            commit,
            ):
        """
        Returns the information about a specific commit. This method was added
        in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  commit: :class:`str`
        :param commit: Identifier of the specific commit.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.commit``.
        :rtype: :class:`Commits.Info`
        :return: Information about the commit.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system or if
            working copy of the software document is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
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
                            'commit': commit,
                            })
class Compliance(VapiInterface):
    """
    The ``Compliance`` class provides methods to get compliance results for a
    standalone host. This class was added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.compliance'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ComplianceStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            host,
            ):
        """
        Returns the compliance state for the host. This method was added in
        vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`com.vmware.esx.settings_client.HostCompliance`
        :return: Host compliance result.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
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
              ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            })
class Components(VapiInterface):
    """
    The ``Components`` class provides methods to manage desired component
    specification for a standalone ESX host. This class was added in vSphere
    API 8.0.0.1.
    """
    RESOURCE_TYPE = "com.vmware.esx.settings.component"
    """
    Resource type for component resource. This class attribute was added in vSphere
    API 8.0.0.1.

    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.components'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ComponentsStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            host,
            component,
            ):
        """
        Returns the component version for the given component in the desired
        software specification. This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  component: :class:`str`
        :param component: Identifier of the component.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.component``.
        :rtype: :class:`com.vmware.esx.settings_client.ComponentInfo` or ``None``
        :return: Details about the component version.
            If None then version is supposed to be chosen based on the
            constraints in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system or or no
            component associated with ``component`` in the system.
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
                            'component': component,
                            })

    def list(self,
             host,
             ):
        """
        Returns a list of components in the desired software specification.
        This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.ComponentInfo`
        :return: Map of ComponentInfo keyed by the component identifier. If no
            version is specified in desired software specification, then it
            will be empty.
            The key in the return value :class:`dict` will be an identifier for
            the resource type: ``com.vmware.esx.settings.component``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
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
        return self._invoke('list',
                            {
                            'host': host,
                            })
class Drafts(VapiInterface):
    """
    The ``Drafts`` class provides methods to manage working copy of software
    documents. This class was added in vSphere API 8.0.0.1.
    """
    RESOURCE_TYPE = "com.vmware.esx.settings.draft"
    """
    Resource type for draft resource. This class attribute was added in vSphere API
    8.0.0.1.

    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.drafts'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _DraftsStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'commit_task': 'commit$task'})
        self._VAPI_OPERATION_IDS.update({'validate_task': 'validate$task'})
        self._VAPI_OPERATION_IDS.update({'scan_task': 'scan$task'})

    class StatusType(Enum):
        """
        The ``Drafts.StatusType`` class defines possible values of status of a
        software draft. This enumeration was added in vSphere API 8.0.0.1.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        VALID = None
        """
        Software draft is valid. This class attribute was added in vSphere API
        8.0.0.1.

        """
        INVALID = None
        """
        Software draft is invalid. This class attribute was added in vSphere API
        8.0.0.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`StatusType` instance.
            """
            Enum.__init__(string)

    StatusType._set_values({
        'VALID': StatusType('VALID'),
        'INVALID': StatusType('INVALID'),
    })
    StatusType._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.hosts.software.drafts.status_type',
        StatusType))


    class SourceType(Enum):
        """
        The ``Drafts.SourceType`` class defines possible values of sources to
        import software specification. This enumeration was added in vSphere API
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
        PULL = None
        """
        Content is pulled from the URL location. The URL scheme of the value in
        {\\\\@link #pullLocation) can be http, https or file. This class attribute
        was added in vSphere API 8.0.0.1.

        """
        PUSH = None
        """
        Content was previously uploaded using the file upload enpoint present on
        vCenter appliance. This endpoint is present at
        https://VCENTERFQDN:9087/vum-fileupload URL. This class attribute was added
        in vSphere API 8.0.0.1.

        """
        JSON_STRING = None
        """
        The string representing the content of the software specfication. This
        class attribute was added in vSphere API 8.0.0.1.

        """
        LATEST_RECOMMENDATION = None
        """
        This class attribute was added in vSphere API 8.0.0.1.

        """
        CURRENT_SERIES_RECOMMENDATION = None
        """
        This class attribute was added in vSphere API 8.0.0.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`SourceType` instance.
            """
            Enum.__init__(string)

    SourceType._set_values({
        'PULL': SourceType('PULL'),
        'PUSH': SourceType('PUSH'),
        'JSON_STRING': SourceType('JSON_STRING'),
        'LATEST_RECOMMENDATION': SourceType('LATEST_RECOMMENDATION'),
        'CURRENT_SERIES_RECOMMENDATION': SourceType('CURRENT_SERIES_RECOMMENDATION'),
    })
    SourceType._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.hosts.software.drafts.source_type',
        SourceType))


    class ValidateResult(VapiStruct):
        """
        The ``Drafts.ValidateResult`` class contains attributes to describe result
        of validation of desired software specification. This class was added in
        vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     notifications=None,
                    ):
            """
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications`
            :param notifications: Notifications associated with the validation. This attribute was
                added in vSphere API 8.0.0.1.
            """
            self.notifications = notifications
            VapiStruct.__init__(self)


    ValidateResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.drafts.validate_result', {
            'notifications': type.ReferenceType('com.vmware.esx.settings_client', 'Notifications'),
        },
        ValidateResult,
        False,
        None))


    class Metadata(VapiStruct):
        """
        The ``Drafts.Metadata`` class defines the metadata information about
        software draft. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     owner=None,
                     status=None,
                     creation_time=None,
                    ):
            """
            :type  owner: :class:`str`
            :param owner: Owner of the software draft. This attribute was added in vSphere
                API 8.0.0.1.
            :type  status: :class:`Drafts.StatusType`
            :param status: Status of the software draft. This attribute was added in vSphere
                API 8.0.0.1.
            :type  creation_time: :class:`datetime.datetime`
            :param creation_time: Creation time of the software draft. This attribute was added in
                vSphere API 8.0.0.1.
            """
            self.owner = owner
            self.status = status
            self.creation_time = creation_time
            VapiStruct.__init__(self)


    Metadata._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.drafts.metadata', {
            'owner': type.StringType(),
            'status': type.ReferenceType(__name__, 'Drafts.StatusType'),
            'creation_time': type.DateTimeType(),
        },
        Metadata,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Drafts.Info`` class defines the information about software draft.
        This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     metadata=None,
                     software=None,
                    ):
            """
            :type  metadata: :class:`Drafts.Metadata`
            :param metadata: Metadata about the software draft. This attribute was added in
                vSphere API 8.0.0.1.
            :type  software: :class:`com.vmware.esx.settings_client.SoftwareInfo`
            :param software: Software specification associated with the draft. This attribute
                was added in vSphere API 8.0.0.1.
            """
            self.metadata = metadata
            self.software = software
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.drafts.info', {
            'metadata': type.ReferenceType(__name__, 'Drafts.Metadata'),
            'software': type.ReferenceType('com.vmware.esx.settings_client', 'SoftwareInfo'),
        },
        Info,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``Drafts.Summary`` class defines the summary information about software
        draft. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     metadata=None,
                    ):
            """
            :type  metadata: :class:`Drafts.Metadata`
            :param metadata: Metadata about the software draft. This attribute was added in
                vSphere API 8.0.0.1.
            """
            self.metadata = metadata
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.drafts.summary', {
            'metadata': type.ReferenceType(__name__, 'Drafts.Metadata'),
        },
        Summary,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``Drafts.FilterSpec`` class contains attributes used to filter the
        results when listing software drafts. See :func:`Drafts.list`. This class
        was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     owners=None,
                    ):
            """
            :type  owners: :class:`set` of :class:`str` or ``None``
            :param owners: Owners of the drafts. This attribute was added in vSphere API
                8.0.0.1.
                If None or empty, drafts from all owners will be returned.
            """
            self.owners = owners
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.drafts.filter_spec', {
            'owners': type.OptionalType(type.SetType(type.StringType())),
        },
        FilterSpec,
        False,
        None))


    class CommitSpec(VapiStruct):
        """
        The ``Drafts.CommitSpec`` class contains attributes that are used to create
        a new commit. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     message=None,
                    ):
            """
            :type  message: :class:`str` or ``None``
            :param message: Message to include with the commit. This attribute was added in
                vSphere API 8.0.0.1.
                If None, message is set to empty string.
            """
            self.message = message
            VapiStruct.__init__(self)


    CommitSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.drafts.commit_spec', {
            'message': type.OptionalType(type.StringType()),
        },
        CommitSpec,
        False,
        None))


    class ImportSpec(VapiStruct):
        """
        The ``Drafts.ImportSpec`` class defines the information used to import the
        desired software specification. This class was added in vSphere API
        8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'source_type',
                {
                    'PULL' : [('location', True)],
                    'PUSH' : [('file_id', True)],
                    'JSON_STRING' : [('software_spec', True)],
                    'LATEST_RECOMMENDATION' : [],
                    'CURRENT_SERIES_RECOMMENDATION' : [],
                }
            ),
        ]



        def __init__(self,
                     source_type=None,
                     location=None,
                     file_id=None,
                     software_spec=None,
                    ):
            """
            :type  source_type: :class:`Drafts.SourceType`
            :param source_type: Type of the source to import the desired software specification.
                This attribute was added in vSphere API 8.0.0.1.
            :type  location: :class:`str`
            :param location: Location of the software specification file to be imported. This
                attribute was added in vSphere API 8.0.0.1.
                This attribute is optional and it is only relevant when the value
                of ``sourceType`` is :attr:`Drafts.SourceType.PULL`.
            :type  file_id: :class:`str`
            :param file_id: File identifier returned by the file upload endpoint after file is
                uploaded. This attribute was added in vSphere API 8.0.0.1.
                This attribute is optional and it is only relevant when the value
                of ``sourceType`` is :attr:`Drafts.SourceType.PUSH`.
            :type  software_spec: :class:`str`
            :param software_spec: The JSON string representing the desired software specification.
                This attribute was added in vSphere API 8.0.0.1.
                This attribute is optional and it is only relevant when the value
                of ``sourceType`` is :attr:`Drafts.SourceType.JSON_STRING`.
            """
            self.source_type = source_type
            self.location = location
            self.file_id = file_id
            self.software_spec = software_spec
            VapiStruct.__init__(self)


    ImportSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.drafts.import_spec', {
            'source_type': type.ReferenceType(__name__, 'Drafts.SourceType'),
            'location': type.OptionalType(type.URIType()),
            'file_id': type.OptionalType(type.StringType()),
            'software_spec': type.OptionalType(type.StringType()),
        },
        ImportSpec,
        False,
        None))




    def commit_task(self,
               host,
               draft,
               spec,
               ):
        """
        Commits the specified draft as the desired state document. The result
        of this operation can be queried by calling the cis/tasks/{task-id}
        where the task-id is the response of this operation. It will also
        validate the document before committing it. This method was added in
        vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  draft: :class:`str`
        :param draft: Identifier of the draft.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :type  spec: :class:`Drafts.CommitSpec`
        :param spec: The spec to be used to create the commit.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If there is another operation in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` or if there is no
            draft associated with ``draft`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If validation of the software document fails. The value of the data
            attribute of :class:`com.vmware.vapi.std.errors_client.Error` will
            be a class that contains all the attributes defined in
            :class:`Drafts.ValidateResult`.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        """
        task_id = self._invoke('commit$task',
                                {
                                'host': host,
                                'draft': draft,
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.IdType(resource_types='com.vmware.esx.settings.commit'))
        return task_instance

    def create(self,
               host,
               ):
        """
        Creates a new software draft from the desired document. It will be
        deleted, when the draft is committed successfully. This method was
        added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`str`
        :return: Identifier of the working copy of the document.
            The return value will be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            If there is already a draft created by this user.
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
              ``VcIntegrity.lifecycleSoftwareSpecification.Write``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSoftwareSpecification.Write``.
        """
        return self._invoke('create',
                            {
                            'host': host,
                            })

    def delete(self,
               host,
               draft,
               ):
        """
        Deletes the software draft. This method was added in vSphere API
        8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  draft: :class:`str`
        :param draft: Identifier of the draft.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` or no draft associated
            with ``draft`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareSpecification.Write``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSoftwareSpecification.Write``.
        """
        return self._invoke('delete',
                            {
                            'host': host,
                            'draft': draft,
                            })

    def get(self,
            host,
            draft,
            ):
        """
        Returns the information about given software draft. This method was
        added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :rtype: :class:`Drafts.Info`
        :return: Information about the Software Draft.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` or no draft associated
            with ``draft`` in the system.
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
                            'draft': draft,
                            })

    def list(self,
             host,
             filter=None,
             ):
        """
        Returns information about the software drafts for the specified host
        that match the :class:`Drafts.FilterSpec`. This method was added in
        vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  filter: :class:`Drafts.FilterSpec` or ``None``
        :param filter: Filter to be applied while returning drafts.
            If None, all drafts will be returned.
        :rtype: :class:`dict` of :class:`str` and :class:`Drafts.Summary`
        :return: Map of software drafts keyed by their identifiers.
            The key in the return value :class:`dict` will be an identifier for
            the resource type: ``com.vmware.esx.settings.draft``.
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
        return self._invoke('list',
                            {
                            'host': host,
                            'filter': filter,
                            })


    def validate_task(self,
                 host,
                 draft,
                 ):
        """
        Validates the software draft. The result of this operation can be
        queried by calling the cis/tasks/{task-id} where the task-id is the
        response of this operation. This method was added in vSphere API
        8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` or no draft associated
            with ``draft`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        """
        task_id = self._invoke('validate$task',
                                {
                                'host': host,
                                'draft': draft,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Drafts.ValidateResult'))
        return task_instance


    def scan_task(self,
             host,
             draft,
             ):
        """
        Scans the host against the software draft. The result of this operation
        can be queried by calling the cis/tasks/{task-id} where the task-id is
        the response of this operation. This method was added in vSphere API
        8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` or no draft associated
            with ``draft`` in the system.
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
                                'draft': draft,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType('com.vmware.esx.settings_client', 'HostCompliance'))
        return task_instance

    def import_software_spec(self,
                             host,
                             spec,
                             ):
        """
        Imports the desired software specification. 
        
        **Warning:** Using HTTP is not secure. Please use HTTPS URLs instead..
        This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  spec: :class:`Drafts.ImportSpec`
        :param spec: Specification to import desired software specification.
        :rtype: :class:`str`
        :return: Identifier of the working copy of the document.
            The return value will be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system or if
            the source type of import specification is of either
            ``LATEST_RECOMMENDATION`` or ``CURRENT_SERIES_RECOMMENDATION``, and
            a recommendation does not exist for the host. It was either never
            generated or deleted due to changes in host state such as a new
            desired image spec being committed.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareSpecification.Write``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSoftwareSpecification.Write``.
        """
        return self._invoke('import_software_spec',
                            {
                            'host': host,
                            'spec': spec,
                            })
class EffectiveComponents(VapiInterface):
    """
    The ``EffectiveComponents`` class provides methods to get effective list of
    components. This class was added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.effective_components'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _EffectiveComponentsStub)
        self._VAPI_OPERATION_IDS = {}


    def list(self,
             host,
             ):
        """
        Returns the effective components for the host. This method was added in
        vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.EffectiveComponentInfo`
        :return: Map of effective components keyed by their identifier.
            The key in the return value :class:`dict` will be an identifier for
            the resource type: ``com.vmware.esx.settings.component``.
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
        return self._invoke('list',
                            {
                            'host': host,
                            })

    def list_with_removed_components(self,
                                     host,
                                     ):
        """
        Returns the list of all the effective components. Pass the param
        "with-removed-components" to get even the removed components. This
        method was added in vSphere API 8.0.3.0.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.EffectiveComponentInfo`
        :return: Map of effective components keyed by their identifier.
            The key in the return value :class:`dict` will be an identifier for
            the resource type: ``com.vmware.esx.settings.component``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the caller does not have the necessary privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
        """
        return self._invoke('list_with_removed_components',
                            {
                            'host': host,
                            })
class Recommendations(VapiInterface):
    """
    The ``Recommendations`` class provides methods to manage the generation and
    retrieval of recommended image specs. This class was added in vSphere API
    8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.recommendations'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _RecommendationsStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'generate_task': 'generate$task'})

    class ExplanationDetails(VapiStruct):
        """
        The ``Recommendations.ExplanationDetails`` class contains attributes to
        describe the result of validation of desired software specification. This
        class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     display_name=None,
                     display_version=None,
                     explanation=None,
                    ):
            """
            :type  display_name: :class:`str`
            :param display_name: Display name of an excluded image entity (base image, add-on etc.).
                This attribute was added in vSphere API 8.0.0.1.
            :type  display_version: :class:`str`
            :param display_version: Display version of an excluded image entity (base image, add-on
                etc.). This attribute was added in vSphere API 8.0.0.1.
            :type  explanation: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param explanation: List of explanations on why the image entity is excluded. This
                attribute was added in vSphere API 8.0.0.1.
            """
            self.display_name = display_name
            self.display_version = display_version
            self.explanation = explanation
            VapiStruct.__init__(self)


    ExplanationDetails._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.recommendations.explanation_details', {
            'display_name': type.StringType(),
            'display_version': type.StringType(),
            'explanation': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        ExplanationDetails,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Recommendations.Info`` class defines the information about the most
        recent recommendation generation result. This class was added in vSphere
        API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     latest_recommendation=None,
                     current_series_recommendation=None,
                     base_image_explanation_details=None,
                     check_time=None,
                    ):
            """
            :type  latest_recommendation: :class:`com.vmware.esx.settings_client.SoftwareInfo` or ``None``
            :param latest_recommendation: Recommended image specification based on latest base image version.
                This attribute was added in vSphere API 8.0.0.1.
                None if no recommended image based on latest base image version is
                available.
            :type  current_series_recommendation: :class:`com.vmware.esx.settings_client.SoftwareInfo` or ``None``
            :param current_series_recommendation: Recommended image specification based on latest base image patch or
                update of the current series. This attribute was added in vSphere
                API 8.0.0.1.
                None if no recommended image based on latest base image patch or
                update of the current series is available.
            :type  base_image_explanation_details: :class:`list` of :class:`Recommendations.ExplanationDetails`
            :param base_image_explanation_details: Details about why some base images are excluded in latest and
                current series recommendations. This is not applicable for
                specified base image recommendations. This attribute was added in
                vSphere API 8.0.0.1.
            :type  check_time: :class:`datetime.datetime` or ``None``
            :param check_time: The most recent timestamp when check for recommended image is
                launched. This attribute was added in vSphere API 8.0.0.1.
                None if no recommendation check has ever been launched.
            """
            self.latest_recommendation = latest_recommendation
            self.current_series_recommendation = current_series_recommendation
            self.base_image_explanation_details = base_image_explanation_details
            self.check_time = check_time
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.software.recommendations.info', {
            'latest_recommendation': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'SoftwareInfo')),
            'current_series_recommendation': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'SoftwareInfo')),
            'base_image_explanation_details': type.ListType(type.ReferenceType(__name__, 'Recommendations.ExplanationDetails')),
            'check_time': type.OptionalType(type.DateTimeType()),
        },
        Info,
        False,
        None))




    def generate_task(self,
                 host,
                 ):
        """
        Generates recommended software image spec(s) based on current desired
        software spec. The result of this operation can be queried by calling
        the cis/tasks/{task-id} where the task-id is the response of this
        operation. This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ConcurrentChange` 
            If a new desired image is committed in parallel via a different
            client while recommendation is being generated.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        """
        task_id = self._invoke('generate$task',
                                {
                                'host': host,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.VoidType())
        return task_instance

    def get(self,
            host,
            ):
        """
        Returns Information about the most recent recommendation generation
        result. This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`Recommendations.Info`
        :return: Information about the most recent recommendation generation result.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
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
class RemovedComponents(VapiInterface):
    """
    The ``RemovedComponents`` class provides methods to manage removal of
    components in a software draft. This class was added in vSphere API
    8.0.3.0.
    """
    RESOURCE_TYPE = "com.vmware.esx.settings.component"
    """
    Resource type for component resource. This class attribute was added in vSphere
    API 8.0.3.0.

    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.removed_components'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _RemovedComponentsStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            host,
            component,
            ):
        """
        Returns the component version for the given removed component in the
        desired software specification. This method was added in vSphere API
        8.0.3.0.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  component: :class:`str`
        :param component: Identifier of the component.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.component``.
        :rtype: :class:`com.vmware.esx.settings_client.ComponentInfo`
        :return: Details about the component.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system or or no
            component associated with ``component`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the caller does not have the necessary privileges.
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
                            'component': component,
                            })

    def list(self,
             host,
             ):
        """
        Returns a map of removed components in the desired software
        specification. This method was added in vSphere API 8.0.3.0.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.ComponentInfo`
        :return: Map of ComponentInfo keyed by the component identifier. If no
            version is specified in desired software specification, then it
            will be empty.
            The key in the return value :class:`dict` will be an identifier for
            the resource type: ``com.vmware.esx.settings.component``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the caller does not have the necessary privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        """
        return self._invoke('list',
                            {
                            'host': host,
                            })
class Solutions(VapiInterface):
    """
    The ``Solutions`` class provides methods to manage desired software
    solution specifications for an ESX host. This class was added in vSphere
    API 8.0.0.1.
    """
    RESOURCE_TYPE = "com.vmware.esx.settings.solution"
    """
    Resource type for solution resource. This class attribute was added in vSphere
    API 8.0.0.1.

    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.software.solutions'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SolutionsStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'set_task': 'set$task'})
        self._VAPI_OPERATION_IDS.update({'delete_task': 'delete$task'})


    def get(self,
            host,
            solution,
            ):
        """
        Returns components registered for the given solution in the desired
        software specification. This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  solution: :class:`str`
        :param solution: Identifier of the solution.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.solution``.
        :rtype: :class:`com.vmware.esx.settings_client.SolutionInfo`
        :return: Specification of components registered by the solution.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` or no solution
            associated with . ``solution`` in the system.
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
                            'solution': solution,
                            })

    def list(self,
             host,
             ):
        """
        Returns all solutions in the desired software specification. This
        method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.SolutionInfo`
        :return: Map of solutions where key is solution identifier and value is a
            list of components registered by that solution.
            The key in the return value :class:`dict` will be an identifier for
            the resource type: ``com.vmware.esx.settings.solution``.
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
        return self._invoke('list',
                            {
                            'host': host,
                            })


    def set_task(self,
            host,
            solution,
            spec,
            ):
        """
        Sets the components registered for the given solution in the desired
        software specification. The task will set only one solution
        specification at a time. Solution constraints would be validated with
        the current desired software specification before it is committed as
        new desired spec. The result of this operation can be queried by
        calling the cis/tasks/{task-id} where the task-id is the response of
        this operation. This method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  solution: :class:`str`
        :param solution: Identifier of the solution.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.solution``.
        :type  spec: :class:`com.vmware.esx.settings_client.SolutionSpec`
        :param spec: Registered solution specification.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` or solution associated
            with ``solution`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        """
        task_id = self._invoke('set$task',
                                {
                                'host': host,
                                'solution': solution,
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.IdType(resource_types='com.vmware.esx.settings.commit'))
        return task_instance


    def delete_task(self,
               host,
               solution,
               ):
        """
        Deletes the given solution from the desired software specification. The
        deletion will be validated along with the entire software specification
        before it is committed as new desired spec. The result of this
        operation can be queried by calling the cis/tasks/{task-id} where the
        task-id is the response of this operation. This method was added in
        vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  solution: :class:`str`
        :param solution: Identifier of the solution.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.solution``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if validation of the software document fails. The value of the data
            attribute of :class:`com.vmware.vapi.std.errors_client.Error` will
            be a class that contains all the attributes defined in
            ValidateResult.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no host associated with ``host`` or solution associated
            with ``solution`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            If the host is not a vLCM managed standlone host.
        """
        task_id = self._invoke('delete$task',
                                {
                                'host': host,
                                'solution': solution,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.IdType(resource_types='com.vmware.esx.settings.commit'))
        return task_instance
class _AddOnStub(ApiInterfaceStub):
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
            url_template='/esx/settings/hosts/{host}/software/add-on',
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
                'output_type': type.ReferenceType('com.vmware.esx.settings_client', 'AddOnInfo'),
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
            self, iface_name='com.vmware.esx.settings.hosts.software.add_on',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _BaseImageStub(ApiInterfaceStub):
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
            url_template='/esx/settings/hosts/{host}/software/base-image',
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
                'output_type': type.ReferenceType('com.vmware.esx.settings_client', 'BaseImageInfo'),
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
            self, iface_name='com.vmware.esx.settings.hosts.software.base_image',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _CommitsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
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
            url_template='/esx/settings/hosts/{host}/software/commits/{commit}',
            path_variables={
                'host': 'host',
                'commit': 'commit',
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
                'output_type': type.ReferenceType(__name__, 'Commits.Info'),
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
            self, iface_name='com.vmware.esx.settings.hosts.software.commits',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _ComplianceStub(ApiInterfaceStub):
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
            url_template='/esx/settings/hosts/{host}/software/compliance',
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
                'output_type': type.ReferenceType('com.vmware.esx.settings_client', 'HostCompliance'),
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
            self, iface_name='com.vmware.esx.settings.hosts.software.compliance',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _ComponentsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'component': type.IdType(resource_types='com.vmware.esx.settings.component'),
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
            url_template='/esx/settings/hosts/{host}/software/components/{component}',
            path_variables={
                'host': 'host',
                'component': 'component',
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
            'host': type.IdType(resource_types='HostSystem'),
        })
        list_error_dict = {
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
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/hosts/{host}/software/components',
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
                'output_type': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'ComponentInfo')),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'ComponentInfo')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.software.components',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _DraftsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for commit operation
        commit_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
            'spec': type.ReferenceType(__name__, 'Drafts.CommitSpec'),
        })
        commit_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        commit_input_value_validator_list = [
        ]
        commit_output_validator_list = [
        ]
        commit_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/software/drafts/{draft}',
            request_body_parameter='spec',
            path_variables={
                'host': 'host',
                'draft': 'draft',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'commit',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
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
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/software/drafts',
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

        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
        })
        delete_error_dict = {
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
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/esx/settings/hosts/{host}/software/drafts/{draft}',
            path_variables={
                'host': 'host',
                'draft': 'draft',
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
            'host': type.IdType(resource_types='HostSystem'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
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
            url_template='/esx/settings/hosts/{host}/software/drafts/{draft}',
            path_variables={
                'host': 'host',
                'draft': 'draft',
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
            'host': type.IdType(resource_types='HostSystem'),
            'filter': type.OptionalType(type.ReferenceType(__name__, 'Drafts.FilterSpec')),
        })
        list_error_dict = {
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
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/hosts/{host}/software/drafts',
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

        # properties for validate operation
        validate_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
        })
        validate_error_dict = {
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
        validate_input_value_validator_list = [
        ]
        validate_output_validator_list = [
        ]
        validate_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/software/drafts/{draft}',
            path_variables={
                'host': 'host',
                'draft': 'draft',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'validate',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for scan operation
        scan_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
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
            url_template='/esx/settings/hosts/{host}/software/drafts/{draft}',
            path_variables={
                'host': 'host',
                'draft': 'draft',
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

        # properties for import_software_spec operation
        import_software_spec_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'spec': type.ReferenceType(__name__, 'Drafts.ImportSpec'),
        })
        import_software_spec_error_dict = {
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
        import_software_spec_input_value_validator_list = [
        ]
        import_software_spec_output_validator_list = [
        ]
        import_software_spec_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/software/drafts',
            request_body_parameter='spec',
            path_variables={
                'host': 'host',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'import-software-spec',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'commit$task': {
                'input_type': commit_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': commit_error_dict,
                'input_value_validator_list': commit_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'create': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.esx.settings.draft'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
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
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Drafts.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.MapType(type.IdType(), type.ReferenceType(__name__, 'Drafts.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'validate$task': {
                'input_type': validate_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': validate_error_dict,
                'input_value_validator_list': validate_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'scan$task': {
                'input_type': scan_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': scan_error_dict,
                'input_value_validator_list': scan_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'import_software_spec': {
                'input_type': import_software_spec_input_type,
                'output_type': type.IdType(resource_types='com.vmware.esx.settings.draft'),
                'errors': import_software_spec_error_dict,
                'input_value_validator_list': import_software_spec_input_value_validator_list,
                'output_validator_list': import_software_spec_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'commit': commit_rest_metadata,
            'create': create_rest_metadata,
            'delete': delete_rest_metadata,
            'get': get_rest_metadata,
            'list': list_rest_metadata,
            'validate': validate_rest_metadata,
            'scan': scan_rest_metadata,
            'import_software_spec': import_software_spec_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.software.drafts',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _EffectiveComponentsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
        })
        list_error_dict = {
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
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/hosts/{host}/software/effective-components',
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

        # properties for list_with_removed_components operation
        list_with_removed_components_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
        })
        list_with_removed_components_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        list_with_removed_components_input_value_validator_list = [
        ]
        list_with_removed_components_output_validator_list = [
        ]
        list_with_removed_components_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/hosts/{host}/software/effective-components',
            path_variables={
                'host': 'host',
            },
            query_parameters={
            },
            dispatch_parameters={
                'with-removed-components': 'null',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'list': {
                'input_type': list_input_type,
                'output_type': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'EffectiveComponentInfo')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list_with_removed_components': {
                'input_type': list_with_removed_components_input_type,
                'output_type': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'EffectiveComponentInfo')),
                'errors': list_with_removed_components_error_dict,
                'input_value_validator_list': list_with_removed_components_input_value_validator_list,
                'output_validator_list': list_with_removed_components_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
            'list_with_removed_components': list_with_removed_components_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.software.effective_components',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _RecommendationsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for generate operation
        generate_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
        })
        generate_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.concurrent_change':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ConcurrentChange'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        generate_input_value_validator_list = [
        ]
        generate_output_validator_list = [
        ]
        generate_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/hosts/{host}/software/recommendations',
            path_variables={
                'host': 'host',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'generate',
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
            url_template='/esx/settings/hosts/{host}/software/recommendations',
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
            'generate$task': {
                'input_type': generate_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': generate_error_dict,
                'input_value_validator_list': generate_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Recommendations.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'generate': generate_rest_metadata,
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.software.recommendations',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _RemovedComponentsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'component': type.IdType(resource_types='com.vmware.esx.settings.component'),
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
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/hosts/{host}/software/removed-components/{component}',
            path_variables={
                'host': 'host',
                'component': 'component',
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
            'host': type.IdType(resource_types='HostSystem'),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/hosts/{host}/software/removed-components',
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
                'output_type': type.ReferenceType('com.vmware.esx.settings_client', 'ComponentInfo'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'ComponentInfo')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.software.removed_components',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _SolutionsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'solution': type.IdType(resource_types='com.vmware.esx.settings.solution'),
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
            url_template='/esx/settings/hosts/{host}/software/solutions/{solution}',
            path_variables={
                'host': 'host',
                'solution': 'solution',
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
            'host': type.IdType(resource_types='HostSystem'),
        })
        list_error_dict = {
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
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/hosts/{host}/software/solutions',
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

        # properties for set operation
        set_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'solution': type.IdType(resource_types='com.vmware.esx.settings.solution'),
            'spec': type.ReferenceType('com.vmware.esx.settings_client', 'SolutionSpec'),
        })
        set_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/esx/settings/hosts/{host}/software/solutions/{solution}',
            request_body_parameter='spec',
            path_variables={
                'host': 'host',
                'solution': 'solution',
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
            'host': type.IdType(resource_types='HostSystem'),
            'solution': type.IdType(resource_types='com.vmware.esx.settings.solution'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/esx/settings/hosts/{host}/software/solutions/{solution}',
            path_variables={
                'host': 'host',
                'solution': 'solution',
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
                'output_type': type.ReferenceType('com.vmware.esx.settings_client', 'SolutionInfo'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'SolutionInfo')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'set$task': {
                'input_type': set_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': set_error_dict,
                'input_value_validator_list': set_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'delete$task': {
                'input_type': delete_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'list': list_rest_metadata,
            'set': set_rest_metadata,
            'delete': delete_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.hosts.software.solutions',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'AddOn': AddOn,
        'BaseImage': BaseImage,
        'Commits': Commits,
        'Compliance': Compliance,
        'Components': Components,
        'Drafts': Drafts,
        'EffectiveComponents': EffectiveComponents,
        'Recommendations': Recommendations,
        'RemovedComponents': RemovedComponents,
        'Solutions': Solutions,
        'drafts': 'com.vmware.esx.settings.hosts.software.drafts_client.StubFactory',
        'reports': 'com.vmware.esx.settings.hosts.software.reports_client.StubFactory',
    }

