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

    perform_backup()                    -- Performs Backup of app-group

    fetch_files()                       -- Function to fetch required files for FS Destination restore

    oop_restore()                       -- Performs Out of place restore

    single_file_restore()               -- Perform FS Destination restore of a single file

    long_name_restore()                 -- Perform Out-of-place restore with long file name

    full_pvc_content_restore()          -- Performing Out-of-place PVC restore

    in_place_restore()                  -- Performs in-place restore of application

    run()                               --  Run function of this test case
"""
import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes import KubernetesUtils
from AutomationUtils.commonutils import get_random_string
from Web.Common.page_object import TestStep


automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, Perform backup and restore of pods,deployment with problematic Dataset
    1.  Connect to Kube API using Config
    2.  Create SA,CRB for CV
    3.  Fetch Token name and Token for SA secret
    4.  Create Long Pod name, long PVC - readonly, long Namespace, Long Deployment, Long SS
    5.  Create k8s client with proxy provided
    6.  Create app group
    7.  Add content for full validation
    7.  Initiate Full backup of each app group and verify job completion
    8.  Initiate out-of-place full app restore and verify job completion
    9.  Cleanup original namespace
    10. Restore OOP with new long app name
    11. perform OOP volume and data restore unconditional Overwrite
    12. FS Destination restore
    13. Initiate in place full app restore and verify job completion
    14. Cleanup testbed
    15. Cleanup client
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Problematic data validation - Long Entity names, paths"
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
        # 253 chars
        self.dnsName = None
        # 63 chars
        self.rfcName = None
        self.accessmode = None
        self.pod_name = None
        self.pod_pvc_name = None
        self.pvc_restore_namespace = None
        self.file_restore_destination = None
        self.pvc_restore_destination = None
        self.restore_destination = None
        self.short_pod_name = None
        self.short_pod_pvc_name = None
        self.before_backup = None
        self.folder_name = None
        self.resources_before_backup = None
        self.resources_after_restore = None
        self.ns_restore_namespace = None
        self.checksum_before_ns_restore = None

    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.dnsName = get_random_string(length=self.tcinputs.get("DnsLength", 253))
        self.rfcName = get_random_string(length=self.tcinputs.get("RfcLength", 63))
        self.testbed_name = "k8s-auto-{}".format(self.id)
        # Creates namespace of length 63 chars
        self.namespace = self.testbed_name + "-" + self.rfcName[:48]
        # Strips last 4 characters of namespace, appends -rst making the length 63
        self.restore_namespace = self.namespace[:59] + "-rst"
        # PVC Restore Namespace to validate OOP PVC Restore test case
        self.pvc_restore_namespace = self.namespace[:55] + "-pvc-rst"
        self.app_grp_name = self.testbed_name + "-app-grp"
        self.serviceaccount = self.testbed_name + "-sa-" + self.rfcName[:45]
        self.authentication = "Service account"
        self.subclientName = "automation-{}".format(self.id)
        self.clientName = "k8sauto-{}".format(self.id)
        self.destclientName = "k8sauto-{}-dest".format(self.id)
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", automation_config.ACCESS_NODE)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        self.controller = self.commcell.clients.get(self.access_node)
        self.controller_id = int(self.controller.client_id)
        self.file_restore_destination = '/tmp' + self.testbed_name
        self.pvc_restore_destination = 'pvc-restore-' + self.dnsName[:241]
        self.pod_pvc_name = self.testbed_name + '-podpvc-' + self.dnsName[:230]
        self.pod_name = self.testbed_name + '-pod-' + self.dnsName[:230]
        self.restore_destination = "/" + self.testbed_name
        self.folder_name = f"{self.dnsName}/{self.rfcName}"
        self.ns_restore_namespace = self.namespace[:55] + '-ns-rst'
        self.accessmode = self.tcinputs.get('AccessMode', 'ReadWriteOnce')
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
            4. Create namespace, restore namespace and PVC Restore namespace
            5. Create service with long name length
            6. Create Config Map and secret with long name length
            7. Create test Pod with PVC of long name length
            8. Create test Pod with PVC of short name length
            9. Create test deployment with PVC with long name length
            10. Create Pod, PVC in PVC restore Namespace
            11. Populate Entities with random data
            12. Add cluster and app group
        """

        self.log.info("Creating cluster resources...")

        # Create service account if it doesn't exist
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, sa_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, sa_namespace, cluster_role)

        time.sleep(30)
        self.servicetoken = self.kubehelper.get_serviceaccount_token(
            self.serviceaccount, sa_namespace
        )

        # Creating testbed namespace if it does not exist
        self.kubehelper.create_cv_namespace(self.namespace)

        # Creating namespace for restore if it does not exist
        self.kubehelper.create_cv_namespace(self.restore_namespace)

        # Creating namespace for OOP PVC restore
        self.kubehelper.create_cv_namespace(self.pvc_restore_namespace)

        # Create Service of long length
        svc_name = 'svc-' + self.rfcName[:59]
        self.kubehelper.create_cv_svc(svc_name, self.namespace)

        # Creating test pod of long length
        secret_name = 'secret-' + self.dnsName[:245]
        config_name = 'cm-' + self.dnsName[:250]
        self.kubehelper.create_cv_secret(secret_name, self.namespace)
        self.kubehelper.create_cv_configmap(config_name, self.namespace)

        self.kubehelper.create_cv_pvc(
            self.pod_pvc_name,
            self.namespace,
            storage_class=self.storageclass,
            accessmode=self.accessmode
        )

        self.kubehelper.create_cv_pod(
            self.pod_name, self.namespace, secret=secret_name, configmap=config_name, pvc_name=self.pod_pvc_name
        )
        time.sleep(30)
        self.content.append(self.namespace + '/' + self.pod_name)

        # creating PVC for short length pod
        self.short_pod_pvc_name = 'podpvc-short'
        self.kubehelper.create_cv_pvc(self.short_pod_pvc_name,
                                      self.namespace,
                                      storage_class=self.storageclass,
                                      accessmode=self.accessmode)
        # creating pod of short length
        self.short_pod_name = "pod-short"
        self.kubehelper.create_cv_pod(
            self.short_pod_name, self.namespace, pvc_name=self.short_pod_pvc_name)
        self.content.append(self.namespace + '/' + self.short_pod_name)

        # creating test deployment
        pvc_deployment_name = 'deploypvc-' + self.dnsName[:243]
        self.kubehelper.create_cv_pvc(pvc_deployment_name,
                                      self.namespace,
                                      storage_class=self.storageclass,
                                      accessmode=self.accessmode)
        deployment_name = 'deployment-' + self.dnsName[:242]
        self.kubehelper.create_cv_deployment(deployment_name, self.namespace, pvc_deployment_name)
        self.content.append(self.namespace + '/' + deployment_name)

        # Creating destination PVC
        self.kubehelper.create_cv_pvc(
            self.pvc_restore_destination, self.pvc_restore_namespace,
            storage_class=self.storageclass,
            accessmode=self.accessmode)

        # Creating destination PVC Pod
        self.kubehelper.create_cv_pod(
            self.pod_name, self.pvc_restore_namespace, pvc_name=self.pvc_restore_destination)

        self.log.info("Populating pods with random data")
        for pod in self.kubehelper.get_namespace_pods(self.namespace):
            # Create a deep path with long file name
            self.kubehelper.create_random_cv_pod_data(
                pod, self.namespace, file_name=self.dnsName, foldername=self.folder_name,
                no_of_files=1)
            time.sleep(10)
        self.log.info("Populated data in pods")

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
        TestCase Setup
        """
        try:
            self.init_inputs()
            self.create_testbed()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    @TestStep()
    def perform_backup(self):
        """
        Step 1 -- Verify Full backup job
        """

        self.log.info("Running FULL Backup job...")
        self.before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.kubehelper.backup('FULL')
        self.log.info('FULL backup job step completed')

    @TestStep()
    def oop_restore(self):
        """
        Step 2 -- Performing Out-of-place restore and restore validation
        """
        self.kubehelper.run_restore_validate(
            self.clientName,
            self.storageclass
        )
        after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
        self.kubehelper.validate_data(self.before_backup, after_restore)

        self.log.info("OOP Restore successful")

    def fetch_files(self, folder="tmp"):
        """
        Fetch the files in folder using browse
        """
        app_list, app_id_dict = self.subclient.browse()
        app_id = app_id_dict['\\' + self.pod_name]['snap_display_name']
        query = "\\" + app_id + "\\" + self.pod_pvc_name + '\\' + folder.replace('/', '\\')

        item_list, item_info_dict = self.subclient.browse(query)
        item_list = list(map(
            lambda file_path: file_path.replace(
                "\\" + self.pod_name + "\\" + self.pod_pvc_name + "\\", ""
            ).replace('\\', '/'),
            item_list
        ))

        return item_list

    @TestStep()
    def single_file_restore(self):
        """
        Step 3 -- Running FS Destination Restore of a single file
        """
        self.log.info("Getting item list")
        item_list = self.fetch_files(folder=self.folder_name)
        item_list = [item_list[0]]

        self.log.info(f"Obtained item list - {item_list}")

        self.log.info("Performing FS Restore")
        self.kubehelper.fs_dest_restore(
            application_name=self.pod_name,
            restore_list=item_list,
            source_namespace=self.namespace,
            pvc_name=self.pod_pvc_name,
            access_node=self.access_node,
            destination_path=self.file_restore_destination
        )

        self.log.info("File system destination restore of single file step complete")

    @TestStep()
    def long_name_restore(self):
        """
        Step 4 -- Verify FULL APPLICATION Out of place Restore with Long APPLICATION name
        """
        source_checksum = {
            self.short_pod_name: self.kubehelper.get_files_checksum(namespace=self.namespace)[self.short_pod_name]
        }
        long_new_name = self.dnsName[:130]
        self.kubehelper.restore_out_of_place(
            self.clientName,
            self.restore_namespace,
            self.storageclass,
            application_list=[self.short_pod_name],
            restore_name_map={self.short_pod_name: long_new_name}
        )
        dest_checksum = {
            self.short_pod_name: self.kubehelper.get_files_checksum(namespace=self.restore_namespace)[long_new_name]
        }
        self.log.info(source_checksum)
        self.log.info(dest_checksum)
        self.kubehelper.verify_checksum_dictionary(source_checksum, dest_checksum)
        self.log.info("Long name OOP Restore successful")

    @TestStep()
    def full_pvc_content_restore(self):
        """
        Step 5 -- Verify Out of place Volume restore
        """
        self.log.info("Performing Out of place Volume restore")
        self.kubehelper.modify_pod_data(
            pod_name=self.pod_name,
            namespace=self.pvc_restore_namespace,
            folder_name="/",
            delete=True
        )
        self.kubehelper.restore_to_pvc(
            application_name=self.pod_name,
            restore_list=["/"],
            source_namespace=self.namespace,
            source_pvc=self.pod_pvc_name,
            destination_pvc=self.pvc_restore_destination,
            destination_namespace=self.pvc_restore_namespace,
            access_node=self.access_node,
            unconditional_overwrite=True,
            destination_path="/"
        )
        self.log.info("Restore to PVC of full pvc content step complete")

    @TestStep()
    def full_pvc_ip_content_restore(self):
        """
        Step 6 -- Verify In place Application file restore
        """
        self.log.info("Performing In-place Volume restore")
        # Get checksum of data
        checksum_before_restore = self.kubehelper.get_files_checksum(
            namespace=self.namespace,
        )
        # Delete data
        self.kubehelper.modify_pod_data(
            pod_name=self.pod_name,
            namespace=self.namespace,
            folder_name=self.folder_name,
            delete=True
        )
        self.kubehelper.restore_to_pvc(
            application_name=self.pod_name,
            restore_list=["/"],
            source_namespace=self.namespace,
            source_pvc=self.pod_pvc_name,
            access_node=self.access_node,
            in_place=True,
            validate_checksum=False
        )
        checksum_after_restore = self.kubehelper.get_files_checksum(
            namespace=self.namespace,
        )

        self.kubehelper.verify_checksum_dictionary(checksum_before_restore, checksum_after_restore)

    @TestStep()
    def in_place_restore(self):
        """
        Step 7 -- Verify FULL APPLICATION In place restore
        """
        self.log.info("Performing Full Application In-place restore")
        self.kubehelper.run_restore_validate(
            self.clientName,
            self.storageclass,
            inplace=True
        )
        self.log.info("In place restore successful")

    @TestStep()
    def verify_full_ns_backup(self):
        """
        Step 8 -- Create app group with namespace as content. Verify FULL Backup of entire namespace as content
        """
        self.log.info('Run FULL Backup job with Namespace as content')
        self.content = [self.namespace]
        self.checksum_before_ns_restore = self.kubehelper.get_files_checksum(namespace=self.namespace)
        KubernetesUtils.add_application_group(
            self,
            content=self.content,
            plan=self.plan,
            name=self.subclientName+'-NS',
        )
        self.kubehelper.source_vm_object_creation(self)
        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.kubehelper.backup("FULL")
        self.log.info('FULL Backup job step with Namespace as content successfully completed')

    @TestStep()
    def verify_namespace_level_oop_restore(self):
        """
        Step 9 -- Verify Namespace-level restore out-of-place
        """
        self.log.info('Run Namespace-level restore out-of-place')
        restore_namespace_map = {
            self.namespace: self.ns_restore_namespace
        }
        self.kubehelper.namespace_level_restore(
            in_place=False,
            namespace_list=self.content,
            restore_name_map=restore_namespace_map,
            overwrite=False
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.ns_restore_namespace)
        checksum_after_ns_restore = self.kubehelper.get_files_checksum(self.ns_restore_namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.kubehelper.verify_checksum_dictionary(self.checksum_before_ns_restore, checksum_after_ns_restore)
        self.log.info('Namespace-level restore out-of-place step successfully completed')

    @TestStep()
    def verify_namespace_level_ip_overwrite(self):
        """
        Step 10- Verify Namespace-level restore in-place with overwrite
        """
        self.log.info('Run Namespace-level restore out-of-place with overwrite')
        self.checksum_before_ns_restore = self.kubehelper.get_files_checksum(self.namespace)
        self.kubehelper.namespace_level_restore(
            namespace_list=self.content,
            in_place=True
        )
        self.resources_after_restore = self.kubehelper.get_all_resources(self.namespace)
        checksum_after_ns_restore = self.kubehelper.get_files_checksum(self.namespace)
        self.kubehelper.validate_data(self.resources_before_backup, self.resources_after_restore)
        self.kubehelper.verify_checksum_dictionary(self.checksum_before_ns_restore, checksum_after_ns_restore)
        self.log.info('Namespace-level restore in-place with overwrite step successfully completed')

    @TestStep()
    def delete_testbed(self):
        """
        Step 11 -- Delete testbed, delete client
        """
        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)
        self.kubehelper.delete_cv_namespace(self.pvc_restore_namespace)
        self.kubehelper.delete_cv_namespace(self.ns_restore_namespace)
        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)
        KubernetesUtils.delete_cluster(self, self.clientName)

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Populating data and performing backup
            self.perform_backup()

            # Performing Out-of-place restore and restore validation
            self.oop_restore()

            # Performing FS destination restore
            self.single_file_restore()

            # Performing Out-of-Place Restore with Long application name
            self.long_name_restore()

            # performing Out-of-Place Volume restore
            self.full_pvc_content_restore()

            # performing in place volume restore
            self.full_pvc_ip_content_restore()

            # Performing in-place application restore
            self.in_place_restore()

            # Create NS level app group and perform backup

            self.verify_full_ns_backup()

            # Perform NS level OOP restore

            self.verify_namespace_level_oop_restore()

            # Perform NS level IN restore

            self.verify_namespace_level_ip_overwrite()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.delete_testbed()
