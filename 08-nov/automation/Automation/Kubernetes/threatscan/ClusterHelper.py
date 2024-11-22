# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for threat scan cluster server running on kubernetes

Classes : ClusterHelper class is defined in this file

ClusterHelper       --  helper class for creating & managing threat scan cluster in AKS

ClusterHelper:

    __init__()                             --  returns the instance of ClusterHelper class

    get_cs_image_tag()                     --  returns the current CU/SP level image tag of CS

    __is_deployment_upgrade_required()     --  returns whether deployment pod image upgrade is needed or not

    __upgrade_helm_deployment()            --  upgrades deployment image to match with CS version

    upgrade_TA_cluster()                   --  Upgrades TA cluster deployment images to match with CS version

    check_TA_Cluster_status()              --  Checks whether all components in TA cluster is up and running

"""""

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.Performance.Utils.performance_helper import AutomationCache
from AutomationUtils import database_helper
from AutomationUtils.database_helper import CommServDatabase
from Install.softwarecache_validation import DownloadValidation
from dynamicindex.utils import constants as dynamic_constants
from Kubernetes.HelmHelper import HelmHelper
from Kubernetes.akscluster_helper import AksClientHelper
from Kubernetes.threatscan import constants as ta_const
from Kubernetes.kubectl_helper import KubectlHelper
from Kubernetes import constants as kuber_constants

_CONFIG_DATA = get_config().DynamicIndex.ThreatScanCluster
_CS_CONFIG_DATA = get_config().SQL


class ClusterHelper:
    """Helper class to manage threat scan cluster in kubernetes"""

    def __init__(
            self,
            commcell_object):
        """Initialize the ClusterHelper class

            Args:

                commcell_object         (obj)       --  Instance of commcell class object

            ********* Please make sure we have inputs for "ThreatScanCluster" dict in config.json *******

        """
        self._commcell = commcell_object
        self.log = logger.get_log()
        self.cache = AutomationCache()
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
            repo_name=ta_const.CV_REPO_NAME,
            repo_path=ta_const.CV_REPO_PATH)
        self.log.info("Initialized HelmHelper object")

    def get_cs_image_tag(self):
        """returns the current CU/SP level image tag of CS

            Args:

                None

            Returns:

                str - CS version in <version>.<SP>.<CU>.Rev<revid> format
        """
        # this function is being called for multiple deployment upgrade so added
        # cache logic
        cache_key = self._commcell.commserv_name
        if self.cache.is_exists(cache_key):
            return self.cache.get_key(cache_key)
        else:
            database_helper.set_csdb(CommServDatabase(self._commcell))
            self.log.info(
                f"Going to find revision id for SP level - {self._commcell.commserv_version}")
            download_obj = DownloadValidation(self._commcell)
            _rev, _, _ = download_obj.get_sp_info(
                self._commcell.commserv_version)
            self.log.info(f"Revision id = {_rev}")
            cache_value = f"{self._commcell.version}.Rev{_rev}"
            self.cache.put_key(cache_key, cache_value)
            return cache_value

    def __is_deployment_upgrade_required(
            self, deploy_name, name_space='default'):
        """returns whether deployment pod image upgrade is required or not

            Args:

                deploy_name     (str)       --  Deployment name

                name_space      (str)       --  Deployment name space (Default - Default namespace)

            Returns:

                bool    -- Specifies whether deployment pod upgrade required or not

            Raises:

                Exception:

                    if failed to find image level details on CS/POD

        """
        cs_version = self.get_cs_image_tag()
        pod_version = None
        _deploy_details = self.kube_master.get_deployment_image(
            name=deploy_name, name_space=name_space)
        for _each_deploy in _deploy_details:
            if deploy_name in _each_deploy:
                # all our cv's pods are single container. so handle that alone
                _container_details = _each_deploy[deploy_name][0]
                _container_name = next(iter(_container_details))
                _image = _container_details[_container_name][kuber_constants.FIELD_IMAGE]
                pod_version = _image.split(":")[1]
                break
        self.log.info(
            f"Comparing Image tag (CS & POD) - {cs_version} & {pod_version}")
        cs_array = cs_version.split(".")
        pod_array = pod_version.split(".")
        if len(cs_array) != len(pod_array):
            raise Exception("Image tag format mismatch. Please check logs")
        if cs_array != pod_array:
            return True
        return False

    def __upgrade_helm_deployment(
            self,
            name,
            name_space,
            helm_app_name,
            chart_name):
        """upgrades deployment pod image to match with CS version

            Args:

                name        (str)       --  Deployment name

                name_space  (str)       --  Deployment name space

                helm_app_name  (str)    --  Helm app name for this deployment

                chart_name      (str)   --  Helm chart name for this deployment

            Returns:

                None

            Raises:

                Exception:

                    if failed to upgrade deployment
        """
        if self.__is_deployment_upgrade_required(
                deploy_name=name, name_space=name_space):
            self.log.info(
                f"Upgrade Required for deployment - {name}")
            _pod_name = self.kube_master.get_pods(
                namespace=name_space,
                selector=f"{ta_const.DEPLOYMENT_NAME_LABEL}{name}")
            # deployments can have many instances of pod running. Never worry
            # about all images. just pick 1st one for validation
            _pod_name = _pod_name[0]
            self.log.info(
                f"Corresponding POD running for deployment[{name}] is - {_pod_name}")
            image_tag = f"{_CONFIG_DATA.Default_ACR}/{chart_name}:{self.get_cs_image_tag()}"
            self.log.info(f"Image tag formed for Upgrade - {image_tag}")
            _set_values = [
                f'{ta_const.LABEL_IMAGE_LOC}"{image_tag}"',
                f'{ta_const.LABEL_IMAGE_PULL_SECRET}"{_CONFIG_DATA.ImageSecrets.Name}"',
                f'{ta_const.LABEL_CLIENT_NAME}{name}']  # deployment name is the client name so set it explicitly in all upgrade calls
            self.log.info(f"Set values formed for Helm = {_set_values}")
            self.helm_master.upgrade_helm_app(
                helm_app_name=helm_app_name,
                namespace=name_space,
                chart=ta_const.ACCESS_NODE_CHART_NAME,
                # Accessnode is the helm chart name used for both IS and
                # scalemgr
                set_values=_set_values)

    def check_TA_Cluster_status(
            self,
            cluster_name=_CONFIG_DATA.Default_Cluster,
            resource_group=_CONFIG_DATA.Default_ResourceGroup,
            **kwargs):
        """Checks whether all components in cluster are up and running

            Args:

                cluster_name        (str)       -- Name of the cluster

                resource_group      (str)       -- cluster Resource group name

            **kwargs options**

                ScaleMgr             -- Deployment name of scale manager pod

                ScaleMgr_NameSpace   -- Deployment namespace of scalemgr pod

                AccessNode           -- Deployment name of static access node pod

                AccessNode_NameSpace -- Deployment namespace of static access node pod


            Returns:

                None

            Raises:

                Exception:

                    if failed to get cluster pods status
        """
        self.az_master.get_credentials(
            cluster_name=cluster_name,
            resource_group=resource_group)
        self.log.info(f"Checking Status of ScaleManager POD")
        scale_mgr_name = kwargs.get(
            'ScaleMgr', _CONFIG_DATA.ScaleMgr_Deployment_Name)
        scale_mgr_namespace = kwargs.get(
            'ScaleMgr_NameSpace',
            _CONFIG_DATA.Default_NameSpace)
        if not self.kube_master.check_deployment_status(
                name=scale_mgr_name, name_space=scale_mgr_namespace):
            raise Exception("Scale Manager Pod is not in ready state")
        self.log.info("***** Scale Manager Pod is READY *****")
        self.log.info(f"Checking Status of Access Node POD")
        access_node_name = kwargs.get(
            'AccessNode', _CONFIG_DATA.IndexServer_Deployment_Name)
        access_node_namespace = kwargs.get(
            'AccessNode_NameSpace',
            _CONFIG_DATA.Default_NameSpace)
        if not self.kube_master.check_deployment_status(
                name=access_node_name, name_space=access_node_namespace):
            raise Exception("Access node Pod is not in ready state")
        self.log.info("***** Access node Pod is READY *****")

        self.log.info(f"Checking Status of Content Extractor POD")
        if not self.kube_master.check_deployment_status(
                name=_CONFIG_DATA.CE_Deployment_Name):
            raise Exception("Content extractor Pod is not in ready state")
        self.log.info("***** Content extractor Pod is READY *****")

        self.log.info(f"Checking Status of Index server controller POD")
        if not self.kube_master.check_deployment_status(
                name=_CONFIG_DATA.DcubeCtrlr_Deployment_Name,
                name_space=_CONFIG_DATA.Default_DCube_NameSpace):
            raise Exception(
                "Index Server controller Pod is not in ready state")
        self.log.info("***** Index Server Controller Pod is READY *****")

    def upgrade_TA_cluster(
            self,
            cluster_name=_CONFIG_DATA.Default_Cluster,
            resource_group=_CONFIG_DATA.Default_ResourceGroup, **kwargs):
        """Upgrades TA cluster deployment images to match with CS version

            Args:

                cluster_name        (str)       -- Name of the cluster

                resource_group      (str)       -- cluster Resource group name

            **kwargs options**

                ScaleMgr             -- Deployment name of scale manager pod

                ScaleMgr_NameSpace   -- Deployment namespace of scalemgr pod

                AccessNode           -- Deployment name of static access node pod

                AccessNode_NameSpace -- Deployment namespace of static access node pod


            Returns:

                None

            Raises:

                Exception:

                    if failed to upgrade TA cluster pods
        """
        self.az_master.get_credentials(
            cluster_name=cluster_name,
            resource_group=resource_group)
        self.log.info(f"Analyzing ScaleManager POD")
        scale_mgr_name = kwargs.get(
            'ScaleMgr', _CONFIG_DATA.ScaleMgr_Deployment_Name)
        scale_mgr_namespace = kwargs.get(
            'ScaleMgr_NameSpace',
            _CONFIG_DATA.Default_NameSpace)
        self.__upgrade_helm_deployment(
            name=scale_mgr_name,
            name_space=scale_mgr_namespace,
            helm_app_name=_CONFIG_DATA.ScaleMgr_Helm_AppName,
            chart_name=ta_const.ACCESS_NODE_CHART_NAME)
        self.log.info("***** Scale Manager POD upgrade completed *****")
        self.log.info(f"Analyzing Access node POD")
        access_node_name = kwargs.get(
            'AccessNode', _CONFIG_DATA.IndexServer_Deployment_Name)
        access_node_namespace = kwargs.get(
            'AccessNode_NameSpace',
            _CONFIG_DATA.Default_NameSpace)
        self.__upgrade_helm_deployment(
            name=access_node_name,
            name_space=access_node_namespace,
            helm_app_name=_CONFIG_DATA.IndexServer_Helm_AppName,
            chart_name=ta_const.INDEX_SERVER_CHART_NAME)
        self.log.info("***** Access node POD upgrade completed *****")
        self.log.info(f"Analyzing Content Extractor POD")
        # CE pods is common to all rings in the cluster, so it will be in default namespace
        # only
        if self.__is_deployment_upgrade_required(
                deploy_name=_CONFIG_DATA.CE_Deployment_Name):
            self.log.info(f"CE pod upgrade required")
            image_tag = f'{_CONFIG_DATA.Default_ACR}/{ta_const.CE_CHART_NAME}:{self.get_cs_image_tag()}'
            self.log.info(f"Image tag formed for Upgrade - {image_tag}")
            self.kube_master.set_deployment_image(
                image=image_tag,
                name=_CONFIG_DATA.CE_Deployment_Name,
                container_name=_CONFIG_DATA.CE_Container_Name)
        self.log.info("***** Content Extractor POD upgrade completed *****")

        self.log.info(f"Analyzing Index Server Cluster POD")
        # IS pods is common to all rings in the cluster, so it will be in datacube namespace
        # only
        if self.__is_deployment_upgrade_required(
                deploy_name=_CONFIG_DATA.DcubeCtrlr_Deployment_Name,
                name_space=_CONFIG_DATA.Default_DCube_NameSpace):
            self.log.info(f"DataCube pod upgrade required")
            image_tag = f'{_CONFIG_DATA.Default_DataCube_ACR}/{ta_const.INDEX_SERVER_CHART_NAME}:{self.get_cs_image_tag()}'
            self.log.info(f"Image tag formed for Upgrade - {image_tag}")
            self.kube_master.set_deployment_image(
                image=image_tag,
                name=_CONFIG_DATA.DcubeCtrlr_Deployment_Name,
                name_space=_CONFIG_DATA.Default_DCube_NameSpace,
                container_name=_CONFIG_DATA.DcubeCtrlr_Container_Name)
            # delete existing deployment else slave pod spawned by controller will
            # be running with older image
            self.kube_master.delete_deployment_app(
                name_space=_CONFIG_DATA.Default_DCube_NameSpace,
                selector=f"{ta_const.DEPLOYMENT_APP_LABEL}{ta_const.IS_APP_NAME}")
            self.kube_master.do_rollout_restart(
                resource=ta_const.LABEL_DEPLOYMENT,
                namespace=_CONFIG_DATA.Default_DCube_NameSpace)
        self.log.info("***** Index Server Cluster POD upgrade completed *****")
        self.log.info(
            "TA cluster Upgrade done")
