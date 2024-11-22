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
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Kubernetes.KubernetesHelper import KubernetesHelper
from Web.AdminConsole.Helper.k8s_helper import K8sHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import TestStep, InitStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    test_step = TestStep()

    """
    Testcase to Add cluster and Application Group, perform NS level Backup and Restore validation.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create testbed
    3. Login to Command Center, Configure new Cluster and Application Group
    4. Create cluster and application group
    5. Verify Full NS level Backup Job
    6. Verify NS level OOP restore Job
    7. Verify Incremental Backup Job
    8. Verify NS Level IP restore Job
    9. Cleanup testbed
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.validate_matrix = None
        self.ns_plain_content = None
        self.app_ns_content = None
        self.name = "Kubernetes Command Center - Manage Application group content"
        self.utils = TestCaseUtils(self)
        self.admin_console = None
        self.browser = None
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.controller_id = None
        self.ns2_labels = None
        self.testbed_name = None
        self.namespace_app = None
        self.namespace_plain = None
        self.namespace_app_labels1 = None
        self.namespace_volumes1 = None
        self.namespace_labels = None
        self.namespace_app_labels2 = None
        self.namespace_volumes2 = None
        self.namespace_labels_labels = None
        self.namespace_app_labels1_labels = None
        self.namespace_app_pod = None
        self.namespace_app_labels1_pod = None
        self.namespace_volumes_pvc1 = None
        self.namespace_app_labels2_pod = None
        self.namespace_app_labels2_pod_labels = None
        self.namespace_volumes_pvc2 = None
        self.namespace_volumes_pvc2_labels = None
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
        self.__cluster_created = False

        self.labels_content = None
        self.volumes_content = None
        self.ns_label_selector_content = None
        self.app_label_selector_content = None

        self.volume_label_selector_content = None

    @InitStep(msg="Load kubeconfig and initialize testcase variables")
    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.ns2_labels = {f"{self.testbed_name}-ns2": "true"}
        self.app_grp_name = self.testbed_name + "-app-grp"
        self.serviceaccount = self.testbed_name + "-sa"
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
        self.namespace_app = self.testbed_name + '-ns-app'
        self.namespace_plain = self.testbed_name + '-ns-plain'
        self.namespace_app_labels1 = self.testbed_name + '-ns-app-labels1'
        self.namespace_volumes1 = self.testbed_name + '-ns-volumes1'
        self.namespace_labels = self.testbed_name + '-ns-labels'
        self.namespace_app_labels2 = self.testbed_name + '-ns-app-labels2'
        self.namespace_volumes2 = self.testbed_name + '-ns-volumes2'
        self.namespace_labels_labels = f"{self.testbed_name}=ns-labels-labels"
        self.namespace_app_labels1_labels = f"{self.testbed_name}=ns-app-labels1-labels"
        self.namespace_app_pod = self.testbed_name + '-ns-app-pod'
        self.namespace_app_labels1_pod = self.testbed_name + '-ns-app-labels1-pod'
        self.namespace_volumes_pvc1 = self.testbed_name + '-ns-volumes1-pvc'
        self.namespace_app_labels2_pod = self.testbed_name + '-ns-app-labels2-pod'
        self.namespace_app_labels2_pod_labels = f"{self.testbed_name}=ns-app-labels2-pod-labels"
        self.namespace_volumes_pvc2 = self.testbed_name + '-ns-volumes2-pvc'
        self.namespace_volumes_pvc2_labels = f"{self.testbed_name}=ns-volumes2-pvc-labels"
        self.validate_matrix = {}

        self.content = [self.namespace_app]

        # self.app_ns_content = [
        #     f'Applications:Applications:{self.namespace_app}/{self.namespace_app_pod}',
        #     f'Applications:Applications:{self.namespace_plain}'
        # ]

        self.app_ns_content = [
            f'Applications:Applications:{self.namespace_app}/{self.namespace_app_pod}'
        ]

        self.ns_plain_content = [f'Applications:Applications:{self.namespace_plain}']

        self.labels_content = [
            f'Applications:Labels:{self.namespace_app_labels1}/{self.namespace_app_labels1_labels}',
        ]
        self.volumes_content = [
            f'Applications:Volumes:{self.namespace_volumes1}/{self.namespace_volumes_pvc1}',
        ]
        self.ns_label_selector_content = [
            f'Selector:Namespaces:{self.namespace_labels_labels}',
        ]
        self.app_label_selector_content = [
            f'Selector:Application:{self.namespace_app_labels2_pod_labels} -n {self.namespace_app_labels2}',
        ]

        self.volume_label_selector_content = [
            f'Selector:Volumes:{self.namespace_volumes_pvc2_labels} -n {self.namespace_volumes2}',
        ]

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

        # Create service account if doesn't exist
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, sa_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, sa_namespace, cluster_role)

        time.sleep(30)
        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, sa_namespace)

        # namespace_app = Contains a pod called namespace_app_pod - DONE

        # namespace_plain = Contains only namespace - DONE

        # namespace_app_labels1 = Contains a pod namespace_app_labels1_pod with labels namespace_app_labels1_labels

        # namespace_volumes1 = Contains a pvc called namespace_volumes_pvc1

        # namespace_labels = Contains a namespace called namespace_labels with label - namespace_labels_labels

        # namespace_app_labels2 = Contains a pod called namespace_app_labels2_pod
        # with label - namespace_app_labels2_pod_labels

        # namespace_volumes2 = Contains a pvc called namespace_volumes_pvc2 with label - namespace_volumes_pvc2_labels

        self.kubehelper.create_cv_namespace(self.namespace_app)
        self.kubehelper.create_cv_namespace(self.namespace_plain)
        self.kubehelper.create_cv_namespace(self.namespace_app_labels1)
        self.kubehelper.create_cv_namespace(self.namespace_volumes1)
        self.kubehelper.create_cv_namespace(
            self.namespace_labels,
            labels=self.string_to_dict(self.namespace_labels_labels)
        )
        self.kubehelper.create_cv_namespace(self.namespace_app_labels2)
        self.kubehelper.create_cv_namespace(self.namespace_volumes2)

        self.kubehelper.create_cv_pod(
            self.namespace_app_pod,
            self.namespace_app
        )
        self.kubehelper.create_cv_pod(
            self.namespace_app_labels1_pod,
            self.namespace_app_labels1,
            labels=self.string_to_dict(self.namespace_app_labels1_labels)
        )
        self.kubehelper.create_cv_pvc(
            self.namespace_volumes_pvc1,
            self.namespace_volumes1
        )
        self.kubehelper.create_cv_pod(
            self.namespace_app_labels2_pod,
            self.namespace_app_labels2,
            labels=self.string_to_dict(self.namespace_app_labels2_pod_labels)
        )

        self.kubehelper.create_cv_pvc(
            self.namespace_volumes_pvc2,
            self.namespace_volumes2,
            labels=self.string_to_dict(self.namespace_volumes_pvc2_labels)
        )

        time.sleep(30)

    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        self.kubehelper.delete_cv_namespace(self.namespace_app)
        self.kubehelper.delete_cv_namespace(self.namespace_plain)
        self.kubehelper.delete_cv_namespace(self.namespace_app_labels1)
        self.kubehelper.delete_cv_namespace(self.namespace_volumes1)
        self.kubehelper.delete_cv_namespace(self.namespace_labels)
        self.kubehelper.delete_cv_namespace(self.namespace_app_labels2)
        self.kubehelper.delete_cv_namespace(self.namespace_volumes2)
        # self.kubehelper.delete_cv_namespace(self.util_namespace)
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

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

    def string_to_dict(self, string):
        key, value = string.split('=')
        result = {key: value}
        self.log.info(result)
        return result

    @test_step
    def create_cluster(self):
        """Step 1 & 2 --  Create Cluster and app group from Command Center"""

        # Cleanup if cluster with same name exists from previous run
        # Step 0 - Cleanup previous cluster
        try:
            self.delete_cluster()
        except CVWebAutomationException as exp:
            self.log.info(exp)

        self.admin_console.navigator.navigate_to_kubernetes()
        self.k8s_helper.configure_new_kubernetes_cluster(
            api_endpoint=self.api_server_endpoint,
            cluster_name=self.server_name,
            authentication=self.authentication,
            service_account=self.serviceaccount,
            service_token=self.servicetoken,
            app_group_name=self.app_grp_name,
            backup_content=self.content,
            plan_name=self.plan,
            access_nodes=self.access_node
        )
        self.__cluster_created = True
        self.log.info("Cluster and app group created.. Proceeding with next steps..")

    @test_step
    def delete_content_from_app_group(self):

        """
        Step 3.1 Deletes app group added to the app group with a particular name in namespace

        namespace       (str)       --  Namespace name

        name            (str)       --  application name

        """

        self.k8s_helper.delete_k8s_app_grp_content(row_idx=1, cluster=self.clientName, app_grp=self.app_grp_name)

    @test_step
    def add_content_to_app_group(self, content):
        """Step 3.x -- Adding content to Application Group via Manage content Pane

                    content      (list)             -- Set backup content with this format -
                                                'ContentType:BrowseType:namespace/app'
                                                Should be a list of strings with above format.

                                                        Valid ContentType -
                                                            Applications, Selector.
                                                            If not specified, default is 'Application'
                                                        Valid BrowseType for Application ContentType -
                                                            Applications, Volumes, Labels
                                                            If not specified, default is 'Applications'
                                                        Valid BrowseType for Selector ContentType -
                                                            Application, Volumes, Namespaces
                                                            If not specified, default is 'Namespaces'

                                                        Examples -
                                                            1. ns001 -- Format : namespace
                                                            2. ns001/app001 -- Format : namespace/app
                                                            3. Volumes:ns001/pvc001 -- Format : BrowseType:namespace/app
                                                            4. Selector:Namespaces:app=demo -n ns004
                                                                    -- Format : ContentType:BrowseType:namespace
                                                            5. ['Application:Volumes:nsvol/vol001', 'nsvol02/app1']

        """
        # namespace_app = Contains a pod called namespace_app_pod

        # namespace_plain = Contains only namespace

        # namespace_app_labels1 = Contains a pod namespace_app_labels1_pod with labels namespace_app_labels1_labels

        # namespace_volumes1 = Contains a pvc called namespace_volumes_pvc1

        # namespace_labels = Contains a namespace called namespace_labels with label - namespace_labels_labels

        # namespace_app_labels2 = Contains a pod called namespace_app_labels2_pod
        # with label - namespace_app_labels2_pod_labels

        # namespace_volumes2 = Contains a pvc called namespace_volumes_pvc2 with label - namespace_volumes_pvc2_labels
        self.log.info(f"Adding content {content} to application group {self.clientName} in cluster {self.app_grp_name}")

        self.k8s_helper.modify_app_group_content(
            cluster=self.clientName,
            app_grp=self.app_grp_name,
            content=content,
            validate_matrix=self.validate_matrix
        )

    @test_step
    def delete_app_group(self):
        """Step 4 -- Delete Application Group"""
        self.k8s_helper.delete_k8s_app_grp(self.app_grp_name)

    @test_step
    def delete_cluster(self):
        """Step 8 -- Delete Cluster"""
        self.k8s_helper.delete_k8s_cluster(self.server_name)

    def run(self):
        """
        Run the Testcase - New K8s configuration, full backup job, inc backup job, out-of-place restore
        """
        try:
            # Step 1 & 2 - Create cluster &  application group with namespace as content
            self.create_cluster()

            # Step 3.1 - Navigate to manage content and delete the existing content

            self.delete_content_from_app_group()

            # Step 3.2 - Add applications to content

            # namespace_app = Contains a pod called namespace_app_pod

            # namespace_plain = Contains only namespace

            # namespace_app_labels1 = Contains a pod namespace_app_labels1_pod with labels namespace_app_labels1_labels

            # namespace_volumes1 = Contains a pvc called namespace_volumes_pvc1

            # namespace_labels = Contains a namespace called namespace_labels with label - namespace_labels_labels

            # namespace_app_labels2 = Contains a pod called namespace_app_labels2_pod
            # with label - namespace_app_labels2_pod_labels

            # namespace_volumes2 = Contains a pvc called namespace_volumes_pvc2 with label -
            # namespace_volumes_pvc2_labels

            self.validate_matrix = {
                "Application name": [self.namespace_app_pod],
                "Type": ['Pod'],
                "Namespace": [self.namespace_app]
            }
            self.add_content_to_app_group(
                content=self.app_ns_content
            )

            # Step 3.2 - Add Namespaces to content. Adding NS1 to content'

            self.validate_matrix = {
                "Application name": [self.namespace_app_pod, self.namespace_plain],
                "Type": ['Pod', 'Namespace'],
                "Namespace": [self.namespace_app, self.namespace_plain]
            }

            self.add_content_to_app_group(
                content=self.ns_plain_content
            )

            self.validate_matrix = {
                "Application name": [self.namespace_app_pod, self.namespace_plain, self.namespace_app_labels1_pod],
                "Type": ['Pod', 'Namespace', 'Pod'],
                "Namespace": [self.namespace_app, self.namespace_plain, self.namespace_app_labels1]
            }

            # Step 3.2 - Add labels to content
            self.add_content_to_app_group(
                content=self.labels_content
            )

            self.validate_matrix = {
                "Application name": [
                    self.namespace_app_pod,
                    self.namespace_plain,
                    self.namespace_app_labels1_pod,
                    self.namespace_volumes_pvc1
                ],
                "Type": ['Pod', 'Namespace', 'Pod', 'PersistentVolumeClaim'],
                "Namespace": [self.namespace_app,
                              self.namespace_plain,
                              self.namespace_app_labels1,
                              self.namespace_volumes1
                              ]
            }

            # # Step 3.3 - Add volumes to content
            self.add_content_to_app_group(
                content=self.volumes_content
            )

            self.validate_matrix = {
                "Application name": [self.namespace_app_pod,
                                     self.namespace_plain,
                                     self.namespace_app_labels1_pod,
                                     self.namespace_volumes_pvc1,
                                     self.namespace_labels
                                     ],
                "Type": ['Pod', 'Namespace', 'Pod', 'PersistentVolumeClaim', 'Namespace'],
                "Namespace": [self.namespace_app,
                              self.namespace_plain,
                              self.namespace_app_labels1,
                              self.namespace_volumes1,
                              self.namespace_labels
                              ]
            }

            # Step 3.3 - Add applications and Namespaces to content
            self.add_content_to_app_group(
                content=self.ns_label_selector_content
            )

            self.validate_matrix = {
                "Application name": [self.namespace_app_pod,
                                     self.namespace_plain,
                                     self.namespace_app_labels1_pod,
                                     self.namespace_volumes_pvc1,
                                     self.namespace_labels,
                                     self.namespace_app_labels2_pod
                                     ],
                "Type": ['Pod', 'Namespace', 'Pod', 'PersistentVolumeClaim', 'Namespace', 'Pod'],
                "Namespace": [self.namespace_app,
                              self.namespace_plain,
                              self.namespace_app_labels1,
                              self.namespace_volumes1,
                              self.namespace_labels,
                              self.namespace_app_labels2]

            }

            # Step 3.5 - Add applications and Namespaces to content
            self.add_content_to_app_group(
                content=self.app_label_selector_content
            )

            self.validate_matrix = {
                "Application name": [self.namespace_app_pod,
                                     self.namespace_plain,
                                     self.namespace_app_labels1_pod,
                                     self.namespace_volumes_pvc1,
                                     self.namespace_labels,
                                     self.namespace_app_labels2_pod,
                                     self.namespace_volumes_pvc2],
                "Type": ['Pod', 'Namespace', 'Pod', 'PersistentVolumeClaim', 'Namespace', 'Pod',
                         'PersistentVolumeClaim'],
                "Namespace": [self.namespace_app,
                              self.namespace_plain,
                              self.namespace_app_labels1,
                              self.namespace_volumes1,
                              self.namespace_labels,
                              self.namespace_app_labels2,
                              self.namespace_volumes2]
            }

            # Step 3.6 - Add applications and Namespaces to content
            self.add_content_to_app_group(content=self.volume_label_selector_content)

            # Step 4 - Delete Application Group
            self.delete_app_group()

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:

            try:
                if self.__cluster_created:
                    # Step 4 - Delete cluster step
                    self.delete_cluster()

            except Exception as error:
                self.utils.handle_testcase_exception(error)

    def tear_down(self):
        """
            Teardown testcase - Delete testbed
        """
        Browser.close_silently(self.browser)
        self.delete_testbed()
