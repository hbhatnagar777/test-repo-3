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
"""


import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from VirtualServer.VSAUtils import VirtualServerUtils
from Kubernetes import KubernetesUtils
from AutomationUtils import machine

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Pre post Scripts validation for K8s.

    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.location = None
        self.name = "PrePost Automation Scripts Validation"
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
        self.pod_name = None
        self.app_grp_name = None
        self.serviceaccount = None
        self.authentication = "Service account"
        self.subclientName = None
        self.clientName = None
        self.destclientName = None
        self.destinationClient = None
        self.controller = None
        self.controller_machine = None
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
        self.pod_name = self.testbed_name + '-pod'
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", automation_config.ACCESS_NODE)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        self.controller = self.commcell.clients.get(self.access_node)
        self.controller_id = int(self.controller.client_id)
        self.controller_machine = machine.Machine(self.controller)

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()
        self.location = self.tcinputs.get('MountPath', '/usr/share/nginx/html')

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

        # Creating namespace for restore if not exists
        self.kubehelper.create_cv_namespace(self.restore_namespace)

        # Creating PVC
        pvc_name = self.testbed_name + '-pvc'
        self.kubehelper.create_cv_pvc(pvc_name, self.namespace, storage_class=self.storageclass)

        # Creating test pod
        self.kubehelper.create_cv_pod(
            self.pod_name,
            self.namespace,
            pvc_name=pvc_name,
            pvc_mount_path=self.location
        )
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

    def delete_testbed(self):
        """
        Delete the generated testbed
        """

        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)

        crb_name = self.testbed_name + '-crb'
        # Delete cluster role binding
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)

    def pre_post_method(self, method=1):
        """Validate pre-post script with old/new method
            Args:
                method      (int)   --  Method for pre/post script to use
        """

        if method == 1:
            self.log.info("Validating pre/post script with files in kscript directory")
        elif method == 2:
            self.log.info("Validating pre/post script with client name folder in kscript directory")

        output_files = [f'k8sscript-prescript-{str(method)}', f'k8sscript-postscript-{str(method)}']
        install_path = self.controller.install_directory

        # Create kscripts directory if it does not exist
        self.log.info("Creating kscripts folder if not present")
        dir_path = ""
        if method == 1:
            dir_path = self.controller_machine.join_path(install_path, "Base", "kscripts")
        elif method == 2:
            dir_path = self.controller_machine.join_path(install_path, "Base", "kscripts", self.clientName)

        if not self.controller_machine.check_directory_exists(dir_path):
            self.controller_machine.create_directory(dir_path)

        # Creating prescript file
        prescript_file = "{0}.{1}.prescript".format(self.namespace, self.pod_name)
        prescript_file_path = self.controller_machine.join_path(dir_path, prescript_file)
        self.log.info(f"Creating prescript file at [{prescript_file_path}]")
        prescript_content = ['mkdir -p /k8sscript', f'touch /k8sscript/k8sscript-prescript-{str(method)}']
        self.controller_machine.create_file(prescript_file_path, "#!/bin/bash")
        for line in prescript_content:
            self.controller_machine.append_to_file(prescript_file_path, line)
        time.sleep(30)

        # Creating postscript file
        postscript_file = "{0}.{1}.postscript".format(self.namespace, self.pod_name)
        postscript_file_path = self.controller_machine.join_path(dir_path, postscript_file)
        self.log.info(f"Creating postscript file at [{postscript_file_path}]")
        postscript_content = ['mkdir -p /k8sscript', f'touch /k8sscript/k8sscript-postscript-{str(method)}']
        self.controller_machine.create_file(postscript_file_path, "#!/bin/bash")
        for line in postscript_content:
            self.controller_machine.append_to_file(postscript_file_path, line)
        time.sleep(30)

        # Run Full Backup
        try:
            self.log.info("Running FULL Backup job")
            self.kubehelper.backup('FULL')
            list_created = self.kubehelper.list_pod_content(self.pod_name, self.namespace, location='/k8sscript')
            for item in output_files:
                if item in list_created:
                    self.log.info("File [{}] created".format(item))
                else:
                    self.log.exception("File [{}] missed / failed to create ".format(item))
                    raise CVTestStepFailure("File [{}] missed / failed to create ".format(item))
        except CVTestStepFailure as exp:
            raise CVTestStepFailure(exp)

        finally:
            # Cleaning up pre-post script files
            self.log.info(f"Deleting file [{prescript_file_path}]")
            self.controller_machine.delete_file(prescript_file_path)

            self.log.info(f"Deleting file [{postscript_file_path}]")
            self.controller_machine.delete_file(postscript_file_path)

            dir_path = self.controller_machine.join_path(install_path, "Base", "kscripts", self.clientName)
            self.log.info(f"Deleting scripts folder [{dir_path}] if it exists")
            if self.controller_machine.check_directory_exists(dir_path):
                self.controller_machine.remove_directory(dir_path)

    def run(self):
        """
        Run the Testcase
        """
        try:
            self.kubehelper.source_vm_object_creation(self)
            VirtualServerUtils.decorative_log("Step 1 -- Add data to pods")
            self.kubehelper.create_random_cv_pod_data(
                self.pod_name,
                self.namespace,
                foldername="FULL",
                location=self.location
            )
            time.sleep(10)
            before_backup = self.kubehelper.get_all_resources(self.namespace)

            VirtualServerUtils.decorative_log("Step 2 -- Verify FULL Backup with Pre-Post script in kscripts folder")
            self.pre_post_method(method=1)

            VirtualServerUtils.decorative_log(
                "Step 3 -- Verify FULL Backup with Pre-Post script in kscripts/Cluster folder"
            )
            self.pre_post_method(method=2)

            VirtualServerUtils.decorative_log("Step 4 -- Verify Full Application Out of place Restore")
            self.log.info("Running out of place Restore")
            self.kubehelper.run_restore_validate(
                self.clientName,
                self.storageclass,
                mount_point=self.location
            )
            after_restore = self.kubehelper.get_all_resources(self.restore_namespace)
            self.kubehelper.validate_data(before_backup, after_restore)
            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 5 -- Delete testbed, delete client ")
            self.delete_testbed()
