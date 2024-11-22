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
    __init__()                              --  initialize TestCase class

    setup()                                 --  setup method for test case

    tear_down()                             --  tear down method for testcase

    init_inputs()                           --  Initialize objects required for the testcase

    create_testbed()                        --  Create the testbed required for the testcase

    delete_testbed()                        --  Delete the testbed created

    init_tcinputs()                         --  Update tcinputs dictionary to be used by helper functions

    change_cluster_credentials()            --  Change SA and SA token of a cluster

    change_cluster_properties()             --  Change cluster access node, image url and secret,
                                            configuration namespace and wait timeout

    change_app_group_properties()           --  Change Access Node, plan, number of readers,worker pod resource settings
                                                and enable live volume fallback on Application Group

    verify_cluster_settings()               --  Validates Logs for Cluster Settings and UI for restore modifier

    verify_application_group_settings()     --  Validates Logs for Application Group Settings

    backup_and_kill_if_fails()              --  Initiates FULL Backup and kills if it is going to fail



    run()                                   --  Run function of this test case
"""

import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.commonutils import get_random_string
from Kubernetes.RestoreModifierHelper import RestoreModifierHelper
from Kubernetes.constants import RestoreModifierConstants
from Reports.utils import TestCaseUtils
from Kubernetes.KubernetesHelper import KubernetesHelper
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep, InitStep
from Kubernetes import KubernetesUtils
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils.interruption import Interruption
from Kubernetes.exceptions import KubernetesException
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.K8s.modifiers import ConfigureModifiers


automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    test_step = TestStep()

    """
    Testcase to validate CRUD operations on cluster and App Groups.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Login to Command Center, Configure new Cluster and Application Group
    4. Create cluster and application group
    5. Change service account and service account token fo the cluster
    6. Take FULL Backup
    7. Change cluster properties like accessnode and advanced options 
    8. Take FULL Backup and verify logs
    9. Change application group properties like plan, accessnode and options 
    10. Take FULL Backup and verify logs
    11. Re-enter service account and service account token of the cluster 
    12. Verify logs to check if advanced options were effected
    13. Perform a FULL APPLICATION OUT-OF-PLACE restore to the restore namespace
    14. Cleanup testbed
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes Cluster Level and Application Group Level Additional Settings Validation"
        self.utils = TestCaseUtils(self)
        self.admin_console = None
        self.browser = None
        self.modified_access_node = None
        self.modified_plan = None
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken1 = None
        self.servicetoken2 = None
        self.access_node = None
        self.controller_id = None
        self.testbed_name = None
        self.namespace = None
        self.restore_namespace = None
        self.configuration_namespace = None
        self.api_modifier = None
        self.add_selector_id_kind_only = None
        self.modifier_namespace_add = None
        self.modifier_name_delete = None
        self.modifier_label_modify = None
        self.modifier_kind_add = None
        self.modifier_field_modify = None
        self.updated_modifier = None
        self.expected_table_json = None
        self.pod_name = None
        self.pvc_name = None
        self.app_grp_name = None
        self.serviceaccount1 = None
        self.serviceaccount2 = None
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
        self.__cluster_created = False
        self.job_obj = None
        self.job_mgr_obj = None
        self.job = None
        self.interruption_helper = None
        self.config_mods = None

    @InitStep(msg="Load kubeconfig and initialize testcase variables")
    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.namespace = self.testbed_name
        self.restore_namespace = self.namespace + "-rst"
        self.configuration_namespace = "cv-config"
        self.api_modifier = self.testbed_name + 'api-modifier'
        self.add_selector_id_kind_only = self.testbed_name + '-add-kind-' + get_random_string()
        self.app_grp_name = self.testbed_name + "-app-grp"
        self.serviceaccount1 = self.testbed_name + "-sa"
        self.serviceaccount2 = self.testbed_name + "-sa-2"
        self.pvc_name = self.testbed_name + "-pvc"
        self.authentication = "Service account"
        self.subclientName = "automation-{}".format(self.id)
        self.clientName = "k8sauto-{}".format(self.id)
        self.server_name = self.clientName
        self.destclientName = "k8sauto-{}-dest".format(self.id)
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", automation_config.ACCESS_NODE)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        self.util_namespace = self.testbed_name + '-utils'
        self.modified_access_node = self.tcinputs.get("ModifiedAccessNode", self.access_node)
        self.modified_plan = self.tcinputs.get("ModifiedPlan", self.plan)
        self.controller = self.commcell.clients.get(self.modified_access_node)
        self.controller_id = int(self.controller.client_id)

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
            Create testbed resources
        """
        self.log.info("Creating cluster resources...")

        # Create 2 service accounts
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount1, sa_namespace)
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount2, sa_namespace)

        # Create 2  cluster role bindings
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount1, sa_namespace, cluster_role)

        crb_name2 = self.testbed_name + '-crb-2'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name2, self.serviceaccount2, sa_namespace, cluster_role)

        time.sleep(5)

        # Fetch service account tokens from both service accounts
        self.servicetoken1 = self.kubehelper.get_serviceaccount_token(self.serviceaccount1, sa_namespace)
        self.servicetoken2 = self.kubehelper.get_serviceaccount_token(self.serviceaccount2, sa_namespace)

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)
        self.kubehelper.create_cv_namespace(self.restore_namespace)
        self.kubehelper.create_cv_namespace(self.configuration_namespace)
        pod_name = self.testbed_name + "-pod"
        self.kubehelper.create_cv_pod(pod_name, self.namespace)

        # Add Cluster
        KubernetesUtils.add_cluster(
            self,
            self.clientName,
            self.api_server_endpoint,
            self.serviceaccount1,
            self.servicetoken1,
            self.access_node
        )
        # Add Application Group
        KubernetesUtils.add_application_group(
            self,
            content=self.content,
            plan=self.plan,
            name=self.subclientName,
        )

    @test_step
    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)
        self.kubehelper.delete_cv_namespace(self.configuration_namespace)

        crb_name = self.testbed_name + '-crb'
        crb_name2 = self.testbed_name + '-crb-2'

        self.kubehelper.delete_cv_clusterrolebinding(crb_name)
        self.kubehelper.delete_cv_clusterrolebinding(crb_name2)

        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount1, sa_namespace=sa_namespace)
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount2, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)

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


    @test_step
    def change_cluster_credentials(self):
        """
        Change SA and SA token of a cluster
        """
        self.k8s_helper.change_sa_and_sa_token(
            cluster_name=self.clientName,
            sa_name=self.serviceaccount2,
            token=self.servicetoken2
        )

    @test_step
    def change_cluster_properties(self, image_url, image_secret, config_ns,
                                  worker_startup, resource_cleanup, snapshot_ready, snapshot_cleanup):
        """
        Change cluster access node, image url and secret, configuration namespace and wait timeout
        """
        self.k8s_helper.change_access_node(self.clientName, self.modified_access_node, self.access_node)

        self.k8s_helper.change_image_url_and_image_secret(
            cluster_name=self.clientName,
            image_url=image_url,
            image_secret=image_secret
        )
        self.k8s_helper.change_config_namespace(
            cluster_name=self.clientName,
            config_ns=config_ns,
            destination=True
        )
        self.k8s_helper.change_wait_timeout(
            cluster_name=self.clientName,
            worker_startup=worker_startup,
            resource_cleanup=resource_cleanup,
            snapshot_ready=snapshot_ready,
            snapshot_cleanup=snapshot_cleanup,
            destination=True
        )
        self.create_modifier_using_api()

    @test_step
    def change_app_group_properties(self, no_of_readers, cpu_request, cpu_limit, memory_request, memory_limit):
        """
        Change Access Node, plan, number of readers, worker pod resource settings  and enable live volume fallback on Application Group
        """
        try:
            self.k8s_helper.change_plan_on_k8s_app_grp(cluster_name=self.clientName, app_group_name=self.subclientName,
                                                   plan_name=self.modified_plan)
        except Exception as e:
            self.log.info(f"Unwanted exception : {e}")
        self.k8s_helper.change_access_node_on_app_grp(cluster_name=self.clientName,
                                                      access_node=self.modified_access_node,
                                                      app_grp_name=self.subclientName)

        self.k8s_helper.change_no_of_readers(
            cluster_name=self.clientName,
            appgroup_name=self.subclientName,
            no_of_readers=no_of_readers,
            destination=True
        )
        self.k8s_helper.change_worker_pod_resource_settings(
            cluster_name=self.clientName,
            appgroup_name=self.subclientName,
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
            cpu_request=cpu_request,
            memory_request=memory_request,
            destination=True

        )
        self.k8s_helper.enable_live_volume_fallback(cluster_name=self.clientName, appgroup_name=self.subclientName)

    @test_step
    def backup_and_kill_if_fails(self):
        """Initiate FULL Backup and kill if it is going to fail"""
        self.job = self.subclient.backup(backup_level="FULL")
        self.job_mgr_obj = JobManager(_job=self.job, commcell=self.commcell)
        self.interruption_helper = Interruption(self.job.job_id, self.commcell)
        self.log.info("Waiting for 5 minutes...")

        self.log.info("Implicitly wait for 5 minutes...")
        time.sleep(300)

        expected_state = ['waiting', 'running']
        if (self.job.status.lower() in expected_state) and self.job.summary.get('percentComplete') <= 10:
            self.log.info(
                f"status : {self.job.status.lower()} and percentComplete : {self.job.summary.get('percentComplete')}")
            self.log.info("Job is in waiting state. Killing Job...")
            self.job.kill(wait_for_job_to_kill=True)
            self.job_mgr_obj.wait_for_state("killed")

        else:
            self.log.info(f"Backup Job with Job id {self.job.job_id} is successfully completed")
        return self.job.job_id

    @test_step
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
    def verify_cluster_settings(self, job_id):
        """
        Validating Logs for Cluster Settings
        """
        self.log.info("Validating logs for advanced options of the cluster....")

        self.log.info("Matching logs for image url and image pull secret")
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=job_id,
            log_file_name="vsbkp.log",
            pattern=r'Setting image registry URL: \[.+\] image registry secret: \[.+\]',
            expected_keyword=None
        )

        self.log.info("Matching logs for configuration namespace")
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=job_id,
            log_file_name="vsbkp.log",
            pattern=r'Setting configuration namespace to \[.+\]',
            expected_keyword=None
        )

        self.log.info("Matching logs for wait timeout for resources")
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=job_id,
            log_file_name="vsbkp.log",
            pattern=r'Setting wait timeout for agent startup \[.+\] during backup',
            expected_keyword=None
        )
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=job_id,
            log_file_name="vsbkp.log",
            pattern=r'Setting wait timeout for agent shutdown \[.+\] during backup',
            expected_keyword=None
        )
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=job_id,
            log_file_name="vsbkp.log",
            pattern=r'Setting wait timeout for snapshot ready \[.+\] during backup',
            expected_keyword=None
        )
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=job_id,
            log_file_name="vsbkp.log",
            pattern=r'Setting wait timeout for snapshot cleanup \[.+\] during backup',
            expected_keyword=None
        )
        self.log.info("Verifying Restore modifier in configuration namespace")
        self.verify_read_operation()

    @test_step
    def verify_application_group_settings(self, job_id):
        """
        Validating Logs for Application Group Settings
        """
        self.log.info("Validating logs for application group settings")

        self.log.info("Validating logs for status of Live volume fallback")
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=job_id,
            log_file_name="vsbkp.log",
            pattern=r'Setting fallback to Live volume on snapshot failure to \[.+\]',
            expected_keyword=None
        )

        self.log.info("Verifying logs for worker pod resource settings")
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=job_id,
            log_file_name="vsbkp.log",
            pattern=r'Setting image Worker Pod resource settings CPU Min: \[.+\] CPU Max: \[.+\] Memory Min: \[.+\] Memory Max: \[.+\]',
            expected_keyword=None
        )

    def run(self):
        """
        Run the Testcase - Verify CRUD operations
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            self.log.info("Step 1 --- Change ServiceAccount and ServiceAccountToken")
            self.change_cluster_credentials()

            self.log.info("Step 2 -- Initiate FULL Backup")
            self.subclient.backup(backup_level="FULL")

            self.log.info("Step 3 --- Change Access Node and Advanced options of the cluster ")
            self.change_cluster_properties(
                image_url="abcd",
                image_secret="defg",
                config_ns=self.configuration_namespace,
                worker_startup='2',
                resource_cleanup='2',
                snapshot_ready='2',
                snapshot_cleanup='2'
            )

            self.log.info("Step 4 --- Initiate FULL Backup")
            job_id = self.backup_and_kill_if_fails()

            self.log.info("Step 5 --- Verify Cluster Settings ")
            self.verify_cluster_settings(job_id)

            self.log.info("Step 6 --- Change Plan, AccessNode, options of the application group")
            self.change_app_group_properties(no_of_readers="3", cpu_request="150", cpu_limit="150", memory_request="150", memory_limit="150")

            self.log.info("Step 7 --- Initiate FULL Backup")
            job_id = self.backup_and_kill_if_fails()

            self.log.info("Step 8 --- Verify Application Group Settings")
            self.verify_application_group_settings(job_id)

            self.log.info("Step 9 --- Re-enter ServiceAccount, ServiceAccount token and change AccessNode")
            self.change_cluster_credentials()
            self.k8s_helper.change_access_node(
                cluster_name=self.clientName,
                old_access_node=self.access_node,
                access_node=self.modified_access_node
            )

            self.log.info("Step 10 --- Take FULL Backup")
            job_id = self.backup_and_kill_if_fails()

            self.log.info("Step 11 --- Verify logs for advanced options of the cluster")
            try:
                self.verify_cluster_settings(job_id)
            except KubernetesException as e:
                self.log.info("ADVANCED OPTIONS HAVE BEEN DELETED AFTER RE-ENTERING THE SERVICE ACCOUNT TOKEN AND ACCESS NODE")
                # raise e
                # MR: 446351

            self.log.info("Step 12 --- Initiate FULL APPLICATION OUT-OF-PLACE RESTORE")
            self.kubehelper.restore_out_of_place(client_name=self.clientName, restore_namespace=self.restore_namespace)

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step 13 -- Delete testbed, delete client ")
            self.delete_testbed()


