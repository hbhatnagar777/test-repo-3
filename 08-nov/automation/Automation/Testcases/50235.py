"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    tear_down()                 --  tear down method for testcase

    create_app()                --  Method to create a new Salesforce app in commcell

    create_objects()            --  Creates hierarchy of objects in Salesforce

    backup_full()               --  Method to run full backup and wait for job completion

    run_restore_to_database()   --  Runs out of place restore

    validate_object_data()      --  Validates restored data with salesforce

    delete()                    --  Deletes Salesforce app from Commcell

    run()                       --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs.

    "testCases": {
        "50235": {
            "ClientName": "",
            "DestinationClient": "",
            "salesforce_options": {
                "login_url": "https://login.salesforce.com",
                "salesforce_user_name": "",
                "salesforce_user_password": "",
                "salesforce_user_token": "",
                "consumer_id": "",
                "consumer_secret": "",
                "sandbox": false
            },
            "infrastructure_options": {
                "access_node": "",
                "cache_path": "/tmp",
                "db_type": "POSTGRESQL",
                "db_host_name": "",
                "db_user_name": "postgres",
                "db_password": ""
            },
            "profile": "Admin",
            "plan": "",
            "resource_pool": "",
            "storage_policy": "",
            "sf_object": "Contact",
            "fields": ["FirstName", "LastName", "Email", "Phone"]
        }
    }
"""
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType
from Web.AdminConsole.Salesforce.constants import ReactRestoreTarget, ParentLevel, DependentLevel


DATABASE = 'tc_50235'
APP_NAME = f"TC_50235_{datetime.now().strftime('%d_%B_%H_%M')}"
FIELD_LABELS = ("Test Field 1", "Test Field 2")

""" Create objects. Run a backup job. Restore to database and validate for each hierarchy."""


class TestCase(CVTestCase):
    """Class for triggering and validating alerts on a Salesforce org """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Restore to database"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.org_name = APP_NAME
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.parent_object = None
        self.parent_data = None
        self.immediate_child = None
        self.immediate_child_data = None
        self.all_children = list()
        self.all_children_data = list()
        self.restore_db_name = None

    def setup(self):
        """Method to set up test variables"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
            stay_logged_in=True
        )
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        if "ClientName" in self.tcinputs:
            self.org_name = self.sf_helper.ClientName
        else:
            self.sf_helper.create_new_database(DATABASE)
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_salesforce()
        self.sf_apps = SalesforceOrganizations(self.admin_console, self.commcell)
        self.sf_app_details = SalesforceOverview(self.admin_console, self.commcell)

    def tear_down(self):
        """Tear down method for testcase"""
        if self.status == PASSED:
            self.sf_helper.delete_object_data(self.parent_object.fullName, self.parent_data)
            self.sf_helper.delete_object_data(self.immediate_child.fullName, self.immediate_child_data)
            for i in range(2):
                child_object = self.all_children[0]
                self.all_children.pop(0)
                child_data = self.all_children_data[0]
                self.all_children_data.pop(0)
                self.sf_helper.delete_object_data(child_object.fullName, child_data)

    @test_step
    def create_app(self):
        """Method to create a new Salesforce app in commcell"""
        try:
            infra_options = self.sf_helper.updated_infrastructure_options(db_name=DATABASE, db_type=DbType.POSTGRESQL)
            self.sf_apps.add_org(
                org_name=self.org_name,
                plan=self.sf_helper.plan,
                oauth=False,
                **self.sf_helper.salesforce_options.__dict__,
                **infra_options.__dict__
            )
            self.org_name = APP_NAME
        except Exception as exp:
            raise CVTestStepFailure from exp

    def create_objects(self):
        """Creates hierarchy of objects in Salesforce"""
        self.parent_object, self.parent_data = self.sf_helper.create_test_object(
            label=f"{APP_NAME}_parent",
            field_labels=FIELD_LABELS,
            rec_count=10
        )
        self.immediate_child, self.immediate_child_data = self.sf_helper.create_child_object(
            label=f"{APP_NAME}_child",
            parent_object=self.parent_object,
            field_labels=FIELD_LABELS,
            rec_count=10
        )
        self.all_children.append(self.immediate_child)
        self.all_children_data.append(self.immediate_child_data)
        for i in range(2):
            child_object, child_data = self.sf_helper.create_child_object(
                label=f"{APP_NAME}_grandchild_{i + 1}",
                parent_object=self.all_children[-1],
                field_labels=FIELD_LABELS,
                rec_count=10
            )
            self.all_children.append(child_object)
            self.all_children_data.append(child_data)

    @test_step
    def backup_full(self):
        """Method to run full backup and wait for job completion"""
        try:
            self.sf_app_details.backup(backup_type="full")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def run_restore_to_database(self, dependent_level):
        """Runs out of place restore"""
        try:
            self.restore_db_name = DATABASE + "_restore"
            infra_options = self.sf_helper.updated_infrastructure_options(
                db_name=self.restore_db_name,
                db_type=DbType.POSTGRESQL
            )
            self.sf_helper.create_new_postgresql_database(self.restore_db_name)
            self.log.info(f"Running out of place restore to database {self.restore_db_name} on "
                          f"{infra_options.db_host_name}")
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.click_on_restore(self.org_name)
            job_id = RSalesforceRestore(self.admin_console).object_level_restore(
                path='/Objects',
                dependent_level=dependent_level,
                parent_level=ParentLevel.NONE,
                file_folders=[self.parent_object.fullName],
                restore_target=ReactRestoreTarget.DATABASE,
                **infra_options.__dict__
            )
            job = self.commcell.job_controller.get(job_id)
            if not job.wait_for_completion():
                raise Exception(f"Failed to run job {job_id} with error: {job.delay_reason}")
            self.log.info(f"Successfully finished job {job_id}")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def validate_object_data(self, dependent_level):
        """
        Validates restored data with postgres db

        Args:
            dependent_level: restore dependent level

        Returns:
            None

        Raises:
            Exception: if validation fails
        """
        try:
            restored_objects = [self.parent_object.fullName]
            restored_data = [self.parent_data]
            objects_not_restored = set([child.fullName for child in self.all_children])
            if dependent_level == DependentLevel.IMMEDIATE:
                restored_objects.append(self.immediate_child.fullName)
                restored_data.append(self.immediate_child_data)
                objects_not_restored.discard(self.immediate_child.fullName)
            if dependent_level == DependentLevel.ALL:
                for child_object, child_object_data in zip(self.all_children, self.all_children_data):
                    restored_objects.append(child_object.fullName)
                    restored_data.append(child_object_data)
                    objects_not_restored.discard(child_object.fullName)

            for sf_object, data in zip(restored_objects, restored_data):
                keys = data[0].keys()
                key_list = list(keys)
                db_data = self.sf_helper.retrieve_object_data_from_postgres_db(self.restore_db_name, sf_object,
                                                                               fields=key_list)
                self.sf_helper.validate_object_data(data, db_data)

        except Exception as exp:
            raise CVTestStepFailure from exp

    def run(self):
        """
                Main function for test case execution
        """
        try:
            self.create_objects()
            # Create new Salesforce App in Command Center
            if "ClientName" in self.tcinputs:
                self.sf_apps.access_organization(self.sf_helper.ClientName)
            else:
                self.create_app()

            self.backup_full()

            self.run_restore_to_database(DependentLevel.NONE)
            # Validate restored data with postgres DB
            self.validate_object_data(DependentLevel.NONE)
            # Run restore to database with dependent level 'Immediate Children'
            self.run_restore_to_database(DependentLevel.IMMEDIATE)
            # Validate restored data with postgres DB
            self.validate_object_data(DependentLevel.IMMEDIATE)
            # Run restore to database with dependent level 'All Children'
            self.run_restore_to_database(DependentLevel.ALL)
            # Validate restored data with postgres DB
            self.validate_object_data(DependentLevel.ALL)

            # Delete Salesforce App
            if "ClientName" not in self.tcinputs:
                self.delete()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def delete(self):
        """Deletes Salesforce app and Connected App credentials from Commcell"""
        try:
            self.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(APP_NAME)
            self.sf_app_details.delete()
        except Exception as exp:
            raise CVTestStepFailure from exp
