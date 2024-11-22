# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Helper file for performing Azure DevOps operations

Classes defined in this file
     AzureDevOpsHelper : Class which establishes connection with azure
                         devops organization and performs operations.

         __init__ : Initialising azure devops helper object

        __connect : Connect to git azure clients

        __select_access_node : Selecting an access node for generation/validation of data

        __initialize_working_env : Creating/initializing required folders/members

        _create_repository : Creation of repository with given details

        _import_repository : Importing Repository

        _delete_repository : Deletes Repository

        check_if_repository_exists : Checks existence of Repository

        check_if_project_exists  : Checks existence of Project

        _create_project : Creates project

        _delete_project : Deletes project

        _list_projects : Returns list of projects started with given prefix

        _list_repositories  :   Returns list of repositories in a given project

        _generate_data : Generates data for repositories.

        _upload_repository : Uploads generated data to Repository

        _download_repository : Downloads repository

        generate_test_data : Returns generated test data

        validate_test_data : Validates given test data

        download_services_data : Downloads services data for given project at path

        validate_services_data : Validates service data

        cleanup : Cleans up generated data and projects that start with given prefix
"""
import os.path
import pickle
import re
import subprocess
import time
import threading

from azure.devops.connection import Connection
from azure.devops.v6_0.cix import TeamProject
from azure.devops.v6_0.git.models import GitImportRequest, GitRepositoryCreateOptions
from azure.devops.v6_0.git.git_client_base import GitClientBase
from azure.devops.v6_0.work_item_tracking import Wiql
from azure.devops.exceptions import AzureDevOpsServiceError, AzureDevOpsClientRequestError
from msrest.authentication import BasicAuthentication

from AutomationUtils import logger, constants
from AutomationUtils.machine import Machine
from deepdiff import DeepDiff


class AzureDevOpsHelper:
    """
    Class which establishes connection with azure
    devops organization and performs operations.
    """

    def __init__(self, commcell, organization_name, access_token, access_nodes, git_bin=None):
        """
        Initialising azure devops helper object
        Args:
            commcell                    (obj)  -- Commcell object
            organization_name           (str)  -- organization name
            access_token                (str)  -- personal access token
            access_nodes                (list) -- list of access nodes
            git_bin                     (str)  -- bin path of git binaries
        Return:
            object - instance of this class
        """
        self.commcell = commcell
        self.git = git_bin
        self._log = logger.get_log()
        self.organization_url = None
        self.credentials = None
        self.git_client = None
        self.core_client = None
        self.connection = None
        self.__connect(organization_name, access_token)
        self.client_machine = None
        self.controller_machine = None
        self.controller_path = None
        self.remote_path = None
        self.backup_path = None
        self.restore_path = None
        self._status_script = None
        self._pull_script = None
        self._push_script = None
        self._index_to_repository_script = None
        self.__initialize_working_env(access_nodes)

    def __connect(self, organization_name, access_token):
        """
        Connect to git azure clients
        Args:
            organization_name           (str)  -- organization name
            access_token                (str)  -- personal access token
        Raises:
            Exception:
                If connection is not successful
        """
        try:
            self._log.info("Connecting to azure git clients")
            self.organization_url = f'https://dev.azure.com/{organization_name}'
            self.credentials = BasicAuthentication('', access_token)
            self.git_client = GitClientBase(base_url=self.organization_url, creds=self.credentials)
            self.connection = Connection(base_url=self.organization_url, creds=self.credentials)
            self.core_client = self.connection.clients.get_core_client()
            self._log.info("Successfully connected")
        except AzureDevOpsClientRequestError as err:
            self._log.info("Connection failed.")
            self._log.info("Please check organization: %s and token:"
                           " %s provided", organization_name, access_token)
            raise Exception('Exception: {0}'.format(str(err)))
        except Exception as err:
            raise Exception("Unable to connect: {0}".format(str(err)))

    def __select_access_node(self, access_nodes):
        """
        Selecting an access node for generation/validation of data
        Args:
            access_nodes          (list) -- list of access nodes
        Returns:
            client                (obj)  -- selected client
        Raises:
            Exception:
                If failed to select an access node.
        """
        self._log.info("Selecting access node for generating and validating test data")
        for access_node in access_nodes:
            client = self.commcell.clients.get(access_node)
            if self.git is None:
                if "unix" in client.os_info.lower():
                    self.git = "/usr/bin"
                    self._status_script = constants.UNIX_GIT_STATUS
                    self._pull_script = constants.UNIX_GIT_PULL
                    self._push_script = constants.UNIX_GIT_PUSH
                    self._index_to_repository_script = constants.UNIX_GIT_RESTORE_FROM_INDEX
                else:
                    self.git = "C:\\Program Files\\Git\\bin"
                    self._status_script = constants.WINDOWS_GIT_STATUS
                    self._pull_script = constants.WINDOWS_GIT_PULL
                    self._push_script = constants.WINDOWS_GIT_PUSH
                    self._index_to_repository_script = constants.WINDOWS_GIT_RESTORE_FROM_INDEX
            data = {'GITBIN': self.git}
            error_list = ["is not recognized", "is not a git command", "No such file or directory"]
            if client.is_ready:
                client_machine = Machine(client.name, self.commcell)
                output = client_machine.execute_script(self._status_script, data)
                if output.exit_code != 0:
                    raise Exception("Git status script execution failed with: %s", output.exception)
                self._log.debug("Output of git status script: %s", output.formatted_output)
                error = output.exception
                if any(error_string in error for error_string in error_list):
                    self._log.info("Skipping this client: %s since "
                                   "git or git lfs is not available", client.name)
                else:
                    self._log.info("Successful selected the client: %s", client.name)
                    self.client_machine = client_machine
                    return client
        self._log.info("Failed to select the node.")
        self._log.info("Access nodes are not ready or wrong git bin path is provided.")
        raise Exception("Access nodes are not ready or wrong git bin path is provided.")

    def __initialize_working_env(self, access_nodes):
        """
        Creating/initializing required folders/members
        Args:
            access_nodes        (list) -- list of access nodes
        """
        self.controller_machine = Machine()
        client = self.__select_access_node(access_nodes)
        self.remote_path = self.client_machine.join_path(client.install_directory, "Temp")
        self.remote_path = self.client_machine.join_path(self.remote_path,
                                                         f"AzureDevOpsTemp_{threading.get_ident()}")
        self.backup_path = self.client_machine.join_path(self.remote_path, "Backup")
        self.restore_path = self.client_machine.join_path(self.remote_path, "Restore")
        self.controller_path = self.controller_machine.join_path(self.controller_machine.tmp_dir,
                                                                 f"AzureDevOpsTemp_{threading.get_ident()}"
                                                                 f"_{int(time.time())}")
        self.client_machine.create_directory(self.remote_path, force_create=True)
        self.client_machine.create_directory(self.backup_path, force_create=True)
        self.client_machine.create_directory(self.restore_path, force_create=True)
        self.controller_machine.create_directory(self.controller_path, force_create=True)

    def _create_repository(self, repo_name, project_name):
        """
        Creation of repository with given details
        Args:
            repo_name           (str) -- name of the repository
            project_name        (str) -- name of the project
        Raises:
            Exception:
                If failed to create repository.
        """
        try:
            self._log.info("Creating repository: %s in "
                           "project: %s", repo_name, project_name)
            self.git_client.create_repository(GitRepositoryCreateOptions
                                              (name=repo_name), project_name)
            self._log.info("Successfully created repository")
        except AzureDevOpsServiceError as err:
            self._log.info("Repository creation failed.")
            raise Exception('Exception: {0}'.format(str(err)))
        except Exception as err:
            raise Exception("Unable to create repository: {0}".format(str(err)))

    def _import_repository(self, git_url, repo_name, project_name):
        """
        Importing Repository
        Args:
            git_url             (str) -- url of git repository
                                         that needs to be imported
            repo_name           (str) -- name of the repository
            project_name        (str) -- name of the project
        Raises:
            Exception:
                If failed to import repository.
        """
        try:
            self._log.info("Importing repository: %s to repository: "
                           "%s in project: %s", git_url, repo_name, project_name)
            self.git_client.create_import_request(GitImportRequest(parameters={
                "gitSource": {
                    "url": git_url
                }}), project_name, repo_name)
            time.sleep(30)
            self._log.info("Successfully imported repository")
        except AzureDevOpsServiceError as err:
            self._log.info('Exception: {0}'.format(str(err)))
            raise Exception('Exception: {0}'.format(str(err)))
        except AzureDevOpsClientRequestError as err:
            self._log.info("Check git url provided")
            raise Exception('Exception: {0}'.format(str(err)))

    def _delete_repository(self, repo_name, project_name):
        """
        Deletes Repository
        Args:
            repo_name           (str) -- name of the repository
            project_name        (str) -- name of the project
        Raises:
            Exception:
                If failed to delete repository.
        """
        try:
            self._log.info("Deleting repository: %s in project: %s", repo_name, project_name)
            repo = self.git_client.get_repository(repo_name, project_name)
            self.git_client.delete_repository(repo.id)
            time.sleep(5)
            self._log.info("Successfully deleted repository")
        except AzureDevOpsServiceError as err:
            self._log.info('Exception: {0}'.format(str(err)))
            raise Exception('Exception: {0}'.format(str(err)))
        except AzureDevOpsClientRequestError as err:
            self._log.info('Exception: {0}'.format(str(err)))
            raise Exception('Exception: {0}'.format(str(err)))

    def check_if_repository_exists(self, repo_name, project_name):
        """
        Checks existence of Repository
        Args:
            repo_name           (str) -- name of the repository
            project_name        (str) -- name of the project
        Raises:
            Exception:
                If failed to check existence of repository.
        """
        try:
            self.git_client.get_repository(repo_name, project_name)
            return True
        except AzureDevOpsServiceError as err:
            raise Exception('Exception: {0}'.format(str(err)))
        except Exception as err:
            raise Exception("Unable to check the repository existence"
                            ": {0}".format(str(err)))

    def check_if_project_exists(self, project_name):
        """
        Checks existence of Project
        Args:
            project_name        (str) -- name of the project
        Raises:
            Exception:
                If failed to check existence of project.
        """
        try:
            self.core_client.get_project(project_name)
            return True
        except AzureDevOpsServiceError as err:
            raise Exception('Exception: {0}'.format(str(err)))
        except Exception as err:
            raise Exception("Unable to check the project existence"
                            ": {0}".format(str(err)))

    def _create_project(self, project_name):
        """
        Creates project
        Args:
            project_name        (str) -- name of the project
        Raises:
            Exception:
                If failed to create project.
        """
        try:
            self._log.info("Creating project: %s", project_name)
            self.core_client.queue_create_project(TeamProject(
                name=project_name, description='',
                capabilities={"versioncontrol": {"sourceControlType": "Git"},
                              "processTemplate": {
                                  "templateTypeId": "6b724908-ef14-45cf-84f8-768b5384da45"
                              }},
                visibility='private'))
            time.sleep(30)
            self._log.info("Successfully created project")
        except AzureDevOpsServiceError as err:
            raise Exception('Exception: {0}'.format(str(err)))
        except Exception as err:
            raise Exception("Unable to create the project"
                            ": {0}".format(str(err)))

    def _delete_project(self, project_name):
        """
        Deletes project
        Args:
            project_name        (str) -- name of the project
        Raises:
            Exception:
                If failed to delete project.
        """
        try:
            self._log.info("Deleting project: %s", project_name)
            self.core_client.queue_delete_project(self.core_client.get_project(project_name).id)
            time.sleep(5)
            self._log.info("Successfully deleted project")
        except AzureDevOpsServiceError as err:
            raise Exception('Exception: {0}'.format(str(err)))
        except Exception as err:
            raise Exception("Unable to delete the project"
                            ": {0}".format(str(err)))

    def _list_projects(self, prefix=""):
        """
        Returns list of projects started with given prefix
        Args:
            prefix           (str) -- prefix value
                default - ""   (Returns all projects)
        Returns:
            prj_list        (list) -- list of projects
        """
        get_projects_response = self.core_client.get_projects()
        prj_list = []
        while get_projects_response is not None:
            for project in get_projects_response.value:
                if project.name.startswith(prefix):
                    prj_list.append(project.name)
            if get_projects_response.continuation_token is not None \
                    and get_projects_response.continuation_token != "":
                # Get the next page of projects
                get_projects_response = self.core_client.get_projects(
                    continuation_token=get_projects_response.continuation_token)
            else:
                # All projects have been retrieved
                get_projects_response = None
        return prj_list

    def _list_repositories(self, project):
        """
        List repositories for given project
        Args:
            project         (str)   --  project name
        Returns:
            repo_list       (list)  --  list of repositories in project
        """
        repo_list = []
        for item in self.git_client.get_repositories(project):
            repo_list.append(item.name)
        return repo_list

    def _generate_data(self, repo_data=None):
        """
        Generates data for repositories.
        Args:
            repo_data       (list) -- data to be generated for each repository
                default - [1,2,24] (eg. [No. of folders, files in each folder, size(mb) of file])
                    To verify git lfs functionality use size>110mb
        """
        self.client_machine.remove_directory(self.backup_path)
        self._log.info(f"Generating test data in local machine: {self.client_machine.machine_name}")
        self._log.info(f"Test data path in {self.client_machine.machine_name}: {self.backup_path}")
        git_backup = self.client_machine.join_path(self.backup_path, "git_backup")
        if repo_data is None:
            repo_data = [1, 2, 24]
        self._log.info(f"Data to be generated is {repo_data[0]} folder(s) each containing "
                       f"{repo_data[1]} file(s) of size {repo_data[2]}mb")
        self.client_machine.generate_test_data(git_backup, repo_data[0], repo_data[1],
                                               repo_data[2] * 1024, hlinks=False, slinks=False,
                                               hslinks=False, sparse=False, zero_size_file=False)
        self._log.info("Successfully generated test data in local machine")

    def _upload_repository(self, repo_name, project_name):
        """
        Uploads generated data to Repository
        Args:
            repo_name           (str) -- name of the repository
            project_name        (str) -- name of the project
        """
        self._log.info("Uploading generated data to repository: "
                       "%s in project: %s", repo_name, project_name)
        url = f"https://automation:{self.credentials.password}@" \
              f"{self.organization_url.split('//')[-1]}/{project_name}/_git/{repo_name}"
        data = {
            'GITBIN': self.git,
            'PUSHPATH': self.backup_path,
            'URL': url
        }
        output = self.client_machine.execute_script(self._push_script, data)
        if output.exit_code != 0:
            raise Exception("Git push script execution failed with: %s", output.exception)
        self._log.debug("Output of git push script: %s", output.formatted_output)
        self._log.info("Successfully uploaded data")

    def _download_repository(self, repo_name, project_name, download_folder=None, bare=True):
        """
        Downloads repository
        Args:
            repo_name           (str)  -- name of the repository
            project_name        (str)  -- name of the project
            download_folder     (str) -- determines where repository should be downloaded
                    default - None    (Downloads to Restore folder in remote path)
            bare     (bool) -- Determines whether to clone repository with bare or not
                default - True  (clones repository with bare option enabled)
        """
        if download_folder is None:
            dest = "Restore"
            self.client_machine.remove_directory(self.restore_path)
            self._log.info(f"Downloading restored data from repository: {repo_name} in "
                           f"project: {project_name} for validation")
        else:
            dest = download_folder if "automation" not in repo_name else f"{download_folder}_{repo_name}"
            path = self.client_machine.join_path(self.remote_path, dest)
            self.client_machine.remove_directory(path)
            self._log.info(f"Downloading backed up repository to {path} for validation")
        url = f"https://automation:{self.credentials.password}@" \
              f"{self.organization_url.split('//')[-1]}/{project_name}/_git/{repo_name}"
        bare = "--bare" if bare else ""
        data = {
            'GITBIN': self.git,
            'PULLPATH': self.remote_path,
            'URL': url,
            'DEST': dest,
            'BARE': bare
        }
        output = self.client_machine.execute_script(self._pull_script, data)
        if output.exit_code != 0:
            raise Exception("Git pull script execution failed with: %s", output.exception)
        self._log.debug("Output of git pull script: %s", output.formatted_output)
        self._log.info("Successfully downloaded data")

    def generate_test_data(self, prefix=None, no_of_projects=None, no_of_repos=None, repo_data=None,
                           download_folder=None, git_url=None, bare_validation=True, cleanup=True):
        """
        Returns generated test data
        Args:
            prefix               (str) -- prefix for the created projects/repositories
            no_of_repos           (int) -- number of repositories
            no_of_projects        (int) -- number of projects
            repo_data           (list) -- data to be generated for each repository
                default - [1,2,24] (eg. [No. of folders, files in each folder, size(mb) of file])
                    To verify git lfs functionality use size>110mb
            download_folder      (str) -- Destination folder where data to be downloaded
                default - None (downloads to Backup folder in remote path)
            git_url              (str) -- url of repository
                default - None (imports data from repository instead of uploading generated data)
            bare_validation      (bool) -- Determines whether to clone repository with bare or not
                default - True  (validates by cloning with bare option enabled)
            cleanup              (bool) -- Deletes projects starting with given prefix
                default - True  (Deletes projects starting with automation_)
        Returns:
            test_data           (dict) -- created projects(keys) and repositories(values)
        """
        prefix = prefix or "automation_"
        if cleanup:
            self.cleanup(prefix, del_only_prj=True)
        prefix += f"{int(time.time())}_"
        if no_of_projects is None:
            no_of_projects = 2
        if no_of_repos is None:
            no_of_repos = 2
        repo_data = repo_data or [1, 2, 24]
        download_folder = download_folder or 'Backup'
        if bare_validation is None:
            bare_validation = True
        test_data = {}
        repo_name, project_name = None, None

        if git_url is None:
            if repo_data[0] != 0 or (no_of_projects != 0 and no_of_repos != 0):
                self._generate_data(repo_data)
        self._log.info(f"{no_of_projects} project(s) are created with each containing "
                       f"{no_of_repos} repositories")
        for project in range(no_of_projects):
            project_name = f"{prefix}project_{str(project)}"
            self._create_project(project_name)
            test_data[project_name] = []
            for repo in range(no_of_repos):
                repo_name = f"{project_name}_repo_{str(repo)}"
                self._create_repository(repo_name, project_name)
                if git_url is not None:
                    self._import_repository(git_url, repo_name, project_name)
                elif repo_data[0] != 0:
                    self._upload_repository(repo_name, project_name)
                test_data[project_name].append(repo_name)
                self._download_repository(repo_name, project_name, download_folder, bare_validation)
            if no_of_repos != 0:
                self._delete_repository(project_name, project_name)
        self._log.info("Successfully generated data")
        return test_data

    def validate_test_data(self, test_data, backup_path=None, disk_path=None, bare_validation=True):
        """
        Validates given test data
        Args:
            test_data       (dict) -- projects(keys) and repositories(values)
            backup_path     (str)  -- restore files that needs to be validated against
            disk_path       (str)  -- where restore files are located (only restore to disk case)
            bare_validation      (bool) -- Determines whether to clone repository with bare or not
                default - True  (validates by cloning with bare option enabled)
        Raises:
            Exception:
                If validation is failed
        """
        organization = self.organization_url.split('//')[-1].split('/')[-1]
        if bare_validation is None:
            bare_validation = True
        if backup_path is not None:
            self.backup_path = backup_path
        else:
            backup_path = self.remote_path
        for project in test_data:
            if disk_path or self.check_if_project_exists(project):
                for repo in test_data[project]:
                    if disk_path or self.check_if_repository_exists(repo, project):
                        current_backup_path = self.client_machine.join_path(backup_path, f"{project}_{repo}")
                        if disk_path is None:
                            self._download_repository(repo, project, bare=bare_validation)
                        else:
                            # restored to disk
                            repo_path = self.client_machine.join_path(disk_path, organization, project, repo)
                            bare = "--bare" if bare_validation else ""
                            data = {
                                'GITBIN': self.git,
                                'SRCPATH': f'{repo_path}.git',
                                'RESTOREPATH': self.client_machine.join_path(disk_path, organization, project),
                                'DEST_REPO': repo,
                                'BARE': bare
                            }
                            output = self.client_machine.execute_script(self._index_to_repository_script, data)
                            if output.exit_code != 0:
                                raise Exception("Git Index to Restore script execution failed with: %s",
                                                output.exception)
                            self._log.debug("Output of Git Index to Restore script: %s", output.formatted_output)
                            self._log.info("Successfully restored data")
                            self.restore_path = self.client_machine.join_path(
                                disk_path, organization, project, repo)
                        self._log.info(f'current backup path : {current_backup_path}')
                        self._log.info(f'restore path : {self.restore_path}')
                        time.sleep(10)
                        compare_output = self.client_machine.compare_folders(
                            self.client_machine, current_backup_path, self.restore_path,
                            ignore_files=[".gitattributes", "config", "packed-refs"], ignore_folder=[".git", "hooks"])
                        if sorted(compare_output) in (
                                ['config', 'hooks\\fsmonitor-watchman.sample'],
                                ['config', 'hooks\\push-to-checkout.sample'],
                                ['config'], []):
                            self._log.info("Successfully validated repository: "
                                           "%s in project: %s", repo, project)
                        else:
                            self._log.info("Validation Failed: %s in %s doesn't "
                                           "match source files", repo, project)
                            self._log.info("Folder comparision output: %s", compare_output)
                            self._log.info(f"Backup Path:{current_backup_path}, "
                                           f"Restore Path: {self.restore_path}")
                            raise Exception("Validation Failed: {0} in {1} doesn't "
                                            "match source files".format(repo, project))
                    else:
                        self.client_machine.remove_directory(self.remote_path)
                        raise Exception("Validation Failed: {0} in {1} "
                                        "doesn't exist".format(repo, project))

    def _get_all_queries(self, project, queries, wit_client=None):
        """Fetches all queries present in project"""
        if wit_client is None:
            wit_client = self.connection.clients_v6_0.get_work_item_tracking_client()
        qlist = {}
        if queries is None:
            return qlist
        for query in queries:
            if query.wiql is not None:
                qlist.update({query.path: query.wiql})
            elif query.has_children is not None and query.children is None:
                sub_query = wit_client.get_query(project=project, query=query.id, expand="all", depth=2)
                qlist.update(self._get_all_queries(project, sub_query.children))
            else:
                qlist.update(self._get_all_queries(project, query.children))
        return qlist

    def _dump_dict_as_pickle(self, project, data_type, dump_dict, path):
        """Dumps the service info dictionary as a pickle file"""
        created_map = {'environments': 'created_on', 'releases': 'created_on', 'variablegroups': 'created_on', }
        if data_type not in ['workitems', 'queries', 'deploymentgroups', 'testplans', 'feeds']:
            tmp, reformat_dict = {}, {}
            for i in dump_dict:
                created_info = dump_dict[i].get(created_map.get(data_type, 'created_date'))
                tmp[f"{dump_dict[i].get('name')}{created_info.split('T')[-1].rstrip('Z')}"] = dump_dict[i]
            if reformat_dict == {}:
                j = 0
                for i in sorted(tmp):
                    reformat_dict.update({j: tmp[i]})
                    j += 1
        else:
            reformat_dict = dump_dict
        tmp_path = self.controller_machine.join_path(self.controller_path, path, project)
        if not self.controller_machine.check_directory_exists(tmp_path):
            self.controller_machine.create_directory(tmp_path)
        pickle_path = self.controller_machine.join_path(tmp_path, f"{data_type}.pickle")
        with open(pickle_path, 'wb') as handle:
            pickle.dump(reformat_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def _download_boards_data(self, project_name, path):
        """Downloads boards data"""
        # work items
        wit_client = self.connection.clients_v6_0.get_work_item_tracking_client()
        query = f"""SELECT * FROM workitem WHERE [System.TeamProject] = '{project_name}' ORDER BY [System.Title] DESC"""
        wiql = Wiql(query=query)
        all_workitems = {}
        workitems = wit_client.query_by_wiql(wiql).work_items
        for item in range(len(workitems)):
            all_workitems[item] = wit_client.get_work_item(id=workitems[item].id).as_dict()
        self._dump_dict_as_pickle(project_name, "workitems", all_workitems, path)

        # queries
        queries = wit_client.get_queries(project=project_name, expand="all", depth=2)
        all_queries = self._get_all_queries(project=project_name, queries=queries)
        self._dump_dict_as_pickle(project_name, "queries", all_queries, path)

        # Delivery Plans
        work_client = self.connection.clients_v6_0.get_work_client()
        all_deliveryplans = {}
        delivery_plans = work_client.get_plans(project=project_name)
        for dp in range(len(delivery_plans)):
            value = work_client.get_plan(project_name, delivery_plans[dp].id).as_dict()
            key = value.get('name')
            all_deliveryplans[key] = value
        self._dump_dict_as_pickle(project_name, "deliveryplans", all_deliveryplans, path)

    def _download_pipelines_data(self, project_name, path):
        """Downloads pipelines data"""
        # Environments
        tac = self.connection.clients_v6_0.get_task_agent_client()
        all_environments = {}
        environments = tac.get_environments(project=project_name)
        for env in range(len(environments)):
            all_environments[env] = tac.get_environment_by_id(project_name, environments[env].id).as_dict()
        self._dump_dict_as_pickle(project_name, "environments", all_environments, path)

        # Releases
        rc = self.connection.clients_v6_0.get_release_client()
        all_releases = {}
        releases = rc.get_release_definitions(project=project_name)
        for release in range(len(releases)):
            all_releases[release] = rc.get_release_definition(project_name, releases[release].id).as_dict()
        self._dump_dict_as_pickle(project_name, "releases", all_releases, path)

        # variable groups
        all_variablegroups = {}
        variablegroups = tac.get_variable_groups(project=project_name)
        for variablegroup in range(len(variablegroups)):
            all_variablegroups[variablegroup] = tac.get_variable_group(project_name,
                                                                       variablegroups[variablegroup].id).as_dict()
        self._dump_dict_as_pickle(project_name, "variablegroups", all_variablegroups, path)

        # deployment groups
        all_deploymentgroups = {}
        deploymentgroups = tac.get_deployment_groups(project=project_name)
        for deploymentgroup in range(len(deploymentgroups)):
            all_deploymentgroups[deploymentgroup] = tac.get_deployment_group(project_name, deploymentgroups[
                deploymentgroup].id).as_dict()
        self._dump_dict_as_pickle(project_name, "deploymentgroups", all_deploymentgroups, path)

    def _download_testplans_data(self, project_name, path):
        """Downloads testplans data"""
        # testplans
        tpc = self.connection.clients_v6_0.get_test_plan_client()
        all_testplans = {}
        testplans = tpc.get_test_plans(project=project_name)
        for testplan in range(len(testplans)):
            all_testplans[testplan] = tpc.get_test_plan_by_id(project_name, testplans[testplan].id).as_dict()
        self._dump_dict_as_pickle(project_name, "testplans", all_testplans, path)

    def _download_artifacts_data(self, project_name, path):
        """Downloads artifacts data"""
        # feeds
        fc = self.connection.clients_v6_0.get_feed_client()
        all_feeds = {}
        feeds = fc.get_feeds(project=project_name)
        # feeds.extend(fc.get_feeds_from_recycle_bin(project=project_name))
        for feed in range(len(feeds)):
            all_feeds[feed] = fc.get_feed(feeds[feed].id, project_name).as_dict()
        self._dump_dict_as_pickle(project_name, "feeds", all_feeds, path)

    def download_services_data(self, project_name, backup=True, services=None):
        """
        Downloads services data for given project at path
        Args:
            project_name    (str)   --  Name of the project
            backup          (bool)  --  decides the path of download for validation
                default - at backup location in controller
            services        (list)  --  services data to be downloaded
                default - all services
        Returns:
            dict of projects and it's repositories in case repos service is selected
        """
        if services is None:
            services = ['Boards', 'Pipelines', 'Repos', 'Test Plans', 'Artifacts']
        repo_list = "Repos" in services
        if repo_list:
            services.remove("Repos")
        if backup and repo_list:
            repo_list = self._list_repositories(project_name)
            for repo in repo_list:
                self._download_repository(repo, project_name, f'{project_name}_{repo}')
        path = "Backup" if backup else "Restore"
        for service in services:
            getattr(self, "_download_" + service.replace(" ", "").lower() + "_data")(project_name, path)
        if repo_list and backup:
            return {project_name: repo_list}

    def validate_services_data(self, project_map, in_place=False):
        """
        Validates service data
        Args:
            project_map        (dict)    -- contains restore project as key and source project as value
            in_place           (bool)    -- in case of inplace restore duplicate data will be restored for some services
        Raises:
            Exception:
                If validation failed for any of the project/service
        """
        comp_validator = {'workitems': 'Title'}
        validation_failed = {}
        for project in project_map:
            backup_path = self.controller_machine.join_path(self.controller_path, "Backup", project_map[project])
            restore_path = self.controller_machine.join_path(self.controller_path, "Restore", project)
            self._log.info(f"Backup path being compared : {backup_path}")
            self._log.info(f"Restore path being compared : {restore_path}")
            files = self.controller_machine.get_files_in_path(restore_path)
            for pickle_file in files:
                serv_comp = pickle_file.rsplit("\\", 1)[-1].rstrip('.pickle')
                with open(self.controller_machine.join_path(backup_path, f"{serv_comp}.pickle"), 'rb') as f:
                    bkp_data = pickle.load(f)
                with open(self.controller_machine.join_path(restore_path, f"{serv_comp}.pickle"), 'rb') as f:
                    rstr_data = pickle.load(f)

                if len(bkp_data) != len(rstr_data):
                    if in_place and serv_comp in ["testplans"] and len(rstr_data) == 2 * len(bkp_data):
                        self._log.info(f"length mismatch as inplace restore done, causing duplicate entries")
                    else:
                        if project_map[project] not in validation_failed:
                            validation_failed[project_map[project]] = set()
                        validation_failed[project_map[project]].add(serv_comp)
                        self._log.exception(f"length of backup and restore data doesn't match for {serv_comp}")
                else:
                    self._log.info(f"length of backup and restore data matched for {serv_comp}")

                diff = DeepDiff(bkp_data, rstr_data)
                if 'values_changed' not in diff:
                    self._log.info(f"no values changed in diff: {diff} for {serv_comp}")
                    continue
                if serv_comp == "queries":
                    res = all(bkp_data.get(key) == rstr_data.get(key) for key in bkp_data)
                    if not res and 'values_changed' not in diff:
                        if project_map[project] not in validation_failed:
                            validation_failed[project_map[project]] = set()
                        validation_failed[project_map[project]].add(serv_comp)
                        self._log.exception(f"{serv_comp} don't match, please check diff:{diff['values_changed']}")
                else:
                    comp_val = comp_validator.get(serv_comp, 'name')
                    for i in diff['values_changed']:
                        if re.findall(f"\\[\\d]\\['{comp_val}']", i):
                            if project_map[project] not in validation_failed:
                                validation_failed[project_map[project]] = set()
                            validation_failed[project_map[project]].add(serv_comp)
                            self._log.exception(
                                f"{serv_comp} have {comp_val} mismatch, please check diff:{diff['values_changed']}")
        if validation_failed:
            raise Exception(f"validation failed for services: {validation_failed}")

    def cleanup(self, prefix=None, del_only_prj=False):
        """
        Cleans up generated data and projects that start with given prefix
        Args:
            prefix          (str)  -- prefix of the projects that needs to be deleted
            del_only_prj    (bool) -- doesn't delete the created temp directory if true
        """
        if prefix != "":
            prefix = prefix or "automation_"
        if not del_only_prj:
            self._log.info("Cleaning up data")
            self.client_machine.remove_directory(self.remote_path)
            self._log.info("Cleaned up data")
        self._log.info("Deleting projects that start with prefix: %s", prefix)
        project_list = self._list_projects(prefix)
        for project in project_list:
            self._delete_project(project)
        self._log.info("Successfully deleted projects that started with prefix: %s", prefix)

    def get_projects_and_repositories(self):
        """
            Returns a dictionary of items for an organization where
                key : project_name
                value : list of repositories in the project
            Example:
                {
                    project1 : [project1_repo1, project1_repo2],
                    project2 : [project2_repo1]
                }
        """
        data = {}

        projects = self._list_projects()
        for project in projects:
            data[project] = self._list_repositories(project)

        return data

    def store_repos(self, data, backup_path='', bare=True):
        """
           Stores repositories data at a specified backup path relative to self.remote_path.

           Args:
               data (Dict[str, List[str]]):
                   Dictionary containing project names as keys and lists of repository names as values.
               backup_path (str): Relative path for storing the backup.
                   Defaults to an empty string, indicating storage at self.remote_path.
               bare (bool): Determines whether repositories should be stored as bare repositories.
                   Defaults to True, indicating bare repositories.

        """
        for project in data:
            for repo in data[project]:
                if self.check_if_project_exists(project) and self.check_if_repository_exists(repo, project):
                    current_backup_path = ''
                    if backup_path == '':
                        current_backup_path = f'{project}_{repo}'
                    else:
                        current_backup_path = self.client_machine.join_path(backup_path, f'{project}_{repo}')
                    self._log.info(f"Downloading {repo} from {project} in {current_backup_path} for validation")
                    self._download_repository(repo, project, current_backup_path, bare)

    def create_project(self, project_name):
        """
        Creates a new project with the specified name.

        Args:
            project_name (str): Name of the project to be created.
        """
        self._create_project(project_name)

    def delete_project(self, project_name):
        """
        Deletes the project with the specified name.

        Args:
            project_name (str): Name of the project to be deleted.
        """
        self._delete_project(project_name)

    def _import_repository_after_clone(self, access_token, remote_repo_url, repo_name, project_name):
        """
            Imports a repository after cloning it from a remote URL.

            Args:
                access_token (str): Access token for authentication.
                remote_repo_url (str): URL of the remote repository to be cloned.
                repo_name (str): Name of the repository.
                project_name (str): Name of the project.
        """
        remote_repo_name = os.path.splitext(os.path.basename(remote_repo_url))[0]
        clone_directory = self.controller_path
        cloned_repo_path = os.path.join(clone_directory, remote_repo_name)
        self.controller_machine.create_directory(cloned_repo_path, force_create=True)
        output = subprocess.check_output(["git", "clone", remote_repo_url, cloned_repo_path], cwd=clone_directory,
                                         text=True)
        self._log.info(f"'Cloned {remote_repo_name} into {cloned_repo_path}'")
        organization_name = self.organization_url.split('/')[-1]
        output = subprocess.check_output(["git", "remote", "add", "fork",
                                          f"https://{organization_name}:{access_token}@dev.azure.com/{organization_name}/{project_name}/_git/{repo_name}"],
                                         cwd=cloned_repo_path, text=True)
        self._log.info(f"Added remote fork url https://{organization_name}:{access_token}@dev.azure.com/{organization_name}/{project_name}/_git/{repo_name}")
        output = subprocess.check_output(["git", "branch", "-M", "main"],
                                         cwd=cloned_repo_path, text=True)
        self._log.info(f'git branch -M main success')
        output = subprocess.check_output(["git", "push", "fork", "main"], cwd=cloned_repo_path, text=True)
        self._log.info(f'git push fork main command success')

    def create_and_push_branches(self, repo_name, branch_identifier):
        """
        Creates and pushes branches to a specified repository.

        Args:
            repo_name (str): Name of the repository.
            branch_identifier (str): Identifier for the branch name.
        """
        repo_path = os.path.join(self.controller_path, repo_name)
        output = subprocess.check_output(["git", "checkout", "-b", f"auto_branch_{branch_identifier}"], cwd=repo_path,
                                         text=True)
        self._log.info(f'Branch creation success')
        output = subprocess.check_output(["git", "push", "fork", f"auto_branch_{branch_identifier}"], cwd=repo_path,
                                         text=True)
        self._log.info(f'Push branch success')

    def create_and_import_repository(self, access_token, git_url, repo_name, project_name):
        """Creates and imports a repository from the provided git_url, repo_name and the project_name"""
        self._create_repository(repo_name, project_name)
        self._import_repository_after_clone(access_token, git_url, repo_name, project_name)

    def validate_out_of_place_restore_data(self, test_data, backup_path=None, bare_validation=True):
        """
        Validates out-of-place restore data against the provided test data.

        Args:
            test_data (Dict[str, List[Tuple[str, str]]]):
                Dictionary containing project names as keys and lists of tuples
                with repository names and their original project (it belongs to) names as values.
            backup_path (Optional[str]): Path for the backup. Defaults to None,
                indicating self.remote_path.
            bare_validation (bool): Determines whether to perform bare validation.
                Defaults to True.

        Raises:
            Exception: If validation fails due to mismatch in source files or if a repository doesn't exist.
        """
        if bare_validation is None:
            bare_validation = True
        if backup_path is not None:
            self.backup_path = backup_path
        else:
            backup_path = self.remote_path
        for project in test_data:
            if self.check_if_project_exists(project):
                # repo_item[0] is repo_name
                # repo_item[1] is the original project it belongs to
                for repo_item in test_data[project]:
                    if self.check_if_repository_exists(repo_item[0], project):
                        current_backup_path = self.client_machine.join_path(
                            backup_path, f"{repo_item[1]}_{repo_item[0]}")

                        self._download_repository(repo_item[0], project, bare=bare_validation)

                        time.sleep(10)
                        compare_output = self.client_machine.compare_folders(
                            self.client_machine, current_backup_path, self.restore_path,
                            ignore_files=[".gitattributes", "config", "packed-refs"], ignore_folder=[".git", "hooks"])
                        if sorted(compare_output) in (
                                ['config', 'hooks\\fsmonitor-watchman.sample'],
                                ['config', 'hooks\\push-to-checkout.sample'],
                                ['config'], []):
                            self._log.info("Successfully validated repository: "
                                           "%s in project: %s", repo_item[0], project)
                        else:
                            self._log.info("Validation Failed: %s in %s doesn't "
                                           "match source files", repo_item[0], project)
                            self._log.info("Folder comparision output: %s", compare_output)
                            self._log.info(f"Backup Path:{current_backup_path}, "
                                           f"Restore Path: {self.restore_path}")
                            raise Exception("Validation Failed: {0} in {1} doesn't "
                                            "match source files".format(repo_item[0], project))
                    else:
                        self.client_machine.remove_directory(self.remote_path)
                        raise Exception("Validation Failed: {0} in {1} "
                                        "doesn't exist".format(repo_item[0], project))

    def validate_github_to_azure_repos(self, test_data, backup_path=None, bare_validation=None):
        """
        Validates GitHub to Azure Repos migration data against the provided test data.

        Args:
            test_data (Dict[str, List[str]]):
                Dictionary containing project names as keys and lists of repository names as values.
            backup_path (Optional[str]): Path for the backup. Defaults to None,
                indicating self.remote_path.
            bare_validation (Optional[bool]): Determines whether to perform bare validation.
                Defaults to True if not specified.

        Raises:
            Exception: If validation fails due to mismatch in source files.
        """
        if bare_validation is None:
            bare_validation = True
        if backup_path is not None:
            self.backup_path = backup_path
        else:
            backup_path = self.remote_path

        for project in test_data:
            for repo in test_data[project]:
                current_backup_path = self.client_machine.join_path(backup_path, repo)
                self._download_repository(repo, project, bare=bare_validation)
                time.sleep(10)
                compare_output = self.client_machine.compare_folders(
                    self.client_machine, current_backup_path, self.restore_path,
                    ignore_files=[".gitattributes", "config", "packed-refs"], ignore_folder=[".git", "hooks"])
                if sorted(compare_output) in (
                        ['config', 'hooks\\fsmonitor-watchman.sample'],
                        ['config', 'hooks\\push-to-checkout.sample'],
                        ['config'], []):
                    self._log.info("Successfully validated repository: "
                                   "%s in project: %s", repo, project)
                else:
                    self._log.info("Validation Failed: %s in %s doesn't "
                                   "match source files", repo, project)
                    self._log.info("Folder comparision output: %s", compare_output)
                    self._log.info(f"Backup Path:{current_backup_path}, "
                                   f"Restore Path: {self.restore_path}")
                    raise Exception("Validation Failed: {0} in {1} doesn't "
                                    "match source files".format(repo, project))

    def get_repositories_for_project(self, project_name):
        if project_name == '':
            raise Exception('Project name is empty!!')
        repos = self._list_repositories(project_name)
        return repos