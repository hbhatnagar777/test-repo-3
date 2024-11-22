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

    run()                               --  Run function of this test case
"""

import time

from AutomationUtils import config
from AutomationUtils.commonutils import get_random_string
from AutomationUtils.cvtestcase import CVTestCase
from Kubernetes.RestoreModifierHelper import RestoreModifierHelper
from Kubernetes.constants import RestoreModifierConstants
from Kubernetes.exceptions import KubernetesException
from Reports.utils import TestCaseUtils
from Kubernetes.KubernetesHelper import KubernetesHelper
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.K8s.modifiers import ConfigureModifiers
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep, InitStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    test_step = TestStep()

    """
    Testcase to create new Tenant, Add cluster and Application Group, perform Backup and Restore validation.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Login to Command Center, Configure new Cluster and Application Group
    4. Create cluster and application 
    5. Create modifiers of various combinations and verify creation on the cluster
    6. Create a modifier using API, verify read from UI
    7. Update modifier, verify update on cluster
    8. Delete a modifier, verify deletion on cluster
    9. Deactivate and Delete tenant
    10. Cleanup testbed
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.api_modifier = None
        self.add_selector_id_kind_only = None
        self.modifier_namespace_add = None
        self.modifier_name_delete = None
        self.modifier_label_modify = None
        self.modifier_kind_add = None
        self.modifier_field_modify = None
        self.updated_modifier = None
        self.expected_table_json = None
        self.mods_helper = None
        self.plural = None
        self.version = None
        self.group = None
        self.restore_sc = None
        self.name = "Kubernetes Command Center - CRUD Operations for Restore modifiers"
        self.utils = TestCaseUtils(self)
        self.admin_console = None
        self.browser = None
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
        self.pvc_name = None
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
        self.util_namespace = None
        self.k8s_setup = None
        self.resources_before_backup = None
        self.resources_after_restore = None
        self.config_mods = None
        self.modifier_name = None
        self.selector_dict = None
        self.action_dict = None
        self.__cluster_created = False

    @InitStep(msg="Load kubeconfig and initialize testcase variables")
    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.namespace = 'cv-config'
        self.restore_namespace = self.namespace + "-rst"
        self.app_grp_name = self.testbed_name + "-app-grp"
        self.serviceaccount = self.testbed_name + "-sa"
        self.pod_name = self.testbed_name + "-pod"
        self.pvc_name = self.testbed_name + "-pvc"
        self.authentication = "Service account"
        self.subclientName = "automation-{}".format(self.id)
        self.clientName = "k8sauto-{}".format(self.id)
        self.server_name = self.clientName
        self.destclientName = "k8sauto-{}-dest".format(self.id)
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", automation_config.ACCESS_NODE)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        self.controller = self.commcell.clients.get(self.access_node)
        self.controller_id = int(self.controller.client_id)
        self.util_namespace = self.testbed_name + '-utils'
        self.add_selector_id_kind_only = self.testbed_name + '-add-kind-' + get_random_string()
        self.api_modifier = self.testbed_name + 'api-modifier'

        self.content = [self.namespace]
        self.group = RestoreModifierConstants.GROUP.value
        self.version = RestoreModifierConstants.VERSION.value
        self.plural = RestoreModifierConstants.PLURAL.value
        self.expected_table_json = {
            'selector': {'Name': ['Kind'],
                         'Value': ['Service'],
                         'Actions': []},

            'action': {'Action': ['Add'],
                       'Path': [f'/metadata/labels/{self.testbed_name}'],
                       'Value': [self.add_selector_id_kind_only],
                       'New Value': [''],
                       'Parameters': ['Exact'],
                       'Actions': []}

        }
        self.mods_helper = RestoreModifierHelper()
        self.modifier_kind_add = {
            'name': f'{self.testbed_name}-modifier-kind-add',
            'selector_dict': {
                'kind': 'Pod'
            },
            'action_dict': [
                {
                    'action': 'add',
                    'path': '/spec/labels/label1',
                    'value': 'new value'
                }
            ]
        }
        self.modifier_label_modify = {
            'name': f'{self.testbed_name}-modifier-label-modify',
            'selector_dict': {
                'labels': {'label1': 'value1'}
            },
            'action_dict': [
                {
                    'action': 'modify',
                    'path': '/spec/labels/label1',
                    'parameters': 'Exact',
                    'value': 'test-value',
                    'newValue': 'new-test-value'
                }
            ]
        }
        self.modifier_name_delete = {
            'name': f'{self.testbed_name}-modifier-name-delete',
            'selector_dict': {
                'name': 'test-name'
            },
            'action_dict': [
                {
                    'action': 'delete',
                    'path': '/spec/labels/label1'
                }
            ]
        }
        self.modifier_namespace_add = {
            'name': f'{self.testbed_name}-modifier-namespace-add',
            'selector_dict': {
                'namespace': 'test-namespace'
            },
            'action_dict': [
                {
                    'action': 'add',
                    'path': '/spec/labels/label1',
                    'value': 'new Value'
                }
            ]
        }
        self.modifier_field_modify = {
            'name': f'{self.testbed_name}-modifier-field-modify',
            'selector_dict': {
                'field': {
                    'path': '/spec/labels/label1',
                    'exact': True,
                    'criteria': 'Contains',
                    'value': 'new value'
                }
            },
            'action_dict': [
                {
                    'action': 'modify',
                    'path': '/spec/labels/label1',
                    'parameters': 'Exact',
                    'value': 'test-value',
                    'newValue': 'new-test-value'
                }
            ]
        }
        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

        self.k8s_helper = K8sHelper(self.admin_console, self)

    @InitStep(msg="Create testbed resources on cluster")
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
        self.kubehelper.create_cv_namespace(self.util_namespace)

        # Create service account if doesn't exist
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, self.util_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, self.util_namespace, cluster_role)

        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, self.util_namespace)
        self.content = [self.util_namespace]

    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)
        self.kubehelper.delete_cv_namespace(self.util_namespace)
        modifiers_created = [self.modifier_name_delete["name"],
                             self.modifier_kind_add["name"],
                             self.modifier_label_modify["name"],
                             self.modifier_namespace_add['name'],
                             self.modifier_field_modify['name'],
                             self.api_modifier
                             ]

        for mod in modifiers_created:
            self.log.info(f"Attempting to delete modifier {mod}")
            try:
                self.kubehelper.delete_cv_custom_resource(
                    namespace=self.namespace,
                    name=mod,
                    group=self.group,
                    version=self.version,
                    plural=self.plural
                )
            except Exception as e:
                self.log.info(f"Modifier deletion failed - Exception - {e}")

    def setup(self):
        """
         Create testbed, launch browser and login
        """
        self.log.info("Step -- Launch browser and login to Command Center")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname
        )
        self.admin_console.login(
            username=self._inputJSONnode['commcell']['commcellUsername'],
            password=self._inputJSONnode['commcell']['commcellPassword']
        )
        self.admin_console.navigate(self.admin_console.base_url)
        self.init_inputs()
        self.create_testbed()
        self.config_mods = ConfigureModifiers(self.admin_console)

    def verify_selectors(self, selectors, selector_dict):
        """
        Verifies selector creation
        """
        # selector_types = ['name', 'namespace', 'kind', 'labels', 'field']
        for stype in selector_dict.keys():

            if stype in selectors and selectors[stype] == selector_dict[stype]:
                self.log.info(f"{stype} selector matched successfully")
            else:
                raise KubernetesException(
                    exception_module="RestoreModifierOperations",
                    exception_id="104",
                    exception_message=f"{stype} selector not matched successfully"
                )

    @test_step
    def verify_modifier_creation(self, modifier_name, selector_dict, action_dict):
        """Creates a modifier on the cluster using UI, compares with object
        on the cluster"""

        self.log.info(f"Modifier Name : [{modifier_name}]")
        # Create a modifier from the UI
        self.k8s_helper.go_to_restore_modifier_config_page(self.server_name)
        self.k8s_helper.configure_new_restore_modifier(
            modifier_name=modifier_name,
            selector_dict=selector_dict,
            action_dict=action_dict,
        )
        time.sleep(10)

        restore_modifier = self.mods_helper.get_restore_modifier_json(kubehelper=self.kubehelper, name=modifier_name)
        selectors = restore_modifier["spec"]["selectors"][0]
        self.verify_selectors(selectors=selectors, selector_dict=selector_dict)

        # Verify modifier is created correctly

        modifiers = restore_modifier["spec"]["modifiers"]
        if len(modifiers) == 0:
            raise KubernetesException(
                exception_module='RestoreModifierOperations',
                exception_id='104',
                exception_message="Actions not created"
            )

        for i in range(0, len(modifiers)):
            modifier = modifiers[i]
            if modifier['action'] == 'Add':
                if modifier['path'] == action_dict[i]['path'] and modifier['value'] == action_dict[i]['value']:
                    self.log.info('Add action successfully matched')
                else:
                    raise KubernetesException(
                        exception_module='RestoreModifierOperations',
                        exception_id='104',
                        exception_message="Add action incorrectly added in backend"
                    )
            elif modifier['action'] == 'Modify':
                if modifier['path'] == action_dict[i]['path'] and \
                        modifier['value'] == action_dict[i]['value'] and \
                        modifier['newValue'] == action_dict[i]['newValue'] and \
                        modifier['parameters'] == action_dict[i]['parameters']:
                    self.log.info('Modify action successfully matched')
                else:
                    raise KubernetesException(
                        exception_module='RestoreModifierOperations',
                        exception_id='104',
                        exception_message="Modify action incorrectly added in backend"
                    )
            elif modifier['action'] == 'Delete':
                if modifier['path'] == action_dict[i]['path']:
                    self.log.info('Delete action successfully matched')
                else:
                    raise KubernetesException(
                        exception_module='RestoreModifierOperations',
                        exception_id='104',
                        exception_message="Delete action incorrectly added in backend"
                    )
            else:
                raise KubernetesException(
                    exception_module='RestoreModifierOperations',
                    exception_id='104',
                    exception_message=f"Invalid action type created. {modifier['action']}"
                )

        self.log.info("All restore modifier fields are added correctly")

    @test_step
    def verify_modifier_deletion(self, modifier_name):
        """
        Delete a modifier and verify its deletion
        """
        self.k8s_helper.go_to_restore_modifier_config_page(self.server_name)
        self.config_mods.delete_modifier(name=modifier_name)
        cr_objects = self.kubehelper.get_namespace_custom_resources(
            group=self.group,
            version=self.version,
            namespace=self.namespace,
            plural=self.plural
        )
        if modifier_name in cr_objects:
            raise KubernetesException(
                exception_module='RestoreModifierOperations',
                exception_id='105',
                exception_message=f"Deletion of modifier [{modifier_name}] failed"
            )
        self.log.info(f"Modifier [{modifier_name}] deleted successfully")

    def create_modifier_using_api(self):
        """
        Creates a modifier using API
        """

        # Add new label to all Service

        self.log.info(
            f"Generating selector with ID [{self.add_selector_id_kind_only}]: Match with all resources of given kind"
            f" from all namespaces of Kind [Service]"
        )
        self.mods_helper.generate_selector(
            selector_id=self.add_selector_id_kind_only,
            kind='Service'
        )

        self.log.info(
            f"Generating modifier with ID [{self.add_selector_id_kind_only}]: "
            f"Add new label [{'/metadata/labels/' + self.testbed_name + ':' + self.add_selector_id_kind_only}]"
        )
        self.mods_helper.generate_add_modifier(
            selector_id=self.add_selector_id_kind_only,
            path='/metadata/labels/' + self.testbed_name,
            value=self.add_selector_id_kind_only
        )

        # Create RestoreModifier CR
        rm_json = self.mods_helper.generate_restore_modifier(
            name=self.api_modifier
        )
        self.log.info(f"Created RestoreModifier [{self.api_modifier}] with JSON : [{rm_json}]")
        self.mods_helper.clear_all_selectors()
        self.mods_helper.clear_all_modifiers()

        self.log.info(f"Creating RestoreModifier CRO on cluster [{self.api_server_endpoint}]")
        self.mods_helper.create_restore_modifier_crs(self.kubehelper)

    @test_step
    def verify_read_operation(self):
        """
        Read the modifier and verify fields displayed in table is correct
        """
        self.create_modifier_using_api()
        self.k8s_helper.go_to_restore_modifier_config_page(self.server_name)
        self.config_mods.select_modifier(name=self.api_modifier)
        __selector_table = Rtable(self.admin_console, id='selectorGridWrapper')
        selector_table_json = __selector_table.get_table_data()
        self.log.info(selector_table_json)
        if selector_table_json != self.expected_table_json['selector']:
            raise KubernetesException(
                "RestoreModifierOperations",
                '102',
                f"Values in table are incorrect. Expected [{self.expected_table_json['selector']}], "
                f"Got [{selector_table_json}]"
            )

        self.log.info("Selector table matched correctly")

        __action_table = Rtable(self.admin_console, id='actionGridWrapper')
        action_table_json = __action_table.get_table_data()
        self.log.info(action_table_json)
        if action_table_json != self.expected_table_json['action']:
            raise KubernetesException(
                "RestoreModifierOperations",
                '102',
                f"Values in table are incorrect. Expected [{self.expected_table_json['action']}], "
                f"Got [{action_table_json}]"
            )

        self.log.info("Action table matched correctly")

    @test_step
    def verify_update_operation(self, modifier_name):
        """Adds a namespace selector to a preexisting modifier and validates with YAML on cluster"""
        self.k8s_helper.go_to_restore_modifier_config_page(self.server_name)
        self.config_mods.select_modifier(name=modifier_name)
        __table = Rtable(self.admin_console)
        self.config_mods.add_selector({
                'namespace': 'newValue'
            })
        self.config_mods.save()
        time.sleep(10)
        updated_modifier = self.mods_helper.get_restore_modifier_json(kubehelper=self.kubehelper, name=modifier_name)
        self.log.info(updated_modifier)
        updated_modifier_selector = updated_modifier["spec"]["selectors"][0]
        if "namespace" in updated_modifier_selector.keys() and updated_modifier_selector["namespace"] == 'newValue':
            self.log.info("Modifier updated successfully")
        else:
            raise KubernetesException(
                "RestoreModifierOperations",
                '102',
                f"Modifier not updated correctly. Expected {self.updated_modifier}, got {updated_modifier}"
            )

    @test_step
    def create_cluster(self):
        """Step 1 & 2 --  Create Cluster and app group from Command Center"""
        self.admin_console.navigator.navigate_to_kubernetes()
        self.k8s_helper.create_k8s_cluster(
            api_server=self.api_server_endpoint,
            name=self.server_name,
            authentication=self.authentication,
            username=self.serviceaccount,
            password=self.servicetoken,
            access_nodes=self.access_node,
        )
        self.__cluster_created = True
        self.log.info("Cluster and app group created.. Proceeding with next steps..")

    @test_step
    def delete_cluster(self):
        """Step 9 -- Delete Cluster"""
        self.k8s_helper.delete_k8s_cluster(self.server_name)

    def run(self):
        """
        Run the Testcase - New K8s configuration, full backup job, inc backup job, out-of-place restore
        """
        try:
            # Step 1 - Create cluster
            self.create_cluster()
            # Step 2.1 - Verify Create operation using UI - Kind selector and Add action
            self.log.info("Step 2.1 - Verify Create operation using UI - Kind selector and Add action")
            self.verify_modifier_creation(
                modifier_name=self.modifier_kind_add['name'],
                selector_dict=self.modifier_kind_add['selector_dict'],
                action_dict=self.modifier_kind_add['action_dict']
            )
            # Step 2.2 - Verify Create operation using UI - Label selector and Modify action
            self.log.info("Step 2.2 - Verify Create operation using UI - Label selector and Modify action")
            self.verify_modifier_creation(
                modifier_name=self.modifier_label_modify['name'],
                selector_dict=self.modifier_label_modify['selector_dict'],
                action_dict=self.modifier_label_modify['action_dict']
            )
            # Step 2.3 - Verify Create operation using UI - Name selector and Delete action
            self.log.info("Step 2.3 - Verify Create operation using UI - Name selector and Delete action")
            self.verify_modifier_creation(
                modifier_name=self.modifier_name_delete['name'],
                selector_dict=self.modifier_name_delete['selector_dict'],
                action_dict=self.modifier_name_delete['action_dict']
            )
            # Step 2.4 - Verify Create operation using UI - Namespace selector and Add action
            self.log.info("Step 2.4 - Verify Create operation using UI - Namespace selector and Add action")
            self.verify_modifier_creation(
                modifier_name=self.modifier_namespace_add['name'],
                selector_dict=self.modifier_namespace_add['selector_dict'],
                action_dict=self.modifier_namespace_add['action_dict']
            )
            # Step 2.5 - Verify Create operation using UI - Field selector and Modify action
            self.log.info("Step 2.5 - Verify Create operation using UI - Field selector and Modify action")
            self.verify_modifier_creation(
                modifier_name=self.modifier_field_modify['name'],
                selector_dict=self.modifier_field_modify['selector_dict'],
                action_dict=self.modifier_field_modify['action_dict']
            )

            # Step 3 - Verify read operation using UI
            self.log.info("Step 3 - Verify read operation using UI")
            self.verify_read_operation()
            # Step 4 - Verify update operation using UI
            self.log.info("Step 4 - Verify update operation using UI")
            self.verify_update_operation(self.modifier_name_delete['name'])
            # Step 5 - Verify delete operation using UI
            self.log.info("Step 5 - Verify delete operation using UI")
            self.verify_modifier_deletion(self.modifier_name_delete['name'])

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            try:
                if self.__cluster_created:
                    # Step 5 - Delete cluster step
                    self.delete_cluster()

            except Exception as error:
                self.utils.handle_testcase_exception(error)

    def tear_down(self):
        """
        Teardown testcase - Delete testbed, deactivate and delete tenant
        """

        self.browser.close_silently(self.browser)
        self.delete_testbed()
