# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Input Example:
    "testCases":{
        "63135":
        {
        "azure_app_name": "<Azure App Name>",
        "azure_access_token": "<Azure Personal Access Token>",
        "azure_organization_name": "<Azure Organization name>",
        "access_nodes": "<string representation of access nodes list>", (eg. "['node']"),
        "content": "list of projects to be selected as repository group backup content"

        "git_app_name": "<Git App Name>",
        "git_access_token": "<Git Personal Access Token>",
        "git_organization_name": "<Git Organization name>",

        "accessnodes_type": "<os type of access nodes>" (optional, required for creating new app),
        "plan": "<Plan name>" (optional, required for creating new app),
        "test_data": "<string representation of test data dictionary>" (optional,eg."{'key':'val'}")
            default- "{
                       "bare_validation": "Validation done with bare", (optional, default-True)
                       }"
        }
    }
"""
from Web.AdminConsole.DevOps.devops_common_DevOpsApp_helper import DevOpsAppHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure

from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "Azure DevOps IDA - Verify Backup and Restore for Repos"
        self.browser = None
        self.admin_console = None
        self.is_azure_app_created = False
        self.is_git_app_created = False
        self.is_azure_repo_group_created = False
        self.tcinputs = {
            "azure_app_name": None,
            "azure_access_token": None,
            "azure_organization_name": None,
            "access_nodes": None,
            "content": None
        }
        self.azure_app_helper = None
        self.git_app_helper = None

    def setup(self):
        """Setup function of this test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.admin_console.navigator.navigate_to_devops()
            self.tcinputs['repository_group'] = self.tcinputs.get('repository_group', f'auto_inplace_{self.id}_135')
            self.tcinputs['azure_services'] = ['Repos']
            self.azure_app_helper = DevOpsAppHelper(self.commcell, self.admin_console, self.tcinputs, self.log,
                                                    is_azure=True)
            self.git_app_helper = DevOpsAppHelper(self.commcell, self.admin_console, self.tcinputs, self.log,
                                                  is_git=True)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def access_or_create_client(self):
        """Access client if exists else creates new one"""
        self.is_git_app_created = self.git_app_helper.access_or_create_instance_from_instances()
        self.admin_console.select_breadcrumb_link_using_text("DevOps")
        self.is_azure_app_created = self.azure_app_helper.access_or_create_instance_from_instances()

    @test_step
    def download_data_and_backup(self):
        """Downloads services data and runs a backup"""
        self.admin_console.access_tab('Repository groups')
        repository_group = self.tcinputs.get('repository_group')
        content = self.tcinputs['content']
        is_exists = self.azure_app_helper.check_if_repository_group_exists_from_repository_groups(repository_group)
        if is_exists:
            self.azure_app_helper.delete_repository_group_from_repository_groups(self.tcinputs.get("repository_group"))
        self.log.info(f"Using repository group: {repository_group} for backup and restore")
        backup_details = self.azure_app_helper.backup_from_repository_groups(repository_group, for_validation=True,
                                                                             services=['Repos'],
                                                                             select=content)
        self.is_azure_repo_group_created = backup_details.get('is_repo_group_created', False)
        self.log.info('Successfully downloaded projects and repositories for validation : %s',
                      self.azure_app_helper.az_data)

    @test_step
    def restore_and_validate_data_in_place(self):
        """Restores and validate repo data"""
        content = self.tcinputs['content']
        for iteration in range(0, 2):
            # Choose all services in iteration 1
            if iteration == 1:
                self.azure_app_helper.cleanup_files(projects=content, delete_temp_files=False)
                services = ['Boards', 'Pipelines', 'Repos', 'Test Plans', 'Artifacts']
            else:
                # Choose only Repos in iteration 0
                services = ['Repos']
            self.azure_app_helper.restore_from_repository_groups(self.tcinputs.get('repository_group', 'default'),
                                                                 validate_data=True,
                                                                 services=services,
                                                                 in_place=True)
            self.log.info(f"Done with restore in place #{iteration}")
            self.admin_console.wait_for_completion()
            self.admin_console.select_breadcrumb_link_using_text(self.azure_app_helper.app_name)
            self.admin_console.wait_for_completion()
            self.admin_console.access_tab('Repository groups')

    @test_step
    def restore_and_validate_data_out_of_place(self):
        """Restores and validate repo data"""
        content = self.tcinputs['content']
        for iteration in range(0, 2):
            if iteration == 1:
                self.azure_app_helper.cleanup_files(projects=[self.tcinputs.get("dest_project", f"dest_prj_{self.id}")],
                                                    delete_temp_files=False)
                services = ['Boards', 'Pipelines', 'Repos', 'Test Plans', 'Artifacts']
            else:
                services = ['Repos']

            dest_project = self.tcinputs.get("dest_project", f"dest_prj_{self.id}")
            self.log.info(
                f"Restoring the repositories and services of {self.tcinputs['azure_organization_name']} to {dest_project} in {self.azure_app_helper.app_name}")
            self.azure_app_helper.restore_from_repository_groups(self.tcinputs.get('repository_group', 'default'),
                                                                 des_app=self.azure_app_helper.app_name,
                                                                 org_name=self.tcinputs['azure_organization_name'],
                                                                 project_name=dest_project,
                                                                 validate_data=True,
                                                                 out_of_place=True,
                                                                 des_app_type="azure",
                                                                 services=services,
                                                                 )
            self.log.info(f"Done with restore out of place #{iteration}")
            self.admin_console.wait_for_completion()
            self.admin_console.select_breadcrumb_link_using_text(self.azure_app_helper.app_name)
            self.admin_console.wait_for_completion()
            self.admin_console.access_tab('Repository groups')

        # Restore to Github
        dest_account_type = self.tcinputs.get("git_acctype") or "Business/Institution"
        self.azure_app_helper.restore_from_repository_groups(self.tcinputs.get('repository_group', 'default'),
                                                             des_app=self.git_app_helper.app_name,
                                                             org_name=self.tcinputs['git_organization_name'],
                                                             account_type=dest_account_type,
                                                             validate_data=True,
                                                             out_of_place=True,
                                                             des_app_type='github',
                                                             app_helper=self.git_app_helper.githelper,
                                                             )
        self.log.info("Done with restore out of place to Github")

        self.admin_console.wait_for_completion()
        self.admin_console.select_breadcrumb_link_using_text(self.azure_app_helper.app_name)
        self.admin_console.wait_for_completion()
        self.admin_console.access_tab('Repository groups')

        des_path = f"/restored_data_{self.tcinputs.get('repository_group', 'default')}" if self.tcinputs[
                                                                                               'accessnodes_type'] == 'unix' else f"C:\\restored_data_{self.tcinputs.get('repository_group', 'default')}"
        # Restore to Disk
        self.azure_app_helper.restore_from_repository_groups(self.tcinputs.get('repository_group', 'default'),
                                                             restore_to_disk=True,
                                                             des_server=self.azure_app_helper.access_nodes[0],
                                                             des_path=des_path,
                                                             validate_data=True,
                                                             )
        self.admin_console.select_breadcrumb_link_using_text('DevOps')

    def run(self):
        """
        Run function of this test case
        1) Access the instance, creates new instance if not present
        2) Backup selected content(projects and repositories) with only Repos service,download service data
        3) Restore all projects and repositories for in place azure restore, select only Repos service
        4) Restore all projects and repositories for in place azure restore, select all services
        5) Repository and services validation by downloading the data - done for both inplace azure restores
        6) Restore all projects and repositories for out of place azure restore, select only Repos service
        7) Restore all projects and repositories for out of place azure restore, select all services
        8) Repository and services validation by downloading the data - done for both out of place azure restores
        9) Restore all projects and repositories for out of place github restore, job should fail with no repos JPR
        """
        try:
            self.access_or_create_client()
            self.download_data_and_backup()
            self.restore_and_validate_data_in_place()
            self.restore_and_validate_data_out_of_place()

            self.azure_app_helper.cleanup_files(projects=[self.tcinputs.get("dest_project", f"dest_prj_{self.id}")])
            all_repos = []
            for org_project_name, repos in self.azure_app_helper.az_data.items():
                all_repos.extend(repos)
            self.git_app_helper.cleanup_files(repos=all_repos,
                                              github_org_name=self.tcinputs['git_organization_name'])
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.is_git_app_created:
            self.git_app_helper.delete_app_from_instances()

        if self.is_azure_app_created:
            self.azure_app_helper.delete_app_from_instances()

        if not self.is_azure_app_created and self.is_azure_repo_group_created:
            self.azure_app_helper.access_instance_from_instances()
            self.admin_console.access_tab('Repository groups')
            self.azure_app_helper.delete_repository_group_from_repository_groups(self.tcinputs.get('repository_group'))
            self.admin_console.wait_for_completion()
            self.admin_console.select_breadcrumb_link_using_text("DevOps")

        if self.is_azure_app_created:
            self.navigator.navigate_to_servers()
            self.azure_app_helper.delete_app_from_servers()

        if self.is_git_app_created:
            self.navigator.navigate_to_servers()
            self.git_app_helper.delete_app_from_servers()

        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
