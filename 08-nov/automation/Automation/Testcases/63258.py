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
    __init__                            --  initialize TestCase class

    setup                               --  setup method for test case

    tear_down                           --  tear down method for testcase

    init_inputs                         --  Initialize objects required for the testcase

    create_testbed                      --  Create the testbed required for the testcase

    delete_testbed                      --  Delete the testbed created

    verify_full_ns_backup               --  Add data and verify backup job

    verify_namespace_level_oop_restore  --  Verify out of place cross cluster restore job

    validate_restored_resources         --  Validate transformations on restored resources

    run                                 --  Run function of this test case
"""

import time
from AutomationUtils import config
from AutomationUtils.commonutils import get_random_string
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Kubernetes.RestoreModifierHelper import RestoreModifierHelper, SelectorCriteria
from Kubernetes.constants import RestoreModifierConstants
from Kubernetes.exceptions import KubernetesException
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVWebAutomationException
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes import KubernetesUtils
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform backups and namespace-level restores.
    This testcase does the following --
    1. Connect to Kubernetes cluster and created the testbed
    2. Initiate Full Backup for namespaces created and verify job completed
    3. Initiate Out-of-place Namespace-level Restore and verify job completed
    4. Validate restored resources have modifiers of MODIFY applied
    5. Cleanup testbed
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.k8s_helper = None
        self.admin_console = None
        self.browser = None
        self.depl_sa = None
        self.orphan_svc = None
        self.svc_name = None
        self.name = ("Kubernetes Restore Modifier Focused Testcase - "
                     "'field' Selector with 'Add', 'Delete' and 'Modify' Modifier")
        self.utils = TestCaseUtils(self)
        self.server_name = None
        self.kubehelper_src = None
        self.kubehelper_dest = None
        self.mods_helper = None
        self.api_server_endpoint = None
        self.api_server_endpoint_2 = None
        self.servicetoken = None
        self.servicetoken_2 = None
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
        self.proxy_obj = None
        self.agentName = "Virtual Server"
        self.instanceName = "Kubernetes"
        self.backupsetName = "defaultBackupSet"
        self.tcinputs = {
            'ConfigFile2': None
        }
        self.k8s_config = None
        self.k8s_dest_config = None
        self.driver = None
        self.plan = None
        self.storageclass = None
        self.content = []
        self.restored_manifests = {}
        self.secret_data = None

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
        self.k8s_dest_config = self.tcinputs.get('ConfigFile2')
        self.proxy_obj = Machine(self.commcell.clients.get(self.access_node))
        self.secret_data = "SomeData"

        self.kubehelper_src = KubernetesHelper(self)
        self.kubehelper_dest = KubernetesHelper(self)
        self.mods_helper = RestoreModifierHelper()

        # Initializing objects using KubernetesHelper
        self.kubehelper_src.load_kubeconfig_file(self.k8s_config)
        self.kubehelper_dest.load_kubeconfig_file(self.k8s_dest_config)
        self.api_server_endpoint = self.kubehelper_src.get_api_server_endpoint()
        self.api_server_endpoint_2 = self.kubehelper_dest.get_api_server_endpoint()

    @TestStep()
    def create_restore_modifiers(self):
        """Create restore modifiers on cluster
        """

        self.log.info("Step 1.5 - Create Restore Modifier CRO on the destination cluster")
        # Creating cv-config Namespace
        self.log.info(
            f"Creating namespace [{RestoreModifierConstants.NAMESPACE.value}] for RestoreModifiers "
            f"on cluster [{self.api_server_endpoint}]"
        )
        self.kubehelper_dest.create_cv_namespace(name=RestoreModifierConstants.NAMESPACE.value, delete=False)

        # Creating RestoreModifier objects
        selector_match_service_account = self.testbed_name + '-match-sa-' + get_random_string()
        selector_match_deployment = self.testbed_name + '-match-deploy-' + get_random_string()

        self.log.info(
            f"Generating selector with ID [{selector_match_service_account}]: Match with ServiceAccount resources "
            f"from namespace [{self.namespace}] with field selector [automountServiceAccountToken = False]"
        )
        self.mods_helper.generate_selector(
            selector_id=selector_match_service_account,
            kind='ServiceAccount',
            namespace=self.namespace,
            path="/automountServiceAccountToken",
            value=False
        )
        self.log.info(
            f"Generating modifier with ID [{selector_match_service_account}]: " +
            f"Add label 'tc63258=add-modifier-applied'"
        )
        self.mods_helper.generate_add_modifier(
            selector_id=selector_match_service_account,
            path=f'/metadata/labels/tc63258',
            value='add-modifier-applied'
        )

        self.log.info(
            f"Generating modifier with ID [{selector_match_service_account}]: " +
            f"Modify automountServiceAccountToken value to True "
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=selector_match_service_account,
            path=f'/automountServiceAccountToken',
            value=False,
            new_value=True,
            parameters="Exact"
        )

        self.log.info(
            f"Generating selector with ID [{selector_match_deployment}]: Match with Deployment "
            f"from namespace [{self.namespace}] if deployment replica is 1"
        )
        self.mods_helper.generate_selector(
            selector_id=selector_match_deployment,
            kind='Deployment',
            namespace=self.namespace,
            path="/spec/replicas/",
            value=1,
            exact=True,
            criteria=SelectorCriteria.CONTAINS
        )

        self.log.info(
            f"Generating modifier with ID [{selector_match_deployment}]: " +
            f"Modify replica to 2 if replica count is 1"
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=selector_match_deployment,
            path='/spec/replicas/',
            value=1,
            new_value=2,
            parameters='Exact'
        )

        self.log.info(
            f"Generating modifier with ID [{selector_match_deployment}]: " +
            f"Modify 'app' label to 'tdst'"
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=selector_match_deployment,
            path='/metadata/labels/app',
            value='est',
            new_value='gmt',
            parameters='Contains'
        )

        self.log.info(
            f"Generating modifier with ID [{selector_match_deployment}]: " +
            f"Modify 'app' label to 'tdst' at path spec.template.metadata.labels.app"
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=selector_match_deployment,
            path='/spec/template/metadata/labels/app',
            value='est',
            new_value='gmt',
            parameters='Contains'
        )

        self.log.info(
            f"Generating modifier with ID [{selector_match_deployment}]: " +
            f"Modify 'app' label to 'tdst' at path spec.selector.matchLabels.app"
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=selector_match_deployment,
            path='/spec/selector/matchLabels/app',
            value='est',
            new_value='gmt',
            parameters='Contains'
        )

        rm_json = self.mods_helper.generate_restore_modifier(
            name=self.testbed_name + '-63258'
        )
        self.log.info(f"Create RestoreModifier [{self.testbed_name + '-63258'}] with JSON : [{rm_json}]")

        # Creating CRs on cluster
        self.log.info(f"Creating RestoreModifier CRO on cluster [{self.api_server_endpoint_2}]")
        self.mods_helper.create_restore_modifier_crs(self.kubehelper_dest)

    @TestStep()
    def create_testbed(self):
        """Create cluster resources and clients for the testcase
        """

        self.log.info("Creating cluster resources...")

        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper_src.create_cv_serviceaccount(self.serviceaccount, sa_namespace)
        self.kubehelper_dest.create_cv_serviceaccount(self.serviceaccount, sa_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper_src.create_cv_clusterrolebinding(crb_name, self.serviceaccount, sa_namespace, cluster_role)
        self.kubehelper_dest.create_cv_clusterrolebinding(crb_name, self.serviceaccount, sa_namespace, cluster_role)

        time.sleep(30)
        self.servicetoken = self.kubehelper_src.get_serviceaccount_token(self.serviceaccount, sa_namespace)
        self.servicetoken_2 = self.kubehelper_dest.get_serviceaccount_token(self.serviceaccount, sa_namespace)

        # Creating testbed namespace if not exists
        self.kubehelper_src.create_cv_namespace(self.namespace)

        # Create Service
        self.svc_name = self.testbed_name + '-svc'
        self.kubehelper_src.create_cv_svc(self.svc_name, self.namespace)

        # Create SA for deployment
        self.depl_sa = self.testbed_name + '-depl-sa'
        self.kubehelper_src.create_cv_serviceaccount(self.depl_sa, self.namespace)
        self.kubehelper_src.create_cv_serviceaccount(self.testbed_name + '-depl-sa-modified', self.namespace)

        # Creating test pod
        secret_name = self.testbed_name + '-secret'
        config_name = self.testbed_name + '-cm'
        self.kubehelper_src.create_cv_secret(secret_name, self.namespace, labels={self.testbed_name: 'york'})
        self.kubehelper_src.create_cv_configmap(config_name, self.namespace)

        deployment_name = self.testbed_name + '-deployment'
        self.kubehelper_src.create_cv_deployment(
            deployment_name,
            self.namespace,
            service_account=self.depl_sa
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
        KubernetesUtils.add_cluster(
            self,
            self.destclientName,
            self.api_server_endpoint_2,
            self.serviceaccount,
            self.servicetoken_2,
            self.access_node,
            populate_client_obj=False
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
        self.mods_helper.delete_restore_modifier_crs(self.kubehelper_dest)
        self.kubehelper_src.delete_cv_namespace(self.namespace)
        self.kubehelper_dest.delete_cv_namespace(self.restore_namespace)

        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper_src.delete_cv_clusterrolebinding(crb_name)
        self.kubehelper_dest.delete_cv_clusterrolebinding(crb_name)

        orphan_crb = self.testbed_name + '-orphan-crb'
        self.kubehelper_src.delete_cv_clusterrolebinding(orphan_crb)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper_src.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)
        self.kubehelper_dest.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)
        KubernetesUtils.delete_cluster(self, self.destclientName)

    def connect_to_command_centre(self):
        """
         Connect to the command centre to perform restore
        """
        try:
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
            self.k8s_helper = K8sHelper(self.admin_console, self)

        except Exception as _exception:
            raise CVWebAutomationException(_exception) from _exception

    @TestStep()
    def verify_full_ns_backup(self):
        """Verify FULL Backup of entire namespace as content
        """
        self.log.info('Step 1 -- Run FULL Backup job with Namespace as content')
        self.kubehelper_src.backup("FULL")
        self.log.info('FULL Backup job step with Namespace as content successfully completed')

    @TestStep()
    def verify_namespace_level_oop_restore_from_ui(self):
        """Performs OOP restore after picking restore modifiers in UI"""

        self.log.info(f'Step 2 -- Run Namespace-level restore out-of-place from cluster '
                      f'[{self.clientName}] to cluster [{self.destclientName}]')
        restore_namespace_map = {
            self.namespace: self.restore_namespace
        }

        self.connect_to_command_centre()
        self.k8s_helper.run_namespace_restore_job(
            cluster_name=self.clientName,
            app_group_name=self.subclientName,
            restore_namespace_map=restore_namespace_map,
            namespace_list=[self.namespace],
            destination_cluster=self.destclientName,
            inplace=False,
            unconditional_overwrite=True,
            modifier_list=[self.testbed_name + '-63258'],
            source_modifier=False,
            access_node=self.access_node
        )
        self.browser.close_silently(self.browser)

        self.log.info('Namespace-level restore out-of-place step successfully completed')

        self.restored_manifests = self.kubehelper_dest.get_all_resources(
            namespace=self.restore_namespace, return_json=True
        )

    @TestStep()
    def validate_restored_resources(self):
        """Validate resources are restored with correct transformation
        """

        self.log.info('Step 3 -- Validate resources for transformation after restore')
        for manifest in self.restored_manifests["ServiceAccount"]:
            if (manifest.metadata.labels.get("tc63258", "")
                    and manifest.metadata.labels.get("tc63258", "") == "add-modifier-applied"):
                self.log.info(
                    f"Validated ADD Modifier to add label 'tc63258=add-modifier-applied' on ServiceAccount in namespace"
                    + f" [{self.namespace}]"
                )
            else:
                raise KubernetesException(
                    'ValidationOperations', '109', f"ServiceAccount [{manifest.metadata.name}] does not have"
                                                   f" added label 'tc63258=add-modifier-applied'"
                )

            if manifest.automount_service_account_token:
                self.log.info(
                    f"Validated MODIFY Modifier to modify automountServiceAccountToken to True"
                    + f" on ServiceAccount in namespace[{self.namespace}]"
                )
            else:
                raise KubernetesException(
                    'ValidationOperations', '109', f"ServiceAccount [{manifest.metadata.name}] does not have modified "
                                                   f"value for automountServiceAccountToken"
                )

        for manifest in self.restored_manifests["Deployment"]:
            if manifest.spec.replicas != 2:
                raise KubernetesException(
                    'ValidationOperations', '109', f'Deployment [{manifest.metadata.name}] does not expected replica'
                                                   f' modified by MODIFY modifier'
                )

            if not manifest.metadata.labels.get("app", "") == "tgmt":
                raise KubernetesException(
                    'ValidationOperations', '109', f'Deployment [{manifest.metadata.name}] does not have modified label'
                                                   f' in metadata.labels'
                )

            if not manifest.spec.template.metadata.labels.get("app", "") == "tgmt":
                raise KubernetesException(
                    'ValidationOperations', '109', f'Deployment [{manifest.metadata.name}] does not have modified label'
                                                   f' in metadata.spec.template.labels'
                )

            if not manifest.spec.selector.match_labels.get("app", "") == "tgmt":
                raise KubernetesException(
                    'ValidationOperations', '109', f'Deployment [{manifest.metadata.name}] does not have modified label'
                                                   f' in metadata.spec.selector.matchLabels'
                )
        else:
            self.log.info("Validated DELETE and MODIFY Modifiers on Deployment")

        self.log.info("RestoreModifiers validation complete")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper_src.source_vm_object_creation(self)

            # Step 1 - Take FULL Backup of App Group
            self.verify_full_ns_backup()

            # Step 1.5 - Create restore modifiers
            self.create_restore_modifiers()

            # Step 2 - Perform cross-cluster OOP Restore of Namespace
            self.verify_namespace_level_oop_restore_from_ui()

            # Step 3 - Validate restored resources in restored namespaces
            self.validate_restored_resources()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 4 -- Delete testbed, delete client")
            self.delete_testbed()