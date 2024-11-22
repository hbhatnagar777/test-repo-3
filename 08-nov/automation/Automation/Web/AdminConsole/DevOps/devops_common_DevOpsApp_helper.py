import datetime
import json
import time

from Application.DevOps.devops_helper import DevOpsHelper
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.panel import RModalPanel
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.DevOps.details import Overview, RepositoryGroups, Configuration, Toolbar
from Web.AdminConsole.DevOps.instances import Instances
from Web.Common.exceptions import CVTestCaseInitFailure

"""
Helper file for performing Azure DevOps operations

Classes defined in this file:
    DevOpsAppHelper: All the utility functions you would need when dealing with a DevOps app.
        __init__: Initializes the DevOpsAppHelper object.
        create_azure_instance_from_instances: Creates an Azure DevOps instance.
        create_git_instance_from_instances: Creates a GitHub instance.

        access_or_create_instance_from_instances: Accesses or creates an instance from the instances page.
        edit_access_nodes_from_configuration: Edits instance access nodes.

        create_repository_group_from_repository_groups: Creates a repository group.
        delete_repository_group_from_repository_groups: Deletes a repository group.
        delete_repository_group_from_toolbar: Deletes a repository group from the toolbar.

        backup_from_repository_groups: Initiates backup from repository groups.
        restore_from_repository_groups: Initiates restoration from repository groups.
        restore_by_time: Initiates restoration within a specified time range.

        delete_app_from_instances: Deletes an app from instances.
        delete_app_from_servers: Deletes an app from servers.

        check_if_instance_exists_from_instances: Checks if an instance exists.
        check_if_repository_group_exists_from_repository_groups: Checks if a repository group exists.
        access_instance_from_instances: Accesses an instance from instances.

        cleanup_files: Cleans up temporary files.
        download_and_validate_services_data: Downloads and validates services data.
"""


class DevOpsAppHelper:
    """
    All the utility functions you would need when dealing with a devops app
    Most of the functions are defined with this syntax : <function_description>_from_<start_location>
        <function_description> : Describes what the function does
        <start_location>       : The page you would have to be at before you call the function
        Eg:
            create_azure_instance_from_instances
            Lets you create an azure instance (app) from the "instances" page.

    """

    def __init__(self, commcell, admin_console, tcinputs, log, is_azure=False, is_git=False):
        """
        Initializes a DevOpsAppHelper object.

        Args:
            commcell (object): The Commcell object.
            admin_console (object): The AdminConsole object.
            tcinputs (dict): Test case inputs.
            log (object): The log object.
            is_azure (bool, optional): Indicates if the instance is Azure DevOps. Defaults to False.
            is_git (bool, optional): Indicates if the instance is GitHub. Defaults to False.
        """
        self._admin_console = admin_console
        self.instances = Instances(admin_console)
        self.overview = Overview(admin_console)
        self.configuration = Configuration(admin_console)
        self.repository_groups = RepositoryGroups(admin_console)
        self.toolbar = Toolbar(admin_console)
        self.tcinputs = tcinputs
        nodes = self.tcinputs['access_nodes']
        self.access_nodes = json.loads(nodes) if isinstance(nodes, str) else nodes
        self.log = log
        self.devopshelper = None
        self.azhelper = None
        self.githelper = None
        self.app_name = None
        if is_azure:
            self.devopshelper = DevOpsHelper(commcell, tcinputs, 'azure')
            self.azhelper = self.devopshelper.azhelper
            self.app_name = tcinputs['azure_app_name']
        if is_git:
            self.devopshelper = DevOpsHelper(commcell, tcinputs, 'git')
            self.githelper = self.devopshelper.githelper
            self.app_name = tcinputs['git_app_name']
        self.az_data = None
        self.git_data = None
        self.is_azure = is_azure
        self.is_git = is_git

    def _select_projects(self, projects):
        """
        Selects projects in the AdminConsole.

        Args:
            projects (list): List of projects to be selected.
        """
        rmodal = RModalPanel(self._admin_console)
        for project in projects:
            rmodal.select_path_from_treeview(project)
        self._admin_console.click_button_using_id("Save")

    def create_azure_instance_from_instances(self):
        """Creates instance"""
        az_instance = self.instances.add_azuredevops_instance()
        az_instance.add_azure_details(self.tcinputs["azure_access_token"],
                                      self.tcinputs["azure_organization_name"],
                                      self.access_nodes,
                                      self.tcinputs["plan"],
                                      self.tcinputs.get("accessnodes_type"),
                                      app_name=self.app_name,
                                      token_name=self.tcinputs['token_name'],
                                      staging_path=self.tcinputs.get("staging_path"))

    def create_git_instance_from_instances(self):
        """
        Creates a GitHub instance from the instances page.

        This function adds details for the GitHub instance using the provided inputs.
        """

        git_instance = self.instances.add_github_instance()
        git_instance.add_git_details(self.tcinputs["git_access_token"],
                                     self.tcinputs["git_organization_name"],
                                     self.devopshelper.access_nodes,
                                     self.tcinputs["plan"],
                                     self.tcinputs.get("accessnodes_type"),
                                     token_name=self.tcinputs['token_name'],
                                     account_type=self.tcinputs.get("git_acctype"),
                                     app_name=self.app_name,
                                     host_url=self.tcinputs.get("git_host_url"),
                                     staging_path=self.tcinputs.get("staging_path"),
                                     impersonate_user=self.tcinputs.get("impersonate_user"))

    def access_or_create_instance_from_instances(self):
        """
        Accesses an existing instance or creates a new one from the instances page.

        If the instance does not exist, it creates a new one based on the provided inputs.
        """

        app_name = ''
        is_app_created = False
        if self.is_azure:
            app_name = self.tcinputs['azure_app_name']
        if self.is_git:
            app_name = self.tcinputs['git_app_name']
        if not self.instances.is_instance_exists(app_name):
            if self.tcinputs.get("plan"):
                if self.is_azure:
                    self.log.info("Creating azure devops instance")
                    self.create_azure_instance_from_instances()
                if self.is_git:
                    self.log.info("Creating github instance")
                    self.create_git_instance_from_instances()
                is_app_created = True
            else:
                raise CVTestCaseInitFailure(f"Instance: {app_name} doesn't exist."
                                            f" Plan is required for creating new instance")
        else:
            self.instances.access_instance(app_name)
        return is_app_created

    def edit_access_nodes_from_configuration(self, new_access_nodes):
        """Edits instance"""
        self.configuration.edit_access_nodes(access_nodes=new_access_nodes,
                                             accessnodes_type=self.tcinputs.get("accessnodes_type"))

    def create_repository_group_from_repository_groups(self, organization_name,
                                                       new_repository_group="automated_repo_group",
                                                       services=None, select=None):
        """
        Creates a new repository group in the repository groups page.

        Args:
            organization_name (str): The name of the organization associated with the repository group.
            new_repository_group (str, optional): The name of the new repository group. Defaults to automated_repo_group
            services (list, optional): List of services to associate with the repository group. Defaults to None.
            select (list, optional): List of items to select for the repository group. Defaults to None.
        """
        plan_name = self.tcinputs['plan']
        self.repository_groups.add_repository_group(plan_name, new_repository_group, organization_name,
                                                    services=services, select=select)

    def delete_repository_group_from_repository_groups(self, repository_group):
        """
        Deletes a repository group from the repository groups page.

        Args:
            repository_group (str): The name of the repository group to be deleted.
        """
        self.repository_groups.delete_repository_group(repository_group)

    def delete_repository_group_from_toolbar(self):
        """
        Deletes a repository group from the toolbar.
        """
        self.toolbar.delete_repository_group()

    def backup_from_repository_groups(self, repository_group='default', for_validation=False, backup_path='',
                                      services=None, select=None):
        """
        Performs a backup operation on the specified repository group.

        Args:
            repository_group (str): The name of the repository group to be backed up. Defaults to 'default'.
            for_validation (bool): If True, downloads the repositories in the repository group for future validation.
                                   Defaults to False.
            backup_path (str): Path relative to the remote path where the repositories will be downloaded for future validation.
                               Defaults to an empty string.
            services (list): List of services to associate with the repository group. Defaults to None.
            select (list): List of items to select for the repository group. Defaults to None.

        Returns:
            dict: A dictionary containing 'backup_job_id' and 'is_repo_group_created' keys.

        Raises:
            Exception: If no app type is chosen for the backup method, or if both Azure and GitHub app types are chosen.
        """

        is_repo_grp_created = False
        is_exists = self.repository_groups.is_repository_group_exists(repository_group)
        if repository_group is not None and not is_exists:
            self.log.info(f"Creating repository group: {repository_group}")
            self.create_repository_group_from_repository_groups(
                self.tcinputs['azure_organization_name'] if self.is_azure else self.tcinputs['git_organization_name'],
                repository_group, services, select=select)
            self.log.info("Successfully created repository group")
            is_repo_grp_created = True
            self._admin_console.wait_for_completion()
            self._admin_console.select_breadcrumb_link_using_text(self.app_name)
            self._admin_console.access_tab('Repository groups')
        self.log.info(f"Using repository group: {repository_group} for backup and restore")

        if not self.is_azure and not self.is_git:
            raise Exception("Please choose the app type in the backup method")
        if self.is_azure and self.is_git:
            raise Exception("Please choose one single app type for the helper")

        if for_validation:
            if self.is_azure:
                if select:
                    data = {}
                    for project in select:
                        data[project] = self.azhelper.get_repositories_for_project(project)
                    self.az_data = data
                else:
                    self.az_data = self.azhelper.get_projects_and_repositories()
                self.log.info("Successfully fetched projects and repositories: %s", self.az_data)
                self.azhelper.store_repos(self.az_data, backup_path=backup_path,
                                          bare=self.devopshelper.test_data.get('bare_validation', False))
            if self.is_git:
                if select:
                    self.git_data = select
                else:
                    self.git_data = self.githelper.get_repositories()
                self.log.info("Successfully fetched repositories: %s", self.git_data)
                self.githelper.store_repos(self.git_data, backup_path=backup_path,
                                           bare=self.devopshelper.test_data.get('bare_validation', False))

        backup_job_id = self.repository_groups.backup_now(repository_group)
        self.devopshelper.wait_for_job_completion(backup_job_id)
        return {'backup_job_id': backup_job_id, 'is_repo_group_created': is_repo_grp_created}

    def restore_from_repository_groups(self, repository_group='default', validate_data=True, backup_path=None,
                                       in_place=False, out_of_place=False, restore_to_disk=False, des_app=None,
                                       org_name=None, project_name=None, account_type=None, no_of_streams=10,
                                       services=None, des_app_type=None, app_helper=None, select_path=None,
                                       verify_jpr=None, des_server=None, des_path=None):
        """
        Restores repositories from the specified repository group.

        Args:
            repository_group (str): The name of the repository group to be restored. Defaults to 'default'.
            validate_data (bool): If True, downloads the restored repositories and validates with the data stored for validation during backup phase. Defaults to True.
            backup_path (str): Path to where all the repositories were stored during the backup phase.

            in_place (bool): If True, restores the repositories in place. Defaults to False.
            out_of_place (bool): If True, restores the repositories out of place. Defaults to False.
            restore_to_disk (bool): If True, restores the repositories to disk. Defaults to False.

            des_app (str): Destination application for out of place restore.
            org_name (str): Organization/group name/username/Account Name for out of place restore.
            project_name (str): Project name for out of place restore.
            account_type (str): Account type for out of place restore.
            no_of_streams (int): Number of streams for out of place restore.
            services (list): List of services to associate with the repository group for out of place restore.
            des_app_type (str): Destination application type for out of place restore.
            app_helper (obj): Helper object for cross-client restores.
            select_path (list): List of items to select for the repository group restore.
            verify_jpr (bool): If True, verifies the JPR file for the restore job.
            des_server (str): Destination server for restore to disk.
            des_path (str): Destination path for restore to disk.
        """

        self.repository_groups.open_restore_browse(repository_group)
        if select_path:
            restore = self.repository_groups.restore_all(select_path)
        else:
            restore = self.repository_groups.restore_all()

        if in_place:
            restore.restore_in_place(services=services)
        if out_of_place:
            if des_app is None:
                raise Exception("Out of place restore requires a destination app")
            if des_app_type not in ["azure", "github"]:
                raise Exception("Please provide the appropriate destination app type")
            if org_name is None:
                raise Exception("Out of place restore requires an organization/group name/username/Account Name")
            if des_app_type == 'azure' and project_name is None:
                project_name = 'automation_out_of_place_project_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            if des_app_type == 'github' and account_type is None:
                account_type = 'Business/Institution'

            restore.restore_out_of_place(des_app, org_name, project_name, account_type, no_of_streams, services)

        if restore_to_disk:
            if des_server is None:
                raise Exception("Please provide a destination server")
            if des_path is None:
                raise Exception("Plase provide a destination path")
            restore.restore_to_disk(des_server, des_path)

        restore_job_id = self._admin_console.get_jobid_from_popup()
        if verify_jpr:
            self.devopshelper.wait_for_job_completion(restore_job_id, verify_jpr=verify_jpr)
        else:
            self.devopshelper.wait_for_job_completion(restore_job_id)
        self.log.info("Done with restore")

        # Validation
        if validate_data:
            if self.is_azure and ((in_place) or (restore_to_disk) or (out_of_place and des_app_type == 'azure')):
                project_and_repos = self.az_data
                if out_of_place:
                    project_and_repos = {project_name: []}
                    for org_project_name, repos in self.az_data.items():
                        for repo in repos:
                            project_and_repos[project_name].append([repo, org_project_name])
                    self.azhelper.validate_out_of_place_restore_data(project_and_repos,
                                                                     bare_validation=self.devopshelper.test_data.get(
                                                                         'bare_validation', False))
                else:
                    # for in-place and restore-to-disk
                    self.azhelper.validate_test_data(project_and_repos,
                                                     backup_path=backup_path,
                                                     disk_path=des_path,
                                                     bare_validation=self.devopshelper.test_data.get('bare_validation', False))

            if self.is_git and ((in_place) or (out_of_place and des_app_type == 'github')):
                repos = self.git_data
                if out_of_place:
                    self.githelper.validate_test_data(repos,
                                                      backup_path=backup_path,
                                                      bare_validation=self.devopshelper.test_data.get(
                                                          'bare_validation', False),
                                                      organization=org_name)
                else:
                    # for in-place and restore-to-disk
                    self.githelper.validate_test_data(repos,
                                                      backup_path=backup_path,
                                                      disk_path=des_path,
                                                      bare_validation=self.devopshelper.test_data.get('bare_validation', False)
                                                      )

            # Cross-Client : Azure to GitHub
            if self.is_azure and out_of_place and des_app_type == 'github':
                project_and_repos = []
                for org_project_name, repos in self.az_data.items():
                    for repo in repos:
                        project_and_repos.append([repo, org_project_name])
                if app_helper is None:
                    raise Exception("Please provide the github helper to perform cross client restores")
                app_helper.validate_azure_to_github_repos(project_and_repos, backup_path=self.azhelper.remote_path,
                                                          bare_validation=self.devopshelper.test_data.get(
                                                              'bare_validation', False))

            # Cross-Client : GitHub to Azure
            if self.is_git and out_of_place and des_app_type == 'azure':
                repos = self.git_data
                project_and_repos = {project_name: repos}
                if app_helper is None:
                    raise Exception("Please provide the github helper to perform cross client restores")
                app_helper.validate_github_to_azure_repos(project_and_repos, backup_path=self.githelper.remote_path,
                                                          bare_validation=self.devopshelper.test_data.get(
                                                              'bare_validation', False))

    def restore_by_time(self, from_time, to_time, repository_group='default', validate=False, bkp_path=None, repos=None, projects_and_repos=None):
        """
        Restores repositories from the specified repository group within a specified time range.

        Args:
            from_time (str): The start time of the backup range in the format '%d-%B-%Y-%I-%M-%p'.
            to_time (str): The end time of the backup range in the format '%d-%B-%Y-%I-%M-%p'.
            repository_group (str): The name of the repository group to be restored. Defaults to 'default'.
            validate (bool): If True, validates the restored repositories against the backed up data. Defaults to False.
            bkp_path (str): Path to where all the repositories were stored during the backup phase.
            repos (list): List of repositories for validation in case of a Git instance.
            projects_and_repos (dict): Dictionary containing projects and repositories for validation in case of an Azure instance.
        """

        self.repository_groups.open_restore_browse(repository_group)
        rbrowse = RBrowse(self._admin_console)
        from_time = time.strftime('%d-%B-%Y-%I-%M-%p',
                                  time.localtime(time.mktime(
                                      time.strptime(from_time, '%d-%B-%Y-%I-%M-%p')) - 60))
        to_time = time.strftime('%d-%B-%Y-%I-%M-%p',
                                time.localtime(time.mktime(
                                    time.strptime(to_time, '%d-%B-%Y-%I-%M-%p')) + 60))
        self.log.info("Perform restore in backup range: " + from_time + " to " + to_time)
        rbrowse.show_backups_by_date_range(from_time=from_time, to_time=to_time, index=0)
        rest = self.repository_groups.restore_all()
        rest.restore_in_place()
        restore_job_id = self._admin_console.get_jobid_from_popup()
        self.devopshelper.wait_for_job_completion(restore_job_id)
        self.log.info("Done with restore in place")
        if validate:
            if self.is_git:
                self.githelper.validate_test_data(repos, bkp_path,
                                                  bare_validation=self.devopshelper.test_data.get('bare_validation', False))
            if self.is_azure:
                self.azhelper.validate_test_data(projects_and_repos, bkp_path,
                                                 bare_validation=self.devopshelper.test_data.get('bare_validation', False))

    def delete_app_from_instances(self):
        """
        Deletes the application from instances.
        """
        self.instances.delete_instance(self.app_name)

    def delete_app_from_servers(self):
        """
        Deletes the application from servers by clicking on the 'Retire' option.
        """
        self._admin_console.click_by_id("Type")
        self._admin_console.click_by_xpath("//div[@role='option']/li[@value='all' and @role='menuitem']")

        rtable = Rtable(self._admin_console)
        rtable.access_action_item(self.app_name, "Retire")
        self._admin_console.fill_form_by_id('confirmText', 'RETIRE')
        self._admin_console.click_by_id('Submit')

    def check_if_instance_exists_from_instances(self):
        """
        Checks if the instance exists in instances.
        """
        return self.instances.is_instance_exists(self.app_name)

    def check_if_repository_group_exists_from_repository_groups(self, repository_group):
        """
        Checks if the repository group exists.
        Args:
            repository_group (str): The name of the repository group to check for existence.
        """
        return self.repository_groups.is_repository_group_exists(repository_group)

    def access_instance_from_instances(self):
        """Access an instance from the instances page"""
        self.instances.access_instance(self.app_name)

    def cleanup_files(self, delete_temp_files=True, projects=None, repos=None, github_org_name=None):
        """
        Cleans up temporary files, deletes projects in Azure DevOps, and deletes repositories in GitHub if specified.

        Args:
            delete_temp_files (bool): If True, deletes temporary files associated with Azure DevOps and GitHub.
            projects (list): List of project names to delete from Azure DevOps.
            repos (list): List of repository names to delete from GitHub.
            github_org_name (str): GitHub organization name if deleting repositories.
        """
        if delete_temp_files:
            if self.azhelper:
                self.azhelper.client_machine.remove_directory(self.azhelper.remote_path)
                self.azhelper.controller_machine.remove_directory(self.azhelper.controller_path)
            if self.githelper:
                self.githelper.client_machine.remove_directory(self.githelper.remote_path)
                self.githelper.controller_machine.remove_directory(self.githelper.controller_path)
        if self.is_azure and projects is not None:
            for project in projects:
                self.azhelper.delete_project(project)
        if self.is_git and repos is not None:
            for repo in repos:
                self.githelper.delete_repository(repo, org_name=github_org_name)

    def download_and_validate_services_data(self, projects, services, in_place=False, out_of_place=False,
                                            project_map=None):
        """
        Downloads services data for specified projects from Azure DevOps and validates it.

        Args:
            projects (list): List of project names to download services data for.
            services (list): List of services to download data for.
            in_place (bool): If True, validates the downloaded services data in place.
            out_of_place (bool): If True, validates the downloaded services data out of place.
            project_map (dict): Dictionary mapping restored project names to source project names for out-of-place validation.
                Required when `out_of_place` is True.

        Raises:
            Exception: If `out_of_place` is True but `project_map` is not provided.
        """
        for project in projects:
            self.azhelper.download_services_data(project, False, services=services)
        if in_place:
            self.azhelper.validate_services_data({project: project for project in projects}, in_place=True)
        if out_of_place:
            if project_map is None:
                raise Exception(
                    "Please provide the project mappings dict with key={restored_project_name} value={source_project_name}")
            self.azhelper.validate_services_data(project_map)
