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

    many_files_backup()                 --  FULL backup of 10000 small files of size 1kb each

    huge_files_backup()                 --  FULL backup of 10 huge files of size 1G each

    verify_app_level_oop_restore        --  Out-Of-Place restore and comparison of hashsum of files in source and
                                            destination

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    run()                               --  Run function of this test case
"""


import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes import KubernetesUtils
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform backup and restore (OOP and IP) of Pod.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create 2 Namespaces, 2 Pod, 2 PVC for testbed
    5. Populate one PVC with 10000 small files and another PVC with 8 large files of size 1GB
    6. Create a Kubernetes client with proxy provided
    7. Create 2 application groups for both namespaces
    8. Initiate Full Backup for first app group created and verify job completed
    10. Initiate out-of-place Full Application Restore of the first app group and verify job completed
    11. Compare Hashsum of files present in source and destination
    12. Initiate Full Backup for second app group created and verify job completed
    13. Initiate out-of-place Full Application Restore of the second app group and verify job completed
    14. Compare Hashsum of files present in source and destination
    15. Cleanup testbed
    16. Cleanup client created.
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes : Backup and restore of large data"
        self.utils = TestCaseUtils(self)
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.controller_id = None
        self.testbed_name = None
        self.namespace_1 = None
        self.namespace_2 = None
        self.restore_namespace = None
        self.pod_1 = None
        self.pod_2 = None
        self.src_checksum = None
        self.dest_checksum = None
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
        self.namespace_1 = self.testbed_name
        self.namespace_2 = self.testbed_name + '-2'
        self.restore_namespace = self.namespace_1 + "-rst"
        self.app_grp_name = self.testbed_name + "-app-grp"
        self.serviceaccount = self.testbed_name + "-sa"
        self.authentication = "Service account"
        self.subclientName = "automation-{}".format(self.id)
        self.clientName = "k8sauto-{}".format(self.id)
        self.destclientName = "k8sauto-{}-dest".format(self.id)
        self.pod_1 = self.testbed_name + '-pod-1'
        self.pod_2 = self.testbed_name + '-pod-2'
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
        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, sa_namespace)

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace_1)
        self.kubehelper.create_cv_namespace(self.namespace_2)

        # Creating namespace for restore if not exists
        self.kubehelper.create_cv_namespace(self.restore_namespace)

        # Creating PVC
        pvc_name = self.testbed_name + '-pvc'
        self.kubehelper.create_cv_pvc(pvc_name, self.namespace_1, storage_class=self.storageclass, storage="1Gi")
        self.kubehelper.create_cv_pvc(pvc_name, self.namespace_2, storage_class=self.storageclass, storage="11Gi")

        # Creating test pod
        self.kubehelper.create_cv_pod(self.pod_1, self.namespace_1, pvc_name=pvc_name)
        self.kubehelper.create_cv_pod(self.pod_2, self.namespace_2, pvc_name=pvc_name)
        time.sleep(30)
        KubernetesUtils.add_cluster(
            self,
            self.clientName,
            self.api_server_endpoint,
            self.serviceaccount,
            self.servicetoken,
            self.access_node
        )

    @TestStep()
    def many_files_backup(self):
        """
         FULL backup of 10000 small files of size 1kb each
        """

        self.kubehelper.create_random_cv_pod_data(
            self.pod_1,
            self.namespace_1,
            files_size=1024,
            no_of_files=10000,
            file_size_in_kb=True
        )
        self.content.append(self.namespace_1 + '/' + self.pod_1)
        KubernetesUtils.add_application_group(
            self,
            content=self.content,
            plan=self.plan,
            name=self.subclientName,
        )

        self.kubehelper.source_vm_object_creation(self)
        self.src_checksum = self.kubehelper.get_files_checksum(self.namespace_1)
        self.log.info("Step 1 -- FULL backup with 10000 small files as content")
        self.kubehelper.backup('FULL')

    @TestStep()
    def verify_app_level_oop_restore(self):
        """
        Out-Of-Place restore and comparison of hashsum of files in source and destination
        """
        self.kubehelper.restore_out_of_place(
            client_name=self.clientName,
            restore_namespace=self.restore_namespace,
            overwrite=True
        )
        self.dest_checksum = self.kubehelper.get_files_checksum(self.restore_namespace)
        self.kubehelper.verify_checksum_dictionary(self.src_checksum, self.dest_checksum)

    @TestStep()
    def huge_files_backup(self):
        """
        FULL backup of 10 huge files of size 1G each
        """
        self.kubehelper.create_random_cv_pod_data(
            self.pod_2,
            self.namespace_2,
            no_of_files=10,
            file_size=1,
            file_size_in_gb=True
        )
        self.content = []
        self.content.append(self.namespace_2 + '/' + self.pod_2)
        KubernetesUtils.add_application_group(
            self,
            content=self.content,
            plan=self.plan,
            name=self.subclientName+'-2',
        )
        self.subclientName = self.subclientName+'-2'
        self.kubehelper.source_vm_object_creation(self)
        self.src_checksum = self.kubehelper.get_files_checksum(self.namespace_2)
        self.log.info("Step 3 --  FULL backup with Huge files of size 1G as content")
        self.kubehelper.backup('FULL')

    def recreate_testbed(self):
        self.kubehelper.delete_cv_namespace(self.namespace_1)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)
        self.kubehelper.create_cv_namespace(self.restore_namespace)

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

        self.kubehelper.delete_cv_namespace(self.namespace_2)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)

        crb_name = self.testbed_name + '-crb'
        # Delete cluster role binding
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
            self.log.info("Step 1 -- FULL backup with 10000 small files as content")
            self.many_files_backup()

            self.log.info("Step 2 -- Out-Of-Place Restore with 10000 small files as content")
            self.verify_app_level_oop_restore()

            self.log.info("Deleting and Recreating restore namespace")
            self.kubehelper.delete_cv_namespace(self.namespace_1)
            self.kubehelper.delete_cv_namespace(self.restore_namespace)
            self.kubehelper.create_cv_namespace(self.restore_namespace)

            self.log.info("Step 3 -- FULL Backup with huge files of 1G as content")
            self.huge_files_backup()

            self.log.info("Step 4 -- Out-Of-Place Restore with huge files of 1G as content")
            self.verify_app_level_oop_restore()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 5 -- Delete testbed, delete client")
            self.delete_testbed()
