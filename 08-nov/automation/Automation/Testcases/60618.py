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
from Reports.utils import TestCaseUtils
from Kubernetes.KubernetesHelper import KubernetesHelper
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import TestStep, InitStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    test_step = TestStep()

    """
    Testcase to create new Tenant, Add cluster and Application Group, perform Backup and Restore validation.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Create new tenant
    4. Login to Command Center, Configure new Cluster and Application Group
    5. create cluster and application 
    6. Verify Full Backup Job
    7. Verify Incremental Backup Job
    8. Run Inplace Full App restore
    9. Run Out of place  Full App restore
    10. Deactivate and Delete tenant
    11. Cleanup testbed
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.restore_sc = None
        self.name = "Kubernetes Command Center Acceptance - Backup and Restore Full Application"
        self.utils = TestCaseUtils(self)
        self.admin_console = None
        self.browser = None
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.controller_id = None
        self.testbed_name = None
        self.namespace = None
        self.restore_namespace = None
        self.pod_name = None
        self.pvc_name = None
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
        self.util_namespace = None
        self.k8s_setup = None
        self.resources_before_backup = None
        self.resources_after_restore = None
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
        self.pod_name = self.testbed_name + "-pod"
        self.pvc_name = self.testbed_name + "-pvc"
        self.authentication = "Service account"
        self.subclientName = "automation-{}".format(self.id)
        self.clientName = "k8sauto-{}".format(self.id)
        self.server_name = self.clientName
        self.destclientName = "k8sauto-{}-dest".format(self.id)
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", automation_config.ACCESS_NODE)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        self.controller = self.commcell.clients.get(self.access_node)
        self.controller_id = int(self.controller.client_id)
        self.util_namespace = self.testbed_name + '-utils'
        self.content = [self.namespace]

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

        self.k8s_helper = K8sHelper(self.admin_console, self)

    @InitStep(msg="Create testbed resources on cluster")
    def create_testbed(self):
        """
            1. Create Service Account
            2. Create Cluster Role Binding
            3. Get SA token
            4. Create namespace and restore namespace
            5. Create PVC
            6. Create test Pod
            7. Generate random data in Pod
        """

        self.log.info("Creating cluster resources...")

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)
        self.kubehelper.create_cv_namespace(self.restore_namespace)

        # Create utils namespace to create service account
        self.kubehelper.create_cv_namespace(self.util_namespace)

        # Create service account if doesn't exist
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, self.util_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, self.util_namespace, cluster_role)

        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, self.util_namespace)

        self.kubehelper.create_cv_pvc(self.pvc_name, self.namespace, storage_class=self.storageclass)
        self.kubehelper.create_cv_pod(self.pod_name, self.namespace, pvc_name=self.pvc_name)

    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)
        self.kubehelper.delete_cv_namespace(self.util_namespace)

        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

    def setup(self):
        """
         Create testbed, launch browser and login
        """
        self.log.info("Step -- Launch browser and login to Command Center")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname
        )
        self.admin_console.login(
            username=self._inputJSONnode['commcell']['commcellUsername'],
            password=self._inputJSONnode['commcell']['commcellPassword']
        )
        self.admin_console.navigate(self.admin_console.base_url)
        self.init_inputs()
        self.create_testbed()

    @test_step
    def create_cluster(self):
        """Step 1 & 2 --  Create Cluster and app group from Command Center"""

        # Cleanup if cluster with same name exists from previous run
        # Step 0 - Cleanup previous cluster
        try:
            self.delete_cluster()
        except CVWebAutomationException as exp:
            self.log.info(exp)

        self.admin_console.navigator.navigate_to_kubernetes()
        self.k8s_helper.configure_new_kubernetes_cluster(
            api_endpoint=self.api_server_endpoint,
            cluster_name=self.server_name,
            authentication=self.authentication,
            service_account=self.serviceaccount,
            service_token=self.servicetoken,
            app_group_name=self.app_grp_name,
            backup_content=self.content,
            plan_name=self.plan,
            access_nodes=self.access_node
        )
        self.log.info("Cluster and app group created.. Proceeding with next steps..")
        self.__cluster_created = True

    @test_step
    def run_full_backup(self):
        """Step 3 -- Run FULL Backup for application group"""
        self.log.info("Creating test data..")
        self.kubehelper.create_random_cv_pod_data(self.pod_name, self.namespace, foldername="FULL")
        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.k8s_helper.run_backup_job(
            cluster_name=self.server_name,
            app_group_name=self.app_grp_name,
            backup_level="FULL"
        )
        self.log.info("FULL Backup complete.. Proceeding with next steps..")

    @test_step
    def run_inc_backup(self):
        """Step 4 -- Run INCREMENTAL Backup for application group"""
        self.log.info("Creating test data..")
        self.kubehelper.create_random_cv_pod_data(self.pod_name, self.namespace, foldername="INC")
        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.k8s_helper.run_backup_job(
            cluster_name=self.server_name,
            app_group_name=self.app_grp_name,
            backup_level="INCREMENTAL"
        )
        self.log.info("INCREMENTAL Backup complete.. Proceeding with next steps..")

    @test_step
    def run_full_app_restore(self):
        """Step 5 -- Run Full Application Restore"""

        self.k8s_helper.run_fullapp_restore_job(
            cluster_name=self.server_name,
            app_group_name=self.app_grp_name,
            restore_namespace=self.restore_namespace,
            unconditional_overwrite=True,
            access_node=self.access_node
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.log.info("Comparing restored resources with original resources")
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.log.info("Validating checksum of restored and original files")
        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)
        self.log.info("Full Application Restore complete.. Proceeding with next steps..")

    @test_step
    def run_full_app_ip_restore(self):
        """Step 6 -- Run Full Application Restore In-Place"""

        original_checksum = self.kubehelper.get_files_checksum(self.namespace)
        self.k8s_helper.run_fullapp_restore_job(
            cluster_name=self.server_name,
            app_group_name=self.app_grp_name,
            unconditional_overwrite=True,
            inplace=True
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.log.info("Comparing restored resources with original resources")
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.log.info("Validating checksum of restored and original files")
        restore_checksum = self.kubehelper.get_files_checksum(self.namespace)
        self.kubehelper.verify_checksum_dictionary(original_checksum, restore_checksum)
        self.log.info("Full Application Restore In-Place complete.. Proceeding with next steps..")

    @test_step
    def restore_across_sc(self):
        """
        Step 7 -- Run Full app restore OOP across StorageClass
        """

        # Get StorageClass List
        sc_list = self.kubehelper.get_all_storage_class_from_cluster()
        self.log.info(f"Found storage classes [{sc_list} on cluster]")
        sc_to_use = None
        sc_list.remove(self.storageclass)
        # Choosing non default sc from cluster
        if len(sc_list) >= 1:
            sc_to_use = sc_list[0]
            self.log.info(f"Expected SC is [{sc_to_use}]")

        if not sc_to_use:
            self.log.info("COULD NOT FIND ANOTHER SC TO USE. SKIPPING THIS STEP")
            return

        original_checksum = self.kubehelper.get_files_checksum(self.namespace)
        self.k8s_helper.run_fullapp_restore_job(
            cluster_name=self.server_name,
            app_group_name=self.app_grp_name,
            restore_namespace=self.restore_namespace,
            unconditional_overwrite=True,
            inplace=False,
            storage_class=sc_to_use
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.log.info("Comparing restored resources with original resources")
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.log.info("Validating checksum of restored and original files")
        restore_checksum = self.kubehelper.get_files_checksum(self.namespace)
        self.kubehelper.verify_checksum_dictionary(original_checksum, restore_checksum)
        self.log.info("Full Application Restore out of place complete.. Checking if the correct StorageClass was used")

        restored_pvc_manifest = self.kubehelper.get_all_resources(
            namespace=self.restore_namespace, return_json=True
        )['PersistentVolumeClaim'][0]

        if restored_pvc_manifest and restored_pvc_manifest.spec.storage_class_name == sc_to_use:
            self.log.info(f"Used correct StorageClass: {sc_to_use}")
        else:
            raise Exception(f"Incorrect Storage Class used : {restored_pvc_manifest.spec.storage_class_name}")

    @test_step
    def delete_app_group(self):
        """Step 8 -- Delete Application Group"""
        self.k8s_helper.delete_k8s_app_grp(self.app_grp_name)

    @test_step
    def delete_cluster(self):
        """Step 9 -- Delete Cluster"""
        self.k8s_helper.delete_k8s_cluster(self.server_name)

    def run(self):
        """
        Run the Testcase - New K8s configuration, full backup job, inc backup job, out-of-place restore
        """
        try:
            # Step 1 & 2 - Create cluster and app group
            self.create_cluster()

            # Step 3 - Run FULL Backup
            self.run_full_backup()

            # Step 4 - Run INC Backup
            self.run_inc_backup()

            # Step 5 - Run Full Application Restore
            self.run_full_app_restore()

            # Step 6 - Run Full Application Restore In-Place
            self.run_full_app_ip_restore()

            # Step 7 - Run Full Application restore In-place across storage classes
            self.restore_across_sc()

            # Step 8 - Delete Application Group
            self.delete_app_group()

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            try:
                # Step 9 - Delete Cluster
                if self.__cluster_created:
                    self.delete_cluster()

            except Exception as error:
                self.utils.handle_testcase_exception(error)

    def tear_down(self):
        """
        Teardown testcase - Delete testbed, deactivate and delete tenant
        """
        Browser.close_silently(self.browser)
        self.delete_testbed()
