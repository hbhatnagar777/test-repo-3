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

    run()                               --  Run function of this test case

    add_app_grp_step()                  --  Perform add app group step in wizard

    add_cluster_step()                  --  Perform add cluster step in wizard

    delete_cluster_step()               --  Perform delete cluster step

    enable_stateless_filter()           --  Enable stateless filter for application group from manage content

    run_backup_validate()               --  Run backup and validate expected applications are backed up

"""

import time

from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Kubernetes.KubernetesHelper import KubernetesHelper
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.Setup.getting_started import GettingStarted
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, InitStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    test_step = TestStep()

    """
    Testcase for Stateless Filter functionality validation from Manage Content 
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Login to Adminconsole , Configure new Cluster from Kubernetes Cluster page
    4. Create cluster and application group
    5. Enable stateless filter from Application Group manage content
    6. Run backup and validate expected applications are backed up
    7. Delete cluster
    8. Cleanup testbed
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Command Center automation to validate stateless application filter functionality"
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
        self.deploy_name = None
        self.sts_name = None
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
        self.expected_content = []
        self.util_namespace = None
        self.getting_started_obj = None
        self.k8s_setup = None
        self.job_obj = None
        self.__cluster_created = False
        self.validate_matrix = None

    @InitStep(msg="Load kubeconfig and initialize testcase variables")
    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.namespace = self.testbed_name
        self.restore_namespace = self.testbed_name + "-rst"
        self.app_grp_name = self.testbed_name + "-app-grp"
        self.serviceaccount = self.testbed_name + "-sa"
        self.pod_name = self.testbed_name + "-pod"
        self.deploy_name = self.testbed_name + "-deploy"
        self.sts_name = self.testbed_name + "-sts"
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
        self.expected_content = [self.namespace, self.sts_name]
        self.validate_matrix = {
                "Application name": [self.namespace, self.sts_name],
                "Type": ['Namespace', 'StatefulSet'],
                "Namespace": [self.namespace, self.namespace]
            }
        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

        self.k8s_helper = K8sHelper(self.admin_console, self)
        self.getting_started_obj = GettingStarted(self.admin_console)

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
        # Create utils namespace to create service account
        self.kubehelper.create_cv_namespace(self.util_namespace)

        # Create service account if doesn't exist
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, self.util_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, self.util_namespace, cluster_role)

        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, self.util_namespace)

        # Creating stateless pod
        self.kubehelper.create_cv_pod(self.pod_name, self.namespace)

        # Creating stateless deployment
        self.kubehelper.create_cv_deployment(self.deploy_name, self.namespace)

        # Creating statefulset
        self.kubehelper.create_cv_statefulset(self.sts_name, self.namespace)

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
        self.driver = self.browser.driver
        self.admin_console.login(
            username=self._inputJSONnode['commcell']['commcellUsername'],
            password=self._inputJSONnode['commcell']['commcellPassword']
        )
        self.admin_console.navigate(self.admin_console.base_url)

        self.init_inputs()
        self.create_testbed()

    @test_step
    def add_cluster_step(self):
        """Add cluster step of guided setup wizard"""
        self.k8s_helper.create_k8s_cluster(
            api_server=self.api_server_endpoint,
            name=self.server_name,
            authentication=self.authentication,
            username=self.serviceaccount,
            password=self.servicetoken,
            access_nodes=self.access_node
        )
        self.__cluster_created = True

    @test_step
    def add_app_grp_step_from_cluster(self):
        """Add application group step of guided setup wizard"""
        self.k8s_helper.add_app_group_from_cluster(
            cluster_name=self.server_name,
            app_group_name=self.app_grp_name,
            content=self.content,
            plan=self.plan
        )
        time.sleep(30)

    @test_step
    def delete_cluster_step(self):
        """Delete cluster and testbed step"""
        self.k8s_helper.delete_k8s_cluster(self.server_name)

    @test_step
    def enable_stateless_filter(self):
        """Enable toggle for stateless filter for application group"""
        self.k8s_helper.enable_stateless_filter(self.server_name, self.app_grp_name)
        # Validate Preview
        self.k8s_helper.validate_preview_content(
            self.server_name,
            self.app_grp_name,
            validate_matrix=self.validate_matrix
        )


    @test_step
    def run_backup_validate(self):
        """Run backup job and validate backed up applications
        """
        job_id = self.k8s_helper.run_backup_job(cluster_name=self.server_name, app_group_name=self.app_grp_name)
        self.job_obj = self.commcell.job_controller.get(job_id)
        child_job_jpr = self.kubehelper.get_child_job_error_reason(self.job_obj, print_log=True)
        applications = list(child_job_jpr.keys())

        assert sorted(applications) == sorted(self.expected_content), \
            f"Validation failed: Backup content does not match with expected content : " \
            f"Backup [{applications}] Expected [{self.expected_content}]"

    def run(self):
        """
        Run the Testcase - New K8s configuration, full backup job, inc backup job, out-of-place restore
        """
        try:

            # Step 1 - Add cluster step
            self.add_cluster_step()

            # Step 2 - Add application group step from cluster details
            self.add_app_grp_step_from_cluster()

            # Step 3 - Enable stateless filter for Application Group
            self.enable_stateless_filter()

            # Step 4 - Run Backup job and verify stateless apps are filtered
            self.run_backup_validate()

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            try:
                if self.__cluster_created:
                    # Step 5 - Delete cluster step
                    self.delete_cluster_step()

            except Exception as error:
                self.utils.handle_testcase_exception(error)

    def tear_down(self):
        """
            Teardown testcase - Delete testbed
        """
        Browser.close_silently(self.browser)
        self.delete_testbed()
