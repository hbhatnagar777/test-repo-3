# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.snapservice.clusters.virtual_machines.disks.
#---------------------------------------------------------------------------

"""
The ``com.vmware.snapservice.clusters.virtual_machines.disks_client`` module
provides classes for managing virtual machine disks in a vSAN cluster.

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


class Snapshots(VapiInterface):
    """
    The ``Snapshots`` class provides methods to manage snapshots for virtual
    disks.
    """

    _VAPI_SERVICE_ID = 'com.vmware.snapservice.clusters.virtual_machines.disks.snapshots'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SnapshotsStub)
        self._VAPI_OPERATION_IDS = {}

    class Info(VapiStruct):
        """
        Information regarding a virtual disk snapshot.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     disk_key=None,
                     sequence_uuid=None,
                     epoch=None,
                     uri=None,
                    ):
            """
            :type  disk_key: :class:`long`
            :param disk_key: Identifier of the virtual disk this snapshot is for.
            :type  sequence_uuid: :class:`str`
            :param sequence_uuid: A sequence UUID represents an "epoch sequence". This is a stable
                UUID across epochs. In the event that the state of LWD becomes
                inconsistent (e.g. VM snapshot revert), a new sequence UUID is
                generated and the epoch counter is reset. The sequence UUID is a
                mechanism to ensure snapshots are consistent in linear time across
                epochs.
            :type  epoch: :class:`long`
            :param epoch: An epoch represents the "logical time" of the snapshot, and is an
                unsigned integer that will be incremented by at least 1 every time
                a snapshot is taken.
            :type  uri: :class:`str`
            :param uri: Represents the vSAN native snapshot URI when native snapshots were
                created by LWD.
            """
            self.disk_key = disk_key
            self.sequence_uuid = sequence_uuid
            self.epoch = epoch
            self.uri = uri
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.snapservice.clusters.virtual_machines.disks.snapshots.info', {
            'disk_key': type.IntegerType(),
            'sequence_uuid': type.StringType(),
            'epoch': type.IntegerType(),
            'uri': type.StringType(),
        },
        Info,
        False,
        None))


class _SnapshotsStub(ApiInterfaceStub):
    def __init__(self, config):
        operations = {
        }
        rest_metadata = {
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.snapservice.clusters.virtual_machines.disks.snapshots',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Snapshots': Snapshots,
    }

