# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Helper file for performing GitHub operations

Classes defined in this file
     GitHubHelper : Class which establishes connection with github
                        organization and performs operations.

         __init__ : Initialising github helper object

        __connect : Connect to github organization

        __select_access_node : Selecting an access node for generation/validation of data

        __initialize_working_env : Creating/initializing required folders/members

        _create_repository : Creation of repository with given details

        _import_repository : Importing Repository

        _delete_repository : Deletes Repository

        _list_repositories : Returns list of repositories started with given prefix

        _generate_data : Generates data for repositories.

        _upload_repository : Uploads generated data to Repository

        _download_repository : Downloads repository

        generate_test_data : Returns generated test data

        validate_test_data : Validates given test data

        cleanup : Cleans up generated data and repositories that start with given prefix
"""
import os
import subprocess
import time
import threading

from github import Github
from github.GithubException import UnknownObjectException, GithubException
import requests

from AutomationUtils import logger, constants
from AutomationUtils.machine import Machine


class GitHubHelper:
    """
    Class which establishes connection with github
    organization and performs operations.
    """

    def __init__(self, commcell, organization_name, access_token, access_nodes, git_bin=None, base_url=None):
        """
        Initialising github helper object
        Args:
            commcell                    (obj)  -- Commcell object
            organization_name           (str)  -- organization name
            access_token                (str)  -- personal access token
            access_nodes                (list) -- list of access nodes
            git_bin                     (str)  -- bin path of git binaries
            base_url                    (str)  -- git url in case of enterprise server
        Return:
            object - instance of this class
        """
        self.commcell = commcell
        self.git = git_bin
        self._log = logger.get_log()
        self.__access_token = access_token
        self.git_client = None
        self.organization = None
        self.organization_name = organization_name
        self._base_url = base_url or "https://api.github.com"
        self._base_url = self._base_url.rstrip("/")
        self.__connect(organization_name)
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
        self._git_end_point = "github.com" if base_url is None else self._base_url.split("https://")[-1]
        self.__initialize_working_env(access_nodes)

    def __connect(self, organization_name):
        """
        Connect to github organization
        Args:
            organization_name           (str)  -- organization name
        Raises:
            Exception:
                If connection is not successful
        """
        try:
            self.git_client = Github(self.__access_token, base_url=self._base_url)
            self.organization = self.git_client.get_organization(organization_name)
        except UnknownObjectException as err:
            self._log.info("Connection failed.")
            self._log.info("Please check organization: %s and token:"
                           " %s provided", organization_name, self.__access_token)
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
        self.controller_path = self.controller_machine.join_path(self.controller_machine.tmp_dir,
                                                                 f"GitHubTemp_{threading.get_ident()}"
                                                                 f"_{int(time.time())}")
        self.remote_path = self.client_machine.join_path(client.install_directory, "Temp")
        self.remote_path = self.client_machine.join_path(self.remote_path,
                                                         f"GitHubTemp_{threading.get_ident()}")
        self.backup_path = self.client_machine.join_path(self.remote_path, "Backup")
        self.restore_path = self.client_machine.join_path(self.remote_path, "Restore")
        self.client_machine.create_directory(self.remote_path, force_create=True)
        self.client_machine.create_directory(self.backup_path, force_create=True)
        self.client_machine.create_directory(self.restore_path, force_create=True)
        self.controller_machine.create_directory(self.controller_path, force_create=True)

    def _create_repository(self, repo_name):
        """
        Creation of repository with given details
        Args:
            repo_name           (str) -- name of the repository
        Raises:
            Exception:
                If failed to create repository.
        """
        try:
            self._log.info("Creating repository: %s", repo_name)
            self.organization.create_repo(repo_name, private=True)
            self._log.info("Successfully created repository")
        except GithubException as err:
            self._log.info("Repository creation failed.")
            raise Exception('Exception: {0}'.format(str(err)))
        except Exception as err:
            raise Exception("Unable to create repository: {0}".format(str(err)))

    def _import_repository(self, git_url, repo_name):
        """
        Importing Repository
        Args:
            git_url             (str) -- url of git repository
                                         that needs to be imported
            repo_name           (str) -- name of the repository
        Raises:
            Exception:
                If failed to import repository.
        """
        self._log.info("Importing repository: %s to repository: %s", git_url, repo_name)
        repo = self.organization.get_repo(repo_name)
        repo.create_source_import('git', git_url)
        status = repo.get_source_import().status
        while status in ['importing', 'mapping', 'pushing']:
            time.sleep(30)
            status = repo.get_source_import().status
        if status == 'complete':
            self._log.info("Successfully imported repository")
        else:
            raise Exception("Import failed")

    def _delete_repository(self, repo_name, organization=None):
        """
        Deletes Repository
        Args:
            repo_name           (str) -- name of the repository
        Raises:
            Exception:
                If failed to delete repository.
        """
        try:
            self._log.info("Deleting repository: %s", repo_name)
            repo = organization.get_repo(repo_name) if organization else self.organization.get_repo(repo_name)
            repo.delete()
            self._log.info("Successfully deleted repository")
        except UnknownObjectException as err:
            self._log.info("Repository deletion failed")
            self._log.info('Exception: {0}'.format(str(err)))
            raise Exception('Exception: {0}'.format(str(err)))

    def _list_repositories(self, prefix=""):
        """
        Returns list of repositories started with given prefix
        Args:
            prefix           (str) -- prefix value
                default - ""   (Returns all repositories)
        Returns:
            repo_list       (list) -- list of repositories
        """
        repo_list = []
        repos = self.organization.get_repos()
        for repo in repos:
            if repo.name.startswith(prefix):
                repo_list.append(repo.name)
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

    def _upload_repository(self, repo_name):
        """
        Uploads generated data to Repository
        Args:
            repo_name           (str) -- name of the repository
        """
        self._log.info("Uploading generated data to "
                       "repository: %s", repo_name)
        url = f"https://automation:{self.__access_token}@{self._git_end_point}/" \
              f"{self.organization.login}/{repo_name}.git"
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

    def _download_repository(self, repo_name, download_folder=None, bare=True, org_name=None):
        """
        Downloads repository
        Args:
            repo_name           (str)  -- name of the repository
            download_folder     (str) -- determines where repository should be downloaded
                    default - None    (Downloads to Restore folder in remote path)
            bare     (bool) -- Determines whether to clone repository with bare or not
                default - True  (clones repository with bare option enabled)
        """
        if download_folder is None:
            dest = "Restore"
            self.client_machine.remove_directory(self.restore_path)
            self._log.info("Downloading restored data from repository: %s"
                           " for validation", repo_name)
        else:
            dest = download_folder if "automation" not in repo_name else f"{download_folder}_{repo_name}"
            path = self.client_machine.join_path(self.remote_path, dest)
            self.client_machine.remove_directory(path)
            self._log.info(f"Downloading backed up repository to {path} for validation")
        url = f"https://automation:{self.__access_token}@{self._git_end_point}/" \
              f"{org_name if org_name else self.organization.login}/{repo_name}.git"
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

    def generate_test_data(self, prefix=None, no_of_repos=None, repo_data=None, download_folder=None, git_url=None,
                           bare_validation=True, cleanup=True):
        """
        Returns generated test data
        Args:
            prefix               (str) -- prefix for the created repositories
            no_of_repos          (int) -- number of repositories
            repo_data           (list) -- data to be generated for each repository
                default - [1,2,24] (eg. [No. of folders, files in each folder, size(mb) of file])
                    To verify git lfs functionality use size>110mb
            download_folder    (str) -- Destination folder where data to be downloaded
                    default - None (Downloads to Backup folder in remote path)
            git_url              (str) -- url of repository
                default - None (imports data from repository instead of uploading generated data)
            bare_validation      (bool) -- Determines whether to clone repository with bare or not
                default - True  (validates by cloning with bare option enabled)
            cleanup              (bool) -- Deletes repositories starting with given prefix
                default - True  (Deletes repositories starting with automation_)
        Returns:
            test_data            (list) -- created repositories
        """
        prefix = prefix or "automation_"
        if cleanup:
            self.cleanup(prefix, del_only_repo=True)
        prefix += f"{int(time.time())}_"
        if no_of_repos is None:
            no_of_repos = 2
        repo_data = repo_data or [1, 2, 24]
        download_folder = download_folder or 'Backup'
        if bare_validation is None:
            bare_validation = True
        test_data = []
        repo_name = None
        if git_url is None:
            if repo_data[0] != 0 or no_of_repos != 0:
                self._generate_data(repo_data)
        self._log.info(f"{no_of_repos} repositories are created")
        for repo in range(no_of_repos):
            repo_name = f"{prefix}repo_{str(repo)}"
            self._create_repository(repo_name)
            if git_url is not None:
                self._import_repository(git_url, repo_name)
            elif repo_data[0] != 0:
                self._upload_repository(repo_name)
            test_data.append(repo_name)
            self._download_repository(repo_name, download_folder, bare_validation)
        self._log.info("Successfully generated data")
        return test_data

    def validate_test_data(self, test_data, backup_path=None, disk_path=None, bare_validation=True, organization=None):
        """
        Validates given test data
        Args:
            test_data       (list) -- repositories list
            backup_path     (str)  -- restore files that needs to be validated against
            disk_path       (str)  -- where restore files are located (only restore to disk case)
            bare_validation      (bool) -- Determines whether to clone repository with bare or not
                default - True  (validates by cloning with bare option enabled)
        Raises:
            Exception:
                If validation is failed
        """
        if bare_validation is None:
            bare_validation = True
        if backup_path is not None:
            self.backup_path = backup_path
        else:
            backup_path = self.remote_path
        for repo in test_data:
            current_backup_path = f"{self.backup_path}_{repo}" if "automation" in repo else self.client_machine.join_path(
                backup_path, repo)
            if disk_path is None:
                self._download_repository(repo, bare=bare_validation, org_name=organization)
            else:
                # restored to disk
                repo_path = self.client_machine.join_path(disk_path, organization if organization else self.organization.login, repo)
                bare = "--bare" if bare_validation else ""
                data = {
                    'GITBIN': self.git,
                    'SRCPATH': f'{repo_path}.git',
                    'RESTOREPATH': self.client_machine.join_path(disk_path, organization if organization else self.organization.login),
                    'DEST_REPO': repo,
                    'BARE': bare
                }
                output = self.client_machine.execute_script(self._index_to_repository_script, data)
                if output.exit_code != 0:
                    raise Exception("Git Index to Restore script execution failed with: %s", output.exception)
                self._log.debug("Output of Git Index to Restore script: %s", output.formatted_output)
                self._log.info("Successfully restored data")

                self.restore_path = self.client_machine.join_path(
                    disk_path, organization if organization else self.organization.login, repo)
            time.sleep(10)
            compare_output = self.client_machine.compare_folders(
                self.client_machine, current_backup_path, self.restore_path,
                ignore_files=[".gitattributes", "config", "packed-refs"], ignore_folder=[".git", "hooks"])
            if sorted(compare_output) in (
                    ['config', 'hooks\\fsmonitor-watchman.sample'], ['config', 'hooks\\push-to-checkout.sample'],
                    ['config'],
                    []):
                self._log.info("Successfully validated repository: %s", repo)
            else:
                self._log.info("Validation Failed: %s doesn't match source files", repo)
                self._log.info("Folder comparision output: %s", compare_output)
                self._log.info(f"Backup Path:{current_backup_path}, Restore Path: {self.restore_path}")
                raise Exception("Validation Failed: {0} doesn't match source files".format(repo))

    def cleanup(self, prefix=None, del_only_repo=False):
        """
        Cleans up generated data and repositories that start with given prefix
        Args:
            prefix      (str) -- prefix of the repositories that needs to be deleted
            del_only_repo    (bool) -- doesn't delete the created temp directory if true
        """
        if prefix != "":
            prefix = prefix or "automation_"
        if not del_only_repo:
            self._log.info("Cleaning up data")
            self.client_machine.remove_directory(self.remote_path)
            self._log.info("Cleaned up data")
        self._log.info("Deleting repositories that start with prefix: %s", prefix)
        repo_list = self._list_repositories(prefix)
        for repo in repo_list:
            self._delete_repository(repo)
        self._log.info("Successfully deleted repositories that started with prefix: %s", prefix)

    def validate_azure_to_github_repos(self, test_data, backup_path=None, bare_validation=True):
        """
        Validates Azure to GitHub Repos migration data against the provided test data.

        Args:
            test_data (List[Tuple[str, str]]):
                List of tuples containing repository names and their original project names.
            backup_path (Optional[str]): Path for the backup. Defaults to None,
                indicating self.remote_path.
            bare_validation (bool): Determines whether to perform bare validation.
                Defaults to True.

        Raises:
            Exception: If validation fails due to mismatch in source files.
        """
        if bare_validation is None:
            bare_validation = True

        if backup_path is not None:
            self.backup_path = backup_path
        else:
            backup_path = self.remote_path

        for repo_item in test_data:
            current_backup_path = self.client_machine.join_path(
                backup_path, f"{repo_item[1]}_{repo_item[0]}")

            self._download_repository(repo_item[0], bare=bare_validation)
            time.sleep(10)
            compare_output = self.client_machine.compare_folders(
                self.client_machine, current_backup_path, self.restore_path,
                ignore_files=[".gitattributes", "config", "packed-refs"], ignore_folder=[".git", "hooks"])
            if sorted(compare_output) in (
                    ['config', 'hooks\\fsmonitor-watchman.sample'], ['config', 'hooks\\push-to-checkout.sample'],
                    ['config'],
                    []):
                self._log.info("Successfully validated repository: %s", repo_item[0])
            else:
                self._log.info("Validation Failed: %s doesn't match source files", repo_item[0])
                self._log.info("Folder comparision output: %s", compare_output)
                self._log.info(f"Backup Path:{current_backup_path}, Restore Path: {self.restore_path}")
                raise Exception("Validation Failed: {0} doesn't match source files".format(repo_item[0]))

    def get_repositories(self, prefix=""):
        """
        Retrieves a list of repositories filtered by the specified prefix.

        Args:
            prefix (str): Prefix used to filter repository names. Defaults to an empty string.

        Returns:
            List[str]: List of repository names filtered by the specified prefix.
        """
        return self._list_repositories(prefix)

    def delete_repository(self, repo, org_name=None):
        """
        Deletes the specified repository from the organization.

        Args:
            repo (str): Name of the repository to be deleted.
            org_name (Optional[str]): Name of the organization. Defaults to None.
        """
        organization = None
        if org_name:
            organization = self._connect_to_organization(org_name)
            self._log.info(f'Connected to organization {org_name} for deleting repos')
        self._delete_repository(repo, organization)

    def store_repos(self, data, backup_path='', bare=True):
        """Stores repo content at backup_path/{repo}"""
        # backup_path relative to self.remote_path
        remote_repos = self._list_repositories()
        for repo in data:
            if repo in remote_repos:
                current_backup_path = ''
                if backup_path == '':
                    current_backup_path = f'{repo}'
                else:
                    current_backup_path = self.client_machine.join_path(backup_path, f'{repo}')
                self._log.info(f"Downloading {repo} in {current_backup_path} for validation")
                self._download_repository(repo, current_backup_path, bare)

    def _import_repository_after_clone(self, repo_name, remote_repo_url):
        """
        Clones a repository from a remote URL and performs necessary setup tasks.

        Args:
            repo_name (str): The name of the repository.
            remote_repo_url (str): The URL of the remote repository to clone.
        """
        remote_repo_name = os.path.splitext(os.path.basename(remote_repo_url))[0]
        clone_directory = self.controller_path
        cloned_repo_path = os.path.join(clone_directory, remote_repo_name)
        self.controller_machine.create_directory(cloned_repo_path, force_create=True)
        output = subprocess.check_output(["git", "clone", remote_repo_url, cloned_repo_path], cwd=clone_directory,
                                         text=True)
        self._log.info('Cloned [%s] into [%s]', remote_repo_name, cloned_repo_path)
        self._log.info(f'Output : {output}')
        output = subprocess.check_output(["git", "remote", "add", "fork",
                                          f"https://{self.__access_token}@github.com/{self.organization_name}/{repo_name}.git"],
                                         cwd=cloned_repo_path, text=True)
        self._log.info('Added remote fork url [%s]',
                       f"https://{self.__access_token}@github.com/{self.organization_name}/{repo_name}.git")
        self._log.info(f'Output : {output}')
        output = subprocess.check_output(["git", "branch", "-M", "main"],
                                         cwd=cloned_repo_path, text=True)
        self._log.info('git branch -M main command being executed...')
        self._log.info(f'Output : {output}')
        output = subprocess.check_output(["git", "push", "fork", "main"], cwd=cloned_repo_path, text=True)
        self._log.info('git push fork main command : Output : ')
        self._log.info(f'Output : {output}')

    def create_and_push_branches(self, repo_name, branch_identifier):
        """
        Creates and pushes a new branch to the remote repository.

        Args:
            repo_name (str): The name of the repository.
            branch_identifier (str): Identifier for the new branch.
        """
        repo_path = os.path.join(self.controller_path, repo_name)
        output = subprocess.check_output(["git", "checkout", "-b", f"auto_branch_{branch_identifier}"], cwd=repo_path,
                                         text=True)
        self._log.info(f'Branch creation : {output}')
        output = subprocess.check_output(["git", "push", "fork", f"auto_branch_{branch_identifier}"], cwd=repo_path, text=True)
        self._log.info(f'Push branch output : {output}')

    def create_and_import_repository(self, repo_name, git_url):
        """
        Creates and imports a repository from the specified Git URL.

        Args:
            repo_name (str): The name of the repository to be created.
            git_url (str): The URL of the Git repository to import.
        """
        self._create_repository(repo_name)
        self._import_repository_after_clone(repo_name, git_url)

    def _connect_to_organization(self, organization_name):
        """
            Connects to GitHub organization
            Args:
                organization_name           (str)  -- organization name
            Raises:
                Exception: If connection is not successful
        """
        try:
            organization = self.git_client.get_organization(organization_name)
        except UnknownObjectException as err:
            self._log.info("Connection failed.")
            self._log.info("Please check organization: %s and token:"
                           " %s provided", organization_name, self.__access_token)
            raise Exception('Exception: {0}'.format(str(err)))
        except Exception as err:
            raise Exception("Unable to connect: {0}".format(str(err)))
        return organization

