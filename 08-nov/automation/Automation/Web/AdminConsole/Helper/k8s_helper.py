# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""

Helper file for Kubernetes related operations on command center.

Classes defined in this file:

    K8sHelper:         class for Kubernetes command center related operations.

        __init__()                              --  Constructor for creating a k8s cluster on command center

        create_k8s_cluster()                    --  create kubernetes clusters from command center

        add_application_group()                 --  add application group

        add_application_group_from_cluster()    --  add application group from cluster details page

        delete_k8s_cluster()                    --  delete kubernetes cluster from command center

        delete_k8s_app_grp()                    --  delete application group from command center

        populate_test_data()                    --  populatest test data

        run_backup_job()                        --  initiate backup job and verify job completed

        run_app_file_restore_job()              --  drop table

        run_manifest_restore_job()              --  initiate manifest restore and verify job complete

        run_fs_dest_restore_job()               --  initiate fs destination restore job

        run_fullapp_restore_job()               --  initiate full app restore and verify job complete

        run_namespace_restore_job()             --  initiate namespace level restore and verify job complete

        enable_etcd_protection()                --  enable etcd protection for a cluster

        go_to_appgroup_details()                --  navigate to application group details for application group

        go_to_appgroup_tab_in_cluster()         --  navigate to app group tab in cluster details page

        go_to_cluster_detail()                  --  navigate to cluster details page

        navigate_to_etcd()                      --  navigate to etcd application group for a cluster

        enable_stateless_filter()               --  enable stateless application filter for application group

        change_sa_and_sa_token()                --  Change ServiceAccount and ServiceAccountToken

        change_image_url_and_image_secret()     --  Change Image URL and Image Pull Secret for a cluster

        change_config_namespace()               --  Change Configuration Namespace for a cluster

        change_wait_timeout()                   --  Change Wait Timeout settings for a cluster

        change_no_of_readers()                  --  Changes Number of Readers for a Application Group

        change_worker_pod_resource_settings()   --  Change Worker Pod Resource Settings for a Application Group

        enable_live_volume_fallback()           --  Enables Live Volume Fallback for a application group


"""

import time

from selenium.common import NoSuchElementException

from Kubernetes.KubernetesHelper import KubernetesHelper
from VirtualServer.VSAUtils.OptionsHelper import VSAMetallicOptions
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Hub.constants import HubServices, VMKubernetesTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.kubernetes import KubernetesHub
from Web.AdminConsole.K8s.application_group_details import AppGroupDetails
from Web.AdminConsole.K8s.modifiers import ConfigureModifiers
from Web.AdminConsole.K8s.restore import FullAppRestore, ApplicationFileRestore, FSDestinationRestore, \
    ManifestRestore, NamespaceRestore
from Web.AdminConsole.Components.dialog import RBackup as Backup
from Web.AdminConsole.K8s.clusters import K8sClusters, AddK8sCluster
from Web.AdminConsole.K8s.cluster_details import Overview, Configuration
from Web.AdminConsole.K8s.application_groups import AppGroups
from Web.Common.exceptions import CVTestStepFailure, CVWebAutomationException
from Web.AdminConsole.Components.alert import Alert


class K8sHelper:
    """
    Helper class for Kubenertes cluster related operations
    """

    def __init__(self, admin_console, testcase):
        """Constructor for creating the K8s helper object"""
        self._admin_console = admin_console
        self.__metallic = testcase.addProp.lower() == "metallic"
        self.__clusters = K8sClusters(self._admin_console)
        self.__k8s_server = AddK8sCluster(self._admin_console)
        self.__app_group = AppGroups(self._admin_console)
        self.__app_group_details = AppGroupDetails(self._admin_console)
        self.__overview = Overview(self._admin_console)
        self.__configuration = Configuration(self._admin_console)
        self.__hub_dashboard = Dashboard(self._admin_console, HubServices.vm_kubernetes, VMKubernetesTypes.kubernetes)
        self.__configure_modifiers = ConfigureModifiers(self._admin_console)

        # For Metallic OEM : Initialize KubernetesHub instead of KubernetesSetup

        self.metallic_options = VSAMetallicOptions(tc_inputs=testcase.tcinputs)
        self.__k8s_setup = KubernetesHub(self._admin_console, metallic_options=self.metallic_options)

        self.__jobs = Jobs(self._admin_console)
        self.__wizard = None
        self.__restore = None
        self.__full_app_restore = FullAppRestore(admin_console=self._admin_console)
        self.__namespace_restore = NamespaceRestore(admin_console=self._admin_console)
        self.kubehelper = KubernetesHelper(testcase)

        self.__wizard_caller_map = {
            "Access Node": self.__k8s_setup.select_access_nodes,
            "Plan": self.__k8s_setup.select_plan,
            "Add Cluster": self.__k8s_setup.add_cluster,
            "Select Cluster": self.__k8s_setup.select_cluster,
            "Add Application Group": self.__k8s_setup.add_application_group,
            "Summary": self.__k8s_setup.validate_summary_step,
        }

        if self.__metallic:
            self.__wizard_caller_map.update({
                "Select Kubernetes service or distribution": self.__k8s_setup.select_deployment_method,
                "Backup method overview": self.__k8s_setup.select_backup_method,
                "Select Backup Gateways": self.__k8s_setup.select_access_nodes,
                "Backup Gateway": self.__k8s_setup.select_access_nodes,
                "Local Storage": self.__k8s_setup.configure_local_storage,
                "Cloud Storage": self.__k8s_setup.configure_cloud_storage,
                "Region": self.__k8s_setup.configure_region,
            })

    def __wait_for_job_success(self, job_id):
        """Wait for Job to complete"""
        jd = self.__jobs.job_completion(job_id=job_id)
        job_status = jd[self._admin_console.props['Status']]
        assert job_status.lower() == "completed", \
            f"Job {job_id} failed to complete, Status : {job_status}"

    def wizard_step_caller(self, step, **kwargs):
        """Call corresponding method based on wizard step
        """
        is_restore_wizard = kwargs.get("is_restore_wizard", False)
        self._admin_console.log.info(f"{'*' * 40} Wizard Step {'*' * 40}")
        self._admin_console.log.info(f"{' ' * 10}{step}")
        self._admin_console.log.info("*" * 93)
        callable_method = self.__wizard_caller_map[step]
        self._admin_console.log.info(f"Calling function [{callable_method.__name__}] with kwargs [{kwargs}]")
        callable_method(**kwargs)

    def configure_new_restore_modifier(self, modifier_name, selector_dict, action_dict):
        """
        Configures a new restore modifier

        Args:


            modifier_name:              (str)   name of the restore modifier

            selector_dict:              (dict)  Key:Value pair for selectors
                                                {
                                                    name: <VALUE>

                                                    namespace: <VALUE>

                                                    kind: <VALUE>
                                                    labels:{
                                                        label1: value1,
                                                        label2: value2,
                                                        ...
                                                    }
                                                    field:{
                                                        path: <PATH>
                                                        exact: <BOOLEAN TRUE FALSE>
                                                        criteria: <Contains / NotContains>
                                                        value: value
                                                    }
                                                }

            action_dict:                (List<dict>)  list of dict with Key: Value pairs
                                                [{
                                                   action: <ACTION>,
                                                   parameters:
                                                   path:
                                                   value:
                                                   newValue
                                                } <Leave empty if not required>
                                                ...]

        """

        self.__configure_modifiers.add_name(name=modifier_name)

        self.__configure_modifiers.add_selector(selector_dict)

        self.__configure_modifiers.add_action(action_list=action_dict)

        # Save the modifier
        self.__configure_modifiers.save()

    def go_to_restore_modifier_config_page(self, cluster_name):
        """
        Navigate to restore modifier config page
        """
        self.go_to_cluster_detail(cluster_name=cluster_name)
        self.__overview.access_configuration()
        time.sleep(30)
        self.__configuration.navigate_to_modifiers()

    def configure_new_kubernetes_cluster(self, **kwargs):
        """New configuration of Kubernetes cluster (Finish Guided Setup from start to end)
        """

        self.__clusters.add_cluster()

        if self.__metallic:
            if "deployment_method" not in kwargs:
                kwargs.update({"deployment_method": "ONPREM"})
            self.wizard_step_caller(step="Select Kubernetes service or distribution", **kwargs)
            self.wizard_step_caller(step="Backup method overview", **kwargs)

        self.__wizard = Wizard(adminconsole=self._admin_console)
        while True:
            try:
                current_wizard = self.__wizard.get_active_step()
            except NoSuchElementException:
                self._admin_console.log.warning("Not on a wizard step. Skipping since this may be valid scenario")
                break
            self.wizard_step_caller(step=current_wizard, **kwargs)

    def create_k8s_cluster(self, api_server, name, authentication, username, password, access_nodes=None, **kwargs):
        """Create kubernetes cluster WITHOUT an app group.

            Args:

                 api_server     (str)       --  API Server endpoint of Kubernetes cluster

                 name           (str)       --  Name of the cluster

                 authentication (str)       --  Authentication type for cluster

                 username       (str)       --  Service account name / Username

                 password       (str)       --  Service token / password

                 access_nodes   (str/list)  --  List of access nodes to select for cluster

        """
        self._admin_console.navigator.navigate_to_kubernetes()
        self._admin_console.navigator.navigate_to_k8s_clusters()
        if self.__clusters.is_cluster_exists(name):
            self.delete_k8s_cluster(name)
        self.__clusters.add_cluster()
        kwargs.update({
            "cluster_name": name,
            "api_endpoint": api_server,
            "authentication": authentication,
            "service_account": username,
            "service_token": password,
            "plan_name": "",
            "access_nodes": access_nodes,
            "get_first_plan": True,
            "deployment_method": kwargs.get('deployment_method', "ONPREM")
        })

        # Order of steps :
        # Deployment Method (METALLIC) --> Access Node --> Cloud Storage (METALLIC) --> Local Storage (METALLIC) -->
        # Plan --> Add Cluster --> Add Application Group --> Summary
        steps = ["Access Node", "Plan", "Add Cluster"]
        if self.__metallic:
            steps = ["Select Kubernetes service or distribution", "Backup method overview", "Select Backup Gateways",
                     "Local Storage", "Cloud Storage", "Plan", "Add Cluster"]

        for step in steps:
            self.wizard_step_caller(step=step, **kwargs)

        # Wait 30 sec before cancel
        time.sleep(30)

        # Close the Plan and add app group step if present
        # We will create app group from separate function
        self.__k8s_setup.exit_wizard()
        self._admin_console.wait_for_completion()

        self._admin_console.navigator.navigate_to_kubernetes()
        self._admin_console.navigator.navigate_to_k8s_clusters()

        if not self.__clusters.is_cluster_exists(name):
            raise CVTestStepFailure("Kubernetes cluster [%s] is not getting created" % name)
        else:
            self._admin_console.log.info("Successfully Created Kubernetes cluster: [%s]" % name)

    def delete_k8s_app_grp_content(self, row_idx, cluster, app_grp):
        """
        Deletes a content from the app group preview pane
        """

        __app_group_details = self.go_to_appgroup_detail(cluster_name=cluster, appgroup_name=app_grp)
        self.__app_group_details.delete_from_manage_content(row_idx=row_idx)

    def modify_app_group_content(self, cluster, app_grp, content, validate_matrix):
        """
        Modify the content of the app group and validate the changes
        """
        __app_group_details = self.go_to_appgroup_detail(
            cluster_name=cluster,
            appgroup_name=app_grp
        )
        __app_group_details.modify_app_group_contents(content=content, validate_matrix=validate_matrix)

    def configure_backup_filters(
            self, cluster, app_grp, backup_filters, remove_existing_filters, exclude_dependencies=True):
        """
        Configure backup filters
        """
        __app_group_details = self.go_to_appgroup_detail(
            cluster_name=cluster,
            appgroup_name=app_grp
        )
        self.__app_group_details.configure_backup_filters(
            backup_filters,
            remove_existing_filters=remove_existing_filters,
            exclude_dependencies=exclude_dependencies
        )

    def add_application_group(self, cluster_name, app_group_name, content, plan, exclusion=None, intellisnap=False,
                              **kwargs):
        """Add application group from wizard

            Args:

                cluster_name    (str)       --  Name of the cluster

                app_group_name  (str)       --  Name of the application group to create

                plan            (str)       --  Plan to select

                content         (list)      --  Set content for application group

                exclusion       (list)      --  Filters for content

                intellisnap     (bool)      --  Toggle intellisnap if enabled
        """
        self._admin_console.navigator.navigate_to_kubernetes()
        self.__app_group.select_add_application_group()

        kwargs.update({
            "cluster_name": cluster_name,
            "app_group_name": app_group_name,
            "plan_name": plan,
            "backup_content": content,
            "filter_content": exclusion,
            "intelli_snap": intellisnap,
            "get_first_plan": False
        })

        steps = ["Select Cluster", "Plan", "Add Application Group"]

        for step in steps:
            self.wizard_step_caller(step=step, **kwargs)

        self._admin_console.navigator.navigate_to_kubernetes()
        self._admin_console.navigator.navigate_to_k8s_appgroup()

        if not self.__app_group.has_app_group(app_group_name):
            raise CVTestStepFailure("Kubernetes Application Group [%s] is not getting created" % app_group_name)
        self._admin_console.log.info("Successfully Created Application Group : [%s]" % app_group_name)

    def add_app_group_from_cluster(self, cluster_name, app_group_name, content, plan, exclusion=None, snap=False,
                                   **kwargs):
        """
        Add application group from cluster details page

        Args:

                cluster_name    (str)       --  Name of the cluster

                app_group_name  (str)       --  Name of the application group to create

                plan            (str)       --  Plan to select

                content         (list)      --  Set content for application group

                exclusion       (list)      --  Filters for content

                snap            (bool)      --  Toggle intellisnap if enabled

        """
        self.go_to_cluster_detail(cluster_name=cluster_name)
        self.__overview.add_application_group()

        # From cluster detail page, select cluster step should be skipped
        self.__k8s_setup.click_next()

        kwargs.update({
            "app_group_name": app_group_name,
            "plan_name": plan,
            "backup_content": content,
            "filter_content": exclusion,
            "intelli_snap": snap,
            "get_first_plan": False
        })

        steps = ["Plan", "Add Application Group"]

        for step in steps:
            self.wizard_step_caller(step=step, **kwargs)

        self._admin_console.navigator.navigate_to_kubernetes()
        self._admin_console.navigator.navigate_to_k8s_appgroup()
        if not self.__app_group.has_app_group(app_group_name):
            raise CVTestStepFailure("Kubernetes app group [%s] is not getting created" % app_group_name)
        self._admin_console.log.info("Successfully Created app group : [%s]" % app_group_name)

    def delete_k8s_app_grp(self, name):
        """Delete application group and verify app group is deleted

            Args:

                name        (str)       --  Name of application group to delete

        """
        self._admin_console.navigator.navigate_to_kubernetes()
        self._admin_console.navigator.navigate_to_k8s_appgroup()
        self.__app_group.action_delete_app_groups(name)
        if self.__app_group.has_app_group(name):
            raise CVTestStepFailure("Kubernetes application group [%s] is not getting deleted" % name)
        self._admin_console.log.info("Deleted application group [%s] from command center successfully" % name)

    def delete_k8s_restore_modifier(self, name, cluster_name):
        """
        Deletes a restore modifier
        """

        self.go_to_restore_modifier_config_page(cluster_name=cluster_name)
        self.__configure_modifiers.delete_modifier(name=name)
        self._admin_console.log.info(f"Modifier [{name}] deleted")

    def delete_k8s_cluster(self, cluster_name):
        """Delete kubernetes cluster and verify cluster is deleted

            Args:

                cluster_name        (str)       --  Name of cluster to delete

        """

        self._admin_console.navigator.navigate_to_kubernetes()
        self._admin_console.navigator.navigate_to_k8s_clusters()
        self.__clusters.delete_cluster_name(cluster_name)
        if self.__clusters.is_cluster_exists(cluster_name):
            raise CVTestStepFailure("Kubernetes cluster [%s] is not getting deleted" % cluster_name)
        self._admin_console.log.info("Deleted cluster [%s] from command center successfully" % cluster_name)

    def run_backup_job(self, cluster_name=None, app_group_name=None, backup_level='FULL'):
        """Initiate the backup and verify backup job is completed
            Args:

                cluster_name    (str)   :   Name of the cluster

                app_group_name  (str)   :   Name of the application group to run backup for

                backup_level    (str)   :   Backup Type as string

            Returns:

                Job ID of the successful job

            Raise:
                Exception if job fails
        """

        if backup_level.lower() == 'full':
            backup_type_enum = Backup.BackupType.FULL
        elif backup_level.lower() == 'incremental':
            backup_type_enum = Backup.BackupType.INCR
        elif backup_level.lower() == 'synthetic_full':
            backup_type_enum = Backup.BackupType.SYNTH
        else:
            raise CVWebAutomationException("Invalid backup type selected for solution Kubernetes")

        # If cluster_name and app_group_name is passed, then navigate to app group details first
        if cluster_name and app_group_name:
            self.go_to_appgroup_detail(cluster_name=cluster_name, appgroup_name=app_group_name)

        self._admin_console.log.info("Run [%s] backup job", backup_level.upper())
        _job_id = self.__app_group_details.backup(backup_type_enum)
        self.__wait_for_job_success(job_id=_job_id)
        self._admin_console.log.info(f"Backup job [{_job_id}] completed successfully.")

        return _job_id

    def attempt_restore_job(self, cluster_name, app_group_name=None, restore_type='Files'):
        """
        Negative scenario. Test if restore files can be viewed

        Args:

                cluster_name        (str)   --  Name of cluster

                app_group_name      (str)   --  Name of application group

                restore_type        (str)   --  Type of restore to perform
        """

        if app_group_name:
            self.go_to_appgroup_detail(cluster_name=cluster_name, appgroup_name=app_group_name)
        self.__app_group_details.restore()
        try:
            if restore_type == 'Files':
                self.__restore = ApplicationFileRestore(self._admin_console)
            elif restore_type == 'Manifest':
                self.__restore = ManifestRestore(self._admin_console)
            elif restore_type == 'Application':
                self.__restore = FullAppRestore(self._admin_console)
            else:
                self.__restore = NamespaceRestore(self._admin_console)
        except CVWebAutomationException as e:
            self._admin_console.log.info(f"{restore_type} type restore not found in the list.")
            return
        self.__restore.select_restore_type()
        try:
            alert = Alert(self._admin_console)
            self._admin_console.log.info(alert.get_content())
        except CVWebAutomationException as exp:
            self._admin_console.log.info(f"No alert message. Failing the TC")

    def run_app_file_restore_job(
            self, cluster_name, destination_namespace, destination_pvc, file_path, app_group_name=None, **kwargs):
        """Initiate restore and verify restore job is completed"""

        destination_cluster = kwargs.get('destination_cluster', cluster_name)
        destination_path = kwargs.get('destination_path', '/mnt/data/')
        inplace = kwargs.get('inplace', False)
        unconditional_overwrite = kwargs.get('unconditional_overwrite', False)
        access_node = kwargs.get('access_node', 'Automatic')
        file_list = kwargs.get('file_list', None)

        # If app_group_name is passed, then navigate to app group details first
        if app_group_name:
            self.go_to_appgroup_detail(cluster_name=cluster_name, appgroup_name=app_group_name)
        self.__app_group_details.restore()

        self.__restore = ApplicationFileRestore(self._admin_console)
        self.__restore.select_restore_type()
        self.__restore.select_for_restore(path=file_path, selection=file_list)
        self.__restore.select_restore()

        self.__restore.run_app_file_restore(
            access_node=access_node,
            destination_namespace=destination_namespace,
            destination_pvc=destination_pvc,
            unconditional_overwrite=unconditional_overwrite,
            inplace=inplace,
            destination_cluster=destination_cluster,
            path=destination_path
        )

        self._admin_console.log.info("Run Application Files Restore to PVC job")
        self.__wait_for_job_success(self._admin_console.get_jobid_from_popup(wait_time=5))
        self._admin_console.log.info("Application Files Restore to PVC completed successfully")

    def run_fs_dest_restore_job(
            self, cluster_name, file_path, destination_client, destination_path, app_group_name=None, **kwargs):
        """Initiate restore and verify restore job is completed

        Args:

            file_path               (str)   --  Path for the files to restore

            destination_client      (str)   --  Target client for restore

            destination_path        (str)   --  Destination path at target

            cluster_name            (str)   --  Source cluster

            app_group_name          (str)   --  Name of application group to perform restore

        Kwargs:

            username                (str)   --  Impersonate username

            password                (str)   --  Impersonate password

            file_list               (list)  --  List of files paths to restore

            unconditional_overwrite (bool)  --  To select unconditional overwrite

        """

        unconditional_overwrite = kwargs.get('unconditional_overwrite', False)
        file_list = kwargs.get('file_list', None)
        username = kwargs.get('username', None)
        password = kwargs.get('password', None)
        skip_restore_type = kwargs.get('skip_restore_type', False)

        # If app_group_name is passed, then navigate to app group details first
        if app_group_name:
            self.go_to_appgroup_detail(cluster_name=cluster_name, appgroup_name=app_group_name)
        self.__app_group_details.restore()

        self.__restore = FSDestinationRestore(self._admin_console)
        if not skip_restore_type:
            self.__restore.select_restore_type()
        self.__restore.select_for_restore(path=file_path, selection=file_list)
        self.__restore.select_restore()
        self.__restore.perform_fs_destination_restore(
            access_node=destination_client,
            path=destination_path,
            unconditional_overwrite=unconditional_overwrite
        )
        self._admin_console.log.info("Run Application Files Restore to FS Destination job")
        self.__wait_for_job_success(self._admin_console.get_jobid_from_popup(wait_time=5))
        self._admin_console.log.info("Application Files Restore to FS Destination completed successfully")

    def run_manifest_restore_job(
            self, cluster_name, source_app, destination_client, destination_path, app_group_name=None, **kwargs):
        """Initiate manifest restore and verify restore job is completed

        Args:

            source_app              (str)   --  Target namespace for restore

            destination_client      (str)   --  Target client for restore

            destination_path        (str)   --  Destination path at target

            cluster_name            (str)   --  Source cluster

            app_group_name          (str)   --  Name of application group to perform restore

        Kwargs:

            username                (str)   --  Impersonate username

            password                (str)   --  Impersonate password

            file_list               (list)  --  List of files paths to restore

            unconditional_overwrite (bool)  --  To select unconditional overwrite

        """
        unconditional_overwrite = kwargs.get('unconditional_overwrite', False)
        file_list = kwargs.get('file_list', None)
        username = kwargs.get('username', None)
        password = kwargs.get('password', None)

        # If app_group_name is passed, then navigate to app group details first
        if app_group_name:
            self.go_to_appgroup_detail(cluster_name=cluster_name, appgroup_name=app_group_name)
        self.__app_group_details.restore()

        self.__restore = ManifestRestore(self._admin_console)
        self.__restore.select_restore_type()
        self.__restore.select_for_restore(path=source_app, selection=file_list, use_tree=False)
        self.__restore.select_restore()

        # Modal opens here
        self.__restore.fill_manifest_restore_modal(
            access_node=destination_client,
            path=destination_path,
            unconditional_overwrite=unconditional_overwrite
        )

        # Wait for restore job to complete
        self.__wait_for_job_success(self._admin_console.get_jobid_from_popup(wait_time=5))
        self._admin_console.log.info("Manifest Restore to destination client completed successfully")

    def run_fullapp_restore_job(self, cluster_name, restore_namespace=None, app_group_name=None, **kwargs):
        """
        Function to initiate full app restore and verify restore job is completed

        Args:

            restore_namespace       (str)   --  Target namespace for restore

            cluster_name            (str)   --  Source cluster

            app_group_name          (str)   --  Name of application group to perform restore

        Kwargs:

            destination_cluster     (str)   --  Target cluster to restore

            storage_class           (str)   --  Storage class for applications at target

            restore_name_map        (dict)  --  Mapping for application names at restore

            application_list        (list)  --  List of applications to restore

            inplace                 (bool)  --  To run inplace restore

            unconditional_overwrite (bool)  --  To select unconditional overwrite

            access_node             (str)   --  Access node to select for restore

            modifier_list           (list)  --  List of modifiers to be applied

            source_modifier         (bool)  --  To choose modifiers from source cluster. If you want to choose modifiers
                                                from destination cluster, pass as false.

        """

        # Initialize all variables needed
        destination_cluster = kwargs.get('destination_cluster', cluster_name)
        storage_class = kwargs.get('storage_class', 'Original')
        restore_name_map = kwargs.get('restore_name_map', {})
        application_list = kwargs.get('application_list', [])
        inplace = kwargs.get('inplace', False)
        unconditional_overwrite = kwargs.get('unconditional_overwrite', False)
        access_node = kwargs.get('access_node', 'Automatic')
        modifier_list = kwargs.get('modifier_list', None)
        source_modifier = kwargs.get('source_modifier', True)

        # Create app_info dictionary to be used in wizard step 2
        app_info = {}
        for app in application_list:
            app_info[app] = {
                'new_name': restore_name_map.get(app),
                'new_namespace': restore_namespace,
                'new_sc': storage_class
            }

        # If app_group_name is passed, then navigate to app group details first
        if app_group_name:
            self.go_to_appgroup_detail(cluster_name=cluster_name, appgroup_name=app_group_name)
        self.__app_group_details.restore()

        # Select restore type and enter inputs
        self.__restore = FullAppRestore(self._admin_console)
        self.__restore.select_restore_type()
        if not application_list:
            application_list = self.__restore.get_application_list()
        self.__restore.select_for_restore(path='/', selection=application_list)
        app_info = {}
        for app in application_list:
            app_info[app] = {
                'new_name': restore_name_map.get(app),
                'new_namespace': restore_namespace,
                'new_sc': storage_class
            }
        self.__restore.select_restore()

        # Wizard steps begin here
        # Order of steps
        # Choose Destination --> Applications --> Restore Options --> Summary

        self.__wizard = Wizard(adminconsole=self._admin_console)
        while True:
            try:
                current_wizard = self.__wizard.get_active_step()
            except NoSuchElementException:
                self._admin_console.log.warning("Not on a wizard step. Skipping since this may be valid scenario")
                break
            if current_wizard == 'Destination':
                self.__restore.select_destination(
                    destination_cluster=destination_cluster,
                    access_node=access_node,
                    inplace=inplace
                )
            elif current_wizard == 'Applications':
                self.__restore.confirm_applications(
                    app_info=app_info,
                    application_list=application_list,
                    inplace=inplace
                )
            elif current_wizard == 'Restore Options':
                self.__restore.select_restore_options(
                    inplace=inplace,
                    unconditional_overwrite=unconditional_overwrite,
                    source_modifier=source_modifier,
                    modifier_list=modifier_list
                )
            elif current_wizard == 'Summary':
                self.__restore.validate_summary()
                break
        self.__wait_for_job_success(self._admin_console.get_jobid_from_popup(wait_time=5))
        self._admin_console.log.info("Full Application Restore job completed successfully")

    def run_namespace_restore_job(self, cluster_name, app_group_name=None, **kwargs):
        """
        Function to initiate namespace level restore and verify restore job is completed

        Args:

            cluster_name            (str)   --  Source cluster

            app_group_name          (str)   --  Name of application group to perform restore

        Kwargs:

            destination_cluster     (str)   --  Target cluster to restore

            storage_class_map       (dict)  --  Storage class mapping for namespace at target

            restore_namespace_map   (dict)  --  Mapping for target namespaces at restore

            namespace_list          (list)  --  List of applications to restore

            inplace                 (bool)  --  To run inplace restore

            unconditional_overwrite (bool)  --  To select unconditional overwrite

            access_node             (str)   --  Access node to select for restore

            modifier_list           (str)   --  List of modifiers to select for restore

            source_modifier         (bool)  -- True to select modifier from source

        """

        # Initialize all variables needed
        destination_cluster = kwargs.get('destination_cluster', cluster_name)
        storage_class_map = kwargs.get('storage_class_map', None)
        restore_namespace_map = kwargs.get('restore_namespace_map', {})
        namespace_list = kwargs.get('namespace_list', None)
        inplace = kwargs.get('inplace', False)
        unconditional_overwrite = kwargs.get('unconditional_overwrite', False)
        access_node = kwargs.get('access_node', 'Automatic')
        modifier_list = kwargs.get('modifier_list', None)
        source_modifier = kwargs.get('source_modifier', True)

        # If app_group_name is passed, then navigate to app group details first
        app_group_details = self.go_to_appgroup_detail(cluster_name=cluster_name, appgroup_name=app_group_name)
        app_group_details.restore()

        # Select restore type and enter inputs
        self.__restore = NamespaceRestore(self._admin_console)
        self.__restore.select_restore_type()
        self.__restore.select_for_restore(path='/', selection=namespace_list)

        if not namespace_list:
            namespace_list = self.__restore.get_application_list(column_name='Namespace')

        namespace_info = {}
        for namespace in namespace_list:
            namespace_info[namespace] = {
                'new_name': restore_namespace_map.get(namespace),
                'sc_mapping': storage_class_map
            }
        self.__restore.select_restore()

        # Wizard steps begin here
        # Order of steps
        # Choose Destination --> Namespaces --> Restore Options --> Summary

        self.__wizard = Wizard(adminconsole=self._admin_console)
        while True:
            try:
                current_wizard = self.__wizard.get_active_step()
            except NoSuchElementException:
                self._admin_console.log.warning("Not on a wizard step. Skipping since this may be valid scenario")
                break
            if current_wizard == 'Destination':
                self.__restore.select_destination(
                    destination_cluster=destination_cluster,
                    access_node=access_node,
                    inplace=inplace
                )
            elif current_wizard == 'Namespaces':
                self.__restore.confirm_namespaces(
                    namespace_info=namespace_info,
                    namespace_list=namespace_list,
                    inplace=inplace
                )
            elif current_wizard == 'Restore Options':
                self.__restore.select_restore_options(
                    inplace=inplace,
                    source_modifier=source_modifier,
                    unconditional_overwrite=unconditional_overwrite,
                    modifier_list=modifier_list
                )
            elif current_wizard == 'Summary':
                self.__restore.validate_summary()
                break
        self.__wait_for_job_success(self._admin_console.get_jobid_from_popup(wait_time=5))
        self._admin_console.log.info("Namespace Level Restore job completed successfully")

    def go_to_cluster_detail(self, cluster_name):
        """Navigate to cluster detail page of given cluster

            Args:

                cluster_name        (str)       --  Name of the cluster

        """
        self._admin_console.navigator.navigate_to_kubernetes()
        self._admin_console.navigator.navigate_to_k8s_clusters()
        self.__clusters.open_cluster(cluster_name)
        self._admin_console.refresh_page()

    def go_to_appgroup_detail(self, cluster_name, appgroup_name):
        """Navigate to application group detail page of given application group

            Args:

                cluster_name        (str)       --  Name of the cluster

                appgroup_name       (str)       --  Name of the application group

        """
        self.go_to_cluster_detail(cluster_name)
        app_group_tab = self.__overview.access_application_groups()
        app_group_details = app_group_tab.open_application_group(appgroup_name)
        self._admin_console.refresh_page()
        return app_group_details

    def go_to_appgroup_tab_in_cluster(self, cluster_name):
        """Navigate to add app group tab wizard in cluster detail page"""
        self.go_to_cluster_detail(cluster_name)
        self.__clusters.access_application_group_tab()

    def navigate_to_etcd(self, cluster_name):
        """Navigate to system generated etcd application group

            Args:

                cluster_name        (str)       --  Name of the cluster

        """

        self.go_to_cluster_detail(cluster_name)
        self.__overview.access_configuration()
        self.__configuration.navigate_to_etcd()

    def enable_etcd_protection(self, cluster_name, plan):
        """Enable etcd protection for a cluster

            Args:

                cluster_name        (str)       --  Name of the cluster

                plan                (str)       --  Name of Plan to use

        """
        self.go_to_cluster_detail(cluster_name=cluster_name)
        self.__overview.access_configuration()
        self.__configuration.enable_etcd_protection(plan_name=plan)

    def change_access_node(self, cluster_name, access_node, old_access_node):
        """Change Access Node for a cluster

            Args:

                cluster_name        (str)       --  Name of the cluster

                access_node         (str)       --  Access Node to select

                old_access_node     (str)       --  Old Access Node to deselect

        """
        self.go_to_cluster_detail(cluster_name)
        self.__overview.access_configuration()
        self.__configuration.change_access_node(access_node, old_access_node)

    def change_access_node_on_app_grp(self, cluster_name, app_grp_name, access_node):
        """Change Access Node for a cluster

            Args:

                cluster_name        (str)       --  Name of the cluster

                access_node         (str)       --  Access Node to select

                app_grp_name        (str)       --   Name of the application group

        """
        self.go_to_appgroup_detail(cluster_name, app_grp_name)
        self.__app_group_details.change_access_node(access_node)

    def change_plan_on_k8s_app_grp(self, cluster_name, app_group_name, plan_name):
        """Change Plan for an application group

            Args:

                cluster_name        (str)       --  Name of the cluster

                app_group_name      (str)       --  Name of the application group

                plan_name           (str)       --  Name of the plan to select

        """
        self.go_to_appgroup_detail(cluster_name=cluster_name, appgroup_name=app_group_name)
        self.__app_group_details.change_plan(plan_name=plan_name)

    def enable_stateless_filter(self, cluster_name, app_group_name):
        """Enable stateless application filter for application group

            Args:

                cluster_name        (str)       --  Name of the cluster

                app_group_name       (str)       --  Name of the application group

        """

        self.__app_group_details = self.go_to_appgroup_detail(
            cluster_name=cluster_name,
            appgroup_name=app_group_name
        )
        self.__app_group_details.skip_stateless_apps()
        self._admin_console.submit_form()

    def validate_preview_content(self, cluster_name, app_group_name, validate_matrix):
        """Validate preview content for an application group

            Args:

                cluster_name        (str)       --  Name of the cluster

                app_group_name      (str)       --  Name of the application group

                validate_matrix             (list)      --  Content to validate

        """
        self.__app_group_details = self.go_to_appgroup_detail(
            cluster_name=cluster_name,
            appgroup_name=app_group_name
        )
        self.__app_group_details.validate_preview_content(validate_matrix=validate_matrix)
        self._admin_console.submit_form()

    def choose_new_kubernetes_configuration(self):
        """Choose New Configuration for Kubernetes from Metallic Hub"""
        if not self.__metallic:
            self._admin_console.log.info("Testcase is not for Metallic OEM. Skipping function execution")
            return
        self.__hub_dashboard.choose_service_from_dashboard()
        self.__hub_dashboard.click_new_configuration()

    def navigate_to_cc_from_hub(self):
        """Navigate to CC from Metallic Hub"""
        if not self.__metallic:
            self._admin_console.log.info("Testcase is not for Metallic OEM. Skipping function execution")
            return
        self.__hub_dashboard.choose_service_from_dashboard()
        self.__hub_dashboard.go_to_admin_console()

    def get_k8s_protected_data_sources(self):
        """Get Protected Data Sources count for Kubernetes Applications on Metallic Hub Dashboard"""
        self.__hub_dashboard.choose_service_from_dashboard()
        k8s_count = int(self.__hub_dashboard.get_protected_data_sources().get("K8s Applications", 0))
        return k8s_count

    def change_sa_and_sa_token(self, cluster_name, sa_name, token):
        """Change ServiceAccount and  ServiceAccountToken for a cluster

                    Args:

                        cluster_name        (str)       --  Name of the cluster

                        sa_name             (str)       --   Name of the Service Account

                        token               (str)       --  Service account Token

        """
        self.go_to_cluster_detail(cluster_name=cluster_name)
        self.__overview.change_sa_and_sa_token_(sa=sa_name, token=token)

    def change_image_url_and_image_secret(self, cluster_name, image_url, image_secret, destination=False):
        """Change Image URL and Image Pull Secret for a cluster

                    Args:

                        cluster_name        (str)       --  Name of the cluster

                        image_url           (str)       --   URL for Worker Pod image

                        image_secret        (str)       --  Image Pull Secret for the worker pod image

                        destination         (bool)      --  Checks if already in destination page

        """
        if not destination:
            self.go_to_cluster_detail(cluster_name=cluster_name)
            self.__overview.access_configuration()
        self.__configuration.change_image_url_and_image_secret_(image_url, image_secret)

    def change_config_namespace(self, cluster_name, config_ns, destination=False):
        """Change Configuration Namespace for a cluster

                    Args:

                        cluster_name        (str)       --  Name of the cluster

                        config_ns           (str)       --  Configuration Namespace

                        destination         (bool)      --  Checks if already in destination page

        """
        if not destination:
            self.go_to_cluster_detail(cluster_name=cluster_name)
            self.__overview.access_configuration()
        self.__configuration.change_config_namespace_(config_ns)

    def change_wait_timeout(self, cluster_name, worker_startup, resource_cleanup, snapshot_ready, snapshot_cleanup, destination=False):
        """Change Wait Timeout settings for a cluster

                    Args:

                        cluster_name        (str)       --  Name of the cluster

                        worker_startup      (str)       --  Timeout for Worker Pod startup

                        resource_cleanup    (str)       --  Timeout for Cluster Resource Cleanup

                        snapshot_ready      (str)       --  Timeout for Snapshot Ready

                        snapshot_cleanup    (str)       --  Timeout for Snapshot Cleanup

                        destination         (bool)      --  Checks if already in destination page
        """
        if not destination:
            self.go_to_cluster_detail(cluster_name=cluster_name)
            self.__overview.access_configuration()
        self.__configuration.change_wait_timeout_(worker_startup, resource_cleanup, snapshot_ready, snapshot_cleanup)

    def change_no_of_readers(self, cluster_name, appgroup_name, no_of_readers, destination=False):
        """Change Number of Readers for a Application Group

                    Args:

                        cluster_name        (str)       --  Name of the cluster

                        appgroup_name       (str)       --  Name of the application group

                        no_of_readers       (str)       --  Number of readers

                        destination         (bool)      --  Checks if already in destination page

        """
        if not destination:
            self.go_to_appgroup_detail(cluster_name=cluster_name, appgroup_name=appgroup_name)
        self.__app_group_details.change_no_of_readers_(no_of_readers=no_of_readers)

    def change_worker_pod_resource_settings(self, cluster_name, appgroup_name, cpu_request, cpu_limit, memory_request, memory_limit, destination=False):
        """Change Worker Pod Resource Settings for a Application Group

                    Args:

                        cluster_name        (str)        --  Name of the cluster

                        appgroup_name       (str)        --  Name of the application group

                        cpu_request         (str)        --  CPU Request

                        cpu_limit           (str)        --  CPU Limit

                        memory_request      (str)        --  Memory Request

                        memory_limit        (str)        --  Memory Limit

                        destination         (bool)       --  Checks if already in destination page

        """
        if destination:
            self.go_to_appgroup_detail(cluster_name=cluster_name, appgroup_name=appgroup_name)
        self.__app_group_details.change_worker_pod_resource_settings_(
            cpu_request=cpu_request,
            cpu_limit=cpu_limit,
            memory_request=memory_request,
            memory_limit=memory_limit
        )

    def enable_live_volume_fallback(self, cluster_name, appgroup_name, destination=False):
        """Enables Live Volume Fallback for a application group

                    Args:

                        cluster_name        (str)       --  Name of the cluster

                        appgroup_name       (str)       --  Name of the application group
        """
        if destination:
            self.go_to_appgroup_detail(cluster_name=cluster_name, appgroup_name=appgroup_name)
        self.__app_group_details.enable_live_volume_fallback_()





