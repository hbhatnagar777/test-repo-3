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

    _get_default_storage_class_from_cluster()   --  Fetch the default storage class from cluster

    setup()                             --  setup method for test case

    tear_down()                         --  tear down method for testcase

    init_inputs()                       --  Initialize objects required for the testcase

    load_kubeconfig_file()              --  Load Kubeconfig file and connect to the Kubernetes API Server

    create_testbed()                    --  Create the testbed required for the testcase

    delete_testbed()                    --  Delete the testbed created

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    run()                               --  Run function of this test case

    fetch_manifest_files()              --  Fetch the backed up manifest files

    single_file_restore()               --  Perform manifest restore for a single file

    multiple_file_restore()             --  Perform manifest restore for multiple files

    modify_existing_files()             --  Modify the existing files at restore destination

    run_backup()                        --  Test step to run Backup
"""


import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Kubernetes import KubernetesUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to validate manifest restore jobs.
    This testcase does the following --
    1. Create testbed for the testcase
    2. Run full backup job and perform validation.
    3. Initiate Full Backup for App group created and verify job completed
    4. Initiate manifest restore job for single file and validate files restore
    5. Initiate manifest restore job for all manifest files and validate files restored
    6. Cleanup testbed
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Manifest Restore"
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
        self.pod_name = None
        self.pvc_name = None
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
        self.proxy_obj = None
        self.restore_destination = None
        self.kubeconfig_on_proxy = None
        self.content = []

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
        self.proxy_obj = Machine(self.controller)
        self.restore_destination = '/tmp/' + self.testbed_name
        self.kubeconfig_on_proxy = '/tmp/kubeconfig-' + self.testbed_name + '.yaml'
        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

    @TestStep()
    def create_testbed(self):
        """Create testbed for testcase
        """

        self.log.info("Creating cluster resources...")

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)

        # Creating namespace for restore if not exists
        self.kubehelper.create_cv_namespace(self.restore_namespace)

        # Create service account if doesn't exist
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, sa_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, sa_namespace, cluster_role)

        time.sleep(30)
        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, sa_namespace)

        # Creating PVC
        self.pvc_name = self.testbed_name + '-pvc'
        self.kubehelper.create_cv_pvc(self.pvc_name, self.namespace, storage_class=self.storageclass)

        # Creating test pod
        self.pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(self.pod_name, self.namespace, pvc_name=self.pvc_name)
        time.sleep(30)
        self.content.append(self.namespace + '/' + self.pod_name)

        # Create Service
        svc_name = self.testbed_name + '-svc'
        self.kubehelper.create_cv_svc(svc_name, self.namespace)

        # Creating test pod
        secret_name = self.testbed_name + '-secret'
        config_name = self.testbed_name + '-cm'
        self.kubehelper.create_cv_secret(secret_name, self.namespace)
        self.kubehelper.create_cv_configmap(config_name, self.namespace)

        self.log.info("Copying kubeconfig from local to access node")
        local_machine = Machine()

        content = local_machine.read_file(self.k8s_config)
        for line in content.split('\n'):
            self.proxy_obj.append_to_file(self.kubeconfig_on_proxy, line)

        self.log.info(f"Kubeconfig copied at {self.kubeconfig_on_proxy}")

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

    def setup(self):
        """
        Setup the Testcase
        """
        try:
            self.init_inputs()
            self.create_testbed()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    @TestStep()
    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)

        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        self.proxy_obj.remove_directory(self.restore_destination)
        self.log.info(f"Removed directory [{self.restore_destination}] from access node [{self.access_node}]")

        self.proxy_obj.delete_file(self.kubeconfig_on_proxy)
        self.log.info(f"Removed temporary kubeconfig file on access node from {self.kubeconfig_on_proxy}")

        KubernetesUtils.delete_cluster(self, self.clientName)

    def fetch_manifest_files(self):
        """Fetch the manifest files using browse
        """
        app_list, app_id_dict = self.subclient.browse()
        app_id = app_id_dict['\\' + self.pod_name]['snap_display_name']

        disk_list, disk_info_dict = self.subclient.disk_level_browse("\\" + app_id)
        manifest_list = list(filter(lambda name: name.split('.')[-1] == "yaml", disk_list))
        manifest_list = [manifest.split('\\')[-1] for manifest in manifest_list]

        return manifest_list

    def modify_existing_files(self):
        """Modify existing files at restore directory
        """

        self.log.info(f"Modifying files at restore destination [{self.restore_destination}]")
        self.proxy_obj = Machine(self.commcell.clients.get(self.access_node))

        self.proxy_obj.modify_test_data(
            data_path=self.restore_destination,
            modify=True,
            acls=True,
            xattr=True,
            permissions=True
        )

    @TestStep()
    def run_backup(self):
        """Run Backup step"""
        self.log.info("Step -- Run and verify FULL backup")
        self.kubehelper.backup('FULL')
        self.log.info("Run Backup Step complete")

    @TestStep()
    def single_file_restore(self):
        """Run Manifest Restore of a single file
        """

        manifest_list = self.fetch_manifest_files()
        manifest_list = [manifest_list[0]]

        self.log.info("Step -- Run manifest restore of single manifest")
        self.kubehelper.manifest_restore(
            application_name=self.pod_name,
            access_node=self.access_node,
            destination_path=self.restore_destination,
            manifest_list=manifest_list,
            unconditional_overwrite=True
        )
        self.log.info("Manifest restore of single file step complete")

        self.log.info("Validating manifest restores using kubectl diff")
        self.kubehelper.validate_restored_manifest(
            self.restore_destination, self.access_node, self.kubeconfig_on_proxy
        )
        self.log.info("Manifest restore validation successful")

    @TestStep()
    def multiple_file_restore(self):
        """Modify existing files and run Manifest Restore of multiple files
        """

        self.log.info("Step -- Modify existing files and run manifest restore of multiple manifests")
        self.modify_existing_files()

        self.kubehelper.manifest_restore(
            application_name=self.pod_name,
            access_node=self.access_node,
            destination_path=self.restore_destination,
            unconditional_overwrite=True
        )
        self.log.info("Manifest restore of multiple file steps complete")

        self.log.info("Validating manifest restores using kubectl diff")
        self.kubehelper.validate_restored_manifest(
            self.restore_destination, self.access_node, self.kubeconfig_on_proxy
        )
        self.log.info("Manifest restore validation successful")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Run FULL Backup step
            self.run_backup()

            # Run single file manifest restore
            self.single_file_restore()

            # Run multiple files manifest restore
            self.multiple_file_restore()

            # Cleanup testbed after successful completion
            self.delete_testbed()

            self.log.info("ALL STEPS COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)
