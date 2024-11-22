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

    load_kubeconfig_file()              --  Load Kubeconfig file and connect to the Kubernetes API Server

    create_testbed()                    --  Create the testbed required for the testcase

    delete_testbed()                    --  Delete the testbed created

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    run()                               --  Run function of this test case
"""


import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from VirtualServer.VSAUtils import VirtualServerUtils
from Kubernetes import KubernetesUtils

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform backup and restore of applications.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create Namespace, Pod, PVC, deployment  for testbed
    5. Create a Kubernetes client with proxy provided
    6. Create application group for kubernetes
    7. Add content for full validation.
    8. Initiate Full Backup for App group created and verify job completed
    9. Initiate out-of-place Full Application Restore and verify job completed
    10. Add content for Incremental  validation.
    11. Initiate Incremental Backup for App group created and verify job completed
    12. Initiate out-of-place Full Application Restore and verify job completed
    13. Initiate Synthfull Backup for App group created and verify job completed
    14. Initiate out-of-place Synthfull  Application Restore and verify job completed
    15. Cleanup testbed
    16. Cleanup client created.
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes Storage Validations"
        self.utils = TestCaseUtils(self)
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.controller_id = None
        self.testbed_name = None
        self.namespace = None
        self.restore_namespace = None
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
        self.plan = None
        self.storageclass = None
        self.kubehelper = None
        self.content = []

    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """
        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.namespace = self.testbed_name
        self.restore_namespace = self.namespace + "-rst"
        self.app_grp_name = self.testbed_name + "-app-grp"
        self.serviceaccount = self.testbed_name + "-sa"
        self.authentication = "Service account"
        self.subclientName = "automation-{}".format(self.id)
        self.clientName = "k8sauto-{}".format(self.id)
        self.destclientName = "k8sauto-{}-dest".format(self.id)
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", automation_config.ACCESS_NODE)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        self.controller = self.commcell.clients.get(self.access_node)
        self.controller_id = int(self.controller.client_id)

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

    def create_testbed(self):
        """
            1. Create Service Account
            2. Create Cluster Role Binding
            3. Get SA token
            4. Create namespace and restore namespace
            5. Create PVC
            6. Create test Pod
            7. Generate random data in Pod
        """

        self.log.info("Creating cluster resources...")

        # Create service account if doesn't exist
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, sa_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, sa_namespace, cluster_role)

        time.sleep(30)
        self.servicetoken = self.kubehelper.get_serviceaccount_token(
            self.serviceaccount, sa_namespace
        )

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)

        # Creating namespace for restore if not exists
        self.kubehelper.create_cv_namespace(self.restore_namespace)

        # Create Service
        svc_name = self.testbed_name + '-svc'
        self.kubehelper.create_cv_svc(svc_name, self.namespace)

        # Creating test pod
        secret_name = self.testbed_name + '-secret'
        config_name = self.testbed_name + '-cm'
        self.kubehelper.create_cv_secret(secret_name, self.namespace)
        self.kubehelper.create_cv_configmap(config_name, self.namespace)

        pod_pvc_name = self.testbed_name + '-podpvc'
        self.kubehelper.create_cv_pvc(pod_pvc_name, self.namespace, storage_class=self.storageclass)

        pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(
            pod_name, self.namespace, secret=secret_name, configmap=config_name, pvc_name=pod_pvc_name
        )
        time.sleep(30)
        self.content.append(self.namespace + '/' + pod_name)

        # Creating test deployment
        pvc_deployment_name = self.testbed_name + '-deploypvc'
        self.kubehelper.create_cv_pvc(pvc_deployment_name, self.namespace, storage_class=self.storageclass)
        deployment_name = self.testbed_name + '-deployment'
        self.kubehelper.create_cv_deployment(deployment_name, self.namespace, pvc_deployment_name)
        self.content.append(self.namespace + '/' + deployment_name)

        KubernetesUtils.add_cluster(
            self,
            self.clientName,
            self.api_server_endpoint,
            self.serviceaccount,
            self.servicetoken,
            self.access_node
        )
        KubernetesUtils.add_application_group(
            self,
            content=self.content,
            plan=self.plan,
            name=self.subclientName,
        )

    def setup(self):
        """
        Setup the Testcase
        """
        try:
            self.init_inputs()
            self.create_testbed()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def delete_testbed(self):
        """
        Delete the generated testbed
        """

        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)

        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)

    def run(self):
        """
        Run the Testcase
        """
        try:
            self.kubehelper.source_vm_object_creation(self)

            VirtualServerUtils.decorative_log("Step 1 -- Add more data and verify FULL backup")
            for pod in self.kubehelper.get_namespace_pods(self.namespace):
                self.kubehelper.create_random_cv_pod_data(pod, self.namespace, foldername="FULL")
                time.sleep(10)

            before_backup = self.kubehelper.get_all_resources(self.namespace)
            self.kubehelper.backup('FULL')

            self.log.info("Running Restore")
            self.kubehelper.restore_out_of_place(
                self.clientName,
                self.restore_namespace,
                self.storageclass
            )

            self.log.info("Running Validation")
            after_backup = self.kubehelper.get_all_resources(self.restore_namespace)
            self.kubehelper.validate_data(before_backup, after_backup)
            self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)

            VirtualServerUtils.decorative_log("Step 2 -- Add more data and verify Incremental backup")
            for pod in self.kubehelper.get_namespace_pods(self.namespace):
                self.kubehelper.create_random_cv_pod_data(pod, self.namespace, foldername="INCR")
                time.sleep(10)
            self.kubehelper.backup('INCREMENTAL')
            self.log.info("Running Restore")
            self.kubehelper.restore_out_of_place(
                self.clientName,
                self.restore_namespace,
                self.storageclass,
            )

            self.log.info("Running Validation")
            after_backup = self.kubehelper.get_all_resources(self.restore_namespace)
            self.kubehelper.validate_data(before_backup, after_backup)

            self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)

            VirtualServerUtils.decorative_log(
                "Step 3 -- Move content and Run Incremental Backup, followed by Out of place Restore"
            )
            self.log.info("Moving the content")
            for pod in self.kubehelper.get_namespace_pods(self.namespace):
                self.kubehelper.move_cv_pod_data(pod, self.namespace, foldername="FULL")
                time.sleep(10)
            self.kubehelper.backup('INCREMENTAL')
            self.kubehelper.restore_out_of_place(
                self.clientName,
                self.restore_namespace,
                self.storageclass
            )

            self.log.info("Running Validation")
            after_backup = self.kubehelper.get_all_resources(self.restore_namespace)
            self.kubehelper.validate_data(before_backup, after_backup)

            self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)

            VirtualServerUtils.decorative_log(
                "Step 4 -- Run Synthetic Full job, followed by Application Out of place Restore"
            )
            self.log.info("Running Synthetic full job")
            self.kubehelper.backup('SYNTHETIC_FULL')
            self.kubehelper.restore_out_of_place(
                self.clientName,
                self.restore_namespace,
                self.storageclass,
            )

            self.log.info("Running Validation")
            after_backup = self.kubehelper.get_all_resources(self.restore_namespace)
            self.kubehelper.validate_data(before_backup, after_backup)
            self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)
            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            VirtualServerUtils.decorative_log("Step 5 -- Delete testbed, delete client ")
            self.delete_testbed()
