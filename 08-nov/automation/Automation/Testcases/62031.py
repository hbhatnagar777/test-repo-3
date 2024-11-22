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

    wait_for_job_progress()             --  wait for the job progress to reach percent_complete

    setup()                             --  setup method for test case

    tear_down()                         --  tear down method for testcase

    init_inputs()                       --  Initialize objects required for the testcase

    load_kubeconfig_file()              --  Load Kubeconfig file and connect to the Kubernetes API Server

    create_testbed()                    --  Create the testbed required for the testcase

    delete_testbed()                    --  Delete the testbed created

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    commit_job_validate()               --  Test step to validate committed job scenario

    kill_job_validate()                 --  Kill backup job and validate cleanup

    verify_restore_step()               --  Verify restore job

    kill_restore_job_validate()         --  Kill restore job and validate cleanup

    restore_job_suspend()               --  Suspend and resume restore job and validate cleanup

    validate_restart_services_backup()  --  Restart services on access node and validate backup

    validate_restart_services_restore() --  Restart services on access node and validate restore

    verify_restore_step()               --  Launch restore and verify file restored resources

    verify_suspend_resume()             --  Suspend and resume backup job and validate cleanup and files backed up

    run()                               --  Run function of this test case
"""

import time

from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.interruption import Interruption
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Server.JobManager.jobmanager_helper import JobManager
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from VirtualServer.VSAUtils import VirtualServerUtils
from Kubernetes import KubernetesUtils
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform backup and restore of stateless applications.
    This testcase does the following --
        1. Connect to Kubernetes API Server using Kubeconfig File
        2. Create Service Account, ClusterRoleBinding for CV
        3. Fetch Token name and Token for the created Service Account Secret
        4. Create Namespace, Pod, PVC, deployment  for testbed
        5. Create a Kubernetes client with proxy provided
        6. Create application group for kubernetes
        7. Create random test data
        8. Initiate Full Backup, suspend and resume the job and validate files are correctly backed up
        9. Initiate Full Backup, Restart services on proxy and validate files are correctly backed up
        10. Initiate Full backup, kill job and validate cleanup
        11. Initiate Full backup, commit job and validate cleanup
        12. Initiate Full App restore, suspend resume and validate restored files
        13. Initiate Full App restore, kill job and validate cleanup
        14. Initiate Full App restore, restart services on proxy and validate files are correctly backed up
        15. Cleanup testbed and cleanup client created
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Restartability and Cleanup Scenarios : Suspend, Resume, Kill, Commit, Service Restart"
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
        self.job_mgr_obj = None
        self.interruption_helper = None

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
        self.controller_machine = Machine(self.controller)

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

    @TestStep()
    def create_testbed(self):
        """Create cluster resources and clients for the testcase
        """

        self.log.info("Deleting testbed if it already exists.")
        self.delete_testbed()

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

        # Commenting out service, secret, configmap since they are conflicting across multiple apps
        # Will enable when we have support for restore of conflicting resources

        # # Create Service
        # svc_name = self.testbed_name + '-svc'
        # self.kubehelper.create_cv_svc(svc_name, self.namespace)
        #
        # # Creating test pod
        # secret_name = self.testbed_name + '-secret'
        # config_name = self.testbed_name + '-cm'
        # self.kubehelper.create_cv_secret(secret_name, self.namespace)
        # self.kubehelper.create_cv_configmap(config_name, self.namespace)

        # Create 5 PVC and Pods
        for i in range(1, 6):
            # Creating PVC
            pvc_name = self.testbed_name + '-pvc-' + str(i)
            self.kubehelper.create_cv_pvc(pvc_name, self.namespace, storage_class=self.storageclass)

            pod_name = self.testbed_name + '-pod-' + str(i)
            self.kubehelper.create_cv_pod(
                # pod_name, self.namespace, secret=secret_name, configmap=config_name, pvc_name=pvc_name
                pod_name, self.namespace, pvc_name=pvc_name
            )
            self.content.append(f"{self.namespace}/{pod_name}")
            time.sleep(30)

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

        # Modifying subclient properties to decrease device streams and populate proxy list
        subclient_props = {'vsaSubclientProp': {
            "proxies": {
                "memberServers": [{
                    "client": {
                        "clientName": self.access_node
                    }
                }]
            }
        }, "commonProperties": {"numberOfBackupStreams": 1}}

        self.log.info("Updating subclient properties of app group to decrease device streams and populate proxy list")
        self.subclient.update_properties(subclient_props)
        self.subclient.refresh()
        self._subclient = self.backupset.subclients.get(self.subclientName)

    def setup(self):
        """
        Setup the Testcase
        """
        try:
            self.init_inputs()
            self.create_testbed()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def delete_testbed(self):
        """
        Delete the generated testbed
        """

        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)

        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)

    def create_data(self):
        """Create test data in all pods
        """
        for pod in self.kubehelper.get_namespace_pods(self.namespace):
            self.log.info(f"Creating random data in {pod}")
            self.kubehelper.create_random_cv_pod_data(pod, self.namespace)
            time.sleep(10)

    @TestStep()
    def verify_suspend_resume(self, backup_type="FULL"):
        """Verify backup job
            Args:
                backup_type     (str)       -- Type of backup job to run (FULL/INCREMENTAL/SYNTH_FULL)
        """

        VirtualServerUtils.decorative_log(f"Verify Suspend/Resume of {backup_type} Backup Job")
        job_obj = self.subclient.backup(backup_level="FULL")
        self.job_mgr_obj = JobManager(_job=job_obj, commcell=self.commcell)

        self.log.info(f"Launched FULL Backup Job to validate for Job Suspend and Resume. Job ID : {job_obj.job_id}")

        self.log.info("Waiting for Job Progress to reach above 20%")
        self.job_mgr_obj.wait_for_job_progress(percent_complete=20)
        self.interruption_helper = Interruption(job_obj.job_id, self.commcell)
        self.interruption_helper.suspend_resume_job()

        self.log.info("Waiting for Job Progress to reach above 40%")
        self.job_mgr_obj.wait_for_job_progress(percent_complete=40)
        self.interruption_helper.suspend_resume_job()

        self.log.info("Job has been resumed. Waiting for job completion.")
        self.job_mgr_obj.wait_for_state()
        self.log.info("Backup job completed successfully")

        # Validate cleanup of CV resources
        self.kubehelper.validate_cv_resource_cleanup(self.namespace, backup_jobid=job_obj.job_id)

    @TestStep()
    def verify_restore_step(self, inplace=False):
        """Verify Restore Step
        """
        VirtualServerUtils.decorative_log(f"Verify Full Application {'In-place' if inplace else 'OOP'} restore")

        self.kubehelper.run_restore_validate(
            self.clientName,
            self.storageclass,
            inplace=inplace
        )

        # Validate CV resources cleanup
        ns = self.namespace if inplace else self.restore_namespace
        self.kubehelper.validate_cv_resource_cleanup(ns, restore_jobid=-1)

        # Validate all resources are restored correctly
        VirtualServerUtils.decorative_log("Validate all resources are restored correctly")

        namespace_resources = self.kubehelper.get_all_resources(self.namespace)

        restore_namespace_resources = self.kubehelper.get_all_resources(
            self.namespace if inplace else self.restore_namespace
        )

        self.kubehelper.validate_data(namespace_resources, restore_namespace_resources)

    @TestStep()
    def kill_job_validate(self):
        """Kill a backup job and validate cleanup
        """
        job = self.subclient.backup(backup_level="FULL")
        VirtualServerUtils.decorative_log(f"Launched FULL Backup Job to validate for Job Kill. Job ID : {job.job_id}")

        self.job_mgr_obj = JobManager(_job=job, commcell=self.commcell)
        self.interruption_helper = Interruption(job.job_id, self.commcell)
        self.interruption_helper.wait_for_job_run()

        self.log.info("Job is in Running state. Killing Job...")
        job.kill(wait_for_job_to_kill=True)
        self.job_mgr_obj.wait_for_state("killed")

        self.log.info("Validating resource cleanup after KILLED job...")
        self.kubehelper.validate_cv_resource_cleanup(self.namespace, backup_jobid=job.job_id)

    @TestStep()
    def commit_job_validate(self):
        """Commit a job and validate cleanup
        """
        job = self.subclient.backup(backup_level="FULL")
        VirtualServerUtils.decorative_log(f"Launched FULL Backup Job to validate for Job Kill. Job ID : {job.job_id}")

        self.job_mgr_obj = JobManager(_job=job, commcell=self.commcell)
        self.interruption_helper = Interruption(job.job_id, self.commcell)
        self.interruption_helper.wait_for_job_run()

        self.log.info("Waiting for Job Progress to reach above 20%")
        self.job_mgr_obj.wait_for_job_progress(percent_complete=20)

        self.log.info("Job is in Running state. Committing Job...")
        job.kill()
        self.job_mgr_obj.wait_for_state(expected_state='committed')
        self.log.info("Validating resource cleanup after COMMITTED job...")
        self.kubehelper.validate_cv_resource_cleanup(self.namespace, backup_jobid=job.job_id)

    @TestStep()
    def validate_restart_services_restore(self):
        """Validate RESTORE with start and stop services and validate cleanup and checksum"""
        proxy_obj = self.commcell.clients.get(self.access_node)

        browse_output = self.subclient.browse()
        source_paths = []
        for path in browse_output[0]:
            source_paths.append(path.strip("\\"))
        self.log.info(f"Applications to restore: [{str(source_paths)}]")

        restore_vm_names = {}
        for source_path in source_paths:
            restore_vm_names[source_path] = source_path

        job = self.subclient.full_app_restore_out_of_place(
            apps_to_restore=source_paths,
            restored_app_name=restore_vm_names,
            kubernetes_client=self.clientName,
            storage_class=self.storageclass,
            restore_namespace=self.restore_namespace,
            overwrite=True
        )
        self.log.info("Started restore out of place job with job id: %s", str(job.job_id))

        self.interruption_helper = Interruption(job.job_id, self.commcell)
        self.interruption_helper.wait_for_job_run()

        self.log.info(f"Restarting service on access node {self.access_node}")
        proxy_obj.restart_services(implicit_wait=120, timeout=60)

        self.log.info("Wait for all restore jobs to complete")
        self.interruption_helper.wait_and_resume()

        self.job_mgr_obj = JobManager(_job=job, commcell=self.commcell)
        self.job_mgr_obj.wait_for_state()
        self.log.info("All restore jobs completed.")

        self.log.info("Validating resource cleanup after Service RESTART...")
        self.kubehelper.validate_cv_resource_cleanup(self.restore_namespace, restore_jobid=-1)

        resources_namespace = self.kubehelper.get_all_resources(self.namespace)
        resources_restore_namespace = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(resources_namespace, resources_restore_namespace)

        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)

    @TestStep()
    def validate_restart_services_backup(self):
        """Validate BACKUP with start and stop services and validate cleanup and restore
        """

        proxy_obj = self.commcell.clients.get(self.access_node)

        job = self.subclient.backup(backup_level="INCREMENTAL")
        VirtualServerUtils.decorative_log(
            f"Launched INC Backup Job to validate for Service Restart. Job ID : {job.job_id}"
        )
        self.log.info("Waiting for Job Progress to reach above 20%")
        self.job_mgr_obj.wait_for_job_progress(percent_complete=20)

        self.interruption_helper = Interruption(job.job_id, self.commcell)
        self.interruption_helper.wait_for_job_run()

        self.log.info(f"Restarting service on access node {self.access_node}")
        proxy_obj.restart_services(implicit_wait=120, timeout=60)
        self.log.info("Restart operation succeeded. Waiting for jobs to go to running...")
        self.interruption_helper.wait_and_resume()

        self.log.info("Jobs have resumed, waiting for jobs to complete...")
        self.job_mgr_obj = JobManager(_job=job, commcell=self.commcell)
        self.job_mgr_obj.wait_for_state()

        self.log.info("Validating resource cleanup after Service RESTART...")
        self.kubehelper.validate_cv_resource_cleanup(self.namespace, backup_jobid=job.job_id)

        # Verify files are backed up correctly by restore validation
        self.verify_restore_step()

    @TestStep()
    def restore_job_suspend(self):
        """Suspend and resume a restore job
        """

        self.log.info("Run FULL backup before Restore suspend step.")
        self.kubehelper.backup("FULL")

        browse_output = self.subclient.browse()
        source_paths = []
        for path in browse_output[0]:
            source_paths.append(path.strip("\\"))
        self.log.info(f"Applications to restore: [{str(source_paths)}]")

        restore_vm_names = {}
        for source_path in source_paths:
            restore_vm_names[source_path] = source_path

        job = self.subclient.full_app_restore_out_of_place(
            apps_to_restore=source_paths,
            restored_app_name=restore_vm_names,
            kubernetes_client=self.clientName,
            storage_class=self.storageclass,
            restore_namespace=self.restore_namespace,
            overwrite=True
        )
        self.log.info("Started restore out of place job with job id: %s", str(job.job_id))

        self.interruption_helper = Interruption(job.job_id, self.commcell)
        self.interruption_helper.wait_for_job_run()

        self.log.info("Suspending Job...")
        self.interruption_helper.suspend_resume_job()

        self.job_mgr_obj = JobManager(_job=job, commcell=self.commcell)
        self.job_mgr_obj.wait_for_state()
        self.log.info("Successfully finished restore job")

        self.kubehelper.validate_cv_resource_cleanup(self.namespace, restore_jobid=job.job_id)

        resources_before_backup = self.kubehelper.get_all_resources(self.namespace)

        resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(resources_before_backup, resources_after_restore)

        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)

    @TestStep()
    def kill_restore_job_validate(self):
        """Kill a restore job and validate cleanup
        """

        browse_output = self.subclient.browse()
        source_paths = []
        for path in browse_output[0]:
            source_paths.append(path.strip("\\"))
        self.log.info(f"Applications to restore: [{str(source_paths)}]")

        restore_vm_names = {}
        for source_path in source_paths:
            restore_vm_names[source_path] = source_path

        job_list = []
        job = self.subclient.full_app_restore_out_of_place(
            apps_to_restore=source_paths,
            restored_app_name=restore_vm_names,
            kubernetes_client=self.clientName,
            storage_class=self.storageclass,
            restore_namespace=self.restore_namespace,
            overwrite=True
        )
        self.log.info("Started restore out of place job with job id: %s", str(job.job_id))
        job_list.append(job)

        self.job_mgr_obj = JobManager(_job=job, commcell=self.commcell)
        self.interruption_helper = Interruption(job.job_id, self.commcell)
        self.interruption_helper.wait_for_job_run()
        time.sleep(20)
        self.log.info(f"Killing the restore job {job.job_id}...")
        job.kill(wait_for_job_to_kill=True)
        self.job_mgr_obj.wait_for_state('killed')

        self.log.info(f"Job {job.job_id} has been killed. Verifying cleanup...")
        self.kubehelper.validate_cv_resource_cleanup(self.restore_namespace, restore_jobid=job.job_id)

        self.log.info("All restore jobs completed.")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Run Full Job and suspend/resume
            self.create_data()
            self.verify_suspend_resume(backup_type="FULL")
            # Validate files with restore
            self.verify_restore_step()

            # Restart Services on Proxy and validate cleanup
            self.validate_restart_services_backup()

            # Validate Kill job and cleanup
            self.kill_job_validate()

            # Validate Commit job and cleanup
            self.commit_job_validate()
            # Validate files with restore
            self.verify_restore_step()

            # Validate Restore job Suspend/Resume
            self.restore_job_suspend()

            # Validate Kill restore job and validate cleanup
            self.kubehelper.backup("FULL")
            self.kill_restore_job_validate()

            # Validate Restore job restart proxy
            self.validate_restart_services_restore()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

    def tear_down(self):
        self.log.info("Step -- Delete testbed, delete client ")
        self.delete_testbed()
