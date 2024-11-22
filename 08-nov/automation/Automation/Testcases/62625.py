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
    Testcase to Add cluster and Application Group, perform NS level Backup and Restore validation.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Login to Command Center, Configure new Cluster and Application Group
    4. Create cluster and application group
    5. Verify Full NS level Backup Job
    6. Verify NS level OOP restore Job
    7. Verify Incremental Backup Job
    8. Verify NS Level IP restore Job
    9. Cleanup testbed
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes Command Center Acceptance - Namespace and cluster level Backup and Restore validation"
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

    @InitStep(msg="Create orphan resources on cluster")
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

    @InitStep(msg="Create testbed resources on cluster")
    def create_testbed(self):
        """
            Create testbed resources
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

        pvc_pod_name = self.testbed_name + '-podpvc'
        self.kubehelper.create_cv_pvc(pvc_pod_name, self.namespace, storage_class=self.storageclass)
        self.pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(
            self.pod_name, self.namespace, secret=secret_name, configmap=config_name, pvc_name=pvc_pod_name
        )
        time.sleep(30)

        # Creating test statefulset
        sts_name = self.testbed_name + '-sts'
        self.kubehelper.create_cv_statefulset(sts_name, self.namespace)
        time.sleep(60)

        # Creating test deployment
        pvc_deployment_name = self.testbed_name + '-deploypvc'
        self.kubehelper.create_cv_pvc(pvc_deployment_name, self.namespace, storage_class=self.storageclass)
        deployment_name = self.testbed_name + '-deployment'
        self.kubehelper.create_cv_deployment(deployment_name, self.namespace, pvc_deployment_name)

        # Create orphan resources in the namespace
        self.create_orphan_resources()
        orphan_sa_2 = self.testbed_name + '-orphan-sa2'
        orphan_crb = self.testbed_name + '-orphan-crb'
        self.kubehelper.create_cv_serviceaccount(orphan_sa_2, self.namespace)
        self.kubehelper.create_cv_clusterrolebinding(orphan_crb, orphan_sa_2, self.namespace, 'view')

    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)

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
        self.__cluster_created = True
        self.log.info("Cluster and app group created.. Proceeding with next steps..")

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
    def run_namespace_level_restore(self, inplace=False):
        """Step -- Run Namespace level restore"""

        if inplace:
            self.log.info("THIS IS AN IN-PLACE RESTORE JOB")
        else:
            self.log.info("THIS IS AN OUT OF PLACE RESTORE JOB")
        self.k8s_helper.run_namespace_restore_job(
            cluster_name=self.clientName,
            app_group_name=self.app_grp_name,
            restore_namespace_map={self.namespace: self.restore_namespace},
            inplace=inplace,
            access_node=self.access_node,
            unconditional_overwrite=inplace,
            storage_class_map={self.storageclass: self.storageclass}
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.log.info("Comparing restored resources with original resources")
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.log.info("Validating checksum of restored and original files")
        if inplace:
            self.log.info('Namespace-level restore in-place step successfully completed')
        else:
            self.log.info('Namespace-level restore out-of-place step successfully completed')

    @test_step
    def delete_app_group(self):
        """Step 7 -- Delete Application Group"""
        self.k8s_helper.delete_k8s_app_grp(self.app_grp_name)

    @test_step
    def delete_cluster(self):
        """Step 8 -- Delete Cluster"""
        self.k8s_helper.delete_k8s_cluster(self.server_name)

    def run(self):
        """
        Run the Testcase - New K8s configuration, full backup job, inc backup job, out-of-place restore
        """
        try:
            # Step 1 & 2 - Create cluster &  application group with namespace as content
            self.create_cluster()

            # Step 3 - Run FULL Backup job
            self.run_full_backup()

            # Step 4 - Run Namespace level restore job
            self.run_namespace_level_restore()

            # Step 5 - Run INC Backup job
            self.run_inc_backup()

            # Step 6 - Run Full Application Restore
            self.run_namespace_level_restore(inplace=True)

            # Step 7 - Delete Application Group
            self.delete_app_group()

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:

            try:
                if self.__cluster_created:
                    # Step 4 - Delete cluster step
                    self.delete_cluster()

            except Exception as error:
                self.utils.handle_testcase_exception(error)

    def tear_down(self):
        """
            Teardown testcase - Delete testbed
        """
        Browser.close_silently(self.browser)
        self.delete_testbed()
