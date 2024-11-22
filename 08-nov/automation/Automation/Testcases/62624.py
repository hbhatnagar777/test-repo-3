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

    verify_overwrite() --               --  Verifies if system namespace has been overwritten

    verify_full_ns_backup()             --  Verify full backup

    run()                               --  Run function of this test case
"""

import time
from AutomationUtils import config
from AutomationUtils.Performance.Utils.constants import JobStatus
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Kubernetes.constants import KubernetesAdditionalSettings, ErrorReasonRepo, LogLineRepo
from Reports.utils import TestCaseUtils
from Server.JobManager.jobmanager_helper import JobManager
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes import KubernetesUtils
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform backups and namespace-level restores on namespaces starting with
    system Prefix. (Eg- kube-* , openshift-*)
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create Namespace kube-* with orphan secrets, configmaps, serviceaccounts,etc for testbed
    5. Create Namespace openshift-* with orphan secrets, configmaps, serviceaccounts,etc for testbed
    6. Create a Kubernetes client with proxy provided
    7. Create application group for kubernetes with kube-* namespace and openshift-* namespace as content
    8. Initiate Full Backup for App group created and verify job completed
    9. Initiate in-place namespace-level restore with overwrite and verify job failed
    10. Cleanup testbed
    11. Cleanup clients created.
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Namespace-level Backup and Restore of namespaces with kube-* and openshift-* prefix"
        self.utils = TestCaseUtils(self)
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.controller_id = None
        self.testbed_name = None
        self.namespace_kube = None
        self.namespace_ocp = None
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
        self.flag = None
        self.job_obj = None
        self.pod_name_1 = None
        self.pod_name_2 = None
        self.restore_namespace = None

    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.namespace_kube = "kube-" + self.testbed_name
        self.namespace_ocp = "openshift-" + self.testbed_name
        self.restore_namespace = "kube-" + self.testbed_name + "-rst"
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
        self.pod_name_1 = self.testbed_name + "-pod-1"
        self.pod_name_2 = self.testbed_name + "-pod-2"

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

    def create_orphan_resources(self):
        """
        Create orphan resources in namespace
        """
        self.log.info(f'Creating some orphan resources in namespace [{self.namespace_kube}]')
        orphan_secret = self.testbed_name + '-orphan-secret'
        orphan_cm = self.testbed_name + '-orphan-cm'
        orphan_svc = self.testbed_name + '-orphan-svc'
        orphan_sa = self.testbed_name + '-orphan-sa'
        # NS format kube-*
        self.kubehelper.create_cv_secret(orphan_secret, self.namespace_kube)
        self.kubehelper.create_cv_configmap(orphan_cm, self.namespace_kube)
        self.kubehelper.create_cv_svc(
            orphan_svc, self.namespace_kube, selector={self.namespace_kube: self.namespace_kube}
        )
        self.kubehelper.create_cv_serviceaccount(orphan_sa, self.namespace_kube)
        # NS format openshift-*
        self.log.info(f'Creating some orphan resources in namespace [{self.namespace_ocp}]')
        self.kubehelper.create_cv_secret(orphan_secret, self.namespace_ocp)
        self.kubehelper.create_cv_configmap(orphan_cm, self.namespace_ocp)
        self.kubehelper.create_cv_svc(orphan_svc, self.namespace_ocp, selector={self.namespace_ocp: self.namespace_ocp})
        self.kubehelper.create_cv_serviceaccount(orphan_sa, self.namespace_ocp)

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

        # Creating testbed namespaces
        self.kubehelper.create_cv_namespace(self.namespace_kube)
        self.kubehelper.create_cv_namespace(self.namespace_ocp)

        self.kubehelper.create_cv_pod(
            self.pod_name_1, self.namespace_kube
        )
        self.kubehelper.create_cv_pod(
            self.pod_name_2, self.namespace_ocp
        )

        # Create orphan resources in the namespace
        self.create_orphan_resources()
        self.content.append(self.namespace_kube)
        self.content.append(self.namespace_ocp)

        # Set regkey to find system namespaces
        self.controller.add_additional_setting(
            category=KubernetesAdditionalSettings.CATEGORY.value,
            key_name=KubernetesAdditionalSettings.SHOW_SYSTEM_NAMESPACES.value,
            data_type=KubernetesAdditionalSettings.BOOLEAN.value,
            value="1"
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

        self.kubehelper.delete_cv_namespace(self.namespace_kube)
        self.kubehelper.delete_cv_namespace(self.namespace_ocp)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)

        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        self.log.info(
            f"Removing additional setting [{KubernetesAdditionalSettings.SHOW_SYSTEM_NAMESPACES.value}] " +
            "if present on access node"
        )
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.SHOW_SYSTEM_NAMESPACES.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.SHOW_SYSTEM_NAMESPACES.value
            )
            self.log.info(
                f"Successfully removed additional setting [{KubernetesAdditionalSettings.SHOW_SYSTEM_NAMESPACES.value}]"
            )

        KubernetesUtils.delete_cluster(self, self.clientName)

    @TestStep()
    def verify_full_ns_backup(self):
        """Verify FULL Backup of entire namespace as content
        """
        self.log.info('Step 1 -- Run FULL Backup job with Namespace as content')
        self.kubehelper.backup("FULL")
        self.log.info('FULL Backup job step with Namespace as content successfully completed')

    @TestStep()
    def verify_overwrite(self):
        """
        Verify failure of Namespace-level restore in-place with overwrite
        """

        self.log.info('Step 2 -- Run Namespace-level restore In place with overwrite')
        resources_before_restore_kube = self.kubehelper.get_all_resources(namespace=self.namespace_kube)
        resources_before_restore_ocp = self.kubehelper.get_all_resources(namespace=self.namespace_ocp)
        self.kubehelper.delete_cv_pod(
            namespace=self.namespace_kube,
            name=self.pod_name_1
        )
        orphan_sa = self.testbed_name + '-orphan-sa'
        self.kubehelper.delete_cv_serviceaccount(
            sa_name=orphan_sa,
            sa_namespace=self.namespace_kube
        )

        self.job_obj = self.kubehelper.namespace_level_restore(
            namespace_list=self.content,
            in_place=True,
            raise_exception=False
        )

        job_mgr_obj = JobManager(self.job_obj)
        job_mgr_obj.validate_job_state(
            expected_state=JobStatus.COMPLETED_WITH_ERRORS
        )
        self.log.info(
            "Job completed w/ one or more errors. Expected scenario achieved. Proceeding with restore validation"
        )

        # Namespace will have an Error Reason but not app
        app_jpr_template = ErrorReasonRepo.UNABLE_TO_CREATE_NEW_APPLICATION.value
        jpr_dict = {
            self.namespace_kube: '',
            self.namespace_ocp: '',
            self.pod_name_1: '',
            self.pod_name_2: app_jpr_template.format(self.pod_name_2, self.access_node)
        }
        self.kubehelper.validate_child_job_jpr(self.job_obj, jpr_dict)

        self.log.info("Validating log lines for expected logging")
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=self.job_obj.job_id,
            log_file_name="vsrst.log",
            pattern=LogLineRepo.RESTORE_APP_IN_SYSTEM_NAMESPACE_EXISTS.value,
            expected_keyword=self.pod_name_2
        )

        resources_after_restore_kube = self.kubehelper.get_all_resources(namespace=self.namespace_kube)
        resources_after_restore_ocp = self.kubehelper.get_all_resources(namespace=self.namespace_ocp)

        self.kubehelper.validate_data(
            resources_before_restore_kube, resources_after_restore_kube
        )
        self.kubehelper.validate_data(
            resources_before_restore_ocp, resources_after_restore_ocp
        )

        self.log.info('Namespace-level restore in-place with overwrite step successfully completed')

    @TestStep()
    def namespace_level_rst(self):
        """Verify namespace level restore out-of-place
        """
        self.log.info('Step 3 -- Run Namespace-level restore out-of-place without overwrite')
        self.kubehelper.namespace_level_restore(
            client_name=self.clientName,
            namespace_list=[self.namespace_ocp],
            restore_name_map={self.namespace_ocp: self.restore_namespace}
        )
        self.log.info('Namespace-level restore out-of-place step successfully completed')

    @TestStep()
    def full_app_restore_oop(self):
        """
        Verify failure of Full Application restore out-of-place with overwrite
        """
        self.log.info('Step 4 -- Run Full Application restore out-of-place with overwrite')
        resources_before_restore_ocp = self.kubehelper.get_all_resources(namespace=self.namespace_ocp)
        self.job_obj = self.kubehelper.restore_out_of_place(
            client_name=self.clientName,
            restore_namespace=self.restore_namespace,
            application_list=[self.pod_name_2],
            raise_exception=False
        )

        job_mgr_obj = JobManager(self.job_obj)
        job_mgr_obj.validate_job_state(
            expected_state=JobStatus.FAILED
        )
        self.log.info("Job failed. Expected scenario achieved. Proceeding with restore validation")

        # Namespace will have an Error Reason but not app
        app_jpr_template = ErrorReasonRepo.UNABLE_TO_CREATE_NEW_APPLICATION.value
        jpr_dict = {
            self.pod_name_2: app_jpr_template.format(self.pod_name_2, self.access_node)
        }
        self.kubehelper.validate_child_job_jpr(self.job_obj, jpr_dict)

        self.log.info("Validating log lines for expected logging")
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=self.job_obj.job_id,
            log_file_name="vsrst.log",
            pattern=LogLineRepo.RESTORE_APP_IN_SYSTEM_NAMESPACE_EXISTS.value,
            expected_keyword=self.pod_name_2
        )

        resources_after_restore_ocp = self.kubehelper.get_all_resources(namespace=self.restore_namespace)
        self.kubehelper.validate_data(
            resources_before_restore_ocp, resources_after_restore_ocp
        )
        self.log.info('Full Application restore out-of-place with overwrite step successfully completed')

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)
            # Step 1 - Take FULL Backup of App Group
            self.verify_full_ns_backup()
            # Step 2 - Perform IP Restore of Namespace with overwrite
            self.verify_overwrite()
            # Step 3 - Perform Out-of-place Namespace level restore
            self.namespace_level_rst()
            # Step 4 - Perform out-of-place full application restore
            self.full_app_restore_oop()

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 6 -- Delete testbed, delete client ")
            self.delete_testbed()
