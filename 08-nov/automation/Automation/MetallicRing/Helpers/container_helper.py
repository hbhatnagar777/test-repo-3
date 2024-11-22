# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for Container related operations in Metallic Ring

    ContainerRingHelper:

        __init__()                      --  Initializes Container Ring Helper

        start_task                      --  Starts the container related tasks for metallic ring

        add_helm_repo                   --  Adds the required helm repo for operations

        create_containers               --  Creates containers required for the ring

        wait_for_deployment_to_complete --  Waits for all the deployments to complete

        is_deployment_ready             --  Checks the kubectl deployment status

        open_port_on_service            --  Opens a port on a kubectl service

        kube_set_context                --  Sets the kubernetes context

        az_set_subscription             --  Sets the azure subscription ID

"""
import time
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs
from MetallicRing.Utils.ring_utils import RingUtils

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class ContainerRingHelper(BaseRingHelper):
    """ helper class for Container related operations in Metallic Ring"""

    def __init__(self):
        super().__init__(None)
        self.local_machine = Machine()
        self.container = self.ring.container_info
        self.wait_time = cs.WaitTime.ONE_MIN.value * 60
        self.ring_id_str = RingUtils.get_ring_string(self.ring.id)
        self.ring_name = RingUtils.get_ring_name(self.ring_id)

    def start_task(self):
        """
        Starts the user related tasks for metallic ring
        """
        try:
            self.log.info(f"Container Helper task started. Setting the user context to {self.container.context}")
            self.kube_set_context(self.container.context)
            self.log.info(f"User context set. Adding Helm repository")
            self.add_helm_repo(self.container.helm_info.repo_name, self.container.helm_info.repo_url)
            self.log.info("Helm repository added. Creating containers using Helm")
            self.create_containers(self.ring_id_str, self.container.tag, self.container.global_registry,
                                   self.container.namespace, self.ring.commserv.new_password)
            self.log.info("Containers created. Waiting for deployment")
            self.wait_for_deployment_to_complete()
            self.open_port_on_service(f"{_CONFIG.commserv.client_name}gateway", cs.CVD_SERVICE, cs.CVD_PORT)
            self.log.info("Deployment complete. Container Helper task complete. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute user helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def add_helm_repo(self, repo_name, repo_url):
        """
        Adds the required helm repo for operations
        Args:
            repo_name(str)  --  Name of the repo
            repo_url(str)   --  URL of the repo
        """
        self.log.info(f"Request received to add the following repo - [{repo_name}] and URL  [{repo_url}]")
        cmd = f"helm repo remove {repo_name}; helm repo add {repo_name} {repo_url} "
        self.run_command(cmd)

    def create_containers(self, ring_id, container_image, global_registry, namespace, password):
        """
        Creates containers required for the ring
        Args:
            ring_id(str)            --  Ring ID string
            container_image(str)    --  Name of the container image
            global_registry(str)    --  Global registry for the container
            namespace(str)          --  Namespace of the global registry
            password(str)           --  Password to access new deployments
        """
        self.log.info(f"Request received to create containers for ring [{self.ring_name}]")
        cmd = f"helm repo update; " \
              f"helm upgrade --install {self.ring_name} internal/metallicring --set config.secret.password='{password}' " \
              f"--set-string global.ringid='{ring_id}' --set global.image.tag='{container_image}' " \
              f"--set global.image.registry='{global_registry}' --set global.image.namespace='{namespace}' " \
              f"--create-namespace --namespace {self.ring_name}"
        self.run_command(cmd)

    def wait_for_deployment_to_complete(self):
        """
        Waits for all the deployments to complete
        """
        self.log.info("Request received to wait for deployment to complete")
        commserv = _CONFIG.commserv
        deployments = [commserv.client_name]
        mas = _CONFIG.media_agents
        for media_agent in mas:
            deployments.append(media_agent.client_name)
        wcs = _CONFIG.web_consoles
        for web_console in wcs:
            deployments.append(web_console.client_name)
        wss = _CONFIG.web_servers
        for web_server in wss:
            deployments.append(web_server.client_name)
        nps = _CONFIG.network_proxies
        for network_proxy in nps:
            deployments.append(network_proxy.client_name)
        for deployment in deployments:
            while not self.is_deployment_ready(f"{deployment}", self.ring_name):
                self.log.info(f"Waiting for 2 minutes for deployment [{deployment}] to get initialised")
                time.sleep(self.wait_time)
            self.log.info(f"Deployment [{deployment}] created and initialized")
        self.log.info("All deployments initialized and ready to use")

    def open_port_on_service(self, kubectl_service_name, cv_service_name, port_no):
        """
        Opens a port on a kubectl service
        Args:
            kubectl_service_name(str)   --  Name of the KubeCtl Service
            cv_service_name(str)        --  Name of the cv service
            port_no(int)        --  Port no to be opened on the service
        """
        self.log.info(f"Request received to allow service [{cv_service_name}] on port [{port_no}] for service "
                      f"[{kubectl_service_name}]")
        cmd = "kubectl patch svc %s -p '{\\\"spec\\\":{\\\"ports\\\":[{\\\"port\\\":%s,\\\"name\\\":\\\"%s\\\"}]}}' " \
              "-n %s"
        kube_cmd = cmd % (kubectl_service_name, port_no, cv_service_name, self.ring_name)
        self.run_command(kube_cmd)
        self.log.info(f"Port [{port_no}] open on service [{cv_service_name}] complete")

    def is_deployment_ready(self, deployment_name, ring_name):
        """
        Checks the status of kubectl deployments
        Args:
            deployment_name(str)    -- Name of the deployment
            ring_name(str)          -- Name of the ring
        Returns:
            Bool    -- True if deployment is ready
                        False otherwise
        """
        cmd = f"kubectl get deployments/{deployment_name} -n {ring_name} | Select-String -Pattern " \
              f"'{deployment_name}\s+(\d+/\d+)' " \
              "| ForEach-Object { $_.Matches.Groups[1].Value}"
        status = self.run_command(cmd)
        if status == '1/1':
            return True
        else:
            return False

    def kube_set_context(self, user_context):
        """
        Sets the kubernetes context
        Args:
            user_context(str)       --  User context to be switched to
        """
        self.log.info(f"Setting kubectl context to user [{user_context}]")
        cmd = f"kubectl config use-context {user_context}"
        self.run_command(cmd)
        self.log.info(f"kubectl context set for user [{user_context}]")

    def az_set_subscription(self, subscription_id):
        """
        Sets the azure subscription ID
        Args:
            subscription_id(str)        --  ID of azure subscription
        """
        self.log.info(f"Setting Azure subscription to [{subscription_id}]")
        cmd = f"az account set --subscription {subscription_id}"
        self.run_command(cmd)
        self.log.info(f"Azure subscription set to [{subscription_id}]")

    def run_command(self, command, output_type="formatted"):
        """
        Runs a given command on the controller machine
        Args:
            command(str)        --  Command to be executed
            output_type(str)    --  Type of output to be returned
                                    Default - Formatted
        Returns:
            string output of the command executed
        Raises:
            Exception when execution of command fails
        """
        self.log.info(f"Request received to run the following command - [{command}]")
        command_op = self.local_machine.execute_command(command)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)
        self.log.info(f"Output - [{command_op.output}]."
                      f"Formatted output - [{command_op.formatted_output}]")
        if output_type == cs.CMD_FORMATTED_OP:
            return command_op.formatted_output
        else:
            return command_op.output
