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
        self.name = "Kubernetes Restore Modifier Focused Testcase - 'name'," \
                    " 'namespace', 'kind', 'labels' Selector with 'Add' and 'Modify' Modifier"
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
        self.secret_data = None

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
        self.secret_data = "SomeData"

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
        self.orphan_svc = self.testbed_name + '-orphan-svc'
        orphan_sa = self.testbed_name + '-orphan-sa'
        self.kubehelper_src.create_cv_secret(orphan_secret, self.orphan_namespace, labels={self.testbed_name: 'apple'})
        self.kubehelper_src.create_cv_configmap(orphan_cm, self.orphan_namespace)
        self.kubehelper_src.create_cv_svc(
            self.orphan_svc,
            self.orphan_namespace,
            selector={self.namespace: self.namespace}
        )
        self.kubehelper_src.create_cv_serviceaccount(orphan_sa, self.orphan_namespace)

        # Creating another orphan Secret
        orphan_secret = self.testbed_name + '-orphan-secret-2'
        self.kubehelper_src.create_cv_secret(
            orphan_secret,
            self.orphan_namespace,
            test_data=self.secret_data,
            labels={self.testbed_name: 'apple'}
        )

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
        # Add new label to all Service
        modify_selector_id_kind_only = self.testbed_name + '-modify-kind-' + get_random_string()
        modify_selector_id_kind_name = self.testbed_name + '-modify-kind-name-' + get_random_string()
        modify_selector_id_kind_name_ns = self.testbed_name + '-modify-kind-name-ns-' + get_random_string()
        modify_selector_id_kind_ns = self.testbed_name + '-modify-kind-ns-' + get_random_string()
        modify_selector_id_kind_ns_label_depl = self.testbed_name + '-modify-kind-ns-label-depl-' + get_random_string()
        modify_selector_id_kind_ns_name_sa = self.testbed_name + '-modify-kind-ns-label-sa-' + get_random_string()
        modify_selector_id_kind_ns_2 = self.testbed_name + '-modify-kind-ns-' + get_random_string()

        self.log.info(
            f"Generating selector with ID [{modify_selector_id_kind_ns_2}]: Match with all resources from all "
            f"namespaces of Kind [Service]"
        )
        self.mods_helper.generate_selector(
            selector_id=modify_selector_id_kind_ns_2,
            kind='Secret',
            namespace=self.namespace
        )
        self.log.info(
            f"Generating modifier with ID [{modify_selector_id_kind_ns_2}]: " +
            f"Change secret label testbedName :york -> new-york"
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=modify_selector_id_kind_ns_2,
            path=f'/metadata/labels/{self.testbed_name}',
            value='york',
            new_value='new-york',
            parameters='Contains'
        )

        self.log.info(
            f"Generating selector with ID [{modify_selector_id_kind_only}]: Match with all resources from all "
            f"namespaces of Kind [Service]"
        )
        self.mods_helper.generate_selector(
            selector_id=modify_selector_id_kind_only,
            kind='Service'
        )

        self.log.info(
            f"Generating selector with ID [{modify_selector_id_kind_name}]: Match with resources with Name"
            f" [{self.testbed_name + '-orphan-cm'}] from all namespaces of Kind [ConfigMap]"
        )
        self.mods_helper.generate_selector(
            selector_id=modify_selector_id_kind_name,
            kind='ConfigMap',
            name=self.testbed_name + '-orphan-cm'
        )

        self.log.info(
            f"Generating selector with ID [{modify_selector_id_kind_name_ns}]: Match with resources with Name"
            f" [{self.testbed_name + '-pod'}] from Namespace [{self.namespace}] of Kind [Pod]"
        )
        self.mods_helper.generate_selector(
            selector_id=modify_selector_id_kind_name_ns,
            kind='Pod',
            name=self.testbed_name + '-pod',
            namespace=self.namespace,
        )

        self.log.info(
            f"Generating modifier with ID [{modify_selector_id_kind_only}]: " +
            f"Change port of svc from [80] to [81]"
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=modify_selector_id_kind_only,
            path='/spec/ports/0/port',
            value=80,
            new_value=81,
            parameters='Exact'
        )

        self.log.info(
            f"Generating modifier with ID [{modify_selector_id_kind_name}]: " +
            f"modify data field [{'/data/testdata from dummy data to dummy data-Modified'}]"
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=modify_selector_id_kind_name,
            path='/data/testdata',
            value='dummy data',
            new_value='dummy data-Modified',
            parameters='Contains'
        )

        self.log.info(
            f"Generating modifier with ID [{modify_selector_id_kind_name_ns}]: " +
            f" to change image name of container in pod "
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=modify_selector_id_kind_name_ns,
            path='/spec/containers/0/name',
            value='k8s-automation-container',
            new_value='ubuntu-modified',
            parameters='Exact'
        )

        self.log.info(
            f"Generating selector with ID [{modify_selector_id_kind_ns}]: Match with all resources "
            f"from Namespace [{self.orphan_namespace}] of Kind [Secret]"
        )
        self.mods_helper.generate_selector(
            selector_id=modify_selector_id_kind_ns,
            kind='Secret',
            namespace=self.orphan_namespace
        )

        labels = {'testbed': self.testbed_name}

        self.log.info(
            f"Generating selector with ID [{modify_selector_id_kind_ns_label_depl}]: Match with all resources " +
            f"from Namespace [{self.namespace}] of Kind [Deployment] having label [{labels}]"
        )
        self.mods_helper.generate_selector(
            selector_id=modify_selector_id_kind_ns_label_depl,
            kind='Deployment',
            namespace=self.namespace,
            labels=labels
        )
        self.log.info(
            f"Generating selector with ID [{modify_selector_id_kind_ns_name_sa}]: Match with all resources " +
            f"from Namespace [{self.namespace}] of Kind [Deployment] having name [{self.depl_sa}]"
        )
        self.mods_helper.generate_selector(
            selector_id=modify_selector_id_kind_ns_name_sa,
            kind='ServiceAccount',
            namespace=self.namespace,
            name=self.depl_sa
        )

        self.log.info(
            f"Generating modifier with ID [{modify_selector_id_kind_ns}]: " +
            f"Modify 'data' field from matching resources"
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=modify_selector_id_kind_ns,
            path=f'/metadata/labels/{self.testbed_name}',
            value='apple',
            new_value='new-apple',
            parameters='Contains'
        )

        self.log.info(
            f"Generating modifier with ID [{modify_selector_id_kind_ns_label_depl}]: " +
            f"Modify service account [/spec/template/spec/serviceAccountName] from matching resources"
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=modify_selector_id_kind_ns_label_depl,
            path='/spec/template/spec/serviceAccountName',
            value=self.depl_sa,
            new_value=self.depl_sa + '-modified',
            parameters='Exact'
        )
        self.log.info(
            f"Generating modifier with ID [{modify_selector_id_kind_ns_name_sa}]: " +
            f"Modify service account [/automountServiceAccountToken] from matching resources"
        )
        self.mods_helper.generate_modify_modifier(
            selector_id=modify_selector_id_kind_ns_name_sa,
            path='/automountServiceAccountToken',
            value=False,
            new_value=True,
            parameters='Exact'
        )
        rm_json = self.mods_helper.generate_restore_modifier(
            name=self.testbed_name + '-modify'
        )
        self.log.info(f"Create RestoreModifier [{self.testbed_name + '-modify'}] with JSON : [{rm_json}]")

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

        pod_name = self.testbed_name + '-pod'
        self.kubehelper_src.create_cv_pod(
            pod_name, self.namespace, secret=secret_name, configmap=config_name
        )
        time.sleep(30)

        deployment_name = self.testbed_name + '-deployment'
        self.kubehelper_src.create_cv_deployment(
            deployment_name,
            self.namespace,
            labels={'testbed': self.testbed_name},
            service_account=self.depl_sa
        )
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
            raise CVWebAutomationException(_exception) from _exception

    @TestStep()
    def verify_full_ns_backup(self):
        """Verify FULL Backup of entire namespace as content
        """
        self.log.info('Step 1 -- Run FULL Backup job with Namespace as content')
        self.kubehelper_src.backup("FULL")
        self.log.info('FULL Backup job step with Namespace as content successfully completed')

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
            modifier_list=[self.testbed_name + '-modify'],
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
    def validate_restored_resources(self):
        """Validate resources are restored with correct transformation
        """

        self.log.info('Step 3 -- Validate resources for transformation after restore')

        # Validate transformations in both namespaces first on Service
        # 'ports/0/port' parameter of Services in both namespaces has been changed from
        # 80 to 81
        for ns in [self.restore_namespace, self.restore_orphan_namespace]:
            for manifest in self.restored_manifests[ns]["Service"]:
                if manifest.spec.ports[0].port != 81:
                    raise KubernetesException(
                        'ValidationOperations', '109', f'Service [{manifest.metadata.name}] port has not been modified'
                                                       f' by modify modifier. Expected - [81]'
                    )
                else:
                    self.log.info(
                        f"Validated MODIFY Modifier to modify 'port' of all Services resources in "
                        f"[{ns}] namespace"
                    )

        # Validate data/testbed_name field added in configMap
        for manifest in self.restored_manifests[self.restore_orphan_namespace]["ConfigMap"]:
            if manifest.metadata.name == (self.testbed_name + '-orphan-cm') \
                    and (manifest.data['testdata'] != 'dummy data-Modified'):
                raise KubernetesException(
                    'ValidationOperations', '109', f'ConfigMap [{manifest.metadata.name}] does not have data'
                                                   f' {manifest.data["testdata"]} modified by MODIFY modifier'
                )
        else:
            self.log.info(
                "Validated MODIFY Modifier to modify data content to specific named" +
                " ConfigMap resource in specific namespace"
            )

        # Validate container name change in restored Pod
        for manifest in self.restored_manifests[self.restore_namespace]["Pod"]:
            if manifest.metadata.name == self.testbed_name + '-pod' and \
                    (manifest.spec.containers[0].name != 'ubuntu-modified'):
                raise KubernetesException(
                    'ValidationOperations', '109', f'Pod [{manifest.metadata.name}] does not have container name'
                                                   f' modified by MODIFY modifier'
                )
        else:
            self.log.info("Validated MODIFY Modifier to change container name")

        # Validate modified labels in all Secrets of restore orphan namespace
        for manifest in self.restored_manifests[self.restore_orphan_namespace]["Secret"]:

            if manifest.metadata.name != self.testbed_name + '-orphan-secret' and \
                    manifest.metadata.name != self.testbed_name + '-orphan-secret-2':
                continue
            if self.testbed_name not in manifest.metadata.labels or \
                    manifest.metadata.labels[self.testbed_name] != 'new-apple':
                raise KubernetesException(
                    'ValidationOperations', '109', f'Secret [{manifest.metadata.name}] has metadata.labels field not'
                                                   f' modified by Modify modifier'
                )
        else:
            self.log.info(
                "Validated MODIFY Modifier to modify labels from all Secret resources in specific namespace"
            )

        for manifest in self.restored_manifests[self.restore_namespace]["Secret"]:

            if manifest.metadata.name != self.testbed_name + '-secret':
                continue
            if self.testbed_name not in manifest.metadata.labels or\
                    manifest.metadata.labels[self.testbed_name] != 'new-york':
                raise KubernetesException(
                    'ValidationOperations', '109', f'Secret [{manifest.metadata.name}] has metadata.labels field not'
                                                   f' modified by Modify modifier,'
                                                   f' got - [{manifest.metadata.labels[self.testbed_name]}]'
                )
        else:
            self.log.info(
                "Validated MODIFY Modifier to modify labels from all Secret resources in specific namespace"
            )

        # Validate modified label key in all Deployments of restore namespace
        for manifest in self.restored_manifests[self.restore_namespace]['ServiceAccount']:
            if manifest.metadata.name == self.depl_sa and manifest.automount_service_account_token is not True:
                raise KubernetesException(
                    'ValidationOperations', '109', f'Service Account [{manifest.metadata.name}] field'
                                                   f' [automountServiceAccountToken] not modified by Modify modifier'
                )
            else:
                self.log.info(
                    "Validated MODIFY Modifier to change [automountServiceAccountToken] field of"
                    " SA with Name and kind in specific namespace"
                )

        for manifest in self.restored_manifests[self.restore_namespace]["Deployment"]:
            if manifest.spec.template.spec.service_account_name != self.depl_sa + "-modified":
                raise KubernetesException(
                    'ValidationOperations', '109', f'Deployment [{manifest.metadata.name}] has SA [{self.depl_sa}] not'
                                                   f'modified by Modify modifier'
                )
        else:
            self.log.info(
                "Validated MODIFY Modifier to change SA from Deployment with label in specific namespace"
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

            # Step 1.5 - Create restore modifiers
            self.create_restore_modifiers()

            # Step 2 - Perform cross-cluster OOP Restore of Namespace
            self.verify_namespace_level_oop_restore_from_ui(source_modifier=False)

            # Step 3 - Validate restored resources in restored namespaces
            self.validate_restored_resources()

            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 4 -- Delete testbed, delete client")
            self.delete_testbed()
