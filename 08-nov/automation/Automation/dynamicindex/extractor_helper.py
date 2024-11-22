# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for extracting kubernetes cluster related operations

ExtractingClusterHelper:

    __init__()                                  --  Initialize the ExtractingClusterHelper object

    create_extracting_cluster()                 --  creates extracting kubernetes cluster on azure

    setup_credential_manager()                  --  Adds azure credential manager settings for RedisCache & AKS Cluster

    delete_credential()                         --  Deletes the credentials from credential vault

    set_cluster_settings_on_cs()                --  sets extracting cluster settings on commserv

    remove_cluster_settings_on_cs()             --  removes extracting cluster settings on commserv

    delete_resource_group()                     --  deletes the resource group on azure

    get_image_info_from_yaml()                  --  parses yaml file and returns image version info

    get_scaling_config_from_yaml()              --  parses yaml file and returns auto scaling configuration

    validate_scale_config()                     --  Validates cluster pod auto scaling based on yaml configuration

    get_cv_logs()                               --  gets commvault logs from all running pods in cluster

    get_pod_logs_for_pattern()                  --  Analyse pod logs for pattern match and return those matching log lines

    get_stdout_logs()                           --  Gets stdout logs for given pod

"""
import time

from AutomationUtils import logger, commonutils
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from Kubernetes.akscluster_helper import AksClientHelper
from Kubernetes.kubectl_helper import KubectlHelper
from Kubernetes import constants as kube_constants
from dynamicindex.utils import constants as dynamic_constants

_CONFIG_DATA = get_config().DynamicIndex.ExtractingCluster


class ExtractingClusterHelper:
    """ contains helper class for extracting service operations for kubernetes cluster"""

    def __init__(self, commcell_object):
        """Initialize ExtractingClusterHelper class

                Args:

                    commcell_object     (obj)   --  Object of class Commcell

        """
        self.commcell = commcell_object
        self.log = logger.get_log()
        self.az_master = AksClientHelper(
            self.commcell,
            machine_name=_CONFIG_DATA.AZMachine.name,
            user_name=_CONFIG_DATA.AZMachine.username,
            password=_CONFIG_DATA.AZMachine.password,
            service_principal={
                dynamic_constants.FIELD_APPID: _CONFIG_DATA.AzureAdServicePrincipals.appId,
                dynamic_constants.FIELD_PASSWORD: _CONFIG_DATA.AzureAdServicePrincipals.password,
                dynamic_constants.FIELD_TENANT: _CONFIG_DATA.AzureAdServicePrincipals.tenant},
            subscription_id=_CONFIG_DATA.AzureSubscription)
        self.log.info("Initialized AksClientHelper object")
        self.kube_master = KubectlHelper(self.commcell,
                                         machine_name=_CONFIG_DATA.KubectlMachine.name,
                                         user_name=_CONFIG_DATA.KubectlMachine.username,
                                         password=_CONFIG_DATA.KubectlMachine.password)
        self.log.info("Initialized KubectlHelper object")

    def delete_resource_group(self, resource_group):
        """Deletes resource group on azure

            Args:

                resource_group      (str)       --  Name of resource group

            Returns:

                None

            Raises:

                None
        """
        if self.az_master.group_exists(name=resource_group):
            self.log.info(f"Resource Group exists - {resource_group}. Deleting it")
            self.az_master.delete_group(name=resource_group)
        self.log.info(f"Successfully deleted the resource group - {resource_group}")

    def create_extracting_cluster(
            self,
            name,
            resource_group,
            location,
            yaml_file,
            **kwargs):
        """Creates extracting kubernetes cluster on azure and setup az/kubectl on machine

            Args:

                name            (str)       --  Cluster name

                resource_group  (str)       --  Resource group name

                location        (str)       --  Location to create cluster

                yaml_file       (str)       --  yaml file path on controller

            kwargs Attributes:

                node_count              (int)       --  Number of nodes in the Kubernetes node pool (Default:1)

                enable_autoscaler       (bool)      --  Enable cluster autoscaler (Default:true)

                min_count               (int)       --  Minimum nodes count used for autoscaler, when "enable_autoscaler" specified
                                                            (Default:1)

                max_count               (int)       --  Maximum nodes count used for autoscaler, when "enable_autoscaler" specified.
                                                            (Default:20)

                vm_size                 (str)       --  Size of Virtual Machines to create as Kubernetes nodes
                                                            (Default: standard_d4s_v3)

                attach_acr              (str)       --  Grant the 'acrpull' role assignment to the ACR specified by name

                ssh                     (str)       --  ssh key value file path [Public key path or key contents to install on node VMs for SSH access]

            Returns:

                str     --  External IP Address of cluster

            Raises:

                Exception:

                        if failed to create kubernetes cluster

                        if failed to find AZ or kubectl command line tools on machine

                        if AZ/Kubectl machine are not same

        """
        if _CONFIG_DATA.AZMachine.name.lower() != _CONFIG_DATA.KubectlMachine.name.lower():
            raise Exception("Not a supported configuration. Use same machine for AZ/Kubectl")
        self.delete_resource_group(resource_group=resource_group)
        self.log.info(f"Going to create resource group - {resource_group}")
        self.az_master.create_group(group_name=resource_group, location=location)
        time.sleep(30)  # Sometimes resource group is not identified on azure
        self.log.info(f"Going to create AKS cluster on azure - {name}")
        if len(kwargs) == 0:
            self.log.info(f"Default configuration for cluster detected")
            self.az_master.create_cluster(name=name, resource_group=resource_group,
                                          attach_acr=dynamic_constants.ACR_NAME, ssh=_CONFIG_DATA.AzureSSHKeyFilePath,
                                          enable_autoscaler=True, min_count=1, max_count=30, node_count=1)
        else:
            self.log.info(f"User configuration for cluster detected for VM sizing")
            self.az_master.create_cluster(
                name=name,
                resource_group=resource_group,
                attach_acr=dynamic_constants.ACR_NAME,
                ssh=_CONFIG_DATA.AzureSSHKeyFilePath,
                **kwargs)
        self.log.info("Waiting for 3mins for cluster to resolved by azure DNS")
        time.sleep(180)
        self.log.info(f"Going to import AKS credentials into .kube/config")
        self.az_master.get_credentials(
            cluster_name=name,
            resource_group=resource_group,
            overwrite=True)
        self.log.info("Going to create secret for docker registry")
        self.kube_master.create_secret_docker_registry(
            secret_name=_CONFIG_DATA.ImageSecrets.Name,
            server=_CONFIG_DATA.ImageSecrets.Server,
            user=_CONFIG_DATA.ImageSecrets.User,
            password=_CONFIG_DATA.ImageSecrets.Password)
        self.log.info(f"Going to apply yaml configuration via kubectl")
        self.kube_master.apply_yaml(yaml_file=yaml_file)
        self.log.info(f"Yaml applied. Wait for 2Min and then try getting public IP of cluster")
        time.sleep(120)
        ip = self.kube_master.get_service(service_name=dynamic_constants.EXTRACTING_SERVICE_NAME)
        ip = ip[dynamic_constants.FIELD_STATUS][dynamic_constants.FIELD_LOADBALANCER][dynamic_constants.FIELD_INGRESS][0][dynamic_constants.FIELD_EXTERNAL_IP]
        if not ip:
            raise Exception("Failed to get cluster IP")
        return ip

    def delete_credential(self, credential_name):
        """Deletes the credential entry from vault

            Args:

                credential_name (str)   --  name to be given to credential account

            Returns:

                None
        """
        cred_mgr = self.commcell.credentials
        if cred_mgr.has_credential(credential_name):
            self.log.info(
                f"Credential with name : {credential_name} exists. Deleting it")
            cred_mgr.delete(credential_name)

    def setup_credential_manager(
            self,
            credential_name,
            account_name,
            access_key_id,
            **kwargs):
        """Creates credential in credential vault for azure

            Args:

                credential_name (str)   --  name to be given to credential account

                account_name  (str)     --  name of the azure storage account

                access_key_id   (str)   --  access key for azure storage

                ** kwargs(dict)         --  Key value pairs for supported arguments

                Supported argument values:
                    owner(str)                  -   owner of the credentials
                    is_user(bool)               -   Represents whether owner passed is a user or user group
                                                    is_user=1 for user, is_user=0 for usergroup
                    description(str)            -   description of the credentials

                    corrupt_access_key(bool)   -   Specifies whether to corrupt the inputted access key id or not

            Returns:

                None

            Raises:

                Exception:

                    if failed to add entry to credential manager

        """
        if kwargs.get('corrupt_access_key', False):
            self.log.info(
                f"Corrupt Key is present. Updating junk values to access key id")
            access_key_id = f"10aaaaaaaaaaaaaa{access_key_id}bbbbbbbbbbbbbbb15"
        cred_mgr = self.commcell.credentials
        self.delete_credential(credential_name=credential_name)
        self.log.info(
            f"Going to create credential with Name -{credential_name} Account - {account_name} Key - {access_key_id}")
        cred_mgr.add_azure_cloud_creds(
            credential_name=credential_name,
            account_name=account_name,
            access_key_id=access_key_id,
            **kwargs)
        self.log.info(
            f"Successfully created credential manager entry for : {credential_name}")

    def set_cluster_settings_on_cs(
            self,
            extracting_ip,
            index_gateway,
            user_name,
            password,
            region="eastus2",
            **kwargs):
        """sets extracting cluster settings on commserv

            Args:

                extracting_ip       (str)       --  External ip address of cluster

                index_gateway       (str)       --  Index gateway installed machine which will be used by CI job

                user_name           (str)       --  User name for accessing index gateway machine

                password            (str)       --  User password

                region              (str)       --  region where this cloud settings applicable to (default:eastus2)

            kwargs Supported values:

                corrupt_cluster_key     (bool)      --  Specifies whether to corrupt inputted cluster key url or not

                feature_type            (str)       --  Specifies the feature type to be set for settings (Default:ContentIndexing)

            Returns:

                None

            Raises:

                Exception:

                    if failed to add additional settings on CS
        """
        # remove older settings if any

        self.remove_cluster_settings_on_cs(
            index_gateway=index_gateway,
            user_name=user_name,
            password=password,
            region=region)

        # FileShare storage
        self.setup_credential_manager(
            credential_name=_CONFIG_DATA.CredentialName_FileShare,
            account_name=_CONFIG_DATA.FileShare_Account,
            access_key_id=_CONFIG_DATA.FileShare_SecretKey,
            owner=self.commcell.commcell_username)
        self.log.info(
            f"Going to map File Share credential - {_CONFIG_DATA.CredentialName_FileShare} entry to cloud region : {region} ")
        qscript = f"-sn {dynamic_constants.CLOUD_APP_STORAGE_QSCRIPT} " \
                  f"-si '{_CONFIG_DATA.CredentialName_FileShare}_{region}' -si 'CREATE' -si '{kwargs.get('feature_type',dynamic_constants.FEATURE_TYPE_CI)}' -si '1' -si '{region}' " \
                  f"-si 'Region' " \
                  f"-si '{dynamic_constants.KEY_FILE_SHARE_STORAGE}' -si '{_CONFIG_DATA.CredentialName_FileShare}'"
        self.log.info(qscript)
        self.commcell._qoperation_execscript(qscript)
        self.log.info(
            "Successfully added File Share storage additional setting on commserv")

        # redis cache
        self.setup_credential_manager(
            credential_name=_CONFIG_DATA.CredentialName_Redis,
            account_name=_CONFIG_DATA.RedisCacheConfigHost,
            access_key_id=_CONFIG_DATA.RedisCacheConfigSecretKey,
            owner=self.commcell.commcell_username)
        self.log.info(
            f"Going to map Redis credential - {_CONFIG_DATA.CredentialName_Redis} entry to cloud region : {region} ")
        qscript = f"-sn {dynamic_constants.CLOUD_APP_STORAGE_QSCRIPT} " \
                  f"-si '{_CONFIG_DATA.CredentialName_Redis}_{region}' -si 'CREATE' -si '{kwargs.get('feature_type',dynamic_constants.FEATURE_TYPE_ALL)}' -si '1' -si '{region}' " \
                  f"-si 'Region' " \
                  f"-si '{dynamic_constants.KEY_REDIS_CACHE_CONFIG}' -si '{_CONFIG_DATA.CredentialName_Redis}'"
        self.log.info(qscript)
        self.commcell._qoperation_execscript(qscript)
        self.log.info(
            "Successfully added Redis cache additional setting on commserv")

        # Aks Cluster
        self.setup_credential_manager(
            credential_name=_CONFIG_DATA.CredentialName_Aks,
            account_name=f"http://{extracting_ip}",
            access_key_id=dynamic_constants.SECRET_KEY_CLUSTER,
            owner=self.commcell.commcell_username,
            corrupt_access_key=kwargs.get(
                'corrupt_cluster_key',
                False))
        self.log.info(
            f"Going to Map AKS Cluster credential - {_CONFIG_DATA.CredentialName_Aks} entry to cloud region : {region} ")
        qscript = f"-sn {dynamic_constants.CLOUD_APP_STORAGE_QSCRIPT} -si '{_CONFIG_DATA.CredentialName_Aks}_{region}' " \
                  f"-si 'CREATE' -si '{kwargs.get('feature_type',dynamic_constants.FEATURE_TYPE_CI)}' -si '1' -si '{region}' -si 'Region' " \
                  f"-si '{dynamic_constants.KEY_EXTRACTING_SERVICE_URL}' -si '{_CONFIG_DATA.CredentialName_Aks}'"
        self.log.info(qscript)
        self.commcell._qoperation_execscript(qscript)
        self.log.info(
            "Successfully added AKS Cluster additional setting on commserv")
        self.log.info(
            f"Restarting IIS on index gateway client - {index_gateway}")
        machine_obj = Machine(
            machine_name=index_gateway,
            username=user_name,
            password=password)
        machine_obj.restart_iis()
        time.sleep(600)
        self.log.info("IIS Restarted")
        self.commcell.refresh()

    def remove_cluster_settings_on_cs(
            self,
            index_gateway,
            user_name,
            password,
            region="eastus2"):
        """removes extracting cluster settings on commserv

            Args:

                index_gateway       (str)       --  Index gateway installed machine which will be used by CI job

                user_name           (str)       --  User name for accessing index gateway machine

                password            (str)       --  User password

                region              (str)       --  region where this cloud settings applicable to (default:eastus2)

            Returns:

                None

            Raises:

                Exception:

                    if failed to remove additional settings on CS
        """
        # FileShare storage
        self.log.info(
            f"Going to unmap File Share credential - {_CONFIG_DATA.CredentialName_FileShare} entry to cloud region : {region} ")
        qscript = f"-sn {dynamic_constants.CLOUD_APP_STORAGE_QSCRIPT} -si '{_CONFIG_DATA.CredentialName_FileShare}_{region}' -si 'DELETE'"
        self.log.info(qscript)
        self.commcell._qoperation_execscript(qscript)
        self.delete_credential(
            credential_name=_CONFIG_DATA.CredentialName_FileShare)
        self.log.info(
            "Successfully deleted FileShare storage additional setting on commserv")

        # redis cache

        self.log.info(
            f"Going to unmap Redis credential - {_CONFIG_DATA.CredentialName_Redis} entry to cloud region : {region} ")
        qscript = f"-sn {dynamic_constants.CLOUD_APP_STORAGE_QSCRIPT} -si '{_CONFIG_DATA.CredentialName_Redis}_{region}' -si 'DELETE'"
        self.log.info(qscript)
        self.commcell._qoperation_execscript(qscript)
        self.delete_credential(
            credential_name=_CONFIG_DATA.CredentialName_Redis)
        self.log.info(
            "Successfully deleted Redis cache additional setting on commserv")

        # Aks Cluster

        self.log.info(
            f"Going to UnMap AKS Cluster credential - {_CONFIG_DATA.CredentialName_Aks} entry to cloud region : {region} ")
        qscript = f"-sn {dynamic_constants.CLOUD_APP_STORAGE_QSCRIPT} -si '{_CONFIG_DATA.CredentialName_Aks}_{region}' -si 'DELETE'"
        self.log.info(qscript)
        self.commcell._qoperation_execscript(qscript)
        self.delete_credential(credential_name=_CONFIG_DATA.CredentialName_Aks)
        self.log.info(
            "Successfully deleted AKS Cluster additional setting on commserv")

        self.log.info(
            f"Restarting IIS on index gateway client - {index_gateway}")
        machine_obj = Machine(
            machine_name=index_gateway,
            username=user_name,
            password=password)
        machine_obj.restart_iis()
        time.sleep(120)
        self.log.info("IIS Restarted")

    def get_image_info_from_yaml(self, yaml_file, container_name):
        """Returns image version by parsing yaml file

            Args:

                yaml_file           (str)       --  Yaml file path on controller

                container_name      (str)       --  Container name whose version has to be fetched

            Returns:

                str --  Image version details. Returns "NA" if container not found
        """
        yaml_dict = self.kube_master.convert_yaml_to_json(yaml_file=yaml_file)
        self.log.info(f"Going to find version info for container - {container_name}")
        for each_obj in yaml_dict:
            if each_obj[kube_constants.FIELD_KIND] == kube_constants.FIELD_DEPLOYMENT:
                containers = each_obj[kube_constants.FIELD_SPEC][kube_constants.FIELD_TEMPLATE][kube_constants.FIELD_SPEC][kube_constants.FIELD_CONTAINERS]
                for container in containers:
                    if container[kube_constants.FIELD_NAME] == container_name:
                        self.log.info(f"Image version found - {container[kube_constants.FIELD_IMAGE]}")
                        return container[kube_constants.FIELD_IMAGE]
        return "NA"

    def get_scaling_config_from_yaml(self, yaml_file, name, kind='HorizontalPodAutoscaler'):
        """Parses yaml file adn returns auto scaling configurations

                Args:

                    yaml_file           (str)       --  Yaml file path on controller

                    name                (str)       --  AutoScaler name

                    kind                (str)       --  Type of autoscaler.(Default:HorizontalPodAutoscaler)

                Returns:

                    dict        --  Containing auto scaler configuration details

                Example :   {
                              "minReplicas": 1,
                              "maxReplicas": 6,
                              "behavior": {
                                "scaleDown": {
                                  "stabilizationWindowSeconds": 600,
                                  "policies": [
                                    {
                                      "type": "Percent",
                                      "value": 10,
                                      "periodSeconds": 120
                                    }
                                  ]
                                },
                                "scaleUp": {
                                  "stabilizationWindowSeconds": 120,
                                  "policies": [
                                    {
                                      "type": "Pods",
                                      "value": 2,
                                      "periodSeconds": 60
                                    }
                                  ]
                                }
                              },
                              "metrics": [
                                {
                                  "type": "Resource",
                                  "resource": {
                                    "name": "cpu",
                                    "target": {
                                      "type": "Utilization",
                                      "averageUtilization": 50
                                    }
                                  }
                                }
                              ]
                            }

                Raises:

                    Exception:

                        if failed to load yaml file
        """
        output = {}
        yaml_dict = commonutils.convert_yaml_to_json(yaml_file=yaml_file)
        self.log.info(f"Going to find Scaling info for - {name}")
        for each_obj in yaml_dict:
            if each_obj[kube_constants.FIELD_KIND] == kind:
                if each_obj[kube_constants.FIELD_METADATA][kube_constants.FIELD_NAME] == name:
                    output[kube_constants.FIELD_MIN_REPLICA] = each_obj[kube_constants.FIELD_SPEC][kube_constants.FIELD_MIN_REPLICA]
                    output[kube_constants.FIELD_MAX_REPLICA] = each_obj[kube_constants.FIELD_SPEC][kube_constants.FIELD_MAX_REPLICA]
                    output[kube_constants.FIELD_BEHAVIOR] = each_obj[kube_constants.FIELD_SPEC][kube_constants.FIELD_BEHAVIOR]
                    output[kube_constants.FIELD_METRICS] = each_obj[kube_constants.FIELD_SPEC][kube_constants.FIELD_METRICS]
                    break
        return output

    def validate_scale_config(
            self,
            yaml_file,
            timeout=15,
            check_interval=120,
            scale_up=True,
            **kwargs):
        """Validates cluster auto scale up based on yaml file configuration

        Args:

                yaml_file       (str)       --  Yaml file path on controller

                timeout         (int)       --  Timeout in mins
                                                    Default:15Mins

                check_interval  (int)       --  Time interval in secs between POD status check
                                                    Default:120Sec

                scale_up        (bool)      --  True -> Validates scale up of auto scaling
                                                False ->Validates scale down of auto scaling

        Kwargs Options:

                raise_error     (bool)      --  Bool to specify whether to raise exception on scale up/down happened or not
                                                                    (Default:True)

            Returns:

                None

            Raises:

                None
        """
        raise_error = kwargs.get("raise_error", True)
        monitor_details = self.kube_master.monitor_pod(
            timeout=timeout, check_interval=check_interval)
        scale_config = self.get_scaling_config_from_yaml(
            yaml_file=yaml_file, name=kube_constants.EXTRACTING_APP_NAME)
        if scale_up:
            max_replica = scale_config[kube_constants.FIELD_MAX_REPLICA]
            scale_up = monitor_details[kube_constants.KEY_SCALED_UP]
            self.log.info(f"Max replica set in yaml file is : {max_replica}")
            if not scale_up and raise_error:
                raise Exception(
                    "POD scale up never happened on given time period")
            self.log.info(
                f"Total no of scale up detected is : {len(scale_up)}")
            max_spawn_pod = 0
            for each_scale in scale_up:
                self.log.info(
                    f"Scale Up Detected @ [{each_scale[kube_constants.KEY_TIME]}] with new pod count [{len(each_scale[kube_constants.KEY_PODS])}]")
                max_spawn_pod = max_spawn_pod + \
                    len(each_scale[kube_constants.KEY_PODS])
            self.log.info(f"Maximum spawned POD - {max_spawn_pod}")
            if max_spawn_pod > max_replica:
                # error condition. Get as much details from cluster to debug
                running_pods = self.kube_master.get_pods(
                    status=kube_constants.FIELD_STATUS_RUNNING)
                self.log.info(f"Running PODS - {running_pods}")
                if running_pods > max_replica:
                    raise Exception(
                        f"Total running POD({running_pods}) is more than Max replica({max_replica}) set in yaml")

                raise Exception(
                    f"Spawned POD is more than max replica set as POD with error status detected")
            self.log.info(
                f"Scale up validation success. Max spawned pod : {max_spawn_pod} & max replica : {max_replica}")
        else:
            min_replica = scale_config[kube_constants.FIELD_MIN_REPLICA]
            scale_down = monitor_details[kube_constants.KEY_SCALED_DOWN]
            self.log.info(f"Min replica set in yaml file is : {min_replica}")
            if not scale_down and raise_error:
                raise Exception(
                    "POD scale down never happened on given time period")
            self.log.info(
                f"Total no of scale down detected is : {len(scale_down)}")
            running_pods = self.kube_master.get_pods(
                status=kube_constants.FIELD_STATUS_RUNNING)
            self.log.info(f"Running PODS - {running_pods}")
            if min_replica != len(running_pods):
                # error condition. Get as much details from cluster to debug
                raise Exception(
                    f"Total running POD({len(running_pods)}) is more than Min replica({min_replica}) set in yaml")
            self.log.info(
                f"Scale down validation success. Running pod : {running_pods} & min replica : {min_replica}")

    def get_cv_logs(self):
        """Gets commvault logs from all pods running on cluster

            Args:

                None

            Returns:

                list(str) --  Folder path containing pod logs

            Raises:

                Exception:

                    if failed to collect logs files from pod
        """
        output = []
        pods = self.kube_master.get_pods()
        for pod in pods:
            output.append(self.kube_master.get_folder_or_file_from_pod(
                file_or_folder=dynamic_constants.POD_LOG_PATH, pod_name=pod))
        return output

    def get_stdout_logs(self):
        """Gets stdout logs from all pods running on cluster

            Args:

                None

            Returns:

                list(str) --  File path containing pod logs

            Raises:

                Exception:

                    if failed to collect logs files from pod
        """
        output = []
        pods = self.kube_master.get_pods()
        for pod in pods:
            output.append(self.kube_master.get_stdout_logs(pod_name=pod))
        return output

    def get_pod_logs_for_pattern(self, file_name, pattern):
        """Analyse pod logs for pattern match and return those matching log lines

            Args:

                file_name       (str)       --  File name to analyze

                pattern         (str)       --  Pattern to look for

            Returns:

                list(str)     -   \r\n separated string containing the matched log lines.

            Raises:

                Exception:

                    None

        """
        output = []
        pod_log_folders = self.get_stdout_logs()
        for log_folder in pod_log_folders:
            self.log.info(
                f"Analyzing log folder : {log_folder} for file : {file_name} & pattern : [{pattern}]")
            file_list = self.kube_master.machine_obj.get_files_in_path(
                folder_path=log_folder)
            for log_file in file_list:
                if file_name.lower() in log_file.lower():
                    self.log.info(
                        f"Log file Match found. start analysing pattern - [{pattern}] in file : {log_file}")
                    log_lines = self.kube_master.machine.read_file(
                        file_path=f"{log_file}",
                        search_term=pattern)
                    if len(log_lines) > 1:
                        log_lines = log_lines.split("\r\n")
                        self.log.info(
                            f"Matching line found for pattern : {len(log_lines)}")
                        output.extend(log_lines)
                    else:
                        self.log.info(
                            f"No line found with matching pattern for file - {log_file}")
        # if any log line matches, then remove the downloaded pod logs else
        # keep it for debugging
        if output:
            for log_folder in pod_log_folders:
                self.log.info(f"Removing log folder - {log_folder}")
                self.kube_master.machine.remove_directory(
                    directory_name=log_folder)
        return output
