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

    create_testbed()                    --  Create the testbed required for the testcase

    delete_testbed()                    --  Delete the testbed created

    create_tenant()                     --  Create new tenant

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    run()                               --  Run function of this test case
"""

import datetime
import time

from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Reports.utils import TestCaseUtils
from Kubernetes.KubernetesHelper import KubernetesHelper
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.Hub.constants import HubServices, VMKubernetesTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, InitStep

constants = config.get_config()


class TestCase(CVTestCase):
    test_step = TestStep()

    """
    Testcase to create new Tenant, Add cluster and Application Group, perform Backup and Restore validation.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Create new tenant
    4. Login to Metallic Hub, configure new Cloud Storage, Configure new Cluster and Application Group
    5. Verify Full Backup Job
    6. Verify Incremental Backup Job
    7. Verify Full Application Out-of-place Restore
    8. Deactivate and Delete tenant
    9. Cleanup testbed
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Metallic VM Kubernetes Acceptance"
        self.utils = TestCaseUtils(self)
        self.admin_console = None
        self.browser = None
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.accessnode = None
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
        self.tcinputs = {
            "ConfigFile": None,
            "MetallicRingName": None
        }
        self.k8s_config = None
        self.driver = None
        self.plan = None
        self.storageclass = None
        self.kubehelper = None
        self.content = []
        self.filter = []
        self.util_namespace = None
        self.k8s_hub = None
        self.backup_job_id = None
        self.ring_name = None
        self.company_name = None
        self.hub_management = None
        self.tenant_user_name = None
        self.is_metallic = True
        self.hub_dashboard = None
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
        self.plan = "{}-plan".format(self.testbed_name)
        self.k8s_config = self.tcinputs['ConfigFile']
        self.util_namespace = self.testbed_name + '-utils'
        self.content = [self.namespace]
        self.filter = []

        self.tcinputs.update({
            "cloudStorageAccount": self.tcinputs.get("StorageAccountType", "Metallic Recovery Reserve"),
            "cloudStorageProvider": self.tcinputs.get("StorageVendorType", "Azure Blob Storage"),
            "cloudStorageRegion": self.tcinputs.get("StorageRegion", "East US 2"),
            "secondaryCloudStorageAccount": self.tcinputs.get(
                "SecondaryStorageAccountType", "Metallic Recovery Reserve"
            ),
            "optNewPlan": self.plan,
            "oneMonthPlan": True
        })

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

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

        # Create service account if doesn't exist

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

        self.kubehelper.create_cv_pvc(self.pvc_name, self.namespace, storage_class=self.storageclass)
        self.kubehelper.create_cv_pod(self.pod_name, self.namespace, pvc_name=self.pvc_name)

        # Create random data in pod
        self.kubehelper.create_random_cv_pod_data(self.pod_name, self.namespace)

    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)
        self.kubehelper.delete_cv_namespace(self.util_namespace)

        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

    @InitStep(msg="Create new tenant")
    def create_tenant(self):
        """
        Create a new tenant for the automation
        """

        self.ring_name = self.tcinputs["MetallicRingName"]
        if len(self.ring_name.split(".")) == 1:
            self.ring_name += ".metallic.io"
        self.company_name = datetime.datetime.now().strftime("K8s-Automation-%d-%B-%H-%M")
        user_firstname = "k8s" + str(int(time.time()))
        user_lastname = "user"
        user_email = user_firstname + user_lastname + '@domain.com'
        user_phonenumber = '00000000'
        user_country = self.tcinputs.get("UserCountry", "United States")

        self.log.info(f"Creating Tenant with Company name {self.company_name}")

        self.hub_management = HubManagement(
            testcase_instance=self,
            commcell=self.ring_name
        )

        # Create a tenant and get password that is returned
        self.tenant_user_name = self.hub_management.create_tenant(
            company_name=self.company_name,
            email=user_email,
            first_name=user_firstname,
            last_name=user_lastname,
            phone_number=user_phonenumber,
            country=user_country
        )

    @test_step
    def setup(self):
        """
        Setup the Testcase - Create new tenant, Load Kubeconfig, create testbed, launch browser and login
        """
        self.log.info("Step -- Create New tenant")
        self.create_tenant()
        self.init_inputs()

        self.log.info("Step -- Create testbed")
        self.create_testbed()

        self.log.info("Step -- Launch browser and login to Metallic Hub")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.ring_name
        )

        self.driver = self.browser.driver
        self.admin_console.login(
            username=self.tenant_user_name,
            password=constants.Metallic.tenant_password,
            stay_logged_in=True
        )

    @test_step
    def navigate_to_hub(self):
        """Navigate Metallic Hub and select Kubernetes New Configuration"""

        self.hub_dashboard = Dashboard(self.admin_console, HubServices.vm_kubernetes, VMKubernetesTypes.kubernetes)
        self.hub_dashboard.click_get_started()
        self.hub_dashboard.choose_service_from_dashboard()
        self.hub_dashboard.click_new_configuration()
        self.hub_dashboard.request_to_trial()

    @test_step
    def configure_cluster_from_hub(self):
        """Configure Kubernetes cluster from Hub"""

        self.k8s_helper = K8sHelper(self.admin_console, self)
        self.k8s_helper.configure_new_kubernetes_cluster(
            deployment_method="AKS",
            api_endpoint=self.api_server_endpoint,
            cluster_name=self.server_name,
            authentication=self.authentication,
            service_account=self.serviceaccount,
            service_token=self.servicetoken,
            app_group_name=self.app_grp_name,
            backup_content=self.content,
            filter_content=self.filter,
            get_first_plan=False
        )
        self.__cluster_created = True

    @test_step
    def run_backup_step(self):
        """Run FULL Backup Step"""
        # Navigate to Kubernetes Clusters and refresh the page

        self.admin_console.navigator.navigate_to_kubernetes()
        self.admin_console.navigator.navigate_to_k8s_clusters()
        self.k8s_helper.run_backup_job(
            cluster_name=self.server_name, app_group_name=self.app_grp_name, backup_level="Full"
        )

    @test_step
    def run_inc_backup(self):
        """Run INCREMENTAL Backup step"""

        self.admin_console.navigator.navigate_to_kubernetes()
        self.admin_console.navigator.navigate_to_k8s_clusters()
        self.admin_console.refresh_page()
        self.kubehelper.create_random_cv_pod_data(self.pod_name, self.namespace)
        self.k8s_helper.run_backup_job(
            cluster_name=self.server_name, app_group_name=self.app_grp_name, backup_level="Incremental"
        )

        # Verify protected data sources are updated
        self.hub_dashboard.go_to_dashboard()
        protected_data_count = self.k8s_helper.get_k8s_protected_data_sources()
        self.log.info(f"Protected Data Sources after backup : [{protected_data_count}]")
        if protected_data_count != 2:
            raise CVTestStepFailure("Protected data source count is not correct")
        self.hub_dashboard.choose_service_from_dashboard()
        self.hub_dashboard.go_to_admin_console()

    @test_step
    def run_full_app_restore(self):
        """Run Full Application Restore Step"""

        self.k8s_helper.run_fullapp_restore_job(
            cluster_name=self.server_name,
            app_group_name=self.app_grp_name,
            restore_namespace=self.restore_namespace,
            unconditional_overwrite=True
        )
        self.kubehelper.k8s_verify_restore_files(self.namespace, self.restore_namespace)

    @test_step
    def delete_cluster(self):
        """Delete cluster step"""
        self.k8s_helper.delete_k8s_cluster(self.server_name)

    @test_step
    def delete_plan(self):
        """Delete Plan step"""

        plan_obj = Plans(self.admin_console)
        self.admin_console.navigator.navigate_to_plan()
        plan_obj.delete_plan(self.plan)

    def run(self):
        """
        Run the Testcase - New K8s configuration, full backup job, inc backup job, out-of-place restore
        """
        try:
            # Step 1 - Navigate to Hub and kubernetes configuration step
            self.navigate_to_hub()

            # Step 2 - Select AKS Flow and configure cloud step
            self.configure_cluster_from_hub()

            # Step 3 - Run FULL Backup step
            self.run_backup_step()

            # Step 4 - Run INC Backup Step
            self.run_inc_backup()

            # Step 5 - Run FULL App Restore Step
            self.run_full_app_restore()

            # Step 7 - Delete Plan Step
            self.delete_plan()

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            if self.__cluster_created:
                # Step 6 - Delete Cluster Step
                try:
                    self.delete_cluster()
                except Exception as error:
                    self.utils.handle_testcase_exception(error)

    def tear_down(self):
        """Cleanup testbed - tenant, cluster, namespaces
        """
        Browser.close_silently(self.browser)
        self.delete_testbed()
        self.hub_management.deactivate_tenant()
        self.hub_management.delete_tenant()
