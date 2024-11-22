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
        "59959":
        {
        "azure_app_name": "<App Name>",
        "azure_access_token": "<Personal Access Token>",
        "azure_organization_name": "<Organization name>",
        "access_nodes": "<string representation of access nodes list>", (eg. "['node']"),
        "no_of_pit_runs": "<Integer, No. of PIT iterations to run>" (optional, default is 3),
        "plan": "<Plan name>"        (optional, required for creating new app),
        "accessnodes_type": "<os type of access nodes>" (optional, required for creating new app),
        "import_repo" : "<dict with repo_name and repo_url to be imported in iteration 0>' "
        "test_data": "<string representation of test data dictionary>" (optional,eg."{'key':'val'}")
            default- "{
                       "bare_validation": "Validation done with bare", (optional, default-True)
                       }
        }
    }
"""
import time
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
        self.name = "Azure DevOps IDA Command Center - ACCT1 PIT In Place Restore"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.start_time_list = None
        self.end_time_list = None
        self.az_data = []
        self.is_repo_group_created = False
        self.is_app_created = False
        self.tcinputs = {
            "azure_app_name": None,
            "azure_access_token": None,
            "azure_organization_name": None,
            "access_nodes": None,
            "plan": None,
            "import_repo": None
        }
        self.azure_app_helper = None

    def setup(self):
        """Setup function of this test case"""
        try:
            self.start_time_list = []
            self.end_time_list = []
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.admin_console.click_button("OK")
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_devops()
            self.tcinputs['repository_group'] = 'auto_repo_59959'
            self.azure_app_helper = DevOpsAppHelper(self.commcell, self.admin_console, self.tcinputs, self.log,
                                                    is_azure=True)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def _update_job_time(self, job_id):
        """Updates job start time and end time
        Args:
            job_id   (int): Job id
        """
        job_obj = self.commcell.job_controller.get(job_id)
        start_time = time.strftime('%d-%B-%Y-%I-%M-%p', time.localtime(
            job_obj.summary['jobStartTime']))
        end_time = time.strftime('%d-%B-%Y-%I-%M-%p', time.localtime(
            job_obj.summary['lastUpdateTime']))
        self.start_time_list.append(start_time)
        self.end_time_list.append(end_time)
        self.log.info(f"For job ID: {job_id} start time is {start_time} and end time is {end_time}")

    @test_step
    def access_or_create_client(self):
        """Access client if exists else creates new one"""
        self.is_app_created = self.azure_app_helper.access_or_create_instance_from_instances()
        self.admin_console.access_tab('Repository groups')

    @test_step
    def backup(self, iteration):
        """
        Runs a backup of the provided repository_group or the 'default' subclient
         Args:
            iteration       (int)       --  job iteration
        """

        repository_group = self.tcinputs.get('repository_group', 'default')
        backup_details = self.azure_app_helper.backup_from_repository_groups(repository_group, for_validation=True,
                                                                             backup_path=f'PIT_{iteration}')
        self.az_data.append(self.azure_app_helper.az_data)
        self.log.info('Backed up projects and repositories : %s', self.az_data[-1])
        if iteration == 0:
            self.is_repo_group_created = backup_details.get('is_repo_group_created')
        backup_job_id = backup_details.get('backup_job_id')
        self._update_job_time(backup_job_id)

    @test_step
    def restore_by_time_and_validate(self, iteration):
        """starts restore of databases based on time and validates
        Args:
            iteration       (int)       --  job iteration
        """
        from_time = self.start_time_list[iteration]
        to_time = self.end_time_list[iteration]

        bkp_path = self.azure_app_helper.azhelper.client_machine.join_path(self.azure_app_helper.azhelper.remote_path,
                                                                           f"PIT_{iteration}")

        repository_group = self.tcinputs.get('repository_group', 'default')
        self.azure_app_helper.restore_by_time(from_time, to_time, repository_group=repository_group, validate=True,
                                              bkp_path=bkp_path,
                                              projects_and_repos=self.az_data[iteration])

    def run(self):
        """
        Run function of this test case
        1) Access the instance, creates new instance if not present
        2) Backup all projects and repositories based on number of iterations
        3) Restore all projects/repositories for in place restore based on PIT for each iteration
        4) Repository validation for each iteration by downloading the data
        """
        try:
            self.access_or_create_client()

            no_of_iterations = int(self.tcinputs.get('no_of_pit_runs') or 2)
            import_repo = self.tcinputs.get('import_repo')
            self.azure_app_helper.azhelper.create_project(f'auto_prj_{self.id}')

            for iteration in range(no_of_iterations):
                if iteration == 0:
                    self.azure_app_helper.azhelper.create_and_import_repository(self.tcinputs['azure_access_token'],
                                                                                import_repo['git_url'],
                                                                                import_repo['repo_name'],
                                                                                f'auto_prj_{self.id}')
                else:
                    self.azure_app_helper.azhelper.create_and_push_branches(import_repo['repo_name'],
                                                                            iteration)
                self.backup(iteration)

            for iteration in range(no_of_iterations):
                if iteration != 0:
                    self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['azure_app_name'])
                    self.admin_console.access_tab('Repository groups')
                self.log.info(f"Projects and repos that were backed up : {self.az_data[iteration]} in iteration: "
                              f"{iteration}")
                self.restore_by_time_and_validate(iteration)

            self.azure_app_helper.cleanup_files(projects=[f'auto_prj_{self.id}'])
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.is_app_created:
            self.log.info('Deleting created app')
            self.admin_console.select_breadcrumb_link_using_text('DevOps')
            self.azure_app_helper.delete_app_from_instances()
            self.navigator.navigate_to_servers()
            self.azure_app_helper.delete_app_from_servers()
        elif self.is_repo_group_created:
            self.log.info('Deleting created repository group')
            self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['azure_app_name'])
            self.admin_console.access_tab('Repository groups')
            self.azure_app_helper.delete_repository_group_from_repository_groups(self.tcinputs.get("repository_group"))

        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
