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
        "62640":
        {
        "azure_app_name": "<Azure App Name>",
        "azure_access_token": "<Azure Personal Access Token>",
        "azure_organization_name": "<Azure Organization name>",
        "access_nodes": "<string representation of access nodes list>", (eg. "['node']"),

        "accessnodes_type": "<os type of access nodes>" (optional, required for creating new app),
        "plan": "<Plan name>" (optional, required for creating new app),
        "staging_path": "<Staging path>"  (optional, used while creating new app if specified),
        "impersonate_user": "<dict of impersonation details>" (optional, default- option disabled),

        "des_server":  "<Destination client>" (optional, uses an access node if not specified),
        "des_path":  "<Destination Path>" (optional, uses temporary path in des_server by default)

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
from Application.DevOps.devops_helper import DevOpsHelper

from Web.AdminConsole.DevOps.instances import Instances
from Web.AdminConsole.DevOps.details import Overview
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
        self.name = "Azure DevOps IDA - Verify Job Restartability For Restore To Disk TC"
        self.browser = None
        self.admin_console = None
        self.instances = None
        self.devopshelper = None
        self.azhelper = None
        self.az_data = None
        self.overview = None
        self.test_data = None
        self.is_repo_group_created = False
        self.tcinputs = {
            "azure_app_name": None,
            "azure_access_token": None,
            "azure_organization_name": None,
            "access_nodes": None
        }

    def setup(self):
        """Setup function of this test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.admin_console.navigator.navigate_to_devops()
            self.instances = Instances(self.admin_console)
            self.instances.select_all_instances_view()
            self.overview = Overview(self.admin_console)
            self.devopshelper = DevOpsHelper(self.commcell, self.tcinputs)
            self.test_data = self.devopshelper.test_data
            self.azhelper = self.devopshelper.azhelper
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def access_or_create_client(self):
        """Access client if exists else creates new one"""
        azure_app_name = self.tcinputs['azure_app_name']
        if not self.instances.is_instance_exists(azure_app_name):
            if self.tcinputs.get("plan"):
                self.log.info("Creating azure devops instance")
                az_instance = self.instances.add_azuredevops_instance()
                az_instance.add_azure_details(self.tcinputs["azure_access_token"],
                                              self.tcinputs["azure_organization_name"],
                                              self.devopshelper.access_nodes,
                                              self.tcinputs["plan"],
                                              self.tcinputs.get("accessnodes_type"),
                                              app_name=azure_app_name,
                                              azure_services=["Repos"],
                                              staging_path=self.tcinputs.get("staging_path"),
                                              impersonate_user=self.tcinputs.get("impersonate_user"))
                self.log.info("successfully created instance")
            else:
                raise CVTestCaseInitFailure(f"Instance: {azure_app_name} doesn't exist."
                                            f" Plan is required for creating new instance")
        self.instances.access_instance(azure_app_name)

    @test_step
    def generate_data_and_backup(self):
        """Generates test data and runs a backup"""
        repository_group = self.tcinputs.get('repository_group', 'default')
        is_exists = self.overview.is_repository_group_exists(repository_group)
        if repository_group is not None and not is_exists:
            self.log.info(f"Creating repository group: {repository_group}")
            self.overview.add_repository_group(repository_group,
                                               self.tcinputs['azure_organization_name'],
                                               self.tcinputs.get('repository_plan'))
            self.log.info("Successfully created repository group")
            self.is_repo_group_created = True
        self.log.info(f"Using repository group: {repository_group} for backup and restore")
        self.log.info("Generating test projects and repositories")
        self.az_data = self.azhelper.generate_test_data(**self.test_data)
        self.log.info("Successfully generated test projects and repositories: %s", self.az_data)
        backup_job_id = self.overview.backup_now(repository_group)
        self.devopshelper.wait_for_job_completion(backup_job_id, check_restartability=True)

    @test_step
    def restore_and_validate_data(self):
        """Restores and validate test data"""
        self.overview.access_restore(self.tcinputs.get('repository_group'))
        rest = self.overview.restore_all()
        dest_path = self.tcinputs.get("des_path") or self.azhelper.restore_path
        rest.restore_to_disk(
            des_server=self.azhelper.client_machine.machine_name, des_path=dest_path)
        restore_job_id = self.admin_console.get_jobid_from_popup()
        self.devopshelper.wait_for_job_completion(restore_job_id, check_restartability=True)
        self.log.info("Done with restore to disk")
        bkp_path = self.test_data.get('download_folder')
        if bkp_path is not None:
            bkp_path = self.azhelper.client_machine.join_path(self.azhelper.remote_path, bkp_path)
        self.azhelper.validate_test_data(self.az_data, bkp_path, disk_path=dest_path,
                                         bare_validation=self.test_data.get('bare_validation'))

    def run(self):
        """
        Run function of this test case
        1) Access the instance, creates new instance if not present
        2) Backup all projects and repositories
        3) Restore all projects and repositories using restore to disk
        4) Repository validation by downloading the data
        """
        try:
            self.access_or_create_client()
            self.generate_data_and_backup()
            self.restore_and_validate_data()
            self.azhelper.cleanup(self.test_data.get('prefix'))
            if "des_path" in self.tcinputs:
                self.azhelper.client_machine.remove_directory(self.tcinputs["des_path"])
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.is_repo_group_created:
            self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['app_name'])
            self.overview.delete_repository_group(self.tcinputs.get("repository_group"))
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
