# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright 2023 VMware, Inc.  All rights reserved.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vmc.draas.
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


class EnableVrScaleOut(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.enable_vr_scale_out'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _EnableVrScaleOutStub)
        self._VAPI_OPERATION_IDS = {}


    def post(self,
             org,
             sddc,
             ):
        """
        Enable VR scale out for Activated with DR SDDC

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :rtype: :class:`com.vmware.vmc.draas.model_client.Task`
        :return: com.vmware.vmc.draas.model.Task
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidRequest` 
            Bad Request
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        """
        return self._invoke('post',
                            {
                            'org': org,
                            'sddc': sddc,
                            })
class GenerateOauthClient(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.generate_oauth_client'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _GenerateOauthClientStub)
        self._VAPI_OPERATION_IDS = {}


    def post(self,
             org,
             sddc,
             site_recovery_node,
             ):
        """
        Generate Oauth Client for Site Recovery node

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :type  site_recovery_node: :class:`str`
        :param site_recovery_node: Site recovery node identifier (required)
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidRequest` 
            Bad Request
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        """
        return self._invoke('post',
                            {
                            'org': org,
                            'sddc': sddc,
                            'site_recovery_node': site_recovery_node,
                            })
class GetSrmConfigExport(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.get_srm_config_export'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _GetSrmConfigExportStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            org,
            sddc,
            srm_node,
            ):
        """
        Get content of the config export file needed for CVDS migration.

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :type  srm_node: :class:`str`
        :param srm_node: SRM node identifier (required)
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Cannot find config-export file in the site recovery node target
            path
        """
        return self._invoke('get',
                            {
                            'org': org,
                            'sddc': sddc,
                            'srm_node': srm_node,
                            })
class GranularReporter(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.granular_reporter'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _GranularReporterStub)
        self._VAPI_OPERATION_IDS = {}


    def create_usage_report(self,
                            org,
                            report_period_config=None,
                            ):
        """
        Create granular usage report for specific time period

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  report_period_config: :class:`com.vmware.vmc.draas.model_client.ReportPeriodConfig` or ``None``
        :param report_period_config: Report period configurations (optional)
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidRequest` 
            Bad Request
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        """
        return self._invoke('create_usage_report',
                            {
                            'org': org,
                            'report_period_config': report_period_config,
                            })
class ReplicaData(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.replica_data'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ReplicaDataStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            org,
            sddc,
            ):
        """
        Get VSR replica data per host

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :rtype: :class:`vmware.vapi.struct.VapiStruct`
        :return: DynamicStructure
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Not found
        """
        return self._invoke('get',
                            {
                            'org': org,
                            'sddc': sddc,
                            })
class ReplicaDiskCollections(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.replica_disk_collections'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ReplicaDiskCollectionsStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            org,
            sddc,
            datastore_mo_id=None,
            ):
        """
        Query replica disk collections

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :type  datastore_mo_id: :class:`str` or ``None``
        :param datastore_mo_id: Represents the datastore moref id to search. (optional)
        :rtype: :class:`list` of :class:`com.vmware.vmc.draas.model_client.ReplicaDiskCollection`
        :return: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Not found
        """
        return self._invoke('get',
                            {
                            'org': org,
                            'sddc': sddc,
                            'datastore_mo_id': datastore_mo_id,
                            })
class ReplicationsData(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.replications_data'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ReplicationsDataStub)
        self._VAPI_OPERATION_IDS = {}


    def post(self,
             org,
             sddc,
             ):
        """
        Get outgoing and incoming replications data.

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :rtype: :class:`list` of :class:`com.vmware.vmc.draas.model_client.ReplicationData`
        :return: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidRequest` 
            Bad Request
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        """
        return self._invoke('post',
                            {
                            'org': org,
                            'sddc': sddc,
                            })
class SiteRecovery(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.site_recovery'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SiteRecoveryStub)
        self._VAPI_OPERATION_IDS = {}


    def delete(self,
               org,
               sddc,
               delete_config_internal=None,
               ):
        """
        Deactivate site recovery for the specified sddc

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :type  delete_config_internal: :class:`com.vmware.vmc.draas.model_client.DeleteConfigInternal` or ``None``
        :param delete_config_internal: Customization, for example if deactivate site recovery forcefully
            and the CSSD/CSCM ticket number and the confirmation code.
            (optional)
        :rtype: :class:`com.vmware.vmc.draas.model_client.Task`
        :return: com.vmware.vmc.draas.model.Task
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidRequest` 
            Invalid action or bad argument
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Cannot find site recovery configuration for sddc identifier
        """
        return self._invoke('delete',
                            {
                            'org': org,
                            'sddc': sddc,
                            'delete_config_internal': delete_config_internal,
                            })

    def get(self,
            org,
            sddc,
            ):
        """
        Query site recovery configuration for the specified sddc

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :rtype: :class:`com.vmware.vmc.draas.model_client.SiteRecovery`
        :return: com.vmware.vmc.draas.model.SiteRecovery
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidRequest` 
            Invalid action or bad argument
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        """
        return self._invoke('get',
                            {
                            'org': org,
                            'sddc': sddc,
                            })

    def post(self,
             org,
             sddc,
             activate_site_recovery_config=None,
             ):
        """
        Activate site recovery for the specified sddc

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :type  activate_site_recovery_config: :class:`com.vmware.vmc.draas.model_client.ActivateSiteRecoveryConfig` or ``None``
        :param activate_site_recovery_config: Customization, for example can specify custom extension key suffix
            for SRM. (optional)
        :rtype: :class:`com.vmware.vmc.draas.model_client.Task`
        :return: com.vmware.vmc.draas.model.Task
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidRequest` 
            Invalid action or bad argument
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Cannot find site recovery configuration for sddc identifier
        """
        return self._invoke('post',
                            {
                            'org': org,
                            'sddc': sddc,
                            'activate_site_recovery_config': activate_site_recovery_config,
                            })
class SiteRecoverySrmNodes(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.site_recovery_srm_nodes'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SiteRecoverySrmNodesStub)
        self._VAPI_OPERATION_IDS = {}


    def delete(self,
               org,
               sddc,
               srm_node,
               ):
        """
        Delete a SRM server.

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :type  srm_node: :class:`str`
        :param srm_node: SRM node identifier (required)
        :rtype: :class:`com.vmware.vmc.draas.model_client.Task`
        :return: com.vmware.vmc.draas.model.Task
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidRequest` 
            Invalid action or bad argument
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Cannot find SDDC or SRM node
        """
        return self._invoke('delete',
                            {
                            'org': org,
                            'sddc': sddc,
                            'srm_node': srm_node,
                            })

    def post(self,
             org,
             sddc,
             provision_srm_config=None,
             ):
        """
        Provision an additional SRM server.

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :type  provision_srm_config: :class:`com.vmware.vmc.draas.model_client.ProvisionSrmConfig` or ``None``
        :param provision_srm_config: Customization, for example can specify custom extension key suffix
            for SRM. (optional)
        :rtype: :class:`com.vmware.vmc.draas.model_client.Task`
        :return: com.vmware.vmc.draas.model.Task
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidRequest` 
            Invalid action or bad argument
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Cannot find site recovery configuration for sddc identifier
        """
        return self._invoke('post',
                            {
                            'org': org,
                            'sddc': sddc,
                            'provision_srm_config': provision_srm_config,
                            })
class SiteRecoveryVersions(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.site_recovery_versions'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _SiteRecoveryVersionsStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            org,
            sddc,
            ):
        """
        Query site recovery versions for the specified sddc

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :rtype: :class:`com.vmware.vmc.draas.model_client.SiteRecoveryVersions`
        :return: com.vmware.vmc.draas.model.SiteRecoveryVersions
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidRequest` 
            Invalid action or bad argument
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Cannot find site recovery versions for sddc identifier
        """
        return self._invoke('get',
                            {
                            'org': org,
                            'sddc': sddc,
                            })
class Task(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.task'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _TaskStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            org,
            task,
            ):
        """
        Retrieve details of a task.

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  task: :class:`str`
        :param task: task identifier (required)
        :rtype: :class:`com.vmware.vmc.draas.model_client.Task`
        :return: com.vmware.vmc.draas.model.Task
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Cannot find the task with given identifier
        """
        return self._invoke('get',
                            {
                            'org': org,
                            'task': task,
                            })

    def list(self,
             org,
             filter=None,
             ):
        """
        List all tasks with optional filtering.

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  filter: :class:`str` or ``None``
        :param filter: Filter expression Binary Operators: 'eq', 'ne', 'lt', 'gt', 'le',
            'ge', 'mul', 'div', 'mod', 'sub', 'add' Unary Operators: 'not', '-'
            (minus) String Operators: 'startswith', 'endswith', 'length',
            'contains', 'tolower', 'toupper', Nested attributes are composed
            using '.' Dates must be formatted as yyyy-MM-dd or
            yyyy-MM-ddTHH:mm:ss[.SSS]Z Strings should enclosed in single
            quotes, escape single quote with two single quotes The special
            literal 'created' will be mapped to the time the resource was first
            created. Examples: - $filter=(updated gt 2016-08-09T13:00:00Z) and
            (org_id eq 278710ff4e-6b6d-4d4e-aefb-ca637f38609e) -
            $filter=(created eq 2016-08-09) - $filter=(created gt 2016-08-09)
            and (sddc.status eq 'READY') (optional)
        :rtype: :class:`list` of :class:`com.vmware.vmc.draas.model_client.Task`
        :return: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        """
        return self._invoke('list',
                            {
                            'org': org,
                            'filter': filter,
                            })

    def update(self,
               org,
               task,
               action=None,
               ):
        """
        Request that a running task be canceled. This is advisory only, some
        tasks may not be cancelable, and some tasks might take an arbitrary
        amount of time to respond to a cancelation request. The task must be
        monitored to determine subsequent status.

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  task: :class:`str`
        :param task: task identifier (required)
        :type  action: :class:`str` or ``None``
        :param action: If = 'cancel', task will be canceled (optional)
        :rtype: :class:`com.vmware.vmc.draas.model_client.Task`
        :return: com.vmware.vmc.draas.model.Task
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidRequest` 
            Invalid action or bad argument
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Cannot find the task with given identifier
        """
        return self._invoke('update',
                            {
                            'org': org,
                            'task': task,
                            'action': action,
                            })
class VrReplicationIssues(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.vr_replication_issues'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _VrReplicationIssuesStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            org,
            sddc,
            ):
        """
        Query VR replication issues

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :rtype: :class:`list` of :class:`com.vmware.vmc.draas.model_client.HmsReplicationIssueInfo`
        :return: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Not found
        """
        return self._invoke('get',
                            {
                            'org': org,
                            'sddc': sddc,
                            })
class VrSiteIssues(VapiInterface):
    """
    
    """

    _VAPI_SERVICE_ID = 'com.vmware.vmc.draas.vr_site_issues'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _VrSiteIssuesStub)
        self._VAPI_OPERATION_IDS = {}


    def get(self,
            org,
            sddc,
            ):
        """
        Query VR site issues

        :type  org: :class:`str`
        :param org: Organization identifier (required)
        :type  sddc: :class:`str`
        :param sddc: sddc identifier (required)
        :rtype: :class:`list` of :class:`com.vmware.vmc.draas.model_client.HmsSiteIssueInfo`
        :return: 
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            Unauthorized
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            Forbidden
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            Not found
        """
        return self._invoke('get',
                            {
                            'org': org,
                            'sddc': sddc,
                            })
class _EnableVrScaleOutStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for post operation
        post_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
        })
        post_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_request':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidRequest'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        post_input_value_validator_list = [
        ]
        post_output_validator_list = [
        ]
        post_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery/vr-scale-out',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
            },
             header_parameters={
                 },
            query_parameters={
            },
            content_type='application/json'
        )

        operations = {
            'post': {
                'input_type': post_input_type,
                'output_type': type.ReferenceType('com.vmware.vmc.draas.model_client', 'Task'),
                'errors': post_error_dict,
                'input_value_validator_list': post_input_value_validator_list,
                'output_validator_list': post_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'post': post_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vmc.draas.enable_vr_scale_out',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _GenerateOauthClientStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for post operation
        post_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
            'site_recovery_node': type.StringType(),
        })
        post_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_request':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidRequest'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        post_input_value_validator_list = [
        ]
        post_output_validator_list = [
        ]
        post_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery/{siteRecoveryNode}/generate-oauth-client',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
                'site_recovery_node': 'siteRecoveryNode',
            },
             header_parameters={
                   },
            query_parameters={
            },
            content_type='application/json'
        )

        operations = {
            'post': {
                'input_type': post_input_type,
                'output_type': type.VoidType(),
                'errors': post_error_dict,
                'input_value_validator_list': post_input_value_validator_list,
                'output_validator_list': post_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'post': post_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vmc.draas.generate_oauth_client',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _GetSrmConfigExportStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
            'srm_node': type.StringType(),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery/srm-nodes/{srmNode}/config/export',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
                'srm_node': 'srmNode',
            },
             header_parameters={
                   },
            query_parameters={
            },
            content_type='application/json'
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.VoidType(),
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
            self, iface_name='com.vmware.vmc.draas.get_srm_config_export',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _GranularReporterStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create_usage_report operation
        create_usage_report_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'report_period_config': type.OptionalType(type.ReferenceType('com.vmware.vmc.draas.model_client', 'ReportPeriodConfig')),
        })
        create_usage_report_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_request':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidRequest'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        create_usage_report_input_value_validator_list = [
        ]
        create_usage_report_output_validator_list = [
        ]
        create_usage_report_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vmc/draas/api/orgs/{org}/report/usage',
            request_body_parameter='report_period_config',
            path_variables={
                'org': 'org',
            },
             header_parameters={
                 },
            query_parameters={
            },
            content_type='application/json'
        )

        operations = {
            'create_usage_report': {
                'input_type': create_usage_report_input_type,
                'output_type': type.VoidType(),
                'errors': create_usage_report_error_dict,
                'input_value_validator_list': create_usage_report_input_value_validator_list,
                'output_validator_list': create_usage_report_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'create_usage_report': create_usage_report_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vmc.draas.granular_reporter',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _ReplicaDataStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery/replica-data',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
            },
             header_parameters={
                 },
            query_parameters={
            },
            content_type='application/json'
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.DynamicStructType('vmware.vapi.dynamic_struct', {}, VapiStruct),
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
            self, iface_name='com.vmware.vmc.draas.replica_data',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _ReplicaDiskCollectionsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
            'datastore_mo_id': type.OptionalType(type.StringType()),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery/replica-disk-collections',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
            },
             header_parameters={
                   },
            query_parameters={
                'datastore_mo_id': 'datastore_mo_id',
            },
            content_type='application/json'
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ListType(type.ReferenceType('com.vmware.vmc.draas.model_client', 'ReplicaDiskCollection')),
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
            self, iface_name='com.vmware.vmc.draas.replica_disk_collections',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _ReplicationsDataStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for post operation
        post_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
        })
        post_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_request':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidRequest'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        post_input_value_validator_list = [
        ]
        post_output_validator_list = [
        ]
        post_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery/replications-data',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
            },
             header_parameters={
                 },
            query_parameters={
            },
            content_type='application/json'
        )

        operations = {
            'post': {
                'input_type': post_input_type,
                'output_type': type.ListType(type.ReferenceType('com.vmware.vmc.draas.model_client', 'ReplicationData')),
                'errors': post_error_dict,
                'input_value_validator_list': post_input_value_validator_list,
                'output_validator_list': post_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'post': post_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vmc.draas.replications_data',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _SiteRecoveryStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
            'delete_config_internal': type.OptionalType(type.ReferenceType('com.vmware.vmc.draas.model_client', 'DeleteConfigInternal')),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_request':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidRequest'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery',
            request_body_parameter='delete_config_internal',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
            },
             header_parameters={
                   },
            query_parameters={
            },
            content_type='application/json'
        )

        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_request':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidRequest'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
            },
             header_parameters={
                 },
            query_parameters={
            },
            content_type='application/json'
        )

        # properties for post operation
        post_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
            'activate_site_recovery_config': type.OptionalType(type.ReferenceType('com.vmware.vmc.draas.model_client', 'ActivateSiteRecoveryConfig')),
        })
        post_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_request':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidRequest'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        post_input_value_validator_list = [
        ]
        post_output_validator_list = [
        ]
        post_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery',
            request_body_parameter='activate_site_recovery_config',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
            },
             header_parameters={
                   },
            query_parameters={
            },
            content_type='application/json'
        )

        operations = {
            'delete': {
                'input_type': delete_input_type,
                'output_type': type.ReferenceType('com.vmware.vmc.draas.model_client', 'Task'),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': delete_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType('com.vmware.vmc.draas.model_client', 'SiteRecovery'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'post': {
                'input_type': post_input_type,
                'output_type': type.ReferenceType('com.vmware.vmc.draas.model_client', 'Task'),
                'errors': post_error_dict,
                'input_value_validator_list': post_input_value_validator_list,
                'output_validator_list': post_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'delete': delete_rest_metadata,
            'get': get_rest_metadata,
            'post': post_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vmc.draas.site_recovery',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _SiteRecoverySrmNodesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
            'srm_node': type.StringType(),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_request':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidRequest'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery/srm-nodes/{srmNode}',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
                'srm_node': 'srmNode',
            },
             header_parameters={
                   },
            query_parameters={
            },
            content_type='application/json'
        )

        # properties for post operation
        post_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
            'provision_srm_config': type.OptionalType(type.ReferenceType('com.vmware.vmc.draas.model_client', 'ProvisionSrmConfig')),
        })
        post_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_request':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidRequest'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        post_input_value_validator_list = [
        ]
        post_output_validator_list = [
        ]
        post_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery/srm-nodes',
            request_body_parameter='provision_srm_config',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
            },
             header_parameters={
                   },
            query_parameters={
            },
            content_type='application/json'
        )

        operations = {
            'delete': {
                'input_type': delete_input_type,
                'output_type': type.ReferenceType('com.vmware.vmc.draas.model_client', 'Task'),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': delete_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'post': {
                'input_type': post_input_type,
                'output_type': type.ReferenceType('com.vmware.vmc.draas.model_client', 'Task'),
                'errors': post_error_dict,
                'input_value_validator_list': post_input_value_validator_list,
                'output_validator_list': post_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'delete': delete_rest_metadata,
            'post': post_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vmc.draas.site_recovery_srm_nodes',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _SiteRecoveryVersionsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_request':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidRequest'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery/versions',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
            },
             header_parameters={
                 },
            query_parameters={
            },
            content_type='application/json'
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType('com.vmware.vmc.draas.model_client', 'SiteRecoveryVersions'),
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
            self, iface_name='com.vmware.vmc.draas.site_recovery_versions',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _TaskStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'task': type.StringType(),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vmc/draas/api/orgs/{org}/tasks/{task}',
            path_variables={
                'org': 'org',
                'task': 'task',
            },
             header_parameters={
                 },
            query_parameters={
            },
            content_type='application/json'
        )

        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'filter': type.OptionalType(type.StringType()),
        })
        list_error_dict = {
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
            url_template='/vmc/draas/api/orgs/{org}/tasks',
            path_variables={
                'org': 'org',
            },
             header_parameters={
                 },
            query_parameters={
                'filter': '$filter',
            },
            content_type='application/json'
        )

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'task': type.StringType(),
            'action': type.OptionalType(type.StringType()),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.invalid_request':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidRequest'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vmc/draas/api/orgs/{org}/tasks/{task}',
            path_variables={
                'org': 'org',
                'task': 'task',
            },
             header_parameters={
                   },
            query_parameters={
                'action': 'action',
            },
            content_type='application/json'
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType('com.vmware.vmc.draas.model_client', 'Task'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType('com.vmware.vmc.draas.model_client', 'Task')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'update': {
                'input_type': update_input_type,
                'output_type': type.ReferenceType('com.vmware.vmc.draas.model_client', 'Task'),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': update_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'list': list_rest_metadata,
            'update': update_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vmc.draas.task',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _VrReplicationIssuesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery/vr-replication-issues',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
            },
             header_parameters={
                 },
            query_parameters={
            },
            content_type='application/json'
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ListType(type.ReferenceType('com.vmware.vmc.draas.model_client', 'HmsReplicationIssueInfo')),
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
            self, iface_name='com.vmware.vmc.draas.vr_replication_issues',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)

class _VrSiteIssuesStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'org': type.StringType(),
            'sddc': type.StringType(),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vmc/draas/api/orgs/{org}/sddcs/{sddc}/site-recovery/vr-site-issues',
            path_variables={
                'org': 'org',
                'sddc': 'sddc',
            },
             header_parameters={
                 },
            query_parameters={
            },
            content_type='application/json'
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ListType(type.ReferenceType('com.vmware.vmc.draas.model_client', 'HmsSiteIssueInfo')),
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
            self, iface_name='com.vmware.vmc.draas.vr_site_issues',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=False)


class StubFactory(StubFactoryBase):
    _attrs = {
        'EnableVrScaleOut': EnableVrScaleOut,
        'GenerateOauthClient': GenerateOauthClient,
        'GetSrmConfigExport': GetSrmConfigExport,
        'GranularReporter': GranularReporter,
        'ReplicaData': ReplicaData,
        'ReplicaDiskCollections': ReplicaDiskCollections,
        'ReplicationsData': ReplicationsData,
        'SiteRecovery': SiteRecovery,
        'SiteRecoverySrmNodes': SiteRecoverySrmNodes,
        'SiteRecoveryVersions': SiteRecoveryVersions,
        'Task': Task,
        'VrReplicationIssues': VrReplicationIssues,
        'VrSiteIssues': VrSiteIssues,
        'model': 'com.vmware.vmc.draas.model_client.StubFactory',
    }

