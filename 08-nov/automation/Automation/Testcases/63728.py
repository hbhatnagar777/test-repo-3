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
    Testcase to validate CRUD operations on cluster and App Groups.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Login to Command Center, Configure new Cluster and Application Group
    4. Create cluster and application group
    5. Verify Change AN on App Group
    6. Verify Change Plan on App Group
    7. Verify Change AN on cluster
    8. Cleanup testbed
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes Metallic CRUD operations"
        self.utils = TestCaseUtils(self)
        self.admin_console = None
        self.browser = None
        self.modified_access_node = None
        self.modified_plan = None
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
        self.modified_access_node = self.tcinputs.get("ModifiedAccessNode", None)
        self.modified_plan = self.tcinputs.get("ModifiedPlan", None)
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
    def change_app_group_access_node(self):
        """Step 3 -- Change Access Node on Application Group"""
        self.k8s_helper.change_access_node_on_app_grp(self.server_name, self.app_grp_name, self.modified_access_node)

    @test_step
    def change_app_group_plan(self):
        """Step 4 -- Change Plan on Application Group"""
        self.k8s_helper.change_plan_on_k8s_app_grp(self.server_name, self.app_grp_name, self.modified_plan)

    @test_step
    def change_cluster_access_node(self):
        """Step 5 -- Change Access Node on Cluster"""
        self.k8s_helper.change_access_node(self.server_name, self.modified_access_node, self.access_node)

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
        Run the Testcase - Verify CRUD operations
        """
        try:
            # Step 1 & 2 - Create cluster &  application group with namespace as content
            self.create_cluster()

            # Step 3 - Change Access Node on application group and verify
            self.change_app_group_access_node()
            # Step 4 - Change plan on application group and verify

            self.change_app_group_plan()
            # Step 5 - Change Access Node on Cluster and verify
            self.change_cluster_access_node()

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
