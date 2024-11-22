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

     _recalculate_lsr()                 --  Click on recalculate button on LSR

    _goto_lsr()                         --  Go to LSR page

    _goto_pvi()                         --  Go to page for PVI

    get_used_column_count()             --  Get the values of Used column

    validate_pvi()                      --  Validate the values of PVI table

    setup()                             --  setup method for test case

    tear_down()                         --  tear down method for testcase

    init_inputs()                       --  Initialize objects required for the testcase

    load_kubeconfig_file()              --  Load Kubeconfig file and connect to the Kubernetes API Server

    create_testbed()                    --  Create the testbed required for the testcase

    delete_testbed()                    --  Delete the testbed created

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    run()                               --  Run function of this test case
"""

import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import VirtualServerUtils
from Kubernetes.KubernetesHelper import KubernetesHelper
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    test_step = TestStep()

    """
    Testcase to create new Tenant, Add cluster and Application Group, perform Backup and Restore validation.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Create new tenant
    4. Login to Adminconsole , Configure new Cluster and Application Group
    5. Create cluster and application 
    6. Verify Full Backup Job
    7. Verify Incremental Backup Job
    8. Validate PVI table for FULL JOB
    9. Verify Synthetic Full Backup
    10. Verify Incrmental Backup job
    11. Validate PVI table for Synthetic Full job
    12. Delete cluster client
    13. Validate PVI after cluster deletion 
    14. Cleanup testbed
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes command center Acceptance"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
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
        self.agentName = "Virtual Server"
        self.instanceName = "Kubernetes"
        self.backupsetName = "defaultBackupSet"
        self.tcinputs = {}
        self.content = []
        self.k8s_config = None
        self.path_to_kubeconfig = None
        self.driver = None
        self.core_v1_api = None
        self.apps_v1_api = None
        self.plan = None
        self.storageclass = None
        self.kubehelper = None

        self.stateless_name = None
        self.stateful_name = None

        self.job_id1 = 0
        self.job_id2 = 0

    def __get_table_id(self, title):
        table_id = self.driver.find_element(
            By.XPATH, f"//div[contains(@class, 'reportstabletitle panel-table-title')]"
                      f"/span[contains(text(), '{title}')]/parent::div/.."
        ).get_attribute("id")
        self.log.info(f"Table ID [{table_id}] found for title [{title}]")
        return table_id

    def _recalculate_lsr(self):
        """Recalculate LSR report"""
        self.admin_console.select_hyperlink("Recalculate")
        time.sleep(60)
        self.admin_console.wait_for_completion()

    def _goto_lsr(self):
        """Go to License Summary Report page"""
        self.admin_console.navigator.navigate_to_reports()
        ManageReport(self.admin_console).access_report('License summary')
        self._recalculate_lsr()

    def _goto_pvi(self):
        """Go to the PVI table page"""
        license_name = "Virtual Operating Instances"
        table_name = "Commvault Complete OI Licenses"
        table_id = self.__get_table_id(table_name)
        self.admin_console.fill_form_by_id(f"{table_id}-search-input", license_name)
        self.admin_console.driver.find_element(By.ID, f"{table_id}-search-input").send_keys(Keys.ENTER)
        time.sleep(2)
        self.admin_console.driver.find_elements(
            By.XPATH, f"//div[@id='Kendo_{table_id}']//tr/td[@data-label='License']/a"
        )[0].click()

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
        self.server_name = "k8sauto-{}".format(self.id)
        self.destclientName = "k8sauto-{}-dest".format(self.id)
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", automation_config.ACCESS_NODE)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        self.controller = self.commcell.clients.get(self.access_node)
        self.controller_id = int(self.controller.client_id)

        self.stateful_name = self.testbed_name + '-stateful'
        self.stateless_name = self.testbed_name + '-stateless'

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

    def create_testbed(self):
        """
            1. Create Service Account
            2. Create Cluster Role Binding
            3. Get SA token
            4. Create namespace
            5. Create PVC
            6. Create test Pods
            7. Generate random data in Pod
        """

        # Create service account if doesn't exist

        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, sa_namespace)

        # Create cluster role binding and fetch service account token
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, sa_namespace, cluster_role)

        self.servicetoken = self.kubehelper.get_serviceaccount_token(
            self.serviceaccount, sa_namespace
        )

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)

        # Creating PVC
        pvc_name = self.testbed_name + '-pvc'
        self.kubehelper.create_cv_pvc(pvc_name, self.namespace, storage_class=self.storageclass)

        # Creating test stateless and stateful pods
        self.kubehelper.create_cv_pod(self.stateful_name, self.namespace, pvc_name=pvc_name)
        self.content.append(self.namespace + "/" + self.stateful_name)
        self.kubehelper.create_cv_pod(self.stateless_name, self.namespace)
        self.content.append(self.namespace + "/" + self.stateless_name)

    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        self.kubehelper.delete_cv_namespace(self.namespace)

        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(
            sa_name=self.serviceaccount, sa_namespace=sa_namespace
        )

    def get_used_column_count(self):
        """Get the value of Used column for Commvault Complete OI Licenses table"""

        license_name = "Virtual Operating Instances"
        table_name = "Commvault Complete OI Licenses"
        table_id = self.__get_table_id(table_name)
        self._recalculate_lsr()
        self.admin_console.fill_form_by_id(f"{table_id}-search-input", license_name)
        self.admin_console.driver.find_element(By.ID, f"{table_id}-search-input").send_keys(Keys.ENTER)
        time.sleep(2)
        return int(
            self.admin_console.driver.find_elements(
                By.XPATH, f"//div[@id='Kendo_{table_id}']//tr//td[@data-label='Used (instances)']"
            )[0].text
        )

    def validate_pvi_table(self):
        """Validate if data has been correctly populated in the PVI table"""
        self._goto_lsr()
        self._goto_pvi()
        license_name = "Current Virtual Operating Instances"
        table_id = self.__get_table_id(license_name)
        self.admin_console.fill_form_by_id(f"{table_id}-search-input", self.stateful_name)
        self.admin_console.driver.find_element(By.ID, f"{table_id}-search-input").send_keys(Keys.ENTER)
        time.sleep(2)

        table_xpath = f"//div[@id='Kendo_{table_id}']"
        headers = list(filter(
            None, [th.text for th in self.admin_console.driver.find_elements(By.XPATH, table_xpath + "//tr//th")]
            )
        )
        values = list(filter(
            None, [td.text for td in self.admin_console.driver.find_elements(By.XPATH, table_xpath + "//tr//td")]
            )
        )
        stateful_row_vals = dict(zip(headers, values))

        self.admin_console.fill_form_by_id(f"{table_id}-search-input", self.stateless_name)
        self.admin_console.driver.find_element(By.ID, f"{table_id}-search-input").send_keys(Keys.ENTER)
        time.sleep(2)
        headers = list(filter(
            None, [th.text for th in self.admin_console.driver.find_elements(By.XPATH, table_xpath + "//tr//th")]
            )
        )
        values = list(filter(
            None, [td.text for td in self.admin_console.driver.find_elements(By.XPATH, table_xpath + "//tr//td")]
            )
        )
        stateless_row_vals = dict(zip(headers, values))

        # Collect Job IDs from other table
        license_name = "Virtual Operating Instances - current usage details"
        table_id = self.__get_table_id(license_name)
        self.admin_console.fill_form_by_id(f"{table_id}-search-input", self.stateful_name)
        self.admin_console.driver.find_element(By.ID, f"{table_id}-search-input").send_keys(Keys.ENTER)
        time.sleep(2)

        table_xpath = f"//div[@id='Kendo_{table_id}']"
        headers = list(filter(
            None, [th.text for th in self.admin_console.driver.find_elements(By.XPATH, table_xpath + "//tr//th")]
            )
        )
        values = list(filter(
            None, [td.text for td in self.admin_console.driver.find_elements(By.XPATH, table_xpath + "//tr//td")]
            )
        )
        stateful_row_vals.update(dict(zip(headers, values)))

        self.admin_console.fill_form_by_id(f"{table_id}-search-input", self.stateless_name)
        self.admin_console.driver.find_element(By.ID, f"{table_id}-search-input").send_keys(Keys.ENTER)
        time.sleep(2)
        headers = list(filter(
            None, [th.text for th in self.admin_console.driver.find_elements(By.XPATH, table_xpath + "//tr//th")]
            )
        )
        values = list(filter(
            None, [td.text for td in self.admin_console.driver.find_elements(By.XPATH, table_xpath + "//tr//td")]
            )
        )
        stateless_row_vals.update(dict(zip(headers, values)))

        # Validate for stateless app
        if stateless_row_vals['VOI Type'] == 'K8s Stateless':
            self.log.info("Flag correct for Stateless application.")
        else:
            self.log.info("Flag incorrect for Stateless application")
            raise Exception(
                "Flag incorrect for Stateless application"
            )

        if self.job_id1 <= int(stateless_row_vals['Job ID']) < self.job_id2:
            self.log.info("Job ID correct for Stateless application.")
        else:
            self.log.info("Job ID incorrect for Stateless application")
            raise Exception(
                "Job ID incorrect for Stateless application"
            )

        # Validation for stateful application
        if stateful_row_vals['VOI Type'] == 'K8s Stateful':
            self.log.info("Flag correct for Stateful application.")
        else:
            self.log.info("Flag incorrect for Stateful application")
            raise Exception(
                "Flag incorrect for Stateful application"
            )

        if self.job_id1 <= int(stateful_row_vals['Job ID']) < self.job_id2:
            self.log.info("Job ID correct for Stateful application.")
        else:
            self.log.info("Job ID incorrect for Stateful application")
            raise Exception(
                "Job ID incorrect for Stateful application"
            )

    @test_step
    def setup(self):
        """
         Load Kubeconfig, create testbed, launch browser and login
        """
        try:
            self.log.info("Step -- Login to browser and navigate to admin console")
            self.init_inputs()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.driver = self.browser.driver
            self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                     password=self._inputJSONnode['commcell']['commcellPassword'])
            self.admin_console.wait_for_completion()
            self.create_testbed()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    @test_step
    def run(self):
        """
        Run the Testcase - New K8s configuration, full backup job, inc backup job, out-of-place restore
        """
        try:

            self.k8s_helper = K8sHelper(self.admin_console, self)
            VirtualServerUtils.decorative_log("Step -- Creating kubernetes cluster Kubernetes New Configuration")

            self.admin_console.navigator.navigate_to_kubernetes()
            self.k8s_helper.create_k8s_cluster(
                api_server=self.api_server_endpoint,
                name=self.server_name,
                authentication=self.authentication,
                username=self.serviceaccount,
                password=self.servicetoken,
                access_nodes=self.access_node
            )
            self.k8s_helper.add_application_group(
                cluster_name=self.server_name,
                app_group_name=self.app_grp_name,
                content=self.content,
                plan=self.plan
            )

            self.log.info("Getting initial values of PVI table from LSR...")
            self._goto_lsr()
            before = self.get_used_column_count()
            self.log.info(f"Used count = {before}")

            VirtualServerUtils.decorative_log("Step -- Running Full backup")
            self.job_id1 = int(self.k8s_helper.run_backup_job(
                cluster_name=self.server_name,
                app_group_name=self.app_grp_name,
                backup_level="FULL"
            ))

            VirtualServerUtils.decorative_log("Step -- Add more data and verify INCR backup")
            self.kubehelper.create_random_cv_pod_data(
                self.stateful_name, self.namespace, foldername="INCR"
            )
            self.job_id2 = int(self.k8s_helper.run_backup_job(
                cluster_name=self.server_name,
                app_group_name=self.app_grp_name,
                backup_level="INCREMENTAL"
            ))

            self.log.info("Getting final values of PVI table from LSR after backup jobs...")
            self._goto_lsr()
            after = self.get_used_column_count()
            self.log.info(f"Used count = {after}")

            if after - before == 2:
                self.log.info("PVI table Used count validation successful.")
            else:
                self.log.error("Incorrect Used count for PVI table")
                raise Exception(
                    "Incorrect Used count for PVI table"
                )

            self.validate_pvi_table()

            VirtualServerUtils.decorative_log("Step -- Verify SYNTHETIC FULL backup")
            self.job_id1 = int(self.k8s_helper.run_backup_job(
                cluster_name=self.server_name,
                app_group_name=self.app_grp_name,
                backup_level="SYNTHETIC_FULL"
            ))
            VirtualServerUtils.decorative_log("Step -- Verify INCREMENTAL backup")
            self.job_id2 = int(self.k8s_helper.run_backup_job(
                cluster_name=self.server_name,
                app_group_name=self.app_grp_name,
                backup_level="INCREMENTAL"
            ))
            self.validate_pvi_table()

            VirtualServerUtils.decorative_log("Step -- Delete Cluster and validate LSR")
            self.k8s_helper.delete_k8s_cluster(self.server_name)

            before = after
            self.log.info("Getting final values of PVI table from LSR after cluster deletion...")
            self._goto_lsr()
            after = self.get_used_column_count()
            self.log.info(f"Used count = {after}")

            if before - after == 2:
                self.log.info("PVI table Used count validation successful.")
            else:
                self.log.error("Incorrect Used count for PVI table")
                raise Exception(
                    "Incorrect Used count for PVI table"
                )

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            Browser.close_silently(self.browser)
            self.log.info("Step -- Delete testbed")
            self.delete_testbed()

    @test_step
    def tear_down(self):
        """
        Teardown
        """
        self.log.info("Testcase execution complete")
