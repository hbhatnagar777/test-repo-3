# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.settings.depots.
#---------------------------------------------------------------------------

"""
The ``com.vmware.esx.settings.depots_client`` module provides classes to manage
VUM compatible ESX Depots.

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


class AffectedBaselineInfo(VapiStruct):
    """
    The ``AffectedBaselineInfo`` class contains the fields that describe which
    updates (bulletins) in the baseline will be affected by the depot to be
    deleted or disabled. This class was added in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 baseline=None,
                 id=None,
                 affected_updates=None,
                ):
        """
        :type  baseline: :class:`str`
        :param baseline: Name of the baseline affected. This attribute was added in vSphere
            API 7.0.3.0.
        :type  id: :class:`long`
        :param id: Identifier of the baseline affected. This attribute was added in
            vSphere API 7.0.3.0.
        :type  affected_updates: :class:`dict` of :class:`str` and :class:`UpdateSummary`
        :param affected_updates: Updates (bulletins) affected. They key is identifier of the update
            (bulletin). The value is summary of the update (bulletin). This
            attribute was added in vSphere API 7.0.3.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``com.vmware.esx.settings.depots.bulletin``. When methods
            return a value of this class as a return value, the key in the
            attribute :class:`dict` will be an identifier for the resource
            type: ``com.vmware.esx.settings.depots.bulletin``.
        """
        self.baseline = baseline
        self.id = id
        self.affected_updates = affected_updates
        VapiStruct.__init__(self)


AffectedBaselineInfo._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.affected_baseline_info', {
        'baseline': type.StringType(),
        'id': type.IntegerType(),
        'affected_updates': type.MapType(type.IdType(), type.ReferenceType(__name__, 'UpdateSummary')),
    },
    AffectedBaselineInfo,
    False,
    None))



class AffectedDesiredStateInfo(VapiStruct):
    """
    The ``AffectedDesiredStateInfo`` class contains the fields that describe
    which release units in the desired state will be affected by the depot to
    be deleted or disabled. This class was added in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 cluster_name=None,
                 cluster_id=None,
                 affected_base_image=None,
                 affected_addon=None,
                 affected_solutions=None,
                 affected_hardware_support=None,
                 affected_independent_components=None,
                ):
        """
        :type  cluster_name: :class:`str`
        :param cluster_name: Since now we have standalone host, we use entityName/entityId to
            better describe name/id of either cluster or standalone host. Name
            of the cluster the affected desired state belongs to. This
            attribute was added in vSphere API 7.0.3.0.
        :type  cluster_id: :class:`str`
        :param cluster_id: Identified of the cluster the affected desired state belongs to.
            This attribute was added in vSphere API 7.0.3.0.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``ClusterComputeResource``. When methods return a value of this
            class as a return value, the attribute will be an identifier for
            the resource type: ``ClusterComputeResource``.
        :type  affected_base_image: :class:`BaseImageVersion` or ``None``
        :param affected_base_image: Affected base image of the desired state. This attribute was added
            in vSphere API 7.0.3.0.
            If None, no base image of the desired state will be affected.
        :type  affected_addon: (:class:`dict` of :class:`str` and :class:`AddonSummary`) or ``None``
        :param affected_addon: Affected addon of the desired state. The key is name of addon.
            Note: there is at most one addon affected. This attribute was added
            in vSphere API 7.0.3.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``com.vmware.esx.settings.add_on``. When methods return a
            value of this class as a return value, the key in the attribute
            :class:`dict` will be an identifier for the resource type:
            ``com.vmware.esx.settings.add_on``.
            If None, no addon of the desired state will be affected.
        :type  affected_solutions: (:class:`dict` of :class:`str` and :class:`SolutionSummary`) or ``None``
        :param affected_solutions: Affected solutions of the desired state. The key is name of
            solution. This attribute was added in vSphere API 7.0.3.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``com.vmware.esx.settings.solution``. When methods return a
            value of this class as a return value, the key in the attribute
            :class:`dict` will be an identifier for the resource type:
            ``com.vmware.esx.settings.solution``.
            If None, no solution of the desired state will be affected.
        :type  affected_hardware_support: (:class:`dict` of :class:`str` and :class:`HardwareSupportManagerSummary`) or ``None``
        :param affected_hardware_support: Affected hardware support of the desired state. The key is HSM
            name. This attribute was added in vSphere API 7.0.3.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``com.vmware.esx.setting.hardware_support.manager``. When
            methods return a value of this class as a return value, the key in
            the attribute :class:`dict` will be an identifier for the resource
            type: ``com.vmware.esx.setting.hardware_support.manager``.
            If None, no hadrware support of the desired state will be affected.
        :type  affected_independent_components: (:class:`dict` of :class:`str` and :class:`ComponentSummary`) or ``None``
        :param affected_independent_components: Affected independent components of the desired state. The
            components belongs to other base images, addons, solutions and
            hardware support packages are not counted. The key is name of
            component. This attribute was added in vSphere API 7.0.3.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``com.vmware.esx.settings.component``. When methods return a
            value of this class as a return value, the key in the attribute
            :class:`dict` will be an identifier for the resource type:
            ``com.vmware.esx.settings.component``.
            If None, no independent components of the desired state will be
            affected.
        """
        self.cluster_name = cluster_name
        self.cluster_id = cluster_id
        self.affected_base_image = affected_base_image
        self.affected_addon = affected_addon
        self.affected_solutions = affected_solutions
        self.affected_hardware_support = affected_hardware_support
        self.affected_independent_components = affected_independent_components
        VapiStruct.__init__(self)


AffectedDesiredStateInfo._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.affected_desired_state_info', {
        'cluster_name': type.StringType(),
        'cluster_id': type.IdType(resource_types='ClusterComputeResource'),
        'affected_base_image': type.OptionalType(type.ReferenceType(__name__, 'BaseImageVersion')),
        'affected_addon': type.OptionalType(type.MapType(type.IdType(), type.ReferenceType(__name__, 'AddonSummary'))),
        'affected_solutions': type.OptionalType(type.MapType(type.IdType(), type.ReferenceType(__name__, 'SolutionSummary'))),
        'affected_hardware_support': type.OptionalType(type.MapType(type.IdType(), type.ReferenceType(__name__, 'HardwareSupportManagerSummary'))),
        'affected_independent_components': type.OptionalType(type.MapType(type.IdType(), type.ReferenceType(__name__, 'ComponentSummary'))),
    },
    AffectedDesiredStateInfo,
    False,
    None))



class UpdateSummary(VapiStruct):
    """
    The ``UpdateSummary`` class contains a fieldsthat describes the summary of
    an update (bulletin). This class was added in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 summary=None,
                ):
        """
        :type  summary: :class:`str`
        :param summary: Summary of the update (bulletin). This attribute was added in
            vSphere API 7.0.3.0.
        """
        self.summary = summary
        VapiStruct.__init__(self)


UpdateSummary._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.update_summary', {
        'summary': type.StringType(),
    },
    UpdateSummary,
    False,
    None))



class BaseImageVersion(VapiStruct):
    """
    The ``BaseImageVersion`` class contains fields that describe a specific
    ESXi base image. This class was added in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 version=None,
                 display_name=None,
                 display_version=None,
                ):
        """
        :type  version: :class:`str`
        :param version: Version of the base image. This attribute was added in vSphere API
            7.0.3.0.
        :type  display_name: :class:`str`
        :param display_name: Human readable name of the base image. This attribute was added in
            vSphere API 7.0.3.0.
        :type  display_version: :class:`str`
        :param display_version: Human readable version of the base image. This attribute was added
            in vSphere API 7.0.3.0.
        """
        self.version = version
        self.display_name = display_name
        self.display_version = display_version
        VapiStruct.__init__(self)


BaseImageVersion._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.base_image_version', {
        'version': type.StringType(),
        'display_name': type.StringType(),
        'display_version': type.StringType(),
    },
    BaseImageVersion,
    False,
    None))



class AddonVersion(VapiStruct):
    """
    The ``AddonVersion`` class contains fields that describe a specific version
    of an addon. This class was added in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 version=None,
                 display_version=None,
                ):
        """
        :type  version: :class:`str`
        :param version: Version of the addon. This attribute was added in vSphere API
            7.0.3.0.
        :type  display_version: :class:`str`
        :param display_version: Human readable version of the addon. This attribute was added in
            vSphere API 7.0.3.0.
        """
        self.version = version
        self.display_version = display_version
        VapiStruct.__init__(self)


AddonVersion._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.addon_version', {
        'version': type.StringType(),
        'display_version': type.StringType(),
    },
    AddonVersion,
    False,
    None))



class AddonSummary(VapiStruct):
    """
    The ``AddonSummary`` class contains fields that describe the summary of an
    addon. This class was added in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 display_name=None,
                 vendor=None,
                 versions=None,
                ):
        """
        :type  display_name: :class:`str`
        :param display_name: Human readable name of the addon. This attribute was added in
            vSphere API 7.0.3.0.
        :type  vendor: :class:`str`
        :param vendor: Vendor of the addon. This attribute was added in vSphere API
            7.0.3.0.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.esx.settings.depots.vendor``. When methods return a
            value of this class as a return value, the attribute will be an
            identifier for the resource type:
            ``com.vmware.esx.settings.depots.vendor``.
        :type  versions: :class:`list` of :class:`AddonVersion`
        :param versions: Different versions of the addon. This attribute was added in
            vSphere API 7.0.3.0.
        """
        self.display_name = display_name
        self.vendor = vendor
        self.versions = versions
        VapiStruct.__init__(self)


AddonSummary._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.addon_summary', {
        'display_name': type.StringType(),
        'vendor': type.IdType(resource_types='com.vmware.esx.settings.depots.vendor'),
        'versions': type.ListType(type.ReferenceType(__name__, 'AddonVersion')),
    },
    AddonSummary,
    False,
    None))



class SolutionVersion(VapiStruct):
    """
    The ``SolutionVersion`` class contains fields that describe a specific
    version of a solution. This class was added in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 version=None,
                 display_version=None,
                ):
        """
        :type  version: :class:`str`
        :param version: Version of the solution. This attribute was added in vSphere API
            7.0.3.0.
        :type  display_version: :class:`str`
        :param display_version: Human readable version of the solution. This attribute was added in
            vSphere API 7.0.3.0.
        """
        self.version = version
        self.display_version = display_version
        VapiStruct.__init__(self)


SolutionVersion._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.solution_version', {
        'version': type.StringType(),
        'display_version': type.StringType(),
    },
    SolutionVersion,
    False,
    None))



class SolutionSummary(VapiStruct):
    """
    The ``SolutionSummary`` class contains fields that describe the summary of
    a solution. This class was added in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 display_name=None,
                 versions=None,
                ):
        """
        :type  display_name: :class:`str`
        :param display_name: Human readable name of the solution. This attribute was added in
            vSphere API 7.0.3.0.
        :type  versions: :class:`list` of :class:`SolutionVersion`
        :param versions: Different versions of the solution. This attribute was added in
            vSphere API 7.0.3.0.
        """
        self.display_name = display_name
        self.versions = versions
        VapiStruct.__init__(self)


SolutionSummary._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.solution_summary', {
        'display_name': type.StringType(),
        'versions': type.ListType(type.ReferenceType(__name__, 'SolutionVersion')),
    },
    SolutionSummary,
    False,
    None))



class HardwareSupportPackageVersion(VapiStruct):
    """
    The ``HardwareSupportPackageVersion`` class contains fields that describe a
    specific version of a hardware support package (HSP). This class was added
    in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 version=None,
                ):
        """
        :type  version: :class:`str`
        :param version: Version of the HSP. This attribute was added in vSphere API
            7.0.3.0.
        """
        self.version = version
        VapiStruct.__init__(self)


HardwareSupportPackageVersion._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.hardware_support_package_version', {
        'version': type.StringType(),
    },
    HardwareSupportPackageVersion,
    False,
    None))



class HardwareSupportPackageSummary(VapiStruct):
    """
    The ``HardwareSupportPackageSummary`` class contains fields that describe
    the summary of a hardware support package (HSP). This class was added in
    vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 versions=None,
                ):
        """
        :type  versions: :class:`list` of :class:`HardwareSupportPackageVersion`
        :param versions: Different versions of the HSP. This attribute was added in vSphere
            API 7.0.3.0.
        """
        self.versions = versions
        VapiStruct.__init__(self)


HardwareSupportPackageSummary._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.hardware_support_package_summary', {
        'versions': type.ListType(type.ReferenceType(__name__, 'HardwareSupportPackageVersion')),
    },
    HardwareSupportPackageSummary,
    False,
    None))



class HardwareSupportManagerSummary(VapiStruct):
    """
    The ``HardwareSupportManagerSummary`` class contains fields that describe
    the summary of a hardware support manager (HSM). This class was added in
    vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 display_name=None,
                 packages=None,
                ):
        """
        :type  display_name: :class:`str`
        :param display_name: UI label for HSM, derived from HSM extension's description's
            'label' field. This attribute was added in vSphere API 7.0.3.0.
        :type  packages: :class:`dict` of :class:`str` and :class:`HardwareSupportPackageSummary`
        :param packages: Different hardware support packages (HSP) published by the HSM. The
            key is name of HSP. This attribute was added in vSphere API
            7.0.3.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``com.vmware.esx.setting.hardware_support.package``. When
            methods return a value of this class as a return value, the key in
            the attribute :class:`dict` will be an identifier for the resource
            type: ``com.vmware.esx.setting.hardware_support.package``.
        """
        self.display_name = display_name
        self.packages = packages
        VapiStruct.__init__(self)


HardwareSupportManagerSummary._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.hardware_support_manager_summary', {
        'display_name': type.StringType(),
        'packages': type.MapType(type.IdType(), type.ReferenceType(__name__, 'HardwareSupportPackageSummary')),
    },
    HardwareSupportManagerSummary,
    False,
    None))



class ComponentVersion(VapiStruct):
    """
    The ``ComponentVersion`` class contains fields that describe a specific
    version of a component. This class was added in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 version=None,
                 display_version=None,
                ):
        """
        :type  version: :class:`str`
        :param version: Version of the component. This attribute was added in vSphere API
            7.0.3.0.
        :type  display_version: :class:`str`
        :param display_version: Human readable version of the component. This attribute was added
            in vSphere API 7.0.3.0.
        """
        self.version = version
        self.display_version = display_version
        VapiStruct.__init__(self)


ComponentVersion._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.component_version', {
        'version': type.StringType(),
        'display_version': type.StringType(),
    },
    ComponentVersion,
    False,
    None))



class ComponentSummary(VapiStruct):
    """
    The ``ComponentSummary`` class contains fields that describe the summary of
    a component. This class was added in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 display_name=None,
                 versions=None,
                ):
        """
        :type  display_name: :class:`str`
        :param display_name: Human readable name of the component. This attribute was added in
            vSphere API 7.0.3.0.
        :type  versions: :class:`list` of :class:`ComponentVersion`
        :param versions: Different versions of the component. This attribute was added in
            vSphere API 7.0.3.0.
        """
        self.display_name = display_name
        self.versions = versions
        VapiStruct.__init__(self)


ComponentSummary._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.component_summary', {
        'display_name': type.StringType(),
        'versions': type.ListType(type.ReferenceType(__name__, 'ComponentVersion')),
    },
    ComponentSummary,
    False,
    None))



class MetadataInfo(VapiStruct):
    """
    The ``MetadataInfo`` class contains fields that show the content of a
    metadata bundle. This class was added in vSphere API 7.0.3.0.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 file_name=None,
                 base_images=None,
                 addons=None,
                 solutions=None,
                 hardware_support=None,
                 independent_components=None,
                 updates=None,
                ):
        """
        :type  file_name: :class:`str`
        :param file_name: File name of the metadata bundle. This attribute was added in
            vSphere API 7.0.3.0.
        :type  base_images: :class:`list` of :class:`BaseImageVersion` or ``None``
        :param base_images: All the base images contained in the metadata bundle. This
            attribute was added in vSphere API 7.0.3.0.
            If None, the metadata bundle contains no base image.
        :type  addons: (:class:`dict` of :class:`str` and :class:`AddonSummary`) or ``None``
        :param addons: All the addons contained in the metadata bundle. The key is name of
            addon. This attribute was added in vSphere API 7.0.3.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``com.vmware.esx.settings.add_on``. When methods return a
            value of this class as a return value, the key in the attribute
            :class:`dict` will be an identifier for the resource type:
            ``com.vmware.esx.settings.add_on``.
            If None, the metadata bundle contains no addon.
        :type  solutions: (:class:`dict` of :class:`str` and :class:`SolutionSummary`) or ``None``
        :param solutions: All the solutions contained in the metadata bundle. The key is name
            of solution. This attribute was added in vSphere API 7.0.3.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``com.vmware.esx.settings.solution``. When methods return a
            value of this class as a return value, the key in the attribute
            :class:`dict` will be an identifier for the resource type:
            ``com.vmware.esx.settings.solution``.
            If None, the metadata bundle contains no solution.
        :type  hardware_support: (:class:`dict` of :class:`str` and :class:`HardwareSupportManagerSummary`) or ``None``
        :param hardware_support: All the HSMs and their HSPs contained in the metadata bundle. The
            key is name of HSM. This attribute was added in vSphere API
            7.0.3.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``com.vmware.esx.setting.hardware_support.manager``. When
            methods return a value of this class as a return value, the key in
            the attribute :class:`dict` will be an identifier for the resource
            type: ``com.vmware.esx.setting.hardware_support.manager``.
            If None, the metadata bundle contains no hardware support manager.
        :type  independent_components: (:class:`dict` of :class:`str` and :class:`ComponentSummary`) or ``None``
        :param independent_components: All the independent components contained in the metadata bundle.
            The components belongs to other base images, addons, solutions and
            hardware support packages are not counted. The ksy is name of
            component. This attribute was added in vSphere API 7.0.3.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``com.vmware.esx.settings.component``. When methods return a
            value of this class as a return value, the key in the attribute
            :class:`dict` will be an identifier for the resource type:
            ``com.vmware.esx.settings.component``.
            If None, the metadata bundle contains no inpendent component.
        :type  updates: (:class:`dict` of :class:`str` and :class:`UpdateSummary`) or ``None``
        :param updates: All the updates (bulletins) contained in the metadata bundle. They
            key is identifier of the update (bulletin). The value is summary of
            the update (bulletin). This attribute was added in vSphere API
            7.0.3.0.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type: ``com.vmware.esx.settings.depots.bulletin``. When methods
            return a value of this class as a return value, the key in the
            attribute :class:`dict` will be an identifier for the resource
            type: ``com.vmware.esx.settings.depots.bulletin``.
            If None, the metadata bundle contains no update (bulletin).
        """
        self.file_name = file_name
        self.base_images = base_images
        self.addons = addons
        self.solutions = solutions
        self.hardware_support = hardware_support
        self.independent_components = independent_components
        self.updates = updates
        VapiStruct.__init__(self)


MetadataInfo._set_binding_type(type.StructType(
    'com.vmware.esx.settings.depots.metadata_info', {
        'file_name': type.StringType(),
        'base_images': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'BaseImageVersion'))),
        'addons': type.OptionalType(type.MapType(type.IdType(), type.ReferenceType(__name__, 'AddonSummary'))),
        'solutions': type.OptionalType(type.MapType(type.IdType(), type.ReferenceType(__name__, 'SolutionSummary'))),
        'hardware_support': type.OptionalType(type.MapType(type.IdType(), type.ReferenceType(__name__, 'HardwareSupportManagerSummary'))),
        'independent_components': type.OptionalType(type.MapType(type.IdType(), type.ReferenceType(__name__, 'ComponentSummary'))),
        'updates': type.OptionalType(type.MapType(type.IdType(), type.ReferenceType(__name__, 'UpdateSummary'))),
    },
    MetadataInfo,
    False,
    None))



class Offline(VapiInterface):
    """
    The ``Offline`` class provides methods to manage offline software depots
    used during ESX lifecycle management.
    """
    RESOURCE_TYPE = "com.vmware.esx.settings.depots.offline"
    """
    Resource type for depots resource

    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.depots.offline'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _OfflineStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'create_task': 'create$task'})
        self._VAPI_OPERATION_IDS.update({'delete_task': 'delete$task'})
        self._VAPI_OPERATION_IDS.update({'create_from_host_task': 'create_from_host$task'})

    class SourceType(Enum):
        """
        The ``Offline.SourceType`` class defines possible values of sources for the
        offline depot.

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
        {\\\\@link CreateSpec#location) can be http, https or file.

        """
        PUSH = None
        """
        Content was previously uploaded using the file upload enpoint present on
        vCenter appliance. This endpoint is present at
        https://VCENTERFQDN:9087/vum-fileupload URL.

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
    })
    SourceType._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.depots.offline.source_type',
        SourceType))


    class CreateSpec(VapiStruct):
        """
        The ``Offline.CreateSpec`` class defines the information used to create a
        depot.

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
                }
            ),
        ]



        def __init__(self,
                     description=None,
                     source_type=None,
                     location=None,
                     file_id=None,
                     ownerdata=None,
                    ):
            """
            :type  description: :class:`str` or ``None``
            :param description: Description of the depot.
                If None, the description will be empty.
            :type  source_type: :class:`Offline.SourceType`
            :param source_type: Type of the source from which offline bundle is obtained.
            :type  location: :class:`str`
            :param location: Location of the depot from which content should be retrieved.
                This attribute is optional and it is only relevant when the value
                of ``sourceType`` is :attr:`Offline.SourceType.PULL`.
            :type  file_id: :class:`str`
            :param file_id: File identifier returned by the file upload endpoint after file is
                uploaded.
                This attribute is optional and it is only relevant when the value
                of ``sourceType`` is :attr:`Offline.SourceType.PUSH`.
            :type  ownerdata: :class:`str` or ``None``
            :param ownerdata: Private data saved by the :attr:`Offline.Info.owner` of the depot.
                It is opaque to vLCM. This attribute was added in vSphere API
                7.0.3.0.
                If None, no ownerdata will be saved.
            """
            self.description = description
            self.source_type = source_type
            self.location = location
            self.file_id = file_id
            self.ownerdata = ownerdata
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.offline.create_spec', {
            'description': type.OptionalType(type.StringType()),
            'source_type': type.ReferenceType(__name__, 'Offline.SourceType'),
            'location': type.OptionalType(type.URIType()),
            'file_id': type.OptionalType(type.StringType()),
            'ownerdata': type.OptionalType(type.StringType()),
        },
        CreateSpec,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Offline.Info`` class defines the information regarding an offline
        depot.

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
                }
            ),
        ]



        def __init__(self,
                     description=None,
                     source_type=None,
                     location=None,
                     file_id=None,
                     create_time=None,
                     owner=None,
                     ownerdata=None,
                    ):
            """
            :type  description: :class:`str`
            :param description: Description of the depot. If not set during import, it will be
                empty.
            :type  source_type: :class:`Offline.SourceType`
            :param source_type: Type of the source from which offline depot is obtained.
            :type  location: :class:`str`
            :param location: Location of the depot from which content is retrieved.
                This attribute is optional and it is only relevant when the value
                of ``sourceType`` is :attr:`Offline.SourceType.PULL`.
            :type  file_id: :class:`str`
            :param file_id: File identifier returned by the file upload endpoint after file is
                uploaded.
                This attribute is optional and it is only relevant when the value
                of ``sourceType`` is :attr:`Offline.SourceType.PUSH`.
            :type  create_time: :class:`datetime.datetime`
            :param create_time: Time when the depot was created.
            :type  owner: :class:`str` or ``None``
            :param owner: Name of the user creating the depot. This attribute was added in
                vSphere API 7.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  ownerdata: :class:`str` or ``None``
            :param ownerdata: Private data saved by the ``owner`` of depot. It is opaque to vLCM.
                This attribute was added in vSphere API 7.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.description = description
            self.source_type = source_type
            self.location = location
            self.file_id = file_id
            self.create_time = create_time
            self.owner = owner
            self.ownerdata = ownerdata
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.offline.info', {
            'description': type.StringType(),
            'source_type': type.ReferenceType(__name__, 'Offline.SourceType'),
            'location': type.OptionalType(type.URIType()),
            'file_id': type.OptionalType(type.StringType()),
            'create_time': type.DateTimeType(),
            'owner': type.OptionalType(type.StringType()),
            'ownerdata': type.OptionalType(type.StringType()),
        },
        Info,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``Offline.Summary`` class defines the summary information regarding an
        offline depot.

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
                }
            ),
        ]



        def __init__(self,
                     description=None,
                     source_type=None,
                     location=None,
                     file_id=None,
                     owner=None,
                     ownerdata=None,
                    ):
            """
            :type  description: :class:`str`
            :param description: Description of the depot. If not set during import, it will be
                empty.
            :type  source_type: :class:`Offline.SourceType`
            :param source_type: Type of the source from which offline depot is obtained.
            :type  location: :class:`str`
            :param location: Location of the depot from which content is retrieved.
                This attribute is optional and it is only relevant when the value
                of ``sourceType`` is :attr:`Offline.SourceType.PULL`.
            :type  file_id: :class:`str`
            :param file_id: File identifier returned by the file upload endpoint after file is
                uploaded.
                This attribute is optional and it is only relevant when the value
                of ``sourceType`` is :attr:`Offline.SourceType.PUSH`.
            :type  owner: :class:`str` or ``None``
            :param owner: Name of the user creating the depot. This attribute was added in
                vSphere API 7.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  ownerdata: :class:`str` or ``None``
            :param ownerdata: Private data saved by the ``owner`` of depot. It is opaque to vLCM.
                This attribute was added in vSphere API 7.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.description = description
            self.source_type = source_type
            self.location = location
            self.file_id = file_id
            self.owner = owner
            self.ownerdata = ownerdata
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.offline.summary', {
            'description': type.StringType(),
            'source_type': type.ReferenceType(__name__, 'Offline.SourceType'),
            'location': type.OptionalType(type.URIType()),
            'file_id': type.OptionalType(type.StringType()),
            'owner': type.OptionalType(type.StringType()),
            'ownerdata': type.OptionalType(type.StringType()),
        },
        Summary,
        False,
        None))


    class CreateResult(VapiStruct):
        """
        The ``Offline.CreateResult`` class defines the result information for a new
        offline depot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     depot=None,
                    ):
            """
            :type  depot: :class:`str`
            :param depot: Identifier of the offline depot.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.esx.settings.depots.offline``. When methods return a
                value of this class as a return value, the attribute will be an
                identifier for the resource type:
                ``com.vmware.esx.settings.depots.offline``.
            """
            self.depot = depot
            VapiStruct.__init__(self)


    CreateResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.offline.create_result', {
            'depot': type.IdType(resource_types='com.vmware.esx.settings.depots.offline'),
        },
        CreateResult,
        False,
        None))


    class HostCredentials(VapiStruct):
        """
        The ``Offline.HostCredentials`` class contains attributes that describe the
        host's username, password, port number, ssl thumbprint or ssl certificate
        to be used when connecting to the host using USERNAME_PASSWORD option in
        the  class. This class was added in vSphere API 7.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     host_name=None,
                     user_name=None,
                     password=None,
                     port=None,
                     ssl_thumb_print=None,
                    ):
            """
            :type  host_name: :class:`str`
            :param host_name: The IP address or DNS resolvable name of the host. This attribute
                was added in vSphere API 7.0.2.0.
            :type  user_name: :class:`str`
            :param user_name: Specifies the username to be used during the
                :func:`Offline.create_from_host` method. This attribute was added
                in vSphere API 7.0.2.0.
            :type  password: :class:`str`
            :param password: Specifies the password to be used during the
                :func:`Offline.create_from_host` method. This attribute was added
                in vSphere API 7.0.2.0.
            :type  port: :class:`long` or ``None``
            :param port: Specifies the port number of the host to be used during
                :func:`Offline.create_from_host` method. This attribute was added
                in vSphere API 7.0.2.0.
                If None, port number is set to 443.
            :type  ssl_thumb_print: :class:`str` or ``None``
            :param ssl_thumb_print: Specifies the sslThumbPrint of the host to be used during
                :func:`Offline.create_from_host` method SHA1 hash of the host's SSL
                certificate. This attribute was added in vSphere API 7.0.2.0.
                If None, :func:`Offline.create_from_host` method this operation
                will throw UnverifiedPeer with the host provided thumbprint as
                data.
            """
            self.host_name = host_name
            self.user_name = user_name
            self.password = password
            self.port = port
            self.ssl_thumb_print = ssl_thumb_print
            VapiStruct.__init__(self)


    HostCredentials._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.offline.host_credentials', {
            'host_name': type.StringType(),
            'user_name': type.StringType(),
            'password': type.SecretType(),
            'port': type.OptionalType(type.IntegerType()),
            'ssl_thumb_print': type.OptionalType(type.StringType()),
        },
        HostCredentials,
        False,
        None))


    class ConnectionSpec(VapiStruct):
        """
        The ``Offline.ConnectionSpec`` class contains attributes that describe the
        specification to be used for connecting to the host during the
        :func:`Offline.create_from_host` method. This class was added in vSphere
        API 7.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'auth_type',
                {
                    'USERNAME_PASSWORD' : [('host_credential', True)],
                    'EXISTING' : [('host', True)],
                }
            ),
        ]



        def __init__(self,
                     auth_type=None,
                     host_credential=None,
                     host=None,
                    ):
            """
            :type  auth_type: :class:`Offline.ConnectionSpec.AuthenticationType`
            :param auth_type: Specifies what type of authentication (USERNAME_PASSWORD, EXISTING)
                is to be used when connecting with the host. USERNAME_PASSWORD is
                intended to be used when connecting to a host that is not currently
                part of the vCenter inventory. EXISTING is intented for hosts that
                are in vCenter inventory, in which case, HostServiceTicket will be
                used to connect to the host. This attribute was added in vSphere
                API 7.0.2.0.
            :type  host_credential: :class:`Offline.HostCredentials`
            :param host_credential: Specifies the host details to be used during the
                :func:`Offline.create_from_host` method. This attribute was added
                in vSphere API 7.0.2.0.
                This attribute is optional and it is only relevant when the value
                of ``authType`` is
                :attr:`Offline.ConnectionSpec.AuthenticationType.USERNAME_PASSWORD`.
            :type  host: :class:`str`
            :param host: Specifies the host Managed Object ID to be used during the
                :func:`Offline.create_from_host` method. This attribute was added
                in vSphere API 7.0.2.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``HostSystem``. When methods return a value of this class as a
                return value, the attribute will be an identifier for the resource
                type: ``HostSystem``.
                This attribute is optional and it is only relevant when the value
                of ``authType`` is
                :attr:`Offline.ConnectionSpec.AuthenticationType.EXISTING`.
            """
            self.auth_type = auth_type
            self.host_credential = host_credential
            self.host = host
            VapiStruct.__init__(self)


        class AuthenticationType(Enum):
            """
            The ``Offline.ConnectionSpec.AuthenticationType`` class defines the
            possible types of authentication supported when connecting to the host.
            This enumeration was added in vSphere API 7.0.2.0.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            USERNAME_PASSWORD = None
            """
            Connect to host using host's credentials  class. This class attribute was
            added in vSphere API 7.0.2.0.

            """
            EXISTING = None
            """
            Connect to the host using service ticket. Note: This is supported only for
            hosts present in the VC inventory. This class attribute was added in
            vSphere API 7.0.2.0.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`AuthenticationType` instance.
                """
                Enum.__init__(string)

        AuthenticationType._set_values({
            'USERNAME_PASSWORD': AuthenticationType('USERNAME_PASSWORD'),
            'EXISTING': AuthenticationType('EXISTING'),
        })
        AuthenticationType._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.depots.offline.connection_spec.authentication_type',
            AuthenticationType))

    ConnectionSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.offline.connection_spec', {
            'auth_type': type.ReferenceType(__name__, 'Offline.ConnectionSpec.AuthenticationType'),
            'host_credential': type.OptionalType(type.ReferenceType(__name__, 'Offline.HostCredentials')),
            'host': type.OptionalType(type.IdType()),
        },
        ConnectionSpec,
        False,
        None))


    class DepotExtractInfo(VapiStruct):
        """
        The ``Offline.DepotExtractInfo`` class contains attributes that describe
        the extracted depot. This class was added in vSphere API 7.0.2.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     notifications=None,
                     software_spec=None,
                     result=None,
                    ):
            """
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications`
            :param notifications: Notifications returned by the extractDepot operation. This
                attribute was added in vSphere API 7.0.2.0.
            :type  software_spec: :class:`com.vmware.esx.settings_client.SoftwareSpec`
            :param software_spec: Software specification of the extracted depot. This attribute was
                added in vSphere API 7.0.2.0.
            :type  result: :class:`Offline.CreateResult`
            :param result: The information about the created offline depot. Empty
                \\\\@name{result} \\\\@term{string} indicates that the depot
                contents are already present in VC cache. This attribute was added
                in vSphere API 7.0.2.0.
            """
            self.notifications = notifications
            self.software_spec = software_spec
            self.result = result
            VapiStruct.__init__(self)


    DepotExtractInfo._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.offline.depot_extract_info', {
            'notifications': type.ReferenceType('com.vmware.esx.settings_client', 'Notifications'),
            'software_spec': type.ReferenceType('com.vmware.esx.settings_client', 'SoftwareSpec'),
            'result': type.ReferenceType(__name__, 'Offline.CreateResult'),
        },
        DepotExtractInfo,
        False,
        None))


    class PrecheckResult(VapiStruct):
        """
        The ``Offline.PrecheckResult`` class contains the fields that show the
        details of affected baselines and desired states found in
        :func:`Offline.delete` method. This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     affected_baselines=None,
                     affected_desired_states=None,
                    ):
            """
            :type  affected_baselines: :class:`list` of :class:`AffectedBaselineInfo` or ``None``
            :param affected_baselines: Baselines affected. This attribute was added in vSphere API
                7.0.3.0.
                If None, no baseline is affected.
            :type  affected_desired_states: :class:`list` of :class:`AffectedDesiredStateInfo` or ``None``
            :param affected_desired_states: Desired states affected. This attribute was added in vSphere API
                7.0.3.0.
                If None, no desired state is affected.
            """
            self.affected_baselines = affected_baselines
            self.affected_desired_states = affected_desired_states
            VapiStruct.__init__(self)


    PrecheckResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.offline.precheck_result', {
            'affected_baselines': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'AffectedBaselineInfo'))),
            'affected_desired_states': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'AffectedDesiredStateInfo'))),
        },
        PrecheckResult,
        False,
        None))


    class DeleteResult(VapiStruct):
        """
        The ``Offline.DeleteResult`` class contains a field that lists all the
        errors encountered after starting the task of :func:`Offline.delete`
        method. This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     notifications=None,
                    ):
            """
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
            :param notifications: Notifications returned by :func:`Offline.delete` method. This
                attribute was added in vSphere API 7.0.3.0.
                If None, no notification is returned.
            """
            self.notifications = notifications
            VapiStruct.__init__(self)


    DeleteResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.offline.delete_result', {
            'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        DeleteResult,
        False,
        None))



    def get(self,
            depot,
            ):
        """
        Gets the information about an imported offline software depot.

        :type  depot: :class:`str`
        :param depot: Identifier for the depot.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.depots.offline``.
        :rtype: :class:`Offline.Info`
        :return: Information about the imported offline software depot.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no depot with given identifier ``depot`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleSettings.Read``.
        """
        return self._invoke('get',
                            {
                            'depot': depot,
                            })

    def list(self):
        """
        Returns currently imported offline software depots.


        :rtype: :class:`dict` of :class:`str` and :class:`Offline.Summary`
        :return: Map of currently imported offline software depots keyed by their
            identifier.
            The key in the return value :class:`dict` will be an identifier for
            the resource type: ``com.vmware.esx.settings.depots.offline``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleSettings.Read``.
        """
        return self._invoke('list', None)


    def create_task(self,
               spec,
               ):
        """
        Imports a new offline software depot. This will also import the
        metadata and payloads from this offline depot. The returned task will
        fail and no offline depot would be created if there are any issues
        during import. The result of this operation can be queried by calling
        the cis/tasks/{task-id} where the task-id is the response of this
        operation. 
        
        **Warning:** Using HTTP is not secure. Please use HTTPS URLs instead.

        :type  spec: :class:`Offline.CreateSpec`
        :param spec: Specification to import an offline depot.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If an invalid :attr:`Offline.CreateSpec.location` is provided.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            If the depot content already exists. The value of the data
            attribute of :class:`com.vmware.vapi.std.errors_client.Error` will
            be a class that contains existing depot identifier as part of depot
            attribute defined in :class:`Offline.CreateResult`.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        """
        task_id = self._invoke('create$task',
                                {
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Offline.CreateResult'))
        return task_instance

    def delete(self,
               depot,
               ):
        """
        
        
        The task-based ``delete`` method removes content of an imported offline
        depot from vLCM completely. 
        
        Note: The non task-based ``delete`` method has been deprecated. It
        deletes only the record of depot from the list of imported offline
        software depots, instead of removing the depot's content from vLCM.

        :type  depot: :class:`str`
        :param depot: Identifier of the depot to be removed.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.depots.offline``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the given depot is system-defined. This error is applicable to
            the task-based ``delete`` method only.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no depot associated with parameter ``depot`` in the
            system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            If the content of depot to be deleted is used in some baseline or
            desired state. The value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            PrecheckResult class that lists the information of affected
            baselines and desired states. This error is applicable to the
            task-based ``delete`` method only.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there some unknown internal error. The accompanying error
            message will give more details about the failure. For task-based
            ``delete`` method, once the task is started, it does NOT stop if
            encountering an error. Instead, it will continuously run to
            completion. In this case, the value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            DeleteResult class that lists all the errors encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleDepots.Delete``.
        """
        return self._invoke('delete',
                            {
                            'depot': depot,
                            })

    def delete_task(self,
               depot,
               ):
        """
        
        
        The task-based ``delete`` method removes content of an imported offline
        depot from vLCM completely. 
        
        Note: The non task-based ``delete`` method has been deprecated. It
        deletes only the record of depot from the list of imported offline
        software depots, instead of removing the depot's content from vLCM.

        :type  depot: :class:`str`
        :param depot: Identifier of the depot to be removed.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.depots.offline``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the given depot is system-defined. This error is applicable to
            the task-based ``delete`` method only.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no depot associated with parameter ``depot`` in the
            system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            If the content of depot to be deleted is used in some baseline or
            desired state. The value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            PrecheckResult class that lists the information of affected
            baselines and desired states. This error is applicable to the
            task-based ``delete`` method only.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there some unknown internal error. The accompanying error
            message will give more details about the failure. For task-based
            ``delete`` method, once the task is started, it does NOT stop if
            encountering an error. Instead, it will continuously run to
            completion. In this case, the value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            DeleteResult class that lists all the errors encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleDepots.Delete``.
        """
        task_id = self._invoke('delete$task',
                                {
                                'depot': depot,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.VoidType())
        return task_instance


    def create_from_host_task(self,
                         spec,
                         ):
        """
        
        
        Extract the current software specification applied to the host and
        import it into the depot. Returns details about the current software
        specification applied to the host. 
        
        The result of this operation can be queried by calling the
        cis/tasks/{task-id} where the task-id is the response of this
        operation.. This method was added in vSphere API 7.0.2.0.

        :type  spec: :class:`Offline.ConnectionSpec`
        :param spec: ConnectionSpec connection spec for the host.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the :class:`Offline.HostCredentials` attribute of ``spec`` is
            invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no :attr:`Offline.HostCredentials.host_name` attribute
            associated with host id in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.UnverifiedPeer` 
            If the SSL certificate of the target node cannot be validated by
            comparing with the thumbprint provided in
            ConnectionSpec.HostCredentials#sslThumbPrint or the full
            certificate provided in
            ConnectionSpec.HostCredentials#sslCertificate.
        """
        task_id = self._invoke('create_from_host$task',
                                {
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Offline.DepotExtractInfo'))
        return task_instance
class Online(VapiInterface):
    """
    The ``Online`` class provides methods to manage online software depots used
    during ESX lifecycle management.
    """
    RESOURCE_TYPE = "com.vmware.esx.settings.depots.online"
    """
    Resource type for depots resource

    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.depots.online'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _OnlineStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'delete_task': 'delete$task'})
        self._VAPI_OPERATION_IDS.update({'flush_task': 'flush$task'})

    class CreateSpec(VapiStruct):
        """
        The ``Online.CreateSpec`` class defines the information used to create a
        depot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     description=None,
                     location=None,
                     enabled=None,
                     ownerdata=None,
                    ):
            """
            :type  description: :class:`str` or ``None``
            :param description: Description of the depot.
                If None, the description will be empty.
            :type  location: :class:`str`
            :param location: Location of the depot. It should be the location to the index.xml
                for the depot.
            :type  enabled: :class:`bool` or ``None``
            :param enabled: Flag indicating whether this depot is enabled or not. Disabling the
                depot doesn't delete its cached metadata and payloads. It will not
                be refreshed next time depots are re-synced.
                If None, the depot will be enabled.
            :type  ownerdata: :class:`str` or ``None``
            :param ownerdata: Private data saved by the :attr:`Online.Info.owner` of the depot.
                It is opaque to vLCM. This attribute was added in vSphere API
                7.0.3.0.
                If None, no ownerdata will be saved.
            """
            self.description = description
            self.location = location
            self.enabled = enabled
            self.ownerdata = ownerdata
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.online.create_spec', {
            'description': type.OptionalType(type.StringType()),
            'location': type.URIType(),
            'enabled': type.OptionalType(type.BooleanType()),
            'ownerdata': type.OptionalType(type.StringType()),
        },
        CreateSpec,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Online.Info`` class defines the information regarding a depot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     description=None,
                     location=None,
                     enabled=None,
                     system_defined=None,
                     owner=None,
                     ownerdata=None,
                    ):
            """
            :type  description: :class:`str`
            :param description: Description of the depot. It will be an empty string if no
                description was provided during create.
            :type  location: :class:`str`
            :param location: Location of the depot.
            :type  enabled: :class:`bool`
            :param enabled: Flag indicating whether this depot is enabled or not.
            :type  system_defined: :class:`bool`
            :param system_defined: Flag to indicate if the depot is system defined. System defined
                depot can not be deleted.
            :type  owner: :class:`str` or ``None``
            :param owner: Name of the user creating the depot. This attribute was added in
                vSphere API 7.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  ownerdata: :class:`str` or ``None``
            :param ownerdata: Private data saved by the ``owner`` of depot. It is opaque to vLCM.
                This attribute was added in vSphere API 7.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.description = description
            self.location = location
            self.enabled = enabled
            self.system_defined = system_defined
            self.owner = owner
            self.ownerdata = ownerdata
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.online.info', {
            'description': type.StringType(),
            'location': type.URIType(),
            'enabled': type.BooleanType(),
            'system_defined': type.BooleanType(),
            'owner': type.OptionalType(type.StringType()),
            'ownerdata': type.OptionalType(type.StringType()),
        },
        Info,
        False,
        None))


    class Summary(VapiStruct):
        """
        The ``Online.Summary`` class defines the summary information regarding a
        depot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     description=None,
                     location=None,
                     enabled=None,
                     system_defined=None,
                     owner=None,
                     ownerdata=None,
                    ):
            """
            :type  description: :class:`str`
            :param description: Description of the depot. It will be an empty string if no
                description was provided during create.
            :type  location: :class:`str`
            :param location: Location of the depot.
            :type  enabled: :class:`bool`
            :param enabled: Flag indicating whether this depot is enabled or not.
            :type  system_defined: :class:`bool`
            :param system_defined: Flag to indicate if the depot is system defined. System defined
                depot can not be deleted.
            :type  owner: :class:`str` or ``None``
            :param owner: Name of the user creating the depot. This attribute was added in
                vSphere API 7.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            :type  ownerdata: :class:`str` or ``None``
            :param ownerdata: Private data saved by the ``owner`` of depot. It is opaque to vLCM.
                This attribute was added in vSphere API 7.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.description = description
            self.location = location
            self.enabled = enabled
            self.system_defined = system_defined
            self.owner = owner
            self.ownerdata = ownerdata
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.online.summary', {
            'description': type.StringType(),
            'location': type.URIType(),
            'enabled': type.BooleanType(),
            'system_defined': type.BooleanType(),
            'owner': type.OptionalType(type.StringType()),
            'ownerdata': type.OptionalType(type.StringType()),
        },
        Summary,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``Online.UpdateSpec`` class defines the information used to update the
        depot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     enabled=None,
                     description=None,
                    ):
            """
            :type  enabled: :class:`bool` or ``None``
            :param enabled: Flag indicating whether this depot is enabled or not. Disabling the
                depot doesn't delete its cached metadata and payloads. It will not
                be refreshed next time depots are re-synced.
                If None, enabled flag is not updated.
            :type  description: :class:`str` or ``None``
            :param description: Description of the depot.
                If None, description is not updated.
            """
            self.enabled = enabled
            self.description = description
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.online.update_spec', {
            'enabled': type.OptionalType(type.BooleanType()),
            'description': type.OptionalType(type.StringType()),
        },
        UpdateSpec,
        False,
        None))


    class PrecheckResult(VapiStruct):
        """
        The ``Online.PrecheckResult`` class contains the fields that show the
        details of affected baselines and desired states found in
        :func:`Online.delete` or :func:`Online.flush` operation. This class was
        added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     affected_baselines=None,
                     affected_desired_states=None,
                    ):
            """
            :type  affected_baselines: :class:`list` of :class:`AffectedBaselineInfo` or ``None``
            :param affected_baselines: Baselines affected. This attribute was added in vSphere API
                7.0.3.0.
                If None, no baseline is affected.
            :type  affected_desired_states: :class:`list` of :class:`AffectedDesiredStateInfo` or ``None``
            :param affected_desired_states: Desired states affected. This attribute was added in vSphere API
                7.0.3.0.
                If None, no desired state is affected.
            """
            self.affected_baselines = affected_baselines
            self.affected_desired_states = affected_desired_states
            VapiStruct.__init__(self)


    PrecheckResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.online.precheck_result', {
            'affected_baselines': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'AffectedBaselineInfo'))),
            'affected_desired_states': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'AffectedDesiredStateInfo'))),
        },
        PrecheckResult,
        False,
        None))


    class DeleteResult(VapiStruct):
        """
        The ``Online.DeleteResult`` class contains a field that lists all the
        errors encountered after starting the task of :func:`Online.delete` method.
        This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     notifications=None,
                    ):
            """
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
            :param notifications: Notifications returned by :func:`Online.delete` method. This
                attribute was added in vSphere API 7.0.3.0.
                If None, no notification is returned.
            """
            self.notifications = notifications
            VapiStruct.__init__(self)


    DeleteResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.online.delete_result', {
            'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        DeleteResult,
        False,
        None))


    class FlushResult(VapiStruct):
        """
        The ``Online.FlushResult`` class contains a field that lists all the errors
        encountered after starting the task of :func:`Online.flush` method. This
        class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     notifications=None,
                    ):
            """
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
            :param notifications: Notifications returned by :func:`Online.flush` method. This
                attribute was added in vSphere API 7.0.3.0.
                If None, no notification is returned.
            """
            self.notifications = notifications
            VapiStruct.__init__(self)


    FlushResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.online.flush_result', {
            'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        FlushResult,
        False,
        None))



    def list(self):
        """
        Returns a list of currently configured online software depots.


        :rtype: :class:`dict` of :class:`str` and :class:`Online.Summary`
        :return: Map of currently configured online software depots keyed by their
            identifiers.
            The key in the return value :class:`dict` will be an identifier for
            the resource type: ``com.vmware.esx.settings.depots.online``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleSettings.Read``.
        """
        return self._invoke('list', None)

    def get(self,
            depot,
            ):
        """
        Gets the information about a currently configured online software
        depot.

        :type  depot: :class:`str`
        :param depot: Identifier for the depot.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.depots.online``.
        :rtype: :class:`Online.Info`
        :return: Information of the currently configured online software depot.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no depot with given identifier ``depot`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleSettings.Read``.
        """
        return self._invoke('get',
                            {
                            'depot': depot,
                            })

    def create(self,
               spec,
               ):
        """
        Adds a new online software depot to the list of currently configured
        online software depots. 
        
        **Warning:** Using HTTP is not secure. Please use HTTPS URLs instead.

        :type  spec: :class:`Online.CreateSpec`
        :param spec: Depot information.
        :rtype: :class:`str`
        :return: Identifier of the currently configured online depot.
            The return value will be an identifier for the resource type:
            ``com.vmware.esx.settings.depots.online``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If an invalid location is provided.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            If depot with given location already exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSettings.Write``.
        """
        return self._invoke('create',
                            {
                            'spec': spec,
                            })

    def delete(self,
               depot,
               ):
        """
        The task-based ``delete`` method removes content of a user-imported
        online depot from vLCM completely. As a result, the URL of the
        user-imported online depot will also be removed. 
        
        Note: 
        
        1. To remove content of system-defined online depots, use ``flush``
        method. 
        
        2. The non task-based ``delete`` method has been deprecated. It only
        deletes the record of depot from the list of imported online software
        depots, instead of removing the depot's content from the system.

        :type  depot: :class:`str`
        :param depot: Identifier of the depot to be removed.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.depots.online``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the given depot is system-defined. This error is applicable to
            the task-based ``delete`` method only.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no depot associated with parameter ``depot`` in the
            system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            If the content of depot to be deleted is used in some baseline or
            desired state. 
            
            The value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            PrecheckResult class that lists the information of affected
            baselines and desired states. 
            
            This error is applicable to the task-based ``delete`` method only.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there some unknown internal error. 
            
            The accompanying error message will give more details about the
            failure. 
            
            For task-based ``delete`` method, once the task is started, it does
            NOT stop if encountering an error. Instead, it will continuously
            run to completion. In this case, the value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            DeleteResult class that lists all the errors encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleDepots.Delete``.
        """
        return self._invoke('delete',
                            {
                            'depot': depot,
                            })

    def delete_task(self,
               depot,
               ):
        """
        The task-based ``delete`` method removes content of a user-imported
        online depot from vLCM completely. As a result, the URL of the
        user-imported online depot will also be removed. 
        
        Note: 
        
        1. To remove content of system-defined online depots, use ``flush``
        method. 
        
        2. The non task-based ``delete`` method has been deprecated. It only
        deletes the record of depot from the list of imported online software
        depots, instead of removing the depot's content from the system.

        :type  depot: :class:`str`
        :param depot: Identifier of the depot to be removed.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.depots.online``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the given depot is system-defined. This error is applicable to
            the task-based ``delete`` method only.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no depot associated with parameter ``depot`` in the
            system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            If the content of depot to be deleted is used in some baseline or
            desired state. 
            
            The value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            PrecheckResult class that lists the information of affected
            baselines and desired states. 
            
            This error is applicable to the task-based ``delete`` method only.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there some unknown internal error. 
            
            The accompanying error message will give more details about the
            failure. 
            
            For task-based ``delete`` method, once the task is started, it does
            NOT stop if encountering an error. Instead, it will continuously
            run to completion. In this case, the value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            DeleteResult class that lists all the errors encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleDepots.Delete``.
        """
        task_id = self._invoke('delete$task',
                                {
                                'depot': depot,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.VoidType())
        return task_instance


    def flush_task(self,
              depot,
              ):
        """
        
        
        The task-based ``flush`` method removes content of a system-defined
        online depot from vLCM completely. As a result, the system-defined
        online depot will be disabled. 
        
        Note: To remove content of user-imported online depots, use the
        task-based ``delete`` method.

        :type  depot: :class:`str`
        :param depot: Identifier of the depot to be removed.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.depots.online``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If the given depot is NOT system-defined.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no depot associated with parameter ``depot`` in the
            system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            If the content of depot to be deleted is used in some baseline or
            desired state. The value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            PrecheckResult class that lists the information of affected
            baselines and desired states.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there some unknown internal error. The accompanying error
            message will give more details about the failure. ``flush`` is a
            task-based method. Once the task is started, it does NOT stop if
            encountering an error. Instead, it will continuously run to
            completion. In this case, the value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            FlushResult class that lists all the errors encountered.
        """
        task_id = self._invoke('flush$task',
                                {
                                'depot': depot,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.VoidType())
        return task_instance

    def update(self,
               depot,
               spec,
               ):
        """
        Updates the configuration of a currently configured online software
        depot.

        :type  depot: :class:`str`
        :param depot: Identifier of the depot to be updated.
            The parameter must be an identifier for the resource type:
            ``com.vmware.esx.settings.depots.online``.
        :type  spec: :class:`Online.UpdateSpec`
        :param spec: Update specification.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If given depot is system defined.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no depot associated with parameter ``depot`` in the
            system.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSettings.Write``.
        """
        return self._invoke('update',
                            {
                            'depot': depot,
                            'spec': spec,
                            })
class SyncSchedule(VapiInterface):
    """
    The ``SyncSchedule`` class provides methods to manage Schedule of Online
    Software Depot sync.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.depots.sync_schedule'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SyncScheduleStub)
        self._VAPI_OPERATION_IDS = {}

    class Recurrence(Enum):
        """
        The ``SyncSchedule.Recurrence`` class contains the supported values for how
        often to sync from online or UMDS depots.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        HOURLY = None
        """
        Hourly.

        """
        DAILY = None
        """
        Daily.

        """
        WEEKLY = None
        """
        Weekly.

        """
        MONTHLY_BY_DAY = None
        """
        Monthly by day.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Recurrence` instance.
            """
            Enum.__init__(string)

    Recurrence._set_values({
        'HOURLY': Recurrence('HOURLY'),
        'DAILY': Recurrence('DAILY'),
        'WEEKLY': Recurrence('WEEKLY'),
        'MONTHLY_BY_DAY': Recurrence('MONTHLY_BY_DAY'),
    })
    Recurrence._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.depots.sync_schedule.recurrence',
        Recurrence))


    class DayOfWeek(Enum):
        """
        The ``SyncSchedule.DayOfWeek`` class contains the supported days of the
        week.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        SUNDAY = None
        """
        Sunday.

        """
        MONDAY = None
        """
        Monday.

        """
        TUESDAY = None
        """
        Tuesday.

        """
        WEDNESDAY = None
        """
        Wednesday.

        """
        THURSDAY = None
        """
        Thursday.

        """
        FRIDAY = None
        """
        Friday.

        """
        SATURDAY = None
        """
        Saturday.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`DayOfWeek` instance.
            """
            Enum.__init__(string)

    DayOfWeek._set_values({
        'SUNDAY': DayOfWeek('SUNDAY'),
        'MONDAY': DayOfWeek('MONDAY'),
        'TUESDAY': DayOfWeek('TUESDAY'),
        'WEDNESDAY': DayOfWeek('WEDNESDAY'),
        'THURSDAY': DayOfWeek('THURSDAY'),
        'FRIDAY': DayOfWeek('FRIDAY'),
        'SATURDAY': DayOfWeek('SATURDAY'),
    })
    DayOfWeek._set_binding_type(type.EnumType(
        'com.vmware.esx.settings.depots.sync_schedule.day_of_week',
        DayOfWeek))


    class Schedule(VapiStruct):
        """
        The ``SyncSchedule.Schedule`` class defines a schedule.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'type',
                {
                    'HOURLY' : [('skip', False), ('minute', True)],
                    'DAILY' : [('skip', False), ('minute', True), ('hour', True)],
                    'WEEKLY' : [('skip', False), ('minute', True), ('hour', True), ('day_of_week', True)],
                    'MONTHLY_BY_DAY' : [('skip', False), ('minute', True), ('hour', True), ('day_of_month', True)],
                }
            ),
        ]



        def __init__(self,
                     type=None,
                     skip=None,
                     minute=None,
                     hour=None,
                     day_of_month=None,
                     day_of_week=None,
                    ):
            """
            :type  type: :class:`SyncSchedule.Recurrence`
            :param type: Frequency of the schedule.
            :type  skip: :class:`long` or ``None``
            :param skip: This determines the units of ``SyncSchedule.Recurrence`` to skip
                before the scheduled task runs again. For example, value of 1 for
                HOURLY type means the scheduled task runs every 2 hours. The value
                must be within the range 0 to 998.
                If None, no unit is skipped.
            :type  minute: :class:`long`
            :param minute: Minute at which schedule should be run. The value must be within
                the range 0 to 59.
                This attribute is optional and it is only relevant when the value
                of ``type`` is one of :attr:`SyncSchedule.Recurrence.HOURLY`,
                :attr:`SyncSchedule.Recurrence.DAILY`,
                :attr:`SyncSchedule.Recurrence.WEEKLY`, or
                :attr:`SyncSchedule.Recurrence.MONTHLY_BY_DAY`.
            :type  hour: :class:`long`
            :param hour: Hour at which schedule should be run. The value must be within the
                range 0 to 23.
                This attribute is optional and it is only relevant when the value
                of ``type`` is one of :attr:`SyncSchedule.Recurrence.DAILY`,
                :attr:`SyncSchedule.Recurrence.WEEKLY`, or
                :attr:`SyncSchedule.Recurrence.MONTHLY_BY_DAY`.
            :type  day_of_month: :class:`long`
            :param day_of_month: Day at which schedule should be run. The value must be within the
                range 1 to 31. If the value exceeds the total number of days in the
                month, the schedule will run on the last day of the month.
                This attribute is optional and it is only relevant when the value
                of ``type`` is :attr:`SyncSchedule.Recurrence.MONTHLY_BY_DAY`.
            :type  day_of_week: :class:`SyncSchedule.DayOfWeek`
            :param day_of_week: Day of the week when schedule should be run
                This attribute is optional and it is only relevant when the value
                of ``type`` is :attr:`SyncSchedule.Recurrence.WEEKLY`.
            """
            self.type = type
            self.skip = skip
            self.minute = minute
            self.hour = hour
            self.day_of_month = day_of_month
            self.day_of_week = day_of_week
            VapiStruct.__init__(self)


    Schedule._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.sync_schedule.schedule', {
            'type': type.ReferenceType(__name__, 'SyncSchedule.Recurrence'),
            'skip': type.OptionalType(type.IntegerType()),
            'minute': type.OptionalType(type.IntegerType()),
            'hour': type.OptionalType(type.IntegerType()),
            'day_of_month': type.OptionalType(type.IntegerType()),
            'day_of_week': type.OptionalType(type.ReferenceType(__name__, 'SyncSchedule.DayOfWeek')),
        },
        Schedule,
        False,
        None))


    class Spec(VapiStruct):
        """
        The ``SyncSchedule.Spec`` class defines the information regarding the sync
        schedule.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     enabled=None,
                     schedule=None,
                     email_addresses=None,
                    ):
            """
            :type  enabled: :class:`bool`
            :param enabled: Flag indicating whether automatic sync is enabled or not
            :type  schedule: :class:`SyncSchedule.Schedule` or ``None``
            :param schedule: The schedule to check for new updates.
                If None the schedule must be disabled.
            :type  email_addresses: :class:`list` of :class:`str`
            :param email_addresses: Email addresses to which the notification will be sent. If empty,
                no notification is sent.
            """
            self.enabled = enabled
            self.schedule = schedule
            self.email_addresses = email_addresses
            VapiStruct.__init__(self)


    Spec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.sync_schedule.spec', {
            'enabled': type.BooleanType(),
            'schedule': type.OptionalType(type.ReferenceType(__name__, 'SyncSchedule.Schedule')),
            'email_addresses': type.ListType(type.StringType()),
        },
        Spec,
        False,
        None))



    def get(self):
        """
        Returns the currently configured software depot sync schedule.


        :rtype: :class:`SyncSchedule.Spec`
        :return: Currently configured sync schedule.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown error. The accompanying error message will
            give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleSettings.Read``.
        """
        return self._invoke('get', None)

    def set(self,
            spec=None,
            ):
        """
        Sets the software depot sync schedule.

        :type  spec: :class:`SyncSchedule.Spec` or ``None``
        :param spec: Information of the software depot sync schedule.
            If None, it will be reset to the default schedule, which is daily
            at a random hour chosen when this API is called.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If :attr:`SyncSchedule.Spec.schedule` is unset while
            :attr:`SyncSchedule.Spec.enabled` is set to true or if any of the
            values is not within valid range.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown error. The accompanying error message will
            give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSettings.Write``.
        """
        return self._invoke('set',
                            {
                            'spec': spec,
                            })
class Umds(VapiInterface):
    """
    The ``Umds`` class provides methods to manage the VMware vSphere Update
    Manager Download Service (UMDS) software depot used during ESX lifecycle
    management. This is the depot downloaded using UMDS. If the UMDS depot is
    specified, then online depots are ignored and data is downloaded only from
    the UMDS depot.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.depots.umds'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _UmdsStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'delete_task': 'delete$task'})

    class SetSpec(VapiStruct):
        """
        The ``Umds.SetSpec`` class defines the information of an UMDS depot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     description=None,
                     enabled=None,
                     location=None,
                    ):
            """
            :type  description: :class:`str` or ``None``
            :param description: Description of the depot.
                If None, the description will be empty.
            :type  enabled: :class:`bool` or ``None``
            :param enabled: Flag indicating whether or not this depot should be enabled.
                Disabling the depot doesn't delete its cached metadata and
                payloads. It will not be refreshed next time depots are re-synced.
                If None, the depot will be enabled.
            :type  location: :class:`str`
            :param location: Location of the depot. It should be the location to the index.xml
                for the depot.
            """
            self.description = description
            self.enabled = enabled
            self.location = location
            VapiStruct.__init__(self)


    SetSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.umds.set_spec', {
            'description': type.OptionalType(type.StringType()),
            'enabled': type.OptionalType(type.BooleanType()),
            'location': type.URIType(),
        },
        SetSpec,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Umds.Info`` class defines the information regarding the UMDS Depot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     description=None,
                     enabled=None,
                     location=None,
                     owner=None,
                    ):
            """
            :type  description: :class:`str`
            :param description: Description of the depot. It will be an empty string if no
                description was provided during create.
            :type  enabled: :class:`bool`
            :param enabled: Flag indicating whether or not this depot is enabled.
            :type  location: :class:`str`
            :param location: Location of the depot.
            :type  owner: :class:`str` or ``None``
            :param owner: Name of the user creating the depot. This attribute was added in
                vSphere API 7.0.3.0.
                This attribute is optional because it was added in a newer version
                than its parent node.
            """
            self.description = description
            self.enabled = enabled
            self.location = location
            self.owner = owner
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.umds.info', {
            'description': type.StringType(),
            'enabled': type.BooleanType(),
            'location': type.URIType(),
            'owner': type.OptionalType(type.StringType()),
        },
        Info,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``Umds.UpdateSpec`` class defines the information used to update the
        UMDS depot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     enabled=None,
                     description=None,
                    ):
            """
            :type  enabled: :class:`bool` or ``None``
            :param enabled: Flag indicating whether or not this depot is enabled. Disabling the
                depot doesn't delete its cached metadata and payloads. It will not
                be refreshed next time depots are re-synced.
                If None, the enabled flag is not updated.
            :type  description: :class:`str` or ``None``
            :param description: Description of the depot.
                If None, the description is not updated.
            """
            self.enabled = enabled
            self.description = description
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.umds.update_spec', {
            'enabled': type.OptionalType(type.BooleanType()),
            'description': type.OptionalType(type.StringType()),
        },
        UpdateSpec,
        False,
        None))


    class PrecheckResult(VapiStruct):
        """
        The ``Umds.PrecheckResult`` class contains the fields that show the details
        of affected baselines and desired states found in :func:`Umds.delete`
        method. This class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     affected_baselines=None,
                     affected_desired_states=None,
                    ):
            """
            :type  affected_baselines: :class:`list` of :class:`AffectedBaselineInfo` or ``None``
            :param affected_baselines: Baselines affected. This attribute was added in vSphere API
                7.0.3.0.
                If None, no baseline is affected.
            :type  affected_desired_states: :class:`list` of :class:`AffectedDesiredStateInfo` or ``None``
            :param affected_desired_states: Desired states affected. This attribute was added in vSphere API
                7.0.3.0.
                If None, no desired state is affected.
            """
            self.affected_baselines = affected_baselines
            self.affected_desired_states = affected_desired_states
            VapiStruct.__init__(self)


    PrecheckResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.umds.precheck_result', {
            'affected_baselines': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'AffectedBaselineInfo'))),
            'affected_desired_states': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'AffectedDesiredStateInfo'))),
        },
        PrecheckResult,
        False,
        None))


    class DeleteResult(VapiStruct):
        """
        The ``Umds.DeleteResult`` class contains a field that lists all the errors
        encountered after starting the task of :func:`Umds.delete` method. This
        class was added in vSphere API 7.0.3.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     notifications=None,
                    ):
            """
            :type  notifications: :class:`com.vmware.esx.settings_client.Notifications` or ``None``
            :param notifications: Notifications returned by :func:`Umds.delete` method. This
                attribute was added in vSphere API 7.0.3.0.
                If None, no notification is returned.
            """
            self.notifications = notifications
            VapiStruct.__init__(self)


    DeleteResult._set_binding_type(type.StructType(
        'com.vmware.esx.settings.depots.umds.delete_result', {
            'notifications': type.OptionalType(type.ReferenceType('com.vmware.esx.settings_client', 'Notifications')),
        },
        DeleteResult,
        False,
        None))



    def get(self):
        """
        Gets the information about a currently configured UMDS software depot.


        :rtype: :class:`Umds.Info`
        :return: Information of the currently configured UMDS software depot.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no UMDS software depot set.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleSettings.Read``.
        """
        return self._invoke('get', None)

    def set(self,
            spec,
            ):
        """
        Sets or overwrites information about the UMDS software depot.

        :type  spec: :class:`Umds.SetSpec`
        :param spec: Specification to set the UMDS depot.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If an invalid location is provided.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSettings.Write``.
        """
        return self._invoke('set',
                            {
                            'spec': spec,
                            })

    def delete(self):
        """
        The task-based ``delete`` method removes content of the UMDS depot from
        vLCM completely. Note: The non task-based ``delete`` method has been
        deprecated. It deletes only the record of UMDS depot from database,
        instead of removing the content of UMDS depot from vLCM.


        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no UMDS depot configured in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            If the content of UMDS depot to be deleted is used in some baseline
            or desired state. The value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            PrecheckResult class that lists the information of affected
            baselines and desired states. This error is applicable to the
            task-based ``delete`` method only.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there some unknown internal error. The accompanying error
            message will give more details about the failure. For task-based
            ``delete`` method, once the task is started, it does NOT stop if
            encountering an error. Instead, it will continuously run to
            completion. In this case, the value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            DeleteResult class that lists all the errors encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleDepots.Delete``.
        """
        return self._invoke('delete', None)

    def delete_task(self):
        """
        The task-based ``delete`` method removes content of the UMDS depot from
        vLCM completely. Note: The non task-based ``delete`` method has been
        deprecated. It deletes only the record of UMDS depot from database,
        instead of removing the content of UMDS depot from vLCM.


        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no UMDS depot configured in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            If the content of UMDS depot to be deleted is used in some baseline
            or desired state. The value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            PrecheckResult class that lists the information of affected
            baselines and desired states. This error is applicable to the
            task-based ``delete`` method only.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there some unknown internal error. The accompanying error
            message will give more details about the failure. For task-based
            ``delete`` method, once the task is started, it does NOT stop if
            encountering an error. Instead, it will continuously run to
            completion. In this case, the value of the data attribute of
            :class:`com.vmware.vapi.std.errors_client.Error` will be the
            DeleteResult class that lists all the errors encountered.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``VcIntegrity.lifecycleDepots.Delete``.
        """
        task_id = self._invoke('delete$task',
                                None)
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.VoidType())
        return task_instance

    def update(self,
               spec,
               ):
        """
        Updates the configuration of a currently configured UMDS software
        depot.

        :type  spec: :class:`Umds.UpdateSpec`
        :param spec: Update specification.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no UMDS depot configured.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is some unknown internal error. The accompanying error
            message will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires
              ``VcIntegrity.lifecycleSettings.Write``.
        """
        return self._invoke('update',
                            {
                            'spec': spec,
                            })
class _OfflineStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'depot': type.IdType(resource_types='com.vmware.esx.settings.depots.offline'),
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
            url_template='/esx/settings/depots/offline/{depot}',
            path_variables={
                'depot': 'depot',
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
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/depots/offline',
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

        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Offline.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/depots/offline',
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
            'depot': type.IdType(resource_types='com.vmware.esx.settings.depots.offline'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_in_use':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInUse'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/esx/settings/depots/offline/{depot}',
            path_variables={
                'depot': 'depot',
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

        # properties for create_from_host operation
        create_from_host_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Offline.ConnectionSpec'),
        })
        create_from_host_error_dict = {
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unverified_peer':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnverifiedPeer'),

        }
        create_from_host_input_value_validator_list = [
        ]
        create_from_host_output_validator_list = [
        ]
        create_from_host_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/depots/offline',
            request_body_parameter='spec',
            path_variables={
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'createFromHost',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Offline.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.MapType(type.IdType(), type.ReferenceType(__name__, 'Offline.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'create$task': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'delete': {
                'input_type': delete_input_type,
                'output_type': type.VoidType(),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': delete_output_validator_list,
                'task_type': TaskType.TASK,
            },
            'delete$task': {
                'input_type': delete_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK,
            },
            'create_from_host$task': {
                'input_type': create_from_host_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': create_from_host_error_dict,
                'input_value_validator_list': create_from_host_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'list': list_rest_metadata,
            'create': create_rest_metadata,
            'delete': delete_rest_metadata,
            'create_from_host': create_from_host_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.depots.offline',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _OnlineStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {})
        list_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/esx/settings/depots/online',
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

        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'depot': type.IdType(resource_types='com.vmware.esx.settings.depots.online'),
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
            url_template='/esx/settings/depots/online/{depot}',
            path_variables={
                'depot': 'depot',
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
            'spec': type.ReferenceType(__name__, 'Online.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/depots/online',
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
            'depot': type.IdType(resource_types='com.vmware.esx.settings.depots.online'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_in_use':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInUse'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/esx/settings/depots/online/{depot}',
            path_variables={
                'depot': 'depot',
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

        # properties for flush operation
        flush_input_type = type.StructType('operation-input', {
            'depot': type.IdType(resource_types='com.vmware.esx.settings.depots.online'),
        })
        flush_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_in_use':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInUse'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        flush_input_value_validator_list = [
        ]
        flush_output_validator_list = [
        ]
        flush_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/esx/settings/depots/online/{depot}',
            path_variables={
                'depot': 'depot',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'flush',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'depot': type.IdType(resource_types='com.vmware.esx.settings.depots.online'),
            'spec': type.ReferenceType(__name__, 'Online.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/esx/settings/depots/online/{depot}',
            request_body_parameter='spec',
            path_variables={
                'depot': 'depot',
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
                'output_type': type.MapType(type.IdType(), type.ReferenceType(__name__, 'Online.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Online.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'create': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.esx.settings.depots.online'),
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
                'task_type': TaskType.TASK,
            },
            'delete$task': {
                'input_type': delete_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK,
            },
            'flush$task': {
                'input_type': flush_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': flush_error_dict,
                'input_value_validator_list': flush_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'update': {
                'input_type': update_input_type,
                'output_type': type.VoidType(),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': update_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
            'get': get_rest_metadata,
            'create': create_rest_metadata,
            'delete': delete_rest_metadata,
            'flush': flush_rest_metadata,
            'update': update_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.depots.online',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _SyncScheduleStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {})
        get_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
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
            url_template='/esx/settings/depots/sync-schedule',
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
            'spec': type.OptionalType(type.ReferenceType(__name__, 'SyncSchedule.Spec')),
        })
        set_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/esx/settings/depots/sync-schedule',
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

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'SyncSchedule.Spec'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
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
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'set': set_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.depots.sync_schedule',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _UmdsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {})
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
            url_template='/esx/settings/depots/umds',
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
            'spec': type.ReferenceType(__name__, 'Umds.SetSpec'),
        })
        set_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/esx/settings/depots/umds',
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
        delete_input_type = type.StructType('operation-input', {})
        delete_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_in_use':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInUse'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/esx/settings/depots/umds',
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

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Umds.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/esx/settings/depots/umds',
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

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Umds.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
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
            'delete': {
                'input_type': delete_input_type,
                'output_type': type.VoidType(),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': delete_output_validator_list,
                'task_type': TaskType.TASK,
            },
            'delete$task': {
                'input_type': delete_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK,
            },
            'update': {
                'input_type': update_input_type,
                'output_type': type.VoidType(),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': update_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'set': set_rest_metadata,
            'delete': delete_rest_metadata,
            'update': update_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.settings.depots.umds',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Offline': Offline,
        'Online': Online,
        'SyncSchedule': SyncSchedule,
        'Umds': Umds,
        'offline': 'com.vmware.esx.settings.depots.offline_client.StubFactory',
        'online': 'com.vmware.esx.settings.depots.online_client.StubFactory',
        'umds': 'com.vmware.esx.settings.depots.umds_client.StubFactory',
    }

