# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.esx.hostd.
#---------------------------------------------------------------------------

"""
The ``com.vmware.esx.attestation`` module provides classes to manage features
supported by hostd Service.

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


class Notifier(VapiInterface):
    """
    The ``NotificationManager`` class provides methods for notifying hostd for
    changes. This is internal API which is used by ConfigStore framework on
    ESXi host to notify hostd about configurations that were updated.
    **Note:** This class is restricted for **VMware internal use only**.
    """

    _VAPI_SERVICE_ID = 'com.vmware.esx.hostd.notifier'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _NotifierStub)
        self._VAPI_OPERATION_IDS = {}


    def notify(self,
               identifiers,
               cartel_id,
               ):
        """
        

        :type  identifiers: :class:`list` of :class:`str`
        :param identifiers: 
        :type  cartel_id: :class:`long`
        :param cartel_id: 
        """
        return self._invoke('notify',
                            {
                            'identifiers': identifiers,
                            'cartel_id': cartel_id,
                            })
class _NotifierStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for notify operation
        notify_input_type = type.StructType('operation-input', {
            'identifiers': type.ListType(type.StringType()),
            'cartel_id': type.IntegerType(),
        })
        notify_error_dict = {}
        notify_input_value_validator_list = [
        ]
        notify_output_validator_list = [
        ]
        notify_rest_metadata = None

        operations = {
            'notify': {
                'input_type': notify_input_type,
                'output_type': type.VoidType(),
                'errors': notify_error_dict,
                'input_value_validator_list': notify_input_value_validator_list,
                'output_validator_list': notify_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'notify': notify_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.esx.hostd.notifier',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Notifier': Notifier,
    }

