# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for azure kubernetes cluster deployment and management using azure CLI

AksClientHelper:

    __init__()                                  --  Initialize the AksClientHelper object

    _get_version_info()                         --  gets azure client version info

    _set_account_subscription()                 --  sets default subscription for account in CLI

    logout()                                    --  does logout in azure CLI

    login()                                     --  does login to azure using azure CLI

    create_group()                              --  creates azure resource group

    create_cluster()                            --  creates AKS cluster

    get_credentials()                           --  Get access credentials for managed kubernetes cluster

    group_exists()                              --  checks whether resource group exists or not

    delete_group()                              --  deletes resource group on azure

    create_nodepool()                           --  creates nodepool on azure cluster

    get_cluster_details()                       --  shows details for managed kubernetes cluster

    get_cluster_status()                        --  returns whether cluster is running or not

    cluster_ops()                               --  performs cluster start/stop operations

Attributes:

    **version**      --  Returns dict containing azure client version info

"""
import json
import time

from AutomationUtils import logger
from AutomationUtils.machine import Machine
from Kubernetes import constants as aks_constants


class AksClientHelper:
    """ contains helper class for azure kubernetes cluster deployment and management"""

    def __init__(
            self,
            commcell_object,
            machine_name,
            user_name,
            password,
            service_principal,
            subscription_id):
        """Initialize AksClientHelper class

                Args:

                    commcell_object     (obj)   --  Object of class Commcell

                    machine_name        (str)   --  Name of machine where azure CLI is installed

                    user_name           (str)   --  User name to access machine

                    password            (str)   --  user login password

                    service_principal   (dict)  --  Service principal details for azure login

                                        Example : {
                                                      "appId": "xxxxx",
                                                      "password": "xxxxxxxxx",
                                                      "tenant": "xxxxxxxxxx"
                                                 }

                    subscription_id     (str)   --  Azure subscription Name/ID
        """
        self.commcell = commcell_object
        self.log = logger.get_log()
        self.machine_obj = None
        self.version_info = None
        self.machine_obj = Machine(machine_name=machine_name, username=user_name, password=password)
        self.version_info = self._get_version_info()
        self.service_pal = service_principal
        if not self.version_info:
            raise Exception("Please check whether azure CLI tool is installed on this machine")
        self.logout()
        self.login(service_principal=service_principal)
        self._set_account_subscription(subscription=subscription_id)

    def _get_version_info(self):
        """Returns azure client version info

            Args:

                None

            Returns:

                dict    --  containing azure client version info details

            Raises:

                Exception:

                    if failed to get version info

        """
        output_json = None
        cmd = f"az version"
        output = self.machine_obj.execute_command(command=cmd)
        self.log.info(f"Output of command - {output.output}")
        # Handle no azure CLI found on machine
        if output.exception_message:
            raise Exception("Failed to get version info from az command")
        try:
            output_json = json.loads(output.output)
        except Exception:
            raise Exception(f"Failed to get proper response for azure version - {output.output}")
        return output_json

    def _set_account_subscription(self, subscription):
        """sets default subscription for this account in azure CLI

            Args:

                subscription        (str)       --  Subscription ID

            Returns:

                None

            Raises:

                Exception:

                    if failed to set subscription
        """
        cmd = f"az account set --subscription {subscription}"
        self.log.info(f"Setting default subscription as : {subscription}")
        output = self.machine_obj.execute_command(command=cmd)
        self.log.info(f"Output of command - {output.output}")
        if output.exception_message or output.exit_code != 0:
            raise Exception(f"Failed to set default subscription for account - {output.exception_message}")
        self.log.info("Default subscription set properly for account in azure CLI")

    def logout(self):
        """does logout from azure CLI

            Args:
                None

            Returns:
                None

            Raises:
                Exception:

                    if failed to do logout
        """
        cmd = f"az logout"
        self.log.info("Logging out in Azure CLI")
        output = self.machine_obj.execute_command(command=cmd)
        self.log.info(f"Output of command - {output.output}")
        if output.exception_message and "no active accounts" in output.exception_message:
            self.log.info("Logged out")
            return
        if output.exception_message or output.exit_code != 0:
            raise Exception(f"Failed to do logout - {output.exception_message}")

    def login(self, service_principal):
        """does login to azure from CLI

            Args:

                service_principal       (dict)      --  dict containing service principal login details

                                        Example : {
                                                      "appId": "xxxxx",
                                                      "password": "xxxxxxxxx",
                                                      "tenant": "xxxxxxxxxx"
                                                 }

            Returns:

                None

            Raises:

                Exception:

                    if failed to do login

                    if login params are missing
        """
        if 'appId' not in service_principal or 'password' not in service_principal or 'tenant' not in service_principal:
            raise Exception("Service principal arguments are missing. Please check")
        cmd = f"az login --service-principal --username {service_principal['appId']} " \
              f"--password {service_principal['password']} " \
              f"--tenant {service_principal['tenant']}"
        self.log.info(f"Logging in Azure CLI using command - {cmd}")
        output = self.machine_obj.execute_command(command=cmd)
        self.log.info(f"Output of command - {output.output}")
        if output.exception_message or output.exit_code != 0:
            raise Exception(f"Failed to do login - {output.exception_message}")
        try:
            _ = json.loads(output.output)
        except Exception:
            raise Exception(f"Failed to get proper response for login - {output.output}")

    def create_group(self, group_name, location):
        """Creates azure resource group

            Args:

                group_name          (str)       --  resource group name

                location            (str)       --  resource location

            Returns:

                None

            Raises:

                Exception:

                    if failed to create resource group
        """
        cmd = f"az group create --name {group_name} --location {location}"
        self.log.info(f"Creating resource group : {group_name} in location : {location}. command - {cmd}")
        output = self.machine_obj.execute_command(command=cmd)
        self.log.info(f"Output of command - {output.output}")
        if output.exception_message or output.exit_code != 0:
            raise Exception(f"Failed to create resource group - {output.exception_message}")
        try:
            _ = json.loads(output.output)
        except Exception:
            raise Exception(f"Create resource group response is not proper - {output.output}")

    def create_cluster(self, name, resource_group, **kwargs):
        """Creates AKS cluster in resource group specified

            Args:

                name            (str)       --  Cluster name

                resource_group  (str)       --  Resource group name

            kwargs Attributes:

                node_count              (int)       --  Number of nodes in the Kubernetes node pool (Default:1)

                enable_autoscaler       (bool)      --  Enable cluster autoscaler (Default:true)

                min_count               (int)       --  Minimum nodes count used for autoscaler, when "enable_autoscaler" specified
                                                            (Default:1)

                max_count               (int)       --  Maximum nodes count used for autoscaler, when "enable_autoscaler" specified.
                                                            (Default:30)

                vm_size                 (str)       --  Size of Virtual Machines to create as Kubernetes nodes
                                                            (Default: standard_d4s_v3)

                attach_acr              (str)       --  Grant the 'acrpull' role assignment to the ACR specified by name

                ssh                     (str)       --  ssh key value file path [Public key path or key contents to install on node VMs for SSH access]

                node_pool_name          (str)       --  Name of node pool

                node_pool_label         (str)       --  Labels for node pool

            Returns:

                None

            Raises:

                Exception:

                        if failed to create kubernetes cluster
        """
        cmd = f"az aks create -n {name} -g {resource_group} --node-count {kwargs.get('node_count',1)} " \
            f"--node-vm-size {kwargs.get('vm_size','standard_d4s_v3')}"
        if 'attach_acr' in kwargs:
            cmd = f"{cmd} --attach-acr {kwargs.get('attach_acr')}"
        if 'ssh' in kwargs:
            cmd = f"{cmd} --ssh-key-value {kwargs.get('ssh')}"
        if kwargs.get('enable_autoscaler', True):
            cmd = f"{cmd} --enable-cluster-autoscaler " \
                  f"--min-count {kwargs.get('min_count', 1)} --max-count {kwargs.get('max_count', 30)} "
        if 'node_pool_name' in kwargs:
            cmd = f"{cmd} --nodepool-name {kwargs.get('node_pool_name')}"
        if 'node_pool_label' in kwargs:
            cmd = f"{cmd} --nodepool-labels {kwargs.get('node_pool_label')}"
        self.log.info(f"Creating kubernetes cluster using command - {cmd}")
        output = self.machine_obj.execute_command(command=cmd)
        self.log.info(f"Output of command - {output.output}")
        try:
            _ = json.loads(output.output)
        except Exception:
            # json load failure so check for any exception
            if output.exception_message or output.exit_code != 0:
                raise Exception(f"Failed to create cluster - {output.exception_message}")
            raise Exception(f"Create cluster response is not proper - {output.output}")

    def get_credentials(
            self,
            cluster_name,
            resource_group,
            overwrite=True,
            **kwargs):
        """Gets managed kubernetes cluster credentials and merge this into kube config file

            Args:

                cluster_name            (str)       --  Name of cluster

                resource_group          (str)       --  Resource group name

                overwrite               (bool)      --  overwrite kube config file

            kwargs:

                retry   (bool)      --   Specifies whether to do retry or not

            Returns:

                None

            Raises:

                Exception:

                    if failed to get credentials for cluster
        """
        retry = kwargs.get('retry', True)
        cmd = f"az aks get-credentials -n {cluster_name} -g {resource_group}"
        if overwrite:
            cmd = f"{cmd} --overwrite-existing"
        self.log.info(f"Getting credentials for cluster using command - {cmd}")
        output = self.machine_obj.execute_command(command=cmd)
        self.log.info(f"Output of command - {output.output}")
        if output.output or output.exit_code != 0:
            raise Exception(
                f"Failed to get credentials for cluster - {output.output}")
        # in case of overwrite, we get exception warning. so handle that case
        if not overwrite and output.exception_message:
            raise Exception(
                f"Failed to get credentials for cluster - {output.exception_message}")
        elif 'ERROR:' in output.exception_message and 'timed out' in output.exception_message and retry:
            time.sleep(60)
            self.get_credentials(cluster_name=cluster_name,
                                 resource_group=resource_group,
                                 overwrite=overwrite,
                                 retry=False)
        elif 'ERROR:' in output.exception_message:
            raise Exception(
                f"Failed to get credentials for cluster - {output.exception_message}")

    def group_exists(self, name):
        """checks whether resource group exists in azure or not

            Args:

                name            (str)       --  Name of resource group

            Returns:

                bool    -- denoting whether group exists or not

            Raises:

                Exception:

                    if failed to execute command
        """
        cmd = f"az group exists -n {name}"
        self.log.info(f"Checking resource group exists or not. command - {cmd}")
        output = self.machine_obj.execute_command(command=cmd)
        self.log.info(f"Output of command - {output.output}")
        if output.exception_message or output.exit_code != 0:
            raise Exception(f"Failed to check resource group existence - {output.exception_message}")
        if output.output.strip() == "true":
            return True
        return False

    def delete_group(self, name, wait_for_deletion=True):
        """Deletes the azure resource group

                Args:

                    name                (str)       --  Resource group name

                    wait_for_deletion   (bool)      --  specifies whether to wait for delete to happen or not
                                                            Default: True
                Returns:

                      None

                Raises:

                      Exception:

                        if failed to delete resource group

                        if failed to find resource group
        """
        if not self.group_exists(name=name):
            raise Exception("Resource group doesn't exists on azure. Please check")
        cmd = f"az group delete -y -n {name}"
        if not wait_for_deletion:
            cmd = f"{cmd} --no-wait"
        self.log.info(f"Deleting resource group. command - {cmd}")
        output = self.machine_obj.execute_command(command=cmd)
        self.log.info(f"Output of command - {output.output}")
        if output.exception_message or output.exit_code != 0:
            raise Exception(
                f"Failed to delete resource group - {output.exception_message}")

    def create_nodepool(
            self,
            cluster_name,
            resource_group,
            node_pool_name,
            **kwargs):
        """Creates nodepool on azure aks cluster

            Args:

                cluster_name        (str)       --  Cluster name

                resource_group      (str)       --  Name of resource group where cluster exists

                node_pool_name      (str)       --  Node pool name to create

            **kwargs Options**

                node_count      (int)   --  Minimum no of node to be up (Default:1)

                node_vm_size    (str)   --  Azure node vm size (Default : Standard_B4ms)

                labels          (str)   --  Labels to apply on node pool

                enable_autoscaler (bool)--  Enable cluster autoscaler (Default:true)

                min_count       (int)   --  Minimum nodes count used for autoscaler, when "enable_autoscaler" specified
                                                            (Default:1)

                max_count       (int)   --  Maximum nodes count used for autoscaler, when "enable_autoscaler" specified.
                                                            (Default:30)


        """
        cmd = f'az aks nodepool add --resource-group {resource_group} --cluster-name {cluster_name} ' \
              f'--name {node_pool_name} --node-count {kwargs.get("node_count",1)} --node-vm-size {kwargs.get("node_vm_size","Standard_B4ms")}'
        if kwargs.get('labels'):
            cmd = f"{cmd} --labels {kwargs.get('labels')}"
        if kwargs.get('enable_autoscaler', True):
            cmd = f"{cmd} --enable-cluster-autoscaler " \
                  f"--min-count {kwargs.get('min_count', 1)} --max-count {kwargs.get('max_count', 30)} "
        self.log.info(f"Nodepool create command - {cmd}")
        output = self.machine_obj.execute_command(command=cmd)
        self.log.info(f"Output of command - {output.output}")
        try:
            _ = json.loads(output.output)
        except Exception:
            # json load failure so check for any exception
            if output.exception_message or output.exit_code != 0:
                raise Exception(
                    f"Failed to create nodepool - {output.exception_message}")
            raise Exception(
                f"Create nodepool response is not proper - {output.output}")

    def get_cluster_details(self, cluster_name,
                            resource_group):
        """get details of given managed kubernetes cluster

            Args:

                cluster_name        (str)       --  Cluster name

                resource_group      (str)       --  Cluster's  resource group

            Returns:

                dict    --  containing cluster details

            Raises:

                Exception:

                    if failed to get details for cluster
        """
        cmd = f'az aks show --resource-group {resource_group} --name {cluster_name}'
        self.log.info(f"Show command - {cmd}")
        output = self.machine_obj.execute_command(command=cmd)
        self.log.info(f"Output of command - {output.output}")
        try:
            _json = json.loads(output.output)
            return _json
        except Exception:
            # json load failure so check for any exception
            if output.exception_message or output.exit_code != 0:
                raise Exception(
                    f"Failed to get cluster details - {output.exception_message}")
            raise Exception(
                f"Show cluster details response is not proper - {output.output}")

    def get_cluster_status(self, cluster_name,
                           resource_group, running=True):
        """Checks whether cluster is running or not

            Args:

                cluster_name        (str)       --  Cluster name

                resource_group      (str)       --  Cluster's  resource group

                running             (bool)      --  Expected state to check for cluster [Default:True]
                                                        True = Running
                                                        False= Stopped

            Returns:

                bool    --  specifies whether cluster is in expected status or not

            Raises:

                Exception:

                    if failed to get status
        """
        _status = self.get_cluster_details(cluster_name=cluster_name, resource_group=resource_group)
        if aks_constants.FIELD_POWER_STATE not in _status:
            raise Exception("Powerstate is not present in response. Please check logs")
        if running:
            if aks_constants.FIELD_CODE in _status[aks_constants.FIELD_POWER_STATE] and _status[
                    aks_constants.FIELD_POWER_STATE][aks_constants.FIELD_CODE] == aks_constants.FIELD_STATUS_RUNNING:
                return True
        else:
            if aks_constants.FIELD_CODE in _status[aks_constants.FIELD_POWER_STATE] and _status[
                    aks_constants.FIELD_POWER_STATE][aks_constants.FIELD_CODE] == aks_constants.FIELD_STATUS_STOPPED:
                return True
        return False

    def cluster_ops(self, cluster_name,
                    resource_group, is_start=True, timeout=30):
        """Performs cluster start/stop operation

            Args:

                cluster_name        (str)       --  Cluster name

                resource_group      (str)       --  Cluster's  resource group

                is_start            (bool)      --  Specifies whether to start cluster or not [Default:True to start]

                timeout             (int)       --  Wait time in mins to cluster operation to complete [Default:30Mins]


            Returns:

                None

            Raises:

                Exception:

                    if failed to start or stop cluster

        """
        if is_start:
            self.log.info(f"Going to start cluster  - {cluster_name}")
            if self.get_cluster_status(cluster_name=cluster_name, resource_group=resource_group, running=True):
                self.log.info(f"Cluster is in running state already. Nothing to do")
                return
            else:
                self.log.info("Starting Cluster ...")
                cmd = f'az aks start --resource-group {resource_group} --name {cluster_name}'
                self.log.info(f"Start command - {cmd}")
                output = self.machine_obj.execute_command(command=cmd)
                self.log.info(f"Output of command - {output.output}")
        else:
            self.log.info(f"Going to stop cluster  - {cluster_name}")
            if self.get_cluster_status(cluster_name=cluster_name, resource_group=resource_group, running=False):
                self.log.info(f"Cluster is in stopped state already. Nothing to do")
                return
            else:
                self.log.info("Stopping Cluster ...")
                cmd = f'az aks stop --resource-group {resource_group} --name {cluster_name}'
                self.log.info(f"Stop command - {cmd}")
                output = self.machine_obj.execute_command(command=cmd)
                self.log.info(f"Output of command - {output.output}")

        # start/stop will not wait for some long running resources to start/stop so handling this via below timeout
        start_time = time.time()
        timeout = timeout * 60
        while time.time() - start_time < timeout:
            if is_start:
                if self.get_cluster_status(cluster_name=cluster_name, resource_group=resource_group, running=True):
                    self.log.info(f"Cluster[{cluster_name}] is in running state")
                    return
            else:
                if self.get_cluster_status(cluster_name=cluster_name, resource_group=resource_group, running=False):
                    self.log.info(f"Cluster[{cluster_name}] is in stopped state")
                    return
            self.log.info(f"Waiting for 1min before checking cluster status again")
            time.sleep(60)
        raise Exception(
            f"Timeout waiting for cluster to be in expected status - {'Running' if is_start else 'Stopped'}")

    @property
    def version(self):
        """returns the client version info

            Args:
                None

            Returns:
                dict    --  containing client version info
        """
        if self.version_info:
            return self.version_info
        return {}
