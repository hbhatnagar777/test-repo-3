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

    fetch_files()                       --  Fetch the backed up files

    single_file_restore()               --  Perform fs dest restore for a single file

    multiple_file_restore()             --  Perform fs dest restore for multiple files

    single_folder_restore()             --  Perform fs dest restore for a single folder

    multiple_folder_restore()           --  Perform fs dest restore for multiple folder

    full_pvc_content()                  --  Perform fs dest restore for complete pvc

    run_backup()                        --  Test step to run Backup

    modify_existing_files()             --  Modify the existing files at restore destination

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
    Testcase to validate FS Destination restore jobs.
    This testcase does the following --
    1. Create testbed for the testcase
    2. Add content for full validation.
    3. Initiate Full Backup for App group created and verify job completed
    4. Restore FS Destination for single file and verify checksum
    5. Restore FS Destination for multiple file and verify checksum
    6. Create new data and run Incremental Backup
    7. Restore FS Destination for single folder and verify checksum
    8. Restore FS Destination for multiple folder and verify checksum
    9. Restore FS Destination for full PVC and verify checksum
    10. Cleanup testbed
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - File System Destination Restore"
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
        self.serviceaccount = None
        self.authentication = "Service account"
        self.subclientName = None
        self.clientName = None
        self.destclientName = None
        self.destinationClient = None
        self.controller = None
        self.restore_destination = None
        self.pvc_name = None
        self.pod_name = None
        self.folders_to_create = []
        self.proxy_obj = None
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
        self.content.append(self.namespace + '/' + self.pod_name)
        time.sleep(30)

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

        KubernetesUtils.delete_cluster(self, self.clientName)

    def fetch_files(self, folder="/tmp"):
        """Fetch the files in folder using browse
        """
        app_list, app_id_dict = self.subclient.browse()
        app_id = app_id_dict['\\' + self.pod_name]['snap_display_name']

        query = "\\" + app_id + "\\" + self.pvc_name + "\\" + folder

        item_list, item_info_dict = self.subclient.browse(query)
        item_list = list(map(
            lambda file_path: file_path.replace(
                "\\" + self.pod_name + "\\" + self.pvc_name + "\\", ""
            ).replace('\\', '/'),
            item_list
        ))

        return item_list

    @TestStep()
    def run_backup(self, backup_level="INCREMENTAL"):
        """Run Backup step"""
        self.log.info("Step -- Add data and verify Backup")

        folder_name = "folder-" + str(int(time.time()))
        self.folders_to_create.append(folder_name)
        for pod in self.kubehelper.get_namespace_pods(self.namespace):
            self.kubehelper.create_random_cv_pod_data(pod, self.namespace, foldername=folder_name)
            time.sleep(10)

        self.kubehelper.backup(backup_level)
        self.log.info("Run Backup Step complete")

    def modify_existing_files(self):
        """Modify existing files at restore directory
        """

        self.log.info(f"Modifying files at restore destination [{self.restore_destination}]")

        self.proxy_obj.modify_test_data(
            data_path=self.restore_destination,
            modify=True,
            acls=True,
            xattr=True,
            permissions=True
        )

    @TestStep()
    def single_file_restore(self):
        """Run FS Destination Restore of a single file
        """

        folder = self.folders_to_create[0]
        item_list = self.fetch_files(folder=folder)
        item_list = [item_list[0]]

        self.log.info("Step -- Run file system destination restore of single file")
        self.kubehelper.fs_dest_restore(
            application_name=self.pod_name,
            restore_list=item_list,
            source_namespace=self.namespace,
            pvc_name=self.pvc_name,
            access_node=self.access_node,
            destination_path=self.restore_destination
        )
        self.log.info("File system destination restore of single file step complete")

    @TestStep()
    def multiple_file_restore(self):
        """Modify existing files and run FS Destination Restore of multiple files
        """

        folder = self.folders_to_create[0]
        item_list = self.fetch_files(folder=folder)

        self.log.info("Step -- Modify existing files and run file system destination restore of multiple files")
        self.modify_existing_files()

        self.kubehelper.fs_dest_restore(
            application_name=self.pod_name,
            restore_list=item_list,
            source_namespace=self.namespace,
            pvc_name=self.pvc_name,
            access_node=self.access_node,
            destination_path=self.restore_destination,
            unconditional_overwrite=True
        )
        self.log.info("File system destination restore of multiple files step complete")

    @TestStep()
    def multiple_folder_restore(self):
        """Modify existing files and Run FS Destination Restore of multiple folders
        """

        self.log.info("Step -- Modify existing files and run file system destination restore of multiple folders")
        self.modify_existing_files()

        self.kubehelper.fs_dest_restore(
            application_name=self.pod_name,
            restore_list=self.folders_to_create,
            source_namespace=self.namespace,
            pvc_name=self.pvc_name,
            access_node=self.access_node,
            destination_path=self.restore_destination,
            unconditional_overwrite=True
        )
        self.log.info("File system destination restore of multiple folders step complete")

    @TestStep()
    def full_pvc_content_restore(self):
        """Modify existing files and Run FS Destination Restore full pvc content
        """

        self.log.info("Step -- Modify existing files and run file system destination restore of full pvc content")
        self.modify_existing_files()

        self.kubehelper.fs_dest_restore(
            application_name=self.pod_name,
            restore_list=['/'],
            source_namespace=self.namespace,
            pvc_name=self.pvc_name,
            access_node=self.access_node,
            destination_path=self.restore_destination,
            unconditional_overwrite=True
        )
        self.log.info("File system destination restore of full pvc content step complete")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Run FULL Backup step
            self.run_backup("FULL")

            # Run single file fs dest restore
            self.single_file_restore()

            # Run multiple files fs dest restore
            self.multiple_file_restore()

            # Run backup and multiple folders fs dest restore
            self.run_backup()
            self.multiple_folder_restore()

            # Run fs dest restore for full PVC
            # Commenting out this step, as root content restores pvc as well
            # Need to study and figure out a way around it
            # self.full_pvc_content_restore()

            # Cleanup testbed after successful completion
            self.delete_testbed()

            self.log.info("ALL STEPS COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)
