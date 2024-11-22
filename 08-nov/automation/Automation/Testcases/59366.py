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
        "59366":
        {
        "azure_app_name": "<Azure App Name>",
        "azure_access_token": "<Azure Personal Access Token>",
        "azure_organization_name": "<Azure Organization name>",
        "azure_app_name": "<Git App Name>",
        "git_access_token": "<Git Personal Access Token>",
        "git_organization_name": "<Git Organization name>",
        "access_nodes": "<string representation of access nodes list>", (eg. "['node']"),

        "accessnodes_type": "<os type of access nodes>" (optional, required for creating new app),
        "plan": "<Plan name>"        (optional, required for creating new app),
        "dest_project": "<destination project>" (optional, default- automation_project_59366),
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
        self.name = "GitHub IDA Command Center - ACCT1 Out Of Place" \
                    "(GitHub) & Cross Client(Azure DevOps) Restore"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.is_git_repo_group_created = False
        self.is_azure_app_created = False
        self.is_git_app_created = False
        self.tcinputs = {
            "azure_app_name": None,
            "azure_access_token": None,
            "azure_organization_name": None,
            "git_app_name": None,
            "git_access_token": None,
            "git_organization_name": None,
            "access_nodes": None,
            "git_destination_organization_name": None
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
            self.azure_app_helper = DevOpsAppHelper(self.commcell, self.admin_console, self.tcinputs, self.log,
                                                    is_azure=True)
            self.git_app_helper = DevOpsAppHelper(self.commcell, self.admin_console, self.tcinputs, self.log,
                                                  is_git=True)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def access_or_create_client(self):
        """Access client if exists else creates new one"""
        self.is_azure_app_created = self.azure_app_helper.access_or_create_instance_from_instances()
        self.admin_console.select_breadcrumb_link_using_text("DevOps")
        self.is_git_app_created = self.git_app_helper.access_or_create_instance_from_instances()

    @test_step
    def backup(self):
        """Runs a backup"""
        self.admin_console.access_tab("Repository groups")
        repository_group = self.tcinputs.get('repository_group', 'default')
        backup_job_details = self.git_app_helper.backup_from_repository_groups(repository_group, for_validation=True)
        self.is_git_repo_group_created = backup_job_details['is_repo_group_created']
        self.log.info('Backed up projects and repositories : %s', self.git_app_helper.git_data)

    @test_step
    def restore_and_validate_data_azure(self):
        """Restores to azure and validates test data"""
        dest_project = self.tcinputs.get("dest_project",
                                         f"dest_prj_{self.id}")
        self.log.info(f"Restoring the repositories to {dest_project} in {self.azure_app_helper.app_name}")
        self.admin_console.access_tab("Repository groups")
        repository_group = self.tcinputs.get('repository_group', 'default')
        self.git_app_helper.restore_from_repository_groups(repository_group=repository_group,
                                                           des_app=self.azure_app_helper.app_name,
                                                           org_name=self.tcinputs['azure_organization_name'],
                                                           project_name=dest_project,
                                                           validate_data=True,
                                                           out_of_place=True,
                                                           des_app_type='azure',
                                                           app_helper=self.azure_app_helper.azhelper
                                                           )
        self.admin_console.select_breadcrumb_link_using_text("DevOps")

    @test_step
    def restore_and_validate_data_git(self):
        """Restores to git and validates test data"""
        repository_group = self.tcinputs.get('repository_group', 'default')
        dest_org = self.tcinputs.get("git_destination_organization_name")
        if dest_org is None:
            raise Exception("Please provide a destination organization in GitHub")
        self.log.info(f"Restoring the repositories to {dest_org} in {self.git_app_helper.app_name}")
        self.git_app_helper.restore_from_repository_groups(repository_group=repository_group,
                                                           des_app=self.git_app_helper.app_name,
                                                           org_name=dest_org,
                                                           validate_data=True,
                                                           out_of_place=True,
                                                           des_app_type="github")

    def run(self):
        """
        Run function of this test case
        1) Creates new git and azure instances if not present
        2) Access the git instance
        3) Backup all projects and repositories
        4) Restore all projects and repositories using out of place restore(git instance)
        5) Repository validation by downloading the data
        6) Restore all projects and repositories using out of place restore(azure instance)
        7) Repository validation by downloading the data
        """
        try:
            self.access_or_create_client()
            self.backup()
            self.restore_and_validate_data_git()
            self.admin_console.select_breadcrumb_link_using_text(self.git_app_helper.app_name)
            self.restore_and_validate_data_azure()

            self.azure_app_helper.cleanup_files(projects=[self.tcinputs.get("dest_project",
                                                                            f"dest_prj_{self.id}")])
            self.git_app_helper.cleanup_files(repos=self.git_app_helper.git_data,
                                              github_org_name=self.tcinputs.get('git_destination_organization_name'))
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.is_git_app_created:
            self.git_app_helper.delete_app_from_instances()

        if self.is_azure_app_created:
            self.azure_app_helper.delete_app_from_instances()

        if not self.is_git_app_created and self.is_git_repo_group_created:
            self.git_app_helper.access_instance_from_instances()
            self.admin_console.access_tab('Repository groups')
            self.git_app_helper.delete_repository_group_from_repository_groups(self.tcinputs.get('repository_group'))
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
