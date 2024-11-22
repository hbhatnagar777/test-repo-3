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

    load_kubeconfig_file()              --  Load Kubeconfig file and connect to the Kubernetes API Server

    create_testbed()                    --  Create the testbed required for the testcase

    delete_testbed()                    --  Delete the testbed created

    init_tcinputs()                     --  Update tcinputs dictionary to be used by helper functions

    backup_step()                       --  Verify backup job

    restore_without_overwrite()         --  Verify restore job without overwrite

    restore_with_overwrite()            --  Verify restore job with overwrite

    restore_after_crd_delete()          --  Verify restore after deleting testbed CRD

    run()                               --  Run function of this test case
"""


import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes import KubernetesUtils
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """
    Testcase to create Kubernetes Cluster, perform backup and inplace restore of applications.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create Namespace, CRDs for testbed
    5. Create a Kubernetes client with proxy provided
    6. Create application group for kubernetes
    7. Initiate Full Backup for App group created and verify job completed
    8. Run restore with overwrite option not enabled
    9. Run restore with overwrite enabled
    10. Run restore after deleting the original Helm chart and CRDs
    11. Cleanup testbed
    12. Cleanup clients created.
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - CRD Backup and Restore"
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
        self.helm_operator_name = 'eck-operator'
        self.helm_operator_namespace = 'k8s-auto-{}'.format(self.id) + '-system'
        self.repo_name = 'k8s-auto-{}'.format(self.id)
        self.repo_path = 'https://helm.elastic.co'
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", automation_config.ACCESS_NODE)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        self.controller = self.commcell.clients.get(self.access_node)
        self.controller_id = int(self.controller.client_id)
        self.proxy_obj = Machine(self.controller)

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

    @TestStep()
    def create_testbed(self):
        """Create cluster resources and clients for the testcase
        """

        self.log.info("Deleting CRD if already present...")
        self.kubehelper.delete_cv_crd('elasticsearch.k8s.elastic.co', 'elasticsearches')
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

        self.log.info("Deploying ECK using Helm Chart")

        self.kubehelper.deploy_helm_apps(
            self.helm_operator_name, self.helm_operator_namespace,
            repo_path=self.repo_path, repo_name=self.repo_name, kubeconfig_path=self.k8s_config
        )

        elasticsearch_json = {
            "apiVersion": "elasticsearch.k8s.elastic.co/v1",
            "kind": "Elasticsearch",
            "metadata": {
                "name": self.testbed_name
            },
            "spec": {
                "version": "8.8.2",
                "nodeSets": [
                    {
                        "name": "default",
                        "count": 1,
                        "config": {
                            "node.store.allow_mmap": False
                        }
                    }
                ]
            }
        }

        self.log.info("Creating Elastic Search Cluster Custom Resource object")
        self.kubehelper.create_cv_custom_resource(
            group='elasticsearch.k8s.elastic.co',
            version='v1',
            plural='elasticsearches',
            namespace=self.namespace,
            body=elasticsearch_json
        )
        self.content.append(f"{self.namespace}/{self.testbed_name}")
        self.log.info("Custom Resource [Elasticsearch] created.")

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
            self.delete_testbed()
            raise CVTestCaseInitFailure(_exception) from _exception

    @TestStep()
    def delete_testbed(self):
        """
        Delete the generated testbed
        """
        self.kubehelper.delete_cv_crd('elasticsearch.k8s.elastic.co', 'elasticsearches')
        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)

        self.kubehelper.cleanup_helm_apps(
            self.helm_operator_name, self.helm_operator_namespace, kubeconfig_path=self.k8s_config
        )
        self.kubehelper.delete_cv_namespace(self.helm_operator_namespace)

        crb_name = self.testbed_name + '-crb'
        # Delete cluster role binding

        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)

    @TestStep()
    def backup_step(self, backup_type="INCREMENTAL"):
        """Initiate Backup Job for Namespace containing CRD
        """
        self.kubehelper.backup(backup_type=backup_type)
        self.log.info("Run Backup Step complete")

    @TestStep()
    def restore_without_overwrite(self):
        """Perform CRD restore to restore namespace without overwrite enabled
        """
        self.kubehelper.run_restore_validate(
            self.clientName,
            self.storageclass,
            validate=False,
            overwrite=False
        )
        self.log.info("Run Restore without overwrite Step complete")

    @TestStep()
    def restore_with_overwrite(self):
        """Perform CRD restore to restore namespace with overwrite enabled
        """
        self.kubehelper.run_restore_validate(
            self.clientName,
            self.storageclass,
            validate=False,
            overwrite=True
        )
        self.log.info("Run Restore with overwrite Step complete")

    @TestStep()
    def restore_after_crd_delete(self):
        """Perform restore after deleting CRDs
        """

        self.kubehelper.delete_cv_namespace(self.restore_namespace)
        self.kubehelper.cleanup_helm_apps(self.helm_operator_name, self.helm_operator_namespace)
        self.kubehelper.run_restore_validate(
            self.clientName,
            self.storageclass,
            validate=False,
            overwrite=False
        )
        self.log.info("Run Restore without overwrite Step complete")

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Run Full Job and incremental job before verifying restore
            self.backup_step('FULL')

            # Run restore without overwrite
            self.restore_without_overwrite()

            # Run restore with overwrite
            self.restore_with_overwrite()

            # Run restore with crd deleted
            self.restore_after_crd_delete()

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step -- Delete testbed, delete client ")
            self.delete_testbed()
            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")
