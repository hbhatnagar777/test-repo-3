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
        "63133":
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
        "staging_path": "<Staging path>"  (optional, used while creating new app if specified),
        "impersonate_user": "<dict of impersonation details>" (optional, default- option disabled),

        "git_bin":  "<Git binary path>"   (optional, required when not using default bin path),
        "test_data": "<string representation of test data dictionary>" (optional,eg."{'key':'val'}")
            default- "{"prefix": "<prefix to be used for generated data>", (default-automation_)
                       "no_of_projects": "<no.of projects>",  (optional, default-2)
                       "no_of_repos": "<no. of repos in each project>",  (optional, default-2)
                       "git_url": "<repo url that need to be imported>", (optional, default-None)
                       "download_folder": "<folder name in remote path>", (optional, default-Backup)
                       "bare_validation": "Validation done with bare", (optional, default-True)
                       "repo_data": <[No. folders, files in each folder, file size(mb)]>}"
                                (optional, default -[2,2,24])
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
        self.name = "Azure DevOps IDA - Verify Backup and Restore for Pipelines"
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
            self.tcinputs['repository_group'] = self.tcinputs.get('repository_group', f'auto_inplace_{self.id}')
            self.tcinputs['azure_services'] = ['Pipelines']
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
        is_exists = self.azure_app_helper.check_if_repository_group_exists_from_repository_groups(repository_group)
        content = self.tcinputs['content']
        if is_exists:
            self.azure_app_helper.delete_repository_group_from_repository_groups(self.tcinputs.get("repository_group"))
        for project in content:
            self.azure_app_helper.azhelper.download_services_data(project, services=['Pipelines'])
        self.log.info("Successfully downloaded services data for test projects : %s", content)
        self.azure_app_helper.backup_from_repository_groups(repository_group, services=['Pipelines'], select=content)

    @test_step
    def restore_and_validate_data_in_place(self):
        """Restores and validate services data"""
        content = self.tcinputs['content']
        for iteration in range(0, 2):
            # Choose all services in iteration 1
            if iteration == 1:
                self.azure_app_helper.cleanup_files(projects=content, delete_temp_files=False)
                services = ['Boards', 'Pipelines', 'Repos', 'Test Plans', 'Artifacts']
            else:
                # Choose only Pipelines in iteration 0
                services = ['Pipelines']
            self.azure_app_helper.restore_from_repository_groups(self.tcinputs.get('repository_group', 'default'),
                                                                 validate_data=False,
                                                                 services=services,
                                                                 in_place=True)
            self.log.info(f"Done with restore in place #{iteration}")
            self.azure_app_helper.download_and_validate_services_data(content, services=['Pipelines'], in_place=True)
            self.admin_console.wait_for_completion()
            self.admin_console.select_breadcrumb_link_using_text(self.azure_app_helper.app_name)
            self.admin_console.wait_for_completion()
            self.admin_console.access_tab('Repository groups')

    @test_step
    def restore_and_validate_data_out_of_place(self):
        """Restores and validate services data"""
        content = self.tcinputs['content']
        new_content = []
        for iteration in range(0, 2):
            if iteration == 1:
                self.azure_app_helper.cleanup_files(projects=new_content, delete_temp_files=False)
                services = ['Boards', 'Pipelines', 'Repos', 'Test Plans', 'Artifacts']
            else:
                services = ['Pipelines']
            project_map = {}
            new_content = []
            for project in content:
                dest_project = f"dest_prj_{project}"
                project_map[dest_project] = project
                new_content.append(dest_project)
                self.log.info(
                    f"Restoring the repositories and services of {project} to {dest_project} in {self.azure_app_helper.app_name}")
                self.azure_app_helper.restore_from_repository_groups(self.tcinputs.get('repository_group', 'default'),
                                                                     des_app=self.azure_app_helper.app_name,
                                                                     org_name=self.tcinputs['azure_organization_name'],
                                                                     project_name=dest_project,
                                                                     validate_data=False,
                                                                     out_of_place=True,
                                                                     des_app_type="azure",
                                                                     services=services,
                                                                     select_path=f"\\{self.tcinputs['azure_organization_name']}\\{project}")
            self.log.info(f"Done with restore out of place #{iteration}")
            self.azure_app_helper.download_and_validate_services_data(new_content, services=['Pipelines'],
                                                                      out_of_place=True,
                                                                      project_map=project_map)
            self.admin_console.wait_for_completion()
            self.admin_console.select_breadcrumb_link_using_text(self.azure_app_helper.app_name)
            self.admin_console.wait_for_completion()
            self.admin_console.access_tab('Repository groups')

        # # Restore to Github and verify JPR
        # dest_account_type = self.tcinputs.get("git_acctype") or "Business/Institution"
        # self.azure_app_helper.restore_from_repository_groups(self.tcinputs.get('repository_group', 'default'),
        #                                                      des_app=self.git_app_helper.app_name,
        #                                                      org_name=self.tcinputs['git_organization_name'],
        #                                                      account_type=dest_account_type,
        #                                                      validate_data=True,
        #                                                      out_of_place=True,
        #                                                      des_app_type='github',
        #                                                      app_helper=self.git_app_helper.githelper,
        #                                                      verify_jpr="Nothing to restore, no repositories found"
        #                                                      )
        # self.log.info("Done with restore out of place and verifed JPR for Github")
        self.admin_console.select_breadcrumb_link_using_text('DevOps')

    def run(self):
        """
        Run function of this test case
        1) Access the instance, creates new instance if not present
        2) Backup selected content(projects and repositories) with only Pipelines service,download service data
        3) Restore all projects and repositories for in place azure restore, select only Pipelines service
        4) Restore all projects and repositories for in place azure restore, select all services
        5) Repository and services validation by downloading the data - done for both inplace azure restores
        6) Restore all projects and repositories for out of place azure restore, select only Pipelines service
        7) Restore all projects and repositories for out of place azure restore, select all services
        8) Repository and services validation by downloading the data - done for both out of place azure restores
        9) Restore all projects and repositories for out of place github restore, job should fail with no repos JPR
        """
        try:
            self.access_or_create_client()
            self.download_data_and_backup()
            self.restore_and_validate_data_in_place()
            self.restore_and_validate_data_out_of_place()

            content = self.tcinputs['content']
            self.azure_app_helper.cleanup_files(projects=[f"dest_prj_{project}" for project in content])
            self.git_app_helper.cleanup_files()
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
