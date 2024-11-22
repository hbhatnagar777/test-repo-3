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
    3. Create namespaces containing rq limiting PVC and rq limiting VolumeSnapshot
    4. Apply regkey bK8sSnapFallBackLiveBkp
    5. Perform backup of PVC rq. PVC creation should fail. But job will fallback to using live volume backup
    6. Verify job success and log lines
    7. Perform backup of VolumeSnapshot rq. PVC creation should fail. But job will fallback to using live volume backup
    8. Verify job success and log lines
    9. Remove regkey bK8sSnapFallBackLiveBkp
    10. Cleanup clients created.
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.lr_only_ns = None
        self.rq_only_ns = None
        self.lr_and_rq = None
        self.name = "Kubernetes - Verify live volume fallback"
        self.utils = TestCaseUtils(self)
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.controller_id = None
        self.testbed_name = None
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
        self.pvc_quota_ns = None
        self.snap_quota_ns = None

    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.pvc_quota_ns = self.testbed_name + "-pvc-quota"
        self.snap_quota_ns = self.testbed_name + "-snap-quota"
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
        self.kubehelper.create_cv_namespace(self.pvc_quota_ns)
        self.kubehelper.create_cv_namespace(self.snap_quota_ns)

        # Create Limit Range in lr_and_rq and lr_only_ns
        pvc_rq = self.testbed_name + '-pvc-rq'
        self.kubehelper.create_cv_resource_quota(
            pvc_rq,
            namespace=self.pvc_quota_ns,
            misc_resource_count={'persistentvolumeclaims': '1'}
        )

        # Create Resource quota in rq_only_ns and lr_and_rq
        snap_rq = self.testbed_name + '-snap-rq'
        self.kubehelper.create_cv_resource_quota(
            snap_rq,
            namespace=self.snap_quota_ns,
            misc_resource_count={'count/volumesnapshots.snapshot.storage.k8s.io': '0'}
        )

        # Creating CV PVC and Pod in all NS
        pvc_pod_name = self.testbed_name + '-podpvc'
        self.kubehelper.create_cv_pvc(pvc_pod_name, self.snap_quota_ns, storage_class=self.storageclass)
        self.kubehelper.create_cv_pvc(pvc_pod_name, self.pvc_quota_ns, storage_class=self.storageclass)
        pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(
            pod_name, self.snap_quota_ns, pvc_name=pvc_pod_name,
            resources={
                "requests": {
                    "memory": "200Mi",
                    "cpu": "500m"
                },
                "limits": {
                    "memory": "500Mi",
                    "cpu": "500m"
                }
            }
        )
        self.kubehelper.create_cv_pod(
            pod_name, self.pvc_quota_ns, pvc_name=pvc_pod_name,
            resources={
                "requests": {
                    "memory": "200Mi",
                    "cpu": "500m"
                },
                "limits": {
                    "memory": "500Mi",
                    "cpu": "500m"
                }
            }
        )

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
        self.remove_keys()
        self.kubehelper.delete_cv_namespace(self.snap_quota_ns)
        self.kubehelper.delete_cv_namespace(self.pvc_quota_ns)

        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)

    @TestStep()
    def create_app_group_and_perform_backup(self, namespace, fallback_type):
        """Create app group and Perform backup

        Args:

            namespace               (str)   namespace to back up

            fallback_type           (str)   pvc or snapshot

        """

        self.content = [namespace]
        KubernetesUtils.add_application_group(
            self,
            content=self.content,
            plan=self.plan,
            name=self.subclientName,
        )
        self.kubehelper.source_vm_object_creation(self)
        self.log.info(f'Run FULL Backup job with {namespace} as content')
        backup_job = self.kubehelper.backup("FULL")
        self.log.info(f'FULL Backup job step with {namespace} as content successfully completed.'
                      'Proceeding with fallback validation from logs')
        self.verify_live_volume_fallback(job_id=backup_job.job_id, fallback_type=fallback_type)
        self.log.info(f'Live volume fallback successful {namespace}')
        # Remove app group
        KubernetesUtils.delete_application_group(self, self.subclientName)

    @TestStep()
    def verify_live_volume_fallback(self, job_id, fallback_type):
        """
        Verifies whether resource limits are correctly applied to pods

        Args:

            job_id          (string)        Job ID

            fallback_type   (string)        'snapshot' or 'pvc'


        """

        if fallback_type == 'snapshot':
            pattern = LogLineRepo.SNAP_FAIL_LIVE_VOLUME_FALLBACK.value
        elif fallback_type == 'pvc':
            pattern = LogLineRepo.PVC_FAIL_LIVE_VOLUME_FALLBACK.value
        else:
            raise KubernetesException(
                exception_module='ValidationOperations',
                exception_id='107',
                exception_message="Invalid fallback type")

        # get logs for a particular job

        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=job_id,
            log_file_name="vsbkp.log",
            pattern=pattern,
            expected_keyword=None
        )

    @TestStep()
    def remove_keys(self):
        """
        Removing regkey
        """
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
    def add_keys(self):
        """
        Add regkey to AN
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

    def run(self):
        """
        Run the Testcase
        """
        try:
            self.add_keys()
            # Step 1 - Take FULL Backup of NS with PVC limit
            self.create_app_group_and_perform_backup(
                namespace=self.pvc_quota_ns,
                fallback_type='pvc'
            )
            # Step 2 - Take FULL Backup of NS Snapshot limit
            self.create_app_group_and_perform_backup(
                namespace=self.snap_quota_ns,
                fallback_type='snapshot'
            )
            self.remove_keys()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 3 -- Delete testbed, delete client, remove keys ")

            self.delete_testbed()
