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
from Kubernetes.constants import KubernetesAdditionalSettings, LogLineRepo
from Kubernetes.exceptions import KubernetesException
from Reports.utils import TestCaseUtils
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes import KubernetesUtils
from Web.Common.page_object import TestStep, InitStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform backups and namespace-level restores.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create Namespace, Pod, deployment, sts with mounted PVC for testbed
    5. Create a Kubernetes client with proxy provided
    6. Create application group for kubernetes with namespace as content
    7. Add additional setting to specify worker namespace
    7. Add content in PVC for full backup.
    8. Initiate Full Backup for App group created and verify job completed
    9. Verify cleanup in worker namespace
    11. Initiate Out-of-place Namespace-level Restore and verify job completed
    12. Validate restored files checksum and restored resources
    15. Cleanup testbed
    16. Cleanup clients created.
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.job_id = None
        self.name = "Kubernetes: Validate backups and restores when worker pod is created in external namespace"
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
        self.worker_namespace = None
        self.__cluster_created = False

    @InitStep(msg="Load kubeconfig and initialize testcase variables")
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
        self.worker_namespace = self.testbed_name + "-worker-namespace"
        self.controller_id = int(self.controller.client_id)
        self.proxy_obj = Machine(self.controller)

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

    @InitStep(msg="Checking if StorageClass has associated VolumeSnapshotClass")
    def check_if_sc_has_associated_snap_class(self):
        """Check if volume snapshot class is present for storageclass"""

        if not self.kubehelper.check_for_sc_snapshot_class(storage_class_name=self.storageclass):
            raise KubernetesException(
                'APIClientOperations',
                '101',
                f'Associated VolumeSnapshotClass not found for {self.storageclass}'
            )
        else:
            self.log.info("Associated volumesnapshotclass found. Continuing with the test case")

    @InitStep(msg="Create testbed resources on cluster")
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

        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, sa_namespace)

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)

        pvc_pod_name = self.testbed_name + '-podpvc'
        self.kubehelper.create_cv_pvc(pvc_pod_name, self.namespace, storage_class=self.storageclass)
        pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(
            pod_name, self.namespace, pvc_name=pvc_pod_name
        )

        # Creating test statefulset
        sts_name = self.testbed_name + '-sts'
        self.kubehelper.create_cv_statefulset(sts_name, self.namespace)

        # Creating test deployment
        pvc_deployment_name = self.testbed_name + '-deploypvc'
        self.kubehelper.create_cv_pvc(pvc_deployment_name, self.namespace, storage_class=self.storageclass)
        deployment_name = self.testbed_name + '-deployment'
        self.kubehelper.create_cv_deployment(deployment_name, self.namespace, pvc_deployment_name)

        # Create orphan resources in the namespace
        self.content.append(self.namespace)

        KubernetesUtils.add_cluster(
            self,
            self.clientName,
            self.api_server_endpoint,
            self.serviceaccount,
            self.servicetoken,
            self.access_node
        )
        self.__cluster_created = True
        KubernetesUtils.add_application_group(
            self,
            content=self.content,
            plan=self.plan,
            name=self.subclientName,
        )
        self.proxy_obj.set_logging_debug_level(service_name='vsbkp', level='2')

    def setup(self):
        """
        Setup the Testcase
        """
        self.init_inputs()
        self.check_if_sc_has_associated_snap_class()
        self.create_testbed()

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

        self.remove_additional_setting()

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
    def verify_namespace_level_oop_overwrite(self):
        """Verify Namespace-level restore out-of-place with overwrite
        """
        self.log.info('Step 4 -- Run Namespace-level restore out-of-place with overwrite')
        self.kubehelper.run_restore_validate(
            self.clientName,
            self.storageclass,
            source_namespace=self.namespace,
            restore_namespace=self.restore_namespace
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.log.info('Namespace-level restore out-of-place with overwrite step successfully completed')

    def remove_additional_setting(self):

        self.log.info(f"removing additional setting {KubernetesAdditionalSettings.WORKER_NAMESPACE.value}:"
                      f" {self.worker_namespace}")
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.WORKER_NAMESPACE.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.WORKER_NAMESPACE.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.WORKER_NAMESPACE.value}]"
            )

    @TestStep()
    def add_additional_setting(self):
        """Add additional setting sK8sWorkerNamespace"""

        # Remove additional setting to disallow fallback to live volume backup

        self.log.info(f"Checking for additional setting {KubernetesAdditionalSettings.LIVE_VOLUME_FALLBACK.value}")
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.LIVE_VOLUME_FALLBACK.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.LIVE_VOLUME_FALLBACK.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.LIVE_VOLUME_FALLBACK.value}]"
            )

        self.log.info(
            f"Adding additional setting {KubernetesAdditionalSettings.WORKER_NAMESPACE.value}:"
            f" {self.worker_namespace}"
        )

        # Check sK8sWorkerCpuMax
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.WORKER_NAMESPACE.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.WORKER_NAMESPACE.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.WORKER_NAMESPACE.value}]"
            )

        self.log.info(f"Adding additional setting [{KubernetesAdditionalSettings.WORKER_NAMESPACE.value}]"
                      f" with value {self.worker_namespace}")

        self.controller.add_additional_setting(
            category=KubernetesAdditionalSettings.CATEGORY.value,
            key_name=KubernetesAdditionalSettings.WORKER_NAMESPACE.value,
            data_type=KubernetesAdditionalSettings.STRING.value,
            value=self.worker_namespace
        )

        self.log.info("Creating worker namespace")

        self.kubehelper.create_cv_namespace(self.worker_namespace)

    @TestStep()
    def add_data_verify_full_ns_backup_check_worker_namespace(self):
        """Run full backup job, and check whether the worker pod was created in the correct namespace"""

        self.log.info("Add data to all pods in the test namespace")
        for pod in self.kubehelper.get_namespace_pods(self.namespace):
            self.kubehelper.create_random_cv_pod_data(pod, self.namespace)

        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        backup_job = self.kubehelper.backup("FULL")
        self.job_id = backup_job.job_id

        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=self.job_id,
            log_file_name="vsbkp.log",
            pattern=LogLineRepo.WORKER_POD_YAML.value,
            expected_keyword=f'"namespace":"{self.worker_namespace}"'
        )
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=self.job_id,
            log_file_name="vsbkp.log",
            pattern=LogLineRepo.SNAPSHOT_YAML.value,
            expected_keyword=f'"namespace":"{self.worker_namespace}"'
        )
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=self.job_id,
            log_file_name="vsbkp.log",
            pattern=LogLineRepo.PVC_YAML.value,
            expected_keyword=f'"namespace":"{self.worker_namespace}"'
        )

    @TestStep()
    def validate_worker_cleanup(self, namespace):
        """"Validate CV Resource cleanup in the worker namespace"""

        self.kubehelper.validate_cv_resource_cleanup(namespace=namespace, backup_jobid=self.job_id)

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Step 1 - Set additional setting to specify worker namespace
            self.add_additional_setting()

            # Step 2 - Perform backup, verify worker pod creation in specified namespace
            self.add_data_verify_full_ns_backup_check_worker_namespace()

            # Step 3 - Validate Worker namespace cleanup
            self.validate_worker_cleanup(namespace=self.worker_namespace)

            # Step 4 - Perform OOP restore of Namespace w/o overwrite, Verify restored resources
            self.verify_namespace_level_oop_overwrite()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            if self.__cluster_created:
                self.log.info("Step 6 -- Delete testbed, delete client ")
                self.delete_testbed()
