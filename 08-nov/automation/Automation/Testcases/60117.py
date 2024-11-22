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

    snapshot_based_backup()             --  Verify Full Snapshot Based Backup job

    live_volume_backup()                --  Verify Full Live Volume Backup

    verify_app_level_oop_restore        --  Verify Application level Out-Of-Place restore

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
from Kubernetes.constants import KubernetesAdditionalSettings, LogLineRepo


automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform backups and namespace-level restores.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create 2 PVCs with ReadWriteOnce and ReadWriteMany accessmodes for testbed
    5. Create temporary pods to populate the PVC with random data
    6. Create a Kubernetes client with proxy provided
    7. Create application group for kubernetes with volumes as content
    8. Initiate Full Backup for App group created and verify job completed
    9. Initiate Out-of-Place restore and verify job completed
    10. Add bK8sSnapFallBackLiveBkp regkey with value 1 and also create ResouceQuota to force live volume fallback
    11. Initiate Full Backup for App group created and verify job completed
    12. Initiate Out-of-Place restore and verify job completed
    13. Cleanup testbed
    14. Cleanup clients created.
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes: Backup and Restore with Volumes as app group content"
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
        self.pvc_1 = None
        self.pvc_2 = None
        self.pod_1 = None
        self.pod_2 = None
        self.rwo = None
        self.rwm = None
        self.src_checksum = None
        self.dest_checksum = None
        self.universal_label = None

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
        self.pvc_1 = self.testbed_name + '-pvc-1'
        self.pvc_2 = self.testbed_name + '-pvc-2'
        self.pod_1 = self.testbed_name + '-pod-1'
        self.pod_2 = self.testbed_name + '-pod-2'
        self.rwo = self.tcinputs.get("ReadWriteOnce", "rook-ceph-block")
        self.rwm = self.tcinputs.get("ReadWriteMany", "rook-cephfs")
        self.universal_label = {"testcase": self.testbed_name}

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
        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, sa_namespace)

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)

        # Creating namespace for restore if not exists
        self.kubehelper.create_cv_namespace(self.restore_namespace)

        # Creating PVC
        self.kubehelper.create_cv_pvc(self.pvc_1, self.namespace, storage_class=self.rwo,
                                      labels=self.universal_label)
        self.kubehelper.create_cv_pvc(self.pvc_2, self.namespace, storage_class=self.rwm,
                                      accessmode="ReadWriteMany", labels=self.universal_label)

        # Creating temporary pods to populate data in PVC
        self.kubehelper.create_cv_pod(self.pod_1, self.namespace, pvc_name=self.pvc_1)
        self.kubehelper.create_cv_pod(self.pod_2, self.namespace, pvc_name=self.pvc_2)

        # Create random data in pod and get the checksum
        self.kubehelper.create_random_cv_pod_data(self.pod_1, self.namespace)
        self.kubehelper.create_random_cv_pod_data(self.pod_2, self.namespace)
        self.src_checksum = self.kubehelper.get_files_checksum(self.namespace)

        # Delete the temporary pods
        self.kubehelper.delete_cv_pod(self.pod_1, self.namespace)
        self.kubehelper.delete_cv_pod(self.pod_2, self.namespace)

        KubernetesUtils.add_cluster(
            self,
            self.clientName,
            self.api_server_endpoint,
            self.serviceaccount,
            self.servicetoken,
            self.access_node
        )
        self.log.info(f"Namespace selector: {self.namespace}")
        namespaces = f'-n {self.namespace}'

        # Select Volumes as Application Group content
        content = [f"Selector:Volumes:testcase={self.testbed_name} {namespaces}"]
        KubernetesUtils.add_application_group(
            self,
            content=content,
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
    def snapshot_based_backup(self):
        """
        Create app group using volume label selectors and perform backup
        """
        self.log.info('Removing regkey bK8sSnapFallBackLiveBkp if present')

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
        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.log.info("Running FULL Backup job...")
        self.kubehelper.backup('FULL')
        self.log.info('FULL backup job step completed')

    def live_volume_backup(self):
        """
        Create app group using volume label selectors and perform backup
        """
        self.log.info('Adding regkey')
        self.log.info(f'bK8sSnapFallBackLiveBkp: 1')

        # Check sK8sWorkerCpuMax
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

        self.log.info(f"Adding additional setting [{KubernetesAdditionalSettings.LIVE_VOLUME_FALLBACK.value}]"
                      f" with value 1")

        self.commcell.clients.get(self.access_node).add_additional_setting(
            category=KubernetesAdditionalSettings.CATEGORY.value,
            key_name=KubernetesAdditionalSettings.LIVE_VOLUME_FALLBACK.value,
            data_type=KubernetesAdditionalSettings.BOOLEAN.value,
            value="true"
        )
        self.log.info("Waiting for 1 minute")
        time.sleep(60)

        # Create Resource quota in namespace to force live volume fallback
        pvc_rq = self.testbed_name + '-pvc-rq'
        self.kubehelper.create_cv_resource_quota(
            pvc_rq,
            namespace=self.namespace,
            misc_resource_count={'persistentvolumeclaims': '2'}
        )

        # Create Resource quota in namespace to force live volume fallback
        snap_rq = self.testbed_name + '-snap-rq'
        self.kubehelper.create_cv_resource_quota(
            snap_rq,
            namespace=self.namespace,
            misc_resource_count={'count/volumesnapshots.snapshot.storage.k8s.io': '0'}
        )
        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.resources_before_backup['Pod'] = []
        self.resources_before_backup['ResourceQuota'] = []
        self.log.info("Running FULL Backup job...")
        backup_job = self.kubehelper.backup('FULL')
        self.log.info('FULL backup job step completed. Proceeding to check the logs')

        # Verifying Log file for live volume fallback
        pattern = LogLineRepo.SNAP_FAIL_LIVE_VOLUME_FALLBACK.value
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=backup_job.job_id,
            log_file_name="vsbkp.log",
            pattern=pattern,
            expected_keyword=None
        )

        # Remove regkey from AN
        self.log.info('Removing regkey bK8sSnapFallBackLiveBkp')

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

    @TestStep()
    def verify_app_level_oop_restore(self):
        """
        Verify App level OOP restore
        """
        self.kubehelper.restore_out_of_place(
            client_name=self.clientName,
            restore_namespace=self.restore_namespace,
            application_list=[self.pvc_1, self.pvc_2],
            overwrite=True
        )
        # Validate resources at source and destination
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)

        # Create temporary pods to get checksum of data present in PVC
        self.kubehelper.create_cv_pod(self.pod_1, self.restore_namespace, pvc_name=self.pvc_1)
        self.kubehelper.create_cv_pod(self.pod_2, self.restore_namespace, pvc_name=self.pvc_2)
        self.dest_checksum = self.kubehelper.get_files_checksum(self.restore_namespace)

        # Compare checksum of data present at source with checksum of data present at destination
        self.kubehelper.verify_checksum_dictionary(self.src_checksum, self.dest_checksum)

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)
            self.log.info("----------------Phase 1 Snapshot Based Backup-----------------------")
            # Step 1 - Take FULL Backup of App Group
            self.snapshot_based_backup()

            # Step 2 - Perform OOP Restore of Namespace
            self.verify_app_level_oop_restore()

            self.log.info("Deleting and Recreating the Restore Namespace")
            self.kubehelper.delete_cv_namespace(self.restore_namespace)
            self.kubehelper.create_cv_namespace(self.restore_namespace)

            self.log.info("---------------Phase 2 Live Volume Backup-------------------------")
            # Step 3 - Take FULL Backup of App Group
            self.live_volume_backup()

            # Step 4 - Perform OOP Restore of Namespace
            self.verify_app_level_oop_restore()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 5 -- Delete testbed, delete client ")
            self.delete_testbed()
