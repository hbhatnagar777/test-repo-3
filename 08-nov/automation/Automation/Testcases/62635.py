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

    compare_content()                   --  Compares source content with backup content

    namespace_labels_backup()           --  Creates an app group with namespace level label selector, Performs backup,
                                            validation

    application_labels_backup()         --  Creates an app group with application level label selector, Performs backup,
                                            validation

    volume_labels_backup()           --  Creates an app group with volume level label selector, Performs backup,
                                            validation

    run()                               --  Run function of this test case
"""


import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
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
    4. Create Namespaces, Pods, PVCs, deployments with labels for testbed
    5. Create a Kubernetes client with proxy provided
    6. Create dummy application group for kubernetes
    7. Add content for full backup.
    8. Create application group using Namespace selectors
    9. Perform Backup and validate
    10. Cleanup Namespace selector based App group
    11. Create application group using Application selectors
    12. Perform Backup and validate
    13. Cleanup Application selector based App group
    14. Create application group using Volume selectors
    15. Perform Backup and validate
    16. Cleanup Volume selector based App group
    17. Cleanup testbed
    18. Cleanup clients created.
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Label selector based app group creation backup validation"
        self.utils = TestCaseUtils(self)
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.controller_id = None
        self.testbed_name = None
        self.namespace1 = None
        self.namespace2 = None
        self.restore_namespace = None
        self.app_grp_name = None
        self.serviceaccount = None
        self.authentication = "Service account"
        self.subclientName = None
        self.subclientNamePrefix = None
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
        self.ns_level_content = []
        self.app_level_content = {}
        self.volume_level_content = {}
        self.default_pod = None
        self.universal_label = None

    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """
        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.namespace1 = self.testbed_name+"-1"
        self.namespace2 = self.testbed_name + "-2"
        self.app_grp_name = self.testbed_name + "-app-grp"
        self.serviceaccount = self.testbed_name + "-sa"
        self.authentication = "Service account"
        self.subclientName = None
        self.subclientNamePrefix = "automation-{}".format(self.id)
        self.clientName = "k8sauto-{}".format(self.id)
        self.destclientName = "k8sauto-{}-dest".format(self.id)
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", automation_config.ACCESS_NODE)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        self.controller = self.commcell.clients.get(self.access_node)
        self.controller_id = int(self.controller.client_id)
        self.proxy_obj = Machine(self.controller)
        self.universal_label = {"testcase": self.testbed_name}
        self.kubehelper = KubernetesHelper(self)
        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

    @TestStep()
    def create_testbed(self):
        """
        Create cluster resources and clients for the testcase
        """

        self.log.info("Creating cluster resources...")
        # Create service account if it doesn't exist
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
        # Creating testbed namespaces if they don't exist
        self.kubehelper.create_cv_namespace(self.namespace1, labels=self.universal_label)
        self.kubehelper.create_cv_namespace(self.namespace2, labels=self.universal_label)
        # Create Services
        svc_name1 = self.testbed_name + '-svc1'
        self.kubehelper.create_cv_svc(svc_name1, self.namespace1, selector=self.universal_label)
        svc_name2 = self.testbed_name + '-svc2'
        self.kubehelper.create_cv_svc(svc_name2, self.namespace2, selector=self.universal_label)

        # Creating test pods with attached PVCs
        pvc_pod_name1 = self.testbed_name + '-podpvc1'
        self.kubehelper.create_cv_pvc(
            pvc_pod_name1,
            self.namespace1,
            storage_class=self.storageclass,
            labels=self.universal_label
        )
        pod_name1 = self.testbed_name + '-pod1'
        self.kubehelper.create_cv_pod(
            pod_name1,
            self.namespace1,
            pvc_name=pvc_pod_name1,
            labels=self.universal_label
        )
        pvc_pod_name2 = self.testbed_name + '-podpvc2'
        self.kubehelper.create_cv_pvc(
            pvc_pod_name2,
            self.namespace2,
            storage_class=self.storageclass,
            labels=self.universal_label)

        pod_name2 = self.testbed_name + '-pod2'
        self.kubehelper.create_cv_pod(
            pod_name2,
            self.namespace2,
            pvc_name=pvc_pod_name2,
            labels=self.universal_label
        )
        time.sleep(30)

        # Creating test deployment with attached PVC
        pvc_deployment_name1 = self.testbed_name + '-deploypvc1'
        self.kubehelper.create_cv_pvc(pvc_deployment_name1,
                                      self.namespace1,
                                      storage_class=self.storageclass,
                                      labels=self.universal_label)

        deployment_name1 = self.testbed_name + '-deployment1'
        self.kubehelper.create_cv_deployment(deployment_name1,
                                             self.namespace1,
                                             pvc_deployment_name1,
                                             labels=self.universal_label)

        time.sleep(60)

        # Creating pod in default NS
        self.default_pod = self.testbed_name + '-default-pod'
        self.kubehelper.create_cv_pod(
            self.default_pod,
            'default',
            labels=self.universal_label
        )

        # Populating expected content arrays

        self.volume_level_content["--all-namespaces_"] = []
        self.volume_level_content["--all-namespaces_"].append(pvc_pod_name1)
        self.volume_level_content["--all-namespaces_"].append(pvc_pod_name2)
        self.volume_level_content["--all-namespaces_"].append(pvc_deployment_name1)
        self.volume_level_content[f"-n {self.namespace2}_"] = []
        self.volume_level_content[f"-n {self.namespace2}_"].append(pvc_pod_name2)

        self.ns_level_content.append(pod_name1)
        self.ns_level_content.append(pod_name2)
        self.ns_level_content.append(deployment_name1)
        self.ns_level_content.append(self.namespace1)
        self.ns_level_content.append(self.namespace2)

        self.app_level_content["--all-namespaces_"] = [self.default_pod]
        self.app_level_content["--all-namespaces_"].append(pod_name1)
        self.app_level_content["--all-namespaces_"].append(pod_name2)
        self.app_level_content["--all-namespaces_"].append(deployment_name1)
        self.app_level_content[f"-n {self.namespace2}_"] = []
        self.app_level_content[f"-n {self.namespace2}_"].append(pod_name2)
        self.app_level_content["_"] = [self.default_pod]

        KubernetesUtils.add_cluster(
            self,
            self.clientName,
            self.api_server_endpoint,
            self.serviceaccount,
            self.servicetoken,
            self.access_node
        )

    def setup(self):
        """
        Testcase setup
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
        self.kubehelper.delete_cv_namespace(self.namespace1)
        self.kubehelper.delete_cv_namespace(self.namespace2)
        self.kubehelper.delete_cv_pod(name=self.default_pod, namespace='default')

        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)

    def compare_content(self, expected_content):
        """
        Compare content of backed up files with expected content
        """
        browse_resp = self.subclient.browse()
        browse_content = [item.lstrip("\\") for item in browse_resp[0]]
        browse_content.sort()
        expected_content.sort()
        self.log.info(f"Browse content: {browse_content}")
        self.log.info(f"Expected content: {expected_content}")
        if browse_content == expected_content:
            self.log.info("Expected content matches backup content")
        else:
            raise Exception("Backed up items do not match source list")

    @TestStep()
    def namespace_labels_backup(self):
        """
        Create app group using namespace labels and perform backup
        """
        content = [f"Selector:Namespaces:testcase={self.testbed_name}"]
        self.subclientName = self.subclientNamePrefix + "-NS"

        KubernetesUtils.add_application_group(
            self,
            content=content,
            plan=self.plan,
            name=self.subclientName,
        )
        self.kubehelper.source_vm_object_creation(self)
        # Perform backup
        self.kubehelper.backup('FULL')
        self.compare_content(expected_content=self.ns_level_content)
        self.log.info('FULL backup job step completed')
        # Remove app group
        KubernetesUtils.delete_application_group(self, self.subclientName)

    @TestStep()
    def application_labels_backup(self, namespaces=""):
        """
        Create app group using application labels and perform backup
        """

        self.log.info(f"Namespace selector: {namespaces}")
        content = [f"Selector:Applications:testcase={self.testbed_name} {namespaces}"]
        if namespaces == "":
            content = [f"Selector:Applications:testcase={self.testbed_name}"]
        self.subclientName = self.subclientNamePrefix + "-APP"
        KubernetesUtils.add_application_group(
            self,
            content=content,
            plan=self.plan,
            name=self.subclientName,
        )
        self.kubehelper.source_vm_object_creation(self)
        # Perform backup
        self.log.info("Running FULL Backup job...")
        self.kubehelper.backup('FULL')
        self.log.info('FULL backup job step completed')
        self.compare_content(expected_content=self.app_level_content[namespaces+"_"])
        # Remove app group
        KubernetesUtils.delete_application_group(self, self.subclientName)

    @TestStep()
    def volume_labels_backup(self, namespaces=""):
        """
        Create app group using volume label selectors and perform backup
        """
        self.log.info(f"Namespace selector: {namespaces}")
        content = [f"Selector:Volumes:testcase={self.testbed_name} {namespaces}"]
        if namespaces == "":
            content = [f"Selector:Volumes:testcase={self.testbed_name}"]
        self.subclientName = self.subclientNamePrefix + "-VOL"
        KubernetesUtils.add_application_group(
            self,
            content=content,
            plan=self.plan,
            name=self.subclientName,
        )
        self.kubehelper.source_vm_object_creation(self)
        # Perform backup
        self.log.info("Running FULL Backup job...")
        self.kubehelper.backup('FULL')
        self.log.info('FULL backup job step completed')
        self.compare_content(expected_content=self.volume_level_content[namespaces+"_"])

        # Remove app group
        KubernetesUtils.delete_application_group(self, self.subclientName)

    def run(self):
        """
        Run the Testcase
        """
        try:

            # Create app group using application labels in default Namespace
            self.application_labels_backup()
            # Create app group using application labels in all Namespaces
            self.application_labels_backup(namespaces='--all-namespaces')
            # Create app group using application labels in Namespace2
            self.application_labels_backup(namespaces=f'-n {self.namespace2}')
            # Create app group using volume labels in all Namespaces
            self.volume_labels_backup(namespaces='--all-namespaces')
            # Create app group using volume labels in Namespace2
            self.volume_labels_backup(namespaces=f'-n {self.namespace2}')
            # Create app group using namespace labels
            self.namespace_labels_backup()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step -- Delete testbed, delete client ")
            self.delete_testbed()
