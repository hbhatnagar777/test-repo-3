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

    verify_backup()                     --  Verify backup job

    verify_restore_step()               --  Verify restore job

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
    Testcase to create Kubernetes Cluster, perform backup and restore of shared PVC applications.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create Namespace, Pod, PVC, deployment  for testbed
    5. Create a Kubernetes client with proxy provided
    6. Create application group for kubernetes
    7. Initiate Full Backup for App group with shared PVC and verify job completed
    8. Initiate Out-of-place Full Application Restore with overwrite false and verify job completed
    9. Initiate Out-of-place Namespace level restore with overwrite true
    10. Initiate In-place Full Application Restore and verify job completed
    11. Cleanup testbed
    12. Cleanup clients created.
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Backup and restore of Applications with shared PVC"
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
        self.restore_namespace_ns = None
        self.app_grp_name = None
        self.serviceaccount = None
        self.authentication = "Service account"
        self.subclientName = None
        self.clientName = None
        self.destclientName = None
        self.destinationClient = None
        self.controller = None
        self.controller_machine = None
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
        self.accessmode = None
        self.deployment_name_1 = None
        self.deployment_name_2 = None
        self.pvc_name = None
        self.resources_before_backup = None
        self.resources_after_restore = None

    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.namespace = self.testbed_name
        self.restore_namespace = self.namespace + "-rst"
        self.restore_namespace_ns = self.namespace + "-ns-rst"
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
        self.controller_machine = Machine(self.controller)
        self.accessmode = self.tcinputs.get('AccessMode', 'ReadWriteOnce')
        self.pvc_name = self.testbed_name + '-pvc'
        self.deployment_name_1 = self.testbed_name + '-dep-1'
        self.deployment_name_2 = self.testbed_name + '-dep-2'

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
        self.content.append(self.namespace)

        # Create Service
        svc_name = self.testbed_name + '-svc'
        self.kubehelper.create_cv_svc(svc_name, self.namespace)

        # Creating test pod
        secret_name = self.testbed_name + '-secret'
        config_name = self.testbed_name + '-cm'
        self.kubehelper.create_cv_secret(secret_name, self.namespace)
        self.kubehelper.create_cv_configmap(config_name, self.namespace)

        self.kubehelper.create_cv_pvc(
            name=self.pvc_name, namespace=self.namespace, accessmode=self.accessmode, storage_class=self.storageclass
        )
        self.kubehelper.create_cv_deployment(
            self.deployment_name_1, self.namespace, env_secret=secret_name, env_configmap=config_name,
            init_containers=True, pvcname=self.pvc_name, replicas=3
        )
        time.sleep(30)
        self.kubehelper.create_cv_deployment(
            self.deployment_name_2, self.namespace, env_secret=secret_name, env_configmap=config_name,
            init_containers=True, pvcname=self.pvc_name, replicas=3
        )
        time.sleep(30)

        pod_name = self.kubehelper.get_namespace_pods(self.namespace)[0]
        self.kubehelper.create_random_cv_pod_data(
            pod_name=pod_name, namespace=self.namespace, foldername=self.id
        )

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
        self.kubehelper.delete_cv_namespace(self.restore_namespace_ns)

        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(
            sa_name=self.serviceaccount, sa_namespace=sa_namespace
        )

        KubernetesUtils.delete_cluster(self, self.clientName)

    @TestStep()
    def verify_backup(self):
        """Validate FULL Backup of applications with shared PVC
        """
        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.kubehelper.backup('FULL')
        self.log.info("Backup of applications with shared PVC completed.")

    @TestStep()
    def verify_restore_step(self, inplace=False, overwrite=False):
        """Verify Full Application Restore Step
        """
        self.log.info(f"Verify Full Application {'In-place' if inplace else 'OOP'} restore")

        self.kubehelper.run_restore_validate(
            self.clientName,
            self.storageclass,
            inplace=inplace,
            validate=True,
            overwrite=overwrite
        )
        restore_namespace = self.namespace if inplace else self.restore_namespace
        self.resources_after_restore = self.kubehelper.get_all_resources(restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.log.info(f"{'In-Place' if inplace else 'Out-of-place'} Full Application Restore step complete")

    @TestStep()
    def verify_ns_restore(self):
        """Verify Namespace level restore out-of-place
        """
        self.kubehelper.namespace_level_restore(
            self.clientName,
            self.access_node,
            namespace_list=[self.namespace],
            restore_name_map={self.namespace: self.restore_namespace_ns},
            overwrite=False
        )
        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace_ns)
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace_ns)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.log.info("Namespace level restore step complete")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Run Full Job and incremental job before verifying restore
            self.verify_backup()

            # Verify out-of-place full app restore
            self.verify_restore_step()

            # Currently restore of apps with shared resources is not supported with overwrite true
            # Validate In-place restore
            # self.verify_restore_step(inplace=True, overwrite=True)

            # Validate Out of place Namespace level restore
            self.verify_ns_restore()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step -- Delete testbed, delete client ")
            self.delete_testbed()
