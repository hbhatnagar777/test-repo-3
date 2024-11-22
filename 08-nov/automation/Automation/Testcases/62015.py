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

    _get_default_storage_class_from_cluster()   --  Fetch the default storage class from cluster

    setup()                             --  setup method for test case

    tear_down()                         --  tear down method for testcase

    init_inputs()                       --  Initialize objects required for the testcase

    load_kubeconfig_file()              --  Load Kubeconfig file and connect to the Kubernetes API Server

    create_testbed()                    --  Create the testbed required for the testcase

    delete_testbed()                    --  Delete the testbed created

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    add_data_verify_backup()            --  Add data and verify backup job

    verify_inplace_restore_step()       --  Verify inplace restore job

    run()                               --  Run function of this test case
"""


import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from VirtualServer.VSAUtils import VirtualServerUtils
from Kubernetes import KubernetesUtils
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform backup and inplace restore of applications.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create Namespace, Pod, PVC, deployment  for testbed
    5. Create a Kubernetes client with proxy provided
    6. Create application group for kubernetes
    7. Add content for full backup.
    8. Initiate Full Backup for App group created and verify job completed
    9. Add content and move content for Incremental backup.
    10. Initiate Incremental Backup for App group created and verify job completed
    11. Initiate In-place Full Application Restore and verify job completed
    12. Validate restored files checksum and restored resources
    13. Cleanup testbed
    14. Cleanup clients created.
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - In-place Full Application Restore"
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
        self.proxy_obj = None

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
        self.proxy_obj = Machine(self.controller)

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

    @TestStep()
    def create_testbed(self):
        """Create cluster resources and clients for the testcase
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

        pvc_pod_name = self.testbed_name + '-podpvc'
        self.kubehelper.create_cv_pvc(pvc_pod_name, self.namespace, storage_class=self.storageclass)
        pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(
            pod_name, self.namespace, secret=secret_name, configmap=config_name, pvc_name=pvc_pod_name
        )
        time.sleep(30)
        self.content.append(self.namespace + '/' + pod_name)

        # Creating test deployment
        pvc_deployment_name = self.testbed_name + '-deploypvc'
        self.kubehelper.create_cv_pvc(pvc_deployment_name, self.namespace, storage_class=self.storageclass)
        deployment_name = self.testbed_name + '-deployment'
        self.kubehelper.create_cv_deployment(deployment_name, self.namespace, pvc_deployment_name)
        self.content.append(self.namespace + '/' + deployment_name)

        # Creating test statefulset
        sts_name = self.testbed_name + '-sts'
        self.kubehelper.create_cv_statefulset(sts_name, self.namespace)
        self.content.append(self.namespace + '/' + sts_name)
        time.sleep(60)

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

    @TestStep()
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

        self.log.info("Removing additional setting [MaxRestoreStreams] if present on access node")
        if self.proxy_obj.check_registry_exists("VirtualServer", "MaxRestoreStreams"):
            self.controller.delete_additional_setting(category="VirtualServer", key_name="MaxRestoreStreams")
            self.log.info("Successfully removed additional setting [MaxRestoreStreams]")

        KubernetesUtils.delete_cluster(self, self.clientName)

    @TestStep()
    def add_data_verify_backup(self, backup_type="FULL"):
        """Add data and verify backup job
            Args:
                backup_type     (str)       -- Type of backup job to run (FULL/INCREMENTAL/SYNTH_FULL)
        """
        VirtualServerUtils.decorative_log("Add data to all pods in the test namespace")
        for pod in self.kubehelper.get_namespace_pods(self.namespace):
            self.kubehelper.create_random_cv_pod_data(pod, self.namespace)
            time.sleep(10)

        if backup_type == "FULL":
            for pod in self.kubehelper.get_namespace_pods(self.namespace):
                self.kubehelper.create_random_cv_pod_data(
                    pod, self.namespace, foldername="DELETE", hlink=True, slink=True
                )
                time.sleep(10)

        if backup_type == "INCREMENTAL":
            for pod in self.kubehelper.get_namespace_pods(self.namespace):
                self.kubehelper.move_cv_pod_data(pod, self.namespace, foldername="DELETE")
                time.sleep(10)

        VirtualServerUtils.decorative_log(f"Verify {backup_type} Backup Job")
        self.kubehelper.backup(backup_type)

    @TestStep()
    def verify_inplace_restore_step(self):
        """Verify In-place Restore Step
        """
        VirtualServerUtils.decorative_log("Verify Full Application In-place restore")

        if self.tcinputs.get("UseSingleStream", False):
            self.log.info(f"Setting additional key MaxRestoreStreams to 1 on access node [{self.access_node}]")
            self.controller.add_additional_setting(
                category="VirtualServer",
                key_name="MaxRestoreStreams",
                data_type="INTEGER",
                value="1"
            )

        self.kubehelper.run_restore_validate(
            self.clientName,
            self.storageclass,
            inplace=True
        )

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Run Full Job and incremental job before verifying restore
            self.add_data_verify_backup("FULL")

            before_backup = self.kubehelper.get_all_resources(self.namespace)
            self.add_data_verify_backup("INCREMENTAL")

            # Validate In-place restore
            self.verify_inplace_restore_step()

            # Validate all resources are restored correctly
            VirtualServerUtils.decorative_log("Validate all resources are restored correctly")
            after_restore = self.kubehelper.get_all_resources(self.namespace)
            self.kubehelper.validate_data(before_backup, after_restore)

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step -- Delete testbed, delete client ")
            self.delete_testbed()
