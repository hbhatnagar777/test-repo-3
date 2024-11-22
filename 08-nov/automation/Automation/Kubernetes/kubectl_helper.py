# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for kubectl command line operations for kubernetes cluster

KubectlHelper:

    __init__()                                  --  Initialize the KubectlHelper object

    _get_version_info()                         --  gets kubectl version info

    _remove_empty_in_list()                     --  removes empty string from list

    _process_table_response()                   --  process table output of kubectl and returns it as dict

    _monitor_metrics_thread()                   --  Monitors pod/node metrics and stores it in csv file

    _write_csv()                                --  Writes pods/node metrics to csv file

    _collect_pod_metrics()                      --  collects pods metrics

    _collect_node_metrics()                     --  collects node metrics

    _setup_report()                             --  Setup automation pod report on CRE

    _setup_performance_datasource()             --  Setup performance open datasource on cs

     get_pods()                                 --  returns the POD details

     get_nodes()                                --  returns the NODE details

     get_service()                              --  returns the service details

     get_top_pod()                              --  returns the POD CPU/Memory details

     get_top_node()                             --  returns the node CPU/Memory Details

     delete_deployment_app()                    --  deletes the deployment apps on kubernetes

     apply_yaml()                               --  apply yaml configuration file to kubernetes

     convert_yaml_to_json()                     --  converts yaml file to json

     download_extracting_yaml()                 --  downloads extracting cluster yaml file from github

     monitor_pod()                              --  Monitors pod's auto scale up & down for specified time interval

     run_cmd_on_pod()                           --  Executes command on given pod in the cluster

     recycle_cv_srv_on_pod()                    --  Recycles commvault services running on POD

     get_folder_or_file_from_pod()              --  Copies folder or file from given pod to local machine

     get_stdout_logs()                          --  gets stdout logs from pod

     do_rollout_restart()                       --  does rollout restart for resource on cluster

     monitor_hpa()                              --  Monitors horizontal POD autoScaler

     create_secret_docker_registry()            --  Creates secret key for docker registry

     monitor_pod_metrics()                      --  Monitors the POD metrics and writes to CSV file

     monitor_node_metrics()                     --  Monitors the NODE metrics and writes to CSV file

     analyze_metrics()                          --  Analyzes metrics folder and returns min/max stats for pod/node

     get_deployments()                          --  returns deployment details

     get_deployment_image()                     --  returns the image details of deployments

     set_deployment_image()                     --  sets the new image to the deployments

     check_deployment_status()                  --  Checks for readiness status of deployment replicas

     scale_deployment()                         --  Scale up/down the replicas count for deployment


Attributes:

    **client_version**      --  Returns dict containing kubectl client version info

    **server_version**      --  Returns dict containing kubectl server version info

    **machine**             --  Returns machine object of kubectl installed machine

    **stop_monitor_threads** -- Returns monitor threads stop flag status

"""
import csv
import json
import os
import re
import threading
import time
from datetime import timedelta, datetime

import pandas

from AutomationUtils import logger, commonutils
from AutomationUtils.Performance.Utils.constants import JobTypes, GeneralConstants
from AutomationUtils.Performance.reportbuilder import ReportBuilder
from AutomationUtils.config import get_config
from AutomationUtils.database_helper import MSSQL
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from Kubernetes import constants as kuber_constants
from Web.API.cc import Reports
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.index_server_helper import IndexServerHelper

_CS_CONFIG_DATA = get_config().SQL
_PERF_CONFIG_DATA = get_config().DynamicIndex.PerformanceStats


class KubectlHelper:
    """ contains helper class for kubectl command line operations for kubernetes cluster"""

    def __init__(self, commcell_object, machine_name, user_name, password):
        """Initialize KubectlHelper class

                Args:

                    commcell_object     (obj)   --  Object of class Commcell

                    machine_name        (str)   --  Name of machine where kubectl is installed

                    user_name           (str)   --  User name to access machine

                    password            (str)   --  user login password
        """
        self.commcell = commcell_object
        self.log = logger.get_log()
        self.machine_obj = None
        self.version_info = None
        self.machine_obj = Machine(machine_name=machine_name, username=user_name, password=password)
        self.version_info = self._get_version_info()
        if not self.version_info:
            raise Exception("Please check whether kubectl command line tool is installed on this machine")
        self.options_obj = OptionsSelector(self.commcell)
        self.local_machine_obj = Machine()
        self.stop_threads = False
        self.threads = []

    def _setup_report(self, build_id):
        """Setup automation report on CRE

                Args:

                    build_id        (int)       --  Unique automation run id

                Returns:

                    None

                Raises:

                    Exception:

                        If failed to import report in CRE

        """
        _report_builder = ReportBuilder(
            commcell_object=self.commcell,
            job_id=None,
            job_type=JobTypes.TIME_BASED_JOB_MONITORING,
            use_data_source=False, build_id=str(build_id))
        _report_builder.import_report()

    def _setup_performance_datasource(self):
        """Setup performance data source on the CS

            Args:

                None

            Returns:

                None

            Raise:

                Exception if it fails to configure open datasource

        """
        data_source_name = kuber_constants.AUTOMATION_POD_METRICS_TBL
        if not self.commcell.datacube.datasources.has_datasource(data_source_name):
            self.log.info(f"Creating Open data source for POD metrics Storage - {data_source_name}")
            index_server_helper = IndexServerHelper(self.commcell, _PERF_CONFIG_DATA.Index_Server)
            ds_helper = DataSourceHelper(self.commcell)
            self.log.info("Index server/Data Source helper initialised")
            index_server_helper.update_roles(index_server_roles=[kuber_constants.ROLE_DATA_ANALYTICS])
            ds_helper.create_open_data_source(
                data_source_name=data_source_name,
                index_server_name=_PERF_CONFIG_DATA.Index_Server)
            ds_helper.update_data_source_schema(data_source_name=data_source_name,
                                                field_name=kuber_constants.POD_DATA_SOURCE_COLUMN,
                                                field_type=kuber_constants.POD_DATA_SOURCE_COLUMN_TYPES,
                                                schema_field=kuber_constants.SCHEMA_FIELDS)
            self.log.info(f"POD level Performance - Open DataSource created successfully")
        self.log.info(f"POD level Performance datasource setup completed")

    def _get_version_info(self):
        """Returns kubernetes version info

            Args:

                None

            Returns:

                dict    --  containing kubernetes client/server version info details

            Raises:

                Exception:

                    if failed to get version info

        """
        output_json = None
        cmd = f"kubectl version --output=json"
        output = self.machine_obj.execute_command(command=cmd)
        # Handle no kubernetes command line exe found on machine
        if len(output.formatted_output) == 0:
            raise Exception("Failed to get version info from kubectl command")
        try:
            output_json = json.loads(output.output)
        except Exception:
            raise Exception("Failed to get proper response for version")
        return output_json

    def _remove_empty_in_list(self, input_list):
        """removes empty string from list

            Args:

                input_list          (list)      --  List of string elements

            Returns:

                list    --  filetered list by removing empty strings

            Raises:

                None
        """
        return list(filter(None, input_list))

    def _process_table_response(self, output):
        """Process table output of kubectl command and return it as dict

            Args:

                output          (obj)       --  Output class object

            Returns:

                dict    --   containing details

            Raises:

                Exception:

                    if failed to process table info output
        """
        pod_usage = {}
        if '\r\n' in output.output:
            all_rows = output.output.split("\r\n")
        else:
            all_rows = output.output.split("\n")
        all_rows = self._remove_empty_in_list(input_list=all_rows)
        header = all_rows[0].split(" ")
        header = self._remove_empty_in_list(input_list=header)
        del all_rows[0]  # remove header so we have only POD details
        for pod in all_rows:
            pod_details = pod.split(" ")
            pod_details = self._remove_empty_in_list(input_list=pod_details)
            index = 0
            temp_dict = {kuber_constants.KEY_POD_NAME: pod_details[0]}
            for item in header:
                temp_dict.update({item: pod_details[index]})
                index = index + 1
            pod_usage[pod_details[0]] = temp_dict
        return pod_usage

    def get_pods(
            self,
            namespace=None,
            status=None,
            ready_only=False,
            **kwargs):
        """returns the running POD details

            Args:

                namespace       (str)       --  Namespace name to get POD details
                                                                (Default:None)

                status          (str)       --  to filter pod based on status string provided
                                                                (Default:None)

                ready_only      (bool)      --  flag to filter out ready only pods in output
                                                                (Default : False)

            **kwargs options**

                selector        (str)       --  selector value

            Returns:

                list    --  Containing POD names

            Raises:

                Exception:

                    if failed to get POD details
        """
        cmd = "kubectl get pods -o=json"
        if namespace:
            cmd = f"{cmd} -n {namespace}"
        if status:
            cmd = f"{cmd} --field-selector status.phase={status}"
        if kwargs.get('selector'):
            cmd = f"{cmd} --selector={kwargs.get('selector')}"
        output = self.machine_obj.execute_command(cmd)
        self.log.info("Getting pod information by running command : %s ", str(cmd))
        pods_list = []
        if ready_only:
            self.log.info(f"ReadyOnly flag set. Drop POD whose containers are not in ready state")
        try:
            if output.exception_message:
                raise Exception(f"Failed to get pod details - {output.exception_message}")
            pod_json = json.loads(output.output)
            if kuber_constants.FIELD_ITEMS not in pod_json:
                return pods_list
            for items in pod_json[kuber_constants.FIELD_ITEMS]:
                meta_data = items.get(kuber_constants.FIELD_METADATA, "")
                if meta_data:
                    if ready_only:
                        container_status = items[kuber_constants.FIELD_STATUS][kuber_constants.FIELD_CONTAINER_STATUS]
                        for each_container in container_status:
                            if each_container[kuber_constants.FIELD_READY]:
                                pods_list.append(meta_data.get(kuber_constants.FIELD_NAME, ""))
                    else:
                        pods_list.append(meta_data.get(kuber_constants.FIELD_NAME, ""))
        except Exception:
            raise Exception(f"Failed to get proper response for pods  - {output.output}")
        return pods_list

    def get_nodes(self, ready_only=False):
        """returns the running POD details

            Args:

                ready_only      (bool)      --  flag to filter out ready only nodes in output
                                                                (Default : False)

            Returns:

                list    --  Containing node names

            Raises:

                Exception:

                    if failed to get node details
        """
        cmd = "kubectl get nodes -o=json"
        output = self.machine_obj.execute_command(cmd)
        self.log.info("Getting node information by running command : %s ", str(cmd))
        node_list = []
        if ready_only:
            self.log.info(f"ReadyOnly flag set. Drop NODE which are not in ready state")
        try:
            if output.exception_message:
                raise Exception(f"Failed to get node details - {output.exception_message}")
            node_json = json.loads(output.output)
            if kuber_constants.FIELD_ITEMS not in node_json:
                return node_list
            for items in node_json[kuber_constants.FIELD_ITEMS]:
                meta_data = items.get(kuber_constants.FIELD_METADATA, "")
                if meta_data:
                    if ready_only:
                        _conditions = items[kuber_constants.FIELD_STATUS][kuber_constants.FIELD_CONDITIONS]
                        for each_condition in _conditions:
                            if each_condition[kuber_constants.FIELD_TYPE] == kuber_constants.FIELD_READY_PRE and each_condition[kuber_constants.FIELD_STATUS]:
                                node_list.append(meta_data.get(kuber_constants.FIELD_NAME, ""))
                    else:
                        node_list.append(meta_data.get(kuber_constants.FIELD_NAME, ""))

        except Exception:
            raise Exception(f"Failed to get proper response for nodes  - {output.output}")
        return node_list

    def get_service(self, service_name, name_space=None):
        """returns the dict containing service details

            Args:

                service_name        (str)       --  Service name in cluster

                name_space          (str)       --  namespace to be used. if none, then default namespace in cluster

            Returns:

                dict    --  containing service details

            Raises:

                Exception:

                    if failed to get service info
        """
        service_json = None
        cmd = f"kubectl get service/{service_name} -o=json"
        if name_space:
            cmd += f" -n {name_space}"
        output = self.machine_obj.execute_command(cmd)
        self.log.info("Getting service information by running command : %s ", str(cmd))
        try:
            if output.exception_message:
                raise Exception(f"Failed to find service details - {output.exception_message}")
            service_json = json.loads(output.output)
        except Exception:
            raise Exception(f"Failed to get proper response for get service - {output.output}")
        return service_json

    def get_top_pod(self, pod_name=None, name_space=None, dump_log=False):
        """returns the POD memory/CPU usage details

            Args:

                pod_name            (str)       --   Name of POD

                name_space          (str)       --  pod's namespace

                dump_log            (bool)      --  dumps response in log. [Default - True]

            Returns:

                dict    --  containing POD CPU/Memory Usage details

            Raises:

                Exception:

                    if failed to get pod usage details
        """
        cmd = f"kubectl top pod"
        if pod_name:
            cmd = f"{cmd} {pod_name}"
        if name_space:
            cmd = f"{cmd} -n {name_space}"
        output = self.machine_obj.execute_command(cmd)
        self.log.info("Getting POD CPU/Memory information by running command  : %s ", str(cmd))
        if dump_log:
            self.log.info(f"Output of command - {output.output}")
        if output.exception_message:
            raise Exception(f"Failed to get pod usage details - {output.exception_message}")
        return self._process_table_response(output=output)

    def get_top_node(self, node_name=None, dump_log=True):
        """returns the node memory/CPU usage details

            Args:

                node_name            (str)       --   Name of node

                dump_log            (bool)       --  dumps response in log. [Default - True]

            Returns:

                dict    --  containing node CPU/Memory Usage details

            Raises:

                Exception:

                    if failed to get node usage details
        """
        cmd = f"kubectl top node"
        if node_name:
            cmd = f"{cmd} {node_name}"
        output = self.machine_obj.execute_command(cmd)
        self.log.info("Getting node CPU/Memory information by running command : %s ", str(cmd))
        if dump_log:
            self.log.info(f"Output of command - {output.output}")
        if output.exception_message:
            raise Exception(f"Failed to get node usage details - {output.exception_message}")
        return self._process_table_response(output=output)

    def delete_deployment_app(self, app_name=None, name_space=None, **kwargs):
        """Deletes the deployment app from kubernetes

            Args:

                app_name            (str)       --   Name of the app

                name_space          (str)       --   Name space where app resides

            kwargs:

                selector    (str)       --  Selector to apply for

            Returns:

                None

            Raises:

                Exception:

                    if failed to find app

                    if failed to delete app
        """
        cmd = f"kubectl delete deployment.apps"
        if app_name:
            cmd += f"/{app_name}"
        if name_space:
            cmd += f" -n {name_space}"
        if kwargs.get('selector', None):
            cmd += f" --selector {kwargs.get('selector')}"
        output = self.machine_obj.execute_command(cmd)
        self.log.info(
            "Deleting deployment app by running command : %s ",
            str(cmd))
        self.log.info(f"Output of command - {output.output}")
        if output.exception_message:
            raise Exception(
                f"Failed to delete deployment app - {output.exception_message}")
        if app_name:
            if f"\"{app_name}\" deleted" not in output.output:
                raise Exception("Failed to delete deployment app")
            self.log.info(f"Successfully deleted deployment app - {app_name}")
        else:
            if f"deleted" not in output.output:
                raise Exception("Failed to delete deployment")
            self.log.info(f"Successfully deleted deployment")

    def apply_yaml(self, yaml_file):
        """Applies yaml configuration file on kubernetes

                Args:

                    yaml_file           (str)       --  Yaml file path on local controller

                Returns:

                    None

                Raises:

                    Exception:

                        if failed to find yaml file

                        if failed to apply yaml configuration file on kubernetes
        """
        if not os.path.exists(yaml_file):
            raise Exception("Yaml file doesn't exists on given path")
        self.log.info(f"Going to copy yaml file to kubectl machine")
        drive = self.options_obj.get_drive(self.machine_obj)
        folder = f"{drive}RuntimeCreatedby_{self.options_obj.get_custom_str()}"
        self.log.info(f"Destination yaml file folder path : {folder}")
        self.machine_obj.create_directory(directory_name=folder, force_create=True)
        if not self.machine_obj.copy_from_local(
                local_path=yaml_file,
                remote_path=folder) and self.commcell.clients.has_client(
                self.machine_obj.machine_name):
            self.log.info(f"Uploading local file via API call as it is commvault client")
            m = Machine(machine_name=self.machine_obj.machine_name, commcell_object=self.commcell)
            m.copy_from_local(local_path=yaml_file, remote_path=folder, raise_exception=True)
        cmd = f"kubectl apply -o=json -f \"{folder}{self.machine_obj.os_sep}{os.path.split(yaml_file)[1]}\""
        self.log.info(f"Going to apply yaml file on kubernetes by command : {cmd}")
        output = self.machine_obj.execute_command(cmd)
        self.log.info(f"Output of command - {output.output}")
        try:
            if output.exception_message:
                self.log.info(f"Exception Message - {output.exception_message}")
                # suppress warnings and raise exception only for other cases
                if 'warning' not in output.exception_message.lower():
                    raise Exception(
                        f"Failed to apply yaml file - {output.exception_message}")
            # Loading output json is considered as success
            _ = json.loads(output.output)
            try:
                self.machine_obj.remove_directory(directory_name=folder)
            except Exception:
                self.log.info(
                    f"[Warning] - Failed to delete staged yaml directory - {folder}")
        except Exception:
            raise Exception(f"Failed to apply yaml file configuration - {output.output}")

    def convert_yaml_to_json(self, yaml_file):
        """Convets yaml file to json and return it as dict

            Args:

                yaml_file       (str)       --  Yaml file path

            Returns:

                dict -- Containing yaml details

            Raises:

                Exception:

                    if failed to convert yaml to json
        """
        self.log.info(f"Processing Yaml file @ {yaml_file}")
        return commonutils.convert_yaml_to_json(yaml_file=yaml_file)

    def download_extracting_yaml(self):
        """returns the yaml file path

            Args:

                None

            Returns:

                str     --  Yaml file path

            Raises:

                Exception:

                    if failed to download yaml file
        """

        import requests
        self.log.info(f"Sending request to get yaml file : {kuber_constants.EXTRACTING_GITHUB_YAML_URL}")
        content = requests.get(kuber_constants.EXTRACTING_GITHUB_YAML_URL).content
        content = content.decode('utf-8')
        folder = f"{AUTOMATION_DIRECTORY}{self.local_machine_obj.os_sep}Temp{self.local_machine_obj.os_sep}" \
                 f"ExtractingGitHubYamlDownload_{self.options_obj.get_custom_str()}"
        self.local_machine_obj.create_directory(directory_name=folder, force_create=True)
        self.log.info(f"Folder name to download yaml file : {folder}")
        dst_file = f"{folder}{self.local_machine_obj.os_sep}extracting.yaml"
        file_obj = open(dst_file, "w")
        file_obj.write(content)
        file_obj.close()
        return file_obj.name

    def monitor_pod(self, timeout=30, check_interval=150):
        """Monitors pod's auto scale up & down for specified time interval

            Args:

                timeout         (int)       --  Timeout in mins
                                                    Default:30Mins

                check_interval  (int)       --  Time interval in secs between POD status check
                                                    Default:150Sec

            Returns:

                dict    --  containing POD auto scaling details within this interval

            Raises:
                None
        """
        output = {
            kuber_constants.KEY_SCALED_UP: [],
            kuber_constants.KEY_SCALED_DOWN: []
        }
        older_details = None
        new_details = None
        time_limit = time.time() + timeout * 60
        while True:
            try:
                new_details = self.get_pods()
                output[kuber_constants.KEY_PODS] = new_details
            except Exception:
                self.log.info("Unable to fetch POD details. Will retry")
                time.sleep(check_interval)
                continue
            if not older_details:
                self.log.info(f"Monitoring it for first time. Current POD count : {len(new_details)}")
                older_details = new_details
            if len(older_details) == len(new_details):
                if older_details.sort() == new_details.sort():
                    self.log.info(f"POD list unchanged - {new_details}")
                else:
                    self.log.info(f"POD count is same but POD name change detected. Possibly POD recreated!!")
            elif len(new_details) > len(older_details):
                diff = len(new_details) - len(older_details)
                self.log.info(f"POD Scale up detected. Old count - {len(older_details)} New count - {len(new_details)}"
                              f" Diff is {diff}")
                new_pods = list(sorted(set(new_details) - set(older_details)))
                self.log.info(f"New POD's are  - {new_pods}")
                pod_json = {
                    kuber_constants.KEY_TIME: int(time.time()),
                    kuber_constants.KEY_PODS: new_pods
                }
                output[kuber_constants.KEY_SCALED_UP].append(pod_json)
            else:
                diff = len(older_details) - len(new_details)
                self.log.info(
                    f"POD Scale down detected. Old count - {len(older_details)} New count - {len(new_details)}"
                    f" Diff is {diff}")
                del_pods = list(sorted(set(older_details) - set(new_details)))
                self.log.info(f"Deleted POD's are  - {del_pods}")
                pod_json = {
                    kuber_constants.KEY_TIME: int(time.time()),
                    kuber_constants.KEY_PODS: del_pods
                }
                output[kuber_constants.KEY_SCALED_DOWN].append(pod_json)
            if time.time() >= time_limit:
                self.log.info(f"Time limit reached. Exiting Monitor POD function with results - {output}")
                return output
            self.log.info(f"Waiting {check_interval} seconds before querying POD details")
            older_details = new_details
            time.sleep(check_interval)

    def run_cmd_on_pod(self, pod_name, command, namespace=None, **kwargs):
        """Executes command on given pod name in the cluster

            Args:

                pod_name        (str)       --  Name of the POD

                command         (str)       --  Command to execute

                namespace       (str)       --  Namespace name to which POD belongs to
                                                                (Default:None)

            Kwargs Options:

                format          (bool)      --  bool to specify whether output is simple or formatted by splitting '\r\n'

            Returns:

                str     --   Command output
                list    --   command output if format is specified as true

            Raises:

                Exception:

                    if command fails to run
        """
        format_out = kwargs.get('format', False)
        cmd = f"kubectl exec"
        if namespace:
            cmd = f"{cmd} -n {namespace}"
        cmd = f"{cmd} -i {pod_name} -- /bin/bash -c \"{command}\""
        output = self.machine_obj.execute_command(cmd)
        self.log.info("Running command on POD : %s ", str(cmd))
        if output.exception_message:
            raise Exception(
                f"Failed to run command on pod - {output.exception_message}")
        if not format_out:
            return output.output
        else:
            output_list = []
            values = re.split('\r\n |\n', output.output.strip())
            for value in values:
                value = value.strip()
                if not value:
                    continue
                output_list.append(value)
            return output_list

    def recycle_cv_srv_on_pod(self, pod_name, option, namespace=None):
        """Recycles commvault services running on the pod

            Args:

                pod_name            (str)       --   Name of the POD

                option              (int)       --  Service operation options

                                                Supported values : 1 - Restart 2- Stop 3 - Start

                namespace           (str)       --  Namespace name to which POD belongs to
                                                                (Default:None)

            Returns:

                None

            Raises:

                Exception:

                    if fails to recycle services on POD

        """
        cmd = f"commvault"
        validate = ""
        if option == 1:
            cmd = f"{cmd} restart"
            validate = "All services started."
        elif option == 2:
            cmd = f"{cmd} stop"
            validate = "All services stopped."
        else:
            cmd = f"{cmd} start"
            validate = "All services started."
        output = self.run_cmd_on_pod(
            pod_name=pod_name,
            command=cmd,
            namespace=namespace)
        if validate not in output:
            raise Exception(
                f"Service command ended in error. Output - {output}")

    def get_stdout_logs(self, pod_name: str,
                        container_name=None,
                        namespace=None,
                        raise_error=False) -> str:
        """Get stdout logs from pod

            Args:

                    pod_name            (str)       --   Name of the POD

                    container_name      (str)       --  POD container name to fetch file/folder
                                                                    (Default:None - First container in pod)

                    namespace           (str)       --  Namespace name to which POD belongs to
                                                                    (Default:None)

                    raise_error         (bool)      --  raises exception if set to True (Default:False)

                Returns:

                    str --  file path

                Raises:

                    Exception:

                        if fails to get stdout logs only if raise_error is set
        """
        # prefix the pod name in front of logs
        cmd = f"kubectl logs {pod_name} --prefix"
        if container_name:
            cmd = f"{cmd} -c {container_name}"
        if namespace:
            cmd = f"{cmd} -n {namespace}"
        file_name = f"{pod_name}_stdout.txt"
        folder_name = f"{pod_name}_stdout_{self.options_obj.get_custom_str()}"
        cmd = f"{cmd} > {file_name}"
        output = self.machine_obj.execute_command(cmd)
        self.log.info("Running command on POD : %s ", str(cmd))
        if output.exception_message and raise_error:
            raise Exception(
                f"Failed to run logs command on pod - {output.exception_message}")
        # find out root drive of script and append to file name to return full
        # path
        output = self.machine_obj.execute_command("(Get-Location).path")
        file_name = f"{output.output.strip()}{self.machine_obj.os_sep}{file_name}"
        folder_name = f"{output.output.strip()}{self.machine_obj.os_sep}{folder_name}"
        self.machine_obj.create_directory(
            directory_name=folder_name, force_create=True)
        self.machine_obj.move_file(
            source_path=file_name,
            destination_path=folder_name)
        return folder_name

    def get_folder_or_file_from_pod(
            self,
            file_or_folder: str,
            pod_name: str,
            container_name=None,
            namespace=None,
            raise_error=False) -> str:
        """Downloads given folder or file from POD to machine

            Args:

                    file_or_folder      (str)       --  Folder or file complete path

                    pod_name            (str)       --   Name of the POD

                    container_name      (str)       --  POD container name to fetch file/folder
                                                                    (Default:None - First container in pod)

                    namespace           (str)       --  Namespace name to which POD belongs to
                                                                    (Default:None)

                    raise_error         (bool)      --  raises exception if set to True (Default:False)

                Returns:

                    str --  folder path containing files

                Raises:

                    Exception:

                        if fails to move file or folder only if raise_error is set
        """
        is_file = True
        if '.' not in file_or_folder:
            is_file = False
        folder_name = f"{pod_name}_FileDownloaded_{self.options_obj.get_custom_str()}"
        if is_file:
            folder_name = f"{folder_name}{self.machine_obj.os_sep}{os.path.basename(file_or_folder)}"
        self.log.info(f"Folder name to download files on remote machine : {folder_name}")
        if namespace:
            pod_name = f"{namespace}/{pod_name}"
        # kubectl cp internally uses tar to compress and copy. it will error out in case if file is being updated
        # so we are retrying 10 times as cv logs are written in runtime in POD.
        cmd = f"kubectl cp {pod_name}:{file_or_folder} ./{folder_name} --retries 10"
        if container_name:
            cmd = f"{cmd} -c {container_name}"
        output = self.machine_obj.execute_command(cmd)
        self.log.info("Running command on POD : %s ", str(cmd))
        if output.exception_message and raise_error:
            raise Exception(
                f"Failed to run CP command on pod - {output.exception_message}")
        # find out root drive of script and append to folder name to return
        # full path
        output = self.machine_obj.execute_command("(Get-Location).path")
        return f"{output.output.strip()}{self.machine_obj.os_sep}{folder_name}"

    def do_rollout_restart(self, resource, namespace=None):
        """does kubectl rollout restart for resource on cluster

            Args:

                resource            (str)       --  Name of resource

                namespace           (str)       --  Resource namespace (Default:None which is default namespace)

            Returns:

                None

            Raises:

                Exception:

                    if failed to rollout restart on resource
        """
        cmd = f"kubectl rollout restart {resource}"
        if namespace:
            cmd = f"{cmd} -n {namespace}"
        output = self.machine_obj.execute_command(cmd)
        self.log.info("Running command on cluster : %s ", str(cmd))
        if output.exception_message:
            raise Exception(
                f"Failed to run rollout restart command on cluster - {output.exception_message}")
        self.log.info(output.output)
        if 'restarted' not in output.output:
            raise Exception(
                "Failed to do restart on rollout. Please check logs")

    def monitor_hpa(self, namespace=None, timeout=10, interval=30):
        """Monitors HPA and returns the stats

            Args:

                namespace   (str)       --  POD namespace (Default : None which means default namespace)

                timeout     (int)       --  Time period to monitor in mins (Default:10Mins)

                interval    (int)       --  Time interval between getting hpa stats (Default:30seconds)

            Returns:

                list(dict)    -   Containing HPA stats

            Raises:

                Exception:

                    if failed to get hpa stats
        """
        stats = []
        cmd = f"kubectl get hpa -o json"
        if namespace:
            cmd = f"{cmd} -n {namespace}"
        time_limit = time.time() + timeout * 60
        while True:
            try:
                output = self.machine_obj.execute_command(cmd)
                self.log.info("Running command on cluster : %s ", str(cmd))
                if output.exception_message:
                    self.log.info(
                        f"Get HPA command - Failed with Exception - {output.exception_message}. Retrying after some time")
                _output_json = json.loads(output.output)
                if kuber_constants.FIELD_ITEMS in _output_json:
                    # loop over each HPA configs
                    for each_hpa in _output_json[kuber_constants.FIELD_ITEMS]:
                        _hpa_stats = {
                            kuber_constants.FIELD_NAME: each_hpa[kuber_constants.FIELD_METADATA][kuber_constants.FIELD_NAME],
                            kuber_constants.FIELD_MIN_REPLICA: each_hpa[kuber_constants.FIELD_SPEC][kuber_constants.FIELD_MIN_REPLICA],
                            kuber_constants.FIELD_MAX_REPLICA: each_hpa[kuber_constants.FIELD_SPEC][kuber_constants.FIELD_MAX_REPLICA],

                        }
                        if kuber_constants.FIELD_METRICS in each_hpa[kuber_constants.FIELD_SPEC]:
                            # Loop over each metric resource configuration
                            # defined for this hpa
                            for _each_metric in each_hpa[kuber_constants.FIELD_SPEC][kuber_constants.FIELD_METRICS]:
                                _metric_stats = {
                                    kuber_constants.FIELD_NAME: _each_metric[kuber_constants.FIELD_RESOURCE][kuber_constants.FIELD_NAME],
                                    kuber_constants.FIELD_AVG_UTILIZATION: _each_metric[kuber_constants.FIELD_RESOURCE][kuber_constants.FIELD_TARGET][kuber_constants.FIELD_AVG_UTILIZATION],
                                    kuber_constants.FIELD_TYPE: _each_metric[kuber_constants.FIELD_TYPE]

                                }
                                _hpa_stats[kuber_constants.FIELD_METRICS] = _metric_stats
                        if kuber_constants.FIELD_STATUS in each_hpa:
                            _hpa_stats[kuber_constants.FIELD_CUR_REPLICAS] = each_hpa[
                                kuber_constants.FIELD_STATUS][kuber_constants.FIELD_CUR_REPLICAS]
                            _hpa_stats[kuber_constants.FIELD_DES_REPLICAS] = each_hpa[
                                kuber_constants.FIELD_STATUS][kuber_constants.FIELD_DES_REPLICAS]
                            _hpa_stats[kuber_constants.FIELD_SCALE_TIME] = each_hpa[
                                kuber_constants.FIELD_STATUS][kuber_constants.FIELD_SCALE_TIME]
                            if kuber_constants.FIELD_CUR_METRICS in each_hpa[kuber_constants.FIELD_STATUS]:
                                # loop over each metric to know current stats
                                for _cur_metrics in each_hpa[kuber_constants.FIELD_STATUS][kuber_constants.FIELD_CUR_METRICS]:
                                    _cur_metrics_stats = {
                                        kuber_constants.FIELD_NAME: _cur_metrics[kuber_constants.FIELD_RESOURCE][kuber_constants.FIELD_NAME],
                                        kuber_constants.FIELD_AVG_UTILIZATION: _cur_metrics[kuber_constants.FIELD_RESOURCE][kuber_constants.FIELD_CURRENT][kuber_constants.FIELD_AVG_UTILIZATION],
                                        kuber_constants.FIELD_TYPE: _cur_metrics[kuber_constants.FIELD_TYPE]
                                    }
                                    _hpa_stats[kuber_constants.FIELD_CUR_METRICS] = _cur_metrics_stats
                        self.log.info(_hpa_stats)
                        stats.append({int(time.time()): _hpa_stats})

            except Exception as ep:
                self.log.exception(
                    f"Get HPA command - Failed. Retrying after some time - {ep}")
            if time.time() >= time_limit:
                self.log.info(
                    f"Time limit reached. Exiting Monitor HPA function with results - {stats}")
                break
            self.log.info(f"Sleeping for {interval} seconds")
            time.sleep(interval)
        return stats

    def create_secret_docker_registry(
            self, secret_name, server, user, password, namespace=None):
        """Creates secret key for docker registry

            Args:

                secret_name     (str)       --  Name of secret

                server          (str)       --  Docker server host name

                user            (str)       --  Username to connect to docker registry

                password        (str)       --  Password to connect to docker registry

                namespace       (str)       --  Namespace to create secret. Default:None

            Returns:

                None

            Raises:

                Exception:

                    if failed to create secret
        """
        cmd = f"kubectl create secret docker-registry {secret_name} --docker-username={user} " \
              f"--docker-password={password} --docker-server={server}"
        if namespace:
            cmd = f'{cmd} --namespace={namespace}'
        output = self.machine_obj.execute_command(cmd)
        self.log.info("Running command on cluster : %s ", str(cmd))
        if f'secret/{secret_name} created' not in output.output:
            raise Exception("Failed to create secret key for docker registry")

    def _write_csv(self, csv_file, stats, init):
        """Writes csv file with metrics

            Args:

                csv_file       (str)        --  CSV file path

                stats          (dict)       --  pod/node metrics collected from top command

                init           (bool)       --  denotes whether to write header or not to csv file

            Returns:

                None

        """
        # when collecting for namespace and one pod metrics fails, then we should
        # not write headers again for successful pod csv file so check for file
        # existence before deciding header insert
        _file_exists = os.path.exists(csv_file)
        data_file = open(csv_file, 'a')
        csv_writer = csv.writer(data_file)
        if not init and not _file_exists:
            self.log.info(f"Writing header to CSV file : {csv_file}")
            csv_writer.writerow(stats.keys())
        csv_writer.writerow(stats.values())
        data_file.close()

    def _collect_pod_metrics(self, pod_name, name_space, folder, init):
        """collects pods metrics and writes to csv file

            Args:

                pod_name    (str)       --  Pod name to be monitored [Default:None - all pods]

                name_space  (str)       --  pod's name space to monitor [Default:None - all namespaces]

                init        (bool)      --  denotes whether to write header or not to csv file

                folder      (str)       --  folder path to store csv files

            Returns:

                None


        """
        _stats = self.get_top_pod(pod_name=pod_name, name_space=name_space, dump_log=False)
        for key, value in _stats.items():
            if isinstance(value, dict):
                _stats = value
        _stats[kuber_constants.KEY_TIME] = int(time.time())
        csv_file = f"{folder}{self.local_machine_obj.os_sep}{pod_name}.csv"
        self._write_csv(csv_file=csv_file, init=init, stats=_stats)

    def _collect_node_metrics(self, folder, init, node_name=None):
        """collects node metrics and writes to csv file

            Args:

                init        (bool)      --  denotes whether to write header or not to csv file

                folder      (str)       --  folder path to store csv files

                node_name    (str)      --  Node name to be monitored [Default:None - all nodes]


        """
        _stats = self.get_top_node(node_name=node_name)
        for key, value in _stats.items():
            if isinstance(value, dict):
                _stats = value
        _stats[kuber_constants.KEY_TIME] = int(time.time())
        csv_file = f"{folder}{self.local_machine_obj.os_sep}{node_name}.csv"
        self._write_csv(csv_file=csv_file, init=init, stats=_stats)

    def _monitor_metrics_thread(self, folder, stop, name=None, name_space=None, interval=60, is_pod=True):
        """Monitors pod/node metrics and stores it in CSV file

                    Args:

                        folder      (str)       --  folder path to store csv files

                        name        (str)       --  Pod/Node name to be monitored [Default:None - all pods]

                        name_space  (str)       --  pod's name space to monitor [Default:None - all namespaces]
                                                            (Applicable only when monitoring pod)

                        interval    (int)       --  Monitor time interval between two samples [Default:60 seconds]

                        stop        (bool)      --  Bool to denote when to stop the monitor thread

                        is_pod      (bool)      --  Denotes whether it is for pod or node

                    Returns:

                        None

                    Raises:

                        Exception:

                            if failed to collect metrics for pod

        """
        init = False
        self.local_machine_obj.create_directory(directory_name=folder, force_create=True)
        init_done = None  # to hold pod names to handle new vs old pod csv file write
        while True:
            # check if quit flag is set
            if stop():
                self.log.info(
                    f"Quit flag set. Stopping the {threading.currentThread().getName()} thread gracefully")
                break
            else:
                try:
                    if name:
                        if is_pod:
                            self._collect_pod_metrics(pod_name=name, name_space=name_space, init=init, folder=folder)
                        else:
                            self._collect_node_metrics(node_name=name, folder=folder, init=init)
                        # once metrics collects, set init to True to avoid header rewrite in csv file
                        init = True

                    else:
                        if is_pod:
                            self.log.info(
                                f"Going to collect metrics for pod in {'default' if not name_space else name_space} namespace")
                            # find out all running pods with ready status
                            running_pods = self.get_pods(namespace=name_space, ready_only=True)
                            if not init_done:
                                init_done = running_pods
                            for _pod in running_pods:
                                if _pod in init_done:
                                    self._collect_pod_metrics(pod_name=_pod, name_space=name_space, init=init,
                                                              folder=folder)
                                else:
                                    self.log.info(f"Got new POD for monitoring - {_pod}")
                                    # send init flag as false as it is new workload pod
                                    self._collect_pod_metrics(pod_name=_pod, name_space=name_space, init=False,
                                                              folder=folder)
                                    init_done.append(_pod)

                        else:
                            self.log.info("Going to collect metrics for all nodes")
                            # find out all running nodes with ready status
                            running_nodes = self.get_nodes(ready_only=True)
                            if not init_done:
                                init_done = running_nodes
                            for _node in running_nodes:
                                if _node in init_done:
                                    self._collect_node_metrics(folder=folder, init=init, node_name=_node)
                                else:
                                    self.log.info(f"Got new Node for monitoring - {_node}")
                                    # send init flag as false as it is new workload node
                                    self._collect_node_metrics(folder=folder, init=False, node_name=_node)
                                    init_done.append(_node)
                        # once metrics collects, set init to True to avoid header rewrite in csv file
                        init = True
                    self.log.info(f"Waiting for {interval} seconds")
                    time.sleep(interval)
                except Exception as ep:
                    self.log.exception(ep)

    def monitor_pod_metrics(self, pod_name=None, name_space=None, interval=60):
        """Monitors pod metrics and writes to CSV file

            Args:

                pod_name    (str)       --  Pod name to be monitored [Default:None - all pods]

                name_space  (str)       --  pod's name space to monitor [Default:None - all namespaces]

                interval    (int)       --  Monitor time interval between two samples [Default:60 seconds]

            Returns:

                obj,str     --  thread class object , CSV folder path

            Raises:

                Exception:

                    None

        """
        folder = f"{AUTOMATION_DIRECTORY}{self.local_machine_obj.os_sep}Temp{self.local_machine_obj.os_sep}" \
                 f"{kuber_constants.KEY_POD_METRICS}_{self.options_obj.get_custom_str()}"
        self.log.info(f"POD Metrics collector starting. CSV Result will be stored in : {folder}")
        monitor_thread = threading.Thread(target=self._monitor_metrics_thread, args=(
            folder, lambda: self.stop_threads, pod_name, name_space, interval, True,))
        monitor_thread.name = "POD Metrics Collector : "
        if name_space:
            monitor_thread.name = f'{monitor_thread.name}-{name_space} NameSpace'
        if pod_name:
            monitor_thread.name = f'{monitor_thread.name}-{pod_name} Pod'
        monitor_thread.start()
        self.threads.append(monitor_thread)
        return monitor_thread, folder

    def monitor_node_metrics(self, node_name=None, interval=60):
        """Monitors node metrics and writes to CSV file

            Args:

                node_name    (str)      --  Node name to be monitored [Default:None - all nodes]

                interval    (int)       --  Monitor time interval between two samples [Default:60 seconds]

            Returns:

                obj,str     --  thread class object , CSV folder path

            Raises:

                Exception:

                    None

        """
        folder = f"{AUTOMATION_DIRECTORY}{self.local_machine_obj.os_sep}Temp{self.local_machine_obj.os_sep}" \
                 f"{kuber_constants.KEY_NODE_METRICS}_{self.options_obj.get_custom_str()}"
        self.log.info(f"NODE Metrics collector starting. CSV Result will be stored in : {folder}")
        monitor_thread = threading.Thread(target=self._monitor_metrics_thread, args=(
            folder, lambda: self.stop_threads, node_name, None, interval, False,))
        monitor_thread.name = "NODE Metrics Collector : "
        if node_name:
            monitor_thread.name = f'{monitor_thread.name}-{node_name} Node'
        monitor_thread.start()
        self.threads.append(monitor_thread)
        return monitor_thread, folder

    def analyze_metrics(self, folder, with_metrics_unit=True, push_to_cs_tbl=False, push_to_datasource=False, **kwargs):
        """Analyses metrics collected in csv file and return min/max for pod/node

            Args:

                folder      (str)           --  Path containing csv metrics files

                with_metrics_unit   (bool)  --  Specifies whether result json should have metrics unit or not (Default:True)

                push_to_cs_tbl      (bool)  --  Specifies whether to push metrics stats to sql table in CS

                push_to_datasource  (bool)  --  Specifies whether to push metrics stats to open datasource

            kwargs:

                Build_Id    (int)           --  Unique build id for automation

                Export      (bool)          --  Specifies whether to export report graph or not

            Returns:

                dict    --  Stats for pod/node

            Raises:

                Exception:

                    if failed to find stats / Push stats
        """
        build_id_param = 'Build_Id'
        export_param = 'Export'
        output = []
        is_pod = False
        mssql_obj = None
        rpt_file_path = ''
        if not os.path.exists(folder):
            raise Exception("Provided folder doesn't exists")
        if push_to_datasource and build_id_param in kwargs:
            self.log.info("Pushing metrics to Automation POD Open datasource")
            self._setup_performance_datasource()
            if kwargs.get(export_param, False):
                self._setup_report(build_id=kwargs.get(build_id_param))
                rpt_api = Reports(
                    self.commcell.webconsole_hostname)
                self.log.info(f"Report core API class initialised")
                export_folder = os.path.join(
                    GeneralConstants.CONTROLLER_FOLDER_PATH,
                    str(kwargs.get(build_id_param)),
                    GeneralConstants.CONTROLLER_REPORTS_FOLDER_NAME,
                    GeneralConstants.CONTROLLER_EXPORT_HTML_FOLDER_NAME)
                os.makedirs(export_folder)
        if push_to_cs_tbl and build_id_param in kwargs:
            self.log.info("Pushing metrics to Automation CS table")
            ss_name_suffix = ""
            if 'windows' in self.commcell.commserv_client.os_info.lower():
                ss_name_suffix = kuber_constants.DB_FIELD_COMMVAULT
            conn_str = self.commcell.commserv_hostname + ss_name_suffix
            self.log.info(f"CS Sql connection String - {conn_str}")
            mssql_obj = MSSQL(conn_str,
                              _CS_CONFIG_DATA.Username,
                              _CS_CONFIG_DATA.Password,
                              kuber_constants.DB_FIELD_COMMSERV,
                              use_pyodbc=False)
            self.log.info("MSSql object initialized to CS")
            _cur = mssql_obj.connection.cursor()
            _cur.execute(kuber_constants.AUTOMATION_POD_METRICS_TBL_SCRIPT)
            self.log.info(f"Setup of {kuber_constants.AUTOMATION_POD_METRICS_TBL} table on CS finished")
        for filename in os.listdir(folder):
            _temp = {}
            _file = os.path.join(folder, filename)
            if not filename.endswith('.csv'):
                self.log.info(f"Folder contains invalid file types - {_file}")
                continue
            if kuber_constants.KEY_POD_METRICS in folder:
                self.log.info(f"Analysing File for POD Metrics via pandas: {_file}")
                is_pod = True
            else:
                self.log.info(f"Analysing File for NODE Metrics via pandas: {_file}")
            try:
                # load csv file into pandas data frame. as we are generating csv file in
                # controller, no need to handle os specific eof/delimiter
                _data_frame = pandas.read_csv(_file)
                self.log.info("CSV loaded into dataframe")
                # mark column to load as int in data frame
                _data_frame[kuber_constants.KEY_POD_CPU] = _data_frame[kuber_constants.KEY_POD_CPU].str.replace(
                    kuber_constants.KEY_CPU_UNIT, '')
                _data_frame[kuber_constants.KEY_POD_CPU] = _data_frame[kuber_constants.KEY_POD_CPU].astype('int')
                _data_frame[kuber_constants.KEY_POD_MEMORY] = _data_frame[kuber_constants.KEY_POD_MEMORY].str.replace(
                    kuber_constants.KEY_MEMORY_UNIT, '')
                _data_frame[kuber_constants.KEY_POD_MEMORY] = _data_frame[kuber_constants.KEY_POD_MEMORY].astype('int')

                if is_pod:
                    # pushing to open datasource
                    if push_to_datasource and build_id_param in kwargs:
                        _import_data = []
                        for index, row in _data_frame.iterrows():
                            _row_dict = {
                                kuber_constants.TABL_FIELD_BUILDID: kwargs.get(build_id_param),
                                kuber_constants.TABL_FIELD_CSVERSION: self.commcell.version,
                                kuber_constants.TABL_FIELD_TIMESTAMP: (datetime(1970, 1, 1) + timedelta(
                                    seconds=int(row[kuber_constants.KEY_TIME]))).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                                kuber_constants.TABL_FIELD_NAME: row[kuber_constants.KEY_POD_NAME],
                                kuber_constants.TABL_FIELD_CPUINMILLICORES: row[kuber_constants.KEY_POD_CPU],
                                kuber_constants.TABL_FIELD_MEMORYINMIB: row[kuber_constants.KEY_POD_MEMORY]
                            }
                            _import_data.append(_row_dict)
                        open_data_source_obj = self.commcell.datacube.datasources.get(
                            kuber_constants.AUTOMATION_POD_METRICS_TBL)
                        open_data_source_obj.import_data(_import_data)
                        self.log.info(f"Total documents inserted into open data source : {len(_import_data)}")

                        # Generate export report
                        if kwargs.get(export_param, False):
                            pod_name = filename.replace('.csv', '')  # pod name will be csv file name
                            self.log.info("Exporting Report for POD Metrics")
                            report_name = f"{pod_name}_{kwargs.get(build_id_param)}"
                            # Report name can be passed as report id. it will work
                            report_id = GeneralConstants.Automation_performance_Report_Name
                            filters = f'pageName=PodStats&PodFilters.filter.include.CSVersion=%5B%22{
                                self.commcell.version}%22%5D&PodFilters.filter.include.BuildId=%5B{
                                kwargs.get(build_id_param)}%5D&PodFilters.filter.include.Name=%5B%22{pod_name}%22%5D'
                            report_file = rpt_api.export_report(
                                report_id,
                                GeneralConstants.REPORT_EXPORT_TYPE,
                                export_folder,
                                report_name,
                                filters)
                            report_name = f"POD_{report_name}.{GeneralConstants.REPORT_EXPORT_TYPE}"
                            path, file = os.path.split(report_file)
                            rpt_file_path = os.path.join(path, report_name)
                            if os.path.exists(rpt_file_path):
                                os.remove(rpt_file_path)
                                self.log.info(f"Removing older reports with same name as : {report_name}")
                            os.rename(report_file, rpt_file_path)
                            self.log.info(f"Successfully renamed report file as - {report_name}")

                    # pushing to cs table
                    if push_to_cs_tbl and build_id_param in kwargs:
                        for index, row in _data_frame.iterrows():
                            _query = f'insert into {kuber_constants.AUTOMATION_POD_METRICS_TBL}({kuber_constants.TABL_FIELD_CSVERSION},{kuber_constants.TABL_FIELD_BUILDID},{kuber_constants.TABL_FIELD_TIMESTAMP},{kuber_constants.TABL_FIELD_NAME},{kuber_constants.TABL_FIELD_CPUINMILLICORES},{kuber_constants.TABL_FIELD_MEMORYINMIB}) values (%s,%s,%s,%s,%s,%s)'
                            _values = (self.commcell.version, kwargs.get(build_id_param,
                                                                         0),
                                       row[kuber_constants.KEY_TIME],
                                       row[kuber_constants.KEY_POD_NAME],
                                       row[kuber_constants.KEY_POD_CPU],
                                       row[kuber_constants.KEY_POD_MEMORY])
                            _cur = mssql_obj.connection.cursor()
                            _cur.execute(_query, _values)
                        self.log.info(
                            f"Total rows inserted into Automation POD Metrics Table in CS : {len(_data_frame)}")

                    _temp = {
                        kuber_constants.KEY_POD_NAME: _data_frame[kuber_constants.KEY_POD_NAME][0],
                        kuber_constants.KEY_POD_CPU_MIN: f"{_data_frame[kuber_constants.KEY_POD_CPU].min()}{kuber_constants.KEY_CPU_UNIT if with_metrics_unit else ''}",
                        kuber_constants.KEY_POD_CPU_MAX: f"{_data_frame[kuber_constants.KEY_POD_CPU].max()}{kuber_constants.KEY_CPU_UNIT if with_metrics_unit else ''}",
                        kuber_constants.KEY_POD_CPU_AVG: f"{round(_data_frame[kuber_constants.KEY_POD_CPU].mean(),2)}{kuber_constants.KEY_CPU_UNIT if with_metrics_unit else ''}",
                        kuber_constants.KEY_POD_MEMORY_MIN: f"{_data_frame[kuber_constants.KEY_POD_MEMORY].min()}{kuber_constants.KEY_MEMORY_UNIT if with_metrics_unit else ''}",
                        kuber_constants.KEY_POD_MEMORY_MAX: f"{_data_frame[kuber_constants.KEY_POD_MEMORY].max()}{kuber_constants.KEY_MEMORY_UNIT if with_metrics_unit else ''}",
                        kuber_constants.KEY_POD_MEMORY_AVG: f"{round(_data_frame[kuber_constants.KEY_POD_MEMORY].mean(),2)}{kuber_constants.KEY_MEMORY_UNIT if with_metrics_unit else ''}",
                        kuber_constants.REPORTS_FOLDER_PATH: rpt_file_path if rpt_file_path else 'NA'

                    }
                else:
                    _temp = {
                        kuber_constants.KEY_POD_NAME: _data_frame[kuber_constants.KEY_POD_NAME][0],
                        kuber_constants.KEY_POD_CPU_MIN: f"{_data_frame[kuber_constants.KEY_POD_CPU].min()}{kuber_constants.KEY_CPU_UNIT if with_metrics_unit else ''}",
                        kuber_constants.KEY_POD_CPU_MAX: f"{_data_frame[kuber_constants.KEY_POD_CPU].max()}{kuber_constants.KEY_CPU_UNIT if with_metrics_unit else ''}",
                        kuber_constants.KEY_POD_CPU_AVG: f"{round(_data_frame[kuber_constants.KEY_POD_CPU].mean(),2)}{kuber_constants.KEY_CPU_UNIT if with_metrics_unit else ''}",
                        kuber_constants.KEY_POD_MEMORY_MIN: f"{_data_frame[kuber_constants.KEY_POD_MEMORY].min()}{kuber_constants.KEY_MEMORY_UNIT if with_metrics_unit else ''}",
                        kuber_constants.KEY_POD_MEMORY_MAX: f"{_data_frame[kuber_constants.KEY_POD_MEMORY].max()}{kuber_constants.KEY_MEMORY_UNIT if with_metrics_unit else ''}",
                        kuber_constants.KEY_POD_MEMORY_AVG: f"{round(_data_frame[kuber_constants.KEY_POD_MEMORY].mean(),2)}{kuber_constants.KEY_MEMORY_UNIT if with_metrics_unit else ''}",
                        kuber_constants.KEY_NODE_CPU_PERCENT_MIN: f"{_data_frame[kuber_constants.KEY_NODE_CPU_PERCENT].min()}",
                        kuber_constants.KEY_NODE_CPU_PERCENT_MAX: f"{_data_frame[kuber_constants.KEY_NODE_CPU_PERCENT].max()}",
                        kuber_constants.KEY_NODE_CPU_PERCENT_AVG: f"{_data_frame[kuber_constants.KEY_NODE_CPU_PERCENT].mean()}",
                        kuber_constants.KEY_NODE_MEMORY_PERCENT_MIN: f"{_data_frame[kuber_constants.KEY_NODE_MEMORY_PERCENT].min()}",
                        kuber_constants.KEY_NODE_MEMORY_PERCENT_MAX: f"{_data_frame[kuber_constants.KEY_NODE_MEMORY_PERCENT].max()}",
                        kuber_constants.KEY_NODE_MEMORY_PERCENT_AVG: f"{_data_frame[kuber_constants.KEY_NODE_MEMORY_PERCENT].mean()}",
                        kuber_constants.REPORTS_FOLDER_PATH: rpt_file_path if rpt_file_path else 'NA'

                    }
            except Exception as ep:
                raise Exception(f"Failed to load/process csv files - {ep}")
            output.append(_temp)
        self.log.info(f"Metrics Result - {output}")
        return output

    def get_deployments(self, name=None, name_space=None, **kwargs):
        """returns deployment details from cluster for given name space

            Args:

                name        (str)       --  Deployment name [Default:None - All deployments]

                name_space  (str)       --  Name space details [Default:None - All namespaces]

            ** kwargs options **

                selector    (str)       --  Selector to apply

            Returns:

                dict    --  deployment details

            Raises:

                Exception:

                    if failed to get details
        """
        cmd = f"kubectl get deployments"
        if name:
            cmd += f" {name}"
        if name_space:
            cmd += f" -n {name_space}"
        if kwargs.get('selector', None):
            cmd += f" --selector {kwargs.get('selector')}"
        cmd += f" -o=json"
        output = self.machine_obj.execute_command(cmd)
        self.log.info("Getting deployments information by running command : %s ", str(cmd))
        try:
            if output.exception_message:
                raise Exception(f"Failed to find deployment details - {output.exception_message}")
            deploy_json = json.loads(output.output)
        except Exception:
            raise Exception(f"Failed to get proper response for get deployment - {output.output}")
        return deploy_json

    def set_deployment_image(
            self,
            image,
            name,
            container_name,
            name_space=None):
        """sets the new image to deployment from cluster for given name space

           Args:

               image        (str)      --  New image to apply to deployment

               name        (str)       --  Deployment name [Default:None - All deployments]

               container_name   (str)  --  Container name to apply image

               name_space  (str)       --  Name space details [Default:None - All namespaces]

           Returns:

               None

           Raises:

               Exception:

                   if failed to set image to deployment
       """
        cmd = f'kubectl set image deployment/{name} {container_name}={image}'
        if name_space:
            cmd = f'{cmd} -n {name_space}'
        output = self.machine_obj.execute_command(cmd)
        self.log.info(
            "Setting deployments image by running command : %s ",
            str(cmd))
        if 'image updated' not in output.output:
            raise Exception(
                f"Failed to set image to deployment - {name} & container - {container_name}")

    def check_deployment_status(self, name, name_space=None):
        """Checks for readiness status of deployment replicas

            Args:

                name    (str)       --  Deployment name

                name_space  (str)   --  Deployment's name space

            Returns:

                bool    --  True if all available replicas are in ready state
                            False otherwise

            Raises:

                Exception:

                    if failed to find replicas status
        """
        _deploy_details = self.get_deployments(
            name=name, name_space=name_space)
        avail_replicas = _deploy_details[kuber_constants.FIELD_STATUS][kuber_constants.FIELD_AVAIL_REPLICA]
        ready_replicas = _deploy_details[kuber_constants.FIELD_STATUS][kuber_constants.FIELD_READY_REPLICA]
        if ready_replicas != avail_replicas:
            self.log.info(
                f"Available replicas[{avail_replicas}] and ready replicas[{ready_replicas}] is not matching")
            return False
        self.log.info(f"Deployment's Available & Ready Replicas matched")
        return True

    def get_deployment_image(self, name=None, name_space=None):
        """returns deployment image details from cluster for given name space

           Args:

               name        (str)       --  Deployment name [Default:None - All deployments]

               name_space  (str)       --  Name space details [Default:None - All namespaces]

           Returns:

               dict    --  deployment image details

           Raises:

               Exception:

                   if failed to get details
       """
        deploy_details = None
        _deployments = self.get_deployments(name=name, name_space=name_space)
        deployments = []
        _name = None
        # if deployment name is passed, then return json struct is different.
        # Handle it accordingly
        if name and kuber_constants.FIELD_ITEMS not in _deployments:
            deploy_details = {
                kuber_constants.FIELD_ITEMS: [_deployments]
            }
        else:
            deploy_details = _deployments
        for items in deploy_details[kuber_constants.FIELD_ITEMS]:
            meta_data = items.get(kuber_constants.FIELD_METADATA, "")
            _temp = []
            if meta_data:
                _name = meta_data.get(kuber_constants.FIELD_NAME, "")
                _containers = items[kuber_constants.FIELD_SPEC][kuber_constants.FIELD_TEMPLATE][
                    kuber_constants.FIELD_SPEC][kuber_constants.FIELD_CONTAINERS]
            for each_container in _containers:
                _container_name = each_container[kuber_constants.FIELD_NAME]
                _container_image = each_container[kuber_constants.FIELD_IMAGE]
                _temp.append({
                    _container_name: {
                        kuber_constants.FIELD_NAME: _container_name,
                        kuber_constants.FIELD_IMAGE: _container_image
                    }
                })
            deployments.append({_name: _temp})
        return deployments

    def scale_deployment(self, deploy_name, replica, namespace=None):
        """Scale up/down the replicas count for deployment

            Args:

                deploy_name     (str)       --  name of deployment

                replica         (int)       --  new desired no of replicas

                namespace       (str)       --  deployment's namespace [Default - None]

            Returns:

                None

            Raises:

                Exception:

                    if failed to set replicas

        """
        cmd = f'kubectl scale deployment/{deploy_name} --replicas={replica}'
        if namespace:
            cmd = f'{cmd} -n {namespace}'
        output = self.machine_obj.execute_command(cmd)
        self.log.info(
            "Setting deployments replicas by running command : %s ",
            str(cmd))
        if 'scaled' not in output.output:
            raise Exception(
                f"Failed to set replicas to deployment - {deploy_name}")

    @property
    def client_version(self):
        """returns the client version info

            Args:
                None

            Returns:
                dict    --  containing client version info
        """
        if 'clientVersion' in self.version_info:
            return self.version_info['clientVersion']
        return {}

    @property
    def server_version(self):
        """returns the server version info

            Args:
                None

            Returns:
                dict    --  containing server version info
        """
        if 'serverVersion' in self.version_info:
            return self.version_info['serverVersion']
        return {}

    @property
    def machine(self):
        """returns the kubectl installed machine object

            Args:
                None

            Returns:

                obj --  Machine class object

        """
        return self.machine_obj

    @property
    def stop_monitor_threads(self):
        """returns current value for threads stop flag

        Args:

            None

        Returns:

            bool    -- Stop thread flag value

        """
        return self.stop_threads

    @stop_monitor_threads.setter
    def stop_monitor_threads(self, flag):
        """setter to set the global threads flag

        Args:

            flag    (bool)      --  bool to set for global thread stop flag

        Returns:

            None

        """
        self.stop_threads = flag
        if flag:
            self.log.info(f"Waiting for all child threads : {self.threads} to go down gracefully")
            while len(self.threads) > 0:
                for _thread in self.threads:
                    if not _thread.is_alive():
                        self.log.info(f"Thread [{_thread.getName()}] is not alive")
                    else:
                        self.log.info("Executing Join for thread : %s", _thread)
                        _thread.join()
                        self.log.info(f"{_thread.getName()} stopped gracefully")
                        # thread came down gracefully. remove thread object from the list
                    self.threads.remove(_thread)
                    self.log.info(f"Removed Thread from stack : {_thread.getName()}")
            self.log.info(f"All child thread went down. Resetting global stop flag to - False")
            self.stop_threads = False
