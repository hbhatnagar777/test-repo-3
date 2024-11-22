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
from AutomationUtils.Performance.Utils.constants import JobStatus
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Kubernetes.constants import ErrorReasonRepo, LogLineRepo
from Reports.utils import TestCaseUtils
from Server.JobManager.jobmanager_helper import JobManager
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes import KubernetesUtils
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform different restores of applications.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create Namespace, Pod, PVC, deployment  for testbed
    5. Create a Kubernetes client with proxy provided
    6. Create application group for kubernetes
    7. Initiate Full Backup for App group with shared PVC and verify job completed
    8. Initiate Out-of-place namespace level restore with overwrite true, app and namespace do not exist
    9. Initiate Out-of-place namespace level restore with overwrite true, app and namespace both exist
    10. Initiate Out-of-place full app restore with overwrite true, app and namespace both exist
    11. Initiate In-place full app restore with overwrite true, app and namespace both exist
    12. Initiate Out-of-place full app restore with overwrite true, namespace exist, app do not exist
    13. Initiate Out-of-place full app restore with overwrite false, namespace exist but app do not exist
    14. Initiate Out-of-place namespace level restore with overwrite false, namespace exist but app do not exist
    15. Initiate Out-of-place namespace level restore with overwrite false, namespace and app both exist
    16. Initiate Out-of-place full app restore with overwrite false, namespace and app both exist
    17. Cleanup testbed
    18. Cleanup clients created.
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Restores with Overwrite option validation"
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
        self.sts_name = None
        self.pvc_name = None
        self.resources_before_backup = None
        self.resources_after_restore = None
        self.job_obj = None

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
        self.sts_name = self.testbed_name + '-sts'

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

        self.kubehelper.create_cv_statefulset(
            name=self.sts_name,
            namespace=self.namespace
        )
        time.sleep(30)

        for pod_name in self.kubehelper.get_namespace_pods(
                namespace=self.namespace
        ):
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
    def verify_ns_oop_restore_step_1(self):
        """Verify Namespace level Restore Step without overwrite and destination not existing
        """
        self.log.info(f"Expectation - Namespace level Restore job should succeed for namespace and application")

        self.kubehelper.namespace_level_restore(
            self.clientName,
            self.access_node,
            namespace_list=[self.namespace],
            restore_name_map={self.namespace: self.restore_namespace_ns},
            overwrite=True
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace_ns)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace_ns)
        self.log.info(f"Namespace level restore step without overwrite succeeded.")

    @TestStep()
    def verify_ns_oop_restore_step_2(self):
        """Verify Namespace level Restore Step with overwrite and destination namespace and apps existing
        """
        self.log.info(f"Expectation - Namespace level Restore job should succeed for namespace and application")

        self.kubehelper.namespace_level_restore(
            self.clientName,
            self.access_node,
            namespace_list=[self.namespace],
            restore_name_map={self.namespace: self.restore_namespace_ns},
            overwrite=True
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace_ns)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace_ns)
        self.log.info(f"Namespace level restore step with overwrite succeeded.")

    @TestStep()
    def verify_app_oop_restore_step_3(self):
        """Verify Full Application Restore Step with overwrite and destination namespace and apps existing
        """
        self.log.info(f"Expectation - Full Application Restore job should succeed for namespace and application")

        self.kubehelper.run_restore_validate(
            client_name=self.clientName
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)
        self.log.info(f"Full Application restore step with overwrite succeeded.")

    @TestStep()
    def verify_app_ip_restore_step_4(self):
        """Verify Full Application Restore In-place Step with overwrite and destination namespace and apps existing
        """
        self.log.info(f"Expectation - Full Application Restore job should succeed for namespace and application")

        checksum_before_restore = self.kubehelper.get_files_checksum(self.namespace)
        self.kubehelper.run_restore_validate(
            client_name=self.clientName,
            inplace=True
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        checksum_after_restore = self.kubehelper.get_files_checksum(self.restore_namespace)
        self.kubehelper.verify_checksum_dictionary(checksum_before_restore, checksum_after_restore)
        self.log.info(f"Full Application restore step in-place with overwrite succeeded.")

    @TestStep()
    def verify_app_oop_restore_step_5(self):
        """Verify Full Application Restore Step with overwrite and destination namespace existing and apps not existing
        """
        self.log.info(f"Expectation - Full Application Restore job should succeed for namespace and application")

        self.kubehelper.delete_cv_namespace(self.restore_namespace)
        self.kubehelper.create_cv_namespace(self.restore_namespace)
        self.kubehelper.run_restore_validate(
            client_name=self.clientName
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)
        self.log.info(f"Full Application restore step with overwrite succeeded.")

    @TestStep()
    def verify_app_oop_restore_step_6(self):
        """Verify Full Application Restore Step without overwrite and apps not existing and namespace existing
        """
        self.log.info(f"Expectation - Full Application Restore job should succeed for namespace and application")

        self.kubehelper.delete_cv_namespace(self.restore_namespace)
        self.kubehelper.create_cv_namespace(self.restore_namespace)
        self.kubehelper.run_restore_validate(
            client_name=self.clientName,
            overwrite=False
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)
        self.log.info(f"Full Application restore step without overwrite succeeded.")

    @TestStep()
    def verify_ns_oop_restore_step_7(self):
        """Verify Namespace level Restore Step without overwrite and apps not existing and namespace existing
        """
        self.log.info(f"Expectation - Namespace level Restore job should succeed for app and namespace")

        self.kubehelper.delete_cv_namespace(self.restore_namespace_ns)
        self.kubehelper.create_cv_namespace(self.restore_namespace_ns)

        self.job_obj = self.kubehelper.namespace_level_restore(
            self.clientName,
            self.access_node,
            namespace_list=[self.namespace],
            restore_name_map={self.namespace: self.restore_namespace_ns},
            overwrite=False,
            raise_exception=False
        )
        job_mgr_obj = JobManager(self.job_obj)
        job_mgr_obj.validate_job_state(
            expected_state=JobStatus.COMPLETED
        )

        self.log.info(
            "Job completed. Expected scenario achieved. Proceeding with restore validation"
        )

        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace_ns)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace_ns)
        self.log.info(f"Namespace level restore step without overwrite succeeded.")

    @TestStep()
    def verify_ns_oop_restore_step_8(self):
        """Verify Namespace level Restore Step without overwrite and apps and namespace existing
        """
        self.log.info(f"Expectation - Namespace level Restore job should fail application and pass for namespace")

        self.job_obj = self.kubehelper.namespace_level_restore(
            self.clientName,
            self.access_node,
            namespace_list=[self.namespace],
            restore_name_map={self.namespace: self.restore_namespace_ns},
            overwrite=False,
            raise_exception=False
        )

        job_mgr_obj = JobManager(self.job_obj)
        job_mgr_obj.validate_job_state(
            expected_state=JobStatus.COMPLETED_WITH_ERRORS
        )
        self.log.info("Job Failed. Expected scenario achieved. Proceeding with JPR validation")

        # App will have an Error Reason
        app_jpr_template = ErrorReasonRepo.ERROR_RESTORING_DATA.value
        jpr_dict = {
            self.sts_name: app_jpr_template
        }
        self.kubehelper.validate_child_job_jpr(self.job_obj, jpr_dict)

        self.log.info("Validating log lines for expected logging")

        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=self.job_obj.job_id,
            log_file_name="vsrst.log",
            pattern=LogLineRepo.RESTORE_FAILURE_APPLICATION_EXISTS.value,
            expected_keyword=self.sts_name
        )

        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace_ns)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace_ns)
        self.log.info(f"Namespace level restore step without overwrite succeeded.")

    @TestStep()
    def verify_app_oop_restore_step_9(self):
        """Verify Full Application Restore Step without overwrite and namespace and apps both existing
        """
        self.log.info(f"Expectation - Full Application Restore job should fail for application")

        self.job_obj = self.kubehelper.restore_out_of_place(
            client_name=self.clientName,
            overwrite=False,
            restore_namespace=self.restore_namespace,
            raise_exception=False
        )
        job_mgr_obj = JobManager(self.job_obj)
        job_mgr_obj.validate_job_state(
            expected_state=JobStatus.FAILED
        )
        self.log.info("Job Failed. Expected scenario achieved. Proceeding with restore validation")

        app_jpr_template = ErrorReasonRepo.ERROR_RESTORING_DATA.value
        jpr_dict = {
            self.sts_name: app_jpr_template
        }
        self.kubehelper.validate_child_job_jpr(self.job_obj, jpr_dict)

        self.log.info("Validating log lines for expected logging")
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=self.job_obj.job_id,
            log_file_name="vsrst.log",
            pattern=LogLineRepo.RESTORE_FAILURE_APPLICATION_EXISTS.value,
            expected_keyword=self.sts_name
        )

        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)
        self.log.info(f"Full Application restore step without overwrite succeeded.")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Run Full Job and incremental job before verifying restore
            self.verify_backup()

            # Namespace-level Restore, Overwrite True, App do not exist, namespace do not exist
            self.verify_ns_oop_restore_step_1()

            # Namespace-leve Restore, Overwrite True, App exist, namespace exist
            self.verify_ns_oop_restore_step_2()

            # Full App Restore, Overwrite True, App exist, namespace exist
            self.verify_app_oop_restore_step_3()

            # Full App Restore In-place, Overwrite True, App exist, namespace exist
            self.verify_app_ip_restore_step_4()

            # Full App Restore, Overwrite True, App do not exist, namespace exist
            self.verify_app_oop_restore_step_5()

            # Full App Restore, Overwrite False, App do not exist, namespace exist
            self.verify_app_oop_restore_step_6()

            # Namespace-level Restore, Overwrite False, App do not exist, namespace exist
            self.verify_ns_oop_restore_step_7()

            # Namespace-level Restore, Overwrite False, App exist, namespace exist
            self.verify_ns_oop_restore_step_8()

            # Full App Restore, Overwrite False, App exist, namespace exist
            self.verify_app_oop_restore_step_9()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step -- Delete testbed, delete client ")
            self.delete_testbed()
