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

    create_inc_applications()           --  Create applications for incremental backup

    create_orphan_resources()           --  Create orphan resources on namespace

    verify_app_level_oop_overwrite()    --  Verify full application out of place restore

    verify_full_ns_backup()             --  Verify FULL Backup of app group

    verify_inc_ns_backup()              --  Verify INC backup of app group after creating StatefulSet

    verify_namespace_level_oop_restore()--  Verify Namespacr level restore out of place

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
    This testcase performs validation on Kubernetes forms using automation framework.
    Kubernetes update center forms have binary CVK8sInfo.dll (Windows) and libCVK8sInfo.so (Linux)
    This testcase does the following --
    1. Create new namespace on a Kubernetes cluster and create the following resources :
        - Pod with PVC
        - Deployment with PVC
        - Deployment without PVC
        - Orphan resources (ConfigMap, Secret, PVC)
    2. Create a new Kubernetes client on command center using Service Account and Token authentication with
        'cluster-admin' Cluster Role
    3. Create new application group and add the namespace as content.
    4. Initiate FULL Backup of Application Group.
    5. Initiate Namespace-level Out Of Place restore.
    6. Create incremental data in Pods in the existing namespace.
    7. Initiate an INCREMENTAL Backup of the application group.
    8. Initiate FULL APPLICATION OUT-OF-PLACE Restore of the StatefulSet backed up in the INCREMENTAL Job.
    9. Delete Application Group.
    10. Delete Kubernetes client.
    11. Cleanup testbed created on the Kubernetes cluster.
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes update form friendly testing using automation framework"
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
        self.controller = None
        self.tcinputs = {}
        self.k8s_config = None
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
        orphan_pvc = self.testbed_name + '-orphan-pvc-' + timestamp
        self.kubehelper.create_cv_secret(orphan_secret, self.namespace)
        self.kubehelper.create_cv_configmap(orphan_cm, self.namespace)
        self.kubehelper.create_cv_svc(orphan_svc, self.namespace, selector={self.namespace: self.namespace})
        self.kubehelper.create_cv_serviceaccount(orphan_sa, self.namespace)
        self.kubehelper.create_cv_pvc(orphan_pvc, self.namespace, storage_class=self.storageclass)

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

        pvc_pod_name = self.testbed_name + '-pod-pvc'
        self.kubehelper.create_cv_pvc(pvc_pod_name, self.namespace, storage_class=self.storageclass)
        pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(
            pod_name, self.namespace, secret=secret_name, configmap=config_name, pvc_name=pvc_pod_name
        )

        # Creating resources for deployment
        self.kubehelper.create_cv_serviceaccount(self.testbed_name + '-mounted-sa', self.namespace)
        self.kubehelper.create_cv_secret(self.testbed_name + '-env-secret', self.namespace)
        self.kubehelper.create_cv_configmap(self.testbed_name + '-env-cm', self.namespace)
        self.kubehelper.create_cv_secret(self.testbed_name + '-proj-secret', self.namespace)
        self.kubehelper.create_cv_configmap(self.testbed_name + '-proj-cm', self.namespace)

        # Creating stateless deployment
        deployment_name = self.testbed_name + '-deployment-stateless'
        self.kubehelper.create_cv_deployment(deployment_name, self.namespace)

        # Creating test deployment
        pvc_deployment_name = self.testbed_name + '-deploy-pvc'
        self.kubehelper.create_cv_pvc(pvc_deployment_name, self.namespace, storage_class=self.storageclass)
        deployment_name = self.testbed_name + '-deployment'
        self.kubehelper.create_cv_deployment(
            name=deployment_name,
            namespace=self.namespace,
            pvcname=pvc_deployment_name,
            env_secret=self.testbed_name + '-env-secret',
            env_configmap=self.testbed_name + '-env-cm',
            projected_secret=self.testbed_name + '-proj-secret',
            projected_configmap=self.testbed_name + '-proj-cm',
            init_containers=True,
            resources=True,
            replicas=1,
            service_account=self.testbed_name + '-mounted-sa'
        )

        # Creating test stateful set
        sts_name = self.testbed_name + '-sts'
        self.kubehelper.create_cv_statefulset(
            name=sts_name,
            namespace=self.namespace
        )

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

    def create_pod_data(self):
        """Create data in Pods in the namespace
        """
        self.log.info(f"Creating data in Pods in namespace [{self.namespace}]")
        for pod in self.kubehelper.get_namespace_pods(self.namespace):
            if 'stateless' not in pod:
                self.kubehelper.create_random_cv_pod_data(
                    pod_name=pod,
                    namespace=self.namespace,
                    no_of_files=10,
                    hlink=True,
                    slink=True
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

        KubernetesUtils.delete_application_group(self, self.app_grp_name)
        KubernetesUtils.delete_cluster(self, self.clientName)

    @TestStep()
    def verify_full_ns_backup(self):
        """Verify FULL Backup of entire namespace as content
        """
        self.log.info('Step 1 -- Run FULL Backup job with Namespace as content')
        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.create_pod_data()
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
        self.kubehelper.k8s_verify_restore_files(
            source_namespace=self.namespace, restore_namespace=self.restore_namespace
        )
        self.log.info('Namespace-level restore out-of-place step successfully completed')

    @TestStep()
    def verify_inc_ns_backup(self):
        """Verify INC Backup of entire namespace as content
        """
        self.log.info('Step 3 -- Run INC Backup job with Namespace as content')
        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.create_pod_data()
        self.kubehelper.backup("INCREMENTAL")
        self.log.info('INCREMENTAL Backup job step with Namespace as content successfully completed')

    @TestStep()
    def verify_app_level_oop_overwrite(self):
        """Verify Full-Application restore out-of-place with overwrite
        """
        self.log.info('Step 4 -- Run Full-Application restore out-of-place with overwrite')
        self.kubehelper.restore_out_of_place(
            client_name=self.clientName,
            restore_namespace=self.restore_namespace,
            application_list=[self.testbed_name + '-sts'],
            overwrite=True
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        source_checksum = self.kubehelper.get_files_checksum(self.namespace)
        destination_checksum = self.kubehelper.get_files_checksum(self.restore_namespace)

        # Keep only StatefulSet pods
        source_checksum = {pod: checksum for pod, checksum in source_checksum.items() if 'sts' in pod}
        destination_checksum = {pod: checksum for pod, checksum in destination_checksum.items() if 'sts' in pod}
        self.kubehelper.verify_checksum_dictionary(source_checksum, destination_checksum)
        self.log.info('Namespace-level restore out-of-place with overwrite step successfully completed')

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
            self.verify_app_level_oop_overwrite()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 6 -- Delete testbed, delete client ")
            self.delete_testbed()
