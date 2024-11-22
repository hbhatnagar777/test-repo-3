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
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes import KubernetesUtils
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform backups and non-namespace-level restores.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create Namespace, Pod, PVC, deployment, orphan secrets, configmaps, serviceaccounts,etc for testbed
    5. Create a Kubernetes client with proxy provided
    6. Create application group for kubernetes with namespace as content
    7. Add content in PVC for full backup.
    8. Initiate Full Backup for App group created and verify job completed
    9. Perform full application out of place restore
    10. Create orphan entities and initiate Incremental Backup for App group created and verify job completed
    11. Initiate manifest restore for namespace-app YAMLs
    12. Perform FS Destination restore and validate files
    13. Cleanup testbed
    14. Cleanup clients created.
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Non-namespace level restores with namespace as application group content"
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
        self.app_list = []
        self.folders_to_create = []
        self.proxy_obj = None
        self.resources_before_backup = None
        self.resources_after_restore = None
        self.restore_destination = None
        self.kubeconfig_on_proxy = None
        self.pod_name = None
        self.pvc_name = None

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
        self.restore_destination = '/tmp/' + self.testbed_name
        self.kubeconfig_on_proxy = '/tmp/kubeconfig-' + self.testbed_name + '.yaml'

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

        self.pvc_name = self.testbed_name + '-podpvc'
        self.kubehelper.create_cv_pvc(self.pvc_name, self.namespace, storage_class=self.storageclass)
        self.pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(
            self.pod_name, self.namespace, secret=secret_name, configmap=config_name, pvc_name=self.pvc_name
        )
        self.app_list.append(self.pod_name)
        time.sleep(30)

        # Creating test statefulset
        sts_name = self.testbed_name + '-sts'
        self.kubehelper.create_cv_statefulset(sts_name, self.namespace)
        self.app_list.append(sts_name)
        time.sleep(60)

        # Creating test deployment
        pvc_deployment_name = self.testbed_name + '-deploypvc'
        self.kubehelper.create_cv_pvc(pvc_deployment_name, self.namespace, storage_class=self.storageclass)
        deployment_name = self.testbed_name + '-deployment'
        self.kubehelper.create_cv_deployment(deployment_name, self.namespace, pvc_deployment_name)
        self.app_list.append(deployment_name)
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

        self.proxy_obj.remove_directory(self.restore_destination)
        self.log.info(f"Removed directory [{self.restore_destination}] from access node [{self.access_node}]")

        self.proxy_obj.delete_file(self.kubeconfig_on_proxy)
        self.log.info(f"Removed temporary kubeconfig file on access node from {self.kubeconfig_on_proxy}")

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
    def verify_full_app_oop_restore(self):
        """Verify Full application restore out-of-place
        """
        self.log.info('Step 2 -- Run Full application restore out-of-place')
        self.kubehelper.restore_out_of_place(
            client_name=self.clientName,
            storage_class=self.storageclass,
            restore_namespace=self.restore_namespace,
            application_list=self.app_list
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.log.info('Full application restore out-of-place step successfully completed')

    @TestStep()
    def verify_inc_ns_backup(self):
        """Verify INC Backup of entire namespace as content
        """
        self.log.info('Step 3 -- Run INC Backup job with Namespace as content')
        self.create_orphan_resources()

        folder_name = "folder-" + str(int(time.time()))
        self.folders_to_create.append(folder_name)
        self.kubehelper.create_random_cv_pod_data(
            pod_name=self.pod_name, namespace=self.namespace, foldername=folder_name
        )

        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.kubehelper.backup("INCREMENTAL")
        self.log.info('INCREMENTAL Backup job step with Namespace as content successfully completed')

    @TestStep()
    def verify_manifest_restore(self):
        """Verify manifest restore of namespace-app
        """
        self.log.info('Step 4 -- Run Manifest restore to access node')

        self.log.info("Copying kubeconfig from local to access node")
        local_machine = Machine()

        content = local_machine.read_file(self.k8s_config)
        for line in content.split('\n'):
            self.proxy_obj.append_to_file(self.kubeconfig_on_proxy, line)

        self.log.info(f"Kubeconfig copied at {self.kubeconfig_on_proxy}")

        self.kubehelper.manifest_restore(
            application_name=self.namespace,
            access_node=self.access_node,
            destination_path=self.restore_destination,
            unconditional_overwrite=True
        )
        self.log.info("Manifest restore of multiple file steps complete")

        self.log.info("Validating manifest restores using kubectl diff")
        self.kubehelper.validate_restored_manifest(
            self.restore_destination, self.access_node, self.kubeconfig_on_proxy
        )
        self.proxy_obj.remove_directory(self.restore_destination)
        self.log.info(f"Removed directory [{self.restore_destination}] from access node [{self.access_node}]")
        self.log.info("Manifest restore validation successful")

    @TestStep()
    def verify_fs_dest_restore(self):
        """FS Destination Restore of folder
        """

        self.log.info("Step 5 -- File system destination restore of folder")

        self.kubehelper.fs_dest_restore(
            application_name=self.pod_name,
            restore_list=self.folders_to_create,
            source_namespace=self.namespace,
            pvc_name=self.pvc_name,
            access_node=self.access_node,
            destination_path=self.restore_destination,
            unconditional_overwrite=True
        )
        self.log.info("File system destination restore of full pvc content step complete")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Step 1 - Take FULL Backup of App Group
            self.verify_full_ns_backup()

            # Step 2 - Perform OOP Restore of Namespace
            self.verify_full_app_oop_restore()

            # Step 3 - Take INC Backup after creating more orphan resources
            self.verify_inc_ns_backup()

            # Step 4 - Perform OOP Restore of Namespace with overwrite
            self.verify_manifest_restore()

            # Step 5 - Perform IP Restore of Namespace with overwrite
            self.verify_fs_dest_restore()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 6 -- Delete testbed, delete client ")
            self.delete_testbed()
