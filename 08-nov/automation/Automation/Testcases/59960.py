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
        "59960":
        {
        "git_app_name": "<App Name>",
        "git_access_token": "<Personal Access Token>",
        "git_organization_name": "<Organization name>",
        "access_nodes": "<List of access nodes>",
        "plan_name": "<Plan name>",
        "token_name": "<Access Token name>",
        "accessnodes_type": "<os type of access nodes>" (optional, required for creating new app),
        }
    }
"""
import json

from Web.AdminConsole.DevOps.devops_common_DevOpsApp_helper import DevOpsAppHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.DevOps.devops_common_db_helper import Verification


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "GitHub IDA Command Center - ACCT1 Create and Delete GitHub DevOps client"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.app_name = None
        self.test_data = None
        self.verification = None
        self.tcinputs = {
            "git_app_name": None,
            "git_access_token": None,
            "git_organization_name": None,
            "access_nodes": None,
            "plan": None,
            "token_name": None,
        }
        self.git_app_helper = None

    def setup(self):
        """Setup function of this test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.admin_console.click_button("OK")
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_devops()
            self.git_app_helper = DevOpsAppHelper(self.commcell, self.admin_console, self.tcinputs, self.log,
                                                  is_git=True)
            self.app_name = self.tcinputs['git_app_name']
            testdata = self.tcinputs.get('test_data', {})
            self.test_data = json.loads(testdata) if isinstance(testdata, str) else testdata
            self.verification = Verification(self.commcell, self.log, self.app_name)
            # deletion if instance exists
            self.verification.delete_validation()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def create_instance(self):
        """Creates instance"""
        self.log.info("Creating azure devops instance")
        self.git_app_helper.create_git_instance_from_instances()
        self.log.info("successfully created instance")
        self.tcinputs["access_nodes"] = self.git_app_helper.access_nodes
        self.verification.app_properties_validation(self.git_app_helper.tcinputs)

    @test_step
    def edit_instance(self):
        """Edits instance Properties"""
        self.log.info("Editing azure devops instance")
        self.admin_console.access_tab('Configuration')
        self.git_app_helper.edit_access_nodes_from_configuration(self.tcinputs['access_nodes'][0:2])
        self.log.info("successfully edited instance")
        edited_properties = {"access_nodes": self.tcinputs['access_nodes'][0:2]}
        self.verification.app_properties_validation(edited_properties)

    @test_step
    def create_and_delete_repository_group(self):
        """Creates repository group"""
        self.admin_console.access_tab('Repository groups')
        self.git_app_helper.create_repository_group_from_repository_groups("githubtestorg3rdApr")
        repo_properties = {"plan_name": self.tcinputs['plan'],
                           "repository_group": 'automated_repo_group',
                           "organization_name": "githubtestorg3rdApr"}
        self.verification.app_properties_validation(repo_properties)
        self.git_app_helper.delete_repository_group_from_toolbar()
        self.admin_console.wait_for_completion()

    @test_step
    def backup(self):
        """Run a backup of the provided repository group or the 'default' subclient"""
        self.admin_console.access_tab("Repository groups")
        self.git_app_helper.backup_from_repository_groups(self.tcinputs.get('repository_group', 'default'),
                                                          for_validation=True)
        self.log.info('Successfully backed up data')

    @test_step
    def restore_and_validate_data(self):
        """Restores to git and validates the data"""
        self.git_app_helper.restore_from_repository_groups(self.tcinputs.get('repository_group', 'default'),
                                                           validate_data=True,
                                                           in_place=True)
        self.log.info('All repositories validated successfully.')
        self.admin_console.select_breadcrumb_link_using_text(self.app_name)

    @test_step
    def delete_instance(self):
        """Delete instance"""
        self.log.info("Deleting [%s] instance", self.app_name)
        self.admin_console.select_breadcrumb_link_using_text("DevOps")
        self.git_app_helper.delete_app_from_instances()
        if self.git_app_helper.check_if_instance_exists_from_instances():
            raise CVTestStepFailure("[%s] instance is not getting deleted" % self.app_name)
        self.log.info("Deleted [%s] instance successfully", self.app_name)
        self.navigator.navigate_to_servers()
        self.git_app_helper.delete_app_from_servers()

    def run(self):
        """
        Run function of this test case
        1) Creates github instance, verifies if same is reflected in db.
        2) Modifies app properties, verifies if same is reflected in db.
        3) Creates new repository group, verifies if same is reflected in db and deletes it.
        4) Run a backup and restore of the default sub-client
        5) Deletes github instance.
        """
        try:
            self.create_instance()
            self.edit_instance()
            self.create_and_delete_repository_group()
            self.backup()
            self.restore_and_validate_data()
            self.delete_instance()

            self.git_app_helper.cleanup_files()
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
