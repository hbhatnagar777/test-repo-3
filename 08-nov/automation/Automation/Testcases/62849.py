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
    3. Create namespaces containing lr only, rq only,lr and rq
    4. Perform backup of ns with lr only. Verify Job completed, pod used correct resource constraints
    5. Perform backup of ns with rq only. Verify job completed, pod used correct resource constraints
    6. Perform backup of ns with lr and rq. Verify job completed, pod used correct resource constraints
    7. Apply regkeys to specify worker resource consumption
    8. Perform backup of ns with lr only. Verify Job completed, pod used correct resource constraints
    9. Perform backup of ns with rq only. Verify job completed, pod used correct resource constraints
    10. Perform backup of ns with lr and rq. Verify job completed, pod used correct resource constraints
    11. Cleanup testbed
    12. Cleanup clients created.
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.lr_only_ns = None
        self.rq_only_ns = None
        self.lr_and_rq = None
        self.name = "Kubernetes - Backup and restore validation with ResourceQuota and LimitRange on " \
                    "Namespace with and without regkey"
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
        self.cpu_max = '300m'
        self.cpu_min = '200m'
        self.mem_max = '512Mi'
        self.mem_min = '256Mi'

    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.lr_only_ns = self.testbed_name + "lr-only"
        self.rq_only_ns = self.testbed_name + "rq-only"
        self.lr_and_rq = self.testbed_name + "lr-rq"
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
        self.kubehelper.create_cv_namespace(self.lr_only_ns)
        self.kubehelper.create_cv_namespace(self.rq_only_ns)
        self.kubehelper.create_cv_namespace(self.lr_and_rq)

        # Create Limit Range in lr_and_rq and lr_only_ns
        lr1 = self.testbed_name + 'lr1'
        self.kubehelper.create_cv_limit_range(
            lr1,
            namespace=self.lr_and_rq,
        )
        self.kubehelper.create_cv_limit_range(
            lr1,
            namespace=self.lr_only_ns,
        )
        # Create Resource quota in rq_only_ns and lr_and_rq
        rq1 = self.testbed_name + 'rq1'
        self.kubehelper.create_cv_resource_quota(
            rq1,
            self.rq_only_ns,
        )
        self.kubehelper.create_cv_resource_quota(
            rq1,
            self.lr_and_rq,
        )

        # Creating CV PVC and Pod in all NS
        pvc_pod_name = self.testbed_name + '-podpvc'
        self.kubehelper.create_cv_pvc(pvc_pod_name, self.lr_and_rq, storage_class=self.storageclass)
        self.kubehelper.create_cv_pvc(pvc_pod_name, self.lr_only_ns, storage_class=self.storageclass)
        self.kubehelper.create_cv_pvc(pvc_pod_name, self.rq_only_ns, storage_class=self.storageclass)
        pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(
            pod_name, self.lr_and_rq, pvc_name=pvc_pod_name
        )
        self.kubehelper.create_cv_pod(
            pod_name, self.lr_only_ns, pvc_name=pvc_pod_name
        )
        self.kubehelper.create_cv_pod(
            pod_name, self.rq_only_ns, pvc_name=pvc_pod_name,
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

        # Set logging debug level
        self.proxy_obj.set_logging_debug_level(service_name='vsbkp', level='2')

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
        self.proxy_obj.set_logging_debug_level(service_name='vsbkp.log', level='1')
        self.kubehelper.delete_cv_namespace(self.lr_and_rq)
        self.kubehelper.delete_cv_namespace(self.lr_only_ns)
        self.kubehelper.delete_cv_namespace(self.rq_only_ns)

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
    def create_app_group_and_perform_backup(self, namespace, mem_min, cpu_min, mem_max, cpu_max):
        """Create app group and Perform backup

        Args:

            namespace               (str)   namespace to back up

            mem_min                 (str)   Expected value of worker pod memory request

            cpu_min                 (str)   Expected value of worker pod cpu request

            mem_max                 (str)   Expected value of worker pod memory limit

            cpu_max                 (str)   Expected value of worker pod cpu limit

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
        self.log.info('FULL Backup job step with Namespace as content successfully completed.'
                      'Proceeding with resource validation from logs')
        self.verify_resource_limits(mem_min, cpu_min, mem_max, cpu_max, job_id=backup_job.job_id)
        self.log.info(f'Resource limits are applied correctly in {namespace}')
        # Remove app group
        KubernetesUtils.delete_application_group(self, self.subclientName)

    @TestStep()
    def verify_resource_limits(self, mem_min, cpu_min, mem_max, cpu_max, job_id):
        """
        Verifies whether resource limits are correctly applied to pods

        Args:
            job_id          (string)        Job ID

            mem_min         (string)        Memory request

            cpu_min         (string)        CPU request

            mem_max         (string)        Memory limit

            cpu_max         (string)        CPU limit
        """

        # get logs for a particular job

        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=job_id,
            log_file_name="vsbkp.log",
            pattern=LogLineRepo.WORKER_POD_RESOURCES.value.format(
                cpu_max,
                mem_max,
                cpu_min,
                mem_min,
            ),
            expected_keyword=None
        )

    @TestStep()
    def remove_keys(self):
        """
        Removing regkey
        """
        self.log.info('Removing regkeys')

        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.WORKER_CPU_MAX.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.WORKER_CPU_MAX.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.WORKER_CPU_MAX.value}]"
            )
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.WORKER_CPU_MIN.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.WORKER_CPU_MIN.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.WORKER_CPU_MIN.value}]"
            )
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.WORKER_MEM_MAX.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.WORKER_MEM_MAX.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.WORKER_MEM_MAX.value}]"
            )
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.WORKER_MEM_MIN.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.WORKER_MEM_MIN.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.WORKER_MEM_MIN.value}]"
            )

    @TestStep()
    def add_keys(self):
        """
        Add regkey to AN
        """

        self.log.info('Adding regkeys')
        self.log.info(f'sK8sWorkerCpuMax: {self.cpu_max} ')
        self.log.info(f'sK8sWorkerCpuMin: {self.cpu_min} ')
        self.log.info(f'sK8sWorkerMemMax: {self.mem_max}')
        self.log.info(f'sK8sWorkerMemMin: {self.mem_min}')

        # Check sK8sWorkerCpuMax
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.WORKER_CPU_MAX.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.WORKER_CPU_MAX.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.WORKER_CPU_MAX.value}]"
            )

        self.log.info(f"Adding additional setting [{KubernetesAdditionalSettings.WORKER_CPU_MAX.value}]"
                      f" with value {self.cpu_max}")

        self.controller.add_additional_setting(
            category=KubernetesAdditionalSettings.CATEGORY.value,
            key_name=KubernetesAdditionalSettings.WORKER_CPU_MAX.value,
            data_type=KubernetesAdditionalSettings.STRING.value,
            value=self.cpu_max
        )

        # Check sK8sWorkerCpuMin
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.WORKER_CPU_MIN.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.WORKER_CPU_MIN.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.WORKER_CPU_MIN.value}]"
            )

        self.log.info(f"Adding additional setting [{KubernetesAdditionalSettings.WORKER_CPU_MIN.value}]"
                      f" with value {self.cpu_min}")

        self.controller.add_additional_setting(
            category=KubernetesAdditionalSettings.CATEGORY.value,
            key_name=KubernetesAdditionalSettings.WORKER_CPU_MIN.value,
            data_type=KubernetesAdditionalSettings.STRING.value,
            value=self.cpu_min
        )

        # Check sK8sWorkerMemMax
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.WORKER_MEM_MAX.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.WORKER_MEM_MAX.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.WORKER_MEM_MAX.value}]"
            )

        self.log.info(f"Adding additional setting [{KubernetesAdditionalSettings.WORKER_MEM_MAX.value}]"
                      f" with value {self.mem_max}")

        self.controller.add_additional_setting(
            category=KubernetesAdditionalSettings.CATEGORY.value,
            key_name=KubernetesAdditionalSettings.WORKER_MEM_MAX.value,
            data_type=KubernetesAdditionalSettings.STRING.value,
            value=self.mem_max
        )

        # Check sK8sWorkerMemMin
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.WORKER_MEM_MIN.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.WORKER_MEM_MIN.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.WORKER_MEM_MIN.value}]"
            )

        self.log.info(f"Adding additional setting [{KubernetesAdditionalSettings.WORKER_MEM_MIN.value}]"
                      f" with value {self.mem_min}")

        self.controller.add_additional_setting(
            category=KubernetesAdditionalSettings.CATEGORY.value,
            key_name=KubernetesAdditionalSettings.WORKER_MEM_MIN.value,
            data_type=KubernetesAdditionalSettings.STRING.value,
            value=self.mem_min
        )

    def run(self):
        """
        Run the Testcase
        """
        try:
            self.remove_keys()
            # Step 1 - Take FULL Backup of NS lr_and_rq with No keys - expectation - Uses min,max specified in LR
            self.create_app_group_and_perform_backup(
                namespace=self.lr_and_rq,
                mem_min='100Mi',
                cpu_min='100m',
                mem_max='1Gi',
                cpu_max='1'
            )
            # Step 2 - Take FULL Backup of NS lr_only with No keys - expectation - Uses min,max specified in LR
            self.create_app_group_and_perform_backup(
                namespace=self.lr_only_ns,
                mem_min='100Mi',
                cpu_min='100m',
                mem_max='1Gi',
                cpu_max='1'
            )
            # Step 3 - Take FULL Backup of NS rq_only with No keys, expectation - Uses commvault default consumption
            self.create_app_group_and_perform_backup(
                namespace=self.rq_only_ns,
                mem_min='16Mi',
                cpu_min='5m',
                mem_max='128Mi',
                cpu_max='500m'
            )
            # Step 4 - Add keys
            self.add_keys()
            # Step 5 - Take FULL Backup of NS lr_and_rq keys - expectation - consumption based on keys
            self.create_app_group_and_perform_backup(
                namespace=self.lr_and_rq,
                mem_min=self.mem_min,
                mem_max=self.mem_max,
                cpu_min=self.cpu_min,
                cpu_max=self.cpu_max
            )
            # Step 6 - Take FULL Backup of NS lr_only_ns with keys - expectation - consumption based on keys
            self.create_app_group_and_perform_backup(
                namespace=self.lr_only_ns,
                mem_min=self.mem_min,
                mem_max=self.mem_max,
                cpu_min=self.cpu_min,
                cpu_max=self.cpu_max

            )
            # Step 7 Take FULL Backup of NS rq_only_ns with keys  - - expectation - consumption based on keys
            self.create_app_group_and_perform_backup(
                namespace=self.rq_only_ns,
                mem_min=self.mem_min,
                mem_max=self.mem_max,
                cpu_min=self.cpu_min,
                cpu_max=self.cpu_max
            )

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 6 -- Delete testbed, delete client, remove keys ")

            self.delete_testbed()
