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

    verify_inplace_restore_step()       --  Verify inplace restore job

    run()                               --  Run function of this test case
"""

import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Kubernetes.constants import KubernetesAdditionalSettings
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
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create Namespace, Pod, PVC, deployment, orphan secrets, configmaps, serviceaccounts,etc for testbed
    5. Create a Kubernetes client with proxy provided
    6. Create application group for kubernetes with namespace as content
    7. Add content in PVC for full backup.
    8. Initiate Full Backup for App group created and verify job completed
    9. Add content and move content, create more orphan entities for Incremental backup.
    10. Initiate Incremental Backup for App group created and verify job completed
    11. Initiate Out-of-place Namespace-level Restore and verify job completed
    12. Validate restored files checksum and restored resources
    13. Initiate in-place namespace-level restore and verify job completed
    14. Validate restored files checksum and restored resources
    15. Cleanup testbed
    16. Cleanup clients created.
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.group = None
        self.name = "Kubernetes Restore Modifier Focused Testcase - Default 'ServiceInstance' and 'ServiceBinding'" \
                    " modifiers"
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
        self.proxy_obj = None
        self.resources_before_backup = None
        self.resources_after_restore = None

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
        self.group = 'servicecatalog.io'

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

        service_binding_object = {
            "apiVersion": "servicecatalog.io/v1",
            "kind": "ServiceBinding",
            "metadata": {
                "name": "svc-bind"
            },
            "spec": {
                "externalID": "old-value",
                "serviceClassRef": "old-value",
                "servicePlanRef": "old-value",
                "userInfo": "old-value"
            }
        }
        service_instance_object = {
            "apiVersion": "servicecatalog.io/v1",
            "kind": "ServiceInstance",
            "metadata": {
                "name": "svc-inst",
                "labels": {
                    "key1": "value1"
                }
            },
            "spec": {
                "externalID": "old-value",
                "serviceClassRef": "old-value",
                "servicePlanRef": "old-value",
                "userInfo": "old-value"
            }
        }

        # Create ServiceBinding CRO
        self.kubehelper.create_cv_custom_resource(
            group=self.group,
            version='v1',
            plural='servicebindings',
            namespace=self.namespace,
            body=service_binding_object
        )

        # Create Service Instance CRO
        self.kubehelper.create_cv_custom_resource(
            group=self.group,
            version='v1',
            plural='serviceinstances',
            namespace=self.namespace,
            body=service_instance_object,

        )

        self.content.append(self.namespace)

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
    def verify_modifier(self):
        """
        Verifies modifier action on servicebinding and serviceinstance CR
        """

        svc_bind = self.kubehelper.get_custom_object(
            group=self.group,
            version='v1',
            namespace=self.restore_namespace,
            plural='servicebindings',
            name='svc-bind'
        )

        svc_inst = self.kubehelper.get_custom_object(
            group=self.group,
            version='v1',
            namespace=self.restore_namespace,
            plural='serviceinstances',
            name='svc-inst'
        )

        if 'externalID' in svc_bind['spec'].keys() or 'userInfo' in svc_bind['spec'].keys():
            raise KubernetesException(
                'ValidationOperations', '109', f'ServiceBinding not appropriately modified [{svc_bind}]'
            )
        else:
            self.log.info("Validation successful. ServiceBinding appropriately modified")
        if 'externalID' in svc_inst['spec'].keys()\
                or 'labels' in svc_inst['metadata'].keys()\
                or 'userInfo' in svc_inst['spec'].keys()\
                or 'serviceClassRef' in svc_inst['spec'].keys()\
                or 'servicePlanRef' in svc_inst['spec'].keys():
            raise KubernetesException(
                'ValidationOperations', '109', f'ServiceInstance not appropriately modified [{svc_inst}]'
            )
        else:
            self.log.info("Validation successful. ServiceInstance appropriately modified")

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
    def check_and_enable_regkey(self):
        """Check for regkey remove if present,
            Then re-add it
        """
        self.log.info(
            f"Step 0 - Check and add additional setting [{KubernetesAdditionalSettings.RESTORE_MODIFIER.value}]"
        )
        if self.proxy_obj.check_registry_exists(
                KubernetesAdditionalSettings.CATEGORY.value, KubernetesAdditionalSettings.RESTORE_MODIFIER.value
        ):
            self.commcell.clients.get(self.access_node).delete_additional_setting(
                category=KubernetesAdditionalSettings.CATEGORY.value,
                key_name=KubernetesAdditionalSettings.SERVICE_CATALOG_MODIFIER.value,
            )
            self.log.info(
                f"Successfully deleted additional setting [{KubernetesAdditionalSettings.RESTORE_MODIFIER.value}]"
            )

        self.log.info(f"Adding additional setting [{KubernetesAdditionalSettings.SERVICE_CATALOG_MODIFIER.value}]"
                      f" with value [1]")

        self.commcell.clients.get(self.access_node).add_additional_setting(
            category=KubernetesAdditionalSettings.CATEGORY.value,
            key_name=KubernetesAdditionalSettings.SERVICE_CATALOG_MODIFIER.value,
            data_type=KubernetesAdditionalSettings.BOOLEAN.value,
            value="true"
        )

        self.log.info(
            f"Successfully added additional setting [{KubernetesAdditionalSettings.SERVICE_CATALOG_MODIFIER.value}]"
        )

    @TestStep()
    def verify_full_ns_backup(self):
        """Verify FULL Backup of entire namespace as content
        """
        self.log.info('Step 1 -- Run FULL Backup job with Namespace as content')
        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        self.kubehelper.backup("FULL")
        self.log.info('FULL Backup job step with Namespace as content successfully completed')

    @TestStep()
    def verify_namespace_level_oop_restore(self):
        """Verify Namespace-level restore out-of-place
        """
        self.log.info('Step 2 -- Run Namespace-level restore out-of-place')
        restore_namespace_map = {
            self.namespace: self.restore_namespace
        }
        self.kubehelper.namespace_level_restore(
            namespace_list=self.content,
            restore_name_map=restore_namespace_map,
            overwrite=False
        )
        self.log.info('Namespace-level restore completed. Proceeding with Modifier validation')
        self.verify_modifier()
        self.log.info('Namespace-level restore out-of-place step successfully completed')

    @TestStep()
    def verify_namespace_level_ip_overwrite(self):
        """Verify Namespace-level restore in-place with overwrite
        """
        self.log.info('Step 3 -- Run Namespace-level restore out-of-place with overwrite')
        self.kubehelper.namespace_level_restore(
            namespace_list=self.content,
            in_place=True
        )
        # Check whether ServiceBroker and ServiceInstance CRO's Have been correctly modified

        self.log.info('Namespace-level restore in-place with overwrite step successfully completed')

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Step 1 - Check controller for Regkey, delete if present and re-add with AMDOCS value
            self.check_and_enable_regkey()

            # Step 2 - Take FULL Backup of App Group
            self.verify_full_ns_backup()

            # Step 3 - Perform OOP Restore of Namespace and validate Modifier action
            self.verify_namespace_level_oop_restore()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 6 -- Delete testbed, delete client ")
            self.delete_testbed()
