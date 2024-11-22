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

    add_cluster_step()                  --  Perform add cluster step in wizard

    delete_cluster_step()               --  Perform delete cluster step

    enable_etcd_step()                  --  Enables ETCD Protection on cluster

    perform_etcd_backup_step()          -- Performs a backup of ETCD

    check_cv_cleanup_step()             -- Validates CV Resource cleanup

    navigate_to_k8s_guided_setup()      --  Navigate to Kubernetes guided setup wizard

    select_plan_step()                  --  Perform select plan step in wizard

    summary_step()                      --  Validate summary step in wizard

    run_fs_dest_restore                 --  Performs FS Destination restore
"""

import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Kubernetes.exceptions import KubernetesException
from Reports.utils import TestCaseUtils
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes.KubernetesUtils import populate_default_objects
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, InitStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    test_step = TestStep()

    """
    Testcase for validate ETCD Backup and cleanup.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Login to Adminconsole , Configure new Cluster from Kubernetes Cluster page
    4. Create cluster
    5. Enable ETCD Protection
    6. Perform FULL ETCD Backup
    7. Validate CV Resource Cleanup from namespace
    8. Perform INCR ETCD Backup
    9. Validate CV Resource Cleanup from namespace
    10. Delete Cluster 
    11. Cleanup testbed
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.top_level_path = None
        self.name = "Kubernetes - Command Center automation to validate etcd protection"
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
        self.backup_job_id = None
        self.overview = None
        self.proxy_obj = None
        self.fs_destination_path = None
        self.__cluster_created = False

    @InitStep(msg="Load kubeconfig and initialize testcase variables")
    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.namespace = "kube-system"
        self.app_grp_name = self.testbed_name + "-app-grp"
        self.serviceaccount = self.testbed_name + "-sa"
        self.pod_name = self.testbed_name + "-pod"
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
        self.proxy_obj = Machine(self.controller)
        self.util_namespace = self.testbed_name + '-utils'
        self.content = []
        self.filter = []
        self.fs_destination_path = self.tcinputs.get("FsDestinationPath", "/tmp/") + self.testbed_name
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
            4. Create util namespace
        """

        self.log.info("Creating cluster resources...")

        # Create utils namespace to create service account
        self.kubehelper.create_cv_namespace(self.util_namespace)

        # Create service account if doesn't exist
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, self.util_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, self.util_namespace, cluster_role)

        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, self.util_namespace)

        # Creating test pod

    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        self.kubehelper.delete_cv_namespace(self.util_namespace)

        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)
        self.proxy_obj.remove_directory(self.fs_destination_path)

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
        """
        Add cluster step of guided setup wizard
        """
        self.k8s_helper.create_k8s_cluster(
            api_server=self.api_server_endpoint,
            name=self.server_name,
            authentication=self.authentication,
            username=self.serviceaccount,
            password=self.servicetoken,
            access_nodes=self.access_node
        )
        self.__cluster_created = True

    def delete_cluster_step(self):
        """
        Delete cluster and testbed step
        """
        self.k8s_helper.delete_k8s_cluster(self.server_name)

    @test_step
    def enable_etcd_step(self):
        """
        Step to enable ETCD Protection
        """
        self.k8s_helper.enable_etcd_protection(
            cluster_name=self.clientName,
            plan=self.plan
        )

    def perform_etcd_backup_step(self, backup_type="FULL"):
        """
        Step to perform ETCD Backup
        """
        self.k8s_helper.navigate_to_etcd(cluster_name=self.clientName)
        self.k8s_helper.run_backup_job(backup_level=backup_type)

    def check_cv_cleanup_step(self):
        """
        Step to validate CV Resource Cleanup
        """
        self.kubehelper.validate_cv_resource_cleanup(
            namespace=self.namespace, backup_jobid=self.backup_job_id
        )

        etcd_pods = self.kubehelper.get_namespace_pods(
            namespace=self.namespace,
            label_selector='component=etcd'
        )
        for etcd_pod in etcd_pods:
            hostpath_contents = self.kubehelper.list_pod_content(
                pod_name=etcd_pod,
                namespace=self.namespace,
                location='/var/lib/etcd'
            )
            if 'etcdsnapdir' in hostpath_contents:
                etcd_snapdir_contents = self.kubehelper.list_pod_content(
                    pod_name=etcd_pod,
                    namespace=self.namespace,
                    location='/var/lib/etcd/etcdsnapdir'
                )
                if len(etcd_snapdir_contents) != 0:
                    raise CVTestStepFailure(f"Hostpath content not cleaned up: {etcd_snapdir_contents}")

        self.log.info("Hostpath contents successfully cleaned up")

    def run_fs_dest_restore(self):
        """Run File System Destination Restore step for etcd application group"""

        self.proxy_obj.create_directory(self.fs_destination_path, force_create=True)

        # Get backed up data
        self.commcell.refresh()
        self._client = self.commcell.clients.get(self.server_name)
        populate_default_objects(self)
        self.subclient.refresh()
        self._subclient = self.backupset.subclients.get('etcd (system generated)')
        self.subclient.refresh()

        app_list, app_metadata = self.subclient.browse()
        etcd_uuid = app_metadata[app_list[0]]['snap_display_name']
        certs = self.subclient.browse(f"{etcd_uuid}\\etcd-certs")[0]

        data = self.subclient.browse(f"{etcd_uuid}\\etcd-data")[0]

        if len(certs) == 0:
            self.log.info("Certs folder empty")
        if len(data) == 0:
            self.log.info("Data folder is empty")

        if len(certs) == 0 or len(data) == 0:
            raise KubernetesException('ValidationOperations', '110', "Certs/Data folder is emtpy")

        file_list = certs
        file_list.extend(data)
        file_list = [file.split('\\', 3)[-1].replace('\\', '/') for file in file_list]

        app_name = app_metadata[app_list[0]]['name']
        self.k8s_helper.navigate_to_etcd(cluster_name=self.clientName)
        self.k8s_helper.run_fs_dest_restore_job(
            cluster_name=self.clientName,
            destination_client=self.access_node,
            destination_path=self.fs_destination_path,
            file_path=app_name,
        )

        # Validate content from browse got restored at destination
        status = True
        for file in file_list:
            if self.proxy_obj.check_file_exists(f'{self.fs_destination_path}/{file}'):
                self.log.info(f"File [{file}] restored successfully to destination [{self.fs_destination_path}]")
            else:
                self.log.error(f"File [{file}] not restored successfully to destination [{self.fs_destination_path}]")
                status = False
        else:
            if not status:
                raise CVTestStepFailure("FS Destination restore did not restore all files.")
            else:
                self.log.info("All files are restored successfully")

    def run(self):
        """
        Run the Testcase - New K8s configuration, full backup job, inc backup job, out-of-place restore
        """
        try:

            # Step 1 - Add cluster step
            self.add_cluster_step()
            # # Step 2 - enable etcd protection
            self.enable_etcd_step()
            # # Step 3 - Perform FULL ETCD Backup
            self.perform_etcd_backup_step()
            # # Step 4 - Check whether CV Resources cleaned up from kube-system Namespace
            self.check_cv_cleanup_step()
            # # Step 5 - Perform FS Destination restore
            self.run_fs_dest_restore()
            # Step 5 - Perform INCR ETCD Backup
            self.perform_etcd_backup_step(backup_type='INCREMENTAL')
            # Step 6 - Check whether CV Resources cleaned up from kube-system Namespace
            self.check_cv_cleanup_step()

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
