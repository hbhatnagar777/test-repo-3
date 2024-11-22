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
from Kubernetes.RestoreModifierHelper import RestoreModifierHelper
from Kubernetes.constants import RestoreModifierConstants
from Kubernetes.exceptions import KubernetesException
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
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
    4. Validate restored resources have modifiers of ADD and DELETE applied
    5. Cleanup testbed
    """
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Kubernetes Restore Modifier Focused Testcase - 'name', 'namespace', 'kind', 'labels'" \
                    " Selector with 'Add' and 'Delete' Modifier"
        self.utils = TestCaseUtils(self)
        self.k8s_helper = None
        self.server_name = None
        self.admin_console = None
        self.browser = None
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
        self.orphan_namespace = None
        self.restore_namespace = None
        self.restore_orphan_namespace = None
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

    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.namespace = self.testbed_name
        self.orphan_namespace = self.testbed_name + '-orphans'
        self.restore_namespace = self.namespace + "-rst"
        self.restore_orphan_namespace = self.orphan_namespace + "-rst"
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

        self.kubehelper_src = KubernetesHelper(self)
        self.kubehelper_dest = KubernetesHelper(self)
        self.mods_helper = RestoreModifierHelper()

        # Initializing objects using KubernetesHelper
        self.kubehelper_src.load_kubeconfig_file(self.k8s_config)
        self.kubehelper_dest.load_kubeconfig_file(self.k8s_dest_config)
        self.api_server_endpoint = self.kubehelper_src.get_api_server_endpoint()
        self.api_server_endpoint_2 = self.kubehelper_dest.get_api_server_endpoint()

    def create_orphan_resources(self):
        """Create orphan resources in namespace
        """
        self.log.info(
            f'Creating some orphan resources in namespace [{self.orphan_namespace}] '
            f'on cluster [{self.api_server_endpoint}]'
        )
        orphan_secret = self.testbed_name + '-orphan-secret'
        orphan_cm = self.testbed_name + '-orphan-cm'
        orphan_svc = self.testbed_name + '-orphan-svc'
        orphan_sa = self.testbed_name + '-orphan-sa'
        self.kubehelper_src.create_cv_secret(orphan_secret, self.orphan_namespace)
        self.kubehelper_src.create_cv_configmap(orphan_cm, self.orphan_namespace)
        self.kubehelper_src.create_cv_svc(orphan_svc, self.orphan_namespace, selector={self.namespace: self.namespace})
        self.kubehelper_src.create_cv_serviceaccount(orphan_sa, self.orphan_namespace)

        # Creating another orphan Secret
        orphan_secret = self.testbed_name + '-orphan-secret-2'
        self.kubehelper_src.create_cv_secret(orphan_secret, self.orphan_namespace)

    @TestStep()
    def create_restore_modifiers(self):
        """Create restore modifiers on cluster
        """

        self.log.info("Step 1.5 - Create Restore Modifier CRO on the destination cluster")
        # Creating cv-config Namespace
        self.log.info(
            f"Creating namespace [{RestoreModifierConstants.NAMESPACE.value}] for RestoreModifiers "
            f"on cluster [{self.api_server_endpoint_2}]"
        )
        self.kubehelper_dest.create_cv_namespace(name=RestoreModifierConstants.NAMESPACE.value, delete=False)

        # Creating RestoreModifier objects
        # Add new label to all Service
        add_selector_id_kind_only = self.testbed_name + '-add-kind-' + get_random_string()
        add_selector_id_kind_name = self.testbed_name + '-add-kind-name-' + get_random_string()
        add_selector_id_kind_name_ns = self.testbed_name + '-add-kind-name-ns-' + get_random_string()
        delete_selector_id_kind_ns = self.testbed_name + '-delete-kind-ns-' + get_random_string()
        delete_selector_id_kind_ns_label = self.testbed_name + '-delete-kind-ns-label-' + get_random_string()

        self.log.info(
            f"Generating selector with ID [{add_selector_id_kind_only}]: Match with all resources from all namespaces "
            f"of Kind [Service]"
        )
        self.mods_helper.generate_selector(
            selector_id=add_selector_id_kind_only,
            kind='Service'
        )

        self.log.info(
            f"Generating selector with ID [{add_selector_id_kind_name}]: Match with resources with Name"
            f" [{self.testbed_name + '-orphan-cm'}] from all namespaces of Kind [ConfigMap]"
        )
        self.mods_helper.generate_selector(
            selector_id=add_selector_id_kind_name,
            kind='ConfigMap',
            name=self.testbed_name + '-orphan-cm'
        )

        matching_namespace = self.namespace
        self.log.info(
            f"Generating selector with ID [{add_selector_id_kind_name_ns}]: Match with resources with Name"
            f" [{self.testbed_name + '-pod'}] from Namespace [{matching_namespace}] of Kind [Pod]"
        )
        self.mods_helper.generate_selector(
            selector_id=add_selector_id_kind_name_ns,
            kind='Pod',
            name=self.testbed_name + '-pod',
            namespace=matching_namespace
        )

        self.log.info(
            f"Generating modifier with ID [{add_selector_id_kind_only}]: "
            f"Add new label [{'/metadata/labels/' + self.testbed_name + ':' + add_selector_id_kind_only}]"
        )
        self.mods_helper.generate_add_modifier(
            selector_id=add_selector_id_kind_only,
            path='/metadata/labels/' + self.testbed_name,
            value=add_selector_id_kind_only
        )

        self.log.info(
            f"Generating modifier with ID [{add_selector_id_kind_name}]: "
            f"Add new data field [{'/data/' + self.testbed_name + ':' + add_selector_id_kind_name}]"
        )
        self.mods_helper.generate_add_modifier(
            selector_id=add_selector_id_kind_name,
            path='/data/' + self.testbed_name,
            value=add_selector_id_kind_name
        )

        image = automation_config.IMAGE_REGISTRY
        manifest = [{
                'name': self.testbed_name,
                'image': (image + '/' if image else "") + 'busybox',
                'command': ["echo", "hello"]
            }]
        self.log.info(
            f"Generating modifier with ID [{add_selector_id_kind_name_ns}]: "
            f"Add new initContainer section with manifest [{manifest}]"
        )
        self.mods_helper.generate_add_modifier(
            selector_id=add_selector_id_kind_name_ns,
            path='/spec/initContainers',
            value=manifest
        )

        # Create RestoreModifier CR
        rm_json = self.mods_helper.generate_restore_modifier(
            name=self.testbed_name + '-add'
        )
        self.log.info(f"Created RestoreModifier [{self.testbed_name + '-add'}] with JSON : [{rm_json}]")
        self.mods_helper.clear_all_selectors()
        self.mods_helper.clear_all_modifiers()

        matching_namespace = self.orphan_namespace
        self.log.info(
            f"Generating selector with ID [{delete_selector_id_kind_ns}]: Match with all resources "
            f"from Namespace [{matching_namespace}] of Kind [Secret]"
        )
        self.mods_helper.generate_selector(
            selector_id=delete_selector_id_kind_ns,
            kind='Secret',
            namespace=self.orphan_namespace
        )

        matching_namespace = self.namespace
        labels = {'testbed': self.testbed_name}
        self.log.info(
            f"Generating selector with ID [{delete_selector_id_kind_ns_label}]: Match with all resources "
            f"from Namespace [{matching_namespace}] of Kind [Deployment] having label [{labels}]"
        )
        self.mods_helper.generate_selector(
            selector_id=delete_selector_id_kind_ns_label,
            kind='Deployment',
            namespace=matching_namespace,
            labels=labels
        )

        self.log.info(
            f"Generating modifier with ID [{delete_selector_id_kind_ns}]: "
            f"Delete 'data' field from matching resources"
        )
        self.mods_helper.generate_delete_modifier(
            selector_id=delete_selector_id_kind_ns,
            path='/data'
        )

        self.log.info(
            f"Generating modifier with ID [{delete_selector_id_kind_ns_label}]: "
            f"Delete label key [/metadata/labels/testbed] from matching resources"
        )
        self.mods_helper.generate_delete_modifier(
            selector_id=delete_selector_id_kind_ns_label,
            path='/metadata/labels/testbed'
        )
        rm_json = self.mods_helper.generate_restore_modifier(
            name=self.testbed_name + '-delete'
        )
        self.log.info(f"Create RestoreModifier [{self.testbed_name + '-delete'}] with JSON : [{rm_json}]")

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
        self.kubehelper_src.create_cv_namespace(self.orphan_namespace)

        # Create Service
        svc_name = self.testbed_name + '-svc'
        self.kubehelper_src.create_cv_svc(svc_name, self.namespace)

        # Creating test pod
        secret_name = self.testbed_name + '-secret'
        config_name = self.testbed_name + '-cm'
        self.kubehelper_src.create_cv_secret(secret_name, self.namespace)
        self.kubehelper_src.create_cv_configmap(config_name, self.namespace)

        pod_name = self.testbed_name + '-pod'
        self.kubehelper_src.create_cv_pod(
            pod_name, self.namespace, secret=secret_name, configmap=config_name
        )
        time.sleep(30)

        deployment_name = self.testbed_name + '-deployment'
        self.kubehelper_src.create_cv_deployment(deployment_name, self.namespace, labels={'testbed': self.testbed_name})

        # Create orphan resources in the namespace
        self.create_orphan_resources()
        orphan_sa_2 = self.testbed_name + '-orphan-sa2'
        orphan_crb = self.testbed_name + '-orphan-crb'
        self.kubehelper_src.create_cv_serviceaccount(orphan_sa_2, self.namespace)
        self.kubehelper_src.create_cv_clusterrolebinding(orphan_crb, orphan_sa_2, self.namespace, 'view')

        self.content.append(self.namespace)
        self.content.append(self.orphan_namespace)

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
        self.kubehelper_src.delete_cv_namespace(self.orphan_namespace)
        self.kubehelper_dest.delete_cv_namespace(self.restore_namespace)
        self.kubehelper_dest.delete_cv_namespace(self.restore_orphan_namespace)

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
            raise CVTestCaseInitFailure(_exception) from _exception

    @TestStep()
    def verify_full_ns_backup(self):
        """Verify FULL Backup of entire namespace as content
        """
        self.log.info('Step 1 -- Run FULL Backup job with Namespace as content')
        self.kubehelper_src.backup("FULL")
        self.log.info('FULL Backup job step with Namespace as content successfully completed')

    @TestStep()
    def verify_namespace_level_oop_restore_from_ui(self, source_modifier=True):
        """Performs OOP restore after picking restore modifiers in UI"""

        self.log.info(f'Step 2 -- Run Namespace-level restore out-of-place from cluster '
                      f'[{self.clientName}] to cluster [{self.destclientName}]')
        restore_namespace_map = {
            self.namespace: self.restore_namespace,
            self.orphan_namespace: self.restore_orphan_namespace
        }

        self.connect_to_command_centre()
        self.k8s_helper.run_namespace_restore_job(
            cluster_name=self.clientName,
            app_group_name=self.subclientName,
            restore_namespace_map=restore_namespace_map,
            namespace_list=[self.namespace, self.orphan_namespace],
            destination_cluster=self.destclientName,
            inplace=False,
            unconditional_overwrite=True,
            modifier_list=[self.testbed_name + '-add', self.testbed_name + '-delete'],
            source_modifier=source_modifier,
            access_node=self.access_node
        )
        self.browser.close_silently(self.browser)

        self.log.info('Namespace-level restore out-of-place step successfully completed')

        self.restored_manifests[self.restore_namespace] = self.kubehelper_dest.get_all_resources(
            namespace=self.restore_namespace, return_json=True
        )
        self.restored_manifests[self.restore_orphan_namespace] = self.kubehelper_dest.get_all_resources(
            namespace=self.restore_orphan_namespace, return_json=True
        )

    @TestStep()
    def verify_namespace_level_oop_restore(self):
        """Verify Namespace-level restore out-of-place
        """
        self.log.info(f'Step 2 -- Run Namespace-level restore out-of-place from cluster '
                      f'[{self.clientName}] to cluster [{self.destclientName}]')
        restore_namespace_map = {
            self.namespace: self.restore_namespace,
            self.orphan_namespace: self.restore_orphan_namespace
        }
        self.kubehelper_src.namespace_level_restore(
            client_name=self.destclientName,
            namespace_list=self.content,
            restore_name_map=restore_namespace_map
        )
        self.log.info('Namespace-level restore out-of-place step successfully completed')
        self.restored_manifests[self.restore_namespace] = self.kubehelper_dest.get_all_resources(
            namespace=self.restore_namespace, return_json=True
        )
        self.restored_manifests[self.restore_orphan_namespace] = self.kubehelper_dest.get_all_resources(
            namespace=self.restore_orphan_namespace, return_json=True
        )

    @TestStep()
    def validate_restored_resources(self):
        """Validate resources are restored with correct transformation
        """

        self.log.info('Step 3 -- Validate resources for transformation after restore')
        # Validate transformations in both namespaces first on Service
        for ns in [self.restore_namespace, self.restore_orphan_namespace]:
            for manifest in self.restored_manifests[ns]["Service"]:
                if self.testbed_name not in manifest.metadata.labels:
                    raise KubernetesException(
                        'ValidationOperations', '109', f'Service [{manifest.metadata.name}] does not have label added'
                                                       f' by Add modifier'
                    )
        else:
            self.log.info(
                "Validated ADD Modifier to add labels to all Services resources in all namespaces"
            )

        # Validate data/testbed_name field added in configMap
        for manifest in self.restored_manifests[self.restore_orphan_namespace]["ConfigMap"]:
            if manifest.metadata.name == (self.testbed_name + '-orphan-cm') and self.testbed_name not in manifest.data:
                raise KubernetesException(
                    'ValidationOperations', '109', f'ConfigMap [{manifest.metadata.name}] does not have data added'
                                                   f' by Add modifier'
                )
        else:
            self.log.info(
                "Validated ADD Modifier to add data content to specific named ConfigMap resource in specific namespace"
            )
        # Validate initContainers in restored Pod
        for manifest in self.restored_manifests[self.restore_namespace]["Pod"]:
            if manifest.metadata.name == (self.testbed_name + '-pod') and not manifest.spec.init_containers:
                raise KubernetesException(
                    'ValidationOperations', '109', f'Pod [{manifest.metadata.name}] does not have initContainers added'
                                                   f' by Add modifier'
                )
        else:
            self.log.info(
                "Validated ADD Modifier to add initContainer node to specific named Pod resource"
            )

        # Validate deleted field data in all Secrets of restore orphan namespace
        for manifest in self.restored_manifests[self.restore_orphan_namespace]["Secret"]:
            if manifest.type and manifest.type == 'kubernetes.io/service-account-token':
                continue
            if manifest.data:
                raise KubernetesException(
                    'ValidationOperations', '109', f'Secret [{manifest.metadata.name}] has data field not delete'
                                                   f' by Delete modifier'
                )
        else:
            self.log.info(
                "Validated DELETE Modifier to remove all data fields from all Secret resources in specific namespace"
            )

        # Validate deleted label key in all Deployments of restore namespace
        label_key = 'testbed'
        for manifest in self.restored_manifests[self.restore_namespace]["Deployment"]:
            if label_key in manifest.metadata.labels:
                raise KubernetesException(
                    'ValidationOperations', '109', f'Deployment [{manifest.metadata.name}] has label [{label_key}] not'
                                                   f'  deleted by Delete modifier'
                )
        else:
            self.log.info(
                "Validated DELETE Modifier to remove label key from Deployment with label in specific namespace"
            )

        self.log.info("RestoreModifiers validation complete")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper_src.source_vm_object_creation(self)

            # Step 1 - Take FULL Backup of App Group
            self.verify_full_ns_backup()

            # Step 1.5 Create restore modifiers
            self.create_restore_modifiers()

            # Step 2 - Perform cross-cluster OOP restore of Namespace using destination modifiers and validate
            self.verify_namespace_level_oop_restore_from_ui(source_modifier=False)
            self.validate_restored_resources()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 4 -- Delete testbed, delete client")
            self.delete_testbed()
