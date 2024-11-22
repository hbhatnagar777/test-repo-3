# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that act as wrapper for testcase and SDK

classes defined:

    KubernetesHelper    -- Kubernetes Helper class

        Methods:

            source_vm_object_creation()     - Initialise Kuberenetes VM objects

            load_kubeconfig_file()          - Load the kubeconfig file for the cluster

            get_api_server_endpoint()       - Get the API server endpoint of the cluster

            backup()                        - Kubernetes backup

            restore_out_of_place()          - Kubernetes out of place restore

            restore_in_place()              - Kubernetes inplace restore

            move_pod_content()              - Move pod content in pod for validation

            validate_data()                 - Validate resources between source and destination lists

            validate_data_with_timestamp()  - Validate resources along with their creation timestamps to verify inplace
                                              restore with overwrite

            add_block_data()                - Add data to block device

            validate_block_data()           - Validate block data

            validate_restored_manifest()    - validate restored manifest data

            k8s_verify_restore_files()      - compare md5 hash values of files in original pod and restored pod

            create_cv_clusterrolebinding()  - create cluster role binding for service account

            create_cv_namespace()           - create namespace with specified name

            create_cv_pod()                 - create test pod

            create_cv_pvc()                 - create test pvc for pod

            create_cv_serviceaccount()      - create a serviceaccount with the specied name

            create_cv_secret()              - create a secret with the specified name

            create_cv_configmap()           - create a configmap with the specified name

            create_cv_svc()                 - create a service with the specified name

            create_random_cv_pod_data()     - generate random data for test pod

            delete_cv_clusterrolebinding()  - delete cluster role binding specified name

            delete_cv_namespace()           - delete namespace with specified name

            delete_cv_serviceaccount()      - delete serviceaccount with specified name

            get_serviceaccount_token()      - get token value from secret of service account

            move_cv_pod_data()              - move content of pod

            create_cv_deployment()          - Deployment creation function.

            get_all_resources()             - LIst of all k8s resources in namespace

            get_namespace_pods()            - List of pods in namespace

            get_namespace_pvcs()            - List of pvcs in namespace

            create_pod_dir()                - Create directory in pod

            get_files_checksum()            - Get checksum of files in folder

            run_restore_validate()          - Run restore with optional validation

            verify_checksum_dictionary()    - Compare dictionary of checksum

            get_namespace_custom_resources()- Get namespaced custom resources

            get_namespace_volume_snapshots()- Get namespaced volumesnapshots

            validate_cv_resource_cleanup()  - Validate CV resource cleanup after backup/restore

            get_default_storage_class_from_cluster() - get the default storage class from cluster

            deploy_helm_apps()              - to deploy helm apps

            compare_with_helm_list()        - checks if helm apps present in a namespace are also present in the output
                                              of helm list -A command

            cleanup_helm_apps()             - To cleanup Helm apps

            list_pod_content()              - list the elements of pod in folder.

            get_pod_file_content()          - Gets the contents of a file inside a pod

            set_namespaced_quota()          - Set Quota on namespace

            manifest_restore()              - Restore manifest files to proxy

            restore_to_pvc()                - Restore files and folders to PVC

            fs_dest_restore()               - Restore files and folders to fs destination on proxy

            create_random_hlinks()          - generate random hardlink files in test pod

            create_random_slinks()          - generate random symbolic link files in test pod

            execute_command_in_pod()        - execute a command inside the pod

            create_cv_custom_resource()     - create a custom resource object

            namespace_level_restore()       - perform a namespace level restore in-place or out-of-place

            worker_pod_debug_wait()         - create debug wait files in access nodes

            get_child_job_error_reason()    - get error reason for child jobs from parent job

            validate_child_job_jpr()        - validate the JPR of child jobs with expected JPR dictionary

            match_logs_for_pattern()        - search for logs with specific pattern and validate if keywords exist

            create_cv_custom_resource()     - create a custom resource object

            namespace_level_restore()       - perform a namespace level restore in-place or out-of-place

            worker_pod_debug_wait()         - create debug wait files in access nodes

            get_child_job_error_reason()    - get error reason for child jobs from parent job

            validate_child_job_jpr()        - validate the JPR of child jobs with expected JPR dictionary

            match_logs_for_pattern()        - search for logs with specific pattern and validate if keywords exist

            create_cv_cluster_role()        - creates a cluster role

            create_cv_custom_resource()     - creates a custom resource from JSON

            create_cv_hpa()                 - creates a HPA

            create_cv_network_policy()      - creates a Network policy

            create_cv_role()                - creates a role

            create_cv_role_binding()         - creates a role binding

            delete_cv_crd()                  - Deletes a custom resource definition

            delete_cv_custom_resource()      - Deletes a custom resource

            delete_cv_resource_generic()     - Deletes a cv resource

            wait_till_resources_are_running()- Verifies if all pods are in running state

            verify_node_selector()           - Verifies if resources are assigned desired node selector during restore

"""

import os
import time
from abc import ABCMeta
from base64 import b64decode
from kubernetes.client import CoreV1Api, AppsV1Api, StorageV1Api, CustomObjectsApi, ApiException, NetworkingV1Api, \
    PolicyV1Api, AutoscalingV1Api, ApiextensionsV1Api
from kubernetes.client import ApiException as K8sApiException
from kubernetes.client.api.rbac_authorization_v1_api import RbacAuthorizationV1Api
from kubernetes.config import load_kube_config
from kubernetes.stream import stream as exec_stream

from AutomationUtils import logger
from AutomationUtils.commonutils import get_random_string
from AutomationUtils.config import get_config
from AutomationUtils.database_helper import get_csdb
from AutomationUtils.machine import Machine
from Install.installer_constants import BaselineStatus
from Kubernetes.HelmHelper import HelmHelper
from Kubernetes.constants import DebugFiles, AutomationLabels, VolumeSnapshotClasses, LogLineRepo
from Kubernetes.decorators import DebugSkip
from Kubernetes.exceptions import KubernetesException
from VirtualServer.VSAUtils import OptionsHelper
from Kubernetes import KubernetesUtils
from VirtualServer.VSAUtils.VirtualServerHelper import (
    AutoVSACommcell,
    AutoVSAVSClient,
    AutoVSAVSInstance,
    AutoVSABackupset
)
from VirtualServer.VSAUtils.VirtualServerHelper.AutoK8sSubclient import AutoK8sSubclient

_KUBERNETES_CONFIG = get_config().Kubernetes
_METALLIC_CONFIG = get_config().Metallic


class KubernetesHelper(object):
    __metaclass__ = ABCMeta
    """
    class that act as wrapper for SDK and Testcass
    """

    def __init__(self, testcase=None):
        """
        Initialize common variables for Kubernetes

        """
        self.testcase = testcase
        self.log = logger.get_log()
        self._csdb = None
        self._VMs = {}
        self._core_v1_api = None
        self._apps_v1_api = None
        self._rbac_auth_v1_api = None
        self._storage_v1_api = None
        self._custom_objects_api = None
        self._networking_v1_api = None
        self._policy_v1_api = None
        self._autoscaling_v2_api = None
        self._autoscaling_v1_api = None
        self._api_extensions_v1_api = None

        # for source_vm_object_creation
        self.commcell = None
        self.client = None
        self.instance = None
        self.backupset = None
        self.subclient = None
        self.auto_commcell = None
        self.auto_client = None
        self.auto_instance = None
        self.auto_backupset = None
        self.auto_subclient = None
        self.delete_dict = None

        # Update Proxies if required

        if _KUBERNETES_CONFIG.UPDATE_PROXY:
            try:
                self.log.info("Updating Access Nodes")
                self.update_client(testcase.access_node)
            except Exception as e:
                self.log.exception(f"Failed to update Access Nodes: {e}")
                raise Exception(f"Failed to update Access Nodes: {e}."
                                f" Please manually update the Access Nodes and retry.")

    def source_vm_object_creation(self, cv_testcase):
        """To create basic VSA SDK objects

        Args:

            cv_testcase    (obj)    --    Object of CVTestCase

        Returns:

            None

        Raises:

            Exception:

                if a valid CVTestCase object is not passed.

                if CVTestCase object doesn't have agent initialized
        """

        self._csdb = get_csdb()

        self.commcell = cv_testcase.commcell
        self.client = cv_testcase.client
        self.instance = cv_testcase.instance
        self.backupset = cv_testcase.backupset
        self.subclient = cv_testcase.subclient

        self.auto_commcell = AutoVSACommcell(cv_testcase.commcell,
                                             cv_testcase.csdb,
                                             **{
                                                 "is_metallic": _KUBERNETES_CONFIG.IS_METALLIC,
                                                 "metallic_ring_info": {
                                                     "commcell": cv_testcase.inputJSONnode['commcell']['webconsoleHostname'],
                                                     "user": _METALLIC_CONFIG.workflow_user,
                                                     "password": _METALLIC_CONFIG.workflow_password
                                                 }
                                             }
                                             )
        self.auto_client = AutoVSAVSClient(self.auto_commcell, cv_testcase.client)
        self.auto_instance = AutoVSAVSInstance(self.auto_client,
                                               cv_testcase.agent,
                                               cv_testcase.instance,
                                               **{
                                                   "is_metallic": _KUBERNETES_CONFIG.IS_METALLIC,
                                                   "metallic_ring_info": {
                                                       "commcell": cv_testcase.inputJSONnode['commcell']['webconsoleHostname'],
                                                       "user": _METALLIC_CONFIG.workflow_user,
                                                       "password": _METALLIC_CONFIG.workflow_password
                                                   }
                                               }
                                               )
        self.auto_backupset = AutoVSABackupset(self.auto_instance, cv_testcase.backupset)
        self.auto_subclient = AutoK8sSubclient(self.auto_backupset, cv_testcase.subclient)

    def update_client(self, client_name):
        """
        update the client to the latest service pack
        Args:
            client_name: name of the client

        Returns:
            None
        """
        commcell = self.testcase.commcell
        client = commcell.clients.get(client_name)
        update_job_object = None
        if client.properties['client']['versionInfo']['UpdateStatus'] == BaselineStatus.NEEDS_UPDATE.value:
            self.log.info(f'client : {client_name} is not up to date, trying to start updates')
            if not client.is_ready:
                self.log.warning(f"check readiness is failing for the client : {client_name} so skipping the update")
                return
            update_job_object = client.push_servicepack_and_hotfix(reboot_client=False)
            self.log.info(f'update job for the client : {client_name} : {update_job_object.job_id} is in progress')
            self.log.info("waiting for the job completion")
            update_job_object.wait_for_completion()
            time.sleep(60)
        else:
            self.log.info(f'client : {client_name} is already up-to-date')
            return
        while not client.is_ready:
            self.log.info("sleeping for 2 mins as the client may be booting after upgrade")
            time.sleep(120)

        client = self.auto_commcell.commcell.clients.get(client_name)
        if client.properties['client']['versionInfo']['UpdateStatus'] != BaselineStatus.NEEDS_UPDATE.value:
            self.log.info(f'update successful for the client : {client_name}')
        else:
            if 'part of another running job' in update_job_object.delay_reason:
                self.log.warning(f'{client_name} is part of another running job')
                return
            self.log.exception(f'the proxy client : {client_name} failed to update to the latest version')
            raise Exception(f'the proxy client : {client_name} failed to update to the latest version')

    def load_kubeconfig_file(self, configfile):
        """
        Load Kubeconfig file and connect to the Kubernetes API Server

            Args:

                configfile      (str)   --      Path to kubeconfig file

        """
        self.log.info(f"Loading Kubeconfig file from location [{configfile}]")
        load_kube_config(configfile)
        self.log.info(f"Successfully loaded Kubeconfig file.")

        # Initialize API objects
        self._core_v1_api = CoreV1Api()
        self._apps_v1_api = AppsV1Api()
        self._rbac_auth_v1_api = RbacAuthorizationV1Api()
        self._storage_v1_api = StorageV1Api()
        self._custom_objects_api = CustomObjectsApi()
        self._networking_v1_api = NetworkingV1Api()
        self._policy_v1_api = PolicyV1Api()
        self._autoscaling_v1_api = AutoscalingV1Api()
        self._api_extensions_v1_api = ApiextensionsV1Api()

        self.delete_dict = {
            'Secret': self._core_v1_api.delete_namespaced_secret,
            'ConfigMap': self._core_v1_api.delete_namespaced_config_map,
            'Role': self._rbac_auth_v1_api.delete_namespaced_role,
            'ClusterRole': self._rbac_auth_v1_api.delete_cluster_role
        }

        self.log.info("Dumping cluster node conditions -")
        error_list = []
        for node_obj in self._core_v1_api.list_node().items:
            self.log.info(f"Conditions for node : [{node_obj.metadata.name}]")
            for condition_obj in node_obj.status.conditions:
                self.log.info(
                    f"Type: [{condition_obj.type}]  Status: [{condition_obj.status}]  Reason: [{condition_obj.reason}]"
                )
                if condition_obj.type == "Ready" and condition_obj.status == 'False':
                    error_list.append(f"Node [{node_obj.metadata.name}] is posting status NotReady.")
        else:
            if error_list:
                for error_msg in error_list:
                    self.log.error(error_msg)
                raise KubernetesException('TestScenario', '102', 'Automation cannot proceed')
            else:
                self.log.info("Cluster is healthy to proceed with automation")

    def get_api_server_endpoint(self):
        """Returns the Kubernetes API Server endpoint of the loaded Kubeconfig
        """
        endpoint = self._core_v1_api.api_client.configuration.host
        if not endpoint:
            self.log.error('Could not fetch Kubernetes API Server endpoint information.')
            raise KubernetesException(
                'APIClientOperations', '101', 'Could not fetch Kubernetes API Server endpoint information.'
            )
        self.log.info(f"Fetched API server endpoint : [{endpoint}]")
        return endpoint

    def backup(self, backup_type, **kwargs):
        """ To Run Kubernetes backup

        Args:

            backup_type    (str)    --    backup type

        Returns:

            None

        Raises:

            Exception:

                if a valid CVTestCase object is not passed.

                if CVTestCase object doesn't have agent initialized
        """

        kwargs.update({
            'skip_discovery': True,
            'msg': f'{backup_type} Backup Job',
            'timeout': 60,
            'return_timeout': 90
        })
        self.log.info(self.testcase.tcinputs)
        backup_options = OptionsHelper.BackupOptions(self.auto_subclient)

        backup_type = backup_type.upper()
        if backup_type not in ["FULL", "INCREMENTAL", "SYNTHETIC_FULL"]:
            raise KubernetesException(
                "BackupOperations", "101"
            )
        backup_options.backup_type = backup_type

        if backup_options.collect_metadata:
            raise Exception("Metadata collection is enabled")

        self.log.info(f"Running [{backup_type}] Backup job")
        self.auto_subclient.backup(backup_options, **kwargs)

        backup_job = self.auto_subclient.backup_job
        if self.testcase.tcinputs.get("k8s_backup_version"):
            k8s_backup_version = self.testcase.tcinputs.get("k8s_backup_version")
            self.log.info(f"Specified K8s Backup Version : {k8s_backup_version}")
            # If this is a KFC job, log lines will have to be validated
            if k8s_backup_version == "v2":
                self.log.info("Validating log lines for KFC job")
                self.log.info('*'*50)
                self.match_logs_for_pattern(
                    client_obj=self.testcase.controller,
                    job_id=backup_job.job_id,
                    log_file_name="vsbkp.log",
                    pattern=LogLineRepo.BACKUP_KFC1.value,
                    expected_keyword=None
                )
                self.match_logs_for_pattern(
                    client_obj=self.testcase.controller,
                    job_id=backup_job.job_id,
                    log_file_name="vsbkp.log",
                    pattern=LogLineRepo.BACKUP_KFC2.value,
                    expected_keyword=None
                )

            # If this is a V3 job, log lines will have to be validated
            elif k8s_backup_version == "v3":
                self.log.info("Validating log lines for V3 job")
                self.log.info('*'*50)
                self.match_logs_for_pattern(
                    client_obj=self.testcase.controller,
                    job_id=backup_job.job_id,
                    log_file_name="vsbkp.log",
                    pattern=LogLineRepo.BACKUP_V3_1.value,
                    expected_keyword=None
                )
                self.log.info('*' * 50)
                self.match_logs_for_pattern(
                    client_obj=self.testcase.controller,
                    job_id=backup_job.job_id,
                    log_file_name="vsbkp.log",
                    pattern=LogLineRepo.BACKUP_V3_2.value,
                    expected_keyword=None
                )
                self.log.info('*' * 50)
                self.match_logs_for_pattern(
                    client_obj=self.testcase.controller,
                    job_id=backup_job.job_id,
                    log_file_name="vsbkp.log",
                    pattern=LogLineRepo.BACKUP_V3_3.value,
                    expected_keyword=None
                )
        self.log.info('*' * 50)
        return backup_job

    def restore_out_of_place(self, client_name, restore_namespace, storage_class=None, raise_exception=True, **kwargs):
        """
        Perform out of place Kubernetes Full application restore

        Args:
                client_name             (str):  Destination cluster to restore to

                storage_class           (str):  Storageclass to use with restore

                restore_namespace       (str):  Restore namespace to restore to

                raise_exception         (bool)  :   Raise exception if job has status other than 'Completed'.
                                                    Default: True

        Kwargs:

                restore_name_map        (dict)  :   Provide new name for source paths
                                                    Eg. {'app1' : 'app1-newname'}

                overwrite               (bool)  :   provide unconditional overwrite option


                application_list        (list)  :   List of applications to restore
                                                    If specified, only the applications in the list will be restored

        Exception:
                        if job fails

                        if validation fails

        """
        restore_name_map = kwargs.get("restore_name_map", {})
        overwrite = kwargs.get("overwrite", True)
        application_list = kwargs.get('application_list', [])
        browse_output = self.subclient.browse()
        source_paths = []
        restore_vm_names = {}
        for app_name, app_details in browse_output[1].items():
            application = app_details['name']
            app_type = app_details['snap_display_name'].split('`')[1]
            if app_type == 'Namespace':
                continue
            if application_list and application not in application_list:
                continue
            source_paths.append(application)
        self.log.info(f"Applications to restore : {source_paths}")
        for source_path in source_paths:
            restore_vm_names[source_path] = source_path
            if source_path in restore_name_map:
                restore_vm_names[source_path] = restore_name_map[source_path]
        job = self.subclient.full_app_restore_out_of_place(
            apps_to_restore=source_paths,
            restored_app_name=restore_vm_names,
            kubernetes_client=client_name,
            storage_class=storage_class,
            restore_namespace=restore_namespace,
            overwrite=overwrite
        )
        self.log.info(f"Started FULL APPLICATION OUT-OF-PLACE RESTORE job with job id: {job.job_id}")
        if not job.wait_for_completion(timeout=60, return_timeout=90):
            exception_msg = f"Failed to run FULL APPLICATION OUT-OF-PLACE RESTORE Job [{job.job_id}] " \
                            f"with error: {job.delay_reason}"
            if raise_exception:
                raise KubernetesException("RestoreOperations", "101", exception_msg)
            self.log.warning(exception_msg)

        if not job.status.lower() == "completed":
            exception_msg = f"Job status is not Completed, Job [{job.job_id}] has status: [{job.status}]"
            if raise_exception:
                raise KubernetesException("RestoreOperations", "101", exception_msg)
            self.log.warning(exception_msg)

        self.log.info("Successfully finished FULL APPLICATION OUT-OF-PLACE RESTORE job")
        self.log.info("Waiting till all pods are in running state...")
        namespace_list = [restore_namespace]
        self.wait_till_resources_are_running(namespace_list)
        return job

    def restore_in_place(self, overwrite=True, raise_exception=True, **kwargs):
        """
        Perform in-place Kubernetes Full Application restore

        Args:

                overwrite               (bool)  :   provide unconditional overwrite option

                raise_exception         (bool)  :   Raise exception if job has status other than 'Completed'.
                                                    Default: True

        Kwargs:

                application_list        (list)  :   List of applications to restore
                                                    If specified, only the applications in the list will be restored

        Exception:
                        if job fails

                        if validation fails

        """
        application_list = kwargs.get('application_list', [])
        browse_output = self.subclient.browse()
        source_paths = []
        for app_name, app_details in browse_output[1].items():
            application = app_details['name']
            app_type = app_details['snap_display_name'].split('`')[1]
            if app_type == 'Namespace':
                continue
            if application_list and application not in application_list:
                continue
            source_paths.append(application)
        self.log.info(f"Applications to restore : {source_paths}")
        job = self.subclient.full_app_restore_in_place(
            apps_to_restore=source_paths,
            overwrite=overwrite
        )
        self.log.info(f"Started FULL APPLICATION IN-PLACE RESTORE job with job id: {job.job_id}")
        if not job.wait_for_completion(timeout=60, return_timeout=90):
            exception_msg = f"Failed to run FULL APPLICATION IN-PLACE RESTORE Job [{job.job_id}]" \
                            f" with error: [{job.delay_reason}]"
            if raise_exception:
                raise KubernetesException("RestoreOperations", "101", exception_msg)
            self.log.warning(exception_msg)
        if not job.status.lower() == "completed":
            exception_msg = f"Job status is not Completed, Job [{job.job_id}] has status: [{job.status}]"
            if raise_exception:
                raise KubernetesException("RestoreOperations", "101", exception_msg)
            self.log.warning(exception_msg)
        self.log.info("Successfully finished FULL APPLICATION IN-PLACE RESTORE job")

        return job

    def validate_data(self, src, rst):
        """
        Function to validate entities from both namespaces.

        Args:
            src   (dict): List of resources before backup.

            rst   (dict):  List of resources after restore.

        Raises:

                Exception:

                    if it fails if validation fails.

        """
        self.log.info("Validating dictionaries")
        self.log.info(f"Source resources: {src}")
        self.log.info(f"Destination resources: {rst}")
        if src == rst:
            self.log.info("Resource validation successful. Resources at source and destination are matching")
        else:
            difference = {
                'Present at Source, Not Present at Destination': {},
                'Present at Destination, Not Present at Source': {}
            }
            for key, value in src.items():
                if key in rst:
                    if value != rst[key]:
                        value_diff = list(set(value) - set(rst[key]))
                        if value_diff:
                            difference['Present at Source, Not Present at Destination'].update({
                                key: value_diff
                            })
                else:
                    difference['Present at Source, Not Present at Destination'].update({key: value})
            for key, value in rst.items():
                if key in src:
                    if value != src[key]:
                        value_diff = list(set(value) - set(src[key]))
                        if value_diff:
                            difference['Present at Destination, Not Present at Source'].update({
                                key: value_diff
                            })
                else:
                    difference['Present at Destination, Not Present at Source'].update({key: value})

            message = f"Resources at source and destination do not match. [{difference}]"
            self.log.error(message)
            raise KubernetesException(
                "ValidationOperations", "108", message
            )

    def validate_data_with_timestamp(self, src, rst):
        """
        Function to validate entities along with their creation timestamps from both namespaces.

        Args:
            src   (dict): List of resources before backup.

            rst   (dict):  List of resources after restore.

        Raises:
            Exception:
                if it fails if validation fails.

        """
        self.log.info("Validating dictionaries")
        self.log.info(f"Source resources: {src}")
        self.log.info(f"Destination resources: {rst}")

        difference = {}

        for resource_type in src:
            for resource_before_backup in src[resource_type]:
                resource_name = resource_before_backup['name']
                creation_timestamp_before_backup = resource_before_backup['creation_timestamp_seconds']

                matching_resources_after_restore = [resource for resource in rst[resource_type]
                                                    if resource['name'] == resource_name]

                if matching_resources_after_restore:
                    creation_timestamp_after_restore = matching_resources_after_restore[0][
                            'creation_timestamp_seconds']

                    if creation_timestamp_after_restore > creation_timestamp_before_backup:
                        self.log.info(f"Resource '{resource_name}' restored in place with overwrite --> "
                                      f"before:{creation_timestamp_before_backup} "
                                      f"after:{creation_timestamp_after_restore}")
                    else:
                        difference[resource_name] = {'status': 'Not restored in place with overwrite',
                                                     'before_backup': resource_before_backup,
                                                     'after_restore': matching_resources_after_restore[0]}
                        self.log.warning(f"Resource '{resource_name}' not restored in place with overwrite.")
                else:
                    difference[resource_name] = {'status': 'Missing after restore',
                                                 'before_backup': resource_before_backup, 'after_restore': None}
                    self.log.error(f"Resource '{resource_name}' missing after restore.")

        message = f"Inplace Restore with overwrite unsuccessful : {difference}"
        if difference:
            self.log.error(message)
            raise KubernetesException(
                    "ValidationOperations", "108", message
            )

    def add_block_data(self, pod_name, namespace, count=30000, device_path="/dev/xdb"):

        """
        Function to add block data to block device.

        Args:
            pod_name    (str)   : Name of the pod which has block device attached.

            namespace   (str)   : Namespace for adding block data

            count       (int)   : Number of input blocks

            device_path (str)   : mount path of device attached to pod

        Raises:

                Exception:

                    if it fails to create data.

        """

        self.log.info("Creating block data on devicePath [{}]".format(device_path))

        command_str = (f'dd if=/var/log/dpkg.log of=/tmp/dpkg-temp.log bs=1 count={count} '
                       f'status=none conv=fdatasync,fsync')
        self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace
        )

        command_str = f'dd if=/tmp/dpkg-temp.log of={device_path} bs=1 count={count} status=none conv=fdatasync,fsync'
        self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace
        )

        self.log.info("Successfully created dummy data for block device")

    def validate_block_data(self, pod_name, namespace, source_path, device_path, count=3000,
                            dest_path="/home/dpkg.log", **kwargs):
        """
        Function to validate block device data

        Args:

            pod_name            (str)   : Name of pod

            namespace           (str)   : Namespace of the pod

            source_path         (str)   : Source content path

            device_path         (str)   : Device path of the block device

            count               (int)   : Number of blocks to copy

            dest_path           (str)   : Destination path to restore

        Raises:

                KubernetesException:

                    if comparison fails

        """

        container = kwargs.get('container', None)

        self.log.info("Copying data from block device [{}] to [{}]".format(device_path, dest_path))

        command_str = f'dd of={dest_path} if={device_path} bs=1 count={count} status=none conv=fdatasync,fsync'
        self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace,
            container=container
        )

        self.log.info("Copying data from [{}] to temporary location [/tmp/dpkg-temp.log]".format(source_path))
        command_str = f'dd of=/tmp/dpkg-temp.log if={source_path} bs=1 count={count} status=none conv=fdatasync,fsync'
        self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace,
            container=container
        )

        self.log.info(f"Performing diff comparison between [/tmp/dpkg-temp.log] and [{dest_path}]")
        command_str = f'diff {dest_path} /tmp/dpkg-temp.log'
        resp = self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace,
            container=container
        )
        if not resp:
            raise KubernetesException('ValidationOperations', '101')
        self.log.info("Diff comparison successful")

        self.log.info(f"Performing cksum comparison between [/tmp/dpkg-temp.log] and [{dest_path}]")
        command_str = f'cksum {dest_path} /tmp/dpkg-temp.log'
        self.log.info(f"Executing command : [{command_str}]")
        resp = exec_stream(
            self._core_v1_api.connect_get_namespaced_pod_exec,
            pod_name,
            namespace,
            container=container,
            command=['/bin/sh', '-c', command_str],
            stderr=True,
            stdin=False, stdout=True, tty=False
        )
        line1, line2 = resp.strip().split('\n')
        if line1.split()[:2] != line2.split()[:2]:
            raise KubernetesException(
                "ValidationOperations", "102", f"Output : {resp.strip()}"
            )
        self.log.info("Cksum comparison successful")

    def validate_restored_manifest(self, manifest_path, master_machine, kubeconfig):
        """
        Function to Compares the current state of the namespace/pod/pvc against the
        state that the namespace/pod/pvc would be in if the manifest was applied.

        Args:

            manifest_path   (String): path to the manifest files.

            master_machine          (string)    : Machine that has kubectl configured with testcase

            kubeconfig              (string)    : Location of kubeconfig file on master_machine

        Raises:

                KubernetesException:

                    If validation fails.

        """
        cmd = "ls {}".format(manifest_path)
        master_machine = Machine(self.commcell.clients.get(master_machine))
        self.log.info("Getting list of yaml files by running command %s " % str(cmd))
        output = master_machine.execute_command(cmd)

        yaml_list = output.formatted_output if (type(output.formatted_output) is list) else [[output.formatted_output]]

        for yaml in yaml_list:
            yaml_name = yaml[0].replace(r"`", r"\`")
            cmd = "kubectl diff -f {0}/{1} --kubeconfig {2}".format(manifest_path, yaml_name, kubeconfig)
            self.log.info("Running command:  %s" % str(cmd))
            output = master_machine.execute_command(cmd)
            if output.exit_code == 0:
                self.log.info("Yaml {0} and current cluster comparison successful ".format(yaml[0]))
            elif 'Service' not in yaml_name:
                raise KubernetesException(
                    'ValidationOperations', '101', f'Command : [{cmd}] Output : [{output.formatted_output}]'
                )
            else:
                for element in output.formatted_output:
                    testline = ""
                    for i in element:
                        testline = testline + i
                    # for db application, the service nodeport will be different from source pod
                    # for "kubectl diff" result, if only nodePort is different, then mark result
                    # as pass
                    if 'Service' not in testline:
                        if testline[0] in ['+', '-'] and 'nodePort' not in testline:
                            raise KubernetesException(
                                'ValidationOperations', '101', 'Manifest for Service is different'
                            )
                self.log.info("Except nodePort, Yaml {0} and current cluster comparison successful".format(yaml[0]))

    def k8s_verify_restore_files(self, source_namespace, restore_namespace,
                                 mount_point='/mnt/data', print_checksum=False, **kwargs):
        """Compare the md5 checksum of files in the mount point

            Args:

                source_namespace    (str)   --  Source namespace

                restore_namespace   (str)   --  Restore destination namespace

                mount_point         (str)   --  Mount point of PVC

                print_checksum      (bool)  --  Print the checksum dictionary if set to true

            Raises:

                  KubernetesException     --  if restore verification fails

        """

        pod_container = kwargs.get('container', None)

        original_files_hash = self.get_files_checksum(source_namespace, mount_point, container=pod_container)
        if print_checksum:
            self.log.info(f"Original Files Hash : {original_files_hash}")

        restored_files_hash = self.get_files_checksum(restore_namespace, mount_point, container=pod_container)
        if print_checksum:
            self.log.info(f"Restored Files Hash : {restored_files_hash}")

        # Validate the two dictionaries
        self.log.info("Comparing checksum for restored pods and original pods")
        self.verify_checksum_dictionary(original_files_hash, restored_files_hash)

        self.log.info("Restored files verification successful.")

    @DebugSkip()
    def delete_cv_clusterrolebinding(self, name):
        """Delete clusterrolebinding

            Args:

                name                (str)   --  Name of clusterrolebinding

        """
        # Delete cluster role binding
        self.log.info(f"Deleting ClusterRoleBinding [{name}]")
        if name in [obj.metadata.name for obj in self._rbac_auth_v1_api.list_cluster_role_binding().items]:
            self._rbac_auth_v1_api.delete_cluster_role_binding(name)
            self.log.info(f"Existing ClusterRoleBinding [{name}] deleted.")
            KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.LOOKUP_WAIT, trials=1)

    def create_cv_serviceaccount(self, name, sa_namespace="default", secret=True):
        """Create service account

            Args:

                name            (str)   --  name of service account

                sa_namespace    (str)   --  service account namespace

                secret          (bool)  --  To create service account token

        """
        if name in [obj.metadata.name for obj in self._core_v1_api.list_namespaced_service_account(sa_namespace).items]:
            self.log.info(f"ServiceAccount [{name}] in namespace [{sa_namespace}] account exists. Deleting to recreate")
            self.delete_cv_serviceaccount(name, sa_namespace)

        self._core_v1_api.create_namespaced_service_account(
            sa_namespace,
            body=KubernetesUtils.serviceaccount_json_manifest(sa_namespace, name)
        )

        self.log.info(f"Created ServiceAccount [{name}] created in namespace [{sa_namespace}]")

        if secret:
            secret_name = name + '-token'
            annotations = {'kubernetes.io/service-account.name': name}
            secret_type = 'kubernetes.io/service-account-token'
            labels = {}
            self.create_cv_secret(
                name=secret_name, namespace=sa_namespace,
                secret_type=secret_type, annotations=annotations, labels=labels
            )

    def create_cv_clusterrolebinding(self, name, sa_name, sa_namespace="default", cluster_role_name="cluster-admin"):
        """Create clusterrolebinding

            Args:

                name                (str)   --  Name of clusterrolebinding

                sa_name             (str)   --  name of service account

                sa_namespace        (str)   --  service account namespace

                cluster_role_name   (str)   --  name of the cluster role

        """
        if name in [obj.metadata.name for obj in self._rbac_auth_v1_api.list_cluster_role_binding().items]:
            self.log.info(f"ClusterRoleBinding [{name}] exists. Deleting to recreate.")
            self.delete_cv_clusterrolebinding(name)

        crb_manifest = KubernetesUtils.clusterrolebinding_json_manifest(name, sa_namespace, sa_name, cluster_role_name)
        self._rbac_auth_v1_api.create_cluster_role_binding(crb_manifest)
        self.log.info(f"ClusterRoleBinding [{name}] created with ClusterRole [{cluster_role_name}]")

    def get_serviceaccount_token(self, name, sa_namespace="default"):
        """Get token for service account

            Args:

                name                (str)   --  Name of service account

                sa_namespace        (str)   --  service account namespace

            Returns:

                Token for service account

        """
        for secret in self._core_v1_api.list_namespaced_secret(namespace=sa_namespace).items:
            if secret.type == "kubernetes.io/service-account-token" and \
                    secret.metadata.annotations['kubernetes.io/service-account.name'] == name:
                decoded_token = b64decode(secret.data['token']).decode('utf-8')
                self.log.info(f"Token fetched for ServiceAccount [{name}] in namespace [{sa_namespace}]")
                break
        else:
            raise KubernetesException(
                "APIClientOperations", "101", "No secret found with kubernetes.io/service-account-token type"
            )

        return decoded_token

    def get_filename_inode_mapping(self, path, access_node=None, pod_name=None, namespace=None):
        """
        Returns a mapping of filenames to inode numbers for all files under the given mount point.

        Args:
            path (str): The mount point or directory to traverse.
            pod_name (str): The name of the pod where the files are located.
            namespace (str): The namespace where the pod is located.
            access_node (str): The name of the access node on to execute the command.

        Returns:
            dict: A dictionary mapping filenames (absolute paths) to their inode numbers.
        """
        # Command to find all files and directories under 'path' and print their paths and inode numbers
        command = f'find {path} -exec stat -c "%n %i" {{}} \\;'

        if (not pod_name) and (not namespace) and access_node:
            self.log.info("Executing the command in the Access Node")
            proxy_obj = Machine(self.commcell.clients.get(access_node))
            resp = proxy_obj.execute_command(command)
            self.log.info(resp)

        else:
            resp = exec_stream(
                self._core_v1_api.connect_get_namespaced_pod_exec, pod_name,
                namespace,
                container=None,
                command=['/bin/sh', '-c', command],
                stderr=True,
                stdin=False, stdout=True, tty=False
            )
            self.log.info(resp)

        # Initialize an empty dictionary to store the mapping
        filename_inode_mapping = {}

        # Process the output line by line
        for line in resp.strip().split('\n'):
            if line:
                # Each line should contain the filename and inode number separated by a space
                try:
                    filepath, inode = line.strip().rsplit(' ', 1)
                    filename_inode_mapping[filepath] = inode
                except ValueError:
                    self.log.warning(f"Unable to parse line: {line}")
                    continue

        self.log.info(f"Filename-Inode mapping: {filename_inode_mapping}")
        return filename_inode_mapping

    def create_cv_namespace(self, name, **kwargs):
        """Create service account

            Args:

                name            (str)   --  name of namespace

            Kwargs:

                labels      (dict)      --  Dictionary of labels {key1: value1 , key2: value2}

                delete      (bool)      --  Delete if already exists and recreate

        """
        delete = kwargs.get("delete", True)
        if name in [obj.metadata.name for obj in self._core_v1_api.list_namespace().items]:
            if not delete:
                self.log.info(f"Namespace [{name}] already exists. Sent flag to skip delete if exists.")
                return
            self.log.info("Namespace [{}] already exists, deleting to recreate it.".format(name))
            self.delete_cv_namespace(name)
        self._core_v1_api.create_namespace(
            body=KubernetesUtils.namespace_json_manifest(name, **kwargs)
        )
        self.log.info("Created Namespace [{}]".format(name))
        KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.APPLICATION_WAIT)

    def create_cv_pvc(self, name, namespace, storage="10Gi", accessmode="ReadWriteOnce", storage_class=None, **kwargs):
        """Create PVC

            Args:

                name                (str)   --  Name of pvc

                namespace           (str)   --  Namespace to create PVC in

                storage             (str)   --  Storage to provision

                accessmode          (str)   --  Access mode for PVC

                storage_class       (str)   --  Storage class for PVC

            Kwargs:

                labels              (dict)  --  Dictionary specifying labels

        """
        self._core_v1_api.create_namespaced_persistent_volume_claim(
            namespace,
            body=KubernetesUtils.pvc_json_manifest(
                name=name,
                storage_class=storage_class,
                accessmode=accessmode,
                storage=storage,
                **kwargs
            )
        )
        self.log.info(f"Created PersistentVolumeClaim [{name}] in namespace [{namespace}]")
        KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.APPLICATION_WAIT)

    def create_cv_secret(self, name, namespace, **kwargs):
        """Create secret

            Args:

                name       (str)   --  name of secret

                namespace   (str)   --  namespace

        """
        self._core_v1_api.create_namespaced_secret(namespace, body=KubernetesUtils.secret_json_manifest(name, **kwargs))
        self.log.info("Created Secret [{}] in namespace [{}]".format(name, namespace))

    def create_cv_configmap(self, name, namespace):
        """Create configmap

            Args:

                name       (str)   --  name of configmap

                namespace   (str)   --  namespace

        """
        self._core_v1_api.create_namespaced_config_map(namespace, body=KubernetesUtils.configmap_json_manifest(name))
        self.log.info("Created ConfigMap [{}] in namespace [{}]".format(name, namespace))

    def create_cv_svc(self, name, namespace, **kwargs):
        """Create Service

            Args:

                name                (str)   --  Name of service

                namespace           (str)   --  Namespace

            Kwargs:

                selector            (dict)  --  Selectors for labels

                port                (int)   --  Port number for service

                labels              (dict)  --  Dictionary specifying labels

        """
        self._core_v1_api.create_namespaced_service(
            namespace=namespace,
            body=KubernetesUtils.service_json_manifest(name, **kwargs)
        )
        self.log.info("Created Service [{}] in namespace [{}]".format(name, namespace))

    def create_cv_pod(self, name, namespace, **kwargs):
        """Create Pod

            Args:

                name                (str)   --  Name of pod

                namespace           (str)   --  Namespace

            Kwargs:

                pvc_name            (str)   --  Name of pvc

                configmap           (str)   --  Name of configmap to mount

                secret              (str)   --  Name of secret to mount

                labels              (dict)  --  Dictionary specifying labels

        """
        self._core_v1_api.create_namespaced_pod(
            namespace=namespace, body=KubernetesUtils.pod_ubuntu_json_manifest(name, **kwargs)
        )
        self.log.info(f"Created Pod [{name}] in namespace [{namespace}]")
        KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.APPLICATION_WAIT)

    def create_random_hlinks(self, pod_name, namespace, **kwargs):
        """Generate random data in pod

            Args:

                pod_name            (str)   --  Name of pod

                namespace           (str)   --  Namespace

            Kwargs:

                no_of_files         (int)   --  Number of files to create

                location            (str)   --  Location for mountpoint

                file_size           (int)   --  Size of files in MB

                foldername          (str)   --  Name of the folder

        """

        no_of_files = kwargs.get("no_of_files", 3)
        location = kwargs.get("location", "/mnt/data")
        file_size = kwargs.get("file_size", 1)
        foldername = kwargs.get("foldername", None)
        container = kwargs.get("container", None)
        random_string = get_random_string()

        if foldername is None:
            foldername = random_string

        # Create Directory in Pod
        self.create_pod_dir(pod_name, namespace, location=location, foldername=foldername)

        # Generate random data for hlinks
        command_str = (
            f'for i in $(seq 1 {no_of_files}); '
            f'do dd if=/dev/urandom of={location}/{foldername}/hfile-{random_string}-$i '
            f'bs=1024 count={file_size}K status=none conv=fdatasync,fsync; '
            f'sync {location}/{foldername}/hfile-{random_string}-$i; done;'
        )
        self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace,
            container=container
        )

        # Create hlinks
        command_str = (
            f'for i in $(seq 1 {no_of_files}); '
            f'do ln {location}/{foldername}/hfile-{random_string}-$i '
            f'{location}/{foldername}/hlink-{random_string}-$i; '
            f'sync {location}/{foldername}/hlink-{random_string}-$i; done;'
        )
        self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace,
            container=container
        )

        self.execute_command_in_pod(
            command="sync --file-system",
            pod=pod_name,
            namespace=namespace,
            container=container
        )

        self.log.info(f"Command to create hard links executed for Pod [{pod_name}] in [{namespace}]")

    def create_random_slinks(self, pod_name, namespace, **kwargs):
        """Generate random data in pod

            Args:

                pod_name            (str)   --  Name of pod

                namespace           (str)   --  Namespace

            Kwargs:

                no_of_files         (int)   --  Number of files to create

                location            (str)   --  Location for mountpoint

                file_size           (int)   --  Size of files in MB

                foldername          (str)   --  Name of the folder

        """

        no_of_files = kwargs.get("no_of_files", 3)
        location = kwargs.get("location", "/mnt/data")
        file_size = kwargs.get("file_size", 1)
        foldername = kwargs.get("foldername", None)
        container = kwargs.get("container", None)
        random_string = get_random_string()

        if foldername is None:
            foldername = random_string

        # Create Directory in Pod
        self.create_pod_dir(pod_name, namespace, location=location, foldername=foldername)

        # Generate random data for slinks
        command_str = (
            f'for i in $(seq 1 {no_of_files}); '
            f'do dd if=/dev/urandom of={location}/{foldername}/sfile-{random_string}-$i '
            f'bs=1024 count={file_size}K status=none conv=fdatasync,fsync; '
            f'sync {location}/{foldername}/sfile-{random_string}-$i; done;'
        )
        self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace,
            container=container
        )

        # Generate slinks
        command_str = (
            f'for i in $(seq 1 {no_of_files}); '
            f'do ln -s {location}/{foldername}/sfile-{random_string}-$i '
            f'{location}/{foldername}/slink-{random_string}-$i; '
            f'sync {location}/{foldername}/slink-{random_string}-$i; done;'
        )
        self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace,
            container=container
        )

        self.execute_command_in_pod(
            command="sync --file-system",
            pod=pod_name,
            namespace=namespace,
            container=container
        )

        self.log.info(f"Command to create symbolic links executed for Pod [{pod_name}] in namespace [{namespace}]")

    def create_random_cv_pod_data(self, pod_name, namespace, **kwargs):
        """Generate random data in pod

            Args:

                pod_name            (str)   --  Name of pod

                namespace           (str)   --  Namespace

            Kwargs:

                no_of_files         (int)   --  Number of files to create

                location            (str)   --  Location for mountpoint

                file_size           (int)   --  Size of files in MB

                foldername          (str)   --  Name of the folder

                hlink               (bool)  --  To create hardlinks

                slink               (bool)  --  To create softlinks

                file_name           (str)   --  Name of file

                file_size_in_kb     (bool)  --  File size is in terms of KB

                file_size_in_gb     (bool)  --  File size is in terms of GB
        """

        no_of_files = kwargs.get("no_of_files", 20)
        location = kwargs.get("location", "/mnt/data")
        file_size = kwargs.get("file_size", 10)
        foldername = kwargs.get("foldername", None)
        hlink = kwargs.get("hlink", False)
        slink = kwargs.get("slink", False)
        random_string = get_random_string()
        file_name = kwargs.get("file_name", f"file-{random_string}")
        container = kwargs.get("container", None)
        file_size_in_kb = kwargs.get("file_size_in_kb", False)
        file_size_in_gb = kwargs.get("file_size_in_gb", False)

        if foldername is None:
            foldername = random_string

        # Create Directory in Pod
        self.create_pod_dir(pod_name, namespace, location=location, foldername=foldername, container=container)

        # Generate random data
        if file_size_in_kb:
            command_str = (
                f'for i in $(seq 1 {no_of_files}); '
                f'do dd if=/dev/urandom of={location}/{foldername}/$i bs={file_size} count=1 status=none; '
                f'done;'
            )
        elif file_size_in_gb:
            bs = str(file_size)+'M'
            command_str = (
                f'for i in $(seq 1 {no_of_files}); '
                f'do dd if=/dev/urandom of={location}/{foldername}/$i bs={bs} count=1024 status=none; '
                f'done;'
            )
        else:
            command_str = (
                f'for i in $(seq 1 {no_of_files}); '
                f'do dd if=/dev/urandom of={location}/{foldername}/{file_name}-$i '
                f'bs=1024 count={file_size}k status=none conv=fdatasync,fsync; '
                f'sync {location}/{foldername}/{file_name}-$i; done;'
            )

        self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace,
            container=container
        )
        self.execute_command_in_pod(
            command="sync --file-system",
            pod=pod_name,
            namespace=namespace,
            container=container
        )

        # Create hardlinks
        if hlink:
            self.create_random_hlinks(
                pod_name, namespace,
                no_of_files=no_of_files,
                location=location,
                file_size=file_size,
                folder=foldername,
                container=container
            )
        # Create symlinks
        if slink:
            self.create_random_slinks(
                pod_name, namespace,
                no_of_files=no_of_files,
                location=location,
                file_size=file_size,
                folder=foldername,
                container=container
            )

        self.log.info(f"Created random test data in Pod [{pod_name}] in namespace [{namespace}]")

    def modify_pod_data(self, pod_name, namespace, folder_name, location='/mnt/data', delete=False, **kwargs):
        """
        Modify existing files at restore directory

            Args:

                pod_name            (str)   --  Name of pod

                namespace           (str)   --  Namespace

                folder_name         (str)   -- folder where data is located, relative to location

                location            (str)   -- mount point

                delete              (bool)  -- True if you want to delete folder

        """

        container = kwargs.get('container', None)

        full_location = f'{location}/{folder_name}'

        self.log.info(
            f"Modifying files at destination [{full_location}]" +
            f"in pod [{pod_name}] and namespace [{namespace}]"
        )

        file_list = self.list_pod_content(
            pod_name=pod_name,
            namespace=namespace,
            location=full_location,
            container=container
        )

        command = "echo 'modified file' > {0}/{1}"
        if delete:
            command = "rm -rf {0}/{1}"

        for file_name in file_list:
            resp = self.execute_command_in_pod(
                command=command.format(full_location, file_name),
                pod=pod_name,
                namespace=namespace,
                container=container,
                wait_time=2
            )
            if not resp:
                raise KubernetesException("APIClientOperations", "102", f"Command execution [{command}] failed")

        self.log.info("Modify existing files successful.")

    def move_cv_pod_data(self, pod_name, namespace, foldername, location='/mnt/data', **kwargs):
        """Move content in pod.

            Args:

                pod_name            (str)   --  Name of pod

                namespace           (str)   --  Namespace

                location            (str)   --  Location for mountpoint

                foldername           (int)  --  Name of the folder

        """

        container = kwargs.get('container', None)

        movepodpath = "MOVED"
        command_str = f'mv -f {location}/{foldername} {location}/{movepodpath}'
        self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace,
            container=container
        )
        self.execute_command_in_pod(
            command="sync --file-system",
            pod=pod_name,
            namespace=namespace,
            container=container
        )

        self.log.info(
            f"Moved folder [{location}/{foldername}] to [{location}/{movepodpath}] in Pod [{namespace}][{pod_name}]"
        )

    @DebugSkip()
    def delete_cv_namespace(self, namespace, **kwargs):
        """Delete namespace

            Args:

                namespace       (str)   --  name of namespace

            Kwargs:

                timeout         (int)   --  Timeout interval in seconds

        """

        timeout = kwargs.get("timeout", 300)

        self.log.info(f"Deleting namespace [{namespace}]")
        if namespace in [obj.metadata.name for obj in self._core_v1_api.list_namespace().items]:
            try:
                start_time = time.time()
                while True:
                    self._core_v1_api.delete_namespace(namespace, _request_timeout=timeout)
                    KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.APPLICATION_WAIT, trials=1)
                    current_time = time.time()

                    if current_time - start_time > timeout:
                        self.log.warning(f"Deletion timed out for Namespace [{namespace}]")
                        break
            except ApiException:
                self.log.info(f"Deleted Namespace [{namespace}]")

    @DebugSkip()
    def delete_cv_serviceaccount(self, sa_name, sa_namespace, secret=True):
        """Delete service account

            Args:

                sa_name         (str)   --  name of service account

                sa_namespace    (str)   --  service account namespace

                secret          (bool)  --  To delete secret created along with service account

        """
        sa_list = self._core_v1_api.list_namespaced_service_account(sa_namespace).items
        if sa_name in [obj.metadata.name for obj in sa_list]:
            self.log.info(f"Deleting ServiceAccount [{sa_name}] from namespace [{sa_namespace}]")
            if secret:
                # Delete token secret before service account
                secret_name = sa_name + "-token"
                self.delete_cv_secret(name=secret_name, namespace=sa_namespace)

            self._core_v1_api.delete_namespaced_service_account(sa_name, sa_namespace)
            self.log.info(f"ServiceAccount [{sa_name}] deleted from namespace [{sa_namespace}]")
            KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.RESOURCE_WAIT)

    @DebugSkip()
    def delete_cv_secret(self, name, namespace):
        """Delete secret

            Args:

                name        (str)       --  Name of Secret to delete

                namespace   (str)       --  Name of namespace which has the Secret

        """

        secret_list = self._core_v1_api.list_namespaced_secret(namespace).items
        if name in [obj.metadata.name for obj in secret_list]:
            self.log.info(f"Deleting Secret [{name}] from namespace [{namespace}]")
            self._core_v1_api.delete_namespaced_secret(name, namespace)
            self.log.info(f"Secret [{name}] deleted from namespace [{namespace}]")
        KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.RESOURCE_WAIT)

    @DebugSkip()
    def delete_cv_resource_generic(self, name, object_type, **kwargs):
        """
        Delete a generic resource.

            Args:

                name:       (str)       -- Name of object

                object_type (str)       -- Type of object [Secret, ConfigMap, Role, ClusterRole]

        """

        namespace = kwargs.get('namespace', None)
        delete_function = self.delete_dict[object_type]

        if namespace:
            self.log.info(f"Deleting [Kind: {object_type}] [Name: {name}] from namespace [{namespace}]")
            delete_function(name=name, namespace=namespace)
        else:
            self.log.info(f"Deleting [Kind: {object_type}] [Name: {name}]")
            delete_function(name=name)

    @DebugSkip()
    def delete_cv_pod(self, name, namespace, **kwargs):
        """Delete Pod in namespace

            Args:

                name        (str)       --  Name of Pod to delete

                namespace   (str)       --  Name of namespace which has the Pod

            Kwargs:

                timeout     (int)       --  Timeout interval in seconds

        """

        timeout = kwargs.get("timeout", 60)

        if name in self.get_namespace_pods(namespace=namespace):
            self.log.info(f"Deleting Pod [{name}] from namespace [{namespace}]")
            try:
                start_time = time.time()
                while True:
                    self._core_v1_api.delete_namespaced_pod(
                        name=name,
                        namespace=namespace,
                        _request_timeout=timeout
                    )
                    KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.LOOKUP_WAIT, trials=1)
                    current_time = time.time()
                    if current_time - start_time > timeout:
                        self.log.warning(f"Deletion timed out for Pod [{name}] in Namespace [{namespace}]")
                        break
            except ApiException:
                self.log.info(f"Deleted Pod [{name}] in Namespace [{namespace}]")

    def create_cv_deployment(self, name, namespace, pvcname=None, **kwargs):
        """Create Deployment

            Args:

                name                (str)   --  Name of pvc

                namespace           (str)   --  Namespace to create PVC in

                pvcname             (str)   --  PVC name

            Kwargs:

                labels              (dict)  --  Dictionary specifying labels

                env_secret          (str)   :   Name of env secret to use

                env_configmap       (str)   :   Name of the environment secret to use

                projected_secret    (str)   :   Name of the secret to use as projected volume

                projected_configmap (str)   :   Name of the configmap to use as projected volume

                init_containers     (bool)  :   Specify whether to use init containers in Pods

                resources           (bool)  :   Specify whether to use resource limits on Pods

                replicas            (int)   :   Number of replicas of pod

                service_account     (str)   :   Name of service account

        """
        self._apps_v1_api.create_namespaced_deployment(
            namespace,
            body=KubernetesUtils.deployment_json_manifest(
                name=name,
                pvcname=pvcname,
                **kwargs
            )
        )
        self.log.info(f"Created Deployment [{name}] in namespace [{namespace}]")
        KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.APPLICATION_WAIT)

    def create_cv_statefulset(self, name, namespace, **kwargs):
        """
        Create Statefulset

            Args:

                name                (str)   --  Name of pvc

                namespace           (str)   --  Namespace to create PVC in

            kwargs:

                labels              (dict)  --  Dictionary of labels

        """
        self._apps_v1_api.create_namespaced_stateful_set(
            namespace,
            body=KubernetesUtils.statefulset_json_manifest(name=name, **kwargs)
        )
        self.log.info(f"Created StatefulSet [{name}] in namespace [{namespace}]")

    def create_cv_role(self, name, namespace):
        """Create Role

            Args:

                name                (str)   --  Name of role

                namespace           (str)   --  Namespace to create role

        """

        role_manifest = KubernetesUtils.role_json_manifest(name, namespace)
        self._rbac_auth_v1_api.create_namespaced_role(namespace, role_manifest)
        KubernetesUtils.implicit_wait(timeout=_KUBERNETES_CONFIG.RESOURCE_WAIT)
        self.log.info(f"Role [{name}] created in namespace [{namespace}]")

    def create_cv_cluster_role(self, name):
        """Create Cluster Role

                            Args:

                                name                (str)   --  Name of role


                """

        cluster_role_manifest = KubernetesUtils.cluster_role_json_manifest(name)
        self._rbac_auth_v1_api.create_cluster_role(cluster_role_manifest)
        KubernetesUtils.implicit_wait(timeout=_KUBERNETES_CONFIG.RESOURCE_WAIT)
        self.log.info(f"Cluster Role [{name}] created")

    def create_cv_role_binding(self, name, namespace, ref_kind, ref_name, sa_name, sa_namespace):
        """Create Role Binding

            Args:

                name                (str)   --  Name of role

                namespace           (str)   --  Namespace to create role

                ref_kind            (str)   --  Reference type - Role or ClusterRole

                ref_name            (str)   --  Name of Role/ClusterRole

                sa_name             (str)   --  Name of Service Account

                sa_namespace        (str)   --  Namespace of Service Account

        """

        role_binding_manifest = KubernetesUtils.role_binding_json_manifest(
            name=name,
            namespace=namespace,
            ref_kind=ref_kind,
            ref_name=ref_name,
            sa_name=sa_name,
            sa_namespace=sa_namespace
        )

        self._rbac_auth_v1_api.create_namespaced_role_binding(namespace=namespace, body=role_binding_manifest)
        KubernetesUtils.implicit_wait(timeout=_KUBERNETES_CONFIG.RESOURCE_WAIT)
        self.log.info(f"Role Binding [{name}] created in namespace [{namespace}]")

    def create_cv_network_policy(self, name, namespace, match_labels, **kwargs):
        """Create Network Policy

            Args:

                name                (str)   --  Name of network policy

                namespace           (str)   --  Namespace to create network policy in in

                match_labels        (dict)  --  Dictionary of labels for Pod Selector

            Kwargs:

                labels              (dict)  --  Dictionary of labels

        """

        self._networking_v1_api.create_namespaced_network_policy(
            namespace=namespace,
            body=KubernetesUtils.network_policy_json_manifest(
                name=name,
                match_labels=match_labels,
                **kwargs
            )
        )
        self.log.info(f"Created NetworkPolicy [{name}] in namespace [{namespace}]")

    def create_cv_ingress(self, name, service_name, namespace, **kwargs):
        """Create Ingress

            Args:

                name                (str)   --  Name of Ingress

                service_name        (str)   --  Name of the service to link Ingress

                namespace           (str)   --  Namespace to create Ingress in

            Kwargs:

                labels              (dict)  --  Dictionary of labels

                tls_secret          (str)   --  Name of TLS secret

        """

        self._networking_v1_api.create_namespaced_ingress(
            namespace=namespace,
            body=KubernetesUtils.ingress_json_manifest(
                name=name,
                service_name=service_name,
                **kwargs
            )
        )
        self.log.info(f"Created Ingress [{name}] in namespace [{namespace}] to Service [{service_name}]")

    def create_cv_resource_quota(self, name, namespace, **kwargs):
        """Create Resource Quota

            Args:

                name                (str)   --  Name of Resource Quota

                namespace           (str)   --  Namespace to create Resource Quota in

            Kwargs:

                labels              (dict)  --  Dictionary of labels

        """

        self._core_v1_api.create_namespaced_resource_quota(
            namespace=namespace,
            body=KubernetesUtils.resource_quota_json_manifest(
                name=name,
                **kwargs
            )
        )
        self.log.info(f"Created ResourceQuota [{name}] in namespace [{namespace}]")

    def create_cv_limit_range(self, name, namespace, **kwargs):
        """Create Limit Range

            Args:

                name                (str)   --  Name of Limit Range

                namespace           (str)   --  Namespace to create Limit Range in

            Kwargs:

                labels              (dict)  --  Dictionary of labels

        """

        self._core_v1_api.create_namespaced_limit_range(
            namespace=namespace,
            body=KubernetesUtils.limit_range_json_manifest(
                name=name,
                **kwargs
            )
        )
        self.log.info(f"Created LimitRange [{name}] in namespace [{namespace}]")

    def create_cv_pdb(self, name, namespace, match_labels, **kwargs):
        """Create Pod Disruption Budget

            Args:

                name                (str)   --  Name of Pod Disruption Budget

                namespace           (str)   --  Namespace to create Pod Disruption Budget in

                match_labels        (dict)  --  Dictionary of labels for Pod Selector

            Kwargs:

                labels              (dict)  --  Dictionary of labels

        """

        self._policy_v1_api.create_namespaced_pod_disruption_budget(
            namespace=namespace,
            body=KubernetesUtils.pdb_json_manifest(
                name=name,
                match_labels=match_labels,
                **kwargs
            )
        )
        self.log.info(f"Created PodDisruptionBudget [{name}] in namespace [{namespace}]")

    def create_cv_hpa(self, name, namespace, target_ref_name, api_version="v1", **kwargs):
        """Create Horizontal Pod Autoscaler

            Args:

                name                (str)   --  Name of Horizontal Pod Autoscaler

                namespace           (str)   --  Namespace to create Horizontal Pod Autoscaler in

                target_ref_name     (str)   --  Name of the target reference resource

                api_version         (str)   --  API Version of the PDB Resource to create

            Kwargs:

                labels              (dict)  --  Dictionary of labels

        """

        funcs = {
            "v1": self._autoscaling_v1_api,
            "v2": self._autoscaling_v2_api
        }

        funcs[api_version].create_namespaced_horizontal_pod_autoscaler(
            namespace=namespace,
            body=KubernetesUtils.hpa_json_manifest(
                name=name,
                api_version=api_version,
                target_ref_name=target_ref_name,
                **kwargs
            )
        )
        self.log.info(f"Created {api_version}/HorizontalPodAutoscaler [{name}] in namespace [{namespace}]")

    def get_custom_object(self, group, version, namespace, plural, name, **kwargs):
        """
        Returns a custom object JSON

            Args:
                group:              (str)   --  Name of group of CR

                version             (str)   --  Version of CR

                namespace           (str)   --  namespace of CRD

                plural              (str)   --  plural of CRD

                name                (str)   --  Name of CR

            Returns:

                A custom object

        """

        custom_object = self._custom_objects_api.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=name,
            **kwargs
        )
        self.log.info(f"Fetched CR object:[{custom_object}]")
        return custom_object

    def get_all_resources(self, namespace, label_selector=AutomationLabels.AUTOMATION_SELECTOR.value,
                          cluster_scoped=False, optional=False, return_json=False, timestamp=False):
        """Get all Kubernetes resources created by automation in namespace

            Args:

                namespace           (str)   --  Namespace to fetch resources

                label_selector      (str)   --  Label selector to use for fetch

                cluster_scoped      (bool)  --  To get cluster scoped resources

                optional            (bool)  --  To fetch optional resources from namespace

                return_json         (bool)  --  Return json of the resources instead of dict of names

                timestamp           (bool)  --  Return dict of resources along with their creation timestamps

            Return:

                resources           (dict)  -- List of all Kubernetes resources in a namespace created by automation.

        """
        self.log.info(f"Discovering all resources in namespace [{namespace}] with label [{label_selector}]")
        resources = dict()
        manifest = dict()

        # Get all Pods
        resources['Pod'] = []
        manifest['Pod'] = self._core_v1_api.list_namespaced_pod(namespace, label_selector=label_selector).items
        if timestamp:
            for pod in manifest['Pod']:
                if pod.metadata.generate_name and pod.metadata.owner_references[0].kind != "StatefulSet":
                    pod_name = pod.metadata.generate_name.rsplit('-', 2)[0]
                else:
                    pod_name = pod.metadata.name
                creation_timestamp_seconds = int(pod.metadata.creation_timestamp.timestamp())
                resources['Pod'].append({'name': pod_name, 'creation_timestamp_seconds': creation_timestamp_seconds})

        else:
            for pod in manifest['Pod']:
                if pod.metadata.generate_name and pod.metadata.owner_references[0].kind != "StatefulSet":
                    resources['Pod'].append(pod.metadata.generate_name.rsplit('-', 2)[0])

                else:
                    resources['Pod'].append(pod.metadata.name)

        # Get all Services
        resources['Service'] = []
        manifest['Service'] = self._core_v1_api.list_namespaced_service(namespace, label_selector=label_selector).items
        for service in manifest['Service']:
            if timestamp:
                creation_timestamp_seconds = int(service.metadata.creation_timestamp.timestamp())
                resources['Service'].append(
                    {'name': service.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
            else:
                resources['Service'].append(service.metadata.name)

        # Get all Secrets
        resources['Secret'] = []
        manifest['Secret'] = self._core_v1_api.list_namespaced_secret(namespace, label_selector=label_selector).items
        for secret in manifest['Secret']:

            # MR :: 362840
            if secret.type != "kubernetes.io/service-account-token":
                if timestamp:
                    creation_timestamp_seconds = int(secret.metadata.creation_timestamp.timestamp())
                    resources['Secret'].append(
                        {'name': secret.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
                else:
                    resources['Secret'].append(secret.metadata.name)

        # Get all ConfigMaps
        resources['ConfigMap'] = []
        manifest['ConfigMap'] = self._core_v1_api.list_namespaced_config_map(
            namespace, label_selector=label_selector).items
        for config in manifest['ConfigMap']:
            if timestamp:
                creation_timestamp_seconds = int(config.metadata.creation_timestamp.timestamp())
                resources['ConfigMap'].append(
                    {'name': config.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
            else:
                resources['ConfigMap'].append(config.metadata.name)

        # Get all PVC
        resources['PersistentVolumeClaim'] = []
        manifest['PersistentVolumeClaim'] = self._core_v1_api.list_namespaced_persistent_volume_claim(
            namespace, label_selector=label_selector).items
        for pvc in manifest['PersistentVolumeClaim']:
            if timestamp:
                creation_timestamp_seconds = int(pvc.metadata.creation_timestamp.timestamp())
                resources['PersistentVolumeClaim'].append(
                    {'name': pvc.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
            else:
                resources['PersistentVolumeClaim'].append(pvc.metadata.name)

        # Get all DaemonSet
        resources['DaemonSet'] = []
        manifest['DaemonSet'] = self._apps_v1_api.list_namespaced_daemon_set(
            namespace, label_selector=label_selector).items
        for ds in manifest['DaemonSet']:
            if timestamp:
                creation_timestamp_seconds = int(ds.metadata.creation_timestamp.timestamp())
                resources['DaemonSet'].append(
                    {'name': ds.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
            else:
                resources['DaemonSet'].append(ds.metadata.name)

        # Get all Deployment
        resources['Deployment'] = []
        manifest['Deployment'] = self._apps_v1_api.list_namespaced_deployment(
            namespace, label_selector=label_selector).items
        for deploy in manifest['Deployment']:
            if timestamp:
                creation_timestamp_seconds = int(deploy.metadata.creation_timestamp.timestamp())
                resources['Deployment'].append(
                    {'name': deploy.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
            else:
                resources['Deployment'].append(deploy.metadata.name)

        # Get all StatefulSet
        resources['StatefulSet'] = []
        manifest['StatefulSet'] = self._apps_v1_api.list_namespaced_stateful_set(
            namespace, label_selector=label_selector).items
        for ss in manifest['StatefulSet']:
            if timestamp:
                creation_timestamp_seconds = int(ss.metadata.creation_timestamp.timestamp())
                resources['StatefulSet'].append(
                    {'name': ss.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
            else:
                resources['StatefulSet'].append(ss.metadata.name)

        resources['ServiceAccount'] = []
        manifest['ServiceAccount'] = self._core_v1_api.list_namespaced_service_account(
            namespace, label_selector=label_selector).items
        for sa in manifest['ServiceAccount']:
            if timestamp:
                creation_timestamp_seconds = int(sa.metadata.creation_timestamp.timestamp())
                resources['ServiceAccount'].append(
                    {'name': sa.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
            else:
                resources['ServiceAccount'].append(sa.metadata.name)

        resources['NetworkPolicy'] = []
        manifest['NetworkPolicy'] = self._networking_v1_api.list_namespaced_network_policy(
            namespace, label_selector=label_selector).items
        for np in manifest['NetworkPolicy']:
            if timestamp:
                creation_timestamp_seconds = int(np.metadata.creation_timestamp.timestamp())
                resources['NetworkPolicy'].append(
                    {'name': np.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
            else:
                resources['NetworkPolicy'].append(np.metadata.name)

        resources['Ingress'] = []
        manifest['Ingress'] = self._networking_v1_api.list_namespaced_ingress(
            namespace, label_selector=label_selector).items
        for ing in manifest['Ingress']:
            if timestamp:
                creation_timestamp_seconds = int(ing.metadata.creation_timestamp.timestamp())
                resources['Ingress'].append(
                    {'name': ing.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
            else:
                resources['Ingress'].append(ing.metadata.name)

        resources['ResourceQuota'] = []
        manifest['ResourceQuota'] = self._core_v1_api.list_namespaced_resource_quota(
            namespace, label_selector=label_selector).items
        for rq in manifest['ResourceQuota']:
            if timestamp:
                creation_timestamp_seconds = int(rq.metadata.creation_timestamp.timestamp())
                resources['ResourceQuota'].append(
                    {'name': rq.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
            else:
                resources['ResourceQuota'].append(rq.metadata.name)

        resources['LimitRange'] = []
        manifest['LimitRange'] = self._core_v1_api.list_namespaced_limit_range(
            namespace, label_selector=label_selector).items
        for lr in manifest['LimitRange']:
            if timestamp:
                creation_timestamp_seconds = int(lr.metadata.creation_timestamp.timestamp())
                resources['LimitRange'].append(
                    {'name': lr.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
            else:
                resources['LimitRange'].append(lr.metadata.name)

        if optional:
            resources['PodDisruptionBudget'] = []
            manifest['PodDisruptionBudget'] = self._policy_v1_api.list_namespaced_pod_disruption_budget(
                namespace, label_selector=label_selector).items

            for pdb in manifest['PodDisruptionBudget']:
                if timestamp:
                    creation_timestamp_seconds = int(pdb.metadata.creation_timestamp.timestamp())
                    resources['PodDisruptionBudget'].append(
                        {'name': pdb.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
                else:
                    resources['PodDisruptionBudget'].append(pdb.metadata.name)

            resources['HorizontalPodAutoscaler'] = []
            manifest['HorizontalPodAutoscaler'] = self._autoscaling_v1_api.list_namespaced_horizontal_pod_autoscaler(
                namespace, label_selector=label_selector).items
            for v1_hpa in manifest['HorizontalPodAutoscaler']:
                if timestamp:
                    creation_timestamp_seconds = int(v1_hpa.metadata.creation_timestamp.timestamp())
                    resources['HorizontalPodAutoscaler'].append(
                        {'name': v1_hpa.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
                else:
                    resources['HorizontalPodAutoscaler'].append(v1_hpa.metadata.name)

        if cluster_scoped:
            resources['ClusterRoleBinding'] = []
            manifest['ClusterRoleBinding'] = self._rbac_auth_v1_api.list_cluster_role_binding(
                label_selector=label_selector).items
            for crb in manifest['ClusterRoleBinding']:
                if timestamp:
                    creation_timestamp_seconds = int(crb.metadata.creation_timestamp.timestamp())
                    resources['ClusterRoleBinding'].append(
                        {'name': crb.metadata.name, 'creation_timestamp_seconds': creation_timestamp_seconds})
                else:
                    resources['ClusterRoleBinding'].append(crb.metadata.name)

        self.log.info(f'Resources Fetched : {resources}')

        if not return_json:
            return resources
        else:
            return manifest

    def fetch_manifest_files(self, application_name):
        """
        Fetch the manifest files using browse

        Args:

            application_name        (str)   Application to browse

        """
        app_list, app_id_dict = self.subclient.browse()
        app_id = app_id_dict['\\' + application_name]['snap_display_name']

        disk_list, disk_info_dict = self.subclient.disk_level_browse("\\" + app_id)
        manifest_list = list(filter(lambda name: name.split('.')[-1] == "yaml", disk_list))
        manifest_list = [manifest.split('\\')[-1] for manifest in manifest_list]

        return manifest_list

    def get_namespace_pods(self, namespace, label_selector=AutomationLabels.AUTOMATION_SELECTOR.value):
        """Get all Pods in namespace

            Args:

                namespace           (str)   --  Namespace to create PVC in

                label_selector      (str)   --  Label selector to select specific Pods

            Return:

                pod_list            (str)   -- List of all pods.

        """
        pods_list = []
        pod_list = self._core_v1_api.list_namespaced_pod(namespace, label_selector=label_selector)
        for pod in pod_list.items:
            pods_list.append(pod.metadata.name)
        return pods_list

    def get_namespace_pvcs(self, namespace, label_selector=AutomationLabels.AUTOMATION_SELECTOR.value):
        """
        Function to get list of pvcs on mentioned namespace.

        Args:

            namespace           (str):  kubernetes namespace

            label_selector      (str):  Label selector to select specific PVC

        Returns:

            pvcs_list           (list): List of pvc

        """
        pvcs_list = []
        pvc_list = self._core_v1_api.list_namespaced_persistent_volume_claim(namespace, label_selector=label_selector)
        for pvc in pvc_list.items:
            pvcs_list.append(pvc.metadata.name)
        return pvcs_list

    def create_pod_dir(self, pod_name, namespace, location='/mnt/data', foldername=None, **kwargs):
        """create directory in pod.

            Args:

                pod_name            (str)   --  Name of pod

                namespace           (str)   --  Namespace

                location            (str)   --  Location for mountpoint

                foldername           (int)   --  Name of the folder

        """

        random_string = get_random_string()
        if foldername is None:
            foldername = random_string

        command_str = f'mkdir -p {location}/{foldername}'
        self.execute_command_in_pod(
            command=command_str,
            pod=pod_name,
            namespace=namespace,
            **kwargs
        )
        self.log.info(f"Created folder [{location}/{foldername}]")

    def get_files_checksum(self, namespace, location='/mnt/data', print_checksum=True, **kwargs):
        """Calculate the checksum of files in location for each pod in the namespace

            Args:

                namespace           (str)   --  Namespace for exec

                location            (str)   --  Location to calculate the checksum on

                print_checksum      (bool)  --  Print the checksum dictionary if set to true

            Returns:

                files_checksum          (dict)  --  Dictionary with hashsum value for files in folder for all pods

            Raise:

                KubernetesException       --  if operation fails

        """

        container = kwargs.get("container", None)

        files_checksum = {}
        self.log.info(f"Fetching all the pods in the namespace [{namespace}]")

        pod_list = self._core_v1_api.list_namespaced_pod(namespace).items
        for pods in pod_list:

            # Skip CV Pods
            if AutomationLabels.CV_POD_LABEL.value in pods.metadata.labels:
                continue

            pod_name = pods.metadata.name
            pod_generate_name = pods.metadata.generate_name

            exec_command = f'find {location} -xtype f -exec md5sum' + ' {} +'

            if print_checksum:
                self.log.info(f"Executing command [{exec_command}] in pod [{pod_name}] in namespace [{namespace}]")

            resp = exec_stream(
                self._core_v1_api.connect_get_namespaced_pod_exec, pod_name,
                namespace,
                container=container,
                command=['/bin/sh', '-c', exec_command],
                stderr=True,
                stdin=False, stdout=True, tty=False
            )
            original_files_hash = {}
            for line in resp.strip().split('\n'):
                if line:
                    output = line.split(None, 1)
                    original_files_hash[output[1]] = output[0]

            if print_checksum:
                self.log.info(f"Files Hash in Pod [{namespace}][{pods.metadata.name}] : [{original_files_hash}]")

            owner_reference = pods.metadata.owner_references
            if owner_reference and (owner_reference[0].kind == 'ReplicaSet'):
                files_checksum[pod_generate_name.rsplit('-', 2)[0]] = original_files_hash
            else:
                files_checksum[pod_name] = original_files_hash

        return files_checksum

    def run_restore_validate(self, client_name, storage_type=None,
                             mount_point='/mnt/data', inplace=False, validate=True, overwrite=True, **kwargs):
        """Run restore job with optional checksum validation

            Args:

                client_name         (str)   --  Client name

                storage_type        (str)   --  Storage class for target resources

                mount_point         (str)   --  Mount point of PVC

                inplace             (bool)  --  If restore to run is inplace

                validate            (bool)  --  To enable/disable checksum validation

                overwrite           (bool)  --  To enable/disable unconditional overwrite

            Raises:

                KubernetesException       --  if operation fails

        """

        pod_container = kwargs.get('container', None)
        restore_namespace = kwargs.get('restore_namespace', self.testcase.restore_namespace if self.testcase else None)
        source_namespace = kwargs.get('source_namespace', self.testcase.namespace if self.testcase else None)

        if inplace:
            restore_namespace = source_namespace

        if not inplace and not restore_namespace:
            raise KubernetesException(
                "RestoreOperations", "101", "Out-of-place restore selected but restore namespace not provided"
            )

        if validate and (not restore_namespace or not source_namespace):
            raise KubernetesException(
                "RestoreOperations", "101", "Source namespace or restore namespace is not provided for validation"
            )

        self.log.info(f"Validate option is set to : {validate}")
        original_files_hash = {}
        if validate:
            self.log.info("Calculating checksum for files in original pods")
            original_files_hash = self.get_files_checksum(source_namespace, mount_point, container=pod_container)

        if inplace:
            self.log.info("Run in-place restore job...")
            self.restore_in_place(overwrite=overwrite)
            self.log.info("Waiting till all pods are in running state...")
            namespace_list = [restore_namespace]
            self.wait_till_resources_are_running(namespace_list)
        else:
            self.log.info("Run out-of-place restore job...")
            self.restore_out_of_place(client_name, restore_namespace, storage_type, overwrite=overwrite)

        if validate:
            KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.LOOKUP_WAIT, trials=1)
            self.log.info("Calculating checksum for files in restored pods")
            restored_files_hash = self.get_files_checksum(restore_namespace, mount_point, container=pod_container)

            # Validate the two dictionaries
            self.log.info("Comparing checksum for restored pods and original pods")
            self.verify_checksum_dictionary(original_files_hash, restored_files_hash)

    def check_for_sc_snapshot_class(self, storage_class_name):
        """Checks if a snapshot class exists for a given storageclass

            Args:

                storage_class_name  (str)  --  Name of storage class
        """

        # Get given storageclass object
        sc_obj_list = self.get_all_storage_class_from_cluster(name_only=False)
        sc_obj = {}
        for obj in sc_obj_list:
            if obj.metadata.name == storage_class_name:
                sc_obj = obj
        if sc_obj == {}:
            raise KubernetesException(
                'APIClientOperations',
                '101',
                f'StorageClass with name {storage_class_name} not found'
            )
        vol_snap_list = self.get_cluster_volume_snapshot_classes()

        if len(vol_snap_list) == 0:
            self.log.info("No volumesnapshot class found")
            return None
        for obj in vol_snap_list:
            if obj['driver'] == sc_obj.provisioner:
                self.log.info(
                    f"Found associated VolumeSnapshotClass [{obj['metadata']['name']}"
                    f" for StorageClass [{sc_obj.metadata.name}]. Provisioner [{sc_obj.provisioner}]"
                )
                return obj['metadata']['name']
        else:
            self.log.info("No Matching snap class found")
            return None

    def verify_checksum_dictionary(self, original_files_hash, restored_files_hash):
        """Compare dictionaries with the md5 checksum of files

            Args:

                original_files_hash     (dict)   --  Dictionary with file hash of original pods

                restored_files_hash     (dict)   --  Dictionary with file hash of restored pods

            Raises:

                  KubernetesException     --  if checksum verification fails

        """

        errors_messages = []

        for pod in original_files_hash.keys():

            original_pod = original_files_hash[pod]
            restore_pod = restored_files_hash[pod]

            # Filtering out prehook and posthook files
            original_pod = {k: v for k, v in original_pod.items() if ('prehook' not in k) and ('posthook' not in k)}
            restore_pod = {k: v for k, v in restore_pod.items() if ('prehook' not in k) and ('posthook' not in k)}

            self.log.info(f"Comparing dictionaries for pod [{pod}]...")
            if len(original_pod) != len(restore_pod):
                errors_messages.append(
                    "Restored file count not equal to original file count for pod {}. Original {} Restored {}".format(
                        pod, len(original_pod), len(restore_pod)
                    )
                )
                continue

            for key in original_pod.keys():
                if original_pod[key] != restore_pod[key]:
                    errors_messages.append(f"File Hash of {key} is different. :: "
                                           f"Original Hash : {original_pod[key]} :: "
                                           f"Restored Hash : {restore_pod[key]}")
            else:
                self.log.info(f"Comparison of md5 checksum of [{len(original_pod)}] files in pod [{pod}] complete.")

        if errors_messages:
            for msg in errors_messages:
                self.log.error(msg)
            else:
                raise KubernetesException("ValidationOperations", "103", "Checksum dictionary verification failed")
        self.log.info("Checksum dictionary verification successful.")

    def get_namespace_custom_resources(self, namespace, group, plural, **kwargs):
        """Get namespaced custom resource

            Args:

                namespace       (str)            -- Namespace to get custom resource

                group           (str)            -- The API group of the custom resource

                plural          (str)            -- The plurals verb of the custom resource

            Kwargs:

                version         (str)            -- API version of the custom resource

            Returns:

                resource_list   (list)           -- Lists of with custom resources in the namespace

        """

        version = kwargs.get("version", "v1")
        resource_list = []
        try:
            resources = self._custom_objects_api.list_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural
            )

            for item in resources["items"]:
                resource_list.append(item["metadata"]["name"])

        except K8sApiException as e:
            self.log.error(f"Resource fetch for {version} {plural} returned exception : {e.body.strip()}")
        finally:
            return resource_list

    def get_cluster_custom_resources(self, group, plural, name_only=True, **kwargs):
        """
        Gets Cluster scoped custom objects
        """
        version = kwargs.get("version", "v1")
        resource_list = []
        resource_list_obj = []
        try:
            resources = self._custom_objects_api.list_cluster_custom_object(
                group=group,
                version=version,
                plural=plural
            )
            resource_list_obj = resources['items']

            for item in resources["items"]:
                resource_list.append(item["metadata"]["name"])

        except K8sApiException as e:
            self.log.error(f"Resource fetch for {version} {plural} returned exception : {e.body.strip()}")
        finally:
            if name_only:
                return resource_list
            else:
                return resource_list_obj

    def get_cluster_volume_snapshot_classes(self):
        """Get VolumeSnapshotClasses on the cluster"""

        return self.get_cluster_custom_resources(
            group=VolumeSnapshotClasses.GROUP.value,
            plural=VolumeSnapshotClasses.PLURAL.value,
            name_only=False
        )

    def get_namespace_volume_snapshots(self, namespace, version="v1"):
        """Get namespaced volumesnapshots of specified version

            Args:

                namespace       (str)            -- Namespace to get volumesnapshots

                version         (str)            -- Version of the volumesnapshot

            Return:

                resource_list   (list)           -- List of volumesnapshots in the namespace

        """
        group = "snapshot.storage.k8s.io"
        plural = "volumesnapshots"

        return self.get_namespace_custom_resources(
            namespace, group=group, plural=plural, version=version
        )

    def validate_cv_resource_cleanup(self, namespace, backup_jobid=None, restore_jobid=None):
        """validate if cleanup happened in the namespace after backup/restore

            Args:

                namespace       (str)       --      Namespace to search

                backup_jobid    (str)       --      To validate cleanup after backup

                restore_jobid   (str)       --      To validate cleanup after restore

            Raises:

                KubernetesException       -- If stray resources are not cleaned up

        """

        if backup_jobid:
            self.log.info("Validating stray resources after backup...")
            for version in ["v1", "v1beta1"]:

                for vs in self.get_namespace_volume_snapshots(namespace, version=version):
                    if vs.split('-')[-1] == backup_jobid:
                        raise KubernetesException(
                            "ValidationOperations", "105", f"{version} VolumeSnapshot {vs} is not cleaned up"
                        )
                else:
                    self.log.info(f"No stray {version} volumesnapshots exist.")

            for pod in self.get_namespace_pods(namespace, label_selector=AutomationLabels.CV_POD_SELECTOR.value):
                if pod.split('-')[-1] == backup_jobid:
                    raise KubernetesException(
                        "ValidationOperations", "105", f"Pod {pod} is not cleaned up"
                    )
            else:
                self.log.info(f"No stray Pods exist.")

            for pvc in self.get_namespace_pvcs(namespace, label_selector=AutomationLabels.CV_POD_SELECTOR.value):
                if pvc.split('-')[-1] == backup_jobid:
                    raise KubernetesException(
                        "ValidationOperations", "105", f"PVC {pvc} is not cleaned up"
                    )
            else:
                self.log.info(f"No stray PVCs exist.")

        if restore_jobid:
            self.log.info("Validating stray resources after restore...")
            for pod in self.get_namespace_pods(namespace, label_selector=AutomationLabels.CV_POD_SELECTOR.value):
                if AutomationLabels.CV_POD_LABEL.value in \
                        self._core_v1_api.read_namespaced_pod(pod, namespace).metadata.labels:
                    raise KubernetesException(
                        "ValidationOperations", "105", f"Pod {pod} is not cleaned up"
                    )
            else:
                self.log.info(f"No stray Pods exist.")

    def deploy_helm_apps(self, helm_app_name, namespace, **kwargs):
        """Deploying Helm chard apps in namespace.

            Args:

                helm_app_name       (str)            -- Name of the helm app

                namespace            (str)           -- Namespace to create the helm app

        """

        repo_path = kwargs.get("repo_path", "https://charts.bitnami.com/bitnami")
        repo_name = kwargs.get("repo_name", os.path.basename(repo_path))
        kubeconfig_path = kwargs.get("kubeconfig_path", _KUBERNETES_CONFIG.KUBECONFIG_FILE)
        _helm_helper = HelmHelper(
            kubeconfig=kubeconfig_path,
            repo_path=repo_path,
            repo_name=repo_name
        )

        self.log.info(f"Cleaning up if previous helm chart [{helm_app_name}] is present in namespace [{namespace}]")
        _helm_helper.cleanup_helm_app(helm_app_name=helm_app_name, namespace=namespace)
        self.log.info("Setting up Helm Repository")
        _helm_helper.add_helm_repo()
        self.log.info(f"Deploying helm chart [{helm_app_name}] in namespace [{namespace}]")
        _helm_helper.deploy_helm_app(helm_app_name=helm_app_name, namespace=namespace, **kwargs)
        self.log.info(f"Successfully deployed helm chart [{helm_app_name}] in namespace [{namespace}]")

    def compare_with_helm_list(self, backup_namespace, restore_namespace, kubeconfig_path):
        """Comparing Helm apps in source namespace + destination namespace with helm list command.

                    Args:

                        backup_namespace      (str)            -- Source Namespace

                        restore_namespace     (str)           -- Destination Namespace

                        kubeconfig_path       (str)           -- Path to kubeconfig file

        """
        _helm_helper = HelmHelper(kubeconfig=kubeconfig_path)
        bkp_cmd = f"helm list -n {backup_namespace}"
        rst_cmd = f"helm list -n {restore_namespace}"
        bkp_list = _helm_helper.execute_helm_command_and_collect(bkp_cmd)
        rst_list = _helm_helper.execute_helm_command_and_collect(rst_cmd)
        bkp_and_rst = bkp_list + rst_list
        helm_list = _helm_helper.execute_helm_command_and_collect('helm list -A')

        bkp_and_rst = set(bkp_and_rst)
        helm_list = set(helm_list)

        self.log.info(f"Resources in Backup and Restore destination : {bkp_and_rst}")
        self.log.info(f"Output of helm list -A command : {helm_list}")
        if bkp_and_rst.issubset(helm_list):
            self.log.info("Resouce Validation Successfull! Resources in backup and restore namespaces are present "
                          "in resources obtained using /'helm list -A/' command")
            return True

        else:
            raise KubernetesException(
                "RestoreOperations", "999",
                f"Resources in helm list is not same as resources in backup and restore namespaces "
                f"does not match\n Helm List : {helm_list}\n Backup and Restore namespace : {bkp_and_rst}"
            )

    @DebugSkip()
    def cleanup_helm_apps(self, helm_app_name, namespace, **kwargs):
        """Deleting/ Removing  Helm chart apps in namespace.

            Args:

                helm_app_name         (str)          -- Name of helm application

                namespace              (str)         -- Namespace to uninstall the helm app

        """

        kubeconfig_path = kwargs.get("kubeconfig_path", _KUBERNETES_CONFIG.KUBECONFIG_FILE)
        _helm_helper = HelmHelper(kubeconfig=kubeconfig_path)

        self.log.info(f"Cleanup Helm chart [{helm_app_name}] from namespace [{namespace}]")
        _helm_helper.cleanup_helm_app(helm_app_name=helm_app_name, namespace=namespace)
        self.log.info(f"Successfully cleaned up helm chart [{helm_app_name}] in namespace [{namespace}]")

    def get_default_storage_class_from_cluster(self):
        """
        Fetch the default storage class from cluster. If default is not present, fetch the first storage class in list

        Return:

            Name of storage class

        """
        sc_list = self._storage_v1_api.list_storage_class().items
        for obj in sc_list:
            if (obj.metadata.annotations
                    and obj.metadata.annotations.get('storageclass.kubernetes.io/is-default-class') == "true"):
                sc = obj.metadata.name
                break
        else:
            sc = sc_list[0].metadata.name

        self.log.info(f"Default storage class of the cluster : [{sc}]")
        return sc

    def get_all_storage_class_from_cluster(self, name_only=True):
        """
        Fetch all Storage classes from cluster

        Return:

                Storage Class List : List(str)
        """

        sc_list_obj = self._storage_v1_api.list_storage_class().items
        sc_list = []
        for obj in sc_list_obj:
            sc_list.append(obj.metadata.name)

        if name_only:
            self.log.info(f"Storage Class List: [{sc_list}]")
            return sc_list
        else:
            return sc_list_obj

    def list_pod_content(self, pod_name, namespace, location, **kwargs):
        """list folder content in pod

            Args:

                pod_name            (str)   --  Name of pod

                namespace           (str)   --  Namespace

                location            (str)   --  path to list.

            Return:

                list_of_items       (list)  -- List of items in location provided

        """
        container = kwargs.get("container", None)

        command_str = 'ls {}'.format(location)
        str_of_items = exec_stream(
            self._core_v1_api.connect_get_namespaced_pod_exec, pod_name,
            namespace,
            container=container,
            command=['/bin/sh', '-c', command_str],
            stderr=True,
            stdin=False, stdout=True, tty=False
        )

        KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.LOOKUP_WAIT, trials=1)
        list_of_items = str_of_items.splitlines()
        return list_of_items

    def get_pod_file_content(self, pod_name, namespace, file_path, **kwargs):
        """Gets the contents of a file inside a pod

            Args:

                pod_name            (str)   --  Name of pod

                namespace           (str)   --  Namespace

                file_path            (str)  --  The file path

            Return:

                file_content       (str)  -- Contents of the file

        """
        container = kwargs.get("container", None)

        command_str = 'cat {}'.format(file_path)
        file_content = exec_stream(
            self._core_v1_api.connect_get_namespaced_pod_exec, pod_name,
            namespace,
            container=container,
            command=['/bin/sh', '-c', command_str],
            stderr=True,
            stdin=False, stdout=True, tty=False
        )

        KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.LOOKUP_WAIT, trials=1)
        return file_content

    def manifest_restore(self, application_name, access_node, destination_path="/tmp", **kwargs):
        """Run manifest restore job to the VSA proxy

            Args:

                application_name        (str)   --  Name of the application for which manifest to be browsed

                access_node             (str)   --  Destination access node to restore to

                destination_path        (str)   --  Destination path on access node to restore to

            Kwargs:

                manifest_list           (list)  --  List of manifest files to restore (optional)

            Raise:

                KubernetesException - if job fails

        """

        extn = ".yaml"
        manifest_list = kwargs.get("manifest_list", None)
        disk_name = None

        if not manifest_list:
            app_list, app_id_dict = self.subclient.browse()
            app_id = app_id_dict['\\' + application_name]['snap_display_name']

            # fetching all disks from the vm
            disk_list, disk_info_dict = self.subclient.disk_level_browse("\\" + app_id)

            manifest_list = list(map(
                lambda name: '\\' + name.split("\\")[-1],
                list(filter(lambda name: name.split('.')[-1] == extn, disk_list)))
            )

        else:
            manifest_list = list(map(
                lambda f_name: f_name if f_name.startswith('\\') else '\\' + f_name, manifest_list
            ))
            disk_name = manifest_list

        self.log.info(f"Manifest files to restore : {manifest_list}")

        self.log.info("Starting manifest restore job...")
        job = self.subclient.disk_restore(
            application_name=application_name,
            proxy_client=access_node,
            destination_path=destination_path,
            disk_name=disk_name,
            **kwargs
        )

        self.log.info(f"Manifest restore job started with job id : [{job.job_id}]")

        if not job.wait_for_completion(timeout=60, return_timeout=90):
            raise KubernetesException(
                "RestoreOperations", "105",
                f"Failed to run Manifest restore Job [{job.job_id}] with error: {job.delay_reason}"
            )

        if not job.status.lower() == "completed":
            raise KubernetesException(
                "RestoreOperations", "105",
                f"Job status is not Completed, Job [{job.job_id}] has status: {job.status}"
            )

        self.log.info(f"Successfully finished Manifest restore job to destination : [{access_node}]")

        self.log.info("Verifying all backed up manifests are restored...")

        proxy_obj = Machine(self.commcell.clients.get(access_node))
        for file in manifest_list:
            file_path = proxy_obj.join_path(destination_path, file.split('\\')[-1]).replace('`', "\\`")
            if proxy_obj.check_file_exists(file_path):
                self.log.info(f"Manifest [{file}] restored at destination path [{destination_path}]")
            else:
                raise KubernetesException(
                    "RestoreOperations", "105",
                    f"Manifest file [{file}] is not restored at destination [{destination_path}]"
                )

        self.log.info("Verified all manifests has been restored")

    def fs_dest_restore(self,
                        application_name,
                        restore_list,
                        source_namespace,
                        pvc_name,
                        access_node,
                        destination_path="/tmp/k8s-auto",
                        **kwargs):
        """Run fs destination restore job to the VSA proxy

            Args:

                application_name        (str)   --  Name of the application for which manifest to be browsed

                access_node             (str)   --  Destination access node to restore to

                destination_path        (str)   --  Destination path on access node to restore to

                restore_list            (list)  --  List of file or folder to restore relative to PVC mount point

                source_namespace        (str)   --  Namespace of the source PVC

                pvc_name                (str)   --  PVC to restore from

            Raise:

                KubernetesException - if job does not succeed

        """

        self.log.info(f"Files and Folders to restore : [{restore_list}] from source PVC [{pvc_name}]")
        self.log.info(
            f"Starting File System Destination restore job to target [{access_node}] at [{destination_path}]"
        )

        self.log.info(f"Fetching checksum of original files from source PVC " +
                      f"[{source_namespace}/{pvc_name}]")
        source_checksum = self.get_files_checksum(
            namespace=source_namespace, print_checksum=False
        )

        # Keep only source application
        source_checksum = {
            application_name: source_checksum[application_name]
        }

        # Filter out checksum of only those files and folders required
        source_checksum[application_name] = {
            key: value for key, value in source_checksum[application_name].items() if any(
                folder_path in key for folder_path in restore_list
            )
        }
        self.log.info(f"Source Checksum :: [{source_checksum}]")

        job = self.subclient.guest_file_restore(
            application_name=application_name,
            proxy_client=access_node,
            destination_path=destination_path,
            disk_name=pvc_name,
            restore_list=restore_list,
            volume_level_restore=7,  # 7 denotes FS Destination restore
            **kwargs
        )

        self.log.info(f"File System Destination restore job started with job id : [{job.job_id}]")

        if not job.wait_for_completion(timeout=60, return_timeout=90):
            raise KubernetesException(
                "RestoreOperations", "103",
                f"Failed to run FS Destination restore Job [{job.job_id}] with error: {job.delay_reason}"
            )

        if not job.status.lower() == "completed":
            KubernetesException(
                "RestoreOperations", "103",
                f"Job status is not Completed, Job [{job.job_id}] has status: {job.status}"
            )

        self.log.info(f"Successfully finished FS Destination restore job to destination : [{access_node}]")
        proxy_obj = Machine(self.commcell.clients.get(access_node))

        self.log.info("Validating files restored using checksum comparison")
        exec_command = f'find {destination_path} -xtype f -exec md5sum' + ' {} +'
        output = proxy_obj.execute_command(exec_command)

        # Output if is of the format "checksum full_file_path"
        formatted_output = output.formatted_output \
            if type(output.formatted_output) is list else [output.formatted_output.split()]

        pvc_mount_point = "/mnt/data"

        # Replacing restore destination path with pvc mount point path
        fs_checksum_dict = {
            item[1].replace(destination_path, pvc_mount_point): item[0] for item in formatted_output if any(
                folder_path in item[1] for folder_path in restore_list)
        }
        destination_checksum = {
            application_name: fs_checksum_dict
        }
        self.log.info(f"Destination Checksum :: [{destination_checksum}]")

        self.verify_checksum_dictionary(source_checksum, destination_checksum)
        self.log.info("Verified all files and folders has been restored")

    def restore_to_pvc(self,
                       application_name,
                       restore_list,
                       source_namespace,
                       source_pvc,
                       access_node,
                       destination_pvc=None,
                       destination_namespace=None,
                       in_place=False,
                       destination_path='/mnt/data',
                       **kwargs):
        """Run restore job to destination PVC

            Args:

                application_name        (str)   --  Name of the application for which manifest to be browsed

                access_node             (str)   --  Destination access node to restore to

                destination_path        (str)   --  Destination path on access node to restore to

                restore_list            (list)  --  List of file or folder to restore relative to PVC mount point

                source_namespace        (str)   --  Source Namespace of the PVC

                source_pvc              (str)   --  PVC to restore from

                destination_pvc         (str)   --  PVC to restore to

                destination_namespace   (str)   --  Namespace of the destination PVC

                in_place                (bool)  --  If inplace job

            Kwargs:

                Options to pass for disk level restore

                validate_checksum       (bool) -- If checksum validation is needed

            Raise:

                KubernetesException - if job fails

        """

        validate_checksum = kwargs.get('validate_checksum', True)
        pod_container = kwargs.get('pod_container', None)
        source_checksum = {}
        destination_checksum = {}

        self.log.info(
            f"Files and Folders to restore : [{restore_list}]"
        )
        self.log.info(
            f"Starting Restore to PVC restore job to destination PVC " +
            (
                f"[{source_pvc}] in-place" if in_place
                else f"[{destination_pvc}] in namespace [{destination_namespace}]"
            )
        )

        pvc_str_guid = ""
        if not in_place:

            # Fetch the strGUID of the destination PVC from cluster content browse
            get_vols = self.backupset.application_groups.browse(
                browse_type="Volumes", namespace=destination_namespace
            )
            for vols in get_vols:
                if vols['name'] == destination_pvc:
                    pvc_str_guid = vols['strGUID']
                    break
            else:
                raise KubernetesException(
                    "RestoreOperations", "104",
                    f"Destination PVC [{destination_pvc}] does not exist in namespace [{destination_namespace}]"
                )
        else:
            destination_pvc = source_pvc
            destination_namespace = source_namespace

        if validate_checksum:
            self.log.info(f"Fetching checksum of original files from source PVC " +
                          f"[{source_namespace}/{source_pvc}]")
            source_checksum = self.get_files_checksum(
                namespace=source_namespace, print_checksum=False, container=pod_container
            )

            # Keep only source application
            source_checksum = {
                application_name: source_checksum[application_name]
            }

            # Filter out checksum of only those files and folders required
            source_checksum[application_name] = {
                key: value for key, value in source_checksum[application_name].items() if any(
                    folder_path in key for folder_path in restore_list
                )
            }
            self.log.info(f"Source Checksum :: [{source_checksum}]")
            source_checksum = source_checksum

        # Initiate Data restore to PVC job
        job = self.subclient.guest_file_restore(
            application_name=application_name,
            proxy_client=access_node,
            destination_path=destination_path,
            restore_pvc_guid=pvc_str_guid,
            disk_name=source_pvc,
            restore_list=restore_list,
            volume_level_restore=6,  # 6 denotes Restore to PVC
            in_place=in_place,
            **kwargs
        )

        self.log.info(f"Restore to PVC {'IN-PLACE ' if in_place else ''}started with job id : [{job.job_id}]")

        if not job.wait_for_completion(timeout=60, return_timeout=90):
            raise KubernetesException(
                "RestoreOperations", "104",
                f"Failed to restore to PVC {'IN-PLACE ' if in_place else ''}Job [{job.job_id}] "
                f"with error: {job.delay_reason}"
            )

        if not job.status.lower() == "completed":
            raise KubernetesException(
                "RestoreOperations", "104",
                f"Job status is not Completed, Job [{job.job_id}] has status: [{job.status}]"
            )

        self.log.info(
            f"Successfully finished Restore to PVC restore job to destination PVC " +
            (
                f"[{source_pvc}] in-place" if in_place
                else f"[{destination_pvc}] in namespace [{destination_namespace}]"
            )
        )

        if validate_checksum:
            self.log.info(f"Fetching checksum of restored files from destination PVC " +
                          f"[{destination_namespace}/{destination_pvc}]")
            destination_checksum = self.get_files_checksum(
                namespace=destination_namespace, print_checksum=False, container=pod_container
            )

            # Keep only destination application
            destination_checksum = {
                application_name: destination_checksum[application_name]
            }

            # Filter out checksum of only those required
            destination_path = '/' if destination_path == '/mnt/data' else destination_path
            destination_checksum[application_name] = {
                key.replace(destination_path + '/', '/'): value for key, value in
                destination_checksum[application_name].items() if any(
                    folder_path in key for folder_path in restore_list
                )
            }
            self.log.info(f"Destination Checksum :: [{destination_checksum}]")
            destination_checksum = destination_checksum

        if validate_checksum:
            # Comparing checksum of source and destination files and folders
            self.verify_checksum_dictionary(source_checksum, destination_checksum)

    def execute_command_in_pod(self, command, pod, namespace, container=None, **kwargs):
        """Execute command inside container of Pod in namespace

            Args:

                pod             (str)       --  Name of the Pod

                namespace       (str)       --  Namespace Pod is in

                command         (str)       --  Command to execute

                container       (str)       --  Container inside the Pod

            Kwargs:

                stderr          (bool)      --  stderr to pass to exec_stream

                stdin           (bool)      --  stdin to pass to exec_stream

                stdout          (bool)      --  stdout to pass to exec_stream

                tty             (bool)      --  tty to pass to exec_stream

                preload_content (bool)      --  _preload_content to pass to exec_stream

            Returns:

                True    -   if execution succeeds

                False   -   if execution fails

        """

        stderr = kwargs.get('stderr', True)
        stdin = kwargs.get('stdin', False)
        stdout = kwargs.get('stdout', True)
        tty = kwargs.get('tty', False)
        preload_content = kwargs.get('preload_content', False)
        wait_time = kwargs.get('wait_time', 15)

        self.log.info(f"Executing command [{command}] in Pod [{pod}] in namespace [{namespace}]")
        resp = exec_stream(
            self._core_v1_api.connect_get_namespaced_pod_exec,
            pod,
            namespace=namespace,
            container=container,
            command=["/bin/bash", "-c", command],
            stderr=stderr,
            stdin=stdin,
            stdout=stdout,
            tty=tty,
            _preload_content=preload_content
        )

        if not preload_content:
            while resp.is_open():
                err_code = resp.read_stderr()
                if err_code:
                    raise KubernetesException("APIClientOperations", "102", f"Execution failed with error: {err_code}")
            KubernetesUtils.implicit_wait(wait_time, trials=1)
            resp.close()
        else:
            KubernetesUtils.implicit_wait(wait_time, trials=1)
            if not stdout and stderr and resp:
                self.log.error(f"Execution failed with error: {resp}")
                return False
            if stdout:
                self.log.info(f"Execution returned stdout: {resp}")

        self.log.info("Execution completed successfully")
        return True

    def create_cv_custom_resource(self, namespace, group, version, plural, body):
        """Create a custom resource in the namespace

            Args:

                namespace       (str)       --  Namespace to create Custom resource

                group           (str)       --  Group of custom resource

                version         (str)       --  API version of custom resource

                plural          (str)       --  Plurals for the custom resource

                body            (dict)      --  JSON dict of the custom resource body

        """
        self._custom_objects_api.create_namespaced_custom_object(
            namespace=namespace, body=body, group=group, version=version, plural=plural
        )
        self.log.info(f"Created [{plural}.{group}] object in namespace [{namespace}]")
        KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.APPLICATION_WAIT)

    def delete_cv_crd(self, group, plural):
        """Delete a Custom Resource Definition (CRD) along with its instances.

        Args:
            group (str): Group of the CRD.
            plural (str): Plurals for the CRD.

        """
        crd_name = f"{plural}.{group}"
        try:
            self._api_extensions_v1_api.read_custom_resource_definition(crd_name)
            self.log.info(f"Custom Resource Definition with name {crd_name} exists, proceeding to delete.")
            try:
                self._api_extensions_v1_api.delete_custom_resource_definition(crd_name)
                self.log.info(f"Custom Resource Definition with name {crd_name} deleted successfully")
            except K8sApiException as delete_error:
                self.log.error(f"Error deleting CRD with name {crd_name}: {delete_error.body.strip()}")
                raise
        except K8sApiException as read_error:
            if read_error.status == 404:
                self.log.info(f"Custom Resource Definition with name {crd_name} does not exist.")
            else:
                self.log.error(f"Error checking existence of CRD with name {crd_name}: {read_error.body.strip()}")
                raise

    def delete_cv_custom_resource(self, namespace, name, group, version, plural):
        """Create a custom resource in the namespace

            Args:

                namespace       (str)       --  Namespace to create Custom resource

                name            (str)       --  Name of the CR to delete

                group           (str)       --  Group of custom resource

                version         (str)       --  API version of custom resource

                plural          (str)       --  Plurals for the custom resource

        """
        self._custom_objects_api.delete_namespaced_custom_object(
            namespace=namespace, group=group, version=version, plural=plural, name=name
        )
        self.log.info(f"Deleted [{plural}.{group}] object [{name}] in namespace [{namespace}]")
        KubernetesUtils.implicit_wait(_KUBERNETES_CONFIG.APPLICATION_WAIT)

    def namespace_level_restore(self, client_name=None, access_node=None, in_place=False,
                                raise_exception=True, **kwargs):
        """
        Perform Namespace-level In-place or Out-of-place restore

        Args:

                client_name             (str)   :   Name of the destination cluster for restore

                access_node             (str)   :   Specify access Node to use for restore

                in_place                (bool)  :   To run in-place restore job

                raise_exception         (bool)  :   Raise exception if job has status other than 'Completed'.
                                                    Default: True

        Kwargs:

                restore_name_map        (dict)  :   Provide new name for namespaces
                                                    Eg. {'namespace1' : 'ns1-newname'}

                overwrite               (bool)  :   provide unconditional overwrite option

                namespace_list          (list)  :   List of namespaces to restore
                                                    If specified, only the namespaces in the list will be restored
                                                    Else, all namespaces backed up by the app group will be restored

                storage_class_map       (dict)  :   Mapping of storage classes for transformation
                                                    Eg. {'rook-ceph-block' : 'azurefile'}

        Exception:
                        if job fails

                        if validation fails

        """

        restore_type = "IN-PLACE" if in_place else "OUT-OF-PLACE"
        restore_name_map = kwargs.get("restore_name_map", {})
        overwrite = kwargs.get("overwrite", True)
        namespace_list = kwargs.get('namespace_list', [])
        storage_class_map = kwargs.get('storage_class_map', None)
        app_list, app_dict = self.subclient.browse()
        if in_place:
            destination_namespaces = namespace_list
        else:
            destination_namespaces = list(restore_name_map.values())

        source_paths = []
        target_namespace_map = {}

        # If namespace list is passed, then restore that,
        # else, restore all namespaces backed up by subclient
        for app, app_metadata in app_dict.items():
            app_guid = app_metadata['snap_display_name']
            app_type = app_guid.split('`')[1]
            app_name = app_metadata['name']

            if namespace_list and app_name not in namespace_list:
                continue
            if app_type == 'Namespace':
                source_paths.append(app_name)

        self.log.info(f"Namespaces to restore : {source_paths}")
        self.log.info(f"Restore type selected : [{restore_type}]")
        self.log.info(f"Overwrite option : [{overwrite}]")
        for source_path in source_paths:
            target_namespace_map[source_path] = source_path
            if source_path in restore_name_map:
                target_namespace_map[source_path] = restore_name_map[source_path]

        if in_place:
            job = self.subclient.namespace_restore_in_place(
                namespace_to_restore=namespace_list,
                overwrite=overwrite,
                proxy_client=access_node
            )
        else:
            job = self.subclient.namespace_restore_out_of_place(
                namespace_to_restore=source_paths,
                target_namespace_name=target_namespace_map,
                target_cluster_name=client_name,
                storage_class_map=storage_class_map,
                overwrite=overwrite,
                proxy_client=access_node
            )
        self.log.info(f"Started {restore_type} NAMESPACE RESTORE job with job id: {job.job_id}")
        if not job.wait_for_completion(timeout=60, return_timeout=90):
            exception_msg = f"Failed to run {restore_type} NAMESPACE RESTORE Job [{job.job_id}] " \
                            f"with error: [{job.delay_reason}]"
            if raise_exception:
                raise KubernetesException("RestoreOperations", "102", exception_msg)
            self.log.warning(exception_msg)

        if not job.status.lower() == "completed":
            exception_msg = f"Job status is not Completed, Job [{job.job_id}] has status: [{job.status}]"
            if raise_exception:
                raise KubernetesException("RestoreOperations", "102", exception_msg)
            self.log.warning(exception_msg)

        self.log.info(f"Successfully finished {restore_type} NAMESPACE RESTORE job")
        self.log.info("Waiting till all pods are in running state...")
        self.wait_till_resources_are_running(destination_namespaces)
        return job

    def worker_pod_debug_wait(self, access_nodes, worker_create=True, worker_delete=True, cleanup=False):
        """Create or delete debug wait files in access node

            Args:

                access_nodes        (list/str)      --  List of access node(s) client objects
                                                        to create/delete debug wait files in

                worker_create       (bool)          --  To create/delete worker created debug wait file

                worker_delete       (bool)          --  To create/delete worker deleting debug wait file

                cleanup             (bool)          --  To clean-up debug files instead of create

        """

        def create_or_delete_file(delete=False):
            if not delete:
                current_time = time.ctime(time.time())
                machine_obj.create_file(
                    file_path=file_path,
                    content=current_time
                )
            else:
                machine_obj.delete_file(file_path=file_path)
            self.log.info(f"{'Deleted' if delete else 'Created'} file [{file_path}] on [{machine_obj.machine_name}]")

        files_list = []
        if worker_create:
            files_list.append(DebugFiles.WORKER_POD_CREATE)
        if worker_delete:
            files_list.append(DebugFiles.WORKER_POD_DELETE)

        access_nodes = list(access_nodes) if type(access_nodes) is str else access_nodes
        for access_node in access_nodes:
            machine_obj = Machine(access_node)
            for file_path in files_list:
                if cleanup and machine_obj.check_file_exists(file_path=file_path):
                    create_or_delete_file(delete=True)
                if not cleanup:
                    create_or_delete_file()

    def get_child_job_error_reason(self, job, print_log=False):
        """Get the error reason for child jobs of a Kubernetes Backup/Restore job

            Args:

                job         (object)    --  Job object for the parent job

                print_log   (bool)      --  To print dict before returning

            Returns:

                Dictionary of error reasons with Application name as key

        """

        child_jobs = job.get_child_jobs()
        error_reasons = {job_dict['vmName']: job_dict['FailureReason'] for job_dict in child_jobs} if child_jobs else {}
        if print_log:
            self.log.info(f"Error Reason Dictionary: [{error_reasons}]")
        return error_reasons

    def validate_child_job_jpr(self, job, jpr_dict):
        """Validate the JPR of the child jobs for each application in input

            Args:

                job         (object)    --  Job object for the parent job

                jpr_dict    (dict)      --  Dictionary of JPRs with Application name as key

            Raises:

                Exception if JPR of child jobs do not match the input

        """

        child_job_jprs = self.get_child_job_error_reason(job=job, print_log=True)
        applications_processed = list(child_job_jprs.keys())

        jpr_dict = {app: jpr_dict[app] if app in jpr_dict else "" for app in applications_processed}

        for key in jpr_dict:
            if jpr_dict[key] not in child_job_jprs[key]:
                raise KubernetesException(
                    "ValidationOperations", "106",
                    f"JPR Validation failed. Expected : [{jpr_dict}] Received : [{child_job_jprs}]"
                )
        self.log.info(f"JPR Validation successful for applications : [{applications_processed}]")

    def match_logs_for_pattern(self, client_obj, job_id, log_file_name, pattern, expected_keyword=None):
        """Get logs for a particular pattern from log file for a particular job and validate expected keyword exists

            Args:

                client_obj      (object)    --  Client object for client to check logs in

                job_id          (str)       --  Job ID to filter logs

                log_file_name   (str)       --  Log file to check logs in

                pattern         (str)       --  Pattern to check logs

                expected_keyword(str)       --  Expected keyword

            Returns:

                Log lines with matching pattern and keyword

        """

        machine_obj = Machine(client_obj)
        matched_log_lines = machine_obj.get_logs_for_job_from_file(
            job_id=job_id,
            log_file_name=log_file_name,
            search_term=pattern
        ).strip()
        self.log.info(f"Matched log lines: [{matched_log_lines}]")

        if not matched_log_lines:
            raise KubernetesException(
                "ValidationOperations", "107", f"No log lines returned for pattern [{pattern}]"
            )

        for line in matched_log_lines.split("\r\n"):
            if expected_keyword and expected_keyword not in line:
                raise KubernetesException(
                    "ValidationOperations", "107", f"Expected keyword [{expected_keyword}] not found in log line {line}"
                )

        return matched_log_lines

    def wait_till_resources_are_running(self, namespace_list, timeout=200):
        """Verifies if all pods are in running state or not repeatedly until timeout period

                    Args:

                        namespace_list     (list)  --  namespace(s) in which resources must be checked

                        timeout            (int)          --  timeout period in seconds

                    Returns:

                        Exception if any pods are not in running state even after the timeout period
        """

        self.log.info("Validating if all pods are in running state")
        # Start the timer
        self.log.info(f"Timeout set for {timeout} seconds")
        start_time = time.time()

        # Check if namespace_list is empty
        if not namespace_list:
            raise ValueError("namespace must not be an empty string or list.")

        while True:
            all_running = True
            not_running_pods = []

            for ns in namespace_list:
                self.log.info(f"Checking pods in namespace: {ns}")
                pods = self._core_v1_api.list_namespaced_pod(namespace=ns).items

                for pod in pods:
                    pod_status = pod.status.phase
                    if pod_status not in ['Running', 'Succeeded']:
                        all_running = False
                        not_running_pods.append((pod.metadata.name, pod_status, ns))

            if all_running:
                self.log.info("All pods are in running State")
                return

            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout:
                for pod_name, pod_status, ns in not_running_pods:
                    print(f"Pod {pod_name} in namespace {ns} is in {pod_status} state.")
                raise KubernetesException(
                    "ValidationOperations", "111",
                    f"Timeout of {timeout} seconds reached. Some pods are still not in running state"
                )
            time.sleep(5)

    def verify_node_selector(self, namespace, stop_event):
        """Verifies if resources are assigned desired node selector during restore

                            Args:

                                namespace          (str)       --  namespace in which resources must be checked

                                stop_event         (Event)     --  a threading event used to stop poling the resources


                            Returns:

                                Exception if resources do not have the desired node selector

        """
        verified_sts = ""
        verified_deploy = ""

        while not stop_event.is_set():

            # Gather Deployments
            deployments = self._apps_v1_api.list_namespaced_deployment(namespace)
            for deploy in deployments.items:
                verified_deploy = verified_deploy + f"{deploy.metadata.name}:{deploy.spec.template.spec.node_selector} "

            # Gather StatefulSets
            statefulsets = self._apps_v1_api.list_namespaced_stateful_set(namespace)
            for sts in statefulsets.items:
                verified_sts = verified_sts + f"{sts.metadata.name}:{sts.spec.template.spec.node_selector}"

            time.sleep(5)

        # List all the deployments present in the namespace
        total_resources = 0
        verified_resources = 0
        deployments = self._apps_v1_api.list_namespaced_deployment(namespace)
        for deploy in deployments.items:
            total_resources = total_resources+1
            search_string = f"{deploy.metadata.name}:{{'cv-restore': 'progress'}}"
            if search_string in verified_deploy:
                verified_resources = verified_resources+1
                self.log.info(f"Deployment '{deploy.metadata.name}' has the desired node selector.")
            else:
                self.log.info(f"Deployment '{deploy.metadata.name}' does NOT have the desired node selector.")

        # List all the statefulsets present in the namespace
        statefulsets = self._apps_v1_api.list_namespaced_stateful_set(namespace)
        for sts in statefulsets.items:
            total_resources = total_resources+1
            search_string = f"{sts.metadata.name}:{{'cv-restore': 'progress'}}"
            if search_string in verified_sts:
                verified_resources = verified_resources+1
                self.log.info(f"StatefulSet '{sts.metadata.name}' has the desired node selector.")
            else:
                self.log.info(f"StatefulSet '{sts.metadata.name}' does NOT have the desired node selector.")

        if verified_resources >= total_resources-1:
            self.log.info("DEPENDENT APPLICATION RESTORE HAS BEEN COMPLETED CORRECTLY")
        else:
            raise KubernetesException(
                "ValidationOperations", "112",
                f"Resources did not have {'cv-restore': 'progress'} as their node selector"
            )

