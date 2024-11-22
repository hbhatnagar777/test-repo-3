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

    add_data_verify_backup()            --  Add data and verify backup job

    verify_inplace_restore_step()       --  Verify inplace restore job

    run()                               --  Run function of this test case
"""

import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Kubernetes.exceptions import KubernetesException
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes import KubernetesUtils
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform backups and namespace-level restores.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Create namespace containing Pod,PVC
    4. Create source data, take full backup
    5. Create hlink1_1-from-source1 slink1_1-from-source1 , take incr backup
    6. Perform OOP restore with overwrite ,verify files
    7. Create source2, hlink2_1-from-source2 slink2_1-from-source2 , take incr backup
    8. Perform OOP restore with overwrite ,verify files
    9. Create hlink1_2-from-source1 and slink1_2-from-source1 , take incr backup
    10.Perform OOP restore with overwrite ,verify files
    11.Create hlink_from_hlink1_1-from-source1 and slink_from_hlink1_1-from-source1 , take incr backup
    12.Perform OOP restore with overwrite ,verify files
    13. Create a dir with random files, and slink to it. Take incr backup
    14. Perform OOP restore with overwrite, Verify files
    15.Create hlink_from_slink1_1-from-source1 and slink_from_slink1_1-from-source1 , take incr backup
    16.Perform OOP restore with overwrite ,verify files
    17.Perform Full backup
    18.Perform OOP restore with overwrite ,verify files
    19. Cleanup testbed
    20. Cleanup clients created.
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.folder = None
        self.pvc_pod_name = None
        self.pod_name = None
        self.lr_only_ns = None
        self.rq_only_ns = None
        self.lr_and_rq = None
        self.name = "Kubernetes: Backup and restore of complex combinations of hard links and soft links"
        self.utils = TestCaseUtils(self)
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.controller_id = None
        self.testbed_name = None
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
        self.proxy_obj = None
        self.namespace = None
        self.restore_namespace = None
        self.path = None
        self.inode_dict = {}

    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.namespace = self.testbed_name + "-ns"
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
        self.folder = self.testbed_name
        self.path = '/mnt/data/{}'.format(self.folder)
        self.restore_namespace = self.namespace+'-rst'

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

    @TestStep()
    def create_testbed(self):
        """Create cluster resources and clients for the testcase
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
        self.kubehelper.create_cv_namespace(self.restore_namespace)

        self.pvc_pod_name = self.testbed_name + '-podpvc'
        self.kubehelper.create_cv_pvc(self.pvc_pod_name, self.namespace, storage_class=self.storageclass)
        self.pod_name = self.testbed_name + '-pod'
        self.kubehelper.create_cv_pod(
            self.pod_name, self.namespace, pvc_name=self.pvc_pod_name
        )

        KubernetesUtils.add_cluster(
            self,
            self.clientName,
            self.api_server_endpoint,
            self.serviceaccount,
            self.servicetoken,
            self.access_node
        )

        self.content = [self.namespace + '/' + self.pod_name]
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

        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        orphan_crb = self.testbed_name + '-orphan-crb'
        self.kubehelper.delete_cv_clusterrolebinding(orphan_crb)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)

    @TestStep()
    def perform_backup(self, backup_type='FULL'):
        """Performs backup
        """

        self.log.info(f'Run FULL Backup job with {self.content} as content')
        self.kubehelper.backup(backup_type)
        self.log.info('FULL Backup job step with Namespace as content successfully completed.')

    @TestStep()
    def create_source_data(self, path, file_name, data=None):
        """
        Creating source data

            Args:

                path:           (str)   location of source data

                file_name       (str)   Name of source file

                data            (data)  source data
        """

        if not data:
            data = f'{self.testbed_name}-{file_name}'

        file_path = f'{path}/{file_name}'

        command_str1 = f'touch {file_path}'
        command_str2 = f'echo {data}>>{file_path}'
        self.log.info(f'creating source file {file_name} at path {path} with data {data}')
        self.kubehelper.execute_command_in_pod(
            command=command_str1,
            pod=self.pod_name,
            namespace=self.namespace
        )
        self.kubehelper.execute_command_in_pod(
            command=command_str2,
            pod=self.pod_name,
            namespace=self.namespace
        )
        self.log.info(f'Created source file {file_name} at path {path} with data {data}')
        self.log.info(f"Adding source file to inode dict")
        self.inode_dict[file_path] = {'hlink': [], 'slink': []}
        self.log.info(self.inode_dict)

    @TestStep()
    def perform_restore_check_contents(self):
        """
        Performing OOP restore with overwrite

        """

        self.kubehelper.restore_out_of_place(
            client_name=self.clientName,
            restore_namespace=self.restore_namespace,
            overwrite=True
        )
        self.log.info("OOP restore success. Checking destination files")
        self.kubehelper.k8s_verify_restore_files(
            source_namespace=self.namespace,
            restore_namespace=self.restore_namespace
        )
        # perform inode and link checks
        self.log.info("Performing inode checks")
        inode_mapping = self.kubehelper.get_filename_inode_mapping(
            path=self.path,
            pod_name=self.pod_name,
            namespace=self.namespace
        )
        # Check the inode_dict, for each source file, check the corresponding hlink.
        # ensure inode of source file == inode of hlink

        self.log.info(inode_mapping)
        self.log.info(self.inode_dict)

        self.compare_source_dest_inodes(inode_mapping=inode_mapping)

    def compare_source_dest_inodes(self, inode_mapping):
        """

        """
        for source_file, link_dict in self.inode_dict.items():
            hlink_list = link_dict['hlink']
            source_inode = inode_mapping[source_file]
            for hlink in hlink_list:
                hlink_inode = inode_mapping[hlink]
                self.log.info(f"Checking inode of source file {source_file} and hlink {hlink}")
                self.log.info(f"Source inode: {source_inode} Hlink inode: {hlink_inode}")
                try:
                    assert source_inode == hlink_inode, f"Source inode {source_inode} != Hlink inode {hlink_inode}"
                except Exception as e:
                    self.log.error(f"Exception while checking inode of source file {source_file} and hlink {hlink}")
                    raise e

    def fetch_files(self):
        """Fetch the files in folder using browse
        """
        app_list, app_id_dict = self.subclient.browse()
        self.log.info(app_id_dict)
        app_id = app_id_dict['\\' + self.pod_name]['snap_display_name']

        query = "\\" + app_id + "\\" + self.pvc_pod_name + "\\" + self.folder
        self.log.info("Querying path: {}".format(query))

        item_list, item_info_dict = self.subclient.browse(query)
        item_list = list(map(
            lambda file_path: file_path.replace(
                "\\" + self.pod_name + "\\" + self.pvc_pod_name + "\\", ""
            ).replace('\\', '/'),
            item_list
        ))

        return item_list

    @TestStep()
    def perform_app_file_restore_check_contents(self):
        """
        Performing FS destination restore and checking contents
        """

        item_list = self.fetch_files()
        restore_destination = f"/tmp/{self.testbed_name}"

        self.kubehelper.fs_dest_restore(
            application_name=self.pod_name,
            restore_list=item_list,
            source_namespace=self.namespace,
            pvc_name=self.pvc_pod_name,
            access_node=self.access_node,
            destination_path=restore_destination,
            unconditional_overwrite=True
        )

        inode_mapping = self.kubehelper.get_filename_inode_mapping(restore_destination, access_node=self.access_node)
        self.log.info(inode_mapping)
        self.log.info(self.inode_dict)
        self.compare_source_dest_inodes(inode_mapping=inode_mapping)

    @TestStep()
    def create_folder(self):
        """Creating a folder for source data"""
        self.kubehelper.create_pod_dir(pod_name=self.pod_name, namespace=self.namespace,foldername=self.folder)

    def create_links_from_source(self, path, source_name, hlink_name=None, slink_name=None):
        """
        Creating links from a source file in pod using exec. link and source created at same path

            Args:

                path                (str)   Path to create link

                hlink_name          (str)   name of hardlink

                slink_name          (str)   name of slink to make

                source_name         (str)   name of source file
        """

        if hlink_name is not None:
            self.log.info(f"Creating hlink - [{hlink_name} from source [{source_name}]")
            command_str_hlink = f'ln {path}/{source_name} {path}/{hlink_name}'
            self.kubehelper.execute_command_in_pod(
                command=command_str_hlink,
                pod=self.pod_name,
                namespace=self.namespace
            )
            self.inode_dict[f'{path}/{source_name}']['hlink'].append(f'{path}/{hlink_name}')

        if slink_name is not None:
            self.log.info(f"Creating slink - [{slink_name} from source [{source_name}]")
            command_str_slink = f'ln -s {path}/{source_name} {path}/{slink_name}'
            self.kubehelper.execute_command_in_pod(
                command=command_str_slink,
                pod=self.pod_name,
                namespace=self.namespace
            )
            self.inode_dict[f'{path}/{source_name}']['slink'].append(f'{path}/{slink_name}')

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Step 1 - Take Full backup of the NS
            self.create_folder()
            self.create_source_data(file_name='source1', path=self.path)
            self.perform_backup()

            # Step 2 - Add source1->hlink1_1,slink1_1

            self.create_links_from_source(
                path=self.path,
                source_name='source1',
                hlink_name='hlink1_1-from-source1',
                slink_name='slink1_1-from-source1'
            )

            # Step 3 - Take incremental, Perform restore, check contents
            self.perform_backup(backup_type='INCREMENTAL')
            self.perform_restore_check_contents()

            # Step 4 - Add source2->hlink2_1,slink2_1
            self.create_source_data(file_name='source2', path=self.path)
            self.create_links_from_source(
                path=self.path,
                source_name='source2',
                hlink_name='hlink2_1-from-source2',
                slink_name='slink2_1-from-source2'
            )

            # Step 5 - Perform Incr backup,Perform restore, check contents
            self.perform_backup(backup_type='INCREMENTAL')
            self.perform_restore_check_contents()

            # Step 6 - create source1->hlink1_2,slink1_2
            self.create_links_from_source(
                path=self.path,
                source_name='source1',
                hlink_name='hlink1_2-from-source1',
                slink_name='slink1_2-from-source1'
            )
            # Step 7 - Perform Incr backup, restore, check contents
            self.perform_backup(backup_type='INCREMENTAL')
            self.perform_restore_check_contents()

            # Step 8 - Create a dir, and its slink
            self.kubehelper.create_pod_dir(
                pod_name=self.pod_name,
                namespace=self.namespace,
                location=self.path,
                foldername='dir1'
            )
            self.log.info(f"Adding source dir to inode dict")
            self.inode_dict[f'{self.path}/dir1'] = {'hlink': [], 'slink': []}
            self.log.info(self.inode_dict)

            self.create_source_data(
                path=self.path+'/dir1',
                file_name='source-dir',
                data='random data'
            )

            self.create_links_from_source(
                path=self.path,
                source_name='dir1',
                slink_name='slink_from_dir1'
            )

            # Step 9 - Perform Incr backup, restore, check contents
            self.perform_backup(backup_type='INCREMENTAL')
            self.perform_restore_check_contents()

            # Step 10 - Add hlink1_1->slink_from_hlink1_1 , hlink_from_hlink1_1
            # Adding source to inode_dict
            self.inode_dict[f'{self.path}/hlink1_1-from-source1'] = {'hlink': [], 'slink': []}
            self.create_links_from_source(
                path=self.path,
                source_name='hlink1_1-from-source1',
                hlink_name='hlink_from_hlink1_1-from-source1',
                slink_name='slink_from_hlink1_1-from-source1'
            )

            # Step 11 - Perform incr, restore,check contents
            self.perform_backup(backup_type='INCREMENTAL')
            self.perform_restore_check_contents()
            # Step 12 - Add slink1_1->slink_from_slink1_1 , hlink_from_slink1_1

            self.inode_dict[f'{self.path}/slink1_1-from-source1'] = {'hlink': [], 'slink': []}
            self.create_links_from_source(
                path=self.path,
                source_name='slink1_1-from-source1',
                hlink_name='hlink_from_slink1_1-from-source1',
                slink_name='slink_from_slink1_1-from-source1'
            )
            # Step 13 - Perform incr, restore, check contents
            self.perform_backup(backup_type='INCREMENTAL')
            self.perform_restore_check_contents()
            # Step 14 - Run Full backup , restore, check contents
            self.perform_backup()
            self.perform_restore_check_contents()
            # Step 15 - Perform app file restore, check contents - BROKEN as per MR
            # https://engweb.commvault.com/defect/464953
            # self.perform_app_file_restore_check_contents()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 15 -- Delete testbed, delete client, remove keys ")

            self.delete_testbed()
