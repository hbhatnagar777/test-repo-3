# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.environment_browser.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.environment_browser_client`` module provides classes
to access to the environment that physical hardware presents for creating and
configuring a virtual machine. 

The environment consists of the following main components: 

* The available configuration option keys that may be used with the
  ConfigOption get() method. Access to the configuration option keys is provided
  through the ConfigOptionDescriptor get() method.
* The virtual machine configuration options. Each vim.vm.ConfigOption describes
  the execution environment for a virtual machine, the particular set of virtual
  hardware that is supported. A given hardware might support multiple sets.
  Access is provided through the ConfigOption get() method.
* The supported device targets. Each virtual device specified in the virtual
  machine needs to be hooked up to a "physical" counterpart. For networks, this
  means choosing a network name; for a virtual CD-rom this might be an ISO image,
  etc. The environment browser provides access to the device targets through the
  ConfigTargets class.



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


class ConfigOptionDescriptors(VapiInterface):
    """
    The ``ConfigOptionDescriptors`` class provides access to the keys used to
    query for available configuration options on certain hardware via the
    :func:`ConfigOptionDescriptors.list` method. This class was added in
    vSphere API 8.0.2.00300.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.environment_browser.config_option_descriptors'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ConfigOptionDescriptorsStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        Contains the definition of a unique key that can be used to retrieve a
        ``ConfigOption`` (``vim.vm.ConfigOption``) object. This class was added in
        vSphere API 8.0.2.00300.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     config_option=None,
                     description=None,
                     hosts=None,
                     create_supported=None,
                     default_config_option=None,
                     run_supported=None,
                     upgrade_supported=None,
                    ):
            """
            :type  config_option: :class:`str`
            :param config_option: A unique key used to identify a ConfigOption object. This attribute
                was added in vSphere API 8.0.2.00300.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.config_option``. When methods return a value
                of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.vcenter.config_option``.
            :type  description: :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
            :param description: A description of the configOption object. This attribute was added
                in vSphere API 8.0.2.00300.
                when None
            :type  hosts: :class:`list` of :class:`str` or ``None``
            :param hosts: List of hosts to which this descriptor applies. List of hosts is
                not set when descriptor is returned for a Datacenter. This
                attribute was added in vSphere API 8.0.2.00300.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will contain identifiers for the
                resource type: ``HostSystem``.
                when None
            :type  create_supported: :class:`bool`
            :param create_supported: Indicates whether the associated set of configuration options can
                be used for virtual machine creation on a given host or cluster.
                This attribute was added in vSphere API 8.0.2.00300.
            :type  default_config_option: :class:`bool`
            :param default_config_option: Indicates whether the associated set of virtual machine
                configuration options is the default one for a given host or
                cluster. Latest version is marked as default unless other version
                is specified via the vim.ComputeResource.ConfigInfo or
                vim.Datacenter.ConfigInfo defaultHardwareVersionKey. 
                
                If this setting is TRUE, virtual machine creates will use the
                associated set of configuration options, unless a config version is
                explicitly specified in the vim.vm.ConfigSpec. . This attribute was
                added in vSphere API 8.0.2.00300.
            :type  run_supported: :class:`bool`
            :param run_supported: Indicates whether the associated set of configuration options can
                be used to power on a virtual machine on a given host or cluster.
                This attribute was added in vSphere API 8.0.2.00300.
            :type  upgrade_supported: :class:`bool`
            :param upgrade_supported: Indicates whether the associated set of configuration options can
                be used as a virtual hardware upgrade target. This attribute was
                added in vSphere API 8.0.2.00300.
            """
            self.config_option = config_option
            self.description = description
            self.hosts = hosts
            self.create_supported = create_supported
            self.default_config_option = default_config_option
            self.run_supported = run_supported
            self.upgrade_supported = upgrade_supported
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.environment_browser.config_option_descriptors.summary', {
            'config_option': type.IdType(resource_types='com.vmware.vcenter.config_option'),
            'description': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
            'hosts': type.OptionalType(type.ListType(type.IdType())),
            'create_supported': type.BooleanType(),
            'default_config_option': type.BooleanType(),
            'run_supported': type.BooleanType(),
            'upgrade_supported': type.BooleanType(),
        },
        Summary,
        False,
        None))


    class ListParams(VapiStruct):
        """
        The ``ConfigOptionDescriptors.ListParams`` class specifies the parameters
        for the :func:`ConfigOptionDescriptors.list` method, such as which clusters
        to query. This class was added in vSphere API 8.0.2.00300.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     clusters=None,
                    ):
            """
            :type  clusters: :class:`set` of :class:`str` or ``None``
            :param clusters: A set of Cluster IDs that specify for which Clusters the
                configuration option descriptors are requested. This attribute was
                added in vSphere API 8.0.2.00300.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will contain identifiers for
                the resource type: ``ClusterComputeResource``.
                if None or empty an error will be returned. Ability to pass unset
                value is left for future expansion.
            """
            self.clusters = clusters
            VapiStruct.__init__(self)


    ListParams._set_binding_type(type.StructType(
        'com.vmware.vcenter.environment_browser.config_option_descriptors.list_params', {
            'clusters': type.OptionalType(type.SetType(type.IdType())),
        },
        ListParams,
        False,
        None))


    class ListResult(VapiStruct):
        """
        The ``ConfigOptionDescriptors.ListResult`` class holds the result of the
        :func:`ConfigOptionDescriptors.list` operation. This class was added in
        vSphere API 8.0.2.00300.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     config_options_descriptors=None,
                    ):
            """
            :type  config_options_descriptors: :class:`list` of :class:`ConfigOptionDescriptors.Summary`
            :param config_options_descriptors: List of configuration options matching the specified hardware. This
                attribute was added in vSphere API 8.0.2.00300.
            """
            self.config_options_descriptors = config_options_descriptors
            VapiStruct.__init__(self)


    ListResult._set_binding_type(type.StructType(
        'com.vmware.vcenter.environment_browser.config_option_descriptors.list_result', {
            'config_options_descriptors': type.ListType(type.ReferenceType(__name__, 'ConfigOptionDescriptors.Summary')),
        },
        ListResult,
        False,
        None))



    def list(self,
             params,
             ):
        """
        Returns the list of ConfigOptionDescriptors available for the specified
        filter. This method was added in vSphere API 8.0.2.00300.

        :type  params: :class:`ConfigOptionDescriptors.ListParams`
        :param params: Specification of the clusters for which config option descriptors
            are requested.
        :rtype: :class:`ConfigOptionDescriptors.ListResult`
        :return: a list of config option keys in
            :class:`ConfigOptionDescriptors.Summary` objects.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system encounters an unexpected error while responding to
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if an invalid filter is supplied.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if object identifiers in the spec cannot be matched.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges for all the
            specified clusters.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``ClusterComputeResource`` referenced by the
              attribute :attr:`ConfigOptionDescriptors.ListParams.clusters`
              requires ``System.View``.
        """
        return self._invoke('list',
                            {
                            'params': params,
                            })
class ConfigOptions(VapiInterface):
    """
    The ``ConfigOptions`` class provides access to virtual machine
    configuration options. The :func:`ConfigOptions.get` provides the keys for
    various config options available on certain hardware. Further the results
    of :func:`ConfigOptions.get` describe the supported execution environment
    for a virtual machine on a particular set of hardware. This class was added
    in vSphere API 8.0.2.00300.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.environment_browser.config_options'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ConfigOptionsStub)
        self._VAPI_OPERATION_IDS = {}

    class GetParams(VapiStruct):
        """
        The ``ConfigOptions.GetParams`` class specifies the parameters for the
        :func:`ConfigOptions.get` method, such as which clusters to query. This
        class was added in vSphere API 8.0.2.00300.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     clusters=None,
                     config_option=None,
                     guest_ids=None,
                    ):
            """
            :type  clusters: :class:`set` of :class:`str` or ``None``
            :param clusters: The clusters whose config option are requested. This attribute was
                added in vSphere API 8.0.2.00300.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will contain identifiers for
                the resource type: ``ClusterComputeResource``.
                if None or empty an InvalidArgument error is returned. None is
                allowed for future extensibility e.g. generating options for hosts,
                VM etc.
            :type  config_option: :class:`str` or ``None``
            :param config_option: Query for a specific config option with the key obtained from
                :func:`ConfigOptionDescriptors.list`. This attribute was added in
                vSphere API 8.0.2.00300.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.config_option``. When methods return a value
                of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.vcenter.config_option``.
                if None then the default config option will be returned.
            :type  guest_ids: :class:`set` of :class:`str` or ``None``
            :param guest_ids: Filter the set of Guest OSs for which descriptors will be returned.
                This attribute was added in vSphere API 8.0.2.00300.
                if None all guest OS descriptors are returned.
            """
            self.clusters = clusters
            self.config_option = config_option
            self.guest_ids = guest_ids
            VapiStruct.__init__(self)


    GetParams._set_binding_type(type.StructType(
        'com.vmware.vcenter.environment_browser.config_options.get_params', {
            'clusters': type.OptionalType(type.SetType(type.IdType())),
            'config_option': type.OptionalType(type.IdType()),
            'guest_ids': type.OptionalType(type.SetType(type.StringType())),
        },
        GetParams,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``ConfigOptions.Info`` class contain the vim.vm.ConfigOption specifying
        the available options for executing virtual machines on a set of clusters.
        The result is contained in a vim.vm.ConfigOption data structure. This class
        was added in vSphere API 8.0.2.00300.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     config_option=None,
                    ):
            """
            :type  config_option: :class:`vmware.vapi.struct.VapiStruct` or ``None``
            :param config_option: A vim.vm.ConfigOption data structure. This attribute was added in
                vSphere API 8.0.2.00300.
                may be None if none of the clusters specified in the #get method
                contained a vim.vm.ConfigOption that matched the requested key
                and/or guest IDs.
            """
            self.config_option = config_option
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.environment_browser.config_options.info', {
            'config_option': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
        },
        Info,
        False,
        None))



    def get(self,
            params,
            ):
        """
        Query for the ``vim.vm.ConfigOption`` from the hosts in the specified
        clusters. The filter spec may be optionally used to narrow the result
        to a specific config option by the key returned from
        :func:`ConfigOptionDescriptors.list` as well as one or more guest OS
        identifier(s). If the config option key is not specified, then the
        default config option for the specified cluster(s) is returned. 
        
        This method requires additional ``api_release`` request parameter which
        must be used to guarantee compatibility with future releases of the
        API. Consult the vSphere Automation SDKs Programming Guide for more
        information. . This method was added in vSphere API 8.0.2.00300.

        :type  params: :class:`ConfigOptions.GetParams`
        :param params: The query specification used to provide key, guest OS
            identifier(s), clusters.
        :rtype: :class:`ConfigOptions.Info`
        :return: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if invalid input is passed like invalid key, OS or cluster.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if at least one of the specified clusters cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges for all the
            specified clusters.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``ClusterComputeResource`` referenced by the
              attribute :attr:`ConfigOptions.GetParams.clusters` requires
              ``System.View``.
        """
        return self._invoke('get',
                            {
                            'params': params,
                            })
class ConfigTargets(VapiInterface):
    """
    The ``ConfigTargets`` class allows one to enumerate the hardware
    capabilities / device backings for particular set of clusters. This class
    was added in vSphere API 8.0.2.00300.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.environment_browser.config_targets'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ConfigTargetsStub)
        self._VAPI_OPERATION_IDS = {}

    class ConfigTargetSpec(Enum):
        """
        ConfigTargetSpec represents the search criteria and filters on a
        vim.vm.ConfigTarget. 
        
        A vim.vm.ConfigTarget has five categories of data: 
        
        * Basic: numCpus, numCpuCores, numNumaNodes, smcPresent,
          maxMemMBOptimalPerf, resourcePool, autoVmotion, maxPersistentMemoryMB
        * Datastores: datastore
        * Networks: network, opaqueNetwork, distributedVirtualPortgroup,
          distributedVirtualSwitch, legacyNetworkInfo
        * Devices: cdRom, serial, parallel, usb, floppy, scsiPassthrough,
          pciPassthrough, sriov, vFlashModule, sharedGpuPassthrough,
          dynamicPassthrough, qat, Intel SGX, AMD-SEV
        * Disks: scsiDisk, ideDisk
        
        
        
        
        
        :func:`ConfigTargets.get` will always return the basic category withing a
        vim.vm.ConfigTarget. For other categories, data is only returned if it is
        requested via the projection parameter. . This enumeration was added in
        vSphere API 8.0.2.00300.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        DATASTORES = None
        """
        Datastores category includes datastore list within a vim.vm.ConfigTarget.
        This class attribute was added in vSphere API 8.0.2.00300.

        """
        NETWORKS = None
        """
        Networks category includes network, opaqueNetwork,
        distributedVirtualPortgroup, distributedVirtualSwitch and legacyNetworkInfo
        within a vim.vm.ConfigTarget. This class attribute was added in vSphere API
        8.0.2.00300.

        """
        DEVICES = None
        """
        Devices category includes cdRom, serial, parallel, sound, usb, floppy,
        scsiPassthrough, pciPassthrough, sriov, vFlashModule and
        sharedGpuPassthroughTypes within a vim.vm.ConfigTarget. This class
        attribute was added in vSphere API 8.0.2.00300.

        """
        DISKS = None
        """
        Disks category includes scsiDisk and ideDisk within a vim.vm.ConfigTarget.
        This class attribute was added in vSphere API 8.0.2.00300.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ConfigTargetSpec` instance.
            """
            Enum.__init__(string)

    ConfigTargetSpec._set_values({
        'DATASTORES': ConfigTargetSpec('DATASTORES'),
        'NETWORKS': ConfigTargetSpec('NETWORKS'),
        'DEVICES': ConfigTargetSpec('DEVICES'),
        'DISKS': ConfigTargetSpec('DISKS'),
    })
    ConfigTargetSpec._set_binding_type(type.EnumType(
        'com.vmware.vcenter.environment_browser.config_targets.config_target_spec',
        ConfigTargetSpec))


    class GetParams(VapiStruct):
        """
        The ``ConfigTargets.GetParams`` class specifies the parameters for the
        :func:`ConfigTargets.get` method, such as which clusters to query. This
        class was added in vSphere API 8.0.2.00300.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     clusters=None,
                     filter=None,
                    ):
            """
            :type  clusters: :class:`set` of :class:`str` or ``None``
            :param clusters: A set of Cluster IDs that specify for which Clusters the
                configuration target is requested. This attribute was added in
                vSphere API 8.0.2.00300.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``ClusterComputeResource``. When methods return a value of this
                class as a return value, the attribute will contain identifiers for
                the resource type: ``ClusterComputeResource``.
                if None or empty an error will be returned. Ability to pass unset
                value is left for future expansion.
            :type  filter: :class:`set` of :class:`ConfigTargets.ConfigTargetSpec` or ``None``
            :param filter: Specify a filter to narrow the results. This attribute was added in
                vSphere API 8.0.2.00300.
                if None or empty, all information for a given config target is
                returned.
            """
            self.clusters = clusters
            self.filter = filter
            VapiStruct.__init__(self)


    GetParams._set_binding_type(type.StructType(
        'com.vmware.vcenter.environment_browser.config_targets.get_params', {
            'clusters': type.OptionalType(type.SetType(type.IdType())),
            'filter': type.OptionalType(type.SetType(type.ReferenceType(__name__, 'ConfigTargets.ConfigTargetSpec'))),
        },
        GetParams,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``ConfigTargets.Info`` class contains the result of the
        :func:`ConfigTargets.get` operation. Its main payload is a
        vim.vm.ConfigTarget matching the supplied filter. This class was added in
        vSphere API 8.0.2.00300.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     config_target=None,
                    ):
            """
            :type  config_target: :class:`vmware.vapi.struct.VapiStruct`
            :param config_target: A vim.vm.ConfigTarget matching the filter. This attribute was added
                in vSphere API 8.0.2.00300.
            """
            self.config_target = config_target
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.environment_browser.config_targets.info', {
            'config_target': type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct),
        },
        Info,
        False,
        None))



    def get(self,
            params,
            ):
        """
        Queries for information about a specific target, a "physical" device
        that can be used to back virtual devices. 
        
        The returned vim.vm.ConfigTarget specifies the set of values that can
        be used for device backings to connect the virtual machine to physical,
        or logical, host devices.  
        
        This method requires additional ``api_release`` request parameter which
        must be used to guarantee compatibility with future releases of the
        API. Consult the vSphere Automation SDKs Programming Guide for more
        information. . This method was added in vSphere API 8.0.2.00300.

        :type  params: :class:`ConfigTargets.GetParams`
        :param params: Search criteria and a filter to control the results.
        :rtype: :class:`ConfigTargets.Info`
        :return: The VI/JSON representation of ``ConfigTarget``
            (``vim.vm.ConfigTarget``) with the devices from the specified
            clusters.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if invalid search criteria or filter is provided
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if one or more of the specified clusters cannot be located.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges for all the
            specified clusters.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``ClusterComputeResource`` referenced by the
              attribute :attr:`ConfigTargets.GetParams.clusters` requires
              ``System.View``.
        """
        return self._invoke('get',
                            {
                            'params': params,
                            })
class _ConfigOptionDescriptorsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'params': type.ReferenceType(__name__, 'ConfigOptionDescriptors.ListParams'),
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
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/environment-browser/config-option-descriptors',
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
                'output_type': type.ReferenceType(__name__, 'ConfigOptionDescriptors.ListResult'),
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
            self, iface_name='com.vmware.vcenter.environment_browser.config_option_descriptors',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _ConfigOptionsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'params': type.ReferenceType(__name__, 'ConfigOptions.GetParams'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
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
            url_template='/vcenter/environment-browser/config-options',
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
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'ConfigOptions.Info'),
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
            self, iface_name='com.vmware.vcenter.environment_browser.config_options',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _ConfigTargetsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'params': type.ReferenceType(__name__, 'ConfigTargets.GetParams'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
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
            url_template='/vcenter/environment-browser/config-targets',
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
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'ConfigTargets.Info'),
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
            self, iface_name='com.vmware.vcenter.environment_browser.config_targets',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'ConfigOptionDescriptors': ConfigOptionDescriptors,
        'ConfigOptions': ConfigOptions,
        'ConfigTargets': ConfigTargets,
    }

