# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespaces.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.namespaces_client`` module provides classes for
managing namespaces related methods.

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


class ResourceQuotaOptionsV1(VapiStruct):
    """
    The ``ResourceQuotaOptionsV1`` class represents the resource quota limits
    which can be applied on the namespace. Refer to `
    <https://kubernetes.io/docs/concepts/policy/resource-quotas>`_ for
    information related to the properties of this object and what they map to.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 memory_limit=None,
                 memory_limit_default=None,
                 memory_request_default=None,
                 cpu_limit=None,
                 cpu_limit_default=None,
                 cpu_request_default=None,
                 storage_request_limit=None,
                 pod_count=None,
                 service_count=None,
                 deployment_count=None,
                 daemon_set_count=None,
                 replica_set_count=None,
                 replication_controller_count=None,
                 stateful_set_count=None,
                 config_map_count=None,
                 secret_count=None,
                 persistent_volume_claim_count=None,
                 job_count=None,
                ):
        """
        :type  memory_limit: :class:`long` or ``None``
        :param memory_limit: This is equivalent to 'limits.memory' option which is the maximum
            memory limit (in mebibytes) across all pods which exist in a
            non-terminal state in the namespace. This value translates to the
            memory limit on the ResourcePool in vCenter Server created for the
            namespace.
            If None, no memory limits are set on the ResourcePool for the
            namespace.
        :type  memory_limit_default: :class:`long` or ``None``
        :param memory_limit_default: This represents the default memory limit (in mebibytes) for
            containers in the pod. This translates to default memory limit in a
            LimitRange object. Refer ` for information about LimitRange.
            <https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/>`_
            If None, no default memory limits are set on containers in the pod.
        :type  memory_request_default: :class:`long` or ``None``
        :param memory_request_default: This represents the default memory request (in mebibytes) for
            containers in the pod. This translates to default memory request in
            a LimitRange object. Refer ` for information about LimitRange.
            <https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/>`_
            If None, no default memory requests are set on containers in the
            pod.
        :type  cpu_limit: :class:`long` or ``None``
        :param cpu_limit: This is equivalent to 'limits.cpu' option which is the maximum CPU
            limit (in MHz) across all pods which exist in a non-terminal state
            in the namespace. If specified, this limit should be at least 10
            MHz. This value translates to the CPU limit on the ResourcePool in
            vCenter Server created for the namespace.
            If None, no CPU limits are set on the ResourcePool for the
            namespace.
        :type  cpu_limit_default: :class:`long` or ``None``
        :param cpu_limit_default: This represents the default cpu limit (in MHz) for containers in
            the pod.
            If None, no default CPU limits are set on containers in the pod.
            Refer ` for information about LimitRange. If specified, this limit
            should be at least 10 MHz.
            <https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/>`_
        :type  cpu_request_default: :class:`long` or ``None``
        :param cpu_request_default: This represents the default CPU request (in MHz) for containers in
            the pod.
            If None, no default CPU requests are set on containers in the pod.
            Refer ` for information about LimitRange. If specified, this field
            should be at least 10 MHz.
            <https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/cpu-default-namespace/>`_
        :type  storage_request_limit: :class:`long` or ``None``
        :param storage_request_limit: This represents 'requests.storage' option which is the maximum
            storage request (in mebibytes) across all persistent volume claims
            from pods which exist in a non-terminal state in the namespace.
            If None, no storage request limits are set on the namespace.
        :type  pod_count: :class:`long` or ``None``
        :param pod_count: This represents 'pods' option which is the maximum number of pods
            which exist in a non-terminal state in the namespace.
            If None, no pod limits are set on the namespace.
        :type  service_count: :class:`long` or ``None``
        :param service_count: This represents 'count/services' option which is the maximum number
            of services in the namespace.
            If None, no service limits are set on the namespace.
        :type  deployment_count: :class:`long` or ``None``
        :param deployment_count: This represents 'count/deployments.apps' option which is the
            maximum number of deployments in the namespace.
            If None, no deployment limits are set on the namespace.
        :type  daemon_set_count: :class:`long` or ``None``
        :param daemon_set_count: This represents 'count/daemonsets.apps' option which is the maximum
            number of DaemonSets in the namespace.
            If None, no daemonset limits are set on the namespace.
        :type  replica_set_count: :class:`long` or ``None``
        :param replica_set_count: This represents 'count/replicasets.apps' option which is the
            maximum number of ReplicaSets in the namespace.
            If None, no replicaset limits are set on the namespace.
        :type  replication_controller_count: :class:`long` or ``None``
        :param replication_controller_count: This represents 'count/replicationcontrollers' option which is the
            maximum number of ReplicationControllers in the namespace.
            If None, no replicationcontroller limits are set on the namespace.
        :type  stateful_set_count: :class:`long` or ``None``
        :param stateful_set_count: This represents 'count/statefulsets.apps' option which is the
            maximum number of StatefulSets in the namespace.
            If None, no statefulset limits are set on the namespace.
        :type  config_map_count: :class:`long` or ``None``
        :param config_map_count: This represents 'count/configmaps' option which is the maximum
            number of ConfigMaps in the namespace.
            If None, no configmap limits are set on the namespace.
        :type  secret_count: :class:`long` or ``None``
        :param secret_count: This represents 'count/secrets' option which is the maximum number
            of secrets in the namespace.
            If None, no secret limits are set on the namespace.
        :type  persistent_volume_claim_count: :class:`long` or ``None``
        :param persistent_volume_claim_count: This represents 'count/persistentvolumeclaims' option which is the
            maximum number of PersistentVolumeClaims in the namespace.
            If None, no persistentvolumeclaim limits are set on the namespace.
        :type  job_count: :class:`long` or ``None``
        :param job_count: This represents 'count/jobs.batch' option which is the maximum
            number jobs in the namespace.
            If None, no job limits are set on the namespace.
        """
        self.memory_limit = memory_limit
        self.memory_limit_default = memory_limit_default
        self.memory_request_default = memory_request_default
        self.cpu_limit = cpu_limit
        self.cpu_limit_default = cpu_limit_default
        self.cpu_request_default = cpu_request_default
        self.storage_request_limit = storage_request_limit
        self.pod_count = pod_count
        self.service_count = service_count
        self.deployment_count = deployment_count
        self.daemon_set_count = daemon_set_count
        self.replica_set_count = replica_set_count
        self.replication_controller_count = replication_controller_count
        self.stateful_set_count = stateful_set_count
        self.config_map_count = config_map_count
        self.secret_count = secret_count
        self.persistent_volume_claim_count = persistent_volume_claim_count
        self.job_count = job_count
        VapiStruct.__init__(self)


ResourceQuotaOptionsV1._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespaces.resource_quota_options_v1', {
        'memory_limit': type.OptionalType(type.IntegerType()),
        'memory_limit_default': type.OptionalType(type.IntegerType()),
        'memory_request_default': type.OptionalType(type.IntegerType()),
        'cpu_limit': type.OptionalType(type.IntegerType()),
        'cpu_limit_default': type.OptionalType(type.IntegerType()),
        'cpu_request_default': type.OptionalType(type.IntegerType()),
        'storage_request_limit': type.OptionalType(type.IntegerType()),
        'pod_count': type.OptionalType(type.IntegerType()),
        'service_count': type.OptionalType(type.IntegerType()),
        'deployment_count': type.OptionalType(type.IntegerType()),
        'daemon_set_count': type.OptionalType(type.IntegerType()),
        'replica_set_count': type.OptionalType(type.IntegerType()),
        'replication_controller_count': type.OptionalType(type.IntegerType()),
        'stateful_set_count': type.OptionalType(type.IntegerType()),
        'config_map_count': type.OptionalType(type.IntegerType()),
        'secret_count': type.OptionalType(type.IntegerType()),
        'persistent_volume_claim_count': type.OptionalType(type.IntegerType()),
        'job_count': type.OptionalType(type.IntegerType()),
    },
    ResourceQuotaOptionsV1,
    False,
    None))



class ResourceQuotaOptionsV1Update(VapiStruct):
    """
    The ``ResourceQuotaOptionsV1Update`` class represents the changes to
    resource quota limits which are set on the namespace. Refer to ` <\a>
    Kubernetes Resource Quota
    <https://kubernetes.io/docs/concepts/policy/resource-quotas>`_ for
    information related to the properties of this object and what they map to.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 memory_limit=None,
                 memory_limit_unset=None,
                 memory_limit_default=None,
                 memory_limit_default_unset=None,
                 memory_request_default=None,
                 memory_request_default_unset=None,
                 cpu_limit=None,
                 cpu_limit_unset=None,
                 cpu_limit_default=None,
                 cpu_limit_default_unset=None,
                 cpu_request_default=None,
                 cpu_request_default_unset=None,
                 storage_request_limit=None,
                 storage_request_limit_unset=None,
                 pod_count=None,
                 pod_count_unset=None,
                 service_count=None,
                 service_count_unset=None,
                 deployment_count=None,
                 deployment_count_unset=None,
                 daemon_set_count=None,
                 daemon_set_count_unset=None,
                 replica_set_count=None,
                 replica_set_count_unset=None,
                 replication_controller_count=None,
                 replication_controller_count_unset=None,
                 stateful_set_count=None,
                 stateful_set_count_unset=None,
                 config_map_count=None,
                 config_map_count_unset=None,
                 secret_count=None,
                 secret_count_unset=None,
                 persistent_volume_claim_count=None,
                 persistent_volume_claim_count_unset=None,
                 job_count=None,
                 job_count_unset=None,
                ):
        """
        :type  memory_limit: :class:`long` or ``None``
        :param memory_limit: This represents the new value for 'limits.memory' option which is
            equivalent to the maximum memory limit (in mebibytes) across all
            pods in the namespace. This field is ignored if
            :attr:`ResourceQuotaOptionsV1Update.memory_limit_unset` is set to
            ``true``.
            If None, the existing memory limit on the ResourcePool will be
            unchanged if
            :attr:`ResourceQuotaOptionsV1Update.memory_limit_unset` is None or
            set to ``false``.
        :type  memory_limit_unset: :class:`bool` or ``None``
        :param memory_limit_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.memory_limit`. If this field is
            set to ``true``, the existing memory limit on the ResourcePool is
            removed. If this field is set to ``false``, the existing memory
            limit will be changed to the value specified in
            :attr:`ResourceQuotaOptionsV1Update.memory_limit`, if any.
            If None, the existing memory limit will be changed to the value
            specified in :attr:`ResourceQuotaOptionsV1Update.memory_limit`, if
            any.
        :type  memory_limit_default: :class:`long` or ``None``
        :param memory_limit_default: This represents the new value for the default memory limit (in
            mebibytes) for containers in the pod. This field is ignored if
            :attr:`ResourceQuotaOptionsV1Update.memory_limit_default_unset` is
            set to ``true``.
            If None, the existing memory limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.memory_limit_default_unset` is
            None or set to ``false``.
        :type  memory_limit_default_unset: :class:`bool` or ``None``
        :param memory_limit_default_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.memory_limit_default`. If this
            field is set to ``true``, the existing default memory limit on
            containers in the pod is removed. If this field is set to
            ``false``, the existing default memory limit will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.memory_limit_default`, if any.
            If None, the existing default memory limit will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.memory_limit_default`, if any.
        :type  memory_request_default: :class:`long` or ``None``
        :param memory_request_default: This represents the new value for the default memory request (in
            mebibytes) for containers in the pod. This field is ignored if
            :attr:`ResourceQuotaOptionsV1Update.memory_request_default_unset`
            is set to ``true``.
            If None, the existing memory request will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.memory_request_default_unset`
            is None or set to ``false``.
        :type  memory_request_default_unset: :class:`bool` or ``None``
        :param memory_request_default_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.memory_request_default`. If
            this field is set to ``true``, the existing default memory request
            on containers in the pod will be removed. If this field is set to
            ``false``, the existing default memory request will be changed to
            the value specified in
            :attr:`ResourceQuotaOptionsV1Update.memory_request_default`, if
            any.
            If None, the existing default memory request will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.memory_request_default`, if
            any.
        :type  cpu_limit: :class:`long` or ``None``
        :param cpu_limit: This represents the new value for 'limits.cpu' option which is
            equivalent to the maximum CPU limit (in MHz) across all pods in the
            namespace. This field is ignored if
            :attr:`ResourceQuotaOptionsV1Update.cpu_limit_unset` is set to
            ``true``. If specified, this limit should be at least 10 MHz.
            If None, the existing CPU limit on the ResourcePool will be
            unchanged if :attr:`ResourceQuotaOptionsV1Update.cpu_limit_unset`
            is None or set to ``false``.
        :type  cpu_limit_unset: :class:`bool` or ``None``
        :param cpu_limit_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.cpu_limit`. If this field is
            set to ``true``, the existing CPU limit on the ResourcePool is
            removed. If this field is set to ``false``, the existing CPU limit
            will be changed to the value specified in
            :attr:`ResourceQuotaOptionsV1Update.cpu_limit`, if any.
            If None, the existing CPU limit will be changed to the value
            specified in :attr:`ResourceQuotaOptionsV1Update.memory_limit`, if
            any.
        :type  cpu_limit_default: :class:`long` or ``None``
        :param cpu_limit_default: This represents the new value for the default CPU limit (in Mhz)
            for containers in the pod. This field is ignored if
            :attr:`ResourceQuotaOptionsV1Update.cpu_limit_default_unset` is set
            to ``true``. If specified, this limit should be at least 10 MHz.
            If None, the existing default CPU limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.cpu_limit_default_unset` is
            None or set to ``false``.
        :type  cpu_limit_default_unset: :class:`bool` or ``None``
        :param cpu_limit_default_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.cpu_limit_default`. If this
            field is set to ``true``, the existing default CPU limit on
            containers in the pod is removed. If this field is set to
            ``false``, the existing default CPU limit will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.cpu_limit_default`, if any.
            If None, the existing default CPU limit will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.cpu_limit_default`, if any.
        :type  cpu_request_default: :class:`long` or ``None``
        :param cpu_request_default: This represents the new value for the default CPU request (in Mhz)
            for containers in the pod. This field is ignored if
            :attr:`ResourceQuotaOptionsV1Update.cpu_request_default_unset` is
            set to ``true``. If specified, this field should be at least 10
            MHz.
            If None, the existing default CPU request will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.cpu_request_default_unset` is
            None or set to ``false``.
        :type  cpu_request_default_unset: :class:`bool` or ``None``
        :param cpu_request_default_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.cpu_request_default`. If this
            field is set to ``true``, the existing default CPU request on
            containers in the pod is removed. If this field is set to
            ``false``, the existing default CPU request will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.cpu_request_default`, if any.
            If None, the existing default CPU request will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.cpu_request_default`, if any.
        :type  storage_request_limit: :class:`long` or ``None``
        :param storage_request_limit: This represents the new value for 'requests.storage' which is the
            limit on storage requests (in mebibytes) across all persistent
            volume claims from pods in the namespace. This field is ignored if
            if :attr:`ResourceQuotaOptionsV1Update.storage_request_limit_unset`
            is set to ``true``.
            If None, the existing storage request limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.storage_request_limit_unset` is
            None or set to ``false``. the namespace.
        :type  storage_request_limit_unset: :class:`bool` or ``None``
        :param storage_request_limit_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.storage_request_limit`. If this
            field is set to ``true``, the existing storage request limit will
            be reset. If this field is set to ``false``, the existing storage
            request limit will be changed to the value specified in
            :attr:`ResourceQuotaOptionsV1Update.storage_request_limit`, if any.
            If None, the existing storage request limit will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.storage_request_limit`, if any.
        :type  pod_count: :class:`long` or ``None``
        :param pod_count: This represents the new value for 'podCount' option which is the
            maximum number of pods in the namespace. This field is ignored if
            :attr:`ResourceQuotaOptionsV1Update.pod_count_unset` is set to
            ``true``.
            If None, the existing 'podCount' limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.pod_count_unset` is None or set
            to ``false``.
        :type  pod_count_unset: :class:`bool` or ``None``
        :param pod_count_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.pod_count`. If this field is
            set to ``true``, the existing 'podCount' limit on the namespace
            will be reset. If this field is set to ``false``, the existing CPU
            limit will be changed to the value specified in
            :attr:`ResourceQuotaOptionsV1Update.pod_count`, if any.
            If None, the existing 'podCount' limit will be changed to the value
            specified in :attr:`ResourceQuotaOptionsV1Update.pod_count`, if
            any.
        :type  service_count: :class:`long` or ``None``
        :param service_count: This represents the new value for 'serviceCount' option which is
            the maximum number of services in the namespace. This field is
            ignored if :attr:`ResourceQuotaOptionsV1Update.service_count_unset`
            is set to ``true``.
            If None, the existing 'serviceCount' limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.service_count_unset` is None or
            set to ``false``.
        :type  service_count_unset: :class:`bool` or ``None``
        :param service_count_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.service_count`. If this field
            is set to ``true``, the existing 'serviceCount' limit on the
            namespace will be reset. If this field is set to ``false``, the
            existing service count limit will be changed to the value specified
            in :attr:`ResourceQuotaOptionsV1Update.service_count`, if any.
            If None, the existing 'serviceCount' limit will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.service_count`, if any.
        :type  deployment_count: :class:`long` or ``None``
        :param deployment_count: This represents the new value for 'deploymentCount' option which is
            the maximum number of deployments in the namespace. This field is
            ignored if
            :attr:`ResourceQuotaOptionsV1Update.deployment_count_unset` is set
            to ``true``.
            If None, the existing 'deploymentCount' limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.deployment_count_unset` is None
            or set to ``false``.
        :type  deployment_count_unset: :class:`bool` or ``None``
        :param deployment_count_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.deployment_count`. If this
            field is set to ``true``, the existing 'deploymentCount' limit on
            the namespace will be reset. If this field is set to ``false``, the
            existing deployment count limit will be changed to the value
            specified in :attr:`ResourceQuotaOptionsV1Update.deployment_count`,
            if any.
            If None, the existing 'deploymentCount' limit will be changed to
            the value specified in
            :attr:`ResourceQuotaOptionsV1Update.deployment_count`, if any.
        :type  daemon_set_count: :class:`long` or ``None``
        :param daemon_set_count: This represents the new value for 'daemonSetCount' option which is
            the maximum number of DaemonSets in the namespace. This field is
            ignored if
            :attr:`ResourceQuotaOptionsV1Update.daemon_set_count_unset` is set
            to ``true``.
            If None, the existing 'daemonSetCount' limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.daemon_set_count_unset` is None
            or set to ``false``.
        :type  daemon_set_count_unset: :class:`bool` or ``None``
        :param daemon_set_count_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.daemon_set_count`. If this
            field is set to ``true``, the existing 'daemonSetCount' limit on
            the namespace will be reset. If this field is set to ``false``, the
            existing daemonset count limit will be changed to the value
            specified in :attr:`ResourceQuotaOptionsV1Update.daemon_set_count`,
            if any.
            If None, the existing 'daemonSetCount' limit will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.daemon_set_count`, if any.
        :type  replica_set_count: :class:`long` or ``None``
        :param replica_set_count: This represents the new value for 'replicaSetCount' option which is
            the maximum number of ReplicaSets in the namespace. This field is
            ignored if
            :attr:`ResourceQuotaOptionsV1Update.replica_set_count_unset` is set
            to ``true``.
            If None, the existing 'replicaSetCount' limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.replica_set_count_unset` is
            None or set to ``false``.
        :type  replica_set_count_unset: :class:`bool` or ``None``
        :param replica_set_count_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.replica_set_count`. If this
            field is set to ``true``, the existing 'replicaSetCount' limit on
            the namespace will be reset. If this field is set to ``false``, the
            existing replicaset count limit will be changed to the value
            specified in
            :attr:`ResourceQuotaOptionsV1Update.replica_set_count`, if any.
            If None, the existing 'replicaSetCount' limit will be changed to
            the value specified in
            :attr:`ResourceQuotaOptionsV1Update.replica_set_count`, if any.
        :type  replication_controller_count: :class:`long` or ``None``
        :param replication_controller_count: This represents the new value for 'replicationControllerCount'
            option which is the maximum number of ReplicationControllers in the
            namespace. This field is ignored if
            :attr:`ResourceQuotaOptionsV1Update.replication_controller_count_unset`
            is set to ``true``.
            If None, the existing 'replicationControllerCount' limit will be
            unchanged if
            :attr:`ResourceQuotaOptionsV1Update.replication_controller_count_unset`
            is None or set to ``false``.
        :type  replication_controller_count_unset: :class:`bool` or ``None``
        :param replication_controller_count_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.replication_controller_count`.
            If this field is set to ``true``, the existing
            'replicationControllerCount' limit on the namespace will be reset.
            If this field is set to ``false``, the existing
            replicationcontroller count limit will be changed to the value
            specified in
            :attr:`ResourceQuotaOptionsV1Update.replication_controller_count`,
            if any.
            If None, the existing 'replicationControllerCount' limit will be
            changed to the value specified in
            :attr:`ResourceQuotaOptionsV1Update.replication_controller_count`,
            if any.
        :type  stateful_set_count: :class:`long` or ``None``
        :param stateful_set_count: This represents the new value for 'statefulSetCount' option which
            is the maximum number of StatefulSets in the namespace. This field
            is ignored if
            :attr:`ResourceQuotaOptionsV1Update.stateful_set_count_unset` is
            set to ``true``.
            If None, the existing 'statefulSetCount' limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.stateful_set_count_unset` is
            None or set to ``false``.
        :type  stateful_set_count_unset: :class:`bool` or ``None``
        :param stateful_set_count_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.stateful_set_count`. If this
            field is set to ``true``, the existing 'statefulSetCount' limit on
            the namespace will be reset. If this field is set to ``false``, the
            existing statefulset count limit will be changed to the value
            specified in
            :attr:`ResourceQuotaOptionsV1Update.stateful_set_count`, if any.
            If None, the existing 'statefulSetCount' limit will be changed to
            the value specified in
            :attr:`ResourceQuotaOptionsV1Update.stateful_set_count`, if any.
        :type  config_map_count: :class:`long` or ``None``
        :param config_map_count: This represents the new value for 'configMapCount' option which is
            the maximum number of ConfigMaps in the namespace. This field is
            ignored if
            :attr:`ResourceQuotaOptionsV1Update.config_map_count_unset` is set
            to ``true``.
            If None, the existing 'configMapCount' limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.config_map_count_unset` is None
            or set to ``false``.
        :type  config_map_count_unset: :class:`bool` or ``None``
        :param config_map_count_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.config_map_count`. If this
            field is set to ``true``, the existing 'configMapCount' limit on
            the namespace will be reset. If this field is set to ``false``, the
            existing configmap count limit will be changed to the value
            specified in :attr:`ResourceQuotaOptionsV1Update.config_map_count`,
            if any.
            If None, the existing 'configMapCount' limit will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.config_map_count`, if any.
        :type  secret_count: :class:`long` or ``None``
        :param secret_count: This represents the new value for 'secretCount' option which is the
            maximum number of secrets in the namespace. This field is ignored
            if :attr:`ResourceQuotaOptionsV1Update.secret_count_unset` is set
            to ``true``.
            If None, the existing 'secretCount' limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.secret_count_unset` is None or
            set to ``false``.
        :type  secret_count_unset: :class:`bool` or ``None``
        :param secret_count_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.secret_count`. If this field is
            set to ``true``, the existing 'secretCount' limit on the namespace
            will be reset. If this field is set to ``false``, the existing
            secret count limit will be changed to the value specified in
            :attr:`ResourceQuotaOptionsV1Update.secret_count`, if any.
            If None, the existing 'secretCount' limit will be changed to the
            value specified in
            :attr:`ResourceQuotaOptionsV1Update.secret_count`, if any.
        :type  persistent_volume_claim_count: :class:`long` or ``None``
        :param persistent_volume_claim_count: This represents the new value for 'persistentVolumeClaimCount'
            option which is the maximum number of PersistentVolumeClaims in the
            namespace. This field is ignored if
            :attr:`ResourceQuotaOptionsV1Update.persistent_volume_claim_count_unset`
            is set to ``true``.
            If None, the existing 'persistentVolumeClaimCount' limit will be
            unchanged if
            :attr:`ResourceQuotaOptionsV1Update.persistent_volume_claim_count_unset`
            is None or set to ``false``.
        :type  persistent_volume_claim_count_unset: :class:`bool` or ``None``
        :param persistent_volume_claim_count_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.persistent_volume_claim_count`.
            If this field is set to ``true``, the existing
            'persistentVolumeClaimCount' limit on the namespace will be reset.
            If this field is set to ``false``, the existing
            replicationcontroller count limit will be changed to the value
            specified in
            :attr:`ResourceQuotaOptionsV1Update.persistent_volume_claim_count`,
            if any.
            If None, the existing 'persistentVolumeClaimCount' limit will be
            changed to the value specified in
            :attr:`ResourceQuotaOptionsV1Update.persistent_volume_claim_count`,
            if any.
        :type  job_count: :class:`long` or ``None``
        :param job_count: This represents the new value for 'jobCount' option which is the
            maximum number of jobs in the namespace. This field is ignored if
            :attr:`ResourceQuotaOptionsV1Update.job_count_unset` is set to
            ``true``.
            If None, the existing 'jobCount' limit will be unchanged if
            :attr:`ResourceQuotaOptionsV1Update.job_count_unset` is None or set
            to ``false``.
        :type  job_count_unset: :class:`bool` or ``None``
        :param job_count_unset: This represents the intent of the change to
            :attr:`ResourceQuotaOptionsV1Update.job_count`. If this field is
            set to ``true``, the existing 'jobCount' limit on the namespace
            will be reset. If this field is set to ``false``, the existing
            secret count limit will be changed to the value specified in
            :attr:`ResourceQuotaOptionsV1Update.job_count`, if any.
            If None, the existing 'jobCount' limit will be changed to the value
            specified in :attr:`ResourceQuotaOptionsV1Update.job_count`, if
            any.
        """
        self.memory_limit = memory_limit
        self.memory_limit_unset = memory_limit_unset
        self.memory_limit_default = memory_limit_default
        self.memory_limit_default_unset = memory_limit_default_unset
        self.memory_request_default = memory_request_default
        self.memory_request_default_unset = memory_request_default_unset
        self.cpu_limit = cpu_limit
        self.cpu_limit_unset = cpu_limit_unset
        self.cpu_limit_default = cpu_limit_default
        self.cpu_limit_default_unset = cpu_limit_default_unset
        self.cpu_request_default = cpu_request_default
        self.cpu_request_default_unset = cpu_request_default_unset
        self.storage_request_limit = storage_request_limit
        self.storage_request_limit_unset = storage_request_limit_unset
        self.pod_count = pod_count
        self.pod_count_unset = pod_count_unset
        self.service_count = service_count
        self.service_count_unset = service_count_unset
        self.deployment_count = deployment_count
        self.deployment_count_unset = deployment_count_unset
        self.daemon_set_count = daemon_set_count
        self.daemon_set_count_unset = daemon_set_count_unset
        self.replica_set_count = replica_set_count
        self.replica_set_count_unset = replica_set_count_unset
        self.replication_controller_count = replication_controller_count
        self.replication_controller_count_unset = replication_controller_count_unset
        self.stateful_set_count = stateful_set_count
        self.stateful_set_count_unset = stateful_set_count_unset
        self.config_map_count = config_map_count
        self.config_map_count_unset = config_map_count_unset
        self.secret_count = secret_count
        self.secret_count_unset = secret_count_unset
        self.persistent_volume_claim_count = persistent_volume_claim_count
        self.persistent_volume_claim_count_unset = persistent_volume_claim_count_unset
        self.job_count = job_count
        self.job_count_unset = job_count_unset
        VapiStruct.__init__(self)


ResourceQuotaOptionsV1Update._set_binding_type(type.StructType(
    'com.vmware.vcenter.namespaces.resource_quota_options_v1_update', {
        'memory_limit': type.OptionalType(type.IntegerType()),
        'memory_limit_unset': type.OptionalType(type.BooleanType()),
        'memory_limit_default': type.OptionalType(type.IntegerType()),
        'memory_limit_default_unset': type.OptionalType(type.BooleanType()),
        'memory_request_default': type.OptionalType(type.IntegerType()),
        'memory_request_default_unset': type.OptionalType(type.BooleanType()),
        'cpu_limit': type.OptionalType(type.IntegerType()),
        'cpu_limit_unset': type.OptionalType(type.BooleanType()),
        'cpu_limit_default': type.OptionalType(type.IntegerType()),
        'cpu_limit_default_unset': type.OptionalType(type.BooleanType()),
        'cpu_request_default': type.OptionalType(type.IntegerType()),
        'cpu_request_default_unset': type.OptionalType(type.BooleanType()),
        'storage_request_limit': type.OptionalType(type.IntegerType()),
        'storage_request_limit_unset': type.OptionalType(type.BooleanType()),
        'pod_count': type.OptionalType(type.IntegerType()),
        'pod_count_unset': type.OptionalType(type.BooleanType()),
        'service_count': type.OptionalType(type.IntegerType()),
        'service_count_unset': type.OptionalType(type.BooleanType()),
        'deployment_count': type.OptionalType(type.IntegerType()),
        'deployment_count_unset': type.OptionalType(type.BooleanType()),
        'daemon_set_count': type.OptionalType(type.IntegerType()),
        'daemon_set_count_unset': type.OptionalType(type.BooleanType()),
        'replica_set_count': type.OptionalType(type.IntegerType()),
        'replica_set_count_unset': type.OptionalType(type.BooleanType()),
        'replication_controller_count': type.OptionalType(type.IntegerType()),
        'replication_controller_count_unset': type.OptionalType(type.BooleanType()),
        'stateful_set_count': type.OptionalType(type.IntegerType()),
        'stateful_set_count_unset': type.OptionalType(type.BooleanType()),
        'config_map_count': type.OptionalType(type.IntegerType()),
        'config_map_count_unset': type.OptionalType(type.BooleanType()),
        'secret_count': type.OptionalType(type.IntegerType()),
        'secret_count_unset': type.OptionalType(type.BooleanType()),
        'persistent_volume_claim_count': type.OptionalType(type.IntegerType()),
        'persistent_volume_claim_count_unset': type.OptionalType(type.BooleanType()),
        'job_count': type.OptionalType(type.IntegerType()),
        'job_count_unset': type.OptionalType(type.BooleanType()),
    },
    ResourceQuotaOptionsV1Update,
    False,
    None))



class Access(VapiInterface):
    """
    The ``Access`` class provides methods to manage access control of subjects
    on namespaces.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespaces.access'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _AccessStub)
        self._VAPI_OPERATION_IDS = {}

    class Role(Enum):
        """
        The ``Access.Role`` class lists the default roles which can be associated
        with a subject on a domain on the namespace.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        OWNER = None
        """
        This role allows modification and deletion of the namespace. This class
        attribute was added in vSphere API 7.0.2.00100.

        """
        EDIT = None
        """
        This role allows modification of the namespace.

        """
        VIEW = None
        """
        This is a read-only role on the namespace.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Role` instance.
            """
            Enum.__init__(string)

    Role._set_values({
        'OWNER': Role('OWNER'),
        'EDIT': Role('EDIT'),
        'VIEW': Role('VIEW'),
    })
    Role._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespaces.access.role',
        Role))


    class SubjectType(Enum):
        """
        The ``Access.SubjectType`` class lists the types of subjects who can be
        associated with a ``Access.Role`` on the namespace.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        USER = None
        """
        Single user.

        """
        GROUP = None
        """
        Group of users.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`SubjectType` instance.
            """
            Enum.__init__(string)

    SubjectType._set_values({
        'USER': SubjectType('USER'),
        'GROUP': SubjectType('GROUP'),
    })
    SubjectType._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespaces.access.subject_type',
        SubjectType))


    class Info(VapiStruct):
        """
        The ``Access.Info`` class contains the information about the access control
        of the subject on given domain on the namespace.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     role=None,
                     identity_provider=None,
                     inherited=None,
                    ):
            """
            :type  role: :class:`Access.Role`
            :param role: Role of the subject on the namespace.
            :type  identity_provider: :class:`str` or ``None``
            :param identity_provider: UUID of an external identity provider for the user, if any. Use
                this field if the user is coming from an external identity provider
                configured via the
                com.vmware.vcenter.namespace_management.supervisors.identity.Providers
                service. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``.
                If unset, vCenter Single Sign-On will be used as the identity
                provider.
            :type  inherited: :class:`bool`
            :param inherited: Flag to indicate if the :attr:`Access.Info.role` is direct or
                inherited. The value is set to ``true`` if the
                :attr:`Access.Info.role` is inherited from group membership. This
                attribute was added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.role = role
            self.identity_provider = identity_provider
            self.inherited = inherited
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.access.info', {
            'role': type.ReferenceType(__name__, 'Access.Role'),
            'identity_provider': type.OptionalType(type.IdType()),
            'inherited': type.OptionalType(type.BooleanType()),
        },
        Info,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``Access.CreateSpec`` class contains the specification required to
        create access control on the namespace.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     role=None,
                     identity_provider=None,
                    ):
            """
            :type  role: :class:`Access.Role`
            :param role: Role to be assigned.
            :type  identity_provider: :class:`str` or ``None``
            :param identity_provider: UUID of an external identity provider for the user, if any. Use
                this field if the user is coming from an external identity provider
                configured via the
                com.vmware.vcenter.namespace_management.supervisors.identity.Providers
                service. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``.
                If unset, vCenter Single Sign-On will be used as the identity
                provider.
            """
            self.role = role
            self.identity_provider = identity_provider
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.access.create_spec', {
            'role': type.ReferenceType(__name__, 'Access.Role'),
            'identity_provider': type.OptionalType(type.IdType()),
        },
        CreateSpec,
        False,
        None))


    class SetSpec(VapiStruct):
        """
        The ``Access.SetSpec`` class contains the specification required to set new
        access control on the namespace.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     role=None,
                     identity_provider=None,
                    ):
            """
            :type  role: :class:`Access.Role`
            :param role: Role to be assigned.
            :type  identity_provider: :class:`str` or ``None``
            :param identity_provider: UUID of an external identity provider for the user, if any. Use
                this field if the user is coming from an external identity provider
                configured via the
                com.vmware.vcenter.namespace_management.supervisors.identity.Providers
                service. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``.
                If unset, vCenter Single Sign-On will be used as the identity
                provider.
            """
            self.role = role
            self.identity_provider = identity_provider
            VapiStruct.__init__(self)


    SetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.access.set_spec', {
            'role': type.ReferenceType(__name__, 'Access.Role'),
            'identity_provider': type.OptionalType(type.IdType()),
        },
        SetSpec,
        False,
        None))



    def create(self,
               namespace,
               domain,
               subject,
               type,
               spec,
               ):
        """
        Set up access control for the subject on given domain on the namespace.

        :type  namespace: :class:`str`
        :param namespace: Identifier for the namespace.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.Instance``.
        :type  domain: :class:`str`
        :param domain: The domain of the subject.
        :type  subject: :class:`str`
        :param subject: The principal for this operation.
        :type  type: :class:`Access.SubjectType`
        :param type: The type of subject (USER or GROUP).
        :type  spec: :class:`Access.CreateSpec`
        :param spec: Information about the access control to be created.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the specified principal on given domain is already associated
            with a role on the namespace.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the namespace is marked for deletion or the associated cluster
            is being disabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``namespace`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors or if an invalid ``type`` is
            specified.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Configure privilege or the
            namespace identifier begins with "vmware-system" prefix.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified principal on given domain is not associated with
            the namespace, or when the user or group does not come from vSphere
            SSO and the OWNER role is being granted.
        """
        return self._invoke('create',
                            {
                            'namespace': namespace,
                            'domain': domain,
                            'subject': subject,
                            'type': type,
                            'spec': spec,
                            })

    def delete(self,
               namespace,
               domain,
               subject,
               type,
               ):
        """
        Remove access control of the subject on given domain from the
        namespace.

        :type  namespace: :class:`str`
        :param namespace: Identifier for the namespace.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.Instance``.
        :type  domain: :class:`str`
        :param domain: The domain of the subject.
        :type  subject: :class:`str`
        :param subject: The principal for this operation.
        :type  type: :class:`Access.SubjectType`
        :param type: The type of subject (USER or GROUP).
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the namespace is marked for deletion or the associated cluster
            is being disabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``namespace`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified principal on given domain is not associated with
            the namespace.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Configure privilege or the
            namespace identifier begins with "vmware-system" prefix.
        """
        return self._invoke('delete',
                            {
                            'namespace': namespace,
                            'domain': domain,
                            'subject': subject,
                            'type': type,
                            })

    def set(self,
            namespace,
            domain,
            subject,
            type,
            spec,
            ):
        """
        Set new access control on the namespace for the subject on given
        domain.

        :type  namespace: :class:`str`
        :param namespace: Identifier for the namespace.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.Instance``.
        :type  domain: :class:`str`
        :param domain: The domain of the subject.
        :type  subject: :class:`str`
        :param subject: The principal for this operation.
        :type  type: :class:`Access.SubjectType`
        :param type: The type of subject (USER or GROUP).
        :type  spec: :class:`Access.SetSpec`
        :param spec: Information about the new access control to be assigned.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the namespace is marked for deletion or the associated cluster
            is being disabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``namespace`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified principal on given domain is not associated with
            the namespace, or when changing to OWNER permission for a user or
            group coming from an external identity provider.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors or if an invalid ``type`` is
            specified.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Configure privilege or the
            namespace identifier begins with "vmware-system" prefix.
        """
        return self._invoke('set',
                            {
                            'namespace': namespace,
                            'domain': domain,
                            'subject': subject,
                            'type': type,
                            'spec': spec,
                            })

    def get(self,
            namespace,
            domain,
            subject,
            type,
            ):
        """
        Get the information about the access control of the subject on given
        domain on the namespace.

        :type  namespace: :class:`str`
        :param namespace: Identifier for the namespace.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.Instance``.
        :type  domain: :class:`str`
        :param domain: The domain of the subject.
        :type  subject: :class:`str`
        :param subject: The principal for this operation.
        :type  type: :class:`Access.SubjectType`
        :param type: The type of subject (USER or GROUP).
        :rtype: :class:`Access.Info`
        :return: Information about the subject including the type and the role on
            the namespace.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``namespace`` cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified principal on given domain is not associated with
            the namespace.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'namespace': namespace,
                            'domain': domain,
                            'subject': subject,
                            'type': type,
                            })
class NamespaceSelfService(VapiInterface):
    """
    The ``NamespaceSelfService`` class provides methods to activate and
    deactivate a namespace template that empowers users as self-service
    namespace users. If the service is activated on a cluster, users can create
    Supervisor Namespaces through kubectl create namespace command without the
    need of extra assistance. This class was added in vSphere API 7.0.2.00100.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespaces.namespace_self_service'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _NamespaceSelfServiceStub)
        self._VAPI_OPERATION_IDS = {}

    class Capability(Enum):
        """
        The ``NamespaceSelfService.Capability`` class describes the self-service
        namespace capability of the cluster on which vSphere Namespaces enabled.
        This enumeration was added in vSphere API 7.0.2.00100.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        UNKNOWN = None
        """
        The initial value that represents the in-progress activity of determining
        the cluster's self-service namespace capability. This class attribute was
        added in vSphere API 7.0.2.00100.

        """
        SUPPORTED = None
        """
        The value that indicates the cluster supports self-service namespace
        capability. The expected transition UNKNOWN --> SUPPORTED. This class
        attribute was added in vSphere API 7.0.2.00100.

        """
        NOTSUPPORTED = None
        """
        The value that indicates the cluster doesn't support the self-service
        namespace capability. The expected transition UNKNOWN --> NOTSUPPORTED.
        This class attribute was added in vSphere API 7.0.2.00100.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Capability` instance.
            """
            Enum.__init__(string)

    Capability._set_values({
        'UNKNOWN': Capability('UNKNOWN'),
        'SUPPORTED': Capability('SUPPORTED'),
        'NOTSUPPORTED': Capability('NOTSUPPORTED'),
    })
    Capability._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespaces.namespace_self_service.capability',
        Capability))


    class Status(Enum):
        """
        The page describes the status of the namespace self-service on the cluster
        on which vSphere Namespaces enabled. This enumeration was added in vSphere
        API 7.0.2.00100.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        CONFIGURING = None
        """
        The configuration is being applied to the service. This class attribute was
        added in vSphere API 7.0.2.00100.

        """
        RUNNING = None
        """
        The namespace self service is configured correctly. The expected
        transitions: 1. CONFIGURING --> RUNNING 2. RUNNING --> CONFIGURING. This
        transition occurs in the below scenarios: a. When different Dev
        Users/Groups are empowered with self-service namespace access. b. To
        reconcile the state of the cluster after the cluster upgrade. This class
        attribute was added in vSphere API 7.0.2.00100.

        """
        REMOVING = None
        """
        The configuration is being removed and service is being deleted. The
        expected transitions: 1. CONFIGURING --> RUNNING --> REMOVING 2.
        CONFIGURING --> REMOVING. This class attribute was added in vSphere API
        7.0.2.00100.

        """
        DEACTIVATED = None
        """
        The namespace self service is deactivated. This status also represents the
        initial status of the service before activation. The expected transitions
        after the service is activated: 1. CONFIGURING --> RUNNING --> REMOVING -->
        DEACTIVATED 2. CONFIGURING --> REMOVING --> DEACTIVATED. This class
        attribute was added in vSphere API 7.0.2.00100.

        """
        ERROR = None
        """
        Failed to apply the configuration to the namespace self-service or unable
        to deactivate the namespace self-service, user intervention needed. The
        expected transitions: 1. CONFIGURING --> ERROR 2. CONFIGURING --> RUNNING
        --> ERROR 3. CONFIGURING --> RUNNING --> REMOVING --> ERROR 4. CONFIGURING
        --> REMOVING --> ERROR The :attr:`NamespaceSelfService.Info.messages` field
        captures the relevant error messages explaining this ERROR status. This
        class attribute was added in vSphere API 7.0.2.00100.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Status` instance.
            """
            Enum.__init__(string)

    Status._set_values({
        'CONFIGURING': Status('CONFIGURING'),
        'RUNNING': Status('RUNNING'),
        'REMOVING': Status('REMOVING'),
        'DEACTIVATED': Status('DEACTIVATED'),
        'ERROR': Status('ERROR'),
    })
    Status._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespaces.namespace_self_service.status',
        Status))


    class Info(VapiStruct):
        """
        The ``NamespaceSelfService.Info`` class contains detailed information about
        the namespace self service. This class was added in vSphere API
        7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     cluster=None,
                     capability=None,
                     status=None,
                     messages=None,
                    ):
            """
            :type  cluster: :class:`str`
            :param cluster: Identifier for the cluster to which namespace service is
                associated. This attribute was added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            :type  capability: :class:`NamespaceSelfService.Capability`
            :param capability: The self-service namespace capability of the cluster with vSphere
                Namespaces enabled. This attribute was added in vSphere API
                7.0.2.00100.
            :type  status: :class:`NamespaceSelfService.Status`
            :param status: The current status of the namespace-self-service. This attribute
                was added in vSphere API 7.0.2.00100.
            :type  messages: :class:`list` of :class:`Instances.Message`
            :param messages: Current set of messages associated with the object. This attribute
                was added in vSphere API 7.0.2.00100.
            """
            self.cluster = cluster
            self.capability = capability
            self.status = status
            self.messages = messages
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.namespace_self_service.info', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'capability': type.ReferenceType(__name__, 'NamespaceSelfService.Capability'),
            'status': type.ReferenceType(__name__, 'NamespaceSelfService.Status'),
            'messages': type.ListType(type.ReferenceType(__name__, 'Instances.Message')),
        },
        Info,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``NamespaceSelfService.Summary`` class contains basic information about
        the namespace service. This class was added in vSphere API 7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     cluster=None,
                     capability=None,
                     status=None,
                    ):
            """
            :type  cluster: :class:`str`
            :param cluster: Identifier for the cluster to which namespace service is
                associated. This attribute was added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            :type  capability: :class:`NamespaceSelfService.Capability`
            :param capability: The self-service namespace capability of the cluster with vSphere
                Namespaces enabled. This attribute was added in vSphere API
                7.0.2.00100.
            :type  status: :class:`NamespaceSelfService.Status`
            :param status: The current status of the namespace-self-service. This attribute
                was added in vSphere API 7.0.2.00100.
            """
            self.cluster = cluster
            self.capability = capability
            self.status = status
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.namespace_self_service.summary', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'capability': type.ReferenceType(__name__, 'NamespaceSelfService.Capability'),
            'status': type.ReferenceType(__name__, 'NamespaceSelfService.Status'),
        },
        Summary,
        False,
        None))


    class ActivateTemplateSpec(VapiStruct):
        """
        The ``NamespaceSelfService.ActivateTemplateSpec`` class contains the
        specification required to create or update namespace template. The create
        or update template operations are combined with service activation in a
        single operation. This class was added in vSphere API 7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     template=None,
                     permissions=None,
                     resource_spec=None,
                     storage_specs=None,
                     networks=None,
                     vm_service_spec=None,
                     content_libraries=None,
                    ):
            """
            :type  template: :class:`str`
            :param template: Identifier of the namespace template that is being activated. This
                attribute was added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.NamespaceTemplate``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.NamespaceTemplate``.
            :type  permissions: :class:`list` of :class:`NamespaceTemplates.Subject`
            :param permissions: Namespace Self Service permission to subjects. This attribute was
                added in vSphere API 7.0.2.00100.
            :type  resource_spec: :class:`vmware.vapi.struct.VapiStruct`
            :param resource_spec: Resource quotas that the template defines. Resource quota on the
                namespace. Refer to
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions.Info#createResourceQuotaType
                and use
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions#get
                for retrieving the type for the value for this field. For an
                example of this, see :class:`ResourceQuotaOptionsV1`. This
                attribute was added in vSphere API 7.0.2.00100.
            :type  storage_specs: :class:`list` of :class:`Instances.StorageSpec`
            :param storage_specs: Storage associated with the self service namespace. This attribute
                was added in vSphere API 7.0.2.00100.
            :type  networks: :class:`list` of :class:`str` or ``None``
            :param networks: vSphere Namespaces network objects to be associated with the
                namespace. The values of this list need to reference names of
                pre-existing
                ``com.vmware.vcenter.namespace_management.Networks.Info`` classs.
                This attribute was added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will contain identifiers for
                the resource type: ``ClusterComputeResource``.
                The field must be left None if the cluster hosting the namespace
                uses NSXT_CONTAINER_PLUGIN as the network provider, since the
                network(s) for this namespace will be managed by NSX-T Container
                Plugin. If field is None when the cluster hosting the namespace
                uses VSPHERE_NETWORK as its network provider, the namespace will
                automatically be associated with the cluster's Supervisor Primary
                Workload Network. The field currently accepts at most only 1
                vSphere Namespaces network object reference.
            :type  vm_service_spec: :class:`Instances.VMServiceSpec` or ``None``
            :param vm_service_spec: VM Service specification to be associated with the namespace
                template. Namespaces created using this template will have access
                to the virtual machine classes and Content Libraries specified in
                this {ActivateTemplateSpec#vmServiceSpec} by default. This
                attribute was added in vSphere API 7.0.3.2.
                If None, the namespaces created using this template will not have
                access to any virtual machine classes, and to any Content Libraries
                by default unless Content Libraries are specified in the
                {ActivateTemplateSpec#contentLibraries}.
            :type  content_libraries: :class:`list` of :class:`Instances.ContentLibrarySpec` or ``None``
            :param content_libraries: Content Library specifications to be associated with the namespace
                template. Namespaces created using this template will have access
                to the Content Libraries specified in this
                {ActivateTemplateSpec#contentLibraries} by default. This attribute
                was added in vSphere API 8.0.2.0.
                If None, the namespaces created using this template will not have
                access to any Content Libraries by default unless Content Libraries
                are specified in the {ActivateTemplateSpec#vmServiceSpec}.
            """
            self.template = template
            self.permissions = permissions
            self.resource_spec = resource_spec
            self.storage_specs = storage_specs
            self.networks = networks
            self.vm_service_spec = vm_service_spec
            self.content_libraries = content_libraries
            VapiStruct.__init__(self)


    ActivateTemplateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.namespace_self_service.activate_template_spec', {
            'template': type.IdType(resource_types='com.vmware.vcenter.namespaces.NamespaceTemplate'),
            'permissions': type.ListType(type.ReferenceType(__name__, 'NamespaceTemplates.Subject')),
            'resource_spec': type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct),
            'storage_specs': type.ListType(type.ReferenceType(__name__, 'Instances.StorageSpec')),
            'networks': type.OptionalType(type.ListType(type.IdType())),
            'vm_service_spec': type.OptionalType(type.ReferenceType(__name__, 'Instances.VMServiceSpec')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.ContentLibrarySpec'))),
        },
        ActivateTemplateSpec,
        False,
        None))



    def activate(self,
                 cluster,
                 ):
        """
        Activate Namespace Self Service on the cluster on which vSphere
        Namespaces enabled. This operation empowers Dev Users/Groups as
        self-service namespace users to create Supervisor Namespaces through
        kubectl create namespace command. activate requires the availability of
        one or more templates in the system. A Supervisor can be running on one
        or multiple vSphere Zones, and each vSphere Zone is associated with one
        or more vSphere Clusters. If a Supervisor running on the specified
        vSphere Cluster is running on additional vSphere Clusters, this
        operation will apply to Supervisor components running on the other
        vSphere Clusters in addition to the specified vSphere Cluster. To call
        this API on a Supervisor with multiple vSphere Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.2.00100.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which vSphere Namespaces will be
            enabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the cluster already has Namespace Self Service activated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if cluster with vSphere Namespaces enabled could not be located or
            no namespace templates exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.UnableToAllocateResource` 
            if the specified cluster is not licensed.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.SelfServiceManage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the service is marked for deactivation or the associated cluster
            is being disabled or no namespace template exists in the system.
        """
        return self._invoke('activate',
                            {
                            'cluster': cluster,
                            })

    def deactivate(self,
                   cluster,
                   ):
        """
        Deactivate Namespace Self Service on the cluster on which vSphere
        Namespaces enabled. This operation reverses Dev Users/Group's
        self-service namespace capability on the cluster. A Supervisor can be
        running on one or multiple vSphere Zones, and each vSphere Zone is
        associated with one or more vSphere Clusters. If a Supervisor running
        on the specified vSphere Cluster is running on additional vSphere
        Clusters, this operation will apply to Supervisor components running on
        the other vSphere Clusters in addition to the specified vSphere
        Cluster. To call this API on a Supervisor with multiple vSphere
        Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.2.00100.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster for which vSphere Namespaces will be
            disabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if cluster with vSphere Namespaced enabled is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.SelfServiceManage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the service is not activated.
        """
        return self._invoke('deactivate',
                            {
                            'cluster': cluster,
                            })

    def get(self,
            cluster,
            ):
        """
        Returns information about Namespace Self Service of a specific cluster.
        A Supervisor can be running on one or multiple vSphere Zones, and each
        vSphere Zone is associated with one or more vSphere Clusters. If a
        Supervisor running on the specified vSphere Cluster is running on
        additional vSphere Clusters, this operation will apply to Supervisor
        components running on the other vSphere Clusters in addition to the
        specified vSphere Cluster. To call this API on a Supervisor with
        multiple vSphere Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.2.00100.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which vSphere Namespaces are enabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`NamespaceSelfService.Info`
        :return: Information about the namespace self service associated with the
            specified cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if cluster with vSphere Namespaced enabled could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            })

    def list(self):
        """
        Returns basic information about Namespace Self Service on all clusters
        on which vSphere Namespaces are enabled on this vCenter. This method
        was added in vSphere API 7.0.2.00100.


        :rtype: :class:`list` of :class:`NamespaceSelfService.Summary`
        :return: List of summary of Namespace Self Service associated with all
            clusters with vSphere Namespaces enabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list', None)

    def activate_with_template(self,
                               cluster,
                               spec,
                               ):
        """
        Activate Namespace Self Service on the cluster after configuring
        namespace template. This is another variant of activate except
        configures template before activation. The template configuration
        includes either creating a new template or updating the existing
        template, depending on the template's existence. Here is supported the
        flow of actions using the activateWithTemplate call: 1. Activate with
        the new template using activateWithTemplate call. 2. Deactivate using
        deactivate call. 3. Active with updating the existing template using
        activateWithTemplate. A Supervisor can be running on one or multiple
        vSphere Zones, and each vSphere Zone is associated with one or more
        vSphere Clusters. If a Supervisor running on the specified vSphere
        Cluster is running on additional vSphere Clusters, this operation will
        apply to Supervisor components running on the other vSphere Clusters in
        addition to the specified vSphere Cluster. To call this API on a
        Supervisor with multiple vSphere Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.2.00100.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which vSphere Namespaces will be
            enabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`NamespaceSelfService.ActivateTemplateSpec`
        :param spec: Specification for activating namespace self service on the cluster
            by granting users/groups to create Supervisor Namespaces.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the cluster already has Namespace Self Service activated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if cluster with vSphere Namespaces enabled could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.UnableToAllocateResource` 
            if the specified cluster is not licensed.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.SelfServiceManage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the service is marked for deactivation or the associated cluster
            is being disabled.
        """
        return self._invoke('activate_with_template',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })
class NamespaceTemplates(VapiInterface):
    """
    The ``NamespaceTemplates`` class provides methods to create and update
    namespace templates on a cluster. The namespace templates are used if the
    ``NamespaceSelfService`` is enabled on a Supervisor. This class was added
    in vSphere API 7.0.2.00100.
    """
    RESOURCE_TYPE = "com.vmware.vcenter.namespaces.NamespaceTemplate"
    """
    The resource type for namespace template. This class attribute was added in
    vSphere API 7.0.2.00100.

    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespaces.namespace_templates'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _NamespaceTemplatesStub)
        self._VAPI_OPERATION_IDS = {}

    class Subject(VapiStruct):
        """
        The ``NamespaceTemplates.Subject`` class contains the user or group
        information granted for namespace self service. This class was added in
        vSphere API 7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     subject_type=None,
                     subject=None,
                     domain=None,
                    ):
            """
            :type  subject_type: :class:`Access.SubjectType`
            :param subject_type: Type of the subject. This attribute was added in vSphere API
                7.0.2.00100.
            :type  subject: :class:`str`
            :param subject: Name of the subject. This attribute was added in vSphere API
                7.0.2.00100.
            :type  domain: :class:`str`
            :param domain: Domain of the subject. This attribute was added in vSphere API
                7.0.2.00100.
            """
            self.subject_type = subject_type
            self.subject = subject
            self.domain = domain
            VapiStruct.__init__(self)


    Subject._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.namespace_templates.subject', {
            'subject_type': type.ReferenceType(__name__, 'Access.SubjectType'),
            'subject': type.StringType(),
            'domain': type.StringType(),
        },
        Subject,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``NamespaceTemplates.Info`` class contains the detailed information
        about the namespace template. This class was added in vSphere API
        7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     cluster=None,
                     template=None,
                     resource_spec=None,
                     storage_specs=None,
                     networks=None,
                     permissions=None,
                     vm_service_spec=None,
                     content_libraries=None,
                    ):
            """
            :type  cluster: :class:`str`
            :param cluster: Identifier for the vSphere cluster associated with namespace
                template. This attribute was added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            :type  template: :class:`str`
            :param template: Name of the namespace template. This attribute was added in vSphere
                API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.NamespaceTemplate``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.NamespaceTemplate``.
            :type  resource_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param resource_spec: Resource quotas that this template defines. Quotas on the namespace
                resources. Refer to
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions#get
                for the type of the value for this field. This attribute was added
                in vSphere API 7.0.2.00100.
                If None, no resource constraints are defined in the namespace
                template.
            :type  storage_specs: :class:`list` of :class:`Instances.StorageSpec`
            :param storage_specs: Storage that this template defines and will be associated with a
                namespace after namespace realization. This attribute was added in
                vSphere API 7.0.2.00100.
            :type  networks: :class:`list` of :class:`str` or ``None``
            :param networks: vSphere Networks that this template captures and are associated
                with the namespace after namespace realization. This attribute was
                added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``.
                This field is None if the cluster hosting this namespace uses
                NSXT_CONTAINER_PLUGIN or NSXT_VPC as its network provider.
            :type  permissions: :class:`list` of :class:`NamespaceTemplates.Subject` or ``None``
            :param permissions: Permissions associated with namespace template. This attribute was
                added in vSphere API 7.0.2.00100.
                If None, only users with the Administrator role can use this
                template; for example, this template is applied to the namespace
                created by self-service-users with the Administrator role.
            :type  vm_service_spec: :class:`Instances.VMServiceSpec` or ``None``
            :param vm_service_spec: Current set of virtual machine classes and Content Libraries
                associated with the template. This attribute was added in vSphere
                API 7.0.3.2.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  content_libraries: :class:`list` of :class:`Instances.ContentLibrarySpec` or ``None``
            :param content_libraries: Current set of Content Library specifications associated with the
                template. This attribute was added in vSphere API 8.0.2.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.cluster = cluster
            self.template = template
            self.resource_spec = resource_spec
            self.storage_specs = storage_specs
            self.networks = networks
            self.permissions = permissions
            self.vm_service_spec = vm_service_spec
            self.content_libraries = content_libraries
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.namespace_templates.info', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'template': type.IdType(resource_types='com.vmware.vcenter.namespaces.NamespaceTemplate'),
            'resource_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
            'storage_specs': type.ListType(type.ReferenceType(__name__, 'Instances.StorageSpec')),
            'networks': type.OptionalType(type.ListType(type.IdType())),
            'permissions': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'NamespaceTemplates.Subject'))),
            'vm_service_spec': type.OptionalType(type.ReferenceType(__name__, 'Instances.VMServiceSpec')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.ContentLibrarySpec'))),
        },
        Info,
        False,
        None))


    class InfoV2(VapiStruct):
        """
        The ``NamespaceTemplates.InfoV2`` class contains the detailed information
        about the namespace template on a Supervisor. This class was added in
        vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor=None,
                     template=None,
                     resource_spec=None,
                     storage_specs=None,
                     networks=None,
                     permissions=None,
                     vm_service_spec=None,
                     content_libraries=None,
                    ):
            """
            :type  supervisor: :class:`str`
            :param supervisor: Identifier for the Supervisor associated with namespace template.
                This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
            :type  template: :class:`str`
            :param template: Name of the namespace template. This attribute was added in vSphere
                API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.NamespaceTemplate``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.NamespaceTemplate``.
            :type  resource_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param resource_spec: Resource quotas that this template defines. Quotas on the namespace
                resources. Refer to
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions#get
                for the type of the value for this field. This attribute was added
                in vSphere API 7.0.2.00100.
                If None, no resource constraints are defined in the namespace
                template.
            :type  storage_specs: :class:`list` of :class:`Instances.StorageSpec`
            :param storage_specs: Storage that this template defines and will be associated with a
                namespace after namespace realization. This attribute was added in
                vSphere API 7.0.2.00100.
            :type  networks: :class:`list` of :class:`str` or ``None``
            :param networks: vSphere Networks that this template captures and are associated
                with the namespace after namespace realization. This attribute was
                added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``.
                This field is None if the cluster hosting this namespace uses
                NSXT_CONTAINER_PLUGIN or NSXT_VPC as its network provider.
            :type  permissions: :class:`list` of :class:`NamespaceTemplates.Subject` or ``None``
            :param permissions: Permissions associated with namespace template. This attribute was
                added in vSphere API 7.0.2.00100.
                If None, only users with the Administrator role can use this
                template; for example, this template is applied to the namespace
                created by self-service-users with the Administrator role.
            :type  vm_service_spec: :class:`Instances.VMServiceSpec` or ``None``
            :param vm_service_spec: Current set of virtual machine classes and Content Libraries
                associated with the template. This attribute was added in vSphere
                API 7.0.3.2.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  content_libraries: :class:`list` of :class:`Instances.ContentLibrarySpec` or ``None``
            :param content_libraries: Current set of Content Library specifications associated with the
                template. This attribute was added in vSphere API 8.0.2.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.supervisor = supervisor
            self.template = template
            self.resource_spec = resource_spec
            self.storage_specs = storage_specs
            self.networks = networks
            self.permissions = permissions
            self.vm_service_spec = vm_service_spec
            self.content_libraries = content_libraries
            VapiStruct.__init__(self)


    InfoV2._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.namespace_templates.info_v2', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'template': type.IdType(resource_types='com.vmware.vcenter.namespaces.NamespaceTemplate'),
            'resource_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
            'storage_specs': type.ListType(type.ReferenceType(__name__, 'Instances.StorageSpec')),
            'networks': type.OptionalType(type.ListType(type.IdType())),
            'permissions': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'NamespaceTemplates.Subject'))),
            'vm_service_spec': type.OptionalType(type.ReferenceType(__name__, 'Instances.VMServiceSpec')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.ContentLibrarySpec'))),
        },
        InfoV2,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``NamespaceTemplates.Summary`` class contains the basic information
        about the namespace template. This class was added in vSphere API
        7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     cluster=None,
                     template=None,
                    ):
            """
            :type  cluster: :class:`str`
            :param cluster: Identifier for the vSphere cluster associated with namespace
                template. This attribute was added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            :type  template: :class:`str`
            :param template: Name of the namespace template. This attribute was added in vSphere
                API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.NamespaceTemplate``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.NamespaceTemplate``.
            """
            self.cluster = cluster
            self.template = template
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.namespace_templates.summary', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'template': type.IdType(resource_types='com.vmware.vcenter.namespaces.NamespaceTemplate'),
        },
        Summary,
        False,
        None))


    class SummaryV2(VapiStruct):
        """
        The ``NamespaceTemplates.SummaryV2`` class contains the basic information
        about the namespace template on a Supervisor. This class was added in
        vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor=None,
                     template=None,
                    ):
            """
            :type  supervisor: :class:`str`
            :param supervisor: Identifier for the Supervisor associated with namespace template.
                This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
            :type  template: :class:`str`
            :param template: Name of the namespace template. This attribute was added in vSphere
                API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.NamespaceTemplate``. When methods
                return a value of this class as a return value, the attribute will
                be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.NamespaceTemplate``.
            """
            self.supervisor = supervisor
            self.template = template
            VapiStruct.__init__(self)


    SummaryV2._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.namespace_templates.summary_v2', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'template': type.IdType(resource_types='com.vmware.vcenter.namespaces.NamespaceTemplate'),
        },
        SummaryV2,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``NamespaceTemplates.CreateSpec`` class contains the specification
        required to create namespace template. This class was added in vSphere API
        7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     template=None,
                     resource_spec=None,
                     storage_specs=None,
                     networks=None,
                     permissions=None,
                     vm_service_spec=None,
                     content_libraries=None,
                    ):
            """
            :type  template: :class:`str`
            :param template: Identifier of the namespace template. This has DNS_LABEL
                restrictions as specified in `
                <https://tools.ietf.org/html/rfc1123>`_. This name is unique across
                all namespaces templates in this vCenter server. This attribute was
                added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            :type  resource_spec: :class:`vmware.vapi.struct.VapiStruct`
            :param resource_spec: Resource quotas that this template defines. Resource quota on the
                namespace. Refer to
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions.Info#createResourceQuotaType
                and use
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions#get
                for retrieving the type for the value for this field. For an
                example of this, see :class:`ResourceQuotaOptionsV1`. This
                attribute was added in vSphere API 7.0.2.00100.
            :type  storage_specs: :class:`list` of :class:`Instances.StorageSpec`
            :param storage_specs: Storage that this template defines and will be associated with a
                namespace after namespace realization. This field should not be
                empty and at least one policy should be supplied. The {link create}
                throws {term InvalidArgument} exception if this field is set empty.
                This attribute was added in vSphere API 7.0.2.00100.
            :type  networks: :class:`list` of :class:`str` or ``None``
            :param networks: vSphere Networks that this template captures and are associated
                with the namespace after namespace realization. vSphere Namespaces
                network objects to be associated with the namespace. The values of
                this list need to reference names of pre-existing
                ``com.vmware.vcenter.namespace_management.Networks.Info`` classs.
                This attribute was added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``.
                The field must be left None if the cluster hosting the namespace
                uses NSXT_CONTAINER_PLUGIN or NSXT_VPC as the network provider,
                since the network(s) for this namespace will be managed by NSX-T
                Container Plugin. If field is None when the cluster hosting the
                namespace uses VSPHERE_NETWORK as its network provider, the
                namespace will automatically be associated with the cluster's
                Supervisor Primary Workload Network. The field currently accepts at
                most only 1 vSphere Namespaces network object reference.
            :type  permissions: :class:`list` of :class:`NamespaceTemplates.Subject` or ``None``
            :param permissions: Permissions associated with namespace template. This attribute was
                added in vSphere API 7.0.2.00100.
                If None, only users with the Administrator role can use this
                template; for example, this template is applied to the namespace
                created by self-service-users with the Administrator role.
            :type  vm_service_spec: :class:`Instances.VMServiceSpec` or ``None``
            :param vm_service_spec: VM Service specification to be associated with the namespace
                template. Namespaces created using this template will have access
                to the virtual machine classes and Content Libraries specified in
                this {CreateSpec#vmServiceSpec} by default. This attribute was
                added in vSphere API 7.0.3.2.
                If None, the namespaces created using this template will not have
                access to any virtual machine classes by default, and to any
                Content Libraries by default unless Content Libraries are specified
                in the {CreateSpec#contentLibraries}.
            :type  content_libraries: :class:`list` of :class:`Instances.ContentLibrarySpec` or ``None``
            :param content_libraries: Content Library specifications to be associated with the namespace
                template. Namespaces created using this template will have access
                to the Content Libraries specified in this
                {CreateSpec#contentLibraries} by default. This attribute was added
                in vSphere API 8.0.2.0.
                If None, the namespaces created using this template will not have
                access to any Content Libraries by default unless Content Libraries
                are specified in the {CreateSpec#vmServiceSpec}.
            """
            self.template = template
            self.resource_spec = resource_spec
            self.storage_specs = storage_specs
            self.networks = networks
            self.permissions = permissions
            self.vm_service_spec = vm_service_spec
            self.content_libraries = content_libraries
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.namespace_templates.create_spec', {
            'template': type.IdType(resource_types='ClusterComputeResource'),
            'resource_spec': type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct),
            'storage_specs': type.ListType(type.ReferenceType(__name__, 'Instances.StorageSpec')),
            'networks': type.OptionalType(type.ListType(type.IdType())),
            'permissions': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'NamespaceTemplates.Subject'))),
            'vm_service_spec': type.OptionalType(type.ReferenceType(__name__, 'Instances.VMServiceSpec')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.ContentLibrarySpec'))),
        },
        CreateSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``NamespaceTemplates.UpdateSpec`` class contains the specification
        required to update a namespace namespace template. This class was added in
        vSphere API 7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     resource_spec=None,
                     storage_specs=None,
                     networks=None,
                     permissions=None,
                     vm_service_spec=None,
                     content_libraries=None,
                    ):
            """
            :type  resource_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param resource_spec: Resource quota on the namespace. Refer to
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions.Info#createResourceQuotaType
                and use
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions#get
                for retrieving the type for the value for this field. For an
                example of this, see :class:`ResourceQuotaOptionsV1`. This
                attribute was added in vSphere API 7.0.2.00100.
                If None, no resource limits will be set on the namespace.
            :type  storage_specs: :class:`list` of :class:`Instances.StorageSpec` or ``None``
            :param storage_specs: Storage that this template defines and will be associated with a
                namespace after namespace realization. This attribute was added in
                vSphere API 7.0.2.00100.
                If None then no update will be made.
            :type  networks: :class:`list` of :class:`str` or ``None``
            :param networks: vSphere Namespaces network objects to be associated with the
                namespace. The values of this list need to reference names of
                pre-existing
                ``com.vmware.vcenter.namespace_management.Networks.Info`` classs.
                This attribute was added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``.
                The field must be left None if the cluster hosting the namespace
                uses NSXT_CONTAINER_PLUGIN or NSXT_VPC as the network provider,
                since the network(s) for this namespace will be managed by NSX-T
                Container Plugin. If field is None when the cluster hosting the
                namespace uses VSPHERE_NETWORK as its network provider, the
                namespace will automatically be associated with the cluster's
                Supervisor Primary Workload Network. The field currently accepts at
                most only 1 vSphere Namespaces network object reference.
            :type  permissions: :class:`list` of :class:`NamespaceTemplates.Subject` or ``None``
            :param permissions: Permissions associated with namespace template. This attribute was
                added in vSphere API 7.0.2.00100.
                If None, only users with the Administrator role can use this
                template; for example, this template is applied to the namespace
                created by self-service-users with the Administrator role.
            :type  vm_service_spec: :class:`Instances.VMServiceSpec` or ``None``
            :param vm_service_spec: VM Service specification to be associated with the namespace
                template. The virtual machine classes and Content Library
                associations of the template will be updated according to this
                {UpdateSpec#vmServiceSpec}. This attribute was added in vSphere API
                7.0.3.2.
                If None, the namespaces created using this template will not have
                access to any virtual machine classes by default, and to any
                Content Libraries by default unless Content Libraries are specified
                in the {UpdateSpec#contentLibraries}.
            :type  content_libraries: :class:`list` of :class:`Instances.ContentLibrarySpec` or ``None``
            :param content_libraries: Content Library specifications to be associated with the namespace
                template. Namespaces created using this template will have access
                to the Content Libraries specified in this
                {UpdateSpec#contentLibraries} by default. This attribute was added
                in vSphere API 8.0.2.0.
                If None, the namespaces created using this template will not have
                access to any Content Libraries by default unless Content Libraries
                are specified in the {UpdateSpec#vmServiceSpec}.
            """
            self.resource_spec = resource_spec
            self.storage_specs = storage_specs
            self.networks = networks
            self.permissions = permissions
            self.vm_service_spec = vm_service_spec
            self.content_libraries = content_libraries
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.namespace_templates.update_spec', {
            'resource_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
            'storage_specs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.StorageSpec'))),
            'networks': type.OptionalType(type.ListType(type.IdType())),
            'permissions': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'NamespaceTemplates.Subject'))),
            'vm_service_spec': type.OptionalType(type.ReferenceType(__name__, 'Instances.VMServiceSpec')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.ContentLibrarySpec'))),
        },
        UpdateSpec,
        False,
        None))



    def get(self,
            cluster,
            template,
            ):
        """
        Get the information about a namespace template on given cluster. A
        Supervisor can be running on one or multiple vSphere Zones, and each
        vSphere Zone is associated with one or more vSphere Clusters. If a
        Supervisor running on the specified vSphere Cluster is running on
        additional vSphere Clusters, this operation will apply to Supervisor
        components running on the other vSphere Clusters in addition to the
        specified vSphere Cluster. To call this API on a Supervisor with
        multiple vSphere Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.2.00100.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which vSphere Namespaces are enabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  template: :class:`str`
        :param template: Name of the namespace template.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.NamespaceTemplate``.
        :rtype: :class:`NamespaceTemplates.Info`
        :return: Information about the namespace template.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``cluster`` doesn't exist or if ``template`` doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'cluster': cluster,
                            'template': template,
                            })

    def get_v2(self,
               supervisor,
               template,
               ):
        """
        Get the information about a namespace template on a Supervisor. This
        method was added in vSphere API 8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  template: :class:`str`
        :param template: Name of the namespace template.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.NamespaceTemplate``.
        :rtype: :class:`NamespaceTemplates.InfoV2`
        :return: Information about the namespace template.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the Supervisor doesn't exist or if ``template`` doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get_v2',
                            {
                            'supervisor': supervisor,
                            'template': template,
                            })

    def list(self,
             cluster,
             ):
        """
        Returns information about all the namespace templates associated with a
        cluster on which vSphere Namespaces are enabled in this vCenter Server.
        A Supervisor can be running on one or multiple vSphere Zones, and each
        vSphere Zone is associated with one or more vSphere Clusters. If a
        Supervisor running on the specified vSphere Cluster is running on
        additional vSphere Clusters, this operation will apply to Supervisor
        components running on the other vSphere Clusters in addition to the
        specified vSphere Cluster. To call this API on a Supervisor with
        multiple vSphere Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.2.00100.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which vSphere Namespaces are enabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :rtype: :class:`list` of :class:`NamespaceTemplates.Summary`
        :return: List of summary of all namespace templates associated with
            ``cluster`` with vSphere Namespaces enabled.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``cluster`` doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list',
                            {
                            'cluster': cluster,
                            })

    def list_v2(self,
                supervisor,
                ):
        """
        Returns information about all the namespace templates associated with a
        Supervisor. This method was added in vSphere API 8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :rtype: :class:`list` of :class:`NamespaceTemplates.SummaryV2`
        :return: List of summary of all namespace templates associated with the
            Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the Supervisor doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list_v2',
                            {
                            'supervisor': supervisor,
                            })

    def create(self,
               cluster,
               spec,
               ):
        """
        Creates a namespace template on a cluster on which vSphere Namespaces
        are enabled in this vCenter Server. This release supports creating a
        single namespace template, and the call fails if there is a request to
        make another one. A Supervisor can be running on one or multiple
        vSphere Zones, and each vSphere Zone is associated with one or more
        vSphere Clusters. If a Supervisor running on the specified vSphere
        Cluster is running on additional vSphere Clusters, this operation will
        apply to Supervisor components running on the other vSphere Clusters in
        addition to the specified vSphere Cluster. To call this API on a
        Supervisor with multiple vSphere Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.2.00100.

        :type  cluster: :class:`str`
        :param cluster: Identifier for the cluster on which vSphere Namespaces are enabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  spec: :class:`NamespaceTemplates.CreateSpec`
        :param spec: Specification for setting up the namespace template.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``cluster`` doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors, or if {link
            CreateSpec#storageSpecs} is empty, or if {link
            CreateSpec#resourceSpec} is not set with {term memory_limit}, {term
            cpu_limit}, {term storage_request_limit}, or if {link
            CreateSpec#networks} is not set with networks if the {term cluster}
            hosting the namespaces uses VSPHERE_NETWORK as its network
            provider, or if {link CreateSpec#networks} is not empty if the
            {term cluster} hosting the namespaces uses NSXT_CONTAINER_PLUGIN or
            NSXT_VPC as its network provider.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if a request arrives to create a second template or to grant access
            to a user or group from an external identity provider.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.SelfServiceManage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the namespace template with given name already exists.
        """
        return self._invoke('create',
                            {
                            'cluster': cluster,
                            'spec': spec,
                            })

    def create_v2(self,
                  supervisor,
                  spec,
                  ):
        """
        Creates a namespace template on a Supervisor. This release supports
        creating a single namespace template, and the call fails if there is a
        request to make another one. This method was added in vSphere API
        8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  spec: :class:`NamespaceTemplates.CreateSpec`
        :param spec: Specification for setting up the namespace template.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the Supervisor doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors, or if {link
            CreateSpec#storageSpecs} is empty, or if {link
            CreateSpec#resourceSpec} is not set with {term memory_limit}, {term
            cpu_limit}, {term storage_request_limit}, or if {link
            CreateSpec#networks} is not set with networks if the Supervisor
            hosting the namespaces uses VSPHERE_NETWORK as its network
            provider, or if {link CreateSpec#networks} is not empty if the
            Supervisor hosting the namespaces uses NSXT_CONTAINER_PLUGIN or
            NSXT_VPC as its network provider.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if a request arrives to create a second template or to grant access
            to a user or group from an external identity provider.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.SelfServiceManage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the namespace template with given name already exists.
        """
        return self._invoke('create_v2',
                            {
                            'supervisor': supervisor,
                            'spec': spec,
                            })

    def update(self,
               cluster,
               template,
               spec,
               ):
        """
        Updates a namespace template associated with cluster on which vSphere
        Namespaces are enabled in this vCenter Server. The specified
        configuration is applied partially and None fields in ``spec`` will
        leave those parts of configuration as-is. A Supervisor can be running
        on one or multiple vSphere Zones, and each vSphere Zone is associated
        with one or more vSphere Clusters. If a Supervisor running on the
        specified vSphere Cluster is running on additional vSphere Clusters,
        this operation will apply to Supervisor components running on the other
        vSphere Clusters in addition to the specified vSphere Cluster. To call
        this API on a Supervisor with multiple vSphere Clusters, use
        com.vmware.vcenter.namespace_management.supervisors.Topology#get to get
        the vSphere Clusters associated with the given Supervisor. Any cluster
        from the list returned can be used as the input of this API. This
        method was added in vSphere API 7.0.2.00100.

        :type  cluster: :class:`str`
        :param cluster: Identifier for cluster on which vSphere Namespaces are enabled.
            The parameter must be an identifier for the resource type:
            ``ClusterComputeResource``.
        :type  template: :class:`str`
        :param template: Name of the namespace template.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.NamespaceTemplate``.
        :type  spec: :class:`NamespaceTemplates.UpdateSpec`
        :param spec: Specification for updating the namespace template.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if ``cluster`` doesn't exist or if ``template`` doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.SelfServiceManage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if trying to grant access to a user or group from an external
            identity provider.
        """
        return self._invoke('update',
                            {
                            'cluster': cluster,
                            'template': template,
                            'spec': spec,
                            })

    def update_v2(self,
                  supervisor,
                  template,
                  spec,
                  ):
        """
        Updates a namespace template associated with a Supervisor. The
        specified configuration is applied partially and None fields in
        ``spec`` will leave those parts of configuration as-is. This method was
        added in vSphere API 8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: Identifier for the Supervisor.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  template: :class:`str`
        :param template: Name of the namespace template.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.NamespaceTemplate``.
        :type  spec: :class:`NamespaceTemplates.UpdateSpec`
        :param spec: Specification for updating the namespace template.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the Supervisor doesn't exist or if ``template`` doesn't exist.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.SelfServiceManage privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if trying to grant access to a user or group from an external
            identity provider.
        """
        return self._invoke('update_v2',
                            {
                            'supervisor': supervisor,
                            'template': template,
                            'spec': spec,
                            })
class Instances(VapiInterface):
    """
    The ``Instances`` class provides methods to create and delete a namespace
    object. In this version, an Instance is an abstraction around a Kubernetes
    namespace.
    """
    RESOURCE_TYPE = "com.vmware.vcenter.namespaces.Instance"
    """
    The resource type for namespace.

    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespaces.instances'
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

    class NetworkProvider(Enum):
        """
        Identifies the network plugin that networking functionalities for this
        vSphere Namespace. This enumeration was added in vSphere API 7.0.2.00100.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        NSXT_CONTAINER_PLUGIN = None
        """
        Network provider is NSX-T Container Plugin. This class attribute was added
        in vSphere API 7.0.2.00100.

        """
        VSPHERE_NETWORK = None
        """
        Network provider is vSphere Networking. This class attribute was added in
        vSphere API 7.0.2.00100.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`NetworkProvider` instance.
            """
            Enum.__init__(string)

    NetworkProvider._set_values({
        'NSXT_CONTAINER_PLUGIN': NetworkProvider('NSXT_CONTAINER_PLUGIN'),
        'VSPHERE_NETWORK': NetworkProvider('VSPHERE_NETWORK'),
    })
    NetworkProvider._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespaces.instances.network_provider',
        NetworkProvider))


    class LoadBalancerSize(Enum):
        """
        The ``Instances.LoadBalancerSize`` enumerates the kinds of load balancer
        sizes supported by NSX. Small load balancer can host 10 to 20 virtual
        servers depending on NSX-T version. Medium load balancer can host 100
        virtual servers. Large load balancer can host 1000 virtual servers. This
        enumeration was added in vSphere API 7.0.2.00100.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        SMALL = None
        """
        Load balancer size of 'small'. This class attribute was added in vSphere
        API 7.0.2.00100.

        """
        MEDIUM = None
        """
        Load balancer size of 'medium'. This class attribute was added in vSphere
        API 7.0.2.00100.

        """
        LARGE = None
        """
        Load balancer size of 'large'. This class attribute was added in vSphere
        API 7.0.2.00100.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`LoadBalancerSize` instance.
            """
            Enum.__init__(string)

    LoadBalancerSize._set_values({
        'SMALL': LoadBalancerSize('SMALL'),
        'MEDIUM': LoadBalancerSize('MEDIUM'),
        'LARGE': LoadBalancerSize('LARGE'),
    })
    LoadBalancerSize._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespaces.instances.load_balancer_size',
        LoadBalancerSize))


    class ConfigStatus(Enum):
        """
        The ``Instances.ConfigStatus`` class describes the status of reaching the
        desired state configuration for the namespace.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        CONFIGURING = None
        """
        The configuration is being applied to the namespace.

        """
        REMOVING = None
        """
        The configuration is being removed and namespace is being deleted.

        """
        RUNNING = None
        """
        The namespace is configured correctly.

        """
        ERROR = None
        """
        Failed to apply the configuration to the namespace, user intervention
        needed.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ConfigStatus` instance.
            """
            Enum.__init__(string)

    ConfigStatus._set_values({
        'CONFIGURING': ConfigStatus('CONFIGURING'),
        'REMOVING': ConfigStatus('REMOVING'),
        'RUNNING': ConfigStatus('RUNNING'),
        'ERROR': ConfigStatus('ERROR'),
    })
    ConfigStatus._set_binding_type(type.EnumType(
        'com.vmware.vcenter.namespaces.instances.config_status',
        ConfigStatus))


    class Access(VapiStruct):
        """
        The ``Instances.Access`` class contains the access control information for
        a subject on a namespace.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     subject_type=None,
                     subject=None,
                     domain=None,
                     role=None,
                     identity_provider=None,
                    ):
            """
            :type  subject_type: :class:`Access.SubjectType`
            :param subject_type: Type of the subject.
            :type  subject: :class:`str`
            :param subject: Name of the subject.
            :type  domain: :class:`str`
            :param domain: Domain of the subject.
            :type  role: :class:`Access.Role`
            :param role: Role of the subject on the namespace instance.
            :type  identity_provider: :class:`str` or ``None``
            :param identity_provider: UUID of an external identity provider for the user, if any. Use
                this field if the user is coming from an external identity provider
                configured via the
                com.vmware.vcenter.namespace_management.supervisors.identity.Providers
                service. This attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``.
                If unset, vCenter Single Sign-On will be used as the identity
                provider.
            """
            self.subject_type = subject_type
            self.subject = subject
            self.domain = domain
            self.role = role
            self.identity_provider = identity_provider
            VapiStruct.__init__(self)


    Access._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.access', {
            'subject_type': type.ReferenceType(__name__, 'Access.SubjectType'),
            'subject': type.StringType(),
            'domain': type.StringType(),
            'role': type.ReferenceType(__name__, 'Access.Role'),
            'identity_provider': type.OptionalType(type.IdType()),
        },
        Access,
        False,
        None))


    class Principal(VapiStruct):
        """
        The ``Instances.Principal`` class contains the information about the
        creator of namespace. This class was added in vSphere API 7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     subject=None,
                     domain=None,
                    ):
            """
            :type  subject: :class:`str`
            :param subject: Name of the subject. This attribute was added in vSphere API
                7.0.2.00100.
            :type  domain: :class:`str`
            :param domain: Domain of the subject. This attribute was added in vSphere API
                7.0.2.00100.
            """
            self.subject = subject
            self.domain = domain
            VapiStruct.__init__(self)


    Principal._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.principal', {
            'subject': type.StringType(),
            'domain': type.StringType(),
        },
        Principal,
        False,
        None))


    class StorageSpec(VapiStruct):
        """
        The ``Instances.StorageSpec`` class contains the specification required to
        configure storage associated with a namespace. Information in this class
        will result in storage quotas on the Kubernetes namespace.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     policy=None,
                     limit=None,
                    ):
            """
            :type  policy: :class:`str`
            :param policy: ID of the storage policy. A Kubernetes storage class is created for
                this storage policy if it does not exist already.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``SpsStorageProfile``. When methods return a value of this class as
                a return value, the attribute will be an identifier for the
                resource type: ``SpsStorageProfile``.
            :type  limit: :class:`long` or ``None``
            :param limit: The maximum amount of storage (in mebibytes) which can be utilized
                by the namespace for this specification.
                If None, no limits are placed.
            """
            self.policy = policy
            self.limit = limit
            VapiStruct.__init__(self)


    StorageSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.storage_spec', {
            'policy': type.IdType(resource_types='SpsStorageProfile'),
            'limit': type.OptionalType(type.IntegerType()),
        },
        StorageSpec,
        False,
        None))


    class VMServiceSpec(VapiStruct):
        """
        The ``Instances.VMServiceSpec`` class contains the specification required
        to configure the VM Service specification associated with a namespace.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     content_libraries=None,
                     vm_classes=None,
                    ):
            """
            :type  content_libraries: :class:`set` of :class:`str` or ``None``
            :param content_libraries: Set of Content Libraries for use by the VM Service. The Content
                Libraries specified should exist in vSphere inventory. 
                
                The Content Libraries specified for the VM Image Service, using
                {CreateSpec#contentLibraries} during :func:`Instances.create`
                method or {UpdateSpec#contentLibraries} during
                :func:`Instances.update` method or {SetSpec#contentLibraries}
                during :func:`Instances.set` method will also be included in this
                list. 
                
                If the same Content Library is present both here and in VM Image
                Service specification, then: 
                
                * The Content Library is only surfaced to users once.
                * The settings in VM Image Service specification are honored.
                
                . This attribute was added in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.content.Library``. When methods return a value of this
                class as a return value, the attribute will contain identifiers for
                the resource type: ``com.vmware.content.Library``.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  vm_classes: :class:`set` of :class:`str` or ``None``
            :param vm_classes: Set of VirtualMachineClasses for use by the VM Service. The class
                names specified here should exist in vSphere inventory. If this
                field is empty in an updated specification, all
                VirtualMachineClasses that are currently associated with the
                namespace will be disassociated from it. 
                
                **NOTE:** Any change in virtual machine classes associated with the
                namespace will not impact existing VMs.. This attribute was added
                in vSphere API 7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.VirtualMachineClass``.
                When methods return a value of this class as a return value, the
                attribute will contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.VirtualMachineClass``.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.content_libraries = content_libraries
            self.vm_classes = vm_classes
            VapiStruct.__init__(self)


    VMServiceSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.VM_service_spec', {
            'content_libraries': type.OptionalType(type.SetType(type.IdType())),
            'vm_classes': type.OptionalType(type.SetType(type.IdType())),
        },
        VMServiceSpec,
        False,
        None))


    class ContentLibrarySpec(VapiStruct):
        """
        The ``Instances.ContentLibrarySpec`` class contains the specification
        required to configure Content Libraries in the VM Image Service. This class
        was added in vSphere API 8.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     content_library=None,
                     writable=None,
                    ):
            """
            :type  content_library: :class:`str`
            :param content_library: Content Library ID used by the VM Image Service. The Content
                Library specified should exist in vSphere inventory. This attribute
                was added in vSphere API 8.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.content.Library``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``com.vmware.content.Library``.
            :type  writable: :class:`bool` or ``None``
            :param writable: Flag to indicate if the Content Library is writable. When
                :class:`set` to ``true``, users with :attr:`Access.Info.role` of
                type OWNER or EDIT on a Supervisor namespace can add or delete
                Content Library items in vSphere from this Supervisor namespace. A
                subscribed Content Library is not allowed to be marked as writable.
                
                An InvalidArgument error will be thrown from
                :func:`Instances.create` method, :func:`Instances.update` method
                and :func:`Instances.set` method if a subscribed Content Library
                has the ``writable`` flag set to ``true``.. This attribute was
                added in vSphere API 8.0.2.0.
                If None, the value defaults to ``false`` and the Content Library is
                read-only to users.
            """
            self.content_library = content_library
            self.writable = writable
            VapiStruct.__init__(self)


    ContentLibrarySpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.content_library_spec', {
            'content_library': type.IdType(resource_types='com.vmware.content.Library'),
            'writable': type.OptionalType(type.BooleanType()),
        },
        ContentLibrarySpec,
        False,
        None))


    class Ipv4Cidr(VapiStruct):
        """
        The specification for representing CIDR notation of IP range. This class
        was added in vSphere API 7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     address=None,
                     prefix=None,
                    ):
            """
            :type  address: :class:`str`
            :param address: The IPv4 address. This attribute was added in vSphere API
                7.0.2.00100.
            :type  prefix: :class:`long`
            :param prefix: The CIDR prefix. This attribute was added in vSphere API
                7.0.2.00100.
            """
            self.address = address
            self.prefix = prefix
            VapiStruct.__init__(self)


    Ipv4Cidr._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.ipv4_cidr', {
            'address': type.StringType(),
            'prefix': type.IntegerType(),
        },
        Ipv4Cidr,
        False,
        None))


    class NetworkCreateSpec(VapiStruct):
        """
        The ``Instances.NetworkCreateSpec`` class contains the specification
        required to create a vSphere Namespaces network object. This class was
        added in vSphere API 7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'network_provider',
                {
                    'NSXT_CONTAINER_PLUGIN' : [('network', True)],
                    'VSPHERE_NETWORK' : [],
                }
            ),
        ]



        def __init__(self,
                     network_provider=None,
                     network=None,
                    ):
            """
            :type  network_provider: :class:`Instances.NetworkProvider`
            :param network_provider: The network provider that will manage the vSphere Namespaces
                network object. This attribute was added in vSphere API
                7.0.2.00100.
            :type  network: :class:`Instances.NsxNetworkCreateSpec`
            :param network: The create spec for an NSXT-backed Namespaces network
                configuration, supported by
                :attr:`Instances.NetworkProvider.NSXT_CONTAINER_PLUGIN` network
                provider. This attribute was added in vSphere API 7.0.2.00100.
                This attribute is optional and it is only relevant when the value
                of ``networkProvider`` is
                :attr:`Instances.NetworkProvider.NSXT_CONTAINER_PLUGIN`.
            """
            self.network_provider = network_provider
            self.network = network
            VapiStruct.__init__(self)


    NetworkCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.network_create_spec', {
            'network_provider': type.ReferenceType(__name__, 'Instances.NetworkProvider'),
            'network': type.OptionalType(type.ReferenceType(__name__, 'Instances.NsxNetworkCreateSpec')),
        },
        NetworkCreateSpec,
        False,
        None))


    class NsxNetworkCreateSpec(VapiStruct):
        """
        The ``Instances.NsxNetworkCreateSpec`` class describes the configuration
        specification of a NSXT-backed Namespaces Network configuration. This class
        was added in vSphere API 7.0.2.00100.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     namespace_network_cidrs=None,
                     ingress_cidrs=None,
                     egress_cidrs=None,
                     nsx_tier0_gateway=None,
                     subnet_prefix_length=None,
                     routed_mode=None,
                     load_balancer_size=None,
                    ):
            """
            :type  namespace_network_cidrs: :class:`list` of :class:`Instances.Ipv4Cidr` or ``None``
            :param namespace_network_cidrs: CIDR blocks from which Kubernetes allocates IP addresses for all
                workloads that attach to the namespace, including PodVMs, TKGS and
                VM Service VMs. This range should not overlap with those in
                :attr:`Instances.NsxNetworkCreateSpec.ingress_cidrs`,
                :attr:`Instances.NsxNetworkCreateSpec.egress_cidrs`, or other
                services running in the datacenter. This attribute was added in
                vSphere API 7.0.2.00100.
                This field is required when
                :attr:`Instances.NsxNetworkCreateSpec.nsx_tier0_gateway` or any of
                :attr:`Instances.NsxNetworkCreateSpec.ingress_cidrs`,
                :attr:`Instances.NsxNetworkCreateSpec.egress_cidrs` are specified.
                An update operation only allows for addition of new CIDR blocks to
                the existing list.
            :type  ingress_cidrs: :class:`list` of :class:`Instances.Ipv4Cidr` or ``None``
            :param ingress_cidrs: CIDR blocks from which NSX assigns IP addresses for Kubernetes
                Ingresses and Kubernetes Services of type LoadBalancer. These
                ranges should not overlap with those in
                :attr:`Instances.NsxNetworkCreateSpec.namespace_network_cidrs`,
                :attr:`Instances.NsxNetworkCreateSpec.egress_cidrs`, or other
                services running in the datacenter. This attribute was added in
                vSphere API 7.0.2.00100.
                This field is required when
                :attr:`Instances.NsxNetworkCreateSpec.nsx_tier0_gateway` or any of
                :attr:`Instances.NsxNetworkCreateSpec.namespace_network_cidrs`,
                :attr:`Instances.NsxNetworkCreateSpec.egress_cidrs` are specified.
                An update operation only allows for addition of new CIDR blocks to
                the existing list.
            :type  egress_cidrs: :class:`list` of :class:`Instances.Ipv4Cidr` or ``None``
            :param egress_cidrs: CIDR blocks from which NSX assigns IP addresses used for performing
                SNAT from container IPs to external IPs. These ranges should not
                overlap with those in
                :attr:`Instances.NsxNetworkCreateSpec.namespace_network_cidrs`,
                :attr:`Instances.NsxNetworkCreateSpec.ingress_cidrs`, or other
                services running in the datacenter. This attribute was added in
                vSphere API 7.0.2.00100.
                This field is required when
                :attr:`Instances.NsxNetworkCreateSpec.routed_mode` is set to False
                and :attr:`Instances.NsxNetworkCreateSpec.nsx_tier0_gateway` or any
                of :attr:`Instances.NsxNetworkCreateSpec.namespace_network_cidrs`,
                :attr:`Instances.NsxNetworkCreateSpec.ingress_cidrs` is specified.
                When :attr:`Instances.NsxNetworkCreateSpec.routed_mode` is set to
                True, this field is not allowed. An update operation only allows
                for addition of new CIDR blocks to the existing list.
            :type  nsx_tier0_gateway: :class:`str` or ``None``
            :param nsx_tier0_gateway: NSX Tier0 Gateway used for this namespace. This field does not
                allow update once applied. This attribute was added in vSphere API
                7.0.2.00100.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``NSXTier0Gateway``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``NSXTier0Gateway``.
                If None, cluster level settings specified in
                com.vmware.vcenter.namespace_management.Clusters.NCPClusterNetworkInfo#nsxTier0Gateway
                will be applied.
            :type  subnet_prefix_length: :class:`long` or ``None``
            :param subnet_prefix_length: Size of the subnet reserved for namespace segments. This attribute
                was added in vSphere API 7.0.2.00100.
                If None, cluster level settings specified in
                com.vmware.vcenter.namespace_management.Clusters.NCPClusterNetworkInfo#namespaceSubnetPrefix
                will be applied.
            :type  routed_mode: :class:`bool` or ``None``
            :param routed_mode: Routed mode for this namespace. When set to True, the traffic in
                the namespace is not NATed. This attribute was added in vSphere API
                7.0.2.00100.
                If None, defaults to False. When this field is set to True,
                :attr:`Instances.NsxNetworkCreateSpec.egress_cidrs` is not allowed.
                This field does not allow update once applied.
            :type  load_balancer_size: :class:`Instances.LoadBalancerSize` or ``None``
            :param load_balancer_size: The size of the NSX Load Balancer used by the namespace. This field
                does not allow update once applied. This attribute was added in
                vSphere API 7.0.2.00100.
                If None, defaults to :attr:`Instances.LoadBalancerSize.SMALL`.
            """
            self.namespace_network_cidrs = namespace_network_cidrs
            self.ingress_cidrs = ingress_cidrs
            self.egress_cidrs = egress_cidrs
            self.nsx_tier0_gateway = nsx_tier0_gateway
            self.subnet_prefix_length = subnet_prefix_length
            self.routed_mode = routed_mode
            self.load_balancer_size = load_balancer_size
            VapiStruct.__init__(self)


    NsxNetworkCreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.nsx_network_create_spec', {
            'namespace_network_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.Ipv4Cidr'))),
            'ingress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.Ipv4Cidr'))),
            'egress_cidrs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.Ipv4Cidr'))),
            'nsx_tier0_gateway': type.OptionalType(type.IdType()),
            'subnet_prefix_length': type.OptionalType(type.IntegerType()),
            'routed_mode': type.OptionalType(type.BooleanType()),
            'load_balancer_size': type.OptionalType(type.ReferenceType(__name__, 'Instances.LoadBalancerSize')),
        },
        NsxNetworkCreateSpec,
        False,
        None))


    class Message(VapiStruct):
        """
        The ``Instances.Message`` class contains the information about the object
        configuration.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     severity=None,
                     details=None,
                    ):
            """
            :type  severity: :class:`Instances.Message.MessageSeverity`
            :param severity: Type of the message.
            :type  details: :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param details: Details about the message.
                If None, message details are not required for taking actions.
            """
            self.severity = severity
            self.details = details
            VapiStruct.__init__(self)


        class MessageSeverity(Enum):
            """
            The ``Instances.Message.MessageSeverity`` class represents the severity of
            the message.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            INFO = None
            """
            Informational message. This may be accompanied by vCenter event.

            """
            WARNING = None
            """
            Warning message. This may be accompanied by vCenter event.

            """
            ERROR = None
            """
            Error message. This is accompanied by vCenter event and/or alarm.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`MessageSeverity` instance.
                """
                Enum.__init__(string)

        MessageSeverity._set_values({
            'INFO': MessageSeverity('INFO'),
            'WARNING': MessageSeverity('WARNING'),
            'ERROR': MessageSeverity('ERROR'),
        })
        MessageSeverity._set_binding_type(type.EnumType(
            'com.vmware.vcenter.namespaces.instances.message.message_severity',
            MessageSeverity))

    Message._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.message', {
            'severity': type.ReferenceType(__name__, 'Instances.Message.MessageSeverity'),
            'details': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        },
        Message,
        False,
        None))


    class Stats(VapiStruct):
        """
        The ``Instances.Stats`` class contains the basic runtime statistics about
        the namespace.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     cpu_used=None,
                     memory_used=None,
                     storage_used=None,
                    ):
            """
            :type  cpu_used: :class:`long`
            :param cpu_used: Overall CPU usage of the namespace, in MHz. This is the sum of CPU
                usage across all pods in the Kubernetes namespace.
            :type  memory_used: :class:`long`
            :param memory_used: Overall memory usage of the namespace (in mebibytes). This is the
                sum of memory usage across all pods.
            :type  storage_used: :class:`long`
            :param storage_used: Overall storage used by the namespace (in mebibytes). This is the
                sum of storage used by pods across all datastores in the cluster
                associated with storage policies configured for the namespace.
            """
            self.cpu_used = cpu_used
            self.memory_used = memory_used
            self.storage_used = storage_used
            VapiStruct.__init__(self)


    Stats._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.stats', {
            'cpu_used': type.IntegerType(),
            'memory_used': type.IntegerType(),
            'storage_used': type.IntegerType(),
        },
        Stats,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``Instances.Summary`` class contains the basic information about the
        namespace on a single vSphere cluster.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     cluster=None,
                     namespace=None,
                     description=None,
                     config_status=None,
                     stats=None,
                     self_service_namespace=None,
                    ):
            """
            :type  cluster: :class:`str`
            :param cluster: Identifier for the vSphere cluster hosting the namespace.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            :type  namespace: :class:`str`
            :param namespace: Identifier of the namespace.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``. When methods return a
                value of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``.
            :type  description: :class:`str`
            :param description: Description of the namespace.
            :type  config_status: :class:`Instances.ConfigStatus`
            :param config_status: Current setting for ``Instances.ConfigStatus``.
            :type  stats: :class:`Instances.Stats`
            :param stats: Basic runtime statistics for the namespace.
            :type  self_service_namespace: :class:`bool` or ``None``
            :param self_service_namespace: Flag to indicate the self service namespace. This attribute was
                added in vSphere API 7.0.2.00100.
                If None, the namespace is not marked as self service namespace.
            """
            self.cluster = cluster
            self.namespace = namespace
            self.description = description
            self.config_status = config_status
            self.stats = stats
            self.self_service_namespace = self_service_namespace
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.summary', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'description': type.StringType(),
            'config_status': type.ReferenceType(__name__, 'Instances.ConfigStatus'),
            'stats': type.ReferenceType(__name__, 'Instances.Stats'),
            'self_service_namespace': type.OptionalType(type.BooleanType()),
        },
        Summary,
        False,
        None))


    class SummaryV2(VapiStruct):
        """
        The ``Instances.SummaryV2`` class contains the basic information about the
        namespace on a Supervisor. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor=None,
                     namespace=None,
                     description=None,
                     config_status=None,
                     stats=None,
                     self_service_namespace=None,
                    ):
            """
            :type  supervisor: :class:`str`
            :param supervisor: Identifier for the Supervisor hosting the namespace. This attribute
                was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
            :type  namespace: :class:`str`
            :param namespace: Identifier of the namespace.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``. When methods return a
                value of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``.
            :type  description: :class:`str`
            :param description: Description of the namespace.
            :type  config_status: :class:`Instances.ConfigStatus`
            :param config_status: Current setting for ``Instances.ConfigStatus``.
            :type  stats: :class:`Instances.Stats`
            :param stats: Basic runtime statistics for the namespace.
            :type  self_service_namespace: :class:`bool` or ``None``
            :param self_service_namespace: Flag to indicate the self service namespace. This attribute was
                added in vSphere API 7.0.2.00100.
                If None, the namespace is not marked as self service namespace.
            """
            self.supervisor = supervisor
            self.namespace = namespace
            self.description = description
            self.config_status = config_status
            self.stats = stats
            self.self_service_namespace = self_service_namespace
            VapiStruct.__init__(self)


    SummaryV2._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.summary_v2', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'description': type.StringType(),
            'config_status': type.ReferenceType(__name__, 'Instances.ConfigStatus'),
            'stats': type.ReferenceType(__name__, 'Instances.Stats'),
            'self_service_namespace': type.OptionalType(type.BooleanType()),
        },
        SummaryV2,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Instances.Info`` class contains the detailed information about the
        namespace on a single vSphere cluster.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     cluster=None,
                     config_status=None,
                     messages=None,
                     stats=None,
                     description=None,
                     resource_spec=None,
                     access_list=None,
                     storage_specs=None,
                     networks=None,
                     vm_service_spec=None,
                     content_libraries=None,
                     creator=None,
                     self_service_namespace=None,
                    ):
            """
            :type  cluster: :class:`str`
            :param cluster: Identifier for the vSphere cluster hosting the namespace.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            :type  config_status: :class:`Instances.ConfigStatus`
            :param config_status: Current setting for ``Instances.ConfigStatus``.
            :type  messages: :class:`list` of :class:`Instances.Message`
            :param messages: Current set of messages associated with the object.
            :type  stats: :class:`Instances.Stats`
            :param stats: Basic runtime statistics for the namespace.
            :type  description: :class:`str`
            :param description: Description of the namespace.
            :type  resource_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param resource_spec: Quotas on the namespace resources. Refer to
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions#get
                for the type of the value for this field.
                If None, no resource constraints are associated with the namespace.
            :type  access_list: :class:`list` of :class:`Instances.Access`
            :param access_list: Access controls associated with the namespace.
            :type  storage_specs: :class:`list` of :class:`Instances.StorageSpec`
            :param storage_specs: Storage associated with the namespace.
            :type  networks: :class:`list` of :class:`str` or ``None``
            :param networks: The vSphere Networks associated with the namespace. This attribute
                was added in vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``.
                This field is None if the cluster hosting this namespace uses
                NSXT_CONTAINER_PLUGIN or NSXT_VPC as its network provider.
            :type  vm_service_spec: :class:`Instances.VMServiceSpec`
            :param vm_service_spec: VM Service specification associated with the namespace. This
                attribute was added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  content_libraries: :class:`list` of :class:`Instances.ContentLibrarySpec` or ``None``
            :param content_libraries: List of Content Libraries used by the VM Image Service. This list
                refers to existing Content Libraries in vSphere inventory. 
                
                The Content Libraries specified in {VMServiceSpec#contentLibraries}
                will also be included in this list but will be read-only by default
                to users. 
                
                If the same Content Library is present both here and in
                {VMServiceSpec#contentLibraries}, then: 
                
                * The Content Library is only surfaced to users once.
                * The settings here are honored.
                
                . This attribute was added in vSphere API 8.0.2.0.
                If None, no Content Libraries are configured for the VM Image
                Service.
            :type  creator: :class:`Instances.Principal` or ``None``
            :param creator: Creator of the namespace. Namespace self-service uses this field to
                populate the user who created this namespace. This attribute was
                added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  self_service_namespace: :class:`bool` or ``None``
            :param self_service_namespace: Flag to indicate the self service namespace. This attribute was
                added in vSphere API 7.0.2.00100.
                If None, the namespace is not marked as self service namespace.
            """
            self.cluster = cluster
            self.config_status = config_status
            self.messages = messages
            self.stats = stats
            self.description = description
            self.resource_spec = resource_spec
            self.access_list = access_list
            self.storage_specs = storage_specs
            self.networks = networks
            self.vm_service_spec = vm_service_spec
            self.content_libraries = content_libraries
            self.creator = creator
            self.self_service_namespace = self_service_namespace
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.info', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'config_status': type.ReferenceType(__name__, 'Instances.ConfigStatus'),
            'messages': type.ListType(type.ReferenceType(__name__, 'Instances.Message')),
            'stats': type.ReferenceType(__name__, 'Instances.Stats'),
            'description': type.StringType(),
            'resource_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
            'access_list': type.ListType(type.ReferenceType(__name__, 'Instances.Access')),
            'storage_specs': type.ListType(type.ReferenceType(__name__, 'Instances.StorageSpec')),
            'networks': type.OptionalType(type.ListType(type.IdType())),
            'vm_service_spec': type.OptionalType(type.ReferenceType(__name__, 'Instances.VMServiceSpec')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.ContentLibrarySpec'))),
            'creator': type.OptionalType(type.ReferenceType(__name__, 'Instances.Principal')),
            'self_service_namespace': type.OptionalType(type.BooleanType()),
        },
        Info,
        False,
        None))


    class InfoV2(VapiStruct):
        """
        The ``Instances.InfoV2`` class contains the detailed information about the
        namespace on a Supervisor. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor=None,
                     config_status=None,
                     messages=None,
                     stats=None,
                     description=None,
                     resource_spec=None,
                     access_list=None,
                     storage_specs=None,
                     networks=None,
                     vm_service_spec=None,
                     content_libraries=None,
                     creator=None,
                     self_service_namespace=None,
                    ):
            """
            :type  supervisor: :class:`str`
            :param supervisor: Identifier for the Supervisor hosting the namespace. This attribute
                was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
            :type  config_status: :class:`Instances.ConfigStatus`
            :param config_status: Current setting for ``Instances.ConfigStatus``.
            :type  messages: :class:`list` of :class:`Instances.Message`
            :param messages: Current set of messages associated with the object.
            :type  stats: :class:`Instances.Stats`
            :param stats: Basic runtime statistics for the namespace.
            :type  description: :class:`str`
            :param description: Description of the namespace.
            :type  resource_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param resource_spec: Quotas on the namespace resources. Refer to
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions#get
                for the type of the value for this field.
                If None, no resource constraints are associated with the namespace.
            :type  access_list: :class:`list` of :class:`Instances.Access`
            :param access_list: Access controls associated with the namespace.
            :type  storage_specs: :class:`list` of :class:`Instances.StorageSpec`
            :param storage_specs: Storage associated with the namespace.
            :type  networks: :class:`list` of :class:`str` or ``None``
            :param networks: The vSphere Networks associated with the namespace. This attribute
                was added in vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``.
                This field is None if the cluster hosting this namespace uses
                NSXT_CONTAINER_PLUGIN or NSXT_VPC as its network provider.
            :type  vm_service_spec: :class:`Instances.VMServiceSpec`
            :param vm_service_spec: VM Service specification associated with the namespace. This
                attribute was added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  content_libraries: :class:`list` of :class:`Instances.ContentLibrarySpec` or ``None``
            :param content_libraries: List of Content Libraries used by the VM Image Service. This list
                refers to existing Content Libraries in vSphere inventory. 
                
                The Content Libraries specified in {VMServiceSpec#contentLibraries}
                will also be included in this list but will be read-only by default
                to users. 
                
                If the same Content Library is present both here and in
                {VMServiceSpec#contentLibraries}, then: 
                
                * The Content Library is only surfaced to users once.
                * The settings here are honored.
                
                . This attribute was added in vSphere API 8.0.2.0.
                If None, no Content Libraries are configured for the VM Image
                Service.
            :type  creator: :class:`Instances.Principal` or ``None``
            :param creator: Creator of the namespace. Namespace self-service uses this field to
                populate the user who created this namespace. This attribute was
                added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  self_service_namespace: :class:`bool` or ``None``
            :param self_service_namespace: Flag to indicate the self service namespace. This attribute was
                added in vSphere API 7.0.2.00100.
                If None, the namespace is not marked as self service namespace.
            """
            self.supervisor = supervisor
            self.config_status = config_status
            self.messages = messages
            self.stats = stats
            self.description = description
            self.resource_spec = resource_spec
            self.access_list = access_list
            self.storage_specs = storage_specs
            self.networks = networks
            self.vm_service_spec = vm_service_spec
            self.content_libraries = content_libraries
            self.creator = creator
            self.self_service_namespace = self_service_namespace
            VapiStruct.__init__(self)


    InfoV2._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.info_v2', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'config_status': type.ReferenceType(__name__, 'Instances.ConfigStatus'),
            'messages': type.ListType(type.ReferenceType(__name__, 'Instances.Message')),
            'stats': type.ReferenceType(__name__, 'Instances.Stats'),
            'description': type.StringType(),
            'resource_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
            'access_list': type.ListType(type.ReferenceType(__name__, 'Instances.Access')),
            'storage_specs': type.ListType(type.ReferenceType(__name__, 'Instances.StorageSpec')),
            'networks': type.OptionalType(type.ListType(type.IdType())),
            'vm_service_spec': type.OptionalType(type.ReferenceType(__name__, 'Instances.VMServiceSpec')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.ContentLibrarySpec'))),
            'creator': type.OptionalType(type.ReferenceType(__name__, 'Instances.Principal')),
            'self_service_namespace': type.OptionalType(type.BooleanType()),
        },
        InfoV2,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``Instances.UpdateSpec`` class contains the specification required to
        update the configuration on the namespace. This class is applied partially,
        and only the specified fields will replace or modify their existing
        counterparts.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     description=None,
                     resource_spec=None,
                     access_list=None,
                     storage_specs=None,
                     vm_service_spec=None,
                     content_libraries=None,
                    ):
            """
            :type  description: :class:`str` or ``None``
            :param description: Description for the namespace.
                If None, the description of the namespace will not be modified.
            :type  resource_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param resource_spec: Resource quota updates on the namespace. Refer to
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions.Info#updateResourceQuotaType
                and use
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions#get
                for retrieving the type for the value for this field. For an
                example of this, see :class:`ResourceQuotaOptionsV1Update`.
                If None, the resource constraints on the namespace will not be
                modified.
            :type  access_list: :class:`list` of :class:`Instances.Access` or ``None``
            :param access_list: Access control associated with the namespace.
                If None, access controls on the namespace will not be modified.
                Existing pods from users will continue to run.
            :type  storage_specs: :class:`list` of :class:`Instances.StorageSpec` or ``None``
            :param storage_specs: Storage associated with the namespace.
                If None, storage policies and their limit will not be modified.
                Pods which are already using persistent storage from the earlier
                version of storage policies will be able to access them till the
                datastores are attached to the worker nodes.
            :type  vm_service_spec: :class:`Instances.VMServiceSpec` or ``None``
            :param vm_service_spec: VM Service specification associated with the namespace. 
                
                **NOTE:** Any change in the VM Service Content Libraries associated
                with the namespace will be updated and merged with the the Content
                Library list in VM Image Service. If {UpdateSpec#contentLibraries}
                is unset, the Content Libraries specified here will be honored if
                no writable Content Libraries are removed from the current Content
                Library list by :func:`Instances.get` method, otherwise
                InvalidArgument error will be thrown.. This attribute was added in
                vSphere API 7.0.2.00100.
                If None, the Content Libraries get configured based on the values
                in {UpdateSpec#contentLibraries}, if it is specified.
            :type  content_libraries: :class:`list` of :class:`Instances.ContentLibrarySpec` or ``None``
            :param content_libraries: List of Content Libraries used by the VM Image Service. This list
                refers to existing Content Libraries in vSphere inventory. 
                
                The Content Libraries specified in {VMServiceSpec#contentLibraries}
                will also be included in this list but will be read-only by default
                to users. 
                
                If the same Content Library is present both here and in
                {VMServiceSpec#contentLibraries}, then: 
                
                * The Content Library is only surfaced to users once.
                * The settings here are honored.
                
                
                
                **NOTE:** Any change in the VM Image Service Content Libraries
                associated with the namespace will be updated and merged with the
                Content Library list in ``Instances.VMServiceSpec``. If
                {UpdateSpec#vmServiceSpec#contentLibraries} is unset, the Content
                Libraries specified here will be honored and the Content Libraries
                removed from the current Content Library list by
                :func:`Instances.get` method will also be removed from VM Service..
                This attribute was added in vSphere API 8.0.2.0.
                If None, the Content Libraries get configured based on the values
                in {UpdateSpec#vmServiceSpec#contentLibraries}, if it is specified.
            """
            self.description = description
            self.resource_spec = resource_spec
            self.access_list = access_list
            self.storage_specs = storage_specs
            self.vm_service_spec = vm_service_spec
            self.content_libraries = content_libraries
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.update_spec', {
            'description': type.OptionalType(type.StringType()),
            'resource_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
            'access_list': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.Access'))),
            'storage_specs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.StorageSpec'))),
            'vm_service_spec': type.OptionalType(type.ReferenceType(__name__, 'Instances.VMServiceSpec')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.ContentLibrarySpec'))),
        },
        UpdateSpec,
        False,
        None))


    class SetSpec(VapiStruct):
        """
        The ``Instances.SetSpec`` class contains the specification required to set
        a new configuration on the namespace. This class is applied in entirety,
        replacing the current specification fully.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     description=None,
                     resource_spec=None,
                     access_list=None,
                     storage_specs=None,
                     vm_service_spec=None,
                     content_libraries=None,
                    ):
            """
            :type  description: :class:`str` or ``None``
            :param description: Description for the namespace.
                If None, the description of the namespace will be cleared.
            :type  resource_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param resource_spec: Resource quota for the namespace. This will replace the existing
                resource constraints on the namespace in entirety. Refer to
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions.Info#createResourceQuotaType
                and use
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions#get
                for retrieving the type for the value for this field. For an
                example of this, see :class:`ResourceQuotaOptionsV1`.
                If None, the resource constraints on the namespace will be cleared.
            :type  access_list: :class:`list` of :class:`Instances.Access` or ``None``
            :param access_list: Access control associated with the namespace.
                If None, the existing access controls on the namespace will be
                removed and users will not be able to access this namespace to
                create new pods. Existing pods from users will continue to run.
            :type  storage_specs: :class:`list` of :class:`Instances.StorageSpec` or ``None``
            :param storage_specs: Storage associated with the namespace.
                If None, the existing storage policies will be disassociated with
                the namespace and existing limits will be cleared. Pods which are
                already using persistent storage from the earlier version of
                storage policies will be able to access them till the datastores
                are attached to the worker nodes.
            :type  vm_service_spec: :class:`Instances.VMServiceSpec` or ``None``
            :param vm_service_spec: VM Service specification associated with the namespace. This
                attribute was added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  content_libraries: :class:`list` of :class:`Instances.ContentLibrarySpec` or ``None``
            :param content_libraries: List of Content Libraries used by the VM Image Service. This list
                refers to existing Content Libraries in vSphere inventory. 
                
                The Content Libraries specified in {VMServiceSpec#contentLibraries}
                will also be included in this list but will be read-only by default
                to users. 
                
                If the same Content Library is present both here and in
                {VMServiceSpec#contentLibraries}, then: 
                
                * The Content Library is only surfaced to users once.
                * The settings here are honored.
                
                . This attribute was added in vSphere API 8.0.2.0.
                If None, the existing Content Libraries configured for the VM Image
                Service will be removed.
            """
            self.description = description
            self.resource_spec = resource_spec
            self.access_list = access_list
            self.storage_specs = storage_specs
            self.vm_service_spec = vm_service_spec
            self.content_libraries = content_libraries
            VapiStruct.__init__(self)


    SetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.set_spec', {
            'description': type.OptionalType(type.StringType()),
            'resource_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
            'access_list': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.Access'))),
            'storage_specs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.StorageSpec'))),
            'vm_service_spec': type.OptionalType(type.ReferenceType(__name__, 'Instances.VMServiceSpec')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.ContentLibrarySpec'))),
        },
        SetSpec,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``Instances.CreateSpec`` class contains the specification required to
        set up a namespace on a single vSphere cluster.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     cluster=None,
                     namespace=None,
                     description=None,
                     resource_spec=None,
                     access_list=None,
                     storage_specs=None,
                     networks=None,
                     vm_service_spec=None,
                     content_libraries=None,
                     creator=None,
                     namespace_network=None,
                    ):
            """
            :type  cluster: :class:`str`
            :param cluster: Identifier of the cluster on which the namespace is being created.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will be an identifier for
                the resource type: ``ClusterComputeResource``.
            :type  namespace: :class:`str`
            :param namespace: Identifier of the namespace. This has DNS_LABEL restrictions as
                specified in ` <https://tools.ietf.org/html/rfc1123>`_. This must
                be an alphanumeric (a-z and 0-9) string and with maximum length of
                63 characters and with the '-' character allowed anywhere except
                the first or last character. This name is unique across all
                Namespaces in this vCenter server. In this version, this maps to
                the name of a Kubernetes namespace.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``. When methods return a
                value of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``.
            :type  description: :class:`str` or ``None``
            :param description: Description for the namespace.
                If None, no description is added to the namespace.
            :type  resource_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param resource_spec: Resource quota on the namespace. Refer to
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions.Info#createResourceQuotaType
                and use
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions#get
                for retrieving the type for the value for this field. For an
                example of this, see :class:`ResourceQuotaOptionsV1`.
                If None, no resource limits will be set on the namespace.
            :type  access_list: :class:`list` of :class:`Instances.Access` or ``None``
            :param access_list: Access controls associated with the namespace.
                If None, only users with Administrator role can access the
                namespace.
            :type  storage_specs: :class:`list` of :class:`Instances.StorageSpec` or ``None``
            :param storage_specs: Storage associated with the namespace.
                If None, storage policies will not be associated with the namespace
                which will prevent users from being able to provision pods with
                persistent storage on the namespace. Users will be able to
                provision pods which use local storage.
            :type  networks: :class:`list` of :class:`str` or ``None``
            :param networks: The vSphere Namespaces network objects to be associated with the
                namespace. The values of this list need to reference names of
                pre-existing
                ``com.vmware.vcenter.namespace_management.Networks.Info`` classs.
                This attribute was added in vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``.
                The field must be left None if the cluster hosting the namespace
                uses NSXT_CONTAINER_PLUGIN or NSXT_VPC as the network provider,
                since the network(s) for this namespace will be managed on NSX-T. 
                
                When using NSXT_CONTAINER_PLUGIN as network provider, a new network
                dedicated to the namespace will be created as part of namespace
                creation to override cluster network configs if
                :class:`Instances.NsxNetworkCreateSpec` is :class:`set`.  
                
                If the field is None when the cluster hosting the namespace uses
                VSPHERE_NETWORK as its network provider, the namespace will
                automatically be associated with the cluster's Supervisor Primary
                Workload Network. The field currently accepts at most only 1
                vSphere Namespaces network object reference.
            :type  vm_service_spec: :class:`Instances.VMServiceSpec` or ``None``
            :param vm_service_spec: VM Service specification associated with the namespace. This
                attribute was added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  content_libraries: :class:`list` of :class:`Instances.ContentLibrarySpec` or ``None``
            :param content_libraries: List of Content Libraries used by the VM Image Service. This list
                refers to existing Content Libraries in vSphere inventory. 
                
                The Content Libraries specified in {VMServiceSpec#contentLibraries}
                will also be used by the VM Image Service but will be read-only by
                default to users. 
                
                If the same Content Library is present both here and in
                {VMServiceSpec#contentLibraries}, then: 
                
                * The Content Library is only surfaced to users once.
                * The settings here are honored.
                
                . This attribute was added in vSphere API 8.0.2.0.
                If None, no additional Content Libraries will be configured for the
                VM Image Service except for the Content Libraries specified in
                {VMServiceSpec#contentLibraries}.
            :type  creator: :class:`Instances.Principal` or ``None``
            :param creator: Creator of the namespace. Namespace self-service uses this field to
                populate the user who created this namespace. This attribute was
                added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  namespace_network: :class:`Instances.NetworkCreateSpec` or ``None``
            :param namespace_network: This field that accepts parameters to define a vSphere Namespace
                Network object that will automatically be associated with this
                Namespace. Networks created in this operation will be given an
                autogenerated ID and cannot be referenced by other Namespaces. This
                attribute was added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.cluster = cluster
            self.namespace = namespace
            self.description = description
            self.resource_spec = resource_spec
            self.access_list = access_list
            self.storage_specs = storage_specs
            self.networks = networks
            self.vm_service_spec = vm_service_spec
            self.content_libraries = content_libraries
            self.creator = creator
            self.namespace_network = namespace_network
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.create_spec', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'description': type.OptionalType(type.StringType()),
            'resource_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
            'access_list': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.Access'))),
            'storage_specs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.StorageSpec'))),
            'networks': type.OptionalType(type.ListType(type.IdType())),
            'vm_service_spec': type.OptionalType(type.ReferenceType(__name__, 'Instances.VMServiceSpec')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.ContentLibrarySpec'))),
            'creator': type.OptionalType(type.ReferenceType(__name__, 'Instances.Principal')),
            'namespace_network': type.OptionalType(type.ReferenceType(__name__, 'Instances.NetworkCreateSpec')),
        },
        CreateSpec,
        False,
        None))


    class CreateSpecV2(VapiStruct):
        """
        The ``Instances.CreateSpecV2`` class contains the specification required to
        set up a namespace on a Supervisor cluster. This class was added in vSphere
        API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     supervisor=None,
                     namespace=None,
                     description=None,
                     resource_spec=None,
                     access_list=None,
                     storage_specs=None,
                     networks=None,
                     vm_service_spec=None,
                     content_libraries=None,
                     creator=None,
                     namespace_network=None,
                    ):
            """
            :type  supervisor: :class:`str`
            :param supervisor: Identifier for the sSupervisor hosting the namespace. This
                attribute was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
            :type  namespace: :class:`str`
            :param namespace: Identifier of the namespace. This has DNS_LABEL restrictions as
                specified in ` <https://tools.ietf.org/html/rfc1123>`_. This must
                be an alphanumeric (a-z and 0-9) string and with maximum length of
                63 characters and with the '-' character allowed anywhere except
                the first or last character. This name is unique across all
                Namespaces in this vCenter server. In this version, this maps to
                the name of a Kubernetes namespace.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``. When methods return a
                value of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.vcenter.namespaces.Instance``.
            :type  description: :class:`str` or ``None``
            :param description: Description for the namespace.
                If None, no description is added to the namespace.
            :type  resource_spec: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param resource_spec: Resource quota on the namespace. Refer to
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions.Info#createResourceQuotaType
                and use
                com.vmware.vcenter.namespace_management.NamespaceResourceOptions#get
                for retrieving the type for the value for this field. For an
                example of this, see :class:`ResourceQuotaOptionsV1`.
                If None, no resource limits will be set on the namespace.
            :type  access_list: :class:`list` of :class:`Instances.Access` or ``None``
            :param access_list: Access controls associated with the namespace.
                If None, only users with Administrator role can access the
                namespace.
            :type  storage_specs: :class:`list` of :class:`Instances.StorageSpec` or ``None``
            :param storage_specs: Storage associated with the namespace.
                If None, storage policies will not be associated with the namespace
                which will prevent users from being able to provision pods with
                persistent storage on the namespace. Users will be able to
                provision pods which use local storage.
            :type  networks: :class:`list` of :class:`str` or ``None``
            :param networks: The vSphere Namespaces network objects to be associated with the
                namespace. The values of this list need to reference names of
                pre-existing
                ``com.vmware.vcenter.namespace_management.Networks.Info`` classs.
                This attribute was added in vSphere API 7.0.1.0.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``. When methods
                return a value of this class as a return value, the attribute will
                contain identifiers for the resource type:
                ``com.vmware.vcenter.namespace_management.Network``.
                The field must be left None if the cluster hosting the namespace
                uses NSXT_CONTAINER_PLUGIN or NSXT_VPC as the network provider,
                since the network(s) for this namespace will be managed on NSX-T. 
                
                When using NSXT_CONTAINER_PLUGIN as network provider, a new network
                dedicated to the namespace will be created as part of namespace
                creation to override cluster network configs if
                :class:`Instances.NsxNetworkCreateSpec` is :class:`set`.  
                
                If the field is None when the cluster hosting the namespace uses
                VSPHERE_NETWORK as its network provider, the namespace will
                automatically be associated with the cluster's Supervisor Primary
                Workload Network. The field currently accepts at most only 1
                vSphere Namespaces network object reference.
            :type  vm_service_spec: :class:`Instances.VMServiceSpec` or ``None``
            :param vm_service_spec: VM Service specification associated with the namespace. This
                attribute was added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  content_libraries: :class:`list` of :class:`Instances.ContentLibrarySpec` or ``None``
            :param content_libraries: List of Content Libraries used by the VM Image Service. This list
                refers to existing Content Libraries in vSphere inventory. 
                
                The Content Libraries specified in {VMServiceSpec#contentLibraries}
                will also be used by the VM Image Service but will be read-only by
                default to users. 
                
                If the same Content Library is present both here and in
                {VMServiceSpec#contentLibraries}, then: 
                
                * The Content Library is only surfaced to users once.
                * The settings here are honored.
                
                . This attribute was added in vSphere API 8.0.2.0.
                If None, no additional Content Libraries will be configured for the
                VM Image Service except for the Content Libraries specified in
                {VMServiceSpec#contentLibraries}.
            :type  creator: :class:`Instances.Principal` or ``None``
            :param creator: Creator of the namespace. Namespace self-service uses this field to
                populate the user who created this namespace. This attribute was
                added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  namespace_network: :class:`Instances.NetworkCreateSpec` or ``None``
            :param namespace_network: This field that accepts parameters to define a vSphere Namespace
                Network object that will automatically be associated with this
                Namespace. Networks created in this operation will be given an
                autogenerated ID and cannot be referenced by other Namespaces. This
                attribute was added in vSphere API 7.0.2.00100.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.supervisor = supervisor
            self.namespace = namespace
            self.description = description
            self.resource_spec = resource_spec
            self.access_list = access_list
            self.storage_specs = storage_specs
            self.networks = networks
            self.vm_service_spec = vm_service_spec
            self.content_libraries = content_libraries
            self.creator = creator
            self.namespace_network = namespace_network
            VapiStruct.__init__(self)


    CreateSpecV2._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.create_spec_v2', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'description': type.OptionalType(type.StringType()),
            'resource_spec': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
            'access_list': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.Access'))),
            'storage_specs': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.StorageSpec'))),
            'networks': type.OptionalType(type.ListType(type.IdType())),
            'vm_service_spec': type.OptionalType(type.ReferenceType(__name__, 'Instances.VMServiceSpec')),
            'content_libraries': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Instances.ContentLibrarySpec'))),
            'creator': type.OptionalType(type.ReferenceType(__name__, 'Instances.Principal')),
            'namespace_network': type.OptionalType(type.ReferenceType(__name__, 'Instances.NetworkCreateSpec')),
        },
        CreateSpecV2,
        False,
        None))


    class RegisterVMSpec(VapiStruct):
        """
        The ``Instances.RegisterVMSpec`` class contains the specification required
        to register a virtual machine with Supervisor. This class was added in
        vSphere API 8.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     vm=None,
                    ):
            """
            :type  vm: :class:`str`
            :param vm: Identifier for the virtual machine being registered with
                Supervisor. This attribute was added in vSphere API 8.0.3.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``VirtualMachine``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``VirtualMachine``.
            """
            self.vm = vm
            VapiStruct.__init__(self)


    RegisterVMSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespaces.instances.register_VM_spec', {
            'vm': type.IdType(resource_types='VirtualMachine'),
        },
        RegisterVMSpec,
        False,
        None))



    def create(self,
               spec,
               ):
        """
        Create a namespace object on a single vSphere cluster.

        :type  spec: :class:`Instances.CreateSpec`
        :param spec: The specification for setting up the namespace.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if a namespace with the same name exists in vCenter server.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors or if an invalid name is specified.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the associated Supervisor cluster is being disabled or if the
            associated Supervisor cluster is being restored from a backup. When
            a Supervisor cluster is restored, there's a window of time during
            which the restored Supervisor cluster's state is being synchronized
            back to vCenter. During that time, namespace creation is not
            allowed.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if :attr:`Instances.CreateSpec.cluster` is not registered on this
            vCenter server.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if:attr:`Instances.CreateSpec.cluster` is not enabled for
            Namespaces, or if the networks field is set when the
            :attr:`Instances.CreateSpec.cluster` hosting the namespace uses
            NSXT_CONTAINER_PLUGIN or NSXT_VPC as its network provider, or if
            the Supervisor cluster does not support customizable VM classes.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Configure privilege or the
            namespace identifier begins with "vmware-system" prefix.
        """
        return self._invoke('create',
                            {
                            'spec': spec,
                            })

    def create_v2(self,
                  spec,
                  ):
        """
        Create a namespace object on a Supervisor. This method was added in
        vSphere API 8.0.0.1.

        :type  spec: :class:`Instances.CreateSpecV2`
        :param spec: The specification for setting up the namespace.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if a namespace with the same name exists in vCenter server.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contains any errors or if an invalid name is specified.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the associated Supervisor is being disabled or if the associated
            Supervisor is being restored from a backup. When a Supervisor is
            restored, there's a window of time during which the restored
            Supervisor's state is being synchronized back to vCenter. During
            that time, namespace creation is not allowed.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the Supervisor is not registered on this vCenter server.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the Supervisor is not enabled for Namespaces, or if the networks
            field is set when the Supervisor hosting the namespace uses
            NSXT_CONTAINER_PLUGIN or NSXT_VPC as its network provider, or if
            the Supervisor does not support customizable VM classes.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Configure privilege or the
            namespace identifier begins with "vmware-system" prefix.
        """
        return self._invoke('create_v2',
                            {
                            'spec': spec,
                            })

    def delete(self,
               namespace,
               ):
        """
        Delete the namespace object in the cluster.

        :type  namespace: :class:`str`
        :param namespace: Identifier for the namespace.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.Instance``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the associated Supervisor cluster is being restored from a
            backup. When a Supervisor cluster is restored, there's a window of
            time during which the restored Supervisor cluster's state is being
            synchronized back to vCenter. During that time, namespace deletion
            is not allowed.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the specified namespace could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Configure privilege or the
            namespace identifier begins with "vmware-system" prefix.
        """
        return self._invoke('delete',
                            {
                            'namespace': namespace,
                            })

    def get(self,
            namespace,
            ):
        """
        Returns information about a specific namespace on a single vSphere
        cluster.

        :type  namespace: :class:`str`
        :param namespace: Identifier for the namespace.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.Instance``.
        :rtype: :class:`Instances.Info`
        :return: Information about the desired state of the specified namespace.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if namespace could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get',
                            {
                            'namespace': namespace,
                            })

    def get_v2(self,
               namespace,
               ):
        """
        Returns information about a specific namespace on a Supervisor. This
        method was added in vSphere API 8.0.0.1.

        :type  namespace: :class:`str`
        :param namespace: Identifier for the namespace.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.Instance``.
        :rtype: :class:`Instances.InfoV2`
        :return: Information about the desired state of the specified namespace on a
            Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if namespace could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('get_v2',
                            {
                            'namespace': namespace,
                            })

    def list(self):
        """
        Returns the information about all namespaces in this vCenter Server.
        The information is tied to a single vSphere cluster.


        :rtype: :class:`list` of :class:`Instances.Summary`
        :return: Information about all namespaces in this vCenter server.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list', None)

    def list_v2(self):
        """
        Returns the information about all namespaces in this vCenter Server.
        The information is tied to a Supervisor. This method was added in
        vSphere API 8.0.0.1.


        :rtype: :class:`list` of :class:`Instances.SummaryV2`
        :return: Information about all namespaces in this vCenter server.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have System.Read privilege.
        """
        return self._invoke('list_v2', None)

    def set(self,
            namespace,
            spec,
            ):
        """
        Set a new configuration on the namespace object. The specified
        configuration is applied in entirety and will replace the current
        configuration fully.

        :type  namespace: :class:`str`
        :param namespace: Identifier for the namespace.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.Instance``.
        :type  spec: :class:`Instances.SetSpec`
        :param spec: New specification for the namespace.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the namespace is marked for deletion or if the associated
            Supervisor cluster is being disabled or if the associated
            Supervisor cluster is being restored from a backup. When a
            Supervisor cluster is restored, there's a window of time during
            which the restored Supervisor cluster's state is being synchronized
            back to vCenter. During that time, namespace configuration
            modifications are not allowed.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if namespace with the name ``namespace`` could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Configure privilege or the
            namespace identifier begins with "vmware-system" prefix.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if customizable VM classes are not supported for this Supervisor
            cluster.
        """
        return self._invoke('set',
                            {
                            'namespace': namespace,
                            'spec': spec,
                            })

    def update(self,
               namespace,
               spec,
               ):
        """
        Update the namespace object. The specified configuration is applied
        partially and None fields in ``spec`` will leave those parts of
        configuration as-is.

        :type  namespace: :class:`str`
        :param namespace: Identifier for the namespace.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.Instance``.
        :type  spec: :class:`Instances.UpdateSpec`
        :param spec: Specification for updating the namespace.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``spec`` contain any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the namespace is marked for deletion or if the associated
            Supervisor cluster is being disabled or if the associated
            Supervisor cluster is being restored from a backup. When a
            Supervisor cluster is restored, there's a window of time during
            which the restored Supervisor cluster's state is being synchronized
            back to vCenter. During that time, namespace configuration
            modifications are not allowed.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if namespace with the name ``namespace`` could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Configure privilege or the
            namespace identifier begins with "vmware-system" prefix.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if customizable VM classes are not supported for this Supervisor
            cluster.
        """
        return self._invoke('update',
                            {
                            'namespace': namespace,
                            'spec': spec,
                            })

    def register_vm(self,
                    namespace,
                    spec,
                    ):
        """
        Register an existing virtual machine as VM Service managed VM. 
        
        This API reads data stored in a VM's ExtraConfig to create a Kubernetes
        resource that may be used to lifecycle manage the VM. This process may
        also result in the creation of a Secret or ConfigMap resource for the
        VM's bootstrap data. Finally, a PersistentVolumeClaim resource may be
        created for each of the first-class disks attached to the VM. 
        
        This API triggers a non-cancellable task and returns its identifier
        which can be queried by calling the cis Tasks get method. The task is
        retained as per the default retention rules configured in vCenter. 
        
        This is a non-idempotent API that creates custom resources on the
        Supervisor as a side effect. If the API returns an error VI admin might
        need to manually address them before attempting registration again..
        This method was added in vSphere API 8.0.3.0.

        :type  namespace: :class:`str`
        :param namespace: Identifier for the namespace.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespaces.Instance``.
        :type  spec: :class:`Instances.RegisterVMSpec`
        :param spec: Specification for registering the virtual machine.
        :rtype: :class:`str`
        :return: The task identifier for the register operation.
            The return value will be an identifier for the resource type:
            ``com.vmware.cis.task``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if namespace with the name ``namespace`` or virtual machine with
            the ``spec`` could not be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the specified virtual machine is invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user does not have Namespaces.Configure privilege.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the Supervisor does not support registering a virtual machine as
            VM Service managed VM.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyInDesiredState` 
            if the custom resource corresponding to the requested virtual
            machine already exists on Supervisor.
        """
        return self._invoke('register_VM',
                            {
                            'namespace': namespace,
                            'spec': spec,
                            })
class _AccessStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'domain': type.StringType(),
            'subject': type.StringType(),
            'type': type.ReferenceType(__name__, 'Access.SubjectType'),
            'spec': type.ReferenceType(__name__, 'Access.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespaces/instances/{namespace}/access/{domain}/{subject}',
            request_body_parameter='spec',
            path_variables={
                'namespace': 'namespace',
                'domain': 'domain',
                'subject': 'subject',
            },
            query_parameters={
                'type': 'type',
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
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'domain': type.StringType(),
            'subject': type.StringType(),
            'type': type.ReferenceType(__name__, 'Access.SubjectType'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vcenter/namespaces/instances/{namespace}/access/{domain}/{subject}',
            path_variables={
                'namespace': 'namespace',
                'domain': 'domain',
                'subject': 'subject',
            },
            query_parameters={
                'type': 'type',
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
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'domain': type.StringType(),
            'subject': type.StringType(),
            'type': type.ReferenceType(__name__, 'Access.SubjectType'),
            'spec': type.ReferenceType(__name__, 'Access.SetSpec'),
        })
        set_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/vcenter/namespaces/instances/{namespace}/access/{domain}/{subject}',
            request_body_parameter='spec',
            path_variables={
                'namespace': 'namespace',
                'domain': 'domain',
                'subject': 'subject',
            },
            query_parameters={
                'type': 'type',
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
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'domain': type.StringType(),
            'subject': type.StringType(),
            'type': type.ReferenceType(__name__, 'Access.SubjectType'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
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
            url_template='/vcenter/namespaces/instances/{namespace}/access/{domain}/{subject}',
            path_variables={
                'namespace': 'namespace',
                'domain': 'domain',
                'subject': 'subject',
            },
            query_parameters={
                'type': 'type',
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'create': {
                'input_type': create_input_type,
                'output_type': type.VoidType(),
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
            'set': {
                'input_type': set_input_type,
                'output_type': type.VoidType(),
                'errors': set_error_dict,
                'input_value_validator_list': set_input_value_validator_list,
                'output_validator_list': set_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Access.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'create': create_rest_metadata,
            'delete': delete_rest_metadata,
            'set': set_rest_metadata,
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespaces.access',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _NamespaceSelfServiceStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for activate operation
        activate_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        activate_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unable_to_allocate_resource':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnableToAllocateResource'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),

        }
        activate_input_value_validator_list = [
        ]
        activate_output_validator_list = [
        ]
        activate_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespaces/namespace-self-service/{cluster}',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'activate',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for deactivate operation
        deactivate_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        deactivate_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),

        }
        deactivate_input_value_validator_list = [
        ]
        deactivate_output_validator_list = [
        ]
        deactivate_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespaces/namespace-self-service/{cluster}',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'deactivate',
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
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
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
            url_template='/vcenter/namespaces/namespace-self-service/{cluster}',
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

        # properties for list operation
        list_input_type = type.StructType('operation-input', {})
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
            url_template='/vcenter/namespaces/namespace-self-service',
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

        # properties for activate_with_template operation
        activate_with_template_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.ReferenceType(__name__, 'NamespaceSelfService.ActivateTemplateSpec'),
        })
        activate_with_template_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unable_to_allocate_resource':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnableToAllocateResource'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),

        }
        activate_with_template_input_value_validator_list = [
        ]
        activate_with_template_output_validator_list = [
        ]
        activate_with_template_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespaces/namespace-self-service/{cluster}',
            request_body_parameter='spec',
            path_variables={
                'cluster': 'cluster',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'activateWithTemplate',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'activate': {
                'input_type': activate_input_type,
                'output_type': type.VoidType(),
                'errors': activate_error_dict,
                'input_value_validator_list': activate_input_value_validator_list,
                'output_validator_list': activate_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'deactivate': {
                'input_type': deactivate_input_type,
                'output_type': type.VoidType(),
                'errors': deactivate_error_dict,
                'input_value_validator_list': deactivate_input_value_validator_list,
                'output_validator_list': deactivate_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'NamespaceSelfService.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'NamespaceSelfService.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'activate_with_template': {
                'input_type': activate_with_template_input_type,
                'output_type': type.VoidType(),
                'errors': activate_with_template_error_dict,
                'input_value_validator_list': activate_with_template_input_value_validator_list,
                'output_validator_list': activate_with_template_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'activate': activate_rest_metadata,
            'deactivate': deactivate_rest_metadata,
            'get': get_rest_metadata,
            'list': list_rest_metadata,
            'activate_with_template': activate_with_template_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespaces.namespace_self_service',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _NamespaceTemplatesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'template': type.IdType(resource_types='com.vmware.vcenter.namespaces.NamespaceTemplate'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
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
            url_template='/vcenter/namespaces/namespace-templates/clusters/{cluster}/templates/{template}',
            path_variables={
                'cluster': 'cluster',
                'template': 'template',
            },
             header_parameters={
                 },
            query_parameters={
            }
        )

        # properties for get_v2 operation
        get_v2_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'template': type.IdType(resource_types='com.vmware.vcenter.namespaces.NamespaceTemplate'),
        })
        get_v2_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        get_v2_input_value_validator_list = [
        ]
        get_v2_output_validator_list = [
        ]
        get_v2_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespaces/namespace-templates/supervisors/{supervisor}/templates/{template}',
            path_variables={
                'supervisor': 'supervisor',
                'template': 'template',
            },
             header_parameters={
                 },
            query_parameters={
            }
        )

        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
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
            url_template='/vcenter/namespaces/namespace-templates/clusters/{cluster}',
            path_variables={
                'cluster': 'cluster',
            },
             header_parameters={
               },
            query_parameters={
            }
        )

        # properties for list_v2 operation
        list_v2_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
        })
        list_v2_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        list_v2_input_value_validator_list = [
        ]
        list_v2_output_validator_list = [
        ]
        list_v2_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespaces/namespace-templates/supervisors/{supervisor}',
            path_variables={
                'supervisor': 'supervisor',
            },
             header_parameters={
               },
            query_parameters={
            }
        )

        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'spec': type.ReferenceType(__name__, 'NamespaceTemplates.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespaces/namespace-templates/clusters/{cluster}',
            path_variables={
                'cluster': 'cluster',
            },
             header_parameters={
                 },
            query_parameters={
            }
        )

        # properties for create_v2 operation
        create_v2_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'spec': type.ReferenceType(__name__, 'NamespaceTemplates.CreateSpec'),
        })
        create_v2_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),

        }
        create_v2_input_value_validator_list = [
        ]
        create_v2_output_validator_list = [
        ]
        create_v2_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespaces/namespace-templates/supervisors/{supervisor}',
            path_variables={
                'supervisor': 'supervisor',
            },
             header_parameters={
                 },
            query_parameters={
            }
        )

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'cluster': type.IdType(resource_types='ClusterComputeResource'),
            'template': type.IdType(resource_types='com.vmware.vcenter.namespaces.NamespaceTemplate'),
            'spec': type.ReferenceType(__name__, 'NamespaceTemplates.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespaces/namespace-templates/clusters/{cluster}/templates/{template}',
            path_variables={
                'cluster': 'cluster',
                'template': 'template',
            },
             header_parameters={
                   },
            query_parameters={
            }
        )

        # properties for update_v2 operation
        update_v2_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'template': type.IdType(resource_types='com.vmware.vcenter.namespaces.NamespaceTemplate'),
            'spec': type.ReferenceType(__name__, 'NamespaceTemplates.UpdateSpec'),
        })
        update_v2_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        update_v2_input_value_validator_list = [
        ]
        update_v2_output_validator_list = [
        ]
        update_v2_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespaces/namespace-templates/supervisors/{supervisor}/templates/{template}',
            path_variables={
                'supervisor': 'supervisor',
                'template': 'template',
            },
             header_parameters={
                   },
            query_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'NamespaceTemplates.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get_v2': {
                'input_type': get_v2_input_type,
                'output_type': type.ReferenceType(__name__, 'NamespaceTemplates.InfoV2'),
                'errors': get_v2_error_dict,
                'input_value_validator_list': get_v2_input_value_validator_list,
                'output_validator_list': get_v2_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'NamespaceTemplates.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list_v2': {
                'input_type': list_v2_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'NamespaceTemplates.SummaryV2')),
                'errors': list_v2_error_dict,
                'input_value_validator_list': list_v2_input_value_validator_list,
                'output_validator_list': list_v2_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'create': {
                'input_type': create_input_type,
                'output_type': type.VoidType(),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'create_v2': {
                'input_type': create_v2_input_type,
                'output_type': type.VoidType(),
                'errors': create_v2_error_dict,
                'input_value_validator_list': create_v2_input_value_validator_list,
                'output_validator_list': create_v2_output_validator_list,
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
            'update_v2': {
                'input_type': update_v2_input_type,
                'output_type': type.VoidType(),
                'errors': update_v2_error_dict,
                'input_value_validator_list': update_v2_input_value_validator_list,
                'output_validator_list': update_v2_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'get_v2': get_v2_rest_metadata,
            'list': list_rest_metadata,
            'list_v2': list_v2_rest_metadata,
            'create': create_rest_metadata,
            'create_v2': create_v2_rest_metadata,
            'update': update_rest_metadata,
            'update_v2': update_v2_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespaces.namespace_templates',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _InstancesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Instances.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespaces/instances',
            request_body_parameter='spec',
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

        # properties for create_v2 operation
        create_v2_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Instances.CreateSpecV2'),
        })
        create_v2_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        create_v2_input_value_validator_list = [
        ]
        create_v2_output_validator_list = [
        ]
        create_v2_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespaces/instances/v2',
            request_body_parameter='spec',
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

        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vcenter/namespaces/instances/{namespace}',
            path_variables={
                'namespace': 'namespace',
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
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
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
            url_template='/vcenter/namespaces/instances/{namespace}',
            path_variables={
                'namespace': 'namespace',
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

        # properties for get_v2 operation
        get_v2_input_type = type.StructType('operation-input', {
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
        })
        get_v2_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        get_v2_input_value_validator_list = [
        ]
        get_v2_output_validator_list = [
        ]
        get_v2_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespaces/instances/v2/{namespace}',
            path_variables={
                'namespace': 'namespace',
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
        list_input_type = type.StructType('operation-input', {})
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
            url_template='/vcenter/namespaces/instances',
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

        # properties for list_v2 operation
        list_v2_input_type = type.StructType('operation-input', {})
        list_v2_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        list_v2_input_value_validator_list = [
        ]
        list_v2_output_validator_list = [
        ]
        list_v2_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespaces/instances/v2',
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

        # properties for set operation
        set_input_type = type.StructType('operation-input', {
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'spec': type.ReferenceType(__name__, 'Instances.SetSpec'),
        })
        set_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/vcenter/namespaces/instances/{namespace}',
            request_body_parameter='spec',
            path_variables={
                'namespace': 'namespace',
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

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'spec': type.ReferenceType(__name__, 'Instances.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespaces/instances/{namespace}',
            request_body_parameter='spec',
            path_variables={
                'namespace': 'namespace',
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

        # properties for register_VM operation
        register_VM_input_type = type.StructType('operation-input', {
            'namespace': type.IdType(resource_types='com.vmware.vcenter.namespaces.Instance'),
            'spec': type.ReferenceType(__name__, 'Instances.RegisterVMSpec'),
        })
        register_VM_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.already_in_desired_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyInDesiredState'),

        }
        register_VM_input_value_validator_list = [
        ]
        register_VM_output_validator_list = [
        ]
        register_VM_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespaces/instances/{namespace}/registervm',
            request_body_parameter='spec',
            path_variables={
                'namespace': 'namespace',
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
            'create': {
                'input_type': create_input_type,
                'output_type': type.VoidType(),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'create_v2': {
                'input_type': create_v2_input_type,
                'output_type': type.VoidType(),
                'errors': create_v2_error_dict,
                'input_value_validator_list': create_v2_input_value_validator_list,
                'output_validator_list': create_v2_output_validator_list,
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
                'output_type': type.ReferenceType(__name__, 'Instances.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get_v2': {
                'input_type': get_v2_input_type,
                'output_type': type.ReferenceType(__name__, 'Instances.InfoV2'),
                'errors': get_v2_error_dict,
                'input_value_validator_list': get_v2_input_value_validator_list,
                'output_validator_list': get_v2_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'Instances.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list_v2': {
                'input_type': list_v2_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'Instances.SummaryV2')),
                'errors': list_v2_error_dict,
                'input_value_validator_list': list_v2_input_value_validator_list,
                'output_validator_list': list_v2_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'set': {
                'input_type': set_input_type,
                'output_type': type.VoidType(),
                'errors': set_error_dict,
                'input_value_validator_list': set_input_value_validator_list,
                'output_validator_list': set_output_validator_list,
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
            'register_VM': {
                'input_type': register_VM_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.task'),
                'errors': register_VM_error_dict,
                'input_value_validator_list': register_VM_input_value_validator_list,
                'output_validator_list': register_VM_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'create': create_rest_metadata,
            'create_v2': create_v2_rest_metadata,
            'delete': delete_rest_metadata,
            'get': get_rest_metadata,
            'get_v2': get_v2_rest_metadata,
            'list': list_rest_metadata,
            'list_v2': list_v2_rest_metadata,
            'set': set_rest_metadata,
            'update': update_rest_metadata,
            'register_VM': register_VM_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespaces.instances',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Access': Access,
        'NamespaceSelfService': NamespaceSelfService,
        'NamespaceTemplates': NamespaceTemplates,
        'Instances': Instances,
        'user': 'com.vmware.vcenter.namespaces.user_client.StubFactory',
    }

