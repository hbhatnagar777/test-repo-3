# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  initialize TestCase class

    setup()                             --  setup method for test case

    tear_down()                         --  tear down method for testcase

    init_inputs()                       --  Initialize objects required for the testcase

    create_testbed()                    --  Create the testbed required for the testcase

    delete_testbed()                    --  Delete the testbed created

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    run()                               --  Run function of this test case
"""

import time

from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Kubernetes import KubernetesUtils
from Reports.utils import TestCaseUtils
from Kubernetes.KubernetesHelper import KubernetesHelper
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import TestStep, InitStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    test_step = TestStep()

    """
    Testcase to validate the Backup filter functionality.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Login to Command Center, Configure new Cluster and Application Group
    4. Create cluster and application group. Add content with first backup filter
    5. Verify Backup and Restore. Verify excluded content is not backed up
    6. Repeat steps 4 and 5 with different backup filters
    7. Cleanup testbed
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.ns1_rst = None
        self.ns2_rst = None
        self.name = "Kubernetes Backup Filter validation"
        self.utils = TestCaseUtils(self)
        self.admin_console = None
        self.browser = None
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.controller_id = None
        self.testbed_name = None
        self.app_grp_name = None
        self.serviceaccount = None
        self.authentication = "Service account"
        self.subclientName = None
        self.clientName = None
        self.destclientName = None
        self.destinationClient = None
        self.controller = None
        self.agentName = "Virtual Server"
        self.instanceName = "Kubernetes"
        self.backupsetName = "defaultBackupSet"
        self.tcinputs = {}
        self.k8s_config = None
        self.driver = None
        self.backup_filters = None
        self.plan = None
        self.storageclass = None
        self.kubehelper = None
        self.content = []
        self.util_namespace = None
        self.k8s_setup = None
        self.resources_before_backup = None
        self.resources_after_restore = None
        self.__cluster_created = False
        self.ns1 = None
        self.ns2 = None
        self.ns3 = None
        self.ns1_rst = None
        self.ns2_rst = None
        self.ns3_rst = None

        self.ns1_pod_name = None
        self.ns1_pod_labels = None
        self.ns1_deploy_name = None
        self.ns1_svc_name = None
        self.ns1_configmap_name = None
        self.ns1_secret_name = None
        self.ns1_cr_name = None

        self.ns2_pod_name = None
        self.ns2_pod_labels = None
        self.ns2_deploy_name = None
        self.ns2_svc_name = None
        self.ns2_configmap_name = None
        self.ns2_secret_name = None
        self.ns2_cr_name = None

        self.ns3_pod_name1 = None
        self.ns3_depl_name1 = None
        self.ns3_depl_name2 = None
        self.ns3_secret_name1 = None
        self.ns3_pvc_name1 = None

        self.plural = None
        self.group = None

    @InitStep(msg="Load kubeconfig and initialize testcase variables")
    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        # self.testbed_name = "k8s-auto-70840-1723464653"
        self.ns1 = self.testbed_name + "-ns1"
        self.ns2 = self.testbed_name + "-ns2"
        self.ns3 = self.testbed_name + "-ns3"
        self.ns1_rst = self.ns1 + "-rst"
        self.ns2_rst = self.ns2 + "-rst"
        self.ns3_rst = self.ns3 + "-rst"
        self.app_grp_name = self.testbed_name + "-app-grp"
        self.serviceaccount = self.testbed_name + "-sa"
        self.authentication = "Service account"
        self.subclientName = "automation-{}".format(self.id)
        self.clientName = "k8sauto-{}".format(self.id)
        self.server_name = self.clientName
        self.destclientName = "k8sauto-{}-dest".format(self.id)
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", automation_config.ACCESS_NODE)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        self.controller = self.commcell.clients.get(self.access_node)
        self.controller_id = int(self.controller.client_id)
        self.util_namespace = self.testbed_name + '-utils'
        self.ns1_pod_name = self.testbed_name + '-pod1'
        self.ns1_pod_labels = f"{self.testbed_name}=ns1-pod-labels"
        self.ns2_pod_name = self.testbed_name + '-pod2'
        self.ns1_svc_name = self.testbed_name + '-svc1'
        self.ns2_svc_name = self.testbed_name + '-svc2'
        self.ns1_deploy_name = self.testbed_name + '-deploy1'
        self.ns2_deploy_name = self.testbed_name + '-deploy2'
        self.ns1_configmap_name = self.testbed_name + '-cm1'
        self.ns2_configmap_name = self.testbed_name + '-cm2'
        self.ns1_secret_name = self.testbed_name + '-secret1'
        self.ns2_secret_name = self.testbed_name + '-secret2'
        self.ns1_cr_name = self.testbed_name + '-cr1'
        self.ns2_cr_name = self.testbed_name + '-cr2'
        self.ns1_configmap_name = self.testbed_name + '-cm'
        self.ns1_secret_name = self.testbed_name + '-secret'

        self.group = 'cvautomation.example.com'
        self.plural = 'cvautomationcrds'

        self.ns3_pod_name1 = self.testbed_name + '-pod1'
        self.ns3_depl_name1 = self.testbed_name + '-deploy1'
        self.ns3_depl_name2 = self.testbed_name + '-deploy2'
        self.ns3_secret_name1 = self.testbed_name + '-secret1'
        self.ns3_pvc_name1 = self.testbed_name + '-pvc1'
        # Initially filter pod1 and pod2
        self.backup_filters = [f'Kind:Equals:Pod']

        self.content = [self.ns1, self.ns2]

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

        self.k8s_helper = K8sHelper(self.admin_console, self)

    def string_to_dict(self, string):
        key, value = string.split('=')
        result = {key: value}
        self.log.info(result)
        return result

    @InitStep(msg="Create testbed resources on cluster")
    def create_testbed(self):
        """
            Create testbed resources
        """
        self.log.info("Creating cluster resources...")

        # Create service account if doesn't exist
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, sa_namespace)
        #
        # # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, sa_namespace, cluster_role)

        time.sleep(30)
        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, sa_namespace)

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.ns1)
        self.kubehelper.create_cv_namespace(self.ns2)

        # Creating Phase 1 resources - ns1 and ns2
        self.kubehelper.create_cv_pod(self.ns1_pod_name, self.ns1)
        self.kubehelper.create_cv_pod(self.ns2_pod_name, self.ns2)

        self.kubehelper.create_cv_svc(self.ns1_svc_name, self.ns1)
        self.kubehelper.create_cv_svc(self.ns2_svc_name, self.ns2)

        self.kubehelper.create_cv_deployment(self.ns1_deploy_name, self.ns1)
        self.kubehelper.create_cv_deployment(self.ns2_deploy_name, self.ns2)

        self.kubehelper.create_cv_configmap(self.ns1_configmap_name, self.ns1)
        self.kubehelper.create_cv_configmap(self.ns2_configmap_name, self.ns2)

        self.kubehelper.create_cv_secret(self.ns1_secret_name, self.ns1)
        self.kubehelper.create_cv_secret(self.ns2_secret_name, self.ns2)

        self.kubehelper.create_cv_custom_resource(
            group=self.group,
            version='v1',
            plural=self.plural,
            namespace=self.ns1,
            body={
                "apiVersion": "cvautomation.example.com/v1",
                "kind": "CvautomationCrd",
                "metadata": {
                    "name": self.ns1_cr_name
                },
                "spec": {
                    "name": "example",
                    "value": "exampleValue"
                }
            }
        )
        self.kubehelper.create_cv_custom_resource(
            group=self.group,
            version='v1beta1',
            plural=self.plural,
            namespace=self.ns2,
            body={
                "apiVersion": "cvautomation.example.com/v1beta1",
                "kind": "CvautomationCrd",
                "metadata": {
                    "name": self.ns2_cr_name
                },
                "spec": {
                    "description": "This is a second CRD example",
                    "enabled": True
                }
            }
        )

        # Contains all content in Phase 1 of this Testcase - Validating single backup filter exhaustively

        content_dictionary_phase1 = {
            self.ns1: {
                'Pod': [self.ns1_pod_name],
                'Service': [self.ns1_svc_name],
                'Deployment': [self.ns1_deploy_name],
                'ConfigMap': [self.ns1_configmap_name],
                'Secret': [self.ns1_secret_name],
                'CustomResource': [self.ns1_cr_name]
            },
            self.ns2: {
                'Pod': [self.ns2_pod_name],
                'Service': [self.ns2_svc_name],
                'Deployment': [self.ns2_deploy_name],
                'ConfigMap': [self.ns2_configmap_name],
                'Secret': [self.ns2_secret_name],
                'CustomResource': [self.ns2_cr_name]
            }
        }

        # Creating Phase 2 resources - ns3 - Contains a pod and 2 deployments

        self.kubehelper.create_cv_namespace(self.ns3)

        self.kubehelper.create_cv_pod(self.ns3_pod_name1, self.ns3)
        self.kubehelper.create_cv_secret(self.ns3_secret_name1, self.ns3)
        self.kubehelper.create_cv_pvc(self.ns3_pvc_name1, self.ns3)
        self.kubehelper.create_cv_deployment(
            self.ns3_depl_name1,
            self.ns3,
            pvcname=self.ns3_pvc_name1,
            env_secret=self.ns3_secret_name1
        )
        self.kubehelper.create_cv_deployment(
            self.ns3_depl_name2,
            self.ns3
        )
        # pass

    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        self.kubehelper.delete_cv_namespace(self.ns1)
        self.kubehelper.delete_cv_namespace(self.ns2)
        self.kubehelper.delete_cv_namespace(self.ns3)
        self.kubehelper.delete_cv_namespace(self.ns1_rst)
        self.kubehelper.delete_cv_namespace(self.ns2_rst)
        self.kubehelper.delete_cv_namespace(self.ns3_rst)
        self.kubehelper.delete_cv_namespace(self.util_namespace)

        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

    def setup(self):
        """
         Create testbed, launch browser and login
        """
        self.log.info("Step -- Launch browser and login to Command Center")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname
        )
        self.admin_console.login(
            username=self._inputJSONnode['commcell']['commcellUsername'],
            password=self._inputJSONnode['commcell']['commcellPassword']
        )
        self.admin_console.navigate(self.admin_console.base_url)
        self.init_inputs()
        self.create_testbed()

    @test_step
    def create_cluster(self):
        """Step 1 & 2 --  Create Cluster and app group from Command Center"""

        # Cleanup if cluster with same name exists from previous run
        # Step 0 - Cleanup previous cluster
        try:
            self.delete_cluster()
        except CVWebAutomationException as exp:
            self.log.info(exp)

        self.admin_console.navigator.navigate_to_kubernetes()
        self.k8s_helper.configure_new_kubernetes_cluster(
            api_endpoint=self.api_server_endpoint,
            cluster_name=self.server_name,
            authentication=self.authentication,
            service_account=self.serviceaccount,
            service_token=self.servicetoken,
            app_group_name=self.app_grp_name,
            backup_content=self.content,
            plan_name=self.plan,
            access_nodes=self.access_node,
            backup_filters=self.backup_filters
        )
        time.sleep(10)
        KubernetesUtils.populate_client_objects(self, client_name=self.server_name)
        KubernetesUtils.populate_subclient_objects(self, application_group_name=self.app_grp_name)
        self.__cluster_created = True
        self.log.info("Cluster and app group created.. Proceeding with next steps..")

    @test_step
    def delete_app_group(self):
        """Step 7 -- Delete Application Group"""
        self.k8s_helper.delete_k8s_app_grp(self.app_grp_name)

    @test_step
    def delete_cluster(self):
        """Step 8 -- Delete Cluster"""
        self.k8s_helper.delete_k8s_cluster(self.server_name)

    @test_step
    def update_backup_filters(self, filter_list, remove_filters=0, exclude_dependencies=True):
        """
        Update backup filters
        """

        self.k8s_helper.configure_backup_filters(
            cluster=self.server_name,
            app_grp=self.app_grp_name,
            backup_filters=filter_list,
            remove_existing_filters=remove_filters,
            exclude_dependencies=exclude_dependencies
        )

    def get_resources_in_namespace(self, namespace):
        """
        Get all resources in the namespace
        """

        resources = {'Pod': [], 'Service': [], 'Deployment': [], 'ConfigMap': [], 'Secret': [], 'pvc': [],
                     'CustomResource': []}
        all_resources = self.kubehelper.get_all_resources(namespace)
        resources['Pod'] = all_resources['Pod']
        resources['Service'] = all_resources['Service']
        resources['Deployment'] = all_resources['Deployment']
        resources['ConfigMap'] = all_resources['ConfigMap']
        resources['Secret'] = all_resources['Secret']
        resources['Pvc'] = all_resources['PersistentVolumeClaim']
        resources['CustomResource'] = self.kubehelper.get_namespace_custom_resources(namespace)
        return resources

    @test_step
    def run_backup_restore_validate(self, validation_dict, restore_name_map):
        """
        Run backup and restore job. Validate backup filter functionality
        """

        self.kubehelper.backup("FULL")
        self.log.info("Backup job completed successfully.. Proceeding with restore")
        self.kubehelper.namespace_level_restore(
            namespace_list=self.content,
            restore_name_map=restore_name_map,
            overwrite=True
        )
        self.log.info("Restore job completed successfully.. Proceeding with validation")

        resources_after_restore = {}
        for key in validation_dict.keys():
            resources_after_restore[key] = self.get_resources_in_namespace(namespace=f'{key}-rst')
            self.kubehelper.validate_data(
                resoures_before_backup=validation_dict[key],
                resources_after_restore=resources_after_restore[key]
            )
        # pass

    @test_step
    def update_backup_filter(self, filter_list, remove_filters):
        """
        Update backup filters

        filter_list:    (List)  List of filters to be added

        remove_filters: (int)   Number of filters to be removed

        """
        self.k8s_helper.update_backup_filters(
            cluster_name=self.server_name,
            filter_list=filter_list,
            remove_filters=remove_filters
        )

    @test_step
    def add_app_group(self, content):
        """
        Add application group with content
        """

        KubernetesUtils.add_application_group(
            self,
            content=content,
            plan=self.plan,
            name=self.subclientName,
        )
        self.kubehelper.source_vm_object_creation(self)

    def run(self):
        """
        Run the Testcase - Verify CRUD operations
        """
        try:
            # Step 1 & 2 - Create cluster & application group with namespace as content. Add backup filters as exclusion
            self.create_cluster()

            self.kubehelper.source_vm_object_creation(self)

            # PHASE 1: Validate backup filter exhaustively with single filter Each time

            # Step 3 - Run backup and restore job.
            # Validate backup filter functionality - Exclude all of Kind Pods
            # Pods should be excluded

            self.run_backup_restore_validate(
                validation_dict={
                    self.ns1: {
                        'Pod': [],
                        'Service': [self.ns1_svc_name],
                        'Deployment': [self.ns1_deploy_name],
                        'ConfigMap': [self.ns1_configmap_name],
                        'Secret': [self.ns1_secret_name],
                        'CustomResource': [self.ns1_cr_name],
                        'Pvc': []
                    },
                    self.ns2: {
                        'Pod': [],
                        'Service': [self.ns2_svc_name],
                        'Deployment': [self.ns2_deploy_name],
                        'ConfigMap': [self.ns2_configmap_name],
                        'Secret': [self.ns2_secret_name],
                        'CustomResource': [self.ns2_cr_name],
                        'Pvc': []
                    }
                },
                restore_name_map={self.ns1: self.ns1_rst, self.ns2: self.ns2_rst}
            )

            # Step 4 - Remove old filter and add new one - Namespace not equals ns2. Will filter out NS1

            self.update_backup_filters(filter_list=[f'Namespace:Does not equal:{self.ns2}'], remove_filters=1)

            # Step 5 - Run backup and restore job. Validate backup filter functionality

            self.run_backup_restore_validate(
                validation_dict={
                    self.ns1: {
                        'Pod': [],
                        'Service': [],
                        'Deployment': [],
                        'ConfigMap': [],
                        'Secret': [],
                        'CustomResource': [],
                        'Pvc': []
                    },
                    self.ns2: {
                        'Pod': [self.ns2_pod_name],
                        'Service': [self.ns2_svc_name],
                        'Deployment': [self.ns1_pod_name],
                        'ConfigMap': [self.ns1_pod_name],
                        'Secret': [self.ns1_secret_name],
                        'CustomResource': [self.ns1_pod_name],
                        'Pvc': []
                    }
                },
                restore_name_map={self.ns1: self.ns1_rst, self.ns2: self.ns2_rst}
            )

            # Step 6 - Remove old filter and add new one - Namespace ends with ns2. Will filter out elements from NS2
            self.update_backup_filters(filter_list=[f'Namespace:Ends with:{self.ns2[4:]}'])
            # Step 5 - Run backup and restore job. Validate backup filter functionality

            self.run_backup_restore_validate(
                validation_dict={
                    self.ns1: {
                        'Pod': [],
                        'Service': [],
                        'Deployment': [],
                        'ConfigMap': [],
                        'Secret': [],
                        'CustomResource': [],
                        'Pvc': []
                    },
                    self.ns2: {
                        'Pod': [],
                        'Service': [],
                        'Deployment': [],
                        'ConfigMap': [],
                        'Secret': [],
                        'CustomResource': [],
                        'Pvc': []
                    }
                },
                restore_name_map={self.ns1: self.ns1_rst, self.ns2: self.ns2_rst}
            )

            # Step 6 - Remove old filter and add new one - Name starts with ns1_secret. Will filter out NS1 secret
            self.update_backup_filters(filter_list=[f'Name:Starts with:{self.ns1_secret_name}'], remove_filters=2)

            # Step 5 - Run backup and restore job. Validate backup filter functionality

            self.run_backup_restore_validate(
                validation_dict={
                    self.ns1: {
                        'Pod': [self.ns1_pod_name],
                        'Service': [self.ns1_svc_name],
                        'Deployment': [self.ns1_deploy_name],
                        'ConfigMap': [self.ns1_configmap_name],
                        'Secret': [],
                        'CustomResource': [self.ns1_cr_name],
                        'Pvc': []
                    },
                    self.ns2: {
                        'Pod': [self.ns2_pod_name],
                        'Service': [self.ns2_svc_name],
                        'Deployment': [self.ns2_deploy_name],
                        'ConfigMap': [self.ns2_configmap_name],
                        'Secret': [self.ns2_secret_name],
                        'CustomResource': [self.ns2_cr_name],
                        'Pvc': []
                    }
                },
                restore_name_map={self.ns1: self.ns1_rst, self.ns2: self.ns2_rst}
            )

            # Step 6 - Remove old filter and add new one - label equals pod label. will filter out the pod1

            self.update_backup_filters(filter_list=[f'Label:Equals:{self.ns1_pod_labels}'], remove_filters=1)

            # Step 5 - Run backup and restore job. Validate backup filter functionality

            self.run_backup_restore_validate(
                validation_dict={
                    self.ns1: {
                        'Pod': [],
                        'Service': [self.ns1_svc_name],
                        'Deployment': [self.ns1_deploy_name],
                        'ConfigMap': [self.ns1_configmap_name],
                        'Secret': [self.ns1_secret_name],
                        'CustomResource': [self.ns1_cr_name],
                        'Pvc': []
                    },
                    self.ns2: {
                        'Pod': [self.ns2_pod_name],
                        'Service': [self.ns2_svc_name],
                        'Deployment': [self.ns2_deploy_name],
                        'ConfigMap': [self.ns2_configmap_name],
                        'Secret': [self.ns2_secret_name],
                        'CustomResource': [self.ns2_cr_name],
                        'Pvc': []
                    }
                },
                restore_name_map={self.ns1: self.ns1_rst, self.ns2: self.ns2_rst}

            )

            # Step 7 - Keep old filter and add new one - group contains apps. Will filter out depl

            self.update_backup_filters(filter_list=[f'Group:Contains:apps'], remove_filters=0)

            self.run_backup_restore_validate(
                validation_dict={
                    self.ns1: {
                        'Pod': [],
                        'Service': [self.ns1_svc_name],
                        'Deployment': [],
                        'ConfigMap': [self.ns1_configmap_name],
                        'Secret': [self.ns1_secret_name],
                        'CustomResource': [self.ns1_cr_name],
                        'Pvc': []
                    },
                    self.ns2: {
                        'Pod': [self.ns2_pod_name],
                        'Service': [self.ns2_svc_name],
                        'Deployment': [],
                        'ConfigMap': [self.ns2_configmap_name],
                        'Secret': [self.ns2_secret_name],
                        'CustomResource': [self.ns2_cr_name],
                        'Pvc': []
                    }
                },
                restore_name_map={self.ns1: self.ns1_rst, self.ns2: self.ns2_rst}
            )

            # Step 8 - Remove old filter and add new one - version not contains beta, will filter out
            # all but the v1beta1 custom resources

            self.update_backup_filters(filter_list=[f'Version:Does not contain:beta'], remove_filters=0)

            self.run_backup_restore_validate(
                validation_dict={
                    self.ns1: {
                        'Pod': [],
                        'Service': [],
                        'Deployment': [],
                        'ConfigMap': [],
                        'Secret': [],
                        'CustomResource': [],
                        'Pvc': []
                    },
                    self.ns2: {
                        'Pod': [],
                        'Service': [],
                        'Deployment': [],
                        'ConfigMap': [],
                        'Secret': [],
                        'CustomResource': [self.ns2_cr_name],
                        'Pvc': []
                    }
                },
                restore_name_map={self.ns1: self.ns1_rst, self.ns2: self.ns2_rst}
            )

            # Step 7 - Delete Application Group
            self.delete_app_group()

            # Step 8 - add new app group with content from ns3

            self.add_app_group(content=[self.ns3])

            # Step 9 - Add filters - NS equals ns3, Group not equals apps, name not equals ns3_deploy2.
            # Disable exclude dependencies.
            self.update_backup_filters(
                filter_list=['Group:Does not equal:apps', f'Name:Does not equal:{self.ns3_depl_name2}'],
                exclude_dependencies=False
            )

            # Step 10 - Run backup and restore job. Validate backup filter functionality. Expected that the
            # deployment ns3_deploy2 is backed up and restored. The secret ns3_secret1 and ns3_pvc1 is also backed up
            # since we disabled exclude dependencies

            self.run_backup_restore_validate(
                validation_dict={
                    self.ns3: {
                        'Pod': [],
                        'Service': [],
                        'Deployment': [self.ns3_depl_name2],
                        'ConfigMap': [],
                        'Secret': [self.ns3_secret_name1],
                        'CustomResource': [],
                        'Pvc': [self.ns3_pvc_name1]
                    }
                },
                restore_name_map={self.ns3: self.ns3_rst}
            )

            self.delete_app_group()

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:

            try:
                if self.__cluster_created:
                    pass
                    # Step 4 - Delete cluster step
                    # self.delete_cluster()

            except Exception as error:
                self.utils.handle_testcase_exception(error)

    def tear_down(self):
        """
            Teardown testcase - Delete testbed
        """
        Browser.close_silently(self.browser)
        self.delete_testbed()
