# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.settings.clusters.
#---------------------------------------------------------------------------

"""
The ``com.vmware.esx.settings.clusters_client`` module provides classes to
manage desired state configuration and software for a cluster of ESX hosts.

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
    The ``Configuration`` class provides methods to manage desired
    configuration of an ESX cluster. This class was added in vSphere API
    8.0.1.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.configuration'
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
        self._VAPI_OPERATION_IDS.update({'apply_task': 'apply$task'})
        self._VAPI_OPERATION_IDS.update({'check_compliance_task': 'check_compliance$task'})
        self._VAPI_OPERATION_IDS.update({'validate_task': 'validate$task'})
        self._VAPI_OPERATION_IDS.update({'precheck_task': 'precheck$task'})
        self._VAPI_OPERATION_IDS.update({'import_config_task': 'import_config$task'})

    class ApplySpec(VapiStruct):
        """
        The ``Configuration.ApplySpec`` class contains attributes that describe the
        specification to be used for applying the desired configuration to a
        cluster. This class was added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     commit=None,
                     hosts=None,
                     apply_policy_spec=None,
                    ):
            """
            :type  commit: :class:`str` or ``None``
            :param commit: The minimum commit identifier of the desired configuration to be
                used during the :func:`Configuration.apply` method. This attribute
                was added in vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
                if None or empty the apply method will use the latest commit to
                fetch the desired configuration.
            :type  hosts: :class:`set` of :class:`str` or ``None``
            :param hosts: The specific hosts within the cluster to be considered during the
                :func:`Configuration.apply` method. This attribute was added in
                vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
                if None or empty the :func:`Configuration.apply` method will
                remediate all hosts within the cluster.
            :type  apply_policy_spec: :class:`com.vmware.esx.settings.clusters.policies.apply_client.Effective.EffectivePolicySpec` or ``None``
            :param apply_policy_spec: The parameter can be used to override the default remediation
                policies for the task. This attribute was added in vSphere API
                8.0.1.0.
                if None the default cluster remediation policies are used.
            """
            self.commit = commit
            self.hosts = hosts
            self.apply_policy_spec = apply_policy_spec
            VapiStruct.__init__(self)


    ApplySpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.apply_spec', {
            'commit': type.OptionalType(type.IdType()),
            'hosts': type.OptionalType(type.SetType(type.IdType())),
            'apply_policy_spec': type.OptionalType(type.ReferenceType('com.vmware.esx.settings.clusters.policies.apply_client', 'Effective.EffectivePolicySpec')),
        },
        ApplySpec,
        False,
        None))


    class ApplyResult(VapiStruct):
        """
        The ``Configuration.ApplyResult`` class contains attributes that describe
        the result of an :func:`Configuration.apply` method. This class was added
        in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     status=None,
                     commit=None,
                     software_commit=None,
                     host_info=None,
                     host_status=None,
                     successful_hosts=None,
                     failed_hosts=None,
                     skipped_hosts=None,
                    ):
            """
            :type  status: :class:`com.vmware.esx.settings.clusters.configuration_client.HostStatus` or ``None``
            :param status: Specifies the aggregated status of the :func:`Configuration.apply`
                method. This attribute was added in vSphere API 8.0.1.0.
                None if the :func:`Configuration.apply` method is in progress.
            :type  commit: :class:`str`
            :param commit: The identifier of the commit used to fetch the desired
                configuration document to be applied to all hosts within the
                cluster. This attribute was added in vSphere API 8.0.1.0.
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
            :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information of the hosts in this cluster to which the desired
                configuration document specified by the
                :attr:`Configuration.ApplyResult.commit` should be applied to. This
                attribute was added in vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  host_status: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings.clusters.configuration_client.HostStatus`
            :param host_status: Status of the hosts in this cluster to which the desired
                configuration specified by the
                :attr:`Configuration.ApplyResult.commit` was applied to. Hosts on
                which the :func:`Configuration.apply` method was successful are
                specified by :attr:`Configuration.ApplyResult.successful_hosts`.
                Hosts on which the apply method failed are specified by
                :attr:`Configuration.ApplyResult.failed_hosts`. Hosts which were
                skipped by the :func:`Configuration.apply` method are specified by
                :attr:`Configuration.ApplyResult.skipped_hosts`. This attribute was
                added in vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  successful_hosts: :class:`set` of :class:`str`
            :param successful_hosts: Hosts in this cluster to which the desired configuration specified
                by the :attr:`Configuration.ApplyResult.commit` has been
                successfully applied to. This attribute was added in vSphere API
                8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  failed_hosts: :class:`set` of :class:`str`
            :param failed_hosts: Hosts in this cluster to which the desired configuration specified
                by the :attr:`Configuration.ApplyResult.commit` failed to be
                applied. This attribute was added in vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  skipped_hosts: :class:`set` of :class:`str`
            :param skipped_hosts: Hosts in this cluster that were skipped by the
                :func:`Configuration.apply` method. This attribute was added in
                vSphere API 8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            """
            self.status = status
            self.commit = commit
            self.software_commit = software_commit
            self.host_info = host_info
            self.host_status = host_status
            self.successful_hosts = successful_hosts
            self.failed_hosts = failed_hosts
            self.skipped_hosts = skipped_hosts
            VapiStruct.__init__(self)


    ApplyResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.apply_result', {
            'status': type.OptionalType(type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'HostStatus')),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'software_commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
            'host_status': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'HostStatus')),
            'successful_hosts': type.SetType(type.IdType()),
            'failed_hosts': type.SetType(type.IdType()),
            'skipped_hosts': type.SetType(type.IdType()),
        },
        ApplyResult,
        False,
        None))


    class Metadata(VapiStruct):
        """
        The ``Configuration.Metadata`` class defines the metadata information about
        configuration commit. This class was added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     id=None,
                     author=None,
                     creation_time=None,
                    ):
            """
            :type  id: :class:`str`
            :param id: The identifier of the commit. This attribute was added in vSphere
                API 8.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  author: :class:`str`
            :param author: Author of the configuration commit. This attribute was added in
                vSphere API 8.0.1.0.
            :type  creation_time: :class:`datetime.datetime`
            :param creation_time: Creation time of the configuration commit. This attribute was added
                in vSphere API 8.0.1.0.
            """
            self.id = id
            self.author = author
            self.creation_time = creation_time
            VapiStruct.__init__(self)


    Metadata._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.metadata', {
            'id': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'author': type.StringType(),
            'creation_time': type.DateTimeType(),
        },
        Metadata,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Configuration.Info`` class defines the information about
        configuration commit. This class was added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     metadata=None,
                     host_info=None,
                     config=None,
                    ):
            """
            :type  metadata: :class:`Configuration.Metadata`
            :param metadata: Metadata about the configuration commit. This attribute was added
                in vSphere API 8.0.1.0.
            :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: A mapping of BIOS UUIDs for every host in the cluster to
                information about that host. The host-specific/host-override
                sections of the configuration use BIOS UUIDs to identify hosts, so
                this information can be useful to get details about hosts mentioned
                there. This attribute was added in vSphere API 8.0.1.0.
            :type  config: :class:`str`
            :param config: Configuration specification associated with the commit, encoded as
                JSON. This attribute was added in vSphere API 8.0.1.0.
            """
            self.metadata = metadata
            self.host_info = host_info
            self.config = config
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.info', {
            'metadata': type.ReferenceType(__name__, 'Configuration.Metadata'),
            'host_info': type.MapType(type.StringType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
            'config': type.StringType(),
        },
        Info,
        False,
        None))


    class ImportSpec(VapiStruct):
        """
        The ``Configuration.ImportSpec`` class contains the desired configuration
        for a cluster and an optional short description of this version of the
        configuration. This class was added in vSphere API 8.0.1.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     config=None,
                     description=None,
                    ):
            """
            :type  config: :class:`str`
            :param config: The cluster configuration, encoded as JSON. This attribute was
                added in vSphere API 8.0.1.0.
            :type  description: :class:`str` or ``None``
            :param description: A description of this version of the configuration. This attribute
                was added in vSphere API 8.0.1.0.
            """
            self.config = config
            self.description = description
            VapiStruct.__init__(self)


    ImportSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.configuration.import_spec', {
            'config': type.StringType(),
            'description': type.OptionalType(type.StringType()),
        },
        ImportSpec,
        False,
        None))



    def get(self,
            cluster,
            commit=None,
            doc_structure=None,
            ):
        """
        Get the cluster configuration and related metadata. The configuration
        returned by this API only contains the user-visible configuration
        properties available for a the cluster. This method was added in
        vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  commit: :class:`str` or ``None``
        :param commit: Identifier of the commit to get.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  doc_structure: :class:`com.vmware.esx.settings.clusters.configuration_client.DocumentStructure` or ``None``
        :param doc_structure: 
        :rtype: :class:`Configuration.Info`
        :return: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` or no commit
            associated with ``commit`` in the system.
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
                            'commit': commit,
                            'doc_structure': doc_structure,
                            })


    def apply_task(self,
              cluster,
              spec,
              ):
        """
        Applies the cluster configuration associated with the cluster on the
        hosts associated with the cluster. This method was added in vSphere API
        8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Configuration.ApplySpec`
        :param spec: The Apply specification.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyInDesiredState` 
            If the cluster is already at the specified commit as described in
            the apply specification.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the :attr:`Configuration.ApplySpec.commit` attribute of ``spec``
            specifies an invalid commit, or the
            :attr:`Configuration.ApplySpec.hosts` attribute of ``spec``
            specifies an invalid host or a host that is not part of the
            cluster, or the ``cluster`` is not managed with a configuration
            specification. Also thrown if the specified ``cluster`` is empty.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no ``cluster`` found in the inventory or no
            :attr:`Configuration.ApplySpec.commit` associated with ``cluster``.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.TimedOut` 
            If the API timed out before completion.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('apply$task',
                                {
                                'cluster': cluster,
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Configuration.ApplyResult'))
        return task_instance


    def check_compliance_task(self,
                         cluster,
                         ):
        """
        Check all the hosts in the cluster for compliance with the desired
        document. This method was added in vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
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
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'ClusterCompliance'))
        return task_instance


    def validate_task(self,
                 cluster,
                 ):
        """
        Check whether the desired cluster configuration is valid. This method
        was added in vSphere API 8.0.1.0.

        .. deprecated:: vSphere API 8.0.2.0
            The desired cluster configuration is validated as part of
            :func:`Configuration.check_compliance`
            :func:`Configuration.precheck` APIs. 

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
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
        task_id = self._invoke('validate$task',
                                {
                                'cluster': cluster,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'ValidationResult'))
        return task_instance


    def precheck_task(self,
                 cluster,
                 ):
        """
        This API will perform precheck of the desired cluster configuration on
        each of the hosts in the cluster. The API will check against the
        desired image schema whether the desired configuration has added any
        requirements for the host to be put in maintenance mode or to be
        rebooted. The API will also invoke plugins provided by the
        configuration owner to detect if the host needs to be put in
        maintenance mode or to be rebooted. If any host needs to be put in
        maintenance mode or rebooted, prechecks will be performed at the
        cluster and host level. The result will specify the validation errors
        if the desired configuration is not valid on the host. If valid, the
        result will specify host impact of the desired configuration, and list
        the configurations that will change on applying the desired
        configuration. If host impact is maintenance mode or reboot, precheck
        results will also be specified in the result. This method was added in
        vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: The cluster on which to perform precheck.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If API is called on a cluster that is not managed by desired
            configuration management platform.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If the cluster is not found in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.TimedOut` 
            If the API timed out before completion.
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


    def import_config_task(self,
                      cluster,
                      spec,
                      ):
        """
        This API replaces the existing desired configuration of the cluster
        with the configuration provided in the input parameter document. The
        API will internally validate the input configuration against the
        configuration schema derived from the cluster software specification
        associated with the cluster. If the input configuration document passes
        validation, then it will be the desired configuration of the cluster.
        The result will specify whether the input document was import
        successfully. The result will also list the validation errors in case
        the import operation failed. This method was added in vSphere API
        8.0.1.0.

        .. deprecated:: vSphere API 8.0.2.0
            Use com.vmware.esx.settings.clusters.configuration.Drafts#Create
            instead. 

        :type  cluster: :class:`str`
        :param cluster: The cluster on which this operation must be performed.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Configuration.ImportSpec`
        :param spec: An ``Configuration.ImportSpec`` that contains the new desired
            configuration for the cluster.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some other unknown internal error. The accompanying
            error message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If the cluster is not found in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('import_config$task',
                                {
                                'cluster': cluster,
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'ImportResult'))
        return task_instance

    def export_config(self,
                      cluster,
                      ):
        """
        This API will export the configuration associated with the cluster.
        This method was added in vSphere API 8.0.1.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster on which operation should be performed.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`com.vmware.esx.settings.clusters.configuration_client.ExportResult`
        :return: This output structure of type
            com.vmware.esx.settings.clusters.Configuration#ExportResult
            contains the configuration document encoded as JSON.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some other unknown internal error. The accompanying
            error message will give more details about the failure.
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
class DepotOverrides(VapiInterface):
    """
    The ``DepotOverrides`` class provides methods to manage software depots
    overriden for a given cluster. In general ESX servers reach out to vCenter
    (VUM) to fetch the metadata and payloads required for lifecycle operations.
    But in ROBO environments ESX clusters can't (or because of bandwidth
    requirements shouldn't) reach out to vCenter to fetch payloads and
    metadata. This class allows setting cluster level overrides for depots. If
    any depots are provided for a cluster, then vCenter level depots are not
    used for that cluster's remediation. These are not synced periodically at
    vCenter and are only used by ESXs for lifecycle operations.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.depot_overrides'
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
        overrides for a given cluster.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     depots=None,
                    ):
            """
            :type  depots: :class:`list` of :class:`DepotOverrides.Depot`
            :param depots: List of the depot overrides.
            """
            self.depots = depots
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.depot_overrides.info', {
            'depots': type.ListType(type.ReferenceType(__name__, 'DepotOverrides.Depot')),
        },
        Info,
        False,
        None))


    class Depot(VapiStruct):
        """
        The ``DepotOverrides.Depot`` class defines the information regarding a
        particular depot override for a given cluster.

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
                file or location to an index.xml file.
            """
            self.location = location
            VapiStruct.__init__(self)


    Depot._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.depot_overrides.depot', {
            'location': type.URIType(),
        },
        Depot,
        False,
        None))



    def get(self,
            cluster,
            ):
        """
        Returns the information about currently configured depot overrides for
        a given cluster.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`DepotOverrides.Info`
        :return: Information about currently configured depot overrides for a given
            cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleSettings.Read``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.lifecycleSettings.Read``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })

    def add(self,
            cluster,
            depot,
            ):
        """
        Adds a new depot override to the list of currently configured depot
        overrides for a given cluster. 
        
        **Warning:** Using HTTP is not secure. Please use HTTPS URLs instead.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  depot: :class:`DepotOverrides.Depot`
        :param depot: Information of a depot override.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If an invalid location is provided.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if depot override with given information already exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSettings.Write``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.lifecycleSettings.Write``.
        """
        return self._invoke('add',
                            {
                            'cluster': cluster,
                            'depot': depot,
                            })

    def remove(self,
               cluster,
               depot,
               ):
        """
        Removes a depot override from the list of currently configured depot
        overrides for a given cluster.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  depot: :class:`DepotOverrides.Depot`
        :param depot: Information of the depot override to be removed.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no depot override with given information or no cluster
            associated with identifier {param.name cluster} in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSettings.Write``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.lifecycleSettings.Write``.
        """
        return self._invoke('remove',
                            {
                            'cluster': cluster,
                            'depot': depot,
                            })
class InstalledImages(VapiInterface):
    """
    The ``InstalledImages`` class provides methods to examine the software
    bundle running on group of ESXi hosts in a cluster. This class was added in
    vSphere API 8.0.3.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.installed_images'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _InstalledImagesStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'extract_task': 'extract$task'})

    class InstalledImage(VapiStruct):
        """
        The ``InstalledImages.InstalledImage`` class contains attributes
        information about installed software image that is running on the group of
        hosts. This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     software_info=None,
                     host_list=None,
                    ):
            """
            :type  software_info: :class:`com.vmware.esx.settings_client.SoftwareInfo`
            :param software_info: Software image installed on group of hosts. This attribute was
                added in vSphere API 8.0.3.0.
            :type  host_list: :class:`set` of :class:`str`
            :param host_list: List of hosts having the same software image. This attribute was
                added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            """
            self.software_info = software_info
            self.host_list = host_list
            VapiStruct.__init__(self)


    InstalledImage._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.installed_images.installed_image', {
            'software_info': type.ReferenceType('com.vmware.esx.settings_client', 'SoftwareInfo'),
            'host_list': type.SetType(type.IdType()),
        },
        InstalledImage,
        False,
        None))


    class ImageCategories(VapiStruct):
        """
        The ``InstalledImages.ImageCategories`` class contains (\\\\@term fields)
        describing software image categorized on pre-defined criteria. This class
        was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     is_highest_and_widely_used_image_equal=None,
                     most_widely_used_image=None,
                     highest_versioned_image=None,
                     host_image_list=None,
                    ):
            """
            :type  is_highest_and_widely_used_image_equal: :class:`bool`
            :param is_highest_and_widely_used_image_equal: Boolean flag indicating if most widely used image and highest
                versioned image is same. If this flag is set, it means
                “mostWidelyUsedImage” and “highestVersionImage” of
                “imageCategories” will contain same software image as value
                otherwise it will contain different value. This attribute was added
                in vSphere API 8.0.3.0.
            :type  most_widely_used_image: :class:`InstalledImages.InstalledImage` or ``None``
            :param most_widely_used_image: This image category contains the software image that is most
                prevalent among the hosts in the cluster. This attribute was added
                in vSphere API 8.0.3.0.
                if None or empty means either there was an error fetching software
                specification of an ESXi host or the hosts in the cluster are
                ineligible to transition to vLCM.
            :type  highest_versioned_image: :class:`InstalledImages.InstalledImage` or ``None``
            :param highest_versioned_image: This image category contains the software image which has highest
                ESXi version in the cluster. This attribute was added in vSphere
                API 8.0.3.0.
                if None or empty means either there was an error fetching software
                specification of an ESXi host or the hosts in the cluster are
                ineligible to transition to vLCM.
            :type  host_image_list: :class:`list` of :class:`InstalledImages.InstalledImage` or ``None``
            :param host_image_list: This list will contain software image running on hosts in the
                cluster excluding “highestVersionedImage” and
                “mostWidelyUsedImage”. This attribute was added in vSphere API
                8.0.3.0.
                if None or empty means there is no ESXi hosts in the cluster
                running software specification which is different than the one
                specified by mostWidelyUsed or highestVersionedImage.
            """
            self.is_highest_and_widely_used_image_equal = is_highest_and_widely_used_image_equal
            self.most_widely_used_image = most_widely_used_image
            self.highest_versioned_image = highest_versioned_image
            self.host_image_list = host_image_list
            VapiStruct.__init__(self)


    ImageCategories._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.installed_images.image_categories', {
            'is_highest_and_widely_used_image_equal': type.BooleanType(),
            'most_widely_used_image': type.OptionalType(type.ReferenceType(__name__, 'InstalledImages.InstalledImage')),
            'highest_versioned_image': type.OptionalType(type.ReferenceType(__name__, 'InstalledImages.InstalledImage')),
            'host_image_list': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'InstalledImages.InstalledImage'))),
        },
        ImageCategories,
        False,
        None))


    class InstalledImageInfo(VapiStruct):
        """
        The ``InstalledImages.InstalledImageInfo`` class contains attributes
        describing software image running on hosts underneath the cluster and its
        relevant metadata. This class was added in vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     completion_time=None,
                     uniform_image=None,
                     status=None,
                     successful_hosts=None,
                     failed_hosts=None,
                     unsupported_hosts=None,
                     image_categories=None,
                     host_notifications=None,
                     host_info=None,
                     orphaned_vibs=None,
                     notifications=None,
                    ):
            """
            :type  completion_time: :class:`datetime.datetime`
            :param completion_time: Timestamp describing the completion of generate candidate image
                operation. This attribute was added in vSphere API 8.0.3.0.
            :type  uniform_image: :class:`bool`
            :param uniform_image: If this flag is set, it means all hosts in cluster are running the
                same software image. In this case, “mostWidelyUsedImage” and
                “highestVersionImage” of “imageCategories” will contain same
                software image as value and subsequently
                “isHighestAndWidelyUsedImageEqual” flag will also be set. If this
                flag is not set, then depending upon the software image running in
                hosts “imageCategories” fields will be filled. This attribute was
                added in vSphere API 8.0.3.0.
            :type  status: :class:`InstalledImages.InstalledImageInfo.Status`
            :param status: Execution status of the task. If it's not SUCCESS then the
                :attr:`InstalledImages.InstalledImageInfo.notifications` attribute
                of this class can be inspected for more information. This attribute
                was added in vSphere API 8.0.3.0.
            :type  successful_hosts: :class:`list` of :class:`str`
            :param successful_hosts: List of Hosts for which software image has extracted. This
                attribute was added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  failed_hosts: :class:`list` of :class:`str`
            :param failed_hosts: List of hosts for which no software image has extracted. This
                attribute was added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  unsupported_hosts: :class:`list` of :class:`str`
            :param unsupported_hosts: List of hosts that were skipped for extracting software image. Host
                will be skipped when software version is less than the supported
                version. This attribute was added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  image_categories: :class:`InstalledImages.ImageCategories`
            :param image_categories: Various categories of software image running on hosts in the
                cluster. This attribute was added in vSphere API 8.0.3.0.
            :type  host_notifications: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.Notifications`
            :param host_notifications: Notifications stating any error or orphaned vibs etc on Hosts. This
                attribute was added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information about the hosts in this cluster for which checks have
                been requested to be run. This attribute was added in vSphere API
                8.0.3.0.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  orphaned_vibs: :class:`dict` of :class:`str` and :class:`list` of :class:`str`
            :param orphaned_vibs: Information about the orphaned vibs available on the hosts
                underlying cluster. Here Key is the orphaned vibs and value is the
                list of hosts where these orphaned vibs have installed. orphaned
                vibs formats are orphaned vibs name(version). This attribute was
                added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the value
                in the attribute :class:`dict` must be an identifier for the
                resource type: ``HostSystem``. When methods return a value of this
                class as a return value, the value in the attribute :class:`dict`
                will be an identifier for the resource type: ``HostSystem``.
            :type  notifications: :class:`dict` of :class:`InstalledImages.InstalledImageInfo.OperationType` and :class:`com.vmware.esx.settings_client.Notifications`
            :param notifications: Various notifications received and segregated based on operation
                type while generating the report. If the task's status is
                ELIGIBILITY_CHECK_FAILURE then the notifications corresponding to
                the ELIGIBILITY_CHECK key can be inspected for more informaiton.
                For any other task status the notifications corresponding to the
                EXTRACT_INSTALLED_IMAGE key can be inspected. This attribute was
                added in vSphere API 8.0.3.0.
            """
            self.completion_time = completion_time
            self.uniform_image = uniform_image
            self.status = status
            self.successful_hosts = successful_hosts
            self.failed_hosts = failed_hosts
            self.unsupported_hosts = unsupported_hosts
            self.image_categories = image_categories
            self.host_notifications = host_notifications
            self.host_info = host_info
            self.orphaned_vibs = orphaned_vibs
            self.notifications = notifications
            VapiStruct.__init__(self)


        class OperationType(Enum):
            """
            The ``InstalledImages.InstalledImageInfo.OperationType`` class will be used
            to distinguish and categorize the notifications generated by various
            operations. This enumeration was added in vSphere API 8.0.3.0.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            ELIGIBILITY_CHECK = None
            """
            Performs enablement check. This check the possibilities whether a cluster
            can be managed with single software image. This class attribute was added
            in vSphere API 8.0.3.0.

            """
            EXTRACT_INSTALLED_IMAGE = None
            """
            Extract Installed image from all the hosts in the cluster. It will check
            for any unsupported hosts, failed hosts, host having orphaned vibs etc.
            This class attribute was added in vSphere API 8.0.3.0.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`OperationType` instance.
                """
                Enum.__init__(string)

        OperationType._set_values({
            'ELIGIBILITY_CHECK': OperationType('ELIGIBILITY_CHECK'),
            'EXTRACT_INSTALLED_IMAGE': OperationType('EXTRACT_INSTALLED_IMAGE'),
        })
        OperationType._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.clusters.installed_images.installed_image_info.operation_type',
            OperationType))

        class Status(Enum):
            """
            The ``InstalledImages.InstalledImageInfo.Status`` class is used to convey
            the status of the extract installed images task. For example, whether it
            was successful or whether some issue occurred during its execution. This
            enumeration was added in vSphere API 8.0.3.0.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            UNAVAILABLE = None
            """
            Indicates that the status of the task is unknown. This could be because the
            task failed before the eligibility check had the chance to run. Another
            reason could be if the cluster has no hosts or if every host in the cluster
            is running a base image version < 7.0.2. This class attribute was added in
            vSphere API 8.0.3.0.

            """
            ELIGIBILITY_CHECK_FAILURE = None
            """
            Indicates there was either an error during the execution of the eligibility
            check or the cluster is not eligible for vLCM management. In either case an
            error will be present in the #notifications field of the InstalledImageInfo
            class. This class attribute was added in vSphere API 8.0.3.0.

            """
            EXTRACT_INSTALLED_IMAGE_FAILURE = None
            """
            Indicates there was an error during the execution of the extract installed
            images task. If this is the case an error will be present in the
            #notifications attribute of the InstalledImageInfo class. This class
            attribute was added in vSphere API 8.0.3.0.

            """
            SUCCESS = None
            """
            Indicates the extract installed images task completed without error. This
            class attribute was added in vSphere API 8.0.3.0.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Status` instance.
                """
                Enum.__init__(string)

        Status._set_values({
            'UNAVAILABLE': Status('UNAVAILABLE'),
            'ELIGIBILITY_CHECK_FAILURE': Status('ELIGIBILITY_CHECK_FAILURE'),
            'EXTRACT_INSTALLED_IMAGE_FAILURE': Status('EXTRACT_INSTALLED_IMAGE_FAILURE'),
            'SUCCESS': Status('SUCCESS'),
        })
        Status._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.clusters.installed_images.installed_image_info.status',
            Status))

    InstalledImageInfo._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.installed_images.installed_image_info', {
            'completion_time': type.DateTimeType(),
            'uniform_image': type.BooleanType(),
            'status': type.ReferenceType(__name__, 'InstalledImages.InstalledImageInfo.Status'),
            'successful_hosts': type.ListType(type.IdType()),
            'failed_hosts': type.ListType(type.IdType()),
            'unsupported_hosts': type.ListType(type.IdType()),
            'image_categories': type.ReferenceType(__name__, 'InstalledImages.ImageCategories'),
            'host_notifications': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
            'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
            'orphaned_vibs': type.MapType(type.StringType(), type.ListType(type.IdType())),
            'notifications': type.MapType(type.ReferenceType(__name__, 'InstalledImages.InstalledImageInfo.OperationType'), type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        InstalledImageInfo,
        False,
        None))




    def extract_task(self,
                cluster,
                ):
        """
        Extract installed images on all the hosts in the cluster. The API will
        work irrespective of whether a cluster is managed by single software
        image or not. If the cluster is not managed by single software image,
        it will first check the possibility to manage with single software
        image and if this check is successful then only it will extract the
        installed images on all the hosts. If the cluster is managed by single
        software image, it will skip eligibility check and directly extract the
        installed images on all the hosts. This method was added in vSphere API
        8.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown error. The accompanying error message will
            give more details about the failure
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the caller is not authorized.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the host does not meet the vLCM transition eligibility criteria
        """
        task_id = self._invoke('extract$task',
                                {
                                'cluster': cluster,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'InstalledImages.InstalledImageInfo'))
        return task_instance

    def get(self,
            cluster,
            ):
        """
        Returns the last extracted installed Image info. This method was added
        in vSphere API 8.0.3.0.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`InstalledImages.InstalledImageInfo`
        :return: last extracted installed images for the cluster
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            If the caller is not authorized.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleSettings.Read``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.lifecycleSettings.Read``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })
class Software(VapiInterface):
    """
    The ``Software`` class provides methods to manage desired software
    specification of an ESX cluster.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.clusters.software'
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
        specification document or image can be exported.

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
        Export software specification document.

        """
        ISO_IMAGE = None
        """
        Export ISO image.

        """
        OFFLINE_BUNDLE = None
        """
        Export offline bundle.

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
        'com.vmware.esx.settings.clusters.software.export_type',
        ExportType))


    class Status(Enum):
        """
        The ``Software.Status`` class defines the status result for a particular
        check.

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
        The check indicates a success.

        """
        WARNING = None
        """
        The check indicates a warning.

        """
        TIMEOUT = None
        """
        The check did not return in a timely manner.

        """
        ERROR = None
        """
        The check indicates an error.

        """
        RETRY = None
        """
        The check failed because of an intermittent error, for example a service is
        overloaded. The client can choose to retry the health check before
        considering the check as failed. This class attribute was added in vSphere
        API 7.0.2.0.

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
        'com.vmware.esx.settings.clusters.software.status',
        Status))


    class ExportSpec(VapiStruct):
        """
        The ``Software.ExportSpec`` class contains information describing how a
        software specification or image should be exported.

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
            :param export_software_spec: Whether to export software specification document.
            :type  export_iso_image: :class:`bool`
            :param export_iso_image: Whether to export ISO image.
            :type  export_offline_bundle: :class:`bool`
            :param export_offline_bundle: Whether to export offline bundle.
            """
            self.export_software_spec = export_software_spec
            self.export_iso_image = export_iso_image
            self.export_offline_bundle = export_offline_bundle
            VapiStruct.__init__(self)


    ExportSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.export_spec', {
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
        cluster. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     commit=None,
                     hosts=None,
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
            :type  hosts: :class:`set` of :class:`str` or ``None``
            :param hosts: The specific hosts within the cluster to be considered during the
                :func:`Software.stage` method. This attribute was added in vSphere
                API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
                if None or empty the :func:`Software.stage` method will stage all
                hosts within the cluster.
            """
            self.commit = commit
            self.hosts = hosts
            VapiStruct.__init__(self)


    StageSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.stage_spec', {
            'commit': type.OptionalType(type.IdType()),
            'hosts': type.OptionalType(type.SetType(type.IdType())),
        },
        StageSpec,
        False,
        None))


    class ApplySpec(VapiStruct):
        """
        The ``Software.ApplySpec`` class contains attributes that describe the
        specification to be used for applying the desired software document to a
        cluster.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     commit=None,
                     hosts=None,
                     accept_eula=None,
                    ):
            """
            :type  commit: :class:`str` or ``None``
            :param commit: The minimum commit identifier of the desired software document to
                be used during the :func:`Software.apply` method.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
                if None or empty the apply method will use the latest commit to
                fetch the desired state document.
            :type  hosts: :class:`set` of :class:`str` or ``None``
            :param hosts: The specific hosts within the cluster to be considered during the
                :func:`Software.apply` method.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
                if None or empty the :func:`Software.apply` method will remediate
                all hosts within the cluster.
            :type  accept_eula: :class:`bool` or ``None``
            :param accept_eula: Accept the VMware End User License Agreement (EULA) before starting
                the :func:`Software.apply` method. The VMware EULA is available for
                download at, https://www.vmware.com/download/eula.html
                if None the :func:`Software.apply` method could fail due to the
                EULA not being accepted.
            """
            self.commit = commit
            self.hosts = hosts
            self.accept_eula = accept_eula
            VapiStruct.__init__(self)


    ApplySpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.apply_spec', {
            'commit': type.OptionalType(type.IdType()),
            'hosts': type.OptionalType(type.SetType(type.IdType())),
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
                None for cluster StageStatus
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
            the desired software specification to hosts within the cluster. This
            enumeration was added in vSphere API 8.0.0.1.

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
            'com.vmware.esx.settings.clusters.software.stage_status.status',
            Status))

    StageStatus._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.stage_status', {
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
        status of an :func:`Software.apply` method.

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
            :param status: The status of the method.
            :type  progress: :class:`com.vmware.cis.task_client.Progress` or ``None``
            :param progress: Progress of the operation. This attribute was added in vSphere API
                7.0.2.1.
                None for cluster ApplyStatus
            :type  start_time: :class:`datetime.datetime`
            :param start_time: Time when the method started.
            :type  end_time: :class:`datetime.datetime`
            :param end_time: Time when the method completed.
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications`
            :param notifications: Notifications providing additional information about the status of
                the method.
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
            the desired software specification to hosts within the cluster.

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
            7.0.1.0.

            """
            OK = None
            """
            The method completed successfully.

            """
            SKIPPED = None
            """
            The method was skipped.

            """
            TIMED_OUT = None
            """
            The method timed out.

            """
            ERROR = None
            """
            The method encountered an unspecified error.

            """
            RETRY_PENDING = None
            """
            The method is being scheduled for retry. This class attribute was added in
            vSphere API 7.0.2.1.

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
            'com.vmware.esx.settings.clusters.software.apply_status.status',
            Status))

    ApplyStatus._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.apply_status', {
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
                     host_status=None,
                     successful_hosts=None,
                     failed_hosts=None,
                     skipped_hosts=None,
                     notifications=None,
                    ):
            """
            :type  status: :class:`Software.StageStatus` or ``None``
            :param status: Specifies the aggregated status of the :func:`Software.stage`
                method. This attribute was added in vSphere API 8.0.0.1.
                None if the :func:`Software.stage` method is in progress.
            :type  commit: :class:`str`
            :param commit: The identifier of the commit used to fetch the desired software
                document to be staged to all hosts within the cluster. This
                attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information of the hosts in this cluster to which the desired
                software document specified by the
                :attr:`Software.StageResult.commit` should be staged to. This
                attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  host_status: :class:`dict` of :class:`str` and :class:`Software.StageStatus`
            :param host_status: Status of the hosts in this cluster to which the desired software
                document specified by the :attr:`Software.StageResult.commit` was
                staged to. Hosts on which the :func:`Software.stage` method was
                successful are specified by
                :attr:`Software.StageResult.successful_hosts`. Hosts on which the
                stage method failed are specified by
                :attr:`Software.StageResult.failed_hosts`. Hosts which were skipped
                by the :func:`Software.stage` method are specified by
                :attr:`Software.StageResult.skipped_hosts`. This attribute was
                added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  successful_hosts: :class:`set` of :class:`str`
            :param successful_hosts: Hosts in this cluster to which the desired software document
                specified by the :attr:`Software.StageResult.commit` has been
                successfully staged to. This attribute was added in vSphere API
                8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  failed_hosts: :class:`set` of :class:`str`
            :param failed_hosts: Hosts in this cluster to which the desired software document
                specified by the :attr:`Software.StageResult.commit` failed to be
                staged to. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  skipped_hosts: :class:`set` of :class:`str`
            :param skipped_hosts: Hosts in this cluster that were skipped by the
                :func:`Software.stage` method. For example hosts which are
                compliant, or are previously staged shall be skipped. This
                attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
            :param notifications: Notifications providing additional information for
                :func:`Software.stage` method. These notifications are mutually
                exclusive with the notifications in ``Software.StageStatus``. This
                attribute was added in vSphere API 8.0.0.1.
            """
            self.status = status
            self.commit = commit
            self.host_info = host_info
            self.host_status = host_status
            self.successful_hosts = successful_hosts
            self.failed_hosts = failed_hosts
            self.skipped_hosts = skipped_hosts
            self.notifications = notifications
            VapiStruct.__init__(self)


    StageResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.stage_result', {
            'status': type.OptionalType(type.ReferenceType(__name__, 'Software.StageStatus')),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
            'host_status': type.MapType(type.IdType(), type.ReferenceType(__name__, 'Software.StageStatus')),
            'successful_hosts': type.SetType(type.IdType()),
            'failed_hosts': type.SetType(type.IdType()),
            'skipped_hosts': type.SetType(type.IdType()),
            'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        StageResult,
        False,
        None))


    class ApplyResult(VapiStruct):
        """
        The ``Software.ApplyResult`` class contains attributes that describe the
        result of an :func:`Software.apply` method.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     status=None,
                     commit=None,
                     host_info=None,
                     host_status=None,
                     successful_hosts=None,
                     failed_hosts=None,
                     skipped_hosts=None,
                     notifications=None,
                    ):
            """
            :type  status: :class:`Software.ApplyStatus` or ``None``
            :param status: Specifies the aggregated status of the :func:`Software.apply`
                method.
                None if the :func:`Software.apply` method is in progress.
            :type  commit: :class:`str`
            :param commit: The identifier of the commit used to fetch the desired software
                document to be applied to all hosts within the cluster.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information of the hosts in this cluster to which the desired
                software document specified by the
                :attr:`Software.ApplyResult.commit` should be applied to.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  host_status: :class:`dict` of :class:`str` and :class:`Software.ApplyStatus`
            :param host_status: Status of the hosts in this cluster to which the desired software
                document specified by the :attr:`Software.ApplyResult.commit` was
                applied to. Hosts on which the :func:`Software.apply` method was
                successful are specified by
                :attr:`Software.ApplyResult.successful_hosts`. Hosts on which the
                apply method failed are specified by
                :attr:`Software.ApplyResult.failed_hosts`. Hosts which were skipped
                by the :func:`Software.apply` method are specified by
                :attr:`Software.ApplyResult.skipped_hosts`.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  successful_hosts: :class:`set` of :class:`str`
            :param successful_hosts: Hosts in this cluster to which the desired software document
                specified by the :attr:`Software.ApplyResult.commit` has been
                successfully applied to.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  failed_hosts: :class:`set` of :class:`str`
            :param failed_hosts: Hosts in this cluster to which the desired software document
                specified by the :attr:`Software.ApplyResult.commit` failed to be
                applied to.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  skipped_hosts: :class:`set` of :class:`str`
            :param skipped_hosts: Hosts in this cluster that were skipped by the
                :func:`Software.apply` method.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
            :param notifications: Notifications providing additional information for
                :func:`Software.apply` method. These notifications are mutually
                exclusive with the notifications in ``Software.ApplyStatus``. This
                attribute was added in vSphere API 7.0.2.1.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.status = status
            self.commit = commit
            self.host_info = host_info
            self.host_status = host_status
            self.successful_hosts = successful_hosts
            self.failed_hosts = failed_hosts
            self.skipped_hosts = skipped_hosts
            self.notifications = notifications
            VapiStruct.__init__(self)


    ApplyResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.apply_result', {
            'status': type.OptionalType(type.ReferenceType(__name__, 'Software.ApplyStatus')),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
            'host_status': type.MapType(type.IdType(), type.ReferenceType(__name__, 'Software.ApplyStatus')),
            'successful_hosts': type.SetType(type.IdType()),
            'failed_hosts': type.SetType(type.IdType()),
            'skipped_hosts': type.SetType(type.IdType()),
            'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        ApplyResult,
        False,
        None))


    class CheckSpec(VapiStruct):
        """
        The ``Software.CheckSpec`` class contains attributes that describe the
        specification to be used for running checks on the cluster before the
        :func:`Software.apply` method.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     commit=None,
                     hosts=None,
                    ):
            """
            :type  commit: :class:`str` or ``None``
            :param commit: The minimum commit identifier of the desired software document to
                be used during the check method.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
                if None or empty the check opertion will use the latest commit to
                fetch the desired state document.
            :type  hosts: :class:`set` of :class:`str` or ``None``
            :param hosts: The specific hosts for which checks need to be performed
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
                if None or empty checks are run for all hosts within the cluster.
            """
            self.commit = commit
            self.hosts = hosts
            VapiStruct.__init__(self)


    CheckSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.check_spec', {
            'commit': type.OptionalType(type.IdType()),
            'hosts': type.OptionalType(type.SetType(type.IdType())),
        },
        CheckSpec,
        False,
        None))


    class CheckInfo(VapiStruct):
        """
        The ``Software.CheckInfo`` class contains attributes that describe a
        particular check.

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
            :param check: The check identifier.
            :type  name: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param name: The check name.
            :type  description: :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param description: Human-readable check description.
            :type  originator: :class:`str` or ``None``
            :param originator: The service that performed the check. This attribute was added in
                vSphere API 7.0.2.0.
                Only :class:`set` if there is an originator available for this
                check.
            """
            self.check = check
            self.name = name
            self.description = description
            self.originator = originator
            VapiStruct.__init__(self)


    CheckInfo._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.check_info', {
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
                7.0.2.0.
            :type  resolution: :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param resolution: Possible resolution for the issue. This should contain actionable
                information that the user can use to resolve the issue. This
                attribute was added in vSphere API 7.0.2.0.
                Can be left None if no meaningful resolution exists.
            """
            self.description = description
            self.resolution = resolution
            VapiStruct.__init__(self)


    CheckIssue._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.check_issue', {
            'description': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
            'resolution': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        CheckIssue,
        False,
        None))


    class CheckStatus(VapiStruct):
        """
        The ``Software.CheckStatus`` class contains attributes that describe a
        check result.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     check=None,
                     status=None,
                     issues=None,
                     check_issues=None,
                    ):
            """
            :type  check: :class:`Software.CheckInfo`
            :param check: Information about this check.
            :type  status: :class:`Software.Status`
            :param status: The status of this check.
            :type  issues: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
            :param issues: The issues encountered while running this check.
            :type  check_issues: :class:`list` of :class:`Software.CheckIssue` or ``None``
            :param check_issues: List of :class:`Software.CheckIssue`s that the check reported. This
                attribute was added in vSphere API 7.0.2.0.
                If not :class:`set`, the service is still using the {#member
                issues}.
            """
            self.check = check
            self.status = status
            self.issues = issues
            self.check_issues = check_issues
            VapiStruct.__init__(self)


    CheckStatus._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.check_status', {
            'check': type.ReferenceType(__name__, 'Software.CheckInfo'),
            'status': type.ReferenceType(__name__, 'Software.Status'),
            'issues': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
            'check_issues': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Software.CheckIssue'))),
        },
        CheckStatus,
        False,
        None))


    class EntityCheckResult(VapiStruct):
        """
        The ``Software.EntityCheckResult`` class contains attributes that describe
        aggregated status of all checks performed on a specific entity.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'type',
                {
                    'CLUSTER' : [('cluster', True)],
                    'HOST' : [('host', True)],
                }
            ),
        ]



        def __init__(self,
                     type=None,
                     cluster=None,
                     host=None,
                     status=None,
                     check_statuses=None,
                    ):
            """
            :type  type: :class:`Software.EntityCheckResult.EntityType`
            :param type: The entity type for which these checks are being run.
            :type  cluster: :class:`str`
            :param cluster: If the entity type is CLUSTER then the cluster identifier for which
                the checks have been run.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
                This attribute is optional and it is only relevant when the value
                of ``type`` is
                :attr:`Software.EntityCheckResult.EntityType.CLUSTER`.
            :type  host: :class:`str`
            :param host: If the entity type is HOST then the host identifier for which the
                checks have been run.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``HostSystem``.
                This attribute is optional and it is only relevant when the value
                of ``type`` is :attr:`Software.EntityCheckResult.EntityType.HOST`.
            :type  status: :class:`Software.Status`
            :param status: Aggregated status from all checks performed on this entity.
            :type  check_statuses: :class:`list` of :class:`Software.CheckStatus`
            :param check_statuses: List of ``Software.CheckStatus`` for all checks performed.
            """
            self.type = type
            self.cluster = cluster
            self.host = host
            self.status = status
            self.check_statuses = check_statuses
            VapiStruct.__init__(self)


        class EntityType(Enum):
            """
            The ``Software.EntityCheckResult.EntityType`` class contains the entitites
            on which checks can be performed.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            CLUSTER = None
            """
            Entity type Cluster

            """
            HOST = None
            """
            Entity type Host

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`EntityType` instance.
                """
                Enum.__init__(string)

        EntityType._set_values({
            'CLUSTER': EntityType('CLUSTER'),
            'HOST': EntityType('HOST'),
        })
        EntityType._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.clusters.software.entity_check_result.entity_type',
            EntityType))

    EntityCheckResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.entity_check_result', {
            'type': type.ReferenceType(__name__, 'Software.EntityCheckResult.EntityType'),
            'cluster': type.OptionalType(type.IdType()),
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
        aggregated status of all checks performed.

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
                     entity_results=None,
                    ):
            """
            :type  status: :class:`Software.Status`
            :param status: Aggregated status from all checks performed.
            :type  start_time: :class:`datetime.datetime`
            :param start_time: Time when the operation started.
            :type  end_time: :class:`datetime.datetime`
            :param end_time: Time when the operation completed.
            :type  commit: :class:`str`
            :param commit: The identifier of the commit on which checks have been run.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.commit``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.esx.settings.commit``.
            :type  host_info: :class:`dict` of :class:`str` and :class:`com.vmware.esx.settings_client.HostInfo`
            :param host_info: Information about the hosts in this cluster for which checks have
                been requested to be run.
                When clients pass a value of this class as a parameter, the key in
                the attribute :class:`dict` must be an identifier for the resource
                type: ``HostSystem``. When methods return a value of this class as
                a return value, the key in the attribute :class:`dict` will be an
                identifier for the resource type: ``HostSystem``.
            :type  entity_results: :class:`list` of :class:`Software.EntityCheckResult`
            :param entity_results: List of ``Software.EntityCheckResult`` for all entities for which
                checks have been run.
            """
            self.status = status
            self.start_time = start_time
            self.end_time = end_time
            self.commit = commit
            self.host_info = host_info
            self.entity_results = entity_results
            VapiStruct.__init__(self)


    CheckResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.clusters.software.check_result', {
            'status': type.ReferenceType(__name__, 'Software.Status'),
            'start_time': type.DateTimeType(),
            'end_time': type.DateTimeType(),
            'commit': type.IdType(resource_types='com.vmware.esx.settings.commit'),
            'host_info': type.MapType(type.IdType(), type.ReferenceType('com.vmware.esx.settings_client', 'HostInfo')),
            'entity_results': type.ListType(type.ReferenceType(__name__, 'Software.EntityCheckResult')),
        },
        CheckResult,
        False,
        None))



    def get(self,
            cluster,
            ):
        """
        Returns the complete desired software specification. In case of
        Homogeneous Cluster, the specification will contain Default Image In
        case of Heterogeneous Cluster, the specification will contain Default
        Image + Alternative Images

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`com.vmware.esx.settings_client.SoftwareInfo`
        :return: Cluster software specification.
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
              ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })


    def scan_task(self,
             cluster,
             ):
        """
        Scans all the hosts in the cluster against the cluster's desired state.
        The result of this operation can be queried by calling the
        cis/tasks/{task-id} where the task-id is the response of this
        operation.

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
            If there is no cluster associated with ``cluster`` in the system or
            if desired software document is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('scan$task',
                                {
                                'cluster': cluster,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType('com.vmware.esx.settings_client', 'ClusterCompliance'))
        return task_instance

    def export(self,
               cluster,
               spec,
               ):
        """
        Exports the desired software specification document and/or image. This
        API will not export the solution section of the desired software
        specification.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Software.ExportSpec`
        :param spec: 
        :rtype: :class:`dict` of :class:`Software.ExportType` and :class:`str`
        :return: A map from export type to URL of the exported data for that type.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is am unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system or
            if desired software document is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
            * The resource ``ClusterComputeResource`` referenced by the
              parameter ``cluster`` requires
              ``VcIntegrity.lifecycleSoftwareSpecification.Read``.
        """
        return self._invoke('export',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })


    def stage_task(self,
              cluster,
              spec,
              ):
        """
        Stages the desired software document associated with the given cluster
        to hosts within the cluster. If ``commit`` attribute is :class:`set`,
        it implies the minimum commit that the :func:`Software.stage` method
        should use, however if subsequent commits have been made to the desired
        state document the stage method will use the most recent desired state
        document. The result of this operation can be queried by calling the
        cis/tasks/{task-id} where the task-id is the response of this
        operation. This method was added in vSphere API 8.0.0.1.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Software.StageSpec`
        :param spec: stage specification.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the ``commit`` attribute of ``spec`` specifies an invalid
            commit, or the ``hosts`` attribute of ``spec`` specifies an invalid
            host or a host not part of the cluster, or the ``cluster`` is not
            managed with a single software specification.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If there is another operation in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system or
            if desired software document is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.TimedOut` 
            If the operation times out.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('stage$task',
                                {
                                'cluster': cluster,
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Software.StageResult'))
        return task_instance


    def apply_task(self,
              cluster,
              spec,
              ):
        """
        Applies the desired software document associated with the given cluster
        to hosts within the cluster. If ``commit`` attribute is :class:`set`,
        it implies the minimum commit that the :func:`Software.apply` method
        should use, however if subsequent commits have been made to the desired
        state document the apply method will use the most recent desired state
        document. The result of this operation can be queried by calling the
        cis/tasks/{task-id} where the task-id is the response of this
        operation.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Software.ApplySpec`
        :param spec: Apply specification.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyInDesiredState` 
            If the cluster is already at specified commit as described in the
            apply specification.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error or if the EULA has not been
            accepted. The accompanying error message will give more details
            about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the ``commit`` attribute of ``spec`` specifies an invalid
            commit, or the ``hosts`` attribute of ``spec`` specifies an invalid
            host or a host not part of the cluster, or the ``cluster`` is not
            managed with a single software specification.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If there is another operation in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system or
            if desired software document is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.TimedOut` 
            If the operation times out.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('apply$task',
                                {
                                'cluster': cluster,
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Software.ApplyResult'))
        return task_instance


    def check_task(self,
              cluster,
              spec,
              ):
        """
        Runs checks on the cluster before applying the desired software
        document across all hosts in the cluster. Checks if all hosts in the
        cluster are in a good state to be updated with the desired software
        document. If ``commit`` attribute is :class:`set` it implies the
        minimum commit that the check method should use, however if subsequent
        commits have been made to the desired state document the check method
        will use the most recent desired state document. The result of this
        operation can be queried by calling the cis/tasks/{task-id} where the
        task-id is the response of this operation.

        :type  cluster: :class:`str`
        :param cluster: Identifier of the cluster.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`Software.CheckSpec`
        :param spec: Check specification.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the ``commit`` attribute of ``spec`` specifies an invalid
            commit, or the ``hosts`` attribute of ``spec`` specifies an invalid
            host or a host not part of the cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If there is another operation in progress or if the ``commit``
            attribute of ``spec`` specifies a commit that has already been
            applied.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no cluster associated with ``cluster`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.TimedOut` 
            If the operation times out.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('check$task',
                                {
                                'cluster': cluster,
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Software.CheckResult'))
        return task_instance
class _ConfigurationStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'commit': type.OptionalType(type.IdType()),
            'doc_structure': type.OptionalType(type.ReferenceType('com.vmware.esx.settings.clusters.configuration_client', 'DocumentStructure')),
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
            url_template='/esx/settings/clusters/{cluster}/configuration',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
                'commit': 'commit',
                'doc_structure': 'doc_structure',
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
            'spec': type.ReferenceType(__name__, 'Configuration.ApplySpec'),
        })
        apply_error_dict = {
            'com.vmware.vapi.std.errors.already_in_desired_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyInDesiredState'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.timed_out':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'TimedOut'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        apply_input_value_validator_list = [
        ]
        apply_output_validator_list = [
        ]
        apply_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/configuration',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
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

        # properties for check_compliance operation
        check_compliance_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        check_compliance_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
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
            url_template='/esx/settings/clusters/{cluster}/configuration',
            path_variables={
                'cluster': 'cluster',
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

        # properties for validate operation
        validate_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        validate_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.timed_out':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'TimedOut'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        validate_input_value_validator_list = [
        ]
        validate_output_validator_list = [
        ]
        validate_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/configuration',
            path_variables={
                'cluster': 'cluster',
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

        # properties for precheck operation
        precheck_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        precheck_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
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
            url_template='/esx/settings/clusters/{cluster}/configuration',
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

        # properties for import_config operation
        import_config_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.ReferenceType(__name__, 'Configuration.ImportSpec'),
        })
        import_config_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        import_config_input_value_validator_list = [
        ]
        import_config_output_validator_list = [
        ]
        import_config_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/configuration',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'importConfig',
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
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.timed_out':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'TimedOut'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        export_config_input_value_validator_list = [
        ]
        export_config_output_validator_list = [
        ]
        export_config_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/configuration',
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

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Configuration.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'apply$task': {
                'input_type': apply_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': apply_error_dict,
                'input_value_validator_list': apply_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'check_compliance$task': {
                'input_type': check_compliance_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': check_compliance_error_dict,
                'input_value_validator_list': check_compliance_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'validate$task': {
                'input_type': validate_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': validate_error_dict,
                'input_value_validator_list': validate_input_value_validator_list,
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
            'import_config$task': {
                'input_type': import_config_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': import_config_error_dict,
                'input_value_validator_list': import_config_input_value_validator_list,
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
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'apply': apply_rest_metadata,
            'check_compliance': check_compliance_rest_metadata,
            'validate': validate_rest_metadata,
            'precheck': precheck_rest_metadata,
            'import_config': import_config_rest_metadata,
            'export_config': export_config_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.clusters.configuration',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _DepotOverridesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/depot-overrides',
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

        # properties for add operation
        add_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        add_input_value_validator_list = [
        ]
        add_output_validator_list = [
        ]
        add_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/depot-overrides',
            request_body_parameter='depot',
            path_variables={
                'cluster': 'cluster',
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
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        remove_input_value_validator_list = [
        ]
        remove_output_validator_list = [
        ]
        remove_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/depot-overrides',
            request_body_parameter='depot',
            path_variables={
                'cluster': 'cluster',
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
            self, iface_name='com.vmware.esx.settings.clusters.depot_overrides',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _InstalledImagesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for extract operation
        extract_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        extract_input_value_validator_list = [
        ]
        extract_output_validator_list = [
        ]
        extract_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/installed-images',
            path_variables={
                'cluster': 'cluster',
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
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/clusters/{cluster}/installed-images',
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
            'extract$task': {
                'input_type': extract_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': extract_error_dict,
                'input_value_validator_list': extract_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'InstalledImages.InstalledImageInfo'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'extract': extract_rest_metadata,
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.clusters.installed_images',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _SoftwareStub(ApiInterfaceStub):
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
            url_template='/esx/settings/clusters/{cluster}/software',
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

        # properties for scan operation
        scan_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        scan_input_value_validator_list = [
        ]
        scan_output_validator_list = [
        ]
        scan_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/software',
            path_variables={
                'cluster': 'cluster',
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

        # properties for export operation
        export_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        export_input_value_validator_list = [
        ]
        export_output_validator_list = [
        ]
        export_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/software',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
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
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        stage_input_value_validator_list = [
        ]
        stage_output_validator_list = [
        ]
        stage_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/software',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
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
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        apply_input_value_validator_list = [
        ]
        apply_output_validator_list = [
        ]
        apply_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/software',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
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
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
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

        }
        check_input_value_validator_list = [
        ]
        check_output_validator_list = [
        ]
        check_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/clusters/{cluster}/software',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
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
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType('com.vmware.esx.settings_client', 'SoftwareInfo'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'scan$task': {
                'input_type': scan_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': scan_error_dict,
                'input_value_validator_list': scan_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
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
            'get': get_rest_metadata,
            'scan': scan_rest_metadata,
            'export': export_rest_metadata,
            'stage': stage_rest_metadata,
            'apply': apply_rest_metadata,
            'check': check_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.clusters.software',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Configuration': Configuration,
        'DepotOverrides': DepotOverrides,
        'InstalledImages': InstalledImages,
        'Software': Software,
        'configuration': 'com.vmware.esx.settings.clusters.configuration_client.StubFactory',
        'enablement': 'com.vmware.esx.settings.clusters.enablement_client.StubFactory',
        'policies': 'com.vmware.esx.settings.clusters.policies_client.StubFactory',
        'software': 'com.vmware.esx.settings.clusters.software_client.StubFactory',
    }

