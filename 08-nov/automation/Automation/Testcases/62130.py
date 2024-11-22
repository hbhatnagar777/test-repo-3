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
        "62130":
        {
        "azure_app_name": "<Azure App Name>",
        "azure_access_token": "<Azure Personal Access Token>",
        "azure_organization_name": "<Azure Organization name>",
        "access_nodes": "<string representation of access nodes list>", (eg. "['node']"),
        "accessnodes_type": "<os type of access nodes>",
        "plan": "<Plan name>",
        "MediaAgentName": "<Name of the media agent to which plan is associate to>",
        "SqlSaPassword": "<password for accessing sql>" (used for moving job and running data aging),

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
        self.name = "Azure DevOps IDA - Verify VOI count is correctly populated in LSR, LSR-WW and SCPU reports with data aging"
        self.browser = None
        self.admin_console = None
        self.instances = None
        self.overview = None
        self.devopshelper = None
        self.azhelper = None
        self.backup_jobs = []
        self.lsr_entry = {}
        self.scpu_entry = {}
        self.test_data = None
        self.tcinputs = {
            "azure_app_name": None,
            "azure_access_token": None,
            "azure_organization_name": None,
            "access_nodes": None,
            "accessnodes_type": None,
            "plan": None,
            "MediaAgentName": None,
            "SqlSaPassword": None
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
            self.test_data['cleanup'] = False
            self.azhelper = self.devopshelper.azhelper
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def access_or_create_client(self, azure_app_name):
        """Access client if exists else creates new one"""
        self.admin_console.goto_adminconsole()
        self.admin_console.navigator.navigate_to_devops()
        self.instances = Instances(self.admin_console)
        self.instances.select_all_instances_view()
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
                                              staging_path=self.tcinputs.get("staging_path"),
                                              impersonate_user=self.tcinputs.get("impersonate_user"))
                self.log.info("successfully created instance")
            else:
                raise CVTestCaseInitFailure(f"Instance: {azure_app_name} doesn't exist."
                                            f" Plan is required for creating new instance")
        self.instances.access_instance(azure_app_name)
        self.commcell.clients.refresh()
        return self.commcell.clients.get(azure_app_name).client_id

    @test_step
    def validate_voi_count(self, gen_data=False, repo=None, age_job=None, case=None, voi_init=None):
        """
        validates voi count
        """
        azure_app_name = self.tcinputs['azure_app_name']
        if voi_init is None:
            bb_purchased, bb_used = self.devopshelper.get_voi_count()
        else:
            bb_purchased, bb_used = voi_init
        self.log.info(f"*** Initial VOI count - [{bb_purchased, bb_used}] for case:{case} ***")
        client_id = self.access_or_create_client(azure_app_name)
        if gen_data:
            az_data = self.generate_data_and_backup(gen_data, repo)
            self.lsr_entry.setdefault(client_id, []).extend(az_data)
            backup_count = len(az_data)
            expected_outcome = f"VOI count should be increased by {backup_count}"
        elif repo:
            self.generate_data_and_backup(gen_data, repo)
            backup_count = 0
            expected_outcome = f"VOI count should be same"
        else:
            old_copy_props = self.devopshelper.modify_plan_retention()
            self.devopshelper.move_job_and_validate_data_aging(age_job, is_aged=True,
                                                               move_job=True, run_aging=True)
            if age_job == self.backup_jobs[-1]:
                backup_count = -len(self.lsr_entry[client_id])
                expected_outcome = f"VOI count should be decreased by {backup_count}"
                self.lsr_entry.pop(client_id, None)
            else:
                backup_count = 0
                expected_outcome = f"VOI count should be same"
            self.devopshelper.modify_plan_retention(old_copy_props)
        self.scpu_entry = self.lsr_entry

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
        org = self.tcinputs['azure_organization_name']
        repository_group = repo or 'default'
        is_exists = self.overview.is_repository_group_exists(repository_group)
        if repository_group is not None and not is_exists:
            self.log.info(f"Creating repository group: {repository_group}")
            self.overview.add_repository_group(repository_group, org,
                                               self.tcinputs.get('repository_plan'))
            self.log.info("Successfully created repository group")
        self.log.info(f"Using repository group: {repository_group} for backup and restore")
        az_data = {}
        if gen_data:
            self.log.info("Generating test projects and repositories")
            az_data = self.azhelper.generate_test_data(**self.test_data)
            self.log.info("Successfully generated test projects and repositories: %s", az_data)
        backup_job_id = self.overview.backup_now(repository_group)
        self.devopshelper.wait_for_job_completion(backup_job_id)
        self.backup_jobs.append(backup_job_id)
        return [f"/{org}/{project}/{repo}" for project in az_data for repo in az_data[project]] if az_data else []

    def run(self):
        """
        Run function of this test case
        Generate data and create a client - A
        Case1- Backup by client A(defaultsc)
                --- VOI count should be increased in LSR and SCPU
        Case2- Backup by client A(newsc), additional content is generated
                --- VOI count should be increased in LSR and SCPU due to additional content
        Case3- Age the backup job of client A(sc - default)
                --- VOI count should be same in LSR and SCPU
        Case4- Age the backup job of client A(sc - newsc)
                --- VOI count should be decreased in LSR but not from SCPU
        """
        try:
            self.azhelper.cleanup("", True)
            azure_app = self.tcinputs['azure_app_name']
            if azure_app in self.commcell.clients.all_clients:
                self.commcell.clients.delete(azure_app)
            self.devopshelper.move_job_and_validate_data_aging(job_id=None, move_job=False,
                                                               run_aging=True, is_aged=None)
            voi_init = None
            case = "Backup by client A(sc - default)" \
                   " --- VOI count should be increased in LSR and SCPU"
            voi_init = self.validate_voi_count(gen_data=True, case=case, voi_init=voi_init)
            case = "Backup by client A(sc - newsc), additional content is generated" \
                   " --- VOI count should be increased in LSR and SCPU"
            voi_init = self.validate_voi_count(gen_data=True, repo='newsc', case=case, voi_init=voi_init)
            for job in self.backup_jobs:
                case = "Age the backup job of client A(sc - default/newsc)" \
                       " --- VOI count should be same/decreased in LSR but not from SCPU"
                voi_init = self.validate_voi_count(gen_data=False, age_job=job, case=case, voi_init=voi_init)

            self.azhelper.cleanup(self.test_data.get('prefix'))
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
