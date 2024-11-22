# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.appliance.vcenter.settings.v1.
#---------------------------------------------------------------------------

"""
The ``com.vmware.appliance.vcenter.settings.v1_client`` module provides classes
to manage the ConfigManagement.

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

class StatusType(Enum):
    """
    The ``StatusType`` class defines possible values of profile status.
    **Warning:** This enumeration is available as Technology Preview. These are
    early access APIs provided to test, automate and provide feedback on the
    feature. Since this can change based on feedback, VMware does not guarantee
    backwards compatibility and recommends against using them in production
    environments. Some Technology Preview APIs might only be applicable to
    specific environments.

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
    Profile configuration is valid. **Warning:** This class attribute is
    available as Technology Preview. These are early access APIs provided to
    test, automate and provide feedback on the feature. Since this can change
    based on feedback, VMware does not guarantee backwards compatibility and
    recommends against using them in production environments. Some Technology
    Preview APIs might only be applicable to specific environments.

    """
    INVALID = None
    """
    Profile Configuration is invalid. **Warning:** This class attribute is
    available as Technology Preview. These are early access APIs provided to
    test, automate and provide feedback on the feature. Since this can change
    based on feedback, VMware does not guarantee backwards compatibility and
    recommends against using them in production environments. Some Technology
    Preview APIs might only be applicable to specific environments.

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
    'com.vmware.appliance.vcenter.settings.v1.status_type',
    StatusType))



class ApplyImpact(Enum):
    """
    The ``ApplyImpact`` class contains information about the impact of applying
    the target state. **Warning:** This enumeration is available as Technology
    Preview. These are early access APIs provided to test, automate and provide
    feedback on the feature. Since this can change based on feedback, VMware
    does not guarantee backwards compatibility and recommends against using
    them in production environments. Some Technology Preview APIs might only be
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
    NO_IMPACT = None
    """
    Appliance has no impact. **Warning:** This class attribute is available as
    Technology Preview. These are early access APIs provided to test, automate
    and provide feedback on the feature. Since this can change based on
    feedback, VMware does not guarantee backwards compatibility and recommends
    against using them in production environments. Some Technology Preview APIs
    might only be applicable to specific environments.

    """
    REBOOT_REQUIRED = None
    """
    Appliance requires reboot to reach this target state. **Warning:** This
    class attribute is available as Technology Preview. These are early access
    APIs provided to test, automate and provide feedback on the feature. Since
    this can change based on feedback, VMware does not guarantee backwards
    compatibility and recommends against using them in production environments.
    Some Technology Preview APIs might only be applicable to specific
    environments.

    """
    RESTART_SERVICE = None
    """
    To reach the target state appliance requires services to restart.
    **Warning:** This class attribute is available as Technology Preview. These
    are early access APIs provided to test, automate and provide feedback on
    the feature. Since this can change based on feedback, VMware does not
    guarantee backwards compatibility and recommends against using them in
    production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`ApplyImpact` instance.
        """
        Enum.__init__(string)

ApplyImpact._set_values({
    'NO_IMPACT': ApplyImpact('NO_IMPACT'),
    'REBOOT_REQUIRED': ApplyImpact('REBOOT_REQUIRED'),
    'RESTART_SERVICE': ApplyImpact('RESTART_SERVICE'),
})
ApplyImpact._set_binding_type(type.EnumType(
    'com.vmware.appliance.vcenter.settings.v1.apply_impact',
    ApplyImpact))




class Impact(VapiStruct):
    """
    The ``Impact`` class contains attributes that describe the impact during
    apply. method. **Warning:** This class is available as Technology Preview.
    These are early access APIs provided to test, automate and provide feedback
    on the feature. Since this can change based on feedback, VMware does not
    guarantee backwards compatibility and recommends against using them in
    production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """

    _validator_list = [
        UnionValidator(
            'apply_impact',
            {
                'RESTART_SERVICE' : [('vcenter_services', False), ('system_services', False)],
                'NO_IMPACT' : [],
                'REBOOT_REQUIRED' : [],
            }
        ),
    ]



    def __init__(self,
                 apply_impact=None,
                 vcenter_services=None,
                 system_services=None,
                 message=None,
                 status=None,
                 notifications=None,
                ):
        """
        :type  apply_impact: :class:`ApplyImpact`
        :param apply_impact: Impact to the vCenter if the profile is applied. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        :type  vcenter_services: :class:`set` of :class:`str` or ``None``
        :param vcenter_services: List of the vCenter services to be restarted. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
            If None there no impact on system.
        :type  system_services: :class:`set` of :class:`str` or ``None``
        :param system_services: List of the System services to be restarted. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
            If None there no impact on system.
        :type  message: :class:`list` of :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param message: Description of the impact. **Warning:** This attribute is available
            as Technology Preview. These are early access APIs provided to
            test, automate and provide feedback on the feature. Since this can
            change based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  status: :class:`StatusType`
        :param status: Validation status of the appliance. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  notifications: :class:`Notifications`
        :param notifications: Notifications returned by the validation operation. **Warning:**
            This attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        """
        self.apply_impact = apply_impact
        self.vcenter_services = vcenter_services
        self.system_services = system_services
        self.message = message
        self.status = status
        self.notifications = notifications
        VapiStruct.__init__(self)


Impact._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.impact', {
        'apply_impact': type.ReferenceType(__name__, 'ApplyImpact'),
        'vcenter_services': type.OptionalType(type.SetType(type.StringType())),
        'system_services': type.OptionalType(type.SetType(type.StringType())),
        'message': type.ListType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
        'status': type.ReferenceType(__name__, 'StatusType'),
        'notifications': type.ReferenceType(__name__, 'Notifications'),
    },
    Impact,
    False,
    None))



class CheckResult(VapiStruct):
    """
    The ``CheckResult`` class contains attributes that describe the precheck
    results of an appliance. method. **Warning:** This class is available as
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
                 impact=None,
                 start_time=None,
                 end_time=None,
                 profile=None,
                 version=None,
                 valid=None,
                 invalid=None,
                ):
        """
        :type  impact: :class:`Impact`
        :param impact: Overall Impact. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  start_time: :class:`datetime.datetime`
        :param start_time: Time when the method started. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  end_time: :class:`datetime.datetime` or ``None``
        :param end_time: Time when the method completed. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            If None, the endTime will be empty.
        :type  profile: :class:`str`
        :param profile: Identifier of the profile on which the prechek is run to generate
            this result. **Warning:** This attribute is available as Technology
            Preview. These are early access APIs provided to test, automate and
            provide feedback on the feature. Since this can change based on
            feedback, VMware does not guarantee backwards compatibility and
            recommends against using them in production environments. Some
            Technology Preview APIs might only be applicable to specific
            environments.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.profile``. When
            methods return a value of this class as a return value, the
            attribute will be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.profile``.
        :type  version: :class:`str`
        :param version: The version of the profile. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``. When
            methods return a value of this class as a return value, the
            attribute will be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``.
        :type  valid: :class:`set` of :class:`str`
        :param valid: Identifiers of the valid components. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``. When
            methods return a value of this class as a return value, the
            attribute will contain identifiers for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``.
        :type  invalid: :class:`set` of :class:`str`
        :param invalid: Identifiers of the Invalid components. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``. When
            methods return a value of this class as a return value, the
            attribute will contain identifiers for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``.
        """
        self.impact = impact
        self.start_time = start_time
        self.end_time = end_time
        self.profile = profile
        self.version = version
        self.valid = valid
        self.invalid = invalid
        VapiStruct.__init__(self)


CheckResult._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.check_result', {
        'impact': type.ReferenceType(__name__, 'Impact'),
        'start_time': type.DateTimeType(),
        'end_time': type.OptionalType(type.DateTimeType()),
        'profile': type.IdType(resource_types='com.vmware.appliance.vcenter.settings.v1.config.profile'),
        'version': type.IdType(resource_types='com.vmware.appliance.vcenter.settings.v1.config.component'),
        'valid': type.SetType(type.IdType()),
        'invalid': type.SetType(type.IdType()),
    },
    CheckResult,
    False,
    None))



class DesiredState(VapiStruct):
    """
    The ``DesiredState`` class defines the configuration about different
    components in vCenter. **Warning:** This class is available as Technology
    Preview. These are early access APIs provided to test, automate and provide
    feedback on the feature. Since this can change based on feedback, VMware
    does not guarantee backwards compatibility and recommends against using
    them in production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 appliance=None,
                 authmgmt=None,
                 inventory=None,
                 vsphereuiconfiguration=None,
                 invtauthmgmt=None,
                 managementcluster=None,
                ):
        """
        :type  appliance: :class:`com.vmware.appliance.vcenter.settings.v1.config.components.applmgmt_client.ApplianceManagement` or ``None``
        :param appliance: Appliance Management component desired spec. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        :type  authmgmt: :class:`com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement_client.AuthenticationManagement` or ``None``
        :param authmgmt: Authentication Management component desired spec. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        :type  inventory: :class:`com.vmware.appliance.vcenter.settings.v1.config.components.inventory_client.InventoryManagement` or ``None``
        :param inventory: Inventory Configurations. **Warning:** This attribute is available
            as Technology Preview. These are early access APIs provided to
            test, automate and provide feedback on the feature. Since this can
            change based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  vsphereuiconfiguration: :class:`com.vmware.appliance.vcenter.settings.v1.config.components.vsphereuiconfiguration_client.VsphereUIConfiguration` or ``None``
        :param vsphereuiconfiguration: Clientcapabilities Configurations. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  invtauthmgmt: :class:`com.vmware.appliance.vcenter.settings.v1.config.components.inventoryauthorization_client.InventoryAuthorization` or ``None``
        :param invtauthmgmt: Inventory Authorization. **Warning:** This attribute is available
            as Technology Preview. These are early access APIs provided to
            test, automate and provide feedback on the feature. Since this can
            change based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  managementcluster: :class:`com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster_client.ManagementCluster` or ``None``
        :param managementcluster: Management Cluster Configurations. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            This attribute is optional because it was added in a newer version
            than its parent node.
        """
        self.appliance = appliance
        self.authmgmt = authmgmt
        self.inventory = inventory
        self.vsphereuiconfiguration = vsphereuiconfiguration
        self.invtauthmgmt = invtauthmgmt
        self.managementcluster = managementcluster
        VapiStruct.__init__(self)


DesiredState._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.desired_state', {
        'appliance': type.OptionalType(type.ReferenceType('com.vmware.appliance.vcenter.settings.v1.config.components.applmgmt_client', 'ApplianceManagement')),
        'authmgmt': type.OptionalType(type.ReferenceType('com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement_client', 'AuthenticationManagement')),
        'inventory': type.OptionalType(type.ReferenceType('com.vmware.appliance.vcenter.settings.v1.config.components.inventory_client', 'InventoryManagement')),
        'vsphereuiconfiguration': type.OptionalType(type.ReferenceType('com.vmware.appliance.vcenter.settings.v1.config.components.vsphereuiconfiguration_client', 'VsphereUIConfiguration')),
        'invtauthmgmt': type.OptionalType(type.ReferenceType('com.vmware.appliance.vcenter.settings.v1.config.components.inventoryauthorization_client', 'InventoryAuthorization')),
        'managementcluster': type.OptionalType(type.ReferenceType('com.vmware.appliance.vcenter.settings.v1.config.components.managementcluster_client', 'ManagementCluster')),
    },
    DesiredState,
    False,
    None))



class Notification(VapiStruct):
    """
    The ``Notification`` class contains attributes to describe any
    info/warning/error messages that Tasks can raise. **Warning:** This class
    is available as Technology Preview. These are early access APIs provided to
    test, automate and provide feedback on the feature. Since this can change
    based on feedback, VMware does not guarantee backwards compatibility and
    recommends against using them in production environments. Some Technology
    Preview APIs might only be applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 notification=None,
                 time=None,
                 message=None,
                 resolution=None,
                ):
        """
        :type  notification: :class:`str`
        :param notification: The notification Identifier. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.notification``.
            When methods return a value of this class as a return value, the
            attribute will be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.notification``.
        :type  time: :class:`datetime.datetime` or ``None``
        :param time: The time the notification was raised. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            Only :class:`set` if the time information is available.
        :type  message: :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param message: The notification message. **Warning:** This attribute is available
            as Technology Preview. These are early access APIs provided to
            test, automate and provide feedback on the feature. Since this can
            change based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  resolution: :class:`com.vmware.vapi.std_client.LocalizableMessage` or ``None``
        :param resolution: The resolution message, if any. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            Only :class:`set` for warnings and errors.
        """
        self.notification = notification
        self.time = time
        self.message = message
        self.resolution = resolution
        VapiStruct.__init__(self)


Notification._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.notification', {
        'notification': type.IdType(resource_types='com.vmware.appliance.vcenter.settings.v1.config.notification'),
        'time': type.OptionalType(type.DateTimeType()),
        'message': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
        'resolution': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage')),
    },
    Notification,
    False,
    None))



class Notifications(VapiStruct):
    """
    The ``Notifications`` class contains info/warning/error messages that can
    be reported be the task. **Warning:** This class is available as Technology
    Preview. These are early access APIs provided to test, automate and provide
    feedback on the feature. Since this can change based on feedback, VMware
    does not guarantee backwards compatibility and recommends against using
    them in production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 info=None,
                 warnings=None,
                 errors=None,
                ):
        """
        :type  info: :class:`list` of :class:`Notification` or ``None``
        :param info: Info notification messages reported. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            Only :class:`set` if an info was reported by the task.
        :type  warnings: :class:`list` of :class:`Notification` or ``None``
        :param warnings: Warning notification messages reported. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            Only :class:`set` if an warning was reported by the task.
        :type  errors: :class:`list` of :class:`Notification` or ``None``
        :param errors: Error notification messages reported. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            Only :class:`set` if an error was reported by the task.
        """
        self.info = info
        self.warnings = warnings
        self.errors = errors
        VapiStruct.__init__(self)


Notifications._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.notifications', {
        'info': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Notification'))),
        'warnings': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Notification'))),
        'errors': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Notification'))),
    },
    Notifications,
    False,
    None))



class DiffResult(VapiStruct):
    """
    The ``DiffResult`` class defines the information about the feature
    configuration. **Warning:** This class is available as Technology Preview.
    These are early access APIs provided to test, automate and provide feedback
    on the feature. Since this can change based on feedback, VMware does not
    guarantee backwards compatibility and recommends against using them in
    production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 current_value=None,
                 desired_value=None,
                 category=None,
                 path=None,
                 description=None,
                ):
        """
        :type  current_value: :class:`DataValue`
        :param current_value: Current property value. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  desired_value: :class:`DataValue`
        :param desired_value: Desired property value. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  category: :class:`str`
        :param category: Category of component configuration. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  path: :class:`str`
        :param path: Path of the component configuration. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  description: :class:`str`
        :param description: Description of the component configuration. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        """
        self.current_value = current_value
        self.desired_value = desired_value
        self.category = category
        self.path = path
        self.description = description
        VapiStruct.__init__(self)


DiffResult._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.diff_result', {
        'current_value': type.OpaqueType(),
        'desired_value': type.OpaqueType(),
        'category': type.StringType(),
        'path': type.StringType(),
        'description': type.StringType(),
    },
    DiffResult,
    False,
    None))



class ComplianceResult(VapiStruct):
    """
    The ``ComplianceResult`` class defines the information about scan results.
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
                 diff_results=None,
                ):
        """
        :type  diff_results: :class:`dict` of :class:`str` and :class:`DiffResult`
        :param diff_results: Map of property value differences between current software state
            and working profile. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        """
        self.diff_results = diff_results
        VapiStruct.__init__(self)


ComplianceResult._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.compliance_result', {
        'diff_results': type.MapType(type.StringType(), type.ReferenceType(__name__, 'DiffResult')),
    },
    ComplianceResult,
    False,
    None))



class ScanResult(VapiStruct):
    """
    The ``ScanResult`` class contains attributes to describe the scan result of
    a appliance. **Warning:** This class is available as Technology Preview.
    These are early access APIs provided to test, automate and provide feedback
    on the feature. Since this can change based on feedback, VMware does not
    guarantee backwards compatibility and recommends against using them in
    production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 status=None,
                 notifications=None,
                 start_time=None,
                 end_time=None,
                 profile=None,
                 version=None,
                 compliant=None,
                 non_compliant=None,
                 unavailable=None,
                 compliance_result=None,
                ):
        """
        :type  status: :class:`ScanResult.ComplianceStatus`
        :param status: Aggregrated compliance state of the appliance. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        :type  notifications: :class:`Notifications`
        :param notifications: Notifications returned by the scan operation. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        :type  start_time: :class:`datetime.datetime`
        :param start_time: Time when the method started. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  end_time: :class:`datetime.datetime` or ``None``
        :param end_time: Time when the method completed. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            If None, the endTime will be empty.
        :type  profile: :class:`str`
        :param profile: Identifier of the apply on which the scan is run to generate this
            result. **Warning:** This attribute is available as Technology
            Preview. These are early access APIs provided to test, automate and
            provide feedback on the feature. Since this can change based on
            feedback, VMware does not guarantee backwards compatibility and
            recommends against using them in production environments. Some
            Technology Preview APIs might only be applicable to specific
            environments.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.profile``. When
            methods return a value of this class as a return value, the
            attribute will be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.profile``.
        :type  version: :class:`str`
        :param version: The version of the profile. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.version``. When
            methods return a value of this class as a return value, the
            attribute will be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.version``.
        :type  compliant: :class:`set` of :class:`str`
        :param compliant: Identifiers of compliant components. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``. When
            methods return a value of this class as a return value, the
            attribute will contain identifiers for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``.
        :type  non_compliant: :class:`set` of :class:`str`
        :param non_compliant: Identifiers of non-compliant components. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``. When
            methods return a value of this class as a return value, the
            attribute will contain identifiers for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``.
        :type  unavailable: :class:`set` of :class:`str`
        :param unavailable: Identifiers of unavailable components. There will not be compliance
            details for these components. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
            When clients pass a value of this class as a parameter, the
            attribute must contain identifiers for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``. When
            methods return a value of this class as a return value, the
            attribute will contain identifiers for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``.
        :type  compliance_result: :class:`dict` of :class:`str` and :class:`ComplianceResult`
        :param compliance_result: Mapping of component identifier to the compliance result.
            **Warning:** This attribute is available as Technology Preview.
            These are early access APIs provided to test, automate and provide
            feedback on the feature. Since this can change based on feedback,
            VMware does not guarantee backwards compatibility and recommends
            against using them in production environments. Some Technology
            Preview APIs might only be applicable to specific environments.
            When clients pass a value of this class as a parameter, the key in
            the attribute :class:`dict` must be an identifier for the resource
            type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``. When
            methods return a value of this class as a return value, the key in
            the attribute :class:`dict` will be an identifier for the resource
            type:
            ``com.vmware.appliance.vcenter.settings.v1.config.component``.
        """
        self.status = status
        self.notifications = notifications
        self.start_time = start_time
        self.end_time = end_time
        self.profile = profile
        self.version = version
        self.compliant = compliant
        self.non_compliant = non_compliant
        self.unavailable = unavailable
        self.compliance_result = compliance_result
        VapiStruct.__init__(self)


    class ComplianceStatus(Enum):
        """
        The ``ScanResult.ComplianceStatus`` class contains the possible different
        status of compliance with respect to target version. **Warning:** This
        enumeration is available as Technology Preview. These are early access APIs
        provided to test, automate and provide feedback on the feature. Since this
        can change based on feedback, VMware does not guarantee backwards
        compatibility and recommends against using them in production environments.
        Some Technology Preview APIs might only be applicable to specific
        environments.

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
        Target configuration is same as the current configuration?. **Warning:**
        This class attribute is available as Technology Preview. These are early
        access APIs provided to test, automate and provide feedback on the feature.
        Since this can change based on feedback, VMware does not guarantee
        backwards compatibility and recommends against using them in production
        environments. Some Technology Preview APIs might only be applicable to
        specific environments.

        """
        NON_COMPLIANT = None
        """
        Target configuration is not same as the current configuration. **Warning:**
        This class attribute is available as Technology Preview. These are early
        access APIs provided to test, automate and provide feedback on the feature.
        Since this can change based on feedback, VMware does not guarantee
        backwards compatibility and recommends against using them in production
        environments. Some Technology Preview APIs might only be applicable to
        specific environments.

        """
        UNAVAILABLE = None
        """
        Scan check failed due to unknown error or check hasn't happened yet and the
        results are not available. **Warning:** This class attribute is available
        as Technology Preview. These are early access APIs provided to test,
        automate and provide feedback on the feature. Since this can change based
        on feedback, VMware does not guarantee backwards compatibility and
        recommends against using them in production environments. Some Technology
        Preview APIs might only be applicable to specific environments.

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
        'UNAVAILABLE': ComplianceStatus('UNAVAILABLE'),
    })
    ComplianceStatus._set_binding_type(type.EnumType(
        'com.vmware.appliance.vcenter.settings.v1.scan_result.compliance_status',
        ComplianceStatus))

ScanResult._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.scan_result', {
        'status': type.ReferenceType(__name__, 'ScanResult.ComplianceStatus'),
        'notifications': type.ReferenceType(__name__, 'Notifications'),
        'start_time': type.DateTimeType(),
        'end_time': type.OptionalType(type.DateTimeType()),
        'profile': type.IdType(resource_types='com.vmware.appliance.vcenter.settings.v1.config.profile'),
        'version': type.IdType(resource_types='com.vmware.appliance.vcenter.settings.v1.config.version'),
        'compliant': type.SetType(type.IdType()),
        'non_compliant': type.SetType(type.IdType()),
        'unavailable': type.SetType(type.IdType()),
        'compliance_result': type.MapType(type.IdType(), type.ReferenceType(__name__, 'ComplianceResult')),
    },
    ScanResult,
    False,
    None))



class TaskInfo(VapiStruct):
    """
    The ``TaskInfo`` class contains information about a task. **Warning:** This
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

    _validator_list = [
        UnionValidator(
            'status',
            {
                'RUNNING' : [('progress', True), ('result', False), ('start_time', True)],
                'BLOCKED' : [('progress', True), ('result', False), ('start_time', True)],
                'SUCCEEDED' : [('progress', True), ('result', False), ('start_time', True), ('end_time', True)],
                'FAILED' : [('progress', True), ('result', False), ('error', False), ('start_time', True), ('end_time', True)],
                'PENDING' : [],
            }
        ),
    ]



    def __init__(self,
                 progress=None,
                 notifications=None,
                 result=None,
                 description=None,
                 service=None,
                 operation=None,
                 parent=None,
                 target=None,
                 status=None,
                 cancelable=None,
                 error=None,
                 start_time=None,
                 end_time=None,
                 user=None,
                ):
        """
        :type  progress: :class:`com.vmware.cis.task_client.Progress`
        :param progress: Progress of the operation. **Warning:** This attribute is available
            as Technology Preview. These are early access APIs provided to
            test, automate and provide feedback on the feature. Since this can
            change based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
            This attribute is optional and it is only relevant when the value
            of ``CommonInfo#status`` is one of
            :attr:`com.vmware.cis.task_client.Status.RUNNING`,
            :attr:`com.vmware.cis.task_client.Status.BLOCKED`,
            :attr:`com.vmware.cis.task_client.Status.SUCCEEDED`, or
            :attr:`com.vmware.cis.task_client.Status.FAILED`.
        :type  notifications: :class:`Notifications` or ``None``
        :param notifications: Notifications to the user. **Warning:** This attribute is available
            as Technology Preview. These are early access APIs provided to
            test, automate and provide feedback on the feature. Since this can
            change based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
            Only :class:`set` if the notifications were reported by this
            particular task.
        :type  result: :class:`DataValue` or ``None``
        :param result: Task result. **Warning:** This attribute is available as Technology
            Preview. These are early access APIs provided to test, automate and
            provide feedback on the feature. Since this can change based on
            feedback, VMware does not guarantee backwards compatibility and
            recommends against using them in production environments. Some
            Technology Preview APIs might only be applicable to specific
            environments.
            This attribute will be None if the task has no result.
        :type  description: :class:`com.vmware.vapi.std_client.LocalizableMessage`
        :param description: Description of the operation associated with the task.
        :type  service: :class:`str`
        :param service: Identifier of the service containing the operation.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.vapi.service``. When methods return a value of this
            class as a return value, the attribute will be an identifier for
            the resource type: ``com.vmware.vapi.service``.
        :type  operation: :class:`str`
        :param operation: Identifier of the operation associated with the task.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.vapi.operation``. When methods return a value of this
            class as a return value, the attribute will be an identifier for
            the resource type: ``com.vmware.vapi.operation``.
        :type  parent: :class:`str` or ``None``
        :param parent: Parent of the current task.
            When clients pass a value of this class as a parameter, the
            attribute must be an identifier for the resource type:
            ``com.vmware.cis.task``. When methods return a value of this class
            as a return value, the attribute will be an identifier for the
            resource type: ``com.vmware.cis.task``.
            This attribute will be None if the task has no parent.
        :type  target: :class:`com.vmware.vapi.std_client.DynamicID` or ``None``
        :param target: Identifier of the target created by the operation or an existing
            one the operation performed on.
            This attribute will be None if the operation has no target or
            multiple targets.
        :type  status: :class:`com.vmware.cis.task_client.Status`
        :param status: Status of the operation associated with the task.
        :type  cancelable: :class:`bool`
        :param cancelable: Flag to indicate whether or not the operation can be cancelled. The
            value may change as the operation progresses.
        :type  error: :class:`Exception` or ``None``
        :param error: Description of the error if the operation status is "FAILED".
            If None the description of why the operation failed will be
            included in the result of the operation (see
            :attr:`com.vmware.cis.task_client.Info.result`).
        :type  start_time: :class:`datetime.datetime`
        :param start_time: Time when the operation is started.
            This attribute is optional and it is only relevant when the value
            of ``status`` is one of
            :attr:`com.vmware.cis.task_client.Status.RUNNING`,
            :attr:`com.vmware.cis.task_client.Status.BLOCKED`,
            :attr:`com.vmware.cis.task_client.Status.SUCCEEDED`, or
            :attr:`com.vmware.cis.task_client.Status.FAILED`.
        :type  end_time: :class:`datetime.datetime`
        :param end_time: Time when the operation is completed.
            This attribute is optional and it is only relevant when the value
            of ``status`` is one of
            :attr:`com.vmware.cis.task_client.Status.SUCCEEDED` or
            :attr:`com.vmware.cis.task_client.Status.FAILED`.
        :type  user: :class:`str` or ``None``
        :param user: Name of the user who performed the operation.
            This attribute will be None if the operation is performed by the
            system.
        """
        self.progress = progress
        self.notifications = notifications
        self.result = result
        self.description = description
        self.service = service
        self.operation = operation
        self.parent = parent
        self.target = target
        self.status = status
        self.cancelable = cancelable
        self.error = error
        self.start_time = start_time
        self.end_time = end_time
        self.user = user
        VapiStruct.__init__(self)


TaskInfo._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.task_info', {
        'progress': type.OptionalType(type.ReferenceType('com.vmware.cis.task_client', 'Progress')),
        'notifications': type.OptionalType(type.ReferenceType(__name__, 'Notifications')),
        'result': type.OptionalType(type.OpaqueType()),
        'description': type.ReferenceType('com.vmware.vapi.std_client', 'LocalizableMessage'),
        'service': type.IdType(resource_types='com.vmware.vapi.service'),
        'operation': type.IdType(resource_types='com.vmware.vapi.operation'),
        'parent': type.OptionalType(type.IdType()),
        'target': type.OptionalType(type.ReferenceType('com.vmware.vapi.std_client', 'DynamicID')),
        'status': type.ReferenceType('com.vmware.cis.task_client', 'Status'),
        'cancelable': type.BooleanType(),
        'error': type.OptionalType(type.AnyErrorType()),
        'start_time': type.OptionalType(type.DateTimeType()),
        'end_time': type.OptionalType(type.DateTimeType()),
        'user': type.OptionalType(type.StringType()),
    },
    TaskInfo,
    False,
    None))



class Config(VapiInterface):
    """
    The ``Config`` class provides methods to manage desired configuration
    specification of vCenter.
    """

    _VAPI_SERVICE_ID = 'com.vmware.appliance.vcenter.settings.v1.config'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ConfigStub)
        self._VAPI_OPERATION_IDS = {}
        self._VAPI_OPERATION_IDS.update({'scan_task': 'scan$task'})
        self._VAPI_OPERATION_IDS.update({'scan_desired_state_task': 'scan_desired_state$task'})
        self._VAPI_OPERATION_IDS.update({'check_desired_state_task': 'check_desired_state$task'})
        self._VAPI_OPERATION_IDS.update({'apply_desired_state_task': 'apply_desired_state$task'})

    class ApplyStatus(Enum):
        """
        The ``Config.ApplyStatus`` class contains the possible different status
        codes that can be returned while trying to apply the configuration
        specification to the vcenter. **Warning:** This enumeration is available as
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
        SUCCESS = None
        """
        The method completed successfully. **Warning:** This class attribute is
        available as Technology Preview. These are early access APIs provided to
        test, automate and provide feedback on the feature. Since this can change
        based on feedback, VMware does not guarantee backwards compatibility and
        recommends against using them in production environments. Some Technology
        Preview APIs might only be applicable to specific environments.

        """
        SKIPPED = None
        """
        The method was skipped. **Warning:** This class attribute is available as
        Technology Preview. These are early access APIs provided to test, automate
        and provide feedback on the feature. Since this can change based on
        feedback, VMware does not guarantee backwards compatibility and recommends
        against using them in production environments. Some Technology Preview APIs
        might only be applicable to specific environments.

        """
        TIMED_OUT = None
        """
        The method timed out. **Warning:** This class attribute is available as
        Technology Preview. These are early access APIs provided to test, automate
        and provide feedback on the feature. Since this can change based on
        feedback, VMware does not guarantee backwards compatibility and recommends
        against using them in production environments. Some Technology Preview APIs
        might only be applicable to specific environments.

        """
        ERROR = None
        """
        The method encountered an error. **Warning:** This class attribute is
        available as Technology Preview. These are early access APIs provided to
        test, automate and provide feedback on the feature. Since this can change
        based on feedback, VMware does not guarantee backwards compatibility and
        recommends against using them in production environments. Some Technology
        Preview APIs might only be applicable to specific environments.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ApplyStatus` instance.
            """
            Enum.__init__(string)

    ApplyStatus._set_values({
        'SUCCESS': ApplyStatus('SUCCESS'),
        'SKIPPED': ApplyStatus('SKIPPED'),
        'TIMED_OUT': ApplyStatus('TIMED_OUT'),
        'ERROR': ApplyStatus('ERROR'),
    })
    ApplyStatus._set_binding_type(type.EnumType(
        'com.vmware.appliance.vcenter.settings.v1.config.apply_status',
        ApplyStatus))


    class CreateSpec(VapiStruct):
        """
        The ``Config.CreateSpec`` class contains the specification required to
        create a profile in vCenter. the spec contains attributes that describe
        information about the profile. **Warning:** This class is available as
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
                     name=None,
                     description=None,
                     desired_state=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: Name of the profile. **Warning:** This attribute is available as
                Technology Preview. These are early access APIs provided to test,
                automate and provide feedback on the feature. Since this can change
                based on feedback, VMware does not guarantee backwards
                compatibility and recommends against using them in production
                environments. Some Technology Preview APIs might only be applicable
                to specific environments.
            :type  description: :class:`str` or ``None``
            :param description: Description of the profile. **Warning:** This attribute is
                available as Technology Preview. These are early access APIs
                provided to test, automate and provide feedback on the feature.
                Since this can change based on feedback, VMware does not guarantee
                backwards compatibility and recommends against using them in
                production environments. Some Technology Preview APIs might only be
                applicable to specific environments.
                If None, the description will be empty.
            :type  desired_state: :class:`DesiredState`
            :param desired_state: Defines the desired state. **Warning:** This attribute is available
                as Technology Preview. These are early access APIs provided to
                test, automate and provide feedback on the feature. Since this can
                change based on feedback, VMware does not guarantee backwards
                compatibility and recommends against using them in production
                environments. Some Technology Preview APIs might only be applicable
                to specific environments.
            """
            self.name = name
            self.description = description
            self.desired_state = desired_state
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.appliance.vcenter.settings.v1.config.create_spec', {
            'name': type.StringType(),
            'description': type.OptionalType(type.StringType()),
            'desired_state': type.ReferenceType(__name__, 'DesiredState'),
        },
        CreateSpec,
        False,
        None))


    class ScanSpec(VapiStruct):
        """
        The ``Config.ScanSpec`` class contains the specification required for
        compliance check against the vCenter current config state. **Warning:**
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
                     message=None,
                     desired_state=None,
                    ):
            """
            :type  message: :class:`str` or ``None``
            :param message: Message for the scan. This may act as an identification for the
                scan operation. **Warning:** This attribute is available as
                Technology Preview. These are early access APIs provided to test,
                automate and provide feedback on the feature. Since this can change
                based on feedback, VMware does not guarantee backwards
                compatibility and recommends against using them in production
                environments. Some Technology Preview APIs might only be applicable
                to specific environments.
                If None, the message will be empty.
            :type  desired_state: :class:`DesiredState`
            :param desired_state: Defines the desired state. **Warning:** This attribute is available
                as Technology Preview. These are early access APIs provided to
                test, automate and provide feedback on the feature. Since this can
                change based on feedback, VMware does not guarantee backwards
                compatibility and recommends against using them in production
                environments. Some Technology Preview APIs might only be applicable
                to specific environments.
            """
            self.message = message
            self.desired_state = desired_state
            VapiStruct.__init__(self)


    ScanSpec._set_binding_type(type.StructType(
        'com.vmware.appliance.vcenter.settings.v1.config.scan_spec', {
            'message': type.OptionalType(type.StringType()),
            'desired_state': type.ReferenceType(__name__, 'DesiredState'),
        },
        ScanSpec,
        False,
        None))


    class CheckSpec(VapiStruct):
        """
        The ``Config.CheckSpec`` class contains attributes that describe desired
        profile check specification for vCenter. **Warning:** This class is
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
                     message=None,
                    ):
            """
            :type  message: :class:`str`
            :param message: Message to include with the check. **Warning:** This attribute is
                available as Technology Preview. These are early access APIs
                provided to test, automate and provide feedback on the feature.
                Since this can change based on feedback, VMware does not guarantee
                backwards compatibility and recommends against using them in
                production environments. Some Technology Preview APIs might only be
                applicable to specific environments.
            """
            self.message = message
            VapiStruct.__init__(self)


    CheckSpec._set_binding_type(type.StructType(
        'com.vmware.appliance.vcenter.settings.v1.config.check_spec', {
            'message': type.StringType(),
        },
        CheckSpec,
        False,
        None))


    class CheckDesiredStateSpec(VapiStruct):
        """
        The ``Config.CheckDesiredStateSpec`` class contains attributes that
        describe desired state spec check specification for vCenter. **Warning:**
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
                     desired_state=None,
                     check_spec=None,
                    ):
            """
            :type  desired_state: :class:`DesiredState`
            :param desired_state: Defines the desired state. **Warning:** This attribute is available
                as Technology Preview. These are early access APIs provided to
                test, automate and provide feedback on the feature. Since this can
                change based on feedback, VMware does not guarantee backwards
                compatibility and recommends against using them in production
                environments. Some Technology Preview APIs might only be applicable
                to specific environments.
            :type  check_spec: :class:`Config.CheckSpec`
            :param check_spec: checkSpec to include a message with the apply. **Warning:** This
                attribute is available as Technology Preview. These are early
                access APIs provided to test, automate and provide feedback on the
                feature. Since this can change based on feedback, VMware does not
                guarantee backwards compatibility and recommends against using them
                in production environments. Some Technology Preview APIs might only
                be applicable to specific environments.
            """
            self.desired_state = desired_state
            self.check_spec = check_spec
            VapiStruct.__init__(self)


    CheckDesiredStateSpec._set_binding_type(type.StructType(
        'com.vmware.appliance.vcenter.settings.v1.config.check_desired_state_spec', {
            'desired_state': type.ReferenceType(__name__, 'DesiredState'),
            'check_spec': type.ReferenceType(__name__, 'Config.CheckSpec'),
        },
        CheckDesiredStateSpec,
        False,
        None))


    class ApplySpec(VapiStruct):
        """
        The ``Config.ApplySpec`` class contains attributes that describe desired
        profile apply specification for vCenter. **Warning:** This class is
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
                     message=None,
                    ):
            """
            :type  message: :class:`str`
            :param message: Message to include with the apply. **Warning:** This attribute is
                available as Technology Preview. These are early access APIs
                provided to test, automate and provide feedback on the feature.
                Since this can change based on feedback, VMware does not guarantee
                backwards compatibility and recommends against using them in
                production environments. Some Technology Preview APIs might only be
                applicable to specific environments.
            """
            self.message = message
            VapiStruct.__init__(self)


    ApplySpec._set_binding_type(type.StructType(
        'com.vmware.appliance.vcenter.settings.v1.config.apply_spec', {
            'message': type.StringType(),
        },
        ApplySpec,
        False,
        None))


    class ApplyDesiredStateSpec(VapiStruct):
        """
        The ``Config.ApplyDesiredStateSpec`` class contains attributes that
        describe desired state spec apply specification for vCenter. **Warning:**
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
                     desired_state=None,
                     apply_spec=None,
                    ):
            """
            :type  desired_state: :class:`DesiredState`
            :param desired_state: Defines the desired state. **Warning:** This attribute is available
                as Technology Preview. These are early access APIs provided to
                test, automate and provide feedback on the feature. Since this can
                change based on feedback, VMware does not guarantee backwards
                compatibility and recommends against using them in production
                environments. Some Technology Preview APIs might only be applicable
                to specific environments.
            :type  apply_spec: :class:`Config.ApplySpec`
            :param apply_spec: applySpec to include a message with the apply. **Warning:** This
                attribute is available as Technology Preview. These are early
                access APIs provided to test, automate and provide feedback on the
                feature. Since this can change based on feedback, VMware does not
                guarantee backwards compatibility and recommends against using them
                in production environments. Some Technology Preview APIs might only
                be applicable to specific environments.
            """
            self.desired_state = desired_state
            self.apply_spec = apply_spec
            VapiStruct.__init__(self)


    ApplyDesiredStateSpec._set_binding_type(type.StructType(
        'com.vmware.appliance.vcenter.settings.v1.config.apply_desired_state_spec', {
            'desired_state': type.ReferenceType(__name__, 'DesiredState'),
            'apply_spec': type.ReferenceType(__name__, 'Config.ApplySpec'),
        },
        ApplyDesiredStateSpec,
        False,
        None))


    class ApplyResult(VapiStruct):
        """
        The ``Config.ApplyResult`` class contains attributes that describe the
        result of an apply operation. **Warning:** This class is available as
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
                     status=None,
                     start_time=None,
                     end_time=None,
                     notifications=None,
                     profile=None,
                     version=None,
                     success=None,
                     failed=None,
                     skipped=None,
                    ):
            """
            :type  status: :class:`Config.ApplyStatus`
            :param status: Specifies the aggregated status. **Warning:** This attribute is
                available as Technology Preview. These are early access APIs
                provided to test, automate and provide feedback on the feature.
                Since this can change based on feedback, VMware does not guarantee
                backwards compatibility and recommends against using them in
                production environments. Some Technology Preview APIs might only be
                applicable to specific environments.
            :type  start_time: :class:`datetime.datetime`
            :param start_time: Time when the method started. **Warning:** This attribute is
                available as Technology Preview. These are early access APIs
                provided to test, automate and provide feedback on the feature.
                Since this can change based on feedback, VMware does not guarantee
                backwards compatibility and recommends against using them in
                production environments. Some Technology Preview APIs might only be
                applicable to specific environments.
            :type  end_time: :class:`datetime.datetime` or ``None``
            :param end_time: Time when the method completed. **Warning:** This attribute is
                available as Technology Preview. These are early access APIs
                provided to test, automate and provide feedback on the feature.
                Since this can change based on feedback, VMware does not guarantee
                backwards compatibility and recommends against using them in
                production environments. Some Technology Preview APIs might only be
                applicable to specific environments.
                If None, the endTime will be empty.
            :type  notifications: :class:`Notifications`
            :param notifications: Notifications providing additional information about the status of
                the method. **Warning:** This attribute is available as Technology
                Preview. These are early access APIs provided to test, automate and
                provide feedback on the feature. Since this can change based on
                feedback, VMware does not guarantee backwards compatibility and
                recommends against using them in production environments. Some
                Technology Preview APIs might only be applicable to specific
                environments.
            :type  profile: :class:`str`
            :param profile: The identifier of the commit used to fetch the configuration state
                to be applied to all components within the appliance. **Warning:**
                This attribute is available as Technology Preview. These are early
                access APIs provided to test, automate and provide feedback on the
                feature. Since this can change based on feedback, VMware does not
                guarantee backwards compatibility and recommends against using them
                in production environments. Some Technology Preview APIs might only
                be applicable to specific environments.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.profile``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.profile``.
            :type  version: :class:`str`
            :param version: The version of the profile. **Warning:** This attribute is
                available as Technology Preview. These are early access APIs
                provided to test, automate and provide feedback on the feature.
                Since this can change based on feedback, VMware does not guarantee
                backwards compatibility and recommends against using them in
                production environments. Some Technology Preview APIs might only be
                applicable to specific environments.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.version``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.version``.
            :type  success: :class:`set` of :class:`str`
            :param success: Set of successfully applied components. **Warning:** This attribute
                is available as Technology Preview. These are early access APIs
                provided to test, automate and provide feedback on the feature.
                Since this can change based on feedback, VMware does not guarantee
                backwards compatibility and recommends against using them in
                production environments. Some Technology Preview APIs might only be
                applicable to specific environments.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.component``. When
                methods return a value of this class as a return value, the
                attribute will contain identifiers for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.component``.
            :type  failed: :class:`set` of :class:`str`
            :param failed: Set of failed components. **Warning:** This attribute is available
                as Technology Preview. These are early access APIs provided to
                test, automate and provide feedback on the feature. Since this can
                change based on feedback, VMware does not guarantee backwards
                compatibility and recommends against using them in production
                environments. Some Technology Preview APIs might only be applicable
                to specific environments.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.component``. When
                methods return a value of this class as a return value, the
                attribute will contain identifiers for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.component``.
            :type  skipped: :class:`set` of :class:`str`
            :param skipped: Set of skipped components. **Warning:** This attribute is available
                as Technology Preview. These are early access APIs provided to
                test, automate and provide feedback on the feature. Since this can
                change based on feedback, VMware does not guarantee backwards
                compatibility and recommends against using them in production
                environments. Some Technology Preview APIs might only be applicable
                to specific environments.
                When clients pass a value of this class as a parameter, the
                attribute must contain identifiers for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.component``. When
                methods return a value of this class as a return value, the
                attribute will contain identifiers for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.component``.
            """
            self.status = status
            self.start_time = start_time
            self.end_time = end_time
            self.notifications = notifications
            self.profile = profile
            self.version = version
            self.success = success
            self.failed = failed
            self.skipped = skipped
            VapiStruct.__init__(self)


    ApplyResult._set_binding_type(type.StructType(
        'com.vmware.appliance.vcenter.settings.v1.config.apply_result', {
            'status': type.ReferenceType(__name__, 'Config.ApplyStatus'),
            'start_time': type.DateTimeType(),
            'end_time': type.OptionalType(type.DateTimeType()),
            'notifications': type.ReferenceType(__name__, 'Notifications'),
            'profile': type.IdType(resource_types='com.vmware.appliance.vcenter.settings.v1.config.profile'),
            'version': type.IdType(resource_types='com.vmware.appliance.vcenter.settings.v1.config.version'),
            'success': type.SetType(type.IdType()),
            'failed': type.SetType(type.IdType()),
            'skipped': type.SetType(type.IdType()),
        },
        ApplyResult,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Config.Info`` class represents information about the config profile.
        the spec contains attributes that describe information about the profile.
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
                     profile=None,
                     version=None,
                     name=None,
                     creation_time=None,
                     owner=None,
                     description=None,
                     desired_state=None,
                    ):
            """
            :type  profile: :class:`str`
            :param profile: The identifier of the profile. **Warning:** This attribute is
                available as Technology Preview. These are early access APIs
                provided to test, automate and provide feedback on the feature.
                Since this can change based on feedback, VMware does not guarantee
                backwards compatibility and recommends against using them in
                production environments. Some Technology Preview APIs might only be
                applicable to specific environments.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.profile``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.profile``.
            :type  version: :class:`str`
            :param version: Version of the profile. **Warning:** This attribute is available as
                Technology Preview. These are early access APIs provided to test,
                automate and provide feedback on the feature. Since this can change
                based on feedback, VMware does not guarantee backwards
                compatibility and recommends against using them in production
                environments. Some Technology Preview APIs might only be applicable
                to specific environments.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.version``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.appliance.vcenter.settings.v1.config.version``.
            :type  name: :class:`str`
            :param name: Name of the profile. **Warning:** This attribute is available as
                Technology Preview. These are early access APIs provided to test,
                automate and provide feedback on the feature. Since this can change
                based on feedback, VMware does not guarantee backwards
                compatibility and recommends against using them in production
                environments. Some Technology Preview APIs might only be applicable
                to specific environments.
            :type  creation_time: :class:`datetime.datetime`
            :param creation_time: Creation time of the profile. **Warning:** This attribute is
                available as Technology Preview. These are early access APIs
                provided to test, automate and provide feedback on the feature.
                Since this can change based on feedback, VMware does not guarantee
                backwards compatibility and recommends against using them in
                production environments. Some Technology Preview APIs might only be
                applicable to specific environments.
            :type  owner: :class:`str`
            :param owner: Owner of the profile, the one who created. **Warning:** This
                attribute is available as Technology Preview. These are early
                access APIs provided to test, automate and provide feedback on the
                feature. Since this can change based on feedback, VMware does not
                guarantee backwards compatibility and recommends against using them
                in production environments. Some Technology Preview APIs might only
                be applicable to specific environments.
            :type  description: :class:`str` or ``None``
            :param description: Custom description provided by the user. **Warning:** This
                attribute is available as Technology Preview. These are early
                access APIs provided to test, automate and provide feedback on the
                feature. Since this can change based on feedback, VMware does not
                guarantee backwards compatibility and recommends against using them
                in production environments. Some Technology Preview APIs might only
                be applicable to specific environments.
                If None description will be empty.
            :type  desired_state: :class:`DesiredState`
            :param desired_state: The desired state. **Warning:** This attribute is available as
                Technology Preview. These are early access APIs provided to test,
                automate and provide feedback on the feature. Since this can change
                based on feedback, VMware does not guarantee backwards
                compatibility and recommends against using them in production
                environments. Some Technology Preview APIs might only be applicable
                to specific environments.
            """
            self.profile = profile
            self.version = version
            self.name = name
            self.creation_time = creation_time
            self.owner = owner
            self.description = description
            self.desired_state = desired_state
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.appliance.vcenter.settings.v1.config.info', {
            'profile': type.IdType(resource_types='com.vmware.appliance.vcenter.settings.v1.config.profile'),
            'version': type.IdType(resource_types='com.vmware.appliance.vcenter.settings.v1.config.version'),
            'name': type.StringType(),
            'creation_time': type.DateTimeType(),
            'owner': type.StringType(),
            'description': type.OptionalType(type.StringType()),
            'desired_state': type.ReferenceType(__name__, 'DesiredState'),
        },
        Info,
        False,
        None))



    def create(self,
               spec,
               ):
        """
        Creates a Profile. **Warning:** This method is available as Technology
        Preview. These are early access APIs provided to test, automate and
        provide feedback on the feature. Since this can change based on
        feedback, VMware does not guarantee backwards compatibility and
        recommends against using them in production environments. Some
        Technology Preview APIs might only be applicable to specific
        environments.

        :type  spec: :class:`Config.CreateSpec`
        :param spec: Specification of the profile to be created.
        :rtype: :class:`str`
        :return: ID of newly-created profile.
            The return value will be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.profile``.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if a profile with the specified name already exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if any of the specified parameters are invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``Infraprofile.Write``.
        """
        return self._invoke('create',
                            {
                            'spec': spec,
                            })

    def get(self):
        """
        Returns information about a profile. **Warning:** This method is
        available as Technology Preview. These are early access APIs provided
        to test, automate and provide feedback on the feature. Since this can
        change based on feedback, VMware does not guarantee backwards
        compatibility and recommends against using them in production
        environments. Some Technology Preview APIs might only be applicable to
        specific environments.


        :rtype: :class:`Config.Info`
        :return: Information about the specified profile.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If given version is different than the latest one.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no profile or version associated with ``profile`` or
            ``version`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``Infraprofile.Read``.
        """
        return self._invoke('get', None)

    def delete(self):
        """
        Deletes a profile. **Warning:** This method is available as Technology
        Preview. These are early access APIs provided to test, automate and
        provide feedback on the feature. Since this can change based on
        feedback, VMware does not guarantee backwards compatibility and
        recommends against using them in production environments. Some
        Technology Preview APIs might only be applicable to specific
        environments.


        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if any other operation running on the same profile.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the profile is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate service to complete the
            request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``Infraprofile.Write``.
        """
        return self._invoke('delete', None)


    def scan_task(self,
             version,
             ):
        """
        Scans all the components in the profiles against the applied profile.
        result of this operation can be queried by calling the api
        cis/tasks/{task-id} where the task-id is the response of this
        operation. **Warning:** This method is available as Technology Preview.
        These are early access APIs provided to test, automate and provide
        feedback on the feature. Since this can change based on feedback,
        VMware does not guarantee backwards compatibility and recommends
        against using them in production environments. Some Technology Preview
        APIs might only be applicable to specific environments.

        :type  version: :class:`str`
        :param version: version of the profile.
            The parameter must be an identifier for the resource type:
            ``com.vmware.appliance.vcenter.settings.v1.config.version``.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            If there is no profile associated with ``profile`` in the system.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('scan$task',
                                {
                                'version': version,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'ScanResult'))
        return task_instance


    def scan_desired_state_task(self,
                           spec,
                           ):
        """
        Scans all the components in the desired state against the applied
        profile. result of this operation can be queried by calling the api
        cis/tasks/{task-id} where the task-id is the response of this
        operation. **Warning:** This method is available as Technology Preview.
        These are early access APIs provided to test, automate and provide
        feedback on the feature. Since this can change based on feedback,
        VMware does not guarantee backwards compatibility and recommends
        against using them in production environments. Some Technology Preview
        APIs might only be applicable to specific environments.

        :type  spec: :class:`Config.ScanSpec`
        :param spec: 
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('scan_desired_state$task',
                                {
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'ScanResult'))
        return task_instance


    def check_desired_state_task(self,
                            spec,
                            ):
        """
        Validate (Check) the specified DesiredState spec containing
        configurations, and verify if it can be applied to the vCenter. The
        result of this operation can be queried by calling the
        cis/tasks/{task-id} where the task-id is the response of this
        operation. **Warning:** This method is available as Technology Preview.
        These are early access APIs provided to test, automate and provide
        feedback on the feature. Since this can change based on feedback,
        VMware does not guarantee backwards compatibility and recommends
        against using them in production environments. Some Technology Preview
        APIs might only be applicable to specific environments.

        :type  spec: :class:`Config.CheckDesiredStateSpec`
        :param spec: CheckDesiredStateSpec spec to be validated.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('check_desired_state$task',
                                {
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'CheckResult'))
        return task_instance


    def apply_desired_state_task(self,
                            spec,
                            ):
        """
        Apply the specified DesiredState spec to the vCenter. The result of
        this operation can be queried by calling the cis/tasks/{task-id} where
        the task-id is the response of this operation. **Warning:** This method
        is available as Technology Preview. These are early access APIs
        provided to test, automate and provide feedback on the feature. Since
        this can change based on feedback, VMware does not guarantee backwards
        compatibility and recommends against using them in production
        environments. Some Technology Preview APIs might only be applicable to
        specific environments.

        :type  spec: :class:`Config.ApplyDesiredStateSpec`
        :param spec: ApplyDesiredStateSpec spec to be validated and applied.
        :rtype: :class:  `vmware.vapi.stdlib.client.task.Task`
        :return: Task instance
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            If there is another operation in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            If validation of the desired-state spec fails. The value of the
            data attribute of :class:`com.vmware.vapi.std.errors_client.Error`
            will be a class that contains all the attributes defined in
            :class:`Config.ApplyResult`.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        """
        task_id = self._invoke('apply_desired_state$task',
                                {
                                'spec': spec,
                                })
        task_svc = Tasks(self._config)
        task_instance = Task(task_id, task_svc, type.ReferenceType(__name__, 'Config.ApplyResult'))
        return task_instance
class ConfigCurrent(VapiInterface):
    """
    The ``ConfigCurrent`` class provides methods to get the current state of
    the vCenter. **Warning:** This class is available as Technology Preview.
    These are early access APIs provided to test, automate and provide feedback
    on the feature. Since this can change based on feedback, VMware does not
    guarantee backwards compatibility and recommends against using them in
    production environments. Some Technology Preview APIs might only be
    applicable to specific environments.
    """

    _VAPI_SERVICE_ID = 'com.vmware.appliance.vcenter.settings.v1.config_current'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ConfigCurrentStub)
        self._VAPI_OPERATION_IDS = {}

    class InvokerType(Enum):
        """
        The ``ConfigCurrent.InvokerType`` class contains the possible invoker type,
        to be passed on to plugins to understand the consumer. **Warning:** This
        enumeration is available as Technology Preview. These are early access APIs
        provided to test, automate and provide feedback on the feature. Since this
        can change based on feedback, VMware does not guarantee backwards
        compatibility and recommends against using them in production environments.
        Some Technology Preview APIs might only be applicable to specific
        environments.

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
        Invoker is an end user. **Warning:** This class attribute is available as
        Technology Preview. These are early access APIs provided to test, automate
        and provide feedback on the feature. Since this can change based on
        feedback, VMware does not guarantee backwards compatibility and recommends
        against using them in production environments. Some Technology Preview APIs
        might only be applicable to specific environments.

        """
        INTERNAL = None
        """
        Invoker requires internal config details in DS spec. **Warning:** This
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
            :param string: String value for the :class:`InvokerType` instance.
            """
            Enum.__init__(string)

    InvokerType._set_values({
        'USER': InvokerType('USER'),
        'INTERNAL': InvokerType('INTERNAL'),
    })
    InvokerType._set_binding_type(type.EnumType(
        'com.vmware.appliance.vcenter.settings.v1.config_current.invoker_type',
        InvokerType))



    def get(self,
            invoker_type=None,
            components=None,
            ):
        """
        Returns the current state of the vCenter. **Warning:** This method is
        available as Technology Preview. These are early access APIs provided
        to test, automate and provide feedback on the feature. Since this can
        change based on feedback, VMware does not guarantee backwards
        compatibility and recommends against using them in production
        environments. Some Technology Preview APIs might only be applicable to
        specific environments.

        :type  invoker_type: :class:`ConfigCurrent.InvokerType` or ``None``
        :param invoker_type: 
        :type  components: :class:`set` of :class:`str` or ``None``
        :param components: 
        :rtype: :class:`DesiredState`
        :return: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is unknown internal error. The accompanying error message
            will give more details about the failure.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            If the service is not available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            If the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * Method execution requires ``Infraprofile.Read``.
        """
        return self._invoke('get',
                            {
                            'invoker_type': invoker_type,
                            'components': components,
                            })
class _ConfigStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Config.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
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
            url_template='/appliance/vcenter/settings/v1/config',
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

        # properties for get operation
        get_input_type = type.StructType('operation-input', {})
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
            url_template='/appliance/vcenter/settings/v1/config',
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
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/appliance/vcenter/settings/v1/config',
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

        # properties for scan operation
        scan_input_type = type.StructType('operation-input', {
            'version': type.IdType(resource_types='com.vmware.appliance.vcenter.settings.v1.config.version'),
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
            url_template='/appliance/vcenter/settings/v1/config/{version}',
            path_variables={
                'version': 'version',
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

        # properties for scan_desired_state operation
        scan_desired_state_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Config.ScanSpec'),
        })
        scan_desired_state_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        scan_desired_state_input_value_validator_list = [
        ]
        scan_desired_state_output_validator_list = [
        ]
        scan_desired_state_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/appliance/vcenter/settings/v1/config',
            request_body_parameter='spec',
            path_variables={
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'scan-desired-state',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for check_desired_state operation
        check_desired_state_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Config.CheckDesiredStateSpec'),
        })
        check_desired_state_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        check_desired_state_input_value_validator_list = [
        ]
        check_desired_state_output_validator_list = [
        ]
        check_desired_state_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/appliance/vcenter/settings/v1/config',
            request_body_parameter='spec',
            path_variables={
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'check-desired-state',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for apply_desired_state operation
        apply_desired_state_input_type = type.StructType('operation-input', {
            'spec': type.ReferenceType(__name__, 'Config.ApplyDesiredStateSpec'),
        })
        apply_desired_state_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        apply_desired_state_input_value_validator_list = [
        ]
        apply_desired_state_output_validator_list = [
        ]
        apply_desired_state_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/appliance/vcenter/settings/v1/config',
            request_body_parameter='spec',
            path_variables={
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'apply-desired-state',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'create': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.appliance.vcenter.settings.v1.config.profile'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Config.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
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
            'scan$task': {
                'input_type': scan_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': scan_error_dict,
                'input_value_validator_list': scan_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'scan_desired_state$task': {
                'input_type': scan_desired_state_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': scan_desired_state_error_dict,
                'input_value_validator_list': scan_desired_state_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'check_desired_state$task': {
                'input_type': check_desired_state_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': check_desired_state_error_dict,
                'input_value_validator_list': check_desired_state_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
            'apply_desired_state$task': {
                'input_type': apply_desired_state_input_type,
                'output_type': type.IdType(resource_types='com.vmware.cis.TASK'),
                'errors': apply_desired_state_error_dict,
                'input_value_validator_list': apply_desired_state_input_value_validator_list,
                'output_validator_list': [],
                'task_type': TaskType.TASK_ONLY,
            },
        }
        rest_metadata = {
            'create': create_rest_metadata,
            'get': get_rest_metadata,
            'delete': delete_rest_metadata,
            'scan': scan_rest_metadata,
            'scan_desired_state': scan_desired_state_rest_metadata,
            'check_desired_state': check_desired_state_rest_metadata,
            'apply_desired_state': apply_desired_state_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.appliance.vcenter.settings.v1.config',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _ConfigCurrentStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'invoker_type': type.OptionalType(type.ReferenceType(__name__, 'ConfigCurrent.InvokerType')),
            'components': type.OptionalType(type.SetType(type.StringType())),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
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
            url_template='/appliance/vcenter/settings/v1/config-current',
            path_variables={
            },
            query_parameters={
                'invoker_type': 'invoker_type',
                'components': 'components',
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
                'output_type': type.ReferenceType(__name__, 'DesiredState'),
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
            self, iface_name='com.vmware.appliance.vcenter.settings.v1.config_current',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Config': Config,
        'ConfigCurrent': ConfigCurrent,
        'config': 'com.vmware.appliance.vcenter.settings.v1.config_client.StubFactory',
    }

