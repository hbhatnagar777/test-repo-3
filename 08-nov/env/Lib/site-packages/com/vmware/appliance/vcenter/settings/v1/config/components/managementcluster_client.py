# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.
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


class ManagementCluster(VapiStruct):
    """
    The ``ManagementCluster`` class contains attributes describing the
    configuration of the management cluster that hosts the management virtual
    machines. It contains the resource settings of the cluster and the
    management virtual machines running inside it. **Warning:** This class is
    available as Technology Preview. These are early access APIs provided to
    test, automate and provide feedback on the feature. Since this can change
    based on feedback, VMware does not guarantee backwards compatibility and
    recommends against using them in production environments. Some Technology
    Preview APIs might only be applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 name=None,
                 parent_path=None,
                 drs=None,
                 management_resourcepools=None,
                 clusters=None,
                ):
        """
        :type  name: :class:`str` or ``None``
        :param name: To be deprecated. Name of the management cluster which hosts the
            management VMs. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  parent_path: :class:`str` or ``None``
        :param parent_path: To be deprecated. Absolute path from root folder to management
            cluster's parent. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  drs: :class:`DrsConfig` or ``None``
        :param drs: To be deprecated. Cluster-wide configuration of the vSphere DRS
            service. **Warning:** This attribute is available as Technology
            Preview. These are early access APIs provided to test, automate and
            provide feedback on the feature. Since this can change based on
            feedback, VMware does not guarantee backwards compatibility and
            recommends against using them in production environments. Some
            Technology Preview APIs might only be applicable to specific
            environments.
        :type  management_resourcepools: :class:`list` of :class:`ResourcePool` or ``None``
        :param management_resourcepools: To be deprecated. The management cluster provides dedicated
            resource pools for running the management virtual machines.
            Management cluster can can run workload VMs outside this resource
            pools. **Warning:** This attribute is available as Technology
            Preview. These are early access APIs provided to test, automate and
            provide feedback on the feature. Since this can change based on
            feedback, VMware does not guarantee backwards compatibility and
            recommends against using them in production environments. Some
            Technology Preview APIs might only be applicable to specific
            environments.
        :type  clusters: :class:`list` of :class:`Cluster` or ``None``
        :param clusters: The management cluster have a list of cluster where management VMs
            may be deployed. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        """
        self.name = name
        self.parent_path = parent_path
        self.drs = drs
        self.management_resourcepools = management_resourcepools
        self.clusters = clusters
        VapiStruct.__init__(self)


ManagementCluster._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.management_cluster', {
        'name': type.OptionalType(type.StringType()),
        'parent_path': type.OptionalType(type.StringType()),
        'drs': type.OptionalType(type.ReferenceType(__name__, 'DrsConfig')),
        'management_resourcepools': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ResourcePool'))),
        'clusters': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Cluster'))),
    },
    ManagementCluster,
    False,
    None))



class Cluster(VapiStruct):
    """
    The ``Cluster`` class contains attributes describing the configuration of
    the the management cluster that hosts the management virtual machines.
    **Warning:** This class is available as Technology Preview. These are early
    access APIs provided to test, automate and provide feedback on the feature.
    Since this can change based on feedback, VMware does not guarantee
    backwards compatibility and recommends against using them in production
    environments. Some Technology Preview APIs might only be applicable to
    specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 name=None,
                 parent_path=None,
                 drs=None,
                 management_resourcepools=None,
                ):
        """
        :type  name: :class:`str`
        :param name: Name of the management cluster which hosts the management VMs.
            **Warning:** This attribute is available as Technology Preview.
            These are early access APIs provided to test, automate and provide
            feedback on the feature. Since this can change based on feedback,
            VMware does not guarantee backwards compatibility and recommends
            against using them in production environments. Some Technology
            Preview APIs might only be applicable to specific environments.
        :type  parent_path: :class:`str`
        :param parent_path: Absolute path from root folder to management cluster's parent.
            **Warning:** This attribute is available as Technology Preview.
            These are early access APIs provided to test, automate and provide
            feedback on the feature. Since this can change based on feedback,
            VMware does not guarantee backwards compatibility and recommends
            against using them in production environments. Some Technology
            Preview APIs might only be applicable to specific environments.
        :type  drs: :class:`DrsConfig` or ``None``
        :param drs: Individual Cluster-level configuration of the vSphere DRS service.
            **Warning:** This attribute is available as Technology Preview.
            These are early access APIs provided to test, automate and provide
            feedback on the feature. Since this can change based on feedback,
            VMware does not guarantee backwards compatibility and recommends
            against using them in production environments. Some Technology
            Preview APIs might only be applicable to specific environments.
        :type  management_resourcepools: :class:`list` of :class:`ResourcePool` or ``None``
        :param management_resourcepools: The management cluster provides dedicated resource pools for
            running the management virtual machines. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        """
        self.name = name
        self.parent_path = parent_path
        self.drs = drs
        self.management_resourcepools = management_resourcepools
        VapiStruct.__init__(self)


Cluster._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.cluster', {
        'name': type.StringType(),
        'parent_path': type.StringType(),
        'drs': type.OptionalType(type.ReferenceType(__name__, 'DrsConfig')),
        'management_resourcepools': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ResourcePool'))),
    },
    Cluster,
    False,
    None))



class DrsConfig(VapiStruct):
    """
    The ``DrsConfig`` class contains attributes describing the DRS specific
    configurations of the management cluster. **Warning:** This class is
    available as Technology Preview. These are early access APIs provided to
    test, automate and provide feedback on the feature. Since this can change
    based on feedback, VMware does not guarantee backwards compatibility and
    recommends against using them in production environments. Some Technology
    Preview APIs might only be applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 enabled=None,
                 automation_level=None,
                 migration_threshold=None,
                 virtual_machine_automation=None,
                ):
        """
        :type  enabled: :class:`bool`
        :param enabled: Flag indicating whether or not DRS service is enabled. **Warning:**
            This attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        :type  automation_level: :class:`DrsConfig.DrsBehaviorInfo` or ``None``
        :param automation_level: Specifies the cluster-wide default DRS behavior for virtual
            machines. You can override the default behavior for a virtual
            machine. **Warning:** This attribute is available as Technology
            Preview. These are early access APIs provided to test, automate and
            provide feedback on the feature. Since this can change based on
            feedback, VMware does not guarantee backwards compatibility and
            recommends against using them in production environments. Some
            Technology Preview APIs might only be applicable to specific
            environments.
            If None or empty, the value is skipped.
        :type  migration_threshold: :class:`long` or ``None``
        :param migration_threshold: Threshold for generated recommendations. DRS generates only those
            recommendations that are above the specified vmotionRate. Ratings
            vary from 1 to 5. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
            If None or empty, the value is skipped.
        :type  virtual_machine_automation: :class:`bool` or ``None``
        :param virtual_machine_automation: Flag that dictates whether DRS Behavior overrides for individual
            VMs. **Warning:** This attribute is available as Technology
            Preview. These are early access APIs provided to test, automate and
            provide feedback on the feature. Since this can change based on
            feedback, VMware does not guarantee backwards compatibility and
            recommends against using them in production environments. Some
            Technology Preview APIs might only be applicable to specific
            environments.
        """
        self.enabled = enabled
        self.automation_level = automation_level
        self.migration_threshold = migration_threshold
        self.virtual_machine_automation = virtual_machine_automation
        VapiStruct.__init__(self)


    class DrsBehaviorInfo(Enum):
        """
        The ``DrsConfig.DrsBehaviorInfo`` class defines the automation levels that
        can be set on a DRS cluster. **Warning:** This enumeration is available as
        Technology Preview. These are early access APIs provided to test, automate
        and provide feedback on the feature. Since this can change based on
        feedback, VMware does not guarantee backwards compatibility and recommends
        against using them in production environments. Some Technology Preview APIs
        might only be applicable to specific environments.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        MANUAL = None
        """
        Specifies that VirtualCenter should generate recommendations for virtual
        machine migration and for placement with a host, but should not implement
        the recommendations automatically. **Warning:** This class attribute is
        available as Technology Preview. These are early access APIs provided to
        test, automate and provide feedback on the feature. Since this can change
        based on feedback, VMware does not guarantee backwards compatibility and
        recommends against using them in production environments. Some Technology
        Preview APIs might only be applicable to specific environments.

        """
        PARTIALLY_AUTOMATED = None
        """
        Specifies that VirtualCenter should generate recommendations for virtual
        machine migration and for placement with a host, but should automatically
        implement only the placement at power on. **Warning:** This class attribute
        is available as Technology Preview. These are early access APIs provided to
        test, automate and provide feedback on the feature. Since this can change
        based on feedback, VMware does not guarantee backwards compatibility and
        recommends against using them in production environments. Some Technology
        Preview APIs might only be applicable to specific environments.

        """
        FULLY_AUTOMATED = None
        """
        Specifies that VirtualCenter should automate both the migration of virtual
        machines and their placement with a host at power on. **Warning:** This
        class attribute is available as Technology Preview. These are early access
        APIs provided to test, automate and provide feedback on the feature. Since
        this can change based on feedback, VMware does not guarantee backwards
        compatibility and recommends against using them in production environments.
        Some Technology Preview APIs might only be applicable to specific
        environments.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`DrsBehaviorInfo` instance.
            """
            Enum.__init__(string)

    DrsBehaviorInfo._set_values({
        'MANUAL': DrsBehaviorInfo('MANUAL'),
        'PARTIALLY_AUTOMATED': DrsBehaviorInfo('PARTIALLY_AUTOMATED'),
        'FULLY_AUTOMATED': DrsBehaviorInfo('FULLY_AUTOMATED'),
    })
    DrsBehaviorInfo._set_binding_type(type.EnumType(
        'com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.drs_config.drs_behavior_info',
        DrsBehaviorInfo))

DrsConfig._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.drs_config', {
        'enabled': type.BooleanType(),
        'automation_level': type.OptionalType(type.ReferenceType(__name__, 'DrsConfig.DrsBehaviorInfo')),
        'migration_threshold': type.OptionalType(type.IntegerType()),
        'virtual_machine_automation': type.OptionalType(type.BooleanType()),
    },
    DrsConfig,
    False,
    None))



class ResourcePool(VapiStruct):
    """
    The ``ResourcePool`` class contains information about the management
    resource pools present in the cluster. **Warning:** This class is available
    as Technology Preview. These are early access APIs provided to test,
    automate and provide feedback on the feature. Since this can change based
    on feedback, VMware does not guarantee backwards compatibility and
    recommends against using them in production environments. Some Technology
    Preview APIs might only be applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 name=None,
                 parent_path=None,
                 config=None,
                 vm=None,
                ):
        """
        :type  name: :class:`str`
        :param name: Name of the vCenter Server resource pool. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        :type  parent_path: :class:`str`
        :param parent_path: Absolute path from root folder to resource pool's parent.
            **Warning:** This attribute is available as Technology Preview.
            These are early access APIs provided to test, automate and provide
            feedback on the feature. Since this can change based on feedback,
            VMware does not guarantee backwards compatibility and recommends
            against using them in production environments. Some Technology
            Preview APIs might only be applicable to specific environments.
        :type  config: :class:`ResourceConfigSpec`
        :param config: Summary of the resource pool containing the resource spec.
            **Warning:** This attribute is available as Technology Preview.
            These are early access APIs provided to test, automate and provide
            feedback on the feature. Since this can change based on feedback,
            VMware does not guarantee backwards compatibility and recommends
            against using them in production environments. Some Technology
            Preview APIs might only be applicable to specific environments.
        :type  vm: :class:`list` of :class:`ManagementVirtualMachine` or ``None``
        :param vm: The management virtual machines contained in this resource pool.
            **Warning:** This attribute is available as Technology Preview.
            These are early access APIs provided to test, automate and provide
            feedback on the feature. Since this can change based on feedback,
            VMware does not guarantee backwards compatibility and recommends
            against using them in production environments. Some Technology
            Preview APIs might only be applicable to specific environments.
            If None or empty, no virtual machine is expected to run in this
            resource pool..
        """
        self.name = name
        self.parent_path = parent_path
        self.config = config
        self.vm = vm
        VapiStruct.__init__(self)


ResourcePool._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.resource_pool', {
        'name': type.StringType(),
        'parent_path': type.StringType(),
        'config': type.ReferenceType(__name__, 'ResourceConfigSpec'),
        'vm': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ManagementVirtualMachine'))),
    },
    ResourcePool,
    False,
    None))



class ManagementVirtualMachine(VapiStruct):
    """
    The ``ManagementVirtualMachine`` class contains information about the
    management virtual machine configurations present in the management
    cluster. **Warning:** This class is available as Technology Preview. These
    are early access APIs provided to test, automate and provide feedback on
    the feature. Since this can change based on feedback, VMware does not
    guarantee backwards compatibility and recommends against using them in
    production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 name=None,
                 mo_id=None,
                 vm_type=None,
                 parent_path=None,
                 resource_config=None,
                ):
        """
        :type  name: :class:`str`
        :param name: Name of the management virtual machine configuration. **Warning:**
            This attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        :type  mo_id: :class:`str` or ``None``
        :param mo_id: Managed Object identifier of the management virtual machine.
            **Warning:** This attribute is available as Technology Preview.
            These are early access APIs provided to test, automate and provide
            feedback on the feature. Since this can change based on feedback,
            VMware does not guarantee backwards compatibility and recommends
            against using them in production environments. Some Technology
            Preview APIs might only be applicable to specific environments.
        :type  vm_type: :class:`ManagementVirtualMachine.ManagementVMType`
        :param vm_type: Type of the management virtual machine. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  parent_path: :class:`str`
        :param parent_path: Absolute path from root folder to management virtual machine parent
            vm folder. **Warning:** This attribute is available as Technology
            Preview. These are early access APIs provided to test, automate and
            provide feedback on the feature. Since this can change based on
            feedback, VMware does not guarantee backwards compatibility and
            recommends against using them in production environments. Some
            Technology Preview APIs might only be applicable to specific
            environments.
        :type  resource_config: :class:`ResourceConfigSpec` or ``None``
        :param resource_config: Configuration of the management virtual machine. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
            If None, then there is no configuration.
        """
        self.name = name
        self.mo_id = mo_id
        self.vm_type = vm_type
        self.parent_path = parent_path
        self.resource_config = resource_config
        VapiStruct.__init__(self)


    class ManagementVMType(Enum):
        """
        The ``ManagementVirtualMachine.ManagementVMType`` class defines the type of
        management virtual machine. **Warning:** This enumeration is available as
        Technology Preview. These are early access APIs provided to test, automate
        and provide feedback on the feature. Since this can change based on
        feedback, VMware does not guarantee backwards compatibility and recommends
        against using them in production environments. Some Technology Preview APIs
        might only be applicable to specific environments.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        VCENTER = None
        """
        The management virtual machine is of type vCenter. **Warning:** This class
        attribute is available as Technology Preview. These are early access APIs
        provided to test, automate and provide feedback on the feature. Since this
        can change based on feedback, VMware does not guarantee backwards
        compatibility and recommends against using them in production environments.
        Some Technology Preview APIs might only be applicable to specific
        environments.

        """
        CLOUD_GATEWAY = None
        """
        The management virtual machine is of type Cloud Gateway. **Warning:** This
        class attribute is available as Technology Preview. These are early access
        APIs provided to test, automate and provide feedback on the feature. Since
        this can change based on feedback, VMware does not guarantee backwards
        compatibility and recommends against using them in production environments.
        Some Technology Preview APIs might only be applicable to specific
        environments.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ManagementVMType` instance.
            """
            Enum.__init__(string)

    ManagementVMType._set_values({
        'VCENTER': ManagementVMType('VCENTER'),
        'CLOUD_GATEWAY': ManagementVMType('CLOUD_GATEWAY'),
    })
    ManagementVMType._set_binding_type(type.EnumType(
        'com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.management_virtual_machine.management_VM_type',
        ManagementVMType))

ManagementVirtualMachine._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.management_virtual_machine', {
        'name': type.StringType(),
        'mo_id': type.OptionalType(type.StringType()),
        'vm_type': type.ReferenceType(__name__, 'ManagementVirtualMachine.ManagementVMType'),
        'parent_path': type.StringType(),
        'resource_config': type.OptionalType(type.ReferenceType(__name__, 'ResourceConfigSpec')),
    },
    ManagementVirtualMachine,
    False,
    None))



class ResourceConfigSpec(VapiStruct):
    """
    The ``ResourceConfigSpec`` class provides resource reserved for a resource
    pool or management virtual machine. **Warning:** This class is available as
    Technology Preview. These are early access APIs provided to test, automate
    and provide feedback on the feature. Since this can change based on
    feedback, VMware does not guarantee backwards compatibility and recommends
    against using them in production environments. Some Technology Preview APIs
    might only be applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 cpu_allocation=None,
                 memory_allocation=None,
                ):
        """
        :type  cpu_allocation: :class:`ResourceAllocationInfo`
        :param cpu_allocation: Resource allocation information for CPU. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        :type  memory_allocation: :class:`ResourceAllocationInfo`
        :param memory_allocation: Resource allocation information for memory. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        """
        self.cpu_allocation = cpu_allocation
        self.memory_allocation = memory_allocation
        VapiStruct.__init__(self)


ResourceConfigSpec._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.resource_config_spec', {
        'cpu_allocation': type.ReferenceType(__name__, 'ResourceAllocationInfo'),
        'memory_allocation': type.ReferenceType(__name__, 'ResourceAllocationInfo'),
    },
    ResourceConfigSpec,
    False,
    None))



class ResourceAllocationInfo(VapiStruct):
    """
    The ``ResourceAllocationInfo`` class contains resource allocation
    information of a resource pool or management virtual machine. **Warning:**
    This class is available as Technology Preview. These are early access APIs
    provided to test, automate and provide feedback on the feature. Since this
    can change based on feedback, VMware does not guarantee backwards
    compatibility and recommends against using them in production environments.
    Some Technology Preview APIs might only be applicable to specific
    environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 reservation=None,
                 expandable_reservation=None,
                 limit=None,
                 shares=None,
                ):
        """
        :type  reservation: :class:`long`
        :param reservation: Amount of resource that is guaranteed available to a resource pool
            or a virtual machine. Reserved resources are not wasted if they are
            not used. If the utilization is less than the reservation, the
            resources can be utilized by other running virtual machines. Units
            are MB fo memory, and MHz for CPU. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  expandable_reservation: :class:`bool`
        :param expandable_reservation: In a resource pool with an expandable reservation, the reservation
            can grow beyond the specified value, if the parent resource pool
            has unreserved resources. A non-expandable reservation is called a
            fixed reservation. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  limit: :class:`long`
        :param limit: The utilization of a resource pool will not exceed this limit, even
            if there are available resources. This is typically used to ensure
            a consistent performance of resource pools independent of available
            resources. If set to -1, then there is no fixed limit on resource
            usage (only bounded by available resources and shares). Units are
            MB for memory, and MHz for CPU. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  shares: :class:`Shares`
        :param shares: Shares are used in case of resource contention. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        """
        self.reservation = reservation
        self.expandable_reservation = expandable_reservation
        self.limit = limit
        self.shares = shares
        VapiStruct.__init__(self)


ResourceAllocationInfo._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.resource_allocation_info', {
        'reservation': type.IntegerType(),
        'expandable_reservation': type.BooleanType(),
        'limit': type.IntegerType(),
        'shares': type.ReferenceType(__name__, 'Shares'),
    },
    ResourceAllocationInfo,
    False,
    None))



class Shares(VapiStruct):
    """
    The ``Shares`` class provides specification of shares. 
    
    Shares are used to determine relative allocation between resource
    consumers. In general, a consumer with more shares gets proportionally more
    of the resource, subject to certain other constraints.. **Warning:** This
    class is available as Technology Preview. These are early access APIs
    provided to test, automate and provide feedback on the feature. Since this
    can change based on feedback, VMware does not guarantee backwards
    compatibility and recommends against using them in production environments.
    Some Technology Preview APIs might only be applicable to specific
    environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 level=None,
                 shares=None,
                ):
        """
        :type  level: :class:`Shares.Level`
        :param level: The allocation level. It maps to a pre-determined set of numeric
            values for shares. If the shares value does not map to a predefined
            size, then the level is set as CUSTOM. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  shares: :class:`long`
        :param shares: When :attr:`Shares.level` is set to CUSTOM, it is the number of
            shares allocated. Otherwise, this value is ignored. 
            
            There is no unit for this value. It is a relative measure based on
            the settings for other resource pools.. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        """
        self.level = level
        self.shares = shares
        VapiStruct.__init__(self)


    class Level(Enum):
        """
        The ``Shares.Level`` class defines the possible values for the allocation
        level. **Warning:** This enumeration is available as Technology Preview.
        These are early access APIs provided to test, automate and provide feedback
        on the feature. Since this can change based on feedback, VMware does not
        guarantee backwards compatibility and recommends against using them in
        production environments. Some Technology Preview APIs might only be
        applicable to specific environments.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        LOW = None
        """
        For CPU: Shares = 500 \* number of virtual CPUs.
        For Memory: Shares = 5 \* virtual machine memory size in MB.
        . **Warning:** This class attribute is available as Technology Preview.
        These are early access APIs provided to test, automate and provide feedback
        on the feature. Since this can change based on feedback, VMware does not
        guarantee backwards compatibility and recommends against using them in
        production environments. Some Technology Preview APIs might only be
        applicable to specific environments.

        """
        NORMAL = None
        """
        For CPU: Shares = 1000 \* number of virtual CPUs.
        For Memory: Shares = 10 \* virtual machine memory size in MB.
        . **Warning:** This class attribute is available as Technology Preview.
        These are early access APIs provided to test, automate and provide feedback
        on the feature. Since this can change based on feedback, VMware does not
        guarantee backwards compatibility and recommends against using them in
        production environments. Some Technology Preview APIs might only be
        applicable to specific environments.

        """
        HIGH = None
        """
        For CPU: Shares = 2000 \* nmumber of virtual CPUs.
        For Memory: Shares = 20 \* virtual machine memory size in MB.
        . **Warning:** This class attribute is available as Technology Preview.
        These are early access APIs provided to test, automate and provide feedback
        on the feature. Since this can change based on feedback, VMware does not
        guarantee backwards compatibility and recommends against using them in
        production environments. Some Technology Preview APIs might only be
        applicable to specific environments.

        """
        CUSTOM = None
        """
        If :class:`set`, in case there is resource contention the server uses the
        shares value to determine the resource allocation. **Warning:** This class
        attribute is available as Technology Preview. These are early access APIs
        provided to test, automate and provide feedback on the feature. Since this
        can change based on feedback, VMware does not guarantee backwards
        compatibility and recommends against using them in production environments.
        Some Technology Preview APIs might only be applicable to specific
        environments.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Level` instance.
            """
            Enum.__init__(string)

    Level._set_values({
        'LOW': Level('LOW'),
        'NORMAL': Level('NORMAL'),
        'HIGH': Level('HIGH'),
        'CUSTOM': Level('CUSTOM'),
    })
    Level._set_binding_type(type.EnumType(
        'com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.shares.level',
        Level))

Shares._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster.shares', {
        'level': type.ReferenceType(__name__, 'Shares.Level'),
        'shares': type.IntegerType(),
    },
    Shares,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

