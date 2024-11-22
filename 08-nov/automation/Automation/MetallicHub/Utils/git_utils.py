# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for executing git commands

    GitUtils:

        __init__()                      --  Initializes GIT helper util class

        git_clone                       --  Clones a given git repo

        git_checkout                    --  Checkouts the given branch

        git_add                         --  Adds the files to git

        git_commit                      --  commits the changes to a given branch

        git_push                        --  Pushes the changes to the branch

        create_pr                       --  Creates a pull request to repo

        git_init                        --  Performs git init operation

"""
import os
import subprocess

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.windows_machine import Machine
from MetallicHub.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.METALLIC_HUB_CONFIG_FILE_PATH).Hub


class GitUtils:
    """ helper class for User related operations in Metallic Ring"""

    def __init__(self, repo_url, branch_name, repo_name):
        """
        Initializes GIT Utils class
        Args:
            repo_url(str)           --  Git repository URL
            branch_name(str)        --  Name of the GIT branch
            repo_name(str)          --  Repository name
        """
        super().__init__()
        # self.clone_path = clone_path
        self.repo_url = repo_url
        self.branch_name = branch_name
        self.repo_name = repo_name
        self.local_machine = Machine()
        self.log = logger.get_log()
        subprocess.run(["git", "config", "--system", "core.longpaths", "true"], check=True)
        cmd = "az config set extension.use_dynamic_install=yes_without_prompt"
        self.local_machine.execute_command(cmd)

    def git_clone(self):
        """
        Performs git clone operation
        """
        self.log.info(f"Request received to clone repo URL - [{self.repo_url}]")
        subprocess.run(["git", "clone", self.repo_url], check=True)
        self.log.info(f"Clone successful")

    def git_init(self):
        """
        Performs git init operation
        """
        self.log.info(f"Request received to perform git init")
        subprocess.run(["git", "init"], check=True)
        self.log.info(f"Git Init successful")

    def git_checkout(self, branch_name=None):
        """
        Checkouts a new git branch
        Args:
            branch_name(str)        --  Name of the git branch
        """
        if branch_name is None:
            branch_name = self.branch_name
        self.log.info(f"Checking out the branch - [{branch_name}]")
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        self.log.info("Checkout complete")

    def git_add(self, add_all=True):
        """
        Add all the new changes to git
        Args:
            add_all(bool)           --  Adds all the new changes
        """
        if add_all:
            self.log.info("Request received to add all files and folders")
            subprocess.run(["git", "add", "."], check=True)
        else:
            self.log.info("Request received to add only files")
            subprocess.run(["git", "add", "*.*"], check=True)
        self.log.info("Git add complete")

    def git_commit(self, message):
        """
        Commits all the changes with a message
        Args:
            message(str)    --  Message for commit
        """
        self.log.info(f"Performing git commit with message - [{message}]")
        op = subprocess.check_output(["git", "status"])
        if cs.GIT_NOTHING_TO_COMMIT_MSG in op.decode('utf-8'):
            self.log.info("Nothing to commit")
            return
        subprocess.run(["git", "commit", "-m", message], check=True)
        self.log.info("Git commit successful")

    def git_push(self, remote_name=cs.REMOTE_BRANCH_NAME, branch_name=None):
        """
        Pushes the changes to branch
        Args:
            remote_name(str)        --  Name of the remote branch
            branch_name(str)        --  Name of the branch
        """
        if branch_name is None:
            branch_name = self.branch_name
        self.log.info(f"Pushing changes of branch - [{branch_name}]")
        subprocess.run(["git", "push", "-u", remote_name, branch_name], check=True)
        self.log.info("Git push successful")

    def create_pr(self, repo_name, branch_name=None):
        """
        Creates a pull request in the git repository
        Args:
            repo_name(str)      --  Name of the repository
            branch_name(str)    --  Name of the branch
        Raises:
            Exception when pull request fails with an exception/exception message
        """
        if repo_name is None:
            repo_name = self.repo_name
        if branch_name is None:
            branch_name = self.branch_name
        self.log.info(f"Creating pull request - [{repo_name}], [{branch_name}]")
        cmd = f"az repos pr create --repository '{repo_name}' --source-branch '{branch_name}' " \
              "--target-branch master --auto-complete true --open --output table"
        command_op = self.local_machine.execute_command(cmd)
        if command_op.exception_message:
            if cs.GIT_ACTIVE_PULL_REQUEST_EXISTS in command_op.exception_message\
                    or cs.GIT_DEVOPS_WARNING_MSG in command_op.exception_message:
                return
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            if cs.GIT_ACTIVE_PULL_REQUEST_EXISTS in command_op.exception\
                    or cs.GIT_DEVOPS_WARNING_MSG in command_op.exception:
                return
            raise Exception(command_op.exception_code, command_op.exception)
        self.log.info("Creating pull request complete. Approve the pull request")