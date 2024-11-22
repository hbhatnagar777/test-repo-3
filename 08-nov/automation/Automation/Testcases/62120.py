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
    Testcase to validate PVC data restore jobs.
    This testcase does the following --
    1. Create testbed for the testcase
    2. Add content for full validation.
    3. Initiate Full Backup for App group created and verify job completed
    4. Run PVC data restore of single file to another PVC at mount point of PVC. Compare checksum after restore.
    5. Delete previous file. Run PVC data restore of single file to new restore directory.
    6. Modify existing file and run PVC restore of multiple files with overwrite enabled and validate checksum.
    7. Add more data and verify INC Job.
    8. Modify existing filesand run PVC restore of multiple folders with overwrite enabled and validate checksum.
    9. Run in-place PVC restore overwrite enabled and validate checksum.
    10. Validate stray folders are not created on access node.
    11. Cleanup testbed
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Restore to PVC"
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
        self.accessmode = None
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
        self.restore_destination = "/" + self.testbed_name
        self.accessmode = self.tcinputs.get('AccessMode', 'ReadWriteOnce')
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
        self.kubehelper.create_cv_pvc(
            self.pvc_name, self.namespace, storage_class=self.storageclass, accessmode=self.accessmode
        )

        # Creating test pod
        self.pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(self.pod_name, self.namespace, pvc_name=self.pvc_name)
        self.content.append(self.namespace + '/' + self.pod_name)
        time.sleep(30)

        # Creating PVC at destination
        self.pvc_name = self.testbed_name + '-pvc'
        self.kubehelper.create_cv_pvc(
            self.pvc_name, self.restore_namespace, storage_class=self.storageclass, accessmode=self.accessmode
        )

        # Creating test pod at destination
        self.pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(self.pod_name, self.restore_namespace, pvc_name=self.pvc_name)
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

        KubernetesUtils.delete_cluster(self, self.clientName)

    def fetch_files(self, folder="/mnt/data"):
        """Fetch the files in folder using browse
        """
        app_list, app_id_dict = self.subclient.browse()
        app_id = app_id_dict['\\' + self.pod_name]['snap_display_name']

        query = "\\" + app_id + "\\" + self.pvc_name + "\\" + folder

        item_list, item_info_dict = self.subclient.browse(query)
        item_list = list(map(
            lambda file_path: file_path.replace(
                "\\" + self.pod_name + "\\" + self.pvc_name + "\\", ""
            ).replace('\\', '/'), item_list
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

        self.log.info(
            f"Modifying files at restore destination [{self.restore_destination}] " +
            f"in pod [{self.pod_name}] and namespace [{self.restore_namespace}]"
        )

        pod_checksum_dict = self.kubehelper.get_files_checksum(self.restore_namespace)[self.pod_name]
        file_list = list(pod_checksum_dict.keys())

        for file_path in file_list:
            resp = self.kubehelper.execute_command_in_pod(
                command=f"echo 'modified file' > {file_path}",
                pod=self.pod_name,
                namespace=self.restore_namespace,
            )
            if not resp:
                raise Exception(f"Command execution failed during modify file.")

        self.log.info("Modify existing files successful.")

    @TestStep()
    def single_file_restore_root(self):
        """Run restore to PVC of a single file to root location
        """

        folder = self.folders_to_create[0]
        item_list = self.fetch_files(folder=folder)
        item_list = [item_list[0]]

        self.log.info("Step -- Run restore to PVC of single file to root location")
        self.kubehelper.restore_to_pvc(
            application_name=self.pod_name,
            restore_list=item_list,
            source_namespace=self.namespace,
            source_pvc=self.pvc_name,
            destination_pvc=self.pvc_name,
            destination_namespace=self.restore_namespace,
            access_node=self.access_node,
            destination_path="/"
        )
        self.log.info("Restore to PVC of single file to root location step complete")

        # Deleting restored files
        resp = self.kubehelper.execute_command_in_pod(
            command="find /mnt/data -mindepth 1 -delete",
            pod=self.pod_name,
            namespace=self.restore_namespace,
        )

        if not resp:
            raise Exception(f"Command to delete restored files failed")

        self.log.info("Single file restore to PVC to root location complete.")

    @TestStep()
    def single_file_restore(self):
        """Run restore to PVC of a single file to new directory
        """

        folder = self.folders_to_create[0]
        item_list = self.fetch_files(folder=folder)
        item_list = [item_list[0]]

        self.log.info("Step -- Run restore to PVC of single file to new directory")
        self.kubehelper.restore_to_pvc(
            application_name=self.pod_name,
            restore_list=item_list,
            source_namespace=self.namespace,
            source_pvc=self.pvc_name,
            destination_pvc=self.pvc_name,
            destination_namespace=self.restore_namespace,
            access_node=self.access_node,
            destination_path=self.restore_destination
        )
        self.log.info("Restore to PVC of single file to new directory step complete")

    @TestStep()
    def multiple_file_restore(self):
        """Modify existing files and run Restore to PVC of multiple files
        """

        folder = self.folders_to_create[0]
        item_list = self.fetch_files(folder=folder)

        self.log.info("Step -- Modify existing files and run Restore to PVC of multiple files")
        self.modify_existing_files()

        self.kubehelper.restore_to_pvc(
            application_name=self.pod_name,
            restore_list=item_list,
            source_pvc=self.pvc_name,
            source_namespace=self.namespace,
            destination_pvc=self.pvc_name,
            destination_namespace=self.restore_namespace,
            access_node=self.access_node,
            destination_path=self.restore_destination,
            unconditional_overwrite=True
        )
        self.log.info("Restore to PVC of multiple files step complete")

    @TestStep()
    def multiple_folder_restore(self):
        """Modify existing files and Run Restore to PVC of multiple folders
        """

        self.log.info("Step -- Modify existing files and run Restore to PVC of multiple folders")
        self.modify_existing_files()

        self.kubehelper.restore_to_pvc(
            application_name=self.pod_name,
            restore_list=self.folders_to_create,
            source_namespace=self.namespace,
            source_pvc=self.pvc_name,
            destination_pvc=self.pvc_name,
            destination_namespace=self.restore_namespace,
            access_node=self.access_node,
            destination_path=self.restore_destination,
            unconditional_overwrite=True
        )
        self.log.info("Restore to PVC of multiple folders step complete")

    @TestStep()
    def full_pvc_content_restore(self):
        """Modify existing files and Run full pvc content Restore to target PVC
        """

        self.log.info("Step -- Modify existing files and run PVC restore of full pvc content")
        self.modify_existing_files()

        self.kubehelper.restore_to_pvc(
            application_name=self.pod_name,
            restore_list=["/"],
            source_namespace=self.namespace,
            source_pvc=self.pvc_name,
            destination_pvc=self.pvc_name,
            destination_namespace=self.restore_namespace,
            access_node=self.access_node,
            destination_path=self.restore_destination,
            unconditional_overwrite=True
        )
        self.log.info("Restore to PVC of full pvc content step complete")

    @TestStep()
    def multiple_file_inplace(self):
        """Run Restore to PVC of multiple files in-place
        """

        folder = self.folders_to_create[0]
        item_list = self.fetch_files(folder=folder)
        item_list.extend(self.fetch_files(self.folders_to_create[1]))

        self.log.info("Step -- Run Restore to PVC of multiple files in-place")

        self.kubehelper.restore_to_pvc(
            application_name=self.pod_name,
            restore_list=item_list,
            source_namespace=self.namespace,
            source_pvc=self.pvc_name,
            access_node=self.access_node,
            in_place=True,
            unconditional_overwrite=True
        )

        self.log.info("Restore to PVC of multiple files in-place step complete")

    @TestStep()
    def validate_access_node_folders(self):
        """Validate folders are not created on access node
        """

        proxy_obj = Machine(self.controller)
        install_dir = self.controller.install_directory

        if proxy_obj.check_directory_exists('/'.join([install_dir, self.restore_destination])):
            raise Exception(
                f"Folder [{'/'.join([install_dir, self.restore_destination])}] created on access node."
            )
        if proxy_obj.check_directory_exists('/' + self.restore_destination):
            raise Exception(
                f"Folder [{'/' + self.restore_destination}] created on access node."
            )

        self.log.info("No folders are created on access node.")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Run FULL Backup step
            self.run_backup("FULL")

            # Run single file Restore to PVC to root
            self.single_file_restore_root()

            # Run single file Restore to PVC to new directory
            self.single_file_restore()

            # Run multiple files Restore to PVC
            self.multiple_file_restore()

            # Run backup and multiple folders Restore to PVC
            self.run_backup()
            self.multiple_folder_restore()

            # Run Restore to PVC for full PVC content
            self.full_pvc_content_restore()

            # Run multiple files pvc restore inplace
            self.multiple_file_inplace()

            # For MR : 334295
            # # Validate folders are not created on access node
            # self.validate_access_node_folders()

            self.log.info("ALL STEPS COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.delete_testbed()
