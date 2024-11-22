# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This file is the Helper to interact with Helm binary for helm related automation

Classes Defined:

    HelmHelper      --      Helper class for Helm

        Methods:

            _get_version_info()     :   returns the helm version details

            add_helm_repo()         :   Add Helm repository to cluster

            cleanup_helm_app()      :   Cleanup Helm chart apps in namespace

            deploy_helm_app()       :   Deploy Helm Chart apps in namespace

            execute_helm_command()  :   Execute helm command

            execute_helm_command_and_collect() : Executes helm list command and stores the result in the form of
                                                 tuples(name of resource,namespace ot belongs to)


            initialize_helm_repo()  :   Initialize the Helm repository path

            is_helm_chart_present() :   Check if Helm chart exists in the namespace

            upgrade_helm_app()      :   Upgrades helm apps

        Attributes:

            **version_info**        : Returns the helm version info

"""
import os
import re
from abc import ABCMeta

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from Kubernetes.exceptions import KubernetesException

_KUBERNETES_CONFIG = get_config().Kubernetes


class HelmHelper(object):
    __metaclass__ = ABCMeta

    """Class to interact with a Kubernetes cluster using Helm"""

    def __init__(
            self,
            kubeconfig=_KUBERNETES_CONFIG.KUBECONFIG_FILE,
            repo_path=None,
            repo_name=None,
            remote_machine=None,
            user_name=None,
            password=None):
        """Initialize common variables

            Args:

                kubeconfig      (str)   :   Location of the kubeconfig file

                repo_path       (str)   :   The URI for the repository

                repo_name       (str)   :   Name to save the repository as

                remote_machine  (str)   :   Remote machine where helm is installed

                user_name       (str)   :   User name to access machine

                password        (str)   :   user login password

        """

        self.__kubeconfig = kubeconfig
        self.__repo_path = repo_path
        self.__repo_name = repo_name
        self.__debug_mode = _KUBERNETES_CONFIG.DEBUG_MODE
        self.log = logger.get_log()
        self.__local_machine = None
        self.__version_info = None

        # Creating local machine object

        if remote_machine:
            if not user_name or not password:
                raise KubernetesException('HelmOperations', '103')
            self.__local_machine = Machine(
                machine_name=remote_machine,
                username=user_name,
                password=password)
        else:
            self.__local_machine = Machine()

        self.__version_info = self._get_version_info()
        if not self.__version_info:
            raise KubernetesException(
                'HelmOperations',
                '104')
        self.__local_machine.set_encoding_type('utf8')
        # Rest of the initialization
        self.__helm_cmd_suffix = f"--kubeconfig '{self.__kubeconfig}' --debug"

    def _get_version_info(self):
        """Returns helm version info

            Args:

                None

            Returns:

                dict    --  containing helm version info details

            Raises:

                Exception:

                    if failed to get version info

        """
        output_json = {}
        cmd = f"helm version"
        output = self.__local_machine.execute_command(command=cmd)
        # Handle no helm command line exe found on machine
        if len(output.formatted_output) == 0:
            raise KubernetesException(
                'HelmOperations',
                '104')
        try:
            parsed_str = output.output.replace(
                'version.BuildInfo',
                '').strip()
            pattern_match = re.findall(
                '([_a-zA-Z]+):(null|\"[^\"]*\")', parsed_str)
            for _each_match in pattern_match:
                (_key, _value) = _each_match
                output_json[_key] = _value
        except Exception:
            raise KubernetesException(
                'HelmOperations',
                '105')
        return output_json

    def initialize_helm_repo(self, repo_path):
        """Initialize the Helm repository path

            Args:

                repo_path       (str)   :   Repository path URI
        """
        self.log.info(f"Initializing helm repository with URI [{repo_path}] and name [{os.path.basename(repo_path)}]")
        self.__repo_path = repo_path
        self.__repo_name = os.path.basename(self.__repo_path)

    def execute_helm_command(self, cmd, raise_exception=True):
        """Execute helm command
            Args:

                cmd             (str)   :   Command to execute (without params)

                raise_exception (bool)  :   Raise exception if command fails

        """
        cmd_with_suffix = " ".join([cmd, self.__helm_cmd_suffix])
        if self.__debug_mode:
            cmd = cmd_with_suffix
        self.log.info(f"Executing helm command : [{cmd}]")
        cmd_output = self.__local_machine.execute_command(cmd_with_suffix)
        success = (cmd_output.exit_code == 0) and cmd_output.output

        if self.__debug_mode:
            self.log.info(
                f"Command output : [{cmd_output.output}], exception : [{cmd_output.exception_message}]"
            )

        if raise_exception and not success:
            if cmd_output.exit_code != 0 or cmd_output.exception:
                raise KubernetesException(
                    'HelmOperations', '102', f"Command raised exception : [{cmd_output.exception_message}]"
                )
        else:
            return cmd_output.exception

    def execute_helm_command_and_collect(self, cmd, raise_exception=True):
        """Execute helm command and collect resources
            Args:

                cmd             (str)   :   Command to execute (without params)

                raise_exception (bool)  :   Raise exception if command fails

        """
        cmd_with_suffix = " ".join([cmd, self.__helm_cmd_suffix])
        if self.__debug_mode:
            cmd = cmd_with_suffix
        self.log.info(f"Executing helm command : [{cmd}]")
        cmd_output = self.__local_machine.execute_command(cmd_with_suffix)
        success = (cmd_output.exit_code == 0) and cmd_output.output

        lines = cmd_output.output.strip().split('\n')

        result = []

        for line in lines[1:]:
            parts = line.split()
            name = parts[0]
            namespace = parts[1]
            result.append((name, namespace))

        self.log.info(f"{result}")

        if raise_exception and not success:
            if cmd_output.exit_code != 0 or cmd_output.exception:
                raise KubernetesException(
                    'HelmOperations', '102', f"Command raised exception : [{cmd_output.exception_message}]"
                )
        else:
            return result

    def is_helm_chart_present(self, helm_app_name, namespace):
        """Check if Helm chart exists in the namespace

            Args:

                helm_app_name       (str)   :   Name of the helm application

                namespace           (str)   :   Namespace where application resides
        """
        self.log.info(f"Checking if Helm Chart [{namespace}/{helm_app_name}] is present")
        cmd = f"helm status {helm_app_name} -n {namespace}  --output json"
        if self.execute_helm_command(cmd, raise_exception=False):
            self.log.info(f"Helm release [{helm_app_name}] not present in namespace [{namespace}]")
            return False
        return True

    def add_helm_repo(self):
        """Add Helm repository to cluster
        """
        self.log.info(f"Adding Helm Repository [{self.__repo_path}]")
        if not self.__repo_name or not self.__repo_path:
            raise KubernetesException('HelmOperations', '101')

        # Remove repo if exists already
        cmd = f"helm repo remove {self.__repo_name}"
        self.execute_helm_command(cmd, raise_exception=False)

        cmd = f"helm repo add {self.__repo_name} {self.__repo_path}"
        self.execute_helm_command(cmd)

        cmd = f"helm repo update"
        self.execute_helm_command(cmd)

    def deploy_helm_app(self, helm_app_name, namespace, **kwargs):
        """Deploy Helm Chart apps in namespace

            Args:

                helm_app_name       (str)   :   Name of the helm application

                namespace           (str)   :   Namespace where application resides

            kwargs:

                set_values      (list)      :   Set of values to be defined in charts templates

                set_values_yaml (str)       :   Yaml file path location
        """
        set_values = kwargs.get("set_values", [])
        set_values_yaml = kwargs.get("set_values_yaml", "")
        self.log.info(
            f"Deploying Helm Application [{namespace}/{helm_app_name}]")
        if self.is_helm_chart_present(helm_app_name, namespace):
            self.cleanup_helm_app(helm_app_name, namespace)
        cmd = f"helm install {helm_app_name} {self.__repo_name}/{helm_app_name} -n {namespace} " \
              f"--create-namespace --wait --output json"
        for set_cmd in set_values:
            cmd += f" --set {set_cmd}"
        if set_values_yaml:
            cmd += f" --values {set_values_yaml}"

        self.execute_helm_command(cmd)

    def cleanup_helm_app(self, helm_app_name, namespace):
        """Cleanup Helm chart apps in namespace

            Args:

                helm_app_name       (str)   :   Name of the helm application

                namespace           (str)   :   Namespace where application resides
        """
        self.log.info(f"Cleaning up Helm Application [{namespace}/{helm_app_name}]")
        if self.is_helm_chart_present(helm_app_name, namespace):
            cmd = f"helm uninstall {helm_app_name} -n {namespace}"
            self.execute_helm_command(cmd)

    def upgrade_helm_app(self, helm_app_name, namespace, chart, **kwargs):
        """Upgrade helm chart app

            Args:

                helm_app_name       (str)       -- Helm app name

                namespace           (str)       -- Namespace where app resides

                chart               (str)       -- Chart name in the repo

            kwargs:

                set_values      (list)      :   Set of values to be defined in charts

                set_values_yaml (str)       :   Yaml file path location

        """
        set_values = kwargs.get("set_values", [])
        set_values_yaml = kwargs.get("set_values_yaml", "")
        self.log.info(
            f"Upgrading Helm Application [{namespace}/{helm_app_name}]")
        if not self.is_helm_chart_present(
                helm_app_name,
                namespace):
            raise Exception(
                f"Helm app {helm_app_name} is not present in namespace {namespace}")
        cmd = f"helm upgrade {helm_app_name} {self.__repo_name}/{chart} -n {namespace} " \
              f"--wait --output json --timeout=30m"
        for set_cmd in set_values:
            cmd += f" --set {set_cmd}"
        if set_values_yaml:
            cmd += f" --values {set_values_yaml}"
        self.log.info(f"Helm cmd = {cmd}")
        self.execute_helm_command(cmd=cmd)

    @property
    def version_info(self):
        """returns the helm version info

            Args:
                None

            Returns:

                dict --  Helm version info

        """
        return self.__version_info
