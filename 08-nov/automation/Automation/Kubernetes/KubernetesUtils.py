# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that provides utility functions for Kubernetes

Methods defined:

    add_cluster()                           --  Add a new Kubernetes client

    delete_cluster()                        --  Delete an existing Kubernetes client

    populate_default_objects()              --  Populate default objects of the testcase

    add_application_group()                 --  Add a new application group to a Kubernetes client

    clusterrolebinding_json_manifest()      --  Returns the json for clusterrolebinding body

    configmap_json_manifest()               --  Returns the json for configmap body

    deployment_json_manifest()              --  Returns the json for deployment body

    namespace_json_manifest()               --  Returns the json for namespace body

    pod_ubuntu_json_manifest()              --  Returns the json for pod body

    pvc_json_manifest()                     --  Returns the json for pvc body

    secret_json_manifest()                  --  Returns the json for secret body

    service_json_manifest()                 --  Returns the json for service body

    serviceaccount_json_manifest()          --  Returns the json for service account body

    statefulset_json_manifest()             --  Returns the json for statefulset body

"""
import base64
from time import sleep
from typing import Any

from cvpysdk.exception import SDKException

from AutomationUtils import logger
from AutomationUtils.config import get_config
from Kubernetes.constants import AutomationLabels
from Kubernetes.decorators import DebugSkip
from VirtualServer.VSAUtils.VirtualServerUtils import encode_base64


@DebugSkip()
def delete_application_group(testcase_obj, application_group_name):
    """Delete the Kubernetes application group

            Args:

                testcase_obj        (obj)       :   Testcase object

                application_group_name        (str)       :   Name of the Kubernetes cluster

        """
    log = logger.get_log()
    if testcase_obj.backupset.subclients.has_subclient(application_group_name):
        log.info(f"Application group with name [{application_group_name}] is present in backupset")
        testcase_obj.backupset.subclients.delete(application_group_name)
        sleep(10)
        testcase_obj.commcell.refresh()
        testcase_obj.backupset.subclients.refresh()
        if not testcase_obj.backupset.subclients.has_subclient(application_group_name):
            log.info(f"Application Group [{application_group_name}] deleted")
        else:
            raise Exception(f'Could not delete application group with name [{application_group_name}]')
    else:
        log.info(f"Application group with name [{application_group_name}] does not exist")


@DebugSkip()
def delete_cluster(testcase_obj, cluster_name):
    """Delete the Kubernetes cluster client

        Args:

            testcase_obj        (obj)       :   Testcase object

            cluster_name        (str)       :   Name of the Kubernetes cluster

    """

    def get_client_name(display_name):
        try:
            obj = testcase_obj.commcell.clients.get(display_name)
            return obj.client_name
        except SDKException:
            return ""

    log = logger.get_log()
    name = get_client_name(cluster_name) or cluster_name
    if testcase_obj.commcell.clients.has_client(name):
        log.info(f"Cluster with name [{name}] is present in CommCell")
        client_obj = testcase_obj.commcell.clients.get(name)
        client_obj.retire()
        testcase_obj.commcell.refresh()
        try:
            client_obj.refresh()
            name = get_client_name(cluster_name) or cluster_name
            testcase_obj.commcell.clients.delete(name)
            testcase_obj.commcell.refresh()

        except SDKException:
            log.info(f"Cluster [{name}] has been retired")

        if testcase_obj.commcell.clients.has_client(name):
            raise Exception(f"Could not delete cluster [{name}]")
        else:
            log.info(f"Cluster [{name}] has been retired and deleted")
            testcase_obj.commcell.refresh()
    else:
        log.info(f"Cluster [{name}] does not exist to delete")


def add_cluster(testcase_obj, cluster_name, api_server, service_account, service_token, access_node=None, **kwargs):
    """Add cluster client with given name and credentials

        Args:

            testcase_obj        (obj)       :   Testcase object

            cluster_name        (str)       :   Name of the cluster

            api_server          (str)       :   API Server endpoint of the cluster

            service_account     (str)       :   Service account to authenticate

            service_token       (str)       :   Service account token to authenticate

            access_node         (list/str)  :   VSA Proxy as member servers

        Kwargs:

            populate_client_obj (bool)      :   If set to true, populate the client and default objects in testcase.
                                                Default: True

    """

    populate_client_obj = kwargs.get('populate_client_obj', True)
    log = logger.get_log()
    log.info(f'Deleting cluster [{cluster_name}] if present')
    delete_cluster(testcase_obj, cluster_name)

    log.info(f'Creating cluster with name [{cluster_name}]')
    if access_node:
        log.info(f'Access nodes to use : [{access_node}]')
    else:
        log.info(f'No access nodes passed. Will be using automatic access node selection.')
    encoded_service_token = base64.b64encode(service_token.encode()).decode()
    testcase_obj.commcell.clients.add_kubernetes_client(
        cluster_name,
        api_server,
        service_account,
        service_token,
        encoded_service_token,
        access_node
    )
    sleep(10)
    testcase_obj.commcell.refresh()
    if testcase_obj.commcell.clients.has_client(cluster_name):
        log.info(f'Cluster created with name [{cluster_name}]')
        if populate_client_obj:
            log.info(f'Creating client object for client: [{cluster_name}]')
            testcase_obj._client = testcase_obj.commcell.clients.get(cluster_name)
            populate_default_objects(testcase_obj)
    else:
        raise Exception(f'Could not create cluster with name [{cluster_name}]')


def populate_default_objects(testcase_obj):
    """Populate default objects of testcase

        Args:

            testcase_obj        (obj)       :   Testcase object

    """

    log = logger.get_log()
    log.info(f"Creating agent object for agent: Virtual Server")
    testcase_obj._agent = testcase_obj.client.agents.get("Virtual Server")
    testcase_obj.commcell.refresh()
    log.info(f"Creating instance object for instance: Kubernetes")
    testcase_obj._instance = testcase_obj.agent.instances.get("Kubernetes")
    testcase_obj.commcell.refresh()
    log.info("Creating backupSet object for: defaultBackupSet")
    testcase_obj._backupset = testcase_obj.instance.backupsets.get("defaultBackupSet")
    testcase_obj.backupset.refresh()
    log.info("Creating subclient object for: default")
    testcase_obj._subclient = testcase_obj.backupset.subclients.get("default")
    testcase_obj.commcell.refresh()

def populate_client_objects(testcase_obj, client_name):
    """Populate client and default objects in testcase"""

    log = logger.get_log()
    log.info(f"Creating client object for client: [{client_name}]")
    testcase_obj.commcell.refresh()
    testcase_obj._client = testcase_obj.commcell.clients.get(client_name)
    populate_default_objects(testcase_obj)

def populate_subclient_objects(testcase_obj, application_group_name):
    """Populate subclient and backupset objects in testcase"""

    log = logger.get_log()
    log.info(f"Creating subclient object for application group: [{application_group_name}]")
    testcase_obj.backupset.refresh()
    testcase_obj._subclient = testcase_obj.backupset.subclients.get(application_group_name)
    testcase_obj.backupset.refresh()


def add_application_group(testcase_obj, name, content, plan=None, filters=None, **kwargs):
    """Add application group with given name and content

        Args:

            testcase_obj        (obj)       :   Testcase object

            name                (str)       :   Name of the application group

            content             (list)      :   Content for the application group

            plan                (str)       :   Name of the plan to use

            filters             (list)      :   Filter content for the application group

        Kwargs:

            populate_subclient_obj (bool)   :   If set to true, populate the subclient and backupset objects in testcase
                                                Default: True

    """
    populate_subclient_obj = kwargs.get('populate_subclient_obj', True)
    log = logger.get_log()
    testcase_obj.backupset.application_groups.create_application_group(
        content=content,
        plan_name=plan,
        subclient_name=name,
        filter=filters
    )
    sleep(10)
    testcase_obj.commcell.refresh()
    testcase_obj.backupset.subclients.refresh()
    if testcase_obj.backupset.subclients.has_subclient(name):
        log.info(f"Application Group created with name: [{name}]")
        if populate_subclient_obj:
            log.info(f"Creating subclient object for application group: [{name}]")
            testcase_obj.backupset.refresh()
            testcase_obj._subclient = testcase_obj.backupset.subclients.get(name)
            testcase_obj.backupset.refresh()
    else:
        raise Exception(f'Could not create application group with name [{name}]')


def namespace_json_manifest(name, **kwargs):
    """Return Namespace json

        Args:

            name        (str)       --  Name of namespace

        Kwargs:
            labels      (dict)      -- Dictionary of labels {key1: value1 , key2: value2}

    """
    labels = kwargs.get("labels", {})
    labels.update({AutomationLabels.AUTOMATION_LABEL.value: ''})

    return {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': name,
            'labels': labels
        }
    }


def configmap_json_manifest(name):
    """Return Configmap json

        Args:

            name                    (str)       -- Name of configmap

    """
    return {
        'apiVersion': 'v1',
        'kind': 'ConfigMap',
        'metadata': {
            'name': name,
            'labels': {
                AutomationLabels.AUTOMATION_LABEL.value: ''
            }
        },
        'data': {
            'testdata': 'dummy data'
        }
    }


def secret_json_manifest(name, **kwargs):
    """Return secret json

        Args:

            name                    (str)       -- Name of secret

    """

    labels = kwargs.get("labels", {})
    labels.update({AutomationLabels.AUTOMATION_LABEL.value: ''})
    secret_type = kwargs.get("secret_type", "Opaque")
    annotations = kwargs.get("annotations", None)

    response = {
        'apiVersion': 'v1',
        'kind': 'Secret',
        'metadata': {
            'name': name,
            'labels': labels
        },
        'type': secret_type,
        'data': {
            'testdata': encode_base64("some dummy data").decode("utf-8")
        }
    }

    if annotations:
        response['metadata'].update({
            'annotations': annotations
        })

    if secret_type == 'kubernetes.io/tls':
        response['data'].update({
            'tls.crt': encode_base64("some dummy data").decode("utf-8"),
            'tls.key': encode_base64("some dummy data").decode("utf-8")
        })

    return response


def service_json_manifest(name, **kwargs):
    """Return json manifest for service

        Args:

            name                (str)       -- Name of service

        Kwargs:

            selector            (dict)      -- Selectors for labels

            port                (int)       --  Port number for service

    """

    selector = kwargs.get("selector", None)
    port = kwargs.get("port", 80)

    if selector is None:
        selector = {
            'app': 'test'
        }

    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": name,
            "labels": {
                AutomationLabels.AUTOMATION_LABEL.value: ''
            }
        },
        "spec": {
            "type": "NodePort",
            "ports": [
                {
                    "port": port,
                    "targetPort": port,
                }
            ],
            "selector": selector
        }
    }


def pvc_json_manifest(name, storage="10Gi", accessmode="ReadWriteOnce", storage_class=None, **kwargs):
    """Return PVC json manifest

        Args:

            name                (str)   --  Name of pvc

            storage             (str)   --  Storage to provision

            accessmode          (str)   --  Access mode for PVC

            storage_class       (str)   --  Storage class for PVC

        Kwargs:
            labels              (dict)  --  Dictionary specifying labels

        Returns:

              JSON manifest of PVC

    """
    labels = kwargs.get("labels", {})
    labels.update({AutomationLabels.AUTOMATION_LABEL.value: ""})
    response = {
        'apiVersion': 'v1',
        'kind': 'PersistentVolumeClaim',
        'metadata': {
            'name': name,
            'labels': labels
        },
        'spec': {
            'accessModes': accessmode if type(accessmode) is list else [accessmode],
            'resources': {
                'requests': {
                    'storage': storage
                }
            }
        }
    }

    if storage_class is not None:
        response['spec']['storageClassName'] = storage_class

    volume_mode = kwargs.get('volume_mode', None)
    if volume_mode == "Block":
        response['spec']['volumeMode'] = "Block"

    return response


def pod_ubuntu_json_manifest(name, pvc_name=None, **kwargs):
    """Return Ubuntu Pod json manifest

        Args:

            name                (str)   --  Name of pod

            pvc_name            (str)   --  Name of pvc

        Kwargs:

            configmap           (str)   --  Name of configmap to mount

            secret              (str)   --  Name of secret to mount

            labels              (dict)  --  Dictionary specifying labels

            pvc_mount_path      (str)   --  Specify PVC mount path

        Returns:

              JSON manifest of Pod

    """

    labels = kwargs.get("labels", {})
    configmap = kwargs.get("configmap", None)
    secret = kwargs.get("secret", None)
    pvc_volume_mode = kwargs.get("pvc_volume_mode", None)
    priority_class = kwargs.get("priority_class", None)
    pvc_mount_path = kwargs.get("pvc_mount_path", "/mnt/data")
    resources = kwargs.get("resources", None)
    image_registry = get_config().Kubernetes.IMAGE_REGISTRY
    labels.update({AutomationLabels.AUTOMATION_LABEL.value: ''})

    manifest = {
        'apiVersion': 'v1',
        'kind': 'Pod',
        'metadata': {
            'name': name,
            'labels': labels
        },
        'spec': {
            'containers': [{
                'image': (image_registry + '/' if image_registry else '') + get_config().Kubernetes.IMAGE,
                'name': AutomationLabels.AUTOMATION_LABEL.value + '-container',
                'command': ["bin/sh", "-c"],
                'args': ["while true; do sleep 3600; done;"],
                "imagePullPolicy": "IfNotPresent",
                "livenessProbe": {
                    'exec': {
                        'command': ['ls', "/mnt/"]
                    }
                }
            }]
        }
    }

    if not get_config().Kubernetes.OPENSHIFT:
        manifest['spec']['containers'][0]['securityContext'] = {'runAsUser': 0}

    if resources:
        manifest['spec']['containers'][0]['resources'] = resources

    if pvc_name or configmap or secret:
        manifest['spec']['volumes'] = []
        manifest['spec']['containers'][0]['volumeMounts'] = []
        if pvc_volume_mode and pvc_volume_mode == "Block":
            manifest['spec']['containers'][0]['volumeDevices'] = []

        if pvc_name:
            manifest['spec']['volumes'].append(
                {
                    'name': name[:59] + '-vol',
                    'persistentVolumeClaim': {
                        'claimName': pvc_name
                    }
                }
            )

            if pvc_volume_mode and pvc_volume_mode == "Block":
                manifest['spec']['containers'][0]['volumeDevices'].append(
                    {
                        'name': name[:59] + '-vol',
                        'devicePath': '/dev/xdb'
                    }
                )
            else:
                manifest['spec']['containers'][0]['volumeMounts'].append(
                    {
                        'name': name[:59] + '-vol',
                        'mountPath': pvc_mount_path
                    }
                )

        if secret:
            manifest['spec']['volumes'].append(
                {
                    'name': name[:56] + '-secret',
                    'secret': {
                        'secretName': secret
                    }
                }
            )

            manifest['spec']['containers'][0]['volumeMounts'].append(
                {
                    'name': name[:56] + '-secret',
                    'mountPath': '/mnt/secret'
                }
            )

        if configmap:
            manifest['spec']['volumes'].append(
                {
                    'name': name[:59] + '-cm',
                    'configMap': {
                        'name': configmap
                    }
                }
            )

            manifest['spec']['containers'][0]['volumeMounts'].append(
                {
                    'name': name[:59] + '-cm',
                    'mountPath': '/mnt/cm'
                }
            )

        if priority_class:
            manifest['spec'].update({'priorityClassName': priority_class})

    return manifest


def role_binding_json_manifest(name, namespace, ref_kind, ref_name, sa_name, sa_namespace):
    """Create role binding in namespace

            Args:

                name                (str)  --  Name of Role

                namespace           (str)  --  Namespace to create rolebinding in

                ref_kind            (str)  -- Role or ClusterRole

                ref_name            (str)  -- Name of Role/ClusterRole

                sa_name             (str)  -- Name of associated Service Account

                sa_namespace        (str)  -- Namespace of associated Service Account

            Returns:

                JSON Manifest of Role Binding

    """

    return {
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'RoleBinding',
        'metadata': {
            'name': name,
            'namespace': namespace,
            'labels': {
                AutomationLabels.AUTOMATION_LABEL.value: ''
            }
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': ref_kind,
            'name': ref_name
        },
        'subjects': [
            {
                'kind': 'ServiceAccount',
                'name': sa_name,
                'namespace': sa_namespace
            }
        ]
    }


def cluster_role_json_manifest(name):
    """Create cluster role

            Args:

                name                (str)  --  Name of Role

            Returns:
                JSON Manifest of Cluster Role

        """
    return {
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'ClusterRole',
        'metadata': {
            'name': name,
            'labels': {
                AutomationLabels.AUTOMATION_LABEL.value: ''
            }
        },
        'rules': [
            {
                'apiGroups': [""],
                'resources': ["secrets"],
                'verbs': ["get", "watch", "list"]
            }
        ]
    }


def role_json_manifest(name, namespace):
    """Create role in namespace

        Args:

            name                (str)  --  Name of Role

            namespace           (str)  -- Namespace of Role

        Returns:
            JSON Manifest of Role

    """
    return {
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'Role',
        'metadata': {
            'namespace': namespace,
            'name': name,
            'labels': {
                AutomationLabels.AUTOMATION_LABEL.value: ''
            }
        },
        'rules': [
            {
                'apiGroups': [""],
                'resources': ["pods"],
                'verbs': ["get", "watch", "list"]
            }
        ]
    }


def clusterrolebinding_json_manifest(name, sa_namespace, sa_name, cluster_role_name):
    """Create service account

        Args:

            name                (str)   --  Name of clusterrolebinding

            sa_name             (str)   --  name of service account

            sa_namespace        (str)   --  service account namespace

            cluster_role_name   (str)   --  name of the cluster role

        Returns:

              JSON manifest of clusterrolebinding

    """
    return {
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'ClusterRoleBinding',
        'metadata': {
            'name': name,
            'labels': {
                AutomationLabels.AUTOMATION_LABEL.value: ''
            }
        },
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': 'ClusterRole',
            'name': cluster_role_name
        },
        'subjects': [
            {
                'kind': 'ServiceAccount',
                'name': sa_name,
                'namespace': sa_namespace
            }
        ]
    }


def serviceaccount_json_manifest(namespace, name=None):
    """Return manifest for serviceaccount

        Args:

            namespace   (str)   --  Namespace for serviceaccount

            name        (str)  --  Name of service account

        Returns:

            JSON manifest of serviceaccount
    """
    return {
        'apiVersion': 'v1',
        'kind': 'ServiceAccount',
        'metadata': {
            'name': name or (namespace + '-sa'),
            'labels': {
                AutomationLabels.AUTOMATION_LABEL.value: ''
            }
        },
        'automountServiceAccountToken': False
    }


def deployment_json_manifest(name, **kwargs):
    """
    Function to deployment yaml

    Args:

        name          (str): Deployment name

    Kwargs:

        pvcname             (str)   :   pvc name

        image_pull_secret   (str)   :   image pull secret

        env_secret          (str)   :   Name of env secret to use

        env_configmap       (str)   :   Name of the environment secret to use

        projected_secret    (str)   :   Name of the secret to use as projected volume

        projected_configmap (str)   :   Name of the configmap to use as projected volume

        init_containers     (bool)  :   Specify whether to use init containers in Pods

        resources           (bool)  :   Specify whether to use resource limits on Deployment

        replicas            (int)   :   Number of replicas for Deployment

        labels              (dict)  :   Dictionary of labels to use as selectors for Deployment

        service_account     (str):   Name of service account

    Raises:

            Exception:

                if it fails to create namespace

    """

    pvcname = kwargs.get("pvcname", None)
    env_secret = kwargs.get("env_secret", None)
    env_configmap = kwargs.get("env_configmap", None)
    projected_secret = kwargs.get("projected_secret", None)
    projected_configmap = kwargs.get("projected_configmap", None)
    init_containers = kwargs.get("init_containers", False)
    resources = kwargs.get("resources", False)
    replicas = kwargs.get("replicas", 1)
    labels = kwargs.get("labels", None)
    service_account = kwargs.get("service_account", None)
    image_pull_secret = kwargs.get("image_pull_secret", None)
    image_registry = get_config().Kubernetes.IMAGE_REGISTRY

    volumes: list[Any] = []
    volume_mounts: list[Any] = []
    container: dict[Any] = {
        "env": [],
        "volumeMounts": [],
        "name": AutomationLabels.AUTOMATION_LABEL.value + '-container',
        "image": (image_registry + '/' if image_registry else '') + "nginxinc/nginx-unprivileged",
        "ports": [
            {
                "containerPort": 8080,
                "name": "nginx-port"
            }
        ],
        "imagePullPolicy": "IfNotPresent",
        "livenessProbe": {
            "tcpSocket": {
                "port": "nginx-port"
            }
        },
        "readinessProbe": {
            "httpGet": {
                "path": "/index.html",
                "port": 8080
            }
        }
    }
    env: list[Any] = [{
        "name": "MY_NAME",
        "value": "Automation"
    }]

    volume_mounts.append(
        {
            "name": "projected",
            "mountPath": "/projected",
            "readOnly": True
        }
    )

    volumes.append(
        {
            "name": "projected",
            "projected": {
                "sources": [{
                    "downwardAPI": {
                        "items": [
                            {
                                "path": "labels",
                                "fieldRef": {
                                    "fieldPath": "metadata.labels"
                                }
                            },
                            {
                                "path": "cpu_limit",
                                "resourceFieldRef": {
                                    "containerName": AutomationLabels.AUTOMATION_LABEL.value + '-container',
                                    "resource": "limits.cpu"
                                }
                            }]
                    }
                }]
            }
        }
    )

    template_spec: dict[Any] = {
        'spec':
            {
                "hostAliases": [{
                    "ip": "127.0.0.1",
                    "hostnames": [
                        "automation.local",
                        "automations.local"
                    ]
                }]
            }
    }

    template_deployment_json: dict[Any] = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "labels": {
                AutomationLabels.AUTOMATION_LABEL.value: '',
                "app": "test"
            }
        },
        "spec": {
            "selector": {
                "matchLabels": {
                    "app": "test",
                    AutomationLabels.AUTOMATION_LABEL.value: ''
                }
            },
            "strategy": {
                "type": "RollingUpdate",
                "rollingUpdate": {
                    "maxSurge": "30%",
                    "maxUnavailable": "30%"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "test",
                        AutomationLabels.AUTOMATION_LABEL.value: ''
                    }
                }
            }
        }
    }

    if labels:
        template_deployment_json['metadata']['labels'].update(labels)
        template_deployment_json['spec']['template']['metadata']['labels'].update(labels)

    if resources:
        resource_template: dict[Any] = {
            'resources': {
                'limits': {
                    'memory': kwargs.get('limits_memory', '200Mi'),
                    'cpu': kwargs.get('limits_cpu', '200m')
                },
                'requests': {
                    'memory': kwargs.get('requests_memory', '100Mi'),
                    'cpu': kwargs.get('requests_cpu', '100m')
                }
            }
        }
        container.update(resource_template)

    if init_containers:
        init_cont_template: dict[Any] = {
            'initContainers': [{
                'command': ['ls', '/tmp'],
                'name': AutomationLabels.AUTOMATION_LABEL.value + '-init-container',
                'image': (image_registry + '/' if image_registry else '') + 'busybox'
            }]
        }
        template_spec['spec'].update(init_cont_template)

    if env_secret:
        env.append({
            "name": "MY_SECRET",
            "valueFrom": {
                "secretKeyRef": {
                    "name": env_secret,
                    "key": "testdata"
                }
            }
        })

    if env_configmap:
        env.append({
            "name": "MY_CONFIGMAP",
            "valueFrom": {
                "configMapKeyRef": {
                    "name": env_configmap,
                    "key": "testdata"
                }
            }
        })

    if pvcname:
        pvc_template: dict[Any] = {
            'name': 'data',
            'persistentVolumeClaim': {
                'claimName': pvcname
            }
        }
        volumes.append(pvc_template)

        pvc_mount: dict[Any] = {
            'name': 'data',
            'mountPath': '/mnt/data'
        }
        volume_mounts.append(pvc_mount)

    if projected_secret:
        secret_template: dict[Any] = {
            'name': 'projected-secret',
            'projected': {
                "sources": [
                    {
                        "secret": {
                            "name": projected_secret,
                            "items": [
                                {
                                    "key": "testdata",
                                    "path": "projected-secret"
                                }]
                        }
                    }]
            }
        }
        volumes.append(secret_template)

        secret_mount: dict[Any] = {
            'name': 'projected-secret',
            'mountPath': '/projected-secret'
        }
        volume_mounts.append(secret_mount)

    if projected_configmap:
        cm_template: dict[Any] = {
            'name': 'projected-configmap',
            'projected': {
                "sources": [
                    {
                        "configMap": {
                            "name": projected_configmap,
                            "items": [
                                {
                                    "key": "testdata",
                                    "path": "projected-configmap"
                                }]
                        }
                    }]
            }
        }
        volumes.append(cm_template)

        cm_mount: dict[Any] = {
            'name': 'projected-configmap',
            'mountPath': '/projected-configmap'
        }
        volume_mounts.append(cm_mount)

    if replicas:
        template_deployment_json['spec'].update(
            {
                'replicas': replicas
            }
        )

    if image_pull_secret:
        template_spec['spec'].update(
            {
                'imagePullSecrets': [
                    {
                        'name': image_pull_secret
                    }
                ]
            }
        )

    container.update({
        'env': env,
        'volumeMounts': volume_mounts
    })

    if not get_config().Kubernetes.OPENSHIFT:
        container.update({
            'securityContext': {
                'runAsUser': 0
            }
        })

    template_spec['spec'].update({
        'volumes': volumes
    })
    template_spec['spec'].update({
        'containers': [container]
    })
    if service_account:
        template_spec['spec'].update({
            'serviceAccountName': service_account
        })
    template_deployment_json['spec']['template'].update(template_spec)

    return template_deployment_json


def statefulset_json_manifest(name, access_mode="ReadWriteOnce", **kwargs):
    """
    Function to deployment yaml

    Args:

        name          (str): StatefulSet name

        access_mode   (str): Access Mode of application

    Kwargs**

        labels        (dict): dictionary containing labels

    """
    labels = kwargs.get("labels", {})
    image_registry = get_config().Kubernetes.IMAGE_REGISTRY
    labels.update({AutomationLabels.AUTOMATION_LABEL.value: ''})
    template_sts_json = {
        "apiVersion": "apps/v1",
        "kind": "StatefulSet",
        "metadata": {
            "name": name,
            "labels": labels
        },
        "spec": {
            "replicas": 3,
            "selector": {
                "matchLabels": labels
            },
            "template": {
                "metadata": {
                    "labels": labels
                },
                "spec": {
                    "containers": [
                        {
                            "name": AutomationLabels.AUTOMATION_LABEL.value + '-container',
                            "image": (image_registry + '/' if image_registry else '') + get_config().Kubernetes.IMAGE,
                            'command': ["bin/sh", "-c"],
                            'args': ["while true; do sleep 3600; done;"],
                            "ports": [
                                {
                                    "containerPort": 80,
                                    "name": "sts"
                                }
                            ],
                            "volumeMounts": [
                                {
                                    "name": "sts-vol",
                                    "mountPath": "/mnt/data"
                                }
                            ],
                            "imagePullPolicy": "IfNotPresent"
                        }
                    ]
                }
            },
            "volumeClaimTemplates": [
                {
                    "metadata": {
                        "name": "sts-vol",
                        AutomationLabels.AUTOMATION_LABEL.value: ''
                    },
                    "spec": {
                        "accessModes": [access_mode],
                        "resources": {
                            "requests": {
                                "storage": "10Gi"
                            }
                        }
                    }
                }
            ]
        }
    }

    if not get_config().Kubernetes.OPENSHIFT:
        template_sts_json['spec']['template']['spec']['containers'][0]['securityContext'] = {'runAsUser': 0}

    return template_sts_json


def pdb_json_manifest(name, match_labels, **kwargs):
    """Return json manifest for Pod Disruption Budget

        Args:

            name                (str)   --  Name of PDB

            match_labels        (dict)  --  Dictionary of labels for Pod Selector

        Returns:

              JSON manifest of PDB

    """
    labels = kwargs.get('labels', {})
    min_available = kwargs.get('minAvailable', 1)
    labels.update({AutomationLabels.AUTOMATION_LABEL.value: ''})

    response = {
        'apiVersion': 'policy/v1',
        'kind': 'PodDisruptionBudget',
        'metadata': {
            'name': name,
            'labels': labels
        },
        'spec': {
            'minAvailable': min_available,
            'selector': {
                'matchLabels': match_labels
            }
        }
    }

    return response


def hpa_json_manifest(name, api_version, target_ref_name, **kwargs):
    """Return json manifest for Horizontal Pod Autoscaler

        Args:

            name                (str)   --  Name of HPA

            api_version         (str)   --  API Version of autoscaling

            target_ref_name     (str)   --  Name of the target resource for HPA

        Kwargs:

            labels                      (dict)  --  Dictionary of labels

            target_ref_api_version      (str)   --  String for the target reference apiVersion

            target_ref_kind             (str)   --  The Kind for the target reference

        Returns:

              JSON manifest of HPA

    """
    target_ref_api_version = kwargs.get('target_ref_api_version', 'apps/v1')
    target_ref_kind = kwargs.get('target_ref_kind', 'Deployment')
    labels = kwargs.get('labels', {})
    labels.update({AutomationLabels.AUTOMATION_LABEL.value: ''})

    response = {
        'apiVersion': f'autoscaling/{api_version}',
        'kind': 'HorizontalPodAutoscaler',
        'metadata': {
            'name': name,
            'labels': labels
        },
        'spec': {
            'scaleTargetRef': {
                'apiVersion': target_ref_api_version,
                'kind': target_ref_kind,
                'name': target_ref_name
            },
            'minReplicas': 1,
            'maxReplicas': 10,
            'targetCPUUtilizationPercentage': 50
        }
    }

    return response


def network_policy_json_manifest(name, match_labels, **kwargs):
    """Return json manifest for Network Policy

        Args:

            name            (str)   --  Name of the network policy

            match_labels    (dict)  --  Dictionary of labels for Pod Selector

        Kwargs:

            labels                      (dict)  --  Dictionary of labels

    """
    labels = kwargs.get('labels', {})
    labels.update({AutomationLabels.AUTOMATION_LABEL.value: ''})

    response = {
        'apiVersion': 'networking.k8s.io/v1',
        'kind': 'NetworkPolicy',
        'metadata': {
            'name': name,
            'labels': labels
        },
        'spec': {
            'podSelector': {
                'matchLabels': match_labels
            },
            'ingress': [{
                'from': [{
                    'podSelector': {
                        'matchLabels': match_labels
                    }
                }]
            }]
        }
    }

    return response


def ingress_json_manifest(name, service_name, **kwargs):
    """Return json manifest for Ingress

        Args:

            name            (str)   --  Name of the network policy

            service_name    (str)   --  Name of the service for Ingress

        Kwargs:

            labels                      (dict)  --  Dictionary of labels

            tls_secret                 (str)   --  TLS Secret Name

    """
    labels = kwargs.get('labels', {})
    tls_secret = kwargs.get('tls_secret', None)
    labels.update({AutomationLabels.AUTOMATION_LABEL.value: ''})

    response = {
        'apiVersion': 'networking.k8s.io/v1',
        'kind': 'Ingress',
        'metadata': {
            'name': name,
            'labels': labels
        },
        'spec': {
            'rules': [{
                'http': {
                    'paths': [{
                        'path': '/testpath',
                        'pathType': 'Prefix',
                        'backend': {
                            'service': {
                                'name': service_name,
                                'port': {
                                    'number': 80
                                }
                            }
                        }
                    }]
                }
            }]
        }
    }

    if tls_secret:
        tls_manifest: dict[Any] = {
            'tls': [{
                'hosts': [name],
                'secretName': tls_secret
            }]
        }
        response['spec'].update(tls_manifest)

    return response


def resource_quota_json_manifest(name, **kwargs):
    """Return json manifest for Resource Quota

        Args:

            name            (str)   --  Name of the network policy

        Kwargs:

            labels                      (dict)  --  Dictionary of labels

            requests_cpu                (str)   --  requests.cpu value for ResourceQuota

            requests_memory             (str)   --  requests.memory value for ResourceQuota

            limits_cpu                  (str)   --  limits.cpu value for ResourceQuota

            limits_memory               (str)   --  limits.memory value for ResourceQuota

            priority_class              (str)   --  Mention priority class to use

            misc_resource_count         (dict)   -- Hard limit on Misc resources. Passed
                                                    eg: {'count/<API Version of any resource except pod,pvc>': '0'}
                                                        Like
                                                        {'count/volumesnapshots.snapshot.storage.k8s.io': '0'}

                                                        Pods and PVCs
                                                        {'persistentvolumeclaims': '1'}
                                                        {'pod': '1'}

    """
    labels = kwargs.get('labels', {})
    labels.update({AutomationLabels.AUTOMATION_LABEL.value: ''})
    requests_cpu = kwargs.get('requests_cpu', '4')
    requests_memory = kwargs.get('requests_memory', '1Gi')
    limits_cpu = kwargs.get('limits_cpu', '8')
    limits_memory = kwargs.get('limits_memory', '2Gi')
    misc_resource_count = kwargs.get('misc_resource_count', None)
    priority_class = kwargs.get('priority_class', None)

    response = {
        'apiVersion': 'v1',
        'kind': 'ResourceQuota',
        'metadata': {
            'name': name,
            'labels': labels
        },
        'spec': {
            'hard': {
                'requests.cpu': requests_cpu,
                'requests.memory': requests_memory,
                'limits.cpu': limits_cpu,
                'limits.memory': limits_memory
            }
        }
    }
    if misc_resource_count:
        response['spec']['hard'].update(misc_resource_count)

    if priority_class:
        priority_class_json: dict[Any] = {
            'scopeSelector': {
                'matchExpressions': [{
                    'operator': 'In',
                    'scopeName': 'PriorityClass',
                    'values': [priority_class]
                }]
            }
        }

        response['spec'].update(priority_class_json)

    return response


def limit_range_json_manifest(name, **kwargs):
    """Return json manifest for LimitRange

        Args:

            name            (str)   --  Name of the LimitRange

        Kwargs:

            labels                      (dict)  --  Dictionary of labels

            max_cpu                     (str)   --  requests.cpu value for LimitRange

            max_memory                  (str)   --  requests.memory value for LimitRange

            min_cpu                     (str)   --  limits.cpu value for LimitRange

            min_memory                  (str)   --  limits.memory value for LimitRange

            default_cpu                 (str)   --  default.cpu value for LimitRange

            default_memory              (str)   --  default.memory value for LimitRange

            default_request_cpu          (str)   --  default.memory value for LimitRange

            default_request_memory       (str)   -- defaultRequest.memory value for LimitRange

        """

    labels = kwargs.get('labels', {})
    labels.update({AutomationLabels.AUTOMATION_LABEL.value: ''})
    max_cpu = kwargs.get('max_cpu', '1')
    max_memory = kwargs.get('max_memory', '1Gi')
    min_cpu = kwargs.get('min_cpu', '100m')
    min_memory = kwargs.get('min_memory', '100Mi')
    default_cpu = kwargs.get('default_cpu', '500m')
    default_memory = kwargs.get('default_memory', '500Mi')
    default_request_cpu = kwargs.get('default_request_cpu', '500m')
    default_request_memory = kwargs.get('default_request_memory', '200Mi')

    response = {
        'apiVersion': 'v1',
        'kind': 'LimitRange',
        'metadata': {
            'name': name,
            'labels': labels
        },
        'spec': {
            'limits': [{
                'default': {
                    'cpu': default_cpu,
                    'memory': default_memory

                },
                'defaultRequest': {
                    'cpu': default_request_cpu,
                    'memory': default_request_memory
                },
                'max': {
                    'cpu': max_cpu,
                    'memory': max_memory
                },
                'min': {
                    'cpu': min_cpu,
                    'memory': min_memory
                },
                'type': 'Container'
            }]
        }
    }

    return response


def implicit_wait(timeout, trials=3):
    """Wait implicitly for the specified time

        Args:

            timeout         (int)   --  Timeout in seconds

            trials          (int)   --  Number times to print wait message

    """

    message_wait = timeout / trials
    log = logger.get_log()

    log.info(f"Implicitly waiting for [{timeout}] seconds")

    for trial in range(trials):
        sleep(message_wait)
        log.info(f"Waited for [{int((trial + 1) * message_wait)}/{timeout}] seconds")
