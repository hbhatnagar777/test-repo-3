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

    verify_pre_post_status()            --  Verifies the pre,post tasks are executed successfully by checking
    the pre, post log file

    verify_pre_post_return_code()       --  Verifies the return code of the pre,post scripts executed

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
        5. Create cvtasks for command, localscript, scripttext types.
        6. Create cvtaskset resource.
        7. Create a Kubernetes client with proxy provided
        8. Create application group for kubernetes with namespace as content
        9. Run FULL backup
        10. Verify if the cvtasks are executed by checking the script output log file.
        11. Run incremental backup
        12. Repeat #10
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = 'Kubernetes - PrePost scripts - Acceptance'
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

    def init_inputs(self):
        """Initialize objects required for the testcase"""

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

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

    @TestStep()
    def create_testbed(self):
        """Create cluster resources and clients for the testcase"""

        self.log.info('Creating cluster resources...')

        # Create service account if it doesn't exist
        sa_namespace = self.tcinputs.get('ServiceAccountNamespace', 'default')
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, sa_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get('ClusterRole', 'cluster-admin')
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, sa_namespace, cluster_role)

        time.sleep(30)
        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, sa_namespace)

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)

        # Create Service
        svc_name = self.testbed_name + '-svc'
        self.kubehelper.create_cv_svc(svc_name, self.namespace)

        pvc_deployment_name = self.testbed_name + '-deploypvc'
        self.kubehelper.create_cv_pvc(
            pvc_deployment_name, self.namespace, storage='50Mi',
            storage_class=self.storageclass
        )

        # Creating deployment
        deployment_name = self.testbed_name + '-deployment'
        self.kubehelper.create_cv_deployment(deployment_name, self.namespace, pvc_deployment_name)

        all_resources = self.kubehelper.get_all_resources(self.namespace, return_json=True)
        self.test_pod = all_resources['Pod'][0].metadata.name
        self.log.info('Pod picked for verification [%s]', self.test_pod)

        self.log.info('Creating local script file on the test pod')
        self.kubehelper.execute_command_in_pod(
            command=r'echo "echo \$1 >> \$2" > /tmp/my-script.sh; chmod 777 /tmp/my-script.sh',
            pod=self.test_pod,
            namespace=self.namespace
        )

        # Creating CVTasks
        self.create_tasks(deployment_name)

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
    def create_tasks(self, deployment_name):
        """Creates the CVTask and CVTaskSet custom resources on the cluster

            Args:
                deployment_name     (str)       --      The name of the deployment to assign the taskset to

        """

        self.log.info('Creating "Command" type task')
        command_task = CVTask('auto-command-task')
        command_task.set_pre_backup_snapshot('Command', 'echo', ['command_pre >> /tmp/pre.log'])
        command_task.set_post_backup_snapshot('Command', 'echo', ['command_post >> /tmp/post.log'])
        command_task.create(self.kubehelper, self.namespace)
        self.log.info('Command task created successfully')

        self.log.info('Creating "LocalScript" type task')
        local_script_task = CVTask('auto-local-script-task')
        local_script_task.set_pre_backup_snapshot(
            'LocalScript', '/tmp/my-script.sh', ['local_script_pre', '/tmp/pre.log']
        )
        local_script_task.set_post_backup_snapshot(
            'LocalScript', '/tmp/my-script.sh', ['local_script_post', '/tmp/post.log']
        )
        local_script_task.create(self.kubehelper, self.namespace)
        self.log.info('Local script task created successfully')

        self.log.info('Creating "ScriptText" type task')
        script_text_task = CVTask('auto-script-text-task')
        script_text_task.set_pre_backup_snapshot(
            'ScriptText',
            """sleep 60; echo $1 >> /tmp/pre.log; exit""",
            ['script_text_pre']
        )
        script_text_task.set_post_backup_snapshot(
            'ScriptText',
            """sleep 60; echo $1 >> /tmp/post.log; exit""",
            ['script_text_post']
        )
        script_text_task.create(self.kubehelper, self.namespace)
        self.log.info('Script text task created successfully')

        self.log.info('Creating CVTaskSet')
        task_set = CVTaskSet(f'auto-task-set-{self.id}')
        task_set.app_name = deployment_name
        task_set.app_namespace = self.namespace

        task_set.add_task(
            task_name=command_task.name,
            task_id=command_task.name,
            task_namespace=self.namespace,
            execution_order=1
        )

        task_set.add_task(
            task_name=local_script_task.name,
            task_id=local_script_task.name,
            task_namespace=self.namespace,
            execution_order=4
        )

        task_set.add_task(
            task_name=local_script_task.name,
            task_id=local_script_task.name,
            task_namespace=self.namespace,
            execution_order=3,
            is_disabled=True
        )

        task_set.add_task(
            task_name=script_text_task.name,
            task_id=script_text_task.name,
            task_namespace=self.namespace,
            execution_order=2
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

            self.log.info('Verifying PRE and POST status after FULL')
            self.verify_pre_post_status(occurrences=1)

            self.log.info('Running Incremental Backup')
            self.kubehelper.backup('INCREMENTAL')

            self.log.info('Verifying PRE and POST status after INCREMENTAL')
            self.verify_pre_post_status(occurrences=2)

            self.log.info('Verifying PRE and POST return code')
            self.verify_pre_post_return_code()

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
    def verify_pre_post_status(self, occurrences):
        """Verifies the pre, post tasks are executed successfully by checking the pre, post log file

            Args:
                occurrences         (int)       --      The number of times the pre,post template to be seen in logs

        """

        self.log.info('Getting contents of the /tmp directory on pod [%s]', self.test_pod)
        temp_dir = self.kubehelper.list_pod_content(
            pod_name=self.test_pod,
            namespace=self.namespace,
            location='/tmp'
        )
        self.log.info('Contents of the /tmp directory %s', temp_dir)

        pre_log_template = 'command_pre\nscript_text_pre\nlocal_script_pre\n'
        post_log_template = 'command_post\nscript_text_post\nlocal_script_post\n'

        self.log.info('Getting /tmp/pre.log file contents')

        actual_pre_log = self.kubehelper.get_pod_file_content(
            pod_name=self.test_pod,
            namespace=self.namespace,
            file_path='/tmp/pre.log'
        )
        self.log.info('Actual pre-scripts log - [%s]', actual_pre_log)

        expected_pre_log = pre_log_template * occurrences
        self.log.info('Expected pre-scripts log - [%s]', expected_pre_log)

        if actual_pre_log != expected_pre_log:
            raise Exception('Pre-scripts were not executed correctly as expected')

        self.log.info('Getting /tmp/post.log file contents')
        
        actual_post_log = self.kubehelper.get_pod_file_content(
            pod_name=self.test_pod,
            namespace=self.namespace,
            file_path='/tmp/post.log'
        )
        self.log.info('Actual post-scripts log - [%s]', actual_post_log)

        expected_post_log = post_log_template * occurrences
        self.log.info('Expected pre-scripts log - [%s]', expected_post_log)

        if actual_post_log != expected_post_log:
            raise Exception('Post-scripts were not executed correctly as expected')

        self.log.info('Verified pre and post tasks are executed on the deployment')

    @TestStep()
    def verify_pre_post_return_code(self):
        """Verifies the return code of the pre, post scripts are executed"""

        self.log.info('Getting pre-script return code')
        pre_rc = self.kubehelper.get_pod_file_content(
            pod_name=self.test_pod,
            namespace=self.namespace,
            file_path='/tmp/pre.rc'
        )

        self.log.info('Value of /tmp/pre.rc file is [%s]', pre_rc)
        if pre_rc.strip() != '0':
            raise Exception('Pre-script return code is non-zero')

        self.log.info('Successfully verified pre-script return code is 0')

        self.log.info('Getting post-script return code')
        post_rc = self.kubehelper.get_pod_file_content(
            pod_name=self.test_pod,
            namespace=self.namespace,
            file_path='/tmp/post.rc'
        )

        self.log.info('Value of /tmp/post.rc file is [%s]', post_rc)
        if post_rc.strip() != '0':
            raise Exception('Post-script return code is non-zero')

        self.log.info('Verified post-script return code is 0')
