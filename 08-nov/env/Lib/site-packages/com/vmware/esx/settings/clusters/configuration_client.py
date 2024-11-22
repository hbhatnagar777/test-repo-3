# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.settings.clusters.configuration.
#---------------------------------------------------------------------------

"""
The ``com.vmware.esx.settings.clusters.configuration_client`` module provides
classes to manage the configuration of an ESX cluster. The
``com.vmware.esx.settings.clusters.configuration.reports_client`` module
provides classes for accessing reports regarding the configuration state of the
cluster.

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

class DocumentStructure(Enum):
    """
    The ``DocumentStructure`` class contains the possible structures of the
    configuration document. This enumeration was added in vSphere API 8.0.1.0.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    HOST_ORIENTED = None
    """
    The host-specific portions of the document are stored in the
    "host-specific" object at the top-level with entries for each host,
    organized by the host's BIOS UUID. This class attribute was added in
    vSphere API 8.0.1.0.

    """
    PROFILE_ORIENTED = None
    """
    The host-specific portions of the document are distributed through the
    "profile" object hierarchy. Each property that is host-specific will be an
    object with entries for each host where the property is defined. The hosts
    in the object are organized by BIOS UUID. This class attribute was added in
    vSphere API 8.0.1.0.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`DocumentStructure` instance.
        """
        Enum.__init__(string)

DocumentStructure._set_values({
    'HOST_ORIENTED': DocumentStructure('HOST_ORIENTED'),
    'PROFILE_ORIENTED': DocumentStructure('PROFILE_ORIENTED'),
})
DocumentStructure._set_binding_type(type.EnumType(
    'com.vmware.esx.settings.clusters.configuration.document_structure',
    DocumentStructure))



class ComplianceStatus(Enum):
    """
    This ``ComplianceStatus`` class represents the compliance status of desired
    configuration on the ESXi host. This enumeration was added in vSphere API
    8.0.1.0.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    COMPLIANT = None
    """
    ESXi host is in compliance with Desired configuration. This class attribute
    was added in vSphere API 8.0.1.0.

    """
    NON_COMPLIANT = None
    """
    ESXi host is not in compliance with Desired configuration. This class
    attribute was added in vSphere API 8.0.1.0.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`ComplianceStatus` instance.
        """
        Enum.__init__(string)

ComplianceStatus._set_values({
    'COMPLIANT': ComplianceStatus('COMPLIANT'),
    'NON_COMPLIANT': ComplianceStatus('NON_COMPLIANT'),
})
ComplianceStatus._set_binding_type(type.EnumType(
    'com.vmware.esx.settings.clusters.configuration.compliance_status',
    ComplianceStatus))



class ImpactType(Enum):
    """
    The ``ImpactType`` class contains information about the impact of applying
    desired configuration on the ESXi host. This enumeration was added in
    vSphere API 8.0.1.0.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    NO_IMPACT = None
    """
    Host has no impact. This class attribute was added in vSphere API 8.0.1.0.

    """
    MAINTENANCE_MODE_REQUIRED = None
    """
    Host requires maintenance mode to reach the desired state. This class
    attribute was added in vSphere API 8.0.1.0.

    """
    REBOOT_REQUIRED = None
    """
    Host requires reboot to reach the desired state. This class attribute was
    added in vSphere API 8.0.1.0.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`ImpactType` instance.
        """
        Enum.__init__(string)

ImpactType._set_values({
    'NO_IMPACT': ImpactType('NO_IMPACT'),
    'MAINTENANCE_MODE_REQUIRED': ImpactType('MAINTENANCE_MODE_REQUIRED'),
    'REBOOT_REQUIRED': ImpactType('REBOOT_REQUIRED'),
})
ImpactType._set_binding_type(type.EnumType(
    'com.vmware.esx.settings.clusters.configuration.impact_type',
    ImpactType))




class HostStatus(VapiStruct):
    """
    The ``HostStatus`` class contains attributes that describe the status of an
    method. This class was added in vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 status=None,
                 attempts=None,
                 remaining_retries=None,
                 start_time=None,
                 end_time=None,
                 notifications=None,
                ):
        """
        :type  status: :class:`HostStatus.Status`
        :param status: The status of the method. This attribute was added in vSphere API
            8.0.1.0.
        :type  attempts: :class:`long` or ``None``
        :param attempts: Number of the performed attempts of the method. This attribute was
            added in vSphere API 8.0.1.0.
            This field is None if it is not applicable.
        :type  remaining_retries: :class:`long` or ``None``
        :param remaining_retries: Number of the remaining attempts of the method. This attribute was
            added in vSphere API 8.0.1.0.
            This field is None if it is not applicable.
        :type  start_time: :class:`datetime.datetime`
        :param start_time: Time when the method started. This attribute was added in vSphere
            API 8.0.1.0.
        :type  end_time: :class:`datetime.datetime`
        :param end_time: Time when the method completed. This attribute was added in vSphere
            API 8.0.1.0.
        :type  notifications: :class:`com.vmware.esx.settings_client.Notifications`
        :param notifications: Notifications providing additional information about the status of
            the method. This attribute was added in vSphere API 8.0.1.0.
        """
        self.status = status
        self.attempts = attempts
        self.remaining_retries = remaining_retries
        self.start_time = start_time
        self.end_time = end_time
        self.notifications = notifications
        VapiStruct.__init__(self)


    class Status(Enum):
        """
        The ``HostStatus.Status`` class contains the possible different status
        codes that can be returned while trying to perform an operation on the
        hosts within the cluster. This enumeration was added in vSphere API
        8.0.1.0.

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
        vSphere API 8.0.1.0.

        """
        PENDING = None
        """
        The method is pending. This class attribute was added in vSphere API
        8.0.1.0.

        """
        RUNNING = None
        """
        The method is in progress. This class attribute was added in vSphere API
        8.0.1.0.

        """
        RETRY_PENDING = None
        """
        The method is pending a retry. This class attribute was added in vSphere
        API 8.0.1.0.

        """
        SKIPPED = None
        """
        The method was skipped. This class attribute was added in vSphere API
        8.0.1.0.

        """
        CANCELED = None
        """
        The method was canceled. This class attribute was added in vSphere API
        8.0.1.0.

        """
        TIMED_OUT = None
        """
        The method timed out. This class attribute was added in vSphere API
        8.0.1.0.

        """
        ERROR = None
        """
        The method encountered an unspecified error. This class attribute was added
        in vSphere API 8.0.1.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Status` instance.
            """
            Enum.__init__(string)

    Status._set_values({
        'OK': Status('OK'),
        'PENDING': Status('PENDING'),
        'RUNNING': Status('RUNNING'),
        'RETRY_PENDING': Status('RETRY_PENDING'),
        'SKIPPED': Status('SKIPPED'),
        'CANCELED': Status('CANCELED'),
        'TIMED_OUT': Status('TIMED_OUT'),
        'ERROR': Status('ERROR'),
    })
    Status._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.configuration.host_status.status',
        Status))

HostStatus._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.host_status', {
        'status': type.ReferenceType(__name__, 'HostStatus.Status'),
        'attempts': type.OptionalType(type.IntegerType()),
        'remaining_retries': type.OptionalType(type.IntegerType()),
        'start_time': type.DateTimeType(),
        'end_time': type.DateTimeType(),
        'notifications': type.ReferenceType('com.vmware.esx.settings_client', 'Notifications'),
    },
    HostStatus,
    False,
    None))



class SettingCompliance(VapiStruct):
    """
    The ``SettingCompliance`` class contains attributes that describe a drift
    in an ESXi host setting. This structure is used to describe either a change
    in configuration value(set) or addition of configuration or deletion of
    configuration. When used to describe addition or deletion of a setting,
    only the path is set. When used to describe a set operation, current and
    target values are set only if drift is in a property that is of primitive
    type. This class was added in vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 path=None,
                 current=None,
                 target=None,
                ):
        """
        :type  path: :class:`str`
        :param path: Full path to the setting within the desired document. This
            attribute was added in vSphere API 8.0.1.0.
        :type  current: :class:`str` or ``None``
        :param current: Value of setting on the ESXi host. This attribute was added in
            vSphere API 8.0.1.0.
            This field is None if there is no host value to report or if
            setting is of complex type.
        :type  target: :class:`str` or ``None``
        :param target: Value of setting in the desired document. This attribute was added
            in vSphere API 8.0.1.0.
            This field is None if there is no value in the desired document to
            report or if setting is of complex type.
        """
        self.path = path
        self.current = current
        self.target = target
        VapiStruct.__init__(self)


SettingCompliance._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.setting_compliance', {
        'path': type.StringType(),
        'current': type.OptionalType(type.StringType()),
        'target': type.OptionalType(type.StringType()),
    },
    SettingCompliance,
    False,
    None))



class ComplianceInfo(VapiStruct):
    """
    The ``ComplianceInfo`` class contains attributes that describe the
    configuration drift between the desired document and the configurations on
    the ESXi host. This class was added in vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 sets=None,
                 adds=None,
                 deletes=None,
                ):
        """
        :type  sets: :class:`list` of :class:`SettingCompliance` or ``None``
        :param sets: List of configuration drifts represented by
            :class:`SettingCompliance`. Each describing a configuration whose
            value on ESXi host is different to that in the desired document.
            This attribute was added in vSphere API 8.0.1.0.
            This field is None if there are no drifts to report in this
            category.
        :type  adds: :class:`list` of :class:`SettingCompliance` or ``None``
        :param adds: List of configuration drifts represented by
            :class:`SettingCompliance`. Each describing a configuration that is
            present in the desired document but absent on the ESXi host. This
            attribute was added in vSphere API 8.0.1.0.
            This field is None if there are no drifts to report in this
            category.
        :type  deletes: :class:`list` of :class:`SettingCompliance` or ``None``
        :param deletes: List of configuration drifts represented by
            :class:`SettingCompliance`. Each describing a configuration that is
            present on the ESXi host but absent in the desired document. This
            attribute was added in vSphere API 8.0.1.0.
            This field is None if there are no drifts to report in this
            category.
        """
        self.sets = sets
        self.adds = adds
        self.deletes = deletes
        VapiStruct.__init__(self)


ComplianceInfo._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.compliance_info', {
        'sets': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'SettingCompliance'))),
        'adds': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'SettingCompliance'))),
        'deletes': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'SettingCompliance'))),
    },
    ComplianceInfo,
    False,
    None))



class HostCompliance(VapiStruct):
    """
    The ``HostCompliance`` class contains attributes that describe compliance
    information for the ESXi host on which the Check Compliance operation
    completed successfully. This class was added in vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """

    _validator_list = [
        UnionValidator(
            'status',
            {
                'NON_COMPLIANT' : [('compliance_info', True)],
                'COMPLIANT' : [],
            }
        ),
    ]



    def __init__(self,
                 status=None,
                 compliance_info=None,
                ):
        """
        :type  status: :class:`ComplianceStatus`
        :param status: This field indicates whether the ESXi host is compliant with the
            desired configuration specified in
            com.vmware.esx.settings_daemon.Configuration#CheckComplianceSpec.
            If COMPLIANT, no other information is available. If NON_COMPLAINT,
            drift information can be fetched from {#ComplianceInfo}. This
            attribute was added in vSphere API 8.0.1.0.
        :type  compliance_info: :class:`ComplianceInfo`
        :param compliance_info: Settings compliance information generated by the CheckCompliance
            operation. This attribute was added in vSphere API 8.0.1.0.
            This attribute is optional and it is only relevant when the value
            of ``status`` is :attr:`ComplianceStatus.NON_COMPLIANT`.
        """
        self.status = status
        self.compliance_info = compliance_info
        VapiStruct.__init__(self)


HostCompliance._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.host_compliance', {
        'status': type.ReferenceType(__name__, 'ComplianceStatus'),
        'compliance_info': type.OptionalType(type.ReferenceType(__name__, 'ComplianceInfo')),
    },
    HostCompliance,
    False,
    None))



class HostResult(VapiStruct):
    """
    This ``HostResult`` class contains attributes that describe the result of
    the check compliance operation on an ESXi host. This class was added in
    vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 host_status=None,
                 summary=None,
                 errors=None,
                 host_compliance=None,
                ):
        """
        :type  host_status: :class:`HostStatus`
        :param host_status: This field represents the status of the check compliance operation.
            If status is OK, the result of operation can be retrived from
            {#HostCompliance} {#Summary} field will summarize the status of the
            operation and if applicable, the specific error that occured.
            Additionally, {#ValidationError} is populated if the operation
            fails due to host validation errors in desired document. This
            attribute was added in vSphere API 8.0.1.0.
        :type  summary: :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param summary: Summary of check compliance operation on the host. This attribute
            was added in vSphere API 8.0.1.0.
        :type  errors: :class:`list` of :class:`ValidationError` or ``None``
        :param errors: List of validation errors returned by the host. This is only set
            for a specific HostStatus ERROR case. This attribute was added in
            vSphere API 8.0.1.0.
            This field is :class:`set` only if the document fails to validate
            on the host.
        :type  host_compliance: :class:`HostCompliance` or ``None``
        :param host_compliance: This field provides compliance results for the host if the
            operation successfully completed on the host. That is, this field
            is populated only if HostStatus is OK. This attribute was added in
            vSphere API 8.0.1.0.
            This field is None if check compliance could not be completed on
            the host.
        """
        self.host_status = host_status
        self.summary = summary
        self.errors = errors
        self.host_compliance = host_compliance
        VapiStruct.__init__(self)


HostResult._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.host_result', {
        'host_status': type.ReferenceType(__name__, 'HostStatus'),
        'summary': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
        'errors': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ValidationError'))),
        'host_compliance': type.OptionalType(type.ReferenceType(__name__, 'HostCompliance')),
    },
    HostResult,
    False,
    None))



class ClusterCompliance(VapiStruct):
    """
    This ``ClusterCompliance`` class contains attributes that describe the
    compliance result for each host in the cluster as well as overall cluster
    compliance status. This class was added in vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 cluster_status=None,
                 commit=None,
                 software_commit=None,
                 summary=None,
                 validation_errors=None,
                 host_info=None,
                 hosts=None,
                 compliant_hosts=None,
                 non_compliant_hosts=None,
                 failed_hosts=None,
                 skipped_hosts=None,
                 end_time=None,
                ):
        """
        :type  cluster_status: :class:`ClusterCompliance.Status`
        :param cluster_status: Consolidated status of all host compliance checks. This attribute
            was added in vSphere API 8.0.1.0.
        :type  commit: :class:`str` or ``None``
        :param commit: This identifier refers to the commit action of importing the
            desired configuration document. It will not be set for a draft
            execution of check compliance. This attribute was added in vSphere
            API 8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.esx.settings.commit``. When methods return a value of
            this class as a return value, the attribute will be an identifier
            for the resource type: ``com.vmware.esx.settings.commit``.
        :type  software_commit: :class:`str`
        :param software_commit: The current commit ID for the software associated with the cluster.
            This attribute was added in vSphere API 8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.esx.settings.commit``. When methods return a value of
            this class as a return value, the attribute will be an identifier
            for the resource type: ``com.vmware.esx.settings.commit``.
        :type  summary: :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param summary: Summarizing check compliance operation on the hosts in the cluster.
            This attribute was added in vSphere API 8.0.1.0.
        :type  validation_errors: :class:`list` of :class:`ValidationError` or ``None``
        :param validation_errors: This field represents the validation errors if the desired
            configuration specified is not valid. This attribute was added in
            vSphere API 8.0.3.0.
            This field may be :class:`set` if
            :attr:`ClusterCompliance.cluster_status` is NOT_COMPLIANT due to
            validation errors.
        :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
        :param host_info: Map of host IDs to hostname. This attribute was added in vSphere
            API 8.0.1.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``HostSystem``. When methods return a value of this class as
            a return value, the key in the attribute :class:`dict` will be an
            identifier for the resource type: ``HostSystem``.
        :type  hosts: :class:`dict` of :class:`str` and :class:`HostResult`
        :param hosts: Map of host IDs to their compliance results. This attribute was
            added in vSphere API 8.0.1.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``HostSystem``. When methods return a value of this class as
            a return value, the key in the attribute :class:`dict` will be an
            identifier for the resource type: ``HostSystem``.
        :type  compliant_hosts: :class:`set` of :class:`str`
        :param compliant_hosts: Identifiers of compliant hosts. This attribute was added in vSphere
            API 8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``HostSystem``. When methods return a value of this class as a
            return value, the attribute will contain identifiers for the
            resource type: ``HostSystem``.
        :type  non_compliant_hosts: :class:`set` of :class:`str`
        :param non_compliant_hosts: Identifiers of non-compliant hosts. This attribute was added in
            vSphere API 8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``HostSystem``. When methods return a value of this class as a
            return value, the attribute will contain identifiers for the
            resource type: ``HostSystem``.
        :type  failed_hosts: :class:`set` of :class:`str`
        :param failed_hosts: Identifiers of hosts where the operation failed. This attribute was
            added in vSphere API 8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``HostSystem``. When methods return a value of this class as a
            return value, the attribute will contain identifiers for the
            resource type: ``HostSystem``.
        :type  skipped_hosts: :class:`set` of :class:`str`
        :param skipped_hosts: Identifiers of hosts where the operation was skipped. i.e
            disconnected hosts. This attribute was added in vSphere API
            8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``HostSystem``. When methods return a value of this class as a
            return value, the attribute will contain identifiers for the
            resource type: ``HostSystem``.
        :type  end_time: :class:`datetime.datetime`
        :param end_time: CheckCompliance completion time. This attribute was added in
            vSphere API 8.0.1.0.
        """
        self.cluster_status = cluster_status
        self.commit = commit
        self.software_commit = software_commit
        self.summary = summary
        self.validation_errors = validation_errors
        self.host_info = host_info
        self.hosts = hosts
        self.compliant_hosts = compliant_hosts
        self.non_compliant_hosts = non_compliant_hosts
        self.failed_hosts = failed_hosts
        self.skipped_hosts = skipped_hosts
        self.end_time = end_time
        VapiStruct.__init__(self)


    class Status(Enum):
        """
        Consolidated compliance status of the cluster. This enumeration was added
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
        RUNNING = None
        """
        The task is in-progress. This class attribute was added in vSphere API
        8.0.1.0.

        """
        COMPLIANT = None
        """
        All hosts in the cluster are compliant. This class attribute was added in
        vSphere API 8.0.1.0.

        """
        NOT_COMPLIANT = None
        """


        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Status` instance.
            """
            Enum.__init__(string)

    Status._set_values({
        'RUNNING': Status('RUNNING'),
        'COMPLIANT': Status('COMPLIANT'),
        'NOT_COMPLIANT': Status('NOT_COMPLIANT'),
    })
    Status._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.configuration.cluster_compliance.status',
        Status))

ClusterCompliance._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.cluster_compliance', {
        'cluster_status': type.ReferenceType(__name__, 'ClusterCompliance.Status'),
        'commit': type.OptionalType(type.IdType()),
        'software_commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
        'summary': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
        'validation_errors': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ValidationError'))),
        'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
        'hosts': type.MapType(type.IdType(), type.ReferenceType(__name__, 'HostResult')),
        'compliant_hosts': type.SetType(type.IdType()),
        'non_compliant_hosts': type.SetType(type.IdType()),
        'failed_hosts': type.SetType(type.IdType()),
        'skipped_hosts': type.SetType(type.IdType()),
        'end_time': type.DateTimeType(),
    },
    ClusterCompliance,
    False,
    None))



class DependencyError(VapiStruct):
    """
    The ``DependencyError`` class contains details of the validation error
    caused by dependency between different properties in the configuration.
    This class was added in vSphere API 8.0.2.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 required_value=None,
                 current_value=None,
                 possible_values=None,
                ):
        """
        :type  required_value: :class:`str`
        :param required_value: The dependency required by a union tag. This attribute was added in
            vSphere API 8.0.2.0.
        :type  current_value: :class:`str` or ``None``
        :param current_value: This attribute was added in vSphere API 8.0.2.0.
            If :class:`set`, it contains the current value of the dependency
            property.
        :type  possible_values: :class:`str`
        :param possible_values: The possible values of the dependency property that are compatible
            with this property. This attribute was added in vSphere API
            8.0.2.0.
        """
        self.required_value = required_value
        self.current_value = current_value
        self.possible_values = possible_values
        VapiStruct.__init__(self)


DependencyError._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.dependency_error', {
        'required_value': type.StringType(),
        'current_value': type.OptionalType(type.StringType()),
        'possible_values': type.StringType(),
    },
    DependencyError,
    False,
    None))



class DetailedValidationError(VapiStruct):
    """
    The ``SchemaValidationError`` class contains details of validation errors
    for a property. This class was added in vSphere API 8.0.2.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """

    _validator_list = [
        UnionValidator(
            'type',
            {
                'PATTERN_MISMATCH' : [('pattern', True)],
                'PROPERTY_NAME_MISMATCH' : [('pattern', True)],
                'INVALID_TYPE' : [('expected_type', True)],
                'DUPLICATE_INSTANCE_ID' : [('instance_id', True)],
                'MISSING_REQUIRED_PROFILE_INSTANCE' : [('instance_id', True), ('path', True), ('required_property', True)],
                'MISSING_INSTANCE_ID' : [('property_name', True)],
                'MAX_STRING_LENGTH' : [('maximum_length', True)],
                'MAX_ARRAY_LENGTH' : [('maximum_length', True)],
                'MIN_STRING_LENGTH' : [('minimum_length', True)],
                'MIN_ARRAY_LENGTH' : [('minimum_length', True)],
                'MAX_VALUE' : [('maximum_value', True)],
                'MIN_VALUE' : [('minimum_value', True)],
                'INVALID_UNION_TAG' : [('dependency_error', True)],
                'UNION_CASE_WITHOUT_UNION_TAG' : [('dependency_error', True)],
                'SCHEMA_NOT_FOUND' : [('component', True), ('group', True), ('key', True)],
                'MISSING_REQUIRED_PROFILE_KEY' : [('path', True), ('required_property', True)],
                'GENERIC' : [],
                'ADDITIONAL_PROPERTY' : [],
                'INVALID_ENUM_OPTION' : [],
                'MISSING_REQUIRED' : [],
                'NULL_VALUE' : [],
                'INVALID_DELETE_DEFAULT' : [],
                'HOST_SPECIFIC_IN_PROFILE' : [],
                'NOT_HOST_SPECIFIC' : [],
                'EMPTY_PROPERTY' : [],
                'KEY_IN_HOST_OVERRIDE' : [],
                'PLACEHOLDER_FOUND' : [],
                'HOST_SPECIFIC_KEY_IN_OVERRIDE' : [],
            }
        ),
    ]



    def __init__(self,
                 hosts=None,
                 message=None,
                 type=None,
                 pattern=None,
                 expected_type=None,
                 instance_id=None,
                 property_name=None,
                 maximum_length=None,
                 minimum_length=None,
                 maximum_value=None,
                 minimum_value=None,
                 dependency_error=None,
                 component=None,
                 group=None,
                 key=None,
                 path=None,
                 required_property=None,
                ):
        """
        :type  hosts: :class:`list` of :class:`str` or ``None``
        :param hosts: If this error is from a host-level validation performed during a
            precheck, the hosts that experienced this error will be added here.
            This attribute was added in vSphere API 8.0.2.0.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``HostSystem``. When methods return a value of this class as a
            return value, the attribute will contain identifiers for the
            resource type: ``HostSystem``.
        :type  message: :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param message: A user-friendly description of the error. This attribute was added
            in vSphere API 8.0.2.0.
        :type  type: :class:`DetailedValidationError.ErrorType`
        :param type: The type of error. Additional information may be set for some types
            of errors. This attribute was added in vSphere API 8.0.2.0.
        :type  pattern: :class:`str`
        :param pattern: The pattern the property is required to match. This attribute was
            added in vSphere API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is one of
            :attr:`DetailedValidationError.ErrorType.PATTERN_MISMATCH` or
            :attr:`DetailedValidationError.ErrorType.PROPERTY_NAME_MISMATCH`.
        :type  expected_type: :class:`str`
        :param expected_type: The expected type of the property. This attribute was added in
            vSphere API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is
            :attr:`DetailedValidationError.ErrorType.INVALID_TYPE`.
        :type  instance_id: :class:`str`
        :param instance_id: The instance ID that was duplicated or is missing from the profile
            section. This attribute was added in vSphere API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is one of
            :attr:`DetailedValidationError.ErrorType.DUPLICATE_INSTANCE_ID` or
            :attr:`DetailedValidationError.ErrorType.MISSING_REQUIRED_PROFILE_INSTANCE`.
        :type  property_name: :class:`str`
        :param property_name: The name of the property that holds the instance ID. This attribute
            was added in vSphere API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is
            :attr:`DetailedValidationError.ErrorType.MISSING_INSTANCE_ID`.
        :type  maximum_length: :class:`long`
        :param maximum_length: The maximum length allowed for a string or array property. This
            attribute was added in vSphere API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is one of
            :attr:`DetailedValidationError.ErrorType.MAX_STRING_LENGTH` or
            :attr:`DetailedValidationError.ErrorType.MAX_ARRAY_LENGTH`.
        :type  minimum_length: :class:`long`
        :param minimum_length: The minimum length allowed for a string or array property. This
            attribute was added in vSphere API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is one of
            :attr:`DetailedValidationError.ErrorType.MIN_STRING_LENGTH` or
            :attr:`DetailedValidationError.ErrorType.MIN_ARRAY_LENGTH`.
        :type  maximum_value: :class:`long`
        :param maximum_value: The maximum allowed value for a property. This attribute was added
            in vSphere API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is :attr:`DetailedValidationError.ErrorType.MAX_VALUE`.
        :type  minimum_value: :class:`long`
        :param minimum_value: The minimum allowed value for a property. This attribute was added
            in vSphere API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is :attr:`DetailedValidationError.ErrorType.MIN_VALUE`.
        :type  dependency_error: :class:`DependencyError`
        :param dependency_error: The dependency required by a union tag. This attribute was added in
            vSphere API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is one of
            :attr:`DetailedValidationError.ErrorType.INVALID_UNION_TAG` or
            :attr:`DetailedValidationError.ErrorType.UNION_CASE_WITHOUT_UNION_TAG`.
        :type  component: :class:`str`
        :param component: For ``SCHEMA_NOT_FOUND`` errors, this will be the component portion
            of the unknown configuration. This attribute was added in vSphere
            API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is
            :attr:`DetailedValidationError.ErrorType.SCHEMA_NOT_FOUND`.
        :type  group: :class:`str`
        :param group: For ``SCHEMA_NOT_FOUND`` errors, this will be the group portion of
            the unknown configuration. This attribute was added in vSphere API
            8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is
            :attr:`DetailedValidationError.ErrorType.SCHEMA_NOT_FOUND`.
        :type  key: :class:`str`
        :param key: For ``SCHEMA_NOT_FOUND`` errors, this will be the key portion of
            the unknown configuration. This attribute was added in vSphere API
            8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is
            :attr:`DetailedValidationError.ErrorType.SCHEMA_NOT_FOUND`.
        :type  path: :class:`str`
        :param path: The JSON-pointer to the configuration key in the profile section
            where the instance/key needs to be added. This attribute was added
            in vSphere API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is one of
            :attr:`DetailedValidationError.ErrorType.MISSING_REQUIRED_PROFILE_INSTANCE`
            or
            :attr:`DetailedValidationError.ErrorType.MISSING_REQUIRED_PROFILE_KEY`.
        :type  required_property: :class:`str`
        :param required_property: The name of the required property that is missing from the profile
            section for this instance/key. This attribute was added in vSphere
            API 8.0.2.0.
            This attribute is optional and it is only relevant when the value
            of ``type`` is one of
            :attr:`DetailedValidationError.ErrorType.MISSING_REQUIRED_PROFILE_INSTANCE`
            or
            :attr:`DetailedValidationError.ErrorType.MISSING_REQUIRED_PROFILE_KEY`.
        """
        self.hosts = hosts
        self.message = message
        self.type = type
        self.pattern = pattern
        self.expected_type = expected_type
        self.instance_id = instance_id
        self.property_name = property_name
        self.maximum_length = maximum_length
        self.minimum_length = minimum_length
        self.maximum_value = maximum_value
        self.minimum_value = minimum_value
        self.dependency_error = dependency_error
        self.component = component
        self.group = group
        self.key = key
        self.path = path
        self.required_property = required_property
        VapiStruct.__init__(self)


    class ErrorType(Enum):
        """
        The ``DetailedValidationError.ErrorType`` enum contains the possible types
        of errors related to property validation. This enumeration was added in
        vSphere API 8.0.2.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        GENERIC = None
        """
        A generic error. Check the ``message`` property for more information. This
        class attribute was added in vSphere API 8.0.2.0.

        """
        ADDITIONAL_PROPERTY = None
        """
        A property that is not specified in the schema was found. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        INVALID_ENUM_OPTION = None
        """
        The value of an enum property does not match one of the allowed values.
        This class attribute was added in vSphere API 8.0.2.0.

        """
        INVALID_TYPE = None
        """
        The value of a property is not the expected type. This class attribute was
        added in vSphere API 8.0.2.0.

        """
        MAX_STRING_LENGTH = None
        """
        The length of a string is larger than the maximum allowed. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        MIN_STRING_LENGTH = None
        """
        The length of a string is smaller than the minimum allowed. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        MISSING_REQUIRED = None
        """
        A required property is missing. This class attribute was added in vSphere
        API 8.0.2.0.

        """
        INVALID_UNION_TAG = None
        """
        A property that is dependent on another property is invalid. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        DUPLICATE_INSTANCE_ID = None
        """
        An instance has an instance ID that was already used in another instance.
        This class attribute was added in vSphere API 8.0.2.0.

        """
        MAX_ARRAY_LENGTH = None
        """
        The length of an array is larger than the maximum allowed. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        MIN_ARRAY_LENGTH = None
        """
        The length of an array is smaller than the minimum allowed. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        MAX_VALUE = None
        """
        The value of a numeric property is larger than the maximum allowed. This
        class attribute was added in vSphere API 8.0.2.0.

        """
        MIN_VALUE = None
        """
        The value of a numeric property is smaller than the minimum allowed. This
        class attribute was added in vSphere API 8.0.2.0.

        """
        PATTERN_MISMATCH = None
        """
        The value of a string property does not match the allowed pattern. This
        class attribute was added in vSphere API 8.0.2.0.

        """
        SCHEMA_NOT_FOUND = None
        """
        A configuration was found for software that is not in the image associated
        with the cluster. This class attribute was added in vSphere API 8.0.2.0.

        """
        NULL_VALUE = None
        """
        A property has a null value. This class attribute was added in vSphere API
        8.0.2.0.

        """
        INVALID_DELETE_DEFAULT = None
        """
        The property is only valid for mutable default configurations. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        HOST_SPECIFIC_IN_PROFILE = None
        """
        The property is host-specific, but was found in the profile section. This
        class attribute was added in vSphere API 8.0.2.0.

        """
        NOT_HOST_SPECIFIC = None
        """
        The property is not host-specific, but was found in the host-specific
        section. This class attribute was added in vSphere API 8.0.2.0.

        """
        MISSING_INSTANCE_ID = None
        """
        An instance does not have the required ID property. This class attribute
        was added in vSphere API 8.0.2.0.

        """
        EMPTY_PROPERTY = None
        """
        An object or array property is empty. This class attribute was added in
        vSphere API 8.0.2.0.

        """
        KEY_IN_HOST_OVERRIDE = None
        """
        The configuration exists in both host-override and host-specific sections.
        This class attribute was added in vSphere API 8.0.2.0.

        """
        PLACEHOLDER_FOUND = None
        """
        The property contains a placeholder that must be replaced. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        PROPERTY_NAME_MISMATCH = None
        """
        A property name does not match the required pattern. This class attribute
        was added in vSphere API 8.0.2.0.

        """
        MISSING_REQUIRED_PROFILE_INSTANCE = None
        """
        The host-specific configuration refers to an instance that does not exist
        in the profile section. This class attribute was added in vSphere API
        8.0.2.0.

        """
        MISSING_REQUIRED_PROFILE_KEY = None
        """
        The host-specific configuration refers to a configuration key that does not
        exist in the profile section. This class attribute was added in vSphere API
        8.0.2.0.

        """
        HOST_SPECIFIC_KEY_IN_OVERRIDE = None
        """
        A host-specific configuration was found in the host-override section. This
        class attribute was added in vSphere API 8.0.2.0.

        """
        UNION_CASE_WITHOUT_UNION_TAG = None
        """
        A union-case property was provided, but the corresponding union tag
        property was not set. This class attribute was added in vSphere API
        8.0.2.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ErrorType` instance.
            """
            Enum.__init__(string)

    ErrorType._set_values({
        'GENERIC': ErrorType('GENERIC'),
        'ADDITIONAL_PROPERTY': ErrorType('ADDITIONAL_PROPERTY'),
        'INVALID_ENUM_OPTION': ErrorType('INVALID_ENUM_OPTION'),
        'INVALID_TYPE': ErrorType('INVALID_TYPE'),
        'MAX_STRING_LENGTH': ErrorType('MAX_STRING_LENGTH'),
        'MIN_STRING_LENGTH': ErrorType('MIN_STRING_LENGTH'),
        'MISSING_REQUIRED': ErrorType('MISSING_REQUIRED'),
        'INVALID_UNION_TAG': ErrorType('INVALID_UNION_TAG'),
        'DUPLICATE_INSTANCE_ID': ErrorType('DUPLICATE_INSTANCE_ID'),
        'MAX_ARRAY_LENGTH': ErrorType('MAX_ARRAY_LENGTH'),
        'MIN_ARRAY_LENGTH': ErrorType('MIN_ARRAY_LENGTH'),
        'MAX_VALUE': ErrorType('MAX_VALUE'),
        'MIN_VALUE': ErrorType('MIN_VALUE'),
        'PATTERN_MISMATCH': ErrorType('PATTERN_MISMATCH'),
        'SCHEMA_NOT_FOUND': ErrorType('SCHEMA_NOT_FOUND'),
        'NULL_VALUE': ErrorType('NULL_VALUE'),
        'INVALID_DELETE_DEFAULT': ErrorType('INVALID_DELETE_DEFAULT'),
        'HOST_SPECIFIC_IN_PROFILE': ErrorType('HOST_SPECIFIC_IN_PROFILE'),
        'NOT_HOST_SPECIFIC': ErrorType('NOT_HOST_SPECIFIC'),
        'MISSING_INSTANCE_ID': ErrorType('MISSING_INSTANCE_ID'),
        'EMPTY_PROPERTY': ErrorType('EMPTY_PROPERTY'),
        'KEY_IN_HOST_OVERRIDE': ErrorType('KEY_IN_HOST_OVERRIDE'),
        'PLACEHOLDER_FOUND': ErrorType('PLACEHOLDER_FOUND'),
        'PROPERTY_NAME_MISMATCH': ErrorType('PROPERTY_NAME_MISMATCH'),
        'MISSING_REQUIRED_PROFILE_INSTANCE': ErrorType('MISSING_REQUIRED_PROFILE_INSTANCE'),
        'MISSING_REQUIRED_PROFILE_KEY': ErrorType('MISSING_REQUIRED_PROFILE_KEY'),
        'HOST_SPECIFIC_KEY_IN_OVERRIDE': ErrorType('HOST_SPECIFIC_KEY_IN_OVERRIDE'),
        'UNION_CASE_WITHOUT_UNION_TAG': ErrorType('UNION_CASE_WITHOUT_UNION_TAG'),
    })
    ErrorType._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.configuration.detailed_validation_error.error_type',
        ErrorType))

DetailedValidationError._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.detailed_validation_error', {
        'hosts': type.OptionalType(type.ListType(type.IdType())),
        'message': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
        'type': type.ReferenceType(__name__, 'DetailedValidationError.ErrorType'),
        'pattern': type.OptionalType(type.StringType()),
        'expected_type': type.OptionalType(type.StringType()),
        'instance_id': type.OptionalType(type.StringType()),
        'property_name': type.OptionalType(type.StringType()),
        'maximum_length': type.OptionalType(type.IntegerType()),
        'minimum_length': type.OptionalType(type.IntegerType()),
        'maximum_value': type.OptionalType(type.IntegerType()),
        'minimum_value': type.OptionalType(type.IntegerType()),
        'dependency_error': type.OptionalType(type.ReferenceType(__name__, 'DependencyError')),
        'component': type.OptionalType(type.StringType()),
        'group': type.OptionalType(type.StringType()),
        'key': type.OptionalType(type.StringType()),
        'path': type.OptionalType(type.StringType()),
        'required_property': type.OptionalType(type.StringType()),
    },
    DetailedValidationError,
    False,
    None))



class ValidationError(VapiStruct):
    """
    The ``ValidationError`` class contains attributes that describes a
    validation error in the configuration. This class was added in vSphere API
    8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 path=None,
                 messages=None,
                ):
        """
        :type  path: :class:`str`
        :param path: Full path to the configuration or the property within the
            configuration which was found to be invalid. This attribute was
            added in vSphere API 8.0.1.0.
        :type  messages: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param messages: Localized error message describing the validation error. This
            attribute was added in vSphere API 8.0.1.0.
        """
        self.path = path
        self.messages = messages
        VapiStruct.__init__(self)


ValidationError._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.validation_error', {
        'path': type.StringType(),
        'messages': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
    },
    ValidationError,
    False,
    None))



class ValidationResult(VapiStruct):
    """
    This ``ValidationResult`` class contains attributes that describe the
    result of validating a configuration document. This class was added in
    vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 valid=None,
                 errors=None,
                ):
        """
        :type  valid: :class:`bool`
        :param valid: This boolean flag indicates whether the configuration document
            validated successfully with no validation errors. This attribute
            was added in vSphere API 8.0.1.0.
        :type  errors: :class:`list` of :class:`ValidationError` or ``None``
        :param errors: Lists all validation errors identified in the configuration
            document. This attribute was added in vSphere API 8.0.1.0.
            This is set when :attr:`ValidationResult.valid` is false.
        """
        self.valid = valid
        self.errors = errors
        VapiStruct.__init__(self)


ValidationResult._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.validation_result', {
        'valid': type.BooleanType(),
        'errors': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ValidationError'))),
    },
    ValidationResult,
    False,
    None))



class ImpactInfo(VapiStruct):
    """
    This ``ImpactInfo`` class contains attributes that describes the Impact if
    the host is not compliant against the desired configuration. This class was
    added in vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 impact=None,
                 info=None,
                ):
        """
        :type  impact: :class:`ImpactType`
        :param impact: This field indicates the ESXi host impact on applying the desired
            configuration. This attribute was added in vSphere API 8.0.1.0.
        :type  info: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param info: This field represents the list of impact information describing the
            configuration changes needed on the host to reach the desired
            state. This attribute was added in vSphere API 8.0.1.0.
        """
        self.impact = impact
        self.info = info
        VapiStruct.__init__(self)


ImpactInfo._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.impact_info', {
        'impact': type.ReferenceType(__name__, 'ImpactType'),
        'info': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
    },
    ImpactInfo,
    False,
    None))



class HostPrecheckResult(VapiStruct):
    """
    This ``HostPrecheckResult`` class contains attributes that describes the
    Precheck API result on a host. This class was added in vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 status=None,
                 summary=None,
                 validation_errors=None,
                 impact=None,
                 precheck_result=None,
                ):
        """
        :type  status: :class:`HostStatus`
        :param status: This field represents the status of the precheck request for this
            host. {link HostStatus#status} is ERROR or SKIPPED, if precheck was
            not completed on the host due to some error or if health checks
            failed. If precheck failed due to host validation errors, details
            are specified in :attr:`HostPrecheckResult.validation_errors`. If
            precheck failed due to generic error, details are specified in the
            :attr:`HostPrecheckResult.summary`. Health check result is
            specified in :attr:`HostPrecheckResult.precheck_result`. This
            attribute was added in vSphere API 8.0.1.0.
        :type  summary: :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param summary: Summarizing precheck operation on the host. This attribute was
            added in vSphere API 8.0.1.0.
        :type  validation_errors: :class:`list` of :class:`ValidationError` or ``None``
        :param validation_errors: This field represents the validation errors if the desired
            configuration specified is not valid. This attribute was added in
            vSphere API 8.0.1.0.
            This field is :class:`set` if #HostStatus#status is ERROR due to
            host returning validation errors.
        :type  impact: :class:`ImpactInfo` or ``None``
        :param impact: This field represents the impact on the host to reach the desired
            configuration state. This attribute was added in vSphere API
            8.0.1.0.
            This field is :class:`set` if there are no validation errors on the
            host. The :attr:`HostStatus.status` may be OK or ERROR.
        :type  precheck_result: :class:`com.vmware.esx.settings_client.StatusInfo` or ``None``
        :param precheck_result: This field represents the health check results from the host, if
            the host needs to be put in maintenance mode or to be rebooted.
            This attribute was added in vSphere API 8.0.1.0.
            This field is :class:`set` if there are not validation errors and
            health checks are run on the host. The :attr:`HostStatus.status`
            may be OK or ERROR.
        """
        self.status = status
        self.summary = summary
        self.validation_errors = validation_errors
        self.impact = impact
        self.precheck_result = precheck_result
        VapiStruct.__init__(self)


HostPrecheckResult._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.host_precheck_result', {
        'status': type.ReferenceType(__name__, 'HostStatus'),
        'summary': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
        'validation_errors': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ValidationError'))),
        'impact': type.OptionalType(type.ReferenceType(__name__, 'ImpactInfo')),
        'precheck_result': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'StatusInfo')),
    },
    HostPrecheckResult,
    False,
    None))



class ClusterPrecheckResult(VapiStruct):
    """
    The ``PrecheckResult`` class contains attributes that describe precheck
    status of applying the desired document to a group of hosts. This class was
    added in vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 status=None,
                 commit=None,
                 software_commit=None,
                 end_time=None,
                 summary=None,
                 remediation_summary=None,
                 remediation_notes=None,
                 validation_errors=None,
                 host_info=None,
                 host_precheck=None,
                 precheck_result=None,
                 successful_hosts=None,
                 failed_hosts=None,
                 skipped_hosts=None,
                ):
        """
        :type  status: :class:`ClusterPrecheckResult.Status`
        :param status: Overall status of precheck on the cluster. Operation is sucessfull
            when precheck is run on all hosts successfully and no validation or
            precheck errors are detected. This attribute was added in vSphere
            API 8.0.1.0.
        :type  commit: :class:`str` or ``None``
        :param commit: This identifier refers to the commit action of importing the
            desired configuration document. This attribute was added in vSphere
            API 8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.esx.settings.commit``. When methods return a value of
            this class as a return value, the attribute will be an identifier
            for the resource type: ``com.vmware.esx.settings.commit``.
            This field is s not set for a precheck of a draft configuration.
        :type  software_commit: :class:`str`
        :param software_commit: The current commit ID for the software associated with the cluster.
            This attribute was added in vSphere API 8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.esx.settings.commit``. When methods return a value of
            this class as a return value, the attribute will be an identifier
            for the resource type: ``com.vmware.esx.settings.commit``.
        :type  end_time: :class:`datetime.datetime`
        :param end_time: Precheck completion time. This attribute was added in vSphere API
            8.0.1.0.
        :type  summary: :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param summary: Summarizing precheck operation on the host and cluster. This
            attribute was added in vSphere API 8.0.1.0.
        :type  remediation_summary: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param remediation_summary: Summarizing remediation stating number of hosts needing reboot and
            maintenance mode during remediation and number of precheck errors
            on host and cluster. This attribute was added in vSphere API
            8.0.1.0.
        :type  remediation_notes: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param remediation_notes: Static notes to the user describing steps that will be taken during
            remediation. This attribute was added in vSphere API 8.0.1.0.
        :type  validation_errors: :class:`list` of :class:`ValidationError` or ``None``
        :param validation_errors: This field represents the validation errors if the desired
            configuration specified is not valid. This attribute was added in
            vSphere API 8.0.3.0.
            This field is :class:`set` if  is ERROR due to validation errors.
        :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
        :param host_info: Map of host IDs to hostname. This attribute was added in vSphere
            API 8.0.1.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``HostSystem``. When methods return a value of this class as
            a return value, the key in the attribute :class:`dict` will be an
            identifier for the resource type: ``HostSystem``.
        :type  host_precheck: :class:`dict` of :class:`str` and :class:`HostPrecheckResult`
        :param host_precheck: Map of host IDs to their precheck results. If
            :attr:`ClusterPrecheckResult.status` is ERROR, This field will
            contain Validation errors or Host Impact and Health Check errors.
            If :attr:`ClusterPrecheckResult.status` is OK, This field will
            contain Impact and Health Check information. This attribute was
            added in vSphere API 8.0.1.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``HostSystem``. When methods return a value of this class as
            a return value, the key in the attribute :class:`dict` will be an
            identifier for the resource type: ``HostSystem``.
        :type  precheck_result: :class:`com.vmware.esx.settings_client.StatusInfo` or ``None``
        :param precheck_result: This field represents the precheck results on the cluster, if any
            one host in the cluster needs to be put in maintenance mode or to
            be rebooted. This attribute was added in vSphere API 8.0.1.0.
            This field is set if cluster prechecks are invoked.
        :type  successful_hosts: :class:`set` of :class:`str`
        :param successful_hosts: Hosts in this cluster where the precheck was sucessfully run. This
            attribute was added in vSphere API 8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``HostSystem``. When methods return a value of this class as a
            return value, the attribute will contain identifiers for the
            resource type: ``HostSystem``.
        :type  failed_hosts: :class:`set` of :class:`str`
        :param failed_hosts: Hosts in this cluster where the precheck failed to run. This
            attribute was added in vSphere API 8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``HostSystem``. When methods return a value of this class as a
            return value, the attribute will contain identifiers for the
            resource type: ``HostSystem``.
        :type  skipped_hosts: :class:`set` of :class:`str`
        :param skipped_hosts: Hosts in this cluster where the precheck was not tried because the
            host was disconnected. This attribute was added in vSphere API
            8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``HostSystem``. When methods return a value of this class as a
            return value, the attribute will contain identifiers for the
            resource type: ``HostSystem``.
        """
        self.status = status
        self.commit = commit
        self.software_commit = software_commit
        self.end_time = end_time
        self.summary = summary
        self.remediation_summary = remediation_summary
        self.remediation_notes = remediation_notes
        self.validation_errors = validation_errors
        self.host_info = host_info
        self.host_precheck = host_precheck
        self.precheck_result = precheck_result
        self.successful_hosts = successful_hosts
        self.failed_hosts = failed_hosts
        self.skipped_hosts = skipped_hosts
        VapiStruct.__init__(self)


    class Status(Enum):
        """
        The ``ClusterPrecheckResult.Status`` class contains the possible statuses
        of the Precheck API on the cluster. This enumeration was added in vSphere
        API 8.0.1.0.

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
        The task is in-progress. This class attribute was added in vSphere API
        8.0.1.0.

        """
        OK = None
        """
        The operation completed successfully. This class attribute was added in
        vSphere API 8.0.1.0.

        """
        ERROR = None
        """
        The operation failed with errors. This class attribute was added in vSphere
        API 8.0.1.0.

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
        'ERROR': Status('ERROR'),
    })
    Status._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.configuration.cluster_precheck_result.status',
        Status))

ClusterPrecheckResult._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.cluster_precheck_result', {
        'status': type.ReferenceType(__name__, 'ClusterPrecheckResult.Status'),
        'commit': type.OptionalType(type.IdType()),
        'software_commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
        'end_time': type.DateTimeType(),
        'summary': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
        'remediation_summary': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        'remediation_notes': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        'validation_errors': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ValidationError'))),
        'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
        'host_precheck': type.MapType(type.IdType(), type.ReferenceType(__name__, 'HostPrecheckResult')),
        'precheck_result': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'StatusInfo')),
        'successful_hosts': type.SetType(type.IdType()),
        'failed_hosts': type.SetType(type.IdType()),
        'skipped_hosts': type.SetType(type.IdType()),
    },
    ClusterPrecheckResult,
    False,
    None))



class ImportResult(VapiStruct):
    """
    This ``ImportResult`` class contains attributes that describe the result of
    importing a configuration document in the cluster. This class was added in
    vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """

    _validator_list = [
        UnionValidator(
            'status',
            {
                'OK' : [('commit', True)],
                'ERROR' : [('errors', True)],
                'RUNNING' : [],
                'CANCELED' : [],
            }
        ),
    ]



    def __init__(self,
                 status=None,
                 commit=None,
                 errors=None,
                ):
        """
        :type  status: :class:`ImportResult.Status`
        :param status: 
        :type  commit: :class:`str`
        :param commit: This identifier refers to the commit action of importing the
            desired configuration document. This identifier can be used in the
            apply API. This attribute was added in vSphere API 8.0.1.0.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.esx.settings.commit``. When methods return a value of
            this class as a return value, the attribute will be an identifier
            for the resource type: ``com.vmware.esx.settings.commit``.
            This attribute is optional and it is only relevant when the value
            of ``status`` is :attr:`ImportResult.Status.OK`.
        :type  errors: :class:`list` of :class:`ValidationError`
        :param errors: Lists all validation errors identified in the configuration
            document. This attribute was added in vSphere API 8.0.1.0.
            This is set when #success is false.
        """
        self.status = status
        self.commit = commit
        self.errors = errors
        VapiStruct.__init__(self)


    class Status(Enum):
        """
        This enum indicates whether the configuration document was imported
        successfully in the cluster. This enumeration was added in vSphere API
        8.0.1.0.

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
        The task is in-progress. This class attribute was added in vSphere API
        8.0.1.0.

        """
        OK = None
        """


        """
        ERROR = None
        """


        """
        CANCELED = None
        """


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
        'ERROR': Status('ERROR'),
        'CANCELED': Status('CANCELED'),
    })
    Status._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.configuration.import_result.status',
        Status))

ImportResult._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.import_result', {
        'status': type.ReferenceType(__name__, 'ImportResult.Status'),
        'commit': type.OptionalType(type.IdType()),
        'errors': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ValidationError'))),
    },
    ImportResult,
    False,
    None))



class DraftImportResult(VapiStruct):
    """
    The ``DraftImportResult`` class contains attributes that describe the
    result of importing the desired configuration for a cluster into a draft.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """

    _validator_list = [
        UnionValidator(
            'status',
            {
                'OK' : [('draft', True)],
                'ERROR' : [('error', True)],
                'RUNNING' : [],
                'CANCELED' : [],
            }
        ),
    ]



    def __init__(self,
                 status=None,
                 draft=None,
                 error=None,
                 warnings=None,
                ):
        """
        :type  status: :class:`DraftImportResult.Status`
        :param status: Status of importing desired configuration.
        :type  draft: :class:`str`
        :param draft: This identifier refers to the commit action of importing the
            desired configuration document. This identifier can be used in the
            apply API.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``. When methods return a value of
            this class as a return value, the attribute will be an identifier
            for the resource type: ``com.vmware.esx.settings.draft``.
            This attribute is optional and it is only relevant when the value
            of ``status`` is :attr:`DraftImportResult.Status.OK`.
        :type  error: :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param error: Localized message describing the error encountered while importing
            desired configuration. The import operation will fail if the
            configuration document is an invalid JSON.
            This attribute is optional and it is only relevant when the value
            of ``status`` is :attr:`DraftImportResult.Status.ERROR`.
        :type  warnings: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
        :param warnings: Any issues found during the import are reported in this list.
        """
        self.status = status
        self.draft = draft
        self.error = error
        self.warnings = warnings
        VapiStruct.__init__(self)


    class Status(Enum):
        """
        The ``DraftImportResult.Status`` class contains the possible status codes
        describing the result of importing desired configuration for a cluster.

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
        The task is in-progress.

        """
        OK = None
        """
        Desired configuration imported successfully.

        """
        ERROR = None
        """
        Desired configuration import failed with error.

        """
        CANCELED = None
        """


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
        'ERROR': Status('ERROR'),
        'CANCELED': Status('CANCELED'),
    })
    Status._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.configuration.draft_import_result.status',
        Status))

DraftImportResult._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.draft_import_result', {
        'status': type.ReferenceType(__name__, 'DraftImportResult.Status'),
        'draft': type.OptionalType(type.IdType()),
        'error': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        'warnings': type.OptionalType(type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'))),
    },
    DraftImportResult,
    False,
    None))



class ExportResult(VapiStruct):
    """
    This ``ExportResult`` class contains attributes that describe the result of
    exporting configuration from the cluster. This class was added in vSphere
    API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 config=None,
                ):
        """
        :type  config: :class:`str`
        :param config: Configuration of the cluster encoded as JSON. This attribute was
            added in vSphere API 8.0.1.0.
        """
        self.config = config
        VapiStruct.__init__(self)


ExportResult._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.export_result', {
        'config': type.StringType(),
    },
    ExportResult,
    False,
    None))



class ConfigurationSpec(VapiStruct):
    """
    The ``ConfigurationSpec`` class contains attributes that describe the
    desired configuration that is associated with a cluster. This class was
    added in vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 spec=None,
                ):
        """
        :type  spec: :class:`str`
        :param spec: Desired configuration document. This attribute was added in vSphere
            API 8.0.1.0.
        """
        self.spec = spec
        VapiStruct.__init__(self)


ConfigurationSpec._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.configuration_spec', {
        'spec': type.StringType(),
    },
    ConfigurationSpec,
    False,
    None))



class ReferenceHostInfo(VapiStruct):
    """
    The ``ReferenceHostInfo`` class contains attributes that describe the host
    that was used as a reference for generating the schema. This class was
    added in vSphere API 8.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """

    _validator_list = [
        UnionValidator(
            'status',
            {
                'OK' : [('host', True), ('name', True)],
                'DISCONNECTED' : [('host', True), ('name', True)],
                'UNAVAILABLE' : [],
            }
        ),
    ]



    def __init__(self,
                 status=None,
                 host=None,
                 name=None,
                 summary=None,
                ):
        """
        :type  status: :class:`ReferenceHostInfo.Status`
        :param status: The current status of the reference host. This attribute was added
            in vSphere API 8.0.3.0.
        :type  host: :class:`str`
        :param host: The ID of the reference host. This attribute was added in vSphere
            API 8.0.3.0.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``HostSystem``. When methods return a value of this class as a
            return value, the attribute will be an identifier for the resource
            type: ``HostSystem``.
            This attribute is optional and it is only relevant when the value
            of ``status`` is one of :attr:`ReferenceHostInfo.Status.OK` or
            :attr:`ReferenceHostInfo.Status.DISCONNECTED`.
        :type  name: :class:`str`
        :param name: The name of the reference host. This attribute was added in vSphere
            API 8.0.3.0.
            This attribute is optional and it is only relevant when the value
            of ``status`` is one of :attr:`ReferenceHostInfo.Status.OK` or
            :attr:`ReferenceHostInfo.Status.DISCONNECTED`.
        :type  summary: :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param summary: A summary of the reference host status. This attribute was added in
            vSphere API 8.0.3.0.
        """
        self.status = status
        self.host = host
        self.name = name
        self.summary = summary
        VapiStruct.__init__(self)


    class Status(Enum):
        """
        The status of the reference host. This enumeration was added in vSphere API
        8.0.3.0.

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
        The reference host is in the cluster and connected. This class attribute
        was added in vSphere API 8.0.3.0.

        """
        DISCONNECTED = None
        """
        The reference host is in the cluster, but disconnected. This class
        attribute was added in vSphere API 8.0.3.0.

        """
        UNAVAILABLE = None
        """
        There is no reference host or it is no longer in the cluster. This class
        attribute was added in vSphere API 8.0.3.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Status` instance.
            """
            Enum.__init__(string)

    Status._set_values({
        'OK': Status('OK'),
        'DISCONNECTED': Status('DISCONNECTED'),
        'UNAVAILABLE': Status('UNAVAILABLE'),
    })
    Status._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.configuration.reference_host_info.status',
        Status))

ReferenceHostInfo._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.reference_host_info', {
        'status': type.ReferenceType(__name__, 'ReferenceHostInfo.Status'),
        'host': type.OptionalType(type.IdType()),
        'name': type.OptionalType(type.StringType()),
        'summary': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
    },
    ReferenceHostInfo,
    False,
    None))



class SchemaResult(VapiStruct):
    """
    The ``SchemaResult`` class contains attributes that describe the
    configuration schema associated with the cluster. This class was added in
    vSphere API 8.0.1.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """

    _validator_list = [
        UnionValidator(
            'source',
            {
                'HOST' : [('reference_host', True)],
                'IMAGE_PROFILE' : [],
            }
        ),
    ]



    def __init__(self,
                 source=None,
                 schema=None,
                 reference_host=None,
                ):
        """
        :type  source: :class:`SchemaResult.Source`
        :param source: The source of this schema. This attribute was added in vSphere API
            8.0.3.0.
            This attribute is optional because it was added in a newer version
            than its parent node.
        :type  schema: :class:`str`
        :param schema: The configuration schema associated with the cluster. This
            attribute was added in vSphere API 8.0.1.0.
        :type  reference_host: :class:`ReferenceHostInfo`
        :param reference_host: If the source of this schema was a reference, this field will be
            populated with the current status of the host. This attribute was
            added in vSphere API 8.0.3.0.
            This attribute is optional and it is only relevant when the value
            of ``source`` is :attr:`SchemaResult.Source.HOST`.
        """
        self.source = source
        self.schema = schema
        self.reference_host = reference_host
        VapiStruct.__init__(self)


    class Source(Enum):
        """
        The possible sources of the schema. This enumeration was added in vSphere
        API 8.0.3.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        IMAGE_PROFILE = None
        """
        The schema was derived from a VLCM image profile. This class attribute was
        added in vSphere API 8.0.3.0.

        """
        HOST = None
        """
        The schema was extracted from a reference host. This class attribute was
        added in vSphere API 8.0.3.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Source` instance.
            """
            Enum.__init__(string)

    Source._set_values({
        'IMAGE_PROFILE': Source('IMAGE_PROFILE'),
        'HOST': Source('HOST'),
    })
    Source._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.configuration.schema_result.source',
        Source))

SchemaResult._set_binding_type(type.StructType(
    'com.vmware.esx.settings.clusters.configuration.schema_result', {
        'source': type.OptionalType(type.ReferenceType(__name__, 'SchemaResult.Source')),
        'schema': type.StringType(),
        'reference_host': type.OptionalType(type.ReferenceType(__name__, 'ReferenceHostInfo')),
    },
    SchemaResult,
    False,
    None))



class AuditRecords(VapiInterface):
    """
    The ``AuditRecords`` class provides methods to get the auditing records of
    the configuration actions performed on a cluster in vCenter Server. This
    class was added in vSphere API 8.0.2.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.configuration.audit_records'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _AuditRecordsStub)
        self._VAPI_OPERATION_IDS = {}

    class OperationType(VapiStruct):
        """
        The ``AuditRecords.OperationType`` class contains class attributes used to
        represent all possible config manager operations. This class was added in
        vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """
        IMPORT = "Import"
        """
        Represents Import config manager operation
        :func:`com.vmware.esx.settings.clusters_client.Configuration.import_config`.
        This class attribute was added in vSphere API 8.0.2.0.

        """
        EXPORT = "Export"
        """
        Represents Export config manager operation
        :func:`com.vmware.esx.settings.clusters_client.Configuration.export_config`.
        This class attribute was added in vSphere API 8.0.2.0.

        """
        REMEDIATE = "Remediate"
        """
        Represents Remediate config manager operation
        :func:`com.vmware.esx.settings.clusters_client.Configuration.apply`. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        CHECK_COMPLIANCE = "Checkcompliance"
        """
        Represents Check compliance config manager operation
        com.vmware.esx.settings.clusters.. This class attribute was added in vSphere
        API 8.0.2.0.

        """
        PRE_CHECK = "Precheck"
        """
        Represents Pre-check config manager operation
        :func:`com.vmware.esx.settings.clusters_client.Configuration.precheck`. This
        class attribute was added in vSphere API 8.0.2.0.

        """
        TRANSITION_ENABLE = "Transition-Enable"
        """
        Represents Transition enable config manager operation
        com.vmware.esx.settings.clusters.enablement.. This class attribute was added in
        vSphere API 8.0.2.0.

        """
        DRAFT_LIST = "Draft-List"
        """
        Represents Configmanager Draft List :func:`Drafts.list`. This class attribute
        was added in vSphere API 8.0.2.0.

        """
        DRAFT_CREATE = "Draft-Create"
        """
        Represents Configmanager Draft Create :func:`Drafts.create`. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        DRAFT_IMPORT_FROM_HOST = "Draft-ImportFromHost"
        """
        Represents Configmanager Draft Import from host
        :mod:`com.vmware.esx.settings.clusters.configuration_client`. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        DRAFT_GET = "Draft-Get"
        """
        Represents Configmanager Draft Get :func:`Drafts.get`. This class attribute was
        added in vSphere API 8.0.2.0.

        """
        DRAFT_EXPORT_CONFIG = "Draft-ExportConfig"
        """
        Represents Configmanager Draft Export Config
        :mod:`com.vmware.esx.settings.clusters.configuration_client`. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        DRAFT_UPDATE = "Draft-Update"
        """
        Represents Configmanager Draft Update :func:`Drafts.update`. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        DRAFT_SHOW_CHANGES = "Draft-ShowChanges"
        """
        Represents Configmanager Draft Show Changes
        :mod:`com.vmware.esx.settings.clusters.configuration_client`. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        DRAFT_CHECK_COMPLIANCE = "Draft-CheckCompliance"
        """
        Represents Configmanager Draft Check Compliance
        :mod:`com.vmware.esx.settings.clusters.configuration_client`. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        DRAFT_PRECHECK = "Draft-Precheck"
        """
        Represents Configmanager Draft Precheck
        :mod:`com.vmware.esx.settings.clusters.configuration_client`. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        DRAFT_DELETE = "Draft-Delete"
        """
        Represents Configmanager Draft Delete :func:`Drafts.delete`. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        DRAFT_APPLY = "Draft-Apply"
        """
        Represents Configmanager Draft Apply
        com.vmware.esx.settings.clusters.configuration.Drafts#impact. This class
        attribute was added in vSphere API 8.0.2.0.

        """
        OPERATIONS = ["Import", "Export", "Remediate", "Checkcompliance", "Precheck", "Transition-Enable", "Draft-List", "Draft-Create", "Draft-ImportFromHost", "Draft-Get", "Draft-ExportConfig", "Draft-Update", "Draft-ShowChanges", "Draft-CheckCompliance", "Draft-Precheck", "Draft-Delete", "Draft-Apply"]
        """
        Represents all audit enabled config manager operations. This class attribute
        was added in vSphere API 8.0.2.0.

        """




        def __init__(self,
                    ):
            """
            """
            VapiStruct.__init__(self)


    OperationType._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.audit_records.operation_type', {
        },
        OperationType,
        False,
        None))


    class TimePeriod(VapiStruct):
        """
        The ``AuditRecords.TimePeriod`` class contains
        :attr:`AuditRecords.TimePeriod.start` and
        :attr:`AuditRecords.TimePeriod.end` to get audit records for a specific
        time period. This class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     start=None,
                     end=None,
                    ):
            """
            :type  start: :class:`datetime.datetime`
            :param start: List of audit records that match the given start time i.e. occurred
                after the DateTime start. This attribute was added in vSphere API
                8.0.2.0.
            :type  end: :class:`datetime.datetime`
            :param end: List of audit records that match the given end time i.e. occurred
                before the DateTime end. This attribute was added in vSphere API
                8.0.2.0.
            """
            self.start = start
            self.end = end
            VapiStruct.__init__(self)


    TimePeriod._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.audit_records.time_period', {
            'start': type.DateTimeType(),
            'end': type.DateTimeType(),
        },
        TimePeriod,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``AuditRecords.FilterSpec`` class contains attributes used to filter
        the audit records. If multiple attributes are specified, only records
        matching all of the attributes match the filter. This class was added in
        vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'time_duration',
                {
                    'CUSTOM' : [('time_period', True)],
                    'THREE_MONTHS' : [],
                    'SIX_MONTHS' : [],
                    'YEAR' : [],
                }
            ),
        ]



        def __init__(self,
                     operations=None,
                     usernames=None,
                     time_duration=None,
                     time_period=None,
                    ):
            """
            :type  operations: :class:`set` of :class:`str` or ``None``
            :param operations: List of audit records that match the given operations An operation
                in operations can be any of 
                
                * Import
                * Export
                * Remediate
                * Checkcompliance
                * Precheck
                * Transition-Enable
                * Draft-List
                * Draft-Create
                * Draft-ImportFromHost
                * Draft-Get
                * Draft-ExportConfig
                * Draft-Update
                * Draft-ShowChanges
                * Draft-CheckCompliance
                * Draft-Precheck
                * Draft-Delete
                * Draft-Apply
                
                . This attribute was added in vSphere API 8.0.2.0.
                If None or empty, records with any operation match the filter.
            :type  usernames: :class:`set` of :class:`str` or ``None``
            :param usernames: List of audit records that match the given users. This attribute
                was added in vSphere API 8.0.2.0.
                If None or empty, records with any users match the filter.
            :type  time_duration: :class:`AuditRecords.FilterSpec.Timeframe` or ``None``
            :param time_duration: List of audit records that match
                ``AuditRecords.FilterSpec.Timeframe``, valid values are
                THREE_MONTHS, SIX_MONTHS, YEAR, CUSTOM. i.e. For ex: records within
                last 3 months. This attribute was added in vSphere API 8.0.2.0.
                If None or empty, last one year audit records match the filter.
            :type  time_period: :class:`AuditRecords.TimePeriod`
            :param time_period: List of audit records that match the given start time i.e. occurred
                after the :attr:`AuditRecords.TimePeriod.start` and the given end
                time i.e. before the :attr:`AuditRecords.TimePeriod.end`. This
                attribute was added in vSphere API 8.0.2.0.
                This attribute is optional and it is only relevant when the value
                of ``timeDuration`` is
                :attr:`AuditRecords.FilterSpec.Timeframe.CUSTOM`.
            """
            self.operations = operations
            self.usernames = usernames
            self.time_duration = time_duration
            self.time_period = time_period
            VapiStruct.__init__(self)


        class Timeframe(Enum):
            """
            List of audit records that match the given time frame i.e. For ex: occurred
            within last 30 days. This enumeration was added in vSphere API 8.0.2.0.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            THREE_MONTHS = None
            """
            To indicate last 3 months audit records. This class attribute was added in
            vSphere API 8.0.2.0.

            """
            SIX_MONTHS = None
            """
            To indicate last 6 months audit records. This class attribute was added in
            vSphere API 8.0.2.0.

            """
            YEAR = None
            """
            To indicate last 1 year audit records. This class attribute was added in
            vSphere API 8.0.2.0.

            """
            CUSTOM = None
            """
            To indicate custom time frame for getting audit records. Users can specify
            start time and end time. This class attribute was added in vSphere API
            8.0.2.0.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Timeframe` instance.
                """
                Enum.__init__(string)

        Timeframe._set_values({
            'THREE_MONTHS': Timeframe('THREE_MONTHS'),
            'SIX_MONTHS': Timeframe('SIX_MONTHS'),
            'YEAR': Timeframe('YEAR'),
            'CUSTOM': Timeframe('CUSTOM'),
        })
        Timeframe._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.clusters.configuration.audit_records.filter_spec.timeframe',
            Timeframe))

    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.audit_records.filter_spec', {
            'operations': type.OptionalType(type.SetType(type.StringType())),
            'usernames': type.OptionalType(type.SetType(type.StringType())),
            'time_duration': type.OptionalType(type.ReferenceType(__name__, 'AuditRecords.FilterSpec.Timeframe')),
            'time_period': type.OptionalType(type.ReferenceType(__name__, 'AuditRecords.TimePeriod')),
        },
        FilterSpec,
        False,
        None))


    class OperationDetails(VapiStruct):
        """
        The ``AuditRecords.OperationDetails`` class contains Operation Details of
        an operation. This class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     error=None,
                     task_id=None,
                     draft_id=None,
                     cancelled=None,
                    ):
            """
            :type  error: :class:`Exception` or ``None``
            :param error: Error occurred during the operation. This attribute was added in
                vSphere API 8.0.2.0.
                error shall only be set if configmanager operation is a task
            :type  task_id: :class:`str` or ``None``
            :param task_id: TaskId of the operation. This attribute was added in vSphere API
                8.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.cis.task``. When methods return a value of this class
                as a return value, the attribute will be an identifier for the
                resource type: ``com.vmware.cis.task``.
                taskId shall only be set if configmanager operation is a task
            :type  draft_id: :class:`str` or ``None``
            :param draft_id: Draft ID of the draft operation. This attribute was added in
                vSphere API 8.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.draft``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.draft``.
                draftId shall only be set if this is an operaton on draft
            :type  cancelled: :class:`bool` or ``None``
            :param cancelled: Indicates if the operation was cancelled. This attribute was added
                in vSphere API 8.0.2.0.
                cancelled shall only be set if configmanager operation is a task
            """
            self.error = error
            self.task_id = task_id
            self.draft_id = draft_id
            self.cancelled = cancelled
            VapiStruct.__init__(self)


    OperationDetails._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.audit_records.operation_details', {
            'error': type.OptionalType(type.AnyErrorType()),
            'task_id': type.OptionalType(type.IdType()),
            'draft_id': type.OptionalType(type.IdType()),
            'cancelled': type.OptionalType(type.BooleanType()),
        },
        OperationDetails,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``AuditRecords.Info`` class contains Audit Info of an operation for a
        cluster in vCenter Server. This class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'status',
                {
                    'PENDING' : [],
                    'RUNNING' : [],
                    'BLOCKED' : [],
                    'SUCCEEDED' : [],
                    'FAILED' : [],
                }
            ),
        ]



        def __init__(self,
                     cluster_id=None,
                     operation=None,
                     username=None,
                     start_time=None,
                     end_time=None,
                     status=None,
                     operation_details=None,
                    ):
            """
            :type  cluster_id: :class:`str`
            :param cluster_id: Identifier of the cluster. This attribute was added in vSphere API
                8.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            :type  operation: :class:`str`
            :param operation: Name of the operation which can be one of 
                
                * Import
                * Export
                * Remediate
                * Checkcompliance
                * Precheck
                * Transition-Enable
                * Draft-List
                * Draft-Create
                * Draft-ImportFromHost
                * Draft-Get
                * Draft-ExportConfig
                * Draft-Update
                * Draft-ShowChanges
                * Draft-CheckCompliance
                * Draft-Precheck
                * Draft-Delete
                * Draft-Apply
                
                . This attribute was added in vSphere API 8.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be one of ``Import``, ``Export``, ``Remediate``,
                ``Checkcompliance``, ``Precheck``, ``Transition-Enable``,
                ``Draft-List``, ``Draft-Create``, ``Draft-ImportFromHost``,
                ``Draft-Get``, ``Draft-ExportConfig``, ``Draft-Update``,
                ``Draft-ShowChanges``, ``Draft-CheckCompliance``,
                ``Draft-Precheck``, ``Draft-Delete``, or ``Draft-Apply``. When
                methods return a value of this class as a return value, the
                attribute will be one of ``Import``, ``Export``, ``Remediate``,
                ``Checkcompliance``, ``Precheck``, ``Transition-Enable``,
                ``Draft-List``, ``Draft-Create``, ``Draft-ImportFromHost``,
                ``Draft-Get``, ``Draft-ExportConfig``, ``Draft-Update``,
                ``Draft-ShowChanges``, ``Draft-CheckCompliance``,
                ``Draft-Precheck``, ``Draft-Delete``, or ``Draft-Apply``.
            :type  username: :class:`str`
            :param username: User who initiated the operation. This attribute was added in
                vSphere API 8.0.2.0.
            :type  start_time: :class:`datetime.datetime` or ``None``
            :param start_time: Time when the operation :attr:`AuditRecords.Info.operation` was
                started. This attribute was added in vSphere API 8.0.2.0.
                startTime might not be available for a task.
            :type  end_time: :class:`datetime.datetime` or ``None``
            :param end_time: Time when the operation :attr:`AuditRecords.Info.operation` was
                completed. This attribute was added in vSphere API 8.0.2.0.
                endTime might not be available for a task.
            :type  status: :class:`com.vmware.cis.task_client.Status`
            :param status: Status of the operation :attr:`AuditRecords.Info.operation`. This
                attribute was added in vSphere API 8.0.2.0.
            :type  operation_details: :class:`AuditRecords.OperationDetails` or ``None``
            :param operation_details: Details of the operation. This attribute was added in vSphere API
                8.0.2.0.
                operationdetails might not be available for an operation which is
                not a task.
            """
            self.cluster_id = cluster_id
            self.operation = operation
            self.username = username
            self.start_time = start_time
            self.end_time = end_time
            self.status = status
            self.operation_details = operation_details
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.audit_records.info', {
            'cluster_id': type.IdType(resource_types='ClusterComputeResource'),
            'operation': type.StringType(),
            'username': type.StringType(),
            'start_time': type.OptionalType(type.DateTimeType()),
            'end_time': type.OptionalType(type.DateTimeType()),
            'status': type.ReferenceType('com.vmware.cis.task_client', 'Status'),
            'operation_details': type.OptionalType(type.ReferenceType(__name__, 'AuditRecords.OperationDetails')),
        },
        Info,
        False,
        None))



    def list(self,
             cluster,
             filters=None,
             ):
        """
        Retrieves audit information about the configuration actions performed
        on the cluster. This method was added in vSphere API 8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  filters: :class:`AuditRecords.FilterSpec` or ``None``
        :param filters: used to filter the audit records.
            If None returns all available audit records associated with
            ``cluster``
        :rtype: :class:`list` of :class:`AuditRecords.Info`
        :return: audit Information about the cluster associated with ``cluster``.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the session id is missing from the request or the corresponding
            session object cannot be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't not have the required privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.View``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.View``.
        """
        return self._invoke('list',
                            {
                            'cluster': cluster,
                            'filters': filters,
                            })
class Drafts(VapiInterface):
    """
    The ``Drafts`` class provides methods to manage cluster configuration
    drafts. This class was added in vSphere API 8.0.2.0.
    """
    RESOURCE_TYPE = "com.vmware.esx.settings.draft"
    """
    Resource type for draft resource. This class attribute was added in vSphere API
    8.0.2.0.

    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.configuration.drafts'
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
        self._VAPI_OPERATION_IDS.update({'import_from_host_task': 'import_from_host$task'})
        self._VAPI_OPERATION_IDS.update({'check_compliance_task': 'check_compliance$task'})
        self._VAPI_OPERATION_IDS.update({'precheck_task': 'precheck$task'})

    class State(Enum):
        """
        The states of the draft configuration. This enumeration was added in
        vSphere API 8.0.2.0.

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
        Configuration draft is valid. This class attribute was added in vSphere API
        8.0.2.0.

        """
        INVALID = None
        """
        Configuration draft is invalid. This class attribute was added in vSphere
        API 8.0.2.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`State` instance.
            """
            Enum.__init__(string)

    State._set_values({
        'VALID': State('VALID'),
        'INVALID': State('INVALID'),
    })
    State._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.clusters.configuration.drafts.state',
        State))


    class Metadata(VapiStruct):
        """
        The ``Drafts.Metadata`` class defines the metadata information about
        configuration draft. This class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     id=None,
                     parent_id=None,
                     owner=None,
                     state=None,
                     revision=None,
                     creation_time=None,
                     modified_time=None,
                     precheck_task=None,
                     image_reference_host=None,
                    ):
            """
            :type  id: :class:`str`
            :param id: The draft identifier. This attribute was added in vSphere API
                8.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.draft``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.draft``.
            :type  parent_id: :class:`str`
            :param parent_id: The identifier of the parent commit. This attribute was added in
                vSphere API 8.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  owner: :class:`str`
            :param owner: Owner of the configuration draft. This attribute was added in
                vSphere API 8.0.2.0.
            :type  state: :class:`Drafts.State`
            :param state: State of the configuration draft. This attribute was added in
                vSphere API 8.0.2.0.
            :type  revision: :class:`long`
            :param revision: The current revision of this draft. Any updates to the draft will
                increment this value. This value should be included in calls to
                :func:`Drafts.update` so that concurrent changes can be detected.
                This attribute was added in vSphere API 8.0.2.0.
            :type  creation_time: :class:`datetime.datetime`
            :param creation_time: Creation time of the configuration draft. This attribute was added
                in vSphere API 8.0.2.0.
            :type  modified_time: :class:`datetime.datetime`
            :param modified_time: Last modified time of the configuration draft. This attribute was
                added in vSphere API 8.0.2.0.
            :type  precheck_task: :class:`str` or ``None``
            :param precheck_task: The ID of the precheck task that was last run for this draft. This
                attribute was added in vSphere API 8.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.cis.task``. When methods return a value of this class
                as a return value, the attribute will be an identifier for the
                resource type: ``com.vmware.cis.task``.
                This field is None if precheck has not been done since the last
                modification.
            :type  image_reference_host: :class:`str` or ``None``
            :param image_reference_host: The ID of the host that is used as a reference for the cluster
                image. This attribute was added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``HostSystem``.
                This field is None if the cluster is managed by VLCM.
            """
            self.id = id
            self.parent_id = parent_id
            self.owner = owner
            self.state = state
            self.revision = revision
            self.creation_time = creation_time
            self.modified_time = modified_time
            self.precheck_task = precheck_task
            self.image_reference_host = image_reference_host
            VapiStruct.__init__(self)


    Metadata._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.metadata', {
            'id': type.IdType(resource_types='com.vmware.esx.settings.draft'),
            'parent_id': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'owner': type.StringType(),
            'state': type.ReferenceType(__name__, 'Drafts.State'),
            'revision': type.IntegerType(),
            'creation_time': type.DateTimeType(),
            'modified_time': type.DateTimeType(),
            'precheck_task': type.OptionalType(type.IdType()),
            'image_reference_host': type.OptionalType(type.IdType()),
        },
        Metadata,
        False,
        None))


    class ValidationErrors(VapiStruct):
        """
        The ``Drafts.ValidationErrors`` class contains schema-based validation
        errors for a given property. This class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     display_path=None,
                     errors=None,
                    ):
            """
            :type  display_path: :class:`list` of :class:`str`
            :param display_path: A list of the display names for components of the property path.
                This attribute was added in vSphere API 8.0.2.0.
            :type  errors: :class:`list` of :class:`DetailedValidationError`
            :param errors: Localized error message describing the validation error. This
                attribute was added in vSphere API 8.0.2.0.
            """
            self.display_path = display_path
            self.errors = errors
            VapiStruct.__init__(self)


    ValidationErrors._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.validation_errors', {
            'display_path': type.ListType(type.StringType()),
            'errors': type.ListType(type.ReferenceType(__name__, 'DetailedValidationError')),
        },
        ValidationErrors,
        False,
        None))


    class ValidationDetails(VapiStruct):
        """
        The ``Drafts.ValidationDetails`` class contains all validation errors
        related to the draft configuration. This class was added in vSphere API
        8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     errors=None,
                    ):
            """
            :type  errors: :class:`dict` of :class:`str` and :class:`Drafts.ValidationErrors`
            :param errors: Map of JSON-Pointers to properties in the draft configuration that
                have validation errors based on the schema and host-level
                validations. This attribute was added in vSphere API 8.0.2.0.
            """
            self.errors = errors
            VapiStruct.__init__(self)


    ValidationDetails._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.validation_details', {
            'errors': type.MapType(type.StringType(), type.ReferenceType(__name__, 'Drafts.ValidationErrors')),
        },
        ValidationDetails,
        False,
        None))


    class ModificationInfo(VapiStruct):
        """
        The ``Drafts.ModificationInfo`` class contains information about a
        modification to a property in the configuration. This class was added in
        vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     display_path=None,
                     original_path=None,
                    ):
            """
            :type  display_path: :class:`list` of :class:`str`
            :param display_path: A list of the display names for components of the property path.
                This attribute was added in vSphere API 8.0.2.0.
            :type  original_path: :class:`str` or ``None``
            :param original_path: This attribute was added in vSphere API 8.0.2.0.
                If set, it contains a JSON-Pointer to the corresponding property in
                the original document. Otherwise, this modification is an addition
                to the draft.
            """
            self.display_path = display_path
            self.original_path = original_path
            VapiStruct.__init__(self)


    ModificationInfo._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.modification_info', {
            'display_path': type.ListType(type.StringType()),
            'original_path': type.OptionalType(type.StringType()),
        },
        ModificationInfo,
        False,
        None))


    class DeletionInfo(VapiStruct):
        """
        The ``Drafts.DeletionInfo`` class contains information about a property
        that was deleted from the draft configuration. This class was added in
        vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     display_path=None,
                    ):
            """
            :type  display_path: :class:`list` of :class:`str`
            :param display_path: A list of the display names for components of the property path.
                This attribute was added in vSphere API 8.0.2.0.
            """
            self.display_path = display_path
            VapiStruct.__init__(self)


    DeletionInfo._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.deletion_info', {
            'display_path': type.ListType(type.StringType()),
        },
        DeletionInfo,
        False,
        None))


    class ChangeDetails(VapiStruct):
        """
        The ``Drafts.ChangeDetails`` class contains information about changes made
        in the draft when compared against the current desired document. This class
        was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     modified_properties=None,
                     deleted_properties=None,
                    ):
            """
            :type  modified_properties: :class:`dict` of :class:`str` and :class:`Drafts.ModificationInfo`
            :param modified_properties: Captures the properties that were added/modified in this draft. The
                map keys are JSON-Pointers that refer to the properties in the
                draft that are modifications. The values contain information about
                the property and, in the case of a modification, the location of
                the corresponding property in the desired document. This attribute
                was added in vSphere API 8.0.2.0.
            :type  deleted_properties: :class:`dict` of :class:`str` and :class:`Drafts.DeletionInfo`
            :param deleted_properties: Captures the properties that were deleted from this draft. The map
                keys are JSON-Pointers that refer to the properties in the desired
                document that were deleted. This attribute was added in vSphere API
                8.0.2.0.
            """
            self.modified_properties = modified_properties
            self.deleted_properties = deleted_properties
            VapiStruct.__init__(self)


    ChangeDetails._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.change_details', {
            'modified_properties': type.MapType(type.StringType(), type.ReferenceType(__name__, 'Drafts.ModificationInfo')),
            'deleted_properties': type.MapType(type.StringType(), type.ReferenceType(__name__, 'Drafts.DeletionInfo')),
        },
        ChangeDetails,
        False,
        None))


    class ConflictPropertyInfo(VapiStruct):
        """
        The ``Drafts.ConflictPropertyInfo`` class contains information about
        conflicts that have been detected when attempting to merge configuration
        changes that have been committed by other users. This class was added in
        vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     property_path=None,
                    ):
            """
            :type  property_path: :class:`str`
            :param property_path: The path refers to the conflicting property in the cluster
                configuration document. This attribute was added in vSphere API
                8.0.2.0.
            """
            self.property_path = property_path
            VapiStruct.__init__(self)


    ConflictPropertyInfo._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.conflict_property_info', {
            'property_path': type.StringType(),
        },
        ConflictPropertyInfo,
        False,
        None))


    class ConflictDetails(VapiStruct):
        """


        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     properties=None,
                    ):
            """
            :type  properties: :class:`dict` of :class:`str` and :class:`Drafts.ConflictPropertyInfo`
            :param properties: Map of properties in the current draft that were changed and
                conflict with changes that were applied to the cluster
                configuration document since this draft was created. This attribute
                was added in vSphere API 8.0.2.0.
            """
            self.properties = properties
            VapiStruct.__init__(self)


    ConflictDetails._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.conflict_details', {
            'properties': type.MapType(type.StringType(), type.ReferenceType(__name__, 'Drafts.ConflictPropertyInfo')),
        },
        ConflictDetails,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Drafts.Info`` class defines the information about configuration
        draft. This class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'host_id_to_UUID': 'host_id_to_uuid',
                                }

        def __init__(self,
                     metadata=None,
                     errors=None,
                     changes=None,
                     conflicts=None,
                     host_info=None,
                     host_id_to_uuid=None,
                     config=None,
                    ):
            """
            :type  metadata: :class:`Drafts.Metadata`
            :param metadata: Metadata about the configuration draft. This attribute was added in
                vSphere API 8.0.2.0.
            :type  errors: :class:`Drafts.ValidationDetails` or ``None``
            :param errors: This attribute was added in vSphere API 8.0.2.0.
                If set, there were validation errors detected in the draft
                configuration.
            :type  changes: :class:`Drafts.ChangeDetails` or ``None``
            :param changes: This attribute was added in vSphere API 8.0.2.0.
                If set, there are changes in this draft configuration from the
                current desired configuration.
            :type  conflicts: :class:`Drafts.ConflictDetails` or ``None``
            :param conflicts: This attribute was added in vSphere API 8.0.2.0.
                If set, there are changes in this draft configuration that conflict
                with changes applied by a different user.
            :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: A mapping of BIOS UUIDs for every host in the cluster to
                information about that host. The host-specific/host-override
                sections of the configuration use BIOS UUIDs to identify hosts, so
                this information can be useful to get details about hosts mentioned
                there. This attribute was added in vSphere API 8.0.2.0.
            :type  host_id_to_uuid: :class:`dict` of :class:`str` and :class:`str`
            :param host_id_to_uuid: Map of host IDs to BIOS UUIDs. This attribute was added in vSphere
                API 8.0.2.0.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  config: :class:`str`
            :param config: Configuration specification associated with the draft, encoded as
                JSON. This attribute was added in vSphere API 8.0.2.0.
            """
            self.metadata = metadata
            self.errors = errors
            self.changes = changes
            self.conflicts = conflicts
            self.host_info = host_info
            self.host_id_to_uuid = host_id_to_uuid
            self.config = config
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.info', {
            'metadata': type.ReferenceType(__name__, 'Drafts.Metadata'),
            'errors': type.OptionalType(type.ReferenceType(__name__, 'Drafts.ValidationDetails')),
            'changes': type.OptionalType(type.ReferenceType(__name__, 'Drafts.ChangeDetails')),
            'conflicts': type.OptionalType(type.ReferenceType(__name__, 'Drafts.ConflictDetails')),
            'host_info': type.MapType(type.StringType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
            'host_id_to_UUID': type.MapType(type.IdType(), type.StringType()),
            'config': type.StringType(),
        },
        Info,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``Drafts.CreateSpec`` class contains information used when creating a
        draft. This class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     config=None,
                     image_reference_host=None,
                    ):
            """
            :type  config: :class:`str` or ``None``
            :param config: The initial configuration for the draft. This attribute was added
                in vSphere API 8.0.2.0.
                If not specified, the current desired configuration for the cluster
                will be used.
            :type  image_reference_host: :class:`str` or ``None``
            :param image_reference_host: The host to use as the desired image for the cluster when VLCM is
                not in use. This attribute was added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``HostSystem``.
                If not specified, the previously used reference host will be
                carried over.
            """
            self.config = config
            self.image_reference_host = image_reference_host
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.create_spec', {
            'config': type.OptionalType(type.StringType()),
            'image_reference_host': type.OptionalType(type.IdType()),
        },
        CreateSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``Drafts.UpdateSpec`` class contains the new configuration for the
        draft. This class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     expected_revision=None,
                     config=None,
                    ):
            """
            :type  expected_revision: :class:`long` or ``None``
            :param expected_revision: When supplied, this revision value will be compared against the
                draft's current revision as returned in
                :attr:`Drafts.Metadata.revision` to ensure no other changes have
                been applied. This attribute was added in vSphere API 8.0.2.0.
            :type  config: :class:`str`
            :param config: The new cluster configuration for this draft, encoded as JSON. This
                attribute was added in vSphere API 8.0.2.0.
            """
            self.expected_revision = expected_revision
            self.config = config
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.update_spec', {
            'expected_revision': type.OptionalType(type.IntegerType()),
            'config': type.StringType(),
        },
        UpdateSpec,
        False,
        None))


    class ApplySpec(VapiStruct):
        """
        The ``Drafts.ApplySpec`` class contains attributes that are used to create
        a new commit. This class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     message=None,
                     apply_policy_spec=None,
                    ):
            """
            :type  message: :class:`str` or ``None``
            :param message: Message to include with the commit. This attribute was added in
                vSphere API 8.0.2.0.
                If None, message is set to empty string.
            :type  apply_policy_spec: :class:`com.vmware.esx.settings.clusters.policies.apply_client.Effective.EffectivePolicySpec` or ``None``
            :param apply_policy_spec: The parameter can be used to override the default remediation
                policies for the apply task. This attribute was added in vSphere
                API 8.0.2.0.
                if None the default cluster remediation policies are used.
            """
            self.message = message
            self.apply_policy_spec = apply_policy_spec
            VapiStruct.__init__(self)


    ApplySpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.apply_spec', {
            'message': type.OptionalType(type.StringType()),
            'apply_policy_spec': type.OptionalType(type.ReferenceType('com.vmware.esx.settings.clusters.policies.apply_client', 'Effective.EffectivePolicySpec')),
        },
        ApplySpec,
        False,
        None))


    class ApplyResult(VapiStruct):
        """
        The ``Drafts.ApplyResult`` class contains the result of committing a draft.
        This class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     commit=None,
                     apply_task=None,
                    ):
            """
            :type  commit: :class:`str`
            :param commit: The ID of the commit created for this operation. This attribute was
                added in vSphere API 8.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  apply_task: :class:`str` or ``None``
            :param apply_task: If the cluster is not empty, this will be set to the ID of the
                Apply task. This attribute was added in vSphere API 8.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.cis.task``. When methods return a value of this class
                as a return value, the attribute will be an identifier for the
                resource type: ``com.vmware.cis.task``.
            """
            self.commit = commit
            self.apply_task = apply_task
            VapiStruct.__init__(self)


    ApplyResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.apply_result', {
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'apply_task': type.OptionalType(type.IdType()),
        },
        ApplyResult,
        False,
        None))


    class ChangedProperty(VapiStruct):
        """
        The ``Drafts.ChangedProperty`` class contains information about a property
        that is different in this draft from the committed configuration. This
        class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     path=None,
                     current=None,
                     draft=None,
                    ):
            """
            :type  path: :class:`str`
            :param path: A JSON-Pointer that refers to the property that has been changed.
                This attribute was added in vSphere API 8.0.2.0.
            :type  current: :class:`str` or ``None``
            :param current: This attribute was added in vSphere API 8.0.2.0.
                If set, the current value of the property in the cluster
                configuration. If not set, the property does not exist in the
                current cluster configuration.
            :type  draft: :class:`str` or ``None``
            :param draft: This attribute was added in vSphere API 8.0.2.0.
                If set, this is the new value for the property in this draft. If
                not set, the property has been deleted in this draft.
            """
            self.path = path
            self.current = current
            self.draft = draft
            VapiStruct.__init__(self)


    ChangedProperty._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.changed_property', {
            'path': type.StringType(),
            'current': type.OptionalType(type.StringType()),
            'draft': type.OptionalType(type.StringType()),
        },
        ChangedProperty,
        False,
        None))


    class ChangesResult(VapiStruct):
        """
        The ``Drafts.ChangesResult`` class contains a detailed description of the
        differences between this draft and the current desired configuration. This
        class was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     sets=None,
                     adds=None,
                     deletes=None,
                    ):
            """
            :type  sets: :class:`list` of :class:`Drafts.ChangedProperty` or ``None``
            :param sets: This attribute was added in vSphere API 8.0.2.0.
                If set, this contains a list of properties that have been changed
                from one value to another in this draft.
            :type  adds: :class:`list` of :class:`Drafts.ChangedProperty` or ``None``
            :param adds: This attribute was added in vSphere API 8.0.2.0.
                If set, this contains a list of properties that have been added in
                this draft.
            :type  deletes: :class:`list` of :class:`Drafts.ChangedProperty` or ``None``
            :param deletes: This attribute was added in vSphere API 8.0.2.0.
                If set, this contains a list of properties that have been deleted
                in this draft.
            """
            self.sets = sets
            self.adds = adds
            self.deletes = deletes
            VapiStruct.__init__(self)


    ChangesResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.drafts.changes_result', {
            'sets': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Drafts.ChangedProperty'))),
            'adds': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Drafts.ChangedProperty'))),
            'deletes': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Drafts.ChangedProperty'))),
        },
        ChangesResult,
        False,
        None))



    def list(self,
             cluster,
             ):
        """
        Get the active drafts for this cluster. This method was added in
        vSphere API 8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`dict` of :class:`str` and :class:`Drafts.Metadata`
        :return: Map of drafts keyed by their identifiers.
            The key in the return value :class:`dict` will be an identifier for
            the resource type: ``com.vmware.esx.settings.draft``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.View``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.View``.
        """
        return self._invoke('list',
                            {
                            'cluster': cluster,
                            })

    def create(self,
               cluster,
               spec=None,
               ):
        """
        Create a new draft with the given values. If a configuration is
        supplied in the spec, it will be used as the initial value. Otherwise,
        the current desired configuration will be used as the initial value.
        The :attr:`Drafts.Metadata.owner` field will be set to the caller's
        user ID and the :attr:`Drafts.Metadata.parent_id` will be set to the
        current commit ID for the cluster. This method was added in vSphere API
        8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Drafts.CreateSpec` or ``None``
        :param spec: Options used when creating the new draft.
        :rtype: :class:`str`
        :return: 
            The return value will be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            If there is already a draft by this author for this cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the supplied configuration is not valid JSON.
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
        return self._invoke('create',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })


    def import_from_host_task(self,
                         cluster,
                         draft,
                         host,
                         ):
        """
        The API imports the desired configuration from a reference host in the
        cluster. The API also adds host-specific and host-overrides from the
        other hosts in the cluster. Import API does not validate the
        configuration against the schema. The result will specify if the
        configuration was imported successfully. The result will provide
        localized error message if the import operation failed. This method was
        added in vSphere API 8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  draft: :class:`str`
        :param draft: 
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
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
                                'draft': draft,
                                'host': host,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'DraftImportResult'))
        return task_instance

    def get_schema(self,
                   cluster,
                   draft,
                   ):
        """
        Returns the configuration schema associated with this draft. This
        method was added in vSphere API 8.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster on which operation should be performed.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :rtype: :class:`SchemaResult`
        :return: This output structure of type :class:`SchemaResult` containing the
            schema document encoded as JSON.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some other unknown internal error. The accompanying
            error message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If the cluster is not found in the system or no draft associated
            with ``draft`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        return self._invoke('get_schema',
                            {
                            'cluster': cluster,
                            'draft': draft,
                            })

    def get(self,
            cluster,
            draft,
            ):
        """
        Get the cluster configuration and related metadata from this draft.
        This method was added in vSphere API 8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :rtype: :class:`Drafts.Info`
        :return: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` or no draft
            associated with ``draft`` in the system.
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
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            'draft': draft,
                            })

    def export_config(self,
                      cluster,
                      draft,
                      ):
        """
        This API will export the draft configuration associated with the
        cluster. This method was added in vSphere API 8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster on which operation should be performed.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :rtype: :class:`ExportResult`
        :return: This output structure of type
            com.vmware.esx.settings.clusters.Configuration#ExportResult
            contains the configuration document encoded as JSON.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some other unknown internal error. The accompanying
            error message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` or no draft
            associated with ``draft`` in the system.
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
                            'draft': draft,
                            })

    def update(self,
               cluster,
               draft,
               spec,
               ):
        """
        Replace the current configuration in this draft with the supplied one.
        If the supplied configuration is different from the current value, the
        :attr:`Drafts.Metadata.precheck_task` fields will be cleared. If an
        expected revision number is provided, it must match the current
        revision of this draft or a ConcurrentChange exception will be raised.
        If no expected revision number is provided, this check will be skipped
        and the update will go through. This method was added in vSphere API
        8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :type  spec: :class:`Drafts.UpdateSpec`
        :param spec: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` or no draft
            associated with ``draft`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the supplied configuration is not valid JSON.
        :raise: :class:`com.vmware.vapi.std.errors_client.ConcurrentChange` 
            If the expectedRevision in the ``spec`` differs from the draft's
            current revision.
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
        return self._invoke('update',
                            {
                            'cluster': cluster,
                            'draft': draft,
                            'spec': spec,
                            })

    def show_changes(self,
                     cluster,
                     draft,
                     ):
        """
        Get the differences between this draft and the current desired state
        for the cluster. This method was added in vSphere API 8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :rtype: :class:`Drafts.ChangesResult`
        :return: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` or no draft
            associated with ``draft`` in the system.
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
        return self._invoke('show_changes',
                            {
                            'cluster': cluster,
                            'draft': draft,
                            })


    def check_compliance_task(self,
                         cluster,
                         draft,
                         ):
        """
        Check all the hosts in the cluster for compliance with the
        configuration specified in the draft. This method was added in vSphere
        API 8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If an internal error occurred. The accompanying error message will
            give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If API is called on a cluster that is not managed by desired
            configuration management platform.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster``
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.TimedOut` 
            If the API timed out before completion.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('check_compliance$task',
                                {
                                'cluster': cluster,
                                'draft': draft,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'ClusterCompliance'))
        return task_instance


    def precheck_task(self,
                 cluster,
                 draft,
                 ):
        """
        This API will perform impact analysis of the configuration specified in
        the draft on each of the hosts in the cluster. The API will check
        against the desired image schema whether the desired configuration has
        added any requirements for the host to be put in maintenance mode or to
        be rebooted. The API will also invoke plugins which will validate the
        configuration on each hosts in the cluster. If the configuration is
        valid the API will also detect if the host needs to be maintenance mode
        or to be rebooted. If the hosts requires maintenance mode or reboot,
        then the API will run health checks to see the hosts can be put into
        the maintenance mode based on their current state. If any host cannot
        be put into maintenance mode due to health errors, then those errors
        will be reported in the result. The result will also list the
        configurations that will change on applying the configuration in the
        draft. This method was added in vSphere API 8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: The cluster on which to perform impact analysis.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('precheck$task',
                                {
                                'cluster': cluster,
                                'draft': draft,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'ClusterPrecheckResult'))
        return task_instance

    def delete(self,
               cluster,
               draft,
               ):
        """
        Delete this draft. Any changes will be abandoned. This method was added
        in vSphere API 8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` or no draft
            associated with ``draft`` in the system.
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
        return self._invoke('delete',
                            {
                            'cluster': cluster,
                            'draft': draft,
                            })

    def apply(self,
              cluster,
              draft,
              spec=None,
              ):
        """
        Commit this draft and make it the new desired configuration for the
        cluster. The draft must be in the :attr:`Drafts.State.VALID` state for
        this method to succeed. A successful commit will result in the draft
        being deleted. If the cluster is not empty, the Apply API will be
        called with the new desired state. This method was added in vSphere API
        8.0.2.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  draft: :class:`str`
        :param draft: Identifier of the working copy of the document.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.draft``.
        :type  spec: :class:`Drafts.ApplySpec` or ``None``
        :param spec: Additional arguments for the operation.
        :rtype: :class:`Drafts.ApplyResult`
        :return: A structure that contains the ID of the new commit and, if an
            ApplySpec was supplied, the ID of the Apply task.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` or no draft
            associated with ``draft`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If the draft is not in the :attr:`Drafts.State.VALID` state.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.ClusterConfiguration.Remediate``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.ClusterConfiguration.Remediate``.
        """
        return self._invoke('apply',
                            {
                            'cluster': cluster,
                            'draft': draft,
                            'spec': spec,
                            })
class Schema(VapiInterface):
    """
    The ``Schema`` class provides methods to manage the desired configuration
    schema of an ESX cluster. This class was added in vSphere API 8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.configuration.schema'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SchemaStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            cluster,
            ):
        """
        Returns the configuration schema associated with the cluster. This
        method was added in vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`SchemaResult`
        :return: The schema associated with the ``cluster``
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            In case of an unknown internal error.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the ``cluster`` is invalid
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If the schema associated with the ``cluster`` is not found
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is unavailable.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the session is unauthenticated.
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
class _AuditRecordsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'filters': type.OptionalType(type.ReferenceType(__name__, 'AuditRecords.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
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
            url_template='/esx/settings/clusters/{cluster}/configuration/audit-records',
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

        operations = {
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'AuditRecords.Info')),
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
            self, iface_name='com.vmware.esx.settings.clusters.configuration.audit_records',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _DraftsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts',
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

        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.OptionalType(type.ReferenceType(__name__, 'Drafts.CreateSpec')),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts',
            request_body_parameter='spec',
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

        # properties for import_from_host operation
        import_from_host_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
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
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts/{draft}',
            path_variables={
                'cluster': 'cluster',
                'draft': 'draft',
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

        # properties for get_schema operation
        get_schema_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
        })
        get_schema_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        get_schema_input_value_validator_list = [
        ]
        get_schema_output_validator_list = [
        ]
        get_schema_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts/{draft}',
            path_variables={
                'cluster': 'cluster',
                'draft': 'draft',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'getSchema',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts/{draft}',
            path_variables={
                'cluster': 'cluster',
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

        # properties for export_config operation
        export_config_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
        })
        export_config_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
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
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts/{draft}',
            path_variables={
                'cluster': 'cluster',
                'draft': 'draft',
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

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
            'spec': type.ReferenceType(__name__, 'Drafts.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.concurrent_change':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ConcurrentChange'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts/{draft}',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
                'draft': 'draft',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'update',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for show_changes operation
        show_changes_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
        })
        show_changes_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        show_changes_input_value_validator_list = [
        ]
        show_changes_output_validator_list = [
        ]
        show_changes_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts/{draft}',
            path_variables={
                'cluster': 'cluster',
                'draft': 'draft',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'showChanges',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for check_compliance operation
        check_compliance_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
        })
        check_compliance_error_dict = {
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

        }
        check_compliance_input_value_validator_list = [
        ]
        check_compliance_output_validator_list = [
        ]
        check_compliance_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts/{draft}',
            path_variables={
                'cluster': 'cluster',
                'draft': 'draft',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'checkCompliance',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for precheck operation
        precheck_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
        })
        precheck_error_dict = {
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

        }
        precheck_input_value_validator_list = [
        ]
        precheck_output_validator_list = [
        ]
        precheck_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts/{draft}',
            path_variables={
                'cluster': 'cluster',
                'draft': 'draft',
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

        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts/{draft}',
            path_variables={
                'cluster': 'cluster',
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

        # properties for apply operation
        apply_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'draft': type.IdType(resource_types='com.vmware.esx.settings.draft'),
            'spec': type.OptionalType(type.ReferenceType(__name__, 'Drafts.ApplySpec')),
        })
        apply_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        apply_input_value_validator_list = [
        ]
        apply_output_validator_list = [
        ]
        apply_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/configuration/drafts/{draft}',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
                'draft': 'draft',
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

        operations = {
            'list': {
                'input_type': list_input_type,
                'output_type': type.MapType(type.IdType(), type.ReferenceType(__name__, 'Drafts.Metadata')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'create': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.esx.settings.draft'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
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
            'get_schema': {
                'input_type': get_schema_input_type,
                'output_type': type.ReferenceType(__name__, 'SchemaResult'),
                'errors': get_schema_error_dict,
                'input_value_validator_list': get_schema_input_value_validator_list,
                'output_validator_list': get_schema_output_validator_list,
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
            'export_config': {
                'input_type': export_config_input_type,
                'output_type': type.ReferenceType(__name__, 'ExportResult'),
                'errors': export_config_error_dict,
                'input_value_validator_list': export_config_input_value_validator_list,
                'output_validator_list': export_config_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'update': {
                'input_type': update_input_type,
                'output_type': type.VoidType(),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': update_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'show_changes': {
                'input_type': show_changes_input_type,
                'output_type': type.ReferenceType(__name__, 'Drafts.ChangesResult'),
                'errors': show_changes_error_dict,
                'input_value_validator_list': show_changes_input_value_validator_list,
                'output_validator_list': show_changes_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'check_compliance$task': {
                'input_type': check_compliance_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': check_compliance_error_dict,
                'input_value_validator_list': check_compliance_input_value_validator_list,
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
            'delete': {
                'input_type': delete_input_type,
                'output_type': type.VoidType(),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': delete_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'apply': {
                'input_type': apply_input_type,
                'output_type': type.ReferenceType(__name__, 'Drafts.ApplyResult'),
                'errors': apply_error_dict,
                'input_value_validator_list': apply_input_value_validator_list,
                'output_validator_list': apply_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
            'create': create_rest_metadata,
            'import_from_host': import_from_host_rest_metadata,
            'get_schema': get_schema_rest_metadata,
            'get': get_rest_metadata,
            'export_config': export_config_rest_metadata,
            'update': update_rest_metadata,
            'show_changes': show_changes_rest_metadata,
            'check_compliance': check_compliance_rest_metadata,
            'precheck': precheck_rest_metadata,
            'delete': delete_rest_metadata,
            'apply': apply_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.clusters.configuration.drafts',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _SchemaStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        get_error_dict = {
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

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/configuration/schema',
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

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'SchemaResult'),
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
            self, iface_name='com.vmware.esx.settings.clusters.configuration.schema',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'AuditRecords': AuditRecords,
        'Drafts': Drafts,
        'Schema': Schema,
        'reports': 'com.vmware.esx.settings.clusters.configuration.reports_client.StubFactory',
    }

