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
    4. Create Namespace, Pod, PVC, deployment, orphan secrets, configmaps, serviceaccounts,etc for testbed
    5. Create a Kubernetes client with proxy provided
    6. Create application group for kubernetes with namespace as content
    7. Add content in PVC for full backup.
    8. Initiate Full Backup for App group created and verify job completed
    9. Add content and move content, create more orphan entities for Incremental backup.
    10. Initiate Incremental Backup for App group created and verify job completed
    11. Initiate Out-of-place Namespace-level Restore and verify job completed
    12. Validate restored files checksum and restored resources
    13. Initiate in-place namespace-level restore and verify job completed
    14. Validate restored files checksum and restored resources
    15. Cleanup testbed
    16. Cleanup clients created.
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Namespace-level Backup and Restore"
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
        self.resources_before_backup = None
        self.resources_after_restore = None

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

    def create_orphan_resources(self):
        """Create orphan resources in namespace
        """
        timestamp = str(int(time.time()))
        self.log.info(f'Creating some orphan resources in namespace [{self.namespace}]')
        orphan_secret = self.testbed_name + '-orphan-secret-' + timestamp
        orphan_cm = self.testbed_name + '-orphan-cm-' + timestamp
        orphan_svc = self.testbed_name + '-orphan-svc-' + timestamp
        orphan_sa = self.testbed_name + '-orphan-sa-' + timestamp
        self.kubehelper.create_cv_secret(orphan_secret, self.namespace)
        self.kubehelper.create_cv_configmap(orphan_cm, self.namespace)
        self.kubehelper.create_cv_svc(orphan_svc, self.namespace, selector={self.namespace: self.namespace})
        self.kubehelper.create_cv_serviceaccount(orphan_sa, self.namespace)

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
        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, sa_namespace)

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)

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

        # Creating test statefulset
        sts_name = self.testbed_name + '-sts'
        self.kubehelper.create_cv_statefulset(sts_name, self.namespace)
        time.sleep(60)

        # Creating test deployment
        pvc_deployment_name = self.testbed_name + '-deploypvc'
        self.kubehelper.create_cv_pvc(pvc_deployment_name, self.namespace, storage_class=self.storageclass)
        deployment_name = self.testbed_name + '-deployment'
        self.kubehelper.create_cv_deployment(deployment_name, self.namespace, pvc_deployment_name)

        # Create orphan resources in the namespace
        self.create_orphan_resources()
        orphan_sa_2 = self.testbed_name + '-orphan-sa2'
        orphan_crb = self.testbed_name + '-orphan-crb'
        self.kubehelper.create_cv_serviceaccount(orphan_sa_2, self.namespace)
        self.kubehelper.create_cv_clusterrolebinding(orphan_crb, orphan_sa_2, self.namespace, 'view')

        self.content.append(self.namespace)

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
        """Verify FULL Backup of entire namespace as content
        """
        self.log.info('Step 1 -- Run FULL Backup job with Namespace as content')
        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.kubehelper.backup("FULL")
        self.log.info('FULL Backup job step with Namespace as content successfully completed')

    @TestStep()
    def verify_namespace_level_oop_restore(self):
        """Verify Namespace-level restore out-of-place
        """
        self.log.info('Step 2 -- Run Namespace-level restore out-of-place')
        restore_namespace_map = {
            self.namespace: self.restore_namespace
        }
        self.kubehelper.namespace_level_restore(
            namespace_list=self.content,
            restore_name_map=restore_namespace_map,
            overwrite=False
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.log.info('Namespace-level restore out-of-place step successfully completed')

    @TestStep()
    def verify_inc_ns_backup(self):
        """Verify INC Backup of entire namespace as content
        """
        self.log.info('Step 3 -- Run INC Backup job with Namespace as content')
        self.create_orphan_resources()

        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.kubehelper.backup("INCREMENTAL")
        self.log.info('INCREMENTAL Backup job step with Namespace as content successfully completed')

    @TestStep()
    def verify_namespace_level_oop_overwrite(self):
        """Verify Namespace-level restore out-of-place with overwrite
        """
        self.log.info('Step 4 -- Run Namespace-level restore out-of-place with overwrite')
        restore_namespace_map = {
            self.namespace: self.restore_namespace
        }
        self.kubehelper.namespace_level_restore(
            namespace_list=self.content,
            restore_name_map=restore_namespace_map
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.log.info('Namespace-level restore out-of-place with overwrite step successfully completed')

    @TestStep()
    def verify_namespace_level_ip_overwrite(self):
        """Verify Namespace-level restore in-place with overwrite
        """
        self.log.info('Step 5 -- Run Namespace-level restore out-of-place with overwrite')
        self.kubehelper.namespace_level_restore(
            namespace_list=self.content,
            in_place=True
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.log.info('Namespace-level restore in-place with overwrite step successfully completed')

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Step 1 - Take FULL Backup of App Group
            self.verify_full_ns_backup()

            # Step 2 - Perform OOP Restore of Namespace
            self.verify_namespace_level_oop_restore()

            # Step 3 - Take INC Backup after creating more orphan resources
            self.verify_inc_ns_backup()

            # Step 4 - Perform OOP Restore of Namespace with overwrite
            self.verify_namespace_level_oop_overwrite()

            # Step 5 - Perform IP Restore of Namespace with overwrite
            self.verify_namespace_level_ip_overwrite()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 6 -- Delete testbed, delete client ")
            self.delete_testbed()
