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

    create_tasks()                      --  Creates the CVTask and CVTaskSet custom resources on the cluster

    delete_testbed()                    --  Delete the testbed created

    verify_task_main_app()              --  Verifies if the pre, post tasks are executed successfully on
    the main deployment

    verify_task_dummy_app()             --  Verifies if the pre, post tasks are NOT executed on the dummy deployment

    run()                               --  Run function of this test case
"""

import time
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Kubernetes.KubernetesHelper import KubernetesHelper
from Kubernetes import KubernetesUtils
from Kubernetes.PrePostScriptsHelper import CVTask, CVTaskSet
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    """This testcase verifies that the prepost kubernetes scripts using CVTask and CVTaskSet CRDs are
    executed as expected.

    Testcase steps:
        1. Connect to Kubernetes API Server using Kubeconfig File
        2. Create Service Account, ClusterRoleBinding for CV
        3. Fetch Token name and Token for the created Service Account Secret
        4. Create Namespace, PVC, deployment, serviceaccounts etc. for testbed
        5. Create main deployment with label "production=yes"
        6. Create dummy deployment with label "dummy=yes"
        7. Create cvtasks for command type
        8. Create cvtaskset resource and set "labelSelector" to "production=yes"
        9. Run FULL backup
        10. Verify if the pre, post tasks are executed on the main deployment
        11. Verify if the pre, post tasks are not executed on the dummy deployment
    """

    def __init__(self):
        super(TestCase, self).__init__()

        self.name = 'Kubernetes - PrePost scripts - Label selector'
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.controller_id = None
        self.testbed_name = None
        self.namespace = None
        self.restore_namespace = None
        self.app_grp_name = None
        self.serviceaccount = None
        self.authentication = 'Service account'
        self.subclientName = None
        self.clientName = None
        self.destclientName = None
        self.destinationClient = None
        self.controller = None
        self.agentName = 'Virtual Server'
        self.instanceName = 'Kubernetes'
        self.backupsetName = 'defaultBackupSet'
        self.tcinputs = {}
        self.k8s_config = None
        self.driver = None
        self.plan = None
        self.storageclass = None
        self.kubehelper = None
        self.content = []
        self.proxy_obj = None
        self.test_pod = None
        self.dummy_pod = None

    def init_inputs(self):
        """Initialize objects required for the testcase"""

        self.testbed_name = 'k8s-auto-{}-{}'.format(self.id, int(time.time()))
        self.namespace = self.testbed_name
        self.restore_namespace = self.namespace + '-rst'
        self.app_grp_name = self.testbed_name + '-app-grp'
        self.serviceaccount = self.testbed_name + '-sa'
        self.authentication = 'Service account'
        self.subclientName = 'automation-{}'.format(self.id)
        self.clientName = 'k8sauto-{}'.format(self.id)
        self.destclientName = 'k8sauto-{}-dest'.format(self.id)
        self.plan = self.tcinputs.get('Plan', automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get('AccessNode', automation_config.ACCESS_NODE)
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
        """Create cluster resources and clients for the testcase"""

        self.log.info("Creating cluster resources...")

        # Create service account if it doesn't exist
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

        # Create Service
        svc_name = self.testbed_name + '-svc'
        self.kubehelper.create_cv_svc(svc_name, self.namespace)

        pvc_name = self.testbed_name + '-deploypvc'
        self.kubehelper.create_cv_pvc(
            pvc_name, self.namespace, storage='50Mi',
            storage_class=self.storageclass
        )

        # Creating deployment
        deployment_name = self.testbed_name + '-deployment'
        self.log.info('Creating main deployment with labels "production=yes, automation=63796"')
        self.kubehelper.create_cv_deployment(
            deployment_name,
            self.namespace,
            pvc_name,
            labels={
                'production': 'yes',
                'automation': self.id
            }
        )

        dummy_pvc_name = self.testbed_name + '-dummy-deploypvc'
        self.kubehelper.create_cv_pvc(
            dummy_pvc_name, self.namespace, storage='50Mi',
            storage_class=self.storageclass
        )

        dummy_deployment_name = self.testbed_name + '-dummy-deployment'
        self.log.info('Creating dummy deployment with labels "dummy=yes, automation=63796"')
        self.kubehelper.create_cv_deployment(
            dummy_deployment_name,
            self.namespace,
            dummy_pvc_name,
            labels={
                'dummy': 'yes',
                'automation': self.id
            }
        )

        all_resources = self.kubehelper.get_all_resources(self.namespace, label_selector='production', return_json=True)
        self.test_pod = all_resources['Pod'][0].metadata.name
        self.log.info('Test pod picked for verification [%s]', self.test_pod)

        all_resources = self.kubehelper.get_all_resources(self.namespace, label_selector='dummy', return_json=True)
        self.dummy_pod = all_resources['Pod'][0].metadata.name
        self.log.info('Dummy pod picked for verification [%s]', self.dummy_pod)

        # Creating CVTasks
        self.create_tasks()

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

    @TestStep()
    def create_tasks(self):
        """Creates the CVTask and CVTaskSet custom resources on the cluster"""

        self.log.info('Creating "Command" type task')
        command_task = CVTask('auto-command-task')
        command_task.set_pre_backup_snapshot('Command', 'echo', ['command_pre >> /tmp/pre.log'])
        command_task.set_post_backup_snapshot('Command', 'echo', ['command_post >> /tmp/post.log'])
        command_task.create(self.kubehelper, self.namespace)
        self.log.info('Command task created successfully')

        self.log.info('Creating CVTaskSet for deployment labels "production=yes, automation"')
        task_set = CVTaskSet(f'auto-task-set-{self.id}')
        task_set.app_namespace = self.namespace
        task_set.label_selectors = [
            ['production=yes', 'automation']
        ]

        task_set.add_task(
            task_name=command_task.name,
            task_id=command_task.name,
            task_namespace=self.namespace,
            execution_order=1
        )

        task_set.delete(self.kubehelper, 'cv-config')

        self.log.info('Creating CVTaskSet with manifest [%s]', task_set.manifest)
        task_set.create(self.kubehelper, 'cv-config')

        self.log.info('CVTaskSet created successfully')

    def setup(self):
        """Setup the testcase"""

        self.init_inputs()
        self.create_testbed()

    def run(self):
        """Run the testcase"""
        try:

            self.kubehelper.source_vm_object_creation(self)

            self.log.info('Running FULL Backup')
            self.kubehelper.backup('FULL')

            self.log.info('Verifying PRE and POST tasks on the main app')
            self.verify_task_main_app()

            self.log.info('Verifying NO TASK is executed on the dummy app')
            self.verify_task_dummy_app()

            self.log.info('Testcase completed successfully')

        except Exception as error:
            raise Exception(error)

        finally:
            self.log.info('Delete testbed, delete client')
            self.delete_testbed()

    @TestStep()
    def delete_testbed(self):
        """Delete the generated testbed"""

        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)

        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)

    @TestStep()
    def verify_task_main_app(self):
        """Verifies if the pre, post tasks are executed successfully on the main deployment"""

        self.log.info('Getting contents of the /tmp directory on main pod [%s]', self.test_pod)
        temp_dir = self.kubehelper.list_pod_content(
            pod_name=self.test_pod,
            namespace=self.namespace,
            location='/tmp'
        )
        self.log.info('Contents of the /tmp directory %s on main pod', temp_dir)

        expected_pre_log = 'command_pre\n'
        expected_post_log = 'command_post\n'

        self.log.info('Getting /tmp/pre.log file contents from pod [%s]', self.test_pod)

        actual_pre_log = self.kubehelper.get_pod_file_content(
            pod_name=self.test_pod,
            namespace=self.namespace,
            file_path='/tmp/pre.log'
        )
        self.log.info('Actual pre-scripts log - [%s]', actual_pre_log)

        self.log.info('Expected pre-scripts log - [%s]', expected_pre_log)

        if actual_pre_log != expected_pre_log:
            raise Exception('Pre-scripts were not executed correctly as expected')

        self.log.info('Getting /tmp/post.log file contents from main pod [%s]', self.test_pod)

        actual_post_log = self.kubehelper.get_pod_file_content(
            pod_name=self.test_pod,
            namespace=self.namespace,
            file_path='/tmp/post.log'
        )
        self.log.info('Actual post-scripts log - [%s]', actual_post_log)

        self.log.info('Expected pre-scripts log - [%s]', expected_post_log)

        if actual_post_log != expected_post_log:
            raise Exception('Post-scripts were not executed correctly as expected')

        self.log.info('Verified pre and post tasks executed on the main app')

    @TestStep()
    def verify_task_dummy_app(self):
        """Verifies if the pre, post tasks are NOT executed on the dummy deployment"""

        self.log.info('Verifying if /tmp/pre.log, post.log are created on the dummy pod [%s]', self.dummy_pod)

        self.log.info('Getting contents of the /tmp directory on dummy pod')
        temp_dir = self.kubehelper.list_pod_content(
            pod_name=self.dummy_pod,
            namespace=self.namespace,
            location='/tmp/'
        )
        self.log.info('Contents of the /tmp directory on dummy pod %s', temp_dir)

        if 'pre.log' in temp_dir and 'post.log' in temp_dir:
            raise Exception('Pre, post tasks were executed on the dummy pod')

        self.log.info('Pre/post tasks didn\'t execute on the dummy pod as expected since CVTaskSet label did not match')
