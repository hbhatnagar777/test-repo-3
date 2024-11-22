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

    create_testbed()                    --  Create the testbed required for the testcase

    backup_step()                       -- Takes Backup of the application group {regkey - bK8sHelmChartBackup : True}

    backup_step_with_regkey()           -- Takes Backup of the application group {regkey - bK8sHelmChartBackup : False}

    restore_with_overwrite()            -- Performs Out-of-Place Restore with overwrite

    restore_without_overwrite()         -- Performs Out-of-Place Restore without overwrite

    check_if_source_deleted()           -- Verifies whether helm apps at source are deleted after deleting helm apps
                                            at destination

    delete_testbed()                    --  Delete the testbed created

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    run()                               --  Run function of this test case
"""

import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Kubernetes.constants import KubernetesAdditionalSettings
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes import KubernetesUtils
from AutomationUtils import machine
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Class to validate Helm apps.
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes Helm chart Validation"
        self.utils = TestCaseUtils(self)
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.proxy_obj = None
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
        self.helm_operator_name = None
        self.helm_operator_namespace = None
        self.repo_name = None
        self.repo_path = None
        self.content = []
        self.backup_content = None
        self.restore_content = None
        self.content_at_source_after_backup = None
        self.content_at_source_after_oop_restore_with_overwrite = None
        self.content_at_source_after_oop_restore_without_overwrite = None
        self.original_content = None
        self.content_at_source_after_deleting_destination = None

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
        self.helm_operator_name = self.tcinputs.get('HelmOperatorName', 'mysql')
        self.helm_operator_namespace = self.namespace
        self.repo_name = 'k8s-auto-{}'.format(self.id)
        self.repo_path = self.tcinputs.get('HelmRepoPath', "https://charts.bitnami.com/bitnami")
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", automation_config.ACCESS_NODE)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        self.controller = self.commcell.clients.get(self.access_node)
        self.controller_id = int(self.controller.client_id)
        self.proxy_obj = machine.Machine(self.controller)

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
            4. Create namespace and restore namespace
            5. Create PVC
            6. Create test Pod
            7. Generate random data in Pod
        """
        self.log.info(
            f"Removing additional setting [{KubernetesAdditionalSettings.HELM_BACKUP.value}] if present on access node"
        )
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.HELM_BACKUP.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.HELM_BACKUP.value,

            )

            self.log.info(f"Successfully removed additional setting [{KubernetesAdditionalSettings.HELM_BACKUP.value}]")
        else:
            self.log.info(f"Additional setting [{KubernetesAdditionalSettings.HELM_BACKUP.value}] not present")

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

        self.log.info(f"Deploying {self.helm_operator_name} application using Helm Chart")

        # Deploying Helm Apps
        self.kubehelper.deploy_helm_apps(
            self.helm_operator_name, self.helm_operator_namespace,
            repo_path=self.repo_path, repo_name=self.repo_name, kubeconfig_path=self.k8s_config,
            set_values=self.tcinputs.get("SetValues", [])
        )

        self.original_content = self.kubehelper.get_all_resources(
            namespace=self.namespace, label_selector=f"app.kubernetes.io/name={self.helm_operator_name}"
        )
        self.content.append(f"{self.namespace}/{self.helm_operator_name}")

        KubernetesUtils.add_cluster(
            self,
            self.clientName,
            self.api_server_endpoint,
            self.serviceaccount,
            self.servicetoken,
            self.access_node
        )
        # Adding additional Setting bK8sHelmChartBackup
        self.controller.add_additional_setting(

            KubernetesAdditionalSettings.CATEGORY.value,
            KubernetesAdditionalSettings.HELM_BACKUP.value,
            'BOOLEAN',
            'true'
        )
        time.sleep(100)

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
        self.kubehelper.cleanup_helm_apps(
            self.helm_operator_name, self.namespace, kubeconfig_path=self.k8s_config
        )
        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)

        crb_name = self.testbed_name + '-crb'
        # Delete cluster role binding

        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)
        self.log.info(
            f"Removing additional setting [{KubernetesAdditionalSettings.HELM_BACKUP.value}] if present on access node"
        )
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.HELM_BACKUP.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.HELM_BACKUP.value,

            )

            self.log.info(f"Successfully removed additional setting [{KubernetesAdditionalSettings.HELM_BACKUP.value}]")
        else:
            self.log.info(f"Additional setting [{KubernetesAdditionalSettings.HELM_BACKUP.value}] not present")

    @TestStep()
    def check_if_source_deleted(self):
        """Deleting helm apps in destination namespace and verifying the status of source namespace
        """

        self.kubehelper.cleanup_helm_apps(
            self.helm_operator_name, self.restore_namespace, kubeconfig_path=self.k8s_config
        )
        self.log.info("Successfully uninstalled Helm chart on restore namespace ")
        self.log.info("Verifying if Source charts are deleted or not ... ")
        self.content_at_source_after_deleting_destination = self.kubehelper.get_all_resources(
            namespace=self.namespace, label_selector=f"app.kubernetes.io/name={self.helm_operator_name}"
        )

        if self.content_at_source_after_deleting_destination == self.original_content:
            self.log.info(
                f"source : {self.content_at_source_after_deleting_destination}\n original : {self.original_content}\n"
                f"Verification Successful."
                f" Helm charts and Helm apps are present in source after Deleting Helm charts and apps at destination")
        else:
            raise Exception(
                f"source : {self.content_at_source_after_deleting_destination}\n original : {self.original_content}\n"
                f" Source Helm charts are deleted are after deleting Helm Charts at destination...")

    @TestStep()
    def backup_step(self, backup_type="INCREMENTAL"):
        """Initiate Backup Job for Namespace containing HelmChart with regkey bK8sHelmChartBackup : true
        """
        self.kubehelper.backup(backup_type=backup_type)
        self.log.info("Verify if backed up application is a HelmChart")

        app_list, app_id_dict = self.subclient.browse()
        app_id = app_id_dict['\\' + self.helm_operator_name]['snap_display_name']

        if 'HelmChart' not in app_id:
            raise Exception("Application not backed up as type HelmChart ")
        else:
            self.log.info("Application successfully backed up as HelmChart type")

        self.content_at_source_after_backup = self.kubehelper.get_all_resources(
            namespace=self.namespace, label_selector=f"app.kubernetes.io/name={self.helm_operator_name}"
        )
        self.kubehelper.validate_data(self.content_at_source_after_backup, self.original_content)
        self.log.info("Content at Source after and before backup is same")
        self.log.info("Run Backup Step and Validation complete")
        self.log.info(
            f"Removing additional setting [{KubernetesAdditionalSettings.HELM_BACKUP.value}] if present on access node"
        )
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.HELM_BACKUP.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.HELM_BACKUP.value,

            )

            self.log.info(f"Successfully removed additional setting [{KubernetesAdditionalSettings.HELM_BACKUP.value}]")
        else:
            self.log.info(f"Additional setting [{KubernetesAdditionalSettings.HELM_BACKUP.value}] not present")
        self.log.info("Waiting for 1 minute...")
        time.sleep(60)

    @TestStep()
    def backup_step_with_regkey(self, backup_type="INCREMENTAL"):

        """Initiate Backup Job for Namespace containing HelmChart with regkey bK8sHelmChartBackup : false
        """
        self.controller.add_additional_setting(
            KubernetesAdditionalSettings.CATEGORY.value,
            KubernetesAdditionalSettings.HELM_BACKUP.value,
            'BOOLEAN',
            'false'
        )

        # self.log.info("Waiting for 5 minutes...")
        time.sleep(100)
        self.log.info("REGKEY bK8sHelmChartBackup : false added in the access node")
        KubernetesUtils.add_application_group(
            self,
            content=self.content,
            plan=self.plan,
            name=self.subclientName + '-2',
        )
        self.subclientName = self.subclientName + '-2'
        self.kubehelper.source_vm_object_creation(self)
        self.log.info("Waiting for 1 minute...")
        time.sleep(60)

        self.kubehelper.backup(backup_type=backup_type)
        self.log.info("Verify if backed up application is a HelmChart")

        app_list, app_id_dict = self.subclient.browse()
        app_id = app_id_dict['\\' + self.helm_operator_name]['snap_display_name']
        self.log.info(f"------------app id : {app_id}---------")

        if 'HelmChart' in app_id:
            raise Exception("Application backed up as type HelmChart even when the REGKEY is present")

        else:
            self.log.info("Application successfully backed up (NOT AS HELM CHART TYPE)")

        self.content_at_source_after_backup = self.kubehelper.get_all_resources(
            namespace=self.namespace, label_selector=f"app.kubernetes.io/name={self.helm_operator_name}"
        )
        self.kubehelper.validate_data(self.content_at_source_after_backup, self.original_content)
        self.log.info("Content at Source after and before backup is same")
        self.log.info("Run Backup Step with REGKEY and Validation complete")
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.HELM_BACKUP.value
        ):
            self.controller.delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.HELM_BACKUP.value,

            )

            self.log.info(f"Successfully removed additional setting [{KubernetesAdditionalSettings.HELM_BACKUP.value}]")
        else:
            self.log.info(f"Additional setting [{KubernetesAdditionalSettings.HELM_BACKUP.value}] not present")
        self.log.info("Waiting for 1 minute...")
        time.sleep(60)

    @TestStep()
    def restore_without_overwrite(self):
        """Perform HelmChart restore to restore namespace without overwrite enabled
        """
        self.kubehelper.run_restore_validate(
            self.clientName,
            self.storageclass,
            validate=False,
            overwrite=False,
            restore_namespace=self.restore_namespace
        )
        self.content_at_source_after_oop_restore_without_overwrite = self.kubehelper.get_all_resources(
            namespace=self.namespace, label_selector=f"app.kubernetes.io/name={self.helm_operator_name}"
        )
        self.restore_content = self.kubehelper.get_all_resources(
            namespace=self.restore_namespace, label_selector=f"app.kubernetes.io/name={self.helm_operator_name}"
        )
        self.kubehelper.validate_data(self.content_at_source_after_oop_restore_without_overwrite, self.original_content)
        self.log.info("Resource validation successful. Resources at Source have not been deleted and remains unchanged")
        self.kubehelper.validate_data(self.original_content, self.restore_content)
        self.log.info("Run Restore without overwrite Step complete")

    @TestStep()
    def restore_with_overwrite(self):
        """Perform HelmChart Out of place restore to restore namespace with overwrite enabled
        """
        self.kubehelper.run_restore_validate(
            self.clientName,
            self.storageclass,
            validate=False,
            overwrite=True,
            restore_namespace=self.restore_namespace
        )
        self.content_at_source_after_oop_restore_with_overwrite = self.kubehelper.get_all_resources(
            namespace=self.namespace, label_selector=f"app.kubernetes.io/name={self.helm_operator_name}"
        )
        self.restore_content = self.kubehelper.get_all_resources(
            namespace=self.restore_namespace, label_selector=f"app.kubernetes.io/name={self.helm_operator_name}"
        )

        self.kubehelper.validate_data(self.content_at_source_after_oop_restore_with_overwrite, self.original_content)
        self.log.info("Resource validation successful. Resources at Source have not been deleted and remains unchanged")
        self.kubehelper.validate_data(self.original_content, self.restore_content)
        self.log.info("Run Restore with overwrite Step complete")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Run Full Job before verifying restore
            self.log.info("------------------------PHASE 1 WITHOUT REGKEY-----------------------------")
            self.backup_step('FULL')
            # Run restore without overwrite
            self.restore_without_overwrite()
            self.log.info("Waiting for 3 minutes....")
            time.sleep(200)

            # # Run restore with overwrite
            self.restore_with_overwrite()
            self.log.info("Waiting for 3 minutes....")
            time.sleep(200)

            self.log.info("Comparing the Resources in Backup and Restore destinations with Helm List Command")
            self.kubehelper.compare_with_helm_list(self.namespace, self.restore_namespace, self.k8s_config)
            self.check_if_source_deleted()
            self.log.info("Deleting and Recreating Restore Namespace")
            self.kubehelper.delete_cv_namespace(self.restore_namespace)
            self.kubehelper.create_cv_namespace(self.restore_namespace)

            self.log.info("------------------------PHASE 2 WITH REGKEY-----------------------------")
            self.backup_step_with_regkey('FULL')
            # # Run restore without overwrite
            self.restore_without_overwrite()
            self.log.info("Waiting for 3 minutes....")
            time.sleep(200)
            # # Run restore with overwrite
            self.restore_with_overwrite()
            self.log.info("Waiting for 3 minutes....")
            time.sleep(200)
            self.log.info("Comparing the Resources in Backup and Restore destinations with Helm List Command")
            self.kubehelper.compare_with_helm_list(self.namespace, self.restore_namespace, self.k8s_config)
            self.check_if_source_deleted()

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step -- Delete testbed, delete client ")
            self.delete_testbed()
            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")
