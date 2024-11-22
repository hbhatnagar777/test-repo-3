# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for index server running on kubernetes

Classes : ClusterApiHelper & ClusterHelper are two different classes defined in this file

    ClusterApiHelper    -- helper class for creating data / managing collection on index server running on kubernetes

    ClusterHelper       --  helper class for creating & managing index server cluster in AKS

ClusterApiHelper:

    __create_solr_query()--  method to create solr query using provided params

    __custom_hook()     --  custom hook method to catch thread failures

    __report_hook()     --  prints thread failures caught so far

    dump_json()         --  dumps json in beautified format in logs

    make_request()      --  Sends http request to index server cluster

    get_cores()         --  returns loaded cores details from datacube controller

    get_servers()       --  returns solr pod details from datacube controller

    get_pvc()           --  returns pvc details from datacube controller

    get_routes()        --  returns collection information from datacube controller

    ping_core()         --  does ping check on the core in index server cluster

    ping_collection()   --  does ping check on the collection in index server cluster

    delete_core()       --  Deletes the core from index server cluster

    push_data()         --  Pushes data to collection on index server cluster

    generate_data()     --  Generates data for collection based on its type

    call_commit()       --  Calls commit on collection in index server cluster

    bulk_push_data()    --  Pushes scale data to collection in index server cluster

    bulk_push_data_thread() --  Pushes scale data(multi-threaded) to collection in index server cluster

    unload_collection()     --  Unloads collection from index server cluster

    delete_collection()     --  deletes the collection from index server cluster

    create_collection()     --  creates collection on index server cluster

    update_routes()         --  updates routing details for collection

    get_loaded_collection_stats()   --  returns the details for loaded collection in cluster

    search_collection()             --  Searches on collection in index server cluster

    get_all_collection_names()      --  returns all collection names from index server cluster

    random_load_collection()        --  loads collection randomly based on input

    get_cluster_stats()             --  returns the overall stats of index server cluster

    get_image_info_from_deployment() -  Returns image info from deployment details

ClusterHelper:

    create_cluster()                --  creates index server cluster on AKS

    delete_resource_group()         --  deletes the resource group in AKS

    set_cluster_ip_in_cs()          --  sets cluster ip in CS for Index server client

    remove_cluster_ip_in_cs()       --  removes cluster ip in CS for Index server client

    extract_image_info()            --  extracts image version info from yaml file

    get_cluster_ip_from_setup()     --  returns cluster ip from environment setup file

    update_test_status_json()       --  updates test status to result json file

    update_config_map()             --  Updates config map in yaml

    apply_yaml_do_rollout()         --  Applies yaml file and do rollout restart on deployment


"""
import os
import re
import threading
import time
import json
import random
from datetime import datetime, timedelta
from AutomationUtils import logger, commonutils
from AutomationUtils.config import get_config
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from AutomationUtils.database_helper import MSSQL
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.Performance.Utils.performance_helper import PerformanceHelper
from essential_generators import DocumentGenerator
from Kubernetes.HelmHelper import HelmHelper
from dynamicindex.utils import constants as dynamic_constants
from Kubernetes.akscluster_helper import AksClientHelper
from Kubernetes.indexserver import constants as ctrl_const
from Kubernetes.kubectl_helper import KubectlHelper
from Kubernetes import constants as kube_constants
_CONFIG_DATA = get_config().DynamicIndex.IndexServerCluster
_CS_CONFIG_DATA = get_config().SQL


class ClusterHelper:
    """Helper class to manage index server cluster in kubernetes"""

    def __init__(
            self,
            commcell_object):
        """Initialize the ClusterHelper class

            Args:

                commcell_object         (obj)       --  Instance of commcell class object

            ********* Please make sure we have inputs for "IndexServerCluster" dict in config.json *******

        """
        self._commcell = commcell_object
        self.log = logger.get_log()
        self.environment_file = os.path.join(
            AUTOMATION_DIRECTORY,
            "Temp",
            f"IS_Cluster_Setup_{self._commcell.commserv_client.client_name}.txt")
        self.result_json_file = os.path.join(
            AUTOMATION_DIRECTORY,
            "Temp",
            f"IS_Cluster_Results_{self._commcell.commserv_client.client_name}.json")
        ss_name_suffix = ""
        if 'windows' in self._commcell.commserv_client.os_info.lower():
            ss_name_suffix = ctrl_const.DB_FIELD_COMMVAULT
        conn_str = self._commcell.commserv_hostname + ss_name_suffix
        self.log.info(f"CS Sql connection String - {conn_str}")
        self._cs_db = MSSQL(conn_str,
                            _CS_CONFIG_DATA.Username,
                            _CS_CONFIG_DATA.Password,
                            ctrl_const.DB_FIELD_COMMSERV)
        self.log.info("MSSql object initialized to CS")
        self.az_master = AksClientHelper(
            self._commcell,
            machine_name=_CONFIG_DATA.AZMachine.name,
            user_name=_CONFIG_DATA.AZMachine.username,
            password=_CONFIG_DATA.AZMachine.password,
            service_principal={
                dynamic_constants.FIELD_APPID: _CONFIG_DATA.AzureAdServicePrincipals.appId,
                dynamic_constants.FIELD_PASSWORD: _CONFIG_DATA.AzureAdServicePrincipals.password,
                dynamic_constants.FIELD_TENANT: _CONFIG_DATA.AzureAdServicePrincipals.tenant},
            subscription_id=_CONFIG_DATA.AzureSubscription)
        self.log.info("Initialized AksClientHelper object")
        self.kube_master = KubectlHelper(
            self._commcell,
            machine_name=_CONFIG_DATA.KubectlMachine.name,
            user_name=_CONFIG_DATA.KubectlMachine.username,
            password=_CONFIG_DATA.KubectlMachine.password)
        self.log.info("Initialized KubectlHelper object")
        self.helm_master = HelmHelper(
            remote_machine=_CONFIG_DATA.KubectlMachine.name,
            user_name=_CONFIG_DATA.KubectlMachine.username,
            password=_CONFIG_DATA.KubectlMachine.password,
            repo_name=ctrl_const.IS_HELM_APP_NAME,
            repo_path=ctrl_const.TRAEFIK_URL)
        self.log.info("Initialized HelmHelper object")

    def apply_yaml_do_rollout(self, yaml_file):
        """Applies yaml file and do rollout restart on deployment


            Args:

                yaml_file       (str)       --  Yaml file path

            Returns:

                None
        """
        self.log.info(f"Going to apply yaml configuration via kubectl")
        self.kube_master.apply_yaml(yaml_file=yaml_file)
        self.log.info("do configuration rollout")
        self.kube_master.do_rollout_restart(
            resource=ctrl_const.RESOURCE_DEPLOYMENT,
            namespace=ctrl_const.IS_NAME_SPACE)
        self.log.info(
            f"Yaml applied. Wait for 3Min")
        time.sleep(180)

    def update_config_map(self, yaml_file, update_dict):
        """Updates config map in yaml file

            Args:

                yaml_file       (str)       --  Yaml file path

                update_dict     (dict)      --  Dict consisting of keys to be updated

            Returns:

                  str   --  Yaml file path  with updated config values
        """
        yaml_list = commonutils.convert_yaml_to_json(yaml_file=yaml_file)
        for each_obj in yaml_list:
            if each_obj[kube_constants.FIELD_KIND] == kube_constants.FIELD_CONFIG_MAP:
                _json_str = each_obj[kube_constants.FIELD_DATA][kube_constants.FIELD_CONFIG_JSON]
                _config_json = json.loads(_json_str)
                self.log.info(f"Config Got - {_config_json}")
                commonutils.dict_merge(dct=_config_json, merge_dct=update_dict)
                self.log.info(f"Config Updated - {_config_json}")
                each_obj[kube_constants.FIELD_DATA][kube_constants.FIELD_CONFIG_JSON] = json.dumps(
                    _config_json)
                break
        _yaml_content = commonutils.convert_json_to_yaml(input_list=yaml_list)
        updated_yaml_file = os.path.join(
            AUTOMATION_DIRECTORY,
            "Temp",
            f"IS_Cluster_yaml_{int(time.time())}.yaml")
        file_obj = open(updated_yaml_file, 'w')
        file_obj.write(_yaml_content)
        file_obj.close()
        self.log.info(f"Updated Yaml file created @ {updated_yaml_file}")
        return updated_yaml_file

    def update_test_status_json(self, test_id, status):
        """Updates test case results to json file

            Args:

                status  (str)   --  Test case result status

                test_id (str)   --  Test case ID

            Returns:

                None
        """
        perf_helper = PerformanceHelper(commcell_object=self._commcell)
        exists_json = {}
        if os.path.exists(self.result_json_file):
            exists_json = perf_helper.read_json_file(
                json_file=self.result_json_file)
        exists_json.update({test_id: status})
        perf_helper.dump_json_to_file(
            json_data=exists_json,
            out_file=self.result_json_file)

    def get_cluster_ip_from_setup(self):
        """Returns cluster ip from environment setup file

            Args:

                None

            Returns:

                Str,str --  Cluster IP Address & associated index server name

            Raises:

                Exception:

                    if failed to find environment setup file
        """
        self.log.info(f"Cluster Environment file - {self.environment_file}")
        if not os.path.exists(self.environment_file):
            raise Exception("Failed to find environment file with cluster ip")
        content = open(self.environment_file, "r").read()
        content = content.strip().split("_")
        return content[0], content[1]

    def extract_image_info(self, yaml_file):
        """extracts image info from yaml and returns the match object

            Args:

                yaml_file       (str)       --  Yaml file path

            Returns:

                Obj --  re match object

        """
        yaml_file_obj = open(yaml_file, "r")
        file_content = yaml_file_obj.read()
        images = re.findall(
            r'["\']?image["\']?\s*:\s*["\']?([^"\']+)["\']?',
            file_content)
        return images

    def set_cluster_ip_in_cs(
            self,
            index_server,
            cluster_ip,
            webserver,
            user_name,
            password):
        """sets cluster ip on CS for Index server

            Args:

                index_server     (str)      --  Index server name

                cluster_ip      (str)       --  Cluster ip address

                webserver       (str)       --  Webserver client name

                user_name       (str)       --  Webserver machine username

                password        (str)       --  Webserver machine password

            Returns:

                None

            Raises:

                Exception:

                    if failed to set cluster ip on cs
        """

        self.remove_cluster_ip_in_cs(
            index_server=index_server,
            cluster_ip=cluster_ip)
        self.log.info(
            f"Setting index server cluster additional setting for - {index_server}")
        _qscript = f"-sn QS_ConfigureK8sIndexServer -si '1' -si '{index_server}' -si '{cluster_ip}' -si '80'"
        self.log.info(_qscript)
        self._commcell._qoperation_execscript(_qscript)
        self.log.info("Cluster setting added for index server")
        self.log.info(f"Restarting iis on webserver - {webserver}")
        machine_obj = Machine(
            machine_name=webserver,
            username=user_name,
            password=password)
        machine_obj.restart_iis()
        time.sleep(600)
        self.log.info("IIS Restarted")
        self._commcell.refresh()

    def remove_cluster_ip_in_cs(
            self,
            index_server,
            cluster_ip,
            webserver=None,
            user_name=None,
            password=None):
        """removes cluster ip on CS for Index server

            Args:

                index_server     (str)      --  Index server name

                cluster_ip      (str)       --  Cluster ip address

                webserver       (str)       --  Webserver client name

                user_name       (str)       --  Webserver machine username

                password        (str)       --  Webserver machine password

            Returns:

                None

            Raises:

                Exception:

                    if failed to remove cluster ip on cs
        """
        self.log.info(
            f"Removing index server cluster additional setting for - {index_server}")
        _qscript = f"-sn QS_ConfigureK8sIndexServer -si '2' -si '{index_server}' -si '{cluster_ip}' -si '80'"
        self.log.info(_qscript)
        self._commcell._qoperation_execscript(_qscript)
        self.log.info("Cluster setting removed for index server")
        if webserver:
            self.log.info(f"Restarting iis on webserver - {webserver}")
            machine_obj = Machine(
                machine_name=webserver,
                username=user_name,
                password=password)
            machine_obj.restart_iis()
            time.sleep(600)
            self.log.info("IIS Restarted")
            self._commcell.refresh()

    def delete_resource_group(
            self,
            resource_group=ctrl_const.DEFAULT_IS_RESOURCE_GROUP):
        """deletes the resource group from aks cluster

            Args:

                resource_group          (str)       --  Resource group's name

            Returns:

                None
        """
        if self.az_master.group_exists(name=resource_group):
            self.log.info(
                f"Resource Group exists - {resource_group}. Deleting it")
            self.az_master.delete_group(name=resource_group)
        self.log.info(
            f"Successfully deleted the resource group - {resource_group}")

    def create_cluster(
            self,
            yaml_file,
            name=ctrl_const.DEFAULT_IS_CLUSTER_NAME,
            resource_group=ctrl_const.DEFAULT_IS_RESOURCE_GROUP,
            location=ctrl_const.DEFAULT_IS_AZURE_LOCATION,
            **kwargs):
        """Creates index server kubernetes cluster on azure and setup az/kubectl on machine

            Args:

                name            (str)       --  Cluster name

                resource_group  (str)       --  Resource group name

                location        (str)       --  Location to create cluster

                yaml_file       (str)       --  yaml file path on controller

            kwargs Attributes:

                node_count              (int)       --  Number of nodes in the Kubernetes node pool (Default:1)

                vm_size                 (str)       --  Size of Virtual Machines to create as Kubernetes nodes
                                                            (Default: standard_d16ads_v5)

                attach_acr              (str)       --  Grant the 'acrpull' role assignment to the ACR specified by name

                ssh                     (str)       --  ssh key value file path [Public key path or key contents to install on node VMs for SSH access]

                node_pool_name          (str)       --  Name of the node pool

                node_pool_label         (str)       --  Labels for nodepool

            Returns:

                str     --  External IP Address of cluster

            Raises:

                Exception:

                        if failed to create kubernetes cluster

                        if failed to find AZ or kubectl command line tools on machine

                        if AZ/Kubectl machine are not same

        """
        if _CONFIG_DATA.AZMachine.name.lower() != _CONFIG_DATA.KubectlMachine.name.lower():
            raise Exception(
                "Not a supported configuration. Use same machine for AZ/Kubectl")
        self.delete_resource_group(resource_group=resource_group)
        self.log.info(f"Going to create resource group - {resource_group}")
        self.az_master.create_group(
            group_name=resource_group,
            location=location)
        time.sleep(30)  # Sometimes resource group is not identified on azure
        self.log.info(f"Going to create AKS cluster on azure - {name}")
        if len(kwargs) == 0:
            self.log.info(f"Default configuration for cluster detected")
            self.az_master.create_cluster(
                name=name,
                resource_group=resource_group,
                attach_acr=ctrl_const.IS_ACR_NAME,
                ssh=_CONFIG_DATA.AzureSSHKeyFilePath,
                node_count=1,
                enable_autoscaler=False,
                vm_size=ctrl_const.CTRLR_NODE_VM_SIZE,
                node_pool_name=ctrl_const.CTRLR_NODE_POOL_NAME,
                node_pool_label=ctrl_const.CTRLR_NODE_POOL_LABEL
            )
        else:
            self.log.info(
                f"User configuration for cluster detected for VM sizing")
            self.az_master.create_cluster(
                name=name,
                resource_group=resource_group,
                attach_acr=ctrl_const.IS_ACR_NAME,
                ssh=_CONFIG_DATA.AzureSSHKeyFilePath,
                enable_autoscaler=False,
                ** kwargs)

        # configure app node pool
        self.log.info(f"Creating User node pool for hosting datacube app")
        self.az_master.create_nodepool(
            cluster_name=name,
            resource_group=resource_group,
            node_pool_name=ctrl_const.APP_NODE_POOL_NAME,
            node_vm_size=ctrl_const.NODE_VM_SIZE,
            node_count=1,
            labels=ctrl_const.APP_NODE_POOL_LABEL)
        self.log.info("Waiting for 3mins for cluster to resolved by azure DNS")
        time.sleep(180)
        self.log.info(f"Going to import AKS credentials into .kube/config")
        self.az_master.get_credentials(
            cluster_name=name,
            resource_group=resource_group,
            overwrite=True)
        self.log.info(f"Going to apply yaml configuration via kubectl")
        self.kube_master.apply_yaml(yaml_file=yaml_file)
        self.log.info("Going to create secret for docker registry")
        self.kube_master.create_secret_docker_registry(
            secret_name=_CONFIG_DATA.ImageSecrets.Name,
            server=_CONFIG_DATA.ImageSecrets.Server,
            user=_CONFIG_DATA.ImageSecrets.User,
            password=_CONFIG_DATA.ImageSecrets.Password,
            namespace=ctrl_const.IS_NAME_SPACE)
        # traefik configuration
        self.helm_master.cleanup_helm_app(
            helm_app_name=ctrl_const.IS_HELM_APP_NAME,
            namespace=ctrl_const.IS_NAME_SPACE)
        self.helm_master.add_helm_repo()
        self.helm_master.deploy_helm_app(
            helm_app_name=ctrl_const.IS_HELM_APP_NAME,
            namespace=ctrl_const.IS_NAME_SPACE,
            set_values=ctrl_const.TRAEFIK_VALUES_YAML)
        _traefik_yaml = os.path.join(
            AUTOMATION_DIRECTORY,
            "Temp",
            ctrl_const.DEFAULT_TRAEFIK_YAML_FILE)
        f = open(
            _traefik_yaml,
            "w")
        f.write(ctrl_const.DEFAULT_TRAEFIK_YAML)
        f.close()
        self.log.info(
            f"Going to apply yaml configuration via kubectl for traefik")
        self.kube_master.apply_yaml(
            yaml_file=_traefik_yaml)
        os.remove(_traefik_yaml)
        self.log.info(
            f"Yaml & Secret applied. Wait for 2Min")
        time.sleep(120)
        # fetch the cluster ip
        ip = self.kube_master.get_service(
            service_name=ctrl_const.TRAEFIK_SERVICE_NAME,
            name_space=ctrl_const.IS_NAME_SPACE)
        ip = ip[dynamic_constants.FIELD_STATUS][dynamic_constants.FIELD_LOADBALANCER][
            dynamic_constants.FIELD_INGRESS][0][dynamic_constants.FIELD_EXTERNAL_IP]
        if not ip:
            raise Exception("Failed to get index server cluster IP")
        return ip


class ClusterApiHelper:
    """Helper class to manage collection operations on index server cluster running in kubernetes"""

    def __init__(
            self,
            commcell_object, cluster_ip):
        """Initialize the ClusterApiHelper class

            Args:

                commcell_object         (obj)       --  Instance of commcell class object

                cluster_ip              (str)       --  Kubernetes cluster IP
        """
        self._commcell = commcell_object
        self.solr_url = f"http://{cluster_ip}/solr"
        self.admin_api_url = f"http://{cluster_ip}/solr/api/admin"
        self.ctrl_url = f"http://{cluster_ip}/dkubectrlr"
        self.collection_url = f"http://{cluster_ip}/solr/servlets/collection"
        self.log = logger.get_log()
        self._success_json = {
            "httpCode": 200,
            "errorCode": 0,
            "errorMsg": None,
            "response": True}
        self._get = "GET"
        self._post = "POST"
        self._commit_interval = 900  # in seconds
        self._commit_thread = None
        self._option_selector = OptionsSelector(commcell_object)
        self._thread_excp = []

    def __form_field_query(self, key, value):
        """
        Returns the query with the key and value passed
        Args:
                key(str)    -- key for forming the query
                value(str)  -- value for forming the query
            Returns:
                query to be executed against solr
        """
        query = None
        if value is None:
            query = f'&{key}'
        else:
            query = f'&{key}={str(value)}'
        return query

    def __create_solr_query(
            self,
            select_dict=None,
            attr_list=None,
            op_params=None):
        """Method to create the solr query based on the params
            Args:
                select_dict     (dictionary)     --  Dictionary containing search criteria and value
                                                     Acts as 'q' field in solr query

                attr_list       (set)            --  Column names to be returned in results.
                                                     Acts as 'fl' in solr query

                op_params       (dictionary)     --  Other params and values for solr query
                                                        (Ex: start, rows)

            Returns:
                The solr url based on params

            Raises:
                Exception:

                        if failed to form solr query
        """
        try:
            search_query = f'q='
            simple_search = 0
            if select_dict:
                for key, value in select_dict.items():
                    if isinstance(key, tuple):
                        if isinstance(value, list):
                            search_query += f'({key[0]}:{str(value[0])}'
                            for val in value[1:]:
                                search_query += f' OR {key[0]}:{str(val)}'
                        else:
                            search_query += f'({key[0]}:{value}'
                        for key_val in key[1:]:
                            if isinstance(value, list):
                                search_query += f' OR {key_val}:{str(value[0])}'
                                for val in value[1:]:
                                    search_query += f' OR {key_val}:{str(val)}'
                            else:
                                search_query += f' OR {key_val}:{value}'
                        search_query += ') AND '
                    elif isinstance(value, list):
                        search_query += f'({key}:{str(value[0])}'
                        for val in value[1:]:
                            search_query += f' OR {key}:{str(val)}'
                        search_query += ") AND "
                    elif key == "keyword":
                        search_query += "(" + value + ")"
                        simple_search = 1
                        break
                    else:
                        search_query = search_query + \
                            f'{key}:{str(value)} AND '
                if simple_search == 0:
                    search_query = search_query[:-5]
            else:
                search_query += "*:*"

            field_query = ""
            if attr_list:
                field_query = "&fl="
                for item in attr_list:
                    field_query += f'{str(item)},'
                field_query = field_query[:-1]
            if attr_list and 'content' in attr_list:
                field_query = f"{field_query}&exclude=false"

            ex_query = ""
            if not op_params:
                op_params = {'wt': "json"}
            else:
                op_params['wt'] = "json"
            for key, values in op_params.items():
                if isinstance(values, list):
                    for value in values:
                        ex_query += self.__form_field_query(key, value)
                else:
                    ex_query += self.__form_field_query(key, values)
            final_url = f'{search_query}{field_query}{ex_query}'
            return final_url
        except Exception as excp:
            raise Exception(
                f"Something went wrong while creating solr query - {excp}")

    def get_image_info_from_deployment(self, yaml_dict, container_name):
        """Returns image version by parsing yaml file

            Args:

                yaml_dict           (dict)      --  deployment details as json

                container_name      (str)       --  Container name whose version has to be fetched

            Returns:

                str --  Image version details. Returns "NA" if container not found
        """

        self.log.info(f"Going to find version info for container - {container_name}")
        for each_obj in yaml_dict[kube_constants.FIELD_ITEMS]:
            if each_obj[kube_constants.FIELD_KIND] == kube_constants.FIELD_DEPLOYMENT:
                containers = each_obj[kube_constants.FIELD_SPEC][kube_constants.FIELD_TEMPLATE][kube_constants.FIELD_SPEC][kube_constants.FIELD_CONTAINERS]
                for container in containers:
                    if container[kube_constants.FIELD_NAME] == container_name:
                        self.log.info(f"Image version found - {container[kube_constants.FIELD_IMAGE]}")
                        return container[kube_constants.FIELD_IMAGE]
        return "NA"

    def dump_json(self, input_json):
        """dumps given json in beautified format in logs

            Args:

                input_json          (dict)      --  dict which needs to de dumped in logs

            Returns:

                None
        """
        self.log.info(
            f"**************************************************************************")
        if input_json:
            self.log.info(json.dumps(input_json, indent=4, sort_keys=True))
        else:
            self.log.info("Nothing to dump... Empty JSON")
        self.log.info(
            f"**************************************************************************")

    def make_request(
            self,
            method,
            url,
            payload=None,
            headers=None,
            stream=False,
            files=None,
            **kwargs):
        """Makes the request of the type specified in the argument 'method' to index server cluster.

            Args:
                method      (str)           --  HTTP operation to perform

                    e.g.:

                    -   GET

                    -   POST

                    -   PUT

                    -   DELETE

                url         (str)           --  the web url or service to run the HTTP request on


                payload     (dict / str)    --  data to be passed along with the request

                    default: None


                headers     (dict)          --  dict of request headers for the request

                        if not specified we use default headers

                    default: None


                stream      (bool)          --  boolean specifying whether the request should get
                data via stream or normal get

                    default: False


                files       (dict)          --  file to upload in the form of

                        {
                            'file': open('report.txt', 'rb')
                        }

                    default: None

                Kwargs supported values:

                    remove_processing_info  (bool)      --  removes the processing instruction info from response.json()

            Returns:
                tuple:
                    (True, response)    -   in case of success

                    (False, response)   -   in case of failure

            Raises:

                Exception:
                    if the method passed is incorrect / not supported

                    if the number of attempts exceed

        """
        attempts = 3
        self.log.info(f"Calling Http [{method}] with Url [{url}]")
        while attempts > 0:
            flag, response = self._commcell._cvpysdk_object.make_request(method=method,
                                                                         url=url, payload=payload, attempts=attempts,
                                                                         headers=headers, stream=stream, files=files,
                                                                         **kwargs)
            attempts = attempts - 1
            if flag:
                if response.json():
                    self.log.info(
                        f"Finished Http [{method}] with url [{url}] & respone [{response.json()}]")
                    return response.json()
                else:
                    self.log.info("Invalid empty response")
                    return
            else:
                self.log.info("Http call failed. Retrying after 5 seconds")
                self.log.info(
                    f"Finished Http [{method}] with url [{url}] & error code : [{response.status_code}] Msg : [{response.content}]")
                time.sleep(5)
        raise Exception(
            f"Http call failed even after multiple retries for url : {url}")

    def get_cores(self, dump_in_log=False):
        """returns loaded cores details from index server cluster

            Args:

                dump_in_log     (bool)      --   Specifies whether to dump this info in log or not

            Returns:

                dict -- containing cores details

        """
        url = f"{self.ctrl_url}/cores"
        response = self.make_request(method=self._get, url=url)
        if dump_in_log:
            self.dump_json(input_json=response)
        return response

    def get_routes(self, dump_in_log=False):
        """returns collection route details from index server cluster

            Args:

                dump_in_log     (bool)      --   Specifies whether to dump this info in log or not

            Returns:

                dict -- containing cores details

        """
        url = f"{self.ctrl_url}/routes"
        response = self.make_request(method=self._get, url=url)
        if dump_in_log:
            self.dump_json(input_json=response)
        return response

    def get_servers(self, dump_in_log=False):
        """returns solr pod details from datacube controller

            Args:

                dump_in_log     (bool)      --   Specifies whether to dump this info in log or not

            Returns:

                dict    --  containing server pod details
        """

        url = f"{self.ctrl_url}/servers"
        response = self.make_request(method=self._get, url=url)
        if dump_in_log:
            self.dump_json(input_json=response)
        return response

    def get_pvc(self, dump_in_log=False):
        """returns loaded pvc details from datacube controller

            Args:

                dump_in_log     (bool)      --   Specifies whether to dump this info in log or not

            Returns:

                dict    --  containing pvc details

        """
        url = f"{self.ctrl_url}/volumes"
        response = self.make_request(method=self._get, url=url)
        if dump_in_log:
            self.dump_json(input_json=response)
        return response

    def ping_core(self, name):
        """does ping check on the core in index server cluster

            Args:

                name        (str)       --  Name of the core

            Returns:

                None

            Raises:

                Exception:

                    if failed to do ping
        """
        url = f"{self.solr_url}/{name}/select?q=*:*&rows=0&wt=json"
        response = self.make_request(method=self._get, url=url)
        num_found = int(response[ctrl_const.FIELD_RESPONSE]
                        [ctrl_const.FIELD_NUMFOUND])
        if not num_found >= 0:
            raise Exception(f"Ping check failed for core - {name}")

    def ping_collection(self, name, do_search=False):
        """does ping check on the collection in index server cluster

            Args:

                name        (str)       --  Name of the collection

                do_search   (bool)      --  Specifies whether to do searches on collection in index server or not after ping

            Returns:

                None

            Raises:

                Exception:

                    if failed to do ping
        """
        url = f"{self.solr_url}/{name}/admin/ping"
        response = self.make_request(method=self._get, url=url)
        if response[ctrl_const.FIELD_RESPONSE_HEADER][ctrl_const.FIELD_STATUS] != 0:
            raise Exception(f"Ping check failed for collection - {name}")
        if do_search:
            self.search_collection(name=name)

    def delete_core(self, name):
        """Deletes the core from index server cluster

            Args:

                name            (str)       --  Name of the core

            Returns:

                None

            Raises:

                Exception:

                    if failed to delete the core
        """
        url = f"{self.collection_url}?type=DELETECORE&corename={name}"
        response = self.make_request(method=self._get, url=url)
        if response != self._success_json:
            raise Exception(
                f"Solr core deletion failed for {name}. Please check logs")

    def push_data(self, data, collection_name):
        """Pushes data to collection on index server cluster

            Args:

                data            list(dict)      --  List of dict containing generated data

                collection_name (str)           --  collection name to which we wanted to push data

            Returns:

                None

            Raises:

                Exception:

                    if failed to push doc
        """
        url = f"{self.solr_url}/{collection_name}/update"
        attempt = 3
        response = None
        while attempt > 0:
            attempt = attempt - 1
            try:
                response = self.make_request(
                    method=self._post, url=url, payload=data, headers={
                        "Content-Type": "application/json; charset=UTF-8"})
                break
            except Exception as ep:
                self.log.info("Something went wrong during connectivity. Attempting again after a min")
                time.sleep(60)
                response = None
                continue
        if not response:
            raise Exception(f"Update request failed for collection due to connection error - {collection_name}")
        if response and response['responseHeader']['status'] != 0:
            raise Exception(
                f"Update request failed for collection - {collection_name}")

    def generate_data(
            self,
            type='File',
            doc_count=2,
            with_content=False,
            **kwargs):
        """Generates data based on type specified and returns it as json

            Args:

                type        (str)       --  Data type to generate

                                        Supported values :

                                            File - File system data

                                            Exchange - Email data

                doc_count   (int)       --  total document to be generated

                with_content    (bool)  --  denotes whether content field will be populated or not

            kwargs:

                doc_gen     (obj)       --  Document Generator object(it is needed when with_content flag is True)

            Returns:

                  dict -- containing generated data

        """
        if type == 'File':
            if with_content:
                if not kwargs.get('doc_gen', None):
                    raise Exception(
                        "Document Generator object needed. Please pass it")
            min_year = 1970
            max_year = 2023
            start = datetime(min_year, 1, 1, 00, 00, 00)
            years = max_year - min_year + 1
            end = start + timedelta(days=365 * years)
            self.log.info(f"Generating File system data - {doc_count}")
            output = []
            while doc_count:
                ext = random.choice(dynamic_constants.FILE_TYPES_DATA_GEN)
                file_name = f"Automation_{random.randint(0,922337203685477580)}.{ext}"
                folder = f"E:\\Data_{random.randint(0,922337203685477580)}"
                req_json = {
                    "contentid": f"ecd{random.randint(0,9)}cc4518334ba7{random.randint(0,9)}506ab0{random.randint(0,10)}2eccf6ee{random.randint(0,922337203685477580)}!c97{random.randint(0,10)}fc777165{random.randint(0,10)}f6b585fee0{random.randint(0,9)}1324e3c1{random.randint(0,922337203685477580)}",
                    "Size": random.randint(0, 922337203685477580),
                    "FileName": file_name,
                    "FolderName": folder,
                    "Url": f"{folder}\\{file_name}",
                    "ModifiedTime": (start + (end - start) * random.random()).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "CommcellNumber": random.randint(1000000, 9223372),
                    "FileChangeTime": (start + (end - start) * random.random()).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "ClientId": random.randint(0, 2000),
                    "SizeOnDisk": random.randint(0, 922337203685477580),
                    "IsFile": 1,
                    "DocumentType": 1,
                    "BackupStartTime": (start + (end - start) * random.random()).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "ApplicationId": random.randint(0, 50000),
                    "DateAdded": (start + (end - start) * random.random()).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "AppType": 33,
                    "IsVisible": True,
                    "IsProtected": False,
                    "IsEncrypted": False,
                    "ParentGUID": f"14160e45fa06eb5e15bdabaffd6605c4{random.randint(0,922337203685477580)}",
                    "CAState": 0,
                    "AchiveFileId": random.randint(0, 50000),
                    "ArchiveFileOffset": random.randint(0, 922337203685477580),
                    "ApplicationGUID": f"CCF26F17-ADA8-4C4B-92DF-0AB26A69BD26{random.randint(0,20)}",
                    "FileNameModifiedTimeSizeHash": f"2ec9c75002006adf5d18cc5052fc0da8{random.randint(0,922337203685477580)}",
                    "BackupSetGUID": f"BBDF4C37-5217-4846-9439-9FBE1B0A016C{random.randint(0,20)}",
                    "CVObjectGUID": f"ecd5cc{random.randint(1111111,9999999)}ba78506ab062eccf6ee",
                    "ClientName": f"dikube{random.randint(0,50)}",
                    "FileNameModifiedTimeHash": f"feb897244992a1b14f57d2fca594a823{random.randint(0,922337203685477580)}",
                    "ClientGUID": f"ACB56956-E5A9-4B81-B92E-FDF12D53C3B9{random.randint(0,50)}",
                    "CVTurboGUID": f"c979fc7771656f6b585fee021324e3c1{random.randint(0,922337203685477580)}",
                    "FileExtension": ext,
                    "ItemState": 1,
                    "ContentIndexingStatus": "0" if not with_content else "1",
                    "JobId": random.randint(0, 1000)}
                if with_content:
                    req_json['content'] = kwargs.get('doc_gen').paragraph(
                        min_sentences=25, max_sentences=random.randint(100, 10000))
                output.append(req_json)
                doc_count = doc_count - 1
            return output

    def call_commit(self, collection_name):
        """Calls collection commit in index server cluster

              Args:

                collection_name         (str)       --  Collection name

            Returns:

                None

            Raises:

                Exception:

                    if failed to call commit
        """
        url = f"{self.solr_url}/{collection_name}/update?commit=true"
        response = self.make_request(method=self._get, url=url)
        if response[ctrl_const.FIELD_RESPONSE_HEADER][ctrl_const.FIELD_STATUS] != 0:
            raise Exception(
                f"commit failed for collection - {collection_name}")
        self.log.info(
            f"Successfully called commit for collection - {collection_name}")

    def bulk_push_data(
            self,
            collection_name,
            doc_count,
            doc_type,
            batch_size=50,
            thread_count=1,
            create_collection=False,
            **kwargs):
        """Pushes scale data to index server cluster

            Args:

                collection_name         (str)       --  Name of the collection

                doc_count               (str)       --  Total document to push

                doc_type                (str)       --  Data type which needs to be generated

                batch_size              (str)       --  Total documents in each batch (Default:50)

                thread_count            (int)       --  No of threads to run (default:1)

                create_collection       (bool)      --  denotes whether to create collection or not

            kwargs arguments:

                num_cores   (int)       --  No of cores to be created for collection

                config_set  (str)       --  Config set for core

                routing     (list)      --  Routing details for cores

                with_content  (bool)    -- Denotes whether to add content field or not

            Returns:

                None

            Raises:

                Exception:

                    if failed to push documents
        """
        threads = []
        if thread_count > doc_count:
            thread_count = 1
        if create_collection:
            self.create_collection(
                name=collection_name, core_name_prefix=collection_name, config_set=kwargs.get(
                    'config_set', 'fsindexV2'), num_cores=kwargs.get(
                    'num_cores', 8), routing=kwargs.get(
                    'routing', None))
        # make sure collection is pingable before starting data generation
        self.ping_collection(name=collection_name)
        docs_per_thread = int(doc_count / thread_count)

        for i in range(thread_count):
            push_thread = threading.Thread(
                target=self.bulk_push_data_thread,
                args=(
                    collection_name,
                    docs_per_thread,
                    doc_type,
                    batch_size,
                    kwargs.get(
                        'with_content',
                        False)))
            push_thread.name = f"PushThread_{i}"
            push_thread.start()
            threads.append(push_thread)

        # schedule the commit thread
        self.log.info(
            f"Starting commit scheduler with interval [{self._commit_interval}] seconds")
        self._commit_thread = threading.Timer(
            self._commit_interval, self.call_commit, args=(
                collection_name,))
        self._commit_thread.start()
        while len(threads) > 0:
            for _thread in threads:
                # join and wait for graceful exit of child thread
                self.log.info("Executing Join for thread : %s", _thread)
                _thread.join()
                self.log.info(f"{_thread.getName()} stopped gracefully")
                # thread came down gracefully. remove thread object from the list
                threads.remove(_thread)
                self.log.info(f"Removed Thread from stack : {_thread.getName()}")
        self.log.info("Cancelling the commit scheduler thread")
        if self._commit_thread:
            self._commit_thread.cancel()
        self.call_commit(collection_name=collection_name)
        self.log.info(
            f"Bulk data generation finished for collection -[{collection_name}] with doc count - [{doc_count}]")

    def bulk_push_data_thread(
            self,
            collection_name,
            doc_count,
            doc_type,
            batch_size=50,
            with_content=False):
        """Pushes scale data to index server cluster

            Args:

                collection_name         (str)       --  Name of the collection

                doc_count               (str)       --  Total document to push

                doc_type                (str)       --  Data type which needs to be generated

                batch_size              (str)       --  Total documents in each batch (Default:50)

                with_content             (bool)      --  Denotes whether to add content field or not

            Returns:

                None

            Raises:

                Exception:

                    if failed to push documents
        """
        start_time = time.time()
        batch = 1
        processed = 0
        _doc_gen = None
        if with_content:
            _doc_gen = DocumentGenerator()
            self.log.info(
                "Initializing Document Generator Word/sentence Caches")
            _doc_gen.init_word_cache(10000)
            _doc_gen.init_sentence_cache(100000)
        if doc_count < batch_size:
            batch_size = doc_count
        self.log.info(
            f"Generating Total data [{doc_count}] of type [{doc_type}]")
        while True:
            self.log.info(
                f"Processing Batch [{batch}] containing [{batch_size}] documents")
            if with_content and batch % 100 == 0:
                self.log.info(
                    "Re_Initializing Document Generator Word/sentence Caches")
                _doc_gen.word_cache = []
                _doc_gen.init_word_cache(10000)
                _doc_gen.sentence_cache = []
                _doc_gen.init_sentence_cache(100000)
            # check if batch size is going beyond total doc count needed. In
            # that case, reduce the batch size accordingly
            if batch_size > doc_count - processed:
                batch_size = doc_count - processed
            docs = self.generate_data(
                type=doc_type,
                doc_count=batch_size,
                with_content=with_content,
                doc_gen=_doc_gen)
            self.push_data(data=docs, collection_name=collection_name)
            batch = batch + 1
            processed = processed + batch_size
            if processed >= doc_count:
                end_time = time.time()
                self.log.info(
                    f"Finished Processing for type[{doc_type}] and doc count [{doc_count}]")
                break
        self.log.info(
            f'Going down gracefully. Total Execution time - [{time.strftime("%H:%M:%S", time.gmtime(end_time-start_time))}]')

    def unload_collection(self, collection_name):
        """unloads the collection from controller index server

            Args:

                collection_name         (str)       --  Name of the collection to be unloaded

            Returns:

                None

            Raises:

                Exception:

                    if failed to unload collection
        """
        url = f"{self.ctrl_url}/unloadcollection?cvCollection={collection_name}"
        response = self.make_request(method=self._get, url=url)
        if response != self._success_json:
            raise Exception(
                f"Solr unload-collection update failed for {collection_name}. Please check logs")
        self.log.info(f"{collection_name} unloaded successfully")

    def delete_collection(self, name):
        """Deletes cvsolr collection on kubernetes index server

                    Args:

                        name            (str)       --  Name of the collection


                    Returns:

                        None
        """
        _collections = self.get_routes()
        for _collection in _collections:
            if name == _collection[ctrl_const.FIELD_COLLECTION_NAME]:
                _cores = _collection[ctrl_const.FIELD_CORES]
                for _core in _cores:
                    self.delete_core(name=_core[ctrl_const.FIELD_NAME])
        self.log.info(f"Deleted the collection successfully - {name}")

    def create_collection(
            self,
            name,
            core_name_prefix,
            config_set,
            num_cores=8,
            routing=None):
        """Creates cvsolr collection on kubernetes index server

            Args:

                name            (str)       --  Name of the collection

                core_name_prefix    (str)   --  Core name prefix to be used

                config_set      (str)       --  solr config to be used. Eg:- fsindexV2

                num_cores       (int)       --  No of cores to create in that collection

                routing         (list)      --  list containing routing hash for cores in this collection

                                                    Default : None uses below routing

                {"0-1fffffff", "80000000-9fffffff", "20000000-3fffffff", "a0000000-bfffffff", "c0000000-dfffffff", "40000000-5fffffff", "e0000000-ffffffff", "60000000-7fffffff"}

            Returns:

                None

        """
        if not routing:
            routing = [
                "0-1fffffff",
                "80000000-9fffffff",
                "20000000-3fffffff",
                "a0000000-bfffffff",
                "c0000000-dfffffff",
                "40000000-5fffffff",
                "e0000000-ffffffff",
                "60000000-7fffffff"]
        index = 0
        while index < num_cores:
            core_name = f"{core_name_prefix}_shards_{index}"
            url = f"{self.collection_url}?type=CREATECORE&corename={core_name}&configSet={config_set}&cvCollection={name}&routeValue={routing[index]}"
            response = self.make_request(method=self._get, url=url)
            if response != self._success_json:
                raise Exception(
                    f"Solr collection creation failed for {name}. Please check logs")
            index = index + 1
        self.log.info(f"Solr collection got created successfully")
        self.update_routes(collection_name=name)

    def update_routes(self, collection_name):
        """calls update routes api for given collection in index server cluster

            Args:

                collection_name         (str)       --  Collection name

            Returns:

                None

            Raises:

                Exception:

                    if failed to update route info
        """
        url = f"{self.admin_api_url}/cvroutes/update?cvCollection={collection_name}"
        response = self.make_request(method=self._get, url=url)
        if response != self._success_json:
            raise Exception(
                f"Solr collection Routing update failed for {collection_name}. Please check logs")
        self.log.info(
            f"Successfully update routing details for collection - {collection_name}")

    def get_loaded_collection_stats(self, dump_in_log=False):
        """returns loaded collection details from cluster

            Args:

                dump_in_log     (bool)      --   Specifies whether to dump this info in log or not

            Returns:

                dict    --  containing loaded collection details
        """
        output = {}
        collections = self.get_routes()
        for collection in collections:
            core_servers = []
            # server id should be mapped for collection and cores should be
            # greater than zero
            if collection[ctrl_const.FIELD_INGRESS_SERVER_ID].strip() and len(
                    collection[ctrl_const.FIELD_CORES]) > 0:
                name = collection[ctrl_const.FIELD_COLLECTION_NAME]
                size = 0
                docs = 0
                output[name] = collection
                output[name][ctrl_const.FIELD_TOTAL_CORES] = len(
                    collection[ctrl_const.FIELD_CORES])
                for core in collection[ctrl_const.FIELD_CORES]:
                    if core[ctrl_const.FIELD_SERVER_ID] not in core_servers:
                        core_servers.append(core[ctrl_const.FIELD_SERVER_ID])
                    size = size + int(core[ctrl_const.FIELD_CORE_SIZE])
                    docs = docs + int(core[ctrl_const.FIELD_CORE_DOCS])
                output[name][ctrl_const.FIELD_ALL_CORE_SERVER_ID] = core_servers
                output[name][ctrl_const.FIELD_TOTAL_CORE_DOCS] = docs
                output[name][ctrl_const.FIELD_TOTAL_CORE_DOCS_STR] = self._option_selector.convert_no(
                    number=docs)
                output[name][ctrl_const.FIELD_TOTAL_CORE_SIZE_STR] = self._option_selector.convert_size(
                    size_bytes=size)
                output[name][ctrl_const.FIELD_TOTAL_CORE_SIZE] = size
        if dump_in_log:
            self.dump_json(input_json=output)
        return output

    def search_collection(
            self,
            name,
            select_dict=None,
            attr_list=None,
            op_params=None):
        """does searches on collection and returns response

            Args:

                name            (str)            --  Name of the collection

                select_dict     (dictionary)     --  Dictionary containing search criteria and value
                                                     Acts as 'q' field in solr query

                attr_list       (set)            --  Column names to be returned in results.
                                                     Acts as 'fl' in solr query

                op_params       (dictionary)     --  Other params and values for solr query
                                                        (Ex: start, rows)

            Returns:

                dict    --  containing solr collection response

            Raises:

                Exception:

                    if failed to do search on cluster

        """
        solr_url = f"{self.solr_url}/{name}/select?{self.__create_solr_query(select_dict, attr_list, op_params)}"
        response = self.make_request(method=self._get, url=solr_url)
        if ctrl_const.FIELD_RESPONSE in response and ctrl_const.FIELD_NUMFOUND in response[
                ctrl_const.FIELD_RESPONSE]:
            return response
        raise Exception(
            f"Something went wrong while querying solr - {response} for collection - {name}")

    def get_all_collection_names(self):
        """returns all the collection name from cluster

            Args:

                None

            Returns:

                list    --  containing collection names
        """
        output = []
        collections = self.get_routes()
        for collection in collections:
            output.append(collection[ctrl_const.FIELD_COLLECTION_NAME])
        return output

    def random_load_collection(
            self,
            collection_count,
            do_search=False,
            do_parallel=False):
        """loads random collection from available collection in index server cluster

            Args:

                collection_count        (int)       --  No of collection to load

                do_search               (bool)      --  Specifies whether to do searches or not after load

                do_parallel             (bool)      --  specifies whether doing load in parallel or sequential

            Returns:

                list    --   Successfully loaded collection list

            Raises:

                Exception:

                    if failed to load collection
        """
        output = []
        collection_names = self.get_all_collection_names()
        if collection_count > len(collection_names):
            raise Exception(
                "Collection load count is greater than available collection")
        collection_names = random.sample(
            population=collection_names, k=collection_count)
        self.log.info(
            f"Selected random collection for loading - {collection_names}")
        if not do_parallel:
            for collection_name in collection_names:
                self.log.info(
                    f"Starting for loading collection - {collection_name} with do Search : [{do_search}]")
                try:
                    self.ping_collection(
                        name=collection_name, do_search=do_search)
                    output.append(collection_name)
                except Exception:
                    self.log.info(
                        f"Failed to load collection - {collection_name}")
                    continue
        else:
            self.log.info("Do Parallel Flag set for loading collection")
            threads = []
            # set custom hook for child threads. Clear the global thread
            # exception list before that
            self._thread_excp = []
            threading.excepthook = self.__custom_hook
            for collection_name in collection_names:
                self.log.info(
                    f"Starting Thread for loading collection - {collection_name} with do Search : [{do_search}]")
                try:
                    ping_thread = threading.Thread(
                        target=self.ping_collection, args=(
                            collection_name, do_search))
                    ping_thread.name = f"PingThread_{collection_name}"
                    ping_thread.start()
                    threads.append(ping_thread)
                except Exception:
                    self.log.info(
                        f"Failed to load collection - {collection_name}")
                    continue
            for _thread in threads:
                # join and wait for graceful exit of child thread
                self.log.info("Executing Join for thread : %s", _thread)
                _thread.join()
                self.log.info(f"{_thread.getName()} stopped gracefully")
            self.__report_hook()
            for collection_name in collection_names:
                found = False
                for excp in self._thread_excp:
                    if collection_name in excp:
                        self.log.info(
                            f"Collection present in Exception Thread list - {collection_name}")
                        found = True
                        break
                if not found:
                    output.append(collection_name)
        return output

    def __custom_hook(self, args):
        """custom hook method to catch thread failures"""
        self.log.info(f'Thread failed: {args.exc_value}')
        self._thread_excp.append(str(args.exc_value))

    def __report_hook(self):
        """reports thread exception caught so far in logs"""
        self.log.info(
            f"**************************************************************************")
        self.log.info(
            f"Total exception caught in threading - {len(self._thread_excp)}. Details as below(if any)")
        for each_excp in self._thread_excp:
            self.log.info(each_excp)
        self.log.info(
            f"**************************************************************************")

    def get_cluster_stats(self):
        """Returns the overall stats of index server cluster

            Args:

                None

            Returns:

                dict    --  Containing index server stats

            Raises:

                None
        """
        output = {}
        pvcs = self.get_pvc()
        output[ctrl_const.FIELD_TOTAL_PVC] = len(pvcs)
        docs = 0
        capcity = 0
        used = 0
        cores = 0
        stats = {}
        # compute pvc stats
        for pvc in pvcs:
            stats.update({pvc[ctrl_const.FIELD_PVC_NAME]: {
                ctrl_const.FIELD_PVC_CAPACITY: self._option_selector.convert_size(
                    size_bytes=pvc[ctrl_const.FIELD_PVC_CAPACITY]),
                ctrl_const.FIELD_PVC_USED: self._option_selector.convert_size(
                    size_bytes=pvc[ctrl_const.FIELD_PVC_USED]),
                ctrl_const.FIELD_TOTAL_CORES_IN_PVC: len(pvc[ctrl_const.FIELD_CORES])
            }})
            capcity = capcity + pvc[ctrl_const.FIELD_PVC_CAPACITY]
            used = used + pvc[ctrl_const.FIELD_PVC_USED]
            cores = cores + len(pvc[ctrl_const.FIELD_CORES])
        output[ctrl_const.FIELD_TOTAL_PVC_CAPACITY] = self._option_selector.convert_size(
            size_bytes=capcity)
        output[ctrl_const.FIELD_TOTAL_PVC_USED] = self._option_selector.convert_size(
            size_bytes=used)
        output[ctrl_const.FIELD_TOTAL_CORES_IN_PVC] = cores
        output[ctrl_const.FIELD_PVC_STATS] = stats
        # compute core document stats
        collections = self.get_routes()
        for collection in collections:
            for core in collection[ctrl_const.FIELD_CORES]:
                docs = docs + int(core[ctrl_const.FIELD_CORE_DOCS])
        output[ctrl_const.FIELD_TOTAL_DOCS] = self._option_selector.convert_no(
            number=docs)
        return output
