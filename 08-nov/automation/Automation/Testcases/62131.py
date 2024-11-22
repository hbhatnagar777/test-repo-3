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
        "62131":
        {
        "git_app_name": "<git App Name>",
        "git_access_token": "<git Personal Access Token>",
        "git_organization_name": "<git Organization name>",
        "access_nodes": "<string representation of access nodes list>", (eg. "['node']"),
        "accessnodes_type": "<os type of access nodes>",
        "plan": "<Plan name>",

        "account_type": "<GitHub Account type>" (optional, default is Business/Institution),
        "staging_path": "<Staging path>"  (optional, used while creating new app if specified),
        "impersonate_user": "<dict of impersonation details>" (optional, default- option disabled),

        "git_bin":  "<Git binary path>"   (optional, required when not using default bin path),

        "test_data": "<string representation of test data dictionary>" (optional,eg."{'key':'val'}")
            default- "{"prefix": "<prefix to be used for generated data>", (default-automation_)
                       "no_of_repos": "<no. of repos in each project>",  (optional, default-2)
                       "git_url": "<repo url that need to be imported>", (optional, default-None)
                       "download_folder": "<folder name in remote path>", (optional, default-Backup)
                       "bare_validation": "Validation done with bare", (optional, default-True)
                       "repo_data": <[No. folders, files in each folder, file size(mb)]>}"
                                (optional, default -[2,2,24])
        }
    }
"""
import copy

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
        self.name = "GitHub IDA - Verify VOI count is correctly populated in LSR, LSR-WW and SCPU reports"
        self.browser = None
        self.admin_console = None
        self.instances = None
        self.overview = None
        self.devopshelper = None
        self.githelper = None
        self.lsr_entry = {}
        self.scpu_entry = {}
        self.test_data = None
        self.tcinputs = {
            "git_app_name": None,
            "git_access_token": None,
            "git_organization_name": None,
            "access_nodes": None,
            "accessnodes_type": None,
            "plan": None
        }

    def setup(self):
        """Setup function of this test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'],
                                     stay_logged_in=True)
            self.overview = Overview(self.admin_console)
            self.devopshelper = DevOpsHelper(self.commcell, self.tcinputs, self.admin_console)
            self.test_data = self.devopshelper.test_data
            self.githelper = self.devopshelper.githelper
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def access_or_create_client(self, git_app_name):
        """Access client if exists else creates new one"""
        self.admin_console.goto_adminconsole()
        self.admin_console.navigator.navigate_to_devops()
        self.instances = Instances(self.admin_console)
        self.instances.select_all_instances_view()
        if not self.instances.is_instance_exists(git_app_name):
            if self.tcinputs.get("plan"):
                self.log.info("Creating github instance")
                git_instance = self.instances.add_github_instance()
                git_instance.add_git_details(self.tcinputs["git_access_token"],
                                             self.tcinputs["git_organization_name"],
                                             self.devopshelper.access_nodes,
                                             self.tcinputs["plan"],
                                             self.tcinputs.get("accessnodes_type"),
                                             account_type=self.tcinputs.get("account_type"),
                                             app_name=git_app_name,
                                             staging_path=self.tcinputs.get("staging_path"),
                                             impersonate_user=self.tcinputs.get("impersonate_user"))
                self.log.info("successfully created instance")
            else:
                raise CVTestCaseInitFailure(f"Instance: {git_app_name} doesn't exist."
                                            f" Plan is required for creating new instance")
        self.instances.access_instance(git_app_name)
        self.commcell.clients.refresh()
        return self.commcell.clients.get(git_app_name).client_id

    @test_step
    def validate_voi_count(self, gen_data=False, repo=None, temp_client=False, delete_case=False, case=None, voi_init=None):
        """
        validates voi count
        """
        git_app_name = f"{self.tcinputs['git_app_name']}{'_temp' if temp_client else ''}"
        if voi_init is None:
            bb_purchased, bb_used = self.devopshelper.get_voi_count()
        else:
            bb_purchased, bb_used = voi_init
        self.log.info(f"*** Initial VOI count - [{bb_purchased, bb_used}] for case:{case} ***")
        if not delete_case:
            client_id = self.access_or_create_client(git_app_name)
            git_data = self.generate_data_and_backup(gen_data, repo)
            if gen_data and repo:
                self.lsr_entry.setdefault(client_id, []).extend(git_data)
                backup_count = len(git_data)
                expected_outcome = f"VOI count should be increased by {backup_count}"
            elif temp_client:
                cl_id = self.commcell.clients.get(self.tcinputs['git_app_name']).client_id
                self.lsr_entry[client_id] = copy.deepcopy(self.lsr_entry[cl_id])
                backup_count = len(self.lsr_entry[client_id])
                expected_outcome = f"VOI count should be increased by {backup_count}"
            elif repo:
                backup_count = 0
                expected_outcome = "VOI count should be same"
            else:
                self.lsr_entry.setdefault(client_id, []).extend(git_data)
                backup_count = len(self.lsr_entry[client_id])
                expected_outcome = f"VOI count should be increased by {backup_count}"
            self.scpu_entry = self.lsr_entry
        else:
            client_id = self.commcell.clients.get(git_app_name).client_id
            if not repo:
                self.commcell.clients.delete(git_app_name)
                backup_count = -len(self.lsr_entry[client_id])
                self.lsr_entry.pop(client_id, None)
                expected_outcome = f"VOI count should be decreased by {backup_count}"
            else:
                self.access_or_create_client(git_app_name)
                self.overview.delete_repository_group(repository_group=repo)
                backup_count = 0
                expected_outcome = "VOI count should be same"
        self.log.info(expected_outcome)
        ab_purchased, ab_used = self.devopshelper.get_voi_count(verify_entry=self.lsr_entry,
                                                                verify_scpu_entry=self.scpu_entry)
        self.log.info(f"*** Final VOI count - [{ab_purchased, ab_used}] for case:{case} ***")
        if (bb_purchased, bb_used+backup_count) != (ab_purchased, ab_used):
            raise Exception(f'LSR- VOI count verification failed, expected: {expected_outcome}')
        return [ab_purchased, ab_used]

    @test_step
    def generate_data_and_backup(self, gen_data=False, repo=None):
        """Generates test data and runs a backup, returns count of backup repos"""
        org = self.tcinputs['git_organization_name']
        repository_group = repo or 'default'
        is_exists = self.overview.is_repository_group_exists(repository_group)
        if repository_group is not None and not is_exists:
            self.log.info(f"Creating repository group: {repository_group}")
            self.overview.add_repository_group(repository_group, org,
                                               self.tcinputs.get('repository_plan'))
            self.log.info("Successfully created repository group")
        self.log.info(f"Using repository group: {repository_group} for backup and restore")
        git_data = {}
        if gen_data:
            self.log.info("Generating test repositories")
            git_data = self.githelper.generate_test_data(**self.test_data)
            self.log.info("Successfully generated test repositories: %s", git_data)
        backup_job_id = self.overview.backup_now(repository_group)
        self.devopshelper.wait_for_job_completion(backup_job_id)
        return [f"/{org}/{repo}" for repo in git_data] if git_data else []

    def run(self):
        """
        Run function of this test case
        Generate data and create two clients - A & B
        Case1- Backup by client A(defaultsc)
                --- VOI count should be increased in LSR and SCPU
        Case2- Backup by client A(newsc)
                --- VOI count should not be increased in LSR and SCPU
        Case3- Backup by client B(defaultsc)
                --- VOI count should be increased in LSR and SCPU
        Case4- Backup by client B(newsc), additional content is generated
                --- VOI count should be increased in LSR and SCPU due to additional content
        Case5- Delete newsc in client B
                --- VOI count should not be decreased in LSR and SCPU
        Case6- Delete newsc in client A
                --- VOI count should not be decreased in LSR and SCPU
        Case7- Delete client B
                --- VOI count should be decreased in LSR but not from SCPU
        Case8- Delete client A
                --- VOI count should be decreased in LSR but not from SCPU
        """
        try:
            self.githelper.cleanup("", True)
            git_app = self.tcinputs['git_app_name']
            for git_app in [git_app, f"{git_app}_temp"]:
                if git_app in self.commcell.clients.all_clients:
                    self.commcell.clients.delete(git_app)
            voi_init = None
            case = "Backup by client A(sc - default)" \
                   " --- VOI count should be increased in LSR and SCPU"
            voi_init = self.validate_voi_count(gen_data=True, repo=None, temp_client=False,
                                               delete_case=False, case=case, voi_init=voi_init)
            case = "Backup by client A(sc - newsc)" \
                   " --- VOI count should not be increased in LSR and SCPU"
            voi_init = self.validate_voi_count(gen_data=False, repo='newsc', temp_client=False,
                                               delete_case=False, case=case, voi_init=voi_init)
            case = "Backup by client B(sc - default)" \
                   " --- VOI count should be increased in LSR and SCPU"
            voi_init = self.validate_voi_count(gen_data=False, repo='default', temp_client=True,
                                               delete_case=False, case=case, voi_init=voi_init)
            case = "Backup by client B(sc - newsc)" \
                   " --- VOI count should be increased in LSR and SCPU due to additional content"
            voi_init = self.validate_voi_count(gen_data=True, repo='newsc', temp_client=True,
                                               delete_case=False, case=case, voi_init=voi_init)
            case = "Delete newsc in client B --- VOI count should not be decreased in LSR and SCPU"
            voi_init = self.validate_voi_count(gen_data=False, repo='newsc', temp_client=True,
                                               delete_case=True, case=case, voi_init=voi_init)
            case = "Delete newsc in client A --- VOI count should not be decreased in LSR and SCPU"
            voi_init = self.validate_voi_count(gen_data=False, repo='newsc', temp_client=False,
                                               delete_case=True, case=case, voi_init=voi_init)
            case = "Delete client B --- VOI count should be decreased in LSR but not from SCPU"
            voi_init = self.validate_voi_count(gen_data=False, repo=None, temp_client=True,
                                               delete_case=True, case=case, voi_init=voi_init)
            case = "Delete client A --- VOI count should be decreased in LSR but not from SCPU"
            self.validate_voi_count(gen_data=False, repo=None, temp_client=False,
                                    delete_case=True, case=case, voi_init=voi_init)

            self.githelper.cleanup(self.test_data.get('prefix'))
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
