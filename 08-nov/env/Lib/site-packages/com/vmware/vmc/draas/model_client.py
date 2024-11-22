# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright 2023 VMware, Inc.  All rights reserved.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vmc.draas.model.
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


class AbstractEntity(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'id': 'id',
                            'version': 'version',
                            'created': 'created',
                            'user_id': 'user_id',
                            'user_name': 'user_name',
                            'updated': 'updated',
                            'updated_by_user_id': 'updated_by_user_id',
                            'updated_by_user_name': 'updated_by_user_name',
                            }

    def __init__(self,
                 id=None,
                 version=None,
                 created=None,
                 user_id=None,
                 user_name=None,
                 updated=None,
                 updated_by_user_id=None,
                 updated_by_user_name=None,
                ):
        """
        :type  id: :class:`str`
        :param id: 
        :type  version: :class:`long`
        :param version: Version of this entity format: int32
        :type  created: :class:`datetime.datetime`
        :param created: 
        :type  user_id: :class:`str`
        :param user_id: User id that last updated this record
        :type  user_name: :class:`str`
        :param user_name: User name that last updated this record
        :type  updated: :class:`datetime.datetime`
        :param updated: 
        :type  updated_by_user_id: :class:`str`
        :param updated_by_user_id: User id that last updated this record
        :type  updated_by_user_name: :class:`str`
        :param updated_by_user_name: User name that last updated this record
        """
        self.id = id
        self.version = version
        self.created = created
        self.user_id = user_id
        self.user_name = user_name
        self.updated = updated
        self.updated_by_user_id = updated_by_user_id
        self.updated_by_user_name = updated_by_user_name
        VapiStruct.__init__(self)


AbstractEntity._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.abstract_entity', {
        'id': type.StringType(),
        'version': type.IntegerType(),
        'created': type.DateTimeType(),
        'user_id': type.StringType(),
        'user_name': type.StringType(),
        'updated': type.DateTimeType(),
        'updated_by_user_id': type.StringType(),
        'updated_by_user_name': type.StringType(),
    },
    AbstractEntity,
    False,
    None))



class ActivateSiteRecoveryConfig(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'srm_extension_key_suffix': 'srm_extension_key_suffix',
                            }

    def __init__(self,
                 srm_extension_key_suffix=None,
                ):
        """
        :type  srm_extension_key_suffix: :class:`str` or ``None``
        :param srm_extension_key_suffix: Optional custom extension key suffix for SRM. If not specified,
            default extension key will be used. The custom extension suffix
            must contain 13 characters or less, be composed of letters,
            numbers, ., -, and _ characters. The extension suffix must begin
            and end with a letter or number. The suffix is appended to
            com.vmware.vcDr- to form the full extension key.
        """
        self.srm_extension_key_suffix = srm_extension_key_suffix
        VapiStruct.__init__(self)


ActivateSiteRecoveryConfig._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.activate_site_recovery_config', {
        'srm_extension_key_suffix': type.OptionalType(type.StringType()),
    },
    ActivateSiteRecoveryConfig,
    False,
    None))



class BuildVersion(VapiStruct):
    """
    The build version.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'version': 'version',
                            'build_number': 'build_number',
                            }

    def __init__(self,
                 version=None,
                 build_number=None,
                ):
        """
        :type  version: :class:`str` or ``None``
        :param version: 
        :type  build_number: :class:`str` or ``None``
        :param build_number: 
        """
        self.version = version
        self.build_number = build_number
        VapiStruct.__init__(self)


BuildVersion._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.build_version', {
        'version': type.OptionalType(type.StringType()),
        'build_number': type.OptionalType(type.StringType()),
    },
    BuildVersion,
    False,
    None))



class DatastoreEntity(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'id': 'id',
                            'name': 'name',
                            'datastore_type': 'datastore_type',
                            'instance_type': 'instance_type',
                            'number_of_hosts': 'number_of_hosts',
                            'replications_number': 'replications_number',
                            'total_datastore_size': 'total_datastore_size',
                            'replica_disks': 'replica_disks',
                            }

    def __init__(self,
                 id=None,
                 name=None,
                 datastore_type=None,
                 instance_type=None,
                 number_of_hosts=None,
                 replications_number=None,
                 total_datastore_size=None,
                 replica_disks=None,
                ):
        """
        :type  id: :class:`str` or ``None``
        :param id: 
        :type  name: :class:`str` or ``None``
        :param name: 
        :type  datastore_type: :class:`str` or ``None``
        :param datastore_type: 
        :type  instance_type: :class:`str` or ``None``
        :param instance_type: 
        :type  number_of_hosts: :class:`float` or ``None``
        :param number_of_hosts: 
        :type  replications_number: :class:`float` or ``None``
        :param replications_number: 
        :type  total_datastore_size: :class:`float` or ``None``
        :param total_datastore_size: 
        :type  replica_disks: :class:`list` of :class:`ReplicaDisk` or ``None``
        :param replica_disks: 
        """
        self.id = id
        self.name = name
        self.datastore_type = datastore_type
        self.instance_type = instance_type
        self.number_of_hosts = number_of_hosts
        self.replications_number = replications_number
        self.total_datastore_size = total_datastore_size
        self.replica_disks = replica_disks
        VapiStruct.__init__(self)


DatastoreEntity._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.datastore_entity', {
        'id': type.OptionalType(type.StringType()),
        'name': type.OptionalType(type.StringType()),
        'datastore_type': type.OptionalType(type.StringType()),
        'instance_type': type.OptionalType(type.StringType()),
        'number_of_hosts': type.OptionalType(type.DoubleType()),
        'replications_number': type.OptionalType(type.DoubleType()),
        'total_datastore_size': type.OptionalType(type.DoubleType()),
        'replica_disks': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ReplicaDisk'))),
    },
    DatastoreEntity,
    False,
    None))



class DeleteConfigInternal(VapiStruct):
    """
    Deactivate Site Recovery or delete Site Recovery node configuration

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'force': 'force',
                            'ticket': 'ticket',
                            'confirmation_code': 'confirmation_code',
                            }

    def __init__(self,
                 force=None,
                 ticket=None,
                 confirmation_code=None,
                ):
        """
        :type  force: :class:`bool` or ``None``
        :param force: If = 'true', will deactivate site recovery forcefully.
        :type  ticket: :class:`str` or ``None``
        :param ticket: CSSD/CSCM ticket number, such as CSSD-xxxx/CSCM-xxxx
        :type  confirmation_code: :class:`str` or ``None``
        :param confirmation_code: The confirmation code generated in prepare delete operation.
        """
        self.force = force
        self.ticket = ticket
        self.confirmation_code = confirmation_code
        VapiStruct.__init__(self)


DeleteConfigInternal._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.delete_config_internal', {
        'force': type.OptionalType(type.BooleanType()),
        'ticket': type.OptionalType(type.StringType()),
        'confirmation_code': type.OptionalType(type.StringType()),
    },
    DeleteConfigInternal,
    False,
    None))



class ErrorResponse(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'error_code': 'error_code',
                            'error_messages': 'error_messages',
                            'status': 'status',
                            'path': 'path',
                            'retryable': 'retryable',
                            }

    def __init__(self,
                 error_code=None,
                 error_messages=None,
                 status=None,
                 path=None,
                 retryable=None,
                ):
        """
        :type  error_code: :class:`str`
        :param error_code: unique error code
        :type  error_messages: :class:`list` of :class:`str`
        :param error_messages: localized error messages
        :type  status: :class:`long`
        :param status: HTTP status code
        :type  path: :class:`str`
        :param path: Originating request URI
        :type  retryable: :class:`bool`
        :param retryable: If true, client should retry operation
        """
        self.error_code = error_code
        self.error_messages = error_messages
        self.status = status
        self.path = path
        self.retryable = retryable
        VapiStruct.__init__(self)


ErrorResponse._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.error_response', {
        'error_code': type.StringType(),
        'error_messages': type.ListType(type.StringType()),
        'status': type.IntegerType(),
        'path': type.StringType(),
        'retryable': type.BooleanType(),
    },
    ErrorResponse,
    False,
    None))



class Fault(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'message': 'message',
                            'cause': 'cause',
                            }

    def __init__(self,
                 message=None,
                 cause=None,
                ):
        """
        :type  message: :class:`str` or ``None``
        :param message: 
        :type  cause: :class:`vmware.vapi.struct.VapiStruct` or ``None``
        :param cause: 
        """
        self.message = message
        self.cause = cause
        VapiStruct.__init__(self)


Fault._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.fault', {
        'message': type.OptionalType(type.StringType()),
        'cause': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
    },
    Fault,
    False,
    None))



class HmsIssueInfo(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'target_object_name': 'target_object_name',
                            'target_object_mo_id': 'target_object_mo_id',
                            'triggered_time': 'triggered_time',
                            'issue_type': 'issue_type',
                            'fault': 'fault',
                            'severity': 'severity',
                            }

    def __init__(self,
                 target_object_name=None,
                 target_object_mo_id=None,
                 triggered_time=None,
                 issue_type=None,
                 fault=None,
                 severity=None,
                ):
        """
        :type  target_object_name: :class:`str` or ``None``
        :param target_object_name: 
        :type  target_object_mo_id: :class:`str`
        :param target_object_mo_id: 
        :type  triggered_time: :class:`datetime.datetime`
        :param triggered_time: 
        :type  issue_type: :class:`str`
        :param issue_type: 
        :type  fault: :class:`Fault` or ``None``
        :param fault: 
        :type  severity: :class:`str`
        :param severity: 
        """
        self.target_object_name = target_object_name
        self.target_object_mo_id = target_object_mo_id
        self.triggered_time = triggered_time
        self.issue_type = issue_type
        self.fault = fault
        self.severity = severity
        VapiStruct.__init__(self)


HmsIssueInfo._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.hms_issue_info', {
        'target_object_name': type.OptionalType(type.StringType()),
        'target_object_mo_id': type.StringType(),
        'triggered_time': type.DateTimeType(),
        'issue_type': type.StringType(),
        'fault': type.OptionalType(type.ReferenceType(__name__, 'Fault')),
        'severity': type.StringType(),
    },
    HmsIssueInfo,
    False,
    None))



class HmsReplicationIssueInfo(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'target_object_name': 'target_object_name',
                            'target_object_mo_id': 'target_object_mo_id',
                            'triggered_time': 'triggered_time',
                            'issue_type': 'issue_type',
                            'fault': 'fault',
                            'severity': 'severity',
                            'source_site_uuid': 'source_site_uuid',
                            'destination_site_uuid': 'destination_site_uuid',
                            'direction': 'direction',
                            }

    def __init__(self,
                 target_object_name=None,
                 target_object_mo_id=None,
                 triggered_time=None,
                 issue_type=None,
                 fault=None,
                 severity=None,
                 source_site_uuid=None,
                 destination_site_uuid=None,
                 direction=None,
                ):
        """
        :type  target_object_name: :class:`str` or ``None``
        :param target_object_name: 
        :type  target_object_mo_id: :class:`str`
        :param target_object_mo_id: 
        :type  triggered_time: :class:`datetime.datetime`
        :param triggered_time: 
        :type  issue_type: :class:`str`
        :param issue_type: 
        :type  fault: :class:`Fault` or ``None``
        :param fault: 
        :type  severity: :class:`str`
        :param severity: 
        :type  source_site_uuid: :class:`str` or ``None``
        :param source_site_uuid: 
        :type  destination_site_uuid: :class:`str` or ``None``
        :param destination_site_uuid: 
        :type  direction: :class:`str` or ``None``
        :param direction: 
        """
        self.target_object_name = target_object_name
        self.target_object_mo_id = target_object_mo_id
        self.triggered_time = triggered_time
        self.issue_type = issue_type
        self.fault = fault
        self.severity = severity
        self.source_site_uuid = source_site_uuid
        self.destination_site_uuid = destination_site_uuid
        self.direction = direction
        VapiStruct.__init__(self)


HmsReplicationIssueInfo._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.hms_replication_issue_info', {
        'target_object_name': type.OptionalType(type.StringType()),
        'target_object_mo_id': type.StringType(),
        'triggered_time': type.DateTimeType(),
        'issue_type': type.StringType(),
        'fault': type.OptionalType(type.ReferenceType(__name__, 'Fault')),
        'severity': type.StringType(),
        'source_site_uuid': type.OptionalType(type.StringType()),
        'destination_site_uuid': type.OptionalType(type.StringType()),
        'direction': type.OptionalType(type.StringType()),
    },
    HmsReplicationIssueInfo,
    False,
    None))



class HmsSiteIssueInfo(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'target_object_name': 'target_object_name',
                            'target_object_mo_id': 'target_object_mo_id',
                            'triggered_time': 'triggered_time',
                            'issue_type': 'issue_type',
                            'fault': 'fault',
                            'severity': 'severity',
                            }

    def __init__(self,
                 target_object_name=None,
                 target_object_mo_id=None,
                 triggered_time=None,
                 issue_type=None,
                 fault=None,
                 severity=None,
                ):
        """
        :type  target_object_name: :class:`str` or ``None``
        :param target_object_name: 
        :type  target_object_mo_id: :class:`str`
        :param target_object_mo_id: 
        :type  triggered_time: :class:`datetime.datetime`
        :param triggered_time: 
        :type  issue_type: :class:`str`
        :param issue_type: 
        :type  fault: :class:`Fault` or ``None``
        :param fault: 
        :type  severity: :class:`str`
        :param severity: 
        """
        self.target_object_name = target_object_name
        self.target_object_mo_id = target_object_mo_id
        self.triggered_time = triggered_time
        self.issue_type = issue_type
        self.fault = fault
        self.severity = severity
        VapiStruct.__init__(self)


HmsSiteIssueInfo._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.hms_site_issue_info', {
        'target_object_name': type.OptionalType(type.StringType()),
        'target_object_mo_id': type.StringType(),
        'triggered_time': type.DateTimeType(),
        'issue_type': type.StringType(),
        'fault': type.OptionalType(type.ReferenceType(__name__, 'Fault')),
        'severity': type.StringType(),
    },
    HmsSiteIssueInfo,
    False,
    None))



class ProvisionSrmConfig(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'srm_extension_key_suffix': 'srm_extension_key_suffix',
                            }

    def __init__(self,
                 srm_extension_key_suffix=None,
                ):
        """
        :type  srm_extension_key_suffix: :class:`str` or ``None``
        :param srm_extension_key_suffix: Optional custom extension key suffix for SRM. If not specified,
            default extension key will be used.
        """
        self.srm_extension_key_suffix = srm_extension_key_suffix
        VapiStruct.__init__(self)


ProvisionSrmConfig._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.provision_srm_config', {
        'srm_extension_key_suffix': type.OptionalType(type.StringType()),
    },
    ProvisionSrmConfig,
    False,
    None))



class ReplicaData(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'datastore_entities': 'datastore_entities',
                            }

    def __init__(self,
                 datastore_entities=None,
                ):
        """
        :type  datastore_entities: :class:`list` of :class:`DatastoreEntity` or ``None``
        :param datastore_entities: DatastoreEntity
        """
        self.datastore_entities = datastore_entities
        VapiStruct.__init__(self)


ReplicaData._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.replica_data', {
        'datastore_entities': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'DatastoreEntity'))),
    },
    ReplicaData,
    False,
    None))



class ReplicaDisk(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'disk_id': 'disk_id',
                            'collection_id': 'collection_id',
                            'name': 'name',
                            'datastore_mo_id': 'datastore_mo_id',
                            'space_requirement': 'space_requirement',
                            'movable': 'movable',
                            'datastores_for_single_host_move': 'datastores_for_single_host_move',
                            }

    def __init__(self,
                 disk_id=None,
                 collection_id=None,
                 name=None,
                 datastore_mo_id=None,
                 space_requirement=None,
                 movable=None,
                 datastores_for_single_host_move=None,
                ):
        """
        :type  disk_id: :class:`str` or ``None``
        :param disk_id: 
        :type  collection_id: :class:`str` or ``None``
        :param collection_id: 
        :type  name: :class:`str` or ``None``
        :param name: 
        :type  datastore_mo_id: :class:`str` or ``None``
        :param datastore_mo_id: 
        :type  space_requirement: :class:`float` or ``None``
        :param space_requirement: 
        :type  movable: :class:`bool` or ``None``
        :param movable: 
        :type  datastores_for_single_host_move: :class:`list` of :class:`vmware.vapi.struct.VapiStruct` or ``None``
        :param datastores_for_single_host_move: 
        """
        self.disk_id = disk_id
        self.collection_id = collection_id
        self.name = name
        self.datastore_mo_id = datastore_mo_id
        self.space_requirement = space_requirement
        self.movable = movable
        self.datastores_for_single_host_move = datastores_for_single_host_move
        VapiStruct.__init__(self)


ReplicaDisk._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.replica_disk', {
        'disk_id': type.OptionalType(type.StringType()),
        'collection_id': type.OptionalType(type.StringType()),
        'name': type.OptionalType(type.StringType()),
        'datastore_mo_id': type.OptionalType(type.StringType()),
        'space_requirement': type.OptionalType(type.DoubleType()),
        'movable': type.OptionalType(type.BooleanType()),
        'datastores_for_single_host_move': type.OptionalType(type.ListType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct))),
    },
    ReplicaDisk,
    False,
    None))



class ReplicaDiskCollection(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'collection_id': 'collection_id',
                            'name': 'name',
                            'placeholder_vm_mo_id': 'placeholder_vm_mo_id',
                            'disks': 'disks',
                            'generated': 'generated',
                            }

    def __init__(self,
                 collection_id=None,
                 name=None,
                 placeholder_vm_mo_id=None,
                 disks=None,
                 generated=None,
                ):
        """
        :type  collection_id: :class:`str` or ``None``
        :param collection_id: 
        :type  name: :class:`str` or ``None``
        :param name: 
        :type  placeholder_vm_mo_id: :class:`str` or ``None``
        :param placeholder_vm_mo_id: 
        :type  disks: :class:`list` of :class:`ReplicaDisk` or ``None``
        :param disks: 
        :type  generated: :class:`datetime.datetime` or ``None``
        :param generated: 
        """
        self.collection_id = collection_id
        self.name = name
        self.placeholder_vm_mo_id = placeholder_vm_mo_id
        self.disks = disks
        self.generated = generated
        VapiStruct.__init__(self)


ReplicaDiskCollection._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.replica_disk_collection', {
        'collection_id': type.OptionalType(type.StringType()),
        'name': type.OptionalType(type.StringType()),
        'placeholder_vm_mo_id': type.OptionalType(type.StringType()),
        'disks': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'ReplicaDisk'))),
        'generated': type.OptionalType(type.DateTimeType()),
    },
    ReplicaDiskCollection,
    False,
    None))



class ReplicationData(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'replication_name': 'replication_name',
                            'replication_uuid': 'replication_uuid',
                            'hbr_server_uuid': 'hbr_server_uuid',
                            'hbr_server_name': 'hbr_server_name',
                            'scale_out': 'scale_out',
                            }

    def __init__(self,
                 replication_name=None,
                 replication_uuid=None,
                 hbr_server_uuid=None,
                 hbr_server_name=None,
                 scale_out=None,
                ):
        """
        :type  replication_name: :class:`str` or ``None``
        :param replication_name: 
        :type  replication_uuid: :class:`str` or ``None``
        :param replication_uuid: 
        :type  hbr_server_uuid: :class:`str` or ``None``
        :param hbr_server_uuid: 
        :type  hbr_server_name: :class:`str` or ``None``
        :param hbr_server_name: 
        :type  scale_out: :class:`bool` or ``None``
        :param scale_out: 
        """
        self.replication_name = replication_name
        self.replication_uuid = replication_uuid
        self.hbr_server_uuid = hbr_server_uuid
        self.hbr_server_name = hbr_server_name
        self.scale_out = scale_out
        VapiStruct.__init__(self)


ReplicationData._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.replication_data', {
        'replication_name': type.OptionalType(type.StringType()),
        'replication_uuid': type.OptionalType(type.StringType()),
        'hbr_server_uuid': type.OptionalType(type.StringType()),
        'hbr_server_name': type.OptionalType(type.StringType()),
        'scale_out': type.OptionalType(type.BooleanType()),
    },
    ReplicationData,
    False,
    None))



class ReportPeriodConfig(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'report_start_day_inclusive': 'report_start_day_inclusive',
                            'report_end_day_inclusive': 'report_end_day_inclusive',
                            }

    def __init__(self,
                 report_start_day_inclusive=None,
                 report_end_day_inclusive=None,
                ):
        """
        :type  report_start_day_inclusive: :class:`datetime.datetime` or ``None``
        :param report_start_day_inclusive: 
        :type  report_end_day_inclusive: :class:`datetime.datetime` or ``None``
        :param report_end_day_inclusive: 
        """
        self.report_start_day_inclusive = report_start_day_inclusive
        self.report_end_day_inclusive = report_end_day_inclusive
        VapiStruct.__init__(self)


ReportPeriodConfig._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.report_period_config', {
        'report_start_day_inclusive': type.OptionalType(type.DateTimeType()),
        'report_end_day_inclusive': type.OptionalType(type.DateTimeType()),
    },
    ReportPeriodConfig,
    False,
    None))



class SiteRecovery(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """
    SITE_RECOVERY_STATE_ACTIVATING = "ACTIVATING"
    """


    """
    SITE_RECOVERY_STATE_ACTIVATED = "ACTIVATED"
    """


    """
    SITE_RECOVERY_STATE_DEACTIVATING = "DEACTIVATING"
    """


    """
    SITE_RECOVERY_STATE_DEACTIVATED = "DEACTIVATED"
    """


    """
    SITE_RECOVERY_STATE_FAILED = "FAILED"
    """


    """
    SITE_RECOVERY_STATE_CANCELED = "CANCELED"
    """


    """
    SITE_RECOVERY_STATE_DELETED = "DELETED"
    """


    """



    _canonical_to_pep_names = {
                            'id': 'id',
                            'version': 'version',
                            'created': 'created',
                            'user_id': 'user_id',
                            'user_name': 'user_name',
                            'updated': 'updated',
                            'updated_by_user_id': 'updated_by_user_id',
                            'updated_by_user_name': 'updated_by_user_name',
                            'sddc_id': 'sddc_id',
                            'site_recovery_state': 'site_recovery_state',
                            'draas_h5_url': 'draas_h5_url',
                            'vr_node': 'vr_node',
                            'srm_nodes': 'srm_nodes',
                            'vrs_nodes': 'vrs_nodes',
                            }

    def __init__(self,
                 id=None,
                 version=None,
                 created=None,
                 user_id=None,
                 user_name=None,
                 updated=None,
                 updated_by_user_id=None,
                 updated_by_user_name=None,
                 sddc_id=None,
                 site_recovery_state=None,
                 draas_h5_url=None,
                 vr_node=None,
                 srm_nodes=None,
                 vrs_nodes=None,
                ):
        """
        :type  id: :class:`str`
        :param id: 
        :type  version: :class:`long`
        :param version: Version of this entity format: int32
        :type  created: :class:`datetime.datetime`
        :param created: 
        :type  user_id: :class:`str`
        :param user_id: User id that last updated this record
        :type  user_name: :class:`str`
        :param user_name: User name that last updated this record
        :type  updated: :class:`datetime.datetime`
        :param updated: 
        :type  updated_by_user_id: :class:`str`
        :param updated_by_user_id: User id that last updated this record
        :type  updated_by_user_name: :class:`str`
        :param updated_by_user_name: User name that last updated this record
        :type  sddc_id: :class:`str` or ``None``
        :param sddc_id: 
        :type  site_recovery_state: :class:`str` or ``None``
        :param site_recovery_state: Possible values are: 
            
            * :attr:`SiteRecovery.SITE_RECOVERY_STATE_ACTIVATING`
            * :attr:`SiteRecovery.SITE_RECOVERY_STATE_ACTIVATED`
            * :attr:`SiteRecovery.SITE_RECOVERY_STATE_DEACTIVATING`
            * :attr:`SiteRecovery.SITE_RECOVERY_STATE_DEACTIVATED`
            * :attr:`SiteRecovery.SITE_RECOVERY_STATE_FAILED`
            * :attr:`SiteRecovery.SITE_RECOVERY_STATE_CANCELED`
            * :attr:`SiteRecovery.SITE_RECOVERY_STATE_DELETED`
        :type  draas_h5_url: :class:`str` or ``None``
        :param draas_h5_url: 
        :type  vr_node: :class:`SiteRecoveryNode` or ``None``
        :param vr_node: 
        :type  srm_nodes: :class:`list` of :class:`SrmNode` or ``None``
        :param srm_nodes: 
        :type  vrs_nodes: :class:`list` of :class:`SiteRecoveryNode` or ``None``
        :param vrs_nodes: 
        """
        self.id = id
        self.version = version
        self.created = created
        self.user_id = user_id
        self.user_name = user_name
        self.updated = updated
        self.updated_by_user_id = updated_by_user_id
        self.updated_by_user_name = updated_by_user_name
        self.sddc_id = sddc_id
        self.site_recovery_state = site_recovery_state
        self.draas_h5_url = draas_h5_url
        self.vr_node = vr_node
        self.srm_nodes = srm_nodes
        self.vrs_nodes = vrs_nodes
        VapiStruct.__init__(self)


SiteRecovery._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.site_recovery', {
        'id': type.StringType(),
        'version': type.IntegerType(),
        'created': type.DateTimeType(),
        'user_id': type.StringType(),
        'user_name': type.StringType(),
        'updated': type.DateTimeType(),
        'updated_by_user_id': type.StringType(),
        'updated_by_user_name': type.StringType(),
        'sddc_id': type.OptionalType(type.StringType()),
        'site_recovery_state': type.OptionalType(type.StringType()),
        'draas_h5_url': type.OptionalType(type.StringType()),
        'vr_node': type.OptionalType(type.ReferenceType(__name__, 'SiteRecoveryNode')),
        'srm_nodes': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'SrmNode'))),
        'vrs_nodes': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'SiteRecoveryNode'))),
    },
    SiteRecovery,
    False,
    None))



class SiteRecoveryNode(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """
    TYPE_VRMS = "VRMS"
    """


    """
    TYPE_SRM = "SRM"
    """


    """
    TYPE_VRS = "VRS"
    """


    """
    STATE_DEPLOYING = "DEPLOYING"
    """


    """
    STATE_PROVISIONED = "PROVISIONED"
    """


    """
    STATE_READY = "READY"
    """


    """
    STATE_DELETING = "DELETING"
    """


    """
    STATE_FAILED = "FAILED"
    """


    """
    STATE_CANCELED = "CANCELED"
    """


    """



    _canonical_to_pep_names = {
                            'id': 'id',
                            'type': 'type',
                            'state': 'state',
                            'vm_moref_id': 'vm_moref_id',
                            'ip_address': 'ip_address',
                            'hostname': 'hostname',
                            }

    def __init__(self,
                 id=None,
                 type=None,
                 state=None,
                 vm_moref_id=None,
                 ip_address=None,
                 hostname=None,
                ):
        """
        :type  id: :class:`str` or ``None``
        :param id: 
        :type  type: :class:`str` or ``None``
        :param type: Possible values are: 
            
            * :attr:`SiteRecoveryNode.TYPE_VRMS`
            * :attr:`SiteRecoveryNode.TYPE_SRM`
            * :attr:`SiteRecoveryNode.TYPE_VRS`
        :type  state: :class:`str` or ``None``
        :param state: Possible values are: 
            
            * :attr:`SiteRecoveryNode.STATE_DEPLOYING`
            * :attr:`SiteRecoveryNode.STATE_PROVISIONED`
            * :attr:`SiteRecoveryNode.STATE_READY`
            * :attr:`SiteRecoveryNode.STATE_DELETING`
            * :attr:`SiteRecoveryNode.STATE_FAILED`
            * :attr:`SiteRecoveryNode.STATE_CANCELED`
        :type  vm_moref_id: :class:`str` or ``None``
        :param vm_moref_id: 
        :type  ip_address: :class:`str` or ``None``
        :param ip_address: 
        :type  hostname: :class:`str` or ``None``
        :param hostname: 
        """
        self.id = id
        self.type = type
        self.state = state
        self.vm_moref_id = vm_moref_id
        self.ip_address = ip_address
        self.hostname = hostname
        VapiStruct.__init__(self)


SiteRecoveryNode._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.site_recovery_node', {
        'id': type.OptionalType(type.StringType()),
        'type': type.OptionalType(type.StringType()),
        'state': type.OptionalType(type.StringType()),
        'vm_moref_id': type.OptionalType(type.StringType()),
        'ip_address': type.OptionalType(type.StringType()),
        'hostname': type.OptionalType(type.StringType()),
    },
    SiteRecoveryNode,
    False,
    None))



class SiteRecoveryNodeVersion(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """
    NODE_TYPE_VRMS = "VRMS"
    """


    """
    NODE_TYPE_SRM = "SRM"
    """


    """
    NODE_TYPE_VRS = "VRS"
    """


    """



    _canonical_to_pep_names = {
                            'node_id': 'node_id',
                            'node_type': 'node_type',
                            'node_ip': 'node_ip',
                            'build_version': 'build_version',
                            'full_version': 'full_version',
                            }

    def __init__(self,
                 node_id=None,
                 node_type=None,
                 node_ip=None,
                 build_version=None,
                 full_version=None,
                ):
        """
        :type  node_id: :class:`str` or ``None``
        :param node_id: 
        :type  node_type: :class:`str` or ``None``
        :param node_type: Possible values are: 
            
            * :attr:`SiteRecoveryNodeVersion.NODE_TYPE_VRMS`
            * :attr:`SiteRecoveryNodeVersion.NODE_TYPE_SRM`
            * :attr:`SiteRecoveryNodeVersion.NODE_TYPE_VRS`
        :type  node_ip: :class:`str` or ``None``
        :param node_ip: 
        :type  build_version: :class:`BuildVersion` or ``None``
        :param build_version: 
        :type  full_version: :class:`str` or ``None``
        :param full_version: 
        """
        self.node_id = node_id
        self.node_type = node_type
        self.node_ip = node_ip
        self.build_version = build_version
        self.full_version = full_version
        VapiStruct.__init__(self)


SiteRecoveryNodeVersion._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.site_recovery_node_version', {
        'node_id': type.OptionalType(type.StringType()),
        'node_type': type.OptionalType(type.StringType()),
        'node_ip': type.OptionalType(type.StringType()),
        'build_version': type.OptionalType(type.ReferenceType(__name__, 'BuildVersion')),
        'full_version': type.OptionalType(type.StringType()),
    },
    SiteRecoveryNodeVersion,
    False,
    None))



class SiteRecoveryVersions(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'sddc_id': 'sddc_id',
                            'node_versions': 'node_versions',
                            'generated': 'generated',
                            }

    def __init__(self,
                 sddc_id=None,
                 node_versions=None,
                 generated=None,
                ):
        """
        :type  sddc_id: :class:`str` or ``None``
        :param sddc_id: 
        :type  node_versions: :class:`list` of :class:`SiteRecoveryNodeVersion` or ``None``
        :param node_versions: list of site recovery node version
        :type  generated: :class:`datetime.datetime` or ``None``
        :param generated: 
        """
        self.sddc_id = sddc_id
        self.node_versions = node_versions
        self.generated = generated
        VapiStruct.__init__(self)


SiteRecoveryVersions._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.site_recovery_versions', {
        'sddc_id': type.OptionalType(type.StringType()),
        'node_versions': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'SiteRecoveryNodeVersion'))),
        'generated': type.OptionalType(type.DateTimeType()),
    },
    SiteRecoveryVersions,
    False,
    None))



class SrmNode(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """
    TYPE_VRMS = "VRMS"
    """


    """
    TYPE_SRM = "SRM"
    """


    """
    TYPE_VRS = "VRS"
    """


    """
    STATE_DEPLOYING = "DEPLOYING"
    """


    """
    STATE_PROVISIONED = "PROVISIONED"
    """


    """
    STATE_READY = "READY"
    """


    """
    STATE_DELETING = "DELETING"
    """


    """
    STATE_FAILED = "FAILED"
    """


    """
    STATE_CANCELED = "CANCELED"
    """


    """



    _canonical_to_pep_names = {
                            'id': 'id',
                            'type': 'type',
                            'state': 'state',
                            'vm_moref_id': 'vm_moref_id',
                            'ip_address': 'ip_address',
                            'hostname': 'hostname',
                            'srm_extension_key_suffix': 'srm_extension_key_suffix',
                            'srm_extension_key': 'srm_extension_key',
                            }

    def __init__(self,
                 id=None,
                 type=None,
                 state=None,
                 vm_moref_id=None,
                 ip_address=None,
                 hostname=None,
                 srm_extension_key_suffix=None,
                 srm_extension_key=None,
                ):
        """
        :type  id: :class:`str` or ``None``
        :param id: 
        :type  type: :class:`str` or ``None``
        :param type: Possible values are: 
            
            * :attr:`SrmNode.TYPE_VRMS`
            * :attr:`SrmNode.TYPE_SRM`
            * :attr:`SrmNode.TYPE_VRS`
        :type  state: :class:`str` or ``None``
        :param state: Possible values are: 
            
            * :attr:`SrmNode.STATE_DEPLOYING`
            * :attr:`SrmNode.STATE_PROVISIONED`
            * :attr:`SrmNode.STATE_READY`
            * :attr:`SrmNode.STATE_DELETING`
            * :attr:`SrmNode.STATE_FAILED`
            * :attr:`SrmNode.STATE_CANCELED`
        :type  vm_moref_id: :class:`str` or ``None``
        :param vm_moref_id: 
        :type  ip_address: :class:`str` or ``None``
        :param ip_address: 
        :type  hostname: :class:`str` or ``None``
        :param hostname: 
        :type  srm_extension_key_suffix: :class:`str` or ``None``
        :param srm_extension_key_suffix: 
        :type  srm_extension_key: :class:`str` or ``None``
        :param srm_extension_key: 
        """
        self.id = id
        self.type = type
        self.state = state
        self.vm_moref_id = vm_moref_id
        self.ip_address = ip_address
        self.hostname = hostname
        self.srm_extension_key_suffix = srm_extension_key_suffix
        self.srm_extension_key = srm_extension_key
        VapiStruct.__init__(self)


SrmNode._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.srm_node', {
        'id': type.OptionalType(type.StringType()),
        'type': type.OptionalType(type.StringType()),
        'state': type.OptionalType(type.StringType()),
        'vm_moref_id': type.OptionalType(type.StringType()),
        'ip_address': type.OptionalType(type.StringType()),
        'hostname': type.OptionalType(type.StringType()),
        'srm_extension_key_suffix': type.OptionalType(type.StringType()),
        'srm_extension_key': type.OptionalType(type.StringType()),
    },
    SrmNode,
    False,
    None))



class Task(VapiStruct):
    """


    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """
    STATUS_STARTED = "STARTED"
    """


    """
    STATUS_CANCELING = "CANCELING"
    """


    """
    STATUS_FINISHED = "FINISHED"
    """


    """
    STATUS_FAILED = "FAILED"
    """


    """
    STATUS_CANCELED = "CANCELED"
    """


    """



    _canonical_to_pep_names = {
                            'id': 'id',
                            'version': 'version',
                            'created': 'created',
                            'user_id': 'user_id',
                            'user_name': 'user_name',
                            'updated': 'updated',
                            'updated_by_user_id': 'updated_by_user_id',
                            'updated_by_user_name': 'updated_by_user_name',
                            'end_time': 'end_time',
                            'error_message': 'error_message',
                            'tenant_id': 'tenant_id',
                            'params': 'params',
                            'resource_id': 'resource_id',
                            'resource_type': 'resource_type',
                            'parent_task_id': 'parent_task_id',
                            'retries': 'retries',
                            'start_time': 'start_time',
                            'status': 'status',
                            'sub_status': 'sub_status',
                            'task_type': 'task_type',
                            'task_version': 'task_version',
                            'task_progress_phases': 'task_progress_phases',
                            'progress_percent': 'progress_percent',
                            'estimated_remaining_minutes': 'estimated_remaining_minutes',
                            }

    def __init__(self,
                 id=None,
                 version=None,
                 created=None,
                 user_id=None,
                 user_name=None,
                 updated=None,
                 updated_by_user_id=None,
                 updated_by_user_name=None,
                 end_time=None,
                 error_message=None,
                 tenant_id=None,
                 params=None,
                 resource_id=None,
                 resource_type=None,
                 parent_task_id=None,
                 retries=None,
                 start_time=None,
                 status=None,
                 sub_status=None,
                 task_type=None,
                 task_version=None,
                 task_progress_phases=None,
                 progress_percent=None,
                 estimated_remaining_minutes=None,
                ):
        """
        :type  id: :class:`str`
        :param id: 
        :type  version: :class:`long`
        :param version: Version of this entity format: int32
        :type  created: :class:`datetime.datetime`
        :param created: 
        :type  user_id: :class:`str`
        :param user_id: User id that last updated this record
        :type  user_name: :class:`str`
        :param user_name: User name that last updated this record
        :type  updated: :class:`datetime.datetime`
        :param updated: 
        :type  updated_by_user_id: :class:`str`
        :param updated_by_user_id: User id that last updated this record
        :type  updated_by_user_name: :class:`str`
        :param updated_by_user_name: User name that last updated this record
        :type  end_time: :class:`datetime.datetime` or ``None``
        :param end_time: 
        :type  error_message: :class:`str` or ``None``
        :param error_message: 
        :type  tenant_id: :class:`str` or ``None``
        :param tenant_id: 
        :type  params: :class:`vmware.vapi.struct.VapiStruct` or ``None``
        :param params: 
        :type  resource_id: :class:`str` or ``None``
        :param resource_id: UUID of resources task is acting upon
        :type  resource_type: :class:`str` or ``None``
        :param resource_type: Type of resource being acted upon
        :type  parent_task_id: :class:`str` or ``None``
        :param parent_task_id: 
        :type  retries: :class:`long` or ``None``
        :param retries: 
        :type  start_time: :class:`datetime.datetime` or ``None``
        :param start_time: 
        :type  status: :class:`str` or ``None``
        :param status: Possible values are: 
            
            * :attr:`Task.STATUS_STARTED`
            * :attr:`Task.STATUS_CANCELING`
            * :attr:`Task.STATUS_FINISHED`
            * :attr:`Task.STATUS_FAILED`
            * :attr:`Task.STATUS_CANCELED`
        :type  sub_status: :class:`str` or ``None``
        :param sub_status: 
        :type  task_type: :class:`str` or ``None``
        :param task_type: 
        :type  task_version: :class:`str` or ``None``
        :param task_version: 
        :type  task_progress_phases: :class:`list` of :class:`TaskProgressPhase` or ``None``
        :param task_progress_phases: Task progress phases involved in current task execution
        :type  progress_percent: :class:`long` or ``None``
        :param progress_percent: Estimated progress percentage the task executed format: int32
        :type  estimated_remaining_minutes: :class:`long` or ``None``
        :param estimated_remaining_minutes: Estimated remaining time in minute of the task execution, < 0 means
            no estimation for the task. format: int32
        """
        self.id = id
        self.version = version
        self.created = created
        self.user_id = user_id
        self.user_name = user_name
        self.updated = updated
        self.updated_by_user_id = updated_by_user_id
        self.updated_by_user_name = updated_by_user_name
        self.end_time = end_time
        self.error_message = error_message
        self.tenant_id = tenant_id
        self.params = params
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.parent_task_id = parent_task_id
        self.retries = retries
        self.start_time = start_time
        self.status = status
        self.sub_status = sub_status
        self.task_type = task_type
        self.task_version = task_version
        self.task_progress_phases = task_progress_phases
        self.progress_percent = progress_percent
        self.estimated_remaining_minutes = estimated_remaining_minutes
        VapiStruct.__init__(self)


Task._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.task', {
        'id': type.StringType(),
        'version': type.IntegerType(),
        'created': type.DateTimeType(),
        'user_id': type.StringType(),
        'user_name': type.StringType(),
        'updated': type.DateTimeType(),
        'updated_by_user_id': type.StringType(),
        'updated_by_user_name': type.StringType(),
        'end_time': type.OptionalType(type.DateTimeType()),
        'error_message': type.OptionalType(type.StringType()),
        'tenant_id': type.OptionalType(type.StringType()),
        'params': type.OptionalType(type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct)),
        'resource_id': type.OptionalType(type.StringType()),
        'resource_type': type.OptionalType(type.StringType()),
        'parent_task_id': type.OptionalType(type.StringType()),
        'retries': type.OptionalType(type.IntegerType()),
        'start_time': type.OptionalType(type.DateTimeType()),
        'status': type.OptionalType(type.StringType()),
        'sub_status': type.OptionalType(type.StringType()),
        'task_type': type.OptionalType(type.StringType()),
        'task_version': type.OptionalType(type.StringType()),
        'task_progress_phases': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'TaskProgressPhase'))),
        'progress_percent': type.OptionalType(type.IntegerType()),
        'estimated_remaining_minutes': type.OptionalType(type.IntegerType()),
    },
    Task,
    False,
    None))



class TaskProgressPhase(VapiStruct):
    """
    A task progress can be (but does NOT have to be) divided to more meaningful
    progress phases.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'id': 'id',
                            'name': 'name',
                            'progress_percent': 'progress_percent',
                            }

    def __init__(self,
                 id=None,
                 name=None,
                 progress_percent=None,
                ):
        """
        :type  id: :class:`str`
        :param id: The identifier of the task progress phase
        :type  name: :class:`str`
        :param name: The display name of the task progress phase
        :type  progress_percent: :class:`long`
        :param progress_percent: The percentage of the phase that has completed format: int32
        """
        self.id = id
        self.name = name
        self.progress_percent = progress_percent
        VapiStruct.__init__(self)


TaskProgressPhase._set_binding_type(type.StructType(
    'com.vmware.vmc.draas.model.task_progress_phase', {
        'id': type.StringType(),
        'name': type.StringType(),
        'progress_percent': type.IntegerType(),
    },
    TaskProgressPhase,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

