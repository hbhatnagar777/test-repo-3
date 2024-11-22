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

    create_tenant()                     --  Create new tenant

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    run()                               --  Run function of this test case
"""

import time

from kubernetes import client
from kubernetes import config as k8s_config_loader
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Kubernetes.KubernetesHelper import KubernetesHelper
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

constants = config.get_config()


class TestCase(CVTestCase):
    test_step = TestStep()

    """
    Testcase to create new Tenant, Add cluster and Application Group, perform Backup and Restore validation.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Create new tenant
    4. Login to Adminconsole ,Configure new Cluster and Application Group
    5. create cluster and application with snap enabled
    6. Verify Full Backup Job
    7. Run Inplace Full App restore
    8. Run Out of place  Full App restore
    9. Run Manifest restore
    10. Run volume k8s restore 
    11. Verify Incremental Backup Job
    12. Verify Full Application Out-of-place Restore
    13. Deactivate and Delete tenant
    14. Cleanup testbed
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes Intellisnap command center Acceptance"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.company_name = None
        self.tenant_user_name = None
        self.tenant_password = None
        self.k8s_server_name = None
        self.k8s_helper = None
        self.k8s_application_group_name = None
        self.k8s_server_endpoint = None
        self.k8s_sa_token = None
        self.k8s_sa = None
        self.access_node = None
        self.namespace = None
        self.restore_namespace = None
        self.testbed_name = None
        self.tcinputs = {
            "configFile": None
        }

        self.k8s_config = None
        self.path_to_kubeconfig = None
        self.driver = None
        self.core_v1_api = None
        self.plan = None
        self.k8s_storage_class = None
        self.hub_management = None

    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.log.info("Initializing Inputs for testcase")
        self.testbed_name = "k8s-auto-{}-{}".format(int(time.time()), self.id)
        self.namespace = self.testbed_name
        self.restore_namespace = self.namespace + "-rst"
        self.k8s_server_name = self.testbed_name
        self.k8s_application_group_name = self.testbed_name + "-app-grp"
        self.k8s_sa = self.testbed_name + "-sa"
        self.path_to_kubeconfig = self.tcinputs["configFile"]
        self.k8s_storage_class = self.tcinputs.get("StorageClass", None)
        self.k8s_application_group_name = "automated_K8s_application_group"

        # Initialize variables with values for new plan
        self.plan = "-".join([self.testbed_name, "plan"])


    def load_kubeconfig_file(self):
        """
        Load Kubeconfig file and connect to the Kubernetes API Server
        """
        self.log.info(f"Loading kubeconfig file from location {self.path_to_kubeconfig}")
        self.k8s_config = client.configuration.Configuration()
        k8s_config_loader.load_kube_config(self.path_to_kubeconfig, client_configuration=self.k8s_config)

        self.k8s_server_endpoint = self.k8s_config.host
        k8s_config_loader.load_kube_config(self.path_to_kubeconfig)

        # Initialize the CoreV1Api object
        self.core_v1_api = client.CoreV1Api()

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

        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.create_cv_serviceaccount(self.core_v1_api, self.k8s_sa, sa_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.create_cv_clusterrolebinding(client, crb_name, self.k8s_sa, sa_namespace)

        time.sleep(30)

        self.k8s_sa_token = self.kubehelper.get_serviceaccount_token(self.core_v1_api, self.k8s_sa, sa_namespace)

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.core_v1_api, client, self.namespace)

        # Creating namespace for restore if not exists
        self.kubehelper.create_cv_namespace(self.core_v1_api, client, self.restore_namespace)

        # Creating PVC
        pvc_name = self.testbed_name + '-pvc'
        self.kubehelper.create_cv_pvc(self.core_v1_api, pvc_name, self.namespace, storage_class=self.k8s_storage_class)

        # Creating test pod
        pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(self.core_v1_api, pod_name, self.namespace, pvc_name)

        time.sleep(30)
        # Create random data in pod
        self.kubehelper.create_random_cv_pod_data(self.core_v1_api, pod_name, self.namespace)

        # Creating PVC
        pvc_name = self.testbed_name + '-pvc'
        self.kubehelper.create_cv_pvc(self.core_v1_api, pvc_name, self.restore_namespace,
                                      storage_class=self.k8s_storage_class)

    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        self.kubehelper.delete_cv_namespace(self.core_v1_api, self.namespace)
        self.kubehelper.delete_cv_namespace(self.core_v1_api, self.restore_namespace)

        crb_name = self.testbed_name + '-crb'

        # Delete cluster role binding
        self.kubehelper.delete_cv_clusterrolebinding(client, crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(self.core_v1_api, sa_name=self.k8s_sa, sa_namespace=sa_namespace)


    @test_step
    def setup(self):
        """
         Load Kubeconfig, create testbed, launch browser and login
        """
        try:
            self.log.info("Step -- Login to  browser and login to Metallic Hub")
            self.init_inputs()
            self.load_kubeconfig_file()
            self.log.info("Step -- Create testbed")
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.driver = self.browser.driver
            self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                     password=self._inputJSONnode['commcell']['commcellPassword'])
            self.admin_console.wait_for_completion()
            self.log.info("Step -- Connect to Kubernetes API Server using Kubeconfig File")
            self.kubehelper = KubernetesHelper(self)
            self.create_testbed()
            self.log.info("Step -- Launch browser and login to Metallic Hub")
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def wait_for_first_job_completion(self, job_obj):
        """
        Wait for first job completion after cluster creation
        """
        job_id = job_obj.get_job_id_by_subclient(self.k8s_application_group_name)
        job_details = job_obj.job_completion(job_id)
        self.log.info(f"Status of Job ID {job_id} : {job_details['Status']}")

    @test_step
    def run(self):
        """
        Run the Testcase - New K8s configuration, full backup job, inc backup job, out-of-place restore
        """
        try:

            self.init_tcinputs()
            self.k8s_helper = K8sHelper(self.admin_console, self)
            self.log.info("Step -- creating kubernetes cluster Kubernetes New Configuration")
            self.log.info("Step -- Add more data and verify FULL backup")
            self.kubehelper.create_random_cv_pod_data(
                self.core_v1_api, self.testbed_name + '-pod', self.namespace, foldername="FULL"
            )
            self.log.info("Step -- Running Full backup")
            self.k8s_helper.create_k8s_cluster(enablesnap=True)
            self.k8s_helper.verify_backup(backup_level=Backup.BackupType.FULL)

            # after full backup, manifest restore and verification
            self.k8s_helper.verify_manifest_restore_job()
            # after full backup, full application out of place restore
            # and verification
            self.k8s_helper.verify_fullapp_restore_job(inplace=False)
            self.kubehelper.k8s_verify_restore_files(
                self.core_v1_api, self.namespace, self.restore_namespace, self.testbed_name + '-pod'
            )
            self.k8s_helper.verify_fullapp_restore_job(inplace=True)
            self.kubehelper.k8s_verify_restore_files(
                self.core_v1_api, self.restore_namespace, self.namespace, self.testbed_name + '-pod'
            )
            # after full backup, Volume  restore and verification
            self.k8s_helper.verify_volumedata_restore_job(inplace=False)
            time.sleep(60)
            pvc_src = (self.kubehelper.get_namespace_pvcs(self.core_v1_api, self.namespace)).sort()
            pvc_dst = (self.kubehelper.get_namespace_pvcs(self.core_v1_api, self.restore_namespace)).sort()
            if pvc_src == pvc_dst:
                self.log.info("Volume Restore successful")
            else:
                self.log.info("Volume Restore Failed")

            self.log.info("Step -- Add more data and verify INCR backup")
            self.kubehelper.create_random_cv_pod_data(
                self.core_v1_api, self.testbed_name + '-pod', self.namespace, foldername="INCR"
            )
            self.k8s_helper.verify_backup(backup_level=Backup.BackupType.INCR)
            # after INCR  backup, manifest restore and verification
            self.k8s_helper.verify_manifest_restore_job()
            # after INCR backup, full application out of place restore
            # and verification
            self.k8s_helper.verify_fullapp_restore_job(inplace=False)
            self.kubehelper.k8s_verify_restore_files(
                self.core_v1_api, self.namespace, self.restore_namespace, self.testbed_name + '-pod'
            )
            self.k8s_helper.verify_fullapp_restore_job(inplace=True)
            self.kubehelper.k8s_verify_restore_files(
                self.core_v1_api, self.restore_namespace, self.namespace, self.testbed_name + '-pod'
            )
            # after INCR backup, Volume  restore and verification
            self.k8s_helper.verify_volumedata_restore_job(inplace=False)
            time.sleep(60)
            pvc_src = (self.kubehelper.get_namespace_pvcs(self.core_v1_api, self.namespace)).sort()
            pvc_dst = (self.kubehelper.get_namespace_pvcs(self.core_v1_api, self.restore_namespace)).sort()
            if pvc_src == pvc_dst:
                self.log.info("Volume Restore successful")
            else:
                self.log.info("Volume Restore Failed")
            # After jobs are successfully completed, delete cluster and plan
            self.log.info("Step -- Delete cluster and plan")
            k8s_utils = K8sHelper(self.admin_console, self)
            k8s_utils.delete_k8s_cluster()

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            Browser.close_silently(self.browser)

    @test_step
    def tear_down(self):
        """
        Teardown testcase - Delete testbed, deactivate and delete tenant
        """
        self.log.info("Step -- Delete testbed, deactivate and delete tenant")
        self.delete_testbed()

