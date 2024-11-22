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

    verify_full_ns_backup()             --  Initiates a Full backup and verifies completion of job

    verify_namespace_level_oop_restore()   --  Initiates Out of Place restore job,verifies dependent application restore
                                               sequence and checks if all pods are running

    verify_namespace_level_oop_overwrite() --  Initiates Out of Place restore job with overwrite,verifies dependent
                                               application restore sequence and checks if all pods are running

    verify_namespace_level_ip_overwrite()  --  Initiates In Place restore job, verifies dependent application restore
                                               sequence and checks if all pods are running

    run()                               --  Run function of this test case
"""


import time
import threading
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
    Testcase to create Kubernetes Cluster, perform backups and namespace-level restores.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create Namespace, 2 deployments, 2 statefulsets for testbed
    5. Create a Kubernetes client with proxy provided
    6. Create application group for kubernetes with namespace as content
    7. Initiate Full Backup for App group created and verify job completed
    8. Initiate Out-of-place Namespace-level Restore and verify dependent application restore sequence and check if all
        pods are in running state
    9. Initiate Out-of-place Namespace-level Restore with Overwrite and verify dependent application restore sequence
        and check if all pods are in running state
    10. Initiate In-place Namespace-level Restore and verify dependent application restore sequence
        and check if all pods are in running state
    11. Cleanup testbed
    12. Cleanup clients created.
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Dependent application Restore sequence"
        self.utils = TestCaseUtils(self)
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
        self.stop_event = False
        self.restore_exception = []

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
        self.restore_exception = []
        self.stop_event = False

    @TestStep()
    def create_testbed(self):
        """Create cluster resources and clients for the testcase
        """
        self.log.info("Creating cluster resources...")

        # Create service account if doesn't exist
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, sa_namespace)

        # Create cluster role binding and serviceaccount token
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, sa_namespace, cluster_role)

        time.sleep(30)
        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, sa_namespace)

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)
        self.kubehelper.create_cv_namespace(self.restore_namespace)

        # Creating deployments
        pvc_deployment_name_1 = self.testbed_name + '-deploypvc1'
        self.kubehelper.create_cv_pvc(pvc_deployment_name_1, self.namespace, storage_class=self.storageclass)
        deployment_name_1 = self.testbed_name + '-deployment1'
        self.kubehelper.create_cv_deployment(deployment_name_1, self.namespace, pvc_deployment_name_1)

        pvc_deployment_name_2 = self.testbed_name + '-deploypvc2'
        self.kubehelper.create_cv_pvc(pvc_deployment_name_2, self.namespace, storage_class=self.storageclass)
        deployment_name_2 = self.testbed_name + '-deployment2'
        self.kubehelper.create_cv_deployment(deployment_name_2, self.namespace, pvc_deployment_name_2)

        # Creating Statefulsets
        sts_name_1 = self.testbed_name + '-sts1'
        self.kubehelper.create_cv_statefulset(sts_name_1, self.namespace)
        time.sleep(60)

        sts_name_2 = self.testbed_name + '-sts2'
        self.kubehelper.create_cv_statefulset(sts_name_2, self.namespace)
        time.sleep(60)

        self.content.append(self.namespace)

        # Create the cluster and application group
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

        orphan_crb = self.testbed_name + '-orphan-crb'
        self.kubehelper.delete_cv_clusterrolebinding(orphan_crb)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)

    @TestStep()
    def verify_full_ns_backup(self):
        """
        Verify FULL Backup of entire namespace as content
        """
        self.kubehelper.backup("FULL")
        self.log.info('FULL Backup job step with Namespace as content successfully completed')

    @TestStep()
    def restore_operation(self, **restore_kwargs):
        """
            Initiates Namespace Level Restore
        """
        try:
            self.kubehelper.namespace_level_restore(**restore_kwargs)
        except Exception as ex:
            self.restore_exception.append(ex)

    @TestStep()
    def verify_namespace_level_oop_restore(self):
        """
        Verify Namespace-level restore out-of-place
        """
        stop_event = threading.Event()
        restore_namespace_map = {
            self.namespace: self.restore_namespace
        }
        restore_kwargs = {
            'namespace_list': self.content,
            'restore_name_map': restore_namespace_map,
            'overwrite': False
        }
        verify_kwargs = {
            'namespace': self.restore_namespace,
            'stop_event': stop_event
        }

        try:
            # Start the restore operation in a separate thread
            restore_thread = threading.Thread(target=self.restore_operation, kwargs=restore_kwargs, daemon=True)
            restore_thread.start()

            # Start the verification in a separate thread
            verify_thread = threading.Thread(
                target=self.kubehelper.verify_node_selector,
                kwargs=verify_kwargs
            )
            verify_thread.start()
            restore_thread.join()

            if self.restore_exception and isinstance(self.restore_exception[0], Exception):
                raise self.restore_exception[0]

            stop_event.set()
            verify_thread.join()

        except Exception as e:
            raise e

        self.log.info("Dependent application Restore sequence for Out of Place restore was successfully completed")

    @TestStep()
    def verify_namespace_level_oop_overwrite(self):
        """
        Verify Namespace-level restore out-of-place with overwrite
        """
        stop_event = threading.Event()
        restore_namespace_map = {
            self.namespace: self.restore_namespace
        }
        restore_kwargs = {
            'namespace_list': self.content,
            'restore_name_map': restore_namespace_map,
        }
        verify_kwargs = {
            'namespace': self.restore_namespace,
            'stop_event': stop_event
        }

        try:
            # Start the restore operation in a separate thread
            restore_thread = threading.Thread(target=self.restore_operation, kwargs=restore_kwargs, daemon=True)
            restore_thread.start()

            # Start the verification in a separate thread
            verify_thread = threading.Thread(
                target=self.kubehelper.verify_node_selector,
                kwargs=verify_kwargs
            )
            verify_thread.start()
            restore_thread.join()

            if self.restore_exception and isinstance(self.restore_exception[0], Exception):
                raise self.restore_exception[0]

            stop_event.set()
            verify_thread.join()

        except Exception as e:
            raise e

        self.log.info("Dependent application Restore sequence for Out of Place restore with overwrite "
                      "was successfully completed")

    def verify_namespace_level_ip_overwrite(self):
        """
        Verify Namespace-level restore in-place with overwrite
        """
        stop_event = threading.Event()
        restore_kwargs = {
            'namespace_list': self.content,
            'in_place': True
        }
        verify_kwargs = {
            'namespace': self.namespace,
            'stop_event': stop_event
        }

        try:
            # Start the restore operation in a separate thread
            restore_thread = threading.Thread(target=self.restore_operation, kwargs=restore_kwargs, daemon=True)
            restore_thread.start()

            # Start the verification in a separate thread
            verify_thread = threading.Thread(
                target=self.kubehelper.verify_node_selector,
                kwargs=verify_kwargs
            )
            verify_thread.start()
            restore_thread.join()

            if self.restore_exception and isinstance(self.restore_exception[0], Exception):
                raise self.restore_exception[0]
            stop_event.set()
            verify_thread.join()

        except Exception as e:
            raise e

        self.log.info(
            "Dependent application Restore sequence for In Place restore with overwrite was successfully completed")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Step 1 - Take FULL Backup of App Group
            self.log.info('Step 1 -- Run FULL Backup job with Namespace as content')
            self.verify_full_ns_backup()

            # Step 2 - Perform OOP Restore of Namespace
            self.log.info('Step 2 -- Run Namespace-level restore out-of-place')
            self.verify_namespace_level_oop_restore()

            # Step 3 - Perform OOP Restore of Namespace with overwrite
            self.log.info('Step 3 -- Run Namespace-level restore out-of-place with overwrite')
            self.verify_namespace_level_oop_overwrite()

            # Step 4 - Perform IP Restore of Namespace with overwrite
            self.log.info('Step 4 -- Run Namespace-level restore out-of-place with overwrite')
            self.verify_namespace_level_ip_overwrite()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 5 -- Delete testbed, delete client ")
            self.delete_testbed()
