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

    verify_backup()                     --  Verify backup job

    verify_restore_step()               --  Verify restore job

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
    Testcase to create Kubernetes Cluster, perform different restores of applications.
    This testcase does the following --
    1. Connect to Kubernetes API Server using Kubeconfig File
    2. Create Service Account, ClusterRoleBinding for CV
    3. Fetch Token name and Token for the created Service Account Secret
    4. Create ClusterRole,Namespace with Role,RoleBinding, Pods with attached secret,configMap
    5. Create a Kubernetes client with proxy provided
    6. Create application group with NS as content for kubernetes
    7. Initiate Full Backup of application group and verify job completed with correct events
    8. Create application group with Pod as content for kubernetes
    9. Initiate Full Backup of application group and verify job completed with correct events
    17. Cleanup testbed
    18. Cleanup clients created.
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Kubernetes - Verify events with missing configs"
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
        self.restore_namespace_ns = None
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
        self.accessmode = None
        self.sts_name = None
        self.pod_name = None
        self.env_secret_name = None
        self.env_cm_name = None
        self.projected_secret_name = None
        self.projected_cm_name = None
        self.pvc_name = None
        self.ingress_name = None
        self.svc_name = None
        self.dummy_serviceaccount = None
        self.role = None
        self.role_binding1 = None
        self.cluster_role = None
        self.role_binding2 = None
        self.tls_secret_name = None
        self.resources_before_backup = None
        self.resources_after_restore = None
        self.job_obj = None

    def init_inputs(self):
        """
        Initialize objects required for the testcase.
        """

        self.testbed_name = "k8s-auto-{}-{}".format(self.id, int(time.time()))
        self.namespace = self.testbed_name
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
        self.controller_machine = Machine(self.controller)
        self.accessmode = self.tcinputs.get('AccessMode', 'ReadWriteOnce')
        self.sts_name = self.testbed_name + '-sts'
        self.pod_name = self.testbed_name + '-pod'
        self.env_secret_name = self.testbed_name + '-env-secret'
        self.env_cm_name = self.testbed_name + '-env-cm'
        self.projected_secret_name = self.testbed_name + '-proj-secret'
        self.projected_cm_name = self.testbed_name + '-proj-cm'
        self.ingress_name = self.testbed_name + '-ingress'
        self.svc_name = self.testbed_name + '-svc'
        self.role = self.testbed_name + '-role'
        self.role_binding1 = self.testbed_name + '-rolebinding1'
        self.role_binding2 = self.testbed_name + '-rolebinding2'
        self.cluster_role = self.testbed_name + '-clusterrole'
        self.dummy_serviceaccount = self.testbed_name + "-dummy-sa"
        self.tls_secret_name = self.testbed_name + '-tls-secret'
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
        self.kubehelper.create_cv_serviceaccount(name=self.serviceaccount, sa_namespace=sa_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(
            name=crb_name,
            sa_name=self.serviceaccount,
            sa_namespace=sa_namespace,
            cluster_role_name=cluster_role
        )

        self.servicetoken = self.kubehelper.get_serviceaccount_token(
            name=self.serviceaccount,
            sa_namespace=sa_namespace
        )

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)

        self.kubehelper.create_cv_serviceaccount(self.dummy_serviceaccount, self.namespace)
        self.kubehelper.create_cv_role(self.role, self.namespace)
        self.kubehelper.create_cv_role_binding(
            self.role_binding1,
            self.namespace,
            'Role',
            self.role,
            self.dummy_serviceaccount,
            self.namespace
        )
        self.kubehelper.create_cv_cluster_role(self.cluster_role)
        self.kubehelper.create_cv_role_binding(
            self.role_binding2,
            self.namespace,
            'ClusterRole',
            self.cluster_role,
            self.dummy_serviceaccount,
            self.namespace
        )
        self.kubehelper.create_cv_secret(
            self.tls_secret_name,
            self.namespace,
            secret_type='kubernetes.io/tls'
        )
        self.kubehelper.create_cv_secret(self.env_secret_name, self.namespace)
        self.kubehelper.create_cv_configmap(self.env_cm_name, self.namespace)
        self.kubehelper.create_cv_secret(self.projected_secret_name, self.namespace)
        self.kubehelper.create_cv_configmap(self.projected_cm_name, self.namespace)
        self.kubehelper.create_cv_svc(self.svc_name, self.namespace)

        # TLS Secret
        self.kubehelper.create_cv_ingress(
            self.ingress_name,
            self.svc_name,
            self.namespace,
            tls_secret=self.tls_secret_name
        )
        self.kubehelper.create_cv_deployment(
            self.pod_name,
            self.namespace,
            labels={
                'app': 'test'
            },
            env_secret=self.env_secret_name,
            projected_secret=self.projected_secret_name,
            env_configmap=self.env_cm_name,
            projected_configmap=self.projected_cm_name,
            service_account=self.dummy_serviceaccount
        )

        # delete secrets,config Maps, roles and clusterRoles
        self.kubehelper.delete_cv_resource_generic(
            name=self.env_secret_name,
            namespace=self.namespace,
            object_type='Secret'
        )
        self.kubehelper.delete_cv_resource_generic(
            name=self.projected_secret_name,
            namespace=self.namespace,
            object_type='Secret'
        )
        self.kubehelper.delete_cv_resource_generic(
            name=self.tls_secret_name,
            namespace=self.namespace,
            object_type='Secret'
        )
        self.kubehelper.delete_cv_resource_generic(
            name=self.env_cm_name,
            namespace=self.namespace,
            object_type='ConfigMap'
        )
        self.kubehelper.delete_cv_resource_generic(
            name=self.projected_cm_name,
            namespace=self.namespace,
            object_type='ConfigMap'
        )
        self.kubehelper.delete_cv_resource_generic(
            name=self.role,
            namespace=self.namespace,
            object_type='Role'
        )
        self.kubehelper.delete_cv_resource_generic(
            name=self.cluster_role,
            object_type='ClusterRole'
        )

        time.sleep(30)

        KubernetesUtils.add_cluster(
            self,
            self.clientName,
            self.api_server_endpoint,
            self.serviceaccount,
            self.servicetoken,
            self.access_node
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

        self.kubehelper.delete_cv_namespace(self.namespace)
        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(
            sa_name=self.serviceaccount, sa_namespace=sa_namespace
        )

        KubernetesUtils.delete_cluster(self, self.clientName)

    @TestStep()
    def match_logs(self, job_id):
        """
        Performing log matching to verify events
        """
        self.kubehelper.match_logs_for_pattern(
            client_obj=self.controller,
            job_id=job_id,
            log_file_name="vsbkp.log",
            pattern=r'DownloadConfigs\(\) - Resource\(s\) \[.*\]',
            expected_keyword=None
        )

    @TestStep()
    def verify_backup(self, content):
        """
        Validate FULL Backup of Namespace
        """

        KubernetesUtils.add_application_group(
            self,
            content=content,
            plan=self.plan,
            name=self.subclientName,
        )
        self.kubehelper.source_vm_object_creation(self)

        self.resources_before_backup = self.kubehelper.get_all_resources(self.namespace)
        backup_job = self.kubehelper.backup('FULL')
        self.log.info("Backup of applications completed. Proceeding with event validation")
        self.match_logs(job_id=backup_job.job_id)
        self.log.info("Event validation successful")
        KubernetesUtils.delete_application_group(self, self.subclientName)

    def run(self):
        """
        Run the Testcase
        """
        try:

            self.kubehelper.source_vm_object_creation(self)

            # Run Full NS backup job
            self.verify_backup([self.namespace])
            # Verify Full App backup job
            self.verify_backup([f'{self.namespace}/{self.pod_name}'])
            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step -- Delete testbed, delete client ")
            self.delete_testbed()
