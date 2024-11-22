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

    wait_for_first_job_completion()     --  Waits for completion of first job that is launched after cluster creation

    init_inputs()                       --  Initialize objects required for the testcase

    load_kubeconfig_file()              --  Load Kubeconfig file and connect to the Kubernetes API Server

    create_testbed()                    --  Create the testbed required for the testcase

    delete_testbed()                    --  Delete the testbed created

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    run()                               --  Run function of this test case

    add_app_grp_step()                  --  Perform add app group step in wizard

    add_cluster_step()                  --  Perform add cluster step in wizard

    delete_cluster_step()               --  Perform delete cluster step

    navigate_to_k8s_guided_setup()      --  Navigate to Kubernetes guided setup wizard

    select_plan_step()                  --  Perform select plan step in wizard

    summary_step()                      --  Vaildate summary step in wizard
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
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import TestStep, InitStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    test_step = TestStep()

    """
    Testcase for Kubernetes Guided setup.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Login to Adminconsole , Configure new Cluster and Application Group
    4. Create cluster and application group
    5. Delete cluster
    6. Cleanup testbed
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Commvault Complete for Kubernetes - Guided Setup"
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
        self.filter = []
        self.util_namespace = None
        self.getting_started_obj = None
        self.k8s_setup = None
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
        self.content = [
            f"Applications:Volumes:{self.namespace}/{self.pvc_name}",
            self.restore_namespace,
            f"{self.namespace}/{self.testbed_name + '-pod'}",
            f"Applications:Labels:{self.namespace}/k8s-automation=",
            f"Selector:Application:app=demo -n {self.restore_namespace}",
            f"Selector:Volumes:app=demo -n {self.namespace}",
            f"Selector:Namespaces:app=demo"
        ]
        self.filter = [
            self.util_namespace,
            f"Applications:Labels:{self.namespace}/k8s-automation=/{self.pod_name}"
        ]

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
        self.kubehelper.create_cv_pod(self.pod_name, self.namespace)

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
    def navigate_to_k8s_guided_setup(self):
        """Navigate to Guided Setup and Configure Kubernetes setup"""
        self.admin_console.navigator.navigate_to_getting_started()
        self.getting_started_obj.expand_solutions()
        self.getting_started_obj.configure_wizard_for_solution("Kubernetes")

    def delete_cluster_step(self):
        """Delete cluster and testbed step"""
        self.k8s_helper.delete_k8s_cluster(self.server_name)

    def run(self):
        """
        Run the Testcase - New K8s configuration, full backup job, inc backup job, out-of-place restore
        """
        try:
            # Cleanup if cluster with same name exists from previous run
            # Step -1 - Cleanup previous cluster
            try:
                self.delete_cluster_step()
            except CVWebAutomationException as exp:
                self.log.info(exp)

            # Step 0 : Configure new cluster form guided setup page
            self.navigate_to_k8s_guided_setup()

            # Step 1 - 6 : Complete create cluster wizard
            self.k8s_helper.configure_new_kubernetes_cluster(
                api_endpoint=self.api_server_endpoint,
                cluster_name=self.server_name,
                authentication=self.authentication,
                service_account=self.serviceaccount,
                service_token=self.servicetoken,
                access_nodes=self.access_node,
                app_group_name=self.app_grp_name,
                backup_content=self.content,
                filter_content=self.filter,
                plan_name=self.plan
            )
            self.__cluster_created = True

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            try:
                if self.__cluster_created:
                    # Step 7 - Delete cluster step
                    self.delete_cluster_step()

            except Exception as error:
                self.utils.handle_testcase_exception(error)

    def tear_down(self):
        """
            Teardown testcase - Delete testbed
        """
        Browser.close_silently(self.browser)
        self.delete_testbed()
