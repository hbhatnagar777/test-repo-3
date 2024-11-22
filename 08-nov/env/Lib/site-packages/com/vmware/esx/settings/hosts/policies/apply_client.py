# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.settings.hosts.policies.apply.
#---------------------------------------------------------------------------

"""
The ``com.vmware.esx.settings.hosts.policies.apply_client`` module provides
classes to manage the policies that affect application of desired state
configuration and software for an ESXi host. Copyright (c) 2019-2023 VMware,
Inc. All rights reserved. -- VMware Confidential Copyright (c) 2019-2023
VMware, Inc. All rights reserved. -- VMware Confidential

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


class Effective(VapiInterface):
    """
    The ``Effective`` class provides methods to manage the effective policies
    that will impact how the software and configuration specification documents
    are applied to an ESXi host. This class was added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.settings.hosts.policies.apply.effective'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _EffectiveStub)
        self._VAPI_OPERATION_IDS = {}

    class FailureAction(VapiStruct):
        """
        The ``Effective.FailureAction`` class contains attributes that describe the
        actions to be taken when entering maintenance mode fails on an ESXi host.
        This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'action',
                {
                    'RETRY' : [('retry_delay', True), ('retry_count', True)],
                    'FAIL' : [],
                }
            ),
        ]



        def __init__(self,
                     action=None,
                     retry_delay=None,
                     retry_count=None,
                    ):
            """
            :type  action: :class:`Effective.FailureAction.Action`
            :param action: What action (FAIL, RETRY) is to be taken if entering maintenance
                mode fails on an ESXi host. This attribute was added in vSphere API
                8.0.0.1.
            :type  retry_delay: :class:`long`
            :param retry_delay: Time to wait to retry the failed operation in seconds. This
                attribute was added in vSphere API 8.0.0.1.
                This attribute is optional and it is only relevant when the value
                of ``action`` is :attr:`Effective.FailureAction.Action.RETRY`.
            :type  retry_count: :class:`long`
            :param retry_count: Number of times to retry the failed operation. This attribute was
                added in vSphere API 8.0.0.1.
                This attribute is optional and it is only relevant when the value
                of ``action`` is :attr:`Effective.FailureAction.Action.RETRY`.
            """
            self.action = action
            self.retry_delay = retry_delay
            self.retry_count = retry_count
            VapiStruct.__init__(self)


        class Action(Enum):
            """
            The ``Effective.FailureAction.Action`` class defines the actions to be
            taken when entering maintenance mode fails on an ESXi host. This
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
            FAIL = None
            """
            Fail the apply method. This class attribute was added in vSphere API
            8.0.0.1.

            """
            RETRY = None
            """
            Retry the task Apply.FailureAction#retryCount number of times on the failed
            host after Apply.FailureAction#retryDelay. This class attribute was added
            in vSphere API 8.0.0.1.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`Action` instance.
                """
                Enum.__init__(string)

        Action._set_values({
            'FAIL': Action('FAIL'),
            'RETRY': Action('RETRY'),
        })
        Action._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.hosts.policies.apply.effective.failure_action.action',
            Action))

    FailureAction._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.policies.apply.effective.failure_action', {
            'action': type.ReferenceType(__name__, 'Effective.FailureAction.Action'),
            'retry_delay': type.OptionalType(type.IntegerType()),
            'retry_count': type.OptionalType(type.IntegerType()),
        },
        FailureAction,
        False,
        None))


    class EffectivePolicySpec(VapiStruct):
        """
        The ``Effective.EffectivePolicySpec`` class contains attributes that
        describe the effective policies to be used when the software and
        configuration specification documents are applied to ESXi hosts. This class
        was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     failure_action=None,
                     pre_remediation_power_action=None,
                     enable_quick_boot=None,
                    ):
            """
            :type  failure_action: :class:`Effective.FailureAction`
            :param failure_action: What action is to be taken if entering maintenance mode fails on an
                ESXi host. This attribute was added in vSphere API 8.0.0.1.
            :type  pre_remediation_power_action: :class:`Effective.EffectivePolicySpec.PreRemediationPowerAction`
            :param pre_remediation_power_action: Specifies what should be done to the power state of the VM before
                entering maintenance mode. This attribute was added in vSphere API
                8.0.0.1.
            :type  enable_quick_boot: :class:`bool`
            :param enable_quick_boot: Enable Quick Boot during remediation of an ESXi host. This
                attribute was added in vSphere API 8.0.0.1.
            """
            self.failure_action = failure_action
            self.pre_remediation_power_action = pre_remediation_power_action
            self.enable_quick_boot = enable_quick_boot
            VapiStruct.__init__(self)


        class PreRemediationPowerAction(Enum):
            """
            The ``Effective.EffectivePolicySpec.PreRemediationPowerAction`` class
            defines the possible actions to take, before entering maintenance mode.
            This enumeration was added in vSphere API 8.0.0.1.

            .. note::
                This class represents an enumerated type in the interface language
                definition. The class contains class attributes which represent the
                values in the current version of the enumerated type. Newer versions of
                the enumerated type may contain new values. To use new values of the
                enumerated type in communication with a server that supports the newer
                version of the API, you instantiate this class. See :ref:`enumerated
                type description page <enumeration_description>`.
            """
            POWER_OFF_VMS = None
            """
            Power off VMs before entering maintenance mode. This class attribute was
            added in vSphere API 8.0.0.1.

            """
            SUSPEND_VMS = None
            """
            Suspend VMs before entering maintenance mode. This class attribute was
            added in vSphere API 8.0.0.1.

            """
            DO_NOT_CHANGE_VMS_POWER_STATE = None
            """
            Do not change the VM power state. This class attribute was added in vSphere
            API 8.0.0.1.

            """
            SUSPEND_VMS_TO_MEMORY = None
            """
            Suspend VMs to Memory before entering maintenance mode. This class
            attribute was added in vSphere API 8.0.0.1.

            """

            def __init__(self, string):
                """
                :type  string: :class:`str`
                :param string: String value for the :class:`PreRemediationPowerAction` instance.
                """
                Enum.__init__(string)

        PreRemediationPowerAction._set_values({
            'POWER_OFF_VMS': PreRemediationPowerAction('POWER_OFF_VMS'),
            'SUSPEND_VMS': PreRemediationPowerAction('SUSPEND_VMS'),
            'DO_NOT_CHANGE_VMS_POWER_STATE': PreRemediationPowerAction('DO_NOT_CHANGE_VMS_POWER_STATE'),
            'SUSPEND_VMS_TO_MEMORY': PreRemediationPowerAction('SUSPEND_VMS_TO_MEMORY'),
        })
        PreRemediationPowerAction._set_binding_type(type.EnumType(
            'com.vmware.esx.settings.hosts.policies.apply.effective.effective_policy_spec.pre_remediation_power_action',
            PreRemediationPowerAction))

    EffectivePolicySpec._set_binding_type(type.StructType(
        'com.vmware.esx.settings.hosts.policies.apply.effective.effective_policy_spec', {
            'failure_action': type.ReferenceType(__name__, 'Effective.FailureAction'),
            'pre_remediation_power_action': type.ReferenceType(__name__, 'Effective.EffectivePolicySpec.PreRemediationPowerAction'),
            'enable_quick_boot': type.BooleanType(),
        },
        EffectivePolicySpec,
        False,
        None))



    def get(self,
            host,
            ):
        """
        Returns the effective policy based on system defaults and what has been
        configured for the ESXi host. This method was added in vSphere API
        8.0.0.1.

        :type  host: :class:`str`
        :param host: The host identifier.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :rtype: :class:`Effective.EffectivePolicySpec`
        :return: The effective policies that impact the apply method
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            If there is an unknown internal error. The accompanying error
            message will give more details about the failure.
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
            
            * Method execution requires ``VcIntegrity.lifecycleSettings.Read``.
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``VcIntegrity.lifecycleSettings.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            })
class _EffectiveStub(ApiInterfaceStub):
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
            url_template='/esx/settings/hosts/{host}/policies/apply/effective',
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
                'output_type': type.ReferenceType(__name__, 'Effective.EffectivePolicySpec'),
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
            self, iface_name='com.vmware.esx.settings.hosts.policies.apply.effective',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Effective': Effective,
    }

