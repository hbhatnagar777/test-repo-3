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

"""


import time

from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Kubernetes.KubernetesHelper import KubernetesHelper
from VirtualServer.VSAUtils import VirtualServerUtils
from Kubernetes import KubernetesUtils
from AutomationUtils import machine
from Web.Common.page_object import TestStep

automation_config = config.get_config().Kubernetes


class TestCase(CVTestCase):
    test_step = TestStep()
    """Multi-tenancy entity check across tenants for Kubernetes
    """
    def __init__(self):
        super(TestCase, self).__init__()

        self.name = "Metallic - Multi-tenancy entity check across tenants for Kubernetes"
        self.utils = TestCaseUtils(self)
        self.admin_console = None
        self.server_name = None
        self.k8s_helper = None
        self.api_server_endpoint = None
        self.servicetoken = None
        self.access_node = None
        self.controller_id = None
        self.testbed_name = None
        self.deploy_name = None
        self.pvc_name = None
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
        self.tcinputs = {
            "DoNotSeeTenant": None
        }
        self.utils_path = VirtualServerUtils.UTILS_PATH
        self.k8s_config = None
        self.plan = None
        self.storageclass = None
        self.kubehelper = None
        self._do_not_see_tenant = None
        self.ring_name = None
        self.company_name = None
        self.proxy_obj = None
        self.hub_management = None
        self.tenant_user_name = None
        self._user_tenant = None
        self.client_list = []
        self.client_group_list = []
        self.agent_list = []
        self.instance_list = []
        self.subclient_list = []
        self.backupset_list = []
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
        self.destclientName = "k8sauto-{}".format(self.id)
        self.plan = self.tcinputs.get("Plan", automation_config.PLAN_NAME)
        self.access_node = self.tcinputs.get("AccessNode", None)
        self.k8s_config = self.tcinputs.get('ConfigFile', automation_config.KUBECONFIG_FILE)
        if self.access_node:
            self.controller = self.commcell.clients.get(self.access_node)
            self.controller_id = int(self.controller.client_id)
            self.proxy_obj = machine.Machine(self.controller)
        self._do_not_see_tenant = self.tcinputs['DoNotSeeTenant']

        current_user = self.inputJSONnode['commcell']['commcellUsername']
        self._user_tenant = self.commcell.users.get(current_user).user_company_name

        self.kubehelper = KubernetesHelper(self)

        # Initializing objects using KubernetesHelper
        self.kubehelper.load_kubeconfig_file(self.k8s_config)
        self.storageclass = self.tcinputs.get('StorageClass', self.kubehelper.get_default_storage_class_from_cluster())
        self.api_server_endpoint = self.kubehelper.get_api_server_endpoint()

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

        # Creating testbed namespace if not exists
        self.kubehelper.create_cv_namespace(self.namespace)

        # Creating namespace for restore if not exists
        self.kubehelper.create_cv_namespace(self.restore_namespace)

        # Create service account if doesn't exist
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.create_cv_serviceaccount(self.serviceaccount, sa_namespace)

        # Create cluster role binding
        crb_name = self.testbed_name + '-crb'
        cluster_role = self.tcinputs.get("ClusterRole", "cluster-admin")
        self.kubehelper.create_cv_clusterrolebinding(crb_name, self.serviceaccount, sa_namespace, cluster_role)

        time.sleep(30)
        self.servicetoken = self.kubehelper.get_serviceaccount_token(self.serviceaccount, sa_namespace)

        # Creating PVC
        self.pvc_name = self.testbed_name + '-pvc'
        self.kubehelper.create_cv_pvc(self.pvc_name, self.namespace, storage_class=self.storageclass)

        # Creating test pod
        self.deploy_name = self.testbed_name + '-deploy'
        self.kubehelper.create_cv_deployment(self.deploy_name, self.namespace, pvcname=self.pvc_name)
        self.content.append(self.namespace + '/' + self.deploy_name)
        time.sleep(30)

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
            raise CVTestCaseInitFailure(_exception) from _exception

    @test_step
    def run_backup(self, backup_level="INCREMENTAL"):
        """Run Backup step"""
        self.log.info("Step -- Add data and verify Backup")

        folder_name = "folder-" + str(int(time.time()))
        for pod in self.kubehelper.get_namespace_pods(self.namespace):
            self.kubehelper.create_random_cv_pod_data(pod, self.namespace, foldername=folder_name)
            time.sleep(10)

        job = self.subclient.backup(backup_level)
        self.log.info(f'Waiting for {backup_level} job {job.job_id} to complete')
        if not job.wait_for_completion():
            raise Exception(f"Failed to run backup with error: {job.delay_reason}")
        self.log.info(f'{backup_level} Backup Job [{job.job_id}] is complete')
        self.log.info("Run Backup Step complete")

    @test_step
    def check_user_list(self):
        """Check list of users for the current tenant"""
        success = True
        user_list = self.commcell.users.all_users
        do_not_see_tenant_lower = self._do_not_see_tenant.lower()
        for user in user_list:
            user_obj = self.commcell.users.get(user)
            user_name = user_obj.user_name
            user_tenant = user_obj.user_company_name
            if do_not_see_tenant_lower == user_tenant:
                self.log.error(f"User [{user_name}] belongs to forbidden tenant [{do_not_see_tenant_lower}]")
                success = False
            elif user_tenant != self._user_tenant.lower():
                self.log.error(f"User [{user_name}] belongs to tenant [{user_tenant}]")
                success = False
            else:
                self.log.info(f"User [{user_name}] is correctly associated with tenant [{self._user_tenant}]")

        if not success:
            raise Exception(f"Some users do not belong to tenant [{self._user_tenant}]")

    @test_step
    def check_user_group_list(self):
        """Check list of user groups for the current tenant"""
        success = True
        ug_list = self.commcell.user_groups.all_user_groups
        do_not_see_tenant_lower = self._do_not_see_tenant.lower()
        for ug in ug_list:
            ug_obj = self.commcell.user_groups.get(ug)
            ug_name = ug_obj.user_group_name
            ug_tenant = ug_obj.company_name.lower()
            if do_not_see_tenant_lower == ug_tenant:
                self.log.error(f"User group [{ug_name}] belongs to forbidden tenant [{do_not_see_tenant_lower}]")
                success = False
            elif ug_tenant != self._user_tenant.lower():
                self.log.error(f"User group [{ug_name}] belongs to tenant [{ug_tenant}]")
                success = False
            else:
                self.log.info(f"User group [{ug_name}] is correctly associated with tenant [{self._user_tenant}]")

        if not success:
            raise Exception(f"Some user groups do not belong to tenant [{self._user_tenant}]")

    @test_step
    def check_client_group_list(self):
        """Check list of client groups for current tenant"""

        success = True
        cg_list = self.commcell.client_groups.all_clientgroups
        do_not_see_tenant_lower = self._do_not_see_tenant.lower()
        for cl in cg_list:
            cl_obj = self.commcell.client_groups.get(cl)
            cl_name = cl_obj.clientgroup_name
            cl_props = cl_obj.properties.get('securityAssociations', {})
            cl_tag_with_company = cl_props.get('tagWithCompany', {})
            cl_tenant = cl_tag_with_company.get('providerDomainName').lower()

            if do_not_see_tenant_lower == cl_tenant:
                self.log.error(f"Client Group [{cl_name}] belongs to forbidden tenant [{do_not_see_tenant_lower}]")
                success = False
            elif cl_tenant != self._user_tenant.lower():
                self.log.error(f"Client Group [{cl_name}] belongs to tenant [{cl_tenant}]")
                success = False
            else:
                self.log.info(f"Client Group [{cl_name}] is correctly associated with tenant [{self._user_tenant}]")

                # check for all agents of this client
                self.client_group_list.append(cl_obj)
        if not success:
            raise Exception(f"Some client groups  do not belong to tenant [{self._user_tenant}]")

    @test_step
    def check_associated_client_list(self):
        """Check list of associated clients for all client groups for current tenant"""

        success = True
        for cg in self.client_group_list:
            self.log.info(f"Checking associated client list for Client Group [{cg.clientgroup_name}]")
            do_not_see_tenant_lower = self._do_not_see_tenant.lower()
            cl_list = cg.associated_clients
            for cl in cl_list:
                cl_obj = self.commcell.clients.get(cl)
                cl_name = cl_obj.client_name
                cl_tenant = cl_obj.company_name.lower()

                if do_not_see_tenant_lower == cl_tenant:
                    self.log.error(f"Client [{cl_name}] belongs to forbidden tenant [{do_not_see_tenant_lower}]")
                    success = False
                elif cl_tenant != self._user_tenant.lower():
                    self.log.error(f"Client [{cl_name}] belongs to tenant [{cl_tenant}]")
                    success = False
                else:
                    self.log.info(f"Client [{cl_name}] is correctly associated with tenant [{self._user_tenant}]")

        if not success:
            raise Exception(f"Some client groups  do not belong to tenant [{self._user_tenant}]")

    @test_step
    def check_plan_list(self):
        """Check list of plans for current tenant"""

        success = True
        plan_list = self.commcell.plans.all_plans
        do_not_see_tenant_lower = self._do_not_see_tenant.lower()
        for plan in plan_list:
            plan_obj = self.commcell.plans.get(plan)
            plan_name = plan_obj.plan_name
            plan_props = plan_obj.properties
            plan_tenant = plan_props['securityAssociations']['tagWithCompany']['providerDomainName'].lower()
            if do_not_see_tenant_lower == plan_tenant:
                self.log.error(f"Plan [{plan_name}] belongs to forbidden tenant [{do_not_see_tenant_lower}]")
                success = False
            elif plan_tenant != "commcell" and plan_tenant != self._user_tenant.lower():
                self.log.error(f"Plan [{plan_name}] belongs to tenant [{plan_tenant}]")
                success = False
            else:
                self.log.info(f"Plan [{plan_name}] is correctly associated with tenant [{self._user_tenant}]")
        if not success:
            raise Exception(f"Some plans do not belong to tenant [{self._user_tenant}]")

    @test_step
    def check_client_list(self):
        """Check list of clients for current tenant"""

        success = True
        cl_list = self.commcell.clients.all_clients
        do_not_see_tenant_lower = self._do_not_see_tenant.lower()
        for cl in cl_list:
            cl_obj = self.commcell.clients.get(cl)
            cl_name = cl_obj.client_name
            cl_tenant = cl_obj.company_name.lower()
            cl_props = cl_obj.properties.get('pseudoClientInfo', {})
            vsa_props = cl_props.get('virtualServerClientProperties', {})
            vs_instance_props = vsa_props.get('virtualServerInstanceInfo', {})
            vs_type = vs_instance_props.get('vsInstanceType', -1)

            # Skip clients which are not Kubernetes instance
            if vs_type != 20:
                continue

            if do_not_see_tenant_lower == cl_tenant:
                self.log.error(f"Client [{cl_name}] belongs to forbidden tenant [{do_not_see_tenant_lower}]")
                success = False
            elif cl_tenant != self._user_tenant.lower():
                self.log.error(f"Client [{cl_name}] belongs to tenant [{cl_tenant}]")
                success = False
            else:
                self.log.info(f"Client [{cl_name}] is correctly associated with tenant [{self._user_tenant}]")

                # check for all agents of this client
                if cl_obj not in self.client_list:
                    self.client_list.append(cl_obj)
        if not success:
            raise Exception(f"Some clients do not belong to tenant [{self._user_tenant}]")

    @test_step
    def check_hidden_client_list(self):
        """Check list of hidden clients for current tenant"""

        success = True
        cl_list = self.commcell.clients.hidden_clients
        do_not_see_tenant_lower = self._do_not_see_tenant.lower()
        for cl in cl_list:
            cl_obj = self.commcell.clients.get(cl)
            cl_name = cl_obj.client_name
            cl_tenant = cl_obj.company_name.lower()

            cl_props = cl_obj.properties.get('vmStatusInfo', {})
            vm_props = cl_props.get('vsaSubClientEntity', '')
            instance_name = vm_props.get('instanceName', '')
            if instance_name.lower() != 'kubernetes':
                continue

            if do_not_see_tenant_lower == cl_tenant:
                self.log.error(f"Client [{cl_name}] belongs to forbidden tenant [{do_not_see_tenant_lower}]")
                success = False
            elif cl_tenant != self._user_tenant.lower():
                self.log.error(f"Client [{cl_name}] belongs to tenant [{cl_tenant}]")
                success = False
            else:
                self.log.info(f"Client [{cl_name}] is correctly associated with tenant [{self._user_tenant}]")

        if not success:
            raise Exception(f"Some clients do not belong to tenant [{self._user_tenant}]")

    @test_step
    def check_agent_list(self):
        """Check list of Virtual Server agents for all clients of current tenant"""

        success = True
        for client_obj in self.client_list:
            agent_list = client_obj.agents.all_agents
            do_not_see_tenant_lower = self._do_not_see_tenant.lower()
            for agent in agent_list:

                if agent != 'virtual server':
                    continue

                agent_obj = client_obj.agents.get(agent)
                agent_name = agent_obj.agent_name
                agent_tenant = agent_obj.properties['securityAssociations']['tagWithCompany']['providerDomainName']
                agent_tenant = agent_tenant.lower()
                if do_not_see_tenant_lower == agent_tenant:
                    self.log.error(
                        f"Agent [{agent_name}] belongs to forbidden tenant [{do_not_see_tenant_lower}] " +
                        f" for client [{client_obj.client_name}]"
                    )
                    success = False
                elif agent_tenant != self._user_tenant.lower():
                    self.log.error(
                        f"Agent [{agent_name}] belongs to tenant [{agent_tenant}]" +
                        f" for client [{client_obj.client_name}]"
                    )
                    success = False
                else:
                    self.log.info(
                        f"Agent [{agent_name}] is correctly associated with tenant [{self._user_tenant}]" +
                        f" for client [{client_obj.client_name}]"
                    )

                    # check for all instances of this client
                    self.agent_list.append(agent_obj)

        if not success:
            raise Exception(f"Some agents do not belong to tenant [{self._user_tenant}]")

    @test_step
    def check_instance_list(self):
        """Check list of Kubernetes instances of all agents for current tenant"""

        success = True
        for agent_obj in self.agent_list:
            inst_list = agent_obj.instances.all_instances
            do_not_see_tenant_lower = self._do_not_see_tenant.lower()
            for inst in inst_list:
                in_obj = agent_obj.instances.get(inst)
                in_name = in_obj.instance_name

                if in_name.lower() != 'kubernetes':
                    continue

                in_client = in_obj.properties['instance']['clientName']
                in_tenant = in_obj.properties['instance']['entityInfo']['companyName'].lower()
                if do_not_see_tenant_lower == in_tenant:
                    self.log.error(
                        f"Instance [{in_name}] belongs to forbidden tenant [{do_not_see_tenant_lower}]" +
                        f" for client [{in_client}]"
                    )
                    success = False
                elif in_tenant != self._user_tenant.lower():
                    self.log.error(
                        f"Instance [{in_name}] belongs to tenant [{in_tenant}]" +
                        f" for client [{in_client}]"
                    )
                    success = False
                else:
                    self.log.info(
                        f"Instance [{in_name}] is correctly associated with tenant [{self._user_tenant}]" +
                        f" for client [{in_client}]"
                    )

                    # Check backup set list for instance
                    self.instance_list.append(in_obj)
        if not success:
            raise Exception(f"Some Instance do not belong to tenant [{self._user_tenant}]")

    @test_step
    def check_backupset_list(self):
        """Check list of all backupsets for the Kubernetes instance for current tenant"""

        success = True
        for instance_obj in self.instance_list:
            bset_list = instance_obj.backupsets.all_backupsets
            do_not_see_tenant_lower = self._do_not_see_tenant.lower()
            for backupset in bset_list:
                bs_obj = instance_obj.backupsets.get(backupset)
                bs_name = bs_obj.backupset_name
                bs_tenant = bs_obj.properties['securityAssociations']['tagWithCompany']['providerDomainName'].lower()
                bs_client = bs_obj.properties['backupSetEntity']['clientName']
                if do_not_see_tenant_lower == bs_tenant:
                    self.log.error(
                        f"BackupSet [{bs_name}] belongs to forbidden tenant [{do_not_see_tenant_lower}]" +
                        f" for client [{bs_client}]"
                    )
                    success = False
                elif bs_tenant != self._user_tenant.lower():
                    self.log.error(
                        f"BackupSet [{bs_name}] belongs to tenant [{bs_tenant}]" +
                        f" for client [{bs_client}]"
                    )
                    success = False
                else:
                    self.log.info(
                        f"BackupSet [{bs_name}] is correctly associated with tenant [{self._user_tenant}]" +
                        f" for client [{bs_client}]"
                    )

                    # Check backup set list for instance
                    self.backupset_list.append(bs_obj)
        if not success:
            raise Exception(f"Some BackupSets do not belong to tenant [{self._user_tenant}]")

    @test_step
    def check_subclient_list(self):
        """Check list of subclients for all backupsets for current tenant"""

        success = True
        for backupset_obj in self.backupset_list:
            sc_list = backupset_obj.subclients.all_subclients
            do_not_see_tenant_lower = self._do_not_see_tenant.lower()
            for subclient in sc_list:
                sc_obj = backupset_obj.subclients.get(subclient)
                sc_name = sc_obj.name
                sc_tenant = sc_obj.properties['commonProperties'][
                    'securityAssociations']['tagWithCompany']['providerDomainName'].lower()
                sc_client = sc_obj.properties['subClientEntity']['clientName']
                if do_not_see_tenant_lower == sc_tenant:
                    self.log.error(
                        f"Subclient [{sc_name}] belongs to forbidden tenant [{do_not_see_tenant_lower}]" +
                        f" for client [{sc_client}]"
                    )
                    success = False
                elif sc_tenant != self._user_tenant.lower():
                    self.log.error(
                        f"Subclient [{sc_name}] belongs to tenant [{sc_tenant}]" +
                        f" for client [{sc_client}]"
                    )
                    success = False
                else:
                    self.log.info(
                        f"Subclient [{sc_name}] is correctly associated with tenant [{self._user_tenant}]" +
                        f" for client [{sc_client}]"
                    )

        if not success:
            raise Exception(f"Some Subclients do not belong to tenant [{self._user_tenant}]")

    @test_step
    def check_job_list(self):
        """Check list of all jobs for current tenant"""

        job_list = self.commcell.job_controller.all_jobs(limit=50, job_summary='full')
        do_not_see_tenant_lower = self._do_not_see_tenant.lower()
        success = True
        for job, summary in job_list.items():
            job_tenant = summary['company']['companyName'].lower()
            if do_not_see_tenant_lower == job_tenant:
                self.log.error(f"Job [{job}] can be seen by forbidden tenant [{do_not_see_tenant_lower}]")
                success = False
            elif job_tenant != self._user_tenant.lower():
                self.log.error(f"Job [{job}] can be seen by tenant [{job_tenant}]")
                success = False
            else:
                self.log.info(f"Job [{job}] is correctly visible to tenant [{self._user_tenant}]")

        if not success:
            raise Exception(f"Some jobs should not be visible to tenant [{self._user_tenant}]")

    @TestStep()
    def delete_testbed(self):
        """
        Delete the generated testbed
        """

        self.kubehelper.delete_cv_namespace(self.namespace)
        self.kubehelper.delete_cv_namespace(self.restore_namespace)

        # Delete cluster role binding
        crb_name = self.testbed_name + '-crb'
        self.kubehelper.delete_cv_clusterrolebinding(crb_name)

        # Delete service account
        sa_namespace = self.tcinputs.get("ServiceAccountNamespace", "default")
        self.kubehelper.delete_cv_serviceaccount(sa_name=self.serviceaccount, sa_namespace=sa_namespace)

        KubernetesUtils.delete_cluster(self, self.clientName)

    def run(self):
        """
        Run the Testcase
        """
        try:

            # Step 1 - Run FULL and INC jobs for newly created Kubernetes client
            self.run_backup(backup_level='FULL')
            self.run_backup()

            # Step 2 - Check association of jobs for current tenant
            self.check_job_list()

            # Step 3 - Check list of users and user groups visible to tenant
            self.check_user_list()
            self.check_user_group_list()

            # Step 4 - Check list of plans visible to tenant
            self.check_plan_list()

            # Step 5 - Check list of clients, hidden clients, client groups and associated clients in client group
            self.check_client_list()
            self.check_client_group_list()
            self.check_associated_client_list()
            self.check_hidden_client_list()

            # Step 6 - Check agent and instance list for all clients
            self.check_agent_list()
            self.check_instance_list()

            # Step 7 - Check list of all backupsets and agents for all clients
            self.check_backupset_list()
            self.check_subclient_list()
            self.log.info("TEST CASE COMPLETED SUCCESSFULLY")

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.log.info("Step -- Delete testbed, delete client ")
            self.delete_testbed()
